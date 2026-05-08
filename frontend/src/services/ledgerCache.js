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

export function useLedgerCache() {
  return {
    ledgers,
    partyLinks,
    lastSync,
    syncLoading,
    refreshLedgerCache
  }
}
