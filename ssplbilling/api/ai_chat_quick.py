"""Quick buttons on the AI Chat page: run one tool from ai_chat_tools and format the result
as markdown here, with no AI call (zero tokens). Same permissions as the AI path, because
the tools run as the logged-in user."""

import json

import frappe
from frappe.utils import format_date, get_first_day, getdate, nowdate

from ssplbilling.api import ai_chat_tools as tools

# action id → (label, needs a search text)
ACTIONS = {
	"sales_today": ("Sales today", False),
	"sales_month": ("Sales this month", False),
	"top_items": ("Top items (80% of sales)", False),
	"top_outstanding": ("Top outstanding", False),
	"customer_outstanding": ("Customer outstanding", True),
	"stock_summary": ("Stock summary", False),
	"item_stock": ("Item stock", True),
}
# Top items shown in the chat; ⬇ Excel has the full list.
QUICK_TOP_ITEMS = 50


def answer(action, query=None):
	"""Returns (label shown as the user's message, markdown reply)."""
	label, query = label_for(action, query)
	tool, args, fmt = _source(action, query)
	data = _tool(tool, **args)
	return label, data if isinstance(data, str) else _scope_line(data) + fmt(data)


def export_source(action, query=None):
	"""(tool, args, title) for the ⬇ Excel button under a quick answer."""
	label, query = label_for(action, query)
	tool, args, _fmt = _source(action, query)
	if tool == "sales_summary":
		args = {**args, "group_by": "item"}
	return tool, args, label


def chart_source(action, query=None):
	"""(tool, args, title, chart_type) for the 📊 Chart button under a quick answer."""
	label, query = label_for(action, query)
	tool, args, _fmt = _source(action, query)
	if action == "sales_month":
		return tool, {**args, "group_by": "day"}, f"{label}: daily", "line"
	return tool, args, label, "bar"


def label_for(action, query):
	if action not in ACTIONS:
		frappe.throw(f"Unknown quick action: {action}")
	label, needs_query = ACTIONS[action]
	query = (query or "").strip()
	if needs_query and not query:
		frappe.throw(f"{label}: type a name, code or mobile first.")
	return (f"{label}: {query}" if query else label), query


def _source(action, query):
	today = getdate(nowdate())
	return {
		"sales_today": ("sales_summary", {"from_date": str(today)}, _sales),
		"sales_month": (
			"sales_summary",
			{"from_date": str(get_first_day(today)), "to_date": str(today)},
			_sales,
		),
		"top_items": (
			"top_items",
			{"from_date": str(get_first_day(today)), "to_date": str(today), "limit": QUICK_TOP_ITEMS},
			_top_items,
		),
		"top_outstanding": ("customer_outstanding", {"limit": 10}, _top_outstanding),
		"customer_outstanding": ("customer_outstanding", {"customer": query, "limit": 20}, _customer),
		"stock_summary": ("item_stock", {}, _stock_summary),
		"item_stock": ("item_stock", {"item": query, "limit": 10}, _item_stock),
	}[action]


def _scope_line(data):
	scope = [data.get("company_filter"), data.get("cost_center_filter")]
	scope = [s for s in scope if s and not s.startswith("all ")]
	return f"_{' · '.join(scope)}_\n\n" if scope else "_All companies_\n\n"


def _tool(name, **args):
	"""Tool result as a dict, or the error text to show as the reply."""
	content, is_error = tools.run_tool(name, args)
	return f"⚠ {content}" if is_error else json.loads(content)


# ── formatting ──────────────────────────────────────────────────────────────


def _sales(data):
	period = _period(data["from_date"], data["to_date"])
	if not data["companies"]:
		return f"No sales {period}."
	rows = []
	for company, c in data["companies"].items():
		drafts = c["pending_drafts"]
		rows.append(
			[
				company,
				c["sales"]["invoices"],
				inr(c["sales"]["grand_total"]),
				inr(c["returns"]["grand_total"]),
				f"**{inr(c['net_sales'])}**",
				f"{drafts['invoices']} · {inr(drafts['grand_total'])}" if drafts["invoices"] else "—",
			]
		)
	return f"**Sales {period}** (incl. tax)\n\n" + _table(
		["Company", "Invoices", "Sales", "Returns", "Net", "Pending drafts"], rows
	)


def _top_items(data):
	period = _period(data["from_date"], data["to_date"])
	if not data["companies"]:
		return f"No item sales {period}."
	out = [f"**Items making {data['share_target_pct']:g}% of net sales {period}** (excl. tax)"]
	for company, c in data["companies"].items():
		out.append(
			f"**{company}** — {c['top_items']} of {c['items_sold']} items sold "
			f"({c['top_items_pct_of_items']:g}%) make {inr(c['top_items_net_sales'])} "
			f"of {inr(c['net_sales'])}"
		)
		out.append(
			_table(
				["#", "Item", "Qty", "Net sales", "Share", "Cumulative"],
				[
					[
						i["rank"],
						f"{i['item_name'] or i['item_code']} ({i['item_code']})",
						f"{qty(i['qty'])} {i['uom'] or ''}".strip(),
						inr(i["net_amount"]),
						f"{i['share_pct']:.1f}%",
						f"{i['cumulative_pct']:.1f}%",
					]
					for i in c["items"]
				],
			)
		)
		if c["more_rows"]:
			out.append(f"_First {len(c['items'])} of {c['top_items']} shown. ⬇ Excel has them all._")
	return "\n\n".join(out)


def _top_outstanding(data):
	if not data["companies"]:
		return "No customer balances."
	out = []
	for company, c in data["companies"].items():
		out.append(
			f"**{company}** — receivable **{inr(c['receivable'])}** from {c['customers_owing']} customers"
			+ (f", advances {inr(c['advances'])}" if c["advances"] else "")
		)
		out.append(
			_table(
				["Customer", "Balance"],
				[[r.get("customer_name") or r["customer"], inr(r["balance"])] for r in c["top"]],
			)
		)
	return "\n\n".join(out)


def _customer(data):
	if not data.get("found"):
		text = data["message"]
		if data.get("candidates"):
			text = (
				"Several customers match. Tap the button again with the exact name or mobile.\n\n"
				+ _table(
					["Customer", "Mobile"],
					[[r["customer_name"] or r["name"], r.get("mobile_no") or ""] for r in data["candidates"]],
				)
			)
		return text
	name = data["customer_name"] or data["customer"]
	out = [f"**{name}**" + (f" · {data['mobile_no']}" if data.get("mobile_no") else "")]
	if data["balance_by_company"]:
		out.append(
			_table(["Company", "Balance"], [[co, inr(b)] for co, b in data["balance_by_company"].items()])
		)
	else:
		out.append("No balance — fully settled.")
	if data["open_invoices"]:
		out.append(
			"Open invoices (oldest first)\n\n"
			+ _table(
				["Invoice", "Company", "Date", "Outstanding", "Overdue"],
				[
					[
						i["name"],
						i["company"],
						format_date(i["posting_date"]),
						inr(i["outstanding_amount"]),
						f"{i['days_overdue']} d" if i["days_overdue"] else "—",
					]
					for i in data["open_invoices"]
				],
			)
		)
	return "\n\n".join(out)


def _stock_summary(data):
	if not data["warehouses"]:
		return "No stock found."
	headers = ["Warehouse", "Company", "Items in stock", "Qty", "Items negative"]
	if data["valuation_shown"]:
		headers.append("Value")
	rows = []
	for w in data["warehouses"]:
		row = [
			w["warehouse"],
			w["company"],
			w["items_in_stock"],
			qty(w["total_qty"]),
			w["items_negative"] or "—",
		]
		if data["valuation_shown"]:
			row.append(inr(w.get("stock_value")))
		rows.append(row)
	return f"**Stock as of {format_date(data['as_of'])}**\n\n" + _table(headers, rows)


def _item_stock(data):
	if not data.get("found"):
		return data["message"]
	out = []
	for item in data["items"]:
		title = f"**{item['item_code']}** — {item['item_name']} ({item['uom']})"
		if item["disabled"]:
			title += " · disabled"
		if not item["warehouses"]:
			out.append(f"{title}\n\nNo stock in any warehouse.")
			continue
		headers = ["Warehouse", "Company", "Qty", "Reserved", "Projected"]
		if data["valuation_shown"]:
			headers.append("Value")
		rows = []
		for w in item["warehouses"]:
			row = [
				w["warehouse"],
				w["company"],
				qty(w["actual_qty"]),
				qty(w["reserved_qty"]),
				qty(w["projected_qty"]),
			]
			if data["valuation_shown"]:
				row.append(inr(w.get("stock_value")))
			rows.append(row)
		out.append(f"{title}\n\n" + _table(headers, rows))
	return "\n\n".join(out)


def _period(from_date, to_date):
	if from_date == to_date:
		return f"on {format_date(from_date)}"
	return f"{format_date(from_date)} to {format_date(to_date)}"


def _table(headers, rows):
	lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
	lines += ["| " + " | ".join(str(v).replace("|", "\\|") for v in r) + " |" for r in rows]
	return "\n".join(lines)


def inr(value):
	"""₹ with Indian digit grouping, whole rupees: ₹12,34,567."""
	value = round(float(value or 0))
	digits = str(abs(value))
	head, tail = digits[:-3], digits[-3:]
	groups = []
	while len(head) > 2:
		groups.insert(0, head[-2:])
		head = head[:-2]
	if head:
		groups.insert(0, head)
	return ("-" if value < 0 else "") + "₹" + ",".join([*groups, tail])


def qty(value):
	value = float(value or 0)
	return f"{value:g}" if value == int(value) else f"{value:.2f}"
