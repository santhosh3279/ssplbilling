# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

"""Mail a bill's PDF to its party from the print modal.

The modal only offers the button when an outgoing Email Account is configured, so a
site without mail never shows an action that can only fail.
"""

import base64

import frappe
from frappe.utils import validate_email_address

from ssplbilling.api.print_preview_api import (
	_party_contact,
	build_preview_filename,
	get_party_link,
	get_party_name,
	preview_print_template_pdf,
)
from ssplbilling.ssplbilling.doctype.sspl_email_settings.sspl_email_settings import (
	AREA_BILL_SENDING,
	get_area_template,
)


def get_outgoing_account():
	"""The default outgoing Email Account, else any enabled one, or None."""
	for filters in ({"enable_outgoing": 1, "default_outgoing": 1}, {"enable_outgoing": 1}):
		name = frappe.db.get_value("Email Account", filters, "name")
		if name:
			return frappe.get_cached_doc("Email Account", name)
	return None


@frappe.whitelist()
def get_email_state():
	"""Whether bills can be mailed from this site, for showing the Send by Mail button."""
	return {"ready": bool(get_outgoing_account())}


def get_party_email(party_doctype, party):
	"""The party's email: its own email_id, else its Contact's."""
	if frappe.get_meta(party_doctype).has_field("email_id"):
		email = frappe.db.get_value(party_doctype, party, "email_id")
		if email:
			return email
	contact_name = _party_contact(party_doctype, party)
	if contact_name:
		return frappe.db.get_value("Contact", contact_name, "email_id") or ""
	return ""


def save_party_email(party_doctype, party, email):
	"""Store email as the primary email of the party's Contact. A party without a Contact gets one."""
	contact_name = _party_contact(party_doctype, party)
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
	else:
		name_field = "customer_name" if party_doctype == "Customer" else "supplier_name"
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": frappe.db.get_value(party_doctype, party, name_field) or party,
				"links": [{"link_doctype": party_doctype, "link_name": party}],
			}
		)

	for row in contact.email_ids:
		row.is_primary = 0
	row = next((r for r in contact.email_ids if r.email_id == email), None)
	if row:
		row.is_primary = 1
	else:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	contact.save(ignore_permissions=True)


def get_email_content(usage_area, doctype, document_name, sender=None):
	"""Subject and message for mailing a document from usage_area.

	Rendered from the Email Template set for the area in SSPL Email Settings, with the
	document's fields at top level ({{ customer_name }}) and as doc ({{ doc.company }}).
	With no template set, or one that fails to render, the built-in message is used.
	"""
	template_name = get_area_template(usage_area)
	if template_name:
		try:
			doc = frappe.get_doc(doctype, document_name)
			args = {**doc.as_dict(), "doc": doc}
			return frappe.get_doc("Email Template", template_name).get_formatted_email(args, sender)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Email Template {template_name} failed")

	party = get_party_name(doctype, document_name)
	company = ""
	if frappe.get_meta(doctype).has_field("company"):
		company = frappe.db.get_value(doctype, document_name, "company")
	greeting = f"Dear {frappe.utils.escape_html(party)}," if party else "Hello,"
	signature = f"<br><br>Regards,<br>{frappe.utils.escape_html(company)}" if company else ""
	return {
		"subject": f"{doctype} {document_name}",
		"message": f"{greeting}<br><br>Please find attached {doctype} {document_name}.{signature}",
	}


def _check_document(doctype, document_name):
	if not doctype or not document_name or not frappe.db.exists(doctype, document_name):
		frappe.throw("Document not found")
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)


@frappe.whitelist()
def get_email_recipient(doctype, document_name):
	"""Party name and email for a bill; an empty email makes the modal ask for one."""
	_check_document(doctype, document_name)
	party_doctype, party = get_party_link(doctype, document_name)
	return {
		"party": get_party_name(doctype, document_name) or party or "",
		"email": get_party_email(party_doctype, party) if party else "",
	}


@frappe.whitelist(methods=["POST"])
def send_document_email(doctype, document_name, print_template, email):
	"""Render the bill with print_template and mail it to email right away.

	Sent with now=True instead of through the Email Queue, so an SMTP failure reaches the
	operator in the modal instead of sitting unnoticed in the queue. When the party had no
	email on file, the address is saved to its Contact so the next bill is prefilled.
	"""
	_check_document(doctype, document_name)
	email = validate_email_address((email or "").strip(), throw=True)

	account = get_outgoing_account()
	if not account:
		frappe.throw("No outgoing Email Account is configured")

	b64 = preview_print_template_pdf(print_template, document_name)
	if not b64:
		frappe.throw(f'"{print_template}" has no PDF output — pick a PDF template')

	content = get_email_content(AREA_BILL_SENDING, doctype, document_name, account.email_id)

	frappe.sendmail(
		recipients=[email],
		sender=account.email_id,
		subject=content["subject"],
		message=content["message"],
		attachments=[
			{
				"fname": build_preview_filename(doctype, document_name, print_template),
				"fcontent": base64.b64decode(b64),
			}
		],
		reference_doctype=doctype,
		reference_name=document_name,
		now=True,
	)

	# Only fills a gap: an address typed over an existing one is used for this bill alone
	saved = False
	party_doctype, party_link = get_party_link(doctype, document_name)
	if party_link and not get_party_email(party_doctype, party_link):
		if frappe.has_permission(party_doctype, "write", doc=party_link):
			save_party_email(party_doctype, party_link, email)
			saved = True
	return {"email": email, "saved": saved}
