<template>
  <div v-if="show" class="fixed inset-0 z-[100] bg-[var(--color-bg)] flex flex-col">

    <!-- Header -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="$emit('close')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← Close
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-bold text-[var(--color-text)]">System Performance</h1>
        </div>
        <span class="text-[10px] text-[var(--color-text-muted)]">Refreshes every 10s</span>
      </div>
    </header>

    <!-- Body -->
    <div class="flex-1 overflow-auto px-10 py-10">
      <div class="mx-auto max-w-5xl space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          
          <!-- Left Column: Usage Stats -->
          <div class="space-y-6">
            <!-- RAM Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div class="mb-4 flex items-center justify-between">
                <div>
                  <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">RAM Usage</div>
                  <div class="mt-1 text-3xl font-black" :class="ramColor">
                    {{ stats.ram_percent }}%
                  </div>
                  <div class="text-sm text-[var(--color-text-muted)]">
                    {{ stats.ram_used_gb }} GB used of {{ stats.ram_total_gb }} GB
                  </div>
                </div>
                <div class="flex h-14 w-14 items-center justify-center rounded-full border-4" :class="ramBorderColor">
                  <span class="text-xl">💾</span>
                </div>
              </div>
              <div class="h-3 w-full overflow-hidden rounded-full bg-[var(--color-surface-raised)]">
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
                  class="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-semibold text-[var(--color-text)] transition hover:bg-[var(--color-surface-raised)] disabled:opacity-50"
                >
                  <span v-if="clearing">Running...</span>
                  <span v-else>🧹 Clear RAM Cache</span>
                </button>
              </div>
            </div>

            <!-- CPU Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div class="mb-4 flex items-center justify-between">
                <div>
                  <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">CPU Usage</div>
                  <div class="mt-1 text-3xl font-black" :class="cpuColor">
                    {{ stats.cpu_percent }}%
                  </div>
                  <div class="text-sm text-[var(--color-text-muted)]">Across all cores</div>
                </div>
                <div class="flex h-14 w-14 items-center justify-center rounded-full border-4" :class="cpuBorderColor">
                  <span class="text-xl">⚡</span>
                </div>
              </div>
              <div class="h-3 w-full overflow-hidden rounded-full bg-[var(--color-surface-raised)]">
                <div
                  class="h-full rounded-full transition-all duration-700"
                  :class="cpuBarColor"
                  :style="{ width: stats.cpu_percent + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Right Column: Site & Users -->
          <div class="space-y-6">
            <!-- Active Users Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div class="mb-4 flex items-center justify-between">
                <div>
                  <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Active Users</div>
                  <div class="mt-1 flex items-end gap-3">
                    <div>
                      <div class="text-3xl font-black text-[var(--color-success)]">{{ sessionData.unique_ips }}</div>
                      <div class="text-sm text-[var(--color-text-muted)]">{{ sessionData.unique_ips === 1 ? 'computer' : 'computers' }}</div>
                    </div>
                    <div class="mb-1 text-[var(--color-text-muted)]">/</div>
                    <div>
                      <div class="text-xl font-bold text-[var(--color-text)]">{{ sessionData.unique_users }}</div>
                      <div class="text-sm text-[var(--color-text-muted)]">{{ sessionData.unique_users === 1 ? 'user' : 'users' }}</div>
                    </div>
                  </div>
                  <div class="mt-1 text-[10px] text-[var(--color-text-muted)]">active in last 15 min</div>
                </div>
                <div class="flex h-14 w-14 items-center justify-center rounded-full border-4 border-[var(--color-success)]">
                  <span class="text-xl">👥</span>
                </div>
              </div>
              <div v-if="sessionData.sessions.length" class="space-y-1 mt-2">
                <div
                  v-for="s in sessionData.sessions"
                  :key="s.user + s.ip"
                  class="flex items-center justify-between rounded-lg bg-[var(--color-bg)]/60 px-3 py-2"
                >
                  <div class="flex items-center gap-2">
                    <span class="h-2 w-2 rounded-full bg-[var(--color-success)] shrink-0"></span>
                    <span class="text-xs font-semibold text-[var(--color-text)]">{{ s.user }}</span>
                  </div>
                  <span class="font-mono text-[10px] text-[var(--color-text-muted)]">{{ s.ip }}</span>
                </div>
              </div>
              <div v-else class="mt-2 text-xs text-[var(--color-text-muted)] text-center py-2">No active sessions</div>
            </div>

            <!-- Backup Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div class="mb-4 flex items-center justify-between">
                <div>
                  <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Site Backup</div>
                  <div class="mt-1 text-sm text-[var(--color-text)]">Run <span class="font-mono text-[11px] text-[var(--color-text-muted)]">frappe_backup.sh</span> manually</div>
                </div>
                <div class="flex h-14 w-14 items-center justify-center rounded-full border-4 border-[var(--color-info)]">
                  <span class="text-xl">💾</span>
                </div>
              </div>
              <div class="flex justify-end">
                <button
                  @click="runBackup"
                  :disabled="backing"
                  class="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-semibold text-[var(--color-text)] transition hover:bg-[var(--color-surface-raised)] disabled:opacity-50"
                >
                  <span v-if="backing">Backing up...</span>
                  <span v-else>📦 Manual Backup</span>
                </button>
              </div>
            </div>
          </div>

        </div>

        <!-- Terminal -->
        <div v-if="terminalVisible" class="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-2xl">
          <!-- Title bar -->
          <div class="flex items-center gap-2 border-b border-slate-200 bg-slate-100 px-4 py-2">
            <span class="h-3 w-3 rounded-full bg-red-500"></span>
            <span class="h-3 w-3 rounded-full bg-amber-500"></span>
            <span class="h-3 w-3 rounded-full bg-emerald-500"></span>
            <span class="ml-2 text-[11px] font-semibold text-slate-500">bash — {{ stats.terminal_user }}@{{ stats.terminal_host }}</span>
          </div>
          <!-- Output -->
          <div ref="terminalEl" @click="focusInput" class="min-h-32 max-h-72 overflow-y-auto p-4 font-mono text-[12px] leading-relaxed cursor-text text-slate-800">
            <div v-for="(line, i) in terminalLines" :key="i">
              <!-- prompt + command line -->
              <div v-if="line.type === 'cmd'" class="flex">
                <span class="select-none text-emerald-700 font-semibold">{{ stats.terminal_user }}@{{ stats.terminal_host }}:{{ shortCwd }}{{ promptSymbol }}&nbsp;</span>
                <span class="text-slate-900">{{ line.text }}</span>
                <span v-if="i === terminalLines.length - 1 && line.typing" class="animate-pulse text-slate-955">▌</span>
              </div>
              <!-- stdout output -->
              <div v-else-if="line.type === 'out'" class="text-slate-800 whitespace-pre">{{ line.text }}</div>
              <!-- success -->
              <div v-else-if="line.type === 'ok'" class="text-emerald-700 font-semibold">{{ line.text }}</div>
              <!-- error -->
              <div v-else-if="line.type === 'err'" class="text-rose-600 font-semibold">{{ line.text }}</div>
              <!-- blank -->
              <div v-else>&nbsp;</div>
            </div>
            <!-- Interactive input line -->
            <div v-if="terminalDone" class="flex items-center">
              <span class="select-none text-emerald-700 font-semibold">{{ stats.terminal_user }}@{{ stats.terminal_host }}:{{ shortCwd }}{{ promptSymbol }}&nbsp;</span>
              <input
                ref="inputEl"
                v-model="cmdInput"
                @keydown.enter="submitCmd"
                @keydown.up.prevent="navigateHistory('up')"
                @keydown.down.prevent="navigateHistory('down')"
                type="text"
                class="flex-1 bg-transparent text-slate-900 outline-none border-none p-0 font-mono text-[12px] focus:ring-0 focus:outline-none"
                placeholder=""
                autofocus
              />
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

const stats = ref({
  ram_used_gb: 0,
  ram_total_gb: 0,
  ram_percent: 0,
  cpu_percent: 0,
  is_docker: false,
  terminal_user: 'root',
  terminal_host: 'container'
})
const sessionData = ref({ sessions: [], unique_users: 0, unique_ips: 0 })
const clearing = ref(false)
const backing = ref(false)

// Terminal state
const terminalVisible = ref(true)
const terminalLines = ref([])
const terminalDone = ref(true)
const terminalEl = ref(null)

const cmdInput = ref('')
const inputEl = ref(null)
const cmdCwd = ref('/home/erpdev/frappe/frappe-bench-v16')
const cmdHistory = ref([])
const cmdHistoryIdx = ref(-1)

const shortCwd = computed(() => {
  const base = '/home/erpdev/frappe/frappe-bench-v16'
  if (cmdCwd.value === base) return '~'
  if (cmdCwd.value.startsWith(base)) {
    return '~' + cmdCwd.value.substring(base.length)
  }
  return cmdCwd.value
})

const promptSymbol = computed(() => stats.value.terminal_user === 'root' ? '#' : '$')

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

async function runBackup() {
  backing.value = true
  terminalVisible.value = true
  terminalLines.value = []
  terminalDone.value = false

  await typeCmd('sudo /opt/scripts/frappe_backup.sh')
  await pushLine('(running — this may take a minute...)', 'out')
  await scrollBottom()

  let result = null
  try {
    result = await dashboardApi.runManualBackup()
  } catch (e) {
    result = { success: false, stderr: String(e), stdout: '' }
  }

  // Print stdout lines
  if (result?.stdout) {
    for (const line of result.stdout.split('\n')) {
      await pushLine(line)
    }
  }

  // Print stderr lines
  if (result?.stderr) {
    for (const line of result.stderr.split('\n')) {
      await pushLine(line, result.success ? 'out' : 'err')
    }
  }

  if (result?.success) {
    await pushLine('')
    await pushLine('✔  Backup completed successfully', 'ok')
  } else {
    await pushLine('')
    await pushLine(`✘  Backup failed (exit code ${result?.returncode ?? '?'})`, 'err')
  }

  terminalDone.value = true
  backing.value = false
  await scrollBottom()
}

function focusInput() {
  if (inputEl.value) {
    inputEl.value.focus()
  }
}

async function submitCmd() {
  const cmd = cmdInput.value.trim()
  if (!cmd) return

  cmdInput.value = ''
  
  // Add to command history
  cmdHistory.value.push(cmd)
  cmdHistoryIdx.value = cmdHistory.value.length

  // Add command to output
  terminalLines.value.push({ type: 'cmd', text: cmd })
  await scrollBottom()

  if (cmd === 'clear') {
    terminalLines.value = []
    return
  }

  if (cmd === 'help') {
    terminalLines.value.push({
      type: 'out',
      text: 'Available commands:\n  cd <dir>  Change directory\n  clear     Clear terminal screen\n  help      Show this help message\n  Any standard shell command (ls, cat, whoami, ps, etc.)'
    })
    await scrollBottom()
    return
  }

  try {
    const res = await dashboardApi.runTerminalCommand(cmd, cmdCwd.value)
    if (res.cwd) {
      cmdCwd.value = res.cwd
    }
    if (res.stdout) {
      terminalLines.value.push({ type: 'out', text: res.stdout })
    }
    if (res.stderr) {
      terminalLines.value.push({ type: 'err', text: res.stderr })
    }
  } catch (e) {
    terminalLines.value.push({ type: 'err', text: `Error: ${e.message || e}` })
  }
  await scrollBottom()
}

function navigateHistory(direction) {
  if (cmdHistory.value.length === 0) return

  if (direction === 'up') {
    if (cmdHistoryIdx.value > 0) {
      cmdHistoryIdx.value--
      cmdInput.value = cmdHistory.value[cmdHistoryIdx.value]
    }
  } else if (direction === 'down') {
    if (cmdHistoryIdx.value < cmdHistory.value.length - 1) {
      cmdHistoryIdx.value++
      cmdInput.value = cmdHistory.value[cmdHistoryIdx.value]
    } else {
      cmdHistoryIdx.value = cmdHistory.value.length
      cmdInput.value = ''
    }
  }
}

// ── polling ──────────────────────────────────────────────────────────────────

async function fetchStats() {
  try {
    const d = await dashboardApi.getSystemStats()
    if (d) stats.value = d
  } catch { /* silent */ }
}

async function fetchSessions() {
  try {
    const d = await dashboardApi.getActiveSessions()
    if (d) sessionData.value = d
  } catch { /* silent */ }
}

function startPolling() {
  fetchStats()
  fetchSessions()
  pollInterval = setInterval(() => { fetchStats(); fetchSessions() }, 10000)
}

function stopPolling() {
  clearInterval(pollInterval)
  pollInterval = null
}

watch(() => props.show, (val) => {
  if (val) {
    terminalVisible.value = true
    terminalLines.value = [
      { type: 'out', text: 'Welcome to ERPNext Interactive Terminal.' },
      { type: 'out', text: 'Type "help" for a list of available commands.' }
    ]
    terminalDone.value = true
    cmdCwd.value = '/home/erpdev/frappe/frappe-bench-v16'
    cmdInput.value = ''
    startPolling()
    nextTick(() => {
      focusInput()
    })
  } else {
    stopPolling()
  }
})

onUnmounted(stopPolling)

// ── color helpers ─────────────────────────────────────────────────────────────

const ramColor      = computed(() => stats.value.ram_percent >= 80 ? 'text-[var(--color-danger)]'     : stats.value.ram_percent >= 60 ? 'text-[var(--color-warning)]' : 'text-[var(--color-success)]')
const ramBarColor   = computed(() => stats.value.ram_percent >= 80 ? 'bg-[var(--color-danger)]'       : stats.value.ram_percent >= 60 ? 'bg-[var(--color-warning)]'   : 'bg-[var(--color-success)]')
const ramBorderColor= computed(() => stats.value.ram_percent >= 80 ? 'border-[var(--color-danger)]'   : stats.value.ram_percent >= 60 ? 'border-[var(--color-warning)]': 'border-[var(--color-success)]')
const cpuColor      = computed(() => stats.value.cpu_percent >= 80 ? 'text-[var(--color-danger)]'     : stats.value.cpu_percent >= 60 ? 'text-[var(--color-warning)]' : 'text-[var(--color-success)]')
const cpuBarColor   = computed(() => stats.value.cpu_percent >= 80 ? 'bg-[var(--color-danger)]'       : stats.value.cpu_percent >= 60 ? 'bg-[var(--color-warning)]'   : 'bg-[var(--color-success)]')
const cpuBorderColor= computed(() => stats.value.cpu_percent >= 80 ? 'border-[var(--color-danger)]'   : stats.value.cpu_percent >= 60 ? 'border-[var(--color-warning)]': 'border-[var(--color-success)]')
</script>
