import { serverNow, serverToday } from './serverTime'
import { ref, toRaw } from 'vue'
import { frappeGet, frappePost } from '../api.js'
import { session } from '../session'
import { readItemSnapshot, writeItemSnapshot, applyPriceList, mergeItemDelta } from './itemCacheStore'

// Must match ITEM_SYNC_SCHEMA in ssplbilling/api/itemsearch_api.py.
const SYNC_SCHEMA = 1
const SYNC_METHOD = 'ssplbilling.api.itemsearch_api.get_items_sync'

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

// Every (company, search type, warehouse) combination loaded in this page session stays in memory
// and is kept current by socket events (useItemSync), so switching pages or scopes never refetches.
// Only a page reload (IndexedDB snapshot + small delta), a socket reconnect (delta) or a refresh
// button (delta) talks to the server again.
const MAX_DATASETS = 3
const datasets = new Map() // key -> { key, company, searchType, warehouse, priceList, list, syncTs, draftCodes }
let activeKey = null
let requestedKey = null

// In-flight syncs per dataset key, so a Dashboard preload and a page mount share one request.
const inflight = new Map()

// Keyed by exactly what the server receives: String(null) -> "null" is a different scope from ''.
function datasetKey(company, searchType, warehouse) {
  return [session.user.value || '', company, searchType, String(warehouse)].join('|')
}

function syncParams(ds) {
  // The previous GET transport stringified nulls to "null" (no warehouse filter match, base rate as
  // price); send them the same way so stock/price semantics stay unchanged under POST.
  return { search_type: ds.searchType, price_list: String(ds.priceList), warehouse: String(ds.warehouse), company: ds.company }
}

// The active dataset is mutated through the reactive `items` proxy; inactive ones directly.
function listFor(ds) {
  return ds.key === activeKey ? items.value : ds.list
}

function storeDataset(ds) {
  datasets.delete(ds.key)
  datasets.set(ds.key, ds)
  for (const key of datasets.keys()) {
    if (datasets.size <= MAX_DATASETS) break
    if (key !== activeKey && key !== ds.key) datasets.delete(key)
  }
  return ds
}

function activateDataset(ds, searchType, priceList, warehouse) {
  if (ds.priceList !== priceList) {
    console.log('[itemCache] switching price list in-memory to:', priceList)
    applyPriceList(ds.list, priceList)
    ds.priceList = priceList
    lastSync.value = serverNow().getTime()
  }
  if (activeKey !== ds.key || toRaw(items.value) !== ds.list) {
    activeKey = ds.key
    items.value = ds.list
  }
  lastParams.value = { searchType, priceList, warehouse }
  storeDataset(ds) // most recently used
}

/**
 * Make the item cache for (searchType, warehouse) active. A combination already loaded in this
 * page session is switched to in memory; otherwise it is loaded from the IndexedDB snapshot plus a
 * delta (a full download only when there is no snapshot). `force` (the refresh buttons) catches a
 * loaded combination up with a delta right away instead of waiting for socket events.
 */
export async function refreshItemCache(searchType = 'Sales', priceList = null, warehouse = null, force = false) {
  const company = localStorage.getItem('wb-company') || ''
  const key = datasetKey(company, searchType, warehouse)
  requestedKey = key

  let run = inflight.get(key)
  if (!run) {
    const loaded = datasets.get(key)
    if (loaded && !force) {
      activateDataset(loaded, searchType, priceList, warehouse)
      return items.value
    }
    run = loaded ? catchUpDataset(loaded) : loadDataset({ key, company, searchType, warehouse, priceList })
    inflight.set(key, run)
  }
  try {
    const ds = await run
    // Another scope may have been requested meanwhile; never let a late sync take over.
    if (requestedKey !== key) return ds.list
    activateDataset(ds, searchType, priceList, warehouse)
    return items.value
  } finally {
    if (inflight.get(key) === run) inflight.delete(key)
  }
}

async function catchUpDataset(ds) {
  syncLoading.value = true
  try {
    return await syncDelta(ds, { keepOnError: false })
  } finally {
    syncLoading.value = false
  }
}

async function loadDataset(spec) {
  syncLoading.value = true
  try {
    let snapshot = null
    let base = null
    try {
      snapshot = await readItemSnapshot(spec.key)
      if (snapshot?.schema === SYNC_SCHEMA && snapshot.syncTs) base = JSON.parse(snapshot.items)
    } catch (e) {
      console.warn('[itemCache] Snapshot unavailable:', e)
    }

    if (base) {
      // Serve the persisted cache right away; the delta below refreshes it.
      const ds = storeDataset({
        ...spec, list: applyPriceList(base, spec.priceList),
        syncTs: snapshot.syncTs, draftCodes: snapshot.draftCodes || [],
      })
      if (requestedKey === spec.key) {
        activateDataset(ds, spec.searchType, spec.priceList, spec.warehouse)
        lastSync.value = snapshot.savedAt
      }
      return await syncDelta(ds, { keepOnError: true })
    }
    // Not stored until the download lands, so concurrent callers wait on `inflight` instead of
    // switching to an empty list.
    return await syncDelta({ ...spec, list: [], syncTs: null, draftCodes: [] }, { keepOnError: false })
  } catch (e) {
    console.error('[itemCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

/**
 * Bring a dataset up to date with one get_items_sync call: a delta when it has a sync point,
 * otherwise a full download. The merged list replaces the dataset's list (and `items` if active).
 */
async function syncDelta(ds, { keepOnError }) {
  const params = syncParams(ds)
  let data
  try {
    data = await frappePost(SYNC_METHOD, {
      ...params,
      since: ds.syncTs || null,
      draft_codes: ds.syncTs ? ds.draftCodes || [] : [],
    }, { silent: true })
  } catch (e) {
    if (!keepOnError) throw e
    console.warn('[itemCache] Delta sync failed, keeping cached items:', e)
    return ds
  }

  const base = toRaw(listFor(ds))
  let list = data.full || !ds.syncTs ? data.items || [] : mergeItemDelta(base, data.items || [], data.removed || [])
  if (!data.full && list.length !== data.total) {
    // Delta drifted from the server (e.g. a renamed item) — fall back to a full download.
    console.warn('[itemCache] Cache count mismatch, resyncing all items:', list.length, data.total)
    data = await frappePost(SYNC_METHOD, { ...params, since: null, draft_codes: [] }, { silent: true })
    list = data.items || []
  }

  applyPriceList(list, ds.priceList)
  ds.list = list
  ds.syncTs = data.sync_ts
  ds.draftCodes = data.draft_codes || []
  storeDataset(ds)
  if (ds.key === activeKey) items.value = list
  saveUomsToStorage(list)
  savePercentagesToStorage(list)
  lastSync.value = serverNow().getTime()
  persistSnapshot(ds)
  return ds
}

/**
 * Catch up every loaded dataset after a socket reconnect (events sent while disconnected were
 * missed). Datasets last synced on an earlier day are left for the next page reload: the server
 * answers those with a full download, which every counter would otherwise fetch at once.
 */
export async function reconcileItemDatasets() {
  const today = serverToday()
  for (const ds of [...datasets.values()]) {
    if (!ds.syncTs || String(ds.syncTs).slice(0, 10) !== today) continue
    try {
      await syncDelta(ds, { keepOnError: true })
    } catch (e) {
      console.warn('[itemCache] Reconnect delta failed:', e)
    }
  }
  window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
}

/** Scopes of the loaded datasets, for fetching per-scope realtime item patches. */
export function getLoadedItemScopes() {
  return [...datasets.values()].map(({ key, company, searchType, priceList, warehouse }) => ({
    key, company, searchType, priceList, warehouse,
  }))
}

// Serialising ~10 MB blocks the main thread, so defer it until the browser is idle.
function persistSnapshot(ds) {
  const { key, list, syncTs, draftCodes, priceList } = ds
  const write = () => {
    let json
    try {
      // Live socket patches since the sync land in `list` too; the next delta refetches them anyway.
      json = JSON.stringify(toRaw(list))
    } catch (e) {
      console.warn('[itemCache] Snapshot serialisation failed:', e)
      return
    }
    writeItemSnapshot({
      key,
      schema: SYNC_SCHEMA,
      syncTs,
      draftCodes,
      priceList,
      savedAt: serverNow().getTime(),
      items: json,
    }).catch(e => console.warn('[itemCache] Snapshot write failed:', e))
  }
  if (typeof requestIdleCallback === 'function') requestIdleCallback(write, { timeout: 5000 })
  else setTimeout(write, 1000)
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
 * Patch a single item in one loaded dataset (the active one by default) without a refresh.
 * Pass null as newData to remove the item (deleted / disabled / filtered out).
 */
export function patchItemInCache(itemCode, newData, key = activeKey) {
  const ds = datasets.get(key)
  const list = ds ? listFor(ds) : items.value
  const idx = list.findIndex(i => i.item_code === itemCode)
  if (newData === null) {
    if (idx !== -1) list.splice(idx, 1)
  } else if (idx !== -1) {
    list.splice(idx, 1, newData)
  } else {
    // New item — insert maintaining item_name alphabetical order
    const insertAt = list.findIndex(i => (i.item_name || '') > (newData.item_name || ''))
    if (insertAt === -1) list.push(newData)
    else list.splice(insertAt, 0, newData)
  }
  lastSync.value = serverNow().getTime()
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

/** Apply an Item Price change to every loaded dataset. */
export function updateItemPriceInCache(itemCode, priceList, rate, uom) {
  const targets = datasets.size ? [...datasets.values()] : [null]
  for (const ds of targets) {
    const list = ds ? listFor(ds) : items.value
    const idx = list.findIndex(i => i.item_code === itemCode)
    if (idx === -1) continue

    const item = { ...list[idx] }
    item.price_lists = [...(item.price_lists || [])]
    item.uom_price_lists = { ...(item.uom_price_lists || {}) }

    if (uom) {
      item.uom_price_lists[priceList] = { ...(item.uom_price_lists[priceList] || {}), [uom]: rate }
    } else {
      const plIdx = item.price_lists.findIndex(pl => pl.name === priceList)
      if (plIdx !== -1) {
        item.price_lists[plIdx] = { ...item.price_lists[plIdx], rate }
      } else {
        item.price_lists.push({ name: priceList, rate })
      }

      const mainPriceList = (ds ? ds.priceList : lastParams.value.priceList) || 'Standard Selling'
      if (priceList === mainPriceList) {
        item.price = rate
        item.rate = rate
      }
    }

    list.splice(idx, 1, item)
  }
  lastSync.value = serverNow().getTime()
}

function sumCompanyDrafts(byWarehouse, fallbackTotal) {
  if (!byWarehouse) return fallbackTotal
  let allowed = []
  try { allowed = JSON.parse(localStorage.getItem('wb-warehouses') || '[]') } catch {}
  return Object.entries(byWarehouse)
    .filter(([warehouse]) => !allowed.length || allowed.includes(warehouse))
    .reduce((sum, [, qty]) => sum + (Number(qty) || 0), 0)
}

/**
 * Apply a realtime stock_update event ({ item_code, warehouse, qty, redis_stock,
 * redis_purchase_stock, draft_qty?, draft_purchase_qty?, valuation_rate? }) to every loaded dataset,
 * recomputing each one's warehouse-scoped figures the way get_all_items_detailed does.
 */
export function updateItemStockInCache(event) {
  const { item_code: itemCode, warehouse, qty } = event
  for (const ds of datasets.values()) {
    const list = listFor(ds)
    const idx = list.findIndex(i => i.item_code === itemCode)
    if (idx === -1) continue

    const item = { ...list[idx] }
    const warehouseStock = [...(item.warehouse_stock || [])]
    const whIdx = warehouseStock.findIndex(w => w.warehouse === warehouse)
    if (whIdx !== -1) {
      warehouseStock[whIdx] = { ...warehouseStock[whIdx], qty }
    } else {
      warehouseStock.push({ warehouse, qty })
    }
    item.warehouse_stock = warehouseStock

    // The server sums every warehouse only when no warehouse is sent ('' is falsy there);
    // any other value — including "null" — counts that one warehouse.
    const scope = String(ds.warehouse)
    if (scope === '') {
      item.stock = warehouseStock.reduce((sum, w) => sum + (w.qty || 0), 0)
      // The server counts drafts in the company's warehouses only; the event totals cover all.
      item.redis_stock = sumCompanyDrafts(event.draft_by_warehouse, event.redis_stock)
      item.redis_purchase_stock = sumCompanyDrafts(event.draft_purchase_by_warehouse, event.redis_purchase_stock)
      // valuation_rate is left as synced: the server takes whichever Bin it happens to read last.
    } else {
      item.stock = warehouseStock.reduce((sum, w) => sum + (w.warehouse === scope ? w.qty || 0 : 0), 0)
      if (warehouse === scope) {
        if (event.draft_qty !== undefined) item.redis_stock = event.draft_qty
        if (event.draft_purchase_qty !== undefined) item.redis_purchase_stock = event.draft_purchase_qty
        if (event.valuation_rate > 0) item.valuation_rate = event.valuation_rate
      }
    }

    list.splice(idx, 1, item)
  }
  lastSync.value = serverNow().getTime()
}

/**
 * Rebuild every loaded dataset with `change(item)` (returns a replacement item, or nothing to keep
 * it), swapping each list in one assignment so a 12k-item update is a single reactive change.
 */
function rewriteAllDatasets(change) {
  for (const ds of datasets.values()) {
    let changed = false
    const next = toRaw(listFor(ds)).map(item => {
      const updated = change(item)
      if (!updated) return item
      changed = true
      return updated
    })
    if (!changed) continue
    applyPriceList(next, ds.priceList)
    ds.list = next
    if (ds.key === activeKey) items.value = next
  }
  lastSync.value = serverNow().getTime()
}

function withoutPriceList(item, name) {
  const inBase = (item.price_lists || []).some(p => p.name === name)
  const inUom = item.uom_price_lists && name in item.uom_price_lists
  if (!inBase && !inUom) return null
  const uomPriceLists = { ...(item.uom_price_lists || {}) }
  delete uomPriceLists[name]
  return { ...item, price_lists: (item.price_lists || []).filter(p => p.name !== name), uom_price_lists: uomPriceLists }
}

/** Drop a disabled / deleted price list from every cached item. */
export function removePriceListFromCache(name) {
  rewriteAllDatasets(item => withoutPriceList(item, name))
}

/** Update the buying / selling flags carried on an enabled list's base-rate entries. */
export function updatePriceListFlagsInCache(name, buying, selling) {
  const flags = { buying: Boolean(buying), selling: Boolean(selling) }
  rewriteAllDatasets(item => {
    if (!(item.price_lists || []).some(p => p.name === name && (p.buying !== flags.buying || p.selling !== flags.selling))) return null
    return { ...item, price_lists: item.price_lists.map(p => (p.name === name ? { ...p, ...flags } : p)) }
  })
}

/** Rename a price list in place across every cached item. */
export function renamePriceListInCache(oldName, newName) {
  // Point selections at the new name first: the rewrite recomputes `price` from ds.priceList.
  for (const ds of datasets.values()) {
    if (ds.priceList === oldName) ds.priceList = newName
  }
  rewriteAllDatasets(item => {
    const inBase = (item.price_lists || []).some(p => p.name === oldName)
    const inUom = item.uom_price_lists && oldName in item.uom_price_lists
    if (!inBase && !inUom) return null
    const uomPriceLists = { ...(item.uom_price_lists || {}) }
    if (inUom) {
      uomPriceLists[newName] = uomPriceLists[oldName]
      delete uomPriceLists[oldName]
    }
    return {
      ...item,
      price_lists: (item.price_lists || []).map(p => (p.name === oldName ? { ...p, name: newName } : p)),
      uom_price_lists: uomPriceLists,
    }
  })
}

/**
 * Replace one price list's rates on every cached item with `rates` ([item_code, uom, rate] rows from
 * get_price_list_rates), the way get_all_items_detailed builds them: per-UOM rows go to
 * uom_price_lists, UOM-less rows to price_lists with the list's buying / selling flags.
 */
export function setPriceListRatesInCache({ name, buying, selling, rates }) {
  const byCode = new Map()
  for (const [code, uom, rate] of rates || []) {
    if (!byCode.has(code)) byCode.set(code, [])
    byCode.get(code).push([uom, rate])
  }
  rewriteAllDatasets(item => {
    const own = byCode.get(item.item_code)
    const stripped = withoutPriceList(item, name)
    if (!own) return stripped
    const next = stripped || { ...item, price_lists: [...(item.price_lists || [])], uom_price_lists: { ...(item.uom_price_lists || {}) } }
    for (const [uom, rate] of own) {
      if (uom) {
        next.uom_price_lists[name] = { ...(next.uom_price_lists[name] || {}), [uom]: rate }
      } else {
        next.price_lists.push({ name, rate, buying: Boolean(buying), selling: Boolean(selling) })
      }
    }
    return next
  })
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

