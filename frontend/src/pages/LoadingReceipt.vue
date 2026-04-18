<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)]">

    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">Loading Receipt</span>
        <span v-if="docName" class="rounded bg-[var(--color-surface-raised)] px-2 py-0.5 font-mono text-xs text-[var(--color-info)]">{{ docName }}</span>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <div class="flex items-center gap-1.5">
          <span class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Today</span>
          <span class="font-mono text-sm font-black text-[var(--color-success)]">&#8377;{{ todayTotal.toFixed(2) }}</span>
        </div>
      </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Tab</kbd> Next field</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">End</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <!-- ── HEADER FIELDS BAR ─────────────────────────────────────── -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 shrink-0">
      <div class="flex flex-wrap items-end gap-6">

        <!-- Date -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Date</label>
          <input
            v-model="form.date"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] tabular-nums"
          />
        </div>

        <!-- Time -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Time</label>
          <input
            v-model="form.time"
            type="time"
            step="1"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] tabular-nums"
          />
        </div>

        <!-- Bill No -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Bill No</label>
          <input
            ref="billNoInput"
            v-model="form.bill_no"
            type="text"
            placeholder="Bill / Ref No"
            class="w-36 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            @keydown.enter.prevent="focusCustomer"
            @keydown.tab.prevent="focusCustomer"
          />
        </div>

        <!-- Customer -->
        <div class="flex flex-col gap-1 relative" ref="customerWrap">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Customer</label>
          <input
            ref="customerInput"
            v-model="customerQuery"
            type="text"
            placeholder="Search customer..."
            class="w-56 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            autocomplete="off"
            @input="onCustomerInput"
            @keydown.down.prevent="customerHighlight = Math.min(customerHighlight + 1, customerResults.length - 1)"
            @keydown.up.prevent="customerHighlight = Math.max(customerHighlight - 1, 0)"
            @keydown.enter.prevent="onCustomerEnter"
            @keydown.escape="customerResults = []"
            @blur="onCustomerBlur"
          />
          <div
            v-if="customerResults.length"
            class="absolute left-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
          >
            <div
              v-for="(c, i) in customerResults"
              :key="c.name"
              class="cursor-pointer px-4 py-2.5 text-sm"
              :class="i === customerHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
              @mousedown.prevent="pickCustomer(c)"
              @mouseover="customerHighlight = i"
            >
              <div class="font-semibold">{{ c.customer_name }}</div>
              <div class="text-[10px] font-mono" :class="i === customerHighlight ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ c.name }}</div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ── BODY: SIDEBAR + MAIN ───────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── LEFT SIDEBAR (10%) ──────────────────────────────────── -->
      <aside class="flex w-[20%] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">

        <!-- Date navigator -->
        <div class="flex items-center justify-between border-b border-[var(--color-border)] px-1.5 py-2 shrink-0">
          <button
            class="flex h-7 w-7 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-base font-bold"
            title="Previous day"
            @click="shiftDate(-1)"
          >&#8592;</button>
          <div class="flex flex-col items-center leading-none">
            <span class="text-[9px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] tabular-nums">{{ sidebarDateLabel }}</span>
          </div>
          <button
            class="flex h-7 w-7 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-base font-bold"
            title="Next day"
            @click="shiftDate(1)"
          >&#8594;</button>
        </div>

        <!-- Receipt list -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="sidebarLoading" class="flex items-center justify-center py-8">
            <span class="text-[10px] text-[var(--color-text-muted)]">Loading...</span>
          </div>
          <div v-else-if="!sidebarReceipts.length" class="flex items-center justify-center py-8 px-2 text-center">
            <span class="text-[10px] italic text-[var(--color-text-muted)]">No receipts</span>
          </div>
          <div v-else class="flex flex-col divide-y divide-slate-700">
            <button
              v-for="r in sidebarReceipts"
              :key="r.name"
              class="w-full px-2 py-2 text-left transition"
              :class="docName === r.name
                ? 'bg-[var(--color-info)]/30 border-l-2 border-[var(--color-info)]'
                : 'hover:bg-[var(--color-surface-raised)] border-l-2 border-transparent'"
              @click="loadReceipt(r.name)"
            >
              <div class="flex items-center justify-between gap-1">
                <div class="truncate font-mono text-[10px] font-bold" :class="docName === r.name ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">{{ r.name }}</div>
                <div class="shrink-0 font-mono text-[10px] font-bold" :class="docName === r.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">&#8377;{{ (r.total || 0).toFixed(2) }}</div>
              </div>
              <div class="truncate text-[10px] text-[var(--color-text)] mt-0.5">{{ r.customer_name || r.customer }}</div>
              <div v-if="r.bill_no" class="truncate text-[9px] text-[var(--color-text-muted)]">{{ r.bill_no }}</div>
            </button>
          </div>
        </div>

        <!-- Sidebar footer: count -->
        <div class="shrink-0 border-t border-[var(--color-border)] px-2 py-1.5 text-center">
          <span class="text-[9px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">{{ sidebarReceipts.length }} receipt{{ sidebarReceipts.length !== 1 ? 's' : '' }}</span>
        </div>
      </aside>

      <!-- ── MAIN CONTENT (90%) ──────────────────────────────────── -->
      <div class="flex flex-1 flex-col overflow-hidden p-4">
        <div class="flex-1 overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm flex flex-col">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-xs border-collapse border border-[var(--color-border)]">
              <colgroup>
                <col style="width: 40px" />
                <col style="width: 160px" />
                <col />
                <col style="width: 100px" />
                <col style="width: 120px" />
                <col style="width: 140px" />
                <col style="width: 40px" />
              </colgroup>
              <thead>
                <tr class="sticky top-0 z-10 bg-[var(--color-surface-raised)]">
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-center text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">#</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-left text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-left text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Name</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-right text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Qty</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-right text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Rate</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5 text-right text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Amount</th>
                  <th class="border border-[var(--color-border)] px-2 py-1.5"></th>
                </tr>
              </thead>
              <tbody>
                <!-- Existing rows -->
                <tr
                  v-for="(row, idx) in rows"
                  :key="idx"
                  :ref="el => setRowRef(el, idx)"
                  tabindex="-1"
                  class="group outline-none transition-colors"
                  :class="selectedRow === idx ? 'bg-[var(--color-info)]/10' : 'hover:bg-[var(--color-surface)]/40'"
                  @click="selectRow(idx)"
                  @keydown="onRowKeydown($event, idx)"
                >
                  <td class="border border-[var(--color-border)] px-2 py-1 text-center text-[var(--color-text-muted)] font-mono bg-[var(--color-surface-raised)]/50">{{ idx + 1 }}</td>

                  <!-- Item code -->
                  <td class="border border-[var(--color-border)] px-1 py-1 relative" :class="{ 'ring-2 ring-inset ring-[var(--color-info)]': selectedRow === idx }">
                    <div v-if="selectedRow === idx" class="relative">
                      <input
                        :ref="el => setRef(el, 'item', idx)"
                        v-model="row.item"
                        class="w-full bg-transparent px-1 font-mono text-[var(--color-text)] outline-none"
                        @input="onRowItemInput(idx)"
                        @keydown.enter.prevent="onRowItemEnter(idx)"
                        @keydown.tab.prevent="focusField('qty', idx)"
                        @keydown.down.prevent="moveRow(idx, 1)"
                        @keydown.up.prevent="moveRow(idx, -1)"
                        @keydown.escape="itemDropdownIdx = null"
                      />
                      <div
                        v-if="itemDropdownIdx === idx && rowItemResults.length"
                        class="absolute left-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
                      >
                        <div
                          v-for="(it, i) in rowItemResults"
                          :key="it.item_code"
                          class="cursor-pointer px-3 py-1.5 text-xs"
                          :class="i === rowItemHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
                          @mousedown.prevent="pickRowItem(idx, it)"
                          @mouseover="rowItemHighlight = i"
                        >
                          <div class="font-mono font-semibold">{{ it.item_code }}</div>
                          <div class="text-[10px]" :class="i === rowItemHighlight ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ it.item_name }}</div>
                        </div>
                      </div>
                    </div>
                    <span v-else class="px-1 font-mono font-semibold text-[var(--color-info)]">{{ row.item || '--' }}</span>
                  </td>

                  <!-- Item name -->
                  <td class="border border-[var(--color-border)] px-1 py-1" :class="{ 'ring-2 ring-inset ring-[var(--color-info)]': selectedRow === idx }">
                    <input
                      v-if="selectedRow === idx"
                      :ref="el => setRef(el, 'item_name', idx)"
                      v-model="row.item_name"
                      class="w-full bg-transparent px-1 text-[var(--color-text)] outline-none"
                      @keydown.enter.prevent="focusField('qty', idx)"
                      @keydown.tab.prevent="focusField('qty', idx)"
                      @keydown.down.prevent="moveRow(idx, 1)"
                      @keydown.up.prevent="moveRow(idx, -1)"
                    />
                    <span v-else class="px-1 text-[var(--color-text)]">{{ row.item_name || '--' }}</span>
                  </td>

                  <!-- Qty -->
                  <td class="border border-[var(--color-border)] px-1 py-1 text-right font-mono" :class="{ 'ring-2 ring-inset ring-[var(--color-info)]': selectedRow === idx }">
                    <input
                      v-if="selectedRow === idx"
                      :ref="el => setRef(el, 'qty', idx)"
                      v-model.number="row.qty"
                      type="number"
                      min="0"
                      step="any"
                      class="w-full bg-transparent px-1 text-right text-[var(--color-text)] outline-none"
                      @input="calcRowAmount(idx)"
                      @keydown.enter.prevent="focusField('rate', idx)"
                      @keydown.tab.prevent="focusField('rate', idx)"
                      @keydown.down.prevent="moveRow(idx, 1)"
                      @keydown.up.prevent="moveRow(idx, -1)"
                    />
                    <span v-else class="px-1 text-[var(--color-text)]">{{ row.qty }}</span>
                  </td>

                  <!-- Rate -->
                  <td class="border border-[var(--color-border)] px-1 py-1 text-right font-mono" :class="{ 'ring-2 ring-inset ring-[var(--color-info)]': selectedRow === idx }">
                    <input
                      v-if="selectedRow === idx"
                      :ref="el => setRef(el, 'rate', idx)"
                      v-model.number="row.rate"
                      type="number"
                      min="0"
                      step="0.01"
                      class="w-full bg-transparent px-1 text-right text-[var(--color-text)] outline-none"
                      @input="calcRowAmount(idx)"
                      @keydown.enter.prevent="goToNextRow(idx)"
                      @keydown.tab.prevent="goToNextRow(idx)"
                      @keydown.down.prevent="moveRow(idx, 1)"
                      @keydown.up.prevent="moveRow(idx, -1)"
                    />
                    <span v-else class="px-1 text-[var(--color-text)]">{{ (row.rate || 0).toFixed(2) }}</span>
                  </td>

                  <!-- Amount -->
                  <td class="border border-[var(--color-border)] px-2 py-1 text-right font-mono font-bold text-[var(--color-text)] bg-[var(--color-surface-raised)]/30">{{ (row.amount || 0).toFixed(2) }}</td>

                  <!-- Delete -->
                  <td class="border border-[var(--color-border)] px-2 py-1 text-center">
                    <button
                      class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition"
                      @click.stop="removeRow(idx)"
                    >&times;</button>
                  </td>
                </tr>

                <!-- NEW ROW -->
                <tr class="bg-[var(--color-info)]/5">
                  <td class="border border-[var(--color-border)] px-2 py-1.5 text-center text-[var(--color-info)] font-bold">+</td>
                  <td class="border border-[var(--color-border)] px-1 py-1 relative">
                    <input
                      ref="newItemInput"
                      v-model="newItem.item"
                      placeholder="Item..."
                      class="w-full bg-transparent px-1 font-mono text-[var(--color-text)] outline-none"
                      @input="onNewItemInput"
                      @keydown.enter.prevent="onNewItemEnter"
                      @keydown.tab.prevent="focusNewQty"
                      @keydown.up.prevent="moveToLastRow"
                      @keydown.escape="newItemResults = []"
                    />
                    <div
                      v-if="newItemResults.length"
                      class="absolute left-0 top-full z-50 mt-1 w-72 overflow-hidden rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
                    >
                      <div
                        v-for="(it, i) in newItemResults"
                        :key="it.item_code"
                        class="cursor-pointer px-3 py-1.5 text-xs"
                        :class="i === newItemHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
                        @mousedown.prevent="pickNewItem(it)"
                        @mouseover="newItemHighlight = i"
                      >
                        <div class="font-mono font-semibold">{{ it.item_code }}</div>
                        <div class="text-[10px]" :class="i === newItemHighlight ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ it.item_name }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="border border-[var(--color-border)] px-2 py-1.5">
                    <div class="text-[var(--color-text-muted)] italic text-xs truncate">{{ newItem.item_name || 'Item name...' }}</div>
                  </td>
                  <td class="border border-[var(--color-border)] px-1 py-1 text-right">
                    <input
                      ref="newQtyInput"
                      v-model.number="newItem.qty"
                      type="number"
                      min="0"
                      step="any"
                      class="w-full bg-transparent px-1 text-right font-mono text-[var(--color-text)] outline-none"
                      @keydown.enter.prevent="addNewRow"
                      @keydown.tab.prevent="focusNewRate"
                    />
                  </td>
                  <td class="border border-[var(--color-border)] px-1 py-1 text-right">
                    <input
                      ref="newRateInput"
                      v-model.number="newItem.rate"
                      type="number"
                      min="0"
                      step="0.01"
                      class="w-full bg-transparent px-1 text-right font-mono text-[var(--color-text)] outline-none"
                      @keydown.enter.prevent="addNewRow"
                    />
                  </td>
                  <td class="border border-[var(--color-border)] px-2 py-1.5 text-right font-mono text-[var(--color-text-muted)] font-bold bg-[var(--color-surface-raised)]/30">{{ ((newItem.qty || 0) * (newItem.rate || 0)).toFixed(2) }}</td>
                  <td class="border border-[var(--color-border)] px-2 py-1.5"></td>
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
        <div class="mt-4 flex gap-3 justify-end shrink-0">
          <button
            @click="clearForm"
            class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5 text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
          >Clear</button>
          <button
            v-if="docName"
            @click="showPrint = true"
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

  <!-- ── PRINT MODAL ───────────────────────────────────────────── -->
  <PrintOptionsModal
    v-if="showPrint && docName"
    :invoice-name="docName"
    doctype="Loading Receipt"
    @close="showPrint = false"
  />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'

const router = useRouter()
const API = 'ssplbilling.api.loading_receipt_api'

// ── HELPERS ─────────────────────────────────────────────────────────
const today = new Date().toISOString().split('T')[0]
const nowTime = () => new Date().toTimeString().slice(0, 8)

function addDays(dateStr, n) {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

function formatDateLabel(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  const t = new Date(today + 'T00:00:00')
  const diff = Math.round((d - t) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff === 1) return 'Tomorrow'
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
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
const form = ref({ date: today, time: nowTime(), bill_no: '', customer: '' })
const rows = ref([])
const docName = ref(null)
const saving = ref(false)
const selectedRow = ref(-1)
const showPrint = ref(false)

// customer search
const customerQuery = ref('')
const customerResults = ref([])
const customerHighlight = ref(0)
let customerTimer = null

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
const rowRefs = {}
const billNoInput = ref(null)
const customerInput = ref(null)
const newItemInput = ref(null)
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

// ── REF HELPERS ──────────────────────────────────────────────────────
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function focusField(f, idx)    { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)         { nextTick(() => rowRefs[idx]?.focus()) }
function focusBillNo()         { nextTick(() => { billNoInput.value?.focus(); billNoInput.value?.select() }) }
function focusCustomer()       { nextTick(() => { customerInput.value?.focus(); customerInput.value?.select() }) }
function focusNewItem()        { nextTick(() => newItemInput.value?.focus()) }
function focusNewQty()         { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }
function focusNewRate()        { nextTick(() => { newRateInput.value?.focus(); newRateInput.value?.select() }) }

// ── ROW NAVIGATION ───────────────────────────────────────────────────
function selectRow(idx) { selectedRow.value = idx; focusRow(idx) }
function moveRow(from, dir) {
  const next = from + dir
  if (next >= 0 && next < rows.value.length) { selectedRow.value = next; focusRow(next) }
  else if (dir === 1) { selectedRow.value = -1; focusNewItem() }
}
function moveToLastRow() {
  if (rows.value.length) { selectedRow.value = rows.value.length - 1; focusRow(rows.value.length - 1) }
}
function goToNextRow(from) {
  const next = from + 1
  if (next < rows.value.length) { selectedRow.value = next; focusRow(next) }
  else { selectedRow.value = -1; focusNewItem() }
}
function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')  { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')    { e.preventDefault(); focusField('item', idx) }
}

// ── AMOUNT CALC ──────────────────────────────────────────────────────
function calcRowAmount(idx) {
  const r = rows.value[idx]
  r.amount = (r.qty || 0) * (r.rate || 0)
}

function removeRow(idx) {
  rows.value.splice(idx, 1)
  selectedRow.value = -1
}

// ── CUSTOMER SEARCH ──────────────────────────────────────────────────
function onCustomerInput() {
  clearTimeout(customerTimer)
  customerHighlight.value = 0
  if (!customerQuery.value.trim()) { customerResults.value = []; form.value.customer = ''; return }
  customerTimer = setTimeout(searchCustomers, 250)
}

async function searchCustomers() {
  try {
    const res = await frappeGet('frappe.client.get_list', {
      doctype: 'Customer',
      filters: [['customer_name', 'like', `%${customerQuery.value}%`]],
      fields: ['name', 'customer_name'],
      limit: 20,
    })
    customerResults.value = res
  } catch { customerResults.value = [] }
}

function onCustomerEnter() {
  if (customerResults.value.length) {
    pickCustomer(customerResults.value[customerHighlight.value])
  } else {
    focusNewItem()
  }
}

function pickCustomer(c) {
  if (!c) return
  form.value.customer = c.name
  customerQuery.value = c.customer_name
  customerResults.value = []
  focusNewItem()
}

function onCustomerBlur() {
  setTimeout(() => { customerResults.value = [] }, 150)
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
  rows.value.push({
    item: newItem.value.item,
    item_name: newItem.value.item_name,
    qty: newItem.value.qty || 1,
    rate: newItem.value.rate || 0,
    amount,
  })
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
      rowItemResults.value = res || []
    } catch { rowItemResults.value = [] }
  }, 250)
}

function onRowItemEnter(idx) {
  if (rowItemResults.value.length) pickRowItem(idx, rowItemResults.value[rowItemHighlight.value])
  else focusField('qty', idx)
}

function pickRowItem(idx, it) {
  rows.value[idx].item = it.item_code
  rows.value[idx].item_name = it.item_name
  rows.value[idx].rate = it.rate || 0
  calcRowAmount(idx)
  rowItemResults.value = []
  itemDropdownIdx.value = null
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
      loading_items: rows.value,
    }
    const method = docName.value ? 'update_loading_receipt' : 'create_loading_receipt'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    docName.value = res.name
    // sync sidebar to the saved receipt's date
    sidebarDate.value = form.value.date
    await Promise.all([fetchSidebarReceipts(), fetchTodayTotal()])
    showPrint.value = true
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function clearForm() {
  if (rows.value.length && !confirm('Clear all data and start a new receipt?')) return
  form.value = { date: today, time: nowTime(), bill_no: '', customer: '' }
  customerQuery.value = ''
  rows.value = []
  docName.value = null
  selectedRow.value = -1
  nextTick(focusBillNo)
}

async function loadReceipt(name) {
  try {
    const d = await frappePost(`${API}.get_loading_receipt`, { name })
    docName.value = d.name
    form.value = {
      date: d.date,
      time: d.time || nowTime(),
      bill_no: d.bill_no || '',
      customer: d.customer,
    }
    customerQuery.value = d.customer_name || d.customer
    rows.value = d.loading_items.map(r => ({ ...r }))
    selectedRow.value = -1
    nextTick(focusBillNo)
  } catch (e) {
    alert(e.message || 'Failed to load receipt')
  }
}

// ── KEYBOARD SHORTCUTS ───────────────────────────────────────────────
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveReceipt() }
  if (e.key === 'End') { e.preventDefault(); saveReceipt() }
  if (e.key === 'Escape') { router.push('/') }
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
