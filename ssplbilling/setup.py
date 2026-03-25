import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
	"Customer": [
		{
			"fieldname": "customer_print_name",
			"fieldtype": "Data",
			"label": "Customer Print Name",
			"insert_after": "customer_name",
			"translatable": 0,
		}
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
}


def after_install():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)


def after_migrate():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
