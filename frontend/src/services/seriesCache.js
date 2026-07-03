import { dashboardApi } from './dashboard.js'

// Naming-series localStorage cache for the core billing DocTypes.
// Dashboard calls syncNamingSeries() on load; consumers call
// getSeriesForDoctype(), which refetches automatically when the cache is empty.

export const SERIES_DOCTYPES = [
  'Sales Invoice',
  'Purchase Invoice',
  'Quotation',
  'Sales Order',
  'Purchase Order',
]

const NAMING_SERIES_TS_KEY = 'wb-naming-series-ts-v1'
const ALL_PREFIXES_KEY = 'wb-all-naming-series'
const CACHE_TTL = 30 * 60 * 1000 // 30 mins — naming series rarely change

export function seriesKeyFor(doctype) {
  return `wb-series-${doctype.toLowerCase().replace(/ /g, '-')}`
}

function readKey(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || 'null')
    return Array.isArray(parsed) && parsed.length ? parsed : null
  } catch {
    return null
  }
}

function cacheIsComplete() {
  return SERIES_DOCTYPES.every(dt => readKey(seriesKeyFor(dt))) && readKey(ALL_PREFIXES_KEY)
}

// Single in-flight fetch shared by concurrent callers.
let inflight = null

/**
 * Fetch naming series for all SERIES_DOCTYPES and store them under the
 * wb-series-<doctype> keys plus the flattened wb-all-naming-series list.
 * Skips the network call while the cache is fresh AND complete, unless forced.
 */
export async function syncNamingSeries(force = false) {
  const ts = Number(localStorage.getItem(NAMING_SERIES_TS_KEY) || 0)
  if (!force && (Date.now() - ts) < CACHE_TTL && cacheIsComplete()) return

  if (!inflight) {
    inflight = (async () => {
      const seriesMap = await dashboardApi.getAllNamingSeries()
      if (!seriesMap) return
      const allPrefixes = new Set()
      Object.keys(seriesMap).forEach(dt => {
        const seriesList = seriesMap[dt] || []
        localStorage.setItem(seriesKeyFor(dt), JSON.stringify(seriesList))

        seriesList.forEach(s => {
          const val = typeof s === 'string' ? s : (s?.prefix || '')
          const prefix = val.split('.')[0]
          if (prefix) allPrefixes.add(prefix)
        })
      })
      localStorage.setItem(ALL_PREFIXES_KEY, JSON.stringify([...allPrefixes]))
      localStorage.setItem(NAMING_SERIES_TS_KEY, String(Date.now()))
    })().finally(() => { inflight = null })
  }
  await inflight
}

/**
 * Return the cached series list for one DocType. When the key is missing or
 * empty, refetch all series first, so consumers never see an empty cache
 * while the backend has data. Returns [] only if the fetch itself fails.
 */
export async function getSeriesForDoctype(doctype) {
  let list = readKey(seriesKeyFor(doctype))
  if (list) return list

  try {
    await syncNamingSeries(true)
  } catch (e) {
    console.warn('[seriesCache] syncNamingSeries failed:', e)
  }
  return readKey(seriesKeyFor(doctype)) || []
}
