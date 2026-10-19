import frappe


def execute():
	"""Copy the old single Discount Rule.price_list into the new price_lists child table."""
	rules = frappe.get_all("Discount Rule", filters={"price_list": ["is", "set"]}, fields=["name", "price_list"])
	for rule in rules:
		if frappe.db.exists("Discount Rule Price List", {"parent": rule.name, "parenttype": "Discount Rule"}):
			continue
		frappe.get_doc(
			{
				"doctype": "Discount Rule Price List",
				"parent": rule.name,
				"parenttype": "Discount Rule",
				"parentfield": "price_lists",
				"idx": 1,
				"price_list": rule.price_list,
			}
		).db_insert()
