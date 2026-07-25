import os
import json
import hmac
import hashlib
from datetime import datetime
import frappe

LICENSE_SECRET = "ssplbilling_secure_license_key_2026_santhosh"

def calculate_signature(customer_name, expiry_date, features):
	sorted_features = sorted(features)
	message = f"{customer_name}|{expiry_date}|{','.join(sorted_features)}"
	return hmac.new(
		LICENSE_SECRET.encode("utf-8"),
		message.encode("utf-8"),
		hashlib.sha256
	).hexdigest()

@frappe.whitelist(allow_guest=True)
def get_license_status():
	"""Reads license.json from site directory, verifies signature & expiry, and returns status."""
	# Location: sites/<site>/license.json
	license_path = frappe.get_site_path("license.json")
	
	if not os.path.exists(license_path):
		# Also fallback to private files in case they upload it via File Manager
		license_path = frappe.get_site_path("private", "files", "license.json")

	if not os.path.exists(license_path):
		return {
			"valid": False,
			"message": "License file not found on server",
			"customer_name": "",
			"expiry_date": "",
			"features": [],
			"days_remaining": 0
		}

	try:
		with open(license_path, "r") as f:
			data = json.load(f)
	except Exception as e:
		return {
			"valid": False,
			"message": f"Failed to parse license file: {str(e)}",
			"customer_name": "",
			"expiry_date": "",
			"features": [],
			"days_remaining": 0
		}

	customer_name = data.get("customer_name")
	expiry_date = data.get("expiry_date")
	features = data.get("features", [])
	signature = data.get("signature")

	if not customer_name or not expiry_date or not signature:
		return {
			"valid": False,
			"message": "Invalid license file format (missing fields)",
			"customer_name": "",
			"expiry_date": "",
			"features": [],
			"days_remaining": 0
		}

	# Verify signature
	expected_sig = calculate_signature(customer_name, expiry_date, features)
	if not hmac.compare_digest(signature, expected_sig):
		return {
			"valid": False,
			"message": "License signature verification failed (tampered)",
			"customer_name": customer_name,
			"expiry_date": expiry_date,
			"features": features,
			"days_remaining": 0
		}

	# Check expiration
	try:
		expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d").date()
	except ValueError:
		return {
			"valid": False,
			"message": "Invalid date format in license. Expected YYYY-MM-DD.",
			"customer_name": customer_name,
			"expiry_date": expiry_date,
			"features": features,
			"days_remaining": 0
		}

	today = datetime.now().date()
	days_remaining = (expiry_dt - today).days

	if days_remaining < 0:
		return {
			"valid": False,
			"message": "License has expired",
			"customer_name": customer_name,
			"expiry_date": expiry_date,
			"features": features,
			"days_remaining": days_remaining
		}

	return {
		"valid": True,
		"message": "License is active",
		"customer_name": customer_name,
		"expiry_date": expiry_date,
		"features": features,
		"days_remaining": days_remaining
	}

@frappe.whitelist()
def generate_license(customer_name, expiry_date, features):
	"""Generates a signed license JSON payload. Restricted to Administrator."""
	if frappe.session.user != "Administrator":
		frappe.throw("Only Administrator can generate licenses")
	
	if isinstance(features, str):
		features = json.loads(features)

	signature = calculate_signature(customer_name, expiry_date, features)
	return {
		"customer_name": customer_name,
		"expiry_date": expiry_date,
		"features": features,
		"signature": signature
	}
