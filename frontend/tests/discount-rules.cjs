// Run with: node --test tests/discount-rules.cjs
const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const path = require('node:path')

const source = fs.readFileSync(path.join(__dirname, '../src/composables/useDiscountRules.js'), 'utf8')
  .replace(/^import .*$/gm, '')
  .replace('export function useDiscountRules', 'function useDiscountRules')

for (const [type, extra, qty, paid, free, discount] of [
  ['Percentage Discount', { min_quantity: 1, percentage_discount: 10 }, 12, 12, 0, 10],
  ['Percentage Discount', { custom_logic_rows: [{ min_quantity: 5, percentage: 15 }] }, 12, 12, 0, 15],
  ['Custom Logic', { custom_logic_type: 'Percentage', custom_logic_rows: [{ min_quantity: 5, percentage: 20 }] }, 12, 12, 0, 20],
  ['Product Discount', { min_quantity: 5, free_quantity: 1, recursive: 1 }, 12, 10, 2, 0],
  ['X to Y product discount', { x_to_y_table: [{ item_code: 'A', min_quantity: 5, free_item_code: 'B', free_item_quantity: 1 }] }, 12, 12, 2, 0],
  ['Custom Logic', { custom_logic_type: 'Product', custom_logic_rows: [{ min_quantity: 5, nos: 2 }] }, 12, 12, 2, 0],
]) {
  test(`${type} ${JSON.stringify(extra)} stays stable across repeated bill edits`, () => {
    const rule = { enabled: 1, discount_type: type, applies_to: 'Item Code', items: [{ item_code: 'A' }], ...extra }
    const context = vm.createContext({
      ref: value => ({ value }), computed: fn => ({ get value() { return fn() } }),
      watch: () => {}, useItemCache: () => ({ discountRules: { value: [rule] } }),
    })
    vm.runInContext(source, context)
    const items = { value: [{ _rowKey: 1, item_code: 'A', qty, rate: 90, discount: 0 }] }
    const engine = context.useDiscountRules({ items, priceList: { value: '' }, lookupItemInCache: () => null })
    for (let edit = 0; edit < 10; edit++) {
      engine.reapplyAllDiscountRules()
      assert.equal(items.value[0].rate, 90)
      assert.equal(items.value[0].qty, paid)
      assert.equal(items.value[0].discount, discount)
      assert.equal(items.value.filter(row => row._is_free).reduce((sum, row) => sum + row.qty, 0), free)
    }
  })
}
