const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const { ref, toRaw, isProxy } = require('vue')

// Loads services/itemCache.js (+ the real itemCacheStore merge helpers) in a sandbox with a fake
// get_items_sync endpoint, so the tests exercise the real module code.
function loadCache({ today = '2026-10-09' } = {}) {
  const storage = new Map([['wb-company', 'Co']])
  const calls = []
  const responders = []
  const ctx = vm.createContext({
    ref, toRaw, console: { log() {}, warn() {}, error() {} }, JSON, Number, String, Math, Object, Set, Map, Promise,
    setTimeout: (fn) => { fn(); return 0 }, requestIdleCallback: undefined, CustomEvent: class { constructor(t) { this.type = t } },
    window: { dispatchEvent() {} },
    localStorage: { getItem: k => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, v) },
    serverNow: () => new Date('2026-10-09T10:00:00Z'), serverToday: () => today,
    session: { user: ref('u@x') },
    frappeGet: async () => [],
    frappePost: (method, args) => {
      calls.push(args)
      const respond = responders.shift()
      return respond ? respond(args) : Promise.resolve(fullResponse(args))
    },
    readItemSnapshot: async () => null,
    writeItemSnapshot: async () => {},
  })
  const strip = src => src.replace(/^import [\s\S]*?from .*\n/gm, '').replace(/^export /gm, '')
  vm.runInContext(strip(fs.readFileSync('src/services/itemCacheStore.js', 'utf8')), ctx)
  vm.runInContext(strip(fs.readFileSync('src/services/itemCache.js', 'utf8')), ctx)
  return { ctx, calls, responders, storage, run: code => vm.runInContext(code, ctx) }
}

// Server-shaped rows for a scope: stock follows get_all_items_detailed's warehouse rules.
function row(code, warehouse) {
  const warehouse_stock = [{ warehouse: 'W1', qty: 10 }, { warehouse: 'W2', qty: 4 }]
  const scope = String(warehouse)
  const stock = scope === '' ? 14 : warehouse_stock.filter(w => w.warehouse === scope).reduce((s, w) => s + w.qty, 0)
  return {
    item_code: code, item_name: code, rate: 5, price: 5, valuation_rate: 1,
    price_lists: [{ name: 'Retail', rate: 7 }], uom_price_lists: {},
    warehouse_stock, stock, redis_stock: 0, redis_purchase_stock: 0,
  }
}
function fullResponse(args) {
  const items = ['A', 'B'].map(code => row(code, args.warehouse))
  return { full: true, items, removed: [], total: items.length, sync_ts: '2026-10-09 09:00:00', draft_codes: [] }
}

;(async () => {
  {
    const { calls, run } = loadCache()
    await run("refreshItemCache('Sales', null, 'W1')")
    await run("refreshItemCache('Purchase', null, 'W1')")
    assert.equal(calls.length, 2, 'Each new scope is synced once')
    assert.equal(calls[0].warehouse, 'W1')
    await run("refreshItemCache('Sales', 'Retail', 'W1')")
    await run("refreshItemCache('Purchase', null, 'W1')")
    await run("refreshItemCache('Sales', null, 'W1')")
    assert.equal(calls.length, 2, 'Switching back to a loaded scope (or price list) makes no request')
    assert.equal(run('lastParams.value.searchType'), 'Sales')
    assert.equal(run('items.value')[0].price, 5, 'Price list switches in memory')
    await run("refreshItemCache('Sales', null, 'W1', true)")
    assert.equal(calls.length, 3, 'A forced refresh still downloads')
    assert.equal(calls[2].since, null)
  }

  {
    const { calls, responders, run } = loadCache()
    let release
    responders.push(args => new Promise(resolve => { release = () => resolve(fullResponse(args)) }))
    const slow = run("refreshItemCache('Sales', null, 'W1')")
    await run("refreshItemCache('Sales', null, 'W2')")
    release()
    await slow
    assert.equal(run('lastParams.value.warehouse'), 'W2', 'A late sync for another scope never takes over')
    assert.equal(run('items.value')[0].stock, 4)
    await run("refreshItemCache('Sales', null, 'W1')")
    assert.equal(calls.length, 2, 'The late scope was kept and is reused without a request')
  }

  {
    const { run } = loadCache()
    await run("refreshItemCache('Sales', null, null)") // sent as "null": no warehouse matches
    await run("refreshItemCache('Sales', null, 'W1')")
    await run("refreshItemCache('Sales', null, '')")   // '' sums every warehouse
    assert.equal(run('items.value')[0].stock, 14)
    run(`updateItemStockInCache({ item_code: 'A', warehouse: 'W1', qty: 7, redis_stock: 9, redis_purchase_stock: 1,
      draft_qty: 3, draft_purchase_qty: 0, valuation_rate: 2.5 })`)
    const scoped = key => toRaw(run(`datasets.get(${JSON.stringify(key)}).list`)).find(i => i.item_code === 'A')
    const all = scoped('u@x|Co|Sales|'), w1 = scoped('u@x|Co|Sales|W1'), none = scoped('u@x|Co|Sales|null')
    assert.deepEqual([all.stock, all.redis_stock], [11, 9], 'All-warehouse scope sums every warehouse (event total without per-warehouse drafts)')
    assert.deepEqual([w1.stock, w1.redis_stock, w1.valuation_rate], [7, 3, 2.5], 'Warehouse scope uses its own figures')
    assert.deepEqual([none.stock, none.redis_stock], [0, 0], '"null" scope keeps 0 stock, as the server returns')
    run(`updateItemStockInCache({ item_code: 'A', warehouse: 'W2', qty: 1, redis_stock: 9, redis_purchase_stock: 1,
      draft_qty: 8, draft_purchase_qty: 0, valuation_rate: 9 })`)
    assert.deepEqual([w1.stock, w1.redis_stock, w1.valuation_rate], [7, 3, 2.5], 'Other-warehouse event leaves W1 figures alone')
    assert.equal(scoped('u@x|Co|Sales|W1').warehouse_stock.find(w => w.warehouse === 'W2').qty, 1)

    run("updateItemPriceInCache('B', 'Retail', 11, null)")
    for (const key of ['u@x|Co|Sales|', 'u@x|Co|Sales|W1', 'u@x|Co|Sales|null']) {
      const b = toRaw(run(`datasets.get(${JSON.stringify(key)}).list`)).find(i => i.item_code === 'B')
      assert.equal(b.price_lists[0].rate, 11, `Price change reaches inactive scope ${key}`)
    }
    run("patchItemInCache('A', null, 'u@x|Co|Sales|W1')")
    assert.equal(toRaw(run("datasets.get('u@x|Co|Sales|W1').list")).length, 1, 'Patches target the given scope')
    assert.equal(run('items.value').length, 2, 'Active scope untouched by another scope patch')
  }

  {
    const { calls, responders, run } = loadCache()
    await run("refreshItemCache('Sales', null, 'W1')")
    responders.push(() => Promise.resolve({ full: false, items: [{ ...row('A', 'W1'), stock: 99 }], removed: [], total: 2,
      sync_ts: '2026-10-09 09:30:00', draft_codes: ['A'] }))
    await run('reconcileItemDatasets()')
    assert.equal(calls.at(-1).since, '2026-10-09 09:00:00', 'Reconnect sends a delta from the last sync point')
    assert.equal(run('items.value')[0].stock, 99)
    const old = loadCache({ today: '2026-10-10' })
    await old.run("refreshItemCache('Sales', null, 'W1')")
    await old.run('reconcileItemDatasets()')
    assert.equal(old.calls.length, 1, 'A dataset from an earlier day is left for the next reload')
  }

  {
    const { run } = loadCache()
    for (const wh of ['W1', 'W2', 'W3', 'W4']) await run(`refreshItemCache('Sales', null, '${wh}')`)
    assert.equal(run('datasets.size'), 3, 'At most three scopes stay in memory')
    assert.ok(!run("datasets.has('u@x|Co|Sales|W1')"), 'Least recently used scope is dropped')
    assert.ok(!isProxy(run("datasets.get('u@x|Co|Sales|W4').list")))
  }
  console.log('Item cache datasets: no refetch on switch, late-sync guard, per-scope stock/price patches, reconnect delta and LRU passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
