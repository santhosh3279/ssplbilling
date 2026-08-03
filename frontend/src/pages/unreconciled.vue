<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="relative flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button
          v-if="!party"
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Unreconciled Entries</h1>
        <button
          v-if="party"
          @click="backToList"
          class="ml-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)] hover:border-[var(--color-highlight)] hover:text-[var(--color-highlight)] transition-all active:scale-95"
        >
          ← All Ledgers
        </button>
      </div>

      <!-- Ledger Selection (Centered) -->
      <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center opacity-100">
        <span class="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--color-text)] opacity-100">Ledger Name (Customer/Supplier)</span>
        <button 
          ref="ledgerBtnRef"
          @click="openSearch"
          class="mt-1 cursor-pointer rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-2 text-xl font-black text-[var(--color-text)] hover:text-[var(--color-highlight)] hover:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 outline-none transition-all min-w-[300px] text-center opacity-100"
        >
          {{ selectedLedgerName || 'Select Ledger...' }}
        </button>
      </div>

      <!-- Right Header Actions -->
      <div class="flex items-center gap-4">
        <!-- Apply Reconcile Button -->
        <button
          v-if="party"
          @click="submitReconciliation"
          :disabled="queuedAllocations.length === 0 || isSubmitting"
          class="h-11 cursor-pointer rounded-xl bg-[var(--color-success)] px-6 text-xs font-black uppercase tracking-widest text-white hover:brightness-105 active:scale-95 disabled:opacity-30 transition-all shadow-md flex items-center justify-center gap-2"
        >
          <span v-if="isSubmitting">Reconciling...</span>
          <template v-else>
            <span>Apply Reconcile</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </template>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden p-6">
      <!-- Landing: ledgers having unlinked payments -->
      <div v-if="!party" class="h-full flex flex-col gap-4 overflow-hidden">
        <div class="flex items-center justify-between shrink-0 gap-4">
          <div class="flex items-center gap-3">
            <h2 class="text-lg font-black uppercase tracking-tight text-[var(--color-text)]">
              Ledgers Ready for Reconciliation
            </h2>
            <span class="px-2.5 py-0.5 rounded-full bg-[var(--color-warning)]/10 text-[var(--color-warning)] text-[10px] font-black uppercase tracking-wider">{{ filteredParties.length }}</span>
          </div>
          <div class="flex items-center gap-3">
            <input
              v-model="partyFilter"
              type="text"
              placeholder="Filter ledgers…"
              class="w-72 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            />
            <button
              @click="loadParties"
              :disabled="partiesLoading"
              class="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:border-[var(--color-highlight)] focus:outline-none transition-colors active:scale-95 disabled:opacity-50 cursor-pointer"
              title="Refresh Ledgers"
            >
              <svg
                class="h-5 w-5"
                :class="{ 'animate-spin': partiesLoading }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89H18v3"
                />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="partiesLoading" class="flex-1 flex flex-col items-center justify-center gap-4">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
          <p class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Finding ledgers...</p>
        </div>

        <div v-else-if="!filteredParties.length" class="flex-1 flex items-center justify-center">
          <div class="max-w-md w-full text-center space-y-4 bg-[var(--color-surface)] p-8 rounded-3xl border border-[var(--color-border)] shadow-xl">
            <div class="text-6xl">✅</div>
            <h2 class="text-xl font-black uppercase tracking-tight text-[var(--color-text)]">
              No Actionable Ledgers
            </h2>
            <p class="text-xs text-[var(--color-text-muted)] leading-relaxed">
              Every payment is allocated. Select a ledger manually.
            </p>
            <button
              @click="openSearch"
              class="w-full py-3 bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] font-bold uppercase tracking-widest rounded-2xl shadow-lg hover:brightness-105 active:scale-98 transition-all"
            >
              Select Ledger
            </button>
          </div>
        </div>

        <div v-else class="flex-1 overflow-y-auto custom-scrollbar pr-1">
          <div class="grid grid-cols-3 gap-4 content-start">
            <div
              v-for="p in filteredParties"
              :key="p.party_type + '::' + p.party"
              @click="selectLedgerFromList(p)"
              class="p-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] cursor-pointer transition-all hover:border-[var(--color-highlight)] hover:shadow-md active:scale-[0.99] flex flex-col gap-2"
            >
              <div class="flex items-center justify-between gap-2">
                <span
                  class="px-2 py-0.5 rounded text-[13.5px] font-black uppercase tracking-widest shrink-0"
                  :class="p.party_type === 'Customer' ? 'bg-[var(--color-info)]/10 text-[var(--color-info)]' : 'bg-[var(--color-supplier)]/10 text-[var(--color-supplier)]'"
                >{{ p.party_type }}</span>
                <span class="text-[15px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider shrink-0">
                  <template v-if="p.party_type === 'Customer'">
                    <template v-if="p.unlinked_count > 0 && p.outstanding_count > 0">
                      {{ p.unlinked_count }} Cr · {{ p.outstanding_count }} Dr
                    </template>
                    <template v-else-if="p.unlinked_count > 0">
                      {{ p.unlinked_count }} Cr
                    </template>
                    <template v-else>
                      {{ p.outstanding_count }} Dr
                    </template>
                  </template>
                  <template v-else>
                    <template v-if="p.unlinked_count > 0 && p.outstanding_count > 0">
                      {{ p.unlinked_count }} Dr · {{ p.outstanding_count }} Cr
                    </template>
                    <template v-else-if="p.unlinked_count > 0">
                      {{ p.unlinked_count }} Dr
                    </template>
                    <template v-else>
                      {{ p.outstanding_count }} Cr
                    </template>
                  </template>
                </span>
              </div>
              <span class="text-[21px] font-black text-[var(--color-text)] truncate" :title="p.label">{{ p.label }}</span>
              <span
                class="text-[30px] font-mono font-black"
                :class="p.unlinked_amount > 0 ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]'"
              >
                ₹{{ fmt(p.amount) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else-if="isLoading" class="h-full flex flex-col items-center justify-center gap-4">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
        <p class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Fetching entries...</p>
      </div>

      <!-- Main Layout Grid -->
      <div v-else class="h-full flex flex-col gap-6 overflow-hidden">
        <!-- Dashboard Summary Bar -->
        <div class="grid grid-cols-3 gap-6 shrink-0">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
              {{ partyType === 'Customer' ? 'Unlinked Credits' : 'Unlinked Debits' }}
            </span>
            <div class="flex items-baseline justify-between mt-1">
              <span class="text-[45px] font-mono font-black text-[var(--color-warning)]">₹{{ fmt(totalUnlinkedAmount) }}</span>
              <span class="text-[18px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Count: {{ payments.length }}</span>
            </div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
              {{ partyType === 'Customer' ? 'Unlinked Debits' : 'Unlinked Credits' }}
            </span>
            <div class="flex items-baseline justify-between mt-1">
              <span class="text-[45px] font-mono font-black text-[var(--color-danger)]">₹{{ fmt(totalOutstandingAmount) }}</span>
              <span class="text-[18px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Count: {{ invoices.length }}</span>
            </div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <span class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Allocations Ready</span>
            <span class="text-[45px] font-mono font-black text-[var(--color-success)] mt-1">₹{{ fmt(totalAllocatedAmount) }}</span>
          </div>
        </div>

        <div class="flex-1 min-h-0 flex gap-6 overflow-hidden">
          <!-- Left Column: Unlinked Payments -->
          <div class="flex-1 flex flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 flex justify-between items-center">
              <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">
                {{ partyType === 'Customer' ? 'Unlinked Credits' : 'Unlinked Debits' }}
              </h3>
              <span class="px-2.5 py-0.5 rounded-full bg-[var(--color-warning)]/10 text-[var(--color-warning)] text-[10px] font-black uppercase tracking-wider">{{ payments.length }}</span>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              <div v-if="payments.length === 0" class="text-center py-12 text-xs italic text-[var(--color-text-muted)]">
                No unlinked {{ partyType === 'Customer' ? 'credits' : 'debits' }} found for this ledger.
              </div>
              <div
                v-for="pay in payments"
                :key="pay.key"
                @click="selectPayment(pay)"
                class="p-4 rounded-2xl border cursor-pointer transition-all flex flex-col gap-2"
                :class="selectedPaymentKey === pay.key
                  ? 'border-[var(--color-focus)] bg-[var(--color-focus)]/5 font-bold shadow-md'
                  : 'border-[var(--color-border)] bg-[var(--color-bg)]/30 hover:border-[var(--color-focus)]/30'"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span
                      class="px-2 py-0.5 rounded text-[13.5px] font-black uppercase tracking-widest"
                      :class="pay.type === 'Payment Entry' ? 'bg-[var(--color-info)]/10 text-[var(--color-info)]'
                        : pay.type === 'Journal Entry' ? 'bg-amber-500/10 text-amber-500'
                        : 'bg-purple-500/10 text-purple-500'"
                    >
                      {{ pay.type === 'Payment Entry' ? 'PE' : pay.type === 'Journal Entry' ? 'JE' : (pay.type === 'Sales Invoice' ? 'CN' : 'DN') }}
                    </span>
                    <span class="text-[21px] font-black text-[var(--color-text)]">{{ pay.name }}</span>
                  </div>
                  <span class="text-[27px] font-mono font-black text-[var(--color-warning)]">₹{{ fmt(pay.unallocated_amount) }}</span>
                </div>
                <div class="flex justify-between items-center text-[15px] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
                  <span>{{ formatDate(pay.posting_date) }} <span v-if="pay.mode_of_payment">· {{ pay.mode_of_payment }}</span></span>
                  <span v-if="pay.remarks" class="normal-case italic truncate max-w-[200px]">{{ pay.remarks }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Middle Connection Form & Actions -->
          <div class="w-80 shrink-0 flex flex-col gap-6 justify-center">
            <!-- Linking Form -->
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-3xl p-6 shadow-md space-y-4">
              <h4 class="text-[18px] font-black uppercase tracking-widest text-[var(--color-text-muted)] text-center">New Allocation</h4>
              
              <div class="space-y-3">
                <div class="rounded-xl bg-[var(--color-bg)]/50 p-3 border border-[var(--color-border)]/50">
                  <span class="text-[13.5px] font-black uppercase tracking-widest text-[var(--color-text-muted)] block">
                    Selected {{ partyType === 'Customer' ? 'Credit' : 'Debit' }}
                  </span>
                  <span class="text-[21px] font-black text-[var(--color-text)] truncate block mt-0.5">{{ selectedPaymentObj?.name || 'None' }}</span>
                </div>

                <div class="rounded-xl bg-[var(--color-bg)]/50 p-3 border border-[var(--color-border)]/50">
                  <span class="text-[13.5px] font-black uppercase tracking-widest text-[var(--color-text-muted)] block">
                    Selected {{ partyType === 'Customer' ? 'Debit' : 'Credit' }}
                  </span>
                  <span class="text-[21px] font-black text-[var(--color-text)] truncate block mt-0.5">{{ selectedInvoiceObj?.name || 'None' }}</span>
                </div>

                <div class="space-y-1">
                  <label class="text-[13.5px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Amount to Allocate</label>
                  <input
                    type="number"
                    v-model.number="allocAmount"
                    class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 px-4 text-right font-mono text-[30px] font-black text-[var(--color-info)] focus:border-[var(--color-focus)] outline-none"
                    placeholder="0.00"
                    :disabled="!selectedPaymentObj || !selectedInvoiceObj"
                  />
                </div>
              </div>

              <button
                @click="addAllocation"
                :disabled="!selectedPaymentObj || !selectedInvoiceObj || !allocAmount || allocAmount <= 0"
                class="w-full py-3 bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] text-[18px] font-black uppercase tracking-widest rounded-xl hover:brightness-105 active:scale-98 disabled:opacity-30 transition-all shadow-md"
              >
                Queue Allocation
              </button>
            </div>

          </div>

          <!-- Right Column: Outstanding Invoices -->
          <div class="flex-1 flex flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 flex justify-between items-center">
              <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">
                {{ partyType === 'Customer' ? 'Unlinked Debits' : 'Unlinked Credits' }}
              </h3>
              <span class="px-2.5 py-0.5 rounded-full bg-[var(--color-danger)]/10 text-[var(--color-danger)] text-[10px] font-black uppercase tracking-wider">{{ invoices.length }}</span>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              <div v-if="invoices.length === 0" class="text-center py-12 text-xs italic text-[var(--color-text-muted)]">
                No unlinked {{ partyType === 'Customer' ? 'debits' : 'credits' }} found for this ledger.
              </div>
              <div
                v-for="inv in invoices"
                :key="inv.name"
                @click="selectInvoice(inv)"
                class="p-4 rounded-2xl border cursor-pointer transition-all flex flex-col gap-2"
                :class="selectedInvoiceName === inv.name
                  ? 'border-[var(--color-focus)] bg-[var(--color-focus)]/5 font-bold shadow-md'
                  : 'border-[var(--color-border)] bg-[var(--color-bg)]/30 hover:border-[var(--color-focus)]/30'"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span
                      class="px-2 py-0.5 rounded text-[13.5px] font-black uppercase tracking-widest"
                      :class="inv.doctype === 'Journal Entry' ? 'bg-amber-500/10 text-amber-500'
                        : inv.doctype === 'Payment Entry' ? 'bg-[var(--color-info)]/10 text-[var(--color-info)]'
                        : 'bg-emerald-500/10 text-emerald-500'"
                    >
                      {{ inv.doctype === 'Journal Entry' ? 'JE' : inv.doctype === 'Payment Entry' ? 'PE' : 'INV' }}
                    </span>
                    <span class="text-[21px] font-black text-[var(--color-text)]">{{ inv.name }}</span>
                  </div>
                  <span class="text-[27px] font-mono font-black text-[var(--color-danger)]">₹{{ fmt(inv.outstanding_amount) }}</span>
                </div>
                <div class="flex justify-between items-center text-[15px] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
                  <span>{{ formatDate(inv.posting_date) }}</span>
                  <span>Total: ₹{{ fmt(inv.grand_total) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Proposed Allocations Queue -->
        <div v-if="queuedAllocations.length > 0" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-3xl p-4 shrink-0 flex flex-col gap-3 shadow-md max-h-48 overflow-hidden">
          <div class="flex items-center justify-between px-2 border-b border-[var(--color-border)] pb-2">
            <h4 class="text-[18px] font-black uppercase tracking-widest text-[var(--color-text)]">Proposed Allocations ({{ queuedAllocations.length }})</h4>
            <button @click="clearQueue" class="text-[15px] font-bold uppercase tracking-widest text-[var(--color-danger)] hover:underline">Clear All</button>
          </div>
          <div class="overflow-y-auto space-y-2 flex-1 custom-scrollbar">
            <div
              v-for="(alloc, idx) in queuedAllocations"
              :key="idx"
              class="flex items-center justify-between bg-[var(--color-bg)]/50 px-4 py-2 rounded-xl border border-[var(--color-border)]/50 text-[18px]"
            >
              <div class="flex items-center gap-3">
                <span class="font-black text-[var(--color-warning)]">{{ alloc.payment_name }}</span>
                <span class="text-[var(--color-text-muted)]">&rarr;</span>
                <span class="font-black text-[var(--color-danger)]">{{ alloc.invoice_name }}</span>
              </div>
              <div class="flex items-center gap-4">
                <span class="font-mono font-black text-[var(--color-success)]">₹{{ fmt(alloc.amount) }}</span>
                <button @click="removeAllocation(idx)" class="text-[var(--color-danger)] hover:scale-115 active:scale-90 transition-all">&times;</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Customer Search Modal -->
    <CustomerSearchModal
      ref="searchModalRef"
      :show="showSearchModal"
      :allowedTypes="['Customer', 'Supplier']"
      initialType="All"
      @close="showSearchModal = false"
      @select="handleSearchSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()

const showSearchModal = ref(false)
const searchModalRef = ref(null)

const partyType = ref('')
const party = ref('')
const selectedLedgerName = ref('')

const isLoading = ref(false)
const isSubmitting = ref(false)

const payments = ref([])
const invoices = ref([])
const queuedAllocations = ref([])

const selectedPaymentKey = ref('')
const selectedInvoiceName = ref('')
const allocAmount = ref(0)

const ledgerBtnRef = ref(null)

// ── Landing list: ledgers having unlinked payments ──
const unlinkedParties = ref([])
const partiesLoading = ref(false)
const partyFilter = ref('')

const filteredParties = computed(() => {
  const q = partyFilter.value.trim().toLowerCase()
  const base = unlinkedParties.value.filter(
    p => p.unlinked_count > 0 && p.outstanding_count > 0
  )
  if (!q) return base
  return base.filter(p =>
    (p.label || '').toLowerCase().includes(q) || (p.party || '').toLowerCase().includes(q)
  )
})

async function loadParties() {
  partiesLoading.value = true
  try {
    unlinkedParties.value = await frappeGet('ssplbilling.api.reconcile_api.get_parties_with_unlinked_entries')
  } catch (e) {
    console.error('[Unreconciled] Failed to load parties:', e)
    unlinkedParties.value = []
  } finally {
    partiesLoading.value = false
  }
}

async function selectLedgerFromList(p) {
  partyType.value = p.party_type
  party.value = p.party
  selectedLedgerName.value = p.label || p.party
  selectedPaymentKey.value = ''
  selectedInvoiceName.value = ''
  allocAmount.value = 0
  queuedAllocations.value = []
  await fetchData()
}

function backToList() {
  party.value = ''
  partyType.value = ''
  selectedLedgerName.value = ''
  selectedPaymentKey.value = ''
  selectedInvoiceName.value = ''
  allocAmount.value = 0
  queuedAllocations.value = []
  loadParties()
}

onMounted(loadParties)

const selectedPaymentObj = computed(() => {
  return payments.value.find(p => p.key === selectedPaymentKey.value)
})

const selectedInvoiceObj = computed(() => {
  return invoices.value.find(i => i.name === selectedInvoiceName.value)
})

const totalUnlinkedAmount = computed(() => {
  return payments.value.reduce((acc, p) => acc + (Number(p.unallocated_amount) || 0), 0)
})

const totalOutstandingAmount = computed(() => {
  return invoices.value.reduce((acc, i) => acc + (Number(i.outstanding_amount) || 0), 0)
})

const totalAllocatedAmount = computed(() => {
  return queuedAllocations.value.reduce((acc, a) => acc + (Number(a.amount) || 0), 0)
})

function openSearch() {
  showSearchModal.value = true
  nextTick(() => searchModalRef.value?.focus())
}

async function handleSearchSelect(item) {
  showSearchModal.value = false
  partyType.value = item.type || 'Customer'
  party.value = item.name
  selectedLedgerName.value = item.label || item.name
  
  // Clear any existing selections or queue
  selectedPaymentKey.value = ''
  selectedInvoiceName.value = ''
  allocAmount.value = 0
  queuedAllocations.value = []
  
  await fetchData()
}

async function fetchData() {
  if (!party.value) return
  isLoading.value = true
  try {
    const [unlinkedRes, outstandingRes] = await Promise.all([
      frappeGet('ssplbilling.api.reconcile_api.get_unlinked_entries', {
        party_type: partyType.value,
        party: party.value
      }),
      frappeGet('ssplbilling.api.reconcile_api.get_outstanding_docs', {
        party_type: partyType.value,
        party: party.value
      })
    ])
    
    // Normalize payments (merge PE and JE rows)
    const pes = (unlinkedRes.payment_entries || []).map(p => ({
      ...p,
      type: 'Payment Entry',
      key: `pe_${p.name}`
    }))
    
    const jes = (unlinkedRes.journal_entries || []).map(j => ({
      ...j,
      type: 'Journal Entry',
      key: `je_${j.name}_${j.reference_row || ''}`
    }))

    // Return invoices (credit/debit notes) carry a negative outstanding — they are
    // credits waiting to be linked, so show them on the payments side as positive
    // amounts instead of negative rows on the invoice side.
    const docs = outstandingRes.docs || []
    const returns = docs
      .filter(d => Number(d.outstanding_amount) < 0)
      .map(d => ({
        ...d,
        type: d.doctype, // 'Sales Invoice' | 'Purchase Invoice'
        key: `ret_${d.name}`,
        unallocated_amount: Math.abs(Number(d.outstanding_amount)),
        mode_of_payment: '',
        remarks: d.doctype === 'Sales Invoice' ? 'Credit Note (Return)' : 'Debit Note (Return)',
      }))

    // Only rows that move in the payment direction (Cr for Customer, Dr for
    // Supplier) are payments. Opposite-direction PE/JE rows are bill-like —
    // reconciling them as payments unbalances the JE — so they belong on the
    // outstanding side, linkable against real payments.
    const payDir = partyType.value === 'Customer' ? 'Cr' : 'Dr'
    const paySide = []
    const oppSide = []
    for (const row of [...pes, ...jes]) {
      if ((row.direction || payDir) === payDir) {
        paySide.push(row)
      } else {
        oppSide.push({
          name: row.name,
          doctype: row.type, // 'Payment Entry' | 'Journal Entry'
          posting_date: row.posting_date,
          grand_total: Number(row.total_amount || row.unallocated_amount),
          outstanding_amount: Number(row.unallocated_amount),
          reference_row: row.reference_row || null,
        })
      }
    }

    payments.value = [...paySide, ...returns]
    invoices.value = [...docs.filter(d => Number(d.outstanding_amount) > 0), ...oppSide]
  } catch (e) {
    alert('Failed to fetch entries: ' + e.message)
  } finally {
    isLoading.value = false
  }
}

function selectPayment(pay) {
  selectedPaymentKey.value = pay.key
  updateDefaultAllocAmount()
  autoQueueIfPaired()
}

function selectInvoice(inv) {
  selectedInvoiceName.value = inv.name
  updateDefaultAllocAmount()
  autoQueueIfPaired()
}

// Clicking one entry on each side allocates immediately (min of the two amounts)
function autoQueueIfPaired() {
  if (selectedPaymentObj.value && selectedInvoiceObj.value && allocAmount.value > 0) {
    addAllocation()
  }
}

function updateDefaultAllocAmount() {
  if (selectedPaymentObj.value && selectedInvoiceObj.value) {
    allocAmount.value = Math.min(
      selectedPaymentObj.value.unallocated_amount,
      selectedInvoiceObj.value.outstanding_amount
    )
  } else {
    allocAmount.value = 0
  }
}

function addAllocation() {
  if (!selectedPaymentObj.value || !selectedInvoiceObj.value || !allocAmount.value) return
  
  const amt = Number(allocAmount.value)
  if (amt <= 0 || amt > selectedPaymentObj.value.unallocated_amount) {
    alert('Allocation amount cannot exceed the payment\'s unallocated amount.')
    return
  }
  if (amt > selectedInvoiceObj.value.outstanding_amount + 0.01) {
    alert('Allocation amount cannot exceed the outstanding amount of the document.')
    return
  }
  
  // Add to proposed queue
  queuedAllocations.value.push({
    payment_type: selectedPaymentObj.value.type,
    payment_name: selectedPaymentObj.value.name,
    reference_row: selectedPaymentObj.value.reference_row || null,
    invoice_type: selectedInvoiceObj.value.doctype,
    invoice_name: selectedInvoiceObj.value.name,
    amount: amt,
    unreconciled_amount: selectedPaymentObj.value.unallocated_amount
  })
  
  // Deduct locally to allow multiple allocations in same session
  selectedPaymentObj.value.unallocated_amount -= amt
  selectedInvoiceObj.value.outstanding_amount -= amt
  
  // Clean up selection
  selectedPaymentKey.value = ''
  selectedInvoiceName.value = ''
  allocAmount.value = 0
}

function removeAllocation(idx) {
  const alloc = queuedAllocations.value[idx]
  
  // Revert local values
  const pay = payments.value.find(
    p => p.name === alloc.payment_name && (p.reference_row || null) === (alloc.reference_row || null)
  )
  if (pay) pay.unallocated_amount += alloc.amount
  
  const inv = invoices.value.find(i => i.name === alloc.invoice_name)
  if (inv) inv.outstanding_amount += alloc.amount
  
  queuedAllocations.value.splice(idx, 1)
}

function clearQueue() {
  // Revert all
  while(queuedAllocations.value.length > 0) {
    removeAllocation(0)
  }
}

async function submitReconciliation() {
  if (queuedAllocations.value.length === 0) return
  
  isSubmitting.value = true
  try {
    const res = await frappePost('ssplbilling.api.reconcile_api.post_reconciliation', {
      party_type: partyType.value,
      party: party.value,
      allocations: JSON.stringify(queuedAllocations.value)
    })
    
    if (res.status === 'ok') {
      alert('Reconciliation successfully applied!')
      queuedAllocations.value = []
      await fetchData()
      loadParties() // keep the landing list totals current
      if (payments.value.length === 0) {
        backToList()
      }
    }
  } catch (e) {
    alert('Reconciliation failed: ' + e.message)
  } finally {
    isSubmitting.value = false
  }
}

function fmt(val) {
  return Math.round(Number(val || 0)).toLocaleString('en-IN')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}
</script>
