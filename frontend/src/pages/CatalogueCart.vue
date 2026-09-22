<template>
  <main class="h-screen overflow-y-auto bg-[var(--color-bg)] p-6 text-[var(--color-text)]">
    <div class="mx-auto max-w-4xl space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <RouterLink to="/catalogueviewer" class="text-sm text-indigo-500 hover:underline">← Catalogues</RouterLink>
          <h1 class="text-3xl font-bold">Your cart</h1>
        </div>
        <span v-if="isLoggedIn" class="text-sm">{{ session.fullName.value || session.user.value }}</span>
      </header>

      <CatalogueOrderParty />
      <p v-if="loading">Loading cart…</p>
      <div v-else-if="error && !preview" role="alert" class="space-y-3 rounded-xl bg-red-100 p-4 text-red-800">
        <p>{{ error }}</p>
        <button v-if="cartItems.length" type="button" class="rounded-lg border border-red-400 px-3 py-1" @click="clearCart">Clear cart</button>
      </div>
      <div v-else-if="!lines.length" class="rounded-xl bg-[var(--color-surface)] p-8 text-center">
        Your cart is empty. <RouterLink to="/catalogueviewer" class="text-indigo-500 underline">Browse catalogues</RouterLink>
      </div>
      <template v-else>
        <p v-if="error" role="alert" class="rounded-xl bg-red-100 p-4 text-red-800">{{ error }}</p>
        <div class="rounded-xl bg-[var(--color-surface)] p-4 text-sm">
          <strong>{{ preview.customer_name }}</strong> · {{ preview.price_list }}
        </div>
        <div v-for="(line, index) in lines" :key="index" class="flex flex-wrap items-center gap-4 rounded-xl bg-[var(--color-surface)] p-4 shadow-sm">
          <img v-if="line.image" :src="line.image" :alt="line.item_name" class="h-20 w-20 rounded-lg bg-white object-contain" />
          <div class="min-w-0 flex-1">
            <div class="font-semibold">{{ line.item_name }} <span v-if="line.is_free_item" class="text-sm text-emerald-600">{{ line.rate ? 'Offer item' : 'Free item' }}</span></div>
            <div class="text-xs text-[var(--color-text-muted)]">{{ line.item_code }} · {{ line.uom }}</div>
            <div class="text-sm">{{ money(line.rate) }} each <span v-if="line.discount_percentage" class="text-emerald-600">· {{ line.discount_percentage }}% off</span></div>
            <div v-if="!line.is_free_item && line.discount_qty" class="text-sm font-semibold text-emerald-600">{{ line.requested_qty }} purchased + {{ line.discount_qty }} bonus = {{ line.total_qty }} items</div>
          </div>
          <div v-if="!line.is_free_item" class="flex items-center gap-2">
            <button type="button" :disabled="updating" :aria-label="`Decrease ${line.item_name}`" class="rounded-lg border px-3 py-1 disabled:opacity-50" @click="changeQuantity(line, -1)">−</button>
            <span class="w-8 text-center">{{ line.requested_qty }}</span>
            <button type="button" :disabled="updating" :aria-label="`Increase ${line.item_name}`" class="rounded-lg border px-3 py-1 disabled:opacity-50" @click="changeQuantity(line, 1)">+</button>
          </div>
          <span v-else class="text-sm">Qty {{ line.qty }}</span>
          <strong class="w-28 text-right">{{ money(line.amount) }}</strong>
          <button
            v-if="!line.is_free_item"
            type="button"
            :disabled="updating"
            :aria-label="`Delete ${line.item_name} from cart`"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-base font-bold text-[var(--color-text-muted)] hover:bg-rose-500/15 hover:text-rose-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-rose-500 disabled:opacity-50 transition cursor-pointer"
            title="Delete item"
            @click="deleteItem(line)"
          >
            ✕
          </button>
          <span v-else class="w-8"></span>
        </div>
        <div class="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[var(--color-surface)] p-5">
          <div class="text-lg font-bold">
            <div>Subtotal {{ money(preview.subtotal) }}</div>
            <div v-if="preview.discount_total" class="text-sm text-emerald-600">Discount −{{ money(preview.discount_total) }}</div>
            <div>Total {{ money(preview.total) }}</div>
          </div>
          <RouterLink to="/catalogue-checkout" class="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700">Checkout</RouterLink>
        </div>
      </template>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { frappePost } from '../api.js'
import { session } from '../session.js'
import CatalogueOrderParty from '../components/CatalogueOrderParty.vue'
import { orderContext, orderParams } from '../services/catalogueOrderContext.js'
import { cartItems, clearCart, setCartUser, setQuantity } from '../services/catalogueCart.js'
import { addDiscountQuantities } from '../services/discount-cart.js'

const isLoggedIn = session.isLoggedIn
const loading = ref(true)
const error = ref('')
const preview = ref(null)
const updating = ref(false)
const lines = computed(() => addDiscountQuantities(preview.value?.items || []))
const money = value => Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

let ready = false
let previewRequest = 0
async function refreshPreview() {
  const id = ++previewRequest
  preview.value = null
  error.value = ''
  loading.value = true
  try {
    const result = cartItems.value.length
      ? await frappePost('ssplbilling.api.catalogue_order_api.get_cart_preview', { items: cartItems.value, ...orderParams() }, { silent: true })
      : null
    if (id === previewRequest) preview.value = result
  } catch (err) {
    if (id === previewRequest) error.value = err.message || 'Could not load cart prices.'
  } finally {
    if (id === previewRequest) loading.value = false
  }
}
watch(orderContext, () => { if (ready) refreshPreview() })

async function changeQuantity(line, delta) {
  if (updating.value) return
  updating.value = true
  error.value = ''
  setQuantity(line.pageaddress, line.item_code, line.requested_qty + delta)
  try {
    await refreshPreview()
  } catch (err) {
    error.value = err.message || 'Could not update cart prices.'
  } finally {
    updating.value = false
  }
}

async function deleteItem(line) {
  if (updating.value) return
  updating.value = true
  error.value = ''
  setQuantity(line.pageaddress, line.item_code, 0)
  try {
    await refreshPreview()
  } catch (err) {
    error.value = err.message || 'Could not update cart prices.'
  } finally {
    updating.value = false
  }
}

onMounted(async () => {
  try {
    await session.checkWebsiteUser()
    if (!session.isWebsiteUser.value && !session.isSystemUser.value) {
      error.value = 'Sign in from a catalogue to view your cart.'
      return
    }
    setCartUser(session.user.value)
    await refreshPreview()
  } catch (err) {
    error.value = err.message || 'Could not load cart.'
  } finally {
    ready = true
    loading.value = false
  }
})
</script>
