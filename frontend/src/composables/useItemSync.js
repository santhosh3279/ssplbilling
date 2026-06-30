import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshItemCache, useItemCache } from '../services/itemCache.js'

const { lastParams, lastSync } = useItemCache()

let _handler = null
let _debounceTimer = null

function _scheduleRefresh() {
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(async () => {
    const { searchType, priceList, warehouse } = lastParams.value
    console.log('[useItemSync] item_cache_invalidated — refreshing item cache')
    try {
      await refreshItemCache(searchType || 'Sales', priceList, warehouse)
      window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
    } catch (e) {
      console.warn('[useItemSync] cache refresh failed:', e)
    }
  }, 1000)
}

export function initItemSync() {
  const socket = getFrappeSocket()
  _handler = () => _scheduleRefresh()
  socket.on('item_cache_invalidated', _handler)
  console.log('[useItemSync] listening for item_cache_invalidated')
}

export function destroyItemSync() {
  clearTimeout(_debounceTimer)
  if (_handler) {
    getFrappeSocket().off('item_cache_invalidated', _handler)
    _handler = null
  }
}
