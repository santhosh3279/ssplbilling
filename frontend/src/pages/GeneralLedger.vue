<template>
  <div
    :class="[
      isSubWindow
        ? 'fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm'
        : 'flex min-h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px]'
    ]"
    @keydown.esc="isSubWindow && $emit('close')"
  >
    <div
      :class="[
        isSubWindow
          ? 'flex h-[92vh] w-[96vw] flex-col overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl'
          : 'flex flex-1 flex-col'
      ]"
    >

    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            v-if="!isSubWindow"
            @click="$router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span v-if="!isSubWindow" class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            General Ledger
            <span v-if="ledgerData" class="ml-2 text-[var(--color-text-muted)] font-normal">— {{ ledgerData.label }}</span>
          </h1>
          <span v-if="ledgerData" class="rounded bg-[var(--color-info)]/20 px-2 py-0.5 text-[10px] font-semibold text-[var(--color-info)]">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- Print -->
          <button
            v-if="ledgerData"
            @click="showPrintModal = true"
            class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:border-[var(--color-info)] hover:text-[var(--color-info)] transition-colors"
            title="Print ledger"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print
          </button>

          <!-- Excel -->
          <button
            v-if="ledgerData"
            @click="exportExcel"
            class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:border-[var(--color-success)] hover:text-[var(--color-success)] transition-colors"
            title="Export to Excel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            Excel
          </button>

          <!-- Zoom -->
          <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <button @click="zoom = Math.max(60, zoom - 10)" class="flex h-7 w-7 items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
            <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] px-2 min-w-[44px]">
              <span class="text-[9px] uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
              <span class="text-[11px] font-semibold text-[var(--color-text)] leading-tight">{{ zoom }}%</span>
            </div>
            <button @click="zoom = Math.min(200, zoom + 10)" class="flex h-7 w-7 items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
          </div>

          <!-- Close -->
          <button
            v-if="isSubWindow"
            @click="$emit('close')"
            class="ml-2 flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            title="Close (Esc)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-wrap items-end gap-3">

        <!-- Party Search -->
        <div class="relative w-72">
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Party</label>
          <div
            v-if="selectedParty"
            class="flex items-center justify-between rounded border border-[var(--color-info)] bg-[var(--color-info)]/10 px-3 py-2 text-sm cursor-pointer"
            @click="clearSelection"
          >
            <span class="font-semibold text-[var(--color-info)] truncate">{{ selectedParty.label }}</span>
            <span class="ml-2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-xs">✕</span>
          </div>
          <div v-else class="relative">
            <div
              @click="openCustomerSearch"
              class="w-full cursor-pointer rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-muted)] outline-none hover:border-[var(--color-info)]"
            >
              Select a party...
            </div>
          </div>
        </div>

        <!-- From Date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
          <input
            v-model="fromDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- To Date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- Refresh Button -->
        <button
          @click="loadLedger"
          :disabled="!selectedParty || loading"
          class="rounded-lg px-5 py-2 text-sm font-semibold transition-colors"
          :class="selectedParty && !loading
            ? 'bg-[var(--color-info)] text-white hover:opacity-90 cursor-pointer'
            : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] cursor-not-allowed'"
        >
          {{ loading ? 'Loading…' : 'Refresh Ledger' }}
        </button>

        <!-- Summary chips -->
        <template v-if="ledgerData">
          <div class="flex items-center gap-2 text-xs flex-wrap">
            <span class="rounded bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1.5 text-[var(--color-text-muted)]">
              Opening
              <span class="ml-1 font-semibold" :class="ledgerData.opening_balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                {{ fmt(Math.abs(ledgerData.opening_balance)) }}
                {{ ledgerData.opening_balance < 0 ? 'Cr' : 'Dr' }}
              </span>
            </span>
            <span class="rounded bg-[var(--color-success)]/15 border border-[var(--color-success)]/30 px-2.5 py-1.5 text-[var(--color-success)]">
              Dr {{ fmt(ledgerData.total_debit) }}
            </span>
            <span class="rounded bg-[var(--color-danger)]/15 border border-[var(--color-danger)]/30 px-2.5 py-1.5 text-[var(--color-danger)]">
              Cr {{ fmt(ledgerData.total_credit) }}
            </span>
            <span
              class="rounded border px-2.5 py-1.5 font-bold"
              :class="ledgerData.closing_balance < 0
                ? 'bg-[var(--color-danger)]/15 border-[var(--color-danger)]/30 text-[var(--color-danger)]'
                : 'bg-[var(--color-success)]/15 border-[var(--color-success)]/30 text-[var(--color-success)]'"
            >
              Balance {{ fmt(Math.abs(ledgerData.closing_balance)) }}
              {{ ledgerData.closing_balance < 0 ? 'Cr' : 'Dr' }}
            </span>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ CONTENT ═══════ -->
    <div class="flex-1 overflow-auto">

      <!-- Empty state -->
      <div v-if="!ledgerData && !loading && !error" class="flex flex-col items-center justify-center gap-3 py-24 text-[var(--color-text-muted)]">
        <div class="text-5xl">📒</div>
        <div class="text-sm font-semibold">Select a party and click Refresh Ledger</div>
        <div class="text-xs">Powered by ERPNext General Ledger report engine</div>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="flex items-center justify-center gap-2 py-24 text-sm text-[var(--color-text-muted)]">
        <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></div>
        Loading ledger…
      </div>

      <!-- Error -->
      <div v-else-if="error" class="m-6 rounded-lg border border-[var(--color-danger)]/50 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
        {{ error }}
      </div>

      <!-- Table -->
      <template v-else-if="ledgerData">
        <table class="w-full border-collapse" :style="{ fontSize: `${(13 * zoom) / 100}px` }">
          <thead class="sticky top-0 z-10 bg-[var(--color-surface)] border-b-2 border-[var(--color-border)]">
            <tr>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Date</th>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Type</th>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Voucher No</th>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Account</th>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Against</th>
              <th class="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Remarks</th>
              <th class="px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Debit (Dr)</th>
              <th class="px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Credit (Cr)</th>
              <th class="px-3 py-2 text-right text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] whitespace-nowrap">Balance</th>
            </tr>
          </thead>
          <tbody>

            <!-- Opening Balance -->
            <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
              <td colspan="6" class="px-3 py-2 text-[var(--color-text-muted)] text-xs">
                Opening Balance
                <span class="ml-1 opacity-60">(before {{ fmtDate(ledgerData.from_date) }})</span>
              </td>
              <td class="px-3 py-2 text-right text-[var(--color-success)] font-mono">
                {{ ledgerData.opening_balance > 0 ? fmt(ledgerData.opening_balance) : '—' }}
              </td>
              <td class="px-3 py-2 text-right text-[var(--color-danger)] font-mono">
                {{ ledgerData.opening_balance < 0 ? fmt(Math.abs(ledgerData.opening_balance)) : '—' }}
              </td>
              <td class="px-3 py-2 text-right font-mono font-semibold"
                :class="ledgerData.opening_balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                {{ fmt(Math.abs(ledgerData.opening_balance)) }}
                <span class="ml-0.5 text-[10px] font-normal text-[var(--color-text-muted)]">{{ ledgerData.opening_balance < 0 ? 'Cr' : 'Dr' }}</span>
              </td>
            </tr>

            <!-- No entries -->
            <tr v-if="!ledgerData.entries.length">
              <td colspan="9" class="px-3 py-12 text-center text-[var(--color-text-muted)]">
                No transactions in the selected date range.
              </td>
            </tr>

            <!-- Entry rows -->
            <tr
              v-for="(entry, idx) in ledgerData.entries"
              :key="idx"
              @click="toggleExpand(idx)"
              class="cursor-pointer border-b border-[var(--color-border)] transition-colors"
              :class="expandedIdx === idx
                ? 'bg-[var(--color-info)]/15'
                : 'hover:bg-[var(--color-surface-raised)]/60'"
            >
              <td class="px-3 py-2 text-[var(--color-text-muted)] whitespace-nowrap font-mono">{{ fmtDate(entry.date) }}</td>
              <td class="px-3 py-2 whitespace-nowrap">
                <span
                  class="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                  :class="voucherBadge(entry.voucher_type)"
                >{{ voucherLabel(entry.voucher_type) }}</span>
              </td>
              <td class="px-3 py-2 whitespace-nowrap">
                <button
                  @click.stop="openInErpNext(entry.voucher_type, entry.voucher_no)"
                  class="font-mono text-[var(--color-info)] hover:underline"
                >{{ entry.voucher_no }}</button>
              </td>
              <td class="px-3 py-2 text-[var(--color-text-muted)] max-w-[160px] truncate" :title="entry.account">{{ entry.account }}</td>
              <td class="px-3 py-2 text-[var(--color-text-muted)] max-w-[200px] truncate" :title="entry.against">{{ entry.against || '—' }}</td>
              <td class="px-3 py-2 text-[var(--color-text-muted)] max-w-[220px]">
                <span v-if="expandedIdx === idx" class="whitespace-pre-wrap break-words">{{ entry.remarks || '—' }}</span>
                <span v-else class="block truncate">{{ entry.remarks || '—' }}</span>
              </td>
              <td class="px-3 py-2 text-right font-mono">
                <span v-if="entry.debit" class="text-[var(--color-success)]">{{ fmt(entry.debit) }}</span>
                <span v-else class="text-[var(--color-text-muted)]">—</span>
              </td>
              <td class="px-3 py-2 text-right font-mono">
                <span v-if="entry.credit" class="text-[var(--color-danger)]">{{ fmt(entry.credit) }}</span>
                <span v-else class="text-[var(--color-text-muted)]">—</span>
              </td>
              <td class="px-3 py-2 text-right font-mono font-semibold"
                :class="entry.balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                {{ fmt(Math.abs(entry.balance)) }}
                <span class="ml-0.5 text-[10px] font-normal text-[var(--color-text-muted)]">{{ entry.balance < 0 ? 'Cr' : 'Dr' }}</span>
              </td>
            </tr>

            <!-- Closing row -->
            <tr v-if="ledgerData.entries.length" class="border-t-2 border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
              <td colspan="3" class="px-3 py-2 font-semibold text-[var(--color-text)]">Closing Balance</td>
              <td colspan="3" class="px-3 py-2 text-xs text-[var(--color-text-muted)]">
                {{ fmtDate(ledgerData.from_date) }} → {{ fmtDate(ledgerData.to_date) }}
              </td>
              <td class="px-3 py-2 text-right font-mono font-semibold text-[var(--color-success)]">{{ fmt(ledgerData.total_debit) }}</td>
              <td class="px-3 py-2 text-right font-mono font-semibold text-[var(--color-danger)]">{{ fmt(ledgerData.total_credit) }}</td>
              <td class="px-3 py-2 text-right font-mono font-bold"
                :class="ledgerData.closing_balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                {{ fmt(Math.abs(ledgerData.closing_balance)) }}
                <span class="ml-0.5 text-[10px] font-normal text-[var(--color-text-muted)]">{{ ledgerData.closing_balance < 0 ? 'Cr' : 'Dr' }}</span>
              </td>
            </tr>

          </tbody>
        </table>
      </template>
    </div>

    <!-- Print Modal -->
    <PrintOptionsModal
      v-if="showPrintModal && ledgerData"
      :invoice-name="ledgerData.party"
      doctype="General Ledger"
      @close="showPrintModal = false"
    />

    <!-- Customer Search Modal -->
    <CustomerSearchModal
      ref="ledgerCustSearchModalRef"
      :show="showCustomerSearchModal"
      :skip-date-filter="true"
      @close="showCustomerSearchModal = false"
      @select="pickCustomer"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet } from '../api.js'
import * as XLSX from 'xlsx'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  isSubWindow: { type: Boolean, default: false },
  ledgerName: { type: String, default: '' },
  ledgerType: { type: String, default: 'Customer' },
  initialFromDate: { type: String, default: '' },
  initialToDate: { type: String, default: '' }
})

const emit = defineEmits(['close'])

useSubwindowWatcher(ref(props.isSubWindow), {
  'ESCAPE': () => emit('close')
})

const router = useRouter()
const route = useRoute()

// ── Filter state ──
const partyType = ref('Customer')
const selectedParty = ref(null)   // { name, label, type }
const fromDate = ref((() => { const d = new Date(); d.setDate(d.getDate() - 90); return d.toISOString().split('T')[0] })())
const toDate = ref(new Date().toISOString().split('T')[0])

onMounted(async () => {
  if (props.initialFromDate) fromDate.value = props.initialFromDate
  if (props.initialToDate) toDate.value = props.initialToDate

  const party = props.ledgerName || route.query.party || route.query.customer || route.query.ledger
  const party_type = props.ledgerType || route.query.party_type || (route.query.customer ? 'Customer' : 'Account')
  const label = route.query.label

  if (party && party_type) {
    partyType.value = party_type
    
    let displayLabel = label || party
    if (!label && party) {
      // Try to fetch label if not provided
      try {
        const nameField = party_type === 'Customer' ? 'customer_name'
          : party_type === 'Supplier' ? 'supplier_name'
          : 'employee_name'
        
        if (['Customer', 'Supplier', 'Employee'].includes(party_type)) {
          const doc = await frappeGet('frappe.client.get', { doctype: party_type, name: party })
          displayLabel = doc[nameField] || party
        }
      } catch (e) {
        console.warn('Failed to fetch party label:', e)
      }
    }

    selectedParty.value = { name: party, label: displayLabel, type: party_type }
    loadLedger()
  }
})

// ── Data state ──
const ledgerData = ref(null)
const loading = ref(false)
const error = ref('')
const expandedIdx = ref(null)

// ── UI ──
const zoom = ref(100)
const showPrintModal = ref(false)

// ── Customer Search Modal ──
const showCustomerSearchModal = ref(false)
const ledgerCustSearchModalRef = ref(null)

function openCustomerSearch() {
  showCustomerSearchModal.value = true
  nextTick(() => ledgerCustSearchModalRef.value?.focus())
}

function pickCustomer(item) {
  showCustomerSearchModal.value = false
  selectedParty.value = item
  partyType.value = item.type
  loadLedger()
}

function clearSelection() {
  selectedParty.value = null
  ledgerData.value = null
  error.value = ''
}

// ── Refresh ledger ──
async function loadLedger() {
  if (!selectedParty.value || loading.value) return
  loading.value = true
  error.value = ''
  expandedIdx.value = null
  try {
    const data = await frappeGet('ssplbilling.api.ledger_api.get_general_ledger', {
      party_type: partyType.value,
      party: selectedParty.value.name,
      from_date: fromDate.value,
      to_date: toDate.value,
    })
    ledgerData.value = data
  } catch (e) {
    console.error('Failed to load GL ledger:', e)
    error.value = e?.message || 'Failed to refresh ledger. Check console for details.'
  } finally {
    loading.value = false
  }
}

// ── Row expand ──
function toggleExpand(idx) {
  expandedIdx.value = expandedIdx.value === idx ? null : idx
}

// ── Formatting ──
function fmt(n) {
  return (Number(n) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDate(d) {
  if (!d) return '—'
  const [y, m, day] = d.split('-')
  return `${day}-${m}-${y}`
}

function voucherLabel(type) {
  const map = {
    'Sales Invoice': 'SI', 'Purchase Invoice': 'PI', 'Payment Entry': 'PE',
    'Journal Entry': 'JE', 'Stock Entry': 'SE', 'Delivery Note': 'DN',
    'Purchase Receipt': 'PR', 'Sales Order': 'SO', 'Purchase Order': 'PO',
  }
  return map[type] || (type || '?').slice(0, 3).toUpperCase()
}

function voucherBadge(type) {
  const map = {
    'Sales Invoice':    'bg-[var(--color-info)]/20 text-[var(--color-info)]',
    'Payment Entry':    'bg-[var(--color-success)]/20 text-[var(--color-success)]',
    'Journal Entry':    'bg-[var(--color-warning)]/20 text-[var(--color-warning)]',
    'Purchase Invoice': 'bg-[var(--color-supplier)]/20 text-[var(--color-supplier)]',
    'Sales Order':      'bg-[var(--color-info)]/10 text-[var(--color-info)]',
  }
  return map[type] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'
}

// ── Excel export ──
function exportExcel() {
  if (!ledgerData.value) return
  const d = ledgerData.value

  const rows = []

  // Title rows
  rows.push([`General Ledger — ${d.label}`])
  rows.push([`${d.party_type}  |  ${fmtDate(d.from_date)} to ${fmtDate(d.to_date)}`])
  rows.push([])

  // Header
  rows.push(['Date', 'Voucher Type', 'Voucher No', 'Account', 'Against', 'Remarks', 'Debit (Dr)', 'Credit (Cr)', 'Balance'])

  // Opening row
  rows.push([
    `Opening (before ${fmtDate(d.from_date)})`, '', '', '', '', '',
    d.opening_balance > 0 ? d.opening_balance : '',
    d.opening_balance < 0 ? Math.abs(d.opening_balance) : '',
    Math.abs(d.opening_balance),
  ])

  // Entry rows
  for (const e of d.entries) {
    rows.push([
      fmtDate(e.date),
      e.voucher_type,
      e.voucher_no,
      e.account,
      e.against,
      e.remarks,
      e.debit || '',
      e.credit || '',
      Math.abs(e.balance),
    ])
  }

  // Closing row
  rows.push([])
  rows.push([
    'Closing Balance', '', '', '', '', '',
    d.total_debit,
    d.total_credit,
    Math.abs(d.closing_balance),
  ])

  const ws = XLSX.utils.aoa_to_sheet(rows)

  // Column widths
  ws['!cols'] = [
    { wch: 12 }, { wch: 18 }, { wch: 22 }, { wch: 28 }, { wch: 28 },
    { wch: 30 }, { wch: 14 }, { wch: 14 }, { wch: 16 },
  ]

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'General Ledger')

  const filename = `GL_${d.party}_${d.from_date}_${d.to_date}.xlsx`
  XLSX.writeFile(wb, filename)
}

function openInErpNext(voucherType, voucherNo) {
  const dtMap = {
    'Sales Invoice': 'sales-invoice',
    'Purchase Invoice': 'purchase-invoice',
    'Payment Entry': 'payment-entry',
    'Journal Entry': 'journal-entry',
    'Stock Entry': 'stock-entry',
    'Delivery Note': 'delivery-note',
  }
  const dt = dtMap[voucherType] || voucherType.toLowerCase().replace(/\s+/g, '-')
  window.open(`/app/${dt}/${encodeURIComponent(voucherNo)}`, '_blank')
}
</script>

<style scoped>
* { font-weight: 400; }
</style>
