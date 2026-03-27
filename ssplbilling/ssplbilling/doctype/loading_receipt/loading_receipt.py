import frappe
from frappe.model.document import Document


class LoadingReceipt(Document):
	def before_save(self):
		self.calculate_total()

	def calculate_total(self):
		total = sum(row.amount or 0 for row in self.loading_items)
		self.total = total
