import frappe

_DOCTYPE_MAP = {
	"Sales Invoice": "Sales Invoice",
	"Purchase Invoice": "Purchase Invoice",
	"Journal Entry": "Journal Entry",
	"Payment Entry": "Payment Entry",
}

_PARTY_FIELD = {
	"Sales Invoice": ("customer", "customer_name"),
	"Purchase Invoice": ("supplier", "supplier_name"),
	"Journal Entry": (None, "user_remark"),
	"Payment Entry": ("party", "party_name"),
}

_AMOUNT_FIELD = {
	"Sales Invoice": "grand_total",
	"Purchase Invoice": "grand_total",
	"Journal Entry": "total_debit",
	"Payment Entry": "paid_amount",
}


def _validate_doctype(doctype):
	if doctype not in _DOCTYPE_MAP:
		frappe.throw(f"Invalid doctype: {doctype}")


@frappe.whitelist()
def get_cancellable_documents(doctype="Sales Invoice", from_date=None, to_date=None, search="", limit=50):
	"""Return submitted (docstatus=1) documents for the given doctype and date range."""
	_validate_doctype(doctype)
	from_date = from_date or frappe.utils.today()
	to_date = to_date or frappe.utils.today()

	date_field = "posting_date" if doctype != "Journal Entry" else "posting_date"
	party_field, party_name_field = _PARTY_FIELD[doctype]
	amount_field = _AMOUNT_FIELD[doctype]

	fields = ["name", date_field, amount_field]
	if party_field:
		fields += [party_field, party_name_field]
	else:
		fields.append(party_name_field)

	if doctype == "Journal Entry":
		fields.append("voucher_type")

	filters = [
		["docstatus", "=", 1],
		[date_field, ">=", from_date],
		[date_field, "<=", to_date],
	]

	if search:
		filters.append(["name", "like", f"%{search}%"])

	docs = frappe.get_all(
		doctype,
		filters=filters,
		fields=fields,
		order_by=f"{date_field} desc, name desc",
		limit=int(limit),
	)
	return docs


@frappe.whitelist()
def get_cancelled_documents(doctype="Sales Invoice", from_date=None, to_date=None, search="", limit=50):
	"""Return cancelled (docstatus=2) documents for the given doctype."""
	_validate_doctype(doctype)
	from_date = from_date or frappe.utils.today()
	to_date = to_date or frappe.utils.today()

	date_field = "posting_date"
	party_field, party_name_field = _PARTY_FIELD[doctype]
	amount_field = _AMOUNT_FIELD[doctype]

	fields = ["name", date_field, amount_field, "amended_from"]
	if party_field:
		fields += [party_field, party_name_field]
	else:
		fields.append(party_name_field)

	if doctype == "Journal Entry":
		fields.append("voucher_type")

	filters = [
		["docstatus", "=", 2],
		[date_field, ">=", from_date],
		[date_field, "<=", to_date],
	]

	if search:
		filters.append(["name", "like", f"%{search}%"])

	docs = frappe.get_all(
		doctype,
		filters=filters,
		fields=fields,
		order_by=f"{date_field} desc, name desc",
		limit=int(limit),
	)
	return docs


@frappe.whitelist()
def get_document_detail(doctype, name):
	"""Return full document detail for preview."""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")

	result = doc.as_dict()

	# Attach items/accounts child table if present
	if doctype in ("Sales Invoice", "Purchase Invoice"):
		result["items"] = [
			{
				"item_code": r.item_code,
				"item_name": r.item_name,
				"qty": r.qty,
				"uom": r.uom,
				"rate": r.rate,
				"amount": r.amount,
			}
			for r in doc.items
		]
		result["taxes"] = [
			{"description": r.description, "tax_amount": r.tax_amount}
			for r in doc.taxes
		]
	elif doctype == "Journal Entry":
		result["accounts"] = [
			{
				"account": r.account,
				"party_type": r.party_type,
				"party": r.party,
				"debit_in_account_currency": r.debit_in_account_currency,
				"credit_in_account_currency": r.credit_in_account_currency,
				"user_remark": r.user_remark,
			}
			for r in doc.accounts
		]
	elif doctype == "Payment Entry":
		result["references"] = [
			{
				"reference_doctype": r.reference_doctype,
				"reference_name": r.reference_name,
				"allocated_amount": r.allocated_amount,
			}
			for r in doc.references
		]
	return result


@frappe.whitelist()
def cancel_document(doctype, name):
	"""Cancel a submitted document."""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("cancel")
	if doc.docstatus != 1:
		frappe.throw(f"{name} is not in submitted state (docstatus={doc.docstatus})")
	doc.cancel()
	frappe.db.commit()
	return {"status": "cancelled", "name": name}


@frappe.whitelist()
def amend_document(doctype, name):
	"""Amend a cancelled document and return the new draft name."""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("write")
	if doc.docstatus != 2:
		frappe.throw(f"{name} is not cancelled (docstatus={doc.docstatus})")
	amended = frappe.copy_doc(doc)
	amended.amended_from = name
	amended.docstatus = 0

	# Clear auto-set fields so Frappe re-derives them on insert
	amended.name = None
	if hasattr(amended, "set_posting_time"):
		amended.set_posting_time = 0

	amended.insert(ignore_permissions=False)
	frappe.db.commit()
	return {"status": "amended", "name": amended.name, "amended_from": name}


@frappe.whitelist()
def submit_amended_document(doctype, name):
	"""Submit a draft amended document."""
	_validate_doctype(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("submit")
	if doc.docstatus != 0:
		frappe.throw(f"{name} is not a draft (docstatus={doc.docstatus})")
	doc.submit()
	frappe.db.commit()
	return {"status": "submitted", "name": name}
