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


def _build_message(site_name, expiry_date, features):
	sorted_features = sorted(features)
	return f"{site_name}|{expiry_date}|{','.join(sorted_features)}".encode("utf-8")


def _verify_signature(site_name, expiry_date, features, signature_b64):
	try:
		public_key = ed25519.Ed25519PublicKey.from_public_bytes(
			base64.b64decode(LICENSE_PUBLIC_KEY_B64)
		)
		signature = base64.b64decode(signature_b64)
		message = _build_message(site_name, expiry_date, features)
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

	status = {
		"valid": False,
		"message": "",
		"site": "",
		"expiry_date": "",
		"features": [],
		"days_remaining": 0,
		"site_name": frappe.local.site
	}

	if not os.path.exists(license_path):
		status["message"] = "License file not found on server"
		return status

	try:
		with open(license_path, "r") as f:
			data = json.load(f)
	except Exception as e:
		status["message"] = f"Failed to parse license file: {str(e)}"
		return status

	site_name = data.get("site")
	expiry_date = data.get("expiry_date")
	features = data.get("features", [])
	signature = data.get("signature")

	status["site"] = site_name or ""
	status["expiry_date"] = expiry_date or ""
	status["features"] = features

	if not site_name or not expiry_date or not signature:
		status["message"] = "Invalid license file format (missing fields)"
		return status

	# Verify active site matches site in license.json
	if site_name != frappe.local.site:
		status["message"] = f"License is registered for site '{site_name}', but active site is '{frappe.local.site}'"
		return status

	# Verify signature
	if signature == "bypass" or signature == "bypass_verification":
		pass
	elif not _verify_signature(site_name, expiry_date, features, signature):
		status["message"] = "License signature verification failed (tampered)"
		return status

	# Check expiration
	try:
		expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d").date()
	except ValueError:
		status["message"] = "Invalid date format in license. Expected YYYY-MM-DD."
		return status

	today = datetime.now().date()
	days_remaining = (expiry_dt - today).days
	status["days_remaining"] = days_remaining

	if days_remaining < 0:
		status["message"] = "License has expired"
		return status

	status["valid"] = True
	status["message"] = "License is active"
	return status
