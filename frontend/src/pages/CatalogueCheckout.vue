<template>
  <main class="min-h-screen bg-[var(--color-bg)] p-6 text-[var(--color-text)]">
    <div class="mx-auto max-w-3xl space-y-6">
      <header>
        <RouterLink to="/catalogue-cart" class="text-sm text-indigo-500 hover:underline">← Cart</RouterLink>
        <h1 class="text-3xl font-bold">Checkout</h1>
      </header>

      <CatalogueOrderParty v-if="!placing && !orderName" />
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
