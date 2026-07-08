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
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Ledger Sales & Purchase</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Customer and Supplier-wise summary of sales and purchase transactions</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
            <input
              v-model="fromDate"
              type="date"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              @change="fetchData"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
            <input
              v-model="toDate"
              type="date"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              @change="fetchData"
            />
          </div>
          <button
            class="flex items-center gap-2 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] active:scale-95 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!salesRows.length && !purchaseRows.length"
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
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching ledger data...</p>
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

      <div v-else-if="salesRows.length === 0 && purchaseRows.length === 0" class="flex h-96 items-center justify-center text-center">
        <div class="max-w-xs">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl border border-[var(--color-border)] shadow-inner">
            📭
          </div>
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No transaction data</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">No sales or purchase transactions found between {{ fromDate }} and {{ toDate }}.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 max-w-3xl mx-auto">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Sales</p>
            <p class="text-3xl font-black text-[var(--color-success)]">{{ formatCurrency(totalSales) }}</p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Purchases</p>
            <p class="text-3xl font-black text-[var(--color-danger)]">{{ formatCurrency(totalPurchases) }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
          <!-- Sales Ledgers -->
          <div class="flex flex-col gap-4">
            <h2 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider border-b border-[var(--color-border)] pb-2">Sales (Customer Wise)</h2>
            <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
              <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
                <thead>
                  <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                    <th class="w-12 px-3 py-2 text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider text-center">S.No</th>
                    <th class="px-4 py-2 text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Customer</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Debit (Dr)</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Credit (Cr)</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Net Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/50">
                  <tr
                    v-for="(row, idx) in salesRows"
                    :key="row.customer"
                    class="hover:bg-[var(--color-surface-raised)]/30 transition-colors"
                  >
                    <td class="w-12 px-3 py-2 font-mono text-base text-[var(--color-text-muted)] text-center">{{ idx + 1 }}</td>
                    <td class="px-4 py-2 text-base font-semibold text-[var(--color-text)] truncate max-w-[200px]" :title="row.customer_name">
                      <div>{{ row.customer_name }}</div>
                      <div class="text-xs text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.customer }}</div>
                    </td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-text-muted)]">{{ formatCurrency(row.debit) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-text-muted)]">{{ formatCurrency(row.credit) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base font-bold text-[var(--color-success)]">{{ formatCurrency(row.net_amount) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-semibold uppercase tracking-wider">
                    <td class="w-12 px-3 py-2"></td>
                    <td class="px-4 py-2 text-base">TOTAL</td>
                    <td class="px-4 py-2 text-right font-mono text-base">{{ formatCurrency(totalSalesDr) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base">{{ formatCurrency(totalSalesCr) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-success)]">{{ formatCurrency(totalSales) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Purchase Ledgers -->
          <div class="flex flex-col gap-4">
            <h2 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider border-b border-[var(--color-border)] pb-2">Purchase (Supplier Wise)</h2>
            <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
              <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
                <thead>
                  <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                    <th class="w-12 px-3 py-2 text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider text-center">S.No</th>
                    <th class="px-4 py-2 text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Supplier</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Debit (Dr)</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Credit (Cr)</th>
                    <th class="px-4 py-2 text-right text-base font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Net Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/50">
                  <tr
                    v-for="(row, idx) in purchaseRows"
                    :key="row.supplier"
                    class="hover:bg-[var(--color-surface-raised)]/30 transition-colors"
                  >
                    <td class="w-12 px-3 py-2 font-mono text-base text-[var(--color-text-muted)] text-center">{{ idx + 1 }}</td>
                    <td class="px-4 py-2 text-base font-semibold text-[var(--color-text)] truncate max-w-[200px]" :title="row.supplier_name">
                      <div>{{ row.supplier_name }}</div>
                      <div class="text-xs text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.supplier }}</div>
                    </td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-text-muted)]">{{ formatCurrency(row.debit) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-text-muted)]">{{ formatCurrency(row.credit) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base font-bold text-[var(--color-danger)]">{{ formatCurrency(row.net_amount) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-semibold uppercase tracking-wider">
                    <td class="w-12 px-3 py-2"></td>
                    <td class="px-4 py-2 text-base">TOTAL</td>
                    <td class="px-4 py-2 text-right font-mono text-base">{{ formatCurrency(totalPurchaseDr) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base">{{ formatCurrency(totalPurchaseCr) }}</td>
                    <td class="px-4 py-2 text-right font-mono text-base text-[var(--color-danger)]">{{ formatCurrency(totalPurchases) }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLedgerWiseSalesPurchaseReport } from '../api.js'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const salesRows = ref([])
const purchaseRows = ref([])

// Current FY defaults
const today = new Date()
const fy = today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1
const fromDate = ref(`${fy}-04-01`)
const toDate = ref(today.toISOString().slice(0, 10))

const totalSales = computed(() => salesRows.value.reduce((sum, r) => sum + (r.net_amount || 0), 0))
const totalSalesDr = computed(() => salesRows.value.reduce((sum, r) => sum + (r.debit || 0), 0))
const totalSalesCr = computed(() => salesRows.value.reduce((sum, r) => sum + (r.credit || 0), 0))

const totalPurchases = computed(() => purchaseRows.value.reduce((sum, r) => sum + (r.net_amount || 0), 0))
const totalPurchaseDr = computed(() => purchaseRows.value.reduce((sum, r) => sum + (r.debit || 0), 0))
const totalPurchaseCr = computed(() => purchaseRows.value.reduce((sum, r) => sum + (r.credit || 0), 0))

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const res = await getLedgerWiseSalesPurchaseReport(fromDate.value, toDate.value)
    salesRows.value = res.sales || []
    purchaseRows.value = res.purchase || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch ledger-wise sales & purchase report'
  } finally {
    loading.value = false
  }
}

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(val || 0)
}

function fmt(n) {
  return Math.round(n || 0)
}

function exportToExcel() {
  const getSalesSheetData = (rows) => {
    const headers = ['Customer Code', 'Customer Name', 'Debit (Dr)', 'Credit (Cr)', 'Net Amount']
    const data = rows.map(r => [
      r.customer,
      r.customer_name,
      fmt(r.debit),
      fmt(r.credit),
      fmt(r.net_amount),
    ])

    const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
    const totals = [
      'GRAND TOTAL',
      '',
      fmt(sum('debit')),
      fmt(sum('credit')),
      fmt(sum('net_amount')),
    ]

    return { headers, data, totals }
  }

  const getPurchaseSheetData = (rows) => {
    const headers = ['Supplier Code', 'Supplier Name', 'Debit (Dr)', 'Credit (Cr)', 'Net Amount']
    const data = rows.map(r => [
      r.supplier,
      r.supplier_name,
      fmt(r.debit),
      fmt(r.credit),
      fmt(r.net_amount),
    ])

    const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
    const totals = [
      'GRAND TOTAL',
      '',
      fmt(sum('debit')),
      fmt(sum('credit')),
      fmt(sum('net_amount')),
    ]

    return { headers, data, totals }
  }

  const salesInfo = getSalesSheetData(salesRows.value)
  const purchaseInfo = getPurchaseSheetData(purchaseRows.value)

  const wb = utils.book_new()

  const wsSales = utils.aoa_to_sheet([salesInfo.headers, ...salesInfo.data, salesInfo.totals])
  wsSales['!cols'] = [{ wch: 20 }, { wch: 35 }, { wch: 20 }, { wch: 20 }, { wch: 20 }]
  utils.book_append_sheet(wb, wsSales, 'Sales Customer Wise')

  const wsPurchase = utils.aoa_to_sheet([purchaseInfo.headers, ...purchaseInfo.data, purchaseInfo.totals])
  wsPurchase['!cols'] = [{ wch: 20 }, { wch: 35 }, { wch: 20 }, { wch: 20 }, { wch: 20 }]
  utils.book_append_sheet(wb, wsPurchase, 'Purchase Supplier Wise')

  writeFile(wb, `SalesPurchase_CustSupplierWise_${fromDate.value}_to_${toDate.value}.xlsx`)
}

onMounted(() => {
  fetchData()
})
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
