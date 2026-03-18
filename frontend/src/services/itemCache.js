import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for items
const items = ref([])
const lastSync = ref(0)
const syncLoading = ref(false)
const lastParams = ref({ searchType: null, priceList: null, warehouse: null })

// Global pricing rules cache
const pricingRules = ref([])

// Global cache for customer sales history
const customerSalesHistory = ref([])
const currentCustomerForHistory = ref(null)
const historyLoading = ref(false)

/**
 * Fetch all items with details from the backend and update the global cache.
 * Also syncs pricing rules in parallel.
 */
export async function refreshItemCache(searchType = 'Sales', priceList = null, warehouse = null) {
  syncLoading.value = true
  try {
    const [data, rules] = await Promise.all([
      frappeGet('ssplbilling.api.itemsearch_api.get_all_items_detailed', {
        search_type: searchType,
        price_list: priceList,
        warehouse: warehouse
      }),
      frappeGet('ssplbilling.api.itemsearch_api.get_pricing_rules', {
        price_list: priceList || ''
      }).catch(() => [])
    ])
    items.value = data || []
    pricingRules.value = rules || []
    lastSync.value = Date.now()
    lastParams.value = { searchType, priceList, warehouse }
    return items.value
  } catch (e) {
    console.error('[itemCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

/**
 * Apply the best matching pricing rule for an item.
 * Returns { discount_percentage, rate } or null if no rule matches.
 */
export function applyPricingRule(item_code, qty = 1, customer = null) {
  if (!pricingRules.value.length) return null

  const matching = pricingRules.value.filter(rule => {
    // Skip disabled rules
    if (rule.disable) return false
    // Item code filter
    if (rule.apply_on === 'Item Code' && rule.item_codes.length && !rule.item_codes.includes(item_code)) return false
    // Qty range
    if (rule.min_qty > 0 && qty < rule.min_qty) return false
    if (rule.max_qty > 0 && qty > rule.max_qty) return false
    // Customer filter
    if (rule.applicable_for === 'Customer' && rule.customer && rule.customer !== customer) return false
    return true
  })

  if (!matching.length) return null

  const rule = matching[0] // highest priority (already sorted asc)
  if (rule.rate_or_discount === 'Discount Percentage' && rule.discount_percentage > 0) {
    return { discount_percentage: rule.discount_percentage, rate: null }
  }
  if (rule.rate_or_discount === 'Rate' && rule.rate > 0) {
    return { discount_percentage: 0, rate: rule.rate }
  }
  return null
}

/**
 * Fetch and cache previous sales history for a customer.
 */
export async function fetchCustomerSalesHistory(customer) {
  if (!customer) {
    customerSalesHistory.value = []
    currentCustomerForHistory.value = null
    return
  }
  
  if (currentCustomerForHistory.value === customer) return

  historyLoading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.itemsearch_api.get_customer_sales_history', {
      customer: customer
    })
    customerSalesHistory.value = data || []
    currentCustomerForHistory.value = customer
  } catch (e) {
    console.warn('[itemCache] History fetch failed:', e)
    customerSalesHistory.value = []
  } finally {
    historyLoading.value = false
  }
}

/**
 * Look up an item by code or barcode in the local cache.
 */
export function lookupItemInCache(code) {
  if (!code) return null
  const cleanCode = code.trim().toLowerCase()
  
  // Try direct match
  return items.value.find(i => 
    (i.item_code || '').toLowerCase() === cleanCode
  ) || null
}

/**
 * Check if an item has history with the currently cached customer.
 */
export function hasHistory(itemCode) {
  if (!itemCode || !customerSalesHistory.value.length) return false
  return customerSalesHistory.value.some(h => h.item_code === itemCode)
}

/**
 * Get the history for a specific item from the cache.
 */
export function getItemHistoryFromCache(itemCode) {
  if (!itemCode) return []
  return customerSalesHistory.value.filter(h => h.item_code === itemCode)
}

export function useItemCache() {
  return {
    items,
    lastSync,
    syncLoading,
    lastParams,
    refreshItemCache,
    lookupItemInCache,
    // Pricing rules
    pricingRules,
    applyPricingRule,
    // History
    customerSalesHistory,
    currentCustomerForHistory,
    historyLoading,
    fetchCustomerSalesHistory,
    hasHistory,
    getItemHistoryFromCache
  }
}
