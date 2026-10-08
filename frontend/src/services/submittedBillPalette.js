// Series are read directly from the same local keys used by the invoice pages.
// This module deliberately never fetches naming series from the backend.
export const BILL_TYPES = [
  { doctype: 'Sales Invoice', date: 'posting_date', party: 'customer_name' },
  { doctype: 'Purchase Invoice', date: 'posting_date', party: 'supplier_name' },
  { doctype: 'Quotation', date: 'transaction_date', party: 'customer_name' },
  { doctype: 'Sales Order', date: 'transaction_date', party: 'customer_name' },
  { doctype: 'Purchase Order', date: 'transaction_date', party: 'supplier_name' },
]

function readArray(storage, key) {
  try {
    const value = JSON.parse(storage.getItem(key) || 'null')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

export function readBillSeries(storage = localStorage) {
  const allowed = readArray(storage, 'wb-allowed-series').filter(value => typeof value === 'string')
  const series = new Set()
  for (const { doctype } of BILL_TYPES) {
    const key = `wb-series-${doctype.toLowerCase().replace(/ /g, '-')}`
    for (const entry of readArray(storage, key)) {
      const prefix = typeof entry === 'string' ? entry : entry?.prefix
      if (typeof prefix === 'string' && prefix && (!allowed.length || allowed.some(value => prefix.startsWith(value)))) series.add(prefix)
    }
  }
  return [...series].sort((a, b) => a.localeCompare(b))
}

export function billListParams(type, { query = '', series = [], company = '', start = 0, limit = 50 } = {}) {
  const filters = [['docstatus', '=', 1]]
  if (company) filters.push(['company', '=', company])
  if (series.length) filters.push(['naming_series', 'in', series])
  const params = {
    doctype: type.doctype,
    fields: ['name', type.date, type.party, 'grand_total', 'naming_series'],
    filters,
    order_by: `${type.date} desc, name desc`,
    limit_start: start,
    limit_page_length: limit,
  }
  if (query.trim()) {
    const text = query.trim()
    const flexible = `%${(text.match(/[A-Za-z]+|\d+/g) || [text]).join('%')}%`
    params.or_filters = [['name', 'like', flexible], [type.party, 'like', `%${text}%`]]
  }
  return params
}

export function sortSubmittedBills(rows) {
  return [...rows].sort((a, b) => b.date.localeCompare(a.date) || b.name.localeCompare(a.name) || a.doctype.localeCompare(b.doctype))
}
