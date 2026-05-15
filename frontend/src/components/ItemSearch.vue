<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm outline-none"
    @click.self="$emit('close')"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-5 py-4 flex items-center gap-8 bg-[var(--color-surface-raised)]">
        <div class="shrink-0">
          <div class="text-2xl text-[var(--color-text)] whitespace-nowrap">Detailed Item Search ({{ searchType }})</div>
          <div class="text-sm text-[var(--color-text-muted)]">View stock info and select item</div>
        </div>

        <!-- Search input integrated into header -->
        <div class="flex-1 relative">
          <input
            ref="searchInput"
            v-model="query"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] p-[8px] text-4xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/20"
            placeholder="Type item code or name..."
            @keydown.esc.stop="$emit('close')"
          />
          <div v-if="loading && !allItems.length" class="absolute right-4 top-1/2 -translate-y-1/2">
            <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent"></span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="isDecrypted = !isDecrypted"
            class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-all"
            :class="isDecrypted ? 'border-[var(--color-warning)] bg-[var(--color-warning)]/20 text-[var(--color-warning)]' : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)]'"
          >
            <span>{{ isDecrypted ? '🔓' : '🔒' }}</span>
            {{ isDecrypted ? 'Decrypt' : 'Encrypt' }}
          </button>
          <button @click="$emit('close')" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
        </div>
      </div>

      <!-- Detail Panel -->
      <div v-if="results[selectedIdx]" class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10 px-6 py-4">
        <div class="flex flex-col gap-4">
          <div class="flex flex-wrap items-start gap-x-10 gap-y-3">
            <div class="flex flex-col min-w-[150px]">
              <span class="text-base uppercase text-[var(--color-text-muted)] font-medium">Current Stock</span>
              <span class="text-3xl font-bold" :class="results[selectedIdx].stock <= 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                {{ results[selectedIdx].stock || 0 }} {{ results[selectedIdx].uom || 'Nos' }}
              </span>
            </div>
            <div v-if="warehouse" class="flex flex-col min-w-[150px] max-w-[250px]">
              <span class="text-base uppercase text-[var(--color-text-muted)] font-medium">Warehouse</span>
              <span class="truncate text-xl text-[var(--color-text)]" :title="warehouse">{{ warehouse }}</span>
            </div>
            <div class="flex flex-col min-w-[150px]">
              <span class="text-base uppercase text-[var(--color-text-muted)] font-medium">{{ priceList || 'Rate' }}</span>
              <span class="text-3xl text-[var(--color-text)] font-mono">
                {{ encPrice(results[selectedIdx].price || 0) }}
              </span>
            </div>
            <div class="flex flex-col flex-[0.6]">
              <span class="text-base uppercase text-[var(--color-text-muted)] font-medium">Item Name</span>
              <span class="text-2xl text-[var(--color-text)] truncate font-semibold">{{ results[selectedIdx].item_name }}</span>
            </div>
            <div class="flex flex-col flex-[0.4]">
              <span class="text-base uppercase text-[var(--color-text-muted)] font-medium">Default Supplier</span>
              <span class="text-2xl text-[var(--color-text-muted)] truncate" :title="results[selectedIdx].default_supplier">{{ results[selectedIdx].default_supplier || '--' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Table -->
      <div ref="scrollContainer" class="flex-1 overflow-y-auto">
        <table class="w-full text-4xl">
          <thead class="sticky top-0 bg-[var(--color-surface-raised)] shadow-sm z-10">
            <tr class="text-2xl uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <th class="p-[5px] text-left w-1/4">Item Code</th>
              <th class="p-[5px] text-left">Item Name</th>
              <th class="p-[5px] text-right">{{ priceList || 'Rate' }}</th>
              <th class="p-[5px] text-right">Stock</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr
              v-for="(item, idx) in results"
              :key="item.item_code"
              class="cursor-pointer transition-colors"
              :class="selectedIdx === idx ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'hover:bg-[var(--color-midlight)]/20'"
              @click="$emit('select', item)"
            >
              <td class="p-[5px] font-mono text-5xl flex items-center gap-2" :class="selectedIdx === idx ? 'text-[var(--color-text-on-highlight)] font-bold' : 'text-[var(--color-highlight)]'">
                <div v-if="item.has_history" class="flex flex-col items-center">
                  <span class="h-3 w-3 shrink-0 rounded-full animate-pulse bg-[var(--color-highlight)]" :class="selectedIdx === idx ? 'bg-[var(--color-text-on-highlight)]/40' : 'bg-[var(--color-highlight)]'" title="Previously sold to this customer"></span>
                  <span class="text-[10px] mt-1 uppercase font-bold text-[var(--color-text-muted)]" :class="selectedIdx === idx ? 'text-[var(--color-text-on-highlight)]' : ''">{{ item.history_qty }}</span>
                </div>
                <span>{{ item.item_code }}</span>
              </td>
              <td class="p-[5px]">
                <div class="font-medium" :class="selectedIdx === idx ? 'text-[var(--color-text-on-highlight)] font-bold' : 'text-[var(--color-text)]'">{{ item.item_name }}</div>
              </td>
              <td class="p-[5px] text-right font-mono tracking-wider" :class="selectedIdx === idx ? 'text-[var(--color-text-on-highlight)] font-bold' : 'text-[var(--color-warning)]'">
                <span>{{ encPrice(item.price || 0) }}</span>
              </td>
              <td class="p-[5px] text-right">
                <span :class="selectedIdx === idx ? 'text-[var(--color-text-on-highlight)] font-bold' : (item.stock <= 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]')">
                  {{ item.stock || 0 }}
                </span>
              </td>
            </tr>
            <tr v-if="!results.length && !loading">
              <td colspan="4" class="px-5 py-12 text-center text-[var(--color-text-muted)] text-xl italic">
                No items found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- UOM Prices Grid -->
      <div v-if="insightData?.uoms?.length > 0" class="border-t border-[var(--color-border)] bg-[var(--color-bg)] px-0 py-0">
        <div class="overflow-x-auto scrollbar-none">
          <table class="w-full border-collapse">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50">
                <th class="border border-[var(--color-border)] px-2 py-1 text-left text-sm font-normal text-[var(--color-text-muted)] uppercase w-32">UOM</th>
                <th v-for="pl in insightData.priceLists" :key="pl.name" class="border border-[var(--color-border)] px-2 py-1 text-right text-xl font-normal text-[var(--color-text-muted)] uppercase min-w-[120px]">
                  {{ pl.name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="uom in insightData.uoms" :key="uom" class="hover:bg-[var(--color-midlight)]/30">
                <td class="border border-[var(--color-border)] px-2 py-1 text-xl text-[var(--color-text-muted)] truncate">{{ uom }}</td>
                <td v-for="pl in insightData.priceLists" :key="pl.name" class="border border-[var(--color-border)] px-2 py-1 text-right font-mono text-[var(--color-warning)] text-3xl tracking-widest">
                  {{ pl.rates[uom] != null ? encPrice(pl.rates[uom]) : '--' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Footer shortcuts -->
      <div class="border-t border-[var(--color-border)] px-5 py-3 bg-[var(--color-surface-raised)] flex gap-6 text-xs text-[var(--color-text-muted)] uppercase tracking-widest font-bold">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Home</kbd> Search</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">↑↓</kbd> Navigate</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Enter</kbd> Select</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+E</kbd> Toggle Enc</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F2</kbd> New</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F3</kbd> Edit</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F4</kbd> Stock Ledger</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">S+F4</kbd> Price</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F5</kbd> Sync</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Close</span>
      </div>

      <DateFilter
        v-if="showDateModal"
        :show="showDateModal"
        :customer-name="results[selectedIdx]?.item_name"
        @close="showDateModal = false"
        @confirm="handleDateConfirm"
      />

      <ItemCreation
        v-if="showCreationModal"
        :show="showCreationModal"
        @close="showCreationModal = false"
        @created="handleItemCreated"
      />

      <ItemCreation
        v-if="showEditModal"
        :show="showEditModal"
        :edit-item-code="editItemCode"
        @close="showEditModal = false; focus()"
        @created="handleItemUpdated"
      />

      <PriceListUpdate
        v-if="showPriceUpdateModal"
        :is-sub-window="true"
        :item-code="results[selectedIdx]?.item_code"
        :selected-price-list="priceList"
        @close="showPriceUpdateModal = false; focus()"
        @saved="showPriceUpdateModal = false; preloadItems(true); focus()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed, onMounted, onUnmounted } from 'vue'
import { useItemCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'
import { frappeGet } from '../api.js'
import DateFilter from './DateFilter.vue'
import ItemCreation from './ItemCreation.vue'
import PriceListUpdate from '../pages/PriceListUpdate.vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

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
  },
  initialQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'select'])

useSubwindowWatcher(computed(() => props.show), {
  ArrowDown: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, results.value.length - 1)
  },
  ArrowUp: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  },
  'CTRL+E': (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    isDecrypted.value = !isDecrypted.value
  },
  Enter: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    const item = results.value[selectedIdx.value]
    if (item) {
      e.preventDefault()
      if (props.skipDateFilter) {
        emit('select', item)
      } else {
        showDateModal.value = true
      }
    }
  },
  F5: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    preloadItems(true)
  },
  F2: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    showCreationModal.value = true
  },
  F3: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    openEditModal()
  },
  F4: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    if (results.value[selectedIdx.value]) {
      isSlMode.value = true
      showDateModal.value = true
    }
  },
  'SHIFT+F4': (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    if (results.value[selectedIdx.value]) showPriceUpdateModal.value = true
  },
  Home: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    focus()
  },
  Escape: (e) => {
    if (showDateModal.value || showCreationModal.value || showEditModal.value || showPriceUpdateModal.value) return
    e.preventDefault()
    emit('close')
  }
})

const { items: allItems, refreshItemCache, lookupItemInCache, lastSync, syncLoading: loading, lastParams } = useItemCache()
const { hasHistory, getItemHistoryFromCache } = useCustomerHistory()

const query = ref('')
const selectedIdx = ref(0)
const searchInput = ref(null)
const scrollContainer = ref(null)
const showDateModal = ref(false)
const isSlMode = ref(false)
const showCreationModal = ref(false)
const showEditModal = ref(false)
const editItemCode = ref('')
const showPriceUpdateModal = ref(false)
const insightData = ref(null)
const cipherMap = ref([])
const isDecrypted = ref(false)

// ─── Encryption Logic ────────────────────────────────────────────────────────

function loadCipherMap() {
  try {
    const raw = localStorage.getItem('wb-cipher')
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
  if (isDecrypted.value || !cipherMap.value.length) return str
  return str.replace(/\d/g, d => cipherMap.value[parseInt(d)] ?? d)
}

// ─── Data Preloading ─────────────────────────────────────────────────────────

async function preloadItems(forceRefresh = false) {
  const currentWarehouse = props.warehouse || null
  const currentPriceList = props.priceList || null
  
  const paramsChanged = forceRefresh || 
    lastParams.value.searchType !== props.searchType ||
    lastParams.value.priceList !== currentPriceList ||
    lastParams.value.warehouse !== currentWarehouse

  if (!paramsChanged && allItems.value.length > 0) return

  try {
    await refreshItemCache(props.searchType, currentPriceList, currentWarehouse)
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
  
  // Extract all UOMs for this item
  const itemUoms = (item.uoms || []).map(u => u.uom)
  if (!itemUoms.includes(item.uom)) itemUoms.unshift(item.uom)
  
  // Prepare a grid: { pl_name: { uom: rate } }
  const allPriceLists = (item.price_lists || []).map(pl => pl.name)
  const uomPricesMap = {}
  
  // Initialize with base rates
  for (const pl of item.price_lists || []) {
    uomPricesMap[pl.name] = { [item.uom]: pl.rate }
  }
  
  // Merge in per-UOM overrides from the cache
  if (item.uom_price_lists) {
    for (const [plName, uomMap] of Object.entries(item.uom_price_lists)) {
      if (!uomPricesMap[plName]) uomPricesMap[plName] = {}
      for (const [uomName, rate] of Object.entries(uomMap)) {
        uomPricesMap[plName][uomName] = rate
      }
    }
  }

  insightData.value = {
    uoms: itemUoms,
    priceLists: Object.keys(uomPricesMap).map(name => ({
      name,
      rates: uomPricesMap[name]
    }))
  }
}

// ─── Local Filtering ─────────────────────────────────────────────────────────

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  const terms = q.split(/\s+/).filter(Boolean)
  let list = allItems.value

  if (terms.length > 0) {
    list = allItems.value.filter(i => {
      const code = (i.item_code || '').toLowerCase()
      const name = (i.item_name || '').toLowerCase()
      const barcodes = (i.barcodes || '').toLowerCase().split(',')
      return terms.every(term => 
        code.includes(term) || 
        name.includes(term) || 
        barcodes.some(b => b.includes(term))
      )
    })

    // Sort: prioritize exact match on item_code or ANY barcode
    list.sort((a, b) => {
      const codeA = (a.item_code || '').toLowerCase()
      const codeB = (b.item_code || '').toLowerCase()
      const barcodesA = (a.barcodes || '').toLowerCase().split(',')
      const barcodesB = (b.barcodes || '').toLowerCase().split(',')
      
      const isExactA = codeA === q || barcodesA.includes(q)
      const isExactB = codeB === q || barcodesB.includes(q)
      
      if (isExactA && !isExactB) return -1
      if (!isExactA && isExactB) return 1
      return 0
    })
  }

  return list.slice(0, 100).map(i => {
    // Find the rate for the selected price list from props
    let displayPrice = i.price
    if (props.priceList) {
      // 1. Check direct price_lists cache
      if (i.price_lists) {
        const pl = i.price_lists.find(p => p.name === props.priceList)
        if (pl) displayPrice = pl.rate
      }
      // 2. Check per-UOM overrides
      if (i.uom_price_lists?.[props.priceList]) {
        const uomRate = i.uom_price_lists[props.priceList][i.uom]
        if (uomRate != null) displayPrice = uomRate
      }
    }

    return {
      ...i,
      price: displayPrice,
      has_history: hasHistory(i.item_code),
      history_qty: getItemHistoryFromCache(i.item_code).reduce((s, h) => s + h.qty, 0)
    }
  })
})

watch(query, () => {
  selectedIdx.value = 0
})

watch([selectedIdx, results], () => {
  const item = results.value[selectedIdx.value]
  if (item) console.log('[ItemSearch] selected item warehouse_stock:', item.warehouse_stock)
  updateItemInsight(item)
}, { immediate: true })

// ─── Navigation & Events ─────────────────────────────────────────────────────

function openEditModal() {
  const item = results.value[selectedIdx.value]
  if (!item) return
  editItemCode.value = item.item_code
  showEditModal.value = true
}

function handleItemUpdated() {
  showEditModal.value = false
  preloadItems(true)
  focus()
}

function handleDateConfirm(dates) {
  const item = results.value[selectedIdx.value]
  if (item) {
    if (isSlMode.value) {
      showDateModal.value = false
      isSlMode.value = false
      window.dispatchEvent(new CustomEvent('wb-open-stock-ledger', {
        detail: {
          item_code: item.item_code,
          from: dates.from,
          to: dates.to
        }
      }))
      emit('close')
    } else {
      showDateModal.value = false
      emit('select', item, dates)
    }
  }
}

function handleItemCreated(item) {
  showCreationModal.value = false
  // Refresh cache to include new item
  preloadItems(true).then(() => {
    // Select the new item after refresh
    emit('select', item)
  })
}

function focus() {
  setTimeout(() => {
    searchInput.value?.focus()
    searchInput.value?.select()
  }, 0)
}

function closeSubForm() {
  showDateModal.value = false
  showCreationModal.value = false
  showEditModal.value = false
  focus()
}

function handleGlobalItemSearch() {
  if (props.show && results.value[selectedIdx.value]) {
    // If already open and an item is selected, trigger stock ledger (via date selector)
    isSlMode.value = true
    showDateModal.value = true
  } else {
    preloadItems(true)
  }
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

watch(() => props.show, async (newVal) => {
  if (newVal) {
    query.value = ''
    isDecrypted.value = false
    loadCipherMap()
    focus() // Focus immediately
    await preloadItems()
    focus() // Refocus after items load if needed
    if (props.initialQuery) {
      const idx = results.value.findIndex(i => i.item_code === props.initialQuery)
      if (idx >= 0) {
        selectedIdx.value = idx
      } else {
        // No exact match — treat as a failed barcode scan: pre-fill the search box
        query.value = props.initialQuery
      }
    }
  } else {
    showDateModal.value = false
    showCreationModal.value = false
    showEditModal.value = false
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
