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
	if status:
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

