<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header 
      class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-2.5 shadow-sm bg-[var(--color-surface)] shrink-0"
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
        <h1 class="text-2xl font-normal uppercase tracking-tight">WGB Payments (Dummy Ledger)</h1>
      </div>

      <!-- Right: Date selector -->
      <div class="flex items-center gap-2 pr-6 py-2.5">
        <span class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</span>
        <div class="flex items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] transition-colors">
          <button
            @click="adjustDate(-1)"
            class="rounded-l-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors focus:bg-black/10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div class="relative min-w-[110px] px-3 py-1.5 text-center">
            <span class="text-2xl font-bold">{{ displayDate }}</span>
            <input type="date" v-model="form.date" class="absolute inset-0 opacity-0 cursor-pointer focus:outline-none" />
          </div>
          <button
            @click="adjustDate(1)"
            class="rounded-r-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors focus:bg-black/10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content Panel with Sidebar -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar (Recent Entries) -->
      <aside class="flex w-80 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <div class="p-3 border-b border-[var(--color-border)] flex flex-col gap-2">
          <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Recent Entries</div>
          <div class="relative">
            <input 
              v-model="sidebarFilter"
              type="text"
              placeholder="Search customer..."
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xl font-bold outline-none focus:border-[var(--color-focus)] transition-all"
            />
          </div>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loading" class="p-4 text-center text-lg text-[var(--color-text-muted)]">Loading...</div>
          <div v-else-if="!entries.length" class="p-4 text-center text-lg text-[var(--color-text-muted)] italic">No entries found</div>
          <div 
            v-for="e in filteredEntries" 
            :key="e.name"
            class="border-b border-[var(--color-border)] p-4 hover:bg-[var(--color-midlight)]/30 cursor-pointer transition-colors"
            @click="selectEntry(e)"
          >
            <div class="flex justify-between items-start mb-1">
              <span class="font-mono text-xl font-bold text-[var(--color-info)]">{{ e.name }}</span>
              <span class="text-lg text-[var(--color-text-muted)] font-mono">{{ formatDate(e.date) }}</span>
            </div>
            <div class="text-xl font-bold text-[var(--color-text)] truncate">{{ e.customer }}</div>
            <div class="flex gap-4 mt-2 text-xl font-mono font-bold">
              <span class="text-[var(--color-danger)]" v-if="e.debit > 0">Dr: {{ fmt(e.debit) }}</span>
              <span class="text-[var(--color-success)]" v-if="e.credit > 0">Cr: {{ fmt(e.credit) }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Entry Form (Excel Table style) -->
      <main class="flex-1 overflow-y-auto p-6 custom-scrollbar bg-[var(--color-bg)] flex flex-col gap-6">
        <div class="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden shrink-0">
          <table class="w-full text-left border-collapse">
            <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
              <tr class="text-3xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-6 py-4 w-[35%]">Customer / Party</th>
                <th class="px-6 py-4 text-right w-[20%] text-[var(--color-danger)]">Debit (Dr)</th>
                <th class="px-6 py-4 text-right w-[20%] text-[var(--color-success)]">Credit (Cr)</th>
                <th class="px-8 py-4 text-right w-[12.5%]">Dummy Balance</th>
                <th class="px-8 py-4 text-right w-[12.5%]">New Dummy Balance</th>
              </tr>
            </thead>
            <tbody>
              <tr class="divide-x divide-[var(--color-border)]">
                <!-- Customer Search input -->
                <td class="px-4 py-3 group hover:bg-[var(--color-midlight)]/20 transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <div class="relative">
                    <input
                      ref="customerInputRef"
                      v-model="customerQuery"
                      type="text"
                      class="w-full bg-transparent text-4xl font-normal focus:outline-none placeholder:text-[var(--color-text-muted)]/40"
                      placeholder="Search Customer..."
                      @input="onCustomerInput"
                      @focus="onCustomerFocus"
                      @keydown="handleInputKeydown"
                    />
                    <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-highlight)] font-bold group-focus-within:text-[var(--color-text-on-focus)] uppercase">Type to Search</div>
                    
                    <QuickLedgerSearch
                      ref="quickSearchRef"
                      :results="searchResults"
                      :query="customerQuery"
                      :anchorEl="customerInputRef"
                      v-if="showQuickSearch && searchResults.length"
                      @select="handleSelect"
                      @close="showQuickSearch = false"
                    />
                  </div>
                </td>

                <!-- Debit (Dr) Input -->
                <td class="px-6 py-3 transition-colors bg-red-500/5 focus-within:bg-[var(--color-focus)]">
                  <input
                    ref="debitInputRef"
                    v-model.number="form.debit"
                    type="number" step="0.01"
                    @input="onDebitInput"
                    @keydown.enter.prevent="handleDebitEnter"
                    class="w-full bg-transparent text-5xl font-light text-right focus:outline-none text-[var(--color-text)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none placeholder:text-[var(--color-text-muted)]/40"
                    placeholder="0.00"
                  />
                </td>

                <!-- Credit (Cr) Input -->
                <td class="px-6 py-3 transition-colors bg-green-500/5 focus-within:bg-[var(--color-focus)]">
                  <input
                    ref="creditInputRef"
                    v-model.number="form.credit"
                    type="number" step="0.01"
                    @input="onCreditInput"
                    @keydown.enter.prevent="handleCreditEnter"
                    class="w-full bg-transparent text-5xl font-light text-right focus:outline-none text-[var(--color-text)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none placeholder:text-[var(--color-text-muted)]/40"
                    placeholder="0.00"
                  />
                </td>

                <!-- Dummy Balance -->
                <td class="px-8 py-3 bg-[var(--color-surface-raised)]">
                  <div v-if="outstandingBalance !== null" class="flex flex-col items-end">
                    <div class="text-4xl font-black text-[var(--color-text)]">
                      {{ Math.abs(outstandingBalance).toLocaleString('en-IN') }} {{ outstandingBalance >= 0 ? 'Dr' : 'Cr' }}
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-2xl italic font-medium text-right">—</div>
                </td>

                <!-- New Dummy Balance -->
                <td class="px-8 py-3 bg-[var(--color-highlight)]/5">
                  <div v-if="outstandingBalance !== null" class="flex flex-col items-end">
                    <div class="text-4xl font-black" :class="newBalance >= 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                      {{ Math.abs(newBalance).toLocaleString('en-IN') }} {{ newBalance >= 0 ? 'Dr' : 'Cr' }}
                    </div>
                  </div>
                  <div v-else class="text-[var(--color-text-muted)] text-2xl italic font-medium text-right">—</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>

    <!-- Bottom Action Bar -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-[0_-4px_20px_rgba(0,0,0,0.1)] shrink-0">
      <div class="flex items-center justify-between gap-8">
        <div class="flex gap-4">
          <button 
            class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-8 py-4 text-2xl font-bold hover:bg-[var(--color-midlight)] active:scale-95 transition-all"
            @click="resetForm"
          >
            Clear
          </button>
        </div>
        <div class="flex items-center pl-8">
          <button
            ref="saveBtnRef"
            @click="saveEntry"
            :disabled="saving || !form.customer || (form.debit <= 0 && form.credit <= 0)"
            class="group relative flex items-center gap-4 overflow-hidden rounded-2xl bg-[var(--color-success)] px-16 py-6 text-4xl font-black text-[var(--color-text-on-highlight)] shadow-xl transition-all hover:scale-[1.02] hover:shadow-2xl active:scale-95 disabled:opacity-40 disabled:hover:scale-100 disabled:grayscale focus:outline-none focus:ring-8 focus:ring-[var(--color-focus)]/50 focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:scale-[1.02]"
          >
            <span v-if="saving" class="flex items-center gap-3">
              <svg class="h-10 w-10 animate-spin" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving...
            </span>
            <span v-else class="flex items-center gap-4">
              Save Entry (End)
              <svg class="h-10 w-10 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </span>
          </button>
        </div>
      </div>
    </footer>



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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import QuickLedgerSearch from '../components/QuickLedgerSearch.vue'
import { useLedgerCache, searchLedgersInCache } from '../services/ledgerCache'

const router = useRouter()
const API = 'ssplbilling.api.gst_ledger_api'

// --- State ---
const today = new Date().toISOString().split('T')[0]
const emptyForm = () => ({
  date: today,
  customer: '',
  debit: 0,
  credit: 0
})

const form = ref(emptyForm())
const customerQuery = ref('')
const outstandingBalance = ref(null)
const saving = ref(false)
const showSuccess = ref(false)
const successDocName = ref('')

const customerInputRef = ref(null)
const debitInputRef = ref(null)
const creditInputRef = ref(null)
const saveBtnRef = ref(null)

// --- Customer Search (QuickLedgerSearch) ---
const showQuickSearch = ref(false)
const searchResults = ref([])
const quickSearchRef = ref(null)

const { refreshLedgerCache } = useLedgerCache()

function searchCustomers() {
  const q = customerQuery.value.trim()
  if (!q) {
    searchResults.value = []
    showQuickSearch.value = false
    return
  }
  try {
    searchResults.value = searchLedgersInCache(q, 'Customer')
    showQuickSearch.value = true
  } catch (e) {
    console.warn('[GstDummyLedger] searchCustomers failed:', e)
    searchResults.value = []
  }
}

function onCustomerInput() {
  form.value.customer = ''
  outstandingBalance.value = null
  searchCustomers()
}

function onCustomerFocus() {
  showQuickSearch.value = true
  searchCustomers()
}

function handleInputKeydown(e) {
  if (e.key === 'Escape') {
    if (showQuickSearch.value) {
      e.preventDefault()
      e.stopPropagation()
      showQuickSearch.value = false
    }
  } else if (e.key === 'Enter') {
    if (showQuickSearch.value && searchResults.value.length > 0 && quickSearchRef.value) {
      quickSearchRef.value.handleKeydown(e)
    } else {
      if (form.value.customer) {
        e.preventDefault()
        debitInputRef.value?.focus()
      }
    }
  } else if (showQuickSearch.value && quickSearchRef.value) {
    quickSearchRef.value.handleKeydown(e)
  }
}

// --- computed ---
const displayDate = computed(() => {
  if (!form.value.date) return ''
  const d = new Date(form.value.date)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
})

const newBalance = computed(() => {
  if (outstandingBalance.value === null) return null
  const deb = parseFloat(form.value.debit) || 0
  const cred = parseFloat(form.value.credit) || 0
  return outstandingBalance.value + deb - cred
})

// --- date navigators ---
function adjustDate(dir) {
  const d = new Date(form.value.date)
  d.setDate(d.getDate() + dir)
  form.value.date = d.toISOString().split('T')[0]
}

function openSearch() {
  showQuickSearch.value = true
  nextTick(() => {
    customerInputRef.value?.focus()
    searchCustomers()
  })
}

async function handleSelect(item) {
  showQuickSearch.value = false
  form.value.customer = item.name
  customerQuery.value = item.label || item.customer_name || item.name
  
  await fetchBalance(item.name)
  nextTick(() => debitInputRef.value?.focus())
}

async function fetchBalance(customerName) {
  if (!customerName) {
    outstandingBalance.value = null
    return
  }
  try {
    const res = await frappeGet('ssplbilling.api.gst_ledger_api.get_gst_ledger', { customer: customerName })
    outstandingBalance.value = res.closing_balance || 0
  } catch (e) {
    console.error(e)
    outstandingBalance.value = 0
  }
}

// --- Actions ---
function onDebitInput() {
  if (form.value.debit > 0) {
    form.value.credit = 0
  }
}

function onCreditInput() {
  if (form.value.credit > 0) {
    form.value.debit = 0
  }
}

function handleDebitEnter() {
  if (form.value.debit > 0) {
    saveBtnRef.value?.focus()
  } else {
    creditInputRef.value?.focus()
  }
}

function handleCreditEnter() {
  saveBtnRef.value?.focus()
}

async function saveEntry() {
  if (!form.value.customer) { alert('Select a customer'); return }
  const deb = parseFloat(form.value.debit) || 0
  const cred = parseFloat(form.value.credit) || 0
  if (deb <= 0 && cred <= 0) { alert('Enter a valid Debit or Credit amount'); return }

  saving.value = true
  
  const payload = {
    date: form.value.date,
    customer: form.value.customer,
    debit: deb,
    credit: cred
  }

  try {
    const res = await frappePost(`${API}.create_gst_dummy_entry`, { data: JSON.stringify(payload) })
    successDocName.value = res
    showSuccess.value = true
    setTimeout(() => showSuccess.value = false, 3000)
    resetForm()
    fetchEntries()
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  form.value = emptyForm()
  customerQuery.value = ''
  outstandingBalance.value = null
  nextTick(() => openSearch())
}

// --- Sidebar Entries ---
const entries = ref([])
const loading = ref(false)
const sidebarFilter = ref('')

async function fetchEntries() {
  loading.value = true
  try {
    entries.value = await frappeGet(`${API}.get_gst_dummy_entries`)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const filteredEntries = computed(() => {
  const q = sidebarFilter.value.toLowerCase()
  if (!q) return entries.value
  return entries.value.filter(e => e.customer.toLowerCase().includes(q) || e.name.toLowerCase().includes(q))
})

async function selectEntry(e) {
  form.value.date = e.date
  form.value.customer = e.customer
  customerQuery.value = e.customer
  showQuickSearch.value = false
  form.value.debit = parseFloat(e.debit) || 0
  form.value.credit = parseFloat(e.credit) || 0
  await fetchBalance(e.customer)
}

function formatDate(dateString) {
  if (!dateString) return ''
  const d = new Date(dateString)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

function fmt(n) {
  return parseFloat(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function handleKeyDown(e) {
  if (e.key === 'End') { e.preventDefault(); saveEntry() }
  if (e.key === 'Escape') {
    if (showQuickSearch.value) {
      showQuickSearch.value = false
      return
    }
    router.push('/')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  fetchEntries()
  refreshLedgerCache(false).catch(e => console.error('Cache sync failed', e))
  nextTick(() => {
    openSearch()
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
