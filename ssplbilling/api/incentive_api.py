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
