import { ref } from 'vue'
import { frappeGet } from '../api'

export function useAllowedSeries() {
  const allowedSeries = ref([])
  const loading = ref(false)

  async function fetchAllowedSeries(doctype) {
    loading.value = true
    try {
      // 1. Fetch backend allowed series (fallback/legacy)
      const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', {
        doctype: doctype
      })
      let series = d.allowed_series || []

      // 2. Perform intersection of wb-allowed-series and wb-series-{doctype}
      const dtKey = `wb-series-${doctype.toLowerCase().replace(/ /g, '-')}`
      const storedAllowed = localStorage.getItem('wb-allowed-series')
      const storedDtSeries = localStorage.getItem(dtKey)

      if (storedAllowed && storedDtSeries) {
        try {
          const allowedPrefixes = JSON.parse(storedAllowed)
          const dtSeries = JSON.parse(storedDtSeries)

          if (Array.isArray(allowedPrefixes) && Array.isArray(dtSeries)) {
            series = dtSeries.filter(s => {
              const prefix = (s || '').split('.')[0]
              return allowedPrefixes.includes(prefix)
            })
          }
        } catch (e) {
          console.warn('[useAllowedSeries] Intersection failed:', e)
        }
      } else if (storedAllowed) {
        try {
          const allowedPrefixes = JSON.parse(storedAllowed)
          if (Array.isArray(allowedPrefixes) && allowedPrefixes.length) {
            series = series.filter(s => {
              const prefix = (s || '').split('.')[0]
              return allowedPrefixes.includes(prefix)
            })
          }
        } catch (e) {
          console.warn('[useAllowedSeries] Failed to parse wb-allowed-series:', e)
        }
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
