import frappe


@frappe.whitelist()
def get_cash_ledger_balance(account):
	"""Return the current balance of a cash/bank account from GL entries."""
	if not account:
		return {"balance": 0.0}
	balance = frappe.db.sql(
		"""
		SELECT IFNULL(SUM(debit) - SUM(credit), 0)
		FROM `tabGL Entry`
		WHERE account = %s
		  AND is_cancelled = 0
		""",
		(account,),
	)
	return {"balance": float(balance[0][0]) if balance else 0.0}


@frappe.whitelist()
def get_cahier_totals(date, op_type="Opening"):
	"""Return the total and cash_ledger_balance from Cashier_Opening for a specific date, user and type."""
	user = frappe.session.user
	doc_name = f"{date}_{op_type}_{user}"
	
	values = frappe.db.get_value("Cashier_Opening", doc_name, ["total", "cash_ledger_balance"], as_dict=True)
	if values:
		return {
			"total": float(values.total or 0.0),
			"cash_ledger_balance": float(values.cash_ledger_balance or 0.0)
		}
	return {"total": 0.0, "cash_ledger_balance": 0.0}


@frappe.whitelist()
def get_upi_day_balances(account, date):
	"""Return UPI account opening balance (before date) and closing balance (up to and including date)."""
	if not account:
		return {"opening": 0.0, "closing": 0.0}

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
	return {
		"opening": float(opening[0][0]) if opening else 0.0,
		"closing": float(closing[0][0]) if closing else 0.0,
	}


@frappe.whitelist()
def get_today_bills(date, series_list):
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

	invoices = frappe.db.sql(
		f"""
		SELECT si.name, si.customer, si.grand_total, si.outstanding_amount, si.posting_time
		FROM `tabSales Invoice` si
		WHERE si.posting_date = %s
		  AND si.docstatus = 1
		  AND ({series_conditions})
		ORDER BY si.posting_time DESC
		""",
		[date] + series_params,
		as_dict=True,
	)

	if not invoices:
		return []

	invoice_names = [inv["name"] for inv in invoices]
	placeholders = ", ".join(["%s"] * len(invoice_names))

	payments = frappe.db.sql(
		f"""
		SELECT per.reference_name AS invoice, pe.mode_of_payment, SUM(per.allocated_amount) AS amount
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE per.reference_name IN ({placeholders})
		  AND pe.docstatus = 1
		GROUP BY per.reference_name, pe.mode_of_payment
		""",
		invoice_names,
		as_dict=True,
	)

	payment_map = {}
	for p in payments:
		payment_map.setdefault(p["invoice"], {})[p["mode_of_payment"]] = float(p["amount"] or 0)

	for inv in invoices:
		inv["pay"] = payment_map.get(inv["name"], {})
		inv["grand_total"] = float(inv["grand_total"] or 0)
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
