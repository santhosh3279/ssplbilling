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
