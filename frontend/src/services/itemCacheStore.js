// IndexedDB persistence for the item cache plus the pure helpers used to merge a delta sync.
// Kept free of Vue/session imports so session.js can clear it on logout without an import cycle.

const DB_NAME = 'sspl_item_cache'
const STORE = 'snapshots'
// One snapshot per (user, company, search type, warehouse); each is ~10 MB of JSON.
const MAX_SNAPSHOTS = 4

let dbPromise = null

function openDb() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('IndexedDB unavailable'))
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      const store = req.result.createObjectStore(STORE, { keyPath: 'key' })
      store.createIndex('savedAt', 'savedAt')
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  }).catch((e) => {
    dbPromise = null
    throw e
  })
  return dbPromise
}

function done(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

/** Snapshot record: { key, schema, syncTs, draftCodes, priceList, savedAt, items (JSON string) } */
export async function readItemSnapshot(key) {
  const db = await openDb()
  return (await done(db.transaction(STORE).objectStore(STORE).get(key))) || null
}

export async function writeItemSnapshot(snapshot) {
  const db = await openDb()
  const tx = db.transaction(STORE, 'readwrite')
  const store = tx.objectStore(STORE)
  store.put(snapshot)
  // Evict least-recently-saved snapshots; a key cursor avoids loading the large item payloads.
  const entries = []
  const cursorReq = store.index('savedAt').openKeyCursor()
  cursorReq.onsuccess = () => {
    const cursor = cursorReq.result
    if (cursor) {
      entries.push(cursor.primaryKey)
      cursor.continue()
      return
    }
    for (const key of entries.slice(0, Math.max(0, entries.length - MAX_SNAPSHOTS))) store.delete(key)
  }
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
    tx.onabort = () => reject(tx.error)
  })
}

/** Remove every persisted snapshot (called on logout — snapshots hold all price lists). */
export async function clearItemSnapshots() {
  const db = await openDb()
  await done(db.transaction(STORE, 'readwrite').objectStore(STORE).clear())
}

/** Set each item's scalar `price` from its base rate in `priceList`, mirroring get_all_items_detailed. */
export function applyPriceList(list, priceList) {
  for (const i of list) {
    const plRate = (i.price_lists || []).find(p => p.name === priceList)
    i.price = plRate ? parseFloat(plRate.rate) || 0 : parseFloat(i.rate) || 0
  }
  return list
}

/**
 * Merge a delta sync into a cached item list: `changed` rows replace or insert (kept in item_name
 * order like patchItemInCache), `removed` codes are dropped. Returns a new array.
 */
export function mergeItemDelta(list, changed, removed) {
  const drop = new Set(removed)
  const index = new Map()
  const out = []
  for (const item of list) {
    if (drop.has(item.item_code)) continue
    index.set(item.item_code, out.length)
    out.push(item)
  }
  const inserts = []
  for (const item of changed) {
    const idx = index.get(item.item_code)
    if (idx !== undefined) out[idx] = item
    else inserts.push(item)
  }
  for (const item of inserts) {
    const insertAt = out.findIndex(i => (i.item_name || '') > (item.item_name || ''))
    if (insertAt === -1) out.push(item)
    else out.splice(insertAt, 0, item)
  }
  return out
}
