const DEFAULT_CIPHER = ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']

export function getCipherMap() {
  try {
    const stored = localStorage.getItem('wb-cipher')
    if (stored) {
      const parsed = JSON.parse(stored)
      // A malformed map must not fall through: a short array yields '?' chars and
      // a non-array throws downstream, both of which leak or corrupt the price.
      if (
        Array.isArray(parsed) &&
        parsed.length === 10 &&
        parsed.every(v => typeof v === 'string' && v)
      ) {
        return parsed
      }
      console.warn('[encryption] Invalid wb-cipher, using default cipher map')
    }
  } catch (e) {
    console.warn('[encryption] Failed to parse wb-cipher:', e)
  }
  return [...DEFAULT_CIPHER]
}

export function encryptPrice(price) {
  if (price == null || isNaN(price)) return '—'
  const cipher = getCipherMap()
  return Math.round(Number(price))
    .toString()
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
