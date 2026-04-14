import json
import frappe


def _resolve_gst_category(gstin):
	return "Registered Regular" if (gstin or "").strip() else "Unregistered"


def _sync_whatsapp_to_contact(supplier_id, whatsapp):
	"""Write WhatsApp number as the second row in the linked Contact's phone_nos table."""
	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Supplier", "link_name": supplier_id, "parenttype": "Contact"},
		"parent",
	)
	if not contact_name:
		return
	contact = frappe.get_doc("Contact", contact_name)
	if len(contact.phone_nos) > 1:
		contact.phone_nos[1].phone = whatsapp
		contact.phone_nos[1].is_primary_mobile_no = 0
	elif whatsapp:
		contact.append("phone_nos", {"phone": whatsapp, "is_primary_mobile_no": 0})
	contact.save(ignore_permissions=True)


@frappe.whitelist()
def get_supplier_groups():
	"""Return all active Supplier Groups for dropdown population."""
	return frappe.get_all(
		"Supplier Group",
		filters={"is_group": 0},
		fields=["name"],
		order_by="name asc",
	)


@frappe.whitelist()
def create_supplier_full(data):
	"""Create a Supplier with optional Address in one server-side call."""
	if isinstance(data, str):
		data = json.loads(data)

	supplier_name = (data.get("supplier_name") or "").strip()
	if not supplier_name:
		frappe.throw("Supplier Name is required")

	sup = frappe.new_doc("Supplier")
	sup.supplier_name = supplier_name
	sup.supplier_type = data.get("supplier_type") or "Individual"
	sup.supplier_group = data.get("supplier_group") or "All Supplier Groups"
	sup.mobile_no = data.get("mobile") or ""
	sup.email_id = data.get("email") or ""
	sup.gstin = data.get("gstin") or ""
	sup.gst_category = _resolve_gst_category(sup.gstin)
	sup.insert(ignore_permissions=True)

	if data.get("address_line1"):
		addr = frappe.new_doc("Address")
		addr.address_title = supplier_name
		addr.address_type = "Billing"
		addr.address_line1 = data.get("address_line1") or ""
		addr.address_line2 = data.get("address_line2") or ""
		addr.city = data.get("city") or ""
		addr.pincode = data.get("pincode") or ""
		addr.state = data.get("state") or ""
		addr.country = "India"
		addr.append("links", {"link_doctype": "Supplier", "link_name": sup.name})
		addr.insert(ignore_permissions=True)

	if data.get("whatsapp"):
		_sync_whatsapp_to_contact(sup.name, data["whatsapp"])

	return {"name": sup.name, "supplier_name": sup.supplier_name}


@frappe.whitelist()
def get_supplier_details(supplier):
	"""Return Supplier fields + linked Address in one call."""
	sup = frappe.get_doc("Supplier", supplier)

	result = {
		"name": sup.name,
		"supplier_name": sup.supplier_name,
		"supplier_type": sup.supplier_type or "Individual",
		"supplier_group": sup.supplier_group or "",
		"mobile": sup.mobile_no or "",
		"email": sup.email_id or "",
		"gstin": sup.gstin or "",
		"gst_category": sup.gst_category or _resolve_gst_category(sup.gstin),
		"whatsapp": "",
		"address_name": "",
		"address_line1": "",
		"address_line2": "",
		"city": "",
		"pincode": "",
		"state": "",
	}

	# Fetch WhatsApp from Contact phone_nos row 1
	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Supplier", "link_name": supplier, "parenttype": "Contact"},
		"parent",
	)
	if contact_name:
		wa = frappe.db.get_value(
			"Contact Phone",
			{"parent": contact_name, "is_primary_mobile_no": 0},
			"phone",
			order_by="idx asc",
		)
		result["whatsapp"] = wa or ""

	address_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Supplier", "link_name": supplier, "parenttype": "Address"},
		"parent",
	)
	if address_name:
		addr = frappe.get_doc("Address", address_name)
		result.update({
			"address_name": addr.name,
			"address_line1": addr.address_line1 or "",
			"address_line2": addr.address_line2 or "",
			"city": addr.city or "",
			"pincode": addr.pincode or "",
			"state": addr.state or "",
		})

	return result


@frappe.whitelist()
def update_supplier_full(data):
	"""Update Supplier + Address in one call."""
	if isinstance(data, str):
		data = json.loads(data)

	supplier_id = data.get("name")
	if not supplier_id:
		frappe.throw("Supplier name is required")

	sup = frappe.get_doc("Supplier", supplier_id)
	sup.supplier_name = data.get("supplier_name") or sup.supplier_name
	sup.supplier_type = data.get("supplier_type") or sup.supplier_type or "Individual"
	sup.supplier_group = data.get("supplier_group") or sup.supplier_group or "All Supplier Groups"
	sup.mobile_no = data.get("mobile") or ""
	sup.email_id = data.get("email") or ""
	sup.gstin = data.get("gstin") or ""
	sup.gst_category = _resolve_gst_category(sup.gstin)
	sup.save(ignore_permissions=True)

	if "whatsapp" in data:
		_sync_whatsapp_to_contact(supplier_id, data.get("whatsapp") or "")

	address_name = data.get("address_name") or frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Supplier", "link_name": supplier_id, "parenttype": "Address"},
		"parent",
	)

	if address_name:
		addr = frappe.get_doc("Address", address_name)
		addr.address_line1 = data.get("address_line1") or addr.address_line1
		addr.address_line2 = data.get("address_line2") or ""
		addr.city = data.get("city") or addr.city
		addr.pincode = data.get("pincode") or ""
		addr.state = data.get("state") or ""
		addr.save(ignore_permissions=True)
	elif data.get("address_line1"):
		addr = frappe.new_doc("Address")
		addr.address_title = sup.supplier_name
		addr.address_type = "Billing"
		addr.address_line1 = data.get("address_line1") or ""
		addr.address_line2 = data.get("address_line2") or ""
		addr.city = data.get("city") or ""
		addr.pincode = data.get("pincode") or ""
		addr.state = data.get("state") or ""
		addr.country = "India"
		addr.append("links", {"link_doctype": "Supplier", "link_name": supplier_id})
		addr.insert(ignore_permissions=True)

	return {"name": sup.name, "supplier_name": sup.supplier_name}


@frappe.whitelist()
def search_suppliers(query=""):
	"""Search suppliers by name."""
	filters = [["supplier_name", "like", f"%{query}%"]] if query else []
	return frappe.get_all("Supplier", filters=filters, fields=["name", "supplier_name"], limit=30)


@frappe.whitelist()
def get_outstanding_purchase_invoices(supplier):
	"""Return outstanding purchase invoices using ERPNext's Payment Ledger Entry
	(same logic as the 'Get Outstanding Invoices' button in Payment Entry doctype)."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents
	from erpnext.accounts.party import get_party_account

	company = frappe.defaults.get_global_default("company")
	party_account = get_party_account("Supplier", supplier, company)

	args = {
		"posting_date": frappe.utils.today(),
		"company": company,
		"party_type": "Supplier",
		"payment_type": "Pay",
		"party": supplier,
		"party_account": party_account,
		"get_outstanding_invoices": True,
	}
	return get_outstanding_reference_documents(args) or []
