import frappe
from frappe.rate_limiter import rate_limit

from ssplbilling.api.itemsearch_api import _build_items_detailed
from ssplbilling.api.offer_api import encrypt_price, parse_cipher

MAX_RESULTS = 20
DEFAULT_CIPHER = list("KLMNOPQRST")


def _like(token):
	"""LIKE pattern for a search token, with the user's own wildcards escaped."""
	escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
	return f"%{escaped}%"


def _search_item_codes(query):
	"""Item codes where every word of `query` matches the item code, item name or a barcode.

	Words may come in any order ("red pen 10" finds "Pen Red 10 Pcs"). Exact item code /
	barcode hits sort first so a scanned barcode lands on its item."""
	tokens = [t for t in query.split() if t][:6]
	if not tokens:
		return []

	conditions = []
	params = {"exact": query.strip(), "limit": MAX_RESULTS}
	for n, token in enumerate(tokens):
		key = f"t{n}"
		params[key] = _like(token)
		conditions.append(
			f"""(item.name LIKE %({key})s OR item.item_name LIKE %({key})s
				OR EXISTS (SELECT 1 FROM `tabItem Barcode` bc
					WHERE bc.parent = item.name AND bc.barcode LIKE %({key})s))"""
		)

	rows = frappe.db.sql(
		f"""SELECT item.name
			FROM `tabItem` item
			WHERE item.disabled = 0 AND item.is_sales_item = 1
				AND {" AND ".join(conditions)}
			ORDER BY
				(item.name = %(exact)s
					OR EXISTS (SELECT 1 FROM `tabItem Barcode` bc
						WHERE bc.parent = item.name AND bc.barcode = %(exact)s)) DESC,
				item.item_name ASC
			LIMIT %(limit)s""",
		params,
	)
	return [r[0] for r in rows]


def _public_row(item, selling_lists, cipher):
	"""Only what a public stock check may show: no valuation, buying rates or tax internals.

	`selling_lists` is in Price List doctype order (creation); prices follow that order."""
	# {price_list: {uom: rate}} from per-UOM Item Prices, with the base (no-UOM) rate as the stock UOM
	prices = {}
	for pl_name, uom_rates in (item.get("uom_price_lists") or {}).items():
		if pl_name in selling_lists:
			prices[pl_name] = {uom: encrypt_price(rate, cipher) for uom, rate in uom_rates.items()}
	for pl in item.get("price_lists", []):
		if pl["name"] in selling_lists:
			prices.setdefault(pl["name"], {}).setdefault(item.get("uom"), encrypt_price(pl["rate"], cipher))

	stock = float(item.get("stock") or 0)
	redis_stock = float(item.get("redis_stock") or 0)
	redis_purchase = float(item.get("redis_purchase_stock") or 0)
	return {
		"item_code": item["item_code"],
		"item_name": item.get("item_name"),
		"uom": item.get("uom"),
		"image": item.get("image") or "",
		"barcodes": [b["barcode"] for b in item.get("barcodes_detailed", [])],
		"uoms": item.get("uoms", []),
		# stock = book stock - draft sales + draft purchases (same figure billing uses)
		"stock": stock,
		"redis_stock": redis_stock,
		"redis_purchase_stock": redis_purchase,
		"actual_stock": stock + redis_stock - redis_purchase,
		"warehouse_stock": [w for w in item.get("warehouse_stock", []) if w.get("qty")],
		"prices": [{"price_list": pl, "rates": prices[pl]} for pl in selling_lists if prices.get(pl)],
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=60)
def search_stock(query=None):
	"""Public mobile stock check: item stock (incl. draft/redis qty) and selling prices."""
	query = (query or "").strip()[:100]
	if len(query) < 2:
		return []

	codes = _search_item_codes(query)
	if not codes:
		return []

	company = frappe.db.get_single_value("Global Defaults", "default_company")
	rows = _build_items_detailed("Sales", None, None, company, item_codes=codes)
	order = {code: n for n, code in enumerate(codes)}
	rows.sort(key=lambda r: order.get(r["item_code"], len(order)))
	selling_lists = frappe.get_all(
		"Price List", filters={"enabled": 1, "selling": 1}, pluck="name", order_by="creation asc"
	)
	# Rates leave the server only as cipher text; with encryption switched off in
	# Settings the default cipher still applies, since this page is public
	cipher_map = frappe.db.get_single_value("SSPL Billing Settings", "cipher_map")
	cipher = parse_cipher(cipher_map) or DEFAULT_CIPHER
	return [_public_row(r, selling_lists, cipher) for r in rows]
