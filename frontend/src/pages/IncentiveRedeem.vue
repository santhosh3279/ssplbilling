<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span class="text-3xl text-[var(--color-text-muted)]">|</span>
          <h1 class="text-4xl font-bold text-[var(--color-text)]">Incentive Redemption</h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleSave"
            :disabled="isSaving || !isValid"
            class="rounded bg-[var(--color-success)] px-4 py-1.5 text-3xl font-bold text-[var(--color-text-on-highlight)] hover:brightness-110 disabled:opacity-50 transition-all"
          >
            {{ isSaving ? 'Submitting...' : 'Submit Redemption' }}
          </button>
        </div>
      </div>
    </header>

    <!-- ═══════ FORM ═══════ -->
    <main class="flex-1 overflow-auto p-8">
      <div class="mx-auto max-w-2xl rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="bg-[var(--color-highlight)]/10 px-6 py-4 border-b border-[var(--color-border)]">
          <h2 class="text-sm font-bold text-[var(--color-text)]">New Redemption Entry</h2>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest mt-0.5">Points to Cash Conversion</p>
        </div>

        <div class="p-8 space-y-6">
          <!-- Employee Selection -->
          <div class="grid grid-cols-2 gap-6">
            <div class="relative">
              <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Employee</label>
              <div class="relative">
                <input
                  ref="empInput"
                  v-model="empSearch"
                  type="text"
                  placeholder="Search by name..."
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                  :class="doc.employee ? 'border-[var(--color-success)] ring-1 ring-[var(--color-success)]/20' : ''"
                  @input="onEmpInput"
                  @focus="showEmpDrop = true"
                  @blur="setTimeout(() => showEmpDrop = false, 200)"
                />
                <div v-if="showEmpDrop && empOptions.length" class="absolute left-0 right-0 top-full z-50 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
                  <button
                    v-for="emp in empOptions"
                    :key="emp.name"
                    @mousedown.prevent="pickEmployee(emp)"
                    class="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-[var(--color-info)]/10 transition-colors border-b border-[var(--color-border)] last:border-0"
                  >
                    <div>
                      <div class="text-sm font-bold text-[var(--color-text)]">{{ emp.employee_name }}</div>
                      <div class="text-[10px] text-[var(--color-text-muted)]">{{ emp.name }} · {{ emp.designation || 'Staff' }}</div>
                    </div>
                    <div class="text-xs font-mono font-bold text-[var(--color-success)]">
                      {{ fmtPts(emp.balance_incentive) }} <span class="text-[9px] opacity-60">pts</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</label>
              <input
                v-model="doc.posting_date"
                type="date"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
              />
            </div>
          </div>

          <!-- Points Display & Entry -->
          <div class="grid grid-cols-2 gap-6 items-end">
            <div class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] p-4">
              <div class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-2">Available Balance</div>
              <div class="flex items-baseline gap-2">
                <span class="text-3xl font-mono font-black text-[var(--color-info)]">{{ fmtPts(doc.balance_points) }}</span>
                <span class="text-xs font-bold text-[var(--color-text-muted)]">Points</span>
              </div>
            </div>

            <div>
              <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Redeem Points</label>
              <div class="relative">
                <input
                  v-model.number="doc.redeem_points"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-mono font-bold text-[var(--color-danger)] outline-none focus:border-[var(--color-danger)] transition-all"
                />
                <div class="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-[var(--color-text-muted)] uppercase">Points</div>
              </div>
            </div>
          </div>

          <!-- Conversion Preview -->
          <div v-if="doc.redeem_points > 0" class="rounded-xl border-2 border-dashed border-[var(--color-success)]/30 bg-[var(--color-success)]/5 p-4 text-center">
            <div class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-success)] mb-1">Conversion Preview</div>
            <div class="flex items-center justify-center gap-4">
              <div class="text-lg font-mono text-[var(--color-text)]">{{ doc.redeem_points }} pts</div>
              <div class="text-2xl">➔</div>
              <div class="text-2xl font-mono font-black text-[var(--color-success)]">₹ {{ fmtPts(doc.redeem_points / conversionFactor) }}</div>
            </div>
            <div class="mt-1 text-[9px] text-[var(--color-text-muted)] italic">Based on conversion factor of {{ conversionFactor }}</div>
          </div>

          <!-- Account Settings -->
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Company</label>
              <select
                v-model="doc.company"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm text-[var(--color-text)] outline-none"
              >
                <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cost Center</label>
              <div class="relative">
                <input
                  v-model="doc.cost_center"
                  type="text"
                  placeholder="Search cost center..."
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-sm text-[var(--color-text)] outline-none"
                  @focus="showCostCenterDrop = true"
                  @blur="setTimeout(() => showCostCenterDrop = false, 200)"
                />
                <!-- Simplified dropdown for demonstration -->
              </div>
            </div>
          </div>

          <div class="border-t border-[var(--color-border)] pt-6">
             <label class="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Incentive Ledger</label>
             <input
               v-model="doc.incentive_ledger"
               type="text"
               readonly
               class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm text-[var(--color-text-muted)]"
             />
             <p class="mt-1.5 text-[9px] text-[var(--color-text-muted)] italic">Ledger is automatically determined by Incentive Rule settings.</p>
          </div>
        </div>
      </div>
    </main>

    <!-- ═══════ STATUS MODAL ═══════ -->
    <div v-if="successDoc" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div class="w-full max-w-sm rounded-2xl bg-[var(--color-surface)] p-8 text-center shadow-2xl border border-[var(--color-border)] animate-in zoom-in duration-300">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-3xl">✅</div>
        <h3 class="text-xl font-black text-[var(--color-text)]">Redemption Successful</h3>
        <p class="mt-2 text-sm text-[var(--color-text-muted)]">Points have been redeemed and payment entry created.</p>
        <div class="mt-6 font-mono text-xs font-bold text-[var(--color-info)] uppercase tracking-widest">{{ successDoc }}</div>
        <button
          @click="resetForm"
          class="mt-8 w-full rounded-xl bg-[var(--color-highlight)] py-3 font-bold text-[var(--color-text-on-highlight)] hover:brightness-110 transition-all"
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
  incentive_ledger: ''
})

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
      incentive_ledger: doc.incentive_ledger
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
