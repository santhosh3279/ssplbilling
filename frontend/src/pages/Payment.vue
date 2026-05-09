<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header 
      class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-2.5 shadow-sm transition-colors duration-300"
      :class="activeTab === 'Payment' ? 'bg-red-500/30' : activeTab === 'Receipt' ? 'bg-green-500/30' : 'bg-blue-500/30'"
    >
      <!-- Left: back + title -->
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Payment & Receipt Entry</h1>
      </div>

      <!-- Center: Payment / Receipt / Transfer tabs -->
      <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5">
        <button
          v-for="t in ['Payment', 'Receipt', 'Expenses']"
          :key="t"
          @click="activeTab = t"
          class="min-w-[110px] rounded-md px-4 py-1 text-2xl font-black uppercase tracking-wide transition-all duration-200"
          :class="activeTab === t
            ? 'bg-[var(--color-highlight)] text-white shadow-sm'
            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)]'"
        >
          {{ t }}
        </button>
      </div>

      <!-- Right: Posting Date with arrow nav -->
      <div class="flex items-center gap-2">
        <span class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</span>
        <div class="flex items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]">
          <button
            @click="adjustDate(-1)"
            class="rounded-l-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div class="relative min-w-[110px] px-3 py-1.5 text-center">
            <span class="text-2xl">{{ displayDate }}</span>
            <input type="date" v-model="postingDate" class="absolute inset-0 opacity-0 cursor-pointer" />
          </div>
          <button
            @click="adjustDate(1)"
            class="rounded-r-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Initial Selection Overlay -->
    <div
      v-if="showInitialSelection"
      ref="selectionOverlayRef"
      tabindex="0"
      class="fixed inset-0 z-[120] flex items-center justify-center bg-black/60 backdrop-blur-md outline-none"
      @keydown="onSelectionKeydown"
    >
      <div class="w-full max-w-2xl rounded-3xl bg-[var(--color-surface)] p-12 text-center shadow-2xl border border-[var(--color-border)] relative">
        <!-- Close/Back -->
        <button
          @click="router.push('/')"
          class="absolute top-6 left-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-midlight)]/20 hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>

        <h2 class="mb-10 text-5xl font-black uppercase tracking-tight">Select Entry Type</h2>
        <div class="grid grid-cols-3 gap-8">
          <button
            @click="selectEntryType('Payment')"
            class="flex flex-col items-center gap-6 rounded-2xl p-12 border-2 transition-all"
            :class="selectionIdx === 0
              ? 'bg-red-500/25 border-red-500 scale-105 shadow-xl'
              : 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20 hover:border-red-500'"
          >
            <span class="text-8xl">💸</span>
            <span class="text-4xl font-black text-red-500 uppercase">Payment</span>
          </button>
          <button
            @click="selectEntryType('Receipt')"
            class="flex flex-col items-center gap-6 rounded-2xl p-12 border-2 transition-all"
            :class="selectionIdx === 1
              ? 'bg-green-500/25 border-green-500 scale-105 shadow-xl'
              : 'bg-green-500/10 border-green-500/30 hover:bg-green-500/20 hover:border-green-500'"
          >
            <span class="text-8xl">💰</span>
            <span class="text-4xl font-black text-green-500 uppercase">Receipt</span>
          </button>
          <button
            @click="selectEntryType('Expenses')"
            class="flex flex-col items-center gap-6 rounded-2xl p-12 border-2 transition-all"
            :class="selectionIdx === 2
              ? 'bg-blue-500/25 border-blue-500 scale-105 shadow-xl'
              : 'bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20 hover:border-blue-500'"
          >
            <span class="text-8xl">🔄</span>
            <span class="text-4xl font-black text-blue-500 uppercase">Expenses</span>
          </button>
        </div>
        <p class="mt-8 text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
          ← → or Tab to navigate &nbsp;·&nbsp; Enter to select &nbsp;·&nbsp; Esc to go back
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden p-4">
      <div class="flex h-full flex-col gap-4">
        
        <!-- Form Row (Table Style) -->
        <div class="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
          <table class="w-full text-left border-collapse">
            <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
              <tr class="text-3xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-4 py-2">
                  {{ activeTab === 'Expenses' ? 'Paid From (Bank/Cash)' : 'Party Name' }}
                </th>
                <th class="px-4 py-2">
                  {{ activeTab === 'Expenses' ? 'Paid To (Bank/Cash)' : (activeTab === 'Payment' ? 'Account Paid From (Bank/Cash)' : 'Account Paid To (Bank/Cash)') }}
                </th>
                <th class="px-6 py-2 text-right w-64">Amount</th>
                <th class="px-6 py-2 text-right w-80">Outstanding</th>
                <th class="px-6 py-2 text-right w-80">New Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr class="divide-x divide-[var(--color-border)]">
                <!-- Party Name / Paid From -->
                <td class="px-2 py-1.5 group hover:bg-[var(--color-midlight)]/20 transition-colors">
                  <div class="relative">
                    <input
                      v-model="partyQuery"
                      @click="openSearch(activeTab === 'Expenses' ? 'paid_from' : 'party')"
                      @keydown.enter="openSearch(activeTab === 'Expenses' ? 'paid_from' : 'party')"
                      readonly
                      class="w-full cursor-pointer bg-transparent text-4xl font-normal focus:outline-none"
                      :placeholder="activeTab === 'Expenses' ? 'Select From Account...' : 'Search Party...'"
                    />
                    <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-highlight)] font-bold">CLICK TO SEARCH</div>
                  </div>
                </td>

                <!-- Bank/Cash Account -->
                <td class="px-2 py-1.5 group hover:bg-[var(--color-midlight)]/20 transition-colors">
                  <div class="relative">
                    <input
                      v-model="mopAccountQuery"
                      @click="openSearch('mop')"
                      @keydown.enter="openSearch('mop')"
                      readonly
                      class="w-full cursor-pointer bg-transparent text-4xl font-normal focus:outline-none"
                      placeholder="Select Account..."
                    />
                    <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-highlight)] font-bold">CLICK TO SEARCH</div>
                  </div>
                </td>

                <!-- Amount -->
                <td class="px-6 py-1.5 bg-[var(--color-highlight)]/5">
                  <input
                    ref="amountInputRef"
                    v-model.number="form.amount"
                    type="number"
                    step="0.01"
                    @keydown.enter="handleAmountEnter"
                    class="w-full bg-transparent text-7xl font-light text-right focus:outline-none text-[var(--color-text)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    placeholder="0.00"
                  />
                </td>

                <!-- Outstanding -->
                <td class="px-6 py-1.5 bg-[var(--color-surface-raised)]">
                  <div v-if="outstandingBalance !== null" class="flex flex-col items-end">
                    <div class="flex items-center gap-3">
                      <div class="text-5xl font-black" :class="outstandingBalance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                        {{ Math.abs(outstandingBalance).toLocaleString('en-IN') }} {{ outstandingBalance > 0 ? 'Dr' : 'Cr' }}
                      </div>
                      <button 
                        v-if="form.party"
                        @click="fetchInvoices"
                        class="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-highlight)]/10 text-xl font-bold text-[var(--color-highlight)] transition-all hover:bg-[var(--color-highlight)] hover:text-white"
                        title="View Outstanding & Unlinked Items"
                      >
                        📄
                      </button>
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-xl italic font-medium text-right">
                    —
                  </div>
                </td>

                <!-- New Balance -->
                <td class="px-6 py-1.5 bg-[var(--color-highlight)]/5">
                  <div v-if="outstandingBalance !== null" class="flex flex-col items-end">
                    <div class="text-5xl font-black" :class="newBalance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                      {{ Math.abs(newBalance).toLocaleString('en-IN') }} {{ newBalance > 0 ? 'Dr' : 'Cr' }}
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-xl italic font-medium text-right">
                    —
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Payment References / Allocation Table -->
        <div v-if="allocationRefs.length" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Payment References</h3>
          </div>
          <div class="rounded-xl border border-[var(--color-border)] overflow-hidden">
            <table class="w-full text-left">
              <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
                <tr class="text-3xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                  <th class="px-4 py-3">Voucher No</th>
                  <th class="px-4 py-3">Inv Type</th>
                  <th class="px-4 py-3 text-right">Outstanding</th>
                  <th class="px-4 py-3 text-right">Allocated</th>
                  <th class="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr v-for="(ref, idx) in allocationRefs" :key="ref.reference_name" class="hover:bg-[var(--color-midlight)]/30 transition-colors">
                  <td class="px-4 py-3 font-mono text-3xl font-black">{{ ref.reference_name }}</td>
                  <td class="px-4 py-3 text-3xl text-[var(--color-text-muted)]">{{ ref.reference_doctype }}</td>
                  <td class="px-4 py-3 text-right text-3xl text-[var(--color-text-muted)]">{{ ref.outstanding_amount.toLocaleString('en-IN') }}</td>
                  <td class="px-4 py-3 text-right">
                    <input
                      v-model.number="ref.allocated_amount"
                      type="number" step="0.01" min="0"
                      class="w-48 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-3xl font-black text-right focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                    />
                  </td>
                  <td class="px-4 py-3 text-right">
                    <button
                      @click="removeAllocation(idx)"
                      class="h-6 w-6 rounded-md bg-[var(--color-danger)]/10 hover:bg-[var(--color-danger)]/25 text-[var(--color-danger)] text-xs flex items-center justify-center ml-auto transition-all"
                    >✕</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Empty state placeholder -->
        <div class="flex-1 flex items-center justify-center opacity-10">
           <svg class="w-32 h-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
           </svg>
        </div>
      </div>
    </main>

    <!-- Bottom Action Bar -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-[0_-4px_20px_rgba(0,0,0,0.1)]">
      <div class="flex items-center justify-between gap-8">
        
        <div class="flex items-center gap-8 flex-1">
          <!-- Left: Remarks Input -->
          <div class="flex-1 max-w-xl flex flex-col gap-1.5">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Internal Remarks</label>
            <textarea
              ref="remarksInput"
              v-model="form.remarks"
              rows="2"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all resize-none"
              placeholder="Add internal notes..."
              @keydown.enter.prevent="refNoInput?.focus()"
            ></textarea>
          </div>

          <!-- Middle: Reference Info -->
          <div class="flex items-center gap-6 border-l border-r border-[var(--color-border)] px-8">
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">
                Ref No (Cheque/UPI)
              </label>
              <input
                ref="refNoInput"
                v-model="form.reference_no"
                type="text"
                class="w-80 rounded-xl border px-4 py-3 text-2xl font-black focus:outline-none transition-all"
                :class="form.reference_no.length > 0 
                  ? (refValid ? 'border-[var(--color-success)] bg-[var(--color-success)]/10 focus:border-[var(--color-success)]' : 'border-[var(--color-danger)]/60 bg-[var(--color-surface-raised)] focus:border-[var(--color-danger)]')
                  : 'border-[var(--color-border)] bg-[var(--color-surface-raised)] focus:border-[var(--color-highlight)]'"
                placeholder="Ref / Chq No..."
                @keydown.enter="saveBtn?.focus()"
              />            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Ref Date</label>
              <input
                v-model="form.reference_date"
                type="date"
                class="w-36 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
              />
            </div>
          </div>

          <!-- Right: Summary -->
          <div v-if="allocationRefs.length" class="flex flex-col text-right">
            <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Allocated Amount</div>
            <div class="text-2xl font-black text-[var(--color-success)]">
              {{ totalAllocated.toLocaleString('en-IN') }}
            </div>
          </div>
        </div>

        <!-- Right End: Save Button -->
        <div class="flex items-center pl-8 border-l border-[var(--color-border)]">
          <button
            ref="saveBtn"
            @click="handleSubmit"
            :disabled="submitting || !isFormValid"
            class="group relative flex items-center gap-4 overflow-hidden rounded-2xl bg-[var(--color-success)] px-16 py-6 text-4xl font-black text-white shadow-xl transition-all hover:scale-[1.02] hover:shadow-2xl active:scale-95 disabled:opacity-40 disabled:hover:scale-100 disabled:grayscale"
          >
            <span v-if="submitting" class="flex items-center gap-3">
              <svg class="h-10 w-10 animate-spin" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving...
            </span>
            <span v-else class="flex items-center gap-4">
              Save {{ activeTab }}
              <svg class="h-10 w-10 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </span>
          </button>
        </div>

      </div>
    </footer>

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showSearchModal"
      :allowedTypes="allowedTypes"
      :initialType="initialSearchType"
      :skipDateFilter="true"
      :hideSecondary="true"
      @close="showSearchModal = false"
      @select="handleSelect"
    />

    <!-- Success Popup -->
    <div 
      v-if="showSuccess" 
      class="fixed top-12 left-1/2 -translate-x-1/2 z-[200] w-full max-w-md animate-in fade-in slide-in-from-top-4 duration-300"
    >
      <div class="rounded-3xl bg-[var(--color-surface)] p-6 shadow-2xl border-2 border-[var(--color-success)] flex items-center gap-6">
        <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-4xl">
          ✅
        </div>
        <div class="flex-1 min-w-0">
          <h2 class="text-2xl font-black truncate">Entry Created!</h2>
          <p class="text-lg text-[var(--color-text-muted)] font-mono truncate">{{ successDocName }}</p>
        </div>
        <button
          @click="showSuccess = false"
          class="h-10 w-10 shrink-0 rounded-full hover:bg-[var(--color-midlight)] transition-colors flex items-center justify-center text-xl"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Outstanding Invoices Modal -->
    <OutstandingBillsModal
      :show="showInvoicesModal"
      :partyType="form.party_type"
      :party="form.party"
      :enteredAmount="form.amount"
      :activeTab="activeTab"
      :modalAmounts="modalAmounts"
      :disablePayments="true"
      @close="showInvoicesModal = false"
      @update-allocations="updateAllocations"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import OutstandingBillsModal from '../components/OutstandingBillsModal.vue'
import { useShortcuts } from '../services/shortcutManager'
import { paymentShortcuts } from '../shortcuts/paymentShortcuts'

const router = useRouter()

// --- State ---
const activeTab = ref('Payment')
const showInitialSelection = ref(true)
const amountInputRef = ref(null)
const remarksInput = ref(null)
const refNoInput = ref(null)
const saveBtn = ref(null)
const selectionOverlayRef = ref(null)
const selectionIdx = ref(0) // 0 = Payment, 1 = Receipt, 2 = Expenses
const ENTRY_TYPES = ['Payment', 'Receipt', 'Expenses']

function cycleTab() {
  if (activeTab.value === 'Payment') activeTab.value = 'Receipt'
  else if (activeTab.value === 'Receipt') activeTab.value = 'Expenses'
  else activeTab.value = 'Payment'
}

function onSelectionKeydown(e) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'Tab') {
    e.preventDefault()
    selectionIdx.value = (selectionIdx.value + 1) % 3
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    selectionIdx.value = (selectionIdx.value + 2) % 3
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    selectEntryType(ENTRY_TYPES[selectionIdx.value])
  } else if (e.key === 'Escape') {
    e.preventDefault()
    router.push('/')
  }
}

function selectEntryType(type) {
  activeTab.value = type
  showInitialSelection.value = false
  setTimeout(() => {
    openSearch('party')
  }, 100)
}

watch(showInitialSelection, (val) => {
  if (val) {
    selectionIdx.value = 0
    nextTick(() => selectionOverlayRef.value?.focus())
  }
})

useShortcuts(paymentShortcuts({
  cycleTab,
}))
const postingDate = ref(new Date().toISOString().split('T')[0])
const displayDate = computed(() => {
  if (!postingDate.value) return ''
  const d = new Date(postingDate.value)
  const day = String(d.getDate()).padStart(2, '0')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const month = months[d.getMonth()]
  const year = d.getFullYear()
  return `${day}-${month}-${year}`
})

function adjustDate(days) {
  const d = new Date(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = d.toISOString().split('T')[0]
}

const form = reactive({
  party_type: 'Customer',
  party: '',
  party_name: '',
  account: 'Debtors - SSPL',
  mop_account: '',
  amount: null,
  reference_no: '',
  reference_date: new Date().toISOString().split('T')[0],
  remarks: ''
})

const showCustomerSearchModal = ref(false)
const custSearchModalRef = ref(null)

const partyQuery = ref('')

const accountQuery = ref('Debtors')
const mopAccountQuery = ref('Search Account')

const submitting = ref(false)
const showSuccess = ref(false)
const successDocName = ref('')
const outstandingBalance = ref(null)
const invoices = ref([])
const unlinkedPayments = ref([])
const unlinkedJournals = ref([])
const showInvoicesModal = ref(false)
const loadingInvoices = ref(false)
const allocationRefs = ref([])
const modalAmounts = reactive({})

// --- Computed ---
const refValid = computed(() => form.reference_no.replace(/\s/g, '').length > 0)

const isFormValid = computed(() => {
  return form.party && form.amount > 0 && form.mop_account
})

const newBalance = computed(() => {
  if (outstandingBalance.value === null) return 0
  const amt = parseFloat(form.amount) || 0
  // If Payment (we pay), it's a Debit to the party (increases balance if Dr)
  // If Receipt (we receive), it's a Credit to the party (decreases balance if Dr)
  // If Expenses, the 'From' account (party) is credited (decreases balance if Dr)
  if (activeTab.value === 'Payment') return outstandingBalance.value + amt
  return outstandingBalance.value - amt
})

const invoiceDocType = computed(() =>
  form.party_type === 'Customer' ? 'Sales Invoice' : 'Purchase Invoice'
)

const totalAllocated = computed(() =>
  allocationRefs.value.reduce((sum, r) => sum + (parseFloat(r.allocated_amount) || 0), 0)
)

const todayDate = computed(() => {
  return new Date().toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
})

const currentTime = ref('')
function updateTime() {
  currentTime.value = new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// --- Methods ---
const searchTarget = ref('party')
const showSearchModal = ref(false)

const allowedTypes = computed(() => {
  if (activeTab.value === 'Expenses') return ['Account']
  if (searchTarget.value === 'party') return ['Customer', 'Supplier', 'Employee', 'Account']
  return ['Account']
})

const initialSearchType = computed(() => {
  if (searchTarget.value === 'party') return 'All'
  return 'Account'
})

function openSearch(target) {
  searchTarget.value = target
  showSearchModal.value = true
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function handleSelect(item) {
  showSearchModal.value = false
  if (searchTarget.value === 'party') {
    form.party = item.name
    form.party_name = item.label || item.customer_name || item.supplier_name || item.employee_name || item.name
    partyQuery.value = form.party_name
    
    // Clear previous allocations
    allocationRefs.value = []
    clearModalAmounts()
    
    // Automatically select party type based on selection
    if (item.type) {
      form.party_type = item.type
    }
    
    // Automatically set default Account based on type
    if (form.party_type === 'Customer') {
      form.account = 'Debtors - SSPL'
      accountQuery.value = 'Debtors'
    } else {
      form.account = 'Creditors - SSPL'
      accountQuery.value = 'Creditors'
    }
    
    fetchOutstanding()
    
    // Automatically chain to MOP account selection
    setTimeout(() => {
      openSearch('mop')
    }, 150)
  } else if (searchTarget.value === 'paid_from') {
    form.party = item.name
    form.party_name = item.label || item.account_name || item.name
    partyQuery.value = form.party_name
    form.party_type = '' // Not a standard party
    
    // Chain to MOP (Paid To)
    setTimeout(() => {
      openSearch('mop')
    }, 150)
  } else if (searchTarget.value === 'account' || searchTarget.value === 'mop') {
    form.mop_account = item.name
    mopAccountQuery.value = item.label || item.account_name || item.name
    
    // Chain to Amount focus
    nextTick(() => {
      setTimeout(() => {
        amountInputRef.value?.focus()
        amountInputRef.value?.select()
      }, 50)
    })
  }
}

function updateAllocations(allocations) {
  allocationRefs.value = allocations
  nextTick(() => {
    remarksInput.value?.focus()
  })
}

function removeAllocation(idx) {
  allocationRefs.value.splice(idx, 1)
}

function handleAmountEnter() {
  if (form.amount > 0 && form.party) {
    fetchInvoices(true) // Pass true to auto-show only if items present
  }
}

async function fetchInvoices(autoShowOnlyIfItems = false) {
  if (!form.party) return
  
  loadingInvoices.value = true
  try {
    const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
      party_type: form.party_type,
      party: form.party,
    })
    
    const targetDir = activeTab.value === 'Receipt' ? 'Dr' : 'Cr'
    const hasInvoices = (res.invoices || []).some(i => i.direction === targetDir)
    const hasPayments = (res.payment_entries || []).some(p => p.direction === targetDir)
    const hasJournals = (res.journal_entries || []).some(j => j.direction === targetDir)
    
    if (hasInvoices || hasPayments || hasJournals) {
      showInvoicesModal.value = true
    } else {
      if (!autoShowOnlyIfItems) {
        console.log('No outstanding items found for direction:', targetDir)
      }
      // Move focus to remarks if no modal is shown
      nextTick(() => {
        remarksInput.value?.focus()
      })
    }
  } catch (e) {
    console.error('Failed to fetch outstanding items:', e)
    // Fallback focus
    nextTick(() => {
      remarksInput.value?.focus()
    })
  } finally {
    loadingInvoices.value = false
  }
}

async function fetchOutstanding() {
  if (!form.party) return
  try {
    const res = await frappeGet('ssplbilling.api.payment_api.get_ledger', {
      ledger_name: form.party,
      ledger_type: activeTab.value === 'Expenses' ? 'Account' : form.party_type,
    })
    if (res && res.closing_balance !== undefined) {
      outstandingBalance.value = res.closing_balance
    }
  } catch (e) {
    console.error('Failed to fetch outstanding:', e)
  }
}

function clearModalAmounts() {
  Object.keys(modalAmounts).forEach(k => delete modalAmounts[k])
}

function handlePartyTypeChange() {
  form.party = ''
  form.party_name = ''
  partyQuery.value = ''
  outstandingBalance.value = null
  invoices.value = []
  unlinkedPayments.value = []
  unlinkedJournals.value = []
  allocationRefs.value = []
  clearModalAmounts()
  
  if (form.party_type === 'Customer') {
    form.account = 'Debtors - SSPL'
    accountQuery.value = 'Debtors'
  } else {
    form.account = 'Creditors - SSPL'
    accountQuery.value = 'Creditors'
  }
}

function resetForm() {
  postingDate.value = new Date().toISOString().split('T')[0]
  form.party = ''
  form.party_name = ''
  partyQuery.value = ''
  form.amount = null
  form.remarks = ''
  outstandingBalance.value = null
  invoices.value = []
  unlinkedPayments.value = []
  unlinkedJournals.value = []
  allocationRefs.value = []
  clearModalAmounts()

  if (form.party_type === 'Customer') {
    form.account = 'Debtors - SSPL'
    accountQuery.value = 'Debtors'
  } else {
    form.account = 'Creditors - SSPL'
    accountQuery.value = 'Creditors'
  }
  
  form.mop_account = ''
  mopAccountQuery.value = 'Search Account'
  form.reference_no = ''
  form.reference_date = new Date().toISOString().split('T')[0]
}

async function handleSubmit() {
  if (!isFormValid.value) return
  submitting.value = true
  
  try {
    let paymentType = 'Pay'
    if (activeTab.value === 'Receipt') paymentType = 'Receive'
    else if (activeTab.value === 'Expenses') paymentType = 'Internal Transfer'

    const payload = {
      payment_type: paymentType,
      party_type: form.party_type,
      party: form.party,
      amount: form.amount,
      mode_of_payment: 'Cash',
      account: form.mop_account,
      posting_date: postingDate.value,
      reference_no: form.reference_no,
      reference_date: form.reference_date,
      cost_center: localStorage.getItem('wb-cost-center') || null,
      remarks: form.remarks,
      "Custom Remarks": 1,
      references: allocationRefs.value.map(r => ({
        reference_doctype: r.reference_doctype,
        reference_name: r.reference_name,
        total_amount: r.total_amount,
        outstanding_amount: r.outstanding_amount,
        allocated_amount: parseFloat(r.allocated_amount) || 0,
      })),
    }
    
    const res = await frappePost('ssplbilling.api.payment_api.create_payment_entry', {
      data: JSON.stringify(payload)
    })
    
    if (res && res.payment_entry) {
      successDocName.value = res.payment_entry
      showSuccess.value = true
      
      // Auto-hide success message and reload after a short delay
      setTimeout(() => {
        showSuccess.value = false
        window.location.reload()
      }, 1500)
    }
  } catch (e) {
    console.error('Submission failed:', e)
    alert('Failed to create payment entry: ' + (e.message || e))
  } finally {
    submitting.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
  nextTick(() => selectionOverlayRef.value?.focus())
})

watch(activeTab, () => {
  resetForm()
})
</script>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
