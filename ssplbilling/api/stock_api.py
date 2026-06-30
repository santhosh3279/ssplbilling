import frappe
from ssplbilling.api.stock_utils import get_draft_invoice_qtys_batch


@frappe.whitelist()
def get_warehouse_stock(item_code):
	"""Return warehouse-wise available stock for a single item (actual_qty minus draft invoices)."""
	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code},
		fields=["warehouse", "actual_qty"],
		order_by="actual_qty desc",
	)
	if not bins:
		return []

	draft_qtys = get_draft_invoice_qtys_batch()
	result = []
	for b in bins:
		draft = draft_qtys.get((item_code, b.warehouse), 0.0)
		qty = float(b.actual_qty or 0) - draft
		result.append({"warehouse": b.warehouse, "qty": qty})

	return result
