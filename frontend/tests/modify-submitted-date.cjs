const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const { ref, computed } = require('vue')
const source = fs.readFileSync('src/pages/modifysubmitted.vue', 'utf8')
const script = source.match(/<script setup>([\s\S]*?)<\/script>/)[1]
let saved = []
let rejectSave = false
const context = vm.createContext({
  ref, computed, onMounted() {}, onUnmounted() {}, nextTick: async () => {},
  useRouter: () => ({ push() {} }),
  localStorage: { getItem: () => '0' }, // General date modification is disabled.
  modifySubmittedBillDate: async (...args) => {
    if (rejectSave) throw new Error('You do not have permission to modify Sales Invoice.')
    saved.push(args)
    return { message: 'Date updated' }
  },
})
vm.runInContext(script.replace(/^import .*\n/gm, ''), context)

;(async () => {
  assert.ok(!source.includes('canModifyDate'), 'Page access authorizes date editing independently of the general date flag')
  assert.ok(source.includes('v-model="newBillDate"'), 'Date input is still bound to the saved ISO date')
  vm.runInContext("invoice.value = { name: 'INV-1', doctype: 'Sales Invoice', posting_date: '2026-10-07' }; newBillDate.value = '2026-10-07'", context)
  vm.runInContext('adjustDate(1)', context)
  assert.equal(vm.runInContext('newBillDate.value', context), '2026-10-08')
  assert.equal(vm.runInContext('isDateChanged.value', context), true)
  await vm.runInContext('handleChangeDate()', context)
  assert.deepEqual(saved, [['INV-1', '2026-10-08', 'Sales Invoice']])
  assert.equal(vm.runInContext('invoice.value.posting_date', context), '2026-10-08')
  await vm.runInContext('handleChangeDate()', context)
  assert.equal(saved.length, 1, 'Unchanged dates are not submitted')

  vm.runInContext("newBillDate.value = '2026-10-09'; loadingUpdate.value = true", context)
  await vm.runInContext('handleChangeDate()', context)
  assert.equal(saved.length, 1, 'Duplicate saves are prevented')
  vm.runInContext('loadingUpdate.value = false; resetToOriginal()', context)
  assert.equal(vm.runInContext('newBillDate.value', context), '2026-10-08')
  vm.runInContext("setPreset('today')", context)
  assert.match(vm.runInContext('newBillDate.value', context), /^\d{4}-\d{2}-\d{2}$/)

  rejectSave = true
  vm.runInContext("newBillDate.value = '2026-10-09'", context)
  await vm.runInContext('handleChangeDate()', context)
  assert.match(vm.runInContext('fetchError.value', context), /permission/)
  assert.equal(vm.runInContext('invoice.value.posting_date', context), '2026-10-08', 'Server permission failures do not change the displayed saved date')
  assert.equal(vm.runInContext('loadingUpdate.value', context), false)
  console.log('Modify Submitted date entry: independent page permission, date adjustment, ISO save, duplicate guards and server errors passed')
})().catch(error => { console.error(error); process.exitCode = 1 })
