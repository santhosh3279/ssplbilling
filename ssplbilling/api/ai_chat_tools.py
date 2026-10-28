"""Read-only business tools the AI Chat (ai_chat_api.py) gives Claude.

Every query goes through frappe.get_list, so it runs with the chat user's own role and user
permissions: a user who can't read Sales Invoice or GL Entry in the desk can't read it here
either. Results are grouped per company and never summed across companies, because the
billing system mirrors invoices into the other company (RTN07075 / RTN07075/).
"""

import json

import frappe
from frappe.utils import cint, date_diff, flt, getdate, nowdate

MAX_ROWS = 100
# Cost price is ciphered on screen in the billing app; only these roles see valuation.
VALUATION_ROLES = {"System Manager", "Stock Manager", "Accounts Manager"}

TOOLS = [
	{
		"name": "sales_summary",
		"description": (
			"Sales totals for a date range from submitted Sales Invoices, per company: sales, returns "
			"(credit notes, negative) and net, plus the drafts still waiting at the cashier. Optionally "
			"breaks the period down by customer, item, day or naming series (top rows by amount). "
			"Use for 'sales today', 'sales this month', 'top customers/items', 'daily sales'."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to from_date."},
				"company": {"type": "string", "description": "Exact company name. Omit for all companies."},
				"group_by": {
					"type": "string",
					"enum": ["none", "customer", "item", "day", "series"],
					"description": "Breakdown to add. 'none' returns totals only.",
				},
				"limit": {"type": "integer", "description": f"Breakdown rows per company (max {MAX_ROWS})."},
			},
		},
	},
	{
		"name": "customer_outstanding",
		"description": (
			"Receivable balance from the General Ledger (the same balance the customer ledger page "
			"shows: invoices minus payments, including unallocated advances), per company. Without "
			"`customer`: totals plus the customers who owe the most. With `customer` (name, code or "
			"mobile): that customer's balance and their open invoices with days overdue."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"customer": {"type": "string", "description": "Customer name, code or mobile to look up."},
				"company": {"type": "string", "description": "Exact company name. Omit for all companies."},
				"limit": {"type": "integer", "description": f"Rows to return (max {MAX_ROWS})."},
			},
		},
	},
	{
		"name": "item_stock",
		"description": (
			"Current stock from the warehouse bins. With `item` (code, name or barcode): matching items "
			"with quantity per warehouse. Without `item`: a summary per warehouse (items in stock, total "
			"quantity, items with negative stock)."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"item": {"type": "string", "description": "Item code, part of the item name, or barcode."},
				"warehouse": {"type": "string", "description": "Warehouse name or part of it."},
				"limit": {"type": "integer", "description": f"Items to return (max {MAX_ROWS})."},
			},
		},
	},
]


def run_tool(name, args):
	"""Returns (content, is_error). Permission and validation errors go back to the model as
	tool errors so it can explain them instead of failing the turn."""
	fn = HANDLERS.get(name)
	if not fn:
		return f"Unknown tool: {name}", True
	if not isinstance(args, dict):
		return "Tool input must be an object.", True
	try:
		return json.dumps(fn(**args), default=str, ensure_ascii=False), False
	except frappe.PermissionError:
		frappe.clear_last_message()
		return "The user does not have permission to read this data in ERPNext.", True
	except (frappe.ValidationError, TypeError, ValueError) as e:
		frappe.clear_last_message()
		return f"Invalid request: {e}", True


# ── sales ───────────────────────────────────────────────────────────────────


def sales_summary(from_date=None, to_date=None, company=None, group_by="none", limit=20):
	from_date = getdate(from_date or nowdate())
	to_date = getdate(to_date or from_date)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	if group_by not in (None, "none", *BREAKDOWN_KEYS, "item"):
		raise ValueError(f"group_by must be one of none, customer, item, day, series; got {group_by!r}")
	limit = _limit(limit)
	filters = {"posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company

	submitted = frappe.get_list(
		"Sales Invoice",
		filters={**filters, "docstatus": 1},
		fields=[
			"company",
			"is_return",
			{"COUNT": "*", "as": "invoices"},
			{"SUM": "base_net_total", "as": "net_total"},
			{"SUM": "base_grand_total", "as": "grand_total"},
		],
		group_by="company, is_return",
		limit=0,
	)
	drafts = frappe.get_list(
		"Sales Invoice",
		filters={**filters, "docstatus": 0},
		fields=[
			"company",
			{"COUNT": "*", "as": "invoices"},
			{"SUM": "base_grand_total", "as": "grand_total"},
		],
		group_by="company",
		limit=0,
	)

	companies = {}
	for row in submitted:
		c = companies.setdefault(row.company, _empty_sales())
		key = "returns" if row.is_return else "sales"
		c[key] = {
			"invoices": row.invoices,
			"net_total": flt(row.net_total, 2),
			"grand_total": flt(row.grand_total, 2),
		}
	for row in drafts:
		companies.setdefault(row.company, _empty_sales())["pending_drafts"] = {
			"invoices": row.invoices,
			"grand_total": flt(row.grand_total, 2),
		}
	for c in companies.values():
		c["net_sales"] = flt(c["sales"]["grand_total"] + c["returns"]["grand_total"], 2)

	if group_by and group_by != "none":
		for name, c in companies.items():
			c[f"by_{group_by}"] = _sales_breakdown(group_by, {**filters, "company": name}, limit)

	return {
		"from_date": from_date,
		"to_date": to_date,
		"amounts": "INR, grand_total includes tax, net_total excludes it",
		"companies": companies,
	}


def _empty_sales():
	zero = {"invoices": 0, "net_total": 0.0, "grand_total": 0.0}
	return {"sales": dict(zero), "returns": dict(zero), "pending_drafts": {"invoices": 0, "grand_total": 0.0}}


BREAKDOWN_KEYS = {
	"customer": ["customer", "customer_name"],
	"day": ["posting_date"],
	"series": ["naming_series"],
}


def _sales_breakdown(group_by, filters, limit):
	"""Top rows of submitted invoices (returns netted in) for one company."""
	if group_by == "item":
		parent_filters = [
			["Sales Invoice", k, *(v if isinstance(v, list) else ["=", v])] for k, v in filters.items()
		]
		parent_filters.append(["Sales Invoice", "docstatus", "=", 1])
		return frappe.get_list(
			"Sales Invoice Item",
			parent_doctype="Sales Invoice",
			filters=parent_filters,
			fields=[
				"item_code",
				"item_name",
				"stock_uom",
				{"SUM": "stock_qty", "as": "qty"},
				{"SUM": "base_net_amount", "as": "net_amount"},
			],
			group_by="item_code, item_name, stock_uom",
			order_by="net_amount desc",
			limit=limit,
		)

	keys = BREAKDOWN_KEYS[group_by]
	return frappe.get_list(
		"Sales Invoice",
		filters={**filters, "docstatus": 1},
		fields=[*keys, {"COUNT": "*", "as": "invoices"}, {"SUM": "base_grand_total", "as": "grand_total"}],
		group_by=", ".join(keys),
		order_by="posting_date asc" if group_by == "day" else "grand_total desc",
		limit=limit,
	)


# ── receivables ─────────────────────────────────────────────────────────────


def customer_outstanding(customer=None, company=None, limit=20):
	limit = _limit(limit)
	if customer:
		return _one_customer(customer, company, limit)

	filters = {"party_type": "Customer", "is_cancelled": 0}
	if company:
		filters["company"] = company
	balances = _gl_balances(filters, ["party", "company"])

	companies = {}
	for row in balances:
		c = companies.setdefault(
			row["company"], {"receivable": 0.0, "advances": 0.0, "customers_owing": 0, "top": []}
		)
		if row["balance"] > 0:
			c["receivable"] += row["balance"]
			c["customers_owing"] += 1
			c["top"].append(row)
		elif row["balance"] < 0:
			c["advances"] += row["balance"]

	names = set()
	for c in companies.values():
		c["receivable"] = flt(c["receivable"], 2)
		c["advances"] = flt(c["advances"], 2)
		c["top"] = sorted(c["top"], key=lambda r: r["balance"], reverse=True)[:limit]
		names.update(r["party"] for r in c["top"])
	labels = _customer_names(names)
	for c in companies.values():
		c["top"] = [
			{"customer": r["party"], "customer_name": labels.get(r["party"]), "balance": r["balance"]}
			for r in c["top"]
		]

	return {
		"as_of": nowdate(),
		"note": "receivable = sum of positive balances; advances = customers in credit (negative)",
		"companies": companies,
	}


def _one_customer(search, company, limit):
	matches = _find_customers(search)
	if not matches:
		return {"found": False, "message": f"No customer matches '{search}'."}
	exact = [m for m in matches if search.lower() in (m.name.lower(), (m.customer_name or "").lower())]
	if len(matches) > 1 and len(exact) != 1:
		return {"found": False, "message": "Several customers match; ask which one.", "candidates": matches}
	cust = exact[0] if exact else matches[0]

	filters = {"party_type": "Customer", "party": cust.name, "is_cancelled": 0}
	if company:
		filters["company"] = company
	balances = {r["company"]: r["balance"] for r in _gl_balances(filters, ["company"])}

	inv_filters = {"customer": cust.name, "docstatus": 1, "outstanding_amount": ["!=", 0]}
	if company:
		inv_filters["company"] = company
	invoices = frappe.get_list(
		"Sales Invoice",
		filters=inv_filters,
		fields=["name", "company", "posting_date", "due_date", "grand_total", "outstanding_amount"],
		order_by="posting_date asc",
		limit=limit,
	)
	today = getdate()
	for inv in invoices:
		inv["days_overdue"] = max(date_diff(today, inv.due_date or inv.posting_date), 0)

	return {
		"found": True,
		"customer": cust.name,
		"customer_name": cust.customer_name,
		"mobile_no": cust.mobile_no,
		"as_of": nowdate(),
		"balance_by_company": balances,
		"open_invoices": invoices,
		"open_invoices_shown": len(invoices),
	}


def _gl_balances(filters, keys):
	rows = frappe.get_list(
		"GL Entry",
		filters=filters,
		fields=[*keys, {"SUM": "debit", "as": "debit"}, {"SUM": "credit", "as": "credit"}],
		group_by=", ".join(keys),
		limit=0,
	)
	out = []
	for r in rows:
		balance = flt(flt(r.debit) - flt(r.credit), 2)
		if balance:
			out.append({**{k: r[k] for k in keys}, "balance": balance})
	return out


def _find_customers(search):
	like = f"%{search}%"
	return frappe.get_list(
		"Customer",
		or_filters={"name": ["like", like], "customer_name": ["like", like], "mobile_no": ["like", like]},
		fields=["name", "customer_name", "mobile_no"],
		limit=10,
	)


def _customer_names(names):
	if not names:
		return {}
	rows = frappe.get_list(
		"Customer", filters={"name": ["in", list(names)]}, fields=["name", "customer_name"], limit=0
	)
	return {r.name: r.customer_name for r in rows}


# ── stock ───────────────────────────────────────────────────────────────────


def item_stock(item=None, warehouse=None, limit=20):
	limit = _limit(limit)
	show_value = bool(VALUATION_ROLES & set(frappe.get_roles()))
	value_fields = ["valuation_rate", "stock_value"] if show_value else []
	bin_filters = {}
	if warehouse:
		bin_filters["warehouse"] = ["like", f"%{warehouse}%"]
	# Each company keeps its own warehouses (mirrored billing), so totals are per company.
	company_of = dict(frappe.get_list("Warehouse", fields=["name", "company"], as_list=True, limit=0))

	if not item:
		fields = [
			"warehouse",
			{"COUNT": "*", "as": "items_in_stock"},
			{"SUM": "actual_qty", "as": "total_qty"},
		]
		if show_value:
			fields.append({"SUM": "stock_value", "as": "stock_value"})
		summary = frappe.get_list(
			"Bin",
			filters={**bin_filters, "actual_qty": [">", 0]},
			fields=fields,
			group_by="warehouse",
			limit=0,
		)
		negative = frappe.get_list(
			"Bin",
			filters={**bin_filters, "actual_qty": ["<", 0]},
			fields=["warehouse", {"COUNT": "*", "as": "items"}],
			group_by="warehouse",
			limit=0,
		)
		negative = {r.warehouse: r["items"] for r in negative}
		for row in summary:
			row["company"] = company_of.get(row.warehouse)
			row["items_negative"] = negative.get(row.warehouse, 0)
		return {"as_of": nowdate(), "valuation_shown": show_value, "warehouses": summary}

	items = _find_items(item, limit)
	if not items:
		return {"found": False, "message": f"No item matches '{item}'."}
	bins = frappe.get_list(
		"Bin",
		filters={**bin_filters, "item_code": ["in", [i.name for i in items]]},
		fields=["item_code", "warehouse", "actual_qty", "reserved_qty", "projected_qty", *value_fields],
		order_by="item_code asc, warehouse asc",
		limit=0,
	)
	by_item = {}
	for b in bins:
		if b.actual_qty or b.reserved_qty or b.projected_qty:
			b["company"] = company_of.get(b.warehouse)
			by_item.setdefault(b.pop("item_code"), []).append(b)

	result = []
	for i in items:
		rows = by_item.get(i.name, [])
		qty_by_company = {}
		for b in rows:
			qty_by_company[b.company] = flt(qty_by_company.get(b.company, 0) + flt(b.actual_qty), 3)
		result.append(
			{
				"item_code": i.name,
				"item_name": i.item_name,
				"uom": i.stock_uom,
				"disabled": bool(i.disabled),
				"qty_by_company": qty_by_company,
				"warehouses": rows,
			}
		)
	return {"as_of": nowdate(), "found": True, "valuation_shown": show_value, "items": result}


def _find_items(search, limit):
	barcode_hits = frappe.get_list(
		"Item Barcode", parent_doctype="Item", filters={"barcode": search}, pluck="parent", limit=5
	)
	like = f"%{search}%"
	return frappe.get_list(
		"Item",
		filters={"is_stock_item": 1},
		or_filters={
			"name": ["in", [search, *barcode_hits]],
			"item_code": ["like", like],
			"item_name": ["like", like],
		},
		fields=["name", "item_name", "stock_uom", "disabled"],
		order_by="disabled asc, item_name asc",
		limit=limit,
	)


def _limit(value):
	return min(max(cint(value) or 20, 1), MAX_ROWS)


HANDLERS = {
	"sales_summary": sales_summary,
	"customer_outstanding": customer_outstanding,
	"item_stock": item_stock,
}
