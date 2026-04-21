<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
    @click.self="close"
  >
    <div
      ref="calculatorRef"
      tabindex="-1"
      class="w-80 overflow-hidden rounded-3xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl outline-none"
      @keydown.esc="close"
    >
      <!-- Display -->
      <div class="p-6 bg-[var(--color-surface)]/50">
        <div class="text-right text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-1 h-4">
          {{ prevInput }} {{ operator }}
        </div>
        <div class="text-right text-4xl font-black text-[var(--color-text)] font-mono truncate">
          {{ display || '0' }}
        </div>
      </div>

      <!-- Buttons Grid -->
      <div class="grid grid-cols-4 gap-px bg-[var(--color-surface)] p-1">
        <button
          v-for="btn in buttons"
          :key="btn.label"
          @click="handleInput(btn)"
          class="h-16 text-xl font-bold transition-all active:scale-95"
          :class="[
            btn.type === 'operator' ? 'bg-[var(--color-surface)] text-[var(--color-info)] hover:bg-[var(--color-surface-raised)]' :
            btn.type === 'action' ? 'bg-[var(--color-surface)] text-[var(--color-danger)] hover:bg-[var(--color-surface-raised)]' :
            'bg-[var(--color-bg)] text-[var(--color-text)] hover:bg-[var(--color-surface)]'
          ]"
        >
          {{ btn.label }}
        </button>
      </div>

      <div class="p-4 bg-[var(--color-bg)] text-center">
        <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-tighter">
          Press <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text)]">ESC</kbd> to Close
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean
})
const emit = defineEmits(['close'])

const calculatorRef = ref(null)
const display = ref('')
const prevInput = ref('')
const operator = ref('')
const shouldReset = ref(false)

const buttons = [
  { label: 'C', type: 'action' },
  { label: 'DEL', type: 'action' },
  { label: '%', type: 'operator' },
  { label: '/', type: 'operator' },
  { label: '7', type: 'number' },
  { label: '8', type: 'number' },
  { label: '9', type: 'number' },
  { label: '*', type: 'operator' },
  { label: '4', type: 'number' },
  { label: '5', type: 'number' },
  { label: '6', type: 'number' },
  { label: '-', type: 'operator' },
  { label: '1', type: 'number' },
  { label: '2', type: 'number' },
  { label: '3', type: 'number' },
  { label: '+', type: 'operator' },
  { label: '0', type: 'number' },
  { label: '.', type: 'number' },
  { label: '=', type: 'operator', cols: 2 }
]

function handleInput(btn) {
  if (btn.type === 'number') {
    if (shouldReset.value) {
      display.value = btn.label
      shouldReset.value = false
    } else {
      if (btn.label === '.' && display.value.includes('.')) return
      display.value += btn.label
    }
  } else if (btn.type === 'action') {
    if (btn.label === 'C') {
      display.value = ''
      prevInput.value = ''
      operator.value = ''
    } else if (btn.label === 'DEL') {
      display.value = display.value.slice(0, -1)
    }
  } else if (btn.type === 'operator') {
    if (btn.label === '=') {
      calculate()
    } else {
      if (display.value === '' && btn.label === '-') {
        display.value = '-'
        return
      }
      if (display.value === '') return
      prevInput.value = display.value
      operator.value = btn.label
      shouldReset.value = true
    }
  }
}

function calculate() {
  if (!operator.value || !prevInput.value || !display.value) return
  const a = parseFloat(prevInput.value)
  const b = parseFloat(display.value)
  let result = 0
  switch (operator.value) {
    case '+': result = a + b; break
    case '-': result = a - b; break
    case '*': result = a * b; break
    case '/': result = a / b; break
    case '%': result = a % b; break
  }
  display.value = String(Number(result.toFixed(8)))
  prevInput.value = ''
  operator.value = ''
  shouldReset.value = true
}

function close() {
  emit('close')
}

watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      calculatorRef.value?.focus()
    })
  }
})

function handleKeydown(e) {
  if (!props.show) return
  
  // Intercept and prevent EVERYTHING to block background shortcuts
  // We only allow Browser DevTools (F12) and some essential browser combos to leak if needed.
  // Using capture phase listener + e.stopPropagation() ensures other listeners don't see the event.
  const isFunctionKey = e.key.startsWith('F') && e.key !== 'F12'
  const isBrowserShortcut = (e.ctrlKey || e.metaKey) && ['r', 'R', 'l', 'L'].includes(e.key)
  
  if (!isFunctionKey && !isBrowserShortcut) {
    e.preventDefault()
    e.stopPropagation()
  }

  if (e.key === 'Escape') {
    close()
    return
  }

  // Focus trap for TAB: Keep focus on the container
  if (e.key === 'Tab') {
    calculatorRef.value?.focus()
    return
  }
  
  if (e.key === 'F12') return 

  if (/[0-9.]/.test(e.key)) handleInput({ label: e.key, type: 'number' })
  if (['+', '-', '*', '/', '%'].includes(e.key)) handleInput({ label: e.key, type: 'operator' })
  if (e.key === 'Enter') handleInput({ label: '=', type: 'operator' })
  if (e.key === 'Backspace') {
    if (display.value === '') handleInput({ label: 'C', type: 'action' })
    else handleInput({ label: 'DEL', type: 'action' })
  }
  if (e.key === 'Delete' || e.key.toLowerCase() === 'c') handleInput({ label: 'C', type: 'action' })
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown, true) // Capture phase
  if (props.show) nextTick(() => calculatorRef.value?.focus())
})
onUnmounted(() => window.removeEventListener('keydown', handleKeydown, true))
</script>
