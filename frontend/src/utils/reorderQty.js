/**
 * Qty to order (stock UOM) from an item's levels; 0 means nothing to order.
 * - Safety stock set: order once stock is at or below it. Otherwise once stock is below max stock
 *   (or, with only a min order qty, once stock has run out).
 * - Fills up to max stock (safety stock when there is no max), never less than min order qty.
 *   A min order qty larger than the gap wins, even if that goes past max stock.
 */
export function reorderQty({ stock, safetyStock, maxStock, minOrderQty }) {
  const num = v => Number(v) || 0
  const have = num(stock)
  const safety = num(safetyStock)
  const max = num(maxStock)
  const moq = num(minOrderQty)
  const target = Math.max(max, safety)
  if (target <= 0 && moq <= 0) return 0

  const due = safety > 0 ? have <= safety : max > 0 ? have < max : have <= 0
  if (!due) return 0
  // Rounded first so float noise (10.000000001) does not add a whole unit
  const gap = Math.ceil(parseFloat((target - have).toFixed(3)))
  return Math.max(gap, moq, 0)
}
