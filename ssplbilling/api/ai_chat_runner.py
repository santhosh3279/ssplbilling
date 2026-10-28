"""Runs one AI Chat turn on the Claude API (Messages API + the tools in ai_chat_tools.py).
ai_chat_runner_gemini.py is the same loop on the Gemini API; both emit the same events.

Tools run in-process as the chat user, so ERPNext role and user permissions apply to every
answer. Streams events through on_event:

	{"type": "text", "text": ...}                 assistant text delta
	{"type": "tool", "name": ..., "input": ...}
	{"type": "tool_result", "name": ..., "ok": bool}
	{"type": "error", "message": ...}

and returns {"text", "tools", "attachments", "error", "history", "duration_ms", "input_tokens",
"output_tokens"}. "history" is the raw message
list to replay next turn, kept verbatim (thinking blocks included) as the API requires.
"""

import time

import anthropic
import frappe

from ssplbilling.api import ai_chat_tools as tools

SETTINGS = "SSPL Assistant Settings"
DEFAULT_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 32000
MAX_STEPS = 10
CANCEL_POLL_SECONDS = 0.5
# Server-side refusal fallback ("default" routing) is accepted on these models only.
FALLBACK_MODELS = ("claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5")


def run(prompt, history=None, on_event=None, is_cancelled=None, settings=None):
	settings = settings or frappe.get_cached_doc(SETTINGS)
	api_key = settings.get_password("anthropic_api_key", raise_exception=False)
	if not api_key:
		frappe.throw(f"Set the Anthropic API key in {SETTINGS}.")

	model = (settings.claude_model or DEFAULT_MODEL).strip()
	params = {
		"model": model,
		"max_tokens": MAX_TOKENS,
		"system": tools.system_prompt(settings),
		"tools": tools.TOOLS,
		"cache_control": {"type": "ephemeral"},
		"output_config": {"effort": settings.claude_effort or "low"},
	}
	if model in FALLBACK_MODELS:
		params["betas"] = ["server-side-fallback-2026-07-01"]
		params["fallbacks"] = "default"

	client = anthropic.Anthropic(api_key=api_key.strip(), max_retries=2)
	timeout = settings.timeout_seconds or 300
	started = time.monotonic()
	messages = [*(history or []), {"role": "user", "content": prompt}]
	result = {
		"text": "",
		"tools": [],
		"attachments": [],
		"error": None,
		"input_tokens": 0,
		"output_tokens": 0,
	}

	def emit(ev):
		if ev["type"] == "text":
			result["text"] += ev["text"]
		elif ev["type"] == "tool":
			result["tools"].append({"name": ev["name"], "input": ev.get("input")})
		if on_event:
			on_event(ev)

	checked = {"at": 0.0}

	def stopped():
		if time.monotonic() - started > timeout:
			result["error"] = f"Timed out after {timeout}s"
			return True
		if is_cancelled and time.monotonic() - checked["at"] >= CANCEL_POLL_SECONDS:
			checked["at"] = time.monotonic()
			return bool(is_cancelled())
		return False

	try:
		for _ in range(MAX_STEPS):
			if result["text"] and not result["text"].endswith("\n\n"):
				emit({"type": "text", "text": "\n\n"})
			halted = False
			with client.beta.messages.stream(messages=messages, **params) as stream:
				for event in stream:
					if event.type == "text":
						emit({"type": "text", "text": event.text})
					if stopped():
						halted = True
						break
				if not halted:
					response = stream.get_final_message()
					usage = response.usage
					result["input_tokens"] += (
						usage.input_tokens
						+ (usage.cache_read_input_tokens or 0)
						+ (usage.cache_creation_input_tokens or 0)
					)
					result["output_tokens"] += usage.output_tokens
			if halted:
				# The partial reply is shown but not kept: history must hold complete turns only.
				break

			tool_uses = [b for b in response.content if b.type == "tool_use"]
			if response.stop_reason == "refusal":
				result["error"] = "Claude declined to answer this request."
				if not tool_uses:
					messages.append({"role": "assistant", "content": _echo_blocks(response.content)})
				break
			if response.stop_reason == "max_tokens" and tool_uses:
				result["error"] = "The reply was cut off. Ask a narrower question."
				break
			messages.append({"role": "assistant", "content": _echo_blocks(response.content)})
			if not tool_uses:
				break

			results = []
			for block in tool_uses:
				emit({"type": "tool", "name": block.name, "input": block.input})
				content, is_error = tools.run_tool(block.name, block.input, result["attachments"])
				emit({"type": "tool_result", "name": block.name, "ok": not is_error})
				results.append(
					{"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error}
				)
			messages.append({"role": "user", "content": results})
		else:
			result["error"] = f"Stopped after {MAX_STEPS} tool rounds without a final answer."
	except anthropic.AuthenticationError:
		result["error"] = f"The Anthropic API key was rejected. Check it in {SETTINGS}."
	except anthropic.RateLimitError:
		result["error"] = "Claude API rate limit reached. Try again in a minute."
	except anthropic.APIStatusError as e:
		result["error"] = f"Claude API error {e.status_code}: {e.message}"
	except anthropic.APIConnectionError:
		result["error"] = "Could not reach the Claude API. Check the server's internet connection."

	if result["error"]:
		emit({"type": "error", "message": result["error"]})
	result["text"] = result["text"].strip()
	result["history"] = messages
	result["duration_ms"] = int((time.monotonic() - started) * 1000)
	return result


def _echo_blocks(content):
	"""Content to append to history. After a mid-reply refusal fallback, only text blocks
	from before the last `fallback` marker may be sent back; everything after it echoes as is."""
	blocks = [b.to_dict() for b in content]
	marks = [i for i, b in enumerate(blocks) if b.get("type") == "fallback"]
	if not marks:
		return blocks
	cut = marks[-1]
	return [b for b in blocks[:cut] if b.get("type") == "text"] + blocks[cut:]
