<template>
  <div class="flex h-screen flex-col bg-slate-50 font-sans text-slate-900 overflow-hidden">
    <!-- TOP NAVBAR -->
    <header class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8 shadow-sm z-20">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2 font-bold text-blue-600">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
          </div>
          <span class="text-lg tracking-tight uppercase">Cashier Desk</span>
        </div>
        
        <div class="h-6 w-px bg-slate-200"></div>
        
        <div class="flex items-center gap-2">
          <button @click="adjustDate(-1)" class="rounded-lg p-1.5 hover:bg-slate-100 text-slate-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div class="flex flex-col items-center min-w-[120px]">
            <input 
              ref="dateInput"
              type="date" 
              v-model="filterDate" 
              class="bg-transparent border-none text-sm font-bold text-slate-700 focus:ring-0 p-0 text-center cursor-pointer"
              @change="loadInvoices"
            />
            <span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">{{ todayStr }}</span>
          </div>
          <button @click="adjustDate(1)" class="rounded-lg p-1.5 hover:bg-slate-100 text-slate-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 rounded-xl bg-slate-100 p-1">
          <button 
            @click="showUnpaid = false; loadInvoices()"
            class="rounded-lg px-4 py-1.5 text-xs font-bold transition-all"
            :class="!showUnpaid ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            Drafts
          </button>
          <button 
            @click="showUnpaid = true; loadInvoices()"
            class="rounded-lg px-4 py-1.5 text-xs font-bold transition-all"
            :class="showUnpaid ? 'bg-white text-rose-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >
            Unpaid
          </button>
        </div>

        <div class="h-6 w-px bg-slate-200"></div>

        <div class="flex items-center gap-3">
          <div class="text-right">
            <div class="text-xs font-bold text-slate-900">{{ session.fullName.value }}</div>
            <div class="truncate text-[10px] text-slate-400">{{ session.user.value }}</div>
          </div>
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 text-xs font-black text-slate-600 border border-slate-200">
            {{ userInitials }}
          </div>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT ASIDE: INVOICE LIST -->
      <aside class="flex w-80 flex-col border-r border-slate-200 bg-white z-10">
        <div class="p-4 border-b border-slate-100">
          <div class="relative group">
            <input 
              v-model="searchQuery"
              @input="debouncedSearch"
              placeholder="Search bills..."
              class="w-full rounded-xl border-slate-200 bg-slate-50 py-2.5 pl-10 text-sm focus:border-blue-500 focus:ring-4 focus:ring-blue-50/50 transition-all"
            />
            <svg class="absolute left-3 top-3 text-slate-400 group-focus-within:text-blue-500 transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-slate-50/30">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-12 gap-3">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></div>
            <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Loading bills...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-12 text-center px-6">
            <div class="mb-3 rounded-2xl bg-slate-100 p-4 text-slate-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
            </div>
            <div class="text-sm font-bold text-slate-500">No bills found</div>
            <div class="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Try changing the date</div>
          </div>
          <div v-else class="p-2 space-y-1">
            <button 
              v-for="inv in invoices" 
              :key="inv.name"
              :data-inv-name="inv.name"
              @click="selectInvoice(inv)"
              class="group flex w-full flex-col rounded-xl p-3 text-left transition-all active:scale-[0.98]"
              :class="selectedInvoice?.name === inv.name 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' 
                : 'bg-white hover:bg-white border border-transparent hover:border-slate-200 text-slate-600 shadow-sm'"
            >
              <div class="flex items-center justify-between mb-1">
                <span 
                  class="rounded px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wider"
                  :class="selectedInvoice?.name === inv.name 
                    ? 'bg-blue-500/50 text-white' 
                    : inv.docstatus === 0 ? 'bg-slate-100 text-slate-500' : 'bg-rose-50 text-rose-500'"
                >
                  {{ inv.docstatus === 0 ? 'DRAFT' : 'UNPAID' }}
                </span>
                <span class="text-[10px] font-medium" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-400'">
                  {{ inv.posting_time }}
                </span>
              </div>
              <div class="text-sm font-bold leading-tight">{{ inv.name }}</div>
              <div class="truncate text-[11px] mt-0.5" :class="selectedInvoice?.name === inv.name ? 'text-blue-100' : 'text-slate-500'">
                {{ inv.customer }}
              </div>
              <div class="mt-2 flex items-center justify-between border-t pt-2" :class="selectedInvoice?.name === inv.name ? 'border-blue-500/50' : 'border-slate-50'">
                <div class="flex items-center gap-1.5">
                  <div class="h-1 w-1 rounded-full" :class="selectedInvoice?.name === inv.name ? 'bg-blue-300' : 'bg-slate-300'"></div>
                  <span class="text-[10px] font-black uppercase tracking-widest opacity-70">{{ inv.items_count || 0 }} items</span>
                </div>
                <div class="font-mono text-xs font-bold">₹{{ fmt(inv.grand_total) }}</div>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- CENTER: INVOICE PREVIEW -->
      <main class="flex flex-1 flex-col bg-slate-50 overflow-hidden relative">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center text-slate-400">
          <div class="mb-6 h-32 w-32 opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
          </div>
          <div class="text-lg font-bold">Select a bill to process payment</div>
          <div class="mt-2 flex items-center gap-4 text-xs font-bold uppercase tracking-[0.2em] opacity-60">
            <span class="flex items-center gap-1"><kbd class="rounded border bg-white px-1.5 py-0.5 shadow-sm text-slate-600">↑</kbd><kbd class="rounded border bg-white px-1.5 py-0.5 shadow-sm text-slate-600">↓</kbd> Navigate</span>
            <span class="flex items-center gap-1"><kbd class="rounded border bg-white px-1.5 py-0.5 shadow-sm text-slate-600">ENTER</kbd> Select</span>
          </div>
        </div>

        <template v-else>
          <!-- Invoice Header -->
          <div class="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-4 shadow-sm z-10">
            <div>
              <h2 class="text-xl font-bold text-slate-900 leading-none mb-1">{{ selectedInvoice.name }}</h2>
              <div class="flex items-center gap-3 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <span class="text-blue-600">{{ selectedInvoice.customer }}</span>
                <span class="h-1 w-1 rounded-full bg-slate-300"></span>
                <span>{{ formatDate(selectedInvoice.posting_date) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button @click="printPlaceholder" class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 active:scale-95 transition-all flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                Print
              </button>
            </div>
          </div>

          <!-- Items Table -->
          <div class="flex-1 overflow-y-auto custom-scrollbar px-8 py-6">
            <div v-if="loadingPreview" class="flex flex-col items-center justify-center h-64 gap-3">
              <div class="h-8 w-8 animate-spin rounded-full border-3 border-blue-600 border-t-transparent"></div>
              <span class="text-xs font-bold text-slate-400 uppercase tracking-[0.2em]">Loading details...</span>
            </div>
            <div v-else class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-slate-50/50 text-[10px] font-black uppercase tracking-widest text-slate-500 border-b border-slate-100">
                    <th class="px-6 py-4">Item Details</th>
                    <th class="px-6 py-4 text-right">Qty</th>
                    <th class="px-6 py-4 text-right">Rate</th>
                    <th class="px-6 py-4 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-50">
                  <tr v-for="item in previewItems" :key="item.name" class="hover:bg-slate-50/50 transition-colors">
                    <td class="px-6 py-4">
                      <div class="text-sm font-bold text-slate-800">{{ item.item_name }}</div>
                      <div class="text-[10px] font-medium text-slate-400 mt-0.5">{{ item.item_code }}</div>
                    </td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-bold text-slate-600">{{ item.qty }} {{ item.uom }}</td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-bold text-slate-600">₹{{ fmt(item.rate) }}</td>
                    <td class="px-6 py-4 text-right font-mono text-sm font-black text-slate-900">₹{{ fmt(item.amount) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Summary Bar -->
          <div class="border-t border-slate-200 bg-white p-8">
            <div class="flex items-end justify-between">
              <div class="flex gap-8">
                <div class="space-y-1">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Total Qty</div>
                  <div class="text-xl font-black tracking-tight text-slate-900">{{ previewItems.reduce((acc, i) => acc + i.qty, 0) }}</div>
                </div>
                <div class="space-y-1">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Items</div>
                  <div class="text-xl font-black tracking-tight text-slate-900">{{ previewItems.length }}</div>
                </div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <div class="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600">Grand Total</div>
                <div class="text-4xl font-black tracking-tighter text-slate-900 font-mono">₹{{ fmt(selectedInvoice.grand_total) }}</div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT ASIDE: PAYMENT CONTROLS -->
      <aside class="flex w-[400px] flex-col border-l border-slate-200 bg-white z-10">
        <div class="p-6 border-b border-slate-100 bg-slate-50/30">
          <h3 class="text-xs font-black uppercase tracking-[0.2em] text-slate-500 mb-4 flex items-center gap-2">
            <div class="h-1.5 w-1.5 rounded-full bg-blue-600"></div>
            Payment Settlement
          </h3>
          
          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-64 text-center">
            <p class="text-xs font-bold text-slate-400 leading-relaxed px-12">Select a bill from the left list to enable payment processing</p>
          </div>

          <template v-else>
            <div class="space-y-4">
              <!-- Summary Mini-Card -->
              <div class="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                <div class="flex justify-between items-start mb-4">
                  <div>
                    <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Bill Amount</div>
                    <div class="text-xl font-black tracking-tight text-slate-900 font-mono">
                      ₹{{ fmt(amountToCollect) }}
                    </div>
                  </div>
                  <button 
                    @click="toggleCredit"
                    class="flex items-center gap-2 rounded-xl px-3 py-2 transition-all border"
                    :class="isCredit 
                      ? 'bg-rose-50 border-rose-200 text-rose-600' 
                      : 'bg-emerald-50 border-emerald-200 text-emerald-600'"
                  >
                    <div class="h-2 w-2 rounded-full animate-pulse" :class="isCredit ? 'bg-rose-500' : 'bg-emerald-500'"></div>
                    <span class="text-[10px] font-black uppercase tracking-widest">{{ isCredit ? 'CREDIT' : 'CASH BILL' }}</span>
                  </button>
                </div>

                <div class="space-y-2 border-t border-slate-100 pt-4">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-bold text-slate-500">Paid Amount</span>
                    <span class="font-mono font-bold text-slate-900">₹{{ fmt(totalPaid) }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-xs font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-emerald-600' : 'text-slate-400'">
                      {{ balance <= 0.01 ? 'Change Return' : 'Balance Due' }}
                    </span>
                    <span class="text-lg font-black font-mono" :class="balance <= 0.01 ? 'text-emerald-600' : 'text-blue-600'">
                      ₹{{ fmt(Math.abs(balance)) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Input Grid -->
              <div v-if="!isCredit" class="space-y-3">
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-400 group-focus-within:text-blue-600 transition-colors uppercase">Cash</div>
                  <input 
                    ref="cashInput"
                    type="number" 
                    v-model="payments.cash"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border-slate-200 bg-slate-50 py-4 pl-16 pr-4 text-right font-mono font-black text-slate-900 focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all group-hover:border-slate-300 shadow-inner"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-400 group-focus-within:text-teal-600 transition-colors uppercase">UPI</div>
                  <input 
                    ref="upiInput"
                    type="number" 
                    v-model="payments.upi"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border-slate-200 bg-slate-50 py-4 pl-16 pr-4 text-right font-mono font-black text-slate-900 focus:border-teal-500 focus:ring-4 focus:ring-teal-50 transition-all group-hover:border-slate-300 shadow-inner"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-400 group-focus-within:text-sky-600 transition-colors uppercase">Bank</div>
                  <input 
                    ref="bankInput"
                    type="number" 
                    v-model="payments.bank"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border-slate-200 bg-slate-50 py-4 pl-16 pr-4 text-right font-mono font-black text-slate-900 focus:border-sky-500 focus:ring-4 focus:ring-sky-50 transition-all group-hover:border-slate-300 shadow-inner"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-black text-slate-400 group-focus-within:text-amber-600 transition-colors uppercase">Disc</div>
                  <input 
                    ref="discountInput"
                    type="number" 
                    v-model="payments.discount"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border-slate-200 bg-slate-50 py-4 pl-16 pr-4 text-right font-mono font-black text-slate-900 focus:border-amber-500 focus:ring-4 focus:ring-amber-50 transition-all group-hover:border-slate-300 shadow-inner"
                  />
                </div>
              </div>

              <!-- Credit Fields -->
              <div v-else class="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div class="rounded-2xl border border-rose-100 bg-rose-50/30 p-4">
                  <label class="text-[10px] font-black uppercase tracking-widest text-rose-500 block mb-2">Promise Date (Due Date)</label>
                  <div class="group relative">
                    <input 
                      ref="dueDateInput"
                      type="text" 
                      v-model="dueDate"
                      @input="handleDueDateInput"
                      placeholder="DD/MM/YYYY"
                      class="w-full rounded-xl border-rose-200 bg-white py-3 px-4 text-center font-mono font-bold text-slate-900 focus:border-rose-500 focus:ring-4 focus:ring-rose-50 transition-all"
                    />
                  </div>
                  <div class="mt-2 flex items-center gap-2 text-[10px] font-bold text-rose-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m5 15 7 7 7-7"/></svg>
                    Credit Ledger Posting
                  </div>
                </div>
              </div>

              <!-- Status Messages -->
              <div class="min-h-[24px]">
                <p v-if="errorMsg" class="text-[11px] font-bold text-rose-500 flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
                  {{ errorMsg }}
                </p>
                <p v-if="successMsg" class="text-[11px] font-bold text-emerald-500 flex items-center gap-1.5 animate-bounce">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  {{ successMsg }}
                </p>
              </div>

              <!-- Action Button -->
              <div class="pt-4">
                <button 
                  @click="processPayment"
                  :disabled="!canSubmit"
                  class="group relative w-full overflow-hidden rounded-2xl py-5 font-black uppercase tracking-[0.2em] shadow-2xl transition-all active:scale-95 disabled:grayscale disabled:opacity-50 disabled:pointer-events-none"
                  :class="isCredit ? 'bg-rose-600 text-white shadow-rose-200' : 'bg-slate-900 text-white shadow-slate-200'"
                >
                  <div v-if="isSubmitting" class="flex items-center justify-center gap-3">
                    <div class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    <span>Processing...</span>
                  </div>
                  <div v-else class="flex items-center justify-center gap-2">
                    <span>{{ isCredit ? 'Post Credit Sale' : 'Post Settlement' }}</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="ml-1 group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                  </div>
                </button>
              </div>
            </div>
          </template>
        </div>
      </aside>
    </div>

    <!-- BANK REFERENCE MODAL -->
    <div v-if="showBankRefModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200 animate-in fade-in zoom-in duration-200">
        <div class="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <h3 class="text-sm font-bold uppercase tracking-widest text-slate-600 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sky-500"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
            Bank Transfer Reference
          </h3>
          <button @click="showBankRefModal = false" class="text-slate-400 hover:text-slate-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <div class="p-8">
          <div class="mb-6 rounded-2xl bg-sky-50/50 border border-sky-100 p-4">
            <p class="text-[11px] font-bold text-sky-600 leading-relaxed uppercase tracking-wider">Please enter the UTR or Reference Number for the bank transfer.</p>
          </div>
          <div class="group relative mb-8">
            <input 
              ref="bankRefInput"
              v-model="bankRefNo"
              @keydown.enter="confirmBankRef"
              class="w-full rounded-2xl border-slate-200 bg-slate-50 py-5 px-6 font-mono font-black text-slate-900 focus:border-sky-500 focus:ring-4 focus:ring-sky-50 transition-all group-hover:border-slate-300 shadow-inner"
              placeholder="Enter bank reference..."
            />
          </div>
          <div class="flex gap-3 pt-2">
            <button 
              @click="showBankRefModal = false"
              class="flex-1 rounded-2xl py-4 text-xs font-bold uppercase tracking-widest text-slate-500 bg-slate-100 hover:bg-slate-200 transition-all active:scale-95"
            >
              Cancel
            </button>
            <button 
              @click="confirmBankRef"
              :disabled="!bankRefNo"
              class="flex-1 rounded-2xl py-4 text-xs font-bold uppercase tracking-widest text-white bg-sky-600 hover:bg-sky-700 shadow-lg shadow-sky-100 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
            >
              Confirm & Post
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- DAY OPENING CHECK MODAL -->
    <transition name="fade">
      <div v-if="showOpeningRequiredModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
        <div class="w-full max-w-md overflow-hidden rounded-2xl border border-amber-200 bg-white shadow-2xl animate-in zoom-in-95 duration-200">
          <div class="bg-amber-50 p-6 flex flex-col items-center text-center">
            <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 text-amber-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            </div>
            <h2 class="mb-2 text-xl font-black text-slate-900 uppercase tracking-tight">Day Opening Required</h2>
            <p class="text-sm font-medium text-slate-600 leading-relaxed">
              Please Update Day Opening Box Cash before processing any payments for today.
            </p>
          </div>
          <div class="flex flex-col gap-2 p-6 bg-slate-50/50">
            <button 
              @click="$router.push('/Cashier-Management')"
              class="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 active:scale-[0.98] transition-all"
            >
              <span>Go to Cashier Management</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </button>
            <button 
              @click="$router.push('/')"
              class="w-full px-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-700 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { session } from '../session'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings, frappeGet } from '../api.js'
import { useShortcuts } from '../services/shortcutManager'
import { cashierpageShortcuts } from '../shortcuts/cashierpageShortcuts'

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
const searchQuery = ref('')
const showUnpaid = ref(false)
const showBankRefModal = ref(false)
const bankRefNo = ref('')
const showOpeningRequiredModal = ref(false)

const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
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
  bank: 0,
  discount: 0
})

const seriesAccounts = ref({
  cash: '',
  upi: '',
  bank: '',
  discount: ''
})

// DOM Refs
const cashInput = ref(null)
const upiInput = ref(null)
const bankInput = ref(null)
const discountInput = ref(null)
const dueDateInput = ref(null)
const bankRefInput = ref(null)
const dateInput = ref(null)

// ==================== COMPUTED ====================
const userInitials = computed(() => {
  const name = String(session.fullName.value || session.user.value || 'U')
  return name.split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2) || 'U'
})

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
  return selectedInvoice.value.docstatus === 1 
    ? Number(selectedInvoice.value.outstanding_amount || 0) 
    : Number(selectedInvoice.value.grand_total || 0)
})

const totalPaid = computed(() => {
  const sum = (Number(payments.value.cash) || 0) + 
              (Number(payments.value.upi) || 0) + 
              (Number(payments.value.bank) || 0) + 
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
                      (Number(payments.value.bank) || 0)
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
  // Only block access if the user is looking at Today
  if (filterDate.value !== getTodayIST()) {
    showOpeningRequiredModal.value = false
    return
  }

  try {
    const hasOpening = await frappeGet('ssplbilling.api.cahierlog_api.check_cashier_opening', {
      date: getTodayIST(),
      user: session.user.value
    })
    showOpeningRequiredModal.value = !hasOpening
  } catch (e) {
    console.error('[CashierDesk] Opening check failed:', e)
  }
}

async function loadInvoices() {
  loadingList.value = true
  try {
    invoices.value = await fetchDraftInvoices(searchQuery.value, 50, filterDate.value, showUnpaid.value)
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

function toggleUnpaid() {
  showUnpaid.value = !showUnpaid.value
  loadInvoices()
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
  bankRefNo.value = ''
  
  payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
  
  try {
    const details = await getInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
    await loadSeriesSettings(details.naming_series)
  } catch (e) {
    errorMsg.value = "Failed to load details: " + e.message
  } finally {
    loadingPreview.value = false
  }
}

async function loadSeriesSettings(series) {
  try {
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi  = localStorage.getItem('wb-upi')
    const lsBank = localStorage.getItem('wb-bank')
    const settings = await fetchDashboardSettings()
    const discountAccount = settings.discount_account || 'Write Off - SSPL'

    if (lsCash || lsUpi || lsBank) {
      const seriesConfig = (settings.billing_series || []).find(s => s.series === series)
      seriesAccounts.value = {
        cash:     lsCash || seriesConfig?.cash_account || 'Cash',
        upi:      lsUpi  || seriesConfig?.upi          || 'UPI',
        bank:     lsBank || seriesConfig?.bank         || 'Bank',
        discount: discountAccount,
      }
    } else {
      const userDefaults  = settings.user_defaults || {}
      const seriesConfig  = (settings.billing_series || []).find(s => s.series === series)
      seriesAccounts.value = {
        cash:     userDefaults.cash         || seriesConfig?.cash_account || 'Cash',
        upi:      userDefaults.upi          || seriesConfig?.upi          || 'UPI',
        bank:     userDefaults.bank_account || seriesConfig?.bank         || 'Bank',
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
  const lsBank = localStorage.getItem('wb-bank')
  if (lsCash) seriesAccounts.value.cash = lsCash
  if (lsUpi)  seriesAccounts.value.upi  = lsUpi
  if (lsBank) seriesAccounts.value.bank = lsBank
}

function toggleCredit() {
  isCredit.value = !isCredit.value
  payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
}

function printPlaceholder() {
  alert("Print feature is ready. Waiting for print format selection.")
}

async function processPayment() {
  if (!canSubmit.value) return

  if (filterDate.value === getTodayIST()) {
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

  if (Number(payments.value.bank) > 0.01 && !bankRefNo.value) {
    showBankRefModal.value = true
    nextTick(() => bankRefInput.value?.focus())
    return
  }

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const bill = amountToCollect.value
    const upi = Number(payments.value.upi) || 0
    const bank = Number(payments.value.bank) || 0
    const disc = Number(payments.value.discount) || 0
    let cash = Number(payments.value.cash) || 0

    const total = cash + upi + bank + disc
    if (total > bill + 0.005) {
      cash = bill - upi - bank - disc
    }

    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: cash,
      upi_amount: upi,
      bank_amount: bank,
      discount_amount: disc,
      is_credit: isCredit.value,
      due_date: getIsoDueDate(),
      bank_ref_no: bankRefNo.value,
      cash_account: seriesAccounts.value.cash,
      upi_account: seriesAccounts.value.upi,
      bank_account: seriesAccounts.value.bank,
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

async function confirmBankRef() {
  if (!bankRefNo.value) return
  showBankRefModal.value = false
  await processPayment()
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
  if (active.tagName !== 'INPUT' || (active.type !== 'number' && active.type !== 'text' && active.type !== 'date')) {
    if (isCredit.value) {
      dueDateInput.value?.focus()
    } else {
      cashInput.value?.focus()
    }
    return
  }
  if (isCredit.value) {
    if (active === dueDateInput.value) processPayment()
  } else {
    if (active === cashInput.value) {
      upiInput.value?.focus()
    } else if (active === upiInput.value) {
      bankInput.value?.focus()
    } else if (active === bankInput.value) {
      discountInput.value?.focus()
    } else if (active === discountInput.value) {
      processPayment()
    }
  }
}

function handleDueDateInput(e) {
  let raw = e.target.value.replace(/\D/g, '')
  if (raw.length > 8) raw = raw.slice(0, 8)
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
watch(filterDate, () => {
  checkDayOpening()
})

// ==================== LIFECYCLE ====================
onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus())
  initAccountsFromLocalStorage()
  loadInvoices()
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
  background: #cbd5e1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
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
