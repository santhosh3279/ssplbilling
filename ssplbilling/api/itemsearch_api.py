import frappe


@frappe.whitelist()
def get_pricing_rules(price_list=None):
	"""Fetch active selling pricing rules with their applicable item codes."""
	today = frappe.utils.today()

	rules = frappe.get_all(
		"Pricing Rule",
		filters={"selling": 1},
		fields=[
			"name", "apply_on", "min_qty", "max_qty", "disable",
			"price_or_product_discount", "rate_or_discount",
			"discount_percentage", "discount_amount", "rate",
			"priority", "applicable_for", "customer", "customer_group",
			"valid_from", "valid_upto", "for_price_list",
		],
		order_by="priority asc",
	)

	result = []
	for rule in rules:
		if rule.for_price_list and price_list and rule.for_price_list != price_list:
			continue

		rule["item_codes"] = []
		if rule.apply_on == "Item Code":
			rows = frappe.get_all("Pricing Rule Item Code", filters={"parent": rule.name}, fields=["item_code"])
			rule["item_codes"] = [r.item_code for r in rows]

		rule["min_qty"] = float(rule.min_qty or 0)
		rule["max_qty"] = float(rule.max_qty or 0)
		rule["discount_percentage"] = float(rule.discount_percentage or 0)
		rule["discount_amount"] = float(rule.discount_amount or 0)
		rule["rate"] = float(rule.rate or 0)
		rule["disable"] = int(rule.disable or 0)
		result.append(rule)

	return result


@frappe.whitelist()
def create_pricing_rule(title=None, apply_on="Item Code", item_codes=None, price_or_product_discount="Price",
		rate_or_discount="Discount Percentage", discount_percentage=0, rate=0, discount_amount=0,
		warehouse=None, min_qty=0, max_qty=0, valid_from=None, valid_upto=None,
		applicable_for=None, customer=None, customer_group=None, territory=None,
		sales_partner=None, campaign=None, for_price_list=None, priority=1):
	"""Create a new selling Pricing Rule."""
	import json
	if isinstance(item_codes, str):
		item_codes = json.loads(item_codes) if item_codes.startswith("[") else [item_codes]

	doc = frappe.new_doc("Pricing Rule")
	doc.title = title or ""
	doc.selling = 1
	doc.buying = 0
	doc.apply_on = apply_on
	doc.price_or_product_discount = price_or_product_discount or "Price"
	doc.rate_or_discount = rate_or_discount
	doc.discount_percentage = float(discount_percentage or 0)
	doc.rate = float(rate or 0)
	doc.discount_amount = float(discount_amount or 0)
	doc.min_qty = float(min_qty or 0)
	doc.max_qty = float(max_qty or 0)
	doc.valid_from = valid_from or None
	doc.valid_upto = valid_upto or None
	doc.warehouse = warehouse or ""
	doc.applicable_for = applicable_for or ""
	doc.customer = customer or ""
	doc.customer_group = customer_group or ""
	doc.territory = territory or ""
	doc.sales_partner = sales_partner or ""
	doc.campaign = campaign or ""
	doc.for_price_list = for_price_list or ""
	doc.priority = int(priority or 1)
	doc.currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "INR"

	if apply_on == "Item Code" and item_codes:
		for code in item_codes:
			if code.strip():
				doc.append("items", {"item_code": code.strip()})

	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def save_pricing_rule(name, discount_percentage=None, rate=None, discount_amount=None,
		min_qty=None, max_qty=None, valid_from=None, valid_upto=None, disable=None):
	"""Update editable fields of a Pricing Rule."""
	doc = frappe.get_doc("Pricing Rule", name)
	if discount_percentage is not None:
		doc.discount_percentage = float(discount_percentage)
	if rate is not None:
		doc.rate = float(rate)
	if discount_amount is not None:
		doc.discount_amount = float(discount_amount)
	if min_qty is not None:
		doc.min_qty = float(min_qty)
	if max_qty is not None:
		doc.max_qty = float(max_qty)
	if valid_from is not None:
		doc.valid_from = valid_from or None
	if valid_upto is not None:
		doc.valid_upto = valid_upto or None
	if disable is not None:
		doc.disable = int(frappe.parse_json(disable))
	doc.save(ignore_permissions=True)
	return {"success": True}


@frappe.whitelist()
def get_all_items_detailed(search_type="Sales", price_list=None, warehouse=None):
	"""Fetch all items with price, stock, and ALL price lists in bulk for local caching."""
	filters = {"disabled": 0}
	if search_type == "Sales":
		filters["is_sales_item"] = 1
	elif search_type == "Purchase":
		filters["is_purchase_item"] = 1
	elif search_type == "Stock":
		filters["is_stock_item"] = 1

	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["item_code", "item_name", "stock_uom as uom", "standard_rate as rate", "valuation_rate"],
		limit=0,
		order_by="item_name asc",
	)

	item_map = {i.item_code: i for i in items}
	item_codes = list(item_map.keys())

	# Initialize fields
	for i in items:
		i["stock"] = 0.0
		i["price"] = float(i.rate or 0)
		i["valuation_rate"] = float(i.valuation_rate or 0)
		i["price_lists"] = []

	# 1. Batch fetch ALL rates for active price lists
	enabled_price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name"])
	pl_names = [pl.name for pl in enabled_price_lists]

	all_rates = frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", item_codes], "price_list": ["in", pl_names]},
		fields=["item_code", "price_list", "price_list_rate"],
	)

	# Main price list requested for the 'price' field
	if not price_list:
		price_list = "Standard Selling" if search_type == "Sales" else "Standard Buying"

	for r in all_rates:
		code = r.item_code
		if code in item_map:
			rate_val = float(r.price_list_rate or 0)
			# Update the primary price if this matches the requested list
			if r.price_list == price_list:
				item_map[code]["price"] = rate_val
			
			# Append to the list of all prices
			item_map[code]["price_lists"].append({
				"name": r.price_list,
				"rate": rate_val
			})

	# 2. Batch fetch stock
	stock_filters = {"item_code": ["in", item_codes]}
	if warehouse:
		stock_filters["warehouse"] = warehouse

	bins = frappe.get_all(
		"Bin",
		filters=stock_filters,
		fields=["item_code", "actual_qty"],
	)
	
	for b in bins:
		if b.item_code in item_map:
			item_map[b.item_code]["stock"] += float(b.actual_qty or 0)

	return items


@frappe.whitelist()
def get_customer_sales_history(customer):
	"""Fetch all previous sales history for a customer in bulk."""
	if not customer:
		return []

	# Fetch last 5000 items sold to this customer
	history = frappe.db.sql(
		"""
		SELECT sii.item_code, si.name, si.posting_date as date, sii.rate, sii.qty, sii.discount_percentage as discount
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.customer = %s AND si.docstatus = 1
		ORDER BY si.posting_date DESC, si.creation DESC
		LIMIT 5000
		""",
		(customer),
		as_dict=True,
	)

	# Group by item_code for easier lookup on frontend
	# or just return as a list if the frontend wants to filter
	for row in history:
		row["date"] = str(row["date"])
		row["rate"] = float(row.rate or 0)
		row["qty"] = float(row.qty or 0)
		row["discount"] = float(row.discount or 0)

	return history
