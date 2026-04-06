import json
import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows


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
        {"item_code": item_code, "price_list": price_list, "buying": 1, "uom": item.stock_uom},
        "price_list_rate",
    ) or frappe.db.get_value(
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

    # Fetch all buying price list rates for this item (including per-UOM)
    all_rates = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "buying": 1},
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
        "uom_price_lists": uom_price_lists,
        "rate": float(rate),
        "stock_qty": float(stock_qty),
        "warehouse": wh,
        "tax_rate": _get_item_tax_rate(item.item_code),
    }


@frappe.whitelist()
def search_items(query, price_list="Standard Buying"):
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
        filters={"disabled": 0, "is_purchase_item": 1},
        fields=["item_code", "item_name", "stock_uom as uom", "last_purchase_rate"],
        limit=20,
        order_by="item_name asc",
    )

    wh = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
    for item in items:
        item["rate"] = float(
            frappe.db.get_value(
                "Item Price",
                {"item_code": item["item_code"], "price_list": price_list, "buying": 1},
                "price_list_rate",
            )
            or item.get("last_purchase_rate")
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
def get_item_insight(item_code, supplier=None, warehouse=None):
    """Get stock across warehouses, last purchase from supplier, all price list rates."""
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
    if supplier:
        rows = frappe.db.sql(
            """
            SELECT pi.name, pi.posting_date as date, pii.rate, pii.qty, pii.discount_percentage as discount
            FROM `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
            WHERE pii.item_code = %s AND pi.supplier = %s AND pi.docstatus = 1
            ORDER BY pi.posting_date DESC, pi.creation DESC
            LIMIT 5
            """,
            (item_code, supplier),
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
        filters={"item_code": item_code, "buying": 1},
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
def create_purchase_invoice(data=None, **kwargs):
    """Create Purchase Invoice in Draft."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("supplier"):
        frappe.throw("Supplier is required")
    if not data.get("items"):
        frappe.throw("At least one item is required")

    pi = frappe.new_doc("Purchase Invoice")
    pi.supplier = data["supplier"]
    pi.bill_no = data.get("bill_no")
    pi.posting_date = data.get("date", frappe.utils.today())
    pi.set_posting_time = 1
    pi.posting_time = frappe.utils.nowtime()
    pi.naming_series = data.get("naming_series", "PINV-.YY.-")
    pi.is_return = data.get("is_return", 0)
    pi.update_stock = 1
    if data.get("cost_center"):
        pi.cost_center = data["cost_center"]

    if data.get("discount_percentage"):
        pi.additional_discount_percentage = float(data["discount_percentage"])

    for item in data["items"]:
        disc = float(item.get("discount_percentage") or 0)
        price_list_rate = float(item.get("price_list_rate") or item["rate"])
        rate = float(item["rate"]) if not disc else round(price_list_rate * (1 - disc / 100), 9)
        qty = float(item["qty"])
        if pi.is_return:
            qty = -abs(qty)
        row = {
            "item_code": item["item_code"],
            "qty": qty,
            "price_list_rate": price_list_rate,
            "discount_percentage": disc,
            "rate": rate,
        }
        if frappe.get_meta("Purchase Invoice Item").has_field("allow_zero_valuation_rate"):
            row["allow_zero_valuation_rate"] = 1
        if item.get("warehouse"):
            row["warehouse"] = item["warehouse"]
        cost_center = item.get("cost_center") or data.get("cost_center") or ""
        if cost_center:
            row["cost_center"] = cost_center
        if item.get("expense_account"):
            row["expense_account"] = item["expense_account"]
        pi.append("items", row)

    if data.get("tax_template"):
        pi.taxes_and_charges = data["tax_template"]
        pi.set("taxes", _erpnext_tax_rows("Purchase Taxes and Charges Template", data["tax_template"]) or [])
        is_inclusive = data.get("is_inclusive", 0)
        if data.get("cost_center") or is_inclusive:
            for tax in pi.taxes:
                if data.get("cost_center") and not tax.cost_center:
                    tax.cost_center = data["cost_center"]
                if is_inclusive and "GST" in (tax.account_head or ""):
                    tax.included_in_print_rate = 1

    # Append extra charge rows from taxes key (freight, packing, loading, other)
    for tax_row in data.get("taxes") or []:
        pi.append("taxes", tax_row)

    pi.insert()

    # Save incentive_system if the field exists
    if frappe.get_meta("Purchase Invoice").has_field("incentive_system"):
        for row in data.get("incentive_system") or []:
            pi.append("incentive_system", {
                "employee": row.get("employee"),
                "role": row.get("role"),
                "points": row.get("points") or 0,
            })
        if data.get("incentive_system"):
            pi.save(ignore_permissions=True)

    return {
        "invoice_name": pi.name,
        "grand_total": float(pi.grand_total),
        "status": "Draft",
    }


@frappe.whitelist()
def get_tax_templates():
    """Return available Purchase Taxes and Charges Templates."""
    return frappe.get_all(
        "Purchase Taxes and Charges Template",
        filters={"disabled": 0},
        fields=["name"],
        order_by="name asc"
    )


@frappe.whitelist()
def get_naming_series():
    """Get available naming series for Purchase Invoice."""
    try:
        prop_value = frappe.db.get_value(
            "Property Setter",
            {"doc_type": "Purchase Invoice", "field_name": "naming_series", "property": "options"},
            "value",
        )
        if prop_value:
            return [s.strip() for s in prop_value.split("\n") if s.strip()]
    except Exception:
        pass

    try:
        meta = frappe.get_meta("Purchase Invoice")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            return [s.strip() for s in series_field.options.split("\n") if s.strip()]
    except Exception:
        pass

    return ["PINV-.YY.-"]


@frappe.whitelist()
def get_next_bill_no(naming_series="PINV-.YY.-"):
    """Get the next number in the naming series."""
    try:
        from frappe.model.naming import parse_naming_series
        return parse_naming_series(naming_series)
    except Exception:
        return naming_series + "???"


@frappe.whitelist()
def get_purchase_invoices(query="", limit=20, posting_date=None, show_submitted=False, naming_series=None, draft_only=False):
    """List Purchase Invoices for modification.
    
    draft_only=True  → only Draft invoices (docstatus=0).
    draft_only=False → all non-cancelled invoices for the date.
    """
    date_filter = posting_date or frappe.utils.today()
    filters = [["posting_date", "=", date_filter], ["docstatus", "!=", 2]]
    
    if frappe.utils.cint(draft_only):
        filters.append(["docstatus", "=", 0])
    
    if naming_series:
        filters.append(["naming_series", "=", naming_series])

    if query:
        import re
        flexible_query = "%" + "%".join(re.findall(r'[A-Za-z]+|\d+', query)) + "%"
        or_filters = [
            ["name", "like", flexible_query],
            ["supplier_name", "like", f"%{query}%"]
        ]
        invoices = frappe.get_all(
            "Purchase Invoice",
            filters=filters,
            or_filters=or_filters,
            fields=["name", "supplier", "supplier_name", "posting_date", "grand_total", "status", "modified", "docstatus"],
            limit=int(limit),
            order_by="name desc",
        )
    else:
        invoices = frappe.get_all(
            "Purchase Invoice",
            filters=filters,
            fields=["name", "supplier", "supplier_name", "posting_date", "grand_total", "status", "modified", "docstatus"],
            limit=int(limit),
            order_by="name desc",
        )

    for inv in invoices:
        inv["grand_total"] = float(inv["grand_total"] or 0)
        inv["customer_name"] = inv.get("supplier_name", "")
    return invoices


@frappe.whitelist()
def get_purchase_invoice(invoice_name):
    """Fetch a Purchase Invoice with its items."""
    pi = frappe.get_doc("Purchase Invoice", invoice_name)
    cost_center = pi.items[0].cost_center if pi.items else ""

    is_inclusive = 0

    def _actual_charge(keyword):
        for t in pi.taxes:
            if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
                return float(t.tax_amount or 0)
        return 0.0

    is_inclusive = 0
    if pi.taxes:
        if any(t.included_in_print_rate for t in pi.taxes):
            is_inclusive = 1

    # Fetch state from supplier address
    party_state = ""
    if pi.supplier_address:
        party_state = frappe.db.get_value("Address", pi.supplier_address, "state") or ""

    freight_amount = _actual_charge("freight")
    packing_amount = _actual_charge("packing")
    loading_amount = _actual_charge("loading")
    other_charges_amount = _actual_charge("other")

    incentive_system = []
    if frappe.get_meta("Purchase Invoice").has_field("incentive_system"):
        incentive_system = [
            {
                "employee": row.employee,
                "employee_name": frappe.db.get_value("Employee", row.employee, "employee_name") if row.employee else "",
                "role": row.role,
                "points": float(row.points or 0),
            }
            for row in (pi.incentive_system or [])
        ]

    return {
        "name": pi.name,
        "supplier": pi.supplier,
        "supplier_name": pi.supplier_name,
        "customer_name": pi.supplier_name,
        "state": party_state,
        "posting_date": str(pi.posting_date),
        "naming_series": pi.naming_series or "",
        "is_return": pi.is_return,
        "discount_percentage": float(pi.additional_discount_percentage or 0),
        "additional_discount_amount": float(pi.discount_amount or 0),
        "price_list": pi.buying_price_list or "",
        "payment_mode": "Cash",
        "freight_amount": freight_amount,
        "packing_amount": packing_amount,
        "loading_amount": loading_amount,
        "other_charges_amount": other_charges_amount,
        "grand_total": float(pi.grand_total or 0),
        "tax_template": pi.taxes_and_charges or "",
        "is_inclusive": is_inclusive,
        "cost_center": cost_center or "",
        "docstatus": pi.docstatus,
        "status": pi.status,
        "items": [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "uom": item.uom or item.stock_uom or "",
                "qty": float(item.qty),
                "price_list_rate": float(item.price_list_rate or item.rate or 0),
                "rate": float(item.rate),
                "discount": float(item.discount_percentage or 0),
                "warehouse": item.warehouse or "",
                "cost_center": item.cost_center or "",
                "tax_rate": _get_item_tax_rate(item.item_code),
                "deleted": False,
            }
            for item in pi.items
        ],
        "incentive_system": incentive_system,
    }


@frappe.whitelist()
def update_purchase_invoice(data=None, **kwargs):
    """Update an existing Draft Purchase Invoice."""
    if not data: data = frappe.form_dict.get("data")
    if isinstance(data, str): data = json.loads(data)

    invoice_name = data.get("invoice_name")
    pi = frappe.get_doc("Purchase Invoice", invoice_name)
    
    if pi.supplier != data["supplier"]:
        pi.supplier = data["supplier"]
        pi.supplier_address = None
        pi.shipping_address_name = None
        pi.contact_person = None
        pi.contact_display = None
        pi.contact_mobile = None
        pi.contact_email = None
        pi.address_display = None

    pi.is_return = data.get("is_return", 0)
    pi.bill_no = data.get("bill_no")
    pi.posting_date = data.get("date", frappe.utils.today())
    pi.set_posting_time = 1
    # Do not overwrite posting_time if it's already set on existing document,
    # unless it's explicitly passed in data.
    if not pi.posting_time:
        pi.posting_time = frappe.utils.nowtime()
    
    pi.additional_discount_percentage = float(data.get("discount_percentage", 0))
    if data.get("tax_template"):
        pi.taxes_and_charges = data["tax_template"]
    elif "tax_template" in data:
        pi.taxes_and_charges = ""
    if data.get("tax_template"):
        pi.taxes_and_charges = data["tax_template"]
        pi.set("taxes", _erpnext_tax_rows("Purchase Taxes and Charges Template", data["tax_template"]) or [])
        is_inclusive = data.get("is_inclusive", 0)
        if data.get("cost_center") or is_inclusive:
            for tax in pi.taxes:
                if data.get("cost_center") and not tax.cost_center:
                    tax.cost_center = data["cost_center"]
                if is_inclusive and "GST" in (tax.account_head or ""):
                    tax.included_in_print_rate = 1
    else:
        pi.taxes = []
    pi.items = []
    for item in data["items"]:
        disc = float(item.get("discount_percentage") or 0)
        price_list_rate = float(item.get("price_list_rate") or item["rate"])
        rate = float(item["rate"]) if not disc else round(price_list_rate * (1 - disc / 100), 9)
        qty = float(item["qty"])
        if pi.is_return:
            qty = -abs(qty)
        row = {
            "item_code": item["item_code"],
            "qty": qty,
            "price_list_rate": price_list_rate,
            "discount_percentage": disc,
            "rate": rate,
            "warehouse": item.get("warehouse"),
        }
        if frappe.get_meta("Purchase Invoice Item").has_field("allow_zero_valuation_rate"):
            row["allow_zero_valuation_rate"] = 1
        cost_center = item.get("cost_center") or data.get("cost_center") or ""
        if cost_center:
            row["cost_center"] = cost_center
        if item.get("expense_account"):
            row["expense_account"] = item["expense_account"]
        pi.append("items", row)

    # Append extra charge rows from taxes key (freight, packing, loading, other)
    for tax_row in data.get("taxes") or []:
        pi.append("taxes", tax_row)

    pi.save()

    # Save incentive_system if the field exists
    if frappe.get_meta("Purchase Invoice").has_field("incentive_system"):
        pi.set("incentive_system", [])
        for row in data.get("incentive_system") or []:
            pi.append("incentive_system", {
                "employee": row.get("employee"),
                "role": row.get("role"),
                "points": row.get("points") or 0,
            })
        pi.save(ignore_permissions=True)

    return {"invoice_name": pi.name, "grand_total": float(pi.grand_total)}


@frappe.whitelist()
def submit_purchase_invoice(invoice_name):
    """Submit a Draft Purchase Invoice."""
    if not invoice_name:
        frappe.throw("Invoice Name is required")
    
    pi = frappe.get_doc("Purchase Invoice", invoice_name)
    if pi.docstatus == 0:
        pi.submit()
        return {"name": pi.name, "status": "Submitted"}
    elif pi.docstatus == 1:
        return {"name": pi.name, "status": "Already Submitted"}
    else:
        frappe.throw(f"Invoice {invoice_name} is already cancelled")

@frappe.whitelist()
def delete_purchase_invoice(invoice_name):
    """Delete a Draft Purchase Invoice."""
    frappe.delete_doc("Purchase Invoice", invoice_name)
    return {"status": "Deleted"}
