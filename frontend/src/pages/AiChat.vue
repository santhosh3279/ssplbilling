<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden text-[var(--color-text)]">
    <header class="shrink-0 flex items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <div class="flex min-w-0 items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="goBack"
        >
          &larr; Back
        </button>
        <div class="min-w-0">
          <h1 class="text-lg font-bold uppercase tracking-wider">AI Chat</h1>
          <p class="truncate text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">
            {{ current?.title || 'Sales · Outstanding · Stock — read-only' }}
          </p>
        </div>
      </div>
      <div v-if="boot?.allowed" class="flex shrink-0 items-center gap-1">
        <!-- Provider: chosen for a new chat; an open chat keeps the one it started with -->
        <div v-if="!current && boot.providers.length > 1" class="flex rounded-full bg-[var(--color-bg)] p-0.5">
          <button
            v-for="p in boot.providers"
            :key="p"
            class="rounded-full px-3 py-1 text-xs font-semibold transition-colors"
            :class="provider === p ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text-muted)]'"
            @click="setProvider(p)"
          >
            {{ p }}
          </button>
        </div>
        <span
          v-else-if="current?.provider || boot.providers.length"
          class="rounded-full bg-[var(--color-bg)] px-3 py-1 text-xs font-semibold text-[var(--color-text-muted)]"
        >
          {{ current?.provider || provider }}
        </span>
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
          @click="newChat"
        >
          + New
        </button>
        <button
          v-if="current"
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/15"
          title="Delete conversation"
          @click="removeCurrent"
        >
          Delete
        </button>
      </div>
    </header>

    <div v-if="booting" class="flex flex-1 items-center justify-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading…</div>

    <div v-else-if="!boot?.allowed" class="flex flex-1 items-center justify-center p-6 text-center">
      <p class="text-sm text-[var(--color-text-muted)]">
        {{ boot?.enabled === false ? 'AI Chat is turned off in SSPL Assistant Settings.' : error || 'Your user does not have access to AI Chat.' }}
      </p>
    </div>

    <div v-else class="flex flex-1 min-h-0">
      <!-- Conversations -->
      <aside
        class="w-full md:w-72 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]"
        :class="listOpen ? 'flex' : 'hidden md:flex'"
      >
        <div class="flex-1 overflow-y-auto">
          <div v-if="!chats.length" class="p-6 text-center text-sm text-[var(--color-text-muted)]">No conversations yet</div>
          <button
            v-for="c in chats"
            :key="c.name"
            class="flex w-full items-center gap-2 px-3 py-3 text-left transition-colors"
            :class="current?.name === c.name ? 'bg-[var(--color-success)]/20' : 'hover:bg-[var(--color-surface-raised)]'"
            @click="openChat(c.name)"
          >
            <span class="min-w-0 flex-1 truncate text-sm">{{ c.title || 'Untitled' }}</span>
            <span class="shrink-0 text-[10px] text-[var(--color-text-muted)]">{{ c.provider }}</span>
            <span v-if="c.status === 'Running'" class="h-2 w-2 shrink-0 rounded-full bg-[var(--color-success)] animate-pulse" title="Answering"></span>
            <span class="shrink-0 text-[10px] text-[var(--color-text-muted)]">{{ ago(c.modified) }}</span>
          </button>
        </div>
      </aside>

      <!-- Conversation -->
      <main class="flex-1 min-w-0 flex-col" :class="listOpen ? 'hidden md:flex' : 'flex'">
        <section ref="scroller" class="flex-1 overflow-y-auto px-4 py-4">
          <div class="mx-auto max-w-3xl space-y-4">
            <div v-if="!current && !messages.length" class="py-10 text-center">
              <h2 class="text-xl font-bold">Ask about your business</h2>
              <p class="mt-1 text-sm text-[var(--color-text-muted)]">
                Live ERPNext data, with your own access rights. Read-only.<br />
                The buttons below answer instantly at no cost; typed questions go to {{ hasAi ? provider : 'the AI (no API key set)' }}.
              </p>
              <div v-if="hasAi" class="mt-6 flex flex-wrap justify-center gap-2">
                <button
                  v-for="q in suggestions"
                  :key="q"
                  class="rounded-full bg-[var(--color-surface)] px-4 py-2 text-sm hover:bg-[var(--color-surface-raised)]"
                  @click="ask(q)"
                >
                  {{ q }}
                </button>
              </div>
            </div>

            <article v-for="m in messages" :key="m.name" :class="m.role === 'user' ? 'flex justify-end' : ''">
              <div v-if="m.role === 'user'" class="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-[var(--color-highlight)] px-4 py-2 text-sm text-[var(--color-text-on-highlight)]">
                {{ m.content }}
              </div>
              <div v-else-if="m.role === 'error'" class="rounded-lg bg-[var(--color-danger)]/15 px-4 py-2 text-sm text-[var(--color-danger)]">⚠ {{ m.content }}</div>
              <div v-else>
                <div v-if="toolsOf(m).length" class="mb-1 flex flex-wrap gap-1">
                  <span v-for="(t, i) in toolsOf(m)" :key="i" class="rounded-full bg-[var(--color-surface)] px-2 py-0.5 text-[11px] text-[var(--color-text-muted)]">
                    {{ prettyTool(t.name) }}
                  </span>
                </div>
                <div class="ai-md text-sm" v-html="md(m.content)"></div>
                <div class="mt-1 flex gap-3 text-[11px] text-[var(--color-text-muted)]">
                  <span v-if="m.quick">⚡ Answered locally · no AI cost</span>
                  <template v-else>
                    <span v-if="current?.provider">{{ current.provider }}</span>
                    <span v-if="m.duration_ms">{{ (m.duration_ms / 1000).toFixed(1) }}s</span>
                    <span v-if="m.input_tokens || m.output_tokens">{{ m.input_tokens || 0 }} in · {{ m.output_tokens || 0 }} out tokens</span>
                  </template>
                  <button class="hover:text-[var(--color-text)]" @click="copy(m.content)">Copy</button>
                </div>
              </div>
            </article>

            <article v-if="running">
              <div v-if="live.tools.length" class="mb-1 flex flex-wrap gap-1">
                <span
                  v-for="(t, i) in live.tools"
                  :key="i"
                  class="rounded-full px-2 py-0.5 text-[11px]"
                  :class="{
                    'bg-[var(--color-info)]/20 animate-pulse': t.state === 'running',
                    'bg-[var(--color-success)]/20': t.state === 'done',
                    'bg-[var(--color-danger)]/20': t.state === 'failed',
                  }"
                  :title="t.input || ''"
                >
                  {{ prettyTool(t.name) }}
                </span>
              </div>
              <div v-if="live.text" class="ai-md text-sm" v-html="md(live.text)"></div>
              <div v-else class="text-sm text-[var(--color-text-muted)] animate-pulse">Thinking…</div>
            </article>
          </div>
        </section>

        <footer class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
          <div class="mx-auto max-w-3xl">
            <p v-if="error" class="mb-2 rounded bg-[var(--color-danger)]/15 px-3 py-1.5 text-sm text-[var(--color-danger)]">{{ error }}</p>
            <!-- Quick buttons: answered by the server without the AI -->
            <div class="mb-2 flex gap-1.5 overflow-x-auto pb-1">
              <button
                v-for="q in boot.quick_actions"
                :key="q.action"
                class="shrink-0 rounded-full px-3 py-1 text-xs font-semibold transition-colors disabled:opacity-50"
                :class="pendingQuick?.action === q.action ? 'bg-[var(--color-success)]/30' : 'bg-[var(--color-bg)] hover:bg-[var(--color-surface-raised)]'"
                :disabled="running || quickBusy"
                @click="pickQuick(q)"
              >
                ⚡ {{ q.label }}{{ q.needs_query ? '…' : '' }}
              </button>
            </div>
            <div class="flex items-end gap-2">
              <textarea
                ref="inputEl"
                v-model="input"
                rows="1"
                :placeholder="pendingQuick ? `${pendingQuick.label}: type a name, code or mobile, then Enter` : hasAi ? 'Ask about sales, outstanding, stock…' : 'Use the quick buttons (AI not set up)'"
                :class="pendingQuick ? 'bg-[var(--color-success)]/15' : ''"
                class="min-w-0 flex-1 resize-none rounded-lg bg-[var(--color-bg)] px-3 py-2 text-sm focus:bg-[var(--color-info)]/15 focus:outline-none"
                @keydown.enter.exact.prevent="submit"
                @keydown.esc="pendingQuick ? (pendingQuick = null) : stop()"
                @input="autosize"
              ></textarea>
              <button
                v-if="running"
                class="rounded-lg bg-[var(--color-danger)] px-4 py-2 text-sm font-bold text-white"
                @click="stop"
              >
                Stop
              </button>
              <button
                v-else
                class="rounded-lg bg-[var(--color-highlight)] px-4 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] disabled:opacity-50"
                :disabled="!input.trim() || quickBusy || (!pendingQuick && !hasAi)"
                @click="submit"
              >
                Send
              </button>
            </div>
            <p class="mt-1 hidden text-[10px] text-[var(--color-text-muted)] md:block">Enter to send · Shift+Enter new line · Esc to stop</p>
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { aiChat } from '../api'
import { getFrappeSocket } from '../services/frappeSocket'

const EVENT = 'sspl_assistant_event'
const PROVIDER_KEY = 'wb-ai-provider'
const POLL_MS = 4000

const router = useRouter()
const route = useRoute()
const booting = ref(true)
const boot = ref(null)
const chats = ref([])
const current = ref(null)
const messages = ref([])
const input = ref('')
const error = ref('')
const running = ref(false)
const listOpen = ref(true)
const pendingQuick = ref(null)
const quickBusy = ref(false)
const hasAi = computed(() => !!boot.value?.providers?.length)
const provider = ref('Claude')
const live = reactive({ text: '', tools: [] })
const scroller = ref(null)
const inputEl = ref(null)
let pollTimer = null

// Questions the quick buttons can't answer; those go to the AI.
const suggestions = [
  'Compare this week’s sales with last week',
  'Top selling items this month',
  'Which customers owe more than ₹50,000?',
]

marked.setOptions({ gfm: true, breaks: true })
const md = (text) => DOMPurify.sanitize(marked.parse(text || ''))

onMounted(async () => {
  try {
    boot.value = await aiChat.bootstrap()
  } catch (e) {
    error.value = lastLine(e)
  }
  booting.value = false
  if (!boot.value?.allowed) return
  const saved = safeGet(PROVIDER_KEY)
  provider.value = boot.value.providers.includes(saved) ? saved : boot.value.providers[0] || 'Claude'

  getFrappeSocket()?.on(EVENT, onEvent)
  await loadChats()
  if (route.query.chat) openChat(String(route.query.chat))
  else if (window.innerWidth >= 768) newChat()
})

onBeforeUnmount(() => {
  getFrappeSocket()?.off(EVENT, onEvent)
  clearInterval(pollTimer)
})

// Safety net for realtime: a missed 'done' event must not leave the page spinning.
// The reply is in the DB anyway.
watch(running, (on) => {
  clearInterval(pollTimer)
  if (on) pollTimer = setInterval(pollStatus, POLL_MS)
})

async function pollStatus() {
  const name = current.value?.name
  if (!name) return
  try {
    const res = await aiChat.messages(name)
    if (current.value?.name !== name || res.chat.status === 'Running') return
    messages.value = res.messages
    resetLive()
    running.value = false
    loadChats()
    scrollDown()
  } catch {}
}

async function loadChats() {
  try {
    chats.value = await aiChat.chats()
  } catch (e) {
    error.value = lastLine(e)
  }
}

async function openChat(name) {
  error.value = ''
  listOpen.value = false
  try {
    const res = await aiChat.messages(name)
    current.value = res.chat
    messages.value = res.messages
    resetLive()
    running.value = res.chat.status === 'Running'
    router.replace({ query: { chat: name } })
    scrollDown()
  } catch (e) {
    error.value = lastLine(e)
  }
}

function newChat() {
  if (running.value && current.value) return (error.value = 'Wait for the answer or press Stop first.')
  current.value = null
  messages.value = []
  resetLive()
  running.value = false
  error.value = ''
  listOpen.value = false
  router.replace({ query: {} })
  nextTick(() => inputEl.value?.focus())
}

function setProvider(p) {
  provider.value = p
  safeSet(PROVIDER_KEY, p)
}

// On a phone the list and the conversation share the screen: Back returns to the list first.
function goBack() {
  if (!listOpen.value && window.innerWidth < 768) listOpen.value = true
  else router.push('/')
}

function ask(q) {
  input.value = q
  submit()
}

// A quick button with a search (customer / item) waits for the text in the composer.
function pickQuick(q) {
  error.value = ''
  if (!q.needs_query) return runQuick(q)
  pendingQuick.value = pendingQuick.value?.action === q.action ? null : q
  nextTick(() => inputEl.value?.focus())
}

async function runQuick(q, query) {
  quickBusy.value = true
  try {
    const res = await aiChat.quick(q.action, query, current.value?.name, provider.value)
    if (!current.value) {
      current.value = res.chat
      router.replace({ query: { chat: res.chat.name } })
    }
    messages.value.push(...res.messages)
    pendingQuick.value = null
    loadChats()
    scrollDown()
  } catch (e) {
    error.value = lastLine(e)
  } finally {
    quickBusy.value = false
  }
}

async function submit() {
  const text = input.value.trim()
  if (pendingQuick.value) {
    if (!text || quickBusy.value) return
    input.value = ''
    autosize()
    return runQuick(pendingQuick.value, text)
  }
  if (!text || running.value || !hasAi.value) return
  error.value = ''
  input.value = ''
  autosize()
  messages.value.push({ name: 'local-' + Date.now(), role: 'user', content: text })
  resetLive()
  running.value = true
  scrollDown()
  try {
    const res = await aiChat.send(text, current.value?.name, provider.value)
    if (!current.value) {
      current.value = res.chat
      router.replace({ query: { chat: res.chat.name } })
    }
    loadChats()
  } catch (e) {
    running.value = false
    error.value = lastLine(e)
    input.value = text
  }
}

async function stop() {
  if (!running.value || !current.value) return
  try {
    await aiChat.cancel(current.value.name)
  } catch (e) {
    error.value = lastLine(e)
  }
}

async function removeCurrent() {
  if (!current.value || !confirm('Delete this conversation?')) return
  try {
    await aiChat.remove(current.value.name)
    newChat()
    listOpen.value = true
    loadChats()
  } catch (e) {
    error.value = lastLine(e)
  }
}

function onEvent(ev) {
  if (ev.type === 'done') loadChats()
  if (!current.value || ev.chat !== current.value.name) return
  if (ev.type === 'start') {
    running.value = true
  } else if (ev.type === 'text') {
    live.text += ev.text
  } else if (ev.type === 'tool') {
    live.tools.push({ name: ev.name, input: ev.input, state: 'running' })
  } else if (ev.type === 'tool_result') {
    const t = live.tools.find((x) => x.name === ev.name && x.state === 'running')
    if (t) t.state = ev.ok ? 'done' : 'failed'
  } else if (ev.type === 'done') {
    messages.value.push(ev.message)
    resetLive()
    running.value = false
    nextTick(() => inputEl.value?.focus())
  }
  scrollDown()
}

function resetLive() {
  live.text = ''
  live.tools = []
}

function toolsOf(m) {
  try {
    return m.tools ? JSON.parse(m.tools) : []
  } catch {
    return []
  }
}

const TOOL_LABELS = { sales_summary: 'Sales', customer_outstanding: 'Outstanding', item_stock: 'Stock' }
function prettyTool(name) {
  return TOOL_LABELS[name] || (name || 'tool').replace(/_/g, ' ')
}

function scrollDown() {
  nextTick(() => {
    const el = scroller.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function autosize() {
  nextTick(() => {
    const el = inputEl.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  })
}

function copy(text) {
  navigator.clipboard?.writeText(text)
}

// frappePost errors carry the HTTP status and the full traceback; show only the message.
function lastLine(e) {
  return String(e?.message || e).trim().split('\n').pop().replace(/^[\w.]+(Error|Exception): /, '')
}

function safeGet(k) {
  try {
    return localStorage.getItem(k)
  } catch {
    return null
  }
}

function safeSet(k, v) {
  try {
    localStorage.setItem(k, v)
  } catch {}
}

function ago(ts) {
  const s = (Date.now() - new Date(String(ts).replace(' ', 'T')).getTime()) / 1000
  if (s < 60) return 'now'
  if (s < 3600) return Math.floor(s / 60) + 'm'
  if (s < 86400) return Math.floor(s / 3600) + 'h'
  return Math.floor(s / 86400) + 'd'
}
</script>

<style scoped>
.ai-md :deep(p) { margin: 0.4em 0; }
.ai-md :deep(ul), .ai-md :deep(ol) { margin: 0.4em 0; padding-left: 1.4em; }
.ai-md :deep(ul) { list-style: disc; }
.ai-md :deep(ol) { list-style: decimal; }
.ai-md :deep(h1), .ai-md :deep(h2), .ai-md :deep(h3) { font-weight: 700; margin: 0.6em 0 0.3em; }
.ai-md :deep(code) { background: var(--color-surface); padding: 0 0.3em; border-radius: 4px; }
.ai-md :deep(table) { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0.5em 0; }
.ai-md :deep(th), .ai-md :deep(td) { border: 1px solid var(--color-border); padding: 4px 8px; text-align: left; white-space: nowrap; }
.ai-md :deep(th) { background: var(--color-surface); font-weight: 600; }
</style>
