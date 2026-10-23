"""Paytm EDC (card machine) integration for the cashier desk.

Flow: cashier presses "POS" -> send_to_device() pushes the amount to the machine's TID
-> customer pays on the machine (UPI QR or card) -> Paytm calls payment_webhook() and/or
the page polls get_status() -> the result fills the UPI or Card box; the cashier submits.

Dynamic UPI QR (channel "QR"): create_qr() asks Paytm PG for a QR bound to an order id and
amount, the cashier page shows it, and the same get_status()/webhook path confirms the payment
through the PG v3 order status API.

Customer receipts (no invoice) on the Paytm receipt page:
- payment link (channel "Link"): create_payment_link() asks Paytm for a fixed-amount link bound to
  our order id (linkOrderId), so the same PG order status API and webhook confirm it;
- receipt QR (channel "QR" with a customer): create_receipt_qr(), a dynamic QR valid for 10 minutes.
Unlike the cashier's EDC/QR payments, which submit_invoice_with_payment() enters, a successful
receipt creates and submits its own Receipt Payment Entry against the customer (_make_receipt).
"""

import base64
import io
import json
import re

import frappe
import requests
from frappe import _
from frappe.utils import flt, now_datetime

# Matches Paytm's ECR sample (head.version 3.1, amount in paise). The production host is the
# older paytm.in one, which does answer ECR requests.
EDC_BASE_URL = {
	"Staging": "https://securestage.paytmpayments.com",
	"Production": "https://securegw-edc.paytm.in",
}
EDC_SALE_PATH = "/ecr/payment/request"
EDC_STATUS_PATH = "/ecr/V2/payment/status"
EDC_VOID_PATH = "/ecr/void"
EDC_CHANNEL_ID = "EDC"
EDC_VERSION = "3.1"
# autoAccept opens the payment on the machine without an accept/reject prompt;
# paymentMode QR opens straight on the UPI QR (ALL would ask the customer to choose)
EDC_EXTENDED_INFO = {"autoAccept": "True", "paymentMode": "QR"}
REQUEST_TIMEOUT = 20

# Paytm PG (online) APIs used by the dynamic UPI QR; signed with the PG Merchant Key
PG_BASE_URL = {
	"Staging": "https://securegw-stage.paytmpayments.in",
	"Production": "https://securegw.paytmpayments.in",
}
PG_QR_CREATE_PATH = "/paymentservices/qr/create"
PG_STATUS_PATH = "/v3/order/status"
# order status resultCode once Paytm has closed an unpaid QR order ("ORDER IS CLOSE.")
PG_ORDER_CLOSED = "810"

# Paytm payment link APIs; signed with the PG Merchant Key, head carries tokenType "AES"
LINK_BASE_URL = {
	"Staging": "https://securestage.paytmpayments.com",
	"Production": "https://secure.paytmpayments.com",
}
LINK_CREATE_PATH = "/link/create"
LINK_EXPIRE_PATH = "/link/expire"

CARD_PAY_METHODS = ("CARD", "CREDIT_CARD", "DEBIT_CARD", "EMI", "CC", "DC")
PG_CHANNELS = ("QR", "Link")
# The scheduler keeps asking Paytm about unpaid links this many days old
LINK_REFRESH_DAYS = 15
# Paytm expires a dynamic QR order 10 minutes after it is created (longer needs Paytm to enable it);
# the scheduler stops asking about an unpaid receipt QR after a day
QR_EXPIRY_SECONDS = 600
RECEIPT_QR_REFRESH_DAYS = 1


def _settings():
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	if not settings.enabled:
		frappe.throw(_("Paytm integration is disabled in SSPL Paytm Settings"))
	if not settings.merchant_id:
		frappe.throw(_("Merchant ID is missing in SSPL Paytm Settings"))
	return settings


def _signing_key(settings):
	key = settings.get_password("edc_merchant_key", raise_exception=False) or settings.get_password(
		"merchant_key", raise_exception=False
	)
	if not key:
		frappe.throw(_("Merchant Key is missing in SSPL Paytm Settings"))
	return key


def _pg_key(settings):
	key = settings.get_password("merchant_key", raise_exception=False)
	if not key:
		frappe.throw(_("Merchant Key is missing in SSPL Paytm Settings"))
	return key


def _is_pg(txn):
	"""QR and payment link orders live on Paytm PG; EDC orders on the card machine (ECR) API."""
	return txn.channel in PG_CHANNELS


def _require_desk_user():
	"""Payment links expose customer phones and amounts; portal (catalogue) users get none of it."""
	if (
		frappe.session.user == "Guest"
		or frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User"
	):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _key_for(settings, txn):
	return _pg_key(settings) if _is_pg(txn) else _signing_key(settings)


def _post_pg(settings, path, body, head=None):
	"""PG variant of _post(): head carries "signature" instead of the EDC checksum fields."""
	from paytmchecksum import generateSignature

	body_str = json.dumps(body, separators=(",", ":"))
	head = {**(head or {}), "signature": generateSignature(body_str, _pg_key(settings))}
	payload = '{"head":' + json.dumps(head, separators=(",", ":")) + ',"body":' + body_str + "}"
	res = requests.post(
		PG_BASE_URL[settings.environment] + path,
		data=payload,
		headers={"Content-Type": "application/json"},
		timeout=REQUEST_TIMEOUT,
	)
	if not res.ok:
		# Paytm explains rejections (e.g. 403 "Unauthorized Access") in a JSON resultInfo
		try:
			msg = (res.json().get("resultInfo") or {}).get("resultMsg")
		except ValueError:
			msg = None
		if msg:
			raise Exception(f"HTTP {res.status_code}: {msg}")
	res.raise_for_status()
	return res.json()


def _post_link(settings, path, body):
	"""Payment link variant of _post_pg(): head is {tokenType, signature}, and rejections come back
	as HTTP 200 with resultInfo.resultStatus FAILED (checked by the caller)."""
	from paytmchecksum import generateSignature

	body_str = json.dumps(body, separators=(",", ":"))
	head = {"tokenType": "AES", "signature": generateSignature(body_str, _pg_key(settings))}
	payload = '{"head":' + json.dumps(head, separators=(",", ":")) + ',"body":' + body_str + "}"
	res = requests.post(
		LINK_BASE_URL[settings.environment] + path,
		data=payload,
		headers={"Content-Type": "application/json"},
		timeout=REQUEST_TIMEOUT,
	)
	res.raise_for_status()
	return res.json()


def _ecr_sign_fields(body):
	# merchantExtendedInfo is signed as if its fields were top level; extendInfo is left out of
	# the checksum (both verified against Paytm, which rejects the other forms)
	fields = {}
	for k, v in body.items():
		if k == "merchantExtendedInfo":
			fields.update({ik: str(iv) for ik, iv in v.items()})
		elif not isinstance(v, dict | list):
			fields[k] = str(v)
	return fields


def _post(settings, path, body):
	"""ECR checksums cover the body's flat fields (sorted, "|"-joined by PaytmChecksum), not the
	JSON text; verified against Paytm, which rejects a signature over the JSON string."""
	from paytmchecksum import generateSignature

	body_str = json.dumps(body, separators=(",", ":"))
	head = {
		"requestTimeStamp": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
		"channelId": EDC_CHANNEL_ID,
		"checksum": generateSignature(_ecr_sign_fields(body), _signing_key(settings)),
		"version": EDC_VERSION,
	}
	payload = '{"head":' + json.dumps(head, separators=(",", ":")) + ',"body":' + body_str + "}"
	res = requests.post(
		EDC_BASE_URL[settings.environment] + path,
		data=payload,
		headers={"Content-Type": "application/json"},
		timeout=REQUEST_TIMEOUT,
	)
	res.raise_for_status()
	return res.json()


def _machine_user(user=None):
	"""The user whose machines apply: an inherited user (frontend `wb-inherited-user`) only for
	Administrator/admin, as in get_allowed_tiles; everyone else always gets their own."""
	current_user = frappe.session.user
	if user and current_user in ("Administrator", "admin"):
		return user
	return current_user


def _user_devices(settings, user=None):
	"""Machines a cashier may use: only rows assigned to them in SSPL Paytm Settings."""
	target = _machine_user(user)
	return [d for d in settings.devices if d.enabled and d.user == target]


def _device_for(settings, tid, user=None):
	for row in _user_devices(settings, user):
		if row.tid == tid:
			return row
	frappe.throw(_("Card machine with TID {0} is not assigned to you or is disabled").format(tid))


def _paytm_bill_no(invoice_name):
	"""Bill number as Paytm sees it: a series set up for mirroring (Automatic Entries) keeps its
	letters, any other series sends only its digits, e.g. EOW05855 -> 05855."""
	from ssplbilling.api.automatic_entries_api import (
		_conversion_mirror_series,
		_sales_mirror_series,
		get_automatic_entries,
	)

	entries = get_automatic_entries()
	naming_series = frappe.db.get_value("Sales Invoice", invoice_name, "naming_series") or ""
	if naming_series.split(".")[0] in _sales_mirror_series(entries) | _conversion_mirror_series(entries):
		return re.sub(r"[^A-Za-z0-9]", "", invoice_name)
	return re.sub(r"\D", "", invoice_name)


@frappe.whitelist()
def get_devices(user=None):
	"""Enabled card machines assigned to this user, for the cashier page; never returns any key."""
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	if not settings.enabled:
		return {"enabled": False, "qr_enabled": False, "devices": []}
	return {
		"enabled": True,
		"qr_enabled": bool(settings.qr_enabled),
		"devices": [
			{"device_name": d.device_name, "tid": d.tid, "user": d.user}
			for d in _user_devices(settings, user)
		],
	}


def _valid_phone(phone):
	"""Last 10 digits of a mobile number, or "" for a missing one or a placeholder such as
	9999999999 (all one digit)."""
	digits = re.sub(r"\D", "", phone or "")[-10:]
	return digits if len(digits) == 10 and len(set(digits)) > 1 else ""


def _invoice_contact(invoice_name):
	si = frappe.db.get_value(
		"Sales Invoice", invoice_name, ["customer", "customer_name", "contact_mobile"], as_dict=True
	)
	phone = _valid_phone(si.contact_mobile) or _valid_phone(
		frappe.db.get_value("Customer", si.customer, "mobile_no")
	)
	return si.customer_name, phone


@frappe.whitelist()
def get_invoice_contact(invoice_name):
	"""Customer name and a real phone number for the Paytm request; phone is "" when the bill only
	has a placeholder, so the cashier page can ask for one."""
	customer_name, phone = _invoice_contact(invoice_name)
	return {"customer_name": customer_name, "phone": phone}


@frappe.whitelist()
def send_to_device(invoice_name, amount, tid, pay_mode="QR", user=None, phone=None):
	"""Push the amount to the card machine; returns the order id to poll.
	pay_mode QR opens the machine on the UPI QR, CARD on card entry. The customer's name and phone
	(the cashier-entered phone wins over the bill's) go in extendInfo, echoed back by Paytm."""
	settings = _settings()
	if pay_mode not in ("QR", "CARD"):
		frappe.throw(_("Payment mode must be QR or CARD"))
	device = _device_for(settings, tid, user)
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice_name))

	now = now_datetime()
	# ECR ids are plain alphanumeric in Paytm's sample; invoice series carry "-" and "/"
	bill_no = _paytm_bill_no(invoice_name)
	order_id = f"{bill_no[:30]}{now.strftime('%y%m%d%H%M%S%f')[:15]}"
	txn_datetime = now.strftime("%Y-%m-%d %H:%M:%S")

	txn = frappe.get_doc(
		{
			"doctype": "SSPL Paytm Transaction",
			"order_id": order_id,
			"sales_invoice": invoice_name,
			"amount": amount,
			"status": "Pending",
			"device_name": device.device_name,
			"tid": tid,
			"transaction_datetime": txn_datetime,
		}
	).insert(ignore_permissions=True)

	body = {
		"paytmMid": settings.merchant_id,
		"paytmTid": tid,
		"transactionDateTime": txn_datetime,
		"merchantTransactionId": order_id,
		"merchantReferenceNo": bill_no,
		"transactionAmount": str(int(round(amount * 100))),  # paise
		"merchantExtendedInfo": {**EDC_EXTENDED_INFO, "paymentMode": pay_mode},
	}
	customer_name, bill_phone = _invoice_contact(invoice_name)
	extend_info = {"customerName": customer_name, "phoneNumber": _valid_phone(phone) or bill_phone}
	extend_info = {k: v for k, v in extend_info.items() if v}
	if extend_info:
		body["extendInfo"] = extend_info
	try:
		res = _post(settings, EDC_SALE_PATH, body)
	except Exception as e:
		_update_txn(txn, "Failed", {"error": str(e)}, str(e))
		frappe.db.commit()
		frappe.log_error(title="Paytm EDC sale request failed", message=frappe.get_traceback())
		frappe.throw(_("Could not reach Paytm: {0}").format(e))

	info = (res.get("body") or {}).get("resultInfo") or {}
	status = (info.get("resultStatus") or "").upper()
	# The machine has only accepted the request here; the payment itself is still pending.
	if status in ("FAIL", "F", "FAILURE"):
		_update_txn(txn, "Failed", res, info.get("resultMsg"))
		frappe.db.commit()
		frappe.throw(_("Paytm rejected the request: {0}").format(info.get("resultMsg") or status))

	_update_txn(txn, "Pending", res, info.get("resultMsg"))
	return {"order_id": order_id, "device_name": device.device_name, "status": "Pending"}


@frappe.whitelist()
def create_qr(invoice_name, amount):
	"""Create a Paytm dynamic UPI QR for the amount; returns the QR image and the order id to poll."""
	settings = _settings()
	if not settings.qr_enabled:
		frappe.throw(_("Dynamic QR is disabled in SSPL Paytm Settings"))
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice_name))

	now = now_datetime()
	# Paytm order ids allow only letters, digits, "_", "-" and "@" (max 50); series often contain "/"
	order_id = f"{_paytm_bill_no(invoice_name)[:40]}-{now.strftime('%H%M%S%f')[:9]}"
	pos_id = settings.qr_pos_id or re.sub(r"[^A-Za-z0-9_]", "_", frappe.session.user)[:20]

	txn = frappe.get_doc(
		{
			"doctype": "SSPL Paytm Transaction",
			"order_id": order_id,
			"sales_invoice": invoice_name,
			"amount": amount,
			"status": "Pending",
			"channel": "QR",
			"device_name": pos_id,
			"transaction_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
		}
	).insert(ignore_permissions=True)

	rb = _request_qr(settings, txn)
	return {
		"order_id": order_id,
		"status": "Pending",
		"qr_image": rb.get("image") or _qr_png(rb.get("qrData")),
		"qr_data": rb.get("qrData"),
	}


def _request_qr(settings, txn):
	"""Ask Paytm PG for the dynamic QR of a new QR row; marks the row Failed (committed) and throws
	when Paytm refuses. Returns Paytm's response body (image, qrData)."""
	body = {
		"mid": settings.merchant_id,
		"orderId": txn.order_id,
		"amount": f"{flt(txn.amount):.2f}",  # rupees, unlike the EDC paise amount
		"businessType": "UPI_QR_CODE",
		"posId": txn.device_name,
	}
	try:
		res = _post_pg(
			settings, PG_QR_CREATE_PATH, body, {"clientId": settings.qr_client_id or "C11", "version": "v1"}
		)
	except Exception as e:
		_update_txn(txn, "Failed", {"error": str(e)}, str(e))
		frappe.db.commit()
		frappe.log_error(title="Paytm QR create failed", message=frappe.get_traceback())
		frappe.throw(_("Could not reach Paytm: {0}").format(e))

	rb = res.get("body") or {}
	info = rb.get("resultInfo") or {}
	# The base64 image is large; keep it out of the stored response
	stored = {**res, "body": {k: v for k, v in rb.items() if k != "image"}}
	if (info.get("resultStatus") or "").upper() != "SUCCESS" or not (rb.get("image") or rb.get("qrData")):
		_update_txn(txn, "Failed", stored, info.get("resultMsg"))
		frappe.db.commit()
		frappe.throw(
			_("Paytm could not create the QR: {0}").format(info.get("resultMsg") or "no QR returned")
		)

	txn.qr_data = rb.get("qrData")
	_update_txn(txn, "Pending", stored, info.get("resultMsg"))
	return rb


def _qr_png(data):
	"""Base64 PNG of the UPI string, for when Paytm returns qrData without an image."""
	from pyqrcode import create as qrcreate

	buf = io.BytesIO()
	qrcreate(data).png(buf, scale=8, quiet_zone=2)
	return base64.b64encode(buf.getvalue()).decode()


@frappe.whitelist(methods=["POST"])
def create_payment_link(customer, amount, description=None, mobile=None, send_sms=0):
	"""Create a fixed-amount Paytm payment link for a customer receipt; returns the link row.
	The link carries our order id (linkOrderId) so status checks and the webhook find it."""
	_require_desk_user()
	settings = _settings()
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	customer_name = frappe.db.get_value("Customer", customer, "customer_name")
	if not customer_name:
		frappe.throw(_("Customer {0} not found").format(customer))
	if not settings.upi_account:
		frappe.throw(_("Set the UPI Account in SSPL Paytm Settings; link payments are received into it"))

	mobile = _valid_phone(mobile) or _valid_phone(frappe.db.get_value("Customer", customer, "mobile_no"))
	if frappe.utils.cint(send_sms) and not mobile:
		frappe.throw(_("A valid mobile number is needed to send the link by SMS"))
	# linkDescription is limited to 30 characters, linkName to 64
	description = (description or "").strip()[:30] or "Payment to Sundaram and Sons"
	now = now_datetime()
	order_id = f"LNK{now.strftime('%y%m%d%H%M%S%f')[:16]}"

	txn = frappe.get_doc(
		{
			"doctype": "SSPL Paytm Transaction",
			"order_id": order_id,
			"amount": amount,
			"status": "Pending",
			"channel": "Link",
			"customer": customer,
			"customer_mobile": mobile,
			"link_description": description,
			"transaction_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
		}
	).insert(ignore_permissions=True)

	body = {
		"mid": settings.merchant_id,
		"linkType": "FIXED",
		"linkName": re.sub(r"[^A-Za-z0-9]", "", customer_name)[:64] or "Payment",
		"linkDescription": description,
		"amount": amount,
		"linkOrderId": order_id,
		"singleTransactionOnly": True,
		"sendSms": bool(frappe.utils.cint(send_sms)),
		"sendEmail": False,
	}
	if settings.payment_notification_url:
		body["statusCallbackUrl"] = settings.payment_notification_url
	if mobile:
		body["customerContact"] = {"customerName": customer_name, "customerMobile": mobile}
	try:
		res = _post_link(settings, LINK_CREATE_PATH, body)
	except Exception as e:
		_update_txn(txn, "Failed", {"error": str(e)}, str(e))
		frappe.db.commit()
		frappe.log_error(title="Paytm link create failed", message=frappe.get_traceback())
		frappe.throw(_("Could not reach Paytm: {0}").format(e))

	rb = res.get("body") or {}
	info = rb.get("resultInfo") or {}
	if (info.get("resultStatus") or "").upper() != "SUCCESS" or not rb.get("shortUrl"):
		msg = info.get("resultMessage") or info.get("resultMsg") or "no link returned"
		_update_txn(txn, "Failed", res, msg)
		frappe.db.commit()
		frappe.throw(_("Paytm could not create the link: {0}").format(msg))

	txn.link_id = str(rb.get("linkId") or "")
	txn.short_url = rb["shortUrl"]
	_update_txn(txn, "Pending", res, info.get("resultMessage"))
	return _txn_result(txn)


@frappe.whitelist(methods=["POST"])
def create_receipt_qr(customer, amount, description=None, mobile=None):
	"""Dynamic UPI QR for a customer receipt (no invoice), shown on screen or shared with the
	customer. Valid for QR_EXPIRY_SECONDS; once paid it gets its Receipt Payment Entry like a link."""
	_require_desk_user()
	settings = _settings()
	if not settings.qr_enabled:
		frappe.throw(_("Dynamic QR is disabled in SSPL Paytm Settings"))
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer {0} not found").format(customer))
	if not settings.upi_account:
		frappe.throw(_("Set the UPI Account in SSPL Paytm Settings; QR receipts are received into it"))

	now = now_datetime()
	txn = frappe.get_doc(
		{
			"doctype": "SSPL Paytm Transaction",
			"order_id": f"RQR{now.strftime('%y%m%d%H%M%S%f')[:16]}",
			"amount": amount,
			"status": "Pending",
			"channel": "QR",
			"customer": customer,
			"customer_mobile": _valid_phone(mobile)
			or _valid_phone(frappe.db.get_value("Customer", customer, "mobile_no")),
			"link_description": (description or "").strip()[:140],
			"device_name": settings.qr_pos_id or re.sub(r"[^A-Za-z0-9_]", "_", frappe.session.user)[:20],
			"transaction_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
		}
	).insert(ignore_permissions=True)
	rb = _request_qr(settings, txn)
	return {**_txn_result(txn), "qr_image": rb.get("image") or _qr_png(rb.get("qrData"))}


@frappe.whitelist()
def get_receipt_qr(order_id):
	"""QR image of an unpaid receipt QR, to show it again after the page is reloaded."""
	_require_desk_user()
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if not _is_receipt(txn) or txn.channel != "QR" or not txn.qr_data:
		frappe.throw(_("No QR stored for {0}").format(order_id))
	return {**_txn_result(txn), "qr_image": _qr_png(txn.qr_data)}


def _is_receipt(txn):
	"""Receipt rows (payment link, receipt QR) belong to a customer, not a bill; a successful one
	creates its own Payment Entry. Cashier EDC/QR rows carry a sales_invoice instead."""
	return bool(txn.customer) and not txn.sales_invoice


def _qr_expires_in(channel, status, creation):
	if channel != "QR" or status != "Pending" or not creation:
		return 0
	age = (now_datetime() - frappe.utils.get_datetime(creation)).total_seconds()
	return max(0, int(QR_EXPIRY_SECONDS - age))


@frappe.whitelist()
def get_payment_links(limit=100, status=None):
	"""Payment links and receipt QRs, newest first, for the left panel of the Paytm receipt page."""
	_require_desk_user()
	filters = {"channel": ("in", PG_CHANNELS), "customer": ("is", "set"), "sales_invoice": ("is", "not set")}
	if status:
		filters["status"] = status
	rows = frappe.get_all(
		"SSPL Paytm Transaction",
		filters=filters,
		fields=[
			"order_id",
			"channel",
			"creation",
			"status",
			"amount",
			"customer",
			"customer_mobile",
			"link_description",
			"short_url",
			"payment_entry",
			"pay_method",
			"rrn",
			"paytm_txn_id",
			"result_message",
			"transaction_datetime",
			"owner",
		],
		order_by="creation desc",
		limit_page_length=frappe.utils.cint(limit) or 100,
	)
	for r in rows:
		r.expires_in = _qr_expires_in(r.channel, r.status, r.pop("creation"))
	return rows


@frappe.whitelist(methods=["POST"])
def retry_link_receipt(order_id):
	"""Create the Payment Entry for a paid link or receipt QR whose automatic receipt failed."""
	_require_desk_user()
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if not _is_receipt(txn) or txn.status != "Success":
		frappe.throw(_("Only a paid payment link or receipt QR can get a receipt"))
	if not txn.payment_entry:
		_make_receipt(txn)
		if not txn.payment_entry:
			frappe.db.commit()
			frappe.throw(_("Payment Entry could not be created; see Error Log"))
		txn.result_message = None
		txn.save(ignore_permissions=True)
	return _txn_result(txn)


def refresh_pending_links():
	"""Scheduler: re-read unpaid receipts from Paytm so one paid after the page was closed (and
	whose webhook was missed) still gets its receipt. One row failing never stops the rest."""
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	if not settings.enabled or not settings.merchant_id:
		return
	now = now_datetime()
	qr_since = frappe.utils.add_days(now, -RECEIPT_QR_REFRESH_DAYS)
	rows = frappe.get_all(
		"SSPL Paytm Transaction",
		filters={
			"channel": ("in", PG_CHANNELS),
			"customer": ("is", "set"),
			"sales_invoice": ("is", "not set"),
			"status": "Pending",
			"creation": (">=", frappe.utils.add_days(now, -LINK_REFRESH_DAYS)),
		},
		fields=["name", "channel", "creation"],
	)
	# Paytm has no QR void: a QR cancelled on the page can still be scanned until it expires
	rows += frappe.get_all(
		"SSPL Paytm Transaction",
		filters={
			"channel": "QR",
			"customer": ("is", "set"),
			"sales_invoice": ("is", "not set"),
			"status": "Cancelled",
			"creation": (">=", frappe.utils.add_to_date(now, seconds=-2 * QR_EXPIRY_SECONDS)),
		},
		fields=["name", "channel", "creation"],
	)
	for row in rows:
		order_id = row.name
		if row.channel == "QR" and row.creation < qr_since:
			# long past Paytm's QR expiry: stop asking
			frappe.db.set_value("SSPL Paytm Transaction", order_id, "status", "Cancelled")
			frappe.db.commit()
			continue
		try:
			_refresh_from_paytm(frappe.get_doc("SSPL Paytm Transaction", order_id))
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Paytm link refresh failed", message=frappe.get_traceback())


def _expire_link(txn):
	settings = _settings()
	try:
		res = _post_link(settings, LINK_EXPIRE_PATH, {"mid": settings.merchant_id, "linkId": txn.link_id})
	except Exception:
		frappe.log_error(title="Paytm link expire failed", message=frappe.get_traceback())
		return
	info = (res.get("body") or {}).get("resultInfo") or {}
	msg = info.get("resultMessage") or info.get("resultMsg") or info.get("resultStatus") or "no reply"
	txn.db_set("result_message", f"Expire: {msg}")


def _make_receipt(txn):
	"""Submit the Receipt Payment Entry for a paid link or receipt QR, once: the row lock makes the webhook and
	the page's polling agree on who creates it. Runs as the link's creator, since the webhook
	request is a Guest. A failure is logged and leaves the link Success without an entry."""
	from ssplbilling.api.paymentv2_api import _build_and_submit_payment_entry

	if frappe.db.get_value("SSPL Paytm Transaction", txn.name, "payment_entry", for_update=True):
		return
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	session_user = frappe.session.user
	frappe.db.savepoint("paytm_link_receipt")
	try:
		if session_user == "Guest":
			frappe.set_user(txn.owner)
		pe_name = _build_and_submit_payment_entry(
			{
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": txn.customer,
				"amount": txn.amount,
				"mop_account": settings.upi_account,
				# same fallback as the cashier desk when no Mode of Payment maps to the account
				"mode_of_payment": frappe.db.get_value(
					"Mode of Payment Account", {"default_account": settings.upi_account}, "parent"
				)
				or "Cash",
				"reference_no": txn.rrn or txn.paytm_txn_id or txn.order_id,
				"reference_date": frappe.utils.today(),
				"remarks": f"Paytm {'payment link' if txn.channel == 'Link' else 'UPI QR'} {txn.order_id}: "
				f"{txn.link_description or ''}".strip(),
			}
		)
		txn.payment_entry = pe_name
		try:
			from ssplbilling.api.automatic_entries_api import mirror_standalone_payment_entry

			frappe.db.savepoint("paytm_link_mirror")
			mirror_standalone_payment_entry(frappe.get_doc("Payment Entry", pe_name))
		except Exception:
			frappe.db.rollback(save_point="paytm_link_mirror")
			frappe.log_error(frappe.get_traceback(), "Automatic Entries: payment mirror failed")
	except Exception:
		frappe.db.rollback(save_point="paytm_link_receipt")
		frappe.log_error(title="Paytm link receipt failed", message=frappe.get_traceback())
		txn.result_message = _("Paid, but the Payment Entry could not be created; see Error Log")
	finally:
		if frappe.session.user != session_user:
			frappe.set_user(session_user)


@frappe.whitelist(methods=["POST"])
def get_status(order_id):
	"""Ask Paytm for the payment status and return the result for the cashier page."""
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if txn.status == "Pending":
		_refresh_from_paytm(txn)
	return _txn_result(txn)


@frappe.whitelist()
def cancel(order_id):
	"""Stop waiting on this order: clear the request off the card machine, then mark it Cancelled.
	A payment that completed before the void is kept (status re-read after the void)."""
	_require_desk_user()
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if txn.status == "Pending":
		_refresh_from_paytm(txn)
	if txn.status == "Pending" and txn.channel == "Link" and txn.link_id:
		_expire_link(txn)
		_refresh_from_paytm(txn)
	elif txn.status == "Pending" and not _is_pg(txn):
		_void_on_machine(txn)
		_refresh_from_paytm(txn)
	if txn.status == "Pending":
		txn.db_set("status", "Cancelled")
	return _txn_result(txn)


def _void_on_machine(txn):
	settings = _settings()
	body = {
		"paytmMid": settings.merchant_id,
		"paytmTid": txn.tid,
		"merchantTransactionId": txn.order_id,
		"transactionDateTime": txn.transaction_datetime,
	}
	try:
		res = _post(settings, EDC_VOID_PATH, body)
	except Exception:
		frappe.log_error(title="Paytm EDC void failed", message=frappe.get_traceback())
		return
	info = (res.get("body") or {}).get("resultInfo") or {}
	txn.db_set("result_message", f"Void: {info.get('resultMsg') or info.get('resultStatus') or 'no reply'}")


@frappe.whitelist(allow_guest=True, methods=["POST"])
def payment_webhook():
	"""Paytm payment notification. The payload is only used to find the order: the status
	is always re-read from Paytm's status API before anything is marked paid."""
	raw = frappe.request.get_data(as_text=True) or ""
	try:
		data = json.loads(raw) if raw.strip().startswith("{") else dict(frappe.form_dict)
	except ValueError:
		data = dict(frappe.form_dict)
	body = data.get("body") if isinstance(data.get("body"), dict) else data

	order_id = str(
		body.get("merchantTransactionId")
		or body.get("ORDERID")
		or body.get("orderId")
		or body.get("linkOrderId")
		or ""
	).strip()
	link_id = str(body.get("linkId") or body.get("LINKID") or "").strip()
	if (not order_id or not frappe.db.exists("SSPL Paytm Transaction", order_id)) and link_id:
		# a link payment may be reported under Paytm's own order id; find it by the link
		order_id = frappe.db.get_value("SSPL Paytm Transaction", {"link_id": link_id}, "name") or ""
	if not order_id or not frappe.db.exists("SSPL Paytm Transaction", order_id):
		# kept so a payload shape we do not recognise (e.g. a new link callback) can be traced
		frappe.log_error(title="Paytm webhook unknown order", message=raw[:5000])
		frappe.local.response["http_status_code"] = 404
		return {"status": "unknown order"}

	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	head = data.get("head") or {}
	checksum = head.get("checksum") or head.get("signature") or body.get("CHECKSUMHASH")
	if checksum:
		from paytmchecksum import verifySignature

		# PG JSON payloads are signed over the raw "body" text exactly as Paytm sent it
		if not _is_pg(txn) and "head" in data:
			signed = _ecr_sign_fields(body)
		elif "head" in data and '"body":' in raw:
			signed = raw[raw.index('"body":') + 7 : raw.rindex("}")].strip()
		else:
			signed = {k: v for k, v in body.items() if k != "CHECKSUMHASH"}
		if not verifySignature(signed, _key_for(settings, txn), checksum):
			frappe.log_error(title="Paytm webhook checksum mismatch", message=raw[:5000])

	# Cancelled rows are re-checked too: the customer can still pay on the machine after
	# the cashier stopped waiting, and that payment must not be silently dropped.
	# A receipt the customer failed to pay can still be retried and paid on the same order.
	if txn.status in ("Pending", "Cancelled") or (_is_receipt(txn) and txn.status == "Failed"):
		was_cancelled = txn.status == "Cancelled"
		_refresh_from_paytm(txn)
		if was_cancelled and txn.status == "Success":
			frappe.log_error(
				title="Paytm late payment on cancelled order",
				message=f"{txn.order_id} ({txn.sales_invoice}): Rs {txn.amount} paid after the cashier "
				"stopped waiting. Check the invoice is not paid twice.",
			)
	frappe.db.commit()
	return {"status": "ok"}


def _refresh_from_paytm(txn):
	if _is_pg(txn):
		return _refresh_qr(txn)
	settings = _settings()
	body = {
		"paytmMid": settings.merchant_id,
		"paytmTid": txn.tid,
		"transactionDateTime": txn.transaction_datetime,
		"merchantTransactionId": txn.order_id,
	}
	try:
		res = _post(settings, EDC_STATUS_PATH, body)
	except Exception:
		_log_status_failure(txn, "Paytm EDC status check failed")
		return

	rb = res.get("body") or {}
	info = rb.get("resultInfo") or {}
	status = (info.get("resultStatus") or "").upper()
	if status in ("SUCCESS", "S", "TXN_SUCCESS"):
		new_status = "Success"
	elif status in ("FAIL", "F", "FAILURE", "TXN_FAILURE"):
		new_status = "Failed"
	else:
		new_status = txn.status  # still waiting (Pending) or already Cancelled locally

	txn.pay_method = rb.get("payMethod") or rb.get("paymentMode") or txn.pay_method
	txn.paytm_txn_id = rb.get("acquirementId") or rb.get("txnId") or txn.paytm_txn_id
	txn.rrn = rb.get("retrievalReferenceNo") or rb.get("rrn") or rb.get("bankTxnId") or txn.rrn
	txn.auth_code = rb.get("authCode") or txn.auth_code
	if new_status == "Success" and rb.get("transactionAmount"):
		_check_amount(txn, flt(rb.get("transactionAmount")) / 100)
	_update_txn(txn, new_status, res, info.get("resultMsg"))


def _refresh_qr(txn):
	settings = _settings()
	try:
		res = _post_pg(settings, PG_STATUS_PATH, {"mid": settings.merchant_id, "orderId": txn.order_id})
	except Exception:
		_log_status_failure(txn, "Paytm QR status check failed")
		return

	rb = res.get("body") or {}
	info = rb.get("resultInfo") or {}
	status = (info.get("resultStatus") or "").upper()
	# Before the customer scans, Paytm can answer TXN_FAILURE ("Invalid Order Id") for an order
	# with no payment attempt yet; only a failure that carries a txnId is a real failed payment.
	message = info.get("resultMsg")
	if status == "TXN_SUCCESS":
		new_status = "Success"
	elif status == "TXN_FAILURE" and info.get("resultCode") == PG_ORDER_CLOSED and _is_receipt(txn):
		# Paytm closed the unpaid order at QR expiry: nothing failed, the customer just did not pay
		new_status, message = "Cancelled", _("QR expired unpaid")
	elif status == "TXN_FAILURE" and rb.get("txnId"):
		new_status = "Failed"
	else:
		new_status = txn.status

	txn.pay_method = rb.get("paymentMode") or txn.pay_method
	txn.paytm_txn_id = rb.get("txnId") or txn.paytm_txn_id
	txn.rrn = rb.get("bankTxnId") or txn.rrn
	if new_status == "Success" and rb.get("txnAmount"):
		_check_amount(txn, flt(rb.get("txnAmount")))  # rupees
	_update_txn(txn, new_status, res, message)


def _log_status_failure(txn, title):
	# The page polls every few seconds; log only the first failure per order
	cache_key = f"paytm_status_failed:{txn.order_id}"
	if not frappe.cache.get_value(cache_key):
		frappe.cache.set_value(cache_key, 1, expires_in_sec=3600)
		frappe.log_error(title=title, message=frappe.get_traceback())


def _check_amount(txn, paid):
	if abs(paid - flt(txn.amount)) > 0.01:
		frappe.log_error(
			title="Paytm amount mismatch",
			message=f"{txn.order_id}: requested {txn.amount}, Paytm reports {paid}",
		)
		txn.amount = paid


def _update_txn(txn, status, response, message=None):
	was_open = txn.status in ("Pending", "Cancelled")
	txn.status = status
	txn.response = json.dumps(response, indent=1, default=str)
	if message:
		txn.result_message = message
	if status == "Success" and _is_receipt(txn) and not txn.payment_entry:
		_make_receipt(txn)
	txn.save(ignore_permissions=True)
	if was_open and status in ("Success", "Failed"):
		frappe.publish_realtime(
			"paytm_payment_update", _txn_result(txn), user=txn.owner, after_commit=True
		)


def _txn_result(txn):
	method = (txn.pay_method or "").upper()
	return {
		"order_id": txn.order_id,
		"channel": txn.channel or "EDC",
		"sales_invoice": txn.sales_invoice,
		"status": txn.status,
		"amount": flt(txn.amount),
		"mode": "card" if not _is_pg(txn) and method in CARD_PAY_METHODS else "upi",
		"pay_method": txn.pay_method,
		"reference_no": txn.rrn or txn.paytm_txn_id or txn.auth_code or txn.order_id,
		"message": txn.result_message,
		"customer": txn.customer,
		"short_url": txn.short_url,
		"payment_entry": txn.payment_entry,
		"expires_in": _qr_expires_in(txn.channel, txn.status, txn.creation),
	}
