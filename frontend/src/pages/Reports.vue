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
      <!-- Main Content (Reorganized into Four Columns) -->
      <main class="flex-1 bg-[var(--color-surface)]/30 p-6 overflow-y-auto">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 align-top max-w-7xl mx-auto">
          
          <!-- Column 1: Tax Register -->
          <div class="flex flex-col gap-3">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-2 mb-2">Tax Register</h3>
            
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
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="openModal('quotation')"
            >
              <span class="text-xl">📊</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Quotation Register</div>
                <div class="text-base text-[var(--color-text-muted)]">All Quotations (Draft & Submitted)</div>
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
          </div>

          <!-- Column 2: Sale Report -->
          <div class="flex flex-col gap-3">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-2 mb-2">Sale Report</h3>
            
            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-warning)]/20 hover:border-[var(--color-warning)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/item-sales-summary')"
            >
              <span class="text-xl">📦</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Item Sales Summary</div>
                <div class="text-base text-[var(--color-text-muted)]">Total items sold by code</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-warning)]/20 hover:border-[var(--color-warning)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/store-wise-item-sales')"
            >
              <span class="text-xl">🏬</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Store Wise Item Sales</div>
                <div class="text-base text-[var(--color-text-muted)]">Items sold by Store & Code</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-warning)]/20 hover:border-[var(--color-warning)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/fast-moving-items')"
            >
              <span class="text-xl">⚡</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Fast Moving Items</div>
                <div class="text-base text-[var(--color-text-muted)]">Top selling items by quantity</div>
              </div>
            </button>

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

          <!-- Column 3: Stock Report -->
          <div class="flex flex-col gap-3">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-2 mb-2">Stock Report</h3>
            
            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-success)]/20 hover:border-[var(--color-success)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/stock-status-report')"
            >
              <span class="text-xl">📈</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Stock Status Report</div>
                <div class="text-base text-[var(--color-text-muted)]">Check current item stock</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-success)]/20 hover:border-[var(--color-success)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/stock-aging-report')"
            >
              <span class="text-xl">⏳</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Stock Aging Report</div>
                <div class="text-base text-[var(--color-text-muted)]">FIFO ageing by item & warehouse</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-success)]/20 hover:border-[var(--color-success)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/material-transfer-report')"
            >
              <span class="text-xl">🔄</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Material Transfer Report</div>
                <div class="text-base text-[var(--color-text-muted)]">Stock Entry transfers by date</div>
              </div>
            </button>
          </div>

          <!-- Column 4: Accounts -->
          <div class="flex flex-col gap-3">
            <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-2 mb-2">Accounts</h3>
            
            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/cashflow-report')"
            >
              <span class="text-xl">💸</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Cashflow Report</div>
                <div class="text-base text-[var(--color-text-muted)]">Cost Center-wise Cash & Bank Flow</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-danger)]/20 hover:border-[var(--color-danger)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/outstanding-customers-report')"
            >
              <span class="text-xl">⚖️</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Outstanding Balance - Customers</div>
                <div class="text-base text-[var(--color-text-muted)]">Receivable balance per customer</div>
              </div>
            </button>

            <button
              class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-4 py-3 text-sm font-medium text-[var(--color-text)] hover:bg-[var(--color-info)]/20 hover:border-[var(--color-info)]/50 hover:text-[var(--color-text)] transition-all active:scale-[0.98]"
              @click="router.push('/ledger-sales-purchase-report')"
            >
              <span class="text-xl">📊</span>
              <div class="text-left">
                <div class="text-lg font-semibold">Ledger Sales & Purchase</div>
                <div class="text-base text-[var(--color-text-muted)]">Ledger-wise sales & purchase summary</div>
              </div>
            </button>
          </div>

        </div>
      </main>
    </div>

    <!-- ====== SHARED MODAL ====== -->
    <transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
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
            <div v-if="reportType !== 'store_summary' && reportType !== 'ledger_sales_purchase'">
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
              :disabled="generating || (!selectedSeries && reportType !== 'store_summary' && reportType !== 'ledger_sales_purchase')"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { utils, writeFile } from 'xlsx'
import ExcelJS from 'exceljs'
import { getSalesTaxRegister, getQuotationTaxRegister, getQuotationSeries, getHsnSummaryReport, getQuotationHsnSummaryReport, getItemSummaryReport, getStoreWiseItemSalesReport, getIncomeAccounts, getLedgerWiseSalesPurchaseReport } from '../api.js'
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
const activeTemplates = ref([])

const modalConfig = computed(() => {
  if (reportType.value === 'quotation') {
    return {
      title: 'Quotation Tax Register',
      subtitle: 'GST-wise summary of quotations (Draft & Submitted)',
      seriesLabel: 'Quotation Series',
      btnClass: 'bg-[var(--color-info)] hover:bg-[var(--color-info)]',
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
  // Cashflow report is now handled in CashflowReport.vue
  if (reportType.value === 'ledger_sales_purchase') {
    return {
      title: 'Ledger Sales & Purchase',
      subtitle: 'Ledger-wise sales and purchase summary',
      seriesLabel: '',
      btnClass: 'bg-[var(--color-info)] hover:bg-[var(--color-info)]',
      sheetName: 'Sales Ledger Wise',
      filePrefix: 'LedgerSalesPurchase',
      noDataMsg: 'No sales or purchase data found for the selected criteria.',
      docLabel: 'Account',
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
  if (!selectedSeries.value && reportType.value !== 'store_summary' && reportType.value !== 'ledger_sales_purchase') {
    modalError.value = 'Please select a series.'
    return
  }
  generating.value = true
  try {
    let rows = []
    let companyName = ''
    let companyAddressLines = []
    if (reportType.value === 'quotation') {
      const res = await getQuotationTaxRegister(selectedSeries.value, fromDate.value, toDate.value)
      rows = res.rows || []
      activeTemplates.value = res.active_templates || []
      companyName = res.company_name || ''
      companyAddressLines = res.company_address_lines || []
    } else if (reportType.value === 'hsn') {
      const res = await getHsnSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
      rows = res.rows || []
      companyName = res.company_name || ''
      companyAddressLines = res.company_address_lines || []
    } else if (reportType.value === 'quotation_hsn') {
      const res = await getQuotationHsnSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
      rows = res.rows || []
      companyName = res.company_name || ''
      companyAddressLines = res.company_address_lines || []
    } else if (reportType.value === 'item_summary') {
      rows = await getItemSummaryReport(selectedSeries.value, fromDate.value, toDate.value)
    } else if (reportType.value === 'store_summary') {
      rows = await getStoreWiseItemSalesReport(fromDate.value, toDate.value, selectedIncomeAccount.value)
    } else if (reportType.value === 'ledger_sales_purchase') {
      const res = await getLedgerWiseSalesPurchaseReport(fromDate.value, toDate.value)
      if ((!res.sales || res.sales.length === 0) && (!res.purchase || res.purchase.length === 0)) {
        modalError.value = modalConfig.value.noDataMsg
        return
      }
      buildLedgerSalesPurchaseExcel(res)
      showModal.value = false
      return
    // Cashflow report is now handled in CashflowReport.vue
    } else {
      const res = await getSalesTaxRegister(selectedSeries.value, fromDate.value, toDate.value)
      rows = res.rows || []
      activeTemplates.value = res.active_templates || []
      companyName = res.company_name || ''
      companyAddressLines = res.company_address_lines || []
    }

    if (!rows || rows.length === 0) {
      modalError.value = modalConfig.value.noDataMsg
      return
    }

    if (reportType.value === 'hsn' || reportType.value === 'quotation_hsn') {
      buildHSNExcel(rows, companyName, companyAddressLines)
    } else if (reportType.value === 'item_summary') {
      buildItemSummaryExcel(rows)
    } else if (reportType.value === 'store_summary') {
      buildStoreWiseItemSummaryExcel(rows)
    } else {
      buildExcel(rows, companyName, companyAddressLines)
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

function buildLedgerSalesPurchaseExcel(res) {
  const sales = res.sales || []
  const purchase = res.purchase || []

  const getSheetData = (rows) => {
    const headers = ['Account', 'Debit (Dr)', 'Credit (Cr)', 'Net Amount']
    const data = rows.map(r => [
      r.account,
      fmt(r.debit),
      fmt(r.credit),
      fmt(r.net_amount),
    ])

    const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
    const totals = [
      'GRAND TOTAL',
      fmt(sum('debit')),
      fmt(sum('credit')),
      fmt(sum('net_amount')),
    ]

    return { headers, data, totals }
  }

  const salesInfo = getSheetData(sales)
  const purchaseInfo = getSheetData(purchase)

  const wb = utils.book_new()

  const wsSales = utils.aoa_to_sheet([salesInfo.headers, ...salesInfo.data, salesInfo.totals])
  wsSales['!cols'] = [{ wch: 45 }, { wch: 20 }, { wch: 20 }, { wch: 20 }]
  utils.book_append_sheet(wb, wsSales, 'Sales Ledger Wise')

  const wsPurchase = utils.aoa_to_sheet([purchaseInfo.headers, ...purchaseInfo.data, purchaseInfo.totals])
  wsPurchase['!cols'] = [{ wch: 45 }, { wch: 20 }, { wch: 20 }, { wch: 20 }]
  utils.book_append_sheet(wb, wsPurchase, 'Purchase Ledger Wise')

  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  writeFile(wb, `LedgerSalesPurchase_${from}_to_${to}.xlsx`)
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

async function buildHSNExcel(rows, companyName, companyAddressLines) {
  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet(modalConfig.value.sheetName)

  // Configure column widths
  worksheet.columns = [
    { key: 'date', width: 14 },        // Date
    { key: 'bill_no', width: 22 },     // Bill No
    { key: 'qty', width: 14 },         // Quantity
    { key: 'taxable', width: 16 },     // Taxable Value
    { key: 'sgst', width: 16 },        // SGST Amount
    { key: 'cgst', width: 16 },        // CGST Amount
    { key: 'igst', width: 16 },        // IGST Amount
    { key: 'total_tax', width: 16 },    // Total Tax
    { key: 'total_value', width: 18 }   // Total Value
  ]

  // Add Company Name in row 1
  const row1 = worksheet.addRow([companyName || ''])
  row1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  row1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(1, 1, 1, 9)

  // Add Address lines in rows 2, 3, 4, 5
  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines[i] || ''
    const rowNum = i + 2
    const row = worksheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    worksheet.mergeCells(rowNum, 1, rowNum, 9)
  }

  // Row 6: Empty spacing row
  worksheet.addRow([])

  // Group rows by hsn_code
  const groups = {}
  for (const r of rows) {
    const hsn = r.hsn_code || 'N/A'
    if (!groups[hsn]) {
      groups[hsn] = []
    }
    groups[hsn].push(r)
  }

  const hsnCodes = Object.keys(groups).sort()

  let grandQty = 0
  let grandTaxable = 0
  let grandSgst = 0
  let grandCgst = 0
  let grandIgst = 0
  let grandTax = 0
  let grandValue = 0

  for (const hsn of hsnCodes) {
    // HSN code header row
    const hsnHeaderRow = worksheet.addRow([`HSN Code: ${hsn}`])
    hsnHeaderRow.getCell(1).font = { name: 'Arial', size: 11, bold: true }
    worksheet.mergeCells(hsnHeaderRow.number, 1, hsnHeaderRow.number, 9)

    // Table header row: Date, Bill No, Quantity, Taxable Value, SGST Amount, CGST Amount, IGST Amount, Total Tax, Total Value
    const tableHeaderRow = worksheet.addRow([
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
    tableHeaderRow.eachCell(cell => {
      cell.font = { name: 'Arial', bold: true }
      cell.alignment = { horizontal: 'center' }
      cell.border = {
        bottom: { style: 'thin' },
        top: { style: 'thin' }
      }
    })

    // Detailed rows
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

      worksheet.addRow([
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

    // Subtotal row
    const subtotalRow = worksheet.addRow([
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
    subtotalRow.eachCell((cell, colNumber) => {
      cell.font = { name: 'Arial', bold: true, italic: true }
      if (colNumber >= 3) {
        cell.border = {
          top: { style: 'thin' }
        }
      }
    })

    grandQty += hsnQty
    grandTaxable += hsnTaxable
    grandSgst += hsnSgst
    grandCgst += hsnCgst
    grandIgst += hsnIgst
    grandTax += hsnTax
    grandValue += hsnValue

    // Add empty row
    worksheet.addRow([])
  }

  // Grand Total row
  if (hsnCodes.length > 0) {
    const grandTotalRow = worksheet.addRow([
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
    grandTotalRow.eachCell((cell, colNumber) => {
      cell.font = { name: 'Arial', bold: true }
      if (colNumber >= 3 || colNumber === 1) {
        cell.border = {
          top: { style: 'thin' },
          bottom: { style: 'double' }
        }
      }
    })
  }

  // Generate blob and download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)

  const series = selectedSeries.value.replace(/[^A-Za-z0-9]/g, '')
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  link.download = `${modalConfig.value.filePrefix}_${series}_${from}_to_${to}.xlsx`
  link.click()
}

async function buildExcel(rows, companyName, companyAddressLines) {
  const docLabel = modalConfig.value.docLabel
  const rType = reportType.value

  const workbook = new ExcelJS.Workbook()
  const worksheet = workbook.addWorksheet(modalConfig.value.sheetName)

  const templateCols = []
  for (const t of activeTemplates.value) {
    templateCols.push({ key: `temp_taxable_${t.name}`, width: 18 }) // Taxable Value
    if (t.gst_rate > 0) {
      templateCols.push({ key: `temp_cgst_${t.name}`, width: 14 })    // CGST Amount
      templateCols.push({ key: `temp_sgst_${t.name}`, width: 14 })    // SGST Amount
      templateCols.push({ key: `temp_igst_${t.name}`, width: 14 })    // IGST Amount
      templateCols.push({ key: `temp_total_tax_${t.name}`, width: 16 }) // Total Tax for %
    }
  }

  // Configure column widths
  worksheet.columns = [
    { key: 'doc_no', width: 28 },       // docLabel
    { key: 'date', width: 14 },         // Date
    { key: 'cust_code', width: 18 },    // Customer Code
    { key: 'cust_name', width: 28 },    // Customer Name
    { key: 'cust_gstin', width: 18 },   // Customer GSTIN
    { key: 'taxable', width: 16 },      // Taxable Amount
    ...templateCols,
    { key: 'cgst_amt', width: 14 },     // CGST Amount
    { key: 'sgst_amt', width: 14 },     // SGST Amount
    { key: 'igst_amt', width: 14 },     // IGST Amount
    { key: 'other_tax', width: 14 },    // Other Tax
    { key: 'total_tax', width: 14 },    // Total Tax
    { key: 'grand_total', width: 18 }   // Grand Total
  ]

  const totalColsCount = 12 + templateCols.length

  // Add Company Name in row 1
  const row1 = worksheet.addRow([companyName || ''])
  row1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  row1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(1, 1, 1, totalColsCount)

  // Add Address lines in rows 2, 3, 4, 5
  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines[i] || ''
    const rowNum = i + 2
    const row = worksheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    worksheet.mergeCells(rowNum, 1, rowNum, totalColsCount)
  }

  // Add Period (From / To Date) in row 6
  const fromStr = fromDate.value || 'All'
  const toStr = toDate.value || 'All'
  const dateRow = worksheet.addRow([`Period: ${fromStr} to ${toStr}`])
  dateRow.getCell(1).font = { name: 'Arial', size: 11, bold: true, italic: true }
  dateRow.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(6, 1, 6, totalColsCount)

  // Row 7: Empty spacing row
  worksheet.addRow([])

  // Table header row: columns/headers
  const headers = [
    docLabel, 'Date', 'Customer Code', 'Customer Name', 'Customer GSTIN',
    'Taxable Amount',
  ]
  for (const t of activeTemplates.value) {
    headers.push(`${t.title} Taxable Value`)
    if (t.gst_rate > 0) {
      headers.push(`${t.title} CGST`)
      headers.push(`${t.title} SGST`)
      headers.push(`${t.title} IGST`)
      headers.push(`${t.title} Total Tax`)
    }
  }
  headers.push(
    'CGST Amount',
    'SGST Amount',
    'IGST Amount',
    'Other Tax', 'Total Tax', 'Grand Total'
  )
  const tableHeaderRow = worksheet.addRow(headers)
  tableHeaderRow.eachCell(cell => {
    cell.font = { name: 'Arial', bold: true }
    cell.alignment = { horizontal: 'center' }
    cell.border = {
      bottom: { style: 'thin' },
      top: { style: 'thin' }
    }
  })

  // Add row items
  for (const r of rows) {
    const rowValues = [
      rType === 'order' ? r.order_no : (rType === 'quotation' ? r.quotation_no : r.invoice_no),
      r.date || '',
      r.customer || '',
      r.customer_name || '',
      r.customer_gstin || '',
      fmt(r.taxable_amount),
    ]
    for (const t of activeTemplates.value) {
      rowValues.push(fmt(r.template_values?.[t.name]?.taxable || 0))
      if (t.gst_rate > 0) {
        const cgst = r.template_values?.[t.name]?.cgst || 0
        const sgst = r.template_values?.[t.name]?.sgst || 0
        const igst = r.template_values?.[t.name]?.igst || 0
        rowValues.push(fmt(cgst))
        rowValues.push(fmt(sgst))
        rowValues.push(fmt(igst))
        rowValues.push(fmt(cgst + sgst + igst))
      }
    }
    rowValues.push(
      fmt(r.cgst_amount),
      fmt(r.sgst_amount),
      fmt(r.igst_amount),
      fmt(r.other_tax),
      fmt(r.total_tax),
      fmt(r.grand_total)
    )
    worksheet.addRow(rowValues)
  }

  // Totals Row
  const sum = key => rows.reduce((s, r) => s + (r[key] || 0), 0)
  const totals = []
  for (const t of activeTemplates.value) {
    totals.push(fmt(rows.reduce((s, r) => s + (r.template_values?.[t.name]?.taxable || 0), 0)))
    if (t.gst_rate > 0) {
      const cgstTotal = rows.reduce((s, r) => s + (r.template_values?.[t.name]?.cgst || 0), 0)
      const sgstTotal = rows.reduce((s, r) => s + (r.template_values?.[t.name]?.sgst || 0), 0)
      const igstTotal = rows.reduce((s, r) => s + (r.template_values?.[t.name]?.igst || 0), 0)
      totals.push(fmt(cgstTotal))
      totals.push(fmt(sgstTotal))
      totals.push(fmt(igstTotal))
      totals.push(fmt(cgstTotal + sgstTotal + igstTotal))
    }
  }
  const totalsRow = worksheet.addRow([
    'GRAND TOTAL', '', '', '', '',
    fmt(sum('taxable_amount')),
    ...totals,
    fmt(sum('cgst_amount')),
    fmt(sum('sgst_amount')),
    fmt(sum('igst_amount')),
    fmt(sum('other_tax')),
    fmt(sum('total_tax')),
    fmt(sum('grand_total')),
  ])
  totalsRow.eachCell((cell, colNumber) => {
    cell.font = { name: 'Arial', bold: true }
    if (colNumber >= 6 || colNumber === 1) {
      cell.border = {
        top: { style: 'thin' },
        bottom: { style: 'double' }
      }
    }
  })

  // Generate blob and download
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)

  const series = selectedSeries.value.replace(/[^A-Za-z0-9]/g, '')
  const from = fromDate.value || 'all'
  const to = toDate.value || 'all'
  link.download = `${modalConfig.value.filePrefix}_${series}_${from}_to_${to}.xlsx`
  link.click()
}

// Cashflow report is now handled in CashflowReport.vue
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
