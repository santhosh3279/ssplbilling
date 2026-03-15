import frappe
import json



@frappe.whitelist()
def create_barcode_print_entry(items, bill_no=None):
	"""
	Create a Barcode_Prinitng document mapping item_code → item, qty → qty.

	Returns:
		name of the created Barcode_Prinitng document
	"""
	if isinstance(items, str):
		items = json.loads(items)

	if not items:
		frappe.throw("No items provided for barcode printing")

	doc = frappe.new_doc("Barcode_Prinitng")

	if bill_no:
		doc.bill_no = bill_no

	for item in items:
		item_code = item.get("item_code")
		if not item_code:
			continue
		doc.append("item", {
			"item": item_code,
			"qty": str(item.get("qty", 1)),
		})

	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return doc.name
