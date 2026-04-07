<template>
  <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="w-[500px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-[var(--color-text)]">Select Billing Series</h2>
          <p class="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider">Choose your active series for this session</p>
        </div>
        <button @click="$emit('close')" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Fetching allowed series...</p>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div 
          v-for="s in allowedSeries" 
          :key="s"
          @click="selectSeries(s)"
          class="group flex cursor-pointer items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 transition-all hover:translate-x-1 hover:border-[var(--color-highlight)] hover:bg-[var(--color-surface-raised)]"
          :class="{ 'border-[var(--color-highlight)] ring-2 ring-[var(--color-highlight)]/20 bg-[var(--color-surface-raised)]': currentSeries === s }"
        >
          <div class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-highlight)] text-xl">
              🔖
            </div>
            <div>
              <div class="text-lg font-bold text-[var(--color-text)]">{{ s }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)] font-medium uppercase tracking-wider">Naming Series</div>
            </div>
          </div>
          <div v-if="currentSeries === s" class="text-[var(--color-highlight)]">
            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>

        <div v-if="!allowedSeries.length" class="py-12 text-center text-slate-500 italic">
          No allowed series found for your user profile.
        </div>
      </div>

      <div class="mt-8 flex justify-end">
        <button 
          @click="$emit('close')"
          class="rounded-lg border border-[var(--color-border)] px-6 py-2.5 text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-all"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { frappeGet } from '../api'

const props = defineProps({
  show: Boolean,
  doctype: { type: String, default: 'Sales Invoice' }
})

const emit = defineEmits(['close', 'selected'])

const allowedSeries = ref([])
const loading = ref(false)
const currentSeries = ref(localStorage.getItem('wb-series') || '')

async function fetchAllowedSeries() {
  loading.value = true
  try {
    const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', {
      doctype: props.doctype
    })
    allowedSeries.value = d.allowed_series || []
    
    // If no series selected yet, or current is not in allowed, auto-select first
    if (!currentSeries.value && allowedSeries.value.length) {
      // Don't auto-select here, let user choose explicitly or keep from storage
    }
  } catch (e) {
    console.error('[Userseries] Fetch failed:', e)
  } finally {
    loading.value = false
  }
}

function selectSeries(s) {
  currentSeries.value = s
  localStorage.setItem('wb-series', s)
  emit('selected', s)
  emit('close')
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    currentSeries.value = localStorage.getItem('wb-series') || ''
    fetchAllowedSeries()
  }
})

onMounted(() => {
  if (props.show) fetchAllowedSeries()
})
</script>
