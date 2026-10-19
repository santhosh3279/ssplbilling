# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class DiscountRule(Document):
	def validate(self):
		# Drop duplicate price list rows; mirror the first into the legacy field.
		seen = set()
		for row in list(self.price_lists):
			if not row.price_list or row.price_list in seen:
				self.remove(row)
			else:
				seen.add(row.price_list)
		self.price_list = self.price_lists[0].price_list if self.price_lists else None
