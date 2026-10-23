import json

import frappe


def _rows(doc):
	return [
		{"pricelist": r.pricelist, "percentage": float(r.percentage or 0)}
		for r in doc.get("pricelist_percentages") or []
	]


@frappe.whitelist()
def get_competitive_items():
	"""List Competitive Items with how many items link to each."""
	items = frappe.get_all("Competitive Item", fields=["name", "modified"], order_by="name asc")
	counts = {
		r.custom_competitive_item: r.cnt
		for r in frappe.get_all(
			"Item",
			filters={"custom_competitive_item": ["is", "set"]},
			fields=["custom_competitive_item", {"COUNT": "name", "as": "cnt"}],
			group_by="custom_competitive_item",
		)
	}
	for i in items:
		i["item_count"] = counts.get(i.name, 0)
	return items


@frappe.whitelist()
def get_competitive_item(name):
	"""Return one Competitive Item with its pricelist percentages and linked items."""
	doc = frappe.get_doc("Competitive Item", name)
	return {
		"name": doc.name,
		"pricelist_percentages": _rows(doc),
		"items": frappe.get_all(
			"Item",
			filters={"custom_competitive_item": doc.name},
			fields=["name as item_code", "item_name"],
			order_by="item_name asc",
			limit=200,
		),
	}


@frappe.whitelist()
def save_competitive_item(data):
	"""Create or update (and rename) a Competitive Item with its percentage rows."""
	if isinstance(data, str):
		data = json.loads(data)

	new_name = (data.get("competitive_item_name") or "").strip()
	if not new_name:
		frappe.throw("Competitive Item Name is required")

	old_name = data.get("name")
	if old_name:
		if old_name != new_name:
			# DB collation is case-insensitive: a case-only rename matches this same record.
			existing = frappe.db.exists("Competitive Item", new_name)
			if existing and existing != old_name:
				frappe.throw(f"Competitive Item '{new_name}' already exists.")
			from frappe.model.rename_doc import rename_doc as _rename_doc
			_rename_doc("Competitive Item", old_name, new_name, ignore_permissions=True)
		doc = frappe.get_doc("Competitive Item", new_name)
	else:
		if frappe.db.exists("Competitive Item", new_name):
			frappe.throw(f"Competitive Item '{new_name}' already exists.")
		doc = frappe.new_doc("Competitive Item")
		doc.competitive_item_name = new_name

	doc.competitive_item_name = new_name
	doc.set("pricelist_percentages", [])
	for p in data.get("pricelist_percentages") or []:
		if p.get("pricelist") and p.get("percentage") not in (None, ""):
			doc.append("pricelist_percentages", {"pricelist": p["pricelist"], "percentage": str(p["percentage"])})
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "pricelist_percentages": _rows(doc)}


@frappe.whitelist()
def delete_competitive_item(name):
	"""Delete a Competitive Item; refused while any Item still links to it."""
	linked = frappe.db.count("Item", {"custom_competitive_item": name})
	if linked:
		frappe.throw(f"{linked} item(s) still use '{name}'. Unlink them first.")
	frappe.delete_doc("Competitive Item", name, ignore_permissions=True)
	return {"deleted": name}
