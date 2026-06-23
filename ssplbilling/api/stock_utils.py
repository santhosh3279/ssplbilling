import frappe

def get_draft_invoice_qty(item_code, warehouse=None):
	"""Return the sum of quantities of an item in draft Sales Invoices."""
	filters = {
		"parenttype": "Sales Invoice",
		"docstatus": 0,
		"item_code": item_code
	}
	if warehouse:
		filters["warehouse"] = warehouse
	
	rows = frappe.get_all(
		"Sales Invoice Item",
		filters=filters,
		fields=["qty"]
	)
	return sum(float(row.qty or 0) for row in rows)

def get_draft_invoice_qtys_batch(warehouse=None):
	"""Return a map of {(item_code, warehouse): qty} for all draft Sales Invoices."""
	filters = {"docstatus": 0}
	if warehouse:
		filters["warehouse"] = warehouse
		
	rows = frappe.get_all(
		"Sales Invoice Item",
		filters=filters,
		fields=["item_code", "warehouse", "qty"]
	)
	
	qtys = {}
	for r in rows:
		key = (r.item_code, r.warehouse)
		qtys[key] = qtys.get(key, 0.0) + float(r.qty or 0)
	return qtys
