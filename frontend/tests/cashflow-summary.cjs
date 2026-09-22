const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync('src/pages/CashflowReport.vue', 'utf8')
  .split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '')
const calls = []
const detailCalls = []
const fixedToday = '2026-09-30'
const context = vm.createContext({
  Date: class extends Date { constructor(...args) { super(...(args.length ? args : [fixedToday + 'T12:00:00Z'])) } },
  getCashflowDetails: async args => { detailCalls.push(args); return { groups: [], entries: [] } },
  ref: value => ({ value }), computed: getter => ({ get value() { return getter() } }),
  useRouter: () => ({}), onMounted: () => {}, onUnmounted: () => {},
  localStorage: { getItem: () => 'Company' },
  getCashflowReport: async (...args) => {
    calls.push(args)
    const rows = args[3] && args[1] === fixedToday
      ? [{ account: 'Bank', account_type: 'Bank', inflow: 900, outflow: 20 }]
      : args[3]
      ? [{ account: 'Till', account_type: 'Cash', inflow: 150, outflow: 40 },
         { account: 'Bank', account_type: 'Bank', inflow: 500, outflow: 20 }]
      : [{ account: 'Till', inflow: 10, outflow: 5 }]
    return { summary: rows, breakdown: rows }
  },
})
vm.runInContext(source, context)
;(async () => {
  await vm.runInContext("fromDate.value = '2026-09-01'; toDate.value = '2026-09-22'; fetchData()", context)
  assert.equal(vm.runInContext('totals.value.cash_balance', context), 590)
  assert.equal(vm.runInContext('totals.value.balance', context), 880)
  assert.equal(vm.runInContext('reportSummary.value.length', context), 5)
  assert.match(vm.runInContext('reportSummary.value[4].description', context), /2026-09-22/)
  assert.deepEqual(calls[0], ['1000-01-01', '2026-09-22', 'Company', true])
  assert.deepEqual(calls[1], ['1000-01-01', fixedToday, 'Company', true])
  assert.match(vm.runInContext('reportSummary.value[3].description', context), /2026-09-30/)
  vm.runInContext("expandedFlow.value = 'cash_balance'", context)
  assert.equal(vm.runInContext('flowAccounts.value.length', context), 2)
  assert.equal(vm.runInContext('flowAccounts.value[0].account', context), 'Bank')
  assert.equal(vm.runInContext('flowAccounts.value[0].cash_balance', context), 480)
  await vm.runInContext("fromDate.value = '2026-09-15'; fetchData()", context)
  assert.equal(vm.runInContext('totals.value.cash_balance', context), 590)
  await vm.runInContext("expandedFlow.value = 'balance'; loadDetails('Bank')", context)
  assert.equal(detailCalls[0].from_date, fixedToday)
  assert.equal(detailCalls[0].to_date, fixedToday)
  await vm.runInContext("expandedFlow.value = 'cash_balance'; loadDetails('Bank')", context)
  assert.equal(detailCalls[1].to_date, '2026-09-22')
  calls.length = 0
  await vm.runInContext("toDate.value = '2026-09-30'; fetchData()", context)
  assert.equal(calls.length, 2)
  assert.equal(vm.runInContext('totals.value.cash_balance', context), 880)
  console.log('Combined cash and bank total, To date, drilldown, and From-date independence passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
