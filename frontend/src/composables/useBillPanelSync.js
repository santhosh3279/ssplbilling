import { getFrappeSocket } from '../services/frappeSocket.js'
import { applyEventToCache } from '../services/billPanelCache.js'

// Global bridge: subscribes once to the `bill_panel_update` websocket event and
// re-emits it as a `wb-bill-panel-update` window event. Each bill page (Sales
// Invoice, Purchase Invoice, Sales Order, Purchase Order, Quotation) listens on
// the window and refreshes its modify-bill panel only when the event's doctype
// and naming_series match what that page is currently showing.

let _handler = null

export function initBillPanelSync() {
  const socket = getFrappeSocket()
  if (!socket || _handler) return

  _handler = (data) => {
    if (!data?.doctype) return
    console.log('[useBillPanelSync] received bill_panel_update:', data)
    // Keep the localStorage panel cache current even when no bill page is
    // open, so the next page open paints from cache without a server call.
    applyEventToCache(data)
    window.dispatchEvent(new CustomEvent('wb-bill-panel-update', { detail: data }))
  }
  socket.on('bill_panel_update', _handler)

  console.log('[useBillPanelSync] listening for bill_panel_update')
}

export function destroyBillPanelSync() {
  const socket = getFrappeSocket()
  if (_handler && socket) {
    socket.off('bill_panel_update', _handler)
  }
  _handler = null
}

/**
 * Register a bill page's modify-panel to auto-refresh over websocket.
 *
 * @param {string}   doctype      Frappe doctype this page shows (e.g. 'Sales Invoice').
 * @param {Ref<string[]>} seriesRef Reactive list of naming_series the panel currently shows.
 * @param {Function} refetch      Called (debounced) when a matching bill changes elsewhere.
 * @param {Function} [onRow]      Optional: called with the event payload when it carries the
 *                                changed row; when it returns true the refetch is skipped so
 *                                the page can patch its list in place instead.
 * @returns {Function} cleanup    Call in onUnmounted to remove the listener.
 *
 * The series check reads seriesRef.value live inside the handler, so it always
 * reflects the panel's current series selection. A save in an allowed-but-not-shown
 * series is skipped — it wouldn't change the visible list anyway.
 */
export function onBillPanelUpdate(doctype, seriesRef, refetch, onRow = null) {
  let debounceTimer = null

  const listener = (e) => {
    const data = e?.detail
    if (!data || data.doctype !== doctype) return
    const series = seriesRef?.value || []
    // If the client hasn't picked a series, its panel shows all allowed series,
    // so refresh on any change to this doctype; otherwise gate on the shown series.
    if (series.length && !series.includes(data.naming_series)) return

    // Payloads carrying the row can be applied in place — no server round trip.
    if (onRow && data.row && onRow(data)) return

    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      debounceTimer = null
      refetch()
    }, 300)
  }

  window.addEventListener('wb-bill-panel-update', listener)

  return () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    window.removeEventListener('wb-bill-panel-update', listener)
  }
}
