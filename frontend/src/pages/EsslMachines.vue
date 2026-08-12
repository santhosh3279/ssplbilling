<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="machines" />

    <!-- ===================== MAIN LIST PANEL ===================== -->
    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            eSSL Machines
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Attendance devices registered in eSSL Machines Attendance
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
            {{ filteredMachines.length }} / {{ machinesList.length }}
          </span>
          <button
            @click="loadMachines"
            :disabled="loading"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] px-5 py-3 font-bold hover:bg-[var(--color-midlight)] active:scale-95 transition-all duration-200 disabled:opacity-50"
          >
            <span>🔄</span> Refresh
          </button>
          <button
            @click="openCreator"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-employee)]/40 bg-[var(--color-employee)]/10 text-[var(--color-employee)] px-5 py-3 font-bold hover:bg-[var(--color-employee)]/20 active:scale-95 transition-all duration-200"
          >
            <span>➕</span> Add Machine
          </button>
          <button
            @click="syncAttendance"
            :disabled="syncing || loading"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15 disabled:opacity-50"
          >
            <span>{{ syncing ? '⏳' : '⬇️' }}</span>
            {{ syncing ? 'Syncing...' : 'Sync Attendance' }}
          </button>
        </div>
      </header>

      <!-- Search & Filters Bar -->
      <div class="bg-[var(--color-surface)] px-8 py-4 border-b border-[var(--color-border)] flex flex-col md:flex-row items-center gap-4 shrink-0 shadow-sm">
        <div class="relative w-full max-w-md group">
          <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-[var(--color-text-muted)]">
            🔍
          </span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by IP, serial number or store..."
            class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-employee)] focus:ring-2 focus:ring-[var(--color-employee)]/15 transition-all duration-200"
          />
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Logs from:</span>
          <input
            v-model="fromDate"
            type="date"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
          />
        </div>

        <div class="flex items-center gap-2 self-stretch md:self-auto ml-auto">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Store:</span>
          <select
            v-model="storeFilter"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
          >
            <option value="All">All Stores</option>
            <option v-for="store in storeOptions" :key="store" :value="store">
              {{ store }}
            </option>
          </select>
        </div>
      </div>

      <!-- Machine list -->
      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="loading" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">Loading machines...</p>
        </div>

        <div
          v-if="error"
          class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500"
        >
          {{ error }}
        </div>

        <!-- Attendance sync summary (cached in localStorage, nothing stored server-side) -->
        <div
          v-if="lastSync"
          class="mb-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-md overflow-hidden"
        >
          <div class="flex flex-wrap items-center gap-4 px-6 py-4 border-b border-[var(--color-border)]">
            <span class="text-sm font-black uppercase tracking-wider text-[var(--color-text)]">
              Attendance Cache
            </span>
            <span class="text-xs font-bold text-[var(--color-text-muted)]">
              Last sync: {{ formatDate(lastSync.syncedAt) }}
            </span>
            <span class="text-xs font-bold text-[var(--color-employee)]">
              {{ lastSync.stored }} of {{ lastSync.total }} logs cached locally
            </span>
            <span v-if="lastSync.fromDate" class="text-xs font-bold text-[var(--color-text-muted)]">
              From {{ lastSync.fromDate }}
            </span>
            <button
              @click="clearAttendanceCache"
              class="ml-auto rounded-xl border border-[var(--color-border)] px-3 py-1.5 text-xs font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] transition-colors"
            >
              Clear cache
            </button>
          </div>

          <div
            v-if="cacheError"
            class="px-6 py-3 text-xs font-bold text-amber-500 bg-amber-500/10 border-b border-[var(--color-border)]"
          >
            {{ cacheError }}
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
              {{ m.store || m.machine }} · {{ m.ip_address }} —
              {{ m.error ? m.error : m.logs + ' logs' }}
            </div>
          </div>
        </div>

        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-2xl border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">IP Address</th>
                  <th class="px-6 py-4">Serial Number</th>
                  <th class="px-6 py-4">Comm Key</th>
                  <th class="px-6 py-4">Store</th>
                  <th class="px-6 py-4">Last Updated</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <!-- name === ip_address (autoname is field:ip_address), so no separate ID column -->
                <tr
                  v-for="machine in filteredMachines"
                  :key="machine.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="px-6 py-4 font-mono font-bold text-[var(--color-employee)]">
                    {{ machine.ip_address || '—' }}
                  </td>
                  <td class="px-6 py-4 font-mono">
                    {{ machine.serial_number || '—' }}
                  </td>
                  <td class="px-6 py-4 font-mono">
                    {{ machine.comm_key || '—' }}
                  </td>
                  <td class="px-6 py-4 font-bold">
                    {{ machine.store || '—' }}
                  </td>
                  <td class="px-6 py-4 font-mono text-xs text-[var(--color-text-muted)]">
                    {{ formatDate(machine.modified) }}
                  </td>
                  <td class="px-6 py-4 text-right whitespace-nowrap">
                    <button
                      @click="openEditor(machine)"
                      class="rounded-xl border border-[var(--color-border)] px-3 py-1.5 text-xs font-bold hover:bg-[var(--color-midlight)] transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      @click="removeMachine(machine)"
                      class="ml-2 rounded-xl border border-rose-500/30 text-rose-500 px-3 py-1.5 text-xs font-bold hover:bg-rose-500/10 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredMachines.length === 0 && !loading">
                  <td colspan="6" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No eSSL machines matching the filters were found.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Add machine modal -->
    <div
      v-if="showCreator"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      @click.self="showCreator = false"
    >
      <div class="w-[520px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-[var(--color-border)] text-lg font-black uppercase tracking-wider">
          {{ newMachine.name ? 'Edit eSSL Machine' : 'New eSSL Machine' }}
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              IP Address <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="newMachine.ip_address"
              type="text"
              placeholder="192.168.1.201"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold font-mono focus:outline-none focus:border-[var(--color-employee)]"
              @keyup.enter="saveMachine"
            />
            <p class="mt-1 text-[11px] text-[var(--color-text-muted)]">
              Doubles as the record id, so it has to be unique. Changing it on an existing
              machine renames the record and repoints its employee mappings.
            </p>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Store</label>
            <input
              v-model="newMachine.store"
              type="text"
              placeholder="NCK SHOP"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              @keyup.enter="saveMachine"
            />
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Comm Key</label>
            <input
              v-model="newMachine.comm_key"
              type="text"
              placeholder="0"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold font-mono focus:outline-none focus:border-[var(--color-employee)]"
              @keyup.enter="saveMachine"
            />
            <p class="mt-1 text-[11px] text-[var(--color-text-muted)]">
              The device password. Leave blank when the device has none.
            </p>
          </div>

          <div>
            <div class="flex items-center justify-between">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Serial Number</label>
              <button
                @click="fetchFromDevice"
                :disabled="!newMachine.ip_address || probing"
                class="rounded-xl border border-[var(--color-border)] px-3 py-1 text-[11px] font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50 transition-colors"
              >
                {{ probing ? 'Reading device...' : 'Read from device' }}
              </button>
            </div>
            <input
              v-model="newMachine.serial_number"
              type="text"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold font-mono focus:outline-none focus:border-[var(--color-employee)]"
              @keyup.enter="saveMachine"
            />
            <p v-if="probing" class="mt-1 text-[11px] text-[var(--color-text-muted)]">
              Reading serial number and clock from the device...
            </p>
            <p v-else-if="!newMachine.serial_number" class="mt-1 text-[11px] text-[var(--color-text-muted)]">
              Left blank it is pulled from the device automatically when this dialog opens.
            </p>
          </div>

          <!-- Device clock: read on probe, corrected against this computer's clock -->
          <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Machine Time
                </div>
                <div class="mt-1 text-sm font-mono font-bold text-[var(--color-text)]">
                  {{ deviceTime ? formatDate(deviceTime) : '—' }}
                </div>
                <div class="text-[11px] font-bold" :class="driftClass">
                  {{ driftLabel }}
                </div>
              </div>
              <button
                @click="correctMachineTime"
                :disabled="!newMachine.ip_address || probing || settingTime"
                class="rounded-xl border border-[var(--color-employee)]/40 bg-[var(--color-employee)]/10 text-[var(--color-employee)] px-4 py-2 text-xs font-bold hover:bg-[var(--color-employee)]/20 disabled:opacity-50 transition-colors"
              >
                {{ settingTime ? 'Setting...' : 'Set to computer time' }}
              </button>
            </div>
            <p class="mt-2 text-[11px] text-[var(--color-text-muted)]">
              This computer: <span class="font-mono">{{ formatDate(computerTime) }}</span>
            </p>
          </div>

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
            @click="saveMachine"
            :disabled="!newMachine.ip_address || saving"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : newMachine.name ? 'Save' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import {
  fetchEsslMachines,
  saveEsslMachine,
  updateEsslMachine,
  deleteEsslMachine,
  syncEsslAttendance,
  fetchEsslMachineInfo,
  setEsslMachineTime,
} from '../api.js'

// Attendance logs live only in localStorage — the sync writes nothing server-side.
const ATTENDANCE_KEY = 'wb-essl-attendance-v1'
// ~90 bytes per log, so 5000 is roughly 450 KB — well inside the 5 MB origin quota
// even alongside the item/customer caches.
const MAX_STORED_LOGS = 5000

const loading = ref(false)
const error = ref('')
const machinesList = ref([])

const syncing = ref(false)
const cacheError = ref('')
const lastSync = ref(null)

const searchQuery = ref('')
const storeFilter = ref('All')
const fromDate = ref(defaultFromDate())

const showCreator = ref(false)
const saving = ref(false)
const creatorError = ref('')
const newMachine = ref({ name: '', ip_address: '', store: '', comm_key: '', serial_number: '' })

const probing = ref(false)
const settingTime = ref(false)
const deviceTime = ref('')
// Computer clock at the instant the device clock was read — drift is measured
// against that snapshot, not against the ticking clock.
const deviceReadAt = ref('')
const computerTime = ref(localTimestamp())
let clockTimer = null

// Local wall-clock "YYYY-MM-DD HH:MM:SS". Deliberately not toISOString(), which is
// UTC and would set every device 5:30 off on IST.
function localTimestamp(d = new Date()) {
  const p = (n) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ` +
    `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  )
}

function parseLocal(str) {
  if (!str) return null
  const d = new Date(String(str).replace(' ', 'T'))
  return isNaN(d.getTime()) ? null : d
}

const driftSeconds = computed(() => {
  const dev = parseLocal(deviceTime.value)
  const pc = parseLocal(deviceReadAt.value)
  if (!dev || !pc) return null
  return Math.round((dev.getTime() - pc.getTime()) / 1000)
})

const driftLabel = computed(() => {
  const drift = driftSeconds.value
  if (drift === null) return deviceTime.value ? '' : 'Not read yet'
  const abs = Math.abs(drift)
  if (abs <= 60) return `In sync (${abs}s off)`
  const mins = Math.round(abs / 60)
  const span = mins >= 120 ? `${Math.round(mins / 60)}h` : `${mins}m`
  return drift > 0 ? `Device ${span} ahead of this computer` : `Device ${span} behind this computer`
})

const driftClass = computed(() => {
  const drift = driftSeconds.value
  if (drift === null) return 'text-[var(--color-text-muted)]'
  return Math.abs(drift) <= 60 ? 'text-emerald-500' : 'text-amber-500'
})

async function loadMachines() {
  loading.value = true
  error.value = ''
  try {
    const list = await fetchEsslMachines()
    machinesList.value = list || []
  } catch (err) {
    console.error('Failed to load eSSL machines:', err)
    error.value = err.message || 'Failed to load eSSL machines.'
    machinesList.value = []
  } finally {
    loading.value = false
  }
}

const storeOptions = computed(() => {
  const stores = machinesList.value.map((m) => (m.store || '').trim()).filter(Boolean)
  return [...new Set(stores)].sort()
})

const filteredMachines = computed(() => {
  let list = machinesList.value

  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter((machine) => {
      const ipMatch = (machine.ip_address || '').toLowerCase().includes(query)
      const serialMatch = (machine.serial_number || '').toLowerCase().includes(query)
      const storeMatch = (machine.store || '').toLowerCase().includes(query)
      return ipMatch || serialMatch || storeMatch
    })
  }

  if (storeFilter.value !== 'All') {
    list = list.filter((machine) => (machine.store || '').trim() === storeFilter.value)
  }

  return list
})

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const [datePart, timePart] = String(dateStr).split(' ')
  const parts = (datePart || '').split('-')
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}${timePart ? ' ' + timePart.slice(0, 5) : ''}` // dd-mm-yyyy hh:mm
  }
  return dateStr
}

function defaultFromDate() {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return d.toISOString().slice(0, 10)
}

function loadCachedSync() {
  try {
    const raw = localStorage.getItem(ATTENDANCE_KEY)
    if (!raw) return
    const cached = JSON.parse(raw)
    lastSync.value = {
      syncedAt: cached.syncedAt,
      fromDate: cached.fromDate,
      total: cached.total,
      stored: (cached.logs || []).length,
      machines: cached.machines || [],
    }
  } catch {
    localStorage.removeItem(ATTENDANCE_KEY)
  }
}

async function syncAttendance() {
  syncing.value = true
  error.value = ''
  cacheError.value = ''
  try {
    const res = await syncEsslAttendance({ fromDate: fromDate.value || null })
    const logs = res?.logs || []
    // Server already sorts newest first; keep only what fits comfortably in localStorage
    const stored = logs.slice(0, MAX_STORED_LOGS)

    const payload = {
      syncedAt: res?.synced_at || '',
      fromDate: res?.from_date || fromDate.value || null,
      total: res?.total ?? logs.length,
      machines: res?.machines || [],
      logs: stored,
    }

    try {
      localStorage.setItem(ATTENDANCE_KEY, JSON.stringify(payload))
      if (payload.total > stored.length) {
        cacheError.value = `Only the newest ${stored.length} of ${payload.total} logs were cached. Narrow the date range to keep fewer.`
      }
    } catch (quotaErr) {
      // Quota blown — keep the summary so the sync result is still visible
      console.error('Could not cache attendance logs:', quotaErr)
      localStorage.setItem(ATTENDANCE_KEY, JSON.stringify({ ...payload, logs: [] }))
      payload.logs = []
      cacheError.value = 'Too many logs to cache locally — narrow the date range and sync again.'
    }

    lastSync.value = {
      syncedAt: payload.syncedAt,
      fromDate: payload.fromDate,
      total: payload.total,
      stored: payload.logs.length,
      machines: payload.machines,
    }
  } catch (err) {
    console.error('Attendance sync failed:', err)
    error.value = err.message || 'Attendance sync failed.'
  } finally {
    syncing.value = false
  }
}

function resetDeviceProbe() {
  deviceTime.value = ''
  deviceReadAt.value = ''
  probing.value = false
  settingTime.value = false
}

function openCreator() {
  newMachine.value = { name: '', ip_address: '', store: '', comm_key: '', serial_number: '' }
  creatorError.value = ''
  resetDeviceProbe()
  showCreator.value = true
}

function openEditor(machine) {
  newMachine.value = {
    name: machine.name,
    ip_address: machine.ip_address || '',
    store: machine.store || '',
    comm_key: machine.comm_key || '',
    serial_number: machine.serial_number || '',
  }
  creatorError.value = ''
  resetDeviceProbe()
  showCreator.value = true

  // Serial missing — pull it off the device. Fire and forget so the 10s connect
  // timeout never blocks the modal from opening.
  if (!newMachine.value.serial_number && newMachine.value.ip_address) {
    fetchFromDevice()
  }
}

// Reads serial + clock in one device connection. Uses the form values so it also
// works before the machine is saved.
async function fetchFromDevice() {
  if (!newMachine.value.ip_address || probing.value) return
  probing.value = true
  creatorError.value = ''
  const askedFor = newMachine.value.ip_address
  try {
    const info = await fetchEsslMachineInfo({
      ipAddress: askedFor,
      commKey: newMachine.value.comm_key || null,
    })
    // The user may have moved on to another machine while the connect was pending
    if (!showCreator.value || newMachine.value.ip_address !== askedFor) return
    if (info?.serial_number) newMachine.value.serial_number = info.serial_number
    deviceTime.value = info?.device_time || ''
    deviceReadAt.value = localTimestamp()
  } catch (err) {
    console.error('Failed to read device:', err)
    creatorError.value = err.message || 'Could not reach the device.'
  } finally {
    probing.value = false
  }
}

async function correctMachineTime() {
  if (!newMachine.value.ip_address || settingTime.value) return
  const now = localTimestamp()
  if (!confirm(`Set the clock on ${newMachine.value.ip_address} to ${now}?`)) return
  settingTime.value = true
  creatorError.value = ''
  try {
    const res = await setEsslMachineTime({
      ipAddress: newMachine.value.ip_address,
      commKey: newMachine.value.comm_key || null,
      timestamp: now,
    })
    deviceTime.value = res?.device_time || now
    deviceReadAt.value = localTimestamp()
  } catch (err) {
    console.error('Failed to set device time:', err)
    creatorError.value = err.message || 'Could not set the device time.'
  } finally {
    settingTime.value = false
  }
}

async function removeMachine(machine) {
  const label = machine.store ? `${machine.store} (${machine.ip_address})` : machine.ip_address
  if (!confirm(`Delete machine ${label}?`)) return
  loading.value = true
  error.value = ''
  try {
    await deleteEsslMachine(machine.name)
    await loadMachines()
  } catch (err) {
    console.error('Failed to delete machine:', err)
    error.value = err.message || 'Failed to delete machine.'
  } finally {
    loading.value = false
  }
}

async function saveMachine() {
  if (!newMachine.value.ip_address || saving.value) return
  saving.value = true
  creatorError.value = ''
  try {
    if (newMachine.value.name) {
      await updateEsslMachine(newMachine.value)
    } else {
      await saveEsslMachine(newMachine.value)
    }
    showCreator.value = false
    await loadMachines()
  } catch (err) {
    console.error('Failed to save machine:', err)
    creatorError.value = err.message || 'Failed to save machine.'
  } finally {
    saving.value = false
  }
}

function clearAttendanceCache() {
  localStorage.removeItem(ATTENDANCE_KEY)
  lastSync.value = null
  cacheError.value = ''
}

onMounted(() => {
  loadMachines()
  loadCachedSync()
  clockTimer = setInterval(() => {
    computerTime.value = localTimestamp()
  }, 1000)
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
})
</script>
