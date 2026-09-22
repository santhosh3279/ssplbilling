const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')

const source = fs.readFileSync('src/pages/CatalogueCart.vue', 'utf8')
  .split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '')

const calls = []
const itemsMap = new Map([['offers:A', 5], ['offers:B', 2]])
const cartItems = {
  value: [
    { pageaddress: 'offers', item_code: 'A', qty: 5 },
    { pageaddress: 'offers', item_code: 'B', qty: 2 }
  ]
}

const context = vm.createContext({
  orderContext: { value: {} },
  orderParams: () => ({}),
  ref: value => ({ value }),
  computed: getter => ({ get value() { return getter() } }),
  watch: () => {},
  onMounted: fn => fn(),
  session: {
    isLoggedIn: { value: true },
    isWebsiteUser: { value: true },
    isSystemUser: { value: false },
    user: { value: 'test@example.com' },
    checkWebsiteUser: async () => true,
  },
  cartItems,
  clearCart: () => { cartItems.value = [] },
  setCartUser: () => {},
  setQuantity: (page, code, qty) => {
    if (qty <= 0) {
      itemsMap.delete(`${page}:${code}`)
      cartItems.value = cartItems.value.filter(i => !(i.pageaddress === page && i.item_code === code))
    } else {
      itemsMap.set(`${page}:${code}`, qty)
      const found = cartItems.value.find(i => i.pageaddress === page && i.item_code === code)
      if (found) found.qty = qty
    }
  },
  addDiscountQuantities: items => items,
  frappePost: async (method, params) => {
    calls.push({ method, params })
    return {
      customer_name: 'Customer 1',
      price_list: 'Standard Selling',
      items: cartItems.value.map(i => ({
        pageaddress: i.pageaddress,
        item_code: i.item_code,
        item_name: `Item ${i.item_code}`,
        requested_qty: i.qty,
        qty: i.qty,
        rate: 100,
        amount: i.qty * 100,
        is_free_item: false
      })),
      subtotal: cartItems.value.reduce((acc, i) => acc + i.qty * 100, 0),
      total: cartItems.value.reduce((acc, i) => acc + i.qty * 100, 0)
    }
  }
})

vm.runInContext(source, context)

;(async () => {
  // Wait for onMounted refreshPreview
  await new Promise(r => setTimeout(r, 10))

  assert.equal(vm.runInContext('cartItems.value.length', context), 2)
  assert.equal(vm.runInContext('lines.value.length', context), 2)

  // Test changeQuantity
  await vm.runInContext("changeQuantity({ pageaddress: 'offers', item_code: 'A', requested_qty: 5 }, 1)", context)
  assert.equal(itemsMap.get('offers:A'), 6, 'changeQuantity increases qty')

  // Test deleteItem
  await vm.runInContext("deleteItem({ pageaddress: 'offers', item_code: 'A' })", context)
  assert.equal(itemsMap.has('offers:A'), false, 'deleteItem deletes item A')
  assert.equal(vm.runInContext('cartItems.value.length', context), 1)
  assert.equal(vm.runInContext('lines.value[0].item_code', context), 'B')

  // Delete last item B
  await vm.runInContext("deleteItem({ pageaddress: 'offers', item_code: 'B' })", context)
  assert.equal(itemsMap.has('offers:B'), false, 'deleteItem deletes item B')
  assert.equal(vm.runInContext('cartItems.value.length', context), 0)
  assert.equal(vm.runInContext('lines.value.length', context), 0)

  console.log('Catalogue cart changeQuantity and deleteItem passed')
})().catch(error => {
  console.error(error)
  process.exitCode = 1
})
