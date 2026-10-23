<template>
  <div class="fixed bottom-3 left-3 z-[10000] text-xs font-bold">
    <div
      v-if="open"
      class="mb-2 w-64 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-xl text-[var(--color-text)]"
    >
      <div class="mb-2 flex items-center justify-between">
        <span class="uppercase tracking-widest text-[var(--color-text-muted)]">Confetti (dev)</span>
        <button class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]" @click="reset">Reset</button>
      </div>
      <label v-for="f in FIELDS" :key="f.key" class="mb-1.5 block">
        <div class="flex justify-between">
          <span>{{ f.label }}</span>
          <span class="tabular-nums text-[var(--color-text-muted)]">{{ opts[f.key] }}</span>
        </div>
        <input v-model.number="opts[f.key]" type="range" :min="f.min" :max="f.max" :step="f.step" class="w-full" />
      </label>
      <pre class="mt-2 whitespace-pre-wrap break-all rounded bg-[var(--color-surface-raised)] p-1.5 font-mono font-normal">{{ snippet }}</pre>
    </div>
    <div class="flex gap-1.5">
      <button
        class="rounded-lg bg-[var(--color-highlight)] px-3 py-1.5 text-[var(--color-text-on-highlight)] shadow active:scale-95"
        @click="fireConfetti({ ...opts })"
      >
        🎉 Test confetti
      </button>
      <button
        class="rounded-lg bg-[var(--color-success)] px-3 py-1.5 text-white shadow active:scale-95"
        @click="emit('mock-upi')"
      >
        Mock UPI
      </button>
      <button
        class="rounded-lg bg-[var(--color-surface-raised)] px-2.5 py-1.5 text-[var(--color-text)] shadow"
        @click="open = !open"
      >
        {{ open ? '▾' : '⚙' }}
      </button>
    </div>
  </div>
</template>

<script setup>
// Dev-only playground for tuning fireConfetti(); CashierDesk loads it only when import.meta.env.DEV
import { ref, reactive, computed } from 'vue'
import { fireConfetti } from '../utils/confetti'

const emit = defineEmits(['mock-upi'])

const DEFAULTS = { count: 160, duration: 2500, speed: 9, spread: 0.9, size: 6, gravity: 0.25, drag: 0.99 }
const FIELDS = [
  { key: 'count', label: 'Count', min: 10, max: 600, step: 10 },
  { key: 'duration', label: 'Duration (ms)', min: 500, max: 8000, step: 100 },
  { key: 'speed', label: 'Speed', min: 2, max: 25, step: 0.5 },
  { key: 'spread', label: 'Spread (rad)', min: 0, max: 3, step: 0.05 },
  { key: 'size', label: 'Size (px)', min: 2, max: 20, step: 1 },
  { key: 'gravity', label: 'Gravity', min: 0, max: 1, step: 0.01 },
  { key: 'drag', label: 'Drag', min: 0.9, max: 1, step: 0.001 },
]

const open = ref(false)
const opts = reactive({ ...DEFAULTS })

// Only values changed from the defaults, ready to paste into a fireConfetti() call
const snippet = computed(() => {
  const changed = Object.entries(opts).filter(([k, v]) => v !== DEFAULTS[k])
  return changed.length ? `fireConfetti({ ${changed.map(([k, v]) => `${k}: ${v}`).join(', ')} })` : 'fireConfetti()'
})

function reset() {
  Object.assign(opts, DEFAULTS)
}
</script>
