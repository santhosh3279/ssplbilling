<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
            @click="router.push('/reports')"
          >
            &larr; Back
          </button>
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Material Transfer Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Bill-wise summary of Stock Entries with Material Transfer type</p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Date Presets -->
          <div class="flex items-center gap-1.5">
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('yesterday')"
            >
              Yesterday
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('current-month')"
            >
              Current Month
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('last-month')"
            >
              Last Month
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('fy')"
            >
              FY
            </button>
          </div>

          <!-- Date Filter -->
          <div class="flex items-center gap-1 bg-[var(--color-bg)]/50 rounded-xl border border-[var(--color-border)] p-1">
            <button
              @click="adjustDate('from', -1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <input
              v-model="fromDate"
              type="date"
              class="bg-transparent border-none text-sm text-[var(--color-text)] focus:ring-0 px-1 py-0.5"
              @change="fetchData"
            />
            <button
              @click="adjustDate('from', 1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <span class="text-[var(--color-text-muted)] text-sm px-1">to</span>

            <button
              @click="adjustDate('to', -1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <input
              v-model="toDate"
              type="date"
              class="bg-transparent border-none text-sm text-[var(--color-text)] focus:ring-0 px-1 py-0.5"
              @change="fetchData"
            />
            <button
              @click="adjustDate('to', 1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <button
            class="flex items-center gap-1.5 rounded-lg bg-[var(--color-info)] px-3.5 py-1.5 text-sm font-semibold text-[var(--color-text-on-highlight)] hover:opacity-90 active:scale-95 transition-all shadow-md"
            @click="exportToExcel"
            :disabled="!filteredData.length"
          >
            <span>⬇</span> Export
          </button>
        </div>
      </div>
    </header>

    <!-- Search and Filters Section -->
    <div class="px-6 py-3 bg-[var(--color-surface)]/40 border-b border-[var(--color-border)]/50">
      <div class="max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by Stock Entry ID, Warehouse, or Remarks..."
          class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none placeholder-[var(--color-text-muted)]/60"
        />
      </div>
    </div>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching transfers...</p>
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

      <div v-else-if="filteredData.length === 0" class="flex h-96 items-center justify-center text-center">
        <div class="max-w-xs">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl border border-[var(--color-border)] shadow-inner">
            📭
          </div>
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No transfers found</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">No stock transfers found for the selected criteria and filter.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-5xl mx-auto">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Transferred Value</p>
            <p class="text-3xl font-black text-[var(--color-success)]">{{ formatCurrency(grandTotalValue) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Qty Transferred</p>
            <p class="text-3xl font-black text-[var(--color-text)]">{{ formatQty(grandTotalQty) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Entries (Bills)</p>
            <p class="text-3xl font-black text-[var(--color-info)]">{{ filteredData.length }} Records</p>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)] select-none">
                <th class="w-16 px-4 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] text-center">S.No</th>
                <th
                  @click="sortBy('stock_entry')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Stock Entry ID (Bill No)
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'stock_entry'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('posting_date')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Posting Date
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'posting_date'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('source_warehouse')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Source Warehouse
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'source_warehouse'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('target_warehouse')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Destination Warehouse
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'target_warehouse'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('total_qty')"
                  class="px-6 py-3 text-right text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-end gap-1.5">
                    Total Qty
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'total_qty'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('total_amount')"
                  class="px-6 py-3 text-right text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-end gap-1.5">
                    Total Value (INR)
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'total_amount'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Remarks</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/10">
              <tr
                v-for="(row, idx) in filteredData"
                :key="row.stock_entry"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors group"
              >
                <td class="w-16 px-4 py-3 font-mono text-sm text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-center">
                  {{ idx + 1 }}
                </td>
                <td class="px-6 py-3 font-mono text-sm font-bold text-[var(--color-info)] border-b border-[var(--color-border)]/50">
                  {{ row.stock_entry }}
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ row.posting_date }} <span class="text-xs text-[var(--color-text-muted)] ml-1">{{ row.posting_time }}</span>
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]/50 font-medium">
                  {{ row.source_warehouse }}
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]/50 font-medium">
                  {{ row.target_warehouse }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-base text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ formatQty(row.total_qty) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-base font-semibold text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ formatCurrencyWithoutSymbol(row.total_amount) }}
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 whitespace-normal max-w-md font-light">
                  {{ row.remarks }}
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="px-4 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]">GRAND TOTAL</td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-right font-mono text-lg text-[var(--color-text)] border-t border-[var(--color-border)]">
                  {{ formatQty(grandTotalQty) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-lg text-[var(--color-success)] border-t border-[var(--color-border)]">
                  {{ formatCurrency(grandTotalValue) }}
                </td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
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
import { getMaterialTransferReport } from '../api.js'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const reportData = ref([])
const searchQuery = ref('')

// Dates configuration (Defaults to today)
const todayStr = new Date().toISOString().slice(0, 10)
const fromDate = ref(todayStr)
const toDate = ref(todayStr)

onMounted(async () => {
  await fetchData()
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const data = await getMaterialTransferReport(fromDate.value, toDate.value)
    reportData.value = data.rows || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch material transfer report data'
  } finally {
    loading.value = false
  }
}

const sortKey = ref('posting_date')
const sortAsc = ref(false) // Default descending order for dates

function sortBy(key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

const filteredData = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  let result = reportData.value
  
  if (query) {
    result = result.filter(r => 
      (r.stock_entry || '').toLowerCase().includes(query) ||
      (r.source_warehouse || '').toLowerCase().includes(query) || 
      (r.target_warehouse || '').toLowerCase().includes(query) || 
      (r.remarks || '').toLowerCase().includes(query)
    )
  }

  const key = sortKey.value
  const asc = sortAsc.value ? 1 : -1

  return [...result].sort((a, b) => {
    let valA = a[key]
    let valB = b[key]

    if (valA === undefined || valA === null) valA = ''
    if (valB === undefined || valB === null) valB = ''

    if (typeof valA === 'string' && typeof valB === 'string') {
      return valA.localeCompare(valB) * asc
    }
    
    if (valA < valB) return -1 * asc
    if (valA > valB) return 1 * asc
    return 0
  })
})

const grandTotalQty = computed(() => {
  return filteredData.value.reduce((sum, r) => sum + (r.total_qty || 0), 0)
})

const grandTotalValue = computed(() => {
  return filteredData.value.reduce((sum, r) => sum + (r.total_amount || 0), 0)
})

function adjustDate(type, days) {
  const ref_ = type === 'from' ? fromDate : toDate
  const d = new Date(ref_.value)
  d.setDate(d.getDate() + days)
  ref_.value = d.toISOString().slice(0, 10)
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
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2
  }).format(val || 0)
}

function formatCurrencyWithoutSymbol(val) {
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(val || 0)
}

function formatQty(val) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 3
  }).format(val || 0)
}

function exportToExcel() {
  if (!filteredData.value.length) return

  const headers = [
    'S.No',
    'Stock Entry ID (Bill No)',
    'Posting Date',
    'Posting Time',
    'Source Warehouse',
    'Destination Warehouse',
    'Total Quantity',
    'Total Amount (INR)',
    'Remarks'
  ]
  
  const data = filteredData.value.map((r, idx) => [
    idx + 1,
    r.stock_entry,
    r.posting_date,
    r.posting_time,
    r.source_warehouse,
    r.target_warehouse,
    r.total_qty,
    r.total_amount,
    r.remarks
  ])

  // Add Grand Total row
  data.push([
    '',
    'GRAND TOTAL',
    '',
    '',
    '',
    '',
    grandTotalQty.value,
    grandTotalValue.value,
    ''
  ])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])

  ws['!cols'] = [
    { wch: 8 },   // S.No
    { wch: 25 },  // Stock Entry ID
    { wch: 14 },  // Date
    { wch: 12 },  // Time
    { wch: 25 },  // Source Warehouse
    { wch: 25 },  // Destination Warehouse
    { wch: 15 },  // Total Qty
    { wch: 20 },  // Total Value
    { wch: 40 }   // Remarks
  ]

  utils.book_append_sheet(wb, ws, 'Material Transfers')
  writeFile(wb, `MaterialTransferSummary_${fromDate.value}_to_${toDate.value}.xlsx`)
}
</script>

<style scoped>
.overflow-x-auto {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.overflow-x-auto::-webkit-scrollbar {
  height: 6px;
}
.overflow-x-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-x-auto::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 20px;
}

table th, table td {
  font-size: calc(0.875rem * 1.5);
  line-height: 1.5;
}
table .text-xs {
  font-size: calc(0.75rem * 1.5) !important;
}
table .text-sm {
  font-size: calc(0.875rem * 1.5) !important;
  line-height: calc(1.25rem * 1.5) !important;
}
table .text-base {
  font-size: calc(1rem * 1.5) !important;
  line-height: calc(1.5rem * 1.5) !important;
}
table .text-lg {
  font-size: calc(1.125rem * 1.5) !important;
  line-height: calc(1.75rem * 1.5) !important;
}
</style>
