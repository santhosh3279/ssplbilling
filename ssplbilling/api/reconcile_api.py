import frappe
import json


def _get_company():
	return frappe.defaults.get_global_default("company")


def _get_party_account(party_type, party):
	from erpnext.accounts.party import get_party_account
	return get_party_account(party_type, party, _get_company())


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
			MAX(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN jea.name ELSE NULL END)                             AS reference_row,
			MAX(je.posting_date)                                              AS posting_date,
			IFNULL(MAX(je.cheque_no), '')                                     AS reference_no,
			IFNULL(MAX(je.user_remark), '')                                   AS remarks,
			MAX(je.total_debit)                                               AS journal_total_debit,
			SUM(ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)) AS total_amount,
			SUM(CASE WHEN (jea.reference_name IS NULL OR jea.reference_name = '')
			         THEN ABS(jea.credit_in_account_currency - jea.debit_in_account_currency)
			         ELSE 0 END)                                              AS unallocated_amount,
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
		HAVING unallocated_amount > 0.005
		ORDER BY posting_date DESC
		""",
		(party_type, party, tuple(account_types), company),
		as_dict=True,
	)

	# Accurate unallocated_amount calculation via Payment Ledger
	if je_entries:
		je_names = list(set(r["name"] for r in je_entries))
		# Sum of all reconciled amounts for these JEs and this party
		pl_links = frappe.db.sql(
			"""
			SELECT name, SUM(linked_amount) as linked_amount FROM (
				SELECT voucher_no as name, SUM(ABS(amount_in_account_currency)) as linked_amount
				FROM `tabPayment Ledger`
				WHERE voucher_no IN %s AND against_voucher_no != voucher_no
				  AND party = %s AND delinked = 0
				GROUP BY voucher_no
				UNION ALL
				SELECT against_voucher_no as name, SUM(ABS(amount_in_account_currency)) as linked_amount
				FROM `tabPayment Ledger`
				WHERE against_voucher_no IN %s AND voucher_no != against_voucher_no
				  AND party = %s AND delinked = 0
				GROUP BY against_voucher_no
			) t GROUP BY name
			""",
			(tuple(je_names), party, tuple(je_names), party),
			as_dict=True,
		)

		links_map = {r["name"]: float(r["linked_amount"]) for r in pl_links}
		
		processed_jes = []
		for je in je_entries:
			linked = links_map.get(je["name"], 0)
			# Re-calculate unallocated_amount: Total party-specific amount minus PL links
			je["unallocated_amount"] = max(0, float(je["total_amount"]) - linked)
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
			       customer_name AS party_name, is_return, 'Sales Invoice' as doctype
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
			       supplier_name AS party_name, is_return, 'Purchase Invoice' as doctype
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
def post_reconciliation(party_type, party, allocations):
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

	company = _get_company()
	account = _get_party_account(party_type, party)

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

			seen_invoices[inv_name] = float(outstanding)
			rec.append("invoices", {
				"invoice_type": inv_type,
				"invoice_number": inv_name,
				"outstanding_amount": float(outstanding),
			})

	# 2. Build allocation rows.
	for alloc in allocations:
		unreconciled = float(alloc.get("unreconciled_amount") or alloc["amount"])
		rec.append(
			"allocation",
			{
				"reference_type": alloc["payment_type"],
				"reference_name": alloc["payment_name"],
				"reference_row": alloc.get("reference_row") or None,
				"invoice_type": alloc["invoice_type"],
				"invoice_number": alloc["invoice_name"],     # ERPNext field name
				"allocated_amount": float(alloc["amount"]),
				"amount": unreconciled,                      # payment's total unreconciled amount
				"unreconciled_amount": unreconciled,
			},
		)

	rec.reconcile()
	return {"status": "ok", "reconciled": len(allocations)}
