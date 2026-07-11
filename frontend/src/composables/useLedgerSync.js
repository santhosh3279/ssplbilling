import { getFrappeSocket } from '../services/frappeSocket.js'
import { updateLedgerBalanceInCache, patchLedgerInCache } from '../services/ledgerCache.js'
import { frappeGet } from '../api.js'

let _balanceHandler = null
let _customerHandler = null

async function _patchCustomer(customerName) {
  console.log('[useLedgerSync] patching cache for customer:', customerName)
  try {
    const result = await frappeGet('ssplbilling.api.customersearch_api.get_single_ledger', {
      party_name: customerName,
      party_type: 'Customer'
    })
    patchLedgerInCache(customerName, result || null)
    window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  } catch (e) {
    console.warn('[useLedgerSync] customer patch failed:', e)
  }
}

export function initLedgerSync() {
  const socket = getFrappeSocket()

  _balanceHandler = (data) => {
    if (!data?.name) return
    console.log('[useLedgerSync] received ledger_balance_update:', data)
    updateLedgerBalanceInCache(data.name, data.balance)
    window.dispatchEvent(new CustomEvent('wb-ledger-cache-updated'))
  }
  socket.on('ledger_balance_update', _balanceHandler)

  _customerHandler = (data) => {
    if (!data?.name) return
    console.log('[useLedgerSync] received customer_update:', data)
    _patchCustomer(data.name)
  }
  socket.on('customer_update', _customerHandler)

  console.log('[useLedgerSync] listening for ledger_balance_update and customer_update')
}

export function destroyLedgerSync() {
  const socket = getFrappeSocket()
  if (_balanceHandler) {
    socket.off('ledger_balance_update', _balanceHandler)
    _balanceHandler = null
  }
  if (_customerHandler) {
    socket.off('customer_update', _customerHandler)
    _customerHandler = null
  }
}
