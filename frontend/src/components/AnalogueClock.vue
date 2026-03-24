<template>
  <div class="relative flex items-center justify-center h-48 w-48 rounded-full border-4 border-slate-600 bg-slate-800 shadow-2xl">
    <svg viewBox="0 0 100 100" class="h-full w-full">
      <!-- Outer circle -->
      <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="2" class="text-slate-700" />
      
      <!-- Hour markers -->
      <line v-for="n in 12" :key="'h'+n" 
        x1="50" y1="10" x2="50" y2="15" 
        stroke="currentColor" stroke-width="2" 
        class="text-slate-500"
        :transform="`rotate(${n * 30} 50 50)`" 
      />

      <!-- Hour hand -->
      <line x1="50" y1="50" x2="50" y2="28" 
        stroke="currentColor" stroke-width="4" stroke-linecap="round"
        class="text-slate-300"
        :transform="`rotate(${hourDeg} 50 50)`" 
      />
      
      <!-- Minute hand -->
      <line x1="50" y1="50" x2="50" y2="20" 
        stroke="currentColor" stroke-width="3" stroke-linecap="round"
        class="text-slate-400"
        :transform="`rotate(${minuteDeg} 50 50)`" 
      />
      
      <!-- Second hand -->
      <line x1="50" y1="50" x2="50" y2="15" 
        stroke="currentColor" stroke-width="1.5" stroke-linecap="round"
        class="text-red-500"
        :transform="`rotate(${secondDeg} 50 50)`" 
      />

      <!-- Center dot -->
      <circle cx="50" cy="50" r="3" fill="currentColor" class="text-slate-300" />
    </svg>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const hourDeg = ref(0)
const minuteDeg = ref(0)
const secondDeg = ref(0)
let timer = null

function updateClock() {
  const now = new Date()
  const seconds = now.getSeconds()
  const minutes = now.getMinutes()
  const hours = now.getHours()

  secondDeg.value = seconds * 6
  minuteDeg.value = minutes * 6 + seconds * 0.1
  hourDeg.value = (hours % 12) * 30 + minutes * 0.5
  
  timer = requestAnimationFrame(updateClock)
}

onMounted(() => {
  updateClock()
})

onUnmounted(() => {
  if (timer) cancelAnimationFrame(timer)
})
</script>
