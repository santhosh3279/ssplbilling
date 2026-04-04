<template>
  <div class="flex h-screen flex-col bg-slate-900 font-sans text-slate-200 overflow-hidden">
    <!-- TOP NAVBAR -->
    <header class="flex h-14 items-center justify-between border-b border-slate-700 bg-slate-800 px-6 z-20 shrink-0">
      <div class="flex items-center gap-4">
        <button @click="$router.push('/')" class="mr-2 flex items-center gap-1.5 rounded-lg bg-slate-700/50 px-2.5 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-700 hover:text-white transition-all active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back
        </button>
        <div class="flex items-center gap-2 font-bold text-blue-400">
          <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
          </div>
          <span class="text-sm font-black tracking-widest uppercase text-slate-200">Cashier Desk</span>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <div class="text-right">
            <div class="text-xs font-bold text-slate-300">{{ session.fullName.value }}</div>
            <div class="truncate text-[10px] text-slate-600">{{ session.user.value }}</div>
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-slate-600 to-slate-700 text-xs font-black text-slate-300 border border-slate-600">
            {{ userInitials }}
          </div>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT ASIDE: INVOICE LIST & CONTROLS -->
      <aside class="flex w-72 flex-col border-r border-slate-700 bg-slate-900 z-10 shrink-0">
        
        <!-- SIDE PANEL CONTROLS -->
        <div class="p-3 border-b border-slate-700 space-y-3 bg-slate-800/30">
          <!-- Date & Toggle Section -->
          <div class="flex flex-col gap-2.5">
            <!-- Date Navigator -->
            <div class="flex items-center justify-between gap-1.5 bg-slate-800 rounded-xl border border-slate-700 p-1">
              <button @click="adjustDate(-1)" class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              </button>
              <div class="flex-1 text-center">
                <input
                  ref="dateInput"
                  type="date"
                  v-model="filterDate"
                  class="bg-transparent border-none text-xs font-black text-slate-300 focus:ring-0 p-0 text-center cursor-pointer w-full"
                  @change="loadInvoices"
                />
              </div>
              <button @click="adjustDate(1)" class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </button>
            </div>

          </div>

          <!-- Search Bar -->
          <div class="relative group">
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              placeholder="Search bills..."
              class="w-full rounded-xl border border-slate-700 bg-slate-800 py-2.5 pl-9 pr-3 text-xs font-bold text-slate-300 placeholder-slate-600 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all"
            />
            <svg class="absolute left-3 top-2.5 text-slate-600 group-focus-within:text-blue-500 transition-colors" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-12 gap-3">
            <div class="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
            <span class="text-xs font-bold text-slate-600 uppercase tracking-widest">Loading...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-12 text-center px-6">
            <div class="mb-3 rounded-xl bg-slate-800 p-4 text-slate-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
            </div>
            <div class="text-sm font-bold text-slate-600">No bills found</div>
            <div class="text-[10px] text-slate-700 uppercase tracking-widest mt-1">Try changing the date</div>
          </div>
          <div v-else class="p-2 space-y-1">
            <button
              v-for="inv in invoices"
              :key="inv.name"
              :data-inv-name="inv.name"
              @click="selectInvoice(inv)"
              class="group flex w-full flex-col rounded-lg p-3 text-left transition-all active:scale-[0.98]"
              :class="selectedInvoice?.name === inv.name
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                : 'bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400'"
            >
              <div class="flex items-center justify-between mb-1">
                <span
                  class="rounded px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider"
                  :class="selectedInvoice?.name === inv.name
                    ? 'bg-blue-500/50 text-white'
                    : inv.docstatus === 0 ? 'bg-slate-700 text-slate-500' : 'bg-rose-900/40 text-rose-400'"
                >{{ inv.docstatus === 0 ? 'DRAFT' : 'UNPAID' }}</span>
                <span class="text-[10px] font-medium" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-600'">
                  {{ inv.posting_time }}
                </span>
              </div>
              <div class="text-sm font-bold leading-tight" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-slate-200'">{{ inv.name }}</div>
              <div class="truncate text-[11px] mt-0.5" :class="selectedInvoice?.name === inv.name ? 'text-blue-100' : 'text-slate-500'">
                {{ inv.customer }}
              </div>
              <div class="mt-2 flex items-center justify-between border-t pt-2" :class="selectedInvoice?.name === inv.name ? 'border-blue-500/50' : 'border-slate-700'">
                <span class="text-[10px] font-black uppercase tracking-widest opacity-70">{{ inv.items_count || 0 }} items</span>
                <div class="font-mono text-xs font-bold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-emerald-400'">₹{{ fmt(inv.grand_total) }}</div>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- CENTER: INVOICE PREVIEW -->
      <main class="flex flex-1 flex-col bg-slate-900 overflow-hidden relative">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center text-slate-700">
          <div class="mb-6 h-28 w-28 opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
          </div>
          <div class="text-base font-bold text-slate-600">Select a bill to process payment</div>
          <div class="mt-3 flex items-center gap-4 text-xs font-bold uppercase tracking-[0.2em] text-slate-700">
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">↑</kbd>
              <kbd class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">↓</kbd>
              Navigate
            </span>
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">ENTER</kbd>
              Select
            </span>
          </div>
        </div>

        <template v-else>
          <!-- Invoice Header -->
          <div class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-6 py-3 z-10">
            <div>
              <h2 class="text-lg font-bold text-slate-100 leading-none mb-1">{{ selectedInvoice.name }}</h2>
              <div class="flex items-center gap-3 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <span class="text-blue-400">{{ selectedInvoice.customer }}</span>
                <span class="h-1 w-1 rounded-full bg-slate-600"></span>
                <span>{{ formatDate(selectedInvoice.posting_date) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button @click="showPrintModal = true" class="rounded-lg border border-slate-700 bg-slate-700 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-600 active:scale-95 transition-all flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                Print
              </button>
            </div>
          </div>

          <!-- Items Table -->
          <div class="flex-1 overflow-y-auto custom-scrollbar px-6 py-4">
            <div v-if="loadingPreview" class="flex flex-col items-center justify-center h-64 gap-3">
              <div class="h-7 w-7 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
              <span class="text-xs font-bold text-slate-600 uppercase tracking-[0.2em]">Loading details...</span>
            </div>
            <div v-else class="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-slate-700/50 text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-slate-700">
                    <th class="px-5 py-3">Item Details</th>
                    <th class="px-5 py-3 text-right">Qty</th>
                    <th class="px-5 py-3 text-right">Rate</th>
                    <th class="px-5 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/50">
                  <tr v-for="item in previewItems" :key="item.name" class="hover:bg-slate-700/30 transition-colors">
                    <td class="px-5 py-3">
                      <div class="text-sm font-bold text-slate-200">{{ item.item_name }}</div>
                      <div class="text-[10px] font-medium text-slate-600 mt-0.5">{{ item.item_code }}</div>
                    </td>
                    <td class="px-5 py-3 text-right font-mono text-sm font-bold text-slate-400">{{ item.qty }} {{ item.uom }}</td>
                    <td class="px-5 py-3 text-right font-mono text-sm font-bold text-slate-400">₹{{ fmt(item.rate) }}</td>
                    <td class="px-5 py-3 text-right font-mono text-sm font-black text-slate-200">₹{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Summary Bar -->
          <div class="border-t border-slate-700 bg-slate-800 px-6 py-4">
            <div class="flex items-end justify-between">
              <div class="flex gap-6">
                <div class="space-y-0.5">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-600">Total Qty</div>
                  <div class="text-xl font-black tracking-tight text-slate-200">{{ previewItems.reduce((acc, i) => acc + i.qty, 0) }}</div>
                </div>
                <div class="space-y-0.5">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-600">Items</div>
                  <div class="text-xl font-black tracking-tight text-slate-200">{{ previewItems.length }}</div>
                </div>
              </div>
              <div class="flex flex-col items-end gap-0.5">
                <div class="text-[10px] font-black uppercase tracking-[0.2em] text-blue-500">Grand Total</div>
                <div class="text-3xl font-black tracking-tighter text-slate-100 font-mono">₹{{ fmt(selectedInvoice.grand_total) }}</div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- UNALLOCATED CASH PANEL -->
      <aside v-if="selectedInvoice && (unallocatedPayments.length > 0 || (selectedInvoice.advances && selectedInvoice.advances.length > 0))" class="flex w-80 flex-col border-l border-slate-700 bg-slate-900 z-10 shrink-0">
        <div class="p-4 border-b border-slate-700 bg-slate-800/30">
          <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-blue-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Payment Reconciliation
          </h3>
          <p class="mt-1 text-[10px] font-bold text-slate-500 uppercase truncate">For {{ selectedInvoice?.customer }}</p>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-4">
          <!-- Already Allocated Section -->
          <div v-if="selectedInvoice.advances && selectedInvoice.advances.length > 0" class="space-y-2">
            <h4 class="text-[9px] font-black uppercase tracking-widest text-slate-600 px-1">Already Allocated</h4>
            <div v-for="adv in selectedInvoice.advances" :key="adv.reference_name" class="rounded-xl border border-blue-900/30 bg-blue-900/10 p-2.5">
              <div class="flex justify-between items-start">
                <span class="text-[10px] font-black text-blue-400 truncate">{{ adv.reference_name }}</span>
                <span class="text-[10px] font-black text-slate-200 font-mono">₹{{ fmt(adv.allocated_amount) }}</span>
              </div>
              <p class="mt-1 text-[8px] font-bold text-slate-500 italic uppercase">In this journal entry this amount is allocated</p>
            </div>
          </div>

          <!-- Unallocated Section -->
          <div v-if="unallocatedPayments.length > 0" class="space-y-2">
            <h4 class="text-[9px] font-black uppercase tracking-widest text-slate-600 px-1">Unallocated Cash</h4>
            <div v-for="(pe, index) in unallocatedPayments" :key="pe.name" class="rounded-xl border border-slate-700 bg-slate-800 p-3 shadow-sm hover:border-slate-600 transition-colors space-y-3">
              <div class="flex justify-between items-start">
                <div class="overflow-hidden">
                  <div class="text-[11px] font-black text-slate-200 truncate">{{ pe.name }}</div>
                  <div class="text-[9px] font-bold text-slate-500 uppercase">{{ formatDate(pe.posting_date) }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] font-black text-emerald-400 font-mono whitespace-nowrap">₹{{ fmt(pe.unallocated_amount) }}</div>
                  <div class="text-[8px] font-bold text-slate-600 uppercase">{{ pe.mode_of_payment }}</div>
                </div>
              </div>
              
              <div class="relative group">
                <div class="absolute left-3 top-1/2 -translate-y-1/2 text-[8px] font-black text-slate-600 uppercase">Alloc</div>
                <input
                  :ref="el => allocationInputs[index] = el"
                  type="number"
                  v-model.number="pe.amount_to_allocate"
                  @focus="$event.target.select()"
                  class="w-full rounded-lg border border-slate-700 bg-slate-900 py-1.5 pl-10 pr-3 text-right font-mono text-xs font-black text-blue-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-all outline-none"
                  @keydown.enter="focusNextAllocation(index)"
                />
              </div>
            </div>
          </div>
        </div>

        <div v-if="unallocatedPayments.length > 0" class="p-4 border-t border-slate-700 bg-slate-800/50 space-y-3">
          <div class="flex justify-between items-center px-1">
            <span class="text-[10px] font-black uppercase tracking-widest text-slate-500">Total to Allocate</span>
            <span class="text-xs font-black text-blue-400 font-mono">₹{{ fmt(totalAmountToAllocate) }}</span>
          </div>

          <button
            ref="allocateButton"
            @click="submitAllocation"
            :disabled="!totalAmountToAllocate || isSubmitting"
            class="w-full rounded-xl bg-blue-600 py-3 text-[10px] font-black uppercase tracking-widest text-white shadow-lg shadow-blue-900/40 hover:bg-blue-500 active:scale-95 disabled:opacity-30 transition-all flex items-center justify-center gap-2"
          >
            <span>Confirm Allocations</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
        </div>
      </aside>

      <!-- RIGHT ASIDE: PAYMENT CONTROLS -->
      <aside class="flex w-[380px] flex-col border-l border-slate-700 bg-slate-800 z-10 shrink-0">
        <div class="p-5 border-b border-slate-700 bg-slate-800/50">
          <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-4 flex items-center gap-2">
            <div class="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
            Payment Settlement
          </h3>

          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-64 text-center">
            <p class="text-xs font-bold text-slate-600 leading-relaxed px-10">Select a bill from the left to enable payment processing</p>
          </div>

          <template v-else>
            <div class="space-y-3">
              <!-- Summary Mini-Card -->
              <div class="relative rounded-xl bg-slate-900 border border-slate-700 p-4">
                <!-- Credit Badge -->
                <div v-if="isCredit" class="absolute -top-2 -right-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-rose-600 text-white shadow-lg animate-pulse ring-4 ring-slate-900">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                </div>

                <div class="flex justify-between items-start mb-4">
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-1">Bill Amount</div>
                    <div class="text-2xl font-black tracking-tight text-slate-100 font-mono">
                      ₹{{ fmt(amountToCollect) }}
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-1">Status</div>
                    <span class="inline-flex rounded px-2 py-0.5 text-[10px] font-black uppercase tracking-widest border"
                      :class="isCredit ? 'bg-rose-900/40 border-rose-700 text-rose-400' : 'bg-emerald-900/30 border-emerald-700 text-emerald-400'">
                      {{ isCredit ? 'Credit' : 'Cash' }}
                    </span>
                  </div>
                </div>

                <div class="space-y-2 border-t border-slate-700 pt-3">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-bold text-slate-600">Paid Amount</span>
                    <span class="font-mono font-bold text-slate-300">₹{{ fmt(totalPaid) }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-xs font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-emerald-400' : 'text-slate-500'">
                      {{ balance <= 0.01 ? 'Change Return' : 'Balance Due' }}
                    </span>
                    <span class="text-xl font-black font-mono" :class="balance <= 0.01 ? 'text-emerald-400' : 'text-blue-400'">
                      ₹{{ fmt(Math.abs(balance)) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Payment Mode Selector Buttons -->
              <div class="flex gap-2">
                <button
                  @click="toggleCredit(false)"
                  class="flex-1 flex items-center justify-center gap-2 rounded-xl py-2.5 text-[10px] font-black uppercase tracking-widest transition-all border"
                  :class="!isCredit ? 'bg-emerald-900/30 border-emerald-700 text-emerald-400 shadow-lg' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-750'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
                  Cash Bill
                </button>
                <button
                  @click="toggleCredit(true)"
                  class="flex-1 flex items-center justify-center gap-2 rounded-xl py-2.5 text-[10px] font-black uppercase tracking-widest transition-all border"
                  :class="isCredit ? 'bg-rose-900/40 border-rose-700 text-rose-400 shadow-lg' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-750'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  Credit
                </button>
              </div>

              <!-- Input Grid -->
              <div v-if="!isCredit" class="space-y-2">
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-600 group-focus-within:text-blue-400 transition-colors uppercase">{{ cashLabel }}</div>
                  <input
                    ref="cashInput"
                    type="number"
                    v-model="payments.cash"
                    @focus="$event.target.select()"
                    class="w-full rounded-xl border border-slate-700 bg-slate-900 py-3.5 pl-16 pr-4 text-right font-mono font-black text-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-600 group-focus-within:text-teal-400 transition-colors uppercase">{{ upiLabel }}</div>
                  <input
                    ref="upiInput"
                    type="number"
                    v-model="payments.upi"
                    @focus="$event.target.select()"
                    class="w-full rounded-xl border border-slate-700 bg-slate-900 py-3.5 pl-16 pr-4 text-right font-mono font-black text-slate-200 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-600 group-focus-within:text-sky-400 transition-colors uppercase">{{ cardLabel }}</div>
                  <input
                    ref="cardInput"
                    type="number"
                    v-model="payments.card"
                    @focus="$event.target.select()"
                    class="w-full rounded-xl border border-slate-700 bg-slate-900 py-3.5 pl-16 pr-4 text-right font-mono font-black text-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-600 group-focus-within:text-amber-400 transition-colors uppercase">{{ discountLabel }}</div>
                  <input
                    ref="discountInput"
                    type="number"
                    v-model="payments.discount"
                    @focus="$event.target.select()"
                    class="w-full rounded-xl border border-slate-700 bg-slate-900 py-3.5 pl-16 pr-4 text-right font-mono font-black text-slate-200 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all"
                  />
                </div>
              </div>

              <!-- Credit Fields -->
              <div v-else class="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div class="rounded-xl border border-rose-800/60 bg-rose-900/20 p-4">
                  <label class="text-[10px] font-black uppercase tracking-widest text-rose-400 block mb-2 ml-1">Promise Date (Due Date)</label>
                  <div class="relative group">
                    <div class="absolute left-4 top-1/2 -translate-y-1/2 text-rose-500 group-focus-within:text-rose-400 transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
                    </div>
                    <input
                      ref="dueDateInput"
                      type="text"
                      v-model="dueDate"
                      @input="handleDueDateInput"
                      @keydown.backspace="handleDueDateKeyDown"
                      placeholder="DDMM or DD/MM/YYYY"
                      class="w-full rounded-xl border border-rose-700/50 bg-slate-900 py-4 pl-12 pr-4 text-center font-mono font-black text-xl text-slate-100 placeholder-slate-700 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 transition-all outline-none"
                    />
                  </div>
                  <div class="mt-3 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-rose-500/80 bg-rose-900/30 rounded-lg p-2 border border-rose-800/40">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m5 15 7 7 7-7"/></svg>
                    Credit Ledger Posting Enabled
                  </div>
                </div>
              </div>

              <!-- Status Messages -->
              <div class="min-h-[20px]">
                <p v-if="errorMsg" class="text-[11px] font-bold text-rose-400 flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
                  {{ errorMsg }}
                </p>
                <p v-if="successMsg" class="text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  {{ successMsg }}
                </p>
              </div>

              <!-- Posting Date Selector -->
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-600 ml-1">Posting Date</label>
                <div class="flex items-center justify-between gap-1.5 bg-slate-900 rounded-xl border border-slate-700 p-1">
                  <button @click="adjustPostingDate(-1)" class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                  </button>
                  <div class="flex-1 text-center">
                    <input
                      type="date"
                      v-model="postingDate"
                      class="bg-transparent border-none text-xs font-black text-slate-300 focus:ring-0 p-0 text-center cursor-pointer w-full"
                    />
                  </div>
                  <button @click="adjustPostingDate(1)" class="rounded-lg p-1.5 text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                  </button>
                </div>
              </div>

              <!-- Action Button -->
              <button
                ref="postButton"
                @click="processPayment"
                :disabled="!canSubmit"
                class="group w-full rounded-xl py-4 font-black uppercase tracking-[0.2em] text-sm transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                :class="isCredit ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/40' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40'"
              >
                <div v-if="isSubmitting" class="flex items-center justify-center gap-3">
                  <div class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  <span>Processing...</span>
                </div>
                <div v-else class="flex items-center justify-center gap-2">
                  <span>{{ isCredit ? 'Post Credit Sale' : 'Post Settlement' }}</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </div>
              </button>
            </div>
          </template>
        </div>
      </aside>
    </div>

    <!-- CARD REFERENCE MODAL -->
    <div v-if="showCardRefModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
      <div class="w-full max-w-md bg-slate-800 rounded-2xl shadow-2xl overflow-hidden border border-slate-700 animate-in fade-in zoom-in duration-200">
        <div class="p-5 border-b border-slate-700 flex justify-between items-center">
          <h3 class="text-sm font-bold uppercase tracking-widest text-slate-300 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sky-400"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
            Card / {{ cardLabel }} Reference
          </h3>
          <button @click="showCardRefModal = false" class="text-slate-600 hover:text-slate-300 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <div class="p-6 space-y-5">
          <div class="rounded-lg bg-sky-900/30 border border-sky-700/50 p-3">
            <p class="text-[11px] font-bold text-sky-400 leading-relaxed uppercase tracking-wider">Enter the authorization or reference number for the card payment.</p>
          </div>
          <input
            ref="cardRefInput"
            v-model="cardRefNo"
            @keydown.enter="confirmCardRef"
            class="w-full rounded-xl border border-slate-700 bg-slate-900 py-4 px-5 font-mono font-black text-slate-200 placeholder-slate-700 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 transition-all outline-none"
            placeholder="Enter card reference..."
          />
          <div class="flex gap-3">
            <button
              @click="showCardRefModal = false"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest text-slate-500 bg-slate-700 hover:bg-slate-600 transition-all active:scale-95"
            >Cancel</button>
            <button
              @click="confirmCardRef"
              :disabled="!cardRefNo"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest text-white bg-sky-600 hover:bg-sky-500 transition-all active:scale-95 disabled:opacity-40 disabled:pointer-events-none"
            >Confirm & Post</button>
          </div>
        </div>
      </div>
    </div>

    <!-- DAY OPENING CHECK MODAL -->
    <transition name="fade">
      <div v-if="showOpeningRequiredModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-sm p-4">
        <div class="w-full max-w-md overflow-hidden rounded-2xl border border-amber-700/50 bg-slate-800 shadow-2xl animate-in zoom-in-95 duration-200">
          <div class="bg-amber-900/30 border-b border-amber-700/40 p-6 flex flex-col items-center text-center">
            <div class="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-900/50 text-amber-400 border border-amber-700/50">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            </div>
            <h2 class="mb-2 text-lg font-black text-slate-100 uppercase tracking-tight">Day Opening Required</h2>
            <p class="text-sm font-medium text-slate-400 leading-relaxed">
              Please record the Day Opening Box Cash before processing any payments for today.
            </p>
          </div>
          <div class="flex flex-col gap-2 p-5">
            <button
              @click="$router.push('/Cashier-Management')"
              class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white hover:bg-blue-500 active:scale-[0.98] transition-all"
            >
              <span>Record Opening Now</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </button>
            <button
              @click="$router.push('/')"
              class="w-full px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-400 transition-colors"
            >Back to Dashboard</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- PRINT OPTIONS MODAL -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="selectedInvoice?.name"
      @close="showPrintModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { session } from '../session'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings, frappeGet, frappePost } from '../api.js'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { cashierpageShortcuts } from '../shortcuts/cashierpageShortcuts'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'

/**
 * HELPER: getTodayIST
 * Defined early to ensure it's available for ref initialization.
 */
function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ==================== STATE (REFS) ====================
// Define all refs first to avoid ReferenceErrors in functions or watchers
const filterDate = ref(getTodayIST())
const postingDate = ref(getTodayIST())
const searchQuery = ref('')

const showCardRefModal = ref(false)
const showPrintModal = ref(false)
const cardRefNo = ref('')
const showOpeningRequiredModal = ref(false)

// Block page shortcuts while any inline subwindow is open
useSubwindowWatcher(showCardRefModal)
useSubwindowWatcher(showPrintModal)
useSubwindowWatcher(showOpeningRequiredModal)

const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const unallocatedPayments = ref([])
const allocatedAdvances = ref([])
const unallocatedAmountTotal = ref(0)
const allocationInputs = ref([])
const allocateButton = ref(null)
const postButton = ref(null)

const totalAmountToAllocate = computed(() => {
  return unallocatedPayments.value.reduce((acc, p) => acc + (Number(p.amount_to_allocate) || 0), 0)
})

const isCredit = ref(false)
const dueDate = ref('')
const isSubmitting = ref(false)
const loadingList = ref(false)
const loadingPreview = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const payments = ref({
  cash: 0,
  upi: 0,
  card: 0,
  discount: 0
})

const seriesAccounts = ref({
  cash: '',
  upi: '',
  card: '',
  discount: ''
})

// DOM Refs
const cashInput = ref(null)
const upiInput = ref(null)
const cardInput = ref(null)
const discountInput = ref(null)
const dueDateInput = ref(null)
const cardRefInput = ref(null)
const dateInput = ref(null)

// ==================== COMPUTED ====================
const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

function glLabel(key, fallback) {
  const acc = localStorage.getItem(key) || ''
  return acc ? acc.split(' - ')[0].trim() : fallback
}
const cashLabel     = computed(() => glLabel('wb-cash',             'Cash'))
const upiLabel      = computed(() => glLabel('wb-upi',              'UPI'))
const cardLabel     = computed(() => glLabel('wb-card',             'Card'))
const discountLabel = computed(() => glLabel('wb-discount-account', 'Disc'))

const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
    timeZone: 'Asia/Kolkata',
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
})

const amountToCollect = computed(() => {
  if (!selectedInvoice.value) return 0
  const gt = Number(selectedInvoice.value.grand_total || 0)
  const os = selectedInvoice.value.outstanding_amount !== undefined && selectedInvoice.value.outstanding_amount !== null
    ? Number(selectedInvoice.value.outstanding_amount)
    : gt
    
  if (selectedInvoice.value.docstatus === 1) return os
  return os < gt ? os : gt
})

const totalPaid = computed(() => {
  const sum = (Number(payments.value.cash) || 0) +
              (Number(payments.value.upi) || 0) +
              (Number(payments.value.card) || 0) +
              (Number(payments.value.discount) || 0)
  return parseFloat(sum.toFixed(2))
})

const balance = computed(() => {
  const diff = amountToCollect.value - totalPaid.value
  return parseFloat(diff.toFixed(2))
})

const changeAmount = computed(() => {
  const actualMoney = (Number(payments.value.cash) || 0) +
                      (Number(payments.value.upi) || 0) +
                      (Number(payments.value.card) || 0)
  const netToPay = amountToCollect.value - (Number(payments.value.discount) || 0)
  const change = actualMoney - netToPay
  return change > 0.005 ? parseFloat(change.toFixed(2)) : 0
})

const canSubmit = computed(() => {
  if (!selectedInvoice.value || isSubmitting.value) return false
  if (isCredit.value) return true
  return balance.value <= 0.01
})

const previewSubtotal = computed(() => {
  return previewItems.value.reduce((acc, item) => acc + (item.qty * item.rate), 0)
})

const previewDiscount = computed(() => {
  if (!selectedInvoice.value?.discount_percentage) return 0
  return previewSubtotal.value * (selectedInvoice.value.discount_percentage / 100)
})

// ==================== FUNCTIONS ====================

async function checkDayOpening() {
  if (!session.user.value) return
  const today = getTodayIST()
  // Only block access if looking at Today or posting for Today
  if (filterDate.value !== today && postingDate.value !== today) {
    showOpeningRequiredModal.value = false
    return
  }

  try {
    const hasOpening = await frappeGet('ssplbilling.api.cahierlog_api.check_cashier_opening', {
      date: today,
      user: session.user.value
    })
    const boxCash = Number(localStorage.getItem('wb-opening-box-cash') || 0)
    showOpeningRequiredModal.value = !hasOpening || !boxCash
  } catch (e) {
    console.error('[CashierDesk] Opening check failed:', e)
  }
}

async function loadInvoices() {
  loadingList.value = true
  try {
    invoices.value = await fetchDraftInvoices(searchQuery.value, 50, filterDate.value)
  } catch (e) {
    errorMsg.value = "Failed to load invoices: " + e.message
  } finally {
    loadingList.value = false
  }
}

function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function updatePayment(field, value) {
  payments.value[field] = value === '' ? 0 : Number(value)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

function adjustDate(days) {
  const d = new Date(filterDate.value)
  d.setDate(d.getDate() + days)
  filterDate.value = d.toISOString().slice(0, 10)
  loadInvoices()
}

function adjustPostingDate(days) {
  const d = new Date(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = d.toISOString().slice(0, 10)
}


let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadInvoices, 300)
}

async function selectInvoice(inv) {
  if (selectedInvoice.value?.name === inv.name) return
  
  loadingPreview.value = true
  selectedInvoice.value = inv
  previewItems.value = []
  errorMsg.value = ''
  successMsg.value = ''
  isCredit.value = false
  cardRefNo.value = ''
  
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0 }
  
  try {
    const details = await getInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    payments.value = { cash: 0, upi: 0, card: 0, discount: 0 }
    await loadSeriesSettings(details.naming_series)

    // Check for Unallocated Cash
    const unallocated = await frappeGet('ssplbilling.api.cashier_api.get_customer_unallocated_cash', {
      customer: details.customer
    })
    
    let remaining = details.outstanding_amount || details.grand_total
    unallocatedPayments.value = (unallocated || []).map(pe => {
      const alloc = Math.min(Number(pe.unallocated_amount), remaining)
      remaining -= alloc
      return { ...pe, amount_to_allocate: parseFloat(alloc.toFixed(2)) }
    })
    
    unallocatedAmountTotal.value = (unallocated || []).reduce((acc, p) => acc + Number(p.unallocated_amount || 0), 0)
    
  } catch (e) {
    errorMsg.value = "Failed to load details: " + e.message
  } finally {
    loadingPreview.value = false
  }
}

function focusNextAllocation(index) {
  if (index + 1 < unallocatedPayments.value.length) {
    allocationInputs.value[index + 1]?.focus()
    allocationInputs.value[index + 1]?.select()
  } else {
    allocateButton.value?.focus()
  }
}

async function loadSeriesSettings(series) {
  try {
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi  = localStorage.getItem('wb-upi')
    const lsCard = localStorage.getItem('wb-card')
    const settings = await fetchDashboardSettings()
    const discountAccount = settings.discount_account || 'Write Off - SSPL'

    if (lsCash || lsUpi || lsCard) {
      const seriesConfig = (settings.billing_series || []).find(s => s.series === series)
      seriesAccounts.value = {
        cash:     lsCash || seriesConfig?.cash_account || 'Cash',
        upi:      lsUpi  || seriesConfig?.upi          || 'UPI',
        card:     lsCard || seriesConfig?.card         || 'Card',
        discount: discountAccount,
      }
    } else {
      const userDefaults  = settings.user_defaults || {}
      const seriesConfig  = (settings.billing_series || []).find(s => s.series === series)
      seriesAccounts.value = {
        cash:     userDefaults.cash         || seriesConfig?.cash_account || 'Cash',
        upi:      userDefaults.upi          || seriesConfig?.upi          || 'UPI',
        card:     userDefaults.card          || seriesConfig?.card         || 'Card',
        discount: discountAccount,
      }
    }
  } catch (e) {
    console.warn("Could not load accounts", e)
  }
}

function initAccountsFromLocalStorage() {
  const lsCash = localStorage.getItem('wb-cash')
  const lsUpi  = localStorage.getItem('wb-upi')
  const lsCard = localStorage.getItem('wb-card')
  if (lsCash) seriesAccounts.value.cash = lsCash
  if (lsUpi)  seriesAccounts.value.upi  = lsUpi
  if (lsCard) seriesAccounts.value.card = lsCard
}

function toggleCredit(val) {
  isCredit.value = (val !== undefined && typeof val === 'boolean') ? val : !isCredit.value
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0 }
  if (isCredit.value) {
    nextTick(() => dueDateInput.value?.focus())
  } else {
    nextTick(() => cashInput.value?.focus())
  }
}

async function processPayment() {
  if (!canSubmit.value) return

  if (postingDate.value === getTodayIST()) {
    try {
      const hasOpening = await frappeGet('ssplbilling.api.cahierlog_api.check_cashier_opening', {
        date: getTodayIST(),
        user: session.user.value
      })
      if (!hasOpening) {
        showOpeningRequiredModal.value = true
        return
      }
    } catch (e) { console.error(e) }
  }

  if (Number(payments.value.card) > 0.01 && !cardRefNo.value) {
    showCardRefModal.value = true
    nextTick(() => cardRefInput.value?.focus())
    return
  }

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    const bill = amountToCollect.value
    const upi  = Number(payments.value.upi)  || 0
    const card = Number(payments.value.card) || 0
    const disc = Number(payments.value.discount) || 0
    let cash = Number(payments.value.cash) || 0

    const total = cash + upi + card + disc
    if (total > bill + 0.005) {
      cash = bill - upi - card - disc
    }

    let finalDueDate = getIsoDueDate()
    const today = getTodayIST()
    if (finalDueDate < today) {
      finalDueDate = today
    }

    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: cash,
      upi_amount: upi,
      card_amount: card,
      discount_amount: disc,
      is_credit: isCredit.value,
      due_date: finalDueDate,
      posting_date: postingDate.value,
      card_ref_no: cardRefNo.value,
      cash_account: seriesAccounts.value.cash,
      upi_account: seriesAccounts.value.upi,
      card_account: seriesAccounts.value.card,
      discount_account: seriesAccounts.value.discount
    }
    
    await submitInvoiceWithPayment(payload)
    
    successMsg.value = `Invoice ${selectedInvoice.value.name} processed successfully!`
    
    const nameToRemove = selectedInvoice.value.name
    setTimeout(() => {
      invoices.value = invoices.value.filter(i => i.name !== nameToRemove)
      selectedInvoice.value = null
      previewItems.value = []
      successMsg.value = ''
    }, 2000)
    
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

async function confirmCardRef() {
  if (!cardRefNo.value) return
  showCardRefModal.value = false
  await processPayment()
}

async function submitAllocation() {
  if (totalAmountToAllocate.value <= 0) {
    unallocatedPayments.value = []
    return
  }
  
  try {
    const allocations = unallocatedPayments.value
      .filter(p => (Number(p.amount_to_allocate) || 0) > 0.005)
      .map(p => ({
        reference_name: p.name,
        allocated_amount: p.amount_to_allocate
      }))

    if (allocations.length === 0) {
      unallocatedPayments.value = []
      return
    }

    const res = await frappePost('ssplbilling.api.cashier_api.update_invoice_advances', {
      invoice_name: selectedInvoice.value.name,
      allocations: allocations
    })
    
    if (res.status === 'success') {
      selectedInvoice.value.outstanding_amount = res.outstanding
      selectedInvoice.value.posting_date = res.posting_date
      selectedInvoice.value.due_date = res.due_date
      
      // Update sidebar list if needed
      const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
      if (idx !== -1) {
        invoices.value[idx].posting_date = res.posting_date
      }

      unallocatedPayments.value = []
      successMsg.value = "Payment allocated successfully!"
      setTimeout(() => successMsg.value = '', 3000)
    }
  } catch (e) {
    errorMsg.value = "Allocation failed: " + e.message
  }
}

// Shortcut Handlers
function navigateBills(dir) {
  if (!invoices.value.length) return
  if (!selectedInvoice.value) {
    selectInvoice(invoices.value[0])
    return
  }
  const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
  const nextIdx = idx + dir
  if (nextIdx >= 0 && nextIdx < invoices.value.length) {
    selectInvoice(invoices.value[nextIdx])
    nextTick(() => {
      const el = document.querySelector(`[data-inv-name="${invoices.value[nextIdx].name}"]`)
      el?.scrollIntoView({ block: 'nearest' })
    })
  }
}

function handleEnter(e) {
  const active = document.activeElement
  
  // 1. If no invoice selected, focus first bill (handled by navigateBills usually, but if enter pressed on main body)
  if (!selectedInvoice.value) {
    if (invoices.value.length) selectInvoice(invoices.value[0])
    return
  }

  // 2. Navigation Logic
  if (active.tagName !== 'INPUT' && active !== allocateButton.value && active !== postButton.value) {
    // If we just selected a bill, go to side panel if exists, else cash
    if (unallocatedPayments.value.length > 0) {
      allocationInputs.value[0]?.focus()
      allocationInputs.value[0]?.select()
    } else if (isCredit.value) {
      dueDateInput.value?.focus()
    } else {
      cashInput.value?.focus()
    }
    return
  }

  // 3. Sequential Input Navigation
  if (unallocatedPayments.value.length > 0) {
    const allocIdx = allocationInputs.value.findIndex(el => el === active)
    if (allocIdx !== -1) {
      if (allocIdx + 1 < unallocatedPayments.value.length) {
        allocationInputs.value[allocIdx + 1]?.focus()
        allocationInputs.value[allocIdx + 1]?.select()
      } else {
        allocateButton.value?.focus()
      }
      return
    }
  }

  if (active === allocateButton.value) {
    submitAllocation().then(() => {
      nextTick(() => {
        if (balance.value > 0.01) {
          if (isCredit.value) dueDateInput.value?.focus()
          else cashInput.value?.focus()
        } else {
          postButton.value?.focus()
        }
      })
    })
    return
  }

  if (isCredit.value) {
    if (active === dueDateInput.value) {
      if (canSubmit.value) postButton.value?.focus()
      else processPayment() // will show error if not valid
    } else if (active === postButton.value) {
      processPayment()
    }
  } else {
    if (active === cashInput.value) {
      upiInput.value?.focus()
      upiInput.value?.select()
    } else if (active === upiInput.value) {
      cardInput.value?.focus()
      cardInput.value?.select()
    } else if (active === cardInput.value) {
      discountInput.value?.focus()
      discountInput.value?.select()
    } else if (active === discountInput.value) {
      if (balance.value <= 0.01) postButton.value?.focus()
      else errorMsg.value = "Payment balance remaining"
    } else if (active === postButton.value) {
      processPayment()
    }
  }
}

function handleDueDateKeyDown(e) {
  if (e.key === 'Backspace' && dueDate.value) {
    dueDate.value = ''
    e.preventDefault()
  }
}

function handleDueDateInput(e) {
  let raw = e.target.value.replace(/\D/g, '')
  if (raw.length > 8) raw = raw.slice(0, 8)
  
  // Quick entry for ddmm (4 digits)
  if (raw.length === 4) {
    const day = raw.slice(0, 2)
    const month = raw.slice(2, 4)
    const year = new Date().getFullYear()
    dueDate.value = `${day}/${month}/${year}`
    return
  }

  let formatted = raw
  if (raw.length >= 5) {
    formatted = raw.slice(0, 2) + '/' + raw.slice(2, 4) + '/' + raw.slice(4)
  } else if (raw.length >= 3) {
    formatted = raw.slice(0, 2) + '/' + raw.slice(2)
  }
  dueDate.value = formatted
}

function getIsoDueDate() {
  if (!dueDate.value || !dueDate.value.includes('/')) {
    if (dueDate.value.match(/^\d{4}-\d{2}-\d{2}$/)) return dueDate.value
    return getTodayIST()
  }
  const parts = dueDate.value.split('/')
  if (parts.length !== 3) return getTodayIST()
  const dd = parts[0]
  const mm = parts[1]
  const yyyy = parts[2]
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`
}

function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    processPayment()
  }
}

// ==================== WATCHERS ====================
watch(filterDate, (newVal) => {
  postingDate.value = newVal
  checkDayOpening()
})
watch(postingDate, () => {
  checkDayOpening()
})

// ==================== LIFECYCLE ====================
onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus())
  initAccountsFromLocalStorage()
  loadInvoices()
  // Immediately block if no opening recorded (fast path via localStorage)
  if (!Number(localStorage.getItem('wb-opening-box-cash') || 0)) {
    showOpeningRequiredModal.value = true
  }
  checkDayOpening()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.removeEventListener('keydown', handleKeydown)
})

// Register shortcuts
useShortcuts(cashierpageShortcuts({
  navigateBillsUp: () => navigateBills(-1),
  navigateBillsDown: () => navigateBills(1),
  handleEnter: handleEnter,
  toggleCredit: toggleCredit,
  submitPayment: processPayment,
  goBack: () => window.history.back()
}))
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569;
}

input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
