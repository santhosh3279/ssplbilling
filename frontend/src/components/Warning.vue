<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @keydown.esc.stop="$emit('close')"
    @keydown.left.prevent="focusBtn('no')"
    @keydown.right.prevent="focusBtn('yes')"
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
          ref="noBtn"
          class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)] outline-none focus:border-[10px] focus:border-[var(--color-focus)]"
          @click="$emit('close')"
        >
          No (Esc)
        </button>
        <button
          ref="yesBtn"
          class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-3 text-xl font-bold text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)] outline-none focus:border-[10px] focus:border-[var(--color-focus)]"
          @click="$emit('confirm')"
        >
          Yes
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
  message: { type: String, default: 'Are you sure you want to proceed?' }
})

const emit = defineEmits(['close', 'confirm'])

const noBtn = ref(null)
const yesBtn = ref(null)

function focusBtn(type) {
  if (type === 'no') noBtn.value?.focus()
  else yesBtn.value?.focus()
}

watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      noBtn.value?.focus()
    })
  }
})
</script>
