<template>
  <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
    <div class="w-[500px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-[var(--color-text)]">Create GST Bill (Quotation)</h2>
          <p class="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider text-left">Select naming series to create Quotation from this Sales Invoice</p>
        </div>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Fetching allowed quotation series...</p>
      </div>

      <div v-else-if="creating" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-success)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Creating quotation...</p>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div 
          v-for="(s, idx) in allowedSeries" 
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
              🔖
              <span class="absolute -top-1.5 -left-1.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-black"
                    :class="focusedIndex === idx ? 'bg-[var(--color-text-on-focus)] text-[var(--color-focus)]' : 'bg-[var(--color-text)] text-[var(--color-bg)]'">
                {{ idx + 1 }}
              </span>
            </div>
            <div>
              <div class="text-lg font-bold" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ s }}</div>
              <div class="text-[10px] font-medium uppercase tracking-wider text-left" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]/70' : 'text-[var(--color-text-muted)]'">Naming Series</div>
            </div>
          </div>
        </div>

        <div v-if="!allowedSeries.length" class="py-12 text-center text-[var(--color-text-muted)] italic">
          No allowed quotation series found for your user profile.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { frappeGet, frappePost } from '../api'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { useRouter } from 'vue-router'

const props = defineProps({
  show: Boolean,
  invoiceName: { type: String, required: true }
})

const emit = defineEmits(['close', 'created'])
const router = useRouter()

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close')
})

const allowedSeries = ref([])
const loading = ref(false)
const creating = ref(false)
const focusedIndex = ref(0)

async function fetchAllowedSeries() {
  loading.value = true
  try {
    const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', {
      doctype: 'Quotation'
    })
    allowedSeries.value = d.allowed_series || []
  } catch (e) {
    console.error('[Gstbillcreator] Fetch failed:', e)
  } finally {
    loading.value = false
  }
}

async function selectSeries(s) {
  creating.value = true
  try {
    const res = await frappePost('ssplbilling.api.quotation_api.create_quotation_from_sales_invoice', {
      sales_invoice_name: props.invoiceName,
      naming_series: s
    })
    if (res && res.quotation_name) {
      alert(`Quotation ${res.quotation_name} created successfully!`)
      emit('created', res.quotation_name)
      emit('close')
    } else {
      alert('Failed to create Quotation.')
    }
  } catch (e) {
    console.error('[Gstbillcreator] Conversion failed:', e)
    alert(e.message || 'Failed to create Quotation from Sales Invoice.')
  } finally {
    creating.value = false
  }
}

function handleKeydown(e) {
  if (!props.show || loading.value || creating.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedIndex.value = (focusedIndex.value + 1) % allowedSeries.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIndex.value = (focusedIndex.value - 1 + allowedSeries.value.length) % allowedSeries.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (allowedSeries.value[focusedIndex.value]) {
      selectSeries(allowedSeries.value[focusedIndex.value])
    }
  } else if (e.key >= '1' && e.key <= '9') {
    const idx = parseInt(e.key) - 1
    if (allowedSeries.value[idx]) {
      selectSeries(allowedSeries.value[idx])
    }
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    focusedIndex.value = 0
    fetchAllowedSeries()
    window.addEventListener('keydown', handleKeydown)
  } else {
    window.removeEventListener('keydown', handleKeydown)
  }
})

onMounted(() => {
  if (props.show) {
    fetchAllowedSeries()
    window.addEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
