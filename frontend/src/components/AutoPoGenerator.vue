<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 p-4">
    <div class="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-[var(--color-surface)] text-[var(--color-text)] shadow-2xl">
      <header class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)] px-5 py-3">
        <div class="min-w-0">
          <h2 class="truncate text-xl font-bold">{{ supplierName }}</h2>
          <p class="text-xs text-[var(--color-text-muted)]">Auto PO · {{ scopeLabel }}</p>
        </div>
        <div class="flex items-center gap-4">
          <label class="flex cursor-pointer items-center gap-2 text-sm font-semibold">
            <input v-model="showZero" type="checkbox" class="h-4 w-4 accent-[var(--color-info)]" />
            Show 0 qty items ({{ zeroCount }})
          </label>
          <button class="rounded-lg px-2 py-1 font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]" @click="emit('close')">✕</button>
        </div>
      </header>

      <div class="min-h-[12rem] flex-1 overflow-auto">
        <div v-if="loading" class="p-6 text-sm text-[var(--color-text-muted)] animate-pulse">Loading items…</div>
        <div v-else-if="error" class="p-6 text-sm font-semibold text-[var(--color-danger)]">{{ error }}</div>
        <div v-else-if="!visibleRows.length" class="p-6 text-sm text-[var(--color-text-muted)]">{{ emptyText }}</div>
        <table v-else class="w-full text-left">
          <thead class="sticky top-0 bg-[var(--color-surface-raised)] text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
            <tr>
              <th class="px-3 py-2">#</th>
              <th class="px-3 py-2">Item</th>
              <th class="px-3 py-2 text-right">Stock</th>
              <th class="px-3 py-2 text-right">Safety</th>
              <th class="px-3 py-2 text-right">Max Stock</th>
              <th class="px-3 py-2 text-right">Min Order</th>
              <th class="w-40 px-3 py-2 text-right">Order Qty</th>
              <th class="px-3 py-2">UOM</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(r, i) in visibleRows"
              :key="r.item_code"
              class="border-b border-[var(--color-border)]/50"
              :class="focusedCode === r.item_code
                ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
                : orderQty(r) > 0 ? '' : 'opacity-60'"
            >
              <td class="px-3 py-1.5 font-mono text-sm">{{ i + 1 }}</td>
              <td class="px-3 py-1.5">
                <div class="font-bold">{{ r.item_name }}</div>
                <div class="font-mono text-xs opacity-70">{{ r.item_code }}</div>
              </td>
              <td class="px-3 py-1.5 text-right font-mono">{{ fmt(r.stock) }}</td>
              <td class="px-3 py-1.5 text-right font-mono">{{ fmt(r.safety_stock) }}</td>
              <td class="px-3 py-1.5 text-right font-mono">{{ fmt(r.max_stock) }}</td>
              <td class="px-3 py-1.5 text-right font-mono">{{ fmt(r.min_order_qty) }}</td>
              <td class="px-3 py-1.5">
                <input
                  :ref="el => { qtyInputs[i] = el }"
                  v-model="r.qty"
                  type="number"
                  min="0"
                  step="any"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-xl font-bold text-[var(--color-text)] outline-none"
                  @focus="focusedCode = r.item_code; $event.target.select()"
                  @blur="focusedCode = ''"
                  @keydown.enter.prevent="focusQty(i + 1)"
                  @keydown.down.prevent="focusQty(i + 1)"
                  @keydown.up.prevent="focusQty(i - 1)"
                />
              </td>
              <td class="px-3 py-1.5 text-sm">{{ r.uom }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-border)] px-5 py-3">
        <span class="text-sm font-semibold">{{ orderRows.length }} item{{ orderRows.length === 1 ? '' : 's' }} to order</span>
        <div class="flex gap-3">
          <button class="rounded-lg bg-[var(--color-surface-raised)] px-5 py-2 text-sm font-bold uppercase tracking-wider hover:brightness-110" @click="emit('close')">Cancel (Esc)</button>
          <button
            class="rounded-lg bg-[var(--color-info)] px-8 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] shadow-md hover:bg-[var(--color-info)]/80 active:scale-95 disabled:opacity-50"
            :disabled="loading || !orderRows.length"
            @click="generate"
          >
            Generate (F8)
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { frappeGet } from '../api.js'
import { refreshItemCache, lookupBillableItem } from '../services/itemCache.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { reorderQty } from '../utils/reorderQty'

const props = defineProps({
  supplier: { type: String, required: true },
  supplierName: { type: String, default: '' },
})
// generate: [{ item_code, qty }] with every qty above 0
const emit = defineEmits(['close', 'generate'])

useSubwindowWatcher(computed(() => true))

const company = localStorage.getItem('wb-company') || ''
const storedWarehouse = localStorage.getItem('wb-warehouse') || ''
const warehouse = storedWarehouse === 'None' ? '' : storedWarehouse
const scopeLabel = [company, warehouse || 'All warehouses'].filter(Boolean).join(' · ')

const rows = ref([])
const loading = ref(true)
const error = ref('')
const showZero = ref(false)
const focusedCode = ref('')
const qtyInputs = []

const orderQty = r => Number(r.qty) || 0
const fmt = v => (Number(v) || 0).toLocaleString('en-IN', { maximumFractionDigits: 3 })

// Hidden by the suggested qty, so a row does not vanish while its qty is being cleared or typed;
// a qty typed on a 0 row keeps that row visible when the 0 rows are hidden again
const visibleRows = computed(() => rows.value.filter(r => showZero.value || r.suggested > 0 || orderQty(r) > 0))
const zeroCount = computed(() => rows.value.filter(r => !(r.suggested > 0)).length)
const orderRows = computed(() => rows.value.filter(r => orderQty(r) > 0))

const emptyText = computed(() => {
  if (!rows.value.length) return 'No items are linked to this supplier.'
  if (!rows.value.some(r => r.safety_stock > 0 || r.max_stock > 0 || r.min_order_qty > 0)) {
    return 'None of these items has a Safety Stock, Max Stock or Min Order Qty set. Tick "Show 0 qty items" to enter quantities.'
  }
  return 'Nothing to order: stock is above the set levels. Tick "Show 0 qty items" to enter quantities.'
})

function stockOf(item) {
  if (warehouse) return Number(item.stock) || 0
  return (item.warehouse_stock || []).reduce((sum, w) => sum + (Number(w.qty) || 0), 0)
}

async function load() {
  try {
    const [codes] = await Promise.all([
      frappeGet('ssplbilling.api.purchase_order_api.get_supplier_items', { supplier: props.supplier }),
      refreshItemCache('Purchase', null, warehouse || 'None'),
    ])
    rows.value = (codes || [])
      .map(code => lookupBillableItem(code))
      .filter(Boolean)
      .map(item => {
        const stock = stockOf(item)
        const suggested = reorderQty({
          stock,
          safetyStock: item.safety_stock,
          maxStock: item.custom_max_stock,
          minOrderQty: item.min_order_qty,
        })
        return {
          item_code: item.item_code,
          item_name: item.item_name || item.item_code,
          uom: item.uom || 'Nos',
          stock,
          safety_stock: Number(item.safety_stock) || 0,
          max_stock: Number(item.custom_max_stock) || 0,
          min_order_qty: Number(item.min_order_qty) || 0,
          suggested,
          qty: suggested,
        }
      })
      .sort((a, b) => a.item_name.localeCompare(b.item_name))
  } catch (e) {
    error.value = e.message || 'Could not load items'
  } finally {
    loading.value = false
    nextTick(() => focusQty(0))
  }
}

function focusQty(i) {
  if (i >= 0 && i < visibleRows.value.length) qtyInputs[i]?.focus()
}

function generate() {
  if (loading.value || !orderRows.value.length) return
  emit('generate', orderRows.value.map(r => ({ item_code: r.item_code, qty: orderQty(r) })))
}

// Capture: the page underneath has its own F2 / F8 / Esc
function onKeydown(e) {
  if (!['F2', 'F8', 'Escape'].includes(e.key)) return
  e.preventDefault()
  e.stopImmediatePropagation()
  if (e.key === 'F8') generate()
  else if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  document.activeElement?.blur()
  window.addEventListener('keydown', onKeydown, true)
  load()
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown, true))
</script>
