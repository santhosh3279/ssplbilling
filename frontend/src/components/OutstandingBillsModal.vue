<template>
  <div v-if="show" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="w-full max-w-[96vw] h-[90vh] rounded-3xl bg-[var(--color-surface)] shadow-2xl border border-[var(--color-border)] flex flex-col overflow-hidden">

      <!-- HEADER -->
      <div class="flex items-center justify-between px-8 py-5 border-b border-[var(--color-border)] shrink-0">
        <div class="flex items-center gap-5">
          <h2 class="text-4xl font-black uppercase tracking-tight text-[var(--color-text)]">Outstanding Items</h2>
          <span v-if="party" class="text-2xl font-bold text-[var(--color-highlight)] bg-[var(--color-highlight)]/10 px-4 py-1.5 rounded-lg font-mono">{{ party }}</span>
          <!-- Direction Filter -->
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5">
            <button
              v-for="d in ['All', 'Dr', 'Cr']"
              :key="d"
              @click="filterDirection = d"
              class="min-w-[60px] rounded-md px-4 py-1.5 text-[20px] font-black uppercase transition-all duration-150"
              :class="filterDirection === d ? 'bg-[var(--color-highlight)] text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >{{ d }}</button>
          </div>
        </div>
        <button @click="$emit('close')" class="h-11 w-11 rounded-full hover:bg-[var(--color-midlight)] flex items-center justify-center text-2xl transition-colors">✕</button>
      </div>

      <!-- SUMMARY STRIP -->
      <div class="grid grid-cols-4 divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface-raised)]/40">
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Net Outstanding</span>
          <span class="text-5xl font-black font-mono"
            :class="netOutstanding > 0.005 ? 'text-[var(--color-danger)]' : netOutstanding < -0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'">
            ₹{{ fmt(netOutstanding) }}<span class="text-2xl ml-1 font-bold">{{ netOutstanding > 0.005 ? 'Dr' : netOutstanding < -0.005 ? 'Cr' : '' }}</span>
          </span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Entered Amount</span>
          <span class="text-5xl font-black font-mono text-[var(--color-text)]">₹{{ fmt(enteredAmount) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Total Allocated</span>
          <span class="text-5xl font-black font-mono text-[var(--color-success)]">₹{{ fmt(totalAllocated) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Remaining Balance</span>
          <span class="text-5xl font-black font-mono"
            :class="Math.abs(remainingBalance) < 0.005 ? 'text-[var(--color-success)]' : remainingBalance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">
            ₹{{ fmt(Math.abs(remainingBalance)) }}
          </span>
        </div>
      </div>

      <!-- TABLE -->
      <div class="flex-1 overflow-y-auto custom-scrollbar">

        <!-- Column Headers (sticky) -->
        <div class="sticky top-0 z-10 bg-[var(--color-surface-raised)] border-b border-[var(--color-border)] px-6 py-3 grid gap-3 text-[20px] font-black uppercase tracking-[0.15em] text-[var(--color-text-muted)]"
          style="grid-template-columns: minmax(300px,2fr) 250px 200px 120px 340px 360px 300px;">
          <div>Reference</div>
          <div>Type</div>
          <div class="text-center">Date / Age</div>
          <div class="text-center">Dir</div>
          <div class="text-right">Outstanding</div>
          <div class="text-right">Allocate</div>
          <div class="text-right">Balance</div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="flex items-center justify-center py-24 gap-3 text-[var(--color-text-muted)]">
          <svg class="animate-spin w-8 h-8 shrink-0" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span class="text-3xl font-bold">Loading...</span>
        </div>

        <!-- Empty -->
        <div v-else-if="!filteredInvoices.length && !filteredPayments.length && !filteredJournals.length"
          class="flex flex-col items-center justify-center py-24 gap-4 text-[var(--color-text-muted)]">
          <span class="text-[6rem] opacity-30">✓</span>
          <span class="text-3xl font-bold">No outstanding items found</span>
        </div>

        <template v-else>

          <!-- OUTSTANDING INVOICES -->
          <template v-if="filteredInvoices.length">
            <div class="px-6 py-3 flex items-center gap-2 bg-[var(--color-danger)]/5 border-b border-[var(--color-danger)]/15">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-danger)] shrink-0"></span>
              <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-danger)]">Outstanding Invoices & Returns</span>
              <span class="ml-auto text-[20px] font-bold text-[var(--color-danger)] opacity-60">{{ filteredInvoices.length }}</span>
            </div>
            <div
              v-for="inv in filteredInvoices"
              :key="inv.name"
              class="px-6 py-8 border-b border-[var(--color-border)] grid gap-3 items-center hover:bg-[var(--color-midlight)]/20 transition-colors"
              style="grid-template-columns: minmax(300px,2fr) 250px 200px 120px 340px 360px 300px;"
            >
              <div class="font-mono text-6xl font-black text-[var(--color-text)] truncate">{{ inv.name }}</div>
              <div class="text-[44px] font-semibold text-[var(--color-text-muted)] truncate">
                {{ inv.doctype === 'Sales Invoice' ? 'Sales Inv' : 'Purch Inv' }}
              </div>
              <div class="flex flex-col items-center gap-0.5">
                <span class="text-[44px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(inv.posting_date) }}</span>
                <span class="text-[40px] font-black"
                  :class="dueDays(inv.posting_date) > 30 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)] opacity-50'">
                  {{ dueDays(inv.posting_date) }}d
                </span>
              </div>
              <div class="flex justify-center">
                <span class="px-3 py-1.5 rounded text-[40px] font-black uppercase"
                  :class="inv.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                  {{ inv.direction }}
                </span>
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono"
                  :class="inv.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  ₹{{ fmt(inv.outstanding_amount) }}
                </span>
              </div>
              <div class="flex justify-end">
                <input
                  v-model.number="localAmounts[inv.name]"
                  type="number" step="0.01" min="0"
                  :max="Math.abs(inv.outstanding_amount)"
                  :disabled="remainingBalance <= 0.005 && !(localAmounts[inv.name] > 0)"
                  class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-5 px-5 text-right font-mono text-6xl font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                  @keydown.enter="focusNextAllocate($event)"
                  @input="onAllocationChange(inv.name)"
                />
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono"
                  :class="balanceFor(inv.name, inv.outstanding_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                  ₹{{ fmt(balanceFor(inv.name, inv.outstanding_amount)) }}
                </span>
              </div>
            </div>
          </template>

          <!-- UNLINKED PAYMENT ENTRIES -->
          <template v-if="filteredPayments.length">
            <div class="px-6 py-3 flex items-center gap-2 bg-[var(--color-success)]/5 border-b border-[var(--color-success)]/15">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-success)] shrink-0"></span>
              <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-success)]">Unlinked Payment Entries</span>
              <span class="ml-auto text-[20px] font-bold text-[var(--color-success)] opacity-60">{{ filteredPayments.length }}</span>
            </div>
            <div
              v-for="pe in filteredPayments"
              :key="pe.name"
              class="px-6 py-8 border-b border-[var(--color-border)] grid gap-3 items-center hover:bg-[var(--color-midlight)]/20 transition-colors"
              style="grid-template-columns: minmax(300px,2fr) 250px 200px 120px 340px 360px 300px;"
            >
              <div class="flex flex-col min-w-0">
                <span class="font-mono text-6xl font-black text-[var(--color-text)] truncate">{{ pe.name }}</span>
                <span v-if="pe.remarks" class="text-[40px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ pe.remarks }}</span>
              </div>
              <div class="text-[44px] font-semibold text-[var(--color-text-muted)]">Payment</div>
              <div class="flex flex-col items-center gap-0.5">
                <span class="text-[44px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(pe.posting_date) }}</span>
                <span class="text-[40px] font-black text-[var(--color-text-muted)] opacity-50">{{ dueDays(pe.posting_date) }}d</span>
              </div>
              <div class="flex justify-center">
                <span class="px-3 py-1.5 rounded text-[40px] font-black uppercase"
                  :class="pe.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                  {{ pe.direction }}
                </span>
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono text-[var(--color-success)]">₹{{ fmt(pe.unallocated_amount) }}</span>
                <div v-if="pe.paid_amount && Math.abs(pe.paid_amount - pe.unallocated_amount) > 0.005"
                  class="text-[40px] text-[var(--color-text-muted)] opacity-50">
                  of ₹{{ fmt(pe.paid_amount) }}
                </div>
              </div>
              <div class="flex justify-end">
                <input
                  v-model.number="localAmounts[pe.name]"
                  type="number" step="0.01" min="0"
                  :max="Math.abs(pe.unallocated_amount)"
                  :disabled="remainingBalance <= 0.005 && !(localAmounts[pe.name] > 0)"
                  class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-5 px-5 text-right font-mono text-6xl font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                  @keydown.enter="focusNextAllocate($event)"
                  @input="onAllocationChange(pe.name)"
                />
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono"
                  :class="balanceFor(pe.name, pe.unallocated_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                  ₹{{ fmt(balanceFor(pe.name, pe.unallocated_amount)) }}
                </span>
              </div>
            </div>
          </template>

          <!-- UNLINKED JOURNAL ENTRIES -->
          <template v-if="filteredJournals.length">
            <div class="px-6 py-3 flex items-center gap-2 bg-[var(--color-info)]/5 border-b border-[var(--color-info)]/15">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-info)] shrink-0"></span>
              <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-info)]">Unlinked Journal Entries</span>
              <span class="ml-auto text-[20px] font-bold text-[var(--color-info)] opacity-60">{{ filteredJournals.length }}</span>
            </div>
            <div
              v-for="je in filteredJournals"
              :key="je.reference_row || (je.name + je.account)"
              class="px-6 py-8 border-b border-[var(--color-border)] grid gap-3 items-center hover:bg-[var(--color-midlight)]/20 transition-colors"
              style="grid-template-columns: minmax(300px,2fr) 250px 200px 120px 340px 360px 300px;"
            >
              <div class="flex flex-col min-w-0">
                <span class="font-mono text-6xl font-black text-[var(--color-text)] truncate">{{ je.name }}</span>
                <span v-if="je.remarks" class="text-[40px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ je.remarks }}</span>
              </div>
              <div class="text-[44px] font-semibold text-[var(--color-text-muted)]">Journal</div>
              <div class="flex flex-col items-center gap-0.5">
                <span class="text-[44px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(je.posting_date) }}</span>
                <span class="text-[40px] font-black text-[var(--color-text-muted)] opacity-50">{{ dueDays(je.posting_date) }}d</span>
              </div>
              <div class="flex justify-center">
                <span class="px-3 py-1.5 rounded text-[40px] font-black uppercase"
                  :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                  {{ je.direction }}
                </span>
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono text-[var(--color-info)]">₹{{ fmt(je.unallocated_amount) }}</span>
              </div>
              <div class="flex justify-end">
                <input
                  v-model.number="localAmounts[je.reference_row]"
                  type="number" step="0.01" min="0"
                  :max="Math.abs(je.unallocated_amount)"
                  :disabled="remainingBalance <= 0.005 && !(localAmounts[je.reference_row] > 0)"
                  class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-5 px-5 text-right font-mono text-6xl font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                  @keydown.enter="focusNextAllocate($event)"
                  @input="onAllocationChange(je.reference_row)"
                />
              </div>
              <div class="text-right">
                <span class="text-6xl font-black font-mono"
                  :class="balanceFor(je.reference_row, je.unallocated_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                  ₹{{ fmt(balanceFor(je.reference_row, je.unallocated_amount)) }}
                </span>
              </div>
            </div>
          </template>

        </template>
      </div>

      <!-- FOOTER -->
      <div class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]/60 px-8 py-5 flex items-center justify-between">
        <div class="text-[20px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest flex items-center gap-4">
          <span>{{ totalItemCount }} item{{ totalItemCount !== 1 ? 's' : '' }}</span>
          <span class="opacity-30">·</span>
          <span>{{ allocatedCount }} allocated</span>
        </div>
        <button
          ref="confirmBtn"
          @click="confirmAdjustments"
          class="rounded-2xl bg-[var(--color-highlight)] px-12 py-5 text-4xl font-black uppercase tracking-widest text-white hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-[var(--color-highlight)]/20"
        >
          Confirm Adjustments
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { frappeGet } from '../api.js'

const props = defineProps({
  show: Boolean,
  loading: { type: Boolean, default: false },
  partyType: { type: String, default: '' },
  party: { type: String, default: '' },
  enteredAmount: { type: Number, default: 0 },
  activeTab: String,
  modalAmounts: { type: Object, default: () => ({}) },
  // Backward-compat props (used when data is passed in from parent)
  invoices: { type: Array, default: () => [] },
  unlinkedPayments: { type: Array, default: () => [] },
  unlinkedJournals: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'update-allocations'])

const localLoading = ref(false)
const localInvoices = ref([])
const localPayments = ref([])
const localJournals = ref([])
const filterDirection = ref('All')
const localAmounts = ref({})
const lastModifiedKey = ref(null)
const confirmBtn = ref(null)

const isLoading = computed(() => props.loading || localLoading.value)

async function fetchData() {
  if (!props.party || !props.partyType) return
  localLoading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
      party_type: props.partyType,
      party: props.party,
    })
    localInvoices.value = res.invoices || []
    localPayments.value = res.payment_entries || []
    localJournals.value = res.journal_entries || []

    // Auto-fill allocations when entering for the first time
    if (Object.keys(localAmounts.value).length === 0 && props.enteredAmount > 0) {
      const targetDir = props.activeTab === 'Receipt' ? 'Dr' : 'Cr'
      let remaining = props.enteredAmount

      localInvoices.value.filter(i => i.direction === targetDir).forEach(inv => {
        const alloc = Math.min(remaining, Math.abs(inv.outstanding_amount))
        localAmounts.value[inv.name] = alloc
        remaining -= alloc
      })

      localJournals.value.filter(j => j.direction === targetDir).forEach(je => {
        const alloc = Math.min(remaining, Math.abs(je.unallocated_amount))
        localAmounts.value[je.reference_row] = alloc
        remaining -= alloc
      })

      localPayments.value.filter(p => p.direction === targetDir).forEach(pe => {
        const alloc = Math.min(remaining, Math.abs(pe.unallocated_amount))
        localAmounts.value[pe.name] = alloc
        remaining -= alloc
      })
    }
  } catch (e) {
    console.error('[OutstandingBillsModal] fetch failed:', e)
  } finally {
    localLoading.value = false
  }
}

watch(() => props.modalAmounts, (newVal) => {
  localAmounts.value = { ...newVal }
  if (!lastModifiedKey.value) {
    const keys = Object.keys(localAmounts.value)
    for (let i = keys.length - 1; i >= 0; i--) {
      if (localAmounts.value[keys[i]] > 0) { lastModifiedKey.value = keys[i]; break }
    }
  }
}, { immediate: true, deep: true })

watch(() => props.show, (val) => {
  if (val) {
    filterDirection.value = props.activeTab === 'Receipt' ? 'Dr' : 'Cr'
    if (props.party) fetchData()
  } else {
    lastModifiedKey.value = null
    localInvoices.value = []
    localPayments.value = []
    localJournals.value = []
  }
}, { immediate: true })

const currentInvoices = computed(() => localInvoices.value.length ? localInvoices.value : props.invoices)
const currentPayments = computed(() => localPayments.value.length ? localPayments.value : props.unlinkedPayments)
const currentJournals = computed(() => localJournals.value.length ? localJournals.value : props.unlinkedJournals)

const filteredInvoices = computed(() => {
  const list = currentInvoices.value || []
  return filterDirection.value === 'All' ? list : list.filter(i => i.direction === filterDirection.value)
})
const filteredPayments = computed(() => {
  const list = currentPayments.value || []
  return filterDirection.value === 'All' ? list : list.filter(p => p.direction === filterDirection.value)
})
const filteredJournals = computed(() => {
  const list = currentJournals.value || []
  return filterDirection.value === 'All' ? list : list.filter(j => j.direction === filterDirection.value)
})

const totalAllocated = computed(() =>
  Object.values(localAmounts.value).reduce((s, v) => s + (isNaN(parseFloat(v)) ? 0 : parseFloat(v)), 0)
)
const remainingBalance = computed(() => props.enteredAmount - totalAllocated.value)

const netOutstanding = computed(() => {
  const sign = (dir) => dir === 'Dr' ? 1 : -1
  const invBal = (currentInvoices.value || []).reduce((s, i) => s + sign(i.direction) * Math.abs(i.outstanding_amount), 0)
  const jeBal  = (currentJournals.value || []).reduce((s, j) => s + sign(j.direction) * Math.abs(j.unallocated_amount), 0)
  const peBal  = (currentPayments.value || []).reduce((s, p) => s + sign(p.direction) * Math.abs(p.unallocated_amount), 0)
  return invBal + jeBal + peBal
})

const totalItemCount = computed(() => filteredInvoices.value.length + filteredPayments.value.length + filteredJournals.value.length)
const allocatedCount = computed(() => Object.values(localAmounts.value).filter(v => parseFloat(v) > 0).length)

function balanceFor(key, outstanding) {
  return Math.max(0, Math.abs(outstanding) - (parseFloat(localAmounts.value[key]) || 0))
}

function onAllocationChange(key) {
  lastModifiedKey.value = key
}

function emitAllocations() {
  const allInvoices = currentInvoices.value.map(i => ({
    reference_doctype: i.doctype,
    reference_name: i.name,
    total_amount: i.grand_total,
    outstanding_amount: Math.abs(i.outstanding_amount),
    allocated_amount: parseFloat(localAmounts.value[i.name]) || 0,
  }))
  const allJournals = currentJournals.value.map(j => ({
    reference_doctype: 'Journal Entry',
    reference_name: j.name,
    total_amount: j.total_amount || j.unallocated_amount,
    outstanding_amount: Math.abs(j.unallocated_amount),
    allocated_amount: parseFloat(localAmounts.value[j.reference_row]) || 0,
    _row: j.reference_row,
  }))
  const allPayments = currentPayments.value.map(p => ({
    reference_doctype: 'Payment Entry',
    reference_name: p.name,
    total_amount: p.paid_amount,
    outstanding_amount: Math.abs(p.unallocated_amount),
    allocated_amount: parseFloat(localAmounts.value[p.name]) || 0,
  }))
  emit('update-allocations', [...allInvoices, ...allJournals, ...allPayments].filter(a => a.allocated_amount > 0))
}

function confirmAdjustments() {
  if (Math.abs(remainingBalance.value) > 0.005) {
    let targetKey = lastModifiedKey.value
    const allVisibleKeys = [
      ...filteredInvoices.value.map(i => i.name),
      ...filteredPayments.value.map(p => p.name),
      ...filteredJournals.value.map(j => j.reference_row),
    ]
    if (targetKey && !allVisibleKeys.includes(targetKey)) targetKey = null
    if (!targetKey) {
      for (let i = allVisibleKeys.length - 1; i >= 0; i--) {
        if (localAmounts.value[allVisibleKeys[i]] > 0) { targetKey = allVisibleKeys[i]; break }
      }
    }
    if (!targetKey && allVisibleKeys.length > 0) targetKey = allVisibleKeys[allVisibleKeys.length - 1]

    if (targetKey) {
      const inv = currentInvoices.value.find(i => i.name === targetKey)
      const pe  = currentPayments.value.find(p => p.name === targetKey)
      const je  = currentJournals.value.find(j => j.reference_row === targetKey)
      const maxOut = inv ? Math.abs(inv.outstanding_amount) : pe ? Math.abs(pe.unallocated_amount) : je ? Math.abs(je.unallocated_amount) : Infinity
      const current = parseFloat(localAmounts.value[targetKey]) || 0
      localAmounts.value[targetKey] = Math.min(current + remainingBalance.value, maxOut)
    }
  }
  emitAllocations()
  emit('close')
}

function fmt(val) {
  return Math.abs(Number(val || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]}`
}

function dueDays(dateStr) {
  if (!dateStr) return 0
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const d = new Date(dateStr); d.setHours(0, 0, 0, 0)
  return Math.floor((today - d) / 86400000)
}

function focusNextAllocate(event) {
  if (Math.abs(remainingBalance.value) < 0.005) { confirmBtn.value?.focus(); return }
  const inputs = Array.from(document.querySelectorAll('.allocate-input:not(:disabled)'))
  const idx = inputs.indexOf(event.target)
  if (idx >= 0 && idx < inputs.length - 1) { inputs[idx + 1].focus(); inputs[idx + 1].select() }
  else confirmBtn.value?.focus()
}
</script>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }

.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }
</style>
