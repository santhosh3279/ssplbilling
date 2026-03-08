import json
import frappe

@frappe.whitelist()
def get_all_ledgers():
    """Fetch all Customers, Suppliers, and Accounts in a unified format for local preloading."""
    ledgers = []

    # 1. Customers
    customers = frappe.get_all(
        "Customer",
        filters={"disabled": 0},
        fields=["name", "customer_name as label", "mobile_no", "email_id as email", "gstin"],
        limit=0
    )
    for c in customers:
        c["type"] = "Customer"
    ledgers.extend(customers)

    # 2. Suppliers
    suppliers = frappe.get_all(
        "Supplier",
        filters={"disabled": 0},
        fields=["name", "supplier_name as label", "mobile_no", "email_id as email", "gstin"],
        limit=0
    )
    for s in suppliers:
        s["type"] = "Supplier"
    ledgers.extend(suppliers)

    # 3. Accounts (Ledgers)
    accounts = frappe.get_all(
        "Account",
        filters={"disabled": 0, "is_group": 0},
        fields=["name", "account_name as label"],
        limit=0
    )
    for a in accounts:
        a["type"] = "Account"
        a["mobile_no"] = ""
        a["email"] = ""
        a["gstin"] = ""
    ledgers.extend(accounts)

    # Map for fast lookup
    ledger_map = {l.name: l for l in ledgers}

    # 4. Batch fetch primary addresses (Customers & Suppliers)
    addresses = frappe.db.sql("""
        SELECT dl.link_name AS name, addr.address_line1, addr.city
        FROM `tabDynamic Link` dl
        JOIN `tabAddress` addr ON addr.name = dl.parent
        WHERE dl.link_doctype IN ('Customer', 'Supplier') AND dl.parenttype = 'Address'
        ORDER BY addr.modified DESC
    """, as_dict=True)
    for a in addresses:
        if a.name in ledger_map:
            l = ledger_map[a.name]
            if not l.get("address_line1"):
                l["address_line1"] = a.address_line1
                l["city"] = a.city

    # 5. Batch fetch WhatsApp (Customers & Suppliers)
    wa_rows = frappe.db.sql("""
        SELECT dl.link_name AS name, cp.phone AS whatsapp
        FROM `tabDynamic Link` dl
        JOIN `tabContact Phone` cp ON cp.parent = dl.parent
        WHERE dl.link_doctype IN ('Customer', 'Supplier') AND dl.parenttype = 'Contact' AND cp.is_primary_mobile_no = 0
    """, as_dict=True)
    for w in wa_rows:
        if w.name in ledger_map:
            ledger_map[w.name]["whatsapp"] = w.whatsapp

    # 6. Batch fetch Balances (Unified)
    balances = frappe.db.sql("""
        SELECT party as name, SUM(debit) - SUM(credit) as balance
        FROM `tabGL Entry`
        WHERE is_cancelled = 0
        GROUP BY party
        UNION
        SELECT account as name, SUM(debit) - SUM(credit) as balance
        FROM `tabGL Entry`
        WHERE is_cancelled = 0 AND (party IS NULL OR party = '')
        GROUP BY account
    """, as_dict=True)
    for b in balances:
        if b.name in ledger_map:
            ledger_map[b.name]["balance"] = float(b.balance or 0)

    # 7. Batch fetch Last Invoice Dates (Customers only)
    last_invoices = frappe.db.sql("""
        SELECT customer, MAX(posting_date) as last_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        GROUP BY customer
    """, as_dict=True)
    for i in last_invoices:
        if i.customer in ledger_map:
            ledger_map[i.customer]["last_invoice_date"] = str(i.last_date)

    return sorted(ledgers, key=lambda x: x["label"].lower())

@frappe.whitelist()
def get_customer_ledger():
    """Fetch all customers with full details (contact, address, balance) for local preloading."""
    # 1. Basic Customer Info
    customers = frappe.get_all(
        "Customer",
        filters={"disabled": 0},
        fields=["name", "customer_name", "mobile_no", "email_id as email", "gstin"],
        order_by="customer_name asc",
        limit=0
    )

    # 2. Batch fetch primary addresses
    addresses = frappe.db.sql("""
        SELECT dl.link_name AS customer, addr.address_line1, addr.city
        FROM `tabDynamic Link` dl
        JOIN `tabAddress` addr ON addr.name = dl.parent
        WHERE dl.link_doctype = 'Customer' AND dl.parenttype = 'Address'
        ORDER BY addr.modified DESC
    """, as_dict=True)
    addr_map = {}
    for a in addresses:
        addr_map.setdefault(a.customer, a)

    # 3. Batch fetch WhatsApp (Secondary Phone)
    wa_rows = frappe.db.sql("""
        SELECT dl.link_name AS customer, cp.phone AS whatsapp
        FROM `tabDynamic Link` dl
        JOIN `tabContact Phone` cp ON cp.parent = dl.parent
        WHERE dl.link_doctype = 'Customer' AND dl.parenttype = 'Contact' AND cp.is_primary_mobile_no = 0
    """, as_dict=True)
    wa_map = {w.customer: w.whatsapp for w in wa_rows}

    # 4. Batch fetch Balances
    balances = frappe.db.sql("""
        SELECT party as customer, SUM(debit) - SUM(credit) as balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer' AND is_cancelled = 0
        GROUP BY party
    """, as_dict=True)
    bal_map = {b.customer: float(b.balance or 0) for b in balances}

    # 5. Batch fetch Last Invoice Dates
    last_invoices = frappe.db.sql("""
        SELECT customer, MAX(posting_date) as last_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        GROUP BY customer
    """, as_dict=True)
    inv_map = {i.customer: str(i.last_date) for i in last_invoices}

    # Merge
    for c in customers:
        addr = addr_map.get(c.name)
        c["address_line1"] = addr.address_line1 if addr else ""
        c["city"] = addr.city if addr else ""
        c["whatsapp"] = wa_map.get(c.name, "")
        c["balance"] = bal_map.get(c.name, 0.0)
        c["last_invoice_date"] = inv_map.get(c.name)

    return customers

@frappe.whitelist()
def get_all_customers_detailed():
    """Fetch all customers with mobile_no, balance, and primary address for local sync."""
    customers = frappe.get_all(
        "Customer",
        filters={"disabled": 0},
        fields=["name", "customer_name", "mobile_no"],
        order_by="customer_name asc",
    )

    # Batch fetch addresses
    addresses = frappe.db.sql("""
        SELECT 
            dl.link_name as customer,
            addr.address_line1,
            addr.city,
            addr.pincode
        FROM `tabDynamic Link` dl
        JOIN `tabAddress` addr ON addr.name = dl.parent
        WHERE dl.link_doctype = 'Customer' AND dl.parenttype = 'Address'
    """, as_dict=True)

    addr_map = {a.customer: a for a in addresses}

    # Batch fetch balances
    balances = frappe.db.sql("""
        SELECT 
            party as customer,
            SUM(debit) - SUM(credit) as balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer' AND is_cancelled = 0
        GROUP BY party
    """, as_dict=True)

    bal_map = {b.customer: float(b.balance or 0) for b in balances}

    for c in customers:
        c["balance"] = bal_map.get(c.name, 0.0)
        addr = addr_map.get(c.name)
        if addr:
            c["address_line1"] = addr.address_line1
            c["city"] = addr.city
            c["pincode"] = addr.pincode
        else:
            c["address_line1"] = ""
            c["city"] = ""
            c["pincode"] = ""

    return customers

@frappe.whitelist()
def get_all_customers_for_sync():
	"""Fetch all active customers for local IndexedDB sync."""
	customers = frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		fields=["name", "customer_name", "mobile_no"],
		order_by="customer_name asc",
		limit=0,
	)

	addresses = frappe.db.sql(
		"""
		SELECT dl.link_name AS customer, addr.address_line1, addr.city
		FROM `tabDynamic Link` dl
		JOIN `tabAddress` addr ON addr.name = dl.parent
		WHERE dl.link_doctype = 'Customer' AND dl.parenttype = 'Address'
		ORDER BY addr.modified DESC
		""",
		as_dict=True,
	)
	addr_map = {}
	for a in addresses:
		addr_map.setdefault(a.customer, a)

	wa_rows = frappe.db.sql(
		"""
		SELECT dl.link_name AS customer, cp.phone AS whatsapp
		FROM `tabDynamic Link` dl
		JOIN `tabContact Phone` cp
			ON cp.parent = dl.parent
			AND cp.parenttype = 'Contact'
			AND cp.is_primary_mobile_no = 0
		WHERE dl.link_doctype = 'Customer' AND dl.parenttype = 'Contact'
		ORDER BY cp.idx ASC
		""",
		as_dict=True,
	)
	wa_map = {}
	for w in wa_rows:
		wa_map.setdefault(w.customer, w.whatsapp)

	for c in customers:
		addr = addr_map.get(c.name)
		c["address_line1"] = addr.address_line1 if addr else ""
		c["city"] = addr.city if addr else ""
		c["whatsapp"] = wa_map.get(c.name, "")

	return customers

@frappe.whitelist()
def search_customers(query):
    """Search customers by name or ID, including mobile, balance, address, whatsapp and last invoice date."""
    if not query or len(query) < 1:
        return []

    customers = frappe.get_all(
        "Customer",
        or_filters={
            "name": ["like", f"%{query}%"],
            "customer_name": ["like", f"%{query}%"],
        },
        filters={"disabled": 0},
        fields=["name", "customer_name", "mobile_no"],
        limit=20,
        order_by="customer_name asc",
    )

    for c in customers:
        balance_row = frappe.db.sql(
            """
            SELECT SUM(debit) - SUM(credit) as balance
            FROM `tabGL Entry`
            WHERE party_type = 'Customer' AND party = %s AND is_cancelled = 0
            """,
            (c.name,),
            as_dict=True,
        )
        c["balance"] = float(balance_row[0].balance or 0) if balance_row else 0.0

        last_inv = frappe.db.get_value("Sales Invoice", 
            {"customer": c.name, "docstatus": 1}, 
            "posting_date", 
            order_by="posting_date desc"
        )
        c["last_invoice_date"] = str(last_inv) if last_inv else None

        addr_name = frappe.db.get_value("Dynamic Link", 
            {"link_doctype": "Customer", "link_name": c.name, "parenttype": "Address"}, 
            "parent"
        )
        if addr_name:
            addr = frappe.db.get_value("Address", addr_name, ["address_line1", "city", "pincode"], as_dict=True)
            if addr:
                c["address_line1"] = addr.address_line1
                c["city"] = addr.city
                c["pincode"] = addr.pincode
        
        contact_name = frappe.db.get_value("Dynamic Link", 
            {"link_doctype": "Customer", "link_name": c.name, "parenttype": "Contact"}, 
            "parent"
        )
        if contact_name:
            wa = frappe.db.get_value("Contact Phone", 
                {"parent": contact_name, "is_primary_mobile_no": 0}, 
                "phone"
            )
            c["whatsapp"] = wa or ""
        else:
            c["whatsapp"] = ""

    return customers

@frappe.whitelist()
def get_customer_full(customer):
	"""Return complete customer data (Customer + Address + WhatsApp)."""
	doc = frappe.get_doc("Customer", customer)

	result = {
		"name": doc.name,
		"customer_name": doc.customer_name or "",
		"mobile": doc.mobile_no or "",
		"email": doc.email_id or "",
		"gstin": doc.gstin or "",
		"whatsapp": "",
		"address_line1": "",
		"address_line2": "",
		"address_line3": "",
		"city": "",
		"pincode": "",
		"state": "",
	}

	addr_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
		"parent",
		order_by="modified desc",
	)
	if addr_name:
		addr = frappe.db.get_value(
			"Address",
			addr_name,
			["address_line1", "address_line2", "address_line3", "city", "pincode", "state"],
			as_dict=True,
		)
		if addr:
			result["address_line1"] = addr.address_line1 or ""
			result["address_line2"] = addr.address_line2 or ""
			result["address_line3"] = addr.address_line3 or ""
			result["city"] = addr.city or ""
			result["pincode"] = addr.pincode or ""
			result["state"] = addr.state or ""

	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
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

	return result

@frappe.whitelist()
def get_customer_quick_stats(customer):
	"""Return ledger balance and last submitted invoice date."""
	balance_row = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(debit) - SUM(credit), 0) AS balance
		FROM `tabGL Entry`
		WHERE party_type = 'Customer' AND party = %s AND is_cancelled = 0
		""",
		(customer,),
		as_dict=True,
	)
	last_inv = frappe.db.sql(
		"""
		SELECT posting_date
		FROM `tabSales Invoice`
		WHERE customer = %s AND docstatus = 1
		ORDER BY posting_date DESC
		LIMIT 1
		""",
		(customer,),
		as_dict=True,
	)
	return {
		"balance": float(balance_row[0].balance or 0) if balance_row else 0.0,
		"last_invoice_date": str(last_inv[0].posting_date) if last_inv else None,
	}

@frappe.whitelist()
def update_customer_full(data):
	"""Update Customer + Address + Contact phones in one call."""
	if isinstance(data, str):
		data = json.loads(data)

	customer_id = data.get("name")
	if not customer_id:
		frappe.throw("Customer name is required")

	cust = frappe.get_doc("Customer", customer_id)
	cust.customer_name = data.get("customer_name") or cust.customer_name
	cust.mobile_no = data.get("mobile") or ""
	cust.email_id = data.get("email") or ""
	cust.gstin = data.get("gstin") or ""
	cust.save(ignore_permissions=True)

	address_name = data.get("address_name") or frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer_id, "parenttype": "Address"},
		"parent",
	)

	if address_name:
		addr = frappe.get_doc("Address", address_name)
		addr.address_line1 = data.get("address_line1") or addr.address_line1
		addr.address_line2 = data.get("address_line2") or ""
		addr.address_line3 = data.get("address_line3") or ""
		addr.city = data.get("city") or addr.city
		addr.pincode = data.get("pincode") or ""
		addr.state = data.get("state") or ""
		addr.save(ignore_permissions=True)
	elif data.get("address_line1") or data.get("city"):
		addr = frappe.get_doc({
			"doctype": "Address",
			"address_title": cust.customer_name,
			"address_type": "Billing",
			"address_line1": data.get("address_line1") or "",
			"address_line2": data.get("address_line2") or "",
			"address_line3": data.get("address_line3") or "",
			"city": data.get("city") or "",
			"pincode": data.get("pincode") or "",
			"state": data.get("state") or "",
			"country": "India",
			"links": [{"link_doctype": "Customer", "link_name": customer_id}],
		})
		addr.insert(ignore_permissions=True)

	contact_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer_id, "parenttype": "Contact"},
		"parent",
	)
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		mobile = data.get("mobile") or ""
		whatsapp = data.get("whatsapp") or ""

		if contact.phone_nos:
			contact.phone_nos[0].phone = mobile
			contact.phone_nos[0].is_primary_mobile_no = 1
		else:
			contact.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})

		if len(contact.phone_nos) > 1:
			contact.phone_nos[1].phone = whatsapp
			contact.phone_nos[1].is_primary_mobile_no = 0
		elif whatsapp:
			contact.append("phone_nos", {"phone": whatsapp, "is_primary_mobile_no": 0})

		contact.save(ignore_permissions=True)

	return {"name": cust.name, "customer_name": cust.customer_name}

@frappe.whitelist()
def quick_create_customer(data=None, **kwargs):
    """Create a Customer with basic details."""
    if not data:
        data = frappe.form_dict
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k != "cmd"}

    if isinstance(data, str):
        data = json.loads(data)

    customer_name = data.get("customer_name", "").strip()
    if not customer_name:
        frappe.throw("Customer name is required")

    cust = frappe.new_doc("Customer")
    cust.customer_name = customer_name
    cust.customer_type = data.get("customer_type") or "Individual"
    cust.customer_group = data.get("customer_group") or "All Customer Groups"
    cust.territory = data.get("territory") or "All Territories"
    cust.mobile_no = data.get("mobile", "")
    cust.email_id = data.get("email", "")
    cust.gstin = data.get("gstin", "")
    cust.insert(ignore_permissions=True)

    if data.get("address_line1") or data.get("city"):
        addr = frappe.new_doc("Address")
        addr.address_title = customer_name
        addr.address_type = "Billing"
        addr.address_line1 = data.get("address_line1", "")
        addr.address_line2 = data.get("address_line2", "")
        addr.city = data.get("city", "")
        addr.state = data.get("state", "")
        addr.pincode = data.get("pincode", "")
        addr.country = "India"
        addr.append("links", {"link_doctype": "Customer", "link_name": cust.name})
        addr.insert(ignore_permissions=True)

    if data.get("mobile") or data.get("email"):
        contact = frappe.new_doc("Contact")
        contact.first_name = customer_name
        contact.append("links", {"link_doctype": "Customer", "link_name": cust.name})
        contact.append("phone_nos", {"phone": data.get("mobile", ""), "is_primary_mobile_no": 1})
        contact.insert(ignore_permissions=True)

    return {"name": cust.name, "customer_name": cust.customer_name}

@frappe.whitelist()
def update_customer_details(customer=None, data=None):
    """Update existing Customer and their primary Address."""
    if not customer:
        customer = frappe.form_dict.get("customer")
    if not data:
        data = frappe.form_dict.get("data")
        
    if isinstance(data, str):
        data = json.loads(data)

    cust = frappe.get_doc("Customer", customer)
    if data.get("customer_name"): cust.customer_name = data["customer_name"]
    if data.get("mobile"): cust.mobile_no = data["mobile"]
    if data.get("email"): cust.email_id = data["email"]
    if data.get("gstin"): cust.gstin = data["gstin"]
    cust.save(ignore_permissions=True)

    addr_name = frappe.db.get_value("Dynamic Link", 
        {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"}, 
        "parent"
    )

    if addr_name:
        addr = frappe.get_doc("Address", addr_name)
    else:
        addr = frappe.new_doc("Address")
        addr.address_title = cust.customer_name
        addr.address_type = "Billing"
        addr.country = "India"
        addr.append("links", {"link_doctype": "Customer", "link_name": customer})

    if data.get("address_line1") is not None: addr.address_line1 = data["address_line1"]
    if data.get("city") is not None: addr.city = data["city"]
    if data.get("state") is not None: addr.state = data["state"]
    if data.get("pincode") is not None: addr.pincode = data["pincode"]
    addr.save(ignore_permissions=True)

    return {"name": cust.name, "customer_name": cust.customer_name}
