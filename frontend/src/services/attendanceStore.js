// IndexedDB persistence for the eSSL attendance sync (EsslMachines page). The logs exist only
// here — the sync writes nothing server-side — and can run to tens of thousands of rows, which
// is why they are not kept in localStorage. Free of Vue/session imports (session.js clears it).

const DB_NAME = 'sspl_essl_attendance'
const STORE = 'syncs'
const KEY = 'latest'

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

/** { syncedAt, fromDate, total, machines, skippedInactive, logs } of the last sync, or null. */
export async function readAttendanceSync() {
  const db = await openDb()
  return (await done(db.transaction(STORE).objectStore(STORE).get(KEY))) || null
}

export async function writeAttendanceSync(payload) {
  const db = await openDb()
  await done(db.transaction(STORE, 'readwrite').objectStore(STORE).put({ ...payload, key: KEY }))
}

export async function clearAttendanceSync() {
  const db = await openDb()
  await done(db.transaction(STORE, 'readwrite').objectStore(STORE).clear())
}
