const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')

const handlers = new Map()
const timers = new Map()
const events = []
const docListeners = new Map()
const document = {
  visibilityState: 'visible',
  addEventListener: (type, fn) => docListeners.set(type, fn),
  removeEventListener: (type, fn) => { if (docListeners.get(type) === fn) docListeners.delete(type) },
}
let calls = 0
let pendingResolve = null
let hold = false
let fail = false
const pushes = []
const patches = []
const socket = {
  connected: false,
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
  applyLedgerBalancePush: payload => { pushes.push(payload); return true },
  patchLedgerInCache: (name, data) => patches.push([name, data]),
  frappeGet: async (method, args) => {
    assert.equal(method, 'ssplbilling.api.customersearch_api.get_single_ledger')
    return args.party_name === 'Gone' ? null : { name: args.party_name, label: 'New', balance: 999, activity: 9 }
  },
  setTimeout: (fn, ms) => { timers.set(fn, ms); return fn },
  clearTimeout: fn => timers.delete(fn),
  Math: Object.assign(Object.create(Math), { random: () => 0.5 }),
  console: { warn() {} },
  document,
  window: { dispatchEvent: event => events.push(event.type) },
  CustomEvent: class { constructor(type) { this.type = type } },
})
const source = fs.readFileSync('src/composables/useLedgerSync.js', 'utf8')
vm.runInContext(source.replace(/^import .*\n/gm, '').replace(/export function /g, 'function '), context)
async function flush(expectedDelay) {
  assert.equal(timers.size, 1)
  const [timer, delay] = [...timers][0]
  if (expectedDelay !== undefined) assert.equal(delay, expectedDelay)
  timers.delete(timer)
  await timer()
}
const tick = () => new Promise(resolve => setImmediate(resolve))

;(async () => {
  vm.runInContext('initLedgerSync(); initLedgerSync()', context)
  assert.equal(handlers.size, 3, 'Subscriptions are not duplicated')
  await flush(0)
  assert.equal(calls, 1, 'Initial subscription reconciles persisted balances')

  handlers.get('connect')()
  assert.equal(timers.size, 0, 'The initial connect does not trigger a second full refresh')

  // Submits are patched from the pushed per-company balances, never by a full refresh.
  handlers.get('ledger_balances')({ ts: 1, ledgers: [{ name: 'Customer A', balances: { 'Company A': 5 } }] })
  handlers.get('ledger_balances')({ ts: 2, ledgers: [{ name: 'Customer B', balances: {} }] })
  assert.equal(pushes.length, 2)
  assert.equal(timers.size, 0, 'Balance pushes do not start a full refresh')
  assert.equal(calls, 1)

  handlers.get('customer_update')({ name: 'Customer A' })
  handlers.get('customer_update')({ name: 'Gone' })
  await tick()
  assert.deepEqual(JSON.parse(JSON.stringify(patches)), [['Customer A', { name: 'Customer A', label: 'New' }], ['Gone', null]],
    'Customer patches drop unscoped balance/activity and remove deleted customers')
  assert.equal(timers.size, 0, 'Customer edits do not start a full refresh')

  // Reconnects spread their full refresh over the window; hidden tabs wait until visible.
  handlers.get('connect')()
  await flush(15000)
  assert.equal(calls, 2, 'Reconnect catches missed pushes')
  document.visibilityState = 'hidden'
  handlers.get('connect')()
  assert.equal(timers.size, 0, 'Hidden tab defers its reconcile')
  document.visibilityState = 'visible'
  docListeners.get('visibilitychange')()
  await flush(2500)
  assert.equal(calls, 3)

  hold = true
  handlers.get('connect')()
  const running = flush()
  handlers.get('connect')()
  assert.equal(timers.size, 0, 'No overlapping refresh')
  hold = false
  pendingResolve()
  await running
  await flush()
  assert.equal(calls, 5, 'Reconnects during a request trigger a follow-up refresh')

  fail = true
  const before = events.length
  handlers.get('connect')()
  await flush()
  assert.equal(events.length, before, 'Failed refresh is not announced as successful')
  fail = false

  vm.runInContext('destroyLedgerSync()', context)
  assert.equal(handlers.size, 0)
  assert.equal(timers.size, 0)
  assert.equal(docListeners.size, 0)
  console.log('Ledger sync: pushed balances, customer patches, spread reconnects, hidden tabs, errors and cleanup passed')

  const { ref, computed } = require('vue')
  const storage = new Map([
    ['wb-company', 'Company A'], ['ae-alternative_company', 'Company B'],
  ])
  let now = 1000
  let apiCalls = 0
  let resolveOld
  let latest = [{ name: 'Customer A', type: 'Customer', balance: 120, alternative_balance: 80 }]
  const cache = vm.createContext({
    ref, console, Date, JSON, Number, Object, setTimeout, clearTimeout,
    serverNow: () => new Date(now * 1000),
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

  // Pushed balances: scoped to the active/alternative company, ordered, and not lost to an older refresh.
  storage.set('wb-company', 'Company A')
  latest = [{ name: 'Customer A', type: 'Customer', balance: 1, alternative_balance: 1 }]
  await vm.runInContext('refreshLedgerCache(true)', cache)
  const row = () => vm.runInContext('ledgers.value', cache).find(l => l.name === 'Customer A')
  const push = payload => vm.runInContext('applyLedgerBalancePush', cache)(payload)
  assert.equal(push({ ts: 1001, ledgers: [{ name: 'Customer A', balances: { 'Company A': 300, 'Company B': 70 }, last_invoice_date: '2026-10-09' }] }), true)
  assert.deepEqual([row().balance, row().alternative_balance, row().last_invoice_date], [300, 70, '2026-10-09'])
  assert.equal(push({ ts: 1000.5, ledgers: [{ name: 'Customer A', balances: { 'Company A': 1 } }] }), false, 'Older push is ignored')
  assert.equal(row().balance, 300)
  assert.equal(push({ ts: 1002, ledgers: [{ name: 'Customer A', balances: {} }] }), true)
  assert.deepEqual([row().balance, row().alternative_balance], [0, 0], 'Fully cancelled ledger drops to zero')
  assert.equal(push({ ts: 1003, ledgers: [{ name: 'Not Cached', balances: { 'Company A': 9 } }] }), false)

  // A full refresh that started before the push must not restore the older balance.
  now = 1010
  let releaseRefresh
  latest = new Promise(resolve => { releaseRefresh = resolve })
  const slow = vm.runInContext('refreshLedgerCache(true)', cache)
  await tick()
  push({ ts: 1011, ledgers: [{ name: 'Customer A', balances: { 'Company A': 555 } }] })
  releaseRefresh([{ name: 'Customer A', type: 'Customer', balance: 400, alternative_balance: 1 }])
  await slow
  assert.equal(row().balance, 555, 'Push newer than the refresh start survives the refresh')
  now = 1020
  latest = [{ name: 'Customer A', type: 'Customer', balance: 600, alternative_balance: 1 }]
  await vm.runInContext('refreshLedgerCache(true)', cache)
  assert.equal(row().balance, 600, 'A refresh started after the push wins')

  storage.set('wb-company', '')
  storage.set('ae-alternative_company', '')
  latest = [{ name: 'Customer A', type: 'Customer', balance: 0 }]
  await vm.runInContext('refreshLedgerCache(true)', cache)
  push({ ts: 1030, ledgers: [{ name: 'Customer A', balances: { 'Company A': 10, 'Company B': 5 } }] })
  assert.equal(row().balance, 15, 'No company selected sums every company')
  console.log('Balance pushes: company scoping, ordering, cancellation, refresh race and all-company sum passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
