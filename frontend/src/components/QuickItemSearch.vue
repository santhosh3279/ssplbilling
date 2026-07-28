<template>
  <div 
    v-if="props.results.length > 0" 
    class="fixed z-[150] w-[700px] rounded-2xl border-[5px] border-[var(--color-highlight)] bg-[var(--color-bg)] shadow-[0_35px_80px_-15px_rgba(0,0,0,0.7)] overflow-hidden"
    :style="positionStyle"
  >
    <div class="bg-[var(--color-surface)] px-4 py-3 border-b border-[var(--color-border)] flex justify-between items-center">
      <span class="text-[1.125rem] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Search</span>
      <div class="flex items-center gap-3">
        <button 
          @click.stop="handleRefresh" 
          class="p-1 rounded hover:bg-[var(--color-surface-raised)] transition-colors text-[var(--color-text-muted)] hover:text-[var(--color-primary)]"
          :class="{ 'animate-spin text-[var(--color-primary)]': syncLoading }"
          title="Refresh Items Cache"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M8 16H3v5"></path></svg>
        </button>
        <span class="text-[1.125rem] text-[var(--color-text-muted)]">{{ filteredItems.length }} items</span>
      </div>
    </div>
    
    <div 
      ref="scrollContainer" 
      class="max-h-[500px] overflow-y-auto scrollbar-none relative"
      @scroll="handleScroll"
    >
      <!-- Spacer to enable browser scrollbar -->
      <div :style="{ height: `${spacerHeight}px`, position: 'relative' }">
        <!-- Render only visible items -->
        <div :style="transformStyle">
          <div 
            v-for="itemMeta in visibleItems" 
            :key="itemMeta.item.item_code"
            class="quick-search-item px-4 cursor-pointer border-b border-[var(--color-border)]/50 last:border-0 transition-all h-[80px] box-border flex flex-col justify-center overflow-hidden"
            :class="selectedIndex === itemMeta.globalIndex ? 'bg-[var(--color-focus)] border-l-4 border-l-[var(--color-focus)] font-bold' : 'hover:bg-[var(--color-surface-raised)]/40'"
            @click="$emit('select', itemMeta.item)"
          >
            <div class="flex justify-between items-center gap-4">
              <div class="min-w-0 flex-1 flex items-center gap-3">
                <div v-if="itemMeta.item.has_history" class="h-3 w-3 shrink-0 rounded-full animate-pulse bg-[var(--color-highlight)]" title="Previously sold to this customer"></div>
                <div class="min-w-0 flex-1">
                  <div class="text-3xl font-normal truncate" :class="selectedIndex === itemMeta.globalIndex ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ itemMeta.item.item_name }}</div>
                  <div class="text-2xl font-mono flex flex-wrap items-center gap-x-2 gap-y-0.5" :class="selectedIndex === itemMeta.globalIndex ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]/80'">
                    <span>{{ itemMeta.item.item_code }}</span>
                    <span v-if="itemMeta.item.hsn_sac" class="text-lg opacity-70">· HSN: {{ itemMeta.item.hsn_sac }}</span>
                    <span v-if="itemMeta.item.suppliers && itemMeta.item.suppliers.length" class="text-lg opacity-70 truncate max-w-[320px]" :title="itemMeta.item.suppliers.map(s => typeof s === 'string' ? s : s.supplier).join(', ')">· Supp: {{ itemMeta.item.suppliers.map(s => typeof s === 'string' ? s : s.supplier).join(', ') }}</span>
                  </div>
                </div>
              </div>
              <div class="flex flex-col items-end shrink-0">
                <div class="text-[1.75rem] font-mono font-bold" :class="selectedIndex === itemMeta.globalIndex ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]'">{{ formatPrice(getItemPrice(itemMeta.item)) }}</div>
                <div 
                  class="text-[1.09375rem] font-bold"
                  :class="selectedIndex === itemMeta.globalIndex ? '!text-[var(--color-text-on-focus)]' : (itemMeta.item.stock > 20 ? 'text-[var(--color-success)]' : itemMeta.item.stock > 0 ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]')"
                >
                  {{ itemMeta.item.stock }} {{ itemMeta.item.uom }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useItemCache } from '../services/itemCache'
import { useCustomerHistory } from '../composables/useCustomerHistory'

const props = defineProps({
  results: { type: Array, default: () => [] },
  query: { type: String, default: '' },
  priceList: { type: String, default: '' },
  searchType: { type: String, default: 'Sales' },
  warehouse: { type: String, default: '' },
  anchorEl: { type: Object, default: null }, // Optional: to position relative to
  lastItemCode: { type: String, default: '' } // The item code of the last entered item
})

const emit = defineEmits(['select', 'close', 'refresh'])

const { items: allItems, refreshItemCache, syncLoading } = useItemCache()
const { hasHistory } = useCustomerHistory()

async function handleRefresh() {
  if (syncLoading.value) return
  await refreshItemCache(props.searchType, props.priceList, props.warehouse)
  emit('refresh')
}

const selectedIndex = ref(0)
const scrollContainer = ref(null)

// Keep sortedAllItems pointing directly to allItems since they are cached sorted
const sortedAllItems = computed(() => allItems.value)

// Populate items with history
const allItemsWithHistory = computed(() => {
  return sortedAllItems.value.map(item => ({
    ...item,
    has_history: hasHistory(item.item_code)
  }))
})

// Narrow the list down to matches as the user types. A pure-whitespace query
// (e.g. the double-space "go to last item" shortcut) has no real terms, so it
// falls through to the full list instead of filtering to nothing.
const filteredItems = computed(() => {
  const terms = props.query.trim().toLowerCase().split(/\s+/).filter(Boolean)
  if (terms.length === 0) return allItemsWithHistory.value

  return allItemsWithHistory.value.filter(i => {
    const code = (i.item_code || '').toLowerCase()
    const name = (i.item_name || '').toLowerCase()
    const barcodes = (i.barcodes || '').toLowerCase().split(',')
    return terms.every(term =>
      code.includes(term) ||
      name.includes(term) ||
      barcodes.some(b => b.includes(term))
    )
  })
})

// --- Virtual Scroll variables and calculations ---
const scrollTop = ref(0)
const containerHeight = ref(500) // fallback
const itemHeight = 80 // height in pixels matching h-[80px]
const buffer = 10

function handleScroll(e) {
  scrollTop.value = e.target.scrollTop
}

const updateContainerHeight = () => {
  if (scrollContainer.value) {
    containerHeight.value = scrollContainer.value.clientHeight || 500
  }
}

const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / itemHeight) - buffer)
})

const endIndex = computed(() => {
  return Math.min(filteredItems.value.length, Math.ceil((scrollTop.value + containerHeight.value) / itemHeight) + buffer)
})

const visibleItems = computed(() => {
  return filteredItems.value.slice(startIndex.value, endIndex.value).map((item, localIdx) => {
    return {
      item,
      globalIndex: startIndex.value + localIdx
    }
  })
})

const spacerHeight = computed(() => {
  return filteredItems.value.length * itemHeight
})

const transformStyle = computed(() => {
  return {
    transform: `translateY(${startIndex.value * itemHeight}px)`,
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0
  }
})

// Search logic inside total items
const findBestMatchIndex = (query) => {
  if (query === '  ') {
    if (props.lastItemCode) {
      const idx = filteredItems.value.findIndex(i => i.item_code === props.lastItemCode)
      if (idx !== -1) return idx
    }
    return 0
  }

  if (!query) return -1
  const cleanQuery = query.trim().toLowerCase()
  const terms = cleanQuery.split(/\s+/).filter(Boolean)
  if (terms.length === 0) return -1

  const list = filteredItems.value

  // 1. Exact match on item_code or barcode (highest priority)
  let bestIdx = list.findIndex(i => {
    const code = (i.item_code || '').toLowerCase()
    const barcodes = (i.barcodes || '').toLowerCase().split(',')
    return code === cleanQuery || barcodes.includes(cleanQuery)
  })
  if (bestIdx !== -1) return bestIdx

  // 2. Starts with query on item_code or item_name
  bestIdx = list.findIndex(i => {
    const code = (i.item_code || '').toLowerCase()
    const name = (i.item_name || '').toLowerCase()
    return code.startsWith(cleanQuery) || name.startsWith(cleanQuery)
  })
  if (bestIdx !== -1) return bestIdx

  // 3. Contains all terms
  bestIdx = list.findIndex(i => {
    const code = (i.item_code || '').toLowerCase()
    const name = (i.item_name || '').toLowerCase()
    const barcodes = (i.barcodes || '').toLowerCase().split(',')
    return terms.every(term =>
      code.includes(term) ||
      name.includes(term) ||
      barcodes.some(b => b.includes(term))
    )
  })
  return bestIdx
}

function scrollToIndex(idx) {
  nextTick(() => {
    const container = scrollContainer.value
    if (!container) return
    const targetScrollTop = idx * itemHeight - (container.clientHeight / 2 - itemHeight / 2)
    container.scrollTop = Math.max(0, targetScrollTop)
  })
}

// Watch props.query to filter, then find and scroll to the best match
watch(() => props.query, (newQuery) => {
  const matchedIdx = findBestMatchIndex(newQuery)
  if (matchedIdx !== -1) {
    selectedIndex.value = matchedIdx
    scrollToIndex(matchedIdx)
  } else if (selectedIndex.value >= filteredItems.value.length) {
    // Filtering just shrank the list past the previously selected row
    selectedIndex.value = 0
    scrollToIndex(0)
  }
})

// Sync initially and whenever results open/change
watch(() => props.results, async (newVal) => {
  if (newVal && newVal.length > 0) {
    selectedIndex.value = 0
    await nextTick()
    updateContainerHeight()
    const matchedIdx = findBestMatchIndex(props.query)
    if (matchedIdx !== -1) {
      selectedIndex.value = matchedIdx
      scrollToIndex(matchedIdx)
    }
  }
}, { deep: true, immediate: true })

// Keep selected item in view on keyboard navigation
watch(selectedIndex, (newIdx) => {
  const container = scrollContainer.value
  if (!container) return
  const itemTop = newIdx * itemHeight
  const itemBottom = itemTop + itemHeight
  const containerTop = container.scrollTop
  const containerBottom = containerTop + containerHeight.value

  if (itemTop < containerTop) {
    container.scrollTop = itemTop
  } else if (itemBottom > containerBottom) {
    container.scrollTop = itemBottom - containerHeight.value
  }
})

const positionStyle = computed(() => {
  return {
    top: '80px',
    left: '50%',
    transform: 'translateX(-50%)',
    maxHeight: 'calc(100vh - 100px)'
  }
})

function getItemPrice(item) {
  if (props.searchType === 'Stock') {
    return item.valuation_rate || item.price || 0
  }
  if (!props.priceList) return item.price

  // 1. Try UOM-specific price list first
  const plUomRates = item.uom_price_lists?.[props.priceList]
  if (plUomRates && plUomRates[item.uom] != null) {
    return plUomRates[item.uom]
  }

  // 2. Try generic price list for the item
  if (item.price_lists && item.price_lists.length) {
    const pl = item.price_lists.find(p => p.name === props.priceList)
    if (pl) return pl.rate
  }

  return item.price
}

function formatPrice(p) {
  return typeof p === 'number' ? p.toFixed(2) : '0.00'
}

function handleQuickSearchKeydown(e) {
  if (filteredItems.value.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % filteredItems.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + filteredItems.value.length) % filteredItems.value.length
  } else if (e.key === 'Enter') {
    if (filteredItems.value[selectedIndex.value]) {
      e.preventDefault()
      e.stopPropagation()
      emit('select', filteredItems.value[selectedIndex.value])
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

// Exposed for the parent to call
defineExpose({
  handleQuickSearchKeydown,
  getSelectedIndex: () => selectedIndex.value,
  getSelectedValue: () => filteredItems.value[selectedIndex.value]
})
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
