import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { runInNewContext } from 'node:vm'

const component = await readFile(new URL('../src/components/CustomerCreator.vue', import.meta.url), 'utf8')
const submitSource = component.slice(component.indexOf('async function submit()'), component.indexOf('defineExpose'))
function formContext(overrides = {}) {
  const context = {
    saving: { value: false }, editLoading: { value: false },
    form: { value: { customer_name: 'New Customer', mobile: '9876543210', customer_group: 'Retail' } },
    props: { isEdit: false }, validate: () => true,
    emit() {}, alert() {}, ...overrides,
  }
  runInNewContext(submitSource, context)
  return context
}

test('repeated shortcut/button calls create once and remain locked after success', async () => {
  let release
  let calls = 0
  let saved = 0
  const response = new Promise(resolve => { release = resolve })
  const context = formContext({ createCustomer: () => { calls++; return response }, emit: () => { saved++ } })
  const first = context.submit()
  await context.submit()
  await context.submit()
  assert.equal(calls, 1)
  release({ name: 'CUSTOMER-1' })
  await first
  // Parent selection may still be waiting for its ledger refresh.
  await context.submit()
  assert.equal(calls, 1)
  assert.equal(saved, 1)
  assert.equal(context.saving.value, true)
})

test('a failed transaction unlocks the form for a corrected retry', async () => {
  let calls = 0
  const errors = []
  const context = formContext({
    createCustomer: async () => { if (++calls === 1) throw new Error('Invalid address'); return { name: 'CUSTOMER-1' } },
    alert: message => errors.push(message),
  })
  await context.submit()
  assert.equal(context.saving.value, false)
  assert.equal(errors.length, 1)
  await context.submit()
  assert.equal(calls, 2)
  assert.equal(context.saving.value, true)
})

test('edit loading and validation block writes; edit submissions are guarded too', async () => {
  let writes = 0
  const context = formContext({
    editLoading: { value: true }, props: { isEdit: true },
    updateCustomer: async () => { writes++; return { name: 'CUSTOMER-1' } },
  })
  await context.submit()
  assert.equal(writes, 0)
  context.editLoading.value = false
  context.validate = () => false
  await context.submit()
  assert.equal(writes, 0)
  context.validate = () => true
  await Promise.all([context.submit(), context.submit()])
  assert.equal(writes, 1)
})

test('customer API sends one atomic request and propagates its error', async () => {
  const source = (await readFile(new URL('../src/api/customer.js', import.meta.url), 'utf8'))
    .replace(/^import .*\n/gm, '').replaceAll('export ', '')
  const calls = []
  const data = { customer_name: 'New Customer', address_line1: 'Road', whatsapp: '9876543210', primary_party: 'SUPPLIER-1' }
  const context = { frappePost: async (...args) => { calls.push(args); return { name: 'CUSTOMER-1' } } }
  runInNewContext(source, context)
  assert.equal((await context.createCustomer(data)).name, 'CUSTOMER-1')
  assert.equal(calls.length, 1)
  assert.equal(calls[0][0], 'ssplbilling.api.customersearch_api.create_customer_full')
  assert.deepEqual(JSON.parse(calls[0][1].data), data)
  assert.equal(calls[0][2].silent, true)
  context.frappePost = async () => { throw new Error('Address denied') }
  await assert.rejects(context.createCustomer(data), /Address denied/)
})
