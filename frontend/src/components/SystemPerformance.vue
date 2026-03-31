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
            <div class="flex h-14 w-14 items-center justify-center rounded-full border-4" :class="ramBorderColor">
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
              <span v-if="clearing">Running...</span>
              <span v-else>🧹 Clear RAM Cache</span>
            </button>
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
            <div class="flex h-14 w-14 items-center justify-center rounded-full border-4" :class="cpuBorderColor">
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

        <!-- Terminal -->
        <div v-if="terminalVisible" class="rounded-xl border border-slate-600 bg-black overflow-hidden shadow-2xl">
          <!-- Title bar -->
          <div class="flex items-center gap-2 border-b border-slate-700 bg-slate-800 px-4 py-2">
            <span class="h-3 w-3 rounded-full bg-red-500"></span>
            <span class="h-3 w-3 rounded-full bg-amber-500"></span>
            <span class="h-3 w-3 rounded-full bg-emerald-500"></span>
            <span class="ml-2 text-[11px] font-semibold text-slate-400">bash — erpdev@server</span>
          </div>
          <!-- Output -->
          <div ref="terminalEl" class="min-h-32 max-h-72 overflow-y-auto p-4 font-mono text-[12px] leading-relaxed">
            <div v-for="(line, i) in terminalLines" :key="i">
              <!-- prompt + command line -->
              <div v-if="line.type === 'cmd'" class="flex">
                <span class="select-none text-emerald-400">erpdev@server:~$&nbsp;</span>
                <span class="text-slate-100">{{ line.text }}</span>
                <span v-if="i === terminalLines.length - 1 && line.typing" class="animate-pulse text-slate-100">▌</span>
              </div>
              <!-- stdout output -->
              <div v-else-if="line.type === 'out'" class="text-slate-300 whitespace-pre">{{ line.text }}</div>
              <!-- success -->
              <div v-else-if="line.type === 'ok'" class="text-emerald-400">{{ line.text }}</div>
              <!-- error -->
              <div v-else-if="line.type === 'err'" class="text-red-400">{{ line.text }}</div>
              <!-- blank -->
              <div v-else>&nbsp;</div>
            </div>
            <!-- idle cursor after all done -->
            <div v-if="terminalDone" class="flex">
              <span class="select-none text-emerald-400">erpdev@server:~$&nbsp;</span>
              <span class="animate-pulse text-slate-100">▌</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { dashboardApi } from '../services/dashboard.js'

const props = defineProps({
  show: { type: Boolean, default: false },
})
defineEmits(['close'])

const stats = ref({ ram_used_gb: 0, ram_total_gb: 0, ram_percent: 0, cpu_percent: 0 })
const clearing = ref(false)

// Terminal state
const terminalVisible = ref(false)
const terminalLines = ref([])
const terminalDone = ref(false)
const terminalEl = ref(null)

let pollInterval = null

// ── helpers ──────────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms))
}

async function scrollBottom() {
  await nextTick()
  if (terminalEl.value) terminalEl.value.scrollTop = terminalEl.value.scrollHeight
}

/** Push a command line with a typewriter effect, then resolve. */
async function typeCmd(text) {
  const line = { type: 'cmd', text: '', typing: true }
  terminalLines.value.push(line)
  await scrollBottom()
  for (const ch of text) {
    line.text += ch
    await sleep(28)
    await scrollBottom()
  }
  line.typing = false
}

/** Push an instant output line. */
async function pushLine(text, type = 'out') {
  terminalLines.value.push({ type, text })
  await scrollBottom()
  await sleep(60)
}

// ── main action ──────────────────────────────────────────────────────────────

async function clearRam() {
  clearing.value = true
  terminalVisible.value = true
  terminalLines.value = []
  terminalDone.value = false

  // Step 1 — sync
  await typeCmd('sync')
  await sleep(180)

  // Step 2 — drop caches (fire API while terminal is still "typing" next cmd)
  await typeCmd('echo 3 | sudo tee /proc/sys/vm/drop_caches')
  await sleep(120)

  let result = null
  try {
    result = await dashboardApi.clearRamCache()
  } catch (e) {
    result = { freed: false, error: String(e) }
  }

  if (result?.freed) {
    await pushLine('3')
  } else {
    await pushLine(result?.error || 'sudo: permission denied', 'err')
  }

  await sleep(120)

  // Step 3 — free -h
  await typeCmd('free -h')
  await sleep(180)

  if (result?.freed) {
    // Header row
    await pushLine('               total        used        free      shared  buff/cache   available')
    const total = result.ram_total_gb
    const used  = result.ram_used_gb
    const free  = Math.max(0, total - used).toFixed(1)
    await pushLine(
      `Mem:           ${String(total + 'Gi').padStart(6)}       ${String(used + 'Gi').padStart(6)}       ${String(free + 'Gi').padStart(6)}       0B         ~freed       ${String(free + 'Gi').padStart(6)}`
    )
    await pushLine('')
    await pushLine(`✔  Freed ~${result.freed_gb} GB  —  RAM now at ${result.ram_percent}%`, 'ok')

    // Update live stats
    stats.value = {
      ...stats.value,
      ram_used_gb: result.ram_used_gb,
      ram_total_gb: result.ram_total_gb,
      ram_percent: result.ram_percent,
    }
  } else {
    await pushLine('free: command output unavailable', 'err')
  }

  terminalDone.value = true
  clearing.value = false
  await scrollBottom()
}

// ── polling ──────────────────────────────────────────────────────────────────

async function fetchStats() {
  try {
    const d = await dashboardApi.getSystemStats()
    if (d) stats.value = d
  } catch { /* silent */ }
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
    terminalVisible.value = false
    terminalLines.value = []
    terminalDone.value = false
    startPolling()
  } else {
    stopPolling()
  }
})

onUnmounted(stopPolling)

// ── color helpers ─────────────────────────────────────────────────────────────

const ramColor      = computed(() => stats.value.ram_percent >= 80 ? 'text-red-400'     : stats.value.ram_percent >= 60 ? 'text-amber-400' : 'text-emerald-400')
const ramBarColor   = computed(() => stats.value.ram_percent >= 80 ? 'bg-red-500'       : stats.value.ram_percent >= 60 ? 'bg-amber-500'   : 'bg-emerald-500')
const ramBorderColor= computed(() => stats.value.ram_percent >= 80 ? 'border-red-500'   : stats.value.ram_percent >= 60 ? 'border-amber-500': 'border-emerald-500')
const cpuColor      = computed(() => stats.value.cpu_percent >= 80 ? 'text-red-400'     : stats.value.cpu_percent >= 60 ? 'text-amber-400' : 'text-emerald-400')
const cpuBarColor   = computed(() => stats.value.cpu_percent >= 80 ? 'bg-red-500'       : stats.value.cpu_percent >= 60 ? 'bg-amber-500'   : 'bg-emerald-500')
const cpuBorderColor= computed(() => stats.value.cpu_percent >= 80 ? 'border-red-500'   : stats.value.cpu_percent >= 60 ? 'border-amber-500': 'border-emerald-500')
</script>
