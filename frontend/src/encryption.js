const DEFAULT_CIPHER = ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']

export function getCipherMap() {
  try {
    const stored = localStorage.getItem('wb-cipher')
    if (stored) return JSON.parse(stored)
  } catch (e) {}
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
