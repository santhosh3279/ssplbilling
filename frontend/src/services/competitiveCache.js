import { ref } from 'vue'
import { frappeGet } from '../api.js'
import { readCompetitiveSnapshot, writeCompetitiveSnapshot } from './competitiveCacheStore'

// Competitive Items are a small master list, so every refresh refetches the whole set.
// The IndexedDB snapshot serves the list instantly (and offline) until that refresh lands.

const competitiveItems = ref([])
const loading = ref(false)
let byName = new Map()
let snapshotLoaded = null
let inflight = null

function setItems(list) {
  competitiveItems.value = list
  byName = new Map(list.map(c => [c.name, c]))
}

function loadSnapshot() {
  if (!snapshotLoaded) {
    snapshotLoaded = readCompetitiveSnapshot()
      .then(snap => { if (snap?.items && !competitiveItems.value.length) setItems(snap.items) })
      .catch(e => console.warn('[competitiveCache] Snapshot unavailable:', e))
  }
  return snapshotLoaded
}

/** Fetch every Competitive Item from the server and persist it; concurrent calls share one request. */
async function refreshCompetitiveCache() {
  if (inflight) return inflight
  loading.value = true
  inflight = (async () => {
    await loadSnapshot()
    try {
      const list = await frappeGet('ssplbilling.api.competitive_api.get_competitive_items_full') || []
      setItems(list)
      await writeCompetitiveSnapshot({ syncedAt: Date.now(), items: list })
        .catch(e => console.warn('[competitiveCache] Could not persist snapshot:', e))
    } catch (e) {
      // Keep serving the snapshot when the server is unreachable.
      console.warn('[competitiveCache] Refresh failed:', e)
    } finally {
      loading.value = false
      inflight = null
    }
    return competitiveItems.value
  })()
  return inflight
}

/** Cached Competitive Item by name, or null. */
function lookupCompetitiveItem(name) {
  return (name && byName.get(name)) || null
}

export function useCompetitiveCache() {
  loadSnapshot()
  return { competitiveItems, loading, refreshCompetitiveCache, lookupCompetitiveItem }
}
