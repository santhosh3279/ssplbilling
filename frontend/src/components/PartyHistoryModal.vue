<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="close">
    <div class="flex h-[80vh] w-[80vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
      <div class="border-b border-[var(--color-border)] px-3 py-2 flex justify-between items-center bg-[var(--color-surface-raised)]">
        <div class="flex items-center gap-6">
          <div>
            <div class="text-4xl font-bold">{{ title }}: {{ partyName }}</div>
            <div class="text-xl text-[var(--color-text-muted)]">{{ totalCount }} {{ totalNoun }} previously purchased</div>
          </div>
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-px ml-4">
            <button
              @click="viewMode = 'invoice'"
              class="px-1.5 py-0.5 text-lg font-bold uppercase rounded transition-all"
              :class="viewMode === 'invoice' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              Invoice-wise
            </button>
            <button
              @click="viewMode = 'item'"
              class="px-1.5 py-0.5 text-lg font-bold uppercase rounded transition-all"
              :class="viewMode === 'item' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              Item-wise
            </button>
            <button
              @click="viewMode = 'not-today'"
              class="px-1.5 py-0.5 text-lg font-bold uppercase rounded transition-all"
              :class="viewMode === 'not-today' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              Not Today
            </button>
          </div>
        </div>
        <button @click="close" class="text-4xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
      </div>
      <div class="flex-1 overflow-y-auto p-2 custom-scrollbar">
        <table class="w-full border-collapse">
          <thead class="sticky top-0 bg-[var(--color-surface-raised)] shadow-sm">
            <!-- Invoice-wise Header -->
            <tr v-if="viewMode === 'invoice'" class="text-left text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="px-2 py-1">Date</th>
              <th class="px-2 py-1">Item Code</th>
              <th class="px-2 py-1">Item Name</th>
              <th class="px-2 py-1">Barcodes</th>
              <th class="px-2 py-1 text-right">Qty</th>
              <th class="px-2 py-1 text-right">Rate</th>
              <th class="px-2 py-1">Invoice</th>
            </tr>
            <!-- Item-wise Header -->
            <tr v-else class="text-left text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="px-2 py-1">Item Code</th>
              <th class="px-2 py-1">Item Name</th>
              <th class="px-2 py-1">Barcodes</th>
              <th class="px-2 py-1 text-right">Total Qty</th>
              <th class="px-2 py-1 text-right">Last Rate</th>
              <th class="px-2 py-1">Last Date</th>
              <th class="px-2 py-1">Last Invoice</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <!-- Invoice-wise Rows -->
            <template v-if="viewMode === 'invoice'">
              <tr v-for="(h, idx) in sortedHistory" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                <td class="px-2 py-1.5 font-mono text-xl">{{ h.date }}</td>
                <td class="px-2 py-1.5 font-mono font-bold text-2xl text-[var(--color-highlight)]">{{ h.item_code }}</td>
                <td class="px-2 py-1.5 text-3xl font-medium">{{ h.item_name }}</td>
                <td class="px-2 py-1.5 font-mono text-lg text-[var(--color-text-muted)]">{{ h.barcodes }}</td>
                <td class="px-2 py-1.5 text-right font-bold text-3xl">{{ h.qty }}</td>
                <td class="px-2 py-1.5 text-right font-mono text-3xl text-[var(--color-warning)]">{{ h.rate.toFixed(2) }}</td>
                <td class="px-2 py-1.5 text-xl text-[var(--color-info)]">{{ h.name }}</td>
              </tr>
            </template>
            <!-- Item-wise Rows -->
            <template v-else-if="viewMode === 'item'">
              <tr v-for="(h, idx) in sortedItemWise" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                <td class="px-2 py-1.5 font-mono font-bold text-2xl text-[var(--color-highlight)]">{{ h.item_code }}</td>
                <td class="px-2 py-1.5 text-3xl font-medium">{{ h.item_name }}</td>
                <td class="px-2 py-1.5 font-mono text-lg text-[var(--color-text-muted)]">{{ h.barcodes }}</td>
                <td class="px-2 py-1.5 text-right font-bold text-3xl">{{ Number(h.total_qty).toFixed(3) }}</td>
                <td class="px-2 py-1.5 text-right font-mono text-3xl text-[var(--color-warning)]">{{ h.last_rate.toFixed(2) }}</td>
                <td class="px-2 py-1.5 font-mono text-xl">{{ h.last_date }}</td>
                <td class="px-2 py-1.5 text-xl text-[var(--color-info)]">{{ h.last_invoice }}</td>
              </tr>
            </template>
            <!-- Not Today Rows -->
            <template v-else-if="viewMode === 'not-today'">
              <tr v-for="(h, idx) in sortedNotTodayItems" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                <td class="px-2 py-1.5 font-mono font-bold text-2xl text-[var(--color-highlight)]">{{ h.item_code }}</td>
                <td class="px-2 py-1.5 text-3xl font-medium">{{ h.item_name }}</td>
                <td class="px-2 py-1.5 font-mono text-lg text-[var(--color-text-muted)]">{{ h.barcodes }}</td>
                <td class="px-2 py-1.5 text-right font-bold text-3xl">{{ Number(h.total_qty).toFixed(3) }}</td>
                <td class="px-2 py-1.5 text-right font-mono text-3xl text-[var(--color-warning)]">{{ h.last_rate.toFixed(2) }}</td>
                <td class="px-2 py-1.5 font-mono text-xl">{{ h.last_date }}</td>
                <td class="px-2 py-1.5 text-xl text-[var(--color-info)]">{{ h.last_invoice }}</td>
              </tr>
            </template>
            <!-- Empty State -->
            <tr v-if="viewMode === 'invoice' ? !history.length : (viewMode === 'item' ? !itemWise.length : !notTodayItems.length)">
              <td colspan="7" class="px-2 py-6 text-center text-2xl text-[var(--color-text-muted)] italic">
                <span v-if="viewMode === 'not-today'">All previously purchased items are in the current invoice</span>
                <span v-else>No history available for this {{ partyNoun }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="border-t border-[var(--color-border)] px-3 py-1.5 bg-[var(--color-surface-raised)] text-right">
        <button @click="close" class="rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] px-3 py-1 text-2xl font-bold uppercase tracking-wider hover:bg-[var(--color-surface-raised)] transition-all">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Reusable "Purchase History" modal shared by Sales Invoice (customer) and Purchase
// Invoice (supplier). The page owns the open state (v-model:show) so its keyboard
// handlers can still read/close it; viewMode + the item-wise aggregation live here.
const props = defineProps({
  show: { type: Boolean, default: false },
  partyName: { type: String, default: '' },
  partyNoun: { type: String, default: 'customer' }, // for the empty-state text
  history: { type: Array, default: () => [] }, // raw invoice-wise history rows
  title: { type: String, default: 'Purchase History' },
  currentItems: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:show'])

const viewMode = ref('item') // 'invoice', 'item', or 'not-today'

// Aggregate the invoice-wise history into one row per item_code.
const itemWise = computed(() => {
  const map = {}
  props.history.forEach((h) => {
    if (!map[h.item_code]) {
      map[h.item_code] = {
        item_code: h.item_code,
        item_name: h.item_name,
        barcodes: h.barcodes,
        total_qty: 0,
        last_rate: h.rate,
        last_date: h.date,
        last_invoice: h.name,
      }
    }
    map[h.item_code].total_qty += h.qty
  })
  return Object.values(map)
})

const notTodayItems = computed(() => {
  const currentItemCodes = new Set(props.currentItems.map(i => i.item_code).filter(Boolean))
  return itemWise.value.filter(item => !currentItemCodes.has(item.item_code))
})

const sortedHistory = computed(() => {
  return [...props.history].sort((a, b) => b.qty - a.qty)
})

const sortedItemWise = computed(() => {
  return [...itemWise.value].sort((a, b) => b.total_qty - a.total_qty)
})

const sortedNotTodayItems = computed(() => {
  return [...notTodayItems.value].sort((a, b) => b.total_qty - a.total_qty)
})

const totalCount = computed(() => {
  if (viewMode.value === 'invoice') return props.history.length
  if (viewMode.value === 'item') return itemWise.value.length
  return notTodayItems.value.length
})

const totalNoun = computed(() => {
  if (viewMode.value === 'invoice') return 'transactions'
  if (viewMode.value === 'item') return 'unique items'
  return 'items not purchased today'
})

function close() {
  emit('update:show', false)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--color-highlight); }
</style>
