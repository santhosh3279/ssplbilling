import frappe
import json

@frappe.whitelist()
def get_item_prices(item_code):
    """Fetch all Item Price records for an item, including both selling and buying."""
    if not item_code:
        return []

    # Get all active price lists
    price_lists = frappe.get_all("Price List", filters={"enabled": 1}, fields=["name", "buying", "selling"])
    
    # Get existing item prices
    item_prices = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code},
        fields=["price_list", "price_list_rate", "currency", "name"]
    )
    
    price_map = {p.price_list: p for p in item_prices}
    
    results = []
    for pl in price_lists:
        existing = price_map.get(pl.name)
        results.append({
            "price_list": pl.name,
            "buying": pl.buying,
            "selling": pl.selling,
            "rate": float(existing.price_list_rate) if existing else 0.0,
            "exists": True if existing else False,
            "item_price_name": existing.name if existing else None
        })
        
    return results

@frappe.whitelist()
def update_item_price(item_code, price_list, rate):
    """Update or create an Item Price record."""
    rate = float(rate)
    
    # Check if entry exists
    existing_name = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list}, "name")
    
    if existing_name:
        doc = frappe.get_doc("Item Price", existing_name)
        doc.price_list_rate = rate
        doc.save()
    else:
        doc = frappe.new_doc("Item Price")
        doc.item_code = item_code
        doc.price_list = price_list
        doc.price_list_rate = rate
        doc.insert()
        
    return doc.name

@frappe.whitelist()
def update_multiple_prices(item_code, prices):
    """Update multiple prices at once."""
    if isinstance(prices, str):
        prices = json.loads(prices)
        
    updated = []
    for p in prices:
        name = update_item_price(item_code, p['price_list'], p['rate'])
        updated.append(name)
        
    return updated
