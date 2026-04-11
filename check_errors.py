import frappe
frappe.init(site="erp.localhost")
frappe.connect()
errors = frappe.get_all("Error Log", fields=["method", "error", "creation"], order_by="creation desc", limit=1)
if errors:
    print(errors[0].error)
else:
    print("No errors found")
