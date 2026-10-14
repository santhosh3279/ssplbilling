<template>
  <main class="h-full overflow-y-auto bg-[var(--color-bg)] p-6 pb-[calc(6rem+env(safe-area-inset-bottom))] text-[var(--color-text)] sm:pb-6">
    <div class="mx-auto max-w-3xl space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <RouterLink to="/catalogue-cart" class="text-sm text-indigo-500 hover:underline">← Cart</RouterLink>
          <h1 class="text-3xl font-bold">Checkout</h1>
        </div>
        <template v-if="session.isSystemUser.value && !placing && !orderName">
          <button
            v-if="orderContext.customer"
            type="button"
            @click="toggleCustomerSection"
            class="flex items-center gap-1.5 rounded-lg border border-indigo-400/40 bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-600 transition hover:bg-indigo-500/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-500 cursor-pointer"
            title="Click to modify customer and price list"
          >
            <span class="max-w-[180px] truncate font-bold">{{ orderContext.customer_name || orderContext.customer }}</span>
            <span class="max-w-[120px] truncate text-[11px]">({{ orderContext.price_list }})</span>
            <span class="ml-0.5 text-[11px]">✏️</span>
          </button>
          <button
            v-else
            type="button"
            @click="toggleCustomerSection"
            class="flex items-center gap-1.5 rounded-lg border border-amber-400/40 bg-amber-500/10 px-2.5 py-1 text-xs text-amber-600 transition hover:bg-amber-500/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-500 cursor-pointer"
            title="Click to select customer and price list"
          >
            <span class="font-bold">Select Customer</span>
            <span class="text-[11px]">🔍</span>
          </button>
        </template>
      </header>

      <CatalogueOrderParty
        v-if="!placing && !orderName && showCustomerSection"
        @applied="showCustomerSection = false"
        @close="showCustomerSection = false"
      />
      <p v-if="loading">Checking prices…</p>
      <p v-else-if="error && !preview" role="alert" class="rounded-xl bg-red-100 p-4 text-red-800">{{ error }}</p>
      <div v-else-if="orderName" class="space-y-4 rounded-xl bg-[var(--color-surface)] p-8 text-center">
        <h2 class="text-2xl font-bold">Order created</h2>
        <p>Your draft Sales Order is <strong>{{ orderName }}</strong>.</p>
        <RouterLink to="/catalogueviewer" class="inline-block rounded-xl bg-indigo-600 px-6 py-3 text-white">Browse catalogues</RouterLink>
      </div>
      <template v-else-if="preview">
        <p v-if="error" role="alert" class="rounded-xl bg-red-100 p-4 text-red-800">{{ error }}</p>
        <div class="rounded-xl bg-[var(--color-surface)] p-5">
          <h2 class="font-bold">{{ preview.customer_name }}</h2>
          <p class="text-sm">Price list: {{ preview.price_list }}</p>
          <p class="text-sm">Order series: {{ preview.naming_series }}</p>
        </div>
        <div class="rounded-xl bg-[var(--color-surface)] p-5">
          <div v-for="(line, index) in preview.items" :key="index" class="flex justify-between gap-4 border-b py-3 last:border-0">
            <div>{{ line.item_name }} <span class="text-sm text-[var(--color-text-muted)]">× {{ line.qty }} {{ line.uom }}</span><span v-if="line.is_free_item" class="ml-2 text-sm text-emerald-600">{{ line.rate ? 'Offer item' : 'Free item' }}</span><span v-else-if="line.discount_percentage" class="ml-2 text-sm text-emerald-600">{{ line.discount_percentage }}% off</span></div>
            <strong>{{ money(line.amount) }}</strong>
          </div>
          <div class="flex justify-between pt-4"><span>Subtotal</span><span>{{ money(preview.subtotal) }}</span></div>
          <div v-if="preview.discount_total" class="flex justify-between text-emerald-600"><span>Discount</span><span>−{{ money(preview.discount_total) }}</span></div>
          <div class="flex justify-between pt-2 text-lg font-bold"><span>Total</span><span>{{ money(preview.total) }}</span></div>
        </div>
        <button type="button" :disabled="placing" class="w-full rounded-xl bg-indigo-600 px-6 py-3 font-bold text-white hover:bg-indigo-700 disabled:opacity-50" @click="placeOrder">
          {{ placing ? 'Creating order…' : 'Place order' }}
        </button>
        <p class="text-sm text-[var(--color-text-muted)]">This creates a draft Sales Order for the customer shown above.</p>
      </template>
    </div>
  </main>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { frappePost } from '../api.js'
import { session } from '../session.js'
import CatalogueOrderParty from '../components/CatalogueOrderParty.vue'
import { orderContext, orderParams } from '../services/catalogueOrderContext.js'
import { cartItems, clearCart, setCartUser } from '../services/catalogueCart.js'

const loading = ref(true)
const placing = ref(false)
const error = ref('')
const preview = ref(null)
const orderName = ref('')
const showCustomerSection = ref(!orderContext.value.customer)
watch(() => orderContext.value.customer, (newCust, oldCust) => {
  if (!oldCust && newCust) showCustomerSection.value = false
  else if (!newCust) showCustomerSection.value = true
})
function toggleCustomerSection() {
  showCustomerSection.value = !showCustomerSection.value
}
const money = value => Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

let ready = false
let previewRequest = 0
async function refreshPreview() {
  const id = ++previewRequest
  preview.value = null
  loading.value = true
  error.value = ''
  try {
    if (!cartItems.value.length) throw new Error('Your cart is empty.')
    const result = await frappePost('ssplbilling.api.catalogue_order_api.get_cart_preview', { items: cartItems.value, ...orderParams() }, { silent: true })
    if (id === previewRequest) preview.value = result
  } catch (err) {
    if (id === previewRequest) error.value = err.message || 'Could not load checkout.'
  } finally {
    if (id === previewRequest) loading.value = false
  }
}
watch(orderContext, () => { if (ready && !placing.value && !orderName.value) refreshPreview() })

onMounted(async () => {
  try {
    await session.checkWebsiteUser()
    if (!session.isWebsiteUser.value && !session.isSystemUser.value) {
      error.value = 'Sign in from a catalogue to check out.'
      return
    }
    setCartUser(session.user.value)
    if (!cartItems.value.length) {
      error.value = 'Your cart is empty.'
      return
    }
    await refreshPreview()
  } catch (err) {
    error.value = err.message || 'Could not load checkout.'
  } finally {
    ready = true
    loading.value = false
  }
})

async function placeOrder() {
  if (placing.value || loading.value || !preview.value) return
  placing.value = true
  error.value = ''
  try {
    const result = await frappePost('ssplbilling.api.catalogue_order_api.place_order', { items: cartItems.value, customer: preview.value.customer, price_list: preview.value.price_list }, { silent: true })
    orderName.value = result.order_name
    clearCart()
  } catch (err) {
    error.value = err.message || 'Could not create Sales Order.'
  } finally {
    placing.value = false
  }
}
</script>
