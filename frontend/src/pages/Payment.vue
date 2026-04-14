<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm">
      <div class="flex items-center gap-4">
        <button 
          @click="router.push('/')"
          class="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-bold tracking-tight">Payment & Receipt Entry</h1>
      </div>
      <div class="flex items-center gap-3">
        <div class="text-right">
          <div class="text-sm font-medium text-[var(--color-text-muted)] uppercase tracking-wider">{{ todayDate }}</div>
          <div class="text-xs font-bold text-[var(--color-highlight)]">{{ currentTime }}</div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-hidden p-4">
      <div class="flex h-full flex-col gap-4">
        
        <!-- Tab Switcher & Posting Date -->
        <div class="flex items-center justify-between">
          <div class="flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1 shadow-sm">
            <button
              v-for="t in ['Payment', 'Receipt']"
              :key="t"
              @click="activeTab = t"
              class="min-w-[120px] rounded-lg px-4 py-1.5 text-sm font-bold transition-all duration-200"
              :class="activeTab === t 
                ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-md' 
                : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)]'"
            >
              {{ t }}
            </button>
          </div>

          <!-- Posting Date -->
          <div class="flex items-center gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl px-4 py-1.5 shadow-sm">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</label>
            <input 
              type="date" 
              v-model="postingDate"
              class="bg-transparent border-none text-sm font-bold text-[var(--color-text)] focus:ring-0 p-0 cursor-pointer"
            />
          </div>
        </div>

        <!-- Form Row -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl">
          <div class="flex items-end gap-4 w-full">
            
            <!-- Party Type -->
            <div class="w-40 shrink-0 space-y-1.5">
              <label class="block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Party Type</label>
              <select
                v-model="form.party_type"
                disabled
                class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-base font-bold focus:outline-none transition-all cursor-not-allowed opacity-70"
              >
                <option value="Customer">Customer</option>
                <option value="Supplier">Supplier</option>
                <option value="Employee">Employee</option>
              </select>
            </div>

            <!-- Party Name (Searchable) -->
            <div class="flex-1 min-w-[200px] space-y-1.5">
              <label class="block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Party Name</label>
              <div class="relative group">
                <input
                  v-model="partyQuery"
                  @click="openSearch('party')"
                  @keydown.enter="openSearch('party')"
                  readonly
                  class="w-full cursor-pointer rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-base font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                  :placeholder="'Search Party...'"
                />
              </div>
            </div>

            <!-- Party Account -->
            <div class="flex-1 min-w-[200px] space-y-1.5">
              <label class="block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">
                {{ activeTab === 'Payment' ? 'Account Paid To (Party)' : 'Account Received From (Party)' }}
              </label>
              <div class="relative group">
                <input
                  v-model="accountQuery"
                  readonly
                  class="w-full cursor-not-allowed rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-base font-bold focus:outline-none transition-all opacity-70"
                  placeholder="Party Account..."
                />
              </div>
            </div>

            <!-- Bank/Cash Account -->
            <div class="flex-1 min-w-[200px] space-y-1.5">
              <label class="block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">
                {{ activeTab === 'Payment' ? 'Account Paid From (Bank/Cash)' : 'Account Paid To (Bank/Cash)' }}
              </label>
              <div class="relative group">
                <input
                  v-model="mopAccountQuery"
                  @click="openSearch('mop')"
                  @keydown.enter="openSearch('mop')"
                  readonly
                  class="w-full cursor-pointer rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-base font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                  placeholder="Select Bank/Cash Account..."
                />
              </div>
            </div>

            <!-- Paid Amount -->
            <div class="w-48 shrink-0 space-y-1.5">
              <label class="block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1">Amount (₹)</label>
              <input
                v-model.number="form.amount"
                type="number"
                step="0.01"
                class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-2xl font-black text-black focus:border-[var(--color-highlight)] focus:outline-none transition-all text-right opacity-100"
                placeholder="0.00"
              />
            </div>

            <!-- Outstanding Mini-Info -->
            <div v-if="outstandingBalance !== null" class="w-48 shrink-0 pb-1 px-2 border-l border-[var(--color-border)] flex flex-col justify-end">
              <div class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] mb-1">Outstanding</div>
              <div class="flex items-center justify-between">
                <div class="text-sm font-black truncate" :class="outstandingBalance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                  ₹{{ Math.abs(outstandingBalance).toLocaleString('en-IN') }} {{ outstandingBalance > 0 ? 'Dr' : 'Cr' }}
                </div>
                <button 
                  v-if="form.party"
                  @click="fetchInvoices"
                  class="ml-2 h-6 w-6 rounded-md bg-[var(--color-midlight)] hover:bg-[var(--color-highlight)] hover:text-white transition-all flex items-center justify-center text-[10px]"
                  title="View Invoices"
                >
                  📄
                </button>
              </div>
            </div>

            <!-- Submit Button (Inline) -->
            <div class="shrink-0 pb-0.5">
              <button
                @click="handleSubmit"
                :disabled="submitting || !isFormValid"
                class="rounded-xl bg-[var(--color-success)] px-8 py-2.5 text-lg font-black text-white shadow-lg transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
              >
                <span v-if="submitting">...</span>
                <span v-else>Save</span>
              </button>
            </div>

          </div>
        </div>

        <!-- Payment References / Allocation Table -->
        <div v-if="allocationRefs.length" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xl">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Payment References</h3>
            <div class="flex items-center gap-3">
              <span class="text-[10px] font-black uppercase text-[var(--color-text-muted)]">Total Allocated</span>
              <span class="text-base font-black" :class="totalAllocated > (form.amount || 0) ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                ₹{{ totalAllocated.toLocaleString('en-IN') }}
              </span>
            </div>
          </div>
          <div class="rounded-xl border border-[var(--color-border)] overflow-hidden">
            <table class="w-full text-left">
              <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
                <tr class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                  <th class="px-4 py-3">Type</th>
                  <th class="px-4 py-3">Voucher No</th>
                  <th class="px-4 py-3 text-right">Outstanding</th>
                  <th class="px-4 py-3 text-right">Allocated (₹)</th>
                  <th class="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr v-for="(ref, idx) in allocationRefs" :key="ref.reference_name" class="hover:bg-[var(--color-midlight)]/30 transition-colors">
                  <td class="px-4 py-3 text-xs text-[var(--color-text-muted)]">{{ ref.reference_doctype }}</td>
                  <td class="px-4 py-3 font-mono text-sm font-black">{{ ref.reference_name }}</td>
                  <td class="px-4 py-3 text-right text-sm text-[var(--color-text-muted)]">₹{{ ref.outstanding_amount.toLocaleString('en-IN') }}</td>
                  <td class="px-4 py-3 text-right">
                    <input
                      v-model.number="ref.allocated_amount"
                      type="number" step="0.01" min="0"
                      class="w-32 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm font-black text-right focus:border-[var(--color-highlight)] focus:outline-none transition-all"
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

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showSearchModal"
      :allowedTypes="allowedTypes"
      :initialType="initialSearchType"
      :skipDateFilter="true"
      @close="showSearchModal = false"
      @select="handleSelect"
    />

    <!-- Success Modal -->
    <div v-if="showSuccess" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-md">
      <div class="w-full max-w-md rounded-3xl bg-[var(--color-surface)] p-10 text-center shadow-2xl border border-[var(--color-border)]">
        <div class="mb-6 flex justify-center">
          <div class="flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-5xl">
            ✅
          </div>
        </div>
        <h2 class="mb-2 text-3xl font-black">{{ activeTab }} Created!</h2>
        <p class="mb-8 text-xl text-[var(--color-text-muted)]">{{ successDocName }}</p>
        <button
          @click="closeSuccess"
          class="w-full rounded-2xl bg-[var(--color-highlight)] py-4 text-xl font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:brightness-110 transition-all"
        >
          Great, next one
        </button>
      </div>
    </div>

    <!-- Outstanding Invoices Modal -->
    <div v-if="showInvoicesModal" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div class="w-full max-w-2xl rounded-3xl bg-[var(--color-surface)] p-8 shadow-2xl border border-[var(--color-border)]">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-black uppercase tracking-tight">Outstanding & Unlinked Items</h2>
          <button @click="showInvoicesModal = false" class="h-8 w-8 rounded-full hover:bg-[var(--color-midlight)] transition-colors flex items-center justify-center">
            ✕
          </button>
        </div>
        
        <div class="max-h-[60vh] overflow-y-auto pr-2 space-y-8 custom-scrollbar">
          <!-- Outstanding Invoices -->
          <div v-if="invoices.length || (!filteredPayments.length && !filteredJournals.length && !loadingInvoices)">
            <h3 class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-3 flex items-center gap-2 px-1">
              <span class="w-2 h-2 rounded-full bg-[var(--color-danger)]"></span>
              Outstanding Invoices
            </h3>
            <div class="rounded-2xl border border-[var(--color-border)] overflow-hidden bg-[var(--color-surface-raised)]/30">
              <table class="w-full text-left">
                <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
                  <tr class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                    <th class="px-6 py-3">Voucher No</th>
                    <th class="px-4 py-3">Date</th>
                    <th class="px-6 py-3 text-right">Outstanding</th>
                    <th class="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr v-if="loadingInvoices">
                    <td colspan="4" class="px-6 py-12 text-center text-[var(--color-text-muted)]">Loading...</td>
                  </tr>
                  <tr v-else-if="!invoices.length">
                    <td colspan="4" class="px-6 py-12 text-center text-[var(--color-text-muted)]">No outstanding invoices found.</td>
                  </tr>
                  <tr v-for="inv in invoices" :key="inv.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                    <td class="px-6 py-4 font-mono text-sm font-bold">{{ inv.name }}</td>
                    <td class="px-4 py-4 text-sm">{{ inv.posting_date }}</td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-black text-[var(--color-danger)]">₹{{ inv.outstanding_amount.toLocaleString('en-IN') }}</td>
                    <td class="px-4 py-4 text-right">
                      <button
                        @click="addToAllocation(inv)"
                        :disabled="!!allocationRefs.find(r => r.reference_name === inv.name)"
                        class="rounded-lg px-3 py-1 text-[10px] font-black uppercase transition-all"
                        :class="allocationRefs.find(r => r.reference_name === inv.name)
                          ? 'bg-[var(--color-success)]/15 text-[var(--color-success)] cursor-not-allowed'
                          : 'bg-[var(--color-highlight)]/10 text-[var(--color-highlight)] hover:bg-[var(--color-highlight)] hover:text-white'"
                      >{{ allocationRefs.find(r => r.reference_name === inv.name) ? 'Added' : '+ Add' }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Unlinked Payments -->
          <div v-if="filteredPayments.length">
            <h3 class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-3 flex items-center gap-2 px-1">
              <span class="w-2 h-2 rounded-full bg-[var(--color-success)]"></span>
              Unlinked Payments (Advance)
            </h3>
            <div class="rounded-2xl border border-[var(--color-border)] overflow-hidden bg-[var(--color-surface-raised)]/30">
              <table class="w-full text-left">
                <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
                  <tr class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                    <th class="px-6 py-3">Payment No</th>
                    <th class="px-4 py-3">Date</th>
                    <th class="px-4 py-3">Mode</th>
                    <th class="px-6 py-3 text-right">Unallocated</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr v-for="pe in filteredPayments" :key="pe.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                    <td class="px-6 py-4 font-mono text-sm font-bold">{{ pe.name }}</td>
                    <td class="px-4 py-4 text-sm">{{ pe.posting_date }}</td>
                    <td class="px-4 py-4 text-sm">{{ pe.mode_of_payment }}</td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-black text-[var(--color-success)]">₹{{ pe.unallocated_amount.toLocaleString('en-IN') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Unlinked Journal Entries -->
          <div v-if="filteredJournals.length">
            <h3 class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-3 flex items-center gap-2 px-1">
              <span class="w-2 h-2 rounded-full bg-[var(--color-info)]"></span>
              Unlinked Journal Entries
            </h3>
            <div class="rounded-2xl border border-[var(--color-border)] overflow-hidden bg-[var(--color-surface-raised)]/30">
              <table class="w-full text-left">
                <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
                  <tr class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                    <th class="px-6 py-3">Voucher No</th>
                    <th class="px-4 py-3">Date</th>
                    <th class="px-4 py-3 text-center">Type</th>
                    <th class="px-6 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr v-for="je in filteredJournals" :key="je.reference_row" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                    <td class="px-6 py-4 font-mono text-sm font-bold">
                      {{ je.name }}
                      <div class="text-[9px] font-normal text-[var(--color-text-muted)] truncate max-w-[200px]">{{ je.remarks }}</div>
                    </td>
                    <td class="px-4 py-4 text-sm">{{ je.posting_date }}</td>
                    <td class="px-4 py-4 text-center">
                      <span
                        class="inline-block rounded px-2 py-0.5 text-[10px] font-black uppercase"
                        :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'"
                      >{{ je.direction }}</span>
                    </td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-black"
                        :class="je.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                      ₹{{ je.unallocated_amount.toLocaleString('en-IN') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <div class="mt-8 flex justify-end">
          <button @click="showInvoicesModal = false" class="rounded-xl bg-[var(--color-highlight)] px-8 py-2.5 text-base font-bold text-white hover:brightness-110 transition-all shadow-lg">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()

// --- State ---
const activeTab = ref('Payment')
const postingDate = ref(new Date().toISOString().split('T')[0])
const form = reactive({
  party_type: 'Customer',
  party: '',
  party_name: '',
  account: 'Debtors - SSPL',
  mop_account: '',
  amount: null
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

// --- Computed ---
const isFormValid = computed(() => {
  return form.party && form.amount > 0 && form.mop_account
})

const filteredJournals = computed(() =>
  activeTab.value === 'Receipt'
    ? unlinkedJournals.value.filter(j => j.direction === 'Dr')
    : unlinkedJournals.value.filter(j => j.direction === 'Cr')
)

const filteredPayments = computed(() =>
  activeTab.value === 'Receipt'
    ? unlinkedPayments.value.filter(p => p.payment_type === 'Receive')
    : unlinkedPayments.value.filter(p => p.payment_type === 'Pay')
)

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
  if (searchTarget.value === 'party') return ['Customer', 'Supplier', 'Employee']
  return ['Account']
})

const initialSearchType = computed(() => {
  if (searchTarget.value === 'party') return form.party_type
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
  } else if (searchTarget.value === 'account') {
    form.account = item.name
    accountQuery.value = item.label || item.account_name || item.name
  } else if (searchTarget.value === 'mop') {
    form.mop_account = item.name
    mopAccountQuery.value = item.label || item.account_name || item.name
  }
}

function addToAllocation(inv) {
  if (allocationRefs.value.find(r => r.reference_name === inv.name)) return
  allocationRefs.value.push({
    reference_doctype: invoiceDocType.value,
    reference_name: inv.name,
    total_amount: inv.grand_total,
    outstanding_amount: inv.outstanding_amount,
    allocated_amount: inv.outstanding_amount,
  })
}

function removeAllocation(idx) {
  allocationRefs.value.splice(idx, 1)
}

async function fetchInvoices() {
  if (!form.party) return
  loadingInvoices.value = true
  showInvoicesModal.value = true
  try {
    const [outstandingRes, unlinkedRes] = await Promise.all([
      frappeGet('ssplbilling.api.reconcile_api.get_outstanding_docs', {
        party_type: form.party_type,
        party: form.party
      }),
      frappeGet('ssplbilling.api.reconcile_api.get_unlinked_entries', {
        party_type: form.party_type,
        party: form.party
      })
    ])
    
    invoices.value = outstandingRes.docs || []
    unlinkedPayments.value = unlinkedRes.payment_entries || []
    unlinkedJournals.value = unlinkedRes.journal_entries || []
  } catch (e) {
    console.error('Failed to fetch invoices:', e)
  } finally {
    loadingInvoices.value = false
  }
}

async function fetchOutstanding() {
  if (!form.party) return
  
  try {
    const method = form.party_type === 'Customer' 
      ? 'ssplbilling.api.payment_api.get_customer_ledger'
      : 'ssplbilling.api.payment_api.get_ledger'
      
    const res = await frappeGet(method, { 
      [form.party_type.toLowerCase()]: form.party,
      party_type: form.party_type,
      party: form.party
    })
    
    if (res && res.closing_balance !== undefined) {
      outstandingBalance.value = res.closing_balance
    }
  } catch (e) {
    console.error('Failed to fetch outstanding:', e)
  }
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
  
  if (form.party_type === 'Customer') {
    form.account = 'Debtors - SSPL'
    accountQuery.value = 'Debtors'
  } else {
    form.account = 'Creditors - SSPL'
    accountQuery.value = 'Creditors'
  }
}

function resetForm() {
  form.party = ''
  form.party_name = ''
  partyQuery.value = ''
  form.amount = null
  outstandingBalance.value = null
  invoices.value = []
  unlinkedPayments.value = []
  unlinkedJournals.value = []
  allocationRefs.value = []
  
  if (form.party_type === 'Customer') {
    form.account = 'Debtors - SSPL'
    accountQuery.value = 'Debtors'
  } else {
    form.account = 'Creditors - SSPL'
    accountQuery.value = 'Creditors'
  }
  
  form.mop_account = ''
  mopAccountQuery.value = 'Search Account'
}

async function handleSubmit() {
  if (!isFormValid.value) return
  submitting.value = true
  
  try {
    const payload = {
      payment_type: activeTab.value === 'Payment' ? 'Pay' : 'Receive',
      party_type: form.party_type,
      party: form.party,
      amount: form.amount,
      mop_account: form.mop_account,
      account: form.account,
      posting_date: postingDate.value,
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
    }
  } catch (e) {
    console.error('Submission failed:', e)
    alert('Failed to create payment entry: ' + (e.message || e))
  } finally {
    submitting.value = false
  }
}

function closeSuccess() {
  showSuccess.value = false
  resetForm()
}

// --- Lifecycle ---
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
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
