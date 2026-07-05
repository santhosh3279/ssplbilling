import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
	"Item": [
		{
			"fieldname": "custom_pricelist_percentages",
			"label": "Pricelist Percentages",
			"fieldtype": "Table",
			"options": "Item Price List Percentage",
			"insert_after": "safety_stock",
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
			"fieldname": "customer_rate_multiplier",
			"fieldtype": "Check",
			"label": "Customer Rate Multiplier",
			"insert_after": "custom_mobile_number",
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
		}
	],
	"Sales Invoice": [
		{
			"fieldname": "mop",
			"label": "MOP",
			"fieldtype": "Select",
			"options": "Cash\nCredit",
			"insert_after": "customer_name",
		}
	],
}


# Mirrors allTiles in frontend/src/pages/Dashboard.vue — (tile_id, tile_label, bucket).
# Add a row here when a new tile is added to the dashboard.
DASHBOARD_TILES = [
	# Sale
	("sales", "Sales Invoice", "Sale"),
	("quotation", "Quotation", "Sale"),
	("cashier", "Cashier Desk", "Sale"),
	("sales-order", "Sales Order", "Sale"),
	("Cashier-Management", "Cashier Management", "Sale"),
	("cancellation", "Cancellation", "Sale"),
	# Purchase
	("purchase-invoice", "Purchase Invoice", "Purchase"),
	("purchase-order", "Purchase Order", "Purchase"),
	("purchase-submit", "Purchase Desk", "Purchase"),
	# Stock
	("stock-reconciliation", "Stock Reconciliation", "Stock"),
	("store-transfer", "Store Transfer", "Stock"),
	("repack", "Repack Entry", "Stock"),
	# Accounts
	("expense", "Cash Box Entry", "Accounts"),
	("single-entry", "Single Entry", "Accounts"),
	("payment", "Payment Receipt", "Accounts"),
	("unreconciled", "Unreconciled Entries", "Accounts"),
	("payment-reconciliation", "Payment Reconciliation", "Accounts"),
	("journal-contra", "Journal Contra", "Accounts"),
	("cheques", "Cheque Register", "Accounts"),
	("outstanding-bills", "Outstanding", "Accounts"),
	("incentive-redeem", "Incentive Redeem", "Accounts"),
	("incentive-entry", "Incentive Entry", "Accounts"),
	# Ledger View
	("stock-ledger", "Stock", "Ledger View"),
	("ledger", "Customer Ledger", "Ledger View"),
	("gst-ledger", "GST Ledger", "Ledger View"),
	("incentive-ledger", "Incentive Ledger", "Ledger View"),
	("general-ledger", "General Ledger", "Ledger View"),
	# SSPL Special
	("loading-receipt", "Loading Receipt", "SSPL Special"),
	("customer-enquiry", "Customer Enquiry", "SSPL Special"),
	("parcel-address", "Parcel Address", "SSPL Special"),
	("gst-dummy-ledger", "WGB Payments", "SSPL Special"),
	("pricing-rules", "Discount Rules", "SSPL Special"),
	("naming-settings", "Naming Settings", "SSPL Special"),
	("barcode-print", "Print Barcodes", "SSPL Special"),
	("catelogue", "Catalogues", "SSPL Special"),
	# Report
	("daily-report", "Daily Report", "Report"),
	("reports", "Reports", "Report"),
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


def after_install():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
	sync_dashboard_tiles()


def after_migrate():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
	sync_dashboard_tiles()
