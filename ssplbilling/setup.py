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


def after_install():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)


def after_migrate():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
