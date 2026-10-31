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
                  @keydown.enter.prevent="focusNewCode"
                  :disabled="isReadOnly || items.length > 0"
                  class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[250px]"
                >
                  <option value="">-- Select Warehouse --</option>
                  <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
                </select>
              </div>

            </div>

            <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Posting Date</label>
              <div class="flex items-center gap-1">
                <button v-if="canModifyDate()" @click="changeDate(-1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center disabled:opacity-30">&larr;</button>
                <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(entryDate) }}</div>
                <button v-if="canModifyDate()" @click="changeDate(1)" :disabled="isReadOnly" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] leading-none flex items-center disabled:opacity-30">&rarr;</button>
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
          <th v-if="showBatchColumn" class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-px whitespace-nowrap">Batch</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Curr Qty</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">New Qty</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Curr Rate</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-20">UOM</th>
          <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">Diff</th>
          <th class="border-b border-[var(--color-border)] w-12"></th>
        </tr>
      </template>

      <template #row="{ item, index }">
        <tr
          :ref="el => setRowRef(el, index)"
          :tabindex="isReadOnly ? -1 : 0"
          class="group border-b border-[var(--color-border)] last:border-0 outline-none cursor-pointer transition-colors"
          :class="isActiveRow(index) ? 'bg-[var(--color-focus)] font-bold' : 'hover:bg-[var(--color-surface)]/40'"
          :style="{ fontSize: dynamicRowStyle.fontSize }"
          @click="selectRow(index)"
          @dblclick="startRowEdit(index)"
          @focus="selectedRow = index"
          @keydown="onRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] font-mono text-3xl text-center" :class="tone(index, 'text-[var(--color-text-muted)]')">{{ index + 1 }}</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <span class="font-mono font-semibold text-4xl truncate block w-40" :class="tone(index, 'text-[var(--color-info)]')" :title="item.item_code">{{ item.item_code }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <div class="text-4xl font-medium" :class="tone(index, 'text-[var(--color-text)]')" :title="item.item_name">{{ item.item_name || '--' }}</div>
          </td>
          <td v-if="showBatchColumn" class="px-2 py-1 border-r border-[var(--color-border)] whitespace-nowrap">
            <button
              v-if="item.batch_no || itemHasBatch(item.item_code)"
              type="button"
              tabindex="-1"
              :disabled="isReadOnly"
              @click.stop="openBatchView({ type: 'row', index })"
              class="rounded px-2 text-3xl font-mono font-bold disabled:cursor-default"
              :class="item.batch_no ? 'bg-[var(--color-info)]/20 text-[var(--color-info)]' : 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'"
              :title="isReadOnly ? 'Batch' : 'Change batch'"
            >{{ item.batch_no || 'No batch' }}</button>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-4xl" :class="tone(index, 'text-[var(--color-text-muted)]')">
            {{ item.current_qty }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right font-mono">
            <input
              v-if="editingRow === index"
              ref="editQtyInput"
              v-model.number="editQty"
              type="number"
              step="any"
              class="w-full bg-white/10 px-2 py-1 text-right text-[var(--color-text)] font-bold outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown="onEditQtyKeydown($event, index)"
            />
            <template v-else>
              <span class="block px-2 py-1 text-6xl font-bold tabular-nums" :class="tone(index, 'text-[var(--color-text)]')">{{ formatQty(item.qty / rowFactor(item)) }}</span>
              <span v-if="rowEntryUom(item) !== item.uom" class="block px-2 pb-1 text-xl" :class="tone(index, 'text-[var(--color-text-muted)]')">= {{ formatQty(item.qty) }} {{ item.uom }}</span>
            </template>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono text-4xl" :class="tone(index, 'text-[var(--color-text-muted)]')">
            {{ item.current_valuation_rate?.toFixed(2) }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <select
              v-if="editingRow === index && itemUoms(item.item_code, item.uom).length > 1"
              ref="editUomSelect"
              v-model="editUom"
              class="w-full bg-white/10 px-2 py-1 text-3xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @change="onEditUomChange(index)"
              @keydown="onEditUomKeydown($event, index)"
            >
              <option v-for="u in itemUoms(item.item_code, item.uom)" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ uomLabel(item.item_code, u) }}</option>
            </select>
            <span v-else class="block px-2 py-1 text-4xl whitespace-nowrap" :class="tone(index, 'text-[var(--color-text-muted)]')">{{ uomLabel(item.item_code, rowEntryUom(item)) || '--' }}</span>
          </td>
          <td
            class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono font-bold text-4xl"
            :class="tone(index, rowDiff(item, index) > 0 ? 'text-[var(--color-success)]' : rowDiff(item, index) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]')"
          >
            {{ rowDiff(item, index).toFixed(2) }}
          </td>
          <td class="px-2 py-1 text-center">
            <button v-if="!isReadOnly" tabindex="-1" class="rounded px-1 py-0.5 hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] transition" :class="tone(index, 'text-[var(--color-text-muted)]')" @click.stop="removeItem(index)">&times;</button>
          </td>
        </tr>
      </template>

      <template #table-extra-rows>
        <!-- Pending row: qty (and UOM) for the scanned / picked item -->
        <tr v-if="!isReadOnly && newPending.item_name" class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10" :style="{ fontSize: dynamicRowStyle.fontSize }">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] font-bold text-3xl text-center">+</td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <span class="font-mono font-semibold text-[var(--color-highlight)] text-4xl truncate block w-40" :title="newItemCode">{{ newItemCode }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)]">
            <div class="text-[var(--color-text)] text-4xl">{{ newPending.item_name }}</div>
          </td>
          <td v-if="showBatchColumn" class="px-2 py-1 border-r border-[var(--color-border)] whitespace-nowrap">
            <span v-if="newPending.batch_no" class="rounded px-2 text-3xl font-mono font-bold bg-[var(--color-info)]/20 text-[var(--color-info)]">{{ newPending.batch_no }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right text-[var(--color-text-muted)] font-mono text-4xl">
            {{ newPending.current_qty }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)] text-right">
            <input
              ref="newQtyInput"
              v-model.number="newQty"
              type="number"
              step="any"
              class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] text-6xl [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown="onNewQtyKeydown"
            />
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right text-[var(--color-text-muted)] font-mono text-4xl">
            {{ newPending.valuation_rate?.toFixed(2) }}
          </td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <select
              v-if="newItemUoms.length > 1"
              ref="newUomSelect"
              v-model="newPending.uom"
              class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-3xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @change="onNewUomChange"
              @keydown="onNewUomKeydown"
            >
              <option v-for="u in newItemUoms" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ uomLabel(newItemCode, u) }}</option>
            </select>
            <span v-else class="block px-2 py-1 text-[var(--color-text-muted)] text-4xl">{{ newPending.uom || '--' }}</span>
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-right font-mono font-bold text-4xl" :class="newDiff > 0 ? 'text-[var(--color-success)]' : newDiff < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
            {{ newDiff.toFixed(2) }}
          </td>
          <td class="px-2 py-1 text-center">
            <button tabindex="-1" class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] transition" @click.stop="cancelPending()">&times;</button>
          </td>
        </tr>

        <!-- Barcode input row -->
        <tr v-else-if="!isReadOnly" class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/5" :style="{ fontSize: dynamicRowStyle.fontSize }">
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] font-mono text-3xl text-center">*</td>
          <td class="p-0 border-r border-[var(--color-border)]">
            <input
              ref="newCodeInput"
              v-model="newItemCode"
              class="w-full bg-transparent px-2 py-1 font-mono text-[var(--color-highlight)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] placeholder:text-[var(--color-text-muted)]/40 text-4xl"
              placeholder="Scan or Type Item..."
              @input="onNewCodeInput"
              @keydown="handleNewCodeKeydown"
            />
          </td>
          <td :colspan="showBatchColumn ? 8 : 7" class="px-2 text-[var(--color-text-muted)] italic text-2xl">Enter item code / barcode &nbsp;·&nbsp; &rarr; search &nbsp;·&nbsp; &uarr; rows</td>
        </tr>
      </template>

      <template #bottom-left>
        <div class="flex flex-col gap-2 p-4 h-[120px] overflow-y-auto">
           <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Keys</div>
           <ul class="text-xs text-[var(--color-text-muted)] list-disc list-inside space-y-1">
             <li><b>F2</b> warehouse, <b>F7</b> fetch all items of the warehouse, <b>F8 / Ctrl+S</b> save.</li>
             <li>Scan / type item, <b>Enter</b>: type qty, <b>Enter</b> (choose UOM, <b>Enter</b>) adds it. A scanned item already in the list jumps to its row.</li>
             <li>Rows: <b>&uarr;&darr; Home End</b> move, <b>Enter</b> or type a number to edit qty, <b>Delete</b> removes, <b>Esc</b> back to the scan box.</li>
             <li>Editing qty: <b>Enter</b> saves and goes to next row, <b>&uarr;&darr;</b> save and edit the row above / below, <b>Esc</b> cancels.</li>
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

  <!-- Batch picker: batch items are counted one batch per row -->
  <BatchView
    v-if="showBatchView && batchTargetItem"
    :show="showBatchView"
    :item-code="batchTargetItem.item_code"
    :item-name="batchTargetItem.item_name"
    :warehouse="warehouse"
    :selected="batchTargetItem.batch_no || ''"
    @select="onBatchSelected"
    @close="closeBatchView"
  />

  <!-- Quick Item Search -->
  <QuickItemSearch
    ref="quickSearchRef"
    :results="quickSearchResults"
    :query="newItemCode"
    search-type="Stock"
    :warehouse="warehouse"
    :anchor-el="quickSearchAnchor"
    :last-item-code="items[items.length - 1]?.item_code"
    @select="onQuickSearchSelect"
    @close="quickSearchResults = []"
    @refresh="onQuickSearchRefresh"
  />

  <!-- Exit Warning Modal -->
  <Warning
    :show="showExitWarning"
    title="Exit Page"
    message="Are you sure you want to exit? Unsaved changes will be lost."
    @close="showExitWarning = false"
    @confirm="showExitWarning = false; router.push('/')"
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
import QuickItemSearch from '../components/QuickItemSearch.vue'
import BatchView from '../components/BatchView.vue'
import Warning from '../components/Warning.vue'
import { useItemCache, uomLabel, itemHasBatch } from '../services/itemCache.js'
import { canModifyDate } from '../composables/usePermission.js'

import { formatDMY } from '../utils/date'
import { scrollInvoiceRowIntoView } from '../utils/invoiceScroll.js'
import { serverToday, toLocalISO, parseCalendarDate } from '../services/serverTime'
import { getCachedList } from '../services/masterCache.js'
const router = useRouter()
const showExitWarning = ref(false)
const API = 'ssplbilling.api.stock_reconciliation_api'
const { allowedSeries: availableSeries, fetchAllowedSeries } = useAllowedSeries()
const { refreshItemCache, lookupItemInCache, searchItemsInCache } = useItemCache()

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
const entryDate = ref(serverToday())
const availableWarehouses = ref([])
const availablePurposes = ref(['Stock Reconciliation', 'Opening Stock'])
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

const isReadOnly = ref(false)
const isDraft = ref(false)

// New entry state
const newItemCode = ref('')
const newQty = ref(0)
const newRate = ref(0)
const newPending = ref({ item_name: '', uom: '', stock_uom: '', current_qty: 0, valuation_rate: 0, batch_no: '' })
const showItemSearch = ref(false)

const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)

// Sidebar state
const sidebarDate = ref(serverToday())
const sidebarSearch = ref('')
const sidebarEntries = ref([])
const sidebarLoading = ref(false)
const draftOnly = ref(true)
const sidebarEntryRefs = new Map()

const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`
}))

// Entry UOMs for the pending item: stock UOM first, then its conversion UOMs.
// Reconciliation rows are stored in stock UOM; the entered qty is converted on add.
const newItemUoms = computed(() => itemUoms(newItemCode.value, newPending.value.stock_uom))

const newFactor = computed(() => uomFactor(newItemCode.value, newPending.value.uom, newPending.value.stock_uom) || 1)
const newDiff = computed(() => (newQty.value || 0) * newFactor.value - newPending.value.current_qty)

const adjustedCount = computed(() => items.value.filter(i => Math.abs(i.qty - i.current_qty) > 0.0001).length)

// Row being edited: its qty is typed in `editUom` and stored back in stock UOM on commit.
const editingRow = ref(-1)
const editQty = ref(0)
const editUom = ref('')
let editPrevUom = ''

const saveButtonText = computed(() => {
  if (isReadOnly.value && !isDraft.value) return 'New'
  if (isReadOnly.value && isDraft.value) return 'Edit'
  return 'Save'
})

// ==================== REFS & FOCUS ====================
const rowRefs = {}
const warehouseSelect = ref(null)
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const newUomSelect = ref(null)
const editQtyInput = ref(null)
const editUomSelect = ref(null)

function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarEntryRef(el, idx) { if (el) sidebarEntryRefs.set(idx, el); else sidebarEntryRefs.delete(idx) }

function focusRow(idx, direction = null) {
  selectedRow.value = idx
  nextTick(() => {
    const el = rowRefs[idx]
    if (!el) return
    el.focus({ preventScroll: true })
    scrollInvoiceRowIntoView(el, direction)
  })
}
function focusWarehouse() { nextTick(() => warehouseSelect.value?.focus()) }
function focusNewCode()   {
  selectedRow.value = -1
  nextTick(() => { newCodeInput.value?.focus(); newCodeInput.value?.scrollIntoView({ block: 'nearest' }) })
}
// Where typing starts: warehouse first when none is chosen, else the scan box.
function focusEntryStart() { if (warehouse.value) focusNewCode(); else focusWarehouse() }
function focusNewQty()    { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }

function navigateSidebarEntry(idx, dir) {
  const target = sidebarEntryRefs.get(idx + dir)
  if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }) }
}

function changeSidebarDate(days) {
  const d = parseCalendarDate(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = toLocalISO(d)
}

function changeDate(dir) {
  if (!canModifyDate()) return
  const d = parseCalendarDate(entryDate.value)
  d.setDate(d.getDate() + dir)
  entryDate.value = toLocalISO(d)
}

function formatDate(dateString) {
  return formatDMY(dateString, '')
}

// ==================== NAVIGATION ====================
function isActiveRow(idx) { return selectedRow.value === idx || editingRow.value === idx }
// Text colour for a cell: on-focus text on the highlighted row, else the cell's own colour.
function tone(idx, cls) { return isActiveRow(idx) ? 'text-[var(--color-text-on-focus)]' : cls }

function selectRow(idx) { if (editingRow.value !== idx) focusRow(idx) }

function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  const last = items.value.length - 1
  if (e.key === 'ArrowDown') { e.preventDefault(); if (idx < last) focusRow(idx + 1, 'down'); else focusNewCode() }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (idx > 0) focusRow(idx - 1, 'up') }
  else if (e.key === 'Home') { e.preventDefault(); focusRow(0, 'up') }
  else if (e.key === 'End') { e.preventDefault(); if (idx === last) focusNewCode(); else focusRow(last, 'down') }
  else if (e.key === 'PageDown') { e.preventDefault(); focusRow(Math.min(idx + 10, last), 'down') }
  else if (e.key === 'PageUp') { e.preventDefault(); focusRow(Math.max(idx - 10, 0), 'up') }
  else if (e.key === 'Enter') { e.preventDefault(); startRowEdit(idx) }
  // Typing a number on a row starts editing its qty with that digit
  else if (/^[0-9.]$/.test(e.key) && !e.ctrlKey && !e.altKey && !e.metaKey) { e.preventDefault(); startRowEdit(idx, e.key) }
  // stopPropagation: the page-level Esc would ask to discard and leave the page
  else if (e.key === 'Escape' && !isReadOnly.value) { e.preventDefault(); e.stopPropagation(); focusNewCode() }
  else if (e.key === 'Delete') { e.preventDefault(); e.stopPropagation(); removeItem(idx) }
}

// ==================== ROW UOM / EDIT ====================
// UOMs an item can be counted in: stock UOM first, then its conversion UOMs.
function itemUoms(itemCode, stockUom) {
  const cached = itemCode && lookupItemInCache(itemCode)
  if (!cached || !stockUom) return []
  const others = (cached.uoms || []).map(u => u.uom).filter(u => u && u !== stockUom)
  return [stockUom, ...new Set(others)]
}

// Rows keep `qty` in stock UOM (`uom`); `entry_uom` is only how the qty is shown and typed.
function rowEntryUom(item) {
  return item.entry_uom && uomFactor(item.item_code, item.entry_uom, item.uom) ? item.entry_uom : item.uom
}
function rowFactor(item) { return uomFactor(item.item_code, rowEntryUom(item), item.uom) || 1 }
function rowDiff(item, idx) {
  const qty = editingRow.value === idx
    ? (editQty.value || 0) * (uomFactor(item.item_code, editUom.value, item.uom) || 1)
    : item.qty
  return (qty || 0) - (item.current_qty || 0)
}
function formatQty(v) { return parseFloat(roundQty(v).toFixed(3)) }

function startRowEdit(idx, firstKey = null, uom = null) {
  if (isReadOnly.value) return
  const item = items.value[idx]
  if (!item) return
  if (editingRow.value !== -1 && editingRow.value !== idx) commitRowEdit(editingRow.value)
  editingRow.value = idx
  selectedRow.value = idx
  editUom.value = uom && uomFactor(item.item_code, uom, item.uom) ? uom : rowEntryUom(item)
  editPrevUom = editUom.value
  editQty.value = firstKey != null ? firstKey : roundQty(item.qty / (uomFactor(item.item_code, editUom.value, item.uom) || 1))
  nextTick(() => {
    const el = editQtyInput.value
    if (!el) return
    el.focus({ preventScroll: true })
    if (firstKey == null) el.select()
    scrollInvoiceRowIntoView(rowRefs[idx])
  })
}

function commitRowEdit(idx) {
  const item = items.value[idx]
  if (item && editingRow.value === idx) {
    const qty = parseFloat(editQty.value)
    if (!isNaN(qty)) {
      item.entry_uom = editUom.value
      item.qty = roundQty(qty * (uomFactor(item.item_code, editUom.value, item.uom) || 1))
    }
  }
  editingRow.value = -1
}

function cancelRowEdit(idx) {
  editingRow.value = -1
  focusRow(idx)
}

// Save this row's edit, then move: to the next row (Enter), or keep editing above / below (arrows).
function commitAndMove(idx, dir, keepEditing) {
  commitRowEdit(idx)
  const next = idx + dir
  if (next < 0) { focusRow(idx); return }
  if (next >= items.value.length) { focusNewCode(); return }
  if (keepEditing) startRowEdit(next)
  else focusRow(next, dir > 0 ? 'down' : 'up')
}

function onEditQtyKeydown(e, idx) {
  if (e.key === 'Enter' || e.key === 'Tab') {
    e.preventDefault()
    if (itemUoms(items.value[idx]?.item_code, items.value[idx]?.uom).length > 1) editUomSelect.value?.focus()
    else commitAndMove(idx, 1, false)
  }
  else if (e.key === 'ArrowDown') { e.preventDefault(); commitAndMove(idx, 1, true) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); commitAndMove(idx, -1, true) }
  else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cancelRowEdit(idx) }
  else if (e.key === 'Delete') e.stopPropagation()
}

function onEditUomChange(idx) {
  const item = items.value[idx]
  if (!item) return
  const stock = (parseFloat(editQty.value) || 0) * (uomFactor(item.item_code, editPrevUom, item.uom) || 1)
  editQty.value = roundQty(stock / (uomFactor(item.item_code, editUom.value, item.uom) || 1))
  editPrevUom = editUom.value
}

function onEditUomKeydown(e, idx) {
  if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); commitAndMove(idx, 1, false) }
  else if (e.key === 'Escape' || e.key === 'ArrowLeft') {
    e.preventDefault(); e.stopPropagation()
    nextTick(() => { editQtyInput.value?.focus(); editQtyInput.value?.select() })
  }
}

// ==================== DATA FETCHING ====================
async function fetchConfig() {
  try {
    const whs = await getCachedList({
      doctype: 'Warehouse',
      filters: { is_group: 0, disabled: 0 },
      fields: ['name'],
      limit: 1000,
      order_by: 'name asc'
    })
    availableWarehouses.value = whs.map(w => w.name)
    const localWh = localStorage.getItem('wb-warehouse')
    if (!warehouse.value) {
      if (localWh && availableWarehouses.value.includes(localWh)) {
        warehouse.value = localWh
      } else if (availableWarehouses.value.length) {
        warehouse.value = availableWarehouses.value[0]
      }
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
    editingRow.value = -1
    if (items.value.length) focusRow(0, 'up')
    else focusNewCode()
  } catch (e) { alert(e.message || 'Fetch failed') }
}

async function lookupItem(code) {
  try {
    return await frappePost(`ssplbilling.api.storetransfer_api.get_item_details`, { item_code: code, warehouse: warehouse.value })
  } catch (e) { return null }
}

// Stock UOMs held by one `uom` of the item; null when the factor is unknown.
function uomFactor(itemCode, uom, stockUom) {
  if (!uom || uom === stockUom) return 1
  const cached = lookupItemInCache(itemCode)
  const cf = parseFloat((cached?.uoms || []).find(u => u.uom === uom)?.conversion_factor)
  return cf > 0 ? cf : null
}

// The cached item's own uom is the stock UOM; a barcode match swaps in the barcode's UOM.
function stockUomOf(itemCode, fallback) {
  return lookupItemInCache(itemCode)?.uom || fallback || ''
}

// Pending row for an item: `uom` is the entry UOM (a scanned barcode's UOM), and the qty
// box starts at the current stock expressed in that UOM so Diff reads 0 until changed.
// A batch item first goes through the batch picker; returns true while that picker is open.
function setNewPending({ item_name, uom, stock_uom, current_qty, valuation_rate, batch_no = '' }) {
  if (!batch_no && itemHasBatch(newItemCode.value)) {
    pendingBatchArgs = { item_name, uom, stock_uom, current_qty, valuation_rate }
    openBatchView({ type: 'pending' })
    return true
  }
  // Stock Reconciliation can't hold an item (batch) twice: go to its row and edit the qty there,
  // in the scanned barcode's UOM.
  const existing = items.value.findIndex(i => i.item_code === newItemCode.value && (i.batch_no || '') === batch_no)
  if (existing !== -1) {
    clearPending()
    startRowEdit(existing, null, uom)
    return false
  }
  // A UOM without a known conversion factor would be counted as stock units; enter in stock UOM.
  const entryUom = uom && uomFactor(newItemCode.value, uom, stock_uom) ? uom : stock_uom
  newPending.value = { item_name: item_name || newItemCode.value, uom: entryUom, stock_uom, current_qty, valuation_rate, batch_no }
  newQty.value = roundQty(current_qty / newFactor.value)
  newRate.value = valuation_rate
  return false
}

// ==================== BATCH ====================
const showBatchView = ref(false)
const batchTarget = ref(null) // { type: 'pending' } | { type: 'row', index }
// Item details of the scanned batch item, waiting for its batch
let pendingBatchArgs = null

const showBatchColumn = computed(() =>
  items.value.some(i => i.batch_no || itemHasBatch(i.item_code)) || !!newPending.value.batch_no)

const batchTargetItem = computed(() => {
  const t = batchTarget.value
  if (!t) return null
  if (t.type === 'pending') return { item_code: newItemCode.value, item_name: pendingBatchArgs?.item_name || newItemCode.value, batch_no: '' }
  return items.value[t.index]
})

function openBatchView(target) {
  batchTarget.value = target
  showBatchView.value = true
}

// Closing without a pick drops the scanned item: a batch item cannot be counted without one
function closeBatchView() {
  const t = batchTarget.value
  showBatchView.value = false
  batchTarget.value = null
  if (t?.type === 'pending') {
    pendingBatchArgs = null
    cancelPending()
  } else if (t?.type === 'row') {
    focusRow(t.index)
  }
}

// Current qty is the batch's own stock, so Diff only moves that batch
function onBatchSelected(batchNo, batch) {
  const t = batchTarget.value
  const batchQty = roundQty(Number(batch?.qty) || 0)
  showBatchView.value = false
  batchTarget.value = null
  if (t?.type === 'pending') {
    const args = pendingBatchArgs
    pendingBatchArgs = null
    if (!args) return cancelPending()
    setNewPending({ ...args, current_qty: batchQty, batch_no: batchNo })
    if (newPending.value.item_name) focusNewQty()
    return
  }
  const row = t && items.value[t.index]
  if (!row) return
  const dup = items.value.findIndex((i, idx) => idx !== t.index && i.item_code === row.item_code && i.batch_no === batchNo)
  if (dup !== -1) {
    alert(`Batch ${batchNo} is already on row ${dup + 1}`)
    focusRow(dup)
    return
  }
  // An uncounted row follows the new batch's stock, so switching alone does not adjust anything
  const untouched = Math.abs((row.qty || 0) - (row.current_qty || 0)) <= 0.0001
  row.batch_no = batchNo
  row.current_qty = batchQty
  if (untouched) row.qty = batchQty
  focusRow(t.index)
}

function roundQty(v) { return Math.round((v || 0) * 1000) / 1000 }

function clearPending() {
  newItemCode.value = ''
  newQty.value = 0
  newRate.value = 0
  newPending.value = { item_name: '', uom: '', stock_uom: '', current_qty: 0, valuation_rate: 0, batch_no: '' }
  quickSearchResults.value = []
}

function cancelPending() {
  clearPending()
  focusNewCode()
}

function onNewQtyKeydown(e) {
  if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); onNewQtyEnter() }
  else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cancelPending() }
  else if (e.key === 'Backspace' && e.target.value === '') { e.preventDefault(); cancelPending() }
  else if (e.key === 'Delete') e.stopPropagation()
}

function onNewUomKeydown(e) {
  if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); addNewItem() }
  else if (e.key === 'Escape' || e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); focusNewQty() }
}

function onNewUomChange() {
  newQty.value = roundQty(newPending.value.current_qty / newFactor.value)
}

function onNewQtyEnter() {
  if (newItemUoms.value.length > 1) newUomSelect.value?.focus()
  else addNewItem()
}

async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) return
  const match = lookupItemInCache(code)
  if (match) {
    onQuickSearchSelect(match)
  } else {
    const r = await lookupItem(code)
    if (r && r.found) {
      newItemCode.value = r.item_code || code
      const picking = setNewPending({ item_name: r.item_name, uom: r.uom, stock_uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.rate })
      quickSearchResults.value = []
      if (!picking) focusNewQty()
    } else {
      showItemSearch.value = true
    }
  }
}

function onNewCodeInput() {
  const code = newItemCode.value.trim()
  if (newItemCode.value === '  ') {
    quickSearchResults.value = [{ item_code: 'DUMMY' }]
    quickSearchAnchor.value = newCodeInput.value
  } else if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = newCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

let lastEnterTime = 0

function handleNewCodeKeydown(e) {
  if (e.key === 'Enter') {
    // Double Enter clears the scan box
    const now = Date.now()
    const isDouble = now - lastEnterTime < 400
    lastEnterTime = now
    if (isDouble) { e.preventDefault(); clearPending(); lastEnterTime = 0; return }
  }

  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    }
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); quickSearchResults.value = []; return }
  }

  if (e.key === 'Enter') { e.preventDefault(); onNewCodeEnter() }
  else if (e.key === 'ArrowRight' && e.target.selectionStart === newItemCode.value.length) { e.preventDefault(); showItemSearch.value = true }
  else if (e.key === 'ArrowUp' && items.value.length) { e.preventDefault(); focusRow(items.value.length - 1, 'down') }
  else if (e.key === 'Escape' && newItemCode.value) { e.preventDefault(); e.stopPropagation(); clearPending() }
}

function onQuickSearchSelect(item) {
  // A scanned barcode resolves to the item with that barcode's UOM
  const barcodeMatch = lookupItemInCache(newItemCode.value.trim())
  const finalItem = (barcodeMatch && barcodeMatch.item_code === item.item_code) ? barcodeMatch : item
  newItemCode.value = finalItem.item_code
  const picking = setNewPending({
    item_name: finalItem.item_name,
    uom: finalItem.uom,
    stock_uom: stockUomOf(finalItem.item_code, finalItem.uom),
    current_qty: finalItem.stock || 0,
    valuation_rate: finalItem.valuation_rate || 0
  })
  quickSearchResults.value = []
  if (!picking) nextTick(() => focusNewQty())
}

function onQuickSearchRefresh() {
  if (newItemCode.value) {
    quickSearchResults.value = searchItemsInCache(newItemCode.value)
  }
}

async function onItemSearchSelect(item) {
  showItemSearch.value = false
  newItemCode.value = item.item_code
  const r = await lookupItem(item.item_code)
  let picking
  if (r && r.found) {
    picking = setNewPending({ item_name: r.item_name, uom: r.uom, stock_uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.rate })
  } else {
    const stockUom = stockUomOf(item.item_code, item.uom)
    picking = setNewPending({ item_name: item.item_name, uom: stockUom, stock_uom: stockUom, current_qty: 0, valuation_rate: 0 })
  }
  if (!picking) nextTick(() => focusNewQty())
}

function addNewItem() {
  if (!newItemCode.value || !newPending.value.item_name) return

  items.value.push({
    item_code: newItemCode.value,
    item_name: newPending.value.item_name,
    uom: newPending.value.stock_uom || newPending.value.uom,
    entry_uom: newPending.value.uom,
    current_qty: newPending.value.current_qty,
    qty: roundQty((newQty.value || 0) * newFactor.value),
    valuation_rate: newRate.value || newPending.value.valuation_rate,
    current_valuation_rate: newPending.value.valuation_rate,
    batch_no: newPending.value.batch_no || '',
  })

  clearPending()
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

const isInitialLoad = ref(true)

watch(warehouse, (newWarehouse) => {
  if (newWarehouse) {
    refreshItemCache('Sales', null, newWarehouse)
    if (!isReadOnly.value && items.value.length === 0) {
      if (isInitialLoad.value) {
        isInitialLoad.value = false
      } else {
        fetchItems()
      }
    }
  }
})

// ==================== ACTIONS ====================
function removeItem(idx) {
  if (isReadOnly.value) return
  editingRow.value = -1
  items.value.splice(idx, 1)
  if (idx < items.value.length) focusRow(idx)
  else if (idx > 0) focusRow(idx - 1)
  else focusNewCode()
}

async function handleSave() {
  if (submitting.value) return
  if (isReadOnly.value && !isDraft.value) {
    startNewEntry()
    return
  }
  if (isReadOnly.value && isDraft.value) {
    isReadOnly.value = false
    focusNewCode()
    return
  }
  await saveEntry()
}

async function saveEntry() {
  if (submitting.value) return
  if (!warehouse.value) { alert('Select warehouse'); return }
  if (!items.value.length) { alert('No items to save'); return }
  if (editingRow.value !== -1) commitRowEdit(editingRow.value)
  // ERPNext refuses a batch item row with no batch ("Please add Serial and Batch Bundle")
  const noBatchIdx = items.value.findIndex(i => Math.abs(i.qty - i.current_qty) > 0.0001 && !i.batch_no && itemHasBatch(i.item_code))
  if (noBatchIdx !== -1) {
    alert(`Select a batch for ${items.value[noBatchIdx].item_code} (row ${noBatchIdx + 1})`)
    openBatchView({ type: 'row', index: noBatchIdx })
    return
  }

  const payload = {
    company: localStorage.getItem('wb-company') || null,
    name: entryName.value,
    posting_date: entryDate.value,
    purpose: purpose.value,
    warehouse: warehouse.value,
    items: items.value.filter(i => Math.abs(i.qty - i.current_qty) > 0.0001).map(i => ({
      item_code: i.item_code,
      warehouse: i.warehouse || warehouse.value,
      qty: i.qty,
      valuation_rate: i.valuation_rate || i.current_valuation_rate,
      batch_no: i.batch_no || '',
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
  editingRow.value = -1
  clearPending()
  focusEntryStart()
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
    editingRow.value = -1
    selectedRow.value = -1
    clearPending()
    isReadOnly.value = true
    isDraft.value = data.docstatus === 0
  } catch (e) { 
    console.error('Load failed', e)
    alert('Load failed: ' + (e.message || 'Unknown error')) 
  }
}

// ==================== SHORTCUTS ====================
// In edit mode (new entry or draft being edited) with rows entered, ask before leaving
function handleBack() {
  if (showExitWarning.value) return
  if (!isReadOnly.value && (items.value.length || newItemCode.value)) {
    showExitWarning.value = true
    return
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

onMounted(async () => {
  fetchAllowedSeries('Stock Reconciliation')
  const configLoaded = fetchConfig()
  fetchSidebarEntries()
  refreshItemCache('Sales')
  if (props.name) loadEntry(props.name)
  else { await configLoaded; focusEntryStart() }
})
</script>
