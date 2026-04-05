import frappe

def get_company_state():
    company = "Sundaram and Sons Private Ltd"
    address_name = frappe.db.get_value("Dynamic Link", {"link_doctype": "Company", "link_name": company, "parenttype": "Address"}, "parent")
    if address_name:
        state = frappe.db.get_value("Address", address_name, "state")
        return state
    return None
