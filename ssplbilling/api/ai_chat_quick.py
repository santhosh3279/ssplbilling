"""Quick buttons on the AI Chat page: run one tool from ai_chat_tools and format the result
as markdown here, with no AI call (zero tokens). Same permissions as the AI path, because
the tools run as the logged-in user."""

import json
import re

import frappe
from frappe.utils import add_days, add_months, format_date, get_first_day, get_last_day, getdate, nowdate

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
	"supplier_sales": ("Supplier item sales", True),
	"purchase_mirrors": ("Purchase mirror bills", True),
}
# Actions that ask more than one thing, in order. The page sends the answers joined by STEP_SEP.
STEPS = {
	"supplier_sales": [
		{"key": "supplier", "label": "Supplier", "hint": "type a supplier name, then pick", "suggest": "supplier"},
		{"key": "months", "label": "Sales months", "hint": "months for the monthly average (Enter = 6)", "default": "6"},
	],
	"purchase_mirrors": [
		{
			"key": "period",
			"label": "Period",
			"hint": "Enter = this month, or today / last month / 7 days / 01-11-2026 to 09-11-2026",
			"default": "this month",
		},
	],
}
STEP_SEP = " | "
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


def pie_source(action, query=None):
	"""(tool, args, title) for the 🥧 Pie button under a quick answer."""
	label, query = label_for(action, query)
	tool, args, _fmt = _source(action, query)
	if tool == "sales_summary":
		return tool, {**args, "group_by": "item"}, f"{label}: share by item"
	return tool, args, f"{label}: share"


def label_for(action, query):
	if action not in ACTIONS:
		frappe.throw(f"Unknown quick action: {action}")
	label, needs_query = ACTIONS[action]
	query = (query or "").strip()
	if needs_query and not query.strip(STEP_SEP):
		frappe.throw(f"{label}: type a name, code or mobile first.")
	if action == "supplier_sales":
		supplier, months = _supplier_sales_args(query)
		return f"{label}: {supplier} · {months} months", query
	if action == "purchase_mirrors":
		return f"{label}: {_period(*_period_args(query))}", query
	return (f"{label}: {query}" if query else label), query


def _supplier_sales_args(query):
	supplier, _sep, months = query.rpartition(STEP_SEP)
	if not _sep:
		supplier, months = query, ""
	months = min(max(int(months) if months.strip().isdigit() else 6, 1), 36)
	return supplier.strip(), months


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
		"supplier_sales": _supplier_sales_source(query),
		"purchase_mirrors": _purchase_mirrors_source(query),
	}[action]


def _supplier_sales_source(query):
	supplier, months = _supplier_sales_args(query)
	return (
		"supplier_item_sales",
		{"supplier": supplier, "months": months, "limit": QUICK_TOP_ITEMS},
		_supplier_sales,
	)


def _purchase_mirrors_source(query):
	from_date, to_date = _period_args(query)
	return (
		"purchase_mirror_check",
		{"from_date": str(from_date), "to_date": str(to_date), "limit": QUICK_TOP_ITEMS},
		_purchase_mirrors,
	)


def _period_args(text):
	"""(from_date, to_date) for "today", "yesterday", "this month", "last month", "7 days",
	"01-11-2026 to 09-11-2026" or one date."""
	text = (text or "").strip().lower() or "this month"
	today = getdate(nowdate())
	if text == "today":
		return today, today
	if text == "yesterday":
		day = add_days(today, -1)
		return day, day
	if text == "this month":
		return get_first_day(today), today
	if text == "last month":
		last = add_months(today, -1)
		return get_first_day(last), get_last_day(last)
	days = re.fullmatch(r"(\d+)\s*days?", text)
	if days:
		return add_days(today, 1 - min(max(int(days.group(1)), 1), 366)), today
	start, _sep, end = text.partition(" to ")
	from_date, to_date = _date(start), _date(end or start)
	if not (from_date and to_date):
		frappe.throw(
			f"Period not understood: {text}. Try this month, last month, 7 days or 01-11-2026 to 09-11-2026."
		)
	if to_date < from_date:
		frappe.throw("Period: the end date is before the start date.")
	return from_date, to_date


def _date(text):
	"""dd-mm-yyyy (or with / or .) or yyyy-mm-dd, else None."""
	text = text.strip()
	m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", text)
	if m:
		text = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
	elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
		return None
	try:
		return getdate(text)
	except Exception:
		return None


def _scope_line(data):
	if data.get("ae_company"):  # purchase_mirror_check names both companies itself
		return ""
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


def _supplier_sales(data):
	if not data.get("found"):
		if data.get("candidates"):
			return "Several suppliers match. Tap the button again and pick one.\n\n" + _table(
				["Supplier", "Mobile"],
				[[r.get("supplier_name") or r["name"], r.get("mobile_no") or ""] for r in data["candidates"]],
			)
		return data["message"]
	name = data["supplier_name"] or data["supplier"]
	months = data["months"]
	head = f"**{name}** — sales averages (weekly: last 4 weeks ÷ 4 · monthly: last {months} months ÷ {months})"
	if not data["companies"]:
		return f"{head}\n\n{data.get('message') or 'No stock or sales for this supplier’s items.'}"
	out = [head]
	for company, c in data["companies"].items():
		out.append(f"**{company}** — {c['items_linked']} items")
		out.append(
			_table(
				["#", "Item", "Stock", "Weekly avg", f"Monthly avg ({months}M)"],
				[
					[
						n,
						f"{i['item_name'] or i['item_code']} ({i['item_code']})",
						f"{qty(i['stock'])} {i['uom'] or ''}".strip(),
						qty(i["weekly_avg"]),
						qty(i["monthly_avg"]),
					]
					for n, i in enumerate(c["items"], 1)
				],
			)
		)
		if c["more_rows"]:
			out.append(f"_First {len(c['items'])} of {c['items_linked']} shown. ⬇ Excel has them all._")
	return "\n\n".join(out)


def _purchase_mirrors(data):
	wb, ae, s = data["wb_company"], data["ae_company"], data["summary"]
	out = [
		f"**Purchase mirror bills {_period(data['from_date'], data['to_date'])}**\n\n"
		f"Billing company: **{wb}** · AE company: **{ae}** · drafts included, cancelled skipped",
		_table(
			["Where", "Bills", "Note"],
			[
				[
					"In both",
					s["in_both"],
					f"⚠ {s['in_both_total_mismatch']} with different totals"
					if s["in_both_total_mismatch"]
					else "—",
				],
				[
					f"Only in {wb}",
					s["only_in_billing_company"],
					f"⚠ {s['only_in_billing_company_in_mirror_series']} in a mirror series: mirror missing"
					if s["only_in_billing_company_in_mirror_series"]
					else "—",
				],
				[f"Only in {ae}", s["only_in_ae_company"], "—"],
			],
		),
	]
	if data["in_both"]:
		out.append(
			f"**In both** ({s['in_both']})\n\n"
			+ _table(
				[
					"#",
					f"Bill ({_abbr(wb)})",
					f"Mirror ({_abbr(ae)})",
					"Date",
					"Supplier",
					"Bill total",
					"Mirror total",
					"Status",
				],
				[
					[
						n,
						r["bill"],
						r["mirror"],
						format_date(r["posting_date"]),
						r["supplier"],
						inr(r["bill_total"]),
						inr(r["mirror_total"]) + (" ⚠" if abs(r["difference"]) >= 1 else ""),
						r["status"],
					]
					for n, r in enumerate(data["in_both"], 1)
				],
			)
		)
	if data["only_in_billing_company"]:
		out.append(
			f"**Only in {wb}** ({s['only_in_billing_company']})\n\n"
			+ _table(
				["#", "Bill", "Date", "Supplier", "Supplier bill no", "Total", "Status", "Mirror series"],
				[
					[
						n,
						r["bill"],
						format_date(r["posting_date"]),
						r["supplier"],
						r["bill_no"] or "",
						inr(r["grand_total"]),
						r["status"],
						"⚠ Yes" if r["mirror_series"] else "No",
					]
					for n, r in enumerate(data["only_in_billing_company"], 1)
				],
			)
		)
	if data["only_in_ae_company"]:
		out.append(
			f"**Only in {ae}** ({s['only_in_ae_company']})\n\n"
			+ _table(
				["#", "Bill", "Date", "Supplier", "Supplier bill no", "Total", "Status", "Linked to"],
				[
					[
						n,
						r["bill"],
						format_date(r["posting_date"]),
						r["supplier"],
						r["bill_no"] or "",
						inr(r["grand_total"]),
						r["status"],
						r["linked_to"] or "—",
					]
					for n, r in enumerate(data["only_in_ae_company"], 1)
				],
			)
		)
	if data["more_rows"]:
		out.append(f"_First {QUICK_TOP_ITEMS} of each list shown. ⬇ Excel has them all._")
	return "\n\n".join(out)


def _abbr(company):
	return frappe.get_cached_value("Company", company, "abbr") or company


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
