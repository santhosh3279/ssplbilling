# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class VersionPurgeSettings(Document):
	@frappe.whitelist()
	def purge_now(self) -> int:
		"""Manually triggers purging of version history records older than configured retention days."""
		days = self.retention_days or 90
		return purge_versions(days)


def purge_versions(days: int) -> int:
	"""Purges Version records older than days without writing to Deleted Document."""
	version_table = frappe.qb.DocType("Version")

	# Count records first to report/return the number of deleted records
	count = frappe.db.count("Version", filters=(version_table.creation < (Now() - Interval(days=days))))

	if count > 0:
		frappe.db.delete(
			version_table,
			filters=(version_table.creation < (Now() - Interval(days=days)))
		)
		frappe.db.commit()

	return count


def daily_purge():
	"""Scheduled job to purge versions daily automatically if enabled in settings."""
	settings = frappe.get_cached_doc("Version Purge Settings")
	if settings.enabled:
		days = settings.retention_days or 90
		purge_versions(days)
