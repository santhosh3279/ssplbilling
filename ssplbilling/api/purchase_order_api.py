import json
import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows


# ──────────────────────────────────────────────────────────────────────────────
# Item helpers (reuse purchase logic)
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
def get_item_details(item_code, price_list="Standard Buying", warehouse=None):
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
		{"item_code": item_code, "price_list": price_list, "buying": 1},
		"price_list_rate",
	) or item.last_purchase_rate or 0

	# Fetch UOM conversions
	uoms = frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": item_code},
		fields=["uom", "conversion_factor"],
	)

	stock_qty = 0
	if wh:
		stock_qty = (
			frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty")
			or 0
		)

	return {
		"found": True,
		"item_code": item.item_code,
		"item_name": item.item_name,
		"uom": item.stock_uom,
		"uoms": [{"uom": u.uom, "conversion_factor": float(u.conversion_factor or 1)} for u in uoms],
		"rate": float(rate),
		"stock_qty": float(stock_qty),
		"warehouse": wh,
		"tax_rate": _get_item_tax_rate(item.item_code),
	}


@frappe.whitelist()
def get_item_insight(item_code, price_list="Standard Buying", warehouse=None):
	"""Return stock across all warehouses + price lists + previous purchase orders."""
	if not item_code or not frappe.db.exists("Item", item_code):
		return {}

	wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code},
		fields=["warehouse", "actual_qty"],
		order_by="actual_qty desc",
	)

	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "buying": 1},
		fields=["price_list", "price_list_rate as rate"],
		order_by="price_list",
	)

	prev_orders = frappe.db.sql(
		"""
		SELECT
			poi.parent AS name,
			po.transaction_date AS date,
			poi.rate,
			poi.qty,
			poi.discount_percentage AS discount
		FROM `tabPurchase Order Item` poi
		JOIN `tabPurchase Order` po ON po.name = poi.parent
		WHERE poi.item_code = %(item_code)s
		  AND po.docstatus = 1
		ORDER BY po.transaction_date DESC
		LIMIT 10
		""",
		{"item_code": item_code},
		as_dict=True,
	)

	return {
		"item_code": item_code,
		"stock": [
			{"warehouse": b.warehouse, "actual_qty": float(b.actual_qty or 0)}
			for b in bins
		],
		"priceLists": [
			{"name": p.price_list, "rate": float(p.rate or 0)}
			for p in prices
		],
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
	"""Return available naming series for Purchase Order."""
	meta = frappe.get_meta("Purchase Order")
	field = next((f for f in meta.fields if f.fieldname == "naming_series"), None)
	if field and field.options:
		return [s.strip() for s in field.options.strip().split("\n") if s.strip()]
	return ["PO-.YYYY.-"]


@frappe.whitelist()
def get_next_bill_no(naming_series):
	"""Return the next Purchase Order number for the given series."""
	if not naming_series:
		return ""
	try:
		from frappe.model.naming import make_autoname
		return make_autoname(naming_series.replace(".####", ".{####}"), "Purchase Order")
	except Exception:
		return ""


# ──────────────────────────────────────────────────────────────────────────────
# List / fetch
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_orders(query="", limit=50, transaction_date=None, show_submitted=False):
	"""Return list of Purchase Orders for the sidebar."""
	filters = {}
	if transaction_date:
		filters["transaction_date"] = transaction_date
	if not show_submitted:
		filters["docstatus"] = 0

	or_filters = None
	if query:
		or_filters = [
			["Purchase Order", "name", "like", f"%{query}%"],
			["Purchase Order", "supplier_name", "like", f"%{query}%"],
			["Purchase Order", "supplier", "like", f"%{query}%"],
		]

	orders = frappe.get_all(
		"Purchase Order",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "supplier", "supplier_name", "grand_total", "status", "docstatus", "transaction_date"],
		order_by="modified desc",
		limit_page_length=int(limit),
	)

	return [
		{
			"name": o.name,
			"supplier": o.supplier,
			"supplier_name": o.supplier_name or o.supplier,
			"grand_total": float(o.grand_total or 0),
			"status": o.status or ("Draft" if o.docstatus == 0 else "Submitted"),
			"docstatus": o.docstatus,
		}
		for o in orders
	]


@frappe.whitelist()
def get_purchase_order(order_name):
	"""Return a single Purchase Order with its items."""
	if not frappe.db.exists("Purchase Order", order_name):
		frappe.throw(f"Purchase Order {order_name} not found")

	po = frappe.get_doc("Purchase Order", order_name)

	items = []
	for i in po.items:
		uoms = frappe.get_all(
			"UOM Conversion Detail",
			filters={"parent": i.item_code},
			fields=["uom", "conversion_factor"],
		)
		items.append({
			"item_code": i.item_code,
			"item_name": i.item_name,
			"uom": i.uom or i.stock_uom,
			"uoms": [{"uom": u.uom, "conversion_factor": float(u.conversion_factor or 1)} for u in uoms],
			"qty": float(i.qty or 0),
			"rate": float(i.rate or 0),
			"discount": float(i.discount_percentage or 0),
			"tax_rate": 0.0,
			"warehouse": i.warehouse or "",
			"deleted": False,
		})

	return {
		"name": po.name,
		"supplier": po.supplier,
		"supplier_name": po.supplier_name,
		"naming_series": po.naming_series,
		"transaction_date": str(po.transaction_date or ""),
		"schedule_date": str(po.schedule_date or ""),
		"discount_percentage": float(po.additional_discount_percentage or 0),
		"additional_discount_amount": float(po.discount_amount or 0),
		"freight_amount": 0.0,
		"loading_amount": 0.0,
		"docstatus": po.docstatus,
		"items": items,
	}


# ──────────────────────────────────────────────────────────────────────────────
# Create / Update
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_purchase_order(data):
	"""Create a new Purchase Order (draft)."""
	if isinstance(data, str):
		data = json.loads(data)

	po = frappe.new_doc("Purchase Order")
	po.naming_series = data.get("naming_series", "PO-.YYYY.-")
	po.supplier = data["supplier"]
	po.transaction_date = data.get("date") or frappe.utils.today()
	po.schedule_date = data.get("schedule_date") or frappe.utils.add_days(frappe.utils.today(), 7)

	if data.get("discount_percentage"):
		po.additional_discount_percentage = data["discount_percentage"]
	if data.get("additional_discount_amount"):
		po.discount_amount = data["additional_discount_amount"]

	# Taxes / charges
	if data.get("tax_template"):
		po.taxes_and_charges = data["tax_template"]
		po.set("taxes", _erpnext_tax_rows("Purchase Taxes and Charges Template", data["tax_template"]) or [])
	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			po.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	for i in data.get("items", []):
		po.append("items", {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
			"warehouse": i.get("warehouse", ""),
			"schedule_date": data.get("schedule_date") or frappe.utils.add_days(frappe.utils.today(), 7),
		})

	po.flags.ignore_permissions = True
	po.save()

	return {"order_name": po.name}


@frappe.whitelist()
def update_purchase_order(data):
	"""Update an existing draft Purchase Order."""
	if isinstance(data, str):
		data = json.loads(data)

	order_name = data.get("order_name")
	if not order_name or not frappe.db.exists("Purchase Order", order_name):
		frappe.throw("Purchase Order not found")

	po = frappe.get_doc("Purchase Order", order_name)
	if po.docstatus != 0:
		frappe.throw("Cannot edit a submitted or cancelled Purchase Order")

	po.supplier = data["supplier"]
	po.transaction_date = data.get("date") or po.transaction_date
	if data.get("schedule_date"):
		po.schedule_date = data["schedule_date"]
	po.additional_discount_percentage = data.get("discount_percentage", 0)
	po.discount_amount = data.get("additional_discount_amount", 0)
	if data.get("tax_template"):
		po.taxes_and_charges = data["tax_template"]
	elif "tax_template" in data:
		po.taxes_and_charges = ""

	if data.get("tax_template"):
		po.set("taxes", _erpnext_tax_rows("Purchase Taxes and Charges Template", data["tax_template"]) or [])
	else:
		po.taxes = []
	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			po.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	po.items = []
	for i in data.get("items", []):
		po.append("items", {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
			"warehouse": i.get("warehouse", ""),
			"schedule_date": data.get("schedule_date") or frappe.utils.add_days(frappe.utils.today(), 7),
		})

	po.flags.ignore_permissions = True
	po.save()

	return {"order_name": po.name}

@frappe.whitelist()
def submit_purchase_order(order_name):
	"""Submit a Draft Purchase Order."""
	if not order_name:
		frappe.throw("Order Name is required")
	po = frappe.get_doc("Purchase Order", order_name)
	if po.docstatus != 0:
		frappe.throw(f"Purchase Order {order_name} is not in Draft state")
	po.flags.ignore_permissions = True
	po.submit()
	return {"order_name": po.name, "docstatus": po.docstatus}
