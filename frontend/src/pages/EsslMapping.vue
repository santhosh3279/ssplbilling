<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="mapping" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Employee Mapping
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Links each eSSL device user id to an Employee. Only mapped users get attendance.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
            {{ mappings.length }} mapped
          </span>
          <button
            @click="loadDeviceUsers"
            :disabled="busy"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-3 font-bold hover:bg-[var(--color-midlight)] active:scale-95 transition-all duration-200 disabled:opacity-50"
          >
            <span>🖥️</span> Read Device Users
          </button>
          <button
            @click="autoMap"
            :disabled="busy"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-employee)]/40 bg-[var(--color-employee)]/10 text-[var(--color-employee)] px-5 py-3 font-bold hover:bg-[var(--color-employee)]/20 active:scale-95 transition-all duration-200 disabled:opacity-50"
          >
            <span>✨</span> Auto-map by Name
          </button>
          <button
            @click="openEditor(null)"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15"
          >
            <span>➕</span> Add Mapping
          </button>
        </div>
      </header>

      <div class="bg-[var(--color-surface)] px-8 py-4 border-b border-[var(--color-border)] flex items-center gap-4 shrink-0 shadow-sm">
        <div class="relative w-full max-w-md">
          <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-[var(--color-text-muted)]">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by device user id, employee or machine..."
            class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-employee)] focus:ring-2 focus:ring-[var(--color-employee)]/15"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="busy" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">{{ busyLabel }}</p>
        </div>

        <div v-if="error" class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500">
          {{ error }}
        </div>

        <div v-if="notice" class="mb-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-5 py-3 text-sm font-semibold text-emerald-500">
          {{ notice }}
        </div>

        <!-- Unmapped device users -->
        <div v-if="unmappedUsers.length" class="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 shadow-md overflow-hidden">
          <div class="px-6 py-4 border-b border-amber-500/20 text-sm font-black uppercase tracking-wider text-amber-500">
            Unmapped device users ({{ unmappedUsers.length }})
          </div>
          <div class="flex flex-wrap gap-3 px-6 py-4">
            <button
              v-for="user in unmappedUsers"
              :key="user.machine + user.user_id"
              @click="openEditorForUser(user)"
              class="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-500 hover:bg-amber-500/20 transition-colors"
            >
              #{{ user.user_id }} · {{ user.device_name || 'unnamed' }}
            </button>
          </div>
        </div>

        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xl border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Device User ID</th>
                  <th class="px-6 py-4">Employee</th>
                  <th class="px-6 py-4">Employee ID</th>
                  <th class="px-6 py-4">Machine</th>
                  <th class="px-6 py-4">Status</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="row in filteredMappings"
                  :key="row.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="px-6 py-4 font-mono font-bold text-[var(--color-employee)]">#{{ row.machine_user_id }}</td>
                  <td class="px-6 py-4 font-bold">{{ row.employee_name || '—' }}</td>
                  <!-- No text-* override: these read at the table's text-xl, same as Employee -->
                  <td class="px-6 py-4 font-mono">{{ row.employee }}</td>
                  <td class="px-6 py-4">{{ row.machine || 'All machines' }}</td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2.5 py-1 font-black rounded-full uppercase tracking-wider"
                      :class="row.enabled && row.employee_status === 'Active'
                        ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                        : 'bg-[var(--color-text-muted)]/10 text-[var(--color-text-muted)] border border-[var(--color-text-muted)]/20'"
                    >
                      ● {{ row.enabled ? row.employee_status : 'Disabled' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-right whitespace-nowrap">
                    <button
                      @click="openEditor(row)"
                      class="rounded-xl border border-[var(--color-border)] px-3 py-1.5 text-xs font-bold hover:bg-[var(--color-midlight)] transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      @click="removeMapping(row)"
                      class="ml-2 rounded-xl border border-rose-500/30 text-rose-500 px-3 py-1.5 text-xs font-bold hover:bg-rose-500/10 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredMappings.length === 0 && !busy">
                  <td colspan="6" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No mappings yet. Read the device users, then auto-map by name or add them manually.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Editor modal -->
    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      @click.self="showEditor = false"
    >
      <div class="w-[520px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-[var(--color-border)] text-lg font-black uppercase tracking-wider">
          {{ form.name ? 'Edit Mapping' : 'New Mapping' }}
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Device User ID</label>
            <input
              v-model="form.machine_user_id"
              type="text"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Employee</label>
            <select
              v-model="form.employee"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="">— Select employee —</option>
              <option v-for="emp in employees" :key="emp.name" :value="emp.name">
                {{ emp.employee_name }} ({{ emp.name }})
              </option>
            </select>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Machine</label>
            <select
              v-model="form.machine"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="">All machines</option>
              <option v-for="m in machines" :key="m.name" :value="m.name">
                {{ m.store || m.name }} ({{ m.ip_address }})
              </option>
            </select>
          </div>

          <label class="flex items-center gap-2 text-sm font-bold">
            <input v-model="form.enabled" type="checkbox" class="h-4 w-4" />
            Enabled
          </label>
        </div>

        <div class="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-3">
          <button
            @click="showEditor = false"
            class="rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold hover:bg-[var(--color-midlight)]"
          >
            Cancel
          </button>
          <button
            @click="saveMapping"
            :disabled="!form.machine_user_id || !form.employee"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import {
  fetchEsslMappings,
  saveEsslMapping,
  deleteEsslMapping,
  fetchEsslDeviceUsers,
  autoMapEsslUsers,
  fetchEsslMachines,
  fetchEmployees,
} from '../api.js'

const busy = ref(false)
const busyLabel = ref('Loading...')
const error = ref('')
const notice = ref('')

const mappings = ref([])
const employees = ref([])
const machines = ref([])
const deviceUsers = ref([])

const searchQuery = ref('')

const showEditor = ref(false)
const form = ref({ name: '', machine_user_id: '', employee: '', machine: '', enabled: true })

const unmappedUsers = computed(() => deviceUsers.value.filter((u) => !u.employee))

const filteredMappings = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return mappings.value
  return mappings.value.filter((row) =>
    [row.machine_user_id, row.employee, row.employee_name, row.machine]
      .some((v) => (v || '').toLowerCase().includes(query)),
  )
})

async function loadAll() {
  busy.value = true
  busyLabel.value = 'Loading mappings...'
  error.value = ''
  try {
    const [maps, emps, machineList] = await Promise.all([
      fetchEsslMappings(),
      fetchEmployees(''),
      fetchEsslMachines(),
    ])
    mappings.value = maps || []
    employees.value = (emps || []).filter((e) => (e.status || 'Active') === 'Active')
    machines.value = machineList || []
  } catch (err) {
    console.error('Failed to load mappings:', err)
    error.value = err.message || 'Failed to load mappings.'
  } finally {
    busy.value = false
  }
}

async function loadDeviceUsers() {
  busy.value = true
  busyLabel.value = 'Reading users from the devices...'
  error.value = ''
  notice.value = ''
  try {
    const res = await fetchEsslDeviceUsers()
    deviceUsers.value = res?.users || []
    const failed = (res?.machines || []).filter((m) => m.error)
    if (failed.length) {
      error.value = failed.map((m) => `${m.ip_address}: ${m.error}`).join(' · ')
    }
    notice.value = `${deviceUsers.value.length} users read from the devices.`
  } catch (err) {
    console.error('Failed to read device users:', err)
    error.value = err.message || 'Failed to read device users.'
  } finally {
    busy.value = false
  }
}

async function autoMap() {
  busy.value = true
  busyLabel.value = 'Matching device names to employees...'
  error.value = ''
  notice.value = ''
  try {
    const res = await autoMapEsslUsers()
    notice.value = `${res?.created?.length || 0} mapped automatically, ${res?.skipped?.length || 0} left for manual mapping.`
    await loadAll()
    await loadDeviceUsers()
  } catch (err) {
    console.error('Auto-map failed:', err)
    error.value = err.message || 'Auto-map failed.'
  } finally {
    busy.value = false
  }
}

function openEditor(row) {
  form.value = row
    ? {
        name: row.name,
        machine_user_id: row.machine_user_id,
        employee: row.employee,
        machine: row.machine || '',
        enabled: !!row.enabled,
      }
    : { name: '', machine_user_id: '', employee: '', machine: '', enabled: true }
  showEditor.value = true
}

function openEditorForUser(user) {
  form.value = {
    name: '',
    machine_user_id: user.user_id,
    employee: '',
    machine: '',
    enabled: true,
  }
  showEditor.value = true
}

async function saveMapping() {
  busy.value = true
  busyLabel.value = 'Saving...'
  error.value = ''
  try {
    await saveEsslMapping({
      name: form.value.name || undefined,
      machine_user_id: form.value.machine_user_id,
      employee: form.value.employee,
      machine: form.value.machine || null,
      enabled: form.value.enabled ? 1 : 0,
    })
    showEditor.value = false
    await loadAll()
    if (deviceUsers.value.length) await loadDeviceUsers()
  } catch (err) {
    console.error('Failed to save mapping:', err)
    error.value = err.message || 'Failed to save mapping.'
  } finally {
    busy.value = false
  }
}

async function removeMapping(row) {
  if (!confirm(`Delete the mapping for device user #${row.machine_user_id}?`)) return
  busy.value = true
  busyLabel.value = 'Deleting...'
  try {
    await deleteEsslMapping(row.name)
    await loadAll()
  } catch (err) {
    console.error('Failed to delete mapping:', err)
    error.value = err.message || 'Failed to delete mapping.'
  } finally {
    busy.value = false
  }
}

onMounted(loadAll)
</script>
