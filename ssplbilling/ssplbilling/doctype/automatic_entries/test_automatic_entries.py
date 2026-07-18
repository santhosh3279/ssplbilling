# Copyright (c) 2026, SSPL and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from ssplbilling.api.automatic_entries_api import should_mirror_sales_invoice
from ssplbilling.api.purchase_mirror_api import should_mirror_purchase_invoice


class TestAutomaticEntries(IntegrationTestCase):
	def test_should_mirror_sales_invoice_with_conversion_series(self):
		ae = frappe.new_doc("Automatic Entries")
		ae.alternative_company = "Alternative Company"
		ae.warehouse = "Alternative Warehouse"
		
		# Append a row to series child table
		ae.append("series", {
			"sales_invoice_series": "SINV-",
			"purchase_invoice_series": "PINV-",
			"conversion_invoice_series": "CONV-",
		})
		
		# Test sales invoice series matching
		self.assertTrue(should_mirror_sales_invoice("SINV-1234", ae))
		
		# Test conversion invoice series matching
		self.assertTrue(should_mirror_sales_invoice("CONV-5678", ae))
		
		# Test non-matching series
		self.assertFalse(should_mirror_sales_invoice("OTHER-9999", ae))

	def test_should_mirror_purchase_invoice(self):
		ae = frappe.new_doc("Automatic Entries")
		ae.alternative_company = "Alternative Company"
		ae.warehouse = "Alternative Warehouse"
		
		# Append a row to series child table
		ae.append("series", {
			"sales_invoice_series": "SINV-",
			"purchase_invoice_series": "PINV-",
			"conversion_invoice_series": "CONV-",
		})
		
		# Test purchase invoice series matching
		self.assertTrue(should_mirror_purchase_invoice("PINV-1234", ae))
		
		# Test non-matching series
		self.assertFalse(should_mirror_purchase_invoice("OTHER-9999", ae))

	def test_ensure_warehouse_in_company(self):
		from ssplbilling.api.automatic_entries_api import ensure_warehouse_in_company
		
		# Test with existing warehouse in target company
		res = ensure_warehouse_in_company("Finished Goods - NCK", "Sundaram And Sons Private Limited 2")
		self.assertEqual(res, "Finished Goods - NCK")

		# Test creating a warehouse in the target company
		frappe.db.begin()
		try:
			if frappe.db.exists("Warehouse", "DAMAGE - NCK"):
				frappe.delete_doc("Warehouse", "DAMAGE - NCK")
				
			target_wh = ensure_warehouse_in_company("DAMAGE - SSPL", "Sundaram And Sons Private Limited 2")
			self.assertEqual(target_wh, "DAMAGE - NCK")
			self.assertTrue(frappe.db.exists("Warehouse", "DAMAGE - NCK"))
		finally:
			frappe.db.rollback()

	def test_ensure_cost_center_in_company(self):
		from ssplbilling.api.automatic_entries_api import ensure_cost_center_in_company
		
		frappe.db.begin()
		try:
			if frappe.db.exists("Cost Center", "NCK - NCK"):
				frappe.delete_doc("Cost Center", "NCK - NCK")
				
			target_cc = ensure_cost_center_in_company("NCK - SSPL", "Sundaram And Sons Private Limited 2")
			self.assertEqual(target_cc, "NCK - NCK")
			self.assertTrue(frappe.db.exists("Cost Center", "NCK - NCK"))
		finally:
			frappe.db.rollback()
