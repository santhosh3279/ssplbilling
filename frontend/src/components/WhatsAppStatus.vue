<template>
  <div v-if="digits(number)" class="flex flex-wrap items-center gap-2 text-xs">
    <span class="rounded-full px-2 py-0.5 font-bold uppercase tracking-wider" :class="badge.cls">{{ badge.label }}</span>
    <span v-if="shownCheckedOn" class="text-[var(--color-text-muted)]">{{ shownCheckedOn }}</span>
    <span v-if="note" class="text-[var(--color-text-muted)]">{{ note }}</span>
    <button
      v-if="canCheck"
      type="button"
      tabindex="-1"
      :disabled="checking"
      class="rounded px-2 py-0.5 font-semibold text-[var(--color-info)] hover:bg-[var(--color-info)]/15 disabled:opacity-50"
      @click="checkNow"
    >
      {{ checking ? 'Checking…' : 'Check now' }}
    </button>
  </div>
</template>

<script setup>
// WhatsApp number status for a Customer / Supplier form. Nothing is checked on its own: the
// number is checked when the party is saved, or when the operator presses "Check now".
import { ref, computed, watch } from 'vue'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  partyDoctype: { type: String, required: true },
  party: { type: String, default: '' },
  number: { type: String, default: '' },
})

const API = 'ssplbilling.api.whatsapp_api'

const saved = ref(null) // { status, verified_number, checked_on, phone }
const checking = ref(false)
const note = ref('')

// Compare on the last 10 digits: the form holds 10 digits, the server keeps the country code
function digits(value) {
  return String(value || '').replace(/\D/g, '').slice(-10)
}

// The stored status belongs to the number that was checked, not to whatever is typed now
const sameAsChecked = computed(() => !!saved.value && digits(props.number) === digits(saved.value.verified_number))
const sameAsSaved = computed(() => !!saved.value && digits(props.number) === digits(saved.value.phone))

const status = computed(() => (sameAsChecked.value ? saved.value.status : 'Not Checked'))

const badge = computed(() => {
  if (status.value === 'Valid') return { label: 'On WhatsApp', cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' }
  if (status.value === 'Invalid') return { label: 'Not on WhatsApp', cls: 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]' }
  return { label: 'Not checked', cls: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' }
})

const shownCheckedOn = computed(() => {
  if (!sameAsChecked.value || !saved.value.checked_on) return ''
  return 'checked ' + String(saved.value.checked_on).slice(0, 16)
})

// "Check now" checks the number saved on the party, so it is offered only while the form shows it
const canCheck = computed(() => !!props.party && sameAsSaved.value)

async function load() {
  note.value = ''
  if (!props.party) {
    saved.value = null
    return
  }
  try {
    saved.value = await frappeGet(`${API}.get_party_whatsapp_status`, { party_doctype: props.partyDoctype, party: props.party })
  } catch {
    saved.value = null
  }
}

async function checkNow() {
  checking.value = true
  note.value = ''
  try {
    const r = await frappePost(`${API}.verify_party_whatsapp`, { party_doctype: props.partyDoctype, party: props.party }, { silent: true })
    if (r.error) note.value = r.error
    await load()
    if (r.error) note.value = r.error
  } catch (e) {
    note.value = e.message || String(e)
  } finally {
    checking.value = false
  }
}

watch(() => props.party, load, { immediate: true })
watch(() => props.number, () => { if (!sameAsSaved.value) note.value = digits(props.number).length === 10 ? 'checked when you save' : '' })
</script>
