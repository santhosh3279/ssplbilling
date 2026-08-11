import frappe

# The doctype name keeps the lowercase "e" and the trailing "Attendance" —
# it must match the DocType record exactly or get_all throws.
ESSL_MACHINE_DOCTYPE = "eSSL Machines Attendance"


@frappe.whitelist()
def get_essl_machines():
	"""Return every eSSL machine. No filters — searching is done client-side."""
	return frappe.get_all(
		ESSL_MACHINE_DOCTYPE,
		fields=[
			"name",
			"serial_number",
			"ip_address",
			"comm_key",
			"store",
			"modified",
		],
		order_by="store asc, ip_address asc",
	)


@frappe.whitelist()
def save_essl_machine(data):
	"""Create a machine record. ip_address is the record name (autoname), so it must
	be unique — a repeat IP is reported as such instead of surfacing a raw DB error."""
	import json

	if isinstance(data, str):
		data = json.loads(data)

	ip_address = (data.get("ip_address") or "").strip()
	if not ip_address:
		frappe.throw("IP Address is required")

	if frappe.db.exists(ESSL_MACHINE_DOCTYPE, ip_address):
		frappe.throw(f"A machine with IP {ip_address} already exists")

	doc = frappe.new_doc(ESSL_MACHINE_DOCTYPE)
	doc.ip_address = ip_address
	doc.serial_number = (data.get("serial_number") or "").strip()
	doc.comm_key = (data.get("comm_key") or "").strip()
	doc.store = (data.get("store") or "").strip()
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "ip_address": doc.ip_address, "store": doc.store}


def connect_machine(row):
	"""Open a ZK connection to one device. Caller is responsible for disconnect()."""
	from zk import ZK

	if not row.ip_address:
		frappe.throw("No IP address configured")

	# comm_key is optional and free text — anything non-numeric means "no key"
	try:
		password = int(row.comm_key or 0)
	except (TypeError, ValueError):
		password = 0

	# ommit_ping: the devices do not answer ICMP even when TCP 4370 is open
	zk = ZK(row.ip_address, port=4370, timeout=10, password=password, ommit_ping=True)
	return zk.connect()


def get_machine_rows(machine=None):
	"""Machine records, one or all. get_all so the System-Manager-only read perm on
	the doctype does not blank the list for billers reaching this via the hrms tile."""
	return frappe.get_all(
		ESSL_MACHINE_DOCTYPE,
		filters={"name": machine} if machine else {},
		fields=["name", "serial_number", "ip_address", "comm_key", "store", "last_sync"],
		order_by="store asc, ip_address asc",
	)


@frappe.whitelist()
def sync_essl_attendance(machine=None, from_date=None):
	"""Pull attendance logs straight off the eSSL devices over the ZK protocol (TCP 4370).

	Nothing is written to the database — the caller caches the logs client-side.
	One unreachable or misconfigured device never aborts the whole sync: its error
	is reported in its own row of the "machines" list and the rest keep going.
	"""
	if from_date:
		from_date = frappe.utils.getdate(from_date)

	machines = get_machine_rows(machine)

	logs = []
	results = []

	for row in machines:
		summary = {
			"machine": row.name,
			"ip_address": row.ip_address,
			"store": row.store,
			"logs": 0,
			"error": None,
		}

		if not row.ip_address:
			summary["error"] = "No IP address configured"
			results.append(summary)
			continue

		conn = None
		try:
			conn = connect_machine(row)
			summary["device_serial"] = conn.get_serialnumber()

			for att in conn.get_attendance() or []:
				if from_date and att.timestamp.date() < from_date:
					continue
				logs.append(
					{
						"machine": row.name,
						"store": row.store,
						"user_id": str(att.user_id),
						# str() keeps the wire format at "YYYY-MM-DD HH:MM:SS"
						"timestamp": str(att.timestamp),
						"status": att.status,
						"punch": att.punch,
					}
				)
				summary["logs"] += 1
		except Exception as e:
			summary["error"] = str(e) or e.__class__.__name__
		finally:
			if conn:
				try:
					conn.disconnect()
				except Exception:
					pass

		results.append(summary)

	logs.sort(key=lambda x: x["timestamp"], reverse=True)

	return {
		"synced_at": frappe.utils.now(),
		"from_date": str(from_date) if from_date else None,
		"total": len(logs),
		"machines": results,
		"logs": logs,
	}
