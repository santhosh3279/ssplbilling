import frappe
from frappe import _

@frappe.whitelist()
def get_party_links(party=None, role=None):
    filters = {}
    if party:
        filters["primary_party"] = party
    if role:
        filters["primary_role"] = role
        
    return frappe.get_all(
        "Party Link",
        fields=["name", "primary_party", "primary_role", "secondary_party", "secondary_role"],
        filters=filters
    )

@frappe.whitelist()
def add_party_link(primary_party, primary_role, secondary_party, secondary_role):
    # Check if link already exists
    exists = frappe.db.exists("Party Link", {
        "primary_party": primary_party,
        "primary_role": primary_role,
        "secondary_party": secondary_party,
        "secondary_role": secondary_role
    })
    
    if exists:
        frappe.throw(_("Party Link already exists"))
        
    doc = frappe.get_doc({
        "doctype": "Party Link",
        "primary_party": primary_party,
        "primary_role": primary_role,
        "secondary_party": secondary_party,
        "secondary_role": secondary_role
    })
    doc.insert()
    return doc

@frappe.whitelist()
def remove_party_link(name):
    frappe.delete_doc("Party Link", name)
    return True

@frappe.whitelist()
def search_parties(doctype, query):
    return frappe.get_all(
        doctype,
        fields=["name", "customer_name" if doctype == "Customer" else "supplier_name"],
        filters={
            "name": ["like", f"%{query}%"],
            "disabled": 0
        },
        limit=20
    )
