import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshItemCache, useItemCache } from '../services/itemCache.js'

const { lastParams } = useItemCache()

let _handler = null
let _debounceTimer = null

function _scheduleRefresh() {
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(async () => {
    const { searchType, priceList, warehouse } = lastParams.value
    console.log('[useItemSync] Item list_update — refreshing item cache')
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

  // Join the doctype:Item room so Frappe's built-in list_update events reach us.
  socket.emit('doctype_subscribe', 'Item')

  // list_update is sent automatically by Frappe on every Item save/delete.
  // No custom Python hook needed — this is already confirmed to arrive.
  _handler = (data) => {
    if (data?.doctype === 'Item') _scheduleRefresh()
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
