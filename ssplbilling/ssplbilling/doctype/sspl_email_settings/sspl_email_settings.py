# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Usage areas, matching the Select options on SSPL Email Template Usage
AREA_BILL_SENDING = "Bill Sending (Print Window)"


class SSPLEmailSettings(Document):
	def validate(self):
		seen = set()
		for row in self.template_usages:
			if row.usage_area in seen:
				frappe.throw(f"Row {row.idx}: {row.usage_area} already has a template")
			seen.add(row.usage_area)


def get_area_template(usage_area):
	"""The Email Template set for usage_area, or None."""
	settings = frappe.get_cached_doc("SSPL Email Settings")
	row = next((r for r in settings.template_usages if r.usage_area == usage_area), None)
	return row.email_template if row and row.email_template else None
