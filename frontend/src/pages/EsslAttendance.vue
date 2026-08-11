<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="attendance" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Attendance
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Built from eSSL device punches for mapped employees
            <span v-if="settings">
              · auto sync {{ settings.enable_auto_sync ? 'every 10 minutes' : 'disabled' }}
            </span>
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
            {{ records.length }} records
          </span>
          <button
            @click="loadRecords"
            :disabled="busy"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-3 font-bold hover:bg-[var(--color-midlight)] active:scale-95 transition-all duration-200 disabled:opacity-50"
          >
            <span>🔄</span> Refresh
          </button>
          <button
            @click="openCreator"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-employee)]/40 bg-[var(--color-employee)]/10 text-[var(--color-employee)] px-5 py-3 font-bold hover:bg-[var(--color-employee)]/20 active:scale-95 transition-all duration-200"
          >
            <span>➕</span> Add Attendance
          </button>
          <button
            @click="syncNow"
            :disabled="busy"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15 disabled:opacity-50"
          >
            <span>{{ syncing ? '⏳' : '⬇️' }}</span>
            {{ syncing ? 'Syncing...' : 'Sync & Create Attendance' }}
          </button>
        </div>
      </header>

      <div class="bg-[var(--color-surface)] px-8 py-4 border-b border-[var(--color-border)] flex flex-wrap items-center gap-4 shrink-0 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">From</span>
          <input
            v-model="fromDate"
            type="date"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">To</span>
          <input
            v-model="toDate"
            type="date"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
          />
        </div>
        <div class="relative w-full max-w-xs">
          <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-[var(--color-text-muted)]">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search employee..."
            class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
          />
        </div>
        <button
          @click="loadRecords"
          class="rounded-xl border border-[var(--color-border)] px-4 py-2.5 text-xs font-bold hover:bg-[var(--color-midlight)] transition-colors"
        >
          Apply
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="busy" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">{{ busyLabel }}</p>
        </div>

        <div v-if="error" class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500">
          {{ error }}
        </div>

        <!-- Last sync summary -->
        <div v-if="lastSync" class="mb-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-md overflow-hidden">
          <div class="flex flex-wrap items-center gap-4 px-6 py-4 border-b border-[var(--color-border)]">
            <span class="text-sm font-black uppercase tracking-wider">Last sync</span>
            <span class="text-xs font-bold text-[var(--color-text-muted)]">{{ lastSync.synced_at }}</span>
            <span class="text-xs font-bold text-[var(--color-employee)]">
              {{ lastSync.totals.mapped }} of {{ lastSync.totals.logs }} punches mapped ·
              {{ lastSync.totals.attendance_created }} attendance created ·
              {{ lastSync.totals.attendance_updated }} updated ·
              {{ lastSync.totals.checkins_created }} checkins
            </span>
            <span v-if="lastSync.totals.skipped_future" class="text-xs font-bold text-amber-500">
              {{ lastSync.totals.skipped_future }} punches dated in the future were skipped (device clock)
            </span>
          </div>
          <div v-if="lastSync.unmapped_ids.length" class="px-6 py-3 text-xs font-bold text-amber-500 bg-amber-500/10">
            Unmapped device users: {{ lastSync.unmapped_ids.join(', ') }} —
            <button class="underline" @click="router.push('/hrms/essl-mapping')">map them</button>
          </div>
          <div class="flex flex-wrap gap-3 px-6 py-4">
            <div
              v-for="m in lastSync.machines"
              :key="m.machine"
              class="rounded-xl border px-4 py-2 text-xs font-bold"
              :class="m.error
                ? 'border-rose-500/20 bg-rose-500/10 text-rose-500'
                : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-500'"
            >
              {{ m.store || m.machine }} — {{ m.error ? m.error : m.logs + ' punches' }}
            </div>
          </div>
        </div>

        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xl border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Date</th>
                  <th class="px-6 py-4">Employee</th>
                  <th class="px-6 py-4">Status</th>
                  <th class="px-6 py-4">In</th>
                  <th class="px-6 py-4">Out</th>
                  <th class="px-6 py-4">Hours</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="row in filteredRecords"
                  :key="row.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="px-6 py-4 font-mono font-bold text-[var(--color-employee)]">
                    {{ formatDate(row.attendance_date) }}
                  </td>
                  <td class="px-6 py-4 font-bold">{{ row.employee_name || row.employee }}</td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2.5 py-1 text-[10px] font-black rounded-full uppercase tracking-wider"
                      :class="statusClass(row.status)"
                    >
                      ● {{ row.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 font-mono text-sm">{{ formatTime(row.in_time) }}</td>
                  <td class="px-6 py-4 font-mono text-sm">{{ formatTime(row.out_time) }}</td>
                  <td class="px-6 py-4 font-mono text-sm">{{ (row.working_hours || 0).toFixed(2) }}</td>
                </tr>
                <tr v-if="filteredRecords.length === 0 && !busy">
                  <td colspan="6" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No attendance records in this range. Map the device users, then run a sync.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Manual attendance modal -->
    <div
      v-if="showCreator"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      @click.self="showCreator = false"
    >
      <div class="w-[560px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-[var(--color-border)] text-lg font-black uppercase tracking-wider">
          Manual Attendance
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Employee <span class="text-rose-500">*</span>
            </label>
            <select
              v-model="newRecord.employee"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="">— Select employee —</option>
              <option v-for="emp in employees" :key="emp.name" :value="emp.name">
                {{ emp.employee_name }} ({{ emp.name }})
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                Date <span class="text-rose-500">*</span>
              </label>
              <input
                v-model="newRecord.attendance_date"
                type="date"
                :max="today"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              />
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Status</label>
              <select
                v-model="newRecord.status"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              >
                <option>Present</option>
                <option>Absent</option>
                <option>Half Day</option>
                <option>On Leave</option>
                <option>Work From Home</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">In Time</label>
              <input
                v-model="newRecord.in_time"
                type="time"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              />
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Out Time</label>
              <input
                v-model="newRecord.out_time"
                type="time"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              />
            </div>
          </div>
          <p class="text-[11px] text-[var(--color-text-muted)]">
            Times are optional — worked hours are computed from them. The record is submitted
            straight away, and a day that already has attendance is refused.
          </p>

          <div v-if="creatorError" class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-2.5 text-xs font-bold text-rose-500">
            {{ creatorError }}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-3">
          <button
            @click="showCreator = false"
            class="rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold hover:bg-[var(--color-midlight)]"
          >
            Cancel
          </button>
          <button
            @click="saveManualAttendance"
            :disabled="!newRecord.employee || !newRecord.attendance_date || saving"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import {
  fetchAttendanceRecords,
  syncEsslAttendanceToErp,
  fetchEsslSyncSettings,
  createManualAttendance,
  fetchEmployees,
} from '../api.js'

const router = useRouter()

const busy = ref(false)
const busyLabel = ref('Loading...')
const syncing = ref(false)
const error = ref('')

const records = ref([])
const settings = ref(null)
const lastSync = ref(null)
const searchQuery = ref('')

const fromDate = ref(daysAgo(30))
const toDate = ref(daysAgo(0))

const employees = ref([])
const showCreator = ref(false)
const saving = ref(false)
const creatorError = ref('')
const today = daysAgo(0)
const newRecord = ref({
  employee: '',
  attendance_date: today,
  status: 'Present',
  in_time: '',
  out_time: '',
})

function daysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

const filteredRecords = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return records.value
  return records.value.filter((row) =>
    [row.employee, row.employee_name].some((v) => (v || '').toLowerCase().includes(query)),
  )
})

async function loadRecords() {
  busy.value = true
  busyLabel.value = 'Loading attendance...'
  error.value = ''
  try {
    records.value = (await fetchAttendanceRecords({
      fromDate: fromDate.value || null,
      toDate: toDate.value || null,
    })) || []
  } catch (err) {
    console.error('Failed to load attendance:', err)
    error.value = err.message || 'Failed to load attendance.'
    records.value = []
  } finally {
    busy.value = false
  }
}

async function syncNow() {
  syncing.value = true
  busy.value = true
  busyLabel.value = 'Pulling devices and creating attendance...'
  error.value = ''
  try {
    // No from_date: each machine resumes from its own last_sync watermark
    lastSync.value = await syncEsslAttendanceToErp({})
    const failed = (lastSync.value?.machines || []).filter((m) => m.error)
    if (failed.length) {
      error.value = failed.map((m) => `${m.ip_address || m.machine}: ${m.error}`).join(' · ')
    }
    await loadRecords()
  } catch (err) {
    console.error('Sync failed:', err)
    error.value = err.message || 'Sync failed.'
  } finally {
    syncing.value = false
    busy.value = false
  }
}

async function openCreator() {
  newRecord.value = {
    employee: '',
    attendance_date: today,
    status: 'Present',
    in_time: '',
    out_time: '',
  }
  creatorError.value = ''
  showCreator.value = true
  if (!employees.value.length) {
    try {
      const list = await fetchEmployees('')
      employees.value = (list || []).filter((e) => (e.status || 'Active') === 'Active')
    } catch (err) {
      console.error('Failed to load employees:', err)
      creatorError.value = err.message || 'Failed to load the employee list.'
    }
  }
}

async function saveManualAttendance() {
  if (saving.value) return
  saving.value = true
  creatorError.value = ''
  try {
    await createManualAttendance(newRecord.value)
    showCreator.value = false
    await loadRecords()
  } catch (err) {
    console.error('Failed to create attendance:', err)
    creatorError.value = err.message || 'Failed to create attendance.'
  } finally {
    saving.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const parts = String(dateStr).split('-')
  return parts.length === 3 ? `${parts[2]}-${parts[1]}-${parts[0]}` : dateStr
}

function formatTime(stamp) {
  if (!stamp) return '—'
  const timePart = String(stamp).split(' ')[1] || ''
  return timePart.slice(0, 5) || '—'
}

function statusClass(status) {
  if (status === 'Present') return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
  if (status === 'Half Day') return 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
  if (status === 'Absent') return 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
  return 'bg-[var(--color-text-muted)]/10 text-[var(--color-text-muted)] border border-[var(--color-text-muted)]/20'
}

onMounted(async () => {
  loadRecords()
  try {
    settings.value = await fetchEsslSyncSettings()
  } catch {
    settings.value = null
  }
})
</script>
