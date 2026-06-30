import frappe
from ssplbilling.api.stock_utils import get_draft_invoice_qtys_batch


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
def get_single_item_detailed(item_code, search_type="Sales", price_list=None, warehouse=None):
	"""Return one item with the same shape as get_all_items_detailed.
	Returns None if the item is deleted, disabled, or excluded by search_type."""
	base_filters = {"name": item_code, "disabled": 0}
	if search_type == "Sales":
		base_filters["is_sales_item"] = 1
	elif search_type == "Purchase":
		base_filters["is_purchase_item"] = 1
	elif search_type == "Stock":
		base_filters["is_stock_item"] = 1

	rows = frappe.get_all(
		"Item",
		filters=base_filters,
		fields=["item_code", "item_name", "item_print_name", "item_group",
				"stock_uom as uom", "standard_rate as rate",
				"valuation_rate", "gst_hsn_code as hsn_sac", "safety_stock"],
	)
	if not rows:
		return None

	item = rows[0]
	item["stock"] = 0.0
	item["redis_stock"] = 0.0
	item["price"] = float(item.rate or 0)
	item["valuation_rate"] = float(item.valuation_rate or item.rate or 0)
	item["price_lists"] = []
	item["uom_price_lists"] = {}
	item["warehouse_stock"] = []

	if not price_list:
		price_list = "Standard Selling" if search_type == "Sales" else "Standard Buying"

	# Prices
	pl_names = [pl.name for pl in frappe.get_all("Price List", filters={"enabled": 1}, fields=["name"])]
	for r in frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "price_list": ["in", pl_names]},
		fields=["price_list", "price_list_rate", "uom"],
	):
		rate_val = float(r.price_list_rate or 0)
		if r.uom:
			item["uom_price_lists"].setdefault(r.price_list, {})[r.uom] = rate_val
		else:
			if r.price_list == price_list:
				item["price"] = rate_val
			item["price_lists"].append({"name": r.price_list, "rate": rate_val})

	# Stock
	bin_filters = {"item_code": item_code}
	if warehouse:
		bin_filters["warehouse"] = warehouse
	draft_qtys = get_draft_invoice_qtys_batch(warehouse)
	for b in frappe.get_all("Bin", filters=bin_filters, fields=["warehouse", "actual_qty", "valuation_rate"]):
		draft = draft_qtys.get((item_code, b.warehouse), 0.0)
		qty = float(b.actual_qty or 0) - draft
		item["stock"] += qty
		item["warehouse_stock"].append({"warehouse": b.warehouse, "qty": qty})
		if b.valuation_rate:
			item["valuation_rate"] = float(b.valuation_rate)
	for (ic, _wh), dq in draft_qtys.items():
		if ic == item_code:
			item["redis_stock"] += dq

	# Tax rate + template name
	today = frappe.utils.today()
	item["tax_rate"] = 0.0
	item["item_tax_template"] = ""
	for row in frappe.get_all(
		"Item Tax",
		filters={"parent": item_code, "parenttype": "Item"},
		fields=["item_tax_template", "valid_from"],
		order_by="valid_from desc",
	):
		if row.item_tax_template and (not row.valid_from or str(row.valid_from) <= today):
			details = frappe.get_all("Item Tax Template Detail", filters={"parent": row.item_tax_template}, fields=["tax_rate"])
			item["tax_rate"] = sum(float(d.tax_rate or 0) for d in details) / 2
			item["item_tax_template"] = row.item_tax_template
			break

	# UOM conversions
	item["uoms"] = [
		{"uom": u.uom, "conversion_factor": float(u.conversion_factor or 1)}
		for u in frappe.get_all("UOM Conversion Detail", filters={"parent": item_code}, fields=["uom", "conversion_factor"])
	]

	# Barcodes
	bc_rows = frappe.get_all("Item Barcode", filters={"parent": item_code}, fields=["barcode", "uom"])
	item["barcodes_detailed"] = [{"barcode": b.barcode, "uom": b.uom or item.uom} for b in bc_rows]
	item["barcodes"] = ",".join(b["barcode"] for b in item["barcodes_detailed"])

	# Suppliers
	item["suppliers"] = [
		{"supplier": s.supplier, "supplier_part_no": s.supplier_part_no or ""}
		for s in frappe.get_all("Item Supplier", filters={"parent": item_code}, fields=["supplier", "supplier_part_no"])
	]

	return item


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
		fields=["item_code", "item_name", "item_print_name", "item_group",
				"stock_uom as uom", "standard_rate as rate", "valuation_rate", "gst_hsn_code as hsn_sac", "safety_stock"],
		limit=0,
		order_by="item_name asc",
	)

	item_map = {i.item_code: i for i in items}
	item_codes = list(item_map.keys())

	# Initialize fields
	for i in items:
		i["stock"] = 0.0
		i["redis_stock"] = 0.0
		i["price"] = float(i.rate or 0)
		i["valuation_rate"] = float(i.valuation_rate or i.rate or 0)
		i["price_lists"] = []

	# 1. Batch fetch ALL rates for active price lists (including per-UOM records)
	enabled_price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name"])
	pl_names = [pl.name for pl in enabled_price_lists]

	all_rates = frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", item_codes], "price_list": ["in", pl_names]},
		fields=["item_code", "price_list", "price_list_rate", "uom"],
	)

	# Main price list requested for the 'price' field
	if not price_list:
		price_list = "Standard Selling" if search_type == "Sales" else "Standard Buying"

	# Initialize uom_price_lists map: {price_list: {uom: rate}}
	for i in items:
		i["uom_price_lists"] = {}

	for r in all_rates:
		code = r.item_code
		if code not in item_map:
			continue
		rate_val = float(r.price_list_rate or 0)
		uom_key = r.uom or ""

		if uom_key:
			# Per-UOM Item Price record — store in uom_price_lists
			uom_pl = item_map[code].setdefault("uom_price_lists", {}).setdefault(r.price_list, {})
			uom_pl[uom_key] = rate_val
		else:
			# Base (stock-UOM) rate
			if r.price_list == price_list:
				item_map[code]["price"] = rate_val
			item_map[code]["price_lists"].append({"name": r.price_list, "rate": rate_val})

	# 2. Batch fetch stock
	stock_filters = {"item_code": ["in", item_codes]}
	if warehouse:
		stock_filters["warehouse"] = warehouse

	bins = frappe.get_all(
		"Bin",
		filters=stock_filters,
		fields=["item_code", "warehouse", "actual_qty", "valuation_rate"],
	)

	# Initialize warehouse_stock list on each item
	for i in items:
		i["warehouse_stock"] = []

	# Get draft invoice quantities for subtraction
	draft_qtys = get_draft_invoice_qtys_batch(warehouse)

	for b in bins:
		if b.item_code in item_map:
			draft_qty = draft_qtys.get((b.item_code, b.warehouse), 0.0)
			qty = float(b.actual_qty or 0) - draft_qty
			item_map[b.item_code]["stock"] += qty
			item_map[b.item_code]["warehouse_stock"].append({
				"warehouse": b.warehouse,
				"qty": qty,
			})
			bin_val_rate = float(b.get("valuation_rate") or 0)
			if bin_val_rate > 0:
				item_map[b.item_code]["valuation_rate"] = bin_val_rate

	# Populate redis stock from cached draft invoice quantities
	for (item_code, wh), draft_qty in draft_qtys.items():
		if item_code in item_map:
			item_map[item_code]["redis_stock"] += draft_qty

	# 3. Batch fetch item tax rates from Item Tax Template
	today = frappe.utils.today()
	all_item_taxes = frappe.get_all(
		"Item Tax",
		filters={"parent": ["in", item_codes], "parenttype": "Item"},
		fields=["parent as item_code", "item_tax_template", "valid_from"],
		order_by="valid_from desc",
	)
	item_template_map = {}
	for row in all_item_taxes:
		ic = row.item_code
		if ic not in item_template_map and row.item_tax_template:
			if not row.valid_from or str(row.valid_from) <= today:
				item_template_map[ic] = row.item_tax_template

	templates = list(set(item_template_map.values()))
	template_rate_map = {}
	if templates:
		template_details = frappe.get_all(
			"Item Tax Template Detail",
			filters={"parent": ["in", templates]},
			fields=["parent", "tax_rate"],
		)
		for d in template_details:
			template_rate_map.setdefault(d.parent, 0.0)
			template_rate_map[d.parent] += float(d.tax_rate or 0)
		for t in template_rate_map:
			template_rate_map[t] /= 2

	for i in items:
		ic = i.item_code
		if ic in item_template_map:
			i["tax_rate"] = template_rate_map.get(item_template_map[ic], 0.0)
			i["item_tax_template"] = item_template_map[ic]
		else:
			i["tax_rate"] = 0.0
			i["item_tax_template"] = ""

	# 4. Batch fetch UOM conversions
	all_item_uoms = frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "uom", "conversion_factor"],
	)
	item_uoms_map = {}
	for row in all_item_uoms:
		item_uoms_map.setdefault(row.item_code, []).append({
			"uom": row.uom,
			"conversion_factor": float(row.conversion_factor or 1),
		})

	for i in items:
		i["uoms"] = item_uoms_map.get(i.item_code, [])

	# 5. Batch fetch Barcodes
	all_barcodes = frappe.get_all(
		"Item Barcode",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "barcode", "uom"],
	)
	item_barcodes_map = {}
	for row in all_barcodes:
		item_barcodes_map.setdefault(row.item_code, []).append({
			"barcode": row.barcode,
			"uom": row.uom or item_map[row.item_code].uom
		})
	
	for i in items:
		i["barcodes_detailed"] = item_barcodes_map.get(i.item_code, [])
		# Maintain backward compatibility for comma-separated search if needed
		i["barcodes"] = ",".join([b["barcode"] for b in i["barcodes_detailed"]])

	# 6. Batch fetch Suppliers
	all_suppliers = frappe.get_all(
		"Item Supplier",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "supplier", "supplier_part_no"],
	)
	item_suppliers_map = {}
	for row in all_suppliers:
		item_suppliers_map.setdefault(row.item_code, []).append(
			{"supplier": row.supplier, "supplier_part_no": row.supplier_part_no or ""}
		)

	for i in items:
		i["suppliers"] = item_suppliers_map.get(i.item_code, [])

	return items


@frappe.whitelist()
def get_customer_sales_history(customer):
	"""Fetch all previous sales history for a customer in bulk with item details."""
	if not customer:
		return []

	# Fetch last 15000 items sold to this customer
	# Join with tabItem to get item_name and then add barcodes separately for performance
	history = frappe.db.sql(
		"""
		SELECT sii.item_code, i.item_name, si.name, si.posting_date as date, sii.rate, sii.qty, sii.discount_percentage as discount
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON si.name = sii.parent
		JOIN `tabItem` i ON i.name = sii.item_code
		WHERE si.customer = %s AND si.docstatus = 1
		ORDER BY si.posting_date DESC, si.creation DESC
		LIMIT 15000
		""",
		(customer,),
		as_dict=True,
	)

	item_codes = list(set(row.item_code for row in history))
	
	# Fetch barcodes for all items in history
	all_barcodes = frappe.get_all(
		"Item Barcode",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "barcode"],
	)
	item_barcodes_map = {}
	for row in all_barcodes:
		item_barcodes_map.setdefault(row.item_code, []).append(row.barcode)

	# Group by item_code for easier lookup on frontend and format values
	for row in history:
		row["date"] = str(row["date"])
		row["rate"] = float(row.rate or 0)
		row["qty"] = float(row.qty or 0)
		row["discount"] = float(row.discount or 0)
		row["barcodes"] = ",".join(item_barcodes_map.get(row.item_code, []))

	return history


@frappe.whitelist()
def get_supplier_purchase_history(supplier):
	"""Fetch all previous purchase history for a supplier in bulk with item details."""
	if not supplier:
		return []

	history = frappe.db.sql(
		"""
		SELECT pii.item_code, i.item_name, pi.name, pi.posting_date as date, pii.rate, pii.qty
		FROM `tabPurchase Invoice Item` pii
		JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		JOIN `tabItem` i ON i.name = pii.item_code
		WHERE pi.supplier = %s AND pi.docstatus = 1
		ORDER BY pi.posting_date DESC, pi.creation DESC
		LIMIT 15000
		""",
		(supplier,),
		as_dict=True,
	)

	item_codes = list(set(row.item_code for row in history))
	if not item_codes:
		return []

	all_barcodes = frappe.get_all(
		"Item Barcode",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "barcode"],
	)
	item_barcodes_map = {}
	for row in all_barcodes:
		item_barcodes_map.setdefault(row.item_code, []).append(row.barcode)

	for row in history:
		row["date"] = str(row["date"])
		row["rate"] = float(row.rate or 0)
		row["qty"] = float(row.qty or 0)
		row["barcodes"] = ",".join(item_barcodes_map.get(row.item_code, []))

	return history


@frappe.whitelist()
def get_item_purchase_history(item_code, current_supplier=None):
	"""Fetch previous purchase history for a specific item from all/other suppliers."""
	if not item_code:
		return []

	query = """
		SELECT
			pi.supplier,
			pi.supplier_name,
			pi.name,
			pi.posting_date as date,
			pii.rate,
			pii.qty
		FROM `tabPurchase Invoice Item` pii
		JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pii.item_code = %s AND pi.docstatus = 1
	"""
	params = [item_code]

	if current_supplier:
		query += " AND pi.supplier != %s"
		params.append(current_supplier)

	query += " ORDER BY pi.posting_date DESC, pi.creation DESC LIMIT 10"

	history = frappe.db.sql(query, tuple(params), as_dict=True)

	for row in history:
		row["date"] = str(row["date"])
		row["rate"] = float(row.rate or 0)
		row["qty"] = float(row.qty or 0)

	return history


