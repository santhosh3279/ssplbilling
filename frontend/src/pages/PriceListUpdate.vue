<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[110] flex items-center justify-center bg-black/50 p-4' : 'min-h-screen bg-gray-50 flex flex-col'">
    <div :class="isSubWindow ? 'flex h-[70vh] w-[70vw] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl' : 'flex flex-1 flex-col'">
      <!-- Header -->
      <header class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div class="flex items-center gap-4">
          <button 
            v-if="isSubWindow"
            class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100" 
            @click="$emit('close')"
          >
            &larr; Back to Entry
          </button>
          <button 
            v-else
            class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100" 
            @click="router.push('/')"
          >
            &larr; Dashboard
          </button>
          <h1 class="text-xl font-bold text-gray-800">Update Item Prices</h1>
          <div v-if="itemCode" class="rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-blue-600">
            {{ itemCode }}
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-gray-400">
            <kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono">F8</kbd> Save All
            <kbd class="ml-2 rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono">Esc</kbd> Close
          </span>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="mx-auto max-w-4xl rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div v-if="loading" class="flex items-center justify-center py-20">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          </div>
          
          <div v-else-if="!itemCode && !isSubWindow" class="p-10 text-center">
            <div class="mb-4 text-gray-400">Please provide an item code to update prices.</div>
            <input 
              v-model="manualItemCode" 
              class="rounded border border-gray-300 px-4 py-2 outline-none focus:border-blue-500"
              placeholder="Enter Item Code..."
              @keydown.enter="loadPrices(manualItemCode)"
            />
          </div>

          <table v-else class="w-full text-left border-collapse">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="px-6 py-3 text-xs font-bold uppercase tracking-wider text-gray-500">Price List</th>
                <th class="px-6 py-3 text-xs font-bold uppercase tracking-wider text-gray-500">Type</th>
                <th class="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider text-gray-500">Current Rate</th>
                <th class="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider text-gray-500">New Rate</th>
                <th v-if="selectedPriceList" class="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider text-gray-500">Disc %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr 
                v-for="(p, idx) in prices" 
                :key="p.price_list" 
                class="hover:bg-gray-50 transition-colors"
                :class="{ 'bg-blue-50/50': activeRow === idx }"
                @click="activeRow = idx"
              >
                <td class="px-6 py-4">
                  <div class="font-semibold text-gray-800">{{ p.price_list }}</div>
                  <div v-if="p.price_list === selectedPriceList" class="text-[10px] font-bold text-blue-500 uppercase">Selected in entry</div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex gap-2">
                    <span v-if="p.buying" class="rounded bg-green-50 px-1.5 py-0.5 text-[10px] font-bold text-green-600">BUYING</span>
                    <span v-if="p.selling" class="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-bold text-blue-600">SELLING</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right font-mono text-gray-500">
                  &#8377;{{ p.original_rate.toFixed(2) }}
                </td>
                <td class="px-6 py-4 text-right">
                  <input 
                    :ref="el => inputRefs[`rate-${idx}`] = el"
                    type="number" 
                    v-model.number="p.rate" 
                    step="0.01"
                    class="w-32 rounded border border-gray-300 px-3 py-1.5 text-right font-mono font-bold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    @keydown.enter.prevent="onRateEnter(idx)"
                    @keydown.up.prevent="moveVertical(idx, -1)"
                    @keydown.down.prevent="moveVertical(idx, 1)"
                  />
                </td>
                <td v-if="selectedPriceList" class="px-6 py-4 text-right">
                  <input 
                    v-if="p.price_list === selectedPriceList"
                    :ref="el => inputRefs[`disc-${idx}`] = el"
                    type="number" 
                    v-model.number="discount" 
                    step="0.5"
                    min="0"
                    max="100"
                    class="w-20 rounded border border-blue-300 bg-blue-50 px-3 py-1.5 text-right font-mono font-bold text-blue-700 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    @keydown.enter.prevent="onDiscEnter(idx)"
                    @keydown.up.prevent="moveVertical(idx, -1)"
                    @keydown.down.prevent="moveVertical(idx, 1)"
                  />
                  <span v-else class="text-gray-300">--</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <!-- Footer -->
      <footer class="border-t border-gray-200 bg-gray-50 px-6 py-4">
        <div class="mx-auto max-w-4xl flex items-center justify-between">
          <div class="text-sm text-gray-500">
            Total Price Lists: <span class="font-bold">{{ prices.length }}</span>
          </div>
          <div class="flex gap-3">
            <button 
              class="rounded-lg border border-gray-300 bg-white px-6 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              @click="isSubWindow ? $emit('close') : router.push('/')"
            >
              Cancel
            </button>
            <button 
              class="rounded-lg bg-blue-600 px-8 py-2 text-sm font-bold text-white shadow-lg transition-all hover:bg-blue-700 active:scale-95"
              @click="saveAll"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Save All Changes (F8)' }}
            </button>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  isSubWindow: { type: Boolean, default: false },
  itemCode: { type: String, default: '' },
  selectedPriceList: { type: String, default: '' },
  initialDiscount: { type: Number, default: 0 }
})

const emit = defineEmits(['close', 'saved'])

const router = useRouter()
const route = useRoute()

const prices = ref([])
const discount = ref(props.initialDiscount)
const loading = ref(false)
const saving = ref(false)
const manualItemCode = ref('')
const activeRow = ref(0)
const inputRefs = ref({})

watch(() => props.initialDiscount, (val) => {
  discount.value = val
})

async function loadPrices(code) {
  if (!code) return
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.pricelist_api.get_item_prices', { item_code: code })
    prices.value = data.map(p => ({
      ...p,
      original_rate: p.rate,
      rate: p.rate // user editable
    }))
    
    // Set active row to selected price list if exists
    if (props.selectedPriceList) {
      const idx = prices.value.findIndex(p => p.price_list === props.selectedPriceList)
      if (idx !== -1) activeRow.value = idx
    }

    nextTick(() => {
      focusInput(`rate-${activeRow.value}`)
    })
  } catch (e) {
    alert('Failed to load prices: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function saveAll() {
  const code = props.itemCode || manualItemCode.value
  if (!code) return
  
  // Only update prices that have changed
  const changedPrices = prices.value.filter(p => p.rate !== p.original_rate)
  const discountChanged = discount.value !== props.initialDiscount

  if (!changedPrices.length && !discountChanged) {
    if (props.isSubWindow) emit('close')
    return
  }

  saving.value = true
  try {
    if (changedPrices.length) {
      await frappePost('ssplbilling.api.pricelist_api.update_multiple_prices', {
        item_code: code,
        prices: JSON.stringify(changedPrices)
      })
    }
    
    // Emit back all relevant data
    emit('saved', {
      changedPrices,
      discount: discount.value,
      discountChanged
    })
    
    if (props.isSubWindow) emit('close')
    else alert('Prices updated successfully')
  } catch (e) {
    alert('Update failed: ' + e.message)
  } finally {
    saving.value = false
  }
}

function onRateEnter(idx) {
  activeRow.value = idx
  // Left to Right: If this row has a discount field, go to it
  if (prices.value[idx].price_list === props.selectedPriceList) {
    focusInput(`disc-${idx}`)
  } else {
    // Otherwise go to next row top to bottom
    goToNextRow(idx)
  }
}

function onDiscEnter(idx) {
  activeRow.value = idx
  // Left to Right / Top to Bottom: After discount, go to next row rate
  goToNextRow(idx)
}

function goToNextRow(idx) {
  if (idx < prices.value.length - 1) {
    activeRow.value = idx + 1
    focusInput(`rate-${idx + 1}`)
  } else {
    // Last field in the whole sequence
    saveAll()
  }
}

function moveVertical(idx, dir) {
  const next = idx + dir
  if (next >= 0 && next < prices.value.length) {
    activeRow.value = next
    // Maintain current column if possible
    const isDisc = document.activeElement?.getAttribute('ref')?.includes('disc') || false
    if (isDisc && prices.value[next].price_list === props.selectedPriceList) {
      focusInput(`disc-${next}`)
    } else {
      focusInput(`rate-${next}`)
    }
  }
}

function focusInput(key) {
  nextTick(() => {
    const el = inputRefs.value[key]
    if (el) {
      el.focus()
      el.select()
    }
  })
}

const handleGlobalKeydown = (e) => {
  if (e.key === 'F8') {
    e.preventDefault()
    saveAll()
  } else if (e.key === 'Escape') {
    if (props.isSubWindow) emit('close')
    else router.push('/')
  }
}

onMounted(() => {
  const code = props.itemCode || route.query.item_code
  if (code) {
    loadPrices(code)
    manualItemCode.value = code
  }
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>
