import frappe


def get_automatic_entries():
	"""Return the Automatic Entries singleton, freshly loaded (not cached) since a
	mirrored bill must always see the latest alternate company / warehouse / account
	mapping configured by the admin."""
	return frappe.get_doc("Automatic Entries", "Automatic Entries")


def _sales_mirror_series(automatic_entries):
	series_set = set()
	for r in (automatic_entries.series or []):
		if r.sales_invoice_series:
			for val in r.sales_invoice_series.split(','):
				val_clean = val.strip()
				if val_clean:
					series_set.add(val_clean)
	return series_set


def _account_map(automatic_entries):
	return {
		r.account: r.alternative_account
		for r in (automatic_entries.accounts or [])
		if r.account and r.alternative_account
	}


def should_mirror_sales_invoice(naming_series, automatic_entries):
	"""Whether `naming_series` is configured in Automatic Entries for cross-company mirroring."""
	if not automatic_entries.alternative_company or not automatic_entries.warehouse:
		return False
	if not naming_series:
		return False
	for prefix in _sales_mirror_series(automatic_entries):
		if naming_series == prefix or naming_series.startswith(prefix):
			return True
	return False


def _mop_for_account(account, company):
	"""Find the Mode of Payment whose default account matches, for the given company."""
	if not account or not company:
		return "Cash"
	return frappe.db.get_value(
		"Mode of Payment Account", {"default_account": account, "company": company}, "parent"
	) or "Cash"


def _mop_default_account(mop_name, company):
	return frappe.db.get_value(
		"Mode of Payment Account", {"parent": mop_name, "company": company}, "default_account"
	) or ""


def resolve_target_account(original_account, account_map, target_company):
	"""Resolve `original_account` (belongs to the source company) to its equivalent in
	`target_company`, in order:
	1. Explicit Automatic Entries account mapping.
	2. An account with the same account_name in the target company's chart.
	3. The default account for original_account's Mode of Payment, in the target company.
	Returns "" if none of these resolve, so callers can fall back to ERPNext's own defaults.
	"""
	if not original_account:
		return ""
	if original_account in account_map:
		return account_map[original_account]

	source_company, account_name = (
		frappe.db.get_value("Account", original_account, ["company", "account_name"]) or (None, None)
	)

	if account_name:
		same_name = frappe.db.get_value(
			"Account",
			{"account_name": account_name, "company": target_company, "is_group": 0},
			"name",
		)
		if same_name:
			return same_name

	mop = _mop_for_account(original_account, source_company)
	return _mop_default_account(mop, target_company)


def create_mirror_sales_invoice(si, automatic_entries):
	"""Create + submit a mirror Sales Invoice for `si` in the alternate company, named
	si.name + '/', posted against the Automatic Entries warehouse with accounts
	substituted via resolve_target_account."""
	mirror_name = f"{si.name}/"
	if frappe.db.exists("Sales Invoice", mirror_name):
		return frappe.get_doc("Sales Invoice", mirror_name)

	target_company = automatic_entries.alternative_company
	target_warehouse = automatic_entries.warehouse
	account_map = _account_map(automatic_entries)

	msi = frappe.new_doc("Sales Invoice")
	msi.company = target_company
	msi.customer = si.customer
	if si.customer_address:
		msi.customer_address = si.customer_address
	msi.naming_series = si.naming_series
	msi.posting_date = si.posting_date
	msi.posting_time = si.posting_time
	msi.set_posting_time = 1
	msi.due_date = si.due_date
	msi.selling_price_list = si.selling_price_list
	msi.additional_discount_percentage = si.additional_discount_percentage
	msi.discount_amount = si.discount_amount
	msi.is_return = si.is_return
	msi.update_stock = si.update_stock
	msi.set_warehouse = target_warehouse

	for item in si.items:
		row = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or item.stock_uom,
			"warehouse": target_warehouse,
		}
		mapped_income = resolve_target_account(item.income_account, account_map, target_company)
		if mapped_income:
			row["income_account"] = mapped_income
		msi.append("items", row)

	if si.taxes_and_charges:
		msi.taxes_and_charges = si.taxes_and_charges
	for tax in si.taxes:
		msi.append("taxes", {
			"charge_type": tax.charge_type,
			"account_head": resolve_target_account(tax.account_head, account_map, target_company) or tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"included_in_print_rate": tax.included_in_print_rate,
		})

	msi.custom_customer_name = si.get("custom_customer_name") or ""
	msi.custom_address_line1 = si.get("custom_address_line1") or ""
	msi.custom_address_line2 = si.get("custom_address_line2") or ""
	msi.custom_mobile_number = si.get("custom_mobile_number") or ""

	msi.flags.ignore_permissions = True
	msi.insert(set_name=mirror_name)
	msi.submit()
	return msi


def mirror_bill(si):
	"""Create the mirror Sales Invoice (bill only, no payments) if `si`'s naming series
	is configured for cross-company mirroring. Returns the mirror doc, or None.
	Isolated with a savepoint so a failure here never rolls back si's own submission.
	"""
	ae = get_automatic_entries()
	if not should_mirror_sales_invoice(si.naming_series, ae):
		return None

	sp = frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		msi = create_mirror_sales_invoice(si, ae)
		frappe.db.release_savepoint(sp)
		return msi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror bill failed")
		return None


def _create_mirror_payment_entry(msi, amount, original_account, account_map, ref_no=None, original_pe_name=None):
	if amount <= 0.01 or not original_account:
		return None
	target_company = msi.company
	paid_to = resolve_target_account(original_account, account_map, target_company)
	if not paid_to:
		return None

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
	if mirror_name:
		pe.insert(set_name=mirror_name)
	else:
		pe.insert()
	pe.submit()
	return pe.name


def mirror_payments(msi, cash_amount=0, upi_amount=0, card_amount=0, discount_amount=0,
                     cash_account=None, upi_account=None, card_account=None,
                     discount_account=None, card_ref_no=None,
                     original_cash_pe=None, original_upi_pe=None, original_card_pe=None,
                     original_discount_je=None):
	"""Replicate the cash/UPI/card payments (and discount write-off) against the mirror
	invoice `msi`. No-op if msi is None. Isolated with its own savepoint.
	"""
	if not msi:
		return []

	ae = get_automatic_entries()
	account_map = _account_map(ae)

	sp = frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		entries = []

		pe_name = _create_mirror_payment_entry(
			msi, cash_amount, cash_account, account_map, original_pe_name=original_cash_pe
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, upi_amount, upi_account, account_map, original_pe_name=original_upi_pe
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, card_amount, card_account, account_map, ref_no=card_ref_no, original_pe_name=original_card_pe
		)
		if pe_name:
			entries.append(pe_name)

		if discount_amount > 0.01 and discount_account:
			mapped_discount = resolve_target_account(discount_account, account_map, msi.company)
			if mapped_discount:
				mirror_je_name = f"{original_discount_je}/" if original_discount_je else None
				if mirror_je_name and frappe.db.exists("Journal Entry", mirror_je_name):
					entries.append(mirror_je_name)
				else:
					je = frappe.new_doc("Journal Entry")
					je.voucher_type = "Journal Entry"
					je.posting_date = msi.posting_date
					je.company = msi.company
					je.append("accounts", {"account": mapped_discount, "debit_in_account_currency": discount_amount})
					je.append("accounts", {
						"account": msi.debit_to,
						"credit_in_account_currency": discount_amount,
						"party_type": "Customer",
						"party": msi.customer,
						"reference_type": "Sales Invoice",
						"reference_name": msi.name,
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
