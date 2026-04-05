<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
    @click.self="$emit('close')"
  >
    <div class="w-[540px] overflow-hidden rounded-2xl bg-slate-800 shadow-2xl border border-slate-600">

      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-700 px-6 py-4">
        <div>
          <div class="text-[10px] font-bold uppercase tracking-widest text-slate-500">{{ title }}</div>
          <div class="text-base font-bold text-white">BOX Cash Entry</div>
        </div>
        <button
          class="rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-slate-600"
          @click="$emit('close')"
        >
          ✕ Close
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-5 max-h-[80vh] overflow-y-auto">

        <!-- Row 1: Date (editable) + Opening/Closing (read-only) -->
        <div class="grid grid-cols-2 gap-4">
          <div class="relative">
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Date</label>
            <div class="flex items-center gap-2">
              <input
                type="text"
                v-model="displayDate"
                @blur="onDisplayDateBlur"
                @keydown.enter.prevent="onDisplayDateBlur"
                class="w-full rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-300 font-mono focus:border-blue-500 outline-none"
                placeholder="DD-MMM-YYYY"
              />
              <button
                type="button"
                @click="datePicker?.showPicker()"
                class="flex h-9 w-10 items-center justify-center rounded-lg border border-slate-600 bg-slate-700 text-slate-400 transition hover:bg-slate-600 hover:text-white"
                title="Open Calendar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              </button>
              <input
                ref="datePicker"
                type="date"
                v-model="form.date"
                class="pointer-events-none absolute h-0 w-0 opacity-0"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Opening or Closing</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2.5 text-sm text-slate-300 font-mono">
              {{ form.opening_or_closing }}
            </div>
          </div>
        </div>

        <!-- Row 2: Cash Account + User -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Cash Account</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm font-mono"
                 :class="form.cash ? 'text-slate-200' : 'text-slate-500 italic'">
              {{ form.cash || (loadingSettings ? 'Loading…' : 'Not configured') }}
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">User</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-300 font-mono">
              {{ form.user }}
            </div>
          </div>
        </div>

        <!-- Row 3: Cash Ledger Balance (read-only) + Difference (computed) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Cash Ledger Balance</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm font-mono"
                 :class="loadingBalance ? 'text-slate-500 italic' : (ledgerBalance >= 0 ? 'text-emerald-400' : 'text-red-400')">
              {{ loadingBalance ? 'Fetching…' : Math.abs(ledgerBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              <span v-if="!loadingBalance" class="text-[10px] ml-1">{{ ledgerBalance >= 0 ? 'DR' : 'CR' }}</span>
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Difference</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm font-mono"
                 :class="difference >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ difference.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
        </div>

        <!-- Denomination Section -->
        <div>
          <div class="mb-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-t border-slate-700 pt-4">
            BOX Cash Denomination
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2">
            <!-- Left column: denominations -->
            <div class="space-y-2">
              <div v-for="(d, i) in denominations" :key="d" class="flex items-center gap-2">
                <label class="w-12 shrink-0 text-right text-sm font-semibold text-slate-300">{{ d }}</label>
                <span class="text-slate-500 text-xs">×</span>
                <input
                  :ref="el => { if (el) denomInputRefs[i] = el }"
                  v-model.number="form.denominations[d]"
                  type="number"
                  min="0"
                  placeholder="0"
                  class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500"
                  @keydown.enter.prevent="onDenomEnter(i)"
                  @keydown.down.prevent="denomInputRefs[i + 1]?.focus()"
                  @keydown.up.prevent="denomInputRefs[i - 1]?.focus()"
                  @focus="$event.target.select()"
                />
                <span class="w-20 shrink-0 text-right text-xs text-slate-400 font-mono">
                  {{ ((form.denominations[d] || 0) * d).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </span>
              </div>
            </div>

            <!-- Right column: total -->
            <div class="flex flex-col items-center justify-center rounded-xl bg-slate-700/50 border border-slate-600 p-4 gap-1">
              <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">BOX Total</div>
              <div class="text-3xl font-black text-emerald-400 font-mono">
                {{ total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="saveError" class="rounded-lg bg-red-900/40 border border-red-700 px-4 py-2 text-sm text-red-300">
          {{ saveError }}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between border-t border-slate-700 px-6 py-4">
        <div v-if="savedName" class="text-xs text-emerald-400 font-mono">Saved: {{ savedName }}</div>
        <div v-else class="text-xs text-slate-600">Fill denominations and save</div>
        <div class="flex gap-3">
          <button
            class="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
            @click="$emit('close')"
          >
            Cancel
          </button>
          <button
            class="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 active:scale-95 transition disabled:opacity-50"
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
import { reactive, ref, computed, onMounted, watch, onBeforeUpdate } from 'vue'
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

const datePicker = ref(null)
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
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { account })
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
  // For Opening, use the pre-today opening balance passed from parent — don't fetch live
  if (form.opening_or_closing === 'Opening' && props.initialLedgerBalance !== null) {
    ledgerBalance.value = props.initialLedgerBalance
    return
  }
  loadingBalance.value = true
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { account })
    ledgerBalance.value = res.balance ?? 0
  } catch (e) {
    console.warn('[CahierEntry] get_cash_ledger_balance failed:', e)
  } finally {
    loadingBalance.value = false
  }
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
  } catch (e) {
    saveError.value = e.message || 'Save failed'
  } finally {
    saving.value = false
  }
}
</script>
