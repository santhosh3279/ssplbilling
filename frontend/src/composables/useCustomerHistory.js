import { ref } from 'vue'
import { frappeGet } from '../api.js'
import { lookupItemInCache } from '../services/itemCache.js'

/**
 * Composable to manage customer sales history for a specific window/session.
 * Unlike itemCache, this does not use a global singleton so it can be cleared independently.
 */
// Global state for sharing across components
const customerSalesHistory = ref([])
const currentCustomerForHistory = ref(null)
const supplierPurchaseHistory = ref([])
const currentSupplierForHistory = ref(null)
const historyLoading = ref(false)

const otherSuppliersItemHistory = ref([])
const otherSuppliersHistoryLoading = ref(false)

const itemStock = ref([])
const stockLoading = ref(false)
const stockCache = new Map()

const itemPrices = ref([])
const pricesLoading = ref(false)
const pricesCache = new Map()

export function useCustomerHistory() {

  /**
   * Fetch and cache previous sales history for a customer.
   */
  async function fetchCustomerSalesHistory(customer) {
    if (!customer) {
      clearHistory()
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
      console.warn('[customerHistory] History fetch failed:', e.message)
      customerSalesHistory.value = []
    } finally {
      historyLoading.value = false
    }
  }

  async function fetchSupplierPurchaseHistory(supplier) {
    if (!supplier) {
      clearHistory()
      return
    }

    if (currentSupplierForHistory.value === supplier) return

    historyLoading.value = true
    try {
      const data = await frappeGet('ssplbilling.api.itemsearch_api.get_supplier_purchase_history', {
        supplier: supplier
      })
      supplierPurchaseHistory.value = data || []
      currentSupplierForHistory.value = supplier
    } catch (e) {
      console.warn('[customerHistory] Supplier history fetch failed:', e.message)
      supplierPurchaseHistory.value = []
    } finally {
      historyLoading.value = false
    }
  }

  /**
   * Fetch warehouse-wise stock levels for a specific item.
   */
  async function fetchItemStock(itemCode) {
    if (!itemCode) return

    // Try local cache lookup first
    const cachedItem = lookupItemInCache(itemCode)
    if (cachedItem) {
      itemStock.value = cachedItem.warehouse_stock || []
      return
    }

    if (stockCache.has(itemCode)) {
      itemStock.value = stockCache.get(itemCode)
      return
    }

    stockLoading.value = true
    try {
      const data = await frappeGet('ssplbilling.api.stock_api.get_warehouse_stock', {
        item_code: itemCode
      })
      const results = data || []
      stockCache.set(itemCode, results)
      itemStock.value = results
    } catch (e) {
      console.warn('[customerHistory] Stock fetch failed:', e.message)
      itemStock.value = []
    } finally {
      stockLoading.value = false
    }
  }

  /**
   * Fetch available price lists and rates for a specific item.
   */
  async function fetchItemPrices(itemCode) {
    if (!itemCode) return

    // Try local cache lookup first
    const cachedItem = lookupItemInCache(itemCode)
    if (cachedItem) {
      let localLists = []
      try {
        localLists = JSON.parse(localStorage.getItem('wb-pricelist') || '[]')
      } catch {}
      
      if (!localLists.length) {
        localLists = (cachedItem.price_lists || []).map(pl => pl.name)
      }

      const results = localLists.map(plName => {
        const plRecord = (cachedItem.price_lists || []).find(p => p.name === plName)
        let rate = plRecord ? plRecord.rate : 0.0
        
        if (rate === 0.0 && cachedItem.uom_price_lists?.[plName]) {
          const uomMap = cachedItem.uom_price_lists[plName]
          const stdUom = cachedItem.uom || ''
          if (stdUom && uomMap[stdUom] !== undefined) {
            rate = uomMap[stdUom]
          } else {
            const values = Object.values(uomMap)
            if (values.length > 0) {
              rate = values[0]
            }
          }
        }

        const buying = plRecord ? (plRecord.buying ? 1 : 0) : 0
        const selling = plRecord ? (plRecord.selling ? 1 : 0) : 1
        
        return {
          price_list: plName,
          price: rate,
          rate: rate,
          buying: buying,
          selling: selling,
          uom_rates: (cachedItem.uom_price_lists || {})[plName] || {}
        }
      })
      
      itemPrices.value = results
      return
    }

    if (pricesCache.has(itemCode)) {
      itemPrices.value = pricesCache.get(itemCode)
      return
    }

    pricesLoading.value = true
    try {
      const res = await frappeGet('ssplbilling.api.pricelist_api.get_item_prices', {
        item_code: itemCode
      })
      const results = res?.prices || []
      pricesCache.set(itemCode, results)
      itemPrices.value = results
    } catch (e) {
      console.warn('[customerHistory] Prices fetch failed:', e.message)
      itemPrices.value = []
    } finally {
      pricesLoading.value = false
    }
  }

  /**
   * Check if an item has history with the currently cached customer.
   */
  function hasHistory(itemCode) {
    if (!itemCode || !customerSalesHistory.value.length) return false
    return customerSalesHistory.value.some(h => h.item_code === itemCode)
  }

  /**
   * Get the history for a specific item from the cache.
   */
  function getItemHistoryFromCache(itemCode) {
    if (!itemCode) return []
    return customerSalesHistory.value.filter(h => h.item_code === itemCode)
  }

  function hasSupplierHistory(itemCode) {
    if (!itemCode || !supplierPurchaseHistory.value.length) return false
    return supplierPurchaseHistory.value.some(h => h.item_code === itemCode)
  }

  function getSupplierItemHistoryFromCache(itemCode) {
    if (!itemCode) return []
    return supplierPurchaseHistory.value.filter(h => h.item_code === itemCode)
  }

  async function fetchOtherSuppliersItemHistory(itemCode, currentSupplier) {
    if (!itemCode) {
      otherSuppliersItemHistory.value = []
      return
    }
    otherSuppliersHistoryLoading.value = true
    try {
      const data = await frappeGet('ssplbilling.api.itemsearch_api.get_item_purchase_history', {
        item_code: itemCode,
        current_supplier: currentSupplier || ''
      })
      otherSuppliersItemHistory.value = data || []
    } catch (e) {
      console.warn('[customerHistory] Other suppliers history fetch failed:', e.message)
      otherSuppliersItemHistory.value = []
    } finally {
      otherSuppliersHistoryLoading.value = false
    }
  }

  /**
   * Clear item-specific insights (stock and prices).
   * Keeps customerSalesHistory intact.
   */
  function clearItemInsights() {
    otherSuppliersItemHistory.value = []
    otherSuppliersHistoryLoading.value = false
    itemStock.value = []
    stockLoading.value = false
    itemPrices.value = []
    pricesLoading.value = false
    stockCache.clear()
    pricesCache.clear()
  }

  /**
   * Clear all history details.
   */
  function clearHistory() {
    customerSalesHistory.value = []
    currentCustomerForHistory.value = null
    supplierPurchaseHistory.value = []
    currentSupplierForHistory.value = null
    historyLoading.value = false
    clearItemInsights()
  }

  return {
    customerSalesHistory,
    currentCustomerForHistory,
    supplierPurchaseHistory,
    currentSupplierForHistory,
    historyLoading,
    fetchCustomerSalesHistory,
    fetchSupplierPurchaseHistory,
    hasHistory,
    getItemHistoryFromCache,
    hasSupplierHistory,
    getSupplierItemHistoryFromCache,
    clearHistory,
    clearItemInsights,
    // Stock levels
    itemStock,
    stockLoading,
    fetchItemStock,
    // Price lists
    itemPrices,
    pricesLoading,
    fetchItemPrices,
    // Other suppliers history
    otherSuppliersItemHistory,
    otherSuppliersHistoryLoading,
    fetchOtherSuppliersItemHistory
  }
}
