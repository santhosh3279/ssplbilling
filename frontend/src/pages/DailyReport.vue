<template>
  <div class="flex h-screen flex-col bg-slate-900 font-sans text-slate-200 overflow-hidden text-[14px] font-normal">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-700 bg-slate-800 px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-slate-100 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-[14px] font-normal tracking-tight text-slate-100">Daily Reports</h1>
      </div>

      <div class="flex items-center gap-4">
        <!-- Series Filter (only for Invoice tab) -->
        <div v-if="activeTab === 'Invoice'" class="flex items-center gap-3 bg-slate-700 px-4 py-1.5 rounded-xl border border-slate-600 shadow-sm">
          <label class="text-[12px] font-normal uppercase tracking-widest text-slate-400">Series</label>
          <select 
            v-model="seriesFilter"
            class="bg-transparent text-[14px] font-normal text-slate-200 outline-none focus:text-blue-400 min-w-[120px]"
            @change="fetchReport"
          >
            <option value="">All Series</option>
            <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="flex items-center gap-3 bg-slate-700 px-4 py-1.5 rounded-xl border border-slate-600 shadow-sm">
          <label class="text-[12px] font-normal uppercase tracking-widest text-slate-400">From</label>
          <div class="flex items-center gap-1">
            <button @click="adjustDate('from', -1)" class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              type="date"
              v-model="fromDate"
              class="bg-transparent text-[14px] font-normal text-slate-200 outline-none focus:text-blue-400 w-36"
              @change="fetchReport"
            />
            <button @click="adjustDate('from', 1)" class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>

          <label class="text-[12px] font-normal uppercase tracking-widest text-slate-400 ml-2">To</label>
          <div class="flex items-center gap-1">
            <button @click="adjustDate('to', -1)" class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              type="date"
              v-model="toDate"
              class="bg-transparent text-[14px] font-normal text-slate-200 outline-none focus:text-blue-400 w-36"
              @change="fetchReport"
            />
            <button @click="adjustDate('to', 1)" class="p-1 hover:bg-slate-600 rounded-md text-slate-400 hover:text-blue-400 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- TABS -->
    <div class="flex border-b border-slate-700 bg-slate-800 px-6">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="activeTab = tab.value"
        class="px-6 py-3 text-[14px] font-normal transition-all relative"
        :class="activeTab === tab.value ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'"
      >
        {{ tab.label }}
        <div v-if="activeTab === tab.value" class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"></div>
      </button>
    </div>

    <!-- CONTENT -->
    <div class="flex-1 overflow-auto p-6 custom-scrollbar">
      <div v-if="loading" class="flex h-full items-center justify-center">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
      </div>
      
      <div v-else-if="!reportData.length" class="flex h-full items-center justify-center text-slate-500 italic">
        No data found for the selected date range.
      </div>

      <div v-else class="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden shadow-sm">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-slate-700 text-slate-400 text-left border-b border-slate-600">
              <th v-for="col in columns" :key="col.key" class="px-4 py-3 font-normal">{{ col.label }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700">
            <tr 
              v-for="row in reportData" 
              :key="row.name" 
              class="hover:bg-slate-750 transition-colors cursor-pointer"
              @click="handleRowClick(row)"
            >
              <td v-for="col in columns" :key="col.key" class="px-4 py-3 font-normal text-slate-300">
                <template v-if="col.type === 'currency'">
                  ₹ {{ (row[col.key] || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </template>
                <template v-else-if="col.key === 'docstatus'">
                  <span 
                    class="px-2 py-0.5 rounded text-[12px]"
                    :class="row[col.key] === 1 ? 'bg-green-900/30 text-green-400' : 'bg-amber-900/30 text-amber-400'"
                  >
                    {{ row[col.key] === 1 ? 'Submitted' : 'Draft' }}
                  </span>
                </template>
                <template v-else>
                  {{ row[col.key] }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'

const router = useRouter()

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options)
  return formatter.format(date)
}

const fromDate = ref(getTodayIST())
const toDate = ref(getTodayIST())
const seriesFilter = ref('')
const availableSeries = ref([])
const activeTab = ref('Invoice')
const reportData = ref([])
const loading = ref(false)

const tabs = [
  { label: 'Invoices', value: 'Invoice' },
  { label: 'Payments', value: 'Payment' },
  { label: 'Journals', value: 'Journal' },
  { label: 'Quotations', value: 'Quotation' },
]

const columns = computed(() => {
  if (activeTab.value === 'Invoice') {
    return [
      { label: 'Invoice No', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Time', key: 'posting_time' },
      { label: 'Amount', key: 'grand_total', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Payment') {
    return [
      { label: 'Payment ID', key: 'name' },
      { label: 'Party', key: 'party_name' },
      { label: 'MOP', key: 'mode_of_payment' },
      { label: 'Amount', key: 'received_amount', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Journal') {
    return [
      { label: 'Journal ID', key: 'name' },
      { label: 'Type', key: 'voucher_type' },
      { label: 'Remark', key: 'user_remark' },
      { label: 'Amount', key: 'total_debit', type: 'currency' },
      { label: 'Status', key: 'docstatus' },
    ]
  } else if (activeTab.value === 'Quotation') {
    return [
      { label: 'Quotation ID', key: 'name' },
      { label: 'Customer', key: 'customer_name' },
      { label: 'Status', key: 'status' },
      { label: 'Amount', key: 'grand_total', type: 'currency' },
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
    reportData.value = data || []
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
  if (activeTab.value === 'Invoice') {
    router.push({ name: 'SalesInvoice', query: { invoice: row.name } })
  } else if (activeTab.value === 'Quotation') {
    router.push({ name: 'QuotationEntry', query: { quotation: row.name } })
  }
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

.bg-slate-750 { background-color: rgba(30, 41, 59, 0.5); }

/* Ensure no bold text globally in this component */
* { font-weight: 400 !important; }
</style>
