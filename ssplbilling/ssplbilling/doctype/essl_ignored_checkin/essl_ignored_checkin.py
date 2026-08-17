# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class eSSLIgnoredCheckin(Document):
	"""A punch the operator deleted on purpose.

	The eSSL sync re-reads an overlapping window on every run, so a deleted
	Employee Checkin would come straight back on the next tick. A row here is the
	only record that the deletion was deliberate — the sync skips any punch whose
	(employee, time) is listed.
	"""

	def validate(self):
		if not self.employee or not self.time:
			frappe.throw("Employee and Time are required")

		duplicate = frappe.db.exists(
			"eSSL Ignored Checkin",
			{"name": ("!=", self.name), "employee": self.employee, "time": self.time},
		)
		if duplicate:
			frappe.throw(f"{self.employee} already has an ignored checkin at {self.time}")
