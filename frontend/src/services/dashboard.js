import { frappeGet, frappePost } from '../api.js'
import { session } from '../session.js'

const API_BASE = 'ssplbilling.api.dashboard_api'

export const dashboardApi = {
  /**
   * Return all users from SSPL Billing Settings.
   */
  getAllUsers: () => {
    return frappeGet(`${API_BASE}.get_all_users`)
  },

  /**
   * Return naming series for multiple DocTypes.
   */
  getAllNamingSeries: () => {
    return frappeGet(`${API_BASE}.get_all_naming_series`)
  },

  /**
   * Return all SSPL Billing Settings data as a read-only summary for the dashboard.
   */
  getBillingSettings: (user = null) => {
    return frappeGet(`${API_BASE}.get_billing_settings`, { user })
  },

  /**
   * Return a list of naming series allowed for the current or specified user.
   */
  getAllowedSeries: (user = null) => {
    return frappeGet(`${API_BASE}.get_allowed_series`, {
      user: user || session.user.value
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
      limit_page_length: 15000,
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
   * Return users currently active on this site (last 15 min).
   */
  getActiveSessions: () => {
    return frappeGet(`${API_BASE}.get_active_sessions`)
  },

  /**
   * Fetch all customers for local sync.
   */
  fetchAllCustomersForSync: () => {
    return frappeGet('frappe.client.get_list', {
      doctype: 'Customer',
      fields: ['name', 'customer_name', 'mobile_no'],
      filters: { disabled: 0 },
      limit_page_length: 15000,
      order_by: 'customer_name asc'
    })
  },

  /**
   * Fetch Sales/Purchase Tax Templates and Price Lists for synchronization.
   */
  getSyncMetadata: () => {
    return frappeGet('ssplbilling.api.SaleEntry_api.get_sync_metadata')
  }
}
