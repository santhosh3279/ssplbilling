// Pending F6 quick-qty entries, shared between ItemSearch and the entry pages.
// Persisted so an accidental modal close doesn't lose typed quantities; the
// entry pages clear it whenever the bill they belong to is closed/reset.

const STORAGE_KEY = 'sspl-quick-qty-map'

export function loadQuickQtyMap() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch (e) {
    return {}
  }
}

export function saveQuickQtyMap(map) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch (e) {}
}

export function clearQuickQtyMap() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {}
  window.dispatchEvent(new CustomEvent('wb-quick-qty-cleared'))
}
