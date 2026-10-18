# Copyright (c) 2026, SSPL and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from ssplbilling.api.modify_submitted_api import (
	get_submitted_invoice,
	modify_submitted_bill_date,
	rename_submitted_bill,
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

	def test_rename_mirrored_purchase_invoice(self):
		"""Renaming a mirrored bill moves its ledgers and keeps both custom_mirrored links."""
		pair = frappe.db.sql(
			"""SELECT a.name AS mirror, b.name AS source FROM `tabPurchase Invoice` a
			   JOIN `tabPurchase Invoice` b ON b.name = a.custom_mirrored AND b.custom_mirrored = a.name
			   WHERE a.docstatus = 1 AND b.docstatus = 1 AND a.name NOT LIKE %s LIMIT 1""",
			("%/",),
			as_dict=True,
		)
		if not pair:
			return
		old, source = pair[0].mirror, pair[0].source
		series = frappe.db.get_value("Purchase Invoice", old, "naming_series")
		from ssplbilling.api.modify_submitted_api import _next_series_name

		new = _next_series_name("Purchase Invoice", series)
		res = rename_submitted_bill(old, new, doctype="Purchase Invoice")
		self.assertEqual(res["new_name"], new)
		self.assertFalse(frappe.db.exists("Purchase Invoice", old))
		self.assertEqual(frappe.db.get_value("Purchase Invoice", source, "custom_mirrored"), new)
		self.assertEqual(frappe.db.get_value("Purchase Invoice", new, "custom_mirrored"), source)
		self.assertEqual(frappe.db.get_value("Purchase Invoice", new, "naming_series"), series)
		for ledger in ("GL Entry", "Payment Ledger Entry", "Stock Ledger Entry"):
			self.assertFalse(frappe.db.exists(ledger, {"voucher_type": "Purchase Invoice", "voucher_no": old}))
		self.assertTrue(frappe.db.exists("GL Entry", {"voucher_type": "Purchase Invoice", "voucher_no": new}))
		frappe.db.rollback()

	def test_rename_rejects_unknown_series(self):
		sub = frappe.db.get_value("Purchase Invoice", {"docstatus": 1}, "name")
		if not sub:
			return
		with self.assertRaises(frappe.ValidationError):
			rename_submitted_bill(sub, "ZZ-NO-SERIES-1", doctype="Purchase Invoice")

	def test_rename_treats_slash_as_distinct_number(self):
		"""A plain number is free even when its slashed twin exists, and vice versa."""
		pair = frappe.db.sql(
			"""SELECT a.name AS slashed, b.name AS plain FROM `tabPurchase Invoice` a
			   JOIN `tabPurchase Invoice` b ON b.name = a.custom_mirrored
			   WHERE a.docstatus = 1 AND b.docstatus = 1 AND a.name LIKE %s LIMIT 1""",
			("%/",),
			as_dict=True,
		)
		if not pair:
			return
		slashed, plain = pair[0].slashed, pair[0].plain
		twin_free = slashed[:-1]
		if frappe.db.exists("Purchase Invoice", twin_free):
			return
		res = rename_submitted_bill(plain, twin_free, doctype="Purchase Invoice")
		self.assertEqual(res["new_name"], twin_free)
		self.assertTrue(frappe.db.exists("Purchase Invoice", slashed))
		self.assertEqual(frappe.db.get_value("Purchase Invoice", slashed, "custom_mirrored"), twin_free)
		frappe.db.rollback()
