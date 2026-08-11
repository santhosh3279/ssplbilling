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
            Attendance counts per day or per employee, stacked by status.
          </p>
        </div>

        <button
          @click="load"
          :disabled="busy"
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
          <div>
            <label class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Group by</label>
            <select
              v-model="groupBy"
              @change="load"
              class="mt-1 block px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] text-sm font-semibold focus:outline-none focus:border-[var(--color-employee)]"
            >
              <option value="date">Day</option>
              <option value="employee">Employee</option>
            </select>
          </div>

          <button
            @click="load"
            :disabled="busy"
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
        <div v-if="buckets.length" class="mb-6 flex flex-wrap gap-3">
          <div
            v-for="status in statuses"
            :key="status"
            class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md"
          >
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              <span class="h-3 w-3 rounded-full" :style="{ background: colorFor(status) }"></span>
              {{ status }}
            </div>
            <div class="text-2xl font-black">{{ statusTotals[status] || 0 }}</div>
          </div>
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 shadow-md">
            <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Total records</div>
            <div class="text-2xl font-black">{{ grandTotal }}</div>
          </div>
        </div>

        <!-- Chart -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-md">
          <div v-if="!buckets.length && !busy" class="py-16 text-center text-sm text-[var(--color-text-muted)] italic">
            No attendance in this range.
          </div>

          <div v-else class="overflow-x-auto">
            <div class="flex items-end gap-3" :style="{ height: CHART_HEIGHT + 'px', minWidth: buckets.length * 44 + 'px' }">
              <div
                v-for="bucket in buckets"
                :key="bucket.key"
                class="flex flex-1 min-w-[32px] flex-col items-center justify-end gap-1 group"
              >
                <span class="text-[11px] font-bold text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ bucket.total }}
                </span>
                <!-- One stacked bar per status; heights are shares of the tallest bar. -->
                <div
                  class="flex w-full flex-col-reverse overflow-hidden rounded-t-lg"
                  :style="{ height: barHeight(bucket.total) + 'px' }"
                  :title="tooltip(bucket)"
                >
                  <div
                    v-for="status in statuses"
                    :key="status"
                    :style="{
                      height: segmentPercent(bucket, status) + '%',
                      background: colorFor(status),
                    }"
                  ></div>
                </div>
                <span class="h-16 w-full origin-top-right -rotate-45 truncate text-[10px] font-semibold text-[var(--color-text-muted)]">
                  {{ shortLabel(bucket.label) }}
                </span>
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
import { fetchAttendanceSummary } from '../api.js'

const CHART_HEIGHT = 320

// Known statuses keep a stable colour; anything else falls back to the grey.
const STATUS_COLORS = {
  Present: '#10b981',
  'Half Day': '#f59e0b',
  'Work From Home': '#3b82f6',
  'On Leave': '#8b5cf6',
  Absent: '#f43f5e',
}
const FALLBACK_COLOR = '#94a3b8'

const busy = ref(false)
const error = ref('')

const fromDate = ref(isoDate(startOfMonth()))
const toDate = ref(isoDate(new Date()))
const groupBy = ref('date')

const statuses = ref([])
const buckets = ref([])

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

const maxTotal = computed(() => buckets.value.reduce((max, b) => Math.max(max, b.total), 0))
const grandTotal = computed(() => buckets.value.reduce((sum, b) => sum + b.total, 0))

const statusTotals = computed(() => {
  const totals = {}
  for (const bucket of buckets.value) {
    for (const [status, count] of Object.entries(bucket.counts || {})) {
      totals[status] = (totals[status] || 0) + count
    }
  }
  return totals
})

function colorFor(status) {
  return STATUS_COLORS[status] || FALLBACK_COLOR
}

// The tallest bar fills the chart; a bar with any records never drops below 4px
// so a single record stays visible next to a busy day.
function barHeight(total) {
  if (!maxTotal.value || !total) return 0
  return Math.max(4, Math.round((total / maxTotal.value) * (CHART_HEIGHT - 40)))
}

function segmentPercent(bucket, status) {
  if (!bucket.total) return 0
  return ((bucket.counts?.[status] || 0) / bucket.total) * 100
}

function tooltip(bucket) {
  const parts = statuses.value
    .filter((s) => bucket.counts?.[s])
    .map((s) => `${s}: ${bucket.counts[s]}`)
  return `${bucket.label}\n${parts.join('\n')}\nTotal: ${bucket.total}`
}

function shortLabel(label) {
  if (groupBy.value === 'date') return String(label).slice(5) // MM-DD
  return String(label).length > 14 ? String(label).slice(0, 14) + '…' : label
}

async function load() {
  busy.value = true
  error.value = ''
  try {
    const res = await fetchAttendanceSummary({
      fromDate: fromDate.value || null,
      toDate: toDate.value || null,
      groupBy: groupBy.value,
    })
    statuses.value = res?.statuses || []
    buckets.value = res?.buckets || []
  } catch (err) {
    console.error('Failed to load the attendance summary:', err)
    error.value = err.message || 'Failed to load the attendance summary.'
    statuses.value = []
    buckets.value = []
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
