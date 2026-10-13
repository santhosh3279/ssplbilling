# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EInvoiceSeries(Document):
	def validate(self):
		self.series = (self.series or "").strip()
		options = frappe.get_meta("Sales Invoice").get_options("naming_series") or ""
		known = [s.strip() for s in options.split("\n") if s.strip()]
		if known and not any(s == self.series or s.startswith(self.series) for s in known):
			frappe.throw(f"{self.series} does not match any Sales Invoice naming series ({', '.join(known)}).")
