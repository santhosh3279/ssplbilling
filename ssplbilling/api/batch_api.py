import frappe
from frappe.utils import flt, getdate


def _batch_item(item_code):
	item = frappe.db.get_value(
		"Item",
		item_code,
		["name", "item_name", "has_batch_no", "create_new_batch", "has_expiry_date", "shelf_life_in_days"],
		as_dict=True,
	)
	if not item:
		frappe.throw(f"Item {item_code} not found")
	if not item.has_batch_no:
		frappe.throw(f"Item {item_code} is not batch tracked")
	return item


@frappe.whitelist()
def get_item_batches(item_code, warehouse=None):
	"""Enabled batches of an item, newest first, with stock in the warehouse (all warehouses when blank)."""
	from erpnext.stock.doctype.batch.batch import get_batch_qty

	item = _batch_item(item_code)
	batches = frappe.get_all(
		"Batch",
		filters={"item": item_code, "disabled": 0},
		fields=["name", "manufacturing_date", "expiry_date", "supplier", "creation"],
		order_by="creation desc",
	)

	# for_stock_levels keeps expired batches in the totals, so every listed batch shows its real stock
	qty = {}
	for row in get_batch_qty(item_code=item_code, warehouse=warehouse or None, for_stock_levels=True) or []:
		qty[row.get("batch_no")] = qty.get(row.get("batch_no"), 0) + flt(row.get("qty"))

	today = getdate()
	return {
		"item_code": item.name,
		"item_name": item.item_name,
		"create_new_batch": item.create_new_batch,
		"has_expiry_date": item.has_expiry_date,
		"shelf_life_in_days": item.shelf_life_in_days,
		"batches": [
			{
				"batch_no": b.name,
				"manufacturing_date": str(b.manufacturing_date) if b.manufacturing_date else "",
				"expiry_date": str(b.expiry_date) if b.expiry_date else "",
				"expired": bool(b.expiry_date and getdate(b.expiry_date) < today),
				"supplier": b.supplier or "",
				"qty": qty.get(b.name, 0),
			}
			for b in batches
		],
	}


@frappe.whitelist()
def create_batch(item_code, batch_id=None, manufacturing_date=None, expiry_date=None, supplier=None):
	"""Create a Batch. A blank batch_id is numbered by the item's series, which needs Automatically
	Create New Batch on the item; a blank expiry is set by Batch from the item's shelf life."""
	item = _batch_item(item_code)
	batch_id = (batch_id or "").strip()
	if not batch_id and not item.create_new_batch:
		frappe.throw("Batch ID is required: the item does not create batch numbers automatically")
	if batch_id and frappe.db.exists("Batch", batch_id):
		frappe.throw(f"Batch {batch_id} already exists")

	batch = frappe.new_doc("Batch")
	batch.item = item_code
	batch.batch_id = batch_id or None
	batch.manufacturing_date = manufacturing_date or None
	batch.expiry_date = expiry_date or None
	batch.supplier = supplier or None
	batch.insert()
	return {
		"batch_no": batch.name,
		"manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else "",
		"expiry_date": str(batch.expiry_date) if batch.expiry_date else "",
		"expired": False,
		"supplier": batch.supplier or "",
		"qty": 0,
	}
