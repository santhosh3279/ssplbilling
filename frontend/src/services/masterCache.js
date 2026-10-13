import { frappeGet } from '../api.js'

// In-memory, per-tab cache for master data that rarely changes (price lists, tax
// templates, warehouses, series defaults). Pages and modals that remount — or several
// components asking for the same list — share one request until the TTL runs out.
// Failures are never cached. Callers get a copy, so mutating a result is safe.

const DEFAULT_TTL_MS = 10 * 60 * 1000
const entries = new Map()

function cached(key, fetcher, ttlMs = DEFAULT_TTL_MS) {
  const hit = entries.get(key)
  if (hit && Date.now() - hit.at < ttlMs) return hit.promise.then(clone)
  const promise = fetcher()
  entries.set(key, { promise, at: Date.now() })
  promise.catch(() => { if (entries.get(key)?.promise === promise) entries.delete(key) })
  return promise.then(clone)
}

function clone(value) {
  return value == null ? value : structuredClone(value)
}

/** Drop cached entries whose key starts with `prefix` (everything when omitted). */
export function invalidateMasterCache(prefix = '') {
  for (const key of [...entries.keys()]) {
    if (key.startsWith(prefix)) entries.delete(key)
  }
}

/** frappe.client.get_list with the same args, cached by doctype + args. */
export function getCachedList(args, ttlMs) {
  return cached(`list:${args.doctype}:${JSON.stringify(args)}`, () => frappeGet('frappe.client.get_list', args), ttlMs)
}

/** salesinvoice_api.get_series_defaults, cached per doctype + series. */
export function getSeriesDefaults(namingSeries, doctype, ttlMs) {
  return cached(
    `series-defaults:${doctype}:${namingSeries}`,
    () => frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: namingSeries, doctype }),
    ttlMs,
  )
}
