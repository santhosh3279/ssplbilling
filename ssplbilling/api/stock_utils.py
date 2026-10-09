import frappe
import json

def _draft_item_rows(parent_doctype, child_doctype):
	"""Item rows of all draft invoices of `parent_doctype`.

	The child table has no docstatus index, so filtering it directly scans every invoice line ever
	posted (~0.2-1 s, on every save). Starting from the parent's drafts and joining on the indexed
	`parent` column reads only the draft lines (~5 ms)."""
	return frappe.db.sql(
		f"""SELECT child.item_code, child.warehouse, child.qty
		   FROM `tab{parent_doctype}` parent
		   JOIN `tab{child_doctype}` child
		     ON child.parent = parent.name AND child.parenttype = %(parenttype)s
		   WHERE parent.docstatus = 0""",
		{"parenttype": parent_doctype},
		as_dict=True,
	)


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
	rows = _draft_item_rows("Sales Invoice", "Sales Invoice Item")
	
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
	rows = _draft_item_rows("Purchase Invoice", "Purchase Invoice Item")
	
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
			if not warehouse:
				qtys[(item_code, wh)] = float(v)
			elif isinstance(warehouse, (list, tuple, set)):
				if wh in warehouse:
					qtys[(item_code, wh)] = float(v)
			elif wh == warehouse:
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
			if not warehouse:
				qtys[(item_code, wh)] = float(v)
			elif isinstance(warehouse, (list, tuple, set)):
				if wh in warehouse:
					qtys[(item_code, wh)] = float(v)
			elif wh == warehouse:
				qtys[(item_code, wh)] = float(v)
	return qtys

def get_item_available_stock(item_code, warehouse):
	"""Compute the live available qty (Bin actual_qty minus draft invoice qty plus draft purchase qty) for one
	item+warehouse, plus the item's total draft (redis) qty across all warehouses.

	The warehouse-scoped draft quantities and Bin valuation rate let warehouse-scoped client caches
	recompute `redis_stock` / `valuation_rate` exactly as get_all_items_detailed would."""
	bin_row = frappe.db.get_value(
		"Bin", {"item_code": item_code, "warehouse": warehouse}, ["actual_qty", "valuation_rate"], as_dict=True
	) or {}
	draft_qty = get_draft_invoice_qty(item_code, warehouse)
	draft_purchase_qty = get_draft_purchase_qty(item_code, warehouse)
	return {
		"item_code": item_code,
		"warehouse": warehouse,
		"qty": float(bin_row.get("actual_qty") or 0) - draft_qty + draft_purchase_qty,
		"redis_stock": get_draft_invoice_qty(item_code),
		"redis_purchase_stock": get_draft_purchase_qty(item_code),
		"draft_qty": draft_qty,
		"draft_purchase_qty": draft_purchase_qty,
		# Per-warehouse drafts let all-warehouse caches sum only their company's warehouses.
		"draft_by_warehouse": _item_qtys_by_warehouse(get_draft_invoice_qtys_from_redis(), item_code),
		"draft_purchase_by_warehouse": _item_qtys_by_warehouse(get_draft_purchase_qtys_from_redis(), item_code),
		"valuation_rate": float(bin_row.get("valuation_rate") or 0),
	}


def _item_qtys_by_warehouse(qtys_raw, item_code):
	"""{warehouse: qty} for one item from a raw "item:warehouse" -> qty draft map."""
	by_warehouse = {}
	for key, qty in qtys_raw.items():
		parts = key.split(":")
		if len(parts) == 2 and parts[0] == item_code:
			by_warehouse[parts[1]] = by_warehouse.get(parts[1], 0.0) + float(qty)
	return by_warehouse

def publish_stock_update(item_code, warehouse):
	"""Broadcast the live stock/redis-stock figures for an item+warehouse to all clients."""
	if not item_code or not warehouse:
		return
	frappe.publish_realtime("stock_update", get_item_available_stock(item_code, warehouse), after_commit=True)
	# Public catalogues receive an invalidation, never private draft bill details.
	from ssplbilling.api.offer_sync import _broadcast_offer_update
	_broadcast_offer_update({"type": "stock", "item_code": item_code})

def publish_stock_ledger_update(doc, method=None):
	"""Doc event (Stock Ledger Entry after_insert): queue a stock_update for the entry's item+warehouse.

	Covers every stock movement (Stock Entry, Delivery Note, Purchase Receipt, Stock Reconciliation,
	repack, invoice submit/cancel), so client item caches can rely on realtime updates instead of
	refetching. Pairs are de-duplicated per transaction and computed after commit, when the Bin holds
	the final quantity."""
	if not doc or not doc.item_code or not doc.warehouse:
		return
	pending = getattr(frappe.local, "_sspl_stock_pairs", None)
	if pending is None:
		pending = frappe.local._sspl_stock_pairs = set()
		frappe.db.after_commit.add(_flush_stock_ledger_updates)
		frappe.db.after_rollback.add(_discard_stock_ledger_updates)
	pending.add((doc.item_code, doc.warehouse))


def _flush_stock_ledger_updates():
	pending = getattr(frappe.local, "_sspl_stock_pairs", None) or set()
	frappe.local._sspl_stock_pairs = None
	for item_code, warehouse in pending:
		frappe.publish_realtime("stock_update", get_item_available_stock(item_code, warehouse), after_commit=False)


def _discard_stock_ledger_updates():
	frappe.local._sspl_stock_pairs = None


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

