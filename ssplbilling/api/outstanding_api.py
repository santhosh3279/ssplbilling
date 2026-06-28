import frappe


def _get_company():
	return frappe.defaults.get_global_default("company")


@frappe.whitelist()
def get_party_outstanding(party_type, party):
	"""Return outstanding invoices, unlinked payment entries, and unlinked journal entries for a party.

	Settled and fully-linked entries are excluded. Only rows with a positive outstanding or
	unallocated balance are returned.
	"""
	company = _get_company()

	# ── 1. Outstanding Invoices ──────────────────────────────────────────────────────────────────
	invoices = []
	payment_entries = []
	journal_entries = []

	from erpnext.accounts.party import get_party_account
	party_account = get_party_account(party_type, party, company)

	if party_account:
		ledger_rows = frappe.db.sql(
			"""
			SELECT
				against_voucher_type AS voucher_type,
				against_voucher_no AS voucher_no,
				SUM(amount_in_account_currency) AS outstanding_amount,
				MAX(posting_date) AS posting_date
			FROM `tabPayment Ledger Entry`
			WHERE party_type = %s
				AND party = %s
				AND account = %s
				AND company = %s
				AND delinked = 0
			GROUP BY against_voucher_type, against_voucher_no
			HAVING ABS(outstanding_amount) > 0.005
			ORDER BY posting_date DESC
			""",
			(party_type, party, party_account, company),
			as_dict=True,
		)

		for d in ledger_rows:
			v_type = d.voucher_type
			v_no = d.voucher_no
			out_amt = float(d.outstanding_amount or 0)
			post_date = str(d.posting_date)

			if v_type in ("Sales Invoice", "Purchase Invoice"):
				inv_info = frappe.db.get_value(v_type, v_no, ["grand_total", "is_return"], as_dict=True) or {"grand_total": 0, "is_return": 0}
				is_return = inv_info.get("is_return") or 0
				grand_total = float(inv_info.get("grand_total") or 0)

				direction = "Dr"
				if v_type == "Sales Invoice":
					direction = "Cr" if is_return or out_amt < 0 else "Dr"
				elif v_type == "Purchase Invoice":
					direction = "Dr" if is_return or out_amt < 0 else "Cr"

				invoices.append({
					"name": v_no,
					"posting_date": post_date,
					"grand_total": grand_total,
					"outstanding_amount": abs(out_amt),
					"is_return": int(is_return or 0),
					"direction": direction,
					"doctype": v_type,
					"linked_count": 0
				})

			elif v_type == "Payment Entry":
				pe_info = frappe.db.get_value("Payment Entry", v_no, ["paid_amount", "mode_of_payment", "remarks"], as_dict=True) or {"paid_amount": 0, "mode_of_payment": "Cash", "remarks": ""}
				paid_amount = float(pe_info.get("paid_amount") or 0)
				mop = pe_info.get("mode_of_payment") or "Cash"
				remarks = pe_info.get("remarks") or ""

				direction = "Cr" if out_amt < 0 else "Dr"

				payment_entries.append({
					"name": v_no,
					"posting_date": post_date,
					"paid_amount": paid_amount,
					"unallocated_amount": abs(out_amt),
					"mode_of_payment": mop,
					"remarks": remarks,
					"direction": direction,
					"linked_count": 0
				})

			elif v_type == "Journal Entry":
				je_row_name = frappe.db.get_value("Journal Entry Account", {"parent": v_no, "party": party, "account": party_account}, "name")
				remarks = frappe.db.get_value("Journal Entry", v_no, "user_remark") or ""

				direction = "Cr" if out_amt < 0 else "Dr"

				journal_entries.append({
					"name": v_no,
					"account": party_account,
					"reference_row": je_row_name or v_no,
					"posting_date": post_date,
					"reference_no": "",
					"remarks": remarks,
					"journal_total_debit": abs(out_amt),
					"total_amount": abs(out_amt),
					"unallocated_amount": abs(out_amt),
					"direction": direction,
					"linked_count": 0
				})

	# ── Linked document counts ───────────────────────────────────────────────────────────────────
	# Invoices: count of submitted PEs + submitted JEs that reference each invoice
	if invoices:
		inv_names = tuple(i["name"] for i in invoices)
		pe_inv_counts = frappe.db.sql(
			"""
			SELECT per.reference_name, COUNT(DISTINCT per.parent) AS cnt
			FROM `tabPayment Entry Reference` per
			JOIN `tabPayment Entry` pe ON pe.name = per.parent
			WHERE per.reference_name IN %s AND pe.docstatus = 1
			GROUP BY per.reference_name
			""",
			(inv_names,), as_dict=True,
		)
		je_inv_counts = frappe.db.sql(
			"""
			SELECT jea.reference_name, COUNT(DISTINCT jea.parent) AS cnt
			FROM `tabJournal Entry Account` jea
			JOIN `tabJournal Entry` je ON je.name = jea.parent
			WHERE jea.reference_name IN %s AND je.docstatus = 1
			GROUP BY jea.reference_name
			""",
			(inv_names,), as_dict=True,
		)
		pe_inv_map = {r["reference_name"]: int(r["cnt"]) for r in pe_inv_counts}
		je_inv_map = {r["reference_name"]: int(r["cnt"]) for r in je_inv_counts}
		for inv in invoices:
			inv["linked_count"] = pe_inv_map.get(inv["name"], 0) + je_inv_map.get(inv["name"], 0)

	# Payment entries: count of reference rows on the PE
	if payment_entries:
		pe_names = tuple(p["name"] for p in payment_entries)
		pe_ref_counts = frappe.db.sql(
			"""
			SELECT parent, COUNT(*) AS cnt
			FROM `tabPayment Entry Reference`
			WHERE parent IN %s
			GROUP BY parent
			""",
			(pe_names,), as_dict=True,
		)
		pe_ref_map = {r["parent"]: int(r["cnt"]) for r in pe_ref_counts}
		for pe in payment_entries:
			pe["linked_count"] = pe_ref_map.get(pe["name"], 0)

	# Journal entries: count of submitted PEs referencing each JE
	if journal_entries:
		je_final_names = tuple(j["name"] for j in journal_entries)
		je_lnk_counts = frappe.db.sql(
			"""
			SELECT per.reference_name, COUNT(DISTINCT per.parent) AS cnt
			FROM `tabPayment Entry Reference` per
			JOIN `tabPayment Entry` pe ON pe.name = per.parent
			WHERE per.reference_doctype = 'Journal Entry'
			      AND per.reference_name IN %s AND pe.docstatus = 1
			GROUP BY per.reference_name
			""",
			(je_final_names,), as_dict=True,
		)
		je_lnk_map = {r["reference_name"]: int(r["cnt"]) for r in je_lnk_counts}
		for je in journal_entries:
			je["linked_count"] = je_lnk_map.get(je["name"], 0)

	# ── Summary ──────────────────────────────────────────────────────────────────────────────────
	inv_dr = sum(abs(float(i["outstanding_amount"])) for i in invoices if i["direction"] == "Dr")
	inv_cr = sum(abs(float(i["outstanding_amount"])) for i in invoices if i["direction"] == "Cr")
	pe_dr  = sum(float(p["unallocated_amount"]) for p in payment_entries if p["direction"] == "Dr")
	pe_cr  = sum(float(p["unallocated_amount"]) for p in payment_entries if p["direction"] == "Cr")
	je_dr  = sum(float(j["unallocated_amount"]) for j in journal_entries if j["direction"] == "Dr")
	je_cr  = sum(float(j["unallocated_amount"]) for j in journal_entries if j["direction"] == "Cr")

	total_dr = round(inv_dr + pe_dr + je_dr, 2)
	total_cr = round(inv_cr + pe_cr + je_cr, 2)

	return {
		"invoices": invoices,
		"payment_entries": [dict(r) for r in payment_entries],
		"journal_entries": journal_entries,
		"summary": {
			"total_dr": total_dr,
			"total_cr": total_cr,
			"net_outstanding": round(total_dr - total_cr, 2),
		},
	}


@frappe.whitelist()
def get_linked_documents(doctype, docname):
	"""Return all documents linked to a given outstanding document with allocated amounts."""
	result = []

	if doctype in ("Sales Invoice", "Purchase Invoice"):
		pe_rows = frappe.db.sql(
			"""
			SELECT per.parent AS name, 'Payment Entry' AS link_doctype,
			       pe.posting_date, per.allocated_amount
			FROM `tabPayment Entry Reference` per
			JOIN `tabPayment Entry` pe ON pe.name = per.parent
			WHERE per.reference_name = %s AND pe.docstatus = 1
			ORDER BY pe.posting_date DESC
			""",
			(docname,), as_dict=True,
		)
		je_rows = frappe.db.sql(
			"""
			SELECT jea.parent AS name, 'Journal Entry' AS link_doctype,
			       je.posting_date,
			       ABS(jea.credit_in_account_currency - jea.debit_in_account_currency) AS allocated_amount
			FROM `tabJournal Entry Account` jea
			JOIN `tabJournal Entry` je ON je.name = jea.parent
			WHERE jea.reference_name = %s AND je.docstatus = 1
			ORDER BY je.posting_date DESC
			""",
			(docname,), as_dict=True,
		)
		result = [dict(r) for r in pe_rows] + [dict(r) for r in je_rows]

	elif doctype == "Payment Entry":
		rows = frappe.db.sql(
			"""
			SELECT reference_name AS name, reference_doctype AS link_doctype, allocated_amount
			FROM `tabPayment Entry Reference`
			WHERE parent = %s
			ORDER BY idx
			""",
			(docname,), as_dict=True,
		)
		for r in rows:
			d = dict(r)
			if d["link_doctype"] in ("Sales Invoice", "Purchase Invoice", "Journal Entry"):
				d["posting_date"] = frappe.db.get_value(d["link_doctype"], d["name"], "posting_date") or ""
			result.append(d)

	elif doctype == "Journal Entry":
		rows = frappe.db.sql(
			"""
			SELECT per.parent AS name, 'Payment Entry' AS link_doctype,
			       pe.posting_date, per.allocated_amount
			FROM `tabPayment Entry Reference` per
			JOIN `tabPayment Entry` pe ON pe.name = per.parent
			WHERE per.reference_doctype = 'Journal Entry'
			      AND per.reference_name = %s AND pe.docstatus = 1
			ORDER BY pe.posting_date DESC
			""",
			(docname,), as_dict=True,
		)
		result = [dict(r) for r in rows]

	total_allocated = sum(float(r.get("allocated_amount") or 0) for r in result)
	return {"docs": result, "total_allocated": round(total_allocated, 2)}



