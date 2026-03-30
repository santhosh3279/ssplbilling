<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
    @click.self="close"
  >
    <div
      class="w-80 overflow-hidden rounded-3xl border border-slate-700 bg-slate-900 shadow-2xl"
      @keydown.esc="close"
    >
      <!-- Display -->
      <div class="p-6 bg-slate-800/50">
        <div class="text-right text-xs font-bold text-slate-500 uppercase tracking-widest mb-1 h-4">
          {{ prevInput }} {{ operator }}
        </div>
        <div class="text-right text-4xl font-black text-white font-mono truncate">
          {{ display || '0' }}
        </div>
      </div>

      <!-- Buttons Grid -->
      <div class="grid grid-cols-4 gap-px bg-slate-800 p-1">
        <button
          v-for="btn in buttons"
          :key="btn.label"
          @click="handleInput(btn)"
          class="h-16 text-xl font-bold transition-all active:scale-95"
          :class="[
            btn.type === 'operator' ? 'bg-slate-800 text-blue-400 hover:bg-slate-700' :
            btn.type === 'action' ? 'bg-slate-800 text-rose-400 hover:bg-slate-700' :
            'bg-slate-900 text-slate-200 hover:bg-slate-800'
          ]"
        >
          {{ btn.label }}
        </button>
      </div>

      <div class="p-4 bg-slate-900 text-center">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
          Press <kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-300">ESC</kbd> to Close
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean
})
const emit = defineEmits(['close'])

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

function handleKeydown(e) {
  if (!props.show) return
  
  // Always prevent default/stop propagation for these keys when calculator is open
  const interceptedKeys = ['Escape', 'Backspace', 'Enter', 'Delete', 'c', 'C', 'F12', '+', '-', '*', '/', '%']
  if (interceptedKeys.includes(e.key) || /[0-9.]/.test(e.key)) {
    e.preventDefault()
    e.stopPropagation()
  }

  if (e.key === 'Escape') {
    close()
    return
  }
  
  if (e.key === 'F12') return // Just consume it so it doesn't leak

  if (/[0-9.]/.test(e.key)) handleInput({ label: e.key, type: 'number' })
  if (['+', '-', '*', '/', '%'].includes(e.key)) handleInput({ label: e.key, type: 'operator' })
  if (e.key === 'Enter') handleInput({ label: '=', type: 'operator' })
  if (e.key === 'Backspace') {
    if (display.value === '') handleInput({ label: 'C', type: 'action' })
    else handleInput({ label: 'DEL', type: 'action' })
  }
  if (e.key === 'Delete' || e.key === 'c' || e.key === 'C') handleInput({ label: 'C', type: 'action' })
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>
