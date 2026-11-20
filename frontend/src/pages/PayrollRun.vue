<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="payroll" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">Payroll Run</h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Check the month, create salary slips for the chosen employees, review them, then submit.
          </p>
        </div>
        <button
          @click="load"
          :disabled="busy"
          class="rounded-xl border border-[var(--color-border)] px-5 py-3 text-sm font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
        >
          🔄 Reload
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-8 relative space-y-6">
        <div v-if="busy" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">{{ busyText }}</p>
        </div>

        <div v-if="error" class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500 whitespace-pre-line">
          {{ error }}
        </div>
        <div
          v-if="messages.length"
          class="rounded-xl border border-[var(--color-info)]/30 bg-[var(--color-info)]/10 px-5 py-3 text-sm font-semibold text-[var(--color-text)] space-y-1"
        >
          <div v-for="(m, i) in messages" :key="i">{{ m }}</div>
        </div>

        <!-- Period -->
        <div class="flex flex-wrap items-end gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Month</label>
            <input
              v-model="month"
              type="month"
              @change="load"
              class="mt-1 block px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Company</label>
            <select
              v-model="company"
              @change="load"
              class="mt-1 block min-w-[260px] px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Posting Date</label>
            <input
              v-model="postingDate"
              type="date"
              :disabled="!!run"
              class="mt-1 block px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)] disabled:opacity-60"
            />
          </div>
          <div v-if="overview" class="ml-auto text-right text-sm">
            <div class="font-bold">{{ fmtDate(overview.start_date) }} → {{ fmtDate(overview.end_date) }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">
              {{ overview.period_days }} days · based on {{ overview.settings.payroll_based_on || '—' }} ·
              payable {{ overview.payroll_payable_account || '—' }}
            </div>
          </div>
        </div>

        <!-- Steps -->
        <div class="grid grid-cols-4 gap-3">
          <div
            v-for="(s, i) in steps"
            :key="s.key"
            class="rounded-xl px-4 py-3 text-sm font-bold"
            :class="i < stepIndex
              ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
              : i === stepIndex
                ? 'bg-[var(--color-employee)] text-white shadow-lg'
                : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border border-[var(--color-border)]'"
          >
            <span class="mr-1">{{ i < stepIndex ? '✓' : i + 1 }}.</span> {{ s.label }}
          </div>
        </div>

        <!-- Checks -->
        <div v-if="overview && overview.checks.length" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md space-y-2">
          <h3 class="text-base font-bold uppercase tracking-wider border-b border-[var(--color-border)] pb-3 mb-2">Before you run</h3>
          <div
            v-for="c in overview.checks"
            :key="c.code + c.message"
            class="flex items-start gap-3 rounded-xl px-4 py-3 text-sm"
            :class="c.level === 'blocker' ? 'bg-rose-500/10 text-rose-500' : 'bg-[var(--color-warning)]/10 text-[var(--color-text)]'"
          >
            <span class="font-black uppercase text-[10px] tracking-wider mt-0.5 shrink-0 w-16">
              {{ c.level === 'blocker' ? '⛔ Fix' : '⚠ Note' }}
            </span>
            <span class="flex-1 font-semibold">{{ c.message }}</span>
            <a
              v-if="deskLink(c.link)"
              :href="deskLink(c.link)"
              target="_blank"
              class="shrink-0 text-xs font-bold underline text-[var(--color-info)]"
            >
              Open in desk ↗
            </a>
          </div>
        </div>

        <!-- Run actions -->
        <div v-if="overview" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex-1 min-w-[260px]">
              <div class="text-xs font-black uppercase tracking-wider text-[var(--color-text-muted)]">
                {{ run ? 'Payroll Entry' : 'No payroll run yet' }}
              </div>
              <div v-if="run" class="text-lg font-black">
                <a :href="`/app/payroll-entry/${encodeURIComponent(run.name)}`" target="_blank" class="hover:underline">{{ run.name }}</a>
                <span class="ml-2 rounded-lg px-2 py-0.5 text-xs" :class="statusClass(run.status)">{{ run.status }}</span>
              </div>
              <div v-else class="text-sm font-semibold">{{ selected.size }} of {{ readyRows.length }} payable employee(s) selected</div>
              <div v-if="run" class="text-xs text-[var(--color-text-muted)] mt-1">
                {{ run.number_of_employees }} employee(s) · {{ run.draft_slips }} draft slip(s) · {{ run.submitted_slips }} submitted
              </div>
              <div v-if="run && run.error_message" class="mt-2 rounded-lg bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-500 whitespace-pre-line">
                {{ run.error_message }}
              </div>
            </div>

            <template v-if="stage === 'select'">
              <button
                @click="startRun"
                :disabled="busy || hasBlocker || !selected.size"
                class="rounded-xl bg-[var(--color-employee)] px-6 py-3 text-sm font-bold text-white shadow hover:brightness-110 disabled:opacity-40"
              >
                ➕ Start Payroll ({{ selected.size }})
              </button>
            </template>
            <template v-else-if="stage === 'create'">
              <button
                @click="createSlips"
                :disabled="busy"
                class="rounded-xl bg-[var(--color-employee)] px-6 py-3 text-sm font-bold text-white shadow hover:brightness-110 disabled:opacity-40"
              >
                🧾 {{ run.docstatus === 1 ? 'Retry Creating Salary Slips' : 'Create Salary Slips' }}
              </button>
            </template>
            <template v-else-if="stage === 'review'">
              <button
                @click="submitSlips"
                :disabled="busy"
                class="rounded-xl bg-[var(--color-success)] px-6 py-3 text-sm font-bold text-white shadow hover:brightness-110 disabled:opacity-40"
              >
                ✅ Submit {{ run.draft_slips }} Salary Slip(s)
              </button>
            </template>
            <template v-else-if="stage === 'queued'">
              <span class="text-sm font-bold text-[var(--color-info)]">⏳ Running in background — refreshing…</span>
            </template>
            <template v-else-if="stage === 'done'">
              <span class="text-sm font-bold text-[var(--color-success)]">✓ Salary slips submitted</span>
            </template>

            <button
              v-if="run && stage !== 'queued'"
              @click="discardRun"
              :disabled="busy"
              class="rounded-xl border border-rose-500/40 px-5 py-3 text-sm font-bold text-rose-500 hover:bg-rose-500/10 disabled:opacity-40"
            >
              {{ run.docstatus === 0 ? '🗑 Discard Run' : '↩ Cancel Run' }}
            </button>
          </div>

          <!-- Totals -->
          <div v-if="slipRows.length" class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="rounded-xl bg-[var(--color-bg)] p-4">
              <div class="text-[10px] font-black uppercase tracking-wider text-[var(--color-text-muted)]">Slips</div>
              <div class="text-xl font-black">{{ slipRows.length }}</div>
            </div>
            <div class="rounded-xl bg-[var(--color-bg)] p-4">
              <div class="text-[10px] font-black uppercase tracking-wider text-[var(--color-text-muted)]">Gross</div>
              <div class="text-xl font-black">{{ money(totals.gross) }}</div>
            </div>
            <div class="rounded-xl bg-[var(--color-bg)] p-4">
              <div class="text-[10px] font-black uppercase tracking-wider text-[var(--color-text-muted)]">Deductions</div>
              <div class="text-xl font-black text-rose-500">{{ money(totals.deduction) }}</div>
            </div>
            <div class="rounded-xl bg-[var(--color-bg)] p-4">
              <div class="text-[10px] font-black uppercase tracking-wider text-[var(--color-text-muted)]">Net Pay</div>
              <div class="text-xl font-black text-[var(--color-success)]">{{ money(totals.net) }}</div>
            </div>
          </div>
        </div>

        <!-- Employees -->
        <div v-if="overview" class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-md overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
            <h3 class="text-base font-bold uppercase tracking-wider">Employees ({{ visibleRows.length }})</h3>
            <label class="flex items-center gap-2 text-xs font-bold text-[var(--color-text-muted)]">
              <input v-model="showBlocked" type="checkbox" class="h-4 w-4" />
              Show employees who can't be paid
            </label>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-[var(--color-bg)] text-[10px] font-black uppercase tracking-wider text-[var(--color-text-muted)]">
                <tr>
                  <th class="px-4 py-3 text-left w-10">
                    <input
                      v-if="stage === 'select'"
                      type="checkbox"
                      class="h-4 w-4"
                      :checked="readyRows.length > 0 && selected.size === readyRows.length"
                      @change="toggleAll($event.target.checked)"
                    />
                  </th>
                  <th class="px-4 py-3 text-left">Employee</th>
                  <th class="px-4 py-3 text-left">Structure</th>
                  <th class="px-4 py-3 text-right">Base</th>
                  <th class="px-4 py-3 text-right" title="Present / Work From Home">Pres</th>
                  <th class="px-4 py-3 text-right">Half</th>
                  <th class="px-4 py-3 text-right">Abs</th>
                  <th class="px-4 py-3 text-right">Leave</th>
                  <th class="px-4 py-3 text-right">Hol</th>
                  <th class="px-4 py-3 text-right" title="Days on the rolls with no attendance and no holiday">Unmarked</th>
                  <th class="px-4 py-3 text-right">Pay Days</th>
                  <th class="px-4 py-3 text-right">Gross</th>
                  <th class="px-4 py-3 text-right">Ded.</th>
                  <th class="px-4 py-3 text-right">Net</th>
                  <th class="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="row in visibleRows"
                  :key="row.employee"
                  class="transition-colors"
                  :class="rowSelected(row) ? 'bg-[var(--color-employee)]/10' : 'hover:bg-[var(--color-midlight)]/40'"
                >
                  <td class="px-4 py-2">
                    <input
                      v-if="stage === 'select' && row.state === 'ready'"
                      type="checkbox"
                      class="h-4 w-4"
                      :checked="selected.has(row.employee)"
                      @change="toggle(row.employee, $event.target.checked)"
                    />
                  </td>
                  <td class="px-4 py-2">
                    <div class="font-bold">{{ row.employee_name }}</div>
                    <div class="text-[10px] text-[var(--color-text-muted)]">{{ row.employee }}<span v-if="row.department"> · {{ row.department }}</span></div>
                  </td>
                  <td class="px-4 py-2 text-xs">{{ row.salary_structure || '—' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.base ? money(row.base) : '—' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.present }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.half_day || '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.absent || '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.on_leave || '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.holidays || '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums font-bold" :class="row.unmarked ? 'text-[var(--color-warning)]' : ''">
                    {{ row.unmarked || '' }}
                  </td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.slip ? row.slip.payment_days : '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums">{{ row.slip ? money(row.slip.gross_pay) : '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums text-rose-500">{{ row.slip ? money(row.slip.total_deduction) : '' }}</td>
                  <td class="px-4 py-2 text-right tabular-nums font-bold">{{ row.slip ? money(row.slip.net_pay) : '' }}</td>
                  <td class="px-4 py-2 text-xs">
                    <template v-if="row.slip">
                      <span class="rounded-lg px-2 py-0.5 font-bold" :class="statusClass(row.slip.status)">{{ row.slip.status }}</span>
                      <a :href="slipPrintUrl(row.slip.name)" target="_blank" class="ml-2 font-bold text-[var(--color-info)] hover:underline">Print</a>
                    </template>
                    <span v-else-if="row.problem" class="font-semibold text-rose-500">{{ row.problem }}</span>
                    <span v-else-if="run && !run.employees.includes(row.employee)" class="text-[var(--color-text-muted)]">Not in this run</span>
                    <span v-else class="font-semibold text-[var(--color-success)]">Ready</span>
                  </td>
                </tr>
                <tr v-if="!visibleRows.length">
                  <td colspan="15" class="px-6 py-10 text-center text-[var(--color-text-muted)]">No employees for this company and month.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import { serverCalendarDate } from '../services/serverTime'
import {
  fetchPayrollOverview,
  createPayrollRun,
  createPayrollSalarySlips,
  submitPayrollSalarySlips,
  cancelPayrollRun,
} from '../api.js'

const steps = [
  { key: 'select', label: 'Check & choose employees' },
  { key: 'create', label: 'Create salary slips' },
  { key: 'review', label: 'Review & submit' },
  { key: 'done', label: 'Done' },
]

// Payroll is normally run for the month just closed, so that is the default.
function previousMonth() {
  const d = serverCalendarDate()
  const prev = new Date(d.getFullYear(), d.getMonth() - 1, 1)
  return `${prev.getFullYear()}-${String(prev.getMonth() + 1).padStart(2, '0')}`
}

function lastDayOf(monthValue) {
  const [y, m] = monthValue.split('-').map(Number)
  const d = new Date(y, m, 0)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const month = ref(previousMonth())
const company = ref('')
const companies = ref([])
const postingDate = ref(lastDayOf(month.value))
const overview = ref(null)
const selected = ref(new Set())
const showBlocked = ref(true)

const busy = ref(false)
const busyText = ref('Loading payroll...')
const error = ref('')
const messages = ref([])
let pollTimer = null

const run = computed(() => overview.value?.run || null)
const rows = computed(() => overview.value?.employees || [])
const readyRows = computed(() => rows.value.filter((r) => r.state === 'ready'))
const visibleRows = computed(() =>
  showBlocked.value ? rows.value : rows.value.filter((r) => r.state !== 'blocked'),
)
const hasBlocker = computed(() => (overview.value?.checks || []).some((c) => c.level === 'blocker'))

const slipRows = computed(() =>
  rows.value.filter((r) => r.slip && (!run.value || r.slip.payroll_entry === run.value.name)),
)
const totals = computed(() =>
  slipRows.value.reduce(
    (t, r) => ({
      gross: t.gross + (r.slip.gross_pay || 0),
      deduction: t.deduction + (r.slip.total_deduction || 0),
      net: t.net + (r.slip.net_pay || 0),
    }),
    { gross: 0, deduction: 0, net: 0 },
  ),
)

// Where the run stands, read from the Payroll Entry rather than remembered client side,
// so a reload (or another user's work) always shows the true step.
const stage = computed(() => {
  const r = run.value
  if (!r) return 'select'
  if (r.status === 'Queued') return 'queued'
  if (r.docstatus === 0 || !r.salary_slips_created) return 'create'
  if (r.draft_slips > 0) return 'review'
  if (r.submitted_slips > 0) return 'done'
  return 'create'
})
const stepIndex = computed(() => ({ select: 0, create: 1, queued: 1, review: 2, done: 3 })[stage.value])

function rowSelected(row) {
  if (stage.value === 'select') return selected.value.has(row.employee)
  return !!run.value?.employees.includes(row.employee)
}

function toggle(emp, on) {
  const next = new Set(selected.value)
  on ? next.add(emp) : next.delete(emp)
  selected.value = next
}

function toggleAll(on) {
  selected.value = on ? new Set(readyRows.value.map((r) => r.employee)) : new Set()
}

const money = (v) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: overview.value?.currency || 'INR', maximumFractionDigits: 2 }).format(v || 0)

function fmtDate(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}-${m}-${y}`
}

function statusClass(status) {
  switch (status) {
    case 'Submitted':
      return 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
    case 'Draft':
      return 'bg-[var(--color-info)]/15 text-[var(--color-info)]'
    case 'Failed':
    case 'Cancelled':
      return 'bg-rose-500/15 text-rose-500'
    case 'Queued':
      return 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'
    default:
      return 'bg-[var(--color-midlight)] text-[var(--color-text)]'
  }
}

function deskLink(code) {
  const c = encodeURIComponent(overview.value?.company || '')
  return {
    'payroll-settings': '/app/payroll-settings',
    company: `/app/company/${c}`,
    'holiday-list': '/app/holiday-list',
    'holiday-list-assignment': '/app/holiday-list-assignment',
    'salary-component': '/app/salary-component',
    'salary-structure-assignment': '/app/salary-structure-assignment',
  }[code]
}

function slipPrintUrl(name) {
  return `/printview?doctype=${encodeURIComponent('Salary Slip')}&name=${encodeURIComponent(name)}`
}

function schedulePoll() {
  clearTimeout(pollTimer)
  if (run.value?.status === 'Queued') pollTimer = setTimeout(() => load({ quiet: true }), 4000)
}

async function load({ quiet = false } = {}) {
  if (!quiet) {
    busy.value = true
    busyText.value = 'Loading payroll...'
  }
  error.value = ''
  try {
    const data = await fetchPayrollOverview({ month: month.value, company: company.value || null })
    overview.value = data
    companies.value = data.companies
    company.value = data.company
    selected.value = new Set(data.employees.filter((r) => r.state === 'ready').map((r) => r.employee))
    if (data.run) postingDate.value = data.run.posting_date
    else postingDate.value = lastDayOf(month.value)
    schedulePoll()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}

// Runs one payroll step, shows what hrms said, then re-reads the month. hrms reports
// most failures on the Payroll Entry rather than as an error, so the reload is what
// tells the user whether the step really worked.
async function step(text, fn) {
  busy.value = true
  busyText.value = text
  error.value = ''
  messages.value = []
  try {
    const res = await fn()
    messages.value = res?.messages || []
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    busy.value = false
  }
  await load()
}

function startRun() {
  return step('Creating payroll run...', () =>
    createPayrollRun({
      month: month.value,
      company: company.value,
      employees: [...selected.value],
      postingDate: postingDate.value,
    }),
  )
}

function createSlips() {
  return step('Creating salary slips...', () => createPayrollSalarySlips(run.value.name))
}

function submitSlips() {
  const n = run.value.draft_slips
  if (!confirm(`Submit ${n} salary slip(s)? This books the salary journal entry.`)) return
  return step('Submitting salary slips...', () => submitPayrollSalarySlips(run.value.name))
}

function discardRun() {
  const r = run.value
  const msg =
    r.docstatus === 0
      ? `Discard draft payroll run ${r.name}?`
      : r.submitted_slips
        ? `Cancel ${r.name}? Its ${r.submitted_slips} submitted salary slip(s) will be cancelled and deleted, and the salary journal entry cancelled.`
        : `Cancel ${r.name}? Its draft salary slips will be deleted.`
  if (!confirm(msg)) return
  return step('Cancelling payroll run...', () => cancelPayrollRun(r.name))
}

onMounted(load)
onBeforeUnmount(() => clearTimeout(pollTimer))
</script>
