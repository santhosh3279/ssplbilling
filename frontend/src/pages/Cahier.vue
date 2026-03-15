<template>
  <div class="relative min-h-screen bg-slate-900 text-slate-200 font-sans overflow-x-hidden">

    <!-- TOP NAVIGATION BAR -->
    <nav class="fixed top-0 left-0 right-0 z-50 flex h-20 items-center justify-between border-b border-slate-800 bg-slate-900/80 px-8 backdrop-blur-xl">
      <div class="flex items-center gap-8">
        <!-- Back Button -->
        <button
          class="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-bold text-slate-300 transition hover:bg-slate-700 hover:text-white active:scale-95 shadow-lg"
          @click="router.push('/')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Dashboard
        </button>

        <div class="h-8 w-px bg-slate-800"></div>

        <!-- Page Title -->
        <h1 class="text-xl font-black tracking-tighter text-white uppercase">
          Cahier <span class="text-slate-500 font-light">Management</span>
        </h1>
      </div>

      <!-- System Status -->
      <div class="flex items-center gap-3 rounded-full bg-slate-800/50 border border-slate-700 px-4 py-2 shadow-inner">
        <div class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
        <span class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">System Online</span>
      </div>
    </nav>

    <!-- FLOATING ACTION ROW (BELOW NAV) -->
    <div class="absolute top-28 left-8 z-40 flex gap-4 w-[600px]">
      <!-- BOX Cash Widget -->
      <div class="group flex-1 overflow-hidden rounded-2xl border border-slate-700 bg-slate-800/40 p-1 backdrop-blur-sm shadow-2xl transition-all hover:border-emerald-500/30">
        <div class="flex h-full items-center gap-4 rounded-xl bg-slate-900/60 px-5 py-4">
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500 shadow-inner">
            <span class="text-2xl font-black">₹</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-0.5">BOX Cash Total</div>
            <div class="font-mono text-2xl font-black text-emerald-400 truncate leading-none">
              {{ boxCashTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Cashier Opening Action -->
      <button
        class="group relative flex-1 flex items-center justify-between overflow-hidden rounded-2xl bg-blue-600 px-6 py-5 text-left text-white shadow-2xl shadow-blue-900/40 transition-all hover:bg-blue-500 active:scale-[0.98]"
        @click="showBoxCash = true"
      >
        <div class="relative z-10">
          <div class="text-[10px] font-bold uppercase tracking-widest text-blue-200 opacity-70 mb-1">Session Action</div>
          <div class="text-lg font-black tracking-tight">Cashier Opening</div>
        </div>
        <div class="relative z-10 flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 text-2xl shadow-lg transition-transform group-hover:scale-110 group-hover:rotate-12">
          💰
        </div>
        <!-- Decorative Glow -->
        <div class="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/10 blur-2xl transition-all group-hover:bg-white/20"></div>
      </button>
    </div>

    <!-- Main Content Area -->
    <div class="flex min-h-screen flex-col pt-60">
      <!-- Main content placeholder -->
      <main class="flex-1 overflow-y-auto p-10 custom-scrollbar">
        <div class="mx-auto max-w-5xl">
          <div class="relative flex flex-col items-center justify-center rounded-[2.5rem] border-2 border-dashed border-slate-800 bg-slate-800/20 py-32 text-center transition-colors hover:border-slate-700">
            <div class="mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-slate-800 text-4xl shadow-2xl">
              📂
            </div>
            <h2 class="text-2xl font-black text-slate-200">Session Logs & History</h2>
            <p class="mt-3 text-base text-slate-500 max-w-md mx-auto leading-relaxed">
              Your reconciliation history, cashier logs, and daily summaries will be displayed here as they are generated.
            </p>
            <button class="mt-8 rounded-xl bg-slate-700 px-6 py-3 text-sm font-black text-slate-300 uppercase tracking-widest hover:bg-slate-600 transition-all active:scale-95 shadow-lg">
              Refresh History
            </button>
          </div>
        </div>
      </main>
      
      <!-- Footer Info -->
      <footer class="p-10 text-right">
        <span class="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-700">Sundaram & Sons • ssplbilling v1.0</span>
      </footer>
    </div>

    <!-- BOX Cash Subwindow -->
    <BoxCashSubwindow
      v-if="showBoxCash"
      title="Cashier Opening Entry"
      @close="showBoxCash = false"
      @saved="onBoxCashSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import BoxCashSubwindow from '../components/Cahier_Entry.vue'

const router = useRouter()
const showBoxCash = ref(false)
const boxCashTotal = ref(Number(localStorage.getItem('opening_cash') || 0))

onMounted(async () => {
  const today = new Date().toLocaleDateString('en-CA')
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_opening_total', { 
      date: today
    })
    const total = res.total || 0
    boxCashTotal.value = total
    localStorage.setItem('opening_cash', String(total))
  } catch (e) {
    console.warn('[Cahier] Failed to fetch opening total:', e)
  }
})

function onBoxCashSaved(data) {
  boxCashTotal.value = data.total
  localStorage.setItem('opening_cash', String(data.total))
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #1e293b;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
