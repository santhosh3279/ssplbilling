<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ═══════ HEADER ═══════ -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-2.5 bg-[var(--color-surface)] shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="router.push('/')"
          class="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <div>
          <h1 class="text-4xl uppercase tracking-tight font-normal">Incentive Redemption</h1>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-highlight)]">New Redemption Entry</span>
            <span class="h-1 w-1 rounded-full bg-[var(--color-border)]"></span>
            <span class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest">Points to Cash Conversion</span>
          </div>
        </div>
      </div>

      <!-- Center: Rule Info -->
      <div class="hidden lg:flex items-center divide-x divide-[var(--color-border)] rounded-2xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] overflow-hidden shadow-sm">
        <div class="px-6 py-2 flex flex-col items-center min-w-[140px]">
          <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Conversion Rate</span>
          <div class="text-2xl font-mono font-black text-[var(--color-info)]">1 pt = ₹ {{ (1/conversionFactor).toFixed(2) }}</div>
        </div>
        <div class="px-6 py-2 flex flex-col items-center min-w-[200px]">
          <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Incentive Ledger</span>
          <div class="text-lg font-bold text-[var(--color-text)] truncate max-w-[300px]">{{ doc.incentive_ledger || '—' }}</div>
        </div>
      </div>

      <!-- Right: Posting Date with arrow nav -->
      <div class="flex items-center gap-2">
        <span class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</span>
        <div class="flex items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] transition-colors">
          <button
            @click="adjustDate(-1)"
            class="rounded-l-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors focus:bg-black/10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div class="relative min-w-[110px] px-3 py-1.5 text-center">
            <span class="text-2xl">{{ displayDate }}</span>
            <input type="date" v-model="doc.posting_date" class="absolute inset-0 opacity-0 cursor-pointer focus:outline-none" />
          </div>
          <button
            @click="adjustDate(1)"
            class="rounded-r-lg p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] hover:text-[var(--color-text)] transition-colors focus:bg-black/10"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <main class="flex-1 overflow-y-auto p-4 custom-scrollbar">
      <div class="flex flex-col gap-4">
        
        <!-- Excel-Style Form Table -->
        <div class="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden shrink-0">
          <table class="w-full text-left border-collapse">
            <thead class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)]">
              <tr class="text-2xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-6 py-4 w-1/3">Employee / Staff</th>
                <th class="px-6 py-4 text-right w-64">Available Points</th>
                <th class="px-6 py-4 text-right w-64 text-[var(--color-danger)]">Redeem Points</th>
                <th class="px-6 py-4 text-right w-64 text-[var(--color-success)]">Balance Points</th>
                <th class="px-6 py-4 text-right w-80">Redeem Amount (₹)</th>
              </tr>
            </thead>
            <tbody>
              <tr class="divide-x divide-[var(--color-border)] border-b border-[var(--color-border)]">
                <!-- Employee Search Column -->
                <td class="px-4 py-3 group hover:bg-[var(--color-midlight)]/20 transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                  <div class="relative">
                    <input
                      ref="empInput"
                      v-model="empSearch"
                      type="text"
                      placeholder="Search Employee..."
                      class="w-full bg-transparent text-4xl font-normal focus:outline-none placeholder:text-inherit"
                      @input="onEmpInput"
                      @focus="showEmpDrop = true"
                      @blur="setTimeout(() => showEmpDrop = false, 200)"
                    />
                    <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[var(--color-highlight)] font-bold group-focus-within:text-[var(--color-text-on-focus)] uppercase">Click to Search</div>
                    
                    <!-- Dropdown -->
                    <div v-if="showEmpDrop && empOptions.length" class="absolute left-0 right-0 top-full z-50 mt-4 max-h-96 overflow-y-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
                      <button
                        v-for="emp in empOptions"
                        :key="emp.name"
                        @mousedown.prevent="pickEmployee(emp)"
                        class="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-[var(--color-info)]/10 transition-colors border-b border-[var(--color-border)] last:border-0"
                      >
                        <div>
                          <div class="text-2xl font-bold text-[var(--color-text)]">{{ emp.employee_name }}</div>
                          <div class="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">{{ emp.name }} · {{ emp.designation || 'Staff' }}</div>
                        </div>
                        <div class="text-right">
                          <div class="text-2xl font-mono font-black text-[var(--color-success)]">{{ fmtPts(emp.balance_incentive) }}</div>
                          <div class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">Available</div>
                        </div>
                      </button>
                    </div>
                  </div>
                </td>

                <!-- Available Balance Column -->
                <td class="px-6 py-3 bg-[var(--color-surface-raised)] text-right">
                  <div class="text-4xl font-mono font-black text-[var(--color-info)]">
                    {{ fmtPts(doc.balance_points) }}
                  </div>
                </td>

                <!-- Redeem Points Input Column -->
                <td class="px-6 py-3 transition-colors bg-[var(--color-danger)]/5 focus-within:bg-[var(--color-focus)]">
                  <input
                    v-model.number="doc.redeem_points"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    class="w-full bg-transparent text-5xl font-mono font-black text-right focus:outline-none text-[var(--color-text)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none placeholder:text-inherit"
                  />
                </td>

                <!-- Balance Points Result Column -->
                <td class="px-6 py-3 bg-[var(--color-surface-raised)] text-right">
                  <div class="text-4xl font-mono font-black" :class="doc.balance_points - (doc.redeem_points || 0) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    {{ fmtPts(doc.balance_points - (doc.redeem_points || 0)) }}
                  </div>
                </td>

                <!-- Redeem Amount Column -->
                <td class="px-6 py-3 bg-[var(--color-success)]/5 text-right">
                  <div class="text-5xl font-mono font-black text-[var(--color-success)]">
                    ₹ {{ fmtPts((doc.redeem_points || 0) / conversionFactor) }}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Visual Spacer / Empty State Placeholder -->
        <div v-if="!doc.employee" class="py-32 flex flex-col items-center justify-center opacity-10 gap-6">
           <svg class="w-48 h-48" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
           </svg>
           <div class="text-4xl font-black uppercase tracking-[0.2em]">Select Employee to Begin</div>
        </div>
      </div>
    </main>

    <!-- ═══════ BOTTOM ACTION BAR ═══════ -->
    <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-[0_-4px_20px_rgba(0,0,0,0.1)]">
      <div class="flex items-center justify-between gap-8">
        
        <div class="flex items-center gap-8 flex-1">
          <!-- Company & Cost Center -->
          <div class="flex items-center gap-6 border-r border-[var(--color-border)] pr-8">
            <div class="flex flex-col gap-1.5 transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5 -m-1.5 rounded-xl">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1 transition-colors">Company</label>
              <select
                v-model="doc.company"
                class="w-64 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-lg font-bold focus:bg-black/5 focus:outline-none transition-all"
              >
                <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5 transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5 -m-1.5 rounded-xl">
              <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1 transition-colors">Cost Center</label>
              <input
                v-model="doc.cost_center"
                type="text"
                placeholder="Cost Center..."
                class="w-64 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-lg font-bold focus:bg-black/5 focus:outline-none transition-all placeholder:text-inherit"
              />
            </div>
          </div>

          <!-- Remarks -->
          <div class="flex-1 flex flex-col gap-1.5 transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)] p-1.5 -m-1.5 rounded-xl">
            <label class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] ml-1 transition-colors">Redemption Remarks</label>
            <textarea
              v-model="doc.remarks"
              rows="1"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-lg font-bold focus:bg-black/5 focus:outline-none transition-all resize-none placeholder:text-inherit"
              placeholder="Internal notes..."
            ></textarea>
          </div>
        </div>

        <!-- Save Button -->
        <div class="flex items-center pl-8 border-l border-[var(--color-border)]">
          <button
            @click="handleSave"
            :disabled="isSaving || !isValid"
            class="group relative flex items-center gap-4 overflow-hidden rounded-2xl bg-[var(--color-success)] px-12 py-5 text-3xl font-black text-[var(--color-text-on-highlight)] shadow-xl transition-all hover:scale-[1.02] hover:shadow-2xl active:scale-95 disabled:opacity-40 disabled:hover:scale-100 disabled:grayscale focus:outline-none focus:ring-8 focus:ring-[var(--color-success)]/30"
          >
            <span v-if="isSaving" class="flex items-center gap-3">
              <svg class="h-8 w-8 animate-spin" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving...
            </span>
            <span v-else class="flex items-center gap-4">
              Submit
              <svg class="h-8 w-8 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </span>
          </button>
        </div>

      </div>
    </footer>

    <!-- ═══════ STATUS MODAL ═══════ -->
    <div v-if="successDoc" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-300">
      <div class="w-full max-w-lg rounded-[2.5rem] bg-[var(--color-surface)] p-12 text-center shadow-2xl border border-[var(--color-border)] animate-in zoom-in duration-300">
        <div class="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-6xl">✅</div>
        <h3 class="text-4xl font-black text-[var(--color-text)] uppercase tracking-tight">Redemption Successful</h3>
        <p class="mt-4 text-xl text-[var(--color-text-muted)]">Points have been redeemed and entry created.</p>
        <div class="mt-8 inline-block rounded-xl bg-[var(--color-surface-raised)] px-6 py-3 font-mono text-xl font-bold text-[var(--color-info)] uppercase tracking-widest border border-[var(--color-border)]">{{ successDoc }}</div>
        <button
          @click="resetForm"
          class="mt-12 w-full rounded-2xl bg-[var(--color-highlight)] py-6 text-3xl font-black text-[var(--color-text-on-highlight)] hover:brightness-110 transition-all shadow-lg active:scale-95"
        >
          Create New Entry
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const isSaving = ref(false)
const successDoc = ref('')
const conversionFactor = ref(4.0)

const empSearch = ref('')
const empOptions = ref([])
const showEmpDrop = ref(false)

const companies = ref([])
const showCostCenterDrop = ref(false)

const doc = reactive({
  employee: '',
  employee_name: '',
  posting_date: new Date().toISOString().split('T')[0],
  company: '',
  balance_points: 0,
  redeem_points: 0,
  cost_center: '',
  incentive_ledger: '',
  remarks: ''
})

// ── Date Navigation ────────────────────────────────────────────────────────
const displayDate = computed(() => {
  if (!doc.posting_date) return ''
  const d = new Date(doc.posting_date)
  const day = String(d.getDate()).padStart(2, '0')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const month = months[d.getMonth()]
  const year = d.getFullYear()
  return `${day}-${month}-${year}`
})

function adjustDate(days) {
  const d = new Date(doc.posting_date)
  d.setDate(d.getDate() + days)
  doc.posting_date = d.toISOString().split('T')[0]
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    // Load rules
    const rule = await frappeGet('frappe.client.get', { doctype: 'Incentive Rule', name: 'Incentive Rule' })
    conversionFactor.value = Number(rule.conversion_factor || 4.0)
    doc.incentive_ledger = rule.incentive_ledger || 'Employee Incentive - SSPL'

    // Load companies
    const compList = await frappeGet('frappe.client.get_list', { doctype: 'Company', fields: ['name'] })
    companies.value = compList.map(c => c.name)
    if (companies.value.length) doc.company = companies.value[0]
    
    // Default Cost Center
    doc.cost_center = localStorage.getItem('wb-cost-center') || ''
  } catch (e) {
    console.error('Failed to init page:', e)
  }
})

// ── Employee Search ────────────────────────────────────────────────────────
let empTimer = null
function onEmpInput(e) {
  const q = e.target.value
  doc.employee = ''
  doc.balance_points = 0
  clearTimeout(empTimer)
  if (!q.trim()) { empOptions.value = []; return }
  empTimer = setTimeout(async () => {
    try {
      empOptions.value = await frappeGet('ssplbilling.api.incentive_ledger_api.search_employees', { query: q })
    } catch { empOptions.value = [] }
  }, 250)
}

function pickEmployee(emp) {
  doc.employee = emp.name
  doc.employee_name = emp.employee_name
  doc.balance_points = emp.balance_incentive
  empSearch.value = emp.employee_name
  showEmpDrop.value = false
}

// ── Validation ─────────────────────────────────────────────────────────────
const isValid = computed(() => {
  return doc.employee && 
         doc.redeem_points > 0 && 
         doc.redeem_points <= doc.balance_points &&
         doc.company &&
         doc.incentive_ledger
})

// ── Actions ────────────────────────────────────────────────────────────────
async function handleSave() {
  if (!isValid.value || isSaving.value) return
  isSaving.value = true
  try {
    const payload = {
      doctype: 'Incentive Redeem',
      employee: doc.employee,
      employee_name: doc.employee_name,
      posting_date: doc.posting_date,
      company: doc.company,
      redeem_points: doc.redeem_points,
      cost_center: doc.cost_center,
      incentive_ledger: doc.incentive_ledger,
      remarks: doc.remarks
    }
    const res = await frappePost('frappe.client.insert', { doc: payload })
    
    // Standard insert doesn't submit. We need to submit it.
    await frappePost('frappe.client.submit', { doc: res })
    
    successDoc.value = res.name
  } catch (e) {
    // Error is handled by frappePost alert
  } finally {
    isSaving.value = false
  }
}

function resetForm() {
  successDoc.value = ''
  doc.employee = ''
  doc.employee_name = ''
  doc.balance_points = 0
  doc.redeem_points = 0
  doc.remarks = ''
  empSearch.value = ''
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fmtPts(val) {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
  -webkit-appearance: none; 
  margin: 0; 
}
</style>
