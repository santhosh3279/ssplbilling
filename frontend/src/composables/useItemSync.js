import { getFrappeSocket } from '../services/frappeSocket.js'
import { frappeGet } from '../api.js'
import { patchItemInCache, updateItemPriceInCache, updateItemStockInCache, useItemCache, refreshDiscountRuleCache } from '../services/itemCache.js'

const { lastParams } = useItemCache()

let _handler = null
let _priceHandler = null
let _stockHandler = null
let _discountRuleHandler = null
let _debounceTimer = null
const pendingPatches = new Set()

async function _patchItem(itemCode) {
  const { searchType, priceList, warehouse } = lastParams.value
  const params = { item_code: itemCode, search_type: searchType || 'Sales' }
  if (priceList) params.price_list = priceList
  if (warehouse) params.warehouse = warehouse

  console.log('[useItemSync] patching cache for item:', itemCode)
  try {
    const result = await frappeGet('ssplbilling.api.itemsearch_api.get_single_item_detailed', params)
    // frappeGet returns json.message ?? json. When Python returns None, result = {message:null}
    // so check for item_code presence to detect "deleted / filtered out"
    patchItemInCache(itemCode, result?.item_code ? result : null)
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  } catch (e) {
    console.warn('[useItemSync] patch failed:', e)
  }
}

function _handleVisibilityChange() {
  if (!document.hidden && pendingPatches.size > 0) {
    console.log('[useItemSync] Tab became visible. Processing deferred patches:', [...pendingPatches])
    for (const itemCode of pendingPatches) {
      _patchItem(itemCode)
    }
    pendingPatches.clear()
  }
}

export function initItemSync() {
  const socket = getFrappeSocket()
  socket.emit('doctype_subscribe', 'Item')

  _handler = (data) => {
    if (data?.doctype !== 'Item' || !data.name) return
    
    if (document.hidden) {
      pendingPatches.add(data.name)
      console.log('[useItemSync] Tab is hidden. Queueing patch for:', data.name)
      return
    }

    clearTimeout(_debounceTimer)
    _debounceTimer = setTimeout(() => _patchItem(data.name), 500)
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
    console.log('[useItemSync] received stock_update:', data)
    updateItemStockInCache(data.item_code, data.warehouse, data.qty, data.redis_stock, data.redis_purchase_stock)
    window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
  }
  socket.on('stock_update', _stockHandler)

  _discountRuleHandler = (data) => {
    console.log('[useItemSync] received discount_rule_update:', data)
    refreshDiscountRuleCache()
  }
  socket.on('discount_rule_update', _discountRuleHandler)

  document.addEventListener('visibilitychange', _handleVisibilityChange)
  console.log('[useItemSync] subscribed to doctype:Item, listening for list_update, item_price_update, stock_update and discount_rule_update')
}

export function destroyItemSync() {
  clearTimeout(_debounceTimer)
  pendingPatches.clear()
  const socket = getFrappeSocket()
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
  document.removeEventListener('visibilitychange', _handleVisibilityChange)
}


