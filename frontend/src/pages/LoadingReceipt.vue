<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)]">

    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">Loading Receipt</span>
        <span v-if="docName" class="rounded bg-[var(--color-surface-raised)] px-2 py-0.5 font-mono text-xs text-[var(--color-info)]">{{ docName }}</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Tab</kbd> Next field</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">&uarr;&darr;</kbd> Row</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+Del</kbd> Delete row</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">End</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <!-- ── HEADER FIELDS BAR ─────────────────────────────────────── -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-4 shrink-0">
      <div class="flex flex-wrap items-end gap-10">

        <!-- Date -->
        <div class="flex flex-col gap-1.5">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Date</label>
          <input
            v-model="form.date"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] tabular-nums"
          />
        </div>

        <!-- Bill No -->
        <div class="flex flex-col gap-1.5">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Bill No</label>
          <input
            ref="billNoInput"
            v-model="form.bill_no"
            type="text"
            placeholder="Bill / Ref No"
            class="w-64 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            @keydown.enter.prevent="focusCustomer"
            @keydown.tab.exact.prevent="focusCustomer"
          />
        </div>

        <!-- Customer -->
        <div class="flex flex-col gap-1.5 relative" ref="customerWrap">
          <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Customer</label>
          <input
            ref="customerInput"
            v-model="customerQuery"
            type="text"
            placeholder="Click to search..."
            class="w-96 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] cursor-pointer"
            autocomplete="off"
            readonly
            @click="showCustomerModal = true"
            @keydown.enter.prevent="showCustomerModal = true"
            @keydown.space.prevent="showCustomerModal = true"
          />
        </div>

        <!-- Today Total -->
        <div class="ml-auto flex flex-col gap-1.5 items-end">
          <span class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Today</span>
          <span class="font-mono text-4xl font-black text-[var(--color-success)] leading-none mb-1">&#8377;{{ todayTotal.toFixed(2) }}</span>
        </div>

      </div>
    </div>

    <!-- ── BODY: SIDEBAR + MAIN ───────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── LEFT SIDEBAR (10%) ──────────────────────────────────── -->
      <aside class="flex w-[20%] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">

        <!-- Date navigator -->
        <div class="flex items-center justify-between border-b border-[var(--color-border)] px-1.5 py-3 shrink-0">
          <button
            class="flex h-10 w-10 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-xl font-bold"
            title="Previous day"
            @click="shiftDate(-1)"
          >&#8592;</button>
          <div class="flex flex-col items-center leading-none">
            <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date</span>
            <span class="text-lg font-bold text-[var(--color-text)] tabular-nums">{{ sidebarDateLabel }}</span>
            <DatePickerButton v-model="sidebarDate" label="Choose list date" />
          </div>
          <button
            class="flex h-10 w-10 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-xl font-bold"
            title="Next day"
            @click="shiftDate(1)"
          >&#8594;</button>
        </div>

        <!-- Receipt list -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="sidebarLoading" class="flex items-center justify-center py-12">
            <span class="text-sm text-[var(--color-text-muted)]">Loading...</span>
          </div>
          <div v-else-if="!sidebarReceipts.length" class="flex items-center justify-center py-12 px-2 text-center">
            <span class="text-sm italic text-[var(--color-text-muted)]">No receipts</span>
          </div>
          <div v-else class="flex flex-col divide-y divide-slate-700">
            <button
              v-for="r in sidebarReceipts"
              :key="r.name"
              class="w-full px-3 py-3 text-left transition"
              :class="docName === r.name
                ? 'bg-[var(--color-info)]/30 border-l-4 border-[var(--color-info)]'
                : 'hover:bg-[var(--color-surface-raised)] border-l-4 border-transparent'"
              @click="loadReceipt(r.name)"
            >
              <div class="flex items-center justify-between gap-1">
                <div class="truncate font-mono text-sm font-bold" :class="docName === r.name ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">{{ r.name }}</div>
                <div class="shrink-0 font-mono text-2xl font-black" :class="docName === r.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">&#8377;{{ (r.total || 0).toFixed(2) }}</div>
              </div>
              <div class="truncate text-2xl font-bold text-[var(--color-text)] mt-1">{{ r.customer_name || r.customer }}</div>
              <div v-if="r.bill_no" class="truncate text-lg font-bold text-[var(--color-text-muted)]">{{ r.bill_no }}</div>
            </button>
          </div>
        </div>

        <!-- Sidebar footer: count & total -->
        <div class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]/30 px-3 py-4 flex flex-col gap-2">
          <div class="flex items-center justify-between text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span>Count</span>
            <span>Day Total</span>
          </div>
          <div class="flex items-baseline justify-between font-bold">
            <span class="text-3xl text-[var(--color-text)]">{{ sidebarReceipts.length }} receipt{{ sidebarReceipts.length !== 1 ? 's' : '' }}</span>
            <span class="font-mono text-4xl text-[var(--color-success)]">&#8377;{{ sidebarTotal.toFixed(2) }}</span>
          </div>
        </div>
      </aside>

      <!-- ── MAIN CONTENT (90%) ──────────────────────────────────── -->
      <div class="flex flex-1 flex-col overflow-hidden p-4">
        <div class="flex-1 overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm flex flex-col">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-4xl border-collapse border border-[var(--color-border)]">
              <colgroup>
                <col style="width: 80px" />
                <col style="width: 280px" />
                <col />
                <col style="width: 160px" />
                <col style="width: 220px" />
                <col style="width: 260px" />
                <col style="width: 60px" />
              </colgroup>
              <thead>
                <tr class="sticky top-0 z-10 bg-[var(--color-surface-raised)]">
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-center text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">#</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-left text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-left text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Name</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-right text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Qty</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-right text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Rate</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0 text-right text-4xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Amount</th>
                  <th class="border border-[var(--color-border)] px-[1px] py-0"></th>
                </tr>
              </thead>
              <tbody>
                <!-- Existing rows: every cell is always editable -->
                <tr
                  v-for="(row, idx) in rows"
                  :key="row._k"
                  class="transition-colors"
                  :class="activeRow === idx ? 'bg-[var(--color-success)]/15' : 'hover:bg-[var(--color-surface-raised)]/40'"
                  @focusin="setActiveRow(idx)"
                >
                  <td class="border border-[var(--color-border)] px-[1px] py-0 text-center text-[var(--color-text-muted)] font-mono bg-[var(--color-surface-raised)]/50 leading-none">{{ idx + 1 }}</td>

                  <!-- Item code -->
                  <td class="border border-[var(--color-border)] px-0 py-0 relative">
                    <input
                      :ref="el => setRef(el, 'item', row._k)"
                      v-model="row.item"
                      :class="cellInput"
                      class="font-mono font-semibold"
                      @focus="selectAll"
                      @blur="closeRowDropdown"
                      @input="onRowItemInput(idx)"
                      @keydown.enter.prevent="onRowItemEnter(idx)"
                      @keydown.down.prevent="onRowItemDown(idx)"
                      @keydown.up.prevent="onRowItemUp(idx)"
                      @keydown.escape="onRowItemEscape"
                      @keydown.ctrl.delete.prevent="removeRow(idx)"
                    />
                    <div
                      v-if="itemDropdownIdx === idx && rowItemResults.length"
                      class="absolute left-0 top-full z-50 mt-1 w-[600px] overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
                    >
                      <div
                        v-for="(it, i) in rowItemResults"
                        :key="it.item_code"
                        class="cursor-pointer px-3 py-2 text-xl"
                        :class="i === rowItemHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
                        @mousedown.prevent="pickRowItem(idx, it)"
                        @mouseover="rowItemHighlight = i"
                      >
                        <div class="flex items-baseline gap-3">
                          <span class="font-mono font-semibold text-[27px] shrink-0">{{ it.item_code }}</span>
                          <span class="text-[22.5px] truncate" :class="i === rowItemHighlight ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ it.item_name }}</span>
                        </div>
                      </div>
                    </div>
                  </td>

                  <!-- Item name -->
                  <td class="border border-[var(--color-border)] px-0 py-0">
                    <input
                      :ref="el => setRef(el, 'item_name', row._k)"
                      v-model="row.item_name"
                      :class="cellInput"
                      class="truncate"
                      @focus="selectAll"
                      @keydown.enter.prevent="focusField('qty', idx)"
                      @keydown.down.prevent="moveRow('item_name', idx, 1)"
                      @keydown.up.prevent="moveRow('item_name', idx, -1)"
                      @keydown.ctrl.delete.prevent="removeRow(idx)"
                    />
                  </td>

                  <!-- Qty -->
                  <td class="border border-[var(--color-border)] px-0 py-0 font-mono">
                    <input
                      :ref="el => setRef(el, 'qty', row._k)"
                      v-model.number="row.qty"
                      type="number"
                      min="0"
                      step="any"
                      :class="cellInput"
                      class="text-right"
                      @focus="selectAll"
                      @wheel="$event.target.blur()"
                      @input="calcRowAmount(idx)"
                      @keydown.enter.prevent="focusField('rate', idx)"
                      @keydown.down.prevent="moveRow('qty', idx, 1)"
                      @keydown.up.prevent="moveRow('qty', idx, -1)"
                      @keydown.ctrl.delete.prevent="removeRow(idx)"
                    />
                  </td>

                  <!-- Rate -->
                  <td class="border border-[var(--color-border)] px-0 py-0 font-mono">
                    <input
                      :ref="el => setRef(el, 'rate', row._k)"
                      v-model.number="row.rate"
                      type="number"
                      min="0"
                      step="0.01"
                      :class="cellInput"
                      class="text-right"
                      @focus="selectAll"
                      @wheel="$event.target.blur()"
                      @input="calcRowAmount(idx)"
                      @keydown.enter.prevent="goToNextRow(idx)"
                      @keydown.down.prevent="moveRow('rate', idx, 1)"
                      @keydown.up.prevent="moveRow('rate', idx, -1)"
                      @keydown.ctrl.delete.prevent="removeRow(idx)"
                    />
                  </td>

                  <!-- Amount -->
                  <td class="border border-[var(--color-border)] px-[1px] py-0 text-right font-mono font-bold text-[var(--color-text)] bg-[var(--color-surface-raised)]/30 leading-none">{{ (row.amount || 0).toFixed(2) }}</td>

                  <!-- Delete -->
                  <td class="border border-[var(--color-border)] px-[1px] py-0 text-center">
                    <button
                      tabindex="-1"
                      title="Delete row (Ctrl+Del)"
                      class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition leading-none"
                      @click.stop="removeRow(idx)"
                    >&times;</button>
                  </td>
                </tr>

                <!-- NEW ROW -->
                <tr class="bg-[var(--color-info)]/5" @focusin="setActiveRow(-1)">
                  <td class="border border-[var(--color-border)] px-[1px] py-0 text-center text-[var(--color-info)] font-bold leading-none">+</td>
                  <td class="border border-[var(--color-border)] px-0 py-0 relative">
                    <input
                      ref="newItemInput"
                      v-model="newItem.item"
                      placeholder="Item..."
                      :class="cellInput"
                      class="font-mono"
                      @focus="selectAll"
                      @blur="newItemResults = []"
                      @input="onNewItemInput"
                      @keydown.enter.prevent="onNewItemEnter"
                      @keydown.tab.exact.prevent="focusNewQty"
                      @keydown.down.prevent="onNewItemDown"
                      @keydown.up.prevent="onNewItemUp"
                      @keydown.escape="onNewItemEscape"
                    />
                    <div
                      v-if="newItemResults.length"
                      class="absolute left-0 top-full z-50 mt-1 w-[600px] overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
                    >
                      <div
                        v-for="(it, i) in newItemResults"
                        :key="it.item_code"
                        class="cursor-pointer px-3 py-2 text-xl"
                        :class="i === newItemHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
                        @mousedown.prevent="pickNewItem(it)"
                        @mouseover="newItemHighlight = i"
                      >
                        <div class="flex items-baseline gap-3">
                          <span class="font-mono font-semibold text-[27px] shrink-0">{{ it.item_code }}</span>
                          <span class="text-[22.5px] truncate" :class="i === newItemHighlight ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ it.item_name }}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="border border-[var(--color-border)] px-0 py-0">
                    <input
                      ref="newNameInput"
                      v-model="newItem.item_name"
                      placeholder="Item name..."
                      :class="cellInput"
                      class="truncate"
                      @focus="selectAll"
                      @keydown.enter.prevent="focusNewQty"
                      @keydown.up.prevent="moveToLastRow('item_name')"
                    />
                  </td>
                  <td class="border border-[var(--color-border)] px-0 py-0">
                    <input
                      ref="newQtyInput"
                      v-model.number="newItem.qty"
                      type="number"
                      min="0"
                      step="any"
                      :class="cellInput"
                      class="text-right font-mono"
                      @focus="selectAll"
                      @wheel="$event.target.blur()"
                      @keydown.enter.prevent="addNewRow"
                      @keydown.tab.exact.prevent="focusNewRate"
                      @keydown.up.prevent="moveToLastRow('qty')"
                    />
                  </td>
                  <td class="border border-[var(--color-border)] px-0 py-0">
                    <input
                      ref="newRateInput"
                      v-model.number="newItem.rate"
                      type="number"
                      min="0"
                      step="0.01"
                      :class="cellInput"
                      class="text-right font-mono"
                      @focus="selectAll"
                      @wheel="$event.target.blur()"
                      @keydown.enter.prevent="addNewRow"
                      @keydown.up.prevent="moveToLastRow('rate')"
                    />
                  </td>
                  <td class="border border-[var(--color-border)] px-[1px] py-0 text-right font-mono text-[var(--color-text-muted)] font-bold bg-[var(--color-surface-raised)]/30 leading-none">{{ ((newItem.qty || 0) * (newItem.rate || 0)).toFixed(2) }}</td>
                  <td class="border border-[var(--color-border)] px-[1px] py-0"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TABLE FOOTER -->
          <div class="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 shrink-0">
            <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Items: {{ rows.length }}</span>
            <div class="flex items-baseline gap-2">
              <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Total:</span>
              <span class="text-2xl font-mono font-black text-[var(--color-text)]">&#8377;{{ grandTotal.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- BOTTOM ACTIONS -->
        <div class="mt-4 flex gap-3 justify-between items-center shrink-0">
          <div>
            <button
              @click="showItemManager = true"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-info)]/10 px-6 py-2.5 text-sm font-bold text-[var(--color-info)] hover:bg-[var(--color-info)]/20 transition flex items-center gap-2"
            >
              📦 Master Items
            </button>
          </div>
          <div class="flex gap-3">
            <button
              @click="clearForm"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
            >Clear</button>
            <button
              v-if="docName"
              @click="showPrint = true; pendingClearAfterPrint = false"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-6 py-2.5 text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition flex items-center gap-2"
            >🖨 Print</button>
            <button
              ref="saveBtn"
              @click="saveReceipt"
              :disabled="saving"
              class="rounded-xl bg-[var(--color-info)] px-8 py-2.5 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] active:scale-95 transition-all disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)]"
            >
              {{ saving ? 'Saving...' : docName ? 'Update Receipt' : 'Save Receipt' }}
            </button>
          </div>
        </div>
      </div>
    </div>

  <!-- ── PRINT MODAL ───────────────────────────────────────────── -->
  <PrintOptionsModal
    v-if="showPrint && docName"
    :invoice-name="docName"
    doctype="Loading Receipt"
    @close="closePrintModal"
  />

  <CustomerSearchModal
    v-if="showCustomerModal"
    :show="showCustomerModal"
    :skip-date-filter="true"
    initial-type="All"
    :allowed-types="['Customer', 'Supplier']"
    @close="showCustomerModal = false"
    @select="onCustomerSelected"
  />

  <LoadingItemManager
    v-if="showItemManager"
    :show="showItemManager"
    @close="showItemManager = false"
  />

  </div>
</template>

<script setup>
import { serverToday, toLocalISO, parseCalendarDate } from '../services/serverTime'
import DatePickerButton from '../components/DatePickerButton.vue'
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import LoadingItemManager from '../components/LoadingItemManager.vue'

import { formatDMY } from '../utils/date'
const router = useRouter()
const API = 'ssplbilling.api.loading_receipt_api'

// ── HELPERS ─────────────────────────────────────────────────────────
const today = serverToday()

function addDays(dateStr, n) {
  const d = parseCalendarDate(dateStr)
  d.setDate(d.getDate() + n)
  return toLocalISO(d)
}

function formatDateLabel(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  const t = new Date(today + 'T00:00:00')
  const diff = Math.round((d - t) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff === 1) return 'Tomorrow'
  return formatDMY(dateStr, '')
}

// ── TODAY'S TOTAL ────────────────────────────────────────────────────
const todayTotal = ref(0)

async function fetchTodayTotal() {
  try {
    const receipts = await frappePost(`${API}.get_loading_receipts`, { date: today, query: '' })
    todayTotal.value = (receipts || []).reduce((s, r) => s + (r.total || 0), 0)
  } catch {
    todayTotal.value = 0
  }
}

// ── FORM STATE ───────────────────────────────────────────────────────
const emptyForm = () => ({ date: today, bill_no: '', customer: '', customer_name: '', party_type: 'Customer', time: '' })
const form = ref(emptyForm())
const rows = ref([])
const docName = ref(null)
const saving = ref(false)
const activeRow = ref(-1)
const showPrint = ref(false)
const showCustomerModal = ref(false)
const showItemManager = ref(false)
const pendingClearAfterPrint = ref(false)

// Every grid cell is an input; the focused one gets a solid fill
const cellInput = 'w-full bg-transparent px-[1px] text-[var(--color-text)] outline-none leading-none focus:bg-[var(--color-info)] focus:text-[var(--color-text-on-highlight)]'

// Stable per-row key so refs and inputs survive row deletion
let rowSeq = 0
const withKey = r => ({ ...r, _k: ++rowSeq })

// ── DIRTY TRACKING ───────────────────────────────────────────────────
const snapshot = () => JSON.stringify({ form: form.value, rows: rows.value.map(({ _k, ...r }) => r) })
const savedSnapshot = ref(snapshot())
const isDirty = computed(() => snapshot() !== savedSnapshot.value)
function markClean() { savedSnapshot.value = snapshot() }
function confirmDiscard(msg = 'Discard unsaved changes?') { return !isDirty.value || confirm(msg) }

// customer search
const customerQuery = ref('')

// item search (new row)
const newItem = ref({ item: '', item_name: '', qty: 1, rate: 0 })
const newItemResults = ref([])
const newItemHighlight = ref(0)
let newItemTimer = null

// item search (existing row)
const rowItemResults = ref([])
const rowItemHighlight = ref(0)
const itemDropdownIdx = ref(null)
let rowItemTimer = null

// refs
const inputRefs = {}
const billNoInput = ref(null)
const customerInput = ref(null)
const newItemInput = ref(null)
const newNameInput = ref(null)
const newQtyInput = ref(null)
const newRateInput = ref(null)
const saveBtn = ref(null)

// ── SIDEBAR STATE ────────────────────────────────────────────────────
const sidebarDate = ref(today)
const sidebarReceipts = ref([])
const sidebarLoading = ref(false)
const sidebarDateLabel = computed(() => formatDateLabel(sidebarDate.value))

async function fetchSidebarReceipts() {
  sidebarLoading.value = true
  try {
    sidebarReceipts.value = await frappePost(`${API}.get_loading_receipts`, { date: sidebarDate.value, query: '' })
  } catch {
    sidebarReceipts.value = []
  } finally {
    sidebarLoading.value = false
  }
}

function shiftDate(n) {
  sidebarDate.value = addDays(sidebarDate.value, n)
}

watch(sidebarDate, fetchSidebarReceipts)

// ── COMPUTED ─────────────────────────────────────────────────────────
const grandTotal = computed(() => rows.value.reduce((s, r) => s + (r.amount || 0), 0))
const sidebarTotal = computed(() => sidebarReceipts.value.reduce((s, r) => s + (r.total || 0), 0))

// ── REF HELPERS ──────────────────────────────────────────────────────
const NEW_ROW_REFS = { item: newItemInput, item_name: newNameInput, qty: newQtyInput, rate: newRateInput }

function setRef(el, type, key) { const k = `${type}-${key}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function focusEl(el)           { el?.focus(); el?.select?.() }
function focusField(f, idx)    { nextTick(() => focusEl(inputRefs[`${f}-${rows.value[idx]?._k}`])) }
function focusNewField(f)      { nextTick(() => focusEl(NEW_ROW_REFS[f]?.value)) }
function focusBillNo()         { nextTick(() => focusEl(billNoInput.value)) }
function focusCustomer()       { nextTick(() => { customerInput.value?.focus() }) }
function focusNewItem()        { focusNewField('item') }
function focusNewQty()         { focusNewField('qty') }
function focusNewRate()        { focusNewField('rate') }
function selectAll(e)          { e.target.select() }

// ── ROW NAVIGATION ───────────────────────────────────────────────────
function setActiveRow(idx) {
  if (activeRow.value === idx) return
  activeRow.value = idx
  rowItemResults.value = []
  itemDropdownIdx.value = null
}
// Move up/down staying in the same column; past the last row lands in the new row
function moveRow(field, from, dir) {
  const next = from + dir
  if (next >= 0 && next < rows.value.length) focusField(field, next)
  else if (dir === 1) focusNewField(field)
}
function moveToLastRow(field = 'item') {
  if (rows.value.length) focusField(field, rows.value.length - 1)
}
function goToNextRow(from) {
  if (from + 1 < rows.value.length) focusField('item', from + 1)
  else focusNewItem()
}

// ── AMOUNT CALC ──────────────────────────────────────────────────────
function calcRowAmount(idx) {
  const r = rows.value[idx]
  r.amount = (r.qty || 0) * (r.rate || 0)
}

function removeRow(idx) {
  rows.value.splice(idx, 1)
  activeRow.value = -1
  if (idx < rows.value.length) focusField('item', idx)
  else focusNewItem()
}

// ── CUSTOMER SEARCH ──────────────────────────────────────────────────
function onCustomerSelected(c) {
  if (!c) return
  form.value.customer = c.name
  form.value.customer_name = c.label || c.customer_name
  form.value.party_type = c.type || 'Customer'
  customerQuery.value = c.label || c.customer_name
  showCustomerModal.value = false
  focusNewItem()
}

// ── ITEM SEARCH (new row) ────────────────────────────────────────────
function onNewItemInput() {
  clearTimeout(newItemTimer)
  newItemHighlight.value = 0
  newItem.value.item_name = ''
  if (!newItem.value.item.trim()) { newItemResults.value = []; return }
  newItemTimer = setTimeout(async () => {
    try {
      const res = await frappePost(`${API}.search_loading_items`, { query: newItem.value.item })
      newItemResults.value = res || []
    } catch { newItemResults.value = [] }
  }, 250)
}

function onNewItemEnter() {
  if (newItemResults.value.length) pickNewItem(newItemResults.value[newItemHighlight.value])
  else focusNewQty()
}

function onNewItemDown() {
  if (newItemResults.value.length) {
    newItemHighlight.value = (newItemHighlight.value + 1) % newItemResults.value.length
  }
}

function onNewItemUp() {
  if (newItemResults.value.length) {
    newItemHighlight.value = (newItemHighlight.value - 1 + newItemResults.value.length) % newItemResults.value.length
  } else {
    moveToLastRow()
  }
}

// Esc with the dropdown open only closes it; it must not reach the page-level "back" handler
function onNewItemEscape(e) {
  if (newItemResults.value.length) { e.stopPropagation(); newItemResults.value = [] }
}

function pickNewItem(it) {
  newItem.value.item = it.item_code
  newItem.value.item_name = it.item_name
  newItem.value.rate = it.rate || 0
  newItemResults.value = []
  focusNewQty()
}

function addNewRow() {
  if (!newItem.value.item) return
  const amount = (newItem.value.qty || 0) * (newItem.value.rate || 0)
  rows.value.push(withKey({
    item: newItem.value.item,
    item_name: newItem.value.item_name,
    qty: newItem.value.qty || 1,
    rate: newItem.value.rate || 0,
    amount,
  }))
  newItem.value = { item: '', item_name: '', qty: 1, rate: 0 }
  newItemResults.value = []
  focusNewItem()
}

// ── ITEM SEARCH (existing row) ───────────────────────────────────────
function onRowItemInput(idx) {
  clearTimeout(rowItemTimer)
  rowItemHighlight.value = 0
  itemDropdownIdx.value = idx
  const q = rows.value[idx].item.trim()
  if (!q) { rowItemResults.value = []; return }
  rowItemTimer = setTimeout(async () => {
    try {
      const res = await frappePost(`${API}.search_loading_items`, { query: q })
      // ignore results that arrive after the user left this cell
      if (itemDropdownIdx.value === idx) rowItemResults.value = res || []
    } catch { rowItemResults.value = [] }
  }, 250)
}

function closeRowDropdown() {
  clearTimeout(rowItemTimer)
  rowItemResults.value = []
  itemDropdownIdx.value = null
}

function rowDropdownOpen(idx) {
  return itemDropdownIdx.value === idx && rowItemResults.value.length > 0
}

function onRowItemEnter(idx) {
  if (rowDropdownOpen(idx)) pickRowItem(idx, rowItemResults.value[rowItemHighlight.value])
  else focusField('item_name', idx)
}

function onRowItemDown(idx) {
  if (rowDropdownOpen(idx)) {
    rowItemHighlight.value = (rowItemHighlight.value + 1) % rowItemResults.value.length
  } else {
    moveRow('item', idx, 1)
  }
}

function onRowItemUp(idx) {
  if (rowDropdownOpen(idx)) {
    rowItemHighlight.value = (rowItemHighlight.value - 1 + rowItemResults.value.length) % rowItemResults.value.length
  } else {
    moveRow('item', idx, -1)
  }
}

function onRowItemEscape(e) {
  if (rowItemResults.value.length) { e.stopPropagation(); closeRowDropdown() }
}

function pickRowItem(idx, it) {
  rows.value[idx].item = it.item_code
  rows.value[idx].item_name = it.item_name
  rows.value[idx].rate = it.rate || 0
  calcRowAmount(idx)
  closeRowDropdown()
  focusField('qty', idx)
}

// ── SAVE / LOAD ──────────────────────────────────────────────────────
async function saveReceipt() {
  if (!form.value.customer) { alert('Select a customer'); return }
  if (!rows.value.length) { alert('Add at least one item'); return }

  saving.value = true
  try {
    const payload = {
      name: docName.value,
      ...form.value,
      amount: grandTotal.value,
      total: grandTotal.value,
      loading_items: rows.value.map(({ _k, ...r }) => r),
    }
    const method = docName.value ? 'update_loading_receipt' : 'create_loading_receipt'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    docName.value = res.name
    markClean()
    // sync sidebar to the saved receipt's date
    sidebarDate.value = form.value.date
    await Promise.all([fetchSidebarReceipts(), fetchTodayTotal()])
    pendingClearAfterPrint.value = true
    showPrint.value = true
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  form.value = emptyForm()
  customerQuery.value = ''
  rows.value = []
  newItem.value = { item: '', item_name: '', qty: 1, rate: 0 }
  docName.value = null
  activeRow.value = -1
  pendingClearAfterPrint.value = false
  markClean()
  nextTick(focusBillNo)
}

function clearForm() {
  if (!confirmDiscard('Clear all data and start a new receipt?')) return
  resetForm()
}

async function loadReceipt(name) {
  if (name === docName.value) return
  if (!confirmDiscard('Discard unsaved changes and open ' + name + '?')) return
  try {
    const d = await frappePost(`${API}.get_loading_receipt`, { name })
    docName.value = d.name
    form.value = {
      date: d.date,
      time: d.time || '',
      bill_no: d.bill_no || '',
      party_type: d.party_type || 'Customer',
      customer: d.customer,
      customer_name: d.customer_name,
    }
    customerQuery.value = d.customer_name || d.customer
    rows.value = d.loading_items.map(withKey)
    activeRow.value = -1
    pendingClearAfterPrint.value = false
    markClean()
    // land on the first row so the operator can start editing right away
    if (rows.value.length) focusField('item', 0)
    else focusNewItem()
  } catch (e) {
    alert(e.message || 'Failed to load receipt')
  }
}

function closePrintModal() {
  showPrint.value = false
  if (pendingClearAfterPrint.value) resetForm()
}

// ── KEYBOARD SHORTCUTS ───────────────────────────────────────────────
// End saves, unless the caret sits mid-text in a text field (then End just moves the caret)
function endShouldSave(el) {
  if (!el || el.tagName !== 'INPUT' || el.type !== 'text') return true
  return el.selectionEnd == null || el.selectionEnd >= el.value.length
}

function onKeydown(e) {
  if (showPrint.value || showCustomerModal.value || showItemManager.value) return
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveReceipt() }
  if (e.key === 'End' && !e.shiftKey && endShouldSave(e.target)) { e.preventDefault(); saveReceipt() }
  if (e.key === 'Escape' && confirmDiscard('Discard unsaved changes and go back?')) { router.push('/') }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  fetchSidebarReceipts()
  fetchTodayTotal()
  nextTick(focusBillNo)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
