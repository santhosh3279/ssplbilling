<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
    @click.self="$emit('close')"
  >
    <div class="w-[800px] overflow-hidden rounded-2xl bg-[var(--color-surface)] shadow-2xl border border-[var(--color-border)]">

      <!-- Header -->
      <div class="flex items-center justify-between border-b border-[var(--color-border)] px-3 py-2">
        <div>
          <div class="text-[20px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">{{ title }}</div>
          <div class="text-3xl font-bold text-[var(--color-text)]">BOX Cash Entry</div>
        </div>
        <button
          class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.75 text-xl text-[var(--color-text)] transition hover:brightness-110 active:scale-95"
          @click="$emit('close')"
        >
          ✕ Close
        </button>
      </div>

      <!-- Body -->
      <div class="p-3 space-y-2.5 max-h-[80vh] overflow-y-auto">

        <!-- Row 1: Date (editable) + Opening/Closing (read-only) -->
        <div class="grid grid-cols-2 gap-2">
          <div class="relative">
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Date</label>
            <div class="flex items-center gap-1">
              <input
                type="text"
                v-model="displayDate"
                @blur="onDisplayDateBlur"
                @keydown.enter.prevent="onDisplayDateBlur"
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1 text-sm text-[var(--color-text)] font-mono focus:border-[var(--color-info)] outline-none placeholder-[var(--color-text-muted)]/50"
                placeholder="DD-MMM-YYYY"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Opening or Closing</label>
            <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1.25 text-sm text-[var(--color-text)] font-mono opacity-80">
              {{ form.opening_or_closing }}
            </div>
          </div>
        </div>

        <!-- Row 2: Cash Account + User -->
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Cash Account</label>
            <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1 text-sm font-mono truncate"
                 :class="form.cash ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)] italic'">
              {{ form.cash || (loadingSettings ? 'Loading…' : 'Not configured') }}
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">User</label>
            <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1 text-sm text-[var(--color-text)] font-mono">
              {{ form.user }}
            </div>
          </div>
        </div>

        <!-- Row 3: Cash Ledger Balance (read-only) + Difference (computed) -->
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Cash Ledger Balance</label>
            <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1 text-sm font-mono"
                 :class="loadingBalance ? 'text-[var(--color-text-muted)] italic' : (ledgerBalance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
              {{ loadingBalance ? 'Fetching…' : Math.abs(ledgerBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              <span v-if="!loadingBalance" class="text-[10px] ml-1">{{ ledgerBalance >= 0 ? 'DR' : 'CR' }}</span>
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Difference</label>
            <div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-1.5 py-1 text-sm font-mono"
                 :class="difference >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              {{ difference.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
        </div>

        <!-- Denomination Section -->
        <div>
          <div class="mb-1.5 text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-t border-[var(--color-border)] pt-2">
            BOX Cash Denomination
          </div>
          <div class="grid grid-cols-2 gap-x-3 gap-y-1">
            <!-- Left column: denominations -->
            <div class="space-y-1">
              <div v-for="(d, i) in denominations" :key="d" class="flex items-center gap-1">
                <label class="w-24 shrink-0 text-right text-2xl font-semibold text-[var(--color-text)]">{{ d }}</label>
                <span class="text-[var(--color-text-muted)] text-xl">×</span>
                <input
                  :ref="el => { if (el) denomInputRefs[i] = el }"
                  v-model.number="form.denominations[d]"
                  type="number"
                  min="0"
                  placeholder="0"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-0.5 py-0.5 text-2xl text-[var(--color-text)] placeholder-[var(--color-text-muted)]/30 outline-none focus:border-[var(--color-info)]"
                  @keydown.enter.prevent="onDenomEnter(i)"
                  @keydown.down.prevent="denomInputRefs[i + 1]?.focus()"
                  @keydown.up.prevent="denomInputRefs[i - 1]?.focus()"
                  @focus="$event.target.select()"
                />
                <span class="w-40 shrink-0 text-right text-xl text-[var(--color-text-muted)] font-mono">
                  {{ ((form.denominations[d] || 0) * d).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </span>
              </div>
            </div>

            <!-- Right column: total -->
            <div class="flex flex-col items-center justify-center rounded-xl bg-[var(--color-surface-raised)]/30 border border-[var(--color-border)] p-2 gap-0.5">
              <div class="text-[20px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">BOX Total</div>
              <div class="text-6xl font-black text-[var(--color-success)] font-mono">
                {{ total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="saveError" class="rounded-lg bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30 px-2 py-1 text-xl text-[var(--color-danger)]">
          {{ saveError }}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between border-t border-[var(--color-border)] px-3 py-2 bg-[var(--color-surface-raised)]/10">
        <div v-if="savedName" class="text-xl text-[var(--color-success)] font-mono font-bold">Saved: {{ savedName }}</div>
        <div v-else class="text-xl text-[var(--color-text-muted)] font-medium">Fill denominations and save</div>
        <div class="flex gap-1.5">
          <button
            class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-lg font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition active:scale-95"
            @click="$emit('close')"
          >
            Cancel
          </button>
          <button
            class="rounded-lg bg-[var(--color-info)] px-2.5 py-1 text-lg font-bold text-[var(--color-text-on-highlight)] hover:brightness-110 active:scale-95 transition disabled:opacity-50 disabled:active:scale-100"
            :disabled="saving || !form.cash"
            @click="handleSave"
          >
            <span v-if="saving">Saving…</span>
            <span v-else>💾 Save</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch, onBeforeUpdate, nextTick } from 'vue'
import { session } from '../session'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  title: {
    type: String,
    default: 'Cashier Opening',
  },
  initialLedgerBalance: {
    type: Number,
    default: null,
  },
  date: {
    type: String,
    default: () => new Date().toLocaleDateString('en-CA'),
  },
})

const emit = defineEmits(['close', 'saved'])

const denominations = [500, 200, 100, 50, 20, 10, 5, 2, 1]
const denomInputRefs = ref([])
onBeforeUpdate(() => { denomInputRefs.value = [] })

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

function formatDate(dateStr) {
  if (!dateStr) return ""
  const [y, m, d] = dateStr.split("-")
  const month = monthNames[parseInt(m) - 1]
  return `${d}-${month}-${y}`
}

function parseDate(displayStr) {
  if (!displayStr) return null
  const parts = displayStr.split("-")
  if (parts.length !== 3) return null
  const d = parts[0].padStart(2, '0')
  const mIdx = monthNames.findIndex(m => m.toLowerCase() === parts[1].toLowerCase())
  if (mIdx === -1) return null
  const m = String(mIdx + 1).padStart(2, '0')
  const y = parts[2]
  if (y.length !== 4) return null
  return `${y}-${m}-${d}`
}

function onDenomEnter(index) {
  if (index < denominations.length - 1) {
    denomInputRefs.value[index + 1]?.focus()
  } else {
    handleSave()
  }
}

const form = reactive({
  date: props.date,
  opening_or_closing: 'Opening',
  cash: '',
  user: '',
  denominations: Object.fromEntries(denominations.map(d => [d, null])),
})

const displayDate = ref(formatDate(form.date))

watch(() => form.date, (newVal) => {
  displayDate.value = formatDate(newVal)
  fetchExistingRecord()
})

function onDisplayDateBlur() {
  const parsed = parseDate(displayDate.value)
  if (parsed && parsed !== form.date) {
    form.date = parsed
  } else {
    displayDate.value = formatDate(form.date)
  }
}

const loadingSettings = ref(false)
const loadingBalance = ref(false)
const ledgerBalance = ref(0)
const saving = ref(false)
const saveError = ref('')
const savedName = ref('')

const total = computed(() =>
  denominations.reduce((s, d) => s + (Number(form.denominations[d]) || 0) * d, 0),
)

const difference = computed(() => total.value - ledgerBalance.value)

// ── Load cash account and existing record ────────────────────────────────────
onMounted(async () => {
  form.user = session.user.value || ''

  // Set opening_or_closing based on title
  const t = props.title || ''
  if (t.includes('Mid-Day-1') || t.includes('Mid Day 1')) {
    form.opening_or_closing = 'Mid-Day-1'
  } else if (t.includes('Mid-Day-2') || t.includes('Mid Day 2')) {
    form.opening_or_closing = 'Mid-Day-2'
  } else if (t.includes('Closing')) {
    form.opening_or_closing = 'Closing'
  } else {
    form.opening_or_closing = 'Opening'
  }

  // Use wb-cash — resolved GL account saved by GeneralSettings sync.
  // If it lacks the company tag (no " - "), fetch the full account name from ERPNext.
  let cashAccount = localStorage.getItem('wb-cash') || ''
  if (cashAccount && !cashAccount.includes(' - ')) {
    try {
      const res = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify({ account_name: cashAccount, account_type: 'Cash', is_group: 0 }),
        fields: ['name'],
        limit_page_length: 1,
      })
      if (res?.[0]?.name) {
        cashAccount = res[0].name
        localStorage.setItem('wb-cash', cashAccount)
      }
    } catch (e) {
      console.warn('[CahierEntry] Could not resolve cash account with company tag:', e)
    }
  }
  form.cash = cashAccount

  await fetchExistingRecord()

  if (!ledgerBalance.value && !savedName.value) {
    if (form.opening_or_closing === 'Opening' && props.initialLedgerBalance !== null) {
      ledgerBalance.value = props.initialLedgerBalance
    } else if (form.cash) {
      await fetchLedgerBalanceManual(form.cash)
    }
  }

  nextTick(() => {
    denomInputRefs.value[0]?.focus()
  })
})

async function fetchExistingRecord() {
  try {
    const existing = await frappeGet('ssplbilling.api.cahierlog_api.get_cashier_opening', {
      date: form.date,
      user: form.user,
      opening_or_closing: form.opening_or_closing
    })
    
    if (existing) {
      savedName.value = existing.name
      // Always use wb-cash (resolved GL account) — never let the stored record override it
      form.cash = localStorage.getItem('wb-cash') || existing.cash || form.cash
      ledgerBalance.value = parseFloat(existing.cash_ledger_balance || 0)
      
      // Load denominations
      denominations.forEach(d => {
        form.denominations[d] = existing[d] ? parseInt(existing[d]) : null
      })
    } else {
      // No existing record: reset state
      savedName.value = ''
      denominations.forEach(d => {
        form.denominations[d] = null
      })

      if (form.opening_or_closing === 'Opening' && props.initialLedgerBalance !== null) {
        // Use the pre-computed opening balance (before today) passed from parent
        ledgerBalance.value = props.initialLedgerBalance
      } else if (form.cash) {
        await fetchLedgerBalanceManual(form.cash)
      }
    }
  } catch (e) {
    console.warn('[CahierEntry] fetchExistingRecord failed:', e)
  }
}

async function fetchLedgerBalanceManual(account) {
  if (!account) return
  loadingBalance.value = true
  try {
    const params = { account }
    if (form.opening_or_closing === 'Opening') {
      params.date = form.date
    } else if (form.opening_or_closing === 'Closing') {
      // For Closing, we want the balance as of the end of the day.
      // So we pass the next day's date to get its opening balance.
      const d = new Date(form.date + 'T00:00:00')
      d.setDate(d.getDate() + 1)
      params.date = d.toLocaleDateString('en-CA')
    }
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', params)
    ledgerBalance.value = res.balance ?? 0
  } catch (e) {
    console.warn('[CahierEntry] get_cash_ledger_balance failed:', e)
  } finally {
    loadingBalance.value = false
  }
}

// ── Watch for type changes ──────────────────────────────────────────────────
watch(() => form.opening_or_closing, async () => {
  if (loadingSettings.value) return 
  await fetchExistingRecord()
})

// ── Fetch ledger balance whenever cash account is set ────────────────────────
watch(() => form.cash, async (account) => {
  if (!account || savedName.value) return
  await fetchLedgerBalanceManual(account)
}, { immediate: false })

// ── Save ─────────────────────────────────────────────────────────────────────
async function handleSave() {
  saveError.value = ''
  saving.value = true
  try {
    const d = form.denominations
    const res = await frappePost('ssplbilling.api.cahierlog_api.save_cashier_opening', {
      date: form.date,
      cash: form.cash,
      cash_ledger_balance: ledgerBalance.value,
      opening_or_closing: form.opening_or_closing,
      user: form.user,
      difference: difference.value,
      d500: d[500] || 0,
      d200: d[200] || 0,
      d100: d[100] || 0,
      d50:  d[50]  || 0,
      d20:  d[20]  || 0,
      d10:  d[10]  || 0,
      d5:   d[5]   || 0,
      d2:   d[2]   || 0,
      d1:   d[1]   || 0,
      total: total.value,
    })
    
    // Pull the value from response (ensure sync with doctype)
    savedName.value = res.name
    form.cash = res.cash
    ledgerBalance.value = parseFloat(res.cash_ledger_balance || 0)
    denominations.forEach(d => {
      form.denominations[d] = res[d] ? parseInt(res[d]) : null
    })
    
    emit('saved', { total: total.value, name: res.name })
    emit('close')
  } catch (e) {
    saveError.value = e.message || 'Save failed'
  } finally {
    saving.value = false
  }
}
</script>