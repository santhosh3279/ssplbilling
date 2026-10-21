<template>
  <div class="fixed inset-x-0 top-0 flex h-[100dvh] flex-col bg-[var(--color-bg)] text-[var(--color-text)]" :style="viewportStyle">
    <header class="z-20 shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-3 pt-[max(1rem,env(safe-area-inset-top))] shadow-sm">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <button type="button" aria-label="Back" class="rounded-lg px-2 py-1 text-lg" @click="goBack">←</button>
          <h1 class="text-lg font-bold">{{ item ? 'Item Barcodes' : 'Find Item' }}</h1>
        </div>
        <span v-if="loading" class="text-xs font-semibold text-[var(--color-info)] animate-pulse">Loading…</span>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto px-4 py-3">
      <div v-if="error" class="mb-3 rounded-xl border border-[var(--color-danger)] bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
        {{ error }}
      </div>

      <!-- No item yet: items are picked only in the scanner (camera, or its typed search) -->
      <div v-if="!item" class="flex flex-col items-center py-12 text-center">
        <button
          type="button"
          class="flex items-center gap-3 rounded-2xl bg-[var(--color-info)] px-8 py-5 text-lg font-bold text-white shadow-sm active:scale-95"
          @click="scanFor = 'find'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8"/><path d="M11 8v8"/><path d="M15 8v8"/><path d="M18 8v8"/></svg>
          Scan Item
        </button>
        <div class="mt-3 text-sm text-[var(--color-text-muted)]">Scan the barcode, or type the item name or code in the scanner</div>
      </div>

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
          class="mb-1.5 flex items-center gap-2 rounded-lg border-2 border-[var(--color-text)] px-2 py-1.5"
          :class="b.barcode === lastAdded ? 'bg-[var(--color-success)]/15' : 'bg-[var(--color-surface)]'"
        >
          <div class="min-w-0 flex-1">
            <div class="break-all font-mono text-xl font-bold leading-tight text-[var(--color-text)]">{{ b.barcode }}</div>
            <div v-if="b.barcode_type" class="text-xs text-[var(--color-text-muted)]">{{ b.barcode_type }}</div>
          </div>
          <select
            :value="b.uom"
            :aria-label="`UOM for barcode ${b.barcode}`"
            :disabled="saving"
            class="max-w-[8rem] shrink-0 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1.5 text-sm outline-none focus:border-[var(--color-info)] disabled:opacity-50"
            @change="changeBarcodeUom(b, $event)"
          >
            <option v-for="u in item.uoms" :key="u.uom" :value="u.uom">{{ uomLabel(u) }}</option>
          </select>
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

        <!-- UOM conversions -->
        <div class="mb-2 mt-5 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Units ({{ item.uoms.length }})
        </div>
        <div
          v-for="u in item.uoms"
          :key="u.uom"
          class="mb-2 flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3"
        >
          <div class="min-w-0 flex-1">
            <div class="truncate text-base font-semibold">{{ u.uom }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">1 {{ u.uom }} = {{ fmtFactor(u.conversion_factor) }} {{ item.stock_uom }}</div>
          </div>
          <span v-if="u.uom === item.stock_uom" class="shrink-0 text-xs text-[var(--color-text-muted)]">Stock UOM</span>
          <template v-else>
            <button
              type="button"
              :disabled="saving"
              class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm active:bg-[var(--color-surface-raised)] disabled:opacity-50"
              @click="editUom(u)"
            >Edit</button>
            <button
              type="button"
              :aria-label="`Remove UOM ${u.uom}`"
              :disabled="saving"
              class="shrink-0 rounded-lg border border-[var(--color-danger)] px-3 py-1.5 text-sm font-semibold text-[var(--color-danger)] active:bg-[var(--color-danger)]/10 disabled:opacity-50"
              @click="removeUom(u.uom)"
            >Remove</button>
          </template>
        </div>
        <div class="mb-4 rounded-xl border border-dashed border-[var(--color-border)] p-3">
          <div class="mb-2 flex gap-2">
            <input
              v-model="uomQuery"
              list="ib-uom-list"
              type="text"
              autocomplete="off"
              autocapitalize="off"
              spellcheck="false"
              placeholder="UOM (e.g. Box)"
              aria-label="UOM"
              class="min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-3 text-base outline-none focus:border-[var(--color-info)]"
            />
            <datalist id="ib-uom-list">
              <option v-for="u in uomOptions" :key="u" :value="u" />
            </datalist>
            <input
              v-model="uomFactor"
              type="number"
              inputmode="decimal"
              min="0"
              step="any"
              placeholder="Factor"
              aria-label="Conversion factor"
              class="w-24 shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-3 text-base outline-none focus:border-[var(--color-info)]"
              @keydown.enter.prevent="saveUom"
            />
          </div>
          <div class="mb-2 text-xs text-[var(--color-text-muted)]">
            1 {{ uomQuery.trim() || 'UOM' }} = {{ uomFactor || '?' }} {{ item.stock_uom }}
          </div>
          <button
            type="button"
            :disabled="saving || !uomQuery.trim() || !(Number(uomFactor) > 0)"
            class="w-full rounded-xl border border-[var(--color-info)] py-2.5 text-base font-semibold text-[var(--color-info)] active:bg-[var(--color-info)]/10 disabled:opacity-50"
            @click="saveUom"
          >{{ isExistingUom ? 'Update Factor' : 'Add UOM' }}</button>
        </div>
      </template>
    </main>

    <!-- Add barcode bar -->
    <footer
      v-if="item"
      class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3"
    >
      <!-- The item being edited, at the bottom with the add bar; Change reopens the scanner -->
      <div class="mb-3 flex items-center gap-3 border-b border-[var(--color-border)] pb-3">
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
          v-model="newUom"
          aria-label="Barcode UOM"
          class="max-w-[45%] rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-3 text-base outline-none focus:border-[var(--color-info)]"
        >
          <option v-for="u in item.uoms" :key="u.uom" :value="u.uom">{{ uomLabel(u) }}</option>
        </select>
        <button
          type="button"
          :disabled="saving || !newBarcode.trim()"
          class="flex-1 rounded-xl bg-[var(--color-highlight)] py-3 text-base font-bold text-[var(--color-text-on-highlight)] active:scale-[0.99] disabled:opacity-50"
          @click="addBarcode"
        >{{ saving ? 'Saving…' : 'Add Barcode' }}</button>
      </div>
    </footer>

    <BarcodeScanner
      v-if="scanFor"
      :verify="scanFor === 'find' ? itemExists : null"
      :search="scanFor === 'find' ? scannerSearch : null"
      @detected="onScanned"
      @close="closeScanner"
    />

    <div
      v-if="toast"
      class="pointer-events-none fixed inset-x-4 bottom-36 z-50 rounded-xl bg-[var(--color-success)] px-4 py-3 text-center text-sm font-semibold text-white shadow-lg"
    >{{ toast }}</div>
  </div>
</template>

<script setup>
/**
 * ItemBarcode.vue — phone page to attach extra barcodes to an Item.
 * Pick the item in the scanner (camera, or its typed search), then scan / type barcodes to add, each tied to
 * one of the item's UOMs; UOM conversions (UOM + factor) are added / edited here too.
 * Every change saves the Item at once. The server refuses a barcode another item uses.
 * The scanner's typed search lists items from the local item cache, as on the billing screen.
 */
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api'
import BarcodeScanner from '../components/BarcodeScanner.vue'
import { lookupItemInCache, refreshItemCache, searchItemsInCache } from '../services/itemCache.js'
import { getDefaultPriceList, getDefaultWarehouse } from '../encryption.js'

const API = 'ssplbilling.api.item_api'
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const item = ref(null)
const newBarcode = ref('')
const newUom = ref('')
const uomOptions = ref([])
const uomQuery = ref('')
const uomFactor = ref('')
const lastAdded = ref('')
const toast = ref('')
const scanFor = ref('') // '' | 'find' | 'add'
const newBarcodeRef = ref(null)

let toastTimer = null

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

// OCR readings in "find" mode are accepted only when they are a real item code / barcode
async function itemExists(code) {
  if (lookupItemInCache(code)) return true
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
  if (!detail.uoms.some(u => u.uom === newUom.value)) newUom.value = detail.stock_uom
}

function changeItem() {
  item.value = null
  newBarcode.value = ''
  uomQuery.value = ''
  uomFactor.value = ''
  error.value = ''
  scanFor.value = 'find'
}

function goBack() {
  if (item.value) return changeItem()
  if (window.history.state?.back) router.back()
  else router.push('/')
}

// ── Scanner ──
const priceList = getDefaultPriceList()

// Price list rate of the item's default UOM, the same lookup as the billing screen
function baseRate(cached) {
  const uom = cached.uom || 'Nos'
  if (cached.uom_price_lists?.[priceList]?.[uom] != null) return cached.uom_price_lists[priceList][uom]
  const entry = (cached.price_lists || []).find(p => p.name === priceList)
  return entry ? entry.rate : parseFloat(cached.price || 0)
}

// Typed-entry matches inside the scanner screen
function scannerSearch(q) {
  return searchItemsInCache(q, 30).map(i => ({
    code: i.item_code,
    name: i.item_name || i.item_code,
    price: baseRate(i),
    barcodes: [
      ...(i.barcodes || '').split(','),
      ...(i.barcodes_detailed || []).map(b => b.barcode || ''),
    ].map(b => b.trim()).filter(Boolean),
  }))
}

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
  // A picked search result or a cached code / barcode opens straight away
  const cached = lookupItemInCache(code)
  if (cached) return openItem(cached.item_code)
  loading.value = true
  error.value = ''
  try {
    const exact = (await fetchResults(code)).filter(r => r.exact)
    if (exact.length === 1) return openItem(exact[0].item_code)
    error.value = `No item found for "${code}". Tap Scan Item to try again.`
  } catch (e) {
    error.value = errText(e)
  } finally {
    loading.value = false
  }
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

// ── UOM conversions ──
function fmtFactor(v) {
  return Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 6 })
}

function uomLabel(u) {
  return u.uom === item.value?.stock_uom ? u.uom : `${u.uom} (${fmtFactor(u.conversion_factor)})`
}

// Typed text matched to a master UOM ignoring case, so "box" saves as "Box"
const resolvedUom = computed(() => {
  const q = uomQuery.value.trim().toLowerCase()
  return uomOptions.value.find(u => u.toLowerCase() === q) || uomQuery.value.trim()
})
const isExistingUom = computed(() => !!item.value?.uoms.some(u => u.uom === resolvedUom.value))

async function loadUomOptions() {
  try {
    uomOptions.value = (await frappeGet(`${API}.get_uom_list`)) || []
  } catch (e) {
    console.warn('[ItemBarcode] get_uom_list failed:', e)
  }
}

function editUom(u) {
  uomQuery.value = u.uom
  uomFactor.value = String(u.conversion_factor)
}

async function saveUom() {
  const uom = resolvedUom.value
  const factor = Number(uomFactor.value)
  if (!item.value || saving.value || !uom || !(factor > 0)) return
  if (uomOptions.value.length && !uomOptions.value.includes(uom)) {
    error.value = `UOM "${uom}" does not exist. Pick one from the list.`
    return
  }
  saving.value = true
  error.value = ''
  try {
    setItem(await frappePost(`${API}.set_item_uom`, {
      item_code: item.value.item_code,
      uom,
      conversion_factor: factor,
    }, { silent: true }))
    newUom.value = uom // the usual next step is a barcode for this pack
    uomQuery.value = ''
    uomFactor.value = ''
    flash(`Saved 1 ${uom} = ${fmtFactor(factor)} ${item.value.stock_uom}`)
  } catch (e) {
    error.value = errText(e)
  } finally {
    saving.value = false
  }
}

async function removeUom(uom) {
  if (!item.value || saving.value) return
  if (!confirm(`Remove UOM ${uom} from ${item.value.item_name}?`)) return
  saving.value = true
  error.value = ''
  try {
    setItem(await frappePost(`${API}.remove_item_uom`, { item_code: item.value.item_code, uom }, { silent: true }))
    flash(`Removed ${uom}`)
  } catch (e) {
    error.value = errText(e)
  } finally {
    saving.value = false
  }
}

async function changeBarcodeUom(b, event) {
  const uom = event.target.value
  if (!item.value || uom === b.uom) return
  saving.value = true
  error.value = ''
  try {
    setItem(await frappePost(`${API}.set_barcode_uom`, {
      item_code: item.value.item_code,
      barcode: b.barcode,
      uom,
    }, { silent: true }))
    flash(`${b.barcode} → ${uom}`)
  } catch (e) {
    event.target.value = b.uom
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
  loadUomOptions()
  refreshItemCache('Sales', priceList, getDefaultWarehouse())
    .catch(e => console.warn('[ItemBarcode] item cache refresh failed:', e))
  const code = router.currentRoute.value.query.item
  if (code) openItem(String(code))
  else scanFor.value = 'find' // item entry is the scanner only
})

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  window.visualViewport?.removeEventListener('resize', fitViewport)
  window.removeEventListener('resize', fitViewport)
})
</script>
