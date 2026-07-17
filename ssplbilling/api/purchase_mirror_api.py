import frappe
from ssplbilling.api.automatic_entries_api import (
	get_automatic_entries,
	_account_map,
	resolve_target_account,
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
	if not automatic_entries.alternative_company or not automatic_entries.warehouse:
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
	target_warehouse = automatic_entries.warehouse
	account_map = _account_map(automatic_entries)

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
	mpi.set_warehouse = target_warehouse
	mpi.additional_discount_percentage = pi.additional_discount_percentage
	mpi.discount_amount = pi.discount_amount

	for item in pi.items:
		row = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or item.stock_uom,
			"warehouse": target_warehouse,
		}
		if frappe.get_meta("Purchase Invoice Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		mapped_expense = resolve_target_account(item.expense_account, account_map, target_company)
		if mapped_expense:
			row["expense_account"] = mapped_expense
		mpi.append("items", row)

	if pi.taxes_and_charges:
		mpi.taxes_and_charges = pi.taxes_and_charges
	for tax in pi.taxes:
		mpi.append("taxes", {
			"charge_type": tax.charge_type,
			"account_head": resolve_target_account(tax.account_head, account_map, target_company) or tax.account_head,
			"description": tax.description,
			"rate": tax.rate,
			"included_in_print_rate": tax.included_in_print_rate,
		})

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
	if not ae.alternative_company or not ae.warehouse:
		return None

	sp = frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		mpi = create_mirror_purchase_invoice(pi, ae)
		frappe.db.release_savepoint(sp)
		return mpi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror purchase bill failed")
		return None
