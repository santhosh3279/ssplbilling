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


def get_available_purchase_mirror_name(naming_series, target_company):
	"""Find the next available purchase invoice number in `target_company` for `naming_series`."""
	import re
	from frappe.model.naming import NamingSeries
	from frappe.utils import cint

	if not naming_series:
		field = frappe.get_meta("Purchase Invoice").get_field("naming_series")
		naming_series = (field.default if field else None) or "PINV-.#####"

	ns = NamingSeries(naming_series)
	prefix = ns.get_prefix()
	m = re.search(r"#+", naming_series)
	digits = len(m.group(0)) if m else 5

	existing_names = frappe.db.get_all(
		"Purchase Invoice",
		filters={"company": target_company, "name": ["like", f"{prefix}%"]},
		pluck="name",
	)
	max_company_num = 0
	for n in existing_names:
		clean = n[len(prefix):].rstrip("/")
		if clean.isdigit():
			val = int(clean)
			if val > max_company_num:
				max_company_num = val

	series_val = frappe.db.sql("SELECT current FROM `tabSeries` WHERE name = %s", (prefix,))
	series_current = cint(series_val[0][0]) if series_val and series_val[0] and series_val[0][0] is not None else 0

	next_num = max(series_current, max_company_num) + 1
	candidate = f"{prefix}{next_num:0{digits}d}"

	while frappe.db.exists("Purchase Invoice", candidate):
		next_num += 1
		candidate = f"{prefix}{next_num:0{digits}d}"

	has_series = frappe.db.sql("SELECT 1 FROM `tabSeries` WHERE name = %s", (prefix,))
	if has_series:
		frappe.db.sql("UPDATE `tabSeries` SET current = GREATEST(current, %s) WHERE name = %s", (next_num, prefix))
	else:
		frappe.db.sql("INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)", (prefix, next_num))

	return candidate


def create_mirror_purchase_invoice(pi, automatic_entries):
	"""Create + submit a mirror Purchase Invoice for `pi` in the alternate company,
	using the next available number in the AE company for that series, posted against
	the Automatic Entries warehouse with accounts substituted via resolve_target_account.
	"""
	if pi.get("custom_mirrored") and frappe.db.exists("Purchase Invoice", pi.custom_mirrored):
		return frappe.get_doc("Purchase Invoice", pi.custom_mirrored)

	old_mirror_name = pi.name[:-1] if pi.name.endswith("/") else f"{pi.name}/"
	if frappe.db.exists("Purchase Invoice", old_mirror_name):
		mpi = frappe.get_doc("Purchase Invoice", old_mirror_name)
		if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
			frappe.db.set_value("Purchase Invoice", pi.name, "custom_mirrored", mpi.name)
			pi.custom_mirrored = mpi.name
		return mpi

	target_company = automatic_entries.alternative_company
	mirror_name = get_available_purchase_mirror_name(pi.naming_series, target_company)

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
	if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		mpi.custom_mirrored = pi.name

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
	if not (should_mirror_purchase_invoice(pi.naming_series, ae) or (pi.name and should_mirror_purchase_invoice(pi.name, ae))):
		return None

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		mpi = create_mirror_purchase_invoice(pi, ae)
		frappe.db.release_savepoint(sp)
		if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored") and mpi:
			frappe.db.set_value("Purchase Invoice", pi.name, "custom_mirrored", mpi.name)
			pi.custom_mirrored = mpi.name
			frappe.clear_document_cache("Purchase Invoice", pi.name)
			if frappe.db.exists("Purchase Invoice", mpi.name):
				frappe.db.set_value("Purchase Invoice", mpi.name, "custom_mirrored", pi.name)
				mpi.custom_mirrored = pi.name
				frappe.clear_document_cache("Purchase Invoice", mpi.name)
		return mpi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror purchase bill failed")
		return None
