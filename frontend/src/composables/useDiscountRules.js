import { ref, computed, watch } from 'vue'
import { useItemCache } from '../services/itemCache.js'

/**
 * Discount rule engine for SalesEntry.
 *
 * Call once per component instance:
 *   const { ignoreDiscountRule, makeRowKey, applyDiscountRuleForRow, reapplyAllDiscountRules }
 *     = useDiscountRules({ items, priceList, lookupItemInCache })
 *
 * items             – ref([])   reactive item rows array (mutated in-place)
 * priceList         – ref('')   current price list name
 * lookupItemInCache – fn(code)  returns cached item or null
 *
 * Row flags managed internally:
 *   _rowKey          – unique identity for regular rows (set by makeRowKey())
 *   _rule_discount   – last percentage set by a rule (null = not rule-applied)
 *   _is_free         – true on auto-inserted free rows
 *   _free_parent_key – _rowKey of the parent that generated this free row
 */
export function useDiscountRules({ items, priceList, lookupItemInCache }) {
  const { discountRules } = useItemCache()

  const ignoreDiscountRule = ref(false)

  let _rowKeyCounter = 0
  function makeRowKey() { return ++_rowKeyCounter }

  let _applyingDiscount = false

  // ── rule matching ─────────────────────────────────────────────────────────

  function _isRuleActive(rule) {
    const today = new Date().toISOString().slice(0, 10)
    if (rule.start_date && today < rule.start_date) return false
    if (rule.end_date   && today > rule.end_date)   return false
    return true
  }

  function _itemMatchesScope(rule, itemCode) {
    const code = (itemCode || '').toLowerCase()
    if (rule.discount_type === 'X to Y product discount') {
      const codes = (rule.x_to_y_table || []).map(i => (i.item_code || '').toLowerCase())
      return codes.includes(code)
    }
    if (rule.applies_to === 'Item Code') {
      const codes = (rule.items || []).map(i => (i.item_code || '').toLowerCase())
      return codes.includes(code)
    }
    if (rule.applies_to === 'Product Group') {
      const cached = lookupItemInCache(itemCode)
      if (!cached?.item_group || !rule.product_group) return false
      return cached.item_group.toLowerCase() === rule.product_group.toLowerCase()
    }
    return false
  }

  function _findMatchingRule(itemCode) {
    if (ignoreDiscountRule.value || !discountRules.value.length) return null
    for (const rule of discountRules.value) {
      if (!rule.enabled) continue
      if (!_isRuleActive(rule)) continue
      if (rule.price_list && rule.price_list !== priceList.value) continue
      if (!_itemMatchesScope(rule, itemCode)) continue
      return rule
    }
    return null
  }

  // ── discount computation ─────────────────────────────────────────────────
  //
  // Returns { freeRows: [], discount: number | null }
  //   discount = null  → no percentage action (don't touch disc column)
  //   discount = 0     → rule matched but qty below threshold → clear disc
  //   discount = N     → apply N% to disc column

  function _buildResult(row, rule) {
    const cached = lookupItemInCache(row.item_code)
    const freeBase = {
      item_code: row.item_code,
      item_name: row.item_name || cached?.item_name || row.item_code,
      uom:       row.uom      || cached?.uom       || '',
      rate: 0, discount: 0, tax_rate: row.tax_rate,
      warehouse: row.warehouse, deleted: false, _is_free: true,
    }

    // ── X to Y Product Discount ──────────────────────────────────────────────
    if (rule.discount_type === 'X to Y product discount') {
      const matchRow = (rule.x_to_y_table || []).find(
        r => (r.item_code || '').toLowerCase() === (row.item_code || '').toLowerCase()
      )
      if (!matchRow) return { freeRows: [], discount: null }

      const minQty = matchRow.min_quantity || 1
      if (row.qty < minQty) return { freeRows: [], discount: null }

      const freeQtyPerMin = matchRow.free_item_quantity || 1
      const totalFree = Math.floor(row.qty / minQty) * freeQtyPerMin
      if (totalFree <= 0) return { freeRows: [], discount: null }

      const yCached = lookupItemInCache(matchRow.free_item_code)

      const freeRowY = {
        item_code: matchRow.free_item_code,
        item_name: matchRow.free_item_name || yCached?.item_name || matchRow.free_item_code,
        uom: yCached?.uom || 'Nos',
        qty: totalFree,
        rate: matchRow.free_item_price || 0.0,
        discount: 0,
        tax_rate: yCached?.tax_rate || row.tax_rate,
        warehouse: row.warehouse,
        deleted: false,
        _is_free: true,
      }
      return { freeRows: [freeRowY], discount: null }
    }

    // ── Product Discount ────────────────────────────────────────────────────
    if (rule.discount_type === 'Product Discount') {
      const minQty = rule.min_quantity || 1
      if (row.qty < minQty) return { freeRows: [], discount: null }
      const freeBase_ = rule.free_quantity || 0
      const totalFree = rule.recursive
        ? Math.floor(row.qty / minQty) * freeBase_
        : freeBase_
      if (totalFree <= 0) return { freeRows: [], discount: null }
      return { freeRows: [{ ...freeBase, qty: totalFree }], discount: null }
    }

    // ── Percentage Discount ─────────────────────────────────────────────────
    // Uses custom_logic_rows for tiered thresholds when available;
    // falls back to the flat min_quantity + percentage_discount fields.
    if (rule.discount_type === 'Percentage Discount') {
      const rows = rule.custom_logic_rows || []
      if (rows.length) {
        // Tiered: find highest tier whose min_quantity ≤ row.qty
        const tier = rows
          .filter(r => row.qty >= (r.min_quantity || 0))
          .sort((a, b) => b.min_quantity - a.min_quantity)[0]
        if (!tier) return { freeRows: [], discount: 0 }  // below all tiers → clear
        return { freeRows: [], discount: tier.percentage || 0 }
      }
      // Flat single-threshold
      const minQty = rule.min_quantity || 0
      if (minQty > 0 && row.qty < minQty) return { freeRows: [], discount: 0 }  // below threshold → clear
      return { freeRows: [], discount: rule.percentage_discount || 0 }
    }

    // ── Custom Logic ────────────────────────────────────────────────────────
    if (rule.discount_type === 'Custom Logic') {
      const tier = (rule.custom_logic_rows || [])
        .filter(r => row.qty >= (r.min_quantity || 0))
        .sort((a, b) => b.min_quantity - a.min_quantity)[0]
      if (!tier) return { freeRows: [], discount: null }
      if (rule.custom_logic_type === 'Product') {
        const freeQty = tier.nos || 0
        if (freeQty <= 0) return { freeRows: [], discount: null }
        return { freeRows: [{ ...freeBase, qty: freeQty }], discount: null }
      }
      if (rule.custom_logic_type === 'Percentage') {
        return { freeRows: [], discount: tier.percentage || 0 }
      }
    }

    return { freeRows: [], discount: null }
  }

  // ── helpers: apply / clear percentage on a row ────────────────────────────

  function _applyDiscount(row, discount) {
    if (discount !== null) {
      row.discount = discount
      row._rule_discount = discount
    }
  }

  function _clearRuleDiscount(row) {
    if (row._rule_discount != null) {
      row.discount = 0
      row._rule_discount = null
    }
  }

  // ── public API ────────────────────────────────────────────────────────────

  function applyDiscountRuleForRow(rowIdx) {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    _applyingDiscount = true
    try {
      const row = items.value[rowIdx]
      if (!row || row._is_free || row.deleted) return
      const key = row._rowKey

      // Remove stale free rows for this parent
      items.value = items.value.filter(r => !(r._is_free && r._free_parent_key === key))
      const newIdx = items.value.findIndex(r => r._rowKey === key)
      if (newIdx === -1) return

      const rule = _findMatchingRule(row.item_code)
      if (!rule) {
        _clearRuleDiscount(row)
        return
      }

      const { freeRows, discount } = _buildResult(row, rule)
      _applyDiscount(row, discount)
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

        const rule = _findMatchingRule(row.item_code)
        if (!rule) {
          _clearRuleDiscount(row)
          continue
        }

        const { freeRows, discount } = _buildResult(row, rule)
        _applyDiscount(row, discount)
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

  // Re-apply when qty or item_code changes on regular rows
  const _regularItemSig = computed(() =>
    items.value
      .filter(i => !i._is_free && !i.deleted)
      .map(i => `${i._rowKey}:${i.qty}:${i.item_code}`)
      .join('|')
  )
  let _discountTimer = null
  watch(_regularItemSig, () => {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    clearTimeout(_discountTimer)
    _discountTimer = setTimeout(reapplyAllDiscountRules, 350)
  })

  // Re-apply when discount rules finish loading (async fetch)
  watch(discountRules, () => {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    clearTimeout(_discountTimer)
    _discountTimer = setTimeout(reapplyAllDiscountRules, 50)
  })

  // Re-apply when price list changes (billing settings load after mount)
  watch(priceList, () => {
    if (_applyingDiscount || ignoreDiscountRule.value) return
    clearTimeout(_discountTimer)
    _discountTimer = setTimeout(reapplyAllDiscountRules, 50)
  })

  watch(ignoreDiscountRule, (ignored) => {
    _applyingDiscount = true
    // Remove free rows; clear rule-applied discounts
    items.value = items.value.filter(r => !r._is_free)
    if (ignored) {
      items.value.forEach(r => _clearRuleDiscount(r))
    }
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
