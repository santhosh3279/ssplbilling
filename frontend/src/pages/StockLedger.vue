<template>
  <div
    :class="[
      isSubWindow
        ? 'fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm'
        : 'flex min-h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px]'
    ]"
    @keydown.esc="isSubWindow && $emit('close')"
  >
    <div
      :class="[
        isSubWindow
          ? 'flex h-[92vh] w-[96vw] flex-col overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl'
          : 'flex flex-1 flex-col'
      ]"
    >
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="handleBack"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-2xl font-bold text-[var(--color-text)]">
            Stock Ledger
            <span v-if="selectedItem" class="ml-3 text-xl text-[var(--color-text-muted)] font-medium">— {{ selectedItem.item_code }} - {{ selectedItem.item_name }}</span>
          </h1>
          <span v-if="ledgerData" class="rounded-lg bg-[var(--color-info)]/20 px-3 py-1 text-lg font-bold text-[var(--color-info)] shadow-sm">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- Zoom Controls -->
          <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <button @click="zoomPercent = Math.max(60, zoomPercent - 10)" class="flex h-7 w-7 items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
            <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] px-2 min-w-[44px]">
              <span class="text-[9px] uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
              <span class="text-[11px] font-semibold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
            </div>
            <button @click="zoomPercent = Math.min(200, zoomPercent + 10)" class="flex h-7 w-7 items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
          </div>

          <!-- Close button for sub-window -->
          <button
            v-if="isSubWindow"
            @click="emit('close')"
            class="ml-2 flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            title="Close (Esc)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-wrap items-center gap-3">

        <!-- Date Filters -->
        <div class="flex items-center gap-2 bg-[var(--color-surface-raised)]/50 px-1 py-0.5 rounded-xl border border-[var(--color-border)] shadow-sm">
          <div class="flex items-center gap-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] ml-2">From</label>
            <input
              ref="dateInput"
              v-model="fromDate"
              type="date"
              class="bg-transparent text-3xl font-mono text-[var(--color-text)] outline-none focus:text-[var(--color-info)] w-48"
            />
          </div>
          
          <div class="h-8 w-px bg-[var(--color-border)] opacity-30 mx-1"></div>

          <div class="flex items-center gap-2">
            <label class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">To</label>
            <input
              v-model="toDate"
              type="date"
              class="bg-transparent text-3xl font-mono text-[var(--color-text)] outline-none focus:text-[var(--color-info)] w-48"
            />
          </div>
        </div>

        <!-- Warehouse filter -->
        <div class="relative min-w-[180px]">
          <select
            v-model="selectedWarehouse"
            class="h-[46px] w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-4 pt-4 pb-1 text-sm font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] appearance-none"
          >
            <option value="">All Warehouses</option>
            <option v-for="w in allowedWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
          <label class="absolute left-4 top-1.5 text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] pointer-events-none">Warehouse</label>
          <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[var(--color-text-muted)]">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </div>
        </div>

        <!-- Refresh Button -->
        <button
          @click="loadLedger"
          :disabled="!selectedItem || loading"
          class="rounded-xl px-5 py-2.5 text-sm font-bold transition-all shadow-sm active:scale-95"
          :class="selectedItem && !loading
            ? 'bg-[var(--color-info)] text-white hover:opacity-90 cursor-pointer'
            : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] cursor-not-allowed'"
        >
          {{ loading ? 'Loading…' : 'Load Ledger' }}
        </button>

        <!-- Summary chips -->
        <template v-if="ledgerData">
          <div class="flex items-center gap-6 flex-wrap ml-4">
            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1">Opening</span>
              <span class="text-3xl font-mono leading-none text-[var(--color-warning)]">
                {{ fmt(ledgerData.opening_balance) }}
              </span>
            </div>

            <div class="h-10 w-px bg-[var(--color-border)] opacity-50"></div>

            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1">Inwards (+)</span>
              <span class="text-3xl font-mono leading-none text-[var(--color-success)]">
                +{{ fmt(ledgerData.total_in) }}
              </span>
            </div>

            <div class="h-10 w-px bg-[var(--color-border)] opacity-50"></div>

            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1">Outwards (-)</span>
              <span class="text-3xl font-mono leading-none text-[var(--color-danger)]">
                -{{ fmt(ledgerData.total_out) }}
              </span>
            </div>

            <div class="h-10 w-px bg-[var(--color-border)] opacity-50"></div>

            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1">Closing</span>
              <span class="text-3xl font-mono leading-none text-[var(--color-info)]">
                {{ fmt(ledgerData.closing_balance) }}
              </span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Ledger Table ── -->
      <div class="flex-1 overflow-auto">

        <!-- Empty / loading state -->
        <div v-if="!ledgerData && !loading && !error" class="flex flex-col items-center justify-center gap-3 py-24 text-[var(--color-text-muted)]">
          <div class="text-5xl">📦</div>
          <div class="text-sm font-semibold">Select an item and load the stock ledger</div>
        </div>

        <div v-else-if="loading" class="flex items-center justify-center gap-2 py-24 text-sm text-[var(--color-text-muted)]">
          <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></div>
          Loading ledger...
        </div>

        <div v-else-if="error" class="m-6 rounded-lg border border-[var(--color-danger)] bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
          {{ error }}
        </div>

        <template v-else-if="ledgerData">
          <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
            <thead class="sticky top-0 z-10 bg-[var(--color-surface)] border-b-2 border-[var(--color-border)]">
              <tr class="text-left">
                <th class="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Date</th>
                <th class="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Type</th>
                <th class="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Voucher No</th>
                <th class="px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</th>
                <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Qty</th>
                <th class="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] w-20">UOM</th>
                <th class="px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Balance</th>
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
                class="cursor-pointer border-b border-[var(--color-border)] transition-all outline-none"
                :class="{
                  'bg-[var(--color-focus)] text-[var(--color-text-on-focus)] font-bold shadow-inner z-10 relative': focusedIdx === idx,
                  'bg-[var(--color-info)]/10': selectedEntry === entry && focusedIdx !== idx,
                  'hover:bg-[var(--color-surface-raised)]/60': focusedIdx !== idx
                }"
              >
                <td class="px-4 font-mono whitespace-nowrap" :style="dynamicRowStyle" :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ fmtDate(entry.date) }}</td>
                <td class="px-4" :style="dynamicRowStyle">
                  <span
                    class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide"
                    :class="voucherBadgeClass(entry.voucher_type)"
                  >
                    {{ voucherLabel(entry.voucher_type) }}
                  </span>
                </td>
                <td class="px-4 whitespace-nowrap" :style="dynamicRowStyle">
                  <button
                    @click.stop="openInErpNext(entry.voucher_type, entry.voucher_no)"
                    class="font-mono hover:underline"
                    :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-info)]'"
                  >
                    {{ entry.voucher_no }}
                  </button>
                </td>
                <td class="px-4 truncate max-w-[150px]" :style="dynamicRowStyle" :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
                  {{ entry.warehouse }}
                </td>
                <td class="px-4 text-right font-mono" :style="dynamicRowStyle">
                  <span :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]' : (entry.actual_qty > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
                    {{ entry.actual_qty > 0 ? '+' : '' }}{{ entry.actual_qty }}
                  </span>
                </td>
                <td class="px-4 text-[var(--color-text-muted)]" :style="dynamicRowStyle" :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]/70' : ''">
                  {{ entry.stock_uom }}
                </td>
                <td class="px-4 text-right font-mono font-bold"
                  :style="dynamicRowStyle"
                  :class="focusedIdx === idx ? 'text-[var(--color-text-on-focus)]' : (entry.balance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
                  {{ entry.balance }}
                </td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>

      <!-- ── Detail Panel ── -->
      <transition name="slide">
        <div
          v-if="selectedEntry"
          class="flex w-96 shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl"
        >
          <!-- Panel header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3 bg-[var(--color-surface-raised)]">
            <div class="flex items-center gap-2">
              <span class="rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider" :class="voucherBadgeClass(selectedEntry.voucher_type)">
                {{ voucherLabel(selectedEntry.voucher_type) }}
              </span>
              <span class="font-mono text-sm font-bold text-[var(--color-text)]">{{ selectedEntry.voucher_no }}</span>
            </div>
            <button @click="closeDetail" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-colors">✕</button>
          </div>

          <!-- Detail Content -->
          <div v-if="voucherDetail" class="flex-1 overflow-y-auto p-4 custom-scrollbar">

            <!-- Key fields Card -->
            <div class="mb-4 space-y-2 rounded-lg bg-[var(--color-surface-raised)] p-3 text-[11px]">
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Date</span>
                <span class="font-semibold text-[var(--color-text)]">{{ fmtDate(voucherDetail.posting_date || selectedEntry.date) }}</span>
              </div>
              <div v-if="voucherDetail.party_name || voucherDetail.party" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Party</span>
                <span class="font-semibold text-[var(--color-text)] text-right">{{ voucherDetail.party_name || voucherDetail.party }}</span>
              </div>
              <div class="flex justify-between border-t border-[var(--color-border)] pt-2 mt-2">
                <span class="text-[var(--color-text-muted)] font-bold uppercase">Amount</span>
                <span class="font-bold text-[var(--color-info)]">₹{{ fmt(voucherDetail.total_amount) }}</span>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
                Items
              </div>

              <div class="space-y-2">
                <div v-for="(item, i) in voucherDetail.items" :key="i" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-[11px]">
                  <div class="flex justify-between font-semibold">
                    <span :class="item.item_code === selectedItem?.item_code ? 'text-[var(--color-info)]' : 'text-[var(--color-text)]'">
                      {{ item.item_code }}
                    </span>
                    <span class="font-mono">₹{{ fmt(item.rate) }}</span>
                  </div>
                  <div class="text-[10px] text-[var(--color-text-muted)] truncate">{{ item.item_name }}</div>
                  <div class="mt-1 flex justify-between text-[10px] opacity-70">
                    <span>{{ item.qty }} {{ item.uom }}</span>
                    <span class="font-bold">₹{{ fmt(item.amount) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedEntry.remarks" class="mt-6 border-t border-[var(--color-border)] pt-4">
              <div class="mb-1 text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Remarks</div>
              <p class="text-[11px] leading-relaxed text-[var(--color-text)] whitespace-pre-wrap">{{ selectedEntry.remarks }}</p>
            </div>
          </div>

          <!-- Panel Footer -->
          <div class="border-t border-[var(--color-border)] p-4 bg-[var(--color-surface-raised)]/30">
            <button
              v-if="['Sales Invoice', 'Quotation'].includes(selectedEntry.voucher_type)"
              @click="openBillDetail(selectedEntry.voucher_type, selectedEntry.voucher_no)"
              class="mb-2 flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-success)] py-2.5 text-xs font-bold text-white shadow-lg transition-all hover:bg-[var(--color-success)]/90 active:scale-95"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              Open Bill
            </button>

            <button
              @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
              class="w-full rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] py-2 text-xs font-semibold text-[var(--color-text)] hover:border-[var(--color-info)] hover:text-[var(--color-info)] transition-all"
            >
              Open in ERPNext ↗
            </button>
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

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="ledgerItemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Stock"
      :skip-date-filter="true"
      @close="showItemSearchModal = false"
      @select="pickItem"
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
import ItemSearch from '../components/ItemSearch.vue'
import { useSubwindowWatcher, isSubwindowActive } from '../services/shortcutManager'

const props = defineProps({
  isSubWindow: { type: Boolean, default: false },
  itemCode: { type: String, default: '' },
  initialFromDate: { type: String, default: '' },
  initialToDate: { type: String, default: '' }
})

const emit = defineEmits(['close'])

// Layer 1: The Stock Ledger itself
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

function clearItem() {
  selectedItem.value = null
  ledgerData.value = null
  error.value = ''
}

// ─── Zoom ─────────────────────────────────────────────────────────────────────
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 100)
const dynamicRowStyle = computed(() => ({
  fontSize: `${(13 * zoomPercent.value) / 100}px`,
  paddingTop: `${(3 * zoomPercent.value) / 100}px`,
  paddingBottom: `${(3 * zoomPercent.value) / 100}px`
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
const fromDate = ref('')
const toDate = ref('')
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
const loadingDetail = ref(false)

// Ledger row keyboard navigation
const focusedIdx = ref(-1)
const tableBodyRef = ref(null)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return (Number(n) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDate(d) {
  if (!d) return ''
  const datePart = String(d).split(' ')[0]
  const parts = datePart.split('-')
  if (parts.length === 3) {
    const [yyyy, mm, dd] = parts
    return `${dd.padStart(2, '0')}/${mm.padStart(2, '0')}/${yyyy}`
  }
  return d
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

// Prop Syncing
watch(() => props.initialFromDate, (newV) => { if (newV) fromDate.value = newV })
watch(() => props.initialToDate, (newV) => { if (newV) toDate.value = newV })
watch(() => props.itemCode, (newV) => { if (newV) autoLoadItem(newV) })

async function autoLoadItem(code) {
  if (!code || code === selectedItem.value?.item_code) return
  loading.value = true
  try {
    const item = await frappeGet('frappe.client.get', {
      doctype: 'Item',
      name: code
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

// ─── Row hover/keyboard → update preview ──
function onRowMouseEnter(entry, idx) {
  if (focusedIdx.value === -1) {
     // only update on hover if not navigating with keyboard
     updatePreview(entry, idx)
  }
}

async function updatePreview(entry, idx) {
  focusedIdx.value = idx
  if (selectedEntry.value === entry) return
  selectedEntry.value = entry
  voucherDetail.value = entry.detail || null
}

function onRowClick(entry, idx) {
  focusedIdx.value = idx
  if (['Sales Invoice', 'Quotation'].includes(entry.voucher_type)) {
    openBillDetail(entry.voucher_type, entry.voucher_no)
    return
  }
  updatePreview(entry, idx)
}

function closeDetail() {
  selectedEntry.value = null
  voucherDetail.value = null
  focusedIdx.value = -1
}

// ─── Keyboard navigation for ledger rows ──────────────────────────────────────
function onTableKeydown(e) {
  if (!ledgerData.value?.entries?.length) return
  const len = ledgerData.value.entries.length

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const nextIdx = Math.min(focusedIdx.value + 1, len - 1)
    updatePreview(ledgerData.value.entries[nextIdx], nextIdx)
    scrollRowIntoView(nextIdx)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const prevIdx = Math.max(focusedIdx.value - 1, 0)
    updatePreview(ledgerData.value.entries[prevIdx], prevIdx)
    scrollRowIntoView(prevIdx)
  } else if (e.key === 'Enter' && focusedIdx.value >= 0) {
    e.preventDefault()
    const entry = ledgerData.value.entries[focusedIdx.value]
    if (['Sales Invoice', 'Quotation'].includes(entry.voucher_type)) {
      openBillDetail(entry.voucher_type, entry.voucher_no)
    } else {
      updatePreview(entry, focusedIdx.value)
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
  if (showItemSearchModal.value || showBillDetail.value) {
    if (e.key === 'Escape' && showItemSearchModal.value) {
      showItemSearchModal.value = false
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

  if (!ledgerData.value) return
  onTableKeydown(e)
}

const handleDateFocus = () => dateInput.value?.focus();

onMounted(async () => {
  window.addEventListener('wb-global-date-focus', handleDateFocus);
  window.addEventListener('keydown', onGlobalKeydown)

  // Load all warehouses from ERPNext
  try {
    const warehouses = await frappeGet('ssplbilling.api.ledger_api.get_warehouses')
    if (warehouses?.length) {
      allowedWarehouses.value = warehouses
      const defaultWh = localStorage.getItem('wb-warehouse') || ''
      selectedWarehouse.value = warehouses.includes(defaultWh) ? defaultWh : warehouses[0]
    }
  } catch (e) {
    console.warn('[StockLedger] Failed to load warehouses:', e.message)
    const wh = localStorage.getItem('wb-warehouse') || ''
    if (wh) { allowedWarehouses.value = [wh]; selectedWarehouse.value = wh }
  }

  // Apply initial dates or defaults
  fromDate.value = props.initialFromDate || getSevenDaysAgoIST()
  toDate.value = props.initialToDate || getTodayIST()

  if (props.itemCode) {
    autoLoadItem(props.itemCode)
  }
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', handleDateFocus);
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>

<script>
export default {
  inheritAttrs: false
}
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
* { font-weight: 400; }
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
</style>
