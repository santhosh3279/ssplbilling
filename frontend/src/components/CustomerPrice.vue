<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-[2px]">
    <div class="w-[400px] overflow-hidden rounded-2xl bg-[var(--color-bg)] border border-[var(--color-highlight)]/40 shadow-2xl">
      <div class="bg-[var(--color-highlight)]/20 px-6 py-4 flex items-center gap-3 border-b border-[var(--color-highlight)]/30">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-highlight)]/40 text-xl text-[var(--color-highlight)]">💰</div>
        <div>
          <div class="text-lg font-bold text-[var(--color-text)]">Update Item Price?</div>
          <div class="text-[10px] text-[var(--color-highlight)] uppercase tracking-wider font-bold">Price Change Detected</div>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <div class="flex flex-col gap-1">
          <div class="text-sm font-bold text-[var(--color-text)]">{{ data.item_name || data.item_code }}</div>
          <div class="text-xs text-[var(--color-text-muted)]">Item Code: {{ data.item_code }}</div>
        </div>

        <div class="grid grid-cols-2 gap-4 rounded-xl bg-[var(--color-surface-raised)]/50 p-4 border border-[var(--color-border)]/50">
          <div class="flex flex-col">
            <span class="text-[10px] text-[var(--color-text-muted)] uppercase font-bold">New Rate</span>
            <span class="text-xl font-mono text-[var(--color-text)]">{{ (data.rate || 0).toFixed(2) }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] text-[var(--color-text-muted)] uppercase font-bold">Factor</span>
            <span class="text-xl font-mono text-[var(--color-highlight)]">{{ (data.multiplication_factor || 1).toFixed(4) }}</span>
          </div>
        </div>

        <div class="text-xs text-[var(--color-text-muted)] leading-relaxed">
          Choose how you want to save this price change. You can save it as a special discount for <span class="text-[var(--color-text)] font-medium">{{ customer }}</span>.
        </div>
      </div>

      <div class="flex flex-col gap-2 p-6 pt-0">
        <button 
          ref="savePriceYesBtn" 
          @click="$emit('saveCustomer')" 
          @keydown="onKeydown" 
          class="w-full rounded-xl bg-[var(--color-highlight)] px-4 py-2.5 text-sm font-bold text-[var(--color-text-on-highlight)] hover:opacity-90 shadow-lg transition-all outline-none focus:ring-2 focus:ring-[var(--color-highlight)]"
        >
          Save for Customer
        </button>
        <button 
          ref="savePriceNoBtn" 
          @click="$emit('dismiss')" 
          @keydown="onKeydown" 
          class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-all outline-none focus:ring-2 focus:ring-[var(--color-border)]"
        >
          Dismiss
        </button>
        <div class="mt-2 text-center">
          <span class="text-[9px] text-[var(--color-text-muted)] uppercase font-bold tracking-widest">
            Press <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 font-mono text-[var(--color-text-muted)]">F4</kbd> for Advanced Update
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useSubwindow } from '../services/shortcutManager'

const props = defineProps({
  data: { type: Object, required: true },
  customer: { type: String, default: '' },
  priceList: { type: String, default: '' }
})

const emit = defineEmits(['saveCustomer', 'updatePricelist', 'dismiss', 'advanced'])

useSubwindow()

const savePriceYesBtn = ref(null)
const savePriceNoBtn = ref(null)

onMounted(() => {
  nextTick(() => {
    savePriceNoBtn.value?.focus()
  })
})

function onKeydown(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    // Do nothing as requested: disable the esc button
    return
  }

  if (e.key === 'F4') {
    e.preventDefault()
    emit('advanced')
    return
  }

  const btns = [savePriceYesBtn.value, savePriceNoBtn.value].filter(Boolean)
  const currIdx = btns.indexOf(document.activeElement)
  
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    const nextIdx = (currIdx - 1 + btns.length) % btns.length
    btns[nextIdx]?.focus()
  } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault()
    const nextIdx = (currIdx + 1) % btns.length
    btns[nextIdx]?.focus()
  }
}
</script>
