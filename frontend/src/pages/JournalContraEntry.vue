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
        <div class="h-4 w-px bg-slate-200 mx-2"></div>
        <div class="flex rounded-lg bg-slate-100 p-1">
          <button 
            @click="isContra = false"
            class="rounded-md px-4 py-1 text-xs font-bold transition-all"
            :class="!isContra ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            Journal
          </button>
          <button 
            @click="isContra = true"
            class="rounded-md px-4 py-1 text-xs font-bold transition-all"
            :class="isContra ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            Contra
          </button>
        </div>
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
          @click="saveEntry"
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
              <tr class="text-[11px] font-bold uppercase tracking-wider text-slate-500 text-left">
                <th class="px-6 py-4 w-12 text-center">#</th>
                <th class="px-4 py-4 min-w-[250px]">Ledger</th>
                <th class="px-4 py-4 w-32 text-right">Balance</th>
                <th class="px-4 py-4 w-32 text-right">Debit (₹)</th>
                <th class="px-4 py-4 w-32 text-right">Credit (₹)</th>
                <th class="px-4 py-4 w-32 text-right">New Bal</th>
                <th class="px-6 py-4 w-12"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr 
                v-for="(row, idx) in rows" 
                :key="idx"
                class="group hover:bg-slate-50/50 transition-colors"
                :class="{ 'bg-blue-50/30': activeRowIdx === idx }"
              >
                <td class="px-6 py-4 text-center text-xs font-bold text-slate-400">
                  {{ idx + 1 }}
                </td>
                <td class="px-4 py-2">
                  <div 
                    ref="ledgerRefs"
                    @click="openLedgerSearch(idx)"
                    @keydown.enter.prevent.stop="openLedgerSearch(idx)"
                    tabindex="0"
                    class="w-full rounded-lg border border-transparent px-3 py-2 text-sm font-bold cursor-pointer hover:border-slate-300 hover:bg-white transition-all flex items-center justify-between group/input outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white focus:border-blue-500"
                    :class="row.account ? 'text-slate-900' : 'text-slate-300 italic'"
                  >
                    <span class="truncate">{{ row.account_name || 'Select Ledger...' }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-300 group-hover/input:text-blue-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                  </div>
                </td>
                <td class="px-4 py-2 text-right">
                  <div v-if="row.account" class="text-xs font-bold text-slate-500 font-mono">
                    {{ formatBalance(row.current_balance) }}
                  </div>
                </td>
                <td class="px-4 py-2">
                  <input 
                    ref="debitRefs"
                    v-model.number="row.debit"
                    @focus="activeRowIdx = idx"
                    @input="row.credit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'debit')"
                    type="number"
                    class="w-full rounded-lg border border-transparent bg-transparent px-3 py-2 text-right font-mono text-sm font-bold text-slate-900 outline-none focus:border-blue-500 focus:bg-white transition-all"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-4 py-2">
                  <input 
                    ref="creditRefs"
                    v-model.number="row.credit"
                    @focus="activeRowIdx = idx"
                    @input="row.debit = 0"
                    @keydown.enter.prevent="moveNext(idx, 'credit')"
                    type="number"
                    class="w-full rounded-lg border border-transparent bg-transparent px-3 py-2 text-right font-mono text-sm font-bold text-slate-900 outline-none focus:border-blue-500 focus:bg-white transition-all"
                    placeholder="0.00"
                  />
                </td>
                <td class="px-4 py-2 text-right">
                  <div v-if="row.account" class="text-xs font-bold font-mono" :class="getNewBalance(row) !== row.current_balance ? 'text-blue-600' : 'text-slate-400'">
                    {{ formatBalance(getNewBalance(row)) }}
                  </div>
                </td>
                <td class="px-6 py-2 text-center">
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
          
          <div class="p-4">
            <button 
              @click="addRow"
              class="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 px-4 py-2 text-xs font-bold text-slate-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-all w-full justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              Add New Row (F2)
            </button>
          </div>
        </div>

        <!-- FOOTER: TOTALS -->
        <div class="shrink-0 bg-slate-50 border-t border-slate-200 p-6 flex items-start justify-between">
          <div class="flex-1 max-w-xl">
            <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1 block">Reference Note / Remarks</label>
            <textarea 
              v-model="userRemarks"
              rows="2"
              class="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all shadow-sm"
              placeholder="Enter reference number, cheque details or internal notes..."
            ></textarea>
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
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 },
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
  ]
  activeRowIdx.value = 0
})

const postingDate = ref(new Date().toISOString().slice(0, 10))
const userRemarks = ref('')
const rows = ref([
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 },
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
])
const activeRowIdx = ref(0)
const isSubmitting = ref(false)
const showSearchModal = ref(false)
const ledgerSearchModal = ref(null)

// Template Refs for Navigation
const ledgerRefs = ref([])
const debitRefs = ref([])
const creditRefs = ref([])

// --- COMPUTED ---
const totalDebit = computed(() => rows.value.reduce((s, r) => s + (Number(r.debit) || 0), 0))
const totalCredit = computed(() => rows.value.reduce((s, r) => s + (Number(r.credit) || 0), 0))
const difference = computed(() => totalDebit.value - totalCredit.value)
const canSave = computed(() => {
  return rows.value.filter(r => r.account).length >= 2 && 
         Math.abs(difference.value) < 0.01 && 
         totalDebit.value > 0
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
  if (rows.value.length <= 2) {
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
  
  // Move focus to Debit after selection
  nextTick(() => {
    debitRefs.value[activeRowIdx.value]?.focus()
    debitRefs.value[activeRowIdx.value]?.select()
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

function moveNext(idx, field) {
  if (field === 'debit') {
    creditRefs.value[idx]?.focus()
    creditRefs.value[idx]?.select()
  } else if (field === 'credit') {
    // If it's the last row, add a new one
    if (idx === rows.value.length - 1) {
      addRow()
    } else {
      activeRowIdx.value = idx + 1
    }
    // Move to next row ledger
    nextTick(() => {
      ledgerRefs.value[activeRowIdx.value]?.focus()
    })
  }
}

// --- SHORTCUTS ---
useShortcuts(journalContraShortcuts({
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
    const target = e.target
    if (target.tagName !== 'INPUT') {
       openLedgerSearch(activeRowIdx.value)
    }
  },
  goBack: () => router.push('/')
}))

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
      { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 },
      { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    ]
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
})

onUnmounted(() => {
})
</script>

<style scoped>
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
