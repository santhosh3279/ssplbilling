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
            <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Stock Status Report</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Real-time stock status with advanced filters</p>
          </div>
        </div>
        <div>
          <button
            @click="exportStockReportToExcel"
            :disabled="loadingStockData || !stockReportRows.length"
            class="flex items-center gap-2 rounded-lg bg-[var(--color-success)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--color-success)]/80 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-950/20"
          >
            <span>⬇</span> Export Excel
          </button>
        </div>
      </div>
    </header>

    <main class="flex-1 overflow-hidden flex flex-col p-6">
      <!-- Filters Row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border)] mb-4">
        <!-- Search -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Search Item</label>
          <input
            v-model="stockFilters.search"
            type="text"
            placeholder="Code or Name..."
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          />
        </div>

        <!-- Warehouse -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Warehouse</label>
          <select
            v-model="stockFilters.warehouse"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          >
            <option value="">— All Warehouses —</option>
            <option v-for="wh in filterOptions.warehouses" :key="wh" :value="wh">{{ wh }}</option>
          </select>
        </div>

        <!-- Supplier -->
        <div>
          <label class="mb-1 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Supplier</label>
          <select
            v-model="stockFilters.supplier"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-1 text-xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          >
            <option value="">— All Suppliers —</option>
            <option v-for="sup in filterOptions.suppliers" :key="sup.id" :value="sup.id">{{ sup.name }}</option>
          </select>
        </div>

        <!-- Negative Stock and Reset -->
        <div class="flex items-center justify-between pt-5">
          <label class="flex items-center gap-2 cursor-pointer select-none text-xl text-[var(--color-text)]">
            <input
              v-model="stockFilters.negativeOnly"
              type="checkbox"
              class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)] w-5 h-5"
            />
            <span>Negative Stock Only</span>
          </label>
          
          <button
            @click="resetStockFilters"
            class="text-base text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-colors underline"
          >
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Report Data Table -->
      <div
        @scroll="handleScroll"
        class="flex-1 overflow-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
      >
        <div v-if="loadingStockData" class="flex h-64 items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-violet-500"></div>
            <p class="text-sm text-[var(--color-text-muted)] font-medium">Fetching stock status...</p>
          </div>
        </div>
        
        <div v-else-if="!filteredStockRows.length" class="flex h-64 flex-col items-center justify-center text-[var(--color-text-muted)]">
          <span class="text-4xl mb-2">📭</span>
          <p class="text-sm">No items found matching the selected filters.</p>
        </div>

        <table v-else class="w-full border-collapse text-left text-xl whitespace-nowrap">
          <thead class="sticky top-0 bg-[var(--color-lowlight)] border-b border-[var(--color-border)] z-10 text-[var(--color-text)]">
            <tr>
              <th class="px-2 py-1.5 font-semibold">Item Code</th>
              <th class="px-2 py-1.5 font-semibold">Item Name</th>
              <th class="px-2 py-1.5 font-semibold">Warehouse</th>
              <th class="px-2 py-1.5 font-semibold text-right">Actual Stock</th>
              <th class="px-2 py-1.5 font-semibold text-right">Safety Stock</th>
              <th class="px-2 py-1.5 font-semibold text-right">Max Stock</th>
              <th class="px-2 py-1.5 font-semibold">UOM</th>
              <th class="px-2 py-1.5 font-semibold">Linked Suppliers</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)] text-[var(--color-text)] font-mono">
            <tr
              v-for="(row, idx) in displayedStockRows"
              :key="row.item_code + '_' + row.warehouse"
              class="transition-colors"
              :class="focusedRowIdx === idx ? 'stock-row-focused bg-[var(--color-focus)] text-[var(--color-text-on-focus)] font-bold shadow-sm' : 'hover:bg-[var(--color-surface-raised)]/30'"
            >
              <td class="px-2 py-1 font-bold">{{ row.item_code }}</td>
              <td class="px-2 py-1 font-sans">{{ row.item_name }}</td>
              <td class="px-2 py-1 font-sans" :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'">{{ row.warehouse }}</td>
              <td class="px-2 py-1 text-right font-semibold tabular-nums" :class="focusedRowIdx === idx ? '' : (row.actual_stock < 0 ? 'text-[var(--color-danger)]' : '')">
                {{ row.actual_stock }}
              </td>
              <td class="px-2 py-1 text-right tabular-nums" :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'">{{ row.safety_stock }}</td>
              <td class="px-2 py-1 text-right tabular-nums" :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'">{{ row.max_stock }}</td>
              <td class="px-2 py-1 font-sans uppercase tracking-wider" :class="focusedRowIdx === idx ? '' : 'text-[var(--color-text-muted)]'">{{ row.stock_uom }}</td>
              <td class="px-2 py-1 font-sans max-w-xs truncate" :title="row.suppliers">{{ row.suppliers || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchStockReportFilters, fetchStockReportData } from '../api.js'
import ExcelJS from 'exceljs'

const router = useRouter()

const loadingStockData = ref(false)
const stockReportRows = ref([])
const focusedRowIdx = ref(-1)
const maxDisplayed = ref(100)
const filterOptions = ref({ warehouses: [], suppliers: [] })

const stockFilters = ref({
  search: '',
  warehouse: '',
  supplier: '',
  negativeOnly: false
})

async function loadStockReportFilters() {
  try {
    const company = localStorage.getItem('wb-company') || ''
    const res = await fetchStockReportFilters(company)
    filterOptions.value = res || { warehouses: [], suppliers: [] }
  } catch (err) {
    console.error('Failed to load stock report filters:', err)
  }
}

async function loadStockReportData() {
  loadingStockData.value = true
  try {
    const company = localStorage.getItem('wb-company') || ''
    const data = await fetchStockReportData({
      company: company,
      warehouse: stockFilters.value.warehouse,
      supplier: stockFilters.value.supplier,
      negative_only: stockFilters.value.negativeOnly
    })
    stockReportRows.value = data || []
    maxDisplayed.value = 100
    focusedRowIdx.value = stockReportRows.value.length ? 0 : -1
  } catch (err) {
    console.error('Failed to load stock report data:', err)
  } finally {
    loadingStockData.value = false
  }
}

watch(
  () => [stockFilters.value.warehouse, stockFilters.value.supplier, stockFilters.value.negativeOnly],
  () => {
    loadStockReportData()
  }
)

watch(
  () => stockFilters.value.search,
  () => {
    maxDisplayed.value = 100
    focusedRowIdx.value = 0
  }
)

watch(focusedRowIdx, (newIdx) => {
  if (newIdx >= maxDisplayed.value) {
    maxDisplayed.value = newIdx + 50
  }
})

function handleScroll(e) {
  const el = e.target
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 200) {
    if (maxDisplayed.value < filteredStockRows.value.length) {
      maxDisplayed.value += 100
    }
  }
}

const filteredStockRows = computed(() => {
  const query = stockFilters.value.search.trim().toLowerCase()
  let rows = stockReportRows.value
  
  if (query) {
    rows = rows.filter(r => 
      r.item_code.toLowerCase().includes(query) || 
      r.item_name.toLowerCase().includes(query)
    )
  }

  // Keep focused row index within bounds
  if (rows.length > 0) {
    if (focusedRowIdx.value < 0 || focusedRowIdx.value >= rows.length) {
      focusedRowIdx.value = 0
    }
  } else {
    focusedRowIdx.value = -1
  }

  return rows
})

const displayedStockRows = computed(() => {
  return filteredStockRows.value.slice(0, maxDisplayed.value)
})

function resetStockFilters() {
  stockFilters.value = {
    search: '',
    warehouse: '',
    supplier: '',
    negativeOnly: false
  }
}

function fmt(n) {
  return Number(Number(n || 0).toFixed(2))
}

async function exportStockReportToExcel() {
  const rows = filteredStockRows.value
  if (!rows || rows.length === 0) {
    alert('No data to export.')
    return
  }

  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet('Stock Status')

  worksheet.columns = [
    { key: 'item_code', width: 20 },
    { key: 'item_name', width: 35 },
    { key: 'warehouse', width: 25 },
    { key: 'actual_stock', width: 15 },
    { key: 'safety_stock', width: 15 },
    { key: 'max_stock', width: 15 },
    { key: 'stock_uom', width: 10 },
    { key: 'suppliers', width: 35 }
  ]

  // Add Table Header
  const headerRow = worksheet.addRow([
    'Item Code', 'Item Name', 'Warehouse', 'Actual Stock', 'Safety Stock', 'Max Stock', 'UOM', 'Suppliers'
  ])
  headerRow.eachCell(cell => {
    cell.font = { name: 'Arial', bold: true }
    cell.alignment = { horizontal: 'center' }
    cell.border = {
      bottom: { style: 'thin' },
      top: { style: 'thin' }
    }
  })

  // Add Rows
  for (const r of rows) {
    worksheet.addRow([
      r.item_code,
      r.item_name,
      r.warehouse,
      fmt(r.actual_stock),
      fmt(r.safety_stock),
      fmt(r.max_stock),
      r.stock_uom,
      r.suppliers || ''
    ])
  }

  // Generate blob and download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  
  const fromStr = stockFilters.value.warehouse ? '_' + stockFilters.value.warehouse.replace(/[^A-Za-z0-9]/g, '') : ''
  const supStr = stockFilters.value.supplier ? '_' + stockFilters.value.supplier.replace(/[^A-Za-z0-9]/g, '') : ''
  const negStr = stockFilters.value.negativeOnly ? '_negative_only' : ''
  link.download = `StockStatusReport${fromStr}${supStr}${negStr}.xlsx`
  link.click()
}

function scrollToFocusedRow() {
  nextTick(() => {
    const el = document.querySelector('.stock-row-focused')
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

function handleKeyDown(e) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const len = filteredStockRows.value.length
    if (len > 0) {
      focusedRowIdx.value = (focusedRowIdx.value + 1) % len
      scrollToFocusedRow()
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const len = filteredStockRows.value.length
    if (len > 0) {
      focusedRowIdx.value = (focusedRowIdx.value - 1 + len) % len
      scrollToFocusedRow()
    }
  }
}

onMounted(() => {
  loadStockReportFilters()
  loadStockReportData()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
/* Optional: improve scrolling for wide tables */
.overflow-auto {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.overflow-auto::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.overflow-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-auto::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 20px;
}
</style>
