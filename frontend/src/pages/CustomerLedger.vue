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
          <h1 class="text-sm font-bold text-gray-800">Customer Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-600">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info for sub-window -->
        <div v-if="isSubWindow" class="flex items-center gap-4 text-[10px] text-gray-400">
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono">Ctrl+L</kbd> Search</span>
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

        <!-- Customer search -->
        <div class="relative w-64">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-gray-400">
            <span>Customer</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-gray-200 bg-gray-50 px-1 font-mono text-[9px]">Ctrl+L</kbd> Search
            </span>
          </label>
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

              <!-- Sales/Purchase/Credit items -->
              <template v-if="['Sales Invoice', 'Purchase Invoice', 'Credit Note'].includes(voucherDetail.voucher_type)">
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

    <StockLedger
      v-if="showStockLedgerWindow"
      :is-sub-window="true"
      :item-code="stockLedgerItemCode"
      :initial-from-date="stockLedgerFromDate"
      :initial-to-date="stockLedgerToDate"
      @close="showStockLedgerWindow = false"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="ledgerCustSearchModalRef"
      :show="showCustomerSearchModal"
      @close="closeCustomerSearchModal"
      @select="(c, d) => { pickCustomer(c, d); closeCustomerSearchModal() }"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="ledgerItemSearchModalRef"
      :show="showItemSearchModal"
      v-model:query="itemSearchQuery"
      v-model:selectedIdx="itemDDIdx"
      :results="itemSearchResults"
      @close="closeItemSearch"
      @select="pickItem"
      @refresh="refreshItemSearch"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchCustomerLedger, fetchVoucherDetail, frappeGet } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import SalesEntry from './SalesEntry.vue'
import StockLedger from './StockLedger.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import ItemSearch from '../components/ItemSearch.vue'
import { createCustomer, updateCustomer } from '../api/customer.js'
import { searchItems } from '../api.js'

const props = defineProps({
  isSubWindow: {
    type: Boolean,
    default: false
  },
  customerName: {
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

// ─── Stock Ledger Sub-window ──────────────────────────────────────────────────
const showStockLedgerWindow = ref(false)
const stockLedgerItemCode = ref('')
const stockLedgerFromDate = ref('')
const stockLedgerToDate = ref('')

function openStockLedger(itemCode, dates = null) {
  stockLedgerItemCode.value = itemCode
  if (dates) {
    stockLedgerFromDate.value = dates.from
    stockLedgerToDate.value = dates.to
  } else {
    stockLedgerFromDate.value = ''
    stockLedgerToDate.value = ''
  }
  showStockLedgerWindow.value = true
}

// ─── Item Search Modal State ──────────────────────────────────────────────────
const showItemSearchModal = ref(false)
const itemSearchQuery = ref('')
const allItems = ref([])
const itemSearchResults = ref([])
const itemDDIdx = ref(0)
const ledgerItemSearchModalRef = ref(null)
const isItemLoading = ref(false)

async function refreshItemSearch() {
  isItemLoading.value = true
  try {
    const items = await searchItems('')
    allItems.value = items.map(i => ({ 
      ...i, 
      price: 0, 
      stock: 0, 
      _loading: true,
      enriched: false 
    }))
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
  itemDDIdx.value = 0
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

function closeItemSearch() {
  showItemSearchModal.value = false
}

function pickItem(item, dates) {
  showItemSearchModal.value = false
  openStockLedger(item.item_code, dates)
}

// ─── Customer Search Modal State ──────────────────────────────────────────────
const showCustomerSearchModal = ref(false)
const custSearchQuery = ref('')
const custSearchResults = ref([])
const custSelectedIdx = ref(0)
const newCustSaving = ref(false)
const isCustLoading = ref(false)

let _custDebounce = null
watch(custSearchQuery, (q) => {
  clearTimeout(_custDebounce)
  if (!q.trim()) {
    custSearchResults.value = []
    return
  }
  isCustLoading.value = true
  _custDebounce = setTimeout(async () => {
    try {
      custSearchResults.value = await searchCustomers(q)
      custSelectedIdx.value = 0
    } catch (e) {
      console.error('Customer search failed:', e)
    } finally {
      isCustLoading.value = false
    }
  }, 300)
})

function openCustomerSearch() {
  showCustomerSearchModal.value = true
  custSearchQuery.value = customerQuery.value
}

function closeCustomerSearchModal() {
  showCustomerSearchModal.value = false
}

async function refreshCustSearch() {
  if (!custSearchQuery.value.trim()) return
  isCustLoading.value = true
  try {
    custSearchResults.value = await searchCustomers(custSearchQuery.value)
  } catch (e) {
    console.error('Customer search refresh failed:', e)
  } finally {
    isCustLoading.value = false
  }
}

async function saveEditCust(data) {
  if (!data.customer_name.trim()) { alert('Customer name is required'); return }
  newCustSaving.value = true
  try {
    const customerId = data.name || selectedCustomer.value?.name
    const res = await updateCustomer(customerId, data)
    if (selectedCustomer.value && selectedCustomer.value.name === customerId) {
      selectedCustomer.value = { ...selectedCustomer.value, ...res }
      customerQuery.value = res.customer_name
    }
    refreshCustSearch()
    alert(`Customer ${res.customer_name} updated successfully!`)
  } catch (e) { 
    alert('Error: ' + (e?.message || 'Unknown')) 
  }
  newCustSaving.value = false
}

async function saveNewCust(data) {
  if (!data.customer_name.trim()) { alert('Customer name is required'); return }
  newCustSaving.value = true
  try {
    const res = await createCustomer(data)
    pickCustomer({ name: res.name, customer_name: res.customer_name })
    showCustomerSearchModal.value = false
  } catch (e) { alert('Error: ' + (e?.message || 'Unknown')) }
  newCustSaving.value = false
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
  const date = new Date(d + 'T00:00:00')
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()
  return `${dd}/${mm}/${yyyy}`
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
  }, 150) // Small debounce for hover/keyboard speed
}

function onRowMouseEnter(entry, idx) {
  updatePreview(entry, idx)
}

// ─── Row click/Enter → open SalesEntry if invoice ─────────────────────────────
async function onRowClick(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx

  if (entry.voucher_type === 'Sales Invoice') {
    openInternalSalesEntry(entry.voucher_no)
    return
  }

  // If not invoice, toggle/ensure preview is open
  if (selectedEntry.value === entry && voucherDetail.value) {
    // Already showing, do nothing or could closeDetail() if toggle preferred
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
      // For other types, Enter just ensures preview is loaded immediately (no debounce)
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
  if (showCustomerSearchModal.value || showItemSearchModal.value) {
    if (e.key === 'Escape') {
      if (showCustomerSearchModal.value) closeCustomerSearchModal()
      if (showItemSearchModal.value) closeItemSearch()
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

  // Only handle arrow/enter when customer input is not focused and ledger is loaded
  if (document.activeElement === customerInputRef.value) return
  if (!ledgerData.value) return
  onTableKeydown(e)
}

onMounted(async () => {
  nextTick(() => customerInputRef.value?.focus())
  window.addEventListener('keydown', onGlobalKeydown)

  // Apply initial dates if provided
  if (props.initialFromDate) fromDate.value = props.initialFromDate
  if (props.initialToDate) toDate.value = props.initialToDate

  // Auto-load if customer is in query params (or prop)
  const targetCust = props.customerName || route.query.customer
  if (targetCust) {
    loading.value = true
    try {
      const cust = await frappeGet('frappe.client.get', {
        doctype: 'Customer',
        name: targetCust
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
