const DEFAULT_CIPHER = ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']

/** Sentinel for an unusable cipher, distinct from null (= encryption off). */
const INVALID = 'invalid'

/** A usable cipher is exactly 10 non-empty strings, one per digit. */
function isWellFormed(parsed) {
  return (
    Array.isArray(parsed) &&
    parsed.length === 10 &&
    parsed.every(v => typeof v === 'string' && v)
  )
}

/**
 * Turn a raw cipher_map value into a 10-entry array.
 *
 * The stored format is plain text: one replacement character per digit 0-9, in
 * order (e.g. "KLMNOPQRST"). Returns null when encryption is off (blank), or
 * the string 'invalid' when the value is unusable.
 *
 * Values written by older builds were JSON arrays, and they can still be sitting
 * in a browser's localStorage or in an un-migrated site, so those are still
 * accepted on read.
 */
function parseCipher(raw) {
  const text = (raw || '').trim()
  if (!text) return null

  if (text.startsWith('[')) {
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed) && parsed.length === 0) return null
      return isWellFormed(parsed) ? parsed : INVALID
    } catch (e) {
      return INVALID
    }
  }

  // Spread rather than split('') so a multi-byte character counts as one slot.
  const chars = [...text]
  if (chars.length !== 10) return INVALID
  if (chars.some(ch => !ch.trim())) return INVALID
  return chars
}

/**
 * Validate a raw cipher_map string before it is stored.
 * Blank is valid and means "encryption off"; anything else must be exactly 10
 * non-blank characters. Used by the settings screen so a typo is rejected
 * loudly instead of silently falling back to the default cipher.
 */
export function isValidCipherMap(raw) {
  return parseCipher(raw) !== INVALID
}

/**
 * The active cipher, or null when encryption is switched off.
 *
 * Blank wb-cipher means "show plain rates". A malformed map is NOT blank: it
 * falls back to the default cipher, because a typo must never expose real
 * prices. Callers must handle null.
 */
export function getCipherMap() {
  let stored = null
  try {
    stored = localStorage.getItem('wb-cipher')
  } catch (e) {
    console.warn('[encryption] Failed to read wb-cipher:', e)
    return [...DEFAULT_CIPHER]
  }

  const parsed = parseCipher(stored)
  if (parsed === INVALID) {
    console.warn('[encryption] Invalid wb-cipher, using default cipher map')
    return [...DEFAULT_CIPHER]
  }
  return parsed
}

export function encryptPrice(price) {
  if (price == null || isNaN(price)) return '—'
  const n = Number(price)
  const cipher = getCipherMap()
  // No cipher configured: encryption is off, so show the real rate. Rounding to
  // an integer was harmless while the output was letters, but would silently
  // turn 26.788 into 27 once the digits are visible. Matches ItemSearch's own
  // plain-rate formatting.
  if (!cipher) return n % 1 === 0 ? String(n) : n.toFixed(getFloatPrecision())
  const rounded = Math.round(n).toString()
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
