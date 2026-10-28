"""Excel files and charts for the AI Chat, built from the data tools in ai_chat_tools.

The model (or a quick button) only names the source — a data tool and its args. The data is
re-read here, as the chat user, and goes straight into the file or chart, so a 5,000-row
export costs the same tokens as a 10-row answer and no figure is ever typed by the model.
Results are appended to `attachments` as dicts the chat page renders:

	{"type": "excel", "file": <File name>, "file_name": ..., "title": ..., "rows": n}
	{"type": "chart", "chart_type": "bar"|"line"|"pie", "title": ..., "labels": [...],
	 "datasets": [{"name": ..., "values": [...]}]}
"""

import io
import re

import frappe
from frappe.utils import cint, flt, getdate, random_string
from openpyxl import Workbook
from openpyxl.styles import Font

from ssplbilling.api import ai_chat_tools as tools

FILE_PREFIX = "ai-chat-"
BAR_POINTS = 30
LINE_POINTS = 400

LABELS = {
	"company": "Company",
	"customer": "Customer",
	"customer_name": "Customer Name",
	"mobile_no": "Mobile",
	"item_code": "Item Code",
	"item_name": "Item Name",
	"stock_uom": "UOM",
	"uom": "UOM",
	"warehouse": "Warehouse",
	"posting_date": "Date",
	"due_date": "Due Date",
	"month": "Month",
	"naming_series": "Series",
	"name": "Invoice",
	"invoices": "Invoices",
	"qty": "Qty",
	"net_amount": "Net Amount (₹)",
	"grand_total": "Grand Total (₹)",
	"net_total": "Net Total (₹)",
	"balance": "Balance (₹)",
	"outstanding_amount": "Outstanding (₹)",
	"days_overdue": "Days Overdue",
	"items_in_stock": "Items in Stock",
	"items_negative": "Items Negative",
	"total_qty": "Qty",
	"actual_qty": "Qty",
	"reserved_qty": "Reserved",
	"projected_qty": "Projected",
	"valuation_rate": "Valuation Rate (₹)",
	"stock_value": "Stock Value (₹)",
	"receivable": "Receivable (₹)",
	"advances": "Advances (₹)",
	"customers_owing": "Customers Owing",
	"returns": "Returns (₹)",
	"net_sales": "Net Sales (₹)",
	"draft_invoices": "Draft Invoices",
	"draft_total": "Draft Total (₹)",
}
MONEY = {
	"net_amount",
	"grand_total",
	"net_total",
	"balance",
	"outstanding_amount",
	"valuation_rate",
	"stock_value",
	"receivable",
	"advances",
	"returns",
	"net_sales",
	"draft_total",
}
QTY = {"qty", "total_qty", "actual_qty", "reserved_qty", "projected_qty"}
DATES = {"posting_date", "due_date"}
FORMATS = {"money": "#,##0.00", "qty": "#,##0.###", "date": "DD-MM-YYYY"}


# ── tools the model calls ───────────────────────────────────────────────────


def export_excel(tool, title, args=None, attachments=None):
	sheets = build_sheets(tool, args)
	rows = sum(len(s["rows"]) for s in sheets)
	if not rows:
		return {"ok": False, "message": "No rows to export."}
	file = _save_xlsx(sheets, title)
	if attachments is not None:
		attachments.append(
			{"type": "excel", "file": file.name, "file_name": file.file_name, "title": title, "rows": rows}
		)
	return {"ok": True, "file_name": file.file_name, "rows": rows, "sheets": [s["name"] for s in sheets]}


def make_chart(tool, title, chart_type="bar", args=None, attachments=None):
	if chart_type not in ("bar", "line", "pie"):
		raise ValueError(f"chart_type must be bar, line or pie; got {chart_type!r}")
	labels, datasets = build_series(tool, args, chart_type)
	if not labels:
		return {"ok": False, "message": "No data to chart."}
	if attachments is not None:
		attachments.append(
			{
				"type": "chart",
				"chart_type": chart_type,
				"title": title,
				"labels": labels,
				"datasets": datasets,
			}
		)
	return {"ok": True, "points": len(labels), "series": [d["name"] for d in datasets]}


# ── tables ──────────────────────────────────────────────────────────────────


def _run(tool, args, limit):
	if tool not in tools.DATA_TOOLS:
		raise ValueError(f"tool must be one of {', '.join(tools.DATA_TOOLS)}; got {tool!r}")
	args = {k: v for k, v in (args or {}).items() if k in _params(tool)}
	with tools.export_rows():
		data = tools.HANDLERS[tool](**{**args, "limit": limit})
	if data.get("found") is False:
		raise ValueError(data.get("message") or "Nothing found.")
	return data


def _params(tool):
	return tools.HANDLERS[tool].__code__.co_varnames[: tools.HANDLERS[tool].__code__.co_argcount]


def build_sheets(tool, args=None):
	"""The tool's data as [{"name", "rows": [dict]}], one sheet per company where it splits."""
	data = _run(tool, args, tools.EXPORT_ROWS)
	if tool == "sales_summary":
		summary = [
			{
				"company": company,
				"invoices": c["sales"]["invoices"],
				"grand_total": c["sales"]["grand_total"],
				"returns": c["returns"]["grand_total"],
				"net_sales": c["net_sales"],
				"draft_invoices": c["pending_drafts"]["invoices"],
				"draft_total": c["pending_drafts"]["grand_total"],
			}
			for company, c in data["companies"].items()
		]
		sheets = [{"name": "Summary", "rows": summary}]
		for company, c in data["companies"].items():
			for key, rows in c.items():
				if key.startswith("by_"):
					sheets.append({"name": company, "rows": rows})
		return sheets

	if tool == "customer_outstanding":
		if data.get("customer"):
			return [
				{
					"name": "Balance",
					"rows": [{"company": co, "balance": b} for co, b in data["balance_by_company"].items()],
				},
				{"name": "Open Invoices", "rows": data["open_invoices"]},
			]
		summary = [
			{
				"company": company,
				"receivable": c["receivable"],
				"advances": c["advances"],
				"customers_owing": c["customers_owing"],
			}
			for company, c in data["companies"].items()
		]
		return [{"name": "Summary", "rows": summary}] + [
			{"name": company, "rows": c["top"]} for company, c in data["companies"].items()
		]

	if "warehouses" in data:
		return [{"name": "Warehouses", "rows": data["warehouses"]}]
	rows = []
	for item in data["items"]:
		for w in item["warehouses"]:
			rows.append(
				{"item_code": item["item_code"], "item_name": item["item_name"], "uom": item["uom"], **w}
			)
	return [{"name": "Stock", "rows": rows}]


def _save_xlsx(sheets, title):
	wb = Workbook()
	wb.remove(wb.active)
	used = set()
	for sheet in sheets:
		if not sheet["rows"]:
			continue
		ws = wb.create_sheet(_sheet_title(sheet["name"], used))
		keys = _columns(sheet["rows"])
		ws.append([LABELS.get(k, k.replace("_", " ").title()) for k in keys])
		for cell in ws[1]:
			cell.font = Font(bold=True)
		for row in sheet["rows"]:
			# Customers named by their own code have no customer_name row value: repeat the code.
			if "customer_name" in keys and not row.get("customer_name"):
				row = {**row, "customer_name": row.get("customer")}
			ws.append([_cell(k, row.get(k)) for k in keys])
		for i, key in enumerate(keys, start=1):
			kind = "money" if key in MONEY else "qty" if key in QTY else "date" if key in DATES else None
			if kind:
				for (cell,) in ws.iter_rows(min_row=2, min_col=i, max_col=i):
					cell.number_format = FORMATS[kind]
			width = max(
				len(str(ws.cell(row=r, column=i).value or "")) for r in range(1, min(ws.max_row, 200) + 1)
			)
			ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max(width + 2, 8), 50)
		ws.freeze_panes = "A2"
	wb.properties.title = title

	buf = io.BytesIO()
	wb.save(buf)
	return frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{FILE_PREFIX}{re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:40] or 'export'}-{random_string(6)}.xlsx",
			"is_private": 1,
			"content": buf.getvalue(),
		}
	).insert(ignore_permissions=True)


def _columns(rows):
	keys = []
	for row in rows:
		keys += [k for k in row if k not in keys]
	return keys


def _cell(key, value):
	if key in DATES and value:
		return getdate(value)
	if value is None or isinstance(value, int | float | str):
		return value
	return str(value)


def _sheet_title(name, used):
	title = re.sub(r"[\[\]:*?/\\]", " ", str(name))[:31].strip() or "Sheet"
	base, n = title, 2
	while title in used:
		title = f"{base[:28]} {n}"
		n += 1
	used.add(title)
	return title


# ── charts ──────────────────────────────────────────────────────────────────


def build_series(tool, args=None, chart_type="bar"):
	"""(labels, [{"name", "values"}]) for a chart, one dataset per company where it splits."""
	args = dict(args or {})
	points = LINE_POINTS if chart_type == "line" else BAR_POINTS
	# A line (trend) needs every point; a bar or pie shows the top N the user asked for.
	limit = points if chart_type == "line" else min(cint(args.get("limit")) or 10, points)
	data = _run(tool, args, limit)

	if tool == "sales_summary":
		group = args.get("group_by") or "none"
		if group == "none":
			labels = list(data["companies"])
			if chart_type == "pie":
				return labels, [
					{"name": "Net sales", "values": [c["net_sales"] for c in data["companies"].values()]}
				]
			return labels, [
				{
					"name": name,
					"values": [
						c[key] if key == "net_sales" else c[key]["grand_total"]
						for c in data["companies"].values()
					],
				}
				for name, key in (("Sales", "sales"), ("Returns", "returns"), ("Net", "net_sales"))
			]
		label_key = {
			"customer": "customer_name",
			"item": "item_name",
			"day": "posting_date",
			"month": "month",
			"series": "naming_series",
		}[group]
		value_key = "net_amount" if group == "item" else "grand_total"
		per_company = {
			company: {_label(r, label_key): r[value_key] for r in c.get(f"by_{group}", [])}
			for company, c in data["companies"].items()
		}
		return _align(per_company, points, sort=group in ("day", "month"))

	if tool == "customer_outstanding":
		if data.get("customer"):
			balances = data["balance_by_company"]
			return list(balances), [{"name": "Balance", "values": list(balances.values())}]
		per_company = {
			company: {_label(r, "customer_name"): r["balance"] for r in c["top"]}
			for company, c in data["companies"].items()
		}
		return _align(per_company, points)

	if "warehouses" in data:
		rows = data["warehouses"][:points]
		key, name = ("stock_value", "Stock value") if data["valuation_shown"] else ("total_qty", "Qty")
		return [r["warehouse"] for r in rows], [{"name": name, "values": [flt(r.get(key), 2) for r in rows]}]

	many = len(data["items"]) > 1
	labels, values = [], []
	for item in data["items"]:
		for w in item["warehouses"]:
			labels.append(f"{item['item_code']} · {w['warehouse']}" if many else w["warehouse"])
			values.append(flt(w["actual_qty"], 3))
	return labels[:points], [{"name": "Qty", "values": values[:points]}]


def _label(row, key):
	value = row.get(key) or row.get("customer") or row.get("item_code")
	return str(value)


def _align(per_company, points, sort=False):
	"""One dataset per company over the union of labels (missing = 0)."""
	labels = []
	for values in per_company.values():
		labels += [label for label in values if label not in labels]
	if sort:
		labels.sort()
	labels = labels[-points:] if sort else labels[:points]
	datasets = [
		{"name": company, "values": [flt(values.get(label), 2) for label in labels]}
		for company, values in per_company.items()
		if values
	]
	return labels, datasets


# ── housekeeping ────────────────────────────────────────────────────────────


def delete_old_exports(days=7):
	"""Daily: export files are kept a week; the chat then says the link has expired."""
	cutoff = frappe.utils.add_days(frappe.utils.now_datetime(), -days)
	for name in frappe.get_all(
		"File",
		filters={"file_name": ["like", f"{FILE_PREFIX}%"], "creation": ["<", cutoff]},
		pluck="name",
	):
		frappe.delete_doc("File", name, ignore_permissions=True, force=True)
	frappe.db.commit()
