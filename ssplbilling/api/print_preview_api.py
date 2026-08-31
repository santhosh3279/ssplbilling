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
import re
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
