import { frappeGet, frappePost } from '../api.js'
import { session } from '../session.js'

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
    return frappeGet(`${API_BASE}.get_allowed_series`, {
      user: session.user.value
    })
  },

  /**
   * Save the user-specific zoom preference to the server.
   */
  saveDefaultZoom: (zoom) => {
    return frappePost(`${API_BASE}.save_default_zoom`, {
      user: session.user.value,
      zoom: zoom
    })
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
   * Return current server RAM and CPU usage.
   */
  getSystemStats: () => {
    return frappeGet(`${API_BASE}.get_system_stats`)
  },

  /**
   * Drop Linux page cache and return updated RAM stats.
   */
  clearRamCache: () => {
    return frappePost(`${API_BASE}.clear_ram_cache`)
  },

  /**
   * Run the site backup script and return its output.
   */
  runManualBackup: () => {
    return frappePost(`${API_BASE}.run_manual_backup`)
  },

  /**
   * Return all active site names in this bench.
   */
  getActiveSites: () => {
    return frappeGet(`${API_BASE}.get_active_sites`)
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
