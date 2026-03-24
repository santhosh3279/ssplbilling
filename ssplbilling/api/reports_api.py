import frappe


def _classify_tax(account_head):
	"""Classify a tax account as CGST, SGST, IGST, or Other based on account name."""
	name = (account_head or "").upper()
	if "CGST" in name:
		return "cgst"
	if "SGST" in name or "UTGST" in name:
		return "sgst"
	if "IGST" in name:
		return "igst"
	return "other"


@frappe.whitelist()
def get_sales_tax_register(series, from_date=None, to_date=None):
	"""Return Sales Tax Account Register rows for the given naming series and date range.

	Each row represents one submitted Sales Invoice with its CGST/SGST/IGST breakdown.
	"""
	filters = [
		["Sales Invoice", "naming_series", "=", series],
		["Sales Invoice", "docstatus", "=", 1],
	]
	if from_date:
		filters.append(["Sales Invoice", "posting_date", ">=", from_date])
	if to_date:
		filters.append(["Sales Invoice", "posting_date", "<=", to_date])

	invoices = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=[
			"name",
			"posting_date",
			"customer",
			"customer_name",
			"net_total",
			"total_taxes_and_charges",
			"grand_total",
			"naming_series",
		],
		order_by="posting_date asc, name asc",
	)

	result = []
	for inv in invoices:
		taxes = frappe.get_all(
			"Sales Taxes and Charges",
			filters={"parent": inv.name, "parenttype": "Sales Invoice"},
			fields=["account_head", "rate", "tax_amount"],
			order_by="idx asc",
		)

		cgst_rate = cgst_amount = 0.0
		sgst_rate = sgst_amount = 0.0
		igst_rate = igst_amount = 0.0
		other_tax = 0.0

		for tax in taxes:
			bucket = _classify_tax(tax.account_head)
			if bucket == "cgst":
				cgst_rate = float(tax.rate or 0)
				cgst_amount += float(tax.tax_amount or 0)
			elif bucket == "sgst":
				sgst_rate = float(tax.rate or 0)
				sgst_amount += float(tax.tax_amount or 0)
			elif bucket == "igst":
				igst_rate = float(tax.rate or 0)
				igst_amount += float(tax.tax_amount or 0)
			else:
				other_tax += float(tax.tax_amount or 0)

		result.append(
			{
				"invoice_no": inv.name,
				"date": str(inv.posting_date),
				"customer": inv.customer,
				"customer_name": inv.customer_name,
				"taxable_amount": float(inv.net_total or 0),
				"cgst_rate": cgst_rate,
				"cgst_amount": cgst_amount,
				"sgst_rate": sgst_rate,
				"sgst_amount": sgst_amount,
				"igst_rate": igst_rate,
				"igst_amount": igst_amount,
				"other_tax": other_tax,
				"total_tax": float(inv.total_taxes_and_charges or 0),
				"grand_total": float(inv.grand_total or 0),
			}
		)

	return result


@frappe.whitelist()
def get_sales_order_tax_register(series, from_date=None, to_date=None):
	"""Return Sales Tax Account Register rows for Sales Orders of the given naming series and date range.

	Sales Orders use transaction_date instead of posting_date.
	Only submitted (docstatus=1) orders are included.
	"""
	filters = [
		["Sales Order", "naming_series", "=", series],
		["Sales Order", "docstatus", "=", 1],
	]
	if from_date:
		filters.append(["Sales Order", "transaction_date", ">=", from_date])
	if to_date:
		filters.append(["Sales Order", "transaction_date", "<=", to_date])

	orders = frappe.get_all(
		"Sales Order",
		filters=filters,
		fields=[
			"name",
			"transaction_date",
			"customer",
			"customer_name",
			"net_total",
			"total_taxes_and_charges",
			"grand_total",
			"naming_series",
		],
		order_by="transaction_date asc, name asc",
	)

	result = []
	for order in orders:
		taxes = frappe.get_all(
			"Sales Taxes and Charges",
			filters={"parent": order.name, "parenttype": "Sales Order"},
			fields=["account_head", "rate", "tax_amount"],
			order_by="idx asc",
		)

		cgst_rate = cgst_amount = 0.0
		sgst_rate = sgst_amount = 0.0
		igst_rate = igst_amount = 0.0
		other_tax = 0.0

		for tax in taxes:
			bucket = _classify_tax(tax.account_head)
			if bucket == "cgst":
				cgst_rate = float(tax.rate or 0)
				cgst_amount += float(tax.tax_amount or 0)
			elif bucket == "sgst":
				sgst_rate = float(tax.rate or 0)
				sgst_amount += float(tax.tax_amount or 0)
			elif bucket == "igst":
				igst_rate = float(tax.rate or 0)
				igst_amount += float(tax.tax_amount or 0)
			else:
				other_tax += float(tax.tax_amount or 0)

		result.append(
			{
				"order_no": order.name,
				"date": str(order.transaction_date),
				"customer": order.customer,
				"customer_name": order.customer_name,
				"taxable_amount": float(order.net_total or 0),
				"cgst_rate": cgst_rate,
				"cgst_amount": cgst_amount,
				"sgst_rate": sgst_rate,
				"sgst_amount": sgst_amount,
				"igst_rate": igst_rate,
				"igst_amount": igst_amount,
				"other_tax": other_tax,
				"total_tax": float(order.total_taxes_and_charges or 0),
				"grand_total": float(order.grand_total or 0),
			}
		)

	return result


@frappe.whitelist()
def get_sales_order_series():
	"""Return naming series options defined on the Sales Order doctype."""
	try:
		prop_value = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Sales Order", "field_name": "naming_series", "property": "options"},
			"value",
		)
		if prop_value:
			series = [s.strip() for s in prop_value.split("\n") if s.strip()]
			if series:
				return series
	except Exception:
		pass

	try:
		meta = frappe.get_meta("Sales Order")
		sf = meta.get_field("naming_series")
		if sf and sf.options:
			return [s.strip() for s in sf.options.split("\n") if s.strip()]
	except Exception:
		pass

	return ["SSPL-SO-.YYYY.-"]


@frappe.whitelist()
def get_quotation_tax_register(series, from_date=None, to_date=None):
	"""Return Quotation Tax Register rows for the given naming series and date range.

	Includes both Draft (0) and Submitted (1) quotations.
	"""
	filters = [
		["Quotation", "naming_series", "=", series],
		["Quotation", "docstatus", "in", [0, 1]],
	]
	if from_date:
		filters.append(["Quotation", "transaction_date", ">=", from_date])
	if to_date:
		filters.append(["Quotation", "transaction_date", "<=", to_date])

	quotations = frappe.get_all(
		"Quotation",
		filters=filters,
		fields=[
			"name",
			"transaction_date",
			"customer",
			"customer_name",
			"net_total",
			"total_taxes_and_charges",
			"grand_total",
			"naming_series",
		],
		order_by="transaction_date asc, name asc",
	)

	result = []
	for qt in quotations:
		taxes = frappe.get_all(
			"Sales Taxes and Charges",
			filters={"parent": qt.name, "parenttype": "Quotation"},
			fields=["account_head", "rate", "tax_amount"],
			order_by="idx asc",
		)

		cgst_rate = cgst_amount = 0.0
		sgst_rate = sgst_amount = 0.0
		igst_rate = igst_amount = 0.0
		other_tax = 0.0

		for tax in taxes:
			bucket = _classify_tax(tax.account_head)
			if bucket == "cgst":
				cgst_rate = float(tax.rate or 0)
				cgst_amount += float(tax.tax_amount or 0)
			elif bucket == "sgst":
				sgst_rate = float(tax.rate or 0)
				sgst_amount += float(tax.tax_amount or 0)
			elif bucket == "igst":
				igst_rate = float(tax.rate or 0)
				igst_amount += float(tax.tax_amount or 0)
			else:
				other_tax += float(tax.tax_amount or 0)

		result.append(
			{
				"quotation_no": qt.name,
				"date": str(qt.transaction_date),
				"customer": qt.customer,
				"customer_name": qt.customer_name,
				"taxable_amount": float(qt.net_total or 0),
				"cgst_rate": cgst_rate,
				"cgst_amount": cgst_amount,
				"sgst_rate": sgst_rate,
				"sgst_amount": sgst_amount,
				"igst_rate": igst_rate,
				"igst_amount": igst_amount,
				"other_tax": other_tax,
				"total_tax": float(qt.total_taxes_and_charges or 0),
				"grand_total": float(qt.grand_total or 0),
			}
		)

	return result


@frappe.whitelist()
def get_quotation_series():
	"""Return naming series options defined on the Quotation doctype."""
	try:
		prop_value = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Quotation", "field_name": "naming_series", "property": "options"},
			"value",
		)
		if prop_value:
			series = [s.strip() for s in prop_value.split("\n") if s.strip()]
			if series:
				return series
	except Exception:
		pass

	try:
		meta = frappe.get_meta("Quotation")
		sf = meta.get_field("naming_series")
		if sf and sf.options:
			return [s.strip() for s in sf.options.split("\n") if s.strip()]
	except Exception:
		pass

	return ["QTN-"]
