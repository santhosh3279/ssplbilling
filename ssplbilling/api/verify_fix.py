import frappe
from ssplbilling.api.cashier_api import submit_invoice_with_payment, update_invoice_advances

def test_new_fix():
    print("Testing fix with EOW00187...")
    
    # 1. Setup EOW00187 with advance EOW00189
    update_invoice_advances("EOW00187", allocations=[{
        "reference_type": "Sales Invoice",
        "reference_name": "EOW00189",
        "allocated_amount": 341.0
    }])
    
    # 2. Submit
    data = {
        "invoice_name": "EOW00187",
        "cash_amount": 0,
        "upi_amount": 0,
        "is_credit": True
    }
    
    try:
        res = submit_invoice_with_payment(data)
        print(f"Success: {res}")
        
        si = frappe.get_doc("Sales Invoice", "EOW00187")
        print(f"EOW00187 Outstanding: {si.outstanding_amount}")
        
        ret_si = frappe.get_doc("Sales Invoice", "EOW00189")
        print(f"EOW00189 Outstanding: {ret_si.outstanding_amount}")
        
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

def fix_eow00188():
    print("\nFixing EOW00188 (applying the missing advance)...")
    si = frappe.get_doc("Sales Invoice", "EOW00188")
    if si.docstatus == 1 and si.outstanding_amount == si.grand_total:
        from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import reconcile_dr_cr_note
        
        reconcile_args = [frappe._dict({
            "voucher_type": "Sales Invoice",
            "voucher_no": "EOW00189",
            "allocated_amount": 341.0,
            "unadjusted_amount": 341.0,
            "dr_or_cr": "credit_in_account_currency",
            "account": si.debit_to,
            "party_type": "Customer",
            "party": si.customer,
            "against_voucher_type": "Sales Invoice",
            "against_voucher": si.name,
            "currency": si.currency,
            "exchange_rate": si.conversion_rate,
            "cost_center": si.cost_center,
            "company": si.company
        })]
        
        reconcile_dr_cr_note(reconcile_args, si.company)
        si.reload()
        print(f"EOW00188 Outstanding now: {si.outstanding_amount}")
    else:
        print("EOW00188 already fixed or in unexpected state.")

if __name__ == "__main__":
    test_new_fix()
    fix_eow00188()
