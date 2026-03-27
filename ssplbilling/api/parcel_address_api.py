import frappe


@frappe.whitelist()
def create_parcel_address(data):
	import json

	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.new_doc("Parcel Address")
	doc.recipient_name = d.get("recipient_name", "")
	doc.mobile_number = d.get("mobile_number", "")
	doc.number_of_packages = d.get("number_of_packages") or 1
	doc.address_line_1 = d.get("address_line_1", "")
	doc.address_line_2 = d.get("address_line_2", "")
	doc.address_line_3 = d.get("address_line_3", "")
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def update_parcel_address(data):
	import json

	d = json.loads(data) if isinstance(data, str) else data
	doc = frappe.get_doc("Parcel Address", d["name"])
	doc.recipient_name = d.get("recipient_name", "")
	doc.mobile_number = d.get("mobile_number", "")
	doc.number_of_packages = d.get("number_of_packages") or 1
	doc.address_line_1 = d.get("address_line_1", "")
	doc.address_line_2 = d.get("address_line_2", "")
	doc.address_line_3 = d.get("address_line_3", "")
	doc.save(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def get_parcel_addresses(query="", date=None):
	query = (query or "").strip()
	clauses = []
	values = []
	if query:
		clauses.append("(pa.name LIKE %s OR pa.recipient_name LIKE %s OR pa.mobile_number LIKE %s)")
		values += [f"%{query}%", f"%{query}%", f"%{query}%"]
	if date:
		clauses.append("DATE(pa.creation) = %s")
		values.append(date)
	where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
	rows = frappe.db.sql(
		f"""
		SELECT pa.name, pa.recipient_name, pa.mobile_number,
		       pa.address_line_1, pa.number_of_packages,
		       DATE(pa.creation) as date
		FROM `tabParcel Address` pa
		{where}
		ORDER BY pa.creation DESC
		LIMIT 100
		""",
		values,
		as_dict=True,
	)
	return rows


@frappe.whitelist()
def get_parcel_address(name):
	doc = frappe.get_doc("Parcel Address", name)
	return {
		"name": doc.name,
		"recipient_name": doc.recipient_name,
		"mobile_number": doc.mobile_number,
		"number_of_packages": doc.number_of_packages,
		"address_line_1": doc.address_line_1,
		"address_line_2": doc.address_line_2,
		"address_line_3": doc.address_line_3,
	}
