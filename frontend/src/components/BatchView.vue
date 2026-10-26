<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
  >
    <div
      ref="panel"
      tabindex="-1"
      class="w-[1100px] max-w-[95vw] max-h-[85vh] bg-[var(--color-bg)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col outline-none"
    >
      <!-- Header -->
      <div class="px-[20px] py-[12px] bg-[var(--color-surface)] border-b border-[var(--color-border)] flex justify-between items-center gap-[16px]">
        <div class="min-w-0">
          <h3 class="text-4xl font-bold text-[var(--color-text)]">Select Batch</h3>
          <p class="text-2xl text-[var(--color-text-muted)] truncate">
            {{ itemCode }} — {{ info.item_name || itemName }}<span v-if="warehouse"> · {{ warehouse }}</span>
          </p>
        </div>
        <div class="flex items-center gap-[12px] shrink-0">
          <button
            v-if="allowCreate"
            type="button"
            @click="openCreator"
            :disabled="loading"
            class="flex items-center gap-[10px] rounded-xl border border-[var(--color-info)] px-[16px] py-[10px] text-2xl font-bold uppercase tracking-wider text-[var(--color-info)] bg-[var(--color-info)]/10 hover:bg-[var(--color-info)]/20 transition-all active:scale-95 disabled:opacity-50"
          >
            <span>+ New Batch</span>
            <kbd class="rounded border border-current px-1.5 py-0.5 font-mono text-xl opacity-70">F2</kbd>
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors px-[16px] py-[8px] hover:bg-[var(--color-surface-raised)] rounded-full text-4xl leading-none"
            aria-label="Close"
          >&times;</button>
        </div>
      </div>

      <!-- Batch list -->
      <div ref="listEl" class="flex-1 overflow-y-auto">
        <table class="w-full border-collapse text-2xl">
          <thead class="sticky top-0">
            <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
              <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Batch No</th>
              <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Mfg Date</th>
              <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Expiry</th>
              <th class="px-[10px] py-[5px] text-left font-bold uppercase text-[var(--color-text-muted)]">Supplier</th>
              <th class="px-[10px] py-[5px] text-right font-bold uppercase text-[var(--color-text-muted)]">Stock</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr
              v-for="(b, idx) in visibleBatches"
              :key="b.batch_no"
              :data-idx="idx"
              @click="choose(b)"
              @mousemove="highlightIdx = idx"
              class="cursor-pointer divide-x divide-[var(--color-border)] transition-colors"
              :class="highlightIdx === idx
                ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
                : 'text-[var(--color-text)] hover:bg-[var(--color-info)]/10'"
            >
              <td class="px-[10px] py-[6px] font-mono font-bold">
                {{ b.batch_no }}
                <span v-if="b.batch_no === selected" class="ml-[8px] text-xl font-normal opacity-80">(current)</span>
              </td>
              <td class="px-[10px] py-[6px]">{{ formatDMY(b.manufacturing_date, '--') }}</td>
              <td class="px-[10px] py-[6px]" :class="{ 'font-bold text-[var(--color-danger)]': b.expired && highlightIdx !== idx }">
                {{ formatDMY(b.expiry_date, '--') }}<span v-if="b.expired"> (expired)</span>
              </td>
              <td class="px-[10px] py-[6px]">{{ b.supplier || '--' }}</td>
              <td class="px-[10px] py-[6px] text-right font-mono">{{ formatQty(b.qty) }}</td>
            </tr>
            <tr v-if="!visibleBatches.length">
              <td colspan="5" class="px-[10px] py-[16px] text-center text-2xl italic text-[var(--color-text-muted)]">
                <template v-if="loading">Loading batches…</template>
                <template v-else-if="error"><span class="text-[var(--color-danger)]">{{ error }}</span></template>
                <template v-else-if="inStockOnly">No batch has stock in this warehouse</template>
                <template v-else>No batches yet{{ allowCreate ? ' — press F2 to create one' : '' }}</template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-[20px] py-[8px] bg-[var(--color-surface)] border-t border-[var(--color-border)] text-xl text-[var(--color-text-muted)]">
        ↑ ↓ move · Enter select · Esc skip
      </div>
    </div>

    <BatchCreator
      v-if="showCreator"
      :show="showCreator"
      :item-code="itemCode"
      :item-name="info.item_name || itemName"
      :supplier="supplier"
      :create-new-batch="info.create_new_batch"
      :has-expiry-date="info.has_expiry_date"
      :shelf-life-in-days="Number(info.shelf_life_in_days) || 0"
      @close="closeCreator"
      @created="onBatchCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { formatDMY } from '../utils/date'
import BatchCreator from './BatchCreator.vue'

const props = defineProps({
  show: Boolean,
  itemCode: { type: String, required: true },
  itemName: { type: String, default: '' },
  warehouse: { type: String, default: '' },
  supplier: { type: String, default: '' },
  // Batch already on the row, highlighted first
  selected: { type: String, default: '' },
  allowCreate: { type: Boolean, default: true },
  // Returns can only send back stock a batch holds
  inStockOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'select'])

const panel = ref(null)
const listEl = ref(null)
const info = ref({})
const batches = ref([])
const loading = ref(false)
const error = ref('')
const highlightIdx = ref(0)
const showCreator = ref(false)

// The Enter that picked the item can reach this window's shortcut layer too and would select
// the first batch at once, so only an Enter pressed after opening counts.
let openedAt = 0

const visibleBatches = computed(() =>
  props.inStockOnly ? batches.value.filter(b => b.qty > 0) : batches.value)

useSubwindowWatcher(computed(() => props.show && !showCreator.value), {
  ESCAPE: () => emit('close'),
  ENTER: (e) => { if (e.timeStamp > openedAt) chooseHighlighted() },
  ARROWDOWN: () => moveHighlight(1),
  ARROWUP: () => moveHighlight(-1),
  F2: () => openCreator(),
})

function formatQty(q) {
  const n = Number(q) || 0
  return Number.isInteger(n) ? String(n) : n.toFixed(3)
}

function moveHighlight(step) {
  const n = visibleBatches.value.length
  if (!n) return
  highlightIdx.value = (highlightIdx.value + step + n) % n
  nextTick(() => listEl.value?.querySelector(`[data-idx="${highlightIdx.value}"]`)?.scrollIntoView({ block: 'nearest' }))
}

function chooseHighlighted() {
  const b = visibleBatches.value[highlightIdx.value]
  if (b) choose(b)
}

function choose(b) {
  emit('select', b.batch_no)
}

function openCreator() {
  if (!props.allowCreate || loading.value) return
  showCreator.value = true
}

function closeCreator() {
  showCreator.value = false
  nextTick(() => panel.value?.focus())
}

// A batch made here is the one being received, so it is selected straight away
function onBatchCreated(batch) {
  showCreator.value = false
  batches.value = [batch, ...batches.value]
  emit('select', batch.batch_no)
}

async function load() {
  loading.value = true
  error.value = ''
  batches.value = []
  try {
    const res = await frappeGet('ssplbilling.api.batch_api.get_item_batches', {
      item_code: props.itemCode,
      warehouse: props.warehouse || '',
    })
    info.value = res || {}
    batches.value = res?.batches || []
    const cur = visibleBatches.value.findIndex(b => b.batch_no === props.selected)
    highlightIdx.value = cur >= 0 ? cur : 0
  } catch (e) {
    error.value = e.message || 'Failed to load batches'
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (open) => {
  if (!open) return
  openedAt = performance.now()
  showCreator.value = false
  info.value = {}
  load()
  // Off the opener's input, so its own Enter/arrow handlers stay quiet while this is up
  nextTick(() => panel.value?.focus())
}, { immediate: true })
</script>
