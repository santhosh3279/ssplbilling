# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SSPLWhatsAppTemplate(Document):
	def validate(self):
		if self.all_users:
			self.users = []
		self.validate_unique_users()
		self.validate_one_default()

	def validate_unique_users(self):
		"""A user sends one template per usage area, so may be on only one template of it."""
		users = [row.user for row in self.users]
		dupes = {u for u in users if users.count(u) > 1}
		if dupes:
			frappe.throw(_("Users listed twice: {0}").format(", ".join(sorted(dupes))))
		if not users:
			return
		taken = frappe.get_all(
			"SSPL WhatsApp Template",
			filters=[
				["usage_area", "=", self.usage_area],
				["name", "!=", self.name],
				["SSPL WhatsApp Template User", "user", "in", users],
			],
			fields=["name", "`tabSSPL WhatsApp Template User`.user as user"],
		)
		if taken:
			frappe.throw(
				_("Already on another {0} template: {1}").format(
					self.usage_area, ", ".join(f"{t.user} ({t.name})" for t in taken)
				)
			)

	def validate_one_default(self):
		if not self.all_users:
			return
		other = frappe.db.get_value(
			"SSPL WhatsApp Template",
			{"usage_area": self.usage_area, "all_users": 1, "name": ["!=", self.name]},
		)
		if other:
			frappe.throw(
				_("{0} is already the All Users template for {1}; untick it there first").format(
					other, self.usage_area
				)
			)
