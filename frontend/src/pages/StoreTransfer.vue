<template>
  <div class="h-screen bg-[var(--color-bg)] overflow-hidden">
    <Item_Invoice_Template
      ref="invoiceTemplateRef"
      title="STORE TRANSFER"
      title-bar-color="#90cdf4"
      :doc-number="transferNo"
      :doc-date="transferDate"
      :items="items"
      :total-amount="totalAmount"
      :item-count="items.length"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentTransfers"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :available-series="availableSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      :selected-sidebar-item-name="transferName"
      :show-bottom-left="false"
      :show-bottom-middle="false"
      table-class="flex-1"
      bottom-class="h-44 shrink-0"
      doctype="Stock Entry"
      @sidebar-date-change="handleSidebarDateChange"
      @doc-date-change="handleDocDateChange"
      @update:sidebarSearch="sidebarSearch = $event"
      @update:sidebarSeries="sidebarSeries = $event"
      @toggle-draft-only="draftOnly = !draftOnly"
      @select-sidebar-item="handleSelectSidebarItem"
      @back="handleBack"
      @save="handleSave"
      @submit="handleSubmit"
      @print="handlePrint"
      @cancel="handleCancel"
      :is-draft="isDraft"
    >
      <template #header-bar>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-6">
            <div v-if="transferNo" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
              <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ transferNo }}</div>
            </div>

            <div class="flex-1 flex items-center gap-8">
              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Source Warehouse</label>
                <select 
                  ref="fromWarehouseInput"
                  v-model="fromWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                  @keydown.enter.prevent="focusToWarehouse"
                >
                  <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
                </select>
              </div>

              <div class="text-4xl text-[var(--color-text-muted)]">→</div>

              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Destination Warehouse</label>
                <select 
                  ref="toWarehouseInput"
                  v-model="toWarehouse" 
                  :disabled="isReadOnly"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
                  @keydown.enter.prevent="focusBarcodeInput"
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
                <button @click="handleDocDateChange(-1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(transferDate) }}</div>
                <button @click="handleDocDateChange(1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center">&rarr;</button>
              </div>
            </div>
          </div>
        </div>
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
                @keydown="handlePendingQtyKeydown"
              />
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ pendingItem.uom || 'Nos' }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right">{{ pendingItem.rate }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right">{{ (pendingItem.qty * pendingItem.rate).toFixed(2) }}</td>
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
          <td colspan="6" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter Item Code to add to transfer</td>
        </tr>
      </template>

      <template #row="{ item, index }">
        <tr 
          :ref="el => { if (el) rowRefs[index] = el }"
          class="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]/50 outline-none transition-all cursor-pointer"
          :tabindex="isReadOnly ? -1 : 0"
          :class="{
            'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)] font-bold !text-[var(--color-text-on-focus)]': !isReadOnly && (selectedRowIdx === index || editingRowIdx === index),
            'hover:bg-[var(--color-surface-raised)]/50': !isReadOnly && selectedRowIdx !== index && editingRowIdx !== index
          }"
          @focus="!isReadOnly && (selectedRowIdx = index)"
          @keydown="handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-center" :class="selectedRowIdx === index ? 'text-black' : 'text-[var(--color-text-muted)]'">{{ index + 1 }}</td>
          
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="!isReadOnly && editingRowIdx === index && editingField === 'code'"
              ref="editCodeInput"
              v-model="item.item_code"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @focus="e => e.target.select()"
              @input="onEditCodeInput(index)"
              @keydown="onEditCodeKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">{{ item.item_code }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-medium" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.item_name }}</td>
          
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="!isReadOnly && editingRowIdx === index && editingField === 'qty'"
              ref="editQtyInput"
              v-model.number="item.qty"
              type="number"
              :step="item.uom === 'Nos' ? '1' : '0.01'"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @focus="e => e.target.select()"
              @keydown="onEditQtyKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.qty }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ item.uom || 'Nos' }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ format(item.rate) }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ format(item.qty * item.rate) }}</td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] focus:outline-none" @click="removeItem(index)">&times;</button>
          </td>
        </tr>
      </template>

      <template #calculation-rows>
        <tr class="bg-[var(--color-highlight)]/5 font-bold">
          <td colspan="2" class="px-4 py-6 text-3xl text-[var(--color-text)] border border-[var(--color-border)]">Total Transfer Value</td>
          <td class="px-4 py-6 text-right font-mono text-[var(--color-success)] text-5xl border border-[var(--color-border)] font-black">₹ {{ format(totalAmount) }}</td>
        </tr>
        <tr>
          <td colspan="2" class="px-4 py-3 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Total Items</td>
          <td class="px-4 py-3 text-right font-mono text-[var(--color-text-muted)] text-3xl border border-[var(--color-border)] font-bold">{{ items.length }}</td>
        </tr>
      </template>

      <template #actions>
        <div class="flex flex-col gap-2 h-full py-2">
          <!-- Row 1: Save/Edit/New and Print -->
          <div v-if="isReadOnly" class="flex gap-2">
            <button 
              ref="saveBtnRef" 
              @click="handleSave" 
              class="flex-1 rounded py-2.5 text-center text-3xl font-semibold text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 transition-colors uppercase focus:bg-[var(--color-success)] focus:outline-none"
            >
              {{ saveButtonText }}
            </button>
            <button 
              @click="handlePrint" 
              class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition-colors focus:outline-none"
            >
              Print
            </button>
          </div>
          <button 
            v-else
            ref="saveBtnRef" 
            @click="handleSave" 
            class="w-full rounded py-2.5 text-center text-3xl font-semibold text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 transition-colors uppercase focus:bg-[var(--color-success)] focus:outline-none"
          >
            {{ saveButtonText }}
          </button>

          <!-- Row 2: Cancel / Submit / Print placeholder -->
          <div class="flex gap-2">
            <button 
              @click="handleCancel" 
              class="flex-1 rounded border border-[#C2A96E] bg-[#D4B896] py-2.5 text-center text-3xl font-semibold text-[#4A3520] hover:bg-[#C9A87A] transition-colors focus:outline-none"
            >
              Cancel
            </button>
            <button 
              v-if="isDraft && isReadOnly" 
              @click="handleSubmit" 
              class="flex-1 rounded border border-[var(--color-success)] bg-[var(--color-success)]/20 py-2.5 text-center text-3xl font-semibold text-[var(--color-success)] hover:bg-[var(--color-success)]/30 transition-colors uppercase focus:outline-none"
            >
              Submit
            </button>
            <button 
              v-else
              disabled
              class="flex-1 rounded border border-[var(--color-border)]/40 bg-[var(--color-surface)]/30 text-[var(--color-text-muted)] opacity-30 cursor-not-allowed py-2.5 text-center text-3xl font-semibold"
            >
              Print
            </button>
          </div>
        </div>
      </template>

    </Item_Invoice_Template>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :query="editingRowIdx !== -1 && editingField === 'code' ? (items[editingRowIdx]?.item_code || '') : barcodeQuery"
      search-type="Stock"
      :warehouse="fromWarehouse"
      :anchor-el="quickSearchAnchor"
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

    <!-- Exit Warning Modal -->
    <Warning
      :show="showExitWarning"
      title="Exit Page"
      message="Are you sure you want to exit? Unsaved changes will be lost."
      @close="showExitWarning = false"
      @confirm="showExitWarning = false; goBack()"
    />

    <!-- Print Options Modal -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="transferNo"
      doctype="Stock Entry"
      :initial-template="defaultTemplate"
      @close="closePrintModal"
    />

    <!-- Jump to Row Modal -->
    <JumpToRowModal
      v-model:show="showJumpModal"
      :max-rows="items.length"
      @jump="handleJump"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useShortcuts } from '../services/shortcutManager'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import ItemSearch from '../components/ItemSearch.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import Warning from '../components/Warning.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import { frappePost } from '../api'
import { useItemCache } from '../services/itemCache.js'

const showPrintModal = ref(false)
const showJumpModal = ref(false)
const defaultTemplate = ref('')
const saveBtnRef = ref(null)

const router = useRouter()

const showExitWarning = ref(false)

useShortcuts({
  'ESCAPE': () => {
    handleBack()
  }
})
const { refreshItemCache, lookupItemInCache, searchItemsInCache } = useItemCache()

const transferNo = ref('')
const transferDate = ref(new Date().toISOString().split('T')[0])
const fromWarehouse = ref('')
const toWarehouse = ref('')
const items = ref([])
const warehouses = ref([])
const availableSeries = ref([])
const selectedSeries = ref('')

const selectedRowIdx = ref(-1)
const rowRefs = ref([])
const editingRowIdx = ref(-1)
const editingField = ref(null)
const editCodeInput = ref(null)
const editQtyInput = ref(null)
const isReadOnly = ref(false)
const isDraft = ref(false)
const submitting = ref(false)
const transferName = ref('')

const barcodeQuery = ref('')
const barcodeInput = ref(null)
const fromWarehouseInput = ref(null)
const toWarehouseInput = ref(null)
const showItemSearch = ref(false)
const itemSearchInitialQuery = ref('')

const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)

const pendingItem = ref(null)
const pendingQtyInput = ref(null)

const sidebarDate = ref(new Date().toISOString().split('T')[0])
const recentTransfers = ref([])
const sidebarSearch = ref('')
const sidebarSeries = ref([])
const draftOnly = ref(false)
const sidebarLoading = ref(false)

const totalAmount = computed(() => {
  return items.value.reduce((sum, item) => sum + (item.qty * item.rate), 0).toFixed(2)
})

const saveButtonText = computed(() => {
  if (isReadOnly.value && !isDraft.value) return 'New'
  if (isReadOnly.value && isDraft.value) return 'Edit'
  return 'Save'
})

onMounted(async () => {
  await fetchMetadata()
  await fetchRecentTransfers()
  refreshItemCache('Stock')
  focusFromWarehouse()
})

async function fetchMetadata() {
  const company = localStorage.getItem('wb-company') || ''
  const res = await frappePost('ssplbilling.api.storetransfer_api.get_metadata', { company })
  warehouses.value = res.warehouses
  availableSeries.value = res.naming_series
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  
  const localWh = localStorage.getItem('wb-warehouse')
  if (localWh && warehouses.value.some(w => w.name === localWh)) {
    fromWarehouse.value = localWh
  } else if (warehouses.value.length > 0) {
    fromWarehouse.value = warehouses.value[0].name
  }

  if (warehouses.value.length >= 2) {
    const defaultTo = warehouses.value[1].name
    if (fromWarehouse.value === defaultTo) {
      toWarehouse.value = warehouses.value[0].name
    } else {
      toWarehouse.value = defaultTo
    }
  }
}

async function fetchRecentTransfers() {
  sidebarLoading.value = true
  recentTransfers.value = await frappePost('ssplbilling.api.storetransfer_api.get_recent_transfers', { date: sidebarDate.value })
  sidebarLoading.value = false
}

function focusBarcodeInput() {
  selectedRowIdx.value = -1
  exitEditMode()
  nextTick(() => barcodeInput.value?.focus())
}

function focusFromWarehouse() {
  nextTick(() => fromWarehouseInput.value?.focus())
}

function focusToWarehouse() {
  nextTick(() => toWarehouseInput.value?.focus())
}

function focusRow(idx) {
  selectedRowIdx.value = idx
  nextTick(() => {
    const el = rowRefs.value[idx]
    if (el) {
      el.focus()
      el.scrollIntoView({ block: 'nearest' })
    }
  })
}

function format(val) {
  if (val === null || val === undefined || val === '') return '0.00'
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

function focusEditField(field, idx) {
  editingRowIdx.value = idx
  editingField.value = field
  selectedRowIdx.value = idx
  nextTick(() => {
    if (field === 'code') {
      editCodeInput.value?.focus()
      editCodeInput.value?.select()
    } else if (field === 'qty') {
      editQtyInput.value?.focus()
      editQtyInput.value?.select()
    }
  })
}

function exitEditMode() {
  editingRowIdx.value = -1
  editingField.value = null
}

async function getItemDetailsFromServer(code) {
  try {
    const res = await frappePost('ssplbilling.api.storetransfer_api.get_item_details', {
      item_code: code,
      warehouse: fromWarehouse.value
    })
    return res
  } catch (err) {
    console.error(err)
    return null
  }
}

function onEditCodeInput(rowIdx) {
  const code = (items.value[rowIdx]?.item_code || '').trim()
  if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = editCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

async function onEditCodeKeydown(e, idx) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Escape') {
      e.preventDefault()
      quickSearchResults.value = []
      return
    }
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    const code = (items.value[idx]?.item_code || '').trim()
    const res = await getItemDetailsFromServer(code)
    if (res && res.found) {
      items.value[idx].item_code = res.item_code
      items.value[idx].item_name = res.item_name
      items.value[idx].uom = res.uom
      items.value[idx].rate = res.rate || 0
      focusEditField('qty', idx)
    } else {
      focusEditField('qty', idx)
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode()
  }
}

function onEditQtyKeydown(e, idx) {
  if (e.key === 'Enter') {
    e.preventDefault()
    exitEditMode()
    if (idx < items.value.length - 1) {
      focusRow(idx + 1)
      nextTick(() => {
        focusEditField('code', idx + 1)
      })
    } else {
      focusBarcodeInput()
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode()
  }
}

function onBarcodeInput() {
  const code = barcodeQuery.value.trim()
  if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = barcodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

function handleBarcodeKeydown(e) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === 'Escape') {
      if (e.key === 'Escape') {
        e.stopPropagation()
      }
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    }
  }

  if (e.key === 'Enter') {
    handleBarcodeEnter()
  } else if (e.key === 'ArrowUp') {
    if (items.value.length > 0) {
      e.preventDefault()
      focusRow(items.value.length - 1)
    }
  }
}

async function handleBarcodeEnter() {
  if (!barcodeQuery.value) return
  
  const code = barcodeQuery.value.trim()
  const res = await getItemDetailsFromServer(code)
  
  if (res && res.found) {
    setPendingItem(res)
    barcodeQuery.value = ''
    quickSearchResults.value = []
  } else {
    openItemSearch(barcodeQuery.value)
  }
}

function onQuickSearchRefresh() {
  // After cache refresh, re-run search if there's a query
  const query = (editingRowIdx.value !== -1 && editingField.value === 'code')
    ? (items.value[editingRowIdx.value]?.item_code || '')
    : barcodeQuery.value
  if (query) {
    quickSearchResults.value = searchItemsInCache(query)
  }
}

async function onQuickSearchSelect(item) {
  if (!item) return
  
  const res = await getItemDetailsFromServer(item.item_code)
  const finalItem = (res && res.found) ? res : item
  
  if (editingRowIdx.value !== -1) {
    const idx = editingRowIdx.value
    items.value[idx].item_code = finalItem.item_code
    items.value[idx].item_name = finalItem.item_name
    items.value[idx].uom = finalItem.uom || finalItem.stock_uom || 'Nos'
    items.value[idx].rate = finalItem.rate || finalItem.valuation_rate || 0
    quickSearchResults.value = []
    focusEditField('qty', idx)
  } else {
    setPendingItem(finalItem)
    barcodeQuery.value = ''
    quickSearchResults.value = []
  }
}

function openItemSearch(query) {
  itemSearchInitialQuery.value = query || ''
  showItemSearch.value = true
}

async function handleItemSelect(item) {
  const res = await getItemDetailsFromServer(item.item_code)
  if (res && res.found) {
    setPendingItem(res)
  } else {
    setPendingItem(item)
  }
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
    rate: details.rate || details.valuation_rate || 0
  }
  nextTick(() => {
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  })
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value
  
  const existing = items.value.find(i => i.item_code === p.item_code)
  if (existing) {
    existing.qty += p.qty
  } else {
    items.value.push({
      item_code: p.item_code,
      item_name: p.item_name,
      qty: p.qty,
      uom: p.uom,
      rate: p.rate || 0
    })
  }
  
  pendingItem.value = null
  focusBarcodeInput()
}

function handlePendingQtyKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    confirmPendingItem()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    pendingItem.value = null
    focusBarcodeInput()
  }
}

function removeItem(index) {
  items.value.splice(index, 1)
}

function handleRowKeydown(e, idx) {
  if (isReadOnly.value) return
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (idx < items.value.length - 1) {
      focusRow(idx + 1)
    } else {
      focusBarcodeInput()
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (idx > 0) {
      focusRow(idx - 1)
    }
  } else if (e.key === 'Enter') {
    e.preventDefault()
    focusEditField('code', idx)
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
  if (fromWarehouse.value === toWarehouse.value) { alert('Source and Destination warehouses must be different'); return }

  submitting.value = true
  try {
    const res = await frappePost('ssplbilling.api.storetransfer_api.save_store_transfer', {
      data: {
        company: localStorage.getItem('wb-company') || null,
        name: transferName.value || undefined,
        naming_series: selectedSeries.value,
        posting_date: transferDate.value,
        from_warehouse: fromWarehouse.value,
        to_warehouse: toWarehouse.value,
        items: items.value
      }
    })
    
    transferNo.value = res.name
    transferName.value = res.name
    isReadOnly.value = true
    isDraft.value = true
    await fetchRecentTransfers()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}

async function handleSubmit() {
  if (!transferName.value) return
  try {
    await frappePost('ssplbilling.api.storetransfer_api.submit_store_transfer', { name: transferName.value })
    isDraft.value = false
    await fetchRecentTransfers()
  } catch (err) {
    console.error(err)
  }
}

function resetForm() {
  transferNo.value = ''
  transferName.value = ''
  items.value = []
  if (availableSeries.value.length) selectedSeries.value = availableSeries.value[0]
  isReadOnly.value = false
  isDraft.value = false
  selectedRowIdx.value = -1
  exitEditMode()
  focusFromWarehouse()
}

function goBack() {
  router.push('/')
}

function handleBack() {
  if (!isReadOnly.value && items.value.length > 0) {
    showExitWarning.value = true
  } else {
    goBack()
  }
}

function handleJump(targetNo) {
  if (items.value.length === 0) return
  let idx = Math.max(0, Math.min(targetNo - 1, items.value.length - 1))
  focusRow(idx)
}

function handleSidebarDateChange(dir) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + dir)
  sidebarDate.value = d.toISOString().split('T')[0]
  fetchRecentTransfers()
}

function handleDocDateChange(dir) {
  const d = new Date(transferDate.value)
  d.setDate(d.getDate() + dir)
  transferDate.value = d.toISOString().split('T')[0]
}

async function handleSelectSidebarItem(item) {
  const details = await frappePost('ssplbilling.api.storetransfer_api.get_store_transfer_details', { name: item.name })
  transferNo.value = details.name
  transferName.value = details.name
  transferDate.value = details.posting_date
  fromWarehouse.value = details.from_warehouse
  toWarehouse.value = details.to_warehouse
  selectedSeries.value = details.naming_series
  items.value = details.items.map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    qty: i.qty,
    uom: i.uom,
    rate: i.basic_rate
  }))
  isReadOnly.value = true
  isDraft.value = details.docstatus === 0
  selectedRowIdx.value = -1
  exitEditMode()
}

function formatDate(dateString) {
  if (!dateString) return ''
  const d = new Date(dateString)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

function handlePrint() {
  if (!transferNo.value) {
    alert('Please save the transfer first.')
    return
  }
  showPrintModal.value = true
}

function closePrintModal() {
  showPrintModal.value = false
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
