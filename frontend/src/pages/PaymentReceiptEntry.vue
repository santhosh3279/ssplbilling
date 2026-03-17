<template>
  <div class="flex h-screen flex-col bg-gray-50 overflow-hidden">
    <!-- Header -->
    <header class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-8 shadow-sm z-20 shrink-0">
      <div class="flex items-center gap-6">
        <button @click="router.push('/')" class="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-500 shadow-sm hover:bg-gray-50 active:scale-95 transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-2xl font-black tracking-tight text-gray-900 uppercase">Payment & Receipt</h1>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="flex rounded-xl bg-gray-100 p-1 border border-gray-200">
          <button 
            v-for="m in modes" 
            :key="m.id"
            @click="switchMode(m.id)"
            class="rounded-lg px-6 py-2 text-sm font-black uppercase tracking-widest transition-all"
            :class="entryMode === m.id ? 'bg-white text-blue-600 shadow-md border border-gray-100' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ m.label }}
          </button>
        </div>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto bg-gray-50 px-4 py-8">
      <div class="mx-auto max-w-2xl">
        <!-- Main Form Card -->
        <div class="rounded-3xl border border-gray-200 bg-white p-8 shadow-xl">
          <div class="space-y-8">
            <!-- Party Search -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">
                    {{ activePartyType }}
                  </label>
                  <div class="flex rounded-lg bg-gray-100 p-0.5 border border-gray-200 overflow-hidden">
                    <button
                      v-for="pt in ['Customer', 'Supplier', 'Employee']"
                      :key="pt"
                      @click="setReceiptPartyType(pt)"
                      class="px-3 py-1 text-[9px] font-black uppercase tracking-widest transition-all rounded-md"
                      :class="receiptPartyType === pt ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'"
                    >
                      {{ pt }}
                    </button>
                  </div>
                </div>
                <button
                  v-if="party"
                  @click="showLedgerWindow = true"
                  class="text-[10px] font-black text-blue-600 hover:underline uppercase tracking-widest"
                >
                  View Ledger &rarr;
                </button>
              </div>
              <div
                ref="partyInput"
                class="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 px-6 py-4 text-xl font-black outline-none cursor-pointer hover:border-blue-400 transition-all focus:ring-4 focus:ring-blue-50 shadow-inner"
                :class="party ? 'text-gray-900 border-blue-100 bg-blue-50/30' : 'text-gray-300 italic'"
                tabindex="0"
                @click="openSearch"
                @keydown.enter.prevent="party ? nextFocus('date') : openSearch()"
                @keydown.space.prevent="openSearch"
              >
                {{ partyName || `Select ${activePartyType.toLowerCase()}...` }}
              </div>
            </div>

            <!-- Date & Amount Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 ml-1">Posting Date</label>
                <input
                  ref="dateInput"
                  v-model="date"
                  type="date"
                  class="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 px-6 py-4 text-lg font-black outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all shadow-inner"
                  @keydown.enter.prevent="nextFocus('amount')"
                />
              </div>

              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600 ml-1">Paid Amount (₹)</label>
                <input
                  ref="amountInput"
                  v-model.number="amount"
                  type="number"
                  class="w-full rounded-2xl border-2 border-blue-100 bg-blue-50/20 px-6 py-4 text-2xl font-black text-blue-600 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all shadow-inner"
                  placeholder="0.00"
                  @focus="$event.target.select()"
                  @keydown.enter.prevent="onAmountEnter"
                />
              </div>
            </div>

            <!-- Mode of Payment -->
            <div class="space-y-2">
              <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 ml-1">
                Payment Mode
                <span class="ml-2 font-medium normal-case text-gray-300">← → arrow keys to switch</span>
              </label>
              <div
                ref="mopZoneRef"
                tabindex="0"
                class="grid grid-cols-4 gap-3 outline-none focus:ring-2 focus:ring-blue-200 p-1"
                @keydown.left.prevent="cycleMop(-1)"
                @keydown.right.prevent="cycleMop(1)"
                @keydown.enter.prevent="nextFocus('ref')"
              >
                <button
                  v-for="m in mops"
                  :key="m"
                  @click="selectMop(m); mopZoneRef?.focus()"
                  class="rounded-2xl border-2 py-3 text-xs font-black uppercase tracking-widest transition-all shadow-sm"
                  :class="mop === m && !selectedLedger ? 'border-blue-500 bg-blue-600 text-white shadow-blue-200' : 'border-gray-100 bg-gray-50 text-gray-500 hover:bg-gray-100'"
                >
                  {{ m }}
                </button>
              </div>
            </div>

            <!-- Linked References -->
            <div v-if="selectedInvoices.length" class="rounded-3xl border-2 border-blue-100 bg-blue-50/30 p-6 animate-in slide-in-from-top-2 duration-300">
              <label class="mb-4 block text-[10px] font-black uppercase tracking-[0.2em] text-blue-500">Allocated References</label>
              <div class="space-y-2">
                <div 
                  v-for="(link, idx) in selectedInvoices" 
                  :key="link.name"
                  class="flex items-center justify-between rounded-2xl bg-white p-4 shadow-sm border border-blue-50"
                >
                  <div class="flex flex-col">
                    <span class="font-mono text-xs font-black text-gray-700 tracking-tight">{{ link.name }}</span>
                    <span class="text-[10px] font-bold text-blue-600 mt-0.5">₹{{ link.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
                  </div>
                  <button @click="removeInvoice(idx)" class="h-8 w-8 flex items-center justify-center rounded-full text-gray-300 hover:bg-rose-50 hover:text-rose-500 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  </button>
                </div>
              </div>
              <div class="mt-4 flex justify-between border-t border-blue-100 pt-4 text-sm font-black text-blue-700 uppercase tracking-widest">
                <span>Total Allocated</span>
                <span class="font-mono">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
              </div>
            </div>

            <!-- More Details (Collapsible or just separated) -->
            <div class="pt-4 space-y-6 border-t border-gray-100">
              <!-- Ledger Override -->
              <div class="space-y-2">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 ml-1">
                  Ledger Account <span class="normal-case text-gray-300 font-medium">(optional override)</span>
                </label>
                <div class="relative">
                  <input
                    v-model="ledgerQuery"
                    @input="onLedgerInput"
                    @keydown.escape="closeLedgerDropdown"
                    @keydown.down.prevent="ledgerHighlight = Math.min(ledgerHighlight + 1, ledgerResults.length - 1)"
                    @keydown.up.prevent="ledgerHighlight = Math.max(ledgerHighlight - 1, 0)"
                    @keydown.enter.prevent="pickLedger(ledgerResults[ledgerHighlight])"
                    class="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 px-6 py-3 text-sm font-black outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50 shadow-inner"
                    :placeholder="selectedLedger ? selectedLedger : 'Search account name...'"
                  />
                  <button
                    v-if="selectedLedger"
                    @click="clearLedger"
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300 hover:text-rose-500"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  </button>
                  <div
                    v-if="ledgerResults.length && ledgerDropdownOpen"
                    class="absolute z-30 mt-2 w-full rounded-2xl border border-gray-200 bg-white shadow-2xl overflow-hidden"
                  >
                    <div
                      v-for="(acct, idx) in ledgerResults"
                      :key="acct.name"
                      @click="pickLedger(acct)"
                      @mouseenter="ledgerHighlight = idx"
                      class="cursor-pointer px-6 py-3 text-sm transition-colors border-b last:border-0 border-gray-50"
                      :class="idx === ledgerHighlight ? 'bg-blue-50 text-blue-800' : 'text-gray-700 hover:bg-gray-50'"
                    >
                      <div class="font-black">{{ acct.account_name }}</div>
                      <div class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{{ acct.name }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Reference & Remarks Grid -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 ml-1">Reference No.</label>
                  <input
                    ref="refInput"
                    v-model="referenceNo"
                    class="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 px-6 py-3 text-sm font-black outline-none focus:border-blue-500 shadow-inner"
                    placeholder="Cheque / UTR / Txn ID"
                    @keydown.enter.prevent="nextFocus('remarks')"
                  />
                </div>
                <div class="space-y-2">
                  <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 ml-1">Remarks</label>
                  <input
                    ref="remarksInput"
                    v-model="remarks"
                    class="w-full rounded-2xl border-2 border-gray-100 bg-gray-50 px-6 py-3 text-sm font-bold outline-none focus:border-blue-500 shadow-inner"
                    placeholder="Internal notes..."
                    @keydown.enter.prevent="saveEntry"
                  />
                </div>
              </div>
            </div>

            <!-- Save Button -->
            <div class="pt-6">
              <button 
                @click="saveEntry" 
                :disabled="saving || !canSave"
                class="group relative w-full overflow-hidden rounded-2xl bg-slate-900 py-5 font-black uppercase tracking-[0.2em] text-white shadow-2xl transition-all active:scale-95 disabled:grayscale disabled:opacity-50"
              >
                <div v-if="saving" class="flex items-center justify-center gap-3">
                  <div class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  <span>Saving...</span>
                </div>
                <div v-else class="flex items-center justify-center gap-2">
                  <span>Save Entry (F9)</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="ml-1 group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ALLOCATION SUBWINDOW (OUTSTANDINGS) -->
    <transition name="fade">
      <div v-if="showAllocationModal" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 backdrop-blur-md p-4">
        <div class="w-full max-w-4xl overflow-hidden rounded-[2.5rem] border border-gray-200 bg-white shadow-2xl flex flex-col max-h-[90vh]">
          <!-- Modal Header -->
          <div class="bg-gray-50 px-8 py-6 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 class="text-xl font-black text-gray-900 uppercase tracking-tight">Allocate Payment</h2>
              <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Remaining to Allocate: <span class="text-blue-600 font-mono text-xs ml-1">₹{{ remainingToAllocate.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span></p>
            </div>
            <button @click="showAllocationModal = false" class="h-10 w-10 flex items-center justify-center rounded-full bg-white border border-gray-200 text-gray-400 hover:text-rose-500 hover:shadow-md transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          <!-- Modal Content (Table) -->
          <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
            <table class="w-full text-left border-collapse">
              <thead class="sticky top-0 bg-white z-10">
                <tr class="bg-gray-50/50 text-[10px] font-black uppercase tracking-widest text-gray-500 border-b border-gray-100">
                  <th class="px-8 py-4">Bill No / Date</th>
                  <th class="px-4 py-4 text-center">Days</th>
                  <th class="px-4 py-4 text-right">Outstanding</th>
                  <th class="px-8 py-4 text-right" style="width: 200px;">This Payment</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="inv in outstandings" :key="inv.name" class="hover:bg-blue-50/30 transition-colors group">
                  <td class="px-8 py-4">
                    <div class="text-sm font-black text-gray-800 font-mono">{{ inv.name }}</div>
                    <div class="text-[10px] font-bold text-gray-400 mt-0.5 uppercase">{{ formatDate(inv.posting_date) }}</div>
                  </td>
                  <td class="px-4 py-4 text-center">
                    <span class="inline-flex rounded-lg px-2.5 py-1 text-[10px] font-black uppercase tracking-widest"
                      :class="getDaysOutstanding(inv.posting_date) > 30 ? 'bg-rose-50 text-rose-600' : 'bg-gray-100 text-gray-500'">
                      {{ getDaysOutstanding(inv.posting_date) }} Days
                    </span>
                  </td>
                  <td class="px-4 py-4 text-right font-mono text-sm font-bold text-gray-600">₹{{ inv.outstanding_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</td>
                  <td class="px-8 py-4 text-right">
                    <input 
                      type="number"
                      v-model.number="allocations[inv.name]"
                      @input="handleAllocationInput(inv.name, inv.outstanding_amount)"
                      @focus="$event.target.select()"
                      placeholder="0.00"
                      class="w-full rounded-xl border-2 border-gray-100 bg-gray-50 px-4 py-2 text-right font-mono font-black text-blue-600 focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all outline-none"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Modal Footer -->
          <div class="bg-gray-50 px-8 py-6 border-t border-gray-200 flex items-center justify-between">
            <div class="flex gap-6">
              <div class="space-y-0.5">
                <div class="text-[9px] font-black uppercase tracking-widest text-gray-400">Selected Total</div>
                <div class="text-lg font-black text-gray-900 font-mono">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</div>
              </div>
            </div>
            <button 
              @click="finishAllocation"
              class="rounded-2xl bg-blue-600 px-10 py-4 text-sm font-black uppercase tracking-widest text-white shadow-xl shadow-blue-200 hover:bg-blue-700 active:scale-95 transition-all"
            >
              Finish Allocation
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modals & Sub-windows -->
    <CustomerSearchModal
      ref="searchModalRef"
      :show="showSearchModal"
      :initial-type="activePartyType"
      :allowed-types="['Customer', 'Supplier', 'Employee']"
      :skip-date-filter="true"
      @close="showSearchModal = false"
      @select="pickParty"
    />

    <CustomerLedger
      v-if="showLedgerWindow"
      :is-sub-window="true"
      :ledger-name="party"
      :ledger-type="activePartyType"
      @close="showLedgerWindow = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet, frappePost, fetchDashboardSettings, searchAccounts } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import CustomerLedger from './CustomerLedger.vue'

const router = useRouter()
const route = useRoute()

// ─── State ───────────────────────────────────────────────────────────────────
const modes = [{ id: 'Receive', label: 'Receipt' }, { id: 'Pay', label: 'Payment' }]
const mops = ['Cash', 'Card', 'Bank', 'UPI']

const entryMode = ref(route.query.mode || 'Receive')
const date = ref(getTodayIST())
const party = ref('')
const partyName = ref('')
const amount = ref(0)
const mop = ref('Cash')
const referenceNo = ref('')
const remarks = ref('')
const selectedInvoices = ref([]) 
const outstandings = ref([])
const allocations = ref({}) // { invoice_name: allocated_amount }

const showSearchModal = ref(false)
const showLedgerWindow = ref(false)
const showAllocationModal = ref(false)
const loadingOutstandings = ref(false)
const saving = ref(false)
const userDefaults = ref(null)

// DOM Refs
const searchModalRef = ref(null)
const partyInput = ref(null)
const dateInput = ref(null)
const amountInput = ref(null)
const mopZoneRef = ref(null)
const refInput = ref(null)
const remarksInput = ref(null)

// ─── Receipt party type ──────────────────────────────────────────────────────
const receiptPartyType = ref(route.query.mode === 'Pay' ? 'Supplier' : 'Customer')
const activePartyType = computed(() => receiptPartyType.value)

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) 
  return formatter.format(date)
}

function setReceiptPartyType(pt) {
  if (receiptPartyType.value === pt) return
  receiptPartyType.value = pt
  party.value = ''; partyName.value = ''; outstandings.value = []; selectedInvoices.value = []; amount.value = 0
  nextTick(() => partyInput.value?.focus())
}

// ─── Ledger override ──────────────────────────────────────────────────────────
const ledgerQuery = ref('')
const ledgerResults = ref([])
const ledgerDropdownOpen = ref(false)
const ledgerHighlight = ref(0)
const selectedLedger = ref('')
let ledgerDebounceTimer = null

// ─── Computed ────────────────────────────────────────────────────────────────
const canSave = computed(() => party.value && amount.value > 0)

const totalAllocated = computed(() => {
  return Object.values(allocations.value).reduce((sum, val) => sum + (Number(val) || 0), 0)
})

const remainingToAllocate = computed(() => {
  return Math.max(0, amount.value - totalAllocated.value)
})

const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
  })
})

// ─── Methods ─────────────────────────────────────────────────────────────────
function switchMode(m) {
  entryMode.value = m; receiptPartyType.value = m === 'Pay' ? 'Supplier' : 'Customer'; resetForm()
  nextTick(() => partyInput.value?.focus())
}

function resetForm() {
  party.value = ''; partyName.value = ''; showSearchModal.value = false; amount.value = 0
  referenceNo.value = ''; remarks.value = ''; selectedInvoices.value = []; outstandings.value = []
  selectedLedger.value = ''; ledgerQuery.value = ''; ledgerResults.value = []; allocations.value = {}
}

async function loadUserDefaults() {
  try {
    const settings = await fetchDashboardSettings()
    if (settings?.user_defaults) userDefaults.value = settings.user_defaults
  } catch (e) { console.warn('[PaymentEntry] Failed to load user defaults:', e) }
}

const focusMap = {
  date:    () => dateInput.value?.focus(),
  amount:  () => amountInput.value?.focus(),
  mop:     () => nextTick(() => mopZoneRef.value?.focus()),
  ref:     () => refInput.value?.focus(),
  remarks: () => remarksInput.value?.focus(),
}

function nextFocus(target) { focusMap[target]?.() }

async function onAmountEnter() {
  if (amount.value <= 0) return
  
  if (outstandings.value.length > 0) {
    // Initialize allocations object
    allocations.value = {}
    selectedInvoices.value.forEach(inv => {
      allocations.value[inv.name] = inv.amount
    })
    
    showAllocationModal.value = true
  } else {
    nextFocus('mop')
  }
}

function handleAllocationInput(name, max) {
  const currentVal = Number(allocations.value[name]) || 0
  
  // 1. Don't exceed outstanding
  if (currentVal > max) allocations.value[name] = max
  
  // 2. Don't exceed remaining total amount
  const otherAllocations = Object.entries(allocations.value)
    .filter(([k]) => k !== name)
    .reduce((sum, [, v]) => sum + (Number(v) || 0), 0)
  
  const allowedMax = amount.value - otherAllocations
  if (allocations.value[name] > allowedMax) {
    allocations.value[name] = parseFloat(allowedMax.toFixed(2))
  }

  // Auto exit if fully allocated
  if (remainingToAllocate.value < 0.01) {
    setTimeout(finishAllocation, 300)
  }
}

function finishAllocation() {
  selectedInvoices.value = Object.entries(allocations.value)
    .filter(([, v]) => Number(v) > 0)
    .map(([name, val]) => ({ name, amount: Number(val) }))
  
  showAllocationModal.value = false
  nextFocus('mop')
}

function getDaysOutstanding(postDate) {
  const start = new Date(postDate)
  const today = new Date()
  const diff = today.getTime() - start.getTime()
  return Math.max(0, Math.floor(diff / (1000 * 60 * 60 * 24)))
}

function cycleMop(dir) {
  const idx = mops.indexOf(mop.value)
  const next = (idx + dir + mops.length) % mops.length
  selectMop(mops[next])
}

function selectMop(m) { mop.value = m; clearLedger() }

function openSearch() {
  showSearchModal.value = true
  nextTick(() => { searchModalRef.value?.closeSubForm(); searchModalRef.value?.focus() })
}

function pickParty(p) {
  party.value = p.name; partyName.value = p.label || p.customer_name || p.supplier_name
  if (p.type === 'Customer' || p.type === 'Supplier') receiptPartyType.value = p.type
  showSearchModal.value = false; fetchOutstandings()
  nextTick(() => amountInput.value?.focus())
}

async function fetchOutstandings() {
  if (!party.value) return
  loadingOutstandings.value = true
  try {
    outstandings.value = await frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
      party: party.value, party_type: activePartyType.value
    })
  } catch (e) { console.error(e) } finally { loadingOutstandings.value = false }
}

function removeInvoice(idx) {
  const name = selectedInvoices.value[idx].name
  delete allocations.value[name]
  selectedInvoices.value.splice(idx, 1)
}

async function saveEntry() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const payload = {
      payment_type: entryMode.value,
      party_type: activePartyType.value,
      party: party.value,
      date: date.value,
      amount: amount.value,
      mode_of_payment: mop.value,
      reference_no: referenceNo.value,
      remarks: remarks.value,
      references: selectedInvoices.value,
      ...(selectedLedger.value && { paid_to: selectedLedger.value })
    }

    if (userDefaults.value) {
      const specificMop = mop.value === 'Cash' ? userDefaults.value.cash :
                          mop.value === 'Card' ? userDefaults.value.card :
                          mop.value === 'UPI'  ? userDefaults.value.upi : userDefaults.value.bank;
      if (specificMop) payload.mode_of_payment = specificMop;
    }
    
    await frappePost('ssplbilling.api.ledgerentry_api.create_payment_entry', { data: payload })
    alert('Entry saved successfully!')
    resetForm()
    nextTick(() => partyInput.value?.focus())
  } catch (e) { alert('Failed to save: ' + e.message) } finally { saving.value = false }
}

function onLedgerInput() {
  ledgerDropdownOpen.value = true; ledgerHighlight.value = 0; clearTimeout(ledgerDebounceTimer)
  ledgerDebounceTimer = setTimeout(async () => {
    if (!ledgerQuery.value.trim()) { ledgerResults.value = []; ledgerDropdownOpen.value = false; return }
    ledgerResults.value = await searchAccounts(ledgerQuery.value); ledgerDropdownOpen.value = true
  }, 250)
}

function pickLedger(acct) {
  if (!acct) return; selectedLedger.value = acct.name; mop.value = ''; ledgerQuery.value = ''
  ledgerResults.value = []; ledgerDropdownOpen.value = false
}

function clearLedger() { selectedLedger.value = ''; ledgerQuery.value = ''; ledgerResults.value = []; ledgerDropdownOpen.value = false }
function closeLedgerDropdown() { ledgerDropdownOpen.value = false }

function fmt(val) { return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatDate(dateStr) { if (!dateStr) return ''; return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }

function handleKeydown(e) {
  if (e.key === 'F9') { e.preventDefault(); saveEntry() }
  else if (e.key === 'Escape') {
    if (showAllocationModal.value) { e.preventDefault(); showAllocationModal.value = false }
    else if (showLedgerWindow.value) { e.preventDefault(); showLedgerWindow.value = false }
    else if (showSearchModal.value) { e.preventDefault(); showSearchModal.value = false }
  }
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('keydown', handleKeydown); loadUserDefaults()
  if (route.query.mode) entryMode.value = route.query.mode
  nextTick(() => partyInput.value?.focus())
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #f1f5f9; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
