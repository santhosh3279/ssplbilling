import frappe
import json
import os

no_cache = 1

ASSET_URL = "/assets/ssplbilling/frontend/"


def get_context(context):
	frontend_dir = os.path.join(os.path.dirname(frappe.get_site_path()), "assets", "ssplbilling", "frontend")
	manifest = _read_manifest(frontend_dir)
	if manifest:
		_set_from_manifest(context, manifest)
	else:
		_set_from_listing(context, os.path.join(frontend_dir, "assets"))
	context.csrf_token = frappe.session.data.csrf_token


def _read_manifest(frontend_dir):
	try:
		with open(os.path.join(frontend_dir, "manifest.json")) as f:
			return json.load(f)
	except (OSError, ValueError):
		return None


def _set_from_manifest(context, manifest):
	entry = manifest["index.html"]
	# main.js imports App + router right after the server-time call; preloading them (and every chunk
	# they statically import) lets the browser download in parallel instead of after that round trip.
	preload, pending = [], list(entry.get("imports", [])) + list(entry.get("dynamicImports", []))
	seen = {"index.html"}  # shared code hoisted into the entry makes chunks import it back
	while pending:
		key = pending.pop(0)
		if key in seen or key not in manifest:
			continue
		seen.add(key)
		preload.append(ASSET_URL + manifest[key]["file"])
		pending.extend(manifest[key].get("imports", []))

	context.spa_js = ASSET_URL + entry["file"]
	context.spa_css = [ASSET_URL + f for f in entry.get("css", [])]
	context.spa_preload = preload


def _set_from_listing(context, assets_dir):
	# Builds without a manifest emitted a single index.<hash>.js / .css pair.
	files = os.listdir(assets_dir)
	css = next((f for f in files if f.startswith("index.") and f.endswith(".css")), None)
	js = next((f for f in files if f.startswith("index.") and f.endswith(".js")), None)

	context.spa_css = [f"{ASSET_URL}assets/{css}"] if css else []
	context.spa_js = f"{ASSET_URL}assets/{js}" if js else ""
	context.spa_preload = []
