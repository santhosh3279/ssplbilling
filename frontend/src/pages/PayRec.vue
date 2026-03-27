<template>
  <div class="flex h-screen flex-col bg-slate-900 font-sans text-slate-100">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-700 bg-slate-800 px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-slate-100 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-slate-100">{{ isReceipt ? 'RECEIPT ENTRY' : 'PAYMENT ENTRY' }}</h1>
        <div class="h-4 w-px bg-slate-600 mx-2"></div>
        <div class="flex rounded-lg bg-slate-700 p-1">
          <button
            @click="isReceipt = true"
            class="rounded-md px-4 py-1 text-xs font-bold transition-all flex items-center gap-1.5"
            :class="isReceipt ? 'bg-slate-800 text-blue-400 shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          >
            <span>Receipt</span>
            <kbd class="rounded border px-1 text-[9px] opacity-50" :class="isReceipt ? 'border-blue-500 bg-blue-900/20' : 'border-slate-600 bg-slate-700'">F2</kbd>
          </button>
          <button
            @click="isReceipt = false"
            class="rounded-md px-4 py-1 text-xs font-bold transition-all flex items-center gap-1.5"
            :class="!isReceipt ? 'bg-slate-800 text-emerald-400 shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          >
            <span>Payment</span>
            <kbd class="rounded border px-1 text-[9px] opacity-50" :class="!isReceipt ? 'border-emerald-600 bg-emerald-900/20' : 'border-slate-600 bg-slate-700'">F3</kbd>
          </button>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- Keyboard hints -->
        <div class="flex items-center gap-3 text-[11px] text-slate-500">
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">INS</kbd> Add Row</span>
          <span class="text-slate-700">|</span>
          <span class="flex items-center gap-1">
            <kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">INS</kbd>
            <span class="text-slate-500">while picking account →</span>
            <span class="font-bold text-slate-400">Show All Accounts</span>
          </span>
          <span class="text-slate-700">|</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 font-mono text-[10px] text-slate-300">F9</kbd> Save</span>
        </div>

        <div class="flex items-center gap-3 bg-slate-700 px-4 py-1.5 rounded-xl border border-slate-600 shadow-sm">
          <label class="text-[11px] font-black uppercase tracking-widest text-slate-400">Posting Date</label>
          <div class="flex items-center gap-1">
            <button
              @click="changeDate(-1)"
              class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              ref="dateInput"
              v-model="displayDate"
              type="text"
              class="bg-transparent text-xl font-black text-slate-200 outline-none focus:text-blue-400 w-44 font-mono"
              placeholder="DD/MM/YYYY"
              @focus="e => e.target.select()"
              @input="onDateInput"
            />
            <button
              @click="changeDate(1)"
              class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="flex-1 overflow-hidden p-6">
      <div class="h-full flex flex-col bg-slate-800 rounded-2xl shadow-sm border border-slate-700 overflow-hidden">
        <!-- TABLE -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
              <tr class="text-xs font-bold uppercase tracking-wider text-slate-400 text-left">
                <th class="px-4 py-2 w-12 text-center">#</th>
                <th class="px-2 py-2 min-w-[300px]">Ledger / Party</th>
                <th class="px-4 py-2 w-80 text-right">Balance</th>
                <th class="px-4 py-2 w-80 text-right">Debit (₹)</th>
                <th class="px-4 py-2 w-80 text-right">Credit (₹)</th>
                <th class="px-4 py-2 w-80 text-right">New Bal</th>
                <th class="px-4 py-2 w-12"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <tr
                v-for="(row, idx) in rows"
                :key="idx"
                class="group hover:bg-slate-800/40 transition-colors"
                :class="{ 'bg-blue-900/20': activeRowIdx === idx }"
              >
                <td class="px-4 py-0.5 text-center text-sm font-bold text-slate-500">
                  {{ idx + 1 }}
                </td>
                <td class="px-2 py-0.5">
                  <div
                    :ref="el => { if (el) ledgerRefs[idx] = el }"
                    @click="openLedgerSearch(idx)"
                    @keydown.enter.prevent.stop="openLedgerSearch(idx)"
                    tabindex="0"
                    class="w-full rounded-lg border border-transparent px-3 py-0.5 text-2xl font-bold cursor-pointer hover:border-slate-600 hover:bg-slate-700 transition-all flex items-center justify-between group/input outline-none focus:ring-2 focus:ring-blue-500 focus:bg-slate-700 focus:border-blue-500"
                    :class="row.account ? 'text-slate-100' : 'text-slate-600 italic'"
                  >
                    <div class="flex items-center gap-2 truncate">
                      <span class="truncate">{{ row.account_name || 'Select Ledger...' }}</span>
                      <span
                        v-if="row.account && getResolvedLabel(row.account)"
                        class="shrink-0 px-2 py-0.5 rounded bg-blue-900/20 text-blue-400 text-[10px] font-black uppercase tracking-tighter"
                      >
                        {{ getResolvedLabel(row.account) }}
                      </span>
                    </div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-600 group-hover/input:text-blue-400"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                  </div>
                </td>
                <td class="px-2 py-0 text-right">
                  <div v-if="row.account" class="text-2xl font-bold text-slate-400 font-mono whitespace-nowrap">
                    {{ formatBalance(row.current_balance) }}
                  </div>
                </td>
                <td class="px-2 py-0">
                  <input
                    :ref="el => { if (el) debitRefs[idx] = el }"
                    v-model.number="row.debit"
                    @focus="activeRowIdx = idx"
                    @input="row.credit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'debit')"
                    :disabled="isFieldDisabled(idx, 'debit')"
                    :tabindex="isFieldDisabled(idx, 'debit') ? -1 : 0"
                    type="number"
                    class="w-full rounded-lg border bg-transparent px-3 py-0 text-right font-mono text-2xl font-bold text-slate-100 outline-none focus:bg-slate-700 transition-all disabled:opacity-20"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'debit' ? 'border-rose-500 bg-red-900/20 animate-blink' : 'border-transparent focus:border-blue-500'"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-2 py-0">
                  <input
                    :ref="el => { if (el) creditRefs[idx] = el }"
                    v-model.number="row.credit"
                    @focus="activeRowIdx = idx"
                    @input="row.debit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'credit')"
                    :disabled="isFieldDisabled(idx, 'credit')"
                    :tabindex="isFieldDisabled(idx, 'credit') ? -1 : 0"
                    type="number"
                    class="w-full rounded-lg border bg-transparent px-3 py-0 text-right font-mono text-2xl font-bold text-slate-100 outline-none focus:bg-slate-700 transition-all disabled:opacity-20"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'credit' ? 'border-rose-500 bg-red-900/20 animate-blink' : 'border-transparent focus:border-blue-500'"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-2 py-0 text-right">
                  <div v-if="row.account" class="text-2xl font-bold font-mono whitespace-nowrap" :class="getNewBalance(row) !== row.current_balance ? 'text-blue-400' : 'text-slate-400'">
                    {{ formatBalance(getNewBalance(row)) }}
                  </div>
                </td>
                <td class="px-4 py-1 text-center">
                  <button
                    @click="removeRow(idx)"
                    class="text-slate-600 hover:text-rose-400 transition-colors opacity-0 group-hover:opacity-100"
                    tabindex="-1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="p-2">
            <button
              @click="addRow"
              class="flex items-center gap-2 rounded-xl border border-dashed border-slate-600 px-4 py-2 text-xs font-bold text-slate-500 hover:border-blue-500 hover:text-blue-400 hover:bg-blue-900/20 transition-all w-full justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              Add New Row (INS)
            </button>
          </div>
        </div>

        <!-- FOOTER: TOTALS -->
        <div class="shrink-0 bg-slate-800 border-t border-slate-700 p-6 flex flex-col gap-4">
          <!-- ERROR ALERT -->
          <div v-if="validationError" class="flex items-center gap-2 bg-red-900/20 text-red-400 px-4 py-2 rounded-lg border border-red-700 text-xs font-bold" :class="errorBlink ? 'animate-blink' : ''">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
            {{ validationError }}
          </div>

          <div class="flex items-start justify-between">
            <div class="flex-1 max-w-xl">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1 block">Reference No</label>
                  <input
                    v-model="referenceNo"
                    type="text"
                    class="w-full rounded-xl border border-slate-600 bg-slate-700 px-4 py-2 text-xl font-bold text-slate-200 outline-none focus:border-blue-500 transition-all shadow-sm"
                    placeholder="Cheque / UTR"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1 block">Remarks</label>
                  <input
                    ref="remarksInput"
                    v-model="userRemarks"
                    @keydown.enter.prevent="handleRemarksEnter"
                    class="w-full rounded-xl border border-slate-600 bg-slate-700 px-4 py-2 text-xl font-bold text-slate-200 outline-none focus:border-blue-500 transition-all shadow-sm"
                    placeholder="Notes..."
                  />
                </div>
              </div>
            </div>
            <div class="flex gap-12 ml-12">
              <div class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Total Debit</div>
                <div class="text-2xl font-black text-slate-100 font-mono">₹ {{ fmt(totalDebit) }}</div>
              </div>
              <div class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Total Credit</div>
                <div class="text-2xl font-black text-slate-100 font-mono">₹ {{ fmt(totalCredit) }}</div>
              </div>
              <div class="text-right border-l border-slate-700 pl-12">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Difference</div>
                <div
                  class="text-2xl font-black font-mono"
                  :class="Math.abs(difference) < 0.01 ? 'text-emerald-400' : 'text-rose-400'"
                >
                  ₹ {{ fmt(difference) }}
                </div>
                <!-- SAVE BUTTON -->
                <div class="mt-4 flex justify-end">
                  <button
                    ref="saveButton"
                    @click="saveEntry"
                    @keydown.enter="saveEntry"
                    :disabled="isSubmitting || !canSave"
                    class="flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3 text-base font-bold text-white shadow-lg shadow-blue-900/50 hover:bg-blue-700 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    <span v-if="isSubmitting" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent mr-1"></span>
                    <span>Save Entry</span>
                    <kbd class="ml-2 rounded border border-blue-400 bg-blue-500 px-2 py-0.5 font-mono text-xs text-blue-100">F9</kbd>
                  </button>
                </div>
              </div>
            </div>
          </div>
      </div>
      </div>
    </div>

    <!-- OUTSTANDING INVOICES MODAL -->
    <div v-if="showOutstandingModal" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="confirmOutstanding">
      <div class="w-[780px] max-h-[85vh] flex flex-col overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-4">
          <div>
            <div class="text-base font-bold text-slate-100">Outstanding Bills</div>
            <div class="text-xs text-slate-400 mt-0.5">
              {{ rows[0].account_name }} &mdash; {{ outstandingInvoices.length }} pending bill{{ outstandingInvoices.length !== 1 ? 's' : '' }}
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="text-right">
              <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Amount Entered</div>
              <div class="font-mono text-2xl font-bold text-blue-400">₹{{ fmt(isReceipt ? rows[0].credit : rows[0].debit) }}</div>
            </div>
            <div class="text-right border-l border-slate-700 pl-4">
              <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Allocated</div>
              <div class="font-mono text-2xl font-bold" :class="outstandingAllocatedTotal > (isReceipt ? rows[0].credit : rows[0].debit) + 0.005 ? 'text-red-400' : 'text-emerald-400'">
                ₹{{ fmt(outstandingAllocatedTotal) }}
              </div>
            </div>
            <div class="text-right border-l border-slate-700 pl-4">
              <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Outstanding</div>
              <div class="font-mono text-2xl font-bold text-amber-400">₹{{ fmt(outstandingInvoices.reduce((s, i) => s + i.outstanding_amount, 0)) }}</div>
            </div>
          </div>
        </div>

        <!-- Invoice List -->
        <div class="flex-1 overflow-y-auto">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 bg-slate-800 border-b border-slate-700">
              <tr class="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th class="px-4 py-2 text-left">Invoice</th>
                <th class="px-4 py-2 text-left">Date</th>
                <th class="px-4 py-2 text-center">Days</th>
                <th class="px-4 py-2 text-right">Invoice Amt</th>
                <th class="px-4 py-2 text-right">Outstanding</th>
                <th class="px-4 py-2 text-right">Allocate</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr v-for="(inv, i) in outstandingInvoices" :key="inv.name"
                class="transition-colors" :class="inv._alloc > 0 ? 'bg-blue-900/10' : 'hover:bg-slate-800/40'">
                <td class="px-4 py-2 font-mono text-sm font-bold text-blue-400">{{ inv.name }}</td>
                <td class="px-4 py-2 text-sm text-slate-400 whitespace-nowrap">{{ inv.posting_date }}</td>
                <td class="px-4 py-2 text-center">
                  <span class="rounded-full px-2 py-0.5 text-xs font-bold"
                    :class="inv._days > 90 ? 'bg-red-900/40 text-red-400' : inv._days > 30 ? 'bg-amber-900/40 text-amber-400' : 'bg-slate-700 text-slate-400'">
                    {{ inv._days }}d
                  </span>
                </td>
                <td class="px-4 py-2 text-right font-mono text-sm text-slate-400">₹{{ fmt(inv.grand_total) }}</td>
                <td class="px-4 py-2 text-right font-mono font-bold text-amber-400">₹{{ fmt(inv.outstanding_amount) }}</td>
                <td class="px-3 py-1.5 text-right">
                  <input
                    v-model.number="inv._alloc"
                    type="number"
                    min="0"
                    :max="inv.outstanding_amount"
                    step="0.01"
                    :ref="el => { if (el) outstandingAllocRefs[i] = el }"
                    @focus="e => e.target.select()"
                    @keydown.enter.prevent="focusNextAllocOrProceed(i)"
                    class="w-28 rounded-lg border border-slate-600 bg-slate-800 px-2 py-1 text-right font-mono text-sm font-bold text-slate-100 outline-none focus:border-blue-500 focus:bg-slate-700"
                    placeholder="0.00"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between border-t border-slate-700 bg-slate-800/50 px-6 py-3">
          <div class="text-xs text-slate-500">
            Enter amount to allocate per bill &middot; Enter on last row proceeds
          </div>
          <div class="flex items-center gap-3">
            <button @click="outstandingInvoices.forEach(i => i._alloc = 0)" class="rounded-lg border border-slate-600 px-4 py-1.5 text-xs font-bold text-slate-400 hover:bg-slate-800 transition-all">
              Clear
            </button>
            <button
              ref="outstandingProceedBtn"
              @click="confirmOutstanding"
              @keydown.enter.prevent="confirmOutstanding"
              class="rounded-xl bg-blue-600 px-6 py-2 text-sm font-bold text-white hover:bg-blue-700 transition-all shadow-lg"
            >
              Proceed &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL -->
    <CustomerSearchModal
      ref="ledgerSearchModal"
      :show="showSearchModal"
      :allowed-types="searchAllowedTypes"
      :initial-type="searchInitialType"
      :filter-list="showAllAccounts ? null : searchFilterList"
      :override-ledgers="(!showAllAccounts && activeRowIdx > 0) ? mopLedgers : null"
      :skip-date-filter="true"
      @close="showSearchModal = false"
      @select="selectLedger"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappePost, frappeGet } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { payrecShortcuts } from '../shortcuts/payrecShortcuts'

const router = useRouter()

// --- STATE ---
const isReceipt = ref(true)
const mopLedgers = ref(null)

watch(isReceipt, () => {
  rows.value = [
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
  ]
  activeRowIdx.value = 0
  nextTick(() => ledgerRefs[0]?.focus())
})

const searchInitialType = computed(() => {
  if (isReceipt.value) {
    if (activeRowIdx.value === 0) return 'Customer'
    return 'Account'
  }
  // Payment Mode
  if (activeRowIdx.value === 0) return 'Supplier'
  return 'Account'
})

const searchFilterList = computed(() => {
  if (activeRowIdx.value > 0) {
    return ['wb-cash', 'wb-card', 'wb-upi', 'wb-bank']
      .map(k => localStorage.getItem(k))
      .filter(Boolean)
  }
  return null
})

const searchAllowedTypes = computed(() => {
  if (activeRowIdx.value > 0) return ['Account']
  return ['Account', 'Customer', 'Supplier', 'Employee']
})

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) 
  return formatter.format(date)
}

const postingDate = ref(getTodayIST())
const displayDate = ref(formatDateToDisplay(postingDate.value))
const dateInput = ref(null)

function formatDateToDisplay(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function onDateInput(e) {
  let val = e.target.value.replace(/\D/g, '')
  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const year = new Date().getFullYear()
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      postingDate.value = `${year}-${monthStr}-${dayStr}`
      displayDate.value = `${dayStr}/${monthStr}/${year}`
      return
    }
  }
  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '/' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '/' + val.slice(2, 4) + '/' + val.slice(4, 8)
  }
  displayDate.value = val
  if (val.length === 10) {
    const [d, m, y] = val.split('/')
    if (d && m && y && y.length === 4) {
      postingDate.value = `${y}-${m}-${d}`
    }
  }
}

function changeDate(days) {
  const d = new Date(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = d.toISOString().slice(0, 10)
  displayDate.value = formatDateToDisplay(postingDate.value)
}

const referenceNo = ref('')
const userRemarks = ref('')
const rows = ref([
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
])
const activeRowIdx = ref(0)
const isSubmitting = ref(false)
const showSearchModal = ref(false)
const showAllAccounts = ref(false)
const ledgerSearchModal = ref(null)
const remarksInput = ref(null)
const saveButton = ref(null)
const errorBlink = ref(false)
const blinkCell = ref(null)
const showOutstandingModal = ref(false)
const outstandingInvoices = ref([])
const outstandingProceedBtn = ref(null)
const outstandingAllocRefs = []
const outstandingAllocatedTotal = computed(() =>
  outstandingInvoices.value.reduce((s, i) => s + (Number(i._alloc) || 0), 0)
)

// Template Refs
const ledgerRefs = []
const debitRefs = []
const creditRefs = []

// --- COMPUTED ---
const totalDebit = computed(() => rows.value.reduce((s, r) => s + (Number(r.debit) || 0), 0))
const totalCredit = computed(() => rows.value.reduce((s, r) => s + (Number(r.credit) || 0), 0))
const difference = computed(() => totalDebit.value - totalCredit.value)

const validationError = computed(() => {
  const r1 = rows.value[0]
  if (!r1) return null
  
  if (Number(r1.debit) > 0.005) {
    const sumOtherCredit = rows.value.slice(1).reduce((s, r) => s + (Number(r.credit) || 0), 0)
    if (sumOtherCredit > Number(r1.debit) + 0.005) {
      return `Total Credit (₹${fmt(sumOtherCredit)}) exceeds first row Debit (₹${fmt(r1.debit)})`
    }
  } else if (Number(r1.credit) > 0.005) {
    const sumOtherDebit = rows.value.slice(1).reduce((s, r) => s + (Number(r.debit) || 0), 0)
    if (sumOtherDebit > Number(r1.credit) + 0.005) {
      return `Total Debit (₹${fmt(sumOtherDebit)}) exceeds first row Credit (₹${fmt(r1.credit)})`
    }
  }
  return null
})

const canSave = computed(() => {
  return rows.value.filter(r => r.account).length >= 2 && 
         Math.abs(difference.value) < 0.01 && 
         totalDebit.value > 0 &&
         !validationError.value
})

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function getResolvedLabel(accountName) {
  if (accountName === localStorage.getItem('wb-cash')) return 'CASH'
  if (accountName === localStorage.getItem('wb-bank')) return 'BANK'
  if (accountName === localStorage.getItem('wb-upi')) return 'UPI'
  if (accountName === localStorage.getItem('wb-card')) return 'CARD'
  return null
}

function addRow() {
  rows.value.push({ account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 })
  activeRowIdx.value = rows.value.length - 1
}

function removeRow(idx) {
  if (rows.value.length <= 1) {
    rows.value[idx] = { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    return
  }
  rows.value.splice(idx, 1)
}

function openLedgerSearch(idx) {
  activeRowIdx.value = idx
  showAllAccounts.value = false
  showSearchModal.value = true
  nextTick(() => ledgerSearchModal.value?.focus())
}

function selectLedger(ledger) {
  const row = rows.value[activeRowIdx.value]
  row.account = ledger.name
  row.account_name = ledger.label
  row.account_type = ledger.type
  row.current_balance = ledger.balance || 0
  showSearchModal.value = false
  
  nextTick(() => {
    let el = null
    if (isFieldDisabled(activeRowIdx.value, 'debit')) {
      el = creditRefs[activeRowIdx.value]
    } else {
      el = debitRefs[activeRowIdx.value]
    }
    if (el) { el.focus(); el.select() }
  })
}

function formatBalance(val) {
  const absVal = Math.abs(val || 0)
  const suffix = val > 0.005 ? ' DR' : (val < -0.005 ? ' CR' : '')
  return absVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + suffix
}

function getNewBalance(row) {
  return (Number(row.current_balance) || 0) + (Number(row.debit) || 0) - (Number(row.credit) || 0)
}

function isFieldDisabled(idx, field) {
  // Row 0: mode-based restriction
  if (idx === 0) {
    if (isReceipt.value && field === 'debit') return true   // Receipt → party is credited
    if (!isReceipt.value && field === 'credit') return true // Payment → party is debited
  }
  // Other rows: follow what row 0 has entered
  const firstRowDebit = Number(rows.value[0]?.debit) || 0
  const firstRowCredit = Number(rows.value[0]?.credit) || 0
  if (firstRowDebit > 0.005 && idx > 0 && field === 'debit') return true
  if (firstRowCredit > 0.005 && idx > 0 && field === 'credit') return true
  return false
}

function triggerBlink(idx, field) {
  errorBlink.value = true
  blinkCell.value = { idx, field }
  nextTick(() => {
    const el = field === 'debit' ? debitRefs[idx] : creditRefs[idx]
    el?.focus()
    el?.select()
  })
  setTimeout(() => {
    errorBlink.value = false
    blinkCell.value = null
  }, 700)
}

async function fetchAndShowOutstanding() {
  const row0 = rows.value[0]
  if (!row0.account) return false
  const partyType = row0.account_type || (isReceipt.value ? 'Customer' : 'Supplier')
  if (!['Customer', 'Supplier', 'Employee'].includes(partyType)) return false
  try {
    const res = await frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
      party: row0.account,
      party_type: partyType,
    })
    const today = new Date()
    outstandingInvoices.value = (res?.invoices || [])
      .filter(i => i.outstanding_amount > 0)
      .map(i => ({
        ...i,
        _alloc: 0,
        _days: Math.floor((today - new Date(i.posting_date)) / 86400000),
      }))
    if (outstandingInvoices.value.length > 0) {
      showOutstandingModal.value = true
      nextTick(() => {
        if (outstandingAllocRefs[0]) { outstandingAllocRefs[0].focus(); outstandingAllocRefs[0].select() }
        else outstandingProceedBtn.value?.focus()
      })
      return true
    }
  } catch (e) {}
  return false
}

function focusNextAllocOrProceed(i) {
  const next = outstandingAllocRefs[i + 1]
  if (next) { next.focus(); next.select() }
  else outstandingProceedBtn.value?.focus()
}

function fillRow1Amount() {
  const row0 = rows.value[0]
  const amount = isReceipt.value ? Number(row0.credit) : Number(row0.debit)
  if (rows.value.length < 2) addRow()
  const row1 = rows.value[1]
  if (isReceipt.value) { row1.debit = amount; row1.credit = 0 }
  else { row1.credit = amount; row1.debit = 0 }
}

function confirmOutstanding() {
  showOutstandingModal.value = false
  fillRow1Amount()
  activeRowIdx.value = 1
  openLedgerSearch(1)
}

async function moveNext(idx, field) {
  if (validationError.value) {
    triggerBlink(idx, field)
    return
  }
  const isBalanced = Math.abs(difference.value) < 0.01
  const hasValue = totalDebit.value > 0
  if (isBalanced && hasValue) {
    nextTick(() => remarksInput.value?.focus())
    return
  }
  if (idx === 0) {
    // Try to show outstanding bills; if none, go directly to row 1
    const shown = await fetchAndShowOutstanding()
    if (!shown) {
      fillRow1Amount()
      activeRowIdx.value = 1
      openLedgerSearch(1)
    }
    return
  }
  // Subsequent rows: move to next row ledger
  if (idx === rows.value.length - 1) addRow()
  else activeRowIdx.value = idx + 1
  nextTick(() => ledgerRefs[activeRowIdx.value]?.focus())
}

function handleRemarksEnter() {
  saveButton.value?.focus()
}

onMounted(async () => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  
  // Load GL account ledgers for row 2+
  try {
    mopLedgers.value = await frappeGet('ssplbilling.api.customersearch_api.get_user_mop_ledgers')
  } catch (e) {
    console.warn('Failed to load account ledgers:', e)
  }

  // Block page shortcuts while the outstanding modal is open
  useSubwindowWatcher(showOutstandingModal)

  useShortcuts(payrecShortcuts({
    switchToReceipt: () => { isReceipt.value = true },
    switchToPayment: () => { isReceipt.value = false },
    addRow: () => {
      if (showSearchModal.value) { showAllAccounts.value = true; nextTick(() => ledgerSearchModal.value?.focus()); return }
      addRow()
    },
    saveEntry: saveEntry,
    navigateUp: () => { if (showSearchModal.value) return; if (activeRowIdx.value > 0) activeRowIdx.value-- },
    navigateDown: () => { if (showSearchModal.value) return; if (activeRowIdx.value < rows.value.length - 1) activeRowIdx.value++ },
    focusDate: () => dateInput.value?.focus(),
    focusLastRow: () => {
      activeRowIdx.value = rows.value.length - 1
      nextTick(() => ledgerRefs[activeRowIdx.value]?.focus())
    },
    handleEnter: (e) => {
      if (showSearchModal.value) return
      const active = document.activeElement
      if (active.tagName === 'BUTTON') { active.click(); return }
      const isBalanced = Math.abs(difference.value) < 0.01
      const hasValue = totalDebit.value > 0
      if (isBalanced && hasValue && active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        remarksInput.value?.focus()
        return
      }
      if (active === document.body || !active) { activeRowIdx.value = 0; openLedgerSearch(0); return }
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') openLedgerSearch(activeRowIdx.value)
    },
    goBack: () => {
      if (showOutstandingModal.value) { confirmOutstanding(); return }
      router.push('/')
    }
  }))
  nextTick(() => ledgerRefs[0]?.focus())
})

async function saveEntry() {
  if (!canSave.value || isSubmitting.value) return
  isSubmitting.value = true
  try {
    const payload = {
      voucher_type: 'Journal Entry', // Standard JE for multiple row pay/rec
      posting_date: postingDate.value,
      user_remark: userRemarks.value,
      cheque_no: referenceNo.value,
      accounts: rows.value
        .filter(r => r.account)
        .map(r => ({
          account: r.account,
          account_type: r.account_type,
          debit_in_account_currency: r.debit,
          credit_in_account_currency: r.credit,
          user_remark: userRemarks.value
        }))
    }
    await frappePost('ssplbilling.api.journalcontra_api.create_journal_contra_entry', { data: payload })
    alert('Entry saved successfully!')
    userRemarks.value = ''
    referenceNo.value = ''
    rows.value = [
      { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    ]
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    isSubmitting.value = false
  }
}

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
})
</script>

<style scoped>
@keyframes blink {
  0%, 100% { opacity: 1; }
  25% { opacity: 0.2; }
  50% { opacity: 1; }
  75% { opacity: 0.2; }
}
.animate-blink {
  animation: blink 0.7s ease-in-out;
}
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #64748b; }
input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
