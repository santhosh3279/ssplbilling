import frappe


def execute():
	"""Index for get_all_ledgers' "last invoice date per customer" query.

	With (customer, docstatus, posting_date) MariaDB answers MAX(posting_date) ... GROUP BY customer
	from the index alone instead of reading every invoice row."""
	frappe.db.add_index("Sales Invoice", ["customer", "docstatus", "posting_date"])
