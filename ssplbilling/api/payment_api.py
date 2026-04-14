import json
import frappe
from collections import OrderedDict

@frappe.whitelist()
def get_ledger(ledger_name, ledger_type="Customer", from_date=None, to_date=None):
    """Return GL Entry rows for a ledger (Customer, Supplier, Employee, or Account) with a running balance."""
    if not ledger_name:
        frappe.throw("ledger_name is required")

    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -90)

    # Resolve display name
    if ledger_type == "Customer":
        filter_sql = "party_type = 'Customer' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Supplier":
        filter_sql = "party_type = 'Supplier' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Employee":
        filter_sql = "party_type = 'Employee' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    else:
        filter_sql = "account = %s AND (party IS NULL OR party = '')"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)

    # Opening balance
    opening_rows = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance
        FROM `tabGL Entry`
        WHERE {filter_sql} AND is_cancelled = 0 AND posting_date < %s
        """,
        params,
        as_dict=True,
    )
    opening_balance = float(opening_rows[0].balance if opening_rows else 0)

    # Detail rows
    entries_raw = frappe.db.sql(
        f"""
        SELECT posting_date, voucher_type, voucher_no, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE {filter_sql} AND is_cancelled = 0 AND posting_date >= %s AND posting_date <= %s
        ORDER BY posting_date ASC, creation ASC
        """,
        detail_params,
        as_dict=True,
    )

    voucher_groups = OrderedDict()
    for row in entries_raw:
        key = row.voucher_no
        if key not in voucher_groups:
            voucher_groups[key] = {
                "date": str(row.posting_date),
                "voucher_type": row.voucher_type,
                "voucher_no": row.voucher_no,
                "debit": 0.0,
                "credit": 0.0,
                "remarks": row.remarks or "",
            }
        voucher_groups[key]["debit"] += float(row.debit or 0)
        voucher_groups[key]["credit"] += float(row.credit or 0)

    balance = opening_balance
    entries = []
    for group in voucher_groups.values():
        balance += group["debit"] - group["credit"]
        entries.append({
            "date": group["date"],
            "voucher_type": group["voucher_type"],
            "voucher_no": group["voucher_no"],
            "debit": round(group["debit"], 2),
            "credit": round(group["credit"], 2),
            "balance": round(balance, 2),
            "remarks": group["remarks"],
        })

    return {
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(balance, 2),
        "entries": entries,
    }

@frappe.whitelist()
def get_customer_ledger(customer, from_date=None, to_date=None):
    return get_ledger(customer, "Customer", from_date, to_date)

@frappe.whitelist()
def get_outstanding_invoices(party, party_type="Customer"):
	"""Return outstanding vouchers (invoices + journal entries) for a party.

	Uses ERPNext's Payment Ledger Entry (PLE) as the primary source — same logic as
	the 'Get Outstanding Invoices' button in the Payment Entry doctype.  Adds a
	direct GL-Entry fallback for Journal Entries that pre-date the PLE migration
	(ERPNext < v14) or were posted without PLE records.
	"""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents
	from erpnext.accounts.party import get_party_account

	company = frappe.defaults.get_global_default("company")
	payment_type = "Receive" if party_type == "Customer" else "Pay"
	party_account = get_party_account(party_type, party, company)

	args = {
		"posting_date": frappe.utils.today(),
		"company": company,
		"party_type": party_type,
		"payment_type": payment_type,
		"party": party,
		"party_account": party_account,
		"get_outstanding_invoices": True,
	}
	erpnext_rows = get_outstanding_reference_documents(args) or []

	# Track voucher_nos already returned so we don't duplicate
	seen = {(r.get("voucher_type"), r.get("voucher_no")) for r in erpnext_rows}

	# GL-based fallback: find Journal Entries whose net party-side balance is positive
	# (outstanding amount) after subtracting any payments made against them.
	# `debit - credit` for Customer (Receivable); `credit - debit` for Supplier (Payable).
	if party_type == "Customer":
		net_expr = "SUM(gle.debit - gle.credit)"
		settled_expr = "SUM(g2.credit - g2.debit)"
	else:
		net_expr = "SUM(gle.credit - gle.debit)"
		settled_expr = "SUM(g2.debit - g2.credit)"

	gl_jvs = frappe.db.sql(
		f"""
		SELECT
			gle.voucher_no,
			MAX(gle.posting_date)         AS posting_date,
			{net_expr}                    AS original_amount,
			COALESCE((
				SELECT {settled_expr}
				FROM `tabGL Entry` g2
				WHERE g2.party_type = %(party_type)s
					AND g2.party       = %(party)s
					AND g2.against_voucher_type = 'Journal Entry'
					AND g2.against_voucher      = gle.voucher_no
					AND g2.is_cancelled = 0
			), 0) AS settled_amount
		FROM `tabGL Entry` gle
		WHERE gle.party_type    = %(party_type)s
			AND gle.party       = %(party)s
			AND gle.voucher_type = 'Journal Entry'
			AND gle.is_cancelled = 0
		GROUP BY gle.voucher_no
		HAVING (original_amount - settled_amount) > 0.01
		ORDER BY posting_date DESC
		LIMIT 200
		""",
		{"party_type": party_type, "party": party},
		as_dict=True,
	)

	for row in gl_jvs:
		key = ("Journal Entry", row.voucher_no)
		if key in seen:
			continue
		outstanding = float(row.original_amount or 0) - float(row.settled_amount or 0)
		if outstanding <= 0.01:
			continue
		erpnext_rows.append(frappe._dict({
			"voucher_type": "Journal Entry",
			"voucher_no": row.voucher_no,
			"posting_date": row.posting_date,
			"due_date": row.posting_date,
			"invoice_amount": outstanding,
			"outstanding_amount": outstanding,
		}))

	return erpnext_rows

@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry."""
    if not data: data = frappe.form_dict.get("data") or dict(frappe.form_dict)
    if isinstance(data, str): data = json.loads(data)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = data.get("payment_type") or "Receive"
    pe.party_type = data.get("party_type") or "Customer"
    pe.party = data.get("party") or data.get("customer") or data.get("customer_id")
    pe.paid_amount = float(data.get("amount") or 0)
    pe.received_amount = pe.paid_amount
    pe.mode_of_payment = data.get("mode_of_payment") or "Cash"
    
    # Explicitly set currencies and exchange rates to INR
    pe.paid_from_account_currency = "INR"
    pe.paid_to_account_currency = "INR"
    pe.source_exchange_rate = 1.0
    pe.target_exchange_rate = 1.0
    
    # RESOLVE ACCOUNTS
    party_account = data.get("account") or _get_party_account(pe.party_type, pe.party)
    mop_account = data.get("mop_account") or _get_mop_account(data.get("mode_of_payment"))

    if pe.payment_type == "Receive":
        pe.paid_from = data.get("paid_from") or party_account
        pe.paid_to = data.get("paid_to") or mop_account
    else: # Pay
        pe.paid_from = data.get("paid_from") or mop_account
        pe.paid_to = data.get("paid_to") or party_account
            
    pe.insert()
    pe.submit()
    return {"payment_entry": pe.name}

def _get_party_account(party_type, party):
    """Get the default receivable/payable account for a party."""
    from erpnext.accounts.party import get_party_account
    company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value('Global Defaults', 'default_company')
    return get_party_account(party_type, party, company)

def _get_mop_account(mode_of_payment):
    """Get the default bank/cash account for a mode of payment."""
    if not mode_of_payment: return None
    company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value('Global Defaults', 'default_company')
    return frappe.db.get_value("Mode of Payment Account", 
        {"parent": mode_of_payment, "company": company}, "default_account")

@frappe.whitelist()
def search_suppliers(query=""):
    from ssplbilling.api.supplier_creator_api import search_suppliers as _impl
    return _impl(query)

@frappe.whitelist()
def search_accounts(query="", account_type=None):
    """Search chart of accounts."""
    filters = [["disabled", "=", 0], ["is_group", "=", 0]]
    if account_type: filters.append(["account_type", "=", account_type])
    if query: filters.append(["account_name", "like", f"%{query}%"])
    return frappe.get_all("Account", filters=filters, fields=["name", "account_name"], limit=25)
