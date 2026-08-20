const DEFAULT_CIPHER = ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']

/** A usable cipher is exactly 10 non-empty strings, one per digit. */
function isWellFormed(parsed) {
  return (
    Array.isArray(parsed) &&
    parsed.length === 10 &&
    parsed.every(v => typeof v === 'string' && v)
  )
}

/**
 * Validate a raw cipher_map string before it is stored.
 * Blank is valid and means "encryption off"; anything else must be a
 * well-formed 10-entry JSON array. Used by the settings screen so a typo is
 * rejected loudly instead of silently falling back to the default cipher.
 */
export function isValidCipherMap(raw) {
  const text = (raw || '').trim()
  if (!text) return true
  try {
    const parsed = JSON.parse(text)
    if (Array.isArray(parsed) && parsed.length === 0) return true
    return isWellFormed(parsed)
  } catch (e) {
    return false
  }
}

/**
 * The active cipher, or null when encryption is switched off.
 *
 * Blank / absent / empty-array wb-cipher means "show plain rates". A malformed
 * map is NOT blank: it falls back to the default cipher, because a typo must
 * never expose real prices. Callers must handle null.
 */
export function getCipherMap() {
  let stored = null
  try {
    stored = localStorage.getItem('wb-cipher')
  } catch (e) {
    console.warn('[encryption] Failed to read wb-cipher:', e)
    return [...DEFAULT_CIPHER]
  }

  if (stored == null || stored.trim() === '') return null

  try {
    const parsed = JSON.parse(stored)
    if (Array.isArray(parsed) && parsed.length === 0) return null
    if (isWellFormed(parsed)) return parsed
    console.warn('[encryption] Invalid wb-cipher, using default cipher map')
  } catch (e) {
    console.warn('[encryption] Failed to parse wb-cipher:', e)
  }
  return [...DEFAULT_CIPHER]
}

export function encryptPrice(price) {
  if (price == null || isNaN(price)) return '—'
  const rounded = Math.round(Number(price)).toString()
  const cipher = getCipherMap()
  // No cipher configured: encryption is off, show the plain rate.
  if (!cipher) return rounded
  return rounded
    .split('')
    .map(ch => {
      const d = parseInt(ch)
      return isNaN(d) ? ch : (cipher[d] || '?')
    })
    .join('')
}

export function getDefaultTaxRate() {
  try {
    return JSON.parse(localStorage.getItem('wb-tax-rate') || '18')
  } catch (e) {
    return 18
  }
}

export function getDefaultWarehouse() {
  return localStorage.getItem('wb-warehouse') || ''
}

export function getDefaultPriceList() {
  return localStorage.getItem('wb-price-list') || 'Standard Selling'
}

export function getDefaultSeries() {
  return localStorage.getItem('wb-series') || 'ACC-SINV-.YYYY.-'
}

// Float precision synced from System Settings by getBillingSettings
export function getFloatPrecision() {
  const p = parseInt(localStorage.getItem('wb-precision'), 10)
  return isNaN(p) ? 3 : p
}
