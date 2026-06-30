import { getFrappeSocket } from '../services/frappeSocket.js'
import { frappeGet } from '../api.js'
import { patchItemInCache, useItemCache } from '../services/itemCache.js'

const { lastParams } = useItemCache()

let _handler = null
let _debounceTimer = null

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

export function initItemSync() {
  const socket = getFrappeSocket()
  socket.emit('doctype_subscribe', 'Item')

  _handler = (data) => {
    if (data?.doctype !== 'Item' || !data.name) return
    clearTimeout(_debounceTimer)
    _debounceTimer = setTimeout(() => _patchItem(data.name), 500)
  }
  socket.on('list_update', _handler)
  console.log('[useItemSync] subscribed to doctype:Item, listening for list_update')
}

export function destroyItemSync() {
  clearTimeout(_debounceTimer)
  if (_handler) {
    getFrappeSocket().off('list_update', _handler)
    _handler = null
  }
}
