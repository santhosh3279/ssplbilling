<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header 
      class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-2.5 shadow-sm transition-colors duration-300"
      :class="activeTab === 'Payment' ? 'bg-red-500/30' : 'bg-green-500/30'"
    >
      <!-- Left: back + title -->
      <div class="flex items-center gap-3">
        <button
          @click="handleBack"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">
          Single Entry
          <span 
            v-if="cashAccount.name" 
            ref="cashAccountBtnRef"
            tabindex="0"
            @click="openSearchAccount"
            @keydown.enter.prevent="openSearchAccount"
            class="ml-4 text-2xl font-normal text-black bg-black/5 hover:bg-black/10 focus:bg-black/10 focus:ring-2 focus:ring-black/20 focus:outline-none cursor-pointer px-4 py-1.5 rounded-full border border-black/10 shadow-sm transition-all animate-in fade-in slide-in-from-left-4 duration-500 inline-flex items-center gap-2"
          >
            <span class="opacity-60 font-normal">{{ activeTab === 'Receipt' ? 'RECEIVE INTO:' : 'PAY FROM:' }}</span> 
            <span>{{ cashAccount.name }}</span>
          </span>
        </h1>
      </div>

      <!-- Center: Tabs -->
      <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5 items-center">
        <button
          v-for="t in ['Payment', 'Receipt']"
          :key="t"
          @click="onTabClick(t)"
          class="min-w-[110px] rounded-md px-4 py-1 text-2xl font-black uppercase tracking-wide transition-all duration-200"
          :class="activeTab === t
            ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)]'"
        >
          {{ t }}
        </button>
        <div class="flex items-center ml-4 px-3 border-l border-[var(--color-border)]">
          <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-xs font-bold text-[var(--color-text-muted)] shadow-sm">F7 to Cycle</kbd>
        </div>
      </div>

      <!-- Right: Posting Date -->
      <div class="flex items-center gap-2">
        <span class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</span>
        <div class="flex items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] transition-colors">
          <button @click="adjustDate(-1)" class="p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] transition-colors"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m15 18-6-6 6-6"/></svg></button>
          <div class="relative min-w-[110px] px-3 py-1.5 text-center">
            <span class="text-2xl">{{ displayDate }}</span>
            <input type="date" v-model="postingDate" class="absolute inset-0 opacity-0 cursor-pointer focus:outline-none" />
          </div>
          <button @click="adjustDate(1)" class="p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] transition-colors"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m9 18 6-6-6-6"/></svg></button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden p-4">
      <div class="flex h-full flex-col gap-4">
        
        <div class="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
          <table class="w-full text-left border-collapse">
            <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
              <tr class="text-3xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-4 py-2 w-1/4">Party</th>
                <th 
                  class="px-4 py-2 text-right w-48"
                  :class="activeTab === 'Receipt' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
                >
                  {{ activeTab === 'Receipt' ? 'Credit (Cr)' : 'Debit (Dr)' }}
                </th>
                <th class="px-4 py-2 w-1/4">Remarks</th>
                <th class="px-4 py-2 w-[350px]">Links</th>
                <th class="px-6 py-2 text-right w-48">Balance</th>
                <th class="px-6 py-2 text-right w-48">New Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in form.rows" :key="idx" class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)]">
                <td class="px-2 py-1.5 group hover:bg-[var(--color-midlight)]/20 transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <div class="relative">
                    <input
                      v-model="row.query"
                      :ref="el => { if (el) expenseSearchRefs[idx] = el }"
                      @click="openSearch(idx)"
                      @keydown.enter="handleAccountEnter(idx)"
                      @keydown.end.prevent="focusReferenceNo"
                      readonly
                      class="w-full cursor-pointer bg-transparent text-4xl font-normal focus:outline-none placeholder:text-inherit"
                      placeholder="Select Party..."
                    />
                    <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-highlight)] font-bold group-focus-within:text-[var(--color-text-on-focus)] uppercase">Search (Enter)</div>
                  </div>

                </td>

                <td 
                  class="px-4 py-1.5 transition-colors focus-within:bg-[var(--color-focus)]"
                  :class="activeTab === 'Receipt' ? 'bg-[var(--color-success)]/5' : 'bg-[var(--color-danger)]/5'"
                >
                  <input
                    :ref="el => { if (el) expenseAmountRefs[idx] = el }"
                    v-model.number="row.amount"
                    type="number" step="0.01"
                    @keydown.enter.prevent="handleAmountEnter(idx)"
                    @keydown.end.prevent="focusReferenceNo"
                    class="w-full bg-transparent text-5xl font-light text-right focus:outline-none text-[var(--color-text)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none placeholder:text-inherit"
                    placeholder="0.00"
                  />
                </td>

                <td class="px-2 py-1.5 transition-colors focus-within:bg-[var(--color-focus)]">
                  <input
                    v-model="row.remarks"
                    :ref="el => { if (el) rowRemarksRefs[idx] = el }"
                    @keydown.enter.prevent="handleRowRemarksEnter(idx)"
                    @keydown.end.prevent="focusReferenceNo"
                    class="w-full bg-transparent text-2xl font-bold focus:outline-none text-[var(--color-text)] focus:text-[var(--color-text-on-focus)] placeholder:text-inherit placeholder:opacity-30"
                    placeholder="Row notes..."
                  />
                </td>

                <!-- Links (Reference allocations) -->
                <td class="px-4 py-1.5 transition-colors focus-within:bg-[var(--color-focus)]">
                  <div class="flex items-center gap-2">
                    <button 
                      v-if="row.account && row.party_type !== 'Account'"
                      @click="openAllocationModal(idx)"
                      class="flex h-7 w-7 items-center justify-center rounded bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-highlight)] hover:bg-[var(--color-border)] active:scale-95 transition-all shadow-sm"
                      title="Link Invoices/Payments"
                    >
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    </button>
                    
                    <div v-if="row.allocations && row.allocations.length" class="flex items-center gap-1.5 overflow-x-auto max-w-[280px] scrollbar-none">
                      <div 
                        v-for="alloc in row.allocations" 
                        :key="alloc.reference_name"
                        class="shrink-0 flex items-center gap-1.5 rounded-md bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-0.5 text-[10px] font-bold shadow-sm"
                      >
                        <span class="text-[var(--color-text-muted)]">{{ alloc.reference_name }}</span>
                        <span class="text-[var(--color-success)]">₹{{ fmt(alloc.allocated_amount) }}</span>
                        <button
                          type="button"
                          @click.stop="unlinkReference(idx, alloc)"
                          class="ml-1 text-[var(--color-text-muted)] hover:text-[var(--color-danger)] font-bold text-xs"
                          title="Unlink"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                    <div v-else-if="row.account && row.party_type !== 'Account'" class="text-[10px] text-[var(--color-text-muted)] italic ml-2">No invoices linked</div>
                  </div>
                </td>

                <td class="px-6 py-1.5 bg-[var(--color-surface-raised)]">
                  <div v-if="row.balance !== null" class="flex flex-col items-end">
                    <div class="text-4xl font-black" :class="row.balance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                      {{ Math.abs(row.balance).toLocaleString('en-IN') }} {{ row.balance > 0 ? 'Dr' : 'Cr' }}
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-xl italic text-right">—</div>
                </td>

                <td class="px-6 py-1.5 bg-[var(--color-highlight)]/5">
                  <div v-if="row.balance !== null" class="flex flex-col items-end">
                    <div class="text-4xl font-black" :class="getNewBalance(row) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                      {{ Math.abs(getNewBalance(row)).toLocaleString('en-IN') }} {{ getNewBalance(row) > 0 ? 'Dr' : 'Cr' }}
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-xl italic text-right">—</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="form.rows.length === 1 && !form.rows[0].account" class="flex-1 flex items-center justify-center opacity-10">
           <svg class="w-32 h-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
           </svg>
        </div>
      </div>
    </main>

    <!-- Bottom Action Bar -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-lg">
      <div class="flex items-center justify-between gap-8">
        
        <div class="flex items-center gap-8 flex-1">
          <div class="flex items-center gap-6 border-r border-[var(--color-border)] px-8">
            <div class="flex flex-col gap-1.5 rounded-xl transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5">
              <label class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Reference No</label>
              <input
                ref="referenceNoInput"
                v-model="form.reference_no"
                type="text"
                @keydown.enter.prevent="focusReferenceDate"
                class="w-80 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-2xl font-black focus:outline-none transition-all focus:bg-black/5 placeholder:text-inherit"
                placeholder="Ref / Chq No..."
              />
            </div>
            <div class="flex flex-col gap-1.5 rounded-xl transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Ref Date</label>
              <input
                ref="referenceDateInput"
                v-model="form.reference_date"
                type="date"
                @keydown.enter.prevent="focusPostButton"
                class="w-36 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm font-bold focus:bg-black/5 focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        <div class="flex items-center pl-8 border-l border-[var(--color-border)]">
          <button
            ref="postButtonRef"
            @click="handleSubmit"
            :disabled="submitting || !isFormValid"
            class="group relative flex items-center gap-4 overflow-hidden rounded-2xl bg-[var(--color-success)] px-16 py-6 text-4xl font-black text-white shadow-xl transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-40 focus:outline-none focus:ring-8 focus:ring-[var(--color-focus)]/50"
          >
            <span v-if="submitting" class="flex items-center gap-3">
              <svg class="h-10 w-10 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              Posting...
            </span>
            <span v-else class="flex items-center gap-4">
              Post {{ totalRows }} Entries
              <svg class="h-10 w-10 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            </span>
          </button>
        </div>

      </div>
    </footer>

    <!-- Account Search Modal -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showSearchModal"
      :title="modalTitle"
      :subtitle="modalSubtitle"
      :allowedTypes="allowedTypes"
      :initialType="initialSearchType"
      :skipDateFilter="true"
      :hideSecondary="true"
      @close="showSearchModal = false"
      @select="handleSelect"
    />

    <!-- Warning Modal -->
    <Warning
      :show="showExitWarning"
      title="Discard Changes?"
      message="You have unsaved changes. Are you sure you want to discard them and exit?"
      @close="showExitWarning = false"
      @confirm="showExitWarning = false; router.push('/')"
    />



    <!-- Success Popup -->
    <div v-if="showSuccess" class="fixed top-12 left-1/2 -translate-x-1/2 z-[200] w-full max-w-md animate-in fade-in slide-in-from-top-4 duration-300">
      <div class="rounded-3xl bg-[var(--color-surface)] p-6 shadow-2xl border-2 border-[var(--color-success)] flex items-center gap-6">
        <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-4xl">✅</div>
        <div class="flex-1 min-w-0">
          <h2 class="text-2xl font-black truncate">Posted Successfully!</h2>
          <p class="text-lg text-[var(--color-text-muted)] font-mono truncate">{{ successDocName }}</p>
        </div>
        <button @click="showSuccess = false" class="h-10 w-10 shrink-0 rounded-full hover:bg-[var(--color-midlight)] transition-colors text-xl">✕</button>
      </div>
    </div>
    <!-- Outstanding Bills Modal -->
    <OutstandingBillsModal
      v-if="modalRowIdx !== null"
      :show="showModal"
      :partyType="form.rows[modalRowIdx].party_type"
      :party="form.rows[modalRowIdx].account"
      :enteredAmount="form.rows[modalRowIdx].amount || 0"
      :activeTab="activeTab"
      :modalAmounts="form.rows[modalRowIdx].modalAmounts"
      :mop="'Cash'"
      @close="closeModal"
      @update-allocations="updateRowAllocations"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import OutstandingBillsModal from '../components/OutstandingBillsModal.vue'
import Warning from '../components/Warning.vue'

import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'

const router = useRouter()

// --- State ---
const activeTab = ref('Payment') // 'Payment', 'Receipt'
const showExitWarning = ref(false)

useSubwindowWatcher(showExitWarning, {
  'ESCAPE': () => { showExitWarning.value = false }
})
const postingDate = ref(new Date().toISOString().split('T')[0])
const cashAccount = ref({
  account: localStorage.getItem('wb-cash') || '',
  name: '',
  balance: null
})

const showModal = ref(false)
const modalRowIdx = ref(null)
const searchTarget = ref('row') // 'row' or 'cash_account'

const form = reactive({
  rows: [
    { account: '', account_name: '', amount: null, query: '', balance: null, remarks: '', party_type: '', allocations: [], modalAmounts: {} }
  ],
  reference_no: '',
  reference_date: new Date().toISOString().split('T')[0]
})

const cashAccountBtnRef = ref(null)
const expenseSearchRefs = ref([])
const expenseAmountRefs = ref([])
const rowRemarksRefs = ref([])
const referenceNoInput = ref(null)
const referenceDateInput = ref(null)
const postButtonRef = ref(null)
const currentIdx = ref(0)
const showSearchModal = ref(false)
const custSearchModalRef = ref(null)
const submitting = ref(false)
const showSuccess = ref(false)
const successDocName = ref('')

// --- Computed ---
const displayDate = computed(() => {
  if (!postingDate.value) return ''
  const d = new Date(postingDate.value)
  const day = String(d.getDate()).padStart(2, '0')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${day}-${months[d.getMonth()]}-${d.getFullYear()}`
})

const isFormValid = computed(() => {
  return form.rows.some(r => r.account && r.amount > 0) && cashAccount.value.account
})

const totalRows = computed(() => form.rows.filter(r => r.account && r.amount > 0).length)

const modalTitle = computed(() => {
  if (searchTarget.value === 'cash_account') return 'Select Cash / Bank Account'
  return 'Select Party'
})

const modalSubtitle = computed(() => {
  if (searchTarget.value === 'cash_account') return 'Choose payment source or destination account'
  if (activeTab.value === 'Payment') return 'Select Party to Pay (Debit)'
  if (activeTab.value === 'Receipt') return 'Select Party to Receive From (Credit)'
  return ''
})

const allowedTypes = computed(() => {
  if (searchTarget.value === 'cash_account') return ['Account']
  return ['Customer', 'Supplier', 'Employee', 'Account']
})

const initialSearchType = computed(() => {
  if (searchTarget.value === 'cash_account') return 'Account'
  return 'All'
})

const hasUnsavedItems = computed(() => {
  return form.rows.some(r => r.account || r.amount > 0 || r.remarks) || form.reference_no !== ''
})

function getNewBalance(row) {
  if (row.balance === null) return 0
  const amt = parseFloat(row.amount) || 0
  if (activeTab.value === 'Receipt') {
    return row.balance - amt
  }
  return row.balance + amt
}

function focusReferenceNo() {
  referenceNoInput.value?.focus()
  referenceNoInput.value?.select()
}

function focusReferenceDate() {
  referenceDateInput.value?.focus()
}

function focusPostButton() {
  postButtonRef.value?.focus()
}

// --- Methods ---
function adjustDate(days) {
  const d = new Date(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = d.toISOString().split('T')[0]
}

async function fetchCashAccountDetails() {
  if (!cashAccount.value.account) return
  try {
    const res = await frappeGet('ssplbilling.api.expense_api.get_ledger', {
      ledger_name: cashAccount.value.account,
      ledger_type: 'Account',
    })
    if (res) {
      cashAccount.value.name = res.account_name || res.label || cashAccount.value.account
    }
  } catch (e) {
    console.error('Failed to fetch cash details:', e)
  }
}

function openSearch(idx) {
  searchTarget.value = 'row'
  currentIdx.value = idx
  showSearchModal.value = true
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function openSearchAccount() {
  searchTarget.value = 'cash_account'
  showSearchModal.value = true
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function handleAccountEnter(idx) {
  const row = form.rows[idx]
  if (!row.account) {
    openSearch(idx)
  } else {
    expenseAmountRefs.value[idx]?.focus()
  }
}



async function handleSelect(item) {
  showSearchModal.value = false
  
  if (searchTarget.value === 'cash_account') {
    cashAccount.value.account = item.name
    cashAccount.value.name = item.label || item.account_name || item.name
    localStorage.setItem('wb-cash', item.name)
    await fetchCashAccountDetails()
    
    // Upon selection, focus to party selection of first row
    nextTick(() => {
      setTimeout(() => {
        expenseSearchRefs.value[0]?.focus()
      }, 50)
    })
    return
  }

  const idx = currentIdx.value
  const row = form.rows[idx]
  row.account = item.name
  row.account_name = item.label || item.account_name || item.name
  row.query = row.account_name
  row.party_type = item.type || ''
  await fetchRowBalance(idx)
  
  nextTick(() => {
    setTimeout(() => {
      expenseAmountRefs.value[idx]?.focus()
      expenseAmountRefs.value[idx]?.select()
    }, 50)
  })
}

async function fetchRowBalance(idx) {
  const row = form.rows[idx]
  if (!row.account) return
  try {
    const res = await frappeGet('ssplbilling.api.expense_api.get_ledger', {
      ledger_name: row.account,
      ledger_type: row.party_type || 'Customer',
    })
    if (res && res.closing_balance !== undefined) {
      row.balance = res.closing_balance
    }
  } catch (e) {
    console.error('Row balance fetch failed:', e)
  }
}

async function handleAmountEnter(idx) {
  const row = form.rows[idx]
  if (row.amount > 0 && row.account) {
    if (row.party_type && row.party_type !== 'Account') {
      try {
        const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
          party_type: row.party_type,
          party: row.account
        })
        const invoices = res.invoices || []
        const payments = res.payment_entries || []
        const journals = res.journal_entries || []

        if (invoices.length > 0 || payments.length > 0 || journals.length > 0) {
          openAllocationModal(idx)
          return
        }
      } catch (err) {
        console.error('Failed to check outstanding on amount enter:', err)
      }
    }

    nextTick(() => {
      setTimeout(() => {
        rowRemarksRefs.value[idx]?.focus()
      }, 50)
    })
  }
}

function handleRowRemarksEnter(idx) {
  if (idx === form.rows.length - 1) {
    form.rows.push({ account: '', account_name: '', amount: null, query: '', balance: null, remarks: '', party_type: '', allocations: [], modalAmounts: {} })
    nextTick(() => {
      setTimeout(() => {
        expenseSearchRefs.value[idx + 1]?.focus()
      }, 50)
    })
  } else {
    expenseSearchRefs.value[idx + 1]?.focus()
  }
}

function onTabClick(t) {
  if (activeTab.value === t) return
  activeTab.value = t
  form.rows = [
    { account: '', account_name: '', amount: null, query: '', balance: null, remarks: '', party_type: '', allocations: [], modalAmounts: {} }
  ]
  nextTick(() => {
    setTimeout(() => {
      expenseSearchRefs.value[0]?.focus()
    }, 50)
  })
}

function cycleTab() {
  const tabs = ['Payment', 'Receipt']
  const nextIdx = (tabs.indexOf(activeTab.value) + 1) % tabs.length
  onTabClick(tabs[nextIdx])
}

function handleBack() {
  if (!hasUnsavedItems.value) {
    router.push('/')
  } else {
    showExitWarning.value = true
  }
}

function handleEscape() {
  handleBack()
}

async function handleSubmit() {
  if (!isFormValid.value) return
  submitting.value = true
  const results = []
  try {
    const validRows = form.rows.filter(r => r.account && r.amount > 0)
    for (const row of validRows) {
      let paymentType = ''
      let party = ''
      let partyType = ''
      let account = ''

      if (row.party_type === 'Account') {
        paymentType = 'Internal Transfer'
        if (activeTab.value === 'Payment') {
          party = cashAccount.value.account
          account = row.account
        } else {
          party = row.account
          account = cashAccount.value.account
        }
        partyType = ''
      } else {
        paymentType = activeTab.value === 'Payment' ? 'Pay' : 'Receive'
        party = row.account
        partyType = row.party_type
        account = cashAccount.value.account
      }

      // Filter out Payment Entry and Journal Entry references from the initial Payment Entry payload,
      // as ERPNext's validate_reference_documents restricts references to only Sales/Purchase Invoices.
      const invoiceRefs = (row.allocations || [])
        .filter(a => ['Sales Invoice', 'Purchase Invoice'].includes(a.reference_doctype))
        .map(a => ({
          reference_doctype: a.reference_doctype,
          reference_name: a.reference_name,
          total_amount: a.total_amount,
          outstanding_amount: a.outstanding_amount,
          allocated_amount: a.allocated_amount
        }))

      const payload = {
        payment_type: paymentType,
        party: party,
        party_type: partyType,
        amount: row.amount,
        mode_of_payment: 'Cash',
        account: account,
        posting_date: postingDate.value,
        reference_no: form.reference_no,
        reference_date: form.reference_date,
        cost_center: localStorage.getItem('wb-cost-center'),
        remarks: row.remarks || '',
        "Custom Remarks": 1,
        references: invoiceRefs
      }

      const res = await frappePost('ssplbilling.api.expense_api.create_payment_entry', {
        data: JSON.stringify(payload)
      })

      if (res && res.payment_entry) {
        const pe_name = res.payment_entry
        results.push(pe_name)

        // Handle cross-reconciliation (linking the new PE to unlinked Payments/Journals)
        const crossAllocations = (row.allocations || [])
          .filter(a => ['Payment Entry', 'Journal Entry'].includes(a.reference_doctype))
          .map(a => ({
            payment_type: 'Payment Entry',
            payment_name: pe_name,
            reference_row: a._row || null,
            invoice_type: a.reference_doctype,
            invoice_name: a.reference_name,
            amount: a.allocated_amount,
            unreconciled_amount: row.amount
          }))

        if (crossAllocations.length > 0) {
          try {
            await frappePost('ssplbilling.api.reconcile_api.post_reconciliation', {
              party_type: partyType,
              party: party,
              allocations: JSON.stringify(crossAllocations)
            })
          } catch (err) {
            console.warn('Cross reconciliation failed for ' + pe_name + ':', err)
          }
        }
      }
    }
    if (results.length > 0) {
      window.location.reload()
    }
  } catch (e) {
    alert('Posting failed: ' + (e.message || e))
  } finally {
    submitting.value = false
  }
}

function openAllocationModal(idx) {
  modalRowIdx.value = idx
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  modalRowIdx.value = null
}

function updateRowAllocations(allocations) {
  if (modalRowIdx.value !== null) {
    const idx = modalRowIdx.value
    form.rows[idx].allocations = allocations
    
    // Re-sync modalAmounts to ensure state persistence
    const newModalAmounts = {}
    allocations.forEach(a => {
      newModalAmounts[a._row || a.reference_name] = a.allocated_amount
    })
    form.rows[idx].modalAmounts = newModalAmounts
    
    closeModal()
    
    // Focus remarks after modal
    nextTick(() => {
      setTimeout(() => {
        rowRemarksRefs.value[idx]?.focus()
      }, 50)
    })
  }
}

function fmt(val) {
  return Math.round(Number(val || 0)).toLocaleString('en-IN')
}

function unlinkReference(idx, alloc) {
  const row = form.rows[idx]
  if (!row) return
  row.allocations = (row.allocations || []).filter(a => a.reference_name !== alloc.reference_name)
  if (row.modalAmounts) {
    const targetKey = alloc._row || alloc.reference_name
    delete row.modalAmounts[targetKey]
  }
}

onMounted(() => {
  fetchCashAccountDetails()
  useShortcuts({
    'F7': cycleTab,
    'ESCAPE': handleEscape,
  })
  setTimeout(() => cashAccountBtnRef.value?.focus(), 300)
})
</script>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
