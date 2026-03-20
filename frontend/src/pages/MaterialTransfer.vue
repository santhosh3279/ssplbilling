<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'h-screen flex flex-col'">
    <div class="flex h-full flex-col">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-4 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700 transition" @click="handleBack">&larr; Dashboard</button>
        <span class="text-sm text-slate-600">|</span>
        <span class="text-sm font-bold text-slate-100 uppercase tracking-tight">Material Transfer Entry</span>
        <button class="rounded border border-slate-600 px-2.5 py-1 text-sm text-slate-300 hover:bg-slate-700 transition" @click="openModifyEntry">Modify Entry</button>
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
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Up/Down</kbd> Navigate</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Tab</kbd> Next</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="border-b border-slate-700 bg-slate-800 px-4 py-3">
      <div class="flex items-center gap-8">
        <!-- Series -->
        <div class="flex items-center gap-2">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">Series</label>
          <select
            ref="seriesSelect"
            v-model="entrySeries"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm font-bold text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500"
          >
            <option v-for="s in availableSeries" :key="s">{{ s }}</option>
          </select>
        </div>

        <!-- Purpose -->
        <div class="flex items-center gap-2 border-l border-slate-800 pl-8">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">Type</label>
          <select
            v-model="purpose"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm font-bold text-blue-400 outline-none focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500 min-w-[150px]"
          >
            <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <!-- From Warehouse -->
        <div v-if="purpose !== 'Material Receipt'" class="flex items-center gap-2 border-l border-slate-800 pl-8">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">From</label>
          <select
            v-model="fromWarehouse"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-1.5 text-lg font-bold text-red-400 outline-none focus:border-red-500 disabled:bg-slate-900 disabled:text-slate-500 min-w-[200px]"
          >
            <option value="">-- Select Source --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <!-- Arrow -->
        <div v-if="purpose === 'Material Transfer'" class="text-2xl text-slate-600">➜</div>

        <!-- To Warehouse -->
        <div v-if="purpose !== 'Material Issue'" class="flex items-center gap-2" :class="{ 'border-l border-slate-800 pl-8': purpose === 'Material Receipt' }">
          <label class="text-[10px] font-bold uppercase text-slate-400 whitespace-nowrap">To</label>
          <select
            v-model="toWarehouse"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-1.5 text-lg font-bold text-green-400 outline-none focus:border-green-500 disabled:bg-slate-900 disabled:text-slate-500 min-w-[200px]"
          >
            <option value="">-- Select Target --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

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
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
                  <th class="w-12 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">#</th>
                  <th class="w-48 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Code</th>
                  <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Name</th>
                  <th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Qty</th>
                  <th class="w-20 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-400">UOM</th>
                  <th class="w-32 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Rate</th>
                  <th class="w-36 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Total Value</th>
                  <th class="w-12 px-4 py-3 text-center"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="group border-b border-slate-700 last:border-0 outline-none transition-colors" :class="{ 'bg-blue-900/30': selectedRow === idx && !item.deleted, 'bg-red-900/20': item.deleted, 'hover:bg-slate-800/40': !item.deleted && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-4 py-2 text-slate-500 font-mono">{{ idx + 1 }}</td>
                  <td class="px-4 py-2">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="entryDocStatus !== 0" class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 font-mono text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-900 disabled:text-slate-500" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono font-semibold" :class="item.deleted ? 'text-slate-600' : 'text-blue-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-4 py-2">
                    <div :class="item.deleted ? 'text-red-400 line-through' : 'text-slate-200 font-medium'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</div>
                  </td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="entryDocStatus !== 0" min="0.001" step="any" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-slate-200 focus:border-blue-400 focus:bg-slate-800 outline-none disabled:text-slate-500" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.qty }}</span>
                  </td>
                  <td class="px-4 py-2 text-slate-500" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="entryDocStatus !== 0" step="0.01" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-slate-200 focus:border-blue-400 focus:bg-slate-800 outline-none disabled:text-slate-500" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ (item.rate || 0).toFixed(2) }}</span>
                  </td>
                  <td class="px-4 py-2 text-right font-mono font-bold text-slate-100" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ (item.qty * item.rate).toFixed(2) }}</td>
                  <td class="px-4 py-2 text-center">
                    <button v-if="!item.deleted" class="rounded p-1 text-slate-600 hover:bg-red-900/20 hover:text-red-400 opacity-0 group-hover:opacity-100 transition" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else class="text-[10px] font-bold text-blue-400 hover:underline" @click.stop="restoreItem(idx)">RESTORE</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="entryDocStatus === 0" class="border-b border-slate-700 bg-blue-900/10" :class="{ 'bg-blue-900/30 ring-2 ring-inset ring-blue-500': selectedRow === -1 }" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-4 py-3 text-blue-400 font-bold">+</td>
                  <td class="px-4 py-3">
                    <input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 font-mono text-slate-200 outline-none focus:border-blue-500 shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Item code / Scan" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" />
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-slate-500 italic" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ newPending.item_name || 'Scan or type to find item...' }}</div>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <input ref="newQtyInput" v-model.number="newQty" type="number" min="0.001" step="any" class="w-24 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-right font-mono text-slate-200 outline-none focus:border-blue-500 shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="addNewItem" />
                  </td>
                  <td class="px-4 py-3 text-slate-500">{{ newPending.uom || '--' }}</td>
                  <td class="px-4 py-3 text-right text-slate-500 font-mono">{{ (newPending.rate || 0).toFixed(2) }}</td>
                  <td class="px-4 py-3 text-right text-slate-500 font-mono font-bold">{{ (newQty * (newPending.rate || 0)).toFixed(2) }}</td>
                  <td class="px-4 py-3"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TABLE FOOTER -->
          <div class="flex items-center justify-between border-t border-slate-700 bg-slate-800 px-6 py-2.5">
            <div class="flex gap-8 items-center text-xs font-bold text-slate-500 uppercase tracking-widest">
              <span>Total Items: {{ activeItems.length }}</span>
              <span v-if="deletedCount > 0" class="text-red-400">{{ deletedCount }} DELETED</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Transfer Total:</span>
              <span class="text-2xl font-mono font-black text-slate-100">₹{{ totalValue.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- BOTTOM PANEL: INSIGHT & ACTIONS -->
        <div class="mt-4 flex gap-4 h-[200px]">
          <!-- Item Insight -->
          <div class="flex-[3] rounded-xl border border-slate-700 bg-slate-800 p-4 shadow-sm overflow-y-auto">
            <div class="mb-3 text-[10px] font-black uppercase tracking-widest text-slate-500">Item Insight <span v-if="selectedItemData" class="ml-2 text-blue-400 font-mono">{{ selectedItemData.item_code }}</span></div>
            <template v-if="selectedItemData">
              <div class="flex gap-12">
                <div class="flex flex-col gap-3 min-w-[200px]">
                  <div class="flex items-center justify-between border-b border-slate-700 pb-1">
                    <span class="text-xs font-bold text-slate-400">From (Source)</span>
                    <span class="rounded bg-red-900/20 px-2 py-0.5 text-xs font-bold text-red-400 font-mono">{{ stockAtSource }} {{ selectedItemData.uom }}</span>
                  </div>
                  <div class="flex items-center justify-between border-b border-slate-700 pb-1">
                    <span class="text-xs font-bold text-slate-400">To (Target)</span>
                    <span class="rounded bg-green-900/20 px-2 py-0.5 text-xs font-bold text-green-400 font-mono">{{ stockAtTarget }} {{ selectedItemData.uom }}</span>
                  </div>
                </div>
                <div class="flex-1">
                  <div class="text-xs font-bold text-slate-400 mb-2">Valuation Details</div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-2xl font-mono font-bold text-slate-200">₹{{ (selectedItemData.valuation_rate || 0).toFixed(2) }}</span>
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Per {{ selectedItemData.uom }}</span>
                  </div>
                </div>
              </div>
            </template>
            <div v-else class="flex h-full items-center justify-center text-sm italic text-slate-600">
              Select an item to see real-time stock and valuation
            </div>
          </div>

          <!-- Actions -->
          <div class="flex-[1] flex flex-col gap-2">
            <button
              ref="saveButton"
              @click="saveEntry"
              :disabled="entryDocStatus !== 0"
              class="flex-1 rounded-xl bg-blue-600 text-lg font-bold text-white shadow-lg hover:bg-blue-700 active:scale-95 transition-all disabled:bg-slate-700 disabled:text-slate-500"
            >
              {{ entryName ? 'Update Entry' : 'Save Draft (Ctrl+S)' }}
            </button>
            <button
              v-if="entryName && entryDocStatus === 0"
              @click="submitEntry"
              class="h-12 rounded-xl bg-green-600 text-sm font-bold text-white shadow-lg hover:bg-green-700 active:scale-95 transition-all"
            >
              Submit / Post
            </button>
            <button
              v-if="entryName"
              @click="showIncentiveModal = true"
              class="h-10 rounded-xl border border-indigo-700 bg-indigo-900/20 text-sm font-semibold text-indigo-400 hover:bg-indigo-900/40 transition-all"
            >👥 Incentive</button>
            <div class="flex gap-2 h-14">
              <button @click="startNewEntry" class="flex-1 rounded-xl border border-slate-700 bg-slate-800 text-sm font-bold text-slate-300 hover:bg-slate-700 transition">Clear</button>
              <button @click="handleBack" class="flex-1 rounded-xl border border-red-800 bg-red-900/20 text-sm font-bold text-red-400 hover:bg-red-900/40 transition">Exit</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- INCENTIVE ENTRY MODAL -->
    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Stock Entry"
      :docname="entryName"
      @close="showIncentiveModal = false"
      @saved="showIncentiveModal = false"
    />

    <!-- =================== MODIFY SUBWINDOW =================== -->
    <div v-if="showModifyEntry" class="fixed inset-0 z-50 flex justify-center bg-black/80 backdrop-blur-sm pt-12" @click.self="showModifyEntry = false">
      <div class="flex max-h-[80vh] w-[700px] flex-col rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="border-b border-slate-700 px-6 py-5 bg-slate-800">
          <div class="text-lg font-bold text-slate-100">Draft Material Transfers</div>
          <div class="text-sm text-slate-400">Pick an entry to continue editing</div>
        </div>
        <div class="p-4 bg-slate-900 border-b border-slate-700">
          <input
            ref="modifySearchInput"
            v-model="modifyQuery"
            class="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-blue-500"
            placeholder="Search by entry name..."
          />
        </div>
        <div class="flex-1 overflow-y-auto">
          <div v-if="modifyLoading" class="p-10 text-center text-slate-500">Loading...</div>
          <table v-else-if="modifyResults.length" class="w-full text-sm">
            <thead class="bg-slate-800 text-slate-400 text-[10px] font-black uppercase tracking-widest border-b border-slate-700">
              <tr>
                <th class="px-6 py-3 text-left">ID</th>
                <th class="px-4 py-3 text-left">From</th>
                <th class="px-4 py-3 text-left">To</th>
                <th class="px-6 py-3 text-right">Date</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <tr
                v-for="e in modifyResults"
                :key="e.name"
                class="cursor-pointer hover:bg-slate-800/40 transition"
                @click="loadEntry(e.name)"
              >
                <td class="px-6 py-4 font-mono font-bold text-blue-400">{{ e.name }}</td>
                <td class="px-4 py-4 text-slate-400">{{ e.from_warehouse }}</td>
                <td class="px-4 py-4 text-slate-400">{{ e.to_warehouse }}</td>
                <td class="px-6 py-4 text-right text-slate-500">{{ e.posting_date }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="p-12 text-center text-slate-600 italic">No draft entries found</div>
        </div>
        <div class="border-t border-slate-700 p-4 bg-slate-800 flex justify-end">
          <button @click="showModifyEntry = false" class="px-6 py-2 text-sm font-bold text-slate-400 hover:text-slate-200">Cancel</button>
        </div>
      </div>
    </div>

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Stock"
      :warehouse="fromWarehouse"
      :skip-date-filter="true"
      @close="showItemSearchModal = false"
      @select="pickItem"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import ItemSearch from '../components/ItemSearch.vue'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import { useShortcuts, useSubwindow } from '../services/shortcutManager'
import { materialTransferShortcuts } from '../shortcuts/materialTransferShortcuts'

const router = useRouter()
const API = 'ssplbilling.api.stock_api'

// ==================== PROPS & EMITS ====================
const props = defineProps({
  isSubWindow: Boolean,
  name: String
})
const emit = defineEmits(['close'])

if (props.isSubWindow) useSubwindow()

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const newItemCode = ref('')
const newQty = ref(1)
const entryName = ref(null)
const entryDocStatus = ref(0)
const entryDate = ref(new Date().toISOString().split('T')[0])
const entrySeries = ref('')
const purpose = ref('Material Transfer')
const fromWarehouse = ref('')
const toWarehouse = ref('')

const availableSeries = ref([])
const availableWarehouses = ref([])
const availablePurposes = ref(['Material Issue', 'Material Receipt', 'Material Transfer'])
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)

const newPending = ref({ item_name: '', uom: '', rate: 0 })
const selectedItemData = ref(null)

const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`
}))

const activeItems = computed(() => items.value.filter(i => !i.deleted))
const deletedCount = computed(() => items.value.filter(i => i.deleted).length)
const totalValue = computed(() => activeItems.value.reduce((s, i) => s + (i.qty * i.rate), 0))

// ==================== REFS & FOCUS ====================
const inputRefs = {}
const rowRefs = {}
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const seriesSelect = ref(null)
const saveButton = ref(null)
const itemSearchModalRef = ref(null)
const showItemSearchModal = ref(false)

function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }

function focusField(f, idx) { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusNewCode()   { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty()    { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }

// ==================== NAVIGATION ====================
function findNextActiveRow(from, dir) { let i = from + dir; while (i >= 0 && i < items.value.length) { if (!items.value[i].deleted) return i; i += dir }; return null }
function moveRow(from, dir) { const n = findNextActiveRow(from, dir); if (n !== null) { selectedRow.value = n; focusRow(n) } else if (dir === 1) { selectedRow.value = -1; focusNewCode() } }
function moveToLastActiveRow() { for (let i = items.value.length - 1; i >= 0; i--) { if (!items.value[i].deleted) { selectedRow.value = i; focusRow(i); return } } }
function selectRow(idx) { if (!items.value[idx].deleted) { selectedRow.value = idx; focusRow(idx) } }
function goToNextRow(from) { const n = findNextActiveRow(from, 1); if (n !== null) { selectedRow.value = n; focusRow(n) } else { selectedRow.value = -1; focusNewCode() } }

function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); focusField('code', idx) }
}

// ==================== DATA FETCHING ====================
async function fetchConfig() {
  try {
    const series = await frappeGet(`${API}.get_naming_series`)
    availableSeries.value = series || []
    if (series.length) entrySeries.value = series[0]

    const whs = await frappeGet('frappe.client.get_list', {
      doctype: 'Warehouse',
      filters: { is_group: 0, disabled: 0 },
      fields: ['name'],
      limit: 1000
    })
    availableWarehouses.value = whs.map(w => w.name)
    
    // Auto-select first two distinct warehouses if available
    if (availableWarehouses.value.length >= 2) {
      fromWarehouse.value = availableWarehouses.value[0]
      toWarehouse.value = availableWarehouses.value[1]
    }

    const purposes = await frappeGet(`${API}.get_stock_entry_purposes`)
    if (purposes && purposes.length) {
      availablePurposes.value = purposes
    }
  } catch (e) {
    console.error('Failed to fetch config', e)
  }
}

async function lookupItem(code) {
  try {
    return await frappeGet(`${API}.get_item_details`, { item_code: code, warehouse: fromWarehouse.value })
  } catch (e) { return null }
}

watch(newItemCode, async (val) => {
  const code = val.trim()
  if (code.length < 2) { newPending.value = { item_name: '', uom: '', rate: 0 }; return }
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.valuation_rate }
  }
})

watch(selectedRow, async (idx) => {
  if (idx >= 0 && items.value[idx]) {
    const item = items.value[idx]
    try {
      const res = await frappeGet(`${API}.get_item_details`, { item_code: item.item_code })
      const stock = await frappeGet('frappe.client.get_list', {
        doctype: 'Bin',
        filters: { item_code: item.item_code, warehouse: ['in', [fromWarehouse.value, toWarehouse.value]] },
        fields: ['warehouse', 'actual_qty']
      })
      selectedItemData.value = { 
        ...res, 
        stock: stock.map(s => ({ warehouse: s.warehouse, qty: s.actual_qty })) 
      }
    } catch (e) {}
  } else {
    selectedItemData.value = null
  }
})

const stockAtSource = computed(() => {
  if (!selectedItemData.value) return 0
  return selectedItemData.value.stock?.find(s => s.warehouse === fromWarehouse.value)?.qty || 0
})

const stockAtTarget = computed(() => {
  if (!selectedItemData.value) return 0
  return selectedItemData.value.stock?.find(s => s.warehouse === toWarehouse.value)?.qty || 0
})

// ==================== ITEM ACTIONS ====================
async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    const row = items.value[idx]
    row.item_name = r.item_name; row.uom = r.uom; row.rate = r.valuation_rate; row.deleted = false
    focusField('qty', idx)
  } else {
    openSearch(idx)
  }
}

async function onNewCodeEnter() {
  const code = newItemCode.value.trim(); if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.valuation_rate }
    focusNewQty()
  } else {
    openSearch()
  }
}

function addNewItem() {
  if (!newItemCode.value || !newPending.value.item_name) return
  
  const existing = items.value.find(i => i.item_code === newItemCode.value && !i.deleted)
  if (existing) {
    existing.qty += newQty.value
  } else {
    items.value.push({
      item_code: newItemCode.value,
      item_name: newPending.value.item_name,
      uom: newPending.value.uom,
      qty: newQty.value,
      rate: newPending.value.rate,
      deleted: false
    })
  }
  
  newItemCode.value = ''
  newQty.value = 1
  newPending.value = { item_name: '', uom: '', rate: 0 }
  focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== SEARCH ====================
function openSearch(idx = null) {
  selectedRow.value = idx === null ? -1 : idx
  showItemSearchModal.value = true
  nextTick(() => itemSearchModalRef.value?.focus())
}

function pickItem(item) {
  showItemSearchModal.value = false
  if (selectedRow.value === -1) {
    newItemCode.value = item.item_code
    newPending.value = { item_name: item.item_name, uom: item.uom, rate: item.valuation_rate }
    nextTick(focusNewQty)
  } else {
    const row = items.value[selectedRow.value]
    row.item_code = item.item_code; row.item_name = item.item_name; row.uom = item.uom; row.rate = item.valuation_rate
    focusField('qty', selectedRow.value)
  }
}

// ==================== SAVE / LOAD ====================
async function saveEntry() {
  if (purpose.value !== 'Material Receipt' && !fromWarehouse.value) { alert('Select From warehouse'); return }
  if (purpose.value !== 'Material Issue' && !toWarehouse.value) { alert('Select To warehouse'); return }
  if (purpose.value === 'Material Transfer' && fromWarehouse.value === toWarehouse.value) { alert('Source and Target warehouses cannot be same'); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    name: entryName.value,
    date: entryDate.value,
    naming_series: entrySeries.value,
    purpose: purpose.value,
    from_warehouse: (purpose.value !== 'Material Receipt') ? fromWarehouse.value : '',
    to_warehouse: (purpose.value !== 'Material Issue') ? toWarehouse.value : '',
    items: activeItems.value.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      uom: i.uom,
      rate: i.rate
    }))
  }

  try {
    const method = entryName.value ? 'update_stock_entry' : 'create_stock_entry'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    entryName.value = res.name
    alert(`Entry ${res.name} saved as Draft`)
    // Optionally stay on the page to allow submission
  } catch (e) {
    alert(e.message || 'Save failed')
  }
}

async function submitEntry() {
  if (!entryName.value) return
  if (!confirm('Are you sure you want to SUBMIT this entry? This will update stock levels and cannot be undone.')) return

  try {
    await frappePost(`${API}.submit_stock_entry`, { name: entryName.value })
    alert(`Entry ${entryName.value} submitted successfully`)
    startNewEntry()
  } catch (e) {
    alert(e.message || 'Submission failed')
  }
}

function startNewEntry() {
  items.value = []; entryName.value = null; entryDocStatus.value = 0
  newItemCode.value = ''; newQty.value = 1; selectedRow.value = -1
  selectedItemData.value = null
  nextTick(focusNewCode)
}

// ==================== MODIFY ====================
const showModifyEntry = ref(false)
const showIncentiveModal = ref(false)
const modifyQuery = ref('')
const modifyResults = ref([])
const modifyLoading = ref(false)
const modifySearchInput = ref(null)

function openModifyEntry() {
  showModifyEntry.value = true
  searchEntries()
  nextTick(() => modifySearchInput.value?.focus())
}

watch(modifyQuery, () => searchEntries())

async function searchEntries() {
  modifyLoading.value = true
  try {
    modifyResults.value = await frappeGet(`${API}.get_stock_entries`, { query: modifyQuery.value })
  } catch (e) {}
  modifyLoading.value = false
}

async function loadEntry(name) {
  try {
    const data = await frappeGet(`${API}.get_stock_entry`, { name })
    entryName.value = data.name
    entryDate.value = data.posting_date
    entrySeries.value = data.naming_series
    purpose.value = data.purpose || 'Material Transfer'
    fromWarehouse.value = data.from_warehouse
    toWarehouse.value = data.to_warehouse
    items.value = data.items
    entryDocStatus.value = data.docstatus
    showModifyEntry.value = false
    nextTick(focusNewCode)
  } catch (e) { alert('Load failed') }
}

// ==================== SHORTCUTS ====================
function handleBack() {
  if (items.value.length && !entryName.value) {
    if (!confirm('Discard unsaved entry?')) return
  }
  router.push('/')
}

useShortcuts(materialTransferShortcuts({
  save: saveEntry,
  searchItem: () => openSearch(),
  deleteRow: () => { if (selectedRow.value >= 0) softDelete(selectedRow.value) },
  focusSeries: () => seriesSelect.value?.focus(),
  openIncentive: () => { if (entryName.value) showIncentiveModal.value = true },
  contextualBack: () => {
    if (showModifyEntry.value) { showModifyEntry.value = false; return }
    if (showItemSearchModal.value) { showItemSearchModal.value = false; return }
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

onMounted(() => {
  fetchConfig()
  nextTick(focusNewCode)
})
</script>
