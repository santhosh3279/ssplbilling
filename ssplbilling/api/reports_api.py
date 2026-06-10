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
			"party_name",
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
				"customer": qt.party_name,
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


@frappe.whitelist()
def get_hsn_summary_report(series, from_date=None, to_date=None):
	"""Return HSN Summary Report for Sales Invoices for the given naming series and date range.
	Group by HSN code.
	"""
	filters = [
		["Sales Invoice", "naming_series", "=", series],
		["Sales Invoice", "docstatus", "=", 1],
	]
	
	query_filters = [series]
	date_condition = ""
	if from_date:
		date_condition += " AND inv.posting_date >= %s"
		query_filters.append(from_date)
	if to_date:
		date_condition += " AND inv.posting_date <= %s"
		query_filters.append(to_date)

	rows = frappe.db.sql(f"""
		SELECT 
			it.gst_hsn_code as hsn_code,
			SUM(it.qty) as total_qty,
			SUM(it.taxable_value) as total_taxable_value,
			SUM(it.cgst_amount) as total_cgst,
			SUM(it.sgst_amount) as total_sgst,
			SUM(it.igst_amount) as total_igst
		FROM 
			`tabSales Invoice` inv
		JOIN 
			`tabSales Invoice Item` it ON it.parent = inv.name
		WHERE 
			inv.naming_series = %s 
			AND inv.docstatus = 1
			{date_condition}
		GROUP BY 
			it.gst_hsn_code
	""", tuple(query_filters), as_dict=1)
	
	# Handle None in hsn_code and calculate totals
	result = []
	for row in rows:
		r = dict(row)
		if not r.get("hsn_code"):
			r["hsn_code"] = "N/A"
		
		r["total_tax"] = float(r.get("total_cgst") or 0) + float(r.get("total_sgst") or 0) + float(r.get("total_igst") or 0)
		r["total_value"] = float(r.get("total_taxable_value") or 0) + r["total_tax"]
		
		# Convert Decimal to float for JSON serialization if needed (frappe does this usually)
		r["total_qty"] = float(r.get("total_qty") or 0)
		r["total_taxable_value"] = float(r.get("total_taxable_value") or 0)
		r["total_cgst"] = float(r.get("total_cgst") or 0)
		r["total_sgst"] = float(r.get("total_sgst") or 0)
		r["total_igst"] = float(r.get("total_igst") or 0)
		
		result.append(r)

	return result


@frappe.whitelist()
def get_quotation_hsn_summary_report(series, from_date=None, to_date=None):
	"""Return HSN Summary Report for Quotations for the given naming series and date range.
	Includes both Draft and Submitted quotations. Group by HSN code.
	"""
	query_filters = [series]
	date_condition = ""
	if from_date:
		date_condition += " AND qt.transaction_date >= %s"
		query_filters.append(from_date)
	if to_date:
		date_condition += " AND qt.transaction_date <= %s"
		query_filters.append(to_date)

	rows = frappe.db.sql(f"""
		SELECT 
			it.gst_hsn_code as hsn_code,
			SUM(it.qty) as total_qty,
			SUM(it.taxable_value) as total_taxable_value,
			SUM(it.cgst_amount) as total_cgst,
			SUM(it.sgst_amount) as total_sgst,
			SUM(it.igst_amount) as total_igst
		FROM 
			`tabQuotation` qt
		JOIN 
			`tabQuotation Item` it ON it.parent = qt.name
		WHERE 
			qt.naming_series = %s 
			AND qt.docstatus IN (0, 1)
			{date_condition}
		GROUP BY 
			it.gst_hsn_code
	""", tuple(query_filters), as_dict=1)
	
	result = []
	for row in rows:
		r = dict(row)
		if not r.get("hsn_code"):
			r["hsn_code"] = "N/A"
		
		r["total_tax"] = float(r.get("total_cgst") or 0) + float(r.get("total_sgst") or 0) + float(r.get("total_igst") or 0)
		r["total_value"] = float(r.get("total_taxable_value") or 0) + r["total_tax"]
		
		r["total_qty"] = float(r.get("total_qty") or 0)
		r["total_taxable_value"] = float(r.get("total_taxable_value") or 0)
		r["total_cgst"] = float(r.get("total_cgst") or 0)
		r["total_sgst"] = float(r.get("total_sgst") or 0)
		r["total_igst"] = float(r.get("total_igst") or 0)
		
		result.append(r)

	return result



@frappe.whitelist()
def get_item_summary_report(series, from_date=None, to_date=None):
	"""Return Item Sales Summary Report for Sales Invoices for the given naming series and date range.
	Group by Item Code.
	"""
	query_filters = [series]
	date_condition = ""
	if from_date:
		date_condition += " AND inv.posting_date >= %s"
		query_filters.append(from_date)
	if to_date:
		date_condition += " AND inv.posting_date <= %s"
		query_filters.append(to_date)

	rows = frappe.db.sql(f"""
		SELECT 
			it.item_code,
			it.item_name,
			it.stock_uom,
			SUM(it.qty) as total_qty,
			SUM(it.taxable_value) as total_taxable_value
		FROM 
			`tabSales Invoice` inv
		JOIN 
			`tabSales Invoice Item` it ON it.parent = inv.name
		WHERE 
			inv.naming_series = %s 
			AND inv.docstatus = 1
			{date_condition}
		GROUP BY 
			it.item_code, it.item_name, it.stock_uom
		ORDER BY 
			it.item_name ASC
	""", tuple(query_filters), as_dict=1)

	result = []
	for row in rows:
		r = dict(row)
		r["total_qty"] = float(r.get("total_qty") or 0)
		r["total_taxable_value"] = float(r.get("total_taxable_value") or 0)
		result.append(r)

	return result


@frappe.whitelist()
def get_store_sale_report(from_date=None, to_date=None):
        """
        Get sale report grouped by store (Income Account) from direct income accounts.
        Preset to today if dates are not provided.
        """
        if not from_date:
                from_date = frappe.utils.today()
        if not to_date:
                to_date = frappe.utils.today()

        # Find accounts under 'Direct Income' group
        direct_income_groups = frappe.get_all(
                "Account",
                filters={"account_name": ["like", "%Direct Income%"], "is_group": 1},
                fields=["name", "lft", "rgt"],
        )

        if not direct_income_groups:
                direct_income_groups = frappe.get_all(
                        "Account", filters={"root_type": "Income", "is_group": 1}, fields=["name", "lft", "rgt"]
                )

        account_list = []
        for acc in direct_income_groups:
                children = frappe.get_all(
                        "Account",
                        filters={"lft": [">=", acc.lft], "rgt": ["<=", acc.rgt], "is_group": 0},
                        fields=["name"],
                )
                account_list.extend([c.name for c in children])

        if not account_list:
                return {"report_data": [], "price_lists": []}

        # Query GL Entry joined with Sales Invoice to get Price List
        # Group by account instead of cost_center
        results = frappe.db.sql(
                """
                SELECT
                        gle.account,
                        si.selling_price_list,
                        SUM(gle.credit - gle.debit) as total_amount
                FROM
                        `tabGL Entry` gle
                LEFT JOIN
                        `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
                WHERE
                        gle.posting_date BETWEEN %s AND %s
                        AND gle.account IN %s
                        AND gle.is_cancelled = 0
                GROUP BY
                        gle.account, si.selling_price_list
                ORDER BY
                        gle.account, total_amount DESC
        """,
                (from_date, to_date, tuple(account_list)),
                as_dict=1,
        )

        # Format results for frontend: Group by Account and pivot Price Lists
        stores = {}
        all_price_lists = set()
        for r in results:
                acc_name = r["account"]
                if acc_name not in stores:
                        store_display_name = acc_name.split(" - ")[0] if " - " in acc_name else acc_name
                        stores[acc_name] = {
                                "account": acc_name,
                                "store_name": store_display_name,
                                "total_amount": 0.0,
                                "price_list_data": {}
                        }
                
                amount = float(r["total_amount"] or 0)
                stores[acc_name]["total_amount"] += amount
                
                pl_name = r["selling_price_list"] or "Other/Direct"
                all_price_lists.add(pl_name)
                stores[acc_name]["price_list_data"][pl_name] = stores[acc_name]["price_list_data"].get(pl_name, 0.0) + amount

        # Convert to list and sort by total amount desc
        report_data = list(stores.values())
        report_data.sort(key=lambda x: x["total_amount"], reverse=True)

        return {
                "report_data": report_data,
                "price_lists": sorted(list(all_price_lists))
        }

@frappe.whitelist()
def get_store_wise_item_sales_report(from_date=None, to_date=None, income_account=None):
	"""Return Store Wise Item Sales Report.
	Group by Income Account and Item Code.
	"""
	query_filters = []
	date_condition = ""
	if from_date:
		date_condition += " AND inv.posting_date >= %s"
		query_filters.append(from_date)
	if to_date:
		date_condition += " AND inv.posting_date <= %s"
		query_filters.append(to_date)

	income_account_condition = ""
	if income_account:
		income_account_condition = " AND it.income_account = %s"
		query_filters.append(income_account)

	rows = frappe.db.sql(f"""
		SELECT 
			it.income_account,
			it.item_code,
			it.item_name,
			it.stock_uom,
			SUM(it.qty) as total_qty,
			SUM(it.taxable_value) as total_taxable_value
		FROM 
			`tabSales Invoice` inv
		JOIN 
			`tabSales Invoice Item` it ON it.parent = inv.name
		WHERE 
			inv.docstatus = 1
			{date_condition}
			{income_account_condition}
		GROUP BY 
			it.income_account, it.item_code, it.item_name, it.stock_uom
		ORDER BY 
			it.income_account ASC, it.item_name ASC
	""", tuple(query_filters), as_dict=1)

	result = []
	for row in rows:
		r = dict(row)
		r["total_qty"] = float(r.get("total_qty") or 0)
		r["total_taxable_value"] = float(r.get("total_taxable_value") or 0)
		result.append(r)

	return result

@frappe.whitelist()
def get_income_accounts():
    """Return a list of income accounts for filtering."""
    return frappe.get_all(
        "Account",
        filters={"root_type": "Income", "is_group": 0},
        pluck="name",
        order_by="name asc"
    )
