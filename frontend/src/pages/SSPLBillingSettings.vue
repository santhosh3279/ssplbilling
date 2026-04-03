<template>
  <div class="flex h-screen flex-col bg-slate-900">
    <header class="shrink-0 flex items-center gap-4 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <button 
        class="rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-400 hover:bg-slate-700 hover:text-white transition-colors" 
        @click="router.push('/')"
      >
        &larr; Dashboard
      </button>
      <div>
        <h1 class="text-lg font-bold text-white uppercase tracking-wider">SSPL Billing Settings</h1>
        <p class="text-[10px] text-slate-400 uppercase tracking-widest font-medium">System Configuration</p>
      </div>
    </header>
    <main class="flex-1 overflow-hidden bg-white">
      <iframe src="/app/sspl-billing-settings" class="h-full w-full border-0"></iframe>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
