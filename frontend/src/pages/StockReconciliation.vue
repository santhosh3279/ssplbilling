<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-[var(--color-bg)]' : 'h-screen bg-[var(--color-bg)]'" class="flex">
    <!-- ===================== SIDEBAR / MODIFY PANEL ===================== -->
    <aside class="flex w-[15%] flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden shrink-0">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-center">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Modify Entries</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-[var(--color-border)] p-1.5 bg-[var(--color-bg)]">
          <button @click="changeSidebarDate(-1)" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)]">&larr;</button>
          <input 
            type="date" 
            v-model="sidebarDate"
            class="w-full bg-transparent text-xs font-bold text-[var(--color-text)] outline-none"
          />
          <button @click="changeSidebarDate(1)" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)]">&rarr;</button>
        </div>

        <!-- Search & Status Filters -->
        <div class="flex flex-col gap-1.5 border-b border-[var(--color-border)] p-2 bg-[var(--color-surface)]/20">
          <input 
            type="text" 
            v-model="sidebarSearch"
            placeholder="Search ID..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-[11px] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
          <button
            @click="draftOnly = !draftOnly"
            class="w-full rounded border py-1 text-[10px] font-bold uppercase transition-colors"
            :class="draftOnly ? 'bg-[var(--color-warning)]/40 border-[var(--color-warning)] text-[var(--color-warning)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Entries' }}
          </button>
        </div>

        <!-- Entry List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="sidebarLoading" class="p-4 text-center text-xs text-[var(--color-text-muted)]">Loading...</div>
          <div v-else-if="!sidebarEntries.length" class="p-4 text-center text-xs text-[var(--color-text-muted)] italic">No entries found</div>
          <div 
            v-for="(ent, idx) in sidebarEntries" 
            :key="ent.name"
            :ref="el => setSidebarEntryRef(el, idx)"
            @click="loadEntry(ent.name)"
            class="group cursor-pointer border-b border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 transition-colors hover:bg-[var(--color-surface)] outline-none focus:bg-[var(--color-surface)] focus:ring-1 focus:ring-[var(--color-info)]"
            :class="{ 'bg-[var(--color-surface)] border-l-2 border-l-blue-500': entryName === ent.name }"
            tabindex="0"
            @keydown.enter="loadEntry(ent.name)"
            @keydown.up.prevent="navigateSidebarEntry(idx, -1)"
            @keydown.down.prevent="navigateSidebarEntry(idx, 1)"
          >
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-1.5 truncate min-w-0">
                <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="ent.docstatus === 0 ? 'bg-[var(--color-warning)]' : 'bg-[var(--color-success)]'"></span>
                <span class="truncate font-mono text-[14px] font-bold text-[var(--color-info)]">{{ ent.name }}</span>
              </div>
              <span class="shrink-0 text-[10px] font-bold text-[var(--color-text-muted)] uppercase tabular-nums">{{ ent.modified?.split(' ')[1]?.slice(0,5) }}</span>
            </div>
            <div class="truncate text-[10px] text-[var(--color-text-muted)] uppercase tracking-tight">{{ ent.company }}</div>
          </div>
        </div>
    </aside>

    <!-- ===================== MAIN CONTENT ===================== -->
    <div class="flex flex-1 flex-col overflow-hidden">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="handleBack">&larr; Dashboard</button>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">Stock Reconciliation</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F7</kbd> Fetch</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <div class="flex items-center gap-8">
        <!-- Purpose -->
        <div class="flex items-center gap-2">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">Purpose</label>
          <select
            v-model="purpose"
            :disabled="entryDocStatus !== 0 || items.length > 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm font-bold text-[var(--color-info)] outline-none focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[150px]"
          >
            <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <!-- Warehouse -->
        <div class="flex items-center gap-2 border-l border-[var(--color-border)] pl-8">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">Warehouse</label>
          <select
            ref="warehouseSelect"
            v-model="warehouse"
            :disabled="entryDocStatus !== 0 || items.length > 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-lg font-bold text-[var(--color-info)] outline-none focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[250px]"
          >
            <option value="">-- Select Warehouse --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <button 
          @click="fetchItems" 
          :disabled="!warehouse || entryDocStatus !== 0 || items.length > 0"
          class="rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)] transition"
        >
          Fetch Items (F7)
        </button>

        <!-- Posting Date -->
        <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-8 ml-auto">
          <div class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm">
            <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</label>
            <div class="flex items-center gap-1">
              <button
                @click="changeDate(-1)"
                :disabled="entryDocStatus !== 0"
                class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all disabled:opacity-30"
                tabindex="-1"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
              </button>
              <input
                v-model="entryDate"
                type="date"
                :disabled="entryDocStatus !== 0"
                class="bg-transparent border-none text-sm font-bold text-[var(--color-text)] outline-none w-[125px] text-center focus:ring-0"
              />
              <button
                @click="changeDate(1)"
                :disabled="entryDocStatus !== 0"
                class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all disabled:opacity-30"
                tabindex="-1"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex flex-1 overflow-hidden bg-[var(--color-bg)]">
      <!-- MAIN CONTENT -->
      <div class="flex w-full flex-col p-4 overflow-hidden">
        <div class="flex-1 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm flex flex-col">
          <div class="flex-1 overflow-y-auto" ref="tableContainer">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                  <th class="w-12 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">#</th>
                  <th class="w-48 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Code</th>
                  <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Name</th>
                  <th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Curr Qty</th>
                  <th class="w-28 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">New Qty</th>
                  <th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Curr Rate</th>
                  <th class="w-28 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">New Rate</th>
                  <th class="w-20 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">UOM</th>
                  <th class="w-28 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Diff</th>
                  <th class="w-12 px-4 py-3 text-center"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="group border-b border-[var(--color-border)] last:border-0 outline-none transition-colors" :class="{ 'bg-[var(--color-info)]/30': selectedRow === idx, 'hover:bg-[var(--color-surface)]/40': selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-4 py-2 text-[var(--color-text-muted)] font-mono text-[10px]">{{ idx + 1 }}</td>
                  <td class="px-4 py-2">
                    <span class="font-mono font-semibold text-[var(--color-info)] truncate block w-40" :title="item.item_code" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-4 py-2">
                    <div class="text-[var(--color-text)] font-medium truncate max-w-[200px]" :title="item.item_name" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</div>
                  </td>
                  <td class="px-4 py-2 text-right font-mono text-[var(--color-text-muted)] text-[11px]">
                    {{ item.current_qty }}
                  </td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="entryDocStatus !== 0" step="any" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-[var(--color-text)] focus:border-[var(--color-info)] focus:bg-[var(--color-surface)] outline-none disabled:text-[var(--color-text-muted)] font-bold" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1, 'qty')" @keydown.up.prevent="moveRow(idx, -1, 'qty')" />
                  </td>
                  <td class="px-4 py-2 text-right font-mono text-[var(--color-text-muted)] text-[11px]">
                    {{ item.current_valuation_rate?.toFixed(2) }}
                  </td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.valuation_rate" :disabled="entryDocStatus !== 0" step="any"
                      class="w-full rounded border px-2 py-1 text-right font-bold text-[var(--color-text)] outline-none disabled:text-[var(--color-text-muted)] focus:bg-[var(--color-surface)]"
                      :class="item.qty > 0 && item.current_qty === 0 && !(item.valuation_rate > 0) && !(item.current_valuation_rate > 0)
                        ? 'border-[var(--color-danger)] bg-[var(--color-danger)]/20 focus:border-[var(--color-danger)]'
                        : 'border-transparent bg-transparent focus:border-[var(--color-info)]'"
                      :style="{ fontSize: dynamicRowStyle.fontSize }"
                      @keydown.enter.prevent="moveRow(idx, 1, 'qty')" @keydown.tab.prevent="moveRow(idx, 1, 'qty')" @keydown.down.prevent="moveRow(idx, 1, 'rate')" @keydown.up.prevent="moveRow(idx, -1, 'rate')" />
                  </td>
                  <td class="px-4 py-2 text-[var(--color-text-muted)] text-[11px]" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-4 py-2 text-right font-mono font-bold text-[11px]" :class="(item.qty - item.current_qty) > 0 ? 'text-[var(--color-success)]' : (item.qty - item.current_qty) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                    {{ (item.qty - item.current_qty).toFixed(2) }}
                  </td>
                  <td class="px-4 py-2 text-center">
                    <button v-if="entryDocStatus === 0" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] opacity-0 group-hover:opacity-100 transition" @click.stop="removeItem(idx)">&times;</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="entryDocStatus === 0" class="border-b border-[var(--color-border)] bg-[var(--color-info)]/10" :class="{ 'bg-[var(--color-info)]/30 ring-2 ring-inset ring-[var(--color-info)]': selectedRow === -1 }" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-4 py-3 text-[var(--color-info)] font-bold text-[10px]">+</td>
                  <td class="px-4 py-3">
                    <input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Item code" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveRow(items.length, -1, 'qty')" />
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-[var(--color-text-muted)] italic truncate max-w-[200px]" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ newPending.item_name || 'Search...' }}</div>
                  </td>
                  <td class="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-[11px]">
                    {{ newPending.current_qty }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <input ref="newQtyInput" v-model.number="newQty" type="number" step="any" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusNewRate" @keydown.tab.prevent="focusNewRate" />
                  </td>
                  <td class="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-[11px]">
                    {{ newPending.valuation_rate?.toFixed(2) }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <input ref="newRateInput" v-model.number="newRate" type="number" step="any" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="addNewItem" />
                  </td>
                  <td class="px-4 py-3 text-[var(--color-text-muted)] text-[11px]">{{ newPending.uom || '--' }}</td>
                  <td class="px-4 py-3 text-right font-mono font-bold text-[11px]" :class="(newQty - newPending.current_qty) > 0 ? 'text-[var(--color-success)]' : (newQty - newPending.current_qty) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                    {{ (newQty - newPending.current_qty).toFixed(2) }}
                  </td>
                  <td class="px-4 py-3"></td>
                </tr>
                <tr v-if="items.length === 0 && entryDocStatus !== 0" class="h-32 text-center text-[var(--color-text-muted)] italic">
                  <td colspan="10">No items in this reconciliation.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TABLE FOOTER -->
          <div class="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5">
            <div class="flex gap-8 items-center text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
              <span>Total Items: {{ items.length }}</span>
              <span>Adjusted: {{ adjustedCount }}</span>
            </div>
          </div>
        </div>

        <!-- BOTTOM PANEL -->
        <div class="mt-4 flex gap-4 h-[120px]">
          <div class="flex-[3] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm overflow-y-auto">
             <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Instructions</div>
             <ul class="text-xs text-[var(--color-text-muted)] list-disc list-inside space-y-1">
               <li>Select warehouse and fetch items to see current stock.</li>
               <li>Update the <span class="text-[var(--color-info)] font-bold">Target Qty</span> for items you want to reconcile.</li>
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
              class="flex-1 rounded-xl bg-[var(--color-info)] text-lg font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] active:scale-95 transition-all disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)]"
            >
              {{ entryName ? 'Update Draft' : 'Save Draft (Ctrl+S)' }}
            </button>
            <button
              v-if="entryName && entryDocStatus === 0"
              @click="submitEntry"
              class="h-12 rounded-xl bg-[var(--color-success)] text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-success)] active:scale-95 transition-all"
            >
              Submit / Apply Changes
            </button>
            <div class="flex gap-2 h-10">
              <button @click="startNewEntry" class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition">Clear All</button>
              <button @click="handleBack" class="flex-1 rounded-xl border border-[var(--color-danger)] bg-[var(--color-danger)]/20 text-xs font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/40 transition">Exit</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    </div>
  </div>

  <!-- Item Search Modal (opens when entered code is not found) -->
  <ItemSearch
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
import ItemSearch from '../components/ItemSearch.vue'

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

// ==================== REFS & FOCUS ====================
const inputRefs = {}
const rowRefs = {}
const warehouseSelect = ref(null)
const saveButton = ref(null)
const newCodeInput = ref(null)
const newQtyInput = ref(null)

function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarEntryRef(el, idx) { if (el) sidebarEntryRefs.set(idx, el); else sidebarEntryRefs.delete(idx) }

function focusField(f, idx) { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusWarehouse() { nextTick(() => warehouseSelect.value?.focus()) }
function focusNewCode()   { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty()    { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }

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

async function lookupItem(code) {
  try {
    return await frappeGet(`ssplbilling.api.stock_api.get_item_details`, { item_code: code, warehouse: warehouse.value })
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
      newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.valuation_rate }
      newQty.value = r.stock_qty
      newRate.value = r.valuation_rate
    }
  }, 300)
})

async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.valuation_rate }
    newQty.value = r.stock_qty
    newRate.value = r.valuation_rate
    focusNewQty()
  } else {
    // Item not found — open search modal with typed code as query
    showItemSearch.value = true
  }
}

async function onItemSearchSelect(item) {
  showItemSearch.value = false
  newItemCode.value = item.item_code
  const r = await lookupItem(item.item_code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, current_qty: r.stock_qty, valuation_rate: r.valuation_rate }
    newQty.value = r.stock_qty
    newRate.value = r.valuation_rate
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
      valuation_rate: i.valuation_rate || i.current_valuation_rate
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

  // Validate: items being set to qty > 0 from zero stock must have a valuation rate
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
