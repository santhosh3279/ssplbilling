const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync('src/pages/CashflowReport.vue', 'utf8')
  .split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '')
const calls = []
const context = vm.createContext({
  ref: value => ({ value }), computed: getter => ({ get value() { return getter() } }),
  useRouter: () => ({}), onMounted: () => {}, onUnmounted: () => {},
  localStorage: { getItem: () => 'Company' },
  getCashflowReport: async (...args) => {
    calls.push(args)
    const rows = args[3]
      ? [{ account: 'Till', account_type: 'Cash', inflow: 150, outflow: 40 },
         { account: 'Bank', account_type: 'Bank', inflow: 500, outflow: 20 }]
      : [{ account: 'Till', inflow: 10, outflow: 5 }]
    return { summary: rows, breakdown: rows }
  },
})
vm.runInContext(source, context)
;(async () => {
  await vm.runInContext("fromDate.value = '2026-09-01'; toDate.value = '2026-09-22'; fetchData()", context)
  assert.equal(vm.runInContext('totals.value.cash_balance', context), 110)
  assert.equal(vm.runInContext('totals.value.balance', context), 590)
  assert.equal(vm.runInContext('reportSummary.value.length', context), 5)
  assert.match(vm.runInContext('reportSummary.value[4].description', context), /2026-09-22/)
  assert.deepEqual(calls[1], ['1000-01-01', '2026-09-22', 'Company', true])
  vm.runInContext("expandedFlow.value = 'cash_balance'", context)
  assert.equal(vm.runInContext('flowAccounts.value.length', context), 1)
  assert.equal(vm.runInContext('flowAccounts.value[0].account', context), 'Till')
  assert.equal(vm.runInContext('flowAccounts.value[0].cash_balance', context), 110)
  await vm.runInContext("fromDate.value = '2026-09-15'; fetchData()", context)
  assert.equal(vm.runInContext('totals.value.cash_balance', context), 110)
  console.log('Cash-only total, bank exclusion, To date, drilldown, and From-date independence passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
