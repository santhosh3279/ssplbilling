"""Payroll Run page (/hrms/payroll): a month-at-a-time front for hrms' Payroll Entry.

The run is split into the same steps as the desk buttons, one request each, so every
step commits before the next starts:

    create_payroll_run    → draft Payroll Entry with the chosen employees
    create_salary_slips   → submits the entry; hrms creates the draft Salary Slips
    submit_salary_slips   → submits the slips; hrms books the accrual Journal Entry
    cancel_payroll_run    → deletes a draft entry, or cancels a submitted one (hrms
                            cancels + deletes its slips and journal entries)

hrms swallows failures inside slip creation / submission (it rolls back, writes
status "Failed" + error_message on the entry and returns normally) and reports the
rest through msgprint. So every action re-reads the entry from the database and hands
back the messages hrms queued, instead of trusting a clean response.

Nothing here uses ignore_permissions. The write steps rely on hrms / the ORM checking
Payroll Entry permission; the read (get_payroll_overview) queries with qb, so it checks
Payroll Entry read permission explicitly first.
"""

import json

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import cint, date_diff, flt, get_last_day, getdate, strip_html
from hrms.utils.holiday_list import get_holiday_dates_between_range, get_holiday_list_for_employee

PAYROLL_ENTRY = "Payroll Entry"
FREQUENCY = "Monthly"

# Attendance statuses as hrms stores them, keyed to the column the page shows.
ATTENDANCE_COLUMNS = {
	"Present": "present",
	"Work From Home": "present",
	"Half Day": "half_day",
	"Absent": "absent",
	"On Leave": "on_leave",
}


def _period(month):
	"""'2026-10' → (2026-10-01, 2026-10-31)."""
	try:
		start = getdate(f"{month}-01")
	except Exception:
		frappe.throw(_("Invalid month {0}").format(month))
	return start, get_last_day(start)


def _company(company=None):
	if company:
		return company
	return (
		frappe.defaults.get_user_default("company")
		or frappe.defaults.get_global_default("company")
		or frappe.db.get_value("Company", {}, "name")
	)


def _company_details(company):
	return frappe.db.get_value(
		"Company",
		company,
		[
			"name",
			"default_currency",
			"cost_center",
			"default_payroll_payable_account",
		],
		as_dict=True,
	)


def _payroll_settings():
	return frappe.get_cached_value(
		"Payroll Settings",
		None,
		(
			"payroll_based_on",
			"consider_unmarked_attendance_as",
			"include_holidays_in_total_working_days",
			"email_salary_slip_to_employee",
		),
		as_dict=True,
	)


def _employees(company, start, end):
	"""Same population hrms pays: not Inactive, joined by the period end, not relieved
	before it starts."""
	emp = frappe.qb.DocType("Employee")
	return (
		frappe.qb.from_(emp)
		.select(
			emp.name.as_("employee"),
			emp.employee_name,
			emp.department,
			emp.designation,
			emp.date_of_joining,
			emp.relieving_date,
			emp.status,
		)
		.where(
			(emp.company == company)
			& (emp.status != "Inactive")
			& ((emp.date_of_joining <= end) | emp.date_of_joining.isnull())
			& ((emp.relieving_date >= start) | emp.relieving_date.isnull())
		)
		.orderby(emp.employee_name)
	).run(as_dict=True)


def _assignments(employees, company, end):
	"""Latest submitted Salary Structure Assignment per employee that is in force by
	the period end, with its structure's state."""
	if not employees:
		return {}
	ssa = frappe.qb.DocType("Salary Structure Assignment")
	ss = frappe.qb.DocType("Salary Structure")
	rows = (
		frappe.qb.from_(ssa)
		.join(ss)
		.on(ss.name == ssa.salary_structure)
		.select(
			ssa.name,
			ssa.employee,
			ssa.salary_structure,
			ssa.from_date,
			ssa.base,
			ssa.variable,
			ssa.currency,
			ssa.payroll_payable_account,
			ss.is_active,
			ss.payroll_frequency,
			ss.docstatus.as_("structure_docstatus"),
		)
		.where(
			(ssa.docstatus == 1)
			& (ssa.company == company)
			& (ssa.from_date <= end)
			& ssa.employee.isin(employees)
		)
		.orderby(ssa.from_date)
	).run(as_dict=True)
	# Ordered by from_date, so the last one written per employee is the one in force.
	return {row.employee: row for row in rows}


def _attendance(employees, start, end):
	"""{employee: {present, half_day, absent, on_leave, marked}} from submitted Attendance."""
	if not employees:
		return {}
	att = frappe.qb.DocType("Attendance")
	rows = (
		frappe.qb.from_(att)
		.select(att.employee, att.status, Count(att.name).as_("n"))
		.where(
			(att.docstatus == 1)
			& att.employee.isin(employees)
			& (att.attendance_date >= start)
			& (att.attendance_date <= end)
		)
		.groupby(att.employee, att.status)
	).run(as_dict=True)

	out = {}
	for row in rows:
		counts = out.setdefault(
			row.employee, {"present": 0, "half_day": 0, "absent": 0, "on_leave": 0, "marked": 0}
		)
		column = ATTENDANCE_COLUMNS.get(row.status)
		if column:
			counts[column] += cint(row.n)
		counts["marked"] += cint(row.n)
	return out


def _slips(employees, company, start, end):
	"""Non-cancelled Salary Slips covering exactly this period, one per employee (the
	newest wins if somebody made two by hand)."""
	if not employees:
		return {}
	rows = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": ["in", employees],
			"company": company,
			"start_date": start,
			"end_date": end,
			"docstatus": ["<", 2],
		},
		fields=[
			"name",
			"employee",
			"docstatus",
			"status",
			"payroll_entry",
			"total_working_days",
			"payment_days",
			"absent_days",
			"leave_without_pay",
			"gross_pay",
			"total_deduction",
			"net_pay",
		],
		order_by="creation asc",
	)
	return {row.employee: row for row in rows}


def _run(company, start, end):
	"""The live (non-cancelled) Payroll Entry for this company and period, if any."""
	rows = frappe.get_all(
		PAYROLL_ENTRY,
		filters={"company": company, "start_date": start, "end_date": end, "docstatus": ["<", 2]},
		fields=[
			"name",
			"docstatus",
			"status",
			"error_message",
			"posting_date",
			"payroll_payable_account",
			"salary_slips_created",
			"salary_slips_submitted",
			"number_of_employees",
		],
		order_by="creation desc",
		limit=1,
	)
	if not rows:
		return None
	run = rows[0]
	run["employees"] = frappe.get_all(
		"Payroll Employee Detail", filters={"parent": run.name, "parenttype": PAYROLL_ENTRY}, pluck="employee"
	)
	slip_counts = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": run.name},
		fields=["docstatus", {"COUNT": "*", "as": "n"}],
		group_by="docstatus",
	)
	counts = {cint(r.docstatus): cint(r.n) for r in slip_counts}
	run["draft_slips"] = counts.get(0, 0)
	run["submitted_slips"] = counts.get(1, 0)
	run["error_message"] = strip_html(run.error_message or "")
	return run


def _components_without_account(structures, company):
	"""Salary components used by these structures that have no account for the company.
	hrms only finds out when it books the accrual Journal Entry, after the slips are
	already submitted, so it is checked up front."""
	if not structures:
		return []
	sd = frappe.qb.DocType("Salary Detail")
	components = (
		frappe.qb.from_(sd)
		.select(sd.salary_component)
		.distinct()
		.where((sd.parenttype == "Salary Structure") & sd.parent.isin(list(structures)))
	).run(pluck=True)
	missing = []
	for component in components:
		if frappe.db.get_value("Salary Component", component, "statistical_component"):
			continue
		if not frappe.db.exists("Salary Component Account", {"parent": component, "company": company}):
			missing.append(component)
	return sorted(missing)


def _check(level, code, message, link=None):
	return {"level": level, "code": code, "message": message, "link": link}


@frappe.whitelist()
def get_payroll_overview(month, company=None):
	"""Everything the page shows for one month: readiness checks, one row per employee
	(structure, attendance, slip) and the payroll run for the period."""
	# The rows carry every employee's salary and are read with qb, which skips
	# permission checks. Salary Slip / Salary Structure Assignment are no gate: the
	# Employee role reads them too (its own record only). Payroll Entry is HR Manager
	# only by default — the same people who can run payroll at all.
	frappe.has_permission(PAYROLL_ENTRY, "read", throw=True)
	company = _company(company)
	if not company:
		frappe.throw(_("No Company found"))
	start, end = _period(month)
	comp = _company_details(company)
	settings = _payroll_settings()
	period_days = date_diff(end, start) + 1

	employees = _employees(company, start, end)
	ids = [e.employee for e in employees]
	assignments = _assignments(ids, company, end)
	attendance = _attendance(ids, start, end)
	slips = _slips(ids, company, start, end)

	today = getdate()
	holiday_lists = set()

	rows = []
	for e in employees:
		ssa = assignments.get(e.employee)
		# hrms v16 resolves holidays through Holiday List Assignment (employee first, then
		# company), not Employee.holiday_list / Company.default_holiday_list. Slip creation
		# looks one up for the period and again for today, so both must resolve.
		holiday_list = get_holiday_list_for_employee(e.employee, raise_exception=False, as_on=end)
		has_list_today = bool(get_holiday_list_for_employee(e.employee, raise_exception=False, as_on=today))
		if holiday_list:
			holiday_lists.add(holiday_list)
		# Days the employee was on the rolls this period
		first = max(start, getdate(e.date_of_joining)) if e.date_of_joining else start
		last = min(end, getdate(e.relieving_date)) if e.relieving_date else end
		on_roll = max(0, date_diff(last, first) + 1)
		holiday_count = (
			len(
				get_holiday_dates_between_range(
					e.employee, first, last, raise_exception_for_holiday_list=False
				)
			)
			if holiday_list and on_roll
			else 0
		)
		att = attendance.get(
			e.employee, {"present": 0, "half_day": 0, "absent": 0, "on_leave": 0, "marked": 0}
		)
		unmarked = max(0, on_roll - holiday_count - att["marked"])

		problem = None
		if not ssa:
			problem = _("No salary structure assigned")
		elif ssa.structure_docstatus != 1 or ssa.is_active != "Yes":
			problem = _("Structure {0} is not active").format(ssa.salary_structure)
		elif ssa.payroll_frequency != FREQUENCY:
			problem = _("Structure {0} is {1}, not Monthly").format(
				ssa.salary_structure, ssa.payroll_frequency
			)
		elif ssa.currency != comp.default_currency:
			problem = _("Assignment currency {0} differs from company").format(ssa.currency)
		elif ssa.payroll_payable_account != comp.default_payroll_payable_account:
			problem = _("Payable account {0} differs from company default").format(
				ssa.payroll_payable_account or "—"
			)
		elif not holiday_list or not has_list_today:
			problem = _("No Holiday List Assignment")

		slip = slips.get(e.employee)
		if slip and slip.docstatus == 1:
			state = "paid"
		elif slip:
			state = "draft"
		elif problem:
			state = "blocked"
		else:
			state = "ready"

		rows.append(
			{
				"employee": e.employee,
				"employee_name": e.employee_name,
				"department": e.department,
				"designation": e.designation,
				"salary_structure": ssa.salary_structure if ssa else None,
				"base": flt(ssa.base) if ssa else 0,
				"holiday_list": holiday_list,
				"holidays": holiday_count,
				"on_roll_days": on_roll,
				**att,
				"unmarked": unmarked,
				"problem": problem,
				"state": state,
				"slip": slip,
			}
		)

	checks = []
	if not settings.payroll_based_on:
		checks.append(
			_check(
				"blocker",
				"based_on",
				_("Payroll Settings has no 'Payroll based on' value."),
				"payroll-settings",
			)
		)
	elif settings.payroll_based_on == "Leave":
		checks.append(
			_check(
				"warning",
				"based_on",
				_(
					"Payroll is based on Leave, so absences recorded by the eSSL attendance are not deducted. "
					"Set 'Payroll based on' to Attendance in Payroll Settings."
				),
				"payroll-settings",
			)
		)
	if (
		settings.payroll_based_on == "Attendance"
		and (settings.consider_unmarked_attendance_as or "Present") == "Present"
	):
		checks.append(
			_check(
				"warning",
				"unmarked_as",
				_(
					"Unmarked days are paid as Present. The device only records days somebody punched, "
					"so a day nobody marked is paid unless 'Consider unmarked attendance as' is Absent."
				),
				"payroll-settings",
			)
		)
	if not comp.default_payroll_payable_account:
		checks.append(
			_check(
				"blocker",
				"payable",
				_("Company {0} has no Default Payroll Payable Account.").format(company),
				"company",
			)
		)
	no_holiday = [r for r in rows if r["problem"] == _("No Holiday List Assignment")]
	if not holiday_lists:
		checks.append(
			_check(
				"blocker",
				"holiday_list",
				_(
					"No Holiday List is assigned to company {0} or its employees. Create a Holiday List "
					"for the year, then a Holiday List Assignment for the company."
				).format(company),
				"holiday-list-assignment",
			)
		)
	elif no_holiday:
		checks.append(
			_check(
				"warning",
				"holiday_list",
				_("{0} employee(s) have no Holiday List Assignment covering this month.").format(
					len(no_holiday)
				),
				"holiday-list-assignment",
			)
		)
	for hl in sorted(holiday_lists):
		covers = frappe.db.get_value("Holiday List", hl, ["from_date", "to_date"], as_dict=True)
		if covers and (getdate(covers.from_date) > start or getdate(covers.to_date) < end):
			checks.append(
				_check(
					"warning",
					"holiday_cover",
					_("Holiday List {0} does not cover the whole month.").format(hl),
					"holiday-list",
				)
			)

	structures = {a.salary_structure for a in assignments.values()}
	missing_accounts = _components_without_account(structures, company)
	if missing_accounts:
		checks.append(
			_check(
				"blocker",
				"component_account",
				_("Salary components with no account for {0}: {1}").format(
					company, ", ".join(missing_accounts)
				),
				"salary-component",
			)
		)

	no_structure = [r for r in rows if r["state"] == "blocked"]
	if rows and len(no_structure) == len(rows):
		checks.append(
			_check(
				"blocker",
				"no_employees",
				_("No employee can be paid yet. Assign a Salary Structure to each employee first."),
				"salary-structure-assignment",
			)
		)
	elif no_structure:
		checks.append(
			_check(
				"warning",
				"some_blocked",
				_("{0} employee(s) will be left out — see the reason in their row.").format(
					len(no_structure)
				),
				"salary-structure-assignment",
			)
		)

	unmarked = [r for r in rows if r["unmarked"] > 0 and r["state"] in ("ready", "draft")]
	if unmarked:
		checks.append(
			_check(
				"warning",
				"unmarked",
				_("{0} employee(s) have days with no attendance this month.").format(len(unmarked)),
			)
		)

	return {
		"company": company,
		"companies": frappe.get_all("Company", pluck="name", order_by="name"),
		"month": month,
		"start_date": str(start),
		"end_date": str(end),
		"period_days": period_days,
		"currency": comp.default_currency,
		"payroll_payable_account": comp.default_payroll_payable_account,
		"settings": settings,
		"checks": checks,
		"employees": rows,
		"run": _run(company, start, end),
	}


def _messages():
	"""What hrms told the user through msgprint during this request, as plain text."""
	out = []
	for entry in frappe.local.message_log or []:
		msg = entry.get("message") if isinstance(entry, dict) else entry
		if isinstance(msg, str):
			try:
				msg = json.loads(msg).get("message", msg)
			except Exception:
				pass
		if msg:
			out.append(strip_html(str(msg)))
	# hrms repeats some notes once per slip
	return list(dict.fromkeys(out))


def _result(entry_name):
	pe = frappe.db.get_value(PAYROLL_ENTRY, entry_name, ["company", "start_date"], as_dict=True)
	run = _run(pe.company, pe.start_date, get_last_day(pe.start_date)) if pe else None
	return {"run": run, "messages": _messages()}


@frappe.whitelist()
def create_payroll_run(month, employees, company=None, posting_date=None):
	"""Step 1 — a draft Payroll Entry for the chosen employees."""
	company = _company(company)
	start, end = _period(month)
	if isinstance(employees, str):
		employees = json.loads(employees)
	employees = set(employees or [])
	if not employees:
		frappe.throw(_("Select at least one employee"))

	if _run(company, start, end):
		frappe.throw(_("A payroll run for this month already exists — reload the page to continue it."))

	comp = _company_details(company)
	if not comp.default_payroll_payable_account:
		frappe.throw(_("Set a Default Payroll Payable Account on Company {0}").format(company))

	pe = frappe.new_doc(PAYROLL_ENTRY)
	pe.company = company
	pe.posting_date = posting_date or end
	pe.payroll_frequency = FREQUENCY
	pe.start_date = start
	pe.end_date = end
	pe.currency = comp.default_currency
	pe.exchange_rate = 1
	pe.payroll_payable_account = comp.default_payroll_payable_account
	pe.cost_center = comp.cost_center
	# Attendance gaps are shown as warnings on the page. Validating them here would
	# refuse the whole run, because eSSL only creates Attendance on days with a punch.
	pe.validate_attendance = 0

	# hrms' own eligibility (structure, frequency, payable account, already paid)
	pe.fill_employee_details()
	eligible = {row.employee for row in pe.employees}
	chosen = [row for row in pe.employees if row.employee in employees]
	if not chosen:
		frappe.throw(_("None of the selected employees can be paid this month."))
	pe.set("employees", chosen)
	pe.insert()

	result = _result(pe.name)
	skipped = sorted(employees - eligible)
	if skipped:
		result["messages"].append(_("Left out by HRMS (not eligible): {0}").format(", ".join(skipped)))
	return result


@frappe.whitelist()
def create_salary_slips(payroll_entry):
	"""Step 2 — submit the entry; hrms creates a draft Salary Slip per employee. Also
	retries creation on an entry whose first attempt failed."""
	pe = frappe.get_doc(PAYROLL_ENTRY, payroll_entry)
	if pe.docstatus == 0:
		pe.submit()
	elif pe.docstatus == 1 and not pe.salary_slips_created:
		pe.create_salary_slips()
	else:
		frappe.throw(_("Salary slips were already created for {0}").format(pe.name))
	return _result(pe.name)


@frappe.whitelist()
def submit_salary_slips(payroll_entry):
	"""Step 3 — submit the draft slips; hrms books the accrual Journal Entry and emails
	the slips if Payroll Settings asks it to."""
	pe = frappe.get_doc(PAYROLL_ENTRY, payroll_entry)
	if pe.docstatus != 1:
		frappe.throw(_("Create the salary slips first"))
	pe.submit_salary_slips()
	return _result(pe.name)


@frappe.whitelist()
def cancel_payroll_run(payroll_entry):
	"""Throw the run away: a draft entry is deleted; a submitted one is cancelled, which
	makes hrms cancel and delete its slips and cancel the accrual journal entry."""
	pe = frappe.get_doc(PAYROLL_ENTRY, payroll_entry)
	if pe.docstatus == 0:
		frappe.delete_doc(PAYROLL_ENTRY, pe.name)
	elif pe.docstatus == 1:
		pe.cancel()
	return {"messages": _messages()}
