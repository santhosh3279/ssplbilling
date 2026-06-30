<template>
  <div 
    v-if="sortedResults.length > 0" 
    class="fixed z-[150] w-[700px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl overflow-hidden"
    :style="positionStyle"
  >
    <div class="bg-[var(--color-surface)] px-4 py-3 border-b border-[var(--color-border)] flex justify-between items-center">
      <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Search</span>
      <div class="flex items-center gap-3">
        <button 
          @click.stop="handleRefresh" 
          class="p-1 rounded hover:bg-[var(--color-surface-raised)] transition-colors text-[var(--color-text-muted)] hover:text-[var(--color-primary)]"
          :class="{ 'animate-spin text-[var(--color-primary)]': syncLoading }"
          title="Refresh Items Cache"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M8 16H3v5"></path></svg>
        </button>
        <span class="text-xs text-[var(--color-text-muted)]">{{ sortedResults.length }} matches</span>
      </div>
    </div>
    
    <div ref="scrollContainer" class="max-h-[600px] overflow-y-auto scrollbar-none relative">
      <div 
        v-for="(item, idx) in sortedResults" 
        :key="item.item_code"
        class="quick-search-item px-4 py-3 cursor-pointer border-b border-[var(--color-border)]/50 last:border-0 transition-all"
        :class="selectedIndex === idx ? 'bg-[var(--color-focus)] border-l-4 border-l-[var(--color-focus)] font-bold' : 'hover:bg-[var(--color-surface-raised)]/40'"
        @click="$emit('select', item)"
      >
        <div class="flex justify-between items-center gap-4">
          <div class="min-w-0 flex-1 flex items-center gap-3">
            <div v-if="item.has_history" class="h-3 w-3 shrink-0 rounded-full animate-pulse bg-[var(--color-highlight)]" title="Previously sold to this customer"></div>
            <div class="min-w-0 flex-1">
              <div class="text-3xl font-normal truncate" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.item_name }}</div>
              <div class="text-2xl font-mono flex flex-wrap items-center gap-x-2 gap-y-0.5" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]/80'">
                <span>{{ item.item_code }}</span>
                <span v-if="item.hsn_sac" class="text-lg opacity-70">· HSN: {{ item.hsn_sac }}</span>
                <span v-if="item.suppliers && item.suppliers.length" class="text-lg opacity-70 truncate max-w-[320px]" :title="item.suppliers.map(s => typeof s === 'string' ? s : s.supplier).join(', ')">· Supp: {{ item.suppliers.map(s => typeof s === 'string' ? s : s.supplier).join(', ') }}</span>
              </div>
            </div>
          </div>
          <div class="flex flex-col items-end shrink-0">
            <div class="text-2xl font-mono font-bold" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]'">{{ formatPrice(getItemPrice(item)) }}</div>
            <div 
              class="text-sm font-bold" 
              :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : (item.stock > 20 ? 'text-[var(--color-success)]' : item.stock > 0 ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]')"
            >
              {{ item.stock }} {{ item.uom }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="bg-[var(--color-surface-raised)]/50 px-4 py-2 border-t border-[var(--color-border)] flex gap-6">
      <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[var(--color-text)]">↑↓</kbd> Navigate</span>
      <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[var(--color-text)]">Enter</kbd> Select</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useItemCache } from '../services/itemCache'

const props = defineProps({
  results: { type: Array, default: () => [] },
  query: { type: String, default: '' },
  priceList: { type: String, default: '' },
  searchType: { type: String, default: 'Sales' },
  warehouse: { type: String, default: '' },
  anchorEl: { type: Object, default: null } // Optional: to position relative to
})

const emit = defineEmits(['select', 'close', 'refresh'])

const { refreshItemCache, syncLoading } = useItemCache()

async function handleRefresh() {
  if (syncLoading.value) return
  await refreshItemCache(props.searchType, props.priceList, props.warehouse)
  emit('refresh')
}

const selectedIndex = ref(0)
const scrollContainer = ref(null)

// Prioritize exact matches first, then items with history
const sortedResults = computed(() => {
  const query = (props.query || '').trim().toLowerCase()
  
  return [...props.results].sort((a, b) => {
    // 1. Exact match priority (highest)
    if (query) {
      const isExactA = (a.item_code || '').toLowerCase() === query || (a.barcodes || '').toLowerCase().split(',').includes(query)
      const isExactB = (b.item_code || '').toLowerCase() === query || (b.barcodes || '').toLowerCase().split(',').includes(query)
      
      if (isExactA && !isExactB) return -1
      if (!isExactA && isExactB) return 1
    }

    // 2. History priority (if exact match status is same)
    if (a.has_history && !b.has_history) return -1
    if (!a.has_history && b.has_history) return 1
    
    return 0
  })
})

// Reset selection when results change
watch(() => props.results, () => {
  selectedIndex.value = 0
}, { deep: true })

// Keep selected item in view
watch(selectedIndex, async (newIdx) => {
  await nextTick()
  const container = scrollContainer.value
  const items = container?.querySelectorAll('.quick-search-item')
  const el = items?.[newIdx]
  if (el) {
    el.scrollIntoView({ block: 'nearest' })
  }
})

const positionStyle = computed(() => {
  if (props.anchorEl) {
    const rect = props.anchorEl.getBoundingClientRect()
    // Position to the right of the input, or slightly overlapping
    return {
      top: `${rect.top}px`,
      left: `${rect.right + 10}px`,
      maxHeight: `calc(100vh - ${rect.top + 20}px)`
    }
  }
  return {
    top: '20%',
    right: '24px'
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
  if (sortedResults.value.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % sortedResults.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + sortedResults.value.length) % sortedResults.value.length
  } else if (e.key === 'Enter') {
    // We only handle Enter here if the user intended to pick from the list
    // In SalesEntry, the barcode field also handles Enter. 
    // We might need to coordinate this.
    if (sortedResults.value[selectedIndex.value]) {
      e.preventDefault()
      e.stopPropagation()
      emit('select', sortedResults.value[selectedIndex.value])
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
  getSelectedValue: () => sortedResults.value[selectedIndex.value]
})
</script>
