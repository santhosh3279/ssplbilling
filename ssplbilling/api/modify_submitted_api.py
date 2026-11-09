import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import add_days, flt, getdate, now


SUPPORTED_DOCTYPES = ("Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order", "Purchase Order")
INVOICE_DOCTYPES = ("Sales Invoice", "Purchase Invoice")


def _validate_doctype(doctype):
	if doctype not in SUPPORTED_DOCTYPES:
		frappe.throw("Select a Sales/Purchase Invoice, Quotation, Sales Order, or Purchase Order.")
	return doctype


def _check_authenticated():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify bills.", frappe.PermissionError)


def _submitted_mirror_name(doctype, invoice_no, company, linked_name=None):
	"""Find an existing submitted mirror in a different company."""
	if doctype not in INVOICE_DOCTYPES:
		return None
	if doctype == "Sales Invoice":
		from ssplbilling.api.automatic_entries_api import mirror_name_for
		linked_name = mirror_name_for(invoice_no)
	if not linked_name:
		return None
	mirror = frappe.db.get_value(doctype, linked_name, ["name", "company", "docstatus"], as_dict=True)
	if mirror and mirror.company != company and mirror.docstatus == 1:
		return mirror.name
	return None


def _linked_payment_vouchers(doc):
	if doc.doctype == "Quotation":
		return set()
	if doc.doctype in ("Sales Order", "Purchase Order"):
		# Order advances are linked through references rather than invoice PLEs.
		payments = frappe.get_all("Payment Entry Reference", filters={
			"reference_doctype": doc.doctype, "reference_name": doc.name, "docstatus": 1,
		}, pluck="parent")
		journals = frappe.get_all("Journal Entry Account", filters={
			"reference_type": doc.doctype, "reference_name": doc.name, "docstatus": 1,
		}, pluck="parent")
		return {("Payment Entry", name) for name in payments} | {("Journal Entry", name) for name in journals}
	from erpnext.accounts.doctype.unreconcile_payment.unreconcile_payment import (
		get_linked_payments_for_doc,
	)

	linked = get_linked_payments_for_doc(company=doc.company, doctype=doc.doctype, docname=doc.name)
	vouchers = {(row.reference_doctype, row.reference_name) for row in linked}
	unsupported = sorted({voucher_type for voucher_type, _ in vouchers} - {"Payment Entry", "Journal Entry"})
	if unsupported:
		frappe.throw(f"Cannot unlink allocations from {', '.join(unsupported)} automatically. Please unreconcile them first.")
	return vouchers


def _unlink_payments_and_cancel(doc, vouchers):
	for voucher_type, voucher_no in sorted(vouchers):
		unreconcile = frappe.new_doc("Unreconcile Payment")
		unreconcile.company = doc.company
		unreconcile.voucher_type = voucher_type
		unreconcile.voucher_no = voucher_no
		unreconcile.add_references()
		unreconcile.allocations = [
			row for row in unreconcile.allocations
			if row.reference_doctype == doc.doctype and row.reference_name == doc.name
		]
		if not unreconcile.allocations:
			frappe.throw(f"Could not unlink payment {voucher_no} from {doc.name}. Please refresh and try again.")
		unreconcile.insert()
		unreconcile.submit()

	doc.reload()
	doc.cancel()


def _archive_cancelled_invoice(doc):
	"""Free the original number while preserving cancelled records and their links."""
	if doc.docstatus != 2:
		frappe.throw("Only cancelled invoices can be archived.")
	original_name = doc.name
	suffix = 1
	while frappe.db.exists(doc.doctype, f"{original_name}-{suffix}"):
		suffix += 1
	archived_name = frappe.rename_doc(
		doc.doctype, original_name, f"{original_name}-{suffix}",
		force=True, show_alert=False,
	)
	return frappe.get_doc(doc.doctype, archived_name)


@frappe.whitelist()
def get_submitted_invoice(invoice_no, doctype=None, allow_draft=0):
	"""Fetch a submitted billing document (or a draft, for the rename page); explicit type avoids
	number collisions."""
	_check_authenticated()
	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please select a bill.")
	if doctype:
		_validate_doctype(doctype)
	else:
		matches = [kind for kind in SUPPORTED_DOCTYPES if frappe.db.exists(kind, invoice_no)]
		if len(matches) > 1:
			frappe.throw("This bill number exists in multiple document types. Select it from the bill palette.")
		doctype = matches[0] if matches else None
	if not doctype or not frappe.db.exists(doctype, invoice_no):
		frappe.throw(f"Bill '{invoice_no}' was not found.")

	doc = frappe.get_doc(doctype, invoice_no)
	doc.check_permission("read")
	if doc.docstatus != 1 and not (doc.docstatus == 0 and frappe.utils.cint(allow_draft)):
		frappe.throw(f"Bill '{invoice_no}' must be submitted. Draft and cancelled documents cannot be modified here.")
	date_field = "posting_date" if doctype in INVOICE_DOCTYPES else "transaction_date"
	party = doc.get("supplier") or doc.get("customer") or doc.get("party_name")
	party_name = doc.get("supplier_name") or doc.get("customer_name") or party
	items = doc.get("items") or []
	return {
		"doctype": doctype,
		"name": doc.name,
		"docstatus": doc.docstatus,
		"party": party,
		"party_name": party_name,
		"posting_date": str(doc.get(date_field)),
		"date_field": date_field,
		"posting_time": str(doc.get("posting_time") or ""),
		"due_date": str(doc.get("due_date") or ""),
		"grand_total": doc.get("grand_total") or 0,
		"outstanding_amount": doc.get("outstanding_amount") or 0,
		"company": doc.company,
		"mirror_invoice": _submitted_mirror_name(doctype, doc.name, doc.company, doc.get("custom_mirrored")),
		"item_count": len(items),
		"items": [{field: item.get(field) for field in ("item_code", "item_name", "qty", "uom", "rate", "amount")} for item in items[:10]],
	}


@frappe.whitelist()
def move_submitted_to_draft(invoice_no, doctype="Sales Invoice"):
	"""Unlink payments, cancel a submitted invoice, and create an amended draft."""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify invoices.", frappe.PermissionError)
	_validate_doctype(doctype)

	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please enter an invoice number.")

	doc = frappe.get_doc(doctype, invoice_no)
	doc.check_permission("cancel")
	doc.check_permission("write")
	if doc.docstatus != 1:
		frappe.throw(f"Invoice '{invoice_no}' must be submitted to move it to draft mode.")

	mirror_name = _submitted_mirror_name(doctype, doc.name, doc.company, doc.get("custom_mirrored"))
	mirror = frappe.get_doc(doctype, mirror_name) if mirror_name else None
	if mirror:
		mirror.check_permission("cancel")
		mirror.check_permission("write")

	# Check both sets of links before mutating either invoice.
	mirror_vouchers = _linked_payment_vouchers(mirror) if mirror else set()
	vouchers = _linked_payment_vouchers(doc)
	if mirror:
		_unlink_payments_and_cancel(mirror, mirror_vouchers)
	_unlink_payments_and_cancel(doc, vouchers)
	if mirror:
		mirror = _archive_cancelled_invoice(mirror)
	doc = _archive_cancelled_invoice(doc)
	amended = frappe.copy_doc(doc)
	amended.amended_from = doc.name
	amended.docstatus = 0
	amended.name = None
	if amended.meta.has_field("advances"):
		amended.set("advances", [])
	if doctype == "Purchase Invoice" and frappe.get_meta(doctype).has_field("custom_mirrored"):
		amended.set("custom_mirrored", None)
	if hasattr(amended, "set_posting_time"):
		amended.set_posting_time = 0
	# Explicit naming bypasses the usual amendment suffix. The cancelled record
	# remains available under its archived name for amendment and ledger history.
	amended.insert(set_name=invoice_no)

	return {
		"status": "draft_created",
		"cancelled_invoice": doc.name,
		"draft_invoice": amended.name,
		"doctype": doctype,
		"cancelled_mirror": mirror.name if mirror else None,
		"unlinked_payments": len(vouchers) + len(mirror_vouchers),
	}


@frappe.whitelist()
def modify_submitted_bill_date(invoice_no, new_date, doctype="Sales Invoice"):
	"""Directly modifies the bill date (posting_date) in the DB for a submitted invoice.

	Updates Sales/Purchase Invoice, GL Entry, Payment Ledger Entry, Stock Ledger Entry,
	and Serial/Batch bundle tables consistently.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required to modify invoices.", frappe.PermissionError)

	invoice_no = (invoice_no or "").strip()
	if not invoice_no:
		frappe.throw("Please enter an invoice number.")
	if not new_date:
		frappe.throw("Please select a new bill date.")

	try:
		new_date_obj = getdate(new_date)
		new_date_str = str(new_date_obj)
	except Exception:
		frappe.throw(f"Invalid date format: {new_date}")

	_validate_doctype(doctype)

	doc = frappe.get_doc(doctype, invoice_no)
	if doc.docstatus != 1:
		frappe.throw(
			f"Invoice '{invoice_no}' is not in submitted state (docstatus={doc.docstatus}). "
			"Only submitted invoices can be modified."
		)

	if doctype not in INVOICE_DOCTYPES:
		return _modify_transaction_date(doc, new_date_str)

	old_date = doc.posting_date
	old_date_str = str(old_date)
	if old_date_str == new_date_str:
		return {
			"status": "unchanged",
			"name": invoice_no,
			"posting_date": new_date_str,
			"message": f"Bill date for {invoice_no} is already {new_date_str}.",
		}

	# Check permissions
	if not (frappe.has_permission(doctype, "write") or frappe.has_permission(doctype, "cancel")):
		frappe.throw(f"You do not have permission to modify {doctype}.", frappe.PermissionError)

	# Calculate fiscal year for the new date
	try:
		fy = get_fiscal_year(new_date_str, company=doc.company)[0]
	except Exception:
		fy = None

	# Calculate due date adjustment
	if doc.due_date and old_date:
		diff_days = (getdate(doc.due_date) - getdate(old_date)).days
		new_due_date = add_days(new_date_str, diff_days)
	else:
		new_due_date = new_date_str

	now_time = now()
	posting_time_str = str(doc.posting_time or "00:00:00")
	if len(posting_time_str.split(":")) == 2:
		posting_time_str += ":00"
	new_posting_datetime = f"{new_date_str} {posting_time_str}"

	# 1. Update Invoice Document in DB
	inv_update = {
		"posting_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if doctype == "Purchase Invoice" and hasattr(doc, "bill_date"):
		inv_update["bill_date"] = new_date_str

	frappe.db.set_value(doctype, invoice_no, inv_update, update_modified=False)

	# If Sales Invoice, update child clearance_date if matching old date
	if doctype == "Sales Invoice":
		frappe.db.sql(
			"""UPDATE `tabSales Invoice Payment`
			   SET clearance_date = %(new_date)s
			   WHERE parent = %(invoice_no)s AND clearance_date = %(old_date)s""",
			{"new_date": new_date_str, "invoice_no": invoice_no, "old_date": old_date_str},
		)

	# 2. Update GL Entry
	gl_updates = {
		"posting_date": new_date_str,
		"transaction_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if fy:
		gl_updates["fiscal_year"] = fy
	gl_set_sql = ", ".join([f"`{k}` = %({k})s" for k in gl_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabGL Entry`
		   SET {gl_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**gl_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 3. Update Payment Ledger Entry
	ple_updates = {
		"posting_date": new_date_str,
		"due_date": new_due_date,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	ple_set_sql = ", ".join([f"`{k}` = %({k})s" for k in ple_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabPayment Ledger Entry`
		   SET {ple_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**ple_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 4. Update Stock Ledger Entry
	sle_updates = {
		"posting_date": new_date_str,
		"posting_datetime": new_posting_datetime,
		"modified": now_time,
		"modified_by": frappe.session.user,
	}
	if fy:
		sle_updates["fiscal_year"] = fy
	sle_set_sql = ", ".join([f"`{k}` = %({k})s" for k in sle_updates.keys()])
	frappe.db.sql(
		f"""UPDATE `tabStock Ledger Entry`
		   SET {sle_set_sql}
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{**sle_updates, "doctype": doctype, "invoice_no": invoice_no},
	)

	# 5. Update Serial and Batch Bundle
	frappe.db.sql(
		"""UPDATE `tabSerial and Batch Bundle`
		   SET posting_datetime = %(posting_datetime)s,
		       modified = %(modified)s,
		       modified_by = %(modified_by)s
		   WHERE voucher_type = %(doctype)s AND voucher_no = %(invoice_no)s""",
		{
			"posting_datetime": new_posting_datetime,
			"modified": now_time,
			"modified_by": frappe.session.user,
			"doctype": doctype,
			"invoice_no": invoice_no,
		},
	)

	# Clear cached document
	frappe.clear_document_cache(doctype, invoice_no)

	# Audit trail comment
	try:
		doc.add_comment(
			"Info",
			f"Bill date modified from {old_date_str} to {new_date_str} by {frappe.session.user}",
		)
	except Exception:
		pass

	frappe.db.commit()

	return {
		"status": "success",
		"name": invoice_no,
		"doctype": doctype,
		"old_date": old_date_str,
		"new_date": new_date_str,
		"message": f"Bill date for {invoice_no} changed from {old_date_str} to {new_date_str} successfully.",
	}


def _modify_transaction_date(doc, new_date):
	"""Orders and quotations have no invoice ledgers; update their transaction date."""
	doc.check_permission("write")
	old_date = str(doc.transaction_date)
	if old_date == new_date:
		return {"status": "unchanged", "name": doc.name, "doctype": doc.doctype,
			"new_date": new_date, "message": f"Bill date for {doc.name} is already {new_date}."}

	# Preserve normal date constraints without silently moving delivery/validity dates.
	for field in ("delivery_date", "schedule_date", "valid_till"):
		if doc.get(field) and getdate(doc.get(field)) < getdate(new_date):
			frappe.throw(f"New bill date cannot be after {doc.meta.get_label(field)} ({doc.get(field)}).")
	for table in ("items", "payment_schedule"):
		for row in doc.get(table) or []:
			for field in ("delivery_date", "schedule_date", "due_date"):
				if row.get(field) and getdate(row.get(field)) < getdate(new_date):
					frappe.throw(f"New bill date cannot be after {field.replace('_', ' ')} ({row.get(field)}).")

	frappe.db.set_value(doc.doctype, doc.name, {
		"transaction_date": new_date, "modified": now(), "modified_by": frappe.session.user,
	}, update_modified=False)
	frappe.clear_document_cache(doc.doctype, doc.name)
	doc.add_comment("Info", f"Bill date modified from {old_date} to {new_date} by {frappe.session.user}")
	return {"status": "success", "name": doc.name, "doctype": doc.doctype,
		"old_date": old_date, "new_date": new_date,
		"message": f"Bill date for {doc.name} changed from {old_date} to {new_date} successfully."}


def _naming_series_options(doctype):
	field = frappe.get_meta(doctype).get_field("naming_series")
	return [opt.strip() for opt in ((field.options if field else "") or "").split("\n") if opt.strip()]


def _series_for_name(doctype, name, preferred=()):
	"""Match `name` to the naming series option it belongs to: (series, prefix, number), or None.

	A name can fit several series (`PLV00101` is both `PLV.#####` and `PLV0.####`), so series
	listed in `preferred` win first; otherwise the longest matching prefix wins so `PLVA00001`
	never resolves to a `PLV` series."""
	from frappe.model.naming import NamingSeries

	preferred = list(preferred or [])
	best = best_key = None
	for series in _naming_series_options(doctype):
		try:
			prefix = NamingSeries(series).get_prefix()
		except Exception:
			continue
		number = name[len(prefix):].rstrip("/")
		if prefix and name.startswith(prefix) and number.isdigit():
			rank = preferred.index(series) if series in preferred else len(preferred)
			key = (-rank, len(prefix))
			if not best or key > best_key:
				best, best_key = (series, prefix, int(number)), key
	return best


def _next_series_name(doctype, series):
	"""Next free name in `series` without consuming the counter."""
	import re
	from frappe.model.naming import NamingSeries

	prefix = NamingSeries(series).get_prefix()
	m = re.search(r"#+", series)
	digits = len(m.group(0)) if m else 5
	# Slashed names are a separate number space, and the shared tabSeries counter
	# also counts them, so only plain names decide the next free number.
	highest = 0
	for name in frappe.get_all(doctype, filters={"name": ["like", f"{prefix}%"]}, pluck="name"):
		number = name[len(prefix):]
		if number.isdigit():
			highest = max(highest, int(number))
	candidate = f"{prefix}{highest + 1:0{digits}d}"
	while frappe.db.exists(doctype, candidate):
		highest += 1
		candidate = f"{prefix}{highest + 1:0{digits}d}"
	return candidate


@frappe.whitelist()
def get_bill_number_series(doctype="Purchase Invoice"):
	"""Naming series of `doctype` with the next free number in each, for the rename page."""
	_check_authenticated()
	_validate_doctype(doctype)
	result = []
	for series in _naming_series_options(doctype):
		try:
			result.append({"series": series, "next_name": _next_series_name(doctype, series)})
		except Exception:
			continue
	return result


@frappe.whitelist()
def rename_submitted_bill(invoice_no, new_name, doctype="Purchase Invoice"):
	"""Rename a submitted or draft bill. Ledger links follow through rename_doc; the Data-typed
	custom_mirrored pair, naming_series and the series counter are fixed up here."""
	_check_authenticated()
	_validate_doctype(doctype)
	invoice_no = (invoice_no or "").strip()
	new_name = (new_name or "").strip()
	if not invoice_no:
		frappe.throw("Please select a bill.")
	if not new_name:
		frappe.throw("Please enter the new bill number.")
	if new_name == invoice_no:
		frappe.throw("The new bill number is the same as the current one.")

	doc = frappe.get_doc(doctype, invoice_no)
	doc.check_permission("write")
	if doc.docstatus == 2:
		frappe.throw(f"Bill '{invoice_no}' is cancelled. Its number cannot be changed.")
	if doc.get("irn") or doc.get("ewaybill"):
		frappe.throw(f"Bill '{invoice_no}' has an e-invoice / e-way bill. Its number cannot be changed.")
	if frappe.db.exists(doctype, new_name):
		frappe.throw(f"{doctype} '{new_name}' already exists.")

	has_mirror_field = doc.meta.has_field("custom_mirrored")
	partner = doc.get("custom_mirrored") if has_mirror_field else None
	if partner and not frappe.db.exists(doctype, partner):
		partner = None
	if doctype == "Sales Invoice":
		from ssplbilling.api.automatic_entries_api import mirror_name_for

		if frappe.db.exists(doctype, mirror_name_for(invoice_no)):
			frappe.throw(f"Bill '{invoice_no}' has a mirror bill linked by its number. Its number cannot be changed.")

	# Prefer the user's allowed series (what the bill lists filter on), then the bill's own.
	from ssplbilling.api.dashboard_api import get_allowed_series

	allowed = get_allowed_series(doctype=doctype)
	allowed = (allowed.get("allowed_series") if isinstance(allowed, dict) else allowed) or []
	match = _series_for_name(doctype, new_name, preferred=[*allowed, doc.naming_series])
	if not match:
		frappe.throw(f"'{new_name}' does not match any {doctype} naming series. Use a number like the suggestions shown.")
	series, prefix, number = match

	frappe.rename_doc(doctype, invoice_no, new_name, force=True, show_alert=False)
	frappe.db.set_value(doctype, new_name, "naming_series", series, update_modified=False)
	frappe.db.sql(
		"""INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)
		   ON DUPLICATE KEY UPDATE current = GREATEST(current, VALUES(current))""",
		(prefix, number),
	)
	if has_mirror_field:
		# custom_mirrored is a Data field, so rename_doc does not follow it.
		frappe.db.sql(
			f"UPDATE `tab{doctype}` SET custom_mirrored = %s WHERE custom_mirrored = %s",
			(new_name, invoice_no),
		)
		if partner:
			frappe.clear_document_cache(doctype, partner)
	frappe.clear_document_cache(doctype, new_name)

	return {
		"status": "success",
		"doctype": doctype,
		"old_name": invoice_no,
		"new_name": new_name,
		"naming_series": series,
		"mirror_invoice": partner,
		"message": f"{doctype} {invoice_no} renamed to {new_name}.",
	}


# ── Purchase mirror link repair ─────────────────────────────────────────────

_MIRROR_FIELDS = [
	"name", "company", "docstatus", "naming_series", "supplier", "supplier_name", "bill_no",
	"posting_date", "base_grand_total", "custom_mirrored",
]


def _norm_bill_no(value):
	return (value or "").strip().lower()


def _mirror_rows(**kwargs):
	"""Purchase Invoices with `custom_mirrored` cleaned up: old bills carry "0" for no link."""
	rows = frappe.get_all("Purchase Invoice", fields=_MIRROR_FIELDS, **kwargs)
	for r in rows:
		link = (r.custom_mirrored or "").strip()
		r.custom_mirrored = "" if link == "0" else link
	return rows


def _same_bill(a, b):
	"""Two bills are the same purchase when their supplier bill numbers match; bills without
	a number only match on an equal total."""
	if _norm_bill_no(a.bill_no) or _norm_bill_no(b.bill_no):
		return _norm_bill_no(a.bill_no) == _norm_bill_no(b.bill_no)
	return abs(flt(a.base_grand_total) - flt(b.base_grand_total)) < 0.02


def _mirror_company():
	from ssplbilling.api.automatic_entries_api import get_automatic_entries

	if not frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		frappe.throw("Purchase Invoice has no Mirrored field, so there are no mirror links to repair.")
	ae = get_automatic_entries()
	if not ae.alternative_company:
		frappe.throw("No alternative company is set in Automatic Entries, so purchase bills are not mirrored.")
	return ae, ae.alternative_company


@frappe.whitelist()
def get_purchase_mirror_links(from_date=None, to_date=None):
	"""Purchase bills of the billing company(s) in the period with the mirror bill they link to and
	the mirror bill that really is their copy (same supplier bill number), plus mirror bills in the
	period that no bill claims. Read only."""
	_check_authenticated()
	from ssplbilling.api.purchase_mirror_api import should_mirror_purchase_invoice

	ae, ae_company = _mirror_company()
	to_date = getdate(to_date or now())
	from_date = getdate(from_date or add_days(to_date, -60))
	if to_date < from_date:
		frappe.throw("To date is before from date.")

	originals = [
		r for r in _mirror_rows(
			filters={"company": ["!=", ae_company], "docstatus": ["<", 2],
				"posting_date": ["between", [from_date, to_date]]},
			order_by="posting_date asc, name asc",
		)
		if r.custom_mirrored or r.name.endswith("/")
		or should_mirror_purchase_invoice(r.naming_series, ae) or should_mirror_purchase_invoice(r.name, ae)
	]
	# Mirrors can be posted on another day than their original, so look well past the period edges.
	pool = {
		r.name: r for r in _mirror_rows(
			filters={"company": ae_company, "docstatus": ["<", 2],
				"posting_date": ["between", [add_days(from_date, -120), add_days(to_date, 120)]]},
		)
	}
	linked = {r.custom_mirrored for r in originals if r.custom_mirrored and r.custom_mirrored not in pool}
	if linked:
		for r in _mirror_rows(
			filters={"name": ["in", list(linked)], "company": ae_company, "docstatus": ["<", 2]},
		):
			pool[r.name] = r

	# Pass 1: links that already point at the right copy keep it.
	used, partner = set(), {}
	for o in originals:
		cur = pool.get(o.custom_mirrored or "")
		if cur and _same_bill(o, cur):
			partner[o.name] = cur
			used.add(cur.name)

	# Pass 2: everything else gets the closest unclaimed copy with the same bill number.
	suggested = {}
	for o in originals:
		if o.name in partner:
			continue
		toggled = o.name[:-1] if o.name.endswith("/") else f"{o.name}/"
		cands = [m for m in pool.values() if m.name not in used and _same_bill(o, m)]
		cands.sort(key=lambda m: (
			abs(flt(m.base_grand_total) - flt(o.base_grand_total)) >= 0.02,
			m.name != toggled,
			abs(flt(m.base_grand_total) - flt(o.base_grand_total)),
			abs((getdate(m.posting_date) - getdate(o.posting_date)).days),
		))
		if cands:
			suggested[o.name] = cands[0]
			used.add(cands[0].name)

	rows = []
	for o in originals:
		mirror = partner.get(o.name) or suggested.get(o.name)
		cur = pool.get(o.custom_mirrored or "")
		diff = flt(flt(o.base_grand_total) - flt(mirror.base_grand_total), 2) if mirror else None
		if o.name in partner:
			back_ok = (mirror.custom_mirrored or "") == o.name
			status = "back_link" if not back_ok else ("amount_diff" if abs(diff) >= 0.5 else "ok")
			fixable = not back_ok
		elif mirror:
			status = "wrong_link" if o.custom_mirrored else "unlinked"
			fixable = True
		else:
			status, fixable = "no_mirror", False
		rows.append({
			"bill": o.name,
			"company": o.company,
			"posting_date": str(o.posting_date),
			"supplier": o.supplier_name or o.supplier,
			"bill_no": o.bill_no or "",
			"docstatus": o.docstatus,
			"total": flt(o.base_grand_total, 2),
			"current": o.custom_mirrored or "",
			"current_total": flt(cur.base_grand_total, 2) if cur else None,
			"mirror": mirror.name if mirror else "",
			"mirror_total": flt(mirror.base_grand_total, 2) if mirror else None,
			"mirror_back": (mirror.custom_mirrored or "") if mirror else "",
			"difference": diff,
			"status": status,
			"fixable": fixable,
		})

	orphans = [
		{
			"mirror": m.name,
			"posting_date": str(m.posting_date),
			"supplier": m.supplier_name or m.supplier,
			"bill_no": m.bill_no or "",
			"docstatus": m.docstatus,
			"total": flt(m.base_grand_total, 2),
			"current": m.custom_mirrored or "",
		}
		for m in sorted(pool.values(), key=lambda m: (m.posting_date, m.name))
		if m.name not in used and from_date <= getdate(m.posting_date) <= to_date
	]
	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"mirror_company": ae_company,
		"rows": rows,
		"orphans": orphans,
	}


@frappe.whitelist()
def fix_purchase_mirror_links(pairs):
	"""Point each {bill, mirror} pair at each other. Any other bill still pointing at one of them
	is unlinked so every link stays one-to-one. Only the Mirrored field changes; ledger, stock and
	`modified` are untouched. Every change is noted in the bills' comments."""
	_check_authenticated()
	_ae, ae_company = _mirror_company()
	pairs = frappe.parse_json(pairs) or []
	if not pairs:
		frappe.throw("Select at least one bill to fix.")

	final, docs = {}, {}
	for p in pairs:
		bill, mirror = (p.get("bill") or "").strip(), (p.get("mirror") or "").strip()
		if not bill or not mirror:
			frappe.throw("Every row needs a bill and a mirror bill.")
		if bill in final or mirror in final:
			frappe.throw(f"{bill if bill in final else mirror} appears in more than one row.")
		o = frappe.db.get_value("Purchase Invoice", bill, _MIRROR_FIELDS, as_dict=True)
		m = frappe.db.get_value("Purchase Invoice", mirror, _MIRROR_FIELDS, as_dict=True)
		if not o or not m:
			frappe.throw(f"Purchase Invoice {bill if not o else mirror} not found.")
		if o.docstatus == 2 or m.docstatus == 2:
			frappe.throw(f"{bill} or {mirror} is cancelled.")
		if o.company == ae_company or m.company != ae_company:
			frappe.throw(f"{mirror} must be in {ae_company} and {bill} in another company.")
		if not _same_bill(o, m):
			frappe.throw(f"{bill} (bill no {o.bill_no or '-'}) and {mirror} (bill no {m.bill_no or '-'}) are not the same purchase.")
		for name in (bill, mirror):
			frappe.has_permission("Purchase Invoice", "write", doc=name, throw=True)
		final[bill], final[mirror] = mirror, bill
		docs[bill], docs[mirror] = o, m

	# Bills outside the batch that still point at a bill in the batch lose that link.
	stale = frappe.get_all(
		"Purchase Invoice",
		filters={"custom_mirrored": ["in", list(final)], "name": ["not in", list(final)]},
		fields=_MIRROR_FIELDS,
	)
	changes = [(name, docs[name].custom_mirrored or "", final[name]) for name in final]
	changes += [(s.name, s.custom_mirrored, "") for s in stale]

	user = frappe.session.user
	for name, old, new in changes:
		if old == new:
			continue
		frappe.db.set_value("Purchase Invoice", name, "custom_mirrored", new, update_modified=False)
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": "Purchase Invoice", "reference_name": name,
			"content": f"Mirror link changed from {old or '(none)'} to {new or '(none)'} by {user} (Fix Mirror Links)",
		}).insert(ignore_permissions=True)
		frappe.clear_document_cache("Purchase Invoice", name)

	return {
		"fixed": len(pairs),
		"unlinked": [s.name for s in stale],
		"changes": [{"name": n, "old": o, "new": v} for n, o, v in changes if o != v],
	}
