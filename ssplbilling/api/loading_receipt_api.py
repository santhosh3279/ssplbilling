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
	if d.get("time"):
		doc.time = d.get("time")
	doc.party_type = d.get("party_type", "Customer")
	doc.customer = d.get("customer")
	doc.customer_name = d.get("customer_name")
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
	if d.get("time"):
		doc.time = d.get("time")
	doc.party_type = d.get("party_type", "Customer")
	doc.customer = d.get("customer")
	doc.customer_name = d.get("customer_name")
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
def get_loading_receipts(query="", date=None):
	query = (query or "").strip()
	clauses = []
	values = []
	if query:
		clauses.append("(lr.name LIKE %s OR lr.customer LIKE %s OR lr.bill_no LIKE %s)")
		values += [f"%{query}%", f"%{query}%", f"%{query}%"]
	if date:
		clauses.append("lr.date = %s")
		values.append(date)
	where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
	rows = frappe.db.sql(
		f"""
		SELECT lr.name, lr.date, lr.bill_no, lr.customer, lr.customer_name, lr.total, lr.party_type
		FROM `tabLoading Receipt` lr
		{where}
		ORDER BY lr.creation DESC
		LIMIT 100
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
		"party_type": doc.party_type,
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
