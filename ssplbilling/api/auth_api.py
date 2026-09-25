import frappe


@frappe.whitelist()
def get_csrf_token():
	return frappe.sessions.get_csrf_token()


@frappe.whitelist()
def get_current_user_type():
	"""Return the authenticated user's type without requiring User list access."""
	return frappe.get_cached_value("User", frappe.session.user, "user_type")


@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def logout():
	"""Explicitly log out the current user, clear server sessions and cookies."""
	sid = None
	if hasattr(frappe, "request") and frappe.request and frappe.request.cookies:
		sid = frappe.request.cookies.get("sid")
	if not sid:
		sid = getattr(getattr(frappe, "session", None), "sid", None)

	user = getattr(getattr(frappe, "session", None), "user", None)

	if getattr(frappe.local, "login_manager", None):
		frappe.local.login_manager.logout(user=user)

	if sid and sid != "Guest":
		frappe.db.delete("Sessions", {"sid": sid})
		frappe.cache.hdel("session", sid)

	frappe.db.commit()
	return {"message": "Logged out"}


