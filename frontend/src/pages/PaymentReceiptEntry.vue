<template>
  <div class="flex h-screen flex-col bg-gray-50">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <div class="flex items-center gap-4">
        <button @click="router.push('/')" class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100">
          &larr; Dashboard
        </button>
        <h1 class="text-xl font-bold text-gray-800">Payment & Receipt Entry</h1>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex rounded-lg bg-gray-100 p-1">
          <button 
            v-for="m in modes" 
            :key="m.id"
            @click="switchMode(m.id)"
            class="rounded-md px-4 py-1.5 text-sm font-bold transition-all"
            :class="entryMode === m.id ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ m.label }}
          </button>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Left: Outstanding Invoices -->
      <div class="flex-[7] flex flex-col overflow-hidden p-6">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-700">
            Outstanding {{ entryMode === 'Receive' ? 'Invoices' : 'Bills' }}
          </h2>
          <div v-if="partyName" class="rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-blue-600">
            {{ partyName }}
          </div>
        </div>

        <div v-if="!party" class="flex flex-1 items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-white text-gray-400">
          <div class="text-center">
            <div class="mb-2 text-4xl">👤</div>
            <p>Select a {{ entryMode === 'Receive' ? 'customer' : 'supplier' }} to view outstanding items</p>
          </div>
        </div>

        <div v-else-if="loadingOutstandings" class="flex flex-1 items-center justify-center">
          <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
        </div>

        <div v-else-if="!outstandings.length" class="flex flex-1 items-center justify-center rounded-2xl bg-white text-gray-400">
          <p>No outstanding {{ entryMode === 'Receive' ? 'invoices' : 'bills' }} found.</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="inv in outstandings" 
            :key="inv.name"
            class="group cursor-pointer rounded-xl border-2 p-4 transition-all"
            :class="isInvoiceSelected(inv.name) ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-100 bg-white hover:border-blue-200'"
            @click="pickInvoice(inv)"
          >
            <div class="mb-2 flex items-start justify-between">
              <span class="font-mono text-xs font-bold text-blue-600">{{ inv.name }}</span>
              <div v-if="isInvoiceSelected(inv.name)" class="rounded-full bg-blue-500 p-1 text-white">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
              <span v-else class="text-[10px] text-gray-400 font-bold uppercase">{{ inv.posting_date }}</span>
            </div>
            <div class="mb-1 text-[10px] font-bold uppercase text-gray-400">Outstanding</div>
            <div class="text-2xl font-black text-red-600">₹{{ (inv.outstanding_amount || 0).toLocaleString('en-IN') }}</div>
            <div class="mt-2 text-[10px] font-bold text-gray-400">Total: ₹{{ (inv.grand_total || 0).toLocaleString('en-IN') }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Entry Form -->
      <div class="flex-[3] border-l border-gray-200 bg-white p-6 shadow-xl overflow-y-auto">
        <div class="space-y-6">
          <!-- Party Search -->
          <div>
            <div class="mb-1.5 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <label class="block text-[10px] font-bold uppercase tracking-wider text-gray-400">
                  {{ activePartyType }}
                </label>
                <!-- Customer / Supplier toggle -->
                <div class="flex rounded border border-gray-200 overflow-hidden">
                  <button
                    v-for="pt in ['Customer', 'Supplier', 'Employee']"
                    :key="pt"
                    @click="setReceiptPartyType(pt)"
                    class="px-2 py-0.5 text-[10px] font-bold transition-all"
                    :class="receiptPartyType === pt ? 'bg-blue-600 text-white' : 'bg-white text-gray-400 hover:bg-gray-50'"
                  >
                    {{ pt }}
                  </button>
                </div>
              </div>
              <button
                v-if="party"
                @click="showLedgerWindow = true"
                class="text-[10px] font-bold text-blue-600 hover:underline"
              >
                VIEW LEDGER &rarr;
              </button>
            </div>
            <div
              ref="partyInput"
              class="w-full rounded-lg border border-gray-300 px-4 py-3 text-lg font-bold outline-none cursor-pointer hover:border-blue-400 transition-all focus:ring-4 focus:ring-blue-50"
              :class="party ? 'bg-blue-50 text-blue-800 border-blue-300' : 'text-gray-300 italic'"
              tabindex="0"
              @click="openSearch"
              @keydown.enter.prevent="party ? nextFocus('date') : openSearch()"
              @keydown.space.prevent="openSearch"
            >
              {{ partyName || `Select ${activePartyType.toLowerCase()}...` }}
            </div>
          </div>

          <!-- Date -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Date</label>
            <input
              ref="dateInput"
              v-model="date"
              type="date"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-base font-bold outline-none focus:border-blue-500"
              @keydown.enter.prevent="nextFocus('amount')"
            />
          </div>

          <!-- Amount -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Amount (₹)</label>
            <input
              ref="amountInput"
              v-model.number="amount"
              type="number"
              class="w-full rounded-lg border border-gray-300 px-4 py-3 text-3xl font-black text-blue-600 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
              placeholder="0.00"
              @keydown.enter.prevent="nextFocus('mop')"
            />
          </div>

          <!-- Mode of Payment -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">
              Payment Mode
              <span class="ml-1 font-normal normal-case text-gray-300">← → to switch</span>
            </label>
            <div
              ref="mopZoneRef"
              tabindex="0"
              class="grid grid-cols-4 gap-2 rounded-lg outline-none focus:ring-2 focus:ring-blue-200"
              @keydown.left.prevent="cycleMop(-1)"
              @keydown.right.prevent="cycleMop(1)"
              @keydown.enter.prevent="nextFocus('ref')"
            >
              <button
                v-for="m in mops"
                :key="m"
                @click="selectMop(m); mopZoneRef?.focus()"
                class="rounded-lg border py-1.5 text-xs font-bold transition-all"
                :class="mop === m && !selectedLedger ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm' : 'border-gray-200 text-gray-500 hover:bg-gray-50'"
              >
                {{ m }}
              </button>
            </div>
          </div>

          <!-- Linked References -->
          <div v-if="selectedInvoices.length" class="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
            <label class="mb-3 block text-[10px] font-bold uppercase tracking-wider text-blue-400">Linked References</label>
            <div class="space-y-2">
              <div 
                v-for="(link, idx) in selectedInvoices" 
                :key="link.name"
                class="flex items-center justify-between rounded-lg bg-white p-2.5 shadow-sm border border-blue-100"
              >
                <div class="flex flex-col">
                  <span class="font-mono text-xs font-bold text-gray-700">{{ link.name }}</span>
                  <span class="text-[10px] font-bold text-blue-600">₹{{ link.amount.toLocaleString('en-IN') }}</span>
                </div>
                <button @click="removeInvoice(idx)" class="text-gray-300 hover:text-red-500">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="mt-3 flex justify-between border-t border-blue-100 pt-2 text-xs font-bold text-blue-700 uppercase">
              <span>Total Linked</span>
              <span>₹{{ amount.toLocaleString('en-IN') }}</span>
            </div>
          </div>

          <!-- Ledger Override -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">
              Ledger <span class="normal-case text-gray-300">(optional override)</span>
            </label>
            <div class="relative">
              <input
                v-model="ledgerQuery"
                @input="onLedgerInput"
                @keydown.escape="closeLedgerDropdown"
                @keydown.down.prevent="ledgerHighlight = Math.min(ledgerHighlight + 1, ledgerResults.length - 1)"
                @keydown.up.prevent="ledgerHighlight = Math.max(ledgerHighlight - 1, 0)"
                @keydown.enter.prevent="pickLedger(ledgerResults[ledgerHighlight])"
                class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-bold outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                :placeholder="selectedLedger ? selectedLedger : 'Search account name...'"
              />
              <button
                v-if="selectedLedger"
                @click="clearLedger"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 hover:text-red-400"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
              <div
                v-if="ledgerResults.length && ledgerDropdownOpen"
                class="absolute z-30 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-xl overflow-hidden"
              >
                <div
                  v-for="(acct, idx) in ledgerResults"
                  :key="acct.name"
                  @click="pickLedger(acct)"
                  @mouseenter="ledgerHighlight = idx"
                  class="cursor-pointer px-4 py-2.5 text-sm transition-colors"
                  :class="idx === ledgerHighlight ? 'bg-blue-50 text-blue-800' : 'text-gray-700 hover:bg-gray-50'"
                >
                  <div class="font-bold">{{ acct.account_name }}</div>
                  <div class="text-[10px] text-gray-400">{{ acct.name }}</div>
                </div>
              </div>
            </div>
            <div v-if="selectedLedger" class="mt-1.5 rounded-md bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700">
              {{ selectedLedger }}
            </div>
          </div>

          <!-- Reference -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Reference No.</label>
            <input
              ref="refInput"
              v-model="referenceNo"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-bold outline-none focus:border-blue-500"
              placeholder="Cheque / UTR / Txn ID"
              @keydown.enter.prevent="nextFocus('remarks')"
            />
          </div>

          <!-- Remarks -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Remarks</label>
            <textarea
              ref="remarksInput"
              v-model="remarks"
              rows="2"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-blue-500"
              placeholder="Internal notes..."
              @keydown.enter.prevent="saveEntry"
            ></textarea>
          </div>

          <!-- Save Button -->
          <button 
            @click="saveEntry" 
            :disabled="saving || !canSave"
            class="w-full rounded-lg bg-blue-600 py-3 text-base font-bold text-white shadow-lg transition-all hover:bg-blue-700 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save Entry (F9)' }}
          </button>
        </div>
      </div>
    </div>

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

// ─── Constants ───────────────────────────────────────────────────────────────
const modes = [
  { id: 'Receive', label: 'Receipt' },
  { id: 'Pay', label: 'Payment' }
]
const mops = ['Cash', 'Card', 'Bank', 'UPI']

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ─── State ───────────────────────────────────────────────────────────────────
const entryMode = ref(route.query.mode || 'Receive') // 'Receive' or 'Pay'
const date = ref(getTodayIST())
const party = ref('')
const partyName = ref('')
const showSearchModal = ref(false)
const searchModalRef = ref(null)
const showLedgerWindow = ref(false)
const amount = ref(0)
const mop = ref('Cash')
const referenceNo = ref('')
const remarks = ref('')
const selectedInvoices = ref([]) // Array of { name, amount }
const userDefaults = ref(null)

const outstandings = ref([])
const loadingOutstandings = ref(false)
const saving = ref(false)

const partyInput  = ref(null)
const dateInput   = ref(null)
const amountInput = ref(null)
const mopZoneRef  = ref(null)
const refInput    = ref(null)
const remarksInput = ref(null)

// ─── Receipt party type (Customer or Supplier, selectable in Receive mode) ────
const receiptPartyType = ref(route.query.mode === 'Pay' ? 'Supplier' : 'Customer')

const activePartyType = computed(() => receiptPartyType.value)

function setReceiptPartyType(pt) {
  if (receiptPartyType.value === pt) return
  receiptPartyType.value = pt
  // Clear party selection when type changes
  party.value = ''
  partyName.value = ''
  outstandings.value = []
  selectedInvoices.value = []
  amount.value = 0
  nextTick(() => partyInput.value?.focus())
}

// ─── Ledger override ──────────────────────────────────────────────────────────
const ledgerQuery = ref('')
const ledgerResults = ref([])
const ledgerDropdownOpen = ref(false)
const ledgerHighlight = ref(0)
const selectedLedger = ref('')  // account name (full)
let ledgerDebounceTimer = null

// ─── Computed ────────────────────────────────────────────────────────────────
const canSave = computed(() => party.value && amount.value > 0)

// ─── Methods ─────────────────────────────────────────────────────────────────
function switchMode(m) {
  entryMode.value = m
  receiptPartyType.value = m === 'Pay' ? 'Supplier' : 'Customer'
  resetForm()
  nextTick(() => partyInput.value?.focus())
}

function resetForm() {
  party.value = ''
  partyName.value = ''
  showSearchModal.value = false
  amount.value = 0
  referenceNo.value = ''
  remarks.value = ''
  selectedInvoices.value = []
  outstandings.value = []
  selectedLedger.value = ''
  ledgerQuery.value = ''
  ledgerResults.value = []
}

async function loadUserDefaults() {
  try {
    const settings = await fetchDashboardSettings()
    if (settings?.user_defaults) {
      userDefaults.value = settings.user_defaults
    }
  } catch (e) {
    console.warn('[PaymentEntry] Failed to load user defaults from backend:', e)
  }
}

// ─── Keyboard navigation ──────────────────────────────────────────────────────
const focusMap = {
  date:    () => dateInput.value?.focus(),
  amount:  () => amountInput.value?.focus(),
  mop:     () => nextTick(() => mopZoneRef.value?.focus()),
  ref:     () => refInput.value?.focus(),
  remarks: () => remarksInput.value?.focus(),
}

function nextFocus(target) {
  focusMap[target]?.()
}

function cycleMop(dir) {
  const idx = mops.indexOf(mop.value)
  const next = (idx + dir + mops.length) % mops.length
  selectMop(mops[next])
}

function selectMop(m) {
  mop.value = m
  clearLedger()
}

function openSearch() {
  showSearchModal.value = true
  nextTick(() => {
    searchModalRef.value?.closeSubForm()
    searchModalRef.value?.focus()
  })
}

function pickParty(p) {
  party.value = p.name
  partyName.value = p.label || p.customer_name || p.supplier_name
  if (p.type === 'Customer' || p.type === 'Supplier') {
    receiptPartyType.value = p.type
  }
  showSearchModal.value = false
  fetchOutstandings()
  nextTick(() => amountInput.value?.focus())
}

async function fetchOutstandings() {
  if (!party.value) return
  loadingOutstandings.value = true
  try {
    outstandings.value = await frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
      party: party.value,
      party_type: activePartyType.value
    })
  } catch (e) {
    console.error(e)
  } finally {
    loadingOutstandings.value = false
  }
}

function isInvoiceSelected(name) {
  return selectedInvoices.value.some(i => i.name === name)
}

function pickInvoice(inv) {
  const existingIdx = selectedInvoices.value.findIndex(i => i.name === inv.name)
  if (existingIdx > -1) {
    selectedInvoices.value.splice(existingIdx, 1)
  } else {
    selectedInvoices.value.push({
      name: inv.name,
      amount: inv.outstanding_amount
    })
  }
  
  // Auto-calculate total amount based on selected invoices
  amount.value = selectedInvoices.value.reduce((sum, item) => sum + item.amount, 0)
  nextTick(() => amountInput.value?.focus())
}

function removeInvoice(idx) {
  selectedInvoices.value.splice(idx, 1)
  amount.value = selectedInvoices.value.reduce((sum, item) => sum + item.amount, 0)
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

    // Resolve specific Mode of Payment from user defaults
    if (userDefaults.value) {
      const specificMop = mop.value === 'Cash' ? userDefaults.value.cash :
                          mop.value === 'Card' ? userDefaults.value.card :
                          mop.value === 'UPI'  ? userDefaults.value.upi :
                          userDefaults.value.bank;
      
      if (specificMop) {
        payload.mode_of_payment = specificMop;
      }
    }
    
    await frappePost('ssplbilling.api.ledgerentry_api.create_payment_entry', { data: payload })
    alert('Entry saved successfully!')
    resetForm()
    nextTick(() => partyInput.value?.focus())
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    saving.value = false
  }
}

function onLedgerInput() {
  ledgerDropdownOpen.value = true
  ledgerHighlight.value = 0
  clearTimeout(ledgerDebounceTimer)
  ledgerDebounceTimer = setTimeout(async () => {
    if (!ledgerQuery.value.trim()) {
      ledgerResults.value = []
      ledgerDropdownOpen.value = false
      return
    }
    ledgerResults.value = await searchAccounts(ledgerQuery.value)
    ledgerDropdownOpen.value = true
  }, 250)
}

function pickLedger(acct) {
  if (!acct) return
  selectedLedger.value = acct.name
  mop.value = ''
  ledgerQuery.value = ''
  ledgerResults.value = []
  ledgerDropdownOpen.value = false
}

function clearLedger() {
  selectedLedger.value = ''
  ledgerQuery.value = ''
  ledgerResults.value = []
  ledgerDropdownOpen.value = false
}

function closeLedgerDropdown() {
  ledgerDropdownOpen.value = false
}

function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    saveEntry()
  } else if (e.key === 'Escape') {
    if (showLedgerWindow.value) {
      e.preventDefault()
      showLedgerWindow.value = false
    } else if (showSearchModal.value) {
      e.preventDefault()
      showSearchModal.value = false
    }
  }
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('keydown', handleKeydown)
  loadUserDefaults()
  if (route.query.mode) {
    entryMode.value = route.query.mode
  }
  nextTick(() => partyInput.value?.focus())
})

watch(() => route.query.mode, (newMode) => {
  if (newMode && newMode !== entryMode.value) {
    switchMode(newMode)
  }
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.removeEventListener('keydown', handleKeydown)
})
</script>
