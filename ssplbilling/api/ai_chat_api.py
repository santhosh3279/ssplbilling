"""AI Chat endpoints (/frontend/ai-chat). A message is answered by a background job that runs
the chat's provider (ai_chat_runner for Claude, ai_chat_runner_gemini for Gemini) as the chat
user and streams events to them over socket.io (event: sspl_assistant_event)."""

import json
import time

import frappe
from frappe.query_builder.functions import Sum
from frappe.utils import add_to_date, cint, get_datetime, get_first_day, now_datetime, today

from ssplbilling.api import (
	ai_chat_cache,
	ai_chat_export,
	ai_chat_quick,
	ai_chat_runner,
	ai_chat_runner_gemini,
	ai_chat_tools,
)

SETTINGS = ai_chat_runner.SETTINGS
RUNNERS = {"Claude": ai_chat_runner, "Gemini": ai_chat_runner_gemini}
API_KEY_FIELDS = {"Claude": "anthropic_api_key", "Gemini": "google_api_key"}
CHAT = "SSPL Assistant Chat"
MESSAGE = "SSPL Assistant Message"
CACHE = ai_chat_cache.CACHE
REALTIME_EVENT = "sspl_assistant_event"
FLUSH_SECONDS = 0.25
MAX_PROMPT = 8000
CHAT_FIELDS = ("name", "title", "provider", "company", "cost_center", "status", "modified")
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
	"cached_from",
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
		"usage": _usage() if allowed else None,
		**(_scope_options() if allowed else {}),
	}


@frappe.whitelist()
def get_usage():
	_check_access()
	return _usage()


@frappe.whitelist()
def list_chats(limit=50):
	_check_access()
	return frappe.get_all(
		CHAT,
		filters={"user": frappe.session.user},
		fields=list(CHAT_FIELDS),
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
def send_message(message, chat=None, provider=None, company=None, cost_center=None, fresh=0):
	"""fresh=1 skips the query cache and saves a new recipe ("Ask AI fresh" under a reused answer)."""
	_check_access()
	message = (message or "").strip()
	if not message:
		frappe.throw("Message is empty.")
	if len(message) > MAX_PROMPT:
		frappe.throw(f"Message is too long (max {MAX_PROMPT} characters).")

	if not _providers(_settings()):
		frappe.throw(f"No AI provider has an API key in {SETTINGS}. The quick buttons still work.")
	_check_limits(chat)
	return _start_turn(message, chat, provider, company, cost_center, fresh=fresh)


@frappe.whitelist()
def list_saved():
	"""Saved questions for the side panel; each re-runs its recipe with fresh values."""
	_check_access()
	return ai_chat_cache.saved_questions(_settings())


@frappe.whitelist(methods=["POST"])
def ask_saved(saved, values=None, provider=None, company=None, cost_center=None):
	"""A saved question from the side panel, in a new chat: its recipe re-runs with the values the
	user typed in the chat box (customer, item… see ai_chat_cache.params), without the AI picking
	tools. Always a new chat, since a reused answer replaces the chat's AI history."""
	_check_access()
	settings = _settings()
	if not settings.enable_query_cache:
		frappe.throw(f"Reuse Earlier Answers is off in {SETTINGS}.")
	row = frappe.db.get_value(CACHE, {"name": saved, "enabled": 1}, ["question", "recipe"], as_dict=True)
	if not row:
		frappe.throw("This saved question is no longer available. Ask it in the chat box.")
	if not _providers(settings):
		frappe.throw(f"No AI provider has an API key in {SETTINGS}. The quick buttons still work.")
	_check_limits(None)
	asked = {p["key"]: p for p in ai_chat_cache.params(row.question, json.loads(row.recipe or "[]"))}
	values = frappe.parse_json(values) if isinstance(values, str) else (values or {})
	values = {k: str(v).strip() for k, v in values.items() if k in asked and str(v or "").strip()}
	message = ai_chat_cache.retitle(row.question, asked, values)
	return {
		**_start_turn(message, None, provider, company, cost_center, cached=saved, values=values),
		"message": message,
	}


def _start_turn(message, chat, provider, company, cost_center, fresh=0, cached=None, values=None):
	doc = _own_chat(chat) if chat else _new_chat(message, provider)
	if doc.status == "Running" and not _is_stale(doc):
		frappe.throw("Still answering the previous message. Wait for it or press Stop.")
	_set_scope(doc, company, cost_center)
	settings = _settings()
	if not cached and not cint(fresh) and settings.enable_query_cache and not doc.history:
		cached = ai_chat_cache.find(message, doc.company, doc.cost_center, settings)

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
		cached=cached,
		fresh=cint(fresh),
		values=values,
	)
	return {"chat": _chat_dict(doc)}


@frappe.whitelist(methods=["POST"])
def quick_answer(action, query=None, chat=None, provider=None, company=None, cost_center=None):
	"""Quick button: answered locally by ai_chat_quick, no AI call and no tokens. Kept in the
	chat for the user to read, but not in the AI history."""
	_check_access()
	label, query = ai_chat_quick.label_for(action, query)
	doc = _own_chat(chat) if chat else _new_chat(label, provider)
	if doc.status == "Running" and not _is_stale(doc):
		frappe.throw("Still answering the previous message. Wait for it or press Stop.")
	_set_scope(doc, company, cost_center)
	with ai_chat_tools.scope(doc.company, doc.cost_center):
		label, reply = ai_chat_quick.answer(action, query)
	messages = [
		_insert_message(doc.name, "user", label, quick=True),
		_insert_message(
			doc.name,
			"assistant",
			reply,
			quick=True,
			quick_source={
				"action": action,
				"query": query,
				"company": doc.company,
				"cost_center": doc.cost_center,
			},
		),
	]
	frappe.db.set_value(CHAT, doc.name, "modified", frappe.utils.now())
	return {"chat": _chat_dict(doc), "messages": messages}


@frappe.whitelist(methods=["POST"])
def quick_output(message, kind):
	"""⬇ Excel / 📊 Chart / 🥧 Pie under a quick answer: built locally from the same data, no AI call.
	The result is added to that message's attachments and the updated message returned."""
	_check_access()
	msg = frappe.get_doc(MESSAGE, message)
	chat = _own_chat(msg.chat)
	if not msg.quick_source:
		frappe.throw("This answer has no data source to export.")
	src = json.loads(msg.quick_source)
	attachments = json.loads(msg.attachments or "[]")
	# The scope the answer was made with, saved on it, so the file matches what was shown.
	with ai_chat_tools.scope(src.get("company"), src.get("cost_center")):
		try:
			res = _quick_output(src, kind, attachments)
		except ValueError as e:  # nothing found / ambiguous search: a message, not a server error
			frappe.throw(str(e))
	if not res.get("ok"):
		frappe.throw(res.get("message") or "Nothing to show.")
	_attach_files(attachments, chat.name)
	frappe.db.set_value(MESSAGE, msg.name, "attachments", json.dumps(attachments, default=str))
	return {k: frappe.db.get_value(MESSAGE, msg.name, k) for k in MESSAGE_FIELDS}


def _quick_output(src, kind, attachments):
	if kind == "excel":
		tool, args, title = ai_chat_quick.export_source(src["action"], src.get("query"))
		res = ai_chat_export.export_excel(tool, title, args, attachments)
	elif kind == "chart":
		tool, args, title, chart_type = ai_chat_quick.chart_source(src["action"], src.get("query"))
		res = ai_chat_export.make_chart(tool, title, chart_type, args, attachments)
	elif kind == "pie":
		tool, args, title = ai_chat_quick.pie_source(src["action"], src.get("query"))
		res = ai_chat_export.make_chart(tool, title, "pie", args, attachments)
	else:
		frappe.throw(f"Unknown output: {kind}")
	return res


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


def process_turn(chat, prompt, cached=None, fresh=0, values=None):
	"""Background job: run the AI as the chat user, stream to them, store the reply. `cached`
	is a saved recipe to re-run instead (ai_chat_cache); fresh ignores the chat's history,
	since it re-asks the question just before it. values: the side panel's (ask_saved)."""
	doc = frappe.get_doc(CHAT, chat)
	user = doc.user
	# Tools query ERPNext in-process, so they must run with the chat user's permissions.
	frappe.set_user(user)
	frappe.cache.delete_value(_cancel_key(chat))
	pending = {"text": "", "at": time.monotonic()}
	calls = []  # tool calls with their outcome, for the query cache
	history = None if cint(fresh) or not doc.history else json.loads(doc.history)

	def publish(payload):
		frappe.publish_realtime(REALTIME_EVENT, {"chat": chat, **payload}, user=user, after_commit=False)

	def flush():
		if pending["text"]:
			publish({"type": "text", "text": pending["text"]})
			pending["text"] = ""
		pending["at"] = time.monotonic()

	def on_event(ev):
		if ev["type"] == "tool":
			calls.append({"name": ev["name"], "input": ev.get("input"), "ok": None})
		elif ev["type"] == "tool_result":
			call = next((c for c in reversed(calls) if c["name"] == ev["name"] and c["ok"] is None), None)
			if call:
				call["ok"] = ev["ok"]
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
		# Tool calls that don't name a company / cost center use the chat's.
		# The user's last questions let the guard tell "all companies" asked for from the AI's own idea.
		with ai_chat_tools.scope(doc.company, doc.cost_center, question=_recent_questions(chat)):
			is_cancelled = lambda: frappe.cache.get_value(_cancel_key(chat))  # noqa: E731
			if cached:
				result = _reuse(doc, prompt, cached, on_event, is_cancelled, values)
			else:
				result = RUNNERS[doc.provider or "Claude"].run(
					prompt, history, on_event=on_event, is_cancelled=is_cancelled
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

	# Only a chat's first question is saved: a follow-up depends on the chat before it.
	savable = not (cached or history or cancelled or result["error"])
	if savable and result["text"] and _settings().enable_query_cache:
		try:
			ai_chat_cache.save(prompt, doc.company, doc.cost_center, doc.provider, calls, result["text"])
		except Exception:
			frappe.log_error(title="SSPL AI Chat query cache save failed")

	if result["text"]:
		msg = _insert_message(chat, "assistant", result["text"], result, cached_from=cached)
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


def _reuse(doc, prompt, cached, on_event, is_cancelled, values=None):
	"""Answer from a saved recipe: re-run its tool calls for live figures, then word the reply
	on the provider's cheapest model without tools, or as plain tables (no AI call). Falls
	back to tables when the AI gives no text."""
	started = time.monotonic()
	attachments = []
	calls = ai_chat_cache.replay(cached, attachments, on_event, values)
	runner = RUNNERS[doc.provider or "Claude"]
	result = None
	if _settings().cache_reply_mode != ai_chat_cache.MODE_TABLES and _providers(_settings()):
		result = runner.run(
			ai_chat_cache.data_prompt(prompt, calls),
			on_event=on_event,
			is_cancelled=is_cancelled,
			use_tools=False,
			model=runner.DEFAULT_MODEL,
		)
		if not result["text"]:
			frappe.log_error(title="SSPL AI Chat reuse rewrite failed", message=result["error"])
			result = None
	if result is None:
		text = ai_chat_cache.tables(calls)
		on_event({"type": "text", "text": text})
		result = {
			"text": text,
			"error": None,
			"input_tokens": 0,
			"output_tokens": 0,
			"history": runner.text_history(prompt, text),
		}
	result["tools"] = [{"name": c["name"], "input": c["input"]} for c in calls]
	result["attachments"] = attachments
	result["duration_ms"] = int((time.monotonic() - started) * 1000)
	return result


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


def _scope_options():
	"""Companies and cost centers the user can read, plus their billing defaults (SSPL Billing
	Settings → user row), for the chat page's dropdowns."""
	companies = frappe.get_list("Company", pluck="name", order_by="name asc", limit=0)
	cost_centers = frappe.get_list(
		"Cost Center",
		filters={"is_group": 0, "disabled": 0, "company": ["in", companies or [""]]},
		fields=["name", "company"],
		order_by="name asc",
		limit=0,
	)
	billing = frappe.get_cached_doc("SSPL Billing Settings")
	row = next((r for r in billing.user_series if r.user == frappe.session.user), None)
	company = (row and row.company) or frappe.defaults.get_user_default("Company") or ""
	cost_center = (row and row.cost_center) or ""
	if company not in companies:
		company, cost_center = "", ""
	if cost_center and not any(c.name == cost_center and c.company == company for c in cost_centers):
		cost_center = ""
	return {
		"companies": companies,
		"cost_centers": cost_centers,
		"default_company": company,
		"default_cost_center": cost_center,
	}


def _recent_questions(chat):
	"""This turn's question and the one before it (a follow-up like "and last month?" keeps the
	earlier "both companies")."""
	return "\n".join(
		frappe.get_all(
			MESSAGE,
			filters={"chat": chat, "role": "user", "quick": 0},
			pluck="content",
			order_by="creation desc",
			limit=2,
		)
	)


def _set_scope(doc, company, cost_center):
	"""Save the page's company / cost center on the chat ("" = all). None leaves it unchanged."""
	if company is None and cost_center is None:
		return
	company, cost_center = company or "", cost_center or ""
	if company and company not in frappe.get_list("Company", pluck="name", limit=0):
		frappe.throw(f"You can't read company {company}.", frappe.PermissionError)
	if cost_center:
		cc_company = frappe.db.get_value("Cost Center", cost_center, "company")
		if not cc_company:
			frappe.throw(f"No cost center named {cost_center}.")
		if company and cc_company != company:
			frappe.throw(f"Cost center {cost_center} belongs to {cc_company}, not {company}.")
		company = cc_company
	if (doc.company or "", doc.cost_center or "") != (company, cost_center):
		frappe.db.set_value(CHAT, doc.name, {"company": company or None, "cost_center": cost_center or None})
		doc.company, doc.cost_center = company or None, cost_center or None


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


def _usage():
	"""The user's AI tokens today and this month (deleted chats drop out, their messages go with them)."""
	msg, chat = frappe.qb.DocType(MESSAGE), frappe.qb.DocType(CHAT)
	day, month = get_datetime(today()), get_datetime(get_first_day(today()))

	def total(since):
		rows = (
			frappe.qb.from_(msg)
			.join(chat)
			.on(chat.name == msg.chat)
			.select(Sum(msg.input_tokens), Sum(msg.output_tokens))
			.where((chat.user == frappe.session.user) & (msg.creation >= since))
			.run()
		)
		inp, out = rows[0] if rows else (0, 0)
		return {"input": cint(inp), "output": cint(out), "total": cint(inp) + cint(out)}

	return {"today": total(day), "month": total(month)}


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
	return {k: doc.get(k) for k in CHAT_FIELDS}


def _insert_message(chat, role, content, result=None, quick=False, quick_source=None, cached_from=None):
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
			"cached_from": cached_from,
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
