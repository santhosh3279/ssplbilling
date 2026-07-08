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

def get_draft_purchase_qtys_from_redis():
	"""Fetch draft purchase invoice quantities from Redis cache. If not present, query database and cache it."""
	cache_key = "ssplbilling:draft_purchase_qtys"
	cached = frappe.cache().get_value(cache_key)
	if cached is not None:
		try:
			return json.loads(cached)
		except Exception:
			pass

	# Cache miss: query database for all draft Purchase Invoices
	rows = frappe.get_all(
		"Purchase Invoice Item",
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

def get_draft_purchase_qty(item_code, warehouse=None):
	"""Return the sum of quantities of an item in draft Purchase Invoices using Redis cache."""
	qtys_raw = get_draft_purchase_qtys_from_redis()
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

def get_draft_purchase_qtys_batch(warehouse=None):
	"""Return a map of {(item_code, warehouse): qty} for draft Purchase Invoices from Redis cache."""
	qtys_raw = get_draft_purchase_qtys_from_redis()
	qtys = {}
	for k, v in qtys_raw.items():
		parts = k.split(":")
		if len(parts) == 2:
			item_code, wh = parts
			if not warehouse or wh == warehouse:
				qtys[(item_code, wh)] = float(v)
	return qtys

def get_item_available_stock(item_code, warehouse):
	"""Compute the live available qty (Bin actual_qty minus draft invoice qty plus draft purchase qty) for one
	item+warehouse, plus the item's total draft (redis) qty across all warehouses."""
	actual_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0.0
	return {
		"item_code": item_code,
		"warehouse": warehouse,
		"qty": float(actual_qty) - get_draft_invoice_qty(item_code, warehouse) + get_draft_purchase_qty(item_code, warehouse),
		"redis_stock": get_draft_invoice_qty(item_code),
		"redis_purchase_stock": get_draft_purchase_qty(item_code),
	}

def publish_stock_update(item_code, warehouse):
	"""Broadcast the live stock/redis-stock figures for an item+warehouse to all clients."""
	if not item_code or not warehouse:
		return
	frappe.publish_realtime("stock_update", get_item_available_stock(item_code, warehouse), after_commit=True)

def _iter_item_warehouse_pairs(doc):
	"""Yield (item_code, warehouse) for every line on the doc AND on its pre-save
	version. Including the pre-save rows means a line removed by a draft edit still
	triggers a rebroadcast, so the freed stock for the removed item+warehouse is
	pushed to clients even though it is no longer on the current doc."""
	docs = [doc]
	before = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	if before is not None:
		docs.append(before)
	for d in docs:
		for row in d.get("items", []):
			if row.item_code and row.warehouse:
				yield row.item_code, row.warehouse

def _publish_stock_updates_for_doc(doc):
	"""Broadcast stock updates for every distinct item+warehouse touched by a document,
	spanning both its current and pre-save line items."""
	if doc is None:
		return
	seen = set()
	for item_code, warehouse in _iter_item_warehouse_pairs(doc):
		key = (item_code, warehouse)
		if key not in seen:
			seen.add(key)
			publish_stock_update(item_code, warehouse)

def publish_stock_updates(doc, method=None):
	"""Doc event handler: broadcast live stock figures for every item on a stock document."""
	_publish_stock_updates_for_doc(doc)

def clear_draft_invoice_qtys_cache(doc=None, method=None):
	"""Invalidate the draft invoice quantities cache in Redis and broadcast the resulting
	live stock/redis-stock figures for every item on the invoice to all clients."""
	frappe.cache().delete_value("ssplbilling:draft_invoice_qtys")
	_publish_stock_updates_for_doc(doc)
	# The broadcast above rebuilt the cache from the current (possibly uncommitted)
	# transaction state, so clear it again — a rollback must not leave a stale cache
	# behind; the next read will rebuild it fresh from committed data.
	frappe.cache().delete_value("ssplbilling:draft_invoice_qtys")

def clear_draft_purchase_qtys_cache(doc=None, method=None):
	"""Invalidate the draft purchase quantities cache in Redis and broadcast the resulting
	live stock/redis-stock figures for every item on the purchase invoice to all clients."""
	frappe.cache().delete_value("ssplbilling:draft_purchase_qtys")
	_publish_stock_updates_for_doc(doc)
	# The broadcast above rebuilt the cache from the current (possibly uncommitted)
	# transaction state, so clear it again — a rollback must not leave a stale cache
	# behind; the next read will rebuild it fresh from committed data.
	frappe.cache().delete_value("ssplbilling:draft_purchase_qtys")

