<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden">
    <header class="shrink-0 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Order Reminder</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Suppliers to order from, and when</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <select
          v-if="companies.length > 1"
          v-model="company"
          class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          @change="load"
        >
          <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
        </select>
        <span v-else class="text-sm font-semibold text-[var(--color-text-muted)]">{{ company }}</span>
        <span class="hidden lg:inline text-xs text-[var(--color-text-muted)]">
          <kbd :class="kbdCls">F2</kbd> New
          <kbd :class="[kbdCls, 'ml-2']">F8</kbd> Save
          <kbd :class="[kbdCls, 'ml-2']">Esc</kbd> Back
        </span>
      </div>
    </header>

    <main class="flex-1 overflow-hidden grid grid-cols-1 text-[var(--color-text)]" :class="editing ? 'lg:grid-cols-[1fr_440px]' : ''">
      <!-- Reminder list -->
      <section class="flex flex-col overflow-hidden">
        <div class="flex flex-wrap items-center gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] p-3">
          <input ref="searchInput" v-model="query" :class="[inputCls, 'max-w-sm']" placeholder="Search supplier..." />
          <div class="flex flex-wrap gap-1.5 text-xs font-bold uppercase tracking-wider">
            <span v-if="counts.overdue" class="rounded-full bg-[var(--color-danger)] px-3 py-1 text-white">{{ counts.overdue }} overdue</span>
            <span v-if="counts.due" class="rounded-full bg-[var(--color-warning)] px-3 py-1 text-white">{{ counts.due }} due</span>
            <span v-if="counts.snoozed" class="rounded-full bg-[var(--color-surface-raised)] px-3 py-1 text-[var(--color-text-muted)]">{{ counts.snoozed }} snoozed</span>
          </div>
          <button
            class="ml-auto shrink-0 rounded-lg bg-[var(--color-info)] px-4 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)]/80 active:scale-95"
            @click="newReminder"
          >
            + Add Supplier
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-5">
          <div v-if="loading" class="p-4 text-sm text-[var(--color-text-muted)] animate-pulse">Loading…</div>
          <div v-else-if="!reminders.length" class="mx-auto mt-16 max-w-md text-center">
            <div class="text-5xl mb-3">🗓️</div>
            <h2 class="text-lg font-bold">No order reminders yet</h2>
            <p class="mt-1 text-sm text-[var(--color-text-muted)]">Add a supplier and say how often you order from them. It shows up here on its ordering day.</p>
          </div>
          <div v-else-if="!groups.length" class="p-4 text-sm italic text-[var(--color-text-muted)]">No supplier matches "{{ query }}".</div>

          <div v-for="group in groups" :key="group.key">
            <h2 class="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-widest" :class="group.titleCls">
              {{ group.title }}
              <span class="rounded-full bg-[var(--color-surface-raised)] px-2 py-0.5 text-[var(--color-text-muted)]">{{ group.rows.length }}</span>
            </h2>
            <div class="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
              <div
                v-for="r in group.rows"
                :key="r.name"
                class="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-[var(--color-border)]/50 px-4 py-3 last:border-b-0 cursor-pointer transition-colors"
                :class="form.name === r.name && editing
                  ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
                  : 'hover:bg-[var(--color-surface-raised)]'"
                @click="editReminder(r)"
              >
                <div class="min-w-0 flex-1 basis-56">
                  <div class="truncate text-lg font-bold">{{ r.supplier_name }}</div>
                  <div class="truncate text-xs opacity-70">
                    {{ r.schedule }}<template v-if="r.lead_days"> · remind {{ r.lead_days }}d before</template><template v-if="r.assigned_to"> · {{ userLabel(r.assigned_to) }}</template>
                  </div>
                  <div v-if="r.notes" class="truncate text-xs italic opacity-70">{{ r.notes }}</div>
                </div>

                <div class="w-36 shrink-0">
                  <div class="text-[10px] font-bold uppercase tracking-wider opacity-60">{{ r.status === 'disabled' ? 'Status' : 'Order on' }}</div>
                  <div class="font-mono font-bold">{{ r.status === 'disabled' ? 'Off' : fmtDate(r.due_date) }}</div>
                  <div class="text-xs font-bold" :class="form.name === r.name && editing ? '' : dueCls(r)">{{ dueText(r) }}</div>
                </div>

                <div class="w-40 shrink-0">
                  <div class="text-[10px] font-bold uppercase tracking-wider opacity-60">Last PO</div>
                  <template v-if="r.last_po">
                    <div class="font-mono font-bold">{{ fmtDate(r.last_po_date) }}<span v-if="r.last_po_is_draft" class="ml-1 text-[10px] uppercase opacity-70">draft</span></div>
                    <div class="font-mono text-xs opacity-70">{{ money(r.last_po_amount) }}</div>
                  </template>
                  <div v-else class="text-sm italic opacity-60">None</div>
                  <div v-if="r.last_action" class="truncate text-[10px] opacity-70" :title="r.last_note || ''">
                    {{ r.last_action }} {{ fmtDate(r.last_action_on) }}<template v-if="r.last_note"> · {{ r.last_note }}</template>
                  </div>
                </div>

                <div v-if="r.status !== 'disabled'" class="flex shrink-0 flex-wrap gap-1.5" @click.stop>
                  <button :class="[btnCls, 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]']" :disabled="busy" @click="createPo(r)">Create PO</button>
                  <button :class="[btnCls, 'bg-[var(--color-success)] text-white']" :disabled="busy" @click="markOrdered(r)">Ordered</button>
                  <button :class="[btnCls, 'bg-[var(--color-surface-raised)] text-[var(--color-text)]']" :disabled="busy" @click="skip(r)">Skip</button>
                  <button
                    v-if="r.status === 'due' || r.status === 'overdue'"
                    :class="[btnCls, 'bg-[var(--color-surface-raised)] text-[var(--color-text)]']"
                    :disabled="busy"
                    @click="snooze(r)"
                  >
                    Snooze
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Editor -->
      <aside v-if="editing" class="overflow-y-auto border-t lg:border-t-0 lg:border-l border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
        <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
          <h2 class="text-xl font-bold">{{ form.name ? 'Edit Reminder' : 'New Reminder' }}</h2>
          <button class="rounded-lg px-2 py-1 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]" @click="closeEditor">✕</button>
        </div>

        <div class="relative">
          <label :class="labelCls">Supplier *</label>
          <input
            ref="supplierInput"
            v-model="supplierQuery"
            :class="inputCls"
            :disabled="!!form.name"
            placeholder="Type supplier name..."
            @input="searchSupplier"
            @keydown.down.prevent="supplierHighlight = Math.min(supplierHighlight + 1, supplierResults.length - 1)"
            @keydown.up.prevent="supplierHighlight = Math.max(supplierHighlight - 1, 0)"
            @keydown.enter.prevent="supplierResults[supplierHighlight] && pickSupplier(supplierResults[supplierHighlight])"
          />
          <div v-if="supplierResults.length" class="absolute z-20 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
            <button
              v-for="(s, i) in supplierResults"
              :key="s.name"
              class="block w-full truncate px-3 py-2 text-left text-sm font-semibold"
              :class="i === supplierHighlight ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'hover:bg-[var(--color-surface-raised)]'"
              @click="pickSupplier(s)"
            >
              {{ s.label }}
            </button>
          </div>
        </div>

        <div>
          <label :class="labelCls">Ordering Frequency</label>
          <div class="grid grid-cols-3 gap-1.5">
            <button v-for="f in FREQUENCIES" :key="f" :class="chipCls(form.frequency === f)" @click="form.frequency = f">{{ f }}</button>
          </div>
        </div>

        <div v-if="form.frequency === 'Weekly'">
          <label :class="labelCls">Ordering Days</label>
          <div class="grid grid-cols-7 gap-1">
            <button v-for="d in WEEKDAYS" :key="d" :class="chipCls(form.weekdays.includes(d))" @click="toggle(form.weekdays, d)">{{ d.slice(0, 3) }}</button>
          </div>
        </div>

        <div v-else-if="form.frequency === 'Monthly'">
          <label :class="labelCls">Days of Month</label>
          <div class="grid grid-cols-7 gap-1">
            <button v-for="d in 31" :key="d" :class="chipCls(form.month_days.includes(d))" @click="toggle(form.month_days, d)">{{ d }}</button>
          </div>
          <p class="mt-1 text-xs text-[var(--color-text-muted)]">29, 30 and 31 fall on the last day of a shorter month.</p>
        </div>

        <div v-else>
          <label :class="labelCls">Order Every (days)</label>
          <input v-model.number="form.interval_days" type="number" min="1" :class="[inputCls, 'font-mono text-xl font-bold']" placeholder="10" />
          <p class="mt-1 text-xs text-[var(--color-text-muted)]">Counted from the last order.</p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label :class="labelCls">Remind Before (days)</label>
            <input v-model.number="form.lead_days" type="number" min="0" :class="[inputCls, 'font-mono']" placeholder="0" />
          </div>
          <div>
            <label :class="labelCls">Start Date</label>
            <input v-model="form.start_date" type="date" :class="[inputCls, 'font-mono']" />
          </div>
        </div>

        <div>
          <label :class="labelCls">Assigned To</label>
          <select v-model="form.assigned_to" :class="inputCls">
            <option value="">Nobody</option>
            <option v-for="u in users" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
          </select>
        </div>

        <div>
          <label :class="labelCls">Notes</label>
          <textarea v-model="form.notes" rows="2" :class="inputCls" placeholder="Minimum order, contact person, what to check..."></textarea>
        </div>

        <label class="flex items-center gap-3 cursor-pointer">
          <input v-model="form.enabled" type="checkbox" class="h-5 w-5 accent-[var(--color-info)]" />
          <span class="text-sm font-semibold">Reminder active</span>
        </label>

        <div class="flex flex-wrap justify-end gap-3 pt-2">
          <button
            v-if="form.name"
            :disabled="busy"
            class="rounded-lg border border-[var(--color-danger)] px-5 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 disabled:opacity-50"
            @click="remove"
          >
            Delete
          </button>
          <button
            :disabled="busy || !form.supplier"
            class="rounded-lg bg-[var(--color-info)] px-8 py-2 text-sm font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] shadow-md hover:bg-[var(--color-info)]/80 active:scale-95 disabled:opacity-50"
            @click="save"
          >
            {{ busy ? 'Saving…' : (form.name ? 'Update (F8)' : 'Create (F8)') }}
          </button>
        </div>
      </aside>
    </main>

    <div
      v-if="toast"
      class="fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg"
      :class="toast.type === 'error' ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-success)]'"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { serverToday } from '../services/serverTime'

const router = useRouter()
const API = 'ssplbilling.api.order_reminder_api'
const FREQUENCIES = ['Weekly', 'Monthly', 'Every N Days']
const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const UPCOMING_DAYS = 7

const inputCls = 'w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-60'
const labelCls = 'block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1'
const kbdCls = 'rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]'
const btnCls = 'rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-wider shadow-sm hover:brightness-110 active:scale-95 disabled:opacity-50'
// Selected = filled, never just an outline
const chipCls = on => [
  'rounded-lg px-1 py-2 text-sm font-bold transition-colors',
  on ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:brightness-110',
]

const company = ref(localStorage.getItem('wb-company') || '')
const companies = ref([])
const reminders = ref([])
const counts = ref({})
const users = ref([])
const loading = ref(false)
const busy = ref(false)
const query = ref('')
const toast = ref(null)
const editing = ref(false)

const searchInput = ref(null)
const supplierInput = ref(null)
const supplierQuery = ref('')
const supplierResults = ref([])
const supplierHighlight = ref(0)

const blankForm = () => ({
  name: '', supplier: '', frequency: 'Weekly', weekdays: [], month_days: [], interval_days: '',
  lead_days: 0, start_date: serverToday(), assigned_to: '', notes: '', enabled: true,
})
const form = reactive(blankForm())

function showToast(message, type = 'success') {
  toast.value = { message, type }
  setTimeout(() => { if (toast.value?.message === message) toast.value = null }, 3500)
}

const userLabel = id => users.value.find(u => u.name === id)?.full_name || id
const money = v => (Number(v) || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function fmtDate(iso) {
  if (!iso) return '—'
  const [y, m, d] = String(iso).split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short' })
}

function dueText(r) {
  if (r.status === 'disabled') return 'Reminder off'
  const n = r.days_to_due
  if (n == null) return ''
  const when = n === 0 ? 'Today' : n === 1 ? 'Tomorrow' : n > 1 ? `In ${n} days` : `${-n} day${n === -1 ? '' : 's'} late`
  return r.status === 'snoozed' ? `${when} · snoozed to ${fmtDate(r.snooze_until)}` : when
}
function dueCls(r) {
  if (r.status === 'overdue') return 'text-[var(--color-danger)]'
  if (r.status === 'due') return 'text-[var(--color-warning)]'
  return 'text-[var(--color-text-muted)]'
}

const groups = computed(() => {
  const q = query.value.trim().toLowerCase()
  const rows = q ? reminders.value.filter(r => r.supplier_name.toLowerCase().includes(q)) : reminders.value
  const byDue = (a, b) => (a.due_date || '').localeCompare(b.due_date || '') || a.supplier_name.localeCompare(b.supplier_name)
  const pick = fn => rows.filter(fn).sort(byDue)
  const soon = r => r.status === 'upcoming' && r.days_to_due != null && r.days_to_due <= UPCOMING_DAYS
  return [
    { key: 'overdue', title: 'Overdue', titleCls: 'text-[var(--color-danger)]', rows: pick(r => r.status === 'overdue') },
    { key: 'due', title: 'Order Now', titleCls: 'text-[var(--color-warning)]', rows: pick(r => r.status === 'due') },
    { key: 'snoozed', title: 'Snoozed', titleCls: 'text-[var(--color-text-muted)]', rows: pick(r => r.status === 'snoozed') },
    { key: 'soon', title: `Next ${UPCOMING_DAYS} Days`, titleCls: 'text-[var(--color-text)]', rows: pick(soon) },
    { key: 'later', title: 'Later', titleCls: 'text-[var(--color-text-muted)]', rows: pick(r => r.status === 'upcoming' && !soon(r)) },
    { key: 'disabled', title: 'Switched Off', titleCls: 'text-[var(--color-text-muted)]', rows: pick(r => r.status === 'disabled') },
  ].filter(g => g.rows.length)
})

async function load() {
  loading.value = !reminders.value.length
  try {
    const data = await frappeGet(`${API}.get_reminders`, { company: company.value })
    company.value = data.company
    companies.value = data.companies || []
    reminders.value = data.reminders || []
    counts.value = data.counts || {}
  } catch (e) {
    showToast(e.message || 'Could not load reminders', 'error')
  } finally {
    loading.value = false
  }
}

function toggle(list, value) {
  const i = list.indexOf(value)
  if (i >= 0) list.splice(i, 1)
  else list.push(value)
}

function newReminder() {
  Object.assign(form, blankForm())
  supplierQuery.value = ''
  supplierResults.value = []
  editing.value = true
  nextTick(() => supplierInput.value?.focus())
}

function editReminder(r) {
  Object.assign(form, blankForm(), {
    name: r.name,
    supplier: r.supplier,
    frequency: r.frequency,
    weekdays: [...(r.weekday_list || [])],
    month_days: [...(r.month_day_list || [])],
    interval_days: r.interval_days || '',
    lead_days: r.lead_days || 0,
    start_date: r.start_date || serverToday(),
    assigned_to: r.assigned_to || '',
    notes: r.notes || '',
    enabled: !!r.enabled,
  })
  supplierQuery.value = r.supplier_name
  supplierResults.value = []
  editing.value = true
}

function closeEditor() {
  editing.value = false
  supplierResults.value = []
}

let supplierTimer = null
function searchSupplier() {
  form.supplier = ''
  clearTimeout(supplierTimer)
  const q = supplierQuery.value.trim()
  if (!q) { supplierResults.value = []; return }
  supplierTimer = setTimeout(async () => {
    try {
      const rows = await frappeGet('ssplbilling.api.item_api.search_suppliers', { query: q })
      if (supplierQuery.value.trim() !== q) return
      supplierResults.value = rows || []
      supplierHighlight.value = 0
    } catch {
      supplierResults.value = []
    }
  }, 200)
}

function pickSupplier(s) {
  form.supplier = s.name
  supplierQuery.value = s.label || s.name
  supplierResults.value = []
}

async function save() {
  if (busy.value || !editing.value) return
  if (!form.supplier) { showToast('Pick a supplier from the list', 'error'); return }
  if (form.frequency === 'Weekly' && !form.weekdays.length) { showToast('Pick at least one ordering day', 'error'); return }
  if (form.frequency === 'Monthly' && !form.month_days.length) { showToast('Pick at least one day of the month', 'error'); return }
  if (form.frequency === 'Every N Days' && !(Number(form.interval_days) >= 1)) { showToast('Enter how many days between orders', 'error'); return }
  busy.value = true
  try {
    await frappePost(`${API}.save_reminder`, {
      data: JSON.stringify({
        ...form,
        company: company.value,
        enabled: form.enabled ? 1 : 0,
        weekdays: form.weekdays.join(', '),
        month_days: form.month_days.join(', '),
      }),
    }, { silent: true })
    showToast(form.name ? 'Reminder updated' : 'Reminder added')
    closeEditor()
    await load()
  } catch (e) {
    showToast(e.message || 'Could not save', 'error')
  } finally {
    busy.value = false
  }
}

async function act(method, args, done) {
  if (busy.value) return
  busy.value = true
  try {
    await frappePost(`${API}.${method}`, args, { silent: true })
    showToast(done)
    await load()
  } catch (e) {
    showToast(e.message || 'Something went wrong', 'error')
  } finally {
    busy.value = false
  }
}

async function remove() {
  if (!form.name || !confirm(`Delete the order reminder for ${supplierQuery.value}?`)) return
  const name = form.name
  closeEditor()
  await act('delete_reminder', { name }, 'Reminder deleted')
}

function createPo(r) {
  router.push({ path: '/purchase-order', query: { supplier: r.supplier } })
}

function markOrdered(r) {
  const note = prompt(`Mark ${r.supplier_name} as ordered without a Purchase Order.\nNote (optional):`, '')
  if (note === null) return
  act('mark_ordered', { name: r.name, note }, `${r.supplier_name}: marked ordered`)
}

function skip(r) {
  const reason = prompt(`Skip this order for ${r.supplier_name}.\nReason (optional):`, '')
  if (reason === null) return
  act('skip_cycle', { name: r.name, reason }, `${r.supplier_name}: skipped to the next ordering day`)
}

function snooze(r) {
  act('snooze', { name: r.name, days: 1 }, `${r.supplier_name}: snoozed to tomorrow`)
}

function onKeydown(e) {
  if (e.key === 'F2') { e.preventDefault(); newReminder() }
  else if (e.key === 'F8') { e.preventDefault(); save() }
  else if (e.key === 'Escape') {
    e.preventDefault()
    if (supplierResults.value.length) supplierResults.value = []
    else if (editing.value) closeEditor()
    else router.push('/')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  load()
  frappeGet(`${API}.get_users`).then(rows => { users.value = rows || [] }).catch(() => {})
  nextTick(() => searchInput.value?.focus())
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  clearTimeout(supplierTimer)
})
</script>
