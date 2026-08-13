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
	doc.description = reason
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
	filters = {"docstatus": 0}

	# Allow Administrator, System Manager, or HR Manager to see all pending applications
	user_roles = frappe.get_roles(current_user)
	if not any(role in user_roles for role in ["Administrator", "System Manager", "HR Manager"]):
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
			# hrms stores the free-text reason in `description`; there is no `reason`
			# column, and selecting one made this whole query fail with a SQL error.
			"description as reason",
			"status",
			"posting_date",
			"leave_approver",
		],
		order_by="from_date desc, creation desc",
	)
	return apps


@frappe.whitelist()
def approve_leave_application(leave_application):
	"""Approve a Leave Application."""
	doc = frappe.get_doc("Leave Application", leave_application)
	user_roles = frappe.get_roles(frappe.session.user)
	if doc.leave_approver != frappe.session.user and not any(
		role in user_roles for role in ["Administrator", "System Manager", "HR Manager"]
	):
		frappe.throw("You are not authorized to approve this leave application")

	doc.status = "Approved"
	doc.submit()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_leave_application(leave_application):
	"""Reject a Leave Application."""
	doc = frappe.get_doc("Leave Application", leave_application)
	user_roles = frappe.get_roles(frappe.session.user)
	if doc.leave_approver != frappe.session.user and not any(
		role in user_roles for role in ["Administrator", "System Manager", "HR Manager"]
	):
		frappe.throw("You are not authorized to reject this leave application")

	doc.status = "Rejected"
	doc.submit()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_hrms_dashboard_data():
	"""Get real metrics, attendance records, payroll, and leave balances for the HRMS dashboard."""
	import datetime
	import calendar
	from frappe.utils import getdate, get_datetime, today as frappe_today

	today = getdate(frappe_today())
	year_start = datetime.date(today.year, 1, 1)
	year_end = datetime.date(today.year, 12, 31)

	# 1. Active Employees
	active_employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name"],
		order_by="employee_name asc"
	)
	employee_count = len(active_employees)

	# 2. Present count today
	attendances = frappe.get_all(
		"Attendance",
		filters={"attendance_date": today, "docstatus": ("<", 2)},
		fields=["name", "employee", "status", "in_time", "out_time"]
	)
	att_map = {att.employee: att for att in attendances}
	present_count = sum(1 for att in attendances if att.status in ("Present", "Half Day"))

	# 3. On leave count today
	on_leave_count = frappe.db.count("Leave Application", {
		"from_date": ("<=", today),
		"to_date": (">=", today),
		"status": "Approved",
		"docstatus": 1
	})

	# 4. Payroll stats for current month
	current_month_start = datetime.date(today.year, today.month, 1)
	latest_slip = frappe.get_all("Salary Slip", order_by="end_date desc", limit=1, fields=["start_date", "end_date"])
	if latest_slip:
		p_start = latest_slip[0].start_date
		p_end = latest_slip[0].end_date
		month_name = getdate(p_start).strftime("%B")
	else:
		p_start = current_month_start
		last_day = calendar.monthrange(today.year, today.month)[1]
		p_end = datetime.date(today.year, today.month, last_day)
		month_name = today.strftime("%B")

	slips = frappe.get_all(
		"Salary Slip",
		filters={"start_date": p_start, "end_date": p_end, "docstatus": ("<", 2)},
		fields=["name", "employee", "employee_name", "gross_pay", "net_pay", "total_deduction", "docstatus"]
	)

	salary_pool = sum(float(s.net_pay or 0) for s in slips)
	processed_count = sum(1 for s in slips if s.docstatus == 1)
	total_count = employee_count
	percent = int((processed_count / total_count * 100)) if total_count > 0 else 0

	payroll_status = {
		"month_name": month_name,
		"processed_count": processed_count,
		"total_count": total_count,
		"percent": percent,
		"salary_pool": salary_pool
	}

	# 5. Attendance details list
	attendance_list = []
	for emp in active_employees:
		att = att_map.get(emp.name)
		in_time_str = "--:--"
		out_time_str = "--:--"
		if att:
			if att.in_time:
				try:
					in_dt = get_datetime(att.in_time)
					in_time_str = in_dt.strftime("%I:%M %p")
				except Exception:
					pass
			if att.out_time:
				try:
					out_dt = get_datetime(att.out_time)
					out_time_str = out_dt.strftime("%I:%M %p")
				except Exception:
					pass
		attendance_list.append({
			"id": emp.name,
			"name": emp.employee_name,
			"in": in_time_str,
			"out": out_time_str,
			"status": att.status if att else "Absent",
			"attendance_record_name": att.name if att else None
		})

	# 6. Leave Balance Details
	allocations = frappe.get_all(
		"Leave Allocation",
		filters={"docstatus": 1, "from_date": ("<=", today), "to_date": (">=", today)},
		fields=["employee", "leave_type", "total_leaves_allocated"]
	)
	alloc_map = {}
	for alloc in allocations:
		alloc_map.setdefault(alloc.employee, {})[alloc.leave_type] = float(alloc.total_leaves_allocated or 0)

	leaves_taken = frappe.get_all(
		"Leave Application",
		filters={"status": "Approved", "docstatus": 1, "from_date": (">=", year_start), "to_date": ("<=", year_end)},
		fields=["employee", "leave_type", "total_leave_days"]
	)
	taken_map = {}
	for l in leaves_taken:
		taken_map.setdefault(l.employee, {}).setdefault(l.leave_type, 0.0)
		taken_map[l.employee][l.leave_type] += float(l.total_leave_days or 0)

	leave_balances = []
	for emp in active_employees:
		emp_alloc = alloc_map.get(emp.name, {})
		emp_taken = taken_map.get(emp.name, {})

		casual_allocated = emp_alloc.get("Casual Leave", 0.0)
		casual_taken = emp_taken.get("Casual Leave", 0.0)

		sick_allocated = emp_alloc.get("Sick Leave", 0.0)
		sick_taken = emp_taken.get("Sick Leave", 0.0)

		privilege_allocated = emp_alloc.get("Privilege Leave", 0.0)
		privilege_taken = emp_taken.get("Privilege Leave", 0.0)

		total_allocated = sum(emp_alloc.values())
		total_taken = sum(emp_taken.values())
		remaining = max(0.0, total_allocated - total_taken)

		status = "Low Balance" if (total_allocated > 0 and remaining / total_allocated < 0.2) else "Good Standing"
		if total_allocated == 0:
			status = "No Allocation"

		leave_balances.append({
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"casual_taken": casual_taken,
			"casual_allocated": casual_allocated,
			"sick_taken": sick_taken,
			"sick_allocated": sick_allocated,
			"privilege_taken": privilege_taken,
			"privilege_allocated": privilege_allocated,
			"remaining_balance": remaining,
			"status": status
		})

	return {
		"stats": {
			"employee_count": employee_count,
			"present_count": present_count,
			"on_leave_count": on_leave_count,
			"payroll": payroll_status
		},
		"attendance": attendance_list,
		"payroll": slips,
		"leave_balances": leave_balances
	}


