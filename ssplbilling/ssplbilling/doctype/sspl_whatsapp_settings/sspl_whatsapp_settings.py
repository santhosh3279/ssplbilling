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

		self.session_name = (self.session_name or "").strip()
		# OpenWA refuses any other name with a bare 400 in production, so catch it here.
		if not re.fullmatch(r"[A-Za-z0-9-]{3,50}", self.session_name):
			frappe.throw(_("Session Name must be 3-50 letters, numbers or hyphens"))
