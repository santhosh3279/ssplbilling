import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import add_days, getdate, now


@frappe.whitelist()
def get_submitted_invoice(invoice_no):
	"""Fetch details of a submitted invoice (docstatus=1).

	Searches Sales Invoice first, then Purchase Invoice.
	Throws an informative error if draft, cancelled, or not found.
	"""
	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please enter an invoice number.")

	# Search in Sales Invoice
	si = frappe.db.get_value(
		"Sales Invoice",
		{"name": invoice_no},
		[
			"name",
			"docstatus",
			"posting_date",
			"posting_time",
			"customer",
			"customer_name",
			"grand_total",
			"outstanding_amount",
			"company",
			"due_date",
		],
		as_dict=True,
	)

	doctype = "Sales Invoice"
	doc_data = si

	# If not found in Sales Invoice, search in Purchase Invoice
	if not doc_data:
		pi = frappe.db.get_value(
			"Purchase Invoice",
			{"name": invoice_no},
			[
				"name",
				"docstatus",
				"posting_date",
				"posting_time",
				"supplier as customer",
				"supplier_name as customer_name",
				"grand_total",
				"outstanding_amount",
				"company",
				"due_date",
			],
			as_dict=True,
		)
		if pi:
			doctype = "Purchase Invoice"
			doc_data = pi

	if not doc_data:
		frappe.throw(f"Invoice '{invoice_no}' was not found.")

	# Check submission status
	if doc_data.docstatus == 0:
		frappe.throw(
			f"Invoice '{doc_data.name}' is a Draft (not submitted). "
			"You can edit the date of draft invoices directly in the invoice form."
		)
	elif doc_data.docstatus == 2:
		frappe.throw(f"Invoice '{doc_data.name}' is Cancelled. Only submitted invoices can be modified.")
	elif doc_data.docstatus != 1:
		frappe.throw(f"Invoice '{doc_data.name}' is not in submitted state (docstatus={doc_data.docstatus}).")

	# Fetch items preview
	item_doctype = "Sales Invoice Item" if doctype == "Sales Invoice" else "Purchase Invoice Item"
	items = frappe.db.sql(
		f"""SELECT item_code, item_name, qty, uom, rate, amount
		   FROM `tab{item_doctype}`
		   WHERE parent = %(parent)s
		   ORDER BY idx ASC LIMIT 10""",
		{"parent": doc_data.name},
		as_dict=True,
	)
	total_items_count = frappe.db.count(item_doctype, {"parent": doc_data.name})

	return {
		"doctype": doctype,
		"name": doc_data.name,
		"party": doc_data.customer,
		"party_name": doc_data.customer_name,
		"posting_date": str(doc_data.posting_date),
		"posting_time": str(doc_data.posting_time or ""),
		"due_date": str(doc_data.due_date) if doc_data.due_date else "",
		"grand_total": doc_data.grand_total,
		"outstanding_amount": doc_data.outstanding_amount,
		"company": doc_data.company,
		"item_count": total_items_count,
		"items": items,
	}


@frappe.whitelist()
def modify_submitted_bill_date(invoice_no, new_date, doctype="Sales Invoice"):
	"""Directly modifies the bill date (posting_date) in the DB for a submitted invoice.

	Updates Sales/Purchase Invoice, GL Entry, Payment Ledger Entry, Stock Ledger Entry,
	and Serial/Batch bundle tables consistently.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify invoices.", frappe.PermissionError)

	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please enter an invoice number.")
	if not new_date:
		frappe.throw("Please select a new bill date.")

	try:
		new_date_obj = getdate(new_date)
		new_date_str = str(new_date_obj)
	except Exception:
		frappe.throw(f"Invalid date format: {new_date}")

	# Determine doctype if not recognized or verify
	if doctype not in ("Sales Invoice", "Purchase Invoice"):
		if frappe.db.exists("Sales Invoice", invoice_no):
			doctype = "Sales Invoice"
		elif frappe.db.exists("Purchase Invoice", invoice_no):
			doctype = "Purchase Invoice"
		else:
			frappe.throw(f"Document '{invoice_no}' does not exist.")

	doc = frappe.get_doc(doctype, invoice_no)
	if doc.docstatus != 1:
		frappe.throw(
			f"Invoice '{invoice_no}' is not in submitted state (docstatus={doc.docstatus}). "
			"Only submitted invoices can be modified."
		)

	old_date = doc.posting_date
	old_date_str = str(old_date)
	if old_date_str == new_date_str:
		return {
			"status": "unchanged",
			"name": invoice_no,
			"posting_date": new_date_str,
			"message": f"Bill date for {invoice_no} is already {new_date_str}.",
		}

	# Check permissions
	if not (frappe.has_permission(doctype, "write") or frappe.has_permission(doctype, "cancel")):
		frappe.throw(f"You do not have permission to modify {doctype}.", frappe.PermissionError)

	# Calculate fiscal year for the new date
	try:
		fy = get_fiscal_year(new_date_str, company=doc.company)[0]
	except Exception:
		fy = None

	# Calculate due date adjustment
	if doc.due_date and old_date:
		diff_days = (getdate(doc.due_date) - getdate(old_date)).days
		new_due_date = add_days(new_date_str, diff_days)
	else:
		new_due_date = new_date_str

	now_time = now()
	posting_time_str = str(doc.posting_time or "00:00:00")
	if len(posting_time_str.split(":")) == 2:
		posting_time_str += ":00"
	new_posting_datetime = f"{new_date_str} {posting_time_str}"

	# 1. Update Invoice Document in DB
	inv_update = {
		"posting_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if doctype == "Purchase Invoice" and hasattr(doc, "bill_date"):
		inv_update["bill_date"] = new_date_str

	frappe.db.set_value(doctype, invoice_no, inv_update, update_modified=False)

	# If Sales Invoice, update child clearance_date if matching old date
	if doctype == "Sales Invoice":
		frappe.db.sql(
			"""UPDATE `tabSales Invoice Payment`
			   SET clearance_date = %(new_date)s
			   WHERE parent = %(invoice_no)s AND clearance_date = %(old_date)s""",
			{"new_date": new_date_str, "invoice_no": invoice_no, "old_date": old_date_str},
		)

	# 2. Update GL Entry
	gl_updates = {
		"posting_date": new_date_str,
		"transaction_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if fy:
		gl_updates["fiscal_year"] = fy
	gl_set_sql = ", ".join([f"`{k}` = %({k})s" for k in gl_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabGL Entry`
		   SET {gl_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**gl_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 3. Update Payment Ledger Entry
	ple_updates = {
		"posting_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	ple_set_sql = ", ".join([f"`{k}` = %({k})s" for k in ple_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabPayment Ledger Entry`
		   SET {ple_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**ple_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 4. Update Stock Ledger Entry
	sle_updates = {
		"posting_date": new_date_str,
		"posting_datetime": new_posting_datetime,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if fy:
		sle_updates["fiscal_year"] = fy
	sle_set_sql = ", ".join([f"`{k}` = %({k})s" for k in sle_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabStock Ledger Entry`
		   SET {sle_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**sle_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 5. Update Serial and Batch Bundle
	frappe.db.sql(
		"""UPDATE `tabSerial and Batch Bundle`
		   SET posting_datetime = %(posting_datetime)s,
		       modified = %(modified)s,
		       modified_by = %(modified_by)s
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{
			"posting_datetime": new_posting_datetime,
			"modified": now_time,
			"modified_by": frappe.session.user,
			"doctype": doctype,
			"invoice_no": invoice_no,
		},
	)

	# Clear cached document
	frappe.clear_document_cache(doctype, invoice_no)

	# Audit trail comment
	try:
		doc.add_comment(
			"Info",
			f"Bill date modified from {old_date_str} to {new_date_str} by {frappe.session.user}",
		)
	except Exception:
		pass

	frappe.db.commit()

	return {
		"status": "success",
		"name": invoice_no,
		"doctype": doctype,
		"old_date": old_date_str,
		"new_date": new_date_str,
		"message": f"Bill date for {invoice_no} changed from {old_date_str} to {new_date_str} successfully.",
	}
