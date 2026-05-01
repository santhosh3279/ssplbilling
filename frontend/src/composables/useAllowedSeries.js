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
