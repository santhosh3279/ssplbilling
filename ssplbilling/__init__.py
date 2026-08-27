__version__ = "0.0.2"

# Monkeypatch frappe.app.handle_exception to automatically log unexpected errors to the Error Log DocType.
try:
	import frappe
	import frappe.app

	original_handle_exception = frappe.app.handle_exception

	def custom_handle_exception(e):
		try:
			# Do not log standard client-side errors / redirects (3xx, 401, 403, 404)
			status_code = getattr(e, "http_status_code", 500)
			if status_code not in (301, 302, 401, 403, 404):
				tb = frappe.get_traceback()
				message = tb or str(e)
				title = f"Web Request Error: {e.__class__.__name__}"
				frappe.log_error(message=message, title=title)
		except Exception:
			pass

		return original_handle_exception(e)

	frappe.app.handle_exception = custom_handle_exception
except Exception:
	pass
