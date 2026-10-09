import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshLedgerCache, applyLedgerBalancePush, patchLedgerInCache } from '../services/ledgerCache.js'
import { frappeGet } from '../api.js'

// A server restart reconnects every tab at once; spread their full refreshes (~5 s of server work each).
const RECONNECT_SPREAD_MS = 30000

let _socket = null
let _balanceHandler = null
let _customerHandler = null
let _connectHandler = null
let _visibilityHandler = null
let _refreshTimer = null
let _refreshRunning = false
let _refreshQueued = false
let _reconcileOnVisible = false

function scheduleLedgerRefresh(delay = 500) {
  if (!_socket) return
  _refreshQueued = true
  if (_refreshTimer !== null || _refreshRunning) return
  _refreshTimer = setTimeout(refreshLedgers, delay)
}

async function refreshLedgers() {
  _refreshTimer = null
  if (!_socket) return
  const socket = _socket
  _refreshQueued = false
  _refreshRunning = true
  try {
    await refreshLedgerCache(true)
    if (_socket === socket) {
      window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
    }
  } catch (e) {
    console.warn('[useLedgerSync] ledger refresh failed:', e)
  } finally {
    _refreshRunning = false
    if (_refreshQueued) scheduleLedgerRefresh()
  }
}

// Hidden tabs wait until they are looked at; visible ones start at a random point in the window.
function scheduleReconcile() {
  if (document.visibilityState !== 'visible') {
    _reconcileOnVisible = true
    return
  }
  scheduleLedgerRefresh(Math.random() * RECONNECT_SPREAD_MS)
}

async function patchCustomer(name) {
  const socket = _socket
  try {
    const ledger = await frappeGet('ssplbilling.api.customersearch_api.get_single_ledger', {
      party_name: name,
      party_type: 'Customer',
    })
    if (_socket !== socket) return
    if (ledger) {
      // Its balance/activity are not company-scoped; keep the cached (pushed) figures instead.
      delete ledger.balance
      delete ledger.activity
    }
    patchLedgerInCache(name, ledger || null)
    window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  } catch (e) {
    console.warn('[useLedgerSync] customer patch failed:', e)
  }
}

export function initLedgerSync() {
  const socket = getFrappeSocket()
  if (!socket || _socket === socket) return
  destroyLedgerSync()
  _socket = socket

  // Submits push the changed ledgers' per-company balances; patch them in place.
  _balanceHandler = (data) => {
    if (applyLedgerBalancePush(data)) window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  }
  _customerHandler = (data) => {
    if (data?.name) patchCustomer(data.name)
  }
  // The first connect is covered by the initial refresh below; later ones may have missed pushes.
  let initialConnectPending = !socket.connected
  _connectHandler = () => {
    if (initialConnectPending) {
      initialConnectPending = false
      return
    }
    scheduleReconcile()
  }
  _visibilityHandler = () => {
    if (document.visibilityState !== 'visible' || !_reconcileOnVisible) return
    _reconcileOnVisible = false
    scheduleLedgerRefresh(Math.random() * 5000)
  }

  socket.on('ledger_balances', _balanceHandler)
  socket.on('customer_update', _customerHandler)
  socket.on('connect', _connectHandler)
  document.addEventListener('visibilitychange', _visibilityHandler)
  // Reconcile changes missed before subscription, including persisted balances.
  scheduleLedgerRefresh(0)
}

export function destroyLedgerSync() {
  if (_socket) {
    _socket.off('ledger_balances', _balanceHandler)
    _socket.off('customer_update', _customerHandler)
    _socket.off('connect', _connectHandler)
  }
  if (_visibilityHandler) document.removeEventListener('visibilitychange', _visibilityHandler)
  clearTimeout(_refreshTimer)
  _refreshTimer = null
  _refreshQueued = false
  _reconcileOnVisible = false
  _balanceHandler = null
  _customerHandler = null
  _connectHandler = null
  _visibilityHandler = null
  _socket = null
}
