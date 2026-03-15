<template>
  <div class="flex min-h-screen bg-slate-900">

    <!-- Sidebar (Navigation + BOX Cash) -->
    <aside class="flex w-64 shrink-0 flex-col border-r border-slate-700 bg-slate-800">
      <!-- Top Bar / Navigation Panel -->
      <div class="border-b border-slate-700 px-4 py-4">
        <button
          class="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:bg-slate-600 active:scale-95"
          @click="router.push('/')"
        >
          ← Dashboard
        </button>
      </div>

      <!-- Left end of screen below navigation panel -->
      <div class="flex-1 space-y-6 px-4 py-6">
        <!-- BOX Cash Display -->
        <div class="space-y-1.5">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-500 px-1">BOX Cash Total</label>
          <div class="flex items-center gap-3 rounded-xl border border-slate-600 bg-slate-900/50 px-4 py-4 shadow-inner">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
              <span class="text-xl font-bold">₹</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="font-mono text-xl font-black text-emerald-400 truncate">
                {{ boxCashTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </div>
              <div class="text-[10px] text-slate-500 font-bold uppercase tracking-tight">Current Balance</div>
            </div>
          </div>
        </div>

        <!-- Cashier Opening Button -->
        <button
          class="group flex w-full items-center justify-between rounded-xl bg-blue-600 p-4 text-left text-white shadow-lg shadow-blue-900/20 transition-all hover:bg-blue-700 active:scale-[0.98]"
          @click="showBoxCash = true"
        >
          <div>
            <div class="text-[10px] font-bold uppercase tracking-widest text-blue-200 opacity-80 mb-0.5">Operation</div>
            <div class="text-base font-bold">Cashier Opening</div>
          </div>
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-white/20 text-xl transition-transform group-hover:scale-110">
            💰
          </div>
        </button>
      </div>

      <!-- Version/Footer (optional) -->
      <div class="p-4 text-center">
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-600">SSPL Billing v1.0</div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Header / Title Bar -->
      <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-8 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-black tracking-tight text-white uppercase">Cahier Management</h1>
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Session</span>
          </div>
        </div>
      </header>

      <!-- Main content placeholder -->
      <main class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div class="mx-auto max-w-5xl">
          <div class="rounded-2xl border border-dashed border-slate-700 bg-slate-800/50 p-20 text-center">
            <div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-700 text-3xl text-slate-500">
              📂
            </div>
            <h2 class="text-lg font-bold text-slate-300">Cahier Ledger & Logs</h2>
            <p class="mt-2 text-sm text-slate-500 max-w-sm mx-auto">
              History of cashier openings, closings, and mid-day reconciliations will appear here.
            </p>
            <button class="mt-6 rounded-lg bg-slate-700 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-600 transition-colors">
              Refresh Logs
            </button>
          </div>
        </div>
      </main>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BoxCashSubwindow from '../components/Cahier_Entry.vue'

const router = useRouter()
const showBoxCash = ref(false)
const boxCashTotal = ref(0)

function onBoxCashSaved(data) {
  boxCashTotal.value = data.total
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
