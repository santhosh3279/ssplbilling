"""Read-only business tools (and the shared instructions) the AI Chat gives Claude or Gemini.

Every query goes through frappe.get_list, so it runs with the chat user's own role and user
permissions: a user who can't read Sales Invoice or GL Entry in the desk can't read it here
either. Results are grouped per company and never summed across companies, because the
billing system mirrors invoices into the other company (RTN07075 / RTN07075/).
"""

import json
from contextlib import contextmanager

import frappe
from frappe.utils import cint, date_diff, flt, get_first_day, getdate, nowdate

MAX_ROWS = 100
# Excel exports re-run a tool with this cap instead; the rows go to the file, not the model.
EXPORT_ROWS = 5000
_row_cap = {"max": MAX_ROWS}
_scope = {"company": None, "cost_center": None}
DATA_TOOLS = ("sales_summary", "customer_outstanding", "item_stock", "account_ledger")
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
				"company": {
					"type": "string",
					"description": 'Exact company name. Omit to use the company selected on the chat page; "all" for every company.',
				},
				"cost_center": {
					"type": "string",
					"description": 'Exact cost center name (branch), e.g. "NCK - SSPL". Omit to use the one selected on the chat page; "all" for every cost center.',
				},
				"group_by": {
					"type": "string",
					"enum": ["none", "customer", "item", "day", "month", "series"],
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
				"company": {
					"type": "string",
					"description": 'Exact company name. Omit to use the company selected on the chat page; "all" for every company.',
				},
				"cost_center": {
					"type": "string",
					"description": 'Exact cost center name (branch), e.g. "NCK - SSPL". Omit to use the one selected on the chat page; "all" for every cost center.',
				},
				"limit": {"type": "integer", "description": f"Rows to return (max {MAX_ROWS})."},
			},
		},
	},
	{
		"name": "item_stock",
		"description": (
			"Current stock from the warehouse bins. With `item` (code, name or barcode): matching items "
			"with quantity per warehouse. Without `item`: a summary per warehouse (items in stock, total "
			"quantity, items with negative stock). Stock is per warehouse: the selected cost center does "
			"not apply, the selected company does."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"item": {"type": "string", "description": "Item code, part of the item name, or barcode."},
				"warehouse": {"type": "string", "description": "Warehouse name or part of it."},
				"company": {
					"type": "string",
					"description": 'Exact company name. Omit to use the company selected on the chat page; "all" for every company.',
				},
				"limit": {"type": "integer", "description": f"Items to return (max {MAX_ROWS})."},
			},
		},
	},
	{
		"name": "account_ledger",
		"description": (
			"General Ledger of one account (bank, UPI wallet, cash, expense, income, or a group account "
			"with all its children) for a date range: opening, debit, credit, closing, and where the money "
			"went or came from (the other accounts in the same vouchers). Use `against` to pick out one "
			"kind of contra entry, e.g. account='PAYTM NCK UPI', against='bank charges' answers 'bank "
			"charges in Paytm NCK UPI this month'. view: summary (totals + contra accounts), entries "
			"(voucher lines with running balance), day or month (period totals)."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"account": {"type": "string", "description": "Account name, part of it, or account number."},
				"from_date": {
					"type": "string",
					"description": "YYYY-MM-DD. Defaults to the 1st of this month.",
				},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"against": {
					"type": "string",
					"description": "Only count the vouchers that also hit an account whose name contains this text, e.g. 'bank charges', 'hdfc'.",
				},
				"view": {"type": "string", "enum": ["summary", "entries", "day", "month"]},
				"company": {
					"type": "string",
					"description": 'Exact company name. Omit to use the company selected on the chat page; "all" for every company.',
				},
				"cost_center": {
					"type": "string",
					"description": 'Exact cost center name (branch). Omit to use the one selected on the chat page; "all" for every cost center.',
				},
				"limit": {"type": "integer", "description": f"Rows to return (max {MAX_ROWS})."},
			},
			"required": ["account"],
		},
	},
]


INSTRUCTIONS = """You are the business assistant for Sundaram and Sons Private Ltd (SSPL), a wholesale business, answering staff questions from live ERPNext data.
- Use the tools for every figure; never invent numbers, names or document ids. If no tool covers the question, say what you can answer (sales, receivables, stock, account ledgers).
- You are read-only. If asked to create or change anything, say so and point to the screen in the app where it is done.
- Amounts are INR (₹) with Indian grouping (₹1,25,000). Keep answers short; use markdown tables for lists.
- State the date range, company and cost center you used (each tool result says which it applied). "Today" means the date given below.
- The user picks a company and cost center on the chat page; the tools use them when you omit company / cost_center. Only pass them when the user names another one, or "all" when they ask for every company or branch.
- Data is per company. An invoice ending in "/" (RTN07075/) is the billing system's mirror of RTN07075 in the other company, so company totals overlap by design: report each company separately and never add companies together unless the user asks.
- Returns (credit notes) are negative. Pending drafts are sales still waiting at the cashier; mention them separately from submitted sales.
- If a tool says the user lacks permission, tell them they don't have access to that data.
- For "Excel", "download" or "export", call export_excel; for "chart", "graph" or "trend", call make_chart. Pass the same tool and args you would use to answer. The file or chart is attached to your reply automatically: don't repeat its rows in text, just say what it contains."""


def system_prompt(settings):
	"""Provider-neutral instructions for both runners."""
	today = getdate(nowdate())
	companies = ", ".join(frappe.get_all("Company", pluck="name", order_by="name asc"))
	extra = (settings.system_prompt or "").strip()
	return "\n\n".join(
		p
		for p in (
			INSTRUCTIONS,
			f"Today is {today.isoformat()} ({today.strftime('%A')}). Companies: {companies}.",
			extra,
		)
		if p
	)


OUTPUT_TOOLS = ("export_excel", "make_chart")
_SOURCE = {
	"tool": {
		"type": "string",
		"enum": list(DATA_TOOLS),
		"description": "Which data tool to take the data from.",
	},
	"args": {
		"type": "object",
		"description": 'Arguments for that tool, as you would pass them to it directly (e.g. {"from_date": "2026-10-01", "group_by": "item"}).',
	},
	"title": {"type": "string", "description": "Short title, e.g. 'Sales by item, October 2026'."},
}
TOOLS += [
	{
		"name": "export_excel",
		"description": (
			f"Make a downloadable Excel file from one of the data tools, with up to {EXPORT_ROWS} rows (not the "
			"short list the tool returns to you), one sheet per company. The rows go straight into the file."
		),
		"input_schema": {"type": "object", "properties": _SOURCE, "required": ["tool", "title"]},
	},
	{
		"name": "make_chart",
		"description": (
			"Show a chart in the chat built from one of the data tools. Use line for sales by day or month, "
			"bar for comparing customers, items, warehouses or companies, pie only for a few shares of one total."
		),
		"input_schema": {
			"type": "object",
			"properties": {**_SOURCE, "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]}},
			"required": ["tool", "title", "chart_type"],
		},
	},
]


def run_tool(name, args, attachments=None):
	"""Returns (content, is_error). Permission and validation errors go back to the model as
	tool errors so it can explain them instead of failing the turn. export_excel / make_chart
	append the file or chart to `attachments`, which the runner saves on the reply."""
	if name in OUTPUT_TOOLS:
		from ssplbilling.api import ai_chat_export

		fn = getattr(ai_chat_export, name)
		args = {**(args if isinstance(args, dict) else {}), "attachments": attachments}
	else:
		fn = HANDLERS.get(name)
	if not fn:
		return f"Unknown tool: {name}", True
	if not isinstance(args, dict):
		return "Tool input must be an object.", True
	try:
		# Compact JSON: every byte of a tool result is billed as input on this and later turns.
		return json.dumps(fn(**args), default=str, ensure_ascii=False, separators=(",", ":")), False
	except frappe.PermissionError:
		frappe.clear_last_message()
		return "The user does not have permission to read this data in ERPNext.", True
	except (frappe.ValidationError, TypeError, ValueError) as e:
		frappe.clear_last_message()
		return f"Invalid request: {e}", True


# ── sales ───────────────────────────────────────────────────────────────────


def sales_summary(from_date=None, to_date=None, company=None, cost_center=None, group_by="none", limit=10):
	from_date = getdate(from_date or nowdate())
	to_date = getdate(to_date or from_date)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	if group_by not in (None, "none", *BREAKDOWN_KEYS, "item", "month"):
		raise ValueError(
			f"group_by must be one of none, customer, item, day, month, series; got {group_by!r}"
		)
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	filters = {"posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center

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
		**_scope_note(company, cost_center),
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
	if group_by == "month":
		# Fold the daily rows: every day is needed, whatever the row limit.
		months = {}
		for day in _sales_breakdown("day", filters, EXPORT_ROWS):
			m = months.setdefault(
				str(day.posting_date)[:7],
				{"month": str(day.posting_date)[:7], "invoices": 0, "grand_total": 0.0},
			)
			m["invoices"] += day.invoices
			m["grand_total"] = flt(m["grand_total"] + flt(day.grand_total), 2)
		return list(months.values())
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
	rows = frappe.get_list(
		"Sales Invoice",
		filters={**filters, "docstatus": 1},
		fields=[*keys, {"COUNT": "*", "as": "invoices"}, {"SUM": "base_grand_total", "as": "grand_total"}],
		group_by=", ".join(keys),
		order_by="posting_date asc" if group_by == "day" else "grand_total desc",
		limit=limit,
	)
	for r in rows:
		_drop_same_name(r, "customer")
	return rows


# ── receivables ─────────────────────────────────────────────────────────────


def customer_outstanding(customer=None, company=None, cost_center=None, limit=10):
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	if customer:
		return _one_customer(customer, company, cost_center, limit)

	filters = {"party_type": "Customer", "is_cancelled": 0}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center
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
			_drop_same_name(
				{"customer": r["party"], "customer_name": labels.get(r["party"]), "balance": r["balance"]},
				"customer",
			)
			for r in c["top"]
		]

	return {
		"as_of": nowdate(),
		**_scope_note(company, cost_center),
		"note": "receivable = sum of positive balances; advances = customers in credit (negative)",
		"companies": companies,
	}


def _one_customer(search, company, cost_center, limit):
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
	if cost_center:
		filters["cost_center"] = cost_center
	balances = {r["company"]: r["balance"] for r in _gl_balances(filters, ["company"])}

	inv_filters = {"customer": cust.name, "docstatus": 1, "outstanding_amount": ["!=", 0]}
	if company:
		inv_filters["company"] = company
	if cost_center:
		inv_filters["cost_center"] = cost_center
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
		**_scope_note(company, cost_center),
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


# ── ledger ──────────────────────────────────────────────────────────────────

BALANCE_SHEET = ("Asset", "Liability", "Equity")
LEDGER_VIEWS = ("summary", "entries", "day", "month")
_CHUNK = 500


def account_ledger(
	account=None,
	from_date=None,
	to_date=None,
	against=None,
	company=None,
	cost_center=None,
	view="summary",
	limit=10,
):
	if not account:
		raise ValueError("account is required, e.g. 'PAYTM NCK UPI' or 'bank charges'")
	view = view or "summary"
	if view not in LEDGER_VIEWS:
		raise ValueError(f"view must be one of {', '.join(LEDGER_VIEWS)}; got {view!r}")
	from_date = getdate(from_date or get_first_day(nowdate()))
	to_date = getdate(to_date or nowdate())
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)

	acc = _find_account(account, company)
	if acc.get("found") is False:
		return acc
	accounts = acc.pop("accounts")
	base = {"account": ["in", accounts], "is_cancelled": 0}
	if cost_center:
		base["cost_center"] = cost_center

	# One row per voucher: everything below is built from these.
	vouchers = frappe.get_list(
		"GL Entry",
		filters={**base, "posting_date": ["between", [from_date, to_date]]},
		fields=[
			"voucher_type",
			"voucher_no",
			"posting_date",
			{"SUM": "debit", "as": "debit"},
			{"SUM": "credit", "as": "credit"},
		],
		group_by="voucher_type, voucher_no, posting_date",
		order_by="posting_date asc",
		limit=0,
	)
	opening = None
	if acc["root_type"] in BALANCE_SHEET:
		opening = sum(
			r["balance"] for r in _gl_balances({**base, "posting_date": ["<", from_date]}, ["company"])
		)
	debit = flt(sum(flt(v.debit) for v in vouchers), 2)
	credit = flt(sum(flt(v.credit) for v in vouchers), 2)

	result = {
		**acc,
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(acc["company"], cost_center),
		"sign": "amounts are debit - credit: positive = Dr, negative = Cr",
		"opening_balance": None if opening is None else flt(opening, 2),
		"debit": debit,
		"credit": credit,
		"net": flt(debit - credit, 2),
		"closing_balance": None if opening is None else flt(opening + debit - credit, 2),
		"vouchers": len(vouchers),
	}
	if opening is None:
		result["note"] = "income/expense account: no opening balance, net is the period total"

	contra = _contra(vouchers, accounts) if view == "summary" or against else {}
	if against:
		needle = against.casefold()
		contra = {
			key: {a: amt for a, amt in by_acc.items() if needle in a.casefold()}
			for key, by_acc in contra.items()
		}
		contra = {key: by_acc for key, by_acc in contra.items() if by_acc}
		vouchers = [v for v in vouchers if (v.voucher_type, v.voucher_no) in contra]
		result["against_filter"] = against
		result["against_total"] = flt(sum(sum(by_acc.values()) for by_acc in contra.values()), 2)
		result["against_vouchers"] = len(vouchers)
		result["against_note"] = (
			"against_total is what the matching accounts were debited (+) or credited (-)"
		)

	if view == "summary":
		totals = {}
		for by_acc in contra.values():
			for a, amt in by_acc.items():
				t = totals.setdefault(a, {"account": a, "amount": 0.0, "vouchers": 0})
				t["amount"] = flt(t["amount"] + amt, 2)
				t["vouchers"] += 1
		result["by_against"] = sorted(totals.values(), key=lambda t: abs(t["amount"]), reverse=True)[:limit]
	elif view == "entries":
		period = {**base, "posting_date": ["between", [from_date, to_date]]}
		result["entries"] = _ledger_entries(period, vouchers, contra if against else None, opening, limit)
	else:
		periods = {}
		for v in vouchers:
			key = str(v.posting_date)[:7] if view == "month" else str(v.posting_date)
			p = periods.setdefault(key, {view: key, "debit": 0.0, "credit": 0.0, "vouchers": 0})
			p["debit"] = flt(p["debit"] + flt(v.debit), 2)
			p["credit"] = flt(p["credit"] + flt(v.credit), 2)
			p["vouchers"] += 1
			if against:
				p["amount"] = flt(
					p.get("amount", 0) + sum(contra[(v.voucher_type, v.voucher_no)].values()), 2
				)
		for p in periods.values():
			p["net"] = flt(p["debit"] - p["credit"], 2)
		result[f"by_{view}"] = list(periods.values())[-limit:]
	return result


def _find_account(search, company):
	"""The account (or group of accounts) to read, or {"found": False, ...} to ask the user."""
	filters = {"company": company} if company else {}
	like = f"%{search}%"
	matches = frappe.get_list(
		"Account",
		filters=filters,
		or_filters={"name": ["like", like], "account_name": ["like", like], "account_number": ["like", like]},
		fields=["name", "account_name", "company", "root_type", "is_group", "lft", "rgt"],
		order_by="is_group asc, name asc",
		limit=20,
	)
	if not matches:
		return {"found": False, "message": f"No account matches '{search}'."}
	needle = search.casefold()
	exact = [m for m in matches if needle in (m.name.casefold(), (m.account_name or "").casefold())]
	if len(exact) == 1:
		acc = exact[0]
	elif len(matches) == 1:
		acc = matches[0]
	else:
		return {
			"found": False,
			"message": "Several accounts match; ask which one.",
			"candidates": [m.name for m in (exact or matches)],
		}
	accounts = [acc.name]
	if acc.is_group:
		accounts = frappe.get_list(
			"Account",
			filters={"company": acc.company, "lft": [">=", acc.lft], "rgt": ["<=", acc.rgt], "is_group": 0},
			pluck="name",
			limit=0,
		) or [""]
	return {
		"found": True,
		"account": acc.name,
		"is_group": bool(acc.is_group),
		"child_accounts": len(accounts) if acc.is_group else None,
		"root_type": acc.root_type,
		"company": acc.company,
		"accounts": accounts,
	}


def _contra(vouchers, accounts):
	"""{(voucher_type, voucher_no): {other account: debit - credit}} for the given vouchers.

	The other lines of a voucher are where the account's money went or came from. In a voucher
	with several lines on both sides this is the whole other side, not a per-line split."""
	by_type = {}
	for v in vouchers:
		by_type.setdefault(v.voucher_type, []).append(v.voucher_no)
	out = {}
	for vtype, names in by_type.items():
		for i in range(0, len(names), _CHUNK):
			rows = frappe.get_list(
				"GL Entry",
				filters={
					"voucher_type": vtype,
					"voucher_no": ["in", names[i : i + _CHUNK]],
					"account": ["not in", accounts],
					"is_cancelled": 0,
				},
				fields=[
					"voucher_no",
					"account",
					{"SUM": "debit", "as": "debit"},
					{"SUM": "credit", "as": "credit"},
				],
				group_by="voucher_no, account",
				limit=0,
			)
			for r in rows:
				amount = flt(flt(r.debit) - flt(r.credit), 2)
				if amount:
					out.setdefault((vtype, r.voucher_no), {})[r.account] = amount
	return out


def _ledger_entries(filters, vouchers, contra, opening, limit):
	"""Voucher lines in date order with a running balance (from the opening, when there is one).
	With `contra` (an `against` filter) only the matching vouchers, and no running balance."""
	if contra is not None:
		filters = {**filters, "voucher_no": ["in", [v.voucher_no for v in vouchers] or [""]]}
	rows = frappe.get_list(
		"GL Entry",
		filters=filters,
		fields=[
			"posting_date",
			"voucher_type",
			"voucher_no",
			"party",
			"debit",
			"credit",
			"against",
			"remarks",
		],
		order_by="posting_date asc, creation asc",
		limit=limit,
	)
	balance = opening or 0.0
	out = []
	for r in rows:
		balance = flt(balance + flt(r.debit) - flt(r.credit), 2)
		row = {
			"posting_date": r.posting_date,
			"voucher_type": r.voucher_type,
			"voucher_no": r.voucher_no,
			"debit": flt(r.debit, 2),
			"credit": flt(r.credit, 2),
			"balance": balance if contra is None else None,
			"against": (r.against or "")[:80],
			"party": r.party,
			"remarks": (r.remarks or "")[:80] or None,
		}
		if contra is not None:
			row["against_amount"] = flt(sum(contra.get((r.voucher_type, r.voucher_no), {}).values()), 2)
		out.append({k: v for k, v in row.items() if v not in (None, "")})
	return out


# ── stock ───────────────────────────────────────────────────────────────────


def item_stock(item=None, warehouse=None, company=None, limit=10):
	limit = _limit(limit)
	company, _cost_center = _scoped(company, None)
	show_value = bool(VALUATION_ROLES & set(frappe.get_roles()))
	value_fields = ["valuation_rate", "stock_value"] if show_value else []
	# Each company keeps its own warehouses (mirrored billing), so totals are per company.
	company_of = dict(frappe.get_list("Warehouse", fields=["name", "company"], as_list=True, limit=0))
	bin_filters = {}
	if company or warehouse:
		bin_filters["warehouse"] = [
			"in",
			[
				w
				for w, c in company_of.items()
				if (not company or c == company) and (not warehouse or warehouse.lower() in w.lower())
			]
			or [""],
		]

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
		# A warehouse holding only negative stock has no row in `summary`; still list it.
		listed = {r.warehouse for r in summary}
		summary += [
			frappe._dict(warehouse=w, items_in_stock=0, total_qty=0) for w in negative if w not in listed
		]
		for row in summary:
			row["company"] = company_of.get(row.warehouse)
			row["items_negative"] = negative.get(row.warehouse, 0)
		return {
			"as_of": nowdate(),
			**_scope_note(company, None),
			"valuation_shown": show_value,
			"warehouses": summary,
		}

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
	return {
		"as_of": nowdate(),
		**_scope_note(company, None),
		"found": True,
		"valuation_shown": show_value,
		"items": result,
	}


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


def _drop_same_name(row, key):
	"""Most customers are named by their own name: don't send it twice."""
	if (row.get("customer_name") or "").casefold() == (row.get(key) or "").casefold():
		row.pop("customer_name", None)
	return row


def _limit(value):
	return min(max(cint(value) or 10, 1), _row_cap["max"])


@contextmanager
def scope(company=None, cost_center=None):
	"""The company / cost center picked on the chat page, used when a tool call omits them."""
	_scope.update(company=company or None, cost_center=cost_center or None)
	try:
		yield
	finally:
		_scope.update(company=None, cost_center=None)


def _scoped(company, cost_center):
	"""Resolve a tool's company / cost_center args against the chat scope. "all" clears it."""
	if company in (None, ""):
		company = _scope["company"]
	if cost_center in (None, ""):
		cost_center = _scope["cost_center"]
	company = None if str(company).lower() == "all" else company
	cost_center = None if str(cost_center).lower() == "all" else cost_center
	if cost_center:
		cc_company = frappe.db.get_value("Cost Center", cost_center, "company")
		if not cc_company:
			raise ValueError(f"No cost center named {cost_center!r}.")
		if company and cc_company != company:
			# The chat's cost center belongs to another company than the one asked about.
			if cost_center == _scope["cost_center"]:
				cost_center = None
			else:
				raise ValueError(f"Cost center {cost_center} belongs to {cc_company}, not {company}.")
		company = company or cc_company
	return company, cost_center


def _scope_note(company, cost_center):
	return {
		"company_filter": company or "all companies",
		"cost_center_filter": cost_center or "all cost centers",
	}


@contextmanager
def export_rows():
	"""Raise the row cap while a tool is re-run for a file or a chart."""
	_row_cap["max"] = EXPORT_ROWS
	try:
		yield
	finally:
		_row_cap["max"] = MAX_ROWS


HANDLERS = {
	"sales_summary": sales_summary,
	"customer_outstanding": customer_outstanding,
	"item_stock": item_stock,
	"account_ledger": account_ledger,
}
