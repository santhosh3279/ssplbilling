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
            <p class="text-xs text-[var(--color-text-muted)]">Cash and bank accounts · Pending cheques excluded · {{ companyName }}</p>
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
            type="button"
            class="rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-semibold text-[var(--color-text)] disabled:opacity-50"
            :disabled="loading"
            @click="fetchData"
          >
            Refresh
          </button>

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
      <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <button type="button" v-for="summary in reportSummary" :key="summary.label" @click="toggleFlow(summary.key)" :aria-expanded="expandedFlow === summary.key" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-left">
          <p class="text-sm text-[var(--color-text-muted)]">{{ expandedFlow === summary.key ? '▾' : '▸' }} {{ summary.label }}</p>
          <p class="mt-2 text-2xl font-bold tabular-nums" :class="summary.label === 'Cash Outflow' || summary.value < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
            {{ formatCurrency(summary.value) }}
          </p>
          <p class="mt-2 text-xs text-[var(--color-text-muted)]">{{ summary.description }}</p>
        </button>
        <section v-if="expandedFlow" class="overflow-x-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] md:col-span-2 xl:col-span-4 text-[var(--color-text)]">
          <h2 class="px-4 py-3 font-semibold">{{ activeSummary.label }} — Account Particulars</h2>
          <p class="px-4 pb-3 text-xs text-[var(--color-text-muted)]">Click an account to expand its transactions. Internal transfers are hidden in all details; closing balances still reflect them. Amounts are in company currency.</p>
          <div v-for="row in flowAccounts" :key="row.account" class="border-t border-[var(--color-border)]">
            <button type="button" class="flex w-full justify-between gap-4 px-4 py-3 text-left hover:bg-[var(--color-surface-raised)]" :aria-expanded="!!expandedAccounts[row.account]" @click="toggleAccount(row.account)">
              <span>{{ expandedAccounts[row.account] ? '▾' : '▸' }} {{ row.account }}</span>
              <span class="tabular-nums font-semibold">{{ formatCurrency(row[expandedFlow]) }}</span>
            </button>
            <div v-if="expandedAccounts[row.account]" class="px-6 pb-4">
              <p v-if="expandedFlow === 'balance' && detailState(row.account).loaded" class="py-2 font-semibold">Opening balance: {{ formatCurrency(detailState(row.account).opening_balance) }}</p>
              <table v-if="detailState(row.account).entries.length" class="w-full text-sm">
                <thead class="bg-[var(--color-surface-raised)]"><tr>
                  <th class="p-2 text-left">Date</th><th class="p-2 text-left">Voucher</th><th class="p-2 text-left">Particulars / Party</th><th class="p-2 text-left">Cost Center</th><th class="p-2 text-left">Remarks</th>
                  <th v-if="expandedFlow !== 'outflow'" class="p-2 text-right">Inflow</th><th v-if="expandedFlow !== 'inflow'" class="p-2 text-right">Outflow</th>
                </tr></thead>
                <tbody><tr v-for="entry in detailState(row.account).entries" :key="entry.name" class="border-b border-[var(--color-border)]">
                  <td class="p-2 whitespace-nowrap">{{ entry.posting_date }}</td>
                  <td class="p-2"><a :href="voucherUrl(entry)" target="_blank" rel="noopener noreferrer" class="text-[var(--color-info)] underline">{{ entry.voucher_no }}</a><div class="text-xs">{{ entry.voucher_type }} {{ entry.payment_type ? `· ${entry.payment_type}` : '' }}</div></td>
                  <td class="p-2">{{ entry.party || entry.against || '—' }}</td><td class="p-2">{{ entry.cost_center || '—' }}</td><td class="p-2 whitespace-pre-wrap">{{ entry.remarks || '—' }}</td>
                  <td v-if="expandedFlow !== 'outflow'" class="p-2 text-right tabular-nums">{{ formatCurrency(entry.debit) }}</td><td v-if="expandedFlow !== 'inflow'" class="p-2 text-right tabular-nums">{{ formatCurrency(entry.credit) }}</td>
                </tr></tbody>
              </table>
              <p v-if="detailState(row.account).loading" class="py-3">Loading transactions…</p>
              <p v-else-if="detailState(row.account).error" class="py-3 text-[var(--color-danger)]">{{ detailState(row.account).error }} <button type="button" class="underline" @click="loadDetails(row.account)">Try Again</button></p>
              <p v-else-if="detailState(row.account).loaded && !detailState(row.account).entries.length" class="py-3">No transactions in the selected period.</p>
              <button v-if="detailState(row.account).has_more && !detailState(row.account).loading && !detailState(row.account).error" type="button" class="py-3 text-[var(--color-info)] underline" @click="loadDetails(row.account)">Load more transactions</button>
            </div>
          </div>
          <p v-if="!flowAccounts.length" class="p-4">No accounts for this cash flow.</p>
          <div class="flex justify-between border-t border-[var(--color-border)] p-4 font-bold"><span>Total</span><span>{{ formatCurrency(activeSummary.value) }}</span></div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCashflowReport, getCashflowDetails } from '../api.js'
import ExcelJS from 'exceljs'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const companyName = ref(localStorage.getItem('wb-company') || '')
const particulars = ref([])
const totals = ref({ inflow: 0, outflow: 0, netflow: 0, balance: 0 })
const reportSummary = computed(() => [
  { key: 'inflow', label: 'Cash Inflow', value: totals.value.inflow, description: 'Received during the selected period, excluding internal transfers' },
  { key: 'outflow', label: 'Cash Outflow', value: totals.value.outflow, description: 'Paid during the selected period, excluding internal transfers' },
  { key: 'netflow', label: 'Net Cash Flow', value: totals.value.netflow, description: 'Inflow minus outflow for the selected period; excludes internal transfers and pending cheques' },
  { key: 'balance', label: 'Net Cash in Hand', value: totals.value.balance, description: `Closing cash and bank balance as of ${loadedFilters.value?.to || toDate.value}, including opening balances` },
])
const loadedFilters = ref(null)
const today = new Date().toISOString().slice(0, 10)
const fromDate = ref(today)
const toDate = ref(today)
let requestId = 0
const expandedFlow = ref('')
const expandedAccounts = ref({})
const detailCache = ref({})
const activeSummary = computed(() => reportSummary.value.find(row => row.key === expandedFlow.value))
const flowAccounts = computed(() => particulars.value.filter(row => {
  if (expandedFlow.value === 'balance') return true
  if (expandedFlow.value === 'netflow') return row.inflow !== 0 || row.outflow !== 0
  return row[expandedFlow.value] !== 0
}))
const detailKey = account => JSON.stringify([expandedFlow.value, account])
const detailState = account => detailCache.value[detailKey(account)] || { entries: [] }
function toggleFlow(flow) {
  expandedFlow.value = expandedFlow.value === flow ? '' : flow
  expandedAccounts.value = {}
}
function toggleAccount(account) {
  expandedAccounts.value[account] = !expandedAccounts.value[account]
  if (expandedAccounts.value[account] && !detailState(account).loaded) loadDetails(account)
}
function voucherUrl(entry) {
  return `/app/${encodeURIComponent(entry.voucher_type.toLowerCase().replaceAll(' ', '-'))}/${encodeURIComponent(entry.voucher_no)}`
}
async function loadDetails(account) {
  if (!loadedFilters.value) return
  const key = detailKey(account)
  const state = detailCache.value[key] || { entries: [], loaded: false }
  if (state.loading) return
  detailCache.value[key] = state
  state.loading = true
  state.error = ''
  // Update via the reactive proxy so loading and completion render immediately.
  const target = detailCache.value[key]
  const currentRequest = requestId
  const filters = loadedFilters.value
  try {
    const result = await getCashflowDetails({ company: filters.company, account, from_date: filters.from, to_date: filters.to, flow: expandedFlow.value === 'netflow' ? 'balance' : expandedFlow.value, start: target.entries.length })
    if (currentRequest !== requestId) return
    target.entries.push(...result.entries)
    target.has_more = result.has_more
    target.opening_balance = result.opening_balance
    target.loaded = true
  } catch (e) {
    if (currentRequest === requestId) target.error = e.message || 'Failed to load transactions'
  } finally {
    target.loading = false
  }
}

async function fetchData() {
  const currentRequest = ++requestId
  error.value = ''
  particulars.value = []
  expandedFlow.value = ''
  expandedAccounts.value = {}
  detailCache.value = {}
  totals.value = { inflow: 0, outflow: 0, netflow: 0, balance: 0 }
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
      netflow: sum(period.summary, 'inflow') - sum(period.summary, 'outflow'),
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
    particulars.value = [...accounts.values()].map(row => ({ ...row, netflow: row.inflow - row.outflow })).sort((a, b) => a.account.localeCompare(b.account))
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
    sheet.addRow(['Cash and bank accounts; pending cheques excluded; amounts in company currency'])
    sheet.addRow([])
    sheet.addRow(['Summary', 'Amount', 'Details']).font = { bold: true }
    for (const summary of reportSummary.value) {
      const row = sheet.addRow([summary.label, summary.value, summary.description])
      row.getCell(2).numFmt = '#,##0.00;[Red]-#,##0.00'
    }
    const details = workbook.addWorksheet('Particulars')
    details.columns = [{ width: 55 }, { width: 24 }, { width: 24 }, { width: 24 }, { width: 24 }]
    details.addRow([filters.company])
    details.addRow([`Cash Flow: ${filters.from} to ${filters.to}`])
    details.addRow(['Amounts in company currency; closing balances include opening balances and transfers'])
    details.addRow(['Inflow and outflow exclude internal transfers; pending cheques are excluded'])
    details.addRow([])
    details.addRow(['Particulars', 'Cash Inflow', 'Cash Outflow', 'Net Cash Flow', 'Net Cash in Hand']).font = { bold: true }
    for (const item of [...particulars.value, { account: 'Total', ...totals.value }]) {
      const row = details.addRow([item.account, item.inflow, item.outflow, item.netflow, item.balance])
      for (const index of [2, 3, 4, 5]) row.getCell(index).numFmt = '#,##0.00;[Red]-#,##0.00'
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

function refreshOnFocus() {
  if (!loading.value) fetchData()
}

onMounted(() => {
  fetchData()
  window.addEventListener('focus', refreshOnFocus)
})
onUnmounted(() => window.removeEventListener('focus', refreshOnFocus))
</script>
