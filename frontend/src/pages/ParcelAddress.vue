<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)]">

    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center gap-6">
        <button class="rounded px-4 py-2 text-2xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-3xl text-[var(--color-text-muted)]">|</span>
        <span class="text-3xl font-bold text-[var(--color-text)] uppercase tracking-tight">Parcel Address</span>
        <span v-if="docName" class="rounded bg-[var(--color-surface-raised)] px-4 py-2 font-mono text-xl text-[var(--color-info)]">{{ docName }}</span>
        <span class="text-3xl text-[var(--color-text-muted)]">|</span>
        <div class="flex items-center gap-3">
          <span class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Today</span>
          <span class="font-mono text-3xl font-black text-[var(--color-success)]">{{ todayCount }} parcel{{ todayCount !== 1 ? 's' : '' }}</span>
        </div>
      </div>
      <div class="flex items-center gap-6 text-xl text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 font-mono text-lg text-[var(--color-text)]">Tab</kbd> Next field</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 font-mono text-lg text-[var(--color-text)]">End</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 font-mono text-lg text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <!-- ── BODY: SIDEBAR + MAIN ───────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── LEFT SIDEBAR (30%) ─────────────────────────────────── -->
      <aside class="flex w-[30%] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">

        <!-- Date navigator -->
        <div class="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-3 shrink-0">
          <button
            class="flex h-10 w-10 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-2xl font-bold"
            title="Previous day"
            @click="shiftDate(-1)"
          >&#8592;</button>
          <div class="flex flex-col items-center leading-none">
            <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date</span>
            <span class="text-xl font-bold text-[var(--color-text)] tabular-nums">{{ sidebarDateLabel }}</span>
          </div>
          <button
            class="flex h-10 w-10 items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition text-2xl font-bold"
            title="Next day"
            @click="shiftDate(1)"
          >&#8594;</button>
        </div>

        <!-- Entry list -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="sidebarLoading" class="flex items-center justify-center py-8">
            <span class="text-xl text-[var(--color-text-muted)]">Loading...</span>
          </div>
          <div v-else-if="!sidebarEntries.length" class="flex items-center justify-center py-8 px-3 text-center">
            <span class="text-xl italic text-[var(--color-text-muted)]">No entries</span>
          </div>
          <div v-else class="flex flex-col divide-y divide-slate-700">
            <button
              v-for="e in sidebarEntries"
              :key="e.name"
              class="w-full px-4 py-4 text-left transition"
              :class="docName === e.name
                ? 'bg-[var(--color-info)]/30 border-l-8 border-[var(--color-info)]'
                : 'hover:bg-[var(--color-surface-raised)] border-l-8 border-transparent'"
              @click="loadEntry(e.name)"
            >
              <div class="flex items-center justify-between gap-3">
                <div class="truncate font-mono text-xl font-bold" :class="docName === e.name ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">{{ e.name }}</div>
                <div class="shrink-0 text-xl font-bold" :class="docName === e.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ e.number_of_packages }} pkg</div>
              </div>
              <div class="truncate text-2xl text-[var(--color-text)] mt-2">{{ e.recipient_name }}</div>
              <div v-if="e.mobile_number" class="truncate text-xl text-[var(--color-text-muted)]">{{ e.mobile_number }}</div>
              <div v-if="e.address_line_1" class="truncate text-xl text-[var(--color-text-muted)]">{{ e.address_line_1 }}</div>
            </button>
          </div>
        </div>

        <!-- Sidebar footer -->
        <div class="shrink-0 border-t border-[var(--color-border)] px-4 py-3 text-center">
          <span class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">{{ sidebarEntries.length }} entr{{ sidebarEntries.length !== 1 ? 'ies' : 'y' }}</span>
        </div>
      </aside>

      <!-- ── MAIN CONTENT (70%) ─────────────────────────────────── -->
      <div class="flex flex-1 flex-col overflow-hidden p-8">
        <div class="flex-1 overflow-y-auto">
          <div class="max-w-6xl mx-auto flex flex-col gap-8">

            <!-- Name + Mobile + Packages -->
            <div class="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 flex flex-col gap-6">
              <div class="text-base font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Recipient Details</div>

              <div class="flex gap-6">
                <!-- Name -->
                <div class="flex flex-1 flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Name <span class="text-[var(--color-danger)]">*</span></label>
                  <input
                    ref="nameInput"
                    v-model="form.recipient_name"
                    type="text"
                    placeholder="Recipient name"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="focusMobile"
                    @keydown.tab.prevent="focusMobile"
                  />
                </div>

                <!-- Mobile -->
                <div class="flex w-[400px] flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Mobile Number</label>
                  <input
                    ref="mobileInput"
                    v-model="form.mobile_number"
                    type="text"
                    placeholder="Mobile"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="focusPackages"
                    @keydown.tab.prevent="focusPackages"
                  />
                </div>

                <!-- Packages -->
                <div class="flex w-64 flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Pkgs</label>
                  <input
                    ref="packagesInput"
                    v-model.number="form.number_of_packages"
                    type="number"
                    min="1"
                    step="1"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-right font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] tabular-nums"
                    @keydown.enter.prevent="focusLine1"
                    @keydown.tab.prevent="focusLine1"
                  />
                </div>
              </div>
            </div>

            <!-- Address -->
            <div class="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 flex flex-col gap-6">
              <div class="text-base font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Address</div>

              <div class="flex flex-col gap-6">
                <div class="flex flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Address Line 1</label>
                  <input
                    ref="line1Input"
                    v-model="form.address_line_1"
                    type="text"
                    placeholder="Street / Building"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="focusLine2"
                    @keydown.tab.prevent="focusLine2"
                  />
                </div>
                <div class="flex flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Address Line 2</label>
                  <input
                    ref="line2Input"
                    v-model="form.address_line_2"
                    type="text"
                    placeholder="Area / Landmark"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="focusLine3"
                    @keydown.tab.prevent="focusLine3"
                  />
                </div>
                <div class="flex flex-col gap-3">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Address Line 3</label>
                  <input
                    ref="line3Input"
                    v-model="form.address_line_3"
                    type="text"
                    placeholder="City / PIN"
                    class="rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-5xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                    @keydown.enter.prevent="saveEntry"
                  />
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- BOTTOM ACTIONS -->
        <div class="mt-6 flex gap-6 justify-end shrink-0">
          <button
            @click="clearForm"
            class="rounded-3xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-10 py-4 text-3xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
          >Clear</button>
          <button
            v-if="docName"
            @click="showPrint = true"
            class="rounded-3xl border-2 border-[var(--color-border)] bg-[var(--color-surface-raised)] px-10 py-4 text-3xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition flex items-center gap-6"
          >🖨 Print</button>
          <button
            @click="saveEntry"
            :disabled="saving"
            class="rounded-3xl bg-[var(--color-info)] px-16 py-4 text-3xl font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] active:scale-95 transition-all disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)]"
          >
            {{ saving ? 'Saving...' : docName ? 'Update' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── PRINT MODAL ───────────────────────────────────────────── -->
    <PrintOptionsModal
      v-if="showPrint && docName"
      :invoice-name="docName"
      doctype="Parcel Address"
      @close="showPrint = false"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappePost } from '../api.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'

const router = useRouter()
const API = 'ssplbilling.api.parcel_address_api'

// ── HELPERS ─────────────────────────────────────────────────────────
const today = new Date().toISOString().split('T')[0]

function addDays(dateStr, n) {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

function formatDateLabel(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  const t = new Date(today + 'T00:00:00')
  const diff = Math.round((d - t) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff === 1) return 'Tomorrow'
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

// ── FORM STATE ───────────────────────────────────────────────────────
const emptyForm = () => ({
  recipient_name: '',
  mobile_number: '',
  number_of_packages: 1,
  address_line_1: '',
  address_line_2: '',
  address_line_3: '',
})

const form = ref(emptyForm())
const docName = ref(null)
const saving = ref(false)
const showPrint = ref(false)

// ── TODAY COUNT ──────────────────────────────────────────────────────
const todayCount = ref(0)

async function fetchTodayCount() {
  try {
    const entries = await frappePost(`${API}.get_parcel_addresses`, { date: today, query: '' })
    todayCount.value = (entries || []).length
  } catch {
    todayCount.value = 0
  }
}

// ── SIDEBAR STATE ────────────────────────────────────────────────────
const sidebarDate = ref(today)
const sidebarEntries = ref([])
const sidebarLoading = ref(false)
const sidebarDateLabel = computed(() => formatDateLabel(sidebarDate.value))

async function fetchSidebarEntries() {
  sidebarLoading.value = true
  try {
    sidebarEntries.value = await frappePost(`${API}.get_parcel_addresses`, { date: sidebarDate.value, query: '' })
  } catch {
    sidebarEntries.value = []
  } finally {
    sidebarLoading.value = false
  }
}

function shiftDate(n) {
  sidebarDate.value = addDays(sidebarDate.value, n)
}

watch(sidebarDate, fetchSidebarEntries)

// ── REFS ─────────────────────────────────────────────────────────────
const nameInput = ref(null)
const mobileInput = ref(null)
const packagesInput = ref(null)
const line1Input = ref(null)
const line2Input = ref(null)
const line3Input = ref(null)

function focusName()     { nextTick(() => { nameInput.value?.focus(); nameInput.value?.select() }) }
function focusMobile()   { nextTick(() => { mobileInput.value?.focus(); mobileInput.value?.select() }) }
function focusPackages() { nextTick(() => { packagesInput.value?.focus(); packagesInput.value?.select() }) }
function focusLine1()    { nextTick(() => line1Input.value?.focus()) }
function focusLine2()    { nextTick(() => line2Input.value?.focus()) }
function focusLine3()    { nextTick(() => line3Input.value?.focus()) }

// ── SAVE / LOAD ──────────────────────────────────────────────────────
async function saveEntry() {
  if (!form.value.recipient_name.trim()) { alert('Enter a name'); return }

  saving.value = true
  try {
    const payload = { name: docName.value, ...form.value }
    const method = docName.value ? 'update_parcel_address' : 'create_parcel_address'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    docName.value = res.name
    sidebarDate.value = today
    await Promise.all([fetchSidebarEntries(), fetchTodayCount()])
    showPrint.value = true
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function clearForm() {
  if (form.value.recipient_name && !confirm('Clear and start a new entry?')) return
  form.value = emptyForm()
  docName.value = null
  nextTick(focusName)
}

async function loadEntry(name) {
  try {
    const d = await frappePost(`${API}.get_parcel_address`, { name })
    docName.value = d.name
    form.value = {
      recipient_name: d.recipient_name || '',
      mobile_number: d.mobile_number || '',
      number_of_packages: d.number_of_packages || 1,
      address_line_1: d.address_line_1 || '',
      address_line_2: d.address_line_2 || '',
      address_line_3: d.address_line_3 || '',
    }
    nextTick(focusName)
  } catch (e) {
    alert(e.message || 'Failed to load entry')
  }
}

// ── KEYBOARD SHORTCUTS ───────────────────────────────────────────────
function onKeydown(e) {
  if (e.key === 'End') { e.preventDefault(); saveEntry() }
  if (e.key === 'Escape') { router.push('/') }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  fetchSidebarEntries()
  fetchTodayCount()
  nextTick(focusName)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
