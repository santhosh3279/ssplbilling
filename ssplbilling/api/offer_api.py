# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate
import datetime

def resolve_rate(uom_rates, uom, stock_uom):
	if not uom_rates:
		return None
	# 1. Try barcode UOM
	if uom and uom in uom_rates:
		return uom_rates[uom]
	# 2. Try stock UOM
	if stock_uom and stock_uom in uom_rates:
		return uom_rates[stock_uom]
	# 3. Try default UOM (empty string)
	if "" in uom_rates:
		return uom_rates[""]
	# 4. Try any UOM if only one exists
	if len(uom_rates) == 1:
		return list(uom_rates.values())[0]
	return None

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
	
	# Fetch all enabled discount rules
	today = datetime.date.today()
	active_rules = frappe.get_all(
		"Discount Rule",
		filters={"enabled": 1},
		fields=[
			"name", "rule_name", "discount_type", "applies_to", 
			"product_group", "start_date", "end_date", "percentage_discount",
			"min_quantity", "free_quantity", "recursive", "custom_logic_type"
		],
		ignore_permissions=True
	)
	
	# Separate into currently active vs fallback (expired or future) enabled rules
	valid_rules = []
	fallback_rules = []
	for rule in active_rules:
		is_active = True
		if rule.start_date and getdate(rule.start_date) > today:
			is_active = False
		if rule.end_date and getdate(rule.end_date) < today:
			is_active = False
			
		if is_active:
			valid_rules.append(rule)
		else:
			fallback_rules.append(rule)
			
	candidate_rules = valid_rules + fallback_rules
		
	# Pre-fetch child items linked to enabled rules
	rule_names = [r.name for r in candidate_rules]
	item_rules = {}
	custom_logic_rows = {}
	if rule_names:
		# 1. Fetch child items for item scope rules
		child_items = frappe.get_all(
			"Discount Rule Item",
			filters={"parent": ["in", rule_names]},
			fields=["parent", "item_code"],
			ignore_permissions=True
		)
		for ci in child_items:
			item_rules.setdefault(ci.item_code, []).append(ci.parent)

		# 2. Fetch custom logic table rows for tiered rules
		logic_rows = frappe.get_all(
			"Discount Rule Custom Logic",
			filters={"parent": ["in", rule_names]},
			fields=["parent", "min_quantity", "nos", "percentage"],
			ignore_permissions=True,
			order_by="min_quantity asc"
		)
		for lr in logic_rows:
			custom_logic_rows.setdefault(lr.parent, []).append(lr)

	# Pre-fetch item group map for offer items
	item_codes = [item.itemcode for item in doc.items]
	item_group_map = {}
	item_image_map = {}
	item_stock_uom_map = {}
	if item_codes:
		item_details = frappe.get_all(
			"Item",
			filters={"item_code": ["in", item_codes]},
			fields=["item_code", "item_group", "image", "stock_uom"],
			ignore_permissions=True
		)
		item_group_map = {i.item_code: i.item_group for i in item_details}
		item_image_map = {i.item_code: i.image for i in item_details}
		item_stock_uom_map = {i.item_code: i.stock_uom for i in item_details}

	# Map barcodes to UOMs
	barcode_uom_map = {}
	barcodes = [item.barcode for item in doc.items if item.barcode]
	if barcodes:
		barcode_data = frappe.get_all(
			"Item Barcode",
			filters={"barcode": ["in", barcodes]},
			fields=["barcode", "uom"],
			ignore_permissions=True
		)
		barcode_uom_map = {b.barcode: b.uom for b in barcode_data}

	# Pre-fetch all barcodes for all items in this offer list
	all_item_barcodes = {}
	if item_codes:
		all_barcodes_data = frappe.get_all(
			"Item Barcode",
			filters={"parent": ["in", item_codes]},
			fields=["parent as item_code", "barcode", "uom"],
			ignore_permissions=True
		)
		for row in all_barcodes_data:
			if row.barcode:
				all_item_barcodes.setdefault(row.item_code, []).append({
					"barcode": row.barcode,
					"uom": row.uom
				})

	# Pre-fetch price list rates for these items and UOMs
	price_lists = [pl.price_list for pl in doc.get("price_lists") if pl.price_list]
	price_map = {}
	if price_lists and item_codes:
		prices_data = frappe.get_all(
			"Item Price",
			filters={
				"item_code": ["in", item_codes],
				"price_list": ["in", price_lists]
			},
			fields=["item_code", "price_list", "price_list_rate", "uom"],
			ignore_permissions=True
		)
		for p in prices_data:
			uom_pl = price_map.setdefault(p.item_code, {}).setdefault(p.price_list, {})
			uom_pl[p.uom or ""] = p.price_list_rate

	items = []
	for item in doc.items:
		item_code = item.itemcode
		item_group = item_group_map.get(item_code)
		stock_uom = item_stock_uom_map.get(item_code)
		barcode_uom = barcode_uom_map.get(item.barcode) if item.barcode else None

		# Compile rates list barcode-wise with fallbacks
		item_rates = []
		for plist in price_lists:
			rate = None
			uom_rates = price_map.get(item_code, {}).get(plist)
			if uom_rates:
				if barcode_uom and barcode_uom in uom_rates:
					rate = uom_rates[barcode_uom]
				elif stock_uom and stock_uom in uom_rates:
					rate = uom_rates[stock_uom]
				elif "" in uom_rates:
					rate = uom_rates[""]
				elif uom_rates:
					rate = list(uom_rates.values())[0]
			if rate is not None:
				item_rates.append({
					"price_list": plist,
					"rate": rate
				})
		# Sort rates in ascending order of rate
		item_rates.sort(key=lambda x: x["rate"])
		
		# Resolve item image safely
		item_image = item_image_map.get(item_code)
		if not item_image:
			item_image = frappe.db.get_value("Item", item_code, "image")
			
		# Ensure it's a valid image path/URL, not a placeholder string
		if item_image and not (item_image.startswith("/") or item_image.startswith("http")):
			item_image = None

		# Match discount rules
		matched_rule = None
		for rule in candidate_rules:
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
			rows = custom_logic_rows.get(matched_rule.name, [])
			
			if discount_type == "Percentage Discount":
				if rows:
					desc_parts = []
					for r in rows:
						min_q = int(r.min_quantity) if r.min_quantity.is_integer() else r.min_quantity
						pct_val = int(r.percentage) if r.percentage.is_integer() else r.percentage
						desc_parts.append(f"Qty {min_q}+: {pct_val}% Off")
					discount_desc = " | ".join(desc_parts)
				else:
					pct = matched_rule.percentage_discount
					pct_str = f"{int(pct)}%" if pct.is_integer() else f"{pct}%"
					min_q = matched_rule.min_quantity
					if min_q and min_q > 0:
						min_str = str(int(min_q)) if min_q.is_integer() else str(min_q)
						discount_desc = f"{pct_str} Off (Min Qty: {min_str})"
					else:
						discount_desc = f"{pct_str} Off"
						
			elif discount_type == "Product Discount":
				min_q = matched_rule.min_quantity
				free_q = matched_rule.free_quantity
				min_str = str(int(min_q)) if min_q.is_integer() else str(min_q)
				free_str = str(int(free_q)) if free_q.is_integer() else str(free_q)
				discount_desc = f"Buy {min_str} Get {free_str} Free"
				
			elif discount_type == "Custom Logic":
				logic_type = matched_rule.custom_logic_type
				if rows:
					desc_parts = []
					for r in rows:
						min_q = int(r.min_quantity) if r.min_quantity.is_integer() else r.min_quantity
						if logic_type == "Product":
							nos_val = int(r.nos) if r.nos.is_integer() else r.nos
							desc_parts.append(f"Buy {min_q} Get {nos_val} Free")
						else:
							pct_val = int(r.percentage) if r.percentage.is_integer() else r.percentage
							desc_parts.append(f"Qty {min_q}+: {pct_val}% Off")
					discount_desc = " | ".join(desc_parts)
				else:
					discount_desc = "Offer"

		# Compile all unique barcodes and their rates for each price list
		barcodes_with_prices = []
		seen_barcodes = set()
		for b_info in all_item_barcodes.get(item_code, []):
			bc = b_info["barcode"]
			b_uom = b_info["uom"]
			if bc and bc not in seen_barcodes:
				seen_barcodes.add(bc)
				rates = {}
				for plist in price_lists:
					uom_rates = price_map.get(item_code, {}).get(plist)
					rates[plist] = resolve_rate(uom_rates, b_uom, stock_uom)
				barcodes_with_prices.append({
					"barcode": bc,
					"uom": b_uom,
					"prices": rates
				})
		if item.barcode and item.barcode not in seen_barcodes:
			seen_barcodes.add(item.barcode)
			b_uom = barcode_uom_map.get(item.barcode) or stock_uom
			rates = {}
			for plist in price_lists:
				uom_rates = price_map.get(item_code, {}).get(plist)
				rates[plist] = resolve_rate(uom_rates, b_uom, stock_uom)
			barcodes_with_prices.append({
				"barcode": item.barcode,
				"uom": b_uom,
				"prices": rates
			})
		if not barcodes_with_prices:
			rates = {}
			for plist in price_lists:
				uom_rates = price_map.get(item_code, {}).get(plist)
				rates[plist] = resolve_rate(uom_rates, stock_uom, stock_uom)
			barcodes_with_prices.append({
				"barcode": "",
				"uom": stock_uom,
				"prices": rates
			})

		items.append({
			"itemcode": item_code,
			"itemname": item.itemname,
			"barcode": item.barcode,
			"barcodes": [b["barcode"] for b in barcodes_with_prices if b["barcode"]],
			"barcode_prices": barcodes_with_prices,
			"image": item_image,
			"discount_type": discount_type,
			"discount_desc": discount_desc,
			"prices": item_rates
		})
		
	return {
		"name": doc.name,
		"heading": doc.heading,
		"pageaddress": doc.pageaddress,
		"tile_grid": doc.tile_grid or "4",
		"timer": doc.timer or 0,
		"price_lists": [{"price_list": pl.price_list} for pl in doc.get("price_lists") if pl.price_list],
		"items": items
	}
