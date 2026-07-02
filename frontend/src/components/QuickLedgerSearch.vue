<template>
  <div 
    v-if="sortedResults.length > 0" 
    class="fixed z-[150] w-[700px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
    :style="positionStyle"
  >
    <div class="bg-[var(--color-surface)] px-4 py-3 border-b border-[var(--color-border)] flex justify-between items-center">
      <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Quick Ledger Search</span>
      <div class="flex items-center gap-3">
        <button 
          @click.stop="handleRefresh" 
          class="p-1 rounded hover:bg-[var(--color-surface-raised)] transition-colors text-[var(--color-text-muted)] hover:text-[var(--color-primary)]"
          :class="{ 'animate-spin text-[var(--color-primary)]': syncLoading }"
          title="Refresh Ledgers Cache"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M8 16H3v5"></path></svg>
        </button>
        <span class="text-xs text-[var(--color-text-muted)]">{{ sortedResults.length }} matches</span>
      </div>
    </div>
    
    <div ref="scrollContainer" class="max-h-[600px] overflow-y-auto scrollbar-none relative">
      <div 
        v-for="(ledger, idx) in sortedResults" 
        :key="ledger.name"
        class="quick-search-ledger px-6 py-4 cursor-pointer border-b border-[var(--color-border)]/50 last:border-0 transition-all"
        :class="selectedIndex === idx ? 'bg-[var(--color-focus)] border-l-4 border-l-[var(--color-focus)] font-bold' : 'hover:bg-[var(--color-surface-raised)]/40'"
        @click="$emit('select', ledger)"
      >
        <div class="flex items-center gap-6">
          <!-- Column 1: Ledger Info -->
          <div class="min-w-0 flex-1">
            <div class="text-3xl font-normal truncate mb-1" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">
              {{ ledger.label }}
            </div>
            <div class="flex items-center gap-2 text-xl font-mono opacity-60" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
              <span 
                class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest shrink-0"
                :class="getTypeClass(ledger.type)"
              >
                {{ ledger.type }}
              </span>
              <span class="truncate">{{ ledger.name }}</span>
              <span v-if="ledger.group" class="truncate">· {{ ledger.group }}</span>
            </div>
          </div>
          
          <!-- Column 2: Contact Info (Middle) -->
          <div class="w-48 shrink-0 flex flex-col justify-center">
            <div v-if="ledger.mobile_no" class="text-2xl font-mono" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)] font-bold' : 'text-[var(--color-text-muted)]'">
              {{ ledger.mobile_no }}
            </div>
            <div v-else class="text-xs italic opacity-20" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : ''">No Mobile</div>
          </div>

          <!-- Column 3: Financial Info (Right) -->
          <div class="w-64 shrink-0 flex flex-col items-end justify-center">
            <div 
              class="text-3xl font-mono font-black" 
              :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : (ledger.balance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]')"
            >
              {{ isPoints ? fmtPts(ledger.balance) : fmtBalance(ledger.balance) }}
            </div>
            <div class="text-[10px] font-bold uppercase tracking-widest opacity-40" :class="selectedIndex === idx ? '!text-[var(--color-text-on-focus)]' : ''">
              {{ balanceLabel }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="bg-[var(--color-surface-raised)] px-4 py-2 border-t border-[var(--color-border)] flex gap-6">
      <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[var(--color-text)]">↑↓</kbd> Navigate</span>
      <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[var(--color-text)]">Enter</kbd> Select</span>
      <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Close</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useLedgerCache } from '../services/ledgerCache'

const props = defineProps({
  results: { type: Array, default: () => [] },
  query: { type: String, default: '' },
  anchorEl: { type: Object, default: null },
  balanceLabel: { type: String, default: 'Closing Balance' },
  isPoints: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'close', 'refresh'])

const { refreshLedgerCache, syncLoading } = useLedgerCache()

async function handleRefresh() {
  if (syncLoading.value) return
  await refreshLedgerCache(true)
  emit('refresh')
}

const selectedIndex = ref(0)
const scrollContainer = ref(null)

const sortedResults = computed(() => {
  const q = (props.query || '').trim().toLowerCase()
  if (!q) return props.results

  return [...props.results].sort((a, b) => {
    // Exact ID match priority
    const exactA = (a.name || '').toLowerCase() === q
    const exactB = (b.name || '').toLowerCase() === q
    if (exactA && !exactB) return -1
    if (!exactA && exactB) return 1

    // Exact label match priority
    const labelA = (a.label || '').toLowerCase() === q
    const labelB = (b.label || '').toLowerCase() === q
    if (labelA && !labelB) return -1
    if (!labelA && labelB) return 1

    return 0
  })
})

watch(() => props.results, () => {
  selectedIndex.value = 0
}, { deep: true })

watch(selectedIndex, async (newIdx) => {
  await nextTick()
  const container = scrollContainer.value
  const items = container?.querySelectorAll('.quick-search-ledger')
  const el = items?.[newIdx]
  if (el) {
    el.scrollIntoView({ block: 'nearest' })
  }
})

const positionStyle = computed(() => {
  if (props.anchorEl) {
    const rect = props.anchorEl.getBoundingClientRect()
    return {
      top: `${rect.bottom + 8}px`,
      left: `${rect.left}px`,
      maxHeight: `calc(100vh - ${rect.bottom + 40}px)`
    }
  }
  return {
    top: '20%',
    left: '50%',
    transform: 'translateX(-50%)'
  }
})

function getTypeClass(type) {
  switch (type) {
    case 'Customer': return 'bg-[var(--color-customer)]/20 text-[var(--color-customer)]'
    case 'Supplier': return 'bg-[#78350f]/20 text-[#78350f]'
    case 'Employee': return 'bg-black text-white'
    case 'Account': return 'bg-[var(--color-text-muted)]/20 text-[var(--color-text-muted)]'
    default: return 'bg-gray-500/10 text-gray-500'
  }
}

function fmtBalance(val) {
  const b = parseFloat(val) || 0
  const abs = Math.abs(b).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  const suffix = b > 0 ? 'Dr' : b < 0 ? 'Cr' : ''
  return `₹ ${abs} ${suffix}`
}

function fmtPts(val) {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' pts'
}

function handleKeydown(e) {
  if (sortedResults.value.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % sortedResults.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + sortedResults.value.length) % sortedResults.value.length
  } else if (e.key === 'Enter') {
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

defineExpose({
  handleKeydown,
  getSelectedIndex: () => selectedIndex.value,
  getSelectedValue: () => sortedResults.value[selectedIndex.value]
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
