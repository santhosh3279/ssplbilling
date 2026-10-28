"""AI Chat endpoints (/frontend/ai-chat). A message is answered by a background job that runs
the chat's provider (ai_chat_runner for Claude, ai_chat_runner_gemini for Gemini) as the chat
user and streams events to them over socket.io (event: sspl_assistant_event)."""

import json
import time

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from ssplbilling.api import ai_chat_runner, ai_chat_runner_gemini

SETTINGS = ai_chat_runner.SETTINGS
RUNNERS = {"Claude": ai_chat_runner, "Gemini": ai_chat_runner_gemini}
API_KEY_FIELDS = {"Claude": "anthropic_api_key", "Gemini": "google_api_key"}
CHAT = "SSPL Assistant Chat"
MESSAGE = "SSPL Assistant Message"
REALTIME_EVENT = "sspl_assistant_event"
FLUSH_SECONDS = 0.25
MAX_PROMPT = 8000


@frappe.whitelist()
def get_bootstrap():
	settings = _settings()
	allowed = bool(settings.enabled and _user_can_chat())
	return {
		"enabled": bool(settings.enabled),
		"allowed": allowed,
		"providers": _providers(settings) if allowed else [],
		"default_provider": settings.default_provider or "Claude",
	}


@frappe.whitelist()
def list_chats(limit=50):
	_check_access()
	return frappe.get_all(
		CHAT,
		filters={"user": frappe.session.user},
		fields=["name", "title", "provider", "status", "modified"],
		order_by="modified desc",
		limit=min(int(limit), 200),
	)


@frappe.whitelist()
def get_messages(chat):
	_check_access()
	doc = _own_chat(chat)
	return {
		"chat": _chat_dict(doc),
		"messages": frappe.get_all(
			MESSAGE,
			filters={"chat": doc.name},
			fields=["name", "role", "content", "tools", "duration_ms", "creation"],
			order_by="creation asc",
			limit=500,
		),
	}


@frappe.whitelist(methods=["POST"])
def send_message(message, chat=None, provider=None):
	_check_access()
	message = (message or "").strip()
	if not message:
		frappe.throw("Message is empty.")
	if len(message) > MAX_PROMPT:
		frappe.throw(f"Message is too long (max {MAX_PROMPT} characters).")

	if chat:
		doc = _own_chat(chat)
	else:
		providers = _providers(_settings())
		if not providers:
			frappe.throw(f"No AI provider has an API key in {SETTINGS}.")
		# A chat keeps its provider: each provider's history format is its own.
		doc = frappe.get_doc(
			{
				"doctype": CHAT,
				"user": frappe.session.user,
				"provider": provider if provider in providers else providers[0],
				"title": message[:80],
				"status": "Idle",
			}
		).insert(ignore_permissions=True)
	if doc.status == "Running" and not _is_stale(doc):
		frappe.throw("Still answering the previous message. Wait for it or press Stop.")

	_insert_message(doc.name, "user", message)
	frappe.db.set_value(CHAT, doc.name, "status", "Running")
	doc.status = "Running"
	frappe.enqueue(
		"ssplbilling.api.ai_chat_api.process_turn",
		queue="long",
		timeout=(_settings().timeout_seconds or 300) + 120,
		enqueue_after_commit=True,
		chat=doc.name,
		prompt=message,
	)
	return {"chat": _chat_dict(doc)}


@frappe.whitelist(methods=["POST"])
def cancel(chat):
	_check_access()
	doc = _own_chat(chat)
	if doc.status == "Running":
		# The run polls this flag between stream events; a dead job is released by _is_stale.
		frappe.cache.set_value(_cancel_key(doc.name), 1, expires_in_sec=600)
	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def delete_chat(chat):
	_check_access()
	doc = _own_chat(chat)
	if doc.status == "Running" and not _is_stale(doc):
		frappe.throw("Stop the running reply first.")
	frappe.db.delete(MESSAGE, {"chat": doc.name})
	frappe.delete_doc(CHAT, doc.name, ignore_permissions=True)
	return {"ok": True}


def process_turn(chat, prompt):
	"""Background job: run Claude as the chat user, stream to them, store the reply."""
	doc = frappe.get_doc(CHAT, chat)
	user = doc.user
	# Tools query ERPNext in-process, so they must run with the chat user's permissions.
	frappe.set_user(user)
	frappe.cache.delete_value(_cancel_key(chat))
	pending = {"text": "", "at": time.monotonic()}

	def publish(payload):
		frappe.publish_realtime(REALTIME_EVENT, {"chat": chat, **payload}, user=user, after_commit=False)

	def flush():
		if pending["text"]:
			publish({"type": "text", "text": pending["text"]})
			pending["text"] = ""
		pending["at"] = time.monotonic()

	def on_event(ev):
		if ev["type"] == "text":
			pending["text"] += ev["text"]
			if time.monotonic() - pending["at"] >= FLUSH_SECONDS:
				flush()
			return
		flush()
		if ev["type"] in ("tool", "tool_result"):
			publish({k: v for k, v in ev.items() if k != "input"} | {"input": _brief(ev.get("input"))})

	publish({"type": "start", "provider": doc.provider})
	try:
		result = RUNNERS[doc.provider or "Claude"].run(
			prompt,
			json.loads(doc.history) if doc.history else None,
			on_event=on_event,
			is_cancelled=lambda: frappe.cache.get_value(_cancel_key(chat)),
		)
	except Exception as e:
		frappe.log_error(title=f"SSPL AI Chat {doc.provider} run failed")
		result = {"text": "", "tools": [], "error": str(e), "duration_ms": 0}
	flush()

	cancelled = frappe.cache.get_value(_cancel_key(chat))
	frappe.cache.delete_value(_cancel_key(chat))
	if cancelled:
		result["error"] = None
		result["text"] = (result["text"] + "\n\n_(stopped)_").strip()

	if result["text"]:
		msg = _insert_message(chat, "assistant", result["text"], result)
	else:
		msg = _insert_message(chat, "error", result["error"] or "No answer.", result)
	if result["error"] and result["text"]:
		_insert_message(chat, "error", result["error"])

	values = {"status": "Idle"}
	if result.get("history"):
		values["history"] = json.dumps(result["history"], ensure_ascii=False, default=str)
	frappe.db.set_value(CHAT, chat, values)
	frappe.db.commit()

	publish({"type": "done", "message": msg})
	return msg


# ── helpers ─────────────────────────────────────────────────────────────────


def _settings():
	return frappe.get_cached_doc(SETTINGS)


def _providers(settings):
	"""Providers with an API key, default first."""
	have = [p for p, field in API_KEY_FIELDS.items() if settings.get_password(field, raise_exception=False)]
	return sorted(have, key=lambda p: p != (settings.default_provider or "Claude"))


def _user_can_chat(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	if user == "Guest":
		return False
	roles = {r.strip() for r in (_settings().allowed_roles or "").splitlines() if r.strip()}
	return bool(roles & set(frappe.get_roles(user)))


def _check_access():
	if not _settings().enabled:
		frappe.throw(f"AI Chat is turned off in {SETTINGS}.", frappe.PermissionError)
	if not _user_can_chat():
		frappe.throw("You do not have access to AI Chat.", frappe.PermissionError)


def _own_chat(name):
	doc = frappe.get_doc(CHAT, name)
	if doc.user != frappe.session.user:
		frappe.throw("Not your chat.", frappe.PermissionError)
	return doc


def _chat_dict(doc):
	return {k: doc.get(k) for k in ("name", "title", "provider", "status", "modified")}


def _insert_message(chat, role, content, result=None):
	tools = [{"name": t["name"]} for t in (result or {}).get("tools") or []]
	doc = frappe.get_doc(
		{
			"doctype": MESSAGE,
			"chat": chat,
			"role": role,
			"content": content,
			"tools": json.dumps(tools) if tools else None,
			"duration_ms": (result or {}).get("duration_ms"),
		}
	).insert(ignore_permissions=True)
	return {k: doc.get(k) for k in ("name", "role", "content", "tools", "duration_ms", "creation")}


def _is_stale(doc):
	timeout = (_settings().timeout_seconds or 300) + 180
	return get_datetime(doc.modified) < add_to_date(now_datetime(), seconds=-timeout)


def _brief(value, limit=300):
	if value is None:
		return None
	text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
	return text[:limit]


def _cancel_key(chat):
	return f"sspl_assistant:cancel:{chat}"
