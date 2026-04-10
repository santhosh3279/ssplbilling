import frappe
import json
import re
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows

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
    doc.naming_series = payload.get("series")

    _apply_payload_to_doc(doc, payload)
    doc.insert(ignore_permissions=True)

    return {"status": "success", "name": doc.name}


def _apply_payload_to_doc(doc, payload):
    """Shared helper: populate a Sales Invoice doc from the given payload dict."""
    doc.customer = payload.get("customer")
    doc.set_posting_time = 1
    doc.posting_date = payload.get("posting_date")
    doc.selling_price_list = payload.get("price_list")
    doc.cost_center = payload.get("cost_center")
    doc.ignore_pricing_rule = 1

    discount_pct = frappe.utils.flt(payload.get("discount_pct"))
    discount_amt = frappe.utils.flt(payload.get("discount_amt"))
    doc.additional_discount_percentage = discount_pct if discount_pct > 0 else 0
    doc.discount_amount = discount_amt if discount_amt > 0 else 0

    doc.is_return = frappe.utils.cint(payload.get("is_return"))
    doc.taxes_and_charges = payload.get("tax_template")

    cost_center = payload.get("cost_center")
    warehouse = payload.get("warehouse")
    income_account = payload.get("income_account")

    # Clear address/contact fields so Frappe re-derives them from the customer;
    # stale values from a previous customer cause a ValidationError.
    doc.customer_address = None
    doc.shipping_address_name = None
    doc.contact_person = None

    doc.set("items", [])
    for item in payload.get("items", []):
        rate = frappe.utils.flt(item.get("rate"))
        price_list_rate = frappe.utils.flt(item.get("price_list_rate", rate))
        item_row = {
            "item_code": item.get("item_code"),
            "qty": item.get("qty"),
            "rate": rate,
            "price_list_rate": price_list_rate,
            "discount_percentage": frappe.utils.flt(item.get("discount")),
            "warehouse": warehouse,
            "income_account": income_account,
            "cost_center": cost_center,
        }
        if frappe.utils.cint(item.get("is_free_item")) == 1:
            item_row["is_free_item"] = 1
        if frappe.get_meta("Sales Invoice Item").has_field("allow_zero_valuation_rate"):
            item_row["allow_zero_valuation_rate"] = 1
        doc.append("items", item_row)

    doc.set_missing_values()
    if doc.taxes_and_charges:
        doc.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", doc.taxes_and_charges) or [])

    for charge in payload.get("additional_charges", []):
        amt = frappe.utils.flt(charge.get("tax_amount"))
        if amt == 0:
            continue
        doc.append("taxes", {
            "charge_type": charge.get("charge_type", "Actual"),
            "account_head": charge.get("account_head"),
            "tax_amount": amt,
            "description": charge.get("description", ""),
            "cost_center": cost_center or None,
        })

    is_inclusive = frappe.utils.cint(payload.get("is_inclusive_tax"))
    if cost_center or is_inclusive == 1:
        for tax in doc.get("taxes", []):
            if cost_center and not tax.cost_center:
                tax.cost_center = cost_center
            if is_inclusive == 1 and tax.account_head and "GST" in tax.account_head.upper():
                tax.included_in_print_rate = 1

    doc.calculate_taxes_and_totals()

    if payload.get("custom_customer_name"):
        doc.custom_customer_name = payload.get("custom_customer_name")
    if payload.get("custom_address_line1"):
        doc.custom_address_line1 = payload.get("custom_address_line1")
    if payload.get("custom_address_line2"):
        doc.custom_address_line2 = payload.get("custom_address_line2")
    if payload.get("custom_mobile_number"):
        doc.custom_mobile_number = payload.get("custom_mobile_number")

    doc.set("incentive_system", [])
    for row in payload.get("incentive_rows", []):
        if row.get("employee") and row.get("role"):
            doc.append("incentive_system", {
                "employee": row.get("employee"),
                "role": row.get("role"),
                "points": frappe.utils.flt(row.get("points") or 0),
            })


@frappe.whitelist()
def update_sales_invoice(invoice_name, payload):
    """Update an existing draft Sales Invoice with new payload."""
    if isinstance(payload, str):
        payload = json.loads(payload)

    doc = frappe.get_doc("Sales Invoice", invoice_name)
    if doc.docstatus != 0:
        frappe.throw(f"Cannot update a submitted or cancelled invoice: {invoice_name}")

    _apply_payload_to_doc(doc, payload)
    doc.save(ignore_permissions=True)

    return {"status": "success", "name": doc.name}
