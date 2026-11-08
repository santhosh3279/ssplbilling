# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SSPLWhatsAppTemplate(Document):
	def validate(self):
		self.validate_area_usages()

	def validate_area_usages(self):
		"""A template moved to another usage area must not stay set for an area it no longer serves."""
		if not self.usage_area or self.is_new():
			return
		wrong = frappe.get_all(
			"SSPL WhatsApp Template Usage",
			filters={"template_name": self.name, "usage_area": ["!=", self.usage_area]},
			pluck="usage_area",
			distinct=True,
		)
		if wrong:
			frappe.throw(
				_("{0} is set for {1} in SSPL WhatsApp Settings; clear it there first").format(
					self.name, ", ".join(wrong)
				)
			)
