import frappe
import json
from frappe import _
from frappe.utils import flt, nowdate

@frappe.whitelist()
def create_gst_dummy_entry(data):
    """Create a new Gst Dummy Ledger entry."""
    if isinstance(data, str):
        data = json.loads(data)
    
    doc = frappe.new_doc("Gst Dummy Ledger")
    doc.update({
        "naming_series": data.get("naming_series") or "GDL-.YYYY.-.####",
        "date": data.get("date") or nowdate(),
        "customer": data.get("customer"),
        "debit": flt(data.get("debit")),
        "credit": flt(data.get("credit"))
    })
    doc.insert()
    return doc.name

@frappe.whitelist()
def get_gst_dummy_entries(customer=None, from_date=None, to_date=None):
    """Fetch Gst Dummy Ledger entries."""
    filters = {}
    if customer:
        filters["customer"] = customer
    if from_date and to_date:
        filters["date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["date"] = [">=", from_date]
    elif to_date:
        filters["date"] = ["<=", to_date]
        
    return frappe.get_all("Gst Dummy Ledger", 
        filters=filters, 
        fields=["name", "date", "customer", "debit", "credit"],
        order_by="date desc, creation desc"
    )
