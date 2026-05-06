import frappe
from ssplbilling.api.cashier_api import submit_invoice_with_payment

def run():
    # Attempt to submit EOW00188
    data = {
        "invoice_name": "EOW00188",
        "cash_amount": 0,
        "upi_amount": 0,
        "is_credit": True # Just try to submit as credit to see if advances cause issue
    }
    try:
        res = submit_invoice_with_payment(data)
        print(f"Success: {res}")
    except Exception as e:
        print(f"Failed as expected: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
