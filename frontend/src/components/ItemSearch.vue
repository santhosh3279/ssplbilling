<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 outline-none" 
    @click.self="$emit('close')"
    @keydown="handleGlobalKeydown"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between bg-gray-50">
        <div>
          <div class="text-2xl font-semibold text-gray-700">Detailed Item Search ({{ searchType }})</div>
          <div class="text-lg text-gray-500">View stock info and select item</div>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="preloadItems(true)" 
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 transition-colors"
            :disabled="loading"
          >
            <span v-if="loading" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent mr-1"></span>
            <span v-else>🔄</span> Refresh <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-gray-400">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-gray-100 p-4 relative">
        <input
          ref="searchInput"
          v-model="query"
          class="w-full rounded border border-gray-300 px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Type item code or name..."
          @keydown.esc.stop="$emit('close')"
        />
        <div v-if="loading && !allItems.length" class="absolute right-8 top-1/2 -translate-y-1/2">
          <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></span>
        </div>
      </div>

      <!-- Detail Panel -->
      <div v-if="results[selectedIdx]" class="border-b border-gray-200 bg-blue-50/30 px-6 py-3">
        <div class="flex flex-col gap-3">
          <div class="flex flex-wrap items-start gap-x-8 gap-y-2">
            <div class="flex flex-col min-w-[130px]">
              <span class="text-[10px] font-bold uppercase text-gray-400">Current Stock</span>
              <span class="text-xl font-bold" :class="results[selectedIdx].stock <= 0 ? 'text-red-600' : 'text-green-600'">
                {{ results[selectedIdx].stock || 0 }} {{ results[selectedIdx].uom || 'Nos' }}
              </span>
            </div>
            <div v-if="warehouse" class="flex flex-col min-w-[130px] max-w-[200px]">
              <span class="text-[10px] font-bold uppercase text-gray-400">Warehouse</span>
              <span class="truncate text-sm font-semibold text-gray-600" :title="warehouse">{{ warehouse }}</span>
            </div>
            <div class="flex flex-col min-w-[130px]">
              <span class="text-[10px] font-bold uppercase text-gray-400">Default Rate</span>
              <span class="text-xl font-bold text-gray-700">
                ₹{{ (results[selectedIdx].price || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </span>
            </div>
            <div class="flex flex-col flex-1">
              <span class="text-[10px] font-bold uppercase text-gray-400">Item Name</span>
              <span class="text-lg text-gray-700 font-semibold">{{ results[selectedIdx].item_name }}</span>
            </div>
          </div>

          <!-- All Price Lists (Encrypted) -->
          <div v-if="insightData?.priceLists?.length" class="flex flex-col gap-1 border-t border-blue-100 pt-2">
            <span class="text-[10px] font-bold uppercase text-gray-400">All Price Lists</span>
            <div class="flex flex-wrap gap-3">
              <span v-for="pl in insightData.priceLists" :key="pl.name" class="rounded bg-amber-50 px-2.5 py-1 text-sm border border-amber-100">
                <span class="text-gray-500 text-[10px] uppercase font-bold mr-1">{{ pl.name }}:</span>
                <span class="font-mono font-bold text-amber-700">₹{{ encPrice(pl.rate || 0) }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Table -->
      <div ref="scrollContainer" class="flex-1 overflow-y-auto">
        <table class="w-full text-2xl">
          <thead class="sticky top-0 bg-white shadow-sm">
            <tr class="text-lg font-bold uppercase tracking-wider text-gray-600 border-b">
              <th class="px-5 py-3 text-left w-1/4">Item Code</th>
              <th class="px-5 py-3 text-left">Item Name</th>
              <th class="px-5 py-3 text-right">Rate</th>
              <th class="px-5 py-3 text-right">Stock</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="(item, idx) in results"
              :key="item.item_code"
              class="cursor-pointer"
              :class="{ 'bg-blue-200': selectedIdx === idx }"
              @click="$emit('select', item)"
            >
              <td class="px-5 py-2 font-mono text-xl text-blue-600 flex items-center gap-2">
                <span v-if="item.has_history" class="h-2 w-2 shrink-0 rounded-full bg-blue-500 animate-pulse" title="Previously sold to this customer"></span>
                <span>{{ item.item_code }}</span>
              </td>
              <td class="px-5 py-2">
                <div class="font-medium text-gray-800">{{ item.item_name }}</div>
              </td>
              <td class="px-5 py-2 text-right font-mono">
                <span>₹{{ (item.price || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
              </td>
              <td class="px-5 py-2 text-right">
                <span class="font-bold" :class="item.stock <= 0 ? 'text-red-600' : 'text-gray-700'">
                  {{ item.stock || 0 }}
                </span>
              </td>
            </tr>
            <tr v-if="!results.length && !loading">
              <td colspan="4" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                No items found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer shortcuts -->
      <div class="border-t border-gray-200 px-5 py-3 bg-gray-50 flex gap-6 text-xs text-gray-400 uppercase tracking-widest font-bold">
        <span><kbd class="rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-[10px]">↑↓</kbd> Navigate</span>
        <span><kbd class="rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-[10px]">Enter</kbd> Select</span>
        <span><kbd class="rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-[10px]">F5</kbd> Refresh</span>
        <span><kbd class="rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-[10px]">Esc</kbd> Close</span>
      </div>

      <!-- SUB-MODALS (Date) -->
      <DateFilter
        v-if="showDateModal"
        :show="showDateModal"
        :customer-name="results[selectedIdx]?.item_name"
        @close="showDateModal = false"
        @confirm="handleDateConfirm"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, onMounted, onUnmounted } from 'vue'
import { useItemCache } from '../services/itemCache.js'
import { frappeGet } from '../api.js'
import DateFilter from './DateFilter.vue'

const props = defineProps({
  show: Boolean,
  searchType: {
    type: String,
    default: 'Sales' // 'Sales' or 'Purchase'
  },
  priceList: {
    type: String,
    default: ''
  },
  warehouse: String,
  skipDateFilter: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'select'])

const { items: allItems, refreshItemCache, lookupItemInCache, lastSync, syncLoading: loading, hasHistory } = useItemCache()

const query = ref('')
const selectedIdx = ref(0)
const searchInput = ref(null)
const scrollContainer = ref(null)
const showDateModal = ref(false)
const insightData = ref(null)
const cipherMap = ref([])
const firstLoadDone = ref(false)

// ─── Encryption Logic ────────────────────────────────────────────────────────

function loadCipherMap() {
  try {
    const cached = JSON.parse(localStorage.getItem('wb-billing-settings-v2') || 'null')
    const raw = cached?.data?.cipher_map
    if (raw) {
      const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
      if (Array.isArray(parsed) && parsed.length === 10) {
        cipherMap.value = parsed
      }
    }
  } catch (e) {
    console.warn('[ItemSearch] Failed to load cipher map:', e)
  }
}

function encPrice(val) {
  const n = Number(val || 0)
  const str = n % 1 === 0 ? String(n) : n.toFixed(2)
  if (!cipherMap.value.length) return str
  return str.replace(/\d/g, d => cipherMap.value[parseInt(d)] ?? d)
}

// ─── Data Preloading ─────────────────────────────────────────────────────────

async function preloadItems(forceRefresh = false) {
  if (!forceRefresh && allItems.value.length > 0) return

  try {
    await refreshItemCache(props.searchType, props.priceList, props.warehouse || null)
  } catch (e) {
    console.error('[ItemSearch] Preload failed:', e)
  }
}

// ─── Insight Fetching ────────────────────────────────────────────────────────

function updateItemInsight(item) {
  if (!item) {
    insightData.value = null
    return
  }
  
  // Use the price lists already available in the cached item object
  insightData.value = {
    priceLists: (item.price_lists || []).map(pl => ({ 
      name: pl.name, 
      rate: pl.rate 
    }))
  }
}

// ─── Local Filtering ─────────────────────────────────────────────────────────

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  let list = allItems.value
  if (q) {
    list = allItems.value.filter(i => 
      (i.item_code || '').toLowerCase().includes(q) ||
      (i.item_name || '').toLowerCase().includes(q)
    )
  }

  return list.slice(0, 100).map(i => ({
    ...i,
    has_history: hasHistory(i.item_code)
  }))
})

watch(query, () => {
  selectedIdx.value = 0
})

watch([selectedIdx, results], () => {
  const item = results.value[selectedIdx.value]
  updateItemInsight(item)
}, { immediate: true })

// ─── Navigation & Events ─────────────────────────────────────────────────────

function handleGlobalKeydown(e) {
  if (showDateModal.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, results.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  } else if (e.key === 'Enter') {
    const item = results.value[selectedIdx.value]
    if (item) {
      e.preventDefault()
      if (props.skipDateFilter) {
        emit('select', item)
      } else {
        showDateModal.value = true
      }
    }
  } else if (e.key === 'F5') {
    e.preventDefault()
    preloadItems(true)
  }
}

function handleDateConfirm(dates) {
  const item = results.value[selectedIdx.value]
  if (item) {
    showDateModal.value = false
    emit('select', item, dates)
  }
}

function focus() {
  nextTick(() => {
    searchInput.value?.focus()
    searchInput.value?.select()
  })
}

function closeSubForm() {
  showDateModal.value = false
  focus()
}

/** 
 * Refresh stock when CTRL+I (item search) is pressed anywhere.
 * This ensures that when the modal opens, stock is already fresh.
 */
function handleGlobalItemSearch() {
  preloadItems(true)
}

defineExpose({ focus, closeSubForm })

watch(selectedIdx, async (idx) => {
  await nextTick()
  const container = scrollContainer.value
  const activeRow = container?.querySelector(`tbody tr:nth-child(${idx + 1})`)
  
  if (container && activeRow) {
    const rowTop = activeRow.offsetTop
    const rowBottom = rowTop + activeRow.offsetHeight
    const containerScrollTop = container.scrollTop
    const containerHeight = container.offsetHeight
    const headerHeight = container.querySelector('thead')?.offsetHeight || 50

    if (rowTop < containerScrollTop + headerHeight) {
      container.scrollTop = rowTop - headerHeight
    } else if (rowBottom > containerScrollTop + containerHeight) {
      container.scrollTop = rowBottom - containerHeight
    }
  }
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadCipherMap()
    // Refresh only the first time it opens, or if cache is empty
    if (!firstLoadDone.value) {
      preloadItems(true)
      firstLoadDone.value = true
    } else {
      preloadItems()
    }
    focus()
  } else {
    showDateModal.value = false
  }
})

onMounted(() => {
  window.addEventListener('wb-global-item-search', handleGlobalItemSearch)
  if (props.show) {
    loadCipherMap()
  }
})

onUnmounted(() => {
  window.removeEventListener('wb-global-item-search', handleGlobalItemSearch)
})
</script>
