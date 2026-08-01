<template>
  <div
    v-if="show"
    ref="modalRef"
    tabindex="-1"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm outline-none"
  >
    <div class="w-[500px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl">
      <div class="mb-6 flex items-start justify-between">
        <div class="flex-1 mr-4">
          <h2 class="text-2xl font-bold text-[var(--color-text)]">Mirror Bill</h2>
          <p class="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider text-left">
            Select conversion series to mirror this invoice
            <template v-if="targetCompany"> into {{ targetCompany }}</template>
          </p>
        </div>
        <button
          @click="$emit('close')"
          class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] focus:outline-none transition-colors"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Fetching conversion series...</p>
      </div>

      <div v-else-if="creating" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-success)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Creating mirror Sales Invoice...</p>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div
          v-for="(s, idx) in seriesList"
          :key="s"
          @click="selectSeries(s)"
          class="group flex cursor-pointer items-center justify-between border-b border-[var(--color-border)] px-5 py-4 transition-colors border-l-4"
          :class="focusedIndex === idx
            ? 'bg-[var(--color-focus)] border-l-[var(--color-focus)] text-[var(--color-text-on-focus)] font-bold'
            : 'bg-[var(--color-surface)] border-l-transparent hover:bg-[var(--color-midlight)]/40'"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg text-xl relative"
                 :class="focusedIndex === idx ? 'bg-black/10' : 'bg-[var(--color-highlight)]'">
              🪞
              <span class="absolute -top-1.5 -left-1.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-black"
                    :class="focusedIndex === idx ? 'bg-[var(--color-text-on-focus)] text-[var(--color-focus)]' : 'bg-[var(--color-text)] text-[var(--color-bg)]'">
                {{ idx + 1 }}
              </span>
            </div>
            <div>
              <div class="text-lg font-bold" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ s }}</div>
              <div class="text-[10px] font-medium uppercase tracking-wider text-left" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]/70' : 'text-[var(--color-text-muted)]'">Conversion Invoice Series</div>
            </div>
          </div>
        </div>

        <div v-if="!seriesList.length" class="py-12 text-center text-[var(--color-text-muted)] italic">
          No Conversion Invoice Series configured in Automatic Entries.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { frappeGet, frappePost } from '../api'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  invoiceName: { type: String, required: true }
})

const emit = defineEmits(['close', 'created'])

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close')
})

const modalRef = ref(null)
const seriesList = ref([])
const targetCompany = ref('')
const loading = ref(false)
const creating = ref(false)
const focusedIndex = ref(0)

function parseConversionSeries(rows) {
  const set = new Set()
  for (const r of rows || []) {
    for (const raw of String(r.conversion_invoice_series || '').split(',')) {
      const val = raw.trim()
      if (val) set.add(val)
    }
  }
  return [...set]
}

// Cache-first: ae-* keys are synced to localStorage by Dashboard/GeneralSettings;
// fall back to the server only when the local cache is empty.
async function loadSeries() {
  targetCompany.value = localStorage.getItem('ae-alternative_company') || ''
  try {
    seriesList.value = parseConversionSeries(JSON.parse(localStorage.getItem('ae-series') || '[]'))
  } catch {
    seriesList.value = []
  }
  if (seriesList.value.length) return

  loading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.automatic_entries_api.get_conversion_series')
    seriesList.value = res?.series || []
    if (res?.company) targetCompany.value = res.company
  } catch (e) {
    console.error('[BillMirrorCreator] Failed to fetch conversion series:', e)
  } finally {
    loading.value = false
  }
}

async function selectSeries(s) {
  creating.value = true
  try {
    // Series-specific defaults cached from SSPL Billing Settings
    let seriesEntry = null
    try {
      const cached = JSON.parse(localStorage.getItem('wb-settings-v2') || 'null')
      seriesEntry = cached?.data?.billing_series?.find(bs => bs.series === s || bs.series.startsWith(s + '.')) || null
    } catch { /* ignore cache parse errors */ }

    const res = await frappePost('ssplbilling.api.automatic_entries_api.create_conversion_mirror_invoice', {
      sales_invoice_name: props.invoiceName,
      naming_series: s,
      price_list: seriesEntry?.price_list || undefined,
      tax_template: seriesEntry?.tax_template || undefined,
      tax_type_incl: seriesEntry?.tax_type_incl !== undefined ? seriesEntry.tax_type_incl : undefined
    })

    if (res && res.invoice_name) {
      alert(`Draft mirror Sales Invoice ${res.invoice_name} created in ${res.company}!`)
      emit('created', res.invoice_name)
      emit('close')
    } else {
      alert('Failed to create mirror Sales Invoice.')
    }
  } catch (e) {
    console.error('[BillMirrorCreator] Mirroring failed:', e)
    alert(e.message || 'Failed to create mirror Sales Invoice.')
  } finally {
    creating.value = false
  }
}

function handleKeydown(e) {
  if (!props.show || loading.value || creating.value) return

  if (e.key === 'Tab') {
    e.preventDefault()
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedIndex.value = (focusedIndex.value + 1) % seriesList.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIndex.value = (focusedIndex.value - 1 + seriesList.value.length) % seriesList.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (seriesList.value[focusedIndex.value]) {
      selectSeries(seriesList.value[focusedIndex.value])
    }
  } else if (e.key === 'Escape' || e.key === 'Esc') {
    e.preventDefault()
    emit('close')
  } else if (e.key >= '1' && e.key <= '9') {
    const idx = parseInt(e.key) - 1
    if (seriesList.value[idx]) {
      selectSeries(seriesList.value[idx])
    }
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    focusedIndex.value = 0
    loadSeries()
    window.addEventListener('keydown', handleKeydown)
    nextTick(() => {
      modalRef.value?.focus()
    })
  } else {
    window.removeEventListener('keydown', handleKeydown)
  }
})

onMounted(() => {
  if (props.show) {
    loadSeries()
    window.addEventListener('keydown', handleKeydown)
    nextTick(() => {
      modalRef.value?.focus()
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
