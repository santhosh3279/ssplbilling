<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-[var(--color-bg)]' : 'flex min-h-screen flex-col bg-[var(--color-bg)]'">
    <div class="flex h-full flex-col">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="handleBack"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-bold text-[var(--color-text)]">Stock Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-[var(--color-info)]/20 px-2 py-0.5 text-[10px] font-semibold text-[var(--color-info)]">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info for sub-window -->
        <div v-if="isSubWindow" class="flex items-center gap-4 text-[10px] text-[var(--color-text-muted)]">
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Ctrl+I</kbd> Item Search</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Close</span>
        </div>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-wrap items-end gap-3">

        <!-- Item search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span>Item</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 font-mono text-[9px] text-[var(--color-text)]">Ctrl+I</kbd> Search
            </span>
          </label>
          <div
            @click="openItemSearch"
            class="w-full cursor-pointer rounded border px-3 py-2 text-sm outline-none transition-colors hover:border-[var(--color-info)]"
            :class="selectedItem ? 'border-[var(--color-info)] bg-[var(--color-info)]/20 font-semibold text-[var(--color-info)]' : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)]'"
          >
            {{ selectedItem ? `${selectedItem.item_code} - ${selectedItem.item_name}` : 'Select an item...' }}
          </div>
          <!-- Clear button -->
          <button
            v-if="selectedItem"
            @click="clearItem"
            class="absolute right-2 top-7 text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          >
            ✕
          </button>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
          <input
            ref="dateInput"
            v-model="fromDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- Warehouse filter -->
        <div class="w-48">
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</label>
          <select
            v-model="selectedWarehouse"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
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
            ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] cursor-pointer'
            : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] cursor-not-allowed'"
        >
          {{ loading ? 'Loading...' : 'Load Ledger' }}
        </button>

        <!-- Summary chips -->
        <template v-if="ledgerData">
          <div class="ml-2 flex items-center gap-2">
            <div class="flex flex-col rounded bg-[var(--color-warning)]/20 px-3 py-1 border border-[var(--color-warning)]">
              <span class="text-[9px] font-bold uppercase text-[var(--color-warning)] leading-none">Opening</span>
              <span class="text-sm font-bold text-[var(--color-warning)] leading-tight">{{ ledgerData.opening_balance }}</span>
            </div>
            <div class="flex flex-col rounded bg-[var(--color-success)]/20 px-3 py-1 border border-[var(--color-success)]">
              <span class="text-[9px] font-bold uppercase text-[var(--color-success)] leading-none">Purchase (In)</span>
              <span class="text-sm font-bold text-[var(--color-success)] leading-tight">+{{ ledgerData.total_in }}</span>
            </div>
            <div class="flex flex-col rounded bg-[var(--color-danger)]/20 px-3 py-1 border border-[var(--color-danger)]">
              <span class="text-[9px] font-bold uppercase text-[var(--color-danger)] leading-none">Sale (Out)</span>
              <span class="text-sm font-bold text-[var(--color-danger)] leading-tight">-{{ ledgerData.total_out }}</span>
            </div>
            <div class="flex flex-col rounded bg-[var(--color-info)]/20 px-3 py-1 border border-[var(--color-info)]">
              <span class="text-[9px] font-bold uppercase text-[var(--color-info)] leading-none">Closing</span>
              <span class="text-sm font-bold text-[var(--color-info)] leading-tight">{{ ledgerData.closing_balance }}</span>
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
        <div v-if="!ledgerData && !loading && !error" class="flex flex-1 flex-col items-center justify-center gap-2 text-[var(--color-text-muted)]">
          <div class="text-4xl">📦</div>
          <div class="text-sm font-semibold">Select an item and load the stock ledger</div>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center text-sm text-[var(--color-text-muted)]">
          Loading ledger...
        </div>

        <div v-else-if="error" class="m-6 rounded-lg border border-[var(--color-danger)] bg-[var(--color-danger)]/20 px-4 py-3 text-sm text-[var(--color-danger)]">
          {{ error }}
        </div>

        <template v-else-if="ledgerData">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
              <thead class="sticky top-0 z-10 bg-[var(--color-surface)]">
                <tr class="border-b border-[var(--color-border)]">
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Date</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Type</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Voucher No</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Qty</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">UOM</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Balance</th>
                </tr>
              </thead>
              <tbody ref="tableBodyRef">
                <!-- No entries message -->
                <tr v-if="!ledgerData.entries.length">
                  <td colspan="7" class="px-4 py-12 text-center text-[var(--color-text-muted)]">
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
                  class="cursor-pointer border-b border-[var(--color-border)] transition-colors"
                  :class="focusedIdx === idx
                    ? 'bg-[var(--color-info)]/30 outline outline-1 outline-blue-500'
                    : selectedEntry === entry
                      ? 'bg-[var(--color-info)]/20'
                      : 'hover:bg-[var(--color-surface)]/40'"
                >
                  <td class="px-4 text-[var(--color-text-muted)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ fmtDate(entry.date) }}</td>
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
                      class="font-mono text-[var(--color-info)] hover:underline"
                    >
                      {{ entry.voucher_no }}
                    </button>
                  </td>
                  <td class="px-4 text-[var(--color-text-muted)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    {{ entry.warehouse }}
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span :class="entry.actual_qty > 0 ? 'font-semibold text-[var(--color-success)]' : 'font-semibold text-[var(--color-danger)]'">
                      {{ entry.actual_qty > 0 ? '+' : '' }}{{ entry.actual_qty }}
                    </span>
                  </td>
                  <td class="px-4 text-[var(--color-text-muted)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    {{ entry.stock_uom }}
                  </td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="entry.balance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
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
          class="flex w-96 shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)]"
        >
          <!-- Panel header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="rounded px-2 py-0.5 text-[10px] font-bold" :class="voucherBadgeClass(selectedEntry.voucher_type)">
                {{ voucherLabel(selectedEntry.voucher_type) }}
              </span>
              <span class="font-mono text-sm font-bold text-[var(--color-text)]">{{ selectedEntry.voucher_no }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="['Sales Invoice', 'Quotation'].includes(selectedEntry.voucher_type)"
                @click="openBillDetail(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-[var(--color-info)] hover:bg-[var(--color-info)]/20"
              >
                View Bill
              </button>
              <button
                @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
                title="Open in ERPNext"
              >
                ERPNext ↗
              </button>
              <button @click="closeDetail" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">✕</button>
            </div>
          </div>

          <!-- Loading detail -->
          <div v-if="voucherDetail" class="flex-1 overflow-y-auto p-4">

            <!-- Key fields -->
            <div class="mb-4 space-y-2 rounded-lg bg-[var(--color-surface-raised)] p-3 text-xs">
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Date</span>
                <span class="font-semibold text-[var(--color-text)]">{{ fmtDate(voucherDetail.posting_date) }}</span>
              </div>
              <div v-if="voucherDetail.party_name || voucherDetail.party" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Party</span>
                <span class="font-semibold text-[var(--color-text)] text-right">{{ voucherDetail.party_name || voucherDetail.party }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Amount</span>
                <span class="font-bold text-[var(--color-text)]">₹{{ fmt(voucherDetail.total_amount) }}</span>
              </div>
              <div v-if="voucherDetail.remarks" class="pt-1">
                <span class="text-[var(--color-text-muted)]">Remarks</span>
                <p class="mt-0.5 text-[var(--color-text)]">{{ voucherDetail.remarks }}</p>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                Items
              </div>

              <!-- Sales/Purchase/Credit items -->
              <template v-if="['Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Stock Entry', 'Delivery Note', 'Purchase Receipt', 'Stock Reconciliation'].includes(voucherDetail.voucher_type)">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] text-[10px] text-[var(--color-text-muted)]">
                      <th class="pb-1.5 text-left font-normal">Item</th>
                      <th class="pb-1.5 text-right font-normal">Qty</th>
                      <th class="pb-1.5 text-right font-normal">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, i) in voucherDetail.items" :key="i" class="border-b border-[var(--color-border)]">
                      <td class="py-1.5">
                        <div class="font-semibold text-[var(--color-text)]" :class="{ 'text-[var(--color-info)]': item.item_code === selectedItem?.item_code }">
                          {{ item.item_code }}
                        </div>
                        <div class="text-[10px] text-[var(--color-text-muted)]">{{ item.item_name }}</div>
                      </td>
                      <td class="py-1.5 text-right text-[var(--color-text)]">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-1.5 text-right font-mono text-[var(--color-text)]">₹{{ fmt(item.rate) }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </div>
          </div>
        </div>
      </transition>

    </div>

    <!-- ═══════ BILL DETAIL OVERLAY ═══════ -->
    <div v-if="showBillDetail" class="fixed inset-0 z-[120] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div class="flex h-[95vh] w-[95vw] flex-col overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl">
        <header class="flex h-12 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
          <div class="flex items-center gap-4">
            <button
              @click="showBillDetail = false"
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <h2 class="text-sm font-semibold text-[var(--color-text)] uppercase tracking-widest">
              {{ billType }}: {{ billName }}
            </h2>
          </div>
          <button @click="showBillDetail = false" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">✕</button>
        </header>
        <div class="flex-1 overflow-hidden">
          <SalesInvoice v-if="billType === 'Sales Invoice'" :is-subwindow="true" :invoice-name="billName" @close="showBillDetail = false" />
          <Quotation v-else-if="billType === 'Quotation'" :is-subwindow="true" :quotation-name="billName" @close="showBillDetail = false" />
        </div>
      </div>
    </div>

    <GeneralLedger
      v-if="showCustomerLedgerWindow"
      :is-sub-window="true"
      :ledger-name="ledgerCustomerName"
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
import SalesInvoice from './SalesInvoice.vue'
import Quotation from './Quotation.vue'
import GeneralLedger from './GeneralLedger.vue'
import ItemSearch from '../components/ItemSearch.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useSubwindow, useSubwindowWatcher, isSubwindowActive } from '../services/shortcutManager'

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

// Layer 1: The Stock Ledger itself (if in subwindow mode)
useSubwindowWatcher(computed(() => props.isSubWindow), {
  'ESCAPE': () => {
    if (selectedEntry.value) {
      closeDetail()
    } else {
      emit('close')
    }
  }
})

// Layer 2: The Bill Detail Subwindow
const showBillDetail = ref(false)
const billName = ref('')
const billType = ref('')

function openBillDetail(voucherType, voucherNo) {
  billName.value = voucherNo
  billType.value = voucherType
  showBillDetail.value = true
}

useSubwindowWatcher(showBillDetail, {
  'ESCAPE': () => {
    showBillDetail.value = false
  }
})

const router = useRouter()
const route = useRoute()

function handleBack() {
  if (props.isSubWindow) {
    emit('close')
  } else {
    router.push('/')
  }
}

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
  'Sales Invoice':    { label: 'SINV', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' },
  'Purchase Invoice': { label: 'PINV', cls: 'bg-[var(--color-supplier)]/20 text-[var(--color-supplier)]' },
  'Stock Entry':      { label: 'SE',   cls: 'bg-[var(--color-employee)]/20 text-[var(--color-employee)]' },
  'Delivery Note':    { label: 'DN',   cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' },
  'Purchase Receipt': { label: 'PR',   cls: 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]' },
  'Stock Reconciliation': { label: 'RECON', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' },
}

function voucherLabel(type) {
  return VOUCHER_CONFIG[type]?.label ?? type?.slice(0, 4).toUpperCase() ?? '?'
}
function voucherBadgeClass(type) {
  return VOUCHER_CONFIG[type]?.cls ?? 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'
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
  if (['Sales Invoice', 'Quotation'].includes(entry.voucher_type)) {
    openBillDetail(entry.voucher_type, entry.voucher_no)
    return
  }
  updatePreview(entry, idx)
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
    if (['Sales Invoice', 'Quotation'].includes(entry.voucher_type)) {
      openBillDetail(entry.voucher_type, entry.voucher_no)
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
  if (isSubwindowActive()) return
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
