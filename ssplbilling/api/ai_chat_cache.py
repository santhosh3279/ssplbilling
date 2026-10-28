"""AI Chat query cache: a question asked again re-runs the tool calls the AI made the first
time (the "recipe", saved in SSPL Assistant Query Cache) instead of letting the AI work them
out again. Figures are always live: the tools re-run as the asking user, and relative dates
(today, this month…) are moved forward to today. Only the wording of the reply is reused
work, either by the provider's cheapest model without tools ("AI Rewrite") or as plain
tables with no AI call ("Tables Only").

A near match must have the same words apart from typos, and numbers and date words must be
identical, so "outstanding of Ravi Traders" never reuses "outstanding of Kumar Stores".
"""

import json
import re
from difflib import SequenceMatcher

import frappe
from frappe.utils import add_days, add_months, add_to_date, cint, flt, get_first_day, get_last_day, getdate
from frappe.utils import now_datetime, nowdate

from ssplbilling.api import ai_chat_quick, ai_chat_tools

CACHE = "SSPL Assistant Query Cache"
MODE_AI = "AI Rewrite"
MODE_TABLES = "Tables Only"

STOP_WORDS = {
	"a", "about", "an", "and", "are", "can", "could", "do", "does", "for", "get", "give", "has",
	"have", "how", "i", "in", "is", "kindly", "list", "many", "me", "much", "my", "need", "of",
	"on", "our", "please", "pls", "plz", "s", "see", "show", "tell", "the", "to", "us", "want",
	"was", "we", "were", "what", "whats", "with", "you",
}  # fmt: skip
SYNONYMS = {
	"sale": "sales", "billing": "sales", "bill": "sales", "turnover": "sales", "revenue": "sales",
	"purchase": "purchases", "due": "outstanding", "dues": "outstanding", "receivable": "outstanding",
	"pending": "outstanding", "product": "item", "inventory": "stock", "todays": "today",
	"yesterdays": "yesterday", "previous": "last", "current": "this", "graph": "chart",
	"xlsx": "excel", "download": "excel", "export": "excel",
}  # fmt: skip
# Must match exactly in a near match: they change which figures the answer is about.
DATE_WORDS = {
	"today", "yesterday", "tomorrow", "day", "daily", "week", "weekly", "month", "monthly",
	"year", "yearly", "fy", "quarter", "last", "this", "next", "ytd", "mtd",
}  # fmt: skip
# A question naming a fixed date keeps its dates on reuse instead of moving them to today.
FIXED_DATE = re.compile(
	r"\b(\d{4}|\d{1,2}[/.-]\d{1,2}|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|"
	r"february|march|april|june|july|august|september|october|november|december)\b",
	re.IGNORECASE,
)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Tool args naming one party / item / account: a saved question asks for them again when
# re-run from the side panel. Dates too, when the question named a fixed date.
PARAM_KEYS = {
	"customer": "Customer",
	"supplier": "Supplier",
	"item": "Item",
	"account": "Account",
	"warehouse": "Warehouse",
}
DATE_KEYS = {
	"from_date": "From date (YYYY-MM-DD)",
	"to_date": "To date (YYYY-MM-DD)",
	"as_of": "As of (YYYY-MM-DD)",
}
MONEY_KEY = re.compile(
	r"amount|total|balance|value|sales|outstanding|receivable|payable|advance|profit|income|"
	r"expense|tax|paid|received|net|debit|credit|opening|closing|cash|bank|price|rate",
	re.IGNORECASE,
)


# ── matching ────────────────────────────────────────────────────────────────


def words(question):
	out = set()
	for w in re.findall(r"[a-z0-9]+", (question or "").lower()):
		w = SYNONYMS.get(w, w)
		if len(w) > 4 and w.endswith("s") and not w.endswith("ss") and not w.isdigit():
			w = SYNONYMS.get(w[:-1], w[:-1])
		if w not in STOP_WORDS:
			out.add(w)
	return sorted(out)


def scope_key(company, cost_center):
	return f"{company or ''}|{cost_center or ''}"


def find(question, company, cost_center, settings):
	"""Name of the saved recipe this question can reuse, or None."""
	tokens = words(question)
	if not tokens:
		return None
	filters = {"enabled": 1, "scope_key": scope_key(company, cost_center), "token_count": len(tokens)}
	if cint(settings.cache_expiry_days):
		filters["modified"] = [">=", add_to_date(now_datetime(), days=-cint(settings.cache_expiry_days))]
	key = " ".join(tokens)
	exact = frappe.get_all(CACHE, filters={**filters, "match_key": key}, pluck="name", limit=1)
	if exact:
		return exact[0]
	threshold = flt(settings.cache_match_threshold) or 0.85
	if threshold >= 1:
		return None
	for row in frappe.get_all(
		CACHE, filters=filters, fields=["name", "match_key"], order_by="hits desc", limit=500
	):
		if _similar(tokens, row.match_key.split(), threshold):
			return row.name
	return None


def _similar(a, b, threshold):
	"""Same number of words, each paired with one at least `threshold` alike; numbers and
	date words only pair with themselves."""
	rest = list(b)
	for w in a:
		if _protected(w):
			if w not in rest:
				return False
			rest.remove(w)
			continue
		best, score = None, 0
		for other in rest:
			if _protected(other):
				continue
			s = SequenceMatcher(None, w, other).ratio()
			if s > score:
				best, score = other, s
		if best is None or score < threshold:
			return False
		rest.remove(best)
	return not rest


def _protected(word):
	return word in DATE_WORDS or any(ch.isdigit() for ch in word)


# ── saving ──────────────────────────────────────────────────────────────────


def save(question, company, cost_center, provider, calls, answer):
	"""Save (or refresh) the recipe for a question the AI answered with tool calls."""
	tokens = words(question)
	calls = [{"name": c["name"], "input": c.get("input") or {}} for c in calls if c.get("ok")]
	if not tokens or not calls:
		return
	values = {
		"question": question[:1000],
		"company": company or None,
		"cost_center": cost_center or None,
		"provider": provider,
		"asked_on": nowdate(),
		"recipe": json.dumps(calls, ensure_ascii=False, default=str, indent=1),
		"answer": answer,
		"enabled": 1,
	}
	key, scope = " ".join(tokens), scope_key(company, cost_center)
	name = frappe.db.get_value(CACHE, {"match_key": key, "scope_key": scope})
	if name:
		doc = frappe.get_doc(CACHE, name)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{"doctype": CACHE, "match_key": key, "scope_key": scope, "token_count": len(tokens), **values}
		).insert(ignore_permissions=True)


# ── replay ──────────────────────────────────────────────────────────────────


def replay(name, attachments, on_event=None, values=None):
	"""Re-run a saved recipe as the current user. Returns [{name, input, content, is_error}].
	values: {param key: new value} from the side panel, put in after the dates move to today."""
	doc = frappe.get_doc(CACHE, name)
	frappe.db.set_value(
		CACHE, name, {"hits": cint(doc.hits) + 1, "last_used": now_datetime()}, update_modified=False
	)
	fixed = bool(FIXED_DATE.search(doc.question or ""))
	asked, today = getdate(doc.asked_on), getdate(nowdate())
	out = []
	for call in json.loads(doc.recipe or "[]"):
		args = call["input"] if fixed else rebase_dates(call["input"], asked, today)
		if values:
			args = _apply(args, values)
		if on_event:
			on_event({"type": "tool", "name": call["name"], "input": args})
		content, is_error = ai_chat_tools.run_tool(call["name"], dict(args), attachments)
		if on_event:
			on_event({"type": "tool_result", "name": call["name"], "ok": not is_error})
		out.append({"name": call["name"], "input": args, "content": content, "is_error": is_error})
	return out


# ── saved questions (side panel) ────────────────────────────────────────────


def saved_questions(settings, limit=30):
	"""Enabled, unexpired recipes as side-panel buttons: [{name, question, params}], most reused
	first. Every user's questions are offered, like the reuse itself."""
	if not settings.enable_query_cache:
		return []
	filters = {"enabled": 1}
	if cint(settings.cache_expiry_days):
		filters["modified"] = [">=", add_to_date(now_datetime(), days=-cint(settings.cache_expiry_days))]
	out, seen = [], set()
	for row in frappe.get_all(
		CACHE,
		filters=filters,
		fields=["name", "question", "recipe"],
		order_by="hits desc, modified desc",
		limit=200,
	):
		key = (row.question or "").strip().casefold()
		if not key or key in seen:
			continue
		seen.add(key)
		out.append(
			{
				"name": row.name,
				"question": row.question,
				"params": params(row.question, json.loads(row.recipe or "[]")),
			}
		)
		if len(out) >= limit:
			break
	return out


def params(question, recipe):
	"""What a saved question asks for before it re-runs: [{key, label, was}], first value per key."""
	keys = {**PARAM_KEYS, **(DATE_KEYS if FIXED_DATE.search(question or "") else {})}
	found = {}
	for call in recipe:
		_collect(call.get("input"), keys, found)
	return [{"key": k, "label": keys[k], "was": v} for k, v in found.items()]


def _collect(args, keys, found):
	if not isinstance(args, dict):
		return
	for k, v in args.items():
		if isinstance(v, dict):
			_collect(v, keys, found)
		elif k in keys and isinstance(v, str) and v.strip() and v.strip().lower() != "all":
			found.setdefault(k, v)


def _apply(args, values):
	"""Swap the user's values into the recipe's args, nested ones (make_chart's args) included."""
	if not isinstance(args, dict):
		return args
	return {k: _apply(v, values) if isinstance(v, dict) else values.get(k, v) for k, v in args.items()}


def retitle(question, asked, values):
	"""The saved question with the user's values in place of the old ones, for the chat and the
	AI Rewrite reply. A value the question didn't spell out is added in brackets."""
	extra = []
	for key, value in values.items():
		was = asked[key]["was"]
		swapped = re.sub(re.escape(was), lambda _m: value, question, flags=re.IGNORECASE)
		if swapped == question:
			extra.append(f"{asked[key]['label'].split(' (')[0]}: {value}")
		question = swapped
	return f"{question} ({', '.join(extra)})" if extra else question


def rebase_dates(args, asked, today):
	"""Move the dates in tool args from the day the question was asked to today. A
	from_date / to_date pair that was a named period then (this month to date, last month,
	this week…) becomes the same period now; anything else shifts by the days in between."""
	if not isinstance(args, dict):
		return args
	out = {k: rebase_dates(v, asked, today) if isinstance(v, dict) else v for k, v in args.items()}
	shift = (today - asked).days
	paired = _is_date(out.get("from_date")) and _is_date(out.get("to_date"))
	for k, v in out.items():
		if _is_date(v) and not (paired and k in ("from_date", "to_date")):
			out[k] = str(add_days(getdate(v), shift))
	if paired:
		pair = (getdate(out["from_date"]), getdate(out["to_date"]))
		for period in PERIODS:
			if period(asked) == pair:
				out["from_date"], out["to_date"] = (str(d) for d in period(today))
				break
		else:
			out["from_date"], out["to_date"] = (str(add_days(d, shift)) for d in pair)
	return out


def _is_date(value):
	return isinstance(value, str) and bool(ISO_DATE.match(value))


def _monday(d):
	return add_days(d, -d.weekday())


def _fy_start(d):
	# Indian financial year: 1 April to 31 March.
	return getdate(f"{d.year if d.month >= 4 else d.year - 1}-04-01")


# Checked in order: on the 1st of a month "today" wins over "this month to date".
PERIODS = (
	lambda d: (d, d),
	lambda d: (get_first_day(d), d),
	lambda d: (get_first_day(d), get_last_day(d)),
	lambda d: (get_first_day(add_months(d, -1)), get_last_day(add_months(d, -1))),
	lambda d: (_monday(d), d),
	lambda d: (add_days(_monday(d), -7), add_days(_monday(d), -1)),
	lambda d: (_fy_start(d), d),
	lambda d: (getdate(f"{d.year}-01-01"), d),
)


# ── replies ─────────────────────────────────────────────────────────────────


def data_prompt(question, calls):
	"""The question plus the fresh tool results, for the AI Rewrite reply (no tools)."""
	blocks = [
		f"[{c['name']} {json.dumps(c['input'], ensure_ascii=False, default=str)}]\n"
		+ (f"ERROR: {c['content']}" if c["is_error"] else c["content"])
		for c in calls
	]
	return (
		f"{question}\n\n"
		"The tool results for this question were already fetched just now and are below. "
		"Answer from them only; no tools are available for this reply.\n\n" + "\n\n".join(blocks)
	)


def tables(calls):
	"""Tables Only reply: each tool result as markdown, no AI call."""
	parts = []
	for c in calls:
		title = f"**{c['name'].replace('_', ' ').capitalize()}**"
		if c["is_error"]:
			parts.append(f"{title}\n\n⚠ {c['content']}")
			continue
		data = json.loads(c["content"])
		if c["name"] in ai_chat_tools.OUTPUT_TOOLS:
			continue  # the file or chart is attached to the reply
		parts.append(f"{title}\n\n{_markdown(data)}")
	return "\n\n".join(parts) or "No data."


def _markdown(value, depth=0):
	if isinstance(value, list):
		if value and all(isinstance(v, dict) for v in value):
			return _list_table(value)
		return ", ".join(_cell("", v) for v in value) or "—"
	if not isinstance(value, dict):
		return _cell("", value)
	lines, grouped, sections = [], [], []
	for k, v in value.items():
		if isinstance(v, dict) and v and not any(isinstance(x, dict | list) for x in v.values()):
			# Sibling groups of plain figures (sales / returns / drafts) read best as one table.
			grouped.append({" ": _label(k), **v})
		elif isinstance(v, dict) and v:
			body = _markdown(v, depth + 1)
			sections.append(f"{'#' * min(depth + 4, 6)} {_label(k)}\n\n{body}")
		elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
			sections.append(f"_{_label(k)}_\n\n{_list_table(v)}")
		else:
			lines.append(f"- {_label(k)}: **{_cell(k, v)}**")
	table = _list_table(grouped) if grouped else ""
	return "\n\n".join(p for p in ("\n".join(lines), table, *sections) if p)


def _list_table(rows):
	headers = []
	for r in rows:
		headers += [k for k in r if k not in headers]
	return ai_chat_quick._table(
		[_label(h) for h in headers], [[_cell(h, r.get(h)) for h in headers] for r in rows]
	)


def _label(key):
	return str(key).replace("_", " ").capitalize()


def _cell(key, value):
	if value is None or value == "":
		return "—"
	if isinstance(value, bool):
		return "Yes" if value else "No"
	if isinstance(value, int | float):
		if "qty" not in str(key).lower() and MONEY_KEY.search(str(key)):
			return ai_chat_quick.inr(value)
		return ai_chat_quick.qty(value)
	if isinstance(value, dict | list):
		return json.dumps(value, ensure_ascii=False, default=str)[:120]
	return str(value).replace("\n", " ")
