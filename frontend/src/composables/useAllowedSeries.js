import { ref } from 'vue'
import { frappeGet } from '../api'
import { getSeriesForDoctype, SERIES_DOCTYPES } from '../services/seriesCache.js'

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
          .filter(s => allowedPrefixes.some(prefix => s.startsWith(prefix)))
        if (series.length > 0) {
          allowedSeries.value = series
          return series
        }
      }

      // 2. Fallback: fetch backend allowed series (strictly filtered)
      const params = { doctype: doctype }
      if (user) params.user = user
      const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', params)
      let series = d.allowed_series || []

      if (allowedPrefixes) {
        // Match DocType series if it starts with any allowed prefix
        series = series.filter(s =>
          allowedPrefixes.some(prefix => s.startsWith(prefix))
        )
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
