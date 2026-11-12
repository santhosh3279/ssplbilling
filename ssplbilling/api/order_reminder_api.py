"""Supplier ordering reminders (SSPL Order Reminder).

One reminder per supplier and company says when that supplier is ordered from:
- Weekly: on the ticked weekdays.
- Monthly: on the listed days of the month (a day past the month's end falls on its last day).
- Every N Days: N days after the last order.

Nothing is stored about "the next due date": it is worked out each time from what is settled.
A cycle is settled by a Purchase Order for the supplier (cancelled ones excluded), or by the
Ordered / Skip buttons, which write `handled_upto`. For Weekly and Monthly, `handled_upto` is the
cycle date that was dealt with and the next due date is the first ordering day after it; a Purchase
Order made within the lead time before an ordering day settles that day. For Every N Days it is the
date of the order and the next due date is N days later.

Snooze only hides a reminder from the due lists until `snooze_until`; it settles nothing.
"""

import calendar
import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, today

from ssplbilling.ssplbilling.doctype.sspl_order_reminder.sspl_order_reminder import (
	WEEKDAYS,
	parse_month_days,
	parse_weekdays,
)

DOCTYPE = "SSPL Order Reminder"
FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"company",
	"enabled",
	"assigned_to",
	"frequency",
	"weekdays",
	"month_days",
	"interval_days",
	"lead_days",
	"start_date",
	"notes",
	"handled_upto",
	"snooze_until",
	"last_action",
	"last_action_on",
	"last_action_by",
	"last_note",
]
# A fixed schedule always has an ordering day within this many days (monthly: at most 31 apart)
SEARCH_DAYS = 400


# --------------------------------------------------------------------------- due date


def _is_ordering_day(rem, day):
	if rem.frequency == "Weekly":
		return WEEKDAYS[day.weekday()] in parse_weekdays(rem.weekdays)
	last = calendar.monthrange(day.year, day.month)[1]
	return day.day in {min(d, last) for d in parse_month_days(rem.month_days)}


def next_ordering_day(rem, after):
	"""First Weekly / Monthly ordering day strictly after `after`."""
	day = getdate(after)
	for _i in range(SEARCH_DAYS):
		day += timedelta(days=1)
		if _is_ordering_day(rem, day):
			return day
	return None


def due_date(rem, last_po_date=None):
	"""The ordering day this reminder is waiting on, given what is already settled."""
	start = getdate(rem.start_date) if rem.start_date else getdate(today())
	handled = getdate(rem.handled_upto) if rem.handled_upto else None
	last_po = getdate(last_po_date) if last_po_date else None

	if rem.frequency == "Every N Days":
		settled = max([d for d in (handled, last_po) if d], default=None)
		if not settled:
			return start
		return max(add_days(settled, max(cint(rem.interval_days), 1)), start)

	settled = [add_days(start, -1)]
	if handled:
		settled.append(handled)
	if last_po:
		settled.append(add_days(last_po, cint(rem.lead_days)))
	return next_ordering_day(rem, max(settled))


def _status(rem, due, day):
	if not cint(rem.enabled):
		return "disabled"
	if not due:
		return "upcoming"
	if day < add_days(due, -cint(rem.lead_days)):
		return "upcoming"
	if rem.snooze_until and day < getdate(rem.snooze_until):
		return "snoozed"
	return "overdue" if day > due else "due"


def _schedule_label(rem):
	if rem.frequency == "Weekly":
		days = parse_weekdays(rem.weekdays)
		return _("Daily") if len(days) == 7 else ", ".join(d[:3] for d in days)
	if rem.frequency == "Monthly":
		return _("Monthly on {0}").format(", ".join(str(d) for d in parse_month_days(rem.month_days)))
	return _("Every {0} days").format(cint(rem.interval_days))


def _last_purchase_orders(company, suppliers):
	"""{supplier: latest Purchase Order row} for the company, cancelled orders excluded."""
	latest = {}
	for supplier in set(suppliers):
		rows = frappe.get_all(
			"Purchase Order",
			filters={"supplier": supplier, "company": company, "docstatus": ["!=", 2]},
			fields=["name", "transaction_date", "grand_total", "docstatus"],
			order_by="transaction_date desc, creation desc",
			limit=1,
		)
		if rows:
			latest[supplier] = rows[0]
	return latest


def _default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
		or frappe.db.get_value("Company", {}, "name")
	)


def reminders_for(company, day=None, enabled_only=False):
	"""Every reminder of the company with its due date and status as of `day`."""
	day = getdate(day or today())
	filters = {"company": company}
	if enabled_only:
		filters["enabled"] = 1
	rows = frappe.get_all(DOCTYPE, filters=filters, fields=FIELDS, order_by="supplier_name asc")
	orders = _last_purchase_orders(company, [r.supplier for r in rows])

	out = []
	for rem in rows:
		po = orders.get(rem.supplier)
		due = due_date(rem, po.transaction_date if po else None)
		status = _status(rem, due, day)
		out.append(
			{
				**rem,
				"supplier_name": rem.supplier_name or rem.supplier,
				"schedule": _schedule_label(rem),
				"weekday_list": parse_weekdays(rem.weekdays) if rem.frequency == "Weekly" else [],
				"month_day_list": parse_month_days(rem.month_days) if rem.frequency == "Monthly" else [],
				"due_date": str(due) if due else None,
				"days_to_due": (due - day).days if due else None,
				"status": status,
				"last_po": po.name if po else None,
				"last_po_date": str(po.transaction_date) if po else None,
				"last_po_amount": flt(po.grand_total) if po else None,
				"last_po_is_draft": bool(po and po.docstatus == 0),
			}
		)
	return out


# --------------------------------------------------------------------------- page endpoints


@frappe.whitelist()
def get_reminders(company=None):
	company = company or _default_company()
	reminders = reminders_for(company)
	counts = {}
	for r in reminders:
		counts[r["status"]] = counts.get(r["status"], 0) + 1
	return {
		"company": company,
		"companies": frappe.get_all("Company", pluck="name", order_by="name asc"),
		"today": today(),
		"reminders": reminders,
		"counts": counts,
	}


@frappe.whitelist()
def get_due_count(company=None):
	"""Reminders due or overdue today — the dashboard tile badge."""
	company = company or _default_company()
	return sum(1 for r in reminders_for(company, enabled_only=True) if r["status"] in ("due", "overdue"))


@frappe.whitelist()
def get_users():
	"""Users a reminder can be assigned to."""
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)


@frappe.whitelist(methods=["POST"])
def save_reminder(data):
	if isinstance(data, str):
		data = json.loads(data)
	name = data.get("name")
	doc = frappe.get_doc(DOCTYPE, name) if name else frappe.new_doc(DOCTYPE)
	was = (doc.frequency, doc.weekdays, doc.month_days, cint(doc.interval_days)) if name else None

	doc.supplier = data.get("supplier")
	doc.company = data.get("company") or _default_company()
	doc.enabled = cint(data.get("enabled", 1))
	doc.assigned_to = data.get("assigned_to") or None
	doc.frequency = data.get("frequency") or "Weekly"
	doc.weekdays = data.get("weekdays") or ""
	doc.month_days = str(data.get("month_days") or "")
	doc.interval_days = cint(data.get("interval_days"))
	doc.lead_days = cint(data.get("lead_days"))
	doc.start_date = data.get("start_date") or doc.start_date or today()
	doc.notes = data.get("notes") or ""
	doc.save(ignore_permissions=True)

	# A snooze belongs to the schedule it was set under
	if was and was != (doc.frequency, doc.weekdays, doc.month_days, cint(doc.interval_days)):
		doc.db_set("snooze_until", None)
	return doc.name


@frappe.whitelist(methods=["POST"])
def delete_reminder(name):
	frappe.delete_doc(DOCTYPE, name, ignore_permissions=True)
	return True


def _current_due(doc):
	po = _last_purchase_orders(doc.company, [doc.supplier]).get(doc.supplier)
	return due_date(doc, po.transaction_date if po else None)


def _settle(doc, action, upto, note=None):
	doc.db_set(
		{
			"handled_upto": upto,
			"snooze_until": None,
			"last_action": action,
			"last_action_on": today(),
			"last_action_by": frappe.session.user,
			"last_note": (note or "").strip() or None,
		}
	)


@frappe.whitelist(methods=["POST"])
def mark_ordered(name, note=None):
	"""The order was placed without a Purchase Order (phone, WhatsApp, visit)."""
	doc = frappe.get_doc(DOCTYPE, name)
	day = getdate(today())
	if doc.frequency == "Every N Days":
		upto = day
	else:
		upto = max(_current_due(doc) or day, day)
	_settle(doc, "Ordered", upto, note)
	return True


@frappe.whitelist(methods=["POST"])
def skip_cycle(name, reason=None):
	"""Nothing to order this time; wait for the next ordering day."""
	doc = frappe.get_doc(DOCTYPE, name)
	day = getdate(today())
	due = _current_due(doc) or day
	if doc.frequency == "Every N Days":
		# Skipping a cycle that is more than a whole interval late must not leave it overdue again
		upto = due if add_days(due, max(cint(doc.interval_days), 1)) > day else day
	else:
		upto = max(due, day)
	_settle(doc, "Skipped", upto, reason)
	return True


@frappe.whitelist(methods=["POST"])
def snooze(name, days=1):
	days = cint(days)
	if days < 1:
		frappe.throw(_("Snooze for at least one day"))
	frappe.get_doc(DOCTYPE, name).db_set("snooze_until", add_days(today(), days))
	return True
