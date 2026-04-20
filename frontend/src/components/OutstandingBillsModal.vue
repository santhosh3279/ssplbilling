<template>
  <div v-if="show" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="w-full max-w-[95vw] rounded-3xl bg-[var(--color-surface)] p-8 shadow-2xl border border-[var(--color-border)] flex flex-col max-h-[95vh]">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-10">
          <h2 class="text-2xl font-normal uppercase tracking-tight">Outstanding & Unlinked Items</h2>
          
          <!-- Summary Display -->
          <div class="flex items-center gap-8 bg-[var(--color-surface-raised)] px-6 py-2.5 rounded-2xl border border-[var(--color-border)] shadow-inner">
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Total Outstanding</span>
              <span class="text-3xl font-black font-mono" :class="totalOutstanding > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                ₹{{ fmt(totalOutstanding) }} {{ totalOutstanding > 0 ? 'Dr' : (totalOutstanding < -0.005 ? 'Cr' : '') }}
              </span>
            </div>
            <div class="h-8 w-px bg-[var(--color-border)]"></div>
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Entered Amount</span>
              <span class="text-3xl font-black text-[var(--color-text)] font-mono">₹{{ fmt(enteredAmount) }}</span>
            </div>
            <div class="h-8 w-px bg-[var(--color-border)]"></div>
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Total Allocated</span>
              <span class="text-3xl font-black text-[var(--color-success)] font-mono">₹{{ fmt(totalAllocated) }}</span>
            </div>
            <div class="h-8 w-px bg-[var(--color-border)]"></div>
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Remaining Balance</span>
              <span class="text-3xl font-black font-mono" :class="remainingBalance < -0.005 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">₹{{ (remainingBalance < -0.005 ? '-' : '') + fmt(remainingBalance) }}</span>
            </div>
          </div>

          <!-- Direction Filter -->
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5 shadow-sm">
            <button
              v-for="d in ['All', 'Dr', 'Cr']"
              :key="d"
              @click="filterDirection = d"
              class="min-w-[50px] rounded-md px-3 py-1 text-[10px] font-normal uppercase transition-all duration-200"
              :class="filterDirection === d 
                ? 'bg-[var(--color-highlight)] text-white shadow-sm' 
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              {{ d }}
            </button>
          </div>
        </div>
        <button @click="$emit('close')" class="h-10 w-10 rounded-full hover:bg-[var(--color-midlight)] transition-colors flex items-center justify-center text-2xl">
          ✕
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar border border-[var(--color-border)] rounded-2xl bg-[var(--color-surface-raised)]/30 p-6 space-y-6">
        <!-- Table Header (Adopted from Unallocated.vue) -->
        <div class="px-6 py-2 flex items-center gap-6 text-[11px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-60">
          <div class="w-[250px] shrink-0">Reference No</div>
          <div class="w-[120px] shrink-0">Type</div>
          <div class="w-[120px] shrink-0">Due Days</div>
          <div class="w-[100px] shrink-0 text-center">Direction</div>
          <div class="w-[180px] shrink-0 text-right">Outstanding</div>
          <div class="flex-1 text-right">Adjustment Amount</div>
          <div class="w-[180px] shrink-0 text-right">Balance</div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="px-6 py-12 text-center text-[var(--color-text-muted)]">Loading...</div>

        <!-- No Items State -->
        <div v-else-if="!filteredInvoices.length && !filteredPayments.length && !filteredJournals.length" class="px-6 py-12 text-center text-[var(--color-text-muted)]">
          No outstanding or unlinked items found.
        </div>

        <!-- Outstanding Invoices Section -->
        <template v-if="filteredInvoices.length">
          <div class="space-y-3">
            <h3 class="px-3 text-[14px] font-black uppercase tracking-widest text-[var(--color-danger)] flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-danger)]"></span>
              Outstanding Invoices / Returns
            </h3>
            <div v-for="inv in filteredInvoices" :key="inv.name" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 shadow-md flex items-center gap-6 group hover:border-[var(--color-highlight)]/30 transition-all">
              <div class="w-[250px] shrink-0 font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ inv.name }}</div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold text-[var(--color-text-muted)] uppercase">{{ inv.doctype }}</div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold" :class="calculateDueDays(inv.posting_date) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                {{ calculateDueDays(inv.posting_date) }} Days
              </div>
              <div class="w-[100px] shrink-0 text-center">
                <span class="px-2 py-0.5 rounded text-[11px] font-black uppercase" :class="inv.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">{{ inv.direction }}</span>
              </div>
              <div class="w-[180px] shrink-0 text-right text-[22px] font-black font-mono" :class="inv.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                ₹{{ fmt(inv.outstanding_amount) }}
              </div>
              <div class="flex-1 flex justify-end">
                <div class="w-48 relative">
                  <input
                    v-model.number="localModalAmounts[inv.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(inv.outstanding_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[inv.name] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-4 text-right font-mono text-[22px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 transition-all outline-none disabled:opacity-20 disabled:grayscale"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(inv, 'invoice')"
                  />
                </div>
              </div>
              <div class="w-[180px] shrink-0 text-right text-[20px] font-black font-mono opacity-40">
                ₹{{ fmt(Math.abs(inv.outstanding_amount) - (localModalAmounts[inv.name] || 0)) }}
              </div>
            </div>
          </div>
        </template>

        <!-- Unlinked Payment Entries Section -->
        <template v-if="filteredPayments.length">
          <div class="space-y-3">
            <h3 class="px-3 text-[14px] font-black uppercase tracking-widest text-[var(--color-success)] flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-success)]"></span>
              Unlinked Payment Entries
            </h3>
            <div v-for="pe in filteredPayments" :key="pe.name" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 shadow-md flex items-center gap-6 group hover:border-[var(--color-highlight)]/30 transition-all">
              <div class="w-[250px] shrink-0 flex flex-col min-w-0">
                <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ pe.name }}</div>
                <div v-if="pe.remarks" class="text-[11px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ pe.remarks }}</div>
              </div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold text-[var(--color-text-muted)] uppercase">Payment Entry</div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold text-[var(--color-text-muted)] uppercase">{{ calculateDueDays(pe.posting_date) }} Days</div>
              <div class="w-[100px] shrink-0 text-center">
                <span class="px-2 py-0.5 rounded text-[11px] font-black uppercase" :class="pe.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">{{ pe.direction }}</span>
              </div>
              <div class="w-[180px] shrink-0 text-right text-[22px] font-black font-mono text-[var(--color-success)]">
                ₹{{ fmt(pe.unallocated_amount) }}
              </div>
              <div class="flex-1 flex justify-end">
                <div class="w-48 relative">
                  <input
                    v-model.number="localModalAmounts[pe.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(pe.unallocated_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[pe.name] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-4 text-right font-mono text-[22px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 transition-all outline-none disabled:opacity-20 disabled:grayscale"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(pe, 'payment')"
                  />
                </div>
              </div>
              <div class="w-[180px] shrink-0 text-right text-[20px] font-black font-mono opacity-40">
                ₹{{ fmt(Math.abs(pe.unallocated_amount) - (localModalAmounts[pe.name] || 0)) }}
              </div>
            </div>
          </div>
        </template>

        <!-- Unlinked Journal Entries Section -->
        <template v-if="filteredJournals.length">
          <div class="space-y-3">
            <h3 class="px-3 text-[14px] font-black uppercase tracking-widest text-[var(--color-info)] flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-[var(--color-info)]"></span>
              Unlinked Journal Entries
            </h3>
            <div v-for="je in filteredJournals" :key="je.reference_row" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 shadow-md flex items-center gap-6 group hover:border-[var(--color-highlight)]/30 transition-all">
              <div class="w-[250px] shrink-0 flex flex-col min-w-0">
                <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ je.name }}</div>
                <div v-if="je.remarks" class="text-[11px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ je.remarks }}</div>
              </div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold text-[var(--color-text-muted)] uppercase">Journal Entry</div>
              <div class="w-[120px] shrink-0 text-[14px] font-bold text-[var(--color-text-muted)] uppercase">{{ calculateDueDays(je.posting_date) }} Days</div>
              <div class="w-[100px] shrink-0 text-center">
                <span class="px-2 py-0.5 rounded text-[11px] font-black uppercase" :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">{{ je.direction }}</span>
              </div>
              <div class="w-[180px] shrink-0 text-right">
                <div class="text-[22px] font-black font-mono text-[var(--color-info)]">
                  ₹{{ fmt(je.unallocated_amount) }}
                </div>
                <div v-if="je.total_amount && Math.abs(je.total_amount - (je.unallocated_amount || 0)) > 0.005" class="text-[10px] font-bold text-[var(--color-text-muted)] opacity-60">
                  {{ fmt(je.total_amount) }} - {{ fmt(je.total_amount - (je.unallocated_amount || 0)) }} (Lnk)
                </div>
              </div>
              <div class="flex-1 flex justify-end">
                <div class="w-48 relative">
                  <input
                    v-model.number="localModalAmounts[je.reference_row]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(je.unallocated_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[je.reference_row] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-4 text-right font-mono text-[22px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 transition-all outline-none disabled:opacity-20 disabled:grayscale"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(je, 'journal')"
                  />
                </div>
              </div>
              <div class="w-[180px] shrink-0 text-right text-[20px] font-black font-mono opacity-40">
                ₹{{ fmt(Math.abs(je.unallocated_amount) - (localModalAmounts[je.reference_row] || 0)) }}
              </div>
            </div>
          </div>
        </template>
      </div>
      
      <div class="mt-8 flex justify-end gap-6">
        <button
          ref="confirmBtn"
          @click="confirmAdjustments"
          class="rounded-2xl bg-[var(--color-highlight)] px-12 py-4 text-2xl font-black uppercase tracking-widest text-white hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-[var(--color-highlight)]/20"
        >
          Confirm Adjustments
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  loading: Boolean,
  enteredAmount: {
    type: Number,
    default: 0
  },
  invoices: {
    type: Array,
    default: () => []
  },
  unlinkedPayments: {
    type: Array,
    default: () => []
  },
  unlinkedJournals: {
    type: Array,
    default: () => []
  },
  activeTab: String,
  allocationRefs: {
    type: Array,
    default: () => []
  },
  modalAmounts: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'update-allocations'])

const filterDirection = ref('All')
const localModalAmounts = ref({})
const lastModifiedKey = ref(null)
const confirmBtn = ref(null)

// Sync localModalAmounts with prop
watch(() => props.modalAmounts, (newVal) => {
  localModalAmounts.value = { ...newVal }
  // Try to find the last key with a non-zero value as a starting point
  if (!lastModifiedKey.value) {
    const keys = Object.keys(localModalAmounts.value)
    for (let i = keys.length - 1; i >= 0; i--) {
      if (localModalAmounts.value[keys[i]] > 0) {
        lastModifiedKey.value = keys[i]
        break
      }
    }
  }
}, { immediate: true, deep: true })

watch(() => props.show, (val) => {
  if (val) {
    filterDirection.value = props.activeTab === 'Receipt' ? 'Dr' : 'Cr'
    nextTick(() => {
      setTimeout(() => {
        const firstInput = document.querySelector('.allocate-input')
        if (firstInput) {
          firstInput.focus()
          firstInput.select()
        }
      }, 150)
    })
  } else {
    lastModifiedKey.value = null
  }
})

const totalAllocated = computed(() => {
  return Object.values(localModalAmounts.value).reduce((sum, val) => sum + (parseFloat(val) || 0), 0)
})

const remainingBalance = computed(() => {
  return props.enteredAmount - totalAllocated.value
})

const totalOutstanding = computed(() => {
  const invs = props.invoices || []
  const jurns = props.unlinkedJournals || []
  const payms = props.unlinkedPayments || []
  const invBal = invs.reduce((sum, i) => sum + (i.direction === 'Dr' ? 1 : -1) * Math.abs(i.outstanding_amount), 0)
  const jeBal = jurns.reduce((sum, j) => sum + (j.direction === 'Dr' ? 1 : -1) * Math.abs(j.unallocated_amount), 0)
  const peBal = payms.reduce((sum, p) => sum + (p.direction === 'Dr' ? 1 : -1) * Math.abs(p.unallocated_amount), 0)
  return invBal + jeBal + peBal
})

const filteredPayments = computed(() => {
  const payms = props.unlinkedPayments || []
  if (filterDirection.value === 'All') return payms
  return payms.filter(p => p.direction === filterDirection.value)
})

const filteredJournals = computed(() => {
  const jurns = props.unlinkedJournals || []
  if (filterDirection.value === 'All') return jurns
  return jurns.filter(j => j.direction === filterDirection.value)
})

const filteredInvoices = computed(() => {
  const invs = props.invoices || []
  if (filterDirection.value === 'All') return invs
  return invs.filter(i => i.direction === filterDirection.value)
})

function onAllocationChange(item, type) {
  const key = type === 'journal' ? item.reference_row : item.name
  lastModifiedKey.value = key
}

function emitAllocations() {
  const allInvoices = props.invoices.map(i => ({
    reference_doctype: i.doctype,
    reference_name: i.name,
    total_amount: i.grand_total,
    outstanding_amount: Math.abs(i.outstanding_amount),
    allocated_amount: parseFloat(localModalAmounts.value[i.name]) || 0
  }))

  const allJournals = props.unlinkedJournals.map(j => ({
    reference_doctype: 'Journal Entry',
    reference_name: j.name,
    total_amount: j.total_amount || j.unallocated_amount,
    outstanding_amount: Math.abs(j.unallocated_amount),
    allocated_amount: parseFloat(localModalAmounts.value[j.reference_row]) || 0,
    _row: j.reference_row
  }))

  const allPayments = props.unlinkedPayments.map(p => ({
    reference_doctype: 'Payment Entry',
    reference_name: p.name,
    total_amount: p.paid_amount,
    outstanding_amount: Math.abs(p.unallocated_amount),
    allocated_amount: parseFloat(localModalAmounts.value[p.name]) || 0
  }))

  const allocations = [...allInvoices, ...allJournals, ...allPayments].filter(a => a.allocated_amount > 0)
  
  emit('update-allocations', allocations)
}

function confirmAdjustments() {
  if (Math.abs(remainingBalance.value) > 0.005) {
    let targetKey = lastModifiedKey.value

    // If last modified key is not in visible rows, clear it
    const allVisibleKeys = [
      ...filteredInvoices.value.map(i => i.name),
      ...filteredPayments.value.map(p => p.name),
      ...filteredJournals.value.map(j => j.reference_row)
    ]
    
    if (targetKey && !allVisibleKeys.includes(targetKey)) {
      targetKey = null
    }

    // If no valid manual edit, find the last row that has any allocation among VISIBLE items
    if (!targetKey) {
      for (let i = allVisibleKeys.length - 1; i >= 0; i--) {
        if (localModalAmounts.value[allVisibleKeys[i]] > 0) {
          targetKey = allVisibleKeys[i]
          break
        }
      }
    }

    // If still no target, just pick the last item in the CURRENT VISIBLE list if it exists
    if (!targetKey && allVisibleKeys.length > 0) {
      targetKey = allVisibleKeys[allVisibleKeys.length - 1]
    }

    if (targetKey) {
      // Cap at the item's outstanding amount so allocated_amount never exceeds outstanding_amount
      const invItem = props.invoices.find(i => i.name === targetKey)
      const peItem = props.unlinkedPayments.find(p => p.name === targetKey)
      const jeItem = props.unlinkedJournals.find(j => j.reference_row === targetKey)
      const maxOutstanding = invItem
        ? Math.abs(invItem.outstanding_amount)
        : peItem
          ? Math.abs(peItem.unallocated_amount)
          : jeItem
            ? Math.abs(jeItem.unallocated_amount)
            : Infinity
      const current = parseFloat(localModalAmounts.value[targetKey]) || 0
      localModalAmounts.value[targetKey] = Math.min(current + remainingBalance.value, maxOutstanding)
    }
  }
  
  // Always emit allocations before closing, even if balance was already 0
  emitAllocations()
  emit('close')
}

function fmt(val) {
  return Math.abs(Number(val || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function calculateDueDays(dateStr) {
  if (!dateStr) return 0
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const postingDate = new Date(dateStr)
  postingDate.setHours(0, 0, 0, 0)
  const diffTime = today - postingDate
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}

function focusNextAllocate(event) {
  const currentInput = event.target
  
  // If balance reached zero, jump straight to confirm
  if (Math.abs(remainingBalance.value) < 0.005) {
    confirmBtn.value?.focus()
    return
  }

  const inputs = Array.from(document.querySelectorAll('.allocate-input:not(:disabled)'))
  const index = inputs.indexOf(currentInput)
  if (index >= 0 && index < inputs.length - 1) {
    inputs[index + 1].focus()
    inputs[index + 1].select()
  } else {
    confirmBtn.value?.focus()
  }
}
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

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
</style>
