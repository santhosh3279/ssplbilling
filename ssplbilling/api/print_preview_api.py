# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

"""Preview wrapper around Print Template.preview_pdf.

An A5 Portrait Custom PDF is rendered sideways on purpose: the printer server
lays the A5 page rotated 90° counter-clockwise onto the top half of an A4 sheet
so it can be printed on A4 stock. That is right for the printer and unreadable
on screen, so the preview copy carries a 90° clockwise page rotation to bring it
back upright. Only the preview is touched; the bytes sent to CUPS are untouched.
"""

import base64
import io
import os
import re
import zipfile
from urllib.parse import quote

import frappe


def needs_clockwise_preview(doc):
	return (
		doc.format_type == "Custom PDF"
		and (doc.custom_pdf_page_size or "A4") == "A5"
		and (doc.custom_pdf_orientation or "Portrait") == "Portrait"
	)


def rotate_pdf_clockwise(pdf_bytes, degrees=90):
	from pypdf import PdfReader, PdfWriter

	reader = PdfReader(io.BytesIO(pdf_bytes))
	writer = PdfWriter()
	for page in reader.pages:
		page.rotate(degrees)
		writer.add_page(page)

	stream = io.BytesIO()
	writer.write(stream)
	return stream.getvalue()


@frappe.whitelist()
def preview_print_template_pdf(print_template, document_name=None):
	"""Base64 PDF for the print preview, upright for A5 Portrait templates."""
	doc = frappe.get_doc("Print Template", print_template)
	doc.check_permission("read")

	b64 = doc.preview_pdf(document_name)
	if not b64 or not needs_clockwise_preview(doc):
		return b64

	try:
		return base64.b64encode(rotate_pdf_clockwise(base64.b64decode(b64))).decode()
	except Exception:
		# A preview that cannot be rotated is still a usable preview.
		frappe.log_error(frappe.get_traceback(), "Offer/A5 preview rotation failed")
		return b64


@frappe.whitelist()
def preview_print_template_file(print_template, document_name=None, doctype=None):
	"""Serve the preview PDF as a file named "<party> - <bill number>.pdf".

	The modal used to open a blob URL, which downloads under a random UUID. This
	returns the same bytes as a real response instead, so Content-Disposition
	carries a name the operator can find on disk.
	"""
	try:
		pdf = base64.b64decode(preview_print_template_pdf(print_template, document_name))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Print preview failed")
		# Same fallback the modal used to do client-side: Frappe's own printview.
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = (
			"/printview?doctype={}&name={}&format={}&trigger_print=0".format(
				quote(doctype or ""), quote(document_name or ""), quote(print_template or "")
			)
		)
		return

	frappe.local.response.filename = build_preview_filename(
		doctype or frappe.db.get_value("Print Template", print_template, "document_type"),
		document_name,
		print_template,
	)
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


# Party field per doctype, most specific first: the printed name beats the link.
PARTY_FIELDS = (
	"customer_name",
	"supplier_name",
	"party_name",
	"customer",
	"supplier",
	"party",
	"title",
)


def get_party_name(doctype, document_name):
	"""The party a document is billed to, or "" when the doctype has no party."""
	if not doctype or not document_name or not frappe.db.exists("DocType", doctype):
		return ""

	meta = frappe.get_meta(doctype)
	for fieldname in PARTY_FIELDS:
		if not meta.has_field(fieldname):
			continue
		value = frappe.db.get_value(doctype, document_name, fieldname)
		if value and value != document_name:
			return str(value)
	return ""


def build_preview_filename(doctype, document_name, print_template):
	"""<party> - <bill number>.pdf, dropping either half when it is unknown."""
	bill_number = document_name or print_template
	parts = [p for p in (get_party_name(doctype, document_name), bill_number) if p]
	# Long customer names are trimmed so the header stays a sane length.
	return "{}.pdf".format(scrub_filename(" - ".join(parts))[:120])


def scrub_filename(name):
	"""Keep the document name recognisable but safe in a Content-Disposition header."""
	cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', "-", str(name)).strip(" .")
	return cleaned or "preview"


# Party link field per doctype, so the WhatsApp lookup knows whose number to fetch.
PARTY_LINK_FIELDS = (
	("customer", "Customer"),
	("supplier", "Supplier"),
)

# Bare numbers in this database are Indian 10-digit mobiles with no country code.
DEFAULT_COUNTRY_CODE = "91"


def get_party_link(doctype, document_name):
	"""(party doctype, party) a document is billed to, or (None, None)."""
	meta = frappe.get_meta(doctype)
	for fieldname, party_doctype in PARTY_LINK_FIELDS:
		if not meta.has_field(fieldname):
			continue
		value = frappe.db.get_value(doctype, document_name, fieldname)
		if value:
			return party_doctype, value

	# Payment Entry / Journal Entry style generic party
	if meta.has_field("party") and meta.has_field("party_type"):
		party_type, party = frappe.db.get_value(doctype, document_name, ["party_type", "party"])
		if party and party_type:
			return party_type, party

	return None, None


def get_party_whatsapp(party_doctype, party):
	"""WhatsApp number for a party: the Contact's secondary phone, else mobile_no.

	Customer/Supplier creation in this app stores the WhatsApp number on the linked
	Contact as a Contact Phone row with is_primary_mobile_no = 0 (see CustomerCreator
	and customersearch_api), which is why the primary mobile is only the fallback.
	"""
	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": party_doctype, "link_name": party, "parenttype": "Contact"},
		"parent",
	)
	if contact_name:
		phone = frappe.db.get_value(
			"Contact Phone", {"parent": contact_name, "is_primary_mobile_no": 0}, "phone"
		)
		if phone:
			return phone

	if frappe.get_meta(party_doctype).has_field("mobile_no"):
		return frappe.db.get_value(party_doctype, party, "mobile_no") or ""

	return ""


def normalize_whatsapp_number(phone):
	"""Digits only, with a country code — the form wa.me / web.whatsapp.com expect."""
	digits = re.sub(r"\D", "", str(phone or ""))
	if not digits:
		return ""
	if digits.startswith("00"):
		digits = digits[2:]
	if len(digits) == 11 and digits.startswith("0"):
		digits = digits[1:]
	if len(digits) == 10:
		digits = DEFAULT_COUNTRY_CODE + digits
	return digits


@frappe.whitelist()
def get_whatsapp_recipient(doctype, document_name):
	"""Party name and WhatsApp number for a bill, for the share button in the print modal.

	An empty phone is a valid answer: the modal then opens WhatsApp with no chat
	preselected so the operator searches the contact themselves.
	"""
	if not doctype or not document_name or not frappe.db.exists(doctype, document_name):
		frappe.throw("Document not found")

	frappe.has_permission(doctype, "read", doc=document_name, throw=True)

	party_doctype, party = get_party_link(doctype, document_name)
	phone = normalize_whatsapp_number(get_party_whatsapp(party_doctype, party)) if party else ""

	meta = frappe.get_meta(doctype)
	amount = None
	for fieldname in ("rounded_total", "grand_total"):
		if meta.has_field(fieldname):
			amount = frappe.db.get_value(doctype, document_name, fieldname)
			if amount:
				break

	return {
		"party": get_party_name(doctype, document_name) or party or "",
		"phone": phone,
		"amount": float(amount or 0),
	}


# Companion Chrome extension, shipped as source in the app repo. Zipped on request so the
# download always matches the installed app instead of a checked-in binary going stale.
EXTENSION_FOLDER = ("chrome-extension", "whatsapp-tab")


def get_extension_path():
	app_root = os.path.dirname(frappe.get_app_path("ssplbilling"))
	return os.path.join(app_root, *EXTENSION_FOLDER)


@frappe.whitelist()
def download_whatsapp_extension():
	"""Serve the SSPL WhatsApp Tab extension as a zip for Chrome's "Load unpacked"."""
	folder = get_extension_path()
	if not os.path.isdir(folder):
		frappe.throw("Extension folder is missing from this installation")

	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
		for root, _dirs, files in os.walk(folder):
			for filename in files:
				full_path = os.path.join(root, filename)
				# Everything sits under one top-level folder, so unzipping cannot scatter
				# files and the folder is ready to hand to "Load unpacked" as it is.
				arcname = os.path.join(
					EXTENSION_FOLDER[-1], os.path.relpath(full_path, folder)
				)
				archive.write(full_path, arcname)

	frappe.local.response.filename = "sspl-whatsapp-tab.zip"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "binary"
