<template>
  <div v-if="show" class="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="$emit('close')">

    <!-- Panel 70vw × 70vh centred -->
    <div class="flex flex-col bg-slate-900 shadow-2xl border border-slate-700 rounded-xl overflow-hidden" style="width:70vw;height:70vh" @keydown.end.prevent="handleSave" @click.stop>

      <!-- HEADER -->
      <header class="flex h-11 shrink-0 items-center justify-between border-b border-slate-700 bg-slate-800 px-4">
        <div class="flex items-center gap-3">
          <button
            @click="$emit('close')"
            class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition"
          >&larr; Close</button>
          <span class="text-sm text-slate-600">|</span>
          <span class="text-sm font-semibold text-slate-200">Incentive Entries</span>
          <span v-if="docname" class="font-mono text-xs text-blue-400">{{ docname }}</span>
        </div>
        <div class="flex items-center gap-3 text-xs text-slate-400">
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Tab</kbd> Next field</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Up/Down</kbd> Navigate</span>
          <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Del</kbd> Remove row</span>
          <span v-if="saved" class="rounded-full bg-emerald-500/20 px-3 py-0.5 font-bold uppercase tracking-widest text-emerald-400">Saved</span>
        </div>
      </header>

      <!-- TABLE -->
      <div class="flex-1 overflow-y-auto">
        <table class="w-full border-collapse border-l border-t border-slate-700 text-sm">
          <thead>
            <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
              <th class="w-8 border-r border-b border-slate-700 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-400">#</th>
              <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-300">Employee</th>
              <th class="w-36 border-r border-b border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-300">Role</th>
              <th class="w-8 border-b border-slate-700"></th>
            </tr>
          </thead>
          <tbody>
            <!-- Existing rows -->
            <tr
              v-for="(row, idx) in localRows"
              :key="idx"
              tabindex="-1"
              class="cursor-pointer border-b border-slate-700 outline-none transition-colors"
              :class="selectedRow === idx
                ? 'bg-blue-900/30 border-l-2 border-l-blue-500'
                : 'hover:bg-slate-800/50'"
              @click="selectRow(idx)"
              @keydown="onRowKeydown($event, idx)"
            >
              <td class="px-3 py-2 border-r border-slate-700">
                <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-slate-400">{{ idx + 1 }}</span>
              </td>

              <!-- Employee -->
              <td class="px-2 py-1 border-r border-slate-700 relative">
                <template v-if="selectedRow === idx">
                  <input
                    :ref="el => setRef(el, 'emp', idx)"
                    v-model="row.empSearch"
                    @input="onEmpInput(idx)"
                    @focus="row.showDrop = true"
                    @blur="closeDropdown(idx)"
                    @keydown.enter.prevent="row.dropResults.length ? pickEmployee(idx, row.dropResults[0]) : focusRole(idx)"
                    @keydown.tab.prevent="focusRole(idx)"
                    @keydown.down.prevent="moveRow(idx, 1)"
                    @keydown.up.prevent="moveRow(idx, -1)"
                    @keydown.delete.stop
                    placeholder="Search employee…"
                    class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-0.5 font-mono text-slate-200 outline-none focus:border-blue-500"
                  />
                  <div
                    v-if="row.showDrop && row.dropResults.length"
                    class="absolute left-2 top-full z-20 mt-0.5 w-72 overflow-hidden rounded-xl border border-slate-600 bg-slate-800 shadow-2xl"
                  >
                    <div
                      v-for="emp in row.dropResults"
                      :key="emp.name"
                      @mousedown.prevent="pickEmployee(idx, emp)"
                      class="flex cursor-pointer flex-col px-4 py-2 hover:bg-slate-700 transition-colors"
                    >
                      <span class="text-sm font-bold text-slate-200">{{ emp.employee_name }}</span>
                      <span class="text-[10px] font-mono text-slate-500">{{ emp.name }}{{ emp.designation ? ' · ' + emp.designation : '' }}</span>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="font-semibold text-slate-200">{{ row.employee_name || '—' }}</div>
                  <div v-if="row.employee" class="font-mono text-[10px] text-slate-500">{{ row.employee }}</div>
                </template>
              </td>

              <!-- Role -->
              <td class="px-2 py-1 border-r border-slate-700">
                <select
                  v-if="selectedRow === idx"
                  :ref="el => setRef(el, 'role', idx)"
                  v-model="row.role"
                  @keydown.tab.prevent="goToNextRow(idx)"
                  @keydown.enter.prevent="goToNextRow(idx)"
                  @keydown.down.prevent="moveRow(idx, 1)"
                  @keydown.up.prevent="moveRow(idx, -1)"
                  class="w-full rounded border border-slate-600 bg-slate-800 px-1 py-0.5 text-sm font-bold text-slate-200 outline-none focus:border-blue-500"
                >
                  <option value="">— Select —</option>
                  <option value="Biller">Biller</option>
                  <option value="Sales">Sales</option>
                </select>
                <span v-else class="font-semibold" :class="row.role ? 'text-slate-200' : 'text-slate-600'">{{ row.role || '—' }}</span>
              </td>

              <!-- Delete -->
              <td class="px-2 py-2 text-center">
                <button
                  @click.stop="removeRow(idx)"
                  class="rounded px-1 py-0.5 text-slate-600 hover:bg-red-900/30 hover:text-red-400 transition-colors"
                >&times;</button>
              </td>
            </tr>

            <!-- NEW ENTRY ROW -->
            <tr
              class="border-b border-slate-700"
              :class="selectedRow === -1 ? 'bg-blue-900/20' : 'bg-slate-800/30'"
            >
              <td class="px-3 py-2 border-r border-slate-700">
                <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-900/50 text-[10px] font-bold text-blue-400">+</span>
              </td>
              <td class="px-2 py-1 border-r border-slate-700 relative">
                <input
                  ref="newEmpInput"
                  v-model="newEmpSearch"
                  @input="onNewEmpInput"
                  @focus="newShowDrop = true; selectedRow = -1"
                  @blur="setTimeout(() => newShowDrop = false, 200)"
                  @keydown.enter.prevent="newDropResults.length ? pickNewEmployee(newDropResults[0]) : newRoleInput?.focus()"
                  @keydown.tab.prevent="newRoleInput?.focus()"
                  @keydown.up.prevent="moveRow(localRows.length - 1, 0)"
                  placeholder="Search employee…"
                  class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-900/50"
                />
                <div
                  v-if="newShowDrop && newDropResults.length"
                  class="absolute left-2 top-full z-20 mt-0.5 w-72 overflow-hidden rounded-xl border border-slate-600 bg-slate-800 shadow-2xl"
                >
                  <div
                    v-for="emp in newDropResults"
                    :key="emp.name"
                    @mousedown.prevent="pickNewEmployee(emp)"
                    class="flex cursor-pointer flex-col px-4 py-2 hover:bg-slate-700 transition-colors"
                  >
                    <span class="text-sm font-bold text-slate-200">{{ emp.employee_name }}</span>
                    <span class="text-[10px] font-mono text-slate-500">{{ emp.name }}{{ emp.designation ? ' · ' + emp.designation : '' }}</span>
                  </div>
                </div>
              </td>
              <td class="px-2 py-1 border-r border-slate-700">
                <select
                  ref="newRoleInput"
                  v-model="newRole"
                  @keydown.tab.prevent="addNewRow"
                  @keydown.enter.prevent="addNewRow"
                  class="w-full rounded border border-slate-600 bg-slate-800 px-1 py-1 text-sm font-bold text-slate-200 outline-none focus:border-blue-500"
                >
                  <option value="">— Select —</option>
                  <option value="Biller">Biller</option>
                  <option value="Sales">Sales</option>
                </select>
              </td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- FOOTER -->
      <div class="shrink-0 border-t border-slate-700 bg-slate-800 px-4 py-2.5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4 text-[10px] text-slate-500">
            <span>{{ localRows.length }} employee{{ localRows.length !== 1 ? 's' : '' }}</span>
            <span v-if="saveError" class="text-red-400">{{ saveError }}</span>
            <span v-else class="italic">Points auto-calculated on document submit.</span>
          </div>
          <div class="flex gap-2">
            <button
              @click="$emit('close')"
              class="rounded-lg border border-slate-600 px-4 py-1.5 text-sm font-bold text-slate-300 hover:bg-slate-700 transition"
            >Cancel</button>
            <button
              @click="handleSave"
              class="rounded-lg bg-indigo-600 px-6 py-1.5 text-sm font-black text-white hover:bg-indigo-500 active:scale-95 transition"
            >
              Save Entries
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show:        { type: Boolean, default: false },
  doctype:     { type: String, required: true },
  docname:     { type: String, default: '' },
  initialRows: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'update:rows'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

// ── state ──────────────────────────────────────────────────────────────
const localRows   = ref([])
const selectedRow = ref(-1)
const saveError   = ref('')
const saved       = ref(false)

// new-row fields
const newEmpInput    = ref(null)
const newRoleInput   = ref(null)
const newEmpSearch   = ref('')
const newEmpId       = ref('')
const newEmpName     = ref('')
const newRole        = ref('')
const newShowDrop    = ref(false)
const newDropResults = ref([])
let   newDebounce    = null

// per-row input refs map
const inputRefs = {}
function setRef(el, field, idx) {
  if (el) inputRefs[`${field}-${idx}`] = el
}

// ── initialise on open ──────────────────────────────────────────────────
watch(() => props.show, async (val) => {
  if (!val) return
  saved.value = false
  saveError.value = ''
  selectedRow.value = -1
  localRows.value = toLocalRows(props.initialRows)
  await nextTick()
  newEmpInput.value?.focus()
})

function toLocalRows(arr) {
  return arr.map(r => ({
    employee:      r.employee || '',
    employee_name: r.employee_name || '',
    role:          r.role || '',
    points:        parseFloat(r.points) || 0,
    empSearch:     r.employee_name || '',
    showDrop:      false,
    dropResults:   [],
    _timer:        null,
  }))
}

// ── row selection ───────────────────────────────────────────────────────
function selectRow(idx) {
  selectedRow.value = idx
  nextTick(() => inputRefs[`emp-${idx}`]?.focus())
}

function moveRow(idx, delta) {
  const next = idx + delta
  if (next < 0) return
  if (next >= localRows.value.length) {
    selectedRow.value = -1
    nextTick(() => newEmpInput.value?.focus())
    return
  }
  selectRow(next)
}

function onRowKeydown(e, idx) {
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (document.activeElement?.tagName !== 'INPUT') {
      e.preventDefault()
      removeRow(idx)
    }
  }
  if (e.key === 'ArrowDown') { e.preventDefault(); moveRow(idx, 1) }
  if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
}

function goToNextRow(idx) {
  if (idx + 1 < localRows.value.length) selectRow(idx + 1)
  else {
    selectedRow.value = -1
    nextTick(() => newEmpInput.value?.focus())
  }
}

function focusRole(idx) {
  nextTick(() => inputRefs[`role-${idx}`]?.focus())
}

// ── employee search ─────────────────────────────────────────────────────
function onEmpInput(idx) {
  const row = localRows.value[idx]
  row.employee = ''
  row.employee_name = ''
  clearTimeout(row._timer)
  row._timer = setTimeout(() => searchEmployees(idx, row.empSearch), 250)
}

async function searchEmployees(idx, query) {
  if (!query || query.length < 2) { localRows.value[idx].dropResults = []; return }
  try {
    const res = await frappeGet('ssplbilling.api.incentive_api.search_employees', { query })
    localRows.value[idx].dropResults = res || []
    localRows.value[idx].showDrop = true
  } catch (_) {}
}

function closeDropdown(idx) {
  setTimeout(() => { localRows.value[idx].showDrop = false }, 200)
}

function pickEmployee(idx, emp) {
  const row = localRows.value[idx]
  row.employee = emp.name
  row.employee_name = emp.employee_name
  row.empSearch = emp.employee_name
  row.showDrop = false
  row.dropResults = []
  nextTick(() => focusRole(idx))
}

// ── new-row search ──────────────────────────────────────────────────────
function onNewEmpInput() {
  newEmpId.value = ''
  newEmpName.value = ''
  clearTimeout(newDebounce)
  newDebounce = setTimeout(() => searchNewEmployees(newEmpSearch.value), 250)
}

async function searchNewEmployees(query) {
  if (!query || query.length < 2) { newDropResults.value = []; return }
  try {
    const res = await frappeGet('ssplbilling.api.incentive_api.search_employees', { query })
    newDropResults.value = res || []
    newShowDrop.value = true
  } catch (_) {}
}

function pickNewEmployee(emp) {
  newEmpId.value     = emp.name
  newEmpName.value   = emp.employee_name
  newEmpSearch.value = emp.employee_name
  newShowDrop.value  = false
  newDropResults.value = []
  // Default role: first row → Biller, subsequent → Sales
  newRole.value = localRows.value.length === 0 ? 'Biller' : 'Sales'
  nextTick(() => newRoleInput.value?.focus())
}

function addNewRow() {
  if (!newEmpId.value || !newRole.value) return
  localRows.value.push({
    employee:      newEmpId.value,
    employee_name: newEmpName.value,
    role:          newRole.value,
    points:        0,
    empSearch:     newEmpName.value,
    showDrop:      false,
    dropResults:   [],
    _timer:        null,
  })
  newEmpSearch.value = ''
  newEmpId.value     = ''
  newEmpName.value   = ''
  newRole.value      = ''
  newDropResults.value = []
  nextTick(() => newEmpInput.value?.focus())
}

function removeRow(idx) {
  localRows.value.splice(idx, 1)
  selectedRow.value = Math.min(selectedRow.value, localRows.value.length - 1)
}

// ── save ────────────────────────────────────────────────────────────────
function handleSave() {
  saveError.value = ''
  const invalid = localRows.value.find(r => !r.employee || !r.role)
  if (invalid) { saveError.value = 'Each row needs an Employee and a Role.'; return }

  emit('update:rows', localRows.value.map(r => ({ employee: r.employee, employee_name: r.employee_name, role: r.role, points: r.points || 0 })))
  saved.value = true
}
</script>
