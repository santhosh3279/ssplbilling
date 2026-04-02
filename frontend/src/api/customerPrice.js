import { frappePost } from '../api.js'

/**
 * Save a specific discount percentage for a customer-item combination.
 */
export async function saveCustomerItemPrice(customer, itemCode, discountPercentage) {
  return frappePost('ssplbilling.api.customer_pricing_api.save_customer_item_price', {
    customer,
    item_code: itemCode,
    discount_percentage: discountPercentage,
  })
}

/**
 * Update the rate for an item in a specific price list, optionally for a specific UOM.
 */
export async function updateItemPriceList(itemCode, priceList, rate, uom = '') {
  return frappePost('ssplbilling.api.pricelist_api.update_item_price', {
    item_code: itemCode,
    price_list: priceList,
    rate,
    uom: uom || "",
  })
}
