<template>
  <div class="relative min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] font-sans">

    <!-- TOP NAVIGATION BAR -->
    <nav class="fixed top-0 left-0 right-0 z-50 flex h-20 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg)]/80 px-8 backdrop-blur-xl">
      <div class="flex items-center gap-8">
        <!-- Back Button -->
        <button
          class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-xs font-bold text-[var(--color-text)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] active:scale-95 shadow-lg"
          @click="router.push('/')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Dashboard
        </button>

        <div class="h-8 w-px bg-[var(--color-surface)]"></div>

        <!-- Page Title -->
        <h1 class="text-xl font-black tracking-tighter uppercase">
          <span class="text-[var(--color-success)]">Cashier</span> <span class="text-[var(--color-text-muted)] font-light">Management</span>
        </h1>
      </div>

      <!-- Date Navigation -->
      <div class="flex items-center gap-1.5">
        <button @click="shiftDate(-1)"
          class="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="flex flex-col items-center rounded-xl border px-6 py-2 min-w-[280px]"
             :class="isToday ? 'border-[var(--color-success)]/50 bg-[var(--color-success)]/20' : 'border-[var(--color-warning)]/50 bg-[var(--color-warning)]/20'">
          <div class="text-lg font-black uppercase tracking-[0.2em]"
               :class="isToday ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'">
            {{ isToday ? 'Today' : 'Past Date' }}
          </div>
          <div class="font-mono text-2xl font-black text-[var(--color-text)] leading-tight">{{ formatDateDisplay(currentDate) }}</div>
        </div>
        <button @click="shiftDate(1)" :disabled="isToday"
          class="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
        </button>
        <button v-if="!isToday" @click="currentDate = new Date().toLocaleDateString('en-CA')"
          class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]">
          Today
        </button>
      </div>

      <!-- Today's Sales Summary -->
      <div class="flex items-center gap-3">
        <div class="flex flex-col items-end rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-4 py-2 shadow-inner">
          <div class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Sales</div>
          <div class="font-mono text-xl font-black text-[var(--color-success)] leading-none">
            {{ totalSales.toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
          </div>
        </div>
        <div class="flex flex-col items-end rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-4 py-2 shadow-inner">
          <div class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Bills</div>
          <div class="font-mono text-xl font-black text-[var(--color-text)] leading-none">{{ filteredBills.length }}</div>
        </div>
      </div>

      <!-- Live Ledger Closing Balance -->
      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-5 py-2.5 shadow-inner backdrop-blur-sm">
          <div class="flex items-center gap-2 mb-0.5">
            <div class="h-1.5 w-1.5 rounded-full" :class="[liveLedgerLoading ? 'bg-[var(--color-warning)] animate-pulse' : 'bg-[var(--color-success)]', !isToday ? 'animate-none' : 'animate-pulse']"></div>
            <span class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
              {{ isToday ? 'Live Cash Ledger' : 'Date Closing Balance' }}
            </span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="font-mono text-2xl font-black leading-none"
                  :class="liveLedgerBalance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              {{ liveLedgerLoading ? '…' : Math.abs(liveLedgerBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </span>
            <span v-if="!liveLedgerLoading" class="text-xs font-black"
                  :class="liveLedgerBalance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
              {{ liveLedgerBalance >= 0 ? 'DR' : 'CR' }}
            </span>
          </div>
          <div class="text-[9px] text-[var(--color-text-muted)] font-mono mt-0.5 truncate max-w-[200px]">{{ liveLedgerAccount || '—' }}</div>
        </div>
        <button
          @click="refreshLiveLedger"
          :disabled="liveLedgerLoading"
          class="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] disabled:opacity-40"
          title="Refresh ledger balance"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="liveLedgerLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
      </div>
    </nav>

    <!-- LAYOUT: left 25% panel = BOX Cash table + UPI stacked -->
    <div class="flex gap-4 p-4 mt-20 overflow-x-auto" style="min-height: calc(100vh - 5rem);">

      <!-- LEFT 40%: BOX Cash compact table + UPI below -->
      <div class="flex flex-col gap-3 overflow-y-auto custom-scrollbar min-w-0" style="width: 40%; flex-shrink: 0;">

      <!-- BOX Cash table card -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 shadow-2xl flex-shrink-0">
        <!-- Table header -->
        <div class="bg-[var(--color-bg)]/80 px-3 py-2 border-b border-[var(--color-border)]">
          <div class="text-sm font-black uppercase tracking-widest text-[var(--color-text-muted)]">BOX Cash — Daily Summary</div>
        </div>
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full" style="font-size: 1.1rem;">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-xs font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="w-px whitespace-nowrap px-3 py-2 text-left">Session</th>
                <th class="px-2 py-2 text-right">BOX</th>
                <th class="px-2 py-2 text-right">Ledger</th>
                <th class="px-2 py-2 text-right">Diff</th>
                <th class="px-2 py-2 text-center">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]/50">

              <!-- Opening row -->
              <tr class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="w-px whitespace-nowrap px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-[var(--color-info)] flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-[var(--color-text)] leading-tight">Opening</div>
                      <button @click="openModal('Cashier Opening')"
                        class="text-xs text-[var(--color-info)] hover:text-[var(--color-info)] font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-[var(--color-success)]">
                  {{ openingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="openingLedger >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(openingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ openingLedger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(openingTotal-openingLedger)===0 ? 'text-[var(--color-text-muted)]' : (openingTotal-openingLedger)>0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ (openingTotal-openingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center">
                  <button v-if="(openingTotal-openingLedger)!==0" @click="openContra('Opening', openingTotal-openingLedger)"
                    class="rounded bg-[var(--color-warning)]/20 border border-[var(--color-warning)]/40 px-2 py-0.5 text-xs font-black text-[var(--color-warning)] hover:bg-[var(--color-warning)]/30 transition whitespace-nowrap">
                    Contra
                  </button>
                </td>
              </tr>

              <!-- Mid-Day-1 row -->
              <tr class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="w-px whitespace-nowrap px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-[var(--color-info)] flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-[var(--color-text)] leading-tight">Mid-Day-1</div>
                      <button @click="openModal('Mid-Day-1')"
                        class="text-xs text-[var(--color-info)] hover:text-[var(--color-info)] font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-[var(--color-success)]">
                  {{ md1Total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="md1Ledger >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(md1Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ md1Ledger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(md1Total-md1Ledger)===0 ? 'text-[var(--color-text-muted)]' : (md1Total-md1Ledger)>0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ (md1Total-md1Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-[var(--color-text-muted)]">—</td>
              </tr>

              <!-- Mid-Day-2 row -->
              <tr class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="w-px whitespace-nowrap px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-[var(--color-info)] flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-[var(--color-text)] leading-tight">Mid-Day-2</div>
                      <button @click="openModal('Mid-Day-2')"
                        class="text-xs text-[var(--color-info)] hover:text-[var(--color-info)] font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-[var(--color-success)]">
                  {{ md2Total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="md2Ledger >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(md2Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ md2Ledger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(md2Total-md2Ledger)===0 ? 'text-[var(--color-text-muted)]' : (md2Total-md2Ledger)>0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ (md2Total-md2Ledger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-[var(--color-text-muted)]">—</td>
              </tr>

              <!-- Closing row -->
              <tr class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="w-px whitespace-nowrap px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-[var(--color-danger)] flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-[var(--color-text)] leading-tight">Closing</div>
                      <button @click="openModal('Closing')"
                        class="text-xs text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold">+ Record</button>
                    </div>
                  </div>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-[var(--color-success)]">
                  {{ closingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black" :class="closingLedger >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(closingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-xs ml-1">{{ closingLedger >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="(closingTotal-closingLedger)===0 ? 'text-[var(--color-text-muted)]' : (closingTotal-closingLedger)>0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ (closingTotal-closingLedger).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center">
                  <template v-if="(closingTotal-closingLedger)!==0">
                    <span v-if="Math.abs(liveLedgerBalance-closingTotal)<0.01"
                      class="inline-flex items-center rounded bg-[var(--color-success)]/20 border border-[var(--color-success)]/40 px-2 py-0.5 text-xs font-black text-[var(--color-success)] whitespace-nowrap">
                      ✓ Adjusted
                    </span>
                    <button v-else @click="openContra('Closing', closingTotal-closingLedger)"
                      class="rounded bg-[var(--color-warning)]/20 border border-[var(--color-warning)]/40 px-2 py-0.5 text-xs font-black text-[var(--color-warning)] hover:bg-[var(--color-warning)]/30 transition whitespace-nowrap">
                      Contra
                    </button>
                  </template>
                </td>
              </tr>

              <!-- UPI row — separator + teal accent -->
              <tr class="border-t-2 border-[var(--color-success)]/40 bg-[var(--color-success)]/10 hover:bg-[var(--color-success)]/20 transition">
                <td class="w-px whitespace-nowrap px-3 py-3">
                  <div class="flex items-center gap-2">
                    <span class="h-3 w-3 rounded-full bg-[var(--color-success)] flex-shrink-0"></span>
                    <div>
                      <div class="font-black text-[var(--color-success)] leading-tight">UPI</div>
                      <button @click="refreshUpi" :disabled="upiLoading"
                        class="text-xs text-[var(--color-success)] hover:text-[var(--color-success)] font-bold disabled:opacity-40">↺ Refresh</button>
                    </div>
                  </div>
                </td>
                <!-- Opening -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-[var(--color-text-muted)]' : (upiOpening >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
                  <div class="text-xs font-black text-[var(--color-text-muted)] mb-0.5">Opening</div>
                  {{ upiLoading ? '…' : Math.abs(upiOpening).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span v-if="!upiLoading" class="text-xs ml-1">{{ upiOpening >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <!-- Closing -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-[var(--color-text-muted)]' : (upiClosing >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
                  <div class="text-xs font-black text-[var(--color-text-muted)] mb-0.5">Closing</div>
                  {{ upiLoading ? '…' : Math.abs(upiClosing).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span v-if="!upiLoading" class="text-xs ml-1">{{ upiClosing >= 0 ? 'DR' : 'CR' }}</span>
                </td>
                <!-- Day's UPI -->
                <td class="px-2 py-3 text-right font-mono font-black"
                    :class="upiLoading ? 'text-[var(--color-text-muted)]' : (upiDiff===0 ? 'text-[var(--color-text-muted)]' : upiDiff>0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]')">
                  <div class="text-xs font-black text-[var(--color-text-muted)] mb-0.5">Day's UPI</div>
                  {{ upiLoading ? '…' : upiDiff.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
                <td class="px-2 py-3 text-center text-[var(--color-text-muted)]">—</td>
              </tr>

            </tbody>
          </table>
        </div>
      </div>
      <!-- end BOX Cash table card -->

      <!-- Export Button -->
      <button @click="exportToExcel"
        class="flex items-center justify-center gap-2 rounded-xl border border-[var(--color-success)]/50 bg-[var(--color-success)]/20 px-4 py-3 text-xs font-black uppercase tracking-widest text-[var(--color-success)] transition hover:bg-[var(--color-success)]/40 active:scale-95 disabled:opacity-30 disabled:grayscale shadow-lg shadow-emerald-900/20">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Export Daily Cashier Report
      </button>

      </div>
      <!-- end left panel -->

      <!-- SECOND 30%: Today's Bills table -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 shadow-2xl min-w-0" style="width: 30%; flex-shrink: 0;">
        <!-- Header -->
        <div class="flex items-center justify-between bg-[var(--color-bg)]/80 px-4 py-3 border-b border-[var(--color-border)] flex-shrink-0">
          <div>
            <div class="text-lg font-black uppercase tracking-widest text-[var(--color-text-muted)]">Today's Bills</div>
            <div class="text-base text-[var(--color-text-muted)] font-mono">
              {{ filteredBills.length }}{{ filteredBills.length !== todayBills.length ? '/' + todayBills.length : '' }} invoices
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <!-- Series filter button -->
            <div class="relative">
              <button @click="showSeriesFilter = !showSeriesFilter"
                :class="['flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-black uppercase tracking-widest transition',
                  selectedSeries.length ? 'border-[var(--color-info)]/60 bg-[var(--color-info)]/10 text-[var(--color-info)]' : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]']">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                Series{{ selectedSeries.length ? ` (${selectedSeries.length})` : '' }}
              </button>
              <!-- Dropdown -->
              <div v-if="showSeriesFilter"
                class="absolute right-0 top-full mt-1 z-30 min-w-[140px] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden">
                <div class="px-2 py-1.5 border-b border-[var(--color-border)] flex items-center justify-between">
                  <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Filter Series</span>
                  <button @click="selectedSeries = []; showSeriesFilter = false"
                    class="text-[9px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] font-bold">Clear</button>
                </div>
                <div v-if="availableSeries.length === 0" class="px-3 py-2 text-[10px] text-[var(--color-text-muted)]">No series found</div>
                <label v-for="s in availableSeries" :key="s"
                  class="flex items-center gap-2 px-3 py-2 text-xs text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/50 cursor-pointer transition">
                  <input type="checkbox" :value="s" v-model="selectedSeries"
                    class="rounded accent-[var(--color-info)] w-3 h-3 cursor-pointer" />
                  <span class="font-mono text-[10px]">{{ s }}</span>
                </label>
              </div>
            </div>
            <button @click="fetchTodayBills" :disabled="billsLoading"
              class="flex items-center justify-center h-8 w-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition disabled:opacity-40">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="billsLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>
        <!-- Table -->
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full text-xl">
            <thead class="sticky top-0 bg-[var(--color-bg)]/95 z-10">
              <tr class="border-b border-[var(--color-border)] text-base font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-3 py-3 text-left">Bill</th>
                <th class="px-2 py-3 text-right text-[var(--color-success)]">Cash</th>
                <th class="px-2 py-3 text-right text-[var(--color-success)]">UPI</th>
                <th class="px-2 py-3 text-right text-[var(--color-info)]">Card</th>
                <th class="px-2 py-3 text-right text-[var(--color-warning)]">Disc</th>
                <th class="px-2 py-3 text-right text-[var(--color-text-muted)]">Unpaid</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]/40">
              <tr v-if="billsLoading">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">Loading…</td>
              </tr>
              <tr v-else-if="filteredBills.length === 0">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">No bills today</td>
              </tr>
              <tr v-for="bill in filteredBills" :key="bill.name" class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="px-3 py-2.5">
                  <div class="font-black text-[var(--color-text)] text-xl leading-tight">{{ bill.name }}</div>
                  <div class="text-base text-[var(--color-text-muted)] truncate max-w-[120px]">{{ bill.customer }}</div>
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="getMopAmount(bill, 'cash') > 0 ? 'text-[var(--color-success)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ getMopAmount(bill, 'cash') > 0 ? getMopAmount(bill, 'cash').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="getMopAmount(bill, 'upi') > 0 ? 'text-[var(--color-success)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ getMopAmount(bill, 'upi') > 0 ? getMopAmount(bill, 'upi').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="getMopAmount(bill, 'card') > 0 ? 'text-[var(--color-info)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ getMopAmount(bill, 'card') > 0 ? getMopAmount(bill, 'card').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="getMopAmount(bill, 'discount') > 0 ? 'text-[var(--color-warning)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ getMopAmount(bill, 'discount') > 0 ? getMopAmount(bill, 'discount').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="getMopAmount(bill, 'credit') > 0 ? 'text-[var(--color-text)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ getMopAmount(bill, 'credit') > 0 ? getMopAmount(bill, 'credit').toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
              </tr>
            </tbody>
            <!-- Totals row -->
            <tfoot v-if="filteredBills.length > 0" class="sticky bottom-0 bg-[var(--color-bg)]/95 border-t border-[var(--color-border)]">
              <tr class="text-base font-black uppercase">
                <td class="px-3 py-2.5 text-[var(--color-text-muted)]">Total</td>
                <td class="px-2 py-2.5 text-right font-mono text-[var(--color-success)] text-xl">
                  {{ billTotals.cash > 0 ? billTotals.cash.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-[var(--color-success)] text-xl">
                  {{ billTotals.upi > 0 ? billTotals.upi.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-[var(--color-info)] text-xl">
                  {{ billTotals.card > 0 ? billTotals.card.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-[var(--color-warning)] text-xl">
                  {{ billTotals.discount > 0 ? billTotals.discount.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-[var(--color-text)] text-xl">
                  {{ billTotals.credit > 0 ? billTotals.credit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- THIRD 30%: Cash Ledger for today -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 shadow-2xl min-w-0" style="width: 30%; flex-shrink: 0;">
        <!-- Header -->
        <div class="flex items-center justify-between bg-[var(--color-bg)]/80 px-4 py-3 border-b border-[var(--color-border)] flex-shrink-0">
          <div>
            <div class="text-lg font-black uppercase tracking-widest text-[var(--color-text-muted)]">Cash Ledger</div>
            <div class="text-base text-[var(--color-text-muted)] font-mono truncate max-w-[200px]">{{ localStorage.getItem('wb-cash') || '—' }}</div>
          </div>
          <button @click="fetchCashLedgerEntries" :disabled="cashLedgerEntriesLoading"
            class="flex items-center justify-center h-8 w-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition disabled:opacity-40">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="cashLedgerEntriesLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          </button>
        </div>
        <!-- Table -->
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full text-xl">
            <thead class="sticky top-0 bg-[var(--color-bg)]/95 z-10">
              <tr class="border-b border-[var(--color-border)] text-base font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-3 py-3 text-left">Time</th>
                <th class="px-2 py-3 text-left">Voucher</th>
                <th class="px-2 py-3 text-right text-[var(--color-success)]">DR</th>
                <th class="px-2 py-3 text-right text-[var(--color-danger)]">CR</th>
                <th class="px-2 py-3 text-right">Balance</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]/40">
              <!-- Opening balance row -->
              <tr class="bg-[var(--color-bg)]/40">
                <td class="px-3 py-2.5 text-sm text-[var(--color-text-muted)]">—</td>
                <td colspan="2" class="px-2 py-2.5 text-base font-black text-[var(--color-text-muted)] uppercase tracking-widest">Opening</td>
                <td class="px-2 py-2.5"></td>
                <td class="px-2 py-2.5 text-right font-mono font-black text-xl"
                    :class="cashLedgerOpening >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(cashLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-sm ml-1">{{ cashLedgerOpening >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
              <tr v-if="cashLedgerEntriesLoading">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">Loading…</td>
              </tr>
              <tr v-else-if="cashLedgerEntries.length === 0 && !cashLedgerEntriesLoading">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">No entries today</td>
              </tr>
              <tr v-for="entry in cashLedgerEntries" :key="entry.voucher_no + entry.debit + entry.credit"
                  class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="px-3 py-2.5 font-mono text-base text-[var(--color-text-muted)] whitespace-nowrap">{{ entry.time }}</td>
                <td class="px-2 py-2.5">
                  <div class="font-black text-[var(--color-text)] text-base leading-tight truncate max-w-[120px]">{{ entry.voucher_no }}</div>
                  <div v-if="entry.party" class="text-sm text-[var(--color-text-muted)] truncate max-w-[120px]">{{ entry.party }}</div>
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="entry.debit > 0 ? 'text-[var(--color-success)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ entry.debit > 0 ? entry.debit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="entry.credit > 0 ? 'text-[var(--color-danger)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ entry.credit > 0 ? entry.credit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono font-black text-xl"
                    :class="entry.balance >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(entry.balance).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-sm ml-1">{{ entry.balance >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
            </tbody>
            <!-- Closing balance row -->
            <tfoot v-if="cashLedgerEntries.length > 0" class="sticky bottom-0 bg-[var(--color-bg)]/95 border-t border-[var(--color-border)]">
              <tr>
                <td colspan="2" class="px-3 py-3 text-base font-black uppercase tracking-widest text-[var(--color-text-muted)]">Closing</td>
                <td class="px-2 py-3 text-right font-mono text-xl text-[var(--color-success)] font-black">
                  {{ cashLedgerEntries.reduce((s, e) => s + e.debit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono text-xl text-[var(--color-danger)] font-black">
                  {{ cashLedgerEntries.reduce((s, e) => s + e.credit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-xl"
                    :class="(cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening) >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-sm ml-1">{{ (cashLedgerEntries.at(-1)?.balance ?? cashLedgerOpening) >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- FOURTH 30%: UPI Ledger for today -->
      <div class="flex flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 shadow-2xl min-w-0" style="width: 30%; flex-shrink: 0;">
        <!-- Header -->
        <div class="flex items-center justify-between bg-[var(--color-bg)]/80 px-4 py-3 border-b border-[var(--color-border)] flex-shrink-0">
          <div>
            <div class="text-lg font-black uppercase tracking-widest text-[var(--color-text-muted)]">UPI Ledger</div>
            <div class="text-base text-[var(--color-text-muted)] font-mono truncate max-w-[200px]">{{ localStorage.getItem('wb-upi') || '—' }}</div>
          </div>
          <button @click="fetchUpiLedgerEntries" :disabled="upiLedgerLoading"
            class="flex items-center justify-center h-8 w-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition disabled:opacity-40">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :class="upiLedgerLoading ? 'animate-spin' : ''"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          </button>
        </div>
        <!-- Table -->
        <div class="overflow-y-auto custom-scrollbar flex-1">
          <table class="w-full text-xl">
            <thead class="sticky top-0 bg-[var(--color-bg)]/95 z-10">
              <tr class="border-b border-[var(--color-border)] text-base font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                <th class="px-3 py-3 text-left">Time</th>
                <th class="px-2 py-3 text-left">Voucher</th>
                <th class="px-2 py-3 text-right text-[var(--color-success)]">DR</th>
                <th class="px-2 py-3 text-right text-[var(--color-danger)]">CR</th>
                <th class="px-2 py-3 text-right">Balance</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]/40">
              <!-- Opening balance row -->
              <tr class="bg-[var(--color-bg)]/40">
                <td class="px-3 py-2.5 text-sm text-[var(--color-text-muted)]">—</td>
                <td colspan="2" class="px-2 py-2.5 text-base font-black text-[var(--color-text-muted)] uppercase tracking-widest">Opening</td>
                <td class="px-2 py-2.5"></td>
                <td class="px-2 py-2.5 text-right font-mono font-black text-xl"
                    :class="upiLedgerOpening >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(upiLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                  <span class="text-sm ml-1">{{ upiLedgerOpening >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
              <tr v-if="upiLedgerLoading">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">Loading…</td>
              </tr>
              <tr v-else-if="upiLedgerEntries.length === 0 && !upiLedgerLoading">
                <td colspan="5" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">No entries today</td>
              </tr>
              <tr v-for="entry in upiLedgerEntries" :key="entry.voucher_no + entry.debit + entry.credit"
                  class="hover:bg-[var(--color-surface-raised)]/20 transition">
                <td class="px-3 py-2.5 font-mono text-base text-[var(--color-text-muted)] whitespace-nowrap">{{ entry.time }}</td>
                <td class="px-2 py-2.5">
                  <div class="font-black text-[var(--color-text)] text-base leading-tight truncate max-w-[120px]">{{ entry.voucher_no }}</div>
                  <div v-if="entry.party" class="text-sm text-[var(--color-text-muted)] truncate max-w-[120px]">{{ entry.party }}</div>
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="entry.debit > 0 ? 'text-[var(--color-success)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ entry.debit > 0 ? entry.debit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono text-xl"
                    :class="entry.credit > 0 ? 'text-[var(--color-danger)] font-black' : 'text-[var(--color-text-muted)]'">
                  {{ entry.credit > 0 ? entry.credit.toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '—' }}
                </td>
                <td class="px-2 py-2.5 text-right font-mono font-black text-xl"
                    :class="entry.balance >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(entry.balance).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-sm ml-1">{{ entry.balance >= 0 ? 'DR' : 'CR' }}</span>
                </td>
              </tr>
            </tbody>
            <!-- Closing balance row -->
            <tfoot v-if="upiLedgerEntries.length > 0" class="sticky bottom-0 bg-[var(--color-bg)]/95 border-t border-[var(--color-border)]">
              <tr>
                <td colspan="2" class="px-3 py-3 text-base font-black uppercase tracking-widest text-[var(--color-text-muted)]">Closing</td>
                <td class="px-2 py-3 text-right font-mono text-xl text-[var(--color-success)] font-black">
                  {{ upiLedgerEntries.reduce((s, e) => s + e.debit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono text-xl text-[var(--color-danger)] font-black">
                  {{ upiLedgerEntries.reduce((s, e) => s + e.credit, 0).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                </td>
                <td class="px-2 py-3 text-right font-mono font-black text-xl"
                    :class="(upiLedgerEntries.at(-1)?.balance ?? upiLedgerOpening) >= 0 ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                  {{ Math.abs(upiLedgerEntries.at(-1)?.balance ?? upiLedgerOpening).toLocaleString('en-IN', { minimumFractionDigits: 0 }) }}
                  <span class="text-sm ml-1">{{ (upiLedgerEntries.at(-1)?.balance ?? upiLedgerOpening) >= 0 ? 'DR' : 'CR' }}</span>
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
        class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[70] flex items-center gap-3 rounded-2xl bg-[var(--color-success)] border border-[var(--color-success)] px-6 py-4 shadow-2xl shadow-emerald-900/50"
      >
        <span class="text-xl">✅</span>
        <span class="text-sm font-bold text-[var(--color-text)]">{{ contraSuccessMsg }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { session } from '../session.js'
import BoxCashSubwindow from '../components/CashierEntry.vue'
import CahierContraModal from '../components/CashierContraModal.vue'

import { generateCashierReport } from '../services/cashierReportExport.js'

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
    const params = { account }
    if (!isToday.value) {
      const d = new Date(currentDate.value + 'T00:00:00')
      d.setDate(d.getDate() + 1)
      params.date = d.toLocaleDateString('en-CA')
    }
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', params)
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

const upiLedgerEntries = ref([])
const upiLedgerOpening = ref(0)
const upiLedgerLoading = ref(false)

async function fetchUpiLedgerEntries() {
  let account = localStorage.getItem('wb-upi') || ''
  if (!account) return
  if (!account.includes(' - ')) {
    try {
      const res = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: JSON.stringify({ account_name: account, is_group: 0 }),
        fields: ['name'], limit_page_length: 1,
      })
      if (res?.[0]?.name) { account = res[0].name; localStorage.setItem('wb-upi', account) }
    } catch {}
  }
  upiLedgerLoading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_entries', { account, date: currentDate.value })
    upiLedgerOpening.value = res.opening ?? 0
    upiLedgerEntries.value = res.entries ?? []
  } catch (e) {
    console.warn('[Cahier] fetchUpiLedgerEntries failed:', e)
  } finally {
    upiLedgerLoading.value = false
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
  const t = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0 }
  for (const bill of filteredBills.value) {
    t.cash      += getMopAmount(bill, 'cash')
    t.upi       += getMopAmount(bill, 'upi')
    t.card      += getMopAmount(bill, 'card')
    t.discount  += getMopAmount(bill, 'discount')
    t.credit    += getMopAmount(bill, 'credit')
  }
  return t
})

const totalSales = computed(() =>
  filteredBills.value.reduce((s, b) => s + b.grand_total, 0)
)

function getMopAmount(bill, type) {
  const pay = bill.pay || {}
  const lower = Object.fromEntries(Object.entries(pay).map(([k, v]) => [k.toLowerCase(), v]))
  if (type === 'cash')      return Object.entries(lower).filter(([k]) => k.includes('cash') && !k.includes('upi')).reduce((s, [, v]) => s + v, 0)
  if (type === 'upi')       return Object.entries(lower).filter(([k]) => k.includes('upi')).reduce((s, [, v]) => s + v, 0)
  if (type === 'card')      return Object.entries(lower).filter(([k]) => k.includes('card') || k.includes('debit')).reduce((s, [, v]) => s + v, 0)
  if (type === 'discount')  return Object.entries(lower).filter(([k]) => k.includes('discount')).reduce((s, [, v]) => s + v, 0)
  if (type === 'credit')    return bill.outstanding_amount > 0.01 ? bill.outstanding_amount : 0
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

  // Ensure latest ledger entries are fetched
  await Promise.all([fetchCashLedgerEntries(), fetchUpiLedgerEntries()])

  generateCashierReport({
    date: currentDate.value,
    docs,
    bills: filteredBills.value,
    ledgerEntries: cashLedgerEntries.value,
    ledgerOpening: cashLedgerOpening.value,
    upiLedgerEntries: upiLedgerEntries.value,
    upiLedgerOpening: upiLedgerOpening.value,
    metadata: {
      billerName: session.fullName.value || session.user.value || '',
      warehouse: localStorage.getItem('wb-warehouse') || '',
      cashAccount: localStorage.getItem('wb-cash') || '',
      upiAccount: localStorage.getItem('wb-upi') || '',
      costCenter: localStorage.getItem('wb-cost-center') || ''
    },
    getMopAmount
  })
}

onMounted(async () => {
  await Promise.all([refreshAll(), refreshLiveLedger(), refreshUpi(), fetchTodayBills(), fetchCashLedgerEntries(), fetchUpiLedgerEntries()])
})

watch(currentDate, async () => {
  selectedSeries.value = []
  await Promise.all([refreshAll(), refreshLiveLedger(), refreshUpi(), fetchTodayBills(), fetchCashLedgerEntries(), fetchUpiLedgerEntries()])
})

function openModal(title) {
  modalTitle.value = title
  showBoxCash.value = true
}

async function refreshAll() {
  const today = currentDate.value
  const account = localStorage.getItem('wb-cash') || ''

  // Fetch Opening
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Opening', account
    })
    openingTotal.value = res.total || 0
    openingLedger.value = res.cash_ledger_balance || 0
    localStorage.setItem('opening_cash', String(openingTotal.value))
    localStorage.setItem('wb-opening-box-cash', String(openingTotal.value))
    localStorage.setItem('cash_ledger_balance', String(openingLedger.value))
  } catch (e) { console.warn('[Cahier] Opening fetch failed:', e) }

  // Fetch Mid-Day-1
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Mid-Day-1', account
    })
    md1Total.value = res.total || 0
    md1Ledger.value = res.cash_ledger_balance || 0
    localStorage.setItem('md1_cash', String(md1Total.value))
    localStorage.setItem('md1_ledger_balance', String(md1Ledger.value))
  } catch (e) { console.warn('[Cahier] Mid-Day-1 fetch failed:', e) }

  // Fetch Mid-Day-2
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Mid-Day-2', account
    })
    md2Total.value = res.total || 0
    md2Ledger.value = res.cash_ledger_balance || 0
    localStorage.setItem('md2_cash', String(md2Total.value))
    localStorage.setItem('md2_ledger_balance', String(md2Ledger.value))
  } catch (e) { console.warn('[Cahier] Mid-Day-2 fetch failed:', e) }

  // Fetch Closing
  try {
    const res = await frappeGet('ssplbilling.api.cahierlog_api.get_cahier_totals', {
      date: today, op_type: 'Closing', account
    })
    closingTotal.value = res.total || 0
    if (!isToday.value) {
      const d = new Date(today + 'T00:00:00')
      d.setDate(d.getDate() + 1)
      const balanceRes = await frappeGet('ssplbilling.api.cahierlog_api.get_cash_ledger_balance', { 
        account, date: d.toLocaleDateString('en-CA') 
      })
      closingLedger.value = balanceRes.balance || 0
    } else {
      closingLedger.value = res.cash_ledger_balance || 0
    }
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
