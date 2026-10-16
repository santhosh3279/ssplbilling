import { serverNow, serverToday } from './serverTime'
import { ref, toRaw } from 'vue'
import { frappePost } from '../api.js'
import { session } from '../session.js'
import { readLedgerSnapshot, writeLedgerSnapshot } from './ledgerCacheStore'

// Global reactive state for ledgers
const ledgers = ref([])
const partyLinks = ref({}) // { party_name: { is_primary, is_secondary, links: [] } }
const lastSync = ref(0)
const syncLoading = ref(false)
const cacheContext = ref(null)
let pendingRefresh = null
// Server timestamp of the last full/delta sync (sent back as `since`) and when it ran locally.
let syncTs = null
let syncedAt = 0

// Socket events (ledger_update, ledger_balances) keep the cache current, so opening a search only
// asks the server for changes once the last sync is older than this.
const STALE_AFTER_MS = 15 * 60 * 1000

function currentContext() {
  return JSON.stringify({
    company: localStorage.getItem('wb-company') || '',
    alternative_company: localStorage.getItem('ae-alternative_company') || '',
    cost_center: localStorage.getItem('wb-cost-center') || ''
  })
}

// Pre-IndexedDB storage (localStorage), read once for an instant first paint, then removed.
const LEGACY_LEDGERS_KEY = 'sspl-ledgers-cache-v2'
const LEGACY_PARTY_LINKS_KEY = 'sspl-partylinks-cache'

async function loadFromStorage() {
  try {
    const snap = await readLedgerSnapshot()
    if (snap && snap.context === currentContext()) {
      cacheContext.value = snap.context
      ledgers.value = JSON.parse(snap.ledgers || '[]')
      partyLinks.value = snap.partyLinks || {}
      lastSync.value = snap.lastSync || 0
      syncTs = snap.syncTs || null
      syncedAt = snap.syncedAt || 0
    }
  } catch (e) {
    console.warn('[ledgerCache] Load from IndexedDB failed:', e)
  }
  try {
    const legacy = localStorage.getItem(LEGACY_LEDGERS_KEY)
    if (legacy && !cacheContext.value) {
      const { data, ts, context } = JSON.parse(legacy)
      // No sync point: the first refresh downloads the full list.
      if (context === currentContext()) {
        cacheContext.value = context
        ledgers.value = data || []
        lastSync.value = ts || 0
        partyLinks.value = JSON.parse(localStorage.getItem(LEGACY_PARTY_LINKS_KEY) || '{}')
      }
    }
  } catch (e) {
    console.warn('[ledgerCache] Legacy cache unreadable:', e)
  }
  localStorage.removeItem(LEGACY_LEDGERS_KEY)
  localStorage.removeItem(LEGACY_PARTY_LINKS_KEY)
}

function saveToStorage() {
  // Serialise now: later in-place patches must not leak into a snapshot whose syncTs predates them.
  writeLedgerSnapshot({
    context: cacheContext.value,
    syncTs,
    syncedAt,
    lastSync: lastSync.value,
    ledgers: JSON.stringify(toRaw(ledgers.value)),
    partyLinks: toRaw(partyLinks.value)
  }).catch(e => console.warn('[ledgerCache] Save to IndexedDB failed:', e))
}

// IndexedDB is async: every refresh waits for the stored copy first, so a page load serves it
// instead of downloading the full list.
export const ledgerCacheReady = loadFromStorage()

/**
 * Bring the ledger cache up to date.
 * - force: download the full list (F5 / explicit refresh, company change).
 * - otherwise: nothing if the last sync is under 15 minutes old; a delta (changes since the last
 *   sync) if older; the full list when there is no usable copy or it is from an earlier day
 *   (the 90-day activity ranking and last-invoice dates move with the date).
 */
export async function refreshLedgerCache(force = false) {
  return runRefresh(force ? 'full' : 'auto')
}

/** Catch up after a reconnect or on the periodic check: always a delta when a copy exists. */
export async function catchUpLedgerCache() {
  return runRefresh('delta')
}

// Ledger endpoints are for System Users. App.vue starts the sync on every page, including the
// public catalogue, where a guest or website user (with a company left in localStorage from an
// earlier staff login) would otherwise get 403s.
async function canSyncLedgers() {
  try {
    await session.checkWebsiteUser()
  } catch {
    return false
  }
  return session.isSystemUser.value
}

async function runRefresh(mode) {
  await ledgerCacheReady
  if (!(await canSyncLedgers())) return ledgers.value
  // A forced realtime refresh must start after any older request finishes:
  // that request may have read balances before the voucher was committed.
  while (pendingRefresh) {
    await pendingRefresh
    if (mode !== 'full' && cacheContext.value === currentContext()) return ledgers.value
  }
  pendingRefresh = fetchLedgerCache(mode)
  try {
    return await pendingRefresh
  } finally {
    pendingRefresh = null
  }
}

function syncMode(mode, context) {
  const usable = cacheContext.value === context && syncTs && ledgers.value.length > 0
  if (mode === 'full' || !usable) return 'full'
  if (mode === 'delta') return 'delta'
  if (String(syncTs).slice(0, 10) !== serverToday()) return 'full'
  return serverNow().getTime() - syncedAt < STALE_AFTER_MS ? 'none' : 'delta'
}

async function fetchLedgerCache(requested) {
  const context = currentContext()
  const mode = syncMode(requested, context)
  if (mode === 'none') return ledgers.value

  syncLoading.value = true
  const startedAt = serverNow().getTime() / 1000
  try {
    const { company, alternative_company, cost_center } = JSON.parse(context)
    const data = await frappePost('ssplbilling.api.customersearch_api.get_ledgers_sync', {
      since: mode === 'delta' ? syncTs : null,
      company,
      alternative_company,
      cost_center
    }, { silent: mode === 'delta' })

    if (data.full) {
      const { rows, links } = splitPartyLinks(data.ledgers || [])
      cacheContext.value = context
      ledgers.value = rows
      partyLinks.value = links
    } else {
      applyLedgerRows(data.ledgers || [], data.removed || [])
    }
    // Balances pushed while this request ran may be newer than what it read.
    reapplyPushesSince(startedAt)
    syncTs = data.sync_ts
    syncedAt = serverNow().getTime()
    lastSync.value = syncedAt

    saveToStorage()
    return ledgers.value
  } catch (e) {
    console.error('[ledgerCache] Refresh failed:', e)
    throw e
  } finally {
    syncLoading.value = false
  }
}

// Server rows carry their Party Link data inline; the cache keeps it in partyLinks instead.
function splitPartyLinks(rawList) {
  const links = {}
  const rows = rawList.map(l => {
    if (l.is_primary || l.is_secondary || l.party_links?.length) {
      links[l.name] = {
        is_primary: !!l.is_primary,
        is_secondary: !!l.is_secondary,
        links: l.party_links || []
      }
    }
    const { is_primary, is_secondary, party_links, ...rest } = l
    return rest
  })
  return { rows, links }
}

const labelKey = l => (l.label || '').toLowerCase()

/**
 * Refetch the named ledgers (a `ledger_update` socket event) and patch them into the cache in one
 * reactive change. Rows come from the same builder as the full list, so they are company-scoped
 * like it; names the server no longer returns (deleted, renamed, disabled, hidden) are dropped.
 */
export async function patchLedgersFromServer(names) {
  const context = currentContext()
  // Nothing loaded for this company yet: the next full refresh will include these rows.
  if (!names?.length || cacheContext.value !== context) return false
  if (!(await canSyncLedgers())) return false
  const { company, alternative_company, cost_center } = JSON.parse(context)
  const startedAt = serverNow().getTime() / 1000
  const res = await frappePost('ssplbilling.api.customersearch_api.get_ledgers_by_name', {
    names: JSON.stringify(names), company, alternative_company, cost_center
  }, { silent: true })
  // A full refresh or company switch that landed meanwhile already holds newer data.
  if (cacheContext.value !== context || pendingRefresh) return false
  applyLedgerRows(res?.ledgers || [], res?.removed || [])
  reapplyPushesSince(startedAt)
  lastSync.value = serverNow().getTime()
  _schedulePersist()
  return true
}

function applyLedgerRows(rawRows, removed) {
  const { rows, links } = splitPartyLinks(rawRows)
  const touched = new Set([...rows.map(r => r.name), ...removed])
  // A party and an account may share a name, so a name can map to more than one row.
  const fresh = new Map()
  for (const r of rows) {
    if (!fresh.has(r.name)) fresh.set(r.name, [])
    fresh.get(r.name).push(r)
  }
  const next = []
  for (const l of toRaw(ledgers.value)) {
    if (!touched.has(l.name)) next.push(l)
    else if (fresh.has(l.name)) {
      next.push(...fresh.get(l.name))
      fresh.delete(l.name)
    }
  }
  if (fresh.size) {
    for (const group of fresh.values()) next.push(...group)
    next.sort((a, b) => (labelKey(a) < labelKey(b) ? -1 : labelKey(a) > labelKey(b) ? 1 : 0))
  }
  const nextLinks = { ...partyLinks.value }
  for (const name of touched) delete nextLinks[name]
  Object.assign(nextLinks, links)
  ledgers.value = next
  partyLinks.value = nextLinks
}

// Debounce the (full-array) IndexedDB write so a burst of realtime balance
// patches doesn't stringify the whole ledger list on every event.
let _persistTimer = null
function _schedulePersist() {
  clearTimeout(_persistTimer)
  _persistTimer = setTimeout(saveToStorage, 1000)
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

/**
 * Employee search from the cache, shaped like the server's search_employees endpoints
 * ({ name, employee_name, designation, balance_incentive }), sorted by name like them.
 * Returns null while this company's ledgers aren't loaded so callers fall back to the server.
 * `matchId` also matches the employee ID (incentive_ledger_api does; incentive_api doesn't).
 */
export function searchEmployeesInCache(query, { limit = 20, matchId = true } = {}) {
  if (cacheContext.value !== currentContext()) return null
  const employees = ledgers.value.filter(l => l.type === 'Employee')
  if (!employees.length) return null
  const q = (query || '').toLowerCase()
  return employees
    .filter(e => (e.label || '').toLowerCase().includes(q) || (matchId && e.name.toLowerCase().includes(q)))
    .map(e => ({
      name: e.name,
      employee_name: e.label || '',
      designation: e.designation || '',
      balance_incentive: e.balance_incentive ?? 0
    }))
    .sort((a, b) => a.employee_name.toLowerCase().localeCompare(b.employee_name.toLowerCase()))
    .slice(0, limit)
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
