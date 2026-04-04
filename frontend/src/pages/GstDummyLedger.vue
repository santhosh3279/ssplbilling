<template>
  <div class="h-screen flex flex-col bg-slate-900 text-slate-200">
    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-4 py-2.5 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700 transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-slate-600">|</span>
        <span class="text-sm font-bold text-slate-100 uppercase tracking-tight">GST Dummy Ledger</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-slate-400">
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Tab</kbd> Next field</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">End</kbd> Save</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- ── LEFT SIDEBAR (Recent Entries) ────────────────────────── -->
      <aside class="flex w-72 shrink-0 flex-col border-r border-slate-700 bg-slate-800 overflow-hidden">
        <div class="p-3 border-b border-slate-700 flex flex-col gap-2">
          <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Recent Entries</div>
          <input 
            v-model="sidebarFilter"
            type="text"
            placeholder="Search customer..."
            class="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs outline-none focus:border-blue-500"
          />
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loading" class="p-4 text-center text-xs text-slate-500">Loading...</div>
          <div v-else-if="!entries.length" class="p-4 text-center text-xs text-slate-600 italic">No entries found</div>
          <div 
            v-for="e in filteredEntries" 
            :key="e.name"
            class="border-b border-slate-700 p-3 hover:bg-slate-700 cursor-pointer transition-colors"
            @click="selectEntry(e)"
          >
            <div class="flex justify-between items-start mb-1">
              <span class="font-mono text-[10px] font-bold text-blue-400">{{ e.name }}</span>
              <span class="text-[9px] text-slate-500 font-mono">{{ e.date }}</span>
            </div>
            <div class="text-xs font-semibold text-slate-200 truncate">{{ e.customer }}</div>
            <div class="flex gap-3 mt-1 text-[10px] font-mono">
              <span class="text-red-400">Dr: {{ fmt(e.debit) }}</span>
              <span class="text-green-400">Cr: {{ fmt(e.credit) }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ── MAIN CONTENT ─────────────────────────────────────────── -->
      <main class="flex-1 p-8 overflow-y-auto">
        <div class="max-w-xl mx-auto space-y-6">
          <div class="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl p-6 space-y-6">
            <h2 class="text-lg font-bold text-white border-b border-slate-700 pb-3">New Entry</h2>
            
            <div class="grid grid-cols-2 gap-6">
              <!-- Date -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Date</label>
                <input 
                  v-model="form.date"
                  type="date"
                  class="rounded-xl border border-slate-600 bg-slate-900 px-4 py-2.5 font-bold text-white outline-none focus:border-blue-500"
                />
              </div>

              <!-- Customer -->
              <div class="flex flex-col gap-1.5 relative">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Customer</label>
                <input 
                  ref="customerInput"
                  v-model="customerQuery"
                  type="text"
                  placeholder="Select Customer..."
                  class="rounded-xl border border-slate-600 bg-slate-900 px-4 py-2.5 font-bold text-white outline-none focus:border-blue-500"
                  @input="onCustomerInput"
                  @keydown.down.prevent="customerHighlight = Math.min(customerHighlight + 1, customerResults.length - 1)"
                  @keydown.up.prevent="customerHighlight = Math.max(customerHighlight - 1, 0)"
                  @keydown.enter.prevent="onCustomerEnter"
                  @keydown.escape="customerResults = []"
                />
                <div v-if="customerResults.length" class="absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-xl border border-slate-600 bg-slate-900 shadow-2xl">
                  <div 
                    v-for="(c, i) in customerResults" 
                    :key="c.name"
                    class="cursor-pointer px-4 py-2.5 text-sm"
                    :class="i === customerHighlight ? 'bg-blue-600 text-white' : 'text-slate-200 hover:bg-slate-800'"
                    @mousedown.prevent="pickCustomer(c)"
                  >
                    <div class="font-semibold">{{ c.customer_name }}</div>
                    <div class="text-[10px] font-mono text-slate-500">{{ c.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-6">
              <!-- Debit -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Debit</label>
                <input 
                  ref="debitInput"
                  v-model.number="form.debit"
                  type="number"
                  step="0.01"
                  class="rounded-xl border border-slate-600 bg-slate-900 px-4 py-2.5 font-mono text-lg font-bold text-red-400 outline-none focus:border-red-500 text-right"
                  @keydown.enter.prevent="focusCredit"
                />
              </div>

              <!-- Credit -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-500">Credit</label>
                <input 
                  ref="creditInput"
                  v-model.number="form.credit"
                  type="number"
                  step="0.01"
                  class="rounded-xl border border-slate-600 bg-slate-900 px-4 py-2.5 font-mono text-lg font-bold text-green-400 outline-none focus:border-green-500 text-right"
                  @keydown.enter.prevent="saveEntry"
                />
              </div>
            </div>

            <div class="flex gap-4 pt-4">
              <button 
                class="flex-1 rounded-xl bg-slate-700 py-3 font-bold text-white hover:bg-slate-600 transition active:scale-95"
                @click="resetForm"
              >Clear</button>
              <button 
                class="flex-[2] rounded-xl bg-blue-600 py-3 font-bold text-white shadow-lg hover:bg-blue-500 transition active:scale-95 disabled:opacity-50"
                :disabled="saving || !form.customer"
                @click="saveEntry"
              >{{ saving ? 'Saving...' : 'Save Entry (End)' }}</button>
            </div>
          </div>

          <!-- SUCCESS MSG -->
          <div v-if="successMsg" class="rounded-xl bg-green-900/30 border border-green-700/50 p-4 text-green-400 text-sm font-bold text-center animate-pulse">
            {{ successMsg }}
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { searchCustomers } from '../customersearch.js'

const router = useRouter()
const API = 'ssplbilling.api.gst_ledger_api'

// ── FORM STATE ───────────────────────────────────────────────────────
const today = new Date().toISOString().split('T')[0]
const emptyForm = () => ({
  date: today,
  customer: '',
  debit: 0,
  credit: 0
})

const form = ref(emptyForm())
const customerQuery = ref('')
const saving = ref(false)
const successMsg = ref('')

// ── CUSTOMER SEARCH ──────────────────────────────────────────────────
const customerResults = ref([])
const customerHighlight = ref(0)
const customerInput = ref(null)

let customerTimer = null
function onCustomerInput() {
  clearTimeout(customerTimer)
  customerTimer = setTimeout(async () => {
    if (!customerQuery.value.trim()) { customerResults.value = []; return }
    customerResults.value = await searchCustomers(customerQuery.value)
    customerHighlight.value = 0
  }, 250)
}

function pickCustomer(c) {
  form.value.customer = c.name
  customerQuery.value = c.customer_name || c.name
  customerResults.value = []
  nextTick(focusDebit)
}

function onCustomerEnter() {
  if (customerResults.value.length) pickCustomer(customerResults.value[customerHighlight.value])
}

// ── SIDEBAR ENTRIES ──────────────────────────────────────────────────
const entries = ref([])
const loading = ref(false)
const sidebarFilter = ref('')

async function fetchEntries() {
  loading.value = true
  try {
    entries.value = await frappeGet(`${API}.get_gst_dummy_entries`)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const filteredEntries = computed(() => {
  const q = sidebarFilter.value.toLowerCase()
  if (!q) return entries.value
  return entries.value.filter(e => e.customer.toLowerCase().includes(q) || e.name.toLowerCase().includes(q))
})

function selectEntry(e) {
  form.value = { ...e }
  customerQuery.value = e.customer
}

// ── ACTIONS ──────────────────────────────────────────────────────────
async function saveEntry() {
  if (!form.value.customer) { alert('Select a customer'); return }
  if (form.value.debit === 0 && form.value.credit === 0) { alert('Enter Debit or Credit amount'); return }

  saving.value = true
  try {
    const res = await frappePost(`${API}.create_gst_dummy_entry`, { data: JSON.stringify(form.value) })
    successMsg.value = `Entry ${res} saved successfully!`
    setTimeout(() => successMsg.value = '', 3000)
    resetForm()
    fetchEntries()
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  form.value = emptyForm()
  customerQuery.value = ''
  customerResults.value = []
  nextTick(focusCustomer)
}

// ── REFS & FOCUS ─────────────────────────────────────────────────────
const debitInput = ref(null)
const creditInput = ref(null)

function focusCustomer() { customerInput.value?.focus() }
function focusDebit()    { debitInput.value?.focus(); debitInput.value?.select() }
function focusCredit()   { creditInput.value?.focus(); creditInput.value?.select() }

// ── HELPERS ───────────────────────────────────────────────────────────
function fmt(n) {
  return parseFloat(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function handleKeyDown(e) {
  if (e.key === 'End') { e.preventDefault(); saveEntry() }
  if (e.key === 'Escape') { router.push('/') }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  fetchEntries()
  nextTick(focusCustomer)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
