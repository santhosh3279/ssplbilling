<template>
  <div class="fixed inset-0 flex flex-col overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
    <header class="shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-2 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))]">
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-2xl text-[var(--color-text-muted)] active:bg-[var(--color-surface-raised)]"
          aria-label="Back"
          @click="goBack"
        >
          &larr;
        </button>
        <div class="min-w-0 flex-1">
          <h1 class="truncate text-lg font-bold">{{ listOpen ? 'AI Chat' : current?.title || 'New chat' }}</h1>
          <!-- The user's own AI token usage (quick buttons use none) -->
          <p v-if="listOpen && usage" class="truncate text-xs text-[var(--color-text-muted)] tabular-nums">
            Today {{ fmtTokens(usage.today.total) }} · Month {{ fmtTokens(usage.month.total) }} tokens
          </p>
          <p v-else-if="!listOpen" class="truncate text-xs text-[var(--color-text-muted)]">
            {{ current?.provider || provider }} · {{ scope.company || 'All companies' }}{{ scope.cost_center ? ' · ' + scope.cost_center : '' }}
          </p>
        </div>
        <template v-if="boot?.allowed">
          <button
            v-if="listOpen"
            type="button"
            class="rounded-full bg-[var(--color-highlight)] px-4 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] active:opacity-80"
            @click="newChat"
          >
            + New
          </button>
          <template v-else>
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full text-xl active:bg-[var(--color-surface-raised)]"
              aria-label="Chat settings"
              @click="sheet = 'scope'"
            >
              ⚙
            </button>
            <button
              v-if="current"
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full text-xl text-[var(--color-danger)] active:bg-[var(--color-danger)]/15"
              aria-label="Delete conversation"
              @click="removeCurrent"
            >
              🗑
            </button>
          </template>
        </template>
      </div>
    </header>

    <div v-if="booting" class="flex flex-1 items-center justify-center text-base text-[var(--color-text-muted)] animate-pulse">Loading…</div>

    <div v-else-if="!boot?.allowed" class="flex flex-1 items-center justify-center p-6 text-center">
      <p class="text-base text-[var(--color-text-muted)]">
        {{ boot?.enabled === false ? 'AI Chat is turned off in SSPL Assistant Settings.' : error || 'Your user does not have access to AI Chat.' }}
      </p>
    </div>

    <!-- Conversations -->
    <div v-else-if="listOpen" class="flex-1 overflow-y-auto pb-[env(safe-area-inset-bottom)]">
      <p v-if="error" class="m-3 rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm text-[var(--color-danger)]">{{ error }}</p>
      <div v-if="!chats.length" class="px-6 py-16 text-center">
        <div class="text-5xl">🤖</div>
        <p class="mt-3 text-base text-[var(--color-text-muted)]">No conversations yet</p>
        <button
          type="button"
          class="mt-5 rounded-full bg-[var(--color-highlight)] px-6 py-3 text-base font-bold text-[var(--color-text-on-highlight)] active:opacity-80"
          @click="newChat"
        >
          Start a chat
        </button>
      </div>
      <button
        v-for="c in chats"
        :key="c.name"
        type="button"
        class="flex w-full items-center gap-3 border-b border-[var(--color-border)] px-4 py-3.5 text-left active:bg-[var(--color-surface-raised)]"
        :class="current?.name === c.name ? 'bg-[var(--color-success)]/20' : ''"
        @click="openChat(c.name)"
      >
        <div class="min-w-0 flex-1">
          <div class="truncate text-base font-medium">{{ c.title || 'Untitled' }}</div>
          <div class="text-xs text-[var(--color-text-muted)]">{{ c.provider }}</div>
        </div>
        <span v-if="c.status === 'Running'" class="h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--color-success)] animate-pulse" title="Answering"></span>
        <span class="shrink-0 text-xs text-[var(--color-text-muted)]">{{ ago(c.modified) }}</span>
      </button>
    </div>

    <!-- Conversation -->
    <template v-else>
      <section ref="scroller" class="flex-1 overflow-y-auto px-3 py-3">
        <div class="space-y-3">
          <div v-if="!current && !messages.length" class="py-8 text-center">
            <h2 class="text-xl font-bold">Ask about your business</h2>
            <p class="mt-1 text-sm text-[var(--color-text-muted)]">
              Live ERPNext data, with your own access rights. Read-only.
              ⚡ buttons answer instantly at no cost; typed questions go to {{ hasAi ? provider : 'the AI (no API key set)' }}.
            </p>
            <div v-if="hasAi" class="mt-5 flex flex-col gap-2">
              <button
                v-for="q in suggestions"
                :key="q"
                type="button"
                class="rounded-xl bg-[var(--color-surface)] px-4 py-3 text-left text-base active:bg-[var(--color-surface-raised)]"
                @click="ask(q)"
              >
                {{ q }}
              </button>
            </div>
          </div>

          <article v-for="m in messages" :key="m.name" :class="m.role === 'user' ? 'flex justify-end' : ''">
            <div v-if="m.role === 'user'" class="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-[var(--color-highlight)] px-4 py-2 text-base text-[var(--color-text-on-highlight)]">
              {{ m.content }}
            </div>
            <div v-else-if="m.role === 'error'" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-base text-[var(--color-danger)]">⚠ {{ m.content }}</div>
            <div v-else class="min-w-0">
              <div v-if="toolsOf(m).length" class="mb-1 flex flex-wrap gap-1">
                <span v-for="(t, i) in toolsOf(m)" :key="i" class="rounded-full bg-[var(--color-surface)] px-2 py-0.5 text-xs text-[var(--color-text-muted)]">
                  {{ prettyTool(t.name) }}
                </span>
              </div>
              <div class="ai-md text-base" v-html="md(m.content)"></div>
              <div v-for="(a, i) in attachmentsOf(m)" :key="i" class="mt-2">
                <AiChart v-if="a.type === 'chart'" :spec="a" />
                <a
                  v-else-if="a.type === 'excel'"
                  :href="aiChat.downloadUrl(a.file)"
                  class="inline-flex items-center gap-2 rounded-lg bg-[var(--color-success)]/20 px-3 py-2 text-base font-semibold active:bg-[var(--color-success)]/30"
                >
                  ⬇ {{ a.title || a.file_name }}.xlsx
                  <span class="text-xs font-normal text-[var(--color-text-muted)]">{{ a.rows }} rows</span>
                </a>
              </div>
              <div v-if="m.quick && m.quick_source" class="mt-2 flex gap-2">
                <button
                  v-for="o in [{ kind: 'excel', label: '⬇ Excel' }, { kind: 'chart', label: '📊 Chart' }, { kind: 'pie', label: '🥧 Pie' }]"
                  :key="o.kind"
                  type="button"
                  class="rounded-full bg-[var(--color-surface)] px-3 py-1.5 text-sm font-semibold active:bg-[var(--color-surface-raised)] disabled:opacity-50"
                  :disabled="outputBusy === m.name + o.kind || hasOutput(m, o.kind)"
                  @click="quickOutput(m, o.kind)"
                >
                  {{ outputBusy === m.name + o.kind ? '…' : o.label }}
                </button>
              </div>
              <div class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-[var(--color-text-muted)]">
                <span v-if="m.quick">⚡ Local · no AI cost</span>
                <template v-else>
                  <span v-if="m.cached_from">♻ Reused{{ m.output_tokens ? '' : ' · no AI cost' }}</span>
                  <span v-if="m.duration_ms">{{ (m.duration_ms / 1000).toFixed(1) }}s</span>
                  <span v-if="m.input_tokens || m.output_tokens">{{ m.input_tokens || 0 }} in · {{ m.output_tokens || 0 }} out</span>
                </template>
                <button type="button" class="active:text-[var(--color-text)]" @click="copy(m.content)">Copy</button>
                <button
                  v-if="m.cached_from && m === messages[messages.length - 1] && !running"
                  type="button"
                  class="font-semibold text-[var(--color-info)]"
                  @click="askFresh(m)"
                >
                  Ask AI fresh
                </button>
              </div>
            </div>
          </article>

          <article v-if="running">
            <div v-if="live.tools.length" class="mb-1 flex flex-wrap gap-1">
              <span
                v-for="(t, i) in live.tools"
                :key="i"
                class="rounded-full px-2 py-0.5 text-xs"
                :class="{
                  'bg-[var(--color-info)]/20 animate-pulse': t.state === 'running',
                  'bg-[var(--color-success)]/20': t.state === 'done',
                  'bg-[var(--color-danger)]/20': t.state === 'failed',
                }"
              >
                {{ prettyTool(t.name) }}
              </span>
            </div>
            <div v-if="live.text" class="ai-md text-base" v-html="md(live.text)"></div>
            <div v-else class="text-base text-[var(--color-text-muted)] animate-pulse">Thinking…</div>
          </article>
        </div>
      </section>

      <footer class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-3 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <p v-if="error" class="mb-2 rounded bg-[var(--color-danger)]/15 px-3 py-1.5 text-sm text-[var(--color-danger)]">{{ error }}</p>
        <div v-if="boot.quick_actions?.length || savedQs.length" class="mb-2 flex gap-1.5 overflow-x-auto pb-1">
          <button
            v-for="q in boot.quick_actions"
            :key="q.action"
            type="button"
            class="shrink-0 rounded-full px-3 py-1.5 text-sm font-semibold disabled:opacity-50"
            :class="pendingQuick?.action === q.action ? 'bg-[var(--color-success)]/30' : 'bg-[var(--color-bg)] active:bg-[var(--color-surface-raised)]'"
            :disabled="running || quickBusy"
            @click="pickQuick(q)"
          >
            ⚡ {{ q.label }}{{ q.needs_query ? '…' : '' }}
          </button>
          <button
            v-for="s in savedQs"
            :key="s.name"
            type="button"
            class="max-w-[14rem] shrink-0 truncate rounded-full px-3 py-1.5 text-sm font-semibold disabled:opacity-50"
            :class="pendingSaved?.item.name === s.name ? 'bg-[var(--color-success)]/30' : 'bg-[var(--color-bg)] active:bg-[var(--color-surface-raised)]'"
            :disabled="running || quickBusy || !hasAi"
            @click="pickSaved(s)"
          >
            ↻ {{ s.question }}{{ s.params.length ? '…' : '' }}
          </button>
        </div>
        <div v-if="pendingQuick || pendingSaved" class="mb-1.5 flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <span class="min-w-0 flex-1 truncate">
            {{ savedParam ? `${savedParam.label} for “${pendingSaved.item.question}” (was ${savedParam.was})` : `${pendingQuick.label}: type a name, code or mobile` }}
          </span>
          <button type="button" class="shrink-0 font-semibold" @click="pendingQuick = null; pendingSaved = null">Cancel</button>
        </div>
        <div class="flex items-end gap-2">
          <!-- text-base (16px) keeps iOS from zooming the page on focus -->
          <textarea
            ref="inputEl"
            v-model="input"
            rows="1"
            enterkeyhint="send"
            :placeholder="pendingQuick || pendingSaved ? 'Type here, then Send' : hasAi ? 'Ask about sales, stock…' : 'Use the ⚡ buttons (AI not set up)'"
            :class="pendingQuick || pendingSaved ? 'bg-[var(--color-success)]/15' : ''"
            class="min-w-0 flex-1 resize-none rounded-2xl bg-[var(--color-bg)] px-4 py-2.5 text-base focus:bg-[var(--color-info)]/15 focus:outline-none"
            @keydown.enter.exact.prevent="submit"
            @input="autosize"
          ></textarea>
          <button
            v-if="running"
            type="button"
            class="h-11 shrink-0 rounded-full bg-[var(--color-danger)] px-4 text-base font-bold text-white"
            @click="stop"
          >
            Stop
          </button>
          <button
            v-else
            type="button"
            class="h-11 shrink-0 rounded-full bg-[var(--color-highlight)] px-4 text-base font-bold text-[var(--color-text-on-highlight)] disabled:opacity-50"
            :disabled="!input.trim() || quickBusy || (!pendingQuick && !hasAi)"
            @click="submit"
          >
            Send
          </button>
        </div>
      </footer>
    </template>

    <!-- Scope + provider sheet: answers use this company / cost center unless the question names another -->
    <div v-if="sheet === 'scope'" class="fixed inset-0 z-50 flex items-end bg-black/40" @click.self="sheet = ''">
      <div class="w-full rounded-t-2xl bg-[var(--color-surface)] px-4 pt-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
        <h3 class="mb-3 text-base font-bold">Chat settings</h3>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Company</label>
        <select v-model="scope.company" class="mb-3 w-full rounded-lg bg-[var(--color-bg)] px-3 py-2.5 text-base focus:outline-none" @change="onCompanyChange">
          <option value="">All companies</option>
          <option v-for="c in boot.companies" :key="c" :value="c">{{ c }}</option>
        </select>
        <label class="mb-1 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Cost center</label>
        <select v-model="scope.cost_center" class="mb-3 w-full rounded-lg bg-[var(--color-bg)] px-3 py-2.5 text-base focus:outline-none">
          <option value="">All cost centers</option>
          <option v-for="c in costCenterOptions" :key="c.name" :value="c.name">{{ c.name }}</option>
        </select>
        <!-- Provider: chosen for a new chat; an open chat keeps the one it started with -->
        <template v-if="!current && boot.providers.length > 1">
          <label class="mb-1 block text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">AI</label>
          <div class="mb-3 flex rounded-full bg-[var(--color-bg)] p-1">
            <button
              v-for="p in boot.providers"
              :key="p"
              type="button"
              class="flex-1 rounded-full py-2 text-base font-semibold"
              :class="provider === p ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text-muted)]'"
              @click="setProvider(p)"
            >
              {{ p }}
            </button>
          </div>
        </template>
        <button
          type="button"
          class="mt-1 w-full rounded-full bg-[var(--color-highlight)] py-3 text-base font-bold text-[var(--color-text-on-highlight)]"
          @click="sheet = ''"
        >
          Done
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Phone front end for AI Chat: the router sends phones here from /ai-chat.
// Same API and realtime flow as AiChat.vue; list and conversation are separate screens.
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { aiChat } from '../api'
import AiChart from '../components/AiChart.vue'
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
const usage = ref(null)
const listOpen = ref(true)
const sheet = ref('')
const pendingQuick = ref(null)
// Saved question waiting for its values: { item: {name, question, params}, values }
const pendingSaved = ref(null)
const savedQs = ref([])
const savedParam = computed(() => pendingSaved.value?.item.params[Object.keys(pendingSaved.value.values).length])
const quickBusy = ref(false)
const outputBusy = ref('')
const hasAi = computed(() => !!boot.value?.providers?.length)
const provider = ref('Claude')
const scope = reactive({ company: '', cost_center: '' })
const costCenterOptions = computed(() =>
  (boot.value?.cost_centers || []).filter((c) => !scope.company || c.company === scope.company)
)
const live = reactive({ text: '', tools: [] })
const scroller = ref(null)
const inputEl = ref(null)
let pollTimer = null

// Questions the quick buttons can't answer; those go to the AI.
const suggestions = [
  'Compare this week’s sales with last week',
  'Chart of monthly sales this year',
  'Excel of sales by item this month',
]

marked.setOptions({ gfm: true, breaks: true })
const md = (text) => DOMPurify.sanitize(marked.parse(text || ''))

onMounted(async () => {
  try {
    boot.value = await aiChat.bootstrap()
    usage.value = boot.value?.usage || null
  } catch (e) {
    error.value = lastLine(e)
  }
  booting.value = false
  if (!boot.value?.allowed) return
  const saved = safeGet(PROVIDER_KEY)
  provider.value = boot.value.providers.includes(saved) ? saved : boot.value.providers[0] || 'Claude'

  getFrappeSocket()?.on(EVENT, onEvent)
  loadSaved()
  resetScope()
  await loadChats()
  // A phone opens on the conversation list unless a chat link was followed
  if (route.query.chat) openChat(String(route.query.chat))
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
    scope.company = res.chat.company || ''
    scope.cost_center = res.chat.cost_center || ''
    resetLive()
    running.value = res.chat.status === 'Running'
    router.replace({ query: { chat: name } })
    scrollDown()
  } catch (e) {
    error.value = lastLine(e)
  }
}

// A new chat starts on the user's billing defaults (SSPL Billing Settings → user row).
function resetScope() {
  scope.company = boot.value?.default_company || ''
  scope.cost_center = boot.value?.default_cost_center || ''
}

function onCompanyChange() {
  if (!costCenterOptions.value.some((c) => c.name === scope.cost_center)) scope.cost_center = ''
}

function newChat() {
  if (running.value && current.value) return (error.value = 'Wait for the answer or press Stop first.')
  resetScope()
  current.value = null
  messages.value = []
  resetLive()
  running.value = false
  error.value = ''
  pendingQuick.value = null
  pendingSaved.value = null
  listOpen.value = false
  router.replace({ query: {} })
}

function setProvider(p) {
  provider.value = p
  safeSet(PROVIDER_KEY, p)
}

// Back from a conversation returns to the list; back from the list leaves the page.
function goBack() {
  if (sheet.value) sheet.value = ''
  else if (!listOpen.value) {
    listOpen.value = true
    loadChats()
  } else router.push('/')
}

function ask(q) {
  input.value = q
  submit()
}

// A quick button with a search (customer / item) waits for the text in the composer.
function pickQuick(q) {
  error.value = ''
  pendingSaved.value = null
  if (!q.needs_query) return runQuick(q)
  pendingQuick.value = pendingQuick.value?.action === q.action ? null : q
  nextTick(() => inputEl.value?.focus())
}

async function runQuick(q, query) {
  quickBusy.value = true
  try {
    const res = await aiChat.quick(q.action, query, current.value?.name, provider.value, { ...scope })
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
  if (pendingSaved.value) {
    if (!text || running.value) return
    input.value = ''
    autosize()
    pendingSaved.value.values[savedParam.value.key] = text
    if (!savedParam.value) runSaved(pendingSaved.value.item, pendingSaved.value.values)
    return
  }
  if (pendingQuick.value) {
    if (!text || quickBusy.value) return
    input.value = ''
    autosize()
    return runQuick(pendingQuick.value, text)
  }
  if (!text || running.value || !hasAi.value) return
  input.value = ''
  autosize()
  sendText(text)
}

// Re-ask the question behind a reused answer, skipping the saved recipe.
function askFresh(m) {
  const i = messages.value.indexOf(m)
  const q = messages.value.slice(0, i).reverse().find((x) => x.role === 'user')
  if (q && !running.value) sendText(q.content, true)
}

async function sendText(text, fresh = false) {
  error.value = ''
  messages.value.push({ name: 'local-' + Date.now(), role: 'user', content: text })
  resetLive()
  running.value = true
  scrollDown()
  try {
    const res = await aiChat.send(text, current.value?.name, provider.value, { ...scope }, fresh)
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
  if (ev.type === 'done') {
    loadChats()
    loadUsage()
    loadSaved() // the answer may have been saved as a new question
  }
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
  }
  scrollDown()
}

function resetLive() {
  live.text = ''
  live.tools = []
}

function attachmentsOf(m) {
  try {
    return m.attachments ? JSON.parse(m.attachments) : []
  } catch {
    return []
  }
}

// Pie and bar/line both attach as type 'chart'; chart_type tells them apart.
function hasOutput(m, kind) {
  return attachmentsOf(m).some((a) =>
    kind === 'pie' ? a.type === 'chart' && a.chart_type === 'pie'
      : kind === 'chart' ? a.type === 'chart' && a.chart_type !== 'pie'
        : a.type === kind,
  )
}

// ⬇ Excel / 📊 Chart under a quick answer: built on the server, no AI call.
async function quickOutput(m, kind) {
  outputBusy.value = m.name + kind
  error.value = ''
  try {
    const updated = await aiChat.output(m.name, kind)
    const i = messages.value.findIndex((x) => x.name === m.name)
    if (i >= 0) messages.value[i] = updated
    if (kind === 'excel') {
      const file = attachmentsOf(updated).filter((a) => a.type === 'excel').pop()
      if (file) window.location.href = aiChat.downloadUrl(file.file)
    }
    scrollDown()
  } catch (e) {
    error.value = lastLine(e)
  } finally {
    outputBusy.value = ''
  }
}

function toolsOf(m) {
  try {
    return m.tools ? JSON.parse(m.tools) : []
  } catch {
    return []
  }
}

const TOOL_LABELS = {
  sales_summary: 'Sales',
  top_items: 'Top items',
  customer_outstanding: 'Outstanding',
  item_stock: 'Stock',
  account_ledger: 'Ledger',
  purchase_summary: 'Purchases',
  supplier_outstanding: 'Payables',
  customer_activity: 'Customer activity',
  item_movement: 'Item movement',
  cash_bank_position: 'Cash & bank',
  profit_loss: 'P&L',
  gst_summary: 'GST',
  payments_summary: 'Payments',
  export_excel: 'Excel',
  make_chart: 'Chart',
}
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
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
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

async function loadSaved() {
  try {
    savedQs.value = await aiChat.saved()
  } catch {
    // keep the last list
  }
}

function pickSaved(s) {
  error.value = ''
  pendingQuick.value = null
  if (running.value) return
  if (!s.params.length) return runSaved(s, {})
  pendingSaved.value = pendingSaved.value?.item.name === s.name ? null : { item: s, values: {} }
  nextTick(() => inputEl.value?.focus())
}

// Always a new chat: a reused answer replaces the chat's AI history. Keeps the picked company / cost center.
async function runSaved(s, values) {
  pendingSaved.value = null
  current.value = null
  messages.value = [{ name: 'local-' + Date.now(), role: 'user', content: s.question }]
  resetLive()
  running.value = true
  listOpen.value = false
  try {
    const res = await aiChat.askSaved(s.name, values, provider.value, { ...scope })
    messages.value[0].content = res.message
    current.value = res.chat
    router.replace({ query: { chat: res.chat.name } })
    loadChats()
  } catch (e) {
    running.value = false
    error.value = lastLine(e)
  }
  scrollDown()
}

async function loadUsage() {
  try {
    usage.value = await aiChat.usage()
  } catch {
    // keep the last figures
  }
}

const fmtTokens = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n || 0))

function ago(ts) {
  const s = (Date.now() - new Date(String(ts).replace(' ', 'T')).getTime()) / 1000
  if (s < 60) return 'now'
  if (s < 3600) return Math.floor(s / 60) + 'm'
  if (s < 86400) return Math.floor(s / 3600) + 'h'
  return Math.floor(s / 86400) + 'd'
}
</script>

<style scoped>
.ai-md { overflow-wrap: anywhere; }
.ai-md :deep(p) { margin: 0.4em 0; }
.ai-md :deep(ul), .ai-md :deep(ol) { margin: 0.4em 0; padding-left: 1.4em; }
.ai-md :deep(ul) { list-style: disc; }
.ai-md :deep(ol) { list-style: decimal; }
.ai-md :deep(h1), .ai-md :deep(h2), .ai-md :deep(h3) { font-weight: 700; margin: 0.6em 0 0.3em; }
.ai-md :deep(code) { background: var(--color-surface); padding: 0 0.3em; border-radius: 4px; }
.ai-md :deep(table) { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 0.5em 0; font-size: 0.875rem; }
.ai-md :deep(th), .ai-md :deep(td) { border: 1px solid var(--color-border); padding: 4px 8px; text-align: left; white-space: nowrap; }
.ai-md :deep(th) { background: var(--color-surface); font-weight: 600; }
</style>
