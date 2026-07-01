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

// Pricelist Percentages cache — persisted to localStorage: { item_code: [{pricelist, percentage}] }
const ITEM_PERCENTAGES_KEY = 'sspl-item-pricelist-percentages'
function loadPercentagesFromStorage() {
  try { return JSON.parse(localStorage.getItem(ITEM_PERCENTAGES_KEY) || '{}') } catch { return {} }
}
function savePercentagesToStorage(itemList) {
  try {
    const map = {}
    for (const i of itemList) {
      if (i.pricelist_percentages?.length) map[i.item_code] = i.pricelist_percentages
    }
    localStorage.setItem(ITEM_PERCENTAGES_KEY, JSON.stringify(map))
  } catch {}
}
const storedPercentages = loadPercentagesFromStorage()


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
    savePercentagesToStorage(items.value)
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
 * Patch a single item in the cache without a full refresh.
 * Pass null as newData to remove the item (deleted / disabled / filtered out).
 */
export function patchItemInCache(itemCode, newData) {
  const idx = items.value.findIndex(i => i.item_code === itemCode)
  if (newData === null) {
    if (idx !== -1) items.value.splice(idx, 1)
  } else if (idx !== -1) {
    items.value.splice(idx, 1, newData)
  } else {
    // New item — insert maintaining item_name alphabetical order
    const insertAt = items.value.findIndex(i => (i.item_name || '') > (newData.item_name || ''))
    if (insertAt === -1) items.value.push(newData)
    else items.value.splice(insertAt, 0, newData)
  }
  lastSync.value = Date.now()
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
    if (!item.pricelist_percentages?.length && storedPercentages[item.item_code]?.length) {
      item.pricelist_percentages = storedPercentages[item.item_code]
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
      item._from_barcode = true
    }
    if (!item.uoms?.length && storedUoms[item.item_code]?.length) {
      item.uoms = storedUoms[item.item_code]
    }
    if (!item.pricelist_percentages?.length && storedPercentages[item.item_code]?.length) {
      item.pricelist_percentages = storedPercentages[item.item_code]
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

export function updateItemPriceInCache(itemCode, priceList, rate, uom) {
  const idx = items.value.findIndex(i => i.item_code === itemCode)
  if (idx === -1) return

  const item = { ...items.value[idx] }
  
  if (!item.price_lists) item.price_lists = []
  if (!item.uom_price_lists) item.uom_price_lists = {}

  if (uom) {
    if (!item.uom_price_lists[priceList]) item.uom_price_lists[priceList] = {}
    item.uom_price_lists[priceList][uom] = rate
  } else {
    const plIdx = item.price_lists.findIndex(pl => pl.name === priceList)
    if (plIdx !== -1) {
      item.price_lists[plIdx] = { ...item.price_lists[plIdx], rate }
    } else {
      item.price_lists.push({ name: priceList, rate })
    }
    
    const { priceList: activePriceList } = lastParams.value
    const mainPriceList = activePriceList || 'Standard Selling'
    if (priceList === mainPriceList) {
      item.price = rate
      item.rate = rate
    }
  }

  items.value.splice(idx, 1, item)
  lastSync.value = Date.now()
}

/**
 * Apply a realtime stock_update event to the cache: patches the affected warehouse's
 * qty, recomputes the item's total stock, and updates its redis (draft) stock figure.
 * Ignored if the cache is currently scoped to a different single warehouse.
 */
export function updateItemStockInCache(itemCode, warehouse, qty, redisStock) {
  const { warehouse: activeWarehouse } = lastParams.value
  if (activeWarehouse && activeWarehouse !== warehouse) return

  const idx = items.value.findIndex(i => i.item_code === itemCode)
  if (idx === -1) return

  const item = { ...items.value[idx] }
  const warehouseStock = [...(item.warehouse_stock || [])]
  const whIdx = warehouseStock.findIndex(w => w.warehouse === warehouse)
  if (whIdx !== -1) {
    warehouseStock[whIdx] = { ...warehouseStock[whIdx], qty }
  } else {
    warehouseStock.push({ warehouse, qty })
  }

  item.warehouse_stock = warehouseStock
  item.stock = warehouseStock.reduce((sum, w) => sum + (w.qty || 0), 0)
  item.redis_stock = redisStock

  items.value.splice(idx, 1, item)
  lastSync.value = Date.now()
}

export function useItemCache() {
  return {
    items,
    lastSync,
    syncLoading,
    lastParams,
    refreshItemCache,
    patchItemInCache,
    lookupItemInCache,
    searchItemsInCache,
    updateItemPriceInCache,
    updateItemStockInCache,
    // Discount Rules (custom doctype)
    discountRules,
    refreshDiscountRuleCache,
    saveDiscountRulesToStorage
  }
}

