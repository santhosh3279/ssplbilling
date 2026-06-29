<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">

    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            @click="router.push('/')"
          >
            ← Back
          </button>
          <div>
            <h1 class="text-3xl font-normal text-[var(--color-text)] uppercase tracking-wider">REPORT</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Business reports and analytics</p>
          </div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar with Buttons -->
      <aside class="w-80 border-r border-[var(--color-border)] bg-[var(--color-surface)]/30 p-6 space-y-4">
        <h3 class="text-lg font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Tax Register</h3>
        <div class="flex flex-col gap-3">
          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('invoice')"
          >
            <span class="text-xl">📊</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Sales Tax Register</div>
              <div class="text-base text-[var(--color-text-muted)]">Submitted Sales Invoices</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/50 hover:border-[var(--color-border)] hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('quotation')"
          >
            <span class="text-xl">📄</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Quotation Register</div>
              <div class="text-base text-[var(--color-text-muted)]">All Quotations</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-success)]/20 hover:border-[var(--color-success)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('hsn')"
          >
            <span class="text-xl">📋</span>
            <div class="text-left">
              <div class="text-lg font-semibold">HSN Summary</div>
              <div class="text-base text-[var(--color-text-muted)]">Sales HSN-wise summary</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-success)]/20 hover:border-[var(--color-success)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('quotation_hsn')"
          >
            <span class="text-xl">📊</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Quotation HSN Summary</div>
              <div class="text-base text-[var(--color-text-muted)]">Quotation HSN-wise summary</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-warning)]/20 hover:border(--color-warning)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('item_summary')"
          >
            <span class="text-xl">📦</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Item Sales Summary</div>
              <div class="text-base text-[var(--color-text-muted)]">Total items sold by code</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-warning)]/20 hover:border(--color-warning)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="openModal('store_summary')"
          >
            <span class="text-xl">🏬</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Store Wise Item Sales</div>
              <div class="text-base text-[var(--color-text-muted)]">Items sold by Store & Code</div>
            </div>
          </button>

          <hr class="border-[var(--color-border)] my-1" />

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="router.push('/store-sale-report')"
          >
            <span class="text-xl">🏪</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Store Sale Report</div>
              <div class="text-base text-[var(--color-text-muted)]">Sales by store (Direct Income)</div>
            </div>
          </button>

          <button
            class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
            @click="router.push('/cost-center-sale-report')"
          >
            <span class="text-xl">🏢</span>
            <div class="text-left">
              <div class="text-lg font-semibold">Cost Center Sale Report</div>
              <div class="text-base text-[var(--color-text-muted)]">Sales by Cost Center (Direct Income)</div>
            </div>
          </button>
        </div>
      </aside>

      <!-- Body placeholder -->
      <main class="flex-1 flex items-center justify-center p-12">
        <div class="text-center text-[var(--color-text-muted)] max-w-sm">
          <div class="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[var(--color-surface)] text-4xl shadow-inner border border-[var(--color-border)]">
            📈
          </div>
          <h2 class="text-xl font-bold text-[var(--color-text)] mb-2">Ready to analyze?</h2>
          <p class="text-sm leading-relaxed">Select a report from the sidebar on the left to generate and download your data.</p>
        </div>
      </main>
    </div>

    <!-- ====== SHARED MODAL ====== -->
    <transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="showModal = false"
      >
        <div class="w-full max-w-md rounded-2xl bg-[var(--color-surface)] shadow-2xl border border-[var(--color-border)]">

          <!-- Modal header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-4">
            <div>
              <h2 class="text-2xl font-bold text-[var(--color-text)]">{{ modalConfig.title }}</h2>
              <p class="text-base text-[var(--color-text-muted)] mt-0.5">{{ modalConfig.subtitle }}</p>
            </div>
            <button
              class="rounded-lg p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
              @click="showModal = false"
            >
              ✕
            </button>
          </div>

          <!-- Modal body -->
          <div class="px-6 py-5 space-y-4">
            <!-- Series selector -->
            <div v-if="reportType !== 'store_summary'">
              <label class="mb-1.5 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                {{ modalConfig.seriesLabel }}
              </label>
              <select
                v-model="selectedSeries"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              >
                <option value="" disabled>— Select a series —</option>
                <option v-for="s in currentSeriesList" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>

            <!-- Income Account (Only for Store Wise) -->
            <div v-if="reportType === 'store_summary'">
              <label class="mb-1.5 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Income Account
              </label>
              <select
                v-model="selectedIncomeAccount"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              >
                <option value="">— All Income Accounts —</option>
                <option v-for="acc in incomeAccountList" :key="acc" :value="acc">{{ acc }}</option>
              </select>
            </div>

            <!-- Date range -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1.5 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From Date</label>
                <input
                  v-model="fromDate"
                  type="date"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
                />
              </div>
              <div>
                <label class="mb-1.5 block text-base font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To Date</label>
                <input
                  v-model="toDate"
                  type="date"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
                />
              </div>
            </div>

            <div class="flex justify-start">
              <button
                class="text-sm font-medium text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors"
                @click="setLastMonth"
              >
                📅 Set Last Month
              </button>
            </div>

            <!-- Error -->
            <p v-if="modalError" class="text-sm text-[var(--color-danger)]">{{ modalError }}</p>
          </div>

          <!-- Modal footer -->
          <div class="flex justify-end gap-2 border-t border-[var(--color-border)] px-6 py-4">
            <button
              class="rounded-lg px-4 py-2 text-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
              @click="showModal = false"
            >
              Cancel
            </button>
            <button
              class="flex items-center gap-2 rounded-lg px-5 py-2 text-lg font-semibold text-[var(--color-text-on-highlight)] disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all"
              :class="modalConfig.btnClass"
              :disabled="generating || (!selectedSeries && reportType !== 'store_summary')"
              @click="generateReport"
            >
              <span v-if="generating" class="animate-spin">⏳</span>
              <span v-else>⬇ Generate Excel</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { utils, writeFile } from 'xlsx'
import { getSalesTaxRegister, getQuotationTaxRegister, getQuotationSeries, getHsnSummaryReport, getQuotationHsnSummaryReport, getItemSummaryReport, getStoreWiseItemSalesReport, getIncomeAccounts } from '../api.js'
import { dashboardApi } from '../services/dashboard'

const router = useRouter()

// ── Series & Account data ───────────────────────────────────────────────────
const invoiceSeriesList = ref([])
const quotationSeriesList = ref([])
const incomeAccountList = ref([])

onMounted(async () => {
  // Invoice series (from billing settings)
  try {
    const d = await dashboardApi.getAllowedSeries()
    invoiceSeriesList.value = d.allowed_series || []
  } catch {
    invoiceSeriesList.value = []
  }

  // Quotation series (from doctype meta)
  try {
    quotationSeriesList.value = await getQuotationSeries() || []
  } catch {
    quotationSeriesList.value = []
  }

  // Income Accounts
  try {
    incomeAccountList.value = await getIncomeAccounts() || []
  } catch {
    incomeAccountList.value = []
  }
})

// ── Date defaults (current FY) ────────────────────────────────────────────────
function defaultDates() {
  const today = new Date()
  const fy = today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1
  return {
    from: `${fy}-04-01`,
    to: today.toISOString().slice(0, 10),
  }
}

function setLastMonth() {
  const today = new Date()
  const firstDayPrevMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  const lastDayPrevMonth = new Date(today.getFullYear(), today.getMonth(), 0)

  // Use local timezone format (YYYY-MM-DD)
  const fmt = (d) => {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  fromDate.value = fmt(firstDayPrevMonth)
  toDate.value = fmt(lastDayPrevMonth)
}

// ── Modal state ───────────────────────────────────────────────────────────────
const showModal = ref(false)
const reportType = ref('invoice') // 'invoice' | 'order' | 'quotation'
const selectedSeries = ref('')
const selectedIncomeAccount = ref('')
const fromDate = ref('')
const toDate = ref('')
const generating = ref(false)
const modalError = ref('')

const modalConfig = computed(() => {
  if (reportType.value === 'quotation') {
    return {
      title: 'Quotation Tax Register',
      subtitle: 'GST-wise summary of quotations (Draft & Submitted)',
      seriesLabel: 'Quotation Series',
      btnClass: 'bg-[var(--color-highlight)] hover:opacity-90',
      sheetName: 'Quotation Tax Register',
      filePrefix: 'QuotationTaxRegister',
      noDataMsg: 'No quotations found for the selected criteria.',
      docLabel: 'Quotation No',
    }
  }
  if (reportType.value === 'hsn') {
    return {
      title: 'HSN Summary',
      subtitle: 'HSN-wise summary of submitted sales invoices',
      seriesLabel: 'Invoice Series',
      btnClass: 'bg-[var(--color-success)] hover:bg-[var(--color-success)]',
      sheetName: 'HSN Summary',
      filePrefix: 'HSNSummary',
      noDataMsg: 'No HSN data found for the selected criteria.',
      docLabel: 'HSN Code',
    }
  }
  if (reportType.value === 'quotation_hsn') {
    return {
      title: 'Quotation HSN Summary',
      subtitle: 'HSN-wise summary of quotations (Draft & Submitted)',
      seriesLabel: 'Quotation Series',
      btnClass: 'bg-[var(--color-success)] hover:bg-[var(--color-success)]',
      sheetName: 'Quotation HSN Summary',
      filePrefix: 'QuotationHSNSummary',
      noDataMsg: 'No HSN data found for the selected criteria.',
      docLabel: 'HSN Code',
    }
  }
  if (reportType.value === 'item_summary') {
    return {
      title: 'Item Sales Summary',
      subtitle: 'Consolidated sales by item code',
      seriesLabel: 'Invoice Series',
      btnClass: 'bg-[var(--color-warning)] hover:bg-[var(--color-warning)]',
      sheetName: 'Item Sales Summary',
      filePrefix: 'ItemSalesSummary',
      noDataMsg: 'No sales data found for the selected criteria.',
      docLabel: 'Item Code',
    }
  }
  if (reportType.value === 'store_summary') {
    return {
      title: 'Store Wise Item Sales',
      subtitle: 'Consolidated sales by Store & Item',
      seriesLabel: 'Invoice Series',
      btnClass: 'bg-[var(--color-warning)] hover:bg-[var(--color-warning)]',
      sheetName: 'Store Wise Item Sales',
      filePrefix: 'StoreWiseItemSales',
      noDataMsg: 'No sales data found for the selected criteria.',
      docLabel: 'Item Code',
    }
  }
  return {
    title: 'Sales Tax Register',
    subtitle: 'GST-wise summary of submitted sales invoices',
    seriesLabel: 'Invoice Series',
    btnClass: 'bg-[var(--color-info)] hover:bg-[var(--color-info)]',
    sheetName: 'Sales Tax Register',
    filePrefix: 'SalesTaxRegister',
    noDataMsg: 'No submitted invoices found for the selected criteria.',
    docLabel: 'Invoice No',
  }
})

const currentSeriesList = computed(() => {
  if (reportType.value === 'quotation' || reportType.value === 'quotation_hsn') return quotationSeriesList.value
  return invoiceSeriesList.value
})

function openModal(type) {
  reportType.value = type
  modalError.value = ''
  selectedIncomeAccount.value = ''
  let list = []
  if (type === 'quotation' || type === 'quotation_hsn') list = quotationSeriesList.value
  else list = invoiceSeriesList.value

  selectedSeries.value = list.length ? list[0] : ''
  const d = defaultDates()
  fromDate.value = d.from
  toDate.value = d.to
  showModal.value = true
}

// ── Report generation ─────────────────────────────────────────────────────────
async function generateReport() {
  modalError.value = ''
  if (!selectedSeries.value && reportType.value !== 'store_summary') {
    modalError.value = 'Please select a series.'
    return
  }
  generating.value = true
  try {
    let rows = []
    if (reportType.value === 'quotation') {
      rows = await getQuotationTaxRegister(selectedSeries.value, fromDate.value, toDate.value)
    } else if (reportType.value === 'hsn') {
      rows = await getHsnSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
    } else if (reportType.value === 'quotation_hsn') {
      rows = await getQuotationHsnSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
    } else if (reportType.value === 'item_summary') {
      rows = await getItemSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
    } else if (reportType.value === 'store_summary') {
      rows = await getStoreWiseItemSalesReport(fromDate.value, toDate.value, selectedIncomeAccount.value)
    } else {
      rows = await getSalesTaxRegister(selectedSeries.value, fromDate.value, toDate.value)
    }

    if (!rows || rows.length === 0) {
      modalError.value = modalConfig.value.noDataMsg
      return
    }

    if (reportType.value === 'hsn' || reportType.value === 'quotation_hsn') {
      buildHSNExcel(rows)
    } else if (reportType.value === 'item_summary') {
      buildItemSummaryExcel(rows)
    } else if (reportType.value === 'store_summary') {
      buildStoreWiseItemSummaryExcel(rows)
    } else {
      buildExcel(rows)
    }
    showModal.value = false
  } catch (e) {
    modalError.value = e.message || 'Failed to fetch report data.'
  } finally {
    generating.value = false
  }
}

// ── Excel builder ─────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(Number(n || 0).toFixed(2))
}

function buildStoreWiseItemSummaryExcel(rows) {
  const headers = [
    'Store (Income Account)', 'Item Code', 'Item Name', 'UOM', 'Total Quantity', 'Total Taxable Value'
  ]

  const data = rows.map(r => [
    r.income_account,
    r.item_code,
    r.item_name,
    r.stock_uom,
    fmt(r.total_qty),
    fmt(r.total_taxable_value),
  ])

  const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
  const totals = [
    'TOTAL', '', '', '',
    fmt(sum('total_qty')),
    fmt(sum('total_taxable_value')),
  ]

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data, totals])
  ws['!cols'] = [
    { wch: 30 }, { wch: 20 }, { wch: 35 }, { wch: 10 }, { wch: 15 }, { wch: 20 }
  ]

  utils.book_append_sheet(wb, ws, 'Store Item Summary')

  const acc = selectedIncomeAccount.value ? '_' + selectedIncomeAccount.value.replace(/[^A-Za-z0-9]/g, '') : ''
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  writeFile(wb, `StoreWiseItemSales${acc}_${from}_to_${to}.xlsx`)
}

function buildItemSummaryExcel(rows) {
  const headers = [
    'Item Code', 'Item Name', 'UOM', 'Total Quantity', 'Total Taxable Value'
  ]

  const data = rows.map(r => [
    r.item_code,
    r.item_name,
    r.stock_uom,
    fmt(r.total_qty),
    fmt(r.total_taxable_value),
  ])

  const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
  const totals = [
    'TOTAL', '', '',
    fmt(sum('total_qty')),
    fmt(sum('total_taxable_value')),
  ]

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data, totals])
  ws['!cols'] = [
    { wch: 20 }, { wch: 35 }, { wch: 10 }, { wch: 15 }, { wch: 20 }
  ]

  utils.book_append_sheet(wb, ws, 'Item Summary')

  const series = selectedSeries.value.replace(/[^A-Za-z0-9]/g, '')
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  writeFile(wb, `ItemSalesSummary_${series}_${from}_to_${to}.xlsx`)
}

function buildHSNExcel(rows) {
  // Group rows by hsn_code
  const groups = {}
  for (const r of rows) {
    const hsn = r.hsn_code || 'N/A'
    if (!groups[hsn]) {
      groups[hsn] = []
    }
    groups[hsn].push(r)
  }

  const aoa = []
  const hsnCodes = Object.keys(groups).sort()

  let grandQty = 0
  let grandTaxable = 0
  let grandSgst = 0
  let grandCgst = 0
  let grandIgst = 0
  let grandTax = 0
  let grandValue = 0

  for (const hsn of hsnCodes) {
    // First row: HSN code header
    aoa.push([`HSN Code: ${hsn}`])

    // Table header row: date, bill no, qty, taxable, sgst, cgst, igst, total tax, total value
    aoa.push([
      'Date',
      'Bill No',
      'Quantity',
      'Taxable Value',
      'SGST Amount',
      'CGST Amount',
      'IGST Amount',
      'Total Tax',
      'Total Value'
    ])

    // All bills under this HSN code
    const groupRows = groups[hsn]
    let hsnQty = 0
    let hsnTaxable = 0
    let hsnSgst = 0
    let hsnCgst = 0
    let hsnIgst = 0
    let hsnTax = 0
    let hsnValue = 0

    for (const r of groupRows) {
      const qty = fmt(r.qty)
      const taxable = fmt(r.taxable_value)
      const sgst = fmt(r.sgst)
      const cgst = fmt(r.cgst)
      const igst = fmt(r.igst)
      const tax = fmt(sgst + cgst + igst)
      const val = fmt(taxable + tax)

      aoa.push([
        r.date || '',
        r.bill_no || '',
        qty,
        taxable,
        sgst,
        cgst,
        igst,
        tax,
        val
      ])

      hsnQty += qty
      hsnTaxable += taxable
      hsnSgst += sgst
      hsnCgst += cgst
      hsnIgst += igst
      hsnTax += tax
      hsnValue += val
    }

    // Add HSN subtotal row
    aoa.push([
      'Subtotal',
      '',
      fmt(hsnQty),
      fmt(hsnTaxable),
      fmt(hsnSgst),
      fmt(hsnCgst),
      fmt(hsnIgst),
      fmt(hsnTax),
      fmt(hsnValue)
    ])

    grandQty += hsnQty
    grandTaxable += hsnTaxable
    grandSgst += hsnSgst
    grandCgst += hsnCgst
    grandIgst += hsnIgst
    grandTax += hsnTax
    grandValue += hsnValue

    // Add a blank row to separate HSN sections
    aoa.push([])
  }

  // Grand Total row at the end
  if (hsnCodes.length > 0) {
    aoa.push([
      'GRAND TOTAL',
      '',
      fmt(grandQty),
      fmt(grandTaxable),
      fmt(grandSgst),
      fmt(grandCgst),
      fmt(grandIgst),
      fmt(grandTax),
      fmt(grandValue)
    ])
  }

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet(aoa)
  ws['!cols'] = [
    { wch: 12 }, // Date
    { wch: 20 }, // Bill No
    { wch: 12 }, // Quantity
    { wch: 15 }, // Taxable Value
    { wch: 15 }, // SGST Amount
    { wch: 15 }, // CGST Amount
    { wch: 15 }, // IGST Amount
    { wch: 15 }, // Total Tax
    { wch: 15 }  // Total Value
  ]

  utils.book_append_sheet(wb, ws, modalConfig.value.sheetName)

  const series = selectedSeries.value.replace(/[^A-Za-z0-9]/g, '')
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  writeFile(wb, `${modalConfig.value.filePrefix}_${series}_${from}_to_${to}.xlsx`)
}

function buildExcel(rows) {
  const docLabel = modalConfig.value.docLabel
  const rType = reportType.value

  const headers = [
    docLabel, 'Date', 'Customer Code', 'Customer Name',
    'Taxable Amount',
    'CGST Rate %', 'CGST Amount',
    'SGST Rate %', 'SGST Amount',
    'IGST Rate %', 'IGST Amount',
    'Other Tax', 'Total Tax', 'Grand Total',
  ]

  const data = rows.map(r => [
    rType === 'order' ? r.order_no : (rType === 'quotation' ? r.quotation_no : r.invoice_no),
    r.date,
    r.customer,
    r.customer_name,
    fmt(r.taxable_amount),
    fmt(r.cgst_rate),
    fmt(r.cgst_amount),
    fmt(r.sgst_rate),
    fmt(r.sgst_amount),
    fmt(r.igst_rate),
    fmt(r.igst_amount),
    fmt(r.other_tax),
    fmt(r.total_tax),
    fmt(r.grand_total),
  ])

  const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
  const totals = [
    'TOTAL', '', '', '',
    fmt(sum('taxable_amount')),
    '', fmt(sum('cgst_amount')),
    '', fmt(sum('sgst_amount')),
    '', fmt(sum('igst_amount')),
    fmt(sum('other_tax')),
    fmt(sum('total_tax')),
    fmt(sum('grand_total')),
  ]

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data, totals])
  ws['!cols'] = [
    { wch: 20 }, { wch: 12 }, { wch: 20 }, { wch: 30 },
    { wch: 14 }, { wch: 10 }, { wch: 12 },
    { wch: 10 }, { wch: 12 },
    { wch: 10 }, { wch: 12 },
    { wch: 10 }, { wch: 12 }, { wch: 14 },
  ]

  utils.book_append_sheet(wb, ws, modalConfig.value.sheetName)

  const series = selectedSeries.value.replace(/[^A-Za-z0-9]/g, '')
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  writeFile(wb, `${modalConfig.value.filePrefix}_${series}_${from}_to_${to}.xlsx`)
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
