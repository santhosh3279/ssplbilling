<template>
  <aside class="flex h-[45vh] w-full shrink-0 flex-col overflow-hidden border-t border-[var(--color-border)] bg-[var(--color-surface)] md:h-auto md:w-80 md:border-l md:border-t-0 xl:w-96" aria-label="Submitted bill palette">
    <div class="border-b border-[var(--color-border)] p-3">
      <h2 class="mb-3 text-lg font-bold text-[var(--color-text)]">Submitted Bills</h2>
      <label for="submitted-series" class="mb-1 block text-xs font-bold uppercase text-[var(--color-text-muted)]">Invoice Series</label>
      <select id="submitted-series" v-model="selectedSeries" :disabled="busy" class="mb-3 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-2 text-[var(--color-text)]">
        <option value="">All Series</option>
        <option v-for="series in availableSeries" :key="series" :value="series">{{ series }}</option>
      </select>
      <p v-if="!availableSeries.length" class="mb-3 text-xs text-[var(--color-text-muted)]">No saved series available. You can still search by bill number or party name.</p>
      <form class="flex gap-2" @submit.prevent="searchBills">
        <input ref="searchInputRef" v-model="searchText" :disabled="busy" type="search" aria-label="Search bill number or party name" placeholder="Bill no. or party name" class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" />
        <button type="submit" :disabled="busy || loading" class="rounded-lg bg-[var(--color-info)] px-3 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] disabled:opacity-50">Search</button>
      </form>
      <p class="mt-2 text-xs text-[var(--color-text-muted)]">{{ bills.length }} submitted bills</p>
    </div>
    <div class="min-h-0 flex-1 overflow-y-auto" aria-live="polite">
      <p v-if="error" class="p-3 text-sm text-[var(--color-danger)]" role="alert">{{ error }}</p>
      <p v-if="!bills.length && !loading && !error" class="p-4 text-center text-sm italic text-[var(--color-text-muted)]">No submitted bills found.</p>
      <template v-for="(bill, index) in bills" :key="`${bill.doctype}:${bill.name}`">
        <div v-if="index === 0 || bill.date !== bills[index - 1].date" class="sticky top-0 border-b border-[var(--color-border)] bg-[var(--color-lowlight)] px-3 py-1 text-sm font-bold text-[var(--color-text-muted)]">{{ formatDMY(bill.date) }}</div>
        <button type="button" :disabled="busy" :aria-pressed="selectedName === bill.name && selectedDoctype === bill.doctype" @click="$emit('select', bill)" @keydown.down.prevent="focusAdjacent($event, 1)" @keydown.up.prevent="focusAdjacent($event, -1)" class="block w-full border-b border-[var(--color-border)] px-3 py-2 text-left outline-none focus:ring-2 focus:ring-inset focus:ring-[var(--color-info)] disabled:opacity-60" :class="selectedName === bill.name && selectedDoctype === bill.doctype ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)] hover:bg-[var(--color-midlight)]'">
          <div class="flex items-baseline justify-between gap-2">
            <span class="min-w-0 truncate font-mono text-xl font-bold">{{ bill.name }}</span>
            <span class="shrink-0 font-mono text-lg tabular-nums">{{ formatAmount(bill.total) }}</span>
          </div>
          <div class="truncate text-lg">{{ bill.party || '—' }}</div>
          <div class="mt-1 text-xs opacity-70">{{ bill.doctype }}</div>
        </button>
      </template>
      <p v-if="loading" class="p-3 text-center text-sm text-[var(--color-text-muted)]">Loading bills…</p>
      <button v-if="hasMore" type="button" :disabled="loading || busy" @click="loadBills(true)" class="w-full p-3 text-sm font-bold text-[var(--color-info)] disabled:opacity-50">Load more</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { frappeGet } from '../api'
import { formatDMY } from '../utils/date'
import { BILL_TYPES, readBillSeries, billListParams, sortSubmittedBills } from '../services/submittedBillPalette'

const props = defineProps({
  busy: Boolean,
  selectedName: { type: String, default: '' },
  selectedDoctype: { type: String, default: '' },
})
defineEmits(['select'])
const availableSeries = ref(readBillSeries())
const selectedSeries = ref('')
const searchText = ref('')
const submittedSearch = ref('')
const searchInputRef = ref(null)
const bills = ref([])
const loading = ref(false)
const error = ref('')
const offsets = new Map()
const moreTypes = ref(BILL_TYPES.map(type => type.doctype))
const hasMore = computed(() => moreTypes.value.length > 0)
const PAGE_SIZE = 50
let requestVersion = 0
let disposed = false

async function loadBills(append = false) {
  if (append && loading.value) return
  const version = ++requestVersion
  if (!append) {
    offsets.clear()
    bills.value = []
    moreTypes.value = BILL_TYPES.map(type => type.doctype)
  }
  loading.value = true
  error.value = ''
  const types = BILL_TYPES.filter(type => moreTypes.value.includes(type.doctype))
  const selected = selectedSeries.value ? [selectedSeries.value] : availableSeries.value
  const company = localStorage.getItem('wb-company') || ''
  const responses = await Promise.allSettled(types.map(async type => {
    const start = offsets.get(type.doctype) || 0
    const rows = await frappeGet('frappe.client.get_list', billListParams(type, {
      query: submittedSearch.value, series: selected, company, start, limit: PAGE_SIZE,
    }))
    return { type, rows: rows || [], start }
  }))
  if (disposed || version !== requestVersion) return
  const next = append ? [...bills.value] : []
  const more = []
  const failed = []
  for (let i = 0; i < responses.length; i++) {
    const result = responses[i]
    if (result.status === 'rejected') {
      failed.push(types[i].doctype)
      continue
    }
    const { type, rows, start } = result.value
    offsets.set(type.doctype, start + rows.length)
    if (rows.length === PAGE_SIZE) more.push(type.doctype)
    next.push(...rows.map(row => ({
      doctype: type.doctype, name: row.name, date: row[type.date] || '',
      party: row[type.party] || '', total: row.grand_total || 0,
    })))
  }
  bills.value = sortSubmittedBills([...new Map(next.map(bill => [`${bill.doctype}:${bill.name}`, bill])).values()])
  moreTypes.value = more
  if (failed.length) error.value = `Could not load ${failed.join(', ')}. Search again to retry.`
  loading.value = false
}

function searchBills() {
  submittedSearch.value = searchText.value.trim()
  return loadBills()
}
function refresh() { return loadBills() }
function focusSearch() { nextTick(() => { searchInputRef.value?.focus(); searchInputRef.value?.select() }) }
function focusAdjacent(event, direction) {
  const buttons = [...event.currentTarget.parentElement.querySelectorAll('button[aria-pressed]')]
  const target = buttons[buttons.indexOf(event.currentTarget) + direction]
  target?.focus()
  target?.scrollIntoView({ block: 'nearest' })
}
function formatAmount(value) {
  return Number(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function reloadLocalSeries() { availableSeries.value = readBillSeries() }
watch(selectedSeries, () => { submittedSearch.value = searchText.value.trim(); loadBills() })
onMounted(() => { loadBills(); window.addEventListener('storage', reloadLocalSeries) })
onUnmounted(() => { disposed = true; requestVersion++; window.removeEventListener('storage', reloadLocalSeries) })
defineExpose({ focusSearch, refresh })
</script>
