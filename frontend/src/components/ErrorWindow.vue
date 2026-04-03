<template>
  <div v-if="show" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm">
    <div class="w-[500px] overflow-hidden rounded-2xl bg-slate-900 border border-red-900/50 shadow-2xl">
      <div class="bg-red-900/20 px-6 py-4 border-b border-red-900/30 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">⚠️</span>
          <h2 class="text-xl font-bold text-red-400 uppercase tracking-wider">Error Occurred</h2>
        </div>
        <button @click="$emit('close')" class="text-slate-500 hover:text-slate-300 text-2xl font-bold">&times;</button>
      </div>
      
      <div class="p-6">
        <div class="bg-slate-950 rounded-lg p-4 border border-slate-800 max-h-[300px] overflow-y-auto scrollbar-none mb-4">
          <p class="text-slate-300 font-mono text-sm whitespace-pre-wrap leading-relaxed">{{ message }}</p>
        </div>
        
        <div class="flex justify-end gap-3">
          <button 
            @click="copyError" 
            class="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-5 py-2 text-sm font-bold text-slate-300 hover:bg-slate-700 transition-all active:scale-95"
          >
            <span v-if="copied" class="text-green-400">Copied!</span>
            <span v-else>Copy Error</span>
          </button>
          <button 
            @click="$emit('close')" 
            class="rounded-xl bg-red-600 px-8 py-2 text-sm font-bold text-white hover:bg-red-700 shadow-md transition-all active:scale-95"
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
