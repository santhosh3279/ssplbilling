import frappe
from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import reconcile_dr_cr_note

def test_reconcile():
    # EOW00188 is the invoice (Draft)
    # EOW00189 is the return (Submitted, -341 outstanding)
    
    # We need EOW00188 to be submitted first.
    si = frappe.get_doc("Sales Invoice", "EOW00188")
    
    # Remove advances for a moment to allow submission
    original_advances = si.advances
    si.advances = []
    si.submit()
    
    print(f"Submitted {si.name}. Outstanding: {si.outstanding_amount}")
    
    # Now reconcile against EOW00189
    # We need to build the args for reconcile_dr_cr_note
    
    # dr_cr_notes should be a list of frappe._dict
    entry = frappe._dict({
        "voucher_type": "Sales Invoice",
        "voucher_no": "EOW00189",
        "allocated_amount": 341.0,
        "unadjusted_amount": 341.0, # abs of outstanding
        "dr_or_cr": "credit_in_account_currency", # because it's a return for a customer? 
        # Wait, reconcile_dr_cr_note uses dr_or_cr to decide which side is which.
        # If it's a Sales Invoice (Credit Note), it's usually a Credit to the Customer?
        # No, a Return Sales Invoice has a Credit balance for the customer.
        # To reconcile it against a Debit (Invoice), we need to Debit the Customer (Return side) and Credit the Customer (Invoice side)?
        # Wait, let's check reconcile_dr_cr_note logic again.
    })
    
    # Actually, let's see how update_against_document_in_jv builds it.
    # if self.doctype == "Sales Invoice":
    #    party_type = "Customer"
    #    party = self.customer
    #    party_account = self.debit_to
    #    dr_or_cr = "credit_in_account_currency"
    
    entry.update({
        "account": si.debit_to,
        "party_type": "Customer",
        "party": si.customer,
        "against_voucher_type": "Sales Invoice",
        "against_voucher": si.name,
        "currency": si.currency,
        "exchange_rate": si.conversion_rate,
        "cost_center": si.cost_center,
        "dr_or_cr": "credit_in_account_currency"
    })
    
    reconcile_dr_cr_note([entry], si.company)
    
    si.reload()
    print(f"After reconciliation. Outstanding: {si.outstanding_amount}")

if __name__ == "__main__":
    # Use a transaction so we can rollback if needed
    frappe.db.begin()
    try:
        test_reconcile()
        frappe.db.rollback() # Rollback for now
        print("Test completed and rolled back.")
    except Exception as e:
        frappe.db.rollback()
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
