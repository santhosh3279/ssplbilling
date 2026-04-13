import json
import frappe
from collections import OrderedDict

@frappe.whitelist()
def get_ledger(ledger_name, ledger_type="Customer", from_date=None, to_date=None):
    """Return GL Entry rows for a ledger (Customer, Supplier, Employee, or Account) with a running balance."""
    if not ledger_name:
        frappe.throw("ledger_name is required")

    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -90)

    # Resolve display name
    if ledger_type == "Customer":
        filter_sql = "party_type = 'Customer' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Supplier":
        filter_sql = "party_type = 'Supplier' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Employee":
        filter_sql = "party_type = 'Employee' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    else:
        filter_sql = "account = %s AND (party IS NULL OR party = '')"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)

    # Opening balance
    opening_rows = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance
        FROM `tabGL Entry`
        WHERE {filter_sql} AND is_cancelled = 0 AND posting_date < %s
        """,
        params,
        as_dict=True,
    )
    opening_balance = float(opening_rows[0].balance if opening_rows else 0)

    # Detail rows
    entries_raw = frappe.db.sql(
        f"""
        SELECT posting_date, voucher_type, voucher_no, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE {filter_sql} AND is_cancelled = 0 AND posting_date >= %s AND posting_date <= %s
        ORDER BY posting_date ASC, creation ASC
        """,
        detail_params,
        as_dict=True,
    )

    voucher_groups = OrderedDict()
    for row in entries_raw:
        key = row.voucher_no
        if key not in voucher_groups:
            voucher_groups[key] = {
                "date": str(row.posting_date),
                "voucher_type": row.voucher_type,
                "voucher_no": row.voucher_no,
                "debit": 0.0,
                "credit": 0.0,
                "remarks": row.remarks or "",
            }
        voucher_groups[key]["debit"] += float(row.debit or 0)
        voucher_groups[key]["credit"] += float(row.credit or 0)

    balance = opening_balance
    entries = []
    for group in voucher_groups.values():
        balance += group["debit"] - group["credit"]
        entries.append({
            "date": group["date"],
            "voucher_type": group["voucher_type"],
            "voucher_no": group["voucher_no"],
            "debit": round(group["debit"], 2),
            "credit": round(group["credit"], 2),
            "balance": round(balance, 2),
            "remarks": group["remarks"],
        })

    return {
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(balance, 2),
        "entries": entries,
    }

@frappe.whitelist()
def get_customer_ledger(customer, from_date=None, to_date=None):
    return get_ledger(customer, "Customer", from_date, to_date)

@frappe.whitelist()
def get_outstanding_invoices(customer):
    """Return submitted Sales Invoices with outstanding balance."""
    return frappe.get_all("Sales Invoice", 
        filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]}, 
        fields=["name", "posting_date", "grand_total", "outstanding_amount"], 
        limit=50
    )

@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry."""
    if not data: data = frappe.form_dict.get("data") or dict(frappe.form_dict)
    if isinstance(data, str): data = json.loads(data)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = data.get("payment_type") or "Receive"
    pe.party_type = data.get("party_type") or "Customer"
    pe.party = data.get("party") or data.get("customer")
    pe.paid_amount = float(data.get("amount") or 0)
    pe.received_amount = pe.paid_amount
    pe.mode_of_payment = data.get("mode_of_payment") or "Cash"
    
    # Party Account (Debtors/Creditors) override
    if data.get("account"):
        pe.party_account = data.get("account")
            
    pe.insert()
    pe.submit()
    return {"payment_entry": pe.name}

@frappe.whitelist()
def search_suppliers(query=""):
    from ssplbilling.api.supplier_creator_api import search_suppliers as _impl
    return _impl(query)

@frappe.whitelist()
def search_accounts(query="", account_type=None):
    """Search chart of accounts."""
    filters = [["disabled", "=", 0], ["is_group", "=", 0]]
    if account_type: filters.append(["account_type", "=", account_type])
    if query: filters.append(["account_name", "like", f"%{query}%"])
    return frappe.get_all("Account", filters=filters, fields=["name", "account_name"], limit=25)
