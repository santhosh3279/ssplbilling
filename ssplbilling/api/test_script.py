import frappe

def test():
    doc = frappe.new_doc("Sales Invoice")
    doc.customer = "Cash"
    doc.append("items", {
        "item_code": "0001",
        "qty": 1,
        "rate": 100
    })
    doc.set_missing_values()
    print("Taxes after set_missing_values:")
    for t in doc.taxes:
        print(t.account_head)
        
    if doc.taxes_and_charges:
        doc.append_taxes_from_master()
    print("Taxes after append_taxes_from_master:")
    for t in doc.taxes:
        print(t.account_head)
