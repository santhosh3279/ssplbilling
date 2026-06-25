import json
import frappe
from frappe import _

@frappe.whitelist()
def get_customer_details(customer):
    """Return customer details for Sales Invoice header."""
    from ssplbilling.api.customersearch_api import get_customer_full
    return get_customer_full(customer)

@frappe.whitelist()
def get_next_invoice_no(naming_series):
    """Get next available invoice number."""
    from frappe.model.naming import parse_naming_series
    return parse_naming_series(naming_series)

@frappe.whitelist()
def get_series_defaults(naming_series, doctype="Sales Invoice"):
    """Return naming series defaults and the next available number."""
    from frappe.model.naming import parse_naming_series
    
    # 1. Get next invoice number
    next_no = parse_naming_series(naming_series)
    
    # 2. Get series-specific defaults from SSPL Billing Settings
    settings = frappe.get_cached_doc("SSPL Billing Settings", "SSPL Billing Settings")
    row = next((r for r in settings.billing_series if r.series == naming_series), None)
    
    # 3. Get user-specific defaults (if any)
    user_row = next((r for r in settings.user_series if r.user == frappe.session.user), None)
    
    res = {
        "invoice_no": next_no,
        "price_list": row.price_list if row and row.price_list else ("Standard Selling" if "Sales" in doctype or doctype == "Quotation" else "Standard Buying"),
        "tax_template": row.tax_template if row and row.tax_template else "",
        "print_format": row.print_format if row and row.print_format else "",
        "warehouse": (user_row.warehouse if user_row and user_row.warehouse else ""),
        "cost_center": (user_row.cost_center if user_row and user_row.cost_center else ""),
        "income_account": (user_row.income_account if user_row and user_row.income_account else ""),
    }
    
    # Handle different field names for order/invoice number
    if doctype == "Sales Order":
        res["order_no"] = next_no
    elif doctype == "Purchase Order":
        res["order_no"] = next_no
    elif doctype == "Quotation":
        res["quotation_no"] = next_no
        
    return res

@frappe.whitelist()
def generate_eway_bill_for_sales_invoice(
	invoice_name,
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
	Generate E-Way Bill for a submitted Sales Invoice:
	1. Load existing submitted Sales Invoice document.
	2. Update transport fields directly via db_set.
	3. Build E-Way Bill JSON payload entirely in-memory.
	4. Call GSP API to generate E-Way Bill.
	5. Save result directly on the Sales Invoice and create standard log.
	"""
	si = frappe.get_doc("Sales Invoice", invoice_name)
	if si.docstatus != 1:
		frappe.throw(_("Sales Invoice must be submitted to generate E-Way Bill."))

	try:
		# In sandbox mode, override real transporter ID with sandbox transporter GSTIN to pass NIC sandbox validation
		sandbox_mode = frappe.get_cached_value("GST Settings", "GST Settings", "sandbox_mode")
		mapped_transporter_id = "05AAACG2115R1ZN" if (gst_transporter_id and sandbox_mode) else gst_transporter_id

		# Update database fields on the submitted invoice
		update_data = {
			"mode_of_transport": mode_of_transport,
			"gst_transporter_id": mapped_transporter_id,
			"transporter_name": transporter_name,
			"vehicle_no": vehicle_no,
			"gst_vehicle_type": gst_vehicle_type,
			"lr_no": lr_no,
			"lr_date": lr_date,
		}
		if distance:
			update_data["distance"] = float(distance)
		
		# Also update in-memory object attributes so EWaybillData reads them
		si.db_set(update_data)
		for k, v in update_data.items():
			setattr(si, k, v)

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

		# Instantiate API and generate e-Waybill
		api = EWaybillAPI.create(si)
		result = api.generate_e_waybill(data)

		eway_bill_no = str(result.get("ewayBillNo"))
		eway_bill_status = result.get("e_waybill_status") or "Generated"

		if not eway_bill_no:
			frappe.throw(_("E-Way Bill generation failed: No e-Waybill number returned from the server."))

		# Update Sales Invoice with generated info
		si.db_set({
			"ewaybill": eway_bill_no,
			"e_waybill_status": eway_bill_status
		})

		# Create log
		fetch_data = frappe.get_cached_value("GST Settings", "GST Settings", "fetch_e_waybill_data")
		log_data = {
			"e_waybill_number": eway_bill_no,
			"created_on": frappe.utils.now_datetime(),
			"valid_upto": None,
			"reference_doctype": si.doctype,
			"reference_name": si.name,
			"is_generated_in_sandbox_mode": sandbox_mode,
			"is_cancelled": 0,
		}

		if result.get("ewayBillDate"):
			log_data["created_on"] = parse_datetime(result.get("ewayBillDate"), day_first=True)
		if result.get("validUpto"):
			log_data["valid_upto"] = parse_datetime(result.get("validUpto"), day_first=True)

		log_and_process_e_waybill(
			si,
			log_data,
			fetch=fetch_data and eway_bill_status != "Manually Generated",
		)

		return {
			"ewaybill": eway_bill_no,
			"e_waybill_status": eway_bill_status,
			"message": "E-Way Bill generated successfully for Sales Invoice."
		}

	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Sales Invoice E-Way Bill Generation Failed")
		raise


@frappe.whitelist()
def record_bill_edit(bill_no):
	"""Record the bill no and username in Redis cache.
	Check if it is already being edited by another user."""
	if not bill_no:
		return {"status": "error", "message": "Bill number is required"}

	cache_key = f"ssplbilling:editing_bill:{bill_no}"
	current_editor = frappe.cache().get_value(cache_key)

	if current_editor and current_editor != frappe.session.user:
		user_info = frappe.db.get_value("User", current_editor, "full_name") or current_editor
		return {"status": "conflict", "user": user_info}

	frappe.cache().set_value(cache_key, frappe.session.user, expires_in_sec=7200)
	return {"status": "success"}


@frappe.whitelist()
def release_bill_edit(bill_no):
	"""Remove the bill no and username from Redis cache."""
	if not bill_no:
		return {"status": "error", "message": "Bill number is required"}

	cache_key = f"ssplbilling:editing_bill:{bill_no}"
	frappe.cache().delete_value(cache_key)
	return {"status": "success"}


@frappe.whitelist()
def get_locked_bills():
	"""Get all currently locked bills from Redis."""
	prefix = "ssplbilling:editing_bill:"
	raw_keys = frappe.cache().get_keys(prefix)

	locked_bills = []
	db_prefix = f"{frappe.local.conf.get('db_name')}|"

	for key in raw_keys:
		key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
		if key_str.startswith(db_prefix):
			key_str = key_str[len(db_prefix):]

		if key_str.startswith(prefix):
			bill_no = key_str[len(prefix):]
			editor = frappe.cache().get_value(key_str)
			if editor:
				user_info = frappe.db.get_value("User", editor, "full_name") or editor
				locked_bills.append({
					"bill_no": bill_no,
					"username": editor,
					"fullname": user_info
				})

	return locked_bills


