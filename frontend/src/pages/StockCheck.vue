<template>
  <div class="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Sticky search bar -->
    <header class="sticky top-0 z-20 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-3 pt-4 shadow-sm">
      <div class="mb-2 flex items-center justify-between">
        <h1 class="text-lg font-bold">Stock Check</h1>
        <span v-if="loading" class="text-xs font-semibold text-[var(--color-info)] animate-pulse">Searching…</span>
        <span v-else-if="searched" class="text-xs text-[var(--color-text-muted)]">{{ results.length }} found</span>
      </div>
      <div class="flex gap-2">
      <div class="relative flex-1">
        <input
          ref="searchRef"
          v-model="query"
          type="search"
          inputmode="search"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="Item name, code or barcode"
          class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-4 pr-11 text-base outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/30"
          @keydown.enter.prevent="runSearch"
        />
        <button
          v-if="query"
          type="button"
          aria-label="Clear search"
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded-full px-2.5 py-1 text-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          @click="clearSearch"
        >&times;</button>
      </div>
      <button
        type="button"
        aria-label="Scan barcode with camera"
        title="Scan barcode"
        class="flex w-14 shrink-0 items-center justify-center rounded-xl bg-[var(--color-info)] text-white shadow-sm active:scale-95"
        @click="showScanner = true"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8"/><path d="M11 8v8"/><path d="M15 8v8"/><path d="M18 8v8"/></svg>
      </button>
      </div>
    </header>

    <main class="mx-auto max-w-xl space-y-3 px-4 py-4">
      <div v-if="error" class="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 p-3 text-sm text-[var(--color-danger)]">
        {{ error }}
      </div>

      <div v-else-if="!searched" class="py-16 text-center text-sm text-[var(--color-text-muted)]">
        Type at least 2 characters. Words can be in any order.
      </div>

      <div v-else-if="!loading && !results.length" class="py-16 text-center text-sm text-[var(--color-text-muted)]">
        No items match “{{ lastQuery }}”.
      </div>

      <article
        v-for="item in results"
        :key="item.item_code"
        class="overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm"
      >
        <div class="flex gap-3 p-3">
          <!-- Photo -->
          <button
            v-if="item.image && !brokenImages[item.item_code]"
            type="button"
            class="h-20 w-20 shrink-0 overflow-hidden rounded-xl border border-[var(--color-border)] bg-white"
            @click="previewImage = item.image"
          >
            <img
              :src="item.image"
              :alt="item.item_name"
              loading="lazy"
              class="h-full w-full object-contain"
              @error="brokenImages[item.item_code] = true"
            />
          </button>
          <div v-else class="flex h-20 w-20 shrink-0 items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] text-2xl text-[var(--color-text-muted)]">
            📦
          </div>

          <!-- Name + stock -->
          <div class="min-w-0 flex-1">
            <h2 class="text-base font-bold leading-snug">{{ item.item_name }}</h2>
            <div class="mt-0.5 truncate font-mono text-xs text-[var(--color-text-muted)]">
              {{ item.item_code }}<template v-if="otherBarcodes(item).length"> · {{ otherBarcodes(item).join(', ') }}</template>
            </div>
            <div class="mt-2 flex items-baseline gap-1.5">
              <span
                class="font-mono text-2xl font-black tabular-nums"
                :class="item.stock > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
              >{{ fmtQty(item.stock) }}</span>
              <span class="text-sm text-[var(--color-text-muted)]">{{ item.uom }} available</span>
            </div>
          </div>
        </div>

        <!-- Stock breakdown (book stock vs draft/redis quantities) -->
        <div class="grid grid-cols-3 border-t border-[var(--color-border)] text-center text-xs">
          <div class="border-r border-[var(--color-border)] px-2 py-2">
            <div class="text-[var(--color-text-muted)]">Book Stock</div>
            <div class="font-mono text-sm font-bold tabular-nums">{{ fmtQty(item.actual_stock) }}</div>
          </div>
          <div class="border-r border-[var(--color-border)] px-2 py-2">
            <div class="text-[var(--color-text-muted)]">In Draft Bills</div>
            <div class="font-mono text-sm font-bold tabular-nums text-[var(--color-warning)]">−{{ fmtQty(item.redis_stock) }}</div>
          </div>
          <div class="px-2 py-2">
            <div class="text-[var(--color-text-muted)]">Draft Purchase</div>
            <div class="font-mono text-sm font-bold tabular-nums text-[var(--color-info)]">+{{ fmtQty(item.redis_purchase_stock) }}</div>
          </div>
        </div>

        <!-- Warehouses -->
        <div v-if="item.warehouse_stock.length > 1" class="border-t border-[var(--color-border)] px-3 py-2">
          <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">By Warehouse</div>
          <div v-for="w in item.warehouse_stock" :key="w.warehouse" class="flex justify-between py-0.5 text-sm">
            <span class="truncate pr-2">{{ w.warehouse }}</span>
            <span class="font-mono font-semibold tabular-nums">{{ fmtQty(w.qty) }}</span>
          </div>
        </div>

        <!-- Selling prices -->
        <div class="border-t border-[var(--color-border)] px-3 py-2">
          <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Selling Price</div>
          <div v-if="!item.prices.length" class="text-sm italic text-[var(--color-text-muted)]">No selling price set</div>
          <div v-for="p in item.prices" :key="p.price_list" class="flex items-start justify-between gap-3 py-0.5 text-sm">
            <span class="truncate">{{ p.price_list }}</span>
            <span class="text-right">
              <span v-for="(rate, uom) in p.rates" :key="uom" class="block font-mono font-semibold tabular-nums">
                {{ rate }}<span v-if="Object.keys(p.rates).length > 1 || uom !== item.uom" class="ml-1 font-sans text-xs font-normal text-[var(--color-text-muted)]">/ {{ uom }}</span>
              </span>
            </span>
          </div>
        </div>
      </article>
    </main>

    <BarcodeScanner v-if="showScanner" @detected="onScanned" @close="showScanner = false" />

    <!-- Full-size photo -->
    <div
      v-if="previewImage"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/85 p-4"
      @click="previewImage = ''"
    >
      <img :src="previewImage" alt="" class="max-h-full max-w-full rounded-lg bg-white object-contain" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, nextTick } from 'vue'
import { frappeGet } from '../api.js'
import BarcodeScanner from '../components/BarcodeScanner.vue'

const query = ref('')
const lastQuery = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)
const error = ref('')
const previewImage = ref('')
const brokenImages = reactive({})
const searchRef = ref(null)
const showScanner = ref(false)

let debounceTimer = null
let requestSeq = 0

async function runSearch() {
  clearTimeout(debounceTimer)
  const q = query.value.trim()
  if (q.length < 2) {
    results.value = []
    searched.value = false
    error.value = ''
    return
  }
  // Only the latest request may update the list (typing fires overlapping searches)
  const seq = ++requestSeq
  loading.value = true
  error.value = ''
  try {
    const rows = await frappeGet('ssplbilling.api.stock_check_api.search_stock', { query: q })
    if (seq !== requestSeq) return
    results.value = Array.isArray(rows) ? rows : []
    lastQuery.value = q
    searched.value = true
  } catch (e) {
    if (seq !== requestSeq) return
    error.value = e.message?.includes('429') ? 'Too many searches. Wait a moment and try again.' : 'Search failed: ' + e.message
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

watch(query, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(runSearch, 350)
})

function onScanned(code) {
  showScanner.value = false
  query.value = code
  // Search now instead of waiting out the typing debounce the query watcher just armed
  nextTick(runSearch)
}

function clearSearch() {
  query.value = ''
  searchRef.value?.focus()
}

function otherBarcodes(item) {
  return (item.barcodes || []).filter(b => b !== item.item_code)
}

function fmtQty(n) {
  const v = Number(n) || 0
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

onMounted(() => searchRef.value?.focus())
</script>
