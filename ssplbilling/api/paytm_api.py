"""Paytm EDC (card machine) integration for the cashier desk.

Flow: cashier presses "POS" -> send_to_device() pushes the amount to the machine's TID
-> customer pays on the machine (UPI QR or card) -> Paytm calls payment_webhook() and/or
the page polls get_status() -> the result fills the UPI or Card box; the cashier submits.

Dynamic UPI QR (channel "QR"): create_qr() asks Paytm PG for a QR bound to an order id and
amount, the cashier page shows it, and the same get_status()/webhook path confirms the payment
through the PG v3 order status API.

Nothing here creates a Payment Entry; submit_invoice_with_payment() still does that.
"""

import base64
import io
import json
import re

import frappe
import requests
from frappe import _
from frappe.utils import flt, now_datetime

# Matches Paytm's ECR sample (head.version 3.1, amount in paise). The production host is the older paytm.in one, which does answer ECR requests.
EDC_BASE_URL = {
	"Staging": "https://securestage.paytmpayments.com",
	"Production": "https://securegw-edc.paytm.in",
}
EDC_SALE_PATH = "/ecr/payment/request"
EDC_STATUS_PATH = "/ecr/V2/payment/status"
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

CARD_PAY_METHODS = ("CARD", "CREDIT_CARD", "DEBIT_CARD", "EMI", "CC", "DC")


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


def _key_for(settings, txn):
	return _pg_key(settings) if txn.channel == "QR" else _signing_key(settings)


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


def _ecr_sign_fields(body):
	# Nested objects such as merchantExtendedInfo are signed as if their fields were top level
	# (verified: Paytm accepts PaymentMode signed flat and rejects every JSON-string form)
	fields = {}
	for k, v in body.items():
		if isinstance(v, dict):
			fields.update({ik: str(iv) for ik, iv in v.items()})
		else:
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


def _device_for(settings, tid):
	for row in settings.devices:
		if row.enabled and row.tid == tid:
			return row
	frappe.throw(_("Card machine with TID {0} is not configured or disabled").format(tid))


@frappe.whitelist()
def get_devices():
	"""Enabled card machines for the cashier page; never returns any key."""
	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	if not settings.enabled:
		return {"enabled": False, "qr_enabled": False, "devices": []}
	return {
		"enabled": True,
		"qr_enabled": bool(settings.qr_enabled),
		"devices": [
			{"device_name": d.device_name, "tid": d.tid, "user": d.user}
			for d in settings.devices
			if d.enabled
		],
	}


@frappe.whitelist()
def send_to_device(invoice_name, amount, tid, pay_mode="QR"):
	"""Push the amount to the card machine; returns the order id to poll.
	pay_mode QR opens the machine on the UPI QR, CARD on card entry."""
	settings = _settings()
	if pay_mode not in ("QR", "CARD"):
		frappe.throw(_("Payment mode must be QR or CARD"))
	device = _device_for(settings, tid)
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice_name))

	now = now_datetime()
	# ECR ids are plain alphanumeric in Paytm's sample; invoice series carry "-" and "/"
	order_id = f"{re.sub(r'[^A-Za-z0-9]', '', invoice_name)[:30]}{now.strftime('%y%m%d%H%M%S%f')[:15]}"
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
		"merchantReferenceNo": re.sub(r"[^A-Za-z0-9]", "", invoice_name),
		"transactionAmount": str(int(round(amount * 100))),  # paise
		"merchantExtendedInfo": {**EDC_EXTENDED_INFO, "paymentMode": pay_mode},
	}
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
	order_id = f"{re.sub(r'[^A-Za-z0-9_@-]', '_', invoice_name)[:40]}-{now.strftime('%H%M%S%f')[:9]}"
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

	body = {
		"mid": settings.merchant_id,
		"orderId": order_id,
		"amount": f"{amount:.2f}",  # rupees, unlike the EDC paise amount
		"businessType": "UPI_QR_CODE",
		"posId": pos_id,
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

	_update_txn(txn, "Pending", stored, info.get("resultMsg"))
	return {
		"order_id": order_id,
		"status": "Pending",
		"qr_image": rb.get("image") or _qr_png(rb.get("qrData")),
		"qr_data": rb.get("qrData"),
	}


def _qr_png(data):
	"""Base64 PNG of the UPI string, for when Paytm returns qrData without an image."""
	from pyqrcode import create as qrcreate

	buf = io.BytesIO()
	qrcreate(data).png(buf, scale=8, quiet_zone=2)
	return base64.b64encode(buf.getvalue()).decode()


@frappe.whitelist(methods=["POST"])
def get_status(order_id):
	"""Ask Paytm for the payment status and return the result for the cashier page."""
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if txn.status == "Pending":
		_refresh_from_paytm(txn)
	return _txn_result(txn)


@frappe.whitelist()
def cancel(order_id):
	"""Stop waiting on this order. Does not void a payment already made on the machine."""
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if txn.status == "Pending":
		_refresh_from_paytm(txn)
	if txn.status == "Pending":
		txn.db_set("status", "Cancelled")
	return _txn_result(txn)


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

	order_id = (
		body.get("merchantTransactionId") or body.get("ORDERID") or body.get("orderId") or ""
	).strip()
	if not order_id or not frappe.db.exists("SSPL Paytm Transaction", order_id):
		frappe.local.response["http_status_code"] = 404
		return {"status": "unknown order"}

	settings = frappe.get_cached_doc("SSPL Paytm Settings")
	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	head = data.get("head") or {}
	checksum = head.get("checksum") or head.get("signature") or body.get("CHECKSUMHASH")
	if checksum:
		from paytmchecksum import verifySignature

		# PG JSON payloads are signed over the raw "body" text exactly as Paytm sent it
		if txn.channel != "QR" and "head" in data:
			signed = _ecr_sign_fields(body)
		elif "head" in data and '"body":' in raw:
			signed = raw[raw.index('"body":') + 7 : raw.rindex("}")].strip()
		else:
			signed = {k: v for k, v in body.items() if k != "CHECKSUMHASH"}
		if not verifySignature(signed, _key_for(settings, txn), checksum):
			frappe.log_error(title="Paytm webhook checksum mismatch", message=raw[:5000])

	# Cancelled rows are re-checked too: the customer can still pay on the machine after
	# the cashier stopped waiting, and that payment must not be silently dropped.
	if txn.status in ("Pending", "Cancelled"):
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
	if txn.channel == "QR":
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
	if status == "TXN_SUCCESS":
		new_status = "Success"
	elif status == "TXN_FAILURE" and rb.get("txnId"):
		new_status = "Failed"
	else:
		new_status = txn.status

	txn.pay_method = rb.get("paymentMode") or txn.pay_method
	txn.paytm_txn_id = rb.get("txnId") or txn.paytm_txn_id
	txn.rrn = rb.get("bankTxnId") or txn.rrn
	if new_status == "Success" and rb.get("txnAmount"):
		_check_amount(txn, flt(rb.get("txnAmount")))  # rupees
	_update_txn(txn, new_status, res, info.get("resultMsg"))


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
		"mode": "card" if txn.channel != "QR" and method in CARD_PAY_METHODS else "upi",
		"pay_method": txn.pay_method,
		"reference_no": txn.rrn or txn.paytm_txn_id or txn.auth_code or txn.order_id,
		"message": txn.result_message,
	}
