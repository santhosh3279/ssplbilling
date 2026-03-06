import json
import frappe


def _get_item_tax_rate(item_code):
    """Return the effective tax rate (%) for an item from its Item Tax Template.

    Looks at the Item's taxes child table, picks the most recent template whose
    valid_from is on or before today, then sums the rates from Item Tax Template Detail.
    Returns 0.0 if no template is configured.
    """
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
def get_item_details(item_code, price_list="Standard Selling", warehouse=None):
    """Look up item by code or barcode. Returns item details + stock + rate."""
    # Try barcode first
    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": item_code}, "parent")
    if barcode_item:
        item_code = barcode_item

    if not frappe.db.exists("Item", item_code):
        return {"found": False, "item_code": item_code}

    item = frappe.get_cached_doc("Item", item_code)
    wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

    # Get selling rate from price list
    rate = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list, "selling": 1},
        "price_list_rate",
    ) or item.standard_rate or 0

    # Get stock qty
    stock_qty = 0
    if wh:
        stock_qty = (
            frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty")
            or 0
        )

    return {
        "found": True,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "uom": item.stock_uom,
        "rate": float(rate),
        "stock_qty": float(stock_qty),
        "warehouse": wh,
        "tax_rate": _get_item_tax_rate(item.item_code),
    }


@frappe.whitelist()
def search_items(query, price_list="Standard Selling"):
    """Search items by code, name, or barcode. Returns list of matches."""
    if not query or len(query) < 1:
        return []

    # Check barcode
    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": query}, "parent")
    if barcode_item:
        return [get_item_details(barcode_item, price_list)]

    items = frappe.get_all(
        "Item",
        or_filters={
            "item_code": ["like", f"%{query}%"],
            "item_name": ["like", f"%{query}%"],
        },
        filters={"disabled": 0, "is_sales_item": 1},
        fields=["item_code", "item_name", "stock_uom as uom", "standard_rate"],
        limit=20,
        order_by="item_name asc",
    )

    # Enrich with rate and stock
    wh = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
    for item in items:
        item["rate"] = float(
            frappe.db.get_value(
                "Item Price",
                {"item_code": item["item_code"], "price_list": price_list, "selling": 1},
                "price_list_rate",
            )
            or item.get("standard_rate")
            or 0
        )
        item["stock_qty"] = float(
            frappe.db.get_value("Bin", {"item_code": item["item_code"], "warehouse": wh}, "actual_qty")
            or 0
        ) if wh else 0
        item["warehouse"] = wh
        item["found"] = True
        item["tax_rate"] = _get_item_tax_rate(item["item_code"])

    return items


@frappe.whitelist()
def get_item_insight(item_code, customer=None, warehouse=None, price_list=None):
    """Get stock across warehouses, last purchase by customer, all price list rates."""
    wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

    # Basic item info
    item_info = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True) or {}

    # All warehouse stock
    stock = frappe.get_all(
        "Bin",
        filters={"item_code": item_code},
        fields=["warehouse", "actual_qty", "reserved_qty", "projected_qty"],
    )
    for s in stock:
        s["actual_qty"] = float(s["actual_qty"] or 0)
        s["reserved_qty"] = float(s["reserved_qty"] or 0)

    # Previous purchases by customer
    previous_purchases = []
    if customer:
        rows = frappe.db.sql(
            """
            SELECT si.name, si.posting_date as date, sii.rate, sii.qty, sii.discount_percentage as discount
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE sii.item_code = %s AND si.customer = %s AND si.docstatus = 1
            ORDER BY si.posting_date DESC, si.creation DESC
            LIMIT 5
            """,
            (item_code, customer),
            as_dict=True,
        )
        for r in rows:
            previous_purchases.append({
                "name": r.name,
                "date": str(r.date),
                "rate": float(r.rate),
                "qty": float(r.qty),
                "discount": float(r.discount or 0),
            })

    # All selling price lists
    price_lists = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "selling": 1},
        fields=["price_list as name", "price_list_rate as rate", "currency"],
        order_by="price_list_rate asc",
    )
    for pl in price_lists:
        pl["rate"] = float(pl["rate"] or 0)

    return {
        "item_name": item_info.get("item_name"),
        "uom": item_info.get("stock_uom"),
        "stock": stock,
        "previous_purchases": previous_purchases,
        "price_lists": price_lists,
    }


@frappe.whitelist()
def search_customers(query):
    """Search customers by name or ID, including mobile and current balance."""
    if not query or len(query) < 1:
        return []

    customers = frappe.get_all(
        "Customer",
        or_filters={
            "name": ["like", f"%{query}%"],
            "customer_name": ["like", f"%{query}%"],
        },
        filters={"disabled": 0},
        fields=["name", "customer_name", "mobile_no"],
        limit=20,
        order_by="customer_name asc",
    )

    for c in customers:
        # Get current balance from GL Entry
        balance = frappe.db.sql(
            """
            SELECT SUM(debit) - SUM(credit) as balance
            FROM `tabGL Entry`
            WHERE party_type = 'Customer' AND party = %s AND is_cancelled = 0
            """,
            (c.name,),
            as_dict=True,
        )
        c["balance"] = float(balance[0].balance or 0) if balance else 0.0

    return customers


@frappe.whitelist()
def quick_create_customer(data=None, **kwargs):
    """Create a Customer with basic details. Accepts JSON data."""
    if not data:
        data = frappe.form_dict
        # Remove cmd key if present
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k != "cmd"}

    if isinstance(data, str):
        data = json.loads(data)

    customer_name = data.get("customer_name", "").strip()
    if not customer_name:
        frappe.throw("Customer name is required")

    cust = frappe.new_doc("Customer")
    cust.customer_name = customer_name
    cust.customer_type = data.get("customer_type") or "Individual"
    cust.customer_group = data.get("customer_group") or frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups"
    cust.territory = data.get("territory") or frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"

    if data.get("mobile"):
        cust.mobile_no = data["mobile"]

    if data.get("email"):
        cust.email_id = data["email"]

    if data.get("gstin"):
        cust.gstin = data["gstin"]

    cust.insert(ignore_permissions=True)

    # Create address if provided
    if data.get("address_line1") or data.get("city"):
        addr = frappe.new_doc("Address")
        addr.address_title = customer_name
        addr.address_type = "Billing"
        addr.address_line1 = data.get("address_line1", "")
        addr.city = data.get("city", "")
        addr.state = data.get("state", "")
        addr.pincode = data.get("pincode", "")
        addr.country = data.get("country", "India")
        addr.phone = data.get("mobile", "")
        addr.email_id = data.get("email", "")
        if data.get("gstin"):
            addr.gstin = data["gstin"]
        addr.append("links", {"link_doctype": "Customer", "link_name": cust.name})
        addr.insert(ignore_permissions=True)

    return {
        "name": cust.name,
        "customer_name": cust.customer_name,
    }


@frappe.whitelist()
def create_sales_invoice(data=None, **kwargs):
    """Create Sales Invoice in Draft."""
    # frappe-ui submit() may send data in different ways
    if not data:
        data = frappe.form_dict.get("data")
    if not data:
        # Try reading from entire form_dict (frappe-ui may spread the JSON as form fields)
        fd = dict(frappe.form_dict)
        fd.pop("cmd", None)
        if fd.get("customer"):
            data = fd
    if not data:
        frappe.throw("No invoice data received. form_dict keys: " + str(list(frappe.form_dict.keys())))
    if isinstance(data, str):
        data = json.loads(data)

    if not data.get("customer"):
        frappe.throw("Customer is required")
    if not data.get("items"):
        frappe.throw("At least one item is required")

    # Create Sales Invoice
    si = frappe.new_doc("Sales Invoice")
    si.customer = data["customer"]
    si.posting_date = data.get("date", frappe.utils.today())
    si.naming_series = data.get("naming_series", "SINV-.YY.-")
    si.update_stock = 1
    if data.get("cost_center"):
        si.cost_center = data["cost_center"]

    if data.get("discount_percentage"):
        si.additional_discount_percentage = float(data["discount_percentage"])

    for item in data["items"]:
        disc = float(item.get("discount_percentage") or 0)
        price_list_rate = float(item.get("price_list_rate") or item["rate"])
        rate = float(item["rate"]) if not disc else round(price_list_rate * (1 - disc / 100), 9)
        row = {
            "item_code": item["item_code"],
            "qty": float(item["qty"]),
            "price_list_rate": price_list_rate,
            "discount_percentage": disc,
            "rate": rate,
        }
        if item.get("warehouse"):
            row["warehouse"] = item["warehouse"]
        cost_center = item.get("cost_center") or data.get("cost_center") or ""
        if cost_center:
            row["cost_center"] = cost_center
        si.append("items", row)

    # Apply tax template if provided
    if data.get("tax_template"):
        si.taxes_and_charges = data["tax_template"]
        try:
            tmpl = frappe.get_doc("Sales Taxes and Charges Template", data["tax_template"])
            for tax in tmpl.taxes:
                si.append("taxes", {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": tax.rate,
                    "cost_center": data.get("cost_center") or tax.cost_center or "",
                })
        except Exception:
            pass  # Non-fatal: ERPNext will still save without tax rows

    si.insert()

    result = {
        "invoice_name": si.name,
        "grand_total": float(si.grand_total),
        "status": "Draft",
        "payment_mode": data.get("payment_mode", "Cash"),
    }

    return result


@frappe.whitelist()
def get_naming_series():
    """Get available naming series for Sales Invoice.

    Checks three sources in order:
    1. Property Setter – written by Document Naming Settings (Frappe v14+)
    2. DocType meta field options – the JSON / DB definition
    3. Hard-coded fallback
    """
    # 1. Property Setter (Document Naming Settings writes here)
    try:
        prop_value = frappe.db.get_value(
            "Property Setter",
            {
                "doc_type": "Sales Invoice",
                "field_name": "naming_series",
                "property": "options",
            },
            "value",
        )
        if prop_value:
            series = [s.strip() for s in prop_value.split("\n") if s.strip()]
            if series:
                return series
    except Exception:
        pass

    # 2. DocType meta field options
    try:
        meta = frappe.get_meta("Sales Invoice")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            series = [s.strip() for s in series_field.options.split("\n") if s.strip()]
            if series:
                return series
    except Exception:
        pass

    return ["SINV-.YY.-"]


@frappe.whitelist()
def get_next_bill_no(naming_series="SINV-.YY.-"):
    """Get the next number in the naming series."""
    try:
        from frappe.model.naming import parse_naming_series
        return parse_naming_series(naming_series)
    except Exception:
        return naming_series + "???"


@frappe.whitelist()
def get_sales_invoices(query="", limit=20, posting_date=None):
    """List Sales Invoices for modification. Searchable by invoice name or customer name.
    Optionally filtered by posting_date (YYYY-MM-DD). Defaults to today when not supplied."""
    date_filter = posting_date or frappe.utils.today()
    kwargs = dict(
        filters={"posting_date": date_filter},
        fields=["name", "customer", "customer_name", "posting_date", "grand_total", "status", "modified", "docstatus"],
        limit=int(limit),
        order_by="modified desc",
    )
    if query:
        kwargs["or_filters"] = {
            "name": ["like", f"%{query}%"],
            "customer_name": ["like", f"%{query}%"],
        }
    invoices = frappe.get_all("Sales Invoice", **kwargs)
    for inv in invoices:
        inv["grand_total"] = float(inv["grand_total"] or 0)
    return invoices


@frappe.whitelist()
def get_sales_invoice(invoice_name):
    """Fetch a Sales Invoice with its items for frontend viewing/editing."""
    si = frappe.get_doc("Sales Invoice", invoice_name)

    payment_mode = "Cash"
    if si.payments:
        payment_mode = si.payments[0].mode_of_payment or "Cash"

    # Cost center: take from first item row (all items share the same CC in our flow)
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
	"""Submit a Draft Sales Invoice and create Payment Entry(ies).

	Supported payment modes: Cash, UPI, Bank, Credit (no PE), Discount (JE write-off).
	Account mappings are read from SSPL Billing Settings for the invoice's naming_series.

	Expected payload::

	    {
	        "invoice_name":   "SINV-2026-001",
	        "cash_amount":    500.0,
	        "upi_amount":     200.0,
	        "bank_amount":    0.0,
	        "discount_amount": 50.0,
	        "is_credit":      false,
	    }
	"""
	if not data:
		data = frappe.form_dict.get("data") or dict(frappe.form_dict)
		if isinstance(data, dict):
			data.pop("cmd", None)
	if isinstance(data, str):
		data = json.loads(data)

	invoice_name = data.get("invoice_name")
	cash_amount = float(data.get("cash_amount") or 0)
	upi_amount = float(data.get("upi_amount") or 0)
	bank_amount = float(data.get("bank_amount") or 0)
	discount_amount = float(data.get("discount_amount") or 0)
	is_credit = bool(data.get("is_credit"))

	if not invoice_name:
		frappe.throw("invoice_name is required")

	si = frappe.get_doc("Sales Invoice", invoice_name)
	if si.docstatus != 0:
		frappe.throw(f"Invoice {invoice_name} is not in Draft state and cannot be submitted here.")

	grand_total = float(si.grand_total)

	# Validate totals (skip for credit — AR stays open)
	if not is_credit:
		total_payment = cash_amount + upi_amount + bank_amount + discount_amount
		if total_payment < grand_total - 0.01:
			frappe.throw(
				f"Total payment ₹{total_payment:.2f} is less than invoice amount ₹{grand_total:.2f}. "
				"Please collect the full amount before submitting."
			)

	# Submit the Sales Invoice
	si.submit()

	# Credit mode: leave AR open, no payment entries needed
	if is_credit:
		return {
			"invoice_name": si.name,
			"payment_entries": [],
			"grand_total": grand_total,
			"status": "Submitted",
		}

	company = si.company
	payment_entries = []

	# Resolve series-specific account mappings from SSPL Billing Settings
	series_cfg = None
	try:
		settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
		series_cfg = next(
			(r for r in settings.billing_series if r.series == si.naming_series), None
		)
	except Exception:
		pass

	def _find_account(name):
		"""Return a valid Account name for *name*, trying with company abbreviation suffix if needed."""
		if not name:
			return None
		if frappe.db.exists("Account", name):
			return name
		# ERPNext appends " - <abbr>" to account names; try that variant
		abbr = frappe.get_cached_value("Company", company, "abbr") or ""
		if abbr:
			suffixed = f"{name} - {abbr}"
			if frappe.db.exists("Account", suffixed):
				return suffixed
		return None

	def _resolve_account(series_field, mop_fallback):
		"""Return account: series config first, then Mode of Payment, then company default."""
		if series_cfg and getattr(series_cfg, series_field, None):
			resolved = _find_account(getattr(series_cfg, series_field))
			if resolved:
				return resolved
		acct = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": mop_fallback, "company": company},
			"default_account",
		)
		return acct or frappe.get_cached_value("Company", company, "default_cash_account") or ""

	def _get_mop_for_account(account, fallback):
		"""Reverse-lookup: find which Mode of Payment has *account* as its default for this company."""
		if not account:
			return fallback
		mop = frappe.db.get_value(
			"Mode of Payment Account",
			{"default_account": account, "company": company},
			"parent",
		)
		return mop or fallback

	def _create_pe(amount, mode_of_payment, paid_to_account):
		"""Create and submit a Payment Entry for *amount* against the submitted SI."""
		if amount <= 0 or not paid_to_account:
			return None

		company_currency = frappe.get_cached_value("Company", company, "default_currency") or "INR"
		account_currency = (
			frappe.get_cached_value("Account", paid_to_account, "account_currency") or company_currency
		)
		outstanding = float(
			frappe.db.get_value("Sales Invoice", si.name, "outstanding_amount") or amount
		)

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.posting_date = si.posting_date
		pe.company = company
		pe.mode_of_payment = mode_of_payment
		pe.party_type = "Customer"
		pe.party = si.customer
		pe.paid_from = si.debit_to
		pe.paid_from_account_currency = company_currency
		pe.paid_to = paid_to_account
		pe.paid_to_account_currency = account_currency
		pe.paid_amount = amount
		pe.received_amount = amount
		pe.source_exchange_rate = 1
		pe.target_exchange_rate = 1

		pe.append(
			"references",
			{
				"reference_doctype": "Sales Invoice",
				"reference_name": si.name,
				"due_date": si.due_date,
				"total_amount": grand_total,
				"outstanding_amount": outstanding,
				"allocated_amount": min(amount, outstanding),
			},
		)

		pe.insert()
		pe.submit()
		return pe.name

	# Discount: Journal Entry (DR write-off account, CR AR account)
	if discount_amount > 0.01:
		write_off_acct = frappe.get_cached_value("Company", company, "write_off_account") or ""
		if not write_off_acct:
			frappe.throw(
				"No write-off account configured for company. "
				"Please set it under Company > Accounts Settings."
			)
		outstanding = float(
			frappe.db.get_value("Sales Invoice", si.name, "outstanding_amount") or 0
		)
		cost_center = (series_cfg.cost_center if series_cfg and series_cfg.cost_center else "") or ""
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = si.posting_date
		je.company = company
		je.user_remark = f"Discount on {si.name}"
		je.append(
			"accounts",
			{
				"account": write_off_acct,
				"debit_in_account_currency": discount_amount,
				"cost_center": cost_center,
			},
		)
		je.append(
			"accounts",
			{
				"account": si.debit_to,
				"credit_in_account_currency": discount_amount,
				"party_type": "Customer",
				"party": si.customer,
				"reference_type": "Sales Invoice",
				"reference_name": si.name,
			},
		)
		je.insert()
		je.submit()
		payment_entries.append(je.name)

	# Cash payment
	if cash_amount > 0.01:
		cash_acct = _resolve_account("cash_account", "Cash")
		cash_mop = _get_mop_for_account(cash_acct, "Cash")
		pe_name = _create_pe(cash_amount, cash_mop, cash_acct)
		if pe_name:
			payment_entries.append(pe_name)

	# UPI payment
	if upi_amount > 0.01:
		upi_acct = _resolve_account("upi", "UPI")
		upi_mop = _get_mop_for_account(upi_acct, "UPI")
		pe_name = _create_pe(upi_amount, upi_mop, upi_acct)
		if pe_name:
			payment_entries.append(pe_name)

	# Bank transfer
	if bank_amount > 0.01:
		bank_acct = _resolve_account("bank", "Bank Transfer")
		bank_mop = _get_mop_for_account(bank_acct, "Bank Transfer")
		pe_name = _create_pe(bank_amount, bank_mop, bank_acct)
		if pe_name:
			payment_entries.append(pe_name)

	return {
		"invoice_name": si.name,
		"payment_entries": payment_entries,
		"grand_total": grand_total,
		"status": "Submitted",
	}


@frappe.whitelist()
def update_sales_invoice(data=None, **kwargs):
    """Update an existing Draft Sales Invoice."""
    if not data:
        data = frappe.form_dict.get("data")
    if isinstance(data, str):
        data = json.loads(data)

    invoice_name = data.get("invoice_name")
    if not invoice_name:
        frappe.throw("invoice_name is required")

    si = frappe.get_doc("Sales Invoice", invoice_name)
    if si.docstatus != 0:
        frappe.throw(f"Invoice {invoice_name} is not a Draft and cannot be modified.")

    si.customer = data["customer"]
    si.posting_date = data.get("date", frappe.utils.today())
    if data.get("naming_series"):
        si.naming_series = data["naming_series"]
    if data.get("cost_center"):
        si.cost_center = data["cost_center"]
    si.additional_discount_percentage = float(data.get("discount_percentage", 0))
    si.update_stock = 1

    # Apply tax template (clear existing taxes first, then re-apply)
    if data.get("tax_template"):
        si.taxes_and_charges = data["tax_template"]
        si.taxes = []
        try:
            tmpl = frappe.get_doc("Sales Taxes and Charges Template", data["tax_template"])
            for tax in tmpl.taxes:
                si.append("taxes", {
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": tax.rate,
                    "cost_center": data.get("cost_center") or tax.cost_center or "",
                })
        except Exception:
            pass

    si.items = []
    for item in data["items"]:
        disc = float(item.get("discount_percentage") or 0)
        price_list_rate = float(item.get("price_list_rate") or item["rate"])
        rate = float(item["rate"]) if not disc else round(price_list_rate * (1 - disc / 100), 9)
        row = {
            "item_code": item["item_code"],
            "qty": float(item["qty"]),
            "price_list_rate": price_list_rate,
            "discount_percentage": disc,
            "rate": rate,
        }
        if item.get("warehouse"):
            row["warehouse"] = item["warehouse"]
        cost_center = item.get("cost_center") or data.get("cost_center") or ""
        if cost_center:
            row["cost_center"] = cost_center
        si.append("items", row)

    si.save()

    return {
        "invoice_name": si.name,
        "grand_total": float(si.grand_total),
    }


# ─── Customer Ledger ──────────────────────────────────────────────────────────


@frappe.whitelist()
def get_customer_ledger(customer, from_date=None, to_date=None):
    """Return GL Entry rows for a customer with a running balance.

    Args:
        customer  : Customer name / ID (party field in GL Entry)
        from_date : ISO date "YYYY-MM-DD", defaults to 90 days ago
        to_date   : ISO date "YYYY-MM-DD", defaults to today

    Returns a dict with keys: customer, customer_name, from_date, to_date,
    opening_balance, closing_balance, total_debit, total_credit, entries[].
    Each entry has: date, voucher_type, voucher_no, debit, credit, balance, remarks.
    """
    if not customer:
        frappe.throw("customer is required")

    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_days(to_date, -90)

    customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer

    # Opening balance: sum of all GL entries before from_date
    opening_rows = frappe.db.sql(
        """
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND is_cancelled = 0
          AND posting_date < %s
        """,
        (customer, from_date),
        as_dict=True,
    )
    opening_balance = float(opening_rows[0].balance if opening_rows else 0)

    # Detail rows for the date range
    entries_raw = frappe.db.sql(
        """
        SELECT
            posting_date,
            voucher_type,
            voucher_no,
            debit,
            credit,
            remarks
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
          AND party = %s
          AND is_cancelled = 0
          AND posting_date >= %s
          AND posting_date <= %s
        ORDER BY posting_date ASC, creation ASC
        LIMIT 500
        """,
        (customer, from_date, to_date),
        as_dict=True,
    )

    balance = opening_balance
    entries = []
    total_debit = 0.0
    total_credit = 0.0

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

    return {
        "customer": customer,
        "customer_name": customer_name,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(balance, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "entries": entries,
    }


@frappe.whitelist()
def get_voucher_detail(voucher_type, voucher_no):
    """Return key fields from a voucher for the customer ledger detail panel.

    Supports: Sales Invoice, Payment Entry, Journal Entry.
    Returns a common shape plus type-specific line items.
    """
    if not frappe.has_permission(voucher_type, "read", voucher_no):
        frappe.throw(f"No permission to read {voucher_type} {voucher_no}", frappe.PermissionError)

    try:
        doc = frappe.get_doc(voucher_type, voucher_no)
    except frappe.DoesNotExistError:
        frappe.throw(f"{voucher_type} {voucher_no} not found")

    base = {
        "voucher_type": voucher_type,
        "voucher_no": voucher_no,
        "posting_date": str(doc.posting_date),
        "status": doc.get("status") or "",
        "remarks": doc.get("remarks") or doc.get("user_remark") or "",
    }

    if voucher_type == "Sales Invoice":
        base.update(
            {
                "party": doc.customer,
                "party_name": doc.customer_name,
                "total_amount": float(doc.grand_total or 0),
                "outstanding_amount": float(doc.outstanding_amount or 0),
                "items": [
                    {
                        "item_code": r.item_code,
                        "item_name": r.item_name,
                        "qty": float(r.qty),
                        "rate": float(r.rate),
                        "amount": float(r.amount),
                        "uom": r.uom or r.stock_uom or "",
                    }
                    for r in doc.items
                ],
            }
        )
    elif voucher_type == "Payment Entry":
        base.update(
            {
                "party": doc.party,
                "party_name": doc.party_name,
                "total_amount": float(doc.paid_amount or 0),
                "mode_of_payment": doc.mode_of_payment or "",
                "payment_type": doc.payment_type or "",
                "items": [
                    {
                        "reference_doctype": r.reference_doctype,
                        "reference_name": r.reference_name,
                        "allocated_amount": float(r.allocated_amount or 0),
                    }
                    for r in doc.references
                ],
            }
        )
    elif voucher_type == "Journal Entry":
        base.update(
            {
                "party": "",
                "party_name": "",
                "total_amount": float(doc.total_debit or 0),
                "items": [
                    {
                        "account": r.account,
                        "debit": float(r.debit_in_account_currency or 0),
                        "credit": float(r.credit_in_account_currency or 0),
                        "cost_center": r.cost_center or "",
                    }
                    for r in doc.accounts
                ],
            }
        )
    else:
        base.update({"party": "", "party_name": "", "total_amount": 0, "items": []})

    return base


# ─── Payment Entry (direct) ───────────────────────────────────────────────────


@frappe.whitelist()
def get_outstanding_invoices(customer):
    """Return submitted Sales Invoices with outstanding balance for a customer."""
    rows = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "posting_date", "grand_total", "outstanding_amount", "naming_series"],
        order_by="posting_date desc",
        limit=50,
    )
    return [
        {
            "name": r.name,
            "posting_date": str(r.posting_date),
            "grand_total": float(r.grand_total),
            "outstanding_amount": float(r.outstanding_amount),
            "naming_series": r.naming_series or "",
        }
        for r in rows
    ]


@frappe.whitelist()
def create_payment_entry(data=None, **kwargs):
    """Create and submit a Payment Entry.

    Supports all three payment types:
    - Receive  (receipt from customer)
    - Pay      (payment to supplier)
    - Internal Transfer (contra between cash/bank accounts)

    Expected payload::

        {
            "payment_type":      "Receive" | "Pay" | "Internal Transfer",
            "party_type":        "Customer" | "Supplier" | "",
            "party":             "CUST-001",         # empty for Internal Transfer
            "amount":            5000.0,
            "mode_of_payment":   "Cash",             # Cash | UPI | Bank Transfer
            "date":              "2026-03-04",
            "reference_no":      "",                 # optional
            "reference_date":    "",                 # optional
            "remarks":           "",                 # optional
            "invoice_name":      "",                 # optional – SI or PI to allocate
            "invoice_doctype":   "Sales Invoice",    # defaults per payment_type
            "paid_from_account": "",                 # optional explicit override
            "paid_to_account":   "",                 # optional explicit override
        }
    """
    if not data:
        data = frappe.form_dict.get("data") or dict(frappe.form_dict)
        if isinstance(data, dict):
            data.pop("cmd", None)
    if isinstance(data, str):
        data = json.loads(data)

    payment_type = data.get("payment_type") or "Receive"
    party_type = data.get("party_type") or (
        "Customer" if payment_type == "Receive" else "Supplier" if payment_type == "Pay" else ""
    )
    party = data.get("party") or data.get("customer") or ""
    amount = float(data.get("amount") or 0)
    mode_of_payment = data.get("mode_of_payment") or "Cash"
    posting_date = data.get("date") or frappe.utils.today()
    reference_no = data.get("reference_no") or ""
    reference_date = data.get("reference_date") or posting_date
    remarks = data.get("remarks") or ""
    invoice_name = data.get("invoice_name") or ""
    invoice_doctype = data.get("invoice_doctype") or (
        "Sales Invoice" if payment_type == "Receive" else "Purchase Invoice"
    )
    paid_from_override = data.get("paid_from_account") or ""
    paid_to_override = data.get("paid_to_account") or ""

    if payment_type != "Internal Transfer" and not party:
        frappe.throw("party is required")
    if amount <= 0:
        frappe.throw("amount must be greater than zero")

    company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )
    company_currency = frappe.get_cached_value("Company", company, "default_currency") or "INR"

    def _find_account(name):
        if not name:
            return None
        if frappe.db.exists("Account", name):
            return name
        abbr = frappe.get_cached_value("Company", company, "abbr") or ""
        if abbr:
            suffixed = f"{name} - {abbr}"
            if frappe.db.exists("Account", suffixed):
                return suffixed
        return None

    def _mop_account():
        acct = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": company},
            "default_account",
        )
        return acct or frappe.get_cached_value("Company", company, "default_cash_account") or ""

    # Resolve paid_from and paid_to based on payment_type
    if payment_type == "Receive":
        paid_from = paid_from_override or (
            frappe.db.get_value("Account", {"account_type": "Receivable", "company": company}, "name")
            or frappe.get_cached_value("Company", company, "default_receivable_account")
            or ""
        )
        paid_to = paid_to_override or _mop_account()
    elif payment_type == "Pay":
        paid_from = paid_from_override or _mop_account()
        paid_to = paid_to_override or (
            frappe.db.get_value("Account", {"account_type": "Payable", "company": company}, "name")
            or frappe.get_cached_value("Company", company, "default_payable_account")
            or ""
        )
    else:  # Internal Transfer
        paid_from = paid_from_override or _mop_account()
        paid_to = paid_to_override
        if not paid_to:
            frappe.throw("paid_to_account is required for Internal Transfer (Contra).")

    if not paid_from:
        frappe.throw("Could not resolve source account.")
    if not paid_to:
        frappe.throw(f"Could not resolve paid-to account for mode '{mode_of_payment}'.")

    from_currency = frappe.get_cached_value("Account", paid_from, "account_currency") or company_currency
    to_currency = frappe.get_cached_value("Account", paid_to, "account_currency") or company_currency

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.posting_date = posting_date
    pe.company = company
    if payment_type != "Internal Transfer":
        pe.mode_of_payment = mode_of_payment
    pe.party_type = party_type
    pe.party = party
    pe.paid_from = paid_from
    pe.paid_from_account_currency = from_currency
    pe.paid_to = paid_to
    pe.paid_to_account_currency = to_currency
    pe.paid_amount = amount
    pe.received_amount = amount
    pe.source_exchange_rate = 1
    pe.target_exchange_rate = 1
    if reference_no:
        pe.reference_no = reference_no
        pe.reference_date = reference_date
    if remarks:
        pe.remarks = remarks

    if invoice_name and payment_type != "Internal Transfer":
        outstanding = float(frappe.db.get_value(invoice_doctype, invoice_name, "outstanding_amount") or 0)
        inv_grand = float(frappe.db.get_value(invoice_doctype, invoice_name, "grand_total") or 0)
        inv_due = frappe.db.get_value(invoice_doctype, invoice_name, "due_date")
        pe.append(
            "references",
            {
                "reference_doctype": invoice_doctype,
                "reference_name": invoice_name,
                "due_date": inv_due,
                "total_amount": inv_grand,
                "outstanding_amount": outstanding,
                "allocated_amount": min(amount, outstanding),
            },
        )

    pe.insert()
    pe.submit()

    return {
        "payment_entry": pe.name,
        "party": party,
        "amount": amount,
        "payment_type": payment_type,
        "mode_of_payment": mode_of_payment,
    }


@frappe.whitelist()
def search_suppliers(query=""):
    """Search suppliers by name."""
    filters = [["supplier_name", "like", f"%{query}%"]] if query else []
    return frappe.get_all(
        "Supplier",
        filters=filters,
        fields=["name", "supplier_name"],
        limit=30,
        order_by="supplier_name asc",
    )


@frappe.whitelist()
def search_accounts(query="", account_type=None):
    """Search chart of accounts, optionally filtered by account_type."""
    filters = [["disabled", "=", 0], ["is_group", "=", 0]]
    if account_type == "CashBank":
        filters.append(["account_type", "in", ["Cash", "Bank"]])
    elif account_type:
        filters.append(["account_type", "=", account_type])
    if query:
        filters.append(["account_name", "like", f"%{query}%"])
    return frappe.get_all(
        "Account",
        filters=filters,
        fields=["name", "account_name", "account_type", "root_type"],
        limit=25,
        order_by="account_name asc",
    )


@frappe.whitelist()
def get_outstanding_purchase_invoices(supplier):
    """Return submitted Purchase Invoices with outstanding balance for a supplier."""
    rows = frappe.get_all(
        "Purchase Invoice",
        filters={"supplier": supplier, "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "posting_date", "grand_total", "outstanding_amount"],
        order_by="posting_date desc",
        limit=50,
    )
    return [
        {
            "name": r.name,
            "posting_date": str(r.posting_date),
            "grand_total": float(r.grand_total),
            "outstanding_amount": float(r.outstanding_amount),
        }
        for r in rows
    ]


@frappe.whitelist()
def create_journal_entry(data=None, **kwargs):
    """Create and submit a Journal Entry.

    Expected payload::

        {
            "date":         "2026-03-04",
            "voucher_type": "Journal Entry",  # or Contra Entry, etc.
            "remarks":      "",
            "accounts": [
                {"account": "Cash - NCK", "debit": 5000, "credit": 0,
                 "party_type": "", "party": ""},
                {"account": "Bank - NCK", "debit": 0, "credit": 5000},
            ]
        }
    """
    if not data:
        data = frappe.form_dict.get("data") or dict(frappe.form_dict)
        if isinstance(data, dict):
            data.pop("cmd", None)
    if isinstance(data, str):
        data = json.loads(data)

    posting_date = data.get("date") or frappe.utils.today()
    voucher_type = data.get("voucher_type") or "Journal Entry"
    remarks = data.get("remarks") or ""
    accounts = data.get("accounts") or []

    if not accounts:
        frappe.throw("At least one account row is required.")

    total_dr = sum(float(r.get("debit") or 0) for r in accounts)
    total_cr = sum(float(r.get("credit") or 0) for r in accounts)
    if abs(total_dr - total_cr) > 0.01:
        frappe.throw(
            f"Debit (₹{total_dr:.2f}) and Credit (₹{total_cr:.2f}) totals must match."
        )

    company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = voucher_type
    je.posting_date = posting_date
    je.company = company
    if remarks:
        je.user_remark = remarks

    for row in accounts:
        account = row.get("account") or ""
        if not account:
            continue
        entry = {
            "account": account,
            "debit_in_account_currency": float(row.get("debit") or 0),
            "credit_in_account_currency": float(row.get("credit") or 0),
        }
        if row.get("party_type") and row.get("party"):
            entry["party_type"] = row["party_type"]
            entry["party"] = row["party"]
        if row.get("cost_center"):
            entry["cost_center"] = row["cost_center"]
        je.append("accounts", entry)

    je.insert()
    je.submit()

    return {"journal_entry": je.name, "total_debit": total_dr}