<template>
  <div class="space-y-5 text-sm text-[var(--color-text)]">
    <p v-if="loading" role="status" class="py-12 text-center text-[var(--color-text-muted)]">Loading voucher details…</p>
    <div v-else-if="error" role="alert" class="rounded-xl border border-[var(--color-danger)] p-5 text-[var(--color-danger)]">
      <p>{{ error }}</p>
      <button type="button" class="mt-3 underline" @click="loadDetails">Try Again</button>
    </div>
    <template v-else-if="voucher">
      <section class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <h2 class="mb-4 text-base">Details</h2>
        <dl class="grid grid-cols-1 gap-x-8 gap-y-4 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="field in fields" :key="field.fieldname" class="min-w-0">
            <dt class="mb-1 text-xs text-[var(--color-text-muted)]">{{ field.label }}</dt>
            <dd class="whitespace-pre-wrap break-words">{{ fieldValue(voucher[field.fieldname], field) }}</dd>
          </div>
        </dl>
      </section>
      <section v-for="table in tables" :key="table.fieldname" class="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
        <h2 class="border-b border-[var(--color-border)] px-5 py-3 text-base">{{ table.label }}</h2>
        <div v-if="voucher[table.fieldname]?.length" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-[var(--color-surface-raised)]">
              <tr>
                <th class="px-3 py-2 font-normal">#</th>
                <th v-for="field in table.fields" :key="field.fieldname" class="whitespace-nowrap px-3 py-2 font-normal">{{ field.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in voucher[table.fieldname]" :key="row.name || index" class="border-t border-[var(--color-border)] align-top">
                <td class="px-3 py-2">{{ index + 1 }}</td>
                <td v-for="field in table.fields" :key="field.fieldname" class="px-3 py-2">
                  <div class="max-h-40 w-max min-w-24 max-w-sm overflow-auto whitespace-pre-wrap break-words">{{ fieldValue(row[field.fieldname], field) }}</div>
                </td>
              </tr>
            </tbody>
            <tfoot v-if="table.totals" class="border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]">
              <tr>
                <td class="px-3 py-2">Total</td>
                <td v-for="field in table.fields" :key="field.fieldname" class="px-3 py-2">
                  {{ table.totals[field.fieldname] !== undefined ? fieldValue(table.totals[field.fieldname], field) : '' }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p v-else class="px-5 py-4 text-[var(--color-text-muted)]">{{ table.empty_message || 'No entries.' }}</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { frappeGet } from '../api.js'
import { formatDMY } from '../utils/date'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
})
const voucher = ref(null)
const fields = ref([])
const tables = ref([])
const loading = ref(false)
const error = ref('')
let requestId = 0

function fieldValue(value, field) {
  if (value === null || value === undefined || value === '') return '—'
  if (field.fieldname === 'docstatus') return ['Draft', 'Submitted', 'Cancelled'][Number(value)] || String(value)
  if (field.fieldtype === 'Check') return Number(value) ? 'Yes' : 'No'
  if (field.fieldtype === 'Date') return formatDMY(String(value), '')
  if (field.fieldtype === 'Datetime') {
    const [date, time = ''] = String(value).split(' ')
    return `${formatDMY(date, '')} ${time.split('.')[0]}`.trim()
  }
  if (['Currency', 'Float', 'Percent'].includes(field.fieldtype)) {
    return Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 6 })
  }
  if (field.fieldtype === 'Text Editor') {
    return new DOMParser().parseFromString(String(value), 'text/html').body.textContent || '—'
  }
  return String(value)
}

async function loadDetails() {
  const currentRequest = ++requestId
  voucher.value = null
  fields.value = []
  tables.value = []
  error.value = ''
  loading.value = true
  try {
    const result = await frappeGet('ssplbilling.api.daily_report_api.get_daily_voucher_details', {
      doctype: props.doctype,
      name: props.name,
    })
    if (currentRequest !== requestId) return
    voucher.value = result.document
    fields.value = result.fields || []
    tables.value = result.tables || []
  } catch (e) {
    if (currentRequest === requestId) error.value = e.message || 'Failed to load voucher details.'
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

watch(() => [props.doctype, props.name], loadDetails, { immediate: true })
onUnmounted(() => { ++requestId })
</script>
