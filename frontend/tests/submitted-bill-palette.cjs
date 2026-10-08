const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const vue = require('vue')
const cached = {
  'wb-series-sales-invoice': JSON.stringify(['SI-.YYYY.-', { prefix: 'SHARED-' }, { prefix: 3 }]),
  'wb-series-purchase-invoice': JSON.stringify(['PI-']),
  'wb-series-quotation': JSON.stringify(['Q-', 'SHARED-']),
  'wb-series-sales-order': JSON.stringify(['SO-']),
  'wb-series-purchase-order': JSON.stringify(['PO-']),
  'wb-company': 'Company A',
}
const localStorage = { getItem: key => cached[key] || null }
const context = vm.createContext({ ...vue, localStorage, console })
vm.runInContext(fs.readFileSync('src/services/submittedBillPalette.js', 'utf8').replace(/^export /gm, ''), context)
const run = code => vm.runInContext(code, context)
const plain = value => JSON.parse(JSON.stringify(value))
assert.deepEqual(plain(run('readBillSeries()')), ['PI-', 'PO-', 'Q-', 'SHARED-', 'SI-.YYYY.-', 'SO-'])
cached['wb-allowed-series'] = '["SI", "SO"]'
assert.deepEqual(plain(run('readBillSeries()')), ['SI-.YYYY.-', 'SO-'])
delete cached['wb-allowed-series']
cached['wb-series-purchase-order'] = 'invalid json'
assert.ok(!run('readBillSeries()').includes('PO-'))
cached['wb-series-purchase-order'] = '["PO-"]'
const params = plain(run("billListParams(BILL_TYPES[3], {query:'SO/2026/12', series:['SO-'], company:'Company A', start:50})"))
assert.deepEqual(params.filters, [['docstatus', '=', 1], ['company', '=', 'Company A'], ['naming_series', 'in', ['SO-']]])
assert.deepEqual(params.or_filters, [['name', 'like', '%SO%2026%12%'], ['customer_name', 'like', '%SO/2026/12%']])
assert.equal(params.limit_start, 50)
assert.ok(params.fields.includes('transaction_date'))
let calls = []
let staleResolve
let phase = 'initial'
context.defineProps = () => ({ busy: false })
context.defineEmits = () => {}
context.defineExpose = () => {}
context.onMounted = () => {}
context.onUnmounted = () => {}
context.watch = () => {}
context.frappeGet = async (method, params) => {
  calls.push({method, params})
  if (phase === 'stale') return new Promise(resolve => { staleResolve = resolve })
  if (phase === 'partial' && params.doctype === 'Purchase Invoice') throw Error('Permission denied')
  if (phase === 'initial' && params.doctype === 'Sales Invoice' && params.limit_start === 0) {
    return Array.from({length:50}, (_, i) => ({ name:`SI-${i}`, posting_date:'2026-10-08', customer_name:'Customer', grand_total:12.345 }))
  }
  return [{ name: phase === 'latest' ? 'LATEST' : 'SAME', [params.doctype.includes('Invoice') ? 'posting_date' : 'transaction_date']:'2026-10-07', grand_total:1 }]
}
const source = fs.readFileSync('src/components/SubmittedBillPalette.vue', 'utf8')
vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*\n/gm, ''), context)
;(async () => {
  await run('loadBills()')
  assert.equal(calls.length, 5)
  assert.ok(calls.every(call => call.method === 'frappe.client.get_list'), 'No series endpoint is called')
  assert.equal(run('bills.value.length'), 54, 'Same names in different document types remain separate')
  assert.deepEqual(plain(run('moreTypes.value')), ['Sales Invoice'])
  await run('loadBills(true)')
  assert.equal(calls[5].params.limit_start, 50)
  assert.equal(run('hasMore.value'), false)
  phase = 'partial'
  await run("selectedSeries.value='SO-'; searchText.value='Customer'; searchBills()")
  assert.equal(run('bills.value.length'), 4, 'A permission failure does not hide other types')
  assert.match(run('error.value'), /Purchase Invoice/)
  assert.ok(calls.slice(-5).every(call => call.params.filters.some(filter => filter[0] === 'naming_series' && filter[2][0] === 'SO-')))
  // Old responses must not overwrite a newer search.
  phase = 'stale'
  const old = run("moreTypes.value=['Sales Invoice']; loadBills(true)")
  phase = 'latest'
  await run('loadBills()')
  staleResolve([{name:'STALE', posting_date:'2026-10-09'}])
  await old
  assert.ok(run("bills.value.every(bill => bill.name === 'LATEST')"))
  const fetched = [], drafts = []
  let refreshed = 0
  const page = vm.createContext({
    ...vue, onMounted() {}, onUnmounted() {}, nextTick: async () => {},
    useRouter: () => ({push() {}}),
    fetchSubmittedInvoice: async (name, doctype) => { fetched.push([name, doctype]); return {name, doctype, posting_date:'2026-10-07'} },
    moveSubmittedToDraft: async (name, doctype) => { drafts.push([name, doctype]); return {draft_invoice:name} },
  })
  const pageSource = fs.readFileSync('src/pages/modifysubmitted.vue', 'utf8')
  vm.runInContext(pageSource.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*\n/gm, ''), page)
  page.refreshPalette = () => { refreshed++ }
  vm.runInContext('billPaletteRef.value = {refresh:refreshPalette}', page)
  for (const doctype of ['Sales Invoice', 'Purchase Invoice', 'Quotation', 'Sales Order', 'Purchase Order']) {
    page.selectedBill = {name:'SAME', doctype}
    await vm.runInContext('handlePaletteSelect(selectedBill)', page)
    assert.equal(vm.runInContext('invoice.value.doctype', page), doctype)
    vm.runInContext('showDraftConfirm.value = true', page)
    await vm.runInContext('handleMoveToDraft()', page)
    assert.equal(vm.runInContext('invoice.value', page), null)
  }
  assert.deepEqual(fetched, drafts, 'Document type is preserved for fetch and draft actions')
  assert.equal(refreshed, 5, 'Submitted list refreshes after each draft creation')
  console.log('Bill palette: five local caches, allowed series, malformed cache, search filters, paging, partial failures and stale responses passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
