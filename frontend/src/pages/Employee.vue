<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- ===================== HRMS SIDEBAR ===================== -->
    <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
      <!-- Portal Brand -->
      <div class="border-b border-[var(--color-border)] px-6 py-5">
        <div class="text-xl font-black tracking-wider text-[var(--color-employee)] flex items-center gap-2">
          <span>👥</span> SSPL HRMS
        </div>
        <div class="mt-1 text-xs text-[var(--color-text-muted)] uppercase tracking-widest font-semibold">
          Workforce Hub
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <button
          @click="router.push('/hrms')"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 hover:bg-[var(--color-midlight)] text-[var(--color-text)]"
        >
          <span class="text-lg">📊</span> Dashboard
        </button>

        <button
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20"
        >
          <span class="text-lg">👥</span> Employees
        </button>

        <button
          @click="router.push('/hrms')"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 hover:bg-[var(--color-midlight)] text-[var(--color-text)]"
        >
          <span class="text-lg">📅</span> Attendance
        </button>

        <button
          @click="router.push('/hrms')"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 hover:bg-[var(--color-midlight)] text-[var(--color-text)]"
        >
          <span class="text-lg">💸</span> Payroll & Salary
        </button>

        <button
          @click="router.push('/hrms')"
          class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200 hover:bg-[var(--color-midlight)] text-[var(--color-text)]"
        >
          <span class="text-lg">✉️</span> Leave Tracker
        </button>
      </nav>

      <!-- Back to wholesale billing -->
      <div class="border-t border-[var(--color-border)] p-4">
        <button
          @click="router.push('/')"
          class="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-3 text-xs font-bold hover:bg-[var(--color-midlight)] transition-all duration-200 active:scale-95 text-[var(--color-text)]"
        >
          ← Back to Billing
        </button>
      </div>
    </aside>

    <!-- ===================== MAIN DIRECTORY PANEL ===================== -->
    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <!-- Top header bar -->
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Employee Directory
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">Add, view and edit company employee profiles</p>
        </div>

        <div>
          <button
            @click="openAddModal"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15"
          >
            <span>➕</span> Add Employee
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
            placeholder="Search by ID, name, email or phone..."
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

      <!-- Employees Table / Grid -->
      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="loading" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">Loading employees directory...</p>
        </div>

        <!-- Table Card -->
        <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm border-collapse text-[var(--color-text)]">
              <thead>
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-6 py-4">ID</th>
                  <th class="px-6 py-4">Name</th>
                  <th class="px-6 py-4">Designation</th>
                  <th class="px-6 py-4">Gender</th>
                  <th class="px-6 py-4">Mobile</th>
                  <th class="px-6 py-4">Email</th>
                  <th class="px-6 py-4">Joining Date</th>
                  <th class="px-6 py-4">Status</th>
                  <th class="px-6 py-4 text-right font-bold">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--color-border)]">
                <tr
                  v-for="emp in filteredEmployees"
                  :key="emp.name"
                  class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                >
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
                    {{ emp.gender }}
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
                  <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        @click="openEditModal(emp)"
                        class="p-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] hover:bg-[var(--color-employee)] hover:text-white transition-all duration-200 active:scale-90"
                        title="Edit profile"
                      >
                        ✏️
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredEmployees.length === 0 && !loading">
                  <td colspan="9" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                    No employees matching the filters were found.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

    <!-- ===================== ADD / EDIT MODAL ===================== -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-2xl bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <!-- Modal Header -->
        <div class="border-b border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface-raised)]/50 flex items-center justify-between">
          <h3 class="text-lg font-black uppercase tracking-wider text-[var(--color-text)]">
            {{ editMode ? 'Edit Employee Profile' : 'Add New Employee' }}
          </h3>
          <button
            @click="closeModal"
            class="text-xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          >
            &times;
          </button>
        </div>

        <!-- Modal Body (Form) -->
        <form @submit.prevent="handleSubmit" class="flex-1 overflow-y-auto p-6 space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- First Name -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">First Name <span class="text-rose-500">*</span></label>
              <input
                v-model="form.first_name"
                type="text"
                required
                placeholder="Enter first name"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Last Name -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Last Name</label>
              <input
                v-model="form.last_name"
                type="text"
                placeholder="Enter last name"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Gender -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Gender</label>
              <select
                v-model="form.gender"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <!-- Date of Birth -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date of Birth</label>
              <input
                v-model="form.date_of_birth"
                type="date"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Date of Joining -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date of Joining</label>
              <input
                v-model="form.date_of_joining"
                type="date"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Mobile -->
            <div class="space-y-1">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile Number</label>
              <input
                v-model="form.mobile"
                type="text"
                placeholder="e.g. 9876543210"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Email -->
            <div class="space-y-1 md:col-span-2">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Personal Email</label>
              <input
                v-model="form.email"
                type="email"
                placeholder="name@email.com"
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)]"
              />
            </div>

            <!-- Current Address -->
            <div class="space-y-1 md:col-span-2">
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Current Address</label>
              <textarea
                v-model="form.current_address"
                rows="3"
                placeholder="Enter address details..."
                class="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)] text-[var(--color-text)] resize-none"
              ></textarea>
            </div>
          </div>
        </form>

        <!-- Modal Footer -->
        <div class="border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface-raised)]/50 flex justify-end gap-3">
          <button
            type="button"
            @click="closeModal"
            class="px-4 py-2 rounded-lg border border-[var(--color-border)] text-sm font-bold hover:bg-[var(--color-midlight)] transition-all"
          >
            Cancel
          </button>
          <button
            type="button"
            @click="handleSubmit"
            :disabled="saving"
            class="px-5 py-2 rounded-lg bg-[var(--color-employee)] text-white text-sm font-bold shadow-md hover:brightness-110 active:scale-95 disabled:opacity-50 transition-all"
          >
            {{ saving ? 'Saving...' : 'Save Profile' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchEmployees, createEmployee, getEmployeeDetails, updateEmployee } from '../api.js'

const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const employeesList = ref([])

const searchQuery = ref('')
const statusFilter = ref('All')

// Modal states
const showModal = ref(false)
const editMode = ref(false)
const currentEmployee = ref(null)

const form = ref({
  first_name: '',
  last_name: '',
  gender: 'Male',
  date_of_birth: '',
  date_of_joining: '',
  mobile: '',
  email: '',
  current_address: ''
})

function resetForm() {
  form.value = {
    first_name: '',
    last_name: '',
    gender: 'Male',
    date_of_birth: '',
    date_of_joining: new Date().toISOString().split('T')[0],
    mobile: '',
    email: '',
    current_address: ''
  }
  currentEmployee.value = null
}

async function loadEmployees() {
  loading.value = true
  try {
    const list = await fetchEmployees()
    employeesList.value = list || []
  } catch (err) {
    console.error('Failed to load employee list:', err)
  } finally {
    loading.value = false
  }
}

const filteredEmployees = computed(() => {
  let list = employeesList.value
  
  // Apply Search
  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter(emp => {
      const nameMatch = (emp.employee_name || '').toLowerCase().includes(query)
      const codeMatch = (emp.name || '').toLowerCase().includes(query)
      const phoneMatch = (emp.cell_number || '').includes(query)
      const emailMatch = (emp.personal_email || '').toLowerCase().includes(query)
      return nameMatch || codeMatch || phoneMatch || emailMatch
    })
  }

  // Apply Status Filter
  if (statusFilter.value !== 'All') {
    list = list.filter(emp => (emp.status || 'Active') === statusFilter.value)
  }

  return list
})

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    const parts = dateStr.split('-')
    if (parts.length === 3) {
      return `${parts[2]}-${parts[1]}-${parts[0]}` // dd-mm-yyyy
    }
  } catch (_) {}
  return dateStr
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

function openAddModal() {
  resetForm()
  editMode.value = false
  showModal.value = true
}

async function openEditModal(emp) {
  loading.value = true
  try {
    const details = await getEmployeeDetails(emp.name)
    form.value = {
      first_name: details.first_name || '',
      last_name: details.last_name || '',
      gender: details.gender || 'Male',
      date_of_birth: details.date_of_birth || '',
      date_of_joining: details.date_of_joining || '',
      mobile: details.mobile || '',
      email: details.email || '',
      current_address: details.current_address || ''
    }
    currentEmployee.value = details
    editMode.value = true
    showModal.value = true
  } catch (err) {
    alert(`Failed to fetch details for employee ${emp.name}`)
  } finally {
    loading.value = false
  }
}

function closeModal() {
  showModal.value = false
  resetForm()
}

async function handleSubmit() {
  if (!form.value.first_name.trim()) {
    alert('First Name is required.')
    return
  }

  saving.value = true
  try {
    const payload = {
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      gender: form.value.gender,
      date_of_birth: form.value.date_of_birth || undefined,
      date_of_joining: form.value.date_of_joining || undefined,
      mobile: form.value.mobile,
      email: form.value.email,
      current_address: form.value.current_address
    }

    if (editMode.value && currentEmployee.value) {
      payload.name = currentEmployee.value.name
      await updateEmployee(payload)
      alert(`Employee ${payload.first_name} updated successfully.`)
    } else {
      await createEmployee(payload)
      alert(`Employee ${payload.first_name} created successfully.`)
    }

    closeModal()
    await loadEmployees()
  } catch (err) {
    console.error('Error saving employee profile:', err)
    alert(err.message || 'Failed to save employee profile.')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadEmployees()
})
</script>
