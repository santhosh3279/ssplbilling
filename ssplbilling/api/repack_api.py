import json
import frappe
from frappe import _

@frappe.whitelist()
def get_repack_details(name):
    """Return Stock Entry details for Repack."""
    doc = frappe.get_doc("Stock Entry", name)
    doc_dict = doc.as_dict()
    
    items = []
    for item in doc.items:
        item_dict = item.as_dict()
        # In a Repack entry, consumed items have s_warehouse and no t_warehouse.
        # Produced items have t_warehouse and no s_warehouse.
        if item.s_warehouse and not item.t_warehouse:
            item_dict["type"] = "Consume"
        elif item.t_warehouse and not item.s_warehouse:
            item_dict["type"] = "Produce"
        else:
            item_dict["type"] = "Consume" if item.s_warehouse else "Produce"
        
        # Add rate/amount mapping for frontend
        item_dict["rate"] = float(item.basic_rate or 0)
        item_dict["amount"] = float(item.amount or 0)
        items.append(item_dict)
        
    doc_dict["items"] = items
    return doc_dict

@frappe.whitelist()
def save_repack(data):
    """Create or update a Stock Entry for Repack."""
    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    if name:
        se = frappe.get_doc("Stock Entry", name)
        if se.docstatus != 0:
            frappe.throw(_("Cannot update a submitted or cancelled Stock Entry."))
    else:
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Repack"
        se.purpose = "Repack"
        se.naming_series = data.get("naming_series") or "MAT-REP-.YYYY.-"

    if data.get("company"):
        se.company = data["company"]
    se.posting_date = data.get("posting_date") or frappe.utils.today()
    se.from_warehouse = data.get("from_warehouse")  # Default Source
    se.to_warehouse = data.get("to_warehouse")      # Default Destination

    se.items = []
    for row in data.get("items") or []:
        is_consume = row.get("type") == "Consume"
        s_wh = row.get("s_warehouse") or (se.from_warehouse if is_consume else None)
        t_wh = row.get("t_warehouse") or (se.to_warehouse if not is_consume else None)
        
        # ERPNext Repack logic:
        # Raw materials: source warehouse set, target warehouse is None.
        # Finished goods: target warehouse set, source warehouse is None.
        if is_consume:
            t_wh = None
        else:
            s_wh = None

        se.append("items", {
            "item_code": row.get("item_code"),
            "qty": float(row.get("qty") or 0),
            "uom": row.get("uom"),
            "s_warehouse": s_wh,
            "t_warehouse": t_wh,
            "basic_rate": float(row.get("rate") or 0)
        })

    if name:
        se.save()
    else:
        se.insert()

    return {
        "name": se.name,
        "status": "Draft"
    }

@frappe.whitelist()
def submit_repack(name):
    """Submit a Stock Entry for Repack."""
    doc = frappe.get_doc("Stock Entry", name)
    doc.submit()
    return {"status": "Submitted"}

@frappe.whitelist()
def get_metadata():
    """Fetch metadata for Repack."""
    return {
        "warehouses": frappe.get_all("Warehouse", filters={"is_group": 0}, fields=["name"]),
        "naming_series": get_naming_series()
    }

def get_naming_series():
    """Get naming series for Stock Entry Repack."""
    try:
        meta = frappe.get_meta("Stock Entry")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            options = [s.strip() for s in series_field.options.split("\n") if s.strip()]
            # Put Repack series first if available
            repack_options = [o for o in options if "REP" in o]
            other_options = [o for o in options if "REP" not in o]
            return repack_options + other_options
    except Exception:
        pass
    return ["MAT-REP-.YYYY.-", "STE-.YYYY.-"]

@frappe.whitelist()
def get_recent_repacks(date=None):
    """Get recent Repack Stock Entries for the sidebar."""
    if not date:
        date = frappe.utils.today()
    
    repacks = frappe.get_all(
        "Stock Entry",
        filters={
            "posting_date": date,
            "purpose": "Repack"
        },
        fields=["name", "total_amount as grand_total", "from_warehouse", "to_warehouse", "docstatus", "posting_date"],
        order_by="creation desc"
    )
    
    for r in repacks:
        r["customer_name"] = f"{r.from_warehouse or ''} -> {r.to_warehouse or ''}"
    
    return repacks
