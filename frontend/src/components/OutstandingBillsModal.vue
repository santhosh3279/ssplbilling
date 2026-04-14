<template>
  <div v-if="show" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="w-full max-w-[95vw] rounded-3xl bg-[var(--color-surface)] p-8 shadow-2xl border border-[var(--color-border)] flex flex-col max-h-[95vh]">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-10">
          <h2 class="text-2xl font-normal uppercase tracking-tight">Outstanding & Unlinked Items</h2>
          
          <!-- Summary Display -->
          <div class="flex items-center gap-8 bg-[var(--color-surface-raised)] px-6 py-2.5 rounded-2xl border border-[var(--color-border)] shadow-inner">
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
              <span class="text-3xl font-black font-mono" :class="remainingBalance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">₹{{ fmt(remainingBalance) }}</span>
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
      
      <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar border border-[var(--color-border)] rounded-2xl bg-[var(--color-surface-raised)]/30">
        <table class="w-full text-left border-separate border-spacing-0">
          <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)] sticky top-0 z-10">
            <tr class="text-2xl font-normal uppercase tracking-widest text-[var(--color-text-muted)]">
              <th class="px-4 py-4 border-b border-[var(--color-border)]">Voucher No</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)]">Type</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)]">Due Days</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)] text-center">Dir/Mode</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)] text-right">Outstanding</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)] text-right w-56">Allocate</th>
              <th class="px-4 py-4 border-b border-[var(--color-border)] text-right w-48">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <!-- Loading State -->
            <tr v-if="loading">
              <td colspan="7" class="px-6 py-12 text-center text-[var(--color-text-muted)]">Loading...</td>
            </tr>

            <!-- No Items State -->
            <tr v-else-if="!filteredInvoices.length && !filteredPayments.length && !filteredJournals.length">
              <td colspan="7" class="px-6 py-12 text-center text-[var(--color-text-muted)]">No outstanding or unlinked items found.</td>
            </tr>

            <!-- Outstanding Invoices Section -->
            <template v-if="filteredInvoices.length">
              <tr class="bg-[var(--color-danger)]/5 sticky top-[56px] z-[5]">
                <td colspan="7" class="px-4 py-2 border-y border-[var(--color-danger)]/10">
                  <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-danger)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-danger)]"></span>
                    Outstanding Invoices / Returns
                  </h3>
                </td>
              </tr>
              <tr v-for="inv in filteredInvoices" :key="inv.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">{{ inv.name }}</td>
                <td class="px-4 py-3 text-2xl text-[var(--color-text-muted)]">{{ inv.doctype }}</td>
                <td class="px-4 py-3 text-2xl font-bold" :class="calculateDueDays(inv.posting_date) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                  {{ calculateDueDays(inv.posting_date) }} Days
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-xl font-normal uppercase"
                    :class="inv.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'"
                  >{{ inv.direction }}</span>
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal" :class="inv.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ fmt(inv.outstanding_amount) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[inv.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(inv.outstanding_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[inv.name] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl font-black text-right text-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-25 disabled:grayscale disabled:cursor-not-allowed"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(inv, 'invoice')"
                  />
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-bold opacity-60">
                  {{ fmt(Math.abs(inv.outstanding_amount) - (localModalAmounts[inv.name] || 0)) }}
                </td>
              </tr>
            </template>

            <!-- Unlinked Payments Section -->
            <template v-if="filteredPayments.length">
              <tr class="bg-[var(--color-success)]/5 sticky top-[56px] z-[5]">
                <td colspan="7" class="px-4 py-2 border-y border-[var(--color-success)]/10">
                  <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-success)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-success)]"></span>
                    Unlinked Payments (Advances)
                  </h3>
                </td>
              </tr>
              <tr v-for="pe in filteredPayments" :key="pe.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">{{ pe.name }}</td>
                <td class="px-4 py-3 text-2xl text-[var(--color-text-muted)]">Payment Entry</td>
                <td class="px-4 py-3 text-2xl font-bold" :class="calculateDueDays(pe.posting_date) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                  {{ calculateDueDays(pe.posting_date) }} Days
                </td>
                <td class="px-4 py-3 text-center text-2xl">{{ pe.mode_of_payment }}</td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal text-[var(--color-success)]">{{ fmt(pe.unallocated_amount) }}</td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[pe.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(pe.unallocated_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[pe.name] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl font-black text-right text-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-25 disabled:grayscale disabled:cursor-not-allowed"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(pe, 'payment')"
                  />
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-bold opacity-60">
                  {{ fmt(Math.abs(pe.unallocated_amount) - (localModalAmounts[pe.name] || 0)) }}
                </td>
              </tr>
            </template>

            <!-- Unlinked Journal Entries Section -->
            <template v-if="filteredJournals.length">
              <tr class="bg-[var(--color-info)]/5 sticky top-[56px] z-[5]">
                <td colspan="7" class="px-4 py-2 border-y border-[var(--color-info)]/10">
                  <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-info)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-info)]"></span>
                    Unlinked Journal Entries
                  </h3>
                </td>
              </tr>
              <tr v-for="je in filteredJournals" :key="je.reference_row" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">
                  {{ je.name }}
                  <div class="text-xl font-normal text-[var(--color-text-muted)] truncate max-w-[200px]">{{ je.remarks }}</div>
                </td>
                <td class="px-4 py-3 text-2xl text-[var(--color-text-muted)]">Journal Entry</td>
                <td class="px-4 py-3 text-2xl font-bold" :class="calculateDueDays(je.posting_date) > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                  {{ calculateDueDays(je.posting_date) }} Days
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-xl font-normal uppercase"
                    :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'"
                  >{{ je.direction }}</span>
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal"
                    :class="je.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ fmt(je.unallocated_amount) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[je.reference_row]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(je.unallocated_amount)"
                    :disabled="remainingBalance <= 0.005 && !(localModalAmounts[je.reference_row] > 0)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl font-black text-right text-[var(--color-highlight)] focus:ring-4 focus:ring-[var(--color-highlight)]/10 focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-25 disabled:grayscale disabled:cursor-not-allowed"
                    @keydown.enter="focusNextAllocate($event)"
                    @input="onAllocationChange(je, 'journal')"
                  />
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-bold opacity-60">
                  {{ fmt(Math.abs(je.unallocated_amount) - (localModalAmounts[je.reference_row] || 0)) }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      
      <div class="mt-8 flex justify-end gap-6">
        <button
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

const filteredJournals = computed(() => {
  if (filterDirection.value === 'All') return props.unlinkedJournals
  return props.unlinkedJournals.filter(j => j.direction === filterDirection.value)
})

const filteredPayments = computed(() => {
  if (filterDirection.value === 'All') return props.unlinkedPayments
  return props.unlinkedPayments.filter(p => {
    const direction = p.payment_type === 'Receive' ? 'Cr' : 'Dr'
    return direction === filterDirection.value
  })
})

const filteredInvoices = computed(() => {
  if (filterDirection.value === 'All') return props.invoices
  return props.invoices.filter(i => i.direction === filterDirection.value)
})

function onAllocationChange(item, type) {
  const key = type === 'journal' ? item.reference_row : item.name
  lastModifiedKey.value = key
  
  emitAllocations()
}

function emitAllocations() {
  const allInvoices = props.invoices.map(i => ({
    reference_doctype: i.doctype,
    reference_name: i.name,
    total_amount: i.grand_total,
    outstanding_amount: Math.abs(i.outstanding_amount),
    allocated_amount: parseFloat(localModalAmounts.value[i.name]) || 0
  }))

  const allPayments = props.unlinkedPayments.map(p => ({
    reference_doctype: 'Payment Entry',
    reference_name: p.name,
    total_amount: p.unallocated_amount,
    outstanding_amount: Math.abs(p.unallocated_amount),
    allocated_amount: parseFloat(localModalAmounts.value[p.name]) || 0
  }))

  const allJournals = props.unlinkedJournals.map(j => ({
    reference_doctype: 'Journal Entry',
    reference_name: j.name,
    total_amount: j.unallocated_amount,
    outstanding_amount: Math.abs(j.unallocated_amount),
    allocated_amount: parseFloat(localModalAmounts.value[j.reference_row]) || 0,
    _row: j.reference_row
  }))

  const allocations = [...allInvoices, ...allPayments, ...allJournals].filter(a => a.allocated_amount > 0)
  
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
      localModalAmounts.value[targetKey] = (parseFloat(localModalAmounts.value[targetKey]) || 0) + remainingBalance.value
      emitAllocations()
    }
  }
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
  const inputs = Array.from(document.querySelectorAll('.allocate-input'))
  const index = inputs.indexOf(currentInput)
  if (index >= 0 && index < inputs.length - 1) {
    inputs[index + 1].focus()
    inputs[index + 1].select()
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
