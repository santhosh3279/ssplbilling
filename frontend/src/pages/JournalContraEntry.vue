<template>
  <div class="flex h-screen flex-col bg-slate-50 font-sans text-slate-900">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button 
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-slate-900">{{ isContra ? 'CONTRA ENTRY' : 'JOURNAL ENTRY' }}</h1>
      </div>

      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end mr-4">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Posting Date</label>
          <input 
            v-model="postingDate"
            type="date"
            class="bg-transparent text-sm font-bold text-slate-700 outline-none focus:text-blue-600"
          />
        </div>
        <button 
          ref="saveButton"
          @click="saveEntry"
          @keydown.enter="saveEntry"
          :disabled="isSubmitting || !canSave"
          class="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
        >
          <span v-if="isSubmitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span>Save Entry</span>
          <kbd class="ml-1 rounded border border-blue-400 bg-blue-500 px-1.5 py-0.5 font-mono text-[10px] text-blue-100">F9</kbd>
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-hidden p-6">
      <div class="h-full flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <!-- TABLE -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 z-10 bg-slate-50 border-b border-slate-200">
              <tr class="text-xs font-bold uppercase tracking-wider text-slate-500 text-left">
                <th class="px-4 py-2 w-12 text-center">#</th>
                <th class="px-2 py-2 min-w-[300px]">Ledger</th>
                <th class="px-4 py-2 w-80 text-right">Balance</th>
                <th class="px-4 py-2 w-80 text-right">Debit (₹)</th>
                <th class="px-4 py-2 w-80 text-right">Credit (₹)</th>
                <th class="px-4 py-2 w-80 text-right">New Bal</th>
                <th class="px-4 py-2 w-12"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr 
                v-for="(row, idx) in rows" 
                :key="idx"
                class="group hover:bg-slate-50/50 transition-colors"
                :class="{ 'bg-blue-50/30': activeRowIdx === idx }"
              >
                <td class="px-4 py-0.5 text-center text-sm font-bold text-slate-400">
                  {{ idx + 1 }}
                </td>
                <td class="px-2 py-0.5">
                  <div 
                    :ref="el => { if (el) ledgerRefs[idx] = el }"
                    @click="openLedgerSearch(idx)"
                    @keydown.enter.prevent.stop="openLedgerSearch(idx)"
                    tabindex="0"
                    class="w-full rounded-lg border border-transparent px-3 py-0.5 text-2xl font-bold cursor-pointer hover:border-slate-300 hover:bg-white transition-all flex items-center justify-between group/input outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white focus:border-blue-500"
                    :class="row.account ? 'text-slate-900' : 'text-slate-300 italic'"
                  >
                    <span class="truncate">{{ row.account_name || 'Select Ledger...' }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-300 group-hover/input:text-blue-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                  </div>
                </td>
                <td class="px-2 py-0 text-right">
                  <div v-if="row.account" class="text-2xl font-bold text-slate-500 font-mono whitespace-nowrap">
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
                    class="w-full rounded-lg border bg-transparent px-3 py-0 text-right font-mono text-2xl font-bold text-slate-900 outline-none focus:bg-white transition-all disabled:opacity-20"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'debit' ? 'border-rose-500 bg-rose-50 animate-blink' : 'border-transparent focus:border-blue-500'"
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
                    class="w-full rounded-lg border bg-transparent px-3 py-0 text-right font-mono text-2xl font-bold text-slate-900 outline-none focus:bg-white transition-all disabled:opacity-20"
                    :class="blinkCell?.idx === idx && blinkCell?.field === 'credit' ? 'border-rose-500 bg-rose-50 animate-blink' : 'border-transparent focus:border-blue-500'"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-2 py-0 text-right">
                  <div v-if="row.account" class="text-2xl font-bold font-mono whitespace-nowrap" :class="getNewBalance(row) !== row.current_balance ? 'text-blue-600' : 'text-slate-400'">
                    {{ formatBalance(getNewBalance(row)) }}
                  </div>
                </td>
                <td class="px-4 py-1 text-center">
                  <button 
                    @click="removeRow(idx)"
                    class="text-slate-300 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
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
              class="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 px-4 py-2 text-xs font-bold text-slate-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-all w-full justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              Add New Row (INS)
            </button>
          </div>
        </div>

        <!-- FOOTER: TOTALS -->
        <div class="shrink-0 bg-slate-50 border-t border-slate-200 p-6 flex flex-col gap-4">
          <!-- ERROR ALERT -->
          <div v-if="validationError" class="flex items-center gap-2 bg-rose-50 text-rose-600 px-4 py-2 rounded-lg border border-rose-100 text-xs font-bold" :class="errorBlink ? 'animate-blink' : ''">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
            {{ validationError }}
          </div>

          <div class="flex items-start justify-between">
            <div class="flex-1 max-w-xl">
              <div>
                <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1 block">Remarks</label>
                <textarea
                  ref="remarksInput"
                  v-model="userRemarks"
                  @keydown.enter.prevent="handleRemarksEnter"
                  rows="2"
                  class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all shadow-sm"
                  placeholder="Internal notes..."
                ></textarea>
              </div>
            </div>
            <div class="flex gap-12 ml-12">
              <div class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Total Debit</div>
                <div class="text-2xl font-black text-slate-900 font-mono">₹ {{ fmt(totalDebit) }}</div>
              </div>
              <div class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Total Credit</div>
                <div class="text-2xl font-black text-slate-900 font-mono">₹ {{ fmt(totalCredit) }}</div>
              </div>
              <div class="text-right border-l border-slate-200 pl-12">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Difference</div>
                <div 
                  class="text-2xl font-black font-mono"
                  :class="Math.abs(difference) < 0.01 ? 'text-emerald-600' : 'text-rose-600'"
                >
                  ₹ {{ fmt(difference) }}
                </div>
                <!-- MODE TOGGLE -->
                <div class="mt-4 flex justify-end">
                  <div class="flex rounded-lg bg-slate-200/50 p-1 shadow-inner">
                    <button 
                      @click="isContra = false"
                      class="rounded-md px-6 py-1.5 text-xs font-bold transition-all flex items-center gap-2"
                      :class="!isContra ? 'bg-white text-blue-600 shadow-sm border border-slate-200' : 'text-slate-500 hover:text-slate-700'"
                    >
                      <span>JOURNAL</span>
                      <kbd class="rounded border px-1 text-[9px] opacity-50" :class="!isContra ? 'border-blue-200 bg-blue-50' : 'border-slate-300 bg-slate-50'">F2</kbd>
                    </button>
                    <button 
                      @click="isContra = true"
                      class="rounded-md px-6 py-1.5 text-xs font-bold transition-all flex items-center gap-2"
                      :class="isContra ? 'bg-white text-emerald-600 shadow-sm border border-slate-200' : 'text-slate-500 hover:text-slate-700'"
                    >
                      <span>CONTRA</span>
                      <kbd class="rounded border px-1 text-[9px] opacity-50" :class="isContra ? 'border-emerald-200 bg-emerald-50' : 'border-slate-300 bg-slate-50'">F3</kbd>
                    </button>
                  </div>
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
      :show="showSearchModal"
      :allowed-types="isContra ? ['Account'] : ['Customer', 'Supplier']"
      :initial-type="isContra ? 'Account' : 'All'"
      :skip-date-filter="true"
      @close="showSearchModal = false"
      @select="selectLedger"
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

// --- STATE ---
const isContra = ref(false)

watch(isContra, () => {
  rows.value = [
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
  ]
  activeRowIdx.value = 0
  nextTick(() => ledgerRefs[0]?.focus())
})

const postingDate = ref(new Date().toISOString().slice(0, 10))
const userRemarks = ref('')
const rows = ref([
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
])
const activeRowIdx = ref(0)
const isSubmitting = ref(false)
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
  
  // Move focus to next available column after selection
  nextTick(() => {
    let el = null
    if (isFieldDisabled(activeRowIdx.value, 'debit')) {
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

onMounted(() => {
  // Mount shortcuts on pageload
  useShortcuts(journalContraShortcuts({
    switchToJournal: () => { isContra.value = false },
    switchToContra: () => { isContra.value = true },
    addRow: addRow,
    saveEntry: saveEntry,
    navigateUp: () => {
      if (activeRowIdx.value > 0) activeRowIdx.value--
    },
    navigateDown: () => {
      if (activeRowIdx.value < rows.value.length - 1) activeRowIdx.value++
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
  if (!canSave.value || isSubmitting.value) return
  isSubmitting.value = true
  try {
    const payload = {
      voucher_type: isContra.value ? 'Contra' : 'Journal Entry',
      posting_date: postingDate.value,
      user_remark: userRemarks.value,
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

    // We'll need a backend method for this or use frappe.client.insert
    await frappePost('ssplbilling.api.ledgerentry_api.create_journal_entry', { data: payload })
    alert('Entry saved successfully!')
    userRemarks.value = ''
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
  background: #cbd5e1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
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
