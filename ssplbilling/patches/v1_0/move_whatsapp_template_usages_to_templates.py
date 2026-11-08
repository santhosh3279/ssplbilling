import frappe


def execute():
	"""Move SSPL WhatsApp Settings > Template per Usage Area onto the templates themselves: a row with
	no user makes its template the area's All Users one, a row with a user lists that user on it.
	The old rows are left in place."""
	if not frappe.db.table_exists("SSPL WhatsApp Template Usage") or not frappe.db.has_column(
		"SSPL WhatsApp Template", "all_users"
	):
		return
	frappe.reload_doc("ssplbilling", "doctype", "sspl_whatsapp_template_user")
	rows = frappe.get_all(
		"SSPL WhatsApp Template Usage",
		filters={"template_name": ["is", "set"], "parenttype": "SSPL WhatsApp Settings"},
		fields=["template_name", "usage_area", "user"],
		order_by="idx asc",
	)
	by_template = {}
	for row in rows:
		by_template.setdefault(row.template_name, []).append(row)

	for name, usages in by_template.items():
		if not frappe.db.exists("SSPL WhatsApp Template", name):
			continue
		doc = frappe.get_doc("SSPL WhatsApp Template", name)
		doc.usage_area = doc.usage_area or usages[0].usage_area
		skipped = [r for r in usages if r.usage_area != doc.usage_area]
		usages = [r for r in usages if r.usage_area == doc.usage_area]
		listed = {r.user for r in doc.users}
		if any(not r.user for r in usages):
			doc.all_users = 1
		else:
			for r in usages:
				if r.user not in listed:
					doc.append("users", {"user": r.user})
					listed.add(r.user)
		try:
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				title="WhatsApp template usage not moved", message=f"{name}\n{frappe.get_traceback()}"
			)
			continue
		if skipped:
			frappe.log_error(
				title="WhatsApp template usage not moved",
				message="{} is for {}, so its rows for {} were not moved; copy the template for those".format(
					name, doc.usage_area, ", ".join(sorted({r.usage_area for r in skipped}))
				),
			)
