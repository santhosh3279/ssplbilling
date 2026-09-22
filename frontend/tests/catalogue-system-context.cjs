const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const storage = new Map()
const systemUser = { value: true }
const ctx = vm.createContext({
  ref: value => ({ value }), session: { isSystemUser: systemUser },
  sessionStorage: { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) },
})
vm.runInContext(fs.readFileSync('src/services/catalogueOrderContext.js', 'utf8').replace(/^import .*$/gm, '').replace(/^export /gm, ''), ctx)
vm.runInContext("setOrderUser('staff'); setOrderContext({ customer: 'C1', customer_name: 'Customer', price_list: 'Wholesale' })", ctx)
assert.equal(vm.runInContext('orderParams().customer', ctx), 'C1')
assert.equal(vm.runInContext('orderParams().price_list', ctx), 'Wholesale')
vm.runInContext("setOrderUser('other')", ctx)
assert.equal(vm.runInContext('orderParams().customer', ctx), '')
vm.runInContext("setOrderUser('staff')", ctx)
assert.equal(vm.runInContext('orderParams().customer', ctx), 'C1')
systemUser.value = false
assert.equal(vm.runInContext('Object.keys(orderParams()).length', ctx), 0, 'Website users do not submit a party override')

const page = fs.readFileSync('src/pages/catalougepage.vue', 'utf8')
const priceFunction = page.slice(page.indexOf('function displayPrice(price)'), page.indexOf('async function handleWebsiteLogin'))
vm.runInContext("const catalogueUser = { value: true }; const rupeeFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }); const getCipherMap = () => 'cipher'; const encryptPrice = () => 'encrypted'", ctx)
vm.runInContext(priceFunction, ctx)
assert.notEqual(vm.runInContext('displayPrice(123)', ctx), 'encrypted')
vm.runInContext('catalogueUser.value = false', ctx)
assert.equal(vm.runInContext('displayPrice(123)', ctx), 'encrypted')

const calls = [], callbacks = []
const party = { value: { customer: 'C1', price_list: 'Wholesale' } }
const checkout = vm.createContext({
  ref: value => ({ value }), watch: (source, fn) => callbacks.push(fn), onMounted: () => {},
  session: { isSystemUser: { value: true } }, orderContext: party,
  orderParams: () => ({ ...party.value }), cartItems: { value: [{ item_code: 'A', qty: 1 }] },
  clearCart: () => {}, frappePost: async (method, args) => {
    calls.push({ method, args })
    return method.endsWith('place_order') ? { order_name: 'SO-1' } : { customer: args.customer, price_list: args.price_list, items: [] }
  },
})
vm.runInContext(fs.readFileSync('src/pages/CatalogueCheckout.vue', 'utf8').split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, ''), checkout)
;(async () => {
  await vm.runInContext('refreshPreview()', checkout)
  assert.equal(calls[0].args.price_list, 'Wholesale')
  party.value = { customer: 'C2', price_list: 'Retail' }
  await vm.runInContext('refreshPreview()', checkout)
  await vm.runInContext('placeOrder()', checkout)
  assert.equal(calls[2].args.customer, 'C2')
  assert.equal(calls[2].args.price_list, 'Retail')
  assert.equal(vm.runInContext('orderName.value', checkout), 'SO-1')
  console.log('Per-user order context, unencrypted staff rates, and checkout party/pricelist propagation passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
