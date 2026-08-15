// Cached lookups for the two lists every print dialog needs: the Print Templates
// valid for a doctype and the configured Printers. Both change rarely (admin-only
// masters) but each open used to cost a separate sequential HTTP round trip, which
// is what made PrintOptionsModal feel slow — the queries themselves run in <20ms.
//
// Strategy: serve from localStorage instantly when fresh, otherwise fetch both in
// parallel. Callers that already have a cached copy can render immediately and call
// refreshPrintCache() to revalidate in the background.
import { frappeGet } from '../api.js'

const TEMPLATES_KEY = 'wb-print-templates-v1' // { [doctype]: { ts, data } }
const PRINTERS_KEY = 'wb-printers-v1' // { ts, data }
const TTL = 30 * 60 * 1000 // 30 mins — matches Dashboard's GENERIC_CACHE_TTL

function readCache(key, bucket) {
  try {
    const raw = JSON.parse(localStorage.getItem(key) || 'null')
    const entry = bucket ? raw?.[bucket] : raw
    if (!entry || !Array.isArray(entry.data)) return null
    return { data: entry.data, fresh: Date.now() - (entry.ts || 0) < TTL }
  } catch (e) {
    return null
  }
}

function writeCache(key, bucket, data) {
  try {
    const entry = { ts: Date.now(), data }
    if (bucket) {
      const raw = JSON.parse(localStorage.getItem(key) || '{}') || {}
      raw[bucket] = entry
      localStorage.setItem(key, JSON.stringify(raw))
    } else {
      localStorage.setItem(key, JSON.stringify(entry))
    }
  } catch (e) {
    // quota / private mode — cache is an optimisation, never fatal
  }
}

async function fetchTemplates(doctype) {
  const rows =
    (await frappeGet('frappe.client.get_list', {
      doctype: 'Print Template',
      filters: { document_type: doctype },
      fields: ['name', 'format_type'],
      limit: 100,
    })) || []
  writeCache(TEMPLATES_KEY, doctype, rows)
  return rows
}

async function fetchPrinters() {
  const rows =
    (await frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers')) || []
  writeCache(PRINTERS_KEY, null, rows)
  return rows
}

// Synchronous cache read. Returns null unless BOTH lists are cached, so callers can
// skip the loading spinner entirely. `fresh` is false for a stale-but-usable hit.
export function getCachedPrintLists(doctype) {
  const templates = readCache(TEMPLATES_KEY, doctype)
  const printers = readCache(PRINTERS_KEY, null)
  if (!templates || !printers) return null
  return {
    templates: templates.data,
    printers: printers.data,
    fresh: templates.fresh && printers.fresh,
  }
}

// Fetches both lists in parallel (one round trip's worth of latency, not two) and
// refreshes the cache.
export async function refreshPrintCache(doctype) {
  const [templates, printers] = await Promise.all([fetchTemplates(doctype), fetchPrinters()])
  return { templates, printers, fresh: true }
}

// Cache-first: returns immediately on a fresh hit, otherwise fetches in parallel.
export async function loadPrintLists(doctype) {
  const cached = getCachedPrintLists(doctype)
  if (cached?.fresh) return cached
  return refreshPrintCache(doctype)
}

// Fire-and-forget warm-up, used by the Dashboard so the first print of a session
// also opens at zero round trips.
export function prefetchPrintLists(doctype = 'Sales Invoice') {
  const cached = getCachedPrintLists(doctype)
  if (cached?.fresh) return
  refreshPrintCache(doctype).catch(() => {})
}
