import frappe
import re

@frappe.whitelist()
def get_sales_invoices(query="", limit=100, posting_date=None, naming_series=None, draft_only=False):
    """List Sales Invoices for the sidebar bill panel."""
    draft_only = frappe.parse_json(draft_only)

    filters = [["docstatus", "!=", 2], ["posting_date", "=", posting_date or frappe.utils.today()]]

    if draft_only:
        filters.append(["docstatus", "=", 0])

    if naming_series:
        filters.append(["naming_series", "=", naming_series])

    or_filters = []
    if query:
        flexible_query = "%" + "%".join(re.findall(r'[A-Za-z]+|\d+', query)) + "%"
        or_filters = [
            ["name", "like", flexible_query],
            ["customer_name", "like", f"%{query}%"],
            ["custom_customer_name", "like", f"%{query}%"]
        ]

    invoices = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "customer", "customer_name", "posting_date", "grand_total", "outstanding_amount", "status", "modified", "docstatus", "custom_customer_name"],
        limit=int(limit),
        order_by="name desc",
    )

    for inv in invoices:
        inv["grand_total"] = float(inv["grand_total"] or 0)
        inv["outstanding_amount"] = float(inv["outstanding_amount"] or 0)

    return invoices
