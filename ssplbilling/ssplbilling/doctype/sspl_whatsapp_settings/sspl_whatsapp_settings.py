# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class SSPLWhatsAppSettings(Document):
	def validate(self):
		self.base_url = (self.base_url or "").strip().rstrip("/")
		if self.base_url.endswith("/api"):
			self.base_url = self.base_url[: -len("/api")]
		self.validate_sessions()
		self.validate_session_users()
		self.validate_template_usages()

	def validate_sessions(self):
		before = self.get_doc_before_save()
		old_rows = {row.name: row for row in (before.sessions if before else [])}
		names = set()

		for row in self.sessions:
			row.session_name = (row.session_name or "").strip()
			# OpenWA refuses any other name with a bare 400 in production, so catch it here.
			if not re.fullmatch(r"[A-Za-z0-9-]{3,50}", row.session_name):
				frappe.throw(
					_("Row {0}: Session Name must be 3-50 letters, numbers or hyphens").format(row.idx)
				)
			if row.session_name in names:
				frappe.throw(_("Row {0}: Session {1} is listed twice").format(row.idx, row.session_name))
			names.add(row.session_name)

			old = old_rows.get(row.name)
			# A different name is a different WhatsApp link on the gateway. The form refills the row
			# from the gateway when a name is picked; a row it did not refill keeps no stale link.
			if old and old.session_name != row.session_name and old.session_id == row.session_id:
				row.session_id = row.status = row.phone = row.push_name = ""

	def validate_session_users(self):
		names = {row.session_name for row in self.sessions}
		users = set()

		for row in self.session_users:
			if row.user in users:
				frappe.throw(
					_("Users per Session row {0}: {1} already has a session").format(row.idx, row.user)
				)
			users.add(row.user)
			if row.session_name not in names:
				frappe.throw(
					_("Users per Session row {0}: {1} is not in the Sessions table").format(
						row.idx, row.session_name
					)
				)

		# A session no user is assigned to is the shared one, and there can be only one of those
		shared = names - {row.session_name for row in self.session_users}
		if len(shared) > 1:
			frappe.throw(
				_("Only one session can be left without users (the shared one): {0}").format(
					", ".join(sorted(shared))
				)
			)

	def validate_template_usages(self):
		from ssplbilling.api.whatsapp_api import TEMPLATE_AREAS

		placeholders = dict(TEMPLATE_AREAS)
		seen = set()
		for row in self.template_usages:
			key = (row.usage_area, row.user or "")
			if key in seen:
				frappe.throw(
					_("Template per Usage Area row {0}: {1} is listed twice for {2}").format(
						row.idx, row.usage_area, row.user or _("everyone")
					)
				)
			seen.add(key)
			row.placeholders = placeholders.get(row.usage_area, row.placeholders)
