# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SSPLPrinterSetting(Document):
	def on_update(self):
		frappe.cache().delete_value("sspl_printer_settings")

	def on_trash(self):
		frappe.cache().delete_value("sspl_printer_settings")
