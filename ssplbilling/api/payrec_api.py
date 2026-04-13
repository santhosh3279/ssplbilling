import frappe
import json

def _get_party_account(party_type, party):
	"""Get the default receivable/payable account for a party."""
	from erpnext.accounts.party import get_party_account
	return get_party_account(party_type, party, frappe.defaults.get_global_default("company"))

def _get_mop_for_account(account, company):
	"""Return the Mode of Payment whose default account matches the given GL account."""
	mop = frappe.db.get_value(
		"Mode of Payment Account",
		{"default_account": account, "company": company},
		"parent",
	)
	return mop or "Cash"

@frappe.whitelist()
def create_payrec_payment_entry(data):
	"""
	Create Payment Entry documents from PayRec data.
	Supports multi-account split (creates one PE per bank/cash row).
	"""
	if isinstance(data, str):
		data = json.loads(data)

	accounts = data.get("accounts") or []
	if not accounts:
		frappe.throw("No accounts provided")

	entry_type = data.get("entry_type")  # 'Receipt' or 'Payment'
	payment_type = "Receive" if entry_type == "Receipt" else "Pay"

	posting_date = data.get("posting_date") or frappe.utils.today()
	cheque_no = data.get("cheque_no") or ""
	user_remark = data.get("user_remark") or ""
	company = frappe.defaults.get_global_default("company")

	# Row 0 = party
	row0 = accounts[0]
	party_type = row0.get("account_type")
	party = row0.get("account")

	if party_type not in ("Customer", "Supplier", "Employee"):
		frappe.throw("First row must be a Customer, Supplier, or Employee")

	party_account = _get_party_account(party_type, party)

	payment_rows = accounts[1:]
	if not payment_rows:
		frappe.throw("At least one bank/cash row is required")

	references = data.get("references") or []
	created_names = []
	refs_added = False

	for row in payment_rows:
		bank_account = row.get("account")
		amount = float(row.get("debit_in_account_currency") or row.get("credit_in_account_currency") or 0)
		if amount < 0.005:
			continue

		mop = _get_mop_for_account(bank_account, company)

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = payment_type
		pe.posting_date = posting_date
		pe.company = company
		pe.party_type = party_type
		pe.party = party
		pe.mode_of_payment = mop
		pe.paid_amount = amount
		pe.received_amount = amount
		pe.reference_no = cheque_no or f"REF-{posting_date}"
		pe.reference_date = posting_date
		pe.remarks = user_remark

		if payment_type == "Receive":
			pe.paid_from = party_account
			pe.paid_to = bank_account
		else:
			pe.paid_from = bank_account
			pe.paid_to = party_account
		
		# Set currencies
		pe.paid_from_account_currency = frappe.db.get_value("Account", pe.paid_from, "account_currency")
		pe.paid_to_account_currency = frappe.db.get_value("Account", pe.paid_to, "account_currency")

		# Attach references to the first PE
		if references and not refs_added:
			for ref in references:
				ref_name = ref.get("name") or ref.get("reference_name")
				allocated = float(ref.get("amount") or ref.get("allocated_amount") or 0)
				if not ref_name or allocated < 0.005:
					continue

				ref_doctype = ref.get("ref_type") or ref.get("reference_type")
				if not ref_doctype:
					if party_type == "Customer": ref_doctype = "Sales Invoice"
					elif party_type == "Supplier": ref_doctype = "Purchase Invoice"
					elif party_type == "Employee": ref_doctype = "Expense Claim"
				
				# Skip Payment Entry references to avoid ERPNext's strict party validation
				if ref_doctype == "Payment Entry":
					continue

				# Fetch actual total and outstanding
				ref_account = party_account
				if ref_doctype in ("Sales Invoice", "Purchase Invoice"):
					total_amount, outstanding = frappe.db.get_value(ref_doctype, ref_name, ["grand_total", "outstanding_amount"])
				elif ref_doctype == "Journal Entry":
					je_row = frappe.db.get_value("Journal Entry Account", 
						{"parent": ref_name, "party_type": party_type, "party": party}, 
						["account", "debit_in_account_currency", "credit_in_account_currency"], as_dict=True)
					if not je_row: continue
					ref_account = je_row.account
					total_amount = float(je_row.debit_in_account_currency or je_row.credit_in_account_currency or 0)
					
					allocated_in_pe = frappe.db.sql("""
						SELECT SUM(allocated_amount) as total
						FROM `tabPayment Entry Reference`
						WHERE reference_doctype = 'Journal Entry' AND reference_name = %s
						  AND docstatus = 1
					""", (ref_name,), as_dict=True)[0].total or 0
					outstanding = total_amount - float(allocated_in_pe)
				else:
					total_amount = float(ref.get("total_amount") or 0)
					outstanding = float(ref.get("outstanding_amount") or allocated)

				if float(outstanding or 0) < 0.005:
					continue

				pe.append("references", {
					"reference_doctype": ref_doctype,
					"reference_name": ref_name,
					"total_amount": float(total_amount or 0),
					"outstanding_amount": float(outstanding or 0),
					"allocated_amount": min(allocated, float(outstanding or 0)),
					"account": ref_account
				})
			refs_added = True

		pe.insert()
		pe.submit()
		created_names.append(pe.name)

	return {"names": created_names, "status": "Submitted"}
