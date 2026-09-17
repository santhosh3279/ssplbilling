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

	return {
		"customer": customer_name,
		"customer_name": customer.customer_name,
		"price_list": customer.default_price_list,
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



def _catalogue_rules(price_list):
	"""Read enabled rules under server authority for a website customer."""
	rules = frappe.get_all(
		"Discount Rule", filters={"enabled": 1},
		fields=["name", "rule_name", "price_list", "discount_type", "applies_to",
			"product_group", "min_quantity", "free_quantity", "recursive",
			"percentage_discount", "custom_logic_type", "start_date", "end_date"],
		order_by="rule_name asc", ignore_permissions=True,
	)
	active = []
	current = today()
	for rule in rules:
		if rule.price_list and rule.price_list != price_list:
			continue
		if rule.start_date and str(rule.start_date) > current:
			continue
		if rule.end_date and str(rule.end_date) < current:
			continue
		rule["items"] = frappe.get_all(
			"Discount Rule Item", filters={"parent": rule.name},
			fields=["item_code"], ignore_permissions=True,
		)
		rule["custom_logic_rows"] = frappe.get_all(
			"Discount Rule Custom Logic", filters={"parent": rule.name},
			fields=["min_quantity", "nos", "percentage"], ignore_permissions=True,
		)
		rule["x_to_y_table"] = frappe.get_all(
			"Discount Rule X to Y", filters={"parent": rule.name},
			fields=["item_code", "min_quantity", "free_item_code", "free_item_quantity", "free_item_price"],
			ignore_permissions=True,
		)
		active.append(rule)
	return active


def _apply_catalogue_rules(lines, price_list):
	rules = _catalogue_rules(price_list)
	priced = []
	for line in lines:
		line["requested_qty"] = line["qty"]
		line["discount_percentage"] = 0
		line["is_free_item"] = 0
		priced.append(line)
		for rule in rules:
			matching_x_to_y = next((entry for entry in rule.x_to_y_table
				if entry.item_code.lower() == line["item_code"].lower()), None)
			if rule.discount_type == "X to Y product discount":
				matches = matching_x_to_y is not None
			elif rule.applies_to == "Item Code":
				matches = any(entry.item_code.lower() == line["item_code"].lower() for entry in rule.items)
			elif rule.applies_to == "Product Group":
				matches = line["item_group"] == rule.product_group
			else:
				matches = False
			if not matches:
				continue

			qty = line["requested_qty"]
			kind = rule.discount_type
			if kind == "Product Discount":
				minimum, free = flt(rule.min_quantity), flt(rule.free_quantity)
				pack = minimum + free
				free_qty = (int(qty // pack) * free if rule.recursive else free if qty >= pack else 0) if pack > 0 and minimum > 0 and free > 0 else 0
				if free_qty:
					line["qty"] = qty - free_qty
					line["amount"] = flt(line["qty"] * line["rate"])
					priced.append({**line, "qty": free_qty, "requested_qty": 0, "rate": 0,
						"amount": 0, "discount_percentage": 0, "is_free_item": 1})
			elif kind == "X to Y product discount" and matching_x_to_y:
				minimum = flt(matching_x_to_y.min_quantity) or 1
				free_qty = int(qty // minimum) * flt(matching_x_to_y.free_item_quantity or 1)
				if free_qty > 0 and matching_x_to_y.free_item_code:
					free_item = frappe.get_cached_doc("Item", matching_x_to_y.free_item_code)
					if free_item.disabled or not free_item.is_sales_item:
						frappe.throw(f"Free item {free_item.name} is unavailable.")
					free_rate = flt(matching_x_to_y.free_item_price)
					priced.append({"pageaddress": line["pageaddress"], "item_code": free_item.name,
						"item_name": free_item.item_name, "image": free_item.image, "item_group": free_item.item_group,
						"qty": free_qty, "requested_qty": 0, "uom": free_item.stock_uom,
						"rate": free_rate, "amount": flt(free_qty * free_rate),
						"discount_percentage": 0, "is_free_item": 1})
			elif kind in ("Percentage Discount", "Custom Logic"):
				rows = sorted((row for row in rule.custom_logic_rows if qty >= flt(row.min_quantity)),
					key=lambda row: flt(row.min_quantity), reverse=True)
				if kind == "Custom Logic" and rule.custom_logic_type == "Product":
					free_qty = flt(rows[0].nos) if rows else 0
					if free_qty > 0:
						priced.append({**line, "qty": free_qty, "requested_qty": 0, "rate": 0,
							"amount": 0, "discount_percentage": 0, "is_free_item": 1})
				else:
					percent = (flt(rows[0].percentage) if rows else 0) if kind == "Custom Logic" or rule.custom_logic_rows else (
						flt(rule.percentage_discount) if qty >= flt(rule.min_quantity) else 0)
					line["discount_percentage"] = max(0, min(100, percent))
					line["amount"] = flt(qty * line["rate"] * (1 - line["discount_percentage"] / 100))
			break
	for line in priced:
		line.pop("item_group", None)
	return priced


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
			"item_group": item.item_group,
			"image": item.image,
			"qty": qty,
			"uom": uom,
			"rate": rate,
			"amount": flt(qty * rate),
		})

	priced = _apply_catalogue_rules(lines, context["price_list"])
	subtotal = flt(sum(line["requested_qty"] * line["rate"] for line in priced)
		+ sum(line["amount"] for line in priced if line["is_free_item"] and line["rate"]))
	total = flt(sum(line["amount"] for line in priced))
	return {
		**context,
		"items": priced,
		"subtotal": subtotal,
		"discount_total": flt(subtotal - total),
		"total": total,
	}


@frappe.whitelist()
def get_cart_preview(items):
	return _preview(items)


@frappe.whitelist()
def place_order(items):
	preview = _preview(items)
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	company = settings.online_order_company
	series = settings.online_order_series
	warehouse = settings.online_order_warehouse
	cost_center = settings.online_order_cost_center
	if not all((company, series, warehouse, cost_center)):
		frappe.throw("Complete Company, Sales Order Series, Source Warehouse, and Cost Center in Online Order Settings.")
	if frappe.db.get_value("Warehouse", warehouse, "company") != company or frappe.db.get_value("Warehouse", warehouse, "is_group"):
		frappe.throw("The Online Order Settings warehouse must be a stock warehouse in the selected company.")
	if frappe.db.get_value("Cost Center", cost_center, "company") != company or frappe.db.get_value("Cost Center", cost_center, "is_group"):
		frappe.throw("The Online Order Settings cost center must be a leaf cost center in the selected company.")

	order = frappe.new_doc("Sales Order")
	order.company = company
	order.set_warehouse = warehouse
	order.naming_series = series
	order.cost_center = cost_center
	order.customer = preview["customer"]
	order.selling_price_list = preview["price_list"]
	order.transaction_date = today()
	order.delivery_date = add_days(today(), 7)
	order.order_type = "Sales"
	order.ignore_pricing_rule = 1  # Custom catalogue discounts are applied to each item below.
	for line in preview["items"]:
		order.append("items", {
			"item_code": line["item_code"],
			"warehouse": warehouse,
			"cost_center": cost_center,
			"qty": line["qty"],
			"uom": line["uom"],
			"rate": line["rate"],
			"price_list_rate": line["rate"],
			"discount_percentage": line["discount_percentage"],
			"is_free_item": line["is_free_item"],
			"delivery_date": order.delivery_date,
		})
	# ERPNext validates Item access during Sales Order insertion. The cart and
	# customer were checked above; keep that validation under server authority.
	user = frappe.session.user
	try:
		frappe.set_user("Administrator")
		order.insert(ignore_permissions=True)
	finally:
		frappe.set_user(user)
	frappe.db.set_value("Sales Order", order.name, "owner", user, update_modified=False)
	return {"order_name": order.name, "total": flt(order.grand_total)}
