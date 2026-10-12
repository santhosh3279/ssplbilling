import { getFrappeSocket } from '../services/frappeSocket.js'
import { refreshLedgerCache, applyLedgerBalancePush, patchLedgersFromServer } from '../services/ledgerCache.js'

// A server restart reconnects every tab at once; spread their full refreshes (~5 s of server work each).
const RECONNECT_SPREAD_MS = 30000

let _socket = null
let _balanceHandler = null
let _ledgerHandler = null
let _patchTimer = null
const _pendingNames = new Set()
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

// Collect a burst of ledger_update events (several commits in quick succession) into one fetch.
function queueLedgerPatch(names) {
  for (const name of names) _pendingNames.add(name)
  if (_patchTimer === null) _patchTimer = setTimeout(patchPendingLedgers, 300)
}

async function patchPendingLedgers() {
  _patchTimer = null
  const socket = _socket
  const names = [..._pendingNames]
  _pendingNames.clear()
  if (!socket || !names.length) return
  try {
    const patched = await patchLedgersFromServer(names)
    if (patched && _socket === socket) window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  } catch (e) {
    console.warn('[useLedgerSync] ledger patch failed:', e)
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
  // Customer / Supplier / Employee / Account (or a linked Address, Contact, Party Link) changed.
  // `full` means no per-row patch fits (e.g. the Visible Accounts setting): reload everything.
  _ledgerHandler = (data) => {
    if (data?.full) scheduleReconcile()
    else if (data?.names?.length) queueLedgerPatch(data.names)
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
  socket.on('ledger_update', _ledgerHandler)
  socket.on('connect', _connectHandler)
  document.addEventListener('visibilitychange', _visibilityHandler)
  // Reconcile changes missed before subscription, including persisted balances. A browser that
  // has never synced settings has no company yet; the Dashboard loads ledgers once it does,
  // instead of fetching an all-company list here that is thrown away seconds later.
  if (localStorage.getItem('wb-company')) scheduleLedgerRefresh(0)
}

export function destroyLedgerSync() {
  if (_socket) {
    _socket.off('ledger_balances', _balanceHandler)
    _socket.off('ledger_update', _ledgerHandler)
    _socket.off('connect', _connectHandler)
  }
  if (_visibilityHandler) document.removeEventListener('visibilitychange', _visibilityHandler)
  clearTimeout(_refreshTimer)
  _refreshTimer = null
  _refreshQueued = false
  _reconcileOnVisible = false
  _balanceHandler = null
  _ledgerHandler = null
  clearTimeout(_patchTimer)
  _patchTimer = null
  _pendingNames.clear()
  _connectHandler = null
  _visibilityHandler = null
  _socket = null
}
