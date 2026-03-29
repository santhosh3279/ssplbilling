<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'flex min-h-screen flex-col bg-slate-900'">
    <div class="flex h-full flex-col">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="handleBack"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200"
          >
            ← {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <span class="text-slate-600">|</span>
          <h1 class="text-sm font-bold text-slate-100">Stock Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-blue-900/20 px-2 py-0.5 text-[10px] font-semibold text-blue-400">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info for sub-window -->
        <div v-if="isSubWindow" class="flex items-center gap-4 text-[10px] text-slate-400">
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Ctrl+I</kbd> Item Search</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Esc</kbd> Close</span>
        </div>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-slate-700 bg-slate-800 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-slate-500 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-slate-300 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex flex-wrap items-end gap-3">

        <!-- Item search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            <span>Item</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-slate-600 bg-slate-700 px-1 font-mono text-[9px] text-slate-300">Ctrl+I</kbd> Search
            </span>
          </label>
          <div
            @click="openItemSearch"
            class="w-full cursor-pointer rounded border px-3 py-2 text-sm outline-none transition-colors hover:border-blue-500"
            :class="selectedItem ? 'border-blue-500 bg-blue-900/20 font-semibold text-blue-300' : 'border-slate-600 bg-slate-800 text-slate-500'"
          >
            {{ selectedItem ? `${selectedItem.item_code} - ${selectedItem.item_name}` : 'Select an item...' }}
          </div>
          <!-- Clear button -->
          <button
            v-if="selectedItem"
            @click="clearItem"
            class="absolute right-2 top-7 text-slate-400 hover:text-slate-200"
          >
            ✕
          </button>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">From</label>
          <input
            ref="dateInput"
            v-model="fromDate"
            type="date"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
          />
        </div>

        <!-- Warehouse filter -->
        <div class="w-48">
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">Warehouse</label>
          <select
            v-model="selectedWarehouse"
            class="w-full rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
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
            : 'bg-slate-700 text-slate-500 cursor-not-allowed'"
        >
          {{ loading ? 'Loading...' : 'Load Ledger' }}
        </button>

        <!-- Summary chips -->
        <template v-if="ledgerData">
          <div class="ml-2 flex items-center gap-2">
            <div class="flex flex-col rounded bg-amber-900/20 px-3 py-1 border border-amber-800">
              <span class="text-[9px] font-bold uppercase text-amber-400 leading-none">Opening</span>
              <span class="text-sm font-bold text-amber-300 leading-tight">{{ ledgerData.opening_balance }}</span>
            </div>
            <div class="flex flex-col rounded bg-green-900/20 px-3 py-1 border border-green-800">
              <span class="text-[9px] font-bold uppercase text-green-400 leading-none">Purchase (In)</span>
              <span class="text-sm font-bold text-green-300 leading-tight">+{{ ledgerData.total_in }}</span>
            </div>
            <div class="flex flex-col rounded bg-red-900/20 px-3 py-1 border border-red-800">
              <span class="text-[9px] font-bold uppercase text-red-400 leading-none">Sale (Out)</span>
              <span class="text-sm font-bold text-red-300 leading-tight">-{{ ledgerData.total_out }}</span>
            </div>
            <div class="flex flex-col rounded bg-blue-900/20 px-3 py-1 border border-blue-800">
              <span class="text-[9px] font-bold uppercase text-blue-400 leading-none">Closing</span>
              <span class="text-sm font-bold text-blue-300 leading-tight">{{ ledgerData.closing_balance }}</span>
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
        <div v-if="!ledgerData && !loading && !error" class="flex flex-1 flex-col items-center justify-center gap-2 text-slate-500">
          <div class="text-4xl">📦</div>
          <div class="text-sm font-semibold">Select an item and load the stock ledger</div>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center text-sm text-slate-400">
          Loading ledger...
        </div>

        <div v-else-if="error" class="m-6 rounded-lg border border-red-700 bg-red-900/20 px-4 py-3 text-sm text-red-400">
          {{ error }}
        </div>

        <template v-else-if="ledgerData">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
              <thead class="sticky top-0 z-10 bg-slate-800">
                <tr class="border-b border-slate-700">
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-slate-400">Date</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-slate-400">Type</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-slate-400">Voucher No</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-slate-400">Warehouse</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-slate-400">Qty</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-slate-400">UOM</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-slate-400">Balance</th>
                </tr>
              </thead>
              <tbody ref="tableBodyRef">
                <!-- No entries message -->
                <tr v-if="!ledgerData.entries.length">
                  <td colspan="7" class="px-4 py-12 text-center text-slate-500">
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
                  class="cursor-pointer border-b border-slate-700 transition-colors"
                  :class="focusedIdx === idx
                    ? 'bg-blue-900/30 outline outline-1 outline-blue-500'
                    : selectedEntry === entry
                      ? 'bg-blue-900/20'
                      : 'hover:bg-slate-800/40'"
                >
                  <td class="px-4 text-slate-400" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ fmtDate(entry.date) }}</td>
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
                      class="font-mono text-blue-400 hover:underline"
                    >
                      {{ entry.voucher_no }}
                    </button>
                  </td>
                  <td class="px-4 text-slate-400" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    {{ entry.warehouse }}
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span :class="entry.actual_qty > 0 ? 'font-semibold text-green-400' : 'font-semibold text-red-400'">
                      {{ entry.actual_qty > 0 ? '+' : '' }}{{ entry.actual_qty }}
                    </span>
                  </td>
                  <td class="px-4 text-slate-400" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    {{ entry.stock_uom }}
                  </td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="entry.balance >= 0 ? 'text-green-400' : 'text-red-400'">
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
          class="flex w-96 shrink-0 flex-col border-l border-slate-700 bg-slate-800"
        >
          <!-- Panel header -->
          <div class="flex items-center justify-between border-b border-slate-700 px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="rounded px-2 py-0.5 text-[10px] font-bold" :class="voucherBadgeClass(selectedEntry.voucher_type)">
                {{ voucherLabel(selectedEntry.voucher_type) }}
              </span>
              <span class="font-mono text-sm font-bold text-slate-100">{{ selectedEntry.voucher_no }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="selectedEntry.voucher_type === 'Sales Invoice'"
                @click="openInternalSalesEntry(selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-blue-400 hover:bg-blue-900/20"
              >
                View / Edit
              </button>
              <button
                @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-slate-400 hover:bg-slate-700"
                title="Open in ERPNext"
              >
                ERPNext ↗
              </button>
              <button @click="closeDetail" class="rounded p-1 text-slate-400 hover:bg-slate-700">✕</button>
            </div>
          </div>

          <!-- Loading detail -->
          <div v-if="voucherDetail" class="flex-1 overflow-y-auto p-4">

            <!-- Key fields -->
            <div class="mb-4 space-y-2 rounded-lg bg-slate-700 p-3 text-xs">
              <div class="flex justify-between">
                <span class="text-slate-400">Date</span>
                <span class="font-semibold text-slate-200">{{ fmtDate(voucherDetail.posting_date) }}</span>
              </div>
              <div v-if="voucherDetail.party_name || voucherDetail.party" class="flex justify-between">
                <span class="text-slate-400">Party</span>
                <span class="font-semibold text-slate-200 text-right">{{ voucherDetail.party_name || voucherDetail.party }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Amount</span>
                <span class="font-bold text-slate-100">₹{{ fmt(voucherDetail.total_amount) }}</span>
              </div>
              <div v-if="voucherDetail.remarks" class="pt-1">
                <span class="text-slate-400">Remarks</span>
                <p class="mt-0.5 text-slate-300">{{ voucherDetail.remarks }}</p>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Items
              </div>

              <!-- Sales/Purchase/Credit items -->
              <template v-if="['Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Stock Entry', 'Delivery Note', 'Purchase Receipt'].includes(voucherDetail.voucher_type)">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-slate-700 text-[10px] text-slate-400">
                      <th class="pb-1.5 text-left font-normal">Item</th>
                      <th class="pb-1.5 text-right font-normal">Qty</th>
                      <th class="pb-1.5 text-right font-normal">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, i) in voucherDetail.items" :key="i" class="border-b border-slate-700">
                      <td class="py-1.5">
                        <div class="font-semibold text-slate-200" :class="{ 'text-blue-400': item.item_code === selectedItem?.item_code }">
                          {{ item.item_code }}
                        </div>
                        <div class="text-[10px] text-slate-400">{{ item.item_name }}</div>
                      </td>
                      <td class="py-1.5 text-right text-slate-300">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-1.5 text-right font-mono text-slate-300">₹{{ fmt(item.rate) }}</td>
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

    <CustomerLedger
      v-if="showCustomerLedgerWindow"
      :is-sub-window="true"
      :customer-name="ledgerCustomerName"
      :initial-from-date="ledgerFromDate"
      :initial-to-date="ledgerToDate"
      @close="showCustomerLedgerWindow = false"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="ledgerItemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Stock"
      :skip-date-filter="true"
      @close="showItemSearchModal = false"
      @select="pickItem"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="ledgerCustSearchModalRef"
      :show="showCustomerSearchModal"
      @close="closeCustomerSearchModal"
      @select="pickCustomer"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchStockLedger, frappeGet } from '../api.js'
import SalesEntry from './SalesEntry.vue'
import CustomerLedger from './CustomerLedger.vue'
import ItemSearch from '../components/ItemSearch.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useSubwindow } from '../services/shortcutManager'

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

if (props.isSubWindow) useSubwindow()

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

// ─── Customer Ledger Sub-window ──────────────────────────────────────────────
const showCustomerLedgerWindow = ref(false)
const ledgerCustomerName = ref('')
const ledgerFromDate = ref('')
const ledgerToDate = ref('')

function openCustomerLedger(customerName, dates = null) {
  ledgerCustomerName.value = customerName
  if (dates) {
    ledgerFromDate.value = dates.from
    ledgerToDate.value = dates.to
  } else {
    ledgerFromDate.value = ''
    ledgerToDate.value = ''
  }
  showCustomerLedgerWindow.value = true
}

// ─── Item Search Modal State ──────────────────────────────────────────────
const showItemSearchModal = ref(false)
const ledgerItemSearchModalRef = ref(null)

function openItemSearch() {
  showItemSearchModal.value = true
  nextTick(() => ledgerItemSearchModalRef.value?.focus())
}

function pickItem(item, dates) {
  showItemSearchModal.value = false
  selectedItem.value = item
  if (dates) {
    fromDate.value = dates.from
    toDate.value = dates.to
  }
  loadLedger()
}

// ─── Customer Search Modal State ──────────────────────────────────────────────
const showCustomerSearchModal = ref(false)
const ledgerCustSearchModalRef = ref(null)

async function openCustomerSearch() {
  showCustomerSearchModal.value = true
  nextTick(() => {
    ledgerCustSearchModalRef.value?.closeSubForm()
    ledgerCustSearchModalRef.value?.focus()
  })
}

function closeCustomerSearchModal() {
  showCustomerSearchModal.value = false
}

function pickCustomer(c, dates) {
  showCustomerSearchModal.value = false
  openCustomerLedger(c.name, dates)
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

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

function getSevenDaysAgoIST() {
  const date = new Date(Date.now() - 7 * 86400000)
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ─── Filter state ─────────────────────────────────────────────────────────────
const today = getTodayIST()
const sevenDaysAgo = getSevenDaysAgoIST()

const fromDate = ref(sevenDaysAgo)
const toDate = ref(today)
const dateInput = ref(null)
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
  'Sales Invoice':    { label: 'SINV', cls: 'bg-blue-900/20 text-blue-400' },
  'Purchase Invoice': { label: 'PINV', cls: 'bg-orange-900/20 text-orange-400' },
  'Stock Entry':      { label: 'SE',   cls: 'bg-purple-900/20 text-purple-400' },
  'Delivery Note':    { label: 'DN',   cls: 'bg-green-900/20 text-green-400' },
  'Purchase Receipt': { label: 'PR',   cls: 'bg-amber-900/20 text-amber-400' },
}

function voucherLabel(type) {
  return VOUCHER_CONFIG[type]?.label ?? type?.slice(0, 4).toUpperCase() ?? '?'
}
function voucherBadgeClass(type) {
  return VOUCHER_CONFIG[type]?.cls ?? 'bg-slate-700 text-slate-400'
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

// ─── Row hover/keyboard → update preview (no API calls — detail pre-loaded) ──
function updatePreview(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx
  if (selectedEntry.value === entry) return
  selectedEntry.value = entry
  voucherDetail.value = entry.detail || null
}

function onRowMouseEnter(entry, idx) {
  updatePreview(entry, idx)
}

function onRowClick(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx
  if (entry.voucher_type === 'Sales Invoice') {
    openInternalSalesEntry(entry.voucher_no)
    return
  }
  updatePreview(entry, idx)
}

function openInternalSalesEntry(invoiceNo) {
  subWindowInvoiceName.value = invoiceNo
  showSalesEntryWindow.value = true
}

function closeDetail() {
  selectedEntry.value = null
  voucherDetail.value = null
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
  if (showItemSearchModal.value || showCustomerSearchModal.value) {
    if (e.key === 'Escape') {
      if (showItemSearchModal.value) showItemSearchModal.value = false
      if (showCustomerSearchModal.value) closeCustomerSearchModal()
    }
    return
  }

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

  if (e.ctrlKey && e.key === 'l') {
    e.preventDefault()
    openCustomerSearch()
    return
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
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('keydown', onGlobalKeydown)

  // Load all warehouses from ERPNext, auto-select user's default
  try {
    const warehouses = await frappeGet('ssplbilling.api.ledger_api.get_warehouses')
    if (warehouses?.length) {
      allowedWarehouses.value = warehouses
      const defaultWh = localStorage.getItem('wb-warehouse') || ''
      selectedWarehouse.value = warehouses.includes(defaultWh) ? defaultWh : warehouses[0]
    }
  } catch (e) {
    console.warn('[StockLedger] Failed to load warehouses:', e.message)
    // Fallback to localStorage
    const wh = localStorage.getItem('wb-warehouse') || ''
    if (wh) { allowedWarehouses.value = [wh]; selectedWarehouse.value = wh }
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
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
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
