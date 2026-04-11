<template>
  <transition name="fade">
    <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center bg-[var(--color-bg)]/80 backdrop-blur-sm p-4">
      <div class="flex w-full max-w-[80vw] flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl overflow-hidden max-h-[90vh]">
        <!-- Modal Header -->
        <div class="p-6 border-b border-[var(--color-border)] bg-[var(--color-surface)]/30 flex items-center justify-between">
          <div>
            <h3 class="text-xs font-black uppercase tracking-[0.2em] text-[var(--color-info)] flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              Payment Reconciliation
            </h3>
            <p class="mt-1 text-[10px] font-bold text-[var(--color-text-muted)] uppercase">Adjust pending ledger cash for this bill</p>
          </div>
          <button @click="$emit('close')" class="h-8 w-8 rounded-full flex items-center justify-center hover:bg-[var(--color-surface-raised)] transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)]"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
          <!-- Already Allocated Section -->
          <div v-if="invoice?.advances && invoice.advances.length > 0" class="space-y-2">
            <h4 class="text-[15px] font-black uppercase tracking-widest text-[var(--color-text-muted)] px-3">Previously Allocated</h4>
            <div v-for="adv in invoice.advances" :key="adv.reference_name" class="rounded-xl border border-[var(--color-info)]/20 bg-[var(--color-info)]/10 px-6 py-2.5 flex items-center justify-between gap-8">
              <div class="flex items-center gap-6 flex-1">
                <span class="text-lg font-black text-[var(--color-info)] min-w-[180px]">{{ adv.reference_name }}</span>
                <span class="text-[12px] font-bold text-[var(--color-text-muted)] uppercase italic">Already adjusted in this invoice</span>
              </div>
              <span class="text-2xl font-black text-[var(--color-text)] font-mono">₹{{ fmt(adv.allocated_amount) }}</span>
            </div>
          </div>

          <!-- Unallocated Section -->
          <div v-if="localUnallocated.length > 0" class="space-y-2">
            <h4 class="text-[15px] font-black uppercase tracking-widest text-amber-500 px-3">Available Unallocated Cash</h4>
            <div v-for="(pe, index) in localUnallocated" :key="pe.name" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 shadow-sm flex items-center gap-8 group hover:border-[var(--color-focus)]/50 transition-colors">
              <!-- Name & Date -->
              <div class="flex items-center gap-6 min-w-[280px]">
                <div class="text-lg font-black text-[var(--color-text)] truncate">{{ pe.name }}</div>
                <div class="text-[12px] font-bold text-[var(--color-text-muted)] uppercase whitespace-nowrap">{{ formatDate(pe.posting_date) }}</div>
              </div>

              <!-- Mode & Balance -->
              <div class="flex items-center gap-6 flex-1">
                <div class="px-3 py-1 rounded bg-[var(--color-surface-raised)] text-[11px] font-black text-[var(--color-text-muted)] uppercase whitespace-nowrap">{{ pe.mode_of_payment }}</div>
                <div class="flex items-center gap-3">
                  <span class="text-[12px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">Balance</span>
                  <span class="text-2xl font-black text-[var(--color-success)] font-mono">₹{{ fmt(pe.unallocated_amount) }}</span>
                </div>
              </div>
              
              <!-- Adjust Input -->
              <div class="flex items-center gap-4">
                <div class="text-[15px] font-black text-[var(--color-text-muted)] uppercase tracking-widest">Adjust</div>
                <div class="w-48 relative">
                  <input
                    :ref="el => allocationInputs[index] = el"
                    type="number"
                    v-model.number="pe.amount_to_allocate"
                    @focus="$event.target.select()"
                    class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-4 text-right font-mono text-2xl font-black text-[var(--color-info)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10 transition-all outline-none"
                    @keydown.enter="focusNextAllocation(index)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="p-6 border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 space-y-4">
          <div class="flex justify-between items-center px-2">
            <span class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)]">Total to Adjust</span>
            <span class="text-2xl font-black text-[var(--color-info)] font-mono">₹{{ fmt(totalAmountToAllocate) }}</span>
          </div>

          <button
            ref="allocateButton"
            @click="submit"
            :disabled="!totalAmountToAllocate || isSubmitting"
            class="w-full rounded-2xl bg-[var(--color-highlight)] py-4 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-[var(--color-focus)]/40 hover:bg-[var(--color-highlight)] active:scale-95 disabled:opacity-30 transition-all flex items-center justify-center gap-3"
          >
            <span v-if="isSubmitting">Applying...</span>
            <template v-else>
              <span>Confirm & Apply Adjustments</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </template>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { frappePost } from '../api'

const props = defineProps({
  show: Boolean,
  invoice: Object,
  unallocated: Array
})

const emit = defineEmits(['close', 'success'])

const localUnallocated = ref([])
const isSubmitting = ref(false)
const allocationInputs = ref([])
const allocateButton = ref(null)

// Sync local state when props change
watch(() => props.unallocated, (newVal) => {
  localUnallocated.value = JSON.parse(JSON.stringify(newVal || []))
}, { immediate: true })

const totalAmountToAllocate = computed(() => {
  return localUnallocated.value.reduce((acc, p) => acc + (Number(p.amount_to_allocate) || 0), 0)
})

function focusNextAllocation(index) {
  if (index + 1 < localUnallocated.value.length) {
    allocationInputs.value[index + 1]?.focus()
    allocationInputs.value[index + 1]?.select()
  } else {
    allocateButton.value?.focus()
  }
}

async function submit() {
  if (totalAmountToAllocate.value <= 0) {
    emit('success', { outstanding: props.invoice.outstanding_amount, advances: [] })
    return
  }

  isSubmitting.value = true
  try {
    const allocations = localUnallocated.value
      .filter(p => (Number(p.amount_to_allocate) || 0) > 0.005)
      .map(p => ({
        reference_name: p.name,
        reference_row: p.reference_row,
        reference_type: p.reference_type,
        allocated_amount: p.amount_to_allocate
      }))

    if (allocations.length === 0) {
      emit('success', { outstanding: props.invoice.outstanding_amount, advances: [] })
      return
    }

    const res = await frappePost('ssplbilling.api.cashier_api.update_invoice_advances', {
      invoice_name: props.invoice.name,
      allocations: allocations
    })

    if (res.status === 'success') {
      emit('success', res)
    }
  } catch (e) {
    alert("Allocation failed: " + e.message)
  } finally {
    isSubmitting.value = false
  }
}

function fmt(val) {
  return Math.round(Number(val || 0)).toLocaleString('en-IN')
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}
</script>
