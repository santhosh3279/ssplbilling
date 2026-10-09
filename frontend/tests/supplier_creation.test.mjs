import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { runInNewContext } from 'node:vm'

const component = await readFile(new URL('../src/components/SupplierCreator.vue', import.meta.url), 'utf8')
const submitSource = component.slice(component.indexOf('async function submit()'), component.indexOf('defineExpose'))
function formContext(overrides = {}) {
  const context = {
    saving: { value: false }, loading: { value: false },
    form: { supplier_name: 'New Supplier', supplier_group: 'Retail' },
    props: { isEdit: false }, validate: () => true,
    emit() {}, alert() {}, ...overrides,
  }
  runInNewContext(submitSource, context)
  return context
}

test('repeated supplier shortcuts create once and stay locked while parent selection finishes', async () => {
  let release
  let calls = 0
  let saved = 0
  const response = new Promise(resolve => { release = resolve })
  const context = formContext({ createSupplier: () => { calls++; return response }, emit: () => { saved++ } })
  const first = context.submit()
  await context.submit()
  assert.equal(calls, 1)
  release({ name: 'SUPPLIER-1' })
  await first
  await context.submit()
  assert.equal(calls, 1)
  assert.equal(saved, 1)
  assert.equal(context.saving.value, true)
})

test('a failed supplier transaction unlocks for a corrected retry', async () => {
  let calls = 0
  const errors = []
  const context = formContext({
    createSupplier: async () => { if (++calls === 1) throw new Error('Invalid address'); return { name: 'SUPPLIER-1' } },
    alert: message => errors.push(message),
  })
  await context.submit()
  assert.equal(context.saving.value, false)
  assert.equal(errors.length, 1)
  await context.submit()
  assert.equal(calls, 2)
  assert.equal(context.saving.value, true)
})

test('supplier loading and validation block writes; successful edits also stay locked', async () => {
  let writes = 0
  const context = formContext({
    loading: { value: true }, props: { isEdit: true },
    updateSupplier: async () => { writes++; return { name: 'SUPPLIER-1' } },
  })
  await context.submit()
  assert.equal(writes, 0)
  context.loading.value = false
  context.validate = () => false
  await context.submit()
  assert.equal(writes, 0)
  context.validate = () => true
  await context.submit()
  await context.submit()
  assert.equal(writes, 1)
})

test('supplier API uses one server creation request and propagates its failure', async () => {
  const source = (await readFile(new URL('../src/api/supplier.js', import.meta.url), 'utf8'))
    .replace(/^import .*\n/gm, '').replaceAll('export ', '')
  const calls = []
  const data = { supplier_name: 'New Supplier', address_line1: 'Road', whatsapp: '9876543210', primary_party: 'CUSTOMER-1' }
  const context = { frappePost: async (...args) => { calls.push(args); return { name: 'SUPPLIER-1' } } }
  runInNewContext(source, context)
  assert.equal((await context.createSupplier(data)).name, 'SUPPLIER-1')
  assert.equal(calls.length, 1)
  assert.equal(calls[0][0], 'ssplbilling.api.supplier_creator_api.create_supplier_full')
  assert.deepEqual(JSON.parse(calls[0][1].data), data)
  context.frappePost = async () => { throw new Error('Address denied') }
  await assert.rejects(context.createSupplier(data), /Address denied/)
})
