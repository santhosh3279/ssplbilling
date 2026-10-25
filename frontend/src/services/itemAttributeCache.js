import { ref } from 'vue'
import { frappeGet } from '../api.js'
import { readItemAttributeSnapshot, writeItemAttributeSnapshot } from './itemAttributeCacheStore'

// Item Attributes are a small master list, so every refresh refetches the whole set. The
// IndexedDB snapshot serves it instantly (and offline); item_attribute_update socket events
// (useItemSync) trigger a refresh whenever an attribute is saved or deleted.

const itemAttributes = ref([])
const loading = ref(false)
let snapshotLoaded = null
let inflight = null
let refreshedThisPage = false

function loadSnapshot() {
  if (!snapshotLoaded) {
    snapshotLoaded = readItemAttributeSnapshot()
      .then(snap => { if (snap?.items && !itemAttributes.value.length) itemAttributes.value = snap.items })
      .catch(e => console.warn('[itemAttributeCache] Snapshot unavailable:', e))
  }
  return snapshotLoaded
}

/** Fetch every enabled Item Attribute from the server and persist it; concurrent calls share one request. */
async function refreshItemAttributeCache() {
  if (inflight) return inflight
  loading.value = true
  inflight = (async () => {
    await loadSnapshot()
    try {
      const list = await frappeGet('ssplbilling.api.item_api.get_item_attributes') || []
      itemAttributes.value = list
      refreshedThisPage = true
      await writeItemAttributeSnapshot({ syncedAt: Date.now(), items: list })
        .catch(e => console.warn('[itemAttributeCache] Could not persist snapshot:', e))
    } catch (e) {
      // Keep serving the snapshot when the server is unreachable.
      console.warn('[itemAttributeCache] Refresh failed:', e)
    } finally {
      loading.value = false
      inflight = null
    }
    return itemAttributes.value
  })()
  return inflight
}

/** Refresh once per page load (catches changes made while no tab was listening); socket events cover the rest. */
function ensureItemAttributeCache() {
  return refreshedThisPage ? loadSnapshot() : refreshItemAttributeCache()
}

export function useItemAttributeCache() {
  loadSnapshot()
  return { itemAttributes, loading, refreshItemAttributeCache, ensureItemAttributeCache }
}
