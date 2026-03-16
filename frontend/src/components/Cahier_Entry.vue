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

        <!-- Row 1: Date (read-only) + Opening/Closing (read-only) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Date</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-300 font-mono">
              {{ form.date }}
            </div>
          </div>
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-500">Opening or Closing</label>
            <div class="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-300 font-mono">
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
              <div v-for="d in denominations" :key="d" class="flex items-center gap-2">
                <label class="w-12 shrink-0 text-right text-sm font-semibold text-slate-300">{{ d }}</label>
                <span class="text-slate-500 text-xs">×</span>
                <input
                  v-model.number="form.denominations[d]"
                  type="number"
                  min="0"
                  placeholder="0"
                  class="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500"
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
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { session } from '../session'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  title: {
    type: String,
    default: 'Cashier Opening',
  },
})

const emit = defineEmits(['close', 'saved'])

const denominations = [500, 200, 100, 50, 20, 10, 5, 2, 1]

const form = reactive({
  date: new Date().toLocaleDateString('en-CA'), // YYYY-MM-DD
  opening_or_closing: 'Opening',
  cash: '',
  user: '',
  denominations: Object.fromEntries(denominations.map(d => [d, null])),
})

const loadingSettings = ref(true)
const loadingBalance = ref(false)
const ledgerBalance = ref(0)
const saving = ref(false)
const saveError = ref('')
const savedName = ref('')
const cachedMopMap = ref({})

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

  // 1. Immediate population from localStorage (General Settings cache)
  const cachedCash = localStorage.getItem('wb-cash')
  if (cachedCash) {
    form.cash = cachedCash
  }

  try {
    const data = await frappeGet('ssplbilling.api.dashboard_api.get_billing_settings')
    const mopMap = data.mop_map || {}
    cachedMopMap.value = mopMap

    const userCash = data.user_defaults?.cash || ''
    
    // Only update if we got a value from API, or if form.cash is still empty
    if (userCash) {
      // Resolve MOP name to account name
      const resolvedCash = mopMap[userCash] || userCash
      form.cash = resolvedCash
      localStorage.setItem('wb-cash', resolvedCash)
    } else if (!form.cash && data.billing_series?.length > 0) {
      // Fallback to first series cash account if user default is missing
      const seriesCash = data.billing_series[0].cash_account
      if (seriesCash) {
        form.cash = seriesCash
        localStorage.setItem('wb-cash', seriesCash)
      }
    }
    
    // After getting settings, try to fetch existing record
    await fetchExistingRecord()
  } catch (e) {
    console.warn('[CahierEntry] Initialization failed:', e)
  } finally {
    loadingSettings.value = false
    // If after all attempts we still don't have a balance but have an account, fetch it
    if (!ledgerBalance.value && form.cash && !savedName.value) {
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
      // Only overwrite cash account if the saved record actually has one
      if (existing.cash) {
        // Resolve MOP name if it was stored as an old unresolved value
        form.cash = cachedMopMap.value[existing.cash] || existing.cash
      }
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
      
      // FALLBACK: Ensure form.cash is populated from resolved defaults if missing
      if (!form.cash) {
        const cached = localStorage.getItem('wb-cash')
        if (cached) form.cash = cached
      }

      // If we have a cash account, ensure we have its current balance
      if (form.cash) {
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
  await fetchExistingRecord()
})

// ── Fetch ledger balance whenever cash account is set ────────────────────────
watch(() => form.cash, async (account) => {
  if (!account || savedName.value) return // Don't overwrite if we already have a saved record
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
