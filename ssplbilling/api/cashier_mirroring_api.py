import frappe
from ssplbilling.api.automatic_entries_api import (
	get_automatic_entries,
	_allowed_accounts,
	resolve_target_account,
	_mop_for_account
)


def _create_mirror_payment_entry(msi, amount, original_account, allowed_accounts, ref_no=None, original_pe_name=None, bypass_whitelist=False):
	if amount <= 0.01 or not original_account:
		return None
	if not bypass_whitelist and original_account not in allowed_accounts:
		return None
	target_company = msi.company
	paid_to = resolve_target_account(original_account, allowed_accounts, target_company)
	if not paid_to:
		return None

	ae = get_automatic_entries()
	if ae.payment_entry_naming_settings and original_pe_name:
		existing = frappe.db.get_value(
			"Payment Entry",
			{"company": target_company, "remarks": ["like", f"%Mirrored from {original_pe_name}%"], "docstatus": ["!=", 2]},
			"name"
		)
		if existing:
			return existing
		mirror_name = None
	else:
		mirror_name = f"{original_pe_name}/" if original_pe_name else None
		if mirror_name and frappe.db.exists("Payment Entry", mirror_name):
			return mirror_name

	outstanding = frappe.db.get_value("Sales Invoice", msi.name, "outstanding_amount") or 0
	allocated = min(amount, outstanding)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.posting_date = msi.posting_date
	pe.company = target_company
	pe.mode_of_payment = _mop_for_account(paid_to, target_company)
	pe.party_type = "Customer"
	pe.party = msi.customer
	pe.paid_from = msi.debit_to
	pe.paid_to = paid_to
	pe.paid_amount = amount
	pe.received_amount = amount
	if original_pe_name:
		pe.remarks = f"Mirrored from {original_pe_name}"
		pe.custom_remarks = 1

	if original_pe_name and not ref_no:
		ref_no = frappe.db.get_value("Payment Entry", original_pe_name, "reference_no")

	if ref_no:
		pe.reference_no = ref_no
		pe.reference_date = msi.posting_date
	if allocated > 0:
		pe.append("references", {
			"reference_doctype": "Sales Invoice",
			"reference_name": msi.name,
			"allocated_amount": allocated,
		})
	pe.flags.ignore_permissions = True
	if ae.payment_entry_naming_settings:
		pe.naming_series = ae.payment_entry_naming_settings
		pe.insert()
	elif mirror_name:
		pe.insert(set_name=mirror_name)
	else:
		pe.insert()
	pe.submit()
	return pe.name


def mirror_payments(msi, cash_amount=0, upi_amount=0, card_amount=0, discount_amount=0,
                     cash_account=None, upi_account=None, card_account=None,
                     discount_account=None, card_ref_no=None,
                     original_cash_pe=None, original_upi_pe=None, original_card_pe=None,
                     original_discount_je=None, bypass_whitelist=True, cost_center=None):
	"""Replicate the cash/UPI/card payments (and discount write-off) against the mirror
	invoice `msi`. No-op if msi is None. Isolated with its own savepoint.
	"""
	if not msi:
		return []

	ae = get_automatic_entries()
	allowed_accounts = _allowed_accounts(ae)

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		entries = []

		pe_name = _create_mirror_payment_entry(
			msi, cash_amount, cash_account, allowed_accounts, original_pe_name=original_cash_pe, bypass_whitelist=bypass_whitelist
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, upi_amount, upi_account, allowed_accounts, original_pe_name=original_upi_pe, bypass_whitelist=bypass_whitelist
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, card_amount, card_account, allowed_accounts, ref_no=card_ref_no, original_pe_name=original_card_pe, bypass_whitelist=bypass_whitelist
		)
		if pe_name:
			entries.append(pe_name)

		if discount_amount > 0.01 and discount_account:
			if bypass_whitelist or discount_account in allowed_accounts:
				mapped_discount = resolve_target_account(discount_account, allowed_accounts, msi.company)
				if mapped_discount:
					mirror_je_name = f"{original_discount_je}/" if original_discount_je else None
					if mirror_je_name and frappe.db.exists("Journal Entry", mirror_je_name):
						entries.append(mirror_je_name)
					else:
						je = frappe.new_doc("Journal Entry")
						je.voucher_type = "Journal Entry"
						je.posting_date = msi.posting_date
						je.company = msi.company
						je.append("accounts", {
							"account": mapped_discount,
							"debit_in_account_currency": discount_amount,
							"cost_center": cost_center or msi.get("cost_center")
						})
						je.append("accounts", {
							"account": msi.debit_to,
							"credit_in_account_currency": discount_amount,
							"party_type": "Customer",
							"party": msi.customer,
							"reference_type": "Sales Invoice",
							"reference_name": msi.name,
							"cost_center": cost_center or msi.get("cost_center")
						})
						if original_discount_je:
							cheque_no, cheque_date = frappe.db.get_value(
								"Journal Entry", original_discount_je, ["cheque_no", "cheque_date"]
							)
							if cheque_no:
								je.cheque_no = cheque_no
							if cheque_date:
								je.cheque_date = cheque_date

						je.flags.ignore_permissions = True
						if mirror_je_name:
							je.insert(set_name=mirror_je_name)
						else:
							je.insert()
						je.submit()
						entries.append(je.name)

		frappe.db.release_savepoint(sp)
		return entries
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror payments failed")
		return []


def mirror_payments_for_gst_conversion(si, msi, ae):
	"""Mirror the payment entries and journal entries (discounts, etc.) associated
	with the original Sales Invoice `si` to the mirror invoice `msi`.
	"""
	allowed_accounts = _allowed_accounts(ae)
	
	# 1. Replicate Payment Entries
	pe_references = frappe.db.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Invoice", "reference_name": si.name, "docstatus": 1},
		fields=["parent", "allocated_amount"]
	)
	for ref in pe_references:
		pe_data = frappe.db.get_value("Payment Entry", ref.parent, ["paid_to", "reference_no"], as_dict=True)
		if pe_data:
			_create_mirror_payment_entry(
				msi=msi,
				amount=ref.allocated_amount,
				original_account=pe_data.paid_to,
				allowed_accounts=allowed_accounts,
				ref_no=pe_data.reference_no,
				original_pe_name=ref.parent,
				bypass_whitelist=True
			)

	# 2. Replicate Journal Entries (discounts, etc.)
	je_references = frappe.db.get_all(
		"Journal Entry Account",
		filters={"reference_type": "Sales Invoice", "reference_name": si.name, "docstatus": 1},
		fields=["parent"]
	)
	unique_je_names = list(set(ref.parent for ref in je_references))
	for je_name in unique_je_names:
		mirror_je_name = f"{je_name}/"
		if frappe.db.exists("Journal Entry", mirror_je_name):
			continue

		je_doc = frappe.get_doc("Journal Entry", je_name)
		si_acc_row = next((acc for acc in je_doc.accounts if acc.reference_name == si.name), None)
		if not si_acc_row:
			continue

		amount = si_acc_row.credit_in_account_currency or si_acc_row.debit_in_account_currency
		if amount <= 0.01:
			continue

		discount_acc_row = next((acc for acc in je_doc.accounts if acc != si_acc_row), None)
		if not discount_acc_row:
			continue

		discount_account = discount_acc_row.account
		if True:  # bypass whitelist
			mapped_discount = resolve_target_account(discount_account, allowed_accounts, msi.company)
			if mapped_discount:
				je = frappe.new_doc("Journal Entry")
				je.voucher_type = "Journal Entry"
				je.posting_date = msi.posting_date
				je.company = msi.company
				je.append("accounts", {"account": mapped_discount, "debit_in_account_currency": amount})
				je.append("accounts", {
					"account": msi.debit_to,
					"credit_in_account_currency": amount,
					"party_type": "Customer",
					"party": msi.customer,
					"reference_type": "Sales Invoice",
					"reference_name": msi.name,
				})
				if je_doc.cheque_no:
					je.cheque_no = je_doc.cheque_no
				if je_doc.cheque_date:
					je.cheque_date = je_doc.cheque_date

				je.flags.ignore_permissions = True
				je.insert(set_name=mirror_je_name)
				je.submit()
