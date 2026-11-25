import json
import frappe
from frappe import _

@frappe.whitelist()
def get_repack_details(name):
    """Return Stock Entry details for Repack."""
    doc = frappe.get_doc("Stock Entry", name)
    doc_dict = doc.as_dict()
    
    items = []
    for item in doc.items:
        item_dict = item.as_dict()
        # In a Repack entry, consumed items have s_warehouse and no t_warehouse.
        # Produced items have t_warehouse and no s_warehouse.
        if item.s_warehouse and not item.t_warehouse:
            item_dict["type"] = "Consume"
        elif item.t_warehouse and not item.s_warehouse:
            item_dict["type"] = "Produce"
        else:
            item_dict["type"] = "Consume" if item.s_warehouse else "Produce"
        
        # Add rate/amount mapping for frontend
        # basic_rate is per stock UOM; the page works in the row's UOM
        item_dict["rate"] = float(item.basic_rate or 0) * float(item.conversion_factor or 1)
        item_dict["amount"] = float(item.amount or 0)
        items.append(item_dict)
        
    doc_dict["items"] = items
    # ERPNext clears header warehouses on Repack save; recover them from the rows
    if not doc_dict.get("from_warehouse"):
        doc_dict["from_warehouse"] = next((i.s_warehouse for i in doc.items if i.s_warehouse), None)
    if not doc_dict.get("to_warehouse"):
        doc_dict["to_warehouse"] = next((i.t_warehouse for i in doc.items if i.t_warehouse), None)
    return doc_dict

@frappe.whitelist()
def save_repack(data):
    """Create or update a Stock Entry for Repack."""
    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    if name:
        se = frappe.get_doc("Stock Entry", name)
        if se.docstatus != 0:
            frappe.throw(_("Cannot update a submitted or cancelled Stock Entry."))
    else:
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Repack"
        se.purpose = "Repack"
        se.naming_series = data.get("naming_series") or "MAT-REP-.YYYY.-"

    if data.get("company"):
        se.company = data["company"]
    se.posting_date = data.get("posting_date") or frappe.utils.today()
    se.posting_time = data.get("posting_time") or se.posting_time or frappe.utils.nowtime()
    # Without this, ERPNext's validate_posting_time resets date/time to now on every save
    se.set_posting_time = 1
    se.from_warehouse = data.get("from_warehouse")  # Default Source
    se.to_warehouse = data.get("to_warehouse")      # Default Destination
    if "remarks" in data:
        se.remarks = data.get("remarks") or ""

    items_list = data.get("items") or []
    fg_count = sum(1 for row in items_list if row.get("type") == "Produce")

    se.items = []
    for row in items_list:
        is_consume = row.get("type") == "Consume"
        s_wh = row.get("s_warehouse") or (se.from_warehouse if is_consume else None)
        t_wh = row.get("t_warehouse") or (se.to_warehouse if not is_consume else None)
        
        # ERPNext Repack logic:
        # Raw materials: source warehouse set, target warehouse is None.
        # Finished goods: target warehouse set, source warehouse is None.
        if is_consume:
            t_wh = None
        else:
            s_wh = None

        # The page's rate is per the row's UOM; basic_rate is per stock UOM
        conversion_factor = _uom_conversion_factor(row.get("item_code"), row.get("uom"))
        item_doc = {
            "item_code": row.get("item_code"),
            "qty": float(row.get("qty") or 0),
            "uom": row.get("uom"),
            "conversion_factor": conversion_factor,
            "s_warehouse": s_wh,
            "t_warehouse": t_wh,
            "basic_rate": float(row.get("rate") or 0) / conversion_factor,
        }
        # Several produced rows, or a rate typed by the user, must not be recalculated by ERPNext
        if not is_consume and (fg_count > 1 or row.get("rate_manual")):
            item_doc["set_basic_rate_manually"] = 1
        
        se.append("items", item_doc)

    if name:
        se.save()
    else:
        se.insert()

    return {
        "name": se.name,
        "posting_time": str(se.posting_time),
        "status": "Draft"
    }

def _uom_conversion_factor(item_code, uom):
    """Stock UOMs held by one `uom` of the item (1 for the stock UOM or when unknown)."""
    if not uom:
        return 1.0
    from erpnext.stock.get_item_details import get_conversion_factor

    return float(get_conversion_factor(item_code, uom).get("conversion_factor") or 1)

@frappe.whitelist()
def submit_repack(name):
    """Submit a Stock Entry for Repack."""
    doc = frappe.get_doc("Stock Entry", name)
    # Keep the draft's own date; without the flag ERPNext resets it to now on submit
    doc.set_posting_time = 1
    doc.submit()
    return {"status": "Submitted"}

@frappe.whitelist()
def get_metadata(company=None):
    """Fetch metadata for Repack."""
    filters = {"is_group": 0}
    if company:
        filters["company"] = company
    return {
        "warehouses": frappe.get_all("Warehouse", filters=filters, fields=["name"]),
        "naming_series": get_naming_series()
    }

def get_naming_series():
    """Get naming series for Stock Entry Repack."""
    try:
        meta = frappe.get_meta("Stock Entry")
        series_field = meta.get_field("naming_series")
        if series_field and series_field.options:
            options = [s.strip() for s in series_field.options.split("\n") if s.strip()]
            # Put Repack series first if available
            repack_options = [o for o in options if "REP" in o]
            other_options = [o for o in options if "REP" not in o]
            return repack_options + other_options
    except Exception:
        pass
    return ["MAT-REP-.YYYY.-", "STE-.YYYY.-"]

@frappe.whitelist()
def get_recent_repacks(date=None, draft_only=False):
    """Get Repack Stock Entries for the sidebar: one date's, or all drafts of every date."""
    draft_only = frappe.parse_json(draft_only)
    filters = {"purpose": "Repack"}
    if draft_only:
        filters["docstatus"] = 0
    else:
        filters["posting_date"] = date or frappe.utils.today()

    repacks = frappe.get_all(
        "Stock Entry",
        filters=filters,
        fields=["name", "total_amount as grand_total", "from_warehouse", "to_warehouse", "docstatus", "posting_date"],
        order_by="creation desc"
    )
    
    for r in repacks:
        r["customer_name"] = f"{r.from_warehouse or ''} -> {r.to_warehouse or ''}"
        if draft_only:
            # The list spans dates, so each row shows its own
            r["customer_name"] = f"{frappe.utils.formatdate(r.posting_date, 'dd-MM-yyyy')} {r['customer_name']}"

    return repacks
