import frappe

def test():
    from ssplbilling.api.SaleEntry_api import get_naming_series as get_sales_series
    from ssplbilling.api.purchase_api import get_naming_series as get_purchase_series
    
    print("Sales:", get_sales_series())
    print("Purchase:", get_purchase_series())

