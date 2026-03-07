<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-white' : 'flex min-h-screen flex-col bg-gray-50'">
    <div class="flex h-full flex-col">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-gray-200 bg-white px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="handleBack"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            ← {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <span class="text-gray-300">|</span>
          <h1 class="text-sm font-bold text-gray-800">Stock Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-600">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info for sub-window -->
        <div v-if="isSubWindow" class="flex items-center gap-4 text-[10px] text-gray-400">
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono">Ctrl+I</kbd> Item Search</span>
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono">Esc</kbd> Close</span>
        </div>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-gray-200 bg-white shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-gray-500 hover:bg-gray-100">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-gray-200 bg-gray-50 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-gray-400 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-gray-600 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-gray-500 hover:bg-gray-100">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-gray-200 bg-white px-6 py-3">
      <div class="flex flex-wrap items-end gap-3">

        <!-- Item search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-gray-400">
            <span>Item</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-gray-200 bg-gray-50 px-1 font-mono text-[9px]">Ctrl+I</kbd> Search
            </span>
          </label>
          <div 
            @click="openItemSearch"
            class="w-full cursor-pointer rounded border border-gray-300 px-3 py-2 text-sm outline-none transition-colors hover:border-blue-400"
            :class="selectedItem ? 'bg-blue-50 font-semibold text-blue-800' : 'bg-white text-gray-400'"
          >
            {{ selectedItem ? `${selectedItem.item_code} - ${selectedItem.item_name}` : 'Select an item...' }}
          </div>
          <!-- Clear button -->
          <button
            v-if="selectedItem"
            @click="clearItem"
            class="absolute right-2 top-7 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400">From</label>
          <input
            v-model="fromDate"
            type="date"
            class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          />
        </div>

        <!-- Warehouse filter -->
        <div class="w-48">
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400">Warehouse</label>
          <select
            v-model="selectedWarehouse"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          >
            <option value="">All Warehouses</option>
            <option v-for="w in allowedWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedItem || loading"
          class="rounded-lg px-5 py-2 text-sm font-semibold transition-colors"
          :class="selectedItem && !loading
            ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
        >
          {{ loading ? 'Loading...' : 'Load Ledger' }}
        </button>

        <!-- Summary chips -->
        <template v-if="ledgerData">
          <div class="ml-2 flex items-center gap-2">
            <div class="flex flex-col rounded bg-orange-50 px-3 py-1 border border-orange-100">
              <span class="text-[9px] font-bold uppercase text-orange-400 leading-none">Opening</span>
              <span class="text-sm font-bold text-orange-700 leading-tight">{{ ledgerData.opening_balance }}</span>
            </div>
            <div class="flex flex-col rounded bg-green-50 px-3 py-1 border border-green-100">
              <span class="text-[9px] font-bold uppercase text-green-400 leading-none">Purchase (In)</span>
              <span class="text-sm font-bold text-green-700 leading-tight">+{{ ledgerData.total_in }}</span>
            </div>
            <div class="flex flex-col rounded bg-red-50 px-3 py-1 border border-red-100">
              <span class="text-[9px] font-bold uppercase text-red-400 leading-none">Sale (Out)</span>
              <span class="text-sm font-bold text-red-700 leading-tight">-{{ ledgerData.total_out }}</span>
            </div>
            <div class="flex flex-col rounded bg-blue-50 px-3 py-1 border border-blue-100">
              <span class="text-[9px] font-bold uppercase text-blue-400 leading-none">Closing</span>
              <span class="text-sm font-bold text-blue-700 leading-tight">{{ ledgerData.closing_balance }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Ledger Table ── -->
      <div class="flex flex-1 flex-col overflow-hidden">

        <!-- Empty / loading state -->
        <div v-if="!ledgerData && !loading && !error" class="flex flex-1 flex-col items-center justify-center gap-2 text-gray-400">
          <div class="text-4xl">📦</div>
          <div class="text-sm font-semibold">Select an item and load the stock ledger</div>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center text-sm text-gray-400">
          Loading ledger...
        </div>

        <div v-else-if="error" class="m-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ error }}
        </div>

        <template v-else-if="ledgerData">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
              <thead class="sticky top-0 z-10 bg-gray-50">
                <tr class="border-b border-gray-200">
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-gray-400">Date</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-gray-400">Type</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-gray-400">Voucher No</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-gray-400">Warehouse</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-gray-400">Qty</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-gray-400">Balance</th>
                </tr>
              </thead>
              <tbody ref="tableBodyRef">
                <!-- No entries message -->
                <tr v-if="!ledgerData.entries.length">
                  <td colspan="6" class="px-4 py-12 text-center text-gray-400">
                    No stock transactions found for the selected period.
                  </td>
                </tr>

                <!-- Ledger rows -->
                <tr
                  v-for="(entry, idx) in ledgerData.entries"
                  :key="idx"
                  :data-idx="idx"
                  @click="onRowClick(entry, idx)"
                  @mouseenter="onRowMouseEnter(entry, idx)"
                  class="cursor-pointer border-b border-gray-100 transition-colors"
                  :class="focusedIdx === idx
                    ? 'bg-blue-100 outline outline-1 outline-blue-300'
                    : selectedEntry === entry
                      ? 'bg-blue-50'
                      : 'hover:bg-gray-50'"
                >
                  <td class="px-4 text-gray-600" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ fmtDate(entry.date) }}</td>
                  <td class="px-4" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span
                      class="rounded px-1.5 py-0.5 font-bold"
                      :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }"
                      :class="voucherBadgeClass(entry.voucher_type)"
                    >
                      {{ voucherLabel(entry.voucher_type) }}
                    </span>
                  </td>
                  <td class="px-4" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button
                      @click.stop="openInErpNext(entry.voucher_type, entry.voucher_no)"
                      class="font-mono text-blue-600 hover:underline"
                    >
                      {{ entry.voucher_no }}
                    </button>
                  </td>
                  <td class="px-4 text-gray-500" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    {{ entry.warehouse }}
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span :class="entry.actual_qty > 0 ? 'font-semibold text-green-600' : 'font-semibold text-red-600'">
                      {{ entry.actual_qty > 0 ? '+' : '' }}{{ entry.actual_qty }}
                    </span>
                  </td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="entry.balance >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ entry.balance }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>

      <!-- ── Detail Panel ── -->
      <transition name="slide">
        <div
          v-if="selectedEntry"
          class="flex w-96 shrink-0 flex-col border-l border-gray-200 bg-white"
        >
          <!-- Panel header -->
          <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="rounded px-2 py-0.5 text-[10px] font-bold" :class="voucherBadgeClass(selectedEntry.voucher_type)">
                {{ voucherLabel(selectedEntry.voucher_type) }}
              </span>
              <span class="font-mono text-sm font-bold text-gray-800">{{ selectedEntry.voucher_no }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="selectedEntry.voucher_type === 'Sales Invoice'"
                @click="openInternalSalesEntry(selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-blue-600 hover:bg-blue-50"
              >
                View / Edit
              </button>
              <button
                @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-gray-500 hover:bg-gray-100"
                title="Open in ERPNext"
              >
                ERPNext ↗
              </button>
              <button @click="closeDetail" class="rounded p-1 text-gray-400 hover:bg-gray-100">✕</button>
            </div>
          </div>

          <!-- Loading detail -->
          <div v-if="loadingDetail" class="flex flex-1 items-center justify-center text-sm text-gray-400">
            Loading...
          </div>

          <div v-else-if="voucherDetail" class="flex-1 overflow-y-auto p-4">

            <!-- Key fields -->
            <div class="mb-4 space-y-2 rounded-lg bg-gray-50 p-3 text-xs">
              <div class="flex justify-between">
                <span class="text-gray-500">Date</span>
                <span class="font-semibold">{{ fmtDate(voucherDetail.posting_date) }}</span>
              </div>
              <div v-if="voucherDetail.party_name || voucherDetail.party" class="flex justify-between">
                <span class="text-gray-500">Party</span>
                <span class="font-semibold text-right">{{ voucherDetail.party_name || voucherDetail.party }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Amount</span>
                <span class="font-bold text-gray-800">₹{{ fmt(voucherDetail.total_amount) }}</span>
              </div>
              <div v-if="voucherDetail.remarks" class="pt-1">
                <span class="text-gray-500">Remarks</span>
                <p class="mt-0.5 text-gray-700">{{ voucherDetail.remarks }}</p>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Items
              </div>

              <!-- Sales/Purchase/Credit items -->
              <template v-if="['Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Stock Entry', 'Delivery Note', 'Purchase Receipt'].includes(voucherDetail.voucher_type)">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-gray-200 text-[10px] text-gray-400">
                      <th class="pb-1.5 text-left font-normal">Item</th>
                      <th class="pb-1.5 text-right font-normal">Qty</th>
                      <th class="pb-1.5 text-right font-normal">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, i) in voucherDetail.items" :key="i" class="border-b border-gray-100">
                      <td class="py-1.5">
                        <div class="font-semibold text-gray-800" :class="{ 'text-blue-600': item.item_code === selectedItem?.item_code }">
                          {{ item.item_code }}
                        </div>
                        <div class="text-[10px] text-gray-500">{{ item.item_name }}</div>
                      </td>
                      <td class="py-1.5 text-right text-gray-600">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-1.5 text-right font-mono text-gray-600">₹{{ fmt(item.rate) }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </div>
          </div>
        </div>
      </transition>

    </div>

    <SalesEntry
      v-if="showSalesEntryWindow"
      :is-sub-window="true"
      :invoice-name="subWindowInvoiceName"
      @close="showSalesEntryWindow = false"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="ledgerItemSearchModalRef"
      :show="showItemSearchModal"
      v-model:query="itemSearchQuery"
      v-model:selectedIdx="itemSelectedIdx"
      :results="itemSearchResults"
      @close="showItemSearchModal = false"
      @select="(i, d) => { pickItem(i, d); showItemSearchModal = false }"
      @refresh="refreshItemSearch"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { searchItems, fetchItemDetails, fetchStockLedger, fetchVoucherDetail, frappeGet, fetchBillingSettings } from '../api.js'
import SalesEntry from './SalesEntry.vue'
import ItemSearch from '../components/ItemSearch.vue'

const props = defineProps({
  isSubWindow: {
    type: Boolean,
    default: false
  },
  itemCode: {
    type: String,
    default: ''
  },
  initialFromDate: {
    type: String,
    default: ''
  },
  initialToDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const router = useRouter()
const route = useRoute()

function handleBack() {
  if (props.isSubWindow) {
    emit('close')
  } else {
    router.push('/')
  }
}

const showSalesEntryWindow = ref(false)
const subWindowInvoiceName = ref('')

// ─── Item Search Modal State ──────────────────────────────────────────────
const showItemSearchModal = ref(false)
const itemSearchQuery = ref('')
const allItems = ref([])
const itemSearchResults = ref([])
const itemSelectedIdx = ref(0)
const ledgerItemSearchModalRef = ref(null)
const isItemLoading = ref(false)

async function refreshItemSearch() {
  isItemLoading.value = true
  try {
    const items = await searchItems('')
    allItems.value = items.map(i => ({ ...i, price: 0, stock: 0, _loading: true, enriched: false }))
    filterItems()
  } catch (e) {
    console.error('Item search refresh failed:', e)
  } finally {
    isItemLoading.value = false
  }
}

function filterItems() {
  const q = itemSearchQuery.value.toLowerCase().trim()
  if (!q) {
    itemSearchResults.value = allItems.value.slice(0, 100)
    return
  }
  itemSearchResults.value = allItems.value.filter(i =>
    i.item_code.toLowerCase().includes(q) ||
    i.item_name.toLowerCase().includes(q)
  ).slice(0, 100)
  itemSelectedIdx.value = 0
}

watch(itemSearchQuery, filterItems)

async function openItemSearch() {
  showItemSearchModal.value = true
  if (allItems.value.length === 0) {
    await refreshItemSearch()
  } else {
    filterItems()
  }
  nextTick(() => ledgerItemSearchModalRef.value?.focus())
}

function pickItem(item, dates) {
  selectedItem.value = item
  if (dates) {
    fromDate.value = dates.from
    toDate.value = dates.to
  }
  loadLedger()
}

function clearItem() {
  selectedItem.value = null
  ledgerData.value = null
  error.value = ''
}

// ─── Zoom ─────────────────────────────────────────────────────────────────────
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)
const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`,
  paddingTop: `${(4 * zoomPercent.value) / 100}px`,
  paddingBottom: `${(4 * zoomPercent.value) / 100}px`
}))

watch(zoomPercent, (newZoom) => {
  localStorage.setItem('wb-zoom', newZoom.toString())
})

// ─── Filter state ─────────────────────────────────────────────────────────────
const today = new Date().toISOString().slice(0, 10)
const sevenDaysAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10)

const fromDate = ref(sevenDaysAgo)
const toDate = ref(today)
const selectedItem = ref(null)
const selectedWarehouse = ref('')
const allowedWarehouses = ref([])

// ─── Ledger state ─────────────────────────────────────────────────────────────
const loading = ref(false)
const error = ref('')
const ledgerData = ref(null)

// ─── Detail panel state ───────────────────────────────────────────────────────
const selectedEntry = ref(null)
const voucherDetail = ref(null)
const loadingDetail = ref(false)

// Ledger row keyboard navigation
const focusedIdx = ref(-1)
const tableBodyRef = ref(null)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(n || 0)
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function fmtDate(d) {
  if (!d) return ''
  const date = new Date(d + 'T00:00:00')
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()
  return `${dd}/${mm}/${yyyy}`
}

const VOUCHER_CONFIG = {
  'Sales Invoice':    { label: 'SINV', cls: 'bg-blue-100 text-blue-700' },
  'Purchase Invoice': { label: 'PINV', cls: 'bg-orange-100 text-orange-700' },
  'Stock Entry':      { label: 'SE',   cls: 'bg-purple-100 text-purple-700' },
  'Delivery Note':    { label: 'DN',   cls: 'bg-green-100 text-green-700' },
  'Purchase Receipt': { label: 'PR',   cls: 'bg-amber-100 text-amber-700' },
}

function voucherLabel(type) {
  return VOUCHER_CONFIG[type]?.label ?? type?.slice(0, 4).toUpperCase() ?? '?'
}
function voucherBadgeClass(type) {
  return VOUCHER_CONFIG[type]?.cls ?? 'bg-gray-100 text-gray-600'
}

function openInErpNext(voucherType, voucherNo) {
  const slug = voucherType.toLowerCase().replace(/ /g, '-')
  window.open(`/app/${slug}/${voucherNo}`, '_blank')
}

// ─── Load Ledger ──────────────────────────────────────────────────────────────
async function loadLedger() {
  if (!selectedItem.value) return
  loading.value = true
  error.value = ''
  ledgerData.value = null
  selectedEntry.value = null
  voucherDetail.value = null
  focusedIdx.value = -1

  try {
    ledgerData.value = await fetchStockLedger(
      selectedItem.value.item_code,
      fromDate.value,
      toDate.value,
      selectedWarehouse.value || null
    )
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Auto-reload when filters change
watch(fromDate, () => { if (selectedItem.value) loadLedger() })
watch(toDate,   () => { if (selectedItem.value) loadLedger() })
watch(selectedWarehouse, () => { if (selectedItem.value) loadLedger() })

// ─── Row hover/keyboard → update preview ───────────────────────────────────
let previewTimer = null
async function updatePreview(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx
  if (selectedEntry.value === entry) return

  selectedEntry.value = entry
  voucherDetail.value = null
  
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    loadingDetail.value = true
    try {
      voucherDetail.value = await fetchVoucherDetail(entry.voucher_type, entry.voucher_no)
    } catch (e) {
      voucherDetail.value = { error: e.message }
    } finally {
      loadingDetail.value = false
    }
  }, 150)
}

function onRowMouseEnter(entry, idx) {
  updatePreview(entry, idx)
}

async function onRowClick(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx

  if (entry.voucher_type === 'Sales Invoice') {
    openInternalSalesEntry(entry.voucher_no)
    return
  }

  if (selectedEntry.value === entry && voucherDetail.value) {
    // Already showing
  } else {
    updatePreview(entry, idx)
  }
}

function openInternalSalesEntry(invoiceNo) {
  subWindowInvoiceName.value = invoiceNo
  showSalesEntryWindow.value = true
}

function closeDetail() {
  selectedEntry.value = null
  voucherDetail.value = null
  clearTimeout(previewTimer)
}

// ─── Keyboard navigation for ledger rows ──────────────────────────────────────
function onTableKeydown(e) {
  if (!ledgerData.value?.entries?.length) return
  const len = ledgerData.value.entries.length

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedIdx.value = Math.min(focusedIdx.value + 1, len - 1)
    updatePreview(ledgerData.value.entries[focusedIdx.value], focusedIdx.value)
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIdx.value = Math.max(focusedIdx.value - 1, 0)
    updatePreview(ledgerData.value.entries[focusedIdx.value], focusedIdx.value)
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'Enter' && focusedIdx.value >= 0) {
    e.preventDefault()
    const entry = ledgerData.value.entries[focusedIdx.value]
    if (entry.voucher_type === 'Sales Invoice') {
      openInternalSalesEntry(entry.voucher_no)
    } else {
      onRowClick(entry, focusedIdx.value)
    }
  }
}

function scrollRowIntoView(idx) {
  nextTick(() => {
    const rows = tableBodyRef.value?.querySelectorAll('tr[data-idx]')
    rows?.[idx]?.scrollIntoView({ block: 'nearest' })
  })
}

function onGlobalKeydown(e) {
  if (showSalesEntryWindow.value) return
  if (showItemSearchModal.value) return

  if (e.key === 'Escape') {
    if (selectedEntry.value) {
      e.preventDefault()
      closeDetail()
      return
    }
    if (props.isSubWindow) {
      e.preventDefault()
      handleBack()
      return
    }
  }

  if (e.ctrlKey && e.key === 'i') {
    e.preventDefault()
    openItemSearch()
    return
  }

  if (!ledgerData.value) return
  onTableKeydown(e)
}

onMounted(async () => {
  window.addEventListener('keydown', onGlobalKeydown)

  // Fetch allowed warehouses from billing settings
  try {
    const settings = await fetchBillingSettings()
    if (settings?.billing_series) {
      const warehouses = [...new Set(settings.billing_series.map(s => s.warehouse).filter(Boolean))]
      allowedWarehouses.value = warehouses
      // Set default warehouse if available
      if (warehouses.length > 0) {
        selectedWarehouse.value = warehouses[0]
      }
    }
  } catch (e) {
    console.warn('[StockLedger] Failed to fetch billing settings:', e.message)
  }

  // Apply initial dates if provided
  if (props.initialFromDate) fromDate.value = props.initialFromDate
  if (props.initialToDate) toDate.value = props.initialToDate

  // Auto-load if itemCode is provided
  if (props.itemCode) {
    loading.value = true
    try {
      // Basic fetch to get item name
      const item = await frappeGet('frappe.client.get', {
        doctype: 'Item',
        name: props.itemCode
      })
      if (item) {
        selectedItem.value = {
          item_code: item.name,
          item_name: item.item_name
        }
        loadLedger()
      }
    } catch (e) {
      console.warn('[StockLedger] Failed to auto-load item:', e.message)
    } finally {
      loading.value = false
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
