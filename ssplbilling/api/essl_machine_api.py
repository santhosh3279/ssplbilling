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
def sync_essl_attendance(machine=None, from_date=None):
	"""Pull attendance logs straight off the eSSL devices over the ZK protocol (TCP 4370).

	Nothing is written to the database — the caller caches the logs client-side.
	One unreachable or misconfigured device never aborts the whole sync: its error
	is reported in its own row of the "machines" list and the rest keep going.
	"""
	from zk import ZK

	if from_date:
		from_date = frappe.utils.getdate(from_date)

	filters = {"name": machine} if machine else {}
	machines = frappe.get_all(
		ESSL_MACHINE_DOCTYPE,
		filters=filters,
		fields=["name", "serial_number", "ip_address", "comm_key", "store"],
		order_by="store asc, ip_address asc",
	)

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
			# comm_key is optional and free text — anything non-numeric means "no key"
			try:
				password = int(row.comm_key or 0)
			except (TypeError, ValueError):
				password = 0

			zk = ZK(row.ip_address, port=4370, timeout=10, password=password, ommit_ping=True)
			conn = zk.connect()
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
