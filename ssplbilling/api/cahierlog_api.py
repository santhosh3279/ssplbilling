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
def get_opening_total(date, cash_account):
	"""Return the total from Cashier_Opening for a specific date, matching account and logged-in user."""
	if not cash_account:
		return {"total": 0.0}
		
	total = frappe.db.get_value(
		"Cashier_Opening", 
		{
			"date": date, 
			"opening_or_closing": "Opening", 
			"cash": cash_account,
			"user": frappe.session.user
		}, 
		"total"
	)
	return {"total": float(total or 0.0)}


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
		# Set custom name: Date_Type (e.g., 2026-03-15_Opening)
		doc.name = f"{date}_{opening_or_closing}"

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
