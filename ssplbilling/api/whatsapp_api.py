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

Chat (WhatsApp Chat page): list_chats() / get_messages() read the linked account's chats live from
the gateway; send_chat_message() / send_chat_file() reply in them. Open to System Managers and to
users whose SSPL Dashboard Tile Access grants the whatsapp-chat tile.
"""

import base64
import binascii
from urllib.parse import quote

import frappe
import requests
from frappe import _
from frappe.utils import now_datetime

from ssplbilling.api.dashboard_api import get_allowed_tiles
from ssplbilling.api.print_preview_api import (
	get_party_link,
	get_party_whatsapp,
	normalize_whatsapp_number,
)

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


def _require_desk_user():
	"""Portal (catalogue) logins can read their own bills but must not drive the business number."""
	if (
		frappe.session.user == "Guest"
		or frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User"
	):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


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


# POST because it mirrors the gateway's status onto the settings, and Frappe only commits writes
# made during unsafe requests
@frappe.whitelist(methods=["POST"])
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
def send_document(doctype, document_name, pdf_base64, filename, caption=""):
	"""Send a bill PDF the print dialog already rendered to the party's WhatsApp.

	The number is looked up here from the bill's party, never taken from the caller, so the
	business number can only ever message the party a bill belongs to.
	"""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	if not frappe.utils.cint(frappe.db.get_single_value(SETTINGS_DOCTYPE, "enabled")):
		frappe.throw(_("Sending bills via OpenWA is turned off"))

	party_doctype, party = get_party_link(doctype, document_name)
	phone = get_party_whatsapp(party_doctype, party) if party else ""
	if not phone:
		frappe.throw(_("No WhatsApp number on file for this party"))

	try:
		head = base64.b64decode(pdf_base64[:8], validate=True)
	except (binascii.Error, TypeError):
		head = b""
	if not head.startswith(b"%PDF"):
		frappe.throw(_("The bill is not a PDF"))

	body = {
		"base64": pdf_base64,
		"mimetype": "application/pdf",
		"filename": filename,
		"caption": (caption or "")[:1024],
	}
	return _send(phone, "Document", "send-document", body, caption, reference=(doctype, document_name))


# ── Chat ─────────────────────────────────────────────────────────────────────────────────────────

CHAT_TILE = "whatsapp-chat"
# Status, channel and broadcast "chats" are not conversations anyone replies in
CHAT_KINDS = ("individual", "group")
# send-image shows a picture inline; anything else goes as a document
IMAGE_MIMETYPES = ("image/jpeg", "image/png", "image/webp")


def _require_chat_user():
	"""The chat reads every conversation on the business number, so it needs an explicit grant."""
	_require_desk_user()
	if "System Manager" in frappe.get_roles():
		return
	if CHAT_TILE not in (get_allowed_tiles().get("tiles") or []):
		frappe.throw(_("WhatsApp Chat is not enabled for you"), frappe.PermissionError)


def _chat_settings():
	settings = _settings()
	if not settings.session_id:
		frappe.throw(_("No WhatsApp number is linked. Open the WhatsApp Link page first."))
	return settings


def _chat_path(settings, chat_id, suffix=""):
	return f"/sessions/{settings.session_id}/messages/{quote(chat_id, safe='@.')}{suffix}"


def _media_info(media):
	if not media:
		return None
	return {"mimetype": media.get("mimetype") or "", "filename": media.get("filename") or ""}


def _live_message(m):
	return {
		"id": m.get("id"),
		"body": m.get("body") or "",
		"type": m.get("type") or "text",
		"from_me": bool(m.get("fromMe")),
		"timestamp": m.get("timestamp") or 0,
		"author": m.get("author") if m.get("isGroup") else "",
		"media": _media_info(m.get("media")),
		"status": "",
	}


def _stored_message(m):
	return {
		"id": m.get("waMessageId") or m.get("id"),
		"body": m.get("body") or "",
		"type": m.get("type") or "text",
		"from_me": m.get("direction") == "outgoing",
		"timestamp": m.get("timestamp") or 0,
		"author": m.get("chatName") or m.get("author") or "",
		"media": _media_info((m.get("metadata") or {}).get("media")),
		"status": m.get("status") or "",
	}


@frappe.whitelist()
def list_chats(limit=200):
	_require_chat_user()

	def run():
		settings = _chat_settings()
		chats = _call(
			settings,
			"GET",
			f"/sessions/{settings.session_id}/chats",
			params={"limit": min(frappe.utils.cint(limit) or 200, 1000)},
		)
		return [
			{
				"id": c.get("id"),
				"name": c.get("name") or c.get("id", "").split("@")[0],
				"is_group": c.get("kind") == "group",
				"unread": c.get("unreadCount") or 0,
				"timestamp": c.get("timestamp") or 0,
				"last_message": c.get("lastMessage") or "",
				"last_type": c.get("lastMessageType") or "",
				"pinned": bool(c.get("pinned")),
			}
			for c in chats
			if (c.get("kind") or "individual") in CHAT_KINDS and not c.get("archived")
		]

	return _guarded(run)


@frappe.whitelist()
def get_messages(chat_id, limit=50):
	"""Newest `limit` messages of a chat, oldest first."""
	_require_chat_user()
	limit = min(frappe.utils.cint(limit) or 50, 100)

	def run():
		settings = _chat_settings()
		try:
			history = _call(
				settings, "GET", _chat_path(settings, chat_id, "/history"), params={"limit": limit}
			)
			return [_live_message(m) for m in history]
		except OpenWAError as e:
			# Only whatsapp-web.js reads history live; Baileys answers 501, so use what OpenWA stored
			if e.status_code != 501:
				raise
		stored = _call(
			settings,
			"GET",
			f"/sessions/{settings.session_id}/messages",
			params={"chatId": chat_id, "limit": limit, "orderBy": "timestamp", "inlineMedia": "false"},
		)
		return [_stored_message(m) for m in reversed(stored.get("messages") or [])]

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def mark_chat_read(chat_id):
	_require_chat_user()
	settings = _chat_settings()
	try:
		_call(settings, "POST", f"/sessions/{settings.session_id}/chats/read", json={"chatId": chat_id})
	except OpenWAError:
		# Unread counts are cosmetic; a failed receipt must not break opening the chat
		pass
	return True


@frappe.whitelist()
def resolve_chat(phone):
	"""Chat id for a new conversation with a number, or an error when it is not on WhatsApp."""
	_require_chat_user()
	return _guarded(lambda: dict(zip(("phone", "chat_id"), _chat_id(_chat_settings(), phone), strict=True)))


def _chat_send(chat_id, message_type, route, body, content):
	settings = _chat_settings()
	phone = chat_id.split("@")[0]
	try:
		result = _call(settings, "POST", f"/sessions/{settings.session_id}/messages/{route}", json=body)
	except OpenWAError as e:
		_log(phone, message_type, content, "Failed", error=str(e))
		frappe.db.commit()
		frappe.throw(str(e), title=_("WhatsApp send failed"))
	_log(phone, message_type, content, "Sent", message_id=result.get("messageId"))
	return {"message_id": result.get("messageId"), "timestamp": result.get("timestamp")}


@frappe.whitelist(methods=["POST"])
def send_chat_message(chat_id, text):
	_require_chat_user()
	text = (text or "").strip()
	if not text:
		frappe.throw(_("Type a message"))
	return _chat_send(chat_id, "Text", "send-text", {"chatId": chat_id, "text": text[:4096]}, text)


@frappe.whitelist(methods=["POST"])
def send_chat_file(chat_id, file_base64, mimetype, filename, caption=""):
	_require_chat_user()
	is_image = mimetype in IMAGE_MIMETYPES
	body = {
		"chatId": chat_id,
		"base64": file_base64,
		"mimetype": mimetype or "application/octet-stream",
		"filename": filename,
		"caption": (caption or "")[:1024],
	}
	return _chat_send(
		chat_id,
		"Image" if is_image else "Document",
		"send-image" if is_image else "send-document",
		body,
		caption or filename,
	)
