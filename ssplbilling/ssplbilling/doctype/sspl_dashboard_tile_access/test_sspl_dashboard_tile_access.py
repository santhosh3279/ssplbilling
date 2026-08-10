# Copyright (c) 2026, SSPL and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from ssplbilling.api.license_api import get_license_status


class TestSSPLDashboardTileAccess(IntegrationTestCase):
	def test_license_bypass_on_dev_server(self):
		# Verify that get_license_status is bypassed in developer_mode
		original_developer_mode = frappe.conf.developer_mode
		try:
			frappe.conf.developer_mode = True
			status = get_license_status()
			self.assertTrue(status.get("valid"))
			self.assertEqual(status.get("message"), "Bypassed on Dev Server")
			self.assertIn("*", status.get("features"))
			self.assertIsNone(status.get("max_tabs"))
		finally:
			frappe.conf.developer_mode = original_developer_mode

	def test_dashboard_tiles_synced(self):
		# Verify that hrms and employee are present in SSPL Dashboard Tile
		self.assertTrue(frappe.db.exists("SSPL Dashboard Tile", "hrms"))
		self.assertTrue(frappe.db.exists("SSPL Dashboard Tile", "employee"))


def test_run():
	import frappe
	from ssplbilling.api.license_api import get_license_status
	# Test license bypass
	original_developer_mode = frappe.conf.developer_mode
	try:
		frappe.conf.developer_mode = True
		status = get_license_status()
		assert status.get("valid") is True, "License should be valid"
		assert status.get("message") == "Bypassed on Dev Server", f"Expected Bypassed message, got {status.get('message')}"
		assert "*" in status.get("features"), "Should have wildcard feature"
		assert status.get("max_tabs") is None, "max_tabs should be None"
		print("License bypass test passed successfully!")
	finally:
		frappe.conf.developer_mode = original_developer_mode

	# Test dashboard tiles synced
	assert frappe.db.exists("SSPL Dashboard Tile", "hrms"), "hrms tile not found"
	assert frappe.db.exists("SSPL Dashboard Tile", "employee"), "employee tile not found"
	print("Dashboard tiles synced test passed successfully!")
