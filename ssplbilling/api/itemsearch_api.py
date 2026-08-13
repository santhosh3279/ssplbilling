import frappe
from ssplbilling.api.stock_utils import get_draft_invoice_qtys_batch, get_draft_purchase_qtys_batch


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
def get_single_item_detailed(item_code, search_type="Sales", price_list=None, warehouse=None, company=None):
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
				"valuation_rate", "gst_hsn_code as hsn_sac", "safety_stock", "min_order_qty", "custom_max_stock", "custom_max_order_qty"],
	)
	if not rows:
		return None

	item = rows[0]
	item["stock"] = 0.0
	item["redis_stock"] = 0.0
	item["redis_purchase_stock"] = 0.0
	item["price"] = float(item.rate or 0)
	item["valuation_rate"] = float(item.valuation_rate or item.rate or 0)
	item["price_lists"] = []
	item["uom_price_lists"] = {}
	item["warehouse_stock"] = []

	if not price_list:
		price_list = "Standard Selling" if search_type == "Sales" else "Standard Buying"

	# Prices
	enabled_price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name", "buying", "selling"])
	pl_names = [pl.name for pl in enabled_price_lists]
	pl_map = {pl.name: {"buying": bool(pl.buying), "selling": bool(pl.selling)} for pl in enabled_price_lists}

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
			pl_info = pl_map.get(r.price_list, {"buying": False, "selling": False})
			item["price_lists"].append({
				"name": r.price_list,
				"rate": rate_val,
				"buying": pl_info["buying"],
				"selling": pl_info["selling"],
			})

	# Stock
	bin_filters = {"item_code": item_code}
	allowed_warehouses = None
	if company:
		allowed_warehouses = frappe.get_all(
			"Warehouse",
			filters={"company": company, "disabled": 0, "is_group": 0},
			pluck="name"
		)
		bin_filters["warehouse"] = ["in", allowed_warehouses]
	draft_qtys = get_draft_invoice_qtys_batch(allowed_warehouses)
	draft_purchase_qtys = get_draft_purchase_qtys_batch(allowed_warehouses)
	for b in frappe.get_all("Bin", filters=bin_filters, fields=["warehouse", "actual_qty", "valuation_rate"]):
		draft = draft_qtys.get((item_code, b.warehouse), 0.0)
		draft_purchase = draft_purchase_qtys.get((item_code, b.warehouse), 0.0)
		qty = float(b.actual_qty or 0) - draft + draft_purchase
		if warehouse and b.warehouse == warehouse:
			item["stock"] += qty
		elif not warehouse:
			item["stock"] += qty
		item["warehouse_stock"].append({"warehouse": b.warehouse, "qty": qty})
		if b.valuation_rate and (not warehouse or b.warehouse == warehouse):
			item["valuation_rate"] = float(b.valuation_rate)
	for (ic, wh), dq in draft_qtys.items():
		if ic == item_code:
			if not warehouse or wh == warehouse:
				item["redis_stock"] += dq
	for (ic, wh), dpq in draft_purchase_qtys.items():
		if ic == item_code:
			if not warehouse or wh == warehouse:
				item["redis_purchase_stock"] += dpq

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
	bc_rows = frappe.get_all("Item Barcode", filters={"parent": item_code}, fields=["barcode", "uom"], order_by="idx asc")
	item["barcodes_detailed"] = [{"barcode": b.barcode, "uom": b.uom or item.uom} for b in bc_rows]
	item["barcodes"] = ",".join(b["barcode"] for b in item["barcodes_detailed"])

	# Suppliers
	item["suppliers"] = [
		{"supplier": s.supplier, "supplier_part_no": s.supplier_part_no or ""}
		for s in frappe.get_all("Item Supplier", filters={"parent": item_code}, fields=["supplier", "supplier_part_no"])
	]

	# Price List Percentages
	item["pricelist_percentages"] = [
		{"pricelist": p.pricelist, "percentage": float(p.percentage or 0)}
		for p in frappe.get_all(
			"Item Price List Percentage",
			filters={"parent": item_code},
			fields=["pricelist", "percentage"],
		)
	]

	return item



@frappe.whitelist()
def get_all_items_detailed(search_type="Sales", price_list=None, warehouse=None, company=None):
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
				"stock_uom as uom", "standard_rate as rate", "valuation_rate", "gst_hsn_code as hsn_sac", "safety_stock", "min_order_qty", "custom_max_stock", "custom_max_order_qty", "image"],
		limit=0,
		order_by="item_name asc",
	)

	item_map = {i.item_code: i for i in items}
	item_codes = list(item_map.keys())

	# Initialize fields
	for i in items:
		i["stock"] = 0.0
		i["redis_stock"] = 0.0
		i["redis_purchase_stock"] = 0.0
		i["price"] = float(i.rate or 0)
		i["valuation_rate"] = float(i.valuation_rate or i.rate or 0)
		i["price_lists"] = []

	# 1. Batch fetch ALL rates for active price lists (including per-UOM records)
	enabled_price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name", "buying", "selling"])
	pl_names = [pl.name for pl in enabled_price_lists]
	pl_map = {pl.name: {"buying": bool(pl.buying), "selling": bool(pl.selling)} for pl in enabled_price_lists}

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
			pl_info = pl_map.get(r.price_list, {"buying": False, "selling": False})
			item_map[code]["price_lists"].append({
				"name": r.price_list,
				"rate": rate_val,
				"buying": pl_info["buying"],
				"selling": pl_info["selling"],
			})

	# 2. Batch fetch stock
	stock_filters = {"item_code": ["in", item_codes]}
	allowed_warehouses = None
	if company:
		allowed_warehouses = frappe.get_all(
			"Warehouse",
			filters={"company": company, "disabled": 0, "is_group": 0},
			pluck="name"
		)
		stock_filters["warehouse"] = ["in", allowed_warehouses]

	bins = frappe.get_all(
		"Bin",
		filters=stock_filters,
		fields=["item_code", "warehouse", "actual_qty", "valuation_rate"],
	)

	# Initialize warehouse_stock list on each item
	for i in items:
		i["warehouse_stock"] = []

	# Get draft invoice/purchase quantities for subtraction/addition across company warehouses
	draft_qtys = get_draft_invoice_qtys_batch(allowed_warehouses)
	draft_purchase_qtys = get_draft_purchase_qtys_batch(allowed_warehouses)

	for b in bins:
		if b.item_code in item_map:
			draft_qty = draft_qtys.get((b.item_code, b.warehouse), 0.0)
			draft_purchase_qty = draft_purchase_qtys.get((b.item_code, b.warehouse), 0.0)
			qty = float(b.actual_qty or 0) - draft_qty + draft_purchase_qty
			if warehouse and b.warehouse == warehouse:
				item_map[b.item_code]["stock"] += qty
			elif not warehouse:
				item_map[b.item_code]["stock"] += qty

			item_map[b.item_code]["warehouse_stock"].append({
				"warehouse": b.warehouse,
				"qty": qty,
			})
			bin_val_rate = float(b.get("valuation_rate") or 0)
			if bin_val_rate > 0 and (not warehouse or b.warehouse == warehouse):
				item_map[b.item_code]["valuation_rate"] = bin_val_rate

	# Populate redis stock from cached draft invoice quantities (active warehouse only)
	for (item_code, wh), draft_qty in draft_qtys.items():
		if item_code in item_map:
			if not warehouse or wh == warehouse:
				item_map[item_code]["redis_stock"] += draft_qty

	# Populate redis purchase stock from cached draft purchase quantities (active warehouse only)
	for (item_code, wh), draft_purchase_qty in draft_purchase_qtys.items():
		if item_code in item_map:
			if not warehouse or wh == warehouse:
				item_map[item_code]["redis_purchase_stock"] += draft_purchase_qty

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
		order_by="idx asc",
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

	# 7. Batch fetch Price List Percentages
	all_percentages = frappe.get_all(
		"Item Price List Percentage",
		filters={"parent": ["in", item_codes]},
		fields=["parent as item_code", "pricelist", "percentage"],
	)
	item_percentages_map = {}
	for row in all_percentages:
		item_percentages_map.setdefault(row.item_code, []).append({
			"pricelist": row.pricelist,
			"percentage": float(row.percentage or 0)
		})

	for i in items:
		i["pricelist_percentages"] = item_percentages_map.get(i.item_code, [])

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
		order_by="idx asc",
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
		order_by="idx asc",
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


@frappe.whitelist()
def print_party_history_pdf(party, party_type, limit=50, view_mode="item", current_items=None):
	"""Generate a PDF of customer/supplier purchase history."""
	if not party or not party_type:
		frappe.throw("Missing party or party_type")

	limit = frappe.utils.cint(limit) or 50

	# 1. Fetch raw history
	if party_type.lower() in ("customer", "sales invoice"):
		raw_history = get_customer_sales_history(party)
		party_noun = "Customer"
		title = f"Sales History for Customer: {party}"
	else:
		raw_history = get_supplier_purchase_history(party)
		party_noun = "Supplier"
		title = f"Purchase History for Supplier: {party}"

	# 2. Process data based on view_mode
	processed_rows = []
	if view_mode == "invoice":
		# Sort by qty descending, limit results
		sorted_raw = sorted(raw_history, key=lambda x: x.get("qty", 0), reverse=True)
		processed_rows = sorted_raw[:limit]
	else:
		# Aggregate to item-wise
		item_map = {}
		for h in raw_history:
			item_code = h.get("item_code")
			if not item_code:
				continue
			if item_code not in item_map:
				item_map[item_code] = {
					"item_code": item_code,
					"item_name": h.get("item_name", ""),
					"barcodes": h.get("barcodes", ""),
					"total_qty": 0.0,
					"last_rate": h.get("rate", 0.0),
					"last_date": h.get("date", ""),
					"last_invoice": h.get("name", ""),
				}
			item_map[item_code]["total_qty"] += h.get("qty", 0.0)

		item_list = list(item_map.values())

		# If 'not-today', filter out items currently in invoice
		if view_mode == "not-today" and current_items:
			current_set = set(item.strip() for item in current_items.split(",") if item.strip())
			item_list = [item for item in item_list if item["item_code"] not in current_set]

		# Sort by total_qty descending, limit results
		sorted_items = sorted(item_list, key=lambda x: x.get("total_qty", 0.0), reverse=True)
		processed_rows = sorted_items[:limit]

	# 3. Generate HTML
	html = _generate_history_html(title, party_noun, party, view_mode, processed_rows)

	# 4. Generate and return PDF
	from frappe.utils.pdf import get_pdf
	
	frappe.response.type = "pdf"
	frappe.response.filename = f"{party_noun}_History_{party.replace(' ', '_')}.pdf"
	frappe.response.filecontent = get_pdf(html)


def _dmy(val):
	"""Render a date-ish value as dd/mm/yyyy for print output."""
	if not val:
		return ""
	s = str(val).split(" ")[0]
	parts = s.split("-")
	if len(parts) == 3 and len(parts[0]) == 4:
		return f"{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}"
	return str(val)


def _generate_history_html(title, party_noun, party, view_mode, rows):
	import datetime
	generated_on = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")

	# Mode label
	if view_mode == "invoice":
		mode_label = "Invoice-wise Transactions"
	elif view_mode == "item":
		mode_label = "Item-wise Summary"
	else:
		mode_label = "Items Not Purchased Today"

	# Build Table Header
	if view_mode == "invoice":
		headers = ["Date", "Item Code", "Item Name", "Barcodes", "Qty", "Rate", "Invoice"]
		col_styles = [
			"width: 12%; text-align: left;",
			"width: 15%; text-align: left; font-family: monospace; font-weight: bold;",
			"width: 33%; text-align: left;",
			"width: 15%; text-align: left; font-family: monospace; color: #555;",
			"width: 8%; text-align: right; font-weight: bold;",
			"width: 10%; text-align: right; font-family: monospace; color: #b45309;",
			"width: 7%; text-align: left;"
		]
	else:
		headers = ["Item Code", "Item Name", "Barcodes", "Total Qty", "Last Rate", "Last Date", "Last Invoice"]
		col_styles = [
			"width: 15%; text-align: left; font-family: monospace; font-weight: bold;",
			"width: 33%; text-align: left;",
			"width: 15%; text-align: left; font-family: monospace; color: #555;",
			"width: 8%; text-align: right; font-weight: bold;",
			"width: 10%; text-align: right; font-family: monospace; color: #b45309;",
			"width: 12%; text-align: left;",
			"width: 7%; text-align: left;"
		]

	thead_html = "".join(f'<th style="{style} padding: 8px; border-bottom: 2px solid #ddd; background-color: #f3f4f6; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">{h}</th>' for h, style in zip(headers, col_styles))

	# Build Table Rows
	tbody_html = ""
	if not rows:
		tbody_html = f'<tr><td colspan="{len(headers)}" style="padding: 20px; text-align: center; font-style: italic; color: #777;">No history records found.</td></tr>'
	else:
		for r in rows:
			if view_mode == "invoice":
				qty_val = float(r.get("qty") or 0)
				qty_str = f"{qty_val:.3f}" if qty_val % 1 != 0 else f"{int(qty_val)}"
				cols = [
					_dmy(r.get("date")),
					r.get("item_code", ""),
					r.get("item_name", ""),
					r.get("barcodes", ""),
					qty_str,
					f'{float(r.get("rate") or 0):.2f}',
					r.get("name", "")
				]
			else:
				total_qty_val = float(r.get("total_qty") or 0)
				total_qty_str = f"{total_qty_val:.3f}" if total_qty_val % 1 != 0 else f"{int(total_qty_val)}"
				cols = [
					r.get("item_code", ""),
					r.get("item_name", ""),
					r.get("barcodes", ""),
					total_qty_str,
					f'{float(r.get("last_rate") or 0):.2f}',
					_dmy(r.get("last_date")),
					r.get("last_invoice", "")
				]

			row_html = "<tr>"
			for val, style in zip(cols, col_styles):
				row_html += f'<td style="{style} padding: 6px 8px; border-bottom: 1px solid #e5e7eb; font-size: 11px;">{val}</td>'
			row_html += "</tr>"
			tbody_html += row_html

	# Main template
	html = f"""
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="utf-8">
		<style>
			@page {{
				size: A4;
				margin: 15mm 15mm 20mm 15mm;
			}}
			body {{
				font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
				color: #1f2937;
				margin: 0;
				padding: 0;
			}}
			.header {{
				border-bottom: 3px solid #10b981;
				padding-bottom: 12px;
				margin-bottom: 20px;
			}}
			.header table {{
				width: 100%;
				border-collapse: collapse;
			}}
			.header .title {{
				font-size: 18px;
				font-weight: bold;
				color: #111827;
			}}
			.header .meta {{
				font-size: 11px;
				color: #6b7280;
				text-align: right;
			}}
			.header .subtitle {{
				font-size: 12px;
				color: #4b5563;
				margin-top: 4px;
				font-weight: 500;
			}}
			.content-table {{
				width: 100%;
				border-collapse: collapse;
				margin-top: 10px;
			}}
			.footer {{
				position: fixed;
				bottom: -12mm;
				left: 0;
				right: 0;
				text-align: center;
				font-size: 10px;
				color: #9ca3af;
				border-top: 1px solid #e5e7eb;
				padding-top: 8px;
			}}
		</style>
	</head>
	<body>
		<div class="header">
			<table>
				<tr>
					<td>
						<div class="title">{title}</div>
						<div class="subtitle">Report Mode: {mode_label} (Top {len(rows)} items)</div>
					</td>
					<td class="meta">
						<strong>Generated:</strong> {generated_on}<br>
						<strong>Party Type:</strong> {party_noun}
					</td>
				</tr>
			</table>
		</div>
		<table class="content-table">
			<thead>
				<tr>
					{thead_html}
				</tr>
			</thead>
			<tbody>
				{tbody_html}
			</tbody>
		</table>
		<div class="footer">
			Sundaram and Sons Private Ltd — Wholesale Billing System
		</div>
	</body>
	</html>
	"""
	return html



