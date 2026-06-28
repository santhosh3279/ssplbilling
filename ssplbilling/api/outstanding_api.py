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

	from erpnext.accounts.party import get_party_account
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents

	party_account = get_party_account(party_type, party, company)

	if party_account:
		args = {
			"party_type": party_type,
			"party": party,
			"party_account": party_account,
			"company": company,
			"get_outstanding_invoices": True,
			"get_orders_to_be_billed": False,
		}
		ref_docs = get_outstanding_reference_documents(args, validate=True) or []
		for d in ref_docs:
			if d.voucher_type in ("Sales Invoice", "Purchase Invoice"):
				is_return = frappe.db.get_value(d.voucher_type, d.voucher_no, "is_return") or 0
				direction = "Dr"
				if d.voucher_type == "Sales Invoice":
					direction = "Cr" if is_return or d.outstanding_amount < 0 else "Dr"
				elif d.voucher_type == "Purchase Invoice":
					direction = "Dr" if is_return or d.outstanding_amount < 0 else "Cr"

				invoices.append({
					"name": d.voucher_no,
					"posting_date": str(d.posting_date),
					"grand_total": float(d.invoice_amount or 0),
					"outstanding_amount": float(d.outstanding_amount or 0),
					"is_return": int(is_return or 0),
					"direction": direction,
					"doctype": d.voucher_type
				})

	# ── 2. Unlinked Payment Entries ──────────────────────────────────────────────────────────────
	payment_entries = frappe.db.sql(
		"""
		SELECT
			name, posting_date, payment_type,
			paid_amount, unallocated_amount,
			mode_of_payment,
			IFNULL(remarks, '') AS remarks,
			CASE WHEN payment_type = 'Receive' THEN 'Cr' ELSE 'Dr' END AS direction
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		      AND party_type = %s AND party = %s
		      AND unallocated_amount > 0.005
		      AND company = %s
		ORDER BY posting_date DESC
		""",
		(party_type, party, company),
		as_dict=True,
	)

	# ── 3. Unlinked Journal Entries ──────────────────────────────────────────────────────────────
	account_types = ("Receivable", "Payable")
	je_raw = frappe.db.sql(
		"""
		SELECT
			jea.parent AS name,
			jea.account AS account,
			MAX(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN jea.name ELSE NULL END)   AS reference_row,
			MAX(je.posting_date)                    AS posting_date,
			IFNULL(MAX(je.cheque_no), '')           AS reference_no,
			IFNULL(MAX(je.user_remark), '')         AS remarks,
			MAX(je.total_debit)                     AS journal_total_debit,
			SUM(ABS(jea.credit_in_account_currency - jea.debit_in_account_currency))  AS total_amount,
			SUM(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)
			         ELSE 0 END)                    AS unallocated_amount_sql,
			CASE WHEN SUM(jea.credit_in_account_currency) > SUM(jea.debit_in_account_currency)
			     THEN 'Cr' ELSE 'Dr' END            AS direction
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je  ON je.name  = jea.parent
		JOIN `tabAccount`       acc ON acc.name = jea.account
		WHERE je.docstatus = 1
		      AND jea.party_type = %s AND jea.party = %s
		      AND acc.account_type IN %s
		      AND je.company = %s
		      AND je.is_opening != 'Yes'
		GROUP BY jea.parent, jea.account, jea.party
		ORDER BY posting_date DESC
		""",
		(party_type, party, account_types, company),
		as_dict=True,
	)

	# Accurate unallocated amount: start from Payment Ledger (if available), then also subtract
	# amounts allocated via tabPayment Entry Reference (PE rows referencing this JE directly).
	journal_entries = []
	if je_raw:
		je_names = list(set(r["name"] for r in je_raw))

		# Method 1: Payment Ledger cross-links (ERPNext v14+)
		pl_links_map = {}
		try:
			pl_links = frappe.db.sql(
				"""
				SELECT
					CASE WHEN voucher_no IN %s THEN voucher_no ELSE against_voucher_no END AS name,
					account,
					SUM(ABS(amount_in_account_currency)) AS linked_amount
				FROM `tabPayment Ledger Entry`
				WHERE (voucher_no IN %s OR against_voucher_no IN %s)
				  AND against_voucher_no != voucher_no
				  AND party = %s AND delinked = 0
				GROUP BY name, account
				""",
				(tuple(je_names), tuple(je_names), tuple(je_names), party),
				as_dict=True,
			)
			pl_links_map = {r["name"]: float(r["linked_amount"]) for r in pl_links}
		except Exception:
			pass  # tabPayment Ledger Entry absent on this install

		# Method 2: Payment Entry References pointing at these JEs (submitted PEs only)
		per_map = {}
		per_rows = frappe.db.sql(
			"""
			SELECT per.reference_name AS je_name,
			       SUM(per.allocated_amount) AS allocated
			FROM `tabPayment Entry Reference` per
			JOIN `tabPayment Entry` pe ON pe.name = per.parent
			WHERE per.reference_doctype = 'Journal Entry'
			      AND per.reference_name IN %s
			      AND pe.docstatus = 1
			GROUP BY per.reference_name
			""",
			(tuple(je_names),),
			as_dict=True,
		)
		per_map = {r["je_name"]: float(r["allocated"]) for r in per_rows}

		for je in je_raw:
			je_name = je["name"]
			sql_unalloc = float(je.get("unallocated_amount_sql") or 0)
			# Use the higher of the two allocation signals
			linked = max(pl_links_map.get(je_name, 0), per_map.get(je_name, 0))
			je["unallocated_amount"] = max(0, sql_unalloc - linked)
			if je["unallocated_amount"] > 0.005:
				journal_entries.append(dict(je))

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
