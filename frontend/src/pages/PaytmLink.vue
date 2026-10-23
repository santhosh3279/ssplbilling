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
        <h1 class="text-2xl font-normal uppercase tracking-tight">Receipt by Paytm Link</h1>
      </div>
      <div class="text-sm text-[var(--color-text-muted)]">
        <span v-if="!paytmEnabled" class="font-bold text-[var(--color-danger)]">Paytm is disabled in SSPL Paytm Settings</span>
        <span v-else>Esc back · F2 customer · Ctrl+Enter create link</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT: created links -->
      <aside class="flex w-[380px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold uppercase tracking-wide text-[var(--color-text-muted)]">Payment Links</span>
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
            {{ loadingLinks ? 'Loading…' : 'No payment links yet' }}
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
              <span class="truncate font-bold">{{ l.customer || '—' }}</span>
              <span class="shrink-0 font-mono font-bold">₹{{ fmt(l.amount) }}</span>
            </div>
            <div class="flex items-center justify-between gap-2 text-xs">
              <span class="truncate opacity-75">{{ l.transaction_datetime }} · {{ l.order_id }}</span>
              <span class="shrink-0 rounded px-1.5 py-0.5 font-bold uppercase" :class="statusClass(l.status)">{{ l.status }}</span>
            </div>
            <div v-if="l.status === 'Success'" class="text-xs opacity-75">
              {{ l.payment_entry ? `Receipt ${l.payment_entry}` : 'Receipt not created' }}
            </div>
          </button>
        </div>
      </aside>

      <!-- RIGHT: create form + selected link -->
      <main class="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div class="mx-auto flex max-w-2xl flex-col gap-6">
          <!-- Create -->
          <section class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <h2 class="text-lg font-bold uppercase tracking-wide">New Payment Link</h2>

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
                  @keydown.enter.prevent="createLink"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-lg text-[var(--color-text)] outline-none"
                />
              </label>
            </div>

            <label class="flex flex-col gap-1 rounded-xl p-1.5 -m-1.5 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
              <span class="text-xs font-bold uppercase opacity-75">Description <span class="normal-case opacity-75">(max 30, shown to customer)</span></span>
              <input
                ref="descInput"
                v-model="form.description"
                maxlength="30"
                placeholder="Payment to Sundaram and Sons"
                @keydown.enter.prevent="mobileInput?.focus()"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none"
              />
            </label>

            <div class="flex items-center justify-between">
              <label class="flex items-center gap-2 text-sm">
                <input v-model="form.send_sms" type="checkbox" class="h-4 w-4" />
                Paytm sends the link by SMS
              </label>
              <button
                @click="createLink"
                :disabled="creating || !paytmEnabled"
                class="rounded-xl bg-[var(--color-success)] px-6 py-2.5 text-lg font-black uppercase text-white shadow-sm transition-opacity disabled:opacity-50"
              >{{ creating ? 'Creating…' : 'Create Link' }}</button>
            </div>
            <div v-if="formError" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-bold text-[var(--color-danger)]">{{ formError }}</div>
          </section>

          <!-- Selected link -->
          <section
            v-if="selected"
            class="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ selected.order_id }}</div>
                <div class="truncate text-xl font-bold">{{ selected.customer }}</div>
                <div class="text-sm text-[var(--color-text-muted)]">{{ selected.link_description }}</div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <span class="font-mono text-3xl font-black">₹{{ fmt(selected.amount) }}</span>
                <span class="rounded px-2 py-0.5 text-sm font-bold uppercase" :class="statusClass(selected.status)">{{ selected.status }}</span>
              </div>
            </div>

            <div v-if="selected.short_url" class="flex items-center gap-2">
              <input
                :value="selected.short_url"
                readonly
                class="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-sm outline-none"
                @focus="$event.target.select()"
              />
              <button @click="copyLink(selected)" class="rounded-lg bg-[var(--color-info)] px-4 py-2 font-bold text-white">{{ copied ? 'Copied' : 'Copy' }}</button>
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
              <template v-if="selected.result_message">
                <dt class="text-[var(--color-text-muted)]">Message</dt><dd>{{ selected.result_message }}</dd>
              </template>
            </dl>

            <div class="flex justify-end gap-2">
              <button
                v-if="selected.status === 'Pending'"
                @click="checkStatus(selected)"
                :disabled="busy"
                class="rounded-lg border border-[var(--color-border)] px-4 py-2 font-bold hover:bg-[var(--color-midlight)] disabled:opacity-50"
              >Check Status</button>
              <button
                v-if="selected.status === 'Pending'"
                @click="expireLink(selected)"
                :disabled="busy"
                class="rounded-lg bg-[var(--color-danger)] px-4 py-2 font-bold text-white disabled:opacity-50"
              >Expire Link</button>
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
      subtitle="Payment link receipt"
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

const paytmEnabled = ref(true)
const links = ref([])
const loadingLinks = ref(false)
const linkSearch = ref('')
const statusFilters = ['All', 'Pending', 'Success', 'Failed', 'Cancelled']
const statusFilter = ref('All')
const selected = ref(null)
const busy = ref(false)
const copied = ref(false)

const showCustomerSearch = ref(false)
const creating = ref(false)
const formError = ref('')
const form = reactive({ customer: '', customer_name: '', amount: '', mobile: '', description: '', send_sms: false })

const customerInput = ref(null)
const amountInput = ref(null)
const descInput = ref(null)
const mobileInput = ref(null)

const fmt = (v) => Number(v || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

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

async function loadLinks() {
  loadingLinks.value = true
  try {
    links.value = await frappeGet(`${API}.get_payment_links`, { limit: 200 })
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

function selectLink(l) {
  selected.value = l
  copied.value = false
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

async function createLink() {
  formError.value = ''
  if (!form.customer) { formError.value = 'Select a customer'; return customerInput.value?.focus() }
  if (!(Number(form.amount) > 0)) { formError.value = 'Enter an amount'; return amountInput.value?.focus() }
  creating.value = true
  try {
    const r = await frappePost(`${API}.create_payment_link`, {
      customer: form.customer,
      amount: Number(form.amount),
      description: form.description,
      mobile: form.mobile,
      send_sms: form.send_sms ? 1 : 0,
    }, { silent: true })
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

async function expireLink(l) {
  if (!confirm(`Expire the link for ${l.customer} (₹${fmt(l.amount)})? The customer will no longer be able to pay it.`)) return
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

async function copyLink(l) {
  try {
    await navigator.clipboard.writeText(l.short_url)
  } catch {
    // clipboard API needs https; fall back to the selected input
    document.execCommand('copy')
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

function whatsappUrl(l) {
  const phone = String(l.customer_mobile).replace(/\D/g, '').slice(-10)
  const text = `Dear ${l.customer}, please pay ₹${fmt(l.amount)} to Sundaram and Sons using this Paytm link: ${l.short_url}`
  return `https://wa.me/91${phone}?text=${encodeURIComponent(text)}`
}

// Socket event from the webhook is the primary signal; poll today's pending links as fallback
let pollTimer = null
let polling = false
async function pollPending() {
  if (polling || document.hidden) return
  polling = true
  try {
    const today = serverToday()
    const pending = links.value.filter((l) => l.status === 'Pending' && (l.transaction_datetime || '').startsWith(today))
    for (const l of pending) await checkStatus(l, { quiet: true })
  } finally {
    polling = false
  }
}

function onPaytmSocket(r) {
  if (r?.channel === 'Link') applyResult(r)
}

function onKeydown(e) {
  if (showCustomerSearch.value) return
  if (e.key === 'Escape') { e.preventDefault(); router.push('/') }
  else if (e.key === 'F2') { e.preventDefault(); openCustomerSearch() }
  else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); createLink() }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  getFrappeSocket()?.on('paytm_payment_update', onPaytmSocket)
  try {
    paytmEnabled.value = (await frappeGet(`${API}.get_devices`)).enabled
  } catch { /* settings missing: create will report it */ }
  await loadLinks()
  pollTimer = setInterval(pollPending, POLL_MS)
  customerInput.value?.focus()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  getFrappeSocket()?.off('paytm_payment_update', onPaytmSocket)
  clearInterval(pollTimer)
})
</script>
