import json
import frappe
import re

@frappe.whitelist()
def get_allowed_series():
    """Return a list of naming series allowed for the current user.

    Logic:
    1. Read 'SSPL Billing Settings' -> 'user_series' table for the current user.
    2. If no record for the user exists, return all available series (fallback).
    3. Split comma-separated series values and collect prefixes.
    4. If 'ALL' is among the prefixes, return all available series.
    5. Compare alphabetic parts of available series with allowed prefixes.
    """

    def get_alpha(s):
        return re.sub(r"[^A-Za-z]", "", s or "")

    def _fallback_series():
        """Read series from Property Setter or DocType meta as last resort."""
        try:
            prop_value = frappe.db.get_value(
                "Property Setter",
                {"doc_type": "Sales Invoice", "field_name": "naming_series", "property": "options"},
                "value",
            )
            if prop_value:
                series = [s.strip() for s in prop_value.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        try:
            meta = frappe.get_meta("Sales Invoice")
            sf = meta.get_field("naming_series")
            if sf and sf.options:
                series = [s.strip() for s in sf.options.split("\n") if s.strip()]
                if series:
                    return series
        except Exception:
            pass
        return ["SINV-.YY.-"]

    settings = None
    available = []
    user_series_rows = []
    try:
        settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
        available = [r.series for r in settings.billing_series if r.series]
        user_series_rows = list(settings.user_series or [])
    except Exception:
        pass

    # If billing_series table is empty, fall back to ERPNext naming series
    if not available:
        available = _fallback_series()

    user = frappe.session.user

    # Find rows for this user
    user_rows = [r for r in user_series_rows if r.user == user]
    if not user_rows:
        return {"allowed_series": available, "user_allowed_string": ""}  # Fallback: show all

    # Extract and split allowed series prefixes
    allowed_prefixes = []
    for r in user_rows:
        raw = r.allowed_series_seperated_by_comma or ""
        if raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            allowed_prefixes.extend(parts)

    # Check for "ALL"
    if "ALL" in allowed_prefixes:
        return {"allowed_series": available, "user_allowed_string": ",".join(allowed_prefixes)}

    allowed_alphas = [get_alpha(p)[:3] for p in allowed_prefixes]

    # Filter available series by matching alpha parts (up to first 3 chars)
    result = [s for s in available if any(get_alpha(s)[:3].startswith(a) for a in allowed_alphas)]

    return {
        "allowed_series": result if result else available,
        "user_allowed_string": ",".join(allowed_prefixes),
    }

@frappe.whitelist()
def save_default_zoom(zoom):
	"""Persist zoom_value to the current user's row in the user_series child table."""
	user = frappe.session.user
	doc = frappe.get_doc("SSPL Billing Settings", "SSPL Billing Settings")
	user_row = next((r for r in doc.user_series if r.user == user), None)
	if not user_row:
		frappe.throw(f"No user series row found for {user}. Add the user in SSPL Billing Settings first.")
	user_row.zoom_value = str(int(float(zoom)))
	doc.save(ignore_permissions=True)
	frappe.clear_document_cache("SSPL Billing Settings", "SSPL Billing Settings")
	return {"user_zoom": user_row.zoom_value}


@frappe.whitelist()
def get_all_items_detailed(search_type="Sales", price_list=None, warehouse=None):
	"""Fetch all items with price and stock in bulk for local caching."""
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

	# 1. Batch fetch rates
	if not price_list:
		price_list = "Standard Selling" if search_type == "Sales" else "Standard Buying"

	rates = frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", item_codes], "price_list": price_list},
		fields=["item_code", "price_list_rate"],
	)
	for r in rates:
		if r.item_code in item_map:
			item_map[r.item_code]["price"] = float(r.price_list_rate or 0)

	# 2. Batch fetch stock
	stock_filters = {"item_code": ["in", item_codes]}
	if warehouse:
		stock_filters["warehouse"] = warehouse

	bins = frappe.get_all(
		"Bin",
		filters=stock_filters,
		fields=["item_code", "actual_qty"],
	)
	
	# Clear initial stock
	for i in items:
		i["stock"] = 0.0
		if "price" not in i:
			i["price"] = float(i.rate or 0)

	for b in bins:
		if b.item_code in item_map:
			item_map[b.item_code]["stock"] += float(b.actual_qty or 0)

	return items


@frappe.whitelist()
def get_billing_settings():
	"""Return SSPL Billing Settings; user_zoom is resolved for the current user."""
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	user = frappe.session.user
	user_row = next((r for r in settings.user_series if r.user == user), None)
	user_zoom = (user_row.zoom_value or "") if user_row else ""
	return {
		"discount_account": settings.discount_account or "",
		"cipher_map": settings.cipher_map or "",
		"user_zoom": user_zoom,
		"billing_series": [
			{
				"series": r.series or "",
				"price_list": r.price_list or "",
				"warehouse": r.warehouse or "",
				"tax_template": r.tax_template or "",
				"cost_center": r.cost_center or "",
				"print_format": r.print_format or "",
				"cash_account": r.cash_account or "",
				"bank": r.bank or "",
				"upi": r.upi or "",
			}
			for r in settings.billing_series
		],
		"user_series": [
			{
				"user": r.user or "",
				"allowed_series": r.allowed_series_seperated_by_comma or "",
				"zoom_value": r.zoom_value or "",
			}
			for r in settings.user_series
		],
	}
