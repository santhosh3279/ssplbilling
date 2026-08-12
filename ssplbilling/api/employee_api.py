import frappe


@frappe.whitelist()
def create_employee(data):
	"""Create a new Employee record."""
	import json
	if isinstance(data, str):
		data = json.loads(data)

	first_name = (data.get("first_name") or "").strip()
	if not first_name:
		frappe.throw("First Name is required")

	emp = frappe.new_doc("Employee")
	emp.first_name = first_name
	emp.last_name = (data.get("last_name") or "").strip()
	emp.employee_name = " ".join(filter(None, [emp.first_name, emp.last_name]))
	emp.gender = data.get("gender") or "Male"
	emp.date_of_birth = data.get("date_of_birth") or None
	emp.date_of_joining = data.get("date_of_joining") or frappe.utils.today()
	emp.cell_number = data.get("mobile") or ""
	emp.personal_email = data.get("email") or ""
	emp.current_address = data.get("current_address") or ""
	emp.status = "Active"
	emp.company = frappe.defaults.get_global_default("company")
	emp.insert(ignore_permissions=True)

	return {"name": emp.name, "employee_name": emp.employee_name}


@frappe.whitelist()
def get_employee_details(employee):
	"""Return Employee fields in a flat dict."""
	emp = frappe.get_doc("Employee", employee)
	return {
		"name": emp.name,
		"first_name": emp.first_name or "",
		"last_name": emp.last_name or "",
		"employee_name": emp.employee_name or "",
		"gender": emp.gender or "Male",
		"date_of_birth": str(emp.date_of_birth) if emp.date_of_birth else "",
		"date_of_joining": str(emp.date_of_joining) if emp.date_of_joining else "",
		"mobile": emp.cell_number or "",
		"email": emp.personal_email or "",
		"current_address": emp.current_address or "",
	}


@frappe.whitelist()
def update_employee(data):
	"""Update an existing Employee record."""
	import json
	if isinstance(data, str):
		data = json.loads(data)

	employee_id = data.get("name")
	if not employee_id:
		frappe.throw("Employee ID is required")

	emp = frappe.get_doc("Employee", employee_id)
	emp.first_name = (data.get("first_name") or emp.first_name or "").strip()
	emp.last_name = (data.get("last_name") or "").strip()
	emp.employee_name = " ".join(filter(None, [emp.first_name, emp.last_name]))
	emp.gender = data.get("gender") or emp.gender or "Male"
	emp.date_of_birth = data.get("date_of_birth") or emp.date_of_birth or None
	emp.date_of_joining = data.get("date_of_joining") or emp.date_of_joining or frappe.utils.today()
	emp.cell_number = data.get("mobile") or ""
	emp.personal_email = data.get("email") or ""
	emp.current_address = data.get("current_address") or ""
	emp.save(ignore_permissions=True)

	return {"name": emp.name, "employee_name": emp.employee_name}


@frappe.whitelist()
def get_employee_list(status=None):
	"""Return a list of employees."""
	filters = {}
	if status and status not in ("undefined", "All"):
		filters["status"] = status
	return frappe.get_all(
		"Employee",
		filters=filters,
		fields=[
			"name",
			"first_name",
			"last_name",
			"employee_name",
			"designation",
			"gender",
			"status",
			"cell_number",
			"personal_email",
			"date_of_joining",
		],
		order_by="employee_name asc",
	)


@frappe.whitelist()
def get_leave_types():
	"""Get all active Leave Types."""
	return frappe.get_all("Leave Type", fields=["name"])


@frappe.whitelist()
def create_leave_application(data):
	"""Create a new Leave Application."""
	import json
	if isinstance(data, str):
		data = json.loads(data)

	employee = data.get("employee")
	leave_type = data.get("leave_type")
	from_date = data.get("from_date")
	to_date = data.get("to_date")
	half_day = data.get("half_day") or 0
	half_day_date = data.get("half_day_date") or None
	reason = data.get("reason") or ""
	leave_approver = data.get("leave_approver") or None

	if not employee:
		frappe.throw("Employee is required")
	if not leave_type:
		frappe.throw("Leave Type is required")
	if not from_date:
		frappe.throw("From Date is required")
	if not to_date:
		frappe.throw("To Date is required")

	# Fetch company from Employee
	company = frappe.db.get_value("Employee", employee, "company")
	if not company:
		company = frappe.defaults.get_global_default("company")

	doc = frappe.new_doc("Leave Application")
	doc.employee = employee
	doc.leave_type = leave_type
	doc.company = company
	doc.from_date = from_date
	doc.to_date = to_date
	doc.half_day = int(half_day)
	if doc.half_day:
		doc.half_day_date = half_day_date or from_date
	doc.reason = reason
	doc.leave_approver = leave_approver
	doc.posting_date = frappe.utils.today()
	doc.status = "Open"
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "employee": doc.employee, "status": doc.status}


@frappe.whitelist()
def get_leave_approvers():
	"""Get list of active system users who can approve leaves."""
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)


@frappe.whitelist()
def get_pending_leave_applications():
	"""Get pending Leave Applications where current user is the leave approver."""
	current_user = frappe.session.user
	filters = {"status": "Open"}

	# Allow Administrator to see all pending leave applications
	if current_user != "Administrator":
		filters["leave_approver"] = current_user

	apps = frappe.get_all(
		"Leave Application",
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_type",
			"from_date",
			"to_date",
			"half_day",
			"half_day_date",
			"total_leave_days",
			"reason",
		],
		order_by="creation desc",
	)
	return apps


@frappe.whitelist()
def approve_leave_application(leave_application):
	"""Approve a Leave Application."""
	doc = frappe.get_doc("Leave Application", leave_application)
	if doc.leave_approver != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You are not authorized to approve this leave application")

	doc.status = "Approved"
	doc.submit()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_leave_application(leave_application):
	"""Reject a Leave Application."""
	doc = frappe.get_doc("Leave Application", leave_application)
	if doc.leave_approver != frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You are not authorized to reject this leave application")

	doc.status = "Rejected"
	doc.submit()
	return {"name": doc.name, "status": doc.status}

