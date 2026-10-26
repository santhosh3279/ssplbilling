<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
  >
    <div class="w-[720px] max-w-[95vw] bg-[var(--color-bg)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="px-[20px] py-[12px] bg-[var(--color-surface)] border-b border-[var(--color-border)] flex justify-between items-center">
        <div>
          <h3 class="text-4xl font-bold text-[var(--color-text)]">New Batch</h3>
          <p class="text-2xl text-[var(--color-text-muted)]">{{ itemCode }} — {{ itemName }}</p>
        </div>
        <button
          type="button"
          @click="$emit('close')"
          class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors px-[16px] py-[8px] hover:bg-[var(--color-surface-raised)] rounded-full text-4xl leading-none"
          aria-label="Close"
        >&times;</button>
      </div>

      <!-- Form -->
      <div class="px-[20px] py-[16px] space-y-[16px]">
        <div class="space-y-[4px]">
          <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">
            Batch ID{{ createNewBatch ? '' : ' *' }}
          </label>
          <input
            ref="batchIdInput"
            v-model="form.batch_id"
            type="text"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] font-mono text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
            :placeholder="createNewBatch ? 'Blank = next number from the series' : 'Enter batch number...'"
          />
        </div>

        <div class="grid grid-cols-2 gap-[16px]">
          <div class="space-y-[4px]">
            <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Mfg Date</label>
            <input
              v-model="form.manufacturing_date"
              type="date"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
            />
          </div>
          <div class="space-y-[4px]">
            <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Expiry Date</label>
            <input
              v-model="form.expiry_date"
              type="date"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
            />
            <p v-if="hasExpiryDate && shelfLifeInDays && !form.expiry_date" class="px-[20px] text-xl text-[var(--color-text-muted)]">
              Blank = Mfg Date + {{ shelfLifeInDays }} days
            </p>
          </div>
        </div>

        <p v-if="supplier" class="px-[20px] text-xl text-[var(--color-text-muted)]">Supplier: {{ supplier }}</p>
        <p v-if="error" class="px-[20px] text-2xl font-bold text-[var(--color-danger)]">{{ error }}</p>
      </div>

      <!-- Footer -->
      <div class="px-[20px] py-[12px] bg-[var(--color-surface)] border-t border-[var(--color-border)] flex gap-[8px]">
        <button
          type="button"
          @click="$emit('close')"
          class="flex-1 rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] border border-[var(--color-border)] hover:bg-[var(--color-midlight)] transition-all active:scale-95"
        >Cancel</button>
        <button
          type="button"
          @click="save"
          :disabled="!canSave || isSaving"
          class="flex-[2] rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] bg-[var(--color-info)] hover:bg-[var(--color-info)]/80 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
        >
          {{ isSaving ? 'Creating…' : 'Create Batch' }}
          <kbd class="ml-1 rounded border border-current px-1.5 py-0.5 font-mono text-xl opacity-70">Enter</kbd>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { frappePost } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { serverToday } from '../services/serverTime'

const props = defineProps({
  show: Boolean,
  itemCode: { type: String, required: true },
  itemName: { type: String, default: '' },
  supplier: { type: String, default: '' },
  // Item settings: without auto-create the batch ID must be typed
  createNewBatch: { type: [Number, Boolean], default: 0 },
  hasExpiryDate: { type: [Number, Boolean], default: 0 },
  shelfLifeInDays: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'created'])

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close'),
  ENTER: () => save(),
  END: () => save(),
})

const batchIdInput = ref(null)
const form = ref({ batch_id: '', manufacturing_date: '', expiry_date: '' })
const error = ref('')
const isSaving = ref(false)

const canSave = computed(() => !!props.createNewBatch || !!form.value.batch_id.trim())

async function save() {
  if (!canSave.value || isSaving.value) return
  if (form.value.expiry_date && form.value.manufacturing_date && form.value.expiry_date < form.value.manufacturing_date) {
    error.value = 'Expiry Date is before Mfg Date'
    return
  }
  error.value = ''
  isSaving.value = true
  try {
    const batch = await frappePost('ssplbilling.api.batch_api.create_batch', {
      item_code: props.itemCode,
      batch_id: form.value.batch_id.trim(),
      manufacturing_date: form.value.manufacturing_date,
      expiry_date: form.value.expiry_date,
      supplier: props.supplier,
    }, { silent: true })
    emit('created', batch)
  } catch (e) {
    error.value = e.message || 'Failed to create batch'
  } finally {
    isSaving.value = false
  }
}

watch(() => props.show, (open) => {
  if (!open) return
  form.value = { batch_id: '', manufacturing_date: serverToday(), expiry_date: '' }
  error.value = ''
  nextTick(() => batchIdInput.value?.focus())
}, { immediate: true })
</script>
