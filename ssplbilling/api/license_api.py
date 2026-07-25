import os
import json
import base64
from datetime import datetime
import frappe
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Public key only — verification cannot forge a license. Signing key lives in the
# separate private license-generator repo and never touches this codebase.
LICENSE_PUBLIC_KEY_B64 = "NCcdnL9384366XVtCpkpqq39XtZU7t/Fy+BYWt/+RBM="


def _build_message(customer_name, expiry_date, features):
	sorted_features = sorted(features)
	return f"{customer_name}|{expiry_date}|{','.join(sorted_features)}".encode("utf-8")


def _verify_signature(customer_name, expiry_date, features, signature_b64):
	try:
		public_key = ed25519.Ed25519PublicKey.from_public_bytes(
			base64.b64decode(LICENSE_PUBLIC_KEY_B64)
		)
		signature = base64.b64decode(signature_b64)
		message = _build_message(customer_name, expiry_date, features)
		public_key.verify(signature, message)
		return True
	except (InvalidSignature, ValueError, TypeError):
		return False


@frappe.whitelist(allow_guest=True)
def get_license_status():
	"""Reads license.json from site directory, verifies Ed25519 signature & expiry, and returns status."""
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
	if not _verify_signature(customer_name, expiry_date, features, signature):
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
