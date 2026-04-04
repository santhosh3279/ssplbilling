import json
import frappe
from frappe import _
from frappe.utils import flt, nowdate, nowtime

@frappe.whitelist()
def get_items_for_reconciliation(warehouse=None):
    """Get all items with their current stock for a warehouse."""
    if not warehouse:
        warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    
    if not warehouse:
        frappe.throw(_("Please provide a warehouse or set a default warehouse in Stock Settings"))

    # Get all items that have stock in this warehouse or are active
    items = frappe.db.sql("""
        SELECT 
            i.item_code, 
            i.item_name, 
            i.stock_uom as uom,
            IFNULL(b.actual_qty, 0) as current_qty,
            IFNULL(b.valuation_rate, IFNULL(i.valuation_rate, 0)) as current_valuation_rate
        FROM 
            `tabItem` i
        LEFT JOIN 
            `tabBin` b ON i.item_code = b.item_code AND b.warehouse = %s
        WHERE 
            i.disabled = 0 AND i.is_stock_item = 1
        ORDER BY 
            i.item_name ASC
    """, (warehouse,), as_dict=1)

    for item in items:
        item.current_qty = flt(item.current_qty)
        item.current_valuation_rate = flt(item.current_valuation_rate)
        item.qty = item.current_qty  # Default target qty to current qty
    
    return items

@frappe.whitelist()
def create_stock_reconciliation(data=None, **kwargs):
    """Create a Stock Reconciliation document in Draft."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("items"):
        frappe.throw(_("At least one item is required"))

    sr = frappe.new_doc("Stock Reconciliation")
    sr.posting_date = data.get("posting_date") or nowdate()
    sr.posting_time = data.get("posting_time") or nowtime()
    sr.company = data.get("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    sr.purpose = data.get("purpose") or "Stock Reconciliation"
    sr.set_posting_time = 1

    for item in data["items"]:
        sr.append("items", {
            "item_code": item["item_code"],
            "warehouse": item.get("warehouse") or data.get("warehouse"),
            "qty": flt(item["qty"]),
            "valuation_rate": flt(item.get("valuation_rate") or item.get("current_valuation_rate") or 0)
        })

    sr.insert()
    return {
        "name": sr.name,
        "status": "Draft",
    }

@frappe.whitelist()
def update_stock_reconciliation(data=None, **kwargs):
    """Update an existing Draft Stock Reconciliation."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    if not name:
        frappe.throw(_("Stock Reconciliation name is required for update"))
        
    sr = frappe.get_doc("Stock Reconciliation", name)
    if sr.docstatus != 0:
        frappe.throw(_("Only Draft Stock Reconciliations can be updated"))

    sr.posting_date = data.get("posting_date") or sr.posting_date
    sr.posting_time = data.get("posting_time") or sr.posting_time
    sr.purpose = data.get("purpose") or sr.purpose
    
    sr.items = []
    for item in data["items"]:
        sr.append("items", {
            "item_code": item["item_code"],
            "warehouse": item.get("warehouse") or data.get("warehouse"),
            "qty": flt(item["qty"]),
            "valuation_rate": flt(item.get("valuation_rate") or 0)
        })
    
    sr.save()
    return {"name": sr.name, "status": "Draft"}

@frappe.whitelist()
def get_stock_reconciliation_purposes():
    """Get all available purposes for Stock Reconciliation."""
    meta = frappe.get_meta("Stock Reconciliation")
    options = meta.get_field("purpose").options
    if options:
        return [o.strip() for o in options.split("\n") if o.strip()]
    return ["Stock Reconciliation", "Opening Stock"]

@frappe.whitelist()
def get_stock_reconciliations(query="", limit=20, posting_date=None, docstatus=None):
    """List Stock Reconciliations."""
    filters = {}
    if docstatus is not None:
        filters["docstatus"] = docstatus
    else:
        filters["docstatus"] = ["<", 2]
        
    if posting_date:
        filters["posting_date"] = posting_date
        
    kwargs = dict(
        filters=filters,
        fields=["name", "posting_date", "company", "modified", "docstatus"],
        limit=int(limit),
        order_by="modified desc",
    )
    if query:
        kwargs["or_filters"] = {
            "name": ["like", f"%{query}%"],
        }
    return frappe.get_all("Stock Reconciliation", **kwargs)

@frappe.whitelist()
def get_stock_reconciliation(name):
    """Fetch a Stock Reconciliation with its items."""
    doc = frappe.get_all("Stock Reconciliation", 
        filters={"name": name},
        fields=["name", "posting_date", "company", "docstatus", "purpose"]
    )
    if not doc:
        frappe.throw(_("Stock Reconciliation {0} not found").format(name))
    
    sr = doc[0]
    items = frappe.get_all("Stock Reconciliation Item",
        filters={"parent": name},
        fields=["item_code", "item_name", "warehouse", "stock_uom", "qty", "valuation_rate", "current_qty", "current_valuation_rate"]
    )

    return {
        "name": sr.name,
        "posting_date": str(sr.posting_date),
        "purpose": sr.purpose,
        "company": sr.company,
        "docstatus": sr.docstatus,
        "items": [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "warehouse": item.warehouse,
                "uom": item.stock_uom,
                "qty": flt(item.qty),
                "valuation_rate": flt(item.valuation_rate),
                "current_qty": flt(item.current_qty),
                "current_valuation_rate": flt(item.current_valuation_rate),
            }
            for item in items
        ],
    }

@frappe.whitelist()
def submit_stock_reconciliation(name):
    """Submit a Draft Stock Reconciliation."""
    if not name:
        frappe.throw(_("Stock Reconciliation name is required"))
    
    sr = frappe.get_doc("Stock Reconciliation", name)
    if sr.docstatus == 0:
        sr.submit()
        return {"name": sr.name, "status": "Submitted"}
    elif sr.docstatus == 1:
        return {"name": sr.name, "status": "Already Submitted"}
    else:
        frappe.throw(_("Stock Reconciliation {0} is already cancelled").format(name))
