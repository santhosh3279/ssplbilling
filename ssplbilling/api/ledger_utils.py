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


def get_account_balance(account):
	"""Current ledger balance (debit - credit) for a party-less Account.

	Mirrors the account balance query in customersearch_api.get_all_ledgers."""
	rows = frappe.db.sql(
		"""SELECT SUM(debit) - SUM(credit) AS balance
		   FROM `tabGL Entry`
		   WHERE is_cancelled = 0 AND (party IS NULL OR party = '') AND account = %s""",
		(account,),
		as_dict=True,
	)
	return float(rows[0].balance or 0) if rows and rows[0].balance is not None else 0.0


def _broadcast_ledger_balance(name, is_party):
	"""Recompute (from committed data) and broadcast one ledger's balance to all clients."""
	balance = get_party_balance(name) if is_party else get_account_balance(name)
	frappe.publish_realtime("ledger_balance_update", {"name": name, "balance": balance})


def publish_ledger_balance_updates(doc, method=None):
	"""Doc event: after a voucher is submitted/cancelled, broadcast the new balance for every
	party and account whose GL Entry balance changed.

	Names are collected now (robust to however cancellation rewrites the entries), but the
	balances are recomputed inside an after-commit callback so the SUM reads the final committed
	state — correct for BOTH submit and cancel, where in-transaction is_cancelled timing differs."""
	if not doc or not doc.name:
		return

	gl_rows = frappe.get_all(
		"GL Entry",
		filters={"voucher_type": doc.doctype, "voucher_no": doc.name},
		fields=["party", "account"],
	)

	parties = set()
	accounts = set()
	for r in gl_rows:
		if r.party:
			parties.add(r.party)
		elif r.account:
			accounts.add(r.account)

	if not parties and not accounts:
		return

	def _emit():
		for p in parties:
			_broadcast_ledger_balance(p, True)
		for a in accounts:
			_broadcast_ledger_balance(a, False)

	frappe.db.after_commit.add(_emit)
