<template>
  <div v-if="show" class="fixed inset-0 z-[100] bg-slate-900 flex flex-col">

    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="$emit('close')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200"
          >
            ← Close
          </button>
          <span class="text-slate-600">|</span>
          <h1 class="text-sm font-bold text-slate-100">System Performance</h1>
        </div>
        <span class="text-[10px] text-slate-500">Refreshes every 10s</span>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-auto px-10 py-10">
      <div class="mx-auto max-w-lg space-y-6">

        <!-- RAM Card -->
        <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-xs font-bold uppercase tracking-wider text-slate-400">RAM Usage</div>
              <div class="mt-1 text-3xl font-black" :class="ramColor">
                {{ stats.ram_percent }}%
              </div>
              <div class="text-sm text-slate-400">
                {{ stats.ram_used_gb }} GB used of {{ stats.ram_total_gb }} GB
              </div>
            </div>
            <div class="flex h-14 w-14 items-center justify-center rounded-full border-4"
              :class="ramBorderColor"
            >
              <span class="text-xl">💾</span>
            </div>
          </div>
          <div class="h-3 w-full overflow-hidden rounded-full bg-slate-700">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="ramBarColor"
              :style="{ width: stats.ram_percent + '%' }"
            ></div>
          </div>
          <div class="mt-4 flex justify-end">
            <button
              @click="clearRam"
              :disabled="clearing"
              class="flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-600 disabled:opacity-50"
            >
              <span v-if="clearing">Clearing...</span>
              <span v-else>🧹 Clear RAM Cache</span>
            </button>
          </div>
          <div v-if="clearResult" class="mt-3 rounded-lg px-3 py-2 text-xs font-medium"
            :class="clearResult.freed ? 'bg-emerald-900/40 text-emerald-400' : 'bg-red-900/40 text-red-400'"
          >
            <span v-if="clearResult.freed">
              Freed {{ clearResult.freed_gb }} GB — RAM now at {{ clearResult.ram_percent }}%
            </span>
            <span v-else>
              Permission denied — process needs write access to /proc/sys/vm/drop_caches
            </span>
          </div>
        </div>

        <!-- CPU Card -->
        <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-xs font-bold uppercase tracking-wider text-slate-400">CPU Usage</div>
              <div class="mt-1 text-3xl font-black" :class="cpuColor">
                {{ stats.cpu_percent }}%
              </div>
              <div class="text-sm text-slate-400">Across all cores</div>
            </div>
            <div class="flex h-14 w-14 items-center justify-center rounded-full border-4"
              :class="cpuBorderColor"
            >
              <span class="text-xl">⚡</span>
            </div>
          </div>
          <div class="h-3 w-full overflow-hidden rounded-full bg-slate-700">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="cpuBarColor"
              :style="{ width: stats.cpu_percent + '%' }"
            ></div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { dashboardApi } from '../services/dashboard.js'

const props = defineProps({
  show: { type: Boolean, default: false },
})
defineEmits(['close'])

const stats = ref({ ram_used_gb: 0, ram_total_gb: 0, ram_percent: 0, cpu_percent: 0 })
const clearing = ref(false)
const clearResult = ref(null)
let pollInterval = null

async function fetchStats() {
  try {
    const d = await dashboardApi.getSystemStats()
    if (d) stats.value = d
  } catch { /* silent */ }
}

async function clearRam() {
  clearing.value = true
  clearResult.value = null
  try {
    const d = await dashboardApi.clearRamCache()
    if (d) {
      clearResult.value = d
      stats.value = {
        ...stats.value,
        ram_used_gb: d.ram_used_gb,
        ram_total_gb: d.ram_total_gb,
        ram_percent: d.ram_percent,
      }
    }
  } catch (e) {
    clearResult.value = { freed: false }
  } finally {
    clearing.value = false
  }
}

function startPolling() {
  fetchStats()
  pollInterval = setInterval(fetchStats, 10000)
}

function stopPolling() {
  clearInterval(pollInterval)
  pollInterval = null
}

watch(() => props.show, (val) => {
  if (val) {
    clearResult.value = null
    startPolling()
  } else {
    stopPolling()
  }
})

onUnmounted(stopPolling)

// Color helpers
const ramColor = computed(() => stats.value.ram_percent >= 80 ? 'text-red-400' : stats.value.ram_percent >= 60 ? 'text-amber-400' : 'text-emerald-400')
const ramBarColor = computed(() => stats.value.ram_percent >= 80 ? 'bg-red-500' : stats.value.ram_percent >= 60 ? 'bg-amber-500' : 'bg-emerald-500')
const ramBorderColor = computed(() => stats.value.ram_percent >= 80 ? 'border-red-500' : stats.value.ram_percent >= 60 ? 'border-amber-500' : 'border-emerald-500')
const cpuColor = computed(() => stats.value.cpu_percent >= 80 ? 'text-red-400' : stats.value.cpu_percent >= 60 ? 'text-amber-400' : 'text-emerald-400')
const cpuBarColor = computed(() => stats.value.cpu_percent >= 80 ? 'bg-red-500' : stats.value.cpu_percent >= 60 ? 'bg-amber-500' : 'bg-emerald-500')
const cpuBorderColor = computed(() => stats.value.cpu_percent >= 80 ? 'border-red-500' : stats.value.cpu_percent >= 60 ? 'border-amber-500' : 'border-emerald-500')
</script>
