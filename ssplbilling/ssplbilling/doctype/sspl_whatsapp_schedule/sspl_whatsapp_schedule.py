# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class SSPLWhatsAppSchedule(Document):
	def validate(self):
		from ssplbilling.api import whatsapp_api as wa
		from ssplbilling.api.whatsapp_scheduler import next_run

		if self.frequency == "Monthly" and not 1 <= cint(self.day_of_month) <= 28:
			frappe.throw(_("Day of Month must be between 1 and 28"))

		sessions = [r.session_name for r in wa._settings().sessions]
		if self.session_name not in sessions:
			frappe.throw(_("WhatsApp session {0} is not in SSPL WhatsApp Settings").format(self.session_name))

		for r in self.recipients:
			if not wa.normalize_whatsapp_number(r.phone):
				frappe.throw(_("Row {0}: {1} is not a valid WhatsApp number").format(r.idx, r.phone))
		if self.enabled and not any(cint(r.enabled) for r in self.recipients):
			frappe.throw(_("Add at least one enabled recipient"))

		for r in self.cost_centers:
			if frappe.db.get_value("Cost Center", r.cost_center, "company") != self.company:
				frappe.throw(_("Cost Center {0} does not belong to {1}").format(r.cost_center, self.company))

		# Also validates the cron expression
		self.next_run_on = next_run(self) if self.enabled else None
