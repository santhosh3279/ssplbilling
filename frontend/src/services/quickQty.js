// Pending F6 quick-qty entries, shared between ItemSearch and the entry pages.
// Persisted so an accidental modal close doesn't lose typed quantities; the
// entry pages clear it whenever the bill they belong to is closed/reset.
//
// The order the operator typed in is kept separately: plain objects iterate
// integer-like keys (numeric item codes) in ascending numeric order, so the
// map alone cannot preserve entry order.

const STORAGE_KEY = 'sspl-quick-qty-map'
const ORDER_KEY = 'sspl-quick-qty-order'

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

export function loadQuickQtyOrder() {
  try {
    const raw = localStorage.getItem(ORDER_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch (e) {
    return []
  }
}

export function saveQuickQtyOrder(order) {
  try {
    localStorage.setItem(ORDER_KEY, JSON.stringify(order))
  } catch (e) {}
}

export function clearQuickQtyMap() {
  try {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(ORDER_KEY)
  } catch (e) {}
  window.dispatchEvent(new CustomEvent('wb-quick-qty-cleared'))
}
