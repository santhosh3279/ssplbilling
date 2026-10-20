import frappe
import json


def get_rule_price_lists(rule_names):
	"""Map each Discount Rule name to its list of price lists (child table order)."""
	result = {name: [] for name in rule_names}
	if not rule_names:
		return result
	rows = frappe.get_all(
		"Discount Rule Price List",
		filters={"parent": ["in", list(rule_names)], "parenttype": "Discount Rule"},
		fields=["parent", "price_list"],
		order_by="idx asc",
		ignore_permissions=True,
	)
	for row in rows:
		result.setdefault(row.parent, []).append(row.price_list)
	return result


def _set_price_lists(doc, data):
	"""Fill doc.price_lists from payload `price_lists` (strings or dicts), falling back to legacy `price_list`."""
	values = data.get("price_lists")
	if values is None:
		values = [data.get("price_list")] if data.get("price_list") else []
	doc.set("price_lists", [])
	for value in values:
		price_list = value.get("price_list") if isinstance(value, dict) else value
		if price_list:
			doc.append("price_lists", {"price_list": price_list})


@frappe.whitelist()
def get_discount_rules(query=""):
	query = (query or "").strip()
	filters = {}
	if query:
		filters = [
			["Discount Rule", "rule_name", "like", f"%{query}%"],
			["Discount Rule", "product_group", "like", f"%{query}%"]
		]

	rules = frappe.get_all(
		"Discount Rule",
		filters=filters,
		fields=[
			"name", "rule_name", "price_list", "discount_type", "applies_to",
			"product_group", "min_quantity", "free_quantity", "recursive",
			"percentage_discount", "custom_logic_type", "start_date", "end_date", "enabled",
		],
		order_by="rule_name asc",
	)
	price_lists = get_rule_price_lists([r["name"] for r in rules])
	for rule in rules:
		rule["price_lists"] = price_lists.get(rule["name"], [])
		rule["items"] = frappe.get_all(
			"Discount Rule Item",
			filters={"parent": rule["name"]},
			fields=["item_code", "item_name", "uom"],
			order_by="idx asc",
		)
		rule["custom_logic_table"] = frappe.get_all(
			"Discount Rule Custom Logic",
			filters={"parent": rule["name"]},
			fields=["min_quantity", "nos", "percentage"],
			order_by="idx asc",
		)
		rule["custom_logic_rows"] = rule["custom_logic_table"]
		rule["x_to_y_table"] = frappe.get_all(
			"Discount Rule X to Y",
			filters={"parent": rule["name"]},
			fields=["item_code", "item_name", "min_quantity", "free_item_code", "free_item_name", "free_item_quantity", "free_item_price"],
			order_by="idx asc",
		)
	return rules


@frappe.whitelist()
def get_discount_rule(name):
	doc = frappe.get_doc("Discount Rule", name)
	doc_dict = doc.as_dict()
	doc_dict["price_lists"] = [d.price_list for d in doc.price_lists]
	doc_dict["items"] = [d.as_dict() for d in doc.items]
	doc_dict["custom_logic_table"] = [d.as_dict() for d in doc.custom_logic_table]
	doc_dict["custom_logic_rows"] = doc_dict["custom_logic_table"]
	doc_dict["x_to_y_table"] = [d.as_dict() for d in doc.x_to_y_table] if doc.get("x_to_y_table") else []
	return doc_dict


@frappe.whitelist()
def create_discount_rule(data):
	if isinstance(data, str):
		data = json.loads(data)

	doc = frappe.new_doc("Discount Rule")
	doc.rule_name = data.get("rule_name")
	doc.enabled = int(data.get("enabled", 1))
	_set_price_lists(doc, data)
	doc.discount_type = data.get("discount_type")
	doc.applies_to = data.get("applies_to")
	doc.product_group = data.get("product_group")
	doc.start_date = data.get("start_date")
	doc.end_date = data.get("end_date")
	doc.min_quantity = float(data.get("min_quantity") or 0.0)
	doc.free_quantity = float(data.get("free_quantity") or 0.0)
	doc.recursive = int(data.get("recursive") or 0)
	doc.percentage_discount = float(data.get("percentage_discount") or 0.0)
	doc.custom_logic_type = data.get("custom_logic_type")

	if data.get("items"):
		for item in data.get("items"):
			doc.append("items", {
				"item_code": item.get("item_code"),
				"item_name": item.get("item_name"),
				"uom": item.get("uom")
			})

	if data.get("custom_logic_table") or data.get("custom_logic_rows"):
		rows = data.get("custom_logic_table") or data.get("custom_logic_rows") or []
		for row in rows:
			doc.append("custom_logic_table", {
				"min_quantity": float(row.get("min_quantity") or 0.0),
				"nos": float(row.get("nos") or 0.0),
				"percentage": float(row.get("percentage") or 0.0)
			})

	if data.get("x_to_y_table"):
		for row in data.get("x_to_y_table"):
			doc.append("x_to_y_table", {
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name"),
				"min_quantity": float(row.get("min_quantity") or 0.0),
				"free_item_code": row.get("free_item_code"),
				"free_item_name": row.get("free_item_name"),
				"free_item_quantity": float(row.get("free_item_quantity") or 0.0),
				"free_item_price": float(row.get("free_item_price") or 0.0)
			})

	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def update_discount_rule(data):
	if isinstance(data, str):
		data = json.loads(data)

	original_name = data.get("name")
	new_rule_name = data.get("rule_name")

	if original_name and new_rule_name and original_name != new_rule_name:
		# DB collation is case-insensitive: a case-only rename matches this same record.
		existing = frappe.db.exists("Discount Rule", new_rule_name)
		if existing and existing != original_name:
			frappe.throw(f"Discount Rule with name '{new_rule_name}' already exists.")
		from frappe.model.rename_doc import rename_doc as _rename_doc
		_rename_doc("Discount Rule", original_name, new_rule_name, ignore_permissions=True)
		original_name = new_rule_name

	doc = frappe.get_doc("Discount Rule", original_name)
	doc.rule_name = new_rule_name
	doc.enabled = int(data.get("enabled", 1))
	_set_price_lists(doc, data)
	doc.discount_type = data.get("discount_type")
	doc.applies_to = data.get("applies_to")
	doc.product_group = data.get("product_group")
	doc.start_date = data.get("start_date")
	doc.end_date = data.get("end_date")
	doc.min_quantity = float(data.get("min_quantity") or 0.0)
	doc.free_quantity = float(data.get("free_quantity") or 0.0)
	doc.recursive = int(data.get("recursive") or 0)
	doc.percentage_discount = float(data.get("percentage_discount") or 0.0)
	doc.custom_logic_type = data.get("custom_logic_type")

	doc.set("items", [])
	if data.get("items"):
		for item in data.get("items"):
			doc.append("items", {
				"item_code": item.get("item_code"),
				"item_name": item.get("item_name"),
				"uom": item.get("uom")
			})

	doc.set("custom_logic_table", [])
	rows = data.get("custom_logic_table") or data.get("custom_logic_rows") or []
	if rows:
		for row in rows:
			doc.append("custom_logic_table", {
				"min_quantity": float(row.get("min_quantity") or 0.0),
				"nos": float(row.get("nos") or 0.0),
				"percentage": float(row.get("percentage") or 0.0)
			})

	doc.set("x_to_y_table", [])
	if data.get("x_to_y_table"):
		for row in data.get("x_to_y_table"):
			doc.append("x_to_y_table", {
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name"),
				"min_quantity": float(row.get("min_quantity") or 0.0),
				"free_item_code": row.get("free_item_code"),
				"free_item_name": row.get("free_item_name"),
				"free_item_quantity": float(row.get("free_item_quantity") or 0.0),
				"free_item_price": float(row.get("free_item_price") or 0.0)
			})

	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def delete_discount_rule(name):
	frappe.delete_doc("Discount Rule", name, ignore_permissions=True)
	return {"status": "success"}


@frappe.whitelist()
def toggle_discount_rule_enabled(name, enabled):
	frappe.db.set_value("Discount Rule", name, "enabled", int(enabled))
	return {"name": name, "enabled": int(enabled)}


@frappe.whitelist()
def get_discount_rule_metadata():
	price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name"])
	item_groups = frappe.get_all("Item Group", fields=["name"])
	return {
		"price_lists": [p.name for p in price_lists],
		"item_groups": [ig.name for ig in item_groups]
	}


def publish_discount_rule_update(doc, method=None):
	"""Publish a realtime update event when a Discount Rule is created, updated, or deleted."""
	if not doc or not doc.name:
		return

	def _emit():
		frappe.publish_realtime("discount_rule_update", {"name": doc.name})

	frappe.db.after_commit.add(_emit)
