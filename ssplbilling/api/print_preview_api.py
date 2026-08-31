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
