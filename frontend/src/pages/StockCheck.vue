<template>
  <div class="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Sticky search bar -->
    <header class="sticky top-0 z-20 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-3 pt-4 shadow-sm">
      <div class="mb-2 flex items-center justify-between">
        <h1 class="text-lg font-bold">Stock Check</h1>
        <span v-if="loading" class="text-xs font-semibold text-[var(--color-info)] animate-pulse">Searching…</span>
        <button
          v-else-if="searched"
          type="button"
          title="Refresh stock from server"
          class="rounded-lg px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          @click="runSearch(true)"
        >{{ results.length }} found · {{ ageLabel }} ↻</button>
      </div>
      <div class="flex gap-2">
      <div class="relative flex-1">
        <input
          ref="searchRef"
          v-model="query"
          type="text"
          inputmode="search"
          enterkeyhint="search"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="Item name, code or barcode"
          class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-4 pr-11 text-base outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/30"
          @keydown.enter.prevent="runSearch()"
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

        <!-- Stock: book stock, draft (redis) quantities, then each warehouse, in one grid -->
        <div class="grid grid-cols-3 gap-px border-t border-[var(--color-border)] bg-[var(--color-border)] text-center text-xs">
          <div class="bg-[var(--color-surface)] px-2 py-2">
            <div class="text-[var(--color-text-muted)]">Book Stock</div>
            <div class="font-mono text-sm font-bold tabular-nums">{{ fmtQty(item.actual_stock) }}</div>
          </div>
          <div class="bg-[var(--color-surface)] px-2 py-2">
            <div class="text-[var(--color-text-muted)]">In Draft Bills</div>
            <div class="font-mono text-sm font-bold tabular-nums text-[var(--color-warning)]">−{{ fmtQty(item.redis_stock) }}</div>
          </div>
          <div class="bg-[var(--color-surface)] px-2 py-2">
            <div class="text-[var(--color-text-muted)]">Draft Purchase</div>
            <div class="font-mono text-sm font-bold tabular-nums text-[var(--color-info)]">+{{ fmtQty(item.redis_purchase_stock) }}</div>
          </div>
          <div v-for="w in item.warehouse_stock" :key="w.warehouse" class="bg-[var(--color-surface)] px-2 py-2">
            <div class="truncate text-[var(--color-text-muted)]" :title="w.warehouse">{{ w.warehouse }}</div>
            <div class="font-mono text-sm font-bold tabular-nums">{{ fmtQty(w.qty) }}</div>
          </div>
          <!-- Pad the last row so it has no gap-coloured holes -->
          <div v-for="n in (3 - item.warehouse_stock.length % 3) % 3" :key="'pad' + n" class="bg-[var(--color-surface)]"></div>
        </div>

        <!-- Selling prices -->
        <div class="border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Selling Price</div>
        <div v-if="!item.prices.length" class="border-t border-[var(--color-border)] px-3 py-2 text-center text-sm italic text-[var(--color-text-muted)]">No selling price set</div>
        <div v-else class="grid gap-px border-t border-[var(--color-border)] bg-[var(--color-border)] text-center text-xs" :class="gridCols(item.prices.length)">
          <div v-for="p in item.prices" :key="p.price_list" class="bg-[var(--color-surface)] px-2 py-2">
            <div class="truncate text-[var(--color-text-muted)]" :title="p.price_list">{{ p.price_list }}</div>
            <div v-for="(rate, uom) in p.rates" :key="uom" class="font-mono text-sm font-bold tabular-nums">
              {{ rate }}<span v-if="Object.keys(p.rates).length > 1 || uom !== item.uom" class="ml-1 font-sans text-[10px] font-normal text-[var(--color-text-muted)]">/ {{ uom }}</span>
            </div>
          </div>
        </div>
      </article>
    </main>

    <BarcodeScanner v-if="showScanner" :verify="codeExists" @detected="onScanned" @close="showScanner = false" />

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
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
const fetchedAt = ref(0)
const now = ref(Date.now())

let debounceTimer = null
let clockTimer = null
let requestSeq = 0

// ── Local result cache ────────────────────────────────────────────
// Searches are kept in localStorage so repeat searches, narrowing a search
// ("pen" → "pen red") and OCR code checks are answered without the server.
// Stock moves, so entries older than CACHE_TTL are shown at once but refetched.
const CACHE_KEY = 'sc-search-cache-v2' // bump when the server's row shape or content rules change
const CACHE_TTL = 2 * 60 * 1000
const CACHE_MAX = 40
const SERVER_LIMIT = 20 // stock_check_api.MAX_RESULTS: fewer rows means the list is complete

function loadCache() {
  try { return JSON.parse(localStorage.getItem(CACHE_KEY)) || {} } catch (e) { return {} }
}
const cache = loadCache()

function saveCache() {
  const keys = Object.keys(cache).sort((a, b) => cache[b].t - cache[a].t)
  for (const k of keys.slice(CACHE_MAX)) delete cache[k]
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(cache)) } catch (e) { /* storage full or blocked */ }
}

const normalize = q => q.trim().toLowerCase().replace(/\s+/g, ' ')
const tokensOf = q => normalize(q).split(' ').filter(Boolean)

function rowMatches(row, tokens) {
  const hay = [row.item_code, row.item_name, ...(row.barcodes || [])].join('\n').toLowerCase()
  return tokens.every(t => hay.includes(t))
}

function isExact(row, key) {
  return row.item_code.toLowerCase() === key || (row.barcodes || []).some(b => b.toLowerCase() === key)
}

/** Cached answer for `key`: its own entry, or a complete entry for a broader query filtered down. */
function fromCache(key) {
  if (cache[key]) return cache[key]
  const tokens = tokensOf(key)
  let best = null
  for (const [k, entry] of Object.entries(cache)) {
    if (entry.rows.length >= SERVER_LIMIT || Date.now() - entry.t > CACHE_TTL) continue
    // Every broader word must be inside one of the new words, so the new matches are a subset
    if (!tokensOf(k).every(o => tokens.some(n => n.includes(o)))) continue
    if (!best || entry.t > best.t) best = entry
  }
  if (!best) return null
  const rows = best.rows.filter(r => rowMatches(r, tokens))
  // Server puts exact code/barcode hits first; keep that order
  rows.sort((a, b) => isExact(b, key) - isExact(a, key))
  return { t: best.t, rows }
}

async function fetchRows(q) {
  const rows = await frappeGet('ssplbilling.api.stock_check_api.search_stock', { query: q })
  const entry = { t: Date.now(), rows: Array.isArray(rows) ? rows : [] }
  cache[normalize(q)] = entry
  saveCache()
  return entry
}

const ageLabel = computed(() => {
  const s = Math.max(0, Math.round((now.value - fetchedAt.value) / 1000))
  return s < 10 ? 'just now' : s < 60 ? `${s}s ago` : `${Math.floor(s / 60)}m ago`
})

function show(entry, q) {
  results.value = entry.rows
  fetchedAt.value = entry.t
  lastQuery.value = q
  searched.value = true
}

async function runSearch(force = false) {
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
  error.value = ''
  const cached = force ? null : fromCache(normalize(q))
  if (cached) {
    show(cached, q)
    loading.value = false
    if (Date.now() - cached.t < CACHE_TTL) return
  }
  loading.value = true
  try {
    const entry = await fetchRows(q)
    if (seq !== requestSeq) return
    show(entry, q)
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
  nextTick(() => runSearch())
}

// OCR readings are guesses: accept one only when it is an exact item code or barcode.
// Any code seen in a cached search answers without the server; misses are cached too.
async function codeExists(code) {
  const key = code.toLowerCase()
  for (const entry of Object.values(cache)) {
    if (entry.rows.some(r => isExact(r, key))) return true
  }
  const cached = cache[normalize(code)]
  if (cached && Date.now() - cached.t < CACHE_TTL) return false
  try {
    const entry = await fetchRows(code)
    return entry.rows.some(r => isExact(r, key))
  } catch (e) {
    return false
  }
}

function clearSearch() {
  query.value = ''
  searchRef.value?.focus()
}

function otherBarcodes(item) {
  return (item.barcodes || []).filter(b => b !== item.item_code)
}

// Same 3-across cell layout as the stock breakdown; fewer cells stretch to fill the row
function gridCols(n) {
  return n === 1 ? 'grid-cols-1' : n === 2 || n === 4 ? 'grid-cols-2' : 'grid-cols-3'
}

function fmtQty(n) {
  const v = Number(n) || 0
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

onMounted(() => {
  searchRef.value?.focus()
  clockTimer = setInterval(() => { now.value = Date.now() }, 15000)
})

onBeforeUnmount(() => clearInterval(clockTimer))
</script>
