<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="employees" />

    <!-- ===================== MAIN LIST PANEL ===================== -->
    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Employees
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Employee list from the Employee doctype
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
            {{ filteredEmployees.length }} / {{ employeesList.length }}
          </span>
          <button
            @click="loadEmployees"
            :disabled="loading"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15 disabled:opacity-50"
          >
            <span>🔄</span> Refresh
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
            placeholder="Search by ID, name, designation, email or phone..."
            class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-employee)] focus:ring-2 focus:ring-[var(--color-employee)]/15 transition-all duration-200"
          />
        </div>

        <div class="flex items-center gap-2 self-stretch md:self-auto ml-auto">
          <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Status:</span>
          <select
            v-model="statusFilter"
            class="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
          >
            <option value="All">All Statuses</option>
            <option value="Active">Active Only</option>
            <option value="Inactive">Inactive Only</option>
            <option value="Suspended">Suspended</option>
            <option value="Left">Left</option>
          </select>
        </div>
      </div>

      <!-- Employee list -->
      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="loading" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">Loading employees...</p>
        </div>

        <div
          v-if="error"
          class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500"
        >
          {{ error }}
        </div>

        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-2xl border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4 min-w-[60px]">#</th>
                  <th class="px-6 py-4">ID</th>
                  <th class="px-6 py-4">Name</th>
                  <th class="px-6 py-4">Designation</th>
                  <th class="px-6 py-4">Gender</th>
                  <th class="px-6 py-4">Mobile</th>
                  <th class="px-6 py-4">Email</th>
                  <th class="px-6 py-4">Joining Date</th>
                  <th class="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="(emp, index) in filteredEmployees"
                  :key="emp.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
                  <td class="px-6 py-4 font-mono text-xs font-bold text-[var(--color-text-muted)]">
                    {{ index + 1 }}
                  </td>
                  <td class="px-6 py-4 font-mono text-xs font-bold text-[var(--color-employee)]">
                    {{ emp.name }}
                  </td>
                  <td class="px-6 py-4 font-bold text-[var(--color-text)]">
                    {{ emp.employee_name }}
                  </td>
                  <td class="px-6 py-4 font-semibold text-[var(--color-text-muted)]">
                    {{ emp.designation || 'Staff' }}
                  </td>
                  <td class="px-6 py-4 text-xs font-semibold">
                    {{ emp.gender || '—' }}
                  </td>
                  <td class="px-6 py-4 font-mono text-xs">
                    {{ emp.cell_number || '—' }}
                  </td>
                  <td class="px-6 py-4 text-xs truncate max-w-[150px]" :title="emp.personal_email">
                    {{ emp.personal_email || '—' }}
                  </td>
                  <td class="px-6 py-4 font-mono text-xs">
                    {{ formatDate(emp.date_of_joining) }}
                  </td>
                  <td class="px-6 py-4">
                    <span
                      class="px-2.5 py-1 text-[10px] font-black rounded-full uppercase tracking-wider"
                      :class="getStatusClass(emp.status)"
                    >
                      ● {{ emp.status || 'Active' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="filteredEmployees.length === 0 && !loading">
                  <td colspan="8" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No employees matching the filters were found.
                  </td>
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
import { ref, computed, onMounted } from 'vue'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import { fetchEmployees } from '../api.js'

import { formatDMY } from '../utils/date'
const loading = ref(false)
const error = ref('')
const employeesList = ref([])

const searchQuery = ref('')
const statusFilter = ref('All')

async function loadEmployees() {
  loading.value = true
  error.value = ''
  try {
    // Empty string (not undefined) — frappeGet stringifies every param, so an
    // undefined status would reach the server as the literal "undefined".
    const list = await fetchEmployees('')
    employeesList.value = list || []
  } catch (err) {
    console.error('Failed to load employee list:', err)
    error.value = err.message || 'Failed to load employee list.'
    employeesList.value = []
  } finally {
    loading.value = false
  }
}

const filteredEmployees = computed(() => {
  let list = employeesList.value

  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter((emp) => {
      const nameMatch = (emp.employee_name || '').toLowerCase().includes(query)
      const codeMatch = (emp.name || '').toLowerCase().includes(query)
      const desigMatch = (emp.designation || '').toLowerCase().includes(query)
      const phoneMatch = (emp.cell_number || '').includes(query)
      const emailMatch = (emp.personal_email || '').toLowerCase().includes(query)
      return nameMatch || codeMatch || desigMatch || phoneMatch || emailMatch
    })
  }

  if (statusFilter.value !== 'All') {
    list = list.filter((emp) => (emp.status || 'Active') === statusFilter.value)
  }

  return list
})

function formatDate(dateStr) {
  return formatDMY(dateStr, '—')
}

function getStatusClass(status) {
  const stat = status || 'Active'
  if (stat === 'Active') {
    return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
  }
  if (stat === 'Left') {
    return 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
  }
  if (stat === 'Suspended') {
    return 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
  }
  return 'bg-[var(--color-text-muted)]/10 text-[var(--color-text-muted)] border border-[var(--color-text-muted)]/20'
}

onMounted(() => {
  loadEmployees()
})
</script>
