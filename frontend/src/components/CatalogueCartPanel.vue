<template>
  <aside v-if="cartItems.length" class="fixed bottom-4 right-4 z-[65] w-[min(18rem,calc(100vw-2rem))] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] shadow-2xl lg:top-20 lg:bottom-4 lg:flex lg:flex-col" aria-label="Your cart">
    <div class="flex items-center justify-between gap-3 border-b border-[var(--color-border)] p-4">
      <h2 class="text-base font-bold">Your cart</h2>
      <span class="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-bold text-indigo-800">{{ cartCount }} {{ cartCount === 1 ? 'item' : 'items' }}</span>
    </div>
    <ul class="hidden min-h-0 flex-1 overflow-y-auto p-3 lg:block">
      <li v-for="item in cartItems" :key="`${item.pageaddress}:${item.item_code}`" class="flex items-start justify-between gap-3 border-b border-[var(--color-border)]/50 px-1 py-3 text-sm last:border-0">
        <div class="min-w-0">
          <div class="break-all font-semibold">{{ item.item_code }}</div>
          <div class="truncate text-xs text-[var(--color-text-muted)]" :title="item.pageaddress">{{ item.pageaddress }}</div>
          <div v-if="purchasedLine(item)?.discount_percentage" class="text-xs font-semibold text-emerald-600">
            {{ purchasedLine(item).discount_percentage }}% off
          </div>
          <div v-for="(bonus, index) in bonusLines(item)" :key="index" class="mt-1 text-xs font-semibold text-emerald-600">
            + {{ bonus.qty }} × {{ bonus.item_code }} ({{ bonus.rate ? 'Offer item' : 'Free item' }})
            <span v-if="bonus.rate">· {{ money(bonus.amount) }}</span>
          </div>
        </div>
        <div class="shrink-0 text-right font-bold">
          <div>× {{ item.qty }}</div>
          <div v-if="preview" class="text-xs">{{ money(purchasedLine(item)?.amount) }}</div>
        </div>
      </li>
    </ul>
    <div v-if="preview" class="space-y-1 border-t border-[var(--color-border)] px-4 py-3 text-sm">
      <div v-if="preview.discount_total" class="flex justify-between text-emerald-600">
        <span>Discount</span>
        <span>−{{ money(preview.discount_total) }}</span>
      </div>
      <div class="flex justify-between font-bold">
        <span>Total</span>
        <span>{{ money(preview.total) }}</span>
      </div>
    </div>
    <RouterLink to="/catalogue-cart" class="m-3 block rounded-xl bg-indigo-600 px-4 py-3 text-center text-sm font-bold text-white hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
      View cart
    </RouterLink>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { frappePost } from '../api.js'
import { orderContext, orderParams } from '../services/catalogueOrderContext.js'
import { cartCount, cartItems } from '../services/catalogueCart.js'

const preview = ref(null)
let requestId = 0
const money = value => Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const purchasedLine = item => preview.value?.items?.find(line =>
  !line.is_free_item && line.pageaddress === item.pageaddress && line.item_code === item.item_code
)
const bonusLines = item => (preview.value?.items || []).filter(line =>
  line.is_free_item && line.pageaddress === item.pageaddress && line.source_item_code === item.item_code
)

watch([cartItems, orderContext], async ([items]) => {
  const currentRequest = ++requestId
  preview.value = null
  if (!items.length) return
  try {
    const result = await frappePost('ssplbilling.api.catalogue_order_api.get_cart_preview', { items, ...orderParams() }, { silent: true })
    if (currentRequest === requestId) preview.value = result
  } catch {
    // The cart remains usable if its price preview cannot be loaded.
  }
}, { deep: true, immediate: true })
</script>
