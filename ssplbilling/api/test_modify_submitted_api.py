# Copyright (c) 2026, SSPL and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from ssplbilling.api.modify_submitted_api import (
	get_submitted_invoice,
	modify_submitted_bill_date,
)


class TestModifySubmittedAPI(IntegrationTestCase):
	def test_tile_registered(self):
		"""Verify modifysubmitted dashboard tile exists."""
		self.assertTrue(frappe.db.exists("SSPL Dashboard Tile", "modifysubmitted"))
		tile = frappe.get_doc("SSPL Dashboard Tile", "modifysubmitted")
		self.assertEqual(tile.bucket, "Sale")

	def test_get_nonexistent_invoice_fails(self):
		"""Querying a non-existent invoice should throw an error."""
		with self.assertRaises(frappe.ValidationError):
			get_submitted_invoice("NON-EXISTENT-INV-999999")

	def test_get_draft_invoice_fails(self):
		"""Querying a draft invoice should throw an error stating it is draft."""
		draft_inv = frappe.db.get_value("Sales Invoice", {"docstatus": 0}, "name")
		if draft_inv:
			with self.assertRaises(frappe.ValidationError):
				get_submitted_invoice(draft_inv)

	def test_get_and_modify_submitted_invoice(self):
		"""Test fetching and updating a submitted invoice's bill date."""
		sub_inv = frappe.db.get_value("Sales Invoice", {"docstatus": 1}, ["name", "posting_date"], as_dict=True)
		if not sub_inv:
			return

		inv_no = sub_inv.name
		orig_date = str(sub_inv.posting_date)

		# 1. Fetch submitted invoice
		data = get_submitted_invoice(inv_no)
		self.assertEqual(data["name"], inv_no)
		self.assertEqual(data["posting_date"], orig_date)

		# 2. Modify to new date
		target_date = "2026-08-30" if orig_date != "2026-08-30" else "2026-08-28"
		res = modify_submitted_bill_date(inv_no, target_date, doctype="Sales Invoice")
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["new_date"], target_date)

		# Verify in DB
		updated_date = str(frappe.db.get_value("Sales Invoice", inv_no, "posting_date"))
		self.assertEqual(updated_date, target_date)

		# Verify in GL Entry if entries exist
		gl_dates = frappe.db.sql(
			"SELECT DISTINCT posting_date FROM `tabGL Entry` WHERE voucher_type='Sales Invoice' AND voucher_no=%s",
			inv_no,
			pluck=True,
		)
		for gld in gl_dates:
			self.assertEqual(str(gld), target_date)

		# 3. Restore original date
		res_restore = modify_submitted_bill_date(inv_no, orig_date, doctype="Sales Invoice")
		self.assertEqual(res_restore["status"], "success")
		restored_date = str(frappe.db.get_value("Sales Invoice", inv_no, "posting_date"))
		self.assertEqual(restored_date, orig_date)
