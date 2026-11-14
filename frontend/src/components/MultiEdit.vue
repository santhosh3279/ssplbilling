<template>
  <div
    v-if="show"
    data-testid="multi-edit"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @mousedown.self="$emit('close')"
  >
    <div class="w-[460px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl">
      <div class="mb-5 flex items-start justify-between">
        <div class="mr-4 flex-1">
          <h2 class="text-2xl font-bold text-[var(--color-text)]">Multi Edit</h2>
          <p class="text-left text-xs font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
            Ticked = removed from this bill · untick to bring back
          </p>
        </div>
        <button
          type="button"
          class="text-2xl text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text)] focus:outline-none"
          aria-label="Close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div v-if="!options.length" class="py-8 text-center text-sm text-[var(--color-text-muted)]">
        No rows on this bill.
      </div>

      <div v-else class="flex flex-col gap-2">
        <label
          v-for="(opt, i) in options"
          :key="opt.key"
          :data-testid="`tax-cleanup-${opt.key}`"
          class="flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-2.5 transition-colors"
          :class="checked.includes(opt.key)
            ? 'border-[var(--color-danger)] bg-[var(--color-danger)]/15 text-[var(--color-danger)]'
            : 'border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]'"
        >
          <kbd class="w-6 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-center text-xs text-[var(--color-text-muted)]">{{ i + 1 }}</kbd>
          <input
            type="checkbox"
            :checked="checked.includes(opt.key)"
            class="h-5 w-5 rounded accent-[var(--color-danger)]"
            @change="$emit('toggle', opt.key, $event.target.checked)"
          />
          <span class="flex-1 text-lg font-bold uppercase" :class="checked.includes(opt.key) ? 'line-through' : ''">{{ opt.label }}</span>
          <span v-if="checked.includes(opt.key)" class="rounded bg-[var(--color-danger)] px-1.5 text-[10px] font-bold uppercase text-white">Removed</span>
          <span data-testid="tax-cleanup-count" class="font-mono text-sm text-[var(--color-text-muted)]">{{ opt.count }} row{{ opt.count === 1 ? '' : 's' }}</span>
        </label>
      </div>

      <div class="mt-5 flex gap-3 text-[10px] font-medium text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">1-9</kbd> Remove / bring back</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Enter</kbd> / <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Esc</kbd> Close</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  // Rows Multi Edit works on (on the bill, or removed by Multi Edit): [{ keys }], where keys
  // are 'gst' / 'nongst' and 'rate:<n>' (0 = Exempt).
  rows: { type: Array, default: () => [] },
  // Ticked categories: their rows are removed from the bill.
  checked: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'toggle'])

const options = computed(() => {
  const counts = new Map()
  for (const row of props.rows) {
    for (const key of row.keys) counts.set(key, (counts.get(key) || 0) + 1)
  }
  const opts = []
  if (counts.has('gst')) opts.push({ key: 'gst', label: 'GST items', count: counts.get('gst') })
  if (counts.has('nongst')) opts.push({ key: 'nongst', label: 'Non-GST items', count: counts.get('nongst') })
  const rates = [...counts.keys()]
    .filter(k => k.startsWith('rate:'))
    .map(k => parseFloat(k.slice(5)))
    .sort((a, b) => b - a)
  for (const r of rates) {
    opts.push({ key: `rate:${r}`, label: r ? `${r}% items` : 'Exempted items', count: counts.get(`rate:${r}`) })
  }
  return opts
})

function toggle(n) {
  const opt = options.value[n - 1]
  if (opt) emit('toggle', opt.key, !props.checked.includes(opt.key))
}

const digitShortcuts = Object.fromEntries(
  Array.from({ length: 9 }, (_, i) => [String(i + 1), () => toggle(i + 1)])
)

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close'),
  ENTER: () => emit('close'),
  ...digitShortcuts,
})
</script>
