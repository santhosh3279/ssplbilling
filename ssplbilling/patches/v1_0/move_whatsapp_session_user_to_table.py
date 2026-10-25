import frappe

SETTINGS = "SSPL WhatsApp Settings"
SESSION = "SSPL WhatsApp Session"


def execute():
	"""Carry each session row's single user over to Users per Session, so nobody loses their session."""
	if not frappe.db.has_column(SESSION, "user"):
		return

	rows = frappe.db.sql(
		f"""select user, session_name from `tab{SESSION}`
		where parent = %s and parenttype = %s and ifnull(user, '') != '' order by idx""",
		(SETTINGS, SETTINGS),
		as_dict=True,
	)
	if not rows:
		return

	settings = frappe.get_single(SETTINGS)
	if settings.session_users:
		return
	for row in rows:
		settings.append("session_users", {"user": row.user, "session_name": row.session_name})
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_validate = True
	settings.save(ignore_permissions=True)
