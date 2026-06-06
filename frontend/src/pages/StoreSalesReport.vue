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
            <p class="text-xs text-[var(--color-text-muted)]">Consolidated sales by Store (Income Account) & Price List</p>
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

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-5xl mx-auto">
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
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                <th class="w-12 px-2 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider sticky left-0 bg-[var(--color-surface)] z-20 border-b border-[var(--color-border)] text-center">S.No</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider sticky left-12 bg-[var(--color-surface)] z-20 border-b border-[var(--color-border)]">Store (Account)</th>
                <!-- Dynamic Price List Columns -->
                <th v-for="pl in priceLists" :key="pl" class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">
                  {{ pl }}
                </th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Total Amount</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider border-b border-[var(--color-border)]">Contribution %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr
                v-for="(row, idx) in reportData"
                :key="row.account"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors group"
              >
                <td class="w-12 px-2 py-2 sticky left-0 bg-[var(--color-surface)] group-hover:bg-[var(--color-surface-raised)]/30 z-10 font-mono text-lg text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 text-center">
                  {{ idx + 1 }}
                </td>
                <td class="px-6 py-2 sticky left-12 bg-[var(--color-surface)] group-hover:bg-[var(--color-surface-raised)]/30 z-10 border-b border-[var(--color-border)]/50">
                  <div class="text-lg font-semibold text-[var(--color-text)] group-hover:text-[var(--color-text)]">{{ row.store_name }}</div>
                  <div class="text-[15px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.account }}</div>
                </td>
                <!-- Dynamic Price List Values -->
                <td v-for="pl in priceLists" :key="pl" class="px-6 py-2 text-right font-mono text-xl border-b border-[var(--color-border)]/50">
                  <span v-if="row.price_list_data[pl]" class="text-[var(--color-text)]">
                    {{ formatCurrency(row.price_list_data[pl]) }}
                  </span>
                  <span v-else class="text-[var(--color-text-muted)] opacity-30">—</span>
                </td>
                <td class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text)] border-b border-[var(--color-border)]/50">
                  {{ formatCurrency(row.total_amount) }}
                </td>
                <td class="px-6 py-2 text-right border-b border-[var(--color-border)]/50">
                  <div class="flex items-center justify-end gap-3">
                    <div class="w-24 h-1.5 bg-[var(--color-surface-raised)] rounded-full overflow-hidden">
                      <div
                        class="h-full bg-[var(--color-info)] rounded-full"
                        :style="{ width: `${(row.total_amount / grandTotal * 100).toFixed(1)}%` }"
                      ></div>
                    </div>
                    <span class="text-lg font-semibold text-[var(--color-text-muted)]">
                      {{ (row.total_amount / grandTotal * 100).toFixed(1) }}%
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="w-12 px-2 py-1.5 text-lg sticky left-0 bg-[var(--color-bg)] z-10 border-t border-[var(--color-border)]"></td>
                <td class="px-6 py-1.5 text-lg sticky left-12 bg-[var(--color-bg)] z-10 border-t border-[var(--color-border)]">GRAND TOTAL</td>
                <!-- Price List Totals -->
                <td v-for="pl in priceLists" :key="pl" class="px-6 py-1.5 text-right font-mono text-xl text-[var(--color-text)] border-t border-[var(--color-border)]">
                   {{ formatCurrency(getPriceListTotal(pl)) }}
                </td>
                <td class="px-6 py-1.5 text-right text-3xl text-[var(--color-success)] border-t border-[var(--color-border)]">
                  {{ formatCurrency(grandTotal) }}
                </td>
                <td class="px-6 py-1.5 text-right text-lg text-[var(--color-text-muted)] font-bold border-t border-[var(--color-border)]">100.0%</td>
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
const priceLists = ref([])

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
    const res = await getStoreSaleReport(fromDate.value, toDate.value)
    reportData.value = res.report_data || []
    priceLists.value = res.price_lists || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch store sale report'
  } finally {
    loading.value = false
  }
}

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0
  }).format(val || 0)
}

function getPriceListTotal(pl) {
  return reportData.value.reduce((sum, row) => sum + (row.price_list_data[pl] || 0), 0)
}

function exportToExcel() {
  if (!reportData.value.length) return

  // Headers: S.No, Store, Account, Price Lists..., Total, Contribution
  const headers = ['S.No', 'Store Name', 'Account', ...priceLists.value, 'Total Amount', 'Contribution %']
  
  const data = reportData.value.map((r, idx) => {
    const row = [
      idx + 1,
      r.store_name,
      r.account
    ]
    // Add amounts for each price list
    priceLists.value.forEach(pl => {
      row.push(r.price_list_data[pl] || 0)
    })
    // Add Total and %
    row.push(r.total_amount)
    row.push(((r.total_amount / grandTotal.value) * 100).toFixed(2) + '%')
    return row
  })

  // Add Grand Total row
  const totalRow = ['', 'GRAND TOTAL', '']
  priceLists.value.forEach(pl => {
    totalRow.push(getPriceListTotal(pl))
  })
  totalRow.push(grandTotal.value)
  totalRow.push('100%')
  data.push(totalRow)

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])

  // Column widths: S.No(8), Store(30), Account(40), PLs(15 each), Total(15), %(15)
  const colWidths = [
    { wch: 8 }, { wch: 30 }, { wch: 40 }
  ]
  priceLists.value.forEach(() => colWidths.push({ wch: 15 }))
  colWidths.push({ wch: 15 }, { wch: 15 })
  ws['!cols'] = colWidths

  utils.book_append_sheet(wb, ws, 'Store Sale Report')
  writeFile(wb, `StoreSaleReport_${fromDate.value}_to_${toDate.value}.xlsx`)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* Optional: improve scrolling for wide tables */
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
