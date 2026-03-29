import json
import frappe

@frappe.whitelist()
def get_ledger(ledger_name, ledger_type="Customer", from_date=None, to_date=None):
    """Return GL Entry rows for a ledger (Customer, Supplier, Employee, or Account) with a running balance.

    Args:
        ledger_name : Name / ID of the party or account
        ledger_type : 'Customer', 'Supplier', 'Employee', or 'Account'
        from_date   : ISO date "YYYY-MM-DD", defaults to 90 days ago
        to_date     : ISO date "YYYY-MM-DD", defaults to today
    """
    if not ledger_name:
        frappe.throw("ledger_name is required")

    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -90)

    # Resolve display name
    if ledger_type == "Customer":
        label = frappe.db.get_value("Customer", ledger_name, "customer_name") or ledger_name
        filter_sql = "party_type = 'Customer' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Supplier":
        label = frappe.db.get_value("Supplier", ledger_name, "supplier_name") or ledger_name
        filter_sql = "party_type = 'Supplier' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    elif ledger_type == "Employee":
        label = frappe.db.get_value("Employee", ledger_name, "employee_name") or ledger_name
        filter_sql = "party_type = 'Employee' AND party = %s"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)
    else:
        label = frappe.db.get_value("Account", ledger_name, "account_name") or ledger_name
        filter_sql = "account = %s AND (party IS NULL OR party = '')"
        params = (ledger_name, from_date)
        detail_params = (ledger_name, from_date, to_date)

    # Opening balance: sum of all GL entries before from_date
    opening_rows = frappe.db.sql(
        f"""
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance
        FROM `tabGL Entry`
        WHERE {filter_sql}
          AND is_cancelled = 0
          AND posting_date < %s
        """,
        params,
        as_dict=True,
    )
    opening_balance = float(opening_rows[0].balance if opening_rows else 0)

    # Detail rows for the date range
    entries_raw = frappe.db.sql(
        f"""
        SELECT
            posting_date,
            voucher_type,
            voucher_no,
            debit,
            credit,
            remarks
        FROM `tabGL Entry`
        WHERE {filter_sql}
          AND is_cancelled = 0
          AND posting_date >= %s
          AND posting_date <= %s
        ORDER BY posting_date ASC, creation ASC
        LIMIT 1000
        """,
        detail_params,
        as_dict=True,
    )

    balance = opening_balance
    entries = []
    total_debit = 0.0
    total_credit = 0.0

    # Collect unique voucher identifiers for batch fetching
    voucher_map = {} # (type, no) -> bool

    for row in entries_raw:
        debit = float(row.debit or 0)
        credit = float(row.credit or 0)
        balance += debit - credit
        total_debit += debit
        total_credit += credit
        entries.append(
            {
                "date": str(row.posting_date),
                "voucher_type": row.voucher_type,
                "voucher_no": row.voucher_no,
                "debit": round(debit, 2),
                "credit": round(credit, 2),
                "balance": round(balance, 2),
                "remarks": row.remarks or "",
            }
        )
        voucher_map[(row.voucher_type, row.voucher_no)] = True

    # ─── BATCH FETCH VOUCHER DETAILS ───
    details_cache = {}

    # 1. Batch fetch Sales Invoice items
    si_names = [v[1] for v in voucher_map.keys() if v[0] == "Sales Invoice"]
    if si_names:
        si_items = frappe.get_all("Sales Invoice Item",
            filters={"parent": ["in", si_names]},
            fields=["parent", "item_code", "item_name", "qty", "rate", "amount", "uom"]
        )
        # Fetch grand totals and outstanding for header-level summary
        si_docs = frappe.get_all("Sales Invoice",
            filters={"name": ["in", si_names]},
            fields=["name", "posting_date", "grand_total", "outstanding_amount", "status", "customer_name", "remarks"]
        )
        si_meta = {d.name: d for d in si_docs}

        for item in si_items:
            parent = item.parent
            if parent not in details_cache:
                m = si_meta.get(parent, {})
                details_cache[parent] = {
                    "voucher_type": "Sales Invoice",
                    "voucher_no": parent,
                    "posting_date": str(m.get("posting_date", "")),
                    "status": m.get("status", ""),
                    "remarks": m.get("remarks", ""),
                    "party_name": m.get("customer_name", ""),
                    "total_amount": float(m.get("grand_total", 0)),
                    "outstanding_amount": float(m.get("outstanding_amount", 0)),
                    "items": []
                }
            details_cache[parent]["items"].append(item)

    # 2. Batch fetch Payment Entry references
    pe_names = [v[1] for v in voucher_map.keys() if v[0] == "Payment Entry"]
    if pe_names:
        pe_refs = frappe.get_all("Payment Entry Reference",
            filters={"parent": ["in", pe_names]},
            fields=["parent", "reference_doctype", "reference_name", "allocated_amount"]
        )
        pe_docs = frappe.get_all("Payment Entry",
            filters={"name": ["in", pe_names]},
            fields=["name", "posting_date", "paid_amount", "mode_of_payment", "payment_type", "party_name", "remarks"]
        )
        pe_meta = {d.name: d for d in pe_docs}

        for ref in pe_refs:
            parent = ref.parent
            if parent not in details_cache:
                m = pe_meta.get(parent, {})
                details_cache[parent] = {
                    "voucher_type": "Payment Entry",
                    "voucher_no": parent,
                    "posting_date": str(m.get("posting_date", "")),
                    "status": "Submitted",
                    "remarks": m.get("remarks", ""),
                    "party_name": m.get("party_name", ""),
                    "total_amount": float(m.get("paid_amount", 0)),
                    "mode_of_payment": m.get("mode_of_payment", ""),
                    "items": []
                }
            details_cache[parent]["items"].append(ref)

    # 3. Batch fetch Journal Entry accounts
    je_names = [v[1] for v in voucher_map.keys() if v[0] == "Journal Entry"]
    if je_names:
        je_items = frappe.get_all("Journal Entry Account",
            filters={"parent": ["in", je_names]},
            fields=["parent", "account", "debit_in_account_currency as debit", "credit_in_account_currency as credit"]
        )
        je_docs = frappe.get_all("Journal Entry",
            filters={"name": ["in", je_names]},
            fields=["name", "posting_date", "total_debit", "user_remark"]
        )
        je_meta = {d.name: d for d in je_docs}

        for item in je_items:
            parent = item.parent
            if parent not in details_cache:
                m = je_meta.get(parent, {})
                details_cache[parent] = {
                    "voucher_type": "Journal Entry",
                    "voucher_no": parent,
                    "posting_date": str(m.get("posting_date", "")),
                    "status": "Submitted",
                    "remarks": m.get("user_remark", ""),
                    "total_amount": float(m.get("total_debit", 0)),
                    "items": []
                }
            details_cache[parent]["items"].append(item)

    return {
        "ledger_name": ledger_name,
        "ledger_type": ledger_type,
        "label": label,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(balance, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "entries": entries,
        "voucher_details": details_cache
    }

@frappe.whitelist()
def get_customer_ledger(customer, from_date=None, to_date=None):
    """Backward compatibility wrapper for get_ledger."""
    return get_ledger(customer, "Customer", from_date, to_date)

@frappe.whitelist()
def get_voucher_detail(voucher_type, voucher_no):
    """Return key fields from a voucher."""
    doc = frappe.get_doc(voucher_type, voucher_no)
    base = {"voucher_type": voucher_type, "voucher_no": voucher_no, "posting_date": str(doc.posting_date), "status": doc.get("status") or "", "items": []}
    if voucher_type == "Sales Invoice":
        base["items"] = [{"item_code": r.item_code, "item_name": r.item_name, "qty": float(r.qty), "rate": float(r.rate), "amount": float(r.amount), "uom": r.uom or r.stock_uom or ""} for r in doc.items]
        base["party_name"] = doc.customer_name
        base["total_amount"] = float(doc.grand_total)
        base["outstanding_amount"] = float(doc.outstanding_amount)
    elif voucher_type == "Payment Entry":
        base["items"] = [{"reference_doctype": r.reference_doctype, "reference_name": r.reference_name, "allocated_amount": float(r.allocated_amount)} for r in doc.references]
        base["party_name"] = doc.party_name
        base["total_amount"] = float(doc.paid_amount)
        base["mode_of_payment"] = doc.mode_of_payment
    elif voucher_type == "Journal Entry":
        base["items"] = [{"account": r.account, "debit": float(r.debit_in_account_currency), "credit": float(r.credit_in_account_currency)} for r in doc.accounts]
        base["total_amount"] = float(doc.total_debit)
    return base

@frappe.whitelist()
def get_outstanding_invoices(customer):
    """Return submitted Sales Invoices with outstanding balance."""
    return frappe.get_all("Sales Invoice", filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]}, fields=["name", "posting_date", "grand_total", "outstanding_amount"], limit=50)

@frappe.whitelist()
def get_outstanding_purchase_invoices(supplier):
    """Return submitted Purchase Invoices with outstanding balance.
    Kept here for backward compat — canonical version in supplier_creator_api.py."""
    from ssplbilling.api.supplier_creator_api import get_outstanding_purchase_invoices as _impl
    return _impl(supplier)

@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry."""
    if not data: data = frappe.form_dict.get("data") or dict(frappe.form_dict)
    if isinstance(data, str): data = json.loads(data)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = data.get("payment_type") or "Receive"
    pe.party_type = data.get("party_type") or "Customer"
    pe.party = data.get("party") or data.get("customer")
    pe.paid_amount = float(data.get("amount") or 0)
    pe.received_amount = pe.paid_amount
    pe.mode_of_payment = data.get("mode_of_payment") or "Cash"
    pe.insert(); pe.submit()
    return {"payment_entry": pe.name}

@frappe.whitelist()
def search_suppliers(query=""):
    """Kept for backward compat — canonical version in supplier_creator_api.py."""
    from ssplbilling.api.supplier_creator_api import search_suppliers as _impl
    return _impl(query)

@frappe.whitelist()
def search_accounts(query="", account_type=None):
    """Search chart of accounts."""
    filters = [["disabled", "=", 0], ["is_group", "=", 0]]
    if account_type: filters.append(["account_type", "=", account_type])
    if query: filters.append(["account_name", "like", f"%{query}%"])
    return frappe.get_all("Account", filters=filters, fields=["name", "account_name"], limit=25)

@frappe.whitelist()
def get_warehouses():
    """Return all enabled, non-group warehouses."""
    return [r.name for r in frappe.get_all(
        "Warehouse",
        filters={"disabled": 0, "is_group": 0},
        fields=["name"],
        order_by="name asc",
    )]


def _batch_voucher_details(entries):
    """Batch-fetch header + line items for all unique vouchers in the entries list."""
    from collections import defaultdict

    by_type = defaultdict(list)
    for e in entries:
        by_type[e.voucher_type].append(e.voucher_no)

    details = {}  # voucher_no -> detail dict

    VOUCHER_MAP = {
        "Sales Invoice":    ("Sales Invoice Item",    "customer_name",  "grand_total",  "uom",        "rate"),
        "Delivery Note":    ("Delivery Note Item",    "customer_name",  "grand_total",  "uom",        "rate"),
        "Purchase Invoice": ("Purchase Invoice Item", "supplier_name",  "grand_total",  "uom",        "rate"),
        "Purchase Receipt": ("Purchase Receipt Item", "supplier_name",  "grand_total",  "uom",        "rate"),
    }

    for vtype, (child_dt, party_field, total_field, uom_field, rate_field) in VOUCHER_MAP.items():
        if not by_type.get(vtype):
            continue
        names = list(set(by_type[vtype]))
        headers = {r.name: r for r in frappe.get_all(
            vtype,
            filters={"name": ["in", names]},
            fields=["name", party_field, total_field],
        )}
        items_rows = frappe.get_all(
            child_dt,
            filters={"parent": ["in", names]},
            fields=["parent", "item_code", "item_name", "qty", rate_field, "amount", uom_field, "stock_uom"],
        )
        items_map = defaultdict(list)
        for r in items_rows:
            items_map[r.parent].append({
                "item_code": r.item_code,
                "item_name": r.item_name,
                "qty": float(r.qty or 0),
                "rate": float(r.get(rate_field) or 0),
                "amount": float(r.amount or 0),
                "uom": r.get(uom_field) or r.stock_uom or "",
            })
        for name in names:
            h = headers.get(name, {})
            details[name] = {
                "voucher_type": vtype,
                "party_name": h.get(party_field) or "",
                "total_amount": float(h.get(total_field) or 0),
                "items": items_map.get(name, []),
            }

    # Stock Entry
    if by_type.get("Stock Entry"):
        names = list(set(by_type["Stock Entry"]))
        headers = {r.name: r for r in frappe.get_all(
            "Stock Entry",
            filters={"name": ["in", names]},
            fields=["name", "stock_entry_type", "total_amount"],
        )}
        items_rows = frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": ["in", names]},
            fields=["parent", "item_code", "item_name", "qty", "basic_rate", "amount", "uom"],
        )
        items_map = defaultdict(list)
        for r in items_rows:
            items_map[r.parent].append({
                "item_code": r.item_code,
                "item_name": r.item_name,
                "qty": float(r.qty or 0),
                "rate": float(r.basic_rate or 0),
                "amount": float(r.amount or 0),
                "uom": r.uom or "",
            })
        for name in names:
            h = headers.get(name, {})
            details[name] = {
                "voucher_type": "Stock Entry",
                "party_name": h.get("stock_entry_type") or "",
                "total_amount": float(h.get("total_amount") or 0),
                "items": items_map.get(name, []),
            }

    return details


@frappe.whitelist()
def get_stock_ledger(item_code, from_date=None, to_date=None, warehouse=None):
    """Return Stock Ledger Entry rows with running balance, summary totals, and pre-loaded voucher details."""
    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -30)

    wh_params = []
    wh_clause = ""
    if warehouse:
        wh_clause = " AND warehouse = %s"
        wh_params.append(warehouse)

    # Opening balance: sum of actual_qty strictly before from_date
    opening_row = frappe.db.sql(
        "SELECT IFNULL(SUM(actual_qty), 0) AS qty FROM `tabStock Ledger Entry` "
        "WHERE item_code = %s AND is_cancelled = 0 AND posting_date < %s" + wh_clause,
        [item_code, from_date] + wh_params,
        as_dict=True,
    )
    opening_balance = float(opening_row[0].qty if opening_row else 0)

    entries = frappe.db.sql(
        "SELECT posting_date as date, voucher_type, voucher_no, actual_qty, stock_uom, warehouse "
        "FROM `tabStock Ledger Entry` "
        "WHERE item_code = %s AND is_cancelled = 0 AND posting_date >= %s AND posting_date <= %s" + wh_clause + " "
        "ORDER BY posting_date ASC, creation ASC",
        [item_code, from_date, to_date] + wh_params,
        as_dict=True,
    )

    running = opening_balance
    total_in = 0.0
    total_out = 0.0
    for e in entries:
        qty = float(e.actual_qty or 0)
        running += qty
        e["balance"] = running
        e["actual_qty"] = qty
        e["date"] = str(e["date"])
        if qty > 0:
            total_in += qty
        else:
            total_out += abs(qty)

    # Batch-fetch all voucher details in one go
    voucher_details = _batch_voucher_details(entries)
    for e in entries:
        e["detail"] = voucher_details.get(e["voucher_no"])

    return {
        "item_code": item_code,
        "entries": entries,
        "opening_balance": opening_balance,
        "total_in": total_in,
        "total_out": total_out,
        "closing_balance": opening_balance + total_in - total_out,
    }
