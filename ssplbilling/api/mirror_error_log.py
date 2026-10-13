"""Record failures of mirror bills, mirror payments and e-Invoices as Mirror Invoice Error rows.

Call log_mirror_error from an except block after rolling back to the savepoint (or the whole
transaction), so the row is written in the surviving transaction and is not lost with the
failed work. A later success for the same document and stage resolves its open rows.
"""

import frappe


def log_mirror_error(stage, reference_doctype, reference_name, mirror_invoice=None, company=None):
	try:
		frappe.get_doc(
			{
				"doctype": "Mirror Invoice Error",
				"status": "Open",
				"stage": stage,
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"mirror_invoice": mirror_invoice,
				"company": company,
				"user": frappe.session.user,
				"error": _last_error_message(),
				"traceback": frappe.get_traceback(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		# The error log must never turn a handled failure into a new one.
		frappe.log_error(title="Mirror Invoice Error: could not record failure", message=frappe.get_traceback())


def resolve_mirror_errors(stage, reference_doctype, reference_name):
	frappe.db.set_value(
		"Mirror Invoice Error",
		{
			"status": "Open",
			"stage": stage,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		},
		"status",
		"Resolved",
	)


def _last_error_message():
	import sys

	exc = sys.exc_info()[1]
	message = str(exc) if exc else ""
	return frappe.utils.strip_html(message)[:1000] or (type(exc).__name__ if exc else "")
