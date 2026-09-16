import frappe


@frappe.whitelist()
def get_csrf_token():
	return frappe.sessions.get_csrf_token()


@frappe.whitelist()
def get_current_user_type():
	"""Return the authenticated user's type without requiring User list access."""
	return frappe.get_cached_value("User", frappe.session.user, "user_type")
