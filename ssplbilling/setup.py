import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELDS = {
	"Account": [
		{
			"fieldname": "custom_show_in_ledger_search",
			"label": "Show in Ledger Search",
			"fieldtype": "Check",
			"insert_after": "account_type",
			"default": "0",
			"description": "Show in billing ledger search even when not listed in SSPL Billing Settings Visible Accounts.",
		},
	],
	"Item": [
		{
			"fieldname": "custom_pricelist_percentages",
			"label": "Pricelist Percentages",
			"fieldtype": "Table",
			"options": "Item Price List Percentage",
			"insert_after": "custom_max_stock",
		},
		{
			"fieldname": "custom_competitive_item",
			"label": "Competitive Item",
			"fieldtype": "Link",
			"options": "Competitive Item",
			"insert_after": "custom_pricelist_percentages",
		},
		{
			"fieldname": "custom_max_stock",
			"label": "Max Stock",
			"fieldtype": "Float",
			"insert_after": "safety_stock",
		},
		{
			"fieldname": "custom_max_order_qty",
			"label": "Max Order Qty",
			"fieldtype": "Float",
			"insert_after": "min_order_qty",
		}
	],
	"Customer": [
		{
			"fieldname": "customer_print_name",
			"fieldtype": "Data",
			"label": "Customer Print Name",
			"insert_after": "customer_name",
			"translatable": 0,
		},
		{
			"fieldname": "pricelist_multiplication_factor",
			"label": "Pricelist multiplication factor",
			"fieldtype": "Float",
			"insert_after": "default_price_list",
		},
		{
			"fieldname": "whatsapp_enabled",
			"label": "WhatsApp Enabled",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "customer_print_name",
			"description": "Untick to stop using the saved WhatsApp number: sending a bill then asks for a number every time and keeps none.",
		},
		{
			"fieldname": "whatsapp_status",
			"label": "WhatsApp Status",
			"fieldtype": "Select",
			"options": "Not Checked\nValid\nInvalid",
			"default": "Not Checked",
			"insert_after": "whatsapp_enabled",
			"read_only": 1,
			"in_standard_filter": 1,
			"description": "Checked when the party is saved, on Check, or when a bill is sent. Stays Valid until a send fails or the number changes.",
		},
		{
			"fieldname": "whatsapp_verified_number",
			"label": "WhatsApp Number Checked",
			"fieldtype": "Data",
			"insert_after": "whatsapp_status",
			"read_only": 1,
		},
		{
			"fieldname": "whatsapp_checked_on",
			"label": "WhatsApp Checked On",
			"fieldtype": "Datetime",
			"insert_after": "whatsapp_verified_number",
			"read_only": 1,
		},
	],
	"Quotation": [
		{
			"fieldname": "custom_address_section",
			"fieldtype": "Section Break",
			"label": "Custom Address",
			"insert_after": "customer_name",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_customer_name",
			"fieldtype": "Data",
			"label": "Custom Customer Name",
			"insert_after": "custom_address_section",
			"translatable": 0,
		},
		{
			"fieldname": "custom_address_line1",
			"fieldtype": "Data",
			"label": "Address Line 1",
			"insert_after": "custom_customer_name",
			"translatable": 0,
		},
		{
			"fieldname": "custom_address_line2",
			"fieldtype": "Data",
			"label": "Address Line 2",
			"insert_after": "custom_address_line1",
			"translatable": 0,
		},
		{
			"fieldname": "custom_mobile_number",
			"fieldtype": "Data",
			"label": "Mobile Number",
			"insert_after": "custom_address_line2",
			"translatable": 0,
		},
		{
			"fieldname": "custom_remarks",
			"fieldtype": "Small Text",
			"label": "Remarks",
			"insert_after": "custom_mobile_number",
		},
		{
			"fieldname": "customer_rate_multiplier",
			"fieldtype": "Check",
			"label": "Customer Rate Multiplier",
			"insert_after": "custom_remarks",
			"default": "1",
		},
		{
			"fieldname": "custom_half_tax_discount",
			"fieldtype": "Check",
			"label": "Half Tax Discount",
			"insert_after": "customer_rate_multiplier",
			"default": "0",
		},
	],
	"Supplier": [
		{
			"fieldname": "supplier_print_name",
			"fieldtype": "Data",
			"label": "Supplier Print Name",
			"insert_after": "supplier_name",
			"translatable": 0,
		},
		{
			"fieldname": "whatsapp_status",
			"label": "WhatsApp Status",
			"fieldtype": "Select",
			"options": "Not Checked\nValid\nInvalid",
			"default": "Not Checked",
			"insert_after": "supplier_print_name",
			"read_only": 1,
			"in_standard_filter": 1,
			"description": "Checked when the party is saved, on Check, or when a bill is sent. Stays Valid until a send fails or the number changes.",
		},
		{
			"fieldname": "whatsapp_verified_number",
			"label": "WhatsApp Number Checked",
			"fieldtype": "Data",
			"insert_after": "whatsapp_status",
			"read_only": 1,
		},
		{
			"fieldname": "whatsapp_checked_on",
			"label": "WhatsApp Checked On",
			"fieldtype": "Datetime",
			"insert_after": "whatsapp_verified_number",
			"read_only": 1,
		},
		{
			"fieldname": "custom_pricelist_percentages",
			"label": "Pricelist Percentages",
			"fieldtype": "Table",
			"options": "Item Price List Percentage",
			"insert_after": "whatsapp_checked_on",
		},
	],
	"Sales Invoice": [
		{
			"fieldname": "mop",
			"label": "MOP",
			"fieldtype": "Select",
			"options": "Cash\nCredit",
			"insert_after": "customer_name",
		},
		{
			"fieldname": "custom_remarks",
			"fieldtype": "Small Text",
			"label": "Remarks",
			"insert_after": "custom_mobile_number",
		}
	],
	"Purchase Invoice": [
		{
			"fieldname": "custom_remarks",
			"fieldtype": "Small Text",
			"label": "Remarks",
			"insert_after": "supplier_name",
			"allow_on_submit": 1,
		},
		{
			"fieldname": "custom_mirrored",
			"fieldtype": "Data",
			"label": "Mirrored Invoice Number",
			"insert_after": "is_return",
			"allow_on_submit": 1,
			"in_list_view": 1,
			"in_standard_filter": 1,
		},
	],
}


# Mirrors allTiles in frontend/src/pages/Dashboard.vue — (tile_id, tile_label, bucket).
# Add a row here when a new tile is added to the dashboard.
DASHBOARD_TILES = [
	# Sale
	("sales", "Sales Invoice", "Sale"),
	("mobile-bill", "Mobile Bill", "Sale"),
	("quotation", "Quotation", "Sale"),
	("cashier", "Cashier Desk", "Sale"),
	("cashier-mobile", "Cashier Mobile", "Sale"),
	("pos", "POS Billing", "Sale"),
	("sales-order", "Sales Order", "Sale"),
	("Cashier-Management", "Cashier Management", "Sale"),
	("cancellation", "Cancellation", "Sale"),
	("modifysubmitted", "Modify Submitted Bill", "Sale"),
	# Purchase
	("purchase-invoice", "Purchase Invoice", "Purchase"),
	("purchase-order", "Purchase Order", "Purchase"),
	("purchase-submit", "Purchase Desk", "Purchase"),
	# Stock
	("stock-reconciliation", "Stock Reconciliation", "Stock"),
	("store-transfer", "Store Transfer", "Stock"),
	("repack", "Repack Entry", "Stock"),
	("land-cost-voucher", "Landed Cost Voucher", "Stock"),
	("stock-check", "Stock Check", "Stock"),
	# Accounts
	("expense", "Cash Box Entry", "Accounts"),
	("single-entry", "Single Entry", "Accounts"),
	("payment", "Payment Receipt", "Accounts"),
	("paytm-link", "Paytm Receipt", "Accounts"),
	("paytm-unknown", "Paytm Unknown Payments", "Accounts"),
	("bank-statement", "Bank Statement", "Accounts"),
	("unreconciled", "Unreconciled Entries", "Accounts"),
	("payment-reconciliation", "Payment Reconciliation", "Accounts"),
	("journal-contra", "Journal Contra", "Accounts"),
	("cheques", "Cheque Register", "Accounts"),
	("outstanding-bills", "Outstanding", "Accounts"),
	("incentive-redeem", "Incentive Redeem", "Accounts"),
	("incentive-entry", "Incentive Entry", "Accounts"),
	("account-tree", "Chart of Accounts", "Accounts"),
	# Ledger View
	("stock-ledger", "Stock", "Ledger View"),
	("ledger", "Customer Ledger", "Ledger View"),
	("incentive-ledger", "Incentive Ledger", "Ledger View"),
	("general-ledger", "General Ledger", "Ledger View"),
	# SSPL Special
	("loading-receipt", "Loading Receipt", "SSPL Special"),
	("customer-enquiry", "Customer Enquiry", "SSPL Special"),
	("parcel-address", "Parcel Address", "SSPL Special"),
	("pricing-rules", "Discount Rules", "SSPL Special"),
	("naming-settings", "Naming Settings", "SSPL Special"),
	("barcode-print", "Print Barcodes", "SSPL Special"),
	("item-barcode", "Item Barcodes", "SSPL Special"),
	("catelogue", "Catalogues", "SSPL Special"),
	("catalogueviewer", "Catalogue Viewer", "SSPL Special"),
	("offer-display", "Offer Display", "SSPL Special"),
	("hrms", "HRMS Dashboard", "SSPL Special"),
	("employee", "Employee Directory", "SSPL Special"),
	("essl-machines", "eSSL Machines", "SSPL Special"),
	("create-user", "Create User", "SSPL Special"),
	("whatsapp-link", "WhatsApp Link", "SSPL Special"),
	("whatsapp-chat", "WhatsApp Chat", "SSPL Special"),
	("competitive", "Competitive Items", "SSPL Special"),
	("ai-chat", "AI Chat", "SSPL Special"),
	("daily-report", "Daily Report", "Report"),
	("reports", "Reports", "Report"),
	("store-sale-report", "Store Sale Report", "Report"),
	("cost-center-sale-report", "Cost Center Sale Report", "Report"),
	("batch-reports", "Batch Reports", "Report"),
]


def sync_dashboard_tiles():
	"""Upsert SSPL Dashboard Tile records from DASHBOARD_TILES. Never deletes,
	so tiles removed from the list stay selectable until removed manually."""
	if not frappe.db.exists("DocType", "SSPL Dashboard Tile"):
		return
	for tile_id, tile_label, bucket in DASHBOARD_TILES:
		if frappe.db.exists("SSPL Dashboard Tile", tile_id):
			frappe.db.set_value(
				"SSPL Dashboard Tile",
				tile_id,
				{"tile_label": tile_label, "bucket": bucket},
				update_modified=False,
			)
		else:
			frappe.get_doc(
				{
					"doctype": "SSPL Dashboard Tile",
					"tile_id": tile_id,
					"tile_label": tile_label,
					"bucket": bucket,
				}
			).insert(ignore_permissions=True)


def sync_template_usages():
	"""One WhatsApp Template per Usage Area row per place the app sends messages (see whatsapp_api)."""
	from ssplbilling.api.whatsapp_api import sync_template_usages as sync

	sync()


def sync_offer_print_template():
	"""Seed the editable catalogue Print Template for the offer page export.

	Only inserted when missing, so desk edits to the layout survive migrations.
	Print Template belongs to the printer_server_configuration app; nothing is
	seeded when that app is not installed.
	"""
	from ssplbilling.api.offer_api import OFFER_PRINT_TEMPLATE, get_default_catalog_html

	if not frappe.db.exists("DocType", "Offer-Items"):
		return
	if not frappe.db.exists("DocType", "Print Template"):
		return
	if frappe.db.exists("Print Template", OFFER_PRINT_TEMPLATE):
		return

	html = get_default_catalog_html()
	if not html:
		return

	frappe.get_doc(
		{
			"doctype": "Print Template",
			"template_name": OFFER_PRINT_TEMPLATE,
			"source_type": "DocType",
			"document_type": "Offer-Items",
			"format_type": "Custom PDF",
			"custom_pdf_page_size": "A4",
			"custom_pdf_orientation": "Portrait",
			"custom_pdf_template": html,
		}
	).insert(ignore_permissions=True)


INVOICE_EMAIL_TEMPLATE = "SSPL Invoice"

# Rendered by email_api.get_email_content with the bill's fields and the bill as doc.
# doc.get() keeps one template working for every doctype the print window mails.
INVOICE_EMAIL_SUBJECT = (
	'{{ doc.doctype }} {{ doc.name }}{% if doc.get("company") %} - {{ doc.get("company") }}{% endif %}'
)

INVOICE_EMAIL_HTML = """\
{%- set party = doc.get("customer_name") or doc.get("supplier_name") or doc.get("party_name") -%}
{%- set date_field = "posting_date" if doc.get("posting_date") else "transaction_date" -%}
<p>Dear {{ party or "Customer" }},</p>
<p>
	Please find attached {{ doc.doctype }} <b>{{ doc.name }}</b>
	{%- if doc.get(date_field) %} dated {{ doc.get_formatted(date_field) }}{% endif %}.
</p>
{%- if doc.get("grand_total") %}
<table cellpadding="4" style="border-collapse: collapse;">
	<tr>
		<td>Bill Amount</td>
		<td style="text-align: right;"><b>{{ doc.get_formatted("rounded_total" if doc.get("rounded_total") else "grand_total") }}</b></td>
	</tr>
	{%- if doc.get("docstatus") == 1 and doc.get("outstanding_amount") %}
	<tr>
		<td>Balance Due</td>
		<td style="text-align: right;"><b>{{ doc.get_formatted("outstanding_amount") }}</b></td>
	</tr>
	{%- endif %}
</table>
{%- endif %}
<p>For any query about this bill, reply to this email.</p>
<p>Thank you for your business.<br>Regards,<br>{{ doc.get("company") or "" }}</p>
{{ email_signature or "" }}
"""


def sync_invoice_email_template():
	"""Seed the bill Email Template and make it the Bill Sending template.

	The template is only inserted when missing, so desk edits survive migrations, and
	is only assigned when Bill Sending has no template yet, so a chosen one is kept.
	"""
	from ssplbilling.ssplbilling.doctype.sspl_email_settings.sspl_email_settings import AREA_BILL_SENDING

	if not frappe.db.exists("Email Template", INVOICE_EMAIL_TEMPLATE):
		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": INVOICE_EMAIL_TEMPLATE,
				"subject": INVOICE_EMAIL_SUBJECT,
				"use_html": 1,
				"response_html": INVOICE_EMAIL_HTML,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("DocType", "SSPL Email Settings"):
		return
	settings = frappe.get_single("SSPL Email Settings")
	row = next((r for r in settings.template_usages if r.usage_area == AREA_BILL_SENDING), None)
	if row and row.email_template:
		return
	if row:
		row.email_template = INVOICE_EMAIL_TEMPLATE
	else:
		settings.append(
			"template_usages", {"usage_area": AREA_BILL_SENDING, "email_template": INVOICE_EMAIL_TEMPLATE}
		)
	settings.save(ignore_permissions=True)


def backfill_mirrored_purchase_invoices():
	"""Set custom_mirrored with mirrored invoice name on existing mirrored purchase invoices."""
	if not frappe.db.has_column("Purchase Invoice", "custom_mirrored"):
		return
	try:
		frappe.db.sql("ALTER TABLE `tabPurchase Invoice` MODIFY `custom_mirrored` varchar(140)")
	except Exception:
		pass
	frappe.db.sql("""
		UPDATE `tabPurchase Invoice` pi1
		JOIN `tabPurchase Invoice` pi2
		ON (CONCAT(pi2.name, '/') = pi1.name OR CONCAT(pi1.name, '/') = pi2.name)
		AND pi1.name != pi2.name
		SET pi1.custom_mirrored = pi2.name, pi2.custom_mirrored = pi1.name
		WHERE pi1.docstatus = 1 AND pi2.docstatus = 1
	""")


def allow_supplier_bill_no_edit_after_submit():
	"""Let the supplier bill no and date on a submitted Purchase Invoice be corrected."""
	for fieldname in ("bill_no", "bill_date"):
		make_property_setter(
			"Purchase Invoice", fieldname, "allow_on_submit", 1, "Check", validate_fields_for_doctype=False
		)


def after_install():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
	sync_dashboard_tiles()
	sync_template_usages()
	sync_offer_print_template()
	sync_invoice_email_template()
	backfill_mirrored_purchase_invoices()
	allow_supplier_bill_no_edit_after_submit()


def after_migrate():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
	sync_dashboard_tiles()
	sync_template_usages()
	sync_offer_print_template()
	sync_invoice_email_template()
	backfill_mirrored_purchase_invoices()
	allow_supplier_bill_no_edit_after_submit()
