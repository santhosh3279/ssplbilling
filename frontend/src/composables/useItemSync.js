import { getFrappeSocket } from '../services/frappeSocket.js'
import { frappeGet } from '../api.js'
import {
  patchItemInCache, updateItemPriceInCache, updateItemStockInCache, refreshDiscountRuleCache,
  getLoadedItemScopes, reconcileItemDatasets, removePriceListFromCache, updatePriceListFlagsInCache,
  renamePriceListInCache, setPriceListRatesInCache,
} from '../services/itemCache.js'

// A server restart reconnects every tab at once; spread their catch-up deltas.
const RECONNECT_SPREAD_MS = 30000
// A newly enabled price list makes every tab fetch its ~12k rates; spread those requests.
const PRICE_LIST_FETCH_SPREAD_MS = 5000

let _socket = null
let _handler = null
let _priceHandler = null
let _stockHandler = null
let _discountRuleHandler = null
let _connectHandler = null
let _priceListHandler = null
let _debounceTimer = null
let _reconcileTimer = null
let _reconcileOnVisible = false
const pendingPatches = new Set()

async function _patchItem(itemCode) {
  console.log('[useItemSync] patching cache for item:', itemCode)
  // Each loaded scope gets the row exactly as its own bulk sync would have built it.
  for (const scope of getLoadedItemScopes()) {
    try {
      const result = await frappeGet('ssplbilling.api.itemsearch_api.get_single_item_detailed', {
        item_code: itemCode,
        search_type: scope.searchType,
        price_list: scope.priceList,
        warehouse: scope.warehouse,
        company: scope.company,
      })
      // frappeGet returns json.message ?? json. When Python returns None, result = {message:null}
      // so check for item_code presence to detect "deleted / filtered out"
      patchItemInCache(itemCode, result?.item_code ? result : null, scope.key)
    } catch (e) {
      console.warn('[useItemSync] patch failed:', e)
    }
  }
  window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
}

async function _loadPriceListRates(name) {
  await new Promise(resolve => setTimeout(resolve, Math.random() * PRICE_LIST_FETCH_SPREAD_MS))
  try {
    const res = await frappeGet('ssplbilling.api.pricelist_api.get_price_list_rates', { price_list: name })
    if (res?.enabled) setPriceListRatesInCache(res)
    else removePriceListFromCache(name)
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  } catch (e) {
    console.warn('[useItemSync] price list rates fetch failed:', e)
  }
}

function _flushPendingPatches() {
  _debounceTimer = null
  const codes = [...pendingPatches]
  pendingPatches.clear()
  for (const itemCode of codes) _patchItem(itemCode)
}

function _scheduleReconcile(delay) {
  if (_reconcileTimer !== null) return
  _reconcileTimer = setTimeout(() => {
    _reconcileTimer = null
    reconcileItemDatasets()
  }, delay)
}

function _handleVisibilityChange() {
  if (document.hidden) return
  if (pendingPatches.size > 0) {
    console.log('[useItemSync] Tab became visible. Processing deferred patches:', [...pendingPatches])
    _flushPendingPatches()
  }
  if (_reconcileOnVisible) {
    _reconcileOnVisible = false
    _scheduleReconcile(Math.random() * 5000)
  }
}

export function initItemSync() {
  const socket = getFrappeSocket()
  _socket = socket
  socket.emit('doctype_subscribe', 'Item')

  _handler = (data) => {
    if (data?.doctype !== 'Item' || !data.name) return
    // Collect a burst of item saves and patch each once (hidden tabs wait until visible).
    pendingPatches.add(data.name)
    if (document.hidden) {
      console.log('[useItemSync] Tab is hidden. Queueing patch for:', data.name)
      return
    }
    clearTimeout(_debounceTimer)
    _debounceTimer = setTimeout(_flushPendingPatches, 500)
  }
  socket.on('list_update', _handler)

  _priceHandler = (data) => {
    if (!data?.item_code) return
    console.log('[useItemSync] received item_price_update:', data)
    updateItemPriceInCache(data.item_code, data.price_list, data.rate, data.uom)
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  }
  socket.on('item_price_update', _priceHandler)

  _stockHandler = (data) => {
    if (!data?.item_code || !data?.warehouse) return

    // Filter stock updates by company's warehouses
    let allowedWarehouses = []
    try {
      allowedWarehouses = JSON.parse(localStorage.getItem('wb-warehouses') || '[]')
    } catch {}
    if (allowedWarehouses.length && !allowedWarehouses.includes(data.warehouse)) {
      console.log('[useItemSync] ignoring stock_update for warehouse not in current company:', data.warehouse)
      return
    }

    console.log('[useItemSync] received stock_update:', data)
    updateItemStockInCache(data)
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  }
  socket.on('stock_update', _stockHandler)

  // Price List enabled / disabled / re-flagged / renamed / deleted: patch cached items in place.
  _priceListHandler = (data) => {
    if (!data?.name) return
    console.log('[useItemSync] received price_list_update:', data)
    if (data.old_name) {
      if (data.merge) {
        removePriceListFromCache(data.old_name)
        _loadPriceListRates(data.name)
      } else {
        renamePriceListInCache(data.old_name, data.name)
      }
    } else if (!data.enabled) {
      removePriceListFromCache(data.name)
    } else if (!data.was_enabled) {
      _loadPriceListRates(data.name) // newly created or re-enabled: rates were never cached
      return
    } else {
      updatePriceListFlagsInCache(data.name, data.buying, data.selling)
    }
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  }
  socket.on('price_list_update', _priceListHandler)

  _discountRuleHandler = (data) => {
    console.log('[useItemSync] received discount_rule_update:', data)
    refreshDiscountRuleCache()
  }
  socket.on('discount_rule_update', _discountRuleHandler)

  // Events sent while disconnected are lost: catch up with a delta per loaded scope. The first
  // connect is the initial one (the page load already synced); hidden tabs wait until visible.
  let initialConnectPending = !socket.connected
  _connectHandler = () => {
    socket.emit('doctype_subscribe', 'Item')
    if (initialConnectPending) {
      initialConnectPending = false
      return
    }
    if (document.hidden) _reconcileOnVisible = true
    else _scheduleReconcile(Math.random() * RECONNECT_SPREAD_MS)
  }
  socket.on('connect', _connectHandler)

  document.addEventListener('visibilitychange', _handleVisibilityChange)
  console.log('[useItemSync] subscribed to doctype:Item, listening for list_update, item_price_update, stock_update and discount_rule_update')
}

export function destroyItemSync() {
  clearTimeout(_debounceTimer)
  clearTimeout(_reconcileTimer)
  _debounceTimer = null
  _reconcileTimer = null
  _reconcileOnVisible = false
  pendingPatches.clear()
  const socket = _socket || getFrappeSocket()
  if (_handler) {
    socket.off('list_update', _handler)
    _handler = null
  }
  if (_priceHandler) {
    socket.off('item_price_update', _priceHandler)
    _priceHandler = null
  }
  if (_stockHandler) {
    socket.off('stock_update', _stockHandler)
    _stockHandler = null
  }
  if (_discountRuleHandler) {
    socket.off('discount_rule_update', _discountRuleHandler)
    _discountRuleHandler = null
  }
  if (_priceListHandler) {
    socket.off('price_list_update', _priceListHandler)
    _priceListHandler = null
  }
  if (_connectHandler) {
    socket.off('connect', _connectHandler)
    _connectHandler = null
  }
  document.removeEventListener('visibilitychange', _handleVisibilityChange)
  _socket = null
}
