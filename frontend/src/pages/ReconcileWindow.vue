<template>
  <div class="fixed inset-0 z-50 flex flex-col bg-slate-900">

    <!-- Header -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center gap-3">
        <span class="text-lg font-bold text-white">Payment Reconciliation</span>
        <span
          v-if="party"
          class="rounded-full bg-violet-700/30 px-3 py-0.5 text-xs font-semibold text-violet-300"
        >{{ partyType }}: {{ party }}</span>
      </div>
      <button @click="$emit('close')" class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white">
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </header>

    <!-- Search bar -->
    <div class="border-b border-slate-700 bg-slate-800/60 px-6 py-3">
      <div class="flex items-center gap-3">
        <!-- Party type -->
        <div class="flex rounded-lg border border-slate-600 overflow-hidden text-sm">
          <button
            v-for="pt in partyTypes"
            :key="pt"
            @click="setPartyType(pt)"
            class="px-3 py-1.5 font-medium transition-colors"
            :class="partyType === pt
              ? 'bg-violet-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'"
          >{{ pt }}</button>
        </div>

        <!-- Party search -->
        <div class="relative flex-1 max-w-sm">
          <input
            ref="partyInput"
            v-model="partyQuery"
            @input="onPartyInput"
            @keydown.down.prevent="partyListIdx = Math.min(partyListIdx + 1, partyOptions.length - 1)"
            @keydown.up.prevent="partyListIdx = Math.max(partyListIdx - 1, 0)"
            @keydown.enter.prevent="selectParty(partyOptions[partyListIdx])"
            @keydown.esc="partyOptions = []"
            placeholder="Search party..."
            class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-sm text-white placeholder-slate-400 focus:border-violet-500 focus:outline-none"
          />
          <ul
            v-if="partyOptions.length"
            class="absolute left-0 top-full z-20 mt-1 max-h-52 w-full overflow-y-auto rounded-lg border border-slate-600 bg-slate-800 shadow-xl"
          >
            <li
              v-for="(opt, i) in partyOptions"
              :key="opt.name"
              @click="selectParty(opt)"
              class="cursor-pointer px-3 py-2 text-sm hover:bg-slate-700"
              :class="i === partyListIdx ? 'bg-slate-700 text-white' : 'text-slate-300'"
            >
              <div class="font-medium">{{ opt.customer_name || opt.supplier_name || opt.employee_name || opt.name }}</div>
              <div class="text-[10px] text-slate-500">{{ opt.name }}</div>
            </li>
          </ul>
        </div>

        <button
          @click="fetchData"
          :disabled="!party || loading"
          class="rounded-lg bg-violet-600 px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-40 hover:bg-violet-500 transition-colors"
        >{{ loading ? 'Loading…' : 'Fetch' }}</button>

        <span v-if="error" class="text-xs text-red-400">{{ error }}</span>
      </div>
    </div>

    <!-- Body -->
    <div class="flex flex-1 overflow-hidden">

      <!-- LEFT: Unlinked Payments -->
      <div class="flex w-[340px] shrink-0 flex-col border-r border-slate-700">
        <div class="border-b border-slate-700 bg-slate-800/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Unlinked Payments
          <span v-if="unlinkedTotal > 0" class="ml-1.5 text-violet-400">₹{{ fmt(unlinkedTotal) }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3 space-y-1.5">
          <template v-if="!fetched">
            <p class="py-8 text-center text-xs text-slate-500">Search a party and click Fetch</p>
          </template>
          <template v-else-if="allUnlinked.length === 0">
            <p class="py-8 text-center text-xs text-slate-500">No unlinked entries</p>
          </template>

          <!-- Payment Entries -->
          <div v-if="unlinkedData.payment_entries.length" class="mb-2">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-slate-500 px-1">Payment Entries</div>
            <div
              v-for="pe in unlinkedData.payment_entries"
              :key="pe.name"
              @click="selectPayment({ type: 'Payment Entry', ...pe, available: remainingOnPayment(pe.name, null) })"
              class="cursor-pointer rounded-lg border px-3 py-2 text-xs transition-all"
              :class="activePayment?.name === pe.name
                ? 'border-violet-500 bg-violet-900/30 text-white'
                : 'border-slate-700 bg-slate-800 text-slate-300 hover:border-slate-500 hover:bg-slate-700'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold">{{ pe.name }}</span>
                <span class="font-mono font-bold text-green-400">₹{{ fmt(remainingOnPayment(pe.name, null)) }}</span>
              </div>
              <div class="mt-0.5 flex items-center justify-between text-[10px] text-slate-500">
                <span>{{ pe.posting_date }}</span>
                <span>{{ pe.mode_of_payment }}</span>
              </div>
            </div>
          </div>

          <!-- Journal Entries -->
          <div v-if="unlinkedData.journal_entries.length">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-slate-500 px-1">Journal Entries</div>
            <div
              v-for="je in unlinkedData.journal_entries"
              :key="je.reference_row"
              @click="selectPayment({ type: 'Journal Entry', name: je.name, reference_row: je.reference_row, unallocated_amount: je.unallocated_amount, posting_date: je.posting_date, remarks: je.remarks, available: remainingOnPayment(je.name, je.reference_row) })"
              class="cursor-pointer rounded-lg border px-3 py-2 text-xs transition-all"
              :class="activePayment?.reference_row === je.reference_row
                ? 'border-violet-500 bg-violet-900/30 text-white'
                : 'border-slate-700 bg-slate-800 text-slate-300 hover:border-slate-500 hover:bg-slate-700'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold">{{ je.name }}</span>
                <span class="font-mono font-bold text-green-400">₹{{ fmt(remainingOnPayment(je.name, je.reference_row)) }}</span>
              </div>
              <div class="mt-0.5 flex items-center justify-between text-[10px] text-slate-500">
                <span>{{ je.posting_date }}</span>
                <span>{{ je.remarks || je.reference_no }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Active payment indicator -->
        <div v-if="activePayment" class="border-t border-violet-700/40 bg-violet-900/20 px-4 py-2 text-xs">
          <div class="font-semibold text-violet-300">Selected: {{ activePayment.name }}</div>
          <div class="text-[10px] text-violet-400">
            Available: ₹{{ fmt(activePayment.available) }} — click invoices to allocate
          </div>
        </div>
      </div>

      <!-- CENTRE: Outstanding Invoices -->
      <div class="flex flex-1 flex-col border-r border-slate-700">
        <div class="border-b border-slate-700 bg-slate-800/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Outstanding {{ outstandingDocType }}s
          <span v-if="outstandingTotal > 0" class="ml-1.5 text-orange-400">₹{{ fmt(outstandingTotal) }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3">
          <template v-if="!fetched">
            <p class="py-8 text-center text-xs text-slate-500">Search a party and click Fetch</p>
          </template>
          <template v-else-if="outstandingData.docs.length === 0">
            <p class="py-8 text-center text-xs text-slate-500">No outstanding documents</p>
          </template>
          <table v-else class="w-full text-xs">
            <thead>
              <tr class="border-b border-slate-700 text-[10px] text-slate-400">
                <th class="pb-2 text-left font-normal">Document</th>
                <th class="pb-2 text-left font-normal">Date</th>
                <th class="pb-2 text-right font-normal">Grand Total</th>
                <th class="pb-2 text-right font-normal">Outstanding</th>
                <th class="pb-2 text-right font-normal">Allocating</th>
                <th class="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="doc in outstandingData.docs"
                :key="doc.name"
                class="border-b border-slate-700/50 hover:bg-slate-800/50"
              >
                <td class="py-1.5 font-mono text-slate-200">{{ doc.name }}</td>
                <td class="py-1.5 text-slate-400">{{ doc.posting_date }}</td>
                <td class="py-1.5 text-right font-mono text-slate-300">₹{{ fmt(doc.grand_total) }}</td>
                <td class="py-1.5 text-right font-mono text-orange-400">₹{{ fmt(remainingOutstanding(doc.name)) }}</td>
                <td class="py-1.5 text-right font-mono text-violet-400">
                  <span v-if="allocatedToDoc(doc.name) > 0">₹{{ fmt(allocatedToDoc(doc.name)) }}</span>
                  <span v-else class="text-slate-600">—</span>
                </td>
                <td class="py-1.5 pl-2">
                  <button
                    v-if="activePayment && remainingOutstanding(doc.name) > 0.005 && activePayment.available > 0.005"
                    @click="addAllocation(doc)"
                    class="rounded bg-violet-700 px-2 py-0.5 text-[10px] font-semibold text-white hover:bg-violet-600"
                  >+ Add</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- RIGHT: Allocations -->
      <div class="flex w-[360px] shrink-0 flex-col">
        <div class="border-b border-slate-700 bg-slate-800/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Allocation Preview
          <span v-if="allocations.length" class="ml-1.5 text-violet-400">{{ allocations.length }} row{{ allocations.length > 1 ? 's' : '' }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3">
          <template v-if="allocations.length === 0">
            <p class="py-8 text-center text-xs text-slate-500">
              Select a payment on the left, then click "+ Add" on an invoice
            </p>
          </template>
          <div v-else class="space-y-1.5">
            <div
              v-for="(alloc, i) in allocations"
              :key="i"
              class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs"
            >
              <div class="mb-1.5 flex items-center justify-between">
                <div>
                  <span class="text-[9px] text-slate-500">{{ alloc.payment_type }}</span>
                  <div class="font-mono font-semibold text-violet-300">{{ alloc.payment_name }}</div>
                </div>
                <button @click="removeAllocation(i)" class="text-slate-500 hover:text-red-400">✕</button>
              </div>
              <div class="mb-1.5">
                <span class="text-[9px] text-slate-500">{{ alloc.invoice_type }}</span>
                <div class="font-mono text-slate-200">{{ alloc.invoice_name }}</div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[10px] text-slate-400 shrink-0">Amount ₹</span>
                <input
                  v-model.number="alloc.amount"
                  type="number"
                  min="0.01"
                  :max="alloc.unreconciled_amount"
                  @change="clampAlloc(alloc)"
                  class="w-full rounded border border-slate-600 bg-slate-700 px-2 py-0.5 text-right font-mono text-sm text-white focus:border-violet-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Footer: total + post button -->
        <div class="border-t border-slate-700 bg-slate-800/60 p-4 space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-slate-400">Total Reconciling</span>
            <span class="font-mono font-bold text-violet-300">₹{{ fmt(totalAllocating) }}</span>
          </div>

          <div v-if="postError" class="rounded bg-red-900/30 px-3 py-2 text-xs text-red-400">{{ postError }}</div>
          <div v-if="postSuccess" class="rounded bg-green-900/30 px-3 py-2 text-xs text-green-400">{{ postSuccess }}</div>

          <button
            @click="postReconcile"
            :disabled="allocations.length === 0 || posting"
            class="w-full rounded-lg bg-violet-600 py-2.5 text-sm font-bold text-white disabled:opacity-40 hover:bg-violet-500 transition-colors"
          >{{ posting ? 'Posting…' : 'Post Reconciliation' }}</button>

          <button
            v-if="allocations.length"
            @click="allocations = []"
            class="w-full rounded-lg border border-slate-600 py-1.5 text-xs text-slate-400 hover:bg-slate-700"
          >Clear All</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { searchCustomers } from '../customersearch.js'
import { searchSuppliers, searchEmployees, getUnlinkedEntries, getOutstandingDocs, postReconciliation } from '../api.js'

const emit = defineEmits(['close'])

// ── Party selector ────────────────────────────────────────────────────
const partyTypes = ['Customer', 'Supplier', 'Employee']
const partyType = ref('Customer')
const party = ref('')
const partyQuery = ref('')
const partyOptions = ref([])
const partyListIdx = ref(0)
const partyInput = ref(null)

function setPartyType(pt) {
  partyType.value = pt
  party.value = ''
  partyQuery.value = ''
  partyOptions.value = []
  reset()
}

let partyTimer = null
function onPartyInput() {
  clearTimeout(partyTimer)
  partyTimer = setTimeout(searchParty, 250)
}

async function searchParty() {
  const q = partyQuery.value.trim()
  partyListIdx.value = 0
  if (!q) { partyOptions.value = []; return }
  if (partyType.value === 'Customer') partyOptions.value = await searchCustomers(q)
  else if (partyType.value === 'Supplier') partyOptions.value = await searchSuppliers(q)
  else partyOptions.value = await searchEmployees(q)
}

function selectParty(opt) {
  if (!opt) return
  party.value = opt.name
  partyQuery.value = opt.customer_name || opt.supplier_name || opt.employee_name || opt.name
  partyOptions.value = []
  reset()
  fetchData()
}

// ── Data fetch ────────────────────────────────────────────────────────
const loading = ref(false)
const fetched = ref(false)
const error = ref('')
const unlinkedData = ref({ payment_entries: [], journal_entries: [] })
const outstandingData = ref({ doc_type: 'Sales Invoice', docs: [] })

const allUnlinked = computed(() => [
  ...unlinkedData.value.payment_entries,
  ...unlinkedData.value.journal_entries,
])
const unlinkedTotal = computed(() =>
  unlinkedData.value.payment_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0) +
  unlinkedData.value.journal_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0)
)
const outstandingDocType = computed(() => outstandingData.value.doc_type || '')
const outstandingTotal = computed(() =>
  outstandingData.value.docs.reduce((s, r) => s + parseFloat(r.outstanding_amount || 0), 0)
)

async function fetchData() {
  if (!party.value) return
  loading.value = true
  error.value = ''
  try {
    const [unlinked, outstanding] = await Promise.all([
      getUnlinkedEntries(partyType.value, party.value),
      getOutstandingDocs(partyType.value, party.value),
    ])
    unlinkedData.value = unlinked
    outstandingData.value = outstanding
    fetched.value = true
    allocations.value = []
    activePayment.value = null
  } catch (e) {
    error.value = e.message || 'Fetch failed'
  } finally {
    loading.value = false
  }
}

// ── Allocation logic ──────────────────────────────────────────────────
const activePayment = ref(null)   // { type, name, reference_row?, available }
const allocations = ref([])       // array of allocation rows

function selectPayment(p) {
  activePayment.value = p
}

/** Amount already allocated from a given payment (key = name + reference_row) */
function usedOnPayment(name, referenceRow) {
  return allocations.value
    .filter(a => a.payment_name === name && (a.reference_row || null) === (referenceRow || null))
    .reduce((s, a) => s + parseFloat(a.amount || 0), 0)
}

function remainingOnPayment(name, referenceRow) {
  const pe = unlinkedData.value.payment_entries.find(p => p.name === name)
  const je = unlinkedData.value.journal_entries.find(j => j.name === name && j.reference_row === referenceRow)
  const available = pe ? parseFloat(pe.unallocated_amount || 0) : je ? parseFloat(je.unallocated_amount || 0) : 0
  return Math.max(0, available - usedOnPayment(name, referenceRow))
}

function allocatedToDoc(invoiceName) {
  return allocations.value
    .filter(a => a.invoice_name === invoiceName)
    .reduce((s, a) => s + parseFloat(a.amount || 0), 0)
}

function remainingOutstanding(invoiceName) {
  const doc = outstandingData.value.docs.find(d => d.name === invoiceName)
  if (!doc) return 0
  return Math.max(0, parseFloat(doc.outstanding_amount || 0) - allocatedToDoc(invoiceName))
}

function addAllocation(doc) {
  if (!activePayment.value) return
  const ap = activePayment.value
  const payAvail = remainingOnPayment(ap.name, ap.reference_row || null)
  const docAvail = remainingOutstanding(doc.name)
  const amount = Math.min(payAvail, docAvail)
  if (amount < 0.005) return

  allocations.value.push({
    payment_type: ap.type,
    payment_name: ap.name,
    reference_row: ap.reference_row || null,
    invoice_type: outstandingDocType.value,
    invoice_name: doc.name,
    amount: parseFloat(amount.toFixed(2)),
    unreconciled_amount: payAvail,
  })

  // Update the active payment's available amount
  activePayment.value = { ...ap, available: remainingOnPayment(ap.name, ap.reference_row || null) }
}

function removeAllocation(i) {
  allocations.value.splice(i, 1)
  if (activePayment.value) {
    const ap = activePayment.value
    activePayment.value = { ...ap, available: remainingOnPayment(ap.name, ap.reference_row || null) }
  }
}

function clampAlloc(alloc) {
  const max = alloc.unreconciled_amount
  if (alloc.amount > max) alloc.amount = parseFloat(max.toFixed(2))
  if (alloc.amount < 0.01) alloc.amount = 0.01
}

const totalAllocating = computed(() =>
  allocations.value.reduce((s, a) => s + parseFloat(a.amount || 0), 0)
)

// ── Post ──────────────────────────────────────────────────────────────
const posting = ref(false)
const postError = ref('')
const postSuccess = ref('')

async function postReconcile() {
  if (!allocations.value.length) return
  posting.value = true
  postError.value = ''
  postSuccess.value = ''
  try {
    const res = await postReconciliation(partyType.value, party.value, allocations.value)
    postSuccess.value = `Reconciled ${res.reconciled} allocation${res.reconciled !== 1 ? 's' : ''} successfully.`
    allocations.value = []
    activePayment.value = null
    setTimeout(() => fetchData(), 800)
  } catch (e) {
    postError.value = e.message || 'Reconciliation failed'
  } finally {
    posting.value = false
  }
}

// ── Helpers ───────────────────────────────────────────────────────────
function fmt(n) {
  return parseFloat(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function reset() {
  fetched.value = false
  unlinkedData.value = { payment_entries: [], journal_entries: [] }
  outstandingData.value = { doc_type: 'Sales Invoice', docs: [] }
  allocations.value = []
  activePayment.value = null
  postError.value = ''
  postSuccess.value = ''
  error.value = ''
}
</script>
