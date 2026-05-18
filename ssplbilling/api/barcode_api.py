import frappe
import json

@frappe.whitelist()
def create_barcode_print_entry(items, bill_no=None, price_list=None):
        """
        Create a Barcode_Prinitng document.
        Removed rate/valuation_rate as per request.

        Returns:
                name of the created Barcode_Prinitng document
        """
        if isinstance(items, str):
                items = json.loads(items)

        if not items:
                frappe.throw("No items provided for barcode printing")

        doc = frappe.new_doc("Barcode_Prinitng")

        if bill_no:
                doc.bill_no = bill_no

        for item in items:
                item_code = item.get("item_code")
                if not item_code:
                        continue

                doc.append("items", {
                        "item_code": item_code,
                        "item_name": item.get("item_name") or "",
                        "qty": int(item.get("qty") or 1),
                        "barcode": item.get("barcode") or "",
                })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return doc.name
