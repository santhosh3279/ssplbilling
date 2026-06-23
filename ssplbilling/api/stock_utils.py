import frappe
import json

def get_draft_invoice_qtys_from_redis():
	"""Fetch draft invoice quantities from Redis cache. If not present, query database and cache it."""
	cache_key = "ssplbilling:draft_invoice_qtys"
	cached = frappe.cache().get_value(cache_key)
	if cached is not None:
		try:
			return json.loads(cached)
		except Exception:
			pass

	# Cache miss: query database for all draft Sales Invoices
	rows = frappe.get_all(
		"Sales Invoice Item",
		filters={"docstatus": 0},
		fields=["item_code", "warehouse", "qty"]
	)
	
	qtys = {}
	for r in rows:
		if not r.item_code or not r.warehouse:
			continue
		key = f"{r.item_code}:{r.warehouse}"
		qtys[key] = qtys.get(key, 0.0) + float(r.qty or 0)

	frappe.cache().set_value(cache_key, json.dumps(qtys))
	return qtys

def get_draft_invoice_qty(item_code, warehouse=None):
	"""Return the sum of quantities of an item in draft Sales Invoices using Redis cache."""
	qtys_raw = get_draft_invoice_qtys_from_redis()
	total = 0.0
	for k, v in qtys_raw.items():
		parts = k.split(":")
		if len(parts) == 2:
			ic, wh = parts
			if ic == item_code:
				if not warehouse or wh == warehouse:
					total += float(v)
	return total

def get_draft_invoice_qtys_batch(warehouse=None):
	"""Return a map of {(item_code, warehouse): qty} for draft Sales Invoices from Redis cache."""
	qtys_raw = get_draft_invoice_qtys_from_redis()
	qtys = {}
	for k, v in qtys_raw.items():
		parts = k.split(":")
		if len(parts) == 2:
			item_code, wh = parts
			if not warehouse or wh == warehouse:
				qtys[(item_code, wh)] = float(v)
	return qtys

def clear_draft_invoice_qtys_cache(doc=None, method=None):
	"""Invalidate the draft invoice quantities cache in Redis."""
	frappe.cache().delete_value("ssplbilling:draft_invoice_qtys")
