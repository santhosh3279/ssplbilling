<template>
  <div class="flex min-h-screen flex-col bg-slate-900">

    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-slate-400 hover:bg-slate-700 hover:text-white"
            @click="router.push('/')"
          >
            ← Back
          </button>
          <div>
            <h1 class="text-lg font-bold text-white">Reports</h1>
            <p class="text-xs text-slate-400">Business reports and analytics</p>
          </div>
        </div>

        <!-- Report buttons -->
        <div class="flex items-center gap-2">
          <button
            class="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 active:scale-95 transition-all"
            @click="openModal('invoice')"
          >
            📊 Sales Tax Register
          </button>
          <button
            class="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 active:scale-95 transition-all"
            @click="openModal('order')"
          >
            📋 Sales Order Tax Register
          </button>
        </div>
      </div>
    </header>

    <!-- Body placeholder -->
    <div class="flex flex-1 items-center justify-center">
      <div class="text-center text-slate-500">
        <div class="mb-3 text-5xl">📊</div>
        <p class="text-sm">Select a report from the top bar to get started.</p>
      </div>
    </div>

    <!-- ====== SHARED MODAL ====== -->
    <transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="showModal = false"
      >
        <div class="w-full max-w-md rounded-2xl bg-slate-800 shadow-2xl border border-slate-600">

          <!-- Modal header -->
          <div class="flex items-center justify-between border-b border-slate-700 px-6 py-4">
            <div>
              <h2 class="text-base font-bold text-white">{{ modalConfig.title }}</h2>
              <p class="text-xs text-slate-400 mt-0.5">{{ modalConfig.subtitle }}</p>
            </div>
            <button
              class="rounded-lg p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white"
              @click="showModal = false"
            >
              ✕
            </button>
          </div>

          <!-- Modal body -->
          <div class="px-6 py-5 space-y-4">
            <!-- Series selector -->
            <div>
              <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400">
                {{ modalConfig.seriesLabel }}
              </label>
              <select
                v-model="selectedSeries"
                class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
              >
                <option value="" disabled>— Select a series —</option>
                <option v-for="s in currentSeriesList" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>

            <!-- Date range -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400">From Date</label>
                <input
                  v-model="fromDate"
                  type="date"
                  class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
                />
              </div>
              <div>
                <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400">To Date</label>
                <input
                  v-model="toDate"
                  type="date"
                  class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-violet-500 focus:outline-none"
                />
              </div>
            </div>

            <!-- Error -->
            <p v-if="modalError" class="text-xs text-red-400">{{ modalError }}</p>
          </div>

          <!-- Modal footer -->
          <div class="flex justify-end gap-2 border-t border-slate-700 px-6 py-4">
            <button
              class="rounded-lg px-4 py-2 text-sm text-slate-400 hover:bg-slate-700 hover:text-white"
              @click="showModal = false"
            >
              Cancel
            </button>
            <button
              class="flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all"
              :class="modalConfig.btnClass"
              :disabled="generating || !selectedSeries"
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
import { getSalesTaxRegister, getSalesOrderTaxRegister, getSalesOrderSeries } from '../api.js'
import { dashboardApi } from '../services/dashboard'

const router = useRouter()

// ── Series data ───────────────────────────────────────────────────────────────
const invoiceSeriesList = ref([])
const orderSeriesList = ref([])

onMounted(async () => {
  // Invoice series (from billing settings)
  try {
    const d = await dashboardApi.getAllowedSeries()
    invoiceSeriesList.value = d.allowed_series || []
  } catch {
    invoiceSeriesList.value = []
  }

  // Sales Order series (from doctype meta)
  try {
    orderSeriesList.value = await getSalesOrderSeries() || []
  } catch {
    orderSeriesList.value = []
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

// ── Modal state ───────────────────────────────────────────────────────────────
const showModal = ref(false)
const reportType = ref('invoice') // 'invoice' | 'order'
const selectedSeries = ref('')
const fromDate = ref('')
const toDate = ref('')
const generating = ref(false)
const modalError = ref('')

const modalConfig = computed(() => {
  if (reportType.value === 'order') {
    return {
      title: 'Sales Order Tax Register',
      subtitle: 'GST-wise summary of submitted sales orders',
      seriesLabel: 'Order Series',
      btnClass: 'bg-sky-600 hover:bg-sky-700',
      sheetName: 'SO Tax Register',
      filePrefix: 'SOTaxRegister',
      noDataMsg: 'No submitted sales orders found for the selected criteria.',
      docLabel: 'Order No',
    }
  }
  return {
    title: 'Sales Tax Register',
    subtitle: 'GST-wise summary of submitted sales invoices',
    seriesLabel: 'Invoice Series',
    btnClass: 'bg-violet-600 hover:bg-violet-700',
    sheetName: 'Sales Tax Register',
    filePrefix: 'SalesTaxRegister',
    noDataMsg: 'No submitted invoices found for the selected criteria.',
    docLabel: 'Invoice No',
  }
})

const currentSeriesList = computed(() =>
  reportType.value === 'order' ? orderSeriesList.value : invoiceSeriesList.value
)

function openModal(type) {
  reportType.value = type
  modalError.value = ''
  const list = type === 'order' ? orderSeriesList.value : invoiceSeriesList.value
  selectedSeries.value = list.length ? list[0] : ''
  const d = defaultDates()
  fromDate.value = d.from
  toDate.value = d.to
  showModal.value = true
}

// ── Report generation ─────────────────────────────────────────────────────────
async function generateReport() {
  modalError.value = ''
  if (!selectedSeries.value) {
    modalError.value = 'Please select a series.'
    return
  }
  generating.value = true
  try {
    const rows = reportType.value === 'order'
      ? await getSalesOrderTaxRegister(selectedSeries.value, fromDate.value, toDate.value)
      : await getSalesTaxRegister(selectedSeries.value, fromDate.value, toDate.value)

    if (!rows || rows.length === 0) {
      modalError.value = modalConfig.value.noDataMsg
      return
    }

    buildExcel(rows)
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

function buildExcel(rows) {
  const docLabel = modalConfig.value.docLabel
  const isOrder = reportType.value === 'order'

  const headers = [
    docLabel, 'Date', 'Customer Code', 'Customer Name',
    'Taxable Amount',
    'CGST Rate %', 'CGST Amount',
    'SGST Rate %', 'SGST Amount',
    'IGST Rate %', 'IGST Amount',
    'Other Tax', 'Total Tax', 'Grand Total',
  ]

  const data = rows.map(r => [
    isOrder ? r.order_no : r.invoice_no,
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
