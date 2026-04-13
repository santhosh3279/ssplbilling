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
    <main class="flex-1 overflow-hidden p-6">
      <div class="mx-auto flex h-full max-w-5xl flex-col gap-6">
        
        <!-- Tab Switcher -->
        <div class="flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1.5 shadow-sm self-start">
          <button
            v-for="t in ['Payment', 'Receipt']"
            :key="t"
            @click="activeTab = t"
            class="min-w-[160px] rounded-lg px-6 py-2.5 text-lg font-bold transition-all duration-200"
            :class="activeTab === t 
              ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-md translate-y-[-1px]' 
              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)]'"
          >
            {{ t }}
          </button>
        </div>

        <!-- Form Card -->
        <div class="flex-1 overflow-y-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-xl">
          <div class="grid grid-cols-2 gap-x-12 gap-y-8">
            
            <!-- Party Type -->
            <div class="space-y-2">
              <label class="block text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">Party Type</label>
              <select
                v-model="form.party_type"
                class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                @change="handlePartyTypeChange"
              >
                <option value="Customer">Customer</option>
                <option value="Supplier">Supplier</option>
                <option value="Employee">Employee</option>
              </select>
            </div>

            <!-- Party Name (Searchable) -->
            <div class="space-y-2 relative">
              <label class="block text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">Party Name</label>
              <div class="relative group">
                <input
                  v-model="partyQuery"
                  @click="openPartySearch"
                  @keydown.enter="openPartySearch"
                  readonly
                  class="w-full cursor-pointer rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                  :placeholder="'Click to Search Party...'"
                />
              </div>
            </div>

            <!-- Party Account (Paid From / Paid To) -->
            <div class="space-y-2 relative">
              <label class="block text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                {{ activeTab === 'Payment' ? 'Account Paid To (Party)' : 'Account Received From (Party)' }}
              </label>
              <div class="relative group">
                <input
                  v-model="accountQuery"
                  @input="searchAccountsList"
                  @focus="showAccountDropdown = true"
                  class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                  placeholder="Search Party Account..."
                />
                <div v-if="showAccountDropdown && accountResults.length" class="absolute left-0 right-0 top-full z-50 mt-2 max-h-64 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl backdrop-blur-md">
                  <div
                    v-for="a in accountResults"
                    :key="a.name"
                    @click="selectAccount(a)"
                    class="cursor-pointer px-5 py-3 text-lg hover:bg-[var(--color-highlight)] hover:text-[var(--color-text-on-highlight)] transition-colors border-b border-[var(--color-border)] last:border-0"
                  >
                    <div class="font-bold">{{ a.account_name }}</div>
                    <div class="text-sm opacity-70">{{ a.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Bank/Cash Account (Paid From / Paid To) -->
            <div class="space-y-2 relative">
              <label class="block text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                {{ activeTab === 'Payment' ? 'Account Paid From (Bank/Cash)' : 'Account Paid To (Bank/Cash)' }}
              </label>
              <div class="relative group">
                <input
                  v-model="mopAccountQuery"
                  @input="searchMopAccountsList"
                  @focus="showMopAccountDropdown = true"
                  class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                  placeholder="Search Bank/Cash Account..."
                />
                <div v-if="showMopAccountDropdown && mopAccountResults.length" class="absolute left-0 right-0 top-full z-50 mt-2 max-h-64 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl backdrop-blur-md">
                  <div
                    v-for="a in mopAccountResults"
                    :key="a.name"
                    @click="selectMopAccount(a)"
                    class="cursor-pointer px-5 py-3 text-lg hover:bg-[var(--color-highlight)] hover:text-[var(--color-text-on-highlight)] transition-colors border-b border-[var(--color-border)] last:border-0"
                  >
                    <div class="font-bold">{{ a.account_name }}</div>
                    <div class="text-sm opacity-70">{{ a.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Paid Amount -->
            <div class="space-y-2">
              <label class="block text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">Amount (₹)</label>
              <input
                v-model.number="form.amount"
                type="number"
                step="0.01"
                class="w-full rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-3xl font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:outline-none transition-all"
                placeholder="0.00"
              />
            </div>

            <!-- Outstanding Button -->
            <div class="col-span-2 pt-4 flex items-center justify-between gap-4">
              <button
                @click="fetchOutstanding"
                :disabled="!form.party"
                class="flex items-center gap-2 rounded-xl bg-[var(--color-info)]/10 px-6 py-3 font-bold text-[var(--color-info)] hover:bg-[var(--color-info)]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>🔍</span> Get Outstanding Balances Account
              </button>
              
              <div v-if="outstandingBalance !== null" class="text-xl font-bold">
                Outstanding: <span :class="outstandingBalance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                  ₹{{ Math.abs(outstandingBalance).toLocaleString('en-IN') }} {{ outstandingBalance > 0 ? 'Dr' : 'Cr' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="flex items-center justify-end gap-4 pb-4">
          <button
            @click="resetForm"
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 text-xl font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] transition-all"
          >
            Clear (Esc)
          </button>
          <button
            @click="handleSubmit"
            :disabled="submitting || !isFormValid"
            class="min-w-[240px] rounded-xl bg-[var(--color-success)] px-10 py-4 text-2xl font-black text-white shadow-lg transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
          >
            <span v-if="submitting">Processing...</span>
            <span v-else>Submit {{ activeTab }}</span>
          </button>
        </div>
      </div>
    </main>

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      initialType="All"
      :skipDateFilter="true"
      @close="showCustomerSearchModal = false"
      @select="pickCust"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()

// --- State ---
const activeTab = ref('Payment')
const form = reactive({
  party_type: 'Customer',
  party: '',
  party_name: '',
  account: 'Debtors - SSPL',
  mop_account: 'Cash - SSPL',
  amount: null
})

const showCustomerSearchModal = ref(false)
const custSearchModalRef = ref(null)

const partyQuery = ref('')

const accountQuery = ref('Debtors')
const accountResults = ref([])
const showAccountDropdown = ref(false)

const mopAccountQuery = ref('Cash')
const mopAccountResults = ref([])
const showMopAccountDropdown = ref(false)

const submitting = ref(false)
const showSuccess = ref(false)
const successDocName = ref('')
const outstandingBalance = ref(null)

// --- Computed ---
const isFormValid = computed(() => {
  return form.party && form.amount > 0 && form.mop_account
})

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
function openPartySearch() {
  showCustomerSearchModal.value = true
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function pickCust(item) {
  showCustomerSearchModal.value = false
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
}

async function searchAccountsList() {
  const res = await frappeGet('ssplbilling.api.payment_api.search_accounts', { query: accountQuery.value })
  accountResults.value = res || []
}

function selectAccount(a) {
  form.account = a.name
  accountQuery.value = a.account_name
  showAccountDropdown.value = false
}

async function searchMopAccountsList() {
  const res = await frappeGet('ssplbilling.api.payment_api.search_accounts', { query: mopAccountQuery.value })
  mopAccountResults.value = res || []
}

function selectMopAccount(a) {
  form.mop_account = a.name
  mopAccountQuery.value = a.account_name
  showMopAccountDropdown.value = false
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
  
  if (form.party_type === 'Customer') {
    form.account = 'Debtors - SSPL'
    accountQuery.value = 'Debtors'
  } else {
    form.account = 'Creditors - SSPL'
    accountQuery.value = 'Creditors'
  }
  
  form.mop_account = 'Cash - SSPL'
  mopAccountQuery.value = 'Cash'
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
      account: form.account // Party Account
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
  searchAccountsList() // Initial empty search
  searchMopAccountsList()
  
  // Close dropdowns on outside click
  window.addEventListener('click', (e) => {
    if (!e.target.closest('.group')) {
      showAccountDropdown.value = false
      showMopAccountDropdown.value = false
    }
  })
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
