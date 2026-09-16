"""Website customer catalogue pricing and draft Sales Order checkout."""

import json

import frappe
from frappe.utils import add_days, flt, today

from ssplbilling.api.offer_api import get_offer_details


def _customer_context():
	user = frappe.session.user
	if user == "Guest" or frappe.get_cached_value("User", user, "user_type") != "Website User":
		frappe.throw("Sign in as a Website User to order.", frappe.PermissionError)

	permissions = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Customer"},
		fields=["for_value", "applicable_for"],
	)
	customers = {p.for_value for p in permissions if not p.applicable_for}
	if len(customers) > 1:
		frappe.throw("Your account is linked to multiple Customers. Contact an administrator.", frappe.PermissionError)
	customer_name = next(iter(customers), None)

	links = frappe.get_all(
		"Portal User",
		filters={"user": user, "parenttype": "Customer", "parentfield": "portal_users"},
		fields=["parent"],
		order_by="creation asc",
		limit=1,
	)
	customer_name = customer_name or (links[0].parent if links else None)
	if not customer_name:
		contacts = frappe.get_all(
			"Contact Email", filters={"email_id": user}, fields=["parent"], limit=20
		)
		for contact in contacts:
			customer_name = frappe.db.get_value(
				"Dynamic Link",
				{"parenttype": "Contact", "parent": contact.parent, "link_doctype": "Customer"},
				"link_name",
			)
			if customer_name:
				break
	if not customer_name:
		frappe.throw("Your account is not linked to a Customer.")

	customer = frappe.db.get_value(
		"Customer", customer_name, ["customer_name", "default_price_list", "disabled"], as_dict=True
	)
	if not customer or customer.disabled:
		frappe.throw("The linked Customer is unavailable.")
	if not customer.default_price_list:
		frappe.throw("Set a default price list on the linked Customer before ordering.")

	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	series = settings.billing_series[0].series if settings.billing_series else None
	if not series:
		frappe.throw("Set the first Billing Series before ordering.")

	return {
		"customer": customer_name,
		"customer_name": customer.customer_name,
		"price_list": customer.default_price_list,
		"naming_series": series,
	}


def _order_price(item_code, price_list, barcode=None):
	item = frappe.get_cached_doc("Item", item_code)
	if item.disabled or not item.is_sales_item:
		return item, item.stock_uom, None

	barcode_uom = None
	if barcode:
		barcode_uom = frappe.db.get_value(
			"Item Barcode", {"parent": item_code, "barcode": barcode}, "uom"
		)
	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "price_list": price_list, "selling": 1},
		fields=["uom", "price_list_rate"],
	)
	for uom in (barcode_uom, item.stock_uom, None, ""):
		for price in prices:
			if (price.uom or None) == (uom or None):
				return item, price.uom or item.stock_uom, flt(price.price_list_rate)
	if len(prices) == 1:
		return item, prices[0].uom or item.stock_uom, flt(prices[0].price_list_rate)
	return item, item.stock_uom, None


@frappe.whitelist()
def get_customer_offer(pageaddress):
	context = _customer_context()
	offer = get_offer_details(pageaddress)
	if not offer:
		return None

	price_list = context["price_list"]
	offer["price_lists"] = [{"price_list": price_list}]
	for row in offer["items"]:
		_, row["order_uom"], row["order_rate"] = _order_price(
			row["itemcode"], price_list, row.get("barcode")
		)
		row["prices"] = ([{"price_list": price_list, "rate": row["order_rate"]}]
			if row["order_rate"] is not None else [])
		for barcode in row["barcode_prices"]:
			_, _, rate = _order_price(row["itemcode"], price_list, barcode.get("barcode"))
			barcode["prices"] = {price_list: rate}
	return {"offer": offer, "customer": context["customer"], "price_list": price_list}


def _preview(items):
	context = _customer_context()
	if isinstance(items, str):
		try:
			items = json.loads(items)
		except (TypeError, ValueError):
			frappe.throw("Invalid cart.")
	if not isinstance(items, list) or not items or len(items) > 100:
		frappe.throw("Cart must contain 1 to 100 items.")

	lines = []
	seen = set()
	for entry in items:
		if not isinstance(entry, dict):
			frappe.throw("Invalid cart item.")
		pageaddress = entry.get("pageaddress")
		item_code = entry.get("item_code")
		qty = entry.get("qty")
		if not isinstance(pageaddress, str) or not isinstance(item_code, str) or not pageaddress or not item_code:
			frappe.throw("Invalid cart item.")
		if isinstance(qty, bool) or not isinstance(qty, int) or not 1 <= qty <= 10000:
			frappe.throw("Quantity must be a whole number from 1 to 10000.")
		key = (pageaddress, item_code)
		if key in seen:
			frappe.throw("Cart contains a duplicate item.")
		seen.add(key)

		offer_name = frappe.db.get_value("Offer-Items", {"pageaddress": pageaddress}, "name")
		if not offer_name:
			frappe.throw(f"Catalogue for {item_code} is unavailable.")
		offer_item = frappe.db.get_value(
			"Offer-Item",
			{"parent": offer_name, "parenttype": "Offer-Items", "parentfield": "items", "itemcode": item_code, "disabled": 0},
			["barcode"], as_dict=True,
		)
		if not offer_item:
			frappe.throw(f"{item_code} is no longer in the catalogue.")
		item, uom, rate = _order_price(item_code, context["price_list"], offer_item.barcode)
		if rate is None:
			frappe.throw(f"{item_code} is unavailable in {context['price_list']}.")
		lines.append({
			"pageaddress": pageaddress,
			"item_code": item_code,
			"item_name": item.item_name,
			"image": item.image,
			"qty": qty,
			"uom": uom,
			"rate": rate,
			"amount": flt(qty * rate),
		})

	return {
		**context,
		"items": lines,
		"total": flt(sum(line["amount"] for line in lines)),
	}


@frappe.whitelist()
def get_cart_preview(items):
	return _preview(items)


@frappe.whitelist()
def place_order(items):
	preview = _preview(items)
	company = frappe.defaults.get_global_default("company")
	if not company:
		frappe.throw("Set a default company before ordering.")

	order = frappe.new_doc("Sales Order")
	order.company = company
	order.naming_series = preview["naming_series"]
	order.customer = preview["customer"]
	order.selling_price_list = preview["price_list"]
	order.transaction_date = today()
	order.delivery_date = add_days(today(), 7)
	order.order_type = "Sales"
	order.ignore_pricing_rule = 1
	for line in preview["items"]:
		order.append("items", {
			"item_code": line["item_code"],
			"qty": line["qty"],
			"uom": line["uom"],
			"rate": line["rate"],
			"price_list_rate": line["rate"],
			"delivery_date": order.delivery_date,
		})
	order.insert(ignore_permissions=True)
	return {"order_name": order.name, "total": flt(order.grand_total)}
