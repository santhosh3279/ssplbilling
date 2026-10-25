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

      <div v-else class="mx-auto max-w-4xl space-y-6">
        <!-- Test send -->
        <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <h2 class="text-xl font-bold border-b border-[var(--color-border)] pb-3">Test Message</h2>

          <div v-if="!sessions.length" class="rounded-lg bg-[var(--color-surface-raised)] p-4 text-sm text-[var(--color-text-muted)]">
            No sessions yet. Add them in <span class="font-mono">SSPL WhatsApp Settings</span>.
          </div>

          <template v-else>
            <div class="grid grid-cols-1 gap-4 md:grid-cols-[1fr_auto] md:items-end">
              <div>
                <label class="block text-sm font-semibold text-[var(--color-text-muted)] mb-1">Session</label>
                <select v-model="selected" :disabled="!!busy" :class="inputCls" @change="refresh">
                  <option v-for="s in sessions" :key="s.session_name" :value="s.session_name">
                    {{ s.session_name }} — {{ s.users?.length ? s.users.join(', ') : 'Shared' }}{{ s.phone ? ' · +' + s.phone : '' }}
                  </option>
                </select>
              </div>
              <button
                @click="refresh"
                :disabled="!!busy"
                class="rounded-lg px-4 py-2 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] disabled:opacity-50"
              >
                {{ busy === 'refresh' ? 'Checking…' : '↻ Refresh' }}
              </button>
            </div>

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
                :disabled="!!busy || status !== 'ready' || !test.phone || !test.text"
                class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black shadow-md transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ busy === 'test' ? 'Sending…' : 'Send' }}
              </button>
            </div>
          </template>

          <p class="text-xs text-[var(--color-text-muted)]">
            10-digit numbers get +91. Every send is recorded in <span class="font-mono">SSPL WhatsApp Log</span>; "Sent" there means OpenWA accepted it, not that it was delivered.
          </p>
        </section>

        <p v-if="message" class="rounded-lg p-3 text-sm" :class="messageIsError ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]' : 'bg-[var(--color-success)]/15 text-[var(--color-success)]'">
          {{ message }}
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.whatsapp_api'
// Statuses that move on their own, shown as starting rather than as a fault
const TRANSIENT = new Set(['initializing', 'qr_ready', 'authenticating'])

const router = useRouter()
const inputCls =
  'w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:bg-[var(--color-info)]/15 focus:outline-none'

const loading = ref(true)
const busy = ref('')
const message = ref('')
const messageIsError = ref(false)
const sessions = ref([])
const selected = ref('')
const test = reactive({ phone: '', text: 'Test message from SSPL Billing' })

const status = computed(() => sessions.value.find((x) => x.session_name === selected.value)?.status || '')

const badge = computed(() => {
  if (status.value === 'ready') return { label: 'Connected', cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' }
  if (status.value === 'qr_ready') return { label: 'Scan QR', cls: 'bg-[var(--color-warning)]/20 text-[var(--color-warning)]' }
  if (TRANSIENT.has(status.value)) return { label: 'Starting', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' }
  if (status.value === 'failed' || status.value === 'action_required')
    return { label: 'Needs attention', cls: 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]' }
  return { label: 'Not connected', cls: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' }
})

function notify(text, isError = false) {
  message.value = text
  messageIsError.value = isError
}

// Re-reads the picked session from the gateway, so Send is enabled only while it is really ready
async function refresh() {
  const name = selected.value
  if (!name) return
  busy.value = 'refresh'
  notify('')
  try {
    const s = await frappePost(`${API}.get_status`, { session_name: name }, { silent: true })
    const row = sessions.value.find((x) => x.session_name === name)
    if (row) Object.assign(row, { status: s.status || '', phone: s.phone || '', push_name: s.push_name || '' })
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    busy.value = ''
  }
}

async function sendTest() {
  if (busy.value || status.value !== 'ready' || !test.phone || !test.text) return
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
    sessions.value = s.sessions || []
    selected.value = sessions.value[0]?.session_name || ''
  } catch (e) {
    notify(e.message || String(e), true)
  } finally {
    loading.value = false
  }
  await refresh()
})
</script>
