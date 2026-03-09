<template>
  <div class="flex h-screen flex-col" style="background:#0f172a; color:#f1f5f9; font-family:'Inter', sans-serif;">
    
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-900 px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button 
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-white">CASHIER DESK</h1>
        <div class="h-4 w-px bg-slate-700 mx-2"></div>
        <span class="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400 border border-blue-500/20">
          {{ invoices.length }} Pending Invoices
        </span>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Current Date</div>
          <div class="text-sm font-medium text-slate-300">{{ todayStr }}</div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      
      <!-- LEFT PANEL: INVOICE LIST -->
      <aside class="flex w-80 shrink-0 flex-col border-r border-slate-800 bg-slate-900/50">
        <div class="p-4 space-y-3">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
            <input 
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text" 
              placeholder="Search invoice or customer..." 
              class="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-4 text-xs text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
          <div class="flex gap-2">
            <input 
              v-model="filterDate"
              @change="loadInvoices"
              type="date" 
              class="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-500 transition-all"
            />
            <button 
              @click="loadInvoices"
              class="rounded-lg bg-slate-800 px-3 text-slate-400 hover:bg-slate-700 hover:text-white transition-all"
              title="Refresh List"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-50">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent mb-2"></div>
            <span class="text-xs">Loading bills...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-20 opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-sm font-medium">No invoices found</span>
          </div>
          <div v-else class="px-3 pb-4">
            <button 
              v-for="inv in invoices" 
              :key="inv.name"
              @click="selectInvoice(inv)"
              class="mb-2 flex w-full flex-col gap-1.5 rounded-xl p-4 text-left transition-all outline-none group"
              :class="selectedInvoice?.name === inv.name 
                ? 'bg-blue-600 shadow-lg shadow-blue-900/20 ring-1 ring-blue-400' 
                : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent hover:border-slate-700'"
            >
              <div class="flex items-start justify-between">
                <span class="font-mono text-[11px] font-bold" :class="selectedInvoice?.name === inv.name ? 'text-blue-100' : 'text-blue-400'">
                  {{ inv.name }}
                </span>
                <span class="text-xs font-bold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-green-400'">
                  ₹{{ fmt(inv.grand_total) }}
                </span>
              </div>
              <div class="truncate text-sm font-semibold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-slate-200'">
                {{ inv.customer_name }}
              </div>
              <div class="flex items-center justify-between mt-1">
                <span class="text-[10px]" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-500'">
                  {{ inv.docstatus === 0 ? 'Draft' : 'Unpaid' }}
                </span>
                <span class="text-[10px]" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-500'">
                  {{ formatDate(inv.posting_date) }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- MIDDLE PANEL: PREVIEW -->
      <main class="flex flex-1 flex-col bg-slate-950">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center opacity-20">
          <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-6"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <p class="text-lg font-medium">Select an invoice to preview</p>
        </div>

        <template v-else>
          <!-- PREVIEW HEADER -->
          <div class="flex items-center justify-between border-b border-slate-800 bg-slate-900/30 px-8 py-4">
            <div>
              <h2 class="text-xl font-bold text-white">{{ selectedInvoice.name }}</h2>
              <p class="text-sm text-slate-400">{{ selectedInvoice.customer_name }}</p>
            </div>
            <div class="flex gap-3">
              <!-- PRINT BUTTON PLACEHOLDER -->
              <button 
                class="flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-700 transition-all border border-slate-700"
                @click="printPlaceholder"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                <span>Print Bill</span>
              </button>
            </div>
          </div>

          <!-- PREVIEW CONTENT -->
          <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div class="mx-auto max-w-3xl rounded-2xl bg-slate-900 p-8 shadow-2xl border border-slate-800">
              <div class="flex justify-between mb-8 border-b border-slate-800 pb-8">
                <div>
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Billing To</div>
                  <div class="text-lg font-bold text-white">{{ selectedInvoice.customer_name }}</div>
                  <div class="text-sm text-slate-400">{{ selectedInvoice.customer }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Invoice Details</div>
                  <div class="text-sm text-slate-300">Date: <span class="font-semibold">{{ formatDate(selectedInvoice.posting_date) }}</span></div>
                  <div class="text-sm text-slate-300">Status: <span class="rounded bg-slate-800 px-2 py-0.5 text-[10px] uppercase font-bold text-blue-400">{{ selectedInvoice.docstatus === 0 ? 'Draft' : 'Unpaid' }}</span></div>
                </div>
              </div>

              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th class="py-3 px-2">Item</th>
                    <th class="py-3 px-2 text-right">Qty</th>
                    <th class="py-3 px-2 text-right">Rate</th>
                    <th class="py-3 px-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody class="text-sm">
                  <tr v-for="item in previewItems" :key="item.item_code" class="border-b border-slate-800/50">
                    <td class="py-4 px-2">
                      <div class="font-semibold text-slate-200">{{ item.item_name }}</div>
                      <div class="text-xs text-slate-500 font-mono">{{ item.item_code }}</div>
                    </td>
                    <td class="py-4 px-2 text-right text-slate-300">{{ item.qty }} {{ item.uom }}</td>
                    <td class="py-4 px-2 text-right text-slate-300 font-mono">₹{{ fmt(item.rate) }}</td>
                    <td class="py-4 px-2 text-right font-bold text-white font-mono">₹{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>

              <div class="mt-8 flex justify-end">
                <div class="w-64 space-y-3">
                  <div class="flex justify-between text-sm text-slate-400">
                    <span>Subtotal</span>
                    <span class="font-mono">₹{{ fmt(previewSubtotal) }}</span>
                  </div>
                  <div v-if="selectedInvoice.discount_percentage" class="flex justify-between text-sm text-orange-400">
                    <span>Discount ({{ selectedInvoice.discount_percentage }}%)</span>
                    <span class="font-mono">-₹{{ fmt(previewDiscount) }}</span>
                  </div>
                  <div class="flex justify-between border-t border-slate-700 pt-3 text-lg font-bold text-white">
                    <span>Grand Total</span>
                    <span class="font-mono text-green-400">₹{{ fmt(selectedInvoice.grand_total) }}</span>
                  </div>
                  <div v-if="selectedInvoice.outstanding_amount && selectedInvoice.docstatus === 1" class="flex justify-between text-sm text-blue-400">
                    <span>Outstanding</span>
                    <span class="font-mono">₹{{ fmt(selectedInvoice.outstanding_amount) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT PANEL: PAYMENT -->
      <aside class="flex w-96 shrink-0 flex-col border-l border-slate-800 bg-slate-900 shadow-2xl">
        <div class="p-6 border-b border-slate-800 bg-slate-900/50">
          <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400">Payment Entry</h2>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-full text-slate-600">
            <p class="text-sm">Select an invoice to proceed with payment</p>
          </div>

          <template v-else>
            <!-- AMOUNT TO COLLECT -->
            <div class="rounded-2xl bg-slate-950 p-6 text-center ring-1 ring-slate-800">
              <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Amount to Collect</div>
              <div class="text-4xl font-black tracking-tight text-white font-mono">
                ₹{{ fmt(amountToCollect) }}
              </div>
              <div v-if="isCredit" class="mt-3 inline-flex items-center gap-1.5 rounded-full bg-purple-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-purple-400 ring-1 ring-purple-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m5 15 7 7 7-7"/></svg>
                Post to Credit Ledger
              </div>
            </div>

            <!-- PAYMENT METHODS -->
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Method</span>
                <button 
                  @click="toggleCredit"
                  class="rounded-lg px-3 py-1 text-[10px] font-bold uppercase tracking-widest transition-all ring-1"
                  :class="isCredit ? 'bg-purple-600 text-white ring-purple-400' : 'bg-slate-800 text-slate-400 ring-slate-700 hover:text-slate-200'"
                >
                  Credit
                </button>
              </div>

              <div class="grid gap-4" :class="{ 'opacity-30 pointer-events-none': isCredit }">
                <!-- CASH -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Cash</label>
                    <span v-if="seriesAccounts.cash" class="text-[9px] text-slate-500 truncate max-w-[150px]">{{ seriesAccounts.cash }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-green-500">₹</span>
                    <input 
                      v-model.number="payments.cash"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-700 bg-slate-950 py-3 pl-8 pr-4 text-right font-mono text-lg text-white outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-all group-hover:border-slate-600"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <!-- UPI -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">UPI / QR</label>
                    <span v-if="seriesAccounts.upi" class="text-[9px] text-slate-500 truncate max-w-[150px]">{{ seriesAccounts.upi }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-blue-500">₹</span>
                    <input 
                      v-model.number="payments.upi"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-700 bg-slate-950 py-3 pl-8 pr-4 text-right font-mono text-lg text-white outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all group-hover:border-slate-600"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <!-- BANK -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Bank Transfer</label>
                    <span v-if="seriesAccounts.bank" class="text-[9px] text-slate-500 truncate max-w-[150px]">{{ seriesAccounts.bank }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-sky-500">₹</span>
                    <input 
                      v-model.number="payments.bank"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-700 bg-slate-950 py-3 pl-8 pr-4 text-right font-mono text-lg text-white outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all group-hover:border-slate-600"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <!-- DISCOUNT -->
                <div class="space-y-1.5">
                  <label class="px-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">Discount / Write-off</label>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-orange-500">₹</span>
                    <input 
                      v-model.number="payments.discount"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-700 bg-slate-950 py-3 pl-8 pr-4 text-right font-mono text-lg text-white outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all group-hover:border-slate-600"
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- SUMMARY -->
            <div class="rounded-2xl bg-slate-800/50 p-5 space-y-3 ring-1 ring-slate-800">
              <div v-if="!isCredit" class="flex justify-between text-xs font-medium">
                <span class="text-slate-400">Total Paid</span>
                <span class="text-white font-mono">₹{{ fmt(totalPaid) }}</span>
              </div>
              <div class="flex items-center justify-between border-t border-slate-700 pt-3">
                <span class="text-sm font-bold text-slate-300">{{ isCredit ? 'Credit Amount' : 'Balance' }}</span>
                <span 
                  class="text-2xl font-black font-mono"
                  :class="isCredit ? 'text-purple-400' : (balance <= 0.01 ? 'text-green-400' : 'text-red-400')"
                >
                  ₹{{ fmt(isCredit ? amountToCollect : Math.max(0, balance)) }}
                </span>
              </div>
              <div v-if="changeAmount > 0.01 && !isCredit" class="flex items-center justify-between border-t border-slate-700 pt-2 text-blue-400">
                <span class="text-xs font-bold uppercase tracking-wider">Change to return</span>
                <span class="text-xl font-bold font-mono">₹{{ fmt(changeAmount) }}</span>
              </div>
            </div>
          </template>
        </div>

        <!-- SUBMIT ACTION -->
        <div class="p-6 border-t border-slate-800 bg-slate-900 shadow-[0_-10px_20px_rgba(0,0,0,0.2)]">
          <div v-if="errorMsg" class="mb-4 rounded-xl bg-red-500/10 p-3 text-xs text-red-400 border border-red-500/20">
            {{ errorMsg }}
          </div>
          <div v-if="successMsg" class="mb-4 rounded-xl bg-green-500/10 p-3 text-xs text-green-400 border border-green-500/20">
            {{ successMsg }}
          </div>

          <button 
            @click="processPayment"
            :disabled="!canSubmit"
            class="flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-sm font-bold uppercase tracking-widest transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none shadow-lg"
            :class="isCredit ? 'bg-purple-600 hover:bg-purple-500 shadow-purple-900/20' : 'bg-green-600 hover:bg-green-500 shadow-green-900/20'"
          >
            <span v-if="isSubmitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            <span v-else>{{ isCredit ? 'Confirm Credit Posting' : 'Complete Payment' }}</span>
          </button>
          <div class="mt-4 text-center">
            <span class="text-[10px] font-bold uppercase tracking-widest text-slate-600">Press <kbd class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-slate-400">F9</kbd> to submit</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- PRINT DIALOG (CAN BE ADDED LATER) -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchBillingSettings } from '../api.js'

// --- STATE ---
const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const isCredit = ref(false)
const isSubmitting = ref(false)
const loadingList = ref(false)
const loadingPreview = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const searchQuery = ref('')
const filterDate = ref(new Date().toISOString().slice(0, 10))

const payments = ref({
  cash: 0,
  upi: 0,
  bank: 0,
  discount: 0
})

const seriesAccounts = ref({
  cash: '',
  upi: '',
  bank: ''
})

// --- COMPUTED ---
const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
})

const amountToCollect = computed(() => {
  if (!selectedInvoice.value) return 0
  // If already submitted, use outstanding amount, otherwise grand total
  return selectedInvoice.value.docstatus === 1 
    ? Number(selectedInvoice.value.outstanding_amount || 0) 
    : Number(selectedInvoice.value.grand_total || 0)
})

const totalPaid = computed(() => {
  return Number(payments.value.cash || 0) + 
         Number(payments.value.upi || 0) + 
         Number(payments.value.bank || 0) + 
         Number(payments.value.discount || 0)
})

const balance = computed(() => {
  return amountToCollect.value - totalPaid.value
})

const changeAmount = computed(() => {
  return Math.max(0, totalPaid.value - amountToCollect.value)
})

const canSubmit = computed(() => {
  if (!selectedInvoice.value || isSubmitting.value) return false
  if (isCredit.value) return true
  // Allow small floating point difference
  return balance.value <= 0.01
})

const previewSubtotal = computed(() => {
  return previewItems.value.reduce((acc, item) => acc + (item.qty * item.rate), 0)
})

const previewDiscount = computed(() => {
  if (!selectedInvoice.value?.discount_percentage) return 0
  return previewSubtotal.value * (selectedInvoice.value.discount_percentage / 100)
})

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

async function loadInvoices() {
  loadingList.value = true
  try {
    // Re-using fetchDraftInvoices but our updated backend returns Draft + Unpaid Submitted
    invoices.value = await fetchDraftInvoices(searchQuery.value, 50, filterDate.value)
  } catch (e) {
    errorMsg.value = "Failed to load invoices: " + e.message
  } finally {
    loadingList.value = false
  }
}

let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadInvoices, 300)
}

async function selectInvoice(inv) {
  if (selectedInvoice.value?.name === inv.name) return
  
  loadingPreview.value = true
  selectedInvoice.value = inv
  previewItems.value = []
  errorMsg.value = ''
  successMsg.value = ''
  isCredit.value = false
  
  // Reset payments
  payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
  
  try {
    const details = await getInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    
    // Auto-fill cash with full amount
    payments.value.cash = details.docstatus === 1 
      ? Number(details.outstanding_amount || 0) 
      : Number(details.grand_total || 0)
      
    // Load accounts for this series
    await loadSeriesSettings(details.naming_series)
    
  } catch (e) {
    errorMsg.value = "Failed to load details: " + e.message
  } finally {
    loadingPreview.value = false
  }
}

async function loadSeriesSettings(series) {
  try {
    const settings = await fetchBillingSettings()
    const config = (settings.billing_series || []).find(s => s.series === series)
    if (config) {
      seriesAccounts.value = {
        cash: config.cash_account || 'Cash',
        upi: config.upi || 'UPI',
        bank: config.bank || 'Bank Transfer'
      }
    } else {
      seriesAccounts.value = { cash: 'Cash', upi: 'UPI', bank: 'Bank Transfer' }
    }
  } catch (e) {
    console.warn("Could not load series settings", e)
  }
}

function toggleCredit() {
  isCredit.value = !isCredit.value
  if (isCredit.value) {
    payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
  } else {
    payments.value.cash = amountToCollect.value
  }
}

function printPlaceholder() {
  alert("Print feature is ready. Waiting for print format selection.")
}

async function processPayment() {
  if (!canSubmit.value) return
  
  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: payments.value.cash,
      upi_amount: payments.value.upi,
      bank_amount: payments.value.bank,
      discount_amount: payments.value.discount,
      is_credit: isCredit.value
    }
    
    await submitInvoiceWithPayment(payload)
    
    successMsg.value = `Invoice ${selectedInvoice.value.name} processed successfully!`
    
    // Refresh list and clear selection
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

// Keyboard shortcut F9
function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    processPayment()
  }
}

onMounted(() => {
  loadInvoices()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
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
  background: #334155;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569;
}

/* Remove arrows from number input */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
