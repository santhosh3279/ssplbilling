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

@frappe.whitelist()
def get_series_defaults(naming_series):
    """Return naming series defaults and the next available number."""
    from frappe.model.naming import parse_naming_series
    
    # 1. Get next invoice number
    next_no = parse_naming_series(naming_series)
    
    # 2. Get series-specific defaults from SSPL Billing Settings
    settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
    row = next((r for r in settings.billing_series if r.series == naming_series), None)
    
    # 3. Get user-specific defaults (if any)
    user_row = next((r for r in settings.user_series if r.user == frappe.session.user), None)
    
    return {
        "invoice_no": next_no,
        "price_list": row.price_list if row and row.price_list else "Standard Selling",
        "tax_template": row.tax_template if row and row.tax_template else "",
        "warehouse": (user_row.warehouse if user_row and user_row.warehouse else ""),
        "cost_center": (user_row.cost_center if user_row and user_row.cost_center else ""),
    }
