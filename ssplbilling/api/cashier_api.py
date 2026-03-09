import json
import frappe

def _get_item_tax_rate(item_code):
    """Return the effective tax rate (%) for an item from its Item Tax Template."""
    today = frappe.utils.today()
    tax_rows = frappe.get_all(
        "Item Tax",
        filters={"parent": item_code, "parenttype": "Item"},
        fields=["item_tax_template", "valid_from"],
        order_by="valid_from desc",
    )
    template_name = None
    for row in tax_rows:
        if not row.valid_from or str(row.valid_from) <= today:
            template_name = row.item_tax_template
            break

    if not template_name:
        return 0.0

    details = frappe.get_all(
        "Item Tax Template Detail",
        filters={"parent": template_name},
        fields=["tax_rate"],
    )
    return float(sum(d.tax_rate or 0 for d in details)) / 2

@frappe.whitelist()
def get_sales_invoices(query="", limit=20, posting_date=None, show_unpaid=False):
    """List Draft (and optionally Unpaid Submitted) Sales Invoices for cashiering."""
    date_filter = posting_date or frappe.utils.today()
    show_unpaid = frappe.parse_json(show_unpaid)
    
    filters = [
        ["posting_date", "=", date_filter],
        ["status", "!=", "Cancelled"]
    ]
    
    if show_unpaid:
        filters.append(["docstatus", "<", 2])
    else:
        filters.append(["docstatus", "=", 0])
    
    invoices = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["name", "customer", "customer_name", "posting_date", "grand_total", "outstanding_amount", "status", "modified", "docstatus"],
        limit=int(limit),
        order_by="modified desc",
    )
    
    # Filter out submitted invoices that are fully paid if show_unpaid is True
    result = []
    for inv in invoices:
        if inv.docstatus == 0 or (inv.docstatus == 1 and float(inv.outstanding_amount or 0) > 0.01):
            inv["grand_total"] = float(inv["grand_total"] or 0)
            inv["outstanding_amount"] = float(inv["outstanding_amount"] or 0)
            result.append(inv)
            
    if query:
        query = query.lower()
        result = [
            inv for inv in result 
            if query in inv.name.lower() or query in (inv.customer_name or "").lower()
        ]
        
    return result[:int(limit)]

@frappe.whitelist()
def get_sales_invoice(invoice_name):
    """Fetch a Sales Invoice with its items."""
    si = frappe.get_doc("Sales Invoice", invoice_name)
    payment_mode = si.payments[0].mode_of_payment if si.payments else "Cash"
    cost_center = si.items[0].cost_center if si.items else ""

    return {
        "name": si.name,
        "customer": si.customer,
        "customer_name": si.customer_name,
        "posting_date": str(si.posting_date),
        "naming_series": si.naming_series or "",
        "payment_mode": payment_mode,
        "discount_percentage": float(si.additional_discount_percentage or 0),
        "grand_total": float(si.grand_total or 0),
        "tax_template": si.taxes_and_charges or "",
        "cost_center": cost_center or "",
        "docstatus": si.docstatus,
        "status": si.status,
        "items": [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "uom": item.uom or item.stock_uom or "",
                "qty": float(item.qty),
                "rate": float(item.rate),
                "warehouse": item.warehouse or "",
                "cost_center": item.cost_center or "",
                "tax_rate": _get_item_tax_rate(item.item_code),
                "deleted": False,
            }
            for item in si.items
        ],
    }

@frappe.whitelist()
def submit_invoice_with_payment(data=None, **kwargs):
	"""Submit a Sales Invoice and create Payment Entries."""
	if not data:
		data = frappe.form_dict.get("data") or dict(frappe.form_dict)
		if isinstance(data, dict): data.pop("cmd", None)
	if isinstance(data, str): data = json.loads(data)

	invoice_name = data.get("invoice_name")
	cash_amount = float(data.get("cash_amount") or 0)
	upi_amount = float(data.get("upi_amount") or 0)
	bank_amount = float(data.get("bank_amount") or 0)
	discount_amount = float(data.get("discount_amount") or 0)
	is_credit = bool(data.get("is_credit"))

	# Explicit accounts passed from frontend
	f_cash_account = data.get("cash_account")
	f_upi_account = data.get("upi_account")
	f_bank_account = data.get("bank_account")
	f_discount_account = data.get("discount_account")
	bank_ref_no = data.get("bank_ref_no")

	si = frappe.get_doc("Sales Invoice", invoice_name)
	grand_total = float(si.grand_total)
	company = si.company

	if not is_credit:
		total_payment = cash_amount + upi_amount + bank_amount + discount_amount
		target_amount = float(si.outstanding_amount if si.docstatus == 1 else grand_total)
		if total_payment < target_amount - 0.01:
			frappe.throw(f"Total payment ₹{total_payment:.2f} is less than amount ₹{target_amount:.2f}.")

	if si.docstatus == 0:
		si.due_date = data.get("due_date") or frappe.utils.today()
		if si.get("payment_schedule"):
			si.payment_schedule = []
		si.submit()

	if is_credit:
		return {"invoice_name": si.name, "payment_entries": [], "grand_total": grand_total, "status": "Submitted"}

	today = frappe.utils.today()
	payment_entries = []

	# --- Resolve accounts from user_series in SSPL Billing Settings ---
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	user_row = next((r for r in (settings.user_series or []) if r.user == frappe.session.user), None)

	def _mop_account(mop_name):
		"""Fallback: account linked to a Mode of Payment for this company."""
		return frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": mop_name, "company": company},
			"default_account",
		) or ""

	cash_account = f_cash_account or (user_row.cash if user_row else None) or _mop_account("Cash")
	upi_account = f_upi_account or (user_row.upi if user_row else None) or _mop_account("UPI")
	bank_account = f_bank_account or (user_row.bank_account if user_row else None) or _mop_account("Bank Transfer")
	discount_account = f_discount_account or settings.discount_account or \
		frappe.get_cached_value("Company", company, "write_off_account") or ""

	def _mop_for_account(account):
		"""Find the Mode of Payment whose default account matches, for this company."""
		return frappe.db.get_value(
			"Mode of Payment Account",
			{"default_account": account, "company": company},
			"parent",
		) or "Cash"

	def _create_pe(amount, paid_to_account, ref_no=None):
		if amount <= 0 or not paid_to_account: return None
		mop = _mop_for_account(paid_to_account)
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.posting_date = today
		pe.company = company
		pe.mode_of_payment = mop
		pe.party_type = "Customer"
		pe.party = si.customer
		pe.paid_from = si.debit_to
		pe.paid_to = paid_to_account
		pe.paid_amount = amount
		pe.received_amount = amount
		if ref_no:
			pe.reference_no = ref_no
			pe.reference_date = today
		pe.append("references", {"reference_doctype": "Sales Invoice", "reference_name": si.name, "allocated_amount": amount})
		pe.insert(); pe.submit()
		return pe.name

	if discount_amount > 0.01:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = today
		je.company = company
		je.append("accounts", {"account": discount_account, "debit_in_account_currency": discount_amount})
		je.append("accounts", {"account": si.debit_to, "credit_in_account_currency": discount_amount, "party_type": "Customer", "party": si.customer, "reference_type": "Sales Invoice", "reference_name": si.name})
		je.insert(); je.submit()
		payment_entries.append(je.name)

	if cash_amount > 0.01:
		pe_name = _create_pe(cash_amount, cash_account)
		if pe_name: payment_entries.append(pe_name)

	if upi_amount > 0.01:
		pe_name = _create_pe(upi_amount, upi_account)
		if pe_name: payment_entries.append(pe_name)

	if bank_amount > 0.01:
		pe_name = _create_pe(bank_amount, bank_account, ref_no=bank_ref_no)
		if pe_name: payment_entries.append(pe_name)

	return {"invoice_name": si.name, "payment_entries": payment_entries, "grand_total": grand_total, "status": "Submitted"}
