import frappe
import json

def check_je_links(je_name):
    # Check Payment Ledger for allocations against this JE or by this JE
    links = frappe.get_all('Payment Ledger', 
        filters={'against_voucher_no': je_name, 'delinked': 0}, 
        fields=['voucher_no', 'voucher_type', 'amount', 'against_voucher_no'])
    
    # Also check where this JE is the one doing the allocation
    allocations = frappe.get_all('Payment Ledger',
        filters={'voucher_no': je_name, 'delinked': 0},
        fields=['against_voucher_no', 'against_voucher_type', 'amount'])
    
    return {
        'links_against_this_je': links,
        'allocations_made_by_this_je': allocations
    }

if __name__ == "__main__":
    je_name = 'ACC-JV-2026-00080'
    result = check_je_links(je_name)
    print(json.dumps(result, indent=4))
