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
                <button v-if="canModifyDate()" @click="handleDocDateChange(-1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(repackDate) }}</div>
                <DatePickerButton v-if="canModifyDate()" v-model="repackDate" label="Choose document date" :disabled="isReadOnly" />
                <button v-if="canModifyDate()" @click="handleDocDateChange(1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&rarr;</button>
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
          :ref="el => { if (el) rowRefs[index] = el }"
          :tabindex="isReadOnly ? -1 : 0"
          class="border-b border-[var(--color-border)] outline-none cursor-pointer transition-all"
          :class="{
            'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)] font-bold !text-[var(--color-text-on-focus)]': !isReadOnly && (selectedRowIdx === index || editingRowIdx === index),
            'hover:bg-[var(--color-surface-raised)]/50': isReadOnly || (selectedRowIdx !== index && editingRowIdx !== index)
          }"
          @focus="!isReadOnly && (selectedRowIdx = index)"
          @keydown="!isReadOnly && handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-center" :class="isSelected(index) ? 'text-black' : 'text-[var(--color-text-muted)]'">{{ index + 1 }}</td>

          <!-- item_code -->
          <td class="p-0 border-r border-[var(--color-border)]" @click="startCellEdit(index, 'code')">
            <input v-if="editingRowIdx === index && editingField === 'code'"
              ref="editCodeInput"
              v-model="item.item_code"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @focus="e => e.target.select()"
              @input="onEditCodeInput(index)"
              @keydown="onEditCodeKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono" :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">{{ item.item_code }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-medium" :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.item_name }}</td>

          <!-- qty -->
          <td class="p-0 border-r border-[var(--color-border)]" @click="startCellEdit(index, 'qty')">
            <input v-if="editingRowIdx === index && editingField === 'qty'"
              ref="editQtyInput"
              v-model.number="item.qty"
              type="number"
              step="0.001"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @keydown="onEditQtyKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums" :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.qty }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl" :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ item.uom }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-4xl tabular-nums" :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]/80'">
            {{ formatRate(getPriceListRate(item, 'Buying')) }}
          </td>

          <!-- rate -->
          <td class="p-0 border-r border-[var(--color-border)]" @click="startCellEdit(index, 'rate')">
            <input v-if="editingRowIdx === index && editingField === 'rate'"
              ref="editRateInput"
              v-model.number="item.rate"
              type="number"
              step="0.001"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-[var(--color-text)] text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @input="onRateInput(item)"
              @keydown="onEditRateKeydown($event, index)"
            />
            <span
              v-else
              class="block px-2 py-1 text-6xl font-mono text-right tabular-nums"
              :class="isSelected(index) ? '!text-[var(--color-text-on-focus)]' : item.rate_manual ? 'text-[var(--color-warning)]' : 'text-[var(--color-text)]'"
              :title="item.rate_manual ? 'Manual rate (clear it to recalculate)' : ''"
            >{{ formatRate(item.rate, item.type === 'Produce' ? PRODUCE_RATE_PRECISION : 2) }}</span>
          </td>

          <!-- type -->
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-center" @click="startCellEdit(index, 'type')">
            <select v-if="editingRowIdx === index && editingField === 'type'"
              ref="editTypeSelect"
              v-model="item.type"
              class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-0.5 font-bold text-2xl outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              :class="item.type === 'Consume' ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
              @change="onTypeChange(item)"
              @keydown="onEditTypeKeydown($event, index)"
            >
              <option value="Consume" class="text-[var(--color-danger)] bg-[var(--color-surface)]">Consume</option>
              <option value="Produce" class="text-[var(--color-success)] bg-[var(--color-surface)]">Produce</option>
            </select>
            <span
              v-else
              class="inline-block px-3 py-1 rounded text-2xl font-bold uppercase tracking-wider"
              :class="item.type === 'Consume' ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'"
            >
              {{ item.type }}
            </span>
          </td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" tabindex="-1" class="rounded px-1 py-0.5 hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]" :class="isSelected(index) ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'" @click.stop="removeItem(index)">&times;</button>
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
                step="0.001"
                @input="onRateInput(pendingItem)"
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
      :query="editQuickSearchRowIdx !== null ? (items[editQuickSearchRowIdx]?.item_code || '') : barcodeQuery"
      search-type="Stock"
      :warehouse="fromWarehouse"
      :anchor-el="quickSearchAnchor"
      :last-item-code="items[items.length - 1]?.item_code"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []; editQuickSearchRowIdx = null"
      @refresh="onQuickSearchRefresh"
    />

    <!-- Item Search Modal -->
    <ItemSearch 
      v-if="showItemSearch"
      :show="showItemSearch"
      :initial-query="itemSearchInitialQuery"
      :skip-date-filter="true"
      @close="closeItemSearch"
      @select="handleItemSelect"
    />

    <!-- Price List Update for produced items -->
    <PriceListUpdate
      v-if="priceListUpdateItem"
      :is-sub-window="true"
      :item-code="priceListUpdateItem.item_code"
      :selected-price-list="buyingPriceList"
      :initial-rate="Number(priceListUpdateItem.rate) || 0"
      :initial-uom="priceListUpdateItem.uom || ''"
      :initial-qty="Number(priceListUpdateItem.qty) || 0"
      @close="closePriceListUpdate"
      @saved="closePriceListUpdate"
    />
  </div>
</template>

<script setup>
import DatePickerButton from '../components/DatePickerButton.vue'
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useShortcuts } from '../services/shortcutManager'
import Stock_Template from '../components/Stock_Template.vue'
import ItemSearch from '../components/ItemSearch.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import PriceListUpdate from './PriceListUpdate.vue'
import { frappePost } from '../api'
import { useItemCache } from '../services/itemCache.js'
import { canModifyDate } from '../composables/usePermission.js'

import { formatDMY } from '../utils/date'
import { serverToday, toLocalISO, parseCalendarDate } from '../services/serverTime'
const router = useRouter()

useShortcuts({
  'ESCAPE': () => {
    goBack()
  }
})
const { refreshItemCache, lookupItemInCache, searchItemsInCache, items: cachedItems } = useItemCache()

const repackNo = ref('')
const repackDate = ref(serverToday())
const repackTime = ref('')
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
const rowRefs = ref([])
const selectedRowIdx = ref(-1)
// Row edit mode, as in Sales Invoice: one cell of one row is editable at a time
const editingRowIdx = ref(-1)
const editingField = ref(null) // 'code' | 'qty' | 'type' | 'rate'
const editCodeInput = ref(null)
const editQtyInput = ref(null)
const editTypeSelect = ref(null)
const editRateInput = ref(null)
const originalRowCode = ref('')
const editQuickSearchRowIdx = ref(null) // null = barcode entry, number = row code edit
const itemSearchRowIdx = ref(null) // row the Item Search modal is picking for
const priceListUpdateItem = ref(null)

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

// Buying price list the produced item's cost rate is entered into
const buyingPriceList = computed(() =>
  priceLists.value.find(p => p === 'Buying')
  || priceLists.value.find(p => String(p).toLowerCase().includes('buying'))
  || 'Buying'
)

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

// Produced item rates are kept and shown to 3 decimals
const PRODUCE_RATE_PRECISION = 3

function formatRate(val, digits = 2) {
  const num = parseFloat(val)
  return (isNaN(num) ? 0 : num).toFixed(digits)
}

function consumedValuation(rows) {
  return rows
    .filter(i => i.type === 'Consume')
    .reduce((sum, item) => sum + (item.qty * (item.rate || getPriceListRate(item, 'Buying') || 0)), 0)
}

// Produce rows share the consumed valuation left after the manually rated ones
function autoCalculateProduceRates() {
  const produceItems = items.value.filter(i => i.type === 'Produce')
  const autoItems = produceItems.filter(i => !i.rate_manual)
  if (!autoItems.length) return

  const manualValuation = produceItems
    .filter(i => i.rate_manual)
    .reduce((sum, item) => sum + (item.qty * (Number(item.rate) || 0)), 0)
  const autoQty = autoItems.reduce((sum, item) => sum + item.qty, 0)

  const ratePerQty = autoQty > 0 ? Math.max(0, (consumedValuation(items.value) - manualValuation) / autoQty) : 0
  const newRate = parseFloat(ratePerQty.toFixed(PRODUCE_RATE_PRECISION))
  for (const item of autoItems) {
    if (item.rate !== newRate) {
      item.rate = newRate
    }
  }
}

// A typed rate on a Produce row sticks; clearing the field hands it back to the auto calculation
function onRateInput(item) {
  if (item?.type !== 'Produce') return
  item.rate_manual = item.rate !== '' && item.rate != null
  if (!item.rate_manual) item.rate = 0
}

function onTypeChange(item) {
  if (item.type !== 'Produce') item.rate_manual = false
}

// Saved entries carry no manual marker of their own: a single produced row is manual when
// set_basic_rate_manually is on, several are manual when their rate differs from an even split
function markLoadedManualRates(serverRows) {
  const produceRows = items.value.filter(i => i.type === 'Produce')
  if (produceRows.length === 1) {
    const idx = items.value.indexOf(produceRows[0])
    produceRows[0].rate_manual = !!serverRows[idx]?.set_basic_rate_manually
    return
  }
  const totalQty = produceRows.reduce((sum, item) => sum + item.qty, 0)
  if (totalQty <= 0) return
  const even = consumedValuation(items.value) / totalQty
  for (const item of produceRows) {
    item.rate_manual = Math.abs((Number(item.rate) || 0) - even) > 0.0005
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
  refreshItemCache('Sales')
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
  const res = await frappePost('ssplbilling.api.repack_api.get_metadata', {
    company: localStorage.getItem('wb-company') || null
  })
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
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
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
  } else if (e.key === 'ArrowUp' && items.value.length) {
    e.preventDefault()
    focusRow(items.value.length - 1)
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
  const query = editQuickSearchRowIdx.value !== null
    ? (items.value[editQuickSearchRowIdx.value]?.item_code || '').trim()
    : barcodeQuery.value
  if (query) {
    quickSearchResults.value = searchItemsInCache(query)
  }
}

function onQuickSearchSelect(item) {
  if (!item) return
  quickSearchResults.value = []
  if (editQuickSearchRowIdx.value !== null) {
    const rowIdx = editQuickSearchRowIdx.value
    editQuickSearchRowIdx.value = null
    applyItemToRow(rowIdx, item)
    return
  }
  setPendingItem(item)
  barcodeQuery.value = ''
}

function openItemSearch(query, rowIdx = null) {
  itemSearchRowIdx.value = rowIdx
  itemSearchInitialQuery.value = query || ''
  showItemSearch.value = true
}

function closeItemSearch() {
  showItemSearch.value = false
  const rowIdx = itemSearchRowIdx.value
  itemSearchRowIdx.value = null
  if (rowIdx !== null && items.value[rowIdx]) focusEditField('code', rowIdx)
  else focusBarcodeInput()
}

function handleItemSelect(item) {
  showItemSearch.value = false
  quickSearchResults.value = []
  const rowIdx = itemSearchRowIdx.value
  itemSearchRowIdx.value = null
  if (rowIdx !== null && items.value[rowIdx]) {
    applyItemToRow(rowIdx, item)
    return
  }
  setPendingItem(item)
  barcodeQuery.value = ''
}

function setPendingItem(details) {
  pendingItem.value = {
    item_code: details.item_code,
    item_name: details.item_name,
    qty: 0,
    uom: details.uom,
    rate: details.valuation_rate || details.rate || 0,
    // Second row is the produced item by default
    type: items.value.length === 1 ? 'Produce' : 'Consume'
  }
  nextTick(() => {
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  })
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value
  
  let idx = items.value.findIndex(i => i.item_code === p.item_code && i.type === p.type)
  if (idx !== -1) {
    items.value[idx].qty += p.qty
  } else {
    idx = items.value.length
    items.value.push({
      item_code: p.item_code,
      item_name: p.item_name,
      qty: p.qty,
      uom: p.uom,
      rate: p.rate || 0,
      type: p.type,
      rate_manual: p.type === 'Produce' && !!p.rate_manual
    })
  }
  
  pendingItem.value = null
  // Produce rows go on to the rate, then the price list update
  if (p.type === 'Produce') focusEditField('rate', idx)
  else focusBarcodeInput()
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

function isSelected(idx) {
  return !isReadOnly.value && (selectedRowIdx.value === idx || editingRowIdx.value === idx)
}

function focusRow(idx) {
  selectedRowIdx.value = idx
  nextTick(() => {
    const el = rowRefs.value[idx]
    if (el) {
      el.focus({ preventScroll: true })
      el.scrollIntoView({ block: 'nearest' })
    }
  })
}

const EDIT_FIELDS = ['code', 'qty', 'type', 'rate']

function focusEditField(field, idx) {
  if (isReadOnly.value || !items.value[idx]) return
  if (editingRowIdx.value !== idx) {
    originalRowCode.value = items.value[idx].item_code
  }
  editingRowIdx.value = idx
  editingField.value = field
  selectedRowIdx.value = idx
  const inputMap = { code: editCodeInput, qty: editQtyInput, type: editTypeSelect, rate: editRateInput }
  nextTick(() => {
    const el = inputMap[field]?.value
    if (!el) return
    el.focus({ preventScroll: true })
    if (el.select) el.select()
    rowRefs.value[idx]?.scrollIntoView({ block: 'nearest' })
  })
}

function startCellEdit(idx, field) {
  if (isReadOnly.value) return
  if (editingRowIdx.value === idx && editingField.value === field) return
  focusEditField(field, idx)
}

function exitEditMode(idx, cancel = false) {
  const item = items.value[idx]
  // An unapplied code edit falls back to the row's item
  if (cancel && item && editingField.value === 'code') item.item_code = originalRowCode.value
  editingRowIdx.value = -1
  editingField.value = null
  quickSearchResults.value = []
  editQuickSearchRowIdx.value = null
  focusRow(idx)
}

// Close the row edit and move on to the next row, or the barcode input after the last one
function finishRowEdit(idx) {
  editingRowIdx.value = -1
  editingField.value = null
  if (idx < items.value.length - 1) focusRow(idx + 1)
  else focusBarcodeInput()
}

// ArrowLeft / ArrowRight move between the editable cells of a row
function handleCellNavigation(e, idx, field) {
  const pos = EDIT_FIELDS.indexOf(field)
  if (e.key === 'ArrowLeft' && pos > 0) {
    if (e.target.type === 'text' && e.target.selectionStart !== 0) return false
    e.preventDefault()
    focusEditField(EDIT_FIELDS[pos - 1], idx)
    return true
  }
  if (e.key === 'ArrowRight' && pos < EDIT_FIELDS.length - 1) {
    if (e.target.type === 'text' && e.target.selectionStart !== e.target.value.length) return false
    e.preventDefault()
    focusEditField(EDIT_FIELDS[pos + 1], idx)
    return true
  }
  return false
}

function applyItemToRow(idx, details) {
  const row = items.value[idx]
  if (!row || !details) return
  row.item_code = details.item_code
  row.item_name = details.item_name
  row.uom = details.uom || details.stock_uom || row.uom
  // Produce rates are recalculated from the consumed items
  if (row.type === 'Consume') row.rate = details.valuation_rate || details.rate || 0
  originalRowCode.value = row.item_code
  focusEditField('qty', idx)
}

function onEditCodeInput(idx) {
  const code = (items.value[idx]?.item_code || '').trim()
  if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = editCodeInput.value
    editQuickSearchRowIdx.value = idx
  } else {
    quickSearchResults.value = []
    editQuickSearchRowIdx.value = null
  }
}

async function onEditCodeKeydown(e, idx) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Escape') {
      e.preventDefault()
      e.stopPropagation()
      quickSearchResults.value = []
      editQuickSearchRowIdx.value = null
      return
    }
  }

  if (handleCellNavigation(e, idx, 'code')) return

  if (e.key === 'Enter') {
    e.preventDefault()
    const code = (items.value[idx]?.item_code || '').trim()
    if (!code || code === originalRowCode.value) {
      items.value[idx].item_code = originalRowCode.value
      focusEditField('qty', idx)
      return
    }
    const match = lookupItemInCache(code)
    if (match) {
      applyItemToRow(idx, match)
      return
    }
    const res = await frappePost('ssplbilling.api.storetransfer_api.get_item_details', {
      item_code: code,
      warehouse: fromWarehouse.value
    })
    if (res?.found) applyItemToRow(idx, res)
    else openItemSearch(code, idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    exitEditMode(idx, true)
  }
}

function onEditQtyKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'qty')) return
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    e.preventDefault()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (items.value[idx]?.qty > 0) focusEditField('type', idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    exitEditMode(idx)
  }
}

function onEditTypeKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'type')) return
  if (e.key === 'Enter') {
    e.preventDefault()
    if (items.value[idx]?.type === 'Produce') focusEditField('rate', idx)
    else finishRowEdit(idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    exitEditMode(idx)
  }
}

function onEditRateKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'rate')) return
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    e.preventDefault()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = items.value[idx]
    if (item?.type === 'Produce' && item.item_code) {
      editingRowIdx.value = -1
      editingField.value = null
      priceListUpdateItem.value = { ...item }
    } else {
      finishRowEdit(idx)
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    exitEditMode(idx)
  }
}

function closePriceListUpdate() {
  priceListUpdateItem.value = null
  focusBarcodeInput()
}

function removeItem(index) {
  items.value.splice(index, 1)
  rowRefs.value.length = items.value.length
  editingRowIdx.value = -1
  editingField.value = null
  if (!items.value.length) {
    focusBarcodeInput()
  } else {
    focusRow(Math.min(index, items.value.length - 1))
  }
}

function handleRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'Enter') {
    e.preventDefault()
    focusEditField('code', idx)
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    openItemSearch(items.value[idx]?.item_code, idx)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (idx < items.value.length - 1) focusRow(idx + 1)
    else focusBarcodeInput()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (idx > 0) focusRow(idx - 1)
  } else if (e.key === 'Home') {
    e.preventDefault()
    focusRow(0)
  } else if (e.key === 'End') {
    e.preventDefault()
    if (idx === items.value.length - 1) focusBarcodeInput()
    else focusRow(items.value.length - 1)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    focusBarcodeInput()
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    e.preventDefault()
    e.stopPropagation()
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
        posting_time: repackTime.value || undefined,
        from_warehouse: fromWarehouse.value,
        to_warehouse: toWarehouse.value,
        items: items.value
      }
    })
    
    repackNo.value = res.name
    repackName.value = res.name
    repackTime.value = res.posting_time
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
  repackTime.value = ''
  items.value = []
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  isReadOnly.value = false
  isDraft.value = false
  focusBarcodeInput()
}

function goBack() {
  router.push('/')
}

function handleSidebarDateChange(dir) {
  const d = parseCalendarDate(sidebarDate.value)
  d.setDate(d.getDate() + dir)
  sidebarDate.value = toLocalISO(d)
  fetchRecentRepacks()
}

function handleDocDateChange(dir) {
  if (!canModifyDate()) return
  const d = parseCalendarDate(repackDate.value)
  d.setDate(d.getDate() + dir)
  repackDate.value = toLocalISO(d)
}

async function handleSelectSidebarItem(item) {
  const details = await frappePost('ssplbilling.api.repack_api.get_repack_details', { name: item.name })
  repackNo.value = details.name
  repackName.value = details.name
  repackDate.value = details.posting_date
  repackTime.value = details.posting_time
  fromWarehouse.value = details.from_warehouse
  toWarehouse.value = details.to_warehouse
  selectedSeries.value = details.naming_series
  items.value = details.items.map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    qty: i.qty,
    uom: i.uom,
    rate: i.rate,
    type: i.type,
    rate_manual: false
  }))
  markLoadedManualRates(details.items)
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
