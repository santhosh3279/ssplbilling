# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerEnquiry(Document):
	def validate(self):
		if not self.customer and not (self.new_customer or "").strip():
			frappe.throw("Select an existing customer or enter a name in New Customer")

		# Title falls back: linked customer name → new customer name → customer id
		if not self.customer_name:
			self.customer_name = (self.new_customer or "").strip() or self.customer

		if self.status == "Closed" and not self.closed_on:
			self.closed_on = frappe.utils.now_datetime()
		elif self.status == "Open":
			self.closed_on = None
