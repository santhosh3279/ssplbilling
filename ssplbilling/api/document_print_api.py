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


@frappe.whitelist(methods=["POST"])
def print_uploaded_file(printer, copies=1):
	"""Send the multipart `file` field to `printer` (a Printer doc name)."""
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

	printer_doc = frappe.get_cached_doc("Printer", printer)
	server_doc = frappe.get_cached_doc("Printer Server", printer_doc.printer_server)
	job_name = (upload.filename or "document")[:100]

	job_id = None
	for _i in range(copies):
		job_id = send_pdf_to_cups(server_doc, printer_doc.cups_printer_name, pdf_bytes, job_name)

	return {"success": True, "cups_job_id": job_id, "copies": copies, "printer": printer_doc.printer_name}
