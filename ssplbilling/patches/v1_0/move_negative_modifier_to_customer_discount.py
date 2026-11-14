"""The pricelist modifier only marks prices up now. A customer whose modifier was below 1
(0.9 = 10% off) gets that as the new Discount % field and a modifier of 1, which is what the
bill pages already did with it: rates stay at the price list, the bill gets the discount."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt

from ssplbilling.setup import CUSTOM_FIELDS


def execute():
	# Custom fields are synced after_migrate, which runs after patches.
	create_custom_fields({"Customer": CUSTOM_FIELDS["Customer"]}, ignore_validate=True)
	rows = frappe.get_all(
		"Customer",
		filters={"pricelist_multiplication_factor": ["between", [0.000001, 0.999999]]},
		fields=["name", "pricelist_multiplication_factor", "customer_discount_percentage"],
		limit=0,
	)
	for r in rows:
		discount = flt((1 - flt(r.pricelist_multiplication_factor)) * 100, 2)
		frappe.db.set_value(
			"Customer",
			r.name,
			{
				"customer_discount_percentage": flt(r.customer_discount_percentage) or discount,
				"pricelist_multiplication_factor": 1,
			},
			update_modified=False,
		)
