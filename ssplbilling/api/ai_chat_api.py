"""AI Chat endpoints (/frontend/ai-chat). A message is answered by a background job that runs
the chat's provider (ai_chat_runner for Claude, ai_chat_runner_gemini for Gemini) as the chat
user and streams events to them over socket.io (event: sspl_assistant_event)."""

import json
import time

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from ssplbilling.api import ai_chat_export, ai_chat_quick, ai_chat_runner, ai_chat_runner_gemini

SETTINGS = ai_chat_runner.SETTINGS
RUNNERS = {"Claude": ai_chat_runner, "Gemini": ai_chat_runner_gemini}
API_KEY_FIELDS = {"Claude": "anthropic_api_key", "Gemini": "google_api_key"}
CHAT = "SSPL Assistant Chat"
MESSAGE = "SSPL Assistant Message"
REALTIME_EVENT = "sspl_assistant_event"
FLUSH_SECONDS = 0.25
MAX_PROMPT = 8000
MESSAGE_FIELDS = (
	"name",
	"role",
	"content",
	"tools",
	"duration_ms",
	"input_tokens",
	"output_tokens",
	"quick",
	"quick_source",
	"attachments",
	"creation",
)


@frappe.whitelist()
def get_bootstrap():
	settings = _settings()
	allowed = bool(settings.enabled and _user_can_chat())
	return {
		"enabled": bool(settings.enabled),
		"allowed": allowed,
		"quick_actions": [
			{"action": a, "label": label, "needs_query": needs}
			for a, (label, needs) in ai_chat_quick.ACTIONS.items()
		],
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
			fields=list(MESSAGE_FIELDS),
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

	if not _providers(_settings()):
		frappe.throw(f"No AI provider has an API key in {SETTINGS}. The quick buttons still work.")
	_check_limits(chat)
	doc = _own_chat(chat) if chat else _new_chat(message, provider)
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
def quick_answer(action, query=None, chat=None, provider=None):
	"""Quick button: answered locally by ai_chat_quick, no AI call and no tokens. Kept in the
	chat for the user to read, but not in the AI history."""
	_check_access()
	label, reply = ai_chat_quick.answer(action, query)
	doc = _own_chat(chat) if chat else _new_chat(label, provider)
	if doc.status == "Running" and not _is_stale(doc):
		frappe.throw("Still answering the previous message. Wait for it or press Stop.")
	messages = [
		_insert_message(doc.name, "user", label, quick=True),
		_insert_message(
			doc.name, "assistant", reply, quick=True, quick_source={"action": action, "query": query}
		),
	]
	frappe.db.set_value(CHAT, doc.name, "modified", frappe.utils.now())
	return {"chat": _chat_dict(doc), "messages": messages}


@frappe.whitelist(methods=["POST"])
def quick_output(message, kind):
	"""⬇ Excel / 📊 Chart under a quick answer: built locally from the same data, no AI call.
	The result is added to that message's attachments and the updated message returned."""
	_check_access()
	msg = frappe.get_doc(MESSAGE, message)
	chat = _own_chat(msg.chat)
	if not msg.quick_source:
		frappe.throw("This answer has no data source to export.")
	src = json.loads(msg.quick_source)
	attachments = json.loads(msg.attachments or "[]")
	if kind == "excel":
		tool, args, title = ai_chat_quick.export_source(src["action"], src.get("query"))
		res = ai_chat_export.export_excel(tool, title, args, attachments)
	elif kind == "chart":
		tool, args, title, chart_type = ai_chat_quick.chart_source(src["action"], src.get("query"))
		res = ai_chat_export.make_chart(tool, title, chart_type, args, attachments)
	else:
		frappe.throw(f"Unknown output: {kind}")
	if not res.get("ok"):
		frappe.throw(res.get("message") or "Nothing to show.")
	_attach_files(attachments, chat.name)
	frappe.db.set_value(MESSAGE, msg.name, "attachments", json.dumps(attachments, default=str))
	return {k: frappe.db.get_value(MESSAGE, msg.name, k) for k in MESSAGE_FIELDS}


@frappe.whitelist()
def download_export(file):
	"""Excel exports are private Files attached to a chat; only that chat's user may fetch them
	(the File's own permission would follow the chat doctype, which staff can't read)."""
	_check_access()
	if not frappe.db.exists("File", file):
		frappe.throw("This export has expired. Ask again to make a new one.", frappe.DoesNotExistError)
	f = frappe.get_doc("File", file)
	if f.attached_to_doctype != CHAT or not f.file_name.startswith(ai_chat_export.FILE_PREFIX):
		frappe.throw("Not an AI Chat export.", frappe.PermissionError)
	_own_chat(f.attached_to_name)
	frappe.local.response.filename = f.file_name
	frappe.local.response.filecontent = f.get_content()
	frappe.local.response.type = "download"


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


def _new_chat(title, provider):
	providers = _providers(_settings()) or ["Claude"]
	# A chat keeps its provider: each provider's history format is its own.
	return frappe.get_doc(
		{
			"doctype": CHAT,
			"user": frappe.session.user,
			"provider": provider if provider in providers else providers[0],
			"title": title[:80],
			"status": "Idle",
		}
	).insert(ignore_permissions=True)


def _check_limits(chat):
	"""AI questions cost tokens; quick buttons don't count."""
	settings = _settings()
	asked = {"role": "user", "quick": 0}
	if settings.daily_question_limit:
		today = frappe.db.count(
			MESSAGE, {**asked, "owner": frappe.session.user, "creation": [">=", frappe.utils.today()]}
		)
		if today >= settings.daily_question_limit:
			frappe.throw(
				f"Daily limit of {settings.daily_question_limit} AI questions reached. The quick buttons still work."
			)
	if (
		chat
		and settings.max_turns
		and frappe.db.count(MESSAGE, {**asked, "chat": chat}) >= settings.max_turns
	):
		frappe.throw(
			f"This chat has {settings.max_turns} questions; each one re-sends the whole chat. Start a New chat."
		)


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


def _insert_message(chat, role, content, result=None, quick=False, quick_source=None):
	tools = [{"name": t["name"]} for t in (result or {}).get("tools") or []]
	attachments = (result or {}).get("attachments") or []
	_attach_files(attachments, chat)
	doc = frappe.get_doc(
		{
			"doctype": MESSAGE,
			"chat": chat,
			"role": role,
			"content": content,
			"tools": json.dumps(tools) if tools else None,
			"duration_ms": (result or {}).get("duration_ms"),
			"input_tokens": (result or {}).get("input_tokens"),
			"output_tokens": (result or {}).get("output_tokens"),
			"quick": int(quick),
			"quick_source": json.dumps(quick_source) if quick_source else None,
			"attachments": json.dumps(attachments, default=str) if attachments else None,
		}
	).insert(ignore_permissions=True)
	return {k: doc.get(k) for k in MESSAGE_FIELDS}


def _attach_files(attachments, chat):
	"""Tie export Files to the chat, which is what download_export checks."""
	for a in attachments:
		if a.get("type") == "excel":
			frappe.db.set_value("File", a["file"], {"attached_to_doctype": CHAT, "attached_to_name": chat})


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
