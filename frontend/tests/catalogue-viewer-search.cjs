const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync('src/pages/catalogueviewer.vue', 'utf8')
  .split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '')
const calls = [], watchers = [], unmount = []
const quantities = new Map()
let response = { items: [{ item_code: 'A', pageaddress: 'offers', order_rate: 12 }], has_more: true }
let resolvePending
const user = { value: true }
const context = vm.createContext({
  ref: value => ({ value }), computed: getter => ({ get value() { return getter() } }),
  watch: (sources, fn) => watchers.push(fn), onMounted: () => {}, onBeforeUnmount: fn => unmount.push(fn),
  useRouter: () => ({}), session: { isWebsiteUser: user, isLoggedIn: { value: true } },
  setTimeout: () => 1, clearTimeout: () => {},
  getQuantity: (page, code) => quantities.get(`${page}:${code}`) || 0,
  setQuantity: (page, code, qty) => quantities.set(`${page}:${code}`, qty),
  frappeGet: async (method, params) => {
    calls.push({ method, params })
    if (response === null) return new Promise(resolve => { resolvePending = resolve })
    return response
  },
})
vm.runInContext(source, context)
;(async () => {
  await vm.runInContext("itemQuery.value = 'soap'; searchItems()", context)
  assert.equal(calls[0].params.query, 'soap')
  assert.equal(vm.runInContext('searchResults.value.length', context), 1)
  vm.runInContext('changeCartQuantity(searchResults.value[0], 1)', context)
  assert.equal(quantities.get('offers:A'), 1)
  await vm.runInContext('searchItems(true)', context)
  assert.equal(calls[1].params.start, 1)
  response = null
  const pending = vm.runInContext('searchItems()', context)
  vm.runInContext("itemQuery.value = ''", context)
  watchers[0]()
  resolvePending({ items: [{ item_code: 'old' }], has_more: false })
  await pending
  assert.equal(vm.runInContext('searchResults.value.length', context), 0)
  assert.equal(vm.runInContext('searchLoading.value', context), false)
  user.value = false
  vm.runInContext("changeCartQuantity({pageaddress: 'offers', item_code: 'A', order_rate: 12}, 1)", context)
  assert.equal(quantities.get('offers:A'), 1, 'Guests cannot add items')
  user.value = true
  vm.runInContext("changeCartQuantity({pageaddress: 'offers', item_code: 'A', order_rate: null}, 1)", context)
  assert.equal(quantities.get('offers:A'), 1, 'Unpriced items cannot be added')
  unmount[0]()
  console.log('Viewer search, pagination, stale responses, and cart controls passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
