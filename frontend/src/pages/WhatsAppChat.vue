<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden text-[var(--color-text)]">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold uppercase tracking-wider">WhatsApp Chat</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Business number via OpenWA</p>
        </div>
      </div>
      <button
        class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
        :disabled="loadingChats"
        @click="loadChats"
      >
        {{ loadingChats ? 'Loading…' : '↻ Refresh' }}
      </button>
    </header>

    <p v-if="error" class="shrink-0 bg-[var(--color-danger)]/15 px-4 py-2 text-sm text-[var(--color-danger)]">{{ error }}</p>

    <div class="flex flex-1 min-h-0">
      <!-- Chat list -->
      <aside
        class="w-full md:w-80 lg:w-96 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]"
        :class="active ? 'hidden md:flex' : 'flex'"
      >
        <div class="space-y-2 border-b border-[var(--color-border)] p-3">
          <input
            v-model="search"
            type="text"
            placeholder="Search chats"
            class="w-full rounded-lg bg-[var(--color-bg)] px-3 py-2 text-sm focus:bg-[var(--color-info)]/15 focus:outline-none"
          />
          <form class="flex gap-2" @submit.prevent="startChat">
            <input
              v-model="newNumber"
              type="tel"
              placeholder="New chat: mobile number"
              class="min-w-0 flex-1 rounded-lg bg-[var(--color-bg)] px-3 py-2 text-sm focus:bg-[var(--color-info)]/15 focus:outline-none"
            />
            <button
              type="submit"
              :disabled="!newNumber || starting"
              class="rounded-lg bg-[#25D366] px-3 py-2 text-sm font-bold text-black disabled:opacity-50"
            >
              {{ starting ? '…' : 'Start' }}
            </button>
          </form>
        </div>

        <div class="flex-1 overflow-y-auto">
          <div v-if="loadingChats && !chats.length" class="p-6 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading chats…</div>
          <div v-else-if="!filteredChats.length" class="p-6 text-center text-sm text-[var(--color-text-muted)]">No chats</div>
          <button
            v-for="c in filteredChats"
            :key="c.id"
            class="flex w-full items-center gap-3 px-3 py-3 text-left transition-colors"
            :class="active?.id === c.id ? 'bg-[var(--color-success)]/20' : 'hover:bg-[var(--color-surface-raised)]'"
            @click="openChat(c)"
          >
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-sm font-bold">
              {{ c.is_group ? '👥' : initials(c.name) }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-baseline justify-between gap-2">
                <span class="truncate font-semibold">{{ c.name }}</span>
                <span class="shrink-0 text-[10px] text-[var(--color-text-muted)]">{{ shortTime(c.timestamp) }}</span>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="truncate text-xs text-[var(--color-text-muted)]">{{ preview(c) }}</span>
                <span
                  v-if="c.unread"
                  class="shrink-0 rounded-full bg-[#25D366] px-1.5 text-[10px] font-bold text-black"
                >{{ c.unread }}</span>
              </div>
            </div>
          </button>
        </div>
      </aside>

      <!-- Thread -->
      <section class="min-w-0 flex-1 flex-col" :class="active ? 'flex' : 'hidden md:flex'">
        <div v-if="!active" class="flex flex-1 items-center justify-center text-sm text-[var(--color-text-muted)]">
          Pick a chat on the left, or start one with a mobile number.
        </div>

        <template v-else>
          <div class="shrink-0 flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">
            <button class="md:hidden rounded px-2 py-1 text-lg" @click="closeChat">&larr;</button>
            <div class="min-w-0">
              <div class="truncate font-bold">{{ active.name }}</div>
              <div class="text-xs text-[var(--color-text-muted)] font-mono">{{ active.is_group ? 'Group' : '+' + active.id.split('@')[0] }}</div>
            </div>
          </div>

          <div ref="threadEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-1">
            <div v-if="loadingThread && !messages.length" class="py-6 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading messages…</div>
            <template v-for="(m, i) in messages" :key="m.id || i">
              <div v-if="dayLabel(m, messages[i - 1])" class="py-2 text-center">
                <span class="rounded-full bg-[var(--color-surface-raised)] px-3 py-0.5 text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">
                  {{ dayLabel(m, messages[i - 1]) }}
                </span>
              </div>
              <div class="flex" :class="m.from_me ? 'justify-end' : 'justify-start'">
                <div
                  class="max-w-[80%] rounded-xl px-3 py-1.5 text-sm shadow-sm"
                  :class="m.from_me ? 'bg-[#25D366]/25' : 'bg-[var(--color-surface)]'"
                >
                  <div v-if="active.is_group && !m.from_me && m.author" class="text-[11px] font-semibold text-[var(--color-info)]">
                    {{ m.author.split('@')[0] }}
                  </div>
                  <div v-if="mediaLabel(m)" class="text-xs font-semibold text-[var(--color-text-muted)]">{{ mediaLabel(m) }}</div>
                  <div v-if="m.body" class="whitespace-pre-wrap break-words">{{ m.body }}</div>
                  <div class="mt-0.5 text-right text-[10px] text-[var(--color-text-muted)]">
                    {{ clock(m.timestamp) }}
                    <span
                      v-if="m.from_me && TICKS[m.status]"
                      class="ml-0.5 font-bold"
                      :class="m.status === 'read' ? 'text-[#34B7F1]' : m.status === 'failed' ? 'text-[var(--color-danger)]' : ''"
                      :title="m.status"
                    >{{ TICKS[m.status] }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div v-if="pendingFile" class="shrink-0 flex items-center justify-between gap-3 bg-[var(--color-info)]/15 px-4 py-2 text-sm">
            <span class="truncate">📎 {{ pendingFile.name }} ({{ fileSize(pendingFile.size) }}) — text below goes as the caption</span>
            <button class="font-bold text-[var(--color-danger)]" @click="pendingFile = null">✕</button>
          </div>

          <form class="shrink-0 flex items-end gap-2 border-t border-[var(--color-border)] bg-[var(--color-surface)] p-3" @submit.prevent="send">
            <label class="cursor-pointer rounded-lg px-2 py-2 text-xl hover:bg-[var(--color-surface-raised)]" title="Attach file">
              📎
              <input type="file" class="hidden" @change="pickFile" />
            </label>
            <textarea
              ref="composerEl"
              v-model="draft"
              rows="1"
              placeholder="Type a message — Enter sends, Shift+Enter new line"
              class="max-h-40 min-h-[40px] flex-1 resize-none rounded-lg bg-[var(--color-bg)] px-3 py-2 text-sm focus:bg-[var(--color-info)]/15 focus:outline-none"
              @keydown.enter.exact.prevent="send"
            />
            <button
              type="submit"
              :disabled="sending || (!draft.trim() && !pendingFile)"
              class="rounded-lg bg-[#25D366] px-5 py-2 text-sm font-bold text-black disabled:opacity-50"
            >
              {{ sending ? '…' : 'Send' }}
            </button>
          </form>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.whatsapp_api'
const CHATS_POLL_MS = 15000
const THREAD_POLL_MS = 5000
// OpenWA's body limit is 25mb by default and base64 adds a third
const MAX_FILE_BYTES = 16 * 1024 * 1024
// WhatsApp's own marks: one tick sent, two delivered, two blue read
const TICKS = { pending: '🕓', sent: '✓', delivered: '✓✓', read: '✓✓', failed: '⚠' }

const router = useRouter()

const chats = ref([])
const search = ref('')
const newNumber = ref('')
const active = ref(null)
const messages = ref([])
const draft = ref('')
const pendingFile = ref(null)
const error = ref('')
const loadingChats = ref(false)
const loadingThread = ref(false)
const sending = ref(false)
const starting = ref(false)
const threadEl = ref(null)
const composerEl = ref(null)

let chatsTimer = null
let threadTimer = null
// A slow answer for a chat the operator has already left must not overwrite the open one
let threadToken = 0
let unmounted = false

const filteredChats = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = q
    ? chats.value.filter((c) => c.name.toLowerCase().includes(q) || c.id.includes(q.replace(/\D/g, '') || '\u0000'))
    : chats.value
  return [...list].sort((a, b) => (b.pinned - a.pinned) || (b.timestamp - a.timestamp))
})

function initials(name) {
  return (name || '?').replace(/[^\p{L}\p{N} ]/gu, '').split(' ').filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase() || '#'
}

function preview(c) {
  if (c.last_message) return c.last_message
  return c.last_type && c.last_type !== 'text' ? `[${c.last_type}]` : ''
}

function toDate(ts) {
  return new Date((ts || 0) * 1000)
}

function clock(ts) {
  return ts ? toDate(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''
}

function shortTime(ts) {
  if (!ts) return ''
  const d = toDate(ts)
  return d.toDateString() === new Date().toDateString() ? clock(ts) : d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

function dayLabel(m, prev) {
  if (!m.timestamp) return ''
  const day = toDate(m.timestamp).toDateString()
  if (prev?.timestamp && toDate(prev.timestamp).toDateString() === day) return ''
  return day === new Date().toDateString() ? 'Today' : toDate(m.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function mediaLabel(m) {
  if (m.type === 'text') return ''
  if (m.type === 'revoked') return '🚫 Message deleted'
  const icon = { image: '🖼', video: '🎬', audio: '🎵', voice: '🎤', document: '📄', sticker: '🏷', location: '📍', contact: '👤', call: '📞' }[m.type] || '•'
  return `${icon} ${m.media?.filename || m.type}`
}

function fileSize(bytes) {
  return bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`
}

function nearBottom() {
  const el = threadEl.value
  return !el || el.scrollHeight - el.scrollTop - el.clientHeight < 80
}

async function scrollToBottom() {
  await nextTick()
  if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight
}

async function loadChats() {
  loadingChats.value = true
  try {
    chats.value = await frappeGet(`${API}.list_chats`)
    error.value = ''
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loadingChats.value = false
  }
}

async function loadThread({ scroll = false } = {}) {
  if (!active.value) return
  const token = threadToken
  const stick = scroll || nearBottom()
  loadingThread.value = true
  try {
    const list = await frappeGet(`${API}.get_messages`, { chat_id: active.value.id, limit: 80 })
    if (token !== threadToken) return
    messages.value = list
    if (stick) scrollToBottom()
  } catch (e) {
    if (token === threadToken) error.value = e.message || String(e)
  } finally {
    if (token === threadToken) loadingThread.value = false
  }
}

function scheduleThreadPoll() {
  clearTimeout(threadTimer)
  if (unmounted || !active.value) return
  threadTimer = setTimeout(async () => {
    await loadThread()
    scheduleThreadPoll()
  }, THREAD_POLL_MS)
}

async function openChat(chat) {
  threadToken++
  active.value = chat
  messages.value = []
  draft.value = ''
  pendingFile.value = null
  await loadThread({ scroll: true })
  scheduleThreadPoll()
  composerEl.value?.focus()
  if (chat.unread) {
    chat.unread = 0
    frappePost(`${API}.mark_chat_read`, { chat_id: chat.id }, { silent: true }).catch(() => {})
  }
}

function closeChat() {
  threadToken++
  clearTimeout(threadTimer)
  active.value = null
  messages.value = []
}

async function startChat() {
  starting.value = true
  try {
    const r = await frappeGet(`${API}.resolve_chat`, { phone: newNumber.value })
    const existing = chats.value.find((c) => c.id === r.chat_id)
    newNumber.value = ''
    error.value = ''
    await openChat(existing || { id: r.chat_id, name: '+' + r.phone, is_group: false, unread: 0, timestamp: 0, last_message: '', pinned: false })
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    starting.value = false
  }
}

function pickFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > MAX_FILE_BYTES) {
    error.value = `${file.name} is ${fileSize(file.size)}; the limit is ${fileSize(MAX_FILE_BYTES)}`
    return
  }
  pendingFile.value = file
  composerEl.value?.focus()
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    // Strip the "data:<mime>;base64," prefix; OpenWA wants the bare payload
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1] || '')
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

async function send() {
  const text = draft.value.trim()
  const file = pendingFile.value
  if (sending.value || !active.value || (!text && !file)) return
  sending.value = true
  const chat = active.value
  try {
    if (file) {
      await frappePost(`${API}.send_chat_file`, {
        chat_id: chat.id,
        file_base64: await fileToBase64(file),
        mimetype: file.type || 'application/octet-stream',
        filename: file.name,
        caption: text,
      }, { silent: true })
    } else {
      await frappePost(`${API}.send_chat_message`, { chat_id: chat.id, text }, { silent: true })
    }
    draft.value = ''
    pendingFile.value = null
    error.value = ''
    if (!chats.value.some((c) => c.id === chat.id)) chats.value.unshift(chat)
    chat.last_message = text || (file ? `[${file.name}]` : '')
    chat.timestamp = Math.floor(Date.now() / 1000)
    await loadThread({ scroll: true })
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    sending.value = false
    composerEl.value?.focus()
  }
}

function scheduleChatsPoll() {
  clearTimeout(chatsTimer)
  if (unmounted) return
  chatsTimer = setTimeout(async () => {
    if (!document.hidden) await loadChats()
    scheduleChatsPoll()
  }, CHATS_POLL_MS)
}

function onKeydown(e) {
  if (e.key === 'Escape' && active.value) closeChat()
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  await loadChats()
  scheduleChatsPoll()
})

onUnmounted(() => {
  unmounted = true
  window.removeEventListener('keydown', onKeydown)
  threadToken++
  clearTimeout(chatsTimer)
  clearTimeout(threadTimer)
})
</script>
