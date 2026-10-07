import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshLedgerCache } from '../services/ledgerCache.js'

let _socket = null
let _balanceHandler = null
let _customerHandler = null
let _connectHandler = null
let _refreshTimer = null
let _refreshRunning = false
let _refreshQueued = false

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
    // Event balances and get_single_ledger are not company-filtered. Fetch the
    // active and alternative company balances together instead of patching them.
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

export function initLedgerSync() {
  const socket = getFrappeSocket()
  if (!socket || _socket === socket) return
  destroyLedgerSync()
  _socket = socket

  _balanceHandler = (data) => {
    if (data?.name) scheduleLedgerRefresh()
  }
  _customerHandler = (data) => {
    if (data?.name) scheduleLedgerRefresh()
  }
  _connectHandler = () => scheduleLedgerRefresh(0)

  socket.on('ledger_balance_update', _balanceHandler)
  socket.on('customer_update', _customerHandler)
  socket.on('connect', _connectHandler)
  // Reconcile changes missed before subscription, including persisted balances.
  scheduleLedgerRefresh(0)
}

export function destroyLedgerSync() {
  if (_socket) {
    _socket.off('ledger_balance_update', _balanceHandler)
    _socket.off('customer_update', _customerHandler)
    _socket.off('connect', _connectHandler)
  }
  clearTimeout(_refreshTimer)
  _refreshTimer = null
  _refreshQueued = false
  _balanceHandler = null
  _customerHandler = null
  _connectHandler = null
  _socket = null
}
