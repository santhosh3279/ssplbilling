<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm">
    <div class="w-[500px] overflow-hidden rounded-2xl bg-[var(--color-bg)] border border-[var(--color-danger)]/50 shadow-2xl">
      <div class="bg-[var(--color-danger)]/20 px-6 py-4 border-b border-[var(--color-danger)]/30 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">⚠️</span>
          <h2 class="text-xl font-bold text-[var(--color-danger)] uppercase tracking-wider">Error Occurred</h2>
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
            <span v-else>Copy Error</span>
          </button>
          <button 
            @click="$emit('close')" 
            class="rounded-xl bg-[var(--color-danger)] px-8 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-danger)] shadow-md transition-all active:scale-95"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  show: Boolean,
  message: { type: String, default: '' }
})

const emit = defineEmits(['close'])

const copied = ref(false)

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
