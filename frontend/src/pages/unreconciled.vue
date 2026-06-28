<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Unreconciled Entries</h1>
      </div>

      <!-- Ledger Selection -->
      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end">
          <span class="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Ledger Name (Customer/Supplier)</span>
          <button 
            ref="ledgerBtnRef"
            @click="openSearch"
            class="mt-1 cursor-pointer rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-2 text-xl font-black text-[var(--color-highlight)] hover:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 outline-none transition-all min-w-[300px] text-right"
          >
            {{ selectedLedgerName || 'Select Ledger...' }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden p-6">
      <!-- Empty State -->
      <div v-if="!party" class="h-full flex flex-col items-center justify-center">
        <div class="max-w-md w-full text-center space-y-6 bg-[var(--color-surface)] p-8 rounded-3xl border border-[var(--color-border)] shadow-xl">
          <div class="text-6xl">🔗</div>
          <h2 class="text-2xl font-black uppercase tracking-tight text-[var(--color-text)]">Reconcile Ledger Entries</h2>
          <p class="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Select a Customer or Supplier ledger to view and match their unlinked payments or advances against outstanding invoices.
          </p>
          <button
            @click="openSearch"
            class="w-full py-4 bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] font-bold uppercase tracking-widest rounded-2xl shadow-lg hover:brightness-105 active:scale-98 transition-all"
          >
            Select Ledger
          </button>
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
            <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Unlinked Payments</span>
            <span class="text-3xl font-mono font-black text-[var(--color-warning)] mt-1">₹{{ fmt(totalUnlinkedAmount) }}</span>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Outstanding Invoices</span>
            <span class="text-3xl font-mono font-black text-[var(--color-danger)] mt-1">₹{{ fmt(totalOutstandingAmount) }}</span>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4 flex flex-col justify-between shadow-sm">
            <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Allocations Ready</span>
            <span class="text-3xl font-mono font-black text-[var(--color-success)] mt-1">₹{{ fmt(totalAllocatedAmount) }}</span>
          </div>
        </div>

        <div class="flex-1 min-h-0 flex gap-6 overflow-hidden">
          <!-- Left Column: Unlinked Payments -->
          <div class="flex-1 flex flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
              <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">Unlinked Payments</h3>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              <div v-if="payments.length === 0" class="text-center py-12 text-xs italic text-[var(--color-text-muted)]">
                No unlinked payments found for this ledger.
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
                      class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest"
                      :class="pay.type === 'Payment Entry' ? 'bg-[var(--color-info)]/10 text-[var(--color-info)]' : 'bg-amber-500/10 text-amber-500'"
                    >
                      {{ pay.type === 'Payment Entry' ? 'PE' : 'JE' }}
                    </span>
                    <span class="text-sm font-black text-[var(--color-text)]">{{ pay.name }}</span>
                  </div>
                  <span class="text-lg font-mono font-black text-[var(--color-warning)]">₹{{ fmt(pay.unallocated_amount) }}</span>
                </div>
                <div class="flex justify-between items-center text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
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
              <h4 class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)] text-center">New Allocation</h4>
              
              <div class="space-y-3">
                <div class="rounded-xl bg-[var(--color-bg)]/50 p-3 border border-[var(--color-border)]/50">
                  <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)] block">Selected Payment</span>
                  <span class="text-sm font-black text-[var(--color-text)] truncate block mt-0.5">{{ selectedPaymentObj?.name || 'None' }}</span>
                </div>

                <div class="rounded-xl bg-[var(--color-bg)]/50 p-3 border border-[var(--color-border)]/50">
                  <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)] block">Selected Invoice</span>
                  <span class="text-sm font-black text-[var(--color-text)] truncate block mt-0.5">{{ selectedInvoiceObj?.name || 'None' }}</span>
                </div>

                <div class="space-y-1">
                  <label class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Amount to Allocate</label>
                  <input
                    type="number"
                    v-model.number="allocAmount"
                    class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 px-4 text-right font-mono text-xl font-black text-[var(--color-info)] focus:border-[var(--color-focus)] outline-none"
                    placeholder="0.00"
                    :disabled="!selectedPaymentObj || !selectedInvoiceObj"
                  />
                </div>
              </div>

              <button
                @click="addAllocation"
                :disabled="!selectedPaymentObj || !selectedInvoiceObj || !allocAmount || allocAmount <= 0"
                class="w-full py-3 bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] text-xs font-black uppercase tracking-widest rounded-xl hover:brightness-105 active:scale-98 disabled:opacity-30 transition-all shadow-md"
              >
                Queue Allocation
              </button>
            </div>

            <!-- Global Action -->
            <button
              @click="submitReconciliation"
              :disabled="queuedAllocations.length === 0 || isSubmitting"
              class="w-full py-4 bg-[var(--color-success)] text-white text-sm font-black uppercase tracking-widest rounded-2xl hover:brightness-105 active:scale-[0.98] disabled:opacity-30 transition-all shadow-lg flex items-center justify-center gap-2"
            >
              <span v-if="isSubmitting">Reconciling...</span>
              <template v-else>
                <span>Apply Reconcile</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
              </template>
            </button>
          </div>

          <!-- Right Column: Outstanding Invoices -->
          <div class="flex-1 flex flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
              <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">Outstanding Invoices</h3>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              <div v-if="invoices.length === 0" class="text-center py-12 text-xs italic text-[var(--color-text-muted)]">
                No outstanding invoices found for this ledger.
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
                      class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-500"
                    >
                      INV
                    </span>
                    <span class="text-sm font-black text-[var(--color-text)]">{{ inv.name }}</span>
                  </div>
                  <span class="text-lg font-mono font-black text-[var(--color-danger)]">₹{{ fmt(inv.outstanding_amount) }}</span>
                </div>
                <div class="flex justify-between items-center text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
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
            <h4 class="text-xs font-black uppercase tracking-widest text-[var(--color-text)]">Proposed Allocations ({{ queuedAllocations.length }})</h4>
            <button @click="clearQueue" class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-danger)] hover:underline">Clear All</button>
          </div>
          <div class="overflow-y-auto space-y-2 flex-1 custom-scrollbar">
            <div
              v-for="(alloc, idx) in queuedAllocations"
              :key="idx"
              class="flex items-center justify-between bg-[var(--color-bg)]/50 px-4 py-2 rounded-xl border border-[var(--color-border)]/50 text-xs"
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
import { ref, computed, nextTick } from 'vue'
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
    
    payments.value = [...pes, ...jes]
    invoices.value = outstandingRes.docs || []
  } catch (e) {
    alert('Failed to fetch entries: ' + e.message)
  } finally {
    isLoading.value = false
  }
}

function selectPayment(pay) {
  selectedPaymentKey.value = pay.key
  updateDefaultAllocAmount()
}

function selectInvoice(inv) {
  selectedInvoiceName.value = inv.name
  updateDefaultAllocAmount()
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
    alert('Invalid allocation amount.')
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
  const pay = payments.value.find(p => p.name === alloc.payment_name && p.reference_row === alloc.reference_row)
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
