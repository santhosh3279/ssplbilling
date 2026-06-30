import frappe
from frappe.realtime import get_doctype_room

# Fields whose changes are relevant to the frontend item cache
_WATCHED_FIELDS = (
	"item_name",
	"item_print_name",
	"disabled",
	"is_sales_item",
	"standard_rate",
	"stock_uom",
)


def _relevant_change(doc):
	"""Return True if this save touched something the frontend item cache cares about."""
	if doc.flags.in_insert:
		return True
	before = doc.get_doc_before_save()
	if not before:
		return True
	for field in _WATCHED_FIELDS:
		if doc.has_value_changed(field):
			return True
	# Barcodes child table
	old_barcodes = {row.barcode for row in (before.barcodes or [])}
	new_barcodes = {row.barcode for row in (doc.barcodes or [])}
	return old_barcodes != new_barcodes


def on_item_save(doc, method):
	"""Broadcast item_cache_invalidated to all browsers after an Item is saved."""
	if not _relevant_change(doc):
		frappe.logger("ssplbilling").info(f"item_realtime: {doc.item_code} saved but no relevant change, skipping")
		return
	frappe.logger("ssplbilling").info(f"item_realtime: publishing item_cache_invalidated for {doc.item_code}")
	frappe.publish_realtime(
		event="item_cache_invalidated",
		message={"item_code": doc.item_code, "action": "save"},
		room=get_doctype_room("Item"),
		after_commit=True,
	)


def on_item_trash(doc, method):
	"""Broadcast item_cache_invalidated to all browsers after an Item is deleted."""
	frappe.publish_realtime(
		event="item_cache_invalidated",
		message={"item_code": doc.item_code, "action": "delete"},
		room=get_doctype_room("Item"),
		after_commit=True,
	)
