import { getFrappeSocket } from '../services/frappeSocket.js'
import { updateLedgerBalanceInCache } from '../services/ledgerCache.js'

let _balanceHandler = null

export function initLedgerSync() {
  const socket = getFrappeSocket()

  _balanceHandler = (data) => {
    if (!data?.name) return
    console.log('[useLedgerSync] received ledger_balance_update:', data)
    updateLedgerBalanceInCache(data.name, data.balance)
    window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  }
  socket.on('ledger_balance_update', _balanceHandler)

  console.log('[useLedgerSync] listening for ledger_balance_update')
}

export function destroyLedgerSync() {
  const socket = getFrappeSocket()
  if (_balanceHandler) {
    socket.off('ledger_balance_update', _balanceHandler)
    _balanceHandler = null
  }
}
