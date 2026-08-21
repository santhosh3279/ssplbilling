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
            Working hours per day for one employee. Each block is a stretch between two
            punches, so the gaps are the breaks. Sundays are marked in orange.
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
              class="mt-1 block min-w-[220px] px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)]"
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
              class="mt-1 block px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
            <input
              v-model="toDate"
              type="date"
              class="mt-1 block px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-[21px] leading-6 font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            />
          </div>

          <button
            @click="load"
            :disabled="busy || !employee"
            class="rounded-xl bg-[var(--color-employee)] text-white px-4 py-2 text-[21px] leading-6 font-bold hover:brightness-110 disabled:opacity-50"
          >
            Apply
          </button>

          <div class="ml-auto flex gap-2">
            <button
              v-for="preset in presets"
              :key="preset.label"
              @click="applyPreset(preset)"
              class="rounded-xl border border-[var(--color-border)] px-3 py-2 text-[18px] leading-5 font-bold hover:bg-[var(--color-midlight)]"
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
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            :title="`First punch to last punch across the ${hourBalance.presentDays} present day(s), with the ` +
              `tail cut at the shift end (${formatHour(shiftEnd)}) and the mid-day exits deducted. ` +
              `${hourBalance.expected.toFixed(2)}h were owed. Today is left out — it is still running.`"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Shift hours on present days</div>
            <div class="text-2xl font-black">{{ hourBalance.shiftHours.toFixed(2) }}</div>
            <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              of {{ hourBalance.expected.toFixed(2) }} owed
            </div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            :title="`Time punched after the shift end (${formatHour(shiftEnd)}), summed over the present days ` +
              `before today`"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Extra hours</div>
            <div class="text-2xl font-black text-emerald-500">{{ hourBalance.extra.toFixed(2) }}</div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            :title="`Shift hours left unworked on the ${hourBalance.missingDays} present day(s) that carry more than ` +
              `two punches — the mid-day exits. Overtime is not netted off here. Days with a single in/out ` +
              `pair and today are left out.`"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Absent hours on present days</div>
            <div class="text-2xl font-black text-rose-500">{{ hourBalance.missing.toFixed(2) }}</div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            title="Absent hours less extra hours — what is still owed once the overtime is set against the shortfall"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Net (absent − extra)
            </div>
            <div
              class="text-2xl font-black"
              :class="hourBalance.net > 0 ? 'text-rose-500' : 'text-emerald-500'"
            >
              {{ hourBalance.net < 0 ? '−' : '' }}{{ Math.abs(hourBalance.net).toFixed(2) }}
            </div>
            <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              {{ hourBalance.net > 0 ? 'owed' : hourBalance.net < 0 ? 'ahead' : 'level' }}
            </div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            :title="`Days worked at least the shift length (${shiftLength.toFixed(2)}h)`"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Full days</div>
            <div class="text-2xl font-black text-emerald-500">{{ dayStats.fullDays }}</div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            title="Days holding one continuous break of an hour or more"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Days with 1h break</div>
            <div class="text-2xl font-black">{{ dayStats.breakDays }}</div>
          </div>
          <div
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
            title="Days the Attendance record is marked Half Day"
          >
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Half days</div>
            <div class="text-2xl font-black text-amber-500">{{ dayStats.halfDays }}</div>
          </div>
          <div class="flex items-center gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full" :style="{ background: WEEKDAY_COLOR }"></span> Weekday
            </span>
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full" :style="{ background: SUNDAY_COLOR }"></span> Sunday
            </span>
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-sm border border-dashed border-rose-500/60 hatch-absent"></span> Absent
            </span>
            <span class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-sm hatch-overtime" :style="{ background: WEEKDAY_COLOR }"></span> Overtime
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
            <div class="flex" :style="{ minWidth: processedDays.length * 52 + 60 + 'px' }">
              <!-- Y axis: working hours. The spacer keeps the ticks level with the
                   plot band, which starts below the row of hour labels. -->
              <div class="w-12 shrink-0">
                <div :style="{ height: LABEL_HEIGHT + 'px' }"></div>
                <div class="relative" :style="{ height: PLOT_HEIGHT + 'px' }">
                  <div
                    v-for="tick in yTicks"
                    :key="tick"
                    class="absolute right-2 -translate-y-1/2 text-[10px] font-bold text-[var(--color-text-muted)]"
                    :style="{ bottom: ((tick - shiftStart) / (yMax - shiftStart)) * PLOT_HEIGHT + 'px' }"
                  >
                    {{ formatHour(tick) }}
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
                    :style="{ bottom: ((tick - shiftStart) / (yMax - shiftStart)) * PLOT_HEIGHT + 'px' }"
                  ></div>

                  <!-- Shift End reference line -->
                  <div
                    class="absolute inset-x-0 border-t-2 border-red-500/40 z-10"
                    :style="{ bottom: ((shiftEnd - shiftStart) / (yMax - shiftStart)) * PLOT_HEIGHT + 'px' }"
                  >
                    <span class="bg-red-500 text-white px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider absolute left-2 -translate-y-1/2 shadow-sm">
                      Shift End ({{ formatHour(shiftEnd) }})
                    </span>
                  </div>
                </div>

                <div class="flex items-end gap-2">
                  <div
                    v-for="day in processedDays"
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
                    <div class="relative w-full" :style="{ height: PLOT_HEIGHT + 'px' }">
                      <!-- A day nobody worked: hollow across the shift, so the gap is
                           visible without pretending hours were logged -->
                      <div
                        v-if="day.absent"
                        class="absolute w-full rounded-lg border-2 border-dashed border-rose-500/50 hatch-absent"
                        :style="{ bottom: day.absentBottomPx + 'px', height: day.absentHeightPx + 'px' }"
                        :title="tooltip(day)"
                      ></div>

                      <!-- One block per worked stretch; the gaps between them are the
                           breaks the employee punched out for -->
                      <div
                        v-for="(block, bi) in day.blocks"
                        :key="bi"
                        class="absolute w-full rounded-lg transition-all"
                        :class="block.overtime ? 'hatch-overtime' : ''"
                        :style="{
                          bottom: block.bottomPx + 'px',
                          height: block.heightPx + 'px',
                          backgroundColor: day.sunday ? SUNDAY_COLOR : WEEKDAY_COLOR,
                        }"
                        :title="tooltip(day)"
                      ></div>

                      <!-- An unpaired punch has no stretch to sit in, so it is drawn as
                           the single reading it is -->
                      <div
                        v-for="(tick, ti) in day.ticks"
                        :key="'t' + ti"
                        class="absolute w-full border-t-2 border-dotted"
                        :style="{ bottom: tick + 'px', borderColor: day.sunday ? SUNDAY_COLOR : WEEKDAY_COLOR }"
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
import { fetchAttendanceSummary, fetchEmployees, fetchEmployeeCheckinDays } from '../api.js'

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
// { '2026-08-12': [{ hours: 9.5, auto: 0 }, ...] } — the punches behind each bar
const punchesByDate = ref({})
const todayIso = isoDate(new Date())

// Each preset returns the [from, to] it selects. Last month is a calendar month,
// not the trailing 30 days — payroll is run on the month, so the two differ.
const presets = [
  { label: 'This month', range: () => [startOfMonth(), new Date()] },
  { label: 'Last month', range: () => lastMonth() },
  { label: 'Last 7 days', range: () => [daysBack(7), new Date()] },
  { label: 'Last 30 days', range: () => [daysBack(30), new Date()] },
]

function startOfMonth() {
  const d = new Date()
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function lastMonth() {
  const d = new Date()
  // Day 0 of this month is the last day of the previous one
  return [new Date(d.getFullYear(), d.getMonth() - 1, 1), new Date(d.getFullYear(), d.getMonth(), 0)]
}

function daysBack(n) {
  const d = new Date()
  d.setDate(d.getDate() - (n - 1))
  return d
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
  const [start, end] = preset.range()
  fromDate.value = isoDate(start)
  toDate.value = isoDate(end)
  load()
}

const totalHours = computed(() => days.value.reduce((sum, d) => sum + d.hours, 0))
const markedDays = computed(() => days.value.filter((d) => d.total > 0).length)

// The shift's own length, which is what a full day is measured against
const shiftLength = computed(() => Math.max(0, shiftEnd.value - shiftStart.value))

// A day only owes shift hours if the employee actually turned up. Statuses come from
// the Attendance record; a day carrying hours but no status still counts as worked.
const PRESENT_STATUSES = ['Present', 'Half Day', 'Work From Home']

// Device clocks drift a minute or two either way, so anything under this reads as
// having hit the shift exactly rather than as a surplus or a shortfall.
const HOUR_SLACK = 0.02

// Time actually spent on the clock inside the shift: first punch to last punch,
// with the tail cut at the shift end so overtime stays out, and the mid-day exits
// dropped because only the entry-to-exit pairs are summed.
function inShiftHours(day, sEnd, shift) {
  const punches = punchesByDate.value[day.date] || []

  if (punches.length >= 2) {
    // Even index is an entry, odd its exit — the pairing the sync and the bars use
    let total = 0
    for (let i = 0; i + 1 < punches.length; i += 2) {
      const start = punches[i].hours
      const end = Math.min(punches[i + 1].hours, sEnd)
      if (end > start) total += end - start
    }
    return total
  }

  // A hand-written Attendance has no punches, so its own window is all there is;
  // the break inside it is unknowable and simply not deducted.
  const { inHours, outHours } = getDayTimes(day)
  if (inHours !== null && outHours !== null) {
    return Math.max(0, Math.min(outHours, sEnd) - inHours)
  }
  return Math.min(day.hours || 0, shift)
}

// The mirror of inShiftHours: only the part of each worked stretch that runs past
// the shift end, so a late checkout counts and the breaks before it do not.
function overtimeHours(day, sEnd) {
  const punches = punchesByDate.value[day.date] || []

  if (punches.length >= 2) {
    let total = 0
    for (let i = 0; i + 1 < punches.length; i += 2) {
      const start = Math.max(punches[i].hours, sEnd)
      const end = punches[i + 1].hours
      if (end > start) total += end - start
    }
    return total
  }

  const { outHours } = getDayTimes(day)
  return outHours !== null ? Math.max(0, outHours - sEnd) : 0
}

const hourBalance = computed(() => {
  const shift = shiftLength.value
  const sEnd = shiftEnd.value
  let presentDays = 0
  let shiftHours = 0
  let expected = 0
  let extra = 0
  let missing = 0
  let missingDays = 0

  for (const day of days.value) {
    // Today is still running — its punches are half in, so it would read as a
    // shortfall every morning. Anything dated later is not owed yet either.
    if (day.date >= todayIso) continue

    const counts = day.counts || {}
    if (!PRESENT_STATUSES.some((status) => counts[status]) && !(day.hours > 0)) continue

    presentDays += 1
    // Half Day owes half the shift, so a half day worked in full is not a shortfall
    const owed = counts['Half Day'] ? shift / 2 : shift
    expected += owed

    // Both figures come off the punches now, split at the shift end: what was worked
    // inside the shift, and what was worked past it. A day can hold both — a late
    // checkout does not cancel a long lunch.
    const worked = inShiftHours(day, sEnd, owed)
    shiftHours += worked
    extra += overtimeHours(day, sEnd)

    // The shortfall is what the shift went unworked, measured against the in-shift
    // figure so overtime cannot paper over it. It only counts once the day has more
    // than the opening in/out pair: two punches mean the employee never stepped out
    // and the gap is just a short shift, not time taken off.
    const short = owed - worked
    if (short > HOUR_SLACK && (punchesByDate.value[day.date] || []).length > 2) {
      missing += short
      missingDays += 1
    }
  }

  // Positive = hours still owed after the overtime is set against them; negative =
  // the employee is ahead. Kept signed so the tile can colour and word itself.
  const net = missing - extra

  return { presentDays, shiftHours, expected, extra, missing, missingDays, net }
})

// The longest continuous break of a day, in hours. Only the odd-indexed gaps are
// breaks: the day opens with an entry, so those are the gaps that follow a
// completed pair — the even ones are the worked stretches themselves.
function longestBreak(punches) {
  let longest = 0
  for (let i = 1; i + 1 < punches.length; i += 2) {
    longest = Math.max(longest, punches[i + 1].hours - punches[i].hours)
  }
  return longest
}

const dayStats = computed(() => {
  // Device clocks put a full day a minute or two under the shift, so the comparison
  // needs a little slack or nothing ever counts as full.
  const full = Math.max(0, shiftLength.value - 0.02)
  let fullDays = 0
  let breakDays = 0
  let halfDays = 0
  for (const day of days.value) {
    if (full > 0 && day.hours >= full) fullDays += 1
    if (longestBreak(punchesByDate.value[day.date] || []) >= 1) breakDays += 1
    if ((day.counts || {})['Half Day']) halfDays += 1
  }
  return { fullDays, breakDays, halfDays }
})

function timeToHours(timeStr) {
  if (!timeStr) return null
  const parts = timeStr.includes(' ') ? timeStr.split(' ')[1].split(':') : timeStr.split(':')
  if (parts.length < 2) return null
  const h = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10)
  const s = parts[2] ? parseInt(parts[2], 10) : 0
  return h + m / 60 + s / 3600
}

function formatHour(h) {
  const hrs = Math.floor(h)
  const mins = Math.round((h - hrs) * 60)
  return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

const shiftStart = computed(() => {
  const dayWithShift = days.value.find(d => d.shift_start)
  return dayWithShift ? timeToHours(dayWithShift.shift_start) : 9.5 // default 09:30
})

const shiftEnd = computed(() => {
  const dayWithShift = days.value.find(d => d.shift_end)
  return dayWithShift ? timeToHours(dayWithShift.shift_end) : 18.5 // default 18:30
})

const maxOutTime = computed(() => {
  let maxVal = shiftEnd.value
  for (const day of days.value) {
    if (day.out_time) {
      const outHours = timeToHours(day.out_time)
      if (outHours && outHours > maxVal) {
        maxVal = outHours
      }
    }
  }
  return maxVal
})

const yMax = computed(() => Math.ceil(maxOutTime.value + 1))

const yTicks = computed(() => {
  const start = shiftStart.value
  const end = yMax.value
  const ticks = []
  for (let h = start; h <= end; h += 1) {
    ticks.push(h)
  }
  return ticks
})

function getDayTimes(day) {
  let inH = null
  let outH = null
  if (day.in_time) {
    inH = timeToHours(day.in_time)
  }
  if (day.out_time) {
    outH = timeToHours(day.out_time)
  }
  
  if (day.hours > 0) {
    if (inH === null && outH === null) {
      inH = shiftStart.value
      outH = shiftStart.value + day.hours
    } else if (inH === null) {
      inH = Math.max(shiftStart.value, outH - day.hours)
    } else if (outH === null) {
      outH = inH + day.hours
    }
  }
  return { inHours: inH, outHours: outH }
}

// One drawn block per worked stretch. A stretch that runs past the shift end is cut
// in two so only the overtime part carries the hatch.
function buildBlocks(fromH, toH, sEnd, sStart, range) {
  const blocks = []
  const push = (a, b, overtime) => {
    if (b <= a) return
    blocks.push({
      bottomPx: Math.round((Math.max(0, a - sStart) / range) * PLOT_HEIGHT),
      heightPx: Math.max(3, Math.round(((b - a) / range) * PLOT_HEIGHT)),
      overtime,
    })
  }
  push(fromH, Math.min(toH, sEnd), false)
  push(Math.max(fromH, sEnd), toH, true)
  return blocks
}

const processedDays = computed(() => {
  const sStart = shiftStart.value
  const sEnd = shiftEnd.value
  const range = yMax.value - sStart
  if (range <= 0) return []

  return days.value.map(day => {
    const { inHours, outHours } = getDayTimes(day)
    const punches = punchesByDate.value[day.date] || []

    let blocks = []
    // Ticks for punches that no block edge already shows — an odd punch count leaves
    // the last one unpaired, and it would otherwise vanish from the chart entirely.
    let ticks = []

    if (punches.length >= 2) {
      // Even index is an entry, odd its exit — the same pairing the sync uses for
      // working_hours, so the gaps drawn here are the breaks it excluded.
      for (let i = 0; i + 1 < punches.length; i += 2) {
        blocks = blocks.concat(buildBlocks(punches[i].hours, punches[i + 1].hours, sEnd, sStart, range))
      }
      if (punches.length % 2 === 1) {
        const last = punches[punches.length - 1]
        ticks.push(Math.round((Math.max(0, last.hours - sStart) / range) * PLOT_HEIGHT))
      }
    } else if (day.hours > 0 && inHours !== null && outHours !== null) {
      // No punches recorded (a hand-written Attendance), so the outer window is all
      // there is to draw.
      blocks = buildBlocks(inHours, outHours, sEnd, sStart, range)
    } else if (punches.length === 1) {
      ticks.push(Math.round((Math.max(0, punches[0].hours - sStart) / range) * PLOT_HEIGHT))
    }

    // A day the employee did not work, drawn hollow across the shift so the gap in
    // the month reads as absence rather than as missing data. Sundays are left blank
    // — nobody is expected in — and so is anything still in the future.
    const absent = !blocks.length && !ticks.length && !day.sunday && day.date <= todayIso

    return {
      ...day,
      inHours,
      outHours,
      punches,
      blocks,
      ticks,
      absent,
      absentBottomPx: 0,
      absentHeightPx: Math.max(3, Math.round(((sEnd - sStart) / range) * PLOT_HEIGHT)),
    }
  })
})

function tooltip(day) {
  const parts = Object.entries(day.counts || {}).map(([status, count]) => `${status}: ${count}`)
  const punches = (day.punches || []).map((p) => formatHour(p.hours) + (p.auto ? ' (auto)' : ''))
  const lines = [`${day.date} (${day.weekday})`, `${day.hours.toFixed(2)} hours`, ...parts]
  if (punches.length) lines.push(`Punches: ${punches.join(' · ')}`)
  return lines.join('\n')
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
      shift: bucket?.shift || null,
      shift_start: bucket?.shift_start || null,
      shift_end: bucket?.shift_end || null,
      in_time: bucket?.in_time || null,
      out_time: bucket?.out_time || null,
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
    const [res, punches] = await Promise.all([
      fetchAttendanceSummary({
        fromDate: fromDate.value || null,
        toDate: toDate.value || null,
        groupBy: 'date',
        employee: employee.value,
      }),
      fetchEmployeeCheckinDays({
        employee: employee.value,
        fromDate: fromDate.value,
        toDate: toDate.value,
      }),
    ])
    const grouped = {}
    ;(punches || []).forEach((p) => {
      const hours = timeToHours(p.time)
      if (hours === null) return
      if (!grouped[p.date]) grouped[p.date] = []
      grouped[p.date].push({ hours, auto: p.auto })
    })
    punchesByDate.value = grouped
    days.value = buildDays(res?.buckets || [])
  } catch (err) {
    console.error('Failed to load the attendance summary:', err)
    error.value = err.message || 'Failed to load the attendance summary.'
    days.value = []
    punchesByDate.value = {}
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await loadEmployees()
  await load()
})
</script>

<style scoped>
.hatch-overtime {
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(0, 0, 0, 0.3) 0px,
    rgba(0, 0, 0, 0.3) 2px,
    transparent 2px,
    transparent 8px
  );
}

/* Hollow on purpose — no fill colour, only the hatch and the dashed outline */
.hatch-absent {
  background-image: repeating-linear-gradient(
    -45deg,
    rgba(244, 63, 94, 0.28) 0px,
    rgba(244, 63, 94, 0.28) 2px,
    transparent 2px,
    transparent 8px
  );
}
</style>
