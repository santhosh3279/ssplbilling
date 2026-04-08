import frappe
import json
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

@frappe.whitelist()
def post_sales_invoice(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)

    doc = frappe.new_doc("Sales Invoice")
    
    # Header logic
    doc.naming_series = payload.get("series")
    doc.customer = payload.get("customer")
    doc.set_posting_time = 1
    doc.posting_date = payload.get("posting_date")
    doc.selling_price_list = payload.get("price_list")
    doc.ignore_pricing_rule = 1
    
    # Discount logic
    discount_pct = frappe.utils.flt(payload.get("discount_pct"))
    discount_amt = frappe.utils.flt(payload.get("discount_amt"))
    if discount_pct > 0:
        doc.additional_discount_percentage = discount_pct
    if discount_amt > 0:
        doc.discount_amount = discount_amt
        
    doc.taxes_and_charges = payload.get("tax_template")
    
    # Items logic
    cost_center = payload.get("cost_center")
    warehouse = payload.get("warehouse")
    income_account = payload.get("income_account")
    
    for item in payload.get("items", []):
        item_row = {
            "item_code": item.get("item_code"),
            "qty": item.get("qty"),
            "rate": item.get("rate"),
            "warehouse": warehouse,
            "income_account": income_account,
            "cost_center": cost_center
        }
        # In case we pass price list rate
        if item.get("price_list_rate"):
            item_row["price_list_rate"] = item.get("price_list_rate")
        doc.append("items", item_row)
        
    # Auto populate taxes
    doc.set_missing_values()
    if doc.taxes_and_charges:
        doc.append_taxes_from_master()
    
    # Inclusive tax logic for GST
    is_inclusive = frappe.utils.cint(payload.get("is_inclusive_tax"))
    if is_inclusive == 1:
        for tax in doc.get("taxes", []):
            if tax.account_head and "GST" in tax.account_head.upper():
                tax.included_in_print_rate = 1

    doc.calculate_taxes_and_totals()
    doc.insert(ignore_permissions=True)
    
    return {"status": "success", "name": doc.name}
