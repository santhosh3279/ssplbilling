import frappe
from frappe.utils import flt


def calculate_incentive_points(doc, method=None):
	"""Auto-populate points in the Incentive System child table on submit."""
	if not getattr(doc, "incentive_system", None):
		return

	rows = doc.incentive_system
	n = len(rows)
	if n == 0:
		return

	rule = frappe.get_single("Incentive Rule")

	doctype = doc.doctype
	percentage = _get_percentage(doc, doctype, rule)

	if not percentage:
		return

	amount = _get_amount(doc, doctype)
	if not amount:
		return

	total_points = flt(percentage) / 100 * flt(amount)

	biller_row = next((r for r in rows if r.role == "Biller"), None)

	if biller_row and n > 1:
		biller_points = total_points / (2 * n)
		remaining = total_points - biller_points
		others_each = remaining / (n - 1)

		for row in rows:
			if row.role == "Biller":
				row.points = flt(biller_points, 2)
			else:
				row.points = flt(others_each, 2)
	else:
		# No biller distinction or only one row — distribute equally
		per_person = total_points / n
		for row in rows:
			row.points = flt(per_person, 2)


def _get_percentage(doc, doctype, rule):
	if doctype == "Sales Invoice":
		wholesale_lists = {
			rule.wholesale_pricelist_1,
			rule.wholesale_pricelist_2,
			rule.wholesale_pricelist_3,
		} - {None, ""}
		if doc.selling_price_list in wholesale_lists:
			return rule.wholesale
		return rule.sales

	if doctype == "Purchase Invoice":
		return rule.purchase

	if doctype == "Stock Entry":
		return rule.store_transfer

	return None


def _get_amount(doc, doctype):
	if doctype in ("Sales Invoice", "Purchase Invoice"):
		return doc.grand_total
	if doctype == "Stock Entry":
		return doc.total_amount or doc.total_outgoing_value
	return None
