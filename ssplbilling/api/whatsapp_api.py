"""OpenWA (self-hosted WhatsApp HTTP gateway) integration.

OpenWA runs beside the bench (Docker, port 2785) and holds the linked WhatsApp sessions listed in
SSPL WhatsApp Settings. ERPNext only ever talks to it from here, so the API key never reaches a
browser. A user works through the session row assigned to them, else through the shared row (the
one with no user); see _session_row().

Linking: sessions are created and scanned on the OpenWA dashboard, then picked in the settings
table. get_status() / refresh_sessions() mirror a session's state onto its row.

Sending: send_document() takes the bill PDF the print dialog already rendered and hands it to
OpenWA's send-document route. Every send is recorded in SSPL WhatsApp Log. OpenWA answers 201
once it has accepted the message, which is not a delivery receipt.

Chat (WhatsApp Chat page): list_chats() / get_messages() read the linked account's chats live from
the gateway; send_chat_message() / send_chat_file() reply in them; get_chat_media() fetches an
attachment for preview or download. Open to System Managers and to
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
	get_party_mobile,
	get_party_saved_whatsapp,
	get_party_whatsapp,
	normalize_whatsapp_number,
)

SETTINGS_DOCTYPE = "SSPL WhatsApp Settings"
SESSION_DOCTYPE = "SSPL WhatsApp Session"
LOG_DOCTYPE = "SSPL WhatsApp Log"

REQUEST_TIMEOUT = 20
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


def _call(settings, method, path, json=None, params=None, timeout=REQUEST_TIMEOUT, raw=False):
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

	if raw:
		return res

	try:
		return res.json()
	except ValueError:
		return {}


def _session_row(settings, user=None):
	"""The session row a user sends and chats through: their own, else the shared one (no user)."""
	user = user or frappe.session.user
	return next((r for r in settings.sessions if r.user == user), None) or next(
		(r for r in settings.sessions if not r.user), None
	)


# Same rule as dashboard_api.get_allowed_tiles: only these may work under another user's settings
INHERIT_USERS = ("Administrator", "admin")


def _inheritable_user(user=None):
	"""`user` when the caller may take on that user's settings, else the caller."""
	if user and frappe.session.user in INHERIT_USERS:
		return user
	return frappe.session.user


def _linked_row(settings, message=None, session_id=None):
	"""The current user's session row, which must already be linked on the gateway.

	`session_id` is the one the browser stored at login (see get_my_session). It is only trusted
	when it is still this user's session, so a browser can never send through someone else's.
	Administrator may also use the session of the user whose settings it inherits."""
	row = _session_row(settings)
	if session_id and (not row or session_id != row.session_id):
		inherited = frappe.session.user in INHERIT_USERS and next(
			(r for r in settings.sessions if r.session_id == session_id), None
		)
		if not inherited:
			frappe.throw(_("Your WhatsApp session has changed. Reload the page and try again."))
		row = inherited
	if not row or not row.session_id:
		frappe.throw(
			message
			or _(
				"No WhatsApp session is linked for you. Ask an administrator to assign one in SSPL WhatsApp Settings."
			)
		)
	return row


def _managed_row(settings, session_name):
	"""A session row picked on the WhatsApp Link page."""
	row = next((r for r in settings.sessions if r.session_name == session_name), None)
	if not row:
		frappe.throw(_("No session named {0} in SSPL WhatsApp Settings").format(session_name))
	return row


def _store_session(row, session):
	"""Mirror the gateway's view of the session onto its row."""
	values = {
		"session_id": session.get("id") or "",
		"status": session.get("status") or "",
		"phone": session.get("phone") or "",
		"push_name": session.get("pushName") or "",
	}
	frappe.db.set_value(SESSION_DOCTYPE, row.name, values, update_modified=False)
	row.update(values)


def _fetch_session(settings, row):
	"""The row's session as OpenWA reports it, or None when it does not exist there."""
	if row.session_id:
		try:
			return _call(settings, "GET", f"/sessions/{row.session_id}")
		except OpenWAError as e:
			if e.status_code != 404:
				raise

	# Stored id missing or stale (session deleted on the dashboard): look it up by name
	found = _call(settings, "GET", "/sessions", params={"name": row.session_name})
	return found[0] if found else None


def _status_payload(settings, row, session):
	payload = {
		"session_name": row.session_name,
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
		"base_url": settings.base_url,
		# The key itself never leaves the server
		"has_api_key": bool(settings.get_password("api_key", raise_exception=False)),
		"sessions": [
			{
				"session_name": r.session_name,
				"user": r.user or "",
				"status": r.status or "",
				"phone": r.phone or "",
				"push_name": r.push_name or "",
			}
			for r in settings.sessions
		],
	}


# POST because it mirrors the gateway's status onto the settings, and Frappe only commits writes
# made during unsafe requests
@frappe.whitelist(methods=["POST"])
def get_status(session_name):
	_require_manager()

	def run():
		settings = _settings()
		row = _managed_row(settings, session_name)
		session = _fetch_session(settings, row)
		if session:
			_store_session(row, session)
		return _status_payload(settings, row, session)

	return _guarded(run)


@frappe.whitelist()
def list_gateway_sessions():
	"""Names of the sessions that exist on the gateway, for the Session Name dropdowns."""
	_require_manager()
	return _guarded(
		lambda: sorted(s.get("name") for s in _call(_settings(), "GET", "/sessions") if s.get("name"))
	)


@frappe.whitelist()
def get_gateway_session(session_name):
	"""A gateway session's id, status, number and profile, to fill a row picked in the settings form."""
	_require_manager()

	def run():
		found = _call(_settings(), "GET", "/sessions", params={"name": session_name})
		session = found[0] if found else {}
		return {
			"session_id": session.get("id") or "",
			"status": session.get("status") or "",
			"phone": session.get("phone") or "",
			"push_name": session.get("pushName") or "",
		}

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def refresh_sessions():
	"""Mirror every row's session from the gateway, for the settings form."""
	_require_manager()

	def run():
		settings = _settings()
		for row in settings.sessions:
			session = _fetch_session(settings, row)
			if session:
				_store_session(row, session)

	return _guarded(run)


@frappe.whitelist()
def get_my_session(user=None):
	"""The session the logged-in user sends through: their own row, else the shared one.
	Administrator gets the session of `user`, the user whose settings it inherits."""
	_require_desk_user()
	row = _session_row(_settings(), _inheritable_user(user))
	if not row:
		return None
	return {"session_name": row.session_name, "session_id": row.session_id or "", "shared": not row.user}


@frappe.whitelist()
def get_gateway_state(session_id=None):
	"""Whether this user's bills can go out through OpenWA right now. Called by the print dialog."""
	settings = _settings()
	try:
		row = _linked_row(settings, session_id=session_id)
	except frappe.ValidationError:
		return {"ready": False}
	try:
		session = _call(settings, "GET", f"/sessions/{row.session_id}", timeout=STATE_TIMEOUT)
	except frappe.ValidationError:
		return {"ready": False}
	return {"ready": session.get("status") == READY}


def _whatsapp_id(settings, row, number, timeout=REQUEST_TIMEOUT):
	"""Canonical chat id when the (normalized) number has a WhatsApp account, else None."""
	check = _call(settings, "GET", f"/sessions/{row.session_id}/contacts/check/{number}", timeout=timeout)
	if not check.get("exists"):
		return None
	return check.get("whatsappId") or f"{number}@c.us"


def _chat_id(settings, row, phone):
	number = normalize_whatsapp_number(phone)
	if not number:
		frappe.throw(_("No WhatsApp number"))
	chat_id = _whatsapp_id(settings, row, number)
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


def _send(phone, message_type, route, body, content, reference=None, chat_id=None, on_failure=None, row=None):
	"""Send and log through `row`, by default the current user's session. `chat_id` skips the
	WhatsApp lookup when the caller already did it.
	`on_failure(error)` runs with the original error before the failure is reported."""
	settings = _settings()
	row = row or _linked_row(settings)
	if not row.session_id:
		frappe.throw(_("Session {0} is not linked yet").format(row.session_name))

	number = normalize_whatsapp_number(phone)
	try:
		if not chat_id:
			number, chat_id = _chat_id(settings, row, phone)
		result = _call(
			settings,
			"POST",
			f"/sessions/{row.session_id}/messages/{route}",
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
def send_test(session_name, phone, text):
	_require_manager()
	row = _managed_row(_settings(), session_name)
	return _send(phone, "Text", "send-text", {"text": text}, text, row=row)


@frappe.whitelist(methods=["POST"])
def send_document(doctype, document_name, pdf_base64, filename, caption="", session_id=None):
	"""Send a bill PDF the print dialog already rendered to the party's WhatsApp.

	The number is looked up here from the bill's party, never taken from the caller, so the
	business number can only ever message the party a bill belongs to. A missing number, one with
	no WhatsApp account, or one WhatsApp refused on sending comes back as `needs_number` instead of
	an error, so the dialog can ask for a new one and store it on the party with
	save_party_whatsapp(). A party with no WhatsApp number is sent to its mobile number, which is
	then stored as its WhatsApp number (`saved_from_mobile`).
	"""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	settings = _settings()
	row = _linked_row(settings, session_id=session_id)

	party_doctype, party = get_party_link(doctype, document_name)
	if not party:
		frappe.throw(_("This document has no customer or supplier to send it to"))
	if not _party_whatsapp_enabled(party_doctype, party):
		# The saved number is not to be used: ask every time, see send_document_to_number()
		return {"needs_number": True, "party_type": party_doctype, "reason": "disabled", "phone": ""}
	number = normalize_whatsapp_number(get_party_saved_whatsapp(party_doctype, party))
	# No WhatsApp number stored: try the mobile, and keep it as the WhatsApp number once a bill
	# reaches it, so the next bill finds it without the fallback
	from_mobile = not number
	if from_mobile:
		number = normalize_whatsapp_number(get_party_mobile(party_doctype, party))
	if not number:
		return {"needs_number": True, "party_type": party_doctype, "reason": "missing", "phone": ""}

	if _party_number_valid(party_doctype, party, number):
		chat_id = f"{number}@c.us"
	else:
		try:
			chat_id = _whatsapp_id(settings, row, number)
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
		sent = _send(
			number,
			"Document",
			"send-document",
			body,
			caption,
			reference=(doctype, document_name),
			chat_id=chat_id,
			on_failure=on_failure,
			row=row,
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

	# Saved only after the bill went through, so a mobile WhatsApp refused never becomes the
	# stored WhatsApp number. The bill is already sent: a Contact that will not save is logged,
	# not reported as a failed send.
	if from_mobile:
		frappe.db.savepoint("save_whatsapp_from_mobile")
		try:
			_set_contact_whatsapp(party_doctype, party, number)
		except Exception:
			frappe.db.rollback(save_point="save_whatsapp_from_mobile")
			frappe.log_error(title=f"Could not save WhatsApp number for {party_doctype} {party}")
			from_mobile = False
	return {**sent, "saved_from_mobile": from_mobile}


@frappe.whitelist(methods=["POST"])
def send_receipt_pay_link(order_id, session_id=None):
	"""Send a pending Paytm receipt's pay link to the customer's WhatsApp as a text: a receipt QR's
	UPI string (what scanning the QR gives, upi://pay?...) or a payment request's Paytm paymentUrl.

	The number and link are read from the row, never taken from the caller, so this can only
	message the number the receipt was made for."""
	_require_desk_user()
	from ssplbilling.api.paytm_api import (
		PAYMENT_REQUEST_PREFIX,
		_qr_expires_in,
	)

	txn = frappe.db.get_value(
		"SSPL Paytm Transaction",
		order_id,
		["order_id", "channel", "status", "customer", "sales_invoice", "customer_mobile", "amount", "short_url", "qr_data", "creation"],
		as_dict=True,
	)
	is_qr = bool(txn) and txn.channel == "QR"
	is_request = bool(txn) and txn.channel == "Link" and txn.order_id.startswith(PAYMENT_REQUEST_PREFIX)
	if not txn or not txn.customer or txn.sales_invoice or not (is_qr or is_request):
		frappe.throw(_("{0} is not a Paytm receipt QR or payment request").format(order_id))
	if txn.status != "Pending" or not (txn.qr_data if is_qr else txn.short_url):
		frappe.throw(_("Only a pending receipt can be sent"))
	minutes_left = _qr_expires_in("QR", txn.status, txn.creation) // 60 if is_qr else 0
	if is_qr and minutes_left <= 0:
		frappe.throw(_("This QR has expired; generate a new one"))
	if not txn.customer_mobile:
		frappe.throw(_("The receipt has no mobile number"))

	settings = _settings()
	row = _linked_row(settings, session_id=session_id)
	customer_name = frappe.db.get_value("Customer", txn.customer, "customer_name") or txn.customer
	amount = frappe.utils.fmt_money(txn.amount, precision=2)
	if is_qr:
		text = _(
			"Dear {0}, please pay Rs. {1} to Sundaram and Sons using this link (valid for {2} minutes): {3}"
		).format(customer_name, amount, max(1, minutes_left), txn.qr_data)
	else:
		text = _("Dear {0}, please pay Rs. {1} to Sundaram and Sons using this Paytm link: {2}").format(
			customer_name, amount, txn.short_url
		)
	return _send(
		txn.customer_mobile,
		"Text",
		"send-text",
		{"text": text},
		text,
		reference=("SSPL Paytm Transaction", txn.order_id),
		row=row,
	)


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
def send_document_to_number(doctype, document_name, phone, pdf_base64, filename, caption="", session_id=None):
	"""Send a bill to a number the operator typed, for a customer whose WhatsApp is disabled.

	The number is used for this one send only: it is not written to the customer, its contact or
	its WhatsApp status. Allowed only when the bill's customer has WhatsApp disabled, so the
	party's saved number is never bypassed this way.
	"""
	_require_desk_user()
	frappe.has_permission(doctype, "read", doc=document_name, throw=True)
	settings = _settings()
	row = _linked_row(settings, session_id=session_id)
	party_doctype, party = get_party_link(doctype, document_name)
	if not party or _party_whatsapp_enabled(party_doctype, party):
		frappe.throw(_("This customer's WhatsApp is enabled; send to the saved number instead"))

	number = normalize_whatsapp_number(phone)
	if not number or len(number) < 11:
		frappe.throw(_("Enter a full mobile number"))
	body = _bill_body(pdf_base64, filename, caption)
	return _send(
		number, "Document", "send-document", body, caption, reference=(doctype, document_name), row=row
	)


@frappe.whitelist()
def check_whatsapp_number(phone):
	"""Whether a number has a WhatsApp account, for forms that take a WhatsApp number."""
	_require_desk_user()
	number = normalize_whatsapp_number(phone)
	if not number:
		return {"phone": "", "exists": False}
	settings = _settings()
	row = _linked_row(settings, _("No WhatsApp number is linked to check against"))
	return _guarded(lambda: {"phone": number, "exists": bool(_whatsapp_id(settings, row, number))})


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
def save_party_whatsapp(doctype, document_name, phone, session_id=None):
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
	row = _linked_row(settings, _("No WhatsApp number is linked to check against"), session_id=session_id)
	try:
		exists = bool(_whatsapp_id(settings, row, number))
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
	row = _session_row(settings)
	if not row or not row.session_id or not settings.get_password("api_key", raise_exception=False):
		return {
			"status": _recorded_status(party_doctype, party, number),
			"phone": number,
			"error": _("No WhatsApp number is linked to check with"),
		}
	try:
		exists = bool(_whatsapp_id(settings, row, number, timeout=SAVE_CHECK_TIMEOUT))
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


def _chat_settings(session_id=None):
	"""The settings and the current user's linked session row the chat reads through."""
	settings = _settings()
	return settings, _linked_row(settings, session_id=session_id)


def _chat_path(row, chat_id, suffix=""):
	return f"/sessions/{row.session_id}/messages/{quote(chat_id, safe='@.')}{suffix}"


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
def list_chats(limit=200, session_id=None):
	_require_chat_user()

	def run():
		settings, row = _chat_settings(session_id)
		chats = _call(
			settings,
			"GET",
			f"/sessions/{row.session_id}/chats",
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


def _apply_receipts(settings, row, chat_id, messages):
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
			f"/sessions/{row.session_id}/messages",
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
def get_messages(chat_id, limit=50, session_id=None):
	"""Newest `limit` messages of a chat, oldest first."""
	_require_chat_user()
	limit = min(frappe.utils.cint(limit) or 50, 100)

	def run():
		settings, row = _chat_settings(session_id)
		try:
			history = _call(settings, "GET", _chat_path(row, chat_id, "/history"), params={"limit": limit})
			messages = [_live_message(m) for m in history]
			_apply_receipts(settings, row, chat_id, messages)
			return messages
		except OpenWAError as e:
			# Only whatsapp-web.js reads history live; Baileys answers 501, so use what OpenWA stored
			if e.status_code != 501:
				raise
		stored = _call(
			settings,
			"GET",
			f"/sessions/{row.session_id}/messages",
			params={"chatId": chat_id, "limit": limit, "orderBy": "timestamp", "inlineMedia": "false"},
		)
		return [_stored_message(m) for m in reversed(stored.get("messages") or [])]

	return _guarded(run)


@frappe.whitelist(methods=["POST"])
def mark_chat_read(chat_id, session_id=None):
	_require_chat_user()
	settings, row = _chat_settings(session_id)
	try:
		_call(settings, "POST", f"/sessions/{row.session_id}/chats/read", json={"chatId": chat_id})
	except OpenWAError:
		# Unread counts are cosmetic; a failed receipt must not break opening the chat
		pass
	return True


@frappe.whitelist()
def resolve_chat(phone, session_id=None):
	"""Chat id for a new conversation with a number, or an error when it is not on WhatsApp."""
	_require_chat_user()
	return _guarded(
		lambda: dict(zip(("phone", "chat_id"), _chat_id(*_chat_settings(session_id), phone), strict=True))
	)


def _chat_send(chat_id, message_type, route, body, content, session_id=None):
	settings, row = _chat_settings(session_id)
	phone = chat_id.split("@")[0]
	try:
		result = _call(settings, "POST", f"/sessions/{row.session_id}/messages/{route}", json=body)
	except OpenWAError as e:
		_log(phone, message_type, content, "Failed", error=str(e))
		frappe.db.commit()
		frappe.throw(str(e), title=_("WhatsApp send failed"))
	_log(phone, message_type, content, "Sent", message_id=result.get("messageId"))
	return {"message_id": result.get("messageId"), "timestamp": result.get("timestamp")}


@frappe.whitelist(methods=["POST"])
def send_chat_message(chat_id, text, session_id=None):
	_require_chat_user()
	text = (text or "").strip()
	if not text:
		frappe.throw(_("Type a message"))
	return _chat_send(
		chat_id, "Text", "send-text", {"chatId": chat_id, "text": text[:4096]}, text, session_id
	)


@frappe.whitelist(methods=["POST"])
def send_chat_file(chat_id, file_base64, mimetype, filename, caption="", session_id=None):
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
		session_id,
	)


def _stored_media(settings, row, chat_id, message_id):
	"""The copy OpenWA kept of a message it saw while linked, or None."""
	try:
		res = _call(
			settings,
			"GET",
			_chat_path(row, chat_id, f"/{quote(message_id, safe='@.')}/media"),
			timeout=60,
			raw=True,
		)
	except OpenWAError as e:
		if e.status_code == 404:
			return None
		raise
	content_type = (res.headers.get("content-type") or "").split(";")[0].strip()
	return {
		# Archived rows come back as a bare attachment; the page sniffs the bytes for those
		"mimetype": "" if content_type == "application/octet-stream" else content_type,
		"filename": "",
		"data": base64.b64encode(res.content).decode(),
	}


def _live_media(settings, row, chat_id, message_id, depth):
	"""Download one message's media from the phone through live history.

	History downloads media oldest first against a per-response budget, so the window is sized to
	start at the wanted message and it is served before anything newer can use the budget up.
	"""
	try:
		history = _call(
			settings,
			"GET",
			_chat_path(row, chat_id, "/history"),
			params={"limit": min(max(depth, 1), 100), "includeMedia": "true"},
			timeout=90,
		)
	except OpenWAError as e:
		# Baileys reads no live history
		if e.status_code == 501:
			return None
		raise
	media = next((m.get("media") for m in history if m.get("id") == message_id), None)
	if not media or not media.get("data"):
		return None
	return {
		"mimetype": media.get("mimetype") or "",
		"filename": media.get("filename") or "",
		"data": media["data"],
	}


@frappe.whitelist()
def get_chat_media(chat_id, message_id, depth=0, session_id=None):
	"""A message's attachment as {mimetype, filename, data (base64)}.

	`depth` is the message's position counted from the newest in the open thread (1 = newest).
	"""
	_require_chat_user()

	def run():
		settings, row = _chat_settings(session_id)
		media = _stored_media(settings, row, chat_id, message_id) or _live_media(
			settings, row, chat_id, message_id, frappe.utils.cint(depth)
		)
		if not media:
			# WhatsApp drops media from its servers after a while; the phone may still hold it
			frappe.throw(_("This attachment could not be downloaded. Open it on the phone instead."))
		return media

	return _guarded(run)
