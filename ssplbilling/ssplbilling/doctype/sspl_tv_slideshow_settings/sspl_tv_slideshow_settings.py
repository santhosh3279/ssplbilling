# Copyright (c) 2026, Sundaram and Sons Private Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SSPLTVSlideshowSettings(Document):
	def validate(self):
		if not 1 <= (self.mat_rows or 0) <= 12:
			frappe.throw("Mat Glider rows must be between 1 and 12")
		if not 1 <= (self.mat_columns or 0) <= 12:
			frappe.throw("Mat Glider columns must be between 1 and 12")
		if (self.mat_speed or 0) < 0:
			frappe.throw("Mat Glider speed cannot be negative")
