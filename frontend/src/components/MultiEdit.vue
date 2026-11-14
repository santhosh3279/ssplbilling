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
            Tick what to remove from this bill
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
          :class="picked.includes(opt.key)
            ? 'border-[var(--color-danger)] bg-[var(--color-danger)]/15 text-[var(--color-danger)]'
            : 'border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]'"
        >
          <kbd class="w-6 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-center text-xs text-[var(--color-text-muted)]">{{ i + 1 }}</kbd>
          <input
            type="checkbox"
            :value="opt.key"
            v-model="picked"
            class="h-5 w-5 rounded accent-[var(--color-danger)]"
          />
          <span class="flex-1 text-lg font-bold uppercase">{{ opt.label }}</span>
          <span data-testid="tax-cleanup-count" class="font-mono text-sm text-[var(--color-text-muted)]">{{ opt.count }} row{{ opt.count === 1 ? '' : 's' }}</span>
        </label>
      </div>

      <div v-if="removed.length" data-testid="multi-edit-removed" class="mt-5 border-t border-[var(--color-border)] pt-4">
        <div class="mb-2 text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Removed from this bill</div>
        <div class="flex flex-col gap-2">
          <div
            v-for="batch in [...removed].reverse()"
            :key="batch.id"
            :data-testid="`multi-edit-batch-${batch.id}`"
            class="flex items-center gap-3 rounded-xl border border-[var(--color-border)] px-4 py-2 text-[var(--color-text)]"
          >
            <span class="flex-1 text-sm font-bold uppercase">{{ batch.labels.join(' + ') }}</span>
            <span class="font-mono text-sm text-[var(--color-text-muted)]">{{ batch.count }} row{{ batch.count === 1 ? '' : 's' }}</span>
            <button
              type="button"
              :data-testid="`multi-edit-undo-${batch.id}`"
              class="rounded-lg border border-[var(--color-info)] px-3 py-1 text-xs font-bold uppercase tracking-widest text-[var(--color-info)] transition-all hover:bg-[var(--color-info)]/15 active:scale-95"
              @click="$emit('undo', batch.id)"
            >
              ↶ Undo
            </button>
          </div>
        </div>
      </div>

      <div class="mt-5 flex items-center justify-between gap-3">
        <div class="flex gap-3 text-[10px] font-medium text-[var(--color-text-muted)]">
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">1-9</kbd> Tick</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Enter</kbd> Delete</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Esc</kbd> Close</span>
        </div>
        <button
          type="button"
          data-testid="tax-cleanup-delete"
          :disabled="!matches.length"
          class="rounded-xl bg-[var(--color-danger)] px-5 py-2 text-sm font-bold uppercase tracking-widest text-white transition-all hover:bg-[var(--color-danger)]/80 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
          @click="apply"
        >
          Delete{{ matches.length ? ` (${matches.length})` : '' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  // Active bill rows: [{ idx, keys }] where keys are 'gst' / 'nongst' and 'rate:<n>' (0 = Exempt).
  rows: { type: Array, default: () => [] },
  // Earlier Multi Edit deletes still undoable: [{ id, labels, count }].
  removed: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'delete', 'undo'])

const picked = ref([])

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

// Rows matching any ticked option.
const matches = computed(() => {
  const set = new Set(picked.value)
  if (!set.size) return []
  return props.rows.filter(row => row.keys.some(k => set.has(k)))
})

// Every opening starts with nothing ticked.
watch(() => props.show, (open) => { if (open) picked.value = [] })

function toggle(n) {
  const opt = options.value[n - 1]
  if (!opt) return
  picked.value = picked.value.includes(opt.key)
    ? picked.value.filter(k => k !== opt.key)
    : [...picked.value, opt.key]
}

function apply() {
  if (!matches.value.length) return
  const labels = options.value.filter(o => picked.value.includes(o.key)).map(o => o.label)
  emit('delete', matches.value.map(row => row.idx), labels)
}

const digitShortcuts = Object.fromEntries(
  Array.from({ length: 9 }, (_, i) => [String(i + 1), () => toggle(i + 1)])
)

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close'),
  ENTER: () => apply(),
  ...digitShortcuts,
})
</script>
