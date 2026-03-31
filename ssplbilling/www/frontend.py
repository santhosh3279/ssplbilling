import frappe
import os

no_cache = 1


def get_context(context):
	assets_dir = os.path.join(
		frappe.get_site_path(), "assets", "ssplbilling", "frontend", "assets"
	)
	files = os.listdir(assets_dir)
	css = next((f for f in files if f.startswith("index.") and f.endswith(".css")), None)
	js = next((f for f in files if f.startswith("index.") and f.endswith(".js")), None)

	context.spa_css = f"/assets/ssplbilling/frontend/assets/{css}" if css else ""
	context.spa_js = f"/assets/ssplbilling/frontend/assets/{js}" if js else ""
