import frappe
import json


def _get_item_price(item_code, price_list):
	"""Return the price_list_rate for an item from Item Price."""
	row = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "selling": 1},
		"price_list_rate",
		order_by="valid_from desc",
	)
	if row:
		return float(row)
	# Fallback: try without selling filter (buying price lists)
	row = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list},
		"price_list_rate",
		order_by="valid_from desc",
	)
	return float(row) if row else 0.0


@frappe.whitelist()
def create_barcode_print_entry(items, bill_no=None, price_list=None):
	"""
	Create a Barcode_Prinitng document (Printer Server Configuration module).
	If rate is missing or 0, it is fetched from Item Price using price_list.

	Returns:
		name of the created Barcode_Prinitng document
	"""
	if isinstance(items, str):
		items = json.loads(items)

	if not items:
		frappe.throw("No items provided for barcode printing")

	effective_price_list = price_list or "Standard Selling"

	doc = frappe.new_doc("Barcode_Prinitng")

	if bill_no:
		doc.bill_no = bill_no

	for item in items:
		item_code = item.get("item_code")
		if not item_code:
			continue

		rate = float(item.get("rate") or 0)
		if not rate:
			rate = _get_item_price(item_code, effective_price_list)

		doc.append("items", {
			"item_code": item_code,
			"item_name": item.get("item_name") or "",
			"qty": int(item.get("qty") or 1),
			"rate": rate,
		})

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return doc.name
