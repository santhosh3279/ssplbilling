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
	company = frappe.db.get_value("Sales Invoice", {"naming_series": series}, "company") or frappe.defaults.get_user_default("company")
	if not company:
		company = frappe.db.get_value("Company", {}, "name")

	templates = frappe.get_all(
		"Item Tax Template",
		filters={"disabled": 0, "company": ["in", [company, None]]},
		fields=["name", "title", "gst_rate"],
		order_by="gst_rate asc, title asc",
	)

	template_map = {t.name: t for t in templates}
	rate_to_template = {}
	for t in templates:
		if t.gst_rate not in rate_to_template:
			rate_to_template[t.gst_rate] = t.name

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
			"billing_address_gstin",
		],
		order_by="posting_date asc, name asc",
	)

	result = []
	for inv in invoices:
		customer_gstin = inv.billing_address_gstin
		if not customer_gstin and inv.customer:
			customer_gstin = frappe.db.get_value("Customer", inv.customer, "gstin") or ""
		customer_gstin = customer_gstin or ""

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

		# Fetch items to calculate template-wise taxable and tax values
		items = frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": inv.name},
			fields=[
				"net_amount", "item_tax_template", "cgst_rate", "sgst_rate", "igst_rate",
				"cgst_amount", "sgst_amount", "igst_amount"
			],
		)
		template_sums = {t.name: {"taxable": 0.0, "tax": 0.0} for t in templates}
		for item in items:
			net_amt = float(item.net_amount or 0)
			tax_amt = float(item.cgst_amount or 0) + float(item.sgst_amount or 0) + float(item.igst_amount or 0)
			template_name = item.item_tax_template
			
			if not template_name or template_name not in template_map:
				# Fallback: match by rate
				igst = float(item.igst_rate or 0)
				cgst = float(item.cgst_rate or 0)
				sgst = float(item.sgst_rate or 0)
				total_rate = round(igst if igst > 0 else (cgst + sgst), 2)
				template_name = rate_to_template.get(total_rate)

			if template_name in template_sums:
				template_sums[template_name]["taxable"] += net_amt
				template_sums[template_name]["tax"] += tax_amt

		result.append(
			{
				"invoice_no": inv.name,
				"date": str(inv.posting_date),
				"customer": inv.customer,
				"customer_name": inv.customer_name,
				"customer_gstin": customer_gstin,
				"taxable_amount": float(inv.net_total or 0),
				"template_values": template_sums,
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

	comp = get_company_details()
	return {
		"rows": result,
		"active_templates": [{"name": t.name, "title": t.title, "gst_rate": t.gst_rate} for t in templates],
		"company_name": comp["company_name"],
		"company_address_lines": comp["address_lines"]
	}


@frappe.whitelist()
def get_quotation_tax_register(series, from_date=None, to_date=None):
	"""Return Quotation Tax Register rows for the given naming series and date range.

	Includes both Draft (0) and Submitted (1) quotations.
	"""
	company = frappe.db.get_value("Quotation", {"naming_series": series}, "company") or frappe.defaults.get_user_default("company")
	if not company:
		company = frappe.db.get_value("Company", {}, "name")

	templates = frappe.get_all(
		"Item Tax Template",
		filters={"disabled": 0, "company": ["in", [company, None]]},
		fields=["name", "title", "gst_rate"],
		order_by="gst_rate asc, title asc",
	)

	template_map = {t.name: t for t in templates}
	rate_to_template = {}
	for t in templates:
		if t.gst_rate not in rate_to_template:
			rate_to_template[t.gst_rate] = t.name

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
			"billing_address_gstin",
		],
		order_by="transaction_date asc, name asc",
	)

	result = []
	for qt in quotations:
		customer_gstin = qt.billing_address_gstin
		if not customer_gstin and qt.party_name:
			customer_gstin = frappe.db.get_value("Customer", qt.party_name, "gstin") or ""
		customer_gstin = customer_gstin or ""

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

		# Fetch items to calculate template-wise taxable and tax values
		items = frappe.get_all(
			"Quotation Item",
			filters={"parent": qt.name},
			fields=[
				"net_amount", "item_tax_template", "cgst_rate", "sgst_rate", "igst_rate",
				"cgst_amount", "sgst_amount", "igst_amount"
			],
		)
		template_sums = {t.name: {"taxable": 0.0, "tax": 0.0} for t in templates}
		for item in items:
			net_amt = float(item.net_amount or 0)
			tax_amt = float(item.cgst_amount or 0) + float(item.sgst_amount or 0) + float(item.igst_amount or 0)
			template_name = item.item_tax_template
			
			if not template_name or template_name not in template_map:
				# Fallback: match by rate
				igst = float(item.igst_rate or 0)
				cgst = float(item.cgst_rate or 0)
				sgst = float(item.sgst_rate or 0)
				total_rate = round(igst if igst > 0 else (cgst + sgst), 2)
				template_name = rate_to_template.get(total_rate)

			if template_name in template_sums:
				template_sums[template_name]["taxable"] += net_amt
				template_sums[template_name]["tax"] += tax_amt

		result.append(
			{
				"quotation_no": qt.name,
				"date": str(qt.transaction_date),
				"customer": qt.party_name,
				"customer_name": qt.customer_name,
				"customer_gstin": customer_gstin,
				"taxable_amount": float(qt.net_total or 0),
				"template_values": template_sums,
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

	comp = get_company_details()
	return {
		"rows": result,
		"active_templates": [{"name": t.name, "title": t.title, "gst_rate": t.gst_rate} for t in templates],
		"company_name": comp["company_name"],
		"company_address_lines": comp["address_lines"]
	}


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


def get_company_details():
	from erpnext import get_default_company
	company = frappe.defaults.get_global_default("company") or get_default_company() or "Sundaram and Sons Private Ltd"
	
	address_fields = ["address_line1", "address_line2", "city", "state", "pincode", "gstin"]
	addr = frappe.db.get_value("Address", {"is_your_company_address": 1}, address_fields, as_dict=True)
	
	address_lines = []
	if addr:
		if addr.get("address_line1"):
			address_lines.append(addr["address_line1"])
		if addr.get("address_line2"):
			address_lines.append(addr["address_line2"])
		city_state = []
		if addr.get("city"):
			city_state.append(addr["city"])
		if addr.get("state"):
			city_state.append(addr["state"])
		if addr.get("pincode"):
			city_state.append(addr["pincode"])
		if city_state:
			address_lines.append(", ".join(city_state))
		if addr.get("gstin"):
			address_lines.append(f"GSTIN: {addr['gstin']}")
	
	return {
		"company_name": company,
		"address_lines": address_lines
	}


@frappe.whitelist()
def get_hsn_summary_report(series, from_date=None, to_date=None):
	"""Return HSN Summary Report for Sales Invoices for the given naming series and date range.
	Group by HSN code and invoice to show bill details.
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
			it.gst_hsn_code as hsn_code,
			inv.posting_date as date,
			inv.name as bill_no,
			SUM(it.qty) as qty,
			SUM(it.taxable_value) as taxable_value,
			SUM(it.cgst_amount) as cgst,
			SUM(it.sgst_amount) as sgst,
			SUM(it.igst_amount) as igst
		FROM 
			`tabSales Invoice` inv
		JOIN 
			`tabSales Invoice Item` it ON it.parent = inv.name
		WHERE 
			inv.naming_series = %s 
			AND inv.docstatus = 1
			{date_condition}
		GROUP BY 
			it.gst_hsn_code,
			inv.name
		ORDER BY 
			it.gst_hsn_code,
			inv.posting_date,
			inv.name
	""", tuple(query_filters), as_dict=1)
	
	# Handle None in hsn_code and convert types
	result = []
	for row in rows:
		r = dict(row)
		if not r.get("hsn_code"):
			r["hsn_code"] = "N/A"
		
		if r.get("date") and hasattr(r["date"], "strftime"):
			r["date"] = r["date"].strftime("%Y-%m-%d")
		elif r.get("date"):
			r["date"] = str(r["date"])
		
		r["qty"] = float(r.get("qty") or 0)
		r["taxable_value"] = float(r.get("taxable_value") or 0)
		r["cgst"] = float(r.get("cgst") or 0)
		r["sgst"] = float(r.get("sgst") or 0)
		r["igst"] = float(r.get("igst") or 0)
		
		result.append(r)

	comp = get_company_details()
	return {
		"rows": result,
		"company_name": comp["company_name"],
		"company_address_lines": comp["address_lines"]
	}


@frappe.whitelist()
def get_quotation_hsn_summary_report(series, from_date=None, to_date=None):
	"""Return HSN Summary Report for Quotations for the given naming series and date range.
	Includes both Draft and Submitted quotations. Group by HSN code and quotation name to show bill details.
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
			qt.transaction_date as date,
			qt.name as bill_no,
			SUM(it.qty) as qty,
			SUM(it.taxable_value) as taxable_value,
			SUM(it.cgst_amount) as cgst,
			SUM(it.sgst_amount) as sgst,
			SUM(it.igst_amount) as igst
		FROM 
			`tabQuotation` qt
		JOIN 
			`tabQuotation Item` it ON it.parent = qt.name
		WHERE 
			qt.naming_series = %s 
			AND qt.docstatus IN (0, 1)
			{date_condition}
		GROUP BY 
			it.gst_hsn_code,
			qt.name
		ORDER BY 
			it.gst_hsn_code,
			qt.transaction_date,
			qt.name
	""", tuple(query_filters), as_dict=1)
	
	result = []
	for row in rows:
		r = dict(row)
		if not r.get("hsn_code"):
			r["hsn_code"] = "N/A"
		
		if r.get("date") and hasattr(r["date"], "strftime"):
			r["date"] = r["date"].strftime("%Y-%m-%d")
		elif r.get("date"):
			r["date"] = str(r["date"])
		
		r["qty"] = float(r.get("qty") or 0)
		r["taxable_value"] = float(r.get("taxable_value") or 0)
		r["cgst"] = float(r.get("cgst") or 0)
		r["sgst"] = float(r.get("sgst") or 0)
		r["igst"] = float(r.get("igst") or 0)
		
		result.append(r)

	comp = get_company_details()
	return {
		"rows": result,
		"company_name": comp["company_name"],
		"company_address_lines": comp["address_lines"]
	}



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
def get_fast_moving_items_report(from_date=None, to_date=None, series=None, income_account=None, limit=50):
	"""Return Fast Moving Items Report.
	Ordered by total quantity sold descending.
	"""
	query_filters = []
	conditions = []

	if from_date:
		conditions.append("inv.posting_date >= %s")
		query_filters.append(from_date)
	if to_date:
		conditions.append("inv.posting_date <= %s")
		query_filters.append(to_date)
	if series:
		conditions.append("inv.naming_series = %s")
		query_filters.append(series)
	if income_account:
		conditions.append("it.income_account = %s")
		query_filters.append(income_account)

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "AND " + where_clause

	# Parse limit safely
	try:
		limit_val = int(limit)
	except (TypeError, ValueError):
		limit_val = 50

	query = f"""
		SELECT 
			it.item_code,
			it.item_name,
			it.stock_uom,
			SUM(it.qty) as total_qty,
			SUM(it.taxable_value) as total_taxable_value,
			COUNT(DISTINCT inv.name) as transaction_count
		FROM 
			`tabSales Invoice` inv
		JOIN 
			`tabSales Invoice Item` it ON it.parent = inv.name
		WHERE 
			inv.docstatus = 1
			{where_clause}
		GROUP BY 
			it.item_code, it.item_name, it.stock_uom
		ORDER BY 
			total_qty DESC
		LIMIT %s
	"""
	query_filters.append(limit_val)

	rows = frappe.db.sql(query, tuple(query_filters), as_dict=1)

	result = []
	for row in rows:
		r = dict(row)
		r["total_qty"] = float(r.get("total_qty") or 0)
		r["total_taxable_value"] = float(r.get("total_taxable_value") or 0)
		r["transaction_count"] = int(r.get("transaction_count") or 0)
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
                return {"report_data": [], "price_lists": [], "bills_data": []}

        # Query GL Entry joined with Sales Invoice to get Price List
        # Group by account instead of cost_center
        results = frappe.db.sql(
                """
                SELECT
                        account,
                        selling_price_list,
                        SUM(bill_amount) as total_amount
                FROM (
                        SELECT DISTINCT
                                gle.account,
                                gle.voucher_no,
                                si.selling_price_list,
                                COALESCE(NULLIF(si.rounded_total, 0), si.grand_total) as bill_amount
                        FROM
                                `tabGL Entry` gle
                        LEFT JOIN
                                `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
                        WHERE
                                gle.posting_date BETWEEN %s AND %s
                                AND gle.account IN %s
                                AND gle.is_cancelled = 0
                ) t
                GROUP BY
                        account, selling_price_list
                ORDER BY
                        account, total_amount DESC
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

        bills_results = frappe.db.sql(
                """
                SELECT
                        gle.account,
                        gle.voucher_no as bill_no,
                        gle.posting_date,
                        si.customer,
                        si.customer_name,
                        si.selling_price_list,
                        MAX(COALESCE(NULLIF(si.rounded_total, 0), si.grand_total)) as bill_amount
                FROM
                        `tabGL Entry` gle
                LEFT JOIN
                        `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
                WHERE
                        gle.posting_date BETWEEN %s AND %s
                        AND gle.account IN %s
                        AND gle.is_cancelled = 0
                GROUP BY
                        gle.account, gle.voucher_no
                ORDER BY
                        gle.account, gle.voucher_no
        """,
                (from_date, to_date, tuple(account_list)),
                as_dict=1,
        )

        for b in bills_results:
                if b.get("posting_date"):
                        b["posting_date"] = str(b["posting_date"])

        return {
                "report_data": report_data,
                "price_lists": sorted(list(all_price_lists)),
                "bills_data": bills_results
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


@frappe.whitelist()
def get_cost_center_sale_report(from_date=None, to_date=None):
        """
        Get sale report grouped by cost center from direct income accounts.
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
                return {"report_data": [], "price_lists": [], "bills_data": []}

        # Query GL Entry joined with Sales Invoice to get Price List
        # Group by cost_center instead of account
        results = frappe.db.sql(
                """
                SELECT
                        cost_center,
                        selling_price_list,
                        SUM(bill_amount) as total_amount
                FROM (
                        SELECT DISTINCT
                                gle.cost_center,
                                gle.voucher_no,
                                si.selling_price_list,
                                COALESCE(NULLIF(si.rounded_total, 0), si.grand_total) as bill_amount
                        FROM
                                `tabGL Entry` gle
                        LEFT JOIN
                                `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
                        WHERE
                                gle.posting_date BETWEEN %s AND %s
                                AND gle.account IN %s
                                AND gle.is_cancelled = 0
                ) t
                GROUP BY
                        cost_center, selling_price_list
                ORDER BY
                        cost_center, total_amount DESC
        """,
                (from_date, to_date, tuple(account_list)),
                as_dict=1,
        )

        # Format results for frontend: Group by Cost Center and pivot Price Lists
        cost_centers = {}
        all_price_lists = set()
        for r in results:
                cc_name = r["cost_center"] or "No Cost Center"
                if cc_name not in cost_centers:
                        cc_display_name = cc_name.split(" - ")[0] if " - " in cc_name else cc_name
                        cost_centers[cc_name] = {
                                "cost_center": cc_name,
                                "cost_center_name": cc_display_name,
                                "total_amount": 0.0,
                                "price_list_data": {}
                        }
                
                amount = float(r["total_amount"] or 0)
                cost_centers[cc_name]["total_amount"] += amount
                
                pl_name = r["selling_price_list"] or "Other/Direct"
                all_price_lists.add(pl_name)
                cost_centers[cc_name]["price_list_data"][pl_name] = cost_centers[cc_name]["price_list_data"].get(pl_name, 0.0) + amount

        # Convert to list and sort by total amount desc
        report_data = list(cost_centers.values())
        report_data.sort(key=lambda x: x["total_amount"], reverse=True)

        bills_results = frappe.db.sql(
                """
                SELECT
                        gle.cost_center,
                        gle.voucher_no as bill_no,
                        gle.posting_date,
                        si.customer,
                        si.customer_name,
                        si.selling_price_list,
                        MAX(COALESCE(NULLIF(si.rounded_total, 0), si.grand_total)) as bill_amount
                FROM
                        `tabGL Entry` gle
                LEFT JOIN
                        `tabSales Invoice` si ON si.name = gle.voucher_no AND gle.voucher_type = 'Sales Invoice'
                WHERE
                        gle.posting_date BETWEEN %s AND %s
                        AND gle.account IN %s
                        AND gle.is_cancelled = 0
                GROUP BY
                        gle.cost_center, gle.voucher_no
                ORDER BY
                        gle.cost_center, gle.voucher_no
        """,
                (from_date, to_date, tuple(account_list)),
                as_dict=1,
        )

        for b in bills_results:
                if b.get("posting_date"):
                        b["posting_date"] = str(b["posting_date"])
                if not b.get("cost_center"):
                        b["cost_center"] = "No Cost Center"

        # Fetch Direct Expenses
        direct_expense_groups = frappe.get_all(
                "Account",
                filters={"account_name": ["like", "Direct Expense%"], "is_group": 1},
                fields=["name", "lft", "rgt"],
        )
        direct_expense_accounts = []
        for acc in direct_expense_groups:
                children = frappe.get_all(
                        "Account",
                        filters={"lft": [">=", acc.lft], "rgt": ["<=", acc.rgt], "is_group": 0},
                        fields=["name"],
                )
                direct_expense_accounts.extend([c.name for c in children])

        direct_expense_data = {}
        direct_heads = set()
        if direct_expense_accounts:
                direct_expenses = frappe.db.sql(
                        """
                        SELECT
                                cost_center,
                                account,
                                SUM(debit - credit) as amount
                        FROM
                                `tabGL Entry`
                        WHERE
                                posting_date BETWEEN %s AND %s
                                AND account IN %s
                                AND is_cancelled = 0
                        GROUP BY
                                cost_center, account
                        """,
                        (from_date, to_date, tuple(direct_expense_accounts)),
                        as_dict=1,
                )
                for de in direct_expenses:
                        cc = de["cost_center"] or "No Cost Center"
                        acc = de["account"]
                        amount = float(de["amount"] or 0)
                        if amount != 0:
                                direct_heads.add(acc)
                                if cc not in direct_expense_data:
                                        direct_expense_data[cc] = {}
                                direct_expense_data[cc][acc] = amount

        # Fetch Indirect Expenses
        indirect_expense_groups = frappe.get_all(
                "Account",
                filters={"account_name": ["like", "Indirect Expense%"], "is_group": 1},
                fields=["name", "lft", "rgt"],
        )
        indirect_expense_accounts = []
        for acc in indirect_expense_groups:
                children = frappe.get_all(
                        "Account",
                        filters={"lft": [">=", acc.lft], "rgt": ["<=", acc.rgt], "is_group": 0},
                        fields=["name"],
                )
                indirect_expense_accounts.extend([c.name for c in children])

        indirect_expense_data = {}
        indirect_heads = set()
        if indirect_expense_accounts:
                indirect_expenses = frappe.db.sql(
                        """
                        SELECT
                                cost_center,
                                account,
                                SUM(debit - credit) as amount
                        FROM
                                `tabGL Entry`
                        WHERE
                                posting_date BETWEEN %s AND %s
                                AND account IN %s
                                AND is_cancelled = 0
                        GROUP BY
                                cost_center, account
                        """,
                        (from_date, to_date, tuple(indirect_expense_accounts)),
                        as_dict=1,
                )
                for ie in indirect_expenses:
                        cc = ie["cost_center"] or "No Cost Center"
                        acc = ie["account"]
                        amount = float(ie["amount"] or 0)
                        if amount != 0:
                                indirect_heads.add(acc)
                                if cc not in indirect_expense_data:
                                        indirect_expense_data[cc] = {}
                                indirect_expense_data[cc][acc] = amount

        # Merge direct and indirect expenses per Cost Center
        expense_ccs = {}
        all_ccs = set(direct_expense_data.keys()).union(set(indirect_expense_data.keys()))
        
        for cc in all_ccs:
                cc_display_name = cc.split(" - ")[0] if " - " in cc else cc
                expense_ccs[cc] = {
                        "cost_center": cc,
                        "cost_center_name": cc_display_name,
                        "direct_expense": 0.0,
                        "indirect_expense": 0.0,
                        "total_expense": 0.0,
                        "account_amounts": {}
                }
                
                # Direct expenses details
                if cc in direct_expense_data:
                        for acc, amt in direct_expense_data[cc].items():
                                expense_ccs[cc]["account_amounts"][acc] = amt
                                expense_ccs[cc]["direct_expense"] += amt
                                expense_ccs[cc]["total_expense"] += amt
                                
                # Indirect expenses details
                if cc in indirect_expense_data:
                        for acc, amt in indirect_expense_data[cc].items():
                                expense_ccs[cc]["account_amounts"][acc] = amt
                                expense_ccs[cc]["indirect_expense"] += amt
                                expense_ccs[cc]["total_expense"] += amt

        expenses_report_data = list(expense_ccs.values())
        expenses_report_data.sort(key=lambda x: x["total_expense"], reverse=True)

        # Entry-level direct expense details (particulars) for Excel export
        direct_expense_entries = []
        if direct_expense_accounts:
                direct_expense_entries = frappe.db.sql(
                        """
                        SELECT
                                cost_center,
                                posting_date,
                                voucher_type,
                                voucher_no,
                                account,
                                against,
                                remarks,
                                (debit - credit) as amount
                        FROM
                                `tabGL Entry`
                        WHERE
                                posting_date BETWEEN %s AND %s
                                AND account IN %s
                                AND is_cancelled = 0
                        ORDER BY
                                cost_center, account, posting_date, voucher_no
                        """,
                        (from_date, to_date, tuple(direct_expense_accounts)),
                        as_dict=1,
                )
                for e in direct_expense_entries:
                        e["cost_center"] = e["cost_center"] or "No Cost Center"
                        e["posting_date"] = str(e["posting_date"] or "")

        # Fetch Sales Invoice Items details for profit report
        profit_results = frappe.db.sql(
                """
                SELECT
                        sii.cost_center,
                        si.selling_price_list,
                        SUM(sii.base_net_amount) as sales_amount,
                        SUM(sii.qty * sii.incoming_rate) as valuation_amount
                FROM
                        `tabSales Invoice Item` sii
                INNER JOIN
                        `tabSales Invoice` si ON si.name = sii.parent
                WHERE
                        si.posting_date BETWEEN %s AND %s
                        AND si.docstatus = 1
                GROUP BY
                        sii.cost_center, si.selling_price_list
                """,
                (from_date, to_date),
                as_dict=1,
        )

        profit_ccs = {}
        profit_price_lists = set()
        for pr in profit_results:
                cc = pr["cost_center"] or "No Cost Center"
                pl = pr["selling_price_list"] or "Other/Direct"
                profit_price_lists.add(pl)
                
                if cc not in profit_ccs:
                        cc_display_name = cc.split(" - ")[0] if " - " in cc else cc
                        profit_ccs[cc] = {
                                "cost_center": cc,
                                "cost_center_name": cc_display_name,
                                "sales_by_pl": {},
                                "valuation_by_pl": {},
                                "total_sales": 0.0,
                                "valuation_amount": 0.0,
                                "profit": 0.0
                        }
                
                sales_amt = float(pr["sales_amount"] or 0)
                val_amt = float(pr["valuation_amount"] or 0)
                
                profit_ccs[cc]["sales_by_pl"][pl] = sales_amt
                profit_ccs[cc]["valuation_by_pl"][pl] = val_amt
                profit_ccs[cc]["total_sales"] += sales_amt
                profit_ccs[cc]["valuation_amount"] += val_amt

        for cc in profit_ccs:
                profit_ccs[cc]["profit"] = profit_ccs[cc]["total_sales"] - profit_ccs[cc]["valuation_amount"]

        profit_report_data = list(profit_ccs.values())
        profit_report_data.sort(key=lambda x: x["profit"], reverse=True)

        # Fetch item-level details for profit report
        item_profit_results = frappe.db.sql(
                """
                SELECT
                        sii.cost_center,
                        si.selling_price_list,
                        sii.item_code,
                        sii.item_name,
                        SUM(sii.qty) as qty,
                        SUM(sii.base_net_amount) as sales_amount,
                        SUM(sii.qty * sii.incoming_rate) as valuation_amount
                FROM
                        `tabSales Invoice Item` sii
                INNER JOIN
                        `tabSales Invoice` si ON si.name = sii.parent
                WHERE
                        si.posting_date BETWEEN %s AND %s
                        AND si.docstatus = 1
                GROUP BY
                        sii.cost_center, si.selling_price_list, sii.item_code, sii.item_name
                ORDER BY
                        sii.cost_center, si.selling_price_list, sales_amount DESC
                """,
                (from_date, to_date),
                as_dict=1,
        )

        return {
                "report_data": report_data,
                "price_lists": sorted(list(all_price_lists)),
                "bills_data": bills_results,
                "expenses_data": expenses_report_data,
                "direct_expense_entries": direct_expense_entries,
                "direct_expense_heads": sorted(list(direct_heads)),
                "indirect_expense_heads": sorted(list(indirect_heads)),
                "profit_data": profit_report_data,
                "profit_price_lists": sorted(list(profit_price_lists)),
                "item_profit_data": item_profit_results,
        }


@frappe.whitelist()
def get_cashflow_report(from_date=None, to_date=None):
	"""Return Cost Center-wise Cash & Bank inflow, outflow, and net flow."""
	if not from_date:
		from_date = frappe.utils.today()
	if not to_date:
		to_date = frappe.utils.today()

	# Get all Cash and Bank accounts
	cash_bank_accounts = frappe.get_all(
		"Account",
		filters={"account_type": ["in", ["Cash", "Bank"]], "is_group": 0},
		pluck="name"
	)

	if not cash_bank_accounts:
		return {
			"summary": [],
			"breakdown": [],
			"company_name": "",
			"company_address_lines": []
		}

	# Get company info
	company_details = get_company_details()
	company_name = company_details.get("company_name", "")
	company_address_lines = company_details.get("address_lines", [])

	# 1. Summary grouped by Cost Center
	summary_rows = frappe.db.sql(
		"""
		SELECT
			COALESCE(gle.cost_center, '') as cost_center,
			SUM(gle.debit) as inflow,
			SUM(gle.credit) as outflow
		FROM
			`tabGL Entry` gle
		WHERE
			gle.posting_date BETWEEN %s AND %s
			AND gle.is_cancelled = 0
			AND gle.account IN %s
		GROUP BY
			gle.cost_center
		ORDER BY
			gle.cost_center ASC
		""",
		(from_date, to_date, tuple(cash_bank_accounts)),
		as_dict=1
	)

	# 2. Breakdown grouped by Cost Center and Account
	breakdown_rows = frappe.db.sql(
		"""
		SELECT
			COALESCE(gle.cost_center, '') as cost_center,
			gle.account,
			SUM(gle.debit) as inflow,
			SUM(gle.credit) as outflow
		FROM
			`tabGL Entry` gle
		WHERE
			gle.posting_date BETWEEN %s AND %s
			AND gle.is_cancelled = 0
			AND gle.account IN %s
		GROUP BY
			gle.cost_center, gle.account
		ORDER BY
			gle.cost_center ASC, gle.account ASC
		""",
		(from_date, to_date, tuple(cash_bank_accounts)),
		as_dict=1
	)

	# Formulate result
	summary = []
	for r in summary_rows:
		row = dict(r)
		if row["cost_center"]:
			cc_name = frappe.db.get_value("Cost Center", row["cost_center"], "cost_center_name")
			row["cost_center_name"] = cc_name or row["cost_center"].split(" - ")[0]
		else:
			row["cost_center_name"] = "No Cost Center"
			row["cost_center"] = "Unspecified"
		row["inflow"] = float(row["inflow"] or 0)
		row["outflow"] = float(row["outflow"] or 0)
		row["net_flow"] = row["inflow"] - row["outflow"]
		summary.append(row)

	breakdown = []
	for r in breakdown_rows:
		row = dict(r)
		if row["cost_center"]:
			cc_name = frappe.db.get_value("Cost Center", row["cost_center"], "cost_center_name")
			row["cost_center_name"] = cc_name or row["cost_center"].split(" - ")[0]
		else:
			row["cost_center_name"] = "No Cost Center"
			row["cost_center"] = "Unspecified"
		row["inflow"] = float(row["inflow"] or 0)
		row["outflow"] = float(row["outflow"] or 0)
		row["net_flow"] = row["inflow"] - row["outflow"]
		breakdown.append(row)

	return {
		"summary": summary,
		"breakdown": breakdown,
		"company_name": company_name,
		"company_address_lines": company_address_lines
	}


@frappe.whitelist()
def get_stock_aging_report(to_date=None, warehouse=None):
	"""FIFO-based stock ageing (0-30 / 31-60 / 61-90 / 91+ day buckets), item x warehouse-wise.

	Reuses ERPNext's Stock Ageing report logic instead of reimplementing FIFO queue math.
	"""
	from erpnext import get_default_company
	from erpnext.stock.report.stock_ageing.stock_ageing import execute as run_stock_ageing

	to_date = to_date or frappe.utils.nowdate()
	company = frappe.defaults.get_global_default("company") or get_default_company()

	filters = frappe._dict({
		"to_date": to_date,
		"range": "30,60,90",
		"company": company,
		"warehouse": warehouse or None,
		"show_warehouse_wise_stock": 1,
	})

	columns, data, _, _ = run_stock_ageing(filters)
	fieldnames = [c["fieldname"] for c in columns]
	rows = [dict(zip(fieldnames, row)) for row in data]

	return {"rows": rows, "as_on_date": to_date}


@frappe.whitelist()
def get_outstanding_customers_report(as_on_date=None, party_type="Customer"):
	"""Outstanding balance per customer/supplier/employee as on a given date, from the GL party ledger."""
	as_on_date = as_on_date or frappe.utils.today()
	party_type = party_type if party_type in ["Customer", "Supplier", "Employee"] else "Customer"

	join_table = f"tab{party_type}"
	if party_type == "Customer":
		name_field = "customer_name"
	elif party_type == "Supplier":
		name_field = "supplier_name"
	else:
		name_field = "employee_name"

	rows = frappe.db.sql(
		f"""
		SELECT
			gle.party AS customer,
			COALESCE(p.{name_field}, gle.party) AS customer_name,
			SUM(gle.debit) - SUM(gle.credit) AS outstanding_amount,
			MAX(gle.posting_date) AS last_transaction_date
		FROM `tabGL Entry` gle
		LEFT JOIN `{join_table}` p ON p.name = gle.party
		WHERE gle.party_type = %s
		  AND gle.is_cancelled = 0
		  AND gle.posting_date <= %s
		GROUP BY gle.party
		HAVING ABS(SUM(gle.debit) - SUM(gle.credit)) > 0.005
		ORDER BY outstanding_amount DESC
		""",
		(party_type, as_on_date),
		as_dict=True,
	)

	for r in rows:
		r["outstanding_amount"] = float(r["outstanding_amount"] or 0)
		r["last_transaction_date"] = str(r["last_transaction_date"]) if r["last_transaction_date"] else ""

	return {"rows": rows, "as_on_date": as_on_date}


@frappe.whitelist()
def get_ledger_wise_sales_purchase_report(from_date=None, to_date=None):
	"""Get sales and purchase customer/supplier-wise summary report for a date range."""
	if not from_date:
		from_date = frappe.utils.today()
	if not to_date:
		to_date = frappe.utils.today()

	sales_rows = frappe.db.sql(
		"""
		SELECT
			gle.party AS customer,
			COALESCE(c.customer_name, gle.party) AS customer_name,
			SUM(gle.debit) AS debit,
			SUM(gle.credit) AS credit,
			SUM(gle.debit) - SUM(gle.credit) AS net_amount
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` c ON c.name = gle.party
		WHERE gle.voucher_type = 'Sales Invoice'
		  AND gle.party_type = 'Customer'
		  AND gle.is_cancelled = 0
		  AND gle.posting_date BETWEEN %s AND %s
		GROUP BY gle.party
		HAVING ABS(SUM(gle.debit)) > 0.005 OR ABS(SUM(gle.credit)) > 0.005
		ORDER BY net_amount DESC, gle.party
		""",
		(from_date, to_date),
		as_dict=True,
	)

	purchase_rows = frappe.db.sql(
		"""
		SELECT
			gle.party AS supplier,
			COALESCE(s.supplier_name, gle.party) AS supplier_name,
			SUM(gle.debit) AS debit,
			SUM(gle.credit) AS credit,
			SUM(gle.credit) - SUM(gle.debit) AS net_amount
		FROM `tabGL Entry` gle
		LEFT JOIN `tabSupplier` s ON s.name = gle.party
		WHERE gle.voucher_type = 'Purchase Invoice'
		  AND gle.party_type = 'Supplier'
		  AND gle.is_cancelled = 0
		  AND gle.posting_date BETWEEN %s AND %s
		GROUP BY gle.party
		HAVING ABS(SUM(gle.debit)) > 0.005 OR ABS(SUM(gle.credit)) > 0.005
		ORDER BY net_amount DESC, gle.party
		""",
		(from_date, to_date),
		as_dict=True,
	)

	for r in sales_rows:
		r["debit"] = float(r["debit"] or 0)
		r["credit"] = float(r["credit"] or 0)
		r["net_amount"] = float(r["net_amount"] or 0)

	for r in purchase_rows:
		r["debit"] = float(r["debit"] or 0)
		r["credit"] = float(r["credit"] or 0)
		r["net_amount"] = float(r["net_amount"] or 0)

	return {
		"sales": sales_rows,
		"purchase": purchase_rows,
		"from_date": from_date,
		"to_date": to_date
	}

