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
        <!-- Series Filter (only for Invoice tab) -->
        <div v-if="activeTab === 'Invoice'" class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm">
          <label class="text-[12px] font-normal uppercase tracking-widest text-[var(--color-text-muted)]">Series</label>
          <select 
            v-model="seriesFilter"
            class="bg-transparent text-[14px] font-normal text-[var(--color-text)] outline-none focus:text-[var(--color-info)] min-w-[120px]"
            @change="fetchReport"
          >
            <option value="">All Series</option>
            <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
          </select>
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
    <div v-if="!showDetail" class="flex border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="activeTab = tab.value"
        class="px-6 py-3 text-[14px] font-normal transition-all relative"
        :class="activeTab === tab.value ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
      >
        {{ tab.label }}
        <div v-if="activeTab === tab.value" class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--color-info)]"></div>
      </button>
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
            <template v-for="(row, index) in sortedReportData" :key="row.name">
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
                    <span v-if="row.direction" class="ml-1 text-sm font-bold" :class="row.direction === 'CR' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">{{ row.direction }}</span>
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
        <SalesInvoice v-if="modalType === 'Invoice'" :is-subwindow="true" :invoice-name="selectedDoc" />
        <Quotation v-else-if="modalType === 'Quotation'" :is-subwindow="true" :quotation-name="selectedDoc" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import SalesInvoice from './SalesInvoice.vue'
import Quotation from './Quotation.vue'

const router = useRouter()
const showDetail = ref(false)
const selectedDoc = ref('')
const modalType = ref('')
const pageTitle = computed(() => {
  if (!showDetail.value) return 'Daily Reports'
  if (modalType.value === 'Invoice') return `Sales Invoice: ${selectedDoc.value}`
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
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${d}-${m}-${y}`
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

const tabs = [
  { label: 'Invoices', value: 'Invoice' },
  { label: 'Payments', value: 'Payment' },
  { label: 'Journals', value: 'Journal' },
  { label: 'Quotations', value: 'Quotation' },
]

const columns = computed(() => {
  if (activeTab.value === 'Invoice') {
    return [
      { label: 'Date', key: 'date', type: 'date' },
      { label: 'Invoice No', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Time', key: 'posting_time', type: 'time' },
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
    const data = await frappeGet('ssplbilling.api.daily_report_api.get_daily_reports', {
      report_type: activeTab.value,
      from_date: fromDate.value,
      to_date: toDate.value,
      naming_series: seriesFilter.value
    })
    reportData.value = (data || []).map(row => {
      let display_amount = 0
      let direction = ''
      
      if (activeTab.value === 'Invoice' || activeTab.value === 'Quotation') {
        display_amount = row.grand_total || 0
        direction = 'DR'
      } else if (activeTab.value === 'Payment') {
        display_amount = row.received_amount > 0 ? row.received_amount : row.paid_amount
        // Receive payment = CR to party, Pay = DR to party
        direction = row.payment_type === 'Receive' ? 'CR' : 'DR'
      } else if (activeTab.value === 'Journal') {
        display_amount = row.total_debit || row.total_credit || 0
        direction = 'DR' // Simplified for Journal total
      }

      return {
        ...row,
        date: row.posting_date || row.transaction_date || '',
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
  try {
    const res = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { doctype: 'Sales Invoice' })
    availableSeries.value = res.allowed_series || []
  } catch (e) {
    console.warn('Failed to fetch series for filter:', e)
  }
}

function handleRowClick(row) {
  selectedDoc.value = row.name
  modalType.value = activeTab.value
  showDetail.value = true
}

watch(activeTab, fetchReport)

onMounted(() => {
  fetchAvailableSeries()
  fetchReport()
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
