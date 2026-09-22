<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
            @click="router.push('/reports')"
          >
            &larr; Back
          </button>
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Cashflow Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">All cash and bank accounts · {{ companyName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <!-- Date Presets -->
          <div class="flex items-center gap-2">
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('yesterday')"
            >
              Yesterday
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('current-month')"
            >
              Current Month
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('last-month')"
            >
              Last Month
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('fy')"
            >
              FY
            </button>
          </div>

          <!-- Date Filter -->
          <div class="flex items-center gap-2">
            <button
              @click="shiftRange(-1)"
              class="p-2 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors hover:bg-[var(--color-border)] active:scale-95"
              title="Shift date range back by 1 day"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            <div class="flex items-center gap-1 bg-[var(--color-bg)]/50 rounded-xl border border-[var(--color-border)] p-1">
              <button
                @click="adjustDate('from', -1)"
                class="p-1.5 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <input
                v-model="fromDate"
                type="date"
                class="bg-transparent border-none text-lg text-[var(--color-text)] focus:ring-0 px-1 py-1"
                @change="fetchData"
              />
              <button
                @click="adjustDate('from', 1)"
                class="p-1.5 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>

              <span class="text-[var(--color-text-muted)] text-lg px-1">to</span>

              <button
                @click="adjustDate('to', -1)"
                class="p-1.5 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <input
                v-model="toDate"
                type="date"
                class="bg-transparent border-none text-lg text-[var(--color-text)] focus:ring-0 px-1 py-1"
                @change="fetchData"
              />
              <button
                @click="adjustDate('to', 1)"
                class="p-1.5 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <button
              @click="shiftRange(1)"
              class="p-2 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors hover:bg-[var(--color-border)] active:scale-95"
              title="Shift date range forward by 1 day"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <button
            class="flex items-center gap-2 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] active:scale-95 transition-all shadow-lg shadow-violet-900/20"
            @click="exportToExcel"
            :disabled="loading || !!error || !loadedFilters"
          >
            <span>⬇</span> Export Excel
          </button>
        </div>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center text-[var(--color-text-muted)]">
        Loading cash flow report…
      </div>
      <div v-else-if="error" class="rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/10 p-6 text-[var(--color-danger)]">
        <p>{{ error }}</p>
        <button type="button" @click="fetchData" class="mt-3 font-semibold underline">Try Again</button>
      </div>
      <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div v-for="summary in reportSummary" :key="summary.label" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <p class="text-sm text-[var(--color-text-muted)]">{{ summary.label }}</p>
          <p class="mt-2 text-2xl font-bold tabular-nums" :class="summary.label === 'Cash Outflow' || summary.value < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
            {{ formatCurrency(summary.value) }}
          </p>
          <p class="mt-2 text-xs text-[var(--color-text-muted)]">{{ summary.description }}</p>
        </div>
        <section class="overflow-x-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] md:col-span-3">
          <h2 class="px-4 pt-4 font-semibold text-[var(--color-text)]">Account-wise Particulars</h2>
          <p class="px-4 py-2 text-xs text-[var(--color-text-muted)]">Inflow and outflow exclude internal transfers. Closing balances include opening balances and transfers. Amounts are in company currency.</p>
          <table class="w-full text-sm text-[var(--color-text)]">
            <thead class="bg-[var(--color-surface-raised)]">
              <tr>
                <th class="px-4 py-3 text-left">Particulars</th>
                <th class="px-4 py-3 text-right">Cash Inflow</th>
                <th class="px-4 py-3 text-right">Cash Outflow</th>
                <th class="px-4 py-3 text-right">Net Cash in Hand</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in particulars" :key="row.account" class="border-t border-[var(--color-border)]">
                <td class="px-4 py-3">{{ row.account }}</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(row.inflow) }}</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(row.outflow) }}</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(row.balance) }}</td>
              </tr>
              <tr v-if="!particulars.length">
                <td colspan="4" class="px-4 py-6 text-center text-[var(--color-text-muted)]">No cash or bank entries through the selected end date.</td>
              </tr>
            </tbody>
            <tfoot class="border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] font-bold">
              <tr>
                <td class="px-4 py-3">Total</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(totals.inflow) }}</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(totals.outflow) }}</td>
                <td class="px-4 py-3 text-right tabular-nums">{{ formatCurrency(totals.balance) }}</td>
              </tr>
            </tfoot>
          </table>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCashflowReport } from '../api.js'
import ExcelJS from 'exceljs'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const companyName = ref(localStorage.getItem('wb-company') || '')
const particulars = ref([])
const totals = ref({ inflow: 0, outflow: 0, balance: 0 })
const reportSummary = computed(() => [
  { label: 'Cash Inflow', value: totals.value.inflow, description: 'Received during the selected period, excluding internal transfers' },
  { label: 'Cash Outflow', value: totals.value.outflow, description: 'Paid during the selected period, excluding internal transfers' },
  { label: 'Net Cash in Hand', value: totals.value.balance, description: `Closing cash and bank balance as of ${loadedFilters.value?.to || toDate.value}, including opening balances` },
])
const loadedFilters = ref(null)
const today = new Date().toISOString().slice(0, 10)
const fromDate = ref(today)
const toDate = ref(today)
let requestId = 0

async function fetchData() {
  const currentRequest = ++requestId
  error.value = ''
  particulars.value = []
  totals.value = { inflow: 0, outflow: 0, balance: 0 }
  loadedFilters.value = null
  companyName.value = localStorage.getItem('wb-company') || ''
  if (!companyName.value || !fromDate.value || !toDate.value || fromDate.value > toDate.value) {
    loading.value = false
    error.value = !companyName.value ? 'Select a billing company before running Cash Flow.' : 'Select a valid date range.'
    return
  }
  const filters = { company: companyName.value, from: fromDate.value, to: toDate.value }
  loading.value = true
  try {
    const [period, cumulative] = await Promise.all([
      getCashflowReport(filters.from, filters.to, filters.company),
      getCashflowReport('1000-01-01', filters.to, filters.company),
    ])
    if (currentRequest !== requestId) return
    const sum = (rows, field) => (rows || []).reduce((total, row) => total + (Number(row[field]) || 0), 0)
    const balances = [...(cumulative.summary || []), ...(cumulative.internal_summary || [])]
    totals.value = {
      inflow: sum(period.summary, 'inflow'),
      outflow: sum(period.summary, 'outflow'),
      balance: sum(balances, 'inflow') - sum(balances, 'outflow'),
    }
    const accounts = new Map()
    const accountRow = account => {
      if (!accounts.has(account)) accounts.set(account, { account, inflow: 0, outflow: 0, balance: 0 })
      return accounts.get(account)
    }
    for (const entry of period.breakdown || []) {
      const row = accountRow(entry.account)
      row.inflow += Number(entry.inflow) || 0
      row.outflow += Number(entry.outflow) || 0
    }
    for (const entry of [...(cumulative.breakdown || []), ...(cumulative.internal_breakdown || [])]) {
      accountRow(entry.account).balance += (Number(entry.inflow) || 0) - (Number(entry.outflow) || 0)
    }
    particulars.value = [...accounts.values()].sort((a, b) => a.account.localeCompare(b.account))
    loadedFilters.value = filters
  } catch (e) {
    if (currentRequest === requestId) error.value = e.message || 'Failed to fetch cash flow report'
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

function adjustDate(type, days) {
  const ref_ = type === 'from' ? fromDate : toDate
  const d = new Date(ref_.value)
  d.setDate(d.getDate() + days)
  ref_.value = d.toISOString().slice(0, 10)
  fetchData()
}

function shiftRange(days) {
  const from = new Date(fromDate.value)
  from.setDate(from.getDate() + days)
  fromDate.value = from.toISOString().slice(0, 10)

  const to = new Date(toDate.value)
  to.setDate(to.getDate() + days)
  toDate.value = to.toISOString().slice(0, 10)

  fetchData()
}

function formatDateIso(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function setDateRange(preset) {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()

  let from = ''
  let to = ''

  if (preset === 'yesterday') {
    const yesterday = new Date()
    yesterday.setDate(now.getDate() - 1)
    from = formatDateIso(yesterday)
    to = formatDateIso(yesterday)
  } else if (preset === 'current-month') {
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    from = formatDateIso(firstDay)
    to = formatDateIso(lastDay)
  } else if (preset === 'last-month') {
    const firstDay = new Date(year, month - 1, 1)
    const lastDay = new Date(year, month, 0)
    from = formatDateIso(firstDay)
    to = formatDateIso(lastDay)
  } else if (preset === 'fy') {
    let startYear = year
    if (month < 3) {
      startYear = year - 1
    }
    const endYear = startYear + 1
    from = `${startYear}-04-01`
    to = `${endYear}-03-31`
  }

  if (from && to) {
    fromDate.value = from
    toDate.value = to
    fetchData()
  }
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value) || 0)
}

async function exportToExcel() {
  if (loading.value || error.value || !loadedFilters.value) return
  try {
    const filters = { ...loadedFilters.value }
    const workbook = new ExcelJS.Workbook()
    const sheet = workbook.addWorksheet('Cash Flow')
    sheet.columns = [{ width: 28 }, { width: 24 }, { width: 90 }]
    sheet.addRow([filters.company])
    sheet.addRow([`Cash Flow: ${filters.from} to ${filters.to}`])
    sheet.addRow(['All cash and bank accounts; amounts in company currency'])
    sheet.addRow([])
    sheet.addRow(['Summary', 'Amount', 'Details']).font = { bold: true }
    for (const summary of reportSummary.value) {
      const row = sheet.addRow([summary.label, summary.value, summary.description])
      row.getCell(2).numFmt = '#,##0.00;[Red]-#,##0.00'
    }
    const details = workbook.addWorksheet('Particulars')
    details.columns = [{ width: 55 }, { width: 24 }, { width: 24 }, { width: 24 }]
    details.addRow([filters.company])
    details.addRow([`Cash Flow: ${filters.from} to ${filters.to}`])
    details.addRow(['Amounts in company currency; closing balances include opening balances and transfers'])
    details.addRow(['Inflow and outflow exclude internal transfers'])
    details.addRow([])
    details.addRow(['Particulars', 'Cash Inflow', 'Cash Outflow', 'Net Cash in Hand']).font = { bold: true }
    for (const item of [...particulars.value, { account: 'Total', ...totals.value }]) {
      const row = details.addRow([item.account, item.inflow, item.outflow, item.balance])
      for (const index of [2, 3, 4]) row.getCell(index).numFmt = '#,##0.00;[Red]-#,##0.00'
    }
    details.lastRow.font = { bold: true }
    const buffer = await workbook.xlsx.writeBuffer()
    const url = URL.createObjectURL(new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `CashFlow_${filters.from}_to_${filters.to}.xlsx`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) {
    error.value = e.message || 'Failed to export Cash Flow'
  }
}

onMounted(fetchData)
</script>
