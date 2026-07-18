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
