import json
import frappe

@frappe.whitelist()
def get_ledger(ledger_name, ledger_type="Customer", from_date=None, to_date=None, company=None):
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

    if not company:
        company = frappe.defaults.get_global_default("company") or frappe.db.get_single_value('Global Defaults', 'default_company')

    # Resolve display name
    if ledger_type == "Customer":
        label = frappe.db.get_value("Customer", ledger_name, "customer_name") or ledger_name
        filter_sql = "party_type = 'Customer' AND party = %s AND company = %s"
        params = (ledger_name, company, from_date)
        detail_params = (ledger_name, company, from_date, to_date)
    elif ledger_type == "Supplier":
        label = frappe.db.get_value("Supplier", ledger_name, "supplier_name") or ledger_name
        filter_sql = "party_type = 'Supplier' AND party = %s AND company = %s"
        params = (ledger_name, company, from_date)
        detail_params = (ledger_name, company, from_date, to_date)
    elif ledger_type == "Employee":
        label = frappe.db.get_value("Employee", ledger_name, "employee_name") or ledger_name
        filter_sql = "party_type = 'Employee' AND party = %s AND company = %s"
        params = (ledger_name, company, from_date)
        detail_params = (ledger_name, company, from_date, to_date)
    else:
        label = frappe.db.get_value("Account", ledger_name, "account_name") or ledger_name
        filter_sql = "account = %s AND (party IS NULL OR party = '') AND company = %s"
        params = (ledger_name, company, from_date)
        detail_params = (ledger_name, company, from_date, to_date)

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
            remarks,
            against_voucher AS reference_no
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

    total_debit = 0.0
    total_credit = 0.0
    voucher_map = {}

    # Group multiple GL rows for the same voucher into a single ledger line.
    # This consolidates split JE rows (e.g. one row per invoice reference) so
    # the ledger shows one transaction = one line item.
    from collections import OrderedDict
    voucher_groups = OrderedDict()

    for row in entries_raw:
        debit = float(row.debit or 0)
        credit = float(row.credit or 0)
        total_debit += debit
        total_credit += credit
        key = row.voucher_no
        if key not in voucher_groups:
            voucher_groups[key] = {
                "date": str(row.posting_date),
                "voucher_type": row.voucher_type,
                "voucher_no": row.voucher_no,
                "debit": 0.0,
                "credit": 0.0,
                "remarks": row.remarks or "",
                "reference_no": row.reference_no or "",
            }
            voucher_map[(row.voucher_type, row.voucher_no)] = True
        voucher_groups[key]["debit"] += debit
        voucher_groups[key]["credit"] += credit

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
            fields=["name", "posting_date", "paid_amount", "mode_of_payment", "payment_type", "party_name", "remarks", "reference_no"]
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
                    "reference_no": m.get("reference_no", ""),
                    "items": []
                }
            details_cache[parent]["items"].append(ref)

    # 3. Batch fetch Journal Entry accounts (including reference links)
    je_names = [v[1] for v in voucher_map.keys() if v[0] == "Journal Entry"]
    if je_names:
        je_items = frappe.get_all("Journal Entry Account",
            filters={"parent": ["in", je_names]},
            fields=[
                "parent", "account",
                "debit_in_account_currency as debit",
                "credit_in_account_currency as credit",
                "party_type", "party",
                "reference_type", "reference_name",
            ]
        )
        je_docs = frappe.get_all("Journal Entry",
            filters={"name": ["in", je_names]},
            fields=["name", "posting_date", "total_debit", "user_remark", "cheque_no"]
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
                    "reference_no": m.get("cheque_no", ""),
                    "total_amount": float(m.get("total_debit", 0)),
                    "items": []
                }
            details_cache[parent]["items"].append({
                "account": item.account,
                "debit": float(item.debit or 0),
                "credit": float(item.credit or 0),
                "party_type": item.party_type or "",
                "party": item.party or "",
                "reference_type": item.reference_type or "",
                "reference_name": item.reference_name or "",
            })

    # Build entry list with running balance in first-occurrence order
    balance = opening_balance
    entries = []
    for group in voucher_groups.values():
        balance += group["debit"] - group["credit"]
        
        # Populate reference_no (linked invoice numbers)
        ref_no = group["reference_no"] # From against_voucher
        v_no = group["voucher_no"]
        v_type = group["voucher_type"]

        if v_type == "Payment Entry" and v_no in details_cache:
            refs = [i["reference_name"] for i in details_cache[v_no]["items"] if i.get("reference_name")]
            if refs:
                ref_no = ", ".join(refs)
        elif v_type == "Journal Entry" and v_no in details_cache:
            refs = [i["reference_name"] for i in details_cache[v_no]["items"] if i.get("reference_name")]
            if refs:
                ref_no = ", ".join(list(set(refs))) # unique
        
        if not ref_no and v_type in ["Payment Entry", "Journal Entry"]:
             ref_no = frappe.db.get_value(v_type, v_no, "reference_no" if v_type == "Payment Entry" else "cheque_no")

        entries.append({
            "date": group["date"],
            "voucher_type": v_type,
            "voucher_no": v_no,
            "debit": round(group["debit"], 2),
            "credit": round(group["credit"], 2),
            "balance": round(balance, 2),
            "remarks": group["remarks"],
            "reference_no": ref_no or "",
        })

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
def get_customer_ledger(customer, from_date=None, to_date=None, company=None):
    """Backward compatibility wrapper for get_ledger."""
    return get_ledger(customer, "Customer", from_date, to_date, company)

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
        base["custom_customer_name"] = doc.get("custom_customer_name") or ""
        base["custom_address"] = ", ".join(
            filter(None, [doc.get("custom_address_line1"), doc.get("custom_address_line2")])
        )
    elif voucher_type == "Purchase Invoice":
        base["items"] = [{"item_code": r.item_code, "item_name": r.item_name, "qty": float(r.qty), "rate": float(r.rate), "amount": float(r.amount), "uom": r.uom or r.stock_uom or ""} for r in doc.items]
        base["party_name"] = doc.supplier_name
        base["total_amount"] = float(doc.grand_total)
        base["outstanding_amount"] = float(doc.outstanding_amount)
        # PI stores a free-text note in the custom remarks field
        base["custom_remarks"] = doc.get("custom_remarks") or ""
    elif voucher_type == "Payment Entry":
        base["items"] = [{"reference_doctype": r.reference_doctype, "reference_name": r.reference_name, "allocated_amount": float(r.allocated_amount)} for r in doc.references]
        base["party_name"] = doc.party_name
        base["total_amount"] = float(doc.paid_amount)
        base["mode_of_payment"] = doc.mode_of_payment
        base["payment_type"] = doc.payment_type or ""
    elif voucher_type == "Journal Entry":
        base["items"] = [{"account": r.account, "debit": float(r.debit_in_account_currency), "credit": float(r.credit_in_account_currency), "party_type": r.party_type or "", "party": r.party or "", "reference_type": r.reference_type or "", "reference_name": r.reference_name or ""} for r in doc.accounts]
        base["total_amount"] = float(doc.total_debit)
        base["user_remark"] = doc.user_remark or ""
    return base

def _is_ledger_admin():
	"""True when the session user may see employee identities in the ledger."""
	if frappe.session.user in ("Administrator", "admin"):
		return True
	try:
		settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	except Exception:
		return False
	row = next((r for r in settings.user_series if r.user == frappe.session.user), None)
	return bool(row and row.admin)


def _resolve_employee_ids_in_against(entries, is_admin):
	"""`GL Entry.against` is a stored text column written at submit time. When the
	counter-side of a voucher is an Employee party, what gets stored is the raw
	employee ID (e.g. "HR-EMP-00026"), so it surfaces as an ID in the ledger's
	Against column on every non-Employee ledger.

	Admins keep the employee ID in `against` and get an `against_employees` list
	([{id, name}]) alongside it, so the frontend can reveal the name on demand.
	Everyone else gets every employee token collapsed to the literal "Employee" —
	neither the ID nor the name ever leaves the server. Non-employee tokens
	(account names, supplier/customer IDs) are left exactly as stored.
	"""
	tokens = set()
	for e in entries:
		for tok in str(e.get("against") or "").split(","):
			tok = tok.strip()
			if tok:
				tokens.add(tok)
	if not tokens:
		return

	names = {
		r.name: (r.employee_name or r.name)
		for r in frappe.get_all(
			"Employee",
			filters={"name": ["in", list(tokens)]},
			fields=["name", "employee_name"],
		)
	}
	if not names:
		return

	for e in entries:
		raw = str(e.get("against") or "")
		if not raw:
			continue
		parts = []
		found = []
		for tok in raw.split(","):
			tok = tok.strip()
			if not tok:
				continue
			if tok not in names:
				parts.append(tok)
				continue
			if is_admin:
				parts.append(tok)
				found.append({"id": tok, "name": names[tok]})
			elif "Employee" not in parts:
				# Collapse every employee token in the cell to one opaque label.
				parts.append("Employee")
		e["against"] = ", ".join(parts)
		if found:
			e["against_employees"] = found

	if not is_admin:
		# The name also rides along on party_name for employee-party rows; drop it
		# so the payload itself carries no employee identity.
		for e in entries:
			if e.get("party_type") == "Employee":
				e["party_name"] = ""
				e["party"] = ""


@frappe.whitelist()
def get_general_ledger(party_type, party, from_date=None, to_date=None, company=None):
    """Return GL entries using ERPNext's built-in General Ledger report engine."""
    if party_type == "Employee" and not _is_ledger_admin():
        frappe.throw("General ledger of employees is accessible only to administrators.")

    from erpnext.accounts.report.general_ledger.general_ledger import execute as _gl_execute
    from erpnext import get_default_company

    if not company:
        company = frappe.defaults.get_user_default("company") or get_default_company()
    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -90)

    # Resolve display label
    label = party
    if party_type == "Customer":
        label = frappe.db.get_value("Customer", party, "customer_name") or party
    elif party_type == "Supplier":
        label = frappe.db.get_value("Supplier", party, "supplier_name") or party
    elif party_type == "Employee":
        label = frappe.db.get_value("Employee", party, "employee_name") or party
    elif party_type == "Account":
        label = frappe.db.get_value("Account", party, "account_name") or party

    filters = frappe._dict({
        "company": company,
        "from_date": from_date,
        "to_date": to_date,
        "categorize_by": "Categorize by Voucher (Consolidated)",
        "show_remarks": 1,
    })
    if party_type == "Account":
        filters["account"] = [party]
    else:
        filters["party_type"] = party_type
        filters["party"] = [party]

    _columns, rows = _gl_execute(filters)

    opening_balance = 0.0
    closing_balance = 0.0
    total_debit = 0.0
    total_credit = 0.0
    entries = []

    for row in (rows or []):
        # Rows without posting_date are summary rows (Opening / Total / Closing)
        if not row.get("posting_date"):
            account_str = str(row.get("account") or "")
            if "Closing" in account_str:
                closing_balance = float(row.get("balance") or 0)
                total_debit = float(row.get("debit") or 0)
                total_credit = float(row.get("credit") or 0)
            elif "Opening" in account_str:
                opening_balance = float(row.get("balance") or 0)
            continue

        entries.append({
            "date": str(row.get("posting_date") or ""),
            "account": str(row.get("account") or ""),
            "party_type": row.get("party_type") or "",
            "party": row.get("party") or "",
            "party_name": row.get("party_name") or "",
            "voucher_type": row.get("voucher_type") or "",
            "voucher_no": row.get("voucher_no") or "",
            "against": row.get("against") or "",
            "debit": float(row.get("debit") or 0),
            "credit": float(row.get("credit") or 0),
            "balance": float(row.get("balance") or 0),
            "remarks": row.get("remarks") or "",
        })

    # ERPNext's GL report hard-excludes cancelled vouchers (is_cancelled=1), so a
    # cancelled transaction otherwise vanishes from this ledger entirely. Splice
    # cancelled vouchers back in as zero-impact rows (debit/credit=0, balance=None)
    # so the frontend can show them struck through without perturbing the running
    # balance math above or in computeWindow() on the client.
    if party_type in ("Customer", "Supplier", "Account"):
        for c in _get_cancelled_entries(party_type, party, from_date, to_date, company):
            entries.append({
                "date": c["date"],
                "account": c.get("account") or "",
                "party_type": party_type,
                "party": party,
                "party_name": label,
                "voucher_type": c["voucher_type"],
                "voucher_no": c["voucher_no"],
                "against": c.get("against") or "",
                "debit": 0.0,
                "credit": 0.0,
                "balance": None,
                "remarks": "",
                "is_cancelled": True,
                "cancelled_amount": c["amount"],
                "cancelled_is_debit": c["is_debit"],
            })
        entries.sort(key=lambda e: e["date"])

    _resolve_employee_ids_in_against(entries, _is_ledger_admin())

    # Attach voucher creation timestamps (batched per voucher type)
    vouchers_by_type = {}
    for e in entries:
        if e["voucher_type"] and e["voucher_no"]:
            vouchers_by_type.setdefault(e["voucher_type"], set()).add(e["voucher_no"])
    creation_map = {}
    for vtype, names in vouchers_by_type.items():
        for r in frappe.get_all(vtype, filters={"name": ["in", list(names)]}, fields=["name", "creation"]):
            creation_map[(vtype, r.name)] = str(r.creation)
    for e in entries:
        e["creation"] = creation_map.get((e["voucher_type"], e["voucher_no"]), "")

    # Pre-load voucher line-item detail for every entry so the frontend never needs a
    # follow-up call per row click / keyboard navigation (same pattern as the stock ledger).
    voucher_details = _batch_voucher_details(entries)
    for e in entries:
        e["detail"] = voucher_details.get(e["voucher_no"])

    return {
        "party_type": party_type,
        "party": party,
        "label": label,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(closing_balance, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "entries": entries,
    }


@frappe.whitelist()
def get_outstanding_invoices(party, party_type="Customer"):
    """Return outstanding invoices using ERPNext's Payment Ledger Entry."""
    from ssplbilling.api.payment_api import get_outstanding_invoices as _impl
    return _impl(party, party_type)

@frappe.whitelist()
def get_outstanding_purchase_invoices(supplier):
    """Return submitted Purchase Invoices with outstanding balance.
    Kept here for backward compat — canonical version in supplier_creator_api.py."""
    from ssplbilling.api.supplier_creator_api import get_outstanding_purchase_invoices as _impl
    return _impl(supplier)

@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry."""
    from ssplbilling.api.payment_api import create_payment_entry as _impl
    return _impl(data, **kwargs)

@frappe.whitelist()
def search_suppliers(query=""):
    """Kept for backward compat — canonical version in supplier_creator_api.py."""
    from ssplbilling.api.supplier_creator_api import search_suppliers as _impl
    return _impl(query)

@frappe.whitelist()
def search_accounts(query="", account_type=None):
    """Search chart of accounts."""
    from ssplbilling.api.payment_api import search_accounts as _impl
    return _impl(query, account_type)

@frappe.whitelist()
def get_warehouses(company=None):
	"""Return all enabled, non-group warehouses."""
	filters = {"disabled": 0, "is_group": 0}
	if company:
		filters["company"] = company
	return [r.name for r in frappe.get_all(
		"Warehouse",
		filters=filters,
		fields=["name"],
		order_by="name asc",
	)]


def _get_cancelled_entries(party_type, party, from_date, to_date, company):
    """Find cancelled Sales/Purchase Invoice, Payment Entry, and Journal Entry
    vouchers for this party/account + date range so they can be shown (struck through,
    zero balance impact) instead of silently vanishing from the ledger.

    Returns a list of {date, voucher_type, voucher_no, is_debit, amount, against, account}.
    `is_debit` is a best-effort guess at which column the amount would have
    landed in, matching the normal GL sign convention for that voucher type.
    """
    cancelled = []

    # 1. Sales & Purchase Invoices
    if party_type == "Customer":
        for d in frappe.get_all(
            "Sales Invoice",
            filters={
                "customer": party,
                "docstatus": 2,
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
            },
            fields=["name", "posting_date", "grand_total"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Sales Invoice",
                "voucher_no": d.name,
                "is_debit": True,
                "amount": float(d.grand_total or 0),
                "against": "",
                "account": "",
            })
    elif party_type == "Supplier":
        for d in frappe.get_all(
            "Purchase Invoice",
            filters={
                "supplier": party,
                "docstatus": 2,
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
            },
            fields=["name", "posting_date", "grand_total"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Purchase Invoice",
                "voucher_no": d.name,
                "is_debit": False,
                "amount": float(d.grand_total or 0),
                "against": "",
                "account": "",
            })
    elif party_type == "Account":
        # Sales Invoices affecting this debit_to account
        for d in frappe.get_all(
            "Sales Invoice",
            filters={
                "debit_to": party,
                "docstatus": 2,
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
            },
            fields=["name", "posting_date", "grand_total", "customer"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Sales Invoice",
                "voucher_no": d.name,
                "is_debit": True,
                "amount": float(d.grand_total or 0),
                "against": d.customer or "",
                "account": party,
            })

        # Purchase Invoices affecting this credit_to account
        for d in frappe.get_all(
            "Purchase Invoice",
            filters={
                "credit_to": party,
                "docstatus": 2,
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
            },
            fields=["name", "posting_date", "grand_total", "supplier"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Purchase Invoice",
                "voucher_no": d.name,
                "is_debit": False,
                "amount": float(d.grand_total or 0),
                "against": d.supplier or "",
                "account": party,
            })

    # 2. Payment Entries
    if party_type in ("Customer", "Supplier"):
        for d in frappe.get_all(
            "Payment Entry",
            filters={
                "party_type": party_type,
                "party": party,
                "docstatus": 2,
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
            },
            fields=["name", "posting_date", "payment_type", "paid_amount"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Payment Entry",
                "voucher_no": d.name,
                "is_debit": d.payment_type == "Pay",
                "amount": float(d.paid_amount or 0),
                "against": "",
                "account": "",
            })
    elif party_type == "Account":
        # Payment Entries where paid_from = party (money paid OUT of this account = Credit)
        for d in frappe.get_all(
            "Payment Entry",
            filters=[
                ["docstatus", "=", 2],
                ["company", "=", company],
                ["posting_date", "between", [from_date, to_date]],
                ["paid_from", "=", party],
            ],
            fields=["name", "posting_date", "paid_amount", "paid_to", "party", "party_name"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Payment Entry",
                "voucher_no": d.name,
                "is_debit": False,
                "amount": float(d.paid_amount or 0),
                "against": d.party_name or d.party or d.paid_to or "",
                "account": party,
            })

        # Payment Entries where paid_to = party (money received INTO this account = Debit)
        for d in frappe.get_all(
            "Payment Entry",
            filters=[
                ["docstatus", "=", 2],
                ["company", "=", company],
                ["posting_date", "between", [from_date, to_date]],
                ["paid_to", "=", party],
            ],
            fields=["name", "posting_date", "paid_amount", "paid_from", "party", "party_name"],
        ):
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Payment Entry",
                "voucher_no": d.name,
                "is_debit": True,
                "amount": float(d.paid_amount or 0),
                "against": d.party_name or d.party or d.paid_from or "",
                "account": party,
            })

    # 3. Journal Entries
    if party_type in ("Customer", "Supplier"):
        je_names = frappe.get_all(
            "Journal Entry",
            filters=[
                ["Journal Entry Account", "party_type", "=", party_type],
                ["Journal Entry Account", "party", "=", party],
                ["Journal Entry", "docstatus", "=", 2],
                ["Journal Entry", "company", "=", company],
                ["Journal Entry", "posting_date", "between", [from_date, to_date]],
            ],
            fields=["name", "posting_date"],
            group_by="`tabJournal Entry`.name",
        )
        for d in je_names:
            totals = frappe.db.sql(
                """
                select sum(debit_in_account_currency) as debit, sum(credit_in_account_currency) as credit
                from `tabJournal Entry Account`
                where parent = %s and party_type = %s and party = %s
                """,
                (d.name, party_type, party),
                as_dict=True,
            )
            debit = float(totals[0].debit or 0) if totals else 0.0
            credit = float(totals[0].credit or 0) if totals else 0.0
            net = debit - credit
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Journal Entry",
                "voucher_no": d.name,
                "is_debit": net >= 0,
                "amount": abs(net),
                "against": "",
                "account": "",
            })
    elif party_type == "Account":
        je_names = frappe.get_all(
            "Journal Entry",
            filters=[
                ["Journal Entry Account", "account", "=", party],
                ["Journal Entry", "docstatus", "=", 2],
                ["Journal Entry", "company", "=", company],
                ["Journal Entry", "posting_date", "between", [from_date, to_date]],
            ],
            fields=["name", "posting_date"],
            group_by="`tabJournal Entry`.name",
        )
        for d in je_names:
            totals = frappe.db.sql(
                """
                select sum(debit_in_account_currency) as debit, sum(credit_in_account_currency) as credit
                from `tabJournal Entry Account`
                where parent = %s and account = %s
                """,
                (d.name, party),
                as_dict=True,
            )
            debit = float(totals[0].debit or 0) if totals else 0.0
            credit = float(totals[0].credit or 0) if totals else 0.0
            net = debit - credit
            # Find the other accounts in the Journal Entry to show in "against"
            against_accounts = frappe.get_all(
                "Journal Entry Account",
                filters={"parent": d.name, "account": ["!=", party]},
                fields=["account"],
                limit=3
            )
            against_str = ", ".join([r.account for r in against_accounts])
            cancelled.append({
                "date": str(d.posting_date),
                "voucher_type": "Journal Entry",
                "voucher_no": d.name,
                "is_debit": net >= 0,
                "amount": abs(net),
                "against": against_str,
                "account": party,
            })

    return cancelled


def _batch_voucher_details(entries):
    """Batch-fetch header + line items for all unique vouchers in the entries list."""
    from collections import defaultdict

    by_type = defaultdict(list)
    for e in entries:
        if isinstance(e, dict):
            v_type = e.get("voucher_type")
            v_no = e.get("voucher_no")
        else:
            v_type = getattr(e, "voucher_type", None)
            v_no = getattr(e, "voucher_no", None)
        
        if v_type and v_no:
            by_type[v_type].append(v_no)

    details = {}  # voucher_no -> detail dict

    VOUCHER_MAP = {
        "Sales Invoice":    ("Sales Invoice Item",    "customer_name",  "grand_total",  "uom",        "rate"),
        "Delivery Note":    ("Delivery Note Item",    "customer_name",  "grand_total",  "uom",        "rate"),
        "Purchase Invoice": ("Purchase Invoice Item", "supplier_name",  "grand_total",  "uom",        "rate"),
        "Purchase Receipt": ("Purchase Receipt Item", "supplier_name",  "grand_total",  "uom",        "rate"),
    }

    # Extra header fields needed by the ledger detail panel, on top of the generic set above
    EXTRA_HEADER_FIELDS = {
        "Sales Invoice": ["custom_customer_name", "custom_address_line1", "custom_address_line2", "custom_remarks"],
        "Purchase Invoice": ["custom_remarks", "bill_no", "bill_date"],
    }

    for vtype, (child_dt, party_field, total_field, uom_field, rate_field) in VOUCHER_MAP.items():
        if not by_type.get(vtype):
            continue
        names = list(set(by_type[vtype]))
        extra_fields = EXTRA_HEADER_FIELDS.get(vtype, [])
        headers = {r.name: r for r in frappe.get_all(
            vtype,
            filters={"name": ["in", names]},
            fields=["name", party_field, total_field, "posting_date", *extra_fields],
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
            detail = {
                "voucher_type": vtype,
                "party_name": h.get(party_field) or "",
                "total_amount": float(h.get(total_field) or 0), "posting_date": str(h.get("posting_date") or "" ),
                "items": items_map.get(name, []),
            }
            if vtype == "Sales Invoice":
                detail["custom_customer_name"] = h.get("custom_customer_name") or ""
                detail["custom_address"] = ", ".join(
                    filter(None, [h.get("custom_address_line1"), h.get("custom_address_line2")])
                )
                detail["custom_remarks"] = h.get("custom_remarks") or ""
            elif vtype == "Purchase Invoice":
                detail["custom_remarks"] = h.get("custom_remarks") or ""
                detail["bill_no"] = h.get("bill_no") or ""
                detail["bill_date"] = str(h.get("bill_date") or "")
            details[name] = detail

    # Stock Entry
    if by_type.get("Stock Entry"):
        names = list(set(by_type["Stock Entry"]))
        headers = {r.name: r for r in frappe.get_all(
            "Stock Entry",
            filters={"name": ["in", names]},
            fields=["name", "stock_entry_type", "total_amount", "posting_date"],
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
                "total_amount": float(h.get("total_amount") or 0), "posting_date": str(h.get("posting_date") or "" ),
                "items": items_map.get(name, []),
            }

    # Stock Reconciliation
    if by_type.get("Stock Reconciliation"):
        names = list(set(by_type["Stock Reconciliation"]))
        headers = {r.name: r for r in frappe.get_all(
            "Stock Reconciliation",
            filters={"name": ["in", names]},
            fields=["name", "purpose", "posting_date", "difference_amount"],
        )}
        items_rows = frappe.get_all(
            "Stock Reconciliation Item",
            filters={"parent": ["in", names]},
            fields=["parent", "item_code", "item_name", "qty", "current_qty", "valuation_rate", "amount", "stock_uom"],
        )
        items_map = defaultdict(list)
        for r in items_rows:
            items_map[r.parent].append({
                "item_code": r.item_code,
                "item_name": r.item_name,
                "qty": float(r.qty or 0),
                "current_qty": float(r.current_qty or 0),
                "rate": float(r.valuation_rate or 0),
                "amount": float(r.amount or 0),
                "uom": r.stock_uom or "",
            })
        for name in names:
            h = headers.get(name, {})
            details[name] = {
                "voucher_type": "Stock Reconciliation",
                "party_name": h.get("purpose") or "Stock Reconciliation",
                "total_amount": float(h.get("difference_amount") or 0),
                "posting_date": str(h.get("posting_date", "")),
                "items": items_map.get(name, []),
            }

    # Payment Entry (dominant voucher type in customer/supplier GL — references, not line items)
    if by_type.get("Payment Entry"):
        names = list(set(by_type["Payment Entry"]))
        pe_refs = frappe.get_all("Payment Entry Reference",
            filters={"parent": ["in", names]},
            fields=["parent", "reference_doctype", "reference_name", "allocated_amount"],
        )
        headers = {r.name: r for r in frappe.get_all(
            "Payment Entry",
            filters={"name": ["in", names]},
            fields=["name", "posting_date", "paid_amount", "mode_of_payment", "payment_type", "party_name"],
        )}
        items_map = defaultdict(list)
        for r in pe_refs:
            items_map[r.parent].append({
                "reference_doctype": r.reference_doctype,
                "reference_name": r.reference_name,
                "allocated_amount": float(r.allocated_amount or 0),
            })
        for name in names:
            h = headers.get(name, {})
            details[name] = {
                "voucher_type": "Payment Entry",
                "party_name": h.get("party_name") or "",
                "total_amount": float(h.get("paid_amount") or 0),
                "posting_date": str(h.get("posting_date", "")),
                "mode_of_payment": h.get("mode_of_payment") or "",
                "payment_type": h.get("payment_type") or "",
                "items": items_map.get(name, []),
            }

    # Journal Entry (dominant voucher type in customer/supplier GL, alongside Payment Entry)
    if by_type.get("Journal Entry"):
        names = list(set(by_type["Journal Entry"]))
        je_items = frappe.get_all("Journal Entry Account",
            filters={"parent": ["in", names]},
            fields=[
                "parent", "account",
                "debit_in_account_currency as debit",
                "credit_in_account_currency as credit",
                "party_type", "party",
                "reference_type", "reference_name",
            ],
        )
        headers = {r.name: r for r in frappe.get_all(
            "Journal Entry",
            filters={"name": ["in", names]},
            fields=["name", "posting_date", "total_debit", "user_remark"],
        )}
        items_map = defaultdict(list)
        for r in je_items:
            items_map[r.parent].append({
                "account": r.account,
                "debit": float(r.debit or 0),
                "credit": float(r.credit or 0),
                "party_type": r.party_type or "",
                "party": r.party or "",
                "reference_type": r.reference_type or "",
                "reference_name": r.reference_name or "",
            })
        for name in names:
            h = headers.get(name, {})
            details[name] = {
                "voucher_type": "Journal Entry",
                "total_amount": float(h.get("total_debit") or 0),
                "posting_date": str(h.get("posting_date", "")),
                "user_remark": h.get("user_remark") or "",
                "items": items_map.get(name, []),
            }

    return details


@frappe.whitelist()
def get_erpnext_stock_ledger(item_code, from_date=None, to_date=None, warehouse=None, company=None):
    """Return Stock Ledger entries using ERPNext's built-in Stock Ledger report engine."""
    from erpnext.stock.report.stock_ledger.stock_ledger import execute as _sl_execute
    from erpnext import get_default_company

    company = company or frappe.defaults.get_user_default("company") or get_default_company()
    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -30)

    filters = frappe._dict({
        "company": company,
        "from_date": from_date,
        "to_date": to_date,
        "item_code": [item_code] if isinstance(item_code, str) else item_code,
        "include_uom": 1,
    })
    if warehouse:
        filters["warehouse"] = warehouse

    _columns, rows = _sl_execute(filters)

    opening_balance = 0.0
    closing_balance = 0.0
    total_in = 0.0
    total_out = 0.0
    entries = []

    # ERPNext Stock Ledger rows usually include:
    # date, voucher_type, voucher_no, warehouse, actual_qty, qty_after_transaction, stock_uom, etc.
    
    # We need to find the opening balance (first row usually contains it if there's history)
    # Actually ERPNext Stock Ledger report returns rows in chronological order.
    
    # Pre-fetch voucher details for the right panel
    voucher_details = _batch_voucher_details(rows)

    for row in (rows or []):
        qty = float(row.get("actual_qty") or 0)
        balance = float(row.get("qty_after_transaction") or 0)
        
        # If it's a summary or header row (ERPNext sometimes returns these)
        if not row.get("voucher_no") and not row.get("actual_qty"):
            continue

        entries.append({
            "date": str(row.get("date") or row.get("posting_date") or ""),
            "voucher_type": row.get("voucher_type") or "",
            "voucher_no": row.get("voucher_no") or "",
            "warehouse": row.get("warehouse") or "",
            "actual_qty": qty,
            "balance": balance,
            "stock_uom": row.get("stock_uom") or "",
            "detail": voucher_details.get(row.get("voucher_no"))
        })

        if qty > 0:
            total_in += qty
        else:
            total_out += abs(qty)

    if entries:
        # Opening = Balance of first entry - Qty of first entry
        opening_balance = entries[0]["balance"] - entries[0]["actual_qty"]
        closing_balance = entries[-1]["balance"]

    return {
        "item_code": item_code,
        "entries": entries,
        "opening_balance": round(opening_balance, 2),
        "total_in": round(total_in, 2),
        "total_out": round(total_out, 2),
        "closing_balance": round(closing_balance, 2),
    }


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

    # Opening balance: sum of qty_after_transaction for the latest entry of each warehouse before from_date
    if warehouse:
        opening_row = frappe.db.sql(
            """
            SELECT qty_after_transaction AS qty 
            FROM `tabStock Ledger Entry` 
            WHERE item_code = %s AND is_cancelled = 0 AND posting_date < %s AND warehouse = %s
            ORDER BY posting_date DESC, creation DESC 
            LIMIT 1
            """,
            [item_code, from_date, warehouse],
            as_dict=True,
        )
        opening_balance = float(opening_row[0].qty if opening_row else 0)
    else:
        # Sum of latest balances for ALL warehouses
        opening_row = frappe.db.sql(
            """
            SELECT SUM(qty) AS qty
            FROM (
                SELECT qty_after_transaction AS qty
                FROM `tabStock Ledger Entry` sle1
                WHERE item_code = %s AND is_cancelled = 0 AND posting_date < %s
                  AND creation = (
                    SELECT MAX(creation)
                    FROM `tabStock Ledger Entry` sle2
                    WHERE sle2.item_code = sle1.item_code 
                      AND sle2.is_cancelled = 0 
                      AND sle2.posting_date < %s
                      AND sle2.warehouse = sle1.warehouse
                  )
            ) sub
            """,
            [item_code, from_date, from_date],
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

    # Batch-fetch all voucher details in one go
    voucher_details = _batch_voucher_details(entries)

    running = opening_balance
    total_in = 0.0
    total_out = 0.0
    for e in entries:
        e["detail"] = voucher_details.get(e["voucher_no"])
        qty = float(e.actual_qty or 0)

        # Fix actual_qty for Stock Reconciliation if it's 0 but there was a change
        if e.voucher_type == "Stock Reconciliation" and qty == 0 and e["detail"]:
            # Find this item in the reconciliation items
            for item in e["detail"].get("items", []):
                if item["item_code"] == item_code:
                    qty = item["qty"] - item["current_qty"]
                    break
        
        running += qty
        e["balance"] = running
        e["actual_qty"] = qty
        e["date"] = str(e["date"])
        if qty > 0:
            total_in += qty
        else:
            total_out += abs(qty)

    return {
        "item_code": item_code,
        "entries": entries,
        "opening_balance": opening_balance,
        "total_in": total_in,
        "total_out": total_out,
        "closing_balance": opening_balance + total_in - total_out,
    }
