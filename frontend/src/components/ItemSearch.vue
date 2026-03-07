<template>
  <div class="relative w-full">
    <input
      ref="inputRef"
      v-model="query"
      class="w-full rounded border border-gray-300 bg-white px-2 py-1 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100"
      :style="{ fontSize: fontSize }"
      placeholder="Item code"
      @keydown.enter.prevent="handleEnter"
      @keydown.tab="handleTab"
      @keydown.up.prevent="handleUp"
      @keydown.down.prevent="handleDown"
      @input="handleInput"
    />

    <!-- ITEM SEARCH POPUP -->
    <div v-if="showSearch" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="closeSearch">
      <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden">
        <div class="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-gray-50/50">
          <div class="text-2xl font-semibold text-gray-700">Search Item</div>
          <button 
            @click="refreshLocalItems" 
            :disabled="isSyncing"
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 hover:bg-blue-100 disabled:opacity-50"
          >
            <span v-if="isSyncing" class="animate-spin">⏳</span>
            <span v-else>🔄</span>
            {{ isSyncing ? 'Syncing...' : 'Refresh Items' }} <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
        </div>
        <div class="border-b border-gray-200 px-4 py-3">
          <input
            ref="searchInput"
            v-model="searchQuery"
            class="w-full rounded border border-gray-300 bg-white px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Type item code or name..."
            @keydown.esc="closeSearch"
            @keydown.down.prevent="moveSearchCursor(1)"
            @keydown.up.prevent="moveSearchCursor(-1)"
            @keydown.enter.prevent="pickSearchItem"
          />
       </div>
        <div class="flex-1 overflow-y-auto" ref="resultsWrapRef">
          <table v-if="searchResults.length" class="w-full text-2xl">
            <thead>
              <tr class="bg-gray-50">
                <th class="px-4 py-3 text-left text-lg font-bold uppercase text-gray-600">Code</th>
                <th class="px-3 py-3 text-left text-lg font-bold uppercase text-gray-600">Item Name</th>
                <th class="px-3 py-3 text-left text-lg font-bold uppercase text-gray-600">UOM</th>
                <th class="px-3 py-3 text-right text-lg font-bold uppercase text-gray-600">Rate</th>
                <th class="px-3 py-3 text-right text-lg font-bold uppercase text-gray-600">Stock</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(item, idx) in searchResults" 
                :key="item.item_code" 
                class="cursor-pointer border-b border-gray-100" 
                :class="{ 'bg-blue-100': searchIdx === idx }" 
                :ref="el => setSearchRowRef(el, idx)"
                @click="pickSearchItemByIdx(idx)" 
                @mouseenter="searchIdx = idx"
              >
                <td class="px-4 py-3 font-mono text-2xl">{{ item.item_code }}</td>
                <td class="px-3 py-3">{{ item.item_name }}</td>
                <td class="px-3 py-3 text-gray-600">{{ item.uom }}</td>
                <td class="px-3 py-3 text-right font-mono">{{ (item.rate || 0).toFixed(2) }}</td>
                <td class="px-3 py-3 text-right">
                  <span class="rounded-full px-3 py-1 text-xl font-bold" :class="item.stock_qty > 20 ? 'bg-green-50 text-green-600' : item.stock_qty > 0 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'">
                    {{ item.stock_qty }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="px-4 py-8 text-center text-2xl text-gray-600">No items found</div>
        </div>
        <div class="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-lg text-gray-600">
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Up/Down</kbd> Navigate <kbd class="ml-2 rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Enter</kbd> Select</span>
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Esc</kbd> Close</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { frappeGet } from '../api.js'
import { localDb } from '../services/localDb'

const props = defineProps({
  initialQuery: { type: String, default: '' },
  fontSize: { type: String, default: '14px' },
  priceList: { type: String, default: 'Standard Selling' },
  warehouse: { type: String, default: '' },
  disabled: Boolean,
})

const emit = defineEmits(['select-item', 'focus-next', 'focus-prev', 'update-pending'])

const query = ref(props.initialQuery)
watch(() => props.initialQuery, (newVal) => {
  query.value = newVal
})
const inputRef = ref(null)

// Search Modal State
const showSearch = ref(false)
const searchQuery = ref('')
const searchIdx = ref(0)
const allItems = ref([])
const searchResults = ref([])
const isSyncing = ref(false)
const searchInput = ref(null)
const resultsWrapRef = ref(null)
const searchRowRefs = new Map()

function setSearchRowRef(el, idx) { 
  if (el) searchRowRefs.set(idx, el)
  else searchRowRefs.delete(idx) 
}

const itemLookup = createResource({ 
  url: '/api/method/ssplbilling.api.sales_api.get_item_details' 
})

async function lookupItem(code) {
  try {
    await itemLookup.submit({ 
      item_code: code, 
      price_list: props.priceList, 
      warehouse: props.warehouse 
    })
    const d = itemLookup.data?.message || itemLookup.data
    return d?.found ? d : null
  } catch (e) { return null }
}

let lookupTimeout = null
function handleInput() {
  clearTimeout(lookupTimeout)
  const code = query.value.trim()
  if (code.length < 2) {
    emit('update-pending', { item_code: '', item_name: '', uom: '', rate: null })
    return
  }
  lookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    if (r) {
      emit('update-pending', { item_code: r.item_code, item_name: r.item_name, uom: r.uom, rate: r.rate })
    } else {
      emit('update-pending', { item_code: code, item_name: '', uom: '', rate: null })
    }
  }, 300)
}

let emptyCodeEnters = 0
async function handleEnter() {
  const code = query.value.trim()
  if (!code) {
    emptyCodeEnters++
    if (emptyCodeEnters >= 2) {
      emptyCodeEnters = 0
      openSearch('')
    }
    return
  }
  emptyCodeEnters = 0
  const r = await lookupItem(code)
  if (r) {
    emit('select-item', r)
    // Clear query after selection if it was a final selection?
    // In SalesEntry, the query is cleared AFTER addItemToTable is called.
    // We'll let the parent handle clearing if needed or clear it here.
    query.value = ''
  } else {
    openSearch(code)
  }
}

function handleTab(e) {
  if (query.value.trim()) {
    // If there's a code, we might want to prevent tab if not found?
    // But SalesEntry currently allows it to move to Qty.
    emit('focus-next')
    e.preventDefault()
  }
}

function handleUp() {
  emit('focus-prev')
}

function handleDown() {
  // Not used in new entry row specifically but kept for consistency
}

// Search Modal Logic
async function refreshLocalItems() {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await fetchAllItems(true)
  } catch (e) {
    console.error('Manual sync failed:', e)
  } finally {
    isSyncing.value = false
  }
}

async function fetchAllItems(force = false) {
  try {
    let itemsFromDb = force ? [] : await localDb.getAllItems()
    
    if (!itemsFromDb || itemsFromDb.length === 0) {
      itemsFromDb = await frappeGet('frappe.client.get_list', {
        doctype: 'Item',
        fields: ['item_code', 'item_name', 'stock_uom as uom', 'standard_rate as rate'],
        filters: { disabled: 0, is_sales_item: 1 },
        limit_page_length: 5000,
        order_by: 'item_name asc'
      })
      if (itemsFromDb && itemsFromDb.length) {
        await localDb.clearStore('items')
        await localDb.saveItems(itemsFromDb)
      }
    }

    const binsRes = await frappeGet('frappe.client.get_list', {
      doctype: 'Bin',
      fields: ['item_code', 'actual_qty as stock_qty'],
      limit_page_length: 10000
    })
    
    const stockMap = {}
    binsRes.forEach(b => {
      stockMap[b.item_code] = (stockMap[b.item_code] || 0) + b.stock_qty
    })

    allItems.value = (itemsFromDb || []).map(i => ({
      ...i,
      stock_qty: stockMap[i.item_code] || 0
    }))
    filterItems()
  } catch (e) {
    console.error('Failed to fetch items:', e)
  }
}

function filterItems() {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) {
    searchResults.value = allItems.value.slice(0, 100)
    return
  }
  searchResults.value = allItems.value.filter(i => 
    i.item_code.toLowerCase().includes(q) || 
    i.item_name.toLowerCase().includes(q)
  ).slice(0, 100)
  searchIdx.value = 0
}

watch(searchQuery, filterItems)

function openSearch(prefill) { 
  searchQuery.value = prefill || ''
  searchIdx.value = 0
  showSearch.value = true
  if (allItems.value.length === 0) fetchAllItems()
  else filterItems()
  nextTick(() => searchInput.value?.focus()) 
}

function closeSearch() { 
  showSearch.value = false
  searchQuery.value = ''
  nextTick(() => inputRef.value?.focus())
}

function moveSearchCursor(dir) {
  if (!searchResults.value.length) return
  searchIdx.value = Math.max(0, Math.min(searchResults.value.length - 1, searchIdx.value + dir))
  nextTick(() => {
    const el = searchRowRefs.get(searchIdx.value)
    if (el) el.scrollIntoView({ block: 'nearest' })
  })
}

function pickSearchItem() { 
  if (searchResults.value.length) pickSearchItemByIdx(searchIdx.value) 
}

async function pickSearchItemByIdx(idx) {
  const p = searchResults.value[idx]
  if (!p) return
  
  // Fetch real-time rate for the selected price list
  let itemData = await lookupItem(p.item_code)
  if (!itemData) {
    // Fallback to what we have in search results
    itemData = { ...p, found: true }
  }

  query.value = itemData.item_code
  showSearch.value = false
  emit('select-item', itemData)
  query.value = '' // Clear after selection
}

defineExpose({
  focus: () => inputRef.value?.focus(),
  openSearch
})

onMounted(() => {
  fetchAllItems()
})
</script>
