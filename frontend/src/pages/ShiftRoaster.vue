<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="roaster" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Shift Roaster
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Shift Assignments — which employee works which shift, and from when
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
            {{ filteredRows.length }} / {{ rows.length }}
          </span>
          <button
            @click="loadRows"
            :disabled="busy"
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-3 font-bold hover:bg-[var(--color-midlight)] active:scale-95 transition-all duration-200 disabled:opacity-50"
          >
            <span>🔄</span> Refresh
          </button>
          <button
            @click="openEditor(null)"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15"
          >
            <span>➕</span> Assign Shift
          </button>
        </div>
      </header>

      <!-- Filters -->
      <div class="bg-[var(--color-surface)] px-8 py-4 border-b border-[var(--color-border)] flex flex-wrap items-center gap-4 shrink-0 shadow-sm">
        <div class="relative w-full max-w-xs">
          <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-[var(--color-text-muted)]">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search employee or shift..."
            class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-employee)] focus:ring-2 focus:ring-[var(--color-employee)]/15"
          />
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Shift</span>
          <select
            v-model="shiftFilter"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)]"
          >
            <option value="All">All shifts</option>
            <option v-for="s in shiftTypes" :key="s.name" :value="s.name">{{ s.name }}</option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Status</span>
          <select
            v-model="statusFilter"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)]"
          >
            <option value="All">All</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
          </select>
        </div>

        <label class="flex items-center gap-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
          <input v-model="currentOnly" type="checkbox" class="accent-[var(--color-employee)]" />
          Running today only
        </label>
      </div>

      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="busy" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">{{ busyLabel }}</p>
        </div>

        <div v-if="error" class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500">
          {{ error }}
        </div>

        <div
          v-if="!shiftTypes.length && !busy"
          class="mb-4 rounded-xl border border-amber-500/20 bg-amber-500/10 px-5 py-3 text-sm font-semibold text-amber-500"
        >
          No Shift Type exists yet. Create one in the desk (HR → Shift Type) before assigning shifts.
        </div>

        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xl border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">Employee</th>
                  <th class="px-6 py-4">Shift</th>
                  <th class="px-6 py-4">Timing</th>
                  <th class="px-6 py-4">From</th>
                  <th class="px-6 py-4">To</th>
                  <th class="px-6 py-4">Status</th>
                  <th class="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="row in filteredRows"
                  :key="row.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="px-6 py-4 font-bold">
                    {{ row.employee_name || row.employee }}
                    <div class="text-xs font-mono text-[var(--color-text-muted)]">{{ row.employee }}</div>
                  </td>
                  <td class="px-6 py-4 font-bold text-[var(--color-employee)]">{{ row.shift_type }}</td>
                  <td class="px-6 py-4 font-mono text-sm text-[var(--color-text-muted)]">
                    {{ shiftTiming(row.shift_type) }}
                  </td>
                  <td class="px-6 py-4 font-mono text-sm">{{ formatDate(row.start_date) }}</td>
                  <td class="px-6 py-4 font-mono text-sm">
                    {{ row.end_date ? formatDate(row.end_date) : 'Open ended' }}
                  </td>
                  <td class="px-6 py-4">
                    <span
                      class="rounded-xl border px-3 py-1 text-xs font-bold"
                      :class="row.status === 'Active' && row.docstatus === 1
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
                        : 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'"
                    >
                      {{ row.docstatus === 0 ? 'Draft' : row.status }}
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
                      @click="removeRow(row)"
                      class="ml-2 rounded-xl border border-rose-500/30 text-rose-500 px-3 py-1.5 text-xs font-bold hover:bg-rose-500/10 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
                <tr v-if="filteredRows.length === 0 && !busy">
                  <td colspan="7" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No shift assignments matching the filters.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- Assign / edit modal -->
    <div
      v-if="showEditor"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      @click.self="showEditor = false"
    >
      <div class="w-[520px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
        <div class="px-6 py-4 border-b border-[var(--color-border)] text-lg font-black uppercase tracking-wider">
          {{ draft.name ? 'Edit Shift Assignment' : 'Assign Shift' }}
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Employee <span class="text-rose-500">*</span>
            </label>
            <select
              v-model="draft.employee"
              :disabled="locked"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)] disabled:opacity-60"
            >
              <option value="">Select employee...</option>
              <option v-for="e in employees" :key="e.name" :value="e.name">
                {{ e.employee_name }} ({{ e.name }})
              </option>
            </select>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Shift Type <span class="text-rose-500">*</span>
            </label>
            <select
              v-model="draft.shift_type"
              :disabled="locked"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)] disabled:opacity-60"
            >
              <option value="">Select shift...</option>
              <option v-for="s in shiftTypes" :key="s.name" :value="s.name">
                {{ s.name }}{{ s.start_time ? ` · ${trimTime(s.start_time)}–${trimTime(s.end_time)}` : '' }}
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                From <span class="text-rose-500">*</span>
              </label>
              <input
                v-model="draft.start_date"
                type="date"
                :disabled="locked"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)] disabled:opacity-60"
              />
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
              <input
                v-model="draft.end_date"
                type="date"
                class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)]"
              />
              <p class="mt-1 text-[11px] text-[var(--color-text-muted)]">Blank means open ended.</p>
            </div>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Status</label>
            <select
              v-model="draft.status"
              class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>

          <p v-if="locked" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-[11px] text-[var(--color-text-muted)]">
            This assignment is submitted, so only the end date and status can change. To move it to
            another employee, shift or start date, delete it and add a new one.
          </p>

          <div v-if="editorError" class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-2.5 text-xs font-bold text-rose-500">
            {{ editorError }}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-3">
          <button
            @click="showEditor = false"
            class="rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold hover:bg-[var(--color-midlight)]"
          >
            Cancel
          </button>
          <button
            @click="saveRow"
            :disabled="saving || !draft.employee || !draft.shift_type || !draft.start_date"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : draft.name ? 'Save' : 'Assign' }}
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
  fetchShiftTypes,
  fetchShiftAssignments,
  saveShiftAssignment,
  deleteShiftAssignment,
  fetchEmployees,
} from '../api.js'

const busy = ref(false)
const busyLabel = ref('Loading roaster...')
const error = ref('')

const rows = ref([])
const shiftTypes = ref([])
const employees = ref([])

const searchQuery = ref('')
const shiftFilter = ref('All')
const statusFilter = ref('All')
const currentOnly = ref(false)

const showEditor = ref(false)
const saving = ref(false)
const editorError = ref('')
const draft = ref(emptyDraft())

// hrms marks only end_date and status allow_on_submit, so a submitted row keeps the
// rest of its fields frozen — the modal mirrors that instead of failing on save.
const locked = computed(() => draft.value.name && draft.value.docstatus === 1)

function emptyDraft() {
  return {
    name: '',
    docstatus: 0,
    employee: '',
    shift_type: '',
    start_date: today(),
    end_date: '',
    status: 'Active',
  }
}

function today() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const parts = String(dateStr).split('-')
  return parts.length === 3 ? `${parts[2]}-${parts[1]}-${parts[0]}` : dateStr
}

function trimTime(value) {
  // "9:30:00" / "09:30:00" → "09:30"
  if (!value) return ''
  const [h, m] = String(value).split(':')
  return `${String(h).padStart(2, '0')}:${m || '00'}`
}

function shiftTiming(shiftName) {
  const shift = shiftTypes.value.find((s) => s.name === shiftName)
  if (!shift || !shift.start_time) return '—'
  return `${trimTime(shift.start_time)} – ${trimTime(shift.end_time)}`
}

const filteredRows = computed(() => {
  let list = rows.value

  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter(
      (r) =>
        (r.employee_name || '').toLowerCase().includes(query) ||
        (r.employee || '').toLowerCase().includes(query) ||
        (r.shift_type || '').toLowerCase().includes(query)
    )
  }

  if (shiftFilter.value !== 'All') {
    list = list.filter((r) => r.shift_type === shiftFilter.value)
  }

  if (statusFilter.value !== 'All') {
    list = list.filter((r) => r.status === statusFilter.value)
  }

  if (currentOnly.value) {
    const now = today()
    list = list.filter((r) => r.start_date <= now && (!r.end_date || r.end_date >= now))
  }

  return list
})

async function loadRows() {
  busy.value = true
  busyLabel.value = 'Loading roaster...'
  error.value = ''
  try {
    const [assignments, types] = await Promise.all([fetchShiftAssignments({}), fetchShiftTypes()])
    rows.value = assignments || []
    shiftTypes.value = types || []
  } catch (err) {
    console.error('Failed to load the roaster:', err)
    error.value = err.message || 'Failed to load the roaster.'
    rows.value = []
  } finally {
    busy.value = false
  }
}

async function loadEmployees() {
  if (employees.value.length) return
  try {
    const list = await fetchEmployees('')
    employees.value = (list || []).filter((e) => (e.status || 'Active') === 'Active')
  } catch (err) {
    console.error('Failed to load employees:', err)
    editorError.value = err.message || 'Failed to load the employee list.'
  }
}

function openEditor(row) {
  editorError.value = ''
  draft.value = row
    ? {
        name: row.name,
        docstatus: row.docstatus,
        employee: row.employee,
        shift_type: row.shift_type,
        start_date: row.start_date || today(),
        end_date: row.end_date || '',
        status: row.status || 'Active',
      }
    : emptyDraft()
  showEditor.value = true
  loadEmployees()
}

async function saveRow() {
  if (saving.value) return
  saving.value = true
  editorError.value = ''
  try {
    await saveShiftAssignment({
      name: draft.value.name || null,
      employee: draft.value.employee,
      shift_type: draft.value.shift_type,
      start_date: draft.value.start_date,
      end_date: draft.value.end_date || null,
      status: draft.value.status,
    })
    showEditor.value = false
    await loadRows()
  } catch (err) {
    console.error('Failed to save the assignment:', err)
    editorError.value = err.message || 'Failed to save the assignment.'
  } finally {
    saving.value = false
  }
}

async function removeRow(row) {
  const label = `${row.employee_name || row.employee} · ${row.shift_type} from ${formatDate(row.start_date)}`
  if (!confirm(`Delete the shift assignment ${label}?`)) return
  busy.value = true
  busyLabel.value = 'Deleting...'
  error.value = ''
  try {
    await deleteShiftAssignment(row.name)
    await loadRows()
  } catch (err) {
    console.error('Failed to delete the assignment:', err)
    error.value = err.message || 'Failed to delete the assignment.'
  } finally {
    busy.value = false
  }
}

onMounted(loadRows)
</script>
