import { serverNow } from './serverTime'
import { ref } from 'vue'
import { frappeGet } from '../api.js'

// Global reactive state for ledgers
const ledgers = ref([])
const partyLinks = ref({}) // { party_name: { is_primary, is_secondary, links: [] } }
const lastSync = ref(0)
const syncLoading = ref(false)
const cacheContext = ref(null)
let pendingRefresh = null

function currentContext() {
  return JSON.stringify({
    company: localStorage.getItem('wb-company') || '',
    alternative_company: localStorage.getItem('ae-alternative_company') || '',
    cost_center: localStorage.getItem('wb-cost-center') || ''
  })
}

const LEDGERS_CACHE_KEY = 'sspl-ledgers-cache-v2'
const PARTY_LINKS_CACHE_KEY = 'sspl-partylinks-cache'

function loadFromStorage() {
  try {
    const cachedLedgers = localStorage.getItem(LEDGERS_CACHE_KEY)
    if (cachedLedgers) {
      const { data, ts, context } = JSON.parse(cachedLedgers)
      if (context !== currentContext()) return
      cacheContext.value = context
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
      ts: lastSync.value,
      context: cacheContext.value
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
  // A forced realtime refresh must start after any older request finishes:
  // that request may have read balances before the voucher was committed.
  while (pendingRefresh) {
    await pendingRefresh
    if (!force && cacheContext.value === currentContext()) return ledgers.value
  }
  pendingRefresh = fetchLedgerCache(force)
  try {
    return await pendingRefresh
  } finally {
    pendingRefresh = null
  }
}

async function fetchLedgerCache(force) {
  const context = currentContext()
  
  // Throttle background refreshes: skip if last sync was < 60s ago, unless forced
  if (!force && cacheContext.value === context && lastSync.value > 0 && (serverNow().getTime() - lastSync.value) < 60000) {
    return ledgers.value
  }

  syncLoading.value = true
  const startedAt = serverNow().getTime() / 1000
  try {
    const { company, alternative_company, cost_center } = JSON.parse(context)
    const data = await frappeGet('ssplbilling.api.customersearch_api.get_all_ledgers', {
      company,
      alternative_company,
      cost_center
    })
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

    cacheContext.value = context
    ledgers.value = cleanedLedgers
    // Balances pushed while this request ran may be newer than what it read.
    reapplyPushesSince(startedAt)
    partyLinks.value = newPartyLinks
    lastSync.value = serverNow().getTime()
    
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
  lastSync.value = serverNow().getTime()
  _schedulePersist()
}

// Latest pushed snapshot per ledger: { ts (server seconds), snapshot }. Lets a full refresh that
// started before a push re-apply it, and drops pushes that arrive out of order.
const PUSH_RETENTION_S = 600
const recentPushes = new Map()

function applySnapshot(snapshot) {
  const { company, alternative_company } = JSON.parse(currentContext())
  const balances = snapshot.balances || {}
  // Same scoping as get_all_ledgers: no company selected means the sum over all companies.
  const balance = company
    ? balances[company] || 0
    : Object.values(balances).reduce((sum, value) => sum + (Number(value) || 0), 0)
  let changed = false
  ledgers.value.forEach((ledger, idx) => {
    if (ledger.name !== snapshot.name) return
    const next = { ...ledger, balance }
    if (alternative_company) next.alternative_balance = balances[alternative_company] || 0
    if (snapshot.last_invoice_date) next.last_invoice_date = snapshot.last_invoice_date
    ledgers.value.splice(idx, 1, next)
    changed = true
  })
  return changed
}

function reapplyPushesSince(startedAt) {
  const cutoff = serverNow().getTime() / 1000 - PUSH_RETENTION_S
  for (const [name, push] of recentPushes) {
    if (push.ts < cutoff) recentPushes.delete(name)
    else if (push.ts > startedAt) applySnapshot(push.snapshot)
  }
}

/**
 * Apply a realtime `ledger_balances` push ({ ts, ledgers: [{ name, balances: { company: bal },
 * last_invoice_date? }] }) to the cached rows. Returns true when any cached ledger changed.
 */
export function applyLedgerBalancePush(payload) {
  const ts = Number(payload?.ts) || 0
  let changed = false
  for (const snapshot of payload?.ledgers || []) {
    if (!snapshot?.name) continue
    const previous = recentPushes.get(snapshot.name)
    if (previous && previous.ts > ts) continue
    recentPushes.set(snapshot.name, { ts, snapshot })
    if (applySnapshot(snapshot)) changed = true
  }
  if (changed) {
    lastSync.value = serverNow().getTime()
    _schedulePersist()
  }
  return changed
}

/**
 * Patch a single ledger in the cache without a full refresh.
 * Pass null as newData to remove the ledger (deleted / disabled).
 */
export function patchLedgerInCache(name, newData) {
  const idx = ledgers.value.findIndex(l => l.name === name)
  if (newData === null) {
    if (idx !== -1) ledgers.value.splice(idx, 1)
  } else if (idx !== -1) {
    // Preserve balance and activity if not provided in the patch
    const merged = {
      ...ledgers.value[idx],
      ...newData,
      balance: newData.balance !== undefined ? newData.balance : ledgers.value[idx].balance,
      activity: newData.activity !== undefined ? newData.activity : ledgers.value[idx].activity
    }
    ledgers.value.splice(idx, 1, merged)
  } else {
    // New ledger — insert maintaining label alphabetical order
    const insertAt = ledgers.value.findIndex(l => (l.label || '').toLowerCase() > (newData.label || '').toLowerCase())
    if (insertAt === -1) ledgers.value.push(newData)
    else ledgers.value.splice(insertAt, 0, newData)
  }
  lastSync.value = serverNow().getTime()
  _schedulePersist()
}

export function useLedgerCache() {
  return {
    ledgers,
    cacheContext,
    partyLinks,
    lastSync,
    syncLoading,
    refreshLedgerCache,
    updateLedgerBalanceInCache,
    applyLedgerBalancePush,
    patchLedgerInCache,
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
