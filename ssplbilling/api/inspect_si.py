import frappe
import json

def run():
    doc = frappe.get_doc("Sales Invoice", "EOW00188")
    advances = [d.as_dict() for d in doc.advances]
    print(json.dumps(advances, default=str, indent=2))
    
    for adv in doc.advances:
        if adv.reference_type == "Payment Entry":
            pe = frappe.get_doc("Payment Entry", adv.reference_name)
            print(f"\nPayment Entry: {pe.name}")
            print(f"Unallocated Amount: {pe.unallocated_amount}")
            print(f"Docstatus: {pe.docstatus}")

run()
