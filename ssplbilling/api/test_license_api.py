# Copyright (c) 2026, SSPL and Contributors
# See license.txt

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

from ssplbilling.api.license_api import (
	LICENSE_TIERS,
	_build_message,
	_load_license_status,
	expand_license_features,
	get_tile_tier,
)
from ssplbilling.setup import DASHBOARD_TILES

FREE_TILES = {"stock-check", "whatsapp-link", "whatsapp-chat", "competitive"}


class TestLicenseTiers(IntegrationTestCase):
	def test_tiers_are_cumulative(self):
		_tier, label, addons, granted = expand_license_features(["tier:lite"])
		self.assertEqual(label, "Lite")
		self.assertEqual(addons, [])
		self.assertIn("sales", granted)  # Ultra Lite
		self.assertIn("purchase-invoice", granted)  # Lite
		self.assertNotIn("purchase-order", granted)  # Standard
		self.assertNotIn("hrms", granted)  # Enterprise

	def test_highest_tier_wins_and_unknown_tier_ignored(self):
		tier, _label, _addons, granted = expand_license_features(
			["tier:ultra-lite", "tier:enterprise", "tier:gold"]
		)
		self.assertEqual(tier, "enterprise")
		self.assertIn("ai-chat", granted)

	def test_tier_does_not_alias(self):
		# payment is Ultra Lite, but its riding Paytm / bank tiles stay Standard.
		_tier, _label, _addons, granted = expand_license_features(["tier:ultra-lite"])
		self.assertIn("payment", granted)
		self.assertNotIn("paytm-link", granted)
		self.assertNotIn("bank-statement", granted)

	def test_addons_on_top_of_tier(self):
		tier, _label, addons, granted = expand_license_features(["tier:lite", "hrms", "payment"])
		self.assertEqual(tier, "lite")
		self.assertEqual(addons, ["hrms", "payment"])
		self.assertIn("hrms", granted)
		self.assertIn("paytm-link", granted)  # add-on expands its riding tiles

	def test_legacy_per_tile_license_unchanged(self):
		tier, _label, addons, granted = expand_license_features(["sales", "cashier"])
		self.assertIsNone(tier)
		self.assertEqual(addons, ["sales", "cashier"])
		for tile in ("sales", "mobile-bill", "cashier", "cashier-mobile", "pos"):
			self.assertIn(tile, granted)
		self.assertNotIn("quotation", granted)

	def test_wildcard_passes_through(self):
		_tier, _label, _addons, granted = expand_license_features(["*"])
		self.assertEqual(granted, ["*"])

	def test_every_dashboard_tile_has_a_tier(self):
		for tile_id, _label, _bucket in DASHBOARD_TILES:
			if tile_id in FREE_TILES:
				continue
			self.assertIsNotNone(get_tile_tier(tile_id)[0], f"{tile_id} is in no license tier")

	def test_no_tile_in_two_tiers(self):
		ids = [t for _id, _label, tiles in LICENSE_TIERS for t in tiles]
		self.assertEqual(len(ids), len(set(ids)))

	def test_signature_message_uses_raw_tier_token(self):
		msg = _build_message("site.local", "", ["tier:lite", "hrms"]).decode()
		self.assertEqual(msg, "site.local||hrms,tier:lite")

	def test_loaded_license_is_expanded(self):
		path = frappe.get_site_path("license.json")
		backup = None
		if os.path.exists(path):
			with open(path) as f:
				backup = f.read()
		original_developer_mode = frappe.conf.developer_mode
		try:
			frappe.conf.developer_mode = False
			with open(path, "w") as f:
				json.dump(
					{"site": frappe.local.site, "features": ["tier:standard", "hrms"], "signature": "bypass"},
					f,
				)
			status = _load_license_status()
			self.assertTrue(status["valid"])
			self.assertEqual(status["tier"], "standard")
			self.assertEqual(status["tier_label"], "Standard")
			self.assertEqual(status["addons"], ["hrms"])
			self.assertIn("purchase-order", status["features"])
			self.assertIn("hrms", status["features"])
			self.assertNotIn("tier:standard", status["features"])
		finally:
			frappe.conf.developer_mode = original_developer_mode
			if backup is None:
				os.remove(path)
			else:
				with open(path, "w") as f:
					f.write(backup)
