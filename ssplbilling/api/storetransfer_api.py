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
    """Create or update a Stock Entry for Store Transfer."""
    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    if name:
        se = frappe.get_doc("Stock Entry", name)
        if se.docstatus != 0:
            frappe.throw(_("Cannot update a submitted or cancelled Stock Entry."))
    else:
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Transfer"
        se.purpose = "Material Transfer"
        se.naming_series = data.get("naming_series") or "MAT-TRA-.YYYY.-"

    se.posting_date = data.get("posting_date") or frappe.utils.today()
    se.from_warehouse = data.get("from_warehouse")
    se.to_warehouse = data.get("to_warehouse")

    if not se.from_warehouse or not se.to_warehouse:
        frappe.throw(_("Source and Destination warehouses are required."))

    se.items = []
    for row in data.get("items") or []:
        se.append("items", {
            "item_code": row.get("item_code"),
            "qty": float(row.get("qty") or 0),
            "uom": row.get("uom"),
            "s_warehouse": row.get("s_warehouse") or se.from_warehouse,
            "t_warehouse": row.get("t_warehouse") or se.to_warehouse,
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
        fields=["name", "total_amount as grand_total", "from_warehouse", "to_warehouse", "docstatus", "posting_date"],
        order_by="creation desc"
    )
    
    # Map for frontend consistency
    for t in transfers:
        t["customer_name"] = f"{t.from_warehouse} -> {t.to_warehouse}"
    
    return transfers

@frappe.whitelist()
def get_item_details(item_code, warehouse=None):
    """Look up item by code or barcode. Returns item details + stock + valuation_rate."""
    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": item_code}, "parent")
    if barcode_item:
        item_code = barcode_item

    if not frappe.db.exists("Item", item_code):
        canonical = frappe.db.get_value("Item", {"item_code": ["like", item_code]}, "item_code")
        if canonical:
            item_code = canonical
        else:
            return {"found": False, "item_code": item_code}

    item = frappe.get_doc("Item", item_code)
    
    val_rate = 0.0
    stock_qty = 0.0
    if warehouse:
        bin_details = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, ["actual_qty", "valuation_rate"], as_dict=True)
        if bin_details:
            stock_qty = float(bin_details.actual_qty or 0)
            val_rate = float(bin_details.valuation_rate or 0)
            
    if not val_rate:
        val_rate = float(item.valuation_rate or item.standard_rate or 0)

    return {
        "found": True,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "uom": item.stock_uom,
        "rate": val_rate,
        "stock_qty": stock_qty,
        "warehouse": warehouse
    }
