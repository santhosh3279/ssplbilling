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
def get_outstanding_invoices(party, party_type="Customer"):
	"""Return all unlinked outstanding GL transactions for a party.

	Groups every GL Entry by its settlement target (against_voucher when set,
	otherwise voucher_no) so that payments correctly reduce the balance of the
	document they are applied against.

	Receipt  (Customer) → vouchers where net debit  > 0  (customer owes us)
	Payment  (Supplier) → vouchers where net credit > 0  (we owe supplier)

	Covers all voucher types: Sales Invoice, Purchase Invoice, Journal Entry, etc.
	"""
	if party_type == "Customer":
		net_expr  = "SUM(gle.debit  - gle.credit)"
		orig_expr = "SUM(GREATEST(gle.debit,  0))"
	else:
		net_expr  = "SUM(gle.credit - gle.debit)"
		orig_expr = "SUM(GREATEST(gle.credit, 0))"

	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(gle.against_voucher_type, ''), gle.voucher_type)  AS voucher_type,
			COALESCE(NULLIF(gle.against_voucher, ''),      gle.voucher_no)    AS voucher_no,
			MAX(gle.posting_date)  AS posting_date,
			{orig_expr}            AS invoice_amount,
			{net_expr}             AS outstanding_amount
		FROM `tabGL Entry` gle
		WHERE gle.party_type    = %s
			AND gle.party       = %s
			AND gle.is_cancelled = 0
		GROUP BY
			COALESCE(NULLIF(gle.against_voucher_type, ''), gle.voucher_type),
			COALESCE(NULLIF(gle.against_voucher, ''),      gle.voucher_no)
		HAVING outstanding_amount > 0.01
		ORDER BY posting_date DESC
		LIMIT 200
		""",
		(party_type, party),
		as_dict=True,
	)

	return [
		frappe._dict({
			"voucher_type":       row.voucher_type,
			"voucher_no":         row.voucher_no,
			"posting_date":       row.posting_date,
			"due_date":           row.posting_date,
			"invoice_amount":     float(row.invoice_amount     or 0),
			"outstanding_amount": float(row.outstanding_amount or 0),
		})
		for row in rows
	]

@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry."""
    if not data: data = frappe.form_dict.get("data") or dict(frappe.form_dict)
    if isinstance(data, str): data = json.loads(data)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = data.get("payment_type") or "Receive"
    pe.party_type = data.get("party_type") or "Customer"
    pe.party = data.get("party") or data.get("customer") or data.get("customer_id")
    pe.paid_amount = float(data.get("amount") or 0)
    pe.received_amount = pe.paid_amount
    pe.mode_of_payment = data.get("mode_of_payment") or data.get("mop_account") or "Cash"
    pe.reference_no = data.get("reference_no")
    pe.reference_date = data.get("reference_date")
    pe.posting_date = data.get("posting_date") or frappe.utils.today()
    
    # Explicitly set currencies and exchange rates to INR
    pe.paid_from_account_currency = "INR"
    pe.paid_to_account_currency = "INR"
    pe.source_exchange_rate = 1.0
    pe.target_exchange_rate = 1.0
    
    # RESOLVE ACCOUNTS
    # 1. Resolve MOP account (Bank/Cash)
    mop_account = data.get("mop_account") or data.get("account")
    if not mop_account and pe.mode_of_payment:
        mop_account = _get_mop_account(pe.mode_of_payment)

    # 2. Resolve Party account (Debtors/Creditors)
    # If account was provided but we used it as mop_account, we should resolve party_account automatically
    party_account = data.get("party_account")
    if not party_account:
        # If 'account' was provided, check if it looks like a party account or MOP account
        # But to be safe and follow the new convention, we resolve it from party if not explicitly given as party_account
        party_account = _get_party_account(pe.party_type, pe.party)

    if pe.payment_type == "Receive":
        pe.paid_from = party_account
        pe.paid_to = mop_account
    else: # Pay
        pe.paid_from = mop_account
        pe.paid_to = party_account
            
    # If mode_of_payment was passed as an account, try to find its parent MOP name
    # or keep it as is if it's already a valid MOP
    if pe.mode_of_payment:
        mop_name = frappe.db.get_value("Mode of Payment Account", {"default_account": pe.mode_of_payment}, "parent")
        if mop_name:
            pe.mode_of_payment = mop_name
            
    for ref in (data.get("references") or []):
        pe.append("references", {
            "reference_doctype": ref.get("reference_doctype"),
            "reference_name": ref.get("reference_name"),
            "total_amount": float(ref.get("total_amount") or 0),
            "outstanding_amount": float(ref.get("outstanding_amount") or 0),
            "allocated_amount": float(ref.get("allocated_amount") or 0),
        })

    if data.get("cost_center"):
        pe.cost_center = data["cost_center"]

    pe.insert()
    pe.submit()
    return {"payment_entry": pe.name}

def _get_party_account(party_type, party):
    """Get the default receivable/payable account for a party."""
    from erpnext.accounts.party import get_party_account
    company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value('Global Defaults', 'default_company')
    return get_party_account(party_type, party, company)

def _get_mop_account(mode_of_payment):
    """Get the default bank/cash account for a mode of payment."""
    if not mode_of_payment: return None
    company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value('Global Defaults', 'default_company')
    return frappe.db.get_value("Mode of Payment Account", 
        {"parent": mode_of_payment, "company": company}, "default_account")

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
