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
            <p class="text-xs text-[var(--color-text-muted)]">ERPNext Cash Flow · {{ companyName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <label class="flex flex-col gap-1 text-xs text-[var(--color-text-muted)]">
            Periodicity
            <select v-model="periodicity" @change="fetchData" class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text)]">
              <option>Monthly</option>
              <option>Quarterly</option>
              <option>Half-Yearly</option>
              <option>Yearly</option>
            </select>
          </label>
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
            :disabled="loading || !!error || reportRows.length === 0"
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
      <div v-else-if="!reportRows.length" class="py-16 text-center text-[var(--color-text-muted)]">
        No cash flow data for the selected period.
      </div>
      <div v-else>
        <div v-if="reportSummary.length" class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div v-for="(summary, index) in reportSummary" :key="index" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <p class="text-sm text-[var(--color-text-muted)]">{{ summary.label }}</p>
            <p class="mt-2 text-2xl font-bold tabular-nums" :class="Number(summary.value) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
              {{ formatCurrency(summary.value) }}
              <span class="text-sm text-[var(--color-text-muted)]">{{ summary.currency }}</span>
            </p>
          </div>
        </div>
        <div class="overflow-x-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
          <table class="w-full border-collapse text-sm">
            <thead class="bg-[var(--color-surface-raised)]">
              <tr>
                <th v-for="column in visibleColumns" :key="column.fieldname" class="border-b border-[var(--color-border)] px-4 py-3 text-[var(--color-text-muted)] whitespace-nowrap" :class="isNumericColumn(column) ? 'text-right' : 'text-left'">
                  {{ column.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in reportRows" :key="index" class="border-b border-[var(--color-border)]/50 text-[var(--color-text)]" :class="!row.parent_section ? 'font-bold bg-[var(--color-surface-raised)]/40' : ''">
                <td v-for="column in visibleColumns" :key="column.fieldname" class="px-4 py-3" :class="isNumericColumn(column) ? 'text-right font-mono tabular-nums whitespace-nowrap' : 'text-left'" :style="column.fieldname === 'section' ? { paddingLeft: `${16 + (Number(row.indent) || 0) * 20}px` } : {}">
                  <template v-if="isNumericColumn(column)">{{ row[column.fieldname] == null ? '' : formatCurrency(row[column.fieldname]) }}</template>
                  <template v-else>{{ displayValue(row[column.fieldname]) }}</template>
                </td>
              </tr>
            </tbody>
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
const companyName = ref(localStorage.getItem('wb-company') || '')
const periodicity = ref('Yearly')
const reportColumns = ref([])
const reportRows = ref([])
const reportSummary = ref([])
const loadedFilters = ref(null)
const visibleColumns = computed(() => reportColumns.value.filter(column => !Number(column.hidden)))
const today = new Date().toISOString().slice(0, 10)
const fromDate = ref(today)
const toDate = ref(today)
let requestId = 0

async function fetchData() {
  const currentRequest = ++requestId
  error.value = ''
  reportRows.value = []
  reportColumns.value = []
  reportSummary.value = []
  loadedFilters.value = null
  companyName.value = localStorage.getItem('wb-company') || ''
  if (!companyName.value || !fromDate.value || !toDate.value || fromDate.value > toDate.value) {
    loading.value = false
    error.value = !companyName.value ? 'Select a billing company before running Cash Flow.' : 'Select a valid date range.'
    return
  }
  const filters = { company: companyName.value, from: fromDate.value, to: toDate.value, periodicity: periodicity.value }
  loading.value = true
  try {
    const result = await getCashflowReport(filters.from, filters.to, filters.company, filters.periodicity)
    if (currentRequest !== requestId) return
    reportColumns.value = result.columns || []
    reportRows.value = (result.result || []).filter(row => row && Object.keys(row).length)
    reportSummary.value = result.report_summary || []
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

function isNumericColumn(column) {
  return ['Currency', 'Float', 'Int', 'Percent'].includes(column.fieldtype)
}

function displayValue(value) {
  return typeof value === 'string' ? value.replace(/^'|'$/g, '') : value ?? ''
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value) || 0)
}

async function exportToExcel() {
  if (loading.value || error.value || !reportRows.value.length || !loadedFilters.value) return
  try {
    const filters = { ...loadedFilters.value }
    const columns = visibleColumns.value
    const workbook = new ExcelJS.Workbook()
    const sheet = workbook.addWorksheet('Cash Flow')
    sheet.columns = columns.map(column => ({ width: isNumericColumn(column) ? 20 : 55 }))
    sheet.addRow([filters.company])
    sheet.addRow([`Cash Flow: ${filters.from} to ${filters.to} (${filters.periodicity})`])
    const currency = reportRows.value.find(row => row.currency)?.currency
    if (currency) sheet.addRow([`Currency: ${currency}`])
    sheet.addRow([])
    const header = sheet.addRow(columns.map(column => column.label))
    header.font = { bold: true }
    for (const row of reportRows.value) {
      const excelRow = sheet.addRow(columns.map(column => {
        const value = row[column.fieldname]
        return isNumericColumn(column) ? (value == null ? null : Number(value)) : displayValue(value)
      }))
      excelRow.font = { bold: !row.parent_section }
      columns.forEach((column, index) => {
        const cell = excelRow.getCell(index + 1)
        if (isNumericColumn(column)) cell.numFmt = '#,##0.00;[Red]-#,##0.00'
        else if (column.fieldname === 'section') cell.alignment = { indent: Number(row.indent) || 0 }
      })
    }
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
