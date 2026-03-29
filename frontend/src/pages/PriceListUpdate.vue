<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4' : 'min-h-screen bg-slate-900 flex flex-col'">
    <div :class="isSubWindow ? 'flex h-[70vh] w-[70vw] flex-col overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl' : 'flex flex-1 flex-col'">
      <!-- Header -->
      <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-4">
        <div class="flex items-center gap-4">
          <button
            v-if="isSubWindow"
            class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700"
            @click="$emit('close')"
          >
            &larr; Back to Entry
          </button>
          <button
            v-else
            class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700"
            @click="router.push('/')"
          >
            &larr; Dashboard
          </button>
          <h1 class="text-xl font-bold text-slate-100">Update Item Prices</h1>
          <div v-if="itemCode" class="rounded-full bg-blue-900/20 px-3 py-1 text-sm font-bold text-blue-400">
            {{ itemCode }}
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-slate-400">
            <kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">F8</kbd> Save All
            <kbd class="ml-2 rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Esc</kbd> Close
          </span>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="mx-auto max-w-4xl rounded-xl border border-slate-700 bg-slate-800 shadow-sm overflow-hidden">
          <div v-if="loading" class="flex items-center justify-center py-20">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          </div>

          <div v-else-if="!itemCode && !isSubWindow" class="p-10 text-center">
            <div class="mb-4 text-slate-400">Please provide an item code to update prices.</div>
            <input
              v-model="manualItemCode"
              class="rounded border border-slate-600 bg-slate-800 px-4 py-2 text-slate-200 outline-none focus:border-blue-500"
              placeholder="Enter Item Code..."
              @keydown.enter="loadPrices(manualItemCode)"
            />
          </div>

          <table v-else class="w-full text-left border-collapse">
            <thead class="bg-slate-800 border-b border-slate-700">
              <tr>
                <th class="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-400">Price List</th>
                <th class="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-400">Type</th>
                <th class="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Current Rate</th>
                <!-- One "New Rate" column per UOM -->
                <th
                  v-for="u in uoms"
                  :key="u.uom"
                  class="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider"
                  :class="u.uom === stockUom ? 'text-blue-400' : 'text-amber-400'"
                >
                  New Rate
                  <span class="block font-normal normal-case text-[10px] mt-0.5 opacity-80">
                    {{ u.uom }}<span v-if="u.conversion_factor !== 1" class="ml-1 text-slate-500">×{{ u.conversion_factor }}</span>
                  </span>
                </th>
                <th v-if="selectedPriceList" class="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Disc %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <tr
                v-for="(p, idx) in prices"
                :key="p.price_list"
                class="hover:bg-slate-800/40 transition-colors"
                :class="{ 'bg-blue-900/30': activeRow === idx }"
                @click="activeRow = idx"
              >
                <td class="px-4 py-3">
                  <div class="font-semibold text-slate-100">{{ p.price_list }}</div>
                  <div v-if="p.price_list === selectedPriceList" class="text-[10px] font-bold text-blue-400 uppercase">Selected in entry</div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex gap-1">
                    <span v-if="p.buying" class="rounded bg-green-900/20 px-1.5 py-0.5 text-[10px] font-bold text-green-400">BUY</span>
                    <span v-if="p.selling" class="rounded bg-blue-900/20 px-1.5 py-0.5 text-[10px] font-bold text-blue-400">SELL</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-right font-mono text-slate-400">
                  &#8377;{{ p.original_rate.toFixed(2) }}
                </td>
                <!-- Rate input per UOM -->
                <td
                  v-for="(u, uidx) in uoms"
                  :key="u.uom"
                  class="px-4 py-3 text-right"
                >
                  <input
                    :ref="el => inputRefs[`rate-${idx}-${uidx}`] = el"
                    type="number"
                    v-model.number="p.uom_rates[u.uom]"
                    step="0.01"
                    class="w-28 rounded border bg-slate-800 px-2 py-1.5 text-right font-mono font-bold text-slate-200 outline-none focus:ring-1 transition-colors"
                    :class="u.uom === stockUom ? 'border-slate-600 focus:border-blue-500 focus:ring-blue-500/20' : 'border-amber-800/40 focus:border-amber-500 focus:ring-amber-500/20'"
                    @keydown.enter.prevent="onRateEnter(idx, uidx)"
                    @keydown.up.prevent="moveVertical(idx, -1, uidx)"
                    @keydown.down.prevent="moveVertical(idx, 1, uidx)"
                  />
                </td>
                <td v-if="selectedPriceList" class="px-4 py-3 text-right">
                  <input
                    v-if="p.price_list === selectedPriceList"
                    :ref="el => inputRefs[`disc-${idx}`] = el"
                    type="number"
                    v-model.number="discount"
                    step="0.5"
                    min="0"
                    max="100"
                    class="w-20 rounded border border-blue-500 bg-blue-900/20 px-3 py-1.5 text-right font-mono font-bold text-blue-300 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20"
                    @keydown.enter.prevent="onDiscEnter(idx)"
                    @keydown.up.prevent="moveVertical(idx, -1, uoms.length - 1)"
                    @keydown.down.prevent="moveVertical(idx, 1, uoms.length - 1)"
                  />
                  <span v-else class="text-slate-600">--</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <!-- Footer -->
      <footer class="border-t border-slate-700 bg-slate-800 px-6 py-4">
        <div class="mx-auto max-w-4xl flex items-center justify-between">
          <div class="text-sm text-slate-400">
            Total Price Lists: <span class="font-bold text-slate-200">{{ prices.length }}</span>
          </div>
          <div class="flex gap-3">
            <button
              class="rounded-lg border border-slate-600 bg-slate-700 px-6 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-600"
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
import { useSubwindow } from '../services/shortcutManager'

const props = defineProps({
  isSubWindow: { type: Boolean, default: false },
  itemCode: { type: String, default: '' },
  selectedPriceList: { type: String, default: '' },
  initialDiscount: { type: Number, default: 0 }
})

const emit = defineEmits(['close', 'saved'])

if (props.isSubWindow) useSubwindow()

const router = useRouter()
const route = useRoute()

const prices = ref([])
const uoms = ref([])
const stockUom = ref('')
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
    uoms.value = data.uoms || []
    stockUom.value = data.stock_uom || ''
    prices.value = (data.prices || []).map(p => ({
      ...p,
      original_rate: p.rate,
      original_uom_rates: { ...(p.uom_rates || {}) },
    }))

    // Set active row to selected price list if exists
    if (props.selectedPriceList) {
      const idx = prices.value.findIndex(p => p.price_list === props.selectedPriceList)
      if (idx !== -1) activeRow.value = idx
    }

    nextTick(() => {
      focusInput(`rate-${activeRow.value}-0`)
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

  // Only update prices that have changed (base rate or any uom rate)
  const changedPrices = prices.value.filter(p => {
    if (p.rate !== p.original_rate) return true
    for (const u of uoms.value) {
      if ((p.uom_rates[u.uom] ?? 0) !== (p.original_uom_rates[u.uom] ?? 0)) return true
    }
    return false
  })
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

function onRateEnter(idx, uidx) {
  activeRow.value = idx
  // Move right across UOM columns first
  if (uidx < uoms.value.length - 1) {
    focusInput(`rate-${idx}-${uidx + 1}`)
    return
  }
  // Last UOM column: go to disc if this row has it
  if (props.selectedPriceList && prices.value[idx].price_list === props.selectedPriceList) {
    focusInput(`disc-${idx}`)
  } else {
    goToNextRow(idx)
  }
}

function onDiscEnter(idx) {
  activeRow.value = idx
  goToNextRow(idx)
}

function goToNextRow(idx) {
  if (idx < prices.value.length - 1) {
    activeRow.value = idx + 1
    focusInput(`rate-${idx + 1}-0`)
  } else {
    saveAll()
  }
}

function moveVertical(idx, dir, uidx) {
  const next = idx + dir
  if (next >= 0 && next < prices.value.length) {
    activeRow.value = next
    focusInput(`rate-${next}-${uidx ?? 0}`)
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
