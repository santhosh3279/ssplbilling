// localStorage cache for the sidebar bill panels (Sales Invoice, Purchase
// Invoice, orders, quotations). One entry per doctype holding the last
// default-view list (no search query) plus the params it was fetched with.
// While a page is open, bill_panel_update socket events upsert rows into the
// cache, so a fresh cache entry can be shown without a server call.

const CACHE_PREFIX = 'wb-bill-panel-'
const CACHE_TTL = 5 * 60 * 1000 // revalidate after 5 min — socket events may be missed while no page is open
const MAX_ROWS = 100

function cacheKey(doctype) {
  return `${CACHE_PREFIX}${doctype.toLowerCase().replace(/ /g, '-')}`
}

function readCache(doctype) {
  try {
    const parsed = JSON.parse(localStorage.getItem(cacheKey(doctype)) || 'null')
    return parsed && Array.isArray(parsed.rows) ? parsed : null
  } catch {
    return null
  }
}

function sameParams(a, b) {
  return (
    a.date === b.date &&
    Boolean(a.draftOnly) === Boolean(b.draftOnly) &&
    JSON.stringify([...(a.series || [])].sort()) === JSON.stringify([...(b.series || [])].sort())
  )
}

/**
 * Return the cached rows for a doctype when they were fetched with the same
 * params (date, series, draftOnly) and are still fresh; null otherwise.
 */
export function loadCachedPanel(doctype, params) {
  const cached = readCache(doctype)
  if (!cached || !cached.params) return null
  if ((Date.now() - (cached.ts || 0)) > CACHE_TTL) return null
  if (!sameParams(cached.params, params)) return null
  return cached.rows
}

/** Store a freshly fetched default-view list along with its params. */
export function saveCachedPanel(doctype, params, rows) {
  try {
    localStorage.setItem(cacheKey(doctype), JSON.stringify({
      params: { date: params.date, series: params.series || [], draftOnly: Boolean(params.draftOnly) },
      rows: (rows || []).slice(0, MAX_ROWS),
      ts: Date.now(),
    }))
  } catch (e) {
    console.warn('[billPanelCache] save failed:', e)
  }
}

/**
 * Apply a bill_panel_update socket payload to an in-memory list, returning a
 * new array (or the original when nothing matched). Mirrors the sidebar list
 * semantics: cancelled/trashed bills drop out, draft-only panels drop
 * submitted bills, new bills go on top (lists are ordered name desc).
 */
export function applyPanelEvent(rows, payload, { date, draftOnly } = {}) {
  const row = payload?.row
  if (!row || !row.name) return rows

  const remove =
    payload.event === 'on_trash' ||
    row.docstatus === 2 ||
    (draftOnly && row.docstatus !== 0)

  const idx = rows.findIndex(r => r.name === row.name)

  if (remove) {
    return idx === -1 ? rows : rows.filter(r => r.name !== row.name)
  }

  // A row dated outside the panel's date doesn't belong in the list.
  const rowDate = row.posting_date || row.transaction_date
  if (date && rowDate && rowDate !== date) {
    return idx === -1 ? rows : rows.filter(r => r.name !== row.name)
  }

  if (idx === -1) return [row, ...rows].slice(0, MAX_ROWS)
  const next = [...rows]
  next[idx] = { ...next[idx], ...row }
  return next
}

/**
 * Upsert a socket payload straight into the localStorage cache (regardless of
 * whether a page is open), so the next page open sees the change instantly.
 */
export function applyEventToCache(payload) {
  const doctype = payload?.doctype
  if (!doctype || !payload?.row) return
  const cached = readCache(doctype)
  if (!cached || !cached.params) return

  const { series = [] } = cached.params
  if (series.length && payload.naming_series && !series.includes(payload.naming_series)) return

  const rows = applyPanelEvent(cached.rows, payload, {
    date: cached.params.date,
    draftOnly: cached.params.draftOnly,
  })
  if (rows === cached.rows) return
  try {
    localStorage.setItem(cacheKey(doctype), JSON.stringify({ ...cached, rows }))
  } catch (e) {
    console.warn('[billPanelCache] update failed:', e)
  }
}
