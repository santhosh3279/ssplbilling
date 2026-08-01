"""Cheque register — Option A clearing-account flow.

Received cheque : Dr Cheques in Hand  / Cr Debtors   (Payment Entry, on handover)
                  Dr Bank             / Cr Cheques in Hand (Journal Entry, on clearance)
Issued cheque   : Dr Creditors        / Cr Cheques Issued  (Payment Entry, on handover)
                  Dr Cheques Issued   / Cr Bank            (Journal Entry, on clearance)

The bank ledger is only touched by the clearance Journal Entry, on the date
the cheque is actually processed at the bank.
"""

import json

import frappe

RECEIVED_ACCOUNT = "Cheques in Hand"
ISSUED_ACCOUNT = "Cheques Issued"


def _company(company=None):
    return company or frappe.defaults.get_global_default("company")


def _get_or_create_clearing_account(direction, company=None):
    """Return the clearing account for the direction, creating it on first use."""
    company = _company(company)
    account_name = RECEIVED_ACCOUNT if direction == "Received" else ISSUED_ACCOUNT
    root_type = "Asset" if direction == "Received" else "Liability"

    existing = frappe.db.get_value("Account", {"account_name": account_name, "company": company})
    if existing:
        return existing

    parent_label = "Current Assets" if root_type == "Asset" else "Current Liabilities"
    parent = frappe.db.get_value(
        "Account", {"account_name": parent_label, "company": company, "is_group": 1}
    )
    if not parent:
        parent = frappe.db.get_value(
            "Account",
            {"root_type": root_type, "company": company, "is_group": 1},
            order_by="lft asc",
        )
    if not parent:
        frappe.throw(f"Could not find a parent account to create '{account_name}' under")

    acc = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "parent_account": parent,
            "company": company,
            "root_type": root_type,
            # account_type Bank so Payment Entry accepts it as paid_from/paid_to
            "account_type": "Bank",
            "is_group": 0,
        }
    )
    acc.insert(ignore_permissions=True)
    return acc.name


def _make_payment_entry(cheque, references, posting_date):
    """Party ↔ clearing account Payment Entry created when the cheque changes hands."""
    from erpnext.accounts.party import get_party_account

    company = cheque.company or _company()
    clearing = _get_or_create_clearing_account(cheque.direction, company)
    party_account = get_party_account(cheque.party_type, cheque.party, company)

    pe = frappe.new_doc("Payment Entry")
    pe.company = company
    pe.payment_type = "Receive" if cheque.direction == "Received" else "Pay"
    pe.party_type = cheque.party_type
    pe.party = cheque.party
    pe.posting_date = posting_date
    pe.paid_amount = cheque.amount
    pe.received_amount = cheque.amount
    pe.reference_no = cheque.cheque_no
    pe.reference_date = cheque.cheque_date
    pe.paid_from_account_currency = "INR"
    pe.paid_to_account_currency = "INR"
    pe.source_exchange_rate = 1.0
    pe.target_exchange_rate = 1.0
    if frappe.db.exists("Mode of Payment", "Cheque"):
        pe.mode_of_payment = "Cheque"

    if cheque.direction == "Received":
        pe.paid_from = party_account
        pe.paid_to = clearing
    else:
        pe.paid_from = clearing
        pe.paid_to = party_account

    pe.remarks = f"Cheque {cheque.cheque_no} {cheque.direction.lower()} — {cheque.name}"

    for ref in references:
        pe.append(
            "references",
            {
                "reference_doctype": ref.get("reference_doctype"),
                "reference_name": ref.get("reference_name"),
                "total_amount": float(ref.get("total_amount") or 0),
                "outstanding_amount": float(ref.get("outstanding_amount") or 0),
                "allocated_amount": float(ref.get("allocated_amount") or 0),
            },
        )

    pe.insert()
    pe.submit()
    return pe


@frappe.whitelist()
def create_cheque(data=None, **kwargs):
    """Register a cheque and post the party ↔ clearing-account Payment Entry."""
    if not data:
        data = frappe.form_dict.get("data") or dict(frappe.form_dict)
    if isinstance(data, str):
        data = json.loads(data)

    direction = data.get("direction")
    if direction not in ("Received", "Issued"):
        frappe.throw("direction must be 'Received' or 'Issued'")

    party_type = data.get("party_type") or ("Customer" if direction == "Received" else "Supplier")
    party = data.get("party")
    amount = float(data.get("amount") or 0)
    cheque_no = (data.get("cheque_no") or "").strip()
    cheque_date = data.get("cheque_date")

    if not party:
        frappe.throw("party is required")
    if amount <= 0:
        frappe.throw("amount must be greater than zero")
    if not cheque_no:
        frappe.throw("cheque_no is required")
    if not cheque_date:
        frappe.throw("cheque_date is required")

    posting_date = cheque_date
    if party_type == "Customer":
        party_name_field = "customer_name"
    elif party_type == "Supplier":
        party_name_field = "supplier_name"
    elif party_type == "Employee":
        party_name_field = "employee_name"
    else:
        party_name_field = "name"
    party_name = frappe.db.get_value(party_type, party, party_name_field) or party
    company = data.get("company") or _company()

    cheque = frappe.get_doc(
        {
            "doctype": "SSPL Cheque",
            "company": company,
            "direction": direction,
            "party_type": party_type,
            "party": party,
            "party_name": party_name,
            "cheque_no": cheque_no,
            "cheque_date": cheque_date,
            "bank_name": data.get("bank_name") or "",
            "amount": amount,
            "status": "Pending",
            "remarks": data.get("remarks") or "",
        }
    ).insert()

    pe = _make_payment_entry(cheque, data.get("references") or [], posting_date)
    cheque.db_set("payment_entry", pe.name)

    return {"cheque": cheque.name, "payment_entry": pe.name}


@frappe.whitelist()
def get_cheques(status="Pending", direction="All", party=None, company=None, limit=200):
    """List cheques for the register, plus pending totals for the summary cards."""
    filters = {}
    if status and status != "All":
        filters["status"] = status
    if direction and direction != "All":
        filters["direction"] = direction
    if party:
        filters["party"] = party
    if company:
        filters["company"] = company

    rows = frappe.get_all(
        "SSPL Cheque",
        filters=filters,
        fields=[
            "name", "direction", "status", "party_type", "party", "party_name",
            "cheque_no", "cheque_date", "bank_name", "amount",
            "payment_entry", "clearance_entry", "clearance_date", "bank_account",
            "remarks", "creation",
        ],
        order_by="cheque_date desc, creation desc",
        limit=int(limit),
    )

    summary = {"received_total": 0.0, "received_count": 0, "issued_total": 0.0, "issued_count": 0}
    
    pending_query = "SELECT direction, SUM(amount) AS total, COUNT(*) AS cnt FROM `tabSSPL Cheque` WHERE status = 'Pending'"
    pending_args = {}
    if company:
        pending_query += " AND company = %(company)s"
        pending_args["company"] = company
    pending_query += " GROUP BY direction"
    
    pending = frappe.db.sql(pending_query, pending_args, as_dict=True)
    for p in pending:
        key = "received" if p.direction == "Received" else "issued"
        summary[f"{key}_total"] = float(p.total or 0)
        summary[f"{key}_count"] = int(p.cnt or 0)

    return {"cheques": rows, "summary": summary}


@frappe.whitelist()
def clear_cheque(name, bank_account, clearance_date=None):
    """Settle a pending cheque: move it from the clearing account into the bank ledger."""
    doc = frappe.get_doc("SSPL Cheque", name)
    if doc.status != "Pending":
        frappe.throw(f"Cheque {name} is {doc.status}; only Pending cheques can be cleared")
    if not bank_account:
        frappe.throw("bank_account is required")

    clearance_date = clearance_date or frappe.utils.today()
    if frappe.utils.getdate(clearance_date) < frappe.utils.getdate(doc.cheque_date):
        frappe.throw(f"Clearance date cannot be before the cheque date ({doc.cheque_date})")

    clearing = _get_or_create_clearing_account(doc.direction)

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Bank Entry"
    je.company = _company()
    je.posting_date = clearance_date
    je.cheque_no = doc.cheque_no
    je.cheque_date = doc.cheque_date
    je.user_remark = f"Cheque {doc.cheque_no} ({doc.party_name or doc.party}) cleared — {doc.name}"

    if doc.direction == "Received":
        je.append("accounts", {"account": bank_account, "debit_in_account_currency": doc.amount})
        je.append("accounts", {"account": clearing, "credit_in_account_currency": doc.amount})
    else:
        je.append("accounts", {"account": clearing, "debit_in_account_currency": doc.amount})
        je.append("accounts", {"account": bank_account, "credit_in_account_currency": doc.amount})

    je.insert()
    je.submit()

    doc.db_set("clearance_entry", je.name)
    doc.db_set("clearance_date", clearance_date)
    doc.db_set("bank_account", bank_account)
    doc.db_set("status", "Cleared")

    return {"cheque": doc.name, "status": "Cleared", "clearance_entry": je.name}


def _revert_pending_cheque(name, new_status):
    """Cancel the handover Payment Entry (restores party outstanding) and set final status."""
    doc = frappe.get_doc("SSPL Cheque", name)
    if doc.status != "Pending":
        frappe.throw(f"Cheque {name} is {doc.status}; only Pending cheques can be marked {new_status}")

    if doc.payment_entry:
        pe = frappe.get_doc("Payment Entry", doc.payment_entry)
        if pe.docstatus == 1:
            pe.cancel()

    doc.db_set("status", new_status)
    return {"cheque": doc.name, "status": new_status}


@frappe.whitelist()
def bounce_cheque(name):
    return _revert_pending_cheque(name, "Bounced")


@frappe.whitelist()
def cancel_cheque(name):
    return _revert_pending_cheque(name, "Cancelled")


@frappe.whitelist()
def get_bank_accounts():
    """Bank/Cash accounts for the settle dialog, excluding the two clearing accounts."""
    return frappe.get_all(
        "Account",
        filters={
            "company": _company(),
            "is_group": 0,
            "disabled": 0,
            "account_type": ["in", ["Bank", "Cash"]],
            "account_name": ["not in", [RECEIVED_ACCOUNT, ISSUED_ACCOUNT]],
        },
        fields=["name", "account_name", "account_type"],
        order_by="account_type asc, name asc",
    )
