<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @keydown.esc.stop="$emit('close')"
    @keydown.left.prevent="moveFocus(-1)"
    @keydown.right.prevent="moveFocus(1)"
  >
    <div class="w-[450px] rounded-2xl border-[10px] border-[color-mix(in_srgb,var(--color-danger)_70%,black_30%)] bg-[color-mix(in_srgb,var(--color-bg)_70%,var(--color-danger)_30%)] p-8 shadow-2xl">
      <div class="mb-6 flex flex-col items-center text-center">
        <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-warning)]/30 text-4xl text-[var(--color-warning)] shadow-[0_0_20px_rgba(245,158,11,0.2)]">
          ⚠️
        </div>
        <h3 class="text-2xl font-bold text-[var(--color-text)]">{{ title }}</h3>
        <p class="mt-2 text-lg text-[var(--color-text-muted)] leading-relaxed">{{ message }}</p>
      </div>

      <div class="flex gap-4">
        <button
          v-if="extraLabel"
          ref="extraBtn"
          class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)] outline-none focus:border-[10px] focus:border-[var(--color-focus)]"
          @click="$emit('extra')"
        >
          {{ extraLabel }}
        </button>
        <button
          ref="noBtn"
          class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)] outline-none focus:border-[10px] focus:border-[var(--color-focus)]"
          @click="$emit('close')"
        >
          {{ cancelLabel }}
        </button>
        <button
          ref="yesBtn"
          class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)] outline-none focus:border-[10px] focus:border-[var(--color-focus)]"
          @click="$emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
      
      <div class="mt-6 text-center text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] font-bold">
        Use <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text-muted)]">← →</kbd> to toggle
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Confirm Action' },
  message: { type: String, default: 'Are you sure you want to proceed?' },
  cancelLabel: { type: String, default: 'No (Esc)' },
  confirmLabel: { type: String, default: 'Yes' },
  // Optional middle button; hidden unless a label is given
  extraLabel: { type: String, default: '' }
})

const emit = defineEmits(['close', 'confirm', 'extra'])

const noBtn = ref(null)
const extraBtn = ref(null)
const yesBtn = ref(null)

function moveFocus(dir) {
  const btns = [extraBtn.value, noBtn.value, yesBtn.value].filter(Boolean)
  // Unfocused: step from No (the default)
  let cur = btns.indexOf(document.activeElement)
  if (cur === -1) cur = btns.indexOf(noBtn.value)
  const next = Math.min(Math.max(cur + dir, 0), btns.length - 1)
  btns[next]?.focus()
}

watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      noBtn.value?.focus()
    })
  }
})
</script>
