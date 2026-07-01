import frappe
import json

@frappe.whitelist()
def get_item_prices(item_code):
	"""Fetch all Item Price records for an item including per-UOM rates."""
	if not item_code or not frappe.db.exists("Item", item_code):
		return {"prices": [], "uoms": [], "stock_uom": "Nos"}

	item = frappe.get_cached_doc("Item", item_code)
	stock_uom = item.stock_uom or "Nos"
	uoms = [
		{"uom": row.uom, "conversion_factor": float(row.conversion_factor or 1)}
		for row in item.uoms
	]

	price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name", "buying", "selling"])

	# Fetch all item prices including per-UOM entries
	item_prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code},
		fields=["price_list", "price_list_rate", "uom", "name"],
	)

	# Map: price_list → uom_key → {rate, name}
	price_map = {}
	for p in item_prices:
		pl = p.price_list
		uom_key = p.uom or ""
		price_map.setdefault(pl, {})[uom_key] = {
			"rate": float(p.price_list_rate or 0),
			"name": p.name,
		}

	results = []
	for pl in price_lists:
		pl_data = price_map.get(pl.name, {})
		base = pl_data.get("") or pl_data.get(stock_uom) or {}
		base_rate = base.get("rate", 0.0) if isinstance(base, dict) else 0.0

		uom_rates = {}
		for u in uoms:
			entry = pl_data.get(u["uom"])
			uom_rates[u["uom"]] = entry["rate"] if entry else 0.0

		results.append({
			"price_list": pl.name,
			"buying": bool(pl.buying),
			"selling": bool(pl.selling),
			"rate": base_rate,
			"uom_rates": uom_rates,
			"exists": bool(pl_data),
			"item_price_name": base.get("name") if isinstance(base, dict) else None,
		})

	pricelist_percentages = []
	if item.get("custom_pricelist_percentages"):
		pricelist_percentages = [
			{"pricelist": row.pricelist, "percentage": row.percentage}
			for row in item.custom_pricelist_percentages
		]

	return {
		"prices": results,
		"uoms": uoms,
		"stock_uom": stock_uom,
		"item_name": item.item_name,
		"pricelist_percentages": pricelist_percentages
	}

@frappe.whitelist()
def update_item_price(item_code, price_list, rate, uom=""):
	"""Update or create an Item Price record, optionally scoped to a UOM."""
	rate = float(rate)
	filters = {"item_code": item_code, "price_list": price_list}
	if uom:
		filters["uom"] = uom

	existing_name = frappe.db.get_value("Item Price", filters, "name")

	if existing_name:
		frappe.db.set_value("Item Price", existing_name, "price_list_rate", rate, update_modified=False)
	else:
		doc = frappe.new_doc("Item Price")
		doc.item_code = item_code
		doc.price_list = price_list
		doc.price_list_rate = rate
		if uom:
			doc.uom = uom
		doc.flags.ignore_permissions = True
		doc.insert()
		existing_name = doc.name

	return existing_name

@frappe.whitelist()
def update_multiple_prices(item_code, prices):
	"""Update base rate and per-UOM rates for multiple price lists."""
	if isinstance(prices, str):
		prices = json.loads(prices)

	updated = []
	realtime_events = []
	for p in prices:
		# Update base rate if changed
		if float(p.get("rate", 0)) != float(p.get("original_rate", p.get("rate", 0))):
			name = update_item_price(item_code, p["price_list"], p["rate"], uom="")
			updated.append(name)
			realtime_events.append({
				"item_code": item_code,
				"price_list": p["price_list"],
				"rate": float(p["rate"]),
				"uom": "",
			})

		# Update per-UOM rates
		for uom, rate in (p.get("uom_rates") or {}).items():
			orig = (p.get("original_uom_rates") or {}).get(uom, 0)
			if float(rate) != float(orig):
				name = update_item_price(item_code, p["price_list"], rate, uom=uom)
				updated.append(name)
				realtime_events.append({
					"item_code": item_code,
					"price_list": p["price_list"],
					"rate": float(rate),
					"uom": uom,
				})

	# frappe.db.set_value (used in update_item_price) bypasses document events,
	# so we publish the realtime events explicitly here after the DB write.
	for event in realtime_events:
		frappe.publish_realtime("item_price_update", event, after_commit=True)

	return updated


@frappe.whitelist()
def save_item_pricelist_percentages(item_code, percentages):
	"""Save price list markup percentages to the Item's custom percentages child table."""
	if isinstance(percentages, str):
		percentages = json.loads(percentages)

	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(f"Item {item_code} not found")

	item = frappe.get_doc("Item", item_code)
	item.set("custom_pricelist_percentages", [])

	for p in percentages:
		if p.get("pricelist") and p.get("percentage") is not None:
			item.append("custom_pricelist_percentages", {
				"pricelist": p["pricelist"],
				"percentage": str(p["percentage"])
			})

	item.flags.ignore_permissions = True
	item.save()
	return {"status": "success"}


def on_item_price_update(doc, method=None):
	"""Publish a realtime update for the parent Item when its Price changes."""
	if doc.get("item_code"):
		is_deleted = (method == "on_trash") or doc.flags.get("in_trash")
		rate = 0.0 if is_deleted else float(doc.price_list_rate or 0)
		frappe.publish_realtime(
			"item_price_update",
			{
				"item_code": doc.item_code,
				"price_list": doc.price_list,
				"rate": rate,
				"uom": doc.uom or ""
			},
			after_commit=True
		)


