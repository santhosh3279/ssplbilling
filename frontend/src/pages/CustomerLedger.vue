<template>
  <div class="flex min-h-screen flex-col bg-gray-50">

    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-gray-200 bg-white px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="$router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            ← Dashboard
          </button>
          <span class="text-gray-300">|</span>
          <h1 class="text-sm font-bold text-gray-800">Customer Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-600">
            {{ ledgerData.entries.length }} entries
          </span>
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

        <!-- Customer search -->
        <div class="relative w-64">
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-gray-400">Customer</label>
          <input
            ref="customerInputRef"
            v-model="customerQuery"
            @input="onCustomerSearch"
            @keydown.down.prevent="cursorDown"
            @keydown.up.prevent="cursorUp"
            @keydown.enter.prevent="pickCursor"
            @keydown.escape="customerDropdownOpen = false"
            @blur="onCustomerBlur"
            placeholder="Search customer..."
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500"
            :class="selectedCustomer ? 'bg-blue-50 font-semibold text-blue-800' : 'bg-white text-gray-800'"
            autocomplete="off"
          />
          <!-- Dropdown -->
          <ul
            v-if="customerDropdownOpen && customerOptions.length"
            class="absolute z-50 mt-1 max-h-48 w-full overflow-y-auto rounded border border-gray-200 bg-white shadow-lg"
          >
            <li
              v-for="(c, idx) in customerOptions"
              :key="c.name"
              @mousedown.prevent="pickCustomer(c)"
              class="cursor-pointer px-3 py-2 text-xs"
              :class="cursor === idx ? 'bg-blue-50' : 'hover:bg-gray-50'"
            >
              <div class="font-semibold text-gray-800">{{ c.customer_name }}</div>
              <div class="font-mono text-[10px] text-gray-400">{{ c.name }}</div>
            </li>
          </ul>
          <!-- Clear button -->
          <button
            v-if="selectedCustomer"
            @click="clearCustomer"
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

        <button
          @click="loadLedger"
          :disabled="!selectedCustomer || loading"
          class="rounded-lg px-5 py-2 text-sm font-semibold transition-colors"
          :class="selectedCustomer && !loading
            ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
        >
          {{ loading ? 'Loading...' : 'Load Ledger' }}
        </button>

        <!-- Summary chips (visible after load) -->
        <template v-if="ledgerData">
          <div class="ml-2 flex items-center gap-3 text-xl">
            <span class="rounded bg-orange-50 px-3 py-1.5 font-semibold text-orange-700">
              Opening ₹{{ fmt(Math.abs(ledgerData.opening_balance)) }} {{ ledgerData.opening_balance < 0 ? '(Cr)' : '(Dr)' }}
            </span>
            <span class="rounded bg-red-50 px-3 py-1.5 font-semibold text-red-700">
              Dr ₹{{ fmt(ledgerData.total_debit) }}
            </span>
            <span class="rounded bg-green-50 px-3 py-1.5 font-semibold text-green-700">
              Cr ₹{{ fmt(ledgerData.total_credit) }}
            </span>
            <span
              class="rounded px-3 py-1.5 font-bold"
              :class="ledgerData.closing_balance >= 0 ? 'bg-orange-50 text-orange-700' : 'bg-green-50 text-green-700'"
            >
              Balance ₹{{ fmt(Math.abs(ledgerData.closing_balance)) }}
              {{ ledgerData.closing_balance < 0 ? '(Cr)' : '(Dr)' }}
            </span>
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
          <div class="text-4xl">📋</div>
          <div class="text-sm font-semibold">Select a customer and load the ledger</div>
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
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-gray-400">Debit (Dr)</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-gray-400">Credit (Cr)</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-gray-400">Balance</th>
                </tr>
              </thead>
              <tbody ref="tableBodyRef">
                <!-- Opening Balance row -->
                <tr class="border-b border-gray-100 bg-gray-50">
                  <td colspan="5" class="px-4 font-semibold text-gray-500" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    Opening Balance
                    <span class="ml-1 font-normal text-gray-400" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">(before {{ fmtDate(ledgerData.from_date) }})</span>
                  </td>
                  <td class="px-4 text-right font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="ledgerData.opening_balance >= 0 ? 'text-orange-600' : 'text-green-600'">
                    ₹{{ fmt(Math.abs(ledgerData.opening_balance)) }}
                    <span class="ml-0.5 font-normal" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ ledgerData.opening_balance < 0 ? 'Cr' : 'Dr' }}</span>
                  </td>
                </tr>

                <!-- No entries message -->
                <tr v-if="!ledgerData.entries.length">
                  <td colspan="6" class="px-4 py-12 text-center text-gray-400">
                    No transactions found for the selected period.
                  </td>
                </tr>

                <!-- Ledger rows -->
                <tr
                  v-for="(entry, idx) in ledgerData.entries"
                  :key="idx"
                  :data-idx="idx"
                  @click="onRowClick(entry, idx)"
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
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="entry.debit" class="font-semibold text-red-600">₹{{ fmt(entry.debit) }}</span>
                    <span v-else class="text-gray-300">—</span>
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="entry.credit" class="font-semibold text-green-600">₹{{ fmt(entry.credit) }}</span>
                    <span v-else class="text-gray-300">—</span>
                  </td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="entry.balance < 0 ? 'text-green-700' : 'text-gray-800'">
                    ₹{{ fmt(Math.abs(entry.balance)) }}
                    <span class="ml-0.5 font-normal text-gray-400" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ entry.balance < 0 ? 'Cr' : 'Dr' }}</span>
                  </td>
                </tr>

                <!-- Closing Balance row -->
                <tr v-if="ledgerData.entries.length" class="border-t-2 border-gray-300 bg-gray-50">
                  <td colspan="3" class="px-4 font-bold text-gray-600" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">Closing Balance</td>
                  <td class="px-4 text-right font-mono font-bold text-red-600" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">₹{{ fmt(ledgerData.total_debit) }}</td>
                  <td class="px-4 text-right font-mono font-bold text-green-600" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">₹{{ fmt(ledgerData.total_credit) }}</td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="ledgerData.closing_balance < 0 ? 'text-green-700' : 'text-orange-700'">
                    ₹{{ fmt(Math.abs(ledgerData.closing_balance)) }}
                    <span class="ml-0.5 font-normal" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ ledgerData.closing_balance < 0 ? 'Cr' : 'Dr' }}</span>
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
                @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-blue-600 hover:bg-blue-50"
                title="Open in ERPNext"
              >
                Open ↗
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
              <div v-if="voucherDetail.mode_of_payment" class="flex justify-between">
                <span class="text-gray-500">Mode</span>
                <span class="font-semibold">{{ voucherDetail.mode_of_payment }}</span>
              </div>
              <div v-if="voucherDetail.outstanding_amount !== undefined" class="flex justify-between">
                <span class="text-gray-500">Outstanding</span>
                <span class="font-semibold" :class="voucherDetail.outstanding_amount > 0 ? 'text-red-600' : 'text-green-600'">
                  ₹{{ fmt(voucherDetail.outstanding_amount) }}
                </span>
              </div>
              <div v-if="voucherDetail.status" class="flex justify-between">
                <span class="text-gray-500">Status</span>
                <span class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                  :class="{
                    'bg-green-100 text-green-700': ['Paid', 'Submitted'].includes(voucherDetail.status),
                    'bg-yellow-100 text-yellow-700': voucherDetail.status === 'Unpaid',
                    'bg-blue-100 text-blue-700': voucherDetail.status === 'Partly Paid',
                    'bg-gray-100 text-gray-600': !['Paid','Submitted','Unpaid','Partly Paid'].includes(voucherDetail.status),
                  }"
                >
                  {{ voucherDetail.status }}
                </span>
              </div>
              <div v-if="voucherDetail.remarks" class="pt-1">
                <span class="text-gray-500">Remarks</span>
                <p class="mt-0.5 text-gray-700">{{ voucherDetail.remarks }}</p>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">
                {{ voucherDetail.voucher_type === 'Payment Entry' ? 'References' :
                   voucherDetail.voucher_type === 'Journal Entry' ? 'Accounts' : 'Items' }}
              </div>

              <!-- Sales Invoice items -->
              <template v-if="voucherDetail.voucher_type === 'Sales Invoice'">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-gray-200 text-[10px] text-gray-400">
                      <th class="pb-1.5 text-left font-normal">Item</th>
                      <th class="pb-1.5 text-right font-normal">Qty</th>
                      <th class="pb-1.5 text-right font-normal">Rate</th>
                      <th class="pb-1.5 text-right font-normal">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, i) in voucherDetail.items" :key="i" class="border-b border-gray-100">
                      <td class="py-1.5">
                        <div class="font-semibold text-gray-800">{{ item.item_code }}</div>
                        <div class="text-[10px] text-gray-500">{{ item.item_name }}</div>
                      </td>
                      <td class="py-1.5 text-right text-gray-600">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-1.5 text-right font-mono text-gray-600">₹{{ fmt(item.rate) }}</td>
                      <td class="py-1.5 text-right font-mono font-semibold text-gray-800">₹{{ fmt(item.amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>

              <!-- Payment Entry references -->
              <template v-else-if="voucherDetail.voucher_type === 'Payment Entry'">
                <div v-for="(ref, i) in voucherDetail.items" :key="i"
                  class="mb-1.5 flex items-center justify-between rounded bg-gray-50 px-3 py-2 text-xs">
                  <div>
                    <span class="text-[10px] text-gray-500">{{ ref.reference_doctype }}</span>
                    <button
                      @click="openInErpNext(ref.reference_doctype, ref.reference_name)"
                      class="ml-1 font-mono text-blue-600 hover:underline"
                    >{{ ref.reference_name }}</button>
                  </div>
                  <span class="font-mono font-semibold text-green-700">₹{{ fmt(ref.allocated_amount) }}</span>
                </div>
              </template>

              <!-- Journal Entry accounts -->
              <template v-else-if="voucherDetail.voucher_type === 'Journal Entry'">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-gray-200 text-[10px] text-gray-400">
                      <th class="pb-1.5 text-left font-normal">Account</th>
                      <th class="pb-1.5 text-right font-normal">Dr</th>
                      <th class="pb-1.5 text-right font-normal">Cr</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(acc, i) in voucherDetail.items" :key="i" class="border-b border-gray-100">
                      <td class="py-1.5 text-gray-700">{{ acc.account }}</td>
                      <td class="py-1.5 text-right font-mono text-red-600">
                        <span v-if="acc.debit">₹{{ fmt(acc.debit) }}</span>
                        <span v-else class="text-gray-300">—</span>
                      </td>
                      <td class="py-1.5 text-right font-mono text-green-600">
                        <span v-if="acc.credit">₹{{ fmt(acc.credit) }}</span>
                        <span v-else class="text-gray-300">—</span>
                      </td>
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
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { searchCustomers, fetchCustomerLedger, fetchVoucherDetail, frappeGet } from '../api.js'
import SalesEntry from './SalesEntry.vue'

const router = useRouter()
const route = useRoute()

const showSalesEntryWindow = ref(false)
const subWindowInvoiceName = ref('')

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
const ninetyDaysAgo = new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10)

const customerQuery = ref('')
const customerOptions = ref([])
const customerDropdownOpen = ref(false)
const selectedCustomer = ref(null)
const cursor = ref(-1)
const fromDate = ref(ninetyDaysAgo)
const toDate = ref(today)

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

// DOM refs
const customerInputRef = ref(null)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(n || 0)
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function fmtDate(d) {
  if (!d) return ''
  return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

const VOUCHER_CONFIG = {
  'Sales Invoice':    { label: 'SINV', cls: 'bg-blue-100 text-blue-700' },
  'Payment Entry':    { label: 'PAY',  cls: 'bg-green-100 text-green-700' },
  'Journal Entry':    { label: 'JE',   cls: 'bg-gray-100 text-gray-600' },
  'Purchase Invoice': { label: 'PINV', cls: 'bg-orange-100 text-orange-700' },
  'Credit Note':      { label: 'CN',   cls: 'bg-purple-100 text-purple-700' },
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

// ─── Customer search ──────────────────────────────────────────────────────────
let searchTimer = null
function onCustomerSearch() {
  selectedCustomer.value = null
  cursor.value = -1
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!customerQuery.value.trim()) { customerOptions.value = []; customerDropdownOpen.value = false; return }
    try {
      customerOptions.value = await searchCustomers(customerQuery.value)
      customerDropdownOpen.value = !!customerOptions.value.length
    } catch { customerOptions.value = [] }
  }, 220)
}

function pickCustomer(c) {
  selectedCustomer.value = c
  customerQuery.value = c.customer_name
  customerOptions.value = []
  customerDropdownOpen.value = false
  cursor.value = -1
  loadLedger()
}

function clearCustomer() {
  selectedCustomer.value = null
  customerQuery.value = ''
  customerOptions.value = []
  customerDropdownOpen.value = false
  ledgerData.value = null
  error.value = ''
  nextTick(() => customerInputRef.value?.focus())
}

function cursorDown() {
  if (!customerDropdownOpen.value) return
  cursor.value = Math.min(cursor.value + 1, customerOptions.value.length - 1)
}
function cursorUp() {
  cursor.value = Math.max(cursor.value - 1, 0)
}
function pickCursor() {
  if (cursor.value >= 0 && customerOptions.value[cursor.value]) {
    pickCustomer(customerOptions.value[cursor.value])
  }
}
function onCustomerBlur() {
  setTimeout(() => { customerDropdownOpen.value = false }, 150)
}

// ─── Load Ledger ──────────────────────────────────────────────────────────────
async function loadLedger() {
  if (!selectedCustomer.value) return
  loading.value = true
  error.value = ''
  ledgerData.value = null
  selectedEntry.value = null
  voucherDetail.value = null
  focusedIdx.value = -1

  try {
    ledgerData.value = await fetchCustomerLedger(
      selectedCustomer.value.name,
      fromDate.value,
      toDate.value,
    )
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Auto-reload when dates change (only if customer already selected)
watch(fromDate, () => { if (selectedCustomer.value) loadLedger() })
watch(toDate,   () => { if (selectedCustomer.value) loadLedger() })

// ─── Row click → detail panel or SalesEntry ───────────────────────────────────
async function onRowClick(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx

  if (entry.voucher_type === 'Sales Invoice') {
    subWindowInvoiceName.value = entry.voucher_no
    showSalesEntryWindow.value = true
    return
  }

  if (selectedEntry.value === entry) {
    closeDetail()
    return
  }
  selectedEntry.value = entry
  voucherDetail.value = null
  loadingDetail.value = true
  try {
    voucherDetail.value = await fetchVoucherDetail(entry.voucher_type, entry.voucher_no)
  } catch (e) {
    voucherDetail.value = { error: e.message }
  } finally {
    loadingDetail.value = false
  }
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
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIdx.value = Math.max(focusedIdx.value - 1, 0)
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'Enter' && focusedIdx.value >= 0) {
    e.preventDefault()
    onRowClick(ledgerData.value.entries[focusedIdx.value], focusedIdx.value)
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
  // Only handle arrow/enter when customer input is not focused and ledger is loaded
  if (document.activeElement === customerInputRef.value) return
  if (!ledgerData.value) return
  onTableKeydown(e)
}

onMounted(async () => {
  nextTick(() => customerInputRef.value?.focus())
  window.addEventListener('keydown', onGlobalKeydown)

  // Auto-load if customer is in query params
  if (route.query.customer) {
    loading.value = true
    try {
      const cust = await frappeGet('frappe.client.get', {
        doctype: 'Customer',
        name: route.query.customer
      })
      if (cust) {
        selectedCustomer.value = {
          name: cust.name,
          customer_name: cust.customer_name
        }
        customerQuery.value = cust.customer_name
        loadLedger()
      }
    } catch (e) {
      console.warn('[Ledger] Failed to auto-load customer:', e.message)
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
