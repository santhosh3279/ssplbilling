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
_scope = {"company": None, "cost_center": None, "question": None, "guarded": []}
# Words in the user's question that let the AI leave the chat's company / cost center.
BROAD_WORDS = re.compile(r"\b(all|both|every|each|other|another|companies|branches)\b")
DATA_TOOLS = (
	"sales_summary",
	"top_items",
	"purchase_summary",
	"customer_outstanding",
	"supplier_outstanding",
	"customer_activity",
	"item_stock",
	"item_movement",
	"supplier_item_sales",
	"item_sales_trend",
	"reorder_suggestion",
	"purchase_mirror_check",
	"account_ledger",
	"cash_bank_position",
	"cashflow_forecast",
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
# Buckets item_sales_trend may return, per period size.
TREND_PERIODS = {"week": 53, "month": 24, "day": 62}
# z-score per service level (% of lead times that should not run out) for safety stock.
SERVICE_LEVELS = {90: 1.28, 95: 1.65, 98: 2.05, 99: 2.33}
# Lead time used when neither the question nor the Item gives one.
DEFAULT_LEAD_DAYS = 7
# Most items one item_sales_trend call reads.
MAX_TREND_ITEMS = 300
# Most parent documents a child-table query resolves by name under Full Read Access.
MAX_PARENTS = 20000
QUERY_AGGREGATES = {"sum": "SUM", "count": "COUNT", "avg": "AVG", "min": "MIN", "max": "MAX"}
# cashflow_forecast: weeks it may project ahead / look back on for the run-rate.
CASHFLOW_WEEKS = (1, 26)
CASHFLOW_HISTORY = (4, 52)
# Invoice age (days since posting) buckets for open receivables / payables.
AGE_BUCKETS = ((30, "0-30"), (60, "31-60"), (90, "61-90"), (None, "90+"))

TOOLS = [
	{
		"name": "sales_summary",
		"description": (
			"Sales totals for a date range from submitted Sales Invoices, per company: sales, returns "
			"(credit notes, negative) and net, plus the drafts still waiting at the cashier. Optionally "
			"breaks the period down by customer, item, day, month, naming series or cost center (branch) "
			"(top rows by amount). Use for 'sales today', 'sales this month', 'top customers/items', "
			"'daily sales', 'cost center wise sales'; with cost_center \"all\" for every branch."
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
					"enum": ["none", "customer", "item", "day", "month", "series", "cost_center"],
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
				"from_date": {
					"type": "string",
					"description": "YYYY-MM-DD. Defaults to the 1st of this month.",
				},
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
			"returns (negative), net and drafts. Optional breakdown by supplier, item, day, month, series or "
			"cost center (branch)."
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
					"enum": ["none", "supplier", "item", "day", "month", "series", "cost_center"],
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
		"name": "supplier_item_sales",
		"description": (
			"Items linked to one supplier (Item Supplier) with stock and average sales qty, per company, "
			"highest weekly sales first. weekly_avg = net qty sold in the last 28 days / 4; monthly_avg = "
			"net qty sold in the last `months` months (months * 30 days) / months. Returns are netted off. "
			"Use for reorder / purchase planning for a supplier."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"supplier": {"type": "string", "description": "Supplier name, code or mobile."},
				"months": {"type": "integer", "description": "Months for the monthly average (default 6)."},
				"company": _COMPANY,
				"limit": _LIMIT,
			},
			"required": ["supplier"],
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
		"name": "cashflow_forecast",
		"description": (
			"Cash flow, per company: actual money in / out of the cash, bank and UPI accounts per week "
			"(internal transfers left out), the average weekly run-rate, and a week-by-week projection of "
			"the cash + bank balance from today's balance at that run-rate, with the lowest week and the "
			"runway when cash is shrinking. Also receivables and payables (GL totals, open invoices aged "
			"0-30 / 31-60 / 61-90 / 90+ days, days of sales / purchases outstanding) and the balance left "
			"if every supplier were paid now. Use for 'cash flow', 'cash forecast', 'will we "
			"have enough money', 'runway', 'money coming in / going out'. Whole company, not per branch."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"weeks": {
					"type": "integer",
					"description": f"Weeks to project ahead ({CASHFLOW_WEEKS[0]}-{CASHFLOW_WEEKS[1]}, default 8).",
				},
				"history_weeks": {
					"type": "integer",
					"description": f"Full past weeks for the run-rate ({CASHFLOW_HISTORY[0]}-{CASHFLOW_HISTORY[1]}, default 12).",
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
	{
		"name": "purchase_mirror_check",
		"description": (
			"Purchase bill mirroring between the billing company and the Automatic Entries (AE) alternate "
			"company for a date range: bills in both (original + mirror), only in the billing company "
			"(mirror missing) and only in the AE company. Drafts included, cancelled skipped."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"from_date": _FROM,
				"to_date": _TO,
				"company": {
					"type": "string",
					"description": "Billing company. Omit to use the chat's company.",
				},
				"limit": _LIMIT,
			},
		},
	},
]


TOOLS += [
	{
		"name": "item_sales_trend",
		"description": (
			"Sales of chosen items over time: net qty sold and net amount per day, week or month, per "
			"company, with every item's qty per period; optionally the purchased qty beside it. Choose the "
			"items by item (code, name or barcode), items (several), supplier (its Item Supplier items) "
			"and / or item_group (with its sub-groups); together they narrow each other. Use for 'weekly "
			"sales of M85', 'monthly sales of Sevana items', 'sales vs purchase pattern of an item', "
			"'which of these items sold more this week', 'item sales in EOW bills' (series). Returns are "
			"netted off; qty is in stock UOM."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"item": {"type": "string", "description": "One item: code, name or barcode."},
				"items": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Several items: codes, names or barcodes.",
				},
				"supplier": {"type": "string", "description": "Supplier name, code or mobile."},
				"item_group": {"type": "string", "description": "Item group; its sub-groups are included."},
				"period": {
					"type": "string",
					"enum": list(TREND_PERIODS),
					"description": "Bucket size (default week; weeks start on Monday).",
				},
				"from_date": {
					"type": "string",
					"description": "YYYY-MM-DD; moved back to the start of its period. Defaults: 30 days, "
					"12 weeks or 6 months back.",
				},
				"to_date": {"type": "string", "description": "YYYY-MM-DD. Defaults to today."},
				"series": {
					"type": "string",
					"description": 'Sales invoice naming series, e.g. "EOW" or "EOW.#####" (sales only).',
				},
				"include_purchases": {
					"type": "boolean",
					"description": "Also the qty bought on submitted purchase invoices per period.",
				},
				"company": _COMPANY,
				"cost_center": _COST_CENTER,
				"limit": {"type": "integer", "description": f"Items to return per company (max {MAX_ROWS})."},
			},
		},
	},
]

TOOLS += [
	{
		"name": "reorder_suggestion",
		"description": (
			"What to reorder and how much, per company, from weekly sales over the last `weeks` full weeks "
			"(returns netted off), stock in the company's warehouses and qty already on order (open "
			"purchase orders). Per item: avg weekly sales, days of cover, safety stock = z x weekly std "
			"dev x sqrt(lead weeks), reorder point = avg daily sales x lead time + safety stock, and "
			"suggested order = avg daily sales x (lead time + review days) + safety stock - stock - on "
			"order. Status: order_now (stock + on order at or below the reorder point), ok, slow_mover (sold in under "
			"1 week in 4 and still in stock), overstock (cover over 3x lead + review), no_sales. Choose items like item_sales_trend. Use for 'what "
			"to reorder', 'safety stock', 'how much should I order', 'is ordering of X healthy', "
			"'lead time is 1 week, how should I order'. Company-wide: cost center is ignored."
		),
		"input_schema": {
			"type": "object",
			"properties": {
				"item": {"type": "string", "description": "One item: code, name or barcode."},
				"items": {"type": "array", "items": {"type": "string"}, "description": "Several items."},
				"supplier": {"type": "string", "description": "Supplier name, code or mobile."},
				"item_group": {"type": "string", "description": "Item group; its sub-groups are included."},
				"lead_time_days": {
					"type": "integer",
					"description": f"Days from order to stock. Defaults to the Item's lead time, else {DEFAULT_LEAD_DAYS}.",
				},
				"review_days": {
					"type": "integer",
					"description": "Days until the next order is placed (order cycle). Default 7.",
				},
				"weeks": {
					"type": "integer",
					"description": "Full weeks of sales history to use (4-52, default 12).",
				},
				"service_level": {
					"type": "integer",
					"enum": list(SERVICE_LEVELS),
					"description": "% of lead times that should not run out of stock (default 95).",
				},
				"only_to_order": {"type": "boolean", "description": "Only items with status order_now."},
				"company": _COMPANY,
				"limit": _LIMIT,
			},
		},
	},
]

INSTRUCTIONS = """You are the business assistant for Sundaram and Sons Private Ltd (SSPL), a wholesale business, answering staff questions from live ERPNext data.
- Use the tools for every figure; never invent numbers, names or document ids. Prefer the specific tools (sales, purchases, receivables, payables, customer activity, stock and item movement, item sales trends, account ledgers, cash and bank, profit and loss, GST, payments). For anything else (orders, quotations, delivery notes, bank charges, journal entries, employees, assets, any other record) use describe_doctype to find the doctype and its fields, then query_records. Never tell the user you can't access something before trying these.
- For one item's, a supplier's or an item group's sales by day, week or month (and purchases beside them) use item_sales_trend, not query_records.
- For what to reorder, how much to order, safety stock, days of cover or whether ordering is healthy use reorder_suggestion; say which lead time, review days and history it used.
- For cash flow, a cash forecast, runway or whether there will be enough money use cashflow_forecast; say it projects at the past weekly run-rate (not a schedule of dues), which history weeks it used, and show overdue receivables / payables apart.
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
			"Child tables (e.g. Sales Invoice Item) filter on parent = the document name, and may also "
			"filter on the parent document's fields, e.g. posting_date, docstatus, customer; the chat's "
			"company / cost center then apply to the parent. "
			"For stock quantities use item_stock (now) or item_movement (opening / closing on a date); "
			"never SUM actual_qty on Stock Ledger Entry for a balance: Stock Reconciliation rows have "
			"actual_qty = 0 and set the balance in qty_after_transaction (latest row per item + warehouse)."
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
	_scope["guarded"] = []
	try:
		data = fn(**args)
		if _scope["guarded"] and isinstance(data, dict):
			selection = " / ".join(filter(None, (_scope["company"], _scope["cost_center"])))
			data["scope_guard"] = (
				f"Kept to the chat's selection ({selection}): the user's question did not ask for "
				f"{', '.join(_scope['guarded'])}. Answer for the selection; they can ask for all "
				"companies or name the other company."
			)
		# Compact JSON: every byte of a tool result is billed as input on this and later turns.
		return json.dumps(data, default=str, ensure_ascii=False, separators=(",", ":")), False
	except frappe.PermissionError:
		frappe.clear_last_message()
		return "The user does not have permission to read this data in ERPNext.", True
	except (frappe.ValidationError, TypeError, ValueError) as e:
		frappe.clear_last_message()
		return f"Invalid request: {e}", True
	except frappe.db.ProgrammingError as e:
		# Bad SQL from the arguments (unknown column, syntax): let the AI fix the call.
		frappe.clear_last_message()
		return f"The database rejected the query: {e.args[-1] if e.args else e}", True


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
	options = ("none", cfg["party"], "item", "day", "month", "series", "cost_center")
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

	keys = {"day": ["posting_date"], "series": ["naming_series"], "cost_center": ["cost_center"]}.get(
		group_by
	) or [
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


def _item_breakdown(doctype, filters, limit, item_codes=None):
	"""Top items of submitted invoices, filtered on the parent invoice. frappe.get_list joins the
	parent only while applying permissions, so with Full Read Access (ignore_permissions) its
	filters would name a table missing from the query (1054 Unknown column); join it here.
	`item_codes` limits the rows to those items (uses the item_code index, so a few items read
	only their own invoice lines instead of every line in the period)."""
	if not _full_read():
		parent_filters = [[doctype, k, *(v if isinstance(v, list) else ["=", v])] for k, v in filters.items()]
		parent_filters.append([doctype, "docstatus", "=", 1])
		if item_codes is not None:
			parent_filters.append([f"{doctype} Item", "item_code", "in", list(item_codes)])
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
	if item_codes is not None:
		query = query.where(item.item_code.isin(list(item_codes)))
	for field, value in filters.items():
		op, val = value if isinstance(value, list) else ["=", value]
		if op == "between":
			query = query.where(inv[field][val[0] : val[1]])
		elif op == "=":
			query = query.where(inv[field] == val)
		elif op == "in":
			query = query.where(inv[field].isin(val))
		elif op == "like":
			query = query.where(inv[field].like(val))
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
	for name in _get_list(
		"Sales Invoice", filters={**filters, "docstatus": 1}, pluck="company", distinct=True
	):
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


def cashflow_forecast(weeks=8, history_weeks=12, company=None):
	"""Run-rate cash projection. Open invoices here carry no payment terms (due date = posting date,
	nearly all already overdue), so dues can't be scheduled by due date: the projection uses the
	actual weekly money in / out, and receivables / payables are aged by invoice date instead."""
	add = frappe.utils.add_days
	weeks = min(max(cint(weeks) or 8, CASHFLOW_WEEKS[0]), CASHFLOW_WEEKS[1])
	history_weeks = min(max(cint(history_weeks) or 12, CASHFLOW_HISTORY[0]), CASHFLOW_HISTORY[1])
	# Cash and bank accounts are per company (branches by name), so the cost center never applies.
	company, _cost_center = _scoped(company, None)
	today = getdate(nowdate())
	this_monday = getdate(_period_start(today, "week"))
	hist_from = getdate(add(this_monday, -7 * history_weeks))
	hist_to = getdate(add(this_monday, -1))
	window_end = getdate(add(today, 7 * weeks))
	company_filter = {"company": company} if company else {}

	accounts = list(_money_accounts(company)) or [""]
	money = {"account": ["in", accounts], "is_cancelled": 0}
	opening = {
		r["company"]: r["balance"]
		for r in _gl_balances({**money, "posting_date": ["<=", today]}, ["company"])
	}
	# Net per voucher on the money accounts: a transfer between cash, bank and UPI nets to 0 and
	# drops out, so money_in / money_out are only what came from or went to someone else.
	vouchers = _get_list(
		"GL Entry",
		filters={**money, "posting_date": ["between", [hist_from, today]]},
		fields=[
			"company",
			"posting_date",
			{"SUM": "debit", "as": "debit"},
			{"SUM": "credit", "as": "credit"},
		],
		group_by="company, posting_date, voucher_type, voucher_no",
		limit=0,
	)
	flows = {}
	for v in vouchers:
		net = flt(v.debit) - flt(v.credit)
		if not net:
			continue
		day = getdate(v.posting_date)
		week = "wtd" if day >= this_monday else str(_period_start(day, "week"))
		f = flows.setdefault(v.company, {}).setdefault(week, [0.0, 0.0])
		f[0 if net > 0 else 1] += abs(net)

	parties = {pt: _cashflow_party(pt, company_filter, today, window_end) for pt in PARTIES}
	sales = {
		r.company: flt(r.total)
		for r in _get_list(
			"Sales Invoice",
			filters={**company_filter, "docstatus": 1, "posting_date": ["between", [hist_from, hist_to]]},
			fields=["company", {"SUM": "base_grand_total", "as": "total"}],
			group_by="company",
			limit=0,
		)
	}
	purchases = {
		r.company: flt(r.total)
		for r in _get_list(
			"Purchase Invoice",
			filters={**company_filter, "docstatus": 1, "posting_date": ["between", [hist_from, hist_to]]},
			fields=["company", {"SUM": "base_grand_total", "as": "total"}],
			group_by="company",
			limit=0,
		)
	}

	names = set(opening) | set(flows) | set(parties["Customer"]) | set(parties["Supplier"])
	if company:
		names.add(company)
	days = history_weeks * 7
	companies = {}
	for co in sorted(names):
		balance = flt(opening.get(co), 2)
		co_flows = flows.get(co, {})
		wtd_in, wtd_out = co_flows.get("wtd", [0.0, 0.0])

		by_week, closing = [], balance - (wtd_in - wtd_out)
		for b in reversed(_trend_buckets(hist_from, hist_to, "week")):
			money_in, money_out = co_flows.get(str(b["from"]), [0.0, 0.0])
			by_week.append(
				{
					"week_from": b["from"],
					"week_ending": b["end"],
					"money_in": flt(money_in, 2),
					"money_out": flt(money_out, 2),
					"net": flt(money_in - money_out, 2),
					"closing_balance": flt(closing, 2),
				}
			)
			closing -= money_in - money_out
		by_week.reverse()
		avg_in = flt(sum(w["money_in"] for w in by_week) / history_weeks, 2)
		avg_out = flt(sum(w["money_out"] for w in by_week) / history_weeks, 2)
		avg_net = flt(avg_in - avg_out, 2)

		receivable = parties["Customer"].get(co) or _cashflow_party_empty()
		payable = parties["Supplier"].get(co) or _cashflow_party_empty()
		forecast, running = [], balance
		for i in range(1, weeks + 1):
			start, end = getdate(add(today, 7 * (i - 1) + 1)), getdate(add(today, 7 * i))
			running += avg_net
			forecast.append(
				{
					"week_from": start,
					"week_ending": end,
					"expected_in": avg_in,
					"expected_out": avg_out,
					"projected_balance": flt(running, 2),
					"receivable_falling_due": flt(receivable["_due"].get(str(end)), 2),
					"payable_falling_due": flt(payable["_due"].get(str(end)), 2),
				}
			)
		for side in (receivable, payable):
			side.pop("_due")
		lowest = min(forecast, key=lambda r: r["projected_balance"])
		daily_sales, daily_purchases = sales.get(co, 0) / days, purchases.get(co, 0) / days

		companies[co] = {
			"balance_today": balance,
			"week_to_date": {"money_in": flt(wtd_in, 2), "money_out": flt(wtd_out, 2)},
			"avg_weekly_in": avg_in,
			"avg_weekly_out": avg_out,
			"avg_weekly_net": avg_net,
			"projected_balance_end": forecast[-1]["projected_balance"],
			"lowest_week": {"week_ending": lowest["week_ending"], "balance": lowest["projected_balance"]},
			"runway_weeks": flt(balance / -avg_net, 1) if avg_net < 0 and balance > 0 else None,
			"receivable": receivable,
			"payable": payable,
			"days_sales_outstanding": flt(receivable["gl_total"] / daily_sales, 1) if daily_sales else None,
			"days_purchases_outstanding": (
				flt(payable["gl_total"] / daily_purchases, 1) if daily_purchases else None
			),
			"balance_if_payables_paid_now": flt(balance - payable["gl_total"], 2),
			"forecast": forecast,
			"by_week": by_week,
		}

	return {
		"as_of": today,
		**_scope_note(company, None),
		"history_from": hist_from,
		"history_to": hist_to,
		"note": (
			"Cash, bank and UPI accounts only; transfers between them are left out. Projection = today's "
			"balance + the average weekly net of the history weeks (the run-rate already includes cash sales "
			"and customer collections, supplier payments and expenses); it is not a schedule of dues. "
			"gl_total = what parties owe / are owed per the party ledger (same as customer_outstanding / "
			"supplier_outstanding); advances = parties in credit. Many payments are not allocated to bills, "
			"so each party's balance is matched to its newest open invoices (oldest bills taken as paid) and "
			"only that invoice_backed part is aged by invoice date; unscheduled = gl_total - invoice_backed "
			"(opening balances, journal entries); invoice_outstanding_unadjusted is the raw bill outstanding, "
			"overstated by unallocated payments. Bills have no payment terms, so *_falling_due only counts "
			"due dates ahead (usually 0). Days outstanding = gl_total / average daily invoiced value of the history. "
			"week_to_date is the current week so far, not in the averages. Whole company, not per branch."
		),
		"companies": companies,
	}


def _cashflow_party(party_type, company_filter, today, window_end):
	"""{company: {gl_total, advances, invoice_backed, unscheduled, overdue, ageing, _due: {week end: amount}}}.

	Many payments here are posted on account without being allocated to bills, so invoice
	outstanding overstates what is owed. Each party's ledger balance is the truth: it is laid on
	that party's open invoices newest first (the oldest bills taken as paid), and only that part
	is aged. gl_total / advances match customer_outstanding / supplier_outstanding."""
	cfg = PARTIES[party_type]
	key = cfg["key"]
	out, owed = {}, {}
	for r in _gl_balances(
		{**company_filter, "party_type": party_type, "is_cancelled": 0}, ["company", "party"]
	):
		side = out.setdefault(r["company"], _cashflow_party_empty())
		balance = cfg["sign"] * r["balance"]
		if balance > 0:
			side["gl_total"] += balance
			owed[(r["company"], r["party"])] = balance
		else:
			side["advances"] += balance
	invoices = _get_list(
		cfg["invoice"],
		filters={**company_filter, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["company", key, "posting_date", "due_date", "outstanding_amount"],
		order_by="posting_date desc, name desc",
		limit=0,
	)
	for inv in invoices:
		side = out.setdefault(inv.company, _cashflow_party_empty())
		side["invoice_outstanding_unadjusted"] += flt(inv.outstanding_amount)
		party = (inv.company, inv[key])
		amount = min(flt(inv.outstanding_amount), owed.get(party, 0.0))
		if amount <= 0:
			continue
		owed[party] -= amount
		side["invoice_backed"] += amount
		age = date_diff(today, inv.posting_date)
		label = next(lbl for days, lbl in AGE_BUCKETS if days is None or age <= days)
		side["ageing"][label] += amount
		due = getdate(inv.due_date or inv.posting_date)
		if due <= today:
			side["overdue"] += amount
		elif due <= window_end:
			# The forecast week (ending today + 7n) the due date falls in.
			week_end = str(getdate(frappe.utils.add_days(today, 7 * -(-date_diff(due, today) // 7))))
			side["_due"][week_end] = side["_due"].get(week_end, 0.0) + amount
	for side in out.values():
		for k in ("gl_total", "advances", "invoice_backed", "overdue", "invoice_outstanding_unadjusted"):
			side[k] = flt(side[k], 2)
		side["unscheduled"] = flt(side["gl_total"] - side["invoice_backed"], 2)
		side["ageing"] = {k: flt(v, 2) for k, v in side["ageing"].items()}
	return out


def _cashflow_party_empty():
	return {
		"gl_total": 0.0,
		"advances": 0.0,
		"invoice_backed": 0.0,
		"unscheduled": 0.0,
		"invoice_outstanding_unadjusted": 0.0,
		"overdue": 0.0,
		"ageing": {label: 0.0 for _days, label in AGE_BUCKETS},
		"_due": {},
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
	"""Opening, in, out and closing qty per warehouse, and the in / out per voucher type.

	Balances come from `qty_after_transaction`, not a sum of `actual_qty`: Stock Reconciliation
	entries set the balance with actual_qty = 0, so summing would drop every reconciled qty.
	Each entry's movement is the change in that running balance.
	"""
	rows = _get_list(
		"Stock Ledger Entry",
		filters={**filters, "posting_date": ["<=", to_date]},
		fields=["warehouse", "posting_date", "voucher_type", "qty_after_transaction"],
		order_by="posting_datetime asc, creation asc",
		limit=0,
	)
	warehouses, moves, balance = {}, {}, {}
	for r in rows:
		before = balance.get(r.warehouse, 0.0)
		after = balance[r.warehouse] = flt(r.qty_after_transaction)
		w = warehouses.setdefault(r.warehouse, {"opening": 0.0, "in_qty": 0.0, "out_qty": 0.0})
		if getdate(r.posting_date) < from_date:
			w["opening"] = after
			continue
		change = flt(after - before, 3)
		if not change:
			continue
		side = "in_qty" if change > 0 else "out_qty"
		m = moves.setdefault(
			(r.warehouse, r.voucher_type),
			{"warehouse": r.warehouse, "voucher_type": r.voucher_type, "in_qty": 0.0, "out_qty": 0.0},
		)
		m[side] = flt(m[side] + abs(change), 3)
		w[side] = flt(w[side] + abs(change), 3)

	out = []
	for name, w in sorted(warehouses.items()):
		w["opening"] = flt(w["opening"], 3)
		closing = flt(balance[name], 3)
		if w["opening"] or w["in_qty"] or w["out_qty"] or closing:
			out.append({"warehouse": name, "company": company_of.get(name), **w, "closing": closing})
	return {
		"note": "qty in stock UOM; in/out per voucher type in `movements` "
		"(a Stock Reconciliation counts as in/out by the qty it changed)",
		"warehouses": out,
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


# ── supplier item sales ─────────────────────────────────────────────────────


def supplier_item_sales(supplier=None, months=6, company=None, limit=None):
	"""A supplier's items with stock and weekly / monthly average sales, per company."""
	if not supplier:
		raise ValueError("supplier is required.")
	months = min(max(cint(months) or 6, 1), 36)
	limit = _limit(limit or _row_cap["max"])
	company, _cost_center = _scoped(company, None)
	party = _pick_party("Supplier", supplier)
	if party.get("found") is False:
		return party

	codes = {
		r.parent
		for r in _get_list(
			"Item Supplier",
			parent_doctype="Item",
			filters={"supplier": party.name, "parenttype": "Item"},
			fields=["parent"],
			limit=0,
		)
	}
	base = {
		"found": True,
		"supplier": party.name,
		"supplier_name": party.get("supplier_name"),
		"months": months,
		"as_of": nowdate(),
		**_scope_note(company, None),
		"note": f"weekly_avg = qty sold in last 28 days / 4; monthly_avg = qty sold in last {months * 30} days / {months}",
	}
	if not codes:
		return {**base, "companies": {}, "message": "No items are linked to this supplier."}

	items = {
		i.name: i
		for i in _get_list(
			"Item",
			filters={"name": ["in", list(codes)]},
			fields=["name", "item_name", "stock_uom", "disabled"],
			limit=0,
		)
	}
	company_of, warehouses = _warehouses(company, None)
	bin_filters = {"item_code": ["in", list(items)]}
	if warehouses is not None:
		bin_filters["warehouse"] = ["in", warehouses]
	stock = {}
	for b in _get_list("Bin", filters=bin_filters, fields=["item_code", "warehouse", "actual_qty"], limit=0):
		key = (company_of.get(b.warehouse), b.item_code)
		stock[key] = flt(stock.get(key, 0) + flt(b.actual_qty), 3)

	today = getdate(nowdate())
	week_from = frappe.utils.add_days(today, -28)
	month_from = frappe.utils.add_days(today, -30 * months)
	companies = [company] if company else [c.name for c in _get_list("Company", fields=["name"], limit=0)]

	out = {}
	for co in companies:
		sold = {}
		for key, from_date in (("week", week_from), ("month", month_from)):
			rows = _item_breakdown(
				"Sales Invoice",
				{"company": co, "posting_date": ["between", [str(from_date), str(today)]]},
				0,
				item_codes=items,
			)
			# Lines saved under an older item name come back as their own row; add them up.
			for r in rows:
				q = sold.setdefault(r.item_code, {})
				q[key] = q.get(key, 0) + flt(r.qty)
		rows = []
		for code, item in items.items():
			qty = sold.get(code, {})
			in_stock = stock.get((co, code), 0)
			if not qty and not in_stock and item.disabled:
				continue
			rows.append(
				{
					"item_code": code,
					"item_name": item.item_name,
					"uom": item.stock_uom,
					"stock": in_stock,
					"weekly_avg": flt(qty.get("week", 0) / 4, 2),
					"monthly_avg": flt(qty.get("month", 0) / months, 2),
				}
			)
		if not any(r["stock"] or r["weekly_avg"] or r["monthly_avg"] for r in rows):
			continue
		rows.sort(key=lambda r: (r["weekly_avg"], r["monthly_avg"], r["stock"]), reverse=True)
		out[co] = {"items_linked": len(rows), "items": rows[:limit], "more_rows": len(rows) > limit}
	return {**base, "companies": out}


# ── item sales trend ────────────────────────────────────────────────────────


def item_sales_trend(
	item=None,
	items=None,
	supplier=None,
	item_group=None,
	period="week",
	from_date=None,
	to_date=None,
	series=None,
	include_purchases=False,
	company=None,
	cost_center=None,
	limit=None,
):
	"""Chosen items' net qty / amount sold per day, week or month, per company."""
	period = period or "week"
	if period not in TREND_PERIODS:
		raise ValueError(f"period must be one of {', '.join(TREND_PERIODS)}; got {period!r}")
	limit = _limit(limit or _row_cap["max"])
	company, cost_center = _scoped(company, cost_center)
	picked = _trend_items(item, items, supplier, item_group)
	if picked.get("found") is False:
		return picked
	catalogue = picked["items"]

	to_date = getdate(to_date or nowdate())
	from_date = _period_start(
		getdate(from_date) if from_date else _trend_default_start(period, to_date), period
	)
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	buckets = _trend_buckets(from_date, to_date, period)
	if len(buckets) > TREND_PERIODS[period]:
		raise ValueError(
			f"{len(buckets)} {period}s is too many (max {TREND_PERIODS[period]}); use a shorter range "
			"or a longer period."
		)

	header = {}
	if cost_center:
		header["cost_center"] = cost_center
	sales_filters = dict(header)
	if series:
		s = str(series).strip()
		sales_filters["naming_series"] = s if "." in s else ["like", f"{s}.%"]
	companies = [company] if company else _get_list("Company", pluck="name", limit=0)

	out = {}
	for co in companies:
		sold = _trend_lines("Sales Invoice", {**sales_filters, "company": co}, buckets, catalogue)
		bought = (
			_trend_lines("Purchase Invoice", {**header, "company": co}, buckets, catalogue)
			if include_purchases
			else {}
		)
		if not sold and not bought:
			continue
		rows = []
		for code in set(sold) | set(bought):
			s_qty = sold.get(code, {}).get("qty", [0.0] * len(buckets))
			row = {
				"item_code": code,
				"item_name": catalogue[code].item_name,
				"uom": catalogue[code].stock_uom,
				"qty": flt(sum(s_qty), 3),
				"net_amount": flt(sum(sold.get(code, {}).get("amount", [])), 2),
				"avg_qty_per_period": flt(sum(s_qty) / len(buckets), 2),
				"qty_by_period": s_qty,
			}
			if include_purchases:
				b_qty = bought.get(code, {}).get("qty", [0.0] * len(buckets))
				row["purchased_qty"] = flt(sum(b_qty), 3)
				row["purchased_by_period"] = b_qty
			rows.append(row)
		rows.sort(key=lambda r: (r["net_amount"], r["qty"]), reverse=True)
		totals = []
		for i, b in enumerate(buckets):
			t = {
				"period": b["label"],
				"qty": flt(sum(v["qty"][i] for v in sold.values()), 3),
				"net_amount": flt(sum(v["amount"][i] for v in sold.values()), 2),
			}
			if include_purchases:
				t["purchased_qty"] = flt(sum(v["qty"][i] for v in bought.values()), 3)
			totals.append(t)
		out[co] = {
			"qty": flt(sum(t["qty"] for t in totals), 3),
			"net_amount": flt(sum(t["net_amount"] for t in totals), 2),
			**(
				{"purchased_qty": flt(sum(t["purchased_qty"] for t in totals), 3)}
				if include_purchases
				else {}
			),
			"items_with_sales": sum(1 for r in rows if r["qty"] or r["net_amount"]),
			"by_period": totals,
			"items": rows[:limit],
			"more_rows": len(rows) > limit,
		}

	notes = [
		"qty in stock UOM, returns netted off; net_amount excludes tax",
		"qty_by_period follows `periods`",
		f"the last {period} runs only to to_date" if buckets[-1]["to"] < buckets[-1]["end"] else "",
		"totals add qty across different UOMs" if len({i.stock_uom for i in catalogue.values()}) > 1 else "",
	]
	return {
		"found": True,
		**picked["selection"],
		"items_matched": len(catalogue),
		"from_date": from_date,
		"to_date": to_date,
		"period": period,
		"periods": [b["label"] for b in buckets],
		**_scope_note(company, cost_center),
		**({"series_filter": series} if series else {}),
		"note": "; ".join(n for n in notes if n),
		"companies": out,
	}


def _trend_items(item, items, supplier, item_group):
	"""{"found", "items": {code: Item row}, "selection"}; each given filter narrows the others."""
	terms = [*(items or []), *([item] if item else [])]
	if not (terms or supplier or item_group):
		raise ValueError("Give item, items, supplier or item_group.")
	codes, selection = None, {}
	if terms:
		found = []
		for term in terms:
			r = _pick_item(str(term).strip())
			if r.get("found") is False:
				return {**r, "message": f"{term}: {r.get('message')}"}
			found.append(r["item_code"])
		codes = set(found)
		selection["items_filter"] = found
	if supplier:
		party = _pick_party("Supplier", supplier)
		if party.get("found") is False:
			return party
		linked = set(
			_get_list(
				"Item Supplier",
				parent_doctype="Item",
				filters={"supplier": party.name, "parenttype": "Item"},
				pluck="parent",
				limit=0,
			)
		)
		codes = linked if codes is None else codes & linked
		selection["supplier"] = party.name
	if item_group:
		group = _pick_item_group(item_group)
		if group.get("found") is False:
			return group
		groups = _get_list(
			"Item Group",
			filters={"lft": [">=", group["lft"]], "rgt": ["<=", group["rgt"]]},
			pluck="name",
			limit=0,
		)
		in_group = set(_get_list("Item", filters={"item_group": ["in", groups]}, pluck="name", limit=0))
		codes = in_group if codes is None else codes & in_group
		selection["item_group"] = group["name"]
	if not codes:
		return {"found": False, "message": "No items match that selection.", **selection}
	if len(codes) > MAX_TREND_ITEMS:
		return {
			"found": False,
			"message": f"{len(codes)} items match (max {MAX_TREND_ITEMS}); narrow by item, supplier or item group.",
			**selection,
		}
	catalogue = {
		i.name: i
		for i in _get_list(
			"Item", filters={"name": ["in", list(codes)]}, fields=["name", "item_name", "stock_uom"], limit=0
		)
	}
	return {"found": True, "items": catalogue, "selection": selection}


def _pick_item_group(search):
	exact = frappe.db.get_value("Item Group", {"name": search}, ["name", "lft", "rgt"], as_dict=True)
	if exact:
		return exact
	hits = _get_list(
		"Item Group", filters={"name": ["like", f"%{search}%"]}, fields=["name", "lft", "rgt"], limit=10
	)
	if len(hits) == 1:
		return hits[0]
	if not hits:
		return {"found": False, "message": f"No item group matches '{search}'."}
	return {
		"found": False,
		"message": "Several item groups match; ask which one.",
		"candidates": [h.name for h in hits],
	}


def _trend_lines(doctype, filters, buckets, catalogue):
	"""{item_code: {"qty": [per bucket], "amount": [per bucket]}} of submitted invoice lines."""
	out = {}
	for i, b in enumerate(buckets):
		rows = _item_breakdown(
			doctype,
			{**filters, "posting_date": ["between", [str(b["from"]), str(b["to"])]]},
			0,
			item_codes=list(catalogue),
		)
		# Lines saved under an older item name come back as their own row; add them up.
		for r in rows:
			v = out.setdefault(r.item_code, {"qty": [0.0] * len(buckets), "amount": [0.0] * len(buckets)})
			v["qty"][i] = flt(v["qty"][i] + flt(r.qty), 3)
			v["amount"][i] = flt(v["amount"][i] + flt(r.net_amount), 2)
	return out


# ── reorder suggestion ──────────────────────────────────────────────────────


def reorder_suggestion(
	item=None,
	items=None,
	supplier=None,
	item_group=None,
	lead_time_days=None,
	review_days=7,
	weeks=12,
	service_level=95,
	only_to_order=False,
	company=None,
	limit=None,
):
	"""Reorder point, safety stock and suggested order qty per item, per company."""
	import math

	weeks = min(max(cint(weeks) or 12, 4), 52)
	review_days = max(cint(review_days) if review_days is not None else 7, 0)
	service_level = cint(service_level) or 95
	if service_level not in SERVICE_LEVELS:
		raise ValueError(f"service_level must be one of {', '.join(map(str, SERVICE_LEVELS))}.")
	z = SERVICE_LEVELS[service_level]
	asked_lead = cint(lead_time_days) if lead_time_days else None
	if asked_lead is not None and asked_lead < 0:
		raise ValueError("lead_time_days can't be negative.")
	limit = _limit(limit or _row_cap["max"])
	company, _cost_center = _scoped(company, None)
	picked = _trend_items(item, items, supplier, item_group)
	if picked.get("found") is False:
		return picked
	catalogue = picked["items"]
	item_lead = dict(
		_get_list(
			"Item",
			filters={"name": ["in", list(catalogue)]},
			fields=["name", "lead_time_days"],
			as_list=True,
			limit=0,
		)
	)

	# Full weeks only: the current week would read low.
	today = getdate(nowdate())
	to_date = getdate(frappe.utils.add_days(_period_start(today, "week"), -1))
	from_date = getdate(frappe.utils.add_days(to_date, -7 * weeks + 1))
	buckets = _trend_buckets(from_date, to_date, "week")

	company_of, warehouses = _warehouses(company, None)
	bin_filters = {"item_code": ["in", list(catalogue)]}
	if warehouses is not None:
		bin_filters["warehouse"] = ["in", warehouses]
	stock, on_order = {}, {}
	for b in _get_list(
		"Bin", filters=bin_filters, fields=["item_code", "warehouse", "actual_qty", "ordered_qty"], limit=0
	):
		key = (company_of.get(b.warehouse), b.item_code)
		stock[key] = flt(stock.get(key, 0) + flt(b.actual_qty), 3)
		on_order[key] = flt(on_order.get(key, 0) + flt(b.ordered_qty), 3)

	companies = [company] if company else _get_list("Company", pluck="name", limit=0)
	out = {}
	for co in companies:
		sold = _trend_lines("Sales Invoice", {"company": co}, buckets, catalogue)
		rows = []
		for code, it in catalogue.items():
			in_stock, ordered = stock.get((co, code), 0.0), on_order.get((co, code), 0.0)
			# A week of more returns than sales counts as no demand, not negative demand.
			weekly = [max(q, 0.0) for q in sold.get(code, {}).get("qty", [0.0] * len(buckets))]
			if not any(weekly) and not in_stock and not ordered:
				continue
			lead = asked_lead if asked_lead is not None else cint(item_lead.get(code)) or DEFAULT_LEAD_DAYS
			avg_week = sum(weekly) / len(weekly)
			std_week = math.sqrt(sum((q - avg_week) ** 2 for q in weekly) / max(len(weekly) - 1, 1))
			daily = avg_week / 7
			safety = z * std_week * math.sqrt(lead / 7)
			reorder_point = daily * lead + safety
			order_up_to = daily * (lead + review_days) + safety
			available = in_stock + ordered
			suggested = max(math.ceil(order_up_to - available), 0) if daily else 0
			cover = flt(max(in_stock, 0) / daily, 1) if daily else None
			weeks_sold = sum(1 for q in weekly if q)
			if not daily:
				status = "no_sales"
			elif weeks_sold < len(weekly) / 4 and available > 0:
				# Sold in under 1 week in 4: the safety stock maths does not fit; still in stock.
				status = "slow_mover"
			elif available <= reorder_point:
				status = "order_now"
			elif cover is not None and cover > 3 * (lead + review_days):
				status = "overstock"
			else:
				status = "ok"
			rows.append(
				{
					"item_code": code,
					"item_name": it.item_name,
					"uom": it.stock_uom,
					"status": status,
					"stock": in_stock,
					"on_order": ordered,
					"avg_weekly_sales": flt(avg_week, 2),
					"weekly_std_dev": flt(std_week, 2),
					"weeks_with_sales": weeks_sold,
					"days_of_cover": cover,
					"lead_time_days": lead,
					"safety_stock": math.ceil(safety),
					"reorder_point": math.ceil(reorder_point),
					"suggested_order": suggested,
				}
			)
		if not rows:
			continue
		rank = {"order_now": 0, "ok": 1, "slow_mover": 2, "overstock": 3, "no_sales": 4}
		# Fast movers first within a status: they run out soonest and matter most.
		rows.sort(key=lambda r: (rank[r["status"]], -r["avg_weekly_sales"], r["stock"]))
		counts = {k: sum(1 for r in rows if r["status"] == k) for k in rank}
		if only_to_order:
			rows = [r for r in rows if r["status"] == "order_now"]
		out[co] = {"status_counts": counts, "items": rows[:limit], "more_rows": len(rows) > limit}

	return {
		"found": True,
		**picked["selection"],
		"items_matched": len(catalogue),
		"as_of": today,
		"sales_from": from_date,
		"sales_to": to_date,
		"weeks": weeks,
		"review_days": review_days,
		"service_level": service_level,
		"lead_time": f"{asked_lead} days (asked)"
		if asked_lead is not None
		else f"per Item lead time, else {DEFAULT_LEAD_DAYS} days",
		**_scope_note(company, None),
		"note": (
			"qty in stock UOM; stock and on_order (open purchase orders) are the company's warehouses now; "
			"days_of_cover = stock / avg daily sales; suggested_order already subtracts stock and on_order"
		),
		"companies": out,
	}


def _trend_default_start(period, to_date):
	add = frappe.utils.add_days
	if period == "day":
		return add(to_date, -29)
	if period == "week":
		return add(to_date, -7 * 11)
	return frappe.utils.add_months(to_date, -5)


def _period_start(day, period):
	if period == "week":
		return frappe.utils.add_days(day, -day.weekday())
	if period == "month":
		return day.replace(day=1)
	return day


def _trend_buckets(from_date, to_date, period):
	buckets, start = [], from_date
	while start <= to_date:
		if period == "day":
			end = start
		elif period == "week":
			end = frappe.utils.add_days(start, 6)
		else:
			end = frappe.utils.get_last_day(start)
		end = getdate(end)
		label = str(start)[:7] if period == "month" else str(start)
		buckets.append({"label": label, "from": start, "end": end, "to": min(end, to_date)})
		start = getdate(frappe.utils.add_days(end, 1))
	return buckets


# ── purchase mirror check ───────────────────────────────────────────────────

MIRROR_FIELDS = [
	"name",
	"naming_series",
	"posting_date",
	"supplier",
	"supplier_name",
	"bill_no",
	"base_grand_total",
	"docstatus",
]


def purchase_mirror_check(from_date=None, to_date=None, company=None, limit=None):
	"""Purchase Invoices of the billing company and the Automatic Entries alternate company, paired the
	way purchase_mirror_api.find_purchase_mirror pairs them (custom_mirrored, else the slash-toggled
	name if that bill is unlinked or links back). A pair counts when either bill is in the period."""
	from ssplbilling.api.automatic_entries_api import get_automatic_entries
	from ssplbilling.api.purchase_mirror_api import should_mirror_purchase_invoice

	ae_doc = get_automatic_entries()
	ae_company = ae_doc.alternative_company
	if not ae_company:
		raise ValueError(
			"No alternative company is set in Automatic Entries, so purchase bills are not mirrored."
		)
	from_date = getdate(from_date or get_first_day(nowdate()))
	to_date = getdate(to_date or nowdate())
	if to_date < from_date:
		raise ValueError("to_date is before from_date")
	limit = _limit(limit)
	wb_company = _mirror_billing_company(company, ae_company)

	fields = list(MIRROR_FIELDS)
	if frappe.get_meta("Purchase Invoice").has_field("custom_mirrored"):
		fields.append("custom_mirrored")

	def bills(company, extra):
		rows = _get_list(
			"Purchase Invoice",
			filters={"company": company, "docstatus": ["<", 2], **extra},
			fields=fields,
			order_by="posting_date asc, name asc",
			limit=0,
		)
		return {r.name: r for r in rows}

	period = {"posting_date": ["between", [from_date, to_date]]}
	wb, ae = bills(wb_company, period), bills(ae_company, period)

	def candidates(row):
		return [n for n in (row.get("custom_mirrored"), _toggle_slash(row.name)) if n]

	# Partners posted outside the period, so a pair split across the period edge is still a pair.
	wanted = {n for r in wb.values() for n in candidates(r) if n not in ae}
	ae_out = bills(ae_company, {"name": ["in", list(wanted)]}) if wanted else {}
	wanted = {n for r in ae.values() for n in candidates(r) if n not in wb}
	wb_out = bills(wb_company, {"name": ["in", list(wanted)]}) if wanted else {}

	pairs, paired_ae = [], set()
	for w in [*wb.values(), *wb_out.values()]:
		for name in candidates(w):
			a = ae.get(name) or ae_out.get(name)
			if a and a.name not in paired_ae and (a.get("custom_mirrored") or "") in ("", w.name):
				if w.name in wb or a.name in ae:
					pairs.append((w, a))
				paired_ae.add(a.name)
				break
	paired_wb = {w.name for w, _a in pairs}
	only_wb = [w for w in wb.values() if w.name not in paired_wb]
	only_ae = [a for a in ae.values() if a.name not in paired_ae]
	pairs.sort(key=lambda p: (p[0].posting_date, p[0].name))

	in_both = [
		{
			"bill": w.name,
			"mirror": a.name,
			"posting_date": w.posting_date,
			"supplier": w.supplier_name or w.supplier,
			"bill_no": w.bill_no,
			"bill_total": flt(w.base_grand_total, 2),
			"mirror_total": flt(a.base_grand_total, 2),
			"difference": flt(flt(w.base_grand_total) - flt(a.base_grand_total), 2),
			"status": _mirror_status(w, a),
		}
		for w, a in pairs
	]
	only_billing = [
		{
			**_mirror_row(w),
			"mirror_series": bool(
				should_mirror_purchase_invoice(w.naming_series, ae_doc)
				or should_mirror_purchase_invoice(w.name, ae_doc)
			),
		}
		for w in only_wb
	]
	only_alternate = [_mirror_row(a) for a in only_ae]
	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"wb_company": wb_company,
		"ae_company": ae_company,
		"summary": {
			"in_both": len(in_both),
			"in_both_total_mismatch": sum(1 for r in in_both if abs(r["difference"]) >= 1),
			"only_in_billing_company": len(only_billing),
			"only_in_billing_company_in_mirror_series": sum(1 for r in only_billing if r["mirror_series"]),
			"only_in_ae_company": len(only_alternate),
			"billing_company_total": flt(sum(flt(r.base_grand_total) for r in wb.values()), 2),
			"ae_company_total": flt(sum(flt(r.base_grand_total) for r in ae.values()), 2),
		},
		"in_both": in_both[:limit],
		"only_in_billing_company": only_billing[:limit],
		"only_in_ae_company": only_alternate[:limit],
		"more_rows": any(len(rows) > limit for rows in (in_both, only_billing, only_alternate)),
		"note": "mirror_series = the bill's series is set for purchase mirroring, so its mirror is missing. "
		"The two company totals overlap by design; never add them.",
	}


def _mirror_billing_company(company, ae_company):
	"""The billing (wb) company to compare against the AE company: the asked / chat company, else the
	user's default company, else the only other company."""
	company, _cost_center = _scoped(company, None)
	if company and company != ae_company:
		return company
	default = frappe.defaults.get_user_default("Company")
	if default and default != ae_company:
		return default
	others = frappe.get_all("Company", filters={"name": ["!=", ae_company]}, pluck="name")
	if len(others) == 1:
		return others[0]
	raise ValueError(f"Pick the billing company (not the AE company {ae_company}) in the company box first.")


def _toggle_slash(name):
	return name[:-1] if name.endswith("/") else f"{name}/"


def _mirror_status(bill, mirror):
	"""One status when both bills agree, else "billing / AE"."""
	states = [_docstatus(bill), _docstatus(mirror)]
	return states[0] if states[0] == states[1] else " / ".join(states)


def _docstatus(row):
	return "Draft" if row.docstatus == 0 else "Submitted"


def _mirror_row(r):
	return {
		"bill": r.name,
		"posting_date": r.posting_date,
		"supplier": r.supplier_name or r.supplier,
		"bill_no": r.bill_no,
		"grand_total": flt(r.base_grand_total, 2),
		"status": _docstatus(r),
		"linked_to": r.get("custom_mirrored") or "",
	}


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
	parent = None
	if meta.istable:
		found = frappe.get_all(
			"DocField", filters={"options": meta.name, "fieldtype": "Table"}, pluck="parent", limit=1
		)
		if found:
			parent = found[0]
			kwargs["parent_doctype"] = parent
	parent_columns = _query_columns(frappe.get_meta(parent)) if parent else set()

	def filter_column(name):
		# A child table may also filter on its parent document's fields (posting_date, docstatus...).
		if name in columns or name not in parent_columns:
			return column(name)
		return name

	own, parent_filters = [], []
	for f in _query_filters(filters, filter_column):
		(own if f[0] in columns else parent_filters).append(f)
	# The chat's company / cost center, as the other tools apply it, unless a filter names them.
	# A child table's company / cost center is on its parent document.
	scope_filters, scope_columns = (parent_filters, parent_columns) if parent else (own, columns)
	named = {f[0]: f for f in [*own, *parent_filters]}  # a child's own cost_center counts too
	scoped = {}  # what the rows are limited to, for the scope note
	if not meta.istable or parent:
		# A company / cost center filter counts as asking for it (and goes through the guard);
		# a chat branch of another company is dropped.
		if "company" in named and not company:
			f = named["company"]
			company = f[2] if f[1] == "=" else "all"
			if f[1] != "=" and not cost_center:
				cost_center = "all"
		if "cost_center" in named and not cost_center:
			f = named["cost_center"]
			cost_center = f[2] if f[1] == "=" else "all"
		company, cost_center = _scoped(company, cost_center)
		for field, value in (("company", company), ("cost_center", cost_center)):
			if value and field in scope_columns:
				scope_filters[:] = [f for f in scope_filters if f[0] != field] + [[field, "=", value]]
				scoped[field] = value
	filters = own
	if parent_filters:
		if _full_read():
			# frappe.get_list joins the parent only while applying permissions, so with Full Read
			# Access its filters would name a table missing from the query (1054 Unknown column).
			names = _get_list(parent, filters=parent_filters, pluck="name", limit=MAX_PARENTS + 1)
			if len(names) > MAX_PARENTS:
				raise ValueError(
					f"Over {MAX_PARENTS} {parent} documents match; narrow the parent filters (e.g. dates)."
				)
			filters = [*own, ["parenttype", "=", parent], ["parent", "in", names or [""]]]
		else:
			filters = [*own, *([parent, *f] for f in parent_filters)]
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
		value = f[2]
		# A list with = / != means in / not in (raw it is invalid SQL: 1064 near '[...]').
		if op in ("=", "!=") and isinstance(value, list | tuple):
			op = "in" if op == "=" else "not in"
		if op in ("in", "not in") and isinstance(value, str):
			value = [v.strip() for v in value.split(",") if v.strip()]
		out.append([column(f[0]), op, value])
	return out


def _get_list(*args, **kwargs):
	"""frappe.get_list as the chat user, or every record when Full Read Access is on."""
	if _full_read():
		kwargs["ignore_permissions"] = True
	return frappe.get_list(*args, **kwargs)


def _full_read():
	return bool(frappe.get_cached_doc("SSPL Assistant Settings").get("full_read_access"))


@contextmanager
def scope(company=None, cost_center=None, question=None):
	"""The company / cost center picked on the chat page, used when a tool call omits them.
	`question` (the user's words, on AI turns) turns on the guard in _guard."""
	_scope.update(
		company=company or None,
		cost_center=cost_center or None,
		question=(question or "").lower() or None,
		guarded=[],
	)
	try:
		yield
	finally:
		_scope.update(company=None, cost_center=None, question=None, guarded=[])


def _guard(company, cost_center):
	"""The AI may leave the chat's company / cost center only when the user's question asks for
	it: "all", "both", "every", "other"..., or names that company / branch. Otherwise the call
	is kept to the chat's selection and run_tool tells the AI so."""
	question = _scope["question"]
	if not question or BROAD_WORDS.search(question):
		return company, cost_center
	if (
		_scope["company"]
		and company not in (None, "", _scope["company"])
		and not _named(company, "Company", question)
	):
		_scope["guarded"].append(f"company {company}")
		company = None
	if (
		_scope["cost_center"]
		and cost_center not in (None, "", _scope["cost_center"])
		and not _named(cost_center, "Cost Center", question)
	):
		_scope["guarded"].append(f"cost center {cost_center}")
		cost_center = None
	return company, cost_center


def _named(value, doctype, question):
	"""Whether the question mentions this company / cost center: full name, first word ("sundaram"),
	the part before " - " ("nck" of "NCK - SSPL"), or for a company its abbreviation and initials
	("sspl" of "SUNDARAM AND SONS PRIVATE LIMITED")."""
	value = str(value)
	if value.lower() == "all":
		return False
	names = {value, value.split(" - ")[0], value.split()[0]}
	if doctype == "Company":
		names.add(frappe.get_cached_value("Company", value, "abbr") or "")
		names.add("".join(w[0] for w in value.split() if w.lower() not in ("and", "of", "the", "&")))
	return any(re.search(rf"\b{re.escape(n.lower())}\b", question) for n in names if len(n.strip()) >= 2)


def _scoped(company, cost_center):
	"""Resolve a tool's company / cost_center args against the chat scope. "all" clears it."""
	company, cost_center = _guard(company, cost_center)
	if company in (None, ""):
		company = _scope["company"]
	all_companies = str(company).lower() == "all"
	if cost_center in (None, ""):
		# "all" companies drops the chat's branch too; it would narrow the answer to its company.
		cost_center = None if all_companies else _scope["cost_center"]
	company = None if all_companies else company
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
	"supplier_item_sales": supplier_item_sales,
	"item_sales_trend": item_sales_trend,
	"reorder_suggestion": reorder_suggestion,
	"purchase_mirror_check": purchase_mirror_check,
	"cash_bank_position": cash_bank_position,
	"cashflow_forecast": cashflow_forecast,
	"profit_loss": profit_loss,
	"gst_summary": gst_summary,
	"payments_summary": payments_summary,
	"describe_doctype": describe_doctype,
	"query_records": query_records,
}
