import frappe
import json

@frappe.whitelist()
def get_outstanding_invoices(party, party_type="Customer"):
    """Fetch outstanding invoices/bills for a given party."""
    if not party:
        return []
    
    doctype = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
    party_field = "customer" if party_type == "Customer" else "supplier"
    
    filters = {
        party_field: party,
        "docstatus": 1,
        "outstanding_amount": [">", 0]
    }
    
    return frappe.get_all(
        doctype,
        filters=filters,
        fields=["name", "posting_date", "grand_total", "outstanding_amount"],
        order_by="posting_date desc"
    )

@frappe.whitelist()
def create_payment_entry(data):
    """Create and submit a Payment Entry."""
    if isinstance(data, str):
        data = json.loads(data)
        
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = data.get("payment_type") # 'Receive' or 'Pay'
    pe.party_type = data.get("party_type") # 'Customer' or 'Supplier'
    pe.party = data.get("party")
    pe.posting_date = data.get("date") or frappe.utils.today()
    
    amount = float(data.get("amount") or 0)
    pe.paid_amount = amount
    pe.received_amount = amount
    
    pe.mode_of_payment = data.get("mode_of_payment") or "Cash"
    
    # If mode is cash/upi, we might need to set the specific account based on settings
    # For now, let Frappe handle defaults or provide them
    if data.get("paid_from"):
        pe.paid_from = data["paid_from"]
    if data.get("paid_to"):
        pe.paid_to = data["paid_to"]
        
    pe.reference_no = data.get("reference_no")
    pe.reference_date = data.get("reference_date") or pe.posting_date
    pe.remarks = data.get("remarks")
    
    # Link to invoice if provided
    if data.get("invoice_name"):
        pe.append("references", {
            "reference_doctype": "Sales Invoice" if pe.party_type == "Customer" else "Purchase Invoice",
            "reference_name": data["invoice_name"],
            "allocated_amount": amount
        })
        
    pe.insert()
    pe.submit()
    
    return {"name": pe.name, "status": "Submitted"}

@frappe.whitelist()
def search_parties(query, party_type="Customer"):
    """Search for Customer or Supplier."""
    doctype = "Customer" if party_type == "Customer" else "Supplier"
    name_field = "customer_name" if party_type == "Customer" else "supplier_name"
    
    filters = {
        "disabled": 0,
        name_field: ["like", f"%{query}%"]
    }
    
    return frappe.get_all(
        doctype,
        filters=filters,
        fields=["name", f"{name_field} as label"],
        limit=20
    )
