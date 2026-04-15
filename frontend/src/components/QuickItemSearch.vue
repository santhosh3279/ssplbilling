<template>
  <div 
    v-if="sortedResults.length > 0" 
    class="fixed z-[150] w-[700px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl overflow-hidden"
    :style="positionStyle"
  >
    <div class="bg-[var(--color-surface)] px-4 py-3 border-b border-[var(--color-border)] flex justify-between items-center">
      <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Search</span>
      <span class="text-xs text-[var(--color-text-muted)]">{{ sortedResults.length }} matches</span>
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
              <div class="text-2xl font-mono" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]/80'">{{ item.item_code }}</div>
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

const props = defineProps({
  results: { type: Array, default: () => [] },
  query: { type: String, default: '' },
  priceList: { type: String, default: '' },
  anchorEl: { type: Object, default: null } // Optional: to position relative to
})

const emit = defineEmits(['select', 'close'])

const selectedIndex = ref(0)
const scrollContainer = ref(null)

// Prioritize items with history, then exact matches
const sortedResults = computed(() => {
  const query = (props.query || '').trim().toLowerCase()
  
  return [...props.results].sort((a, b) => {
    // 1. History priority
    if (a.has_history && !b.has_history) return -1
    if (!a.has_history && b.has_history) return 1
    
    // 2. Exact match priority (if history status is same)
    if (query) {
      const isExactA = (a.item_code || '').toLowerCase() === query || (a.barcodes || '').toLowerCase().split(',').includes(query)
      const isExactB = (b.item_code || '').toLowerCase() === query || (b.barcodes || '').toLowerCase().split(',').includes(query)
      
      if (isExactA && !isExactB) return -1
      if (!isExactA && isExactB) return 1
    }
    
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
