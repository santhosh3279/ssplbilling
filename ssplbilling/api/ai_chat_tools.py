"""Read-only business tools (and the shared instructions) the AI Chat gives Claude or Gemini.

Every query goes through _get_list, which runs frappe.get_list with the chat user's own role and
user permissions (a user who can't read Sales Invoice in the desk can't read it here either), or
ignores them when Full Read Access is on in SSPL Assistant Settings. Results are grouped per company and never summed across companies, because the
billing system mirrors invoices into the other company (RTN07075 / RTN07075/).
"""

import json
import re
from contextlib import contextmanager

import frappe
from frappe.utils import cint, date_diff, flt, get_first_day, getdate, nowdate

MAX_ROWS = 100
# Excel exports re-run a tool with this cap instead; the rows go to the file, not the model.
EXPORT_ROWS = 5000
_row_cap = {"max": MAX_ROWS}
_scope = {"company": None, "cost_center": None}
DATA_TOOLS = (
	"sales_summary",
	"top_items",
	"purchase_summary",
	"customer_outstanding",
	"supplier_outstanding",
	"customer_activity",
	"item_stock",
	"item_movement",
	"account_ledger",
	"cash_bank_position",
	"profit_loss",
	"gst_summary",
	"payments_summary",
	"query_records",
)
# Cost price is ciphered on screen in the billing app; only these roles see valuation.
VALUATION_ROLES = {"System Manager", "Stock Manager", "Accounts Manager"}
# Modules query_records / describe_doctype may read; the specific tools above cover the rest.
QUERY_MODULES = {
	# ERPNext
	"Accounts",
	"Assets",
	"Buying",
	"CRM",
	"Maintenance",
	"Manufacturing",
	"Projects",
	"Quality Management",
	"Regional",
	"Selling",
	"Setup",
	"Stock",
	"Subcontracting",
	"Support",
	# HRMS, India Compliance, this app, addresses / contacts
	"HR",
	"Payroll",
	"GST India",
	"Income Tax India",
	"Ssplbilling",
	"Contacts",
}
# The assistant's own chats and settings (API keys) are never open to it.
QUERY_DENIED_PREFIX = "SSPL Assistant"
QUERY_HIDDEN_FIELDTYPES = {"Password", "Attach", "Attach Image", "Code", "Signature"}
QUERY_OPERATORS = {
	"=",
	"!=",
	">",
	"<",
	">=",
	"<=",
	"like",
	"not like",
	"in",
	"not in",
	"between",
	"is",
}
QUERY_AGGREGATES = {"sum": "SUM", "count": "COUNT", "avg": "AVG", "min": "MIN", "max": "MAX"}

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
		"name": "top_items",
		"description": (
			"Pareto / ABC of item-wise sales: ranks the items sold by net sales (returns netted in) and "
			"returns the top items that together make `share` percent (default 80) of the period's net "
			"sales, per company, with each item's share and cumulative share, plus how many items that "
			"is out of all items sold. Use for 'top 20% items', 'items making 80% of sales', 'A-class items'."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to the 1st of this month."},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"company": {
					"type": "string",
					"description": 'Exact company name. Omit to use the company selected on the chat page; "all" for every company.',
				},
				"cost_center": {
					"type": "string",
					"description": 'Exact cost center name (branch). Omit to use the one selected on the chat page; "all" for every cost center.',
				},
				"share": {
					"type": "number",
					"description": "Cumulative percent of net sales the top items must reach (1-100). Default 80.",
				},
				"limit": {"type": "integer", "description": f"Item rows per company (max {MAX_ROWS})."},
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

_COMPANY = {
	"type": "string",
	"description": (
		"Exact company name. Omit it to use the company selected on the chat page (the default). Pass "
		'it only when the user names another company; "all" only when they ask for all / both companies.'
	),
}
_COST_CENTER = {
	"type": "string",
	"description": (
		"Exact cost center name (branch). Omit it to use the one selected on the chat page (the default). "
		'Pass it only when the user names another branch; "all" only when they ask for every branch.'
	),
}
_FROM = {"type": "string", "description": "YYYY-MM-DD. Defaults to the 1st of this month."}
_TO = {"type": "string", "description": "YYYY-MM-DD. Defaults to today."}
_LIMIT = {"type": "integer", "description": f"Rows to return (max {MAX_ROWS})."}

TOOLS += [
	{
		"name": "purchase_summary",
		"description": (
			"Purchase totals for a date range from submitted Purchase Invoices, per company: purchases, "
			"returns (negative), net and drafts. Optional breakdown by supplier, item, day, month or series."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to from_date."},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"group_by": {
					"type": "string",
					"enum": ["none", "supplier", "item", "day", "month", "series"],
				},
				"limit": _LIMIT,
			},
		},
	},
	{
		"name": "supplier_outstanding",
		"description": (
			"What we owe suppliers, from the General Ledger, per company (positive = we owe). Without "
			"`supplier`: totals and the suppliers owed most. With `supplier`: balance and unpaid bills."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"supplier": {"type": "string", "description": "Supplier name, code or mobile."},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": _LIMIT,
			},
		},
	},
	{
		"name": "customer_activity",
		"description": (
			"Buying pattern. With `customer`: first / last invoice, days since last, average gap, monthly "
			"totals for 12 months. Without: customers who bought in the last year but not in `days` days."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"customer": {"type": "string", "description": "Customer name, code or mobile."},
				"days": {
					"type": "integer",
					"description": "Lapsed = no purchase in this many days. Default 60.",
				},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": _LIMIT,
			},
		},
	},
	{
		"name": "item_movement",
		"description": (
			"Stock movement from the stock ledger. movement: one item's opening, in, out, closing per "
			"warehouse by voucher type. fast: most sold items by qty. not_sold: items in stock with no sale in `days` days."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"item": {"type": "string", "description": "Item code, name or barcode (for movement)."},
				"view": {"type": "string", "enum": ["movement", "fast", "not_sold"]},
				"from_date": _FROM,
				"to_date": _TO,
				"days": {"type": "integer", "description": "For not_sold. Default 90."},
				"warehouse": {"type": "string", "description": "Warehouse name or part of it."},
				"company": _COMPANY,
				"limit": _LIMIT,
			},
		},
	},
	{
		"name": "cash_bank_position",
		"description": (
			"Balances of every cash, coin, bank and UPI / card account as of a date, per company, "
			"grouped (Cash In Hand, Bank Accounts, UPI...). Use for 'cash in hand', 'bank balance'."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"as_of": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"account": {
					"type": "string",
					"description": "Only accounts or groups whose name contains this.",
				},
				"company": _COMPANY,
			},
		},
	},
	{
		"name": "profit_loss",
		"description": (
			"Profit and loss from the General Ledger for a date range, per company: income, expense, net "
			"profit, totals per group (Direct / Indirect Income / Expenses) and the biggest accounts."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": _FROM,
				"to_date": _TO,
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": _LIMIT,
			},
		},
	},
	{
		"name": "gst_summary",
		"description": (
			"GST collected (output) vs paid (input credit) from the GST accounts, per company, by CGST / "
			"SGST / IGST, net payable, reverse charge apart, plus taxable sales and purchase value. Whole company, not per branch."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": _FROM,
				"to_date": _TO,
				"group_by": {"type": "string", "enum": ["none", "month"]},
				"company": _COMPANY,
			},
		},
	},
	{
		"name": "payments_summary",
		"description": (
			"Money received and paid through Payment Entries for a date range, per company, broken down "
			"by account (cash, bank, each UPI), mode, day or party, plus internal transfers."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to from_date."},
				"group_by": {"type": "string", "enum": ["account", "mode", "day", "party"]},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": _LIMIT,
			},
		},
	},
]


INSTRUCTIONS = """You are the business assistant for Sundaram and Sons Private Ltd (SSPL), a wholesale business, answering staff questions from live ERPNext data.
- Use the tools for every figure; never invent numbers, names or document ids. Prefer the specific tools (sales, purchases, receivables, payables, customer activity, stock and item movement, account ledgers, cash and bank, profit and loss, GST, payments). For anything else (orders, quotations, delivery notes, bank charges, journal entries, employees, assets, any other record) use describe_doctype to find the doctype and its fields, then query_records. Never tell the user you can't access something before trying these.
- You are read-only. If asked to create or change anything, say so and point to the screen in the app where it is done.
- Amounts are INR (₹) with Indian grouping (₹1,25,000). Keep answers short; use markdown tables for lists.
- State the date range, company and cost center you used (each tool result says which it applied). "Today" means the date given below.
- The user picks a company and cost center on the chat page (named below); the tools use them when you omit company / cost_center. Answer for that selection only: omit company / cost_center in every call. Pass another company or branch only when the user names it, and "all" only when they ask for all / both companies or every branch. A vague question ("total sales", "upi receipts") is about the selection, not every company.
- Data is per company. An invoice ending in "/" (RTN07075/) is the billing system's mirror of RTN07075 in the other company, so company totals overlap by design: when the user asks for several companies, report each separately and never add them together unless asked.
- Returns (credit notes) are negative. Pending drafts are sales still waiting at the cashier; mention them separately from submitted sales.
- Only if a tool itself says the user lacks permission, tell them they don't have access to that data.
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
			"Selected on the chat page: company: "
			+ (_scope["company"] or "all companies")
			+ "; cost center: "
			+ (_scope["cost_center"] or "all cost centers (every branch)")
			+ ".",
			extra,
		)
		if p
	)


TOOLS += [
	{
		"name": "describe_doctype",
		"description": (
			"Find ERPNext doctypes and their fields, for questions the other tools don't cover. With search "
			"(e.g. 'order', 'journal', 'employee') lists matching doctypes; with doctype lists its fields "
			"(fieldname, label, type, linked doctype) and its child tables. Call before query_records."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"search": {"type": "string", "description": "Words in the doctype name."},
				"doctype": {"type": "string", "description": "Exact doctype name, e.g. 'Sales Order'."},
			},
		},
	},
	{
		"name": "query_records",
		"description": (
			"Read any ERPNext records: a list of rows, or totals with aggregates and group_by. Like the "
			"other tools it applies the chat page's company / cost center when the doctype has those "
			"fields and no filter names them. docstatus 1 = submitted, 0 = draft, 2 = cancelled; filter "
			"docstatus 1 for real totals. "
			"Child tables (e.g. Sales Invoice Item) filter on parent = the document name."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "Exact doctype name."},
				"fields": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Fieldnames to return. Defaults to name plus the list-view fields.",
				},
				"filters": {
					"type": "array",
					"items": {"type": "array"},
					"description": (
						f"[[fieldname, operator, value], ...]. Operators: {', '.join(sorted(QUERY_OPERATORS))}. "
						'e.g. [["posting_date", "between", ["2026-10-01", "2026-10-31"]], ["docstatus", "=", 1]]'
					),
				},
				"aggregates": {
					"type": "array",
					"items": {
						"type": "object",
						"properties": {
							"fn": {"type": "string", "enum": list(QUERY_AGGREGATES)},
							"field": {"type": "string"},
						},
						"required": ["fn"],
					},
					"description": "Totals, returned as <fn>_<field>, e.g. sum_grand_total, count_name.",
				},
				"group_by": {"type": "string", "description": "Fieldname to group the aggregates by."},
				"order_by": {
					"type": "string",
					"description": "Fieldname or aggregate name, optionally followed by asc / desc.",
				},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": _LIMIT,
			},
			"required": ["doctype"],
		},
	},
]


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
			"bar for comparing customers, items, warehouses or companies, pie for shares of one total "
			"(the 8 biggest slices plus Others)."
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


# ── sales / purchases ───────────────────────────────────────────────────────

# Sales and purchase summaries share one shape; only these keys differ.
INVOICES = {
	"Sales Invoice": {"party": "customer", "total": "sales", "net": "net_sales"},
	"Purchase Invoice": {"party": "supplier", "total": "purchases", "net": "net_purchases"},
}


def sales_summary(from_date=None, to_date=None, company=None, cost_center=None, group_by="none", limit=10):
	return _invoice_summary("Sales Invoice", from_date, to_date, company, cost_center, group_by, limit)


def purchase_summary(from_date=None, to_date=None, company=None, cost_center=None, group_by="none", limit=10):
	return _invoice_summary("Purchase Invoice", from_date, to_date, company, cost_center, group_by, limit)


def _invoice_summary(doctype, from_date, to_date, company, cost_center, group_by, limit):
	cfg = INVOICES[doctype]
	from_date = getdate(from_date or nowdate())
	to_date = getdate(to_date or from_date)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	options = ("none", cfg["party"], "item", "day", "month", "series")
	if group_by not in (None, *options):
		raise ValueError(f"group_by must be one of {', '.join(options)}; got {group_by!r}")
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	filters = {"posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center

	submitted = _get_list(
		doctype,
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
	drafts = _get_list(
		doctype,
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
		c = companies.setdefault(row.company, _empty_invoices(cfg["total"]))
		key = "returns" if row.is_return else cfg["total"]
		c[key] = {
			"invoices": row.invoices,
			"net_total": flt(row.net_total, 2),
			"grand_total": flt(row.grand_total, 2),
		}
	for row in drafts:
		companies.setdefault(row.company, _empty_invoices(cfg["total"]))["pending_drafts"] = {
			"invoices": row.invoices,
			"grand_total": flt(row.grand_total, 2),
		}
	for c in companies.values():
		c[cfg["net"]] = flt(c[cfg["total"]]["grand_total"] + c["returns"]["grand_total"], 2)

	if group_by and group_by != "none":
		for name, c in companies.items():
			c[f"by_{group_by}"] = _breakdown(doctype, group_by, {**filters, "company": name}, limit)

	return {
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(company, cost_center),
		"amounts": "INR, grand_total includes tax, net_total excludes it",
		"companies": companies,
	}


def _empty_invoices(total_key):
	zero = {"invoices": 0, "net_total": 0.0, "grand_total": 0.0}
	return {
		total_key: dict(zero),
		"returns": dict(zero),
		"pending_drafts": {"invoices": 0, "grand_total": 0.0},
	}


def _breakdown(doctype, group_by, filters, limit):
	"""Top rows of submitted invoices (returns netted in) for one company."""
	if group_by == "month":
		# Fold the daily rows: every day is needed, whatever the row limit.
		months = {}
		for day in _breakdown(doctype, "day", filters, EXPORT_ROWS):
			m = months.setdefault(
				str(day.posting_date)[:7],
				{"month": str(day.posting_date)[:7], "invoices": 0, "grand_total": 0.0},
			)
			m["invoices"] += day.invoices
			m["grand_total"] = flt(m["grand_total"] + flt(day.grand_total), 2)
		return list(months.values())
	if group_by == "item":
		return _item_breakdown(doctype, filters, limit)

	keys = {"day": ["posting_date"], "series": ["naming_series"]}.get(group_by) or [
		group_by,
		f"{group_by}_name",
	]
	rows = _get_list(
		doctype,
		filters={**filters, "docstatus": 1},
		fields=[*keys, {"COUNT": "*", "as": "invoices"}, {"SUM": "base_grand_total", "as": "grand_total"}],
		group_by=", ".join(keys),
		order_by="posting_date asc" if group_by == "day" else "grand_total desc",
		limit=limit,
	)
	if group_by in ("customer", "supplier"):
		for r in rows:
			_drop_same_name(r, group_by)
	return rows


def _item_breakdown(doctype, filters, limit):
	"""Top items of submitted invoices, filtered on the parent invoice. frappe.get_list joins the
	parent only while applying permissions, so with Full Read Access (ignore_permissions) its
	filters would name a table missing from the query (1054 Unknown column); join it here."""
	if not _full_read():
		parent_filters = [[doctype, k, *(v if isinstance(v, list) else ["=", v])] for k, v in filters.items()]
		parent_filters.append([doctype, "docstatus", "=", 1])
		return _get_list(
			f"{doctype} Item",
			parent_doctype=doctype,
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

	from frappe.query_builder import Order
	from frappe.query_builder.functions import Sum

	inv, item = frappe.qb.DocType(doctype), frappe.qb.DocType(f"{doctype} Item")
	net_amount = Sum(item.base_net_amount)
	query = (
		frappe.qb.from_(item)
		.join(inv)
		.on(inv.name == item.parent)
		.select(
			item.item_code,
			item.item_name,
			item.stock_uom,
			Sum(item.stock_qty).as_("qty"),
			net_amount.as_("net_amount"),
		)
		.where((item.parenttype == doctype) & (inv.docstatus == 1))
		.groupby(item.item_code, item.item_name, item.stock_uom)
		.orderby(net_amount, order=Order.desc)
	)
	for field, value in filters.items():
		op, val = value if isinstance(value, list) else ["=", value]
		if op == "between":
			query = query.where(inv[field][val[0] : val[1]])
		elif op == "=":
			query = query.where(inv[field] == val)
		elif op == "in":
			query = query.where(inv[field].isin(val))
		else:
			raise ValueError(f"Unsupported invoice filter {field} {op}")
	if limit:
		query = query.limit(limit)
	return query.run(as_dict=True)


def top_items(from_date=None, to_date=None, company=None, cost_center=None, share=80, limit=None):
	"""Pareto of item-wise sales: the top items that together reach `share`% of net sales."""
	today = getdate(nowdate())
	from_date = getdate(from_date or get_first_day(today))
	to_date = getdate(to_date or today)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	share = flt(share) or 80
	if not 0 < share <= 100:
		raise ValueError("share is a percent between 1 and 100")
	limit = _limit(limit or _row_cap["max"])
	company, cost_center = _scoped(company, cost_center)
	filters = {"posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center

	companies = {}
	for name in _get_list("Sales Invoice", filters={**filters, "docstatus": 1}, pluck="company", distinct=True):
		# Every item sold is needed to rank them; items netting to zero or below (returned) are left out.
		rows = _item_breakdown("Sales Invoice", {**filters, "company": name}, 0)
		rows = [r for r in rows if flt(r.net_amount) > 0]
		total = sum(flt(r.net_amount) for r in rows)
		if not total:
			continue
		top, running = [], 0.0
		for r in rows:
			running += flt(r.net_amount)
			top.append(
				{
					"rank": len(top) + 1,
					"item_code": r.item_code,
					"item_name": r.item_name,
					"uom": r.stock_uom,
					"qty": flt(r.qty, 3),
					"net_amount": flt(r.net_amount, 2),
					"share_pct": flt(flt(r.net_amount) * 100 / total, 2),
					"cumulative_pct": flt(running * 100 / total, 2),
				}
			)
			if running * 100 / total >= share:
				break
		companies[name] = {
			"items_sold": len(rows),
			"top_items": len(top),
			"top_items_pct_of_items": flt(len(top) * 100 / len(rows), 1),
			"top_items_net_sales": flt(running, 2),
			"net_sales": flt(total, 2),
			"items": top[:limit],
			"more_rows": len(top) > limit,
		}

	return {
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(company, cost_center),
		"share_target_pct": share,
		"amounts": "INR, net of tax, returns netted in",
		"companies": companies,
	}


# ── receivables / payables ──────────────────────────────────────────────────

# sign turns the GL's debit - credit into "owed" for that side: customers owe us, we owe suppliers.
PARTIES = {
	"Customer": {
		"invoice": "Sales Invoice",
		"key": "customer",
		"sign": 1,
		"total": "receivable",
		"count": "customers_owing",
		"note": "receivable = sum of positive balances; advances = customers in credit (negative)",
	},
	"Supplier": {
		"invoice": "Purchase Invoice",
		"key": "supplier",
		"sign": -1,
		"total": "payable",
		"count": "suppliers_owed",
		"note": "payable = what we owe suppliers (sum of positive balances); advances = suppliers we paid ahead (negative)",
	},
}


def customer_outstanding(customer=None, company=None, cost_center=None, limit=10):
	return _party_outstanding("Customer", customer, company, cost_center, limit)


def supplier_outstanding(supplier=None, company=None, cost_center=None, limit=10):
	return _party_outstanding("Supplier", supplier, company, cost_center, limit)


def _party_outstanding(party_type, search, company, cost_center, limit):
	cfg = PARTIES[party_type]
	key = cfg["key"]
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	if search:
		return _one_party(party_type, search, company, cost_center, limit)

	filters = {"party_type": party_type, "is_cancelled": 0}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center
	balances = _gl_balances(filters, ["party", "company"])

	companies = {}
	for row in balances:
		c = companies.setdefault(
			row["company"], {cfg["total"]: 0.0, "advances": 0.0, cfg["count"]: 0, "top": []}
		)
		balance = cfg["sign"] * row["balance"]
		if balance > 0:
			c[cfg["total"]] += balance
			c[cfg["count"]] += 1
			c["top"].append({**row, "balance": balance})
		elif balance < 0:
			c["advances"] += balance

	names = set()
	for c in companies.values():
		c[cfg["total"]] = flt(c[cfg["total"]], 2)
		c["advances"] = flt(c["advances"], 2)
		c["top"] = sorted(c["top"], key=lambda r: r["balance"], reverse=True)[:limit]
		names.update(r["party"] for r in c["top"])
	labels = _party_names(party_type, names)
	for c in companies.values():
		c["top"] = [
			_drop_same_name(
				{key: r["party"], f"{key}_name": labels.get(r["party"]), "balance": r["balance"]},
				key,
			)
			for r in c["top"]
		]

	return {
		"as_of": nowdate(),
		**_scope_note(company, cost_center),
		"note": cfg["note"],
		"companies": companies,
	}


def _one_party(party_type, search, company, cost_center, limit):
	cfg = PARTIES[party_type]
	key = cfg["key"]
	party = _pick_party(party_type, search)
	if party.get("found") is False:
		return party

	filters = {"party_type": party_type, "party": party.name, "is_cancelled": 0}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center
	balances = {r["company"]: cfg["sign"] * r["balance"] for r in _gl_balances(filters, ["company"])}

	inv_filters = {key: party.name, "docstatus": 1, "outstanding_amount": ["!=", 0]}
	if company:
		inv_filters["company"] = company
	if cost_center:
		inv_filters["cost_center"] = cost_center
	invoices = _get_list(
		cfg["invoice"],
		filters=inv_filters,
		fields=[
			"name",
			*(["bill_no"] if party_type == "Supplier" else []),
			"company",
			"posting_date",
			"due_date",
			"grand_total",
			"outstanding_amount",
		],
		order_by="posting_date asc",
		limit=limit,
	)
	today = getdate()
	for inv in invoices:
		inv["days_overdue"] = max(date_diff(today, inv.due_date or inv.posting_date), 0)

	return {
		"found": True,
		key: party.name,
		f"{key}_name": party.get(f"{key}_name"),
		"mobile_no": party.mobile_no,
		"as_of": nowdate(),
		**_scope_note(company, cost_center),
		"balance_by_company": balances,
		"open_invoices": invoices,
		"open_invoices_shown": len(invoices),
	}


def _gl_balances(filters, keys):
	rows = _get_list(
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


def _pick_party(party_type, search):
	"""The one customer / supplier `search` names, or {"found": False, ...} to ask the user."""
	label = f"{PARTIES[party_type]['key']}_name"
	noun = party_type.lower()
	matches = _find_parties(party_type, search)
	if not matches:
		return {"found": False, "message": f"No {noun} matches '{search}'."}
	exact = [m for m in matches if search.lower() in (m.name.lower(), (m.get(label) or "").lower())]
	if len(matches) > 1 and len(exact) != 1:
		return {"found": False, "message": f"Several {noun}s match; ask which one.", "candidates": matches}
	return exact[0] if exact else matches[0]


def _find_parties(party_type, search):
	label = f"{PARTIES[party_type]['key']}_name"
	like = f"%{search}%"
	return _get_list(
		party_type,
		or_filters={"name": ["like", like], label: ["like", like], "mobile_no": ["like", like]},
		fields=["name", label, "mobile_no"],
		limit=10,
	)


def _party_names(party_type, names):
	if not names:
		return {}
	label = f"{PARTIES[party_type]['key']}_name"
	rows = _get_list(party_type, filters={"name": ["in", list(names)]}, fields=["name", label], limit=0)
	return {r.name: r[label] for r in rows}


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
	vouchers = _get_list(
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
	matches = _get_list(
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
		accounts = _get_list(
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
			rows = _get_list(
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
	rows = _get_list(
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


# ── cash and bank ───────────────────────────────────────────────────────────

# Groups holding money accounts that ERPNext doesn't type as Cash / Bank (UPI wallets, card).
MONEY_GROUP = re.compile(r"\b(UPI|CARD|WALLET|PAYTM)\b", re.IGNORECASE)


def cash_bank_position(as_of=None, account=None, company=None):
	as_of = getdate(as_of or nowdate())
	company, _cost_center = _scoped(company, None)
	accounts = _money_accounts(company)
	if account:
		needle = account.casefold()
		accounts = {a: g for a, g in accounts.items() if needle in a.casefold() or needle in g.casefold()}
		if not accounts:
			return {"found": False, "message": f"No cash, bank or UPI account matches '{account}'."}
	balances = _gl_balances(
		{"account": ["in", list(accounts) or [""]], "is_cancelled": 0, "posting_date": ["<=", as_of]},
		["company", "account"],
	)
	companies = {}
	for r in balances:
		c = companies.setdefault(r["company"], {"total": 0.0, "by_group": {}, "accounts": []})
		group = accounts[r["account"]]
		c["total"] += r["balance"]
		c["by_group"][group] = c["by_group"].get(group, 0.0) + r["balance"]
		c["accounts"].append({"account": r["account"], "group": group, "balance": r["balance"]})
	for c in companies.values():
		c["total"] = flt(c["total"], 2)
		c["by_group"] = [{"group": g, "balance": flt(b, 2)} for g, b in c["by_group"].items()]
		c["accounts"].sort(key=lambda r: (r["group"], -r["balance"]))
	return {
		"as_of": as_of,
		**_scope_note(company, None),
		"note": "balance as per the ledger (Dr positive). Cash, bank and UPI accounts are per branch by name, so the cost center filter does not apply; accounts with a zero balance are left out.",
		"companies": companies,
	}


def _money_accounts(company):
	"""{leaf account: its group's name} for cash, bank, coin and UPI accounts.

	Typed Cash / Bank asset accounts, plus every leaf under the groups that hold them (Cash In
	Hand, Coins, Bank Accounts) or that are named like a wallet (UPI). Broad groups directly
	under the root (Current Assets) are skipped so debtors and stock never come in."""
	rows = _get_list(
		"Account",
		filters={"company": company} if company else {},
		fields=[
			"name",
			"account_name",
			"parent_account",
			"account_type",
			"root_type",
			"is_group",
			"lft",
			"rgt",
		],
		limit=0,
	)
	by_name = {r.name: r for r in rows}

	def under_root(group):
		parent = by_name.get(group.parent_account)
		return not parent or not parent.parent_account

	holders = set()
	for r in rows:
		if r.is_group:
			if r.root_type == "Asset" and MONEY_GROUP.search(r.account_name or ""):
				holders.add(r.name)
		elif r.account_type in ("Cash", "Bank") and r.root_type == "Asset":
			parent = by_name.get(r.parent_account)
			if parent and not under_root(parent):
				holders.add(parent.name)
	ranges = [(by_name[h].lft, by_name[h].rgt) for h in holders]

	out = {}
	for r in rows:
		if r.is_group or r.root_type != "Asset":
			continue
		typed = r.account_type in ("Cash", "Bank")
		if typed or any(lft < r.lft and r.rgt < rgt for lft, rgt in ranges):
			parent = by_name.get(r.parent_account)
			out[r.name] = ((parent.account_name if parent else "") or "").strip()
	return out


# ── profit and loss ─────────────────────────────────────────────────────────


def profit_loss(from_date=None, to_date=None, company=None, cost_center=None, limit=10):
	from_date = getdate(from_date or get_first_day(nowdate()))
	to_date = getdate(to_date or nowdate())
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	accounts = _get_list(
		"Account",
		filters={"root_type": ["in", ["Income", "Expense"]], **({"company": company} if company else {})},
		fields=["name", "account_name", "parent_account", "root_type", "is_group"],
		limit=0,
	)
	by_name = {a.name: a for a in accounts}

	def head(name):
		"""The account's group just below the root: Direct / Indirect Income / Expenses."""
		a = by_name[name]
		while a.parent_account in by_name and by_name[a.parent_account].parent_account:
			a = by_name[a.parent_account]
		return a.account_name

	filters = {
		"account": ["in", [a.name for a in accounts if not a.is_group] or [""]],
		"is_cancelled": 0,
		"posting_date": ["between", [from_date, to_date]],
		# Year-end closing moves P&L to equity; it would zero the period out.
		"voucher_type": ["!=", "Period Closing Voucher"],
	}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center
	rows = _get_list(
		"GL Entry",
		filters=filters,
		fields=["company", "account", {"SUM": "debit", "as": "debit"}, {"SUM": "credit", "as": "credit"}],
		group_by="company, account",
		limit=0,
	)

	companies = {}
	for r in rows:
		acc = by_name[r.account]
		income = acc.root_type == "Income"
		amount = flt(flt(r.credit) - flt(r.debit) if income else flt(r.debit) - flt(r.credit), 2)
		if not amount:
			continue
		c = companies.setdefault(r.company, {"income": 0.0, "expense": 0.0, "by_group": {}, "accounts": []})
		c["income" if income else "expense"] += amount
		group = head(r.account)
		g = c["by_group"].setdefault(group, {"group": group, "type": acc.root_type, "amount": 0.0})
		g["amount"] = flt(g["amount"] + amount, 2)
		c["accounts"].append({"account": r.account, "type": acc.root_type, "amount": amount})
	for c in companies.values():
		c["income"] = flt(c["income"], 2)
		c["expense"] = flt(c["expense"], 2)
		c["net_profit"] = flt(c["income"] - c["expense"], 2)
		c["by_group"] = list(c["by_group"].values())
		c["top_accounts"] = sorted(c.pop("accounts"), key=lambda a: a["amount"], reverse=True)[:limit]
	return {
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(company, cost_center),
		"note": "from the General Ledger: income = credit - debit, expense = debit - credit; cost of goods sold is the stock expense posted with each sale",
		"companies": companies,
	}


# ── GST ─────────────────────────────────────────────────────────────────────

# GST Settings → GST Accounts: which rows are tax collected and which are tax paid.
GST_KINDS = {
	"Output": "output",
	"Input": "input",
	"Sales Reverse Charge": "rcm_output",
	"Purchase Reverse Charge": "rcm_input",
}


def gst_summary(from_date=None, to_date=None, company=None, group_by="none"):
	from_date = getdate(from_date or get_first_day(nowdate()))
	to_date = getdate(to_date or nowdate())
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	if group_by not in (None, "none", "month"):
		raise ValueError(f"group_by must be none or month; got {group_by!r}")
	# GST is filed per company (GSTIN), and tax lines don't carry the branch cost center.
	company, _cost_center = _scoped(company, None)
	accounts = _gst_accounts(company)
	if not accounts:
		return {"found": False, "message": "No GST accounts are set in GST Settings for this company."}

	filters = {
		"account": ["in", list(accounts)],
		"is_cancelled": 0,
		"posting_date": ["between", [from_date, to_date]],
	}
	if company:
		filters["company"] = company
	rows = _get_list(
		"GL Entry",
		filters=filters,
		fields=[
			"company",
			"account",
			"posting_date",
			{"SUM": "debit", "as": "debit"},
			{"SUM": "credit", "as": "credit"},
		],
		group_by="company, account, posting_date",
		limit=0,
	)

	companies = {}
	for r in rows:
		kind, tax = accounts[r.account]
		# Tax collected sits on the credit side, tax paid (input credit) on the debit side.
		amount = (
			flt(r.credit) - flt(r.debit) if kind in ("output", "rcm_output") else flt(r.debit) - flt(r.credit)
		)
		c = companies.setdefault(r.company, _empty_gst())
		c[kind] += amount
		if kind in ("output", "input"):
			by_tax = c[f"{kind}_by_tax"]
			by_tax[tax] = by_tax.get(tax, 0.0) + amount
		if group_by == "month":
			month = str(r.posting_date)[:7]
			m = c["by_month"].setdefault(month, {"month": month, "output": 0.0, "input": 0.0})
			if kind in ("output", "input"):
				m[kind] += amount

	for name, c in companies.items():
		for kind in GST_KINDS.values():
			c[kind] = flt(c[kind], 2)
		for kind in ("output", "input"):
			c[f"{kind}_by_tax"] = {t: flt(v, 2) for t, v in c[f"{kind}_by_tax"].items()}
		c["net_payable"] = flt(c["output"] - c["input"], 2)
		if group_by == "month":
			c["by_month"] = [
				{
					**m,
					"output": flt(m["output"], 2),
					"input": flt(m["input"], 2),
					"net": flt(m["output"] - m["input"], 2),
				}
				for m in sorted(c["by_month"].values(), key=lambda m: m["month"])
			]
		else:
			c.pop("by_month")
		c.update(_taxable_values(name, from_date, to_date))
	return {
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(company, None),
		"note": "output = GST collected, input = GST paid (input credit), net_payable = output - input before reverse charge (rcm_* shown apart). From the ledger: check GSTR-1 / GSTR-3B before filing.",
		"companies": companies,
	}


def _empty_gst():
	return {
		**dict.fromkeys(GST_KINDS.values(), 0.0),
		"output_by_tax": {},
		"input_by_tax": {},
		"by_month": {},
	}


def _gst_accounts(company):
	"""{account: (kind, "CGST" | "SGST" | ...)} from GST Settings (configuration, not business data)."""
	meta = frappe.get_meta("GST Account")
	fields = [f.fieldname for f in meta.fields if f.fieldname.endswith("_account")]
	rows = frappe.get_all(
		"GST Account",
		filters={"parent": "GST Settings", **({"company": company} if company else {})},
		fields=["account_type", *fields],
	)
	out = {}
	for r in rows:
		kind = GST_KINDS.get(r.account_type)
		for f in fields:
			if kind and r[f]:
				out[r[f]] = (kind, f.removesuffix("_account").replace("_", " ").upper())
	return out


def _taxable_values(company, from_date, to_date):
	"""Net (pre-tax) value of submitted sales and purchases, returns netted in."""
	out = {}
	for doctype, key in (
		("Sales Invoice", "sales_taxable_value"),
		("Purchase Invoice", "purchase_taxable_value"),
	):
		filters = {"company": company, "docstatus": 1, "posting_date": ["between", [from_date, to_date]]}
		row = _get_list(doctype, filters=filters, fields=[{"SUM": "base_net_total", "as": "total"}], limit=1)
		out[key] = flt(row[0].total if row else 0, 2)
	return out


# ── payments ────────────────────────────────────────────────────────────────

PAYMENT_GROUPS = ("account", "mode", "day", "party")


def payments_summary(
	from_date=None, to_date=None, company=None, cost_center=None, group_by="account", limit=10
):
	from_date = getdate(from_date or nowdate())
	to_date = getdate(to_date or from_date)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	group_by = group_by or "account"
	if group_by not in PAYMENT_GROUPS:
		raise ValueError(f"group_by must be one of {', '.join(PAYMENT_GROUPS)}; got {group_by!r}")
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	filters = {"docstatus": 1, "posting_date": ["between", [from_date, to_date]]}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center

	companies = {}
	# UPI, card and Paytm all use mode "Bank": the account they land in is what tells them apart.
	for payment_type, side, account, amount in (
		("Receive", "received", "paid_to", "base_received_amount"),
		("Pay", "paid", "paid_from", "base_paid_amount"),
	):
		keys = {
			"account": [account],
			"mode": ["mode_of_payment"],
			"day": ["posting_date"],
			"party": ["party_type", "party", "party_name"],
		}[group_by]
		rows = _get_list(
			"Payment Entry",
			filters={**filters, "payment_type": payment_type},
			fields=[
				"company",
				*keys,
				{"COUNT": "*", "as": "entries"},
				{"SUM": amount, "as": "amount"},
			],
			group_by=", ".join(["company", *keys]),
			limit=0,
		)
		for r in rows:
			c = companies.setdefault(r.pop("company"), _empty_payments(group_by))
			s = c[side]
			s["total"] = flt(s["total"] + flt(r.amount), 2)
			s["entries"] += r.entries
			r["amount"] = flt(r.amount, 2)
			if group_by == "account":
				r["account"] = r.pop(account)
			if group_by == "party" and (r.get("party_name") or "") == (r.get("party") or ""):
				r.pop("party_name", None)
			s[f"by_{group_by}"].append(r)

	transfers = _get_list(
		"Payment Entry",
		filters={**filters, "payment_type": "Internal Transfer"},
		fields=["company", {"COUNT": "*", "as": "entries"}, {"SUM": "base_paid_amount", "as": "amount"}],
		group_by="company",
		limit=0,
	)
	for r in transfers:
		companies.setdefault(r.company, _empty_payments(group_by))["internal_transfers"] = {
			"entries": r.entries,
			"total": flt(r.amount, 2),
		}

	for c in companies.values():
		c["net"] = flt(c["received"]["total"] - c["paid"]["total"], 2)
		for side in ("received", "paid"):
			rows = c[side].pop(f"by_{group_by}")
			if group_by == "day":
				rows = sorted(rows, key=lambda r: r["posting_date"])[-limit:]
			else:
				rows = sorted(rows, key=lambda r: r["amount"], reverse=True)[:limit]
			c[side][f"by_{group_by}"] = rows
	return {
		"from_date": from_date,
		"to_date": to_date,
		**_scope_note(company, cost_center),
		"note": "Payment Entries only (receipts, payments, internal transfers between own accounts); journal entries are not included, use account_ledger for an account's full movement.",
		"companies": companies,
	}


def _empty_payments(group_by):
	return {
		"received": {"total": 0.0, "entries": 0, f"by_{group_by}": []},
		"paid": {"total": 0.0, "entries": 0, f"by_{group_by}": []},
		"internal_transfers": {"entries": 0, "total": 0.0},
	}


# ── stock ───────────────────────────────────────────────────────────────────


def item_stock(item=None, warehouse=None, company=None, limit=10):
	limit = _limit(limit)
	company, _cost_center = _scoped(company, None)
	show_value = _full_read() or bool(VALUATION_ROLES & set(frappe.get_roles()))
	value_fields = ["valuation_rate", "stock_value"] if show_value else []
	# Each company keeps its own warehouses (mirrored billing), so totals are per company.
	company_of, warehouses = _warehouses(company, warehouse)
	bin_filters = {"warehouse": ["in", warehouses]} if warehouses is not None else {}

	if not item:
		fields = [
			"warehouse",
			{"COUNT": "*", "as": "items_in_stock"},
			{"SUM": "actual_qty", "as": "total_qty"},
		]
		if show_value:
			fields.append({"SUM": "stock_value", "as": "stock_value"})
		summary = _get_list(
			"Bin",
			filters={**bin_filters, "actual_qty": [">", 0]},
			fields=fields,
			group_by="warehouse",
			limit=0,
		)
		negative = _get_list(
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
	bins = _get_list(
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
	barcode_hits = _get_list(
		"Item Barcode", parent_doctype="Item", filters={"barcode": search}, pluck="parent", limit=5
	)
	like = f"%{search}%"
	return _get_list(
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


# ── item movement ───────────────────────────────────────────────────────────

MOVEMENT_VIEWS = ("movement", "fast", "not_sold")
# How far back not_sold looks for an item's last sale.
LAST_SALE_LOOKBACK = 730


def item_movement(
	item=None, from_date=None, to_date=None, warehouse=None, company=None, view=None, days=90, limit=10
):
	view = view or ("movement" if item else "fast")
	if view not in MOVEMENT_VIEWS:
		raise ValueError(f"view must be one of {', '.join(MOVEMENT_VIEWS)}; got {view!r}")
	from_date = getdate(from_date or get_first_day(nowdate()))
	to_date = getdate(to_date or nowdate())
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	limit = _limit(limit)
	company, _cost_center = _scoped(company, None)
	company_of, warehouses = _warehouses(company, warehouse)
	sle = {"is_cancelled": 0}
	if warehouses is not None:
		sle["warehouse"] = ["in", warehouses]
	base = {**_scope_note(company, None), "warehouse_filter": warehouse or "all warehouses"}

	if view == "movement":
		if not item:
			raise ValueError("item is required for view 'movement'")
		found = _pick_item(item)
		if found.get("found") is False:
			return found
		return {
			**found,
			"from_date": from_date,
			"to_date": to_date,
			**base,
			**_movement({**sle, "item_code": found["item_code"]}, from_date, to_date, company_of),
		}

	if view == "fast":
		# Per company: mirrored invoices sell the same stock in both companies.
		rows = _get_list(
			"Stock Ledger Entry",
			filters={
				**sle,
				"voucher_type": "Sales Invoice",
				"posting_date": ["between", [from_date, to_date]],
			},
			fields=["company", "item_code", {"SUM": "actual_qty", "as": "qty"}],
			group_by="company, item_code",
			limit=0,
		)
		companies = {}
		for r in sorted(rows, key=lambda r: flt(r.qty)):
			top = companies.setdefault(r.company, {"items": []})["items"]
			if flt(r.qty) < 0 and len(top) < limit:
				top.append({"item_code": r.item_code, "qty_sold": flt(-r.qty, 3)})
		_add_item_names(companies)
		return {
			"from_date": from_date,
			"to_date": to_date,
			**base,
			"note": "qty sold = stock out on sales invoices, returns netted in",
			"companies": companies,
		}

	# not_sold: in stock now, no sale in the last `days` days.
	days = max(cint(days) or 90, 1)
	today = getdate(nowdate())
	cutoff = getdate(frappe.utils.add_days(today, -days))
	show_value = _full_read() or bool(VALUATION_ROLES & set(frappe.get_roles()))
	bin_filters = {"actual_qty": [">", 0]}
	if warehouses is not None:
		bin_filters["warehouse"] = ["in", warehouses]
	bins = _get_list(
		"Bin",
		filters=bin_filters,
		fields=[
			"warehouse",
			"item_code",
			{"SUM": "actual_qty", "as": "qty"},
			*([{"SUM": "stock_value", "as": "stock_value"}] if show_value else []),
		],
		group_by="warehouse, item_code",
		limit=0,
	)
	stock = {}
	for b in bins:
		s = stock.setdefault((company_of.get(b.warehouse), b.item_code), {"qty": 0.0, "stock_value": 0.0})
		s["qty"] += flt(b.qty)
		s["stock_value"] += flt(b.get("stock_value"))
	last_sale = {
		(r.company, r.item_code): getdate(r.last_sold)
		for r in _get_list(
			"Stock Ledger Entry",
			filters={
				**sle,
				"voucher_type": "Sales Invoice",
				"actual_qty": ["<", 0],
				"posting_date": [">=", frappe.utils.add_days(today, -LAST_SALE_LOOKBACK)],
			},
			fields=["company", "item_code", {"MAX": "posting_date", "as": "last_sold"}],
			group_by="company, item_code",
			limit=0,
		)
	}
	key = "stock_value" if show_value else "qty"
	companies = {}
	for (co, code), s in sorted(stock.items(), key=lambda kv: kv[1][key], reverse=True):
		last = last_sale.get((co, code))
		if last and last >= cutoff:
			continue
		c = companies.setdefault(co, {"items_not_sold": 0, "value_not_sold": 0.0, "items": []})
		c["items_not_sold"] += 1
		c["value_not_sold"] += s["stock_value"]
		if len(c["items"]) < limit:
			c["items"].append(
				{
					"item_code": code,
					"qty": flt(s["qty"], 3),
					**({"stock_value": flt(s["stock_value"], 2)} if show_value else {}),
					"last_sold": last,
					"days_since_sale": date_diff(today, last) if last else None,
				}
			)
	for c in companies.values():
		if show_value:
			c["value_not_sold"] = flt(c["value_not_sold"], 2)
		else:
			c.pop("value_not_sold")
	_add_item_names(companies)
	return {
		"as_of": today,
		**base,
		"days": days,
		"note": f"items in stock with no sale in the last {days} days; last_sold empty = no sale in {LAST_SALE_LOOKBACK} days",
		"valuation_shown": show_value,
		"companies": companies,
	}


def _add_item_names(companies):
	"""Put item_name / uom right after item_code in every company's item rows."""
	names = _item_names(list({i["item_code"] for c in companies.values() for i in c["items"]}))
	for c in companies.values():
		c["items"] = [{"item_code": i["item_code"], **names.get(i["item_code"], {}), **i} for i in c["items"]]


def _movement(filters, from_date, to_date, company_of):
	"""Opening, in, out and closing qty per warehouse, and the in / out per voucher type."""
	opening = _get_list(
		"Stock Ledger Entry",
		filters={**filters, "posting_date": ["<", from_date]},
		fields=["warehouse", {"SUM": "actual_qty", "as": "qty"}],
		group_by="warehouse",
		limit=0,
	)
	period = {**filters, "posting_date": ["between", [from_date, to_date]]}
	moves = {}
	for side, sign in (("in_qty", [">", 0]), ("out_qty", ["<", 0])):
		for r in _get_list(
			"Stock Ledger Entry",
			filters={**period, "actual_qty": sign},
			fields=["warehouse", "voucher_type", {"SUM": "actual_qty", "as": "qty"}],
			group_by="warehouse, voucher_type",
			limit=0,
		):
			m = moves.setdefault(
				(r.warehouse, r.voucher_type),
				{"warehouse": r.warehouse, "voucher_type": r.voucher_type, "in_qty": 0.0, "out_qty": 0.0},
			)
			m[side] = flt(abs(flt(r.qty)), 3)

	warehouses = {}
	for r in opening:
		warehouses[r.warehouse] = {"opening": flt(r.qty, 3), "in_qty": 0.0, "out_qty": 0.0}
	for m in moves.values():
		w = warehouses.setdefault(m["warehouse"], {"opening": 0.0, "in_qty": 0.0, "out_qty": 0.0})
		w["in_qty"] = flt(w["in_qty"] + m["in_qty"], 3)
		w["out_qty"] = flt(w["out_qty"] + m["out_qty"], 3)
	rows = []
	for name, w in sorted(warehouses.items()):
		closing = flt(w["opening"] + w["in_qty"] - w["out_qty"], 3)
		if w["opening"] or w["in_qty"] or w["out_qty"] or closing:
			rows.append({"warehouse": name, "company": company_of.get(name), **w, "closing": closing})
	return {
		"note": "qty in stock UOM; in/out per voucher type in `movements`",
		"warehouses": rows,
		"movements": sorted(moves.values(), key=lambda m: (m["warehouse"], m["voucher_type"])),
	}


def _pick_item(search):
	barcode_hits = _get_list(
		"Item Barcode", parent_doctype="Item", filters={"barcode": search}, pluck="parent", limit=5
	)
	# An exact code, barcode or name wins over the fuzzy matches (item "82" vs "Clay Lamp 182").
	exact = _get_list(
		"Item",
		or_filters={"name": ["in", [search, *barcode_hits]], "item_name": search},
		fields=["name", "item_name", "stock_uom"],
		limit=2,
	)
	items = exact if len(exact) == 1 else _find_items(search, 10)
	if not items:
		return {"found": False, "message": f"No item matches '{search}'."}
	needle = search.casefold()
	exact = [i for i in items if needle in (i.name.casefold(), (i.item_name or "").casefold())]
	if len(items) > 1 and len(exact) != 1:
		return {
			"found": False,
			"message": "Several items match; ask which one.",
			"candidates": [{"item_code": i.name, "item_name": i.item_name} for i in items],
		}
	i = exact[0] if exact else items[0]
	return {"found": True, "item_code": i.name, "item_name": i.item_name, "uom": i.stock_uom}


def _item_names(codes):
	if not codes:
		return {}
	rows = _get_list(
		"Item", filters={"name": ["in", codes]}, fields=["name", "item_name", "stock_uom"], limit=0
	)
	return {r.name: {"item_name": r.item_name, "uom": r.stock_uom} for r in rows}


def _warehouses(company, warehouse):
	"""({warehouse: company}, the warehouses to filter on or None for all)."""
	company_of = dict(_get_list("Warehouse", fields=["name", "company"], as_list=True, limit=0))
	if not company and not warehouse:
		return company_of, None
	names = [
		w
		for w, c in company_of.items()
		if (not company or c == company) and (not warehouse or warehouse.lower() in w.lower())
	]
	return company_of, names or [""]


# ── customer activity ───────────────────────────────────────────────────────


def customer_activity(customer=None, days=60, company=None, cost_center=None, limit=10):
	days = max(cint(days) or 60, 1)
	limit = _limit(limit)
	company, cost_center = _scoped(company, cost_center)
	today = getdate(nowdate())
	year_ago = frappe.utils.add_days(today, -365)
	filters = {"docstatus": 1, "is_return": 0}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center

	if customer:
		cust = _pick_party("Customer", customer)
		if cust.get("found") is False:
			return cust
		filters["customer"] = cust.name
		totals = _get_list(
			"Sales Invoice",
			filters=filters,
			fields=[
				"company",
				{"MIN": "posting_date", "as": "first_invoice"},
				{"MAX": "posting_date", "as": "last_invoice"},
				{"COUNT": "*", "as": "invoices"},
				{"SUM": "base_grand_total", "as": "total"},
			],
			group_by="company",
			limit=0,
		)
		days_rows = _get_list(
			"Sales Invoice",
			filters={**filters, "posting_date": [">=", year_ago]},
			fields=["company", "posting_date", {"SUM": "base_grand_total", "as": "total"}],
			group_by="company, posting_date",
			limit=0,
		)
		companies = {}
		for t in totals:
			gap = date_diff(t.last_invoice, t.first_invoice) / (t.invoices - 1) if t.invoices > 1 else None
			companies[t.company] = {
				"first_invoice": t.first_invoice,
				"last_invoice": t.last_invoice,
				"days_since_last": date_diff(today, t.last_invoice),
				"invoices": t.invoices,
				"total": flt(t.total, 2),
				"avg_days_between": round(gap) if gap is not None else None,
				"by_month": {},
			}
		for d in days_rows:
			months = companies[d.company]["by_month"]
			m = str(d.posting_date)[:7]
			months[m] = flt(months.get(m, 0) + flt(d.total), 2)
		for c in companies.values():
			c["by_month"] = [{"month": m, "total": t} for m, t in sorted(c["by_month"].items())]
		return {
			"found": True,
			"customer": cust.name,
			"customer_name": cust.customer_name,
			"mobile_no": cust.mobile_no,
			"as_of": today,
			**_scope_note(company, cost_center),
			"note": "submitted sales invoices, returns excluded; total is all time, by_month the last 12 months",
			"companies": companies,
		}

	rows = _get_list(
		"Sales Invoice",
		filters={**filters, "posting_date": [">=", year_ago]},
		fields=[
			"company",
			"customer",
			"customer_name",
			{"MAX": "posting_date", "as": "last_purchase"},
			{"COUNT": "*", "as": "invoices"},
			{"SUM": "base_grand_total", "as": "total"},
		],
		group_by="company, customer, customer_name",
		limit=0,
	)
	cutoff = frappe.utils.add_days(today, -days)
	companies = {}
	for r in rows:
		c = companies.setdefault(r.company, {"active_customers": 0, "lapsed_customers": 0, "lapsed": []})
		if getdate(r.last_purchase) >= getdate(cutoff):
			c["active_customers"] += 1
			continue
		c["lapsed_customers"] += 1
		c["lapsed"].append(
			_drop_same_name(
				{
					"customer": r.customer,
					"customer_name": r.customer_name,
					"last_purchase": r.last_purchase,
					"days_since": date_diff(today, r.last_purchase),
					"invoices": r.invoices,
					"total": flt(r.total, 2),
				},
				"customer",
			)
		)
	for c in companies.values():
		c["lapsed"] = sorted(c["lapsed"], key=lambda r: r["total"], reverse=True)[:limit]
	return {
		"as_of": today,
		**_scope_note(company, cost_center),
		"days": days,
		"note": f"customers who bought in the last 12 months but not in the last {days} days, biggest buyers first; invoices / total cover the last 12 months",
		"companies": companies,
	}


# ── helpers ─────────────────────────────────────────────────────────────────


def _drop_same_name(row, key):
	"""Most customers and suppliers are named by their own name: don't send it twice."""
	label = f"{key}_name"
	if (row.get(label) or "").casefold() == (row.get(key) or "").casefold():
		row.pop(label, None)
	return row


def _limit(value):
	return min(max(cint(value) or 10, 1), _row_cap["max"])


# ── any record ──────────────────────────────────────────────────────────────


def describe_doctype(search=None, doctype=None):
	if doctype:
		meta = _queryable(doctype)
		fields = [
			{
				"fieldname": f.fieldname,
				"label": f.label,
				"type": f.fieldtype,
				**(
					{"options": f.options} if f.fieldtype in ("Link", "Select", "Table") and f.options else {}
				),
			}
			for f in meta.fields
			if f.fieldname in _query_columns(meta) or f.fieldtype in ("Table", "Table MultiSelect")
		]
		return {"doctype": meta.name, "is_child_table": bool(meta.istable), "fields": fields}
	words = [w for w in re.split(r"\W+", search or "") if w]
	if not words:
		raise ValueError("Pass search words or an exact doctype.")
	names = frappe.get_all(
		"DocType",
		filters=[["name", "like", f"%{w}%"] for w in words]
		+ [["module", "in", list(QUERY_MODULES)], ["issingle", "=", 0], ["is_virtual", "=", 0]],
		pluck="name",
		order_by="istable asc, name asc",
		limit=40,
	)
	return {"doctypes": [n for n in names if not n.startswith(QUERY_DENIED_PREFIX)]}


def query_records(
	doctype,
	fields=None,
	filters=None,
	aggregates=None,
	group_by=None,
	order_by=None,
	limit=20,
	company=None,
	cost_center=None,
):
	meta = _queryable(doctype)
	columns = _query_columns(meta)

	def column(name):
		if name not in columns:
			raise ValueError(f"{meta.name} has no readable field {name!r}. Call describe_doctype.")
		return name

	select = []
	aliases = set()
	for agg in aggregates or []:
		fn = str(agg.get("fn", "")).lower() if isinstance(agg, dict) else ""
		if fn not in QUERY_AGGREGATES:
			raise ValueError(f"Aggregate fn must be one of {', '.join(QUERY_AGGREGATES)}.")
		field = column(agg.get("field") or "name")
		alias = f"{fn}_{field}"
		select.append({QUERY_AGGREGATES[fn]: field, "as": alias})
		aliases.add(alias)
	if group_by:
		select.insert(0, column(group_by))
	if not aggregates:
		select = [column(f) for f in fields or []] or _default_fields(meta, columns)

	order = None
	if order_by:
		parts = str(order_by).split()
		direction = parts[1].lower() if len(parts) > 1 else "desc"
		if len(parts) > 2 or direction not in ("asc", "desc"):
			raise ValueError("order_by is a fieldname, optionally followed by asc or desc.")
		order = f"{parts[0] if parts[0] in aliases else column(parts[0])} {direction}"
	elif not aggregates and "modified" in columns:
		order = "modified desc"

	limit = _limit(limit)
	kwargs = {}
	if meta.istable:
		parent = frappe.get_all(
			"DocField", filters={"options": meta.name, "fieldtype": "Table"}, pluck="parent", limit=1
		)
		if parent:
			kwargs["parent_doctype"] = parent[0]
	filters = _query_filters(filters, column)
	# The chat's company / cost center, as the other tools apply it, unless a filter names them.
	# Child tables are left alone: their company is on the parent document.
	named = {f[0]: f for f in filters}
	scoped = {}  # what the rows are limited to, for the scope note
	if not meta.istable:
		if "company" in named and not company:
			# A company filter replaces the chat's company; a chat branch of another company is dropped.
			f = named["company"]
			company = f[2] if f[1] == "=" else "all"
			if f[1] != "=" and not cost_center:
				cost_center = "all"
		company, cost_center = _scoped(company, cost_center)
		for field, value in (("company", company), ("cost_center", cost_center)):
			if value and field in columns:
				if field not in named:
					filters.append([field, "=", value])
				scoped[field] = value
	rows = _get_list(
		meta.name,
		fields=select,
		filters=filters,
		group_by=group_by or None,
		order_by=order,
		limit=limit,
		**kwargs,
	)
	return {
		"doctype": meta.name,
		**_scope_note(scoped.get("company"), scoped.get("cost_center")),
		"rows": rows,
		"more_rows": len(rows) == limit,
	}


def _queryable(doctype):
	if not isinstance(doctype, str) or not frappe.db.exists("DocType", doctype):
		raise ValueError(f"No doctype named {doctype!r}. Call describe_doctype with search words.")
	meta = frappe.get_meta(doctype)
	if (
		meta.module not in QUERY_MODULES
		or meta.name.startswith(QUERY_DENIED_PREFIX)
		or meta.issingle
		or meta.is_virtual
	):
		raise ValueError(f"{meta.name} is not open to AI Chat.")
	return meta


def _query_columns(meta):
	hidden = {f.fieldname for f in meta.fields if f.fieldtype in QUERY_HIDDEN_FIELDTYPES}
	return set(meta.get_valid_columns()) - hidden


def _default_fields(meta, columns):
	wanted = ["name", meta.title_field] + [f.fieldname for f in meta.fields if f.in_list_view]
	wanted += ["parent"] if meta.istable else ["docstatus"]
	return list(dict.fromkeys(f for f in wanted if f and f in columns))[:12]


def _query_filters(filters, column):
	if not filters:
		return []
	if isinstance(filters, dict):
		filters = [[k, *(v if isinstance(v, list) else ["=", v])] for k, v in filters.items()]
	out = []
	for f in filters:
		if not isinstance(f, list | tuple) or len(f) != 3:
			raise ValueError("Each filter is [fieldname, operator, value].")
		op = str(f[1]).lower()
		if op not in QUERY_OPERATORS:
			raise ValueError(f"Operator must be one of {', '.join(sorted(QUERY_OPERATORS))}.")
		out.append([column(f[0]), op, f[2]])
	return out


def _get_list(*args, **kwargs):
	"""frappe.get_list as the chat user, or every record when Full Read Access is on."""
	if _full_read():
		kwargs["ignore_permissions"] = True
	return frappe.get_list(*args, **kwargs)


def _full_read():
	return bool(frappe.get_cached_doc("SSPL Assistant Settings").get("full_read_access"))


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
	"top_items": top_items,
	"customer_outstanding": customer_outstanding,
	"item_stock": item_stock,
	"account_ledger": account_ledger,
	"purchase_summary": purchase_summary,
	"supplier_outstanding": supplier_outstanding,
	"customer_activity": customer_activity,
	"item_movement": item_movement,
	"cash_bank_position": cash_bank_position,
	"profit_loss": profit_loss,
	"gst_summary": gst_summary,
	"payments_summary": payments_summary,
	"describe_doctype": describe_doctype,
	"query_records": query_records,
}
