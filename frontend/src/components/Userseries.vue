<template>
  <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
    <div class="w-[500px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] p-6 shadow-2xl">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-[var(--color-text)]">Select Billing Series</h2>
          <p class="text-xs text-[var(--color-text-muted)] font-medium uppercase tracking-wider">Choose your active series for this session</p>
        </div>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-12">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--color-highlight)] border-t-transparent"></div>
        <p class="mt-4 text-sm text-[var(--color-text-muted)] font-medium">Fetching allowed series...</p>
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
              <div class="text-[10px] font-medium uppercase tracking-wider" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]/70' : 'text-[var(--color-text-muted)]'">Naming Series</div>
            </div>
          </div>
          <div v-if="currentSeries === s" :class="focusedIndex === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">
            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>

        <div v-if="!allowedSeries.length" class="py-12 text-center text-[var(--color-text-muted)] italic">
          No allowed series found for your user profile.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  doctype: { type: String, default: 'Sales Invoice' }
})

const emit = defineEmits(['close', 'selected'])

useSubwindowWatcher(computed(() => props.show), {
  ESCAPE: () => emit('close')
})

// Cache-first: resolves from the local series cache ∩ wb-allowed-series,
// hitting the server only when the local data is unavailable.
const { allowedSeries, loading, fetchAllowedSeries: fetchSeries } = useAllowedSeries()
const currentSeries = ref(localStorage.getItem('wb-series') || '')
const focusedIndex = ref(0)

async function fetchAllowedSeries() {
  await fetchSeries(props.doctype)

  // Set focused index to current series if found, otherwise 0
  if (currentSeries.value) {
    const idx = allowedSeries.value.indexOf(currentSeries.value)
    if (idx !== -1) focusedIndex.value = idx
  }
}

function selectSeries(s) {
  currentSeries.value = s
  localStorage.setItem('wb-series', s)
  emit('selected', s)
  emit('close')
}

function handleKeydown(e) {
  if (!props.show || loading.value) return

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
    // Top row and numpad both return "1"-"9"
    const idx = parseInt(e.key) - 1
    if (allowedSeries.value[idx]) {
      selectSeries(allowedSeries.value[idx])
    }
  }
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    currentSeries.value = localStorage.getItem('wb-series') || ''
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
