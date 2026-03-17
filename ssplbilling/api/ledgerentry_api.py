import frappe
import json

def _get_party_account(party_type, party):
    """Get the default receivable/payable account for a party."""
    from erpnext.accounts.party import get_party_account
    return get_party_account(party_type, party, frappe.defaults.get_global_default("company"))

def _get_mop_account(mode_of_payment):
    """Get the default bank/cash account for a mode of payment."""
    company = frappe.defaults.get_global_default("company")
    account = frappe.db.get_value("Mode of Payment Account", 
        {"parent": mode_of_payment, "company": company}, "default_account")
    
    if not account:
        # Fallback to general company defaults
        if "Cash" in mode_of_payment:
            account = frappe.db.get_value("Company", company, "default_cash_account")
        else:
            account = frappe.db.get_value("Company", company, "default_bank_account")
            
    return account

@frappe.whitelist()
def get_outstanding_invoices(party, party_type="Customer", mop=None):
    """Fetch outstanding invoices/bills for a given party, including current balance and MoP balance."""
    if not party:
        return {"invoices": [], "balance": 0, "mop_balance": 0}

    # Fetch ledger balance
    balance = 0
    if party_type in ["Customer", "Supplier", "Employee"]:
        balance_row = frappe.db.sql(
            """
            SELECT COALESCE(SUM(debit) - SUM(credit), 0) as balance
            FROM `tabGL Entry`
            WHERE party_type = %s AND party = %s AND is_cancelled = 0
            """,
            (party_type, party),
            as_dict=True,
        )
        balance = float(balance_row[0].balance or 0) if balance_row else 0.0
    else:
        # Fallback for Account type if needed
        balance_row = frappe.db.sql(
            """
            SELECT COALESCE(SUM(debit) - SUM(credit), 0) as balance
            FROM `tabGL Entry`
            WHERE account = %s AND (party IS NULL OR party = '') AND is_cancelled = 0
            """,
            (party,),
            as_dict=True,
        )
        balance = float(balance_row[0].balance or 0) if balance_row else 0.0

    # Fetch MoP Balance
    mop_balance = 0
    if mop:
        mop_account = _get_mop_account(mop)
        if mop_account:
            mop_bal_row = frappe.db.sql(
                """
                SELECT COALESCE(SUM(debit) - SUM(credit), 0) as balance
                FROM `tabGL Entry`
                WHERE account = %s AND is_cancelled = 0
                """,
                (mop_account,),
                as_dict=True,
            )
            mop_balance = float(mop_bal_row[0].balance or 0) if mop_bal_row else 0.0

    if party_type == "Employee":
        claims = frappe.get_all(
            "Expense Claim",
            filters={"employee": party, "docstatus": 1, "status": ["!=", "Paid"]},
            fields=["name", "posting_date", "total_claimed_amount as grand_total", "total_claimed_amount", "total_amount_reimbursed"],
            order_by="posting_date desc",
        )
        for c in claims:
            c["outstanding_amount"] = float(c.get("total_claimed_amount") or 0) - float(c.get("total_amount_reimbursed") or 0)
        
        invoices = [c for c in claims if c["outstanding_amount"] > 0]
        return {"invoices": invoices, "balance": balance, "mop_balance": mop_balance}

    doctype = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
    party_field = "customer" if party_type == "Customer" else "supplier"

    invoices = frappe.get_all(
        doctype,
        filters={party_field: party, "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "posting_date", "grand_total", "outstanding_amount"],
        order_by="posting_date desc",
    )
    
    return {"invoices": invoices, "balance": balance, "mop_balance": mop_balance}

@frappe.whitelist()
def get_mop_balances(mops):
    """Fetch current ledger balances for a list of modes of payment."""
    if isinstance(mops, str):
        mops = json.loads(mops)
    
    balances = {}
    for m in mops:
        account = _get_mop_account(m)
        if account:
            bal_row = frappe.db.sql(
                """
                SELECT COALESCE(SUM(debit) - SUM(credit), 0) as balance
                FROM `tabGL Entry`
                WHERE account = %s AND is_cancelled = 0
                """,
                (account,),
                as_dict=True,
            )
            balances[m] = float(bal_row[0].balance or 0) if bal_row else 0.0
        else:
            balances[m] = 0.0
    return balances

@frappe.whitelist()
def create_payment_entry(data):
    """Create and submit a Payment Entry."""
    if isinstance(data, str):
        data = json.loads(data)
        
    payment_type = data.get("payment_type") # 'Receive' or 'Pay'
    party_type = data.get("party_type") # 'Customer' or 'Supplier'
    party = data.get("party")
    mop = data.get("mode_of_payment") or "Cash"
    amount = float(data.get("amount") or 0)
    company = frappe.defaults.get_global_default("company")

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.posting_date = data.get("date") or frappe.utils.today()
    pe.company = company
    
    pe.paid_amount = amount
    pe.received_amount = amount
    pe.mode_of_payment = mop
    
    # Set exchange rates to 1.0 to avoid conversion issues
    pe.source_exchange_rate = 1.0
    pe.target_exchange_rate = 1.0
    
    # RESOLVE ACCOUNTS
    party_account = _get_party_account(party_type, party)
    mop_account = _get_mop_account(mop)
    
    if payment_type == "Receive":
        pe.paid_from = data.get("paid_from") or party_account
        pe.paid_to = data.get("paid_to") or mop_account
    else: # Pay
        pe.paid_from = data.get("paid_from") or mop_account
        pe.paid_to = data.get("paid_to") or party_account

    # Explicitly set currencies to avoid MandatoryError
    pe.paid_from_account_currency = frappe.db.get_value("Account", pe.paid_from, "account_currency")
    pe.paid_to_account_currency = frappe.db.get_value("Account", pe.paid_to, "account_currency")
        
    pe.reference_no = data.get("reference_no")
    pe.reference_date = data.get("reference_date") or pe.posting_date
    pe.remarks = data.get("remarks")
    
    # Link to invoices if provided
    references = data.get("references") or []
    if not references and data.get("invoice_name"):
        references = [{"name": data["invoice_name"], "amount": amount}]

    ref_doctype = (
        "Sales Invoice" if pe.party_type == "Customer"
        else "Expense Claim" if pe.party_type == "Employee"
        else "Purchase Invoice"
    )
    for ref in references:
        pe.append("references", {
            "reference_doctype": ref_doctype,
            "reference_name": ref["name"],
            "allocated_amount": float(ref.get("amount") or 0)
        })

    pe.insert()
    pe.submit()
    
    return {"name": pe.name, "status": "Submitted"}

@frappe.whitelist()
def search_parties(query, party_type="Customer"):
    """Search for Customer or Supplier."""
    doctype = "Customer" if party_type == "Customer" else "Supplier"
    name_field = "customer_name" if party_type == "Customer" else "supplier_name"
    
    filters = {
        "disabled": 0,
        name_field: ["like", f"%{query}%"]
    }
    
    return frappe.get_all(
        doctype,
        filters=filters,
        fields=["name", f"{name_field} as label"],
        limit=20
    )
