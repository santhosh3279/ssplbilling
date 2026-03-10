import frappe
import json

@frappe.whitelist()
def get_item_creation_metadata():
	"""Fetch all metadata needed for the item creation form."""
	return {
		"item_groups": frappe.get_all("Item Group", filters={"is_group": 0}, fields=["name"]),
		"uoms": frappe.get_all("UOM", fields=["name"]),
		"tax_templates": frappe.get_all("Item Tax Template", fields=["name"]),
		"hsn_codes": frappe.get_all("GST HSN Code", fields=["name"]),
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
	"""Get next barcode from naming series."""
	from frappe.model.naming import make_autoname
	return make_autoname(naming_series)

@frappe.whitelist()
def create_item(data):
	"""Create a new Item."""
	if isinstance(data, str):
		data = json.loads(data)
	
	item = frappe.new_doc("Item")
	item.item_code = data.get("barcode") # Using barcode as item_code if provided
	item.item_name = data.get("item_name")
	item.item_group = data.get("item_group")
	item.stock_uom = data.get("stock_uom")
	item.standard_rate = float(data.get("standard_rate") or 0)
	item.safety_stock = float(data.get("safety_stock") or 0)
	
	if data.get("hsn_sac"):
		item.gst_hsn_code = data.get("hsn_sac")
	
	if data.get("item_tax_template"):
		item.append("taxes", {
			"item_tax_template": data.get("item_tax_template"),
			"tax_category": ""
		})
	
	if data.get("barcode"):
		item.append("barcodes", {
			"barcode": data.get("barcode")
		})
	
	item.is_sales_item = 1
	item.is_purchase_item = 1
	item.update_stock = 1
	
	item.insert()
	return item.name
