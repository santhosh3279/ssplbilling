import json

import frappe


def execute():
	"""Convert cipher_map from a JSON array to plain text.

	Older builds stored the cipher as '["K","L",...]'. It is now one replacement
	character per digit 0-9, in order ("KLMNOPQRST"). Anything that is already
	plain text, blank, or not a usable 10-entry array is left untouched.
	"""
	value = frappe.db.get_single_value("SSPL Billing Settings", "cipher_map")
	if not value or not value.strip().startswith("["):
		return

	try:
		parsed = json.loads(value)
	except ValueError:
		return

	if not isinstance(parsed, list) or len(parsed) != 10:
		return
	if not all(isinstance(v, str) and len(v) == 1 for v in parsed):
		# Multi-character entries cannot be expressed in the plain-text format;
		# leave them alone so the frontend keeps reading them as legacy JSON.
		return

	frappe.db.set_single_value("SSPL Billing Settings", "cipher_map", "".join(parsed))
