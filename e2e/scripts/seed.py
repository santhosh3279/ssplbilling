"""Create (or remove) the tester bot's own user, customers and items on a dev site.

Run with the bench's Python, from anywhere:

    ../../../env/bin/python scripts/seed.py                 # create / refresh test data, write .env
    ../../../env/bin/python scripts/seed.py --clean         # delete the bot's draft invoices only
    ../../../env/bin/python scripts/seed.py --purge         # delete drafts, test data and the bot user

Everything it makes is named TESTBOT…, so nothing a real user owns is touched. It refuses to run on
a site that is not in developer mode unless --force is given.
"""

import argparse
import os
import secrets
import sys

E2E_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_DIR = os.path.abspath(os.path.join(E2E_DIR, "..", "..", ".."))
ENV_FILE = os.path.join(E2E_DIR, ".env")

BOT_USER = "testbot@sspl.local"
PREFIX = "TESTBOT"
# name -> party modifier (Customer.pricelist_multiplication_factor)
CUSTOMERS = {
	f"{PREFIX} PLAIN": 1,
	f"{PREFIX} MARKUP": 1.05,
	f"{PREFIX} DISCOUNT": 0.9,
}
# item_code -> (item_name, wholesale rate, retail rate)
ITEMS = {
	f"{PREFIX}-A": (f"{PREFIX} Item A", 98.60, 110),
	f"{PREFIX}-B": (f"{PREFIX} Item B", 250, 275),
	f"{PREFIX}-C": (f"{PREFIX} Item C", 40, 45),
}


def read_env():
	values = {}
	if os.path.exists(ENV_FILE):
		for line in open(ENV_FILE):
			if "=" in line and not line.lstrip().startswith("#"):
				key, value = line.rstrip("\n").split("=", 1)
				values[key.strip()] = value
	return values


def write_env(values):
	with open(ENV_FILE, "w") as f:
		f.write("# Written by scripts/seed.py. Untracked: never commit this file.\n")
		for key, value in values.items():
			f.write(f"{key}={value}\n")
	os.chmod(ENV_FILE, 0o600)


def pick_series(frappe, settings, template_row):
	"""Three of the template user's Sales Invoice series: tax exempt, GST inclusive, GST exclusive."""
	allowed = {s.strip() for s in (template_row.allowed_series_seperated_by_comma or "").split(",") if s.strip()}
	picked = {}
	for row in settings.billing_series:
		prefix = row.series.split(".")[0]
		if row.is_return or row.price_list == "Buying" or (allowed and prefix not in allowed):
			continue
		if not frappe.db.exists("Sales Invoice", {"naming_series": row.series}):
			continue  # a series of another doctype (Quotation, Sales Order, …)
		exempt = "exempt" in (row.tax_template or "").lower()
		kind = "exempt" if exempt else ("inclusive" if row.tax_type_incl else "exclusive")
		picked.setdefault(kind, row)
	return picked


def seed(frappe, args):
	settings = frappe.get_single("SSPL Billing Settings")
	template = next((r for r in settings.user_series if r.biller and r.user != BOT_USER), None)
	if not template:
		sys.exit("No biller row in SSPL Billing Settings > User Series to copy the bot's defaults from.")
	series = pick_series(frappe, settings, template)
	if "exempt" not in series:
		sys.exit(f"{template.user} has no tax exempt Sales Invoice series to test with.")

	# --- user
	env = read_env()
	password = env.get("E2E_PASSWORD") or secrets.token_urlsafe(18)
	if frappe.db.exists("User", BOT_USER):
		user = frappe.get_doc("User", BOT_USER)
	else:
		user = frappe.new_doc("User")
		user.email = BOT_USER
		user.first_name = "Tester"
		user.last_name = "Bot"
		user.send_welcome_email = 0
	user.enabled = 1
	user.new_password = password
	user.flags.ignore_password_policy = True
	user.save(ignore_permissions=True)
	user.add_roles(*[r for r in frappe.get_roles(template.user) if r not in ("All", "Guest", "Desk User")])

	# --- billing defaults: the template biller's row, limited to the series under test
	row = next((r for r in settings.user_series if r.user == BOT_USER), None) or settings.append("user_series", {})
	for field in frappe.get_meta("USER SERIES").fields:
		if field.fieldtype not in ("Section Break", "Column Break"):
			row.set(field.fieldname, template.get(field.fieldname))
	row.user = BOT_USER
	row.allowed_series_seperated_by_comma = ", ".join(r.series.split(".")[0] for r in series.values())
	row.admin, row.cashier, row.accounts, row.biller = 0, 0, 0, 1
	settings.save(ignore_permissions=True)

	# --- customers
	for name, modifier in CUSTOMERS.items():
		doc = frappe.get_doc("Customer", name) if frappe.db.exists("Customer", name) else frappe.new_doc("Customer")
		doc.customer_name = name
		doc.customer_type = "Individual"
		doc.customer_group = doc.customer_group or frappe.db.get_value("Customer Group", {"is_group": 0})
		doc.territory = doc.territory or frappe.db.get_value("Territory", {"is_group": 0})
		doc.gst_category = "Unregistered"
		doc.pricelist_multiplication_factor = modifier
		doc.save(ignore_permissions=True)

	# --- items, priced in every selling price list the series under test use
	price_lists = sorted({r.price_list for r in series.values()})
	sample = frappe.db.get_value(
		"Item", {"disabled": 0, "is_stock_item": 1, "gst_hsn_code": ["is", "set"]}, ["name", "item_group", "gst_hsn_code"], as_dict=True
	)
	sample_taxes = frappe.get_all("Item Tax", filters={"parent": sample.name}, fields=["item_tax_template"], order_by="idx")
	for code, (item_name, wholesale, retail) in ITEMS.items():
		if frappe.db.exists("Item", code):
			item = frappe.get_doc("Item", code)
		else:
			item = frappe.new_doc("Item")
			item.item_code = code
			item.item_group = sample.item_group
			item.stock_uom = "Nos"
			item.gst_hsn_code = sample.gst_hsn_code
			item.is_stock_item = 1
			for tax in sample_taxes:
				item.append("taxes", {"item_tax_template": tax.item_tax_template})
			item.append("barcodes", {"barcode": code})
		item.item_name = item_name
		item.disabled = 0
		item.save(ignore_permissions=True)
		for price_list in price_lists:
			rate = wholesale if price_list.upper().startswith("W") else retail
			existing = frappe.db.get_value("Item Price", {"item_code": code, "price_list": price_list, "uom": ["in", ["", None, "Nos"]]})
			if existing:
				frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
			else:
				frappe.get_doc(
					{"doctype": "Item Price", "item_code": code, "price_list": price_list, "price_list_rate": rate}
				).insert(ignore_permissions=True)

	frappe.db.commit()
	env.update(
		{
			"E2E_BASE_URL": env.get("E2E_BASE_URL") or args.base_url,
			"E2E_SITE": args.site,
			"E2E_USER": BOT_USER,
			"E2E_PASSWORD": password,
			"E2E_COMPANY": row.company or "",
			"E2E_SERIES_EXEMPT": series["exempt"].series,
			"E2E_SERIES_INCLUSIVE": series["inclusive"].series if "inclusive" in series else "",
			"E2E_SERIES_EXCLUSIVE": series["exclusive"].series if "exclusive" in series else "",
		}
	)
	for kind, r in series.items():
		env[f"E2E_PRICE_LIST_{kind.upper()}"] = r.price_list
	write_env(env)
	print(f"Seeded {args.site}: user {BOT_USER}, {len(CUSTOMERS)} customers, {len(ITEMS)} items.")
	print("Series:", {k: f"{r.series} ({r.price_list})" for k, r in series.items()})
	print(f"Login details written to {ENV_FILE}")


def clean(frappe):
	"""Delete every draft the bot left behind. Only drafts, only for TESTBOT customers."""
	deleted = 0
	for doctype in ("Sales Invoice", "Sales Order", "Quotation"):
		party = "party_name" if doctype == "Quotation" else "customer"
		for name in frappe.get_all(doctype, filters={party: ["like", f"{PREFIX}%"], "docstatus": 0}, pluck="name"):
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
			deleted += 1
	frappe.db.commit()
	print(f"Deleted {deleted} draft document(s) of {PREFIX} customers.")


def purge(frappe):
	clean(frappe)
	settings = frappe.get_single("SSPL Billing Settings")
	settings.user_series = [r for r in settings.user_series if r.user != BOT_USER]
	settings.save(ignore_permissions=True)
	for doctype, names in (("Item Price", None), ("Item", list(ITEMS)), ("Customer", list(CUSTOMERS)), ("User", [BOT_USER])):
		if doctype == "Item Price":
			names = frappe.get_all("Item Price", filters={"item_code": ["in", list(ITEMS)]}, pluck="name")
		for name in names:
			if frappe.db.exists(doctype, name):
				try:
					frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
				except Exception as e:
					print(f"Kept {doctype} {name}: {e}")
	frappe.db.commit()
	if os.path.exists(ENV_FILE):
		os.remove(ENV_FILE)
	print("Removed the bot user and its test data.")


def main():
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--site", default=os.environ.get("E2E_SITE") or read_env().get("E2E_SITE") or "erp.localhost")
	parser.add_argument("--base-url", default="http://erp.localhost:8001")
	parser.add_argument("--clean", action="store_true", help="delete the bot's draft documents")
	parser.add_argument("--purge", action="store_true", help="delete drafts, test data and the bot user")
	parser.add_argument("--force", action="store_true", help="run even when the site is not in developer mode")
	args = parser.parse_args()

	os.chdir(os.path.join(BENCH_DIR, "sites"))
	import frappe

	frappe.init(site=args.site, sites_path=".")
	frappe.connect()
	try:
		if not frappe.conf.developer_mode and not args.force:
			sys.exit(f"{args.site} is not in developer mode. The tester bot is for dev sites; use --force to override.")
		frappe.set_user("Administrator")
		if args.purge:
			purge(frappe)
		elif args.clean:
			clean(frappe)
		else:
			seed(frappe, args)
	finally:
		frappe.destroy()


if __name__ == "__main__":
	main()
