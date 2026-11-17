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
            <template v-if="tab === 'remove'">Ticked = removed from this bill · untick to bring back</template>
            <template v-else-if="base === 'valuation'">Set rates above valuation to valuation rate + a percentage</template>
            <template v-else>Change every row's rate by a percentage</template>
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

      <div class="mb-4 flex gap-1 rounded-xl bg-[var(--color-surface-raised)] p-1">
        <button
          v-for="t in TABS"
          :key="t.id"
          type="button"
          :data-testid="`multi-edit-tab-${t.id}`"
          class="flex-1 rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-colors"
          :class="tab === t.id ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          @click="setTab(t.id)"
        >
          {{ t.label }}
        </button>
      </div>

      <!-- Rate Edit. Current rate: + lowers every rate, − raises it, always from the rates before
           Rate Edit. Valuation: rate = valuation rate × (1 + %), a markup on cost. -->
      <div v-if="tab === 'rate'" class="flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Based on</span>
          <div class="flex flex-1 gap-1 rounded-xl border border-[var(--color-border)] p-1">
            <button
              v-for="b in BASES"
              :key="b.id"
              type="button"
              :data-testid="`rate-edit-base-${b.id}`"
              class="flex-1 rounded-lg px-3 py-1 text-xs font-bold uppercase tracking-widest transition-colors"
              :class="base === b.id ? 'bg-[var(--color-info)] text-white shadow' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
              @click="setBase(b.id)"
            >
              {{ b.label }}
            </button>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div class="relative flex-1">
            <input
              ref="pctInput"
              v-model="pctText"
              data-testid="rate-edit-pct"
              type="number"
              step="0.1"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 pr-10 text-3xl font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
              placeholder="0"
            />
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-xl font-bold text-[var(--color-text-muted)]">%</span>
          </div>
          <button
            type="button"
            data-testid="rate-edit-apply"
            :disabled="!activeRows || pctInvalid"
            class="rounded-xl bg-[var(--color-highlight)] px-5 py-3 text-sm font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-highlight)]/80 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
            @click="applyRate"
          >
            Apply
          </button>
        </div>
        <p class="text-xs font-semibold" :class="pctInvalid ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
          <template v-if="pctInvalid">{{ base === 'valuation' ? 'Percentage must be above −100.' : 'Percentage must be below 100.' }}</template>
          <template v-else-if="base === 'valuation'">
            <template v-if="!valuationRows">No row is above its valuation rate.</template>
            <template v-else>
              Rates set to valuation {{ pctValue < 0 ? '−' : '+' }} {{ Math.abs(pctValue) }}% on {{ valuationRows }} row{{ valuationRows === 1 ? '' : 's' }}<template v-if="rateRows > valuationRows">; {{ rateRows - valuationRows }} without valuation or not above it keep their rate</template>.
            </template>
          </template>
          <template v-else-if="pctValue > 0">Rates go down {{ pctValue }}% on {{ rateRows }} row{{ rateRows === 1 ? '' : 's' }}.</template>
          <template v-else-if="pctValue < 0">Rates go up {{ -pctValue }}% on {{ rateRows }} row{{ rateRows === 1 ? '' : 's' }}.</template>
          <template v-else>0% puts back the rates from before Rate Edit. Positive lowers, negative raises.</template>
        </p>
        <div
          v-if="!pctInvalid && (pctValue !== ratePct || base !== rateBase) && previewLoss > 0"
          data-testid="rate-edit-loss-preview"
          class="rounded-xl border border-[var(--color-danger)] bg-[var(--color-danger)]/15 px-4 py-2 text-sm font-bold text-[var(--color-danger)]"
        >
          ⚠ {{ previewLoss }} row{{ previewLoss === 1 ? '' : 's' }} will sell below cost at {{ base === 'valuation' ? 'valuation ' + (pctValue < 0 ? '−' : '+') + Math.abs(pctValue) : pctValue }}%
        </div>
        <div class="flex items-center justify-between rounded-xl border border-[var(--color-border)] px-4 py-2">
          <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Applied now</span>
          <span data-testid="rate-edit-applied" class="font-mono text-lg font-bold" :class="ratePct || rateBase === 'valuation' ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'">
            <template v-if="rateBase === 'valuation'">Val {{ ratePct < 0 ? `−${-ratePct}` : `+${ratePct}` }}%</template>
            <template v-else>{{ ratePct > 0 ? `−${ratePct}` : ratePct < 0 ? `+${-ratePct}` : '0' }}%</template>
          </span>
          <button
            v-if="ratePct || rateBase === 'valuation'"
            type="button"
            data-testid="rate-edit-reset"
            class="rounded-lg border border-[var(--color-info)] px-3 py-1 text-xs font-bold uppercase tracking-widest text-[var(--color-info)] transition-all hover:bg-[var(--color-info)]/15 active:scale-95"
            @click="resetRate"
          >
            ↶ Reset
          </button>
        </div>
        <p v-if="appliedLoss > 0" data-testid="rate-edit-loss" class="text-xs font-bold text-[var(--color-danger)]">
          ⚠ {{ appliedLoss }} row{{ appliedLoss === 1 ? '' : 's' }} below cost now
        </p>
      </div>

      <div v-else-if="!options.length" class="py-8 text-center text-sm text-[var(--color-text-muted)]">
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

      <div class="mt-5 flex flex-wrap gap-3 text-[10px] font-medium text-[var(--color-text-muted)]">
        <span v-if="tab === 'remove'"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">1-9</kbd> Remove / bring back</span>
        <template v-else>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Enter</kbd> Apply</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">F2</kbd> Rate / Valuation</span>
        </template>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">PgUp</kbd> / <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">PgDn</kbd> Tab</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 text-[var(--color-text)]">Esc</kbd> Close</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  // Rows Multi Edit works on (on the bill, or removed by Multi Edit): [{ keys }], where keys
  // are 'gst' / 'nongst' and 'rate:<n>' (0 = Exempt).
  rows: { type: Array, default: () => [] },
  // Ticked categories: their rows are removed from the bill.
  checked: { type: Array, default: () => [] },
  // Rate Edit % applied now (positive = rates lowered), and how many rows it would change.
  ratePct: { type: Number, default: 0 },
  rateRows: { type: Number, default: 0 },
  // What the applied % works on: 'rate' (pre-Rate-Edit rate) or 'valuation' (markup on cost),
  // and how many rows sit above their valuation rate (the only ones a valuation Rate Edit changes).
  rateBase: { type: String, default: 'rate' },
  valuationRows: { type: Number, default: 0 },
  // (pct, base) => rows that would sell below cost with that Rate Edit, bill discount included.
  lossAt: { type: Function, default: () => 0 },
})

const emit = defineEmits(['close', 'toggle', 'rate'])

const TABS = [
  { id: 'remove', label: 'Remove' },
  { id: 'rate', label: 'Rate Edit' },
]
const BASES = [
  { id: 'rate', label: 'Current rate' },
  { id: 'valuation', label: 'Valuation' },
]
const tab = ref('remove')
const base = ref('rate')
const pctText = ref('')
const pctInput = ref(null)
const pctValue = computed(() => parseFloat(pctText.value) || 0)
const pctInvalid = computed(() => (base.value === 'valuation' ? pctValue.value <= -100 : pctValue.value >= 100))
const activeRows = computed(() => (base.value === 'valuation' ? props.valuationRows : props.rateRows))
const previewLoss = computed(() => (props.show && tab.value === 'rate' ? props.lossAt(pctValue.value, base.value) : 0))
const appliedLoss = computed(() => (props.show && tab.value === 'rate' ? props.lossAt(props.ratePct, props.rateBase) : 0))

function setTab(id) {
  tab.value = id
  if (id === 'rate') {
    base.value = props.rateBase
    pctText.value = props.ratePct || props.rateBase === 'valuation' ? String(props.ratePct) : ''
    focusPct()
  }
}

function focusPct() {
  nextTick(() => { pctInput.value?.focus(); pctInput.value?.select() })
}

function setBase(id) {
  if (base.value === id) return
  base.value = id
  pctText.value = id === props.rateBase && (props.ratePct || id === 'valuation') ? String(props.ratePct) : ''
  focusPct()
}

watch(() => props.show, (open) => { if (open) tab.value = 'remove' })

function applyRate() {
  if (!activeRows.value || pctInvalid.value) return
  emit('rate', pctValue.value, base.value)
}

function resetRate() {
  pctText.value = ''
  base.value = 'rate'
  emit('rate', 0, 'rate')
}

function switchTab(step) {
  const i = TABS.findIndex(t => t.id === tab.value)
  setTab(TABS[(i + step + TABS.length) % TABS.length].id)
}

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
  if (tab.value !== 'remove') return
  const opt = options.value[n - 1]
  if (opt) emit('toggle', opt.key, !props.checked.includes(opt.key))
}

const digitShortcuts = Object.fromEntries(
  Array.from({ length: 9 }, (_, i) => [String(i + 1), () => toggle(i + 1)])
)

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close'),
  ENTER: () => (tab.value === 'rate' ? applyRate() : emit('close')),
  PAGEUP: () => switchTab(-1),
  PAGEDOWN: () => switchTab(1),
  F2: () => { if (tab.value === 'rate') setBase(base.value === 'rate' ? 'valuation' : 'rate') },
  ...digitShortcuts,
})
</script>
