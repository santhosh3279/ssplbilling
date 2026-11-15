import { ref } from 'vue'
import { frappeGet } from '../api'
import { getSeriesForDoctype, SERIES_DOCTYPES } from '../services/seriesCache.js'

// A series is allowed only when its prefix (the part before the first '.') is exactly
// one of the user's allowed prefixes: "PO" allows "PO.#####" but not "POR.#####".
export function seriesPrefix(series) {
  return (series || '').split('.')[0].trim().toUpperCase()
}

const ADMIN_USERS = ['Administrator', 'admin']

// Writes wb-allowed-series (the prefixes useAllowedSeries filters by) for `targetUser` — the
// inherited user when an admin previews another user — from the SSPL Billing Settings payload.
// Same rules as dashboard_api.get_allowed_series: Administrator / an "ALL" entry get every billing
// series, a user without a row or with a blank list gets none, otherwise exact prefix matches.
// With nothing allowed the key is removed, so the server (which gets the user too) decides.
export function writeAllowedSeriesPrefixes(settings, targetUser) {
  if (!settings) return
  // Stored as written in the series (other pages read the key too); compared case-insensitively
  const allPrefixes = (settings.billing_series || []).map(bs => (bs.series || '').split('.')[0].trim()).filter(Boolean)
  const userRow = (settings.user_series || []).find(r => r.user === targetUser)
  const entries = (userRow?.allowed_series || '').split(',').map(seriesPrefix).filter(Boolean)

  let prefixes
  if (ADMIN_USERS.includes(targetUser) || entries.includes('ALL')) prefixes = allPrefixes
  else prefixes = allPrefixes.filter(p => entries.includes(seriesPrefix(p)))
  prefixes = [...new Set(prefixes)]

  try {
    if (prefixes.length) localStorage.setItem('wb-allowed-series', JSON.stringify(prefixes))
    else localStorage.removeItem('wb-allowed-series')
  } catch { /* storage blocked */ }
}

function isAllowedSeries(series, allowedPrefixes) {
  const prefix = seriesPrefix(series)
  return allowedPrefixes.some(p => seriesPrefix(p) === prefix)
}

export function useAllowedSeries() {
  const allowedSeries = ref([])
  const loading = ref(false)

  function readAllowedPrefixes() {
    try {
      const parsed = JSON.parse(localStorage.getItem('wb-allowed-series') || 'null')
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : null
    } catch (e) {
      console.error('[useAllowedSeries] Failed to parse wb-allowed-series:', e)
      return null
    }
  }

  async function fetchAllowedSeries(doctype, user = null) {
    loading.value = true
    try {
      const allowedPrefixes = readAllowedPrefixes()

      // 1. Cache-first: intersect the cached doctype series with the user's
      //    allowed prefixes — no per-page server call when both are available.
      //    Without wb-allowed-series we cannot filter locally, so fall through
      //    to the backend which enforces user permissions itself.
      if (allowedPrefixes && SERIES_DOCTYPES.includes(doctype)) {
        const cached = await getSeriesForDoctype(doctype)
        const series = cached
          .map(s => (typeof s === 'string' ? s : s?.prefix || ''))
          .filter(s => isAllowedSeries(s, allowedPrefixes))
        if (series.length > 0) {
          allowedSeries.value = series
          return series
        }
      }

      // 2. Fallback: fetch backend allowed series (strictly filtered)
      // The inherited user's series when an admin previews another user (the server only
      // honours `user` for Administrator / admin and ignores it for everyone else).
      const params = { doctype: doctype }
      const target = user || localStorage.getItem('wb-inherited-user')
      if (target) params.user = target
      const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', params)
      let series = d.allowed_series || []

      if (allowedPrefixes) {
        series = series.filter(s => isAllowedSeries(s, allowedPrefixes))
      }

      allowedSeries.value = series
      return series
    } catch (e) {
      console.error('[useAllowedSeries] Fetch failed:', e)
      return []
    } finally {
      loading.value = false
    }
  }

  return {
    allowedSeries,
    loading,
    fetchAllowedSeries
  }
}
