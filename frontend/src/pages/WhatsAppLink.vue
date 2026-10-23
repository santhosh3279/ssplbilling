<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">WhatsApp Link</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">OpenWA Gateway</p>
        </div>
      </div>
      <span class="rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider" :class="badge.cls">
        {{ badge.label }}
      </span>
    </header>

    <main class="flex-1 overflow-y-auto p-6 text-[var(--color-text)]">
      <div v-if="loading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
        <span class="text-xl animate-pulse">Loading…</span>
      </div>

      <div v-else class="mx-auto grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Gateway settings -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Gateway</h2>

          <div>
            <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Gateway URL</label>
            <input v-model="form.base_url" type="text" placeholder="http://127.0.0.1:2785" :class="inputCls" />
            <p class="mt-1 text-xs text-[var(--color-text-muted)]">Where OpenWA listens, as seen from the ERPNext server. No <span class="font-mono">/api</span> suffix.</p>
          </div>

          <div>
            <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">API Key</label>
            <input
              v-model="form.api_key"
              type="password"
              autocomplete="new-password"
              :placeholder="hasApiKey ? '•••••••• saved — type to replace' : 'owa_k1_…'"
              :class="inputCls"
            />
            <p class="mt-1 text-xs text-[var(--color-text-muted)]">Unscoped OPERATOR key from the OpenWA dashboard. Stored encrypted; never sent back to the browser.</p>
          </div>

          <div class="flex justify-end">
            <button
              @click="save"
              :disabled="busy"
              class="rounded-lg bg-[var(--color-info)] px-6 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ busy === 'save' ? 'Saving…' : 'Save' }}
            </button>
          </div>
        </section>

        <!-- Sessions: one per user, plus the shared one for users without their own -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Sessions</h2>

          <div v-if="!sessions.length" class="rounded-lg bg-[var(--color-surface-raised)] p-4 text-sm text-[var(--color-text-muted)]">
            No sessions yet. Add one below, then Connect it.
          </div>
          <div v-else class="space-y-2">
            <button
              v-for="s in sessions"
              :key="s.session_name"
              @click="select(s.session_name)"
              :disabled="!!busy"
              class="flex w-full items-center justify-between gap-3 rounded-lg p-3 text-left transition-colors disabled:cursor-not-allowed"
              :class="s.session_name === selected ? 'bg-[var(--color-info)]/15' : 'bg-[var(--color-surface-raised)] hover:bg-[var(--color-info)]/10'"
            >
              <span class="min-w-0">
                <span class="block truncate text-sm font-bold">{{ s.session_name }}</span>
                <span class="block truncate text-xs text-[var(--color-text-muted)]">
                  {{ s.user ? userLabel(s.user) : 'Shared — everyone without their own' }}
                </span>
              </span>
              <span class="shrink-0 text-right text-xs">
                <span class="block font-mono">{{ s.phone ? '+' + s.phone : '' }}</span>
                <span class="block text-[var(--color-text-muted)]">{{ s.status || 'not linked' }}</span>
              </span>
            </button>
          </div>

          <div class="grid grid-cols-1 gap-3 border-t border-[var(--color-border)] pt-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">User</label>
              <select v-model="newSession.user" :class="inputCls">
                <option value="">Shared</option>
                <option v-for="u in users" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Session Name</label>
              <select v-model="newSession.pick" :class="inputCls">
                <option value="" disabled>Select a session</option>
                <option v-for="n in freeGatewaySessions" :key="n" :value="n">{{ n }}</option>
                <option :value="NEW_SESSION">New session…</option>
              </select>
              <input
                v-if="newSession.pick === NEW_SESSION"
                v-model="newSession.session_name"
                type="text"
                placeholder="sspl-billing"
                :class="[inputCls, 'mt-2']"
                @keydown.enter="addSession"
              />
            </div>
            <button
              @click="addSession"
              :disabled="!!busy || !newSessionName"
              class="rounded-lg bg-[var(--color-info)] px-5 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ busy === 'add' ? 'Adding…' : 'Add' }}
            </button>
          </div>
          <p class="text-xs text-[var(--color-text-muted)]">Pick a session already on the gateway, or start a new one: 3-50 letters, numbers or hyphens. Each session links its own WhatsApp number.</p>
        </section>

        <!-- Link status / QR -->
        <section v-if="selected" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4 lg:col-span-2">
          <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Linked Number · {{ selected }}</h2>

          <div v-if="state.status === 'ready'" class="rounded-lg bg-[var(--color-success)]/15 p-4">
            <div class="text-2xl font-bold font-mono">+{{ state.phone }}</div>
            <div class="text-sm text-[var(--color-text-muted)]">{{ state.push_name || 'WhatsApp account' }}</div>
          </div>

          <div v-else-if="state.qr" class="flex flex-col items-center gap-3">
            <img :src="state.qr" alt="WhatsApp QR" class="h-64 w-64 rounded-lg bg-white p-2" />
            <ol class="list-decimal pl-5 text-sm text-[var(--color-text-muted)] space-y-1">
              <li>Open WhatsApp on the phone that will send bills.</li>
              <li>Settings → <b>Linked devices</b> → <b>Link a device</b>.</li>
              <li>Scan this code. It refreshes every few seconds.</li>
            </ol>
          </div>

          <div v-else class="rounded-lg bg-[var(--color-surface-raised)] p-4 text-sm text-[var(--color-text-muted)]">
            {{ statusHint }}
          </div>

          <p v-if="state.last_error" class="rounded-lg bg-[var(--color-danger)]/15 p-3 text-sm text-[var(--color-danger)]">{{ state.last_error }}</p>
          <p v-if="state.restriction" class="rounded-lg bg-[var(--color-warning)]/15 p-3 text-sm">
            WhatsApp restriction: {{ state.restriction.kind }} ({{ state.restriction.code }})
          </p>

          <div class="flex flex-wrap gap-3">
            <button
              v-if="!state.engine_loaded"
              @click="run('connect')"
              :disabled="!!busy || !hasApiKey"
              class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ busy === 'connect' ? 'Starting…' : 'Connect' }}
            </button>
            <button
              v-if="state.engine_loaded"
              @click="run('disconnect')"
              :disabled="!!busy"
              class="rounded-lg bg-[var(--color-surface-raised)] px-5 py-2 text-sm font-semibold transition-all active:scale-95 disabled:opacity-50"
            >
              {{ busy === 'disconnect' ? 'Stopping…' : 'Stop' }}
            </button>
            <button
              v-if="state.engine_loaded && state.status === 'ready'"
              @click="confirmLogout"
              :disabled="!!busy"
              class="rounded-lg bg-[var(--color-danger)]/15 px-5 py-2 text-sm font-semibold text-[var(--color-danger)] transition-all active:scale-95 disabled:opacity-50"
            >
              {{ busy === 'logout' ? 'Unlinking…' : 'Unlink Number' }}
            </button>
            <button
              @click="refresh"
              :disabled="!!busy"
              class="rounded-lg px-4 py-2 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] disabled:opacity-50"
            >
              ↻ Refresh
            </button>
            <button
              @click="confirmRemove"
              :disabled="!!busy"
              class="ml-auto rounded-lg px-4 py-2 text-sm font-semibold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/15 disabled:opacity-50"
            >
              Remove Session
            </button>
          </div>
        </section>

        <!-- Test send -->
        <section v-if="selected" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4 lg:col-span-2">
          <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Test Message · {{ selected }}</h2>
          <div class="grid grid-cols-1 gap-4 md:grid-cols-[220px_1fr_auto] md:items-end">
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Mobile</label>
              <input v-model="test.phone" type="tel" placeholder="98xxxxxxxx" :class="inputCls" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Text</label>
              <input v-model="test.text" type="text" :class="inputCls" @keydown.enter="sendTest" />
            </div>
            <button
              @click="sendTest"
              :disabled="!!busy || state.status !== 'ready' || !test.phone || !test.text"
              class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ busy === 'test' ? 'Sending…' : 'Send' }}
            </button>
          </div>
          <p class="text-xs text-[var(--color-text-muted)]">
            10-digit numbers get +91. Every send is recorded in <span class="font-mono">SSPL WhatsApp Log</span>; "Sent" there means OpenWA accepted it, not that it was delivered.
          </p>
        </section>

        <p v-if="message" class="lg:col-span-2 rounded-lg p-3 text-sm" :class="messageIsError ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'">
          {{ message }}
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.whatsapp_api'
// OpenWA rotates the QR roughly every 20s; polling faster keeps the shown one scannable
const POLL_MS = 3000
// Statuses that move on their own, so the page keeps asking until they settle
const TRANSIENT = new Set(['initializing', 'qr_ready', 'authenticating'])

const router = useRouter()
const inputCls =
  'w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:bg-[var(--color-info)]/15 focus:outline-none'

const loading = ref(true)
const busy = ref('')
const hasApiKey = ref(false)
const message = ref('')
const messageIsError = ref(false)
const form = reactive({ base_url: '', api_key: '' })
const sessions = ref([])
const users = ref([])
const selected = ref('')
const NEW_SESSION = '__new__'
const newSession = reactive({ user: '', pick: '', session_name: '' })
const gatewaySessions = ref([])
// Gateway sessions no row uses yet; a name can belong to one row only
const freeGatewaySessions = computed(() =>
  gatewaySessions.value.filter((n) => !sessions.value.some((x) => x.session_name === n)),
)
const newSessionName = computed(() =>
  newSession.pick === NEW_SESSION ? newSession.session_name.trim() : newSession.pick,
)
const state = reactive({ status: '', phone: '', push_name: '', engine_loaded: false, qr: '', last_error: '', restriction: null })
const test = reactive({ phone: '', text: 'Test message from SSPL Billing' })

let pollTimer = null
let unmounted = false

const badge = computed(() => {
  if (state.status === 'ready') return { label: 'Connected', cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' }
  if (state.status === 'qr_ready') return { label: 'Scan QR', cls: 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]' }
  if (TRANSIENT.has(state.status)) return { label: 'Starting', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' }
  if (state.status === 'failed' || state.status === 'action_required')
    return { label: 'Needs attention', cls: 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]' }
  return { label: 'Not connected', cls: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' }
})

const statusHint = computed(() => {
  if (!hasApiKey.value) return 'Save the gateway URL and API key, then press Connect.'
  if (state.status === 'not_created') return 'No session on the gateway yet. Connect creates it and shows a QR to scan.'
  if (state.status === 'initializing' || state.status === 'authenticating') return 'Starting WhatsApp… the QR appears here in a few seconds.'
  if (state.status === 'disconnected') return 'Session stopped. Connect resumes it — no scan needed unless the number was unlinked.'
  if (!state.status) return 'Status unknown. Press Refresh.'
  return `Session status: ${state.status}`
})

function userLabel(name) {
  const u = users.value.find((x) => x.name === name)
  return u?.full_name || name
}

function applySettings(s) {
  hasApiKey.value = !!s.has_api_key
  sessions.value = s.sessions || []
  users.value = s.users || []
  if (!sessions.value.some((x) => x.session_name === selected.value)) selected.value = sessions.value[0]?.session_name || ''
}

async function loadGatewaySessions() {
  if (!hasApiKey.value) return
  try {
    gatewaySessions.value = await frappeGet(`${API}.list_gateway_sessions`)
  } catch {
    // An unreachable gateway still leaves "New session…"
    gatewaySessions.value = []
  }
}

function notify(text, isError = false) {
  message.value = text
  messageIsError.value = isError
}

function applyState(s) {
  // A reply for a session the page has since moved off must not overwrite the shown one
  if (s.session_name && s.session_name !== selected.value) return
  const row = sessions.value.find((x) => x.session_name === s.session_name)
  if (row) Object.assign(row, { status: s.status || '', phone: s.phone || '', push_name: s.push_name || '' })
  Object.assign(state, {
    status: s.status || '',
    phone: s.phone || '',
    push_name: s.push_name || '',
    engine_loaded: !!s.engine_loaded,
    qr: s.qr || '',
    last_error: s.last_error || '',
    restriction: s.restriction || null,
  })
  schedulePoll()
}

function schedulePoll() {
  clearTimeout(pollTimer)
  if (!unmounted && TRANSIENT.has(state.status)) pollTimer = setTimeout(poll, POLL_MS)
}

async function poll() {
  if (!selected.value) return
  try {
    applyState(await frappePost(`${API}.get_status`, { session_name: selected.value }, { silent: true }))
  } catch (e) {
    notify(e.message || String(e), true)
  }
}

async function refresh() {
  if (!hasApiKey.value || !selected.value) return
  busy.value = 'refresh'
  try {
    applyState(await frappePost(`${API}.get_status`, { session_name: selected.value }, { silent: true }))
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
}

async function save() {
  busy.value = 'save'
  try {
    const s = await frappePost(`${API}.save_settings`, {
      base_url: form.base_url,
      api_key: form.api_key || null,
    }, { silent: true })
    applySettings(s)
    form.api_key = ''
    notify('Saved')
    loadGatewaySessions()
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
  await refresh()
}

function select(name) {
  if (name === selected.value) return
  selected.value = name
  clearTimeout(pollTimer)
  const row = sessions.value.find((x) => x.session_name === name) || {}
  Object.assign(state, { status: row.status || '', phone: row.phone || '', push_name: row.push_name || '', engine_loaded: false, qr: '', last_error: '', restriction: null })
  notify('')
  refresh()
}

async function addSession() {
  if (busy.value || !newSessionName.value) return
  busy.value = 'add'
  try {
    const name = newSessionName.value
    applySettings(await frappePost(`${API}.add_session`, { session_name: name, user: newSession.user || null }, { silent: true }))
    Object.assign(newSession, { user: '', pick: '', session_name: '' })
    busy.value = ''
    selected.value = ''
    select(name)
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    if (busy.value === 'add') busy.value = ''
  }
}

async function confirmRemove() {
  if (!confirm(`Remove session ${selected.value}?\n\nIts user falls back to the shared session. Unlink the number first if it should stop being linked on the gateway.`)) return
  busy.value = 'remove'
  try {
    clearTimeout(pollTimer)
    applySettings(await frappePost(`${API}.remove_session`, { session_name: selected.value }, { silent: true }))
    busy.value = ''
    const next = selected.value
    selected.value = ''
    if (next) select(next)
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    if (busy.value === 'remove') busy.value = ''
  }
}

async function run(action) {
  busy.value = action
  notify('')
  try {
    applyState(await frappePost(`${API}.${action}`, { session_name: selected.value }, { silent: true }))
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
}

function confirmLogout() {
  if (!confirm(`Unlink +${state.phone} from this gateway?\n\nBills stop going out until the phone scans a new QR.`)) return
  run('logout')
}

async function sendTest() {
  if (busy.value || state.status !== 'ready' || !test.phone || !test.text) return
  busy.value = 'test'
  try {
    const r = await frappePost(`${API}.send_test`, { session_name: selected.value, phone: test.phone, text: test.text }, { silent: true })
    notify(`Accepted by OpenWA for +${r.phone}`)
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
}

onMounted(async () => {
  try {
    const s = await frappeGet(`${API}.get_settings`)
    Object.assign(form, { base_url: s.base_url || '', api_key: '' })
    applySettings(s)
    const row = sessions.value.find((x) => x.session_name === selected.value) || {}
    Object.assign(state, { status: row.status || '', phone: row.phone || '', push_name: row.push_name || '' })
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    loading.value = false
  }
  loadGatewaySessions()
  await refresh()
})

onUnmounted(() => {
  unmounted = true
  clearTimeout(pollTimer)
})
</script>
