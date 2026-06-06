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
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Store Sale Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Consolidated sales by store (Direct Income)</p>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <!-- Date Filter -->
          <div class="flex items-center gap-2 bg-[var(--color-bg)]/50 rounded-xl border border-[var(--color-border)] p-1">
            <input
              v-model="fromDate"
              type="date"
              class="bg-transparent border-none text-xs text-[var(--color-text)] focus:ring-0 px-2 py-1"
              @change="fetchData"
            />
            <span class="text-[var(--color-text-muted)] text-xs">to</span>
            <input
              v-model="toDate"
              type="date"
              class="bg-transparent border-none text-xs text-[var(--color-text)] focus:ring-0 px-2 py-1"
              @change="fetchData"
            />
          </div>

          <button
            class="flex items-center gap-2 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] active:scale-95 transition-all shadow-lg shadow-violet-900/20"
            @click="exportToExcel"
          >
            <span>⬇</span> Export Excel
          </button>
        </div>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching store data...</p>
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

      <div v-else-if="reportData.length === 0" class="flex h-96 items-center justify-center text-center">
        <div class="max-w-xs">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl border border-[var(--color-border)] shadow-inner">
            📭
          </div>
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No sales found</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">We couldn't find any direct income entries for the selected date range.</p>
        </div>
      </div>

      <div v-else class="mx-auto max-w-5xl">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Sales</p>
            <p class="text-3xl font-black text-[var(--color-success)]">{{ formatCurrency(grandTotal) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Active Stores</p>
            <p class="text-3xl font-black text-[var(--color-text)]">{{ reportData.length }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Average / Store</p>
            <p class="text-3xl font-black text-[var(--color-info)]">{{ formatCurrency(grandTotal / reportData.length) }}</p>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                <th class="px-6 py-4 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Store Name (Cost Center)</th>
                <th class="px-6 py-4 text-right text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Sale Amount</th>
                <th class="px-6 py-4 text-right text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Contribution %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr
                v-for="row in reportData"
                :key="row.cost_center"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors group"
              >
                <td class="px-6 py-4">
                  <div class="font-semibold text-[var(--color-text)] group-hover:text-[var(--color-text)]">{{ row.store_name }}</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.cost_center }}</div>
                </td>
                <td class="px-6 py-4 text-right font-bold text-[var(--color-text)]">
                  {{ formatCurrency(row.total_amount) }}
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-3">
                    <div class="w-24 h-1.5 bg-[var(--color-surface-raised)] rounded-full overflow-hidden">
                      <div
                        class="h-full bg-[var(--color-info)] rounded-full"
                        :style="{ width: `${(row.total_amount / grandTotal * 100).toFixed(1)}%` }"
                      ></div>
                    </div>
                    <span class="text-xs font-semibold text-[var(--color-text-muted)]">
                      {{ (row.total_amount / grandTotal * 100).toFixed(1) }}%
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)]">
                <td class="px-6 py-5 font-black text-[var(--color-text)] uppercase tracking-wider">GRAND TOTAL</td>
                <td class="px-6 py-5 text-right text-xl font-black text-[var(--color-success)]">
                  {{ formatCurrency(grandTotal) }}
                </td>
                <td class="px-6 py-5 text-right text-[var(--color-text-muted)] font-bold">100.0%</td>
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
import { getStoreSaleReport } from '../api.js'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const reportData = ref([])

// Default dates: Today
const today = new Date().toISOString().slice(0, 10)
const fromDate = ref(today)
const toDate = ref(today)

const grandTotal = computed(() => {
  return reportData.value.reduce((sum, r) => sum + (r.total_amount || 0), 0)
})

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const data = await getStoreSaleReport(fromDate.value, toDate.value)
    reportData.value = data || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch store sale report'
  } finally {
    loading.value = false
  }
}

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val || 0)
}

function exportToExcel() {
  if (!reportData.value.length) return

  const headers = ['Store Name', 'Cost Center', 'Sale Amount', 'Contribution %']
  const data = reportData.value.map(r => [
    r.store_name,
    r.cost_center,
    r.total_amount,
    ((r.total_amount / grandTotal.value) * 100).toFixed(2) + '%'
  ])

  // Add total row
  data.push(['GRAND TOTAL', '', grandTotal.value, '100%'])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])

  // Column widths
  ws['!cols'] = [
    { wch: 30 }, { wch: 40 }, { wch: 15 }, { wch: 15 }
  ]

  utils.book_append_sheet(wb, ws, 'Store Sale Report')
  writeFile(wb, `StoreSaleReport_${fromDate.value}_to_${toDate.value}.xlsx`)
}

onMounted(() => {
  fetchData()
})
</script>
