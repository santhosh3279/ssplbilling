import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for ledgers
const ledgers = ref([])
const lastSync = ref(0)
const syncLoading = ref(false)

const LEDGERS_CACHE_KEY = 'sspl-ledgers-cache'

function loadFromStorage() {
  try {
    const cached = localStorage.getItem(LEDGERS_CACHE_KEY)
    if (cached) {
      const { data, ts } = JSON.parse(cached)
      ledgers.value = data || []
      lastSync.value = ts || 0
    }
  } catch (e) {
    console.warn('[ledgerCache] Load from storage failed:', e)
  }
}

function saveToStorage(data) {
  try {
    localStorage.setItem(LEDGERS_CACHE_KEY, JSON.stringify({
      data,
      ts: Date.now()
    }))
  } catch (e) {
    console.warn('[ledgerCache] Save to storage failed:', e)
  }
}

// Initial load
loadFromStorage()

/**
 * Fetch all ledgers from the backend and update the global cache.
 */
export async function refreshLedgerCache() {
  syncLoading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.customersearch_api.get_all_ledgers')
    ledgers.value = data || []
    lastSync.value = Date.now()
    saveToStorage(ledgers.value)
    return ledgers.value
  } catch (e) {
    console.error('[ledgerCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

export function useLedgerCache() {
  return {
    ledgers,
    lastSync,
    syncLoading,
    refreshLedgerCache
  }
}
