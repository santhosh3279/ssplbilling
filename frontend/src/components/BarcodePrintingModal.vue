<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm"
    @keydown.esc="$emit('close')"
  >
    <div class="flex h-[80vh] w-[60vw] flex-col rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="border-b border-slate-700 px-6 py-4 flex items-center justify-between bg-slate-800">
        <div>
          <div class="text-xl font-bold text-slate-100">Barcode Printing</div>
          <div class="text-xs text-slate-400">Select item and specify quantity to print</div>
        </div>
        <button @click="$emit('close')" class="text-2xl text-slate-500 hover:text-slate-300">✕</button>
      </div>

      <div class="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
        <!-- Item Search -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase text-slate-500">Search Item</label>
          <div class="relative">
            <input
              ref="itemInput"
              v-model="query"
              class="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-lg text-slate-100 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="Start typing item code or name..."
              @keydown.down.prevent="moveSelection(1)"
              @keydown.up.prevent="moveSelection(-1)"
              @keydown.enter.prevent="handleEnter"
            />
            
            <!-- Search Results Dropdown -->
            <div v-if="showResults && results.length" class="absolute left-0 right-0 top-full z-10 mt-1 max-h-60 overflow-y-auto rounded-lg border border-slate-700 bg-slate-800 shadow-2xl custom-scrollbar">
              <div
                v-for="(item, idx) in results"
                :key="item.item_code"
                class="flex items-center justify-between border-b border-slate-700/50 px-4 py-2.5 cursor-pointer hover:bg-slate-700"
                :class="{ 'bg-slate-700': selectedIdx === idx }"
                @click="selectItem(item)"
              >
                <div class="flex flex-col">
                  <span class="font-mono text-sm font-bold text-blue-400">{{ item.item_code }}</span>
                  <span class="text-xs text-slate-300">{{ item.item_name }}</span>
                </div>
                <span class="text-[10px] font-bold text-slate-500 uppercase">{{ item.uom }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Item & Quantity -->
        <div v-if="selectedItem" class="rounded-xl border border-blue-900/30 bg-blue-900/10 p-4 flex items-center justify-between animate-in fade-in zoom-in duration-200">
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-blue-400 mb-1">Selected Item</span>
            <span class="text-lg font-bold text-slate-100">{{ selectedItem.item_name }}</span>
            <span class="font-mono text-xs text-slate-400">{{ selectedItem.item_code }}</span>
          </div>
          
          <div class="flex flex-col items-end gap-2">
            <label class="text-[10px] font-bold uppercase text-slate-500">Quantity to Print</label>
            <div class="flex items-center gap-3">
              <button @click="qty = Math.max(1, qty - 1)" class="h-10 w-10 rounded-lg bg-slate-800 text-xl font-bold text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-700">&minus;</button>
              <input 
                ref="qtyInput"
                type="number" 
                v-model.number="qty" 
                min="1"
                class="h-10 w-20 rounded-lg border border-slate-700 bg-slate-800 text-center text-xl font-bold text-slate-100 outline-none focus:border-blue-500"
                @keydown.enter.prevent="printBarcode"
              />
              <button @click="qty++" class="h-10 w-10 rounded-lg bg-slate-800 text-xl font-bold text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-700">&plus;</button>
            </div>
          </div>
        </div>

        <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-600 border-2 border-dashed border-slate-800 rounded-2xl">
          <span class="text-4xl mb-2">🏷️</span>
          <p class="text-sm">Search and select an item to begin</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-slate-700 bg-slate-800/50 px-6 py-4 flex items-center justify-between">
        <div class="flex gap-4">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            <kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 text-slate-300 mr-1">ESC</kbd> Close
          </span>
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            <kbd class="rounded border border-slate-600 bg-slate-700 px-1.5 py-0.5 text-slate-300 mr-1">ENTER</kbd> Print
          </span>
        </div>
        
        <button 
          @click="printBarcode"
          :disabled="!selectedItem || printing"
          class="rounded-xl bg-blue-600 px-8 py-2.5 text-sm font-bold text-white shadow-lg transition-all hover:bg-blue-700 hover:shadow-blue-900/20 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span v-if="printing" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          {{ printing ? 'Creating Document...' : 'Create & Print Barcode' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useItemCache } from '../services/itemCache.js'
import { frappePost } from '../api.js'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close'])

const { items: allItems } = useItemCache()

const query = ref('')
const selectedIdx = ref(0)
const selectedItem = ref(null)
const qty = ref(1)
const printing = ref(false)
const showResults = ref(false)

const itemInput = ref(null)
const qtyInput = ref(null)

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return allItems.value.filter(i => 
    (i.item_code || '').toLowerCase().includes(q) ||
    (i.item_name || '').toLowerCase().includes(q)
  ).slice(0, 10)
})

watch(query, (newVal) => {
  showResults.value = newVal.length > 0
  selectedIdx.value = 0
})

function moveSelection(dir) {
  if (!results.value.length) return
  selectedIdx.value = (selectedIdx.value + dir + results.value.length) % results.value.length
}

function handleEnter() {
  if (showResults.value && results.value[selectedIdx.value]) {
    selectItem(results.value[selectedIdx.value])
  } else if (selectedItem.value) {
    printBarcode()
  }
}

function selectItem(item) {
  selectedItem.value = item
  query.value = item.item_name
  showResults.value = false
  nextTick(() => {
    qtyInput.value?.focus()
    qtyInput.value?.select()
  })
}

async function printBarcode() {
  if (!selectedItem.value || printing.value) return
  
  printing.value = true
  try {
    const docName = await frappePost('ssplbilling.api.item_api.print_barcodes', {
      items: [{ item_code: selectedItem.value.item_code, qty: qty.value }]
    })
    
    // Open print view in new tab
    const url = `/printview?doctype=Barcode_Prinitng&name=${docName}&format=Standard`
    window.open(url, '_blank')
    
    // Reset for next print
    selectedItem.value = null
    query.value = ''
    qty.value = 1
    nextTick(() => itemInput.value?.focus())
  } catch (e) {
    alert('Failed to create barcode document: ' + (e.message || 'Unknown error'))
  } finally {
    printing.value = false
  }
}

onMounted(() => {
  if (props.show) {
    nextTick(() => itemInput.value?.focus())
  }
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    query.value = ''
    selectedItem.value = null
    qty.value = 1
    nextTick(() => itemInput.value?.focus())
  }
})
</script>
