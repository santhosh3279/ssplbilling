import frappe
import json


def _get_company():
	return frappe.defaults.get_global_default("company")


def _get_party_account(party_type, party):
	from erpnext.accounts.party import get_party_account
	return get_party_account(party_type, party, _get_company())


def _get_je_row_unadjusted_amount(reference_row, party_type):
	"""Signed account-currency amount of a single Journal Entry Account row.

	ERPNext's update_reference_in_journal_entry() *overwrites* the row with
	(unadjusted_amount - allocated_amount) and appends a new row for
	allocated_amount, so unadjusted_amount must be the row's raw amount. Passing
	anything net of prior Payment Ledger links (as our unallocated_amount is)
	shrinks the row by that difference and throws "Debit and Credit not equal".
	This mirrors ERPNext's own get_jv_entries(), which selects credit - debit
	with no link subtraction.
	"""
	import erpnext

	row = frappe.db.get_value(
		"Journal Entry Account",
		reference_row,
		["parent", "debit_in_account_currency", "credit_in_account_currency"],
		as_dict=True,
	)
	if not row:
		frappe.throw(f"Journal Entry row {reference_row} not found")

	debit = float(row.debit_in_account_currency or 0)
	credit = float(row.credit_in_account_currency or 0)

	if erpnext.get_party_account_type(party_type) == "Receivable":
		amount = credit - debit
	else:
		amount = debit - credit

	# ERPNext's get_jv_entries() filters these out (dr_or_cr > 0). A row moving the
	# other way needs a negated allocated_amount that we never send, so reconciling
	# it here would silently unbalance the Journal Entry.
	if amount <= 0.005:
		frappe.throw(
			f"Journal Entry row {reference_row} of {row.parent} moves against the party account "
			f"and cannot be reconciled from this side."
		)

	return amount


def _get_je_outstanding(je_name, party_type, party, account):
	"""Open balance of a Journal Entry for one party, straight from the Payment Ledger.

	The same figure ERPNext keeps: the JE's own entries plus every entry made against it.
	A JE can move either way, so the total is read in the direction of the JE's own
	entries; zero or less means nothing is left to reconcile.
	"""
	own, total = frappe.db.sql(
		"""
		SELECT
			SUM(CASE WHEN voucher_no = %(je)s THEN amount_in_account_currency ELSE 0 END),
			SUM(amount_in_account_currency)
		FROM `tabPayment Ledger Entry`
		WHERE against_voucher_type = 'Journal Entry' AND against_voucher_no = %(je)s
			AND party_type = %(party_type)s AND party = %(party)s AND account = %(account)s
			AND delinked = 0 AND docstatus = 1
		""",
		{"je": je_name, "party_type": party_type, "party": party, "account": account},
	)[0]
	own, total = float(own or 0), float(total or 0)
	return max(0.0, total if own >= 0 else -total)


def _get_je_row_available_amount(party_type, party, reference_row):
	"""Authoritative unallocated balance of a JE row, net of existing Payment Ledger links.

	Grounding unadjusted_amount in the raw row amount removes ERPNext's own
	over-allocation guard (validate_allocation compares against `amount`), so cap
	the allocation here instead. Reuses get_unlinked_entries so the link maths
	stays in one place, and never trusts the client-supplied figure.
	"""
	entries = get_unlinked_entries(party_type, party)
	for je in entries["journal_entries"]:
		if je.get("reference_row") == reference_row:
			return float(je.get("unallocated_amount") or 0)

	frappe.throw(
		f"Journal Entry row {reference_row} is no longer unreconciled. Refresh and try again."
	)


@frappe.whitelist()
def get_parties_with_unlinked_entries(show_all=False):
	"""Return Customer/Supplier parties that have unallocated Payment Entries or
	unlinked Journal Entry rows, with count and total for the landing list."""
	company = _get_company()

	if isinstance(show_all, str):
		show_all = frappe.parse_json(show_all)
	show_all = bool(show_all)

	pe_rows = frappe.db.sql(
		"""
		SELECT party_type, party,
			CASE WHEN payment_type = 'Receive' THEN 'Cr' ELSE 'Dr' END AS direction,
			COUNT(*) AS cnt,
			SUM(unallocated_amount) AS amount
		FROM `tabPayment Entry`
		WHERE docstatus = 1
			AND party_type IN ('Customer', 'Supplier')
			AND unallocated_amount > 0.005
			AND company = %s
		GROUP BY party_type, party,
			(CASE WHEN payment_type = 'Receive' THEN 'Cr' ELSE 'Dr' END)
		""",
		(company,),
		as_dict=True,
	)

	je_entries = frappe.db.sql(
		"""
		SELECT jea.party_type, jea.party, jea.parent AS name, jea.account,
			SUM(ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)) AS total_amount,
			SUM(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)
			         ELSE 0 END) AS unallocated_amount_sql,
			CASE WHEN SUM(jea.credit_in_account_currency) > SUM(jea.debit_in_account_currency) THEN 'Cr' ELSE 'Dr' END AS direction
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je  ON je.name  = jea.parent
		JOIN `tabAccount`       acc ON acc.name = jea.account
		WHERE je.docstatus = 1
			AND jea.party_type IN ('Customer', 'Supplier')
			AND acc.account_type IN ('Receivable', 'Payable')
			AND je.company = %s
			AND je.is_opening != 'Yes'
		GROUP BY jea.parent, jea.account, jea.party_type, jea.party
		""",
		(company,),
		as_dict=True,
	)

	je_rows = []
	if je_entries:
		je_names = list(set(r["name"] for r in je_entries))
		
		# Fetch referenced names set for each JE account row to prevent double-subtracting
		# already-allocated rows' links from the unallocated rows.
		je_rows_ref = frappe.db.sql(
			"""
			SELECT parent, account, party, reference_name
			FROM `tabJournal Entry Account`
			WHERE parent IN %s
				AND reference_name IS NOT NULL
				AND reference_name != ''
			""",
			(tuple(je_names),),
			as_dict=True,
		)
		ref_map = {}
		for r in je_rows_ref:
			k = (r["parent"], r["account"], r["party"])
			if k not in ref_map:
				ref_map[k] = set()
			ref_map[k].add(r["reference_name"])

		pl_links = frappe.db.sql(
			"""
			SELECT 
				-- A link consumes the document it is made AGAINST. Check that side first: a
				-- reconciliation JE is itself one of these JEs, and attributing its link to it
				-- (instead of the JE it adjusts) left that JE looking unreconciled forever.
				CASE WHEN against_voucher_no IN %s THEN against_voucher_no ELSE voucher_no END as name,
				account,
				party,
				voucher_no,
				against_voucher_no,
				amount_in_account_currency
			FROM `tabPayment Ledger Entry`
			WHERE (voucher_no IN %s OR against_voucher_no IN %s)
			  AND against_voucher_no != voucher_no
			  AND delinked = 0
			""",
			(tuple(je_names), tuple(je_names), tuple(je_names)),
			as_dict=True,
		)

		links_map = {}
		for r in pl_links:
			je_name = r["name"]
			acc = r["account"]
			pty = r["party"]
			k = (je_name, acc, pty)
			linked_doc = r["against_voucher_no"] if r["voucher_no"] == je_name else r["voucher_no"]
			if k in ref_map and linked_doc in ref_map[k]:
				continue
			links_map[k] = links_map.get(k, 0.0) + abs(float(r["amount_in_account_currency"] or 0.0))

		grouped_je = {}
		for je in je_entries:
			linked = links_map.get((je["name"], je["account"], je["party"]), 0.0)
			sql_unalloc = float(je.get("unallocated_amount_sql") or 0.0)
			unallocated = max(0.0, sql_unalloc - linked)
			if unallocated > 0.005:
				key = (je["party_type"], je["party"], je["direction"])
				if key not in grouped_je:
					grouped_je[key] = frappe._dict({
						"party_type": je["party_type"],
						"party": je["party"],
						"direction": je["direction"],
						"cnt": 0,
						"amount": 0.0
					})
				grouped_je[key]["cnt"] += 1
				grouped_je[key]["amount"] += unallocated
		je_rows = list(grouped_je.values())

	# Return invoices (credit/debit notes) carry negative outstanding — they are
	# credits waiting to be linked, same as an unallocated payment.
	ret_rows = frappe.db.sql(
		"""
		SELECT 'Customer' AS party_type, customer AS party, 'Cr' AS direction,
			COUNT(*) AS cnt, SUM(ABS(outstanding_amount)) AS amount
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND outstanding_amount < -0.005 AND company = %s
		GROUP BY customer
		UNION ALL
		SELECT 'Supplier' AS party_type, supplier AS party, 'Dr' AS direction,
			COUNT(*) AS cnt, SUM(ABS(outstanding_amount)) AS amount
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND outstanding_amount < -0.005 AND company = %s
		GROUP BY supplier
		""",
		(company, company),
		as_dict=True,
	)

	# Outstanding invoices (outstanding_amount > 0.005)
	outstanding_rows = frappe.db.sql(
		"""
		SELECT 'Customer' AS party_type, customer AS party, 'Dr' AS direction,
			COUNT(*) AS cnt, SUM(outstanding_amount) AS amount
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND outstanding_amount > 0.005 AND company = %s
		GROUP BY customer
		UNION ALL
		SELECT 'Supplier' AS party_type, supplier AS party, 'Cr' AS direction,
			COUNT(*) AS cnt, SUM(outstanding_amount) AS amount
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 AND outstanding_amount > 0.005 AND company = %s
		GROUP BY supplier
		""",
		(company, company),
		as_dict=True,
	)

	combined = {}
	# Group all entries by party and accumulate Cr vs Dr counts & amounts
	all_rows = list(pe_rows) + list(je_rows) + list(ret_rows) + list(outstanding_rows)
	for r in all_rows:
		key = (r.party_type, r.party)
		if key not in combined:
			combined[key] = {
				"party_type": r.party_type,
				"party": r.party,
				"cr_count": 0,
				"cr_amount": 0.0,
				"dr_count": 0,
				"dr_amount": 0.0,
			}
		if r.direction == "Cr":
			combined[key]["cr_count"] += int(r.cnt or 0)
			combined[key]["cr_amount"] += float(r.amount or 0)
		else:
			combined[key]["dr_count"] += int(r.cnt or 0)
			combined[key]["dr_amount"] += float(r.amount or 0)

	# If show_all is False, filter to only keep parties that have both unlinked Cr AND unlinked Dr
	if not show_all:
		combined = {k: v for k, v in combined.items() if v["cr_count"] > 0 and v["dr_count"] > 0}

	# Resolve display labels in bulk
	labels = {}
	customers = [k[1] for k in combined if k[0] == "Customer"]
	suppliers = [k[1] for k in combined if k[0] == "Supplier"]
	if customers:
		for d in frappe.get_all("Customer", filters={"name": ["in", customers]}, fields=["name", "customer_name"]):
			labels[("Customer", d.name)] = d.customer_name or d.name
	if suppliers:
		for d in frappe.get_all("Supplier", filters={"name": ["in", suppliers]}, fields=["name", "supplier_name"]):
			labels[("Supplier", d.name)] = d.supplier_name or d.name

	result = list(combined.values())
	for key, row in combined.items():
		row["label"] = labels.get(key, row["party"])
		# Map cr/dr back to unlinked/outstanding for frontend compatibility
		if row["party_type"] == "Customer":
			row["unlinked_count"] = row["cr_count"]
			row["unlinked_amount"] = row["cr_amount"]
			row["outstanding_count"] = row["dr_count"]
			row["outstanding_amount"] = row["dr_amount"]
		else:
			row["unlinked_count"] = row["dr_count"]
			row["unlinked_amount"] = row["dr_amount"]
			row["outstanding_count"] = row["cr_count"]
			row["outstanding_amount"] = row["cr_amount"]

		# Compatibility and sorting fields
		row["count"] = row["unlinked_count"] if row["unlinked_count"] > 0 else row["outstanding_count"]
		row["amount"] = row["unlinked_amount"] if row["unlinked_amount"] > 0 else row["outstanding_amount"]

	result.sort(key=lambda r: r["amount"], reverse=True)
	return result


@frappe.whitelist()
def get_unlinked_entries(party_type, party):
	"""Return unallocated Payment Entries and Journal Entry rows for a party."""
	company = _get_company()
	
	# Fetch from both Receivable and Payable if it's a Customer/Supplier
	# as they might have both types of entries.
	account_types = ["Receivable", "Payable"]
	

	payment_entries = frappe.db.sql(
		"""
		SELECT
			name, posting_date, payment_type,
			paid_amount, unallocated_amount,
			mode_of_payment,
			IFNULL(remarks, '') AS remarks,
			IFNULL(reference_no, '') AS reference_no,
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

	je_entries = frappe.db.sql(
		"""
		SELECT
			jea.parent                                                        AS name,
			jea.account                                                       AS account,
			MAX(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN jea.name ELSE NULL END)                             AS reference_row,
			MAX(je.posting_date)                                              AS posting_date,
			IFNULL(MAX(je.cheque_no), '')                                     AS reference_no,
			IFNULL(MAX(je.user_remark), '')                                   AS remarks,
			MAX(je.total_debit)                                               AS journal_total_debit,
			SUM(ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)) AS total_amount,
			SUM(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)
			         ELSE 0 END)                                              AS unallocated_amount_sql,
			CASE WHEN SUM(jea.credit_in_account_currency) > SUM(jea.debit_in_account_currency)
			     THEN 'Cr' ELSE 'Dr' END                                      AS direction
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry`  je  ON je.name  = jea.parent
		JOIN `tabAccount`        acc ON acc.name = jea.account
		WHERE je.docstatus = 1
			AND jea.party_type = %s AND jea.party = %s
			AND acc.account_type IN %s
			AND je.company = %s
			AND je.is_opening != 'Yes'
		GROUP BY jea.parent, jea.account, jea.party
		ORDER BY posting_date DESC
		""",
		(party_type, party, tuple(account_types), company),
		as_dict=True,
	)

	# Accurate unallocated_amount calculation via Payment Ledger
	if je_entries:
		je_names = list(set(r["name"] for r in je_entries))
		
		# Fetch referenced names set for each JE account row to prevent double-subtracting
		# already-allocated rows' links from the unallocated rows.
		je_rows_ref = frappe.db.sql(
			"""
			SELECT parent, account, party, reference_name
			FROM `tabJournal Entry Account`
			WHERE parent IN %s
				AND reference_name IS NOT NULL
				AND reference_name != ''
			""",
			(tuple(je_names),),
			as_dict=True,
		)
		ref_map = {}
		for r in je_rows_ref:
			k = (r["parent"], r["account"], r["party"])
			if k not in ref_map:
				ref_map[k] = set()
			ref_map[k].add(r["reference_name"])

		# Sum of all reconciled amounts for these JEs, this party, and these specific accounts.
		pl_links = frappe.db.sql(
			"""
			SELECT 
				-- A link consumes the document it is made AGAINST. Check that side first: a
				-- reconciliation JE is itself one of these JEs, and attributing its link to it
				-- (instead of the JE it adjusts) left that JE looking unreconciled forever.
				CASE WHEN against_voucher_no IN %s THEN against_voucher_no ELSE voucher_no END as name,
				account,
				party,
				voucher_no,
				against_voucher_no,
				amount_in_account_currency
			FROM `tabPayment Ledger Entry`
			WHERE (voucher_no IN %s OR against_voucher_no IN %s)
			  AND against_voucher_no != voucher_no
			  AND party = %s AND delinked = 0
			""",
			(tuple(je_names), tuple(je_names), tuple(je_names), party),
			as_dict=True,
		)

		links_map = {}
		for r in pl_links:
			je_name = r["name"]
			acc = r["account"]
			pty = r["party"]
			k = (je_name, acc, pty)
			linked_doc = r["against_voucher_no"] if r["voucher_no"] == je_name else r["voucher_no"]
			if k in ref_map and linked_doc in ref_map[k]:
				continue
			links_map[(je_name, acc)] = links_map.get((je_name, acc), 0.0) + abs(float(r["amount_in_account_currency"] or 0.0))
		
		processed_jes = []
		for je in je_entries:
			linked = links_map.get((je["name"], je["account"]), 0)
			# Re-calculate unallocated_amount: Total party-specific amount minus PL links
			# We also respect the SQL-level unallocated (rows with reference_name are already allocated)
			sql_unalloc = float(je.get("unallocated_amount_sql") or 0)
			je["unallocated_amount"] = max(0, sql_unalloc - linked)
			
			if je["unallocated_amount"] > 0.005:
				processed_jes.append(dict(je))
		je_entries = processed_jes


	return {
		"payment_entries": [dict(r) for r in payment_entries],
		"journal_entries": [dict(r) for r in je_entries],
	}


@frappe.whitelist()
def get_outstanding_docs(party_type, party):
	"""Return submitted invoices with outstanding balance for a party.

	Filters strictly by party_type so Customer and Supplier ledgers for the
	same name never bleed into each other's reference lists.
	"""
	company = _get_company()
	all_docs = []

	if party_type != "Supplier":
		# Sales Invoices — Customer side
		si_docs = frappe.db.sql(
			"""
			SELECT name, posting_date, grand_total, outstanding_amount,
			       customer_name AS party_name, is_return, return_against, 'Sales Invoice' as doctype
			FROM `tabSales Invoice`
			WHERE docstatus = 1 AND customer = %s
			      AND ABS(outstanding_amount) > 0.005 AND company = %s
			ORDER BY posting_date ASC
			""",
			(party, company),
			as_dict=True,
		)
		for d in si_docs:
			d["direction"] = "Cr" if d.get("is_return") or d.get("outstanding_amount", 0) < 0 else "Dr"
			all_docs.append(dict(d))

	if party_type != "Customer":
		# Purchase Invoices — Supplier side
		pi_docs = frappe.db.sql(
			"""
			SELECT name, posting_date, grand_total, outstanding_amount,
			       supplier_name AS party_name, is_return, return_against, 'Purchase Invoice' as doctype
			FROM `tabPurchase Invoice`
			WHERE docstatus = 1 AND supplier = %s
			      AND ABS(outstanding_amount) > 0.005 AND company = %s
			ORDER BY posting_date ASC
			""",
			(party, company),
			as_dict=True,
		)
		for d in pi_docs:
			d["direction"] = "Dr" if d.get("is_return") or d.get("outstanding_amount", 0) < 0 else "Cr"
			all_docs.append(dict(d))

	return {"doc_type": "Invoice", "docs": all_docs}


@frappe.whitelist()
def get_unlinked_opposite_entries(party_type, party):
	"""Return unlinked entries that move in the OPPOSITE direction to get_unlinked_entries.

	For Customer: Payment Entries of type 'Pay' (refunds out) + JE debit rows on Receivable.
	For Supplier: Payment Entries of type 'Receive' (money back from supplier) + JE credit rows on Payable.
	These can be cross-reconciled against the unlinked receipts from get_unlinked_entries.
	"""
	company = _get_company()
	account_type = "Receivable" if party_type == "Customer" else "Payable"
	opposite_payment_type = "Pay" if party_type == "Customer" else "Receive"

	payment_entries = frappe.db.sql(
		"""
		SELECT name, posting_date, payment_type,
		       paid_amount, unallocated_amount,
		       mode_of_payment, IFNULL(remarks, '') AS remarks
		FROM `tabPayment Entry`
		WHERE docstatus = 1
		      AND party_type = %s AND party = %s
		      AND payment_type = %s
		      AND unallocated_amount > 0.005
		      AND company = %s
		ORDER BY posting_date DESC
		""",
		(party_type, party, opposite_payment_type, company),
		as_dict=True,
	)

	# JE rows where the party account moves the opposite way (debit for Customer, credit for Supplier)
	je_col = "debit_in_account_currency" if party_type == "Customer" else "credit_in_account_currency"
	je_opp = "credit_in_account_currency" if party_type == "Customer" else "debit_in_account_currency"
	je_entries = frappe.db.sql(
		f"""
		SELECT jea.parent AS name,
		       jea.name   AS reference_row,
		       je.posting_date,
		       IFNULL(je.cheque_no, '')     AS reference_no,
		       IFNULL(je.user_remark, '')   AS remarks,
		       (jea.{je_col} - jea.{je_opp}) AS unallocated_amount
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je  ON je.name  = jea.parent
		JOIN `tabAccount`       acc ON acc.name = jea.account
		WHERE je.docstatus = 1
		      AND jea.party_type = %s AND jea.party = %s
		      AND jea.{je_col} > jea.{je_opp}
		      AND (jea.reference_name IS NULL OR jea.reference_name = '')
		      AND acc.account_type = %s
		      AND je.company = %s
		      AND je.is_opening != 'Yes'
		ORDER BY je.posting_date DESC
		""",
		(party_type, party, account_type, company),
		as_dict=True,
	)

	return {
		"payment_entries": [dict(r) for r in payment_entries],
		"journal_entries": [dict(r) for r in je_entries],
	}


@frappe.whitelist()
def post_cross_reconciliation(party_type, party, allocations):
	"""Cross-reconcile a floating receipt against a floating payment (or vice versa)
	by using the Payment Reconciliation tool to link their GL Entries.
	"""
	if isinstance(allocations, str):
		allocations = json.loads(allocations)

	if not allocations:
		frappe.throw("No allocations provided")

	# Re-map cross-allocations to match post_reconciliation structure
	# left (receipt/credit) -> payment side
	# right (payment/debit) -> invoice side
	mapped_allocs = []
	for a in allocations:
		mapped_allocs.append({
			"payment_type": a["left_type"],
			"payment_name": a["left_name"],
			"reference_row": a["left_row"],
			"invoice_type": a["right_type"],
			"invoice_name": a["right_name"],
			"right_row": a.get("right_row"), # Row on the "invoice" side
			"amount": a["amount"],
			"unreconciled_amount": a.get("unreconciled_amount")
		})

	return post_reconciliation(party_type, party, mapped_allocs)


@frappe.whitelist()
def post_reconciliation(party_type, party, allocations, company=None):
	"""Reconcile unlinked payments / JEs against outstanding invoices / opposite entries.

	Each item in `allocations`:
	  payment_type        – "Payment Entry" | "Journal Entry"
	  payment_name        – name of the PE or JE
	  reference_row       – name of the JE account row (only for JE)
	  invoice_type        – doc type of the Debit side (Sales Invoice, PE, JE etc.)
	  invoice_name        – name of the Debit side document
	  amount              – amount to allocate
	  unreconciled_amount – available unreconciled balance of the payment row
	"""
	if isinstance(allocations, str):
		allocations = json.loads(allocations)

	if not allocations:
		frappe.throw("No allocations provided")

	# Normalize allocations: ERPNext's Payment Reconciliation tool requires that 
	# Payment Entry is always the "reference" (payment) and Journal Entry or Invoice is the "invoice_number" (outstanding).
	# If we received a JE on the payment side and a PE on the invoice side, we must swap them.
	normalized_allocations = []
	for alloc in allocations:
		p_type = alloc.get("payment_type")
		p_name = alloc.get("payment_name")
		ref_row = alloc.get("reference_row")
		
		i_type = alloc.get("invoice_type")
		i_name = alloc.get("invoice_name")
		
		if i_type == "Payment Entry" and p_type == "Journal Entry":
			pe_unallocated = frappe.db.get_value("Payment Entry", i_name, "unallocated_amount") or 0.0
			normalized_allocations.append({
				"payment_type": i_type,
				"payment_name": i_name,
				"reference_row": None,
				"invoice_type": p_type,
				"invoice_name": p_name,
				"right_row": ref_row,
				"amount": alloc["amount"],
				"unreconciled_amount": float(pe_unallocated)
			})
		elif p_type == "Payment Entry":
			pe_unallocated = frappe.db.get_value("Payment Entry", p_name, "unallocated_amount") or 0.0
			alloc["unreconciled_amount"] = float(pe_unallocated)
			alloc["reference_row"] = None
			normalized_allocations.append(alloc)
		else:
			normalized_allocations.append(alloc)
	allocations = normalized_allocations

	# Callers that know the bill's company pass it; otherwise fall back to the default company.
	from erpnext.accounts.party import get_party_account

	company = company or _get_company()
	account = get_party_account(party_type, party, company)

	rec = frappe.new_doc("Payment Reconciliation")
	rec.party_type = party_type
	rec.party = party
	rec.company = company
	rec.receivable_payable_account = account

	# 1. Populate the invoices child table. 
	# Payment Reconciliation validation checks this table to ensure outstanding balance.
	seen_invoices = {}
	opposite_entries = None
	for alloc in allocations:
		inv_name = alloc["invoice_name"]
		inv_type = alloc["invoice_type"]
		
		# For "invoice" side, we identify unique docs but also need unique rows for JEs
		# BUT standard Payment Reconciliation only tracks unique document names in 'invoices' table.
		# However, if we have multiple rows from same JE, we must sum them up for the tool's validation?
		# No, the tool validates 'outstanding_amount' per invoice name.
		
		if inv_name not in seen_invoices:
			if inv_type in ["Sales Invoice", "Purchase Invoice"]:
				outstanding = frappe.db.get_value(inv_type, inv_name, "outstanding_amount") or 0
			else:
				# It's a Payment Entry or Journal Entry (cross-reconciliation)
				# Pull its unallocated amount from opposite entries API logic
				if opposite_entries is None:
					opposite_entries = get_unlinked_opposite_entries(party_type, party)
				
				# Find unallocated amount for THIS document (sum of all unallocated rows in it)
				doc_rows = [x for x in opposite_entries["payment_entries"] + opposite_entries["journal_entries"] if x["name"] == inv_name]
				outstanding = sum([float(x["unallocated_amount"]) for x in doc_rows]) if doc_rows else alloc["amount"]
				if inv_type == "Journal Entry":
					# The opposite-entries query ignores links already made against the JE, so
					# a JE reconciled before still looked fully open and every click posted
					# another reconciliation JE for the same amount. Cap by the Payment Ledger.
					outstanding = min(outstanding, _get_je_outstanding(inv_name, party_type, party, account))
					if outstanding <= 0.005:
						frappe.throw(
							f"Journal Entry {inv_name} is already fully reconciled for {party}. Refresh and try again."
						)

			seen_invoices[inv_name] = float(outstanding)
			rec.append("invoices", {
				"invoice_type": inv_type,
				"invoice_number": inv_name,
				"outstanding_amount": float(outstanding),
			})

	# The bill side may not take more than it has open, summed over every allocation to it
	allocated_to = {}
	for alloc in allocations:
		allocated_to[alloc["invoice_name"]] = allocated_to.get(alloc["invoice_name"], 0.0) + float(alloc["amount"])
	for inv_name, total in allocated_to.items():
		open_amount = abs(seen_invoices.get(inv_name, 0.0))
		if total - open_amount > 0.009:
			frappe.throw(f"Allocated amount {total} exceeds the open balance {open_amount} of {inv_name}.")

	# 2. Build allocation rows.
	# ERPNext rewrites a JE row to (unadjusted - allocated) once per allocation, on
	# the same in-memory document, so a row split across several bills must pass
	# what is left of it each time, not the raw amount again.
	je_row_used = {}
	je_row_available = {}
	for alloc in allocations:
		allocated = float(alloc["amount"])
		unreconciled = float(alloc.get("unreconciled_amount") or alloc["amount"])
		ref_row = alloc.get("reference_row") or None

		if alloc["payment_type"] == "Journal Entry" and ref_row:
			# unadjusted_amount must be the JE row's raw amount, not its unallocated
			# balance, or ERPNext rewrites the row short and unbalances the entry.
			used = je_row_used.get(ref_row, 0.0)
			unadjusted = _get_je_row_unadjusted_amount(ref_row, party_type) - used
			if ref_row not in je_row_available:
				je_row_available[ref_row] = _get_je_row_available_amount(party_type, party, ref_row)
			available = je_row_available[ref_row] - used
			je_row_used[ref_row] = used + allocated
			if allocated - available > 0.009:
				frappe.throw(
					f"Allocated amount {allocated} exceeds the unreconciled balance {available} "
					f"of Journal Entry {alloc['payment_name']}."
				)
			unreconciled = available
		else:
			unadjusted = unreconciled

		rec.append(
			"allocation",
			{
				"reference_type": alloc["payment_type"],
				"reference_name": alloc["payment_name"],
				"reference_row": ref_row,
				"invoice_type": alloc["invoice_type"],
				"invoice_number": alloc["invoice_name"],     # ERPNext field name
				"allocated_amount": allocated,
				"amount": unadjusted,                        # ERPNext reads this as unadjusted_amount
				"unreconciled_amount": unreconciled,
			},
		)

	rec.reconcile()
	return {"status": "ok", "reconciled": len(allocations)}


# ── Auto reconciliation ───────────────────────────────────────────────────────
# Each ledger is matched in stages, most certain first, and every stage only
# uses what the earlier stages left over:
#   return       – credit / debit note against the invoice it was returned against
#   reference    – a bill number in the remarks / reference no of either entry
#                  (short forms like "ERE282" for ERE00282 count)
#   exact        – one payment and one outstanding entry of the same amount,
#                  same-day pairs first
#   combo        – one payment equal to the sum of two or three outstanding entries
#   oldest_first – whatever is left, oldest payment to oldest bill, partial allowed
# Oldest-first is a guess, so the all-ledgers run keeps it only for ledgers whose
# GL balance is zero; the per-ledger Auto Allocate shows it in the queue for review.
# The preview is what the Proceed / Apply buttons post back.
# Payment Entries count only what the Payment Ledger still has open: refunds that
# Credit Note JEs already used are skipped, and over-used ones are listed as warnings.

AUTO_MATCH_TOLERANCE = 0.01
COMBO_POOL = 20  # outstanding entries considered per payment for combo matches
MATCH_ORDER = ("return", "reference", "exact", "combo", "oldest_first")


def _build_reconcile_sides(party_type, party):
	"""Payment-side and outstanding-side rows for a party.

	Mirrors the split unreconciled.vue does after fetching: rows moving in the
	party's payment direction (Cr for Customer, Dr for Supplier) are payments,
	opposite-direction PE/JE rows are outstanding, and return invoices carry a
	negative outstanding so they sit on the payment side.
	"""
	unlinked = get_unlinked_entries(party_type, party)
	outstanding = get_outstanding_docs(party_type, party)

	pay_dir = "Cr" if party_type == "Customer" else "Dr"
	payments, invoices = [], []

	rows = [dict(r, doctype="Payment Entry") for r in unlinked.get("payment_entries") or []]
	rows += [dict(r, doctype="Journal Entry") for r in unlinked.get("journal_entries") or []]
	pe_open = _payment_entry_open_amounts(
		party_type, party, [r["name"] for r in rows if r["doctype"] == "Payment Entry"]
	)

	for row in rows:
		unallocated = float(row.get("unallocated_amount") or 0)
		amount = unallocated
		if row["doctype"] == "Payment Entry" and row["name"] in pe_open:
			# Credit Note JEs that point at a refund PE consume it in the Payment
			# Ledger without touching unallocated_amount, so only the ledger's open
			# balance is really free to allocate.
			amount = min(amount, pe_open[row["name"]])
		if amount <= AUTO_MATCH_TOLERANCE:
			continue
		entry = {
			"doctype": row["doctype"],
			"name": row["name"],
			"reference_row": row.get("reference_row") or None,
			"posting_date": str(row.get("posting_date") or ""),
			"amount": amount,
			# Payment Reconciliation checks this against the PE's own unallocated amount
			"unreconciled_amount": unallocated,
			"remarks": row.get("remarks") or "",
			"reference_no": row.get("reference_no") or "",
		}
		if (row.get("direction") or pay_dir) == pay_dir:
			payments.append(entry)
		else:
			invoices.append(entry)

	for doc in outstanding.get("docs") or []:
		amount = float(doc.get("outstanding_amount") or 0)
		if abs(amount) <= AUTO_MATCH_TOLERANCE:
			continue
		entry = {
			"doctype": doc["doctype"],
			"name": doc["name"],
			"reference_row": None,
			"posting_date": str(doc.get("posting_date") or ""),
			"amount": abs(amount),
		}
		if amount > 0:
			invoices.append(entry)
		else:
			# Return invoices (credit / debit notes) are credits waiting to be linked;
			# Payment Reconciliation posts them through a Credit / Debit Note JE.
			entry["return_against"] = doc.get("return_against") or ""
			payments.append(entry)

	return payments, invoices


def _payment_entry_open_amounts(party_type, party, names):
	"""Open Payment Ledger balance of each Payment Entry, as a positive amount in its own direction.

	A PE used up by more JEs than it covers comes out zero or negative here.
	"""
	if not names:
		return {}
	rows = frappe.db.sql(
		"""SELECT against_voucher_no AS name, SUM(amount_in_account_currency) AS open_amount
		FROM `tabPayment Ledger Entry`
		WHERE company = %s AND party_type = %s AND party = %s AND delinked = 0
			AND against_voucher_type = 'Payment Entry' AND against_voucher_no IN %s
		GROUP BY against_voucher_no""",
		(_get_company(), party_type, party, tuple(names)), as_dict=True,
	)
	types = dict(
		frappe.db.get_all("Payment Entry", {"name": ["in", names]}, ["name", "payment_type"], as_list=True)
	)
	# Receive PEs post negative ledger amounts, Pay PEs positive
	return {
		r.name: float(r.open_amount or 0) * (-1 if types.get(r.name) == "Receive" else 1)
		for r in rows
	}


def _overused_payment_entries(party_type, party):
	"""Payment Entries whose Payment Ledger links exceed the PE itself (one refund used twice)."""
	names = frappe.db.get_all(
		"Payment Entry",
		{"company": _get_company(), "party_type": party_type, "party": party, "docstatus": 1},
		pluck="name",
	)
	return [
		{"name": name, "excess": round(-amount, 2)}
		for name, amount in _payment_entry_open_amounts(party_type, party, names).items()
		if amount < -AUTO_MATCH_TOLERANCE
	]


def _ledger_is_zero(party_type, party):
	"""Require one party account, matching the account used for reconciliation."""
	rows = frappe.db.sql(
		"""SELECT account, SUM(debit_in_account_currency - credit_in_account_currency) AS balance
		FROM `tabGL Entry`
		WHERE company = %s AND party_type = %s AND party = %s AND is_cancelled = 0
		GROUP BY account""",
		(_get_company(), party_type, party), as_dict=True,
	)
	return (
		len(rows) == 1
		and rows[0].account == _get_party_account(party_type, party)
		and abs(float(rows[0].balance or 0)) < 0.005
	)


def _paise(amount):
	from decimal import Decimal, ROUND_HALF_UP

	return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _mentions(text, name):
	"""True when `name` appears in `text` as a whole token (SINV-1 does not match SINV-12).

	Counter staff write bill numbers short, so "ERE282" or "ER282" also matches
	ERE00282, and "RTN7096" matches RTN07096/: same number, letters a prefix of the
	series, leading zeros and a trailing "/" or "-1" ignored.
	"""
	import re

	if len(name) < 5 or not text:
		return False
	if re.search(r"(?<![A-Z0-9])" + re.escape(name.upper()) + r"(?![A-Z0-9])", text):
		return True
	bill = re.fullmatch(r"([A-Z]{2,})0*(\d+)(?:[/-].*)?", name.upper())
	if not bill:
		return False
	series, number = bill.groups()
	for letters, digits in re.findall(r"(?<![A-Z0-9])([A-Z]{2,})0*(\d+)(?![0-9])", text):
		if digits == number and series.startswith(letters):
			return True
	return False


def _plan_allocations(payments, invoices):
	"""Allocate payments to outstanding entries in stages; returns (pay, inv, amount, match_type).

	Works in integer paise so partial allocations never drift. Input rows are not
	modified, and a document is never allocated against itself.
	"""
	from itertools import combinations

	order = lambda row: (row["posting_date"], row["name"], row.get("reference_row") or "")
	pays = [{"row": r, "left": _paise(r["amount"])} for r in sorted(payments, key=order)]
	invs = [{"row": r, "left": _paise(r["amount"])} for r in sorted(invoices, key=order)]
	pays = [p for p in pays if p["left"] > 0]
	invs = [i for i in invs if i["left"] > 0]
	plan = []

	def same_doc(p, i):
		return (p["row"]["doctype"], p["row"]["name"]) == (i["row"]["doctype"], i["row"]["name"])

	def take(p, i, amount, kind):
		plan.append((p["row"], i["row"], amount / 100, kind))
		p["left"] -= amount
		i["left"] -= amount

	# 1. Credit / debit note against the invoice it returns
	for p in pays:
		against = p["row"].get("return_against")
		if not against:
			continue
		for i in invs:
			if i["left"] and i["row"]["doctype"] == p["row"]["doctype"] and i["row"]["name"] == against:
				take(p, i, min(p["left"], i["left"]), "return")
				break

	# 2. Bill number written on either side: the payment's remarks naming the bill,
	#    or a refund's remarks naming the return it pays out ("ERE282")
	def text_of(row):
		return f"{row.get('remarks') or ''} {row.get('reference_no') or ''}".upper()

	for p in pays:
		if not p["left"]:
			continue
		p_text = text_of(p["row"])
		for i in invs:
			if not p["left"]:
				break
			if not i["left"] or same_doc(p, i):
				continue
			if _mentions(p_text, i["row"]["name"]) or _mentions(text_of(i["row"]), p["row"]["name"]):
				take(p, i, min(p["left"], i["left"]), "reference")

	# 3. Equal amounts, one to one; same-day pairs first (a return and its refund
	#    are posted together), then oldest first
	for same_day in (True, False):
		for p in pays:
			if not p["left"]:
				continue
			for i in invs:
				if (
					i["left"] == p["left"]
					and not same_doc(p, i)
					and (not same_day or i["row"]["posting_date"] == p["row"]["posting_date"])
				):
					take(p, i, p["left"], "exact")
					break

	# 4. One payment covering two or three whole bills
	for p in pays:
		if not p["left"]:
			continue
		pool = [i for i in invs if 0 < i["left"] < p["left"] and not same_doc(p, i)][:COMBO_POOL]
		match = next(
			(combo for size in (2, 3) for combo in combinations(pool, size)
			 if sum(i["left"] for i in combo) == p["left"]),
			None,
		)
		for i in match or ():
			take(p, i, i["left"], "combo")

	# 5. Everything left, oldest payment to oldest bill
	for p in pays:
		for i in invs:
			if not p["left"]:
				break
			if i["left"] and not same_doc(p, i):
				take(p, i, min(p["left"], i["left"]), "oldest_first")

	return plan


@frappe.whitelist()
def preview_auto_reconcile(party_type=None, party=None):
	"""Staged allocations for the confirmation dialog (every ledger, or just one).

	With no party given (the all-ledgers run, posted without row-by-row review),
	oldest-first rows are kept only for ledgers whose GL balance is zero.
	"""
	single = bool(party_type and party)
	if single:
		parties = [{"party_type": party_type, "party": party, "label": party}]
	else:
		parties = get_parties_with_unlinked_entries()

	proposals = []
	skipped = []
	warnings = []
	for row in parties:
		try:
			payments, invoices = _build_reconcile_sides(row["party_type"], row["party"])
			plan = _plan_allocations(payments, invoices)
			guesses = any(kind == "oldest_first" for *_, kind in plan)
			if not single and guesses and not _ledger_is_zero(row["party_type"], row["party"]):
				plan = [step for step in plan if step[3] != "oldest_first"]
			for pe in _overused_payment_entries(row["party_type"], row["party"]):
				warnings.append(
					{
						"party": row.get("label") or row["party"],
						"name": pe["name"],
						"excess": pe["excess"],
					}
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Auto reconcile preview failed")
			skipped.append({"party": row.get("label") or row["party"], "reason": "Could not read entries"})
			continue

		for pay, inv, amount, kind in plan:
			proposals.append(
				{
					"party_type": row["party_type"],
					"party": row["party"],
					"label": row.get("label") or row["party"],
					"payment_type": pay["doctype"],
					"payment_name": pay["name"],
					"reference_row": pay["reference_row"],
					"payment_date": pay["posting_date"],
					"invoice_type": inv["doctype"],
					"invoice_name": inv["name"],
					"invoice_date": inv["posting_date"],
					"amount": round(amount, 2),
					"match_type": kind,
					"unreconciled_amount": pay.get("unreconciled_amount", pay["amount"]),
				}
			)

	# Ledgers stay together; inside one, the most certain matches come first
	rank = {kind: n for n, kind in enumerate(MATCH_ORDER)}
	proposals.sort(key=lambda p: (p["label"], p["party"], rank[p["match_type"]]))
	return {
		"proposals": proposals,
		"total_amount": round(sum(p["amount"] for p in proposals), 2),
		"party_count": len({(p["party_type"], p["party"]) for p in proposals}),
		"skipped": skipped,
		"warnings": warnings,
	}


def _check_plan_still_valid(party_type, party, rows):
	"""Throw if the ledger changed since the preview so any row would over-allocate."""
	payments, invoices = _build_reconcile_sides(party_type, party)
	available = {}
	for r in payments:
		available[("pay", r["doctype"], r["name"], r.get("reference_row") or None)] = _paise(r["amount"])
	for r in invoices:
		key = ("inv", r["doctype"], r["name"])
		available[key] = available.get(key, 0) + _paise(r["amount"])

	wanted = {}
	for r in rows:
		for key in (
			("pay", r["payment_type"], r["payment_name"], r.get("reference_row") or None),
			("inv", r["invoice_type"], r["invoice_name"]),
		):
			wanted[key] = wanted.get(key, 0) + _paise(r["amount"])

	for key, amount in wanted.items():
		if amount - available.get(key, 0) > 1:
			frappe.throw(
				f"{key[2]} changed since the preview. Refresh the auto reconcile preview and try again."
			)


@frappe.whitelist()
def run_auto_reconcile(allocations):
	"""Post the previewed matches, one Payment Reconciliation run per ledger.

	A ledger that fails is reported and the rest still go through, so one bad
	entry cannot block every other match in the batch.
	"""
	if isinstance(allocations, str):
		allocations = json.loads(allocations)
	if not allocations:
		frappe.throw("No allocations provided")

	grouped = {}
	for alloc in allocations:
		grouped.setdefault((alloc["party_type"], alloc["party"]), []).append(alloc)

	reconciled = 0
	failures = []
	for (p_type, p_name), rows in grouped.items():
		payload = [
			{
				"payment_type": r["payment_type"],
				"payment_name": r["payment_name"],
				"reference_row": r.get("reference_row"),
				"invoice_type": r["invoice_type"],
				"invoice_name": r["invoice_name"],
				"amount": float(r["amount"]),
				"unreconciled_amount": float(r.get("unreconciled_amount") or r["amount"]),
			}
			for r in rows
		]
		savepoint = "auto_reconcile"
		frappe.db.savepoint(savepoint)
		try:
			guesses = any(r.get("match_type") == "oldest_first" for r in rows)
			if guesses and not _ledger_is_zero(p_type, p_name):
				frappe.throw("Ledger balance changed since preview. Refresh the auto reconcile preview and try again.")
			_check_plan_still_valid(p_type, p_name, rows)
			post_reconciliation(p_type, p_name, payload)
			reconciled += len(payload)
		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(frappe.get_traceback(), "Auto reconcile failed")
			label = rows[0].get("label") or p_name
			failures.append({"party": label, "error": str(e)})

	return {
		"status": "ok",
		"reconciled": reconciled,
		"parties": len(grouped) - len(failures),
		"failures": failures,
	}
