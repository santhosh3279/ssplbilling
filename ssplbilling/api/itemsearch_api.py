import frappe

@frappe.whitelist()
def get_all_items_detailed(search_type="Sales", price_list=None, warehouse=None):
	"""Fetch all items with price, stock, and ALL price lists in bulk for local caching."""
	filters = {"disabled": 0}
	if search_type == "Sales":
		filters["is_sales_item"] = 1
	elif search_type == "Purchase":
		filters["is_purchase_item"] = 1

	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["item_code", "item_name", "stock_uom as uom", "standard_rate as rate"],
		limit=0,
		order_by="item_name asc",
	)

	item_map = {i.item_code: i for i in items}
	item_codes = list(item_map.keys())

	# Initialize fields
	for i in items:
		i["stock"] = 0.0
		i["price"] = float(i.rate or 0)
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
