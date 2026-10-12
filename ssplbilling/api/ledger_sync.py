"""Realtime invalidation for the client ledger cache (Customers, Suppliers, Employees, Accounts).

Changed ledger names are collected per transaction and broadcast once after commit as
`ledger_update` {"names": [...]}; clients refetch just those rows with
customersearch_api.get_ledgers_by_name. Changes no per-row patch can express (the Visible
Accounts list in SSPL Billing Settings, very large imports) send {"full": True} instead, and
clients reload the whole list.
"""

import frappe

# Above this many names a single message asks clients to reload everything instead.
MAX_NAMES = 500


def queue_ledger_update(names=(), full=False):
	pending = getattr(frappe.local, "_sspl_ledger_pending", None)
	if pending is None:
		pending = frappe.local._sspl_ledger_pending = {"names": {}, "full": False}
		frappe.db.after_commit.add(_flush)
		frappe.db.after_rollback.add(_discard)
	pending["names"].update(dict.fromkeys(n for n in names if n))
	pending["full"] = pending["full"] or full


def _flush():
	pending = getattr(frappe.local, "_sspl_ledger_pending", None)
	frappe.local._sspl_ledger_pending = None
	if not pending:
		return
	names = list(pending["names"])
	if pending["full"] or len(names) > MAX_NAMES:
		payload = {"full": True}
	elif names:
		payload = {"names": names}
	else:
		return
	# Already committed, so publish now rather than queueing for a commit that won't come.
	frappe.publish_realtime("ledger_update", payload, after_commit=False)


def _discard():
	frappe.local._sspl_ledger_pending = None


# ── Doc event handlers ──────────────────────────────────────────────────────────


def on_ledger_change(doc, method=None):
	"""Customer / Supplier / Employee / Account inserted, updated or deleted."""
	if doc and doc.name:
		queue_ledger_update([doc.name])


def on_ledger_rename(doc, method=None, old=None, new=None, merge=False):
	"""Drop the row under the old name and add it under the new one."""
	queue_ledger_update([old, new or (doc.name if doc else None)])


def on_linked_party_change(doc, method=None):
	"""Address / Contact changed: refresh every Customer or Supplier it is (or was) linked to."""
	docs = [doc]
	before = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	if before is not None:
		docs.append(before)
	queue_ledger_update(
		link.link_name
		for d in docs
		for link in (d.get("links") or [])
		if link.link_doctype in ("Customer", "Supplier")
	)


def on_party_link_change(doc, method=None):
	if doc:
		queue_ledger_update([doc.get("primary_party"), doc.get("secondary_party")])


def on_billing_settings_change(doc, method=None):
	"""The Visible Accounts list decides which accounts are ledgers at all."""
	queue_ledger_update(full=True)
