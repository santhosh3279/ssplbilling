import frappe


def execute():
	"""Purchase bills now mirror like sales bills (same series, `<name>/`), so the
	Purchase Mirroring Series table of Automatic Entries is gone."""
	if frappe.db.exists("DocType", "Purchase Mirroring Series"):
		frappe.delete_doc("DocType", "Purchase Mirroring Series", force=True, ignore_missing=True)
