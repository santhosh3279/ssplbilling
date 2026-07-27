import time

import frappe

from ssplbilling.api.license_api import _load_license_status

TAB_KEY_PREFIX = "ssplbilling:active_tab:"
# Generous vs. the 20s frontend heartbeat: backgrounded browser tabs get their
# setInterval throttled (sometimes to 60s+), so a short TTL would expire and
# free a still-open tab's own slot before its next heartbeat lands.
TAB_TTL_SECONDS = 120


def _active_tab_ids():
	"""List currently live tab ids (Redis auto-expires stale ones via TAB_TTL_SECONDS)."""
	raw_keys = frappe.cache().get_keys(TAB_KEY_PREFIX)
	db_prefix = f"{frappe.local.conf.get('db_name')}|"

	tab_ids = []
	for key in raw_keys:
		key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
		if key_str.startswith(db_prefix):
			key_str = key_str[len(db_prefix):]
		if key_str.startswith(TAB_KEY_PREFIX):
			tab_ids.append(key_str[len(TAB_KEY_PREFIX):])
	return tab_ids


def _max_tabs_from_license():
	"""Verified (signed) tab cap from license.json, or None if unset/unlimited."""
	return _load_license_status().get("max_tabs")


@frappe.whitelist()
def register_tab(tab_id):
	"""Register or heartbeat a browser tab. New tabs are rejected once the
	site-wide concurrent count reaches the license's max_tabs; an already
	registered tab_id just renews its TTL and is never rejected."""
	if not tab_id:
		return {"status": "error", "message": "tab_id is required"}

	cache_key = f"{TAB_KEY_PREFIX}{tab_id}"
	max_tabs = _max_tabs_from_license()
	is_new_tab = not frappe.cache().get_value(cache_key)

	if max_tabs is not None and is_new_tab:
		active_count = len(_active_tab_ids())
		if active_count >= max_tabs:
			return {"status": "limit_reached", "active_tabs": active_count, "max_tabs": max_tabs}

	frappe.cache().set_value(
		cache_key,
		f"{frappe.session.user}|{time.time()}",
		expires_in_sec=TAB_TTL_SECONDS,
	)
	return {"status": "ok", "active_tabs": len(_active_tab_ids()), "max_tabs": max_tabs}


@frappe.whitelist()
def release_tab(tab_id):
	"""Free a tab slot immediately on tab close/logout instead of waiting for TTL expiry."""
	if not tab_id:
		return {"status": "error", "message": "tab_id is required"}

	frappe.cache().delete_value(f"{TAB_KEY_PREFIX}{tab_id}")
	return {"status": "ok"}
