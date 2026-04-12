<template>
  <div class="fixed inset-0 z-50 flex flex-col bg-[var(--color-bg)]">

    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-3">
        <span class="text-lg font-bold text-[var(--color-text-on-highlight)]">Payment Reconciliation</span>
        <span
          v-if="party"
          class="rounded-full bg-[var(--color-info)]/30 px-3 py-0.5 text-xs font-semibold text-[var(--color-info)]"
        >{{ partyType }}: {{ party }}</span>
      </div>
      <button @click="$emit('close')" class="rounded-lg p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text-on-highlight)]">
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </header>

    <!-- Search bar -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/60 px-6 py-3">
      <div class="flex items-center gap-3">
        <!-- Party type toggle -->
        <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden text-sm">
          <button
            v-for="pt in partyTypes"
            :key="pt"
            @click="setPartyType(pt)"
            class="px-3 py-1.5 font-medium transition-colors"
            :class="partyType === pt
              ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
              : 'bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]'"
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
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm text-[var(--color-text-on-highlight)] placeholder-slate-400 focus:border-[var(--color-info)] focus:outline-none"
          />
          <ul
            v-if="partyOptions.length"
            class="absolute left-0 top-full z-20 mt-1 max-h-52 w-full overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl"
          >
            <li
              v-for="(opt, i) in partyOptions"
              :key="opt.name"
              @click="selectParty(opt)"
              class="cursor-pointer px-3 py-2 text-sm hover:bg-[var(--color-surface-raised)]"
              :class="i === partyListIdx ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)]'"
            >
              <div class="font-medium">{{ opt.customer_name || opt.supplier_name || opt.employee_name || opt.name }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)]">{{ opt.name }}</div>
            </li>
          </ul>
        </div>

        <button
          @click="fetchData"
          :disabled="!party || loading"
          class="rounded-lg bg-[var(--color-info)] px-4 py-1.5 text-sm font-semibold text-[var(--color-text-on-highlight)] disabled:opacity-40 hover:bg-[var(--color-info)] transition-colors"
        >{{ loading ? 'Loading…' : 'Fetch' }}</button>

        <span v-if="error" class="text-xs text-[var(--color-danger)]">{{ error }}</span>
      </div>
    </div>

    <!-- Body -->
    <div class="flex flex-1 overflow-hidden">

      <!-- COLUMN 1: Unlinked Payments -->
      <div class="flex w-[280px] shrink-0 flex-col border-r border-[var(--color-border)]">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Unlinked Payments
          <span v-if="unlinkedTotal > 0" class="ml-1.5 text-[var(--color-info)]">₹{{ fmt(unlinkedTotal) }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3 space-y-1.5">
          <template v-if="!fetched">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">Search a party and click Fetch</p>
          </template>
          <template v-else-if="allUnlinked.length === 0">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">No unlinked entries</p>
          </template>

          <div v-if="unlinkedData.payment_entries.length" class="mb-2">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] px-1">Payment Entries</div>
            <div
              v-for="pe in unlinkedData.payment_entries"
              :key="pe.name"
              @click="selectPayment({ type: 'Payment Entry', ...pe })"
              class="cursor-pointer rounded-lg border px-3 py-2 text-xs transition-all"
              :class="activePayment?.name === pe.name && !activePayment?.reference_row
                ? 'border-[var(--color-info)] bg-[var(--color-info)]/30 text-[var(--color-text-on-highlight)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold">{{ pe.name }}</span>
                <span class="font-mono font-bold text-[var(--color-success)]">₹{{ fmt(leftRemaining(pe.name, null)) }}</span>
              </div>
              <div class="mt-0.5 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
                <span>{{ pe.posting_date }}</span>
                <span>{{ pe.mode_of_payment }}</span>
              </div>
            </div>
          </div>

          <div v-if="unlinkedData.journal_entries.length">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] px-1">Journal Entries</div>
            <div
              v-for="je in unlinkedData.journal_entries"
              :key="je.reference_row"
              @click="selectPayment({ type: 'Journal Entry', name: je.name, reference_row: je.reference_row, unallocated_amount: je.unallocated_amount, posting_date: je.posting_date, remarks: je.remarks })"
              class="cursor-pointer rounded-lg border px-3 py-2 text-xs transition-all"
              :class="activePayment?.reference_row === je.reference_row
                ? 'border-[var(--color-info)] bg-[var(--color-info)]/30 text-[var(--color-text-on-highlight)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold">{{ je.name }}</span>
                <span class="font-mono font-bold text-[var(--color-success)]">₹{{ fmt(leftRemaining(je.name, je.reference_row)) }}</span>
              </div>
              <div class="mt-0.5 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
                <span>{{ je.posting_date }}</span>
                <span>{{ je.remarks || je.reference_no }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Active payment indicator -->
        <div v-if="activePayment" class="border-t border-[var(--color-info)]/40 bg-[var(--color-info)]/20 px-4 py-2 text-xs">
          <div class="font-semibold text-[var(--color-info)] truncate">Selected: {{ activePayment.name }}</div>
          <div class="text-[10px] text-[var(--color-info)]">
            Available: ₹{{ fmt(leftRemainingForActive) }}
          </div>
        </div>
      </div>

      <!-- COLUMN 2: Unlinked Receipts (Invoices) -->
      <div class="flex w-[320px] shrink-0 flex-col border-r border-[var(--color-border)]">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Unlinked Receipts
          <span v-if="outstandingTotal > 0" class="ml-1.5 text-[var(--color-supplier)]">₹{{ fmt(outstandingTotal) }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3">
          <template v-if="!fetched">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">Search a party and click Fetch</p>
          </template>
          <template v-else-if="outstandingData.docs.length === 0">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">No outstanding invoices</p>
          </template>
          <div v-else class="space-y-2">
            <div
              v-for="doc in outstandingData.docs"
              :key="doc.name"
              @click="activePayment && invoiceRemaining(doc.name) > 0.005 ? addInvoiceAllocation(doc) : null"
              class="rounded-lg border px-3 py-2 text-xs transition-all"
              :class="[
                activePayment && invoiceRemaining(doc.name) > 0.005 && leftRemainingForActive > 0.005
                  ? 'cursor-pointer border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-info)] hover:bg-[var(--color-surface-raised)]'
                  : 'border-[var(--color-border)] bg-[var(--color-surface)]/50 opacity-80',
                allocatedToInvoice(doc.name) > 0 ? 'ring-1 ring-violet-500/50' : ''
              ]"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold text-[var(--color-text)]">{{ doc.name }}</span>
                <span class="font-mono font-bold text-[var(--color-supplier)]">₹{{ fmt(invoiceRemaining(doc.name)) }}</span>
              </div>
              <div class="mt-0.5 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
                <span>{{ doc.posting_date }}</span>
                <span v-if="allocatedToInvoice(doc.name) > 0" class="font-bold text-[var(--color-info)]">Linked: ₹{{ fmt(allocatedToInvoice(doc.name)) }}</span>
                <span v-else class="italic">Outstanding</span>
              </div>
              
              <!-- Action hint -->
              <div v-if="activePayment && invoiceRemaining(doc.name) > 0.005 && leftRemainingForActive > 0.005" class="mt-1.5 text-center text-[9px] font-bold uppercase text-[var(--color-info)]">
                Click to Link
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- COLUMN 3: Cross-Reconciliation -->
      <div class="flex flex-1 flex-col border-r border-[var(--color-border)]">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Unlinked {{ partyType === 'Supplier' ? 'Receipts' : 'Payments' }} (Opposite)
          <span v-if="oppositeTotal > 0" class="ml-1.5 text-[var(--color-warning)]">₹{{ fmt(oppositeTotal) }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3 space-y-1.5">
          <div class="mb-2 rounded bg-[var(--color-warning)]/20 border border-[var(--color-warning)]/30 px-3 py-2 text-[10px] text-[var(--color-warning)] leading-tight">
            Match floating receipts against floating {{ partyType === 'Supplier' ? 'receipts from supplier' : 'refunds' }} to net them off via Journal Entry.
          </div>
          
          <template v-if="!fetched">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">Search a party and click Fetch</p>
          </template>
          <template v-else-if="allOpposite.length === 0">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">
              No opposite unlinked entries
            </p>
          </template>

          <div v-if="oppositeData.payment_entries.length" class="mb-2">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] px-1">Payment Entries</div>
            <div
              v-for="pe in oppositeData.payment_entries"
              :key="pe.name"
              @click="activePayment && rightRemaining(pe.name, null) > 0.005 ? addCrossAllocation({ type: 'Payment Entry', name: pe.name, reference_row: null, unallocated_amount: pe.unallocated_amount }) : null"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs transition-all"
              :class="activePayment && rightRemaining(pe.name, null) > 0.005 && leftRemainingForActive > 0.005 ? 'cursor-pointer hover:border-[var(--color-warning)] hover:bg-[var(--color-surface-raised)]' : 'opacity-60'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold text-[var(--color-warning)]">{{ pe.name }}</span>
                <span class="font-mono font-bold text-[var(--color-warning)]">₹{{ fmt(rightRemaining(pe.name, null)) }}</span>
              </div>
              <div class="mt-0.5 text-[10px] text-[var(--color-text-muted)]">{{ pe.posting_date }} · {{ pe.mode_of_payment }}</div>
            </div>
          </div>

          <div v-if="oppositeData.journal_entries.length">
            <div class="mb-1 text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] px-1">Journal Entries</div>
            <div
              v-for="je in oppositeData.journal_entries"
              :key="je.reference_row"
              @click="activePayment && rightRemaining(je.name, je.reference_row) > 0.005 ? addCrossAllocation({ type: 'Journal Entry', name: je.name, reference_row: je.reference_row, unallocated_amount: je.unallocated_amount }) : null"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs transition-all"
              :class="activePayment && rightRemaining(je.name, je.reference_row) > 0.005 && leftRemainingForActive > 0.005 ? 'cursor-pointer hover:border-[var(--color-warning)] hover:bg-[var(--color-surface-raised)]' : 'opacity-60'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono font-semibold text-[var(--color-warning)]">{{ je.name }}</span>
                <span class="font-mono font-bold text-[var(--color-warning)]">₹{{ fmt(rightRemaining(je.name, je.reference_row)) }}</span>
              </div>
              <div class="mt-0.5 text-[10px] text-[var(--color-text-muted)]">{{ je.posting_date }} · {{ je.remarks || je.reference_no }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Allocation Preview -->
      <div class="flex w-[360px] shrink-0 flex-col">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/40 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
          Allocation Preview
          <span v-if="allocations.length" class="ml-1.5 text-[var(--color-info)]">{{ allocations.length }} row{{ allocations.length > 1 ? 's' : '' }}</span>
        </div>

        <div class="flex-1 overflow-y-auto p-3">
          <template v-if="allocations.length === 0">
            <p class="py-8 text-center text-xs text-[var(--color-text-muted)]">
              Select a payment on the left, then click "+ Add"
            </p>
          </template>
          <div v-else class="space-y-1.5">
            <div
              v-for="(alloc, i) in allocations"
              :key="i"
              class="rounded-lg border px-3 py-2 text-xs"
              :class="alloc.mode === 'cross' ? 'border-[var(--color-warning)]/40 bg-[var(--color-warning)]/10' : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
            >
              <!-- Cross-reconcile row -->
              <template v-if="alloc.mode === 'cross'">
                <div class="mb-1.5 flex items-center justify-between">
                  <span class="text-[9px] font-bold uppercase text-[var(--color-warning)]">Cross-Reconcile</span>
                  <button @click="removeAllocation(i)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)]">✕</button>
                </div>
                <div class="mb-1 flex items-center gap-2 text-[10px]">
                  <div class="flex-1 rounded bg-[var(--color-info)]/30 px-2 py-1">
                    <div class="text-[var(--color-info)]">{{ alloc.left_type }}</div>
                    <div class="font-mono font-semibold text-[var(--color-text-on-highlight)]">{{ alloc.left_name }}</div>
                  </div>
                  <span class="text-[var(--color-text-muted)]">↔</span>
                  <div class="flex-1 rounded bg-[var(--color-warning)]/30 px-2 py-1">
                    <div class="text-[var(--color-warning)]">{{ alloc.right_type }}</div>
                    <div class="font-mono font-semibold text-[var(--color-text-on-highlight)]">{{ alloc.right_name }}</div>
                  </div>
                </div>
              </template>
              <!-- Invoice reconcile row -->
              <template v-else>
                <div class="mb-1.5 flex items-center justify-between">
                  <div>
                    <span class="text-[9px] text-[var(--color-text-muted)]">{{ alloc.payment_type }}</span>
                    <div class="font-mono font-semibold text-[var(--color-info)]">{{ alloc.payment_name }}</div>
                  </div>
                  <button @click="removeAllocation(i)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)]">✕</button>
                </div>
                <div class="mb-1.5">
                  <span class="text-[9px] text-[var(--color-text-muted)]">{{ alloc.invoice_type }}</span>
                  <div class="font-mono text-[var(--color-text)]">{{ alloc.invoice_name }}</div>
                </div>
              </template>
              <div class="flex items-center gap-2">
                <span class="text-[10px] text-[var(--color-text-muted)] shrink-0">Amount ₹</span>
                <input
                  v-model.number="alloc.amount"
                  type="number"
                  min="0.01"
                  @change="clampAlloc(alloc)"
                  class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-0.5 text-right font-mono text-sm text-[var(--color-text-on-highlight)] focus:border-[var(--color-info)] focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/60 p-4 space-y-3">
          <div class="flex items-center justify-between text-sm">
            <span class="text-[var(--color-text-muted)]">Total Reconciling</span>
            <span class="font-mono font-bold text-[var(--color-info)]">₹{{ fmt(totalAllocating) }}</span>
          </div>

          <div v-if="postError" class="rounded bg-[var(--color-danger)]/30 px-3 py-2 text-xs text-[var(--color-danger)]">{{ postError }}</div>
          <div v-if="postSuccess" class="rounded bg-[var(--color-success)]/30 px-3 py-2 text-xs text-[var(--color-success)]">{{ postSuccess }}</div>

          <button
            @click="postReconcile"
            :disabled="allocations.length === 0 || posting"
            class="w-full rounded-lg bg-[var(--color-info)] py-2.5 text-sm font-bold text-[var(--color-text-on-highlight)] disabled:opacity-40 hover:bg-[var(--color-info)] transition-colors"
          >{{ posting ? 'Posting…' : 'Post Reconciliation' }}</button>

          <button
            v-if="allocations.length"
            @click="allocations = []"
            class="w-full rounded-lg border border-[var(--color-border)] py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          >Clear All</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { searchCustomers } from '../customersearch.js'
import {
  searchSuppliers, searchEmployees,
  getUnlinkedEntries, getUnlinkedOppositeEntries,
  getOutstandingDocs,
  postReconciliation, postCrossReconciliation,
} from '../api.js'

const emit = defineEmits(['close'])

// ── Party selector ────────────────────────────────────────────────────
const partyTypes = ['Customer', 'Supplier', 'Employee']
const partyType = ref('Customer')
const party = ref('')
const partyQuery = ref('')
const partyOptions = ref([])
const partyListIdx = ref(0)

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

// ── Data ──────────────────────────────────────────────────────────────
const loading = ref(false)
const fetched = ref(false)
const error = ref('')

const unlinkedData  = ref({ payment_entries: [], journal_entries: [] })
const oppositeData  = ref({ payment_entries: [], journal_entries: [] })
const outstandingData = ref({ doc_type: 'Sales Invoice', docs: [] })

const allUnlinked = computed(() => [
  ...unlinkedData.value.payment_entries,
  ...unlinkedData.value.journal_entries,
])
const unlinkedTotal = computed(() =>
  unlinkedData.value.payment_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0) +
  unlinkedData.value.journal_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0)
)
const allOpposite = computed(() => [
  ...oppositeData.value.payment_entries,
  ...oppositeData.value.journal_entries,
])
const oppositeTotal = computed(() =>
  oppositeData.value.payment_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0) +
  oppositeData.value.journal_entries.reduce((s, r) => s + parseFloat(r.unallocated_amount || 0), 0)
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
    const [unlinked, opposite, outstanding] = await Promise.all([
      getUnlinkedEntries(partyType.value, party.value),
      getUnlinkedOppositeEntries(partyType.value, party.value),
      getOutstandingDocs(partyType.value, party.value),
    ])
    unlinkedData.value  = unlinked
    oppositeData.value  = opposite
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

// ── Active payment selection ──────────────────────────────────────────
const activePayment = ref(null)

function selectPayment(p) {
  activePayment.value = p
}

// ── Remaining calculations ────────────────────────────────────────────

/** Remaining available on a LEFT panel entry (receipt/credit). */
function leftRemaining(name, referenceRow) {
  const pe = unlinkedData.value.payment_entries.find(p => p.name === name)
  const je = unlinkedData.value.journal_entries.find(j => j.name === name && j.reference_row === referenceRow)
  const original = parseFloat((pe || je)?.unallocated_amount || 0)
  const used = allocations.value
    .filter(a => {
      if (a.mode === 'cross') return a.left_name === name && (a.left_row || null) === (referenceRow || null)
      return a.payment_name === name && (a.reference_row || null) === (referenceRow || null)
    })
    .reduce((s, a) => s + parseFloat(a.amount || 0), 0)
  return Math.max(0, original - used)
}

const leftRemainingForActive = computed(() => {
  if (!activePayment.value) return 0
  return leftRemaining(activePayment.value.name, activePayment.value.reference_row || null)
})

/** Remaining on a RIGHT panel OPPOSITE entry (payment/debit). */
function rightRemaining(name, referenceRow) {
  const pe = oppositeData.value.payment_entries.find(p => p.name === name)
  const je = oppositeData.value.journal_entries.find(j => j.name === name && j.reference_row === referenceRow)
  const original = parseFloat((pe || je)?.unallocated_amount || 0)
  const used = allocations.value
    .filter(a => a.mode === 'cross' && a.right_name === name && (a.right_row || null) === (referenceRow || null))
    .reduce((s, a) => s + parseFloat(a.amount || 0), 0)
  return Math.max(0, original - used)
}

/** Amount of invoice already allocated in the list. */
function allocatedToInvoice(invoiceName) {
  return allocations.value
    .filter(a => a.mode !== 'cross' && a.invoice_name === invoiceName)
    .reduce((s, a) => s + parseFloat(a.amount || 0), 0)
}

/** Remaining outstanding on an invoice. */
function invoiceRemaining(invoiceName) {
  const doc = outstandingData.value.docs.find(d => d.name === invoiceName)
  if (!doc) return 0
  return Math.max(0, parseFloat(doc.outstanding_amount || 0) - allocatedToInvoice(invoiceName))
}

// ── Add allocations ───────────────────────────────────────────────────
const allocations = ref([])

/** Add an invoice-mode allocation row. */
function addInvoiceAllocation(doc) {
  if (!activePayment.value) return
  const ap = activePayment.value
  const amount = Math.min(leftRemainingForActive.value, invoiceRemaining(doc.name))
  if (amount < 0.005) return
  allocations.value.push({
    mode: 'invoice',
    payment_type: ap.type,
    payment_name: ap.name,
    reference_row: ap.reference_row || null,
    invoice_type: outstandingDocType.value,
    invoice_name: doc.name,
    amount: parseFloat(amount.toFixed(2)),
    unreconciled_amount: parseFloat((ap.unallocated_amount || amount).toFixed(2)),
  })
}

/** Add a cross-mode allocation row (payment ↔ opposite entry). */
function addCrossAllocation(rightEntry) {
  if (!activePayment.value) return
  const ap = activePayment.value
  const amount = Math.min(leftRemainingForActive.value, rightRemaining(rightEntry.name, rightEntry.reference_row || null))
  if (amount < 0.005) return
  allocations.value.push({
    mode: 'cross',
    left_type: ap.type,
    left_name: ap.name,
    left_row: ap.reference_row || null,
    right_type: rightEntry.type,
    right_name: rightEntry.name,
    right_row: rightEntry.reference_row || null,
    amount: parseFloat(amount.toFixed(2)),
    unreconciled_amount: parseFloat((ap.unallocated_amount || amount).toFixed(2)),
  })
}

function removeAllocation(i) {
  allocations.value.splice(i, 1)
}

function clampAlloc(alloc) {
  const max = alloc.unreconciled_amount || alloc.amount
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
    const invoiceAllocs = allocations.value.filter(a => a.mode !== 'cross')
    const crossAllocs   = allocations.value.filter(a => a.mode === 'cross')
    let reconciled = 0

    if (invoiceAllocs.length) {
      const res = await postReconciliation(partyType.value, party.value, invoiceAllocs)
      reconciled += res.reconciled || 0
    }
    if (crossAllocs.length) {
      const res = await postCrossReconciliation(partyType.value, party.value, crossAllocs)
      reconciled += res.reconciled || 0
    }

    postSuccess.value = `Reconciled ${reconciled} allocation${reconciled !== 1 ? 's' : ''} successfully.`
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
  unlinkedData.value  = { payment_entries: [], journal_entries: [] }
  oppositeData.value  = { payment_entries: [], journal_entries: [] }
  outstandingData.value = { doc_type: 'Sales Invoice', docs: [] }
  allocations.value = []
  activePayment.value = null
  postError.value = ''
  postSuccess.value = ''
  error.value = ''
}
</script>
