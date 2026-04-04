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
def get_sales_invoices(query="", limit=20, posting_date=None, show_unpaid=False, naming_series=None, draft_only=False):
    """List Sales Invoices for the sidebar bill panel.

    draft_only=True  → only Draft invoices (docstatus=0).
    draft_only=False → all non-cancelled invoices for the date (paid, unpaid, draft).
    """
    draft_only = frappe.parse_json(draft_only)

    filters = [["docstatus", "!=", 2], ["posting_date", "=", posting_date or frappe.utils.today()]]

    if draft_only:
        filters.append(["docstatus", "=", 0])

    if naming_series:
        filters.append(["naming_series", "=", naming_series])

    if query:
        filters.append(["customer_name", "like", f"%{query}%"])

    invoices = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["name", "customer", "customer_name", "posting_date", "grand_total", "outstanding_amount", "status", "modified", "docstatus"],
        limit=int(limit),
        order_by="modified desc",
    )

    result = []
    for inv in invoices:
        inv["grand_total"] = float(inv["grand_total"] or 0)
        inv["outstanding_amount"] = float(inv["outstanding_amount"] or 0)
        # Add item count
        inv["items_count"] = frappe.db.count("Sales Invoice Item", {"parent": inv["name"]})
        result.append(inv)

    return result

@frappe.whitelist()
def get_sales_invoice(invoice_name):
    """Fetch a Sales Invoice with its items."""
    si = frappe.get_doc("Sales Invoice", invoice_name)
    payment_mode = si.payments[0].mode_of_payment if si.payments else "Cash"
    cost_center = si.items[0].cost_center if si.items else ""

    def _actual_charge(keyword):
        for t in si.taxes:
            if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
                return float(t.tax_amount or 0)
        return 0.0

    freight_amount = _actual_charge("freight")
    packing_amount = _actual_charge("packing")
    loading_amount = _actual_charge("loading")
    other_charges_amount = _actual_charge("other")

    return {
        "name": si.name,
        "customer": si.customer,
        "customer_name": si.customer_name,
        "posting_date": str(si.posting_date),
        "naming_series": si.naming_series or "",
        "payment_mode": payment_mode,
        "discount_percentage": float(si.additional_discount_percentage or 0),
        "additional_discount_amount": float(si.discount_amount or 0),
        "freight_amount": freight_amount,
        "packing_amount": packing_amount,
        "loading_amount": loading_amount,
        "other_charges_amount": other_charges_amount,
        "grand_total": float(si.grand_total or 0),
        "outstanding_amount": float(si.outstanding_amount or 0),
        "tax_template": si.taxes_and_charges or "",
        "cost_center": cost_center or "",
        "price_list": si.selling_price_list or "",
        "docstatus": si.docstatus,
        "status": si.status,
        "items": [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "uom": item.uom or item.stock_uom or "",
                "qty": float(item.qty),
                "price_list_rate": float(item.price_list_rate or item.rate or 0),
                "rate": float(item.rate),
                "discount": float(item.discount_percentage or 0),
                "warehouse": item.warehouse or "",
                "cost_center": item.cost_center or "",
                "tax_rate": _get_item_tax_rate(item.item_code),
                "deleted": False,
            }
            for item in si.items
        ],
        "incentive_system": [
            {
                "employee": row.employee,
                "employee_name": frappe.db.get_value("Employee", row.employee, "employee_name") if row.employee else "",
                "role": row.role,
                "points": float(row.points or 0),
            }
            for row in (si.incentive_system or [])
        ],
        "advances": [
            {
                "reference_name": row.reference_name,
                "allocated_amount": float(row.allocated_amount or 0)
            }
            for row in (si.advances or [])
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
	card_amount = float(data.get("card_amount") or 0)
	discount_amount = float(data.get("discount_amount") or 0)
	is_credit = bool(data.get("is_credit"))
	posting_date = data.get("posting_date") or frappe.utils.today()

	# Explicit accounts passed from frontend
	f_cash_account = data.get("cash_account")
	f_upi_account = data.get("upi_account")
	f_card_account = data.get("card_account")
	f_discount_account = data.get("discount_account")
	card_ref_no = data.get("card_ref_no")

	si = frappe.get_doc("Sales Invoice", invoice_name)
	grand_total = float(si.grand_total)
	company = si.company

	if not is_credit:
		total_payment = cash_amount + upi_amount + card_amount + discount_amount
		# Use outstanding_amount even for Drafts if it's already reduced by Advances
		target_amount = float(si.outstanding_amount if (si.docstatus == 1 or si.outstanding_amount < si.grand_total) else grand_total)
		if total_payment < target_amount - 0.01:
			frappe.throw(f"Total payment ₹{total_payment:.2f} is less than amount ₹{target_amount:.2f}.")

	if si.docstatus == 0:
		# Update posting date if provided or default to today
		si.posting_date = posting_date
		si.posting_time = frappe.utils.nowtime()

		si.due_date = data.get("due_date") or posting_date
		if str(si.due_date) < str(si.posting_date):
			si.due_date = si.posting_date

		if si.get("payment_schedule"):
			si.payment_schedule = []
		si.submit()

	if is_credit:
		return {"invoice_name": si.name, "payment_entries": [], "grand_total": grand_total, "status": "Submitted"}

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
	card_account = f_card_account or (user_row.card if user_row else None) or _mop_account("Credit Card")
	discount_account = f_discount_account or settings.discount_account or \
		frappe.get_cached_value("Company", company, "write_off_account") or ""

	def _resolve_gl_account(name):
		"""If name is a plain account name without company tag, resolve to full Account name."""
		if not name:
			return name
		if " - " in name:
			return name  # already fully qualified
		# Try exact match first
		exact = frappe.db.get_value("Account", {"name": name, "company": company, "is_group": 0}, "name")
		if exact:
			return exact
		# Try by account_name field
		by_name = frappe.db.get_value("Account", {"account_name": name, "company": company, "is_group": 0}, "name")
		if by_name:
			return by_name
		# Try treating it as a Mode of Payment name
		via_mop = _mop_account(name)
		return via_mop or name

	cash_account     = _resolve_gl_account(cash_account)
	upi_account      = _resolve_gl_account(upi_account)
	card_account     = _resolve_gl_account(card_account)
	discount_account = _resolve_gl_account(discount_account)

	def _mop_for_account(account):
		"""Find the Mode of Payment whose default account matches, for this company."""
		return frappe.db.get_value(
			"Mode of Payment Account",
			{"default_account": account, "company": company},
			"parent",
		) or "Cash"

	def _create_pe(amount, paid_to_account, ref_no=None):
		if amount <= 0 or not paid_to_account: return None
		outstanding = frappe.db.get_value("Sales Invoice", si.name, "outstanding_amount") or 0
		allocated = min(amount, outstanding)
		mop = _mop_for_account(paid_to_account)
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.posting_date = posting_date
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
			pe.reference_date = posting_date
		if allocated > 0:
			pe.append("references", {"reference_doctype": "Sales Invoice", "reference_name": si.name, "allocated_amount": allocated})
		pe.insert(); pe.submit()
		return pe.name

	if discount_amount > 0.01:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = posting_date
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

	if card_amount > 0.01:
		pe_name = _create_pe(card_amount, card_account, ref_no=card_ref_no)
		if pe_name: payment_entries.append(pe_name)

	return {"invoice_name": si.name, "payment_entries": payment_entries, "grand_total": grand_total, "status": "Submitted"}

@frappe.whitelist()
def get_customer_unallocated_cash(customer):
	"""Returns a list of unallocated Payment Entries and Journal Entries for a customer."""
	if not customer:
		return []
	
	# 1. Payment Entries
	pe_list = frappe.get_all(
		"Payment Entry",
		filters={
			"party_type": "Customer",
			"party": customer,
			"docstatus": 1,
			"unallocated_amount": [">", 0],
		},
		fields=["name", "unallocated_amount", "posting_date", "mode_of_payment", "reference_no"],
	)
	
	results = []
	for pe in pe_list:
		results.append({
			"name": pe.name,
			"unallocated_amount": float(pe.unallocated_amount),
			"posting_date": str(pe.posting_date),
			"mode_of_payment": pe.mode_of_payment or "Cash",
			"reference_no": pe.reference_no,
			"reference_type": "Payment Entry"
		})
		
	# 2. Journal Entries (unlinked credits to Receivable accounts for this customer)
	je_list = frappe.db.sql("""
		SELECT 
			jea.parent as name, 
			(jea.credit_in_account_currency - jea.debit_in_account_currency) as unallocated_amount,
			je.posting_date,
			je.cheque_no as reference_no
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE je.docstatus = 1
		  AND jea.party = %s
		  AND jea.party_type = 'Customer'
		  AND jea.credit_in_account_currency > 0
		  AND (jea.reference_name IS NULL OR jea.reference_name = '')
	""", (customer,), as_dict=True)
	
	for je in je_list:
		# Check if it's already fully allocated by searching for GL Entries against this JE row
		# or simpler: check if outstanding is > 0 (Journal Entry doesn't have a single 'unallocated' field easily)
		# For simplicity in this specialized app, we assume if reference_name is empty in JEA, it's unallocated.
		# But we should verify if it's already used in another SI's advances.
		
		already_used = frappe.db.sql_list("""
			SELECT SUM(allocated_amount) FROM `tabSales Invoice Advance` 
			WHERE reference_type = 'Journal Entry' AND reference_name = %s
		""", (je.name,))
		
		used_amt = float(already_used[0] or 0) if already_used else 0
		available = float(je.unallocated_amount) - used_amt
		
		if available > 0.005:
			results.append({
				"name": je.name,
				"unallocated_amount": available,
				"posting_date": str(je.posting_date),
				"mode_of_payment": "Journal Entry",
				"reference_no": je.reference_no,
				"reference_type": "Journal Entry"
			})
			
	# Sort by date
	results.sort(key=lambda x: x["posting_date"])
	return results

@frappe.whitelist()
def update_invoice_advances(invoice_name, total_amount=0, allocations=None):
	"""Update the advances table. If allocations (list of dicts) is provided, use those.
	Otherwise, automatically allocate total_amount across available unallocated payments.
	"""
	si = frappe.get_doc("Sales Invoice", invoice_name)
	if si.docstatus != 0:
		frappe.throw("Advances can only be updated for Draft invoices.")

	# Update past dated bills to today
	today_str = frappe.utils.today()
	if str(si.posting_date) < today_str:
		si.posting_date = today_str
		si.due_date = today_str
		si.posting_time = frappe.utils.nowtime()

	# Double check due_date to prevent "Due Date cannot be before Posting Date"
	if str(si.due_date) < str(si.posting_date):
		si.due_date = si.posting_date

	if si.get("payment_schedule"):
		si.payment_schedule = []

	if allocations:
		if isinstance(allocations, str):
			allocations = json.loads(allocations)
		
		si.set("advances", [])
		for alloc in allocations:
			amt = float(alloc.get("allocated_amount") or 0)
			if amt <= 0.005:
				continue
				
			pe_name = alloc.get("reference_name")
			ref_type = alloc.get("reference_type") or "Payment Entry"
			
			# Verify PE/JE exists
			if ref_type == "Payment Entry":
				pe_data = frappe.db.get_value("Payment Entry", pe_name, ["unallocated_amount", "reference_no"], as_dict=True)
				if not pe_data: continue
				
				si.append("advances", {
					"reference_type": "Payment Entry",
					"reference_name": pe_name,
					"remarks": f"Allocated from {pe_name} via Cashier Desk",
					"advance_amount": pe_data.unallocated_amount,
					"allocated_amount": amt,
					"ref_no": pe_data.reference_no,
				})
			else:
				# Journal Entry
				je_data = frappe.db.get_value("Journal Entry", pe_name, ["total_debit", "cheque_no"], as_dict=True)
				if not je_data: continue
				
				si.append("advances", {
					"reference_type": "Journal Entry",
					"reference_name": pe_name,
					"remarks": f"Allocated from {pe_name} via Cashier Desk",
					"advance_amount": amt, # Use amt as placeholder for JE advance amount
					"allocated_amount": amt,
					"ref_no": je_data.cheque_no,
				})
	else:
		amount_left = float(total_amount or 0)
		if amount_left <= 0:
			si.set("advances", [])
		else:
			# Fetch fresh list of unallocated payments (now includes JEs)
			unallocated_payments = get_customer_unallocated_cash(si.customer)
			
			si.set("advances", [])
			for pe_data in unallocated_payments:
				if amount_left <= 0.005:
					break
					
				alloc_amount = min(float(pe_data["unallocated_amount"]), amount_left)
				
				si.append("advances", {
					"reference_type": pe_data["reference_type"],
					"reference_name": pe_data["name"],
					"remarks": f"Allocated from {pe_data['name']} via Cashier Desk",
					"advance_amount": pe_data["unallocated_amount"],
					"allocated_amount": alloc_amount,
					"ref_no": pe_data["reference_no"],
				})
				amount_left -= alloc_amount

	si.save(ignore_permissions=True)
	return {
		"status": "success", 
		"grand_total": float(si.grand_total), 
		"outstanding": float(si.outstanding_amount),
		"posting_date": str(si.posting_date),
		"due_date": str(si.due_date)
	}

