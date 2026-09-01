import frappe
from frappe.utils import getdate, nowdate, nowtime


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


def should_mirror_sales_invoice(naming_series, automatic_entries, company=None):
	"""Whether `naming_series` is configured in Automatic Entries for cross-company mirroring."""
	if not automatic_entries.alternative_company:
		return False
	if company and company == automatic_entries.alternative_company:
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
def resolve_account_to_company(account, company):
	"""Return `account` mapped onto `company`'s chart of accounts.

	Globally configured accounts — the SSPL Billing Settings discount account above
	all — carry a single company's tag, so using one against another company either
	fails validation when posting or silently matches nothing when filtering.
	Accounts that already belong to `company` (or that are not Account records at
	all) are returned untouched; otherwise this falls back to the company's
	write_off_account, then to the original value.
	"""
	if not account or not company:
		return account or ""

	account_company = frappe.db.get_value("Account", account, "company")
	if account_company in (None, company):
		return account

	return (
		resolve_target_account(account, [], company)
		or frappe.get_cached_value("Company", company, "write_off_account")
		or account
	)


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


def resolve_target_taxes_and_charges_template(source_template, source_company, target_company):
	"""Resolve a source Sales Taxes and Charges Template to its equivalent in the target company.
	First tries to replace the abbreviation, then falls back to title matching.
	"""
	if not source_template or not target_company:
		return ""

	if source_company:
		source_abbr = frappe.db.get_value("Company", source_company, "abbr")
		target_abbr = frappe.db.get_value("Company", target_company, "abbr")
		if source_abbr and target_abbr:
			suffix = f" - {source_abbr}"
			if source_template.endswith(suffix):
				target_template_name = source_template[:-len(suffix)] + f" - {target_abbr}"
				if frappe.db.exists("Sales Taxes and Charges Template", target_template_name):
					return target_template_name

	title = frappe.db.get_value("Sales Taxes and Charges Template", source_template, "title")
	if title:
		target_template = frappe.db.get_value(
			"Sales Taxes and Charges Template", {"company": target_company, "title": title}, "name"
		)
		if target_template:
			return target_template
	return ""


def get_interstate_tax_template(tax_template, target_company, is_interstate=False):
	"""Resolve and swap In-State and Out-State tax templates based on company vs party state comparison."""
	if not tax_template:
		return tax_template

	title = frappe.db.get_value("Sales Taxes and Charges Template", tax_template, "title") or tax_template

	new_title = title
	replacements = []
	if is_interstate:
		replacements = [
			("In-state", "Out-state"),
			("In state", "Out state"),
			("in-state", "out-state"),
			("in state", "out state"),
			("IN-STATE", "OUT-STATE"),
			("IN STATE", "OUT STATE"),
		]
	else:
		replacements = [
			("Out-state", "In-state"),
			("Out state", "In state"),
			("out-state", "in-state"),
			("out state", "in state"),
			("OUT-STATE", "IN-STATE"),
			("OUT STATE", "IN STATE"),
		]

	for src, dest in replacements:
		if src in new_title:
			new_title = new_title.replace(src, dest)

	if new_title != title:
		target_template = frappe.db.get_value(
			"Sales Taxes and Charges Template", {"company": target_company, "title": new_title}, "name"
		)
		if target_template:
			return target_template

	return None


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


def mirror_name_for(name):
	"""Name of the mirror document for `name`. The rule is bidirectional: a source
	name gains a trailing slash, and a name that already ends in one (a return series
	such as RTN06879/) loses it, so the pair never collides."""
	return name[:-1] if name.endswith("/") else f"{name}/"


def create_mirror_sales_invoice(si, automatic_entries):
	"""Create + submit a mirror Sales Invoice for `si` in the alternate company, named
	si.name + '/', posted against the Automatic Entries warehouse with accounts
	substituted via resolve_target_account."""
	mirror_name = mirror_name_for(si.name)
	if frappe.db.exists("Sales Invoice", mirror_name):
		return frappe.get_doc("Sales Invoice", mirror_name)

	target_company = automatic_entries.alternative_company
	
	source_warehouse = si.set_warehouse or (si.items[0].warehouse if si.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or automatic_entries.warehouse
	
	source_cost_center = si.cost_center or (si.items[0].cost_center if si.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)
	
	allowed_accounts = _allowed_accounts(automatic_entries)
	allow_zero_valuation = int(automatic_entries.get("mirror_allow_zero_valuation_rate") or 0)

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
		if allow_zero_valuation:
			# The alternate company may never have received these items, so its FIFO
			# queue has no rate to consume and ERPNext would throw "Valuation Rate
			# Missing" on submit. Mirror rows then post stock movement without COGS.
			row["allow_zero_valuation_rate"] = 1
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

	# Determine if it's interstate
	is_interstate = False
	company_address = frappe.db.get_value("Dynamic Link", {"link_doctype": "Company", "link_name": target_company, "parenttype": "Address"}, "parent")
	company_state = frappe.db.get_value("Address", company_address, "state") if company_address else ""
	if not company_state:
		company_links = frappe.db.get_all("Dynamic Link", {"link_doctype": "Company", "link_name": target_company, "parenttype": "Address"}, ["parent"])
		for link in company_links:
			company_state = frappe.db.get_value("Address", link.parent, "state")
			if company_state:
				break

	party_state = ""
	if si.customer_address:
		party_state = frappe.db.get_value("Address", si.customer_address, "state") or ""
	if not party_state and si.place_of_supply:
		party_state = si.place_of_supply.split("-")[-1].strip()
	if not party_state and si.customer:
		cust_address = frappe.db.get_value("Dynamic Link", {"link_doctype": "Customer", "link_name": si.customer, "parenttype": "Address"}, "parent")
		if cust_address:
			party_state = frappe.db.get_value("Address", cust_address, "state") or ""

	if company_state and party_state:
		is_interstate = (company_state.lower().strip() != party_state.lower().strip())

	applied_tax_template = None
	if si.taxes_and_charges:
		resolved_template = resolve_target_taxes_and_charges_template(si.taxes_and_charges, si.company, target_company) or si.taxes_and_charges
		adjusted_template = get_interstate_tax_template(resolved_template, target_company, is_interstate)
		applied_tax_template = adjusted_template or resolved_template

	source_is_inclusive = any(int(t.included_in_print_rate or 0) for t in si.taxes)

	if applied_tax_template:
		msi.taxes_and_charges = applied_tax_template
		from erpnext.controllers.accounts_controller import get_taxes_and_charges
		taxes = get_taxes_and_charges("Sales Taxes and Charges Template", applied_tax_template)
		msi.taxes = []
		for tax in taxes:
			tax_row = {
				"charge_type": tax.get("charge_type"),
				"account_head": tax.get("account_head"),
				"description": tax.get("description"),
				"rate": tax.get("rate"),
				"included_in_print_rate": 1 if source_is_inclusive else tax.get("included_in_print_rate"),
			}
			if tax.get("cost_center"):
				tax_row["cost_center"] = ensure_cost_center_in_company(tax.get("cost_center"), target_company)
			msi.append("taxes", tax_row)
	else:
		for tax in si.taxes:
			tax_row = {
				"charge_type": tax.charge_type,
				"account_head": resolve_target_account(tax.account_head, allowed_accounts, target_company) or tax.account_head,
				"description": tax.description,
				"rate": tax.rate,
				"included_in_print_rate": 1 if source_is_inclusive else tax.included_in_print_rate,
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
	if not should_mirror_sales_invoice(si.naming_series, ae, si.company):
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


@frappe.whitelist()
def retry_mirror_bill(sales_invoice_name):
	"""Manually create the mirror bill (and its payments) for an already-submitted
	Sales Invoice whose automatic mirroring failed.

	Unlike `mirror_bill`, this does NOT swallow the failure into the Error Log — the
	exception propagates so the operator sees why it failed and can fix it.

	Returns one of:
	  {"status": "exists",         "invoice_name": ...}  mirror already there, nothing done
	  {"status": "created",        "invoice_name": ...}  mirror created now
	  {"status": "not_configured"}                       series is not set up for mirroring
	"""
	si = frappe.get_doc("Sales Invoice", sales_invoice_name)
	if si.docstatus != 1:
		frappe.throw("Only a submitted Sales Invoice can be mirrored.")

	ae = get_automatic_entries()
	# Checked before the exists lookup on purpose: should_mirror_sales_invoice is False
	# when si is itself in the alternate company, so opening a mirror and pressing the
	# key reports "not configured" rather than a misleading "already created".
	if not should_mirror_sales_invoice(si.naming_series, ae, si.company):
		return {"status": "not_configured"}

	mirror_name = mirror_name_for(si.name)
	if frappe.db.exists("Sales Invoice", mirror_name):
		return {"status": "exists", "invoice_name": mirror_name, "company": ae.alternative_company}

	msi = create_mirror_sales_invoice(si, ae)

	# A mirror that was just created has no payments yet, so this cannot double-post.
	# The helpers are the same ones the GST-conversion mirror uses and derive the
	# amounts from si's own submitted Payment Entries / Journal Entries.
	payments_error = None
	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		from ssplbilling.api.cashier_mirroring_api import mirror_payments_for_gst_conversion

		mirror_payments_for_gst_conversion(si, msi, ae)
		frappe.db.release_savepoint(sp)
	except Exception as e:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: manual mirror payments failed")
		payments_error = str(e)

	return {
		"status": "created",
		"invoice_name": msi.name,
		"company": msi.company,
		"payments_error": payments_error,
	}









def mirror_standalone_payment_entry(pe):
	"""Mirror a standalone Payment Entry (paymentv2 flow) into the Automatic Entries
	alternative company, named pe.name + '/'. Only fires when every involved bank/cash
	account is whitelisted in the Automatic Entries accounts table (party accounts are
	exempt — they are resolved/created via ensure_account_in_company). References are
	re-linked to their mirrored counterparts ('<name>/') when those exist and are
	submitted. Savepoint-isolated: a failure never rolls back the source entry.
	Returns the mirror name, or None when not applicable/failed."""
	ae = get_automatic_entries()
	target_company = ae.alternative_company
	if not target_company or pe.company == target_company:
		return None

	allowed = _allowed_accounts(ae)
	if pe.payment_type == "Receive":
		mop_side = [pe.paid_to]
	elif pe.payment_type == "Pay":
		mop_side = [pe.paid_from]
	else:  # Internal Transfer — both sides are plain accounts
		mop_side = [pe.paid_from, pe.paid_to]
	if not all(a and a in allowed for a in mop_side):
		return None

	if ae.payment_entry_naming_settings:
		existing = frappe.db.get_value(
			"Payment Entry",
			{"company": target_company, "remarks": ["like", f"%Mirrored from {pe.name}%"], "docstatus": ["!=", 2]},
			"name"
		)
		if existing:
			return existing
		mirror_name = None
	else:
		mirror_name = f"{pe.name}/"
		if frappe.db.exists("Payment Entry", mirror_name):
			return mirror_name

	sp = "sp_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(sp)
	try:
		mpe = frappe.new_doc("Payment Entry")
		mpe.payment_type = pe.payment_type
		mpe.company = target_company
		mpe.posting_date = pe.posting_date
		if pe.party_type and pe.party:
			mpe.party_type = pe.party_type
			mpe.party = pe.party
		mpe.paid_from_account_currency = pe.paid_from_account_currency
		mpe.paid_to_account_currency = pe.paid_to_account_currency
		mpe.source_exchange_rate = pe.source_exchange_rate
		mpe.target_exchange_rate = pe.target_exchange_rate
		mpe.paid_amount = pe.paid_amount
		mpe.received_amount = pe.received_amount
		if pe.reference_no:
			mpe.reference_no = pe.reference_no
			mpe.reference_date = pe.reference_date or pe.posting_date
		original_remarks = pe.remarks or ""
		mpe.remarks = f"{original_remarks}\nMirrored from {pe.name}".strip()
		mpe.custom_remarks = 1
		if pe.get("custom_remarks"):
			mpe.set("custom_remarks", pe.get("custom_remarks"))
		if pe.cost_center:
			mpe.cost_center = ensure_cost_center_in_company(pe.cost_center, target_company)

		if pe.payment_type == "Receive":
			mpe.paid_from = ensure_account_in_company(pe.paid_from, target_company)
			mpe.paid_to = resolve_target_account(pe.paid_to, allowed, target_company)
		elif pe.payment_type == "Pay":
			mpe.paid_from = resolve_target_account(pe.paid_from, allowed, target_company)
			mpe.paid_to = ensure_account_in_company(pe.paid_to, target_company)
		else:
			mpe.paid_from = resolve_target_account(pe.paid_from, allowed, target_company)
			mpe.paid_to = resolve_target_account(pe.paid_to, allowed, target_company)

		if not mpe.paid_from or not mpe.paid_to:
			frappe.db.rollback(save_point=sp)
			return None

		# Prefer the target company's MOP for the mapped account; otherwise keep the
		# source MOP rather than _mop_for_account's "Cash" fallback.
		mop_account = mpe.paid_from if pe.payment_type == "Pay" else mpe.paid_to
		target_mop = frappe.db.get_value(
			"Mode of Payment Account", {"default_account": mop_account, "company": target_company}, "parent"
		)
		mpe.mode_of_payment = target_mop or pe.mode_of_payment

		# Re-link allocations against mirrored vouchers when they exist,
		# belong to the target company and are submitted (drafts cannot be allocated).
		for ref in (pe.references or []):
			mirror_ref = ref.reference_name[:-1] if ref.reference_name.endswith("/") else f"{ref.reference_name}/"
			if not frappe.db.exists(ref.reference_doctype, mirror_ref):
				continue
			ref_doc = frappe.db.get_value(
				ref.reference_doctype, mirror_ref, ["company", "docstatus", "outstanding_amount"], as_dict=True
			)
			if not ref_doc or ref_doc.company != target_company or ref_doc.docstatus != 1:
				continue
			allocated = min(ref.allocated_amount or 0, ref_doc.outstanding_amount or 0)
			if allocated > 0:
				mpe.append("references", {
					"reference_doctype": ref.reference_doctype,
					"reference_name": mirror_ref,
					"allocated_amount": allocated,
				})

		mpe.flags.ignore_permissions = True
		if ae.payment_entry_naming_settings:
			mpe.naming_series = ae.payment_entry_naming_settings
			mpe.insert()
		elif mirror_name:
			mpe.insert(set_name=mirror_name)
		else:
			mpe.insert()
		mpe.submit()
		frappe.db.release_savepoint(sp)
		return mpe.name
	except Exception:
		frappe.db.rollback(save_point=sp)
		frappe.log_error(frappe.get_traceback(), "Automatic Entries: standalone payment mirror failed")
		return None


def create_mirror_invoice_for_gst_conversion(si, ae, naming_series=None, price_list=None, tax_template=None, tax_type_incl=None, use_series_naming=False, submit=True, posting_date=None):
	"""Create a mirror Sales Invoice in target company (ae_company) for a Sales Invoice
	that is being converted to a GST bill (Quotation).
	It creates a Sales Invoice in target company, with name si.name + '/', and copies all accounts,
	creating them in the target company if they don't exist.

	With use_series_naming=True the mirror is named from `naming_series` instead of
	si.name + '/', so repeated calls create new invoices (manual conversion mirroring).
	"""
	mirror_name = None if use_series_naming else mirror_name_for(si.name)
	if mirror_name and frappe.db.exists("Sales Invoice", mirror_name):
		return frappe.get_doc("Sales Invoice", mirror_name)

	target_company = ae.alternative_company
	
	source_warehouse = si.set_warehouse or (si.items[0].warehouse if si.items else None)
	target_warehouse = ensure_warehouse_in_company(source_warehouse, target_company) or ae.warehouse
	
	source_cost_center = si.cost_center or (si.items[0].cost_center if si.items else None)
	target_cost_center = ensure_cost_center_in_company(source_cost_center, target_company)

	allow_zero_valuation = int(ae.get("mirror_allow_zero_valuation_rate") or 0)

	msi = frappe.new_doc("Sales Invoice")
	msi.company = target_company
	msi.customer = si.customer
	if si.customer_address:
		msi.customer_address = si.customer_address
	msi.naming_series = naming_series or si.naming_series
	# `posting_date` overrides the source date for mirrors raised by hand long after
	# the original was billed; the automatic same-day mirror passes nothing and keeps
	# the source date.
	msi.posting_date = posting_date or si.posting_date
	msi.posting_time = nowtime() if posting_date else si.posting_time
	msi.set_posting_time = 1
	msi.due_date = si.due_date
	if msi.due_date and getdate(msi.due_date) < getdate(msi.posting_date):
		# A due date copied from an older invoice would be before the mirror's own
		# posting date, which ERPNext rejects.
		msi.due_date = msi.posting_date
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
		if allow_zero_valuation:
			# The alternate company may never have received these items, so its FIFO
			# queue has no rate to consume and ERPNext would throw "Valuation Rate
			# Missing" on submit. Mirror rows then post stock movement without COGS.
			row["allow_zero_valuation_rate"] = 1
		if item_cc:
			row["cost_center"] = item_cc
		if item.item_tax_template:
			target_tax_template = resolve_target_item_tax_template(item.item_tax_template, target_company)
			if target_tax_template:
				row["item_tax_template"] = target_tax_template
		if item.income_account:
			row["income_account"] = ensure_account_in_company(item.income_account, target_company)
		msi.append("items", row)

	# Determine if it's interstate
	is_interstate = False
	company_address = frappe.db.get_value("Dynamic Link", {"link_doctype": "Company", "link_name": target_company, "parenttype": "Address"}, "parent")
	company_state = frappe.db.get_value("Address", company_address, "state") if company_address else ""
	if not company_state:
		company_links = frappe.db.get_all("Dynamic Link", {"link_doctype": "Company", "link_name": target_company, "parenttype": "Address"}, ["parent"])
		for link in company_links:
			company_state = frappe.db.get_value("Address", link.parent, "state")
			if company_state:
				break

	party_state = ""
	if si.customer_address:
		party_state = frappe.db.get_value("Address", si.customer_address, "state") or ""
	if not party_state and si.place_of_supply:
		party_state = si.place_of_supply.split("-")[-1].strip()
	if not party_state and si.customer:
		cust_address = frappe.db.get_value("Dynamic Link", {"link_doctype": "Customer", "link_name": si.customer, "parenttype": "Address"}, "parent")
		if cust_address:
			party_state = frappe.db.get_value("Address", cust_address, "state") or ""

	if company_state and party_state:
		is_interstate = (company_state.lower().strip() != party_state.lower().strip())

	applied_tax_template = None

	# Determine if the source template is exempted (e.g. "Exempted - SSPL")
	is_exempted = True
	if si.taxes_and_charges:
		title = frappe.db.get_value("Sales Taxes and Charges Template", si.taxes_and_charges, "title") or si.taxes_and_charges
		is_exempted = "exempt" in title.lower()

	# If original bill has a tax template and it is NOT exempted, map it to target company.
	# Otherwise, use the series tax template from local storage.
	source_template_to_use = None
	if si.taxes_and_charges and not is_exempted:
		source_template_to_use = si.taxes_and_charges
	else:
		source_template_to_use = tax_template or si.taxes_and_charges

	if source_template_to_use:
		resolved_template = resolve_target_taxes_and_charges_template(source_template_to_use, si.company, target_company) or source_template_to_use
		adjusted_template = get_interstate_tax_template(resolved_template, target_company, is_interstate)
		applied_tax_template = adjusted_template or resolved_template

	is_inclusive = False
	if tax_type_incl is not None:
		is_inclusive = bool(int(tax_type_incl))
	else:
		is_inclusive = any(int(t.included_in_print_rate or 0) for t in si.taxes)

	if applied_tax_template:
		msi.taxes_and_charges = applied_tax_template
		from erpnext.controllers.accounts_controller import get_taxes_and_charges
		taxes = get_taxes_and_charges("Sales Taxes and Charges Template", applied_tax_template)
		for tax in taxes:
			tax_row = {
				"charge_type": tax.get("charge_type"),
				"account_head": tax.get("account_head"),
				"description": tax.get("description"),
				"rate": tax.get("rate"),
				"included_in_print_rate": 1 if is_inclusive else tax.get("included_in_print_rate"),
			}
			if tax.get("cost_center"):
				tax_row["cost_center"] = ensure_cost_center_in_company(tax.get("cost_center"), target_company)
			msi.append("taxes", tax_row)
	else:
		for tax in si.taxes:
			tax_row = {
				"charge_type": tax.charge_type,
				"account_head": ensure_account_in_company(tax.account_head, target_company) or tax.account_head,
				"description": tax.description,
				"rate": tax.rate,
				"included_in_print_rate": 1 if is_inclusive else tax.included_in_print_rate,
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
		# Replicate payment entries and journal entries associated with the original Sales Invoice `si`
		sp = "sp_" + frappe.generate_hash(length=10)
		frappe.db.savepoint(sp)
		try:
			from ssplbilling.api.cashier_mirroring_api import mirror_payments_for_gst_conversion
			mirror_payments_for_gst_conversion(si, msi, ae)
			frappe.db.release_savepoint(sp)
		except Exception:
			frappe.db.rollback(save_point=sp)
			frappe.log_error(frappe.get_traceback(), "Automatic Entries: mirror converted payments failed")
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
def create_conversion_mirror_invoice(sales_invoice_name, naming_series, price_list=None, tax_template=None, tax_type_incl=None):
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

	if tax_template is None or tax_type_incl is None:
		try:
			settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
			base_series = naming_series.split(".")[0] if naming_series else ""
			for row in settings.billing_series or []:
				row_series = row.series.split(".")[0] if row.series else ""
				if row_series == base_series:
					if tax_template is None:
						tax_template = row.tax_template
					if tax_type_incl is None:
						tax_type_incl = row.tax_type_incl
					break
		except Exception:
			pass

	si = frappe.get_doc("Sales Invoice", sales_invoice_name)
	msi = create_mirror_invoice_for_gst_conversion(
		si, ae, naming_series=naming_series, price_list=price_list, tax_template=tax_template, tax_type_incl=tax_type_incl, use_series_naming=True, submit=False, posting_date=nowdate()
	)
	return {"status": "success", "invoice_name": msi.name, "company": msi.company}


def _naming_series_options(doctype):
	"""Naming series configured for `doctype`, as a list of strings. Property Setter
	first, since that is where a site's customised series lives."""
	options = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": "naming_series", "property": "options"},
		"value",
	)
	if not options:
		field = frappe.get_meta(doctype).get_field("naming_series")
		options = field.options if field else ""
	return [opt.strip() for opt in (options or "").split("\n") if opt.strip()]


@frappe.whitelist()
def get_payment_entry_series():
	"""Return naming series configured for Payment Entry as a list of strings."""
	return _naming_series_options("Payment Entry")


@frappe.whitelist()
def get_journal_entry_series():
	"""Return naming series configured for Journal Entry as a list of strings."""
	return _naming_series_options("Journal Entry")

