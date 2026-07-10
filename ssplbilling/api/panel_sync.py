import datetime

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

# Superset of the sidebar list fields across the bill doctypes (see e.g.
# sales.get_sales_invoices). Fields a doctype doesn't have are simply skipped,
# so one list serves Sales Invoice, Purchase Invoice, orders and quotations.
BILL_ROW_FIELDS = [
	"name",
	"company",
	"customer",
	"customer_name",
	"custom_customer_name",
	"supplier",
	"supplier_name",
	"posting_date",
	"transaction_date",
	"grand_total",
	"rounded_total",
	"outstanding_amount",
	"status",
	"modified",
	"docstatus",
	"mop",
]


def _bill_row(doc):
	"""Build the sidebar list row for a bill doc, mirroring the fields the
	list endpoints return so clients can upsert it into their cached panel
	without refetching."""
	row = {}
	for field in BILL_ROW_FIELDS:
		value = getattr(doc, field, None)
		if value is None:
			continue
		if isinstance(value, (datetime.date, datetime.datetime)):
			value = str(value)
		row[field] = value
	for field in ("grand_total", "rounded_total", "outstanding_amount"):
		if field in row:
			row[field] = float(row[field] or 0)
	return row


def publish_bill_panel_update(doc, method=None):
	"""Doc event: whenever one of the bill doctypes is created, updated, submitted,
	cancelled or deleted, broadcast the changed row so every other client can patch
	its modify-bill panel in place — but only if that client is currently showing the
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
		"event": method,
		"row": _bill_row(doc),
	}
	frappe.publish_realtime("bill_panel_update", payload, after_commit=True)
