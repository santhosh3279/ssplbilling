<template>
  <!-- Keys the panel owns stop here: the SalesInvoice shortcuts listen on window,
       and its Escape would otherwise leave the page from inside the cash box -->
  <aside
    class="flex w-[360px] shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto"
    @keydown="handleKeydown"
  >
    <div class="p-4 space-y-3">
      <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] flex items-center gap-2">
        <div class="h-1.5 w-1.5 rounded-full bg-[var(--color-highlight)]"></div>
        Payment
        <span class="ml-auto font-mono normal-case tracking-normal text-[11px]">F9</span>
      </h3>

      <!-- Last settled bill stays visible until the next one comes in -->
      <div
        v-if="lastSettled && !invoice"
        class="rounded-xl border border-[var(--color-success)] bg-[var(--color-success)]/15 p-4 text-center"
      >
        <div class="text-[11px] font-black uppercase tracking-widest text-[var(--color-success)]">Settled</div>
        <div class="font-mono text-sm font-bold text-[var(--color-text)] mt-1">{{ lastSettled.name }}</div>
        <div v-if="lastSettled.change > 0" class="mt-2">
          <div class="text-[11px] font-black uppercase tracking-widest text-[var(--color-danger)]">Change Return</div>
          <div class="font-mono text-[36px] font-black text-[var(--color-danger)]">₹{{ fmt(lastSettled.change) }}</div>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent"></div>
      </div>

      <div v-else-if="!invoice" class="flex h-48 items-center justify-center text-center">
        <p class="px-6 text-xs font-bold leading-relaxed text-[var(--color-text-muted)]">
          Save the bill (F8) or pick a draft from the bill list to take payment
        </p>
      </div>

      <template v-else>
        <!-- Summary -->
        <div class="relative rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
          <div class="flex items-start justify-between">
            <div class="min-w-0">
              <div class="truncate font-mono text-xs font-bold text-[var(--color-text-muted)]">{{ invoice.name }}</div>
              <div class="truncate text-sm font-bold text-[var(--color-text)]">{{ invoice.customer_name || invoice.customer }}</div>
            </div>
            <span
              class="shrink-0 rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest"
              :class="isCredit
                ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)]'
                : 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)]'"
            >{{ isCredit ? 'Credit' : 'Cash' }}</span>
          </div>
          <div class="mt-2 text-[12px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Bill Amount</div>
          <div class="font-mono text-[34px] font-black tracking-tight text-[var(--color-text)]">₹{{ fmt(amountToCollect) }}</div>
          <div class="mt-2 space-y-1 border-t border-[var(--color-border)] pt-2">
            <div class="flex items-center justify-between">
              <span class="text-[15px] font-bold text-[var(--color-text-muted)]">Paid</span>
              <span class="font-mono text-[15px] font-bold text-[var(--color-text)]">₹{{ fmt(totalPaid) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[15px] font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                {{ balance <= 0.01 ? 'Change' : 'Balance' }}
              </span>
              <span class="font-mono text-[26px] font-black" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">
                ₹{{ fmt(Math.abs(balance)) }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="alreadySettled" class="rounded-xl border border-[var(--color-success)] bg-[var(--color-success)]/15 p-3 text-center text-xs font-black uppercase tracking-widest text-[var(--color-success)]">
          {{ invoice.docstatus === 2 ? 'Cancelled bill' : 'Already settled' }}
        </div>

        <template v-else>
          <!-- Mode -->
          <div class="flex gap-2">
            <button
              type="button"
              @click="toggleCredit(false)"
              :disabled="isSecondaryParty || invoice.is_return"
              class="flex-1 rounded-xl border py-1.5 text-[15px] font-black uppercase tracking-widest transition-all disabled:cursor-not-allowed disabled:opacity-30"
              :class="!isCredit ? 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)]'"
              :title="isSecondaryParty ? 'Secondary parties can only process Credit Sales' : (invoice.is_return ? 'Sales returns can only be processed as Credit' : '')"
            >Cash Bill</button>
            <button
              type="button"
              @click="toggleCredit(true)"
              class="flex-1 rounded-xl border py-1.5 text-[15px] font-black uppercase tracking-widest transition-all"
              :class="isCredit ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)]'"
            >Credit</button>
          </div>

          <template v-if="!isCredit">
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ cashLabel }}</div>
              <input
                ref="cashInput"
                type="number"
                step="0.01"
                v-model="payments.cash"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20"
              />
            </div>
            <!-- Tendered notes: cash above the bill shows as change and is capped to the bill on posting -->
            <div class="grid grid-cols-4 gap-1.5">
              <button
                v-for="q in quickCash"
                :key="q.label"
                type="button"
                tabindex="-1"
                @click="payments.cash = q.value; cashInput?.focus()"
                class="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] py-1 font-mono text-[13px] font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]"
              >{{ q.label }}</button>
            </div>
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ upiLabel }}</div>
              <input
                ref="upiInput"
                type="number"
                step="0.01"
                v-model="payments.upi"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-success)] focus:ring-4 focus:ring-[var(--color-success)]/20"
              />
            </div>
            <input
              v-if="Number(payments.upi) > 0"
              v-model.trim="upiRefNo"
              type="text"
              tabindex="-1"
              placeholder="UPI Ref No (optional)"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-1.5 text-right font-mono text-[14px] font-bold text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-success)]"
            />
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ cardLabel }}</div>
              <input
                ref="cardInput"
                type="number"
                step="0.01"
                v-model="payments.card"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-info)] focus:ring-4 focus:ring-[var(--color-info)]/20"
              />
            </div>
            <!-- Required for a card payment: saved as the Card Payment Entry's Reference No -->
            <input
              v-if="Number(payments.card) > 0"
              ref="cardRefInput"
              v-model.trim="cardRefNo"
              type="text"
              placeholder="Card Ref No (required)"
              class="w-full rounded-xl border bg-[var(--color-bg)] px-4 py-1.5 text-right font-mono text-[14px] font-bold text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-info)]"
              :class="cardRefNo ? 'border-[var(--color-border)]' : 'border-[var(--color-danger)]'"
            />
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">Credit</div>
              <input
                ref="creditInput"
                type="number"
                step="0.01"
                v-model="payments.credit"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-danger)] focus:ring-4 focus:ring-[var(--color-danger)]/20"
              />
            </div>
            <div class="relative">
              <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">{{ discountLabel }}</div>
              <input
                ref="discountInput"
                type="number"
                step="0.01"
                v-model="payments.discount"
                @focus="$event.target.select()"
                class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-24 pr-4 text-right font-mono text-[22px] font-black text-[var(--color-text)] focus:border-[var(--color-warning)] focus:ring-4 focus:ring-amber-500/20"
              />
            </div>
          </template>

          <div v-else class="rounded-xl border border-[var(--color-danger)]/60 bg-[var(--color-danger)]/20 p-3">
            <label class="mb-1.5 block text-[13px] font-black uppercase tracking-widest text-[var(--color-danger)]">Promise Date (Due Date)</label>
            <div class="relative">
              <input
                ref="dueDateInput"
                type="text"
                v-model="dueDate"
                @input="handleDueDateInput"
                @keydown.backspace="handleDueDateKeyDown"
                placeholder="DDMM or DD/MM/YYYY"
                class="w-full rounded-2xl border border-[var(--color-danger)]/50 bg-[var(--color-bg)] py-3 pl-4 pr-12 text-center font-mono text-[20px] font-black text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-danger)]"
              />
              <div class="absolute right-2 top-1/2 -translate-y-1/2">
                <DatePickerButton :model-value="dueDate ? getIsoDueDate() : ''" label="Choose promise date" @update:model-value="dueDate = $event ? $event.split('-').reverse().join('/') : ''" />
              </div>
            </div>
          </div>

          <div class="relative">
            <div class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[16px] font-black uppercase text-[var(--color-text-muted)]">Remarks</div>
            <input
              ref="remarksInput"
              type="text"
              v-model="payments.remarks"
              @focus="$event.target.select()"
              class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2.5 pl-28 pr-4 text-right font-mono text-[18px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20"
            />
          </div>

          <p v-if="errorMsg" class="text-[12px] font-bold text-[var(--color-danger)]">{{ errorMsg }}</p>

          <button
            ref="postButton"
            type="button"
            @click="processPayment"
            :disabled="!canSubmit"
            class="w-full rounded-xl py-4 text-sm font-black uppercase tracking-[0.2em] transition-all active:scale-95 focus:outline-none disabled:pointer-events-none disabled:opacity-30"
            :class="isCredit
              ? 'bg-[var(--color-danger)] border-2 border-[var(--color-danger)] text-[var(--color-text-on-highlight)] hover:brightness-110'
              : 'border-2 border-[var(--color-success)] text-[var(--color-success)] hover:bg-[var(--color-success)]/10 focus:bg-[var(--color-success)] focus:text-[var(--color-text-on-highlight)]'"
          >
            <span v-if="isSubmitting">Processing...</span>
            <span v-else>{{ isCredit ? 'Post Credit Sale' : 'Post Settlement' }} (F9)</span>
          </button>
        </template>
      </template>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import DatePickerButton from './DatePickerButton.vue'
import { getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings } from '../api.js'
import { useLedgerCache } from '../services/ledgerCache'
import { canModifyDate } from '../composables/usePermission'
import { serverToday, serverCalendarDate } from '../services/serverTime'

const props = defineProps({
  // bill in view on the POS screen; null when a new bill is being entered
  invoiceName: { type: String, default: null },
  // bumped when the same bill is saved again, so its new totals are fetched
  reloadKey: { type: Number, default: 0 },
})

const emit = defineEmits(['settled', 'back', 'loaded'])

const invoice = ref(null)
const loading = ref(false)
const isSubmitting = ref(false)
const errorMsg = ref('')
const isCredit = ref(false)
const dueDate = ref('')
const upiRefNo = ref('')
const cardRefNo = ref('')
const lastSettled = ref(null)
const payments = ref({ cash: 0, upi: 0, card: 0, credit: 0, discount: 0, remarks: '' })
const seriesAccounts = ref({ cash: '', upi: '', card: '', discount: '' })

const cashInput = ref(null)
const upiInput = ref(null)
const cardInput = ref(null)
const cardRefInput = ref(null)
const creditInput = ref(null)
const discountInput = ref(null)
const remarksInput = ref(null)
const dueDateInput = ref(null)
const postButton = ref(null)

const { partyLinks } = useLedgerCache()

function getTodayIST() {
  return serverToday()
}

function fmt(val) {
  return (Number(val) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function glLabel(key, fallback) {
  const acc = localStorage.getItem(key) || ''
  return acc ? acc.split(' - ')[0].trim() : fallback
}
const cashLabel = computed(() => glLabel('wb-cash', 'Cash'))
const upiLabel = computed(() => glLabel('wb-upi', 'UPI'))
const cardLabel = computed(() => glLabel('wb-card', 'Card'))
const discountLabel = computed(() => {
  const acc = seriesAccounts.value.discount || localStorage.getItem('wb-discount-account') || ''
  return acc ? acc.split(' - ')[0].trim() : 'Disc'
})

const isSecondaryParty = computed(() => {
  if (!invoice.value?.customer) return false
  return partyLinks.value[invoice.value.customer]?.is_secondary || false
})

const amountToCollect = computed(() => {
  if (!invoice.value) return 0
  const gt = Number(invoice.value.rounded_total || invoice.value.grand_total || 0)
  const os = invoice.value.outstanding_amount !== undefined && invoice.value.outstanding_amount !== null
    ? Number(invoice.value.outstanding_amount)
    : gt
  if (invoice.value.docstatus === 1) return os
  return os < gt ? os : gt
})

const totalPaid = computed(() => {
  const p = payments.value
  const sum = (Number(p.cash) || 0) + (Number(p.upi) || 0) + (Number(p.card) || 0) + (Number(p.credit) || 0) + (Number(p.discount) || 0)
  return parseFloat(sum.toFixed(2))
})

const balance = computed(() => parseFloat((amountToCollect.value - totalPaid.value).toFixed(2)))

const changeAmount = computed(() => {
  const p = payments.value
  const money = (Number(p.cash) || 0) + (Number(p.upi) || 0) + (Number(p.card) || 0)
  const net = amountToCollect.value - (Number(p.discount) || 0) - (Number(p.credit) || 0)
  const change = money - net
  return change > 0.005 ? parseFloat(change.toFixed(2)) : 0
})

const alreadySettled = computed(() => {
  if (!invoice.value) return false
  if (invoice.value.docstatus === 2) return true
  return invoice.value.docstatus === 1 && (invoice.value.outstanding_amount || 0) <= 0.01
})

const canSubmit = computed(() => {
  if (!invoice.value || isSubmitting.value || alreadySettled.value) return false
  if (invoice.value.is_return && !isCredit.value) return false
  if (isCredit.value) return true
  return balance.value <= 0.01
})

// Exact amount plus the next notes up from it
const quickCash = computed(() => {
  const due = Math.ceil(amountToCollect.value)
  const out = [{ label: 'Exact', value: amountToCollect.value }]
  for (const step of [100, 500, 2000]) {
    const v = Math.ceil(due / step) * step
    if (v > due && !out.some(o => o.value === v)) out.push({ label: String(v), value: v })
  }
  return out.slice(0, 4)
})

// Billing settings depend on the user, not the bill: fetch once
let billingSettingsPromise = null
function getBillingSettingsCached() {
  if (!billingSettingsPromise) {
    const targetUser = localStorage.getItem('wb-inherited-user') || null
    billingSettingsPromise = fetchDashboardSettings(targetUser).catch(e => {
      billingSettingsPromise = null
      throw e
    })
  }
  return billingSettingsPromise
}

async function loadSeriesSettings(series) {
  try {
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi = localStorage.getItem('wb-upi')
    const lsCard = localStorage.getItem('wb-card')
    const settings = await getBillingSettingsCached()
    // Server resolves discount_account against wb-company
    const discountAccount = settings.discount_account || ''
    const seriesConfig = (settings.billing_series || []).find(s => s.series === series)
    const defaults = (lsCash || lsUpi || lsCard)
      ? { cash: lsCash, upi: lsUpi, card: lsCard }
      : (settings.user_defaults || {})
    seriesAccounts.value = {
      cash: defaults.cash || seriesConfig?.cash_account || 'Cash',
      upi: defaults.upi || seriesConfig?.upi || 'UPI',
      card: defaults.card || seriesConfig?.card || 'Card',
      discount: discountAccount,
    }
  } catch (e) {
    console.warn('Could not load accounts', e)
  }
}

let loadSeq = 0
async function loadInvoice(name) {
  const seq = ++loadSeq
  errorMsg.value = ''
  isCredit.value = false
  dueDate.value = ''
  upiRefNo.value = ''
  cardRefNo.value = ''
  payments.value = { cash: 0, upi: 0, card: 0, credit: 0, discount: 0, remarks: '' }
  if (!name) {
    invoice.value = null
    return
  }
  loading.value = true
  try {
    const details = await getInvoiceDetails(name)
    if (seq !== loadSeq) return
    invoice.value = details
    lastSettled.value = null
    await loadSeriesSettings(details.naming_series)
    if (seq !== loadSeq) return
    // submit writes the box back to custom_remarks, so start from the saved remark
    payments.value.remarks = details.custom_remarks || ''
    if (details.is_return || isSecondaryParty.value || details.mop === 'Credit') {
      isCredit.value = true
    } else if (!alreadySettled.value) {
      // the common case is a full cash payment: Enter on the cash box goes straight to post
      payments.value.cash = amountToCollect.value
    }
    loading.value = false
    emit('loaded', name)
  } catch (e) {
    if (seq === loadSeq) {
      invoice.value = null
      errorMsg.value = 'Failed to load bill: ' + e.message
    }
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

watch(() => [props.invoiceName, props.reloadKey], () => loadInvoice(props.invoiceName), { immediate: true })

function toggleCredit(val) {
  if (!val && isSecondaryParty.value) {
    errorMsg.value = 'Secondary parties can only process Credit Sales.'
    return
  }
  if (!val && invoice.value?.is_return) {
    errorMsg.value = 'Sales returns can only be processed as Credit.'
    return
  }
  isCredit.value = val
  errorMsg.value = ''
  const keptRemarks = payments.value.remarks || ''
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: keptRemarks }
  nextTick(() => (isCredit.value ? dueDateInput.value : cashInput.value)?.focus())
}

function handleDueDateKeyDown(e) {
  if (e.key === 'Backspace' && dueDate.value) {
    dueDate.value = ''
    e.preventDefault()
  }
}

function handleDueDateInput(e) {
  let raw = e.target.value.replace(/\D/g, '')
  if (raw.length > 8) raw = raw.slice(0, 8)
  // Quick entry for ddmm (4 digits)
  if (raw.length === 4) {
    dueDate.value = `${raw.slice(0, 2)}/${raw.slice(2, 4)}/${serverCalendarDate().getFullYear()}`
    return
  }
  let formatted = raw
  if (raw.length >= 5) formatted = raw.slice(0, 2) + '/' + raw.slice(2, 4) + '/' + raw.slice(4)
  else if (raw.length >= 3) formatted = raw.slice(0, 2) + '/' + raw.slice(2)
  dueDate.value = formatted
}

function getIsoDueDate() {
  if (!dueDate.value || !dueDate.value.includes('/')) {
    if (dueDate.value.match(/^\d{4}-\d{2}-\d{2}$/)) return dueDate.value
    return getTodayIST()
  }
  const parts = dueDate.value.split('/')
  if (parts.length !== 3) return getTodayIST()
  const [dd, mm, yyyy] = parts
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`
}

async function processPayment() {
  if (!canSubmit.value) return
  errorMsg.value = ''

  if (Number(payments.value.card) > 0.01 && !cardRefNo.value) {
    errorMsg.value = 'Enter the card reference number.'
    nextTick(() => cardRefInput.value?.focus())
    return
  }

  const bill = amountToCollect.value
  const upi = Number(payments.value.upi) || 0
  const card = Number(payments.value.card) || 0
  const disc = Number(payments.value.discount) || 0
  const credit = Number(payments.value.credit) || 0
  let cash = Number(payments.value.cash) || 0
  // overpaid: the excess is change handed back, so cash is reduced to fit the bill
  if (cash + upi + card + disc + credit > bill + 0.005) {
    cash = Math.max(0, bill - upi - card - disc - credit)
  }

  let finalDueDate = getIsoDueDate()
  const today = getTodayIST()
  if (finalDueDate < today) finalDueDate = today

  const name = invoice.value.name
  const change = changeAmount.value
  isSubmitting.value = true
  try {
    await submitInvoiceWithPayment({
      invoice_name: name,
      cash_amount: cash,
      upi_amount: upi,
      card_amount: card,
      discount_amount: disc,
      credit_amount: credit,
      is_credit: isCredit.value,
      due_date: finalDueDate,
      // the bill's own date, which the biller could only move with date permission
      posting_date: canModifyDate() ? (invoice.value.posting_date || today) : today,
      card_ref_no: cardRefNo.value,
      upi_ref_no: upiRefNo.value,
      cash_account: seriesAccounts.value.cash,
      upi_account: seriesAccounts.value.upi,
      card_account: seriesAccounts.value.card,
      discount_account: seriesAccounts.value.discount,
      custom_remarks: payments.value.remarks,
      cost_center: localStorage.getItem('wb-cost-center') || null,
    })
    lastSettled.value = { name, change }
    invoice.value = null
    emit('settled', name)
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

function inputOrder() {
  const order = isCredit.value
    ? [dueDateInput, remarksInput]
    : [cashInput, upiInput, cardInput, cardRefInput, creditInput, discountInput, remarksInput]
  return order.map(r => r.value).filter(Boolean)
}

function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    e.stopPropagation()
    processPayment()
    return
  }
  if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    emit('back')
    return
  }
  if (e.key === 'Enter') {
    e.stopPropagation()
    const fields = inputOrder()
    const idx = fields.indexOf(e.target)
    if (idx === -1) return
    e.preventDefault()
    // a fully paid bill skips the remaining boxes
    if (idx === fields.length - 1 || (!isCredit.value && balance.value <= 0.01)) {
      if (canSubmit.value) postButton.value?.focus()
      else fields[idx + 1]?.focus()
    } else {
      fields[idx + 1].focus()
    }
    return
  }
  // single keys and Delete / PageUp belong to the panel, not to the bill's shortcuts
  if (e.key.length === 1 || e.key === 'Delete' || e.key === 'PageUp') e.stopPropagation()
}

function focus() {
  if (!invoice.value) return false
  nextTick(() => (isCredit.value ? dueDateInput.value : cashInput.value)?.focus())
  return true
}

defineExpose({ focus })
</script>
