import frappe


@frappe.whitelist()
def get_customer_pricing(customer):
	"""Return a dict of {item_code: multiplication_factor} for the customer."""
	if not customer:
		return {}

	if not frappe.db.exists("Customer Pricing", customer):
		return {}

	rows = frappe.get_all(
		"Customer Pricing Item",
		filters={"parent": customer, "parenttype": "Customer Pricing"},
		fields=["item_code", "multiplication_factor"],
	)
	return {r.item_code: float(r.multiplication_factor or 1.0) for r in rows}


@frappe.whitelist()
def save_customer_item_price(customer, item_code, multiplication_factor):
	"""Upsert an item multiplication factor in Customer Pricing for the given customer."""
	multiplication_factor = float(multiplication_factor or 1.0)

	if frappe.db.exists("Customer Pricing", customer):
		doc = frappe.get_doc("Customer Pricing", customer)
		existing = next((r for r in doc.items if r.item_code == item_code), None)
		if existing:
			existing.multiplication_factor = multiplication_factor
		else:
			doc.append("items", {"item_code": item_code, "multiplication_factor": multiplication_factor})
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Customer Pricing")
		doc.customer = customer
		doc.append("items", {"item_code": item_code, "multiplication_factor": multiplication_factor})
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
	return {"ok": True, "customer": customer, "item_code": item_code, "multiplication_factor": multiplication_factor}
