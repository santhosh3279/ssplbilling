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


def _conversion_mirror_series(automatic_entries):
	series_set = set()
	for r in (automatic_entries.series or []):
		val_raw = r.get("conversion_invoice_series")
		if val_raw:
			for val in val_raw.split(','):
				val_clean = val.strip()
				if val_clean:
					series_set.add(val_clean)
	return series_set


def _allowed_accounts(automatic_entries):
	return {
		r.account
		for r in (automatic_entries.accounts or [])
		if r.account
	}


def should_mirror_sales_invoice(naming_series, automatic_entries):
	"""Whether `naming_series` is configured in Automatic Entries for cross-company mirroring."""
	if not automatic_entries.alternative_company or not automatic_entries.warehouse:
		return False
	if not naming_series:
		return False
	allowed = _sales_mirror_series(automatic_entries) | _conversion_mirror_series(automatic_entries)
	for prefix in allowed:
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


def ensure_account_in_company(original_account, target_company):
	"""Ensure that an equivalent of original_account exists in target_company.
	If not, create it copying attributes from original_account (and recursively for its parent).
	"""
	if not original_account or not target_company:
		return None

	orig_doc = frappe.db.get_value(
		"Account",
		original_account,
		[
			"account_name",
			"company",
			"parent_account",
			"account_type",
			"root_type",
			"report_type",
			"is_group",
			"account_currency",
			"tax_rate",
		],
		as_dict=True,
	)
	if not orig_doc:
		return None

	if orig_doc.company == target_company:
		return original_account

	exists = frappe.db.get_value(
		"Account",
		{"account_name": orig_doc.account_name, "company": target_company},
		"name",
	)
	if exists:
		return exists

	target_parent = None
	if orig_doc.parent_account:
		target_parent = ensure_account_in_company(orig_doc.parent_account, target_company)

	new_acc = frappe.new_doc("Account")
	new_acc.account_name = orig_doc.account_name
	new_acc.company = target_company
	new_acc.parent_account = target_parent
	new_acc.account_type = orig_doc.account_type
	new_acc.root_type = orig_doc.root_type
	new_acc.report_type = orig_doc.report_type
	new_acc.is_group = orig_doc.is_group
	new_acc.account_currency = orig_doc.account_currency or frappe.get_cached_value(
		"Company", target_company, "default_currency"
	)
	if orig_doc.tax_rate:
		new_acc.tax_rate = orig_doc.tax_rate

	new_acc.flags.ignore_permissions = True
	new_acc.insert()
	return new_acc.name


def resolve_target_account(original_account, allowed_accounts, target_company):
	"""Resolve `original_account` (belongs to the source company) to its equivalent in
	`target_company`, in order:
	1. An account with the same account_name in the target company's chart.
	2. Automatically created account copying the source account structure (if whitelisted).
	3. The default account for original_account's Mode of Payment, in the target company.
	Returns "" if none of these resolve, so callers can fall back to ERPNext's own defaults.
	"""
	if not original_account:
		return ""

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

		# Account does not exist in target company, so auto-create it (if whitelisted)
		if original_account in allowed_accounts:
			created_acc = ensure_account_in_company(original_account, target_company)
			if created_acc:
				return created_acc

	mop = _mop_for_account(original_account, source_company)
	return _mop_default_account(mop, target_company)
def resolve_target_item_tax_template(source_template, target_company):
	"""Resolve a source item tax template to its equivalent in the target company
	by matching the title of the template.
	"""
	if not source_template or not target_company:
		return ""
	title = frappe.db.get_value("Item Tax Template", source_template, "title")
	if title:
		target_template = frappe.db.get_value(
			"Item Tax Template", {"company": target_company, "title": title}, "name"
		)
		if target_template:
			return target_template
	return ""


def ensure_warehouse_in_company(original_warehouse, target_company):
	"""Ensure that an equivalent of original_warehouse exists in target_company.
	If not, create it copying attributes from original_warehouse (and recursively for its parent).
	"""
	if not original_warehouse or not target_company:
		return None

	orig_doc = frappe.db.get_value(
		"Warehouse",
		original_warehouse,
		[
			"warehouse_name",
			"company",
			"parent_warehouse",
			"is_group",
			"is_rejected_warehouse",
		],
		as_dict=True,
	)
	if not orig_doc:
		return None

	if orig_doc.company == target_company:
		return original_warehouse

	exists = frappe.db.get_value(
		"Warehouse",
		{"warehouse_name": orig_doc.warehouse_name, "company": target_company},
		"name",
	)
	if exists:
		return exists

	# Find or ensure the parent warehouse exists in the target company
	target_parent = None
	if orig_doc.parent_warehouse:
		target_parent = ensure_warehouse_in_company(orig_doc.parent_warehouse, target_company)
	else:
		# Root warehouse, return target root warehouse
		target_root = frappe.db.get_value(
			"Warehouse",
			{"company": target_company, "parent_warehouse": ["in", ["", None]]},
			"name",
		)
		if target_root:
			return target_root

	new_wh = frappe.new_doc("Warehouse")
	new_wh.warehouse_name = orig_doc.warehouse_name
	new_wh.company = target_company
	new_wh.parent_warehouse = target_parent
	new_wh.is_group = orig_doc.is_group
	new_wh.is_rejected_warehouse = orig_doc.is_rejected_warehouse

	new_wh.flags.ignore_permissions = True
	new_wh.insert()
	return new_wh.name


def ensure_cost_center_in_company(original_cost_center, target_company):
	"""Ensure that an equivalent of original_cost_center exists in target_company.
	If not, create it copying attributes from original_cost_center (and recursively for its parent).
	"""
	if not original_cost_center or not target_company:
		return None

	orig_doc = frappe.db.get_value(
		"Cost Center",
		original_cost_center,
		[
			"cost_center_name",
			"company",
			"parent_cost_center",
			"is_group",
			"disabled",
		],
		as_dict=True,
	)
	if not orig_doc:
		return None

	if orig_doc.company == target_company:
		return original_cost_center

	exists = frappe.db.get_value(
		"Cost Center",
		{"cost_center_name": orig_doc.cost_center_name, "company": target_company},
		"name",
	)
	if exists:
		return exists

	# Find or ensure the parent cost center exists in the target company
	target_parent = None
	if orig_doc.parent_cost_center:
		target_parent = ensure_cost_center_in_company(orig_doc.parent_cost_center, target_company)
	else:
		# Root cost center, return target root cost center
		target_root = frappe.db.get_value(
			"Cost Center",
			{"company": target_company, "parent_cost_center": ["in", ["", None]]},
			"name",
		)
		if target_root:
			return target_root

	new_cc = frappe.new_doc("Cost Center")
	new_cc.cost_center_name = orig_doc.cost_center_name
	new_cc.company = target_company
	new_cc.parent_cost_center = target_parent
	new_cc.is_group = orig_doc.is_group
	new_cc.disabled = orig_doc.disabled

	new_cc.flags.ignore_permissions = True
	new_cc.insert()
	return new_cc.name


def create_mirror_sales_invoice(si, automatic_entries):
	"""Create + submit a mirror Sales Invoice for `si` in the alternate company, named
	si.name + '/', posted against the Automatic Entries warehouse with accounts
	substituted via resolve_target_account."""
	mirror_name = f"{si.name}/"
	if frappe.db.exists("Sales Invoice", mirror_name):
		return frappe.get_doc("Sales Invoice", mirror_name)

	target_company = automatic_entries.alternative_company
	
	source_warehouse = si.set_warehouse or (si.items[0].warehouse if si.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or automatic_entries.warehouse
	
	source_cost_center = si.cost_center or (si.items[0].cost_center if si.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)
	
	allowed_accounts = _allowed_accounts(automatic_entries)

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
	
	if si.set_warehouse:
		msi.set_warehouse = ensure_warehouse_in_company(si.set_warehouse, target_company) or target_warehouse
	else:
		msi.set_warehouse = target_warehouse
		
	if si.cost_center:
		msi.cost_center = ensure_cost_center_in_company(si.cost_center, target_company)
	elif target_cost_center:
		msi.cost_center = target_cost_center

	for item in si.items:
		item_wh = ensure_warehouse_in_company(item.warehouse, target_company) or target_warehouse
		item_cc = ensure_cost_center_in_company(item.cost_center, target_company) or msi.cost_center
		row = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or item.stock_uom,
			"warehouse": item_wh,
		}
		if item_cc:
			row["cost_center"] = item_cc
		if item.item_tax_template:
			target_tax_template = resolve_target_item_tax_template(item.item_tax_template, target_company)
			if target_tax_template:
				row["item_tax_template"] = target_tax_template
		mapped_income = resolve_target_account(item.income_account, allowed_accounts, target_company)
		if mapped_income:
			row["income_account"] = mapped_income
		msi.append("items", row)

	if si.taxes_and_charges:
		msi.taxes_and_charges = si.taxes_and_charges
	for tax in si.taxes:
		tax_row = {
			"charge_type": tax.charge_type,
			"account_head": resolve_target_account(tax.account_head, allowed_accounts, target_company) or tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"included_in_print_rate": tax.included_in_print_rate,
		}
		if tax.cost_center:
			tax_row["cost_center"] = ensure_cost_center_in_company(tax.cost_center, target_company)
		msi.append("taxes", tax_row)

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

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		msi = create_mirror_sales_invoice(si, ae)
		frappe.db.release_savepoint(sp)
		return msi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror bill failed")
		return None






def _create_mirror_payment_entry(msi, amount, original_account, allowed_accounts, ref_no=None, original_pe_name=None):
	if amount <= 0.01 or not original_account:
		return None
	if original_account not in allowed_accounts:
		return None
	target_company = msi.company
	paid_to = resolve_target_account(original_account, allowed_accounts, target_company)
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
	allowed_accounts = _allowed_accounts(ae)

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		entries = []

		pe_name = _create_mirror_payment_entry(
			msi, cash_amount, cash_account, allowed_accounts, original_pe_name=original_cash_pe
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, upi_amount, upi_account, allowed_accounts, original_pe_name=original_upi_pe
		)
		if pe_name:
			entries.append(pe_name)

		pe_name = _create_mirror_payment_entry(
			msi, card_amount, card_account, allowed_accounts, ref_no=card_ref_no, original_pe_name=original_card_pe
		)
		if pe_name:
			entries.append(pe_name)

		if discount_amount > 0.01 and discount_account:
			if discount_account in allowed_accounts:
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


def create_mirror_invoice_for_gst_conversion(si, ae, naming_series=None, price_list=None, use_series_naming=False, submit=True):
	"""Create a mirror Sales Invoice in target company (ae_company) for a Sales Invoice
	that is being converted to a GST bill (Quotation).
	It creates a Sales Invoice in target company, with name si.name + '/', and copies all accounts,
	creating them in the target company if they don't exist.

	With use_series_naming=True the mirror is named from `naming_series` instead of
	si.name + '/', so repeated calls create new invoices (manual conversion mirroring).
	"""
	mirror_name = None if use_series_naming else f"{si.name}/"
	if mirror_name and frappe.db.exists("Sales Invoice", mirror_name):
		return frappe.get_doc("Sales Invoice", mirror_name)

	target_company = ae.alternative_company
	
	source_warehouse = si.set_warehouse or (si.items[0].warehouse if si.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or ae.warehouse
	
	source_cost_center = si.cost_center or (si.items[0].cost_center if si.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)

	msi = frappe.new_doc("Sales Invoice")
	msi.company = target_company
	msi.customer = si.customer
	if si.customer_address:
		msi.customer_address = si.customer_address
	msi.naming_series = naming_series or si.naming_series
	msi.posting_date = si.posting_date
	msi.posting_time = si.posting_time
	msi.set_posting_time = 1
	msi.due_date = si.due_date
	msi.selling_price_list = price_list or si.selling_price_list
	msi.additional_discount_percentage = si.additional_discount_percentage
	msi.discount_amount = si.discount_amount
	msi.is_return = si.is_return
	msi.update_stock = si.update_stock

	if si.set_warehouse:
		msi.set_warehouse = ensure_warehouse_in_company(si.set_warehouse, target_company) or target_warehouse
	else:
		msi.set_warehouse = target_warehouse

	if si.cost_center:
		msi.cost_center = ensure_cost_center_in_company(si.cost_center, target_company)
	elif target_cost_center:
		msi.cost_center = target_cost_center

	if si.debit_to:
		msi.debit_to = ensure_account_in_company(si.debit_to, target_company)

	for item in si.items:
		item_wh = ensure_warehouse_in_company(item.warehouse, target_company) or target_warehouse
		item_cc = ensure_cost_center_in_company(item.cost_center, target_company) or msi.cost_center
		row = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or item.stock_uom,
			"warehouse": item_wh,
		}
		if item_cc:
			row["cost_center"] = item_cc
		if item.item_tax_template:
			target_tax_template = resolve_target_item_tax_template(item.item_tax_template, target_company)
			if target_tax_template:
				row["item_tax_template"] = target_tax_template
		if item.income_account:
			row["income_account"] = ensure_account_in_company(item.income_account, target_company)
		msi.append("items", row)

	if si.taxes_and_charges:
		msi.taxes_and_charges = si.taxes_and_charges
	for tax in si.taxes:
		tax_row = {
			"charge_type": tax.charge_type,
			"account_head": ensure_account_in_company(tax.account_head, target_company) or tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"included_in_print_rate": tax.included_in_print_rate,
		}
		if tax.cost_center:
			tax_row["cost_center"] = ensure_cost_center_in_company(tax.cost_center, target_company)
		msi.append("taxes", tax_row)

	msi.custom_customer_name = si.get("custom_customer_name") or ""
	msi.custom_address_line1 = si.get("custom_address_line1") or ""
	msi.custom_address_line2 = si.get("custom_address_line2") or ""
	msi.custom_mobile_number = si.get("custom_mobile_number") or ""

	msi.flags.ignore_permissions = True
	if mirror_name:
		msi.insert(set_name=mirror_name)
	else:
		msi.insert()
	if submit:
		msi.submit()
	return msi


@frappe.whitelist()
def get_conversion_series():
	"""Conversion Invoice Series configured in Automatic Entries, plus the target company."""
	ae = get_automatic_entries()
	return {
		"company": ae.alternative_company or "",
		"series": sorted(_conversion_mirror_series(ae)),
	}


def _expand_series_prefix(prefix, doctype="Sales Invoice"):
	"""Expand a bare series prefix (e.g. 'WGB') to the full naming series option
	configured for the doctype (e.g. 'WGB.#####'), so invoices always store the
	exact option value the sidebar panels filter on. Returns the input unchanged
	when it already contains a '.' or no matching option exists."""
	if not prefix or "." in prefix:
		return prefix

	options = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": "naming_series", "property": "options"},
		"value",
	)
	if not options:
		field = frappe.get_meta(doctype).get_field("naming_series")
		options = field.options if field else ""

	for opt in (options or "").split("\n"):
		opt = opt.strip()
		if opt == prefix or opt.startswith(prefix + "."):
			return opt
	return prefix


@frappe.whitelist()
def create_conversion_mirror_invoice(sales_invoice_name, naming_series, price_list=None):
	"""Mirror `sales_invoice_name` into the Automatic Entries alternative company as a new
	draft Sales Invoice named from `naming_series` (must be a configured Conversion
	Invoice Series). Missing accounts, warehouses and cost centers are auto-created in
	the target company via the ensure_*_in_company helpers."""
	ae = get_automatic_entries()
	if not ae.alternative_company:
		frappe.throw("Automatic Entries: alternative company is not configured.")
	if naming_series not in _conversion_mirror_series(ae):
		frappe.throw(f"Series {naming_series} is not a Conversion Invoice Series in Automatic Entries.")

	naming_series = _expand_series_prefix(naming_series)
	si = frappe.get_doc("Sales Invoice", sales_invoice_name)
	msi = create_mirror_invoice_for_gst_conversion(
		si, ae, naming_series=naming_series, price_list=price_list, use_series_naming=True, submit=False
	)
	return {"status": "success", "invoice_name": msi.name, "company": msi.company}
