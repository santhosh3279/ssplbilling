<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm">
    <div 
      class="w-[500px] overflow-hidden rounded-2xl bg-[var(--color-bg)] border shadow-2xl"
      :class="type === 'success' ? 'border-[var(--color-success)]/50' : 'border-[var(--color-danger)]/50'"
    >
      <div 
        class="px-6 py-4 border-b flex items-center justify-between"
        :class="type === 'success' ? 'bg-[var(--color-success)]/20 border-[var(--color-success)]/30' : 'bg-[var(--color-danger)]/20 border-[var(--color-danger)]/30'"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl">{{ type === 'success' ? '✅' : '⚠️' }}</span>
          <h2 
            class="text-xl font-bold uppercase tracking-wider"
            :class="type === 'success' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
          >
            {{ type === 'success' ? 'Success' : title }}
          </h2>
        </div>
        <button @click="$emit('close')" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-2xl font-bold">&times;</button>
      </div>
      
      <div class="p-6">
        <div class="bg-[var(--color-bg)] rounded-lg p-4 border border-[var(--color-border)] max-h-[300px] overflow-y-auto scrollbar-none mb-4">
          <p class="text-[var(--color-text)] font-mono text-sm whitespace-pre-wrap leading-relaxed">{{ message }}</p>
        </div>
        
        <div class="flex justify-end gap-3">
          <button 
            @click="copyError" 
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-2 text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-all active:scale-95"
          >
            <span v-if="copied" class="text-[var(--color-success)]">Copied!</span>
            <span v-else>Copy {{ type === 'success' ? 'Message' : 'Error' }}</span>
          </button>
          <button 
            ref="dismissButton"
            @click="$emit('close')" 
            class="rounded-xl px-8 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-md transition-all active:scale-95"
            :class="type === 'success' ? 'bg-[var(--color-success)] hover:bg-[var(--color-success)]/90' : 'bg-[var(--color-danger)] hover:bg-[var(--color-danger)]/90'"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  message: { type: String, default: '' },
  title: { type: String, default: 'Error Occurred' },
  type: { type: String, default: 'error' } // 'error' | 'success'
})

const emit = defineEmits(['close'])

const copied = ref(false)
const dismissButton = ref(null)

watch(() => props.show, (newVal) => {
  if (newVal) {
    nextTick(() => {
      dismissButton.value?.focus()
    })
  }
})

async function copyError() {
  try {
    await navigator.clipboard.writeText(props.message)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy text: ', err)
  }
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
