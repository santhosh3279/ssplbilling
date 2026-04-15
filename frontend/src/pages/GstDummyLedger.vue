<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">WGB PAYMENTS</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Tab</kbd> Next field</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">End</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- ── LEFT SIDEBAR (Recent Entries) ────────────────────────── -->
      <aside class="flex w-72 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <div class="p-3 border-b border-[var(--color-border)] flex flex-col gap-2">
          <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Recent Entries</div>
          <input 
            v-model="sidebarFilter"
            type="text"
            placeholder="Search customer..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-xs outline-none focus:border-[var(--color-info)]"
          />
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loading" class="p-4 text-center text-xs text-[var(--color-text-muted)]">Loading...</div>
          <div v-else-if="!entries.length" class="p-4 text-center text-xs text-[var(--color-text-muted)] italic">No entries found</div>
          <div 
            v-for="e in filteredEntries" 
            :key="e.name"
            class="border-b border-[var(--color-border)] p-3 hover:bg-[var(--color-surface-raised)] cursor-pointer transition-colors"
            @click="selectEntry(e)"
          >
            <div class="flex justify-between items-start mb-1">
              <span class="font-mono text-[10px] font-bold text-[var(--color-info)]">{{ e.name }}</span>
              <span class="text-[9px] text-[var(--color-text-muted)] font-mono">{{ e.date }}</span>
            </div>
            <div class="text-xs font-semibold text-[var(--color-text)] truncate">{{ e.customer }}</div>
            <div class="flex gap-3 mt-1 text-[10px] font-mono">
              <span class="text-[var(--color-danger)]">Dr: {{ fmt(e.debit) }}</span>
              <span class="text-[var(--color-success)]">Cr: {{ fmt(e.credit) }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ── MAIN CONTENT ─────────────────────────────────────────── -->
      <main class="flex-1 p-8 overflow-y-auto">
        <div class="max-w-xl mx-auto space-y-6">
          <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-2xl p-6 space-y-6">
            <h2 class="text-lg font-bold text-[var(--color-text-on-highlight)] border-b border-[var(--color-border)] pb-3">New Entry</h2>
            
            <div class="grid grid-cols-2 gap-6">
              <!-- Date -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Date</label>
                <input 
                  v-model="form.date"
                  type="date"
                  class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2.5 font-bold text-[var(--color-text-on-highlight)] outline-none focus:border-[var(--color-info)]"
                />
              </div>

              <!-- Customer -->
              <div class="flex flex-col gap-1.5 relative">
                <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Customer</label>
                <input 
                  ref="customerInput"
                  v-model="customerQuery"
                  type="text"
                  placeholder="Select Customer..."
                  class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2.5 font-bold text-[var(--color-text-on-highlight)] outline-none focus:border-[var(--color-info)]"
                  @input="onCustomerInput"
                  @keydown.down.prevent="customerHighlight = Math.min(customerHighlight + 1, customerResults.length - 1)"
                  @keydown.up.prevent="customerHighlight = Math.max(customerHighlight - 1, 0)"
                  @keydown.enter.prevent="onCustomerEnter"
                  @keydown.escape="customerResults = []"
                />
                <div v-if="customerResults.length" class="absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl">
                  <div 
                    v-for="(c, i) in customerResults" 
                    :key="c.name"
                    class="cursor-pointer px-4 py-2.5 text-sm"
                    :class="i === customerHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)] hover:bg-[var(--color-surface)]'"
                    @mousedown.prevent="pickCustomer(c)"
                  >
                    <div class="font-semibold">{{ c.customer_name }}</div>
                    <div class="text-[10px] font-mono text-[var(--color-text-muted)]">{{ c.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-6">
              <!-- Debit -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Debit</label>
                <input 
                  ref="debitInput"
                  v-model.number="form.debit"
                  type="number"
                  step="0.01"
                  class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2.5 font-mono text-lg font-bold text-[var(--color-danger)] outline-none focus:border-[var(--color-danger)] text-right"
                  @keydown.enter.prevent="focusCredit"
                />
              </div>

              <!-- Credit -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Credit</label>
                <input 
                  ref="creditInput"
                  v-model.number="form.credit"
                  type="number"
                  step="0.01"
                  class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2.5 font-mono text-lg font-bold text-[var(--color-success)] outline-none focus:border-[var(--color-success)] text-right"
                  @keydown.enter.prevent="saveEntry"
                />
              </div>
            </div>

            <div class="flex gap-4 pt-4">
              <button 
                class="flex-1 rounded-xl bg-[var(--color-surface-raised)] py-3 font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-surface-raised)] transition active:scale-95"
                @click="resetForm"
              >Clear</button>
              <button 
                class="flex-[2] rounded-xl bg-[var(--color-info)] py-3 font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] transition active:scale-95 disabled:opacity-50"
                :disabled="saving || !form.customer"
                @click="saveEntry"
              >{{ saving ? 'Saving...' : 'Save Entry (End)' }}</button>
            </div>
          </div>

          <!-- SUCCESS MSG -->
          <div v-if="successMsg" class="rounded-xl bg-[var(--color-success)]/30 border border-[var(--color-success)]/50 p-4 text-[var(--color-success)] text-sm font-bold text-center animate-pulse">
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
