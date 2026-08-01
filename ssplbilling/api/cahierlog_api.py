import frappe


@frappe.whitelist()
def get_cash_ledger_balance(account, date=None):
	"""Return the current balance (or opening balance for a date) of a cash/bank account."""
	if not account:
		return {"balance": 0.0}

	condition = ""
	params = [account]
	if date:
		condition = " AND posting_date < %s"
		params.append(date)

	balance = frappe.db.sql(
		f"""
		SELECT IFNULL(SUM(debit) - SUM(credit), 0)
		FROM `tabGL Entry`
		WHERE account = %s
		  AND is_cancelled = 0
		  {condition}
		""",
		tuple(params),
	)
	return {"balance": float(balance[0][0]) if balance else 0.0}


@frappe.whitelist()
def get_opening_total(date):
	"""Return the Opening cash total for the current user on a given date."""
	return get_cahier_totals(date, op_type="Opening")


@frappe.whitelist()
def get_cahier_totals(date, op_type="Opening", account=None, user=None):
	"""Return the total and cash_ledger_balance from Cashier_Opening for a specific date, user and type."""
	if not user:
		user = frappe.session.user
	doc_name = f"{date}_{op_type}_{user}"

	values = frappe.db.get_value("Cashier_Opening", doc_name, ["total", "cash_ledger_balance", "is_locked"], as_dict=True)
	if values:
		return {
			"total": float(values.total or 0.0),
			"cash_ledger_balance": float(values.cash_ledger_balance or 0.0),
			"is_locked": int(values.is_locked or 0)
		}

	# Fallback for Opening: if no record exists, return the opening balance from GL entries
	if op_type == "Opening" and account:
		opening_res = get_cash_ledger_balance(account, date)
		return {"total": 0.0, "cash_ledger_balance": opening_res.get("balance", 0.0), "is_locked": 0}

	return {"total": 0.0, "cash_ledger_balance": 0.0, "is_locked": 0}


@frappe.whitelist()
def get_upi_day_balances(account, date):
	"""Return UPI account opening balance (before date), closing balance, and day's debit."""
	if not account:
		return {"opening": 0.0, "closing": 0.0, "debit": 0.0}

	opening = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(debit) - SUM(credit), 0)
		FROM `tabGL Entry`
		WHERE account = %s AND is_cancelled = 0 AND posting_date < %s
		""",
		(account, date),
	)
	closing = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(debit) - SUM(credit), 0)
		FROM `tabGL Entry`
		WHERE account = %s AND is_cancelled = 0 AND posting_date <= %s
		""",
		(account, date),
	)
	debit = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(debit), 0)
		FROM `tabGL Entry`
		WHERE account = %s AND is_cancelled = 0 AND posting_date = %s
		""",
		(account, date),
	)
	return {
		"opening": float(opening[0][0]) if opening else 0.0,
		"closing": float(closing[0][0]) if closing else 0.0,
		"debit": float(debit[0][0]) if debit else 0.0,
	}


@frappe.whitelist()
def get_today_bills(date, series_list, cash_account=None, upi_account=None, card_account=None, discount_account=None, company=None):
	"""Return today's submitted Sales Invoices for the given series with payment mode breakdown."""
	import json

	if isinstance(series_list, str):
		try:
			series_list = json.loads(series_list)
		except Exception:
			series_list = [s.strip() for s in series_list.split(",") if s.strip()]

	if not series_list:
		return []

	series_conditions = " OR ".join(["si.name LIKE %s"] * len(series_list))
	series_params = [f"{s}%" for s in series_list]

	company_condition = ""
	params = [date]
	if company:
		company_condition = " AND si.company = %s"
		params.append(company)
	params.extend(series_params)

	invoices = frappe.db.sql(
		f"""
		SELECT si.name, si.customer, si.grand_total, si.discount_amount, si.outstanding_amount, si.posting_time
		FROM `tabSales Invoice` si
		WHERE si.posting_date = %s
		  AND si.docstatus = 1
		  {company_condition}
		  AND ({series_conditions})
		ORDER BY si.posting_time DESC
		""",
		params,
		as_dict=True,
	)

	if not invoices:
		return []

	invoice_names = [inv["name"] for inv in invoices]
	# 0. Resolve accounts if company is available
	company = frappe.db.get_value("Sales Invoice", invoices[0]["name"], "company") if invoices else None
	
	def _resolve(name):
		if name in [None, "", "null", "undefined"]:
			return None
		if not company or " - " in name:
			return name
		res = frappe.db.get_value("Account", {"account_name": name, "company": company, "is_group": 0}, "name")
		if not res:
			res = frappe.db.get_value("Account", {"name": name, "company": company, "is_group": 0}, "name")
		return res or name

	cash_account = _resolve(cash_account)
	upi_account = _resolve(upi_account)
	card_account = _resolve(card_account)
	discount_account = _resolve(discount_account)

	placeholders = ", ".join(["%s"] * len(invoice_names))

	payments = frappe.db.sql(
		f"""
		SELECT per.reference_name AS invoice, pe.paid_to AS account, SUM(per.allocated_amount) AS amount
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE per.reference_name IN ({placeholders})
		  AND pe.docstatus = 1
		GROUP BY per.reference_name, pe.paid_to
		""",
		invoice_names,
		as_dict=True,
	)

	payment_map = {}
	for p in payments:
		inv_name = p["invoice"]
		acc = p["account"]
		amt = float(p["amount"] or 0)
		if inv_name not in payment_map:
			payment_map[inv_name] = {"cash": 0.0, "upi": 0.0, "card": 0.0}
		if cash_account and acc == cash_account:
			payment_map[inv_name]["cash"] += amt
		elif upi_account and acc == upi_account:
			payment_map[inv_name]["upi"] += amt
		elif card_account and acc == card_account:
			payment_map[inv_name]["card"] += amt

	# 3. Journal Entry Discounts (linked to Sales Invoice)
	je_condition = ""
	je_params = list(invoice_names)
	if discount_account:
		# The reference is on the Customer row (Receivable), while the discount account is on the other row.
		# So we check if the Journal Entry contains at least one row with the discount_account.
		je_condition = """ AND EXISTS (
			SELECT 1 FROM `tabJournal Entry Account` jea2 
			WHERE jea2.parent = je.name AND jea2.account = %s
		)"""
		je_params.append(discount_account)

	je_discounts = frappe.db.sql(
		f"""
		SELECT jea.reference_name AS invoice, SUM(jea.credit_in_account_currency) AS discount
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE jea.reference_type = "Sales Invoice"
		  AND jea.reference_name IN ({placeholders})
		  AND je.docstatus = 1
		  AND jea.credit_in_account_currency > 0
		  {je_condition}
		GROUP BY jea.reference_name
		""",
		je_params,
		as_dict=True,
	)
	je_discount_map = {d["invoice"]: float(d["discount"] or 0) for d in je_discounts}

	for inv in invoices:
		mops = payment_map.get(inv["name"], {"cash": 0.0, "upi": 0.0, "card": 0.0})
		inv["mop_cash"] = mops["cash"]
		inv["mop_upi"] = mops["upi"]
		inv["mop_card"] = mops["card"]
		inv["grand_total"] = float(inv["grand_total"] or 0)
		inv["discount_amount"] = float(inv["discount_amount"] or 0) + je_discount_map.get(inv["name"], 0)
		inv["outstanding_amount"] = float(inv["outstanding_amount"] or 0)

	return invoices


@frappe.whitelist()
def get_cash_ledger_entries(account, date):
	"""Return GL entries for a cash account on a given date with running balance."""
	if not account:
		return []

	opening_bal = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(debit) - SUM(credit), 0)
		FROM `tabGL Entry`
		WHERE account = %s AND is_cancelled = 0 AND posting_date < %s
		""",
		(account, date),
	)
	opening = float(opening_bal[0][0]) if opening_bal else 0.0

	entries = frappe.db.sql(
		"""
		SELECT
			gle.name,
			gle.voucher_type,
			gle.voucher_no,
			gle.debit,
			gle.credit,
			gle.remarks,
			gle.posting_date,
			gle.creation,
			COALESCE(pe.party, si.customer, '') AS party
		FROM `tabGL Entry` gle
		LEFT JOIN `tabPayment Entry` pe ON pe.name = gle.voucher_no AND gle.voucher_type = 'Payment Entry'
		LEFT JOIN `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
		WHERE gle.account = %s
		  AND gle.is_cancelled = 0
		  AND gle.posting_date = %s
		ORDER BY gle.creation ASC
		""",
		(account, date),
		as_dict=True,
	)

	running = opening
	result = []
	for e in entries:
		running += float(e.debit or 0) - float(e.credit or 0)
		result.append({
			"voucher_no":   e.voucher_no,
			"voucher_type": e.voucher_type,
			"party":        e.party or "",
			"debit":        float(e.debit or 0),
			"credit":       float(e.credit or 0),
			"balance":      running,
			"time":         str(e.creation)[11:16] if e.creation else "",
		})

	return {"opening": opening, "entries": result}


@frappe.whitelist()
def check_cashier_opening(date, user):
	"""Check if an 'Opening' record exists for the given date and user."""
	return frappe.db.exists("Cashier_Opening", {"date": date, "user": user, "opening_or_closing": "Opening"})


@frappe.whitelist()
def get_cashier_opening(date, user, opening_or_closing):
	"""Fetch an existing Cashier_Opening record."""
	doc_name = frappe.db.get_value(
		"Cashier_Opening",
		{"date": date, "user": user, "opening_or_closing": opening_or_closing},
		"name"
	)
	if doc_name:
		return frappe.get_doc("Cashier_Opening", doc_name)
	return None


@frappe.whitelist()
def save_cashier_opening(date, cash, cash_ledger_balance, opening_or_closing, user, difference,
						 d500, d200, d100, d50, d20, d10, d5, d2, d1, total):
	"""Create or update a Cashier_Opening document and return its name."""
	existing_name = frappe.db.get_value(
		"Cashier_Opening",
		{"date": date, "user": user, "opening_or_closing": opening_or_closing},
		"name"
	)

	if existing_name:
		doc = frappe.get_doc("Cashier_Opening", existing_name)
	else:
		doc = frappe.new_doc("Cashier_Opening")
		# Set custom name: Date_Type_User (e.g., 2026-03-15_Opening_biller@gmail.com)
		doc.name = f"{date}_{opening_or_closing}_{user}"

	doc.date = date
	doc.cash = cash
	doc.cash_ledger_balance = str(cash_ledger_balance)
	doc.opening_or_closing = opening_or_closing
	doc.user = user
	doc.difference = str(difference)
	doc.update({
		"500": str(d500 or 0),
		"200": str(d200 or 0),
		"100": str(d100 or 0),
		"50":  str(d50  or 0),
		"20":  str(d20  or 0),
		"10":  str(d10  or 0),
		"5":   str(d5   or 0),
		"2":   str(d2   or 0),
		"1":   str(d1   or 0),
	})
	doc.total = float(total or 0)
	doc.save(ignore_permissions=True)
	return doc


@frappe.whitelist()
def get_day_contras(account, date):
	"""Return a dictionary of session_type -> journal_entry_name for Contra Entry JVs on a date and account."""
	if not account:
		return {}

	entries = frappe.db.sql(
		"""
		SELECT je.name, je.user_remark
		FROM `tabJournal Entry` je
		JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
		WHERE je.posting_date = %s
		  AND je.voucher_type = 'Contra Entry'
		  AND je.docstatus = 1
		  AND jea.account = %s
		""",
		(date, account),
		as_dict=True,
	)

	result = {}
	for e in entries:
		remark = e.get("user_remark") or ""
		# Check which session type this matches
		for session_type in ["Opening", "Mid-Day-1", "Mid-Day-2", "Closing"]:
			# Support both 'Opening' and 'Cashier Opening'
			if session_type in remark or (session_type == "Opening" and "Cashier Opening" in remark):
				result[session_type] = e.get("name")
				break
	return result


@frappe.whitelist()
def lock_day_entries(date, user=None):
	"""Set is_locked = 1 on all Cashier_Opening documents for the given date and user."""
	if not user:
		user = frappe.session.user

	# Set is_locked = 1 on the 4 potential documents:
	# Opening, Mid-Day-1, Mid-Day-2, Closing
	locked_count = 0
	for op_type in ["Opening", "Mid-Day-1", "Mid-Day-2", "Closing"]:
		doc_name = f"{date}_{op_type}_{user}"
		if frappe.db.exists("Cashier_Opening", doc_name):
			frappe.db.set_value("Cashier_Opening", doc_name, "is_locked", 1)
			locked_count += 1

	if locked_count > 0:
		frappe.db.commit()

	return {"status": "Success", "locked_count": locked_count}


