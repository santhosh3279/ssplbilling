<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            class="rounded-lg px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition"
            @click="router.push('/')"
          >
            ← Back
          </button>
          <div>
            <h1 class="text-3xl font-normal text-[var(--color-text)] uppercase tracking-wider">Batch Report Exporter</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Consolidate multiple report registers into a single ZIP archive</p>
          </div>
        </div>
      </div>
    </header>

    <main class="flex-1 bg-[var(--color-surface)]/30 p-6 overflow-y-auto">
      <div class="max-w-4xl mx-auto space-y-6">
        <!-- Date Range Selection Card -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-2 mb-4">
            📅 Select Date Range & Period
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From Date</label>
              <input
                v-model="fromDate"
                type="date"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
            <div>
              <label class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To Date</label>
              <input
                v-model="toDate"
                type="date"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-lg text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
              />
            </div>
          </div>
          <!-- Presets -->
          <div class="flex flex-wrap gap-2 mt-4 pt-2 border-t border-[var(--color-border)]/50">
            <button
              v-for="p in presets"
              :key="p.label"
              @click="setPreset(p.days)"
              class="rounded bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition"
            >
              {{ p.label }}
            </button>
          </div>
        </div>

        <!-- Reports Selection Card -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
          <div class="flex justify-between items-center border-b border-[var(--color-border)] pb-2 mb-4">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              📋 Select Reports to Export
            </h2>
            <div class="flex gap-2">
              <button
                @click="selectAll(true)"
                class="text-xs text-[var(--color-info)] hover:underline transition"
              >
                Select All
              </button>
              <span class="text-[var(--color-border)]">|</span>
              <button
                @click="selectAll(false)"
                class="text-xs text-[var(--color-text-muted)] hover:underline transition"
              >
                Clear Selection
              </button>
            </div>
          </div>

          <div class="space-y-4">
            <div
              v-for="report in reports"
              :key="report.id"
              class="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-xl border transition-all"
              :class="report.selected ? 'bg-[var(--color-info)]/5 border-[var(--color-info)]/30' : 'bg-[var(--color-surface-raised)]/30 border-[var(--color-border)]'"
            >
              <div class="flex items-start gap-3">
                <input
                  type="checkbox"
                  v-model="report.selected"
                  :id="report.id"
                  class="mt-1 h-5 w-5 rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-info)]/30 cursor-pointer"
                />
                <label :for="report.id" class="cursor-pointer select-none">
                  <div class="text-lg font-semibold text-[var(--color-text)]">{{ report.name }}</div>
                  <div class="text-xs text-[var(--color-text-muted)]">{{ report.description }}</div>
                </label>
              </div>

              <!-- Series Dropdown -->
              <div class="mt-3 md:mt-0 flex items-center gap-2">
                <span class="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Series:</span>
                <select
                  v-model="report.series"
                  :disabled="!report.selected"
                  class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-info)] disabled:opacity-50 transition w-44"
                >
                  <option value="" disabled>— Select Series —</option>
                  <option v-for="s in getSeriesListForType(report.seriesType)" :key="s" :value="s">
                    {{ s }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Global Messages & Exporters -->
        <div v-if="error" class="rounded-xl bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30 p-4 text-sm text-[var(--color-danger)]">
          ⚠️ {{ error }}
        </div>

        <div v-if="successSummary" class="rounded-xl bg-[var(--color-success)]/10 border border-[var(--color-success)]/30 p-4 text-sm text-[var(--color-success)] space-y-1">
          <div class="font-bold">🎉 Export Completed Successfully!</div>
          <div class="text-xs text-[var(--color-text-muted)]">{{ successSummary }}</div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 items-center">
          <!-- Spinner & status -->
          <div v-if="generating" class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
            <span class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></span>
            <span>{{ progressMsg }}</span>
          </div>

          <button
            @click="generateZip"
            :disabled="generating || !hasSelection"
            class="rounded-xl px-6 py-3 text-lg font-semibold text-[var(--color-text-on-highlight)] transition active:scale-95 shadow-lg cursor-pointer disabled:opacity-50"
            :class="hasSelection ? 'bg-[var(--color-info)] hover:bg-[var(--color-info)]/90 shadow-[var(--color-info)]/15' : 'bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] shadow-none'"
          >
            ⚡ Export as ZIP
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import JSZip from 'jszip'
import ExcelJS from 'exceljs'
import { utils, write } from 'xlsx'
import {
  getSalesTaxRegister,
  getPurchaseTaxRegister,
  getQuotationTaxRegister,
  getHsnSummaryReport,
  getQuotationHsnSummaryReport,
  getItemSummaryReport,
  getPurchaseSeries,
  getQuotationSeries
} from '../api.js'
import { dashboardApi } from '../services/dashboard'

const router = useRouter()

// Date filter variables
const fromDate = ref('')
const toDate = ref('')
const generating = ref(false)
const progressMsg = ref('')
const error = ref('')
const successSummary = ref('')

// Series cache lists
const invoiceSeriesList = ref([])
const quotationSeriesList = ref([])
const purchaseSeriesList = ref([])

// Preset options
const presets = [
  { label: 'Today', days: 0 },
  { label: 'Yesterday', days: 1 },
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
]

// Available report definitions
const reports = ref([
  {
    id: 'sales_tax',
    name: 'Sales Tax Register',
    description: 'GST-wise summary of submitted Sales Invoices',
    selected: true,
    seriesType: 'invoice',
    series: '',
  },
  {
    id: 'purchase_tax',
    name: 'Purchase Tax Register',
    description: 'GST-wise summary of submitted Purchase Invoices',
    selected: true,
    seriesType: 'purchase',
    series: '',
  },
  {
    id: 'hsn_summary',
    name: 'HSN Summary',
    description: 'HSN-wise summary of submitted Sales Invoices',
    selected: false,
    seriesType: 'invoice',
    series: '',
  },
  {
    id: 'quotation_tax',
    name: 'Quotation Register',
    description: 'GST-wise summary of Quotations (Draft & Submitted)',
    selected: false,
    seriesType: 'quotation',
    series: '',
  },
  {
    id: 'quotation_hsn',
    name: 'Quotation HSN Summary',
    description: 'HSN-wise summary of Quotations (Draft & Submitted)',
    selected: false,
    seriesType: 'quotation',
    series: '',
  },
  {
    id: 'item_sales_summary',
    name: 'Item Sales Summary',
    description: 'Consolidated sales volumes by item code',
    selected: false,
    seriesType: 'invoice',
    series: '',
  },
])

// Returns correct series list depending on report's target doctype
function getSeriesListForType(type) {
  if (type === 'quotation') return quotationSeriesList.value
  if (type === 'purchase') return purchaseSeriesList.value
  return invoiceSeriesList.value
}

// Check if any report is checked
const hasSelection = computed(() => reports.value.some(r => r.selected))

// Setup date values on load
function defaultDates() {
  const today = new Date()
  const y = today.getFullYear()
  const m = String(today.getMonth() + 1).padStart(2, '0')
  const d = String(today.getDate()).padStart(2, '0')
  const todayStr = `${y}-${m}-${d}`
  return { from: todayStr, to: todayStr }
}

function setPreset(days) {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - days)
  
  const formatDateStr = (date) => {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }
  
  fromDate.value = formatDateStr(start)
  toDate.value = formatDateStr(end)
}

// Helper to select/deselect all
function selectAll(val) {
  reports.value.forEach(r => {
    r.selected = val
  })
}

onMounted(async () => {
  const d = defaultDates()
  fromDate.value = d.from
  toDate.value = d.to

  // Load allowed Invoice naming series
  try {
    const res = await dashboardApi.getAllowedSeries()
    invoiceSeriesList.value = res.allowed_series || []
  } catch (e) {
    invoiceSeriesList.value = []
  }

  // Load Quotation series options
  try {
    quotationSeriesList.value = await getQuotationSeries() || []
  } catch (e) {
    quotationSeriesList.value = []
  }

  // Load Purchase series options
  try {
    purchaseSeriesList.value = await getPurchaseSeries() || []
  } catch (e) {
    purchaseSeriesList.value = []
  }

  // Set initial default series in dropdown selectors
  reports.value.forEach(r => {
    const list = getSeriesListForType(r.seriesType)
    if (list.length) r.series = list[0]
  })
})

// Number formatter
function fmt(n) {
  return Number(Number(n || 0).toFixed(2))
}

// ── Zip Generator Main Flow ──
async function generateZip() {
  error.value = ''
  successSummary.value = ''

  // Validate date selectors
  if (!fromDate.value || !toDate.value) {
    error.value = 'Please select both From and To dates.'
    return
  }

  const selectedReports = reports.value.filter(r => r.selected)
  
  // Validate series selections
  for (const r of selectedReports) {
    if (!r.series) {
      error.value = `Please select a Naming Series for "${r.name}".`
      return
    }
  }

  generating.value = true
  progressMsg.value = 'Starting generation...'
  
  const zip = new JSZip()
  const generatedFiles = []
  const skippedFiles = []

  try {
    for (const r of selectedReports) {
      progressMsg.value = `Fetching data for: ${r.name}...`
      
      const cleanSeries = r.series.replace(/[^A-Za-z0-9]/g, '')
      const filePrefix = r.id.toUpperCase()
      const filename = `${filePrefix}_${cleanSeries}_${fromDate.value}_to_${toDate.value}.xlsx`

      let fileBuffer = null

      if (r.id === 'sales_tax') {
        const res = await getSalesTaxRegister(r.series, fromDate.value, toDate.value)
        if (res.rows && res.rows.length) {
          fileBuffer = await buildRegisterExcelBuffer('sales_tax', res.rows, res.company_name, res.company_address_lines, res.active_templates)
        }
      } else if (r.id === 'purchase_tax') {
        const res = await getPurchaseTaxRegister(r.series, fromDate.value, toDate.value)
        if (res.rows && res.rows.length) {
          fileBuffer = await buildRegisterExcelBuffer('purchase_tax', res.rows, res.company_name, res.company_address_lines, res.active_templates)
        }
      } else if (r.id === 'hsn_summary') {
        const res = await getHsnSummaryReport(r.series, fromDate.value, toDate.value)
        if (res.rows && res.rows.length) {
          fileBuffer = await buildHSNExcelBuffer('hsn_summary', res.rows, res.company_name, res.company_address_lines)
        }
      } else if (r.id === 'quotation_tax') {
        const res = await getQuotationTaxRegister(r.series, fromDate.value, toDate.value)
        if (res.rows && res.rows.length) {
          fileBuffer = await buildRegisterExcelBuffer('quotation', res.rows, res.company_name, res.company_address_lines, res.active_templates)
        }
      } else if (r.id === 'quotation_hsn') {
        const res = await getQuotationHsnSummaryReport(r.series, fromDate.value, toDate.value)
        if (res.rows && res.rows.length) {
          fileBuffer = await buildHSNExcelBuffer('quotation_hsn', res.rows, res.company_name, res.company_address_lines)
        }
      } else if (r.id === 'item_sales_summary') {
        const rows = await getItemSummaryReport(r.series, fromDate.value, toDate.value)
        if (rows && rows.length) {
          fileBuffer = buildItemSummaryExcelBuffer(rows)
        }
      }

      if (fileBuffer) {
        progressMsg.value = `Packaging: ${filename}...`
        zip.file(filename, fileBuffer)
        generatedFiles.push(r.name)
      } else {
        skippedFiles.push(`${r.name} (No data)`)
      }
    }

    if (generatedFiles.length === 0) {
      error.value = 'No data found for any of the selected reports in this date range.'
      generating.value = false
      return
    }

    progressMsg.value = 'Creating ZIP file...'
    const zipBlob = await zip.generateAsync({ type: 'blob' })
    
    // Download ZIP link trigger
    const link = document.createElement('a')
    link.href = URL.createObjectURL(zipBlob)
    link.download = `BatchReports_${fromDate.value}_to_${toDate.value}.zip`
    link.click()

    successSummary.value = `Exported: ${generatedFiles.join(', ')}.`
    if (skippedFiles.length) {
      successSummary.value += ` Skipped: ${skippedFiles.join(', ')}.`
    }
  } catch (e) {
    console.error('[BatchReports] Failed to generate zip file:', e)
    error.value = e.message || 'Failed to generate report ZIP archive.'
  } finally {
    generating.value = false
  }
}

// ── Generic excel builder helpers generating ArrayBuffers for JSZip package ──

async function buildRegisterExcelBuffer(type, rows, companyName, companyAddressLines, activeTemplates) {
  const workbook = new ExcelJS.Workbook()
  const sheetName = type === 'purchase_tax' ? 'Purchase Tax Register' : (type === 'quotation' ? 'Quotation Tax Register' : 'Sales Tax Register')
  const worksheet = workbook.addWorksheet(sheetName)

  const templateCols = []
  for (const t of activeTemplates) {
    templateCols.push({ key: `temp_taxable_${t.name}`, width: 18 })
    if (t.gst_rate > 0) {
      templateCols.push({ key: `temp_cgst_${t.name}`, width: 14 })
      templateCols.push({ key: `temp_sgst_${t.name}`, width: 14 })
      templateCols.push({ key: `temp_igst_${t.name}`, width: 14 })
      templateCols.push({ key: `temp_total_tax_${t.name}`, width: 16 })
    }
  }

  worksheet.columns = [
    { key: 'doc_no', width: 28 },
    { key: 'date', width: 14 },
    { key: 'cust_code', width: 18 },
    { key: 'cust_name', width: 28 },
    { key: 'cust_gstin', width: 18 },
    { key: 'taxable', width: 16 },
    ...templateCols,
    { key: 'cgst_amt', width: 14 },
    { key: 'sgst_amt', width: 14 },
    { key: 'igst_amt', width: 14 },
    { key: 'other_tax', width: 14 },
    { key: 'total_tax', width: 14 },
    { key: 'grand_total', width: 18 }
  ]

  const totalColsCount = 12 + templateCols.length

  const row1 = worksheet.addRow([companyName || ''])
  row1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  row1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(1, 1, 1, totalColsCount)

  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines[i] || ''
    const rowNum = i + 2
    const row = worksheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    worksheet.mergeCells(rowNum, 1, rowNum, totalColsCount)
  }

  const fromStr = fromDate.value || 'All'
  const toStr = toDate.value || 'All'
  const dateRow = worksheet.addRow([`Period: ${fromStr} to ${toStr}`])
  dateRow.getCell(1).font = { name: 'Arial', size: 11, bold: true, italic: true }
  dateRow.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(6, 1, 6, totalColsCount)

  worksheet.addRow([])

  const docLabel = type === 'quotation' ? 'Quotation No' : 'Invoice No'
  const headers = [
    docLabel, 'Date',
    type === 'purchase_tax' ? 'Supplier Code' : 'Customer Code',
    type === 'purchase_tax' ? 'Supplier Name' : 'Customer Name',
    type === 'purchase_tax' ? 'Supplier GSTIN' : 'Customer GSTIN',
    'Taxable Amount',
  ]
  for (const t of activeTemplates) {
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

  for (const r of rows) {
    const rowValues = [
      type === 'quotation' ? r.quotation_no : r.invoice_no,
      r.date || '',
      type === 'purchase_tax' ? (r.supplier || '') : (r.customer || ''),
      type === 'purchase_tax' ? (r.supplier_name || '') : (r.customer_name || ''),
      type === 'purchase_tax' ? (r.supplier_gstin || '') : (r.customer_gstin || ''),
      fmt(r.taxable_amount),
    ]
    for (const t of activeTemplates) {
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

  const totals = []
  for (const t of activeTemplates) {
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
    fmt(rows.reduce((s, r) => s + (r.taxable_amount || 0), 0)),
    ...totals,
    fmt(rows.reduce((s, r) => s + (r.cgst_amount || 0), 0)),
    fmt(rows.reduce((s, r) => s + (r.sgst_amount || 0), 0)),
    fmt(rows.reduce((s, r) => s + (r.igst_amount || 0), 0)),
    fmt(rows.reduce((s, r) => s + (r.other_tax || 0), 0)),
    fmt(rows.reduce((s, r) => s + (r.total_tax || 0), 0)),
    fmt(rows.reduce((s, r) => s + (r.grand_total || 0), 0)),
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

  return await workbook.xlsx.writeBuffer()
}

async function buildHSNExcelBuffer(type, rows, companyName, companyAddressLines) {
  const workbook = new ExcelJS.Workbook()
  const sheetName = type === 'quotation_hsn' ? 'Quotation HSN Summary' : 'HSN Summary'
  const worksheet = workbook.addWorksheet(sheetName)

  worksheet.columns = [
    { key: 'date', width: 14 },
    { key: 'bill_no', width: 22 },
    { key: 'qty', width: 14 },
    { key: 'taxable', width: 16 },
    { key: 'sgst', width: 16 },
    { key: 'cgst', width: 16 },
    { key: 'igst', width: 16 },
    { key: 'total_tax', width: 16 },
    { key: 'total_value', width: 18 }
  ]

  const row1 = worksheet.addRow([companyName || ''])
  row1.getCell(1).font = { name: 'Arial', size: 14, bold: true }
  row1.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
  worksheet.mergeCells(1, 1, 1, 9)

  for (let i = 0; i < 4; i++) {
    const addrLine = companyAddressLines[i] || ''
    const rowNum = i + 2
    const row = worksheet.addRow([addrLine])
    row.getCell(1).font = { name: 'Arial', size: 10 }
    row.getCell(1).alignment = { horizontal: 'center', vertical: 'middle' }
    worksheet.mergeCells(rowNum, 1, rowNum, 9)
  }

  worksheet.addRow([])

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
    const hsnHeaderRow = worksheet.addRow([`HSN Code: ${hsn}`])
    hsnHeaderRow.getCell(1).font = { name: 'Arial', size: 11, bold: true }
    worksheet.mergeCells(hsnHeaderRow.number, 1, hsnHeaderRow.number, 9)

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

    worksheet.addRow([])
  }

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
      if (colNumber >= 3) {
        cell.border = {
          top: { style: 'thin' },
          bottom: { style: 'double' }
        }
      }
    })
  }

  return await workbook.xlsx.writeBuffer()
}

function buildItemSummaryExcelBuffer(rows) {
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
  return write(wb, { bookType: 'xlsx', type: 'array' })
}
</script>

<style scoped>
</style>
