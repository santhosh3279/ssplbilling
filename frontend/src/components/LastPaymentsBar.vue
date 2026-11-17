<template>
  <div
    v-if="party && (payments.length || loading || checked)"
    class="flex items-start gap-6 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-8 py-2"
  >
    <div class="flex flex-col pt-2">
      <span class="text-xl font-black uppercase tracking-widest text-[var(--color-text-muted)] whitespace-nowrap">Last Payments</span>
      <span v-if="label" class="max-w-[260px] truncate text-lg font-bold text-[var(--color-text-muted)]">{{ label }}</span>
    </div>
    <span v-if="loading" class="text-4xl font-normal text-[var(--color-text-muted)]">Loading…</span>
    <span v-else-if="!payments.length" class="text-4xl font-normal text-[var(--color-text-muted)]">No previous payments</span>
    <table v-else class="border-collapse">
      <tbody>
        <tr
          v-for="p in payments"
          :key="p.name"
          :title="`${p.name}${p.reference_no ? ' · Ref ' + p.reference_no : ''}`"
        >
          <td class="py-0.5 pr-6">
            <span
              class="inline-block rounded-xl px-4 py-0.5 text-2xl font-black uppercase"
              :class="p.payment_type === 'Receive'
                ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]'
                : p.payment_type === 'Pay'
                  ? 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'
                  : 'bg-[var(--color-highlight)]/15 text-[var(--color-highlight)]'"
            >{{ p.payment_type === 'Receive' ? 'Receipt' : p.payment_type === 'Pay' ? 'Payment' : 'Transfer' }}</span>
          </td>
          <td class="py-0.5 pr-6 text-right text-4xl font-black whitespace-nowrap">₹{{ Number(p.paid_amount || 0).toLocaleString('en-IN') }}</td>
          <td class="py-0.5 pr-4 text-3xl font-normal whitespace-nowrap">{{ formatDate(p.posting_date) }}</td>
          <td class="py-0.5 pr-6 text-2xl font-normal text-[var(--color-text-muted)] whitespace-nowrap">({{ p.days_ago === 0 ? 'today' : `${p.days_ago}d ago` }})</td>
          <td class="py-0.5 text-3xl font-normal whitespace-nowrap">{{ p.mop_account }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
// Shows the last few submitted Payment Entries of a party (or account) as a large bar.
import { ref, watch } from 'vue'
import { frappeGet } from '../api.js'
import { parseCalendarDate } from '../services/serverTime'

const props = defineProps({
  party: { type: String, default: '' },
  partyType: { type: String, default: '' },
  label: { type: String, default: '' },
  limit: { type: Number, default: 3 },
})

const payments = ref([])
const loading = ref(false)
const checked = ref(false)
let seq = 0

async function load() {
  const mySeq = ++seq
  payments.value = []
  checked.value = false
  loading.value = false
  if (!props.party) return
  loading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.paymentv2_api.get_last_payments', {
      party: props.party,
      party_type: props.partyType || '',
      company: localStorage.getItem('wb-company') || '',
      limit: props.limit,
    })
    if (mySeq !== seq) return
    payments.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('Failed to fetch last payments:', e)
  } finally {
    if (mySeq === seq) {
      loading.value = false
      checked.value = true
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = parseCalendarDate(dateStr)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${String(d.getDate()).padStart(2, '0')}-${months[d.getMonth()]}-${d.getFullYear()}`
}

watch(() => [props.party, props.partyType], load, { immediate: true })
</script>
