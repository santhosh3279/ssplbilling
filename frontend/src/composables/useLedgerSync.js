import { getFrappeSocket } from '../services/frappeSocket.js'
import {
  refreshLedgerCache, catchUpLedgerCache, applyLedgerBalancePush, patchLedgersFromServer
} from '../services/ledgerCache.js'

// A server restart reconnects every tab at once; spread their catch-up requests.
const RECONNECT_SPREAD_MS = 30000
// Safety net for changes no socket event announced (GL from other documents, SQL edits, a lost
// message): every 15 minutes ask for the ledgers changed since the last sync. Delta only.
const PERIODIC_CHECK_MS = 15 * 60 * 1000

// 'full' reloads every ledger; 'delta' fetches changes since the last sync; 'auto' lets the cache
// decide (nothing / delta / full, see refreshLedgerCache). A queued stronger mode wins.
const MODE_RANK = { auto: 0, delta: 1, full: 2 }
const RUN = { auto: () => refreshLedgerCache(false), delta: catchUpLedgerCache, full: () => refreshLedgerCache(true) }

let _socket = null
let _balanceHandler = null
let _ledgerHandler = null
let _patchTimer = null
const _pendingNames = new Set()
let _connectHandler = null
let _visibilityHandler = null
let _refreshTimer = null
let _refreshRunning = false
let _queuedMode = null
let _visibleMode = null
let _periodicTimer = null

const stronger = (a, b) => (!a || MODE_RANK[b] > MODE_RANK[a] ? b : a)

function scheduleLedgerRefresh(delay = 500, mode = 'auto') {
  if (!_socket) return
  _queuedMode = stronger(_queuedMode, mode)
  if (_refreshTimer !== null || _refreshRunning) return
  _refreshTimer = setTimeout(refreshLedgers, delay)
}

async function refreshLedgers() {
  _refreshTimer = null
  if (!_socket) return
  const socket = _socket
  const mode = _queuedMode || 'auto'
  _queuedMode = null
  _refreshRunning = true
  try {
    await RUN[mode]()
    if (_socket === socket) {
      window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
    }
  } catch (e) {
    console.warn('[useLedgerSync] ledger refresh failed:', e)
  } finally {
    _refreshRunning = false
    if (_queuedMode) scheduleLedgerRefresh(500, _queuedMode)
  }
}

// Hidden tabs wait until they are looked at; visible ones start at a random point in the window.
function scheduleReconcile(mode, spreadMs = RECONNECT_SPREAD_MS) {
  if (document.visibilityState !== 'visible') {
    _visibleMode = stronger(_visibleMode, mode)
    return
  }
  scheduleLedgerRefresh(Math.random() * spreadMs, mode)
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
    if (data?.full) scheduleReconcile('full')
    else if (data?.names?.length) queueLedgerPatch(data.names)
  }
  // The first connect is covered by the initial refresh below; later ones may have missed pushes.
  let initialConnectPending = !socket.connected
  _connectHandler = () => {
    if (initialConnectPending) {
      initialConnectPending = false
      return
    }
    scheduleReconcile('delta')
  }
  _visibilityHandler = () => {
    if (document.visibilityState !== 'visible' || !_visibleMode) return
    const mode = _visibleMode
    _visibleMode = null
    scheduleLedgerRefresh(Math.random() * 5000, mode)
  }

  socket.on('ledger_balances', _balanceHandler)
  socket.on('ledger_update', _ledgerHandler)
  socket.on('connect', _connectHandler)
  document.addEventListener('visibilitychange', _visibilityHandler)
  // Reconcile changes missed before subscription, including persisted balances. A browser that
  // has never synced settings has no company yet; the Dashboard loads ledgers once it does,
  // instead of fetching an all-company list here that is thrown away seconds later.
  // The stored copy (IndexedDB) is reused: fresh → nothing, older → delta, earlier day → full.
  if (localStorage.getItem('wb-company')) scheduleLedgerRefresh(0, 'auto')
  clearInterval(_periodicTimer)
  _periodicTimer = setInterval(() => scheduleReconcile('delta', 5000), PERIODIC_CHECK_MS)
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
  clearInterval(_periodicTimer)
  _periodicTimer = null
  _queuedMode = null
  _visibleMode = null
  _balanceHandler = null
  _ledgerHandler = null
  clearTimeout(_patchTimer)
  _patchTimer = null
  _pendingNames.clear()
  _connectHandler = null
  _visibilityHandler = null
  _socket = null
}
