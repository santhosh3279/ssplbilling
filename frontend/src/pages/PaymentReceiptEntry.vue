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
        <button 
          @click="saveEntry" 
          :disabled="saving || !canSave"
          class="rounded-lg bg-blue-600 px-6 py-2 text-sm font-bold text-white shadow-lg transition-all hover:bg-blue-700 disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : 'Save Entry (F9)' }}
        </button>
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
            :class="selectedInvoice === inv.name ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-100 bg-white hover:border-blue-200'"
            @click="pickInvoice(inv)"
          >
            <div class="mb-2 flex items-start justify-between">
              <span class="font-mono text-xs font-bold text-blue-600">{{ inv.name }}</span>
              <span class="text-[10px] text-gray-400 font-bold uppercase">{{ inv.posting_date }}</span>
            </div>
            <div class="mb-1 text-[10px] font-bold uppercase text-gray-400">Outstanding</div>
            <div class="text-2xl font-black text-red-600">₹{{ (inv.outstanding_amount || 0).toLocaleString('en-IN') }}</div>
            <div class="mt-2 text-[10px] font-bold text-gray-400">Total: ₹{{ (inv.grand_total || 0).toLocaleString('en-IN') }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Entry Form -->
      <div class="flex-[3] border-l border-gray-200 bg-white p-6 shadow-xl">
        <div class="space-y-6">
          <!-- Party Search -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">
              {{ entryMode === 'Receive' ? 'Customer' : 'Supplier' }}
            </label>
            <div class="relative">
              <input 
                ref="partyInput"
                v-model="partyQuery"
                @input="onPartySearch"
                @keydown.down.prevent="cursorDown"
                @keydown.up.prevent="cursorUp"
                @keydown.enter.prevent="pickCurrentCursor"
                class="w-full rounded-lg border border-gray-300 px-4 py-3 text-lg font-bold outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                :placeholder="`Search ${entryMode === 'Receive' ? 'customer' : 'supplier'}...`"
              />
              <div v-if="partyResults.length" class="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-2xl overflow-hidden">
                <div 
                  v-for="(res, idx) in partyResults" 
                  :key="res.name"
                  @click="pickParty(res)"
                  class="cursor-pointer px-4 py-3 text-sm transition-colors"
                  :class="cursorIdx === idx ? 'bg-blue-500 text-white' : 'hover:bg-gray-50'"
                >
                  <div class="font-bold">{{ res.label }}</div>
                  <div class="text-[10px]" :class="cursorIdx === idx ? 'text-blue-100' : 'text-gray-400'">{{ res.name }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Date -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Date</label>
            <input 
              v-model="date" 
              type="date"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-base font-bold outline-none focus:border-blue-500"
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
            />
          </div>

          <!-- Mode of Payment -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Payment Mode</label>
            <div class="grid grid-cols-3 gap-2">
              <button 
                v-for="m in mops" 
                :key="m"
                @click="mop = m"
                class="rounded-lg border py-2 text-xs font-bold transition-all"
                :class="mop === m ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm' : 'border-gray-200 text-gray-500 hover:bg-gray-50'"
              >
                {{ m }}
              </button>
            </div>
          </div>

          <!-- Reference -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Reference No.</label>
            <input 
              v-model="referenceNo" 
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-bold outline-none focus:border-blue-500"
              placeholder="Cheque / UTR / Txn ID"
            />
          </div>

          <!-- Remarks -->
          <div>
            <label class="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-gray-400">Remarks</label>
            <textarea 
              v-model="remarks" 
              rows="2"
              class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-blue-500"
              placeholder="Internal notes..."
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const router = useRouter()
const route = useRoute()

// ─── Constants ───────────────────────────────────────────────────────────────
const modes = [
  { id: 'Receive', label: 'Receipt' },
  { id: 'Pay', label: 'Payment' }
]
const mops = ['Cash', 'UPI', 'Bank Transfer']

// ─── State ───────────────────────────────────────────────────────────────────
const entryMode = ref(route.query.mode || 'Receive') // 'Receive' or 'Pay'
const date = ref(new Date().toISOString().split('T')[0])
const party = ref('')
const partyName = ref('')
const partyQuery = ref('')
const partyResults = ref([])
const cursorIdx = ref(-1)
const amount = ref(0)
const mop = ref('Cash')
const referenceNo = ref('')
const remarks = ref('')
const selectedInvoice = ref('')

const outstandings = ref([])
const loadingOutstandings = ref(false)
const saving = ref(false)

const partyInput = ref(null)
const amountInput = ref(null)

// ─── Computed ────────────────────────────────────────────────────────────────
const canSave = computed(() => party.value && amount.value > 0)

// ─── Methods ─────────────────────────────────────────────────────────────────
function switchMode(m) {
  entryMode.value = m
  resetForm()
  nextTick(() => partyInput.value?.focus())
}

function resetForm() {
  party.value = ''
  partyName.value = ''
  partyQuery.value = ''
  partyResults.value = []
  cursorIdx.value = -1
  amount.value = 0
  referenceNo.value = ''
  remarks.value = ''
  selectedInvoice.value = ''
  outstandings.value = []
}

let partyTimer = null
function onPartySearch() {
  clearTimeout(partyTimer)
  partyTimer = setTimeout(async () => {
    if (partyQuery.value.length < 2) {
      partyResults.value = []
      return
    }
    try {
      partyResults.value = await frappeGet('ssplbilling.api.ledgerentry_api.search_parties', {
        query: partyQuery.value,
        party_type: entryMode.value === 'Receive' ? 'Customer' : 'Supplier'
      })
      cursorIdx.value = partyResults.value.length ? 0 : -1
    } catch (e) {
      console.error(e)
    }
  }, 300)
}

function pickParty(p) {
  party.value = p.name
  partyName.value = p.label
  partyQuery.value = p.label
  partyResults.value = []
  fetchOutstandings()
  nextTick(() => amountInput.value?.focus())
}

function cursorDown() {
  if (cursorIdx.value < partyResults.value.length - 1) cursorIdx.value++
}
function cursorUp() {
  if (cursorIdx.value > 0) cursorIdx.value--
}
function pickCurrentCursor() {
  if (cursorIdx.value >= 0 && partyResults.value[cursorIdx.value]) {
    pickParty(partyResults.value[cursorIdx.value])
  }
}

async function fetchOutstandings() {
  if (!party.value) return
  loadingOutstandings.value = true
  try {
    outstandings.value = await frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
      party: party.value,
      party_type: entryMode.value === 'Receive' ? 'Customer' : 'Supplier'
    })
  } catch (e) {
    console.error(e)
  } finally {
    loadingOutstandings.value = false
  }
}

function pickInvoice(inv) {
  selectedInvoice.value = inv.name
  amount.value = inv.outstanding_amount
  nextTick(() => amountInput.value?.focus())
}

async function saveEntry() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const payload = {
      payment_type: entryMode.value,
      party_type: entryMode.value === 'Receive' ? 'Customer' : 'Supplier',
      party: party.value,
      date: date.value,
      amount: amount.value,
      mode_of_payment: mop.value,
      reference_no: referenceNo.value,
      remarks: remarks.value,
      invoice_name: selectedInvoice.value
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

function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    saveEntry()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
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
  window.removeEventListener('keydown', handleKeydown)
})
</script>
