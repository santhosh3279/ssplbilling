<template>
  <div ref="rootRef" class="flex flex-col gap-4">
    <div v-if="loading" class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
      <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></span>
      Loading bank accounts…
    </div>

    <div v-else-if="!rows.length" class="rounded border border-dashed border-[var(--color-border)] p-6 text-center text-[var(--color-text-muted)]">
      No bank account yet.
    </div>

    <div
      v-for="(row, i) in rows"
      :key="row._key"
      class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
      :class="row.is_default ? 'bg-[var(--color-info)]/10' : ''"
    >
      <div class="mb-3 flex items-center justify-between">
        <label class="flex cursor-pointer items-center gap-2">
          <input
            type="radio"
            :name="radioName"
            :checked="!!row.is_default"
            class="h-5 w-5"
            @change="setDefault(i)"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
          <span class="text-base font-semibold uppercase tracking-wider text-[var(--color-text)]">
            {{ row.is_default ? 'Default Account' : 'Make Default' }}
          </span>
        </label>
        <button
          type="button"
          class="rounded px-3 py-1 text-sm font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10"
          @click="removeRow(i)"
        >
          Remove
        </button>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Account Holder Name</label>
          <input
            v-model="row.account_name"
            :class="inputClass"
            :style="inputStyle"
            :placeholder="partyName || 'Name on the account'"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Bank Name *</label>
          <input
            v-model="row.bank"
            :list="datalistId"
            :class="inputClass"
            :style="inputStyle"
            placeholder="e.g. State Bank of India"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Account Number *</label>
          <input
            v-model="row.bank_account_no"
            inputmode="numeric"
            maxlength="20"
            :class="[inputClass, 'font-mono']"
            :style="inputStyle"
            placeholder="Digits only"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">IFSC{{ meta.ifsc_required ? ' *' : '' }}</label>
          <input
            v-model="row.branch_code"
            maxlength="11"
            :class="[inputClass, 'font-mono uppercase']"
            :style="inputStyle"
            placeholder="SBIN0001234"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
        </div>
        <div v-if="meta.email_field" class="col-span-2 flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Email{{ meta.email_required && !partyEmail ? ' *' : '' }}</label>
          <input
            v-model="row.email"
            type="email"
            :class="inputClass"
            :style="inputStyle"
            :placeholder="partyEmail ? `Blank uses ${partyEmail}` : 'email@example.com'"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="next"
          />
        </div>
      </div>
    </div>

    <button
      v-if="!loading"
      type="button"
      class="self-start rounded border border-[var(--color-info)] px-4 py-2 font-bold text-[var(--color-info)] hover:bg-[var(--color-info)]/10"
      @click="addRow"
    >
      + Add Bank Account
    </button>

    <datalist :id="datalistId">
      <option v-for="b in banks" :key="b" :value="b" />
    </datalist>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { fetchBankFormMeta } from '../api/customer.js'

const rows = defineModel({ type: Array, default: () => [] })

const props = defineProps({
  partyName: { type: String, default: '' },
  partyEmail: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'submit'])

const uid = Math.random().toString(36).slice(2, 8)
const datalistId = `bank-list-${uid}`
const radioName = `bank-default-${uid}`

const inputClass = 'rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]'
const inputStyle = 'font-size: 1.5rem; padding: 0.2em;'

const rootRef = ref(null)
const banks = ref([])
// Site rules from the server; india_banking makes IFSC and email mandatory
const meta = ref({ strict_names: false, ifsc_required: false, email_field: false, email_required: false })
let keySeq = 0

// Rows arrive from the parent after a fetch: give each a stable key for v-for
watch(rows, list => {
  for (const r of list || []) if (!r._key) r._key = ++keySeq
}, { immediate: true })

onMounted(async () => {
  try {
    const { banks: list, ...rules } = await fetchBankFormMeta()
    banks.value = list || []
    meta.value = rules
  } catch (e) {
    console.warn('[BankAccountsEditor] fetchBankFormMeta failed:', e)
  }
})

function addRow() {
  rows.value.push({
    _key: ++keySeq,
    name: '',
    account_name: '',
    bank: '',
    bank_account_no: '',
    branch_code: '',
    email: '',
    is_default: rows.value.length ? 0 : 1,
  })
  focusRow(rows.value.length - 1)
}

function removeRow(i) {
  const wasDefault = rows.value[i].is_default
  rows.value.splice(i, 1)
  if (wasDefault && rows.value.length) rows.value[0].is_default = 1
}

function setDefault(i) {
  rows.value.forEach((r, j) => { r.is_default = j === i ? 1 : 0 })
}

function focusRow(i) {
  nextTick(() => {
    const cards = rootRef.value?.querySelectorAll('.grid')
    cards?.[i]?.querySelector('input')?.focus()
  })
}

function focusFirst() {
  if (!rows.value.length) addRow()
  else focusRow(0)
}

// Enter walks the bank fields; Enter on the last one saves the whole form
function next(e) {
  const inputs = Array.from(rootRef.value?.querySelectorAll('input') || [])
  const idx = inputs.indexOf(e.target)
  if (idx > -1 && idx < inputs.length - 1) inputs[idx + 1].focus()
  else emit('submit')
}

/** Message for the first invalid row, or '' when all rows can be saved. */
function validate() {
  for (const r of rows.value) {
    const no = String(r.bank_account_no || '').replace(/\s+/g, '')
    const bank = (r.bank || '').trim()
    if (!no && !bank) continue
    if (!bank) return 'Bank Name is required for every bank account'
    if (!no) return `Account number is required for the ${bank} account`
    if (!/^\d+$/.test(no)) return `Account number "${r.bank_account_no}" must contain digits only`
    const ifsc = (r.branch_code || '').trim().toUpperCase()
    if (ifsc && !/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc)) return `IFSC "${ifsc}" is not valid (e.g. SBIN0001234)`
    if (!ifsc && meta.value.ifsc_required) return `IFSC is required for account ${no}`
    if (meta.value.strict_names) {
      const holder = (r.account_name || '').trim().replace(/\s+/g, ' ')
      if (holder && !/^[A-Za-z0-9.]+( [A-Za-z0-9.]+)*$/.test(holder)) {
        return `Account holder name "${holder}" may contain only letters, digits, dots and spaces`
      }
      if (!/^[A-Za-z0-9]+( [A-Za-z0-9]+)*$/.test(bank.replace(/\s+/g, ' '))) {
        return `Bank name "${bank}" may contain only letters, digits and spaces`
      }
    }
    if (meta.value.email_required && !(r.email || '').trim() && !props.partyEmail.trim()) {
      return `Email is required for account ${no}: enter it here or in the party's Email field`
    }
  }
  return ''
}

defineExpose({ focusFirst, validate })
</script>
