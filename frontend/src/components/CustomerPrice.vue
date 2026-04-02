<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-[2px]">
    <div class="w-[400px] overflow-hidden rounded-2xl bg-slate-900 border border-purple-500/40 shadow-2xl">
      <div class="bg-purple-900/20 px-6 py-4 flex items-center gap-3 border-b border-purple-500/30">
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-purple-900/40 text-xl text-purple-400">💰</div>
        <div>
          <div class="text-lg font-bold text-slate-100">Update Item Price?</div>
          <div class="text-[10px] text-purple-400 uppercase tracking-wider font-bold">Price Change Detected</div>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <div class="flex flex-col gap-1">
          <div class="text-sm font-bold text-slate-200">{{ data.item_name || data.item_code }}</div>
          <div class="text-xs text-slate-500">Item Code: {{ data.item_code }}</div>
        </div>

        <div class="grid grid-cols-2 gap-4 rounded-xl bg-slate-800/50 p-4 border border-slate-700/50">
          <div class="flex flex-col">
            <span class="text-[10px] text-slate-500 uppercase font-bold">New Rate</span>
            <span class="text-xl font-mono text-slate-100">{{ (data.rate || 0).toFixed(2) }}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] text-slate-500 uppercase font-bold">Discount %</span>
            <span class="text-xl font-mono text-purple-400">{{ (data.discount_percentage || 0).toFixed(2) }}%</span>
          </div>
        </div>

        <div class="text-xs text-slate-400 leading-relaxed">
          Choose how you want to save this price change. You can save it as a special discount for <span class="text-slate-200 font-medium">{{ customer }}</span>, or update the main <span class="text-slate-200 font-medium">{{ priceList }}</span> price list.
        </div>
      </div>

      <div class="flex flex-col gap-2 p-6 pt-0">
        <div class="flex gap-2">
          <button 
            ref="savePriceYesBtn" 
            @click="$emit('saveCustomer')" 
            @keydown="onKeydown" 
            class="flex-1 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-purple-700 shadow-lg shadow-purple-900/20 transition-all outline-none focus:ring-2 focus:ring-purple-500"
          >
            Save for Customer
          </button>
          <button 
            ref="updatePricelistBtn" 
            @click="$emit('updatePricelist')" 
            @keydown="onKeydown" 
            class="flex-1 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-blue-700 shadow-lg shadow-blue-900/20 transition-all outline-none focus:ring-2 focus:ring-blue-500"
          >
            Update Price List
          </button>
        </div>
        <button 
          ref="savePriceNoBtn" 
          @click="$emit('dismiss')" 
          @keydown="onKeydown" 
          class="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-bold text-slate-300 hover:bg-slate-700 transition-all outline-none focus:ring-2 focus:ring-slate-500"
        >
          Dismiss
        </button>
        <div class="mt-2 text-center">
          <span class="text-[9px] text-slate-500 uppercase font-bold tracking-widest">
            Press <kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 font-mono text-slate-400">F4</kbd> for Advanced Update
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const props = defineProps({
  data: { type: Object, required: true },
  customer: { type: String, default: '' },
  priceList: { type: String, default: '' }
})

const emit = defineEmits(['saveCustomer', 'updatePricelist', 'dismiss', 'advanced'])

const savePriceYesBtn = ref(null)
const updatePricelistBtn = ref(null)
const savePriceNoBtn = ref(null)

onMounted(() => {
  nextTick(() => {
    savePriceNoBtn.value?.focus()
  })
})

function onKeydown(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    emit('dismiss')
    return
  }

  if (e.key === 'F4') {
    e.preventDefault()
    emit('advanced')
    return
  }

  const btns = [savePriceYesBtn.value, updatePricelistBtn.value, savePriceNoBtn.value].filter(Boolean)
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
