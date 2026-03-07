<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/20 backdrop-blur-[1px]">
    <div class="w-40 rounded-2xl bg-white p-6 shadow-2xl border-2 border-blue-500 animate-in zoom-in duration-100">
      <div class="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2 text-center">Go to Row</div>
      <div class="text-6xl font-black text-blue-600 text-center tabular-nums">
        {{ rowInput }}
      </div>
      <div class="mt-4 flex justify-center gap-2 text-[10px] font-medium text-gray-400">
        <span><kbd class="rounded border px-1 bg-gray-50">Enter</kbd> Jump</span>
        <span><kbd class="rounded border px-1 bg-gray-50">Esc</kbd> Cancel</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean,
  maxRows: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['jump', 'update:show'])

const rowInput = ref('')

function handleGlobalKeydown(e) {
  // 1. If modal is already open
  if (props.show) {
    if (e.key >= '0' && e.key <= '9') {
      e.preventDefault()
      e.stopPropagation()
      rowInput.value += e.key
      return
    }
    if (e.key === 'Backspace') {
      e.preventDefault()
      e.stopPropagation()
      rowInput.value = rowInput.value.slice(0, -1)
      if (rowInput.value === '') close()
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      e.stopPropagation()
      const target = parseInt(rowInput.value)
      if (!isNaN(target)) {
        emit('jump', target)
      }
      close()
      return
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      e.stopPropagation()
      close()
      return
    }
    // Block other keys when modal is open
    if (e.key.length === 1 || e.key === 'Tab') {
      e.preventDefault()
      e.stopPropagation()
    }
    return
  }

  // 2. If modal is NOT open, check if we should open it
  const active = document.activeElement
  const isInputFocused = active && (
    active.tagName === 'INPUT' || 
    active.tagName === 'TEXTAREA' || 
    active.tagName === 'SELECT' || 
    active.isContentEditable
  )

  if (!isInputFocused && e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.altKey && !e.metaKey) {
    e.preventDefault()
    e.stopPropagation()
    rowInput.value = e.key
    emit('update:show', true)
  }
}

function close() {
  emit('update:show', false)
  rowInput.value = ''
}

onMounted(() => {
  // Use capture=true to ensure JumpToRowModal catches keys BEFORE the focused elements
  window.addEventListener('keydown', handleGlobalKeydown, true)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown, true)
})
</script>

<style scoped>
kbd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>
