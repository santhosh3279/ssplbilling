<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @keydown.esc="$emit('close')"
    @keydown.left.prevent="focusBtn('no')"
    @keydown.right.prevent="focusBtn('yes')"
  >
    <div class="w-[450px] rounded-2xl border border-slate-700 bg-slate-900 p-8 shadow-2xl">
      <div class="mb-6 flex flex-col items-center text-center">
        <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-900/30 text-4xl text-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
          ⚠️
        </div>
        <h3 class="text-2xl font-bold text-slate-100">{{ title }}</h3>
        <p class="mt-2 text-lg text-slate-400 leading-relaxed">{{ message }}</p>
      </div>

      <div class="flex gap-4">
        <button
          ref="noBtn"
          class="flex-1 rounded-xl border border-slate-700 bg-slate-800 py-3 text-xl font-bold text-slate-300 transition-all hover:bg-slate-700 focus:border-blue-500 focus:bg-slate-700 focus:ring-4 focus:ring-blue-500/20"
          @click="$emit('close')"
        >
          No (Esc)
        </button>
        <button
          ref="yesBtn"
          class="flex-1 rounded-xl bg-red-600 py-3 text-xl font-bold text-white transition-all hover:bg-red-700 focus:ring-4 focus:ring-red-500/20 shadow-lg shadow-red-900/20"
          @click="$emit('confirm')"
        >
          Yes
        </button>
      </div>
      
      <div class="mt-6 text-center text-[10px] uppercase tracking-widest text-slate-600 font-bold">
        Use <kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-500">← →</kbd> to toggle
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Confirm Action' },
  message: { type: String, default: 'Are you sure you want to proceed?' }
})

const emit = defineEmits(['close', 'confirm'])

const noBtn = ref(null)
const yesBtn = ref(null)

function focusBtn(type) {
  if (type === 'no') noBtn.value?.focus()
  else yesBtn.value?.focus()
}

watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      noBtn.value?.focus()
    })
  }
})
</script>
