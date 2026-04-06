import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_daily_reports(report_type, date):
	"""
	Returns a list of documents for a specific date and type.
	report_type: 'Invoice', 'Payment', 'Journal', 'Quotation'
	"""
	if not date:
		date = frappe.utils.today()

	if report_type == 'Invoice':
		return frappe.get_all(
			"Sales Invoice",
			filters={"posting_date": date, "docstatus": ["<", 2]},
			fields=["name", "customer_name", "grand_total", "docstatus", "posting_time"],
			order_by="posting_time desc"
		)
	
	elif report_type == 'Payment':
		return frappe.get_all(
			"Payment Entry",
			filters={"posting_date": date, "docstatus": ["<", 2]},
			fields=["name", "party_name", "paid_amount", "received_amount", "mode_of_payment", "docstatus"],
			order_by="creation desc"
		)

	elif report_type == 'Journal':
		return frappe.get_all(
			"Journal Entry",
			filters={"posting_date": date, "docstatus": ["<", 2]},
			fields=["name", "voucher_type", "total_debit", "docstatus", "user_remark"],
			order_by="creation desc"
		)

	elif report_type == 'Quotation':
		return frappe.get_all(
			"Quotation",
			filters={"transaction_date": date, "docstatus": ["<", 2]},
			fields=["name", "customer_name", "grand_total", "docstatus", "status"],
			order_by="creation desc"
		)

	return []
