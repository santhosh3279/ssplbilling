# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, get_url, getdate
from urllib.parse import quote
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

def _catalogue_stock(item_codes):
	"""Available stock in the configured online-order warehouse, in stock UOM."""
	from ssplbilling.api.stock_utils import get_draft_invoice_qtys_batch, get_draft_purchase_qtys_batch

	settings = frappe.get_single("SSPL Billing Settings")
	warehouse = settings.get("online_order_warehouse")
	company = settings.get("online_order_company")
	if not item_codes or not warehouse or not company:
		return {}
	warehouse_doc = frappe.get_cached_doc("Warehouse", warehouse)
	if warehouse_doc.company != company or warehouse_doc.is_group or warehouse_doc.disabled:
		return {}
	bins = frappe.get_all("Bin", filters={"item_code": ["in", item_codes], "warehouse": warehouse},
		fields=["item_code", "actual_qty"])
	actual = {row.item_code: float(row.actual_qty or 0) for row in bins}
	sales = get_draft_invoice_qtys_batch(warehouse)
	purchases = get_draft_purchase_qtys_batch(warehouse)
	return {code: actual.get(code, 0.0) - sales.get((code, warehouse), 0.0)
		+ purchases.get((code, warehouse), 0.0) for code in item_codes}


def _catalogue_variants(item_codes):
	"""Enabled sales variants of any template among item_codes, read live so new variants show up."""
	if not item_codes:
		return []
	variants = frappe.get_all(
		"Item",
		filters={"variant_of": ["in", list(item_codes)], "disabled": 0, "is_sales_item": 1},
		fields=["name", "item_name", "variant_of"],
		order_by="name asc",
		ignore_permissions=True,
	)
	labels = {}
	if variants:
		for row in frappe.get_all(
			"Item Variant Attribute",
			filters={"parent": ["in", [v.name for v in variants]], "parenttype": "Item"},
			fields=["parent", "attribute_value"],
			order_by="idx asc",
			ignore_permissions=True,
		):
			if row.attribute_value:
				labels.setdefault(row.parent, []).append(row.attribute_value)
	for variant in variants:
		variant.variant_label = " / ".join(labels.get(variant.name, [])) or variant.item_name
	return variants


@frappe.whitelist(allow_guest=True)
def get_offer_stock(pageaddress):
	"""Refresh only stock for the public catalogue's enabled items and their variants."""
	name = frappe.db.get_value("Offer-Items", {"pageaddress": pageaddress}, "name") if pageaddress else None
	if not name:
		return {}
	doc = frappe.get_doc("Offer-Items", name)
	codes = [row.itemcode for row in doc.items if not row.get("disabled")]
	return _catalogue_stock(codes + [v.name for v in _catalogue_variants(codes)])


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
	active_items = [item for item in doc.items if not item.get("disabled")]
	
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

	# Template rows expand to their current variants; a variant already listed as its own row is not repeated.
	direct_codes = {item.itemcode for item in active_items}
	variants = [v for v in _catalogue_variants(direct_codes) if v.name not in direct_codes]
	variant_rows = [
		frappe._dict(itemcode=v.name, itemname=v.item_name, barcode=None, variant_of=v.variant_of,
			variant_label=v.variant_label)
		for v in variants
	]

	# Pre-fetch item group map for offer items
	item_codes = [item.itemcode for item in active_items + variant_rows]
	live_stock = _catalogue_stock(item_codes)
	item_group_map = {}
	item_display_name_map = {}
	item_image_map = {}
	item_stock_uom_map = {}
	item_gst_map = {}
	template_codes = set()
	if item_codes:
		item_details = frappe.get_all(
			"Item",
			filters={"item_code": ["in", item_codes]},
			fields=["item_code", "item_group", "image", "stock_uom", "item_name", "item_print_name", "custom_is_gst_item", "has_variants"],
			ignore_permissions=True
		)
		template_codes = {i.item_code for i in item_details if i.has_variants}
		item_group_map = {i.item_code: i.item_group for i in item_details}
		item_display_name_map = {i.item_code: i.item_print_name or i.item_name for i in item_details}
		item_image_map = {i.item_code: i.image for i in item_details}
		item_stock_uom_map = {i.item_code: i.stock_uom for i in item_details}
		item_gst_map = {i.item_code: frappe.utils.cint(i.custom_is_gst_item) for i in item_details}

	# Map barcodes to UOMs
	barcode_uom_map = {}
	barcodes = [item.barcode for item in active_items if item.barcode]
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
			order_by="idx asc",
			ignore_permissions=True
		)
		for row in all_barcodes_data:
			if row.barcode:
				all_item_barcodes.setdefault(row.item_code, []).append({
					"barcode": row.barcode,
					"uom": row.uom
				})

	# UOM conversion factors per item, so barcodes can be grouped one per factor
	uom_factor_map = {}
	if item_codes:
		for row in frappe.get_all(
			"UOM Conversion Detail",
			filters={"parent": ["in", item_codes], "parenttype": "Item"},
			fields=["parent", "uom", "conversion_factor"],
			ignore_permissions=True
		):
			uom_factor_map.setdefault(row.parent, {})[row.uom] = row.conversion_factor

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
	variant_entries = {}
	for item in active_items + variant_rows:
		item_code = item.itemcode
		item_group = item_group_map.get(item_code)
		stock_uom = item_stock_uom_map.get(item_code)
		barcode_uom = barcode_uom_map.get(item.barcode) if item.barcode else None
		# Like ERPNext, a variant without its own Item Price uses its template's.
		item_prices = price_map.get(item_code) or price_map.get(item.get("variant_of")) or {}

		# Compile rates list barcode-wise with fallbacks
		item_rates = []
		for plist in price_lists:
			rate = None
			uom_rates = item_prices.get(plist)
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

		# One barcode per conversion factor. For factor 1 only the default barcode is shown:
		# the barcode picked on the catalogue row, else the first stock-UOM barcode.
		candidates = []
		if item.barcode:
			candidates.append({"barcode": item.barcode, "uom": barcode_uom_map.get(item.barcode) or stock_uom})
		candidates += all_item_barcodes.get(item_code, [])
		factors = uom_factor_map.get(item_code, {})
		barcode_by_factor = {}
		for b_info in candidates:
			b_uom = b_info["uom"] or stock_uom
			factor = 1.0 if b_uom == stock_uom else float(factors.get(b_uom) or 1)
			if b_info["barcode"] and factor not in barcode_by_factor:
				barcode_by_factor[factor] = {"barcode": b_info["barcode"], "uom": b_uom}
		barcodes_with_prices = []
		for factor in sorted(barcode_by_factor):
			b_info = barcode_by_factor[factor]
			rates = {}
			for plist in price_lists:
				uom_rates = item_prices.get(plist)
				rates[plist] = resolve_rate(uom_rates, b_info["uom"], stock_uom)
			barcodes_with_prices.append({
				"barcode": b_info["barcode"],
				"uom": b_info["uom"],
				"prices": rates
			})
		if not barcodes_with_prices:
			rates = {}
			for plist in price_lists:
				uom_rates = item_prices.get(plist)
				rates[plist] = resolve_rate(uom_rates, stock_uom, stock_uom)
			barcodes_with_prices.append({
				"barcode": "",
				"uom": stock_uom,
				"prices": rates
			})

		entry = {
			"itemcode": item_code,
			"available_stock": live_stock.get(item_code),
			"stock_uom": stock_uom,
			"itemname": item_display_name_map.get(item_code) or item.itemname,
			"barcode": item.barcode,
			"barcodes": [b["barcode"] for b in barcodes_with_prices if b["barcode"]],
			"barcode_prices": barcodes_with_prices,
			"image": item_image,
			"discount_type": discount_type,
			"discount_desc": discount_desc,
			"is_gst_item": item_gst_map.get(item_code, 0),
			"prices": item_rates
		}
		if item.get("variant_of"):
			entry["variant_label"] = item.variant_label
			variant_entries.setdefault(item.variant_of, []).append(entry)
		else:
			items.append(entry)

	for entry in items:
		if entry["itemcode"] in template_codes:
			entry["is_template"] = 1
			entry["variants"] = variant_entries.get(entry["itemcode"], [])
			for variant in entry["variants"]:
				variant["image"] = variant["image"] or entry["image"]

	settings = frappe.get_single("SSPL Billing Settings")
	cipher_map = settings.cipher_map or ""

	return {
		"name": doc.name,
		"heading": doc.heading,
		"pageaddress": doc.pageaddress,
		"tile_grid": doc.tile_grid or "4",
		"timer": doc.timer or 0,
		"price_lists": [{"price_list": pl.price_list} for pl in doc.get("price_lists") if pl.price_list],
		"items": items,
		"sub_catalogues": _sub_catalogues(doc),
		"cipher_map": cipher_map
	}


def _active_item_counts(names):
	if not names:
		return {}
	counts = frappe.get_all(
		"Offer-Item",
		filters={
			"parent": ["in", list(names)],
			"parenttype": "Offer-Items",
			"parentfield": "items",
			"disabled": 0,
		},
		fields=["parent", {"COUNT": "name", "as": "item_count"}],
		group_by="parent",
		ignore_permissions=True,
	)
	return {row.parent: row.item_count for row in counts}


def _sub_catalogues(doc):
	"""Linked child catalogues, in table order, rendered as folders on the public page."""
	names = [row.offer for row in doc.get("sub_catalogues") or [] if row.offer]
	if not names:
		return []
	details = {
		row.name: row
		for row in frappe.get_all(
			"Offer-Items",
			filters={"name": ["in", names]},
			fields=["name", "heading", "pageaddress"],
			ignore_permissions=True,
		)
	}
	counts = _active_item_counts(names)
	return [
		{
			"name": name,
			"heading": details[name].heading,
			"pageaddress": details[name].pageaddress,
			"item_count": counts.get(name, 0),
		}
		for name in names
		if name in details
	]

@frappe.whitelist(allow_guest=True)
def get_offer_list():
	# A site may serve requests before its DocType schema migration completes.
	has_priority = frappe.db.has_column("Offer-Items", "priority")
	# Hidden catalogues are reachable only as sub folders of a catalogue that links them.
	has_visibility = frappe.db.has_column("Offer-Items", "show_in_catalogue")
	catalogues = frappe.get_all(
		"Offer-Items",
		filters={"show_in_catalogue": 1} if has_visibility else None,
		fields=["name", "heading", "pageaddress", "timer", "creation"] + (["priority"] if has_priority else []),
		order_by="priority asc, creation desc" if has_priority else "creation desc"
	)
	if not catalogues:
		return catalogues

	names = [catalogue.name for catalogue in catalogues]
	counts_by_parent = _active_item_counts(names)
	folders_by_parent = {}
	if frappe.db.table_exists("Offer-Sub Catalogue"):
		folders = frappe.get_all(
			"Offer-Sub Catalogue",
			filters={"parent": ["in", names], "parenttype": "Offer-Items"},
			fields=["parent", {"COUNT": "name", "as": "folder_count"}],
			group_by="parent",
			ignore_permissions=True,
		)
		folders_by_parent = {row.parent: row.folder_count for row in folders}
	for catalogue in catalogues:
		catalogue.item_count = counts_by_parent.get(catalogue.name, 0)
		catalogue.folder_count = folders_by_parent.get(catalogue.name, 0)
	return catalogues



# ── Catalogue printing ────────────────────────────────────────────────────────
# The A4 catalogue layout used to live as a hidden block inside OfferPage.vue.
# It is now a Jinja template so it can be customised from the desk: the
# "SSPL Offer Catalogue" Print Template (format_type = Custom PDF, document_type
# = Offer-Items) wins when it exists, otherwise the bundled seed file below is
# rendered. Print Template lives in the printer_server_configuration app, so
# every lookup tolerates the doctype being absent.

OFFER_PRINT_TEMPLATE = "SSPL Offer Catalogue"
ITEMS_PER_PAGE = 9


def get_default_catalog_html():
	"""The seed template shipped with the app."""
	import os

	path = frappe.get_app_path("ssplbilling", "print_templates", "offer_catalog.html")
	if not os.path.exists(path):
		return ""
	with open(path, encoding="utf-8") as f:
		return f.read()


def parse_cipher(raw):
	"""Mirror of parseCipher() in frontend/src/encryption.js.

	Returns a 10-entry list, or None when encryption is switched off (blank
	cipher_map). A malformed map falls back to the default cipher rather than
	exposing real prices.
	"""
	default_cipher = ["K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"]
	text = (raw or "").strip()
	if not text:
		return None

	if text.startswith("["):
		try:
			parsed = frappe.parse_json(text)
		except Exception:
			return default_cipher
		if isinstance(parsed, list) and not parsed:
			return None
		if isinstance(parsed, list) and len(parsed) == 10 and all(isinstance(v, str) and v for v in parsed):
			return parsed
		return default_cipher

	chars = list(text)
	if len(chars) != 10 or any(not ch.strip() for ch in chars):
		return default_cipher
	return chars


def encrypt_price(value, cipher):
	"""Mirror of encryptPrice() in frontend/src/encryption.js."""
	if value is None:
		return ""
	try:
		n = float(value)
	except (TypeError, ValueError):
		return ""

	if not cipher:
		return str(int(n)) if n.is_integer() else f"{n:.2f}"

	return "".join(cipher[int(ch)] if ch.isdigit() else ch for ch in str(int(round(n))))


def format_rate(value, cipher_map, encrypt):
	"""Rendered price cell: cipher letters when asked, plain rupees otherwise."""
	if value is None:
		return ""
	if encrypt:
		return encrypt_price(value, parse_cipher(cipher_map))
	try:
		n = float(value)
	except (TypeError, ValueError):
		return ""
	# Match the old client-side formatting: no decimals on whole rupees.
	return f"₹{int(n):,}" if n.is_integer() else f"₹{n:,.2f}"


def print_template_doctype_exists():
	return bool(frappe.db.exists("DocType", "Print Template"))


@frappe.whitelist(allow_guest=True)
def get_offer_print_templates():
	"""Print Templates a user can pick for the catalogue export."""
	if not print_template_doctype_exists():
		return []
	templates = frappe.get_all(
		"Print Template",
		filters={"document_type": "Offer-Items", "format_type": "Custom PDF"},
		fields=["name"],
		order_by="name asc",
		ignore_permissions=True,
	)
	return [t.name for t in templates]


def get_catalog_template_html(print_template=None):
	"""Layout HTML: the named template, the seeded one, then the bundled file."""
	if print_template_doctype_exists():
		for name in (print_template, OFFER_PRINT_TEMPLATE):
			if name and frappe.db.exists("Print Template", name):
				html = frappe.db.get_value("Print Template", name, "custom_pdf_template")
				if html:
					return html
	return get_default_catalog_html()


@frappe.whitelist(allow_guest=True)
def render_offer_catalog(pageaddress, print_template=None, include_prices=0, encrypt_prices=0, customer=None, price_list=None):
	"""Render the offer catalogue to standalone HTML for printing.

	The offer page is public, so this stays guest-accessible and reuses
	get_offer_details() rather than going through /printview (which enforces
	read permission on Offer-Items and has a doc-centric Jinja context that
	cannot see the computed barcode/price/discount data).
	"""
	include_prices = cint(include_prices)
	encrypt_prices = cint(encrypt_prices)

	from ssplbilling.api.catalogue_order_api import _is_system_user, get_customer_offer
	if _is_system_user():
		encrypt_prices = 0
		offer = (get_customer_offer(pageaddress, customer, price_list) or {}).get("offer") if customer else get_offer_details(pageaddress)
	else:
		offer = get_offer_details(pageaddress)
	if not offer:
		frappe.throw(frappe._("Offer list not found"))

	cipher_map = offer.get("cipher_map") or ""
	price_lists = [pl["price_list"] for pl in offer.get("price_lists") or []]
	base_url = get_url()

	# Print templates know only plain items, so each template row prints as its variants.
	offer["items"] = [v for item in offer["items"] for v in (item.get("variants") if item.get("is_template") else [item])]
	for item in offer["items"]:
		# wkhtmltopdf and a detached print window both need absolute image URLs,
		# and file names routinely contain spaces, so the path is escaped too.
		if item.get("image") and item["image"].startswith("/"):
			item["image"] = base_url + quote(item["image"])
		for bp in item.get("barcode_prices") or []:
			bp["display_prices"] = [
				format_rate((bp.get("prices") or {}).get(pl), cipher_map, encrypt_prices)
				for pl in price_lists
			]

	items = offer["items"]
	pages = [items[i : i + ITEMS_PER_PAGE] for i in range(0, len(items), ITEMS_PER_PAGE)]

	html = get_catalog_template_html(print_template)

	# Exposed for templates that want the dynamic name; the seed layout keeps the
	# printed company literal so existing catalogues keep their masthead.
	company = frappe.db.get_single_value("Global Defaults", "default_company") or ""

	return frappe.render_template(
		html,
		{
			"offer": offer,
			"items": items,
			"pages": pages,
			"company": company,
			"include_prices": include_prices,
			"encrypt_prices": encrypt_prices,
			"items_per_page": ITEMS_PER_PAGE,
		},
		restrict_globals=True,
	)
