const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ExcelJS = require('exceljs')
const source = fs.readFileSync('src/pages/CashflowReport.vue', 'utf8')
  .split('<script setup>')[1].split('</script>')[0].replace(/^import .*$/gm, '')
let blob, clicks = 0, fail = false
const calls = []
const context = vm.createContext({
  // ExcelJS checks instanceof Array; normalize arrays crossing the VM boundary.
  ExcelJS: { Workbook: class extends ExcelJS.Workbook {
    addWorksheet(...args) {
      const sheet = super.addWorksheet(...args)
      const addRow = sheet.addRow.bind(sheet)
      sheet.addRow = values => addRow(Array.from(values))
      return sheet
    }
  } }, Blob, setTimeout: () => {},
  ref: value => ({ value }), computed: getter => ({ get value() { return getter() } }),
  useRouter: () => ({}), onMounted: () => {}, onUnmounted: () => {},
  localStorage: { getItem: () => 'Company' },
  URL: { createObjectURL: value => { blob = value; return 'blob:test' } },
  document: { createElement: () => ({ click: () => { clicks++ } }) },
  getCashflowDetails: async args => {
    calls.push(args)
    if (fail) throw new Error('Voucher request failed')
    const amount = args.flow === 'inflow' ? 10 : 4
    return { entries: [{ posting_date: '2026-09-01', voucher_no: `${args.flow}-${args.start}`, voucher_type: 'Payment Entry', debit: amount, credit: amount, counterpart_account: 'Party Account' }], has_more: args.start === 0 }
  },
})
vm.runInContext(source, context)
vm.runInContext(`loadedFilters.value = { company: 'Company', from: '2026-09-01', to: '2026-09-22', currentDate: '2026-09-30' }; particulars.value = [{ account: 'Bank', inflow: 20, outflow: 8, balance: 12, cash_balance: 12 }]; totals.value = { inflow: 20, outflow: 8, netflow: 12, balance: 12, cash_balance: 12 }`, context)
;(async () => {
  await vm.runInContext('exportToExcel()', context)
  assert.equal(clicks, 1)
  assert.equal(calls.length, 4)
  assert.ok(calls.every(call => call.from_date === '2026-09-01' && call.to_date === '2026-09-22'))
  const workbook = new ExcelJS.Workbook()
  await workbook.xlsx.load(await blob.arrayBuffer())
  assert.deepEqual(workbook.worksheets.map(sheet => sheet.name), ['Cash Flow', 'Particulars', 'Inflow Vouchers', 'Outflow Vouchers'])
  for (const [name, total] of [['Inflow Vouchers', 20], ['Outflow Vouchers', 8]]) {
    const sheet = workbook.getWorksheet(name)
    assert.equal(sheet.rowCount, 6)
    assert.equal(sheet.getCell('D4').value, 'Bank')
    assert.equal(sheet.getCell('E4').value, 'Party Account')
    assert.equal(sheet.getCell('I6').value, total)
  }
  fail = true
  await vm.runInContext('exportToExcel()', context)
  assert.equal(clicks, 1, 'Failed exports must not download a partial workbook')
  assert.equal(vm.runInContext('exporting.value', context), false)
  assert.equal(vm.runInContext('error.value', context), '')
  assert.equal(vm.runInContext('exportError.value', context), 'Voucher request failed')
  console.log('Voucher worksheets, pagination, amounts, dates, and export failure handling passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
