import json

import frappe

SHIFT_ASSIGNMENT = "Shift Assignment"


def _parse(data):
	return json.loads(data) if isinstance(data, str) else (data or {})


@frappe.whitelist()
def get_shift_types():
	"""Shift masters for the roaster dropdown. start_time/end_time are timedeltas,
	so they are stringified here rather than left for the JSON encoder."""
	rows = frappe.get_all(
		"Shift Type",
		fields=["name", "start_time", "end_time", "enable_auto_attendance"],
		order_by="name asc",
	)
	for row in rows:
		row["start_time"] = str(row.start_time) if row.start_time else None
		row["end_time"] = str(row.end_time) if row.end_time else None
	return rows


@frappe.whitelist()
def get_shift_assignments(employee=None, shift_type=None, from_date=None, to_date=None):
	"""Roaster rows. Cancelled assignments are dropped — they carry no roster meaning.

	from_date/to_date filter on overlap, not containment: an assignment counts when any
	part of it falls inside the window, and an open-ended one (no end_date) always does.
	"""
	filters = {"docstatus": ("<", 2)}
	if employee:
		filters["employee"] = employee
	if shift_type:
		filters["shift_type"] = shift_type
	if to_date:
		filters["start_date"] = ("<=", to_date)

	rows = frappe.get_all(
		SHIFT_ASSIGNMENT,
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"department",
			"shift_type",
			"company",
			"start_date",
			"end_date",
			"status",
			"docstatus",
		],
		order_by="start_date desc, employee_name asc",
		limit_page_length=0,
	)

	if from_date:
		from_date = frappe.utils.getdate(from_date)
		rows = [r for r in rows if not r.end_date or frappe.utils.getdate(r.end_date) >= from_date]

	return rows


@frappe.whitelist()
def save_shift_assignment(data):
	"""Create a submitted assignment, or edit an existing one.

	A submitted Shift Assignment only allows end_date and status to change (that is what
	hrms marks allow_on_submit); anything else has to be cancelled and re-created, so the
	attempt is refused with that instruction instead of failing deeper in the ORM.
	"""
	data = _parse(data)

	name = data.get("name")
	employee = (data.get("employee") or "").strip()
	shift_type = (data.get("shift_type") or "").strip()
	start_date = data.get("start_date")
	end_date = data.get("end_date") or None
	status = data.get("status") or "Active"

	if not name:
		if not employee:
			frappe.throw("Employee is required")
		if not shift_type:
			frappe.throw("Shift Type is required")
		if not start_date:
			frappe.throw("Start Date is required")

	if end_date and start_date and frappe.utils.getdate(end_date) < frappe.utils.getdate(start_date):
		frappe.throw("End Date cannot be before Start Date")

	if name:
		doc = frappe.get_doc(SHIFT_ASSIGNMENT, name)
		if doc.docstatus == 1:
			if employee and employee != doc.employee:
				frappe.throw("A submitted assignment cannot change employee — cancel it and add a new one")
			if shift_type and shift_type != doc.shift_type:
				frappe.throw("A submitted assignment cannot change shift — cancel it and add a new one")
			if start_date and frappe.utils.getdate(start_date) != frappe.utils.getdate(doc.start_date):
				frappe.throw(
					"A submitted assignment cannot change its start date — cancel it and add a new one"
				)
			doc.end_date = end_date
			doc.status = status
			doc.save(ignore_permissions=True)
			return _as_row(doc)

		doc.employee = employee or doc.employee
		doc.shift_type = shift_type or doc.shift_type
		doc.start_date = start_date or doc.start_date
	else:
		doc = frappe.new_doc(SHIFT_ASSIGNMENT)
		doc.employee = employee
		doc.shift_type = shift_type
		doc.start_date = start_date

	doc.end_date = end_date
	doc.status = status
	doc.company = data.get("company") or frappe.db.get_value("Employee", doc.employee, "company")

	if doc.get("__islocal") or not doc.name:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	doc.submit()
	return _as_row(doc)


def _as_row(doc):
	return {
		"name": doc.name,
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"shift_type": doc.shift_type,
		"start_date": str(doc.start_date) if doc.start_date else None,
		"end_date": str(doc.end_date) if doc.end_date else None,
		"status": doc.status,
		"docstatus": doc.docstatus,
	}


@frappe.whitelist()
def cancel_shift_assignment(name):
	"""Cancel a submitted assignment — the only way to retire a wrong employee/shift/date."""
	doc = frappe.get_doc(SHIFT_ASSIGNMENT, name)
	if doc.docstatus == 1:
		doc.cancel()
	return {"cancelled": name}


@frappe.whitelist()
def delete_shift_assignment(name):
	"""Delete outright. A submitted assignment is cancelled first, matching what the
	desk does, so the roaster never leaves a stale submitted row behind."""
	doc = frappe.get_doc(SHIFT_ASSIGNMENT, name)
	if doc.docstatus == 1:
		doc.cancel()
	frappe.delete_doc(SHIFT_ASSIGNMENT, name, ignore_permissions=True, force=True)
	return {"deleted": name}


@frappe.whitelist()
def save_shift_type(name, start_time, end_time, is_new=0):
	"""Create or edit a Shift Type."""
	if not name:
		frappe.throw("Shift Name is required")
	if not start_time:
		frappe.throw("Start Time is required")
	if not end_time:
		frappe.throw("End Time is required")

	name = name.strip()
	is_new = int(is_new)

	if is_new:
		if frappe.db.exists("Shift Type", name):
			frappe.throw(f"Shift Type {name} already exists")
		doc = frappe.new_doc("Shift Type")
		doc.name = name
	else:
		if not frappe.db.exists("Shift Type", name):
			frappe.throw(f"Shift Type {name} does not exist")
		doc = frappe.get_doc("Shift Type", name)

	doc.start_time = start_time
	doc.end_time = end_time

	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {
		"name": doc.name,
		"start_time": str(doc.start_time) if doc.start_time else None,
		"end_time": str(doc.end_time) if doc.end_time else None,
	}
