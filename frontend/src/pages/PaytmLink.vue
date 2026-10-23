<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-green-500/30 px-6 py-2.5 shadow-sm">
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/')"
          class="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-[var(--color-midlight)] transition-colors"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-normal uppercase tracking-tight">Paytm Receipt</h1>
      </div>
      <div class="text-sm text-[var(--color-text-muted)]">
        <span v-if="!paytmEnabled" class="font-bold text-[var(--color-danger)]">Paytm is disabled in SSPL Paytm Settings</span>
        <span v-else>Esc back · F2 customer · F4 QR / Link · Ctrl+Enter create</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT: created QRs and links -->
      <aside class="flex w-[380px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold uppercase tracking-wide text-[var(--color-text-muted)]">QR &amp; Payment Links</span>
            <button
              @click="loadLinks"
              class="rounded-md px-2 py-0.5 text-sm hover:bg-[var(--color-midlight)]"
              :disabled="loadingLinks"
            >{{ loadingLinks ? 'Loading…' : '↻ Refresh' }}</button>
          </div>
          <input
            v-model="linkSearch"
            placeholder="Search customer / order / amount"
            class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
          />
          <div class="flex flex-wrap gap-1">
            <button
              v-for="s in statusFilters"
              :key="s"
              @click="statusFilter = s"
              class="rounded-md px-2 py-0.5 text-xs font-bold uppercase"
              :class="statusFilter === s
                ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
            >{{ s }} <span class="opacity-70">{{ statusCount(s) }}</span></button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="!filteredLinks.length" class="p-6 text-center text-sm text-[var(--color-text-muted)]">
            {{ loadingLinks ? 'Loading…' : 'Nothing created yet' }}
          </div>
          <button
            v-for="l in filteredLinks"
            :key="l.order_id"
            @click="selectLink(l)"
            class="flex w-full flex-col gap-0.5 border-b border-[var(--color-border)] px-3 py-2 text-left transition-colors"
            :class="selected?.order_id === l.order_id
              ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]'
              : 'hover:bg-[var(--color-midlight)]'"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="flex min-w-0 items-center gap-1.5">
                <span class="shrink-0 rounded border border-current px-1 text-[10px] font-bold uppercase opacity-75">{{ l.channel === 'QR' ? 'QR' : 'Link' }}</span>
                <span class="truncate font-bold">{{ l.customer || '—' }}</span>
              </span>
              <span class="shrink-0 font-mono font-bold">₹{{ fmt(l.amount) }}</span>
            </div>
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="truncate opacity-75">{{ l.transaction_datetime }} · {{ l.order_id }}</span>
              <span class="shrink-0 rounded px-1.5 py-0.5 font-bold uppercase" :class="statusClass(l.status)">{{ statusLabel(l) }}</span>
            </div>
            <div v-if="l.status === 'Success'" class="text-xs opacity-75">
              {{ l.payment_entry ? `Receipt ${l.payment_entry}` : 'Receipt not created' }}
            </div>
          </button>
        </div>
      </aside>

      <!-- RIGHT: create form + selected entry -->
      <main class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div class="mx-auto flex max-w-2xl flex-col gap-6">
          <!-- Create -->
          <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-bold uppercase tracking-wide">New Receipt</h2>
              <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-0.5">
                <button
                  v-for="m in modes"
                  :key="m.id"
                  @click="mode = m.id"
                  class="rounded-md px-4 py-1 text-sm font-black uppercase tracking-wide transition-colors"
                  :class="mode === m.id
                    ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]'
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)]'"
                >{{ m.label }}</button>
              </div>
            </div>
            <p class="-mt-2 text-xs text-[var(--color-text-muted)]">
              <template v-if="mode === 'qr'">Dynamic UPI QR for the exact amount. Paytm keeps it payable for 10 minutes; once paid it cannot be paid again.</template>
              <template v-else>Paytm payment link the customer can pay later. Needs Payment Links enabled on the Paytm account.</template>
            </p>

            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">Customer</span>
              <input
                ref="customerInput"
                :value="form.customer_name"
                readonly
                placeholder="Press Enter to search customer"
                @keydown.enter.prevent="openCustomerSearch"
                @click="openCustomerSearch"
                class="w-full cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-lg text-[var(--color-text)] outline-none"
              />
            </label>

            <div class="grid grid-cols-2 gap-4">
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">Amount (₹)</span>
                <input
                  ref="amountInput"
                  v-model="form.amount"
                  type="number"
                  min="0"
                  step="0.01"
                  @keydown.enter.prevent="descInput?.focus()"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-right font-mono text-2xl font-bold text-[var(--color-text)] outline-none"
                />
              </label>
              <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <span class="text-xs font-bold uppercase opacity-75">Mobile</span>
                <input
                  ref="mobileInput"
                  v-model="form.mobile"
                  maxlength="14"
                  placeholder="10-digit mobile"
                  @keydown.enter.prevent="createEntry"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-lg text-[var(--color-text)] outline-none"
                />
              </label>
            </div>

            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">
                {{ mode === 'link' ? 'Description' : 'Remarks' }}
                <span class="normal-case opacity-75">{{ mode === 'link' ? '(max 30, shown to customer)' : '(goes on the Payment Entry)' }}</span>
              </span>
              <input
                ref="descInput"
                v-model="form.description"
                :maxlength="mode === 'link' ? 30 : 140"
                :placeholder="mode === 'link' ? 'Payment to Sundaram and Sons' : 'Optional'"
                @keydown.enter.prevent="mobileInput?.focus()"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
              />
            </label>

            <div class="flex items-center justify-between">
              <label v-if="mode === 'link'" class="flex items-center gap-2 text-sm">
                <input v-model="form.send_sms" type="checkbox" class="h-4 w-4" />
                Paytm sends the link by SMS
              </label>
              <span v-else-if="!qrEnabled" class="text-sm font-bold text-[var(--color-danger)]">Dynamic QR is disabled in SSPL Paytm Settings</span>
              <span v-else></span>
              <button
                @click="createEntry"
                :disabled="creating || !paytmEnabled || (mode === 'qr' && !qrEnabled)"
                class="rounded-xl bg-[var(--color-success)] px-6 py-2.5 text-lg font-black uppercase text-white shadow-sm transition-opacity disabled:opacity-50"
              >{{ creating ? 'Creating…' : mode === 'qr' ? 'Generate QR' : 'Create Link' }}</button>
            </div>
            <div v-if="formError" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-bold text-[var(--color-danger)]">{{ formError }}</div>
          </section>

          <!-- Selected entry -->
          <section
            v-if="selected"
            class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ selected.channel === 'QR' ? 'UPI QR' : 'Payment Link' }} · {{ selected.order_id }}</div>
                <div class="truncate text-xl font-bold">{{ selected.customer }}</div>
                <div class="text-sm text-[var(--color-text-muted)]">{{ selected.link_description }}</div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span class="font-mono text-3xl font-black">₹{{ fmt(selected.amount) }}</span>
                <span class="rounded px-2 py-0.5 text-sm font-bold uppercase" :class="statusClass(selected.status)">{{ statusLabel(selected) }}</span>
              </div>
            </div>

            <!-- QR -->
            <template v-if="selected.channel === 'QR'">
              <div v-if="selected.status === 'Success'" class="rounded-xl bg-[var(--color-success)] py-6 text-center text-white">
                <div class="text-4xl font-black uppercase">Paid</div>
                <div class="text-sm opacity-90">₹{{ fmt(selected.amount) }} via {{ selected.pay_method || 'UPI' }}</div>
              </div>
              <div v-else-if="selected.status === 'Pending' && qrSecondsLeft(selected) > 0" class="flex flex-col items-center gap-3">
                <div class="rounded-2xl bg-white p-3 shadow">
                  <img v-if="qrImages[selected.order_id]" :src="`data:image/png;base64,${qrImages[selected.order_id]}`" alt="UPI QR" class="h-64 w-64" />
                  <div v-else class="flex h-64 w-64 items-center justify-center text-sm text-gray-500">Loading QR…</div>
                </div>
                <div class="text-center">
                  <div class="font-mono text-2xl font-black" :class="qrSecondsLeft(selected) < 60 ? 'text-[var(--color-danger)]' : ''">{{ mmss(qrSecondsLeft(selected)) }}</div>
                  <div class="text-xs text-[var(--color-text-muted)]">Waiting for payment · scan with any UPI app</div>
                </div>
              </div>
              <div v-else class="rounded-xl bg-[var(--color-midlight)] py-6 text-center">
                <div class="text-xl font-bold uppercase">{{ selected.status === 'Pending' ? 'QR expired' : selected.status === 'Cancelled' ? 'Stopped waiting' : 'Payment failed' }}</div>
                <div class="text-sm text-[var(--color-text-muted)]">Not paid. Generate a new QR for the customer.</div>
              </div>
            </template>

            <!-- Link -->
            <div v-else-if="selected.short_url" class="flex items-center gap-2">
              <input
                ref="urlInput"
                :value="selected.short_url"
                readonly
                class="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-sm outline-none"
                @focus="$event.target.select()"
              />
              <button @click="copyText(selected.short_url)" class="rounded-lg bg-[var(--color-info)] px-4 py-2 font-bold text-white">{{ copied ? 'Copied' : 'Copy' }}</button>
              <a
                v-if="selected.customer_mobile"
                :href="whatsappUrl(selected)"
                target="_blank"
                rel="noopener"
                class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white"
              >WhatsApp</a>
            </div>

            <dl class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <dt class="text-[var(--color-text-muted)]">Created</dt><dd>{{ selected.transaction_datetime }} · {{ selected.owner }}</dd>
              <dt class="text-[var(--color-text-muted)]">Mobile</dt><dd>{{ selected.customer_mobile || '—' }}</dd>
              <template v-if="selected.status === 'Success'">
                <dt class="text-[var(--color-text-muted)]">Paid via</dt><dd>{{ selected.pay_method || '—' }}</dd>
                <dt class="text-[var(--color-text-muted)]">Bank ref</dt><dd class="font-mono">{{ selected.rrn || selected.paytm_txn_id || '—' }}</dd>
                <dt class="text-[var(--color-text-muted)]">Receipt</dt>
                <dd>
                  <a v-if="selected.payment_entry" :href="`/app/payment-entry/${selected.payment_entry}`" target="_blank" class="font-bold text-[var(--color-info)] underline">{{ selected.payment_entry }}</a>
                  <span v-else class="font-bold text-[var(--color-danger)]">Not created</span>
                </dd>
              </template>
              <template v-if="selected.result_message && selected.status !== 'Pending'">
                <dt class="text-[var(--color-text-muted)]">Message</dt><dd>{{ selected.result_message }}</dd>
              </template>
            </dl>

            <div class="flex flex-wrap justify-end gap-2">
              <template v-if="selected.channel === 'QR' && selected.status === 'Pending' && qrSecondsLeft(selected) > 0">
                <button v-if="canShareFiles" @click="shareQr(selected)" class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white">Share QR</button>
                <button @click="downloadQr(selected)" class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)]">Download QR</button>
              </template>
              <button
                v-if="selected.status === 'Pending'"
                @click="checkStatus(selected)"
                :disabled="busy"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
              >Check Status</button>
              <button
                v-if="selected.status === 'Pending'"
                @click="stopWaiting(selected)"
                :disabled="busy"
                class="rounded-lg bg-[var(--color-danger)] px-4 py-2 font-bold text-white disabled:opacity-50"
              >{{ selected.channel === 'QR' ? 'Stop Waiting' : 'Expire Link' }}</button>
              <button
                v-if="selected.channel === 'QR' && selected.status !== 'Success' && qrSecondsLeft(selected) === 0"
                @click="regenerateQr(selected)"
                :disabled="creating"
                class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white disabled:opacity-50"
              >New QR</button>
              <button
                v-if="selected.status === 'Success' && !selected.payment_entry"
                @click="retryReceipt(selected)"
                :disabled="busy"
                class="rounded-lg bg-[var(--color-warning)] px-4 py-2 font-bold text-white disabled:opacity-50"
              >Create Receipt</button>
            </div>
          </section>
        </div>
      </main>
    </div>

    <CustomerSearchModal
      :show="showCustomerSearch"
      title="Select Customer"
      subtitle="Paytm receipt"
      :allowedTypes="['Customer']"
      initialType="Customer"
      :skipDateFilter="true"
      :hideSecondary="true"
      @close="showCustomerSearch = false"
      @select="onCustomerSelect"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { getFrappeSocket } from '../services/frappeSocket.js'
import { serverToday } from '../services/serverTime'

const router = useRouter()
const API = 'ssplbilling.api.paytm_api'
const POLL_MS = 10000
// A shown QR is checked this often; the socket event usually arrives first
const QR_POLL_MS = 4000

const paytmEnabled = ref(true)
const qrEnabled = ref(true)
const modes = [{ id: 'qr', label: 'UPI QR' }, { id: 'link', label: 'Payment Link' }]
const mode = ref('qr')

const links = ref([])
const loadingLinks = ref(false)
const linkSearch = ref('')
const statusFilters = ['All', 'Pending', 'Success', 'Failed', 'Cancelled']
const statusFilter = ref('All')
const selected = ref(null)
const busy = ref(false)
const copied = ref(false)

// QR images by order id (only returned on create / get_receipt_qr), and each QR's expiry instant
const qrImages = reactive({})
const qrDeadlines = reactive({})
const nowMs = ref(Date.now())

const showCustomerSearch = ref(false)
const creating = ref(false)
const formError = ref('')
const form = reactive({ customer: '', customer_name: '', amount: '', mobile: '', description: '', send_sms: false })

const customerInput = ref(null)
const amountInput = ref(null)
const descInput = ref(null)
const mobileInput = ref(null)
const urlInput = ref(null)

const canShareFiles = typeof navigator !== 'undefined' && !!navigator.canShare

const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const mmss = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

const filteredLinks = computed(() => {
  const q = linkSearch.value.trim().toLowerCase()
  return links.value.filter((l) => {
    if (statusFilter.value !== 'All' && l.status !== statusFilter.value) return false
    if (!q) return true
    return [l.customer, l.order_id, l.customer_mobile, l.payment_entry, String(l.amount)]
      .some((v) => (v || '').toLowerCase().includes(q))
  })
})

function statusCount(s) {
  return s === 'All' ? links.value.length : links.value.filter((l) => l.status === s).length
}

function statusClass(status) {
  return {
    Success: 'bg-[var(--color-success)] text-white',
    Pending: 'bg-[var(--color-warning)] text-white',
    Failed: 'bg-[var(--color-danger)] text-white',
    Cancelled: 'bg-[var(--color-midlight)] text-[var(--color-text)]',
  }[status] || 'bg-[var(--color-midlight)]'
}

function statusLabel(l) {
  if (l.channel === 'QR' && l.status === 'Pending' && qrSecondsLeft(l) === 0) return 'Expired'
  return l.status === 'Success' ? 'Paid' : l.status
}

// expires_in comes from the server (seconds), so the countdown does not depend on the PC clock
// (0 = already expired: keep an earlier deadline, or none, so a reload does not restart the grace)
function setDeadline(orderId, expiresIn) {
  if (Number(expiresIn) > 0) qrDeadlines[orderId] = Date.now() + Number(expiresIn) * 1000
}

function qrSecondsLeft(l) {
  const d = qrDeadlines[l.order_id]
  return d ? Math.max(0, Math.round((d - nowMs.value) / 1000)) : 0
}

async function loadLinks() {
  loadingLinks.value = true
  try {
    links.value = await frappeGet(`${API}.get_payment_links`, { limit: 200 })
    for (const l of links.value) setDeadline(l.order_id, l.expires_in)
    if (selected.value) selected.value = links.value.find((l) => l.order_id === selected.value.order_id) || null
  } catch (e) {
    formError.value = e.message
  } finally {
    loadingLinks.value = false
  }
}

// Merge a get_status / socket result into the list row (result keys differ from list fields)
function applyResult(r) {
  if (!r?.order_id) return
  const row = links.value.find((l) => l.order_id === r.order_id)
  if (!row) return loadLinks()
  Object.assign(row, {
    status: r.status,
    amount: r.amount,
    pay_method: r.pay_method,
    payment_entry: r.payment_entry,
    result_message: r.message,
    short_url: r.short_url || row.short_url,
  })
  if (r.reference_no && r.reference_no !== r.order_id) row.rrn = r.reference_no
}

async function selectLink(l) {
  selected.value = l
  copied.value = false
  if (l.channel === 'QR' && l.status === 'Pending' && qrSecondsLeft(l) > 0 && !qrImages[l.order_id]) {
    try {
      const r = await frappeGet(`${API}.get_receipt_qr`, { order_id: l.order_id })
      qrImages[l.order_id] = r.qr_image
      setDeadline(l.order_id, r.expires_in)
    } catch (e) {
      formError.value = e.message
    }
  }
}

function openCustomerSearch() {
  showCustomerSearch.value = true
}

function onCustomerSelect(item) {
  showCustomerSearch.value = false
  form.customer = item.name
  form.customer_name = item.label || item.customer_name || item.name
  if (item.mobile_no) form.mobile = item.mobile_no
  nextTick(() => amountInput.value?.focus())
}

function resetForm() {
  Object.assign(form, { customer: '', customer_name: '', amount: '', mobile: '', description: '', send_sms: false })
}

async function createEntry() {
  formError.value = ''
  if (!form.customer) { formError.value = 'Select a customer'; return customerInput.value?.focus() }
  if (!(Number(form.amount) > 0)) { formError.value = 'Enter an amount'; return amountInput.value?.focus() }
  const args = { customer: form.customer, amount: Number(form.amount), description: form.description, mobile: form.mobile }
  if (mode.value === 'qr') await createQr(args)
  else await createLink({ ...args, send_sms: form.send_sms ? 1 : 0 })
}

async function createQr(args) {
  creating.value = true
  try {
    const r = await frappePost(`${API}.create_receipt_qr`, args, { silent: true })
    qrImages[r.order_id] = r.qr_image
    setDeadline(r.order_id, r.expires_in)
    resetForm()
    await loadLinks()
    selected.value = links.value.find((l) => l.order_id === r.order_id) || null
  } catch (e) {
    formError.value = e.message
    loadLinks() // the failed attempt is recorded too
  } finally {
    creating.value = false
  }
}

async function createLink(args) {
  creating.value = true
  try {
    const r = await frappePost(`${API}.create_payment_link`, args, { silent: true })
    resetForm()
    await loadLinks()
    selected.value = links.value.find((l) => l.order_id === r.order_id) || null
  } catch (e) {
    formError.value = e.message
    loadLinks()
  } finally {
    creating.value = false
  }
}

// Same customer and amount as an expired / stopped QR
function regenerateQr(l) {
  formError.value = ''
  createQr({ customer: l.customer, amount: l.amount, description: l.link_description, mobile: l.customer_mobile })
}

async function checkStatus(l, { quiet = false } = {}) {
  if (!quiet) busy.value = true
  try {
    applyResult(await frappePost(`${API}.get_status`, { order_id: l.order_id }, { silent: true }))
  } catch (e) {
    if (!quiet) formError.value = e.message
  } finally {
    if (!quiet) busy.value = false
  }
}

async function stopWaiting(l) {
  const msg = l.channel === 'QR'
    ? `Stop waiting for ₹${fmt(l.amount)} from ${l.customer}?\n\nPaytm cannot cancel a QR: it stays payable until it expires. If the customer still pays, the receipt is still posted.`
    : `Expire the link for ${l.customer} (₹${fmt(l.amount)})? The customer will no longer be able to pay it.`
  if (!confirm(msg)) return
  busy.value = true
  try {
    applyResult(await frappePost(`${API}.cancel`, { order_id: l.order_id }, { silent: true }))
  } catch (e) {
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

async function retryReceipt(l) {
  busy.value = true
  try {
    applyResult(await frappePost(`${API}.retry_link_receipt`, { order_id: l.order_id }, { silent: true }))
  } catch (e) {
    formError.value = e.message
  } finally {
    busy.value = false
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // clipboard API needs https (store terminals use http on the LAN); copy from the input instead
    urlInput.value?.select()
    if (!document.execCommand('copy')) return
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

function qrFile(l) {
  const bytes = Uint8Array.from(atob(qrImages[l.order_id]), (c) => c.charCodeAt(0))
  return new File([bytes], `paytm-qr-${l.order_id}.png`, { type: 'image/png' })
}

// Phone / tablet: hands the QR image to WhatsApp or any other app
async function shareQr(l) {
  const file = qrFile(l)
  const text = `Dear ${l.customer}, please scan this QR to pay ₹${fmt(l.amount)} to Sundaram and Sons. Valid for ${Math.ceil(qrSecondsLeft(l) / 60)} minutes.`
  if (!navigator.canShare({ files: [file] })) return downloadQr(l)
  try {
    await navigator.share({ files: [file], text })
  } catch { /* share sheet closed */ }
}

function downloadQr(l) {
  const url = URL.createObjectURL(qrFile(l))
  const a = document.createElement('a')
  a.href = url
  a.download = `paytm-qr-${l.order_id}.png`
  a.click()
  URL.revokeObjectURL(url)
}

function whatsappUrl(l) {
  const phone = String(l.customer_mobile).replace(/\D/g, '').slice(-10)
  const text = `Dear ${l.customer}, please pay ₹${fmt(l.amount)} to Sundaram and Sons using this Paytm link: ${l.short_url}`
  return `https://wa.me/91${phone}?text=${encodeURIComponent(text)}`
}

// Socket event from the webhook is the primary signal; polling is the fallback:
// the shown QR every few seconds, today's other pending entries less often
let pollTimer = null
let qrPollTimer = null
let tickTimer = null
let polling = false
async function pollPending() {
  if (polling || document.hidden) return
  polling = true
  try {
    const today = serverToday()
    const pending = links.value.filter((l) => l.status === 'Pending'
      && (l.transaction_datetime || '').startsWith(today)
      && (l.channel !== 'QR' || qrStillLive(l)))
    for (const l of pending) await checkStatus(l, { quiet: true })
  } finally {
    polling = false
  }
}

// keeps checking a minute past expiry, for a payment started just before it;
// the scheduler picks up anything later
function qrStillLive(l) {
  return nowMs.value - (qrDeadlines[l.order_id] || 0) < 60000
}

function pollSelectedQr() {
  const l = selected.value
  if (!l || l.channel !== 'QR' || l.status !== 'Pending' || document.hidden || !qrStillLive(l)) return
  checkStatus(l, { quiet: true })
}

function onPaytmSocket(r) {
  if (r?.customer) applyResult(r)
}

function onKeydown(e) {
  if (showCustomerSearch.value) return
  if (e.key === 'Escape') { e.preventDefault(); router.push('/') }
  else if (e.key === 'F2') { e.preventDefault(); openCustomerSearch() }
  else if (e.key === 'F4') { e.preventDefault(); mode.value = mode.value === 'qr' ? 'link' : 'qr' }
  else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); createEntry() }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  getFrappeSocket()?.on('paytm_payment_update', onPaytmSocket)
  try {
    const s = await frappeGet(`${API}.get_devices`)
    paytmEnabled.value = s.enabled
    qrEnabled.value = s.qr_enabled
    if (!s.qr_enabled) mode.value = 'link'
  } catch { /* settings missing: create will report it */ }
  await loadLinks()
  pollTimer = setInterval(pollPending, POLL_MS)
  qrPollTimer = setInterval(pollSelectedQr, QR_POLL_MS)
  tickTimer = setInterval(() => { nowMs.value = Date.now() }, 1000)
  customerInput.value?.focus()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  getFrappeSocket()?.off('paytm_payment_update', onPaytmSocket)
  clearInterval(pollTimer)
  clearInterval(qrPollTimer)
  clearInterval(tickTimer)
})
</script>
