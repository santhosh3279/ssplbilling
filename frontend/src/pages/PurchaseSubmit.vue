<template>
  <div class="flex h-screen flex-col bg-slate-50 text-slate-900 font-sans">
    
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button 
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-slate-900">PURCHASE SUBMISSION</h1>
        <div class="h-4 w-px bg-slate-200 mx-2"></div>
        <span class="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-600 border border-amber-100">
          {{ invoices.length }} Pending Purchases
        </span>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Current Date</div>
          <div class="text-sm font-medium text-slate-600">{{ todayStr }}</div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      
      <!-- LEFT PANEL: INVOICE LIST -->
      <aside class="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div class="p-4 space-y-3">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
            <input 
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text" 
              placeholder="Search PINV or supplier..." 
              class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-xs text-slate-700 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
          <div class="flex gap-1 items-center">
            <button 
              @click="adjustDate(-1)"
              class="rounded-lg bg-slate-100 p-1.5 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-all border border-slate-200"
              title="Previous Day"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input 
              v-model="filterDate"
              @change="loadInvoices"
              type="date" 
              class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 outline-none focus:border-blue-500 transition-all"
            />
            <button 
              @click="adjustDate(1)"
              class="rounded-lg bg-slate-100 p-1.5 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-all border border-slate-200"
              title="Next Day"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
            <button 
              @click="loadInvoices"
              class="rounded-lg bg-slate-100 p-1.5 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-all border border-slate-200"
              title="Refresh List"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-slate-50/50">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-50">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-amber-500 border-t-transparent mb-2"></div>
            <span class="text-xs text-slate-500">Loading purchases...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-20 opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4 text-slate-400"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-sm font-medium text-slate-500">No draft purchases found</span>
          </div>
          <div v-else class="px-3 pb-4">
            <button 
              v-for="inv in invoices" 
              :key="inv.name"
              :data-inv-name="inv.name"
              @click="selectInvoice(inv)"
              class="mb-2 flex w-full flex-col gap-1.5 rounded-xl p-4 text-left transition-all outline-none group border shadow-sm"
              :class="selectedInvoice?.name === inv.name 
                ? 'bg-amber-600 border-amber-500 ring-2 ring-amber-100' 
                : 'bg-white hover:bg-slate-50 border-slate-200'"
            >
              <div class="flex items-start justify-between">
                <span class="font-mono text-[11px] font-bold" :class="selectedInvoice?.name === inv.name ? 'text-amber-100' : 'text-amber-600'">
                  {{ inv.name }}
                </span>
                <span class="text-xs font-bold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-emerald-600'">
                  ₹{{ fmt(inv.grand_total) }}
                </span>
              </div>
              <div class="truncate text-sm font-semibold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-slate-900'">
                {{ inv.supplier_name }}
              </div>
              <div class="flex items-center justify-between mt-1">
                <span class="text-[10px] font-bold tracking-wider" :class="selectedInvoice?.name === inv.name ? 'text-amber-200' : 'text-slate-400'">
                  DRAFT
                </span>
                <span class="text-[10px] font-medium" :class="selectedInvoice?.name === inv.name ? 'text-amber-200' : 'text-slate-400'">
                  {{ formatDate(inv.posting_date) }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- MIDDLE PANEL: PREVIEW -->
      <main class="flex flex-1 flex-col bg-slate-100/30 overflow-hidden">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-6 text-slate-400"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <p class="text-lg font-medium text-slate-500">Select a purchase to preview</p>
        </div>

        <template v-else>
          <!-- PREVIEW HEADER -->
          <div class="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-4 shadow-sm z-10">
            <div>
              <h2 class="text-xl font-bold text-slate-900 leading-none mb-1">{{ selectedInvoice.name }}</h2>
              <p class="text-sm font-medium text-slate-500">{{ selectedInvoice.supplier_name }}</p>
            </div>
            <div class="flex gap-3">
              <!-- BARCODE PRINT BUTTON -->
              <button 
                class="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-all border border-slate-200 shadow-sm active:scale-95"
                @click="barcodePrintPlaceholder"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500"><path d="M3 5v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2z"/><path d="M7 7h10"/><path d="M7 12h10"/><path d="M7 17h10"/></svg>
                <span>Print Barcodes</span>
              </button>
              <!-- BILL PRINT BUTTON -->
              <button 
                class="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-all border border-slate-200 shadow-sm active:scale-95"
                @click="billPrintPlaceholder"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                <span>Print Bill</span>
              </button>
            </div>
          </div>

          <!-- PREVIEW CONTENT -->
          <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div class="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-md border border-slate-200">
              <div class="flex justify-between mb-8 border-b border-slate-100 pb-8">
                <div>
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Supplier</div>
                  <div class="text-lg font-bold text-slate-900 leading-none mb-1">{{ selectedInvoice.supplier_name }}</div>
                  <div class="text-sm font-medium text-slate-500 font-mono">{{ selectedInvoice.supplier }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Purchase Details</div>
                  <div class="text-sm text-slate-600 mb-1">Date: <span class="font-bold text-slate-900">{{ formatDate(selectedInvoice.posting_date) }}</span></div>
                  <div class="flex justify-end">
                    <span class="rounded px-2 py-0.5 text-[10px] uppercase font-bold border bg-slate-100 text-slate-600 border-slate-200">
                      DRAFT
                    </span>
                  </div>
                </div>
              </div>

              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    <th class="py-3 px-2">Item</th>
                    <th class="py-3 px-2 text-right">Qty</th>
                    <th class="py-3 px-2 text-right">Rate</th>
                    <th class="py-3 px-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody class="text-sm">
                  <tr v-for="item in previewItems" :key="item.item_code" class="border-b border-slate-50">
                    <td class="py-4 px-2">
                      <div class="font-bold text-slate-800">{{ item.item_name }}</div>
                      <div class="text-[11px] text-slate-400 font-mono">{{ item.item_code }}</div>
                    </td>
                    <td class="py-4 px-2 text-right text-slate-600 font-medium">{{ item.qty }} {{ item.uom }}</td>
                    <td class="py-4 px-2 text-right text-slate-600 font-mono">₹{{ fmt(item.rate) }}</td>
                    <td class="py-4 px-2 text-right font-bold text-slate-900 font-mono">₹{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>

              <div class="mt-8 flex justify-end">
                <div class="w-64 space-y-3">
                  <div class="flex justify-between border-t border-slate-200 pt-3 text-lg font-bold text-slate-900">
                    <span>Grand Total</span>
                    <span class="font-mono text-amber-600">₹{{ fmt(selectedInvoice.grand_total) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT PANEL: SUBMISSION -->
      <aside class="flex w-96 shrink-0 flex-col border-l border-slate-200 bg-white shadow-xl">
        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-full text-slate-400 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-3 mx-auto"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            <p class="text-xs font-medium uppercase tracking-wider">Select purchase to submit</p>
          </div>

          <template v-else>
            <!-- SUMMARY CARD -->
            <div class="rounded-2xl bg-amber-50/50 border-2 border-amber-100 p-6 relative overflow-hidden text-center">
              <div class="absolute top-0 left-0 w-full h-1 bg-amber-500"></div>
              <div class="text-[10px] font-bold uppercase tracking-widest text-amber-600 mb-2">Total Payable to Supplier</div>
              <div class="text-4xl font-black tracking-tight text-slate-900 font-mono">
                ₹{{ fmt(selectedInvoice.grand_total) }}
              </div>
              <div class="mt-4 inline-flex items-center gap-1.5 rounded-full bg-slate-900 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white">
                Credit Purchase
              </div>
            </div>

            <div class="space-y-4">
              <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Submission Note</div>
                <p class="text-xs text-slate-600 leading-relaxed">
                  Submitting this invoice will update your stock and post the liability to the supplier's ledger as a credit entry.
                </p>
              </div>

              <!-- SUBMIT ACTION -->
              <div class="pt-4">
                <div v-if="errorMsg" class="mb-4 rounded-xl bg-rose-50 p-3 text-xs font-bold text-rose-600 border border-rose-100">
                  {{ errorMsg }}
                </div>
                <div v-if="successMsg" class="mb-4 rounded-xl bg-emerald-50 p-3 text-xs font-bold text-emerald-600 border border-emerald-100">
                  {{ successMsg }}
                </div>

                <button 
                  @click="confirmSubmission"
                  :disabled="isSubmitting"
                  class="flex w-full items-center justify-center gap-2 rounded-2xl py-5 text-sm font-bold uppercase tracking-widest transition-all active:scale-95 disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none shadow-lg text-white bg-amber-600 hover:bg-amber-700 shadow-amber-100 group"
                >
                  <span v-if="isSubmitting" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                  <span v-else>Confirm & Submit Purchase</span>
                  <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="ml-1 group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </button>
              </div>
            </div>
          </template>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { fetchPurchaseInvoices, getPurchaseInvoiceDetails, submitPurchaseInvoice } from '../api.js'
import { useShortcuts } from '../services/shortcutManager'

// --- STATE ---
const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const isSubmitting = ref(false)
const loadingList = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const searchQuery = ref('')
const filterDate = ref(new Date().toISOString().slice(0, 10))

// --- SHORTCUTS ---
useShortcuts({
  'ARROWUP':   () => navigateBills(-1),
  'ARROWDOWN': () => navigateBills(1),
  'ENTER':     () => { if (selectedInvoice.value && !isSubmitting.value) confirmSubmission() },
  'ESCAPE':    () => window.history.back(),
  'F5':        () => loadInvoices(),
  'F9':        () => { if (selectedInvoice.value && !isSubmitting.value) confirmSubmission() }
})

function navigateBills(dir) {
  if (!invoices.value.length) return
  if (!selectedInvoice.value) {
    selectInvoice(invoices.value[0])
    return
  }
  const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
  const nextIdx = idx + dir
  if (nextIdx >= 0 && nextIdx < invoices.value.length) {
    selectInvoice(invoices.value[nextIdx])
    nextTick(() => {
      const el = document.querySelector(`[data-inv-name="${invoices.value[nextIdx].name}"]`)
      el?.scrollIntoView({ block: 'nearest' })
    })
  }
}

// --- COMPUTED ---
const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
  })
})

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2, maximumFractionDigits: 2
  })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

async function loadInvoices() {
  loadingList.value = true
  try {
    // Backend filters for docstatus=0
    const all = await fetchPurchaseInvoices(searchQuery.value, 50, filterDate.value)
    invoices.value = all.filter(i => i.docstatus === 0)
  } catch (e) {
    errorMsg.value = "Failed to load invoices: " + e.message
  } finally {
    loadingList.value = false
  }
}

function adjustDate(days) {
  const d = new Date(filterDate.value)
  d.setDate(d.getDate() + days)
  filterDate.value = d.toISOString().slice(0, 10)
  loadInvoices()
}

let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadInvoices, 300)
}

async function selectInvoice(inv) {
  if (selectedInvoice.value?.name === inv.name) return
  
  selectedInvoice.value = inv
  previewItems.value = []
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const details = await getPurchaseInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
  } catch (e) {
    errorMsg.value = "Failed to load details: " + e.message
  }
}

function barcodePrintPlaceholder() {
  alert("Barcode print feature is ready. Waiting for barcode format selection.")
}

function billPrintPlaceholder() {
  alert("Bill print feature is ready. Waiting for print format selection.")
}

async function confirmSubmission() {
  if (!selectedInvoice.value || isSubmitting.value) return

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    await submitPurchaseInvoice(selectedInvoice.value.name)
    
    successMsg.value = `Purchase Invoice ${selectedInvoice.value.name} submitted successfully!`
    
    const nameToRemove = selectedInvoice.value.name
    setTimeout(() => {
      invoices.value = invoices.value.filter(i => i.name !== nameToRemove)
      selectedInvoice.value = null
      previewItems.value = []
      successMsg.value = ''
    }, 2000)
    
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  loadInvoices()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
