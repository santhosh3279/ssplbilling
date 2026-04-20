import frappe
from ssplbilling.api.payment_api import get_ledger, create_payment_entry
from ssplbilling.api.reconcile_api import get_outstanding_docs, get_unlinked_entries


@frappe.whitelist()
def get_party_balance(party, party_type="Customer"):
	"""Closing balance for a party — used per row in Single (Bulk) Payment Entry."""
	return get_ledger(ledger_name=party, ledger_type=party_type)


@frappe.whitelist()
def get_party_docs(party_type, party):
	"""Outstanding invoices + unlinked entries for a party in one round-trip."""
	outstanding = get_outstanding_docs(party_type=party_type, party=party)
	unlinked = get_unlinked_entries(party_type=party_type, party=party)
	return {
		"docs": outstanding.get("docs", []),
		"payment_entries": unlinked.get("payment_entries", []),
		"journal_entries": unlinked.get("journal_entries", []),
	}


@frappe.whitelist()
def create_bulk_payment(data):
	"""Create and submit a single Payment Entry row from the bulk entry screen."""
	return create_payment_entry(data=data)
