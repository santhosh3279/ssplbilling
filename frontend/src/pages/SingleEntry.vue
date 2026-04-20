<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Single Payment Entry (Bulk)</h1>
      </div>

      <!-- Account Selection (MOP Account) -->
      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end">
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Target Account (Paid To/From)</span>
          <div 
            @click="openSearch('mop')"
            class="mt-1 cursor-pointer rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-2 text-xl font-black text-[var(--color-highlight)] hover:border-[var(--color-highlight)] transition-all min-w-[300px] text-right"
          >
            {{ mopAccountLabel || 'Select Account...' }}
          </div>
        </div>

        <div class="h-10 w-px bg-[var(--color-border)] mx-2"></div>

        <!-- Date -->
        <div class="flex flex-col items-end">
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Posting Date</span>
          <input 
            type="date" 
            v-model="postingDate"
            class="mt-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xl font-bold focus:border-[var(--color-highlight)] outline-none"
          />
        </div>
      </div>
    </header>

    <!-- Main Grid -->
    <main class="flex-1 overflow-hidden p-4">
      <div class="flex h-full flex-col gap-4 rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="flex-1 overflow-auto custom-scrollbar">
          <table class="w-full text-left border-collapse table-fixed">
            <thead class="sticky top-0 z-20 bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
              <tr class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-4 py-3 w-16 text-center">#</th>
                <th class="px-4 py-3 w-80">Party Name</th>
                <th class="px-4 py-3 w-40 text-right text-[var(--color-danger)]">Debit (Dr)</th>
                <th class="px-4 py-3 w-40 text-right text-[var(--color-success)]">Credit (Cr)</th>
                <th class="px-4 py-3 w-48 text-right">Outstanding</th>
                <th class="px-4 py-3 w-48 text-right">New Balance</th>
                <th class="px-4 py-3 min-w-[400px]">Linked Invoices / References</th>
                <th class="px-4 py-3 w-16"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
              <tr 
                v-for="(row, idx) in rows" 
                :key="row.id"
                class="group transition-colors hover:bg-[var(--color-midlight)]/5"
              >
                <!-- Row Number -->
                <td class="px-4 py-2 text-center text-[var(--color-text-muted)] font-mono">{{ idx + 1 }}</td>
                
                <!-- Party Selection -->
                <td class="px-2 py-1.5">
                  <div 
                    @click="openSearch('party', idx)"
                    class="cursor-pointer rounded-lg border border-transparent px-2 py-1 text-xl font-bold truncate hover:border-[var(--color-highlight)]/30 transition-all"
                    :class="row.party ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)] italic'"
                  >
                    {{ row.party_name || 'Select Party...' }}
                  </div>
                </td>

                <!-- Amount: Debit (Dr) -->
                <td class="px-2 py-1.5">
                  <input
                    v-model.number="row.dr"
                    type="number"
                    step="0.01"
                    @input="row.cr = null"
                    @keydown.enter="handleAmountEnter(idx)"
                    class="w-full bg-transparent text-2xl font-black text-right focus:outline-none focus:bg-[var(--color-danger)]/5 rounded-lg px-2 py-1 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    placeholder="0.00"
                  />
                </td>

                <!-- Amount: Credit (Cr) -->
                <td class="px-2 py-1.5">
                  <input
                    v-model.number="row.cr"
                    type="number"
                    step="0.01"
                    @input="row.dr = null"
                    @keydown.enter="handleAmountEnter(idx)"
                    class="w-full bg-transparent text-2xl font-black text-right focus:outline-none focus:bg-[var(--color-success)]/5 rounded-lg px-2 py-1 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    placeholder="0.00"
                  />
                </td>

                <!-- Outstanding -->
                <td class="px-4 py-2 text-right">
                  <div v-if="row.outstanding !== null" class="text-xl font-bold" :class="row.outstanding > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    {{ Math.abs(row.outstanding).toLocaleString('en-IN') }} {{ row.outstanding > 0 ? 'Dr' : 'Cr' }}
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] italic">—</div>
                </td>

                <!-- New Balance -->
                <td class="px-4 py-2 text-right">
                  <div v-if="row.outstanding !== null" class="text-xl font-black" :class="calculateNewBalance(row) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    {{ Math.abs(calculateNewBalance(row)).toLocaleString('en-IN') }} {{ calculateNewBalance(row) > 0 ? 'Dr' : 'Cr' }}
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] italic">—</div>
                </td>

                <!-- Linked Invoices (Horizontal Scroll) -->
                <td class="px-2 py-1.5 overflow-hidden">
                  <div class="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 px-1">
                    <button 
                      v-if="row.party && row.amount > 0"
                      @click="triggerModal(idx)"
                      class="shrink-0 flex items-center justify-center h-8 w-8 rounded-lg bg-[var(--color-highlight)]/10 text-[var(--color-highlight)] hover:bg-[var(--color-highlight)] hover:text-white transition-all"
                    >
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    </button>
                    
                    <div v-if="row.allocations.length" class="flex items-center gap-1.5">
                      <div 
                        v-for="alloc in row.allocations" 
                        :key="alloc.reference_name"
                        class="shrink-0 flex items-center gap-2 rounded-md bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-1 text-[10px] font-bold shadow-sm"
                      >
                        <span class="text-[var(--color-text-muted)]">{{ alloc.reference_name }}</span>
                        <span class="text-[var(--color-success)]">₹{{ alloc.allocated_amount.toLocaleString('en-IN') }}</span>
                      </div>
                    </div>
                    <div v-else class="text-[10px] text-[var(--color-text-muted)] italic ml-2">No invoices linked</div>
                  </div>
                </td>

                <!-- Remove Row -->
                <td class="px-4 py-2 text-center">
                  <button 
                    @click="removeRow(idx)"
                    class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors opacity-0 group-hover:opacity-100"
                  >
                    ✕
                  </button>
                </td>
              </tr>
              
              <!-- Add Row Button Row -->
              <tr>
                <td colspan="7" class="px-4 py-4">
                  <button 
                    @click="addRow"
                    class="flex items-center gap-2 rounded-xl bg-[var(--color-surface-raised)] px-4 py-2 text-sm font-bold text-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/10 transition-all border border-dashed border-[var(--color-highlight)]/50"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                    Add Another Entry (Insert)
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Footer Action -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shadow-2xl">
      <div class="flex items-center gap-10">
        <div class="flex flex-col">
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Entries</span>
          <span class="text-3xl font-black">{{ rows.filter(r => r.party && r.amount > 0).length }}</span>
        </div>
        <div class="h-8 w-px bg-[var(--color-border)]"></div>
        <div class="flex flex-col">
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Amount</span>
          <span class="text-3xl font-black text-[var(--color-highlight)]">₹{{ totalBulkAmount.toLocaleString('en-IN') }}</span>
        </div>
      </div>

      <button
        @click="saveAllEntries"
        :disabled="submitting || !canSave"
        class="group flex items-center gap-4 rounded-2xl bg-[var(--color-success)] px-16 py-4 text-3xl font-black text-white shadow-xl transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-40 disabled:grayscale"
      >
        <span v-if="submitting">Processing...</span>
        <span v-else class="flex items-center gap-3">
          Save All Entries (Ctrl+S)
          <svg class="h-8 w-8 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
        </span>
      </button>
    </footer>

    <!-- Modals -->
    <CustomerSearchModal
      ref="searchModalRef"
      :show="showSearchModal"
      :allowedTypes="searchTarget === 'party' ? ['Customer', 'Supplier'] : ['Account']"
      :initialType="searchTarget === 'party' ? 'All' : 'Account'"
      :skipDateFilter="true"
      @close="showSearchModal = false"
      @select="handleSearchSelect"
    />

    <OutstandingBillsModal
      v-if="modalRowIdx !== null"
      :show="showModal"
      :loading="loadingInvoices"
      :enteredAmount="rows[modalRowIdx].amount"
      :invoices="rowInvoices"
      :unlinkedPayments="rowUnlinkedPayments"
      :unlinkedJournals="rowUnlinkedJournals"
      :activeTab="rowActiveTab"
      :allocationRefs="rows[modalRowIdx].allocations"
      :modalAmounts="rows[modalRowIdx].modalAmounts"
      @close="closeModal"
      @update-allocations="updateRowAllocations"
    />

    <!-- Multi-Success Toast -->
    <transition name="slide-up">
      <div v-if="saveStats" class="fixed bottom-24 right-8 z-[200] rounded-2xl bg-slate-900 p-6 text-white shadow-2xl border border-slate-700">
         <div class="flex items-center gap-4">
            <div class="h-12 w-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-2xl">✅</div>
            <div>
               <div class="text-xl font-bold">Successfully Saved!</div>
               <div class="text-sm opacity-70">{{ saveStats.count }} entries created successfully.</div>
            </div>
         </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import OutstandingBillsModal from '../components/OutstandingBillsModal.vue'

const router = useRouter()

// --- Core State ---
const mopAccount = ref('')
const mopAccountLabel = ref('')
const postingDate = ref(new Date().toISOString().split('T')[0])
const rows = ref([createEmptyRow()])
const submitting = ref(false)
const saveStats = ref(null)

// --- Modal State ---
const showSearchModal = ref(false)
const searchModalRef = ref(null)
const searchTarget = ref('party') // 'party' or 'mop'
const currentIdx = ref(null)

const showModal = ref(false)
const modalRowIdx = ref(null)
const loadingInvoices = ref(false)
const rowInvoices = ref([])
const rowUnlinkedPayments = ref([])
const rowUnlinkedJournals = ref([])
const rowActiveTab = ref('Receipt') // Inferred based on amount direction/party type

// --- Helpers ---
function createEmptyRow() {
  return {
    id: Math.random().toString(36).substr(2, 9),
    party: '',
    party_name: '',
    party_type: 'Customer',
    dr: null,
    cr: null,
    outstanding: null,
    allocations: [],
    modalAmounts: {}
  }
}

function addRow() {
  rows.value.push(createEmptyRow())
}

function removeRow(idx) {
  if (rows.value.length > 1) {
    rows.value.splice(idx, 1)
  } else {
    rows.value[0] = createEmptyRow()
  }
}

const totalBulkAmount = computed(() => 
  rows.value.reduce((sum, r) => sum + rowAmount(r), 0)
)

const canSave = computed(() => 
  mopAccount.value && rows.value.some(r => r.party && rowAmount(r) > 0)
)

function rowAmount(r) {
  return (parseFloat(r.dr) || 0) + (parseFloat(r.cr) || 0)
}

function calculateNewBalance(row) {
  if (row.outstanding === null) return 0
  const dr = parseFloat(row.dr) || 0
  const cr = parseFloat(row.cr) || 0
  // Debit increases balance (if Dr), Credit decreases balance (if Dr)
  return row.outstanding + dr - cr
}

// --- Search Methods ---
function openSearch(target, idx = null) {
  searchTarget.value = target
  currentIdx.value = idx
  showSearchModal.value = true
}

async function handleSearchSelect(item) {
  showSearchModal.value = false
  
  if (searchTarget.value === 'mop') {
    mopAccount.value = item.name
    mopAccountLabel.value = item.label || item.account_name || item.name
  } else if (searchTarget.value === 'party') {
    const idx = currentIdx.value
    rows.value[idx].party = item.name
    rows.value[idx].party_name = item.label || item.customer_name || item.supplier_name || item.name
    rows.value[idx].party_type = item.type || 'Customer'
    
    // Fetch outstanding balance for this party
    try {
      const res = await frappeGet('ssplbilling.api.payment_api.get_ledger', {
        ledger_name: item.name,
        ledger_type: rows.value[idx].party_type,
      })
      rows.value[idx].outstanding = res.closing_balance || 0
    } catch (e) {
      console.warn('Outstanding fetch failed:', e)
    }
  }
}

// --- Invoice Linking Methods ---
async function handleAmountEnter(idx) {
  if (rows.value[idx].party && rowAmount(rows.value[idx]) > 0) {
    triggerModal(idx)
  }
}

async function triggerModal(idx) {
  modalRowIdx.value = idx
  loadingInvoices.value = true
  showModal.value = true
  
  const row = rows.value[idx]
  // If we are DEBITING the party, it's a PAY (payment to supplier / debit note to customer)
  // If we are CREDITING the party, it's a RECEIVE (receipt from customer / credit note to supplier)
  rowActiveTab.value = row.cr > 0 ? 'Receipt' : 'Payment'
  
  try {
    const [outstandingRes, unlinkedRes] = await Promise.all([
      frappeGet('ssplbilling.api.reconcile_api.get_outstanding_docs', {
        party_type: row.party_type,
        party: row.party
      }),
      frappeGet('ssplbilling.api.reconcile_api.get_unlinked_entries', {
        party_type: row.party_type,
        party: row.party
      })
    ])
    
    rowInvoices.value = outstandingRes.docs || []
    rowUnlinkedPayments.value = unlinkedRes.payment_entries || []
    rowUnlinkedJournals.value = unlinkedRes.journal_entries || []

    // Pre-fill allocations if not already done
    if (Object.keys(row.modalAmounts).length === 0) {
      const targetDir = row.cr > 0 ? 'Dr' : 'Cr' // If Receipt (Cr party), look for Dr invoices
      let remaining = rowAmount(row)
      
      rowInvoices.value.filter(i => i.direction === targetDir).forEach(inv => {
        const out = Math.abs(inv.outstanding_amount)
        const alloc = Math.min(remaining, out)
        row.modalAmounts[inv.name] = alloc
        remaining -= alloc
      })
    }

  } catch (e) {
    console.error('Invoice fetch failed:', e)
  } finally {
    loadingInvoices.value = false
  }
}

function updateRowAllocations(allocations) {
  if (modalRowIdx.value !== null) {
    rows.value[modalRowIdx.value].allocations = allocations
    // Re-sync modalAmounts to ensure state persistence
    const newModalAmounts = {}
    allocations.forEach(a => {
      newModalAmounts[a._row || a.reference_name] = a.allocated_amount
    })
    rows.value[modalRowIdx.value].modalAmounts = newModalAmounts
  }
}

function closeModal() {
  showModal.value = false
  modalRowIdx.value = null
}

// --- Save Methods ---
async function saveAllEntries() {
  if (!canSave.value || submitting.value) return
  
  const validRows = rows.value.filter(r => r.party && rowAmount(r) > 0)
  if (!validRows.length) return
  
  submitting.value = true
  let successCount = 0
  
  try {
    for (const row of validRows) {
      const payload = {
        payment_type: row.cr > 0 ? 'Receive' : 'Pay',
        party_type: row.party_type,
        party: row.party,
        amount: rowAmount(row),
        mode_of_payment: 'Cash', // Default
        account: mopAccount.value,
        posting_date: postingDate.value,
        remarks: `Bulk Entry - ${row.party_name}`,
        references: row.allocations.map(a => ({
          reference_doctype: a.reference_doctype,
          reference_name: a.reference_name,
          total_amount: a.total_amount,
          outstanding_amount: a.outstanding_amount,
          allocated_amount: a.allocated_amount
        }))
      }
      
      await frappePost('ssplbilling.api.payment_api.create_payment_entry', {
        data: JSON.stringify(payload)
      })
      successCount++
    }
    
    saveStats.value = { count: successCount }
    setTimeout(() => {
      saveStats.value = null
      router.push('/payment') // Redirect back to payment list or reset
    }, 3000)
    
  } catch (e) {
    alert('Failed to save entries: ' + (e.message || e))
  } finally {
    submitting.value = false
  }
}

// --- Lifecycle ---
onMounted(() => {
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault()
      saveAllEntries()
    }
    if (e.key === 'Insert') {
      e.preventDefault()
      addRow()
    }
  })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(100%) scale(0.9);
  opacity: 0;
}
</style>
