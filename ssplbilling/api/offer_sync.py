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
	_broadcast_offer_update({"type": "item", "item_code": getattr(doc, "item_code", doc.name)})


def publish_offer_items_update(doc, method=None):
	"""Offer-Items changed → tell the matching public offer page (by pageaddress) to refresh."""
	if not doc or not doc.name:
		return
	_broadcast_offer_update({"type": "offer", "pageaddress": getattr(doc, "pageaddress", None)})
