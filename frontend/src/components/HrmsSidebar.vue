<template>
  <aside class="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg">
    <div class="border-b border-[var(--color-border)] px-6 py-5">
      <div class="text-xl font-black tracking-wider text-[var(--color-employee)] flex items-center gap-2">
        <span>👥</span> SSPL HRMS
      </div>
      <div class="mt-1 text-xs text-[var(--color-text-muted)] uppercase tracking-widest font-semibold">
        Workforce Hub
      </div>
    </div>

    <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
      <button
        v-for="link in links"
        :key="link.key"
        @click="link.key === active ? null : router.push(link.path)"
        class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-bold transition-all duration-200"
        :class="link.key === active
          ? 'bg-[var(--color-employee)] text-white shadow-lg shadow-[var(--color-employee)]/20'
          : 'hover:bg-[var(--color-midlight)] text-[var(--color-text)]'"
      >
        <span class="text-lg">{{ link.icon }}</span> {{ link.label }}
      </button>
    </nav>

    <div class="border-t border-[var(--color-border)] p-4">
      <button
        @click="router.push('/')"
        class="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-3 text-xs font-bold hover:bg-[var(--color-midlight)] transition-all duration-200 active:scale-95 text-[var(--color-text)]"
      >
        ← Back to Billing
      </button>
    </div>
  </aside>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  // key of the link to highlight: dashboard | employees | machines | mapping | attendance
  active: { type: String, default: '' },
})

const router = useRouter()

const links = [
  { key: 'dashboard',  label: 'Dashboard',        icon: '📊', path: '/hrms' },
  { key: 'employees',  label: 'Employees',        icon: '👥', path: '/hrms/employees' },
  { key: 'machines',   label: 'eSSL Machines',    icon: '🖥️', path: '/hrms/essl-machines' },
  { key: 'mapping',    label: 'Employee Mapping', icon: '🔗', path: '/hrms/essl-mapping' },
  { key: 'attendance', label: 'Attendance',       icon: '📅', path: '/hrms/attendance' },
]
</script>
