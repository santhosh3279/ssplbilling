<template>
  <div class="flex min-h-screen flex-col bg-slate-900">

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
          <h1 class="text-sm font-bold text-slate-100">Incentive Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-emerald-900/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex flex-wrap items-end gap-4">

        <!-- Employee search -->
        <div class="relative w-80">
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-400">Employee</label>
          <div class="relative">
            <input
              ref="empInput"
              v-model="empSearch"
              type="text"
              autocomplete="off"
              placeholder="Search employee..."
              class="w-full rounded border bg-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500 transition-colors"
              :class="selectedEmployee ? 'border-emerald-600' : 'border-slate-600'"
              @input="onEmpInput"
              @focus="showEmpDrop = true"
              @blur="setTimeout(() => { showEmpDrop = false }, 150)"
              @keydown.escape="clearEmployee"
              @keydown.enter.prevent="empOptions.length ? pickEmployee(empOptions[0]) : null"
            />
            <button
              v-if="selectedEmployee"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-400"
              @click.prevent="clearEmployee"
              tabindex="-1"
            >&times;</button>
            <div
              v-if="showEmpDrop && empOptions.length"
              class="absolute left-0 right-0 top-full z-20 mt-1 max-h-52 overflow-y-auto rounded border border-slate-600 bg-slate-800 shadow-xl"
            >
              <button
                v-for="emp in empOptions"
                :key="emp.name"
                class="w-full px-3 py-2 text-left text-sm hover:bg-blue-900/30 flex items-center justify-between"
                @mousedown.prevent="pickEmployee(emp)"
              >
                <div>
                  <div class="font-semibold text-slate-200">{{ emp.employee_name }}</div>
                  <div class="text-[10px] text-slate-500">{{ emp.name }} · {{ emp.designation || '—' }}</div>
                </div>
                <span class="ml-3 text-xs font-mono text-emerald-400">{{ fmtPts(emp.balance_incentive) }} pts</span>
              </button>
            </div>
          </div>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-400">From</label>
          <input
            v-model="fromDate"
            type="date"
            class="rounded border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-400">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
          />
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedEmployee || isLoading"
          class="rounded bg-blue-600 px-5 py-2 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-40 disabled:pointer-events-none transition-colors"
        >
          <span v-if="isLoading" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-1 align-middle"></span>
          Load
        </button>

        <button
          v-if="ledgerData"
          @click="clearAll"
          class="rounded border border-slate-600 px-4 py-2 text-sm text-slate-400 hover:bg-slate-700 transition-colors"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- ═══════ BODY ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Summary panel ── -->
      <div v-if="ledgerData" class="w-56 shrink-0 border-r border-slate-700 bg-slate-800 flex flex-col p-4 gap-4">
        <!-- Employee card -->
        <div class="rounded-lg bg-slate-700/50 border border-slate-600 p-3">
          <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">Employee</div>
          <div class="text-sm font-bold text-slate-200">{{ ledgerData.summary.employee_name }}</div>
          <div class="text-[10px] text-slate-500 mt-0.5">{{ ledgerData.summary.employee }}</div>
          <div v-if="ledgerData.summary.designation" class="mt-1 text-[10px] text-slate-400 italic">{{ ledgerData.summary.designation }}</div>
        </div>

        <!-- Stat cards -->
        <div class="rounded-lg bg-emerald-900/20 border border-emerald-800 p-3">
          <div class="text-[10px] font-bold uppercase tracking-wider text-emerald-500">Total Earned</div>
          <div class="mt-1 text-xl font-bold text-emerald-400 font-mono">{{ fmtPts(ledgerData.summary.total_incentive) }}</div>
          <div class="text-[10px] text-emerald-600">points</div>
        </div>

        <div class="rounded-lg bg-red-900/20 border border-red-800 p-3">
          <div class="text-[10px] font-bold uppercase tracking-wider text-red-400">Total Redeemed</div>
          <div class="mt-1 text-xl font-bold text-red-400 font-mono">{{ fmtPts(ledgerData.summary.redeemed_incentive) }}</div>
          <div class="text-[10px] text-red-700">points</div>
        </div>

        <div class="rounded-lg bg-blue-900/20 border border-blue-800 p-3">
          <div class="text-[10px] font-bold uppercase tracking-wider text-blue-400">Balance</div>
          <div class="mt-1 text-2xl font-bold text-blue-300 font-mono">{{ fmtPts(ledgerData.summary.balance_incentive) }}</div>
          <div class="text-[10px] text-blue-700">points</div>
        </div>
      </div>

      <!-- ── Ledger table ── -->
      <div class="flex-1 overflow-auto">
        <!-- Empty / loading state -->
        <div v-if="isLoading" class="flex h-full items-center justify-center">
          <div class="flex flex-col items-center gap-3 text-slate-500">
            <span class="h-8 w-8 animate-spin rounded-full border-4 border-slate-600 border-t-blue-500"></span>
            <span class="text-sm">Loading ledger...</span>
          </div>
        </div>

        <div v-else-if="!ledgerData" class="flex h-full items-center justify-center">
          <div class="text-center text-slate-600">
            <div class="text-5xl mb-4">🏆</div>
            <div class="text-lg font-semibold text-slate-500">Select an employee to view their incentive ledger</div>
            <div class="text-sm text-slate-600 mt-1">Search by name in the filter bar above</div>
          </div>
        </div>

        <div v-else-if="ledgerData.entries.length === 0" class="flex h-full items-center justify-center">
          <div class="text-center text-slate-600">
            <div class="text-4xl mb-3">📭</div>
            <div class="text-sm text-slate-500">No incentive entries found for the selected period</div>
          </div>
        </div>

        <table v-else class="w-full text-sm">
          <thead class="sticky top-0 bg-slate-800 z-10">
            <tr class="border-b border-slate-700 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Voucher No</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-left">Role</th>
              <th class="px-4 py-3 text-left">Party</th>
              <th class="px-4 py-3 text-right text-emerald-500">Earned</th>
              <th class="px-4 py-3 text-right text-red-400">Redeemed</th>
              <th class="px-4 py-3 text-right text-blue-400">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            <tr
              v-for="(row, idx) in ledgerData.entries"
              :key="idx"
              class="hover:bg-slate-800/50 transition-colors"
              :class="row.voucher_type === 'Incentive Redeem' ? 'bg-red-900/10' : ''"
            >
              <td class="px-4 py-2 font-mono text-[11px] text-slate-400">{{ row.date }}</td>
              <td class="px-4 py-2">
                <span class="font-mono text-xs text-blue-400">{{ row.voucher_no }}</span>
              </td>
              <td class="px-4 py-2">
                <span
                  class="rounded px-2 py-0.5 text-[10px] font-bold uppercase"
                  :class="typeClass(row.voucher_type)"
                >{{ shortType(row.voucher_type) }}</span>
              </td>
              <td class="px-4 py-2 text-[11px] text-slate-400">{{ row.role || '—' }}</td>
              <td class="px-4 py-2 text-[11px] text-slate-400 max-w-[160px] truncate" :title="row.party">{{ row.party || '—' }}</td>
              <td class="px-4 py-2 text-right font-mono font-bold" :class="row.earned ? 'text-emerald-400' : 'text-slate-700'">
                {{ row.earned ? '+' + fmtPts(row.earned) : '—' }}
              </td>
              <td class="px-4 py-2 text-right font-mono font-bold" :class="row.redeemed ? 'text-red-400' : 'text-slate-700'">
                {{ row.redeemed ? '-' + fmtPts(row.redeemed) : '—' }}
              </td>
              <td class="px-4 py-2 text-right font-mono font-bold text-slate-200">{{ fmtPts(row.balance) }}</td>
            </tr>
          </tbody>
          <!-- Footer totals -->
          <tfoot class="sticky bottom-0 bg-slate-800 border-t-2 border-slate-600">
            <tr class="text-sm font-bold">
              <td colspan="5" class="px-4 py-2 text-right text-slate-500 uppercase text-[10px] tracking-wider">Totals (filtered)</td>
              <td class="px-4 py-2 text-right font-mono text-emerald-400">+{{ fmtPts(totalEarned) }}</td>
              <td class="px-4 py-2 text-right font-mono text-red-400">-{{ fmtPts(totalRedeemed) }}</td>
              <td class="px-4 py-2 text-right font-mono text-blue-300">{{ fmtPts(totalEarned - totalRedeemed) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'

const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const empSearch = ref('')
const empOptions = ref([])
const showEmpDrop = ref(false)
const selectedEmployee = ref('')   // employee ID
const fromDate = ref('')
const toDate = ref('')
const isLoading = ref(false)
const ledgerData = ref(null)

let empSearchTimer = null

// ── Employee search ─────────────────────────────────────────────────────────
function onEmpInput(e) {
  const q = e.target.value
  empSearch.value = q
  selectedEmployee.value = ''
  ledgerData.value = null
  clearTimeout(empSearchTimer)
  if (!q.trim()) { empOptions.value = []; return }
  empSearchTimer = setTimeout(async () => {
    try {
      empOptions.value = await frappeGet('ssplbilling.api.incentive_ledger_api.search_employees', { query: q, limit: 15 })
    } catch { empOptions.value = [] }
  }, 250)
}

function pickEmployee(emp) {
  selectedEmployee.value = emp.name
  empSearch.value = emp.employee_name
  empOptions.value = []
  showEmpDrop.value = false
  loadLedger()
}

function clearEmployee() {
  selectedEmployee.value = ''
  empSearch.value = ''
  empOptions.value = []
  ledgerData.value = null
}

function clearAll() {
  clearEmployee()
  fromDate.value = ''
  toDate.value = ''
}

// ── Ledger load ──────────────────────────────────────────────────────────────
async function loadLedger() {
  if (!selectedEmployee.value) return
  isLoading.value = true
  ledgerData.value = null
  try {
    const params = { employee: selectedEmployee.value }
    if (fromDate.value) params.from_date = fromDate.value
    if (toDate.value) params.to_date = toDate.value
    ledgerData.value = await frappeGet(
      'ssplbilling.api.incentive_ledger_api.get_employee_incentive_ledger',
      params
    )
  } catch (e) {
    alert('Failed to load ledger: ' + (e.message || e))
  } finally {
    isLoading.value = false
  }
}

// ── Computed totals ──────────────────────────────────────────────────────────
const totalEarned = computed(() =>
  (ledgerData.value?.entries || []).reduce((s, r) => s + (r.earned || 0), 0)
)
const totalRedeemed = computed(() =>
  (ledgerData.value?.entries || []).reduce((s, r) => s + (r.redeemed || 0), 0)
)

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtPts(val) {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function shortType(t) {
  const map = {
    'Sales Invoice': 'Sales',
    'Purchase Invoice': 'Purchase',
    'Stock Entry': 'Transfer',
    'Incentive Redeem': 'Redeem',
  }
  return map[t] || t
}

function typeClass(t) {
  const map = {
    'Sales Invoice':    'bg-blue-900/30 text-blue-400',
    'Purchase Invoice': 'bg-amber-900/30 text-amber-400',
    'Stock Entry':      'bg-violet-900/30 text-violet-400',
    'Incentive Redeem': 'bg-red-900/30 text-red-400',
  }
  return map[t] || 'bg-slate-700 text-slate-400'
}
</script>
