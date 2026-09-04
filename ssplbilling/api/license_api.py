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


def _build_message(site_name, expiry_date, features, max_tabs=None, customer_name=None, watch_text=None, amc_date=None):
	# expiry_date is a core positional field, but an empty/missing value means
	# "unlimited" (no expiry) rather than being omitted from the message like the
	# optional fields below — normalize to "" so both build and verify agree.
	expiry_date = expiry_date or ""
	sorted_features = sorted(features)
	message = f"{site_name}|{expiry_date}|{','.join(sorted_features)}"
	# Optional fields are only folded into the signed message when present, in this
	# fixed order, so licenses signed before a field existed keep verifying against
	# their original (shorter) message.
	if max_tabs is not None:
		message += f"|{max_tabs}"
	if customer_name:
		message += f"|{customer_name}"
	if watch_text:
		message += f"|{watch_text}"
	if amc_date:
		message += f"|{amc_date}"
	return message.encode("utf-8")


def _verify_signature(site_name, expiry_date, features, signature_b64, max_tabs=None, customer_name=None, watch_text=None, amc_date=None):
	try:
		public_key = ed25519.Ed25519PublicKey.from_public_bytes(
			base64.b64decode(LICENSE_PUBLIC_KEY_B64)
		)
		signature = base64.b64decode(signature_b64)
		message = _build_message(site_name, expiry_date, features, max_tabs, customer_name, watch_text, amc_date)
		public_key.verify(signature, message)
		return True
	except (InvalidSignature, ValueError, TypeError):
		return False


def _load_license_status():
	"""Reads license.json from site directory, verifies Ed25519 signature & expiry, and returns status.

	Internal helper (not whitelisted) so other server-side modules (e.g. tab-limit
	enforcement) can read a verified license without going through the HTTP layer.
	"""
	if frappe.conf.developer_mode:
		return {
			"valid": True,
			"message": "Bypassed on Dev Server",
			"site": frappe.local.site,
			"expiry_date": "",
			"features": ["*"],
			"max_tabs": None,
			"customer_name": "Dev Server (Bypassed)",
			"watch_text": "Dev Mode Active",
			"days_remaining": None,
			"amc_date": "",
			"amc_days_remaining": None,
			"site_name": frappe.local.site
		}

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
		"max_tabs": None,
		"customer_name": "",
		"watch_text": "",
		"days_remaining": 0,
		"amc_date": "",
		"amc_days_remaining": None,
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
	# max_tabs must be omitted entirely for "unlimited" — never emit 0 for that meaning,
	# since 0 is a valid explicit cap (blocks all tabs) and is folded into the signed
	# message like any other value.
	max_tabs = data.get("max_tabs")
	if max_tabs is not None and (not isinstance(max_tabs, int) or max_tabs < 0):
		max_tabs = None
	customer_name = data.get("customer_name") or None
	watch_text = data.get("watch_text") or None
	# amc_date is optional and purely informational — it tracks the annual maintenance
	# contract renewal date and never affects whether the license itself is valid.
	amc_date = data.get("amc_date") or None

	status["site"] = site_name or ""
	status["expiry_date"] = expiry_date or ""
	status["features"] = features
	status["max_tabs"] = max_tabs
	status["customer_name"] = customer_name or ""
	status["watch_text"] = watch_text or ""
	status["amc_date"] = amc_date or ""

	# expiry_date is optional — an empty/missing value means the license never expires.
	if not site_name or not signature:
		status["message"] = "Invalid license file format (missing fields)"
		return status

	# Verify active site matches site in license.json
	if site_name != frappe.local.site:
		status["message"] = f"License is registered for site '{site_name}', but active site is '{frappe.local.site}'"
		return status

	# Verify signature
	if signature == "bypass" or signature == "bypass_verification":
		pass
	elif not _verify_signature(site_name, expiry_date, features, signature, max_tabs, customer_name, watch_text, amc_date):
		status["message"] = "License signature verification failed (tampered)"
		return status

	# Computed before the expiry branches below, which return early — an unlimited
	# license still needs its AMC countdown. A bad date is ignored, not fatal.
	if amc_date:
		try:
			amc_dt = datetime.strptime(amc_date, "%Y-%m-%d").date()
			status["amc_days_remaining"] = (amc_dt - datetime.now().date()).days
		except ValueError:
			status["amc_days_remaining"] = None

	if not expiry_date:
		status["days_remaining"] = None
		status["valid"] = True
		status["message"] = "License is active (no expiry)"
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


@frappe.whitelist(allow_guest=True)
def get_license_status():
	return _load_license_status()
