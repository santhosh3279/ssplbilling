import { ref } from 'vue'
import { frappeGet } from '../api'

export function useAllowedSeries() {
  const allowedSeries = ref([])
  const loading = ref(false)

  async function fetchAllowedSeries(doctype) {
    loading.value = true
    try {
      // 1. Fetch backend allowed series (strictly filtered)
      const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', {
        doctype: doctype
      })
      let series = d.allowed_series || []

      // 2. Intersect with wb-allowed-series from localStorage
      const storedAllowedRaw = localStorage.getItem('wb-allowed-series')
      if (storedAllowedRaw) {
        try {
          const storedAllowed = JSON.parse(storedAllowedRaw)
          if (Array.isArray(storedAllowed) && storedAllowed.length > 0) {
            // Match DocType series if it starts with any allowed prefix
            series = series.filter(s => 
              storedAllowed.some(prefix => s.startsWith(prefix))
            )
          }
        } catch (e) {
          console.error('[useAllowedSeries] Failed to parse wb-allowed-series:', e)
        }
      }

      // Store the user allowed string for reference if needed
      if (d.user_allowed_string) {
        localStorage.setItem('wb-user-allowed-string', d.user_allowed_string)
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
