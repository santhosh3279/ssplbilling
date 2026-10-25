import frappe
from frappe.realtime import get_website_room


def _broadcast_offer_update(payload):
	"""Broadcast to the WEBSITE room so guest (not-logged-in) offer pages receive it.

	The default publish_realtime target is the site room ("all"), which only System
	Users join — guests never do. The public offer page (`/offer/<pageaddress>`,
	allow_guest) is a guest socket, so we must publish to the website room, which
	every socket (guest included) joins. See frappe/realtime/handlers.js."""
	frappe.publish_realtime(
		"offer_page_update",
		payload,
		room=get_website_room(),
		after_commit=True,
	)


def publish_item_offer_update(doc, method=None):
	"""Item changed → tell any public offer page currently showing this item to refresh.

	The front-end gates on item_code, so a change to an item not in a given offer is a
	no-op for that page. Item is autonamed by item_code, so doc.name == doc.item_code,
	but we send item_code explicitly to stay correct if that ever changes."""
	if not doc or not doc.name:
		return
	# variant_of lets a page listing the template refresh when one of its variants is added or changed.
	_broadcast_offer_update({"type": "item", "item_code": getattr(doc, "item_code", doc.name),
		"variant_of": getattr(doc, "variant_of", None)})


def publish_offer_items_update(doc, method=None):
	"""Offer-Items changed → tell the matching public offer page (by pageaddress) to refresh."""
	if not doc or not doc.name:
		return
	_broadcast_offer_update({"type": "offer", "pageaddress": getattr(doc, "pageaddress", None)})


def publish_catalogue_stock_update(doc, method=None):
	"""Invalidate public stock after a committed stock ledger movement."""
	if doc and doc.item_code:
		queue_catalogue_stock_invalidation([doc.item_code])


def queue_catalogue_stock_invalidation(item_codes):
	"""Collect item codes whose public stock changed in this transaction; one
	offer_page_update {"type": "stock", "item_codes": [...]} goes out after commit.

	A 70-line bill used to send 70 messages (plus one per Stock Ledger Entry on submit)
	to every socket in the website room. Nothing is sent if the transaction rolls back."""
	pending = getattr(frappe.local, "_sspl_offer_stock_codes", None)
	if pending is None:
		pending = frappe.local._sspl_offer_stock_codes = {}
		frappe.db.after_commit.add(_flush_catalogue_stock_invalidation)
		frappe.db.after_rollback.add(_discard_catalogue_stock_invalidation)
	pending.update(dict.fromkeys(code for code in item_codes if code))


def _flush_catalogue_stock_invalidation():
	codes = list(getattr(frappe.local, "_sspl_offer_stock_codes", None) or {})
	frappe.local._sspl_offer_stock_codes = None
	if not codes:
		return
	payload = {"type": "stock", "item_codes": codes}
	if len(codes) == 1:
		payload["item_code"] = codes[0]  # pages loaded before item_codes existed read this
	# Already committed, so publish now rather than queueing for a commit that won't come.
	frappe.publish_realtime("offer_page_update", payload, room=get_website_room(), after_commit=False)


def _discard_catalogue_stock_invalidation():
	frappe.local._sspl_offer_stock_codes = None
