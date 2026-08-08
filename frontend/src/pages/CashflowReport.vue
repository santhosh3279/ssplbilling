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
            <p class="text-xs text-[var(--color-text-muted)]">Cost Center-wise Cash & Bank Flow</p>
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
            :disabled="loading || currentSummaryData.length === 0"
          >
            <span>⬇</span> Export Excel
          </button>
        </div>
      </div>
    </header>

    <!-- Tabs -->
    <div class="flex border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 overflow-x-auto">
      <button
        @click="activeTab = 'payments'; expandedRows.clear()"
        class="px-8 py-4 text-base font-bold transition-all relative shrink-0 uppercase tracking-wider"
        :class="activeTab === 'payments' ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
      >
        Payments & Receipts
        <div v-if="activeTab === 'payments'" class="absolute bottom-0 left-0 right-0 h-[3px] bg-[var(--color-info)]"></div>
      </button>
      <button
        @click="activeTab = 'internal'; expandedRows.clear()"
        class="px-8 py-4 text-base font-bold transition-all relative shrink-0 uppercase tracking-wider"
        :class="activeTab === 'internal' ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
      >
        Internal Transfer Expenses
        <div v-if="activeTab === 'internal'" class="absolute bottom-0 left-0 right-0 h-[3px] bg-[var(--color-info)]"></div>
      </button>
    </div>

    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching cashflow data...</p>
        </div>
      </div>

      <div v-else-if="error" class="mx-auto max-w-md rounded-2xl bg-[var(--color-danger)]/20 border border-[var(--color-danger)]/30 p-8 text-center">
        <div class="text-4xl mb-4">⚠️</div>
        <h3 class="text-lg font-bold text-[var(--color-danger)] mb-2">Failed to load report</h3>
        <p class="text-sm text-[var(--color-danger)]/80 mb-6">{{ error }}</p>
        <button
          @click="fetchData"
          class="rounded-xl bg-[var(--color-danger)]/20 px-6 py-2 text-sm font-semibold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/30 transition-colors"
        >
          Try Again
        </button>
      </div>

      <div v-else-if="currentSummaryData.length === 0" class="flex h-96 items-center justify-center text-center">
        <div class="max-w-xs">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl border border-[var(--color-border)] shadow-inner">
            📭
          </div>
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No cashflow found</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">We couldn't find any cash or bank entries for the selected date range.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-5xl mx-auto">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Inflow (Dr)</p>
            <p class="text-3xl font-black text-[var(--color-success)]">{{ formatCurrency(grandInflowTotal) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Outflow (Cr)</p>
            <p class="text-3xl font-black text-[var(--color-warning)]">{{ formatCurrency(grandOutflowTotal) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Net Cashflow</p>
            <p class="text-3xl font-black" :class="grandNetTotal >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              {{ formatCurrency(grandNetTotal) }}
            </p>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl max-w-6xl mx-auto">
          <table class="w-full text-left border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                <th class="w-12 px-4 py-2.5 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider sticky left-0 bg-[var(--color-surface)] z-20 border-b border-[var(--color-border)] text-center">S.No</th>
                <th class="w-12 px-2 py-2.5 text-lg font-bold text-[var(--color-text-muted)] border-b border-[var(--color-border)] text-center"></th>
                <th class="px-6 py-2.5 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider sticky left-12 bg-[var(--color-surface)] z-20 border-b border-[var(--color-border)]">Cost Center</th>
                <th class="px-6 py-2.5 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Inflow (Debit)</th>
                <th class="px-6 py-2.5 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Outflow (Credit)</th>
                <th class="px-6 py-2.5 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Net Cash Flow</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <template v-for="(row, idx) in currentSummaryData" :key="row.cost_center">
                <!-- Summary Row -->
                <tr
                  class="hover:bg-[var(--color-surface-raised)]/30 transition-colors group cursor-pointer"
                  @click="toggleRow(row.cost_center)"
                >
                  <td class="w-12 px-4 py-3 sticky left-0 bg-[var(--color-surface)] group-hover:bg-[var(--color-surface-raised)]/30 z-10 font-mono text-lg text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-center">
                    {{ idx + 1 }}
                  </td>
                  <td class="w-12 px-2 py-3 text-center text-lg border-b border-[var(--color-border)]/50">
                    <span class="inline-block transform transition-transform duration-200" :class="expandedRows.has(row.cost_center) ? 'rotate-90 text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">
                      ▶
                    </span>
                  </td>
                  <td class="px-6 py-3 sticky left-12 bg-[var(--color-surface)] group-hover:bg-[var(--color-surface-raised)]/30 z-10 border-b border-[var(--color-border)]/50">
                    <div class="text-lg font-semibold text-[var(--color-text)]">{{ row.cost_center_name }}</div>
                    <div class="text-[15px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.cost_center }}</div>
                  </td>
                  <td class="px-6 py-3 text-right font-mono text-xl text-[var(--color-success)] border-b border-[var(--color-border)]/50">
                    {{ formatCurrency(row.inflow) }}
                  </td>
                  <td class="px-6 py-3 text-right font-mono text-xl text-[var(--color-warning)] border-b border-[var(--color-border)]/50">
                    {{ formatCurrency(row.outflow) }}
                  </td>
                  <td class="px-6 py-3 text-right font-mono text-xl font-bold border-b border-[var(--color-border)]/50" :class="row.net_flow >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                    {{ formatCurrency(row.net_flow) }}
                  </td>
                </tr>

                <!-- Expanded Breakdown Row -->
                <tr v-if="expandedRows.has(row.cost_center)">
                  <td colspan="6" class="bg-[var(--color-surface-raised)]/10 px-6 py-4 border-b border-[var(--color-border)]/50">
                    <div class="ml-16 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 overflow-hidden shadow-inner">
                      <table class="w-full text-left">
                        <thead>
                          <tr class="bg-[var(--color-surface-raised)]/30 text-[var(--color-text-muted)] text-[15px] font-bold uppercase tracking-wider">
                            <th class="px-6 py-2">Account</th>
                            <th class="px-6 py-2 text-right">Inflow (Debit)</th>
                            <th class="px-6 py-2 text-right">Outflow (Credit)</th>
                            <th class="px-6 py-2 text-right">Net Flow</th>
                          </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-700/30 text-lg">
                          <tr
                            v-for="sub in getBreakdownForCostCenter(row.cost_center)"
                            :key="sub.account"
                            class="hover:bg-[var(--color-surface-raised)]/20 transition-colors"
                          >
                            <td class="px-6 py-2.5 text-[var(--color-text)] font-semibold">{{ sub.account }}</td>
                            <td class="px-6 py-2.5 text-right font-mono text-[var(--color-success)]">{{ formatCurrency(sub.inflow) }}</td>
                            <td class="px-6 py-2.5 text-right font-mono text-[var(--color-warning)]">{{ formatCurrency(sub.outflow) }}</td>
                            <td class="px-6 py-2.5 text-right font-mono font-bold" :class="sub.net_flow >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                              {{ formatCurrency(sub.net_flow) }}
                            </td>
                          </tr>
                          <tr v-if="getBreakdownForCostCenter(row.cost_center).length === 0">
                            <td colspan="4" class="px-6 py-3 text-center text-[var(--color-text-muted)] italic">No breakdown details available.</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="w-12 px-4 py-2 sticky left-0 bg-[var(--color-bg)] z-10 border-t border-[var(--color-border)]"></td>
                <td class="w-12 px-2 py-2 border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-2 sticky left-12 bg-[var(--color-bg)] z-10 border-t border-[var(--color-border)]">GRAND TOTAL</td>
                <td class="px-6 py-2 text-right font-mono text-xl text-[var(--color-success)] border-t border-[var(--color-border)]">
                  {{ formatCurrency(grandInflowTotal) }}
                </td>
                <td class="px-6 py-2 text-right font-mono text-xl text-[var(--color-warning)] border-t border-[var(--color-border)]">
                  {{ formatCurrency(grandOutflowTotal) }}
                </td>
                <td class="px-6 py-2 text-right font-mono text-2xl border-t border-[var(--color-border)]" :class="grandNetTotal >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ formatCurrency(grandNetTotal) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
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
const activeTab = ref('payments') // 'payments' or 'internal'

const summaryData = ref([])
const breakdownData = ref([])
const internalSummaryData = ref([])
const internalBreakdownData = ref([])

const expandedRows = ref(new Set())
const companyName = ref('')
const companyAddressLines = ref([])

// Default dates: Today
const today = new Date().toISOString().slice(0, 10)
const fromDate = ref(today)
const toDate = ref(today)

const currentSummaryData = computed(() => {
  return activeTab.value === 'payments' ? summaryData.value : internalSummaryData.value
})

const currentBreakdownData = computed(() => {
  return activeTab.value === 'payments' ? breakdownData.value : internalBreakdownData.value
})

const grandInflowTotal = computed(() => {
  return currentSummaryData.value.reduce((sum, r) => sum + (r.inflow || 0), 0)
})

const grandOutflowTotal = computed(() => {
  return currentSummaryData.value.reduce((sum, r) => sum + (r.outflow || 0), 0)
})

const grandNetTotal = computed(() => {
  return currentSummaryData.value.reduce((sum, r) => sum + (r.net_flow || 0), 0)
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const res = await getCashflowReport(fromDate.value, toDate.value)
    summaryData.value = res.summary || []
    breakdownData.value = res.breakdown || []
    internalSummaryData.value = res.internal_summary || []
    internalBreakdownData.value = res.internal_breakdown || []
    companyName.value = res.company_name || ''
    companyAddressLines.value = res.company_address_lines || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch cashflow report'
  } finally {
    loading.value = false
  }
}

function toggleRow(costCenter) {
  if (expandedRows.value.has(costCenter)) {
    expandedRows.value.delete(costCenter)
  } else {
    expandedRows.value.add(costCenter)
  }
}

function getBreakdownForCostCenter(costCenter) {
  return currentBreakdownData.value.filter(b => b.cost_center === costCenter)
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

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0
  }).format(val || 0)
}

function fmt(n) {
  return Number(Number(n || 0).toFixed(2))
}

async function exportToExcel() {
  const activeSummary = currentSummaryData.value
  const activeBreakdown = currentBreakdownData.value
  if (activeSummary.length === 0) return

  const workbook = new ExcelJS.Workbook()
  const titleSuffix = activeTab.value === 'payments' ? 'Payments & Receipts' : 'Internal Transfers'

  // ── SHEET 1: SUMMARY ──
  const summarySheet = workbook.addWorksheet(`${titleSuffix} Summary`)
  summarySheet.columns = [
    { key: 'cc_name', width: 25 },
    { key: 'cc_code', width: 25 },
    { key: 'inflow', width: 18 },
    { key: 'outflow', width: 18 },
    { key: 'net_flow', width: 20 }
  ]

  // Company Name
  const row1 = summarySheet.addRow([companyName.value || ''])
  row1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  row1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  summarySheet.mergeCells(1, 1, 1, 5)

  // Address lines
  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines.value[i] || ''
    const rowNum = i + 2
    const row = summarySheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    summarySheet.mergeCells(rowNum, 1, rowNum, 5)
  }

  // Report Title
  const titleRow = summarySheet.addRow([`Cashflow Summary Report - ${titleSuffix} (${fromDate.value} to ${toDate.value})`])
  titleRow.getCell(1).font = { name: 'Arial', size: 11, bold: true }
  titleRow.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  summarySheet.mergeCells(6, 1, 6, 5)

  // Spacing
  summarySheet.addRow([])

  // Headers
  const headers = ['Cost Center', 'Cost Center Code', 'Inflow (Debit)', 'Outflow (Credit)', 'Net Cash Flow']
  const headerRow = summarySheet.addRow(headers)
  headerRow.eachCell(cell => {
    cell.font = { name: 'Arial', bold: true }
    cell.alignment = { horizontal: 'center' }
    cell.border = {
      bottom: { style: 'thin' },
      top: { style: 'thin' }
    }
  })

  // Rows
  let totalInflow = 0
  let totalOutflow = 0
  let totalNetFlow = 0

  for (const r of activeSummary) {
    summarySheet.addRow([
      r.cost_center_name,
      r.cost_center,
      fmt(r.inflow),
      fmt(r.outflow),
      fmt(r.net_flow)
    ])
    totalInflow += r.inflow
    totalOutflow += r.outflow
    totalNetFlow += r.net_flow
  }

  // Total row
  const totalRow = summarySheet.addRow([
    'GRAND TOTAL',
    '',
    fmt(totalInflow),
    fmt(totalOutflow),
    fmt(totalNetFlow)
  ])
  totalRow.eachCell((cell, colNumber) => {
    cell.font = { name: 'Arial', bold: true }
    if (colNumber >= 3 || colNumber === 1) {
      cell.border = {
        top: { style: 'thin' },
        bottom: { style: 'double' }
      }
    }
  })

  // ── SHEET 2: BREAKDOWN ──
  const breakdownSheet = workbook.addWorksheet(`${titleSuffix} Breakdown`)
  breakdownSheet.columns = [
    { key: 'cc_name', width: 25 },
    { key: 'account', width: 35 },
    { key: 'inflow', width: 18 },
    { key: 'outflow', width: 18 },
    { key: 'net_flow', width: 20 }
  ]

  // Company Name
  const bRow1 = breakdownSheet.addRow([companyName.value || ''])
  bRow1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  bRow1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  breakdownSheet.mergeCells(1, 1, 1, 5)

  // Address lines
  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines.value[i] || ''
    const rowNum = i + 2
    const row = breakdownSheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    breakdownSheet.mergeCells(rowNum, 1, rowNum, 5)
  }

  // Report Title
  const bTitleRow = breakdownSheet.addRow([`Cashflow Account-wise Breakdown - ${titleSuffix} (${fromDate.value} to ${toDate.value})`])
  bTitleRow.getCell(1).font = { name: 'Arial', size: 11, bold: true }
  bTitleRow.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  breakdownSheet.mergeCells(6, 1, 6, 5)

  // Spacing
  breakdownSheet.addRow([])

  // Headers
  const bHeaders = ['Cost Center', 'Account', 'Inflow (Debit)', 'Outflow (Credit)', 'Net Cash Flow']
  const bHeaderRow = breakdownSheet.addRow(bHeaders)
  bHeaderRow.eachCell(cell => {
    cell.font = { name: 'Arial', bold: true }
    cell.alignment = { horizontal: 'center' }
    cell.border = {
      bottom: { style: 'thin' },
      top: { style: 'thin' }
    }
  })

  // Rows
  for (const r of activeBreakdown) {
    breakdownSheet.addRow([
      r.cost_center_name,
      r.account,
      fmt(r.inflow),
      fmt(r.outflow),
      fmt(r.net_flow)
    ])
  }

  // Total row
  const bTotalRow = breakdownSheet.addRow([
    'GRAND TOTAL',
    '',
    fmt(totalInflow),
    fmt(totalOutflow),
    fmt(totalNetFlow)
  ])
  bTotalRow.eachCell((cell, colNumber) => {
    cell.font = { name: 'Arial', bold: true }
    if (colNumber >= 3 || colNumber === 1) {
      cell.border = {
        top: { style: 'thin' },
        bottom: { style: 'double' }
      }
    }
  })

  // Generate blob and download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)

  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  const fileLabel = activeTab.value === 'payments' ? 'CashflowReport' : 'InternalTransfersReport'
  link.download = `${fileLabel}_${from}_to_${to}.xlsx`
  link.click()
}

onMounted(() => {
  fetchData()
})
</script>
