import { ref } from 'vue'
import { frappeGet } from '../api.js'

/**
 * Composable to manage customer sales history for a specific window/session.
 * Unlike itemCache, this does not use a global singleton so it can be cleared independently.
 */
export function useCustomerHistory() {
  const customerSalesHistory = ref([])
  const currentCustomerForHistory = ref(null)
  const historyLoading = ref(false)
  
  const itemStock = ref([])
  const stockLoading = ref(false)

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

  /**
   * Fetch warehouse-wise stock levels for a specific item.
   */
  async function fetchItemStock(itemCode) {
    if (!itemCode) {
      itemStock.value = []
      return
    }
    stockLoading.value = true
    try {
      const data = await frappeGet('ssplbilling.api.stock_api.get_warehouse_stock', {
        item_code: itemCode
      })
      itemStock.value = data || []
    } catch (e) {
      console.warn('[customerHistory] Stock fetch failed:', e.message)
      itemStock.value = []
    } finally {
      stockLoading.value = false
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

  /**
   * Clear all history details.
   */
  function clearHistory() {
    customerSalesHistory.value = []
    currentCustomerForHistory.value = null
    historyLoading.value = false
    itemStock.value = []
    stockLoading.value = false
  }

  return {
    customerSalesHistory,
    currentCustomerForHistory,
    historyLoading,
    fetchCustomerSalesHistory,
    hasHistory,
    getItemHistoryFromCache,
    clearHistory,
    // Stock levels
    itemStock,
    stockLoading,
    fetchItemStock
  }
}
