import json

import frappe


def _row_dict(row):
	return {
		"item_code": row.item_code,
		"item_name": row.item_name,
		"is_new_item": row.is_new_item,
		"description": row.description,
	}


def _apply_data(doc, d):
	doc.enquiry_date = d.get("enquiry_date")
	doc.cost_center = d.get("cost_center")
	doc.customer = d.get("customer")
	doc.customer_name = d.get("customer_name")
	doc.new_customer = d.get("new_customer")
	doc.mobile_no = d.get("mobile_no")
	doc.status = d.get("status") or "Open"
	doc.items = []
	for row in d.get("items", []):
		doc.append(
			"items",
			{
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name"),
				"is_new_item": 1 if row.get("is_new_item") else 0,
				"description": row.get("description"),
			},
		)


@frappe.whitelist()
def create_enquiry(data):
	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.new_doc("Customer Enquiry")
	_apply_data(doc, d)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def update_enquiry(data):
	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.get_doc("Customer Enquiry", d["name"])
	_apply_data(doc, d)
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def get_enquiries(status="Open", query="", cost_center=None):
	clauses = ["ce.status = %s"]
	values = [status]
	query = (query or "").strip()
	if query:
		clauses.append("(ce.name LIKE %s OR ce.customer_name LIKE %s OR ce.mobile_no LIKE %s)")
		values += [f"%{query}%"] * 3
	if cost_center:
		clauses.append("ce.cost_center = %s")
		values.append(cost_center)
	enquiries = frappe.db.sql(
		f"""
		SELECT ce.name, ce.enquiry_date, ce.cost_center, ce.status, ce.customer,
		       ce.customer_name, ce.new_customer, ce.mobile_no, ce.closed_on
		FROM `tabCustomer Enquiry` ce
		WHERE {" AND ".join(clauses)}
		ORDER BY ce.enquiry_date DESC, ce.creation DESC
		LIMIT 200
		""",
		values,
		as_dict=True,
	)
	if not enquiries:
		return []
	items = frappe.get_all(
		"Customer Enquiry Item",
		filters={"parent": ["in", [e.name for e in enquiries]], "parenttype": "Customer Enquiry"},
		fields=["parent", "item_code", "item_name", "is_new_item", "description"],
		order_by="parent, idx asc",
	)
	by_parent = {}
	for it in items:
		by_parent.setdefault(it.pop("parent"), []).append(it)
	for e in enquiries:
		e["items"] = by_parent.get(e.name, [])
		e["enquiry_date"] = str(e.enquiry_date) if e.enquiry_date else None
		e["closed_on"] = str(e.closed_on) if e.closed_on else None
	return enquiries


@frappe.whitelist()
def get_enquiry(name):
	doc = frappe.get_doc("Customer Enquiry", name)
	return {
		"name": doc.name,
		"enquiry_date": str(doc.enquiry_date) if doc.enquiry_date else None,
		"cost_center": doc.cost_center,
		"status": doc.status,
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"new_customer": doc.new_customer,
		"mobile_no": doc.mobile_no,
		"closed_on": str(doc.closed_on) if doc.closed_on else None,
		"items": [_row_dict(r) for r in doc.items],
	}


@frappe.whitelist()
def close_enquiry(name):
	doc = frappe.get_doc("Customer Enquiry", name)
	doc.status = "Closed"
	doc.closed_on = frappe.utils.now_datetime()
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reopen_enquiry(name):
	doc = frappe.get_doc("Customer Enquiry", name)
	doc.status = "Open"
	doc.closed_on = None
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}
