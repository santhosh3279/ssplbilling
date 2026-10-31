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
        <span v-else>Esc back · F2 customer · Ctrl+Enter send to machine · F8 send request</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT: created QRs -->
      <aside class="flex w-[380px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm font-bold uppercase tracking-wide text-[var(--color-text-muted)]">QRs &amp; Requests</span>
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
                <span class="shrink-0 rounded border border-current px-1 text-[10px] font-bold uppercase opacity-75">{{ isRequest(l) ? 'Req' : isMachine(l) ? 'POS' : 'QR' }}</span>
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

      <!-- RIGHT: entry row + selected QR + action footer (paymentv2 layout) -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <main class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <div class="flex flex-col gap-4">
            <!-- Entry row (table style) -->
            <div class="shrink-0 overflow-hidden rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl">
              <table class="w-full border-collapse text-left">
                <thead class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]">
                  <tr class="text-3xl font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                    <th class="w-1/2 px-4 py-2">Customer</th>
                    <th class="w-64 px-4 py-2 text-right text-[var(--color-success)]">Amount (Cr)</th>
                    <th class="w-72 px-4 py-2">WhatsApp</th>
                    <th class="w-64 px-6 py-2 text-right">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="divide-x divide-[var(--color-border)]">
                    <td class="group px-2 py-1.5 transition-colors hover:bg-[var(--color-midlight)]/20 focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                      <div class="relative">
                        <input
                          ref="customerInput"
                          :value="form.customer_name"
                          readonly
                          placeholder="Search Customer..."
                          @keydown.enter.prevent="openCustomerSearch"
                          @click="openCustomerSearch"
                          class="w-full cursor-pointer bg-transparent text-4xl font-normal placeholder:text-inherit focus:outline-none"
                        />
                        <div class="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] font-bold text-[var(--color-highlight)] opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:text-[var(--color-text-on-focus)]">CLICK TO SEARCH</div>
                      </div>
                    </td>
                    <td class="bg-[var(--color-success)]/5 px-4 py-1.5 transition-colors focus-within:bg-[var(--color-focus)]">
                      <input
                        ref="amountInput"
                        v-model="form.amount"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        @keydown.enter.prevent="mobileInput?.focus()"
                        class="w-full bg-transparent text-right text-5xl font-light text-[var(--color-text)] placeholder:text-inherit focus:text-[var(--color-text-on-focus)] focus:outline-none"
                      />
                    </td>
                    <td class="px-4 py-1.5 transition-colors focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                      <input
                        ref="mobileInput"
                        v-model="form.mobile"
                        maxlength="14"
                        placeholder="WhatsApp / mobile"
                        @keydown.enter.prevent="descInput?.focus()"
                        class="w-full bg-transparent font-mono text-3xl placeholder:text-inherit focus:outline-none"
                      />
                    </td>
                    <td class="bg-[var(--color-surface-raised)] px-6 py-1.5 text-right">
                      <div v-if="ledgerBalance !== null" class="text-4xl font-black" :class="ledgerBalance > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                        {{ Math.abs(ledgerBalance).toLocaleString('en-IN') }} {{ ledgerBalance > 0 ? 'Dr' : 'Cr' }}
                      </div>
                      <div v-else class="text-xl font-medium italic text-[var(--color-text-muted)]">—</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Selected QR -->
            <div
              v-if="selected"
              class="flex flex-col gap-4 rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-lg"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                  <div class="text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)]">{{ isRequest(selected) ? 'Payment Request' : isMachine(selected) ? 'Card Machine' : 'UPI QR' }} · {{ selected.order_id }}</div>
                  <div class="truncate text-4xl font-normal">{{ selected.customer }}</div>
                  <div class="text-sm text-[var(--color-text-muted)]">{{ selected.link_description }}</div>
                </div>
                <div class="flex flex-col items-end gap-1">
                  <span class="text-5xl font-black">₹{{ fmt(selected.amount) }}</span>
                  <span class="rounded px-2 py-0.5 text-sm font-bold uppercase" :class="statusClass(selected.status)">{{ statusLabel(selected) }}</span>
                </div>
              </div>

              <div class="flex gap-6">
                <!-- QR / result -->
                <div class="flex w-80 shrink-0 flex-col items-center justify-center">
                  <div v-if="selected.status === 'Success'" class="w-full rounded-2xl bg-[var(--color-success)] py-10 text-center text-white">
                    <div class="text-5xl font-black uppercase">Paid</div>
                    <div class="text-sm opacity-90">₹{{ fmt(selected.amount) }} via {{ selected.pay_method || 'UPI' }}</div>
                  </div>
                  <div v-else-if="isRequest(selected) && selected.status === 'Pending'" class="w-full rounded-2xl bg-[var(--color-info)]/15 px-4 py-10 text-center">
                    <div class="text-2xl font-black uppercase">Request sent</div>
                    <div class="font-mono text-lg">+91 {{ selected.customer_mobile }}</div>
                    <div class="mt-1 text-xs text-[var(--color-text-muted)]">Waiting for the customer to pay in their UPI app</div>
                  </div>
                  <div v-else-if="isMachine(selected) && selected.status === 'Pending'" class="w-full rounded-2xl bg-[var(--color-info)]/15 px-4 py-10 text-center">
                    <div class="text-2xl font-black uppercase">Sent to machine</div>
                    <div class="font-mono text-lg">{{ selected.device_name }}</div>
                    <div class="mt-1 text-xs text-[var(--color-text-muted)]">Waiting for the customer to scan and pay on the machine</div>
                  </div>
                  <div v-else-if="selected.status === 'Pending' && qrSecondsLeft(selected) > 0" class="flex flex-col items-center gap-3">
                    <div class="rounded-2xl bg-white p-3 shadow">
                      <img v-if="qrImages[selected.order_id]" :src="`data:image/png;base64,${qrImages[selected.order_id]}`" alt="UPI QR" class="h-64 w-64" />
                      <div v-else class="flex h-64 w-64 items-center justify-center text-sm text-gray-500">Loading QR…</div>
                    </div>
                    <div class="text-center">
                      <div class="font-mono text-3xl font-black" :class="qrSecondsLeft(selected) < 60 ? 'text-[var(--color-danger)]' : ''">{{ mmss(qrSecondsLeft(selected)) }}</div>
                      <div class="text-xs text-[var(--color-text-muted)]">Waiting for payment · scan with any UPI app</div>
                    </div>
                  </div>
                  <div v-else class="w-full rounded-2xl bg-[var(--color-midlight)] py-10 text-center">
                    <div class="text-2xl font-bold uppercase">{{ qrExpired(selected) ? 'QR expired' : selected.status === 'Cancelled' ? 'Stopped waiting' : 'Payment failed' }}</div>
                    <div class="text-sm text-[var(--color-text-muted)]">Not paid. {{ isRequest(selected) ? 'Send a new request' : isMachine(selected) ? 'Send it to the machine again' : 'Generate a new QR' }} for the customer.</div>
                  </div>
                </div>

                <!-- Details + actions -->
                <div class="flex min-w-0 flex-1 flex-col justify-between gap-4">
                  <dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 text-lg">
                    <dt class="text-[var(--color-text-muted)]">Created</dt><dd>{{ selected.transaction_datetime }} · {{ selected.owner }}</dd>
                    <dt class="text-[var(--color-text-muted)]">Mobile</dt><dd>{{ selected.customer_mobile || '—' }}</dd>
                    <template v-if="isMachine(selected)">
                      <dt class="text-[var(--color-text-muted)]">Machine</dt><dd>{{ selected.device_name || '—' }}</dd>
                    </template>
                    <template v-if="selected.status === 'Success'">
                      <dt class="text-[var(--color-text-muted)]">Paid via</dt><dd>{{ selected.pay_method || '—' }}</dd>
                      <dt class="text-[var(--color-text-muted)]">Bank ref</dt><dd class="font-mono">{{ selected.rrn || selected.paytm_txn_id || '—' }}</dd>
                      <dt class="text-[var(--color-text-muted)]">Receipt</dt>
                      <dd>
                        <a v-if="selected.payment_entry" :href="`/app/payment-entry/${selected.payment_entry}`" target="_blank" class="font-bold text-[var(--color-info)] underline">{{ selected.payment_entry }}</a>
                        <span v-else class="font-bold text-[var(--color-danger)]">Not created</span>
                      </dd>
                    </template>
                    <template v-if="waResult[selected.order_id]">
                      <dt class="text-[var(--color-text-muted)]">WhatsApp</dt>
                      <dd class="font-bold" :class="waResult[selected.order_id].ok ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">{{ waResult[selected.order_id].text }}</dd>
                    </template>
                    <template v-if="selected.result_message && selected.status !== 'Pending'">
                      <dt class="text-[var(--color-text-muted)]">Message</dt><dd>{{ selected.result_message }}</dd>
                    </template>
                  </dl>

                  <div class="flex flex-wrap justify-end gap-2">
                    <template v-if="payLinkLive(selected)">
                      <button @click="copyText(payUrl(selected))" class="rounded-lg bg-[var(--color-info)] px-4 py-2 font-bold text-white">{{ copied ? 'Copied' : 'Copy Link' }}</button>
                      <button
                        v-if="selected.customer_mobile"
                        @click="sendPayLink(selected)"
                        :disabled="waSending[selected.order_id]"
                        :title="selected.channel === 'QR' ? 'Sends the pay QR picture to the customer\'s WhatsApp through OpenWA' : 'Sends the pay link to the customer\'s WhatsApp through OpenWA'"
                        class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white disabled:opacity-50"
                      >{{ waSending[selected.order_id] ? 'Sending…' : waResult[selected.order_id]?.ok ? 'Send Again' : selected.channel === 'QR' ? 'Send QR on WhatsApp' : 'Send Link on WhatsApp' }}</button>
                    </template>
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
                    >Stop Waiting</button>
                    <button
                      v-if="selected.channel === 'QR' && selected.status !== 'Success' && qrSecondsLeft(selected) === 0"
                      @click="regenerateQr(selected)"
                      :disabled="creating"
                      class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white disabled:opacity-50"
                    >New QR</button>
                    <button
                      v-if="isMachine(selected) && !['Pending', 'Success'].includes(selected.status)"
                      @click="resendToMachine(selected)"
                      :disabled="creating || !machines.length"
                      class="rounded-lg bg-[var(--color-success)] px-4 py-2 font-bold text-white disabled:opacity-50"
                    >Send Again</button>
                    <button
                      v-if="selected.status === 'Success' && !selected.payment_entry"
                      @click="retryReceipt(selected)"
                      :disabled="busy"
                      class="rounded-lg bg-[var(--color-warning)] px-4 py-2 font-bold text-white disabled:opacity-50"
                    >Create Receipt</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Empty state placeholder -->
            <div v-else class="flex flex-col items-center justify-center gap-2 py-24 opacity-10">
              <svg class="h-32 w-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h2v2h-2v-2zm4 0h2v2h-2v-2zm-4 4h2v2h-2v-2zm4 0h2v2h-2v-2z" />
              </svg>
            </div>
          </div>
        </main>

        <!-- Bottom action bar -->
        <footer class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-[0_-4px_20px_rgba(0,0,0,0.1)]">
          <div class="flex items-center justify-between gap-8">
            <div class="flex flex-1 items-center gap-8">
              <div class="-m-1.5 flex max-w-xl flex-1 flex-col gap-1.5 rounded-xl p-1.5 transition-all focus-within:bg-[var(--color-focus)] focus-within:text-[var(--color-text-on-focus)]">
                <label class="ml-1 text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Remarks · goes on the Payment Entry</label>
                <textarea
                  ref="descInput"
                  v-model="form.description"
                  rows="2"
                  maxlength="140"
                  placeholder="Optional"
                  @keydown.enter.prevent="generateBtn?.focus()"
                  class="w-full resize-none rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-3 text-xl font-bold transition-all placeholder:text-inherit focus:bg-black/5 focus:outline-none"
                ></textarea>
              </div>
              <div class="flex min-w-0 flex-col gap-1 text-sm">
                <span v-if="!machines.length" class="font-bold text-[var(--color-danger)]">No card machine is assigned to you in SSPL Paytm Settings</span>
                <span v-else class="text-[var(--color-text-muted)]">Send to Machine: the amount goes to {{ machines[0].device_name }}, which shows its UPI QR.</span>
                <span v-if="!qrEnabled" class="font-bold text-[var(--color-danger)]">Dynamic QR is disabled in SSPL Paytm Settings</span>
                <span v-else class="text-[var(--color-text-muted)]">Send Request: makes a QR and sends its picture to the customer's WhatsApp.</span>
                <span v-if="formError" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-1.5 font-bold text-[var(--color-danger)]">{{ formError }}</span>
              </div>
            </div>

            <div class="flex items-center gap-4 border-l border-[var(--color-border)] pl-8">
              <button
                @click="createRequest"
                :disabled="creating || !paytmEnabled || !qrEnabled"
                title="Generates a QR and sends its picture to the customer's WhatsApp (F8)"
                class="rounded-2xl bg-[var(--color-info)] px-8 py-6 text-2xl font-black text-white shadow-xl transition-all hover:scale-[1.02] focus:scale-[1.02] focus:outline-none focus:ring-[10px] focus:ring-[var(--color-focus)] active:scale-95 disabled:opacity-40 disabled:grayscale disabled:hover:scale-100"
              >Send Request</button>
              <button
                ref="generateBtn"
                @click="createEntry"
                :disabled="creating || !paytmEnabled || !machines.length"
                title="Sends the amount to your card machine, which shows its UPI QR (Ctrl+Enter)"
                class="group relative flex items-center gap-4 overflow-hidden rounded-2xl bg-[var(--color-success)] px-16 py-6 text-4xl font-black text-[var(--color-text-on-highlight)] shadow-xl transition-all hover:scale-[1.02] hover:shadow-2xl focus:scale-[1.02] focus:outline-none focus:ring-[10px] focus:ring-[var(--color-focus)] active:scale-95 disabled:opacity-40 disabled:grayscale disabled:hover:scale-100"
              >
                <span v-if="creating" class="flex items-center gap-3">
                  <svg class="h-10 w-10 animate-spin" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </span>
                <span v-else class="flex items-center gap-4">
                  Send to Machine
                  <svg class="h-10 w-10 transition-transform group-hover:translate-x-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        </footer>
      </div>
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
import { session, getWhatsAppSessionId } from '../session.js'

const router = useRouter()
const API = 'ssplbilling.api.paytm_api'
const POLL_MS = 10000
// A shown QR or a machine request is checked this often; the socket event usually arrives first
const QR_POLL_MS = 4000

const paytmEnabled = ref(true)
const qrEnabled = ref(true)
// card machines assigned to this user; Send to Machine uses the first, as the POS panel does
const machines = ref([])

const links = ref([])
const loadingLinks = ref(false)
const linkSearch = ref('')
const statusFilters = ['All', 'Pending', 'Success', 'Failed', 'Cancelled']
const statusFilter = ref('All')
const selected = ref(null)
const busy = ref(false)

// QR images by order id (only returned on create / get_receipt_qr), and each QR's expiry instant
const qrImages = reactive({})
const qrDeadlines = reactive({})
const nowMs = ref(Date.now())

const showCustomerSearch = ref(false)
const creating = ref(false)
const formError = ref('')
const form = reactive({ customer: '', customer_name: '', amount: '', mobile: '', description: '' })
const ledgerBalance = ref(null)

const customerInput = ref(null)
const amountInput = ref(null)
const descInput = ref(null)
const mobileInput = ref(null)
const generateBtn = ref(null)
const copied = ref(false)
// OpenWA send of a receipt's pay link, by order id
const waSending = reactive({})
const waResult = reactive({})

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

// The server marks an unpaid receipt QR Cancelled with this message once Paytm closes the order
const QR_EXPIRED_MSG = 'QR expired unpaid'

// Payment requests are "Link" rows with a PRQ order id (old /link/create links stay hidden)
const REQUEST_PREFIX = 'PRQ'
function isRequest(l) {
  return l.channel === 'Link' && (l.order_id || '').startsWith(REQUEST_PREFIX)
}

function isMachine(l) {
  return l.channel === 'EDC'
}

function qrExpired(l) {
  return l.channel === 'QR' && ((l.status === 'Pending' && qrSecondsLeft(l) === 0)
    || (l.status === 'Cancelled' && l.result_message === QR_EXPIRED_MSG))
}

function statusLabel(l) {
  if (qrExpired(l)) return 'Expired'
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
    // the server also returns old payment links; this page handles QRs, machine receipts and payment requests only
    links.value = (await frappeGet(`${API}.get_payment_links`, { limit: 200 }))
      .filter((l) => l.channel === 'QR' || isMachine(l) || isRequest(l))
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
  form.mobile = item.whatsapp || item.mobile_no || ''
  fetchLedgerBalance(item.name)
  fetchMobile(item.name, form.mobile)
  nextTick(() => amountInput.value?.focus())
}

// WhatsApp number, else mobile. Search results can lack both (they may live only on the
// linked Contact), so the server has the final say
async function fetchMobile(customer, prefilled) {
  try {
    const mobile = await frappeGet(`${API}.get_customer_whatsapp`, { customer })
    // keep a number the operator already typed, and ignore a late reply for another customer
    if (mobile && form.customer === customer && form.mobile === prefilled) form.mobile = mobile
  } catch { /* operator can still type it */ }
}

// Customer's ledger closing balance (positive = Dr, they owe us)
async function fetchLedgerBalance(customer) {
  ledgerBalance.value = null
  try {
    const res = await frappeGet('ssplbilling.api.paymentv2_api.get_ledger', {
      ledger_name: customer,
      ledger_type: 'Customer',
      company: localStorage.getItem('wb-company') || '',
    })
    // ignore a late reply for a customer that is no longer selected
    if (form.customer === customer && res?.closing_balance !== undefined) ledgerBalance.value = res.closing_balance
  } catch { /* balance is informational only */ }
}

function resetForm() {
  Object.assign(form, { customer: '', customer_name: '', amount: '', mobile: '', description: '' })
  ledgerBalance.value = null
}

function formArgs() {
  formError.value = ''
  if (!form.customer) { formError.value = 'Select a customer'; customerInput.value?.focus(); return null }
  if (!(Number(form.amount) > 0)) { formError.value = 'Enter an amount'; amountInput.value?.focus(); return null }
  return { customer: form.customer, amount: Number(form.amount), description: form.description, mobile: form.mobile }
}

// operator defaults: the receipt is debited to wb-upi under wb-company / wb-cost-center
function accountArgs() {
  return {
    company: localStorage.getItem('wb-company') || '',
    cost_center: localStorage.getItem('wb-cost-center') || '',
    upi_account: localStorage.getItem('wb-upi') || '',
  }
}

async function createEntry() {
  const args = formArgs()
  if (args) await sendToMachine(args)
}

// same machine user as the POS panel: an admin's inherited user, else the logged-in user
function machineUser() {
  let inherited = ''
  try { inherited = localStorage.getItem('wb-inherited-user') || '' } catch { /* storage blocked */ }
  return inherited || session.user.value
}

// The machine opens on its UPI QR; the webhook / polling posts the receipt once paid
async function sendToMachine(args) {
  creating.value = true
  try {
    const r = await frappePost(`${API}.send_receipt_to_device`, {
      ...args, ...accountArgs(), tid: machines.value[0]?.tid, user: machineUser(),
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

// Same customer and amount as a failed / stopped machine receipt
function resendToMachine(l) {
  formError.value = ''
  sendToMachine({ customer: l.customer, amount: l.amount, description: l.link_description, mobile: l.customer_mobile })
}

// Generate QR, then send its UPI link (the QR's own upi://pay string) on WhatsApp
async function createRequest() {
  const args = formArgs()
  if (!args) return
  if (!/^\d{10}$/.test(String(args.mobile).replace(/\D/g, '').slice(-10))) {
    formError.value = 'Enter the 10-digit WhatsApp / mobile number'
    return mobileInput.value?.focus()
  }
  await createQr(args, { sendLink: true })
}

// Receipt QRs: their UPI string (pay_url, what scanning gives); old payment requests: Paytm link (short_url)
function payUrl(l) {
  return l.channel === 'QR' ? l.pay_url : l.short_url
}

function payLinkLive(l) {
  if (l.status !== 'Pending' || !payUrl(l)) return false
  return l.channel !== 'QR' || qrSecondsLeft(l) > 0
}

// The QR stands even when WhatsApp fails; the button on the entry retries the send
async function sendPayLink(l) {
  if (waSending[l.order_id]) return
  waSending[l.order_id] = true
  try {
    const sent = await frappePost('ssplbilling.api.whatsapp_api.send_receipt_pay_link', {
      order_id: l.order_id,
      session_id: getWhatsAppSessionId(),
    }, { silent: true })
    waResult[l.order_id] = { ok: true, text: `${l.channel === 'QR' ? 'QR' : 'Link'} sent to +${sent.phone}` }
  } catch (e) {
    waResult[l.order_id] = { ok: false, text: `Not sent: ${e.message || e}` }
  } finally {
    waSending[l.order_id] = false
  }
}

async function createQr(args, { sendLink = false } = {}) {
  creating.value = true
  try {
    const r = await frappePost(`${API}.create_receipt_qr`, { ...args, ...accountArgs() }, { silent: true })
    qrImages[r.order_id] = r.qr_image
    setDeadline(r.order_id, r.expires_in)
    resetForm()
    await loadLinks()
    selected.value = links.value.find((l) => l.order_id === r.order_id) || null
    if (sendLink && selected.value) sendPayLink(selected.value)
  } catch (e) {
    formError.value = e.message
    loadLinks() // the failed attempt is recorded too
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
  const what = isRequest(l) ? 'a payment request: it stays payable on the customer\'s phone' : 'a QR: it stays payable until it expires'
  const msg = isMachine(l)
    ? `Stop waiting for ₹${fmt(l.amount)} from ${l.customer}?\n\nThe request is cleared off the machine. If the customer already paid, the receipt is still posted.`
    : `Stop waiting for ₹${fmt(l.amount)} from ${l.customer}?\n\nPaytm cannot cancel ${what}. If the customer still pays, the receipt is still posted.`
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

function qrFile(l) {
  const bytes = Uint8Array.from(atob(qrImages[l.order_id]), (c) => c.charCodeAt(0))
  return new File([bytes], `paytm-qr-${l.order_id}.png`, { type: 'image/png' })
}

function qrMessage(l) {
  return `Dear ${l.customer}, please scan this QR to pay ₹${fmt(l.amount)} to Sundaram and Sons. Valid for ${Math.ceil(qrSecondsLeft(l) / 60)} minutes.`
}

// Phone / tablet (https only): hands the QR image to WhatsApp or any other app
async function shareQr(l) {
  const file = qrFile(l)
  const text = qrMessage(l)
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

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // clipboard API needs https (store terminals use http on the LAN); copy via a temporary textarea
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    if (!ok) return
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
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
  if (!l || l.status !== 'Pending' || document.hidden) return
  if (!isMachine(l) && (l.channel !== 'QR' || !qrStillLive(l))) return
  checkStatus(l, { quiet: true })
}

function onPaytmSocket(r) {
  if (r?.customer) applyResult(r)
}

function onKeydown(e) {
  if (showCustomerSearch.value) return
  if (e.key === 'Escape') { e.preventDefault(); router.push('/') }
  else if (e.key === 'F2') { e.preventDefault(); openCustomerSearch() }
  else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); createEntry() }
  else if (e.key === 'F8') { e.preventDefault(); createRequest() }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  getFrappeSocket()?.on('paytm_payment_update', onPaytmSocket)
  try {
    const s = await frappeGet(`${API}.get_devices`, { user: machineUser() })
    paytmEnabled.value = s.enabled
    qrEnabled.value = s.qr_enabled
    machines.value = s.devices || []
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

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style>
