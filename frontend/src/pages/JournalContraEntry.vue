<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)]">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-[var(--color-text)] uppercase">
          {{ entryType === 'Contra' ? 'CONTRA ENTRY' : (entryType === 'Opening Entry' ? 'OPENING ENTRY' : 'JOURNAL ENTRY') }}
          <span v-if="companyName" class="normal-case font-normal text-[var(--color-text-muted)] text-sm border-l border-[var(--color-border)] pl-2.5 ml-2.5">
            {{ companyName }}
          </span>
        </h1>
        <div class="h-4 w-px bg-[var(--color-surface-raised)] mx-2"></div>
        <div class="flex rounded-xl bg-[var(--color-surface-raised)] p-1.5 shadow-inner">
          <button
            @click="entryType = 'Journal Entry'"
            class="rounded-lg px-6 py-1.5 text-3xl font-black transition-all flex items-center gap-2"
            :class="entryType === 'Journal Entry' ? 'bg-[var(--color-surface)] text-[var(--color-info)] shadow-md' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          >
            <span>Journal</span>
          </button>
          <button
            @click="entryType = 'Contra'"
            class="rounded-lg px-6 py-1.5 text-3xl font-black transition-all flex items-center gap-2"
            :class="entryType === 'Contra' ? 'bg-[var(--color-surface)] text-[var(--color-success)] shadow-md' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          >
            <span>Contra</span>
          </button>
          <button
            @click="entryType = 'Opening Entry'"
            class="rounded-lg px-6 py-1.5 text-3xl font-black transition-all flex items-center gap-2"
            :class="entryType === 'Opening Entry' ? 'bg-[var(--color-surface)] text-[var(--color-warning)] shadow-md' : 'text-[var(--color-text-muted)] hover:text(--color-text)'"
          >
            <span>Opening Entry</span>
          </button>
          <div class="flex items-center ml-4 px-3 border-l border-[var(--color-border)]">
            <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-xs font-bold text-[var(--color-text-muted)] shadow-sm">F7 to Cycle</kbd>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- Account selection for Expense Entry -->
        <div v-if="entryType === 'Opening Entry'" class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-warning)]/40 shadow-sm transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
          <label class="text-sm font-black uppercase tracking-widest text-[var(--color-warning)] group-focus-within:text-[var(--color-text-on-focus)]">Account</label>
          <div
            ref="balancingAccountRef"
            @click="showBalancingSearch = true"
            tabindex="0"
            class="min-w-[300px] px-3 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-xl font-bold text-[var(--color-text)] cursor-pointer hover:border-[var(--color-focus)] transition-all flex items-center justify-between outline-none focus:ring-2 focus:ring-[var(--color-focus)] group-focus-within:border-black/20"
          >
            <span :class="!balancingAccount.name ? 'text-[var(--color-text-muted)] italic font-normal' : ''">
              {{ balancingAccount.label || 'Select Account...' }}
            </span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)] group-focus-within:text-black/50"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>

        <div class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
          <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)] group-focus-within:text-[var(--color-text-on-focus)]">Posting Date</label>
          <div class="flex items-center gap-1">
            <button
              @click="changeDate(-1)"
              class="p-1 hover:bg-black/10 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all group-focus-within:text-black/70"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              ref="dateInput"
              v-model="displayDate"
              type="text"
              class="bg-transparent text-xl font-black text-[var(--color-text)] outline-none focus:text-inherit w-44 font-mono placeholder:text-inherit"
              placeholder="DD/MM/YYYY"
              @focus="e => e.target.select()"
              @input="onDateInput"
            />
            <button
              @click="changeDate(1)"
              class="p-1 hover:bg-black/10 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all group-focus-within:text-black/70"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="flex-1 overflow-hidden p-6">
      <div class="h-full flex flex-col bg-[var(--color-surface)] rounded-2xl shadow-sm border border-[var(--color-border)] overflow-hidden">
        <!-- TABLE -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <table class="w-full border-collapse border border-[var(--color-border)]">
            <thead class="sticky top-0 z-10 bg-[var(--color-surface-raised)]">
              <tr class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] text-left">
                <th class="px-4 py-2 w-12 text-center border border-[var(--color-border)]">#</th>
                <th class="px-3 py-2 min-w-[300px] border border-[var(--color-border)]">Ledger</th>
                <th class="px-4 py-2 w-72 text-right border border-[var(--color-border)]">Balance</th>
                <th class="px-4 py-2 w-72 text-right border border-[var(--color-border)]">Debit (₹)</th>
                <th class="px-4 py-2 w-72 text-right border border-[var(--color-border)]">Credit (₹)</th>
                <th class="px-4 py-2 w-72 text-right border border-[var(--color-border)]">New Bal</th>
                <th class="px-4 py-2 w-12 border border-[var(--color-border)]"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, idx) in rows"
                :key="idx"
                class="group transition-colors"
              >
                <td class="px-4 py-0 text-center text-sm font-bold text-[var(--color-text-muted)] border border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                  {{ idx + 1 }}
                </td>
                <td class="px-0 py-0 border border-[var(--color-border)] relative transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <div
                    :ref="el => { if (el) ledgerRefs[idx] = el }"
                    @click="openLedgerSearch(idx)"
                    @keydown.enter.prevent.stop="openLedgerSearch(idx)"
                    tabindex="0"
                    class="w-full h-full min-h-[56px] px-3 py-2 text-2xl font-bold cursor-pointer hover:bg-black/5 transition-all flex items-center justify-between outline-none focus:ring-2 focus:ring-inset focus:ring-[var(--color-focus)]"
                    :class="row.account ? 'text-inherit' : 'text-[var(--color-text-muted)] italic group-focus-within:text-inherit/60'"
                  >
                    <span class="truncate">{{ row.account_name || 'Select Ledger...' }}</span>
                  </div>
                </td>
                <td class="px-3 py-0 text-right border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30">
                  <div v-if="row.account" class="text-3xl font-bold text-[var(--color-text-muted)] font-mono whitespace-nowrap">
                    {{ formatBalance(row.current_balance) }}
                  </div>
                </td>
                <td class="px-0 py-0 border border-[var(--color-border)] transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <input
                    :ref="el => { if (el) debitRefs[idx] = el }"
                    v-model.number="row.debit"
                    @focus="activeRowIdx = idx"
                    @input="row.credit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'debit')"
                    :disabled="isFieldDisabled(idx, 'debit')"
                    :tabindex="isFieldDisabled(idx, 'debit') ? -1 : 0"
                    type="number"
                    class="w-full h-[56px] bg-transparent px-3 py-0 text-right font-mono text-3xl font-bold text-[var(--color-text)] outline-none focus:bg-black/5 focus:ring-2 focus:ring-inset focus:ring-[var(--color-focus)] transition-all disabled:opacity-20 focus:text-inherit placeholder:text-inherit"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'debit' ? 'bg-[var(--color-danger)]/20 animate-blink' : ''"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-0 py-0 border border-[var(--color-border)] transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <input
                    :ref="el => { if (el) creditRefs[idx] = el }"
                    v-model.number="row.credit"
                    @focus="activeRowIdx = idx"
                    @input="row.debit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'credit')"
                    :disabled="isFieldDisabled(idx, 'credit')"
                    :tabindex="isFieldDisabled(idx, 'credit') ? -1 : 0"
                    type="number"
                    class="w-full h-[56px] bg-transparent px-3 py-0 text-right font-mono text-3xl font-bold text-[var(--color-text)] outline-none focus:bg-black/5 focus:ring-2 focus:ring-inset focus:ring-[var(--color-focus)] transition-all disabled:opacity-20 focus:text-inherit placeholder:text-inherit"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'credit' ? 'bg-[var(--color-danger)]/20 animate-blink' : ''"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-3 py-0 text-right border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30">
                  <div v-if="row.account" class="text-3xl font-bold font-mono whitespace-nowrap" :class="getNewBalance(row) !== row.current_balance ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">
                    {{ formatBalance(getNewBalance(row)) }}
                  </div>
                </td>
                <td class="px-0 py-0 text-center border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30">
                  <button
                    @click="removeRow(idx)"
                    class="w-full h-[56px] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors opacity-0 group-hover:opacity-100"
                    tabindex="-1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="p-4">
            <button
              @click="addRow"
              class="flex items-center gap-2 rounded-xl border border-dashed border-[var(--color-border)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] hover:border-[var(--color-info)] hover:text-[var(--color-info)] hover:bg-[var(--color-info)]/10 transition-all w-full justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              Add New Row (INS)
            </button>
          </div>
        </div>

        <!-- FOOTER: TOTALS -->
        <div class="shrink-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-6 flex flex-col gap-4">
          <!-- ERROR ALERT -->
          <div v-if="validationError" class="flex items-center gap-2 bg-[var(--color-danger)]/20 text-[var(--color-danger)] px-4 py-2 rounded-lg border border-[var(--color-danger)] text-xs font-bold" :class="errorBlink ? 'animate-blink' : ''">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
            {{ validationError }}
          </div>

          <div class="flex items-start justify-between">
            <div class="flex-1 max-w-xl">
              <div class="group rounded-xl transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5 -m-1.5">
                <label class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1 block transition-colors group-focus-within:text-inherit">Remarks</label>
                <textarea
                  ref="remarksInput"
                  v-model="userRemarks"
                  @keydown.enter.prevent="handleRemarksEnter"
                  rows="2"
                  class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-2xl font-bold text-[var(--color-text)] outline-none focus:bg-black/5 transition-all shadow-sm focus:text-inherit placeholder:text-inherit"
                  placeholder="Internal notes..."
                ></textarea>
              </div>
            </div>
            <div class="flex gap-12 ml-12">
              <div v-if="entryType !== 'Opening Entry'" class="text-right">
                <div class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Debit</div>
                <div class="text-5xl font-black text-[var(--color-text)] font-mono">₹ {{ fmt(totalDebit) }}</div>
              </div>
              <div v-if="entryType !== 'Opening Entry'" class="text-right">
                <div class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Credit</div>
                <div class="text-5xl font-black text-[var(--color-text)] font-mono">₹ {{ fmt(totalCredit) }}</div>
              </div>
              <div class="text-right border-l border-[var(--color-border)] pl-12" :class="{ 'border-none': entryType === 'Opening Entry' }">
                <div v-if="entryType !== 'Opening Entry'">
                  <div class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Difference</div>
                  <div
                    class="text-5xl font-black font-mono"
                    :class="Math.abs(difference) < 0.01 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
                  >
                    ₹ {{ fmt(difference) }}
                  </div>
                </div>
                <!-- SAVE BUTTON -->
                <div class="mt-4 flex justify-end">
                  <button
                    ref="saveButton"
                    @click="saveEntry"
                    @keydown.enter="saveEntry"
                    :disabled="isSubmitting || !canSave || submitting"
                    class="flex items-center gap-2 rounded-xl bg-[var(--color-info)] px-8 py-3 text-base font-bold text-[var(--color-text-on-highlight)] shadow-lg shadow-blue-900/50 hover:bg-[var(--color-info)] transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    <span v-if="isSubmitting" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent mr-1"></span>
                    <span>Save Entry</span>
                    <kbd class="ml-2 rounded border border-[var(--color-info)] bg-[var(--color-info)] px-2 py-0.5 font-mono text-xs text-[var(--color-text-on-focus)]">F9</kbd>
                  </button>
                </div>
              </div>
            </div>
          </div>
      </div>
      </div>
    </div>

    <!-- MODAL -->
    <CustomerSearchModal
      ref="ledgerSearchModal"
      :allowed-types="entryType === 'Contra' ? ['Account'] : ['Customer', 'Supplier', 'Employee', 'Account']"
      :initial-type="entryType === 'Contra' ? 'Account' : 'All'"
      :show="showSearchModal"
      :skip-date-filter="true"
      :hideSecondary="true"
      @close="showSearchModal = false"
      @select="selectLedger"
    />

    <CustomerSearchModal
      :show="showBalancingSearch"
      :allowed-types="['Customer', 'Supplier', 'Employee', 'Account']"
      initial-type="Account"
      :skip-date-filter="true"
      :hideSecondary="true"
      @close="showBalancingSearch = false"
      @select="ledger => { balancingAccount = { name: ledger.name, label: ledger.label }; showBalancingSearch = false }"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useShortcuts } from '../services/shortcutManager'
import { journalContraShortcuts } from '../shortcuts/journalContraShortcuts'

const router = useRouter()
const companyName = computed(() => localStorage.getItem('wb-company') || '')

// --- STATE ---
const entryType = ref('Journal Entry')
const cashAccount = localStorage.getItem('wb-cash') || ''
const balancingAccount = ref({ name: '', label: '' })
const balancingAccountRef = ref(null)
const isContra = computed(() => entryType.value === 'Contra')

const showBalancingSearch = ref(false)

watch(entryType, () => {
  rows.value = [
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
  ]
  balancingAccount.value = {
    name: entryType.value === 'Opening Entry' ? cashAccount : '',
    label: entryType.value === 'Opening Entry' ? cashAccount : ''
  }
  activeRowIdx.value = 0
  nextTick(() => {
    // Focus to first row ledger search as requested
    ledgerRefs[0]?.focus()
  })
})

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
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
  let val = e.target.value.replace(/\D/g, '') // Keep only digits
  
  // Smart Year Logic: If user enters 4 digits (DDMM), auto-complete the current year
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

  // Basic formatting as user types beyond 2 digits
  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '/' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '/' + val.slice(2, 4) + '/' + val.slice(4, 8)
  }
  displayDate.value = val

  // Try to update ISO if we have a full valid date
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

const userRemarks = ref('')
const rows = ref([
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
])
const activeRowIdx = ref(0)
const isSubmitting = ref(false)
const submitting = ref(false)
const showSearchModal = ref(false)
const ledgerSearchModal = ref(null)
const remarksInput = ref(null)
const saveButton = ref(null)
const errorBlink = ref(false)
const blinkCell = ref(null)

// Template Refs for Navigation (using plain arrays for function refs)
const ledgerRefs = []
const debitRefs = []
const creditRefs = []

// --- COMPUTED ---
const totalDebit = computed(() => rows.value.reduce((s, r) => s + (Number(r.debit) || 0), 0))
const totalCredit = computed(() => rows.value.reduce((s, r) => s + (Number(r.credit) || 0), 0))
const difference = computed(() => totalDebit.value - totalCredit.value)

const validationError = computed(() => {
  if (entryType.value === 'Opening Entry') return null
  
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
  const activeRows = rows.value.filter(r => r.account)
  if (entryType.value === 'Opening Entry') {
    return activeRows.length >= 1 && 
           balancingAccount.value.name &&
           activeRows.every(r => (Number(r.debit) > 0 || Number(r.credit) > 0))
  }
  return activeRows.length >= 2 && 
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

  // Auto-fill amount for 2nd row if there's a difference
  if (activeRowIdx.value === 1 && entryType.value !== 'Opening Entry') {
    const diff = difference.value
    if (Math.abs(diff) > 0.005) {
      if (diff > 0) {
        row.credit = diff
        row.debit = 0
      } else {
        row.debit = Math.abs(diff)
        row.credit = 0
      }
    }
  }
  
  // Move focus to next available column after selection
  nextTick(() => {
    let el = null
    // Prioritize the field that has a value (useful for Journal entries where both are enabled)
    if (row.credit > 0.005 && row.debit === 0) {
      el = creditRefs[activeRowIdx.value]
    } else if (isFieldDisabled(activeRowIdx.value, 'debit')) {
      el = creditRefs[activeRowIdx.value]
    } else {
      el = debitRefs[activeRowIdx.value]
    }
    
    if (el) {
      el.focus()
      el.select()
    }
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
  // Opening and Journal entries allow full flexibility
  if (entryType.value === 'Opening Entry' || entryType.value === 'Journal Entry') return false

  // Contra entry logic: follow row 0
  const firstRowDebit = Number(rows.value[0]?.debit) || 0
  const firstRowCredit = Number(rows.value[0]?.credit) || 0
  if (firstRowDebit > 0.005) {
    if (idx === 0 && field === 'credit') return true
    if (idx > 0 && field === 'debit') return true
  }
  if (firstRowCredit > 0.005) {
    if (idx === 0 && field === 'debit') return true
    if (idx > 0 && field === 'credit') return true
  }
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

function moveNext(idx, field) {
  if (validationError.value) {
    triggerBlink(idx, field)
    return
  }

  const isBalanced = Math.abs(difference.value) < 0.01
  const hasValue = totalDebit.value > 0

  if (isBalanced && hasValue) {
    nextTick(() => {
      remarksInput.value?.focus()
    })
    return
  }

  if (field === 'debit') {
    // If first row debit > 0, move straight to second row ledger search
    if (idx === 0 && Number(rows.value[0].debit) > 0.005) {
      if (rows.value.length < 2) addRow()
      activeRowIdx.value = 1
      openLedgerSearch(1)
      return
    }
    
    const el = creditRefs[idx]
    if (el) {
      el.focus()
      el.select()
    }
  } else if (field === 'credit') {
    // Not balanced (checked at top), move to next row or add one
    if (idx === rows.value.length - 1) {
      addRow()
    } else {
      activeRowIdx.value = idx + 1
    }
    nextTick(() => {
      ledgerRefs[activeRowIdx.value]?.focus()
    })
  }
}

function handleRemarksEnter() {
  saveButton.value?.focus()
}

const ENTRY_TYPES = ['Journal Entry', 'Contra', 'Opening Entry']
function cycleEntryType() {
  const currentIdx = ENTRY_TYPES.indexOf(entryType.value)
  const nextIdx = (currentIdx + 1) % ENTRY_TYPES.length
  entryType.value = ENTRY_TYPES[nextIdx]
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  // Mount shortcuts on pageload
  useShortcuts(journalContraShortcuts({
    cycleEntryType,
    addRow: addRow,
    saveEntry: saveEntry,
    navigateUp: () => {
      if (activeRowIdx.value > 0) activeRowIdx.value--
    },
    navigateDown: () => {
      if (activeRowIdx.value < rows.value.length - 1) activeRowIdx.value++
    },
    focusDate: () => {
      dateInput.value?.focus()
    },
    focusLastRow: () => {
      activeRowIdx.value = rows.value.length - 1
      nextTick(() => {
        ledgerRefs[activeRowIdx.value]?.focus()
      })
    },
    jumpToRemarks: () => {
      remarksInput.value?.focus()
    },
    handleEnter: (e) => {
      if (showSearchModal.value) return
      const active = document.activeElement
      
      // If a button is focused, click it
      if (active.tagName === 'BUTTON') {
        active.click()
        return
      }

      const isBalanced = Math.abs(difference.value) < 0.01
      const hasValue = totalDebit.value > 0

      // If balanced and not in an input, go to remarks
      if (isBalanced && hasValue && active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        remarksInput.value?.focus()
        return
      }

      if (active === document.body || !active) {
        activeRowIdx.value = 0
        openLedgerSearch(0)
        return
      }
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
         openLedgerSearch(activeRowIdx.value)
      }
    },
    goBack: () => router.push('/')
  }))

  nextTick(() => {
    ledgerRefs[0]?.focus()
  })
})

async function saveEntry() {
  if (!canSave.value || isSubmitting.value || submitting.value) return
  isSubmitting.value = true
  submitting.value = true
  try {
    const payload = {
      voucher_type: entryType.value === 'Opening Entry' ? 'Journal Entry' : entryType.value,
      posting_date: postingDate.value,
      company: localStorage.getItem('wb-company') || null,
      user_remark: userRemarks.value,
      balancing_account: balancingAccount.value.name,
      accounts: rows.value
        .filter(r => r.account)
        .map(r => ({
          account: r.account,
          account_type: r.account_type,
          debit_in_account_currency: r.debit,
          credit_in_account_currency: r.credit,
          cost_center: localStorage.getItem('wb-cost-center') || null,
          user_remark: userRemarks.value
        }))
    }

    // We'll need a backend method for this or use frappe.client.insert
    await frappePost('ssplbilling.api.journalcontra_api.create_journal_contra_entry', { data: payload })
    alert('Entry saved successfully!')
    userRemarks.value = ''
    rows.value = [
      { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    ]
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    isSubmitting.value = false
    submitting.value = false
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

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
