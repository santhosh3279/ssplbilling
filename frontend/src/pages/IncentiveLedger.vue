<template>
  <div class="flex min-h-screen flex-col bg-[var(--color-bg)]">

    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-xl font-bold text-[var(--color-text)]">Incentive Ledger</h1>
          <span v-if="ledgerData" class="rounded bg-[var(--color-success)]/20 px-2 py-0.5 text-[20px] font-semibold text-[var(--color-success)]">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-wrap items-end gap-4">

        <!-- Employee search -->
        <div class="relative w-80">
          <label class="mb-1 block text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Employee</label>
          <div class="relative">
            <input
              ref="empInput"
              v-model="empSearch"
              type="text"
              autocomplete="off"
              placeholder="Search employee..."
              class="w-full rounded border bg-[var(--color-surface-raised)] px-3 py-2 text-xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-colors"
              :class="selectedEmployee ? 'border-[var(--color-success)]' : 'border-[var(--color-border)]'"
              @input="onEmpInput"
              @focus="showEmpDrop = true"
              @blur="setTimeout(() => { showEmpDrop = false }, 150)"
              @keydown="quickLedgerSearchRef?.handleKeydown($event)"
            />
            <button
              v-if="selectedEmployee"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-danger)]"
              @click.prevent="clearEmployee"
              tabindex="-1"
            >&times;</button>

            <!-- Quick Ledger Search -->
            <QuickLedgerSearch
              ref="quickLedgerSearchRef"
              :results="empOptions"
              :query="empSearch"
              :anchorEl="empInput"
              balanceLabel="Points Total"
              :isPoints="true"
              v-if="showEmpDrop && empOptions.length"
              @select="pickEmployee"
              @close="showEmpDrop = false"
            />
          </div>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
          <input
            v-model="fromDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedEmployee || isLoading"
          class="rounded bg-[var(--color-info)] px-5 py-2 text-xl font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] disabled:opacity-40 disabled:pointer-events-none transition-colors"
        >
          <span v-if="isLoading" class="inline-block h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent mr-1 align-middle"></span>
          Load
        </button>

        <button
          v-if="ledgerData"
          @click="clearAll"
          class="rounded border border-[var(--color-border)] px-4 py-2 text-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-colors"
        >
          Clear
        </button>

        <!-- Horizontal Summary Stats -->
        <div v-if="ledgerData" class="ml-auto flex items-center gap-8">
          <div class="flex flex-col items-end">
            <span class="text-[14px] font-bold uppercase tracking-wider text-[var(--color-success)]">Earned</span>
            <span class="text-3xl font-bold text-[var(--color-success)] font-mono">{{ fmtPts(ledgerData.summary.total_incentive) }}</span>
          </div>
          <div class="flex flex-col items-end border-l border-[var(--color-border)] pl-8">
            <span class="text-[14px] font-bold uppercase tracking-wider text-[var(--color-danger)]">Redeemed</span>
            <span class="text-3xl font-bold text-[var(--color-danger)] font-mono">{{ fmtPts(ledgerData.summary.redeemed_incentive) }}</span>
          </div>
          <div class="flex flex-col items-end border-l border-[var(--color-border)] pl-8">
            <span class="text-[14px] font-bold uppercase tracking-wider text-[var(--color-info)]">Balance</span>
            <span class="text-4xl font-bold text-[var(--color-info)] font-mono">{{ fmtPts(ledgerData.summary.balance_incentive) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════ BODY ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Ledger table ── -->
      <div class="flex-1 overflow-auto">
        <!-- Empty / loading state -->
        <div v-if="isLoading" class="flex h-full items-center justify-center">
          <div class="flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
            <span class="h-16 w-16 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-blue-500"></span>
            <span class="text-xl">Loading ledger...</span>
          </div>
        </div>

        <div v-else-if="!ledgerData" class="flex h-full items-center justify-center">
          <div class="text-center text-[var(--color-text-muted)]">
            <div class="text-9xl mb-4">🏆</div>
            <div class="text-3xl font-semibold text-[var(--color-text-muted)]">Select an employee to view their incentive ledger</div>
            <div class="text-xl text-[var(--color-text-muted)] mt-1">Search by name in the filter bar above</div>
          </div>
        </div>

        <div v-else-if="ledgerData.entries.length === 0" class="flex h-full items-center justify-center">
          <div class="text-center text-[var(--color-text-muted)]">
            <div class="text-8xl mb-3">📭</div>
            <div class="text-xl text-[var(--color-text-muted)]">No incentive entries found for the selected period</div>
          </div>
        </div>

        <table v-else class="w-full text-xl">
          <thead class="sticky top-0 bg-[var(--color-surface)] z-10">
            <tr class="border-b border-[var(--color-border)] text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Voucher No</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-left">Role</th>
              <th class="px-4 py-3 text-left">Party</th>
              <th class="px-4 py-3 text-right text-[var(--color-success)]">Earned</th>
              <th class="px-4 py-3 text-right text-[var(--color-danger)]">Redeemed</th>
              <th class="px-4 py-3 text-right text-[var(--color-info)]">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            <tr
              v-for="(row, idx) in ledgerData.entries"
              :key="idx"
              class="hover:bg-[var(--color-surface)]/50 transition-colors"
              :class="row.voucher_type === 'Incentive Redeem' ? 'bg-[var(--color-danger)]/10' : ''"
            >
              <td class="px-4 py-2 font-mono text-[22px] text-[var(--color-text-muted)]">{{ formatDMY(row.date, '') }}</td>
              <td class="px-4 py-2">
                <span class="font-mono text-4xl text-[var(--color-info)]">{{ row.voucher_no }}</span>
              </td>
              <td class="px-4 py-2">
                <span
                  class="rounded px-2 py-0.5 text-[20px] font-bold uppercase"
                  :class="typeClass(row.voucher_type)"
                >{{ shortType(row.voucher_type) }}</span>
              </td>
              <td class="px-4 py-2 text-[22px] text-[var(--color-text-muted)]">{{ row.role || '—' }}</td>
              <td class="px-4 py-2 text-[22px] text-[var(--color-text-muted)] max-w-[320px] truncate" :title="row.party">{{ row.party || '—' }}</td>
              <td class="px-4 py-2 text-right font-mono font-bold text-4xl" :class="row.earned ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'">
                {{ row.earned ? '+' + fmtPts(row.earned) : '—' }}
              </td>
              <td class="px-4 py-2 text-right font-mono font-bold text-4xl" :class="row.redeemed ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                {{ row.redeemed ? '-' + fmtPts(row.redeemed) : '—' }}
              </td>
              <td class="px-4 py-2 text-right font-mono font-bold text-4xl text-[var(--color-text)]">{{ fmtPts(row.balance) }}</td>
            </tr>
          </tbody>
          <!-- Footer totals -->
          <tfoot class="sticky bottom-0 bg-[var(--color-surface)] border-t-2 border-[var(--color-border)]">
            <tr class="text-xl font-bold">
              <td colspan="5" class="px-4 py-2 text-right text-[var(--color-text-muted)] uppercase text-[20px] tracking-wider">Totals (filtered)</td>
              <td class="px-4 py-2 text-right font-mono text-4xl text-[var(--color-success)]">+{{ fmtPts(totalEarned) }}</td>
              <td class="px-4 py-2 text-right font-mono text-4xl text-[var(--color-danger)]">-{{ fmtPts(totalRedeemed) }}</td>
              <td class="px-4 py-2 text-right font-mono text-4xl text-[var(--color-info)]">{{ fmtPts(totalEarned - totalRedeemed) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import QuickLedgerSearch from '../components/QuickLedgerSearch.vue'

import { formatDMY } from '../utils/date'
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

const empInput = ref(null)
const quickLedgerSearchRef = ref(null)

let empSearchTimer = null

onMounted(() => {
  nextTick(() => {
    empInput.value?.focus()
  })
})

// ── Employee search ─────────────────────────────────────────────────────────
function onEmpInput(e) {
  const q = e.target.value
  empSearch.value = q
  selectedEmployee.value = ''
  ledgerData.value = null
  showEmpDrop.value = true
  clearTimeout(empSearchTimer)
  if (!q.trim()) { empOptions.value = []; return }
  empSearchTimer = setTimeout(async () => {
    try {
      const raw = await frappeGet('ssplbilling.api.incentive_ledger_api.search_employees', { query: q, limit: 15 })
      empOptions.value = raw.map(e => ({
        ...e,
        label: e.employee_name,
        balance: e.balance_incentive,
        type: 'Employee',
        group: e.designation
      }))
    } catch { empOptions.value = [] }
  }, 250)
}

function pickEmployee(emp) {
  selectedEmployee.value = emp.name
  empSearch.value = emp.label || emp.employee_name
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
    'Sales Invoice':    'bg-[var(--color-info)]/30 text-[var(--color-info)]',
    'Purchase Invoice': 'bg-[var(--color-warning)]/30 text-[var(--color-warning)]',
    'Stock Entry':      'bg-[var(--color-info)]/30 text-[var(--color-info)]',
    'Incentive Redeem': 'bg-[var(--color-danger)]/30 text-[var(--color-danger)]',
  }
  return map[t] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'
}
</script>
