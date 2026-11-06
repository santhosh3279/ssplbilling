"""Print an uploaded document straight to a CUPS printer.

The upload is read from the multipart request body into memory, converted to PDF
when it is an image, and handed to CUPS over IPP. Nothing is written to the
database or the file system: no File doc, no attachment, no print log.
"""

import io

import frappe
from frappe import _

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_COPIES = 50
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff")


def _require_user():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)


def _image_to_pdf(raw):
	from PIL import Image, ImageSequence

	try:
		img = Image.open(io.BytesIO(raw))
		frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(img)]
	except Exception:
		frappe.throw(_("Could not read the image file"))
	buf = io.BytesIO()
	frames[0].save(buf, "PDF", resolution=150, save_all=True, append_images=frames[1:])
	return buf.getvalue()


def _to_pdf(filename, raw):
	name = (filename or "").lower()
	if raw[:5] == b"%PDF-":
		return raw
	if name.endswith(IMAGE_EXTENSIONS):
		return _image_to_pdf(raw)
	frappe.throw(_("Only PDF and image files can be printed"))


def _page_number(value, label):
	try:
		number = int(value)
	except TypeError, ValueError:
		frappe.throw(_("{0} must be a whole number").format(label))
	if number < 1:
		frappe.throw(_("{0} must be 1 or more").format(label))
	return number


def _select_pages(pdf_bytes, page_from, page_to):
	"""Return (pdf_bytes, total_pages, printed_pages) keeping only pages page_from..page_to (1-based)."""
	from pypdf import PdfReader, PdfWriter

	try:
		reader = PdfReader(io.BytesIO(pdf_bytes))
		total = len(reader.pages)
	except Exception:
		frappe.throw(_("Could not read the PDF file"))

	if not page_from and not page_to:
		return pdf_bytes, total, total

	start = _page_number(page_from or 1, _("From page"))
	end = _page_number(page_to or start, _("To page"))
	if start > end:
		frappe.throw(_("From page ({0}) is after To page ({1})").format(start, end))
	if end > total:
		frappe.throw(_("The document has only {0} page(s)").format(total))
	if start == 1 and end == total:
		return pdf_bytes, total, total

	writer = PdfWriter()
	for index in range(start - 1, end):
		writer.add_page(reader.pages[index])
	buf = io.BytesIO()
	writer.write(buf)
	return buf.getvalue(), total, end - start + 1


@frappe.whitelist(methods=["POST"])
def print_uploaded_file(printer, copies=1, page_from=None, page_to=None):
	"""Send the multipart `file` field to `printer` (a Printer doc name).

	`page_from` / `page_to` (1-based, inclusive) limit printing to those pages; both empty = all pages.
	"""
	from printer_server_configuration.printer_server_configuration.utils.cups_utils import (
		send_pdf_to_cups,
	)

	_require_user()

	upload = frappe.request.files.get("file") if frappe.request else None
	if not upload:
		frappe.throw(_("No file uploaded"))

	raw = upload.stream.read(MAX_UPLOAD_BYTES + 1)
	if not raw:
		frappe.throw(_("The uploaded file is empty"))
	if len(raw) > MAX_UPLOAD_BYTES:
		frappe.throw(_("File is larger than {0} MB").format(MAX_UPLOAD_BYTES // (1024 * 1024)))

	copies = max(1, min(int(copies or 1), MAX_COPIES))
	pdf_bytes = _to_pdf(upload.filename, raw)
	pdf_bytes, total_pages, printed_pages = _select_pages(pdf_bytes, page_from, page_to)

	printer_doc = frappe.get_cached_doc("Printer", printer)
	server_doc = frappe.get_cached_doc("Printer Server", printer_doc.printer_server)
	job_name = (upload.filename or "document")[:100]

	job_id = None
	for _i in range(copies):
		job_id = send_pdf_to_cups(server_doc, printer_doc.cups_printer_name, pdf_bytes, job_name)

	return {
		"success": True,
		"cups_job_id": job_id,
		"copies": copies,
		"printer": printer_doc.printer_name,
		"total_pages": total_pages,
		"printed_pages": printed_pages,
	}


@frappe.whitelist(methods=["POST"])
def count_pages():
	"""Return the page count of the multipart `file` field (PDF or image). Nothing is stored."""
	_require_user()
	upload = frappe.request.files.get("file") if frappe.request else None
	if not upload:
		frappe.throw(_("No file uploaded"))
	raw = upload.stream.read(MAX_UPLOAD_BYTES + 1)
	if not raw or len(raw) > MAX_UPLOAD_BYTES:
		frappe.throw(_("File is empty or larger than {0} MB").format(MAX_UPLOAD_BYTES // (1024 * 1024)))
	_pdf, total, _printed = _select_pages(_to_pdf(upload.filename, raw), None, None)
	return {"total_pages": total}
