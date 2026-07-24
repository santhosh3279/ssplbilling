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

	def test_resolve_target_account(self):
		from ssplbilling.api.automatic_entries_api import resolve_target_account
		
		# Test direct name matching (always works regardless of whitelist)
		res = resolve_target_account("Cash - SSPL", set(), "Sundaram And Sons Private Limited 2")
		self.assertEqual(res, "Cash - NCK")
		
		frappe.db.begin()
		try:
			# Create a temporary unique source account in SSPL
			src_acc = frappe.new_doc("Account")
			src_acc.account_name = "Temp Test Acc Whitelist"
			src_acc.company = "Sundaram And Sons Private Limited"
			src_acc.parent_account = "Cash In Hand - SSPL"
			src_acc.account_type = "Cash"
			src_acc.root_type = "Asset"
			src_acc.report_type = "Balance Sheet"
			src_acc.is_group = 0
			src_acc.insert()
			
			# If it's not whitelisted, resolve_target_account should not auto-create it
			res_not_allowed = resolve_target_account(src_acc.name, set(), "Sundaram And Sons Private Limited 2")
			self.assertNotEqual(res_not_allowed, "Temp Test Acc Whitelist - NCK")
			
			# If it is whitelisted, it should be auto-created
			res_allowed = resolve_target_account(src_acc.name, {src_acc.name}, "Sundaram And Sons Private Limited 2")
			self.assertEqual(res_allowed, "Temp Test Acc Whitelist - NCK")
			self.assertTrue(frappe.db.exists("Account", "Temp Test Acc Whitelist - NCK"))
		finally:
			frappe.db.rollback()

	def test_create_mirror_payment_entry_allowed(self):
		from ssplbilling.api.automatic_entries_api import _create_mirror_payment_entry
		
		msi = frappe.new_doc("Sales Invoice")
		msi.company = "Sundaram And Sons Private Limited 2"
		msi.customer = "Test Customer"
		msi.posting_date = "2026-07-18"
		msi.debit_to = "Debtors - NCK"
		
		# If the payment account is not whitelisted, it must return None
		res_not_allowed = _create_mirror_payment_entry(msi, 100.0, "Cash - SSPL", set())
		self.assertIsNone(res_not_allowed)

	def test_create_mirror_invoice_for_gst_conversion_payments(self):
		from ssplbilling.api.automatic_entries_api import create_mirror_invoice_for_gst_conversion
		
		# Set up a temporary Sales Invoice with a Payment Entry
		frappe.db.begin()
		try:
			# Create a Sales Invoice in main company
			si = frappe.new_doc("Sales Invoice")
			si.company = "Sundaram And Sons Private Limited"
			si.customer = "Test Customer"
			si.posting_date = frappe.utils.today()
			si.debit_to = "Debtors - SSPL"
			# Add an item
			si.append("items", {
				"item_code": "Test Item",
				"qty": 1,
				"rate": 100.0,
				"warehouse": "Finished Goods - SSPL",
				"income_account": "Sales - SSPL",
				"cost_center": "Main - SSPL"
			})
			si.save()
			si.submit()
			
			# Create a Payment Entry for it
			pe = frappe.new_doc("Payment Entry")
			pe.payment_type = "Receive"
			pe.company = "Sundaram And Sons Private Limited"
			pe.posting_date = frappe.utils.today()
			pe.party_type = "Customer"
			pe.party = "Test Customer"
			pe.paid_from = "Debtors - SSPL"
			pe.paid_to = "Cash - SSPL"
			pe.paid_amount = 100.0
			pe.received_amount = 100.0
			pe.append("references", {
				"reference_doctype": "Sales Invoice",
				"reference_name": si.name,
				"allocated_amount": 100.0
			})
			pe.save()
			pe.submit()
			
			# Set up Automatic Entries settings
			ae = frappe.new_doc("Automatic Entries")
			ae.alternative_company = "Sundaram And Sons Private Limited 2"
			ae.warehouse = "Finished Goods - NCK"
			ae.append("accounts", {
				"source_account": "Cash - SSPL",
				"target_account": "Cash - NCK"
			})
			
			# Trigger mirroring
			msi = create_mirror_invoice_for_gst_conversion(si, ae, submit=True)
			
			# Verify mirror invoice was created
			self.assertTrue(frappe.db.exists("Sales Invoice", f"{si.name}/"))
			
			# Verify the mirror Payment Entry was created and submitted
			mirror_pe_name = f"{pe.name}/"
			self.assertTrue(frappe.db.exists("Payment Entry", mirror_pe_name))
			mirror_pe = frappe.get_doc("Payment Entry", mirror_pe_name)
			self.assertEqual(mirror_pe.company, "Sundaram And Sons Private Limited 2")
			self.assertEqual(mirror_pe.docstatus, 1)
			self.assertEqual(mirror_pe.paid_amount, 100.0)
			
		finally:
			frappe.db.rollback()
