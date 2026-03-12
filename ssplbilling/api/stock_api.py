import json
import frappe
from frappe import _


@frappe.whitelist()
def get_item_details(item_code, warehouse=None):
    """Look up item by code or barcode. Returns item details + stock."""
    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": item_code}, "parent")
    if barcode_item:
        item_code = barcode_item

    if not frappe.db.exists("Item", item_code):
        return {"found": False, "item_code": item_code}

    item = frappe.get_cached_doc("Item", item_code)
    wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

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
        "stock_qty": float(stock_qty),
        "warehouse": wh,
        "valuation_rate": float(item.valuation_rate or 0),
    }


@frappe.whitelist()
def search_items(query, warehouse=None):
    """Search items by code, name, or barcode. Returns list of matches."""
    if not query or len(query) < 1:
        return []

    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": query}, "parent")
    if barcode_item:
        return [get_item_details(barcode_item, warehouse)]

    items = frappe.get_all(
        "Item",
        or_filters={
            "item_code": ["like", f"%{query}%"],
            "item_name": ["like", f"%{query}%"],
        },
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["item_code", "item_name", "stock_uom as uom", "valuation_rate"],
        limit=20,
        order_by="item_name asc",
    )

    wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
    for item in items:
        item["stock_qty"] = float(
            frappe.db.get_value("Bin", {"item_code": item["item_code"], "warehouse": wh}, "actual_qty")
            or 0
        ) if wh else 0
        item["warehouse"] = wh
        item["found"] = True
        item["valuation_rate"] = float(item["valuation_rate"] or 0)

    return items


@frappe.whitelist()
def create_stock_entry(data=None, **kwargs):
    """Create Stock Entry for Material Transfer in Draft."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("items"):
        frappe.throw(_("At least one item is required"))

    se = frappe.new_doc("Stock Entry")
    se.purpose = data.get("purpose", "Material Transfer")
    se.posting_date = data.get("date", frappe.utils.today())
    se.naming_series = data.get("naming_series", "MAT-TRA-.YYYY.-")
    
    # Global warehouses
    default_from = data.get("from_warehouse")
    default_to = data.get("to_warehouse")
    
    if default_from:
        se.from_warehouse = default_from
    if default_to:
        se.to_warehouse = default_to

    for item in data["items"]:
        row = {
            "item_code": item["item_code"],
            "qty": float(item["qty"]),
            "uom": item.get("uom"),
            "s_warehouse": item.get("from_warehouse") or default_from,
            "t_warehouse": item.get("to_warehouse") or default_to,
            "basic_rate": float(item.get("rate") or 0),
        }
        se.append("items", row)

    se.insert()

    return {
        "name": se.name,
        "status": "Draft",
    }


@frappe.whitelist()
def update_stock_entry(data=None, **kwargs):
    """Update an existing Draft Stock Entry."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    entry_name = data.get("name")
    if not entry_name:
        frappe.throw(_("Stock Entry name is required for update"))
        
    se = frappe.get_doc("Stock Entry", entry_name)
    if se.docstatus != 0:
        frappe.throw(_("Only Draft Stock Entries can be updated"))

    se.purpose = data.get("purpose", se.purpose)
    se.posting_date = data.get("date", frappe.utils.today())
    
    default_from = data.get("from_warehouse")
    default_to = data.get("to_warehouse")
    
    if default_from:
        se.from_warehouse = default_from
    if default_to:
        se.to_warehouse = default_to

    se.items = []
    for item in data["items"]:
        se.append("items", {
            "item_code": item["item_code"],
            "qty": float(item["qty"]),
            "uom": item.get("uom"),
            "s_warehouse": item.get("from_warehouse") or default_from,
            "t_warehouse": item.get("to_warehouse") or default_to,
            "basic_rate": float(item.get("rate") or 0),
        })
    
    se.save()
    return {"name": se.name, "status": "Draft"}


@frappe.whitelist()
def get_naming_series():
    """Get available naming series for Stock Entry."""
    try:
        prop_value = frappe.db.get_value(
            "Property Setter",
            {"doc_type": "Stock Entry", "field_name": "naming_series", "property": "options"},
            "value",
        )
        if prop_value:
            return [s.strip() for s in prop_value.split("\n") if s.strip()]
    except Exception:
        pass

    try:
        meta = frappe.get_meta("Stock Entry")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            return [s.strip() for s in series_field.options.split("\n") if s.strip()]
    except Exception:
        pass

    return ["MAT-TRA-.YYYY.-"]


@frappe.whitelist()
def get_stock_entries(query="", limit=20, posting_date=None):
    """List Stock Entries for modification."""
    date_filter = posting_date or frappe.utils.today()
    kwargs = dict(
        filters={
            "posting_date": date_filter,
            "purpose": "Material Transfer",
            "docstatus": 0
        },
        fields=["name", "from_warehouse", "to_warehouse", "posting_date", "total_outgoing_value", "status", "modified", "docstatus"],
        limit=int(limit),
        order_by="modified desc",
    )
    if query:
        kwargs["or_filters"] = {
            "name": ["like", f"%{query}%"],
        }
    return frappe.get_all("Stock Entry", **kwargs)


@frappe.whitelist()
def get_stock_entry(name):
    """Fetch a Stock Entry with its items."""
    se = frappe.get_doc("Stock Entry", name)

    return {
        "name": se.name,
        "purpose": se.purpose,
        "posting_date": str(se.posting_date),
        "naming_series": se.naming_series or "",
        "from_warehouse": se.from_warehouse or "",
        "to_warehouse": se.to_warehouse or "",
        "docstatus": se.docstatus,
        "status": se.status,
        "items": [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "uom": item.uom or item.stock_uom or "",
                "qty": float(item.qty),
                "rate": float(item.basic_rate),
                "from_warehouse": item.s_warehouse or "",
                "to_warehouse": item.t_warehouse or "",
                "deleted": False,
            }
            for item in se.items
        ],
    }


@frappe.whitelist()
def submit_stock_entry(name):
    """Submit a Draft Stock Entry."""
    if not name:
        frappe.throw(_("Stock Entry name is required"))
    
    se = frappe.get_doc("Stock Entry", name)
    if se.docstatus == 0:
        se.submit()
        return {"name": se.name, "status": "Submitted"}
    elif se.docstatus == 1:
        return {"name": se.name, "status": "Already Submitted"}
    else:
        frappe.throw(_("Stock Entry {0} is already cancelled").format(name))


@frappe.whitelist()
def get_stock_entry_purposes():
    """Get all available purposes for Stock Entry."""
    meta = frappe.get_meta("Stock Entry")
    options = meta.get_field("purpose").options
    if options:
        return [o.strip() for o in options.split("\n") if o.strip()]
    return ["Material Issue", "Material Receipt", "Material Transfer"]
