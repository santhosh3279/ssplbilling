// Attach server-awarded bonus quantities to the purchased cart lines.
// The preview and checkout remain authoritative for rule matching and prices.
export function addDiscountQuantities(items = []) {
  const lines = items.map(item => ({
    ...item,
    discount_qty: 0,
    total_qty: item.is_free_item ? item.qty : (item.requested_qty ?? item.qty),
  }))
  const purchased = new Map()

  for (const line of lines) {
    const key = `${line.pageaddress}\u0000${line.item_code}`
    if (!line.is_free_item) {
      purchased.set(key, line)
      continue
    }
    const sourceKey = `${line.pageaddress}\u0000${line.source_item_code || line.item_code}`
    const parent = purchased.get(sourceKey)
    if (!parent) continue
    parent.discount_qty += Number(line.qty) || 0
    parent.total_qty += Number(line.qty) || 0
  }

  return lines
}
