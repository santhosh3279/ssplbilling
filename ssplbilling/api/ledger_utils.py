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


def _broadcast_party_balance(party):
	"""Recompute (from committed data) and broadcast one party's balance to all clients."""
	frappe.publish_realtime("ledger_balance_update", {"name": party, "balance": get_party_balance(party)})


def publish_ledger_balance_updates(doc, method=None):
	"""Doc event: after a voucher is submitted/cancelled, broadcast the new balance for every
	Customer/Supplier party whose GL Entry balance changed.

	Names are collected now (robust to however cancellation rewrites the entries), but the
	balances are recomputed inside an after-commit callback so the SUM reads the final committed
	state — correct for BOTH submit and cancel, where in-transaction is_cancelled timing differs.

	Deliberately party-only: a party sum is bounded per-customer, whereas a hot account (e.g. the
	Sales/GST account) would sum every entry ever posted to it on every submit. Account-type
	ledgers reconcile on the next full get_all_ledgers refresh."""
	if not doc or not doc.name:
		return

	gl_rows = frappe.get_all(
		"GL Entry",
		filters={"voucher_type": doc.doctype, "voucher_no": doc.name},
		fields=["party"],
	)

	parties = {r.party for r in gl_rows if r.party}
	if not parties:
		return

	def _emit():
		for p in parties:
			_broadcast_party_balance(p)

	frappe.db.after_commit.add(_emit)
