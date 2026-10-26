import frappe
import json


def _find_item_by_name(item_name, exclude_item=None):
	"""Return the code of an item whose name matches, else "". Both sides are trimmed —
	legacy rows carry leading spaces — and the DB collation makes it case-insensitive."""
	item_name = (item_name or "").strip()
	if not item_name:
		return ""
	rows = frappe.db.sql(
		"select name from `tabItem` where trim(item_name) = %s and name != %s limit 1",
		(item_name, exclude_item or ""),
	)
	return rows[0][0] if rows else ""


def _check_duplicate_item_name(item_name, exclude_item=None):
	"""Item names must be unique (print names may repeat)."""
	existing = _find_item_by_name(item_name, exclude_item)
	if existing:
		frappe.throw(
			f"Item name '{(item_name or '').strip()}' already exists (Item {existing})",
			title="Duplicate Item Name",
		)


@frappe.whitelist()
def check_item_name_exists(item_name, exclude_item=None):
	"""Live duplicate check for the item creation form. Returns the existing item code, or ""
	(not None — the frontend transport falls back to the whole response on a null message)."""
	return _find_item_by_name(item_name, exclude_item)


@frappe.whitelist()
def get_item_creation_metadata(company=None):
	"""Fetch all metadata needed for the item creation form.

	Item Tax Templates are company-scoped, so they are filtered to `company`
	(the frontend's wb-company) falling back to the user's default company.
	With neither resolvable, every template is returned rather than none.
	"""
	company = company or frappe.defaults.get_user_default("company")
	tax_filters = {"company": company} if company else {}
	return {
		"item_groups": frappe.get_all("Item Group", filters={"is_group": 0}, fields=["name"]),
		"uoms": frappe.get_all("UOM", fields=["name"]),
		"tax_templates": frappe.get_all("Item Tax Template", filters=tax_filters, fields=["name"]),
		"hsn_codes": frappe.get_all("GST HSN Code", fields=["name", "description"]),
		"competitive_items": frappe.get_all("Competitive Item", fields=["name"], order_by="name asc"),
		"naming_series": get_item_naming_series()
	}


@frappe.whitelist()
def get_item_attributes():
	"""Enabled Item Attributes with their values (or numeric range) for the variants tab.
	The frontend keeps this in IndexedDB and refetches it on item_attribute_update."""
	attributes = frappe.get_all(
		"Item Attribute",
		filters={"disabled": 0},
		fields=["name", "numeric_values", "from_range", "to_range", "increment"],
		order_by="name asc",
	)
	values = {}
	for row in frappe.get_all(
		"Item Attribute Value", fields=["parent", "attribute_value"], order_by="parent asc, idx asc"
	):
		values.setdefault(row.parent, []).append(row.attribute_value)
	for attr in attributes:
		attr["values"] = values.get(attr.name, [])
	return attributes


# Above this many combinations in one go the variants tab asks for a smaller selection.
_MAX_VARIANTS_PER_CREATE = 100


@frappe.whitelist()
def get_item_variants(template):
	"""Variants of a template item with their attribute values, for the variants tab."""
	variants = frappe.get_all(
		"Item",
		filters={"variant_of": template},
		fields=["item_code", "item_name", "disabled", "image"],
		order_by="item_code asc",
	)
	if not variants:
		return []
	attrs = {}
	for row in frappe.get_all(
		"Item Variant Attribute",
		filters={"parenttype": "Item", "parent": ["in", [v.item_code for v in variants]]},
		fields=["parent", "attribute", "attribute_value"],
		order_by="parent asc, idx asc",
	):
		attrs.setdefault(row.parent, {})[row.attribute] = row.attribute_value
	for v in variants:
		v["attributes"] = attrs.get(v.item_code, {})
	return variants


@frappe.whitelist()
def create_item_variants(template, args):
	"""Create a variant for every combination of the chosen attribute values ({attribute: [values]}).
	Combinations that already exist are skipped. Returns the number created."""
	from erpnext.controllers.item_variant import create_multiple_variants, generate_keyed_value_combinations

	frappe.has_permission("Item", ptype="create", throw=True)
	args = frappe.parse_json(args) or {}
	args = {key: values for key, values in args.items() if values}
	if not args:
		frappe.throw("Select at least one attribute value")
	if not frappe.db.get_value("Item", template, "has_variants"):
		frappe.throw(f"Item {template} is not a template (Has Variants is not set)")
	if len(generate_keyed_value_combinations(args)) > _MAX_VARIANTS_PER_CREATE:
		frappe.throw(f"Do not create more than {_MAX_VARIANTS_PER_CREATE} variants at a time")
	return {"created": create_multiple_variants(template, args)}


@frappe.whitelist()
def update_variant_attributes(variant, attributes, disabled=None):
	"""Change a variant's attribute values ({attribute: value}) and, when given, its disabled flag. ERPNext validates these only on
	insert, so the same checks run here. The item code stays; an item name still auto-generated
	from the old values is regenerated from the new ones when that name is free."""
	from erpnext.controllers.item_variant import (
		get_variant,
		make_variant_item_code,
		validate_item_variant_attributes,
	)

	attributes = frappe.parse_json(attributes) or {}
	doc = frappe.get_doc("Item", variant)
	doc.check_permission("write")
	if not doc.variant_of:
		frappe.throw(f"Item {variant} is not a variant")
	if any(not str(attributes.get(row.attribute) or "").strip() for row in doc.attributes):
		frappe.throw("Every attribute needs a value")

	template = frappe.get_cached_doc("Item", doc.variant_of)
	old_name = frappe._dict(item_code=None, item_name=None, attributes=doc.attributes)
	make_variant_item_code(template.item_code, template.item_name, old_name)

	args = {row.attribute: str(attributes[row.attribute]).strip() for row in doc.attributes}
	existing = get_variant(doc.variant_of, args, doc.name)
	if existing:
		frappe.throw(f"Item variant {existing} exists with same attributes")
	validate_item_variant_attributes(doc, args)

	for row in doc.attributes:
		row.attribute_value = args[row.attribute]
	if old_name.item_name and doc.item_name == old_name.item_name:
		new_name = frappe._dict(item_code=None, item_name=None, attributes=doc.attributes)
		make_variant_item_code(template.item_code, template.item_name, new_name)
		# Item names are unique; on a clash the old name stays rather than blocking the change
		if new_name.item_name and not _find_item_by_name(new_name.item_name, doc.name):
			doc.item_name = new_name.item_name
	if disabled is not None:
		doc.disabled = 1 if frappe.utils.cint(disabled) else 0
	doc.save()
	return {"item_code": doc.name, "item_name": doc.item_name, "disabled": doc.disabled}


@frappe.whitelist()
def search_linkable_items(template, txt=""):
	"""Normal items (neither template nor variant) matching code or name, to link as variants."""
	txt = f"%{(txt or '').strip()}%"
	return frappe.get_all(
		"Item",
		filters={"has_variants": 0, "variant_of": ["is", "not set"], "name": ["!=", template]},
		or_filters={"item_code": ["like", txt], "item_name": ["like", txt]},
		fields=["item_code", "item_name", "stock_uom", "disabled"],
		order_by="item_code asc",
		limit=20,
	)


# Copied from the template onto its variants on every template save (copy_attributes_to_variant),
# then frozen by cant_change once transactions exist, so a mismatch would block later template saves.
_VARIANT_MATCH_FIELDS = ("is_stock_item", "has_batch_no", "has_serial_no")


def _valuation_method(item):
	"""Item's valuation method, an empty one meaning the Stock Settings default (as cant_change reads it)."""
	return item.valuation_method or frappe.get_single_value("Stock Settings", "valuation_method") or "FIFO"


@frappe.whitelist()
def get_variant_update_setting():
	"""Item Variant Settings' "Do not update variants on save" (global) and whether this user may change it."""
	return {
		"do_not_update_variants": frappe.utils.cint(
			frappe.db.get_single_value("Item Variant Settings", "do_not_update_variants")
		),
		"can_edit": frappe.has_permission("Item Variant Settings", ptype="write"),
	}


@frappe.whitelist()
def set_variant_update_setting(do_not_update_variants):
	"""Turn copying template fields onto variants on every template save off (1) or on (0), for all templates."""
	settings = frappe.get_doc("Item Variant Settings")
	settings.check_permission("write")
	settings.do_not_update_variants = 1 if frappe.utils.cint(do_not_update_variants) else 0
	settings.save()
	return {"do_not_update_variants": settings.do_not_update_variants}


@frappe.whitelist()
def link_item_as_variant(template, item_code, attributes):
	"""Make an existing normal item a variant of the template with the given values ({attribute: value}).
	The item keeps its code, name, stock and history. Variant Of is set-only-once and ERPNext also refuses
	it once stock transactions exist, so variant_of and the attribute rows are written directly, after the
	same checks ERPNext runs on a new variant."""
	from erpnext.controllers.item_variant import get_variant, validate_item_variant_attributes

	attributes = frappe.parse_json(attributes) or {}
	doc = frappe.get_doc("Item", item_code)
	doc.check_permission("write")
	tmpl = frappe.get_doc("Item", template)
	if not tmpl.has_variants:
		frappe.throw(f"Item {template} is not a template (Has Variants is not set)")
	if (tmpl.variant_based_on or "Item Attribute") != "Item Attribute":
		frappe.throw(f"Template {template} is not based on Item Attribute")
	if doc.name == tmpl.name or doc.has_variants:
		frappe.throw(f"Item {item_code} is a template")
	if doc.variant_of:
		frappe.throw(f"Item {item_code} is already a variant of {doc.variant_of}")

	args = {row.attribute: str(attributes.get(row.attribute) or "").strip() for row in tmpl.attributes}
	if not args or not all(args.values()):
		frappe.throw("Every attribute needs a value")
	for field in _VARIANT_MATCH_FIELDS:
		if frappe.utils.cint(doc.get(field)) != frappe.utils.cint(tmpl.get(field)):
			label = doc.meta.get_label(field)
			frappe.throw(f"{label} differs between {item_code} and template {template}")
	if doc.is_stock_item and _valuation_method(doc) != _valuation_method(tmpl):
		frappe.throw(
			f"Valuation Method of {item_code} ({_valuation_method(doc)}) must match"
			f" template {template} ({_valuation_method(tmpl)})"
		)
	if doc.stock_uom != tmpl.stock_uom and not frappe.db.get_single_value(
		"Item Variant Settings", "allow_different_uom"
	):
		frappe.throw(
			f"Stock UOM of {item_code} ({doc.stock_uom}) must match template {template} ({tmpl.stock_uom})"
		)
	existing = get_variant(template, args, doc.name)
	if existing:
		frappe.throw(f"Item variant {existing} exists with same attributes")
	validate_item_variant_attributes(frappe._dict(name=doc.name, variant_of=template), args)

	frappe.db.delete("Item Variant Attribute", {"parenttype": "Item", "parent": doc.name})
	doc.set("attributes", [])
	for attribute, value in args.items():
		row = doc.append("attributes", {"attribute": attribute, "attribute_value": value, "variant_of": template})
		row.db_insert()
	doc.db_set({"variant_of": template, "variant_based_on": "Item Attribute"})
	doc.add_comment("Edit", f"Linked as a variant of {template}")
	return {"item_code": doc.name, "item_name": doc.item_name}


def publish_item_attribute_update(doc, method=None):
	"""Tell every tab to refetch the Item Attribute list (insert, edit, disable, delete)."""
	frappe.publish_realtime("item_attribute_update", {"name": doc.name}, after_commit=True)


def _has_variants_lock(item):
	"""Why Has Variants cannot be toggled on this saved item ("" when it can), per ERPNext's rules:
	hidden on variants, read-only once stock exists, and a template with variants cannot be unset."""
	if item.variant_of:
		return f"Variant of {item.variant_of}"
	if item.stock_ledger_created():
		return "Stock transactions exist for this item"
	if item.has_variants and frappe.db.exists("Item", {"variant_of": item.name}):
		return "Variants already created from this template"
	return ""


def _has_batch_lock(item):
	"""Why Has Batch No cannot be toggled on this item ("" when it can), per ERPNext's rules: shown
	only on stock items, copied to variants from the template (Item Variant Settings), and
	frozen by cant_change once submitted transactions exist."""
	if not item.is_stock_item:
		return "Not a stock item"
	if item.is_new():
		return ""
	if item.variant_of:
		return f"Copied from template {item.variant_of}"
	if item._get_linked_submitted_documents(["has_batch_no"]):
		return "Submitted transactions exist for this item"
	return ""


def _set_batch_fields(item, data):
	"""Apply the batch settings. Has Batch No is left as is when locked, the rest only while it is on."""
	if "has_batch_no" not in data:
		return
	if not _has_batch_lock(item):
		item.has_batch_no = 1 if frappe.utils.cint(data.get("has_batch_no")) else 0
	if not item.has_batch_no:
		item.create_new_batch = 0
		item.batch_number_series = None
		item.has_expiry_date = 0
		item.shelf_life_in_days = 0
		return
	if item.variant_of:
		return
	item.create_new_batch = 1 if frappe.utils.cint(data.get("create_new_batch")) else 0
	series = (data.get("batch_number_series") or "").strip()
	item.batch_number_series = series if item.create_new_batch and series else None
	item.has_expiry_date = 1 if frappe.utils.cint(data.get("has_expiry_date")) else 0
	shelf_life = frappe.utils.cint(data.get("shelf_life_in_days"))
	if item.has_expiry_date and shelf_life <= 0:
		frappe.throw("Shelf Life In Days is required when Has Expiry Date is set")
	item.shelf_life_in_days = shelf_life if item.has_expiry_date else 0


def _set_variant_attributes(item, data):
	"""Apply has_variants and the template's attribute rows. Rows for attributes that stay are
	kept as they are; numeric ranges are copied from the Item Attribute (no fetch_from on them)."""
	if "has_variants" not in data or item.variant_of:
		return
	item.has_variants = 1 if frappe.utils.cint(data.get("has_variants")) else 0
	if not item.has_variants:
		if item.is_new() or not frappe.db.exists("Item", {"variant_of": item.name}):
			item.set("attributes", [])
		return

	wanted = []
	for row in data.get("attributes") or []:
		attr = (row.get("attribute") or "").strip()
		if attr and attr not in wanted:
			wanted.append(attr)

	existing = {d.attribute: d for d in item.attributes}
	rows = []
	for attr in wanted:
		if attr in existing:
			rows.append(existing[attr])
			continue
		meta = frappe.db.get_value(
			"Item Attribute", attr, ["numeric_values", "from_range", "to_range", "increment"], as_dict=True
		)
		if not meta:
			frappe.throw(f"Item Attribute {attr} not found")
		rows.append({
			"attribute": attr,
			"numeric_values": meta.numeric_values,
			"from_range": meta.from_range,
			"to_range": meta.to_range,
			"increment": meta.increment,
		})
	item.set("attributes", rows)

def get_item_naming_series():
	"""Get naming series for Item."""
	try:
		meta = frappe.get_meta("Item")
		series_field = meta.get_field("naming_series")
		if series_field and series_field.options:
			return [s.strip() for s in series_field.options.split("\n") if s.strip()]
	except Exception:
		pass
	return []

@frappe.whitelist()
def get_next_barcode(naming_series):
	"""
	Peek at the next barcode without incrementing the database counter.
	Returns only the digit part of the peeked value.
	"""
	from frappe.model.naming import parse_naming_series
	import re
	
	res = parse_naming_series(naming_series)
	return re.sub(r"\D", "", res)

@frappe.whitelist()
def create_item(data):
	"""Create a new Item."""
	if isinstance(data, str):
		data = json.loads(data)

	# Before make_autoname so a rejected item does not consume a series number
	_check_duplicate_item_name(data.get("item_name"))
	
	is_manual = data.get("is_manual_barcode")
	naming_series = data.get("naming_series")
	barcode = data.get("barcode")
	
	if not is_manual and naming_series:
		# Server-side increment and fetch of the REAL next name
		from frappe.model.naming import make_autoname
		import re
		res = make_autoname(naming_series)
		# Strip non-digits and leading zeros for the auto-assigned code
		digits = re.sub(r"\D", "", res)
		barcode = digits.lstrip("0") or digits
	
	if not barcode:
		frappe.throw("Barcode/Item Code is required")
		
	item = frappe.new_doc("Item")
	item.item_code = barcode
	item.item_name = (data.get("item_name") or "").strip()
	item.item_print_name = data.get("item_print_name")
	item.item_group = data.get("item_group")
	item.stock_uom = data.get("stock_uom")
	item.standard_rate = float(data.get("standard_rate") or 0)
	item.safety_stock = float(data.get("safety_stock") or 0)
	if "custom_is_gst_item" in data:
		item.custom_is_gst_item = 1 if frappe.utils.cint(data.get("custom_is_gst_item")) else 0
	if "custom_competitive_item" in data:
		item.custom_competitive_item = data.get("custom_competitive_item") or None
	
	if data.get("hsn_sac"):
		item.gst_hsn_code = data.get("hsn_sac")

	if "image" in data:
		item.image = data.get("image")

	_set_variant_attributes(item, data)
	_set_batch_fields(item, data)
	
	# Add to barcodes child table
	item.append("barcodes", {"barcode": barcode, "uom": item.stock_uom})
	for row in (data.get("extra_barcodes") or []):
		extra = (row.get("barcode") or "").strip()
		uom = row.get("uom") or item.stock_uom
		if extra and extra != barcode:
			item.append("barcodes", {"barcode": extra, "uom": uom})

	# UOM conversions child table
	stock_uom = data.get("stock_uom", "Nos")
	item.append("uoms", {"uom": stock_uom, "conversion_factor": 1.0})
	for row in (data.get("uom_conversions") or []):
		uom_name = row.get("uom")
		factor = float(row.get("conversion_factor") or 1)
		if uom_name and uom_name != stock_uom:
			item.append("uoms", {"uom": uom_name, "conversion_factor": factor})

	# Tax template
	if data.get("item_tax_template"):
		wb_tax_template = data["item_tax_template"]
		taxes = [{"item_tax_template": wb_tax_template}]
		
		ae_company = frappe.db.get_single_value("Automatic Entries", "alternative_company")
		if ae_company:
			wb_company = frappe.db.get_value("Item Tax Template", wb_tax_template, "company")
			if wb_company and wb_company != ae_company:
				wb_abbr = frappe.db.get_value("Company", wb_company, "abbr")
				ae_abbr = frappe.db.get_value("Company", ae_company, "abbr")
				if wb_abbr and ae_abbr:
					suffix_wb = f" - {wb_abbr}"
					suffix_ae = f" - {ae_abbr}"
					if wb_tax_template.endswith(suffix_wb):
						ae_tax_template = wb_tax_template[:-len(suffix_wb)] + suffix_ae
						if frappe.db.exists("Item Tax Template", ae_tax_template):
							taxes.append({"item_tax_template": ae_tax_template})
		item.set("taxes", taxes)

	# Add supplier mapping (multiple support)
	if data.get("suppliers"):
		for row in data["suppliers"]:
			sup = row.get("supplier")
			if sup:
				item.append("supplier_items", {
					"supplier": sup,
					"supplier_part_no": row.get("supplier_part_no") or "",
				})
	elif data.get("supplier"):
		item.append("supplier_items", {
			"supplier": data["supplier"],
			"supplier_part_no": data.get("supplier_part_no") or "",
		})

	item.is_sales_item = 1
	item.is_purchase_item = 1
	item.update_stock = 1

	item.insert()
	return {
		"name": item.name,
		"item_code": item.item_code
	}

@frappe.whitelist()
def get_item_for_edit(item_code):
	"""Fetch all editable fields for an existing item."""
	if not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")

	item = frappe.get_doc("Item", item_code)

	# Standard selling rate from Item Price
	standard_rate = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "selling": 1},
		"price_list_rate",
	) or item.standard_rate or 0

	# Active item tax template
	item_tax_template = ""
	if item.taxes:
		item_tax_template = item.taxes[0].item_tax_template or ""

	# First barcode (the item's own barcode code)
	barcode = item_code  # fallback to item_code itself
	if item.barcodes:
		barcode = item.barcodes[0].barcode or item_code

	# Supplier mapping (all entries)
	suppliers = [
		{"supplier": row.supplier, "supplier_part_no": row.supplier_part_no or ""}
		for row in item.supplier_items
	]
	supplier = suppliers[0]["supplier"] if suppliers else ""
	supplier_part_no = suppliers[0]["supplier_part_no"] if suppliers else ""

	# Extra barcodes (all except the primary barcode)
	extra_barcodes = [
		{"barcode": row.barcode, "uom": row.uom}
		for row in item.barcodes[1:]
		if row.barcode != barcode
	]

	# UOM conversions (exclude the stock UOM base row)
	uom_conversions = [
		{"uom": row.uom, "conversion_factor": float(row.conversion_factor or 1)}
		for row in item.uoms
		if row.uom != item.stock_uom
	]

	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		"item_print_name": item.item_print_name or "",
		"barcode": barcode,
		"item_group": item.item_group or "",
		"custom_is_gst_item": frappe.utils.cint(item.get("custom_is_gst_item")),
		"custom_competitive_item": item.get("custom_competitive_item") or "",
		"hsn_sac": item.gst_hsn_code or "",
		"stock_uom": item.stock_uom or "Nos",
		"standard_rate": float(standard_rate),
		"safety_stock": float(item.safety_stock or 0),
		"item_tax_template": item_tax_template,
		"supplier": supplier,
		"supplier_part_no": supplier_part_no,
		"suppliers": suppliers,
		"uom_conversions": uom_conversions,
		"extra_barcodes": extra_barcodes,
		"image": item.image or "",
		"disabled": frappe.utils.cint(item.disabled),
		"has_variants": frappe.utils.cint(item.has_variants),
		"variant_of": item.variant_of or "",
		"has_variants_lock": _has_variants_lock(item),
		"attributes": [{"attribute": row.attribute} for row in item.attributes if not item.variant_of],
		"has_batch_no": frappe.utils.cint(item.has_batch_no),
		"create_new_batch": frappe.utils.cint(item.create_new_batch),
		"batch_number_series": item.batch_number_series or "",
		"has_expiry_date": frappe.utils.cint(item.has_expiry_date),
		"shelf_life_in_days": frappe.utils.cint(item.shelf_life_in_days),
		"has_batch_lock": _has_batch_lock(item),
	}


@frappe.whitelist()
def set_item_disabled(item_code, disabled):
	"""Enable or disable an item. The realtime item sync drops it from (or restores it to) every cache."""
	if not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")
	item = frappe.get_doc("Item", item_code)
	item.disabled = 1 if frappe.utils.cint(disabled) else 0
	item.flags.ignore_permissions = True
	item.save()
	return {"item_code": item.item_code, "disabled": item.disabled}


@frappe.whitelist()
def update_item(data):
	"""Update an existing item's editable fields."""
	if isinstance(data, str):
		data = json.loads(data)

	item_code = data.get("item_code")
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw("Item not found")

	item = frappe.get_doc("Item", item_code)
	new_name = (data.get("item_name") or "").strip()
	# Only on rename, so items that already share a name can still be edited
	if new_name and new_name.lower() != (item.item_name or "").strip().lower():
		_check_duplicate_item_name(new_name, exclude_item=item_code)
	item.item_name = new_name or item.item_name
	item.item_print_name = data.get("item_print_name") or ""
	item.item_group = data.get("item_group") or item.item_group
	item.stock_uom = data.get("stock_uom") or item.stock_uom
	item.safety_stock = float(data.get("safety_stock") or 0)
	if "custom_is_gst_item" in data:
		item.custom_is_gst_item = 1 if frappe.utils.cint(data.get("custom_is_gst_item")) else 0
	if "custom_competitive_item" in data:
		item.custom_competitive_item = data.get("custom_competitive_item") or None
	if data.get("hsn_sac"):
		item.gst_hsn_code = data["hsn_sac"]
	if "image" in data:
		item.image = data.get("image")
	_set_variant_attributes(item, data)
	_set_batch_fields(item, data)

	# Update barcodes (primary may be changed, extras replaced)
	current_primary = (item.barcodes[0].barcode if item.barcodes else "") or item.item_code
	primary_barcode = (data.get("barcode") or "").strip().lstrip("0") or current_primary
	if primary_barcode != current_primary:
		owner = _barcode_owner(primary_barcode, exclude_item=item_code)
		if owner:
			owner_name = frappe.db.get_value("Item", owner, "item_name") or owner
			frappe.throw(f"Barcode {primary_barcode} is already used by {owner} ({owner_name})")
	item.barcodes = []
	item.append("barcodes", {"barcode": primary_barcode, "uom": item.stock_uom})
	for row in (data.get("extra_barcodes") or []):
		extra = (row.get("barcode") or "").strip()
		uom = row.get("uom") or item.stock_uom
		if extra and extra != primary_barcode:
			item.append("barcodes", {"barcode": extra, "uom": uom})

	# Update UOM conversions
	stock_uom = data.get("stock_uom") or item.stock_uom
	item.uoms = []
	item.append("uoms", {"uom": stock_uom, "conversion_factor": 1.0})
	for row in (data.get("uom_conversions") or []):
		uom_name = row.get("uom")
		factor = float(row.get("conversion_factor") or 1)
		if uom_name and uom_name != stock_uom:
			item.append("uoms", {"uom": uom_name, "conversion_factor": factor})

	# Update tax template
	if data.get("item_tax_template"):
		wb_tax_template = data["item_tax_template"]
		taxes = [{"item_tax_template": wb_tax_template}]
		
		ae_company = frappe.db.get_single_value("Automatic Entries", "alternative_company")
		if ae_company:
			wb_company = frappe.db.get_value("Item Tax Template", wb_tax_template, "company")
			if wb_company and wb_company != ae_company:
				wb_abbr = frappe.db.get_value("Company", wb_company, "abbr")
				ae_abbr = frappe.db.get_value("Company", ae_company, "abbr")
				if wb_abbr and ae_abbr:
					suffix_wb = f" - {wb_abbr}"
					suffix_ae = f" - {ae_abbr}"
					if wb_tax_template.endswith(suffix_wb):
						ae_tax_template = wb_tax_template[:-len(suffix_wb)] + suffix_ae
						if frappe.db.exists("Item Tax Template", ae_tax_template):
							taxes.append({"item_tax_template": ae_tax_template})
		item.set("taxes", taxes)
	else:
		item.set("taxes", [])

	# Update supplier items (multiple support)
	item.supplier_items = []
	if data.get("suppliers"):
		for row in data["suppliers"]:
			sup = row.get("supplier")
			if sup:
				item.append("supplier_items", {
					"supplier": sup,
					"supplier_part_no": row.get("supplier_part_no") or "",
				})
	elif data.get("supplier"):
		item.append("supplier_items", {
			"supplier": data["supplier"],
			"supplier_part_no": data.get("supplier_part_no") or "",
		})

	if data.get("standard_rate") is not None:
		item.standard_rate = float(data["standard_rate"])

	item.flags.ignore_permissions = True
	item.save()

	return {"item_code": item.item_code, "item_name": item.item_name}


@frappe.whitelist()
def search_suppliers(query="", limit=20):
	"""Search suppliers by name for the item creation form."""
	results = frappe.get_all(
		"Supplier",
		filters=[["disabled", "=", 0], ["supplier_name", "like", f"%{query}%"]],
		fields=["name", "supplier_name"],
		order_by="supplier_name asc",
		limit_page_length=int(limit),
	)
	return [{"name": r.name, "label": r.supplier_name} for r in results]


@frappe.whitelist()
def print_barcodes(items, bill_no=None):
	if isinstance(items, str):
		items = json.loads(items)

	doc = frappe.new_doc("Barcode_Printing")
	if bill_no:
		doc.bill_no = bill_no

	for item in items:
		item_code = item.get("item_code")
		item_doc = frappe.get_cached_doc("Item", item_code) if item_code else None
		item_name = item.get("item_name") or (item_doc.item_name if item_doc else item_code)
		# Use item_code itself as the barcode value (barcode to print)
		barcode_val = item_code
		if item_doc and item_doc.barcodes:
			barcode_val = item_doc.barcodes[0].barcode or item_code
		doc.append("item", {
			"item_code": item_code,
			"item_name": item_name,
			"qty": item.get("qty", 1),
			"barcode": barcode_val,
		})
	doc.insert(ignore_permissions=True)
	return doc.name


# ── Mobile Item Barcode page ──────────────────────────────────────────────────


def _barcode_owner(barcode, exclude_item=None):
	"""Item that already carries `barcode` (as a barcode row or as its item code)."""
	filters = {"barcode": barcode, "parenttype": "Item"}
	if exclude_item:
		filters["parent"] = ["!=", exclude_item]
	owner = frappe.db.get_value("Item Barcode", filters, "parent")
	if not owner and barcode != exclude_item and frappe.db.exists("Item", barcode):
		owner = barcode
	return owner


def _item_uoms(item):
	"""Stock UOM first (factor 1), then the item's other conversions."""
	rows = [{"uom": item.stock_uom, "conversion_factor": 1.0}]
	rows += [
		{"uom": row.uom, "conversion_factor": float(row.conversion_factor or 1)}
		for row in item.uoms
		if row.uom != item.stock_uom
	]
	return rows


def _item_barcode_detail(item_code):
	item = frappe.get_doc("Item", item_code)
	return {
		"item_code": item.item_code,
		"item_name": item.item_name,
		"stock_uom": item.stock_uom,
		"image": item.image or "",
		"uoms": _item_uoms(item),
		"barcodes": [
			{"barcode": row.barcode, "uom": row.uom or item.stock_uom, "barcode_type": row.barcode_type or ""}
			for row in item.barcodes
		],
	}


@frappe.whitelist()
def search_items_for_barcode(query=""):
	"""Items where every word of `query` matches the item code, name or a barcode; exact hits first."""
	from ssplbilling.api.stock_check_api import _like

	tokens = [t for t in (query or "").split() if t][:6]
	if not tokens:
		return []

	conditions = []
	params = {"exact": query.strip()}
	for n, token in enumerate(tokens):
		key = f"t{n}"
		params[key] = _like(token)
		conditions.append(
			f"""(item.name LIKE %({key})s OR item.item_name LIKE %({key})s
				OR EXISTS (SELECT 1 FROM `tabItem Barcode` bc
					WHERE bc.parent = item.name AND bc.barcode LIKE %({key})s))"""
		)

	return frappe.db.sql(
		f"""SELECT item.name AS item_code, item.item_name, item.stock_uom,
				(SELECT COUNT(*) FROM `tabItem Barcode` bc WHERE bc.parent = item.name) AS barcode_count,
				(item.name = %(exact)s
					OR EXISTS (SELECT 1 FROM `tabItem Barcode` bc
						WHERE bc.parent = item.name AND bc.barcode = %(exact)s)) AS exact
			FROM `tabItem` item
			WHERE item.disabled = 0 AND {" AND ".join(conditions)}
			ORDER BY exact DESC, item.item_name ASC
			LIMIT 30""",
		params,
		as_dict=True,
	)


@frappe.whitelist()
def get_item_barcodes(item_code):
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")
	return _item_barcode_detail(item_code)


@frappe.whitelist()
def add_item_barcode(item_code, barcode, uom=None):
	"""Append one barcode row to an item; refuses a barcode already used by any item."""
	barcode = (barcode or "").strip()
	if not barcode:
		frappe.throw("Barcode is required")
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")

	item = frappe.get_doc("Item", item_code)
	if any(row.barcode == barcode for row in item.barcodes):
		frappe.throw(f"Barcode {barcode} is already on this item")
	owner = _barcode_owner(barcode, exclude_item=item_code)
	if owner:
		owner_name = frappe.db.get_value("Item", owner, "item_name") or owner
		frappe.throw(f"Barcode {barcode} is already used by {owner} ({owner_name})")

	valid_uoms = {row.uom for row in item.uoms} | {item.stock_uom}
	if uom and uom not in valid_uoms:
		frappe.throw(f"UOM {uom} is not set on this item. Add it with a conversion factor first.")
	item.append("barcodes", {"barcode": barcode, "uom": uom or item.stock_uom})
	item.flags.ignore_permissions = True
	item.save()
	return _item_barcode_detail(item_code)


@frappe.whitelist()
def remove_item_barcode(item_code, barcode):
	"""Delete one barcode row; the item's own code barcode stays."""
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")
	if barcode == item_code:
		frappe.throw("The item code barcode cannot be removed")

	item = frappe.get_doc("Item", item_code)
	keep = [row for row in item.barcodes if row.barcode != barcode]
	if len(keep) == len(item.barcodes):
		frappe.throw(f"Barcode {barcode} is not on this item")
	item.set("barcodes", keep)
	item.flags.ignore_permissions = True
	item.save()
	return _item_barcode_detail(item_code)


@frappe.whitelist()
def get_uom_list():
	return frappe.get_all("UOM", filters={"enabled": 1}, pluck="name", order_by="name asc")


@frappe.whitelist()
def set_item_uom(item_code, uom, conversion_factor):
	"""Add a UOM conversion to an item, or change the factor of an existing one."""
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")
	if not uom or not frappe.db.exists("UOM", uom):
		frappe.throw(f"UOM {uom} not found")
	factor = frappe.utils.flt(conversion_factor)
	if factor <= 0:
		frappe.throw("Conversion factor must be greater than 0")

	item = frappe.get_doc("Item", item_code)
	if uom == item.stock_uom:
		frappe.throw(f"{uom} is the stock UOM; its factor is always 1")
	row = next((r for r in item.uoms if r.uom == uom), None)
	if row:
		row.conversion_factor = factor
	else:
		item.append("uoms", {"uom": uom, "conversion_factor": factor})
	item.flags.ignore_permissions = True
	item.save()
	return _item_barcode_detail(item_code)


@frappe.whitelist()
def remove_item_uom(item_code, uom):
	"""Delete a UOM conversion; refused for the stock UOM or while a barcode still uses it."""
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")

	item = frappe.get_doc("Item", item_code)
	if uom == item.stock_uom:
		frappe.throw("The stock UOM cannot be removed")
	in_use = [r.barcode for r in item.barcodes if r.uom == uom]
	if in_use:
		frappe.throw(f"UOM {uom} is used by barcode {', '.join(in_use)}. Remove or change those first.")
	keep = [r for r in item.uoms if r.uom != uom]
	if len(keep) == len(item.uoms):
		frappe.throw(f"UOM {uom} is not on this item")
	item.set("uoms", keep)
	item.flags.ignore_permissions = True
	item.save()
	return _item_barcode_detail(item_code)


@frappe.whitelist()
def set_barcode_uom(item_code, barcode, uom):
	"""Point an existing barcode at another of the item's UOMs."""
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")

	item = frappe.get_doc("Item", item_code)
	if uom not in ({r.uom for r in item.uoms} | {item.stock_uom}):
		frappe.throw(f"UOM {uom} is not set on this item")
	row = next((r for r in item.barcodes if r.barcode == barcode), None)
	if not row:
		frappe.throw(f"Barcode {barcode} is not on this item")
	row.uom = uom
	item.flags.ignore_permissions = True
	item.save()
	return _item_barcode_detail(item_code)
