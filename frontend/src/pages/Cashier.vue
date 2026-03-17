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
        <h1 class="text-xl font-black tracking-tighter uppercase">
          <span class="text-emerald-400">Cashier</span> <span class="text-slate-500 font-light">Management</span>
        </h1>
      </div>

      <!-- Date Navigation -->
      <div class="flex items-center gap-1.5">
        <button @click="shiftDate(-1)"
          class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-400 transition hover:bg-slate-700 hover:text-white active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="flex flex-col items-center rounded-xl border px-4 py-1.5 min-w-[160px]"
             :class="isToday ? 'border-emerald-700/50 bg-emerald-900/20' : 'border-amber-700/50 bg-amber-900/20'">
          <div class="text-[9px] font-black uppercase tracking-[0.2em]"
               :class="isToday ? 'text-emerald-600' : 'text-amber-600'">
            {{ isToday ? 'Today' : 'Past Date' }}
          </div>
          <div class="font-mono text-xs font-black text-white leading-tight">{{ formatDateDisplay(currentDate) }}</div>
        </div>
        <button @click="shiftDate(1)" :disabled="isToday"
          class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-400 transition hover:bg-slate-700 hover:text-white active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </button>
        <button v-if="!isToday" @click="currentDate = new Date().toLocaleDateString('en-CA')"
          class="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-slate-400 transition hover:bg-slate-700 hover:text-white">
          Today
        </button>
      </div>

      <!-- Today's Sales Summary -->
      <div class="flex items-center gap-3">
        <div class="flex flex-col items-end rounded-2xl border border-slate-700 bg-slate-800/60 px-4 py-2 shadow-inner">
          <div class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Total Sales</div>
          <div class="font-mono text-xl font-black text-emerald-400 leading-none">
            {{ totalSales.toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
          </div>
        </div>
        <div class="flex flex-col items-end rounded-2xl border border-slate-700 bg-slate-800/60 px-4 py-2 shadow-inner">
          <div class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Bills</div>
          <div class="font-mono text-xl font-black text-white leading-none">{{ filteredBills.length }}</div>
        </div>
      </div>

      <!-- Live Ledger Closing Balance -->
      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end rounded-2xl border border-slate-700 bg-slate-800/60 px-5 py-2.5 shadow-inner backdrop-blur-sm">
          <div class="flex items-center gap-2 mb-0.5">
            <div class="h-1.5 w-1.5 rounded-full animate-pulse" :class="liveLedgerLoading ? 'bg-amber-500' : 'bg-emerald-500'"></div>
            <span class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Live Cash Ledger</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="font-mono text-2xl font-black leading-none"
                  :class="liveLedgerBalance >= 0 ? 'text-emerald-400' : 'text-red-400'">
              {{ liveLedgerLoading ? '…' : Math.abs(liveLedgerBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </span>
            <span v-if="!liveLedgerLoading" class="text-xs font-black"
                  :class="liveLedgerBalance >= 0 ? 'text-emerald-600' : 'text-red-600'">
              {{ liveLedgerBalance >= 0 ? 'DR' : 'CR' }}
            </span>
          </div>
          <div class="text-[9px] text-slate-600 font-mono mt-0.5 truncate max-w-[200px]">{{ liveLedgerAccount || '—' }}</div>
        </div>
        <button
          @click="refreshLiveLedger"
          :disabled="liveLedgerLoading"
          class="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-700 bg-slate-800 text-slate-400 transition hover:bg-slate-700 hover:text-white disabled:opacity-40"
          title="Refresh ledger balance"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="liveLedgerLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
      </div>
    </nav>

    <!-- LAYOUT: left 25% panel = BOX Cash table + UPI stacked -->
    <div class="flex gap-4 p-4 mt-20" style="height: calc(100vh - 5rem);">

      <!-- LEFT 40%: BOX Cash compact table + UPI below -->
      <div class="flex flex-col gap-3 overflow-y-auto custom-scrollbar min-w-0" style="width: 40%; flex-shrink: 0;">

      <!-- BOX Cash table card -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-800/60 shadow-2xl flex-shrink-0">
        <!-- Table header -->
        <div class="bg-slate-900/80 px-3 py-2 border-b border-slate-700">
          <div class="text-sm font-black uppercase tracking-widest text-slate-400">BOX Cash — Daily Summary</div>
        </div>
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full" style="font-size: 1.1rem;">
            <thead>
              <tr class="border-b border-slate-700 text-xs font-black uppercase tracking-widest text-slate-500">
                <th class="px-3 py-2 text-left">Session</th>
                <th class="px-2 py-2 text-right">BOX</th>
                <th class="px-2 py-2 text-right">Ledger</th>
                <th class="px-2 py-2 text-right">Diff</th>
                <th class="px-2 py-2 text-center">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">

              <!-- Opening row -->
              <tr class="hover:bg-slate-700/20 transition">
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-blue-500 flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-white leading-tight">Opening</div>
                      <button @click="openModal('Cashier Opening')"
                        class="text-xs text-blue-400 hover:text-blue-300 font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-emerald-400">
                  {{ openingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="openingLedger >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(openingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ openingLedger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(openingTotal-openingLedger)===0 ? 'text-slate-500' : (openingTotal-openingLedger)>0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ (openingTotal-openingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center">
                  <button v-if="(openingTotal-openingLedger)!==0" @click="openContra('Opening', openingTotal-openingLedger)"
                    class="rounded bg-amber-500/20 border border-amber-500/40 px-2 py-0.5 text-xs font-black text-amber-400 hover:bg-amber-500/30 transition whitespace-nowrap">
                    Contra
                  </button>
                </td>
              </tr>

              <!-- Mid-Day-1 row -->
              <tr class="hover:bg-slate-700/20 transition">
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-indigo-500 flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-white leading-tight">Mid-Day-1</div>
                      <button @click="openModal('Mid-Day-1')"
                        class="text-xs text-indigo-400 hover:text-indigo-300 font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-emerald-400">
                  {{ md1Total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="md1Ledger >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(md1Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ md1Ledger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(md1Total-md1Ledger)===0 ? 'text-slate-500' : (md1Total-md1Ledger)>0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ (md1Total-md1Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-slate-600">—</td>
              </tr>

              <!-- Mid-Day-2 row -->
              <tr class="hover:bg-slate-700/20 transition">
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-violet-500 flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-white leading-tight">Mid-Day-2</div>
                      <button @click="openModal('Mid-Day-2')"
                        class="text-xs text-violet-400 hover:text-violet-300 font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-emerald-400">
                  {{ md2Total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="md2Ledger >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(md2Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ md2Ledger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(md2Total-md2Ledger)===0 ? 'text-slate-500' : (md2Total-md2Ledger)>0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ (md2Total-md2Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-slate-600">—</td>
              </tr>

              <!-- Closing row -->
              <tr class="hover:bg-slate-700/20 transition">
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-rose-500 flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-white leading-tight">Closing</div>
                      <button @click="openModal('Closing')"
                        class="text-xs text-rose-400 hover:text-rose-300 font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-emerald-400">
                  {{ closingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="closingLedger >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(closingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ closingLedger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(closingTotal-closingLedger)===0 ? 'text-slate-500' : (closingTotal-closingLedger)>0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ (closingTotal-closingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center">
                  <template v-if="(closingTotal-closingLedger)!==0">
                    <span v-if="Math.abs(liveLedgerBalance-closingTotal)<0.01"
                      class="inline-flex items-center rounded bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-xs font-black text-emerald-400 whitespace-nowrap">
                      ✓ Adjusted
                    </span>
                    <button v-else @click="openContra('Closing', closingTotal-closingLedger)"
                      class="rounded bg-amber-500/20 border border-amber-500/40 px-2 py-0.5 text-xs font-black text-amber-400 hover:bg-amber-500/30 transition whitespace-nowrap">
                      Contra
                    </button>
                  </template>
                </td>
              </tr>

              <!-- UPI row — separator + teal accent -->
              <tr class="border-t-2 border-teal-700/40 bg-teal-900/10 hover:bg-teal-900/20 transition">
                <td class="px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-teal-500 flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-teal-300 leading-tight">UPI</div>
                      <button @click="refreshUpi" :disabled="upiLoading"
                        class="text-xs text-teal-500 hover:text-teal-400 font-bold disabled:opacity-40">↺ Refresh</button>
                    </div>
                  </div>
                </td>
                <!-- Opening -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-slate-500' : (upiOpening >= 0 ? 'text-teal-400' : 'text-red-400')">
                  <div class="text-xs font-black text-slate-500 mb-0.5">Opening</div>
                  {{ upiLoading ? '…' : Math.abs(upiOpening).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span v-if="!upiLoading" class="text-xs ml-1">{{ upiOpening >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <!-- Closing -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-slate-500' : (upiClosing >= 0 ? 'text-emerald-400' : 'text-red-400')">
                  <div class="text-xs font-black text-slate-500 mb-0.5">Closing</div>
                  {{ upiLoading ? '…' : Math.abs(upiClosing).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span v-if="!upiLoading" class="text-xs ml-1">{{ upiClosing >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <!-- Day's UPI -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-slate-500' : (upiDiff===0 ? 'text-slate-400' : upiDiff>0 ? 'text-emerald-400' : 'text-red-400')">
                  <div class="text-xs font-black text-slate-500 mb-0.5">Day's UPI</div>
                  {{ upiLoading ? '…' : upiDiff.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-slate-700">—</td>
              </tr>

            </tbody>
          </table>
        </div>
      </div>
      <!-- end BOX Cash table card -->

      <!-- Export Button -->
      <button @click="exportToExcel"
        class="flex items-center justify-center gap-2 rounded-xl border border-emerald-700/50 bg-emerald-900/20 px-4 py-3 text-xs font-black uppercase tracking-widest text-emerald-400 transition hover:bg-emerald-900/40 active:scale-95 disabled:opacity-30 disabled:grayscale shadow-lg shadow-emerald-900/20">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Export Daily Cashier Report
      </button>

      </div>
      <!-- end left panel -->

      <!-- SECOND 30%: Today's Bills table -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-800/60 shadow-2xl min-w-0" style="width: 30%; flex-shrink: 0;">
        <!-- Header -->
        <div class="flex items-center justify-between bg-slate-900/80 px-3 py-2 border-b border-slate-700 flex-shrink-0">
          <div>
            <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Today's Bills</div>
            <div class="text-[9px] text-slate-600 font-mono">
              {{ filteredBills.length }}{{ filteredBills.length !== todayBills.length ? '/' + todayBills.length : '' }} invoices
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <!-- Series filter button -->
            <div class="relative">
              <button @click="showSeriesFilter = !showSeriesFilter"
                :class="['flex items-center gap-1 rounded-lg border px-2 py-1 text-[9px] font-black uppercase tracking-widest transition',
                  selectedSeries.length ? 'border-blue-500/60 bg-blue-500/10 text-blue-400' : 'border-slate-700 bg-slate-800 text-slate-500 hover:text-slate-300']">
                <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                Series{{ selectedSeries.length ? ` (${selectedSeries.length})` : '' }}
              </button>
              <!-- Dropdown -->
              <div v-if="showSeriesFilter"
                class="absolute right-0 top-full mt-1 z-30 min-w-[140px] rounded-xl border border-slate-600 bg-slate-800 shadow-2xl overflow-hidden">
                <div class="px-2 py-1.5 border-b border-slate-700 flex items-center justify-between">
                  <span class="text-[9px] font-black uppercase tracking-widest text-slate-500">Filter Series</span>
                  <button @click="selectedSeries = []; showSeriesFilter = false"
                    class="text-[9px] text-slate-500 hover:text-slate-300 font-bold">Clear</button>
                </div>
                <div v-if="availableSeries.length === 0" class="px-3 py-2 text-[10px] text-slate-600">No series found</div>
                <label v-for="s in availableSeries" :key="s"
                  class="flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:bg-slate-700/50 cursor-pointer transition">
                  <input type="checkbox" :value="s" v-model="selectedSeries"
                    class="rounded accent-blue-500 w-3 h-3 cursor-pointer" />
                  <span class="font-mono text-[10px]">{{ s }}</span>
                </label>
              </div>
            </div>
            <button @click="fetchTodayBills" :disabled="billsLoading"
              class="flex items-center justify-center h-6 w-6 rounded-lg border border-slate-700 bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition disabled:opacity-40">
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="billsLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>
        <!-- Table -->
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full text-xs">
            <thead class="sticky top-0 bg-slate-900/95 z-10">
              <tr class="border-b border-slate-700 text-[9px] font-black uppercase tracking-widest text-slate-500">
                <th class="px-2 py-2 text-left">Bill</th>
                <th class="px-1 py-2 text-right text-emerald-600">Cash</th>
                <th class="px-1 py-2 text-right text-teal-600">UPI</th>
                <th class="px-1 py-2 text-right text-blue-600">Card</th>
                <th class="px-1 py-2 text-right text-slate-500">Unpaid</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/40">
              <tr v-if="billsLoading">
                <td colspan="5" class="px-3 py-4 text-center text-[10px] text-slate-500">Loading…</td>
              </tr>
              <tr v-else-if="filteredBills.length === 0">
                <td colspan="5" class="px-3 py-4 text-center text-[10px] text-slate-600">No bills today</td>
              </tr>
              <tr v-for="bill in filteredBills" :key="bill.name" class="hover:bg-slate-700/20 transition">
                <td class="px-2 py-1.5">
                  <div class="font-black text-white text-[10px] leading-tight">{{ bill.name }}</div>
                  <div class="text-[9px] text-slate-500 truncate max-w-[80px]">{{ bill.customer }}</div>
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="getMopAmount(bill, 'cash') > 0 ? 'text-emerald-400 font-black' : 'text-slate-700'">
                  {{ getMopAmount(bill, 'cash') > 0 ? getMopAmount(bill, 'cash').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="getMopAmount(bill, 'upi') > 0 ? 'text-teal-400 font-black' : 'text-slate-700'">
                  {{ getMopAmount(bill, 'upi') > 0 ? getMopAmount(bill, 'upi').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="getMopAmount(bill, 'card') > 0 ? 'text-blue-400 font-black' : 'text-slate-700'">
                  {{ getMopAmount(bill, 'card') > 0 ? getMopAmount(bill, 'card').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="getMopAmount(bill, 'credit') > 0 ? 'text-slate-300 font-black' : 'text-slate-700'">
                  {{ getMopAmount(bill, 'credit') > 0 ? getMopAmount(bill, 'credit').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
              </tr>
            </tbody>
            <!-- Totals row -->
            <tfoot v-if="filteredBills.length > 0" class="sticky bottom-0 bg-slate-900/95 border-t border-slate-600">
              <tr class="text-[9px] font-black uppercase">
                <td class="px-2 py-1.5 text-slate-400">Total</td>
                <td class="px-1 py-1.5 text-right font-mono text-emerald-400">
                  {{ billTotals.cash > 0 ? billTotals.cash.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-teal-400">
                  {{ billTotals.upi > 0 ? billTotals.upi.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-blue-400">
                  {{ billTotals.card > 0 ? billTotals.card.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-slate-300">
                  {{ billTotals.credit > 0 ? billTotals.credit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- THIRD 30%: Cash Ledger for today -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-800/60 shadow-2xl min-w-0" style="width: 30%; flex-shrink: 0;">
        <!-- Header -->
        <div class="flex items-center justify-between bg-slate-900/80 px-3 py-2 border-b border-slate-700 flex-shrink-0">
          <div>
            <div class="text-[9px] font-black uppercase tracking-widest text-slate-400">Cash Ledger</div>
            <div class="text-[9px] text-slate-600 font-mono truncate max-w-[140px]">{{ localStorage.getItem('wb-cash') || '—' }}</div>
          </div>
          <button @click="fetchCashLedgerEntries" :disabled="cashLedgerEntriesLoading"
            class="flex items-center justify-center h-6 w-6 rounded-lg border border-slate-700 bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition disabled:opacity-40">
            <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="cashLedgerEntriesLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          </button>
        </div>
        <!-- Table -->
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full text-xs">
            <thead class="sticky top-0 bg-slate-900/95 z-10">
              <tr class="border-b border-slate-700 text-[9px] font-black uppercase tracking-widest text-slate-500">
                <th class="px-2 py-2 text-left">Time</th>
                <th class="px-1 py-2 text-left">Voucher</th>
                <th class="px-1 py-2 text-right text-emerald-600">DR</th>
                <th class="px-1 py-2 text-right text-red-600">CR</th>
                <th class="px-1 py-2 text-right">Balance</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/40">
              <!-- Opening balance row -->
              <tr class="bg-slate-900/40">
                <td class="px-2 py-1.5 text-[9px] text-slate-600">—</td>
                <td colspan="2" class="px-1 py-1.5 text-[9px] font-black text-slate-500 uppercase tracking-widest">Opening</td>
                <td class="px-1 py-1.5"></td>
                <td class="px-1 py-1.5 text-right font-mono font-black text-[10px]"
                    :class="cashLedgerOpening >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(cashLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-[8px]">{{ cashLedgerOpening >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
              <tr v-if="cashLedgerEntriesLoading">
                <td colspan="5" class="px-3 py-4 text-center text-[10px] text-slate-500">Loading…</td>
              </tr>
              <tr v-else-if="cashLedgerEntries.length === 0 && !cashLedgerEntriesLoading">
                <td colspan="5" class="px-3 py-4 text-center text-[10px] text-slate-600">No entries today</td>
              </tr>
              <tr v-for="entry in cashLedgerEntries" :key="entry.voucher_no + entry.debit + entry.credit"
                  class="hover:bg-slate-700/20 transition">
                <td class="px-2 py-1.5 font-mono text-[9px] text-slate-500 whitespace-nowrap">{{ entry.time }}</td>
                <td class="px-1 py-1.5">
                  <div class="font-black text-white text-[9px] leading-tight truncate max-w-[70px]">{{ entry.voucher_no }}</div>
                  <div v-if="entry.party" class="text-[8px] text-slate-500 truncate max-w-[70px]">{{ entry.party }}</div>
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="entry.debit > 0 ? 'text-emerald-400 font-black' : 'text-slate-700'">
                  {{ entry.debit > 0 ? entry.debit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px]"
                    :class="entry.credit > 0 ? 'text-red-400 font-black' : 'text-slate-700'">
                  {{ entry.credit > 0 ? entry.credit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono font-black text-[10px]"
                    :class="entry.balance >= 0 ? 'text-sky-400' : 'text-red-400'">
                  {{ Math.abs(entry.balance).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-[8px]">{{ entry.balance >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
            </tbody>
            <!-- Closing balance row -->
            <tfoot v-if="cashLedgerEntries.length > 0" class="sticky bottom-0 bg-slate-900/95 border-t border-slate-600">
              <tr>
                <td colspan="2" class="px-2 py-1.5 text-[9px] font-black uppercase tracking-widest text-slate-400">Closing</td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px] text-emerald-400 font-black">
                  {{ cashLedgerEntries.reduce((s, e) => s + e.debit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono text-[10px] text-red-400 font-black">
                  {{ cashLedgerEntries.reduce((s, e) => s + e.credit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-1 py-1.5 text-right font-mono font-black text-[10px]"
                    :class="(cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening) >= 0 ? 'text-sky-300' : 'text-red-400'">
                  {{ Math.abs(cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-[8px]">{{ (cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening) >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

    </div>

    <!-- BOX Cash Subwindow -->
    <BoxCashSubwindow
      v-if="showBoxCash"
      :title="modalTitle"
      :date="currentDate"
      :initial-ledger-balance="modalTitle === 'Cashier Opening' ? cashLedgerOpening : null"
      @close="showBoxCash = false"
      @saved="onBoxCashSaved"
    />

    <!-- Contra Modal (full-screen subwindow) -->
    <CahierContraModal
      v-if="showContraModal"
      :cash-account="localStorage.getItem('wb-cash') || ''"
      :diff="contraDiff"
      :entry-type="contraEntryType"
      @close="showContraModal = false"
      @saved="onContraSaved"
    />

    <!-- Contra Success Toast -->
    <transition name="slide-up">
      <div
        v-if="contraSuccessMsg"
        class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[70] flex items-center gap-3 rounded-2xl bg-emerald-700 border border-emerald-500 px-6 py-4 shadow-2xl shadow-emerald-900/50"
      >
        <span class="text-xl">✅</span>
        <span class="text-sm font-bold text-white">{{ contraSuccessMsg }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { session } from '../session.js'
import BoxCashSubwindow from '../components/Cahier_Entry.vue'
import CahierContraModal from '../components/CahierContraModal.vue'

const router = useRouter()
const localStorage = window.localStorage
const showBoxCash = ref(false)
const modalTitle = ref('Cashier Opening')

// ── Date navigation ───────────────────────────────────────────────────────────
const currentDate = ref(new Date().toLocaleDateString('en-CA'))
const isToday = computed(() => currentDate.value === new Date().toLocaleDateString('en-CA'))

function shiftDate(days) {
  const d = new Date(currentDate.value + 'T00:00:00')
  d.setDate(d.getDate() + days)
  currentDate.value = d.toLocaleDateString('en-CA')
}

function formatDateDisplay(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

// UPI balances
const upiOpening = ref(0)
const upiClosing = ref(0)
const upiLoading = ref(false)
const upiAccount = ref(localStorage.getItem('wb-upi') || '')
const upiDiff = computed(() => upiClosing.value - upiOpening.value)

async function refreshUpi() {
  let account = localStorage.getItem('wb-upi') || ''
  if (!account) return
  // Resolve to full GL account with company tag if needed
  if (!account.includes(' - ')) {
    try {
      const res = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify({ account_name: account, is_group: 0 }),
        fields: ['name'],
        limit_page_length: 1,
      })
      if (res?.[0]?.name) {
        account = res[0].name
        localStorage.setItem('wb-upi', account)
      }
    } catch (e) { console.warn('[Cahier] UPI account resolve failed:', e) }
  }
  upiAccount.value = account
  upiLoading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_upi_day_balances', { account, date: currentDate.value })
    upiOpening.value = res.opening ?? 0
    upiClosing.value = res.closing ?? 0
  } catch (e) {
    console.warn('[Cahier] UPI balances fetch failed:', e)
  } finally {
    upiLoading.value = false
  }
}

// Live ledger balance (top-right)
const liveLedgerBalance = ref(0)
const liveLedgerLoading = ref(false)
const liveLedgerAccount = ref('')

async function refreshLiveLedger() {
  let account = localStorage.getItem('wb-cash') || ''
  if (!account) return
  liveLedgerLoading.value = true
  try {
    // Resolve to full GL account with company tag if not already resolved
    if (!account.includes(' - ')) {
      const res = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify({ account_name: account, account_type: 'Cash', is_group: 0 }),
        fields: ['name'],
        limit_page_length: 1,
      })
      if (res?.[0]?.name) {
        account = res[0].name
        localStorage.setItem('wb-cash', account)
      }
    }
    liveLedgerAccount.value = account
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { account })
    liveLedgerBalance.value = res.balance ?? 0
  } catch (e) {
    console.warn('[Cahier] Live ledger fetch failed:', e)
  } finally {
    liveLedgerLoading.value = false
  }
}

// Contra modal state
const showContraModal = ref(false)
const contraEntryType = ref('')
const contraDiff = ref(0)
const contraSuccessMsg = ref('')

// Opening Row State
const openingTotal = ref(Number(localStorage.getItem('opening_cash') || 0))
const openingLedger = ref(Number(localStorage.getItem('cash_ledger_balance') || 0))

// Mid-Day-1 Row State
const md1Total = ref(Number(localStorage.getItem('md1_cash') || 0))
const md1Ledger = ref(Number(localStorage.getItem('md1_ledger_balance') || 0))

// Mid-Day-2 Row State
const md2Total = ref(Number(localStorage.getItem('md2_cash') || 0))
const md2Ledger = ref(Number(localStorage.getItem('md2_ledger_balance') || 0))

// Closing Row State
const closingTotal = ref(Number(localStorage.getItem('closing_cash') || 0))
const closingLedger = ref(Number(localStorage.getItem('closing_ledger_balance') || 0))


// Cash Ledger Entries
const cashLedgerEntries = ref([])
const cashLedgerOpening = ref(0)
const cashLedgerEntriesLoading = ref(false)

async function fetchCashLedgerEntries() {
  let account = localStorage.getItem('wb-cash') || ''
  if (!account) return
  if (!account.includes(' - ')) {
    try {
      const res = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify({ account_name: account, account_type: 'Cash', is_group: 0 }),
        fields: ['name'], limit_page_length: 1,
      })
      if (res?.[0]?.name) { account = res[0].name; localStorage.setItem('wb-cash', account) }
    } catch {}
  }
  cashLedgerEntriesLoading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_entries', { account, date: currentDate.value })
    cashLedgerOpening.value = res.opening ?? 0
    cashLedgerEntries.value = res.entries ?? []
  } catch (e) {
    console.warn('[Cahier] fetchCashLedgerEntries failed:', e)
  } finally {
    cashLedgerEntriesLoading.value = false
  }
}

// Today's Bills
const todayBills = ref([])
const billsLoading = ref(false)
const showSeriesFilter = ref(false)
const selectedSeries = ref([])   // empty = all

const availableSeries = computed(() => {
  const stored = localStorage.getItem('wb-allowed-series')
  if (stored) { try { return JSON.parse(stored) } catch {} }
  // Derive from bill names as fallback
  const prefixes = new Set()
  for (const bill of todayBills.value) {
    const m = bill.name.match(/^([A-Z]+-[A-Z]+-)/i)
    if (m) prefixes.add(m[1])
  }
  return [...prefixes]
})

const filteredBills = computed(() => {
  if (!selectedSeries.value.length) return todayBills.value
  return todayBills.value.filter(bill =>
    selectedSeries.value.some(s => bill.name.startsWith(s))
  )
})

const billTotals = computed(() => {
  const t = { cash: 0, upi: 0, card: 0, credit: 0 }
  for (const bill of filteredBills.value) {
    t.cash   += getMopAmount(bill, 'cash')
    t.upi    += getMopAmount(bill, 'upi')
    t.card   += getMopAmount(bill, 'card')
    t.credit += getMopAmount(bill, 'credit')
  }
  return t
})

const totalSales = computed(() =>
  filteredBills.value.reduce((s, b) => s + b.grand_total, 0)
)

function getMopAmount(bill, type) {
  const pay = bill.pay || {}
  const lower = Object.fromEntries(Object.entries(pay).map(([k, v]) => [k.toLowerCase(), v]))
  if (type === 'cash')   return Object.entries(lower).filter(([k]) => k.includes('cash') && !k.includes('upi')).reduce((s, [, v]) => s + v, 0)
  if (type === 'upi')    return Object.entries(lower).filter(([k]) => k.includes('upi')).reduce((s, [, v]) => s + v, 0)
  if (type === 'card')   return Object.entries(lower).filter(([k]) => k.includes('card') || k.includes('debit')).reduce((s, [, v]) => s + v, 0)
  if (type === 'credit') return bill.outstanding_amount > 0.01 ? bill.outstanding_amount : 0
  return 0
}

async function fetchTodayBills() {
  billsLoading.value = true
  try {
    // Gather allowed series from localStorage
    let seriesList = []
    const allowedRaw = localStorage.getItem('wb-allowed-series')
    if (allowedRaw) {
      try { seriesList = JSON.parse(allowedRaw) } catch { seriesList = [] }
    }
    if (!seriesList.length) {
      const s = localStorage.getItem('wb-series')
      if (s) seriesList = [s.split('.')[0]]  // "SSPL-SI-.YYYY.-" → "SSPL-SI-"
    }
    if (!seriesList.length) return
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_today_bills', {
      date: currentDate.value,
      series_list: JSON.stringify(seriesList),
    })
    todayBills.value = res || []
  } catch (e) {
    console.warn('[Cahier] fetchTodayBills failed:', e)
  } finally {
    billsLoading.value = false
  }
}

async function exportToExcel() {
  const types = ['Opening', 'Mid-Day-1', 'Mid-Day-2', 'Closing']
  const docs = {}
  
  await Promise.all(types.map(async t => {
    try {
      const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cashier_opening', {
        date: currentDate.value,
        user: session.user.value,
        opening_or_closing: t
      })
      docs[t] = res?.message || res
    } catch (e) { console.warn(`[Cahier] Export ${t} fetch failed:`, e) }
  }))

  const denoms = ['500', '200', '100', '50', '20', '10', '5', '2', '1']

  // ── SHEET 1: DAILY CASH SUMMARY (Side-by-Side) ───────────────────
  const billerName = session.fullName.value || session.user.value || ''
  const warehouse = localStorage.getItem('wb-warehouse') || ''
  const cashAccount = localStorage.getItem('wb-cash') || ''
  const costCenter = localStorage.getItem('wb-cost-center') || ''

  let summaryXML = `
    <Worksheet ss:Name="Daily Cash Summary">
      <Table>
        <Column ss:Width="100"/><Column ss:Width="150"/><Column ss:Width="100"/><Column ss:Width="150"/>
        
        <Row ss:Height="18">
          <Cell ss:StyleID="sLabel"><Data ss:Type="String">Biller Name:</Data></Cell>
          <Cell><Data ss:Type="String">${billerName}</Data></Cell>
          <Cell ss:StyleID="sLabel"><Data ss:Type="String">Warehouse:</Data></Cell>
          <Cell><Data ss:Type="String">${warehouse}</Data></Cell>
        </Row>
        <Row ss:Height="18">
          <Cell ss:StyleID="sLabel"><Data ss:Type="String">Cash Account:</Data></Cell>
          <Cell><Data ss:Type="String">${cashAccount}</Data></Cell>
          <Cell ss:StyleID="sLabel"><Data ss:Type="String">Cost Center:</Data></Cell>
          <Cell><Data ss:Type="String">${costCenter}</Data></Cell>
        </Row>
        <Row ss:Height="10"></Row>

        <Column ss:Width="60"/><Column ss:Width="40"/><Column ss:Width="60"/><Column ss:Width="20"/>
        <Column ss:Width="60"/><Column ss:Width="40"/><Column ss:Width="60"/><Column ss:Width="20"/>
        <Column ss:Width="60"/><Column ss:Width="40"/><Column ss:Width="60"/><Column ss:Width="20"/>
        <Column ss:Width="60"/><Column ss:Width="40"/><Column ss:Width="60"/><Column ss:Width="20"/>
        
        <Row ss:Height="20">
          ${types.map(t => `<Cell ss:MergeAcross="2" ss:StyleID="sHeader"><Data ss:Type="String">${t.toUpperCase()}</Data></Cell><Cell></Cell>`).join('')}
        </Row>
        <Row>
          ${types.map(() => `<Cell ss:StyleID="sLabel"><Data ss:Type="String">Denom</Data></Cell><Cell ss:StyleID="sLabel"><Data ss:Type="String">Count</Data></Cell><Cell ss:StyleID="sLabel"><Data ss:Type="String">Value</Data></Cell><Cell></Cell>`).join('')}
        </Row>`

  // Data Rows
  denoms.forEach(d => {
    summaryXML += `<Row>`
    types.forEach(t => {
      const doc = docs[t]
      const count = doc ? Number(doc[d] || 0) : 0
      const val = count * Number(d)
      summaryXML += `
        <Cell><Data ss:Type="Number">${d}</Data></Cell>
        <Cell><Data ss:Type="Number">${count}</Data></Cell>
        <Cell><Data ss:Type="Number">${val}</Data></Cell>
        <Cell></Cell>`
    })
    summaryXML += `</Row>`
  })

  summaryXML += `<Row ss:Height="10"></Row>` // Spacer

  // Total BOX row
  summaryXML += `<Row>
    ${types.map(t => {
      const doc = docs[t]
      return `<Cell ss:StyleID="sLabel"><Data ss:Type="String">TOTAL BOX</Data></Cell><Cell></Cell><Cell ss:StyleID="sLabel"><Data ss:Type="Number">${doc?.total || 0}</Data></Cell><Cell></Cell>`
    }).join('')}
  </Row>`

  // Ledger Balance row
  summaryXML += `<Row>
    ${types.map(t => {
      const doc = docs[t]
      return `<Cell ss:StyleID="sLabel"><Data ss:Type="String">LEDGER BAL</Data></Cell><Cell></Cell><Cell ss:StyleID="sLabel"><Data ss:Type="Number">${doc?.cash_ledger_balance || 0}</Data></Cell><Cell></Cell>`
    }).join('')}
  </Row>`

  // Difference and Status row
  summaryXML += `<Row>
    ${types.map(t => {
      const doc = docs[t]
      const diff = Number(doc?.difference || 0)
      const status = diff === 0 ? 'Tally' : (diff > 0 ? 'Excess' : 'Short')
      const style = diff >= 0 ? 'sGreen' : 'sRed'
      return `
        <Cell ss:StyleID="sLabel"><Data ss:Type="String">DIFFERENCE</Data></Cell>
        <Cell></Cell>
        <Cell ss:StyleID="${style}"><Data ss:Type="Number">${diff}</Data></Cell>
        <Cell ss:StyleID="${style}"><Data ss:Type="String">${status}</Data></Cell>`
    }).join('')}
  </Row>`

  summaryXML += `</Table></Worksheet>`

  // ── SHEET 2: TODAY'S BILLS ─────────────────────────────────
  let billsXML = `
    <Worksheet ss:Name="Today Bills">
      <Table>
        <Row ss:Height="18">
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Bill No</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Customer</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Total</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Cash</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">UPI</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Card</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Credit</Data></Cell>
        </Row>`
  filteredBills.value.forEach(bill => {
    billsXML += `<Row>
      <Cell><Data ss:Type="String">${bill.name}</Data></Cell>
      <Cell><Data ss:Type="String">${bill.customer}</Data></Cell>
      <Cell><Data ss:Type="Number">${bill.grand_total}</Data></Cell>
      <Cell><Data ss:Type="Number">${getMopAmount(bill, 'cash')}</Data></Cell>
      <Cell><Data ss:Type="Number">${getMopAmount(bill, 'upi')}</Data></Cell>
      <Cell><Data ss:Type="Number">${getMopAmount(bill, 'card')}</Data></Cell>
      <Cell><Data ss:Type="Number">${getMopAmount(bill, 'credit')}</Data></Cell>
    </Row>`
  })
  billsXML += `<Row ss:Height="18">
    <Cell ss:StyleID="sLabel"><Data ss:Type="String">TOTAL</Data></Cell>
    <Cell></Cell>
    <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${totalSales.value}</Data></Cell>
    <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${billTotals.value.cash}</Data></Cell>
    <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${billTotals.value.upi}</Data></Cell>
    <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${billTotals.value.card}</Data></Cell>
    <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${billTotals.value.credit}</Data></Cell>
  </Row>`
  billsXML += `</Table></Worksheet>`

  // ── SHEET 3: CASH LEDGER ───────────────────────────────────
  let ledgerXML = `
    <Worksheet ss:Name="Cash Ledger">
      <Table>
        <Row ss:Height="18">
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Time</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Voucher No</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Party</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Debit (DR)</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Credit (CR)</Data></Cell>
          <Cell ss:StyleID="sHeader"><Data ss:Type="String">Balance</Data></Cell>
        </Row>
        <Row>
          <Cell></Cell>
          <Cell ss:MergeAcross="3" ss:StyleID="sLabel"><Data ss:Type="String">OPENING BALANCE</Data></Cell>
          <Cell ss:StyleID="sLabel"><Data ss:Type="Number">${cashLedgerOpening.value}</Data></Cell>
        </Row>`
  cashLedgerEntries.value.forEach(entry => {
    ledgerXML += `<Row>
      <Cell><Data ss:Type="String">${entry.time}</Data></Cell>
      <Cell><Data ss:Type="String">${entry.voucher_no}</Data></Cell>
      <Cell><Data ss:Type="String">${entry.party || ''}</Data></Cell>
      <Cell><Data ss:Type="Number">${entry.debit || 0}</Data></Cell>
      <Cell><Data ss:Type="Number">${entry.credit || 0}</Data></Cell>
      <Cell><Data ss:Type="Number">${entry.balance || 0}</Data></Cell>
    </Row>`
  })
  ledgerXML += `</Table></Worksheet>`

  // Assemble the SpreadsheetML
  const finalXML = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
  <Author>Gemini CLI</Author>
  <Created>${new Date().toISOString()}</Created>
 </DocumentProperties>
 <Styles>
  <Style ss:ID="sHeader">
   <Font ss:Bold="1" ss:Size="11" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#1e293b" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
   </Borders>
  </Style>
  <Style ss:ID="sLabel">
   <Font ss:Bold="1"/>
  </Style>
  <Style ss:ID="sRed">
   <Font ss:Color="#FF0000" ss:Bold="1"/>
   <Alignment ss:Horizontal="Right"/>
  </Style>
  <Style ss:ID="sGreen">
   <Font ss:Color="#10b981" ss:Bold="1"/>
   <Alignment ss:Horizontal="Right"/>
  </Style>
 </Styles>
 ${summaryXML}
 ${billsXML}
 ${ledgerXML}
</Workbook>`

  const blob = new Blob([finalXML], { type: 'application/vnd.ms-excel' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `Cashier_Report_${currentDate.value}.xls`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

onMounted(async () => {
  await Promise.all([refreshAll(), refreshLiveLedger(), refreshUpi(), fetchTodayBills(), fetchCashLedgerEntries()])
})

watch(currentDate, async () => {
  selectedSeries.value = []
  await Promise.all([refreshAll(), refreshLiveLedger(), refreshUpi(), fetchTodayBills(), fetchCashLedgerEntries()])
})

function openModal(title) {
  modalTitle.value = title
  showBoxCash.value = true
}

async function refreshAll() {
  const today = currentDate.value

  // Fetch Opening
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Opening'
    })
    openingTotal.value = res.total || 0
    openingLedger.value = res.cash_ledger_balance || 0
    localStorage.setItem('opening_cash', String(openingTotal.value))
    localStorage.setItem('cash_ledger_balance', String(openingLedger.value))
  } catch (e) { console.warn('[Cahier] Opening fetch failed:', e) }

  // Fetch Mid-Day-1
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Mid-Day-1'
    })
    md1Total.value = res.total || 0
    md1Ledger.value = res.cash_ledger_balance || 0
    localStorage.setItem('md1_cash', String(md1Total.value))
    localStorage.setItem('md1_ledger_balance', String(md1Ledger.value))
  } catch (e) { console.warn('[Cahier] Mid-Day-1 fetch failed:', e) }

  // Fetch Mid-Day-2
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Mid-Day-2'
    })
    md2Total.value = res.total || 0
    md2Ledger.value = res.cash_ledger_balance || 0
    localStorage.setItem('md2_cash', String(md2Total.value))
    localStorage.setItem('md2_ledger_balance', String(md2Ledger.value))
  } catch (e) { console.warn('[Cahier] Mid-Day-2 fetch failed:', e) }

  // Fetch Closing
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Closing'
    })
    closingTotal.value = res.total || 0
    closingLedger.value = res.cash_ledger_balance || 0
    localStorage.setItem('closing_cash', String(closingTotal.value))
    localStorage.setItem('closing_ledger_balance', String(closingLedger.value))
  } catch (e) { console.warn('[Cahier] Closing fetch failed:', e) }

}

async function onBoxCashSaved() {
  await Promise.all([refreshAll(), refreshLiveLedger(), fetchTodayBills(), fetchCashLedgerEntries()])
}

function openContra(entryType, diff) {
  contraEntryType.value = entryType
  contraDiff.value = diff
  contraSuccessMsg.value = ''
  showContraModal.value = true
}

async function onContraSaved() {
  showContraModal.value = false
  await Promise.all([refreshAll(), refreshLiveLedger()])
  const diff = contraEntryType.value === 'Opening'
    ? openingTotal.value - openingLedger.value
    : closingTotal.value - closingLedger.value
  if (Math.abs(diff) < 0.01) {
    contraSuccessMsg.value = `${contraEntryType.value}: Short or excess is corrected with contra entry.`
    setTimeout(() => { contraSuccessMsg.value = '' }, 6000)
  }
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

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
