<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-[var(--color-bg)]' : 'h-screen bg-[var(--color-bg)]'" class="overflow-hidden">
    <Stock_Template
      ref="invoiceTemplateRef"
      title="STOCK RECONCILIATION"
      title-bar-color="#ed8936"
      :doc-number="entryName"
      :doc-date="entryDate"
      :items="items"
      :total-amount="adjustedCount"
      :total-label="'Adjusted Items'"
      :show-total-currency="false"
      :item-count="items.length"
      :sidebar-date="sidebarDate"
      :sidebar-items="sidebarEntries"
      :sidebar-search="sidebarSearch"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      :is-draft="isDraft"
      :show-bottom-left="true"
      :show-bottom-middle="false"
      :show-print-button="false"
      @sidebar-date-change="changeSidebarDate"
      @doc-date-change="changeDate"
      @update:sidebarSearch="sidebarSearch = $event"
      @toggle-draft-only="draftOnly = !draftOnly"
      @select-sidebar-item="loadEntry($event.name)"
      @back="handleBack"
      @save="handleSave"
      @submit="submitEntry"
      @cancel="startNewEntry"
      :selected-sidebar-item-name="entryName"
    >
      <template #header-right>
        <!-- Zoom controls -->
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
        <span class="mr-3 text-lg"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-sm text-[var(--color-text)]">F7</kbd> Fetch</span>
        <span class="mr-3 text-lg"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-sm text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span class="text-lg"><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-sm text-[var(--color-text)]">Esc</kbd> Back</span>
      </template>

      <template #header-bar>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-6">
            <div v-if="entryName" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
              <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ entryName }}</div>
            </div>

            <div class="flex-1 flex items-center gap-8">
              <div class="flex flex-col gap-1">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Purpose</label>
                <select
                  v-model="purpose"
                  :disabled="isReadOnly || items.length > 0"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)]"
                >
                  <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
                </select>
              </div>

              <div class="flex flex-col gap-1 border-l border-[var(--color-border)] pl-8">
                <label class="text-sm font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
                <select
                  ref="warehouseSelect"
                  v-model="warehouse"
                  :disabled="isReadOnly || items.length > 0"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[250px]"
                >
                  <option value="">-- Select Warehouse --</option>
                  <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
                </select>
              </div>

              <button 
                @click="fetchItems" 
                :disabled="!warehouse || isReadOnly || items.length > 0"
                class="rounded bg-[var(--color-info)] px-4 py-2 text-2xl font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)] transition self-end ml-4"
              >
                Fetch Items (F7)
              </button>
            </div>

            <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Posting Date</label>
              <div class="flex items-center gap-1">
                <button @click="changeDate(-1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center disabled:opacity-30">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(entryDate) }}</div>
                <button @click="changeDate(1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center disabled:opacity-30">&rarr;</button>
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
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Curr Qty</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">New Qty</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Curr Rate</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">New Rate</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-20">UOM</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">Diff</th>
          <th class="border-b border-[var(--color-border)] w-12"></th>
        </tr>
      </template>

      <template #row="{ item, index }">
        <tr
          :ref="el => setRowRef(el, index)"
          tabindex="-1"
          class="group border-b border-[var(--color-border)] last:border-0 outline-none transition-colors"
          :class="{ 'bg-[var(--color-info)]/30': selectedRow === index, 'hover:bg-[var(--color-surface)]/40': selectedRow !== index }"
          :style="{ fontSize: dynamicRowStyle.fontSize }"
          @click="selectRow(index)"
          @keydown="onRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] font-mono text-3xl text-center">{{ index + 1 }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <span class="font-mono font-semibold text-[var(--color-info)] text-4xl truncate block w-40" :title="item.item_code">{{ item.item_code }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <div class="text-[var(--color-text)] text-4xl font-medium truncate max-w-[200px]" :title="item.item_name">{{ item.item_name || '--' }}</div>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-[var(--color-text-muted)] text-4xl">
            {{ item.current_qty }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right font-mono">
            <input
              :ref="el => setRef(el, 'qty', index)"
              type="number"
              v-model.number="item.qty"
              :disabled="isReadOnly"
              step="any"
              class="w-full bg-transparent px-2 py-1 text-right text-[var(--color-text)] font-bold outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl"
              @keydown.enter.prevent="focusField('rate', index)"
              @keydown.tab.prevent="focusField('rate', index)"
              @keydown.down.prevent="moveRow(index, 1)"
              @keydown.up.prevent="moveRow(index, -1)"
            />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-[var(--color-text-muted)] text-4xl">
            {{ item.current_valuation_rate?.toFixed(2) }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right font-mono">
            <input
              :ref="el => setRef(el, 'rate', index)"
              type="number"
              v-model.number="item.valuation_rate"
              :disabled="isReadOnly"
              step="any"
              class="w-full px-2 py-1 text-right font-bold text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl"
              :class="item.qty > 0 && item.current_qty === 0 && !(item.valuation_rate > 0) && !(item.current_valuation_rate > 0)
                ? 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'
                : 'bg-transparent'"
              @keydown.enter.prevent="moveRow(index, 1)"
              @keydown.tab.prevent="moveRow(index, 1)"
              @keydown.down.prevent="moveRow(index, 1)"
              @keydown.up.prevent="moveRow(index, -1)"
            />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-4xl">{{ item.uom || '--' }}</td>
          <td
            class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono font-bold text-4xl"
            :class="(item.qty - item.current_qty) > 0 ? 'text-[var(--color-success)]' : (item.qty - item.current_qty) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'"
          >
            {{ (item.qty - item.current_qty).toFixed(2) }}
          </td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] transition" @click.stop="removeItem(index)">&times;</button>
          </td>
        </tr>
      </template>

      <template #table-extra-rows>
        <tr v-if="!isReadOnly" class="border-b border-[var(--color-border)] bg-[var(--color-info)]/10" :class="{ 'bg-[var(--color-info)]/30 ring-2 ring-inset ring-[var(--color-info)]': selectedRow === -1 }" :style="{ fontSize: dynamicRowStyle.fontSize }">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-info)] font-bold text-3xl text-center">+</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm text-4xl" placeholder="Item code" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <div class="text-[var(--color-text-muted)] italic truncate max-w-[200px] text-4xl">{{ newPending.item_name || 'Search...' }}</div>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right text-[var(--color-text-muted)] font-mono text-4xl">
            {{ newPending.current_qty }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right">
            <input ref="newQtyInput" v-model.number="newQty" type="number" step="any" class="w-full bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl" @keydown.enter.prevent="focusNewRate" @keydown.tab.prevent="focusNewRate" />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right text-[var(--color-text-muted)] font-mono text-4xl">
            {{ newPending.valuation_rate?.toFixed(2) }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right">
            <input ref="newRateInput" v-model.number="newRate" type="number" step="any" class="w-full bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl" @keydown.enter.prevent="addNewItem" />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-4xl">{{ newPending.uom || '--' }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono font-bold text-4xl" :class="(newQty - newPending.current_qty) > 0 ? 'text-[var(--color-success)]' : (newQty - newPending.current_qty) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
            {{ (newQty - newPending.current_qty).toFixed(2) }}
          </td>
          <td class="px-2 py-1"></td>
        </tr>
      </template>

      <template #bottom-left>
        <div class="flex flex-col gap-2 p-4 h-[120px] overflow-y-auto">
           <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Instructions</div>
           <ul class="text-xs text-[var(--color-text-muted)] list-disc list-inside space-y-1">
             <li>Select warehouse and fetch items to see current stock.</li>
             <li>Update the <span class="text-[var(--color-info)] font-bold">Target Qty</span> for items you want to reconcile.</li>
             <li>Items with Difference = 0 will be ignored on submit.</li>
             <li>Save as Draft first, then Submit to apply changes.</li>
           </ul>
        </div>
      </template>
    </Stock_Template>
  </div>

  <!-- Item Search Modal -->
  <ItemSearch
    v-if="showItemSearch"
    :show="showItemSearch"
    search-type="Sales"
    :warehouse="warehouse"
    :initial-query="newItemCode"
    :skip-date-filter="true"
    @close="showItemSearch = false; nextTick(() => focusNewCode())"
    @select="onItemSearchSelect"
  />
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { stockReconciliationShortcuts } from '../shortcuts/stockReconciliationShortcuts'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import ItemSearch from '../components/ItemSearch.vue'
import Stock_Template from '../components/Stock_Template.vue'

const router = useRouter()
const API = 'ssplbilling.api.stock_reconciliation_api'
const { allowedSeries: availableSeries, fetchAllowedSeries } = useAllowedSeries()

const props = defineProps({
  isSubWindow: Boolean,
  name: String
})
const emit = defineEmits(['close'])

if (props.isSubWindow) useSubwindow()

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const warehouse = ref('')
const purpose = ref('Stock Reconciliation')
const entryName = ref(null)
const entryDocStatus = ref(0)
const submitting = ref(false)
const entryDate = ref(new Date().toISOString().split('T')[0])
const availableWarehouses = ref([])
const availablePurposes = ref(['Stock Reconciliation', 'Opening Stock'])
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

const isReadOnly = ref(false)
const isDraft = ref(false)

// New entry state
const newItemCode = ref('')
const newQty = ref(0)
const newRate = ref(0)
const newPending = ref({ item_name: '', uom: '', current_qty: 0, valuation_rate: 0 })
const showItemSearch = ref(false)

// Sidebar state
const sidebarDate = ref(new Date().toISOString().split('T')[0])
const sidebarSearch = ref('')
const sidebarEntries = ref([])
const sidebarLoading = ref(false)
const draftOnly = ref(true)
const sidebarEntryRefs = new Map()

const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`
}))

const adjustedCount = computed(() => items.value.filter(i => Math.abs(i.qty - i.current_qty) > 0.0001).length)

const saveButtonText = computed(() => {
  if (isReadOnly.value && !isDraft.value) return 'New'
  if (isReadOnly.value && isDraft.value) return 'Edit'
  return 'Save'
})

// ==================== REFS & FOCUS ====================
const inputRefs = {}
const rowRefs = {}
const warehouseSelect = ref(null)
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const newRateInput = ref(null)

function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarEntryRef(el, idx) { if (el) sidebarEntryRefs.set(idx, el); else sidebarEntryRefs.delete(idx) }

function focusField(f, idx) { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusWarehouse() { nextTick(() => warehouseSelect.value?.focus()) }
function focusNewCode()   { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty()    { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }
function focusNewRate()   { nextTick(() => { newRateInput.value?.focus(); newRateInput.value?.select() }) }

function navigateSidebarEntry(idx, dir) {
  const target = sidebarEntryRefs.get(idx + dir)
  if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }) }
}

function changeSidebarDate(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

function changeDate(dir) {
  const d = new Date(entryDate.value)
  d.setDate(d.getDate() + dir)
  entryDate.value = d.toISOString().split('T')[0]
}

function formatDate(dateString) {
  if (!dateString) return ''
  const d = new Date(dateString)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

// ==================== NAVIGATION ====================
function moveRow(from, dir) { 
  let n = from + dir
  if (n >= 0 && n < items.value.length) { 
    selectedRow.value = n; 
    focusField('qty', n) 
    rowRefs[n]?.scrollIntoView({ block: 'nearest' })
  } 
}
function selectRow(idx) { selectedRow.value = idx; focusField('qty', idx) }

function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
}

// ==================== DATA FETCHING ====================
async function fetchConfig() {
  try {
    const whs = await frappeGet('frappe.client.get_list', {
      doctype: 'Warehouse',
      filters: { is_group: 0, disabled: 0 },
      fields: ['name'],
      limit: 1000,
      order_by: 'name asc'
    })
    availableWarehouses.value = whs.map(w => w.name)
    if (!warehouse.value && availableWarehouses.value.length) {
       warehouse.value = availableWarehouses.value[0]
    }

    const purposes = await frappeGet(`${API}.get_stock_reconciliation_purposes`)
    if (purposes && purposes.length) {
      availablePurposes.value = purposes
    }
  } catch (e) { console.error('Failed to fetch config', e) }
}

async function fetchItems() {
  if (!warehouse.value) return
  try {
    const res = await frappeGet(`${API}.get_items_for_reconciliation`, { warehouse: warehouse.value })
    items.value = res
    if (items.value.length) {
      selectedRow.value = 0
      nextTick(() => focusField('qty', 0))
    }
  } catch (e) { alert(e.message || 'Fetch failed') }
}

async function lookupItem(code) {
  try {
    return await frappePost(`ssplbilling.api.storetransfer_api.get_item_details`, { item_code: code, warehouse: warehouse.value })
  } catch (e) { return null }
}

let itemLookupTimeout = null
watch(newItemCode, (val) => {
  const code = val.trim()
  clearTimeout(itemLookupTimeout)
  if (code.length < 2) {
    newPending.value = { item_name: '', uom: '', current_qty: 0, valuation_rate: 0 }
    return
  }
  itemLookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    if (r && r.found) {
      newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.rate }
      newQty.value = r.stock_qty
      newRate.value = r.rate
    }
  }, 300)
})

async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.rate }
    newQty.value = r.stock_qty
    newRate.value = r.rate
    focusNewQty()
  } else {
    showItemSearch.value = true
  }
}

async function onItemSearchSelect(item) {
  showItemSearch.value = false
  newItemCode.value = item.item_code
  const r = await lookupItem(item.item_code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.rate }
    newQty.value = r.stock_qty
    newRate.value = r.rate
  } else {
    newPending.value = { item_name: item.item_name, uom: item.uom || '', current_qty: 0, valuation_rate: 0 }
    newQty.value = 0
    newRate.value = 0
  }
  nextTick(() => focusNewQty())
}

function addNewItem() {
  if (!newItemCode.value || !newPending.value.item_name) return
  
  const existing = items.value.find(i => i.item_code === newItemCode.value)
  if (existing) {
    alert('Item already in list')
    newItemCode.value = ''
    return
  }

  items.value.push({
    item_code: newItemCode.value,
    item_name: newPending.value.item_name,
    uom: newPending.value.uom,
    current_qty: newPending.value.current_qty,
    qty: newQty.value,
    valuation_rate: newRate.value || newPending.value.valuation_rate,
    current_valuation_rate: newPending.value.valuation_rate
  })

  newItemCode.value = ''
  newQty.value = 0
  newRate.value = 0
  newPending.value = { item_name: '', uom: '', current_qty: 0, valuation_rate: 0 }
  focusNewCode()
}

async function fetchSidebarEntries() {
  sidebarLoading.value = true
  try {
    const params = {
      posting_date: sidebarSearch.value ? null : sidebarDate.value,
      query: sidebarSearch.value,
    }
    if (draftOnly.value) params.docstatus = 0
    
    sidebarEntries.value = await frappeGet(`${API}.get_stock_reconciliations`, params)
  } catch (e) {}
  sidebarLoading.value = false
}

watch([sidebarDate, draftOnly], () => fetchSidebarEntries())

let searchTimeout = null
watch(sidebarSearch, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(fetchSidebarEntries, 300)
})

// ==================== ACTIONS ====================
function removeItem(idx) {
  items.value.splice(idx, 1)
  if (selectedRow.value >= items.value.length) selectedRow.value = items.value.length - 1
}

async function handleSave() {
  if (submitting.value) return
  if (isReadOnly.value && !isDraft.value) {
    startNewEntry()
    return
  }
  if (isReadOnly.value && isDraft.value) {
    isReadOnly.value = false
    return
  }
  await saveEntry()
}

async function saveEntry() {
  if (submitting.value) return
  if (!warehouse.value) { alert('Select warehouse'); return }
  if (!items.value.length) { alert('No items to save'); return }

  const payload = {
    name: entryName.value,
    posting_date: entryDate.value,
    purpose: purpose.value,
    warehouse: warehouse.value,
    items: items.value.filter(i => Math.abs(i.qty - i.current_qty) > 0.0001).map(i => ({
      item_code: i.item_code,
      warehouse: i.warehouse || warehouse.value,
      qty: i.qty,
      valuation_rate: i.valuation_rate || i.current_valuation_rate
    }))
  }

  if (payload.items.length === 0) {
    if (!confirm('No items have been adjusted. Save anyway?')) return
  }

  submitting.value = true
  try {
    const method = entryName.value ? 'update_stock_reconciliation' : 'create_stock_reconciliation'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    entryName.value = res.name
    entryDocStatus.value = 0
    isReadOnly.value = true
    isDraft.value = true
    alert(`Entry ${res.name} saved as Draft`)
    fetchSidebarEntries()
  } catch (e) { alert(e.message || 'Save failed') }
  finally {
    submitting.value = false
  }
}

async function submitEntry() {
  if (!entryName.value) return

  const needsRate = items.value.filter(
    i => i.qty > 0 && i.current_qty === 0 && !(i.valuation_rate > 0) && !(i.current_valuation_rate > 0)
  )
  if (needsRate.length) {
    alert(
      `Valuation Rate required for the following item(s) that have no current stock:\n\n` +
      needsRate.map(i => `  • ${i.item_code} – ${i.item_name}`).join('\n') +
      `\n\nPlease enter a value in the "New Rate" column before submitting.`
    )
    return
  }

  if (!confirm('SUBMIT reconciliation? This updates stock levels immediately.')) return

  try {
    await frappePost(`${API}.submit_stock_reconciliation`, { name: entryName.value })
    alert(`Reconciliation ${entryName.value} submitted successfully`)
    entryDocStatus.value = 1
    isDraft.value = false
    isReadOnly.value = true
    fetchSidebarEntries()
  } catch (e) { alert(e.message || 'Submission failed') }
}

function startNewEntry() {
  items.value = []; entryName.value = null; entryDocStatus.value = 0
  isReadOnly.value = false
  isDraft.value = false
  selectedRow.value = -1
}

// ==================== MODIFY HISTORY ====================
async function loadEntry(name) {
  try {
    const data = await frappeGet(`${API}.get_stock_reconciliation`, { name })
    entryName.value = data.name
    entryDate.value = data.posting_date
    purpose.value = data.purpose || 'Stock Reconciliation'
    warehouse.value = data.items.length ? (data.items[0].warehouse || '') : ''
    items.value = data.items
    entryDocStatus.value = data.docstatus
    isReadOnly.value = true
    isDraft.value = data.docstatus === 0
  } catch (e) { 
    console.error('Load failed', e)
    alert('Load failed: ' + (e.message || 'Unknown error')) 
  }
}

// ==================== SHORTCUTS ====================
function handleBack() {
  if (items.value.length && !entryName.value) {
    if (!confirm('Discard unsaved reconciliation?')) return
  }
  router.push('/')
}

useShortcuts(stockReconciliationShortcuts({
  save: handleSave,
  fetchItems: fetchItems,
  focusWarehouse: focusWarehouse,
  contextualBack: () => {
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

onMounted(() => {
  fetchAllowedSeries('Stock Reconciliation')
  fetchConfig()
  fetchSidebarEntries()
  if (props.name) loadEntry(props.name)
})
</script>
