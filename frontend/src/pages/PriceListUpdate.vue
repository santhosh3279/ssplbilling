<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[210] flex items-center justify-center bg-black/80 backdrop-blur-md p-4' : 'min-h-screen bg-[var(--color-bg)] flex flex-col'">
    <div :class="isSubWindow ? 'flex h-[90vh] w-[90vw] flex-col overflow-hidden rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl' : 'flex flex-1 flex-col'">
      <!-- Header -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <div class="flex items-center gap-4">
          <button
            v-if="isSubWindow"
            class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            @click="$emit('close')"
          >
            &larr; Back to Entry
          </button>
          <button
            v-else
            class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
            @click="router.push('/')"
          >
            &larr; Dashboard
          </button>
          <h1 class="text-3xl text-[var(--color-text)]">{{ itemName || 'Update Item Prices' }}</h1>
          <div v-if="currentItemCode" class="rounded-full bg-[var(--color-info)]/20 px-3 py-1 text-3xl font-bold text-[var(--color-info)]">
            {{ currentItemCode }}
          </div>
          <div v-if="cachedItem && cachedItem.stock !== undefined" class="rounded-full px-3 py-1 text-3xl font-bold" :class="cachedItem.stock <= 0 ? 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/20 text-[var(--color-success)]'">
            Stock: {{ cachedItem.stock }} {{ cachedItem.uom || '' }}
          </div>
          <div v-if="hsnSac" class="rounded-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1 text-3xl font-bold text-[var(--color-text-muted)]">
            HSN: {{ hsnSac }}
          </div>
          <div v-if="taxRate !== undefined && taxRate !== null" class="rounded-full bg-[var(--color-warning)]/20 px-3 py-1 text-3xl font-bold text-[var(--color-warning)]">
            Tax: {{ taxRate }}%
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-[var(--color-text-muted)]">
            <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F8</kbd> Save All
            <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Close
          </span>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-x-auto">
          <div v-if="loading" class="flex items-center justify-center py-20">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-info)] border-t-transparent"></div>
          </div>

          <div v-else-if="!currentItemCode && !isSubWindow" class="p-10 text-center">
            <div class="mb-4 text-[var(--color-text-muted)]">Please provide an item code to update prices.</div>
            <input
              v-model="manualItemCode"
              class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
              placeholder="Enter Item Code..."
              @keydown.enter="loadPrices(manualItemCode)"
            />
          </div>

          <table v-else class="w-full text-left border-collapse min-w-full">
            <thead class="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
              <!-- Row 1: Indicators -->
              <tr>
                <th class="px-2 py-1.5 sticky left-0 top-0 bg-[var(--color-surface)] z-30 border-r border-b border-[var(--color-border)] w-40 text-xl font-bold uppercase text-[var(--color-text-muted)]">Type</th>
                <th
                  v-for="p in prices"
                  :key="`ind-${p.price_list}`"
                  class="px-2 py-1.5 text-right sticky top-0 bg-[var(--color-surface)] z-10"
                  :class="p.price_list === selectedPriceList 
                    ? 'bg-[var(--color-info)]/10 border-x-2 border-t-2 border-[var(--color-info)]' 
                    : 'border-b border-[var(--color-border)]'"
                >
                  <div class="flex justify-end gap-1">
                    <span v-if="p.buying" class="rounded-lg bg-[var(--color-success)]/20 px-4 py-1.5 text-[20px] font-black text-[var(--color-success)] uppercase tracking-wide shadow-sm">Buy</span>
                    <span v-if="p.selling" class="rounded-lg bg-[var(--color-info)]/20 px-4 py-1.5 text-[20px] font-black text-[var(--color-info)] uppercase tracking-wide shadow-sm">Sell</span>
                  </div>
                </th>
              </tr>
              <!-- Row 2: Price List Name -->
              <tr>
                <th class="px-2 py-1.5 text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)] sticky left-0 top-[48px] bg-[var(--color-surface)] z-30 border-r border-b border-[var(--color-border)] w-40">Price List</th>
                <th
                  v-for="p in prices"
                  :key="`name-${p.price_list}`"
                  class="px-2 py-1.5 text-right text-lg font-bold uppercase tracking-wider min-w-[160px] sticky top-[48px] bg-[var(--color-surface)] z-10"
                  :class="p.price_list === selectedPriceList 
                    ? 'bg-[var(--color-info)]/10 border-x-2 border-[var(--color-info)]' 
                    : 'border-b border-[var(--color-border)]'"
                >
                  <div class="font-bold text-[var(--color-text)] truncate" :title="p.price_list">{{ p.price_list }}</div>
                </th>
              </tr>
              <!-- Row 3: Calc Row (Input for Base Rate) -->
              <tr>
                <th class="px-2 py-1.5 text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)] sticky left-0 top-[84px] bg-[var(--color-surface)] z-30 border-r border-b border-[var(--color-border)] w-40">
                  <div class="flex flex-col gap-1.5 items-start w-full">
                    <div class="flex items-center gap-1.5">
                      <span>Calc</span>
                      <span v-if="hasFetchedPercentages" class="text-[18px] bg-[var(--color-success)]/20 text-[var(--color-success)] px-1.5 py-0.5 rounded font-black uppercase tracking-wider leading-none">Fetched</span>
                    </div>
                  </div>
                </th>
                <th
                  v-for="(p, idx) in prices"
                  :key="`calc-row-${p.price_list}`"
                  class="px-2 py-1.5 text-right sticky top-[84px] bg-[var(--color-surface)] z-10"
                  :class="p.price_list === selectedPriceList 
                    ? 'bg-[var(--color-info)]/10 border-x-2 border-b-2 border-[var(--color-info)]' 
                    : 'border-b border-[var(--color-border)]'"
                >
                  <div v-if="idx !== 0" class="flex items-center justify-end gap-1">
                    <input
                      :ref="el => inputRefs[`calc-${idx}`] = el"
                      type="number"
                      v-model.number="p.markup"
                      step="0.01"
                      placeholder="%"
                      class="w-32 rounded border border-[var(--color-info)]/30 bg-[var(--color-info)]/5 px-1 py-1 text-right font-mono font-bold text-[var(--color-info)] text-[18px] outline-none focus:ring-1 transition-colors"
                      @keydown.enter.prevent="onCalcEnter(idx)"
                      @keydown.down.prevent="focusInput(`rate-${idx}-0`)"
                    />
                    <button
                      @click="applyCalc(p, idx)"
                      class="rounded bg-[var(--color-info)] p-1 text-white hover:bg-[var(--color-info)]/80 shadow-sm transition-transform active:scale-95 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                      title="Apply to all UOMs"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                    </button>
                  </div>
                  <div v-else class="flex justify-end">
                    <button
                      type="button"
                      @click="savePercentageToItemMaster"
                      :disabled="savingPercentage || !currentItemCode"
                      class="w-full rounded bg-[var(--color-info)] px-2 py-1 text-[15px] font-bold uppercase tracking-wider text-white transition-all hover:bg-[var(--color-info)]/80 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-md text-center whitespace-nowrap"
                      title="Save all markup percentages to the Item Master child table"
                    >
                      {{ savingPercentage ? 'Saving...' : (hasFetchedPercentages ? 'Update % to Item Master' : 'Save % to Item Master') }}
                    </button>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <template v-for="(u, uidx) in uoms" :key="u.uom">
                <!-- Proposed Rate (Interactive) -->
                <tr
                  class="hover:bg-[var(--color-surface)]/40 transition-colors"
                  :class="{ 'bg-[var(--color-info)]/30': activeRow === uidx }"
                  @click="activeRow = uidx"
                >
                  <td class="px-2 py-2 sticky left-0 bg-[var(--color-surface)] z-10 border-r border-[var(--color-border)]">
                    <div class="flex items-center justify-between gap-2">
                      <div class="font-bold text-2xl" :class="u.uom === stockUom ? 'text-[var(--color-info)]' : 'text-[var(--color-warning)]'">
                        {{ u.uom }}
                      </div>
                      <span class="shrink-0 text-[8px] font-black px-1 rounded bg-[var(--color-info)] text-white uppercase">Price</span>
                    </div>
                    <div v-if="u.conversion_factor !== 1" class="text-[10px] text-[var(--color-text-muted)] italic leading-none mt-1">
                      Factor: {{ u.conversion_factor }}
                    </div>
                  </td>
                  <td
                    v-for="(p, idx) in prices"
                    :key="`prop-${p.price_list}-${u.uom}`"
                    class="px-2 py-2 text-right"
                    :class="p.price_list === selectedPriceList 
                      ? 'bg-[var(--color-info)]/5 border-x-2 border-[var(--color-info)]' 
                      : 'border-b border-[var(--color-border)]/10'"
                  >
                    <div class="flex items-center justify-end gap-2">
                      <span class="text-[14px] font-mono italic opacity-100 pointer-events-none select-none text-[var(--color-text-muted)]">
                        {{ (p.original_uom_rates[u.uom] || 0).toFixed(2) }}
                      </span>
                      <input
                        :ref="el => inputRefs[`rate-${idx}-${uidx}`] = el"
                        type="number"
                        v-model.number="p.uom_rates[u.uom]"
                        step="0.01"
                        class="w-44 rounded border bg-[var(--color-surface)] px-1 py-1 text-right font-mono font-bold text-[var(--color-text)] text-[20px] outline-none focus:ring-1 transition-colors"
                        :class="u.uom === stockUom ? 'border-[var(--color-border)] focus:border-[var(--color-info)] focus:ring-[var(--color-info)]/20' : 'border-[var(--color-warning)]/40 focus:border-[var(--color-warning)] focus:ring-amber-500/20'"
                        @keydown.enter.prevent="onRateEnter(idx, uidx)"
                        @keydown.up.prevent="moveVertical(uidx, -1, idx)"
                        @keydown.down.prevent="moveVertical(uidx, 1, idx)"
                      />
                    </div>
                  </td>
                </tr>
                <!-- Row C: Calculated Rate (Based on Header Calc) -->
                <tr class="bg-[var(--color-info)]/5 text-[var(--color-info)]/80">
                  <td class="px-2 py-1 sticky left-0 bg-[var(--color-surface)] z-10 border-r border-[var(--color-border)]">
                    <div class="flex items-center justify-between gap-2">
                      <span class="text-xl font-black uppercase truncate">{{ u.uom }}</span>
                      <span class="shrink-0 text-[8px] font-black px-1 rounded bg-[var(--color-info)]/20 uppercase">Calculated</span>
                    </div>
                  </td>
                  <td
                    v-for="(p, idx) in prices"
                    :key="`calc-uom-${p.price_list}-${u.uom}`"
                    class="px-2 py-1 text-right font-mono text-[14px] font-bold"
                    :class="[
                      p.price_list === selectedPriceList ? 'bg-[var(--color-info)]/5 border-x-2 border-[var(--color-info)]' : '',
                      idx !== 0 ? 'cursor-pointer hover:underline decoration-dotted' : ''
                    ]"
                    @click="idx !== 0 && (p.uom_rates[u.uom] = Number(((calculatedRatesByUom[u.uom] || [])[idx] || 0).toFixed(2)))"
                    :title="idx !== 0 ? 'Click to apply to proposed' : ''"
                  >
                    {{ ((calculatedRatesByUom[u.uom] || [])[idx] || 0).toFixed(2) }}
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Purchase History Sections -->
        <div v-if="currentItemCode" class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-[var(--color-text)]">
          <!-- Same Supplier History (only if props.supplier is present) -->
          <div v-if="props.supplier" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm">
            <h3 class="mb-3 text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex items-center justify-between">
              <span>Purchase History (Same Supplier)</span>
              <span v-if="historyLoading" class="text-xs text-[var(--color-info)] animate-pulse">Loading...</span>
            </h3>
            <div v-if="!historyLoading && !sameSupplierHistory.length" class="text-sm text-[var(--color-text-muted)] italic py-4 text-center bg-[var(--color-bg)]/20 rounded-lg">
              No previous history found for this supplier.
            </div>
            <div v-else class="max-h-60 overflow-y-auto custom-scrollbar">
              <table class="w-full text-left text-lg border-collapse">
                <thead>
                  <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-sm uppercase font-bold">
                    <th class="py-2 pr-2">Bill No</th>
                    <th class="py-2 px-2">Date</th>
                    <th class="py-2 px-2 text-right">Qty</th>
                    <th class="py-2 px-2 text-right">Rate</th>
                    <th class="py-2 pl-2 text-right">Disc%</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]/30 font-mono text-lg">
                  <tr v-for="(h, i) in sameSupplierHistory.slice(0, 10)" :key="i" class="hover:bg-[var(--color-surface-raised)]/20">
                    <td class="py-2 pr-2 leading-none truncate max-w-[120px]" :title="h.name">{{ h.name }}</td>
                    <td class="py-2 px-2 leading-none whitespace-nowrap">{{ formatDateShort(h.date) }}</td>
                    <td class="py-2 px-2 text-right leading-none">{{ h.qty }}</td>
                    <td class="py-2 px-2 text-right leading-none font-bold text-[var(--color-success)]">{{ h.rate.toFixed(2) }}</td>
                    <td class="py-2 pl-2 text-right leading-none text-[var(--color-warning)]">{{ h.discount || 0 }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Different Suppliers / General Purchase History -->
          <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm" :class="{ 'col-span-2': !props.supplier }">
            <h3 class="mb-3 text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex items-center justify-between">
              <span>{{ props.supplier ? 'Purchase History (Different Suppliers)' : 'Purchase History' }}</span>
              <span v-if="otherSuppliersHistoryLoading" class="text-xs text-[var(--color-info)] animate-pulse">Loading...</span>
            </h3>
            <div v-if="!otherSuppliersHistoryLoading && !otherSuppliersItemHistory.length" class="text-sm text-[var(--color-text-muted)] italic py-4 text-center bg-[var(--color-bg)]/20 rounded-lg">
              No previous history found.
            </div>
            <div v-else class="max-h-60 overflow-y-auto custom-scrollbar">
              <table class="w-full text-left text-lg border-collapse">
                <thead>
                  <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-sm uppercase font-bold">
                    <th class="py-2 pr-2">Supplier</th>
                    <th class="py-2 px-2">Bill No</th>
                    <th class="py-2 px-2">Date</th>
                    <th class="py-2 px-2 text-right">Qty</th>
                    <th class="py-2 pl-2 text-right">Rate</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]/30 font-mono text-lg">
                  <tr v-for="(h, i) in otherSuppliersItemHistory.slice(0, 10)" :key="i" class="hover:bg-[var(--color-surface-raised)]/20">
                    <td class="py-2 pr-2 leading-none truncate max-w-[200px] font-sans font-semibold text-[var(--color-text)]" :title="h.supplier_name || h.supplier">{{ h.supplier_name || h.supplier }}</td>
                    <td class="py-2 px-2 leading-none truncate max-w-[120px]" :title="h.name">{{ h.name }}</td>
                    <td class="py-2 px-2 leading-none whitespace-nowrap">{{ formatDateShort(h.date) }}</td>
                    <td class="py-2 px-2 text-right leading-none">{{ h.qty }}</td>
                    <td class="py-2 pl-2 text-right leading-none font-bold text-[var(--color-success)]">{{ h.rate.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      <!-- Footer -->
      <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="text-sm text-[var(--color-text-muted)]">
            Total Price Lists: <span class="font-bold text-[var(--color-text)]">{{ prices.length }}</span>
          </div>
          <div class="flex gap-3">
            <button
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-2 text-sm font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:border-[var(--color-focus)]"
              @click="isSubWindow ? $emit('close') : router.push('/')"
            >
              Cancel
            </button>
            <button
              class="rounded-lg bg-[var(--color-info)] px-8 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg transition-all hover:bg-[var(--color-info)] active:scale-95 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:ring-2 focus:ring-[var(--color-focus)]"
              @click="saveAll"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Save All Changes (F8)' }}
            </button>
          </div>
        </div>
      </footer>
    <!-- Ephemeral Toast Message -->
    <div
      v-if="toast"
      class="fixed bottom-6 right-6 z-[250] flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg transition-all duration-300 font-medium text-sm text-white"
      :class="toast.type === 'error' ? 'bg-[var(--color-error)] border border-red-500/30' : 'bg-[var(--color-success)] border border-green-500/30'"
    >
      <span class="text-base font-bold">{{ toast.type === 'success' ? '✓' : '✕' }}</span>
      <span>{{ toast.message }}</span>
      <button @click="toast = null" class="ml-2 hover:opacity-85 text-xs font-black">✕</button>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'
import { useItemCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'

const props = defineProps({
  isSubWindow: { type: Boolean, default: false },
  itemCode: { type: String, default: '' },
  selectedPriceList: { type: String, default: '' },
  initialFactor: { type: Number, default: 1 },
  initialRate: { type: Number, default: 0 },
  initialUom: { type: String, default: '' },
  initialDiscount: { type: Number, default: 0 },
  taxRate: { type: Number, default: 0 },
  isInclusive: { type: Boolean, default: false },
  supplier: { type: String, default: '' }
})

const emit = defineEmits(['close', 'saved'])

if (props.isSubWindow) useSubwindow()

const router = useRouter()
const route = useRoute()

const prices = ref([])
const itemName = ref('')
const uoms = ref([])
const stockUom = ref('')
const factor = ref(props.initialFactor)
const loading = ref(false)
const saving = ref(false)
const savingPercentage = ref(false)
const hasFetchedPercentages = ref(false)
const manualItemCode = ref('')
const activeRow = ref(0)
const inputRefs = ref({})
const hsnSac = ref('')
const taxRate = ref(0)

const toast = ref(null)

const { lookupItemInCache } = useItemCache()
const loadedItemCode = ref('')
const currentItemCode = computed(() => props.itemCode || loadedItemCode.value)

const cachedItem = computed(() => {
  if (!currentItemCode.value) return null
  return lookupItemInCache(currentItemCode.value)
})

const {
  fetchSupplierPurchaseHistory,
  getSupplierItemHistoryFromCache,
  fetchOtherSuppliersItemHistory,
  otherSuppliersItemHistory,
  historyLoading,
  otherSuppliersHistoryLoading
} = useCustomerHistory()

const sameSupplierHistory = computed(() => {
  if (!currentItemCode.value) return []
  return getSupplierItemHistoryFromCache(currentItemCode.value)
})

function formatDateShort(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  return `${day}-${month}-${year}`
}

function showToast(message, type = 'success') {
  toast.value = { message, type }
  setTimeout(() => {
    if (toast.value && toast.value.message === message) {
      toast.value = null
    }
  }, 3000)
}

const calculatedRatesByUom = computed(() => {
  const result = {}
  if (!uoms.value.length || !prices.value.length) return result

  // 1. Determine the purchase rate for the stock UOM first to use as a base
  let stockPurchaseRate = 0
  const initialUomData = uoms.value.find(u => u.uom === props.initialUom)
  if (initialUomData && props.initialRate) {
    stockPurchaseRate = props.initialRate / initialUomData.conversion_factor
  }

  for (const u of uoms.value) {
    const rates = []
    // Base rate for this UOM is the first price list's rate for this UOM
    let firstRate = prices.value[0]?.uom_rates[u.uom] || 0
    
    // If we have an entered purchase rate, derive this UOM's landing cost
    if (stockPurchaseRate > 0) {
      const uomPurchaseRate = stockPurchaseRate * u.conversion_factor
      const netRate = uomPurchaseRate * (1 - props.initialDiscount / 100)
      if (!props.isInclusive) {
        firstRate = netRate * (1 + props.taxRate / 100)
      } else {
        firstRate = netRate
      }
    }
    
    rates.push(firstRate)
    
    for (let i = 1; i < prices.value.length; i++) {
      const prev = rates[i - 1]
      const markup = prices.value[i]?.markup || 0
      rates.push(prev * (1 + markup / 100))
    }
    result[u.uom] = rates
  }
  return result
})

watch(() => props.initialFactor, (val) => {
  factor.value = val
})

watch(() => props.itemCode, (newVal) => {
  if (newVal) {
    loadPrices(newVal)
    manualItemCode.value = newVal
  }
})

watch(() => prices.value, (newPrices) => {
  if (!newPrices || !stockUom.value) return
  
  // 1. Sync base rate with stock UOM proposed rate
  newPrices.forEach(p => {
    const stockRate = p.uom_rates[stockUom.value]
    if (stockRate !== undefined && p.rate !== stockRate) {
      p.rate = stockRate
    }
  })

  // 2. Persist markups to local storage
  const markups = {}
  newPrices.forEach(p => {
    if (p.price_list) markups[p.price_list] = p.markup
  })
  localStorage.setItem('sspl_pricelist_markups', JSON.stringify(markups))
}, { deep: true })

async function loadPrices(code) {
  if (!code) return
  loading.value = true
  try {
    if (props.supplier) {
      fetchSupplierPurchaseHistory(props.supplier)
    }
    fetchOtherSuppliersItemHistory(code, props.supplier)

    const cached = lookupItemInCache(code)
    let data
    if (cached) {
      console.log('[PriceListUpdate] loading prices from cache for:', code)
      const localPriceLists = JSON.parse(localStorage.getItem('wb-pricelist') || '[]')
      if (!localPriceLists.length) {
        localPriceLists.push('Standard Selling', 'Standard Buying')
      }
      const uomsList = [
        { uom: cached.uom, conversion_factor: 1.0 },
        ...(cached.uoms || []).filter(u => u.uom !== cached.uom)
      ]
      const pricesList = localPriceLists.map(plName => {
        const basePriceEntry = (cached.price_lists || []).find(pl => pl.name === plName)
        const baseRate = basePriceEntry ? parseFloat(basePriceEntry.rate || 0) : 0.0
        
        const uomRatesMap = {}
        for (const u of uomsList) {
          const cachedUomPl = cached.uom_price_lists?.[plName]
          const uomRate = cachedUomPl?.[u.uom] !== undefined ? parseFloat(cachedUomPl[u.uom] || 0) : 0.0
          uomRatesMap[u.uom] = uomRate
        }
        
        return {
          price_list: plName,
          buying: plName.toLowerCase().includes('buying'),
          selling: plName.toLowerCase().includes('selling'),
          rate: baseRate,
          uom_rates: uomRatesMap,
          exists: baseRate > 0 || Object.values(uomRatesMap).some(r => r > 0),
          item_price_name: null
        }
      })
      data = {
        prices: pricesList,
        uoms: uomsList,
        stock_uom: cached.uom,
        item_name: cached.item_name,
        pricelist_percentages: cached.pricelist_percentages || [],
        hsn_sac: cached.hsn_sac || '',
        tax_rate: cached.tax_rate || 0
      }
    } else {
      console.log('[PriceListUpdate] loading prices from server for:', code)
      data = await frappeGet('ssplbilling.api.pricelist_api.get_item_prices', { item_code: code })
    }

    loadedItemCode.value = code
    itemName.value = data.item_name || ''
    stockUom.value = data.stock_uom || ''
    hsnSac.value = data.hsn_sac || ''
    taxRate.value = data.tax_rate || 0

    // Ensure stock UOM is always first and there are no duplicate UOM rows
    const rawUoms = data.uoms || []
    const normalizedUoms = []
    if (stockUom.value) {
      const stockUomEntry = rawUoms.find(u => u.uom === stockUom.value)
      normalizedUoms.push({
        uom: stockUom.value,
        conversion_factor: stockUomEntry ? stockUomEntry.conversion_factor : 1.0
      })
    }
    for (const u of rawUoms) {
      if (u.uom !== stockUom.value && !normalizedUoms.some(nu => nu.uom === u.uom)) {
        normalizedUoms.push(u)
      }
    }
    uoms.value = normalizedUoms

    hasFetchedPercentages.value = !!(data.pricelist_percentages && data.pricelist_percentages.length > 0)


    const savedMarkups = JSON.parse(localStorage.getItem('sspl_pricelist_markups') || '{}')

    prices.value = (data.prices || []).map((p, idx, arr) => {
      let markup = 0
      
      // 1. Prioritize fetched markup from child table in item master
      const fetched = (data.pricelist_percentages || []).find(fp => fp.pricelist === p.price_list)
      if (fetched) {
        markup = parseFloat(fetched.percentage) || 0
      }
      // 2. Fallback to saved markup from local storage if it exists
      else if (savedMarkups[p.price_list] !== undefined) {
        markup = savedMarkups[p.price_list]
      }
      // 3. Fallback to calculating markup from existing rates
      else if (idx > 0) {
        const prevRate = arr[idx - 1].rate || 1
        markup = Number(((p.rate / prevRate - 1) * 100).toFixed(2))
      }
      
      const res = {
        ...p,
        markup,
        original_rate: p.rate,
        original_uom_rates: { ...(p.uom_rates || {}) },
      }

      // Apply initial rate from props if provided for this price list and UOM
      if (props.selectedPriceList && p.price_list === props.selectedPriceList && props.initialRate && props.initialUom) {
        res.uom_rates[props.initialUom] = props.initialRate
        if (props.initialUom === stockUom.value) {
          res.rate = props.initialRate
        }
      }
      return res
    })

    // Set active row to selected price list if exists
    activeRow.value = 0 // In transposed, activeRow is UOM index
    let startPlIdx = 0
    if (props.selectedPriceList) {
      const idx = prices.value.findIndex(p => p.price_list === props.selectedPriceList)
      if (idx !== -1) startPlIdx = idx
    }

    nextTick(() => {
      // Always focus the first UOM rate of the first price list
      focusInput('rate-0-0')
    })
  } catch (e) {
    showToast('Failed to load prices: ' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

function applyCalc(p, idx) {
  p.rate = (calculatedRatesByUom.value[stockUom.value] || [])[idx] || 0
  for (const u of uoms.value) {
    p.uom_rates[u.uom] = Number(((calculatedRatesByUom.value[u.uom] || [])[idx] || 0).toFixed(2))
  }
}

async function saveAll() {
  const code = currentItemCode.value
  if (!code) return

  // Only update prices that have changed (base rate or any uom rate)
  const changedPrices = prices.value.filter(p => {
    if (p.rate !== p.original_rate) return true
    for (const u of uoms.value) {
      if ((p.uom_rates[u.uom] ?? 0) !== (p.original_uom_rates[u.uom] ?? 0)) return true
    }
    return false
  })
  const factorChanged = factor.value !== props.initialFactor

  if (!changedPrices.length && !factorChanged) {
    if (props.isSubWindow) emit('close')
    return
  }

  saving.value = true
  try {
    if (changedPrices.length) {
      await frappePost('ssplbilling.api.pricelist_api.update_multiple_prices', {
        item_code: code,
        prices: JSON.stringify(changedPrices)
      })
    }

    // Emit back all relevant data
    emit('saved', {
      changedPrices,
      factor: factor.value,
      factorChanged
    })

    if (props.isSubWindow) emit('close')
    else showToast('Prices updated successfully', 'success')
  } catch (e) {
    showToast('Update failed: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

async function savePercentageToItemMaster() {
  const code = currentItemCode.value
  if (!code) {
    showToast('Item code is required.', 'error')
    return
  }

  const percentages = prices.value.map(p => ({
    pricelist: p.price_list,
    percentage: p.markup !== undefined && p.markup !== null ? String(p.markup) : '0'
  }))

  savingPercentage.value = true
  try {
    await frappePost('ssplbilling.api.pricelist_api.save_item_pricelist_percentages', {
      item_code: code,
      percentages: JSON.stringify(percentages)
    })
    showToast('Percentages saved to Item Master successfully.', 'success')
  } catch (e) {
    console.error('Failed to save percentages:', e)
    showToast('Failed to save percentages: ' + (e.message || e), 'error')
  } finally {
    savingPercentage.value = false
  }
}

function onCalcEnter(idx) {
  if (idx < prices.value.length - 1) {
    focusInput(`calc-${idx + 1}`)
  } else {
    focusInput(`rate-0-0`)
  }
}

function onRateEnter(idx, uidx) {
  activeRow.value = uidx
  // Move right across Price List columns first
  if (idx < prices.value.length - 1) {
    focusInput(`rate-${idx + 1}-${uidx}`)
    return
  }
  // Last PL column: go to next UOM row
  goToNextRow(uidx)
}

function goToNextRow(uidx) {
  if (uidx < uoms.value.length - 1) {
    activeRow.value = uidx + 1
    focusInput(`rate-0-${uidx + 1}`)
  } else {
    saveAll()
  }
}

function moveVertical(uidx, dir, idx) {
  const next = uidx + dir
  if (next >= 0 && next < uoms.value.length) {
    activeRow.value = next
    focusInput(`rate-${idx}-${next}`)
  }
}

function focusInput(key) {
  nextTick(() => {
    const el = inputRefs.value[key]
    if (el) {
      el.focus()
      el.select()
    }
  })
}

const handleGlobalKeydown = (e) => {
  if (e.key === 'F8') {
    e.preventDefault()
    e.stopPropagation()
    saveAll()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    if (props.isSubWindow) emit('close')
    else router.push('/')
  } else if (e.key === 'PageUp') {
    e.preventDefault()
    e.stopPropagation()
    // Focus the first editable Calc input (idx 1 since idx 0 is usually buying/base)
    // If only one PL exists or we want the very first possible calc input:
    if (inputRefs.value['calc-1']) {
      focusInput('calc-1')
    } else {
      focusInput('calc-0')
    }
  } else {
    // Disable all other global shortcuts by stopping propagation
    // This prevents parent containers/window listeners from catching common keys (F1, F2, etc.)
    e.stopPropagation()
  }
}

onMounted(() => {
  const code = props.itemCode || route.query.item_code
  if (code) {
    loadPrices(code)
    manualItemCode.value = code
  }
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>
