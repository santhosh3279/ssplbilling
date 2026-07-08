<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div class="flex items-center gap-3 flex-shrink-0">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
            @click="router.push('/reports')"
          >
            &larr; Back
          </button>
          <div>
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Fast Moving Items</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Top selling items sorted by total quantity sold</p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Limit Selector -->
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Show:</span>
            <select
              v-model="selectedLimit"
              @change="fetchData"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2.5 py-1.5 text-sm font-semibold text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
            >
              <option :value="20">Top 20</option>
              <option :value="50">Top 50</option>
              <option :value="100">Top 100</option>
              <option :value="500">Top 500</option>
              <option :value="100000">All</option>
            </select>
          </div>

          <!-- Series Selector -->
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Series:</span>
            <select
              v-model="selectedSeries"
              @change="fetchData"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2.5 py-1.5 text-sm font-semibold text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none max-w-[130px]"
            >
              <option value="">— All Series —</option>
              <option v-for="s in seriesList" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>

          <!-- Income Account Selector -->
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Store:</span>
            <select
              v-model="selectedIncomeAccount"
              @change="fetchData"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2.5 py-1.5 text-sm font-semibold text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none max-w-[160px]"
            >
              <option value="">— All Stores —</option>
              <option v-for="acc in incomeAccounts" :key="acc" :value="acc">{{ acc }}</option>
            </select>
          </div>

          <!-- Date Presets -->
          <div class="flex items-center gap-1">
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('yesterday')"
            >
              Yesterday
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('current-month')"
            >
              Month
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
              @click="setDateRange('last-month')"
            >
              Last M
            </button>
            <button
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all active:scale-95 uppercase tracking-wider"
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
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <input
              v-model="fromDate"
              type="date"
              class="bg-transparent border-none text-xs text-[var(--color-text)] focus:ring-0 px-0.5 py-0.5"
              @change="fetchData"
            />
            <button
              @click="adjustDate('from', 1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <span class="text-[var(--color-text-muted)] text-xs px-0.5">to</span>

            <button
              @click="adjustDate('to', -1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <input
              v-model="toDate"
              type="date"
              class="bg-transparent border-none text-xs text-[var(--color-text)] focus:ring-0 px-0.5 py-0.5"
              @change="fetchData"
            />
            <button
              @click="adjustDate('to', 1)"
              class="p-1 rounded-lg hover:bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
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
          placeholder="Filter by Item Code or Item Name..."
          class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none placeholder-[var(--color-text-muted)]/60"
        />
      </div>
    </div>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching fast moving items...</p>
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
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No sales found</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">No items sold for the selected criteria and filter.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-5xl mx-auto">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Sales Taxable Value</p>
            <p class="text-3xl font-black text-[var(--color-success)]">{{ formatCurrency(grandTotalTaxableValue) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Qty Sold</p>
            <p class="text-3xl font-black text-[var(--color-text)]">{{ formatQty(grandTotalQty) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Unique Items Count</p>
            <p class="text-3xl font-black text-[var(--color-info)]">{{ filteredData.length }} Items</p>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)] select-none">
                <th class="w-16 px-4 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] text-center">S.No</th>
                <th
                  @click="sortBy('item_code')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Item Code
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'item_code'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('item_name')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center gap-1.5">
                    Item Name
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'item_name'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('stock_uom')"
                  class="px-6 py-3 text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] text-center cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-center gap-1.5">
                    UOM
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'stock_uom'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('total_qty')"
                  class="px-6 py-3 text-right text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-end gap-1.5">
                    Total Quantity Sold
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'total_qty'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('total_taxable_value')"
                  class="px-6 py-3 text-right text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-end gap-1.5">
                    Total Sales Value
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'total_taxable_value'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
                <th
                  @click="sortBy('transaction_count')"
                  class="px-6 py-3 text-right text-sm font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-raised)] transition-colors"
                >
                  <div class="flex items-center justify-end gap-1.5">
                    Invoices Count
                    <span class="text-xs text-[var(--color-info)]" v-if="sortKey === 'transaction_count'">{{ sortAsc ? '▲' : '▼' }}</span>
                    <span class="text-xs text-[var(--color-text-muted)]/30" v-else>⇅</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/10">
              <tr
                v-for="(row, idx) in filteredData"
                :key="row.item_code"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors group"
              >
                <td class="w-16 px-4 py-3 font-mono text-sm text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-center">
                  {{ idx + 1 }}
                </td>
                <td class="px-6 py-3 font-mono text-sm font-semibold text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ row.item_code }}
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text)] border-b border-[var(--color-border)]/50 whitespace-normal max-w-md">
                  {{ row.item_name }}
                </td>
                <td class="px-6 py-3 text-sm text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-center">
                  {{ row.stock_uom }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-base text-[var(--color-text)] border-b border-[var(--color-border)]/50 font-bold">
                  {{ formatQty(row.total_qty) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-base font-semibold text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ formatCurrency(row.total_taxable_value) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-base text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                  {{ row.transaction_count }}
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="px-4 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]">GRAND TOTAL</td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-sm border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-3 text-right font-mono text-lg text-[var(--color-text)] border-t border-[var(--color-border)]">
                  {{ formatQty(grandTotalQty) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-lg text-[var(--color-success)] border-t border-[var(--color-border)]">
                  {{ formatCurrency(grandTotalTaxableValue) }}
                </td>
                <td class="px-6 py-3 text-right font-mono text-lg text-[var(--color-text)] border-t border-[var(--color-border)]">
                  {{ grandTotalTransactions }}
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
import { getFastMovingItemsReport, getIncomeAccounts } from '../api.js'
import { dashboardApi } from '../services/dashboard'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const seriesList = ref([])
const incomeAccounts = ref([])
const selectedSeries = ref('')
const selectedIncomeAccount = ref('')
const selectedLimit = ref(50)
const reportData = ref([])
const searchQuery = ref('')

// Dates configuration (Default to current month)
const today = new Date()
const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
const formatDateIso = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const fromDate = ref(formatDateIso(firstDay))
const toDate = ref(formatDateIso(lastDay))

onMounted(async () => {
  loading.value = true
  try {
    const d = await dashboardApi.getAllowedSeries()
    seriesList.value = d.allowed_series || []
    
    incomeAccounts.value = await getIncomeAccounts() || []
    
    await fetchData()
  } catch (e) {
    error.value = e.message || 'Failed to initialize report configurations.'
  } finally {
    loading.value = false
  }
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const data = await getFastMovingItemsReport(
      fromDate.value,
      toDate.value,
      selectedSeries.value,
      selectedIncomeAccount.value,
      selectedLimit.value
    )
    reportData.value = data || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch fast moving items data'
  } finally {
    loading.value = false
  }
}

const sortKey = ref('total_qty')
const sortAsc = ref(false) // Default DESC for fast moving items

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
      (r.item_code || '').toLowerCase().includes(query) || 
      (r.item_name || '').toLowerCase().includes(query)
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

const grandTotalTaxableValue = computed(() => {
  return filteredData.value.reduce((sum, r) => sum + (r.total_taxable_value || 0), 0)
})

const grandTotalTransactions = computed(() => {
  return filteredData.value.reduce((sum, r) => sum + (r.transaction_count || 0), 0)
})

function adjustDate(type, days) {
  const ref_ = type === 'from' ? fromDate : toDate
  const d = new Date(ref_.value)
  d.setDate(d.getDate() + days)
  ref_.value = d.toISOString().slice(0, 10)
  fetchData()
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

function formatQty(val) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 3
  }).format(val || 0)
}

function exportToExcel() {
  if (!filteredData.value.length) return

  const headers = ['S.No', 'Item Code', 'Item Name', 'UOM', 'Total Quantity Sold', 'Total Sales Value', 'Invoices Count']
  
  const data = filteredData.value.map((r, idx) => [
    idx + 1,
    r.item_code,
    r.item_name,
    r.stock_uom,
    r.total_qty,
    r.total_taxable_value,
    r.transaction_count
  ])

  // Add Grand Total row
  data.push([
    '',
    'GRAND TOTAL',
    '',
    '',
    grandTotalQty.value,
    grandTotalTaxableValue.value,
    grandTotalTransactions.value
  ])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])

  ws['!cols'] = [
    { wch: 8 },
    { wch: 20 },
    { wch: 35 },
    { wch: 10 },
    { wch: 18 },
    { wch: 18 },
    { wch: 15 }
  ]

  utils.book_append_sheet(wb, ws, 'Fast Moving Items')

  const seriesPart = selectedSeries.value ? '_' + selectedSeries.value.replace(/[^A-Za-z0-9]/g, '') : ''
  const storePart = selectedIncomeAccount.value ? '_' + selectedIncomeAccount.value.replace(/[^A-Za-z0-9]/g, '') : ''
  writeFile(wb, `FastMovingItems${seriesPart}${storePart}_${fromDate.value}_to_${toDate.value}.xlsx`)
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
</style>
