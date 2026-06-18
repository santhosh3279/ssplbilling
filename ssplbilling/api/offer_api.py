# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate
import datetime

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
	
	# Fetch all active discount rules
	today = datetime.date.today()
	active_rules = frappe.get_all(
		"Discount Rule",
		filters={"enabled": 1},
		fields=[
			"name", "rule_name", "discount_type", "applies_to", 
			"product_group", "start_date", "end_date", "percentage_discount",
			"min_quantity", "free_quantity"
		],
		ignore_permissions=True
	)
	
	# Filter rules valid today
	valid_rules = []
	for rule in active_rules:
		if rule.start_date and getdate(rule.start_date) > today:
			continue
		if rule.end_date and getdate(rule.end_date) < today:
			continue
		valid_rules.append(rule)
		
	# Pre-fetch child items linked to valid rules
	rule_names = [r.name for r in valid_rules]
	item_rules = {}
	if rule_names:
		child_items = frappe.get_all(
			"Discount Rule Item",
			filters={"parent": ["in", rule_names]},
			fields=["parent", "item_code"],
			ignore_permissions=True
		)
		for ci in child_items:
			item_rules.setdefault(ci.item_code, []).append(ci.parent)

	# Pre-fetch item group map for offer items
	item_codes = [item.itemcode for item in doc.items]
	item_group_map = {}
	if item_codes:
		item_details = frappe.get_all(
			"Item",
			filters={"item_code": ["in", item_codes]},
			fields=["item_code", "item_group", "image"],
			ignore_permissions=True
		)
		item_group_map = {i.item_code: i.item_group for i in item_details}
		item_image_map = {i.item_code: i.image for i in item_details}
	else:
		item_image_map = {}

	items = []
	for item in doc.items:
		item_code = item.itemcode
		item_group = item_group_map.get(item_code)
		item_image = item_image_map.get(item_code) or item.barcode # Fallback check if it was set in child table
		if not item_image:
			# Fetch direct from Item DB if not loaded
			item_image = frappe.db.get_value("Item", item_code, "image")
			
		# Match discount rules
		matched_rule = None
		for rule in valid_rules:
			# Direct item code match
			if rule.applies_to == "Item Code" and rule.name in item_rules.get(item_code, []):
				matched_rule = rule
				break
			# Product Group match
			elif rule.applies_to == "Product Group" and item_group == rule.product_group:
				matched_rule = rule
				break

		discount_type = None
		discount_desc = None
		if matched_rule:
			discount_type = matched_rule.discount_type
			if discount_type == "Percentage Discount":
				pct = matched_rule.percentage_discount
				discount_desc = f"{int(pct)}% Off" if pct.is_integer() else f"{pct}% Off"
			elif discount_type == "Product Discount":
				min_q = matched_rule.min_quantity
				free_q = matched_rule.free_quantity
				min_str = str(int(min_q)) if min_q.is_integer() else str(min_q)
				free_str = str(int(free_q)) if free_q.is_integer() else str(free_q)
				discount_desc = f"Buy {min_str} Get {free_str} Free"
			elif discount_type == "Custom Logic":
				discount_desc = "Special Offer"

		items.append({
			"itemcode": item_code,
			"itemname": item.itemname,
			"barcode": item.barcode,
			"image": item_image,
			"discount_type": discount_type,
			"discount_desc": discount_desc
		})
		
	return {
		"name": doc.name,
		"heading": doc.heading,
		"pageaddress": doc.pageaddress,
		"items": items
	}
