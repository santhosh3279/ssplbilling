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
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Stock Aging Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">FIFO-based ageing of available stock, item &times; warehouse-wise</p>
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
          <div class="flex items-center gap-2">
            <label class="text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</label>
            <select
              v-model="warehouse"
              class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1.5 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              @change="fetchData"
            >
              <option value="">— All Warehouses —</option>
              <option v-for="wh in warehouses" :key="wh" :value="wh">{{ wh }}</option>
            </select>
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
          <p class="text-sm text-[var(--color-text-muted)] font-medium">Computing stock ageing...</p>
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
          <h3 class="text-lg font-bold text-[var(--color-text)] mb-1">No stock found</h3>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">No available stock as on {{ asOnDate }}{{ warehouse ? ` in ${warehouse}` : '' }}.</p>
        </div>
      </div>

      <div v-else class="w-full">
        <!-- Data Table -->
        <div class="overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
          <table class="w-full text-left whitespace-nowrap border-separate border-spacing-0">
            <thead>
              <tr class="bg-[var(--color-surface-raised)]/50 border-b border-[var(--color-border)]">
                <th class="w-12 px-2 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider text-center">S.No</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Item</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Warehouse</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Available Qty</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Avg Age (Days)</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">0-30</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">31-60</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">61-90</th>
                <th class="px-6 py-2 text-right text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">91+</th>
                <th class="px-6 py-2 text-lg font-bold text-[var(--color-text-muted)] uppercase tracking-wider">UOM</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr
                v-for="(row, idx) in rows"
                :key="row.item_code + '_' + row.warehouse"
                class="hover:bg-[var(--color-surface-raised)]/30 transition-colors"
              >
                <td class="w-12 px-2 py-2 font-mono text-lg text-[var(--color-text-muted)] text-center">{{ idx + 1 }}</td>
                <td class="px-6 py-2">
                  <div class="text-lg font-semibold text-[var(--color-text)]">{{ row.item_name }}</div>
                  <div class="text-[15px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.item_code }}</div>
                </td>
                <td class="px-6 py-2 text-lg text-[var(--color-text-muted)]">{{ row.warehouse }}</td>
                <td class="px-6 py-2 text-right font-mono text-xl font-bold text-[var(--color-text)]">{{ formatQty(row.qty) }}</td>
                <td class="px-6 py-2 text-right font-mono text-lg" :class="row.average_age > 90 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                  {{ formatQty(row.average_age) }}
                </td>
                <td class="px-6 py-2 text-right font-mono text-lg text-[var(--color-text)]">{{ formatQty(row.range1) || '—' }}</td>
                <td class="px-6 py-2 text-right font-mono text-lg text-[var(--color-text)]">{{ formatQty(row.range2) || '—' }}</td>
                <td class="px-6 py-2 text-right font-mono text-lg text-[var(--color-warning)]">{{ formatQty(row.range3) || '—' }}</td>
                <td class="px-6 py-2 text-right font-mono text-lg text-[var(--color-danger)]">{{ formatQty(row.range4) || '—' }}</td>
                <td class="px-6 py-2 text-lg text-[var(--color-text-muted)]">{{ row.uom }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="bg-[var(--color-bg)]/50 border-t border-[var(--color-border)] font-black uppercase tracking-wider">
                <td class="w-12 px-2 py-1.5"></td>
                <td class="px-6 py-1.5 text-lg">TOTAL ({{ rows.length }} rows)</td>
                <td class="px-6 py-1.5"></td>
                <td class="px-6 py-1.5 text-right font-mono text-xl text-[var(--color-text)]">{{ formatQty(totalQty) }}</td>
                <td class="px-6 py-1.5"></td>
                <td class="px-6 py-1.5 text-right font-mono text-lg">{{ formatQty(totalRange1) }}</td>
                <td class="px-6 py-1.5 text-right font-mono text-lg">{{ formatQty(totalRange2) }}</td>
                <td class="px-6 py-1.5 text-right font-mono text-lg text-[var(--color-warning)]">{{ formatQty(totalRange3) }}</td>
                <td class="px-6 py-1.5 text-right font-mono text-lg text-[var(--color-danger)]">{{ formatQty(totalRange4) }}</td>
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
import { getStockAgingReport, fetchStockReportFilters } from '../api.js'
import { utils, writeFile } from 'xlsx'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const rows = ref([])
const asOnDate = ref(new Date().toISOString().slice(0, 10))
const warehouse = ref('')
const warehouses = ref([])

const totalQty = computed(() => rows.value.reduce((sum, r) => sum + (r.qty || 0), 0))
const totalRange1 = computed(() => rows.value.reduce((sum, r) => sum + (r.range1 || 0), 0))
const totalRange2 = computed(() => rows.value.reduce((sum, r) => sum + (r.range2 || 0), 0))
const totalRange3 = computed(() => rows.value.reduce((sum, r) => sum + (r.range3 || 0), 0))
const totalRange4 = computed(() => rows.value.reduce((sum, r) => sum + (r.range4 || 0), 0))

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const res = await getStockAgingReport(asOnDate.value, warehouse.value)
    rows.value = res.rows || []
  } catch (e) {
    error.value = e.message || 'Failed to fetch stock aging report'
  } finally {
    loading.value = false
  }
}

function formatQty(val) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(val || 0)
}

function exportToExcel() {
  if (!rows.value.length) return

  const headers = [
    'S.No', 'Item Code', 'Item Name', 'Warehouse', 'Available Qty', 'Avg Age (Days)',
    '0-30 Qty', '0-30 Value', '31-60 Qty', '31-60 Value', '61-90 Qty', '61-90 Value', '91+ Qty', '91+ Value',
    'Earliest (Days)', 'Latest (Days)', 'UOM',
  ]
  const data = rows.value.map((r, idx) => [
    idx + 1,
    r.item_code,
    r.item_name,
    r.warehouse,
    r.qty,
    r.average_age,
    r.range1, r.range1value,
    r.range2, r.range2value,
    r.range3, r.range3value,
    r.range4, r.range4value,
    r.earliest,
    r.latest,
    r.uom,
  ])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])
  ws['!cols'] = [
    { wch: 6 }, { wch: 16 }, { wch: 32 }, { wch: 16 }, { wch: 14 }, { wch: 12 },
    { wch: 10 }, { wch: 12 }, { wch: 10 }, { wch: 12 }, { wch: 10 }, { wch: 12 }, { wch: 10 }, { wch: 12 },
    { wch: 12 }, { wch: 10 }, { wch: 10 },
  ]
  utils.book_append_sheet(wb, ws, 'Stock Aging')

  const wh = warehouse.value ? '_' + warehouse.value.replace(/[^A-Za-z0-9]/g, '') : ''
  writeFile(wb, `StockAging_asOn_${asOnDate.value}${wh}.xlsx`)
}

onMounted(async () => {
  try {
    const filters = await fetchStockReportFilters()
    warehouses.value = filters.warehouses || []
  } catch {
    warehouses.value = []
  }
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
