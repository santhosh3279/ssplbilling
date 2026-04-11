import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for items
const items = ref([])
const lastSync = ref(0)
const syncLoading = ref(false)
const lastParams = ref({ searchType: null, priceList: null, warehouse: null })

// UOM map cache — persisted to localStorage: { item_code: [{uom, conversion_factor}] }
const ITEM_UOMS_KEY = 'sspl-item-uoms'
function loadUomsFromStorage() {
  try { return JSON.parse(localStorage.getItem(ITEM_UOMS_KEY) || '{}') } catch { return {} }
}
function saveUomsToStorage(itemList) {
  try {
    const map = {}
    for (const i of itemList) {
      if (i.uoms?.length) map[i.item_code] = i.uoms
    }
    localStorage.setItem(ITEM_UOMS_KEY, JSON.stringify(map))
  } catch {}
}
const storedUoms = loadUomsFromStorage()

// Discount Rules cache (custom Discount Rule doctype) — persisted to localStorage
const DISCOUNT_RULES_KEY = 'sspl-discount-rules'
function loadDiscountRulesFromStorage() {
  try { return JSON.parse(localStorage.getItem(DISCOUNT_RULES_KEY) || '[]') } catch { return [] }
}
export function saveDiscountRulesToStorage(rules) {
  try { localStorage.setItem(DISCOUNT_RULES_KEY, JSON.stringify(rules)) } catch {}
}
const discountRules = ref(loadDiscountRulesFromStorage())

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
      frappeGet('ssplbilling.api.SaleEntry_api.get_discount_rules').catch(() => [])
    ])
    items.value = data || []
    discountRules.value = discRules || []
    saveDiscountRulesToStorage(discountRules.value)
    saveUomsToStorage(items.value)
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
    const data = await frappeGet('ssplbilling.api.SaleEntry_api.get_discount_rules')
    discountRules.value = data || []
    saveDiscountRulesToStorage(discountRules.value)
    return discountRules.value
  } catch (e) {
    console.warn('[itemCache] Discount rule refresh failed:', e)
    return discountRules.value
  }
}

/**
 * Look up an item by code or barcode in the local cache.
 * If found via barcode, returns the item with the barcode's specific UOM.
 */
export function lookupItemInCache(code) {
  if (!code) return null
  const cleanCode = code.trim().toLowerCase()
  
  // 1. Check direct item_code match
  let found = items.value.find(i => (i.item_code || '').toLowerCase() === cleanCode)
  if (found) {
    const item = { ...found }
    if (!item.uoms?.length && storedUoms[item.item_code]?.length) {
      item.uoms = storedUoms[item.item_code]
    }
    return item
  }

  // 2. Check barcode match
  found = items.value.find(i => {
    const detailed = i.barcodes_detailed || []
    return detailed.some(b => (b.barcode || '').toLowerCase() === cleanCode)
  })

  if (found) {
    const item = { ...found }
    const match = item.barcodes_detailed.find(b => (b.barcode || '').toLowerCase() === cleanCode)
    if (match && match.uom) {
      item.uom = match.uom // Use the UOM linked to this specific barcode
    }
    if (!item.uoms?.length && storedUoms[item.item_code]?.length) {
      item.uoms = storedUoms[item.item_code]
    }
    return item
  }

  return null
}

/**
 * Search for items in the local cache by code or name.
 * Supports multi-term search (all terms must match partially).
 */
export function searchItemsInCache(query, maxResults = 50) {
  if (!query || query.length < 2) return []
  const cleanQuery = query.trim().toLowerCase()
  const terms = cleanQuery.split(/\s+/).filter(Boolean)
  if (terms.length === 0) return []
  
  const filtered = items.value.filter(i => {
    const code = (i.item_code || '').toLowerCase()
    const name = (i.item_name || '').toLowerCase()
    const barcodes = (i.barcodes || '').toLowerCase().split(',')
    
    // Check if all terms match either the code, name, or any barcode
    return terms.every(term => 
      code.includes(term) || 
      name.includes(term) || 
      barcodes.some(b => b.includes(term))
    )
  })

  // Sort: prioritize exact match on item_code or ANY barcode
  filtered.sort((a, b) => {
    const codeA = (a.item_code || '').toLowerCase()
    const codeB = (b.item_code || '').toLowerCase()
    const barcodesA = (a.barcodes || '').toLowerCase().split(',')
    const barcodesB = (b.barcodes || '').toLowerCase().split(',')
    
    const isExactA = codeA === cleanQuery || barcodesA.includes(cleanQuery)
    const isExactB = codeB === cleanQuery || barcodesB.includes(cleanQuery)
    
    if (isExactA && !isExactB) return -1
    if (!isExactA && isExactB) return 1
    return 0
  })

  return filtered.slice(0, maxResults)
}

export function useItemCache() {
  return {
    items,
    lastSync,
    syncLoading,
    lastParams,
    refreshItemCache,
    lookupItemInCache,
    searchItemsInCache,
    // Discount Rules (custom doctype)
    discountRules,
    refreshDiscountRuleCache,
    saveDiscountRulesToStorage
  }
}
