import frappe


def execute():
	"""Give each SSPL WhatsApp Template the usage area it is already set for in SSPL WhatsApp
	Settings > Template per Usage Area. A template set for several areas, or for none, is left with
	no area, which any area may still use."""
	if not frappe.db.has_column("SSPL WhatsApp Template", "usage_area"):
		return
	areas = {}
	for row in frappe.get_all(
		"SSPL WhatsApp Template Usage",
		filters={"template_name": ["is", "set"]},
		fields=["template_name", "usage_area"],
	):
		areas.setdefault(row.template_name, set()).add(row.usage_area)
	for name, used_in in areas.items():
		if len(used_in) != 1 or not frappe.db.exists("SSPL WhatsApp Template", name):
			continue
		if not frappe.db.get_value("SSPL WhatsApp Template", name, "usage_area"):
			frappe.db.set_value(
				"SSPL WhatsApp Template", name, "usage_area", used_in.pop(), update_modified=False
			)
