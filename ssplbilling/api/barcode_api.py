import frappe
import json

@frappe.whitelist()
def create_barcode_print_entry(items, bill_no=None, price_lists=None):
        """
        Create a Barcode_Printing document.
        Removed rate/valuation_rate as per request.

        Returns:
                name of the created Barcode_Printing document
        """
        if isinstance(items, str):
                items = json.loads(items)

        if price_lists and isinstance(price_lists, str):
                price_lists = json.loads(price_lists)

        if not items:
                frappe.throw("No items provided for barcode printing")

        doc = frappe.new_doc("Barcode_Printing")

        if bill_no:
                doc.bill_no = bill_no

        if price_lists:
                for idx, pl in enumerate(price_lists):
                        if idx < 10:
                                doc.set(f"price_list_{idx + 1}", pl)

        for item in items:
                item_code = item.get("item_code")
                if not item_code:
                        continue

                doc.append("items", {
                        "item_code": item_code,
                        "item_name": item.get("item_name") or "",
                        "uom": item.get("uom") or "Nos",
                        "qty": int(item.get("qty") or 1),
                        "barcode": item.get("barcode") or "",
                        "rate_1": float(item.get("rate_1") or 0),
                        "rate_2": float(item.get("rate_2") or 0),
                        "rate_3": float(item.get("rate_3") or 0),
                        "rate_4": float(item.get("rate_4") or 0),
                        "rate_5": float(item.get("rate_5") or 0),
                        "rate_6": float(item.get("rate_6") or 0),
                        "rate_7": float(item.get("rate_7") or 0),
                        "rate_8": float(item.get("rate_8") or 0),
                        "rate_9": float(item.get("rate_9") or 0),
                        "rate_10": float(item.get("rate_10") or 0),
                })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return doc.name
