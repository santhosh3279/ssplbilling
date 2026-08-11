<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <HrmsSidebar active="chart" />

    <main class="flex-1 overflow-hidden bg-[var(--color-bg)] flex flex-col">
      <header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 class="text-2xl font-black uppercase tracking-wider text-[var(--color-text)]">
            Attendance Chart
          </h1>
          <p class="text-xs text-[var(--color-text-muted)] font-medium">
            Working hours per day for one employee. Sundays are marked in orange.
          </p>
        </div>

        <button
          @click="load"
          :disabled="busy || !employee"
          class="rounded-xl border border-[var(--color-border)] px-5 py-3 text-sm font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
        >
          🔄 Reload
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-8 relative">
        <div v-if="busy" class="absolute inset-0 bg-[var(--color-bg)]/80 flex flex-col items-center justify-center gap-3 z-20">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-employee)] border-t-transparent"></div>
          <p class="text-sm font-semibold text-[var(--color-text-muted)]">Loading attendance...</p>
        </div>

        <div v-if="error" class="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-5 py-3 text-sm font-semibold text-rose-500">
          {{ error }}
        </div>

        <!-- Filters -->
        <div class="mb-6 flex flex-wrap items-end gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Employee</label>
            <select
              v-model="employee"
              @change="load"
              class="mt-1 block min-w-[220px] px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="">— Select —</option>
              <option v-for="emp in employees" :key="emp.name" :value="emp.name">
                {{ emp.employee_name || emp.name }}
              </option>
            </select>
          </div>

          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
            <input
              v-model="fromDate"
              type="date"
              class="mt-1 block px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
            <input
              v-model="toDate"
              type="date"
              class="mt-1 block px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>

          <button
            @click="load"
            :disabled="busy || !employee"
            class="rounded-xl bg-[var(--color-employee)] text-white px-5 py-2.5 text-sm font-bold hover:brightness-110 disabled:opacity-50"
          >
            Apply
          </button>

          <div class="ml-auto flex gap-2">
            <button
              v-for="preset in presets"
              :key="preset.label"
              @click="applyPreset(preset)"
              class="rounded-xl border border-[var(--color-border)] px-4 py-2.5 text-xs font-bold hover:bg-[var(--color-midlight)]"
            >
              {{ preset.label }}
            </button>
          </div>
        </div>

        <!-- Totals -->
        <div v-if="days.length" class="mb-6 flex flex-wrap gap-3">
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md">
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Total hours</div>
            <div class="text-2xl font-black">{{ totalHours.toFixed(2) }}</div>
          </div>
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md">
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Days marked</div>
            <div class="text-2xl font-black">{{ markedDays }}</div>
          </div>
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md">
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Average hours / marked day</div>
            <div class="text-2xl font-black">{{ averageHours.toFixed(2) }}</div>
          </div>
          <div class="flex items-center gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full" :style="{ background: WEEKDAY_COLOR }"></span> Weekday
            </span>
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full" :style="{ background: SUNDAY_COLOR }"></span> Sunday
            </span>
          </div>
        </div>

        <!-- Chart -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
          <div v-if="!employee" class="py-16 text-center text-sm text-[var(--color-text-muted)] italic">
            Pick an employee to draw their working hours.
          </div>
          <div v-else-if="!days.length && !busy" class="py-16 text-center text-sm text-[var(--color-text-muted)] italic">
            No attendance for this employee in this range.
          </div>

          <div v-else class="overflow-x-auto">
            <div class="flex" :style="{ minWidth: days.length * 52 + 60 + 'px' }">
              <!-- Y axis: working hours. The spacer keeps the ticks level with the
                   plot band, which starts below the row of hour labels. -->
              <div class="w-12 shrink-0">
                <div :style="{ height: LABEL_HEIGHT + 'px' }"></div>
                <div class="relative" :style="{ height: PLOT_HEIGHT + 'px' }">
                  <div
                    v-for="tick in yTicks"
                    :key="tick"
                    class="absolute right-2 -translate-y-1/2 text-[10px] font-bold text-[var(--color-text-muted)]"
                    :style="{ bottom: (tick / yMax) * PLOT_HEIGHT + 'px' }"
                  >
                    {{ tick }}h
                  </div>
                </div>
              </div>

              <!-- Plot -->
              <div class="relative flex-1">
                <!-- Gridlines sit behind the bars, in the same band -->
                <div
                  class="pointer-events-none absolute inset-x-0"
                  :style="{ top: LABEL_HEIGHT + 'px', height: PLOT_HEIGHT + 'px' }"
                >
                  <div
                    v-for="tick in yTicks"
                    :key="tick"
                    class="absolute inset-x-0 border-t border-dashed border-[var(--color-border)] opacity-60"
                    :style="{ bottom: (tick / yMax) * PLOT_HEIGHT + 'px' }"
                  ></div>
                </div>

                <div class="flex items-end gap-2">
                  <div
                    v-for="day in days"
                    :key="day.date"
                    class="flex min-w-[44px] flex-1 flex-col items-center"
                  >
                    <!-- Hours printed on top of every bar -->
                    <span
                      class="flex items-end text-[10px] font-black"
                      :style="{ height: LABEL_HEIGHT + 'px' }"
                      :class="day.sunday ? 'text-amber-500' : 'text-[var(--color-text)]'"
                    >
                      {{ day.hours ? day.hours.toFixed(2) + 'h' : '—' }}
                    </span>
                    <div class="flex w-full items-end" :style="{ height: PLOT_HEIGHT + 'px' }">
                      <div
                        class="w-full rounded-t-lg transition-all"
                        :style="{
                          height: barHeight(day.hours) + 'px',
                          background: day.sunday ? SUNDAY_COLOR : WEEKDAY_COLOR,
                        }"
                        :title="tooltip(day)"
                      ></div>
                    </div>
                    <!-- X axis: the date, with the weekday under it -->
                    <span class="mt-2 text-[10px] font-bold" :class="day.sunday ? 'text-amber-500' : 'text-[var(--color-text-muted)]'">
                      {{ day.dayLabel }}
                    </span>
                    <span class="text-[9px] font-semibold uppercase" :class="day.sunday ? 'text-amber-500' : 'text-[var(--color-text-muted)]'">
                      {{ day.weekday }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import HrmsSidebar from '../components/HrmsSidebar.vue'
import { fetchAttendanceSummary, fetchEmployees } from '../api.js'

// The band the bars are drawn in, plus the strip above it holding the hour label.
const PLOT_HEIGHT = 300
const LABEL_HEIGHT = 18

const WEEKDAY_COLOR = '#10b981'
const SUNDAY_COLOR = '#f97316'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const busy = ref(false)
const error = ref('')

const employees = ref([])
const employee = ref('')
const fromDate = ref(isoDate(startOfMonth()))
const toDate = ref(isoDate(new Date()))

const days = ref([])

const presets = [
  { label: 'This month', days: null },
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
]

function startOfMonth() {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function isoDate(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

// Parsed as local time on purpose — new Date('2026-08-09') is UTC midnight and
// can land on the previous day, which would mark the wrong bar as a Sunday.
function parseDate(iso) {
  const [y, m, d] = String(iso).split('-').map(Number)
  return new Date(y, (m || 1) - 1, d || 1)
}

function applyPreset(preset) {
  const today = new Date()
  if (preset.days === null) {
    fromDate.value = isoDate(startOfMonth())
  } else {
    const start = new Date()
    start.setDate(today.getDate() - (preset.days - 1))
    fromDate.value = isoDate(start)
  }
  toDate.value = isoDate(today)
  load()
}

const totalHours = computed(() => days.value.reduce((sum, d) => sum + d.hours, 0))
const markedDays = computed(() => days.value.filter((d) => d.total > 0).length)
const averageHours = computed(() => (markedDays.value ? totalHours.value / markedDays.value : 0))

const maxHours = computed(() => days.value.reduce((max, d) => Math.max(max, d.hours), 0))
// Scale rounded up to a whole hour so the gridline labels stay tidy.
const yMax = computed(() => Math.max(1, Math.ceil(maxHours.value)))
const yTicks = computed(() => {
  const step = yMax.value <= 4 ? 1 : Math.ceil(yMax.value / 4)
  const ticks = []
  for (let h = 0; h <= yMax.value; h += step) ticks.push(h)
  if (ticks[ticks.length - 1] !== yMax.value) ticks.push(yMax.value)
  return ticks
})

// A day with hours never drops below 3px, so a short shift stays visible.
function barHeight(hours) {
  if (!hours) return 0
  return Math.max(3, Math.round((hours / yMax.value) * PLOT_HEIGHT))
}

function tooltip(day) {
  const parts = Object.entries(day.counts || {}).map(([status, count]) => `${status}: ${count}`)
  return `${day.date} (${day.weekday})\n${day.hours.toFixed(2)} hours\n${parts.join('\n')}`
}

// Every date in the range gets a bar — days with no attendance stay at zero so
// the gaps in the month are visible rather than silently collapsed.
function buildDays(buckets) {
  const byDate = {}
  for (const bucket of buckets) byDate[bucket.key] = bucket

  const start = parseDate(fromDate.value)
  const end = parseDate(toDate.value)
  const out = []
  for (const cursor = new Date(start); cursor <= end; cursor.setDate(cursor.getDate() + 1)) {
    const iso = isoDate(cursor)
    const bucket = byDate[iso]
    out.push({
      date: iso,
      dayLabel: iso.slice(8), // day of the month
      weekday: WEEKDAYS[cursor.getDay()],
      sunday: cursor.getDay() === 0,
      hours: Number(bucket?.hours || 0),
      total: bucket?.total || 0,
      counts: bucket?.counts || {},
    })
  }
  return out
}

async function loadEmployees() {
  try {
    const res = await fetchEmployees('Active')
    employees.value = res || []
    if (!employee.value && employees.value.length) employee.value = employees.value[0].name
  } catch (err) {
    console.error('Failed to load the employees:', err)
    error.value = err.message || 'Failed to load the employees.'
  }
}

async function load() {
  if (!employee.value) {
    days.value = []
    return
  }
  busy.value = true
  error.value = ''
  try {
    const res = await fetchAttendanceSummary({
      fromDate: fromDate.value || null,
      toDate: toDate.value || null,
      groupBy: 'date',
      employee: employee.value,
    })
    days.value = buildDays(res?.buckets || [])
  } catch (err) {
    console.error('Failed to load the attendance summary:', err)
    error.value = err.message || 'Failed to load the attendance summary.'
    days.value = []
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await loadEmployees()
  await load()
})
</script>
