# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist(allow_guest=True)
def get_offer_details(pageaddress):
	if not pageaddress:
		return None

	offer_names = frappe.get_all(
		"Offer-Items",
		filters={"pageaddress": pageaddress},
		ignore_permissions=True,
		limit=1
	)
	if not offer_names:
		return None

	doc = frappe.get_doc("Offer-Items", offer_names[0].name)
	
	items = []
	for item in doc.items:
		item_image = frappe.db.get_value("Item", item.itemcode, "image")
		items.append({
			"itemcode": item.itemcode,
			"itemname": item.itemname,
			"barcode": item.barcode,
			"image": item_image
		})
		
	return {
		"name": doc.name,
		"heading": doc.heading,
		"pageaddress": doc.pageaddress,
		"items": items
	}
