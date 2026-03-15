<template>
  <div class="flex min-h-screen flex-col bg-slate-900">

    <!-- Top Bar -->
    <header class="sticky top-0 z-40 border-b border-slate-700 bg-slate-800 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <!-- Back -->
          <button
            class="rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-600"
            @click="router.push('/')"
          >
            ← Dashboard
          </button>

          <h1 class="text-lg font-bold text-white">Cahier</h1>
        </div>

        <!-- Cashier Opening button + BOX Cash label -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2 rounded-xl border border-slate-600 bg-slate-700 px-4 py-2">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">BOX Cash</span>
            <span class="font-mono text-sm font-bold text-emerald-400">
              {{ boxCashTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </span>
          </div>
          <button
            class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 active:scale-95 transition"
            @click="showBoxCash = true"
          >
            💰 Cashier Opening
          </button>
        </div>
      </div>
    </header>

    <!-- Main content placeholder -->
    <main class="flex flex-1 items-center justify-center">
      <div class="text-center text-slate-600 text-sm">Page content coming soon</div>
    </main>

    <!-- BOX Cash Subwindow -->
    <BoxCashSubwindow
      v-if="showBoxCash"
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
