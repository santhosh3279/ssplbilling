# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, today

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def parse_weekdays(value):
	"""'mon, Thursday' -> ['Monday', 'Thursday'] in week order. Unknown names raise."""
	picked = set()
	for part in (value or "").split(","):
		part = part.strip().lower()
		if not part:
			continue
		match = [d for d in WEEKDAYS if d.lower().startswith(part[:3])] if len(part) >= 3 else []
		if not match:
			frappe.throw(_("{0} is not a day of the week").format(part))
		picked.add(match[0])
	return [d for d in WEEKDAYS if d in picked]


def parse_month_days(value):
	"""'15, 1' -> [1, 15]. Days outside 1-31 raise."""
	picked = set()
	for part in str(value or "").split(","):
		part = part.strip()
		if not part:
			continue
		if not part.isdigit() or not 1 <= int(part) <= 31:
			frappe.throw(_("Day of month must be between 1 and 31, not {0}").format(part))
		picked.add(int(part))
	return sorted(picked)


class SSPLOrderReminder(Document):
	def validate(self):
		if frappe.db.exists(
			"SSPL Order Reminder",
			{"supplier": self.supplier, "company": self.company, "name": ["!=", self.name]},
		):
			frappe.throw(
				_("{0} already has an order reminder for {1}").format(self.supplier, self.company)
			)

		if self.frequency == "Weekly":
			days = parse_weekdays(self.weekdays)
			if not days:
				frappe.throw(_("Pick at least one ordering day"))
			self.weekdays = ", ".join(days)
		elif self.frequency == "Monthly":
			days = parse_month_days(self.month_days)
			if not days:
				frappe.throw(_("Pick at least one day of the month"))
			self.month_days = ", ".join(str(d) for d in days)
		elif cint(self.interval_days) < 1:
			frappe.throw(_("Every (days) must be 1 or more"))

		self.lead_days = max(cint(self.lead_days), 0)
		if not self.start_date:
			self.start_date = today()
