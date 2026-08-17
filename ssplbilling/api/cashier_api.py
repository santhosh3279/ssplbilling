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
def get_sales_invoices(query="", limit=20, posting_date=None, naming_series=None, draft_only=False, company=None):
    """List Sales Invoices for the sidebar bill panel."""
    draft_only = frappe.parse_json(draft_only)

    filters = [["docstatus", "!=", 2]]

    if company:
        filters.append(["company", "=", company])

    # If no search query and not draft_only, restrict by date
    if not query and not draft_only:
        filters.append(["posting_date", "=", posting_date or frappe.utils.today()])

    if draft_only:
        filters.append(["docstatus", "=", 0])
    else:
        # If showing submitted bills, only show those with an outstanding balance
        filters.append(["outstanding_amount", ">", 0.01])

    if query:
        # When searching, we don't filter by specific series, 
        # but we MUST still restrict to allowed series for security.
        from ssplbilling.api.dashboard_api import get_allowed_series
        res = get_allowed_series(doctype="Sales Invoice")
        allowed = res.get("allowed_series") if isinstance(res, dict) else res
        if allowed:
            filters.append(["naming_series", "in", allowed])
    else:
        if naming_series:
            if isinstance(naming_series, str) and "," in naming_series:
                naming_series = [s.strip() for s in naming_series.split(",") if s.strip()]
            
            if isinstance(naming_series, (list, tuple)):
                filters.append(["naming_series", "in", naming_series])
            else:
                filters.append(["naming_series", "=", naming_series])
        else:
            from ssplbilling.api.dashboard_api import get_allowed_series
            res = get_allowed_series(doctype="Sales Invoice")
            allowed = res.get("allowed_series") if isinstance(res, dict) else res
            if allowed:
                filters.append(["naming_series", "in", allowed])

    if query:
        # Create a flexible bill number search (e.g., "EO141" -> "%EO%141%")
        # We split by transitions between letters and digits
        import re
        flexible_query = "%" + "%".join(re.findall(r'[A-Za-z]+|\d+', query)) + "%"

        or_filters = [
            ["name", "like", flexible_query],
            ["customer_name", "like", f"%{query}%"],
            ["custom_customer_name", "like", f"%{query}%"]
        ]
        
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            or_filters=or_filters,
            fields=["name", "customer", "customer_name", "posting_date", "posting_time", "grand_total", "rounded_total", "outstanding_amount", "status", "modified", "docstatus", "custom_customer_name", "mop"],
            limit=int(limit),
            order_by="name desc",
        )
    else:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "customer", "customer_name", "posting_date", "posting_time", "grand_total", "rounded_total", "outstanding_amount", "status", "modified", "docstatus", "custom_customer_name", "mop"],
            limit=int(limit),
            order_by="name desc",
        )

    result = []
    for inv in invoices:
        inv["grand_total"] = float(inv["grand_total"] or 0)
        inv["rounded_total"] = float(inv.get("rounded_total") or inv["grand_total"] or 0)
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

    # Fetch linked Payment Entries & Journal Entries
    payments = []
    pe_references = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_doctype": "Sales Invoice", "reference_name": invoice_name, "docstatus": ["!=", 2]},
        fields=["parent", "allocated_amount"]
    )
    if pe_references:
        pe_names = [r.parent for r in pe_references]
        pes = frappe.get_all(
            "Payment Entry",
            filters={"name": ["in", pe_names]},
            fields=["name", "posting_date", "mode_of_payment", "reference_no", "paid_amount", "docstatus", "paid_to"]
        )
        pe_alloc_map = {r.parent: r.allocated_amount for r in pe_references}
        for pe in pes:
            payments.append({
                "name": pe.name,
                "type": "Payment Entry",
                "mode_of_payment": pe.mode_of_payment,
                "posting_date": str(pe.posting_date),
                "reference_no": pe.reference_no or "",
                "amount": float(pe_alloc_map.get(pe.name, pe.paid_amount) or 0),
                "docstatus": pe.docstatus,
                "account": pe.paid_to or ""
            })

    je_accounts = frappe.get_all(
        "Journal Entry Account",
        filters={"reference_type": "Sales Invoice", "reference_name": invoice_name, "docstatus": ["!=", 2]},
        fields=["parent", "credit_in_account_currency", "debit_in_account_currency"]
    )
    if je_accounts:
        je_names = [r.parent for r in je_accounts]
        jes = frappe.get_all(
            "Journal Entry",
            filters={"name": ["in", je_names]},
            fields=["name", "posting_date", "cheque_no", "docstatus", "user_remark"]
        )
        for je in jes:
            je_row = next((r for r in je_accounts if r.parent == je.name), None)
            amount = 0.0
            if je_row:
                amount = je_row.credit_in_account_currency or je_row.debit_in_account_currency or 0.0
            
            # Find the account not referencing this invoice in the Journal Entry
            je_rows = frappe.get_all(
                "Journal Entry Account",
                filters={"parent": je.name},
                fields=["account", "reference_name"]
            )
            opp_account = ""
            for row in je_rows:
                if row.reference_name != invoice_name:
                    opp_account = row.account
                    break
            if not opp_account and je_rows:
                opp_account = je_rows[0].account

            payments.append({
                "name": je.name,
                "type": "Journal Entry",
                "mode_of_payment": "Discount / Adjustment" if "discount" in (je.user_remark or "").lower() else "Journal Entry",
                "posting_date": str(je.posting_date),
                "reference_no": je.cheque_no or "",
                "amount": float(amount),
                "docstatus": je.docstatus,
                "account": opp_account
            })

    for p in (si.payments or []):
        if p.amount > 0:
            payments.append({
                "name": si.name,
                "type": "Sales Invoice Payment",
                "mode_of_payment": p.mode_of_payment,
                "posting_date": str(si.posting_date),
                "reference_no": p.account or "",
                "amount": float(p.amount),
                "docstatus": si.docstatus,
                "account": p.account or ""
            })

    existing_names = {p["name"] for p in payments}
    for adv in (si.advances or []):
        if adv.reference_name and adv.reference_name not in existing_names:
            if adv.reference_type == "Payment Entry":
                pe = frappe.db.get_value("Payment Entry", adv.reference_name, ["posting_date", "mode_of_payment", "reference_no", "docstatus", "paid_to"], as_dict=True)
                if pe:
                    payments.append({
                        "name": adv.reference_name,
                        "type": "Payment Entry",
                        "mode_of_payment": pe.mode_of_payment,
                        "posting_date": str(pe.posting_date),
                        "reference_no": pe.reference_no or "",
                        "amount": float(adv.allocated_amount or 0),
                        "docstatus": pe.docstatus,
                        "account": pe.paid_to or ""
                    })
            elif adv.reference_type == "Journal Entry":
                je = frappe.db.get_value("Journal Entry", adv.reference_name, ["posting_date", "cheque_no", "docstatus", "user_remark"], as_dict=True)
                if je:
                    je_rows = frappe.get_all(
                        "Journal Entry Account",
                        filters={"parent": adv.reference_name},
                        fields=["account", "reference_name"]
                    )
                    opp_account = ""
                    for row in je_rows:
                        if row.reference_name != invoice_name:
                            opp_account = row.account
                            break
                    if not opp_account and je_rows:
                        opp_account = je_rows[0].account

                    payments.append({
                        "name": adv.reference_name,
                        "type": "Journal Entry",
                        "mode_of_payment": "Discount / Adjustment" if "discount" in (je.user_remark or "").lower() else "Journal Entry",
                        "posting_date": str(je.posting_date),
                        "reference_no": je.cheque_no or "",
                        "amount": float(adv.allocated_amount or 0),
                        "docstatus": je.docstatus,
                        "account": opp_account
                    })

    def _actual_charge(keyword):
        for t in si.taxes:
            if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
                return float(t.tax_amount or 0)
        return 0.0

    freight_amount = _actual_charge("freight")
    packing_amount = _actual_charge("packing")
    loading_amount = _actual_charge("loading") or _actual_charge("tax collected")
    other_charges_amount = _actual_charge("other")

    is_inclusive = 0
    if si.taxes:
        if any(t.included_in_print_rate for t in si.taxes):
            is_inclusive = 1

    # Fetch state from billing address
    party_state = ""
    if si.customer_address:
        party_state = frappe.db.get_value("Address", si.customer_address, "state") or ""

    return {
        "name": si.name,
        "customer": si.customer,
        "customer_name": si.customer_name,
        "state": party_state,
        "posting_date": str(si.posting_date),
        "posting_time": str(si.posting_time) if si.posting_time else "",
        "naming_series": si.naming_series or "",
        "payment_mode": payment_mode,
        "discount_percentage": float(si.additional_discount_percentage or 0),
        "additional_discount_amount": float(si.discount_amount or 0),
        "freight_amount": freight_amount,
        "packing_amount": packing_amount,
        "loading_amount": loading_amount,
        "other_charges_amount": other_charges_amount,
        "grand_total": float(si.grand_total or 0),
        "rounded_total": float(si.rounded_total or si.grand_total or 0),
        "outstanding_amount": float(si.outstanding_amount or 0),
        "tax_template": si.taxes_and_charges or "",
        "is_inclusive": is_inclusive,
        "is_return": frappe.utils.cint(si.is_return),
        "customer_rate_multiplier": frappe.utils.cint(si.get("customer_rate_multiplier") or 0),
        "cost_center": cost_center or "",
        "price_list": si.selling_price_list or "",
        "warehouse": si.get("set_warehouse") or (si.items[0].warehouse if si.items else ""),
        "income_account": si.items[0].income_account if si.items else "",
        "mop": si.get("mop") or "Cash",
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
                "income_account": item.income_account or "",
                "cost_center": item.cost_center or "",
                "tax_rate": _get_item_tax_rate(item.item_code),
                "is_free_item": frappe.utils.cint(item.get("is_free_item")),
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
            for row in (si.get("incentive_system") or [])
        ],
        "advances": [
            {
                "reference_name": row.reference_name,
                "allocated_amount": float(row.allocated_amount or 0)
            }
            for row in (si.advances or [])
        ],
        "custom_customer_name": si.get("custom_customer_name") or "",
        "custom_address_line1": si.get("custom_address_line1") or "",
        "custom_address_line2": si.get("custom_address_line2") or "",
        "custom_mobile_number": si.get("custom_mobile_number") or "",
        "custom_remarks": si.get("custom_remarks") or "",
        "payments": payments,
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
	credit_amount = float(data.get("credit_amount") or 0)
	is_credit = bool(data.get("is_credit"))
	posting_date = data.get("posting_date") or frappe.utils.today()

	# Explicit accounts passed from frontend
	f_cash_account = data.get("cash_account")
	f_upi_account = data.get("upi_account")
	f_card_account = data.get("card_account")
	f_discount_account = data.get("discount_account")
	card_ref_no = data.get("card_ref_no")

	si = frappe.get_doc("Sales Invoice", invoice_name)
	grand_total = float(si.rounded_total or si.grand_total or 0)
	company = si.company
	cost_center = data.get("cost_center") or si.get("cost_center")

	if not is_credit:
		total_payment = cash_amount + upi_amount + card_amount + discount_amount + credit_amount
		# Use outstanding_amount even for Drafts if it's already reduced by Advances
		target_amount = float(si.outstanding_amount if (si.docstatus == 1 or si.outstanding_amount < si.grand_total) else grand_total)
		if total_payment < target_amount - 0.01:
			frappe.throw(f"Total payment ₹{total_payment:.2f} is less than amount ₹{target_amount:.2f}.")

	if si.docstatus == 0:
		# Update posting date if provided or default to today
		# si.posting_date = posting_date
		# si.posting_time = frappe.utils.nowtime()

		si.due_date = data.get("due_date") or posting_date
		if str(si.due_date) < str(si.posting_date):
			si.due_date = si.posting_date

		if si.get("payment_schedule"):
			si.payment_schedule = []

		si.custom_remarks = data.get("custom_remarks") or ""

		# --- Handle Sales Invoice/Purchase Invoice Advances (Credit/Debit Notes) ---
		# Standard reconcile_against_document (called during SI.submit) fails for these types in v16.
		special_advances = []
		if si.get("advances"):
			special_advances = [
				adv for adv in si.advances 
				if adv.reference_type in ["Sales Invoice", "Purchase Invoice"]
			]
			if special_advances:
				si.advances = [
					adv for adv in si.advances 
					if adv.reference_type not in ["Sales Invoice", "Purchase Invoice"]
				]

		si.submit()

		# Reconcile special advances manually after submission
		if special_advances:
			from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import reconcile_dr_cr_note
			
			reconcile_args = []
			for adv in special_advances:
				# Use 'credit_in_account_currency' for Sales Invoice (new SI gets credited)
				# For PI, it might be different but reconcile_dr_cr_note handles it based on voucher_type
				reconcile_args.append(frappe._dict({
					"voucher_type": adv.reference_type,
					"voucher_no": adv.reference_name,
					"allocated_amount": adv.allocated_amount,
					"unadjusted_amount": adv.advance_amount,
					"dr_or_cr": "credit_in_account_currency" if si.doctype == "Sales Invoice" else "debit_in_account_currency",
					"account": si.debit_to if si.doctype == "Sales Invoice" else si.credit_to,
					"party_type": "Customer" if si.doctype == "Sales Invoice" else "Supplier",
					"party": si.customer if si.doctype == "Sales Invoice" else si.supplier,
					"against_voucher_type": si.doctype,
					"against_voucher": si.name,
					"currency": si.currency,
					"exchange_rate": si.conversion_rate,
					"cost_center": si.cost_center,
					"company": si.company,
					"difference_amount": 0.0
				}))
			
			if reconcile_args:
				reconcile_dr_cr_note(reconcile_args, si.company)

	mirrored = False
	if is_credit:
		# Mirror credit bill if naming series matches configuration in Automatic Entries
		try:
			from ssplbilling.api.automatic_entries_api import mirror_bill
			msi = mirror_bill(si)
			if msi:
				mirrored = True
		except Exception:
			frappe.log_error(title="Automatic Entries: mirror credit bill failed", message=frappe.get_traceback())

		return {"invoice_name": si.name, "payment_entries": [], "grand_total": grand_total, "status": "Submitted", "mirrored": mirrored}

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

	original_discount_je = None
	original_cash_pe = None
	original_upi_pe = None
	original_card_pe = None

	if discount_amount > 0.01:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = posting_date
		je.company = company
		je.append("accounts", {
			"account": discount_account,
			"debit_in_account_currency": discount_amount,
			"cost_center": cost_center
		})
		je.append("accounts", {
			"account": si.debit_to,
			"credit_in_account_currency": discount_amount,
			"party_type": "Customer",
			"party": si.customer,
			"reference_type": "Sales Invoice",
			"reference_name": si.name,
			"cost_center": cost_center
		})
		je.insert(); je.submit()
		payment_entries.append(je.name)
		original_discount_je = je.name

	if cash_amount > 0.01:
		pe_name = _create_pe(cash_amount, cash_account)
		if pe_name:
			payment_entries.append(pe_name)
			original_cash_pe = pe_name

	if upi_amount > 0.01:
		pe_name = _create_pe(upi_amount, upi_account)
		if pe_name:
			payment_entries.append(pe_name)
			original_upi_pe = pe_name

	if card_amount > 0.01:
		pe_name = _create_pe(card_amount, card_account, ref_no=card_ref_no)
		if pe_name:
			payment_entries.append(pe_name)
			original_card_pe = pe_name

	# Mirror bill and payment entries if naming series matches configuration in Automatic Entries
	try:
		from ssplbilling.api.automatic_entries_api import mirror_bill
		from ssplbilling.api.cashier_mirroring_api import mirror_payments
		msi = mirror_bill(si)
		if msi:
			mirrored = True
			mirror_payments(
				msi,
				cash_amount=cash_amount,
				upi_amount=upi_amount,
				card_amount=card_amount,
				discount_amount=discount_amount,
				cash_account=cash_account,
				upi_account=upi_account,
				card_account=card_account,
				discount_account=discount_account,
				card_ref_no=card_ref_no,
				original_cash_pe=original_cash_pe,
				original_upi_pe=original_upi_pe,
				original_card_pe=original_card_pe,
				original_discount_je=original_discount_je,
				cost_center=cost_center,
			)
	except Exception:
		frappe.log_error(title="Automatic Entries: mirror bill and payments failed", message=frappe.get_traceback())

	return {"invoice_name": si.name, "payment_entries": payment_entries, "grand_total": grand_total, "status": "Submitted", "mirrored": mirrored}

@frappe.whitelist()
def get_customer_unallocated_cash(customer, invoice_name=None):
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
		fields=["name", "unallocated_amount", "posting_date", "mode_of_payment", "reference_no", "paid_amount", "remarks", "payment_type"],
	)

	results = []
	for pe in pe_list:
		results.append({
			"name": pe.name,
			"unallocated_amount": float(pe.unallocated_amount),
			"total_amount": float(pe.paid_amount),
			"posting_date": str(pe.posting_date),
			"mode_of_payment": pe.mode_of_payment or "Cash",
			"reference_no": pe.reference_no,
			"reference_type": "Payment Entry",
			"remarks": pe.remarks,
			"payment_type": pe.payment_type
		})

	# 2. Journal Entries (unlinked credits to Receivable accounts for this customer)
	# We must restrict to rows whose account is a Receivable-type account so that
	# ERPNext's reconcile_against_document can balance the GL map on invoice submit.
	je_list = frappe.db.sql("""
		SELECT
			jea.parent as name,
			jea.name as reference_row,
			(jea.credit_in_account_currency - jea.debit_in_account_currency) as unallocated_amount,
			je.total_amount,
			je.posting_date,
			je.cheque_no as reference_no,
			je.user_remark as remarks
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		JOIN `tabAccount` acc ON acc.name = jea.account
		WHERE je.docstatus = 1
		  AND jea.party = %s
		  AND jea.party_type = 'Customer'
		  AND jea.credit_in_account_currency > 0
		  AND (jea.reference_name IS NULL OR jea.reference_name = '')
		  AND acc.account_type = 'Receivable'
	""", (customer,), as_dict=True)

	for je in je_list:
		# Check if it's already used in another SI's advances.
		# Exclude current invoice if provided.
		query = """
			SELECT SUM(allocated_amount) FROM `tabSales Invoice Advance` 
			WHERE reference_type = 'Journal Entry' AND reference_name = %s
			  AND reference_row = %s
		"""
		params = [je.name, je.reference_row]
		if invoice_name:
			query += " AND parent != %s"
			params.append(invoice_name)

		already_used = frappe.db.sql_list(query, tuple(params))

		used_amt = float(already_used[0] or 0) if already_used else 0
		available = float(je.unallocated_amount) - used_amt

		if available > 0.005:
			results.append({
				"name": je.name,
				"reference_row": je.reference_row,
				"unallocated_amount": available,
				"total_amount": float(je.total_amount),
				"posting_date": str(je.posting_date),
				"mode_of_payment": "Journal Entry",
				"reference_no": je.reference_no,
				"reference_type": "Journal Entry",
				"remarks": je.remarks
			})

	# 3. Sales Invoice (Returns / Credit Notes)
	si_list = frappe.db.sql("""
		SELECT 
			name, posting_date, grand_total, outstanding_amount,
			remarks
		FROM `tabSales Invoice`
		WHERE docstatus = 1 AND customer = %s
		  AND outstanding_amount < -0.005
	""", (customer,), as_dict=True)

	for si in si_list:
		results.append({
			"name": si.name,
			"unallocated_amount": abs(float(si.outstanding_amount)),
			"total_amount": abs(float(si.grand_total)),
			"posting_date": str(si.posting_date),
			"mode_of_payment": "Credit Note",
			"reference_no": si.name,
			"reference_type": "Sales Invoice",
			"remarks": si.remarks
		})

	# 4. Purchase Invoice (Returns / Debit Notes) - if customer is also a supplier
	pi_list = frappe.db.sql("""
		SELECT 
			name, posting_date, grand_total, outstanding_amount,
			remarks, supplier
		FROM `tabPurchase Invoice`
		WHERE docstatus = 1 
		  AND supplier = %s
		  AND outstanding_amount < -0.005
	""", (customer,), as_dict=True)

	for pi in pi_list:
		results.append({
			"name": pi.name,
			"unallocated_amount": abs(float(pi.outstanding_amount)),
			"total_amount": abs(float(pi.grand_total)),
			"posting_date": str(pi.posting_date),
			"mode_of_payment": "Debit Note",
			"reference_no": pi.name,
			"reference_type": "Purchase Invoice",
			"remarks": pi.remarks
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
	# today_str = frappe.utils.today()
	# if str(si.posting_date) < today_str:
	# 	si.posting_date = today_str
	# 	si.due_date = today_str
	# 	si.posting_time = frappe.utils.nowtime()

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
			
			# Verify PE/JE/SI exists
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
			elif ref_type == "Sales Invoice":
				# Return Invoice / Credit Note
				si_data = frappe.db.get_value("Sales Invoice", pe_name, ["outstanding_amount"], as_dict=True)
				if not si_data: continue

				# advance_amount must be the full net credit (negative outstanding)
				full_credit = abs(float(si_data.outstanding_amount))

				si.append("advances", {
					"reference_type": "Sales Invoice",
					"reference_name": pe_name,
					"remarks": f"Allocated from Return {pe_name} via Cashier Desk",
					"advance_amount": full_credit,
					"allocated_amount": amt,
					"ref_no": pe_name,
				})
			elif ref_type == "Purchase Invoice":
				# Purchase Return / Debit Note
				pi_data = frappe.db.get_value("Purchase Invoice", pe_name, ["outstanding_amount"], as_dict=True)
				if not pi_data: continue

				full_credit = abs(float(pi_data.outstanding_amount))

				si.append("advances", {
					"reference_type": "Purchase Invoice",
					"reference_name": pe_name,
					"remarks": f"Allocated from Debit Note {pe_name} via Cashier Desk",
					"advance_amount": full_credit,
					"allocated_amount": amt,
					"ref_no": pe_name,
				})
			else:
				# Journal Entry
				# Use provided reference_row or find the first unlinked receivable row for this customer in the JV
				ref_row_name = alloc.get("reference_row")
				
				if ref_row_name:
					je_row = frappe.db.get_value("Journal Entry Account", {
						"name": ref_row_name,
						"parent": pe_name,
						"party_type": "Customer",
						"party": si.customer,
					}, ["name", "credit_in_account_currency", "debit_in_account_currency"], as_dict=True)
				else:
					je_row = frappe.db.get_value("Journal Entry Account", {
						"parent": pe_name,
						"party_type": "Customer",
						"party": si.customer,
						"credit_in_account_currency": [">", 0],
						"reference_name": ("in", ["", None])
					}, ["name", "credit_in_account_currency", "debit_in_account_currency"], as_dict=True)
				
				if not je_row: continue
				
				# advance_amount must be the full net credit of the JE row (credit - debit).
				# ERPNext's reconcile_against_document uses this to build balanced GL entries;
				# it tracks other invoices' allocations from the same row independently.
				# Setting advance_amount to a reduced "available" value causes a GL imbalance.
				full_credit = float(je_row.credit_in_account_currency) - float(je_row.debit_in_account_currency)

				# Guard: don't allocate more than what's actually unallocated
				already_used = frappe.db.sql("""
					SELECT COALESCE(SUM(allocated_amount), 0) FROM `tabSales Invoice Advance`
					WHERE reference_type = 'Journal Entry'
					  AND reference_name = %s
					  AND reference_row = %s
					  AND parent != %s
				""", (pe_name, je_row.name, si.name))[0][0] or 0

				available = full_credit - float(already_used)
				if amt > available + 0.01:
					amt = round(available, 2)
				if amt <= 0.005:
					continue

				je_data = frappe.db.get_value("Journal Entry", pe_name, ["cheque_no"], as_dict=True)

				si.append("advances", {
					"reference_type": "Journal Entry",
					"reference_name": pe_name,
					"reference_row": je_row.name,  # CRITICAL for JV reconciliation
					"remarks": f"Allocated from {pe_name} via Cashier Desk",
					"advance_amount": full_credit,   # full net credit — not reduced by other invoices
					"allocated_amount": amt,
					"ref_no": je_data.cheque_no if je_data else "",
				})
	else:
		amount_left = float(total_amount or 0)
		if amount_left <= 0:
			si.set("advances", [])
		else:
			# Fetch fresh list of unallocated payments (now includes JEs)
			unallocated_payments = get_customer_unallocated_cash(si.customer, invoice_name=si.name)
			
			si.set("advances", [])
			for pe_data in unallocated_payments:
				if amount_left <= 0.005:
					break
					
				alloc_amount = min(float(pe_data["unallocated_amount"]), amount_left)
				
				si.append("advances", {
					"reference_type": pe_data["reference_type"],
					"reference_name": pe_data["name"],
					"reference_row": pe_data.get("reference_row"),
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
		"due_date": str(si.due_date),
		"advances": [{
			"reference_type": adv.reference_type,
			"reference_name": adv.reference_name,
			"remarks": adv.remarks,
			"advance_amount": float(adv.advance_amount),
			"allocated_amount": float(adv.allocated_amount),
			"ref_no": adv.ref_no,
			"reference_row": adv.reference_row
		} for adv in si.get("advances")]
	}

