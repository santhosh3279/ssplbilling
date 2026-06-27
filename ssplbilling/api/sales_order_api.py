import json
import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows
from ssplbilling.api.stock_utils import get_draft_invoice_qty


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
		{"item_code": item_code, "price_list": price_list, "selling": 1},
		"price_list_rate",
	) or item.standard_rate or 0

	stock_qty = 0
	if wh:
		stock_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty") or 0
		stock_qty = float(stock_qty) - get_draft_invoice_qty(item_code, wh)

	return {
		"found": True,
		"item_code": item.item_code,
		"item_name": item.item_name,
		"uom": item.stock_uom,
		"rate": float(rate),
		"stock_qty": float(stock_qty),
		"warehouse": wh,
		"tax_rate": _get_item_tax_rate(item.item_code),
	}


@frappe.whitelist()
def get_item_insight(item_code, price_list="Standard Selling", warehouse=None):
	"""Return stock across all warehouses + selling price lists + previous sales orders."""
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

	prev_orders = frappe.db.sql(
		"""
		SELECT
			soi.parent AS name,
			so.transaction_date AS date,
			soi.rate,
			soi.qty,
			soi.discount_percentage AS discount
		FROM `tabSales Order Item` soi
		JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE soi.item_code = %(item_code)s
		  AND so.docstatus = 1
		ORDER BY so.transaction_date DESC
		LIMIT 10
		""",
		{"item_code": item_code},
		as_dict=True,
	)

	return {
		"item_code": item_code,
		"stock": [{"warehouse": b.warehouse, "actual_qty": float(b.actual_qty or 0) - get_draft_invoice_qty(item_code, b.warehouse)} for b in bins],
		"priceLists": [{"name": p.price_list, "rate": float(p.rate or 0)} for p in prices],
		"previousPurchases": [
			{
				"name": p.name,
				"date": str(p.date or ""),
				"rate": float(p.rate or 0),
				"qty": float(p.qty or 0),
				"discount": float(p.discount or 0),
			}
			for p in prev_orders
		],
	}


# ──────────────────────────────────────────────────────────────────────────────
# Naming series
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_naming_series():
	"""Return available naming series for Sales Order."""
	try:
		prop_value = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Sales Order", "field_name": "naming_series", "property": "options"},
			"value",
		)
		if prop_value:
			series = [s.strip() for s in prop_value.split("\n") if s.strip()]
			if series:
				return series
	except Exception:
		pass
	try:
		meta = frappe.get_meta("Sales Order")
		field = next((f for f in meta.fields if f.fieldname == "naming_series"), None)
		if field and field.options:
			return [s.strip() for s in field.options.strip().split("\n") if s.strip()]
	except Exception:
		pass
	return ["SSPL-SO-.YYYY.-"]


@frappe.whitelist()
def get_next_order_no(naming_series):
	"""Preview the next Sales Order number for a given series."""
	if not naming_series:
		return ""
	try:
		from frappe.model.naming import make_autoname
		return make_autoname(naming_series.replace(".####", ".{####}"), "Sales Order")
	except Exception:
		return ""


# ──────────────────────────────────────────────────────────────────────────────
# List / fetch
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_orders(query="", limit=50, transaction_date=None, show_submitted=False):
	"""Return list of Sales Orders for the sidebar."""
	filters = {}
	if transaction_date:
		filters["transaction_date"] = transaction_date
	if not frappe.parse_json(show_submitted) if isinstance(show_submitted, str) else not show_submitted:
		filters["docstatus"] = 0

	or_filters = None
	if query:
		or_filters = [
			["Sales Order", "name", "like", f"%{query}%"],
			["Sales Order", "customer_name", "like", f"%{query}%"],
			["Sales Order", "customer", "like", f"%{query}%"],
		]

	orders = frappe.get_all(
		"Sales Order",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "customer", "customer_name", "grand_total", "rounded_total", "status", "docstatus", "transaction_date"],
		order_by="modified desc",
		limit_page_length=int(limit),
	)

	return [
		{
			"name": o.name,
			"customer": o.customer,
			"customer_name": o.customer_name or o.customer,
			"grand_total": float(o.grand_total or 0),
			"rounded_total": float(o.rounded_total or o.grand_total or 0),
			"status": o.status or ("Draft" if o.docstatus == 0 else "Submitted"),
			"docstatus": o.docstatus,
		}
		for o in orders
	]


@frappe.whitelist()
def get_sales_order(order_name):
	"""Return a single Sales Order with its items and taxes."""
	if not frappe.db.exists("Sales Order", order_name):
		frappe.throw(f"Sales Order {order_name} not found")

	so = frappe.get_doc("Sales Order", order_name)
	cost_center = so.items[0].cost_center if so.items else ""

	def _actual_charge(keyword):
		for t in (so.taxes or []):
			if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
				return float(t.tax_amount or 0)
		return 0.0

	items = []
	for i in so.items:
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
	if so.taxes:
		if any(t.included_in_print_rate for t in so.taxes):
			is_inclusive = 1

	return {
		"name": so.name,
		"customer": so.customer,
		"customer_name": so.customer_name,
		"naming_series": so.naming_series,
		"transaction_date": str(so.transaction_date or ""),
		"delivery_date": str(so.delivery_date or ""),
		"discount_percentage": float(so.additional_discount_percentage or 0),
		"additional_discount_amount": float(so.discount_amount or 0),
		"freight_amount": _actual_charge("freight"),
		"packing_amount": _actual_charge("packing"),
		"loading_amount": _actual_charge("loading"),
		"other_charges_amount": _actual_charge("other"),
		"tax_template": so.taxes_and_charges or "",
		"is_inclusive": is_inclusive,
		"cost_center": cost_center or "",
		"price_list": so.selling_price_list or "",
		"docstatus": so.docstatus,
		"items": items,
	}


# ──────────────────────────────────────────────────────────────────────────────
# Create / Update
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_sales_order(data):
	"""Create a new draft Sales Order."""
	if isinstance(data, str):
		data = json.loads(data)

	so = frappe.new_doc("Sales Order")
	so.naming_series = data.get("naming_series", "SSPL-SO-.YYYY.-")
	so.customer = data["customer"]
	so.transaction_date = data.get("date") or frappe.utils.today()
	so.delivery_date = data.get("delivery_date") or frappe.utils.add_days(frappe.utils.today(), 7)
	so.order_type = "Sales"

	if data.get("discount_percentage"):
		so.additional_discount_percentage = data["discount_percentage"]
	if data.get("additional_discount_amount"):
		so.discount_amount = data["additional_discount_amount"]
	if data.get("tax_template"):
		so.taxes_and_charges = data["tax_template"]
		so.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in so.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1

	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			so.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	for i in data.get("items", []):
		so.append("items", {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"uom": i.get("uom"),
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
			"delivery_date": data.get("delivery_date") or frappe.utils.add_days(frappe.utils.today(), 7),
		})

	so.flags.ignore_permissions = True
	so.save()

	return {"order_name": so.name}


@frappe.whitelist()
def update_sales_order(data):
	"""Update an existing draft Sales Order."""
	if isinstance(data, str):
		data = json.loads(data)

	order_name = data.get("order_name")
	if not order_name or not frappe.db.exists("Sales Order", order_name):
		frappe.throw("Sales Order not found")

	so = frappe.get_doc("Sales Order", order_name)
	if so.docstatus != 0:
		frappe.throw("Cannot edit a submitted or cancelled Sales Order")

	if so.customer != data["customer"]:
		so.customer = data["customer"]
		so.customer_address = None
		so.shipping_address_name = None
		so.contact_person = None
		so.contact_display = None
		so.contact_mobile = None
		so.contact_email = None
		so.address_display = None

	so.transaction_date = data.get("date") or so.transaction_date
	if data.get("delivery_date"):
		so.delivery_date = data["delivery_date"]
	so.additional_discount_percentage = data.get("discount_percentage", 0)
	so.discount_amount = data.get("additional_discount_amount", 0)
	if data.get("tax_template"):
		so.taxes_and_charges = data["tax_template"]
	elif "tax_template" in data:
		so.taxes_and_charges = ""

	if data.get("tax_template"):
		so.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in so.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1
	else:
		so.taxes = []
	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			so.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	so.items = []
	for i in data.get("items", []):
		so.append("items", {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"uom": i.get("uom"),
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
			"delivery_date": data.get("delivery_date") or frappe.utils.add_days(frappe.utils.today(), 7),
		})

	so.flags.ignore_permissions = True
	so.save()

	return {"order_name": so.name}

@frappe.whitelist()
def submit_sales_order(order_name):
	"""Submit a draft Sales Order (docstatus 0 → 1)."""
	if not order_name or not frappe.db.exists("Sales Order", order_name):
		frappe.throw("Sales Order not found")

	so = frappe.get_doc("Sales Order", order_name)
	if so.docstatus != 0:
		frappe.throw("Sales Order is already submitted or cancelled")

	so.flags.ignore_permissions = True
	so.submit()

	return {"order_name": so.name, "docstatus": so.docstatus}
