<template>
  <div class="flex min-h-screen flex-col bg-slate-900 text-slate-200">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200"
          >
            ← Dashboard
          </button>
          <span class="text-slate-600">|</span>
          <h1 class="text-sm font-bold text-slate-100 uppercase tracking-tight">GST Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-indigo-900/40 px-2 py-0.5 text-[10px] font-semibold text-indigo-400">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info -->
        <div class="flex items-center gap-4 text-[10px] text-slate-400">
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Ctrl+L</kbd> Search</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-slate-300">Esc</kbd> Back</span>
        </div>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-slate-700 bg-slate-800 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-slate-500 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-slate-300 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-slate-700 bg-slate-800 px-6 py-3 shadow-xl">
      <div class="flex flex-wrap items-end gap-4">

        <!-- Party search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            <span>Customer</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-slate-600 bg-slate-700 px-1 font-mono text-[9px] text-slate-300">Ctrl+L</kbd> Search
            </span>
          </label>
          <div
            class="flex items-center justify-between rounded border px-3 py-2 text-sm cursor-pointer transition-colors"
            :class="selectedCustomer ? 'bg-indigo-900/20 font-semibold text-indigo-400 border-indigo-700' : 'bg-slate-800 text-slate-500 border-slate-600 hover:border-indigo-500'"
            @click="showCustomerSearchModal = true"
          >
            <div class="truncate flex items-center gap-2">
              <span v-if="selectedCustomer">{{ selectedCustomer.customer_name || selectedCustomer.name }}</span>
              <span v-else>Select customer...</span>
            </div>
            <button
              v-if="selectedCustomer"
              @click.stop="clearLedger"
              class="ml-2 text-slate-500 hover:text-slate-300"
            >✕</button>
          </div>
        </div>

        <!-- Dates -->
        <div class="flex gap-2">
          <div>
            <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">From</label>
            <input v-model="fromDate" type="date" class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">To</label>
            <input v-model="toDate" type="date" class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          </div>
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedCustomer || loading"
          class="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-bold text-white transition-all hover:bg-indigo-500 active:scale-95 disabled:opacity-40"
        >
          {{ loading ? 'Loading...' : 'Fetch Ledger' }}
        </button>

        <!-- Summary -->
        <template v-if="ledgerData">
          <div class="ml-auto flex items-center gap-4">
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-slate-500">Opening</span>
              <span class="font-mono text-lg font-bold text-slate-400">₹{{ fmt(ledgerData.opening_balance) }}</span>
            </div>
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-slate-500">Total Debit</span>
              <span class="font-mono text-lg font-bold text-green-400">₹{{ fmt(ledgerData.total_debit) }}</span>
            </div>
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-slate-500">Total Credit</span>
              <span class="font-mono text-lg font-bold text-red-400">₹{{ fmt(ledgerData.total_credit) }}</span>
            </div>
            <div class="flex flex-col items-end border-l border-slate-700 pl-4">
              <span class="text-[9px] font-bold uppercase text-slate-500">Net Balance</span>
              <span class="font-mono text-xl font-black text-indigo-400">₹{{ fmt(ledgerData.closing_balance) }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <div class="flex flex-1 overflow-hidden">
      
      <!-- Ledger Table -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <div v-if="!ledgerData && !loading" class="flex flex-1 flex-col items-center justify-center gap-2 text-slate-600 opacity-50">
          <div class="text-6xl">📖</div>
          <p class="font-bold uppercase tracking-widest">Select a customer to view GST Ledger</p>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center gap-3">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
          <span class="text-sm font-medium text-slate-400">Loading ledger data...</span>
        </div>

        <div v-else-if="ledgerData" class="flex-1 overflow-y-auto">
          <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
            <thead class="sticky top-0 z-10 bg-slate-800 shadow-md">
              <tr class="border-b border-slate-700 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <th class="px-6 py-3 text-left">Date</th>
                <th class="px-6 py-3 text-left">Type</th>
                <th class="px-6 py-3 text-left">Voucher No</th>
                <th class="px-6 py-3 text-right">Debit</th>
                <th class="px-6 py-3 text-right">Credit</th>
                <th class="px-6 py-3 text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              <!-- Opening Balance Row -->
              <tr class="border-b border-slate-800 bg-slate-800/50">
                <td colspan="5" class="px-6 py-3 font-bold text-slate-500 uppercase tracking-widest text-[10px]">
                  Opening Balance <span class="ml-2 font-normal lowercase opacity-60">(before {{ ledgerData.from_date }})</span>
                </td>
                <td class="px-6 py-3 text-right font-mono font-black text-slate-400 bg-slate-800/30">
                  ₹{{ fmt(ledgerData.opening_balance) }}
                </td>
              </tr>

              <tr 
                v-for="(entry, idx) in ledgerData.entries" 
                :key="idx"
                class="border-b border-slate-800 transition-colors hover:bg-slate-800/50 cursor-pointer"
                :class="{ 'bg-indigo-900/10': selectedEntry?.voucher_no === entry.voucher_no }"
                @click="onRowClick(entry)"
              >
                <td class="px-6 py-3 font-mono text-slate-400">{{ entry.date }}</td>
                <td class="px-6 py-3">
                  <span 
                    class="rounded-full px-2 py-0.5 text-[9px] font-black uppercase tracking-tight"
                    :class="entry.voucher_type === 'Quotation' ? 'bg-amber-500/20 text-amber-400' : 'bg-indigo-500/20 text-indigo-400'"
                  >
                    {{ entry.voucher_type === 'Quotation' ? 'QUOTE' : 'DUMMY' }}
                  </span>
                </td>
                <td class="px-6 py-3 font-mono text-blue-400 font-bold underline decoration-blue-400/30 underline-offset-2">{{ entry.voucher_no }}</td>
                <td class="px-6 py-3 text-right font-mono font-bold text-green-400">
                  {{ entry.debit ? '₹' + fmt(entry.debit) : '—' }}
                </td>
                <td class="px-6 py-3 text-right font-mono font-bold text-red-400">
                  {{ entry.credit ? '₹' + fmt(entry.credit) : '—' }}
                </td>
                <td class="px-6 py-3 text-right font-mono font-black text-indigo-300 bg-slate-800/30">
                  ₹{{ fmt(entry.balance) }}
                </td>
              </tr>
              <tr v-if="!ledgerData.entries.length" class="h-32 text-center text-slate-600 italic">
                <td colspan="6">No entries found for this period.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Detail Panel -->
      <transition name="slide">
        <div v-if="selectedEntry" class="flex w-[400px] shrink-0 flex-col border-l border-slate-700 bg-slate-800 shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-700 px-4 py-3 bg-slate-900/50">
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-widest text-slate-500">{{ selectedEntry.voucher_type }}</span>
              <span class="font-mono text-sm font-bold text-blue-400">{{ selectedEntry.voucher_no }}</span>
            </div>
            <button @click="selectedEntry = null" class="rounded p-1.5 text-slate-500 hover:bg-slate-700 hover:text-white transition">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
            <!-- Summary Card -->
            <div class="mb-6 rounded-xl bg-slate-900/50 p-4 border border-slate-700">
              <div class="flex justify-between items-center mb-3">
                <span class="text-[10px] font-bold text-slate-500 uppercase">Amount</span>
                <span class="font-mono text-lg font-black" :class="selectedEntry.debit ? 'text-green-400' : 'text-red-400'">
                  ₹{{ fmt(selectedEntry.debit || selectedEntry.credit) }}
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-[10px] font-bold text-slate-500 uppercase">Posting Date</span>
                <span class="text-sm font-bold text-slate-300">{{ selectedEntry.date }}</span>
              </div>
            </div>

            <!-- Items table (if Quotation) -->
            <div v-if="selectedEntryDetail?.items?.length">
              <div class="mb-2 text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-slate-700 pb-1">Items</div>
              <div class="space-y-2">
                <div v-for="(it, i) in selectedEntryDetail.items" :key="i" class="rounded-lg bg-slate-700/30 p-2.5 border border-slate-700/50">
                  <div class="flex justify-between mb-1">
                    <span class="font-mono text-[11px] font-bold text-indigo-300">{{ it.item_code }}</span>
                    <span class="font-mono text-xs font-black text-slate-200">₹{{ fmt(it.amount) }}</span>
                  </div>
                  <div class="text-[10px] text-slate-400 truncate mb-1">{{ it.item_name }}</div>
                  <div class="flex gap-2 text-[10px] font-bold">
                    <span class="text-slate-500">{{ it.qty }} {{ it.uom }}</span>
                    <span class="text-slate-600">@</span>
                    <span class="text-slate-500">₹{{ fmt(it.rate) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="selectedEntry.voucher_type === 'Gst Dummy Ledger'" class="flex flex-1 items-center justify-center py-20 text-slate-600">
              <p class="text-center italic text-xs">No item details for dummy ledger entries</p>
            </div>
          </div>
          
          <div class="p-4 border-t border-slate-700 bg-slate-900/30">
            <button 
              @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
              class="w-full rounded-lg bg-slate-700 py-2 text-xs font-bold text-slate-300 hover:bg-slate-600 transition"
            >
              Open in ERPNext ↗
            </button>
          </div>
        </div>
      </transition>
    </div>

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchRef"
      :show="showCustomerSearchModal"
      initial-type="Customer"
      @close="showCustomerSearchModal = false"
      @select="pickCustomer"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'

const router = useRouter()
const API = 'ssplbilling.api.gst_ledger_api'

// ── STATE ────────────────────────────────────────────────────────────
const selectedCustomer = ref(null)
const fromDate = ref('')
const toDate = ref(new Date().toISOString().split('T')[0])
const loading = ref(false)
const ledgerData = ref(null)
const selectedEntry = ref(null)
const showCustomerSearchModal = ref(false)
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

// ── COMPUTED ─────────────────────────────────────────────────────────
const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`,
  paddingTop: `${(4 * zoomPercent.value) / 100}px`,
  paddingBottom: `${(4 * zoomPercent.value) / 100}px`
}))

const selectedEntryDetail = computed(() => {
  if (!selectedEntry.value || !ledgerData.value?.voucher_details) return null
  return ledgerData.value.voucher_details[selectedEntry.value.voucher_no] || null
})

// ── ACTIONS ──────────────────────────────────────────────────────────
function pickCustomer(c) {
  selectedCustomer.value = c
  showCustomerSearchModal.value = false
  loadLedger()
}

function clearLedger() {
  selectedCustomer.value = null
  ledgerData.value = null
  selectedEntry.value = null
}

async function loadLedger() {
  if (!selectedCustomer.value) return
  loading.value = true
  selectedEntry.value = null
  try {
    const res = await frappeGet(`${API}.get_gst_ledger`, {
      customer: selectedCustomer.value.name,
      from_date: fromDate.value,
      to_date: toDate.value
    })
    ledgerData.value = res
  } catch (e) {
    alert(e.message || 'Fetch failed')
  } finally {
    loading.value = false
  }
}

function onRowClick(entry) {
  selectedEntry.value = entry
}

function openInErpNext(type, name) {
  const doctype = type === 'Quotation' ? 'Quotation' : 'Gst Dummy Ledger'
  const slug = doctype.toLowerCase().replace(/ /g, '-')
  window.open(`/app/${slug}/${name}`, '_blank')
}

// ── HELPERS ───────────────────────────────────────────────────────────
function fmt(n) {
  return parseFloat(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function handleKeyDown(e) {
  if (e.ctrlKey && e.key === 'l') { e.preventDefault(); showCustomerSearchModal.value = true }
  if (e.key === 'Escape') { 
    if (showCustomerSearchModal.value) showCustomerSearchModal.value = false
    else if (selectedEntry.value) selectedEntry.value = null
    else router.push('/')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  // Default from date: 90 days ago
  const d = new Date()
  d.setDate(d.getDate() - 90)
  fromDate.value = d.toISOString().split('T')[0]
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease, opacity 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); opacity: 0; }

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
