import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshItemCache, useItemCache } from '../services/itemCache.js'

const { lastParams, lastSync } = useItemCache()

let _handler = null
let _debounceTimer = null

function _scheduleRefresh() {
  // Don't refresh if the cache was never populated (e.g. browser just opened)
  if (lastSync.value === 0) return
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(async () => {
    const { searchType, priceList, warehouse } = lastParams.value
    console.log('[useItemSync] item_cache_invalidated — refreshing item cache')
    try {
      await refreshItemCache(searchType, priceList, warehouse)
      // Let any interested component react without coupling to a specific toast library
      window.dispatchEvent(new CustomEvent('wb-item-cache-updated'))
    } catch (e) {
      console.warn('[useItemSync] cache refresh failed:', e)
    }
  }, 1000)
}

export function initItemSync() {
  const socket = getFrappeSocket()
  _handler = (data) => {
    if (data?.event === 'item_cache_invalidated') {
      _scheduleRefresh()
    }
  }
  socket.on('events', _handler)
  console.log('[useItemSync] listening for item_cache_invalidated')
}

export function destroyItemSync() {
  clearTimeout(_debounceTimer)
  if (_handler) {
    getFrappeSocket().off('events', _handler)
    _handler = null
  }
}
