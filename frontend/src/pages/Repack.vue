<template>
  <div class="h-screen bg-[var(--color-bg)] overflow-hidden">
    <Stock_Template
      ref="invoiceTemplateRef"
      title="REPACK ENTRY"
      title-bar-color="#805ad5"
      :doc-number="repackNo"
      :doc-date="repackDate"
      :items="items"
      :total-amount="totalAmount"
      :total-label="'Total Produced Qty'"
      :show-total-currency="false"
      :item-count="items.length"
      :show-rate="false"
      :show-amount="false"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentRepacks"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :available-series="availableSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      :selected-sidebar-item-name="repackName"
      :show-bottom-left="false"
      :show-bottom-middle="false"
      @sidebar-date-change="handleSidebarDateChange"
      @doc-date-change="handleDocDateChange"
      @update:sidebarSearch="sidebarSearch = $event"
      @update:sidebarSeries="sidebarSeries = $event"
      @toggle-draft-only="draftOnly = !draftOnly"
      @select-sidebar-item="handleSelectSidebarItem"
      @back="goBack"
      @save="handleSave"
      @submit="handleSubmit"
      @print="handlePrint"
      @cancel="handleCancel"
      :is-draft="isDraft"
    >
      <template #header-bar>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-6">
            <div v-if="repackNo" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
              <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ repackNo }}</div>
            </div>

            <div class="flex-1 flex items-center gap-8">
              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Source Warehouse</label>
                <select 
                  v-model="fromWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                >
                  <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
                </select>
              </div>

              <div class="text-4xl text-[var(--color-text-muted)]">→</div>

              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Destination Warehouse</label>
                <select 
                  v-model="toWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                >
                  <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
                </select>
              </div>

              <div class="flex flex-col gap-1 border-l border-[var(--color-border)] pl-8">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Series</label>
                <select 
                  v-model="selectedSeries" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                >
                  <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>

            <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Date</label>
              <div class="flex items-center gap-1">
                <button @click="handleDocDateChange(-1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(repackDate) }}</div>
                <button @click="handleDocDateChange(1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&rarr;</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template #thead>
        <tr class="sticky top-0 z-10 bg-[var(--color-lowlight)] border-b border-[var(--color-border)]">
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-8">#</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-48">Item Code</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)]">Item Name</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">Qty</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">UOM</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Buying</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Rate</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-center text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-36">Type</th>
          <th class="border-b border-[var(--color-border)] w-12"></th>
        </tr>
      </template>

      <template #row="{ item, index }">
        <tr 
          class="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]/50 outline-none"
          :tabindex="isReadOnly ? -1 : 0"
          @keydown="handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl font-mono text-center">{{ index + 1 }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-4xl font-mono">{{ item.item_code }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-4xl font-medium">{{ item.item_name }}</td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input 
              v-if="!isReadOnly"
              v-model.number="item.qty"
              type="number"
              class="w-full bg-transparent px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @keydown.up.prevent
              @keydown.down.prevent
              @keydown.enter.prevent="focusType(index)"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums">{{ item.qty }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ item.uom }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-4xl text-[var(--color-text)]/80 tabular-nums bg-transparent">
            {{ formatRate(getPriceListRate(item, 'Buying')) }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input 
              v-if="!isReadOnly"
              v-model.number="item.rate"
              type="number"
              step="0.01"
              class="w-full bg-transparent px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @keydown.up.prevent
              @keydown.down.prevent
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums">{{ formatRate(item.rate) }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-center">
            <span 
              v-if="isReadOnly"
              class="inline-block px-3 py-1 rounded text-2xl font-bold uppercase tracking-wider"
              :class="item.type === 'Consume' ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'"
            >
              {{ item.type }}
            </span>
            <select 
              v-else
              :ref="el => setTypeRef(el, index)"
              v-model="item.type"
              class="bg-transparent border border-[var(--color-border)] rounded px-2 py-0.5 font-bold text-2xl outline-none focus:border-[var(--color-focus)]"
              :class="item.type === 'Consume' ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
              @keydown.enter.prevent="focusBarcodeInput"
            >
              <option value="Consume" class="text-[var(--color-danger)] bg-[var(--color-surface)]">Consume</option>
              <option value="Produce" class="text-[var(--color-success)] bg-[var(--color-surface)]">Produce</option>
            </select>
          </td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]" @click="removeItem(index)">&times;</button>
          </td>
        </tr>
      </template>

      <template #table-extra-rows>
        <!-- Pending item row -->
        <template v-if="pendingItem && !isReadOnly">
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10 font-bold">
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-3xl font-mono text-center">+</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-4xl font-mono">{{ pendingItem.item_code }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-4xl font-medium">{{ pendingItem.item_name }}</td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="pendingQtyInput"
                v-model.number="pendingItem.qty"
                type="number"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                @keydown.up.prevent
                @keydown.down.prevent
                @keydown="handlePendingQtyKeydown"
              />
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ pendingItem.uom || 'Nos' }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-4xl text-[var(--color-text)]/70 tabular-nums bg-transparent">
              {{ formatRate(getPriceListRate(pendingItem, 'Buying')) }}
            </td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                v-model.number="pendingItem.rate"
                type="number"
                step="0.01"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                @keydown.up.prevent
                @keydown.down.prevent
              />
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-center">
              <select 
                ref="pendingTypeInput"
                v-model="pendingItem.type"
                class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-1 text-2xl font-bold outline-none focus:border-[var(--color-focus)]"
                :class="pendingItem.type === 'Consume' ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
                @keydown="handlePendingTypeKeydown"
              >
                <option value="Consume" class="text-[var(--color-danger)]">Consume</option>
                <option value="Produce" class="text-[var(--color-success)]">Produce</option>
              </select>
            </td>
            <td class="px-2 py-1 text-center">
              <button class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:text-[var(--color-danger)]" @click="pendingItem = null; focusBarcodeInput()">&times;</button>
            </td>
          </tr>
        </template>

        <tr v-if="!isReadOnly && !pendingItem" class="bg-[var(--color-highlight)]/5">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl font-mono text-center">*</td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input
              ref="barcodeInput"
              v-model="barcodeQuery"
              placeholder="Scan Barcode or Type Item Name..."
              class="w-full bg-transparent px-4 py-3 text-4xl font-mono text-[var(--color-highlight)] outline-none placeholder:text-[var(--color-text-muted)]/30"
              @input="onBarcodeInput"
              @keydown="handleBarcodeKeydown"
            />
          </td>
          <td :colspan="5 + priceLists.length" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter Item Code to add to Repack</td>
        </tr>
      </template>
    </Stock_Template>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :query="barcodeQuery"
      search-type="Stock"
      :warehouse="fromWarehouse"
      :anchor-el="quickSearchAnchor"
      :last-item-code="items[items.length - 1]?.item_code"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
      @refresh="onQuickSearchRefresh"
    />

    <!-- Item Search Modal -->
    <ItemSearch 
      v-if="showItemSearch"
      :show="showItemSearch"
      :initial-query="itemSearchInitialQuery"
      :skip-date-filter="true"
      @close="showItemSearch = false"
      @select="handleItemSelect"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useShortcuts } from '../services/shortcutManager'
import Stock_Template from '../components/Stock_Template.vue'
import ItemSearch from '../components/ItemSearch.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { frappePost } from '../api'
import { useItemCache } from '../services/itemCache.js'

import { formatDMY } from '../utils/date'
import { serverToday, toLocalISO } from '../services/serverTime'
const router = useRouter()

useShortcuts({
  'ESCAPE': () => {
    goBack()
  }
})
const { refreshItemCache, lookupItemInCache, searchItemsInCache, items: cachedItems } = useItemCache()

const repackNo = ref('')
const repackDate = ref(serverToday())
const fromWarehouse = ref('')
const toWarehouse = ref('')
const items = ref([])
const warehouses = ref([])
const availableSeries = ref([])
const selectedSeries = ref('')

const isReadOnly = ref(false)
const isDraft = ref(false)
const submitting = ref(false)
const repackName = ref('')

const barcodeQuery = ref('')
const barcodeInput = ref(null)
const showItemSearch = ref(false)
const itemSearchInitialQuery = ref('')

const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)

const pendingItem = ref(null)
const pendingQtyInput = ref(null)
const pendingTypeInput = ref(null)
const typeRefs = ref([])

const sidebarDate = ref(serverToday())
const recentRepacks = ref([])
const sidebarSearch = ref('')
const sidebarSeries = ref([])
const draftOnly = ref(false)
const sidebarLoading = ref(false)

const totalAmount = computed(() => {
  // Sum the produced items quantity as total repacked quantity
  return items.value
    .filter(i => i.type === 'Produce')
    .reduce((sum, item) => sum + item.qty, 0)
})

const saveButtonText = computed(() => {
  if (isReadOnly.value && !isDraft.value) return 'New'
  if (isReadOnly.value && isDraft.value) return 'Edit'
  return 'Save'
})

const priceLists = ref([])
try {
  priceLists.value = JSON.parse(localStorage.getItem('wb-pricelist') || '[]')
} catch {
  priceLists.value = []
}

function getPriceListRate(item, priceListName) {
  if (!item) return 0.0
  
  if (item.price_lists) {
    const pl = item.price_lists.find(p => p.name === priceListName)
    if (pl) return pl.rate
  }
  
  if (item.uom_price_lists?.[priceListName]) {
    const targetUom = item.uom || 'Nos'
    if (item.uom_price_lists[priceListName][targetUom] != null) {
      return item.uom_price_lists[priceListName][targetUom]
    }
    const rates = Object.values(item.uom_price_lists[priceListName])
    if (rates.length) return rates[0]
  }
  
  const cached = lookupItemInCache(item.item_code)
  if (cached) {
    if (cached.uom_price_lists?.[priceListName]) {
      const targetUom = item.uom || cached.uom || 'Nos'
      if (cached.uom_price_lists[priceListName][targetUom] != null) {
        return cached.uom_price_lists[priceListName][targetUom]
      }
      const rates = Object.values(cached.uom_price_lists[priceListName])
      if (rates.length) return rates[0]
    }
    
    if (cached.price_lists) {
      const pl = cached.price_lists.find(p => p.name === priceListName)
      if (pl) return pl.rate
    }
  }
  
  return 0.0
}

function formatRate(val) {
  const num = parseFloat(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

function autoCalculateProduceRates() {
  const consumeItems = items.value.filter(i => i.type === 'Consume')
  const produceItems = items.value.filter(i => i.type === 'Produce')
  
  if (!produceItems.length) return
  
  // Calculate total consumed valuation
  const totalConsumedValuation = consumeItems.reduce((sum, item) => {
    const rate = item.rate || getPriceListRate(item, 'Buying') || 0
    return sum + (item.qty * rate)
  }, 0)
  
  // Calculate total produced quantity
  const totalProduceQty = produceItems.reduce((sum, item) => sum + item.qty, 0)
  
  if (totalProduceQty <= 0) {
    for (const item of produceItems) {
      if (item.rate !== 0) item.rate = 0
    }
    return
  }
  
  // Distribute the valuation
  const ratePerQty = totalConsumedValuation / totalProduceQty
  const newRate = parseFloat(ratePerQty.toFixed(4))
  for (const item of produceItems) {
    if (item.rate !== newRate) {
      item.rate = newRate
    }
  }
}

watch(
  items,
  () => {
    if (isReadOnly.value) return
    autoCalculateProduceRates()
  },
  { deep: true }
)

watch(
  cachedItems,
  () => {
    if (isReadOnly.value) return
    autoCalculateProduceRates()
  }
)

onMounted(async () => {
  await fetchMetadata()
  await fetchRecentRepacks()
  refreshItemCache('Stock')
  focusBarcodeInput()

  if (!priceLists.value.length) {
    try {
      const res = await frappePost('ssplbilling.api.SaleEntry_api.get_sync_metadata')
      if (res && res.price_lists) {
        priceLists.value = res.price_lists
        localStorage.setItem('wb-pricelist', JSON.stringify(res.price_lists))
      }
    } catch (e) {
      console.error('Failed to fetch price lists:', e)
    }
  }
})

async function fetchMetadata() {
  const res = await frappePost('ssplbilling.api.repack_api.get_metadata')
  warehouses.value = res.warehouses
  availableSeries.value = res.naming_series
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  
  const localWh = localStorage.getItem('wb-warehouse')
  if (localWh && warehouses.value.some(w => w.name === localWh)) {
    fromWarehouse.value = localWh
    toWarehouse.value = localWh
  } else if (warehouses.value.length > 0) {
    fromWarehouse.value = warehouses.value[0].name
    toWarehouse.value = warehouses.value[0].name
  }
}

async function fetchRecentRepacks() {
  sidebarLoading.value = true
  recentRepacks.value = await frappePost('ssplbilling.api.repack_api.get_recent_repacks', { date: sidebarDate.value })
  sidebarLoading.value = false
}

function focusBarcodeInput() {
  nextTick(() => barcodeInput.value?.focus())
}

function onBarcodeInput() {
  const code = barcodeQuery.value.trim()
  if (barcodeQuery.value === '  ') {
    quickSearchResults.value = [{ item_code: 'DUMMY' }]
    quickSearchAnchor.value = barcodeInput.value
  } else if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = barcodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

function handleBarcodeKeydown(e) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === 'Escape') {
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    }
  }

  if (e.key === 'Enter') {
    handleBarcodeEnter()
  }
}

async function handleBarcodeEnter() {
  if (!barcodeQuery.value) return
  
  const code = barcodeQuery.value.trim()
  const match = lookupItemInCache(code)
  
  if (match) {
    setPendingItem(match)
    barcodeQuery.value = ''
    quickSearchResults.value = []
  } else {
    const res = await frappePost('ssplbilling.api.storetransfer_api.get_item_details', { 
      item_code: barcodeQuery.value,
      warehouse: fromWarehouse.value
    })
    
    if (res.found) {
      setPendingItem(res)
      barcodeQuery.value = ''
      quickSearchResults.value = []
    } else {
      openItemSearch(barcodeQuery.value)
    }
  }
}

function onQuickSearchRefresh() {
  if (barcodeQuery.value) {
    quickSearchResults.value = searchItemsInCache(barcodeQuery.value)
  }
}

function onQuickSearchSelect(item) {
  setPendingItem(item)
  barcodeQuery.value = ''
  quickSearchResults.value = []
}

function openItemSearch(query) {
  itemSearchInitialQuery.value = query || ''
  showItemSearch.value = true
}

function handleItemSelect(item) {
  setPendingItem(item)
  barcodeQuery.value = ''
  quickSearchResults.value = []
  showItemSearch.value = false
}

function setPendingItem(details) {
  pendingItem.value = {
    item_code: details.item_code,
    item_name: details.item_name,
    qty: 0,
    uom: details.uom,
    rate: details.valuation_rate || details.rate || 0,
    type: 'Consume'
  }
  nextTick(() => {
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  })
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value
  
  const existing = items.value.find(i => i.item_code === p.item_code && i.type === p.type)
  if (existing) {
    existing.qty += p.qty
  } else {
    items.value.push({
      item_code: p.item_code,
      item_name: p.item_name,
      qty: p.qty,
      uom: p.uom,
      rate: p.rate || 0,
      type: p.type
    })
  }
  
  pendingItem.value = null
  focusBarcodeInput()
}

function handlePendingQtyKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    pendingTypeInput.value?.focus()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    pendingItem.value = null
    focusBarcodeInput()
  }
}

function handlePendingTypeKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    confirmPendingItem()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    pendingItem.value = null
    focusBarcodeInput()
  }
}

function setTypeRef(el, idx) {
  if (el) {
    typeRefs.value[idx] = el
  }
}

function focusType(idx) {
  nextTick(() => {
    typeRefs.value[idx]?.focus()
  })
}

function removeItem(index) {
  items.value.splice(index, 1)
}

function handleRowKeydown(e, idx) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusBarcodeInput()
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    e.preventDefault()
    removeItem(idx)
  }
}

async function handleSave() {
  if (submitting.value) return
  if (isReadOnly.value && !isDraft.value) {
    resetForm()
    return
  }
  if (isReadOnly.value && isDraft.value) {
    isReadOnly.value = false
    return
  }

  if (!items.value.length) { alert('No items to save'); return }

  submitting.value = true
  try {
    const res = await frappePost('ssplbilling.api.repack_api.save_repack', {
      data: {
        company: localStorage.getItem('wb-company') || null,
        name: repackName.value || undefined,
        naming_series: selectedSeries.value,
        posting_date: repackDate.value,
        from_warehouse: fromWarehouse.value,
        to_warehouse: toWarehouse.value,
        items: items.value
      }
    })
    
    repackNo.value = res.name
    repackName.value = res.name
    isReadOnly.value = true
    isDraft.value = true
    await fetchRecentRepacks()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}

async function handleSubmit() {
  if (!repackName.value) return
  try {
    await frappePost('ssplbilling.api.repack_api.submit_repack', { name: repackName.value })
    isDraft.value = false
    await fetchRecentRepacks()
  } catch (err) {
    console.error(err)
  }
}

function resetForm() {
  repackNo.value = ''
  repackName.value = ''
  items.value = []
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  isReadOnly.value = false
  isDraft.value = false
  focusBarcodeInput()
}

function goBack() {
  router.push('/')
}

function handleSidebarDateChange(dir) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + dir)
  sidebarDate.value = toLocalISO(d)
  fetchRecentRepacks()
}

function handleDocDateChange(dir) {
  const d = new Date(repackDate.value)
  d.setDate(d.getDate() + dir)
  repackDate.value = toLocalISO(d)
}

async function handleSelectSidebarItem(item) {
  const details = await frappePost('ssplbilling.api.repack_api.get_repack_details', { name: item.name })
  repackNo.value = details.name
  repackName.value = details.name
  repackDate.value = details.posting_date
  fromWarehouse.value = details.from_warehouse
  toWarehouse.value = details.to_warehouse
  selectedSeries.value = details.naming_series
  items.value = details.items.map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    qty: i.qty,
    uom: i.uom,
    rate: i.rate,
    type: i.type
  }))
  isReadOnly.value = true
  isDraft.value = details.docstatus === 0
}

function formatDate(dateString) {
  return formatDMY(dateString, '')
}

function handlePrint() {
  // Print logic if needed
}

function handleCancel() {
  if (confirm('Are you sure you want to cancel?')) {
    resetForm()
  }
}
</script>

<style scoped>
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}
</style>
