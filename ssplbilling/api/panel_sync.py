import frappe

# Doctypes whose modify-bill panels are kept in sync across clients over websocket.
# Each entry maps a Frappe doctype to the front-end page that renders its panel.
BILL_PANEL_DOCTYPES = {
	"Sales Invoice",
	"Purchase Invoice",
	"Sales Order",
	"Purchase Order",
	"Quotation",
}


def publish_bill_panel_update(doc, method=None):
	"""Doc event: whenever one of the bill doctypes is created, updated, submitted,
	cancelled or deleted, broadcast a lightweight signal so every other client can
	refresh its modify-bill panel — but only if that client is currently showing the
	same naming_series (the front-end gates on this).

	Payload is fully known at hook time, so we broadcast with after_commit=True (same
	pattern as stock_update / item_price_update) — the row is committed before the
	event fires, so a client's refetch sees the change."""
	if not doc or not doc.name:
		return

	payload = {
		"doctype": doc.doctype,
		"name": doc.name,
		"naming_series": getattr(doc, "naming_series", None),
		"docstatus": doc.docstatus,
	}
	frappe.publish_realtime("bill_panel_update", payload, after_commit=True)
