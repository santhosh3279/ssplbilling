import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for ledgers
const ledgers = ref([])
const partyLinks = ref({}) // { party_name: { is_primary, is_secondary, links: [] } }
const lastSync = ref(0)
const syncLoading = ref(false)

const LEDGERS_CACHE_KEY = 'sspl-ledgers-cache'
const PARTY_LINKS_CACHE_KEY = 'sspl-partylinks-cache'

function loadFromStorage() {
  try {
    const cachedLedgers = localStorage.getItem(LEDGERS_CACHE_KEY)
    if (cachedLedgers) {
      const { data, ts } = JSON.parse(cachedLedgers)
      ledgers.value = data || []
      lastSync.value = ts || 0
    }
    const cachedLinks = localStorage.getItem(PARTY_LINKS_CACHE_KEY)
    if (cachedLinks) {
      partyLinks.value = JSON.parse(cachedLinks)
    }
  } catch (e) {
    console.warn('[ledgerCache] Load from storage failed:', e)
  }
}

function saveToStorage(ledgerData, linkData) {
  try {
    localStorage.setItem(LEDGERS_CACHE_KEY, JSON.stringify({
      data: ledgerData,
      ts: Date.now()
    }))
    localStorage.setItem(PARTY_LINKS_CACHE_KEY, JSON.stringify(linkData))
  } catch (e) {
    console.warn('[ledgerCache] Save to storage failed:', e)
  }
}

// Initial load
loadFromStorage()

/**
 * Fetch all ledgers from the backend and update the global cache.
 */
export async function refreshLedgerCache(force = false) {
  if (syncLoading.value) return ledgers.value
  
  // Throttle background refreshes: skip if last sync was < 60s ago, unless forced
  if (!force && lastSync.value > 0 && (Date.now() - lastSync.value) < 60000) {
    return ledgers.value
  }

  syncLoading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.customersearch_api.get_all_ledgers')
    const rawList = data || []
    
    const newPartyLinks = {}
    const cleanedLedgers = rawList.map(l => {
      // Extract link data
      if (l.is_primary || l.is_secondary || l.party_links?.length) {
        newPartyLinks[l.name] = {
          is_primary: !!l.is_primary,
          is_secondary: !!l.is_secondary,
          links: l.party_links || []
        }
      }
      
      // Return a copy without link data
      const { is_primary, is_secondary, party_links, ...rest } = l
      return rest
    })

    ledgers.value = cleanedLedgers
    partyLinks.value = newPartyLinks
    lastSync.value = Date.now()
    
    saveToStorage(cleanedLedgers, newPartyLinks)
    return cleanedLedgers
  } catch (e) {
    console.error('[ledgerCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

// Debounce the (full-array) localStorage write so a burst of realtime balance
// patches doesn't stringify the whole ledger list on every event.
let _persistTimer = null
function _schedulePersist() {
  clearTimeout(_persistTimer)
  _persistTimer = setTimeout(() => saveToStorage(ledgers.value, partyLinks.value), 1000)
}

/**
 * Apply a realtime ledger_balance_update event to the cache: patches the party/account's
 * balance in place. Ignored if that ledger isn't cached yet (reconciled on next full refresh).
 */
export function updateLedgerBalanceInCache(name, balance) {
  if (!name) return
  const idx = ledgers.value.findIndex(l => l.name === name)
  if (idx === -1) return
  ledgers.value.splice(idx, 1, { ...ledgers.value[idx], balance: Number(balance) || 0 })
  lastSync.value = Date.now()
  _schedulePersist()
}

export function useLedgerCache() {
  return {
    ledgers,
    partyLinks,
    lastSync,
    syncLoading,
    refreshLedgerCache,
    updateLedgerBalanceInCache,
    searchLedgersInCache
  }
}

// Rank: Customers first, Suppliers second, then the rest; within each group
// busiest ledgers first (recent GL activity, provided by get_all_ledgers).
const TYPE_PRIORITY = { Customer: 0, Supplier: 1 }
function ledgerRank(a, b) {
  const pa = TYPE_PRIORITY[a.type] ?? 2
  const pb = TYPE_PRIORITY[b.type] ?? 2
  if (pa !== pb) return pa - pb
  return (b.activity || 0) - (a.activity || 0)
}

/**
 * Perform a fast local search across cached ledgers.
 * Matches are ranked (see ledgerRank), so the sort must run before the result
 * cap — a busy ledger low in the cache order would otherwise be cut off.
 */
export function searchLedgersInCache(query, typeFilter = null) {
  if (!query || query.length < 1) return []

  const q = query.toLowerCase()
  return ledgers.value
    .filter(l => {
      if (typeFilter && l.type !== typeFilter) return false

      return (
        l.name.toLowerCase().includes(q) ||
        l.label.toLowerCase().includes(q) ||
        (l.mobile_no && l.mobile_no.includes(q)) ||
        (l.gstin && l.gstin.toLowerCase().includes(q))
      )
    })
    .sort(ledgerRank)
    .slice(0, 50) // Limit for performance
}
