# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class eSSLDeviceUser(Document):
	def validate(self):
		self.employee_code = (self.employee_code or "").strip()
		self.template_count = len(self.fingerprints or [])

		# One device code per employee, or attendance would land on two records
		if self.employee:
			clash = frappe.db.exists(
				"eSSL Device User",
				{"employee": self.employee, "name": ("!=", self.name)},
			)
			if clash:
				frappe.throw(f"{self.employee} already holds device code {clash}")
