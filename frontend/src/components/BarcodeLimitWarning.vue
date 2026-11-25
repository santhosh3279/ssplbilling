<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @keydown.left.prevent="cancelBtn?.focus()"
    @keydown.right.prevent="printBtn?.focus()"
    @keydown.tab.prevent="toggleFocus"
  >
    <div
      role="alertdialog"
      aria-modal="true"
      class="flex max-h-[85vh] w-[600px] flex-col rounded-2xl border-[10px] border-[color-mix(in_srgb,var(--color-danger)_70%,black_30%)] bg-[color-mix(in_srgb,var(--color-bg)_70%,var(--color-danger)_30%)] p-8 shadow-2xl"
    >
      <h3 class="text-center text-2xl font-bold text-[var(--color-text)]">⚠️ Barcode Sticker Limit Exceeded</h3>

      <div class="mt-5 grid grid-cols-3 gap-3 text-center">
        <div v-for="s in summary" :key="s.label" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
          <div class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">{{ s.label }}</div>
          <div class="mt-1 font-mono text-3xl font-black" :class="s.over ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'">{{ s.value }}</div>
        </div>
      </div>

      <div v-if="overItems.length" class="mt-4 min-h-0 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div
          v-for="(item, i) in overItems"
          :key="i"
          class="flex items-center justify-between gap-4 border-b border-[var(--color-border)] px-4 py-2 text-lg last:border-b-0"
        >
          <span class="min-w-0 break-words text-[var(--color-text)]">{{ item.item_name || item.item_code }}</span>
          <span class="shrink-0 font-mono font-bold text-[var(--color-danger)]">{{ item.qty }}</span>
        </div>
      </div>
      <p v-else class="mt-4 text-center text-lg text-[var(--color-text-muted)]">
        No single item is above the limit, but the total is.
      </p>

      <div class="mt-6 flex gap-4">
        <button ref="cancelBtn" :class="btnClass" @click="$emit('close')">Cancel (Esc)</button>
        <button ref="printBtn" :class="btnClass" @click="$emit('confirm')">Print Anyway</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  limit: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  // Rows whose own sticker count is above the limit
  overItems: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'confirm'])

const btnClass = 'flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] outline-none hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]'

const cancelBtn = ref(null)
const printBtn = ref(null)

const summary = computed(() => [
  { label: 'Limit', value: props.limit },
  { label: 'Total stickers', value: props.total, over: props.total > props.limit },
  { label: 'Items above limit', value: props.overItems.length, over: props.overItems.length > 0 },
])

function toggleFocus() {
  const next = document.activeElement === cancelBtn.value ? printBtn.value : cancelBtn.value
  next?.focus()
}

// Top shortcut layer while open, so Esc closes this window and not the barcode page
useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

watch(() => props.show, val => {
  if (val) nextTick(() => cancelBtn.value?.focus())
})
</script>
