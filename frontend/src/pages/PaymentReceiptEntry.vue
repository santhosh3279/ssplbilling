<template>
  <div class="flex h-screen flex-col bg-gray-950 overflow-hidden">
    <!-- Header -->
    <header class="flex h-14 items-center justify-between border-b border-gray-800 bg-gray-900 px-6 shadow-lg z-20 shrink-0">
      <div class="flex items-center gap-5">
        <button @click="router.push('/')" class="flex h-9 w-9 items-center justify-center rounded-xl border border-gray-700 bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white active:scale-95 transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-black tracking-widest text-white uppercase">Payment & Receipt</h1>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex rounded-xl bg-gray-800 p-1 border border-gray-700">
          <button
            v-for="m in modes"
            :key="m.id"
            @click="switchMode(m.id)"
            class="rounded-lg px-5 py-1.5 text-xs font-black uppercase tracking-widest transition-all"
            :class="entryMode === m.id ? 'bg-blue-600 text-white shadow-md' : 'text-gray-500 hover:text-gray-300'"
          >
            {{ m.label }}
          </button>
        </div>
      </div>
    </header>

    <!-- Body: two-column split -->
    <div class="flex-1 flex overflow-hidden">

      <!-- LEFT — Invoices panel -->
      <div class="flex-1 flex flex-col border-r border-gray-800 overflow-hidden bg-gray-900">
        <!-- Panel header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800 shrink-0">
          <div>
            <div class="flex items-center gap-2">
              <p class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Outstanding Invoices</p>
              <span v-if="party" class="px-2 py-0.5 rounded-full bg-blue-950 text-blue-400 text-[10px] font-black font-mono border border-blue-900/50">
                Bal: ₹{{ ledgerBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </span>
            </div>
            <p v-if="party" class="text-sm font-black text-white mt-0.5">{{ partyName }}</p>
            <p v-else class="text-sm font-bold text-gray-600 italic mt-0.5">No party selected</p>
          </div>
          <button
            v-if="party"
            @click="showLedgerWindow = true"
            class="text-[10px] font-black text-blue-400 hover:text-blue-300 uppercase tracking-widest transition-colors"
          >
            View Ledger &rarr;
          </button>
        </div>

        <!-- Remaining amount bar (shows once amount > 0 and outstandings exist) -->
        <div v-if="amount > 0 && outstandings.length" class="shrink-0 flex items-center justify-between px-6 py-2.5 border-b border-gray-800"
          :class="remainingToAllocate < 0.01 ? 'bg-emerald-950/40' : 'bg-amber-950/30'">
          <div class="flex items-center gap-5">
            <div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600">Payment</div>
              <div class="font-mono text-sm font-black text-gray-300">₹{{ amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</div>
            </div>
            <div class="text-gray-700">−</div>
            <div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600">Allocated</div>
              <div class="font-mono text-sm font-black text-blue-400">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</div>
            </div>
            <div class="text-gray-700">=</div>
            <div>
              <div class="text-[9px] font-black uppercase tracking-widest" :class="remainingToAllocate < 0.01 ? 'text-emerald-600' : 'text-amber-600'">Remaining</div>
              <div class="font-mono text-sm font-black" :class="remainingToAllocate < 0.01 ? 'text-emerald-400' : 'text-amber-400'">
                ₹{{ remainingToAllocate.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
              </div>
            </div>
          </div>
          <div v-if="remainingToAllocate < 0.01" class="flex items-center gap-1.5 text-emerald-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span class="text-[10px] font-black uppercase tracking-widest">Fully Allocated</span>
          </div>
        </div>

        <!-- Outstanding list -->
        <div class="flex-1 overflow-y-auto custom-scrollbar px-3 py-3 space-y-1">
          <!-- Loading -->
          <div v-if="loadingOutstandings" class="flex items-center justify-center h-full">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          </div>

          <!-- Empty state -->
          <div v-else-if="!party" class="flex flex-col items-center justify-center h-full gap-3 text-center">
            <div class="h-14 w-14 rounded-2xl bg-gray-800 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-gray-600"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <p class="text-xs font-bold text-gray-600 uppercase tracking-widest">Select a party<br>to see invoices</p>
          </div>

          <div v-else-if="outstandings.length === 0" class="flex flex-col items-center justify-center h-full gap-3 text-center">
            <div class="h-14 w-14 rounded-2xl bg-gray-800 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-600"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <p class="text-xs font-bold text-gray-600 uppercase tracking-widest">No outstanding<br>invoices</p>
          </div>

          <!-- Invoice rows -->
          <template v-else>
            <!-- Column header -->
            <div class="grid grid-cols-[auto_1fr_auto_auto_auto] gap-x-3 items-center px-4 pb-1 mb-0.5">
              <div class="w-5"></div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600">Bill / Date</div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600 text-center w-14">Age</div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600 text-right">Outstanding</div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-600 text-right w-20">Payment</div>
            </div>

            <div
              v-for="inv in outstandings"
              :key="inv.name"
              class="grid grid-cols-[auto_1fr_auto_auto_auto] gap-x-3 items-center px-4 py-2.5 rounded-xl border transition-all cursor-pointer"
              :class="allocations[inv.name] > 0
                ? 'border-blue-500/30 bg-gray-800/80'
                : 'border-gray-800/60 bg-gray-800/30 hover:bg-gray-800/60 hover:border-gray-700'"
              @click="focusAllocation(inv.name)"
            >
              <!-- Checkbox -->
              <div class="shrink-0 h-4 w-4 rounded border-2 flex items-center justify-center transition-all"
                :class="allocations[inv.name] > 0 ? 'border-blue-500 bg-blue-600' : 'border-gray-700'">
                <svg v-if="allocations[inv.name] > 0" xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>

              <!-- Bill name + date -->
              <div class="min-w-0">
                <div class="font-mono text-xs font-black truncate"
                  :class="allocations[inv.name] > 0 ? 'text-blue-200' : 'text-gray-500'">
                  {{ inv.name }}
                </div>
                <div class="text-[10px] font-bold text-gray-600 mt-0.5">{{ formatDate(inv.posting_date) }}</div>
              </div>

              <!-- Age badge -->
              <div class="w-14 flex justify-center">
                <span class="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-black tabular-nums"
                  :class="getDaysOutstanding(inv.posting_date) > 60
                    ? 'bg-rose-950 text-rose-400 border border-rose-800/50'
                    : getDaysOutstanding(inv.posting_date) > 30
                      ? 'bg-amber-950 text-amber-400 border border-amber-800/50'
                      : 'bg-gray-800 text-gray-500 border border-gray-700/50'">
                  {{ getDaysOutstanding(inv.posting_date) }}d
                </span>
              </div>

              <!-- Outstanding amount -->
              <div class="text-right shrink-0">
                <div class="text-xs font-mono font-black" :class="allocations[inv.name] > 0 ? 'text-gray-400' : 'text-gray-600'">₹{{ inv.outstanding_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</div>
                <div v-if="allocations[inv.name] > 0" class="text-[10px] font-mono font-black text-blue-400 mt-0.5">
                  Final: ₹{{ (inv.outstanding_amount - Number(allocations[inv.name])).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </div>
              </div>

              <!-- Allocation input -->
              <input
                :ref="el => { if (el) allocationInputRefs[inv.name] = el }"
                type="number"
                v-model.number="allocations[inv.name]"
                @input="handleAllocationInput(inv.name, inv.outstanding_amount)"
                @focus="$event.target.select()"
                @click.stop
                @keydown.enter.prevent="navigateAllocation(inv.name, 1)"
                @keydown.down.prevent="navigateAllocation(inv.name, 1)"
                @keydown.up.prevent="navigateAllocation(inv.name, -1)"
                placeholder="0"
                class="w-20 rounded-lg border bg-gray-900 px-2 py-1.5 text-right font-mono text-xs font-black outline-none transition-all"
                :class="allocations[inv.name] > 0
                  ? 'border-blue-500/60 text-blue-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-900'
                  : 'border-gray-700 text-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-900/50'"
              />
            </div>
          </template>
        </div>

        <!-- Left footer: allocation summary -->
        <div v-if="outstandings.length" class="shrink-0 border-t border-gray-800 px-6 py-3 bg-gray-900">
          <div class="flex items-center justify-between text-xs font-black uppercase tracking-widest">
            <span class="text-gray-500">Allocated</span>
            <span class="font-mono text-blue-400">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
          </div>
          <div v-if="amount > 0" class="flex items-center justify-between text-xs font-black uppercase tracking-widest mt-1">
            <span class="text-gray-500">Unallocated</span>
            <span class="font-mono" :class="remainingToAllocate > 0 ? 'text-amber-400' : 'text-emerald-400'">
              ₹{{ remainingToAllocate.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
            </span>
          </div>
        </div>
      </div>

      <!-- RIGHT — Entry form panel -->
      <div class="w-[400px] shrink-0 flex flex-col overflow-hidden bg-gray-900">
        <div class="flex-1 overflow-y-auto custom-scrollbar px-6 py-5 space-y-4">

          <!-- Party -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">{{ activePartyType }}</label>
                <div class="flex rounded-lg bg-gray-800 p-0.5 border border-gray-700">
                  <button
                    v-for="pt in ['Customer', 'Supplier', 'Employee']"
                    :key="pt"
                    @click="setReceiptPartyType(pt)"
                    class="px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest transition-all rounded-md"
                    :class="receiptPartyType === pt ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-gray-300'"
                  >
                    {{ pt }}
                  </button>
                </div>
              </div>
            </div>
            <div
              ref="partyInput"
              class="w-full rounded-2xl border-2 px-4 py-3 text-base font-black outline-none cursor-pointer transition-all"
              :class="party
                ? 'border-blue-500/50 bg-blue-950/30 text-white'
                : 'border-gray-700 bg-gray-800 text-gray-600 italic hover:border-gray-600'"
              tabindex="0"
              @click="openSearch"
              @keydown.enter.prevent="party ? nextFocus('date') : openSearch()"
              @keydown.space.prevent="openSearch"
            >
              {{ partyName || `Select ${activePartyType.toLowerCase()}...` }}
            </div>
          </div>

          <!-- Date & Amount -->
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 ml-1">Date</label>
              <input
                ref="dateInput"
                v-model="date"
                type="date"
                class="w-full rounded-2xl border-2 border-gray-700 bg-gray-800 px-4 py-3 text-sm font-black text-gray-200 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-900 transition-all"
                @keydown.enter.prevent="nextFocus('amount')"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-[10px] font-black uppercase tracking-[0.2em] text-blue-400 ml-1">Amount (₹)</label>
              <input
                ref="amountInput"
                v-model.number="amount"
                type="number"
                class="w-full rounded-2xl border-2 border-blue-500/40 bg-blue-950/30 px-4 py-3 text-xl font-black text-blue-300 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-900 transition-all"
                placeholder="0.00"
                @focus="$event.target.select()"
                @keydown.enter.prevent="onAmountEnter"
              />
            </div>
          </div>

          <!-- Balance Summary (only if party is selected) -->
          <div v-if="party" class="flex items-center justify-between rounded-xl bg-gray-800/50 border border-gray-700/50 px-5 py-2.5 transition-all">
            <div class="space-y-1">
              <p class="text-[9px] font-black uppercase tracking-widest text-gray-500">Current Bal</p>
              <p class="font-mono text-xs font-black text-gray-200">₹{{ ledgerBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</p>
            </div>
            <div class="text-gray-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
            <div class="text-right space-y-1">
              <p class="text-[9px] font-black uppercase tracking-widest text-blue-400">New Bal</p>
              <p class="font-mono text-xs font-black text-blue-300">₹{{ newBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</p>
            </div>
          </div>

          <!-- Mode of Payment -->
          <div class="space-y-1.5">
            <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 ml-1">
              Payment Mode
              <span class="ml-1.5 font-medium normal-case text-gray-700">← →</span>
            </label>
            <div
              ref="mopZoneRef"
              tabindex="0"
              class="grid grid-cols-4 gap-2 outline-none focus:ring-2 focus:ring-blue-800 rounded-xl p-0.5"
              @keydown.left.prevent="cycleMop(-1)"
              @keydown.right.prevent="cycleMop(1)"
              @keydown.enter.prevent="nextFocus('ref')"
            >
              <button
                v-for="m in mops"
                :key="m"
                @click="selectMop(m); mopZoneRef?.focus()"
                class="rounded-xl border-2 py-2.5 text-xs font-black uppercase tracking-widest transition-all"
                :class="mop === m && !selectedLedger
                  ? 'border-blue-500 bg-blue-600 text-white'
                  : 'border-gray-700 bg-gray-800 text-gray-500 hover:border-gray-600 hover:text-gray-300'"
              >
                {{ m }}
              </button>
            </div>
          </div>

          <!-- Divider -->
          <div class="border-t border-gray-800"></div>

          <!-- Ledger Override -->
          <div class="space-y-1.5">
            <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 ml-1">
              Ledger <span class="normal-case text-gray-700 font-medium">(optional)</span>
            </label>
            <div class="relative">
              <input
                v-model="ledgerQuery"
                @input="onLedgerInput"
                @keydown.escape="closeLedgerDropdown"
                @keydown.down.prevent="ledgerHighlight = Math.min(ledgerHighlight + 1, ledgerResults.length - 1)"
                @keydown.up.prevent="ledgerHighlight = Math.max(ledgerHighlight - 1, 0)"
                @keydown.enter.prevent="pickLedger(ledgerResults[ledgerHighlight])"
                class="w-full rounded-2xl border-2 border-gray-700 bg-gray-800 px-4 py-2.5 text-sm font-black text-gray-200 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-900 transition-all"
                :placeholder="selectedLedger ? selectedLedger : 'Search account...'"
              />
              <button
                v-if="selectedLedger"
                @click="clearLedger"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-rose-400 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
              <div
                v-if="ledgerResults.length && ledgerDropdownOpen"
                class="absolute z-30 mt-1.5 w-full rounded-2xl border border-gray-700 bg-gray-900 shadow-2xl overflow-hidden"
              >
                <div
                  v-for="(acct, idx) in ledgerResults"
                  :key="acct.name"
                  @click="pickLedger(acct)"
                  @mouseenter="ledgerHighlight = idx"
                  class="cursor-pointer px-5 py-2.5 text-sm transition-colors border-b last:border-0 border-gray-800"
                  :class="idx === ledgerHighlight ? 'bg-blue-900/40 text-blue-200' : 'text-gray-300 hover:bg-gray-800'"
                >
                  <div class="font-black text-sm">{{ acct.account_name }}</div>
                  <div class="text-[10px] text-gray-600 font-bold uppercase tracking-widest">{{ acct.name }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Ref & Remarks -->
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 ml-1">Ref No.</label>
              <input
                ref="refInput"
                v-model="referenceNo"
                class="w-full rounded-2xl border-2 border-gray-700 bg-gray-800 px-4 py-2.5 text-sm font-black text-gray-200 outline-none focus:border-blue-500 transition-all"
                placeholder="Cheque / UTR"
                @keydown.enter.prevent="nextFocus('remarks')"
              />
            </div>
            <div class="space-y-1.5">
              <label class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 ml-1">Remarks</label>
              <input
                ref="remarksInput"
                v-model="remarks"
                class="w-full rounded-2xl border-2 border-gray-700 bg-gray-800 px-4 py-2.5 text-sm font-bold text-gray-200 outline-none focus:border-blue-500 transition-all"
                placeholder="Notes..."
                @keydown.enter.prevent="saveEntry"
              />
            </div>
          </div>
        </div>

        <!-- Save button pinned to bottom -->
        <div class="shrink-0 px-6 py-4 border-t border-gray-800 bg-gray-900">
          <!-- Allocation summary strip -->
          <div v-if="selectedInvoices.length" class="mb-3 flex items-center justify-between rounded-xl bg-blue-950/50 border border-blue-500/20 px-4 py-2">
            <span class="text-[10px] font-black uppercase tracking-widest text-blue-500">{{ selectedInvoices.length }} invoice{{ selectedInvoices.length > 1 ? 's' : '' }} linked</span>
            <span class="font-mono text-xs font-black text-blue-300">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span>
          </div>

          <button
            @click="saveEntry"
            :disabled="saving || !canSave"
            class="group w-full rounded-2xl py-4 font-black uppercase tracking-[0.2em] text-white transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
            :class="canSave ? 'bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-900/50' : 'bg-gray-700'"
          >
            <div v-if="saving" class="flex items-center justify-center gap-3">
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              <span>Saving...</span>
            </div>
            <div v-else class="flex items-center justify-center gap-2">
              <span>Save Entry (F9)</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- ALLOCATION MODAL (kept for keyboard shortcut / overflow use) -->
    <transition name="fade">
      <div v-if="showAllocationModal" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-md p-4">
        <div class="w-full max-w-3xl overflow-hidden rounded-[2rem] border border-gray-700 bg-gray-900 shadow-2xl flex flex-col max-h-[85vh]">
          <div class="bg-gray-800 px-8 py-5 border-b border-gray-700 flex items-center justify-between">
            <div>
              <h2 class="text-lg font-black text-white uppercase tracking-tight">Allocate Payment</h2>
              <p class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-0.5">Remaining: <span class="text-blue-400 font-mono text-xs ml-1">₹{{ remainingToAllocate.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</span></p>
            </div>
            <button @click="showAllocationModal = false" class="h-9 w-9 flex items-center justify-center rounded-full bg-gray-700 text-gray-400 hover:text-rose-400 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto custom-scrollbar">
            <table class="w-full text-left border-collapse">
              <thead class="sticky top-0 bg-gray-800 z-10">
                <tr class="text-[10px] font-black uppercase tracking-widest text-gray-500 border-b border-gray-700">
                  <th class="px-6 py-3">Bill No / Date</th>
                  <th class="px-4 py-3 text-center">Days</th>
                  <th class="px-4 py-3 text-right">Outstanding</th>
                  <th class="px-6 py-3 text-right" style="width: 160px;">This Payment</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-800">
                <tr v-for="inv in outstandings" :key="inv.name" class="hover:bg-gray-800/60 transition-colors">
                  <td class="px-6 py-3">
                    <div class="text-sm font-black text-gray-200 font-mono">{{ inv.name }}</div>
                    <div class="text-[10px] font-bold text-gray-600 mt-0.5 uppercase">{{ formatDate(inv.posting_date) }}</div>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="inline-flex rounded-lg px-2 py-0.5 text-[10px] font-black uppercase tracking-widest"
                      :class="getDaysOutstanding(inv.posting_date) > 30 ? 'bg-rose-900/50 text-rose-400' : 'bg-gray-800 text-gray-500'">
                      {{ getDaysOutstanding(inv.posting_date) }}d
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right font-mono text-sm font-bold text-gray-400">₹{{ inv.outstanding_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</td>
                  <td class="px-6 py-3 text-right">
                    <input
                      type="number"
                      v-model.number="allocations[inv.name]"
                      @input="handleAllocationInput(inv.name, inv.outstanding_amount)"
                      @focus="$event.target.select()"
                      placeholder="0.00"
                      class="w-full rounded-xl border-2 border-gray-700 bg-gray-800 px-3 py-1.5 text-right font-mono font-black text-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-900 outline-none transition-all"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="bg-gray-800 px-8 py-5 border-t border-gray-700 flex items-center justify-between">
            <div>
              <div class="text-[9px] font-black uppercase tracking-widest text-gray-500">Selected Total</div>
              <div class="text-lg font-black text-white font-mono mt-0.5">₹{{ totalAllocated.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}</div>
            </div>
            <button
              @click="finishAllocation"
              class="rounded-2xl bg-blue-600 px-8 py-3 text-sm font-black uppercase tracking-widest text-white hover:bg-blue-500 active:scale-95 transition-all"
            >
              Finish Allocation
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modals -->
    <CustomerSearchModal
      ref="searchModalRef"
      :show="showSearchModal"
      :initial-type="activePartyType"
      :allowed-types="['Customer', 'Supplier', 'Employee']"
      :skip-date-filter="true"
      @close="showSearchModal = false"
      @select="pickParty"
    />

    <CustomerLedger
      v-if="showLedgerWindow"
      :is-sub-window="true"
      :ledger-name="party"
      :ledger-type="activePartyType"
      @close="showLedgerWindow = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { frappeGet, frappePost, fetchDashboardSettings, searchAccounts } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import CustomerLedger from './CustomerLedger.vue'

const router = useRouter()
const route = useRoute()

// ─── State ───────────────────────────────────────────────────────────────────
const modes = [{ id: 'Receive', label: 'Receipt' }, { id: 'Pay', label: 'Payment' }]
const mops = ['Cash', 'Card', 'Bank', 'UPI']

const entryMode = ref(route.query.mode || 'Receive')
const date = ref(getTodayIST())
const party = ref('')
const partyName = ref('')
const ledgerBalance = ref(0)
const amount = ref(0)
const mop = ref('Cash')
const referenceNo = ref('')
const remarks = ref('')
const selectedInvoices = ref([])
const outstandings = ref([])
const allocations = ref({}) // { invoice_name: allocated_amount }

const showSearchModal = ref(false)
const showLedgerWindow = ref(false)
const showAllocationModal = ref(false)
const loadingOutstandings = ref(false)
const saving = ref(false)
const userDefaults = ref(null)

// DOM Refs
const searchModalRef = ref(null)
const partyInput = ref(null)
const dateInput = ref(null)
const amountInput = ref(null)
const mopZoneRef = ref(null)
const refInput = ref(null)
const remarksInput = ref(null)
const allocationInputRefs = ref({})

// ─── Receipt party type ──────────────────────────────────────────────────────
const receiptPartyType = ref(route.query.mode === 'Pay' ? 'Supplier' : 'Customer')
const activePartyType = computed(() => receiptPartyType.value)

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options)
  return formatter.format(date)
}

function setReceiptPartyType(pt) {
  if (receiptPartyType.value === pt) return
  receiptPartyType.value = pt
  party.value = ''; partyName.value = ''; outstandings.value = []; selectedInvoices.value = []; amount.value = 0
  nextTick(() => partyInput.value?.focus())
}

// ─── Ledger override ──────────────────────────────────────────────────────────
const ledgerQuery = ref('')
const ledgerResults = ref([])
const ledgerDropdownOpen = ref(false)
const ledgerHighlight = ref(0)
const selectedLedger = ref('')
let ledgerDebounceTimer = null

// ─── Computed ────────────────────────────────────────────────────────────────
const canSave = computed(() => party.value && amount.value > 0)

const totalAllocated = computed(() => {
  return Object.values(allocations.value).reduce((sum, val) => sum + (Number(val) || 0), 0)
})

const newBalance = computed(() => {
  // If receiving (Receipt), balance reduces (Credit to party)
  // If paying (Payment), balance increases (Debit to party)
  if (entryMode.value === 'Receive') {
    return ledgerBalance.value - (amount.value || 0)
  } else {
    return ledgerBalance.value + (amount.value || 0)
  }
})

const remainingToAllocate = computed(() => {
  return Math.max(0, amount.value - totalAllocated.value)
})

// ─── Methods ─────────────────────────────────────────────────────────────────
function switchMode(m) {
  entryMode.value = m; receiptPartyType.value = m === 'Pay' ? 'Supplier' : 'Customer'; resetForm()
  nextTick(() => partyInput.value?.focus())
}

function resetForm() {
  party.value = ''; partyName.value = ''; showSearchModal.value = false; amount.value = 0
  referenceNo.value = ''; remarks.value = ''; selectedInvoices.value = []; outstandings.value = []
  selectedLedger.value = ''; ledgerQuery.value = ''; ledgerResults.value = []; allocations.value = {}
}

async function loadUserDefaults() {
  try {
    const settings = await fetchDashboardSettings()
    if (settings?.user_defaults) userDefaults.value = settings.user_defaults
  } catch (e) { console.warn('[PaymentEntry] Failed to load user defaults:', e) }
}

const focusMap = {
  date:    () => dateInput.value?.focus(),
  amount:  () => amountInput.value?.focus(),
  mop:     () => nextTick(() => mopZoneRef.value?.focus()),
  ref:     () => refInput.value?.focus(),
  remarks: () => remarksInput.value?.focus(),
}

function nextFocus(target) { focusMap[target]?.() }

function focusAllocation(name) {
  nextTick(() => allocationInputRefs.value[name]?.focus())
}

function navigateAllocation(currentName, dir) {
  const names = outstandings.value.map(i => i.name)
  const idx = names.indexOf(currentName)
  const next = idx + dir
  if (next >= 0 && next < names.length) {
    nextTick(() => allocationInputRefs.value[names[next]]?.focus())
  } else if (next >= names.length) {
    // End of list — go to MOP
    nextFocus('mop')
  }
  // dir = -1 at first row: do nothing (stay)
}

function onAmountEnter() {
  if (amount.value <= 0) return
  if (outstandings.value.length === 0) { nextFocus('mop'); return }

  // Auto-distribute FIFO: fill invoices oldest-first up to the entered amount
  let remaining = amount.value
  const newAllocations = {}
  for (const inv of outstandings.value) {
    if (remaining <= 0) break
    const alloc = parseFloat(Math.min(remaining, inv.outstanding_amount).toFixed(2))
    newAllocations[inv.name] = alloc
    remaining = parseFloat((remaining - alloc).toFixed(2))
  }
  allocations.value = newAllocations
  selectedInvoices.value = Object.entries(newAllocations)
    .map(([name, val]) => ({ name, amount: val }))

  // Focus first allocation input
  nextTick(() => {
    const firstName = outstandings.value[0]?.name
    if (firstName) allocationInputRefs.value[firstName]?.focus()
  })
}

function handleAllocationInput(name, max) {
  const currentVal = Number(allocations.value[name]) || 0
  if (currentVal > max) allocations.value[name] = max

  const otherAllocations = Object.entries(allocations.value)
    .filter(([k]) => k !== name)
    .reduce((sum, [, v]) => sum + (Number(v) || 0), 0)

  const allowedMax = amount.value - otherAllocations
  if (allocations.value[name] > allowedMax) {
    allocations.value[name] = parseFloat(allowedMax.toFixed(2))
  }

  // Sync selectedInvoices live
  selectedInvoices.value = Object.entries(allocations.value)
    .filter(([, v]) => Number(v) > 0)
    .map(([n, val]) => ({ name: n, amount: Number(val) }))
}

function finishAllocation() {
  selectedInvoices.value = Object.entries(allocations.value)
    .filter(([, v]) => Number(v) > 0)
    .map(([name, val]) => ({ name, amount: Number(val) }))
  showAllocationModal.value = false
  nextFocus('mop')
}

function getDaysOutstanding(postDate) {
  const start = new Date(postDate)
  const today = new Date()
  return Math.max(0, Math.floor((today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)))
}

function cycleMop(dir) {
  const idx = mops.indexOf(mop.value)
  selectMop(mops[(idx + dir + mops.length) % mops.length])
}

function selectMop(m) { mop.value = m; clearLedger() }

function openSearch() {
  showSearchModal.value = true
  nextTick(() => { searchModalRef.value?.closeSubForm(); searchModalRef.value?.focus() })
}

function pickParty(p) {
  party.value = p.name; partyName.value = p.label || p.customer_name || p.supplier_name
  if (p.type === 'Customer' || p.type === 'Supplier') receiptPartyType.value = p.type
  showSearchModal.value = false; fetchOutstandings()
  nextTick(() => amountInput.value?.focus())
}

async function fetchOutstandings() {
  if (!party.value) return
  loadingOutstandings.value = true
  try {
    const res = await frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
      party: party.value, party_type: activePartyType.value
    })
    outstandings.value = res.invoices || []
    ledgerBalance.value = res.balance || 0
    allocations.value = {}
  } catch (e) { console.error(e) } finally { loadingOutstandings.value = false }
}

function removeInvoice(idx) {
  const name = selectedInvoices.value[idx].name
  delete allocations.value[name]
  selectedInvoices.value.splice(idx, 1)
}

async function saveEntry() {
  if (!canSave.value || saving.value) return
  saving.value = true
  try {
    const payload = {
      payment_type: entryMode.value,
      party_type: activePartyType.value,
      party: party.value,
      date: date.value,
      amount: amount.value,
      mode_of_payment: mop.value,
      reference_no: referenceNo.value,
      remarks: remarks.value,
      references: selectedInvoices.value,
      ...(selectedLedger.value && { paid_to: selectedLedger.value })
    }

    if (userDefaults.value) {
      const specificMop = mop.value === 'Cash' ? userDefaults.value.cash :
                          mop.value === 'Card' ? userDefaults.value.card :
                          mop.value === 'UPI'  ? userDefaults.value.upi : userDefaults.value.bank
      if (specificMop) payload.mode_of_payment = specificMop
    }

    await frappePost('ssplbilling.api.ledgerentry_api.create_payment_entry', { data: payload })
    alert('Entry saved successfully!')
    resetForm()
    nextTick(() => partyInput.value?.focus())
  } catch (e) { alert('Failed to save: ' + e.message) } finally { saving.value = false }
}

function onLedgerInput() {
  ledgerDropdownOpen.value = true; ledgerHighlight.value = 0; clearTimeout(ledgerDebounceTimer)
  ledgerDebounceTimer = setTimeout(async () => {
    if (!ledgerQuery.value.trim()) { ledgerResults.value = []; ledgerDropdownOpen.value = false; return }
    ledgerResults.value = await searchAccounts(ledgerQuery.value); ledgerDropdownOpen.value = true
  }, 250)
}

function pickLedger(acct) {
  if (!acct) return; selectedLedger.value = acct.name; mop.value = ''; ledgerQuery.value = ''
  ledgerResults.value = []; ledgerDropdownOpen.value = false
}

function clearLedger() { selectedLedger.value = ''; ledgerQuery.value = ''; ledgerResults.value = []; ledgerDropdownOpen.value = false }
function closeLedgerDropdown() { ledgerDropdownOpen.value = false }

function formatDate(dateStr) { if (!dateStr) return ''; return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }

function handleKeydown(e) {
  if (e.key === 'F9') { e.preventDefault(); saveEntry() }
  else if (e.key === 'Escape') {
    if (showAllocationModal.value) { e.preventDefault(); showAllocationModal.value = false }
    else if (showLedgerWindow.value) { e.preventDefault(); showLedgerWindow.value = false }
    else if (showSearchModal.value) { e.preventDefault(); showSearchModal.value = false }
    else { router.push('/') }
  }
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus())
  window.addEventListener('keydown', handleKeydown); loadUserDefaults()
  if (route.query.mode) entryMode.value = route.query.mode
  nextTick(() => partyInput.value?.focus())
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus())
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #374151; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #4b5563; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
input[type=date]::-webkit-calendar-picker-indicator { filter: invert(0.5); }
</style>
