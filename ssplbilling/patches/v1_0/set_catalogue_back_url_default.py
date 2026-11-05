import frappe


def execute():
	"""The catalogue Back button used to be hardcoded to this link; keep it for existing sites.
	Runs once, so a link cleared later on purpose stays cleared."""
	if not frappe.db.get_single_value("SSPL Billing Settings", "catalogue_back_url"):
		frappe.db.set_single_value("SSPL Billing Settings", "catalogue_back_url", "https://www.chettiyarkada.in")
