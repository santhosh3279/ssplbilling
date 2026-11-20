# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words

PRINT_NAME_FIELDS = {
	"Customer": "customer_print_name",
	"Supplier": "supplier_print_name",
}


class SSPLCheque(Document):
	def validate(self):
		if self.amount:
			self.amount_in_words = money_in_words(self.amount, "INR")
		else:
			self.amount_in_words = ""
		self.set_print_name()

	def set_print_name(self):
		"""Copy the party's print name; leave empty when the party doctype has no such field."""
		fieldname = PRINT_NAME_FIELDS.get(self.party_type)
		if not (fieldname and self.party and frappe.get_meta(self.party_type).has_field(fieldname)):
			self.print_name = ""
			return
		self.print_name = frappe.db.get_value(self.party_type, self.party, fieldname) or ""
