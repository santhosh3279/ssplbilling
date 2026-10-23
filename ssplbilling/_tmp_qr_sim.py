import frappe, json, time
from ssplbilling.api import paytm_api

def run():
	# wait until the first test QR is 11+ minutes old (created 08:45:54)
	target = frappe.utils.get_datetime("2026-10-23 08:57:00")
	while frappe.utils.now_datetime() < target:
		time.sleep(10)
	s = paytm_api._settings()
	print("NOW", frappe.utils.now_datetime())
	for oid in ("RQR2610230845540579", "RQR2610230848367635"):
		b = paytm_api._post_pg(s, paytm_api.PG_STATUS_PATH, {"mid": s.merchant_id, "orderId": oid}).get("body") or {}
		print(oid, frappe.db.get_value("SSPL Paytm Transaction", oid, ["status", "payment_entry"]), json.dumps(b.get("resultInfo")), b.get("txnAmount"))
