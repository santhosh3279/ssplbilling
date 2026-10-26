"""Paytm payments the system did not start (static QR, soundbox, links made in the Paytm dashboard).

payment_webhook() hands any notification whose order is not an SSPL Paytm Transaction to
record_unknown_payment(), which keeps it as an SSPL Paytm Unknown Payment. The Paytm Unknown
Payments page lists them; staff either delete one or turn it into a Receipt Payment Entry by
picking the From and To ledgers.

The webhook is a guest endpoint, so a record is only marked verified when Paytm's order status
API confirms it (PG orders) or its checksum is valid. Receipting an unverified one needs an
explicit override.
"""

import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from ssplbilling.api.paytm_api import (
	PG_STATUS_PATH,
	_ecr_sign_fields,
	_post_pg,
	_require_desk_user,
)

DOCTYPE = "SSPL Paytm Unknown Payment"
LOG_DOCTYPE = "SSPL Paytm Webhook Log"
SUCCESS_STATUSES = ("TXN_SUCCESS", "SUCCESS", "S")
LIST_FIELDS = [
	"name",
	"received_at",
	"amount",
	"status",
	"verified",
	"verification",
	"paytm_order_id",
	"paytm_txn_id",
	"rrn",
	"pay_method",
	"txn_date",
	"tid",
	"payment_entry",
	"party_type",
	"party",
	"paid_to",
	"reference_no",
]


def _first(body, *keys):
	for k in keys:
		v = body.get(k)
		if v not in (None, ""):
			return str(v).strip()
	return ""


def _parse(body):
	"""Pull what the page needs out of either payload shape: PG form fields (ORDERID, TXNAMOUNT in
	rupees) or ECR JSON (merchantTransactionId, transactionAmount in paise)."""
	info = body.get("resultInfo") if isinstance(body.get("resultInfo"), dict) else {}
	if body.get("TXNAMOUNT") or body.get("txnAmount"):
		amount = flt(_first(body, "TXNAMOUNT", "txnAmount"))
	elif body.get("transactionAmount"):
		amount = flt(body.get("transactionAmount")) / 100
	else:
		amount = flt(_first(body, "amount", "AMOUNT"))
	return {
		"paytm_order_id": _first(body, "ORDERID", "orderId", "merchantTransactionId", "linkOrderId"),
		"paytm_txn_id": _first(body, "TXNID", "txnId", "acquirementId"),
		"rrn": _first(body, "BANKTXNID", "bankTxnId", "retrievalReferenceNo", "rrn"),
		"pay_method": _first(body, "PAYMENTMODE", "paymentMode", "payMethod"),
		"txn_date": _first(body, "TXNDATE", "txnDate", "transactionDateTime"),
		"tid": _first(body, "paytmTid", "TID", "tid"),
		"mid": _first(body, "MID", "mid", "paytmMid"),
		"amount": amount,
		"status": (_first(body, "STATUS", "status") or info.get("resultStatus") or "").upper(),
	}


def _checksum_ok(settings, data, body, raw):
	"""True / False when the payload carries a checksum, None when it carries none. Unknown orders
	can be PG or ECR, so every shape is tried with both keys."""
	from paytmchecksum import verifySignature

	head = data.get("head") or {}
	checksum = head.get("checksum") or head.get("signature") or body.get("CHECKSUMHASH")
	if not checksum:
		return None
	if "head" in data:
		shapes = [_ecr_sign_fields(body)]
		if '"body":' in raw:
			shapes.append(raw[raw.index('"body":') + 7 : raw.rindex("}")].strip())
	else:
		shapes = [{k: v for k, v in body.items() if k != "CHECKSUMHASH"}]
	keys = [
		k
		for k in (
			settings.get_password("merchant_key", raise_exception=False),
			settings.get_password("edc_merchant_key", raise_exception=False),
		)
		if k
	]
	for key in keys:
		for signed in shapes:
			try:
				if verifySignature(signed, key, checksum):
					return True
			except Exception:
				continue
	return False


def _pg_status(settings, order_id):
	"""Paytm's own word on a PG order: the status body, or None when the call fails."""
	try:
		res = _post_pg(settings, PG_STATUS_PATH, {"mid": settings.merchant_id, "orderId": order_id})
	except Exception:
		return None
	return res.get("body") or {}


def _apply_pg_status(fields, rb):
	"""Overwrite the payload's claims with the status API's answer. Returns the Paytm status."""
	info = rb.get("resultInfo") or {}
	status = (info.get("resultStatus") or "").upper()
	if status == "TXN_SUCCESS":
		fields["amount"] = flt(rb.get("txnAmount")) or fields["amount"]
		fields["paytm_txn_id"] = rb.get("txnId") or fields["paytm_txn_id"]
		fields["rrn"] = rb.get("bankTxnId") or fields["rrn"]
		fields["pay_method"] = rb.get("paymentMode") or fields["pay_method"]
		fields["txn_date"] = rb.get("txnDate") or fields["txn_date"]
	return status


def _known_elsewhere(fields):
	"""A payment the system did start but whose payload the webhook could not match to its order."""
	for field in ("paytm_txn_id", "rrn"):
		value = fields.get(field)
		if value and frappe.db.exists("SSPL Paytm Transaction", {field: value}):
			return True
	return False


def _existing(fields):
	for field in ("paytm_txn_id", "rrn"):
		value = fields.get(field)
		if value:
			name = frappe.db.get_value(DOCTYPE, {field: value}, "name")
			if name:
				return name
	return None


def record_unknown_payment(raw, data, body):
	"""Called by payment_webhook() for an order it does not know. Never raises: Paytm retries any
	non-200 reply. Forged, failed or duplicate notifications are dropped; anything unreadable is
	logged so the payload shape can be traced."""
	try:
		return _record(raw, data, body)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(
			title="Paytm unknown payment not recorded", message=f"{frappe.get_traceback()}\n\n{raw[:5000]}"
		)
		return "error"


def _record(raw, data, body):
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	fields = _parse(body)
	if fields["mid"] and settings.merchant_id and fields["mid"] != settings.merchant_id:
		frappe.log_error(title="Paytm webhook MID mismatch", message=raw[:5000])
		return "rejected"

	checksum = _checksum_ok(settings, data, body, raw)
	if checksum is False:
		frappe.log_error(title="Paytm webhook checksum mismatch", message=raw[:5000])
		return "rejected"

	verified, verification = 0, "Checksum valid" if checksum else "Not verified"
	if checksum:
		verified = 1
	# Paytm EDC sales carry a TID and live on the ECR API; everything else is a PG order
	if fields["paytm_order_id"] and not fields["tid"] and settings.merchant_id:
		rb = _pg_status(settings, fields["paytm_order_id"])
		if rb is None:
			verification = f"{verification}; status check failed"
		else:
			status = _apply_pg_status(fields, rb)
			if status == "TXN_SUCCESS":
				verified, verification = 1, "Confirmed by Paytm status API"
			elif status:
				fields["status"] = status
				verified, verification = 0, f"Paytm status: {status}"

	if fields["status"] and fields["status"] not in SUCCESS_STATUSES:
		return "not paid"
	if not fields["amount"] or not (fields["paytm_txn_id"] or fields["rrn"]):
		frappe.log_error(title="Paytm webhook unknown order", message=raw[:5000])
		return "unreadable"
	if _known_elsewhere(fields):
		return "known"
	if _existing(fields):
		return "duplicate"

	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"received_at": now_datetime(),
			"amount": fields["amount"],
			"status": "Open",
			"verified": verified,
			"verification": verification,
			"paytm_order_id": fields["paytm_order_id"],
			"paytm_txn_id": fields["paytm_txn_id"],
			"rrn": fields["rrn"],
			"pay_method": fields["pay_method"],
			"txn_date": fields["txn_date"],
			"tid": fields["tid"],
			# form posts are stored as JSON too, so the page can show them field by field
			"payload": (raw if raw.strip().startswith("{") else json.dumps(data, indent=1, default=str))[:60000],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.publish_realtime("paytm_unknown_payment", {"name": doc.name}, after_commit=True)
	return "recorded"


def log_webhook(raw, data, body, result, txn=None):
	"""Keep every notification payment_webhook() receives, with what it did with it, for the
	Webhook Log view. Never raises and commits on its own: a log failure must not cost a payment."""
	try:
		fields = _parse(body)
		ref_doctype, ref_name = None, None
		if txn:
			ref_doctype, ref_name = "SSPL Paytm Transaction", txn.name
			fields["amount"] = flt(txn.amount) or fields["amount"]
			fields["status"] = txn.status
		elif result in ("recorded", "duplicate"):
			ref_doctype, ref_name = DOCTYPE, _existing(fields)
		elif result == "known":
			for field in ("paytm_txn_id", "rrn"):
				if fields.get(field):
					ref_name = frappe.db.get_value("SSPL Paytm Transaction", {field: fields[field]}, "name")
					if ref_name:
						ref_doctype = "SSPL Paytm Transaction"
						break
		doc = frappe.get_doc(
			{
				"doctype": LOG_DOCTYPE,
				"received_at": now_datetime(),
				"result": result,
				"amount": fields["amount"],
				"paytm_status": fields["status"],
				"order_id": fields["paytm_order_id"],
				"paytm_txn_id": fields["paytm_txn_id"],
				"rrn": fields["rrn"],
				"pay_method": fields["pay_method"],
				"tid": fields["tid"],
				"ref_doctype": ref_doctype if ref_name else None,
				"ref_name": ref_name,
				"payload": (raw if raw.strip().startswith("{") else json.dumps(data, indent=1, default=str))[:60000],
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.publish_realtime("paytm_webhook_log", {"name": doc.name})
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Paytm webhook log not saved", message=frappe.get_traceback())


@frappe.whitelist()
def get_webhook_logs(limit=500):
	"""Every webhook hit, newest first, for the Webhook Log view, each marked with whether its
	money is already booked (see _mark_linked)."""
	_require_desk_user()
	rows = frappe.get_all(
		LOG_DOCTYPE,
		fields=[
			"name",
			"received_at",
			"result",
			"amount",
			"paytm_status",
			"order_id",
			"paytm_txn_id",
			"rrn",
			"pay_method",
			"tid",
			"ref_doctype",
			"ref_name",
		],
		order_by="creation desc",
		limit_page_length=frappe.utils.cint(limit) or 500,
	)
	_mark_linked(rows)
	return rows


def _mark_linked(rows):
	"""Set linked (1 booked, 0 still to book, None no payment to book, e.g. failed or its unknown
	payment deleted) and linked_to / linked_doctype on each row. A system order is booked once its Sales Invoice is submitted or its receipt Payment
	Entry exists; an unknown payment once it is receipted."""
	txn_names = {r.ref_name for r in rows if r.ref_doctype == "SSPL Paytm Transaction" and r.ref_name}
	unknown_names = {r.ref_name for r in rows if r.ref_doctype == DOCTYPE and r.ref_name}
	txns = {
		t.name: t
		for t in frappe.get_all(
			"SSPL Paytm Transaction",
			filters={"name": ("in", list(txn_names))},
			fields=["name", "status", "sales_invoice", "payment_entry", "device_name"],
		)
	} if txn_names else {}
	tids = {r.tid for r in rows if r.tid}
	tid_pos = dict(
		frappe.get_all(
			"SSPL Paytm Device", filters={"tid": ("in", list(tids))}, fields=["tid", "pos_id"], as_list=True
		)
	) if tids else {}
	invoices = {t.sales_invoice for t in txns.values() if t.sales_invoice}
	invoice_status = dict(
		frappe.get_all(
			"Sales Invoice", filters={"name": ("in", list(invoices))}, fields=["name", "docstatus"], as_list=True
		)
	) if invoices else {}
	unknowns = {
		u.name: u
		for u in frappe.get_all(
			DOCTYPE, filters={"name": ("in", list(unknown_names))}, fields=["name", "status", "payment_entry"]
		)
	} if unknown_names else {}

	for r in rows:
		r.linked, r.linked_doctype, r.linked_to = None, None, None
		t = txns.get(r.ref_name) if r.ref_doctype == "SSPL Paytm Transaction" else None
		# POS ID the hit came from: the system order's posId, else the machine's by TID
		r.pos_id = (t and t.device_name) or tid_pos.get(r.tid) or None
		r.txn_status = t.status if t else None
		if r.result not in ("matched", "recorded", "duplicate", "known"):
			continue
		u = unknowns.get(r.ref_name) if r.ref_doctype == DOCTYPE else None
		if t:
			if t.status != "Success":
				continue
			if t.payment_entry:
				r.linked, r.linked_doctype, r.linked_to = 1, "Payment Entry", t.payment_entry
			elif t.sales_invoice:
				r.linked = 1 if invoice_status.get(t.sales_invoice) == 1 else 0
				r.linked_doctype, r.linked_to = "Sales Invoice", t.sales_invoice
			else:
				r.linked = 0
		elif u:
			r.linked = 1 if u.status == "Receipted" else 0
			if u.payment_entry:
				r.linked_doctype, r.linked_to = "Payment Entry", u.payment_entry


@frappe.whitelist()
def get_webhook_log(name):
	_require_desk_user()
	return frappe.get_doc(LOG_DOCTYPE, name).as_dict()


@frappe.whitelist()
def get_unknown_payments(status=None, limit=200):
	"""Rows for the left panel, newest first, plus the default To ledger (Paytm UPI account)."""
	_require_desk_user()
	filters = {"status": status} if status else {}
	rows = frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=LIST_FIELDS,
		order_by="creation desc",
		limit_page_length=frappe.utils.cint(limit) or 200,
	)
	return {
		"rows": rows,
		"upi_account": frappe.db.get_single_value("SSPL Paytm Settings", "upi_account"),
	}


@frappe.whitelist()
def get_unknown_payment(name):
	_require_desk_user()
	return frappe.get_doc(DOCTYPE, name).as_dict()


@frappe.whitelist(methods=["POST"])
def recheck_unknown_payment(name):
	"""Ask Paytm's status API again, e.g. after a status call failed when the webhook arrived."""
	_require_desk_user()
	doc = frappe.get_doc(DOCTYPE, name)
	if doc.status != "Open":
		frappe.throw(_("Only an open payment can be re-checked"))
	if not doc.paytm_order_id or doc.tid:
		frappe.throw(_("Paytm has no status lookup for this payment (card machine sale or no order id)"))
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	rb = _pg_status(settings, doc.paytm_order_id)
	if rb is None:
		frappe.throw(_("Paytm status check failed; see Error Log"))
	fields = {k: doc.get(k) for k in ("amount", "paytm_txn_id", "rrn", "pay_method", "txn_date")}
	status = _apply_pg_status(fields, rb)
	if status == "TXN_SUCCESS":
		doc.update(fields)
		doc.verified, doc.verification = 1, "Confirmed by Paytm status API"
	else:
		doc.verified, doc.verification = 0, f"Paytm status: {status or 'no reply'}"
	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def delete_unknown_payment(name):
	_require_desk_user()
	status = frappe.db.get_value(DOCTYPE, name, "status", for_update=True)
	if status != "Open":
		frappe.throw(_("A receipted payment cannot be deleted; cancel its Payment Entry instead"))
	frappe.delete_doc(DOCTYPE, name, ignore_permissions=True)
	return {"deleted": name}


@frappe.whitelist(methods=["POST"])
def create_receipt(
	name,
	party_type,
	party,
	paid_to,
	reference_no=None,
	remarks=None,
	allow_unverified=0,
	company=None,
	cost_center=None,
):
	"""Submit the Payment Entry for an unknown payment, once: the row lock stops a double click from
	booking it twice. From an Account it is an Internal Transfer (both must be Bank / Cash, as on the
	Payment / Receipt page); from a Customer / Supplier / Employee it is a Receive. Company and cost
	center are the operator's defaults, as on the Payment / Receipt page; the entry is posted on the
	day Paytm took the money."""
	from ssplbilling.api.paymentv2_api import _build_and_submit_payment_entry

	_require_desk_user()
	row = frappe.db.get_value(
		DOCTYPE, name, ["status", "payment_entry", "verified"], as_dict=True, for_update=True
	)
	if not row:
		frappe.throw(_("Payment {0} not found").format(name))
	if row.status != "Open" or row.payment_entry:
		frappe.throw(_("A receipt was already created: {0}").format(row.payment_entry))
	if not row.verified and not frappe.utils.cint(allow_unverified):
		frappe.throw(_("This payment is not verified by Paytm. Confirm it in the Paytm dashboard first."))
	if not party or not paid_to:
		frappe.throw(_("Select both From and To ledgers"))
	if party_type == "Account" and party == paid_to:
		frappe.throw(_("From and To ledgers must differ"))

	company = company or frappe.defaults.get_user_default("company") or frappe.defaults.get_global_default(
		"company"
	)
	if cost_center and frappe.db.get_value("Cost Center", cost_center, "company") != company:
		frappe.throw(_("Cost center {0} does not belong to {1}").format(cost_center, company))

	doc = frappe.get_doc(DOCTYPE, name)
	reference_no = (reference_no or "").strip() or doc.rrn or doc.paytm_txn_id or doc.name
	posting_date = _txn_posting_date(doc)
	is_transfer = party_type == "Account"
	pe_name = _build_and_submit_payment_entry(
		{
			"payment_type": "Internal Transfer" if is_transfer else "Receive",
			"party_type": None if is_transfer else party_type,
			"party": party,
			"amount": doc.amount,
			"mop_account": paid_to,
			# same fallback as the cashier desk when no Mode of Payment maps to the account
			"mode_of_payment": frappe.db.get_value(
				"Mode of Payment Account", {"default_account": paid_to}, "parent"
			)
			or "Cash",
			"reference_no": reference_no,
			"posting_date": posting_date,
			"reference_date": posting_date,
			"company": company,
			"cost_center": cost_center or None,
			"remarks": (
				f"Paytm {doc.pay_method or 'payment'} {doc.paytm_txn_id or doc.rrn} ({doc.name})"
				+ (f": {remarks.strip()}" if remarks and remarks.strip() else "")
			),
			# keeps these remarks instead of ERPNext's generated "Amount INR ... received from ..."
			"Custom Remarks": 1,
		}
	)
	doc.update(
		{
			"status": "Receipted",
			"payment_entry": pe_name,
			"party_type": party_type,
			"party": party,
			"paid_to": paid_to,
			"reference_no": reference_no,
		}
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	try:
		from ssplbilling.api.automatic_entries_api import mirror_standalone_payment_entry

		mirror_standalone_payment_entry(frappe.get_doc("Payment Entry", pe_name))
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: payment mirror failed")

	return {k: doc.get(k) for k in LIST_FIELDS}


def _txn_posting_date(doc):
	"""The day Paytm took the money: its txn date ("2026-10-23 16:25:27", sometimes with ".0"),
	else the day the payment reached us. Never later than today, which ERPNext would refuse."""
	for value in (doc.txn_date, doc.received_at):
		try:
			if value:
				return min(frappe.utils.getdate(str(value).replace("T", " ")[:10]), frappe.utils.getdate())
		except Exception:
			continue
	return frappe.utils.getdate()
