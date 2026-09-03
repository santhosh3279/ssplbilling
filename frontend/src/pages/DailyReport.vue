<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] overflow-hidden text-[14px] font-normal">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="showDetail ? backToReport() : $router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-[14px] font-normal tracking-tight text-[var(--color-text)] uppercase tracking-widest">{{ pageTitle }}</h1>
      </div>

      <div v-if="!showDetail" class="flex items-center gap-4">
        <!-- Presets -->
        <div class="flex items-center gap-1.5 bg-[var(--color-surface-raised)] px-2 py-1 rounded-xl border border-[var(--color-border)] shadow-sm">
          <button 
            v-for="p in presets" 
            :key="p.label" 
            @click="setPreset(p.value)"
            class="px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-lg transition-all hover:bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-info)] active:scale-95"
          >
            {{ p.label }}
          </button>
        </div>

        <!-- Series Filter (only for Invoice tabs) -->
        <div v-if="activeTab === 'Sales Invoice' || activeTab === 'Purchase Invoice'" class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm">
          <label class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)]">Series</label>
          
          <!-- Series Multi-select -->
          <div ref="seriesDropdownRef" class="relative series-dropdown-container">
            <button
              @click="showSeriesDropdown = !showSeriesDropdown"
              class="bg-transparent text-[14px] font-normal text-[var(--color-text)] outline-none focus:text-[var(--color-info)] min-w-[120px] text-left flex justify-between items-center gap-2 cursor-pointer select-none"
            >
              <span class="truncate">
                {{ selectedSeriesList.length === availableSeries.length ? 'All Series' : (selectedSeriesList.length > 0 ? selectedSeriesList[0] + (selectedSeriesList.length > 1 ? '...' : '') : 'None') }}
              </span>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" :class="{'rotate-180': showSeriesDropdown}" class="transition-transform"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            
            <!-- Dropdown Menu -->
            <div v-if="showSeriesDropdown" class="absolute top-full left-0 mt-1 min-w-[160px] max-w-[240px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-2xl z-50 py-2 max-h-64 overflow-y-auto custom-scrollbar">
              <div class="px-3 py-1.5 border-b border-[var(--color-border)] mb-1 flex items-center gap-2 cursor-pointer select-none hover:bg-[var(--color-surface-raised)]" @click="toggleAllSeries">
                <input 
                  type="checkbox" 
                  :checked="selectedSeriesList.length === availableSeries.length" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-normal uppercase tracking-wider">All Series</span>
              </div>
              <div v-for="s in availableSeries" :key="s" class="px-3 py-1.5 flex items-center gap-2 cursor-pointer select-none hover:bg-[var(--color-surface-raised)]" @click="toggleSeries(s)">
                <input 
                  type="checkbox" 
                  :checked="isSeriesSelected(s)" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-normal uppercase tracking-wider">{{ s }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm">
          <label class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)]">From</label>
          <div class="flex items-center gap-1">
            <button @click="adjustDate('from', -1)" class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              type="date"
              v-model="fromDate"
              class="bg-transparent text-[14px] font-normal text-[var(--color-text)] outline-none focus:text-[var(--color-info)] w-36"
              @change="fetchReport"
            />
            <button @click="adjustDate('from', 1)" class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>

          <label class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] ml-2">To</label>
          <div class="flex items-center gap-1">
            <button @click="adjustDate('to', -1)" class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              type="date"
              v-model="toDate"
              class="bg-transparent text-[14px] font-normal text-[var(--color-text)] outline-none focus:text-[var(--color-info)] w-36"
              @change="fetchReport"
            />
            <button @click="adjustDate('to', 1)" class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- TABS -->
    <div v-if="!showDetail" class="flex border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="activeTab = tab.value"
        class="px-[36px] py-[18px] text-[21px] font-normal transition-all relative shrink-0"
        :class="activeTab === tab.value ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
      >
        {{ tab.label }}
        <div v-if="activeTab === tab.value" class="absolute bottom-0 left-0 right-0 h-[3px] bg-[var(--color-info)]"></div>
      </button>
    </div>

    <!-- SUMMARY ROW -->
    <div v-if="!showDetail && reportData.length" class="mx-6 mt-4 flex items-center gap-8 bg-[var(--color-surface-raised)]/50 px-6 py-3 rounded-xl border border-[var(--color-border)] shadow-sm">
      <div class="flex flex-col">
        <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">No. of Entries</span>
        <span class="text-[28px] font-normal text-[var(--color-text)] leading-none font-mono">{{ summary.count }}</span>
      </div>
      <template v-if="summary.hasTax">
        <div class="h-10 w-px bg-[var(--color-border)]"></div>
        <div class="flex flex-col">
          <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">Sum of Net</span>
          <span class="text-[28px] font-normal text-[var(--color-text)] leading-none font-mono">₹ {{ summary.net.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
        </div>
        <div class="h-10 w-px bg-[var(--color-border)]"></div>
        <div class="flex flex-col">
          <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">Sum of Tax</span>
          <span class="text-[28px] font-normal text-[var(--color-warning)] leading-none font-mono">₹ {{ summary.tax.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
        </div>
        <div class="h-10 w-px bg-[var(--color-border)]"></div>
        <div class="flex flex-col">
          <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">Avg Tax</span>
          <span class="text-[28px] font-normal text-[var(--color-warning)] leading-none font-mono">{{ summary.avgTax.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}%</span>
        </div>
      </template>
      <div class="h-10 w-px bg-[var(--color-border)]"></div>
      <div class="flex flex-col">
        <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">Sum of Total</span>
        <span class="text-[28px] font-normal text-[var(--color-info)] leading-none font-mono">₹ {{ summary.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
      </div>
      <template v-if="summary.hasQty">
        <div class="h-10 w-px bg-[var(--color-border)]"></div>
        <div class="flex flex-col">
          <span class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)] leading-none mb-1.5">Total Quantity</span>
          <span class="text-[28px] font-normal text-[var(--color-success)] leading-none font-mono">{{ summary.qty.toLocaleString('en-IN') }}</span>
        </div>
      </template>
    </div>

    <!-- CONTENT -->
    <div class="flex-1 overflow-auto p-6 custom-scrollbar">
      <div v-if="loading" class="flex h-full items-center justify-center">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-info)] border-t-transparent"></div>
      </div>
      
      <div v-else-if="!showDetail && !reportData.length" class="flex h-full items-center justify-center text-[var(--color-text-muted)] italic">
        No data found for the selected date range.
      </div>

      <!-- Report Table -->
      <div v-else-if="!showDetail" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm">
        <table class="w-full border-collapse custom-table">
          <thead>
            <tr class="bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] text-left border-b border-[var(--color-border)]">
              <th v-for="col in columns" :key="col.key" class="px-2 py-1.5 font-normal text-[21px]">{{ col.label }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700">
            <template v-for="(row, index) in sortedReportData" :key="row.name + (row.item || '')">
              <!-- Date Grouping Row -->
              <tr v-if="index === 0 || row.date !== sortedReportData[index - 1].date" class="bg-[var(--color-surface-raised)]/30">
                <td :colspan="columns.length" class="px-2 py-1 text-[18px] font-medium uppercase tracking-wider text-[var(--color-info)]">
                  {{ formatDate(row.date) }}
                </td>
              </tr>
              <tr 
                class="hover:bg-[var(--color-surface-raised)] transition-colors cursor-pointer"
                @click="handleRowClick(row)"
              >
                <td v-for="col in columns" :key="col.key" class="px-2 py-1.5 font-normal text-[var(--color-text)] text-[21px]">
                  <template v-if="col.type === 'currency'">
                    ₹ {{ (row[col.key] || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                    <span v-if="row.direction && col.key === 'display_amount'" class="ml-1 text-sm font-bold" :class="row.direction === 'CR' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">{{ row.direction }}</span>
                  </template>
                  <template v-else-if="col.type === 'date'">
                    {{ formatDate(row[col.key]) }}
                  </template>
                  <template v-else-if="col.type === 'time'">
                    {{ formatTime(row[col.key]) }}
                  </template>
                  <template v-else-if="col.key === 'docstatus'">
                    <span 
                      class="px-2 py-0.5 rounded text-[18px]"
                      :class="row[col.key] === 1 ? 'bg-[var(--color-success)]/30 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/30 text-[var(--color-warning)]'"
                    >
                      {{ row[col.key] === 1 ? 'Submitted' : 'Draft' }}
                    </span>
                  </template>
                  <template v-else>
                    {{ row[col.key] }}
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Inline Detail View -->
      <div v-else class="h-full">
        <SalesInvoice v-if="modalType === 'Sales Invoice'" :is-subwindow="true" :invoice-name="selectedDoc" @close="backToReport" />
        <Quotation v-else-if="modalType === 'Quotation'" :is-subwindow="true" :quotation-name="selectedDoc" @close="backToReport" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import SalesInvoice from './SalesInvoice.vue'
import Quotation from './Quotation.vue'

import { formatDMY } from '../utils/date'
const router = useRouter()
const showDetail = ref(false)
const selectedDoc = ref('')
const modalType = ref('')
const pageTitle = computed(() => {
  if (!showDetail.value) return 'Daily Reports'
  if (modalType.value === 'Sales Invoice') return `Sales Invoice: ${selectedDoc.value}`
  if (modalType.value === 'Quotation') return `Quotation: ${selectedDoc.value}`
  return 'Daily Reports'
})

function backToReport() {
  showDetail.value = false
  selectedDoc.value = ''
  modalType.value = ''
}

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options)
  return formatter.format(date)
}

function formatDate(dateStr) {
  return formatDMY(dateStr, '')
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const parts = timeStr.split(':')
  if (parts.length >= 2) {
    return `${parts[0]}:${parts[1]}`
  }
  return timeStr
}

const fromDate = ref(getTodayIST())
const toDate = ref(getTodayIST())
const seriesFilter = ref('')
const availableSeries = ref([])
const showSeriesDropdown = ref(false)
const seriesDropdownRef = ref(null)
const selectedSeriesList = ref([])
const activeTab = ref('Invoice')
const reportData = ref([])
const loading = ref(false)

const sortedReportData = computed(() => {
  return [...reportData.value].sort((a, b) => {
    // Primary: Date descending
    const dateCompare = (b.date || '').localeCompare(a.date || '')
    if (dateCompare !== 0) return dateCompare
    // Secondary: Name descending
    return (b.name || '').localeCompare(a.name || '')
  })
})

const summary = computed(() => {
  const count = reportData.value.length
  let amount = 0
  let net = 0
  let tax = 0
  let qty = 0
  let hasQty = false
  // Only the invoice tabs carry a net and a tax; a payment or a journal has neither, and showing
  // them as zero there would read as "no tax on these" rather than "not a thing here".
  let hasTax = false

  reportData.value.forEach(row => {
    amount += (row.display_amount || 0)
    if (row.qty !== undefined) {
      qty += (row.qty || 0)
      hasQty = true
    }
    if (row.total_taxes_and_charges !== undefined) {
      net += (row.net_total || 0)
      tax += (row.total_taxes_and_charges || 0)
      hasTax = true
    }
  })

  const avgTax = net ? (tax / net) * 100 : 0

  return { count, amount, net, tax, avgTax, qty, hasQty, hasTax }
})

const presets = [
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'Curr Month', value: 'curr_month' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'FY', value: 'fy' },
]

async function setPreset(type) {
  const now = new Date()
  let from = new Date()
  let to = new Date()

  if (type === 'yesterday') {
    from.setDate(now.getDate() - 1)
    to.setDate(now.getDate() - 1)
  } else if (type === 'curr_month') {
    from = new Date(now.getFullYear(), now.getMonth(), 1)
    to = now
  } else if (type === 'last_month') {
    from = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    to = new Date(now.getFullYear(), now.getMonth(), 0)
  } else if (type === 'fy') {
    loading.value = true
    try {
      const fy = await frappeGet('ssplbilling.api.daily_report_api.get_current_fiscal_year_dates')
      if (fy) {
        fromDate.value = fy.from
        toDate.value = fy.to
        fetchReport()
        return
      }
    } catch (e) {
      console.error('Failed to fetch fiscal year dates:', e)
    } finally {
      loading.value = false
    }
    // Static fallback if API fails
    let startYear = now.getFullYear()
    if (now.getMonth() < 3) startYear -= 1
    from = new Date(startYear, 3, 1)
    to = new Date(startYear + 1, 2, 31)
  }

  fromDate.value = from.toISOString().slice(0, 10)
  toDate.value = to.toISOString().slice(0, 10)
  fetchReport()
}

const tabs = [
  { label: 'Sales Invoices', value: 'Sales Invoice' },
  { label: 'Purchase Invoices', value: 'Purchase Invoice' },
  { label: 'Payments', value: 'Payment' },
  { label: 'Journals', value: 'Journal' },
  { label: 'Quotations', value: 'Quotation' },
  { label: 'Loading', value: 'Loading' },
]

const columns = computed(() => {
  if (activeTab.value === 'Sales Invoice') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Invoice No', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Time', key: 'posting_time', type: 'time' },
      { label: 'Tax', key: 'total_taxes_and_charges', type: 'currency' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Purchase Invoice') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Invoice No', key: 'name' },
      { label: 'Supplier', key: 'supplier_name' },
      { label: 'Time', key: 'posting_time', type: 'time' },
      { label: 'Tax', key: 'total_taxes_and_charges', type: 'currency' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Payment') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Payment ID', key: 'name' },
      { label: 'Party', key: 'party_name' },
      { label: 'MOP', key: 'mode_of_payment' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Journal') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Journal ID', key: 'name' },
      { label: 'Type', key: 'voucher_type' },
      { label: 'Remark', key: 'user_remark' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Quotation') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Quotation ID', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Status', key: 'status' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
      { label: 'DocStatus', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Loading') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Receipt', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Item', key: 'item_name' },
      { label: 'Qty', key: 'qty' },
      { label: 'Rate', key: 'rate', type: 'currency' },
      { label: 'Amount', key: 'display_amount', type: 'currency' },
    ]
  }
  return []
})

function adjustDate(type, days) {
  const target = type === 'from' ? fromDate : toDate
  const d = new Date(target.value)
  d.setDate(d.getDate() + days)
  target.value = d.toISOString().slice(0, 10)
  fetchReport()
}

async function fetchReport() {
  loading.value = true
  try {
    let namingSeriesParam = seriesFilter.value
    if (activeTab.value === 'Sales Invoice' || activeTab.value === 'Purchase Invoice') {
      if (selectedSeriesList.value.length === availableSeries.value.length) {
        namingSeriesParam = ''
      } else if (selectedSeriesList.value.length === 0) {
        namingSeriesParam = ['']
      } else {
        namingSeriesParam = selectedSeriesList.value
      }
    }
    const data = await frappeGet('ssplbilling.api.daily_report_api.get_daily_reports', {
      report_type: activeTab.value,
      from_date: fromDate.value,
      to_date: toDate.value,
      naming_series: namingSeriesParam,
      company: localStorage.getItem('wb-company') || ''
    })
    reportData.value = (data || []).map(row => {
      let display_amount = 0
      let direction = ''
      
      if (activeTab.value === 'Sales Invoice' || activeTab.value === 'Purchase Invoice' || activeTab.value === 'Quotation') {
        display_amount = row.grand_total || 0
        direction = 'DR'
      } else if (activeTab.value === 'Payment') {
        display_amount = row.received_amount > 0 ? row.received_amount : row.paid_amount
        // Receive payment = CR to party, Pay = DR to party
        direction = row.payment_type === 'Receive' ? 'CR' : 'DR'
      } else if (activeTab.value === 'Journal') {
        display_amount = row.total_debit || row.total_credit || 0
        direction = 'DR' // Simplified for Journal total
      } else if (activeTab.value === 'Loading') {
        display_amount = row.amount || 0
        direction = ''
      }

      return {
        ...row,
        date: row.posting_date || row.transaction_date || row.date || '',
        display_amount,
        direction
      }
    })
  } catch (e) {
    console.error('Failed to fetch daily report:', e)
    reportData.value = []
  } finally {
    loading.value = false
  }
}

async function fetchAvailableSeries() {
  seriesFilter.value = ''
  selectedSeriesList.value = []
  if (activeTab.value !== 'Sales Invoice' && activeTab.value !== 'Purchase Invoice') {
    availableSeries.value = []
    return
  }
  try {
    const res = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { doctype: activeTab.value })
    availableSeries.value = res.allowed_series || []
    if (activeTab.value === 'Sales Invoice' || activeTab.value === 'Purchase Invoice') {
      selectedSeriesList.value = [...availableSeries.value]
    }
  } catch (e) {
    console.warn('Failed to fetch series for filter:', e)
  }
}

function toggleAllSeries() {
  if (selectedSeriesList.value.length === availableSeries.value.length) {
    selectedSeriesList.value = []
  } else {
    selectedSeriesList.value = [...availableSeries.value]
  }
  fetchReport()
}

function toggleSeries(s) {
  const current = [...selectedSeriesList.value]
  const idx = current.indexOf(s)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(s)
  }
  selectedSeriesList.value = current
  fetchReport()
}

function isSeriesSelected(s) {
  return selectedSeriesList.value.includes(s)
}

function handleRowClick(row) {
  if (activeTab.value === 'Loading' || activeTab.value === 'Purchase Invoice') {
    // For now, no detail view for Loading and Purchase Invoice
    return
  }
  selectedDoc.value = row.name
  modalType.value = activeTab.value
  showDetail.value = true
}

watch(activeTab, () => {
  fetchAvailableSeries()
  fetchReport()
})

onMounted(() => {
  fetchAvailableSeries()
  fetchReport()

  const handleClickOutside = (e) => {
    if (seriesDropdownRef.value && !seriesDropdownRef.value.contains(e.target)) {
      showSeriesDropdown.value = false
    }
  }
  window.addEventListener('click', handleClickOutside)

  onUnmounted(() => {
    window.removeEventListener('click', handleClickOutside)
  })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #64748b; }

.custom-table td, .custom-table th { font-size: 21px !important; }

/* Ensure no bold text globally in this component */
* { font-weight: 400 !important; }
</style>
