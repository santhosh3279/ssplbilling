"""Runs one AI Chat turn on the Gemini API (google-genai, manual function calling with the
tools in ai_chat_tools.py). Same contract as ai_chat_runner.run: streams the same events
through on_event and returns {"text", "tools", "attachments", "error", "history", "duration_ms",
"input_tokens", "output_tokens"}.

"history" holds every Content exactly as Gemini returned it (JSON-dumped, thought signatures
included): Gemini 3 rejects function-calling history whose signatures were dropped.
"""

import json
import time

import frappe
import httpx
from google import genai
from google.genai import errors, types

from ssplbilling.api import ai_chat_tools as tools

SETTINGS = "SSPL Assistant Settings"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 10
CANCEL_POLL_SECONDS = 0.5


def run(prompt, history=None, on_event=None, is_cancelled=None, settings=None):
	settings = settings or frappe.get_cached_doc(SETTINGS)
	api_key = settings.get_password("google_api_key", raise_exception=False)
	if not api_key:
		frappe.throw(f"Set the Google API key in {SETTINGS}.")

	model = (settings.gemini_model or DEFAULT_MODEL).strip()
	config = types.GenerateContentConfig(
		system_instruction=tools.system_prompt(settings),
		tools=[
			types.Tool(
				function_declarations=[
					types.FunctionDeclaration(
						name=t["name"], description=t["description"], parameters_json_schema=t["input_schema"]
					)
					for t in tools.TOOLS
				]
			)
		],
		# We run the tools ourselves, as the chat user, and stream progress to the page.
		automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
	)

	client = genai.Client(api_key=api_key.strip())
	timeout = settings.timeout_seconds or 300
	started = time.monotonic()
	contents = [types.Content.model_validate(c) for c in history or []]
	contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
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
			parts, finish, halted, usage = [], None, False, None
			for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
				usage = chunk.usage_metadata or usage
				candidate = chunk.candidates[0] if chunk.candidates else None
				if candidate:
					finish = candidate.finish_reason or finish
					for part in (candidate.content.parts if candidate.content else None) or []:
						parts.append(part)
						if part.text and not part.thought:
							emit({"type": "text", "text": part.text})
				if stopped():
					halted = True
					break
			if usage:
				# Thinking tokens are billed as output.
				result["input_tokens"] += usage.prompt_token_count or 0
				result["output_tokens"] += (usage.candidates_token_count or 0) + (
					usage.thoughts_token_count or 0
				)
			if halted:
				# The partial reply is shown but not kept: history must hold complete turns only.
				break

			calls = [p.function_call for p in parts if p.function_call]
			if not parts:
				result["error"] = f"Gemini returned no answer ({finish or 'empty response'})."
				break
			if finish == types.FinishReason.MAX_TOKENS and calls:
				result["error"] = "The reply was cut off. Ask a narrower question."
				break
			contents.append(types.Content(role="model", parts=parts))
			if not calls:
				break

			responses = []
			for call in calls:
				args = dict(call.args or {})
				emit({"type": "tool", "name": call.name, "input": args})
				content, is_error = tools.run_tool(call.name, args, result["attachments"])
				emit({"type": "tool_result", "name": call.name, "ok": not is_error})
				response = {"error": content} if is_error else {"output": json.loads(content)}
				responses.append(
					types.Part(
						function_response=types.FunctionResponse(
							id=call.id, name=call.name, response=response
						)
					)
				)
			contents.append(types.Content(role="user", parts=responses))
		else:
			result["error"] = f"Stopped after {MAX_STEPS} tool rounds without a final answer."
	except errors.ClientError as e:
		# An invalid key comes back as 400 API_KEY_INVALID, a revoked one as 401/403.
		if e.code in (401, 403) or "API key" in (e.message or ""):
			result["error"] = f"The Google API key was rejected. Check it in {SETTINGS}."
		elif e.code == 429:
			result["error"] = "Gemini API rate limit or quota reached. Try again in a minute."
		else:
			result["error"] = f"Gemini API error {e.code}: {e.message}"
	except errors.ServerError as e:
		result["error"] = f"Gemini API error {e.code}: {e.message}"
	except httpx.TransportError:
		result["error"] = "Could not reach the Gemini API. Check the server's internet connection."

	if result["error"]:
		emit({"type": "error", "message": result["error"]})
	result["text"] = result["text"].strip()
	result["history"] = [c.model_dump(mode="json", exclude_none=True) for c in contents]
	result["duration_ms"] = int((time.monotonic() - started) * 1000)
	return result
