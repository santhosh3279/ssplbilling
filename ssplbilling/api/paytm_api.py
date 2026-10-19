"""Paytm EDC (card machine) integration for the cashier desk.

Flow: cashier presses "POS" -> send_to_device() pushes the amount to the machine's TID
-> customer pays on the machine (UPI QR or card) -> Paytm calls payment_webhook() and/or
the page polls get_status() -> the result fills the UPI or Card box; the cashier submits.

Nothing here creates a Payment Entry; submit_invoice_with_payment() still does that.
"""

import json

import frappe
import requests
from frappe import _
from frappe.utils import flt, now_datetime

# TODO: verify against the Paytm EDC / ECR integration document issued to the merchant —
# base URLs, paths, channelId and the amount unit (paise) are from Paytm's public EDC docs.
EDC_BASE_URL = {
	"Staging": "https://securegw-stage.paytm.in",
	"Production": "https://securegw-edc.paytm.in",
}
EDC_SALE_PATH = "/ecr/payment/request"
EDC_STATUS_PATH = "/ecr/V2/payment/status"
EDC_CHANNEL_ID = "EDC"
EDC_PAYMENT_MODE = "ALL"  # machine lets the customer choose UPI QR or card
REQUEST_TIMEOUT = 20

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


def _post(settings, path, body):
	"""Sign the exact body string and send those same bytes, so Paytm's checksum matches."""
	from paytmchecksum import generateSignature

	body_str = json.dumps(body, separators=(",", ":"))
	head = {
		"requestTimeStamp": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
		"channelId": EDC_CHANNEL_ID,
		"checksum": generateSignature(body_str, _signing_key(settings)),
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
		return {"enabled": False, "devices": []}
	return {
		"enabled": True,
		"devices": [
			{"device_name": d.device_name, "tid": d.tid, "user": d.user}
			for d in settings.devices
			if d.enabled
		],
	}


@frappe.whitelist()
def send_to_device(invoice_name, amount, tid):
	"""Push the amount to the card machine; returns the order id to poll."""
	settings = _settings()
	device = _device_for(settings, tid)
	amount = flt(amount, 2)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than 0"))
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Sales Invoice {0} not found").format(invoice_name))

	now = now_datetime()
	order_id = f"{invoice_name}-{now.strftime('%H%M%S%f')[:9]}"
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
		"merchantReferenceNo": invoice_name,
		"transactionAmount": str(int(round(amount * 100))),  # paise
		"merchantExtendedInfo": {"paymentMode": EDC_PAYMENT_MODE},
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
	checksum = (data.get("head") or {}).get("checksum") or body.get("CHECKSUMHASH")
	if checksum:
		from paytmchecksum import verifySignature

		signed = json.dumps(body, separators=(",", ":")) if "head" in data else {
			k: v for k, v in body.items() if k != "CHECKSUMHASH"
		}
		if not verifySignature(signed, _signing_key(settings), checksum):
			frappe.log_error(title="Paytm webhook checksum mismatch", message=raw[:5000])

	txn = frappe.get_doc("SSPL Paytm Transaction", order_id)
	if txn.status == "Pending":
		_refresh_from_paytm(txn)
	frappe.db.commit()
	return {"status": "ok"}


def _refresh_from_paytm(txn):
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
		frappe.log_error(title="Paytm EDC status check failed", message=frappe.get_traceback())
		return

	rb = res.get("body") or {}
	info = rb.get("resultInfo") or {}
	status = (info.get("resultStatus") or "").upper()
	if status in ("SUCCESS", "S", "TXN_SUCCESS"):
		new_status = "Success"
	elif status in ("FAIL", "F", "FAILURE", "TXN_FAILURE"):
		new_status = "Failed"
	else:
		new_status = "Pending"

	txn.pay_method = rb.get("payMethod") or rb.get("paymentMode") or txn.pay_method
	txn.paytm_txn_id = rb.get("acquirementId") or rb.get("txnId") or txn.paytm_txn_id
	txn.rrn = rb.get("retrievalReferenceNo") or rb.get("rrn") or rb.get("bankTxnId") or txn.rrn
	txn.auth_code = rb.get("authCode") or txn.auth_code
	if new_status == "Success" and rb.get("transactionAmount"):
		paid = flt(rb.get("transactionAmount")) / 100
		if abs(paid - flt(txn.amount)) > 0.01:
			frappe.log_error(
				title="Paytm amount mismatch",
				message=f"{txn.order_id}: requested {txn.amount}, Paytm reports {paid}",
			)
			txn.amount = paid
	_update_txn(txn, new_status, res, info.get("resultMsg"))


def _update_txn(txn, status, response, message=None):
	was_pending = txn.status == "Pending"
	txn.status = status
	txn.response = json.dumps(response, indent=1, default=str)
	if message:
		txn.result_message = message
	txn.save(ignore_permissions=True)
	if was_pending and status != "Pending":
		frappe.publish_realtime(
			"paytm_payment_update", _txn_result(txn), user=txn.owner, after_commit=True
		)


def _txn_result(txn):
	method = (txn.pay_method or "").upper()
	return {
		"order_id": txn.order_id,
		"sales_invoice": txn.sales_invoice,
		"status": txn.status,
		"amount": flt(txn.amount),
		"mode": "card" if method in CARD_PAY_METHODS else "upi",
		"pay_method": txn.pay_method,
		"reference_no": txn.rrn or txn.paytm_txn_id or txn.auth_code or txn.order_id,
		"message": txn.result_message,
	}
