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

	def _emit():
		frappe.publish_realtime(
			"ledger_balances",
			{"ts": time.time(), "ledgers": get_ledger_balance_snapshots(parties, accounts)},
			after_commit=False,
		)

	frappe.db.after_commit.add(_emit)
