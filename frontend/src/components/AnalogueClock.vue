<template>
  <div class="relative flex items-center justify-center h-48 w-48 rounded-full border-4 border-slate-700 bg-[#F5F5DC] shadow-2xl overflow-hidden">
    <!-- Subtle Inner Shadow Overlay -->
    <div class="absolute inset-0 rounded-full shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)] pointer-events-none"></div>

    <svg viewBox="0 0 100 100" class="h-full w-full">
      <!-- Hour markers (Standard Numbers) -->
      <g v-for="n in 12" :key="n">
        <text
          x="50"
          y="18"
          text-anchor="middle"
          class="text-[9px] font-sans font-bold fill-black select-none"
          :transform="`rotate(${ n * 30} 50 50)`"
        >
          <tspan :transform="`rotate(${ -n * 30} 50 15)`">{{ n }}</tspan>
        </text>
      </g>

      <!-- Brand/Logo Text -->
      <text
        x="50"
        y="40"
        text-anchor="middle"
        class="text-[7px] font-sans font-black fill-slate-800 select-none tracking-widest"
      >
        CTR
      </text>
      
      <!-- Minute markers (ticks) -->
      <line v-for="n in 60" :key="'m'+n" 
        x1="50" y1="5" x2="50" y2="7" 
        stroke="black" stroke-width="0.5" 
        :transform="`rotate(${n * 6} 50 50)`" 
      />

      <!-- Hour hand -->
      <line x1="50" y1="50" x2="50" y2="30" 
        stroke="black" stroke-width="3" stroke-linecap="round"
        :transform="`rotate(${hourDeg} 50 50)`" 
      />
      
      <!-- Minute hand -->
      <line x1="50" y1="50" x2="50" y2="15" 
        stroke="black" stroke-width="2" stroke-linecap="round"
        :transform="`rotate(${minuteDeg} 50 50)`" 
      />
      
      <!-- Second hand -->
      <line x1="50" y1="50" x2="50" y2="10" 
        stroke="#DC2626" stroke-width="1" stroke-linecap="round"
        :transform="`rotate(${secondDeg} 50 50)`" 
      />

      <!-- Center dot -->
      <circle cx="50" cy="50" r="2.5" fill="black" />
      <circle cx="50" cy="50" r="1" fill="#F5F5DC" />
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
