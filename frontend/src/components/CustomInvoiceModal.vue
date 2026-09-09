<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
    @click.self="close"
    @keydown.esc="close"
  >
    <div
      class="w-full max-w-md overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl animate-in zoom-in duration-150"
    >
      <!-- Modal Header -->
      <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg)] px-6 py-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xl">🏷️</span>
            <h3 class="text-lg font-bold text-[var(--color-text)]">Custom Invoice Number</h3>
          </div>
          <p class="text-xs text-[var(--color-text-muted)] font-medium mt-0.5">
            Generate invoice with a specific custom number
          </p>
        </div>
        <button
          type="button"
          @click="close"
          class="rounded-lg p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 space-y-4">
        <!-- Series info pill -->
        <div v-if="series" class="flex items-center justify-between rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] px-4 py-2.5">
          <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Active Series</span>
          <span class="font-mono text-sm font-bold text-[var(--color-highlight)]">{{ series }}</span>
        </div>

        <!-- Input Section -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-xs font-bold uppercase tracking-wider text-[var(--color-text)]">
              Invoice Number
            </label>
            <span
              class="font-mono text-xs font-bold"
              :class="invoiceInput.length > 16 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'"
            >
              {{ invoiceInput.length }} / 16
            </span>
          </div>

          <div class="relative">
            <input
              ref="inputRef"
              v-model="invoiceInput"
              type="text"
              maxlength="20"
              placeholder="e.g. CTRG08450"
              class="w-full rounded-xl border-2 bg-[var(--color-bg)] px-4 py-3 text-2xl font-mono font-bold tracking-wider text-[var(--color-text)] outline-none transition-all uppercase placeholder:normal-case placeholder:font-sans placeholder:font-normal placeholder:text-base placeholder:text-[var(--color-text-muted)]/50"
              :class="inputBorderClass"
              @input="onInputChange"
              @keydown.enter.prevent="submit"
              @keydown.esc.prevent="close"
            />
            <div v-if="checking" class="absolute right-3.5 top-1/2 -translate-y-1/2">
              <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent"></div>
            </div>
          </div>

          <!-- Helper / Validation Messages -->
          <div class="mt-2 min-h-[20px] text-xs">
            <p v-if="invoiceInput.length > 16" class="text-[var(--color-danger)] font-medium flex items-center gap-1">
              <span>⚠️</span> Maximum 16 characters allowed for GST compliance
            </p>
            <p v-else-if="!isValidFormat && invoiceInput.length > 0" class="text-[var(--color-danger)] font-medium flex items-center gap-1">
              <span>⚠️</span> Must start with alphanumeric and only use letters, digits, '-' or '/'
            </p>
            <p v-else-if="exists" class="text-[var(--color-danger)] font-bold flex items-center gap-1">
              <span>❌</span> Invoice <span class="font-mono underline">{{ invoiceInput }}</span> already exists in database
            </p>
            <p v-else-if="invoiceInput.length > 0 && !checking && isValidFormat" class="text-[var(--color-success)] font-medium flex items-center gap-1">
              <span>✓</span> Invoice number is available
            </p>
            <p v-else class="text-[var(--color-text-muted)]">
              Enter the exact invoice number to generate. Letters, digits, '-' and '/' allowed.
            </p>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-bg)] px-6 py-3.5">
        <div>
          <button
            v-if="currentCustomNo"
            type="button"
            @click="resetToAuto"
            class="rounded-lg px-3 py-2 text-xs font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 transition-colors flex items-center gap-1.5"
            title="Clear custom number and revert to automatic series numbering"
          >
            <span>↺</span> Reset to Auto Series
          </button>
        </div>

        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="close"
            class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors"
          >
            Cancel (Esc)
          </button>
          <button
            type="button"
            @click="submit"
            :disabled="!canSubmit"
            class="rounded-lg bg-[var(--color-highlight)] px-5 py-2 text-xs font-black uppercase tracking-wider text-[var(--color-text-on-highlight)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md active:scale-95"
          >
            Apply Number
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { frappeGet } from '../api'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: { type: Boolean, default: false },
  series: { type: String, default: '' },
  currentCustomNo: { type: String, default: '' },
  suggestedNo: { type: String, default: '' }
})

const emit = defineEmits(['close', 'apply', 'reset'])

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: close
})

const inputRef = ref(null)
const invoiceInput = ref('')
const checking = ref(false)
const exists = ref(false)

const GST_FORMAT = /^[a-zA-Z0-9][a-zA-Z0-9\-\/]*$/

const isValidFormat = computed(() => {
  if (!invoiceInput.value) return false
  return GST_FORMAT.test(invoiceInput.value)
})

const canSubmit = computed(() => {
  return (
    invoiceInput.value.length > 0 &&
    invoiceInput.value.length <= 16 &&
    isValidFormat.value &&
    !exists.value &&
    !checking.value
  )
})

const inputBorderClass = computed(() => {
  if (invoiceInput.value.length > 16 || (!isValidFormat.value && invoiceInput.value.length > 0) || exists.value) {
    return 'border-[var(--color-danger)] focus:border-[var(--color-danger)]'
  }
  if (invoiceInput.value.length > 0 && !checking.value && isValidFormat.value) {
    return 'border-[var(--color-success)] focus:border-[var(--color-success)]'
  }
  return 'border-[var(--color-border)] focus:border-[var(--color-focus)]'
})

let checkTimeout = null

function onInputChange() {
  invoiceInput.value = invoiceInput.value.toUpperCase().replace(/\s+/g, '')
  exists.value = false
  if (checkTimeout) clearTimeout(checkTimeout)

  if (!invoiceInput.value || !isValidFormat.value || invoiceInput.value.length > 16) {
    checking.value = false
    return
  }

  checking.value = true
  checkTimeout = setTimeout(async () => {
    try {
      const res = await frappeGet('ssplbilling.api.sales.check_invoice_exists', {
        invoice_name: invoiceInput.value
      })
      exists.value = !!res?.exists
    } catch (e) {
      console.error('[CustomInvoiceModal] check failed:', e)
    } finally {
      checking.value = false
    }
  }, 250)
}

function initModal() {
  const initial = props.currentCustomNo || props.suggestedNo || ''
  invoiceInput.value = initial.trim().toUpperCase().replace(/\s+/g, '')
  exists.value = false
  checking.value = false
  nextTick(() => {
    inputRef.value?.focus()
    inputRef.value?.select()
  })
  if (invoiceInput.value && isValidFormat.value && invoiceInput.value.length <= 16) {
    onInputChange()
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    initModal()
  }
})

function close() {
  emit('close')
}

function resetToAuto() {
  emit('reset')
  close()
}

function submit() {
  if (!canSubmit.value) return
  emit('apply', invoiceInput.value.trim().toUpperCase())
  close()
}
</script>
