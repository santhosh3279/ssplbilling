import frappe

SETTINGS = "SSPL WhatsApp Settings"


def execute():
	"""Carry the single linked session over as the shared row, so it keeps sending without a rescan."""
	old = dict(
		frappe.db.sql(
			"""select field, value from `tabSingles` where doctype = %s
			and field in ('session_name', 'session_id', 'status', 'phone', 'push_name')""",
			SETTINGS,
		)
	)
	if not old.get("session_name"):
		return

	settings = frappe.get_single(SETTINGS)
	if settings.sessions:
		return
	settings.append(
		"sessions",
		{
			"session_name": old["session_name"],
			"session_id": old.get("session_id") or "",
			"status": old.get("status") or "",
			"phone": old.get("phone") or "",
			"push_name": old.get("push_name") or "",
		},
	)
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)
