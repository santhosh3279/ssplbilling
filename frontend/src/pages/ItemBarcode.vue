<template>
  <div class="fixed inset-x-0 top-0 flex h-[100dvh] flex-col bg-[var(--color-bg)] text-[var(--color-text)]" :style="viewportStyle">
    <header class="z-20 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-3 pt-[max(1rem,env(safe-area-inset-top))] shadow-sm">
      <div class="mb-2 flex items-center justify-between">
        <div class="flex items-center gap-1">
          <button type="button" aria-label="Back" class="rounded-lg px-2 py-1 text-lg" @click="goBack">←</button>
          <h1 class="text-lg font-bold">{{ item ? 'Item Barcodes' : 'Find Item' }}</h1>
        </div>
        <span v-if="loading" class="text-xs font-semibold text-[var(--color-info)] animate-pulse">Loading…</span>
      </div>

      <!-- Step 1: find the item -->
      <div v-if="!item" class="flex gap-2">
        <div class="relative flex-1">
          <input
            ref="searchRef"
            v-model="query"
            type="search"
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
            class="absolute right-2 top-1/2 -translate-y-1/2 rounded-full px-2.5 py-1 text-lg text-[var(--color-text-muted)]"
            @click="query = ''; results = []"
          >&times;</button>
        </div>
        <button
          type="button"
          aria-label="Scan item barcode"
          class="flex w-14 shrink-0 items-center justify-center rounded-xl bg-[var(--color-info)] text-white shadow-sm active:scale-95"
          @click="scanFor = 'find'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8"/><path d="M11 8v8"/><path d="M15 8v8"/><path d="M18 8v8"/></svg>
        </button>
      </div>

      <!-- Step 2: the item being edited -->
      <div v-else class="flex items-center gap-3">
        <img v-if="item.image" :src="item.image" alt="" class="h-12 w-12 shrink-0 rounded-lg object-cover" />
        <div class="min-w-0 flex-1">
          <div class="truncate text-base font-semibold">{{ item.item_name }}</div>
          <div class="truncate font-mono text-xs text-[var(--color-text-muted)]">{{ item.item_code }} · {{ item.stock_uom }}</div>
        </div>
        <button
          type="button"
          class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-text-muted)] active:bg-[var(--color-surface-raised)]"
          @click="changeItem"
        >Change</button>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto px-4 py-3">
      <div v-if="error" class="mb-3 rounded-xl border border-[var(--color-danger)] bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
        {{ error }}
      </div>

      <!-- Search results -->
      <template v-if="!item">
        <div v-if="searched && !results.length && !loading" class="py-10 text-center text-sm text-[var(--color-text-muted)]">
          No items found
        </div>
        <button
          v-for="r in results"
          :key="r.item_code"
          type="button"
          class="mb-2 flex w-full items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3 text-left active:bg-[var(--color-surface-raised)]"
          @click="openItem(r.item_code)"
        >
          <div class="min-w-0 flex-1">
            <div class="truncate font-semibold">{{ r.item_name }}</div>
            <div class="truncate font-mono text-xs text-[var(--color-text-muted)]">{{ r.item_code }}</div>
          </div>
          <span class="shrink-0 rounded-full bg-[var(--color-surface-raised)] px-2 py-0.5 text-xs text-[var(--color-text-muted)]">
            {{ r.barcode_count }} barcode{{ r.barcode_count === 1 ? '' : 's' }}
          </span>
        </button>
        <div v-if="!searched" class="py-10 text-center text-sm text-[var(--color-text-muted)]">
          Search or scan to pick the item to edit
        </div>
      </template>

      <!-- Barcode list -->
      <template v-else>
        <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Barcodes ({{ item.barcodes.length }})
        </div>
        <div v-if="!item.barcodes.length" class="mb-2 rounded-xl border border-dashed border-[var(--color-border)] py-6 text-center text-sm text-[var(--color-text-muted)]">
          No barcodes yet
        </div>
        <div
          v-for="b in item.barcodes"
          :key="b.barcode"
          class="mb-2 flex items-center gap-3 rounded-xl border px-3 py-3"
          :class="b.barcode === lastAdded ? 'border-[var(--color-success)] bg-[var(--color-success)]/10' : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
        >
          <div class="min-w-0 flex-1">
            <div class="break-all font-mono text-base font-semibold">{{ b.barcode }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">{{ b.uom }}<span v-if="b.barcode_type"> · {{ b.barcode_type }}</span></div>
          </div>
          <span v-if="b.barcode === item.item_code" class="shrink-0 text-xs text-[var(--color-text-muted)]">Item code</span>
          <button
            v-else
            type="button"
            :aria-label="`Remove barcode ${b.barcode}`"
            :disabled="saving"
            class="shrink-0 rounded-lg border border-[var(--color-danger)] px-3 py-1.5 text-sm font-semibold text-[var(--color-danger)] active:bg-[var(--color-danger)]/10 disabled:opacity-50"
            @click="removeBarcode(b.barcode)"
          >Remove</button>
        </div>
      </template>
    </main>

    <!-- Add barcode bar -->
    <footer
      v-if="item"
      class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3"
    >
      <div class="mb-2 flex gap-2">
        <input
          ref="newBarcodeRef"
          v-model="newBarcode"
          type="text"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="New barcode"
          class="min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 font-mono text-base outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/30"
          @keydown.enter.prevent="addBarcode"
        />
        <button
          type="button"
          aria-label="Scan new barcode"
          class="flex w-14 shrink-0 items-center justify-center rounded-xl bg-[var(--color-info)] text-white shadow-sm active:scale-95"
          @click="scanFor = 'add'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8"/><path d="M11 8v8"/><path d="M15 8v8"/><path d="M18 8v8"/></svg>
        </button>
      </div>
      <div class="flex gap-2">
        <select
          v-if="item.uoms.length > 1"
          v-model="newUom"
          aria-label="Barcode UOM"
          class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-3 text-base outline-none focus:border-[var(--color-info)]"
        >
          <option v-for="u in item.uoms" :key="u" :value="u">{{ u }}</option>
        </select>
        <button
          type="button"
          :disabled="saving || !newBarcode.trim()"
          class="flex-1 rounded-xl bg-[var(--color-highlight)] py-3 text-base font-bold text-[var(--color-text-on-highlight)] active:scale-[0.99] disabled:opacity-50"
          @click="addBarcode"
        >{{ saving ? 'Saving…' : 'Add Barcode' }}</button>
      </div>
    </footer>

    <BarcodeScanner v-if="scanFor" :verify="scanFor === 'find' ? itemExists : null" @detected="onScanned" @close="closeScanner" />

    <div
      v-if="toast"
      class="pointer-events-none fixed inset-x-4 bottom-36 z-50 rounded-xl bg-[var(--color-success)] px-4 py-3 text-center text-sm font-semibold text-white shadow-lg"
    >{{ toast }}</div>
  </div>
</template>

<script setup>
/**
 * ItemBarcode.vue — phone page to attach extra barcodes to an Item.
 * Pick the item (search or camera scan), then scan / type barcodes to add; each add
 * or remove saves the Item at once. The server refuses a barcode another item uses.
 */
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api'
import BarcodeScanner from '../components/BarcodeScanner.vue'

const API = 'ssplbilling.api.item_api'
const router = useRouter()

const query = ref('')
const results = ref([])
const searched = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const item = ref(null)
const newBarcode = ref('')
const newUom = ref('')
const lastAdded = ref('')
const toast = ref('')
const scanFor = ref('') // '' | 'find' | 'add'
const searchRef = ref(null)
const newBarcodeRef = ref(null)

let debounceTimer = null
let toastTimer = null
let requestSeq = 0

function errText(e) {
  return e?.message || String(e || 'Request failed')
}

function flash(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

// ── Find item ──
async function fetchResults(q) {
  return (await frappeGet(`${API}.search_items_for_barcode`, { query: q })) || []
}

async function runSearch() {
  clearTimeout(debounceTimer)
  const q = query.value.trim()
  if (q.length < 2) { results.value = []; searched.value = false; return }
  const seq = ++requestSeq
  loading.value = true
  error.value = ''
  try {
    const rows = await fetchResults(q)
    if (seq !== requestSeq) return
    results.value = rows
    searched.value = true
  } catch (e) {
    if (seq === requestSeq) error.value = errText(e)
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

watch(query, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(runSearch, 300)
})

// OCR readings in "find" mode are accepted only when they are a real item code / barcode
async function itemExists(code) {
  try {
    const rows = await fetchResults(code)
    return rows.some(r => r.exact)
  } catch {
    return false
  }
}

async function openItem(code) {
  loading.value = true
  error.value = ''
  try {
    setItem(await frappeGet(`${API}.get_item_barcodes`, { item_code: code }))
    lastAdded.value = ''
  } catch (e) {
    error.value = errText(e)
  } finally {
    loading.value = false
  }
}

function setItem(detail) {
  item.value = detail
  if (!detail.uoms.includes(newUom.value)) newUom.value = detail.stock_uom
}

function changeItem() {
  item.value = null
  newBarcode.value = ''
  error.value = ''
  nextTick(() => searchRef.value?.focus())
}

function goBack() {
  if (item.value) return changeItem()
  if (window.history.state?.back) router.back()
  else router.push('/')
}

// ── Scanner ──
async function onScanned(code) {
  const mode = scanFor.value
  scanFor.value = ''
  code = String(code || '').trim()
  if (!code) return
  if (mode === 'add') {
    // Shown in the box first so a misread can be fixed before saving
    newBarcode.value = code
    nextTick(() => newBarcodeRef.value?.focus())
    return
  }
  query.value = code
  await runSearch()
  const exact = results.value.filter(r => r.exact)
  if (exact.length === 1) openItem(exact[0].item_code)
}

function closeScanner() {
  scanFor.value = ''
}

// ── Add / remove ──
async function addBarcode() {
  const code = newBarcode.value.trim()
  if (!code || !item.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    setItem(await frappePost(`${API}.add_item_barcode`, {
      item_code: item.value.item_code,
      barcode: code,
      uom: newUom.value,
    }, { silent: true }))
    lastAdded.value = code
    newBarcode.value = ''
    flash(`Added ${code}`)
  } catch (e) {
    error.value = errText(e)
  } finally {
    saving.value = false
  }
}

async function removeBarcode(code) {
  if (!item.value || saving.value) return
  if (!confirm(`Remove barcode ${code} from ${item.value.item_name}?`)) return
  saving.value = true
  error.value = ''
  try {
    setItem(await frappePost(`${API}.remove_item_barcode`, { item_code: item.value.item_code, barcode: code }, { silent: true }))
    flash(`Removed ${code}`)
  } catch (e) {
    error.value = errText(e)
  } finally {
    saving.value = false
  }
}

// ── Keep the layout above the on-screen keyboard ──
const viewportHeight = ref(0)
const viewportStyle = computed(() => (viewportHeight.value ? { height: viewportHeight.value + 'px' } : null))

function fitViewport() {
  viewportHeight.value = window.visualViewport?.height || window.innerHeight
}

onMounted(() => {
  fitViewport()
  window.visualViewport?.addEventListener('resize', fitViewport)
  window.addEventListener('resize', fitViewport)
  // Fetch the ZXing decoder now so the camera reads bars from its first frame on iOS Safari
  import('@zxing/browser').catch(() => {})
  import('@zxing/library').catch(() => {})
  const code = router.currentRoute.value.query.item
  if (code) openItem(String(code))
  else searchRef.value?.focus()
})

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
  clearTimeout(toastTimer)
  window.visualViewport?.removeEventListener('resize', fitViewport)
  window.removeEventListener('resize', fitViewport)
})
</script>
