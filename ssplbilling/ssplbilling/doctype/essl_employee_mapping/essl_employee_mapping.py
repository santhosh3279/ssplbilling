# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class eSSLEmployeeMapping(Document):
	def validate(self):
		self.machine_user_id = (self.machine_user_id or "").strip()
		if not self.machine_user_id:
			frappe.throw("Machine User ID is required")

		# A device user id may map to only one employee per machine. A row with no
		# machine is the catch-all, so it must not collide with another catch-all.
		# An unset Link lands in the column as NULL or "" depending on how the row was
		# written, so the catch-all scope has to match both.
		machine_filter = self.machine or ("in", ["", None])
		duplicate = frappe.db.exists(
			"eSSL Employee Mapping",
			{
				"name": ("!=", self.name),
				"machine_user_id": self.machine_user_id,
				"machine": machine_filter,
			},
		)
		if duplicate:
			scope = f"machine {self.machine}" if self.machine else "all machines"
			frappe.throw(f"Machine User ID {self.machine_user_id} is already mapped for {scope}")
