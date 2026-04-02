<template>
  <div 
    v-if="results.length > 0" 
    class="fixed z-[150] w-96 rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden"
    :style="positionStyle"
  >
    <div class="bg-slate-800 px-3 py-2 border-b border-slate-700 flex justify-between items-center">
      <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Quick Search</span>
      <span class="text-[10px] text-slate-600">{{ results.length }} matches</span>
    </div>
    
    <div class="max-h-[400px] overflow-y-auto scrollbar-none">
      <div 
        v-for="(item, idx) in results" 
        :key="item.item_code"
        class="px-3 py-2 cursor-pointer border-b border-slate-800/50 last:border-0"
        :class="selectedIndex === idx ? 'bg-blue-600/20 ring-1 ring-inset ring-blue-500/50' : 'hover:bg-slate-800/40'"
        @click="$emit('select', item)"
      >
        <div class="flex justify-between items-start gap-2">
          <div class="min-w-0 flex-1">
            <div class="text-sm font-bold text-slate-200 truncate">{{ item.item_name }}</div>
            <div class="text-[10px] font-mono text-slate-500">{{ item.item_code }}</div>
          </div>
          <div class="flex flex-col items-end shrink-0">
            <div class="text-xs font-mono text-amber-400">{{ formatPrice(item.price) }}</div>
            <div 
              class="text-[10px] font-bold" 
              :class="item.stock > 20 ? 'text-green-500' : item.stock > 0 ? 'text-amber-500' : 'text-red-500'"
            >
              {{ item.stock }} {{ item.uom }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="bg-slate-800/50 px-3 py-1.5 border-t border-slate-700 flex gap-3">
      <span class="text-[9px] text-slate-500"><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-400">↑↓</kbd> Navigate</span>
      <span class="text-[9px] text-slate-500"><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-400">Enter</kbd> Select</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  results: { type: Array, default: () => [] },
  query: { type: String, default: '' },
  anchorEl: { type: Object, default: null } // Optional: to position relative to
})

const emit = defineEmits(['select', 'close'])

const selectedIndex = ref(0)

// Reset selection when results change
watch(() => props.results, () => {
  selectedIndex.value = 0
}, { deep: true })

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

function formatPrice(p) {
  return typeof p === 'number' ? p.toFixed(2) : '0.00'
}

function handleQuickSearchKeydown(e) {
  if (props.results.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % props.results.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + props.results.length) % props.results.length
  } else if (e.key === 'Enter') {
    // We only handle Enter here if the user intended to pick from the list
    // In SalesEntry, the barcode field also handles Enter. 
    // We might need to coordinate this.
    if (props.results[selectedIndex.value]) {
      e.preventDefault()
      e.stopPropagation()
      emit('select', props.results[selectedIndex.value])
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
  getSelectedValue: () => props.results[selectedIndex.value]
})
</script>
