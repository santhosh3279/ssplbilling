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
		# Strip non-digits for the auto-assigned code
		barcode = re.sub(r"\D", "", res)
	
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
	item.append("barcodes", {
		"barcode": barcode
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
def print_barcodes(items, bill_no=None):
	if isinstance(items, str):
		items = json.loads(items)

	doc = frappe.new_doc("Barcode_Prinitng")
	if bill_no:
		doc.bill_no = bill_no

	for item in items:
		item_code = item.get("item_code")
		item_doc = frappe.get_cached_doc("Item", item_code) if item_code else None
		item_name = item.get("item_name") or (item_doc.item_name if item_doc else item_code)
		rate = item.get("rate") or (item_doc.standard_rate if item_doc else 0)
		# Use item_code itself as the barcode value (barcode to print)
		barcode_val = item_code
		if item_doc and item_doc.barcodes:
			barcode_val = item_doc.barcodes[0].barcode or item_code
		doc.append("item", {
			"item_code": item_code,
			"item_name": item_name,
			"qty": item.get("qty", 1),
			"rate": rate,
			"barcode": barcode_val,
		})
	doc.insert(ignore_permissions=True)
	return doc.name
