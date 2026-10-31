import time

import frappe


def get_party_balance(party):
	"""Current ledger balance (debit - credit) for a Customer/Supplier party.

	Mirrors the party balance query in customersearch_api.get_all_ledgers so the
	realtime figure equals what a full refresh would show."""
	rows = frappe.db.sql(
		"""SELECT SUM(debit) - SUM(credit) AS balance
		   FROM `tabGL Entry`
		   WHERE is_cancelled = 0 AND party = %s""",
		(party,),
		as_dict=True,
	)
	return float(rows[0].balance or 0) if rows and rows[0].balance is not None else 0.0


def get_ledger_balance_snapshots(parties, accounts):
	"""Per-company balances for the given parties/accounts, in the shape the ledger cache patches.

	Uses the same rules as get_all_ledgers: party sums ignore party_type, account sums only count
	rows without a party. Each client picks its own company / alternative company from `balances`
	(an empty company means the sum over all companies)."""
	snapshots = {}

	def add(rows):
		for r in rows:
			entry = snapshots.setdefault(r.name, {"name": r.name, "balances": {}})
			entry["balances"][r.company or ""] = float(r.balance or 0)

	if parties:
		add(
			frappe.db.sql(
				"""SELECT party AS name, company, SUM(debit) - SUM(credit) AS balance
				   FROM `tabGL Entry`
				   WHERE is_cancelled = 0 AND party IN %(names)s
				   GROUP BY party, company""",
				{"names": list(parties)},
				as_dict=True,
			)
		)
		last_invoices = frappe.db.sql(
			"""SELECT customer, MAX(posting_date) AS last_date
			   FROM `tabSales Invoice`
			   WHERE docstatus = 1 AND customer IN %(names)s
			   GROUP BY customer""",
			{"names": list(parties)},
			as_dict=True,
		)
	else:
		last_invoices = []
	if accounts:
		add(
			frappe.db.sql(
				"""SELECT account AS name, company, SUM(debit) - SUM(credit) AS balance
				   FROM `tabGL Entry`
				   WHERE is_cancelled = 0 AND account IN %(names)s AND (party IS NULL OR party = '')
				   GROUP BY account, company""",
				{"names": list(accounts)},
				as_dict=True,
			)
		)

	# A ledger whose entries were all cancelled has no rows left: report it with no balances (= 0).
	for name in set(parties) | set(accounts):
		snapshots.setdefault(name, {"name": name, "balances": {}})
	for i in last_invoices:
		if i.last_date:
			snapshots[i.customer]["last_invoice_date"] = str(i.last_date)
	return list(snapshots.values())


def publish_ledger_balance_updates(doc, method=None):
	"""Doc event: after a voucher is submitted/cancelled, push the new per-company balances of every
	party and ledger-search account it touched to all desk users.

	Clients patch these rows in place, so one submit costs one small query here instead of every
	open tab re-downloading all ledgers. Names are collected now (robust to however cancellation
	rewrites the entries), but the balances are computed in an after-commit callback so the SUM
	reads the final committed state for both submit and cancel."""
	if not doc or not doc.name:
		return

	gl_rows = frappe.get_all(
		"GL Entry",
		filters={"voucher_type": doc.doctype, "voucher_no": doc.name},
		fields=["party", "account"],
	)
	parties = {r.party for r in gl_rows if r.party}
	accounts = {r.account for r in gl_rows if not r.party and r.account}
	if accounts:
		from ssplbilling.api.customersearch_api import _get_search_accounts

		# Only accounts the ledger search shows; hot posting accounts (Sales, GST) are never cached.
		accounts &= {a.name for a in _get_search_accounts()}
	if not parties and not accounts:
		return
	_queue_ledger_balances(parties, accounts)


def _queue_ledger_balances(parties, accounts):
	"""Collect the parties/accounts touched in this transaction; one ledger_balances message
	covering all of them goes out after commit.

	A cashier submit posts the invoice, one Payment Entry per mode and a discount Journal Entry
	in one request; each used to send its own message with the same customer recomputed. Nothing
	is sent on rollback."""
	state = getattr(frappe.local, "_sspl_ledger_balances_pending", None)
	if state is None:
		state = frappe.local._sspl_ledger_balances_pending = {"parties": set(), "accounts": set()}
		frappe.db.after_commit.add(_flush_ledger_balances)
		frappe.db.after_rollback.add(_discard_ledger_balances)
	state["parties"].update(parties)
	state["accounts"].update(accounts)


def _flush_ledger_balances():
	# Runs after commit, so the worker's SUM reads the final committed state for submit and cancel.
	# The SUM itself is left to a worker: for a counter customer it scans tens of thousands of GL
	# rows (~2s), and in an after-commit callback it held up the cashier's submit response.
	state = getattr(frappe.local, "_sspl_ledger_balances_pending", None)
	frappe.local._sspl_ledger_balances_pending = None
	if not state or not (state["parties"] or state["accounts"]):
		return
	frappe.enqueue(
		"ssplbilling.api.ledger_utils.publish_ledger_balances",
		queue="short",
		parties=list(state["parties"]),
		accounts=list(state["accounts"]),
	)


def publish_ledger_balances(parties, accounts):
	"""Worker: compute the balances and push one ledger_balances message."""
	frappe.publish_realtime(
		"ledger_balances",
		{"ts": time.time(), "ledgers": get_ledger_balance_snapshots(set(parties), set(accounts))},
		after_commit=False,
	)


def _discard_ledger_balances():
	frappe.local._sspl_ledger_balances_pending = None
