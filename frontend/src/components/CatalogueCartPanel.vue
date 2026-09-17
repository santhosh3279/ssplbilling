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
        </div>
        <span class="shrink-0 font-bold">× {{ item.qty }}</span>
      </li>
    </ul>
    <RouterLink to="/catalogue-cart" class="m-3 block rounded-xl bg-indigo-600 px-4 py-3 text-center text-sm font-bold text-white hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
      View cart
    </RouterLink>
  </aside>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { cartCount, cartItems } from '../services/catalogueCart.js'
</script>
