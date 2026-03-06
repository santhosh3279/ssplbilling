import { frappeGet, frappePost } from '../api.js'

const API_BASE = 'ssplbilling.api.dashboard_api'

export const dashboardApi = {
  /**
   * Return all SSPL Billing Settings data as a read-only summary for the dashboard.
   */
  getBillingSettings: () => {
    return frappeGet(`${API_BASE}.get_billing_settings`)
  },

  /**
   * Return a list of naming series allowed for the current user.
   */
  getAllowedSeries: () => {
    return frappeGet(`${API_BASE}.get_allowed_series`)
  },

  /**
   * Fetch all sales items for local sync.
   */
  fetchAllItemsForSync: () => {
    return frappeGet('frappe.client.get_list', {
      doctype: 'Item',
      fields: ['item_code', 'item_name', 'stock_uom as uom', 'standard_rate as rate'],
      filters: { disabled: 0, is_sales_item: 1 },
      limit_page_length: 5000,
      order_by: 'item_name asc'
    })
  },

  /**
   * Fetch all customers for local sync.
   */
  fetchAllCustomersForSync: () => {
    return frappeGet('frappe.client.get_list', {
      doctype: 'Customer',
      fields: ['name', 'customer_name', 'mobile_no'],
      filters: { disabled: 0 },
      limit_page_length: 5000,
      order_by: 'customer_name asc'
    })
  }
}
