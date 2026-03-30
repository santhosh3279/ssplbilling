<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'h-screen bg-slate-900'" class="flex">
    <!-- ===================== SIDEBAR / MODIFY PANEL ===================== -->
    <aside class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Modify Entries</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-slate-700 p-1.5 bg-slate-900">
          <button @click="changeSidebarDate(-1)" class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300">&larr;</button>
          <input 
            type="date" 
            v-model="sidebarDate"
            class="w-full bg-transparent text-xs font-bold text-slate-300 outline-none"
          />
          <button @click="changeSidebarDate(1)" class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300">&rarr;</button>
        </div>

        <!-- Search & Status Filters -->
        <div class="flex flex-col gap-1.5 border-b border-slate-700 p-2 bg-slate-800/20">
          <input 
            type="text" 
            v-model="sidebarSearch"
            placeholder="Search ID..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 outline-none focus:border-blue-500"
          />
          <button
            @click="draftOnly = !draftOnly"
            class="w-full rounded border py-1 text-[10px] font-bold uppercase transition-colors"
            :class="draftOnly ? 'bg-amber-900/40 border-amber-500 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Entries' }}
          </button>
        </div>

        <!-- Entry List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="sidebarLoading" class="p-4 text-center text-xs text-slate-500">Loading...</div>
          <div v-else-if="!sidebarEntries.length" class="p-4 text-center text-xs text-slate-600 italic">No entries found</div>
          <div 
            v-for="(ent, idx) in sidebarEntries" 
            :key="ent.name"
            :ref="el => setSidebarEntryRef(el, idx)"
            @click="loadEntry(ent.name)"
            class="group cursor-pointer border-b border-slate-800 bg-slate-900 px-2 py-1 transition-colors hover:bg-slate-800 outline-none focus:bg-slate-800 focus:ring-1 focus:ring-blue-500"
            :class="{ 'bg-slate-800 border-l-2 border-l-blue-500': entryName === ent.name }"
            tabindex="0"
            @keydown.enter="loadEntry(ent.name)"
            @keydown.up.prevent="navigateSidebarEntry(idx, -1)"
            @keydown.down.prevent="navigateSidebarEntry(idx, 1)"
          >
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-1.5 truncate min-w-0">
                <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="ent.docstatus === 0 ? 'bg-amber-500' : 'bg-green-500'"></span>
                <span class="truncate font-mono text-[14px] font-bold text-blue-400">{{ ent.name }}</span>
              </div>
              <span class="shrink-0 text-[10px] font-bold text-slate-500 uppercase tabular-nums">{{ ent.modified?.split(' ')[1]?.slice(0,5) }}</span>
            </div>
            <div class="truncate text-[10px] text-slate-400 uppercase tracking-tight">{{ ent.company }}</div>
          </div>
        </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <div class="flex flex-1 flex-col overflow-hidden">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-4 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700 transition" @click="handleBack">&larr; Dashboard</button>
        <span class="text-sm text-slate-600">|</span>
        <span class="text-sm font-bold text-slate-100 uppercase tracking-tight">Stock Reconciliation</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-slate-400">
        <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-slate-700 bg-slate-800 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-slate-500 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-slate-300 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
        </div>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">F7</kbd> Fetch</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="border-b border-slate-700 bg-slate-800 px-4 py-3">
      <div class="flex items-center gap-8">
        <!-- Purpose -->
        <div class="flex items-center gap-2">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">Purpose</label>
          <select
            v-model="purpose"
            :disabled="entryDocStatus !== 0 || items.length > 0"
            class="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm font-bold text-indigo-400 outline-none focus:border-indigo-500 disabled:bg-slate-900 disabled:text-slate-500 min-w-[150px]"
          >
            <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <!-- Warehouse -->
        <div class="flex items-center gap-2 border-l border-slate-700 pl-8">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">Warehouse</label>
          <select
            ref="warehouseSelect"
            v-model="warehouse"
            :disabled="entryDocStatus !== 0 || items.length > 0"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-1.5 text-lg font-bold text-blue-400 outline-none focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500 min-w-[250px]"
          >
            <option value="">-- Select Warehouse --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <button 
          @click="fetchItems" 
          :disabled="!warehouse || entryDocStatus !== 0 || items.length > 0"
          class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700 disabled:bg-slate-700 disabled:text-slate-500 transition"
        >
          Fetch Items (F7)
        </button>

        <!-- Date -->
        <div class="flex items-center gap-3 border-l border-slate-800 pl-8 ml-auto">
          <label class="text-[10px] font-bold uppercase text-slate-400">Date</label>
          <input
            v-model="entryDate"
            type="date"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-lg font-bold text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500 tabular-nums"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-1 overflow-hidden bg-slate-900">
      <!-- MAIN CONTENT -->
      <div class="flex w-full flex-col p-4 overflow-hidden">
        <div class="flex-1 overflow-hidden rounded-xl border border-slate-700 bg-slate-800 shadow-sm flex flex-col">
          <div class="flex-1 overflow-y-auto" ref="tableContainer">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
                  <th class="w-12 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">#</th>
                  <th class="w-48 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Code</th>
                  <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Name</th>
                  <th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Current Qty</th>
                  <th class="w-32 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Target Qty</th>
                  <th class="w-20 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">UOM</th>
                  <th class="w-32 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Difference</th>
                  <th class="w-12 px-4 py-3 text-center"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="group border-b border-slate-700 last:border-0 outline-none transition-colors" :class="{ 'bg-blue-900/30': selectedRow === idx, 'hover:bg-slate-800/40': selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-4 py-2 text-slate-500 font-mono">{{ idx + 1 }}</td>
                  <td class="px-4 py-2">
                    <span class="font-mono font-semibold text-blue-400" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-4 py-2">
                    <div class="text-slate-200 font-medium" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</div>
                  </td>
                  <td class="px-4 py-2 text-right font-mono text-slate-400">
                    {{ item.current_qty }}
                  </td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="entryDocStatus !== 0" step="any" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-slate-200 focus:border-blue-400 focus:bg-slate-800 outline-none disabled:text-slate-500 font-bold" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="moveRow(idx, 1)" @keydown.tab.prevent="moveRow(idx, 1)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                  </td>
                  <td class="px-4 py-2 text-slate-500" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-4 py-2 text-right font-mono font-bold" :class="(item.qty - item.current_qty) > 0 ? 'text-green-400' : (item.qty - item.current_qty) < 0 ? 'text-red-400' : 'text-slate-500'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                    {{ (item.qty - item.current_qty).toFixed(3) }}
                  </td>
                  <td class="px-4 py-2 text-center">
                    <button class="rounded p-1 text-slate-600 hover:bg-red-900/20 hover:text-red-400 opacity-0 group-hover:opacity-100 transition" @click.stop="removeItem(idx)">&times;</button>
                  </td>
                </tr>
                <tr v-if="items.length === 0" class="h-32 text-center text-slate-600 italic">
                  <td colspan="8">Select a warehouse and click "Fetch Items" to start.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TABLE FOOTER -->
          <div class="flex items-center justify-between border-t border-slate-700 bg-slate-800 px-6 py-2.5">
            <div class="flex gap-8 items-center text-xs font-bold text-slate-500 uppercase tracking-widest">
              <span>Total Items: {{ items.length }}</span>
              <span>Adjusted: {{ adjustedCount }}</span>
            </div>
          </div>
        </div>

        <!-- BOTTOM PANEL -->
        <div class="mt-4 flex gap-4 h-[120px]">
          <div class="flex-[3] rounded-xl border border-slate-700 bg-slate-800 p-4 shadow-sm overflow-y-auto">
             <div class="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Instructions</div>
             <ul class="text-xs text-slate-400 list-disc list-inside space-y-1">
               <li>Select warehouse and fetch items to see current stock.</li>
               <li>Update the <span class="text-blue-400 font-bold">Target Qty</span> for items you want to reconcile.</li>
               <li>Items with Difference = 0 will be ignored on submit.</li>
               <li>Save as Draft first, then Submit to apply changes.</li>
             </ul>
          </div>

          <!-- Actions -->
          <div class="flex-[1] flex flex-col gap-2">
            <button
              ref="saveButton"
              @click="saveEntry"
              :disabled="entryDocStatus !== 0 || items.length === 0"
              class="flex-1 rounded-xl bg-blue-600 text-lg font-bold text-white shadow-lg hover:bg-blue-700 active:scale-95 transition-all disabled:bg-slate-700 disabled:text-slate-500"
            >
              {{ entryName ? 'Update Draft' : 'Save Draft (Ctrl+S)' }}
            </button>
            <button
              v-if="entryName && entryDocStatus === 0"
              @click="submitEntry"
              class="h-12 rounded-xl bg-green-600 text-sm font-bold text-white shadow-lg hover:bg-green-700 active:scale-95 transition-all"
            >
              Submit / Apply Changes
            </button>
            <div class="flex gap-2 h-10">
              <button @click="startNewEntry" class="flex-1 rounded-xl border border-slate-700 bg-slate-800 text-xs font-bold text-slate-300 hover:bg-slate-700 transition">Clear All</button>
              <button @click="handleBack" class="flex-1 rounded-xl border border-red-800 bg-red-900/20 text-xs font-bold text-red-400 hover:bg-red-900/40 transition">Exit</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { stockReconciliationShortcuts } from '../shortcuts/stockReconciliationShortcuts'

const router = useRouter()
const API = 'ssplbilling.api.stock_reconciliation_api'

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
const entryDate = ref(new Date().toISOString().split('T')[0])
const availableWarehouses = ref([])
const availablePurposes = ref(['Stock Reconciliation', 'Opening Stock'])
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

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

// ==================== REFS & FOCUS ====================
const inputRefs = {}
const rowRefs = {}
const warehouseSelect = ref(null)
const saveButton = ref(null)

function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarEntryRef(el, idx) { if (el) sidebarEntryRefs.set(idx, el); else sidebarEntryRefs.delete(idx) }

function focusField(f, idx) { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusWarehouse() { nextTick(() => warehouseSelect.value?.focus()) }

function navigateSidebarEntry(idx, dir) {
  const target = sidebarEntryRefs.get(idx + dir)
  if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }) }
}

function changeSidebarDate(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

// ==================== NAVIGATION ====================
function moveRow(from, dir) { 
  let n = from + dir
  if (n >= 0 && n < items.value.length) { 
    selectedRow.value = n; 
    focusField('qty', n) 
    // Scroll into view if needed
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

async function fetchSidebarEntries() {
  sidebarLoading.value = true
  try {
    sidebarEntries.value = await frappeGet(`${API}.get_stock_reconciliations`, {
      posting_date: sidebarSearch.value ? null : sidebarDate.value,
      query: sidebarSearch.value,
      docstatus: draftOnly.value ? 0 : null
    })
  } catch (e) {}
  sidebarLoading.value = false
}

watch([sidebarDate, sidebarSearch, draftOnly], () => fetchSidebarEntries())

// ==================== ACTIONS ====================
function removeItem(idx) {
  items.value.splice(idx, 1)
  if (selectedRow.value >= items.value.length) selectedRow.value = items.value.length - 1
}

async function saveEntry() {
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
      valuation_rate: i.current_valuation_rate
    }))
  }

  if (payload.items.length === 0) {
    if (!confirm('No items have been adjusted. Save anyway?')) return
  }

  try {
    const method = entryName.value ? 'update_stock_reconciliation' : 'create_stock_reconciliation'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    entryName.value = res.name
    alert(`Entry ${res.name} saved as Draft`)
    fetchSidebarEntries()
  } catch (e) { alert(e.message || 'Save failed') }
}

async function submitEntry() {
  if (!entryName.value) return
  if (!confirm('SUBMIT reconciliation? This updates stock levels immediately.')) return

  try {
    await frappePost(`${API}.submit_stock_reconciliation`, { name: entryName.value })
    alert(`Reconciliation ${entryName.value} submitted successfully`)
    startNewEntry()
    fetchSidebarEntries()
  } catch (e) { alert(e.message || 'Submission failed') }
}

function startNewEntry() {
  items.value = []; entryName.value = null; entryDocStatus.value = 0
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
  save: saveEntry,
  fetchItems: fetchItems,
  focusWarehouse: focusWarehouse,
  contextualBack: () => {
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

onMounted(() => {
  fetchConfig()
  fetchSidebarEntries()
  if (props.name) loadEntry(props.name)
})
</script>
