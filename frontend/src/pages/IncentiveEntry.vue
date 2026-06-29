<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    
    <!-- ═══════ LEFT SIDE PANEL (UNPOSTED BILLS) ═══════ -->
    <aside class="w-96 border-r border-[var(--color-border)] bg-[var(--color-surface)]/30 flex flex-col h-full shrink-0">
      
      <!-- Panel Header -->
      <div class="p-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <h2 class="text-xl font-bold uppercase tracking-wider text-[var(--color-text)]">Unposted Bills</h2>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Select a bill to distribute incentives</p>
        
        <!-- Search & Filter Bar -->
        <div class="mt-3 flex gap-2">
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Search by Bill No or detail..."
            class="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-2xl text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none placeholder:text-[var(--color-text-muted)]/50"
          />
          <button
            @click="fetchBills"
            class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-xl hover:bg-[var(--color-midlight)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            title="Refresh list"
          >
            🔄
          </button>
        </div>

        <!-- Pill/Filter Tabs -->
        <div class="mt-2.5 flex gap-1.5 overflow-x-auto">
          <button
            v-for="filter in ['All', 'Sales', 'Purchase', 'Stock Entry']"
            :key="filter"
            @click="activeFilter = filter"
            class="rounded-full px-3 py-1 text-xs font-semibold transition-all"
            :class="activeFilter === filter 
              ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' 
              : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          >
            {{ filter }}
          </button>
        </div>
      </div>

      <!-- Bills List -->
      <div class="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
        <div v-if="loadingBills" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
          <span class="animate-spin inline-block mr-2">⏳</span> Loading bills...
        </div>
        <div v-else-if="filteredBills.length === 0" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
          No unposted bills found.
        </div>
        <div
          v-for="bill in filteredBills"
          :key="bill.name"
          @click="selectBill(bill)"
          class="rounded-xl border p-5 cursor-pointer transition-all hover:translate-x-1 duration-200"
          :class="selectedBill?.name === bill.name 
            ? 'bg-[var(--color-highlight)]/10 border-[var(--color-highlight)] shadow-md' 
            : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]'"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="font-mono font-bold text-3xl tracking-tight text-[var(--color-text)]">
              {{ bill.name }}
            </span>
            <span 
              class="rounded px-3 py-1.5 text-xl font-black uppercase tracking-wider shrink-0"
              :class="getBadgeClass(bill.doctype)"
            >
              {{ bill.doctype }}
            </span>
          </div>
          <div class="mt-4 flex items-center justify-between text-2xl text-[var(--color-text-muted)] gap-3">
            <span class="truncate max-w-[200px]">{{ bill.detail || '—' }}</span>
            <span class="font-bold text-[var(--color-text)] shrink-0">
              ₹ {{ fmt(bill.amount) }}
            </span>
          </div>
          <div class="mt-3 text-xl text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
            {{ bill.date }}
          </div>
        </div>
      </div>
    </aside>

    <!-- ═══════ MAIN CONTENT AREA ═══════ -->
    <main class="flex-1 flex flex-col h-full overflow-hidden bg-[var(--color-surface)]/20">
      
      <!-- Header -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-3 bg-[var(--color-surface)] shadow-sm shrink-0">
        <div class="flex items-center gap-4">
          <button
            @click="router.push('/')"
            class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] hover:bg-[var(--color-midlight)] transition-colors"
          >
            ←
          </button>
          <div>
            <h1 class="text-2xl font-bold uppercase tracking-wider">Incentive Entry</h1>
            <p class="text-xs text-[var(--color-text-muted)]">Post employee incentive shares for transactions</p>
          </div>
        </div>
        
        <!-- Current Doc Date/Time info -->
        <div class="flex items-center gap-6 text-sm text-[var(--color-text-muted)] shrink-0">
          <div class="flex flex-col items-end">
            <span class="uppercase tracking-widest font-black text-xs text-[var(--color-text-muted)]">Posting Date</span>
            <span class="font-mono font-bold text-2xl text-[var(--color-text)] mt-0.5">{{ doc.date }}</span>
          </div>
          <span class="h-10 w-px bg-[var(--color-border)]"></span>
          <div class="flex flex-col items-end">
            <span class="uppercase tracking-widest font-black text-xs text-[var(--color-text-muted)]">User</span>
            <span class="font-mono font-bold text-2xl text-[var(--color-text)] mt-0.5">({{ doc.user }})</span>
          </div>
        </div>
      </header>

      <!-- Main Panel Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        
        <!-- Placeholder when no bill selected -->
        <div v-if="!selectedBill" class="h-full flex flex-col items-center justify-center opacity-25 py-24 gap-4">
          <span class="text-6xl">🏆</span>
          <div class="text-xl font-bold uppercase tracking-widest text-center">
            Select a Bill from the left panel to begin
          </div>
        </div>

        <div v-else class="space-y-6">
          
          <!-- Selected Bill Info Panel -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm">
            <div class="flex items-center justify-between gap-6 flex-wrap">
              <!-- Selected Document -->
              <div class="flex items-baseline gap-3 text-3xl font-black text-[var(--color-text)]">
                <span class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Selected Document:</span>
                <span class="font-mono text-3xl">{{ selectedBill.name }}</span>
                <span class="text-xs font-semibold text-[var(--color-text-muted)] tracking-wider uppercase ml-2 bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-2.5 py-0.5 rounded-lg">
                  {{ selectedBill.doctype }} · {{ selectedBill.date }}
                </span>
              </div>
              <!-- Net Total Value -->
              <div class="flex items-baseline gap-3 text-3xl font-black text-[var(--color-text)]">
                <span class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Net Total Value:</span>
                <span class="text-3xl text-[var(--color-success)]">₹ {{ fmt(selectedBill.amount) }}</span>
              </div>
            </div>
          </div>

          <!-- Child Table: Incentive System -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-md">
            
            <table class="w-full text-left border-collapse border border-[var(--color-border)]">
              <thead>
                <tr class="bg-[var(--color-surface-raised)] border-b border-[var(--color-border)] text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)] divide-x divide-[var(--color-border)]">
                  <th class="border border-[var(--color-border)] px-4 py-3 w-16 text-center rounded-tl-2xl">#</th>
                  <th class="border border-[var(--color-border)] px-4 py-3 w-3/5">Employee Name</th>
                  <th class="border border-[var(--color-border)] px-4 py-3 w-1/5 text-center">Role</th>
                  <th class="border border-[var(--color-border)] px-4 py-3 w-40 text-center rounded-tr-2xl">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr v-if="doc.incentive_system.length === 0">
                  <td colspan="4" class="border border-[var(--color-border)] px-5 py-8 text-center text-sm text-[var(--color-text-muted)]">
                    No employees added.
                  </td>
                </tr>
                <tr 
                  v-for="(row, idx) in doc.incentive_system" 
                  :key="idx"
                  class="group hover:bg-[var(--color-midlight)]/10 transition-colors divide-x divide-[var(--color-border)]"
                >
                  <!-- Index -->
                  <td class="border border-[var(--color-border)] px-2 py-1 text-center text-2xl font-mono text-[var(--color-text-muted)]">
                    {{ idx + 1 }}
                  </td>
                  
                  <!-- Employee Name search -->
                  <td class="border border-[var(--color-border)] p-0 relative">
                    <div class="relative w-full h-full">
                      <input
                        :ref="el => { if (el) empRowInputs[idx] = el }"
                        type="text"
                        placeholder="Search employee..."
                        v-model="row._search"
                        @input="onEmployeeSearch(idx, $event.target.value)"
                        @focus="activeRowIndex = idx; activeOptionIndex = empOptions.length > 0 ? 0 : -1"
                        @blur="handleEmpBlur(idx)"
                        @keydown.down.prevent="handleEmpKeyDown"
                        @keydown.up.prevent="handleEmpKeyUp"
                        @keydown.enter.prevent="handleEmpEnter(idx)"
                        @keydown.end.prevent="focusSubmitButton"
                        class="w-full h-full bg-transparent px-2 py-1 text-3xl font-bold focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:outline-none placeholder:text-[var(--color-text-muted)]/30"
                      />
                      
                      <!-- Employee Dropdown Results -->
                      <div 
                        v-if="activeRowIndex === idx && empOptions.length > 0"
                        class="absolute left-0 right-0 top-full z-50 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl p-1 max-h-72 overflow-y-auto mt-0.5"
                      >
                        <div
                          v-for="(emp, eIdx) in empOptions"
                          :key="emp.name"
                          @mousedown.prevent="pickEmployee(idx, emp)"
                          class="rounded-xl px-5 py-3 text-2xl cursor-pointer flex justify-between gap-4 transition-colors"
                          :class="activeOptionIndex === eIdx 
                            ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] font-bold' 
                            : 'hover:bg-[var(--color-highlight)]/10 text-[var(--color-text)]'"
                        >
                          <span class="font-bold text-inherit">{{ emp.employee_name }}</span>
                          <span class="text-lg text-[var(--color-text-muted)] hover:text-inherit">{{ emp.designation || 'Staff' }}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <!-- Role Select -->
                  <td class="border border-[var(--color-border)] p-0">
                    <select
                      :ref="el => { if (el) roleSelectInputs[idx] = el }"
                      v-model="row.role"
                      @change="recalculatePoints"
                      @keydown.enter.prevent="handleRoleEnter(idx)"
                      @keydown.end.prevent="focusSubmitButton"
                      class="w-full h-full bg-transparent px-2 py-1 text-3xl font-bold text-center focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:outline-none appearance-none cursor-pointer"
                    >
                      <option value="Biller">Biller</option>
                      <option value="Sales">Sales</option>
                    </select>
                  </td>

                  <!-- Action -->
                  <td class="border border-[var(--color-border)] px-2 py-1 text-center">
                    <button
                      @click="removeRow(idx)"
                      class="text-2xl font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 rounded-lg px-3 py-1 transition-colors whitespace-nowrap"
                      title="Remove row"
                    >
                      ✕ Delete
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

        </div>

      </div>

      <!-- Bottom Submit Bar -->
      <footer 
        v-if="selectedBill"
        class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-5 shadow-md flex items-center justify-between shrink-0"
      >
        <div class="flex items-center gap-4">
          <!-- Warnings -->
          <span 
            v-if="Math.abs(distributedTotal - billDetails.totalPoints) > 0.05"
            class="text-sm font-bold text-[var(--color-warning)] bg-[var(--color-warning)]/10 px-3.5 py-1 rounded-full whitespace-nowrap"
          >
            ⚠️ Incomplete distribution
          </span>
        </div>

        <button
          ref="submitBtn"
          @click="handleSubmit"
          :disabled="isSaving || !isValid"
          class="flex items-center gap-3 rounded-2xl bg-[var(--color-success)] px-12 py-5 font-black text-2xl text-[var(--color-text-on-highlight)] shadow-lg hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed focus:ring-4 focus:ring-[var(--color-success)]/50 focus:outline-none transition-all"
        >
          <span v-if="isSaving" class="animate-spin">⏳</span>
          Submit Incentive Entry
        </button>
      </footer>

    </main>

    <!-- Success Overlay -->
    <transition name="fade">
      <div 
        v-if="successDoc"
        class="fixed top-12 left-1/2 -translate-x-1/2 z-[200] rounded-2xl bg-[var(--color-surface)] p-6 shadow-2xl border border-[var(--color-success)] flex items-center gap-4 animate-bounce"
      >
        <span class="text-2xl">✅</span>
        <div>
          <h4 class="text-base font-bold text-[var(--color-text)]">Entry Submitted!</h4>
          <p class="text-xs font-mono text-[var(--color-text-muted)]">{{ successDoc }}</p>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { session } from '../session'
import { frappeGet, frappePost, getUnpostedBills, calculateBillIncentive } from '../api.js'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const bills = ref([])
const loadingBills = ref(false)
const selectedBill = ref(null)
const searchTerm = ref('')
const activeFilter = ref('All')

const billDetails = ref({
  amount: 0,
  percentage: 0,
  totalPoints: 0
})

const doc = reactive({
  inv_no: '',
  date: new Date().toISOString().split('T')[0],
  time: new Date().toTimeString().split(' ')[0],
  user: '',
  incentive_system: []
})

const activeRowIndex = ref(-1)
const empOptions = ref([])
const isSaving = ref(false)
const successDoc = ref('')

const empRowInputs = ref([])
const roleSelectInputs = ref([])
const submitBtn = ref(null)

function focusSubmitButton() {
  nextTick(() => {
    if (submitBtn.value && !submitBtn.value.disabled) {
      submitBtn.value.focus()
    }
  })
}

function focusRowInput(idx) {
  nextTick(() => {
    const el = empRowInputs.value[idx]
    if (el) {
      el.focus()
      el.select()
    }
  })
}

function handleRoleEnter(idx) {
  if (idx === doc.incentive_system.length - 1) {
    addRow()
    nextTick(() => {
      focusRowInput(idx + 1)
    })
  } else {
    focusRowInput(idx + 1)
  }
}

const activeOptionIndex = ref(-1)

function handleEmpKeyDown() {
  if (empOptions.value.length > 0) {
    activeOptionIndex.value = (activeOptionIndex.value + 1) % empOptions.value.length
  }
}

function handleEmpKeyUp() {
  if (empOptions.value.length > 0) {
    if (activeOptionIndex.value <= 0) {
      activeOptionIndex.value = empOptions.value.length - 1
    } else {
      activeOptionIndex.value--
    }
  }
}

function handleEmpEnter(idx) {
  const row = doc.incentive_system[idx]
  if (!row) return

  const optIdx = activeOptionIndex.value >= 0 ? activeOptionIndex.value : 0
  
  if (!row.employee && empOptions.value && empOptions.value.length > optIdx) {
    pickEmployee(idx, empOptions.value[optIdx])
    return
  }
  
  if (!row.employee) {
    focusRowInput(idx)
    return
  }
  
  nextTick(() => {
    const el = roleSelectInputs.value[idx]
    if (el) el.focus()
  })
}

function handleEmpBlur(idx) {
  setTimeout(() => {
    const row = doc.incentive_system[idx]
    if (!row) return
    
    if (row._search !== row.employee_name) {
      if (row.employee) {
        row._search = row.employee_name
      } else {
        row._search = ''
      }
    }
    
    if (activeRowIndex.value === idx) {
      activeRowIndex.value = -1
      empOptions.value = []
    }
  }, 200)
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  doc.user = session.user.value
  await fetchBills()
})

// ── Get Unposted Bills list ────────────────────────────────────────────────
async function fetchBills() {
  loadingBills.value = true
  try {
    bills.value = await getUnpostedBills()
  } catch (e) {
    console.error('Failed to load unposted bills:', e)
  } finally {
    loadingBills.value = false
  }
}

// Filter bills based on search & doctype filter pills
const filteredBills = computed(() => {
  let list = bills.value

  // Doctype filter
  if (activeFilter.value !== 'All') {
    if (activeFilter.value === 'Sales') {
      list = list.filter(b => b.doctype === 'Sales Invoice')
    } else if (activeFilter.value === 'Purchase') {
      list = list.filter(b => b.doctype === 'Purchase Invoice')
    } else if (activeFilter.value === 'Stock Entry') {
      list = list.filter(b => b.doctype === 'Stock Entry')
    }
  }

  // Search filter
  if (searchTerm.value.trim()) {
    const q = searchTerm.value.toLowerCase()
    list = list.filter(b => 
      b.name.toLowerCase().includes(q) || 
      (b.detail && b.detail.toLowerCase().includes(q))
    )
  }

  return list
})

// ── Bill Selection ─────────────────────────────────────────────────────────
async function selectBill(bill) {
  selectedBill.value = bill
  doc.inv_no = bill.name
  
  // Clear any existing incentive distribution setup
  doc.incentive_system = []
  activeRowIndex.value = -1
  
  // Fetch points calculation
  try {
    const res = await calculateBillIncentive(bill.doctype, bill.name)
    billDetails.value = {
      amount: res.amount || 0,
      percentage: res.percentage || 0,
      totalPoints: res.total_points || 0
    }
    
    // Automatically add the first row
    addRow()
    
    // Focus the first row's employee search input
    focusRowInput(0)
  } catch (e) {
    console.error('Failed to calculate incentive points:', e)
    billDetails.value = { amount: 0, percentage: 0, totalPoints: 0 }
  }
}

// ── Child Table Actions ────────────────────────────────────────────────────
function addRow() {
  doc.incentive_system.push({
    employee: '',
    employee_name: '',
    role: doc.incentive_system.length === 0 ? 'Biller' : 'Sales',
    points: 0,
    _search: ''
  })
  recalculatePoints()
}

function removeRow(idx) {
  doc.incentive_system.splice(idx, 1)
  recalculatePoints()
}

// Recalculate points based on the logic from backend hooks
function recalculatePoints() {
  // Reset all row points first
  doc.incentive_system.forEach(row => {
    row.points = 0
  })

  const validRows = doc.incentive_system.filter(r => r.employee)
  const n = validRows.length
  if (n === 0) return

  const totalPoints = billDetails.value.totalPoints
  const billerIndex = validRows.findIndex(r => r.role === 'Biller')

  if (billerIndex !== -1 && n > 1) {
    const billerPoints = Number((totalPoints / (2 * n)).toFixed(2))
    const remaining = totalPoints - billerPoints
    const othersEach = Number((remaining / (n - 1)).toFixed(2))

    validRows.forEach((row, idx) => {
      row.points = idx === billerIndex ? billerPoints : othersEach
    })
  } else {
    const perPerson = Number((totalPoints / n).toFixed(2))
    validRows.forEach(row => {
      row.points = perPerson
    })
  }
}

const distributedTotal = computed(() => {
  const validRows = doc.incentive_system.filter(r => r.employee)
  return validRows.reduce((sum, r) => sum + (r.points || 0), 0)
})

// ── Employee Search within child row ───────────────────────────────────────
let searchTimer = null
function onEmployeeSearch(index, query) {
  clearTimeout(searchTimer)
  doc.incentive_system[index].employee = ''
  doc.incentive_system[index].employee_name = ''
  
  if (!query.trim()) {
    empOptions.value = []
    activeOptionIndex.value = -1
    return
  }

  searchTimer = setTimeout(async () => {
    try {
      const raw = await frappeGet('ssplbilling.api.incentive_api.search_employees', { query })
      empOptions.value = raw
      activeOptionIndex.value = raw.length > 0 ? 0 : -1
    } catch {
      empOptions.value = []
      activeOptionIndex.value = -1
    }
  }, 200)
}

function pickEmployee(index, emp) {
  const row = doc.incentive_system[index]
  row.employee = emp.name
  row.employee_name = emp.employee_name
  row._search = emp.employee_name
  
  empOptions.value = []
  activeRowIndex.value = -1
  activeOptionIndex.value = -1
  
  recalculatePoints()
  
  nextTick(() => {
    const el = roleSelectInputs.value[index]
    if (el) el.focus()
  })
}

// ── Form Validation ────────────────────────────────────────────────────────
const isValid = computed(() => {
  if (!doc.inv_no) return false
  
  const validRows = doc.incentive_system.filter(r => r.employee)
  if (validRows.length === 0) return false
  
  // Sum of valid rows points should equal rule total points (with a tiny decimal delta margin of 0.05)
  if (Math.abs(distributedTotal.value - billDetails.value.totalPoints) > 0.05) return false
  
  return true
})

// ── Document submission ─────────────────────────────────────────────────────
async function handleSubmit() {
  if (!isValid.value || isSaving.value) return
  isSaving.value = true

  try {
    const payload = {
      doctype: 'Invoice Incentive',
      inv_no: doc.inv_no,
      date: doc.date,
      time: doc.time,
      user: doc.user,
      incentive_system: doc.incentive_system.filter(r => r.employee).map(r => ({
        employee: r.employee,
        role: r.role,
        points: r.points
      }))
    }

    const res = await frappePost('frappe.client.insert', { doc: payload })
    await frappePost('frappe.client.submit', { doc: res })

    successDoc.value = res.name

    // Clear page selection
    selectedBill.value = null
    doc.inv_no = ''
    doc.incentive_system = []
    billDetails.value = { amount: 0, percentage: 0, totalPoints: 0 }

    // Reload bills list
    await fetchBills()

    setTimeout(() => {
      successDoc.value = ''
    }, 3000)
  } catch (e) {
    console.error('Failed to submit Invoice Incentive:', e)
  } finally {
    isSaving.value = false
  }
}

// ── UI Badges ──
function getBadgeClass(doctype) {
  if (doctype === 'Sales Invoice') return 'bg-[var(--color-info)]/10 text-[var(--color-info)]'
  if (doctype === 'Purchase Invoice') return 'bg-[var(--color-success)]/10 text-[var(--color-success)]'
  if (doctype === 'Stock Entry') return 'bg-[var(--color-warning)]/10 text-[var(--color-warning)]'
  return 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'
}

function fmt(n) {
  return Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtPts(n) {
  return Number(n || 0).toFixed(2)
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
