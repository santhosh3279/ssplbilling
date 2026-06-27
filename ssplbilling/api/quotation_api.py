import json
import frappe
from frappe.model.naming import parse_naming_series
from erpnext.controllers.accounts_controller import get_taxes_and_charges as _erpnext_tax_rows
from ssplbilling.api.stock_utils import get_draft_invoice_qty


# ──────────────────────────────────────────────────────────────────────────────
# Item helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_item_tax_rate(item_code):
	"""Return the effective tax rate (%) for an item from its Item Tax Template."""
	today = frappe.utils.today()
	tax_rows = frappe.get_all(
		"Item Tax",
		filters={"parent": item_code, "parenttype": "Item"},
		fields=["item_tax_template", "valid_from"],
		order_by="valid_from desc",
	)
	template_name = None
	for row in tax_rows:
		if not row.valid_from or str(row.valid_from) <= today:
			template_name = row.item_tax_template
			break

	if not template_name:
		return 0.0

	details = frappe.get_all(
		"Item Tax Template Detail",
		filters={"parent": template_name},
		fields=["tax_rate"],
	)
	return float(sum(d.tax_rate or 0 for d in details)) / 2


@frappe.whitelist()
def get_item_details(item_code, price_list="Standard Selling", warehouse=None):
	"""Look up item by code or barcode. Returns item details + stock + rate."""
	barcode_item = frappe.db.get_value("Item Barcode", {"barcode": item_code}, "parent")
	if barcode_item:
		item_code = barcode_item

	if not frappe.db.exists("Item", item_code):
		return {"found": False, "item_code": item_code}

	item = frappe.get_cached_doc("Item", item_code)
	wh = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

	rate = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "selling": 1, "uom": item.stock_uom},
		"price_list_rate",
	) or frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "price_list": price_list, "selling": 1},
		"price_list_rate",
	) or item.standard_rate or 0

	# Fetch UOM conversions
	uoms = frappe.get_all(
		"UOM Conversion Detail",
		filters={"parent": item_code},
		fields=["uom", "conversion_factor"],
	)

	# Fetch all price list rates for this item (including per-UOM)
	all_rates = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "selling": 1},
		fields=["price_list", "price_list_rate", "uom"],
	)

	uom_price_lists = {}
	for r in all_rates:
		pl = r.price_list
		uom_key = r.uom or ""
		if uom_key:
			uom_price_lists.setdefault(pl, {})[uom_key] = float(r.price_list_rate or 0)

	stock_qty = 0
	if wh:
		stock_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty") or 0
		stock_qty = float(stock_qty) - get_draft_invoice_qty(item_code, wh)

	return {
		"found": True,
		"item_code": item.item_code,
		"item_name": item.item_name,
		"uom": item.stock_uom,
		"uoms": [{"uom": u.uom, "conversion_factor": float(u.conversion_factor or 1)} for u in uoms],
		"uom_price_lists": uom_price_lists,
		"rate": float(rate),
		"stock_qty": float(stock_qty),
		"warehouse": wh,
		"tax_rate": _get_item_tax_rate(item.item_code),
	}


@frappe.whitelist()
def search_items(query, price_list="Standard Selling"):
	"""Search items by code, name, or barcode. Returns list of matches."""
	if not query or len(query) < 1:
		return []

	barcode_item = frappe.db.get_value("Item Barcode", {"barcode": query}, "parent")
	if barcode_item:
		return [get_item_details(barcode_item, price_list)]

	items = frappe.get_all(
		"Item",
		or_filters={
			"item_code": ["like", f"%{query}%"],
			"item_name": ["like", f"%{query}%"],
		},
		filters={"disabled": 0, "is_sales_item": 1},
		fields=["item_code", "item_name", "stock_uom as uom", "standard_rate"],
		limit=20,
		order_by="item_name asc",
	)

	wh = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
	for item in items:
		item["rate"] = float(
			frappe.db.get_value(
				"Item Price",
				{"item_code": item["item_code"], "price_list": price_list, "selling": 1},
				"price_list_rate",
			)
			or item.get("standard_rate")
			or 0
		)
		item["stock_qty"] = (
			float(
				frappe.db.get_value("Bin", {"item_code": item["item_code"], "warehouse": wh}, "actual_qty")
				or 0
			) - get_draft_invoice_qty(item["item_code"], wh)
		) if wh else 0
		item["warehouse"] = wh
		item["found"] = True
		item["tax_rate"] = _get_item_tax_rate(item["item_code"])

	return items


@frappe.whitelist()
def get_item_insight(item_code, price_list="Standard Selling", warehouse=None):
	"""Return stock across all warehouses + selling price lists + previous quotations."""
	if not item_code or not frappe.db.exists("Item", item_code):
		return {}

	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code},
		fields=["warehouse", "actual_qty"],
		order_by="actual_qty desc",
	)

	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item_code, "selling": 1},
		fields=["price_list", "price_list_rate as rate"],
		order_by="price_list",
	)

	prev_quotes = frappe.db.sql(
		"""
		SELECT
			qi.parent AS name,
			q.transaction_date AS date,
			qi.rate,
			qi.qty,
			qi.discount_percentage AS discount
		FROM `tabQuotation Item` qi
		JOIN `tabQuotation` q ON q.name = qi.parent
		WHERE qi.item_code = %(item_code)s
		  AND q.docstatus = 1
		ORDER BY q.transaction_date DESC
		LIMIT 10
		""",
		{"item_code": item_code},
		as_dict=True,
	)

	return {
		"item_code": item_code,
		"stock": [{"warehouse": b.warehouse, "actual_qty": float(b.actual_qty or 0) - get_draft_invoice_qty(item_code, b.warehouse)} for b in bins],
		"priceLists": [{"name": p.price_list, "rate": float(p.rate or 0)} for p in prices],
		"previousPurchases": [
			{
				"name": p.name,
				"date": str(p.date or ""),
				"rate": float(p.rate or 0),
				"qty": float(p.qty or 0),
				"discount": float(p.discount or 0),
			}
			for p in prev_quotes
		],
	}


# ──────────────────────────────────────────────────────────────────────────────
# Naming series
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_naming_series():
	"""Return available naming series for Quotation."""
	try:
		prop_value = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Quotation", "field_name": "naming_series", "property": "options"},
			"value",
		)
		if prop_value:
			series = [s.strip() for s in prop_value.split("\n") if s.strip()]
			if series:
				return series
	except Exception:
		pass
	try:
		meta = frappe.get_meta("Quotation")
		field = next((f for f in meta.fields if f.fieldname == "naming_series"), None)
		if field and field.options:
			return [s.strip() for s in field.options.strip().split("\n") if s.strip()]
	except Exception:
		pass
	return ["SSPL-QT-.YYYY.-"]


@frappe.whitelist()
def get_next_quotation_no(naming_series):
	"""Preview the next Quotation number for a given series."""
	try:
		return parse_naming_series(naming_series)
	except Exception:
		return naming_series + "???"


# ──────────────────────────────────────────────────────────────────────────────
# List / fetch
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_quotations(query="", limit=50, transaction_date=None, show_submitted=False):
	"""Return list of Quotations for the sidebar."""
	filters = {"quotation_to": "Customer"}
	if transaction_date:
		filters["transaction_date"] = transaction_date
	if not (frappe.parse_json(show_submitted) if isinstance(show_submitted, str) else show_submitted):
		filters["docstatus"] = 0

	or_filters = None
	if query:
		import re
		flexible_query = "%" + "%".join(re.findall(r'[A-Za-z]+|\d+', query)) + "%"
		or_filters = [
			["Quotation", "name", "like", flexible_query],
			["Quotation", "party_name", "like", f"%{query}%"],
			["Quotation", "customer_name", "like", f"%{query}%"],
		]

	quotes = frappe.get_all(
		"Quotation",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "party_name", "customer_name", "grand_total", "rounded_total", "status", "docstatus", "transaction_date"],
		order_by="name desc",
		limit_page_length=int(limit),
	)

	return [
		{
			"name": q.name,
			"customer": q.party_name,
			"customer_name": q.customer_name or q.party_name,
			"grand_total": float(q.grand_total or 0),
			"rounded_total": float(q.rounded_total or q.grand_total or 0),
			"status": q.status or ("Draft" if q.docstatus == 0 else "Submitted"),
			"docstatus": q.docstatus,
		}
		for q in quotes
	]


@frappe.whitelist()
def get_quotation(quotation_name):
	"""Return a single Quotation with its items."""
	if not frappe.db.exists("Quotation", quotation_name):
		frappe.throw(f"Quotation {quotation_name} not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	cost_center = getattr(qt, "cost_center", "") or ""

	def _actual_charge(keyword):
		for t in (qt.taxes or []):
			if t.charge_type == "Actual" and keyword.lower() in (t.description or "").lower():
				return float(t.tax_amount or 0)
		return 0.0

	items = []
	for i in qt.items:
		items.append({
			"item_code": i.item_code,
			"item_name": i.item_name,
			"uom": i.uom or i.stock_uom,
			"qty": float(i.qty or 0),
			"price_list_rate": float(i.price_list_rate or i.rate or 0),
			"rate": float(i.rate or 0),
			"discount": float(i.discount_percentage or 0),
			"tax_rate": _get_item_tax_rate(i.item_code),
			"deleted": False,
		})

	is_inclusive = 0
	if qt.taxes:
		if any(t.included_in_print_rate for t in qt.taxes):
			is_inclusive = 1

	# Fetch state from billing address
	party_state = ""
	if qt.customer_address:
		party_state = frappe.db.get_value("Address", qt.customer_address, "state") or ""

	return {
		"name": qt.name,
		"customer": qt.party_name,
		"customer_name": qt.customer_name,
		"state": party_state,
		"naming_series": qt.naming_series,
		"transaction_date": str(qt.transaction_date or ""),
		"valid_till": str(qt.valid_till or ""),
		"discount_percentage": float(qt.additional_discount_percentage or 0),
		"additional_discount_amount": float(qt.discount_amount or 0),
		"freight_amount": _actual_charge("freight"),
		"packing_amount": _actual_charge("packing"),
		"loading_amount": _actual_charge("loading"),
		"other_charges_amount": _actual_charge("other"),
		"tax_template": qt.taxes_and_charges or "",
		"is_inclusive": is_inclusive,
		"cost_center": cost_center or "",
		"price_list": qt.selling_price_list or "",
		"docstatus": qt.docstatus,
		"status": qt.status,
		"custom_customer_name": qt.custom_customer_name or "",
		"custom_address_line1": qt.custom_address_line1 or "",
		"custom_address_line2": qt.custom_address_line2 or "",
		"custom_mobile_number": qt.custom_mobile_number or "",
		"custom_half_tax_discount": qt.custom_half_tax_discount or 0,
		"ewaybill": qt.get("ewaybill") or "",
		"e_waybill_status": qt.get("e_waybill_status") or "",
		"items": items,
	}


# ──────────────────────────────────────────────────────────────────────────────
# Create / Update
# ──────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_quotation(data):
	"""Create a new draft Quotation."""
	if isinstance(data, str):
		data = json.loads(data)

	qt = frappe.new_doc("Quotation")
	qt.naming_series = data.get("naming_series", "SSPL-QT-.YYYY.-")
	qt.quotation_to = "Customer"
	qt.party_name = data["customer"]
	if data.get("customer_address"):
		qt.customer_address = data["customer_address"]
	qt.transaction_date = data.get("date") or frappe.utils.today()
	if data.get("valid_till"):
		qt.valid_till = data["valid_till"]

	if data.get("price_list"):
		qt.selling_price_list = data["price_list"]
	if data.get("tax_template"):
		qt.taxes_and_charges = data["tax_template"]
		qt.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in qt.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1

	if data.get("discount_percentage"):
		qt.additional_discount_percentage = data["discount_percentage"]
	if data.get("additional_discount_amount"):
		qt.discount_amount = data["additional_discount_amount"]

	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			qt.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	for i in data.get("items", []):
		row = {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"uom": i.get("uom"),
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
		}
		if frappe.get_meta("Quotation Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		qt.append("items", row)

	qt.custom_customer_name = data.get("custom_customer_name") or ""
	qt.custom_address_line1 = data.get("custom_address_line1") or ""
	qt.custom_address_line2 = data.get("custom_address_line2") or ""
	qt.custom_mobile_number = data.get("custom_mobile_number") or ""
	qt.custom_half_tax_discount = 1 if data.get("custom_half_tax_discount") else 0

	qt.flags.ignore_permissions = True
	qt.save()

	return {"quotation_name": qt.name}


@frappe.whitelist()
def update_quotation(data):
	"""Update an existing draft Quotation."""
	if isinstance(data, str):
		data = json.loads(data)

	quotation_name = data.get("quotation_name")
	if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
		frappe.throw("Quotation not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	if qt.docstatus != 0:
		frappe.throw("Cannot edit a submitted or cancelled Quotation")

	if qt.party_name != data["customer"]:
		qt.party_name = data["customer"]
		qt.customer_address = data.get("customer_address")
		qt.shipping_address_name = None
		qt.contact_person = None
		qt.contact_display = None
		qt.contact_mobile = None
		qt.contact_email = None
		qt.address_display = None
	elif data.get("customer_address"):
		qt.customer_address = data["customer_address"]

	qt.transaction_date = data.get("date") or qt.transaction_date
	if data.get("valid_till"):
		qt.valid_till = data["valid_till"]
	if data.get("price_list"):
		qt.selling_price_list = data["price_list"]
	if data.get("tax_template"):
		qt.taxes_and_charges = data["tax_template"]
	elif "tax_template" in data:
		qt.taxes_and_charges = ""
	qt.additional_discount_percentage = data.get("discount_percentage", 0)
	qt.discount_amount = data.get("additional_discount_amount", 0)

	if data.get("tax_template"):
		qt.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", data["tax_template"]) or [])
		is_inclusive = data.get("is_inclusive", 0)
		if is_inclusive:
			for tax in qt.taxes:
				if "GST" in (tax.account_head or ""):
					tax.included_in_print_rate = 1
	else:
		qt.taxes = []
	for t in data.get("taxes", []):
		if t.get("tax_amount", 0):
			qt.append("taxes", {
				"charge_type": "Actual",
				"account_head": t.get("account_head", ""),
				"description": t.get("description", ""),
				"tax_amount": t["tax_amount"],
			})

	qt.items = []
	for i in data.get("items", []):
		row = {
			"item_code": i["item_code"],
			"qty": i["qty"],
			"uom": i.get("uom"),
			"rate": i.get("rate", 0),
			"price_list_rate": i.get("price_list_rate", i.get("rate", 0)),
			"discount_percentage": i.get("discount_percentage", 0),
		}
		if frappe.get_meta("Quotation Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		qt.append("items", row)

	qt.custom_customer_name = data.get("custom_customer_name") or ""
	qt.custom_address_line1 = data.get("custom_address_line1") or ""
	qt.custom_address_line2 = data.get("custom_address_line2") or ""
	qt.custom_mobile_number = data.get("custom_mobile_number") or ""
	qt.custom_half_tax_discount = 1 if data.get("custom_half_tax_discount") else 0

	qt.flags.ignore_permissions = True
	qt.save()

	return {"quotation_name": qt.name}

@frappe.whitelist()
def submit_quotation(quotation_name):
	"""Submit a draft Quotation (docstatus 0 → 1)."""
	if not quotation_name or not frappe.db.exists("Quotation", quotation_name):
		frappe.throw("Quotation not found")

	qt = frappe.get_doc("Quotation", quotation_name)
	if qt.docstatus != 0:
		frappe.throw("Quotation is already submitted or cancelled")

	qt.flags.ignore_permissions = True
	qt.submit()

	return {"quotation_name": qt.name, "docstatus": qt.docstatus}

@frappe.whitelist()
def delete_quotation(quotation_name):
	"""Delete a Draft Quotation."""
	frappe.delete_doc("Quotation", quotation_name)
	return {"status": "Deleted"}


def ensure_custom_fields_exist():
	"""Ensure that ewaybill and e_waybill_status custom fields exist on the Quotation doctype."""
	if not frappe.db.exists("Custom Field", {"dt": "Quotation", "fieldname": "ewaybill"}):
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		create_custom_fields({
			"Quotation": [
				{
					"fieldname": "ewaybill",
					"label": "e-Waybill No.",
					"fieldtype": "Data",
					"insert_after": "customer",
					"allow_on_submit": 1,
					"read_only": 1
				},
				{
					"fieldname": "e_waybill_status",
					"label": "e-Waybill Status",
					"fieldtype": "Select",
					"insert_after": "ewaybill",
					"options": "\nPending\nGenerated\nCancelled\nFailed\nNot Applicable",
					"allow_on_submit": 1,
					"read_only": 1
				}
			]
		})
		frappe.db.commit()


@frappe.whitelist()
def generate_eway_bill_for_quotation(
	quotation_name,
	mode_of_transport="Road",
	gst_transporter_id=None,
	transporter_name=None,
	vehicle_no=None,
	gst_vehicle_type="Regular",
	lr_no=None,
	lr_date=None,
	distance=None,
):
	"""
	Generate E-Way Bill for a submitted Quotation entirely in memory:
	1. Mock an in-memory Sales Invoice document.
	2. Build E-Way Bill JSON payload directly from the in-memory document.
	3. Call India Compliance GSP API endpoint.
	4. Save results directly on the Quotation and log in standard e-Waybill Log.
	"""
	ensure_custom_fields_exist()

	q = frappe.get_doc("Quotation", quotation_name)
	if q.docstatus != 1:
		frappe.throw("Quotation must be submitted to generate E-Way Bill.")

	try:
		from erpnext.selling.doctype.quotation.quotation import make_sales_invoice
		si = make_sales_invoice(quotation_name)

		# Set required transport details
		si.name = "MOCK-QTN-INV"  # Must match GST_INVOICE_NUMBER_FORMAT (<= 16 chars)
		si.posting_date = frappe.utils.today()
		si.mode_of_transport = mode_of_transport

		# In sandbox mode, override real transporter ID with sandbox transporter GSTIN to pass NIC sandbox validation
		sandbox_mode = frappe.get_cached_value("GST Settings", "GST Settings", "sandbox_mode")
		if gst_transporter_id and sandbox_mode:
			si.gst_transporter_id = "05AAACG2115R1ZN"
		else:
			si.gst_transporter_id = gst_transporter_id

		si.transporter_name = transporter_name
		si.vehicle_no = vehicle_no
		si.gst_vehicle_type = gst_vehicle_type
		si.lr_no = lr_no
		si.lr_date = lr_date
		if distance:
			si.distance = float(distance)
		si.e_waybill_status = "Pending"

		if not si.debit_to:
			from erpnext.accounts.party import get_party_account
			si.debit_to = get_party_account("Customer", si.customer, si.company)

		from india_compliance.gst_india.utils.e_waybill import (
			EWaybillData,
			EWaybillAPI,
			log_and_process_e_waybill,
		)
		from india_compliance.gst_india.utils import parse_datetime

		# Build JSON payload entirely in-memory
		data = EWaybillData(si).get_data(with_irn=False)

		# Force distance to be integer (GST GSP API expects int, not float)
		if data.get("transDistance"):
			data["transDistance"] = int(data["transDistance"])

		# In sandbox mode, override state codes and pincodes to match the sandbox GSTIN (Uttarakhand - 05)
		# to prevent state-pincode mismatch validation errors from the government sandbox API
		if sandbox_mode:
			data["fromStateCode"] = 5
			data["actFromStateCode"] = 5
			data["fromPincode"] = 248001

			data["toStateCode"] = 5
			data["actToStateCode"] = 5
			data["toPincode"] = 248001

		# Instantiate API and generate e-Waybill without DB persistence
		api = EWaybillAPI.create(si)
		result = api.generate_e_waybill(data)

		eway_bill_no = str(result.get("ewayBillNo"))
		eway_bill_status = result.get("e_waybill_status") or "Generated"

		if not eway_bill_no:
			frappe.throw("E-Way Bill generation failed: No e-Waybill number returned from the server.")

		# Update Quotation directly in DB
		q.db_set({
			"ewaybill": eway_bill_no,
			"e_waybill_status": eway_bill_status
		})

		# Create the e-Waybill Log referencing the Quotation so tracking and PDF attachments work
		sandbox_mode, fetch_data = frappe.get_cached_value(
			"GST Settings", "GST Settings", ["sandbox_mode", "fetch_e_waybill_data"]
		)

		log_data = {
			"e_waybill_number": eway_bill_no,
			"created_on": frappe.utils.now_datetime(),
			"valid_upto": None,
			"reference_doctype": q.doctype,
			"reference_name": q.name,
			"is_generated_in_sandbox_mode": sandbox_mode,
			"is_cancelled": 0,
		}

		if result.get("ewayBillDate"):
			log_data["created_on"] = parse_datetime(result.get("ewayBillDate"), day_first=True)
		if result.get("validUpto"):
			log_data["valid_upto"] = parse_datetime(result.get("validUpto"), day_first=True)

		log_and_process_e_waybill(
			q,
			log_data,
			fetch=fetch_data and eway_bill_status != "Manually Generated",
		)

		return {
			"ewaybill": eway_bill_no,
			"e_waybill_status": eway_bill_status,
			"message": "E-Way Bill generated successfully for Quotation."
		}

	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Quotation E-Way Bill Generation Failed")
		raise


@frappe.whitelist()
def create_quotation_from_sales_invoice(sales_invoice_name, naming_series):
	"""Create a Quotation from a saved Sales Invoice."""
	si = frappe.get_doc("Sales Invoice", sales_invoice_name)

	qt = frappe.new_doc("Quotation")
	qt.naming_series = naming_series
	qt.quotation_to = "Customer"
	qt.party_name = si.customer
	if si.customer_address:
		qt.customer_address = si.customer_address
	qt.transaction_date = frappe.utils.today()

	# Fetch series-specific defaults from SSPL Billing Settings
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	row = next((r for r in settings.billing_series if r.series == naming_series), None)

	tax_template = row.tax_template if row and row.tax_template else ""
	is_inclusive = frappe.utils.cint(row.tax_type_incl) if row else 0

	qt.selling_price_list = (row.price_list if row and row.price_list else si.selling_price_list) or "Standard Selling"

	if tax_template:
		qt.taxes_and_charges = tax_template
		qt.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", tax_template) or [])
		if is_inclusive:
			for tax in qt.taxes:
				if tax.account_head and "GST" in tax.account_head.upper():
					tax.included_in_print_rate = 1

	qt.additional_discount_percentage = si.additional_discount_percentage
	qt.discount_amount = si.discount_amount

	for item in si.items:
		row = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or item.stock_uom or "Nos",
			"warehouse": item.warehouse
		}
		if frappe.get_meta("Quotation Item").has_field("allow_zero_valuation_rate"):
			row["allow_zero_valuation_rate"] = 1
		qt.append("items", row)

	qt.custom_customer_name = si.get("custom_customer_name") or ""
	qt.custom_address_line1 = si.get("custom_address_line1") or ""
	qt.custom_address_line2 = si.get("custom_address_line2") or ""
	qt.custom_mobile_number = si.get("custom_mobile_number") or ""

	qt.flags.ignore_permissions = True
	qt.save()

	return {"status": "success", "quotation_name": qt.name}


@frappe.whitelist()
def create_sales_invoice_from_quotation(
	quotation_name, naming_series, warehouse=None, income_account=None, cost_center=None
):
	"""Create a Sales Invoice from a saved Quotation."""
	qt = frappe.get_doc("Quotation", quotation_name)

	si = frappe.new_doc("Sales Invoice")
	si.naming_series = naming_series
	si.customer = qt.party_name
	if qt.customer_address:
		si.customer_address = qt.customer_address
	si.posting_date = frappe.utils.today()
	si.posting_time = frappe.utils.nowtime()
	si.set_posting_time = 1

	# Fetch series-specific defaults from SSPL Billing Settings
	settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
	row = next((r for r in settings.billing_series if r.series == naming_series), None)

	tax_template = row.tax_template if row and row.tax_template else ""
	is_inclusive = frappe.utils.cint(row.tax_type_incl) if row else 0

	si.selling_price_list = (row.price_list if row and row.price_list else qt.selling_price_list) or "Standard Selling"

	if tax_template:
		si.taxes_and_charges = tax_template
		si.set("taxes", _erpnext_tax_rows("Sales Taxes and Charges Template", tax_template) or [])
		if is_inclusive:
			for tax in si.taxes:
				if tax.account_head and "GST" in tax.account_head.upper():
					tax.included_in_print_rate = 1

	if cost_center:
		si.cost_center = cost_center
		for tax in si.get("taxes", []):
			if not tax.cost_center:
				tax.cost_center = cost_center

	si.additional_discount_percentage = qt.additional_discount_percentage
	si.discount_amount = qt.discount_amount

	for item in qt.items:
		row_item = {
			"item_code": item.item_code,
			"qty": item.qty,
			"rate": item.rate,
			"price_list_rate": item.price_list_rate or item.rate,
			"discount_percentage": item.discount_percentage,
			"uom": item.uom or "Nos",
			"warehouse": warehouse or item.warehouse
		}
		if income_account:
			row_item["income_account"] = income_account
		if cost_center:
			row_item["cost_center"] = cost_center
		si.append("items", row_item)

	if warehouse:
		for row_i in si.items:
			row_i.warehouse = warehouse

	si.custom_customer_name = qt.get("custom_customer_name") or ""
	si.custom_address_line1 = qt.get("custom_address_line1") or ""
	si.custom_address_line2 = qt.get("custom_address_line2") or ""
	si.custom_mobile_number = qt.get("custom_mobile_number") or ""

	si.update_stock = 1

	si.flags.ignore_permissions = True
	si.save()

	return {"status": "success", "invoice_name": si.name}

