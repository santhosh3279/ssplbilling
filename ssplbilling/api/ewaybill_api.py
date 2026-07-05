import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

ALLOWED_DOCTYPES = ("Sales Invoice", "Quotation")


@frappe.whitelist()
def cancel_eway_bill(doctype, docname, reason, remark=None):
	"""
	Cancel the e-Way Bill linked to a Sales Invoice or Quotation via the NIC API.

	Works for both doctypes (india_compliance's own cancel_e_waybill only supports
	its native doctypes, not Quotation). Mirrors its behaviour: calls CANEWB,
	marks the e-Waybill Log cancelled, clears `ewaybill` on the document and sets
	`e_waybill_status` to Cancelled so a fresh e-Way Bill can be generated.
	"""
	if doctype not in ALLOWED_DOCTYPES:
		frappe.throw(_("e-Way Bill cancellation is only supported for: {0}").format(", ".join(ALLOWED_DOCTYPES)))

	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")

	ewaybill_no = doc.get("ewaybill")
	if not ewaybill_no:
		frappe.throw(_("No e-Way Bill found on {0} {1}.").format(_(doctype), docname))

	from india_compliance.gst_india.constants.e_waybill import CANCEL_REASON_CODES

	if reason not in CANCEL_REASON_CODES:
		frappe.throw(_("Invalid cancellation reason: {0}").format(reason))

	# NIC allows cancellation only within 24 hours of generation
	created_on = frappe.db.get_value("e-Waybill Log", ewaybill_no, "created_on")
	if created_on and add_to_date(get_datetime(created_on), days=1, as_datetime=True) < now_datetime():
		frappe.throw(_("e-Way Bill can be cancelled only within 24 hours of its generation."))

	from india_compliance.gst_india.utils import parse_datetime
	from india_compliance.gst_india.utils.e_waybill import EWaybillAPI, log_and_process_e_waybill

	company_gstin = doc.get("company_gstin") or frappe.get_cached_value("Company", doc.company, "gstin")

	try:
		api = EWaybillAPI.create(company_gstin=company_gstin)
		result = api.cancel_e_waybill(
			{
				"ewbNo": ewaybill_no,
				"cancelRsnCode": CANCEL_REASON_CODES[reason],
				"cancelRmrk": remark or reason,
			}
		)

		# error_code 312: already cancelled on the portal — still mark cancelled locally
		cancelled_on = (
			now_datetime()
			if result.error_code == "312"
			else parse_datetime(result.cancelDate, day_first=True)
		)

		log_and_process_e_waybill(
			doc,
			{
				"name": ewaybill_no,
				"is_cancelled": 1,
				"cancel_reason_code": CANCEL_REASON_CODES[reason],
				"cancel_remark": remark or reason,
				"cancelled_on": cancelled_on,
			},
		)

		doc.db_set({"ewaybill": "", "e_waybill_status": "Cancelled"})

		return {
			"e_waybill_status": "Cancelled",
			"message": _("e-Way Bill {0} cancelled successfully.").format(ewaybill_no),
		}

	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="e-Way Bill Cancellation Failed")
		raise
