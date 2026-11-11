"""Scheduled WhatsApp messages (SSPL WhatsApp Schedule).

run_due_schedules() runs every 5 minutes from hooks.py. Each enabled schedule whose next_run_on is
due gets its next_run_on moved forward (committed first, so a slow send is never picked up twice)
and a background send_schedule() job. Messages go through whatsapp_api._send() on the schedule's
session, so every send lands in SSPL WhatsApp Log with the schedule as its reference.

Daily Sales Summary, for one company and one day:
- Sales / Returns: submitted Sales Invoices grouped by the invoice header cost center, returns
  (is_return) on their own lines. Amounts are the rounded total (grand total when not rounded).
- UPI receipts: submitted Receive Payment Entries paid to a UPI account. The cashier's payment
  entries carry no cost center of their own (and say "Cash" as mode of payment when the UPI account
  is not mapped), so UPI is matched by account and split over the cost centers of the bills it was
  allocated to; any unallocated part (advance / on-account receipt) is its own line.
"""

from datetime import datetime

import frappe
from croniter import croniter
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils import (
	add_days,
	cint,
	flt,
	fmt_money,
	formatdate,
	get_datetime,
	get_time,
	getdate,
	now_datetime,
)
from pypika.terms import Case

DOCTYPE = "SSPL WhatsApp Schedule"
UNALLOCATED = "__unallocated__"
CRON_WEEKDAYS = {
	"Sunday": 0,
	"Monday": 1,
	"Tuesday": 2,
	"Wednesday": 3,
	"Thursday": 4,
	"Friday": 5,
	"Saturday": 6,
}

DEFAULT_SECTIONS = {
	"header": "*{schedule}*\n{company} · {date}",
	"sales": "*Sales* ({invoice_count} bills)\n{sales_lines}\n*Total: {total_sales}*",
	"returns": "*Returns* ({return_count})\n{return_lines}\n*Total: {total_returns}*\n\n*Net Sales: {net_sales}*",
	"upi": "*UPI Receipts* ({upi_count})\n{upi_lines}\n*Total: {total_upi}*",
}


# --------------------------------------------------------------------------- timing


def cron_expression(doc):
	if doc.frequency == "Custom Cron":
		return (doc.cron_expression or "").strip()
	t = get_time(doc.send_time or "00:00:00")
	if doc.frequency == "Weekly":
		return f"{t.minute} {t.hour} * * {CRON_WEEKDAYS[doc.weekday]}"
	if doc.frequency == "Monthly":
		return f"{t.minute} {t.hour} {cint(doc.day_of_month)} * *"
	return f"{t.minute} {t.hour} * * *"


def next_run(doc, after=None):
	expr = cron_expression(doc)
	if not croniter.is_valid(expr):
		frappe.throw(_("Invalid cron expression: {0}").format(expr))
	return croniter(expr, get_datetime(after or now_datetime())).get_next(datetime)


def report_date_for(doc, run_on):
	"""The day reported on: that of the scheduled slot, not of when the worker got to it."""
	day = getdate(run_on)
	return add_days(day, -1) if doc.report_period == "Previous Day" else day


def run_due_schedules():
	now = now_datetime()
	for s in frappe.get_all(DOCTYPE, filters={"enabled": 1}, fields=["name", "next_run_on"]):
		try:
			doc = frappe.get_doc(DOCTYPE, s.name)
			if not s.next_run_on:
				doc.db_set("next_run_on", next_run(doc, now), update_modified=False)
				frappe.db.commit()
				continue
			due = get_datetime(s.next_run_on)
			if due > now:
				continue
			# Moved forward and committed before the job exists, so the next tick cannot resend it
			doc.db_set("next_run_on", next_run(doc, now), update_modified=False)
			frappe.db.commit()
			frappe.enqueue(
				f"{__name__}.send_schedule",
				queue="short",
				job_id=f"sspl-whatsapp-schedule::{s.name}::{due.isoformat()}",
				deduplicate=True,
				schedule=s.name,
				due_on=due.isoformat(),
			)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"WhatsApp schedule {s.name} could not be queued")


# --------------------------------------------------------------------------- report data


def _cost_center_label(cost_center):
	if cost_center == UNALLOCATED:
		return _("On Account / Unallocated")
	if not cost_center:
		return _("No Cost Center")
	return frappe.get_cached_value("Cost Center", cost_center, "cost_center_name") or cost_center


def _upi_accounts(company):
	"""Accounts a UPI receipt is paid into: the per-user UPI accounts in SSPL Billing Settings and the
	default accounts of every UPI Mode of Payment for the company."""
	accounts = set(
		frappe.get_all(
			"Mode of Payment Account",
			filters={"parent": ["like", "%UPI%"], "company": company, "default_account": ["is", "set"]},
			pluck="default_account",
		)
	)
	accounts |= set(
		frappe.get_all(
			"USER SERIES",
			filters={"parenttype": "SSPL Billing Settings", "upi": ["is", "set"]},
			pluck="upi",
		)
	)
	return sorted(accounts)


def _sales_by_cost_center(company, day, cost_centers):
	si = frappe.qb.DocType("Sales Invoice")
	amount = Case().when(si.base_rounded_total != 0, si.base_rounded_total).else_(si.base_grand_total)
	query = (
		frappe.qb.from_(si)
		.select(si.cost_center, si.is_return, Count(si.name).as_("count"), Sum(amount).as_("amount"))
		.where((si.docstatus == 1) & (si.company == company) & (si.posting_date == day))
		.groupby(si.cost_center, si.is_return)
	)
	if cost_centers:
		query = query.where(si.cost_center.isin(cost_centers))

	sales, returns = {}, {}
	for row in query.run(as_dict=True):
		target = returns if cint(row.is_return) else sales
		target[row.cost_center] = {"count": cint(row.count), "amount": flt(row.amount, 2)}
	return sales, returns


def _upi_by_cost_center(company, day, cost_centers):
	accounts = _upi_accounts(company)
	if not accounts:
		return {}, accounts

	entries = frappe.get_all(
		"Payment Entry",
		filters={
			"docstatus": 1,
			"payment_type": "Receive",
			"company": company,
			"posting_date": day,
			"paid_to": ["in", accounts],
		},
		fields=["name", "received_amount", "cost_center"],
	)
	if not entries:
		return {}, accounts

	refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"parenttype": "Payment Entry",
			"parent": ["in", [e.name for e in entries]],
			"reference_doctype": "Sales Invoice",
		},
		fields=["parent", "reference_name", "allocated_amount"],
		order_by="idx asc",
	)
	invoice_cc = (
		dict(
			frappe.get_all(
				"Sales Invoice",
				filters={"name": ["in", list({r.reference_name for r in refs})]},
				fields=["name", "cost_center"],
				as_list=True,
			)
		)
		if refs
		else {}
	)
	refs_by_entry = {}
	for r in refs:
		refs_by_entry.setdefault(r.parent, []).append(r)

	totals = {}

	def add(cost_center, amount, entry):
		if amount <= 0.005:
			return
		if cost_centers and cost_center not in cost_centers:
			return
		bucket = totals.setdefault(cost_center, {"amount": 0.0, "entries": set()})
		bucket["amount"] += amount
		bucket["entries"].add(entry)

	for e in entries:
		remaining = flt(e.received_amount, 2)
		for r in refs_by_entry.get(e.name, []):
			part = min(flt(r.allocated_amount, 2), remaining)
			add(invoice_cc.get(r.reference_name), part, e.name)
			remaining -= part
		# Not against any bill: its own line, or under the entry's cost center when only some are wanted
		add(e.cost_center if cost_centers else UNALLOCATED, remaining, e.name)

	return {
		cc: {"count": len(v["entries"]), "amount": flt(v["amount"], 2), "entries": v["entries"]}
		for cc, v in totals.items()
	}, accounts


def get_daily_sales_summary(doc, day):
	cost_centers = [r.cost_center for r in doc.cost_centers or []]
	sales, returns = _sales_by_cost_center(doc.company, day, cost_centers)
	upi, upi_accounts = _upi_by_cost_center(doc.company, day, cost_centers) if doc.include_upi else ({}, [])
	if not doc.include_returns:
		returns = {}
	return {"sales": sales, "returns": returns, "upi": upi, "upi_accounts": upi_accounts}


# --------------------------------------------------------------------------- message


def _lines(groups, money, sign=1):
	if not groups:
		return "• " + _("None")
	ordered = sorted(groups.items(), key=lambda kv: abs(kv[1]["amount"]), reverse=True)
	return "\n".join(
		f"• {_cost_center_label(cc)}: {money(sign * abs(v['amount']))} ({v['count']})" for cc, v in ordered
	)


def build_message(doc, day):
	data = get_daily_sales_summary(doc, day)
	currency = frappe.get_cached_value("Company", doc.company, "default_currency")

	def money(value):
		return fmt_money(value, precision=0, currency=currency)

	total_sales = sum(v["amount"] for v in data["sales"].values())
	total_returns = sum(abs(v["amount"]) for v in data["returns"].values())
	total_upi = sum(v["amount"] for v in data["upi"].values())
	values = {
		"schedule": doc.schedule_name,
		"company": doc.company,
		"date": formatdate(day),
		"sales_lines": _lines(data["sales"], money),
		"total_sales": money(total_sales),
		"invoice_count": sum(v["count"] for v in data["sales"].values()),
		"return_lines": _lines(data["returns"], money, sign=-1),
		"total_returns": money(-total_returns),
		"return_count": sum(v["count"] for v in data["returns"].values()),
		"net_sales": money(total_sales - total_returns),
		"upi_lines": _lines(data["upi"], money),
		"total_upi": money(total_upi),
		# an entry split over two cost centers is still one receipt
		"upi_count": len(set().union(*(v["entries"] for v in data["upi"].values()))),
	}

	template = (doc.message_template or "").strip()
	if not template:
		sections = [DEFAULT_SECTIONS["header"], DEFAULT_SECTIONS["sales"]]
		if doc.include_returns:
			sections.append(DEFAULT_SECTIONS["returns"])
		if doc.include_upi:
			sections.append(DEFAULT_SECTIONS["upi"])
		template = "\n\n".join(sections)

	# Plain replace, so a stray brace in a custom template never breaks the send
	message = template
	for key, value in values.items():
		message = message.replace("{" + key + "}", str(value))
	return message, data


# --------------------------------------------------------------------------- sending


def send_schedule(schedule, due_on=None, report_date=None):
	from ssplbilling.api import whatsapp_api as wa

	doc = frappe.get_doc(DOCTYPE, schedule)
	day = (
		getdate(report_date) if report_date else report_date_for(doc, get_datetime(due_on or now_datetime()))
	)
	recipients = [r for r in doc.recipients if cint(r.enabled)]
	sent, errors = 0, []
	try:
		if not recipients:
			frappe.throw(_("No enabled recipients"))
		message, _data = build_message(doc, day)
		row = wa._managed_row(wa._settings(), doc.session_name)
		for r in recipients:
			try:
				wa._send(
					r.phone,
					"Text",
					"send-text",
					{"text": message},
					message,
					reference=(DOCTYPE, doc.name),
					row=row,
				)
				sent += 1
			except Exception as e:
				errors.append(f"{r.recipient_name or r.phone}: {e}")
	except Exception as e:
		errors.append(str(e))
	finally:
		# _send() throws (and msgprints) on a failed number; the result below reports it instead
		frappe.clear_messages()

	status = "Sent" if not errors else ("Partial" if sent else "Failed")
	doc.db_set(
		{"last_run_on": now_datetime(), "last_status": status, "last_error": "\n".join(errors) or None},
		update_modified=False,
	)
	frappe.db.commit()
	if status != "Sent" and not frappe.request:
		frappe.log_error(title=f"WhatsApp schedule {schedule}: {status}", message="\n".join(errors))
	return {"status": status, "sent": sent, "errors": errors, "date": str(day)}


@frappe.whitelist()
def preview(name, report_date=None):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	day = getdate(report_date) if report_date else report_date_for(doc, now_datetime())
	message, data = build_message(doc, day)
	return {"date": str(day), "message": message, "upi_accounts": data["upi_accounts"]}


@frappe.whitelist(methods=["POST"])
def send_now(name, report_date=None):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	return send_schedule(name, report_date=report_date or report_date_for(doc, now_datetime()))
