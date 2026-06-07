import frappe
import json

@frappe.whitelist()
def get_item_creation_metadata():
	"""Fetch all metadata needed for the item creation form."""
	return {
		"item_groups": frappe.get_all("Item Group", filters={"is_group": 0}, fields=["name"]),
		"uoms": frappe.get_all("UOM", fields=["name"]),
		"tax_templates": frappe.get_all("Item Tax Template", fields=["name"]),
		"hsn_codes": frappe.get_all("GST HSN Code", fields=["name", "description"]),
		"naming_series": get_item_naming_series()
	}

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
	item.item_name = data.get("item_name")
	item.item_print_name = data.get("item_print_name")
	item.item_group = data.get("item_group")
	item.stock_uom = data.get("stock_uom")
	item.standard_rate = float(data.get("standard_rate") or 0)
	item.safety_stock = float(data.get("safety_stock") or 0)
	
	if data.get("hsn_sac"):
		item.gst_hsn_code = data.get("hsn_sac")
	
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
		item.set("taxes", [{"item_tax_template": data["item_tax_template"]}])

	# Add supplier mapping
	if data.get("supplier"):
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

	# Supplier mapping (first entry)
	supplier = ""
	supplier_part_no = ""
	if item.supplier_items:
		supplier = item.supplier_items[0].supplier or ""
		supplier_part_no = item.supplier_items[0].supplier_part_no or ""

	# Extra barcodes (all except the primary/item_code barcode)
	extra_barcodes = [
		{"barcode": row.barcode, "uom": row.uom}
		for row in item.barcodes
		if row.barcode != item.item_code
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
		"hsn_sac": item.gst_hsn_code or "",
		"stock_uom": item.stock_uom or "Nos",
		"standard_rate": float(standard_rate),
		"safety_stock": float(item.safety_stock or 0),
		"item_tax_template": item_tax_template,
		"supplier": supplier,
		"supplier_part_no": supplier_part_no,
		"uom_conversions": uom_conversions,
		"extra_barcodes": extra_barcodes,
	}


@frappe.whitelist()
def update_item(data):
	"""Update an existing item's editable fields."""
	if isinstance(data, str):
		data = json.loads(data)

	item_code = data.get("item_code")
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw("Item not found")

	item = frappe.get_doc("Item", item_code)
	item.item_name = data.get("item_name") or item.item_name
	item.item_print_name = data.get("item_print_name") or ""
	item.item_group = data.get("item_group") or item.item_group
	item.stock_uom = data.get("stock_uom") or item.stock_uom
	item.safety_stock = float(data.get("safety_stock") or 0)
	if data.get("hsn_sac"):
		item.gst_hsn_code = data["hsn_sac"]

	# Update barcodes (keep primary, replace extras)
	primary_barcode = item.item_code
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
		item.set("taxes", [{"item_tax_template": data["item_tax_template"]}])
	else:
		item.set("taxes", [])

	# Update supplier items (replace first entry)
	item.supplier_items = []
	if data.get("supplier"):
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
