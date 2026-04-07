import json
import frappe
from frappe import _

@frappe.whitelist()
def get_customer_details(customer):
    """Return customer details for Sales Invoice header."""
    from ssplbilling.api.customersearch_api import get_customer_full
    return get_customer_full(customer)

@frappe.whitelist()
def get_next_invoice_no(naming_series):
    """Get next available invoice number."""
    from frappe.model.naming import parse_naming_series
    return parse_naming_series(naming_series)
