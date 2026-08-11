"""User enrollment across eSSL devices: machine to machine, and ERP to machine.

Fingerprint templates travel with the user. Face templates do NOT — pyzk has no
face read/write commands, so a face enrolled on one device cannot be copied and
has to be re-enrolled on each device by hand.
"""

import json

import frappe
from frappe.utils import now_datetime

from ssplbilling.api.essl_machine_api import connect_machine, get_machine_rows

DEVICE_USER_DOCTYPE = "eSSL Device User"
MAPPING_DOCTYPE = "eSSL Employee Mapping"

# The 73 byte user packet holds a 24 byte name field; anything longer is clipped
# by the device, so it is truncated deliberately and reported back.
DEVICE_NAME_MAX = 24


def _machine_row(name):
	rows = get_machine_rows(name)
	if not rows:
		frappe.throw(f"Machine {name} not found")
	return rows[0]


def _user_payload(user, template_count=0):
	return {
		"uid": user.uid,
		"user_id": str(user.user_id),
		"name": user.name or "",
		"privilege": "Admin" if int(user.privilege or 0) else "User",
		"password": str(user.password or ""),
		"group_id": str(user.group_id or ""),
		"card": int(user.card or 0),
		"templates": template_count,
	}


def _read_machine(conn):
	"""Users plus their fingerprint templates, keyed by the device-internal uid."""
	users = conn.get_users() or []
	fingers = {}
	for finger in conn.get_templates() or []:
		fingers.setdefault(finger.uid, []).append(finger)
	return users, fingers


@frappe.whitelist()
def get_machine_users(machine):
	"""Live user list of one device, with fingerprint counts and mapping status."""
	row = _machine_row(machine)
	mapped = {
		str(m.machine_user_id): m.employee
		for m in frappe.get_all(MAPPING_DOCTYPE, fields=["machine_user_id", "employee"])
	}
	known = {d.name for d in frappe.get_all(DEVICE_USER_DOCTYPE, fields=["name"])}

	conn = None
	try:
		conn = connect_machine(row)
		users, fingers = _read_machine(conn)
		payload = []
		for user in users:
			item = _user_payload(user, len(fingers.get(user.uid, [])))
			item["employee"] = mapped.get(item["user_id"])
			item["in_erp"] = item["user_id"] in known
			payload.append(item)
	finally:
		if conn:
			try:
				conn.disconnect()
			except Exception:
				pass

	payload.sort(key=lambda u: (not u["user_id"].isdigit(), int(u["user_id"]) if u["user_id"].isdigit() else 0))
	return {"machine": row.name, "store": row.store, "users": payload}


def _next_uid(existing_uids):
	return (max(existing_uids) + 1) if existing_uids else 1


def _write_user(conn, uid, user_id, name, privilege, password, group_id, card, fingers):
	"""Create/update one user on the connected device, templates included.

	set_user packs group_id/password as strings and card as int on the 73 byte
	path, so everything is normalised here rather than trusting the source device.
	"""
	from zk.user import User

	conn.set_user(
		uid=uid,
		name=(name or "")[:DEVICE_NAME_MAX],
		privilege=int(privilege or 0),
		password=str(password or ""),
		group_id=str(group_id or ""),
		user_id=str(user_id),
		card=int(card or 0),
	)

	if not fingers:
		return 0

	target_user = User(
		uid=uid,
		name=(name or "")[:DEVICE_NAME_MAX],
		privilege=int(privilege or 0),
		password=str(password or ""),
		group_id=str(group_id or ""),
		user_id=str(user_id),
		card=int(card or 0),
	)
	conn.save_user_template(target_user, fingers)
	return len(fingers)


@frappe.whitelist()
def copy_users(source, target, user_ids=None):
	"""Copy users (and their fingerprints) from one device to another.

	Matching is by user_id — the code printed on the punch log — never by uid,
	which is a per-device index and differs between machines for the same person.
	"""
	if isinstance(user_ids, str):
		user_ids = json.loads(user_ids)
	wanted = {str(u) for u in (user_ids or [])}

	if source == target:
		frappe.throw("Source and target machine must be different")

	source_row = _machine_row(source)
	target_row = _machine_row(target)

	src_conn = None
	try:
		src_conn = connect_machine(source_row)
		users, fingers = _read_machine(src_conn)
	finally:
		if src_conn:
			try:
				src_conn.disconnect()
			except Exception:
				pass

	selected = [u for u in users if not wanted or str(u.user_id) in wanted]
	if not selected:
		frappe.throw("No matching users found on the source machine")

	results = []
	tgt_conn = None
	try:
		tgt_conn = connect_machine(target_row)
		existing = tgt_conn.get_users() or []
		uid_by_user_id = {str(u.user_id): u.uid for u in existing}
		used_uids = {u.uid for u in existing}

		# Writes are done with the device disabled so a punch mid-transfer cannot
		# corrupt it. enable_device lives in finally — a device left disabled is
		# unusable at the counter.
		tgt_conn.disable_device()

		for user in selected:
			row = {"user_id": str(user.user_id), "name": user.name or "", "templates": 0, "error": None}
			try:
				uid = uid_by_user_id.get(str(user.user_id))
				if uid is None:
					uid = _next_uid(used_uids)
					used_uids.add(uid)

				# Fresh Finger objects pointing at the target uid — mutating the
				# source ones would corrupt a copy to a second target.
				from zk.finger import Finger

				copied = [
					Finger(uid=uid, fid=f.fid, valid=f.valid, template=f.template)
					for f in fingers.get(user.uid, [])
				]
				row["templates"] = _write_user(
					tgt_conn,
					uid,
					user.user_id,
					user.name,
					user.privilege,
					user.password,
					user.group_id,
					user.card,
					copied,
				)
				if user.name and len(user.name) > DEVICE_NAME_MAX:
					row["error"] = f"Name truncated to {DEVICE_NAME_MAX} characters on the device"
			except Exception as e:
				row["error"] = str(e) or e.__class__.__name__
			results.append(row)

		tgt_conn.refresh_data()
	finally:
		if tgt_conn:
			try:
				tgt_conn.enable_device()
			except Exception:
				pass
			try:
				tgt_conn.disconnect()
			except Exception:
				pass

	return {
		"source": source_row.name,
		"target": target_row.name,
		"copied": sum(1 for r in results if not r["error"]),
		"failed": sum(1 for r in results if r["error"]),
		"users": results,
	}


def _push_users_to_machine(machine, employee_codes=None):
	"""Write eSSL Device User records (fingerprints included) onto a device.

	Internal helper for create_employee_and_enroll — not a whitelisted endpoint."""
	if isinstance(employee_codes, str):
		employee_codes = json.loads(employee_codes)

	filters = {"name": ("in", employee_codes)} if employee_codes else {}
	names = [d.name for d in frappe.get_all(DEVICE_USER_DOCTYPE, filters=filters, fields=["name"])]
	if not names:
		frappe.throw("No device users selected")

	row = _machine_row(machine)
	results = []

	conn = None
	try:
		conn = connect_machine(row)
		existing = conn.get_users() or []
		uid_by_user_id = {str(u.user_id): u.uid for u in existing}
		used_uids = {u.uid for u in existing}
		conn.disable_device()

		from zk.finger import Finger

		for name in names:
			doc = frappe.get_doc(DEVICE_USER_DOCTYPE, name)
			result = {"employee_code": doc.name, "device_name": doc.device_name, "templates": 0, "error": None}
			try:
				uid = uid_by_user_id.get(doc.name)
				if uid is None:
					uid = _next_uid(used_uids)
					used_uids.add(uid)

				fingers = []
				for tpl in doc.fingerprints or []:
					template = bytes.fromhex(tpl.template_hex or "")
					if tpl.size and len(template) != tpl.size:
						raise ValueError(f"Template {tpl.fid} is corrupt ({len(template)} bytes, expected {tpl.size})")
					fingers.append(Finger(uid=uid, fid=tpl.fid, valid=tpl.valid, template=template))

				result["templates"] = _write_user(
					conn,
					uid,
					doc.name,
					doc.device_name or doc.employee_name or doc.name,
					1 if doc.privilege == "Admin" else 0,
					doc.password,
					doc.group_id,
					doc.card,
					fingers,
				)
				frappe.db.set_value(DEVICE_USER_DOCTYPE, doc.name, "last_pushed", now_datetime(), update_modified=False)
			except Exception as e:
				result["error"] = str(e) or e.__class__.__name__
			results.append(result)

		conn.refresh_data()
	finally:
		if conn:
			try:
				conn.enable_device()
			except Exception:
				pass
			try:
				conn.disconnect()
			except Exception:
				pass

	frappe.db.commit()
	return {
		"machine": row.name,
		"pushed": sum(1 for r in results if not r["error"]),
		"failed": sum(1 for r in results if r["error"]),
		"users": results,
	}


@frappe.whitelist()
def next_employee_code():
	"""Lowest free numeric code across every device and the ERP registry.

	Every machine must answer: a code that only exists on an unreachable device
	would otherwise be handed out twice and two people would share a punch id.
	"""
	codes = set()
	unreachable = []

	for row in get_machine_rows():
		conn = None
		try:
			conn = connect_machine(row)
			for user in conn.get_users() or []:
				codes.add(str(user.user_id))
		except Exception as e:
			unreachable.append({"machine": row.name, "error": str(e) or e.__class__.__name__})
		finally:
			if conn:
				try:
					conn.disconnect()
				except Exception:
					pass

	for doc in frappe.get_all(DEVICE_USER_DOCTYPE, fields=["name"]):
		codes.add(str(doc.name))
	for row in frappe.get_all(MAPPING_DOCTYPE, fields=["machine_user_id"]):
		codes.add(str(row.machine_user_id))

	numeric = [int(c) for c in codes if c.isdigit()]
	return {
		"next_code": str(max(numeric) + 1) if numeric else "1",
		"used_codes": sorted(codes),
		"unreachable": unreachable,
	}


@frappe.whitelist()
def create_employee_and_enroll(data):
	"""Create an Employee, give it a device code, and push it to the chosen machines.

	The attendance mapping is created in the same call, so punches from the new code
	turn into attendance straight away.
	"""
	if isinstance(data, str):
		data = json.loads(data)

	code = str(data.get("employee_code") or "").strip()
	if not code:
		frappe.throw("Employee code is required")
	if frappe.db.exists(DEVICE_USER_DOCTYPE, code):
		frappe.throw(f"Device code {code} is already in use")

	employee = data.get("employee")
	if employee:
		emp = frappe.get_doc("Employee", employee)
	else:
		from ssplbilling.api.employee_api import create_employee

		created = create_employee(
			{
				"first_name": data.get("first_name"),
				"last_name": data.get("last_name"),
				"gender": data.get("gender"),
				"date_of_birth": data.get("date_of_birth"),
				"date_of_joining": data.get("date_of_joining"),
				"mobile": data.get("mobile"),
				"email": data.get("email"),
			}
		)
		emp = frappe.get_doc("Employee", created["name"])

	device_name = (data.get("device_name") or emp.employee_name or "")[:DEVICE_NAME_MAX]

	doc = frappe.new_doc(DEVICE_USER_DOCTYPE)
	doc.employee_code = code
	doc.employee = emp.name
	doc.device_name = device_name
	doc.privilege = data.get("privilege") or "User"
	doc.password = str(data.get("password") or "")
	doc.card = str(data.get("card") or "0")
	doc.insert(ignore_permissions=True)

	# Same code the attendance sync reads punches under
	if not frappe.db.exists(MAPPING_DOCTYPE, {"machine_user_id": code, "machine": ("in", ["", None])}):
		mapping = frappe.new_doc(MAPPING_DOCTYPE)
		mapping.machine_user_id = code
		mapping.employee = emp.name
		mapping.enabled = 1
		mapping.insert(ignore_permissions=True)

	frappe.db.commit()

	machines = data.get("machines") or []
	pushes = [_push_users_to_machine(m, [code]) for m in machines]

	return {
		"employee": emp.name,
		"employee_name": emp.employee_name,
		"employee_code": code,
		"device_name": device_name,
		"name_truncated": bool(emp.employee_name and len(emp.employee_name) > DEVICE_NAME_MAX),
		"pushes": pushes,
	}


@frappe.whitelist()
def delete_machine_user(machine, user_id):
	"""Remove one user (and their templates) from a device. The ERP copy stays."""
	row = _machine_row(machine)
	conn = None
	try:
		conn = connect_machine(row)
		users = conn.get_users() or []
		match = [u for u in users if str(u.user_id) == str(user_id)]
		if not match:
			frappe.throw(f"User {user_id} is not on {row.name}")
		conn.disable_device()
		conn.delete_user(uid=match[0].uid)
		conn.refresh_data()
	finally:
		if conn:
			try:
				conn.enable_device()
			except Exception:
				pass
			try:
				conn.disconnect()
			except Exception:
				pass

	return {"machine": row.name, "deleted": str(user_id)}


@frappe.whitelist()
def update_machine_user(machine, user_id, name=None, privilege=None, password=None, card=None):
	"""Rewrite the details of one user already on a device.

	The uid and user_id are kept as they are — the templates are stored against the
	uid, so changing it would strand the fingerprints already enrolled on the device.
	"""
	row = _machine_row(machine)
	conn = None
	try:
		conn = connect_machine(row)
		users = conn.get_users() or []
		match = [u for u in users if str(u.user_id) == str(user_id)]
		if not match:
			frappe.throw(f"User {user_id} is not on {row.name}")
		current = match[0]

		new_name = current.name if name is None else name
		new_privilege = (
			int(current.privilege or 0)
			if privilege is None
			else (1 if str(privilege).lower() in ("admin", "1", "true") else 0)
		)
		new_password = current.password if password is None else password
		new_card = current.card if card is None else card

		conn.disable_device()
		_write_user(
			conn,
			current.uid,
			current.user_id,
			new_name,
			new_privilege,
			new_password,
			current.group_id,
			new_card,
			None,
		)
		conn.refresh_data()
	finally:
		if conn:
			try:
				conn.enable_device()
			except Exception:
				pass
			try:
				conn.disconnect()
			except Exception:
				pass

	truncated = bool(new_name and len(str(new_name)) > DEVICE_NAME_MAX)
	return {
		"machine": row.name,
		"user_id": str(user_id),
		"name": str(new_name or "")[:DEVICE_NAME_MAX],
		"privilege": "Admin" if new_privilege else "User",
		"name_truncated": truncated,
	}
