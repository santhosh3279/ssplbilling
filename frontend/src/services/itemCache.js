import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for items
const items = ref([])
const lastSync = ref(0)
const syncLoading = ref(false)

/**
 * Fetch all items with details from the backend and update the global cache.
 */
export async function refreshItemCache(searchType = 'Sales', priceList = null, warehouse = null) {
  syncLoading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.itemsearch_api.get_all_items_detailed', {
      search_type: searchType,
      price_list: priceList,
      warehouse: warehouse
    })
    items.value = data || []
    lastSync.value = Date.now()
    return items.value
  } catch (e) {
    console.error('[itemCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

/**
 * Look up an item by code or barcode in the local cache.
 */
export function lookupItemInCache(code) {
  if (!code) return null
  const cleanCode = code.trim().toLowerCase()
  
  // Try direct match or barcode match (if barcode field was included, 
  // but currently we mostly match by item_code)
  return items.value.find(i => 
    (i.item_code || '').toLowerCase() === cleanCode
  ) || null
}

export function useItemCache() {
  return {
    items,
    lastSync,
    syncLoading,
    refreshItemCache,
    lookupItemInCache
  }
}
