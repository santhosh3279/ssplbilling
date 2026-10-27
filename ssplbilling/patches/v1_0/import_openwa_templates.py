"""Copy the OpenWA templates named in SSPL WhatsApp Settings into SSPL WhatsApp Template records.

Template per Usage Area used to name a template on the OpenWA gateway, read from the sending
user's session at send time, so one name could carry different text per session. The shared
session's text (else the first session's) keeps the name; a session whose text differs gets
"<name> - <session>" plus a user row for each of its users, so every user keeps the message they
sent before. Names that could not be fetched are blanked, since the field is now a Link.
"""

import frappe

SETTINGS = "SSPL WhatsApp Settings"
USAGE = "SSPL WhatsApp Template Usage"
TEMPLATE = "SSPL WhatsApp Template"


def execute():
	if not frappe.db.exists("DocType", TEMPLATE):
		return
	try:
		migrate()
	except Exception:
		# The gateway may be down or the settings odd; a failed import must not fail the migrate
		frappe.db.rollback()
		frappe.log_error(title="OpenWA templates not imported", message=frappe.get_traceback())
		blank_dangling()


def gateway_texts(settings):
	"""{session name: {template name: text}}, shared session first, as the old render joined it."""
	from ssplbilling.api.whatsapp_api import _call

	assigned = {r.session_name for r in settings.session_users}
	sessions = sorted((r for r in settings.sessions if r.session_id), key=lambda r: r.session_name in assigned)
	texts = {}
	for row in sessions:
		try:
			found = _call(settings, "GET", f"/sessions/{row.session_id}/templates") or []
		except Exception:
			frappe.log_error(title="OpenWA templates could not be listed", message=frappe.get_traceback())
			continue
		texts[row.session_name] = {
			(t.get("name") or "").strip(): "\n\n".join(
				p for p in (t.get("header"), t.get("body"), t.get("footer")) if p
			)
			for t in found
		}
	return texts


def create_template(name, text):
	if text and not frappe.db.exists(TEMPLATE, name):
		frappe.get_doc({"doctype": TEMPLATE, "template_name": name, "message": text}).insert(
			ignore_permissions=True
		)


def migrate():
	settings = frappe.get_single(SETTINGS)
	usages = settings.get("template_usages") or []
	names = {r.template_name for r in usages if r.template_name}
	if not names:
		return

	texts = gateway_texts(settings)
	users_by_session = {}
	for su in settings.session_users:
		users_by_session.setdefault(su.session_name, []).append(su.user)
	own_rows = {(r.usage_area, r.user) for r in usages if r.user}
	next_idx = max((r.idx for r in usages), default=0) + 1

	for name in names:
		variants = [(session, found[name]) for session, found in texts.items() if found.get(name)]
		if not variants:
			continue
		base_text = variants[0][1]
		create_template(name, base_text)

		for session, text in variants[1:]:
			if text == base_text:
				continue
			variant = f"{name} - {session}"
			create_template(variant, text)
			users = set(users_by_session.get(session, []))
			for row in usages:
				if row.template_name != name:
					continue
				if row.user:
					# A user's own row now names the text of that user's session
					if row.user in users:
						frappe.db.set_value(USAGE, row.name, "template_name", variant, update_modified=False)
					continue
				for user in sorted(users):
					if (row.usage_area, user) in own_rows:
						continue
					frappe.get_doc(
						{
							"doctype": USAGE,
							"parent": SETTINGS,
							"parenttype": SETTINGS,
							"parentfield": "template_usages",
							"idx": next_idx,
							"usage_area": row.usage_area,
							"user": user,
							"template_name": variant,
							"placeholders": row.placeholders,
						}
					).db_insert()
					own_rows.add((row.usage_area, user))
					next_idx += 1

	blank_dangling()


def blank_dangling():
	"""Clear names with no SSPL WhatsApp Template, or the settings form could never be saved again."""
	for row in frappe.get_all(USAGE, filters={"parent": SETTINGS}, fields=["name", "template_name"]):
		if row.template_name and not frappe.db.exists(TEMPLATE, row.template_name):
			frappe.db.set_value(USAGE, row.name, "template_name", "", update_modified=False)
