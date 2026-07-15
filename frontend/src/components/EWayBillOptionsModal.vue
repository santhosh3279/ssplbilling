<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
    @keydown.esc.prevent="!showPrintModal && emit('close')"
  >
    <div class="flex flex-col bg-[var(--color-bg)] rounded-2xl border border-[var(--color-border)] shadow-2xl overflow-hidden w-[560px]">

      <!-- Header -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <span class="text-2xl font-bold uppercase tracking-tight text-[var(--color-text)]">
          {{ mode === 'cancel' ? 'Cancel E-Way Bill' : 'E-Way Bill Options' }}
        </span>
        <button
          class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition"
          @click="emit('close')"
        >✕</button>
      </header>

      <div class="flex flex-col gap-4 p-6">

        <!-- E-Way Bill number banner -->
        <div class="flex items-center justify-between rounded-xl border border-[var(--color-info)]/30 bg-[var(--color-info)]/10 px-4 py-3">
          <span class="text-lg font-bold uppercase text-[var(--color-text-muted)]">E-Way Bill No</span>
          <span class="font-mono text-3xl font-bold text-[var(--color-info)]">{{ ewaybill }}<template v-if="status"> ({{ status }})</template></span>
        </div>

        <!-- ══════════ MENU MODE ══════════ -->
        <template v-if="mode === 'menu'">
          <div class="grid grid-cols-2 gap-4">
            <button
              ref="printBtnRef"
              @click="openPrint('standard')"
              :disabled="printLoading"
              class="flex flex-col items-center gap-1 rounded-xl border-2 border-[var(--color-info)] bg-[var(--color-info)]/15 px-4 py-5 text-2xl font-bold uppercase text-[var(--color-info)] hover:bg-[var(--color-info)]/30 transition-all active:scale-95 disabled:opacity-50"
            >
              🖨️ Print
              <span class="text-sm font-medium normal-case text-[var(--color-text-muted)]">Standard e-Way Bill</span>
            </button>
            <button
              @click="openPrint('detailed')"
              :disabled="printLoading"
              class="flex flex-col items-center gap-1 rounded-xl border-2 border-[var(--color-info)] bg-[var(--color-info)]/15 px-4 py-5 text-2xl font-bold uppercase text-[var(--color-info)] hover:bg-[var(--color-info)]/30 transition-all active:scale-95 disabled:opacity-50"
            >
              🖨️ Print Detailed
              <span class="text-sm font-medium normal-case text-[var(--color-text-muted)]">With item details</span>
            </button>
          </div>
          <button
            @click="mode = 'cancel'"
            class="flex flex-col items-center gap-1 rounded-xl border-2 border-[var(--color-danger)] bg-[var(--color-danger)]/10 px-4 py-4 text-2xl font-bold uppercase text-[var(--color-danger)] hover:bg-[var(--color-danger)]/20 transition-all active:scale-95"
          >
            ✕ Cancel E-Way Bill
            <span class="text-sm font-medium normal-case text-[var(--color-text-muted)]">Allowed only within 24 hours of generation</span>
          </button>
        </template>

        <!-- ══════════ CANCEL MODE ══════════ -->
        <template v-else>
          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Reason <span class="text-[var(--color-danger)]">*</span></label>
            <select
              ref="reasonRef"
              v-model="cancelForm.reason"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
            >
              <option value="Duplicate">Duplicate</option>
              <option value="Order Cancelled">Order Cancelled</option>
              <option value="Data Entry Mistake">Data Entry Mistake</option>
              <option value="Others">Others</option>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Remark</label>
            <input
              v-model="cancelForm.remark"
              type="text"
              placeholder="Optional remark"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="handleCancelEWayBill"
            />
          </div>

          <p class="rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 px-4 py-3 text-lg text-[var(--color-danger)]">
            ⚠ This cancels the e-Way Bill on the GST portal. It cannot be undone — a new e-Way Bill must be generated if needed.
          </p>
        </template>

      </div>

      <!-- Footer -->
      <footer class="flex justify-end gap-4 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <button
          v-if="mode === 'cancel'"
          @click="mode = 'menu'"
          :disabled="cancelling"
          class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-8 py-3 text-2xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition disabled:opacity-50"
        >Back</button>
        <button
          v-else
          @click="emit('close')"
          class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-8 py-3 text-2xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
        >Close</button>
        <button
          v-if="mode === 'cancel'"
          @click="handleCancelEWayBill"
          :disabled="cancelling"
          class="rounded-xl px-10 py-3 text-2xl font-bold text-white transition-all active:scale-95 disabled:opacity-50"
          :class="cancelling ? 'bg-slate-500' : 'bg-[var(--color-danger)] hover:brightness-110'"
        >
          {{ cancelling ? 'Cancelling...' : 'Confirm Cancellation' }}
        </button>
      </footer>

    </div>

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="ewaybill"
      doctype="e-Waybill Log"
      :initial-template="activePrintTemplate"
      lock-template
      header-label="E-Way Bill"
      @close="showPrintModal = false"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { frappeGet, frappePost } from '../api'
import PrintOptionsModal from './PrintOptionsModal.vue'

const props = defineProps({
  doctype: { type: String, required: true },   // 'Sales Invoice' | 'Quotation'
  docname: { type: String, required: true },
  ewaybill: { type: String, required: true },
  status: { type: String, default: '' },
})

const emit = defineEmits(['close', 'cancelled'])

const mode = ref('menu') // 'menu' | 'cancel'
const cancelling = ref(false)
const printLoading = ref(false)
const showPrintModal = ref(false)
const activePrintTemplate = ref('')
let printTemplates = null // { standard, detailed } — Print Template names, fetched once

const printBtnRef = ref(null)
const reasonRef = ref(null)

const cancelForm = ref({
  reason: 'Data Entry Mistake',
  remark: '',
})

onMounted(() => {
  nextTick(() => printBtnRef.value?.focus())
})

watch(mode, (m) => {
  if (m === 'cancel') nextTick(() => reasonRef.value?.focus())
})

async function openPrint(variant) {
  if (printLoading.value) return
  printLoading.value = true
  try {
    // Ensures the e-Way Bill Print Templates (on e-Waybill Log) exist and returns their names
    if (!printTemplates) {
      printTemplates = await frappeGet('ssplbilling.api.ewaybill_api.get_eway_print_templates')
    }
    activePrintTemplate.value = printTemplates[variant]
    showPrintModal.value = true
  } catch (e) {
    alert(e.message || 'Failed to load e-Way Bill print templates.')
  } finally {
    printLoading.value = false
  }
}

async function handleCancelEWayBill() {
  if (cancelling.value) return
  cancelling.value = true
  try {
    const res = await frappePost('ssplbilling.api.ewaybill_api.cancel_eway_bill', {
      doctype: props.doctype,
      docname: props.docname,
      reason: cancelForm.value.reason,
      remark: cancelForm.value.remark,
    })
    alert(res.message || 'e-Way Bill cancelled successfully.')
    emit('cancelled', res)
  } catch (e) {
    alert(e.message || 'Failed to cancel e-Way Bill.')
  } finally {
    cancelling.value = false
  }
}
</script>
