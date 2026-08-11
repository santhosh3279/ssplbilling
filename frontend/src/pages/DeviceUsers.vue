<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="enroll" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Device Users
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Copy enrolled users between machines, or create an employee and push them to a device.
            Fingerprints travel with the user — face templates cannot be copied.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <button
            @click="openEnroll"
            class="flex items-center gap-2 rounded-xl bg-[var(--color-employee)] text-white px-5 py-3 font-bold hover:brightness-110 active:scale-95 transition-all duration-200 shadow-md shadow-[var(--color-employee)]/15"
          >
            <span>➕</span> New Employee + Enroll
          </button>
        </div>
      </header>

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

        <div>
          <div class="mb-6 flex flex-wrap items-end gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Source machine</label>
              <select
                v-model="sourceMachine"
                @change="loadMachineUsers"
                class="mt-1 block px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              >
                <option value="">— Select —</option>
                <option v-for="m in machines" :key="m.name" :value="m.name">
                  {{ m.store || m.name }} ({{ m.ip_address }})
                </option>
              </select>
            </div>

            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Target machine</label>
              <select
                v-model="targetMachine"
                @change="loadTargetUsers"
                class="mt-1 block px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
              >
                <option value="">— Select —</option>
                <option v-for="m in machines" :key="m.name" :value="m.name" :disabled="m.name === sourceMachine">
                  {{ m.store || m.name }} ({{ m.ip_address }})
                </option>
              </select>
            </div>

            <button
              @click="copyToTarget"
              :disabled="!sourceMachine || !targetMachine || !selected.length || busy"
              class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
            >
              Copy {{ selected.length }} to target →
            </button>

            <button
              @click="loadMachineUsers"
              :disabled="!sourceMachine || busy"
              class="ml-auto rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
            >
              🔄 Reload
            </button>

            <p
              v-if="targetMachine"
              class="w-full text-[11px] font-semibold text-[var(--color-text-muted)]"
            >
              Showing only the {{ visibleUsers.length }} user(s) missing on the target —
              {{ machineUsers.length - visibleUsers.length }} already enrolled there are hidden.
            </p>
          </div>

          <div class="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-md overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left text-lg border-collapse">
                <thead>
                  <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 font-bold text-sm uppercase tracking-wider text-[var(--color-text-muted)]">
                    <th class="px-6 py-4">
                      <input type="checkbox" :checked="allSelected" @change="toggleAll" class="h-4 w-4" />
                    </th>
                    <th class="px-6 py-4">Code</th>
                    <th class="px-6 py-4">Name on device</th>
                    <th class="px-6 py-4">Fingerprints</th>
                    <th class="px-6 py-4">Privilege</th>
                    <th class="px-6 py-4">Employee</th>
                    <th class="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]">
                  <tr
                    v-for="user in visibleUsers"
                    :key="user.user_id"
                    class="hover:bg-[var(--color-midlight)]/40 transition-colors"
                  >
                    <td class="px-6 py-3">
                      <input type="checkbox" :value="user.user_id" v-model="selected" class="h-4 w-4" />
                    </td>
                    <td class="px-6 py-3 font-mono font-bold text-[var(--color-employee)]">{{ user.user_id }}</td>
                    <td class="px-6 py-3 font-bold">{{ user.name || '—' }}</td>
                    <td class="px-6 py-3">
                      <span
                        class="px-2.5 py-1 text-[10px] font-black rounded-full uppercase tracking-wider"
                        :class="user.templates
                          ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'"
                      >
                        {{ user.templates }} 👆
                      </span>
                    </td>
                    <td class="px-6 py-3 text-sm font-semibold">{{ user.privilege }}</td>
                    <td class="px-6 py-3 text-sm">{{ user.employee || '— unmapped —' }}</td>
                    <td class="px-6 py-3 text-right whitespace-nowrap">
                      <button
                        @click="removeFromMachine(user)"
                        class="rounded-xl border border-rose-500/30 text-rose-500 px-3 py-1.5 text-xs font-bold hover:bg-rose-500/10 transition-colors"
                      >
                        Remove from device
                      </button>
                    </td>
                  </tr>
                  <tr v-if="!visibleUsers.length && !busy">
                    <td colspan="7" class="px-6 py-12 text-center text-sm text-[var(--color-text-muted)] italic">
                      <template v-if="targetMachine && machineUsers.length">
                        Every user on the source machine is already enrolled on the target.
                      </template>
                      <template v-else>
                        Pick a source machine to read the users enrolled on it.
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Enroll modal -->
    <div
      v-if="showEnroll"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
      @click.self="showEnroll = false"
    >
      <div class="w-[620px] max-h-[90vh] overflow-y-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
        <div class="px-6 py-4 border-b border-[var(--color-border)] text-lg font-black uppercase tracking-wider">
          New Employee + Device Enrollment
        </div>

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                First Name <span class="text-rose-500">*</span>
              </label>
              <input v-model="enroll.first_name" type="text" class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]" />
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Last Name</label>
              <input v-model="enroll.last_name" type="text" class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile</label>
              <input v-model="enroll.mobile" type="text" class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]" />
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date of Joining</label>
              <input v-model="enroll.date_of_joining" type="date" class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                Employee Code <span class="text-rose-500">*</span>
              </label>
              <div class="mt-1 flex gap-2">
                <input v-model="enroll.employee_code" type="text" class="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold font-mono focus:outline-none focus:border-[var(--color-employee)]" />
                <button @click="suggestCode" class="rounded-xl border border-[var(--color-border)] px-3 text-xs font-bold hover:bg-[var(--color-midlight)]">Next free</button>
              </div>
              <p class="mt-1 text-[11px] text-[var(--color-text-muted)]">
                The id the device stores against every punch. Checked against all machines.
              </p>
            </div>
            <div>
              <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Privilege</label>
              <select v-model="enroll.privilege" class="mt-1 w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]">
                <option>User</option>
                <option>Admin</option>
              </select>
            </div>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Push to machines</label>
            <div class="mt-2 flex flex-wrap gap-3">
              <label
                v-for="m in machines"
                :key="m.name"
                class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] px-4 py-2 text-sm font-bold cursor-pointer hover:bg-[var(--color-midlight)]"
              >
                <input type="checkbox" :value="m.name" v-model="enroll.machines" class="h-4 w-4" />
                {{ m.store || m.name }}
              </label>
            </div>
            <p class="mt-2 text-[11px] text-[var(--color-text-muted)]">
              The user is created on the device with no fingerprint — enroll the finger on the
              device itself, then copy the user to the other machines from here.
            </p>
          </div>

          <div v-if="enrollError" class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-2.5 text-xs font-bold text-rose-500">
            {{ enrollError }}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-3">
          <button @click="showEnroll = false" class="rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold hover:bg-[var(--color-midlight)]">
            Cancel
          </button>
          <button
            @click="saveEnroll"
            :disabled="!enroll.first_name || !enroll.employee_code || saving"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            {{ saving ? 'Working...' : 'Create & Enroll' }}
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
  fetchEsslMachines,
  fetchMachineUsers,
  copyMachineUsers,
  fetchNextEmployeeCode,
  createEmployeeAndEnroll,
  deleteMachineUser,
} from '../api.js'

const busy = ref(false)
const busyLabel = ref('Loading...')
const error = ref('')
const notice = ref('')

const machines = ref([])
const machineUsers = ref([])
const targetUserIds = ref([])

const sourceMachine = ref('')
const targetMachine = ref('')
const selected = ref([])

const showEnroll = ref(false)
const saving = ref(false)
const enrollError = ref('')
const enroll = ref(blankEnroll())

function blankEnroll() {
  return {
    first_name: '',
    last_name: '',
    mobile: '',
    date_of_joining: '',
    employee_code: '',
    privilege: 'User',
    machines: [],
  }
}

// With a target picked, only the users the target does not have yet are worth copying.
const visibleUsers = computed(() => {
  if (!targetMachine.value) return machineUsers.value
  const have = new Set(targetUserIds.value.map(String))
  return machineUsers.value.filter((u) => !have.has(String(u.user_id)))
})

const allSelected = computed(
  () => visibleUsers.value.length > 0 && selected.value.length === visibleUsers.value.length,
)

function toggleAll(event) {
  selected.value = event.target.checked ? visibleUsers.value.map((u) => u.user_id) : []
}

async function run(label, fn) {
  busy.value = true
  busyLabel.value = label
  error.value = ''
  notice.value = ''
  try {
    return await fn()
  } catch (err) {
    console.error(label, err)
    error.value = err.message || label + ' failed.'
    return null
  } finally {
    busy.value = false
  }
}

async function loadMachines() {
  await run('Loading machines...', async () => {
    machines.value = (await fetchEsslMachines()) || []
    if (!sourceMachine.value && machines.value.length) {
      sourceMachine.value = machines.value[0].name
      await loadMachineUsers()
    }
  })
}

async function loadMachineUsers() {
  selected.value = []
  machineUsers.value = []
  if (!sourceMachine.value) return
  await run('Reading users from the device...', async () => {
    const res = await fetchMachineUsers(sourceMachine.value)
    machineUsers.value = res?.users || []
  })
}

async function loadTargetUsers() {
  targetUserIds.value = []
  if (!targetMachine.value) return
  await run('Reading users already on the target device...', async () => {
    const res = await fetchMachineUsers(targetMachine.value)
    targetUserIds.value = (res?.users || []).map((u) => u.user_id)
  })
  // Anything now hidden must not stay selected.
  const shown = new Set(visibleUsers.value.map((u) => String(u.user_id)))
  selected.value = selected.value.filter((id) => shown.has(String(id)))
}

async function copyToTarget() {
  const res = await run('Copying users to the target device...', () =>
    copyMachineUsers({ source: sourceMachine.value, target: targetMachine.value, userIds: selected.value }),
  )
  if (res) {
    notice.value = `${res.copied} user(s) copied to ${res.target}${res.failed ? `, ${res.failed} failed` : ''}.`
    const failed = (res.users || []).filter((u) => u.error)
    if (failed.length) error.value = failed.map((u) => `${u.user_id}: ${u.error}`).join(' · ')
    const copyNotice = notice.value
    const copyError = error.value
    await loadTargetUsers()
    notice.value = copyNotice
    error.value = copyError
  }
}

async function removeFromMachine(user) {
  if (!confirm(`Remove ${user.name || user.user_id} from this device? Fingerprints on it are lost.`)) return
  const res = await run('Removing user from the device...', () =>
    deleteMachineUser({ machine: sourceMachine.value, userId: user.user_id }),
  )
  if (res) {
    notice.value = `${res.deleted} removed from ${res.machine}.`
    await loadMachineUsers()
  }
}

async function openEnroll() {
  enroll.value = blankEnroll()
  enrollError.value = ''
  showEnroll.value = true
  await suggestCode()
}

async function suggestCode() {
  try {
    const res = await fetchNextEmployeeCode()
    enroll.value.employee_code = res?.next_code || ''
    if (res?.unreachable?.length) {
      enrollError.value =
        'Could not reach ' +
        res.unreachable.map((u) => u.machine).join(', ') +
        ' — a code already used there may be handed out twice.'
    }
  } catch (err) {
    console.error('Failed to suggest a code:', err)
    enrollError.value = err.message || 'Failed to read the used codes.'
  }
}

async function saveEnroll() {
  saving.value = true
  enrollError.value = ''
  try {
    const res = await createEmployeeAndEnroll(enroll.value)
    showEnroll.value = false
    notice.value = `${res.employee_name} created as ${res.employee} with code ${res.employee_code}.`
    if (res.name_truncated) {
      notice.value += ' The name was shortened to 24 characters on the device.'
    }
    await loadMachineUsers()
  } catch (err) {
    console.error('Enrollment failed:', err)
    enrollError.value = err.message || 'Enrollment failed.'
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadMachines()
})
</script>
