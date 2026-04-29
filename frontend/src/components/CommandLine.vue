<template>
  <div
    v-if="show"
    class="fixed bottom-0 left-0 right-0 z-[1000] bg-[var(--color-surface)] border-t border-[var(--color-border)] shadow-2xl p-2 animate-in slide-in-from-bottom duration-200"
  >
    <div class="max-w-4xl mx-auto">
      <!-- History and Suggestions -->
      <div v-if="history.length || suggestions.length" class="mb-4 max-h-80 overflow-y-auto bg-[var(--color-bg)] rounded border border-[var(--color-border)]">
        <div v-for="(item, i) in history" :key="'h-'+i" class="text-lg text-[var(--color-text-muted)] font-mono px-2 border-b border-[var(--color-border)] last:border-0">
          <span class="text-[var(--color-info)]">calc:</span> {{ item.input }} = <span class="text-[var(--color-text)] font-bold">{{ item.result }}</span>
        </div>
        <div v-for="(route, i) in suggestions" :key="'r-'+i" 
             class="text-lg px-2 cursor-pointer hover:bg-[var(--color-surface-raised)] rounded flex justify-between items-center"
             :class="{ 'bg-[var(--color-surface-raised)]': i === activeSuggestionIndex }"
             @click="navigateTo(route)"
        >
          <span>{{ route.meta?.title || route.name }}</span>
          <span class="text-[var(--color-text-muted)] text-sm font-mono">{{ route.path }}</span>
        </div>
      </div>

      <!-- Input Line -->
      <div class="flex items-center gap-2">
        <div class="text-[var(--color-info)] font-mono font-bold text-lg">></div>
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          class="flex-1 bg-transparent border-none outline-none text-[var(--color-text)] font-mono text-lg placeholder:text-[var(--color-text-muted)]/50"
          placeholder="Calculate or search page..."
          @keydown="handleKeydown"
          @input="updateSuggestions"
        />
        <div class="flex items-center gap-2 text-[var(--color-text-muted)] text-[10px] uppercase font-bold tracking-tighter">
          <span class="px-1 py-0.5 rounded border border-[var(--color-border)] bg-[var(--color-bg)]">ENTER</span> to execute
          <span class="px-1 py-0.5 rounded border border-[var(--color-border)] bg-[var(--color-bg)]">ESC</span> to close
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean
})
const emit = defineEmits(['close'])

const router = useRouter()
const inputRef = ref(null)
const query = ref('')
const history = ref([])
const suggestions = ref([])
const activeSuggestionIndex = ref(0)
const historyIndex = ref(-1)
const lastActiveElement = ref(null)

// Block global shortcuts when command line is open
useSubwindowWatcher(computed(() => props.show), {
  'ESCAPE': () => close()
})

function close() {
  emit('close')
  historyIndex.value = -1
  if (lastActiveElement.value && typeof lastActiveElement.value.focus === 'function') {
    nextTick(() => lastActiveElement.value.focus())
  }
}

watch(() => props.show, (val) => {
  if (val) {
    lastActiveElement.value = document.activeElement
    query.value = ''
    suggestions.value = []
    historyIndex.value = -1
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
})

function handleKeydown(e) {
  if (e.key === 'Escape') {
    close()
    return
  }

  if (e.key === 'Enter') {
    execute()
    return
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (suggestions.value.length > 0) {
      activeSuggestionIndex.value = (activeSuggestionIndex.value + 1) % suggestions.value.length
    } else if (historyIndex.value >= 0) {
      historyIndex.value--
      query.value = historyIndex.value === -1 ? '' : history.value[historyIndex.value].input
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (suggestions.value.length > 0) {
      activeSuggestionIndex.value = (activeSuggestionIndex.value - 1 + suggestions.value.length) % suggestions.value.length
    } else if (history.value.length > 0) {
      historyIndex.value = Math.min(historyIndex.value + 1, history.value.length - 1)
      query.value = history.value[historyIndex.value].input
    }
  }
}

function updateSuggestions() {
  // Reset history index if user types something manually
  const isFromHistory = historyIndex.value !== -1 && history.value[historyIndex.value]?.input === query.value
  if (!isFromHistory) {
    historyIndex.value = -1
  }

  if (!query.value.trim()) {
    suggestions.value = []
    return
  }

  // If it looks like a math expression, don't show route suggestions as prominently or filter them
  const isMath = /^[\d\s+\-*/%().]+$/.test(query.value)
  if (isMath) {
    suggestions.value = []
    return
  }

  const q = query.value.toLowerCase()
  suggestions.value = router.getRoutes().filter(r => {
    // Only suggest routes with titles and not the current one
    if (!r.meta?.title) return false
    return r.meta.title.toLowerCase().includes(q) || r.name?.toLowerCase().includes(q) || r.path.toLowerCase().includes(q)
  }).slice(0, 5)
  
  activeSuggestionIndex.value = 0
}

function execute() {
  const q = query.value.trim()
  if (!q) return

  // Try math evaluation
  try {
    // Simple math check to avoid security issues with eval (though this is local)
    if (/^[\d\s+\-*/%().]+$/.test(q)) {
      // eslint-disable-next-line no-eval
      const result = eval(q)
      history.value.unshift({ input: q, result })
      if (history.value.length > 3) history.value.pop()
      query.value = ''
      historyIndex.value = -1
      return
    }
  } catch (err) {
    // Not a math expression or invalid math
  }

  // If suggestions exist, navigate to the active one
  if (suggestions.value.length > 0) {
    navigateTo(suggestions.value[activeSuggestionIndex.value])
    return
  }

  // Fallback: try to find a route that matches exactly
  const exactMatch = router.getRoutes().find(r => 
    r.meta?.title?.toLowerCase() === q.toLowerCase() || 
    r.name?.toLowerCase() === q.toLowerCase()
  )
  if (exactMatch) {
    navigateTo(exactMatch)
  }
}

function navigateTo(route) {
  router.push(route.path)
  close()
}
</script>

<style scoped>
@keyframes slide-in-from-bottom {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
.animate-in {
  animation-fill-mode: both;
}
</style>
