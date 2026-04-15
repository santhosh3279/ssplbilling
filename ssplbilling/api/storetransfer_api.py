import json
import frappe
from frappe import _

@frappe.whitelist()
def get_store_transfer_details(name):
    """Return Stock Entry details for Store Transfer."""
    doc = frappe.get_doc("Stock Entry", name)
    return doc.as_dict()

@frappe.whitelist()
def save_store_transfer(data):
    """Create a new Stock Entry for Store Transfer."""
    if isinstance(data, str):
        data = json.loads(data)

    se = frappe.new_doc("Stock Entry")
    se.purpose = "Material Transfer"
    se.naming_series = data.get("naming_series") or "MAT-TRA-.YYYY.-"
    se.posting_date = data.get("posting_date") or frappe.utils.today()
    se.from_warehouse = data.get("from_warehouse")
    se.to_warehouse = data.get("to_warehouse")

    if not se.from_warehouse or not se.to_warehouse:
        frappe.throw(_("Source and Destination warehouses are required."))

    for row in data.get("items") or []:
        se.append("items", {
            "item_code": row.get("item_code"),
            "qty": float(row.get("qty") or 0),
            "uom": row.get("uom"),
            "s_warehouse": row.get("s_warehouse") or se.from_warehouse,
            "t_warehouse": row.get("t_warehouse") or se.to_warehouse,
            "basic_rate": float(row.get("rate") or 0)
        })

    se.insert()
    return {
        "name": se.name,
        "status": "Draft"
    }

@frappe.whitelist()
def submit_store_transfer(name):
    """Submit a Stock Entry."""
    doc = frappe.get_doc("Stock Entry", name)
    doc.submit()
    return {"status": "Submitted"}

@frappe.whitelist()
def get_metadata():
    """Fetch metadata for Store Transfer."""
    return {
        "warehouses": frappe.get_all("Warehouse", filters={"is_group": 0}, fields=["name"]),
        "naming_series": get_naming_series()
    }

def get_naming_series():
    """Get naming series for Stock Entry."""
    try:
        meta = frappe.get_meta("Stock Entry")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            return [s.strip() for s in series_field.options.split("\n") if s.strip()]
    except Exception:
        pass
    return ["MAT-TRA-.YYYY.-"]

@frappe.whitelist()
def get_recent_transfers(date=None):
    """Get recent Store Transfers for the sidebar."""
    if not date:
        date = frappe.utils.today()
    
    transfers = frappe.get_all(
        "Stock Entry",
        filters={
            "posting_date": date,
            "purpose": "Material Transfer"
        },
        fields=["name", "total_amount as grand_total", "from_warehouse", "to_warehouse", "docstatus"],
        order_by="creation desc"
    )
    
    # Map for frontend consistency
    for t in transfers:
        t["customer_name"] = f"{t.from_warehouse} -> {t.to_warehouse}"
    
    return transfers
