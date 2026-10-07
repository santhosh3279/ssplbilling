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

  const modal = fs.readFileSync('src/components/CustomerSearchModal.vue', 'utf8')
  const pollStart = modal.indexOf('function stopBalanceRefresh()')
  const pollEnd = modal.indexOf('\n}', pollStart) + 2
  const watchStart = modal.indexOf('watch([() => props.show, liveBalances]')
  const watchEnd = modal.indexOf('}, { immediate: true })', watchStart) + '}, { immediate: true })'.length
  let callback
  let refreshes = 0
  const intervals = new Set()
  const pollContext = vm.createContext({
    balanceRefreshTimer: null,
    props: { show: false }, liveBalances: { value: false }, syncLoading: { value: false },
    document: { visibilityState: 'visible' },
    localStorage: { setItem() {} },
    preloadLedger: force => { assert.equal(force, true); refreshes++ },
    setInterval: (fn, ms) => { assert.equal(ms, 30000); intervals.add(fn); return fn },
    clearInterval: fn => intervals.delete(fn),
    watch: (_, fn) => { callback = fn },
  })
  vm.runInContext(modal.slice(pollStart, pollEnd) + '\n' + modal.slice(watchStart, watchEnd), pollContext)
  callback([true, true])
  assert.equal(refreshes, 1)
  assert.equal(intervals.size, 1)
  const tick = [...intervals][0]
  tick()
  assert.equal(refreshes, 2)
  pollContext.syncLoading.value = true
  tick()
  assert.equal(refreshes, 2, 'Busy requests are not overlapped')
  pollContext.syncLoading.value = false
  pollContext.document.visibilityState = 'hidden'
  tick()
  assert.equal(refreshes, 2, 'Hidden tabs do not poll')
  callback([false, true])
  assert.equal(intervals.size, 0, 'Closing modal stops polling')
  callback([true, true])
  callback([true, false])
  assert.equal(intervals.size, 0, 'Disabling live balances stops polling')
  assert.ok(modal.includes('onUnmounted(() => {\n  stopBalanceRefresh()'))
  console.log('Live option: immediate refresh, interval, busy/hidden guards and close/disable cleanup passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
