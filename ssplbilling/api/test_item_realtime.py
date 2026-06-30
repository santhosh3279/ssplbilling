"""
Diagnostic test for item_realtime socket.io pipeline.
Run with: bench --site erp.localhost execute ssplbilling.api.test_item_realtime.run_test
         bench --site erp.localhost execute ssplbilling.api.test_item_realtime.test_actual_save
"""
import frappe


def run_test():
	results = {}

	# ── Step 1: Find any enabled sales item ──────────────────────────────────
	item_code = frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "item_code")
	if not item_code:
		return {"error": "No enabled sales item found"}
	results["item_code"] = item_code

	# ── Step 2: Load document, simulate a watched-field change ────────────────
	doc = frappe.get_doc("Item", item_code)
	original_name = doc.item_name

	# Check what _relevant_change returns on the live doc
	from ssplbilling.api.item_realtime import _relevant_change, _WATCHED_FIELDS

	# Simulate: force _doc_before_save so has_value_changed works
	doc._doc_before_save = doc.get_doc_before_save()
	results["has_doc_before_save"] = doc._doc_before_save is not None
	results["watched_fields"] = list(_WATCHED_FIELDS)

	# Temporarily modify item_name to trigger the check
	doc.item_name = original_name + "_TEST"
	results["has_value_changed_item_name"] = doc.has_value_changed("item_name")
	results["relevant_change_would_fire"] = _relevant_change(doc)

	# Restore
	doc.item_name = original_name

	# ── Step 3: Directly call publish_realtime and confirm no exception ───────
	try:
		frappe.publish_realtime(
			event="item_cache_invalidated",
			message={"item_code": item_code, "action": "test", "source": "test_item_realtime"},
			after_commit=False,
		)
		results["publish_realtime_ok"] = True
	except Exception as e:
		results["publish_realtime_ok"] = False
		results["publish_realtime_error"] = str(e)

	# ── Step 4: Check the hook is registered in doc_events ───────────────────
	import frappe.hooks as hooks_mod

	doc_events = getattr(hooks_mod, "doc_events", {})
	app_hooks = frappe.get_hooks("doc_events", app_name="ssplbilling")
	results["item_hook_registered"] = "Item" in app_hooks
	results["item_hook_after_save"] = app_hooks.get("Item", {}).get("after_save")

	# ── Step 5: Confirm site name (used as socket.io namespace) ──────────────
	results["site_name"] = frappe.local.site
	results["socketio_port"] = frappe.conf.get("socketio_port", 9000)

	return results
