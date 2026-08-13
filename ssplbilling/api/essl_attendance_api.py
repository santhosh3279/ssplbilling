"""Maps eSSL device user ids to Employee records and turns device punches into
Employee Checkin + Attendance documents.

The sync is idempotent by design: every run re-reads a small overlapping window
(see Lookback Days in eSSL Sync Settings) and skips anything already recorded, so
the 10-minute scheduler tick can run forever without duplicating a single punch.
"""

import json

import frappe
from frappe.utils import flt, get_datetime, getdate, now_datetime

from ssplbilling.api.essl_machine_api import ESSL_MACHINE_DOCTYPE, connect_machine, get_machine_rows

MAPPING_DOCTYPE = "eSSL Employee Mapping"
SETTINGS_DOCTYPE = "eSSL Sync Settings"

# Window used the very first time a machine is synced (it has no watermark yet).
# Without this a fresh device dumps years of logs and back-dates thousands of
# Attendance records — the manual sync takes an explicit from_date for backfills.
DEFAULT_INITIAL_DAYS = 7


def _settings():
	doc = frappe.get_cached_doc(SETTINGS_DOCTYPE)
	return {
		"enable_auto_sync": bool(doc.enable_auto_sync),
		"lookback_days": int(doc.lookback_days or 2),
		"create_checkins": bool(doc.create_checkins),
		"create_attendance": bool(doc.create_attendance),
		"mark_half_day_below_hours": flt(doc.mark_half_day_below_hours),
	}


@frappe.whitelist()
def get_sync_settings():
	return _settings()


# ─────────────────────────── mapping CRUD ───────────────────────────


@frappe.whitelist()
def get_mappings():
	"""Every device-user-id to Employee mapping, with the employee's current status."""
	rows = frappe.get_all(
		MAPPING_DOCTYPE,
		fields=["name", "machine_user_id", "employee", "employee_name", "machine", "enabled"],
		order_by="machine_user_id asc",
	)
	employees = {
		e.name: e
		for e in frappe.get_all("Employee", fields=["name", "employee_name", "status", "designation"])
	}
	for row in rows:
		emp = employees.get(row.employee)
		row["employee_name"] = (emp and emp.employee_name) or row.employee_name
		row["employee_status"] = (emp and emp.status) or "Unknown"
		row["designation"] = (emp and emp.designation) or ""
	return rows


@frappe.whitelist()
def save_mapping(data):
	"""Create or update one mapping. Pass name to update, omit it to create."""
	if isinstance(data, str):
		data = json.loads(data)

	if data.get("name") and frappe.db.exists(MAPPING_DOCTYPE, data["name"]):
		doc = frappe.get_doc(MAPPING_DOCTYPE, data["name"])
	else:
		doc = frappe.new_doc(MAPPING_DOCTYPE)

	doc.machine_user_id = str(data.get("machine_user_id") or "").strip()
	doc.employee = data.get("employee")
	doc.machine = data.get("machine") or None
	doc.enabled = 1 if data.get("enabled", 1) else 0
	doc.save(ignore_permissions=True)

	return {"name": doc.name, "employee_name": doc.employee_name}


@frappe.whitelist()
def delete_mapping(name):
	frappe.delete_doc(MAPPING_DOCTYPE, name, ignore_permissions=True)
	return {"deleted": name}


def _mapping_index():
	"""{(machine_user_id, machine or None): employee_row}. A mapping with no machine
	is the fallback used by every device."""
	index = {}
	rows = frappe.get_all(
		MAPPING_DOCTYPE,
		filters={"enabled": 1},
		fields=["machine_user_id", "employee", "machine"],
	)
	employees = {
		e.name: e
		for e in frappe.get_all(
			"Employee", filters={"status": "Active"}, fields=["name", "employee_name", "company"]
		)
	}
	for row in rows:
		emp = employees.get(row.employee)
		if not emp:
			# Left/Inactive employees never receive attendance
			continue
		index[(str(row.machine_user_id), row.machine or None)] = emp
	return index


def _resolve_employee(index, user_id, machine):
	return index.get((str(user_id), machine)) or index.get((str(user_id), None))


# ─────────────────────────── device users ───────────────────────────


@frappe.whitelist()
def get_device_users(machine=None):
	"""Read the user list off the devices so unmapped ids can be spotted and mapped."""
	index = _mapping_index()
	users = []
	results = []

	for row in get_machine_rows(machine):
		summary = {"machine": row.name, "ip_address": row.ip_address, "store": row.store, "users": 0, "error": None}
		conn = None
		try:
			conn = connect_machine(row)
			for user in conn.get_users() or []:
				emp = _resolve_employee(index, user.user_id, row.name)
				users.append(
					{
						"machine": row.name,
						"store": row.store,
						"user_id": str(user.user_id),
						"device_name": user.name or "",
						"employee": emp.name if emp else None,
						"employee_name": emp.employee_name if emp else None,
					}
				)
				summary["users"] += 1
		except Exception as e:
			summary["error"] = str(e) or e.__class__.__name__
		finally:
			if conn:
				try:
					conn.disconnect()
				except Exception:
					pass
		results.append(summary)

	users.sort(key=lambda u: (u["employee"] is not None, int(u["user_id"]) if u["user_id"].isdigit() else 0))
	return {"machines": results, "users": users}


@frappe.whitelist()
def auto_map_by_name(machine=None):
	"""Map device users to employees whose name matches the name stored on the device.

	Only exact (case/space-insensitive) matches are taken, and only when the name
	belongs to exactly one Active employee — anything ambiguous is left for a human.
	"""
	device = get_device_users(machine)
	employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name"])

	by_name = {}
	for emp in employees:
		key = " ".join((emp.employee_name or "").lower().split())
		by_name.setdefault(key, []).append(emp.name)

	created = []
	skipped = []

	for user in device["users"]:
		if user["employee"]:
			continue
		key = " ".join((user["device_name"] or "").lower().split())
		matches = by_name.get(key) or []
		if len(matches) != 1:
			skipped.append(
				{
					"user_id": user["user_id"],
					"device_name": user["device_name"],
					"reason": "No matching employee" if not matches else "Name matches more than one employee",
				}
			)
			continue

		doc = frappe.new_doc(MAPPING_DOCTYPE)
		doc.machine_user_id = user["user_id"]
		doc.employee = matches[0]
		doc.enabled = 1
		doc.insert(ignore_permissions=True)
		created.append({"user_id": user["user_id"], "employee": matches[0], "employee_name": user["device_name"]})

	frappe.db.commit()
	return {"created": created, "skipped": skipped, "machines": device["machines"]}


# ─────────────────────────── the sync itself ───────────────────────────


def _create_checkin(employee, timestamp, machine):
	if frappe.db.exists("Employee Checkin", {"employee": employee, "time": timestamp}):
		return False
	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee
	doc.time = timestamp
	doc.device_id = machine
	# hrms builds its own Attendance from checkins via Shift Type auto-attendance;
	# this sync writes Attendance itself, so the two must not both act on the punch.
	doc.skip_auto_attendance = 1
	doc.insert(ignore_permissions=True)
	return True


# Statuses this sync assigns itself. Anything else on an existing record was set
# by a human (or by Leave Application) and is never overwritten by a later tick.
SYNC_OWNED_STATUSES = ("Present", "Half Day")


def _attendance_status(hours, half_day_below):
	if half_day_below and hours < half_day_below:
		return "Half Day"
	return "Present"


def _upsert_attendance(employee, emp_row, day, in_time, out_time, half_day_below):
	"""Insert (and submit) Attendance for the day, or widen the existing record's
	in/out window. Returns 'created', 'updated' or None."""
	existing = frappe.db.get_value(
		"Attendance",
		{"employee": employee, "attendance_date": day, "docstatus": ("<", 2)},
		["name", "in_time", "out_time", "status", "docstatus"],
		as_dict=True,
	)

	hours = 0.0
	if in_time and out_time and out_time > in_time:
		hours = flt((out_time - in_time).total_seconds() / 3600.0, 2)

	if existing:
		old_in = get_datetime(existing.in_time) if existing.in_time else None
		old_out = get_datetime(existing.out_time) if existing.out_time else None
		new_in = min([t for t in (in_time, old_in) if t], default=None)
		new_out = max([t for t in (out_time, old_out) if t], default=None)
		if new_in == old_in and new_out == old_out:
			return None
		new_hours = 0.0
		if new_in and new_out and new_out > new_in:
			new_hours = flt((new_out - new_in).total_seconds() / 3600.0, 2)
		# Submitted Attendance cannot be re-saved through the ORM, so the window is
		# widened with a direct field update.
		values = {"in_time": new_in, "out_time": new_out, "working_hours": new_hours}
		# A mid-day tick stamps the status from a partial window (9am-2pm looks like a
		# Half Day); once the evening punch widens the window the status has to follow,
		# or the employee stays Half Day for a full shift.
		if existing.status in SYNC_OWNED_STATUSES:
			values["status"] = _attendance_status(new_hours, half_day_below)
		frappe.db.set_value(
			"Attendance",
			existing.name,
			values,
			update_modified=False,
		)
		return "updated"

	status = _attendance_status(hours, half_day_below)

	doc = frappe.new_doc("Attendance")
	doc.employee = employee
	doc.attendance_date = day
	doc.status = status
	doc.company = emp_row.company or frappe.defaults.get_global_default("company")
	doc.in_time = in_time
	doc.out_time = out_time
	doc.working_hours = hours
	doc.insert(ignore_permissions=True)
	doc.submit()
	return "created"


def _sync_machine(row, settings, from_date=None):
	"""Pull one device and write the documents. Never raises — the caller reports
	the error row and moves to the next machine."""
	summary = {
		"machine": row.name,
		"ip_address": row.ip_address,
		"store": row.store,
		"logs": 0,
		"mapped": 0,
		"unmapped_ids": [],
		"checkins_created": 0,
		"attendance_created": 0,
		"attendance_updated": 0,
		"skipped_future": 0,
		"error": None,
	}

	if from_date:
		window_start = getdate(from_date)
	elif row.last_sync:
		window_start = frappe.utils.add_days(getdate(row.last_sync), -settings["lookback_days"])
	else:
		window_start = frappe.utils.add_days(getdate(now_datetime()), -DEFAULT_INITIAL_DAYS)

	index = _mapping_index()
	now = now_datetime()
	unmapped = set()
	# {(employee, date): [timestamps]}
	per_day = {}

	conn = None
	try:
		conn = connect_machine(row)
		for att in conn.get_attendance() or []:
			stamp = att.timestamp
			if stamp.date() < window_start:
				continue
			if stamp > now:
				# Devices with a wrong clock emit logs dated in the future; recording
				# them would create Attendance for days that have not happened yet.
				summary["skipped_future"] += 1
				continue

			summary["logs"] += 1
			emp = _resolve_employee(index, att.user_id, row.name)
			if not emp:
				unmapped.add(str(att.user_id))
				continue

			summary["mapped"] += 1
			per_day.setdefault((emp.name, stamp.date()), []).append(stamp)
	except Exception as e:
		summary["error"] = str(e) or e.__class__.__name__
		return summary
	finally:
		if conn:
			try:
				conn.disconnect()
			except Exception:
				pass

	summary["unmapped_ids"] = sorted(unmapped)

	employees = {e.name: e for e in frappe.get_all("Employee", fields=["name", "company"])}

	for (employee, day), stamps in per_day.items():
		try:
			stamps.sort()
			if settings["create_checkins"]:
				for stamp in stamps:
					if _create_checkin(employee, stamp, row.name):
						summary["checkins_created"] += 1

			if settings["create_attendance"]:
				action = _upsert_attendance(
					employee,
					employees.get(employee) or frappe._dict({"company": None}),
					day,
					stamps[0],
					stamps[-1],
					settings["mark_half_day_below_hours"],
				)
				if action == "created":
					summary["attendance_created"] += 1
				elif action == "updated":
					summary["attendance_updated"] += 1
		except Exception:
			frappe.log_error(
				title=f"eSSL attendance sync failed for {employee} on {day}",
				message=frappe.get_traceback(),
			)

	frappe.db.set_value(ESSL_MACHINE_DOCTYPE, row.name, "last_sync", now, update_modified=False)
	return summary


@frappe.whitelist()
def sync_attendance(machine=None, from_date=None):
	"""Pull the devices and create the documents. Safe to call repeatedly — a punch
	already recorded is skipped rather than duplicated."""
	settings = _settings()
	results = []

	for row in get_machine_rows(machine):
		try:
			results.append(_sync_machine(row, settings, from_date))
		except Exception as e:
			frappe.log_error(title=f"eSSL sync failed for {row.name}", message=frappe.get_traceback())
			results.append({"machine": row.name, "ip_address": row.ip_address, "error": str(e)})
		# Commit per machine so one dead device does not throw away the progress
		# already made on the others.
		frappe.db.commit()

	counters = (
		"logs",
		"mapped",
		"checkins_created",
		"attendance_created",
		"attendance_updated",
		"skipped_future",
	)
	totals = {key: sum(r.get(key) or 0 for r in results) for key in counters}
	unmapped = sorted({uid for r in results for uid in (r.get("unmapped_ids") or [])})

	return {
		"synced_at": frappe.utils.now(),
		"machines": results,
		"totals": totals,
		"unmapped_ids": unmapped,
	}


def run_auto_sync():
	"""Scheduler entry point — runs every 10 minutes (see hooks.py)."""
	try:
		if not _settings()["enable_auto_sync"]:
			return
		sync_attendance()
	except Exception:
		frappe.log_error(title="eSSL auto attendance sync failed", message=frappe.get_traceback())


# ─────────────────────────── attendance read ───────────────────────────


def _stamp_on(day, value):
	"""'HH:MM' from the form becomes a full datetime on the attendance date. A value
	that already carries a date is taken as is."""
	if not value:
		return None
	value = str(value)
	return get_datetime(f"{day} {value}:00" if len(value) <= 5 else value)


def _worked_hours(in_time, out_time):
	if in_time and out_time and out_time > in_time:
		return flt((out_time - in_time).total_seconds() / 3600.0, 2)
	return 0.0


@frappe.whitelist()
def create_manual_attendance(data):
	"""Create one Attendance record by hand, for days the devices never captured.

	Unlike the device sync this respects the status the user picked and refuses to
	touch a day that already has a record — correcting an existing day is an edit,
	not a create.
	"""
	if isinstance(data, str):
		data = json.loads(data)

	employee = data.get("employee")
	attendance_date = data.get("attendance_date")
	if not employee or not attendance_date:
		frappe.throw("Employee and date are required")

	attendance_date = getdate(attendance_date)
	if attendance_date > getdate(now_datetime()):
		frappe.throw("Attendance cannot be dated in the future")

	existing = frappe.db.get_value(
		"Attendance",
		{"employee": employee, "attendance_date": attendance_date, "docstatus": ("<", 2)},
		"name",
	)
	if existing:
		frappe.throw(f"Attendance {existing} already exists for this employee on {attendance_date}")

	emp = frappe.db.get_value("Employee", employee, ["name", "employee_name", "company"], as_dict=True)
	if not emp:
		frappe.throw(f"Employee {employee} not found")

	in_time = _stamp_on(attendance_date, data.get("in_time"))
	out_time = _stamp_on(attendance_date, data.get("out_time"))
	hours = _worked_hours(in_time, out_time)

	doc = frappe.new_doc("Attendance")
	doc.employee = employee
	doc.attendance_date = attendance_date
	doc.status = data.get("status") or "Present"
	doc.company = emp.company or frappe.defaults.get_global_default("company")
	doc.in_time = in_time
	doc.out_time = out_time
	doc.working_hours = hours
	doc.insert(ignore_permissions=True)
	doc.submit()

	return {
		"name": doc.name,
		"employee": doc.employee,
		"employee_name": emp.employee_name,
		"attendance_date": str(doc.attendance_date),
		"status": doc.status,
	}


@frappe.whitelist()
def update_attendance(data):
	"""Edit one Attendance record.

	Attendance is submittable, so a submitted record cannot simply be re-saved: it is
	cancelled and replaced by an amendment (name gains a -1 suffix) which keeps the
	audit trail intact. Drafts are edited in place.
	"""
	if isinstance(data, str):
		data = json.loads(data)

	name = data.get("name")
	if not name:
		frappe.throw("Attendance id is required")

	old = frappe.get_doc("Attendance", name)
	if old.docstatus == 2:
		frappe.throw(f"Attendance {name} is cancelled and can no longer be edited")

	day = getdate(data.get("attendance_date") or old.attendance_date)
	if day > getdate(now_datetime()):
		frappe.throw("Attendance cannot be dated in the future")

	employee = data.get("employee") or old.employee
	# Moving the record onto a day/employee that already has one would break the
	# one-record-per-employee-per-day rule hrms enforces.
	clash = frappe.db.get_value(
		"Attendance",
		{
			"employee": employee,
			"attendance_date": day,
			"docstatus": ("<", 2),
			"name": ("!=", name),
		},
		"name",
	)
	if clash:
		frappe.throw(f"Attendance {clash} already exists for this employee on {day}")

	in_time = _stamp_on(day, data.get("in_time"))
	out_time = _stamp_on(day, data.get("out_time"))
	status = data.get("status") or old.status
	company = old.company or frappe.db.get_value("Employee", employee, "company")

	if old.docstatus == 0:
		old.employee = employee
		old.attendance_date = day
		old.status = status
		old.in_time = in_time
		old.out_time = out_time
		old.working_hours = _worked_hours(in_time, out_time)
		old.save(ignore_permissions=True)
		return {"name": old.name, "amended": False}

	old.cancel()

	doc = frappe.new_doc("Attendance")
	doc.amended_from = old.name
	doc.employee = employee
	doc.attendance_date = day
	doc.status = status
	doc.company = company
	doc.in_time = in_time
	doc.out_time = out_time
	doc.working_hours = _worked_hours(in_time, out_time)
	doc.insert(ignore_permissions=True)
	doc.submit()

	return {"name": doc.name, "amended": True, "replaced": old.name}


@frappe.whitelist()
def delete_attendance(name):
	"""Cancel (when submitted) and delete one Attendance record."""
	doc = frappe.get_doc("Attendance", name)
	if doc.docstatus == 1:
		doc.cancel()
	frappe.delete_doc("Attendance", name, ignore_permissions=True, force=True)
	return {"deleted": name}


@frappe.whitelist()
def get_attendance_records(from_date=None, to_date=None, employee=None):
	"""Attendance rows for the page. Cancelled records are left out."""
	filters = {"docstatus": ("<", 2)}
	if from_date and to_date:
		filters["attendance_date"] = ("between", [getdate(from_date), getdate(to_date)])
	elif from_date:
		filters["attendance_date"] = (">=", getdate(from_date))
	elif to_date:
		filters["attendance_date"] = ("<=", getdate(to_date))
	if employee:
		filters["employee"] = employee

	return frappe.get_all(
		"Attendance",
		filters=filters,
		fields=[
			"name",
			"employee",
			"employee_name",
			"attendance_date",
			"status",
			"in_time",
			"out_time",
			"working_hours",
			"docstatus",
		],
		order_by="attendance_date desc, employee_name asc",
		limit_page_length=2000,
	)


@frappe.whitelist()
def get_attendance_summary(from_date=None, to_date=None, group_by="date", employee=None):
	"""Attendance counts and working hours per day or per employee, for the bar chart.

	Aggregated in SQL on purpose: get_attendance_records caps at 2000 rows, which
	would silently clip the oldest days of a wide range and draw wrong bars.
	"""
	if group_by not in ("date", "employee"):
		frappe.throw("group_by must be 'date' or 'employee'")

	from frappe.query_builder.functions import Count, Sum, Min, Max

	table = frappe.qb.DocType("Attendance")
	key_columns = [table.attendance_date] if group_by == "date" else [table.employee, table.employee_name]

	query = frappe.qb.from_(table).select(
		*key_columns,
		table.status,
		Count(table.name).as_("count"),
		Sum(table.working_hours).as_("hours"),
		Min(table.in_time).as_("in_time"),
		Max(table.out_time).as_("out_time"),
		Min(table.shift).as_("shift"),
	)
	query = query.where(table.docstatus < 2)
	if from_date:
		query = query.where(table.attendance_date >= getdate(from_date))
	if to_date:
		query = query.where(table.attendance_date <= getdate(to_date))
	if employee:
		query = query.where(table.employee == employee)

	for column in key_columns:
		query = query.groupby(column)
	query = query.groupby(table.status)
	query = query.orderby(table.attendance_date if group_by == "date" else table.employee_name)

	rows = query.run(as_dict=True)

	shift_types = frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"])
	shift_map = {}
	for st in shift_types:
		shift_map[st.name] = {
			"start_time": str(st.start_time) if st.start_time else None,
			"end_time": str(st.end_time) if st.end_time else None,
		}

	fallback_shift = None
	if employee:
		fallback_shift = frappe.db.get_value(
			"Shift Assignment",
			{"employee": employee, "status": "Active", "docstatus": 1},
			"shift_type",
			order_by="start_date desc",
		)

	buckets = {}
	order = []
	for row in rows:
		if group_by == "date":
			key = str(row.attendance_date)
			label = key
		else:
			key = row.employee
			label = row.employee_name or row.employee
		if key not in buckets:
			shift_name = row.shift or fallback_shift
			shift_info = shift_map.get(shift_name) if shift_name else None
			buckets[key] = {
				"key": key,
				"label": label,
				"total": 0,
				"hours": 0.0,
				"counts": {},
				"shift": shift_name,
				"shift_start": shift_info["start_time"] if shift_info else None,
				"shift_end": shift_info["end_time"] if shift_info else None,
				"in_time": str(row.in_time) if row.in_time else None,
				"out_time": str(row.out_time) if row.out_time else None,
			}
			order.append(key)
		bucket = buckets[key]
		bucket["counts"][row.status or "Unknown"] = bucket["counts"].get(row.status or "Unknown", 0) + row.count
		bucket["total"] += row.count
		bucket["hours"] = flt(bucket["hours"] + flt(row.hours), 2)

	statuses = sorted({r.status or "Unknown" for r in rows})
	return {
		"group_by": group_by,
		"statuses": statuses,
		"buckets": [buckets[k] for k in order],
	}
