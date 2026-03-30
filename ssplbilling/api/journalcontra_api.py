import frappe
import json

def _get_party_account(party_type, party):
    """Get the default receivable/payable account for a party."""
    from erpnext.accounts.party import get_party_account
    return get_party_account(party_type, party, frappe.defaults.get_global_default("company"))

@frappe.whitelist()
def get_journal_entry_types():
    """Return available voucher types for Journal Entry."""
    meta = frappe.get_meta("Journal Entry")
    options = meta.get_field("voucher_type").options
    return [opt.strip() for opt in options.split("\n") if opt.strip()]

@frappe.whitelist()
def create_journal_contra_entry(data):
    """Create and submit a Journal Entry or Contra."""
    if isinstance(data, str):
        data = json.loads(data)
        
    accounts = data.get("accounts") or []
    if not accounts:
        frappe.throw("At least two accounts are required for a Journal Entry")
        
    company = frappe.defaults.get_global_default("company")
    je = frappe.new_doc("Journal Entry")
    voucher_type = data.get("voucher_type") or "Journal Entry"
    # Map frontend shorthand to ERPNext's exact select option
    if voucher_type == "Contra":
        voucher_type = "Contra Entry"
    je.voucher_type = voucher_type
    je.posting_date = data.get("posting_date") or frappe.utils.today()
    je.company = company
    je.user_remark = data.get("user_remark") or ""
    
    if data.get("cheque_no"):
        je.cheque_no = data.get("cheque_no")
        je.cheque_date = data.get("posting_date") or frappe.utils.today()

    for acc in accounts:
        row_account = acc.get("account")
        account_type = acc.get("account_type")
        party_type = None
        party = None
        
        # If it's a Customer, Supplier, or Employee, we need their receivable/payable account
        if account_type in ["Customer", "Supplier", "Employee"]:
            party_type = account_type
            party = row_account
            row_account = _get_party_account(party_type, party)
            
        debit = float(acc.get("debit_in_account_currency") or 0)
        credit = float(acc.get("credit_in_account_currency") or 0)

        # Primary Row
        je.append("accounts", {
            "account": row_account,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,
            "party_type": party_type,
            "party": party,
            "cost_center": acc.get("cost_center"),
            "user_remark": acc.get("user_remark")
        })

        # If Opening Entry, user wants a second balancing row for each input
        if voucher_type == "Opening Entry":
            je.append("accounts", {
                "account": row_account,
                "debit_in_account_currency": credit, # Flipped
                "credit_in_account_currency": debit, # Flipped
                "party_type": party_type,
                "party": party,
                "cost_center": acc.get("cost_center"),
                "user_remark": (acc.get("user_remark") or "") + " (Balancing Row)"
            })
        
    je.insert()
    je.submit()
    return {"name": je.name, "status": "Submitted"}
