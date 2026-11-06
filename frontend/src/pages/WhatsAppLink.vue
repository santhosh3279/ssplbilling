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
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">OpenWA Gateway · link and manage sessions</p>
        </div>
      </div>
      <span v-if="selected" class="rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider" :class="badgeFor(state.status).cls">
        {{ badgeFor(state.status).label }}
      </span>
    </header>

    <main class="flex-1 overflow-y-auto p-6 text-[var(--color-text)]">
      <div v-if="loading" class="flex h-full items-center justify-center text-[var(--color-text-muted)]">
        <span class="text-xl animate-pulse">Loading…</span>
      </div>

      <div v-else class="mx-auto grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">
        <p v-if="!hasApiKey" class="lg:col-span-2 rounded-lg bg-[var(--color-warning)]/15 p-3 text-sm">
          Set the OpenWA Gateway URL and API Key in <span class="font-mono">SSPL WhatsApp Settings</span> first.
        </p>

        <!-- Sessions list + add -->
        <aside class="space-y-4">
          <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Sessions</h2>
              <button
                class="text-xs font-semibold text-[var(--color-info)] hover:underline disabled:opacity-50"
                :disabled="!!busy"
                @click="refreshAll"
              >
                {{ busy === 'refresh-all' ? 'Checking…' : '↻ Refresh all' }}
              </button>
            </div>
            <div v-if="!sessions.length" class="rounded-lg bg-[var(--color-surface-raised)] p-3 text-sm text-[var(--color-text-muted)]">
              No sessions yet. Add one below.
            </div>
            <ul v-else class="space-y-1">
              <li v-for="s in sessions" :key="s.session_name">
                <button
                  class="w-full rounded-lg px-3 py-2 text-left transition-colors"
                  :class="s.session_name === selected ? 'bg-[var(--color-info)]/20' : 'hover:bg-[var(--color-surface-raised)]'"
                  @click="select(s.session_name)"
                >
                  <div class="flex items-center justify-between gap-2">
                    <span class="font-semibold truncate">{{ s.session_name }}</span>
                    <span class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase" :class="badgeFor(s.status).cls">
                      {{ badgeFor(s.status).label }}
                    </span>
                  </div>
                  <div class="truncate text-xs text-[var(--color-text-muted)]">
                    {{ s.phone ? '+' + s.phone : 'No number' }} · {{ s.users?.length ? s.users.map(userLabel).join(', ') : 'Shared' }}
                  </div>
                </button>
              </li>
            </ul>
          </section>

          <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-3">
            <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Add Session</h2>
            <div>
              <label class="mb-1 block text-xs font-semibold text-[var(--color-text-muted)]">Session name</label>
              <select v-model="newSession.pick" :class="inputCls">
                <option value="" disabled>Select a session</option>
                <option v-for="n in freeGatewaySessions" :key="n" :value="n">{{ n }} (on gateway)</option>
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
            <UserPicker v-model="newSession.users" :users="users" :label="userLabel" :input-cls="inputCls" />
            <button
              :disabled="!!busy || !newSessionName"
              class="w-full rounded-lg bg-[var(--color-info)] px-5 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              @click="addSession"
            >
              {{ busy === 'add' ? 'Adding…' : 'Add' }}
            </button>
            <p class="text-xs text-[var(--color-text-muted)]">
              3-50 letters, numbers or hyphens. Each session links its own WhatsApp number. Leave users empty for the shared session (only one allowed).
            </p>
          </section>
        </aside>

        <div v-if="!selected" class="flex items-center justify-center rounded-xl border border-dashed border-[var(--color-border)] p-10 text-sm italic text-[var(--color-text-muted)]">
          Pick or add a session.
        </div>

        <div v-else class="space-y-6">
          <!-- Link status / QR -->
          <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
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
                :disabled="!!busy || !hasApiKey"
                class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                @click="run('connect')"
              >
                {{ busy === 'connect' ? 'Starting…' : state.phone ? 'Connect' : 'Link Number' }}
              </button>
              <button
                v-if="state.engine_loaded"
                :disabled="!!busy"
                class="rounded-lg bg-[var(--color-surface-raised)] px-5 py-2 text-sm font-semibold transition-all active:scale-95 disabled:opacity-50"
                @click="run('disconnect')"
              >
                {{ busy === 'disconnect' ? 'Stopping…' : 'Stop' }}
              </button>
              <button
                v-if="state.engine_loaded && state.status === 'ready'"
                :disabled="!!busy"
                class="rounded-lg bg-[var(--color-danger)]/15 px-5 py-2 text-sm font-semibold text-[var(--color-danger)] transition-all active:scale-95 disabled:opacity-50"
                @click="confirmLogout"
              >
                {{ busy === 'logout' ? 'Unlinking…' : 'Unlink Number' }}
              </button>
              <button
                :disabled="!!busy || !hasApiKey"
                class="rounded-lg px-4 py-2 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] disabled:opacity-50"
                @click="refresh"
              >
                {{ busy === 'refresh' ? 'Checking…' : '↻ Refresh' }}
              </button>
            </div>
          </section>

          <!-- Edit session -->
          <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
            <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Session Settings</h2>
            <UserPicker v-model="edit.users" :users="users" :label="userLabel" :input-cls="inputCls" />
            <label class="flex items-center gap-2 text-sm">
              <input v-model="edit.auto_reconnect" type="checkbox" class="h-4 w-4" />
              Auto Reconnect — restart this session when the gateway leaves it offline
            </label>
            <div class="flex flex-wrap gap-3">
              <button
                :disabled="!!busy || !editDirty"
                class="rounded-lg bg-[var(--color-info)] px-5 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                @click="saveSession"
              >
                {{ busy === 'save' ? 'Saving…' : 'Save' }}
              </button>
              <button
                :disabled="!!busy"
                class="ml-auto rounded-lg px-4 py-2 text-sm font-semibold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/15 disabled:opacity-50"
                @click="confirmRemove"
              >
                {{ busy === 'remove' ? 'Removing…' : 'Remove Session' }}
              </button>
            </div>
            <p class="text-xs text-[var(--color-text-muted)]">
              Users here send and chat through this session; a user moved here leaves their old one. No users = the shared session.
            </p>
          </section>

          <!-- Test send -->
          <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
            <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Test Message</h2>
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
                :disabled="!!busy || state.status !== 'ready' || !test.phone || !test.text"
                class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                @click="sendTest"
              >
                {{ busy === 'test' ? 'Sending…' : 'Send' }}
              </button>
            </div>
            <p class="text-xs text-[var(--color-text-muted)]">
              10-digit numbers get +91. Every send is recorded in <span class="font-mono">SSPL WhatsApp Log</span>; "Sent" there means OpenWA accepted it, not that it was delivered.
            </p>
          </section>
        </div>

        <p
          v-if="message"
          class="lg:col-span-2 rounded-lg p-3 text-sm whitespace-pre-wrap"
          :class="messageIsError ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'"
        >
          {{ message }}
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.whatsapp_api'
// OpenWA rotates the QR roughly every 20s; polling faster keeps the shown one scannable
const POLL_MS = 3000
// Statuses that move on their own, shown as starting rather than as a fault
const TRANSIENT = new Set(['initializing', 'qr_ready', 'authenticating'])
const NEW_SESSION = '__new__'

const router = useRouter()
const inputCls =
  'w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:bg-[var(--color-info)]/15 focus:outline-none'

// Chips of picked users plus a dropdown to add one
const UserPicker = defineComponent({
  props: { modelValue: { type: Array, default: () => [] }, users: { type: Array, default: () => [] }, label: Function, inputCls: String },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const remove = (u) => emit('update:modelValue', props.modelValue.filter((x) => x !== u))
    const add = (e) => {
      const u = e.target.value
      e.target.value = ''
      if (u && !props.modelValue.includes(u)) emit('update:modelValue', [...props.modelValue, u])
    }
    return () =>
      h('div', [
        h('label', { class: 'mb-1 block text-xs font-semibold text-[var(--color-text-muted)]' }, 'Users'),
        h(
          'div',
          { class: 'mb-2 flex flex-wrap gap-1' },
          props.modelValue.length
            ? props.modelValue.map((u) =>
                h('span', { class: 'flex items-center gap-1 rounded-full bg-[var(--color-info)]/20 px-2 py-0.5 text-xs font-semibold' }, [
                  props.label(u),
                  h('button', { class: 'text-[var(--color-danger)]', title: 'Remove', onClick: () => remove(u) }, '✕'),
                ])
              )
            : [h('span', { class: 'text-xs italic text-[var(--color-text-muted)]' }, 'Shared — no users')]
        ),
        h(
          'select',
          { class: props.inputCls, onChange: add },
          [
            h('option', { value: '' }, '+ Add user…'),
            ...props.users
              .filter((u) => !props.modelValue.includes(u.name))
              .map((u) => h('option', { value: u.name }, u.full_name ? `${u.full_name} (${u.name})` : u.name)),
          ]
        ),
      ])
  },
})

const loading = ref(true)
const busy = ref('')
const message = ref('')
const messageIsError = ref(false)
const hasApiKey = ref(false)
const sessions = ref([])
const users = ref([])
const gatewaySessions = ref([])
const selected = ref('')
const state = reactive({ status: '', phone: '', push_name: '', engine_loaded: false, qr: '', last_error: '', restriction: null })
const edit = reactive({ users: [], auto_reconnect: true })
const newSession = reactive({ pick: '', session_name: '', users: [] })
const test = reactive({ phone: '', text: 'Test message from SSPL Billing' })
let pollTimer = null
let unmounted = false

const selectedRow = computed(() => sessions.value.find((x) => x.session_name === selected.value))
const freeGatewaySessions = computed(() => {
  const used = new Set(sessions.value.map((s) => s.session_name))
  return gatewaySessions.value.filter((n) => !used.has(n))
})
const newSessionName = computed(() =>
  (newSession.pick === NEW_SESSION ? newSession.session_name : newSession.pick).trim()
)
const editDirty = computed(() => {
  const row = selectedRow.value
  if (!row) return false
  const a = [...(row.users || [])].sort().join('|')
  const b = [...edit.users].sort().join('|')
  return a !== b || !!row.auto_reconnect !== !!edit.auto_reconnect
})

function badgeFor(status) {
  if (status === 'ready') return { label: 'Connected', cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' }
  if (status === 'qr_ready') return { label: 'Scan QR', cls: 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]' }
  if (TRANSIENT.has(status)) return { label: 'Starting', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' }
  if (status === 'failed' || status === 'action_required')
    return { label: 'Needs attention', cls: 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]' }
  return { label: 'Not connected', cls: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' }
}

const statusHint = computed(() => {
  if (!hasApiKey.value) return 'Set the gateway URL and API key in SSPL WhatsApp Settings, then press Link Number.'
  if (state.status === 'not_created') return 'No session on the gateway yet. Link Number creates it and shows a QR to scan.'
  if (state.status === 'initializing' || state.status === 'authenticating') return 'Starting WhatsApp… the QR appears here in a few seconds.'
  if (state.status === 'disconnected') return 'Session stopped. Connect resumes it — no scan needed unless the number was unlinked.'
  if (!state.status) return 'Status unknown. Press Refresh.'
  return `Session status: ${state.status}`
})

function userLabel(name) {
  return users.value.find((x) => x.name === name)?.full_name || name
}

function notify(text, isError = false) {
  message.value = text
  messageIsError.value = isError
}

function loadEdit() {
  const row = selectedRow.value
  edit.users = [...(row?.users || [])]
  edit.auto_reconnect = row ? !!row.auto_reconnect : true
}

function applySettings(s) {
  hasApiKey.value = !!s.has_api_key
  sessions.value = s.sessions || []
  users.value = s.users || []
  if (!sessions.value.some((x) => x.session_name === selected.value)) selected.value = sessions.value[0]?.session_name || ''
  loadEdit()
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

async function refreshAll() {
  if (!hasApiKey.value) return
  busy.value = 'refresh-all'
  notify('')
  try {
    await frappePost(`${API}.refresh_sessions`, {}, { silent: true })
    applySettings(await frappeGet(`${API}.get_settings`))
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
  const row = selectedRow.value || {}
  Object.assign(state, { status: row.status || '', phone: row.phone || '', push_name: row.push_name || '', engine_loaded: false, qr: '', last_error: '', restriction: null })
  loadEdit()
  notify('')
  refresh()
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
  if (!confirm(`Unlink +${state.phone} from session ${selected.value}?\n\nLinking again needs a fresh QR scan from the phone.`)) return
  run('logout')
}

async function addSession() {
  if (busy.value || !newSessionName.value) return
  busy.value = 'add'
  notify('')
  try {
    const name = newSessionName.value
    applySettings(await frappePost(`${API}.add_session`, { session_name: name, users: newSession.users }, { silent: true }))
    Object.assign(newSession, { pick: '', session_name: '', users: [] })
    busy.value = ''
    selected.value = ''
    select(name)
    notify(`Added ${name}. Press Link Number to scan its QR.`)
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    if (busy.value === 'add') busy.value = ''
  }
}

async function saveSession() {
  if (busy.value || !editDirty.value) return
  busy.value = 'save'
  notify('')
  try {
    applySettings(
      await frappePost(
        `${API}.update_session`,
        { session_name: selected.value, users: edit.users, auto_reconnect: edit.auto_reconnect ? 1 : 0 },
        { silent: true }
      )
    )
    notify('Saved')
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
}

async function confirmRemove() {
  const name = selected.value
  const linked = state.phone ? `\n\n+${state.phone} stays linked on the gateway — Unlink Number first to free it.` : ''
  if (!confirm(`Remove session ${name} from SSPL WhatsApp Settings?${linked}`)) return
  busy.value = 'remove'
  notify('')
  try {
    clearTimeout(pollTimer)
    applySettings(await frappePost(`${API}.remove_session`, { session_name: name }, { silent: true }))
    loadGatewaySessions()
    const next = selected.value
    selected.value = ''
    busy.value = ''
    if (next) select(next)
    notify(`Removed ${name}`)
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    if (busy.value === 'remove') busy.value = ''
  }
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
    applySettings(await frappeGet(`${API}.get_settings`))
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    loading.value = false
  }
  loadGatewaySessions()
  const row = selectedRow.value
  if (row) Object.assign(state, { status: row.status || '', phone: row.phone || '', push_name: row.push_name || '' })
  await refresh()
})

onUnmounted(() => {
  unmounted = true
  clearTimeout(pollTimer)
})
</script>
