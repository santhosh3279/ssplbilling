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


def get_purchase_mirror_mapping(series_or_name, automatic_entries):
	"""Return {'purchase_series': ..., 'mirroring_series': ...} from automatic_entries.purchase_mirroring_series
	matching series_or_name, or None."""
	if not series_or_name or not automatic_entries:
		return None
	from frappe.model.naming import NamingSeries

	clean_input = series_or_name.strip().rstrip("/")
	try:
		input_prefix = NamingSeries(clean_input).get_prefix().strip() if clean_input else ""
	except Exception:
		input_prefix = clean_input

	for r in (automatic_entries.get("purchase_mirroring_series") or []):
		if not r.purchase_series:
			continue
		for p_val in r.purchase_series.split(","):
			p_val = p_val.strip()
			if not p_val:
				continue
			try:
				p_prefix = NamingSeries(p_val).get_prefix().strip() if p_val else ""
			except Exception:
				p_prefix = p_val

			if (
				clean_input == p_val
				or (p_prefix and clean_input == p_prefix)
				or clean_input.startswith(p_val)
				or (p_prefix and clean_input.startswith(p_prefix))
				or p_val.startswith(clean_input)
				or (p_prefix and input_prefix and p_prefix == input_prefix)
			):
				return {
					"purchase_series": p_val,
					"mirroring_series": (r.mirroring_series or "").strip(),
				}
	return None


def resolve_purchase_naming_series(series_str):
	"""Resolve series_str (e.g. 'PLV' or 'PLV.#####') to a valid Purchase Invoice naming series."""
	if not series_str:
		return "PINV-.#####"
	series_clean = series_str.strip()
	field = frappe.get_meta("Purchase Invoice").get_field("naming_series")
	options = [opt.strip() for opt in (field.options or "").split("\n") if opt.strip()]
	if series_clean in options:
		return series_clean
	from frappe.model.naming import NamingSeries
	for opt in options:
		prefix = NamingSeries(opt).get_prefix().strip()
		if series_clean == prefix or series_clean.rstrip(".") == prefix.rstrip("."):
			return opt
	if "#" not in series_clean:
		return f"{series_clean}.#####" if not series_clean.endswith(".") else f"{series_clean}#####"
	return series_clean


def should_mirror_purchase_invoice(naming_series, automatic_entries):
	"""Whether `naming_series` is configured in Automatic Entries for cross-company mirroring of purchases."""
	if not automatic_entries.alternative_company:
		return False
	if not naming_series:
		return False
	if get_purchase_mirror_mapping(naming_series, automatic_entries):
		return True
	for prefix in _purchase_mirror_series(automatic_entries):
		if naming_series == prefix or naming_series.startswith(prefix):
			return True
	return False


def get_available_purchase_mirror_name(naming_series, target_company):
	"""Next purchase invoice number for `naming_series`, taken from the bills already in
	`target_company` (highest existing number + 1), not from the shared `tabSeries` counter."""
	import re
	from frappe.model.naming import NamingSeries

	if not naming_series:
		field = frappe.get_meta("Purchase Invoice").get_field("naming_series")
		naming_series = (field.default if field else None) or "PINV-.#####"

	ns = NamingSeries(naming_series)
	prefix = ns.get_prefix()
	m = re.search(r"#+", naming_series)
	digits = len(m.group(0)) if m else 5

	# The series row is only used as a lock so two mirrors cannot pick the same number.
	if not frappe.db.sql("SELECT 1 FROM `tabSeries` WHERE name = %s", (prefix,)):
		frappe.db.sql("INSERT INTO `tabSeries` (name, current) VALUES (%s, 0)", (prefix,))
	frappe.db.sql("SELECT current FROM `tabSeries` WHERE name = %s FOR UPDATE", (prefix,))

	existing_names = frappe.db.get_all(
		"Purchase Invoice",
		filters={"company": target_company, "name": ["like", f"{prefix}%"]},
		pluck="name",
	)
	max_company_num = 0
	for n in existing_names:
		# Slashed names are original bills, not mirrors, so they never set the next number.
		if n.endswith("/"):
			continue
		clean = n[len(prefix):]
		if clean.isdigit():
			digits = max(digits, len(clean))
			val = int(clean)
			if val > max_company_num:
				max_company_num = val

	next_num = max_company_num + 1
	candidate = f"{prefix}{next_num:0{digits}d}"

	# Names are unique across companies, so skip numbers another company already holds.
	while frappe.db.exists("Purchase Invoice", candidate):
		next_num += 1
		candidate = f"{prefix}{next_num:0{digits}d}"

	# Keep the counter at or past every used number so native entries in this series never collide.
	frappe.db.sql("UPDATE `tabSeries` SET current = GREATEST(current, %s) WHERE name = %s", (next_num, prefix))

	return candidate


def _mirrors_purchase_bill(pi, automatic_entries):
	"""Whether `pi` is an original bill in a series set for purchase mirroring.
	Bills in the alternate company are mirrors themselves and are never mirrored again."""
	if not automatic_entries.alternative_company or pi.company == automatic_entries.alternative_company:
		return False
	return bool(
		should_mirror_purchase_invoice(pi.naming_series, automatic_entries)
		or (pi.name and should_mirror_purchase_invoice(pi.name, automatic_entries))
	)


def is_purchase_mirror(doc, automatic_entries=None):
	"""Whether `doc` is the alternate-company mirror of another bill that links back to it."""
	ae = automatic_entries or get_automatic_entries()
	if not ae.alternative_company or doc.company != ae.alternative_company or not doc.get("custom_mirrored"):
		return False
	partner = frappe.db.get_value("Purchase Invoice", doc.custom_mirrored, ["company", "custom_mirrored"], as_dict=True)
	return bool(partner and partner.company != ae.alternative_company and partner.custom_mirrored == doc.name)


def find_purchase_mirror(pi, automatic_entries):
	"""The non-cancelled alternate-company bill paired with `pi`, as {name, docstatus}, or None.

	PG.##### and PG0.#### render the same names (PG + 00124 == PG0 + 0124), so a bill found by
	the slash-toggled name only counts if it is unlinked or already links back to `pi`."""
	has_mirror_field = frappe.get_meta("Purchase Invoice").has_field("custom_mirrored")
	old_mirror_name = pi.name[:-1] if pi.name.endswith("/") else f"{pi.name}/"
	for name in (pi.get("custom_mirrored"), old_mirror_name):
		if not name:
			continue
		rows = frappe.get_all(
			"Purchase Invoice",
			filters={"name": name, "company": automatic_entries.alternative_company, "docstatus": ["<", 2]},
			fields=["name", "docstatus", "custom_mirrored"] if has_mirror_field else ["name", "docstatus"],
		)
		if rows and (rows[0].get("custom_mirrored") or "") in ("", pi.name):
			return rows[0]
	return None


def _link_purchase_pair(pi, mpi):
	"""Point the original and its mirror at each other without touching `modified`,
	so the in-memory docs can still be saved or submitted in the same request."""
	if not frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		return
	for doc, partner in ((pi, mpi), (mpi, pi)):
		if doc.get("custom_mirrored") != partner.name:
			frappe.db.set_value("Purchase Invoice", doc.name, "custom_mirrored", partner.name, update_modified=False)
			doc.custom_mirrored = partner.name


def _fill_mirror_from_parent(mpi, pi, automatic_entries):
	"""Copy `pi`'s supplier, bill details, warehouse, discount, items and taxes onto mirror `mpi`,
	replacing whatever rows it had, with warehouses, cost centers, accounts and tax templates
	moved into the alternate company."""
	target_company = automatic_entries.alternative_company

	source_warehouse = pi.set_warehouse or (pi.items[0].warehouse if pi.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or automatic_entries.warehouse

	source_cost_center = pi.cost_center or (pi.items[0].cost_center if pi.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)

	allowed_accounts = _allowed_accounts(automatic_entries)

	mpi.supplier = pi.supplier
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

	mpi.set("items", [])
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
		if item.batch_no:
			# Batches are not per company, so the mirror receives into the same batch
			row["batch_no"] = item.batch_no
			row["use_serial_batch_fields"] = 1
		mpi.append("items", row)

	mpi.taxes_and_charges = pi.taxes_and_charges
	mpi.set("taxes", [])
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


def create_mirror_purchase_invoice(pi, automatic_entries):
	"""Create the draft mirror of `pi` in the alternate company, named with the next number of the
	configured mirroring series among that company's bills, and link the two bills."""
	target_company = automatic_entries.alternative_company
	mapping = get_purchase_mirror_mapping(pi.naming_series, automatic_entries)
	if not mapping and pi.name:
		mapping = get_purchase_mirror_mapping(pi.name, automatic_entries)

	if mapping and mapping.get("mirroring_series"):
		target_naming_series = resolve_purchase_naming_series(mapping["mirroring_series"])
	else:
		target_naming_series = pi.naming_series

	mirror_name = get_available_purchase_mirror_name(target_naming_series, target_company)

	mpi = frappe.new_doc("Purchase Invoice")
	mpi.company = target_company
	mpi.naming_series = target_naming_series
	if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		mpi.custom_mirrored = pi.name
	_fill_mirror_from_parent(mpi, pi, automatic_entries)

	mpi.flags.ignore_permissions = True
	mpi.insert(set_name=mirror_name)
	_link_purchase_pair(pi, mpi)
	return mpi


def create_purchase_mirror_draft(pi):
	"""On the first save of `pi`, create its draft mirror if its series is set for mirroring.
	A failure is logged and never blocks the save; submit_purchase_mirror creates it again."""
	ae = get_automatic_entries()
	if not _mirrors_purchase_bill(pi, ae):
		return None

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	from ssplbilling.api.mirror_error_log import log_mirror_error, resolve_mirror_errors

	try:
		found = find_purchase_mirror(pi, ae)
		mpi = frappe.get_doc("Purchase Invoice", found.name) if found else create_mirror_purchase_invoice(pi, ae)
		_link_purchase_pair(pi, mpi)
		frappe.db.release_savepoint(sp)
		resolve_mirror_errors("Purchase Mirror Bill", "Purchase Invoice", pi.name)
		return mpi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror purchase draft failed")
		log_mirror_error("Purchase Mirror Bill", "Purchase Invoice", pi.name, None, ae.alternative_company)
		return None


def submit_purchase_mirror(pi):
	"""After `pi` is submitted, bring its mirror up to date with it and submit the mirror,
	creating the mirror first if it has none. Raises on failure so the caller's transaction,
	including `pi`'s own submit, rolls back and neither bill is submitted."""
	ae = get_automatic_entries()
	if not _mirrors_purchase_bill(pi, ae):
		return None

	found = find_purchase_mirror(pi, ae)
	if found and found.docstatus == 1:
		mpi = frappe.get_doc("Purchase Invoice", found.name)
		_link_purchase_pair(pi, mpi)
		return mpi

	mpi = frappe.get_doc("Purchase Invoice", found.name) if found else create_mirror_purchase_invoice(pi, ae)
	_fill_mirror_from_parent(mpi, pi, ae)
	mpi.flags.ignore_permissions = True
	mpi.submit()
	_link_purchase_pair(pi, mpi)

	from ssplbilling.api.mirror_error_log import resolve_mirror_errors

	resolve_mirror_errors("Purchase Mirror Bill", "Purchase Invoice", pi.name)
	return mpi


def delete_purchase_mirror_draft(pi):
	"""Delete the draft mirror of draft `pi`, before `pi` itself is deleted."""
	ae = get_automatic_entries()
	if not ae.alternative_company:
		return
	found = find_purchase_mirror(pi, ae)
	if found and found.docstatus == 0:
		frappe.delete_doc("Purchase Invoice", found.name, ignore_permissions=True)
