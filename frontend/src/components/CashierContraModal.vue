<template>
  <div class="fixed inset-0 z-[60] flex flex-col bg-[var(--color-bg)] text-[var(--color-text)]">

    <!-- HEADER -->
    <div class="flex h-16 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8">
      <div class="flex items-center gap-4">
        <button
          @click="$emit('close')"
          class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xs font-bold text-[var(--color-text)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] active:scale-95"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back to Cahier
        </button>
        <div class="h-5 w-px bg-[var(--color-surface-raised)]"></div>
        <div>
          <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Contra Entry</div>
          <div class="text-base font-black text-[var(--color-text)]">{{ entryType }} Cash Adjustment</div>
        </div>
        <span
          class="rounded-full px-3 py-1 text-xs font-black uppercase tracking-widest"
          :class="diff > 0 ? 'bg-[var(--color-success)]/20 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'"
        >
          {{ diff > 0 ? 'Excess' : 'Short' }} ₹{{ Math.abs(diff).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
        </span>
      </div>
      <div class="flex items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 px-4 py-2">
        <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Date</span>
        <span class="font-mono text-sm font-bold text-[var(--color-text)]">{{ postingDate }}</span>
      </div>
    </div>

    <!-- BODY -->
    <div class="flex-1 overflow-y-auto p-8">
      <div v-if="loading" class="flex h-40 items-center justify-center text-[var(--color-text-muted)] text-sm">
        Resolving accounts…
      </div>
      <template v-else>
        <div class="mx-auto max-w-4xl rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 overflow-hidden">
          <table class="w-full">
            <thead class="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
              <tr class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] text-left">
                <th class="px-6 py-3 w-8">#</th>
                <th class="px-4 py-3">Ledger</th>
                <th class="px-4 py-3 text-right w-48">Current Balance</th>
                <th class="px-4 py-3 text-right w-48">Debit (₹)</th>
                <th class="px-4 py-3 text-right w-48">Credit (₹)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr v-for="(row, idx) in rows" :key="idx" class="hover:bg-[var(--color-surface-raised)]/20 transition-colors">
                <td class="px-6 py-4 text-sm font-bold text-[var(--color-text-muted)]">{{ idx + 1 }}</td>
                <td class="px-4 py-4">
                  <div class="text-base font-bold text-[var(--color-text)]">{{ row.account_name }}</div>
                  <div class="text-[10px] text-[var(--color-text-muted)] font-mono mt-0.5">{{ row.account }}</div>
                </td>
                <td class="px-4 py-4 text-right font-mono text-sm font-semibold"
                    :class="row.current_balance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(row.current_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-[10px] ml-1">{{ row.current_balance >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-4 py-4 text-right font-mono text-lg font-black"
                    :class="row.debit > 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">
                  {{ row.debit > 0 ? row.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '—' }}
                </td>
                <td class="px-4 py-4 text-right font-mono text-lg font-black"
                    :class="row.credit > 0 ? 'text-[var(--color-warning)]' : 'text-[var(--color-text-muted)]'">
                  {{ row.credit > 0 ? row.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Remarks -->
        <div class="mx-auto max-w-4xl mt-6">
          <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Remarks</label>
          <textarea
            v-model="remarks"
            rows="2"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/20 transition-all resize-none"
          ></textarea>
        </div>

        <!-- Error -->
        <div v-if="saveError" class="mx-auto max-w-4xl mt-4 rounded-xl bg-[var(--color-danger)]/40 border border-[var(--color-danger)] px-4 py-3 text-sm text-[var(--color-danger)]">
          {{ saveError }}
        </div>
      </template>
    </div>

    <!-- FOOTER -->
    <div class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4">
      <div class="mx-auto max-w-4xl flex items-center justify-between">
        <div class="flex gap-12 text-sm">
          <div>
            <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Debit</div>
            <div class="font-mono text-xl font-black text-[var(--color-text)]">
              ₹ {{ totalDebit.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
          <div>
            <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Credit</div>
            <div class="font-mono text-xl font-black text-[var(--color-text)]">
              ₹ {{ totalCredit.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
          <div>
            <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Difference</div>
            <div class="font-mono text-xl font-black" :class="Math.abs(totalDebit - totalCredit) < 0.01 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              ₹ {{ Math.abs(totalDebit - totalCredit).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
        </div>
        <div class="flex gap-3">
          <button
            @click="$emit('close')"
            class="rounded-xl border border-[var(--color-border)] px-5 py-2.5 text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
          >
            Cancel
          </button>
          <button
            @click="handleSave"
            :disabled="saving || loading || Math.abs(totalDebit - totalCredit) >= 0.01"
            class="rounded-xl bg-[var(--color-success)] px-8 py-2.5 text-sm font-black text-[var(--color-text-on-highlight)] shadow-lg shadow-emerald-900/40 hover:bg-[var(--color-success)] active:scale-95 transition disabled:opacity-50 disabled:pointer-events-none"
          >
            <span v-if="saving">Saving…</span>
            <span v-else>💾 Save Contra Entry</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { frappeGet, frappePost } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'

useSubwindow()

const props = defineProps({
  cashAccount: { type: String, required: true },
  diff:        { type: Number, required: true },
  entryType:   { type: String, required: true },
})

const emit = defineEmits(['close', 'saved'])

const postingDate = new Date().toLocaleDateString('en-CA')
const loading  = ref(true)
const saving   = ref(false)
const saveError = ref('')
const remarks  = ref('')
const rows     = ref([])

const totalDebit  = computed(() => rows.value.reduce((s, r) => s + (r.debit  || 0), 0))
const totalCredit = computed(() => rows.value.reduce((s, r) => s + (r.credit || 0), 0))

async function resolveAccount(nameHint) {
  try {
    const res = await frappeGet('frappe.client.get_list', {
      doctype: 'Account',
      filters: JSON.stringify([
        ['account_name', 'like', `%${nameHint.split(' - ')[0]}%`],
        ['is_group', '=', 0],
      ]),
      fields: ['name', 'account_type'],
      limit_page_length: 1,
    })
    if (res?.[0]) return { name: res[0].name, type: res[0].account_type || '' }
  } catch (e) {
    console.warn('[CahierContra] resolveAccount failed for', nameHint, e)
  }
  return { name: nameHint, type: '' }
}

async function fetchBalance(accountName) {
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { account: accountName })
    return res?.balance ?? 0
  } catch (_) { return 0 }
}

onMounted(async () => {
  const amount = Math.abs(props.diff)
  const isExcess = props.diff > 0

  // diff > 0 (excess): DR Cash, CR Short Or Excess
  // diff < 0 (short):  DR Short Or Excess, CR Cash
  const [cashResolved, adjResolved] = await Promise.all([
    resolveAccount(props.cashAccount),
    resolveAccount('Short Or Excess'),
  ])
  const [cashBal, adjBal] = await Promise.all([
    fetchBalance(cashResolved.name),
    fetchBalance(adjResolved.name),
  ])

  rows.value = [
    {
      account:         cashResolved.name,
      account_name:    cashResolved.name,
      account_type:    cashResolved.type,
      current_balance: cashBal,
      debit:           isExcess ? amount : 0,
      credit:          isExcess ? 0 : amount,
    },
    {
      account:         adjResolved.name,
      account_name:    adjResolved.name,
      account_type:    adjResolved.type,
      current_balance: adjBal,
      debit:           isExcess ? 0 : amount,
      credit:          isExcess ? amount : 0,
    },
  ]

  remarks.value = `Cash ${isExcess ? 'Excess' : 'Short'} — ${props.entryType} adjustment (Diff: ₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })})`
  loading.value = false
})

async function handleSave() {
  saveError.value = ''
  saving.value = true
  try {
    const payload = {
      voucher_type: 'Contra',
      posting_date: postingDate,
      user_remark: remarks.value,
      accounts: rows.value.map(r => ({
        account:                       r.account,
        account_type:                  r.account_type,
        debit_in_account_currency:     r.debit,
        credit_in_account_currency:    r.credit,
        user_remark:                   remarks.value,
      })),
    }
    await frappePost('ssplbilling.api.journalcontra_api.create_journal_contra_entry', { data: payload })
    emit('saved')
  } catch (e) {
    saveError.value = e.message || 'Save failed'
  } finally {
    saving.value = false
  }
}
</script>
