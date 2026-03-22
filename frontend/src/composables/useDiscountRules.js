import { ref, computed, watch } from 'vue'
import { useItemCache } from '../services/itemCache.js'

/**
 * Discount rule engine for SalesEntry.
 *
 * Call once per component instance:
 *   const { ignoreDiscountRule, makeRowKey, applyDiscountRuleForRow, reapplyAllDiscountRules }
 *     = useDiscountRules({ items, priceList, lookupItemInCache })
 *
 * items        – ref([])  the reactive item rows array (mutated in-place)
 * priceList    – ref('')  current price list name
 * lookupItemInCache – fn(item_code) → cached item or null
 */
export function useDiscountRules({ items, priceList, lookupItemInCache }) {
  const { discountRules } = useItemCache()

  const ignoreDiscountRule = ref(false)

  let _rowKeyCounter = 0
  function makeRowKey() { return ++_rowKeyCounter }

  let _applyingDiscount = false

  // ── helpers ──────────────────────────────────────────────────────────────

  function _isRuleActive(rule) {
    const today = new Date().toISOString().slice(0, 10)
    if (rule.start_date && today < rule.start_date) return false
    if (rule.end_date && today > rule.end_date) return false
    return true
  }

  function _findMatchingRule(itemCode, qty) {
    if (ignoreDiscountRule.value || !discountRules.value.length) return null
    for (const rule of discountRules.value) {
      if (!rule.enabled) continue
      if (!_isRuleActive(rule)) continue
      if (rule.price_list && rule.price_list !== priceList.value) continue
      if (rule.applies_to === 'Item Code') {
        const codes = (rule.items || []).map(i => i.item_code)
        if (!codes.includes(itemCode)) continue
      } else if (rule.applies_to === 'Product Group') {
        const cached = lookupItemInCache(itemCode)
        if (cached?.item_group && rule.product_group && cached.item_group !== rule.product_group) continue
      }
      return rule
    }
    return null
  }

  function _buildFreeRows(row, rule) {
    const cached = lookupItemInCache(row.item_code)
    const base = {
      item_code: row.item_code,
      item_name: row.item_name || cached?.item_name || row.item_code,
      uom: row.uom || cached?.uom || '',
      rate: 0, discount: 0, tax_rate: row.tax_rate,
      warehouse: row.warehouse, deleted: false, _is_free: true,
    }

    if (rule.discount_type === 'Product Discount') {
      const minQty = rule.min_quantity || 1
      if (row.qty < minQty) return { freeRows: [], discount: null }
      const freeBase = rule.free_quantity || 0
      const totalFree = rule.recursive ? Math.floor(row.qty / minQty) * freeBase : freeBase
      if (totalFree <= 0) return { freeRows: [], discount: null }
      return { freeRows: [{ ...base, qty: totalFree }], discount: null }
    }

    if (rule.discount_type === 'Percentage Discount') {
      const minQty = rule.min_quantity || 0
      if (minQty > 0 && row.qty < minQty) return { freeRows: [], discount: null }
      return { freeRows: [], discount: rule.percentage_discount || 0 }
    }

    if (rule.discount_type === 'Custom Logic') {
      const tier = (rule.custom_logic_rows || [])
        .filter(r => row.qty >= (r.min_quantity || 0))
        .sort((a, b) => b.min_quantity - a.min_quantity)[0]
      if (!tier) return { freeRows: [], discount: null }
      if (rule.custom_logic_type === 'Product') {
        const freeQty = tier.nos || 0
        if (freeQty <= 0) return { freeRows: [], discount: null }
        return { freeRows: [{ ...base, qty: freeQty }], discount: null }
      }
      if (rule.custom_logic_type === 'Percentage') {
        return { freeRows: [], discount: tier.percentage || 0 }
      }
    }
    return { freeRows: [], discount: null }
  }

  // ── public API ────────────────────────────────────────────────────────────

  function applyDiscountRuleForRow(rowIdx) {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    _applyingDiscount = true
    try {
      const row = items.value[rowIdx]
      if (!row || row._is_free || row.deleted) return
      const key = row._rowKey
      items.value = items.value.filter(r => !(r._is_free && r._free_parent_key === key))
      const newIdx = items.value.findIndex(r => r._rowKey === key)
      if (newIdx === -1) return
      const rule = _findMatchingRule(row.item_code, row.qty)
      if (!rule) return
      const { freeRows, discount } = _buildFreeRows(row, rule)
      if (discount !== null) row.discount = discount
      if (freeRows.length) {
        items.value.splice(newIdx + 1, 0, ...freeRows.map(r => ({ ...r, _free_parent_key: key })))
      }
    } finally {
      _applyingDiscount = false
    }
  }

  function reapplyAllDiscountRules() {
    if (_applyingDiscount) return
    _applyingDiscount = true
    try {
      items.value = items.value.filter(r => !r._is_free)
      const snap = [...items.value]
      let offset = 0
      for (let i = 0; i < snap.length; i++) {
        const row = snap[i]
        if (row.deleted || ignoreDiscountRule.value) continue
        const rule = _findMatchingRule(row.item_code, row.qty)
        if (!rule) continue
        const { freeRows, discount } = _buildFreeRows(row, rule)
        if (discount !== null) row.discount = discount
        if (freeRows.length) {
          items.value.splice(i + 1 + offset, 0, ...freeRows.map(r => ({ ...r, _free_parent_key: row._rowKey })))
          offset += freeRows.length
        }
      }
    } finally {
      _applyingDiscount = false
    }
  }

  // ── watchers ──────────────────────────────────────────────────────────────

  const _regularItemSig = computed(() =>
    items.value.filter(i => !i._is_free && !i.deleted).map(i => `${i._rowKey}:${i.qty}:${i.item_code}`).join('|')
  )
  let _discountTimer = null
  watch(_regularItemSig, () => {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    clearTimeout(_discountTimer)
    _discountTimer = setTimeout(reapplyAllDiscountRules, 350)
  })

  watch(ignoreDiscountRule, (ignored) => {
    _applyingDiscount = true
    items.value = items.value.filter(r => !r._is_free)
    _applyingDiscount = false
    if (!ignored) reapplyAllDiscountRules()
  })

  return {
    ignoreDiscountRule,
    makeRowKey,
    applyDiscountRuleForRow,
    reapplyAllDiscountRules,
  }
}
