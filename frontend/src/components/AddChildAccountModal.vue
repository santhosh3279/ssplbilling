<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/70 backdrop-blur-sm"
    @keydown.esc="$emit('close')"
  >
    <div class="w-[420px] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-2xl">
      <h3 class="mb-1 text-lg font-bold text-[var(--color-text)]">New Account</h3>
      <p class="mb-4 text-xs text-[var(--color-text-muted)]">Under <span class="font-semibold text-[var(--color-text)]">{{ parentAccount }}</span></p>

      <div class="space-y-3">
        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Account Name *</label>
          <input
            ref="nameInput"
            v-model="form.account_name"
            type="text"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
            @keydown.enter="submit"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Account Number</label>
            <input
              v-model="form.account_number"
              type="text"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
            />
          </div>
          <div class="flex items-end pb-2.5">
            <label class="flex items-center gap-2 text-sm text-[var(--color-text)]">
              <input v-model="form.is_group" type="checkbox" class="h-4 w-4 rounded border-[var(--color-border)]" />
              Is Group
            </label>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Account Type</label>
          <select
            v-model="form.account_type"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          >
            <option value="">—</option>
            <option v-for="opt in ACCOUNT_TYPES" :key="opt" :value="opt">{{ opt }}</option>
          </select>
        </div>

        <div v-if="!form.is_group">
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Currency</label>
          <input
            v-model="form.account_currency"
            type="text"
            placeholder="Defaults to company currency"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          />
        </div>

        <div v-if="!form.is_group && form.account_type === 'Tax'">
          <label class="mb-1 block text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Tax Rate</label>
          <input
            v-model.number="form.tax_rate"
            type="number"
            step="0.01"
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] focus:border-[var(--color-info)] focus:outline-none"
          />
        </div>

        <p v-if="error" class="rounded border border-[var(--color-danger)]/50 bg-[var(--color-danger)]/10 px-3 py-2 text-xs text-[var(--color-danger)]">{{ error }}</p>
      </div>

      <div class="mt-5 flex gap-3">
        <button
          class="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] py-2 text-sm font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-colors"
          @click="$emit('close')"
        >
          Cancel
        </button>
        <button
          :disabled="!form.account_name.trim() || submitting"
          class="flex-1 rounded-lg bg-[var(--color-info)] py-2 text-sm font-bold text-[var(--color-text-on-highlight)] transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
          @click="submit"
        >
          {{ submitting ? 'Creating…' : 'Create' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { frappePost } from '../api.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  parentAccount: { type: String, required: true },
  company: { type: String, default: '' },
})

const emit = defineEmits(['close', 'created'])

const ACCOUNT_TYPES = [
  'Accumulated Depreciation', 'Asset Received But Not Billed', 'Bank', 'Cash', 'Chargeable',
  'Capital Work in Progress', 'Cost of Goods Sold', 'Current Asset', 'Current Liability',
  'Depreciation', 'Direct Expense', 'Direct Income', 'Equity', 'Expense Account',
  'Expenses Included In Asset Valuation', 'Expenses Included In Valuation', 'Fixed Asset',
  'Income Account', 'Indirect Expense', 'Indirect Income', 'Liability', 'Payable', 'Receivable',
  'Round Off', 'Round Off for Opening', 'Stock', 'Stock Adjustment', 'Stock Received But Not Billed',
  'Service Received But Not Billed', 'Tax', 'Temporary',
]

const nameInput = ref(null)
const submitting = ref(false)
const error = ref('')

function emptyForm() {
  return {
    account_name: '',
    account_number: '',
    is_group: false,
    account_type: '',
    account_currency: '',
    tax_rate: null,
  }
}

const form = reactive(emptyForm())

watch(() => props.show, (val) => {
  if (val) {
    Object.assign(form, emptyForm())
    error.value = ''
    nextTick(() => nameInput.value?.focus())
  }
})

async function submit() {
  if (!form.account_name.trim() || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const doc = {
      doctype: 'Account',
      account_name: form.account_name.trim(),
      parent_account: props.parentAccount,
      is_group: form.is_group ? 1 : 0,
    }
    if (props.company) doc.company = props.company
    if (form.account_number.trim()) doc.account_number = form.account_number.trim()
    if (form.account_type) doc.account_type = form.account_type
    if (!form.is_group && form.account_currency.trim()) doc.account_currency = form.account_currency.trim()
    if (!form.is_group && form.account_type === 'Tax' && form.tax_rate) doc.tax_rate = form.tax_rate

    const created = await frappePost('frappe.client.insert', { doc })
    emit('created', created.name)
  } catch (e) {
    error.value = e.message || 'Failed to create account.'
  } finally {
    submitting.value = false
  }
}
</script>
