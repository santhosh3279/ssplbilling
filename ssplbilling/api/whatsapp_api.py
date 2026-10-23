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
	DEFAULT_COUNTRY_CODE,
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

# A customer/supplier save waits on this check, so a stalled gateway must give up quickly
SAVE_CHECK_TIMEOUT = 8

# Customer / Supplier `whatsapp_status` values. A number is checked only when an operator acts
# (saves the party, presses Check, or sends it a bill); nothing checks in the background. Once
# Valid it is trusted until a send to it fails or the number is changed.
NOT_CHECKED = "Not Checked"
VALID = "Valid"
INVALID = "Invalid"
STATUS_DOCTYPES = ("Customer", "Supplier")

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


def _whatsapp_id(settings, number, timeout=REQUEST_TIMEOUT):
	"""Canonical chat id when the (normalized) number has a WhatsApp account, else None."""
	check = _call(
		settings, "GET", f"/sessions/{settings.session_id}/contacts/check/{number}", timeout=timeout
	)
	if not check.get("exists"):
		return None
	return check.get("whatsappId") or f"{number}@c.us"


def _chat_id(settings, phone):
	number = normalize_whatsapp_number(phone)
	if not number:
		frappe.throw(_("No WhatsApp number"))
	chat_id = _whatsapp_id(settings, number)
	if not chat_id:
		frappe.throw(_("{0} is not on WhatsApp").format(number))
	return number, chat_id


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


def _is_number_failure(error):
	"""Whether a failed send says something about the recipient rather than the gateway.

	OpenWA refuses a recipient it cannot resolve with 400. Everything else (gateway unreachable,
	bad key, session not ready, timeouts, 5xx) is the gateway's problem and says nothing about
	the number. A 400 about the session is the gateway's too.
	"""
	if not isinstance(error, OpenWAError):
		# Our own refusals before the gateway was asked, e.g. "not on WhatsApp"
		return True
	return error.status_code == 400 and "session" not in str(error).lower()


def _send(phone, message_type, route, body, content, reference=None, chat_id=None, on_failure=None):
	"""Send and log. `chat_id` skips the WhatsApp lookup when the caller already did it.
	`on_failure(error)` runs with the original error before the failure is reported."""
	settings = _settings()
	if not settings.session_id:
		frappe.throw(_("No WhatsApp session is linked. Open the WhatsApp Link page first."))

	number = normalize_whatsapp_number(phone)
	try:
		if not chat_id:
			number, chat_id = _chat_id(settings, phone)
		result = _call(
			settings,
			"POST",
			f"/sessions/{settings.session_id}/messages/{route}",
			json={"chatId": chat_id, **body},
		)
	except frappe.ValidationError as e:
		_log(number, message_type, content, "Failed", error=str(e), reference=reference)
		if on_failure:
			on_failure(e)
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
	business number can only ever message the party a bill belongs to. A missing number, one with
	no WhatsApp account, or one WhatsApp refused on sending comes back as `needs_number` instead of
	an error, so the dialog can ask for a new one and store it on the party with
	save_party_whatsapp().
	"""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	settings = _settings()
	if not settings.enabled:
		frappe.throw(_("Sending bills via OpenWA is turned off"))

	party_doctype, party = get_party_link(doctype, document_name)
	if not party:
		frappe.throw(_("This document has no customer or supplier to send it to"))
	if not _party_whatsapp_enabled(party_doctype, party):
		# The saved number is not to be used: ask every time, see send_document_to_number()
		return {"needs_number": True, "party_type": party_doctype, "reason": "disabled", "phone": ""}
	number = normalize_whatsapp_number(get_party_whatsapp(party_doctype, party))
	if not number:
		return {"needs_number": True, "party_type": party_doctype, "reason": "missing", "phone": ""}

	if _party_number_valid(party_doctype, party, number):
		chat_id = f"{number}@c.us"
	else:
		try:
			chat_id = _whatsapp_id(settings, number)
		except OpenWAError as e:
			frappe.throw(str(e), title=_("WhatsApp send failed"))
		_record_party_status(party_doctype, party, number, VALID if chat_id else INVALID)
		if not chat_id:
			# Kept although the request returns normally: Frappe commits POSTs
			return {"needs_number": True, "party_type": party_doctype, "reason": "invalid", "phone": number}

	body = _bill_body(pdf_base64, filename, caption)
	number_failure = {}

	def on_failure(error):
		# A send refused over the recipient is the one thing that makes a Valid number worth
		# checking again; a gateway outage says nothing about the number, so it stays as it was
		if _is_number_failure(error):
			_record_party_status(party_doctype, party, number, NOT_CHECKED)
			number_failure["error"] = str(error)

	try:
		return _send(
			number,
			"Document",
			"send-document",
			body,
			caption,
			reference=(doctype, document_name),
			chat_id=chat_id,
			on_failure=on_failure,
		)
	except frappe.ValidationError:
		if not number_failure:
			raise
		# The number itself was refused: let the dialog ask for a new one instead of erroring.
		# The failure is already logged and committed by _send.
		frappe.clear_messages()
		return {
			"needs_number": True,
			"party_type": party_doctype,
			"reason": "failed",
			"phone": number,
			"error": number_failure["error"],
		}


def _bill_body(pdf_base64, filename, caption):
	try:
		head = base64.b64decode(pdf_base64[:8], validate=True)
	except (binascii.Error, TypeError):
		head = b""
	if not head.startswith(b"%PDF"):
		frappe.throw(_("The bill is not a PDF"))
	return {
		"base64": pdf_base64,
		"mimetype": "application/pdf",
		"filename": filename,
		"caption": (caption or "")[:1024],
	}


def _party_whatsapp_enabled(party_doctype, party):
	"""Only customers carry the switch; suppliers always use their saved number."""
	if party_doctype != "Customer":
		return True
	enabled = frappe.db.get_value("Customer", party, "whatsapp_enabled")
	# A row from before the field existed reads None: that is the default, enabled
	return enabled is None or bool(frappe.utils.cint(enabled))


@frappe.whitelist(methods=["POST"])
def send_document_to_number(doctype, document_name, phone, pdf_base64, filename, caption=""):
	"""Send a bill to a number the operator typed, for a customer whose WhatsApp is disabled.

	The number is used for this one send only: it is not written to the customer, its contact or
	its WhatsApp status. Allowed only when the bill's customer has WhatsApp disabled, so the
	party's saved number is never bypassed this way.
	"""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	settings = _settings()
	if not settings.enabled:
		frappe.throw(_("Sending bills via OpenWA is turned off"))
	party_doctype, party = get_party_link(doctype, document_name)
	if not party or _party_whatsapp_enabled(party_doctype, party):
		frappe.throw(_("This customer's WhatsApp is enabled; send to the saved number instead"))

	number = normalize_whatsapp_number(phone)
	if not number or len(number) < 11:
		frappe.throw(_("Enter a full mobile number"))
	body = _bill_body(pdf_base64, filename, caption)
	return _send(number, "Document", "send-document", body, caption, reference=(doctype, document_name))


@frappe.whitelist()
def check_whatsapp_number(phone):
	"""Whether a number has a WhatsApp account, for forms that take a WhatsApp number."""
	_require_desk_user()
	number = normalize_whatsapp_number(phone)
	if not number:
		return {"phone": "", "exists": False}
	settings = _settings()
	if not settings.session_id:
		frappe.throw(_("No WhatsApp number is linked to check against"))
	return _guarded(lambda: {"phone": number, "exists": bool(_whatsapp_id(settings, number))})


def _set_contact_whatsapp(party_doctype, party, number):
	"""Store the WhatsApp number where this app keeps it: the party Contact's non-primary phone row
	(see get_party_whatsapp). A party without a Contact gets one."""
	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": party_doctype, "link_name": party, "parenttype": "Contact"},
		"parent",
	)
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
	else:
		name_field = "customer_name" if party_doctype == "Customer" else "supplier_name"
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": frappe.db.get_value(party_doctype, party, name_field) or party,
				"links": [{"link_doctype": party_doctype, "link_name": party}],
			}
		)

	# Stored the way the customer and supplier forms store it: bare 10 digits for Indian numbers
	if number.startswith(DEFAULT_COUNTRY_CODE) and len(number) == len(DEFAULT_COUNTRY_CODE) + 10:
		number = number[len(DEFAULT_COUNTRY_CODE) :]

	row = next((p for p in contact.phone_nos if not p.is_primary_mobile_no), None)
	if row:
		row.phone = number
	else:
		contact.append("phone_nos", {"phone": number, "is_primary_mobile_no": 0})
	contact.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def save_party_whatsapp(doctype, document_name, phone):
	"""Verify a number on WhatsApp and store it as the bill party's WhatsApp number."""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	party_doctype, party = get_party_link(doctype, document_name)
	if not party:
		frappe.throw(_("This document has no customer or supplier"))
	frappe.has_permission(party_doctype, "write", doc=party, throw=True)

	number = normalize_whatsapp_number(phone)
	if not number or len(number) < 11:
		frappe.throw(_("Enter a full mobile number"))
	settings = _settings()
	try:
		exists = bool(_whatsapp_id(settings, number))
	except OpenWAError as e:
		frappe.throw(str(e), title=_("OpenWA"))
	if not exists:
		frappe.throw(_("{0} is not on WhatsApp").format(number))

	_set_contact_whatsapp(party_doctype, party, number)
	_record_party_status(party_doctype, party, number, VALID)
	return {"phone": number, "party": party}


def _record_party_status(party_doctype, party, number, status):
	if party_doctype not in STATUS_DOCTYPES:
		return
	frappe.db.set_value(
		party_doctype,
		party,
		{
			"whatsapp_status": status,
			"whatsapp_verified_number": number or "",
			"whatsapp_checked_on": now_datetime(),
		},
		update_modified=False,
	)


def _party_number_valid(party_doctype, party, number):
	"""Valid only for the number that was checked; an edited number has to be checked again."""
	if party_doctype not in STATUS_DOCTYPES:
		return False
	status, checked = frappe.db.get_value(
		party_doctype, party, ["whatsapp_status", "whatsapp_verified_number"]
	) or (None, None)
	return status == VALID and normalize_whatsapp_number(checked) == number


def _recorded_status(party_doctype, party, number):
	"""The stored status, if it was recorded for this number; any other number is Not Checked."""
	status, checked = frappe.db.get_value(
		party_doctype, party, ["whatsapp_status", "whatsapp_verified_number"]
	) or (None, None)
	if status and normalize_whatsapp_number(checked) == number:
		return status
	return NOT_CHECKED


def check_party_whatsapp(party_doctype, party, force=False):
	"""Check a party's saved WhatsApp number and record the result on the party.

	Called from the customer / supplier save and the Check button. A number already Valid is not
	checked again unless `force`. A gateway that is down or unlinked never blocks the caller and
	never changes the recorded status, since it says nothing about the number; the reason is
	returned instead.
	"""
	if not _party_whatsapp_enabled(party_doctype, party):
		# A disabled number is never used, so it is not checked either
		return {"status": NOT_CHECKED, "phone": "", "error": "", "disabled": True}
	number = normalize_whatsapp_number(get_party_whatsapp(party_doctype, party))
	if not number:
		_record_party_status(party_doctype, party, "", NOT_CHECKED)
		return {"status": NOT_CHECKED, "phone": "", "error": ""}
	if not force and _party_number_valid(party_doctype, party, number):
		return {"status": VALID, "phone": number, "error": ""}

	settings = _settings()
	if not settings.session_id or not settings.get_password("api_key", raise_exception=False):
		return {
			"status": _recorded_status(party_doctype, party, number),
			"phone": number,
			"error": _("No WhatsApp number is linked to check with"),
		}
	try:
		exists = bool(_whatsapp_id(settings, number, timeout=SAVE_CHECK_TIMEOUT))
	except OpenWAError as e:
		return {"status": _recorded_status(party_doctype, party, number), "phone": number, "error": str(e)}

	status = VALID if exists else INVALID
	_record_party_status(party_doctype, party, number, status)
	return {"status": status, "phone": number, "error": ""}


@frappe.whitelist()
def get_party_whatsapp_status(party_doctype, party):
	_require_desk_user()
	if party_doctype not in STATUS_DOCTYPES:
		frappe.throw(_("Not a customer or supplier"))
	frappe.has_permission(party_doctype, "read", doc=party, throw=True)
	status, checked, checked_on = frappe.db.get_value(
		party_doctype, party, ["whatsapp_status", "whatsapp_verified_number", "whatsapp_checked_on"]
	) or (None, None, None)
	return {
		"enabled": _party_whatsapp_enabled(party_doctype, party),
		"status": status or NOT_CHECKED,
		"verified_number": checked or "",
		"checked_on": checked_on,
		"phone": normalize_whatsapp_number(get_party_whatsapp(party_doctype, party)),
	}


@frappe.whitelist(methods=["POST"])
def verify_party_whatsapp(party_doctype, party):
	"""The Check button: check the saved number now, even if it was Valid before."""
	_require_desk_user()
	if party_doctype not in STATUS_DOCTYPES:
		frappe.throw(_("Not a customer or supplier"))
	frappe.has_permission(party_doctype, "write", doc=party, throw=True)
	return check_party_whatsapp(party_doctype, party, force=True)


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


def _apply_receipts(settings, chat_id, messages):
	"""Live history carries no ack, so take sent/delivered/read from the rows OpenWA stored.

	Only messages the gateway has seen have a row: anything sent while it was linked, from ERPNext
	or the phone. Older messages keep no receipt.
	"""
	if not any(m["from_me"] for m in messages):
		return
	try:
		stored = _call(
			settings,
			"GET",
			f"/sessions/{settings.session_id}/messages",
			params={"chatId": chat_id, "direction": "outgoing", "limit": 100, "inlineMedia": "false"},
		)
	except OpenWAError:
		# Receipts are a nicety; the thread still shows without them
		return
	status = {m.get("waMessageId"): m.get("status") for m in stored.get("messages") or []}
	for m in messages:
		if m["from_me"]:
			m["status"] = status.get(m["id"], "")


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
			messages = [_live_message(m) for m in history]
			_apply_receipts(settings, chat_id, messages)
			return messages
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
