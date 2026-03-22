import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for items
const items = ref([])
const lastSync = ref(0)
const syncLoading = ref(false)
const lastParams = ref({ searchType: null, priceList: null, warehouse: null })

// Discount Rules cache (custom Discount Rule doctype) — persisted to localStorage
const DISCOUNT_RULES_KEY = 'sspl-discount-rules'
function loadDiscountRulesFromStorage() {
  try { return JSON.parse(localStorage.getItem(DISCOUNT_RULES_KEY) || '[]') } catch { return [] }
}
export function saveDiscountRulesToStorage(rules) {
  try { localStorage.setItem(DISCOUNT_RULES_KEY, JSON.stringify(rules)) } catch {}
}
const discountRules = ref(loadDiscountRulesFromStorage())

// Global cache for customer sales history
const customerSalesHistory = ref([])
const currentCustomerForHistory = ref(null)
const historyLoading = ref(false)

/**
 * Fetch all items with details from the backend and update the global cache.
 * Also syncs discount rules in parallel.
 */
export async function refreshItemCache(searchType = 'Sales', priceList = null, warehouse = null) {
  syncLoading.value = true
  try {
    const [data, discRules] = await Promise.all([
      frappeGet('ssplbilling.api.itemsearch_api.get_all_items_detailed', {
        search_type: searchType,
        price_list: priceList,
        warehouse: warehouse
      }),
      frappeGet('ssplbilling.api.sales_api.get_discount_rules').catch(() => [])
    ])
    items.value = data || []
    discountRules.value = discRules || []
    saveDiscountRulesToStorage(discountRules.value)
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
 * Refresh only the Discount Rules cache from the backend.
 */
export async function refreshDiscountRuleCache() {
  try {
    const data = await frappeGet('ssplbilling.api.sales_api.get_discount_rules')
    discountRules.value = data || []
    saveDiscountRulesToStorage(discountRules.value)
    return discountRules.value
  } catch (e) {
    console.warn('[itemCache] Discount rule refresh failed:', e)
    return discountRules.value
  }
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
    // Discount Rules (custom doctype)
    discountRules,
    refreshDiscountRuleCache,
    saveDiscountRulesToStorage,
    // History
    customerSalesHistory,
    currentCustomerForHistory,
    historyLoading,
    fetchCustomerSalesHistory,
    hasHistory,
    getItemHistoryFromCache
  }
}
