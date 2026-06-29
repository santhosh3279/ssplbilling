import frappe
from frappe.utils import flt


def calculate_incentive_points(doc, method=None):
	"""Calculate and persist points in Incentive System child table on submit."""
	if not getattr(doc, "incentive_system", None):
		return

	rows = doc.incentive_system
	n = len(rows)
	if n == 0:
		return

	rule = frappe.get_single("Incentive Rule")
	
	ref_doc = doc
	if doc.doctype == "Invoice Incentive":
		ref_doctype = None
		if frappe.db.exists("Sales Invoice", doc.inv_no):
			ref_doctype = "Sales Invoice"
		elif frappe.db.exists("Purchase Invoice", doc.inv_no):
			ref_doctype = "Purchase Invoice"
		elif frappe.db.exists("Stock Entry", doc.inv_no):
			ref_doctype = "Stock Entry"
		
		if ref_doctype:
			ref_doc = frappe.get_doc(ref_doctype, doc.inv_no)
		else:
			return

	percentage = _get_percentage(ref_doc, rule)

	if not percentage:
		return

	amount = _get_amount(ref_doc)
	if not amount:
		return

	total_points = flt(percentage) / 100 * flt(amount)

	biller_row = next((r for r in rows if r.role == "Biller"), None)

	if biller_row and n > 1:
		biller_points = flt(total_points / (2 * n), 2)
		remaining = total_points - biller_points
		others_each = flt(remaining / (n - 1), 2)

		for row in rows:
			points = biller_points if row.role == "Biller" else others_each
			row.points = points
			frappe.db.set_value("Incentive System", row.name, "points", points)
	else:
		per_person = flt(total_points / n, 2)
		for row in rows:
			row.points = per_person
			frappe.db.set_value("Incentive System", row.name, "points", per_person)

	_update_employee_totals(doc, multiplier=1)


def reverse_incentive_points(doc, method=None):
	"""Reverse employee incentive totals on document cancellation."""
	if not getattr(doc, "incentive_system", None):
		return
	if not doc.incentive_system:
		return
	_update_employee_totals(doc, multiplier=-1)


def _update_employee_totals(doc, multiplier):
	"""Add or subtract points from each employee's total and recompute balance."""
	for row in doc.incentive_system:
		if not row.employee or not flt(row.points):
			continue

		current = frappe.db.get_value(
			"Employee", row.employee, ["total_incentive", "redeemed_incentive"], as_dict=True
		)
		if not current:
			continue

		new_total = flt(current.total_incentive) + multiplier * flt(row.points)
		new_balance = new_total - flt(current.redeemed_incentive)

		frappe.db.set_value(
			"Employee",
			row.employee,
			{"total_incentive": flt(new_total, 2), "balance_incentive": flt(new_balance, 2)},
		)


def _get_percentage(doc, rule):
	doctype = doc.doctype
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


def _get_amount(doc):
	doctype = doc.doctype
	if doctype in ("Sales Invoice", "Purchase Invoice"):
		return doc.grand_total
	if doctype == "Stock Entry":
		return doc.total_amount or doc.total_outgoing_value
	return None
