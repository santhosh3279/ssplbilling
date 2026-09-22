<template>
  <section v-if="session.isSystemUser.value" class="m-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-[var(--color-text)] space-y-3">
    <h2 class="font-bold">Sales Order customer and price list</h2>
    <p v-if="orderContext.customer" class="text-sm">Selected: {{ orderContext.customer_name || orderContext.customer }} · {{ orderContext.price_list }}</p>
    <form class="flex flex-wrap items-end gap-3" @submit.prevent="apply">
      <label class="flex-1 min-w-[180px] text-sm">Find customer
        <input v-model="query" type="search" placeholder="Customer name or code" class="mt-1 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2" />
      </label>
      <label class="flex-1 min-w-[180px] text-sm">Customer / Party
        <select v-model="customer" required class="mt-1 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2" @change="chooseCustomer">
          <option value="">Select customer</option>
          <option v-if="customer && !customers.some(row => row.name === customer)" :value="customer">{{ customer }}</option>
          <option v-for="row in customers" :key="row.name" :value="row.name">{{ row.customer_name }} ({{ row.name }})</option>
        </select>
      </label>
      <label class="flex-1 min-w-[180px] text-sm">Price list
        <select v-model="priceList" required class="mt-1 w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2">
          <option value="">Select price list</option>
          <option v-for="row in priceLists" :key="row.name" :value="row.name">{{ row.name }}</option>
        </select>
      </label>
      <button type="submit" :disabled="saving || loading" class="rounded bg-indigo-600 px-4 py-2 font-bold text-white disabled:opacity-50">{{ saving ? 'Applying…' : 'Apply' }}</button>
    </form>
    <p v-if="loading" role="status" class="text-sm">Loading customers and price lists…</p>
    <p v-if="error" role="alert" class="text-sm text-red-600">{{ error }}</p>
  </section>
</template>
<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { frappeGet, frappePost } from '../api.js'
import { session } from '../session.js'
import { orderContext, setOrderContext } from '../services/catalogueOrderContext.js'
const query = ref('')
const customer = ref(orderContext.value.customer)
const priceList = ref(orderContext.value.price_list)
const customers = ref([])
const priceLists = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
let timer, request = 0
watch(orderContext, value => { customer.value = value.customer; priceList.value = value.price_list })
watch([query, session.isSystemUser], () => {
  clearTimeout(timer)
  const id = ++request
  loading.value = false
  if (!session.isSystemUser.value) return
  loading.value = true
  timer = setTimeout(async () => {
    try {
      const result = await frappeGet('ssplbilling.api.catalogue_order_api.get_order_options', { query: query.value })
      if (id !== request) return
      customers.value = result.customers
      priceLists.value = result.price_lists
      error.value = ''
    } catch (err) {
      if (id === request) error.value = err.message || 'Could not load customers.'
    } finally {
      if (id === request) loading.value = false
    }
  }, 250)
}, { immediate: true })
function chooseCustomer() {
  priceList.value = customers.value.find(row => row.name === customer.value)?.default_price_list || ''
}
async function apply() {
  if (saving.value) return
  saving.value = true
  error.value = ''
  try {
    const result = await frappePost('ssplbilling.api.catalogue_order_api.get_system_order_context', { customer: customer.value, price_list: priceList.value }, { silent: true })
    setOrderContext(result)
  } catch (err) {
    error.value = err.message || 'Could not select this customer and price list.'
  } finally { saving.value = false }
}
onBeforeUnmount(() => { ++request; clearTimeout(timer) })
</script>
