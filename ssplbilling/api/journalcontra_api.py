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
    voucher_type = data.get("voucher_type") or "Journal Entry"
    # Map frontend shorthand to ERPNext's exact select option
    if voucher_type == "Contra":
        voucher_type = "Contra Entry"
    
    posting_date = data.get("posting_date") or frappe.utils.today()
    user_remark = data.get("user_remark") or ""
    cheque_no = data.get("cheque_no")

    def _create_single_je(row_accounts):
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = voucher_type
        if voucher_type == "Opening Entry":
            je.is_opening = "Yes"
        je.posting_date = posting_date
        je.company = company
        je.user_remark = user_remark
        if cheque_no:
            je.cheque_no = cheque_no
            je.cheque_date = posting_date

        for acc in row_accounts:
            row_account = acc.get("account")
            account_type = acc.get("account_type")
            party_type = None
            party = None
            references = acc.get("references") or []

            if account_type in ["Customer", "Supplier", "Employee"]:
                party_type = account_type
                party = row_account
                row_account = _get_party_account(party_type, party)

            debit = float(acc.get("debit_in_account_currency") or 0)
            credit = float(acc.get("credit_in_account_currency") or 0)

            if references and party_type and voucher_type != "Opening Entry":
                is_credit_side = credit >= debit
                base_amount = credit if is_credit_side else debit
                total_ref_alloc = sum(float(r.get("alloc_amount") or 0) for r in references)

                for ref in references:
                    alloc = float(ref.get("alloc_amount") or 0)
                    if alloc < 0.005: continue
                    je.append("accounts", {
                        "account": row_account,
                        "debit_in_account_currency": 0 if is_credit_side else alloc,
                        "credit_in_account_currency": alloc if is_credit_side else 0,
                        "party_type": party_type,
                        "party": party,
                        "reference_type": ref.get("ref_type"),
                        "reference_name": ref.get("ref_name"),
                        "cost_center": acc.get("cost_center"),
                        "user_remark": acc.get("user_remark"),
                    })

                residual = round(base_amount - total_ref_alloc, 2)
                if residual > 0.005:
                    je.append("accounts", {
                        "account": row_account,
                        "debit_in_account_currency": 0 if is_credit_side else residual,
                        "credit_in_account_currency": residual if is_credit_side else 0,
                        "party_type": party_type,
                        "party": party,
                        "cost_center": acc.get("cost_center"),
                        "user_remark": acc.get("user_remark"),
                    })
            else:
                je.append("accounts", {
                    "account": row_account,
                    "debit_in_account_currency": debit,
                    "credit_in_account_currency": credit,
                    "party_type": party_type,
                    "party": party,
                    "cost_center": acc.get("cost_center"),
                    "user_remark": acc.get("user_remark")
                })

                if voucher_type == "Opening Entry":
                    temp_opening = frappe.db.get_value("Company", company, "default_opening_balance_equity_account") or "Temporary Opening - SSPL"
                    je.append("accounts", {
                        "account": temp_opening,
                        "debit_in_account_currency": credit,
                        "credit_in_account_currency": debit,
                        "cost_center": acc.get("cost_center"),
                        "user_remark": acc.get("user_remark") or user_remark
                    })
        
        je.insert()
        je.submit()
        return je.name

    created_names = []
    if voucher_type == "Opening Entry":
        # Create separate JE for each account row
        for single_acc in accounts:
            name = _create_single_je([single_acc])
            created_names.append(name)
    else:
        # Standard one-JE-for-all-rows behavior
        name = _create_single_je(accounts)
        created_names.append(name)

    return {"names": created_names, "status": "Submitted"}
