// IndexedDB persistence for the Competitive Item cache (name + pricelist percentages).
// Its own database, so the item cache's schema never has to change for it. Kept free of
// Vue/session imports so session.js can clear it on logout without an import cycle.

const DB_NAME = 'sspl_competitive_cache'
const STORE = 'snapshots'
const KEY = 'competitive_items'

let dbPromise = null

function openDb() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('IndexedDB unavailable'))
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: 'key' })
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

/** Snapshot: { syncedAt, items: [{ name, modified, pricelist_percentages: [{ pricelist, percentage }] }] } */
export async function readCompetitiveSnapshot() {
  const db = await openDb()
  return (await done(db.transaction(STORE).objectStore(STORE).get(KEY))) || null
}

export async function writeCompetitiveSnapshot(snapshot) {
  const db = await openDb()
  await done(db.transaction(STORE, 'readwrite').objectStore(STORE).put({ ...snapshot, key: KEY }))
}

/** Remove the snapshot (called on logout). */
export async function clearCompetitiveSnapshot() {
  const db = await openDb()
  await done(db.transaction(STORE, 'readwrite').objectStore(STORE).clear())
}
