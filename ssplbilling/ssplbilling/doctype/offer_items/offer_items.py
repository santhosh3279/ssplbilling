# -*- coding: utf-8 -*-
# Copyright (c) 2026, SSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OfferItems(Document):
	def validate(self):
		if not self.get("items") and not self.get("sub_catalogues"):
			frappe.throw(_("Add at least one Item or Sub Folder to the catalogue."))
		self.validate_sub_catalogues()

	def validate_sub_catalogues(self):
		seen = set()
		for row in self.get("sub_catalogues") or []:
			if row.offer == self.name:
				frappe.throw(_("Row {0}: a catalogue cannot be a sub-folder of itself.").format(row.idx))
			if row.offer in seen:
				frappe.throw(_("Row {0}: {1} is already added as a sub-folder.").format(row.idx, row.offer))
			seen.add(row.offer)
		if self.name and seen and self.name in _descendants(seen):
			frappe.throw(_("Sub-folders cannot contain this catalogue again (circular folder link)."))


def _descendants(roots):
	"""All catalogues reachable from roots through sub-folder links."""
	found, frontier = set(), set(roots)
	while frontier:
		found |= frontier
		rows = frappe.get_all(
			"Offer-Sub Catalogue",
			filters={"parenttype": "Offer-Items", "parent": ["in", list(frontier)]},
			pluck="offer",
		)
		frontier = set(rows) - found
	return found
