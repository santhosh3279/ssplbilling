"""Keep a transaction's party address and derived fields in sync."""

import frappe


def set_party_address(doc, party_type, party_name, address_name, party_field):
    address_field = "customer_address" if party_type == "Customer" else "supplier_address"
    address_name = address_name or None
    if address_name and not frappe.db.exists("Dynamic Link", {
        "parent": address_name,
        "parenttype": "Address",
        "link_doctype": party_type,
        "link_name": party_name,
    }):
        frappe.throw(f"Address {address_name} is not linked to {party_type} {party_name}")

    doc.set(party_field, party_name)
    doc.set(address_field, address_name)
    fields = (
        "shipping_address_name", "shipping_address", "contact_person",
        "contact_display", "contact_mobile", "contact_email", "address_display",
        "tax_category", "gst_category", "tax_id", "place_of_supply",
    )
    if party_type == "Customer":
        fields += ("customer_name", "billing_address_gstin")
    else:
        fields += ("supplier_name", "supplier_gstin")
    for field in fields:
        if doc.meta.has_field(field):
            doc.set(field, None)
