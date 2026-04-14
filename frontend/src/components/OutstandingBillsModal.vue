<template>
  <div v-if="show" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="w-full max-w-[90vw] rounded-3xl bg-[var(--color-surface)] p-8 shadow-2xl border border-[var(--color-border)]">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-6">
          <h2 class="text-2xl font-normal uppercase tracking-tight">Outstanding & Unlinked Items</h2>
          
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
        <button @click="$emit('close')" class="h-8 w-8 rounded-full hover:bg-[var(--color-midlight)] transition-colors flex items-center justify-center">
          ✕
        </button>
      </div>
      
      <div class="max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar border border-[var(--color-border)] rounded-2xl bg-[var(--color-surface-raised)]/30">
        <table class="w-full text-left">
          <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)] sticky top-0 z-10">
            <tr class="text-3xl font-normal uppercase tracking-widest text-[var(--color-text-muted)]">
              <th class="px-4 py-3">Voucher No</th>
              <th class="px-4 py-3">Type</th>
              <th class="px-4 py-3">Date</th>
              <th class="px-4 py-3 text-center">Dir/Mode</th>
              <th class="px-4 py-3 text-right">Outstanding/Unallocated</th>
              <th class="px-4 py-3 text-right">Allocate</th>
              <th class="px-4 py-3"></th>
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
              <tr class="bg-[var(--color-danger)]/5">
                <td colspan="7" class="px-4 py-2">
                  <h3 class="text-[10px] font-normal uppercase tracking-widest text-[var(--color-danger)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-danger)]"></span>
                    Outstanding Invoices / Returns
                  </h3>
                </td>
              </tr>
              <tr v-for="inv in filteredInvoices" :key="inv.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">{{ inv.name }}</td>
                <td class="px-4 py-3 text-3xl text-[var(--color-text-muted)]">{{ inv.doctype }}</td>
                <td class="px-4 py-3 text-3xl">{{ inv.posting_date }}</td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-2xl font-normal uppercase"
                    :class="inv.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'"
                  >{{ inv.direction }}</span>
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal" :class="inv.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ inv.outstanding_amount.toLocaleString('en-IN') }}
                </td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[inv.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(inv.outstanding_amount)"
                    :disabled="isAlreadyAllocated(inv.name)"
                    class="allocate-input w-44 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1 text-3xl font-normal text-right focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-40"
                    @keydown.enter="focusNextAllocate($event)"
                  />
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    @click="addAllocation(inv, 'invoice')"
                    :disabled="isAlreadyAllocated(inv.name)"
                    class="rounded-lg px-3 py-1 text-2xl font-normal uppercase transition-all whitespace-nowrap"
                    :class="isAlreadyAllocated(inv.name)
                      ? 'bg-[var(--color-success)]/15 text-[var(--color-success)] cursor-not-allowed'
                      : 'bg-[var(--color-highlight)]/10 text-[var(--color-highlight)] hover:bg-[var(--color-highlight)] hover:text-white'"
                  >{{ isAlreadyAllocated(inv.name) ? '✓ Added' : '+ Add' }}</button>
                </td>
              </tr>
            </template>

            <!-- Unlinked Payments Section -->
            <template v-if="filteredPayments.length">
              <tr class="bg-[var(--color-success)]/5">
                <td colspan="7" class="px-4 py-2">
                  <h3 class="text-[10px] font-normal uppercase tracking-widest text-[var(--color-success)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-success)]"></span>
                    Unlinked Payments (Advances)
                  </h3>
                </td>
              </tr>
              <tr v-for="pe in filteredPayments" :key="pe.name" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">{{ pe.name }}</td>
                <td class="px-4 py-3 text-3xl text-[var(--color-text-muted)]">Payment Entry</td>
                <td class="px-4 py-3 text-3xl">{{ pe.posting_date }}</td>
                <td class="px-4 py-3 text-center text-3xl">{{ pe.mode_of_payment }}</td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal text-[var(--color-success)]">{{ pe.unallocated_amount.toLocaleString('en-IN') }}</td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[pe.name]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(pe.unallocated_amount)"
                    :disabled="isAlreadyAllocated(pe.name)"
                    class="allocate-input w-44 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1 text-3xl font-normal text-right focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-40"
                    @keydown.enter="focusNextAllocate($event)"
                  />
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    @click="addAllocation(pe, 'payment')"
                    :disabled="isAlreadyAllocated(pe.name)"
                    class="rounded-lg px-3 py-1 text-2xl font-normal uppercase transition-all whitespace-nowrap"
                    :class="isAlreadyAllocated(pe.name)
                      ? 'bg-[var(--color-success)]/15 text-[var(--color-success)] cursor-not-allowed'
                      : 'bg-[var(--color-highlight)]/10 text-[var(--color-highlight)] hover:bg-[var(--color-highlight)] hover:text-white'"
                  >{{ isAlreadyAllocated(pe.name) ? '✓ Added' : '+ Add' }}</button>
                </td>
              </tr>
            </template>

            <!-- Unlinked Journal Entries Section -->
            <template v-if="filteredJournals.length">
              <tr class="bg-[var(--color-info)]/5">
                <td colspan="7" class="px-4 py-2">
                  <h3 class="text-[10px] font-normal uppercase tracking-widest text-[var(--color-info)] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-info)]"></span>
                    Unlinked Journal Entries
                  </h3>
                </td>
              </tr>
              <tr v-for="je in filteredJournals" :key="je.reference_row" class="hover:bg-[var(--color-midlight)]/50 transition-colors">
                <td class="px-4 py-3 font-mono text-3xl font-normal">
                  {{ je.name }}
                  <div class="text-2xl font-normal text-[var(--color-text-muted)] truncate max-w-[160px]">{{ je.remarks }}</div>
                </td>
                <td class="px-4 py-3 text-3xl text-[var(--color-text-muted)]">Journal Entry</td>
                <td class="px-4 py-3 text-3xl">{{ je.posting_date }}</td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="inline-block rounded px-2 py-0.5 text-2xl font-normal uppercase"
                    :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'"
                  >{{ je.direction }}</span>
                </td>
                <td class="px-4 py-3 text-right font-mono text-3xl font-normal"
                    :class="je.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ je.unallocated_amount.toLocaleString('en-IN') }}
                </td>
                <td class="px-4 py-3 text-right">
                  <input
                    v-model.number="localModalAmounts[je.reference_row]"
                    type="number" step="0.01" min="0"
                    :max="Math.abs(je.unallocated_amount)"
                    :disabled="isAlreadyAllocated(je.name, je.reference_row)"
                    class="allocate-input w-44 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1 text-3xl font-normal text-right focus:border-[var(--color-highlight)] focus:outline-none transition-all disabled:opacity-40"
                    @keydown.enter="focusNextAllocate($event)"
                  />
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    @click="addAllocation(je, 'journal')"
                    :disabled="isAlreadyAllocated(je.name, je.reference_row)"
                    class="rounded-lg px-3 py-1 text-2xl font-normal uppercase transition-all whitespace-nowrap"
                    :class="isAlreadyAllocated(je.name, je.reference_row)
                      ? 'bg-[var(--color-success)]/15 text-[var(--color-success)] cursor-not-allowed'
                      : 'bg-[var(--color-highlight)]/10 text-[var(--color-highlight)] hover:bg-[var(--color-highlight)] hover:text-white'"
                  >{{ isAlreadyAllocated(je.name, je.reference_row) ? '✓ Added' : '+ Add' }}</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      
      <div class="mt-8 flex justify-end">
        <button @click="$emit('close')" class="rounded-xl bg-[var(--color-highlight)] px-8 py-2.5 text-base font-normal text-white hover:brightness-110 transition-all shadow-lg">
          Close
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

const emit = defineEmits(['close', 'add-allocation'])

const filterDirection = ref('All')
const localModalAmounts = ref({})

// Sync localModalAmounts with prop
watch(() => props.modalAmounts, (newVal) => {
  localModalAmounts.value = { ...newVal }
}, { immediate: true, deep: true })

// Sync back to parent if needed (though we mostly use it for adding)
watch(localModalAmounts, (newVal) => {
  // We don't necessarily need to emit this back unless the parent needs real-time sync
}, { deep: true })

watch(() => props.show, (val) => {
  if (val) {
    filterDirection.value = props.activeTab === 'Receipt' ? 'Dr' : 'Cr'
    nextTick(() => {
      setTimeout(() => {
        const firstInput = document.querySelector('.allocate-input:not(:disabled)')
        if (firstInput) {
          firstInput.focus()
          firstInput.select()
        }
      }, 150)
    })
  }
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

function isAlreadyAllocated(name, row) {
  if (row) {
    return !!props.allocationRefs.find(r => r.reference_name === name && r._row === row)
  }
  return !!props.allocationRefs.find(r => r.reference_name === name)
}

function addAllocation(item, type) {
  let allocation = {}
  let amountKey = ''

  if (type === 'invoice') {
    allocation = {
      reference_doctype: item.doctype,
      reference_name: item.name,
      total_amount: item.grand_total,
      outstanding_amount: item.outstanding_amount
    }
    amountKey = item.name
  } else if (type === 'payment') {
    allocation = {
      reference_doctype: 'Payment Entry',
      reference_name: item.name,
      total_amount: item.unallocated_amount,
      outstanding_amount: item.unallocated_amount
    }
    amountKey = item.name
  } else if (type === 'journal') {
    allocation = {
      reference_doctype: 'Journal Entry',
      reference_name: item.name,
      total_amount: item.unallocated_amount,
      outstanding_amount: item.unallocated_amount,
      _row: item.reference_row
    }
    amountKey = item.reference_row
  }

  const allocated_amount = parseFloat(localModalAmounts.value[amountKey]) || Math.abs(allocation.outstanding_amount)
  
  emit('add-allocation', { ...allocation, allocated_amount }, amountKey)
}

function focusNextAllocate(event) {
  const currentInput = event.target
  const inputs = Array.from(document.querySelectorAll('.allocate-input:not(:disabled)'))
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
