import frappe
import json
from frappe import _
from frappe.utils import flt, nowdate, add_days

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

@frappe.whitelist()
def get_gst_ledger(customer, from_date=None, to_date=None):
    """Return a combined ledger of Quotations and GST Dummy entries for a customer."""
    if not customer:
        frappe.throw(_("Customer is required"))

    to_date = to_date or nowdate()
    from_date = from_date or add_days(to_date, -90)

    # 0. Calculate Opening Balance (before from_date)
    # Quotations
    q_opening = frappe.db.sql("""
        SELECT SUM(grand_total) FROM `tabQuotation`
        WHERE quotation_to = 'Customer' AND party_name = %s
          AND docstatus < 2 AND transaction_date < %s
    """, (customer, from_date))[0][0] or 0.0

    # GST Dummy Ledger
    d_opening = frappe.db.sql("""
        SELECT SUM(debit - credit) FROM `tabGst Dummy Ledger`
        WHERE customer = %s AND date < %s
    """, (customer, from_date))[0][0] or 0.0

    opening_balance = flt(q_opening) + flt(d_opening)

    # 1. Fetch Quotations (treat grand_total as DEBIT)
    quotations = frappe.db.get_all("Quotation",
        filters={
            "quotation_to": "Customer",
            "party_name": customer,
            "docstatus": ["<", 2],
            "transaction_date": ["between", [from_date, to_date]]
        },
        fields=["name", "transaction_date as date", "grand_total as debit", "customer_name"],
        order_by="transaction_date asc"
    )
    
    # 2. Fetch Gst Dummy Ledger entries
    dummy_entries = frappe.db.get_all("Gst Dummy Ledger",
        filters={
            "customer": customer,
            "date": ["between", [from_date, to_date]]
        },
        fields=["name", "date", "debit", "credit"],
        order_by="date asc"
    )

    # Merge and sort
    all_entries = []
    for q in quotations:
        all_entries.append({
            "date": str(q.date),
            "voucher_type": "Quotation",
            "voucher_no": q.name,
            "debit": flt(q.debit),
            "credit": 0.0,
            "label": q.customer_name or customer
        })
    
    for d in dummy_entries:
        all_entries.append({
            "date": str(d.date),
            "voucher_type": "Gst Dummy Ledger",
            "voucher_no": d.name,
            "debit": flt(d.debit),
            "credit": flt(d.credit),
            "label": customer
        })

    all_entries.sort(key=lambda x: (x["date"], x["voucher_no"]))

    # Calculate totals and running balance
    total_debit = 0.0
    total_credit = 0.0
    balance = opening_balance
    
    for entry in all_entries:
        total_debit += entry["debit"]
        total_credit += entry["credit"]
        balance += entry["debit"] - entry["credit"]
        entry["balance"] = balance

    # Fetch details for detail panel (Quotations only)
    quotation_names = [e["voucher_no"] for e in all_entries if e["voucher_type"] == "Quotation"]
    voucher_details = {}
    
    if quotation_names:
        items = frappe.get_all("Quotation Item",
            filters={"parent": ["in", quotation_names]},
            fields=["parent", "item_code", "item_name", "qty", "rate", "amount", "uom"]
        )
        
        # Group items by parent
        for it in items:
            p = it.parent
            if p not in voucher_details:
                voucher_details[p] = {
                    "voucher_type": "Quotation",
                    "voucher_no": p,
                    "items": []
                }
            voucher_details[p]["items"].append(it)

    return {
        "customer": customer,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "opening_balance": round(opening_balance, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "closing_balance": round(balance, 2),
        "entries": all_entries,
        "voucher_details": voucher_details
    }
