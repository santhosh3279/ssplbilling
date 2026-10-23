"""OpenWA (self-hosted WhatsApp HTTP gateway) integration.

OpenWA runs beside the bench (Docker, port 2785) and holds one linked WhatsApp session. ERPNext
only ever talks to it from here, so the API key never reaches a browser.

Linking (WhatsApp Link page, System Manager): connect() creates the named session on the gateway
if it is missing and starts it -> get_status() polls and returns the QR while it is "qr_ready" ->
the phone scans it under Linked Devices -> status turns "ready". disconnect() stops the engine but
keeps the pairing; logout() unlinks the device, so the next connect needs a fresh scan.

Sending: send_document() takes the bill PDF the print dialog already rendered and hands it to
OpenWA's send-document route. Every send is recorded in SSPL WhatsApp Log. OpenWA answers 201
once it has accepted the message, which is not a delivery receipt.
"""

import frappe
import requests
from frappe import _
from frappe.utils import now_datetime

from ssplbilling.api.print_preview_api import normalize_whatsapp_number

SETTINGS_DOCTYPE = "SSPL WhatsApp Settings"
LOG_DOCTYPE = "SSPL WhatsApp Log"

REQUEST_TIMEOUT = 20
# A slow engine launch answers 504 after ~30s, so the start call must outwait it
START_TIMEOUT = 60
# The print dialog asks on open; a dead gateway must not hold the dialog up
STATE_TIMEOUT = 3

# OpenWA wire values for session status (lowercase)
READY = "ready"
QR_READY = "qr_ready"


class OpenWAError(frappe.ValidationError):
	def __init__(self, status_code, message, code=None):
		super().__init__(message)
		self.status_code = status_code
		self.code = code


def _require_manager():
	frappe.only_for("System Manager")


def _settings():
	return frappe.get_single(SETTINGS_DOCTYPE)


def _error_message(res):
	"""OpenWA errors are NestJS-shaped; `message` is a string or a list of field errors."""
	try:
		body = res.json()
	except ValueError:
		return (res.text or res.reason or "").strip()[:300], None
	message = body.get("message") if isinstance(body, dict) else None
	if isinstance(message, list):
		message = "; ".join(str(m) for m in message)
	return str(message or res.reason), body.get("code") if isinstance(body, dict) else None


def _call(settings, method, path, json=None, params=None, timeout=REQUEST_TIMEOUT):
	base_url = (settings.base_url or "").rstrip("/")
	api_key = settings.get_password("api_key", raise_exception=False)
	if not base_url or not api_key:
		frappe.throw(_("Set the OpenWA Gateway URL and API Key first"))

	try:
		res = requests.request(
			method,
			f"{base_url}/api{path}",
			headers={"X-API-Key": api_key},
			json=json,
			params=params,
			timeout=timeout,
		)
	except requests.RequestException as e:
		raise OpenWAError(0, _("Cannot reach OpenWA at {0}: {1}").format(base_url, e)) from e

	if not res.ok:
		message, code = _error_message(res)
		if res.status_code == 401:
			message = _("OpenWA rejected the API key")
		raise OpenWAError(res.status_code, message, code)

	try:
		return res.json()
	except ValueError:
		return {}


def _store_session(session):
	"""Mirror the gateway's view of the session onto the settings record."""
	frappe.db.set_single_value(
		SETTINGS_DOCTYPE,
		{
			"session_id": session.get("id") or "",
			"status": session.get("status") or "",
			"phone": session.get("phone") or "",
			"push_name": session.get("pushName") or "",
			"last_checked": now_datetime(),
		},
	)


def _fetch_session(settings):
	"""The configured session as OpenWA reports it, or None when it does not exist there."""
	if settings.session_id:
		try:
			return _call(settings, "GET", f"/sessions/{settings.session_id}")
		except OpenWAError as e:
			if e.status_code != 404:
				raise

	# Stored id missing or stale (session deleted on the dashboard): look it up by name
	found = _call(settings, "GET", "/sessions", params={"name": settings.session_name})
	return found[0] if found else None


def _status_payload(settings, session):
	payload = {
		"status": session.get("status") if session else "not_created",
		"session_id": (session or {}).get("id") or "",
		"phone": (session or {}).get("phone") or "",
		"push_name": (session or {}).get("pushName") or "",
		"engine_loaded": bool((session or {}).get("engineLoaded")),
		"last_error": (session or {}).get("lastError") or "",
		"restriction": (session or {}).get("restriction"),
		"qr": "",
	}

	if session and session.get("status") == QR_READY:
		try:
			payload["qr"] = _call(settings, "GET", f"/sessions/{session['id']}/qr").get("qrCode") or ""
		except OpenWAError as e:
			# 400 = the QR rotated out or the scan just landed; the next poll catches up
			if e.status_code != 400:
				raise
	return payload


def _guarded(fn):
	"""Turn gateway failures into a clean message for the page."""
	try:
		return fn()
	except OpenWAError as e:
		frappe.throw(str(e), title=_("OpenWA"))


@frappe.whitelist()
def get_settings():
	_require_manager()
	settings = _settings()
	return {
		"enabled": settings.enabled,
		"base_url": settings.base_url,
		"session_name": settings.session_name,
		# The key itself never leaves the server
		"has_api_key": bool(settings.get_password("api_key", raise_exception=False)),
		"session_id": settings.session_id,
		"status": settings.status,
		"phone": settings.phone,
		"push_name": settings.push_name,
		"last_checked": settings.last_checked,
	}


@frappe.whitelist(methods=["POST"])
def save_settings(base_url, session_name, enabled=0, api_key=None):
	_require_manager()
	settings = _settings()
	settings.base_url = base_url
	settings.enabled = 1 if frappe.utils.cint(enabled) else 0
	if session_name != settings.session_name:
		# A different name is a different WhatsApp link on the gateway
		settings.session_name = session_name
		settings.session_id = ""
		settings.status = ""
		settings.phone = ""
		settings.push_name = ""
	if api_key:
		settings.api_key = api_key
	settings.save()
	return get_settings()


@frappe.whitelist()
def get_status():
	_require_manager()

	def run():
		settings = _settings()
		session = _fetch_session(settings)
		if session:
			_store_session(session)
		return _status_payload(settings, session)

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def connect():
	"""Create the session on the gateway if needed and start it; the QR follows via get_status()."""
	_require_manager()

	def run():
		settings = _settings()
		session = _fetch_session(settings)
		if not session:
			session = _call(settings, "POST", "/sessions", json={"name": settings.session_name})

		# engineLoaded, not status: "disconnected" also covers an engine still backing off
		if not session.get("engineLoaded"):
			try:
				session = _call(settings, "POST", f"/sessions/{session['id']}/start", timeout=START_TIMEOUT)
			except OpenWAError as e:
				# 400 = already started / starting, which is what we wanted
				if e.status_code != 400 or "maximum concurrent" in str(e).lower():
					raise
				session = _call(settings, "GET", f"/sessions/{session['id']}")

		_store_session(session)
		return _status_payload(settings, session)

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def disconnect():
	"""Stop the engine. The pairing is kept, so connect() resumes without a scan."""
	_require_manager()

	def run():
		settings = _settings()
		session = _fetch_session(settings)
		if session and session.get("engineLoaded"):
			session = _call(settings, "POST", f"/sessions/{session['id']}/stop")
		if session:
			_store_session(session)
		return _status_payload(settings, session)

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def logout():
	"""Unlink this device from the WhatsApp account. The next connect needs a fresh QR scan."""
	_require_manager()

	def run():
		settings = _settings()
		session = _fetch_session(settings)
		if not session:
			return _status_payload(settings, None)
		if not session.get("engineLoaded"):
			frappe.throw(_("Connect the session first — WhatsApp can only unlink a running session"))
		try:
			_call(settings, "POST", f"/sessions/{session['id']}/logout", timeout=START_TIMEOUT)
		except OpenWAError as e:
			# Torn down locally but WhatsApp did not confirm; the phone may still list the device
			if e.code != "SESSION_LOGOUT_INCOMPLETE":
				raise
			frappe.msgprint(
				_(
					"Logged out here, but WhatsApp did not confirm. Remove the device from Linked Devices on the phone."
				)
			)
		session = _call(settings, "GET", f"/sessions/{session['id']}")
		_store_session(session)
		return _status_payload(settings, session)

	return _guarded(run)


@frappe.whitelist()
def get_gateway_state():
	"""Whether bills can go out through OpenWA right now. Called by the print dialog for every user."""
	settings = _settings()
	if not settings.enabled or not settings.session_id:
		return {"ready": False}
	try:
		session = _call(settings, "GET", f"/sessions/{settings.session_id}", timeout=STATE_TIMEOUT)
	except frappe.ValidationError:
		return {"ready": False}
	return {"ready": session.get("status") == READY}


def _chat_id(settings, phone):
	number = normalize_whatsapp_number(phone)
	if not number:
		frappe.throw(_("No WhatsApp number"))
	check = _call(settings, "GET", f"/sessions/{settings.session_id}/contacts/check/{number}")
	if not check.get("exists"):
		frappe.throw(_("{0} is not on WhatsApp").format(number))
	return number, check.get("whatsappId") or f"{number}@c.us"


def _log(phone, message_type, content, status, message_id=None, error=None, reference=None):
	reference_doctype, reference_name = reference or (None, None)
	frappe.get_doc(
		{
			"doctype": LOG_DOCTYPE,
			"phone": phone,
			"message_type": message_type,
			"content": content,
			"status": status,
			"message_id": message_id,
			"error": error,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	).insert(ignore_permissions=True)


def _send(phone, message_type, route, body, content, reference=None):
	settings = _settings()
	if not settings.session_id:
		frappe.throw(_("No WhatsApp session is linked. Open the WhatsApp Link page first."))

	number = normalize_whatsapp_number(phone)
	try:
		number, chat_id = _chat_id(settings, phone)
		result = _call(
			settings,
			"POST",
			f"/sessions/{settings.session_id}/messages/{route}",
			json={"chatId": chat_id, **body},
		)
	except frappe.ValidationError as e:
		_log(number, message_type, content, "Failed", error=str(e), reference=reference)
		# The failure is worth keeping even though the request is about to roll back
		frappe.db.commit()
		frappe.throw(str(e), title=_("WhatsApp send failed"))

	_log(number, message_type, content, "Sent", message_id=result.get("messageId"), reference=reference)
	return {"phone": number, "message_id": result.get("messageId")}


@frappe.whitelist(methods=["POST"])
def send_test(phone, text):
	_require_manager()
	return _send(phone, "Text", "send-text", {"text": text}, text)


@frappe.whitelist(methods=["POST"])
def send_document(doctype, document_name, phone, base64, filename, caption=""):
	"""Send a bill PDF the print dialog already rendered to the party's WhatsApp."""
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	if not frappe.utils.cint(frappe.db.get_single_value(SETTINGS_DOCTYPE, "enabled")):
		frappe.throw(_("Sending bills via OpenWA is turned off"))

	body = {
		"base64": base64,
		"mimetype": "application/pdf",
		"filename": filename,
		"caption": (caption or "")[:1024],
	}
	return _send(phone, "Document", "send-document", body, caption, reference=(doctype, document_name))
