import frappe
from ssplbilling.api.automatic_entries_api import (
	get_automatic_entries,
	mirror_name_for,
	_allowed_accounts,
	resolve_target_account,
	resolve_target_item_tax_template,
	ensure_warehouse_in_company,
	ensure_cost_center_in_company,
)
from ssplbilling.api.mirror_error_log import log_mirror_error, resolve_mirror_errors


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
	"""Whether `naming_series` (or a bill name) is in a Purchase Invoice Series of Automatic
	Entries, so the bill is mirrored into the alternative company."""
	if not automatic_entries.alternative_company:
		return False
	if not naming_series:
		return False
	for prefix in _purchase_mirror_series(automatic_entries):
		if naming_series == prefix or naming_series.startswith(prefix):
			return True
	return False


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


def create_mirror_purchase_invoice(pi, automatic_entries, submit=True):
	"""Create the mirror of `pi` in the alternative company, the same way sales bills are
	mirrored: same naming series, named `<pi.name>/` (mirror_name_for), linked both ways
	through `custom_mirrored`. Submitted unless `submit` is False."""
	mpi = frappe.new_doc("Purchase Invoice")
	mpi.company = automatic_entries.alternative_company
	mpi.naming_series = pi.naming_series
	if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		mpi.custom_mirrored = pi.name
	_fill_mirror_from_parent(mpi, pi, automatic_entries)

	mpi.flags.ignore_permissions = True
	mpi.insert(set_name=mirror_name_for(pi.name))
	if submit:
		mpi.submit()
	_link_purchase_pair(pi, mpi)
	return mpi


def mirror_purchase_bill(pi):
	"""Mirror submitted `pi` into the alternative company if its series is set for mirroring.
	Returns the mirror doc, or None. An existing submitted mirror is kept as it is; a draft
	mirror left by the old save-time mirroring is refreshed from `pi` and submitted.
	Isolated with a savepoint and logged on failure, so `pi` itself is never affected."""
	ae = get_automatic_entries()
	if not _mirrors_purchase_bill(pi, ae):
		return None

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		found = find_purchase_mirror(pi, ae)
		if found and found.docstatus == 1:
			mpi = frappe.get_doc("Purchase Invoice", found.name)
		elif found:
			mpi = frappe.get_doc("Purchase Invoice", found.name)
			_fill_mirror_from_parent(mpi, pi, ae)
			mpi.flags.ignore_permissions = True
			mpi.submit()
		else:
			mpi = create_mirror_purchase_invoice(pi, ae)
		_link_purchase_pair(pi, mpi)
		frappe.db.release_savepoint(sp)
		resolve_mirror_errors("Purchase Mirror Bill", "Purchase Invoice", pi.name)
		return mpi
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror purchase bill failed")
		log_mirror_error(
			"Purchase Mirror Bill", "Purchase Invoice", pi.name, mirror_name_for(pi.name), ae.alternative_company
		)
		return None


def queue_purchase_mirror(pi):
	"""Queue mirroring of submitted `pi` after the request commits, like the cashier's sales
	mirror. Returns True when a job was queued."""
	try:
		if not _mirrors_purchase_bill(pi, get_automatic_entries()):
			return False
		frappe.enqueue(
			"ssplbilling.api.purchase_mirror_api.run_purchase_mirror",
			queue="long",
			enqueue_after_commit=True,
			job_id=f"purchase-mirror:{pi.name}",
			deduplicate=True,
			invoice_name=pi.name,
		)
		return True
	except Exception:
		frappe.log_error(title="Automatic Entries: queue purchase mirror failed", message=frappe.get_traceback())
		return False


def run_purchase_mirror(invoice_name):
	"""Worker: create the mirror once the source bill is committed."""
	pi = frappe.get_doc("Purchase Invoice", invoice_name)
	if pi.docstatus != 1:
		frappe.throw(f"Purchase Invoice {invoice_name} must be submitted before mirroring.")
	mirror_purchase_bill(pi)


def delete_purchase_mirror_draft(pi):
	"""Delete the draft mirror of draft `pi`, before `pi` itself is deleted (drafts left by
	the old save-time mirroring)."""
	ae = get_automatic_entries()
	if not ae.alternative_company:
		return
	found = find_purchase_mirror(pi, ae)
	if found and found.docstatus == 0:
		frappe.delete_doc("Purchase Invoice", found.name, ignore_permissions=True)


@frappe.whitelist()
def retry_purchase_mirror_bill(invoice_name):
	"""Manually mirror an already-submitted Purchase Invoice now (Ctrl+Shift+O in the
	Purchase Invoice page), e.g. when the background mirror failed.

	Unlike `mirror_purchase_bill`, a failure is NOT swallowed into the Error Log; the
	exception propagates so the operator sees why it failed.

	Returns one of:
	  {"status": "exists",  "invoice_name": ...}  submitted mirror already there, nothing done
	  {"status": "created", "invoice_name": ...}  mirror created (or its old draft submitted) now
	  {"status": "not_configured"}                series is not set for purchase mirroring
	"""
	pi = frappe.get_doc("Purchase Invoice", invoice_name)
	pi.check_permission("submit")
	if pi.docstatus != 1:
		frappe.throw("Only a submitted Purchase Invoice can be mirrored.")

	ae = get_automatic_entries()
	# Checked first: a bill in the alternate company is a mirror itself, so pressing the
	# key on it reports "not configured" rather than a misleading "already created".
	if not _mirrors_purchase_bill(pi, ae):
		return {"status": "not_configured"}

	found = find_purchase_mirror(pi, ae)
	if found and found.docstatus == 1:
		_link_purchase_pair(pi, frappe.get_doc("Purchase Invoice", found.name))
		return {"status": "exists", "invoice_name": found.name, "company": ae.alternative_company}

	# Same as submit: the mirror needs its items marked as GST items.
	try:
		from ssplbilling.api.purchase_api import map_items_as_gst_item

		item_codes = list({item.item_code for item in pi.items if item.item_code})
		if item_codes:
			map_items_as_gst_item(item_codes)
	except Exception:
		frappe.log_error(title="Purchase mirror: map items as GST items failed", message=frappe.get_traceback())

	if found:
		mpi = frappe.get_doc("Purchase Invoice", found.name)
		_fill_mirror_from_parent(mpi, pi, ae)
		mpi.flags.ignore_permissions = True
		mpi.submit()
	else:
		mpi = create_mirror_purchase_invoice(pi, ae)
	_link_purchase_pair(pi, mpi)
	resolve_mirror_errors("Purchase Mirror Bill", "Purchase Invoice", pi.name)
	return {"status": "created", "invoice_name": mpi.name, "company": mpi.company}
