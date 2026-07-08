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
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Outstanding Balance - Customers</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Receivable balance per customer as on a given date</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">As On</label>
            <input
              v-model="asOnDate"
              type="date"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              @change="fetchData"
            />
          </div>
          <button
            class="flex items-center gap-2 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-semibold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] active:scale-95 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!rows.length"
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
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching outstanding balances...</p>
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

      <div v-else-if="rows.length === 0" class="flex h-96 items-center justify-center text-center">
        <div class="max-w-xs">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl border border-[var(--color-border)] shadow-inner">
            📭
          </div>
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No outstanding balances</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">No customers have an outstanding balance as on {{ asOnDate }}.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-5xl mx-auto">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Debit (Dr)</p>
            <p class="text-3xl font-black text-[var(--color-danger)]">
              {{ formatCurrency(totalDebit) }}
            </p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Total Credit (Cr)</p>
            <p class="text-3xl font-black text-[var(--color-success)]">
              {{ formatCurrency(totalCredit) }}
            </p>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-2xl shadow-sm">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest mb-1">Customers with Balance</p>
            <p class="text-3xl font-black text-[var(--color-text)]">{{ rows.length }}</p>
          </div>
        </div>

        <!-- Data Table -->
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                <th class="w-12 px-2 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider text-center">S.No</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Customer</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Debit (Dr)</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Credit (Cr)</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Last Transaction</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr
                v-for="(row, idx) in rows"
                :key="row.customer"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors"
              >
                <td class="w-12 px-2 py-2 font-mono text-lg text-[var(--color-text-muted)] text-center">{{ idx + 1 }}</td>
                <td class="px-6 py-2">
                  <div class="text-lg font-semibold text-[var(--color-text)]">{{ row.customer_name }}</div>
                  <div class="text-[15px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.customer }}</div>
                </td>
                <td class="px-6 py-2 text-right font-mono text-xl font-bold">
                  <span v-if="row.outstanding_amount > 0" class="text-[var(--color-danger)]">
                    {{ formatCurrency(row.outstanding_amount) }}
                  </span>
                  <span v-else class="text-[var(--color-text-muted)]">—</span>
                </td>
                <td class="px-6 py-2 text-right font-mono text-xl font-bold">
                  <span v-if="row.outstanding_amount < 0" class="text-[var(--color-success)]">
                    {{ formatCurrency(Math.abs(row.outstanding_amount)) }}
                  </span>
                  <span v-else class="text-[var(--color-text-muted)]">—</span>
                </td>
                <td class="px-6 py-2 text-lg text-[var(--color-text-muted)]">{{ row.last_transaction_date }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="w-12 px-2 py-1.5"></td>
                <td class="px-6 py-1.5 text-lg">GRAND TOTAL</td>
                <td class="px-6 py-1.5 text-right font-mono text-2xl text-[var(--color-danger)]">{{ formatCurrency(totalDebit) }}</td>
                <td class="px-6 py-1.5 text-right font-mono text-2xl text-[var(--color-success)]">{{ formatCurrency(totalCredit) }}</td>
                <td class="px-6 py-1.5"></td>
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
import { getOutstandingCustomersReport } from '../api.js'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const rows = ref([])
const asOnDate = ref(new Date().toISOString().slice(0, 10))

const totalOutstanding = computed(() => rows.value.reduce((sum, r) => sum + (r.outstanding_amount || 0), 0))
const totalDebit = computed(() => rows.value.reduce((sum, r) => sum + (r.outstanding_amount > 0 ? r.outstanding_amount : 0), 0))
const totalCredit = computed(() => rows.value.reduce((sum, r) => sum + (r.outstanding_amount < 0 ? Math.abs(r.outstanding_amount) : 0), 0))

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const res = await getOutstandingCustomersReport(asOnDate.value)
    rows.value = res.rows || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch outstanding customers report'
  } finally {
    loading.value = false
  }
}

function formatCurrency(val) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(val || 0)
}

function exportToExcel() {
  if (!rows.value.length) return

  const headers = ['S.No', 'Customer Code', 'Customer Name', 'Debit (Dr)', 'Credit (Cr)', 'Last Transaction Date']
  const data = rows.value.map((r, idx) => {
    const isCr = (r.outstanding_amount || 0) < 0
    const amt = Math.abs(Math.round(r.outstanding_amount || 0))
    return [
      idx + 1,
      r.customer,
      r.customer_name,
      isCr ? '' : amt,
      isCr ? amt : '',
      r.last_transaction_date,
    ]
  })
  data.push(['', '', 'GRAND TOTAL', Math.round(totalDebit.value || 0), Math.round(totalCredit.value || 0), ''])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])
  ws['!cols'] = [{ wch: 8 }, { wch: 20 }, { wch: 35 }, { wch: 20 }, { wch: 20 }, { wch: 18 }]
  utils.book_append_sheet(wb, ws, 'Outstanding Customers')

  writeFile(wb, `OutstandingCustomers_asOn_${asOnDate.value}.xlsx`)
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
