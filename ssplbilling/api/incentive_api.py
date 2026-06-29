import json

import frappe


@frappe.whitelist()
def get_incentive_system(doctype, docname):
	doc = frappe.get_doc(doctype, docname)
	return [
		{
			"name": r.name,
			"employee": r.employee,
			"employee_name": frappe.db.get_value("Employee", r.employee, "employee_name") if r.employee else "",
			"role": r.role,
			"points": r.points,
		}
		for r in (doc.incentive_system or [])
	]


@frappe.whitelist()
def save_incentive_system(doctype, docname, rows):
	if isinstance(rows, str):
		rows = json.loads(rows)
	doc = frappe.get_doc(doctype, docname)
	doc.set("incentive_system", [])
	for row in rows:
		doc.append(
			"incentive_system",
			{
				"employee": row.get("employee"),
				"role": row.get("role"),
				"points": row.get("points") or 0,
			},
		)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return [
		{
			"name": r.name,
			"employee": r.employee,
			"employee_name": frappe.db.get_value("Employee", r.employee, "employee_name") if r.employee else "",
			"role": r.role,
			"points": r.points,
		}
		for r in doc.incentive_system
	]


@frappe.whitelist()
def search_employees(query):
	return frappe.get_all(
		"Employee",
		filters=[["employee_name", "like", f"%{query}%"], ["status", "=", "Active"]],
		fields=["name", "employee_name", "designation"],
		limit=10,
	)


@frappe.whitelist()
def get_unposted_bills():
	# Get all posted bill names (including drafts and submitted)
	posted = frappe.get_all("Invoice Incentive", filters={"docstatus": ["in", [0, 1]]}, fields=["inv_no"])
	posted_set = {d.inv_no for d in posted if d.inv_no}

	from ssplbilling.api.dashboard_api import get_allowed_series

	# 1. Fetch Sales Invoices
	si_allowed_res = get_allowed_series(doctype="Sales Invoice")
	si_filters = {"docstatus": 1}
	if si_allowed_res.get("user_allowed_string") != "ALL":
		si_filters["naming_series"] = ["in", si_allowed_res.get("allowed_series") or []]

	sales_invoices = frappe.get_all(
		"Sales Invoice",
		filters=si_filters,
		fields=["name", "posting_date as date", "grand_total as amount", "customer_name as detail"],
		order_by="posting_date desc",
		limit=100
	)
	
	# 2. Fetch Purchase Invoices
	pi_allowed_res = get_allowed_series(doctype="Purchase Invoice")
	pi_filters = {"docstatus": 1}
	if pi_allowed_res.get("user_allowed_string") != "ALL":
		pi_filters["naming_series"] = ["in", pi_allowed_res.get("allowed_series") or []]

	purchase_invoices = frappe.get_all(
		"Purchase Invoice",
		filters=pi_filters,
		fields=["name", "posting_date as date", "grand_total as amount", "supplier_name as detail"],
		order_by="posting_date desc",
		limit=100
	)
	
	# 3. Fetch Stock Entries of purpose "Material Transfer"
	se_allowed_res = get_allowed_series(doctype="Stock Entry")
	se_filters = {"docstatus": 1, "purpose": "Material Transfer"}
	if se_allowed_res.get("user_allowed_string") != "ALL":
		se_filters["naming_series"] = ["in", se_allowed_res.get("allowed_series") or []]

	stock_entries = frappe.get_all(
		"Stock Entry",
		filters=se_filters,
		fields=["name", "posting_date as date", "total_outgoing_value as amount"],
		order_by="posting_date desc",
		limit=100
	)


	bills = []
	for si in sales_invoices:
		if si.name not in posted_set:
			bills.append({
				"name": si.name,
				"doctype": "Sales Invoice",
				"date": str(si.date),
				"amount": float(si.amount or 0),
				"detail": si.detail or ""
			})

	for pi in purchase_invoices:
		if pi.name not in posted_set:
			bills.append({
				"name": pi.name,
				"doctype": "Purchase Invoice",
				"date": str(pi.date),
				"amount": float(pi.amount or 0),
				"detail": pi.detail or ""
			})

	for se in stock_entries:
		if se.name not in posted_set:
			bills.append({
				"name": se.name,
				"doctype": "Stock Entry",
				"date": str(se.date),
				"amount": float(se.amount or 0),
				"detail": "Material Transfer"
			})

	# Sort combined list by date descending
	bills.sort(key=lambda x: x["date"], reverse=True)
	return bills


@frappe.whitelist()
def calculate_bill_incentive(doctype, name):
	from ssplbilling.incentive_utils import _get_percentage, _get_amount
	doc = frappe.get_doc(doctype, name)
	rule = frappe.get_single("Incentive Rule")
	percentage = _get_percentage(doc, rule)
	amount = _get_amount(doc)
	
	total_points = 0.0
	if percentage and amount:
		total_points = (float(percentage) / 100.0) * float(amount)
		
	return {
		"doctype": doctype,
		"name": name,
		"amount": float(amount or 0),
		"percentage": float(percentage or 0),
		"total_points": float(total_points)
	}

