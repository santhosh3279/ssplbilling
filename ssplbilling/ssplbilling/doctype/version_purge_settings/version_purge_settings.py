# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class VersionPurgeSettings(Document):
	@frappe.whitelist()
	def purge_now(self) -> dict:
		"""Manually triggers purging of both version history and deleted documents."""
		results = {"versions": 0, "deleted_docs": 0}

		if self.enabled:
			days = self.retention_days or 90
			results["versions"] = purge_versions(days)

		if self.purge_deleted_docs:
			days = self.deleted_docs_retention_days or 180
			results["deleted_docs"] = purge_deleted_documents(days)

		return results


def purge_versions(days: int) -> int:
	"""Purges Version records older than days without writing to Deleted Document."""
	version_table = frappe.qb.DocType("Version")

	count = frappe.db.count("Version", filters=(version_table.creation < (Now() - Interval(days=days))))

	if count > 0:
		frappe.db.delete(
			version_table,
			filters=(version_table.creation < (Now() - Interval(days=days)))
		)
		frappe.db.commit()

	return count


def purge_deleted_documents(days: int) -> int:
	"""Purges Deleted Document records older than days."""
	deleted_doc_table = frappe.qb.DocType("Deleted Document")

	count = frappe.db.count("Deleted Document", filters=(deleted_doc_table.creation < (Now() - Interval(days=days))))

	if count > 0:
		frappe.db.delete(
			deleted_doc_table,
			filters=(deleted_doc_table.creation < (Now() - Interval(days=days)))
		)
		frappe.db.commit()

	return count


def daily_purge():
	"""Scheduled job to purge versions and deleted documents daily automatically if enabled."""
	settings = frappe.get_cached_doc("Version Purge Settings")

	if settings.enabled:
		days = settings.retention_days or 90
		purge_versions(days)

	if settings.purge_deleted_docs:
		days = settings.deleted_docs_retention_days or 180
		purge_deleted_documents(days)
