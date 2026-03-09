import json
import frappe


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
        stock_qty = (
            frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty")
            or 0
        )

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
def get_item_insight(item_code, customer=None, warehouse=None, price_list=None):
    """Get stock across warehouses, last purchase by customer, all price list rates."""
    wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
    item_info = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True) or {}

    stock = frappe.get_all(
        "Bin",
        filters={"item_code": item_code},
        fields=["warehouse", "actual_qty", "reserved_qty", "projected_qty"],
    )
    for s in stock:
        s["actual_qty"] = float(s["actual_qty"] or 0)
        s["reserved_qty"] = float(s["reserved_qty"] or 0)

    previous_purchases = []
    if customer:
        rows = frappe.db.sql(
            """
            SELECT si.name, si.posting_date as date, sii.rate, sii.qty, sii.discount_percentage as discount
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s AND si.customer = %s AND si.docstatus = 1
            ORDER BY si.posting_date DESC, si.creation DESC
            LIMIT 5
            """,
            (item_code, customer),
            as_dict=True,
        )
        for r in rows:
            previous_purchases.append({
                "name": r.name,
                "date": str(r.date),
                "rate": float(r.rate),
                "qty": float(r.qty),
                "discount": float(r.discount or 0),
            })

    price_lists = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "selling": 1},
        fields=["price_list as name", "price_list_rate as rate", "currency"],
        order_by="price_list_rate asc",
    )
    for pl in price_lists:
        pl["rate"] = float(pl["rate"] or 0)

    return {
        "item_name": item_info.get("item_name"),
        "uom": item_info.get("stock_uom"),
        "stock": stock,
        "previous_purchases": previous_purchases,
        "price_lists": price_lists,
    }


@frappe.whitelist()
def create_sales_invoice(data=None, **kwargs):
    """Create Sales Invoice in Draft."""
    if not data:
        data = frappe.form_dict.get("data")
    if not data:
        fd = dict(frappe.form_dict)
        fd.pop("cmd", None)
        if fd.get("customer"):
            data = fd
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("customer"):
        frappe.throw("Customer is required")
    if not data.get("items"):
        frappe.throw("At least one item is required")

    si = frappe.new_doc("Sales Invoice")
    si.customer = data["customer"]
    si.posting_date = data.get("date", frappe.utils.today())
    si.naming_series = data.get("naming_series", "SINV-.YY.-")
    si.update_stock = 1
    if data.get("cost_center"):
        si.cost_center = data["cost_center"]

    if data.get("discount_percentage"):
        si.additional_discount_percentage = float(data["discount_percentage"])

    for item in data["items"]:
        disc = float(item.get("discount_percentage") or 0)
        price_list_rate = float(item.get("price_list_rate") or item["rate"])
        rate = float(item["rate"]) if not disc else round(price_list_rate * (1 - disc / 100), 9)
        row = {
            "item_code": item["item_code"],
            "qty": float(item["qty"]),
            "price_list_rate": price_list_rate,
            "discount_percentage": disc,
            "rate": rate,
        }
        if item.get("warehouse"):
            row["warehouse"] = item["warehouse"]
        cost_center = item.get("cost_center") or data.get("cost_center") or ""
        if cost_center:
            row["cost_center"] = cost_center
        si.append("items", row)

    if data.get("tax_template"):
        si.taxes_and_charges = data["tax_template"]
        try:
            tmpl = frappe.get_doc("Sales Taxes and Charges Template", data["tax_template"])
            for tax in tmpl.taxes:
                si.append("taxes", {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": tax.rate,
                    "cost_center": data.get("cost_center") or tax.cost_center or "",
                })
        except Exception:
            pass

    si.insert()

    return {
        "invoice_name": si.name,
        "grand_total": float(si.grand_total),
        "status": "Draft",
        "payment_mode": data.get("payment_mode", "Cash"),
    }


@frappe.whitelist()
def get_naming_series(doctypes=None):
    """Get available naming series for specified DocTypes. Defaults to Sales Invoice."""
    if not doctypes:
        doctypes = ["Sales Invoice"]
    if isinstance(doctypes, str):
        if doctypes.startswith("["):
            doctypes = json.loads(doctypes)
        else:
            doctypes = [doctypes]

    def _get_series_for_doctype(doctype):
        try:
            prop_value = frappe.db.get_value(
                "Property Setter",
                {"doc_type": doctype, "field_name": "naming_series", "property": "options"},
                "value",
            )
            if prop_value:
                return [s.strip() for s in prop_value.split("\n") if s.strip()]
        except Exception:
            pass
        try:
            meta = frappe.get_meta(doctype)
            sf = meta.get_field("naming_series")
            if sf and sf.options:
                return [s.strip() for s in sf.options.split("\n") if s.strip()]
        except Exception:
            pass
        return []

    all_series = []
    for dt in doctypes:
        all_series.extend(_get_series_for_doctype(dt))

    # Return unique sorted series. Fallback if none found.
    result = sorted(list(set(all_series)))
    return result if result else ["SINV-.YY.-"]


@frappe.whitelist()
def get_next_bill_no(naming_series="SINV-.YY.-"):
    """Get the next number in the naming series."""
    try:
        from frappe.model.naming import parse_naming_series
        return parse_naming_series(naming_series)
    except Exception:
        return naming_series + "???"


@frappe.whitelist()
def update_sales_invoice(data=None, **kwargs):
    """Update an existing Draft Sales Invoice."""
    if not data: data = frappe.form_dict.get("data")
    if isinstance(data, str): data = json.loads(data)

    invoice_name = data.get("invoice_name")
    si = frappe.get_doc("Sales Invoice", invoice_name)
    si.customer = data["customer"]
    si.posting_date = data.get("date", frappe.utils.today())
    si.additional_discount_percentage = float(data.get("discount_percentage", 0))
    si.items = []
    for item in data["items"]:
        si.append("items", {"item_code": item["item_code"], "qty": float(item["qty"]), "rate": float(item["rate"]), "warehouse": item.get("warehouse")})
    si.save()
    return {"invoice_name": si.name, "grand_total": float(si.grand_total)}
