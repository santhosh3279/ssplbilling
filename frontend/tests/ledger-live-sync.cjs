const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')

const handlers = new Map()
const timers = new Set()
const events = []
let calls = 0
let pendingResolve = null
let hold = false
let fail = false
const socket = {
  on(event, handler) { assert.ok(!handlers.has(event)); handlers.set(event, handler) },
  off(event, handler) { assert.equal(handlers.get(event), handler); handlers.delete(event) },
}
const context = vm.createContext({
  getFrappeSocket: () => socket,
  refreshLedgerCache: async force => {
    assert.equal(force, true)
    calls++
    if (fail) throw new Error('offline')
    if (hold) await new Promise(resolve => { pendingResolve = resolve })
  },
  setTimeout: fn => { timers.add(fn); return fn },
  clearTimeout: fn => timers.delete(fn),
  console: { warn() {} },
  window: { dispatchEvent: event => events.push(event.type) },
  CustomEvent: class { constructor(type) { this.type = type } },
})
const source = fs.readFileSync('src/composables/useLedgerSync.js', 'utf8')
vm.runInContext(source.replace(/^import .*\n/gm, '').replace(/export function /g, 'function '), context)
async function flush() {
  assert.equal(timers.size, 1)
  const timer = [...timers][0]
  timers.delete(timer)
  await timer()
}

;(async () => {
  vm.runInContext('initLedgerSync(); initLedgerSync()', context)
  assert.equal(handlers.size, 3, 'Subscriptions are not duplicated')
  await flush()
  assert.equal(calls, 1, 'Initial subscription reconciles persisted balances')

  // The all-company event value must never directly replace scoped balances.
  handlers.get('ledger_balance_update')({ name: 'Customer A', balance: 999999 })
  handlers.get('ledger_balance_update')({ name: 'Customer B', balance: -100 })
  handlers.get('customer_update')({ name: 'Customer A' })
  await flush()
  assert.equal(calls, 2, 'A burst triggers one company-filtered refresh')
  assert.equal(events.length, 2)

  hold = true
  handlers.get('ledger_balance_update')({ name: 'Customer A' })
  const running = flush()
  handlers.get('ledger_balance_update')({ name: 'Customer B' })
  assert.equal(timers.size, 0, 'No overlapping refresh')
  hold = false
  pendingResolve()
  await running
  await flush()
  assert.equal(calls, 4, 'Changes during a request trigger a follow-up refresh')

  handlers.get('connect')()
  await flush()
  assert.equal(calls, 5, 'Reconnect catches missed events')
  fail = true
  handlers.get('ledger_balance_update')({ name: 'Customer A' })
  await flush()
  assert.equal(events.length, 5, 'Failed refresh is not announced as successful')
  fail = false
  handlers.get('connect')()
  await flush()
  assert.equal(calls, 7, 'Refresh recovers after failure')

  handlers.get('ledger_balance_update')({ name: 'Customer A' })
  vm.runInContext('destroyLedgerSync()', context)
  assert.equal(handlers.size, 0)
  assert.equal(timers.size, 0)
  console.log('Ledger sync: scoped refresh, debounce, in-flight changes, reconnect, errors and cleanup passed')

  const { ref, computed } = require('vue')
  const storage = new Map([
    ['wb-company', 'Company A'], ['ae-alternative_company', 'Company B'],
  ])
  let apiCalls = 0
  let resolveOld
  let latest = [{ name: 'Customer A', type: 'Customer', balance: 120, alternative_balance: 80 }]
  const cache = vm.createContext({
    ref, console, Date, JSON, Number, setTimeout, clearTimeout,
    localStorage: {
      getItem: key => storage.get(key) || null,
      setItem: (key, value) => storage.set(key, value),
    },
    frappeGet: async (method, args) => {
      assert.equal(method, 'ssplbilling.api.customersearch_api.get_all_ledgers')
      assert.equal(args.company, storage.get('wb-company'))
      assert.equal(args.alternative_company, storage.get('ae-alternative_company'))
      if (++apiCalls === 1) return new Promise(resolve => { resolveOld = resolve })
      return latest
    },
  })
  const cacheSource = fs.readFileSync('src/services/ledgerCache.js', 'utf8')
  vm.runInContext(cacheSource.replace(/^import .*\n/gm, '').replace(/export /g, ''), cache)
  const older = vm.runInContext('refreshLedgerCache()', cache)
  const forced = vm.runInContext('refreshLedgerCache(true)', cache)
  resolveOld([{ name: 'Customer A', type: 'Customer', balance: 10, alternative_balance: 5 }])
  await Promise.all([older, forced])
  assert.equal(apiCalls, 2, 'Forced socket refresh fetches new data after an older in-flight request')

  const modal = fs.readFileSync('src/components/CustomerSearchModal.vue', 'utf8')
  assert.ok(!modal.includes('liveBalances'), 'No live balance checkbox or polling remains')
  const displayStart = modal.indexOf('const isSameCompany = computed(')
  const displayEnd = modal.indexOf('// The backend has already applied', displayStart)
  const display = vm.createContext({
    computed,
    allLedgers: vm.runInContext('ledgers', cache),
    cacheContext: vm.runInContext('cacheContext', cache),
    localStorage: cache.localStorage,
  })
  vm.runInContext(modal.slice(displayStart, displayEnd), display)
  const getBalance = vm.runInContext('getDisplayBalance', display)
  const supplied = { name: 'Customer A', type: 'Customer', balance: 10, alternative_balance: 5 }
  assert.equal(getBalance(supplied), 120, 'Balance column uses refreshed company balance, even with supplied result lists')
  latest = [{ name: 'Customer A', type: 'Customer', balance: 240, alternative_balance: 160 }]
  await vm.runInContext('refreshLedgerCache(true)', cache)
  assert.equal(getBalance(supplied), 240, 'Balance column reacts to subsequent cache replacements')
  storage.set('wb-company', 'Company B')
  latest = [{ name: 'Customer A', type: 'Customer', balance: 240, alternative_balance: 160 }]
  await vm.runInContext('refreshLedgerCache(true)', cache)
  assert.equal(getBalance(supplied), 160, 'Alternative company balance responds to context changes')
  assert.equal(getBalance({ name: 'Uncached', type: 'Customer', alternative_balance: 42 }), 42)
  assert.equal(getBalance({ name: 'Customer A', type: 'Supplier', alternative_balance: 7 }), 7, 'Party types do not collide')
  console.log('Balance column: forced refresh race, company filters, supplied lists, reactive updates and alternative company passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
