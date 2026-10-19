# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url

WEBHOOK_PATH = "/api/method/ssplbilling.api.paytm_api.payment_webhook"


class SSPLPaytmSettings(Document):
	def validate(self):
		if not self.payment_notification_url:
			self.payment_notification_url = get_url(WEBHOOK_PATH)

		seen = set()
		for row in self.devices:
			tid = (row.tid or "").strip()
			if tid in seen:
				frappe.throw(_("Row {0}: TID {1} is listed more than once").format(row.idx, tid))
			row.tid = tid
			seen.add(tid)
