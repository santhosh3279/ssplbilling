<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">GST Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-[var(--color-info)]/40 px-2 py-0.5 text-[10px] font-semibold text-[var(--color-info)]">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info -->
        <div class="flex items-center gap-4 text-[10px] text-[var(--color-text-muted)]">
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Ctrl+L</kbd> Search</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Back</span>
        </div>

        <div class="flex items-center gap-2">
          <!-- Print Button -->
          <button
            v-if="ledgerData"
            @click="showPrintModal = true"
            class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            title="Print Ledger"
          >
            🖨 Print
          </button>

          <!-- Excel Button -->
          <button
            v-if="ledgerData"
            @click="exportExcel"
            class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            title="Export to Excel"
          >
            ⬇ Excel
          </button>
        </div>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-xl">
      <div class="flex flex-wrap items-end gap-4">

        <!-- Party search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span>Customer</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 font-mono text-[9px] text-[var(--color-text)]">Ctrl+L</kbd> Search
            </span>
          </label>
          <div
            class="flex items-center justify-between rounded border px-3 py-2 text-sm cursor-pointer transition-colors"
            :class="selectedCustomer ? 'bg-[var(--color-info)]/20 font-semibold text-[var(--color-info)] border-[var(--color-info)]' : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)] hover:border-[var(--color-info)]'"
            @click="showCustomerSearchModal = true"
          >
            <div class="truncate flex items-center gap-2">
              <span v-if="selectedCustomer">{{ selectedCustomer.customer_name || selectedCustomer.name }}</span>
              <span v-else>Select customer...</span>
            </div>
            <button
              v-if="selectedCustomer"
              @click.stop="clearLedger"
              class="ml-2 text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            >✕</button>
          </div>
        </div>

        <!-- Dates -->
        <div class="flex gap-2">
          <div>
            <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
            <input v-model="fromDate" type="date" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" />
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
            <input v-model="toDate" type="date" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" />
          </div>
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedCustomer || loading"
          class="rounded-lg bg-[var(--color-info)] px-6 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-info)] active:scale-95 disabled:opacity-40"
        >
          {{ loading ? 'Loading...' : 'Fetch Ledger' }}
        </button>

        <!-- Summary -->
        <template v-if="ledgerData">
          <div class="ml-auto flex items-center gap-4">
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Opening</span>
              <span class="font-mono text-lg font-bold text-[var(--color-text-muted)]">₹{{ fmt(ledgerData.opening_balance) }}</span>
            </div>
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Total Debit</span>
              <span class="font-mono text-lg font-bold text-[var(--color-success)]">₹{{ fmt(ledgerData.total_debit) }}</span>
            </div>
            <div class="flex flex-col items-end">
              <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Total Credit</span>
              <span class="font-mono text-lg font-bold text-[var(--color-danger)]">₹{{ fmt(ledgerData.total_credit) }}</span>
            </div>
            <div class="flex flex-col items-end border-l border-[var(--color-border)] pl-4">
              <span class="text-[9px] font-bold uppercase text-[var(--color-text-muted)]">Net Balance</span>
              <span class="font-mono text-xl font-black text-[var(--color-info)]">₹{{ fmt(ledgerData.closing_balance) }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <div class="flex flex-1 overflow-hidden">
      
      <!-- Ledger Table -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <div v-if="!ledgerData && !loading" class="flex flex-1 flex-col items-center justify-center gap-2 text-[var(--color-text-muted)] opacity-50">
          <div class="text-6xl">📖</div>
          <p class="font-bold uppercase tracking-widest">Select a customer to view GST Ledger</p>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center gap-3">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></div>
          <span class="text-sm font-medium text-[var(--color-text-muted)]">Loading ledger data...</span>
        </div>

        <div v-else-if="ledgerData" class="flex-1 overflow-y-auto">
          <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
            <thead class="sticky top-0 z-10 bg-[var(--color-surface)] shadow-md">
              <tr class="border-b border-[var(--color-border)] text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                <th class="px-6 py-3 text-left">Date</th>
                                <th class="px-6 py-3 text-left">Voucher No</th>
                <th class="px-6 py-3 text-right">Debit</th>
                <th class="px-6 py-3 text-right">Credit</th>
                <th class="px-6 py-3 text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              <!-- Opening Balance Row -->
              <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/50">
                <td colspan="4" class="px-6 py-3 font-bold text-[var(--color-text-muted)] uppercase tracking-widest text-[10px]">
                  Opening Balance <span class="ml-2 font-normal lowercase opacity-60">(before {{ ledgerData.from_date }})</span>
                </td>
                <td class="px-6 py-3 text-right font-mono font-black text-[var(--color-text-muted)] bg-[var(--color-surface)]/30">
                  ₹{{ fmt(ledgerData.opening_balance) }}
                </td>
              </tr>

              <tr 
                v-for="(entry, idx) in ledgerData.entries" 
                :key="idx"
                class="border-b border-[var(--color-border)] transition-colors hover:bg-[var(--color-surface)]/50 cursor-pointer"
                :class="{ 'bg-[var(--color-info)]/10': selectedEntry?.voucher_no === entry.voucher_no }"
                @click="onRowClick(entry)"
              >
                <td class="px-6 py-3 font-mono text-[var(--color-text-muted)]">{{ entry.date }}</td>
                <td class="px-6 py-3 font-mono text-[var(--color-info)] font-bold underline decoration-blue-400/30 underline-offset-2">{{ entry.voucher_no }}</td>
                <td class="px-6 py-3 text-right font-mono font-bold text-[var(--color-success)]">
                  {{ entry.debit ? '₹' + fmt(entry.debit) : '—' }}
                </td>
                <td class="px-6 py-3 text-right font-mono font-bold text-[var(--color-danger)]">
                  {{ entry.credit ? '₹' + fmt(entry.credit) : '—' }}
                </td>
                <td class="px-6 py-3 text-right font-mono font-black text-[var(--color-info)] bg-[var(--color-surface)]/30">
                  ₹{{ fmt(entry.balance) }}
                </td>
              </tr>
              <tr v-if="!ledgerData.entries.length" class="h-32 text-center text-[var(--color-text-muted)] italic">
                <td colspan="5">No entries found for this period.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Detail Panel -->
      <transition name="slide">
        <div v-if="selectedEntry" class="flex w-[400px] shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
          <div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3 bg-[var(--color-bg)]/50">
            <div class="flex flex-col">
              <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">{{ selectedEntry.voucher_type }}</span>
              <span class="font-mono text-sm font-bold text-[var(--color-info)]">{{ selectedEntry.voucher_no }}</span>
            </div>
            <button @click="selectedEntry = null" class="rounded p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text-on-highlight)] transition">✕</button>
          </div>

          <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
            <!-- Summary Card -->
            <div class="mb-6 rounded-xl bg-[var(--color-bg)]/50 p-4 border border-[var(--color-border)]">
              <div class="flex justify-between items-center mb-3">
                <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase">Amount</span>
                <span class="font-mono text-lg font-black" :class="selectedEntry.debit ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  ₹{{ fmt(selectedEntry.debit || selectedEntry.credit) }}
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase">Posting Date</span>
                <span class="text-sm font-bold text-[var(--color-text)]">{{ selectedEntry.date }}</span>
              </div>
            </div>

            <!-- Items table (if Quotation) -->
            <div v-if="selectedEntryDetail?.items?.length">
              <div class="mb-2 text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] border-b border-[var(--color-border)] pb-1">Items</div>
              <div class="space-y-2">
                <div v-for="(it, i) in selectedEntryDetail.items" :key="i" class="rounded-lg bg-[var(--color-surface-raised)]/30 p-2.5 border border-[var(--color-border)]/50">
                  <div class="flex justify-between mb-1">
                    <span class="font-mono text-[11px] font-bold text-[var(--color-info)]">{{ it.item_code }}</span>
                    <span class="font-mono text-xs font-black text-[var(--color-text)]">₹{{ fmt(it.amount) }}</span>
                  </div>
                  <div class="text-[10px] text-[var(--color-text-muted)] truncate mb-1">{{ it.item_name }}</div>
                  <div class="flex gap-2 text-[10px] font-bold">
                    <span class="text-[var(--color-text-muted)]">{{ it.qty }} {{ it.uom }}</span>
                    <span class="text-[var(--color-text-muted)]">@</span>
                    <span class="text-[var(--color-text-muted)]">₹{{ fmt(it.rate) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="selectedEntry.voucher_type === 'Gst Dummy Ledger'" class="flex flex-1 items-center justify-center py-20 text-[var(--color-text-muted)]">
              <p class="text-center italic text-xs">No item details for dummy ledger entries</p>
            </div>
          </div>
          
          <div class="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg)]/30">
            <button 
              @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
              class="w-full rounded-lg bg-[var(--color-surface-raised)] py-2 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
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
    <!-- PRINT MODAL -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="printKey"
      :doctype="''"
      @close="showPrintModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import { utils, writeFile } from 'xlsx'

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
const showPrintModal = ref(false)
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 120)

// ── COMPUTED ─────────────────────────────────────────────────────────
const printKey = computed(() => {
  if (!selectedCustomer.value) return ''
  return `${selectedCustomer.value.name}||${fromDate.value}||${toDate.value}||Gst Ledger`
})

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

// ── EXPORT EXCEL ───────────────────────────────────────────────────────
function exportExcel() {
  if (!ledgerData.value || !ledgerData.value.entries.length) return

  const headers = ['Date', 'Voucher No', 'Debit', 'Credit', 'Balance']
  const data = ledgerData.value.entries.map(e => [
    e.date,
    e.voucher_no,
    e.debit || 0,
    e.credit || 0,
    e.balance || 0
  ])

  // Add opening balance at the top
  data.unshift(['', 'Opening Balance', '', '', ledgerData.value.opening_balance])

  const wb = utils.book_new()
  const ws = utils.aoa_to_sheet([headers, ...data])
  
  ws['!cols'] = [
    { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 15 }, { wch: 15 }
  ]

  utils.book_append_sheet(wb, ws, 'GST Ledger')
  
  const custName = selectedCustomer.value?.customer_name || selectedCustomer.value?.name || 'Customer'
  writeFile(wb, `GST_Ledger_${custName}_${fromDate.value}_to_${toDate.value}.xlsx`)
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
