"""Decide which Sales Invoices get an e-Invoice, and generate it in a background worker.

Rules (only while e-Invoicing and the GST API are enabled in GST Settings):
- Automatic Entries has an alternative company: only the mirror bills, i.e. invoices of
  that alternative company, get an e-Invoice.
- No alternative company: only invoices whose naming series is listed in E Invoice Series.

India Compliance would otherwise auto-generate an e-Invoice for every applicable invoice
submitted through the API, so before_submit switches that off and these rules decide instead.
"""

import frappe


def _e_invoice_enabled():
	from india_compliance.gst_india.utils import is_api_enabled

	settings = frappe.get_cached_doc("GST Settings")
	if not (settings.enable_e_invoice and is_api_enabled(settings)):
		return None
	return settings


def _series_listed(naming_series):
	if not naming_series:
		return False
	listed = frappe.get_all("E Invoice Series", filters={"enabled": 1}, pluck="series")
	return any(naming_series == s or naming_series.startswith(s) for s in listed)


def should_generate_e_invoice(doc):
	from ssplbilling.api.automatic_entries_api import get_automatic_entries

	alternative_company = get_automatic_entries().alternative_company
	if alternative_company:
		return doc.company == alternative_company
	return _series_listed(doc.naming_series)


def before_submit(doc, method=None):
	"""Doc event: take over e-Invoice generation from India Compliance's auto-generate."""
	if not _e_invoice_enabled():
		return
	# India Compliance skips its own auto e-Invoice (and auto e-Waybill) for invoices
	# flagged as submitted from its form; our on_submit decides instead.
	doc._submitted_from_ui = True
	doc.flags.sspl_generate_e_invoice = should_generate_e_invoice(doc)


def on_submit(doc, method=None):
	"""Doc event: queue the e-Invoice in a worker once the submit has committed."""
	if not doc.flags.get("sspl_generate_e_invoice"):
		return
	settings = _e_invoice_enabled()
	if not settings:
		return

	from india_compliance.gst_india.utils.e_invoice import validate_e_invoice_applicability

	# B2C, same-GSTIN, before the applicable date, etc. are skipped silently
	if not validate_e_invoice_applicability(doc, settings, throw=False):
		return

	frappe.enqueue(
		"ssplbilling.api.e_invoice_api.run_e_invoice",
		queue="short",
		timeout=240,
		enqueue_after_commit=True,
		job_id=f"sspl-e-invoice:{doc.name}",
		deduplicate=True,
		docname=doc.name,
	)


def run_e_invoice(docname):
	"""Worker: generate the e-Invoice and record any failure as a Mirror Invoice Error."""
	from india_compliance.gst_india.utils.e_invoice import generate_e_invoice

	from ssplbilling.api.mirror_error_log import log_mirror_error, resolve_mirror_errors

	company = frappe.db.get_value("Sales Invoice", docname, "company")
	try:
		generate_e_invoice(docname, throw=True)
	except Exception:
		frappe.db.rollback()
		log_mirror_error("e-Invoice", "Sales Invoice", docname, docname, company)
		frappe.db.commit()  # nosemgrep -- worker job; keep the error row
		return

	# GSP server errors are handled inside India Compliance without raising: the
	# invoice is left without an IRN, marked Failed or queued for Auto-Retry.
	irn, status = frappe.db.get_value("Sales Invoice", docname, ["irn", "einvoice_status"])
	if irn:
		resolve_mirror_errors("e-Invoice", "Sales Invoice", docname)
	else:
		try:
			raise frappe.ValidationError(f"e-Invoice not generated (status: {status or 'unknown'}); see Error Log")
		except frappe.ValidationError:
			log_mirror_error("e-Invoice", "Sales Invoice", docname, docname, company)
	frappe.db.commit()  # nosemgrep -- worker job
