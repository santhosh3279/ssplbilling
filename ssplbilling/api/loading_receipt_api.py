import frappe


@frappe.whitelist()
def search_loading_items(query=""):
	query = (query or "").strip()
	filters = {"disabled": 0} if not query else [
		["item_code", "like", f"%{query}%"],
		["or"],
		["item_name", "like", f"%{query}%"],
	]
	# simple OR search
	conditions = ""
	values = []
	if query:
		conditions = "WHERE (item_code LIKE %s OR item_name LIKE %s)"
		values = [f"%{query}%", f"%{query}%"]
	rows = frappe.db.sql(
		f"""
		SELECT item_code, item_name, uom, rate
		FROM `tabLoading Item`
		{conditions}
		ORDER BY item_name
		LIMIT 50
		""",
		values,
		as_dict=True,
	)
	return rows


@frappe.whitelist()
def create_loading_receipt(data):
	import json

	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.new_doc("Loading Receipt")
	doc.bill_no = d.get("bill_no", "")
	doc.date = d.get("date")
	doc.time = d.get("time")
	doc.customer = d.get("customer")
	doc.amount = d.get("amount") or 0
	for row in d.get("loading_items", []):
		doc.append(
			"loading_items",
			{
				"item": row.get("item"),
				"item_name": row.get("item_name"),
				"qty": row.get("qty") or 0,
				"rate": row.get("rate") or 0,
				"amount": row.get("amount") or 0,
			},
		)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def update_loading_receipt(data):
	import json

	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.get_doc("Loading Receipt", d["name"])
	doc.bill_no = d.get("bill_no", "")
	doc.date = d.get("date")
	doc.time = d.get("time")
	doc.customer = d.get("customer")
	doc.amount = d.get("amount") or 0
	doc.loading_items = []
	for row in d.get("loading_items", []):
		doc.append(
			"loading_items",
			{
				"item": row.get("item"),
				"item_name": row.get("item_name"),
				"qty": row.get("qty") or 0,
				"rate": row.get("rate") or 0,
				"amount": row.get("amount") or 0,
			},
		)
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def get_loading_receipts(query=""):
	query = (query or "").strip()
	conditions = ""
	values = []
	if query:
		conditions = "WHERE (lr.name LIKE %s OR lr.customer LIKE %s OR lr.bill_no LIKE %s)"
		values = [f"%{query}%", f"%{query}%", f"%{query}%"]
	rows = frappe.db.sql(
		f"""
		SELECT lr.name, lr.date, lr.bill_no, lr.customer, lr.customer_name, lr.total
		FROM `tabLoading Receipt` lr
		{conditions}
		ORDER BY lr.creation DESC
		LIMIT 50
		""",
		values,
		as_dict=True,
	)
	return rows


@frappe.whitelist()
def get_loading_receipt(name):
	doc = frappe.get_doc("Loading Receipt", name)
	return {
		"name": doc.name,
		"date": str(doc.date),
		"time": str(doc.time) if doc.time else "",
		"bill_no": doc.bill_no,
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"amount": doc.amount,
		"total": doc.total,
		"loading_items": [
			{
				"item": r.item,
				"item_name": r.item_name,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
			}
			for r in doc.loading_items
		],
	}
