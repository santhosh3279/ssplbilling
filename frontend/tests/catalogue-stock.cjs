const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync('src/pages/catalougepage.vue', 'utf8')
const handlers = new Map()
const timers = new Set()
const offer = { value: { items: [{ itemcode: 'A', available_stock: 1, stock_uom: 'Nos' }] } }
const socket = { on: (event, fn) => handlers.set(event, fn), off: event => handlers.delete(event) }
let stock = { A: 9 }, reject = false, resolvePending
const context = vm.createContext({
  offer, pageaddress: 'offers', console: { warn: () => {} },
  initFrappeSocket: async () => socket,
  frappeGet: async (method, args) => {
    assert.equal(method, 'ssplbilling.api.offer_api.get_offer_stock')
    assert.equal(args.pageaddress, 'offers')
    if (reject) throw new Error('offline')
    if (stock === null) return new Promise(resolve => { resolvePending = resolve })
    return stock
  },
  setTimeout: fn => { timers.add(fn); return fn }, clearTimeout: fn => timers.delete(fn),
  loadOffer: () => { throw new Error('Stock events must not reload prices or the catalogue') },
})
vm.runInContext(source.slice(source.indexOf('let _offerSocket = null'), source.indexOf('onMounted(() => {')), context)
;(async () => {
  vm.runInContext('setupOfferSocket()', context)
  await Promise.resolve()
  assert.ok(handlers.has('connect'))
  timers.clear()
  handlers.get('offer_page_update')({ type: 'stock', item_code: 'Other' })
  assert.equal(timers.size, 0)
  handlers.get('offer_page_update')({ type: 'stock', item_code: 'A' })
  handlers.get('offer_page_update')({ type: 'stock', item_code: 'A' })
  assert.equal(timers.size, 1, 'Stock events are debounced')
  await [...timers][0]()
  assert.equal(offer.value.items[0].available_stock, 9)
  stock = null
  const pending = vm.runInContext('refreshCatalogueStock()', context)
  stock = { A: 4 }
  await vm.runInContext('refreshCatalogueStock()', context)
  resolvePending({ A: 99 })
  await pending
  assert.equal(offer.value.items[0].available_stock, 4, 'Older responses cannot overwrite newer stock')
  reject = true
  await vm.runInContext('refreshCatalogueStock()', context)
  assert.equal(offer.value.items[0].available_stock, null)
  vm.runInContext('teardownOfferSocket()', context)
  assert.equal(handlers.size, 0)
  assert.equal(timers.size, 0)
  vm.runInContext('setupOfferSocket()', context)
  await Promise.resolve()
  assert.equal(handlers.size, 0, 'No subscriptions after unmount')
  console.log('Catalogue stock events, debounce, stale responses, errors, and cleanup passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
