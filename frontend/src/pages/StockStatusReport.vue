<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
            @click="router.push('/reports')"
          >
            &larr; Back
          </button>
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Stock Status Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Real-time stock status with advanced filters</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="saveMsg" class="text-sm" :class="saveError ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">{{ saveMsg }}</span>
          <button
            v-if="dirtyCount"
            @click="discardEdits"
            :disabled="savingEdits"
            class="rounded-lg px-3 py-2 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50"
          >
            Discard
          </button>
          <button
            @click="saveEdits"
            :disabled="savingEdits || !dirtyCount"
            title="Save Safety Stock / Max Stock / Min Ord to Item master (Ctrl+S)"
            class="flex items-center gap-2 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--color-info)]/80 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ savingEdits ? 'Saving…' : `Save${dirtyCount ? ` (${dirtyCount})` : ''}` }}
          </button>
          <button
            @click="exportStockReportToExcel"
            :disabled="loadingStockData || !stockReportRows.length"
            class="flex items-center gap-2 rounded-lg bg-[var(--color-success)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--color-success)]/80 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-950/20"
          >
            <span>⬇</span> Export Excel
          </button>
        </div>
      </div>
    </header>

    <main class="flex-1 overflow-hidden flex flex-col p-6">
      <!-- Filters Row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border)] mb-4">
        <!-- Search -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Search Item</label>
          <input
            v-model="stockFilters.search"
            type="text"
            placeholder="Code or Name..."
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          />
        </div>

        <!-- Warehouse -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</label>
          <select
            v-model="stockFilters.warehouse"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          >
            <option value="">— All Warehouses —</option>
            <option v-for="wh in filterOptions.warehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
        </div>

        <!-- Supplier -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            Supplier<span v-if="stockFilters.suppliers.length" class="ml-1 normal-case">({{ stockFilters.suppliers.length }} selected)</span>
          </label>
          <div class="relative" data-supplier-combo>
            <input
              v-model="supplierQuery"
              type="text"
              :placeholder="stockFilters.suppliers.length ? 'Type to add more…' : '— All Suppliers —'"
              class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 pr-7 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              @focus="openSupplierList"
              @input="supplierOpen = true; supplierActiveIdx = 0"
              @keydown="onSupplierKeydown"
              @blur="closeSupplierList"
            />
            <button
              v-if="stockFilters.suppliers.length || supplierQuery"
              type="button"
              class="absolute right-1.5 top-1/2 -translate-y-1/2 text-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
              title="Clear all suppliers"
              @mousedown.prevent="clearSuppliers"
            >×</button>
            <ul
              v-if="supplierOpen && supplierMatches.length"
              class="supplier-list absolute z-30 mt-1 max-h-72 w-full overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
            >
              <li
                v-for="(sup, i) in supplierMatches"
                :key="sup.id"
                class="flex cursor-pointer items-center gap-2 px-2 py-1 text-lg text-[var(--color-text)]"
                :class="[
                  i === supplierActiveIdx
                    ? 'supplier-active bg-[var(--color-focus)] text-[var(--color-text-on-focus)]'
                    : selectedSupplierSet.has(sup.id) ? 'bg-[var(--color-surface-raised)]' : 'hover:bg-[var(--color-surface-raised)]',
                  selectedSupplierSet.has(sup.id) ? 'font-semibold' : ''
                ]"
                @mousedown.prevent="$event.detail < 2 && toggleSupplier(sup)"
                @mouseenter="supplierActiveIdx = i"
              >
                <input
                  type="checkbox"
                  tabindex="-1"
                  class="pointer-events-none h-4 w-4 shrink-0"
                  :checked="selectedSupplierSet.has(sup.id)"
                />
                <span class="truncate">
                  {{ sup.name }}
                  <span v-if="sup.name !== sup.id" class="ml-1 text-sm opacity-70">{{ sup.id }}</span>
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Options dropdown and Reset -->
        <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 pt-5">
          <div ref="monthsBox" class="relative" data-months-combo @keydown.esc="monthsOpen = false">
            <button
              type="button"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              :aria-expanded="monthsOpen"
              @click="monthsOpen = !monthsOpen"
            >
              Avg {{ avgMonths }}M · High Week {{ weekMonths }}M{{ stockFilters.negativeOnly ? ' · Negative' : '' }}{{ stockFilters.showDisabled ? '' : ' · Disabled hidden' }} ▾
            </button>
            <div
              v-if="monthsOpen"
              class="absolute right-0 z-30 mt-1 w-72 space-y-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-lg"
            >
              <label class="flex items-center justify-between gap-4 select-none text-xl text-[var(--color-text)]" title="Monthly avg = sales of last N months ÷ N">
                <span>Avg Months</span>
                <select
                  v-model="stockFilters.avgMonths"
                  class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
                >
                  <option v-for="n in 36" :key="n" :value="n">{{ n }}</option>
                </select>
              </label>
              <label class="flex items-center justify-between gap-4 select-none text-xl text-[var(--color-text)]" title="Highest Weekly Sale looks at the last N months">
                <span>High Week Months</span>
                <select
                  v-model="stockFilters.weekMonths"
                  class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
                >
                  <option v-for="n in 36" :key="n" :value="n">{{ n }}</option>
                </select>
              </label>
              <label class="flex items-center justify-between gap-4 cursor-pointer select-none text-xl text-[var(--color-text)]">
                <span>Negative Stock Only</span>
                <input
                  v-model="stockFilters.negativeOnly"
                  type="checkbox"
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)] w-5 h-5"
                />
              </label>
              <label class="flex items-center justify-between gap-4 cursor-pointer select-none text-xl text-[var(--color-text)]">
                <span>Show Disabled Items</span>
                <input
                  v-model="stockFilters.showDisabled"
                  type="checkbox"
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)] w-5 h-5"
                />
              </label>
            </div>
          </div>

          <button
            @click="resetStockFilters"
            class="text-base text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-colors underline"
          >
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Item count: rows matching the filters, out of all rows loaded -->
      <div v-if="!loadingStockData" class="mb-2 text-lg text-[var(--color-text-muted)]" data-testid="stock-item-count">
        Showing <span class="font-bold tabular-nums text-[var(--color-text)]">{{ filteredStockRows.length.toLocaleString('en-IN') }}</span>
        <template v-if="filteredStockRows.length !== stockReportRows.length"> of {{ stockReportRows.length.toLocaleString('en-IN') }}</template>
        items
      </div>

      <!-- Report Data Table -->
      <div
        @scroll="handleScroll"
        class="flex-1 overflow-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
      >
        <div v-if="loadingStockData" class="flex h-64 items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
            <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching stock status...</p>
          </div>
        </div>
        
        <div v-else-if="!filteredStockRows.length" class="flex h-64 flex-col items-center justify-center text-[var(--color-text-muted)]">
          <span class="text-4xl mb-2">📭</span>
          <p class="text-sm">No items found matching the selected filters.</p>
        </div>

        <table v-else class="w-full border-collapse text-left text-xl whitespace-nowrap">
          <thead class="sticky top-0 bg-[var(--color-lowlight)] border-b border-[var(--color-border)] z-10 text-[var(--color-text)]">
            <tr>
              <th class="px-2 py-1.5 font-semibold">Item Code</th>
              <th class="px-2 py-1.5 font-semibold">Item Name</th>
              <th class="px-2 py-1.5 font-semibold text-right" title="Book stock + draft purchases − draft sales">Actual Stock</th>
              <th class="px-2 py-1.5 font-semibold text-right" title="Net qty sold in last 4 weeks ÷ 4">Weekly Avg Sales</th>
              <th class="px-2 py-1.5 font-semibold text-right" :title="`Net qty sold in last ${avgMonths} months ÷ ${avgMonths}`">Monthly Avg Sales ({{ avgMonths }}M)</th>
              <th class="px-2 py-1.5 font-semibold text-right" :title="`Most net qty sold in any one 7-day week of the last ${weekMonths} months`">Highest Weekly Sale ({{ weekMonths }}M)</th>
              <th class="px-2 py-1.5 font-semibold text-right" :title="`Most net qty sold in any one calendar month of the last ${avgMonths} (incl. current month)`">Highest Monthly Sale ({{ avgMonths }}M)</th>
              <th class="px-2 py-1.5 font-semibold text-right">Safety Stock</th>
              <th class="px-2 py-1.5 font-semibold text-right">Max Stock</th>
              <th class="px-2 py-1.5 font-semibold text-right" title="Minimum order qty (Item master)">Min Ord</th>
              <th class="px-2 py-1.5 font-semibold">UOM</th>
              <th class="px-2 py-1.5 font-semibold">Linked Suppliers</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)] text-[var(--color-text)] font-mono">
            <tr
              v-for="(row, idx) in displayedStockRows"
              :key="row.item_code"
              class="transition-colors"
              :class="[
                focusedRowIdx === idx ? 'stock-row-focused bg-[var(--color-focus)] text-[var(--color-text-on-focus)] font-bold shadow-sm' : 'hover:bg-[var(--color-surface-raised)]/30',
                row.disabled && focusedRowIdx !== idx ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] opacity-60' : ''
              ]"
              :title="row.disabled ? 'Disabled item' : undefined"
            >
              <td class="px-2 py-1 font-bold">{{ row.item_code }}</td>
              <td class="px-2 py-1 font-sans">{{ row.item_name }}</td>
              <td class="px-2 py-1 text-right font-semibold tabular-nums" :class="focusedRowIdx === idx ? '' : (row.actual_stock < 0 ? 'text-[var(--color-danger)]' : '')">
                {{ row.actual_stock }}
                <span
                  v-if="row.draft_purchase || row.draft_sales"
                  class="ml-1 text-base font-normal"
                  :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'"
                  :title="`Book ${fmt(row.book_stock)} + draft purchase ${fmt(row.draft_purchase)} − draft sales ${fmt(row.draft_sales)}`"
                >({{ fmt(row.book_stock) }} +{{ fmt(row.draft_purchase) }} −{{ fmt(row.draft_sales) }})</span>
              </td>
              <td class="px-2 py-1 text-right tabular-nums">{{ fmt(row.weekly_avg_sales) }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ fmt(row.monthly_avg_sales) }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ fmt(row.highest_weekly_sales) }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ fmt(row.highest_monthly_sales) }}</td>
              <td v-for="f in EDIT_FIELDS" :key="f" class="px-1 py-0.5 text-right">
                <input
                  v-model.number="row[f]"
                  type="number"
                  min="0"
                  step="any"
                  :data-edit-field="f"
                  :data-row-idx="idx"
                  class="w-24 rounded border px-1.5 py-0.5 text-right text-xl tabular-nums focus:border-[var(--color-info)] focus:outline-none"
                  :class="isFieldDirty(row, f)
                    ? 'border-[var(--color-warning)] bg-[var(--color-warning)]/20 text-[var(--color-text)]'
                    : 'border-transparent bg-transparent text-inherit hover:border-[var(--color-border)]'"
                  @focus="focusedRowIdx = idx; $event.target.select()"
                  @input="markEdited(row)"
                />
              </td>
              <td class="px-2 py-1 font-sans uppercase tracking-wider" :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'">{{ row.stock_uom }}</td>
              <td class="px-2 py-1 font-sans max-w-xs truncate" :title="row.suppliers">{{ row.suppliers || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchStockReportFilters, fetchStockReportData, frappePost } from '../api.js'
import ExcelJS from 'exceljs'

const router = useRouter()

const loadingStockData = ref(false)
const stockReportRows = ref([])
const focusedRowIdx = ref(-1)
const maxDisplayed = ref(100)
const filterOptions = ref({ warehouses: [], suppliers: [] })

// Inline-editable Item master fields. `originals` holds each edited item's values as loaded, so a row
// is dirty only while some field differs from what the Item master has.
const EDIT_FIELDS = ['safety_stock', 'max_stock', 'min_order_qty']
const originals = ref({})
const savingEdits = ref(false)
const saveMsg = ref('')
const saveError = ref(false)

function num(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function isFieldDirty(row, f) {
  const orig = originals.value[row.item_code]
  return !!orig && num(row[f]) !== num(orig[f])
}

function markEdited(row) {
  if (!originals.value[row.item_code]) {
    // First edit: the input already changed row[f], so rebuild the original from the loaded copy.
    const loaded = loadedValues.get(row.item_code) || {}
    originals.value[row.item_code] = { ...loaded }
  }
  saveMsg.value = ''
}

const dirtyRows = computed(() =>
  stockReportRows.value.filter(r => originals.value[r.item_code] && EDIT_FIELDS.some(f => isFieldDirty(r, f)))
)
const dirtyCount = computed(() => dirtyRows.value.length)

// Snapshot of the editable fields as last loaded / saved, keyed by item_code.
let loadedValues = new Map()
function snapshotLoaded(rows) {
  loadedValues = new Map(rows.map(r => [r.item_code, Object.fromEntries(EDIT_FIELDS.map(f => [f, num(r[f])]))]))
}

function discardEdits() {
  for (const r of stockReportRows.value) {
    const orig = originals.value[r.item_code]
    if (orig) for (const f of EDIT_FIELDS) r[f] = orig[f]
  }
  originals.value = {}
  saveMsg.value = ''
}

async function saveEdits() {
  const rows = dirtyRows.value
  if (!rows.length || savingEdits.value) return
  savingEdits.value = true
  saveMsg.value = ''
  saveError.value = false
  try {
    await frappePost('ssplbilling.api.purchase_api.update_items_order_quantities', {
      items: JSON.stringify(rows.map(r => ({
        item_code: r.item_code,
        safety_stock: num(r.safety_stock),
        custom_max_stock: num(r.max_stock),
        min_order_qty: num(r.min_order_qty)
      })))
    })
    for (const r of rows) {
      for (const f of EDIT_FIELDS) r[f] = num(r[f])
      loadedValues.set(r.item_code, Object.fromEntries(EDIT_FIELDS.map(f => [f, r[f]])))
    }
    originals.value = {}
    saveMsg.value = `Saved ${rows.length} item${rows.length === 1 ? '' : 's'}`
  } catch (err) {
    console.error('Failed to save item quantities:', err)
    saveError.value = true
    saveMsg.value = err?.message || 'Save failed'
  } finally {
    savingEdits.value = false
  }
}

const stockFilters = ref({
  search: '',
  warehouse: '',
  suppliers: [],
  negativeOnly: false,
  showDisabled: true,
  avgMonths: 6,
  weekMonths: 12
})

// Searchable multi-supplier filter: typing filters the list by name or id; clicking / Enter toggles a
// supplier in stockFilters.suppliers (ids). The list stays open so several can be picked in a row.
const supplierQuery = ref('')
const supplierOpen = ref(false)
const supplierActiveIdx = ref(0)

const selectedSupplierSet = computed(() => new Set(stockFilters.value.suppliers))

// Every typed word must appear somewhere in the name or id ("sev hy" finds "Sevana Hygiene").
// Selected suppliers come first, so they can be seen and unticked at the top of the list.
const supplierMatches = computed(() => {
  const words = supplierQuery.value.trim().toLowerCase().split(/\s+/).filter(Boolean)
  const list = (filterOptions.value.suppliers || []).filter(s => {
    const text = `${s.name || ''} ${s.id}`.toLowerCase()
    return words.every(w => text.includes(w))
  })
  const selected = selectedSupplierSet.value
  return [...list.filter(s => selected.has(s.id)), ...list.filter(s => !selected.has(s.id))]
})

function openSupplierList() {
  supplierOpen.value = true
  supplierActiveIdx.value = 0
}

function closeSupplierList() {
  supplierOpen.value = false
  supplierQuery.value = ''
}

function toggleSupplier(sup) {
  const list = stockFilters.value.suppliers
  stockFilters.value.suppliers = list.includes(sup.id) ? list.filter(id => id !== sup.id) : [...list, sup.id]
  // The row moves to / from the top group: keep the highlight on it.
  supplierActiveIdx.value = Math.max(0, supplierMatches.value.findIndex(s => s.id === sup.id))
}

function clearSuppliers() {
  stockFilters.value.suppliers = []
  supplierQuery.value = ''
}

function scrollActiveSupplier() {
  nextTick(() => {
    const el = document.querySelector('.supplier-list .supplier-active')
    if (el) el.scrollIntoView({ block: 'nearest' })
  })
}

function onSupplierKeydown(e) {
  const len = supplierMatches.value.length
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    if (!supplierOpen.value) return openSupplierList()
    if (!len) return
    const step = e.key === 'ArrowDown' ? 1 : -1
    supplierActiveIdx.value = (supplierActiveIdx.value + step + len) % len
    scrollActiveSupplier()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (supplierOpen.value && len) {
      toggleSupplier(supplierMatches.value[supplierActiveIdx.value])
      scrollActiveSupplier()
    }
  } else if (e.key === 'Delete') {
    // Delete clears the typed text only; picked suppliers stay selected.
    e.preventDefault()
    supplierQuery.value = ''
    supplierActiveIdx.value = 0
  } else if (e.key === 'Escape') {
    supplierOpen.value = false
    supplierQuery.value = ''
  }
}

// Dropdown holding the month settings and the negative / disabled options; a click outside closes it.
const monthsOpen = ref(false)
const monthsBox = ref(null)
function closeMonthsOnOutsideClick(e) {
  if (monthsOpen.value && !monthsBox.value?.contains(e.target)) monthsOpen.value = false
}

// Monthly avg divisor: sales of last N months (N*30 days) ÷ N. Invalid input falls back to 6.
const avgMonths = computed(() => {
  const n = Math.floor(Number(stockFilters.value.avgMonths))
  return n >= 1 ? Math.min(n, 36) : 6
})

// Months searched for the highest weekly sale. Invalid input falls back to 12.
const weekMonths = computed(() => {
  const n = Math.floor(Number(stockFilters.value.weekMonths))
  return n >= 1 ? Math.min(n, 36) : 12
})

async function loadStockReportFilters() {
  try {
    const company = localStorage.getItem('wb-company') || ''
    const res = await fetchStockReportFilters(company)
    filterOptions.value = res || { warehouses: [], suppliers: [] }
  } catch (err) {
    console.error('Failed to load stock report filters:', err)
  }
}

async function loadStockReportData() {
  if (dirtyCount.value && !confirm(`Discard ${dirtyCount.value} unsaved change(s)?`)) return
  originals.value = {}
  saveMsg.value = ''
  loadingStockData.value = true
  try {
    const company = localStorage.getItem('wb-company') || ''
    const data = await fetchStockReportData({
      company: company,
      warehouse: stockFilters.value.warehouse,
      supplier: stockFilters.value.suppliers.length ? stockFilters.value.suppliers : '',
      negative_only: stockFilters.value.negativeOnly,
      avg_months: avgMonths.value,
      week_months: weekMonths.value
    })
    stockReportRows.value = data || []
    snapshotLoaded(stockReportRows.value)
    maxDisplayed.value = 100
    focusedRowIdx.value = stockReportRows.value.length ? 0 : -1
  } catch (err) {
    console.error('Failed to load stock report data:', err)
  } finally {
    loadingStockData.value = false
  }
}

watch(
  () => [stockFilters.value.warehouse, stockFilters.value.suppliers.join('\u0001'), stockFilters.value.negativeOnly, avgMonths.value, weekMonths.value],
  () => {
    loadStockReportData()
  }
)

watch(
  () => [stockFilters.value.search, stockFilters.value.showDisabled],
  () => {
    maxDisplayed.value = 100
    focusedRowIdx.value = 0
  }
)

watch(focusedRowIdx, (newIdx) => {
  if (newIdx >= maxDisplayed.value) {
    maxDisplayed.value = newIdx + 50
  }
})

function handleScroll(e) {
  const el = e.target
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 200) {
    if (maxDisplayed.value < filteredStockRows.value.length) {
      maxDisplayed.value += 100
    }
  }
}

const filteredStockRows = computed(() => {
  const query = stockFilters.value.search.trim().toLowerCase()
  let rows = stockReportRows.value

  if (!stockFilters.value.showDisabled) rows = rows.filter(r => !r.disabled)

  if (query) {
    rows = rows.filter(r => 
      r.item_code.toLowerCase().includes(query) || 
      r.item_name.toLowerCase().includes(query)
    )
  }

  // Keep focused row index within bounds
  if (rows.length > 0) {
    if (focusedRowIdx.value < 0 || focusedRowIdx.value >= rows.length) {
      focusedRowIdx.value = 0
    }
  } else {
    focusedRowIdx.value = -1
  }

  return rows
})

const displayedStockRows = computed(() => {
  return filteredStockRows.value.slice(0, maxDisplayed.value)
})

function resetStockFilters() {
  stockFilters.value = {
    search: '',
    warehouse: '',
    suppliers: [],
    negativeOnly: false,
    showDisabled: true,
    avgMonths: 6,
    weekMonths: 12
  }
}

function fmt(n) {
  return Number(Number(n || 0).toFixed(2))
}

async function exportStockReportToExcel() {
  const rows = filteredStockRows.value
  if (!rows || rows.length === 0) {
    alert('No data to export.')
    return
  }

  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet('Stock Status')

  worksheet.columns = [
    { key: 'item_code', width: 20 },
    { key: 'item_name', width: 35 },
    { key: 'actual_stock', width: 15 },
    { key: 'weekly_avg_sales', width: 18 },
    { key: 'monthly_avg_sales', width: 18 },
    { key: 'highest_weekly_sales', width: 20 },
    { key: 'highest_monthly_sales', width: 22 },
    { key: 'safety_stock', width: 15 },
    { key: 'max_stock', width: 15 },
    { key: 'min_order_qty', width: 12 },
    { key: 'stock_uom', width: 10 },
    { key: 'suppliers', width: 35 }
  ]

  // Add Table Header
  const headerRow = worksheet.addRow([
    'Item Code', 'Item Name', 'Actual Stock', 'Weekly Avg Sales', `Monthly Avg Sales (${avgMonths.value}M)`, `Highest Weekly Sale (${weekMonths.value}M)`, `Highest Monthly Sale (${avgMonths.value}M)`, 'Safety Stock', 'Max Stock', 'Min Ord', 'UOM', 'Suppliers'
  ])
  headerRow.eachCell(cell => {
    cell.font = { name: 'Arial', bold: true }
    cell.alignment = { horizontal: 'center' }
    cell.border = {
      bottom: { style: 'thin' },
      top: { style: 'thin' }
    }
  })

  // Add Rows
  for (const r of rows) {
    worksheet.addRow([
      r.item_code,
      r.item_name,
      fmt(r.actual_stock),
      fmt(r.weekly_avg_sales),
      fmt(r.monthly_avg_sales),
      fmt(r.highest_weekly_sales),
      fmt(r.highest_monthly_sales),
      fmt(r.safety_stock),
      fmt(r.max_stock),
      fmt(r.min_order_qty),
      r.stock_uom,
      r.suppliers || ''
    ])
  }

  // Generate blob and download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  
  const fromStr = stockFilters.value.warehouse ? '_' + stockFilters.value.warehouse.replace(/[^A-Za-z0-9]/g, '') : ''
  const sups = stockFilters.value.suppliers
  const supStr = sups.length === 1 ? '_' + sups[0].replace(/[^A-Za-z0-9]/g, '') : sups.length > 1 ? `_${sups.length}suppliers` : ''
  const negStr = stockFilters.value.negativeOnly ? '_negative_only' : ''
  link.download = `StockStatusReport${fromStr}${supStr}${negStr}.xlsx`
  link.click()
}

function scrollToFocusedRow() {
  nextTick(() => {
    const el = document.querySelector('.stock-row-focused')
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

function handleKeyDown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveEdits()
    return
  }
  // Arrow keys inside the supplier box move through its list, not the report rows.
  if (e.target instanceof Element && e.target.closest('[data-supplier-combo]')) return
  // Likewise the months dropdown: arrows change its selects.
  if (e.target instanceof Element && e.target.closest('[data-months-combo]')) return
  // In an editable cell: Up/Down/Enter jump to the same field in the previous/next row.
  const field = e.target instanceof Element && e.target.getAttribute('data-edit-field')
  if (field && (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter')) {
    e.preventDefault()
    const len = filteredStockRows.value.length
    if (!len) return
    const step = e.key === 'ArrowUp' ? -1 : 1
    focusedRowIdx.value = (Number(e.target.getAttribute('data-row-idx')) + step + len) % len
    nextTick(() => {
      const el = document.querySelector(`[data-edit-field="${field}"][data-row-idx="${focusedRowIdx.value}"]`)
      if (el) { el.focus(); el.scrollIntoView({ block: 'nearest' }) }
    })
    return
  }
  // Left/Right: move between editable columns of the row. From outside a cell, Right enters the first one.
  if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
    const inOtherInput = !field && e.target instanceof Element && e.target.matches('input, select, textarea')
    if (inOtherInput || focusedRowIdx.value < 0) return
    let col
    if (field) col = EDIT_FIELDS.indexOf(field) + (e.key === 'ArrowRight' ? 1 : -1)
    else if (e.key === 'ArrowRight') col = 0
    else return
    e.preventDefault()
    if (col < 0) {
      e.target.blur() // Left from the first cell leaves edit mode; Up/Down then move rows again.
      return
    }
    if (col >= EDIT_FIELDS.length) return
    const rowIdx = field ? e.target.getAttribute('data-row-idx') : focusedRowIdx.value
    const el = document.querySelector(`[data-edit-field="${EDIT_FIELDS[col]}"][data-row-idx="${rowIdx}"]`)
    if (el) el.focus()
    return
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const len = filteredStockRows.value.length
    if (len > 0) {
      focusedRowIdx.value = (focusedRowIdx.value + 1) % len
      scrollToFocusedRow()
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const len = filteredStockRows.value.length
    if (len > 0) {
      focusedRowIdx.value = (focusedRowIdx.value - 1 + len) % len
      scrollToFocusedRow()
    }
  }
}

onMounted(() => {
  loadStockReportFilters()
  loadStockReportData()
  window.addEventListener('keydown', handleKeyDown)
  document.addEventListener('mousedown', closeMonthsOnOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('mousedown', closeMonthsOnOutsideClick)
})
</script>

<style scoped>
/* Optional: improve scrolling for wide tables */
.overflow-auto {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.overflow-auto::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.overflow-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-auto::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 20px;
}
</style>
