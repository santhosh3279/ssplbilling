import json
import frappe
from frappe.model.naming import parse_naming_series
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows


# ──────────────────────────────────────────────────────────────────────────────
# Item helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_item_tax_rate(item_code):
	"""Return the effective tax rate (%) for an item from its Item Tax Template."""
	today = frappe.utils.today()
	tax_rows = frappe.get_all(
		"Item Tax",
		filters={"parent": item_code, "parenttype": "Item"},
		fields=["item_tax_template", "valid_from"],
		order_by="valid_from desc",
	)
	template_name = None
	for row in tax_rows:
		if not row.valid_from or str(row.valid_from) <= today:
			template_name = row.item_tax_template
			break

	if not template_name:
		return 0.0

	details = frappe.get_all(
		"Item Tax Template Detail",
		filters={"parent": template_name},
		fields=["tax_rate"],
	)
	return float(sum(d.tax_rate or 0 for d in details)) / 2


@frappe.whitelist()
def get_item_details(item_code, price_list="Standard Selling", warehouse=None):
	"""Look up item by code or barcode. Returns item details + stock + rate."""
	barcode_item = frappe.db.get_value("Item Barcode", {"barcode": item_code}, "parent")
	if barcode_item:
		item_code = barcode_item

	if not frappe.db.exists("Item", item_code):
		return {"found": False, "item_code": item_code}

	item = frappe.get_cached_doc("Item", item_code)
	wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

	rate = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "selling": 1, "uom": item.stock_uom},
		"price_list_rate",
	) or frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "selling": 1},
		"price_list_rate",
	) or item.standard_rate or 0

	# Fetch UOM conversions
	uoms = frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": item_code},
		fields=["uom", "conversion_factor"],
	)

	# Fetch all price list rates for this item (including per-UOM)
	all_rates = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "selling": 1},
		fields=["price_list", "price_list_rate", "uom"],
	)

	uom_price_lists = {}
	for r in all_rates:
		pl = r.price_list
		uom_key = r.uom or ""
		if uom_key:
			uom_price_lists.setdefault(pl, {})[uom_key] = float(r.price_list_rate or 0)

	stock_qty = 0
	if wh:
		stock_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty") or 0

	return {
		"found": True,
		"item_code": item.item_code,
		"item_name": item.item_name,
		"uom": item.stock_uom,
		"uoms": [{"uom": u.uom, "conversion_factor": float(u.conversion_factor or 1)} for u in uoms],
		"uom_price_lists": uom_price_lists,
		"rate": float(rate),
		"stock_qty": float(stock_qty),
		"warehouse": wh,
		"tax_rate": _get_item_tax_rate(item.item_code),
	}


@frappe.whitelist()
def search_items(query, price_list="Standard Selling"):
	"""Search items by code, name, or barcode. Returns list of matches."""
	if not query or len(query) < 1:
		return []

	barcode_item = frappe.db.get_value("Item Barcode", {"barcode": query}, "parent")
	if barcode_item:
		return [get_item_details(barcode_item, price_list)]

	items = frappe.get_all(
		"Item",
		or_filters={
			"item_code": ["like", f"%{query}%"],
			"item_name": ["like", f"%{query}%"],
		},
		filters={"disabled": 0, "is_sales_item": 1},
		fields=["item_code", "item_name", "stock_uom as uom", "standard_rate"],
		limit=20,
		order_by="item_name asc",
	)

	wh = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
	for item in items:
		item["rate"] = float(
			frappe.db.get_value(
				"Item Price",
				{"item_code": item["item_code"], "price_list": price_list, "selling": 1},
				"price_list_rate",
			)
			or item.get("standard_rate")
			or 0
		)
		item["stock_qty"] = float(
			frappe.db.get_value("Bin", {"item_code": item["item_code"], "warehouse": wh}, "actual_qty")
			or 0
		) if wh else 0
		item["warehouse"] = wh
		item["found"] = True
		item["tax_rate"] = _get_item_tax_rate(item["item_code"])

	return items


@frappe.whitelist()
def get_item_insight(item_code, price_list="Standard Selling", warehouse=None):
	"""Return stock across all warehouses + selling price lists + previous quotations."""
	if not item_code or not frappe.db.exists("Item", item_code):
		return {}

	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code},
		fields=["warehouse", "actual_qty"],
		order_by="actual_qty desc",
	)

	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "selling": 1},
		fields=["price_list", "price_list_rate as rate"],
		order_by="price_list",
	)

	prev_quotes = frappe.db.sql(
		"""
		SELECT
			qi.parent AS name,
			q.transaction_date AS date,
			qi.rate,
			qi.qty,
			qi.discount_percentage AS discount
		FROM `tabQuotation Item` qi
		JOIN `tabQuotation` q ON q.name = qi.parent
		WHERE qi.item_code = %(item_code)s
		  AND q.docstatus = 1
		ORDER BY q.transaction_date DESC
		LIMIT 10
		""",
		{"item_code": item_code},
		as_dict=True,
	)

	return {
		"item_code": item_code,
		"stock": [{"warehouse": b.warehouse, "actual_qty": float(b.actual_qty or 0)} for b in bins],
		"priceLists": [{"name": p.price_list, "rate": float(p.rate or 0)} for p in prices],
		"previousPurchases": [
			{
				"name": p.name,
				"date": str(p.date or ""),
				"rate": float(p.rate or 0),
				"qty": float(p.qty or 0),
				"discount": float(p.discount or 0),
			}
			for p in prev_quotes
		],
	}


# ──────────────────────────────────────────────────────────────────────────────
# Naming series
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_naming_series():
	"""Return available naming series for Quotation."""
	try:
		prop_value = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Quotation", "field_name": "naming_series", "property": "options"},
			"value",
		)
		if prop_value:
			series = [s.strip() for s in prop_value.split("\n") if s.strip()]
			if series:
				return series
	except Exception:
		pass
	try:
		meta = frappe.get_meta("Quotation")
		field = next((f for f in meta.fields if f.fieldname == "naming_series"), None)
		if field and field.options:
			return [s.strip() for s in field.options.strip().split("\n") if s.strip()]
	except Exception:
		pass
	return ["SSPL-QT-.YYYY.-"]


@frappe.whitelist()
def get_next_quotation_no(naming_series):
	"""Preview the next Quotation number for a given series."""
	try:
		return parse_naming_series(naming_series)
	except Exception:
		return naming_series + "???"


# ──────────────────────────────────────────────────────────────────────────────
# List / fetch
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_quotations(query="", limit=50, transaction_date=None, show_submitted=False):
	"""Return list of Quotations for the sidebar."""
	filters = {"quotation_to": "Customer"}
	if transaction_date:
		filters["transaction_date"] = transaction_date
	if not (frappe.parse_json(show_submitted) if isinstance(show_submitted, str) else show_submitted):
		filters["docstatus"] = 0

	or_filters = None
	if query:
		import re
		flexible_query = "%" + "%".join(re.findall(r'[A-Za-z]+|\d+', query)) + "%"
		or_filters = [
			["Quotation", "name", "like", flexible_query],
			["Quotation", "party_name", "like", f"%{query}%"],
			["Quotation", "customer_name", "like", f"%{query}%"],
		]

	quotes = frappe.get_all(
		"Quotation",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "party_name", "customer_name", "grand_total", "status", "docstatus", "transaction_date"],
		order_by="name desc",
		limit_page_length=int(limit),
	)

	return [
		{
			"name": q.name,
			"customer": q.party_name,
			"customer_name": q.customer_name or q.party_name,
			"grand_total": float(q.grand_total or 0),
			"status": q.status or ("Draft" if q.docstatus == 0 else "Submitted"),
			"docstatus": q.docstatus,
		}
		for q in quotes
	]


@frappe.whitelist()
def get_quotation(quotation_name):
	"""Return a single Quotation with its items."""
	if not frappe.db.exists("Quotation", quotation_name):
		frappe.throw(f"Quotation {quotation_name} not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	cost_center = getattr(qt, "cost_center", "") or ""

	def _actual_charge(keyword):
		for t in (qt.taxes or []):
			if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
				return float(t.tax_amount or 0)
		return 0.0

	items = []
	for i in qt.items:
		items.append({
			"item_code": i.item_code,
			"item_name": i.item_name,
			"uom": i.uom or i.stock_uom,
			"qty": float(i.qty or 0),
			"price_list_rate": float(i.price_list_rate or i.rate or 0),
			"rate": float(i.rate or 0),
			"discount": float(i.discount_percentage or 0),
			"tax_rate": _get_item_tax_rate(i.item_code),
			"deleted": False,
		})

	is_inclusive = 0
	if qt.taxes:
		if any(t.included_in_print_rate for t in qt.taxes):
			is_inclusive = 1

	# Fetch state from billing address
	party_state = ""
	if qt.customer_address:
		party_state = frappe.db.get_value("Address", qt.customer_address, "state") or ""

	return {
		"name": qt.name,
		"customer": qt.party_name,
		"customer_name": qt.customer_name,
		"state": party_state,
		"naming_series": qt.naming_series,
		"transaction_date": str(qt.transaction_date or ""),
		"valid_till": str(qt.valid_till or ""),
		"discount_percentage": float(qt.additional_discount_percentage or 0),
		"additional_discount_amount": float(qt.discount_amount or 0),
		"freight_amount": _actual_charge("freight"),
		"packing_amount": _actual_charge("packing"),
		"loading_amount": _actual_charge("loading"),
		"other_charges_amount": _actual_charge("other"),
		"tax_template": qt.taxes_and_charges or "",
		"is_inclusive": is_inclusive,
		"cost_center": cost_center or "",
		"price_list": qt.selling_price_list or "",
		"docstatus": qt.docstatus,
		"status": qt.status,
		"custom_customer_name": qt.custom_customer_name or "",
		"custom_address_line1": qt.custom_address_line1 or "",
		"custom_address_line2": qt.custom_address_line2 or "",
		"custom_mobile_number": qt.custom_mobile_number or "",
		"custom_half_tax_discount": qt.custom_half_tax_discount or 0,
		"items": items,
	}


# ──────────────────────────────────────────────────────────────────────────────
# Create / Update
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_quotation(data):
	"""Create a new draft Quotation."""
	if isinstance(data, str):
		data = json.loads(data)

	qt = frappe.new_doc("Quotation")
	qt.naming_series = data.get("naming_series", "SSPL-QT-.YYYY.-")
	qt.quotation_to = "Customer"
	qt.party_name = data["customer"]
	if data.get("customer_address"):
		qt.customer_address = data["customer_address"]
	qt.transaction_date = data.get("date") or frappe.utils.today()
	if data.get("valid_till"):
		qt.valid_till = data["valid_till"]

	if data.get("price_list"):
		qt.selling_price_list = data["price_list"]
	if data.get("tax_template"):
		qt.taxes_and_charges = data["tax_template"]
		qt.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in qt.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1

	if data.get("discount_percentage"):
		qt.additional_discount_percentage = data["discount_percentage"]
	if data.get("additional_discount_amount"):
		qt.discount_amount = data["additional_discount_amount"]

	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			qt.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	for i in data.get("items", []):
		row = {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
		}
		if frappe.get_meta("Quotation Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		qt.append("items", row)

	qt.custom_customer_name = data.get("custom_customer_name") or ""
	qt.custom_address_line1 = data.get("custom_address_line1") or ""
	qt.custom_address_line2 = data.get("custom_address_line2") or ""
	qt.custom_mobile_number = data.get("custom_mobile_number") or ""
	qt.custom_half_tax_discount = 1 if data.get("custom_half_tax_discount") else 0

	qt.flags.ignore_permissions = True
	qt.save()

	return {"quotation_name": qt.name}


@frappe.whitelist()
def update_quotation(data):
	"""Update an existing draft Quotation."""
	if isinstance(data, str):
		data = json.loads(data)

	quotation_name = data.get("quotation_name")
	if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
		frappe.throw("Quotation not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	if qt.docstatus != 0:
		frappe.throw("Cannot edit a submitted or cancelled Quotation")

	if qt.party_name != data["customer"]:
		qt.party_name = data["customer"]
		qt.customer_address = data.get("customer_address")
		qt.shipping_address_name = None
		qt.contact_person = None
		qt.contact_display = None
		qt.contact_mobile = None
		qt.contact_email = None
		qt.address_display = None
	elif data.get("customer_address"):
		qt.customer_address = data["customer_address"]

	qt.transaction_date = data.get("date") or qt.transaction_date
	if data.get("valid_till"):
		qt.valid_till = data["valid_till"]
	if data.get("price_list"):
		qt.selling_price_list = data["price_list"]
	if data.get("tax_template"):
		qt.taxes_and_charges = data["tax_template"]
	elif "tax_template" in data:
		qt.taxes_and_charges = ""
	qt.additional_discount_percentage = data.get("discount_percentage", 0)
	qt.discount_amount = data.get("additional_discount_amount", 0)

	if data.get("tax_template"):
		qt.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in qt.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1
	else:
		qt.taxes = []
	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			qt.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	qt.items = []
	for i in data.get("items", []):
		row = {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
		}
		if frappe.get_meta("Quotation Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		qt.append("items", row)

	qt.custom_customer_name = data.get("custom_customer_name") or ""
	qt.custom_address_line1 = data.get("custom_address_line1") or ""
	qt.custom_address_line2 = data.get("custom_address_line2") or ""
	qt.custom_mobile_number = data.get("custom_mobile_number") or ""
	qt.custom_half_tax_discount = 1 if data.get("custom_half_tax_discount") else 0

	qt.flags.ignore_permissions = True
	qt.save()

	return {"quotation_name": qt.name}

@frappe.whitelist()
def submit_quotation(quotation_name):
	"""Submit a draft Quotation (docstatus 0 → 1)."""
	if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
		frappe.throw("Quotation not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	if qt.docstatus != 0:
		frappe.throw("Quotation is already submitted or cancelled")

	qt.flags.ignore_permissions = True
	qt.submit()

	return {"quotation_name": qt.name, "docstatus": qt.docstatus}

@frappe.whitelist()
def delete_quotation(quotation_name):
	"""Delete a Draft Quotation."""
	frappe.delete_doc("Quotation", quotation_name)
	return {"status": "Deleted"}
