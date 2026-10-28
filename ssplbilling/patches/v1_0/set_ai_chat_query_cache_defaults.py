import frappe

SETTINGS = "SSPL Assistant Settings"
DEFAULTS = {
	"enable_query_cache": 1,
	"cache_reply_mode": "AI Rewrite",
	"cache_match_threshold": 0.85,
	"cache_expiry_days": 30,
}


def execute():
	"""New fields on a Single don't get their defaults on an existing record: set them once."""
	for field, value in DEFAULTS.items():
		if frappe.db.get_single_value(SETTINGS, field) in (None, "", 0):
			frappe.db.set_single_value(SETTINGS, field, value)
