import frappe
from ssplbilling.api.automatic_entries_api import (
	get_automatic_entries,
	_allowed_accounts,
	resolve_target_account,
	resolve_target_item_tax_template,
	ensure_warehouse_in_company,
	ensure_cost_center_in_company,
)


def _purchase_mirror_series(automatic_entries):
	series_set = set()
	for r in (automatic_entries.series or []):
		if r.purchase_invoice_series:
			for val in r.purchase_invoice_series.split(","):
				val_clean = val.strip()
				if val_clean:
					series_set.add(val_clean)
	return series_set


def should_mirror_purchase_invoice(naming_series, automatic_entries):
	"""Whether `naming_series` is configured in Automatic Entries for cross-company mirroring of purchases."""
	if not automatic_entries.alternative_company:
		return False
	if not naming_series:
		return False
	for prefix in _purchase_mirror_series(automatic_entries):
		if naming_series == prefix or naming_series.startswith(prefix):
			return True
	return False


def create_mirror_purchase_invoice(pi, automatic_entries):
	"""Create + submit a mirror Purchase Invoice for `pi` in the alternate company, named
	pi.name + '/', posted against the Automatic Entries warehouse with accounts
	substituted via resolve_target_account.
	"""
	mirror_name = f"{pi.name}/"
	if frappe.db.exists("Purchase Invoice", mirror_name):
		return frappe.get_doc("Purchase Invoice", mirror_name)

	target_company = automatic_entries.alternative_company
	
	source_warehouse = pi.set_warehouse or (pi.items[0].warehouse if pi.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or automatic_entries.warehouse
	
	source_cost_center = pi.cost_center or (pi.items[0].cost_center if pi.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)
	
	allowed_accounts = _allowed_accounts(automatic_entries)

	mpi = frappe.new_doc("Purchase Invoice")
	mpi.company = target_company
	mpi.supplier = pi.supplier
	mpi.naming_series = pi.naming_series
	mpi.bill_no = pi.bill_no
	mpi.bill_date = pi.bill_date
	mpi.posting_date = pi.posting_date
	mpi.posting_time = pi.posting_time
	mpi.set_posting_time = 1
	mpi.is_return = pi.is_return
	mpi.update_stock = pi.update_stock
	
	if pi.set_warehouse:
		mpi.set_warehouse = ensure_warehouse_in_company(pi.set_warehouse, target_company) or target_warehouse
	else:
		mpi.set_warehouse = target_warehouse
		
	if pi.cost_center:
		mpi.cost_center = ensure_cost_center_in_company(pi.cost_center, target_company)
	elif target_cost_center:
		mpi.cost_center = target_cost_center

	mpi.additional_discount_percentage = pi.additional_discount_percentage
	mpi.discount_amount = pi.discount_amount

	for item in pi.items:
		item_wh = ensure_warehouse_in_company(item.warehouse, target_company) or target_warehouse
		item_cc = ensure_cost_center_in_company(item.cost_center, target_company) or mpi.cost_center
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
		if frappe.get_meta("Purchase Invoice Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		mapped_expense = resolve_target_account(item.expense_account, allowed_accounts, target_company)
		if mapped_expense:
			row["expense_account"] = mapped_expense
		mpi.append("items", row)

	if pi.taxes_and_charges:
		mpi.taxes_and_charges = pi.taxes_and_charges
	for tax in pi.taxes:
		tax_row = {
			"charge_type": tax.charge_type,
			"account_head": resolve_target_account(tax.account_head, allowed_accounts, target_company) or tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"included_in_print_rate": tax.included_in_print_rate,
		}
		if tax.cost_center:
			tax_row["cost_center"] = ensure_cost_center_in_company(tax.cost_center, target_company)
		mpi.append("taxes", tax_row)

	mpi.flags.ignore_permissions = True
	mpi.insert(set_name=mirror_name)
	mpi.submit()
	return mpi


def mirror_purchase_bill(pi):
	"""Create the mirror Purchase Invoice if `pi`'s naming series is configured
	for cross-company mirroring. Returns the mirror doc, or None.
	Isolated with a savepoint so a failure here never rolls back pi's own submission.
	"""
	ae = get_automatic_entries()
	if not should_mirror_purchase_invoice(pi.naming_series, ae):
		return None

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		mpi = create_mirror_purchase_invoice(pi, ae)
		frappe.db.release_savepoint(sp)
		return mpi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror purchase bill failed")
		return None
