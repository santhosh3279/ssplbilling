import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import add_days, getdate, now


SUPPORTED_DOCTYPES = ("Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order", "Purchase Order")
INVOICE_DOCTYPES = ("Sales Invoice", "Purchase Invoice")


def _validate_doctype(doctype):
	if doctype not in SUPPORTED_DOCTYPES:
		frappe.throw("Select a Sales/Purchase Invoice, Quotation, Sales Order, or Purchase Order.")
	return doctype


def _check_authenticated():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify bills.", frappe.PermissionError)


def _submitted_mirror_name(doctype, invoice_no, company, linked_name=None):
	"""Find an existing submitted mirror in a different company."""
	if doctype not in INVOICE_DOCTYPES:
		return None
	if doctype == "Sales Invoice":
		from ssplbilling.api.automatic_entries_api import mirror_name_for
		linked_name = mirror_name_for(invoice_no)
	if not linked_name:
		return None
	mirror = frappe.db.get_value(doctype, linked_name, ["name", "company", "docstatus"], as_dict=True)
	if mirror and mirror.company != company and mirror.docstatus == 1:
		return mirror.name
	return None


def _linked_payment_vouchers(doc):
	if doc.doctype == "Quotation":
		return set()
	if doc.doctype in ("Sales Order", "Purchase Order"):
		# Order advances are linked through references rather than invoice PLEs.
		payments = frappe.get_all("Payment Entry Reference", filters={
			"reference_doctype": doc.doctype, "reference_name": doc.name, "docstatus": 1,
		}, pluck="parent")
		journals = frappe.get_all("Journal Entry Account", filters={
			"reference_type": doc.doctype, "reference_name": doc.name, "docstatus": 1,
		}, pluck="parent")
		return {("Payment Entry", name) for name in payments} | {("Journal Entry", name) for name in journals}
	from erpnext.accounts.doctype.unreconcile_payment.unreconcile_payment import (
		get_linked_payments_for_doc,
	)

	linked = get_linked_payments_for_doc(company=doc.company, doctype=doc.doctype, docname=doc.name)
	vouchers = {(row.reference_doctype, row.reference_name) for row in linked}
	unsupported = sorted({voucher_type for voucher_type, _ in vouchers} - {"Payment Entry", "Journal Entry"})
	if unsupported:
		frappe.throw(f"Cannot unlink allocations from {', '.join(unsupported)} automatically. Please unreconcile them first.")
	return vouchers


def _unlink_payments_and_cancel(doc, vouchers):
	for voucher_type, voucher_no in sorted(vouchers):
		unreconcile = frappe.new_doc("Unreconcile Payment")
		unreconcile.company = doc.company
		unreconcile.voucher_type = voucher_type
		unreconcile.voucher_no = voucher_no
		unreconcile.add_references()
		unreconcile.allocations = [
			row for row in unreconcile.allocations
			if row.reference_doctype == doc.doctype and row.reference_name == doc.name
		]
		if not unreconcile.allocations:
			frappe.throw(f"Could not unlink payment {voucher_no} from {doc.name}. Please refresh and try again.")
		unreconcile.insert()
		unreconcile.submit()

	doc.reload()
	doc.cancel()


def _archive_cancelled_invoice(doc):
	"""Free the original number while preserving cancelled records and their links."""
	if doc.docstatus != 2:
		frappe.throw("Only cancelled invoices can be archived.")
	original_name = doc.name
	suffix = 1
	while frappe.db.exists(doc.doctype, f"{original_name}-{suffix}"):
		suffix += 1
	archived_name = frappe.rename_doc(
		doc.doctype, original_name, f"{original_name}-{suffix}",
		force=True, show_alert=False,
	)
	return frappe.get_doc(doc.doctype, archived_name)


@frappe.whitelist()
def get_submitted_invoice(invoice_no, doctype=None):
	"""Fetch a submitted billing document; explicit type avoids number collisions."""
	_check_authenticated()
	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please select a bill.")
	if doctype:
		_validate_doctype(doctype)
	else:
		matches = [kind for kind in SUPPORTED_DOCTYPES if frappe.db.exists(kind, invoice_no)]
		if len(matches) > 1:
			frappe.throw("This bill number exists in multiple document types. Select it from the bill palette.")
		doctype = matches[0] if matches else None
	if not doctype or not frappe.db.exists(doctype, invoice_no):
		frappe.throw(f"Bill '{invoice_no}' was not found.")

	doc = frappe.get_doc(doctype, invoice_no)
	doc.check_permission("read")
	if doc.docstatus != 1:
		frappe.throw(f"Bill '{invoice_no}' must be submitted. Draft and cancelled documents cannot be modified here.")
	date_field = "posting_date" if doctype in INVOICE_DOCTYPES else "transaction_date"
	party = doc.get("supplier") or doc.get("customer") or doc.get("party_name")
	party_name = doc.get("supplier_name") or doc.get("customer_name") or party
	items = doc.get("items") or []
	return {
		"doctype": doctype,
		"name": doc.name,
		"party": party,
		"party_name": party_name,
		"posting_date": str(doc.get(date_field)),
		"date_field": date_field,
		"posting_time": str(doc.get("posting_time") or ""),
		"due_date": str(doc.get("due_date") or ""),
		"grand_total": doc.get("grand_total") or 0,
		"outstanding_amount": doc.get("outstanding_amount") or 0,
		"company": doc.company,
		"mirror_invoice": _submitted_mirror_name(doctype, doc.name, doc.company, doc.get("custom_mirrored")),
		"item_count": len(items),
		"items": [{field: item.get(field) for field in ("item_code", "item_name", "qty", "uom", "rate", "amount")} for item in items[:10]],
	}


@frappe.whitelist()
def move_submitted_to_draft(invoice_no, doctype="Sales Invoice"):
	"""Unlink payments, cancel a submitted invoice, and create an amended draft."""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify invoices.", frappe.PermissionError)
	_validate_doctype(doctype)

	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please enter an invoice number.")

	doc = frappe.get_doc(doctype, invoice_no)
	doc.check_permission("cancel")
	doc.check_permission("write")
	if doc.docstatus != 1:
		frappe.throw(f"Invoice '{invoice_no}' must be submitted to move it to draft mode.")

	mirror_name = _submitted_mirror_name(doctype, doc.name, doc.company, doc.get("custom_mirrored"))
	mirror = frappe.get_doc(doctype, mirror_name) if mirror_name else None
	if mirror:
		mirror.check_permission("cancel")
		mirror.check_permission("write")

	# Check both sets of links before mutating either invoice.
	mirror_vouchers = _linked_payment_vouchers(mirror) if mirror else set()
	vouchers = _linked_payment_vouchers(doc)
	if mirror:
		_unlink_payments_and_cancel(mirror, mirror_vouchers)
	_unlink_payments_and_cancel(doc, vouchers)
	if mirror:
		mirror = _archive_cancelled_invoice(mirror)
	doc = _archive_cancelled_invoice(doc)
	amended = frappe.copy_doc(doc)
	amended.amended_from = doc.name
	amended.docstatus = 0
	amended.name = None
	if amended.meta.has_field("advances"):
		amended.set("advances", [])
	if doctype == "Purchase Invoice" and frappe.get_meta(doctype).has_field("custom_mirrored"):
		amended.set("custom_mirrored", None)
	if hasattr(amended, "set_posting_time"):
		amended.set_posting_time = 0
	# Explicit naming bypasses the usual amendment suffix. The cancelled record
	# remains available under its archived name for amendment and ledger history.
	amended.insert(set_name=invoice_no)

	return {
		"status": "draft_created",
		"cancelled_invoice": doc.name,
		"draft_invoice": amended.name,
		"doctype": doctype,
		"cancelled_mirror": mirror.name if mirror else None,
		"unlinked_payments": len(vouchers) + len(mirror_vouchers),
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

	_validate_doctype(doctype)

	doc = frappe.get_doc(doctype, invoice_no)
	if doc.docstatus != 1:
		frappe.throw(
			f"Invoice '{invoice_no}' is not in submitted state (docstatus={doc.docstatus}). "
			"Only submitted invoices can be modified."
		)

	if doctype not in INVOICE_DOCTYPES:
		return _modify_transaction_date(doc, new_date_str)

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


def _modify_transaction_date(doc, new_date):
	"""Orders and quotations have no invoice ledgers; update their transaction date."""
	doc.check_permission("write")
	old_date = str(doc.transaction_date)
	if old_date == new_date:
		return {"status": "unchanged", "name": doc.name, "doctype": doc.doctype,
			"new_date": new_date, "message": f"Bill date for {doc.name} is already {new_date}."}

	# Preserve normal date constraints without silently moving delivery/validity dates.
	for field in ("delivery_date", "schedule_date", "valid_till"):
		if doc.get(field) and getdate(doc.get(field)) < getdate(new_date):
			frappe.throw(f"New bill date cannot be after {doc.meta.get_label(field)} ({doc.get(field)}).")
	for table in ("items", "payment_schedule"):
		for row in doc.get(table) or []:
			for field in ("delivery_date", "schedule_date", "due_date"):
				if row.get(field) and getdate(row.get(field)) < getdate(new_date):
					frappe.throw(f"New bill date cannot be after {field.replace('_', ' ')} ({row.get(field)}).")

	frappe.db.set_value(doc.doctype, doc.name, {
		"transaction_date": new_date, "modified": now(), "modified_by": frappe.session.user,
	}, update_modified=False)
	frappe.clear_document_cache(doc.doctype, doc.name)
	doc.add_comment("Info", f"Bill date modified from {old_date} to {new_date} by {frappe.session.user}")
	return {"status": "success", "name": doc.name, "doctype": doc.doctype,
		"old_date": old_date, "new_date": new_date,
		"message": f"Bill date for {doc.name} changed from {old_date} to {new_date} successfully."}
