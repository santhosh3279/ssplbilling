// Collapse a template and its variants into one card: template image (else the first
// variant image), one barcode/price row per variant labelled with its size.
export function templateCard(item) {
  const variants = [...(item.variants || [])]
  if (!variants.length) return item
  const sortKey = v => (v.variant_attributes || []).map(a => a.sort)
  variants.sort((a, b) => {
    const ka = sortKey(a)
    const kb = sortKey(b)
    for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
      if ((ka[i] ?? 0) !== (kb[i] ?? 0)) return (ka[i] ?? 0) - (kb[i] ?? 0)
    }
    return 0
  })
  const offerVariant = variants.find(v => v.discount_desc)
  return {
    ...item,
    image: item.image || variants.find(v => v.image)?.image || null,
    discount_type: item.discount_type || offerVariant?.discount_type || null,
    discount_desc: item.discount_desc || offerVariant?.discount_desc || null,
    barcode_prices: variants.map(v => ({
      ...(v.barcode_prices?.[0] || { barcode: '', uom: v.stock_uom, prices: {} }),
      size: v.variant_label,
      key: v.itemcode,
    })),
  }
}

// Lowest and highest rate across a card's rows for one price list, for tiles too small for a table.
export function rateRange(item, priceList) {
  const rates = (item.barcode_prices || []).map(bp => bp.prices?.[priceList]).filter(r => r != null)
  if (!rates.length) return null
  return { min: Math.min(...rates), max: Math.max(...rates) }
}
