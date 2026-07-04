# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import money_in_words


class SSPLCheque(Document):
	def validate(self):
		if self.amount:
			self.amount_in_words = money_in_words(self.amount, "INR")
		else:
			self.amount_in_words = ""
