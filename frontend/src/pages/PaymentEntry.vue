<template>
  <div class="flex min-h-screen flex-col bg-gray-50" @keydown.f9.prevent="handleF9">

    <!-- ═══════ HEADER / MODE TABS ═══════ -->
    <header class="sticky top-0 z-40 flex h-12 items-stretch border-b border-gray-200 bg-white">

      <button
        @click="$router.push('/')"
        class="flex items-center gap-1 border-r border-gray-200 px-4 text-xs text-gray-400 hover:bg-gray-50 hover:text-gray-600"
      >
        ← Dashboard
      </button>

      <!-- Mode tabs -->
      <button
        v-for="m in MODES"
        :key="m.id"
        @click="switchMode(m.id)"
        class="relative flex items-center gap-2 border-r border-gray-200 px-6 text-sm font-semibold transition-colors focus:outline-none"
        :class="mode === m.id
          ? 'bg-white text-blue-700 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-600'
          : 'text-gray-400 hover:bg-gray-50 hover:text-gray-700'"
      >
        <span>{{ m.icon }}</span>
        <span>{{ m.label }}</span>
        <kbd class="rounded border border-current px-1 py-0.5 font-mono text-[9px] opacity-40">{{ m.key }}</kbd>
      </button>

      <!-- spacer -->
      <div class="flex-1"></div>

      <!-- Success / Error badge -->
      <div
        v-if="flashMsg"
        class="flex items-center px-4 text-xs font-semibold"
        :class="flashMsg.type === 'ok' ? 'text-green-600' : 'text-red-600'"
      >
        {{ flashMsg.text }}
      </div>

      <!-- Save button -->
      <button
        @click="save"
        :disabled="!canSave || saving"
        class="flex items-center gap-2 border-l border-gray-200 px-6 text-sm font-bold transition-colors"
        :class="canSave && !saving
          ? 'text-green-700 hover:bg-green-50 cursor-pointer'
          : 'text-gray-300 cursor-not-allowed'"
      >
        {{ saving ? 'Saving…' : 'Save' }}
        <kbd class="rounded border border-current px-1.5 py-0.5 font-mono text-[10px] opacity-60">F9</kbd>
      </button>
    </header>

    <!-- ═══════ BODY: two columns ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── LEFT PANEL: context-specific content ── -->
      <div class="flex-1 overflow-y-auto p-6">

        <!-- RECEIPT / PAYMENT: outstanding list -->
        <template v-if="mode === 'receipt' || mode === 'payment'">
          <div class="mb-3 flex items-center gap-3">
            <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
              Outstanding {{ mode === 'receipt' ? 'Invoices' : 'Bills' }}
            </span>
            <span v-if="form.partyName" class="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
              {{ form.partyName }}
            </span>
          </div>

          <div v-if="!form.party" class="flex flex-col items-center justify-center py-20 text-gray-300">
            <div class="mb-3 text-5xl">{{ mode === 'receipt' ? '👤' : '🏭' }}</div>
            <div class="text-sm">Select a {{ mode === 'receipt' ? 'customer' : 'supplier' }} →</div>
          </div>

          <div v-else-if="loadingInvoices" class="py-10 text-center text-sm text-gray-400">
            Loading…
          </div>

          <div v-else-if="!outstandingList.length" class="py-10 text-center text-sm text-gray-400">
            No outstanding {{ mode === 'receipt' ? 'invoices' : 'bills' }}.
          </div>

          <div v-else class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="inv in outstandingList"
              :key="inv.name"
              @click="selectInvoice(inv)"
              class="cursor-pointer rounded-xl border p-4 transition-all"
              :class="form.invoiceName === inv.name
                ? 'border-blue-400 bg-blue-50 shadow-sm'
                : 'border-gray-200 bg-white hover:border-blue-200 hover:bg-gray-50'"
            >
              <div class="mb-1 font-mono text-sm font-bold text-gray-800">{{ inv.name }}</div>
              <div class="text-[11px] text-gray-400">{{ fmtDate(inv.posting_date) }}</div>
              <div class="mt-2 flex items-end justify-between">
                <div>
                  <div class="text-[10px] text-gray-400">Outstanding</div>
                  <div class="text-lg font-bold text-red-600">₹{{ fmt(inv.outstanding_amount) }}</div>
                </div>
                <div class="text-right text-[10px] text-gray-400">
                  of ₹{{ fmt(inv.grand_total) }}
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- JOURNAL: account rows table -->
        <template v-else-if="mode === 'journal'">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-gray-400">Account Rows</span>
            <button
              @click="addJournalRow"
              class="rounded border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-600 hover:bg-gray-100"
            >
              + Add Row
            </button>
          </div>

          <!-- Header -->
          <div class="mb-1 grid grid-cols-[2fr_1fr_1fr_28px] gap-2 px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">
            <div>Account</div>
            <div class="text-right">Debit (Dr)</div>
            <div class="text-right">Credit (Cr)</div>
            <div></div>
          </div>

          <!-- Rows -->
          <div v-for="(row, idx) in form.rows" :key="idx" class="mb-1.5">
            <div class="grid grid-cols-[2fr_1fr_1fr_28px] items-center gap-2">
              <!-- Account autocomplete -->
              <div class="relative">
                <input
                  v-model="row.accountQuery"
                  @input="onAccountSearch(idx)"
                  @keydown.down.prevent="rowCursorDown(idx)"
                  @keydown.up.prevent="rowCursorUp(idx)"
                  @keydown.enter.prevent="pickRowAccount(idx)"
                  @keydown.escape="row.accountOpen = false"
                  @blur="() => setTimeout(() => { row.accountOpen = false }, 150)"
                  :placeholder="`Account ${idx + 1}`"
                  autocomplete="off"
                  class="w-full rounded border px-2 py-1.5 text-sm outline-none transition-colors focus:border-blue-500"
                  :class="row.account ? 'border-blue-300 bg-blue-50 text-blue-800' : 'border-gray-300'"
                />
                <ul
                  v-if="row.accountOpen && row.accountOptions.length"
                  class="absolute z-50 mt-0.5 max-h-44 w-full overflow-y-auto rounded border border-gray-200 bg-white shadow-lg"
                >
                  <li
                    v-for="(opt, i) in row.accountOptions"
                    :key="opt.name"
                    @mousedown.prevent="setRowAccount(idx, opt)"
                    class="cursor-pointer px-3 py-1.5 text-xs"
                    :class="row.accountCursor === i ? 'bg-blue-50' : 'hover:bg-gray-50'"
                  >
                    <span class="font-semibold text-gray-800">{{ opt.account_name }}</span>
                    <span class="ml-2 text-[10px] text-gray-400">{{ opt.account_type }}</span>
                  </li>
                </ul>
              </div>
              <!-- Debit -->
              <input
                v-model.number="row.debit"
                type="number"
                min="0"
                placeholder="0.00"
                @focus="row.credit = null"
                class="rounded border border-gray-300 px-2 py-1.5 text-right text-sm outline-none focus:border-blue-500"
              />
              <!-- Credit -->
              <input
                v-model.number="row.credit"
                type="number"
                min="0"
                placeholder="0.00"
                @focus="row.debit = null"
                class="rounded border border-gray-300 px-2 py-1.5 text-right text-sm outline-none focus:border-blue-500"
              />
              <!-- Delete -->
              <button
                @click="removeJournalRow(idx)"
                :disabled="form.rows.length <= 2"
                class="flex h-7 w-7 items-center justify-center rounded text-gray-300 transition-colors hover:bg-red-50 hover:text-red-500 disabled:opacity-20"
              >✕</button>
            </div>
          </div>

          <!-- Totals -->
          <div class="mt-3 grid grid-cols-[2fr_1fr_1fr_28px] gap-2 border-t-2 border-gray-200 pt-3 px-2">
            <div class="text-xs font-bold text-gray-500">Total</div>
            <div
              class="text-right text-sm font-bold font-mono"
              :class="journalBalanced ? 'text-gray-700' : 'text-red-600'"
            >₹{{ fmt(journalTotalDr) }}</div>
            <div
              class="text-right text-sm font-bold font-mono"
              :class="journalBalanced ? 'text-gray-700' : 'text-red-600'"
            >₹{{ fmt(journalTotalCr) }}</div>
            <div class="flex items-center justify-center text-sm">
              {{ journalBalanced ? '✓' : '⚠' }}
            </div>
          </div>
        </template>

        <!-- CONTRA: animated from→to diagram -->
        <template v-else-if="mode === 'contra'">
          <div class="flex flex-col items-center justify-center py-12">
            <div
              class="w-72 rounded-xl border-2 px-6 py-5 text-center transition-all"
              :class="form.fromAccount ? 'border-orange-300 bg-orange-50' : 'border-dashed border-gray-300 bg-white'"
            >
              <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">From Account</div>
              <div class="mt-2 text-base font-bold" :class="form.fromAccount ? 'text-orange-800' : 'text-gray-300'">
                {{ form.fromAccountName || '—' }}
              </div>
            </div>

            <div class="my-5 flex flex-col items-center gap-1 text-gray-400">
              <div class="h-8 w-px bg-gray-300"></div>
              <div
                class="rounded-full px-4 py-1.5 text-sm font-bold transition-all"
                :class="form.amount ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-400'"
              >
                ₹{{ fmt(form.amount || 0) }}
              </div>
              <div class="h-8 w-px bg-gray-300"></div>
              <div class="text-xl">↓</div>
            </div>

            <div
              class="w-72 rounded-xl border-2 px-6 py-5 text-center transition-all"
              :class="form.toAccount ? 'border-green-300 bg-green-50' : 'border-dashed border-gray-300 bg-white'"
            >
              <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400">To Account</div>
              <div class="mt-2 text-base font-bold" :class="form.toAccount ? 'text-green-800' : 'text-gray-300'">
                {{ form.toAccountName || '—' }}
              </div>
            </div>
          </div>
        </template>

      </div>

      <!-- ── RIGHT PANEL: keyboard form ── -->
      <div class="flex w-80 shrink-0 flex-col overflow-y-auto border-l border-gray-200 bg-white">
        <div class="flex-1 p-5">

          <!-- Date -->
          <div class="mb-4">
            <label class="field-lbl">Date</label>
            <input
              ref="dateRef"
              v-model="form.date"
              type="date"
              class="field-inp"
            />
          </div>

          <!-- Customer (Receipt) / Supplier (Payment) -->
          <div v-if="mode === 'receipt' || mode === 'payment'" class="mb-4">
            <label class="field-lbl">{{ mode === 'receipt' ? 'Customer' : 'Supplier' }}</label>
            <div class="relative">
              <input
                ref="partyRef"
                v-model="partyQuery"
                @input="onPartySearch"
                @keydown.down.prevent="partyCursorDown"
                @keydown.up.prevent="partyCursorUp"
                @keydown.enter.prevent="pickPartyCursor"
                @keydown.escape="partyDropdownOpen = false"
                @blur="onPartyBlur"
                :placeholder="`Search ${mode === 'receipt' ? 'customer' : 'supplier'}…`"
                autocomplete="off"
                class="field-inp pr-7"
                :class="form.party ? '!border-blue-400 bg-blue-50 font-semibold text-blue-800' : ''"
              />
              <button
                v-if="form.party"
                @click="clearParty"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-600"
              >✕</button>
              <ul
                v-if="partyDropdownOpen && partyOptions.length"
                class="absolute z-50 mt-0.5 max-h-44 w-full overflow-y-auto rounded border border-gray-200 bg-white shadow-lg"
              >
                <li
                  v-for="(c, i) in partyOptions"
                  :key="c.name"
                  @mousedown.prevent="pickParty(c)"
                  class="cursor-pointer px-3 py-2 text-xs"
                  :class="partyCursor === i ? 'bg-blue-50' : 'hover:bg-gray-50'"
                >
                  <div class="font-semibold text-gray-800">{{ c.customer_name || c.supplier_name }}</div>
                  <div class="font-mono text-[10px] text-gray-400">{{ c.name }}</div>
                </li>
              </ul>
            </div>
          </div>

          <!-- Amount (all except journal) -->
          <div v-if="mode !== 'journal'" class="mb-4">
            <label class="field-lbl">Amount (₹)</label>
            <input
              ref="amountRef"
              v-model.number="form.amount"
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              class="w-full rounded border border-gray-300 px-3 py-2 text-right text-2xl font-bold tracking-tight outline-none transition-colors focus:border-blue-500"
            />
          </div>

          <!-- Mode of Payment (Receipt / Payment) -->
          <div v-if="mode === 'receipt' || mode === 'payment'" class="mb-4">
            <label class="field-lbl">Mode of Payment</label>
            <div class="flex gap-1.5">
              <button
                v-for="m in MOPS"
                :key="m.id"
                @click="form.mop = m.id"
                class="flex-1 rounded border py-2 text-xs font-bold transition-colors"
                :class="form.mop === m.id
                  ? 'border-blue-500 bg-blue-600 text-white'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'"
              >
                {{ m.label }}
              </button>
            </div>
          </div>

          <!-- Link Invoice (Receipt / Payment, only if outstanding exist) -->
          <div v-if="(mode === 'receipt' || mode === 'payment') && outstandingList.length" class="mb-4">
            <label class="field-lbl">
              Link Invoice
              <span class="ml-1 font-normal text-gray-400">optional</span>
            </label>
            <select v-model="form.invoiceName" class="field-inp">
              <option value="">None (unlinked)</option>
              <option v-for="inv in outstandingList" :key="inv.name" :value="inv.name">
                {{ inv.name }} — ₹{{ fmt(inv.outstanding_amount) }}
              </option>
            </select>
          </div>

          <!-- From Account (Contra) -->
          <div v-if="mode === 'contra'" class="mb-4">
            <label class="field-lbl">From Account</label>
            <div class="relative">
              <input
                ref="fromRef"
                v-model="form.fromAccountQuery"
                @input="onFromSearch"
                @keydown.down.prevent="fromCursorDown"
                @keydown.up.prevent="fromCursorUp"
                @keydown.enter.prevent="pickFromCursor"
                @keydown.escape="fromDropdownOpen = false"
                @blur="() => setTimeout(() => { fromDropdownOpen = false }, 150)"
                placeholder="Cash / Bank account…"
                autocomplete="off"
                class="field-inp"
                :class="form.fromAccount ? '!border-orange-400 bg-orange-50 text-orange-800' : ''"
              />
              <ul
                v-if="fromDropdownOpen && fromOptions.length"
                class="absolute z-50 mt-0.5 max-h-44 w-full overflow-y-auto rounded border border-gray-200 bg-white shadow-lg"
              >
                <li
                  v-for="(a, i) in fromOptions"
                  :key="a.name"
                  @mousedown.prevent="pickFromAccount(a)"
                  class="cursor-pointer px-3 py-1.5 text-xs"
                  :class="fromCursor === i ? 'bg-blue-50' : 'hover:bg-gray-50'"
                >
                  <span class="font-semibold">{{ a.account_name }}</span>
                  <span class="ml-2 text-[10px] text-gray-400">{{ a.account_type }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- To Account (Contra) -->
          <div v-if="mode === 'contra'" class="mb-4">
            <label class="field-lbl">To Account</label>
            <div class="relative">
              <input
                ref="toRef"
                v-model="form.toAccountQuery"
                @input="onToSearch"
                @keydown.down.prevent="toCursorDown"
                @keydown.up.prevent="toCursorUp"
                @keydown.enter.prevent="pickToCursor"
                @keydown.escape="toDropdownOpen = false"
                @blur="() => setTimeout(() => { toDropdownOpen = false }, 150)"
                placeholder="Cash / Bank account…"
                autocomplete="off"
                class="field-inp"
                :class="form.toAccount ? '!border-green-400 bg-green-50 text-green-800' : ''"
              />
              <ul
                v-if="toDropdownOpen && toOptions.length"
                class="absolute z-50 mt-0.5 max-h-44 w-full overflow-y-auto rounded border border-gray-200 bg-white shadow-lg"
              >
                <li
                  v-for="(a, i) in toOptions"
                  :key="a.name"
                  @mousedown.prevent="pickToAccount(a)"
                  class="cursor-pointer px-3 py-1.5 text-xs"
                  :class="toCursor === i ? 'bg-blue-50' : 'hover:bg-gray-50'"
                >
                  <span class="font-semibold">{{ a.account_name }}</span>
                  <span class="ml-2 text-[10px] text-gray-400">{{ a.account_type }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Journal Type (Journal) -->
          <div v-if="mode === 'journal'" class="mb-4">
            <label class="field-lbl">Journal Type</label>
            <select v-model="form.journalType" class="field-inp">
              <option>Journal Entry</option>
              <option>Opening Entry</option>
              <option>Depreciation Entry</option>
              <option>Credit Note</option>
              <option>Debit Note</option>
              <option>Write Off Entry</option>
            </select>
          </div>

          <!-- Journal totals summary -->
          <div v-if="mode === 'journal'" class="mb-4 rounded-lg bg-gray-50 p-3">
            <div class="mb-1 flex justify-between text-xs">
              <span class="text-gray-400">Total Dr</span>
              <span class="font-mono font-bold text-red-600">₹{{ fmt(journalTotalDr) }}</span>
            </div>
            <div class="mb-1 flex justify-between text-xs">
              <span class="text-gray-400">Total Cr</span>
              <span class="font-mono font-bold text-green-600">₹{{ fmt(journalTotalCr) }}</span>
            </div>
            <div class="flex justify-between border-t border-gray-200 pt-1 text-xs">
              <span class="font-semibold text-gray-600">Difference</span>
              <span
                class="font-mono font-bold"
                :class="journalBalanced ? 'text-green-600' : 'text-red-600'"
              >
                {{ journalBalanced ? '✓ Balanced' : `₹${fmt(Math.abs(journalTotalDr - journalTotalCr))} off` }}
              </span>
            </div>
          </div>

          <!-- Reference No (Receipt / Payment / Contra) -->
          <div v-if="mode !== 'journal'" class="mb-4">
            <label class="field-lbl">
              Reference No
              <span class="ml-1 font-normal text-gray-400">optional</span>
            </label>
            <div class="flex gap-2">
              <input
                v-model="form.referenceNo"
                type="text"
                placeholder="Cheque / UTR / Txn ID"
                class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              />
              <input
                v-model="form.referenceDate"
                type="date"
                class="w-32 rounded border border-gray-300 px-2 py-2 text-xs outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Remarks -->
          <div class="mb-5">
            <label class="field-lbl">
              Remarks
              <span class="ml-1 font-normal text-gray-400">optional</span>
            </label>
            <textarea
              v-model="form.remarks"
              rows="2"
              placeholder="Optional note…"
              class="w-full resize-none rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <!-- Error -->
          <div
            v-if="errorMsg"
            class="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700"
          >
            {{ errorMsg }}
          </div>

          <!-- Save -->
          <button
            @click="save"
            :disabled="!canSave || saving"
            class="w-full rounded-xl py-3 text-sm font-bold transition-colors"
            :class="canSave && !saving
              ? 'bg-green-600 text-white hover:bg-green-700 cursor-pointer'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
          >
            {{ saving ? 'Saving…' : `Save ${MODES.find(m => m.id === mode)?.label}` }}
            <kbd v-if="canSave" class="ml-2 rounded border border-current px-1.5 py-0.5 font-mono text-[10px] opacity-60">F9</kbd>
          </button>

          <!-- Status hint -->
          <div class="mt-2 text-center text-[10px] text-gray-400">
            <span v-if="mode === 'receipt' && !form.party">Select a customer to start</span>
            <span v-else-if="mode === 'payment' && !form.party">Select a supplier to start</span>
            <span v-else-if="mode === 'contra' && !form.fromAccount">Select from account</span>
            <span v-else-if="mode === 'contra' && !form.toAccount">Select to account</span>
            <span v-else-if="mode !== 'journal' && !(form.amount > 0)">Enter an amount</span>
            <span v-else-if="mode === 'journal' && !journalBalanced">Dr and Cr totals must match</span>
            <span v-else class="text-green-600 font-semibold">Ready — press F9 to save</span>
          </div>

        </div>
      </div><!-- end right panel -->

    </div><!-- end body -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  searchSuppliers, searchAccounts,
  fetchOutstandingInvoices, fetchOutstandingPurchaseInvoices,
  createPaymentEntry, createJournalEntry,
  frappeGet,
} from '../api.js'
import { searchCustomers } from '../customersearch.js'
const router = useRouter()
const today = new Date().toISOString().slice(0, 10)

// ─── Constants ────────────────────────────────────────────────────────────────
const MODES = [
  { id: 'receipt', label: 'Receipt', icon: '📥', key: '1' },
  { id: 'payment', label: 'Payment', icon: '💸', key: '2' },
  { id: 'journal', label: 'Journal', icon: '📒', key: '3' },
  { id: 'contra',  label: 'Contra',  icon: '🔄', key: '4' },
]
const MOPS = [
  { id: 'Cash',          label: 'Cash' },
  { id: 'UPI',           label: 'UPI' },
  { id: 'Bank Transfer', label: 'Bank' },
]

// ─── Mode ─────────────────────────────────────────────────────────────────────
const mode = ref('receipt')

function switchMode(m) {
  if (mode.value === m) return
  mode.value = m
  resetForm()
}

// ─── Form ─────────────────────────────────────────────────────────────────────
function newRow() {
  return { accountQuery: '', account: '', accountName: '', accountOptions: [], accountOpen: false, accountCursor: -1, debit: null, credit: null }
}
function emptyForm() {
  return {
    date: today,
    remarks: '',
    // Receipt / Payment
    party: '', partyName: '',
    amount: null,
    mop: 'Cash',
    invoiceName: '',
    referenceNo: '', referenceDate: today,
    // Journal
    journalType: 'Journal Entry',
    rows: [newRow(), newRow()],
    // Contra
    fromAccountQuery: '', fromAccount: '', fromAccountName: '',
    toAccountQuery: '',   toAccount: '',   toAccountName: '',
  }
}

const form = ref(emptyForm())

function resetForm() {
  form.value = emptyForm()
  partyQuery.value = ''
  partyOptions.value = []
  partyDropdownOpen.value = false
  outstandingList.value = []
  errorMsg.value = ''
}

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const dateRef   = ref(null)
const partyRef  = ref(null)
const amountRef = ref(null)
const fromRef   = ref(null)
const toRef     = ref(null)

// ─── Party search (customer / supplier) ───────────────────────────────────────
const partyQuery       = ref('')
const partyOptions     = ref([])
const partyDropdownOpen = ref(false)
const partyCursor      = ref(-1)

let partyTimer = null
function onPartySearch() {
  form.value.party = ''
  partyCursor.value = -1
  clearTimeout(partyTimer)
  partyTimer = setTimeout(async () => {
    const q = partyQuery.value.trim()
    if (!q) { partyOptions.value = []; partyDropdownOpen.value = false; return }
    try {
      partyOptions.value = mode.value === 'receipt'
        ? await searchCustomers(q)
        : await searchSuppliers(q)
      partyDropdownOpen.value = !!partyOptions.value.length
    } catch { partyOptions.value = [] }
  }, 220)
}

function pickParty(c) {
  form.value.party = c.name
  form.value.partyName = c.customer_name || c.supplier_name || c.name
  partyQuery.value = form.value.partyName
  partyOptions.value = []
  partyDropdownOpen.value = false
  partyCursor.value = -1
  loadOutstanding(c.name)
  setTimeout(() => amountRef.value?.focus(), 30)
}

function clearParty() {
  form.value.party = ''; form.value.partyName = ''
  form.value.invoiceName = ''
  partyQuery.value = ''
  outstandingList.value = []
  partyRef.value?.focus()
}

function partyCursorDown() { partyCursor.value = Math.min(partyCursor.value + 1, partyOptions.value.length - 1) }
function partyCursorUp()   { partyCursor.value = Math.max(partyCursor.value - 1, 0) }
function pickPartyCursor() {
  if (partyCursor.value >= 0 && partyOptions.value[partyCursor.value]) pickParty(partyOptions.value[partyCursor.value])
}
function onPartyBlur() { setTimeout(() => { partyDropdownOpen.value = false }, 150) }

// ─── Outstanding invoices ─────────────────────────────────────────────────────
const outstandingList  = ref([])
const loadingInvoices  = ref(false)

async function loadOutstanding(party) {
  loadingInvoices.value = true
  outstandingList.value = []
  form.value.invoiceName = ''
  try {
    outstandingList.value = mode.value === 'receipt'
      ? await fetchOutstandingInvoices(party)
      : await fetchOutstandingPurchaseInvoices(party)
    if (outstandingList.value.length === 1) selectInvoice(outstandingList.value[0])
  } catch { /* ignore */ }
  finally { loadingInvoices.value = false }
}

function selectInvoice(inv) {
  form.value.invoiceName = inv.name
  if (!form.value.amount) form.value.amount = inv.outstanding_amount
}

// ─── Contra: From account search ──────────────────────────────────────────────
const fromOptions      = ref([])
const fromDropdownOpen = ref(false)
const fromCursor       = ref(-1)
let fromTimer = null

function onFromSearch() {
  form.value.fromAccount = ''
  clearTimeout(fromTimer)
  fromTimer = setTimeout(async () => {
    const q = form.value.fromAccountQuery.trim()
    if (!q) { fromOptions.value = []; fromDropdownOpen.value = false; return }
    try {
      fromOptions.value = await searchAccounts(q, 'CashBank')
      fromDropdownOpen.value = !!fromOptions.value.length
    } catch { fromOptions.value = [] }
  }, 220)
}

function pickFromAccount(a) {
  form.value.fromAccount = a.name
  form.value.fromAccountName = a.account_name
  form.value.fromAccountQuery = a.account_name
  fromOptions.value = []
  fromDropdownOpen.value = false
  fromCursor.value = -1
  setTimeout(() => toRef.value?.focus(), 30)
}

function fromCursorDown() { fromCursor.value = Math.min(fromCursor.value + 1, fromOptions.value.length - 1) }
function fromCursorUp()   { fromCursor.value = Math.max(fromCursor.value - 1, 0) }
function pickFromCursor() {
  if (fromCursor.value >= 0 && fromOptions.value[fromCursor.value]) pickFromAccount(fromOptions.value[fromCursor.value])
}

// ─── Contra: To account search ────────────────────────────────────────────────
const toOptions      = ref([])
const toDropdownOpen = ref(false)
const toCursor       = ref(-1)
let toTimer = null

function onToSearch() {
  form.value.toAccount = ''
  clearTimeout(toTimer)
  toTimer = setTimeout(async () => {
    const q = form.value.toAccountQuery.trim()
    if (!q) { toOptions.value = []; toDropdownOpen.value = false; return }
    try {
      toOptions.value = await searchAccounts(q, 'CashBank')
      toDropdownOpen.value = !!toOptions.value.length
    } catch { toOptions.value = [] }
  }, 220)
}

function pickToAccount(a) {
  form.value.toAccount = a.name
  form.value.toAccountName = a.account_name
  form.value.toAccountQuery = a.account_name
  toOptions.value = []
  toDropdownOpen.value = false
  toCursor.value = -1
  setTimeout(() => amountRef.value?.focus(), 30)
}

function toCursorDown() { toCursor.value = Math.min(toCursor.value + 1, toOptions.value.length - 1) }
function toCursorUp()   { toCursor.value = Math.max(toCursor.value - 1, 0) }
function pickToCursor() {
  if (toCursor.value >= 0 && toOptions.value[toCursor.value]) pickToAccount(toOptions.value[toCursor.value])
}

// ─── Journal entry rows ───────────────────────────────────────────────────────
const accountSearchTimers = {}

function addJournalRow() { form.value.rows.push(newRow()) }
function removeJournalRow(idx) {
  if (form.value.rows.length > 2) form.value.rows.splice(idx, 1)
}

function onAccountSearch(idx) {
  form.value.rows[idx].account = ''
  clearTimeout(accountSearchTimers[idx])
  accountSearchTimers[idx] = setTimeout(async () => {
    const q = form.value.rows[idx].accountQuery.trim()
    if (!q) { form.value.rows[idx].accountOptions = []; form.value.rows[idx].accountOpen = false; return }
    try {
      form.value.rows[idx].accountOptions = await searchAccounts(q)
      form.value.rows[idx].accountOpen = !!form.value.rows[idx].accountOptions.length
    } catch { form.value.rows[idx].accountOptions = [] }
  }, 220)
}

function rowCursorDown(idx) {
  form.value.rows[idx].accountCursor = Math.min(form.value.rows[idx].accountCursor + 1, form.value.rows[idx].accountOptions.length - 1)
}
function rowCursorUp(idx) {
  form.value.rows[idx].accountCursor = Math.max(form.value.rows[idx].accountCursor - 1, 0)
}
function pickRowAccount(idx) {
  const c = form.value.rows[idx].accountCursor
  if (c >= 0 && form.value.rows[idx].accountOptions[c]) setRowAccount(idx, form.value.rows[idx].accountOptions[c])
}
function setRowAccount(idx, opt) {
  form.value.rows[idx].account = opt.name
  form.value.rows[idx].accountName = opt.account_name
  form.value.rows[idx].accountQuery = opt.account_name
  form.value.rows[idx].accountOpen = false
  form.value.rows[idx].accountCursor = -1
}

const journalTotalDr = computed(() => form.value.rows.reduce((s, r) => s + (Number(r.debit) || 0), 0))
const journalTotalCr = computed(() => form.value.rows.reduce((s, r) => s + (Number(r.credit) || 0), 0))
const journalBalanced = computed(() =>
  journalTotalDr.value > 0 && Math.abs(journalTotalDr.value - journalTotalCr.value) < 0.01
)

// ─── Can save ─────────────────────────────────────────────────────────────────
const canSave = computed(() => {
  if (mode.value === 'receipt' || mode.value === 'payment') {
    return !!form.value.party && form.value.amount > 0
  }
  if (mode.value === 'journal') return journalBalanced.value
  if (mode.value === 'contra') {
    return !!form.value.fromAccount && !!form.value.toAccount && form.value.amount > 0
  }
  return false
})

// ─── Save ─────────────────────────────────────────────────────────────────────
const saving   = ref(false)
const errorMsg = ref('')
const flashMsg = ref(null)
let flashTimer = null

function showFlash(text, type = 'ok') {
  flashMsg.value = { text, type }
  clearTimeout(flashTimer)
  flashTimer = setTimeout(() => { flashMsg.value = null }, 3500)
}

async function save() {
  if (!canSave.value || saving.value) return
  saving.value = true
  errorMsg.value = ''
  try {
    let result
    if (mode.value === 'receipt') {
      result = await createPaymentEntry({
        payment_type: 'Receive', party_type: 'Customer',
        party: form.value.party, amount: form.value.amount,
        mode_of_payment: form.value.mop, date: form.value.date,
        reference_no: form.value.referenceNo, reference_date: form.value.referenceDate,
        remarks: form.value.remarks, invoice_name: form.value.invoiceName,
      })
      showFlash(`Receipt saved: ${result.payment_entry}`)
    } else if (mode.value === 'payment') {
      result = await createPaymentEntry({
        payment_type: 'Pay', party_type: 'Supplier',
        party: form.value.party, amount: form.value.amount,
        mode_of_payment: form.value.mop, date: form.value.date,
        reference_no: form.value.referenceNo, reference_date: form.value.referenceDate,
        remarks: form.value.remarks, invoice_name: form.value.invoiceName,
        invoice_doctype: 'Purchase Invoice',
      })
      showFlash(`Payment saved: ${result.payment_entry}`)
    } else if (mode.value === 'journal') {
      result = await createJournalEntry({
        date: form.value.date, voucher_type: form.value.journalType,
        remarks: form.value.remarks,
        accounts: form.value.rows
          .filter(r => r.account)
          .map(r => ({ account: r.account, debit: r.debit || 0, credit: r.credit || 0 })),
      })
      showFlash(`Journal saved: ${result.journal_entry}`)
    } else if (mode.value === 'contra') {
      result = await createPaymentEntry({
        payment_type: 'Internal Transfer',
        amount: form.value.amount, date: form.value.date,
        reference_no: form.value.referenceNo, reference_date: form.value.referenceDate,
        remarks: form.value.remarks,
        paid_from_account: form.value.fromAccount,
        paid_to_account: form.value.toAccount,
      })
      showFlash(`Contra saved: ${result.payment_entry}`)
    }
    resetForm()
    setTimeout(() => {
      if (mode.value === 'receipt' || mode.value === 'payment') partyRef.value?.focus()
      else if (mode.value === 'contra') fromRef.value?.focus()
      else dateRef.value?.focus()
    }, 50)
  } catch (e) {
    errorMsg.value = e.message
    showFlash(e.message, 'err')
  } finally {
    saving.value = false
  }
}

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────
function handleF9() { save() }

function onGlobalKey(e) {
  const tag = document.activeElement?.tagName
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return
  if (e.key === '1') switchMode('receipt')
  else if (e.key === '2') switchMode('payment')
  else if (e.key === '3') switchMode('journal')
  else if (e.key === '4') switchMode('contra')
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKey)
  setTimeout(() => partyRef.value?.focus(), 50)
})
onUnmounted(() => window.removeEventListener('keydown', onGlobalKey))

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(n || 0).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}
function fmtDate(d) {
  if (!d) return ''
  return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.field-lbl {
  @apply mb-1 block text-[10px] font-bold uppercase tracking-wider text-gray-400;
}
.field-inp {
  @apply w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500;
}
</style>
