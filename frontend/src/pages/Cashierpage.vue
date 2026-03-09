<template>
  <div class="flex h-screen flex-col bg-slate-50 text-slate-900 font-sans">
    
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button 
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-slate-900">CASHIER DESK</h1>
        <div class="h-4 w-px bg-slate-200 mx-2"></div>
        <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600 border border-blue-100">
          {{ invoices.length }} Pending Invoices
        </span>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Current Date</div>
          <div class="text-sm font-medium text-slate-600">{{ todayStr }}</div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      
      <!-- LEFT PANEL: INVOICE LIST -->
      <aside class="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div class="p-4 space-y-3">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
            <input 
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text" 
              placeholder="Search invoice or customer..." 
              class="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-xs text-slate-700 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
          <div class="flex gap-2">
            <input 
              v-model="filterDate"
              @change="loadInvoices"
              type="date" 
              class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 outline-none focus:border-blue-500 transition-all"
            />
            <button 
              @click="loadInvoices"
              class="rounded-lg bg-slate-100 px-3 text-slate-500 hover:bg-slate-200 hover:text-slate-900 transition-all"
              title="Refresh List"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-slate-50/50">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-50">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent mb-2"></div>
            <span class="text-xs text-slate-500">Loading bills...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-20 opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4 text-slate-400"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-sm font-medium text-slate-500">No invoices found</span>
          </div>
          <div v-else class="px-3 pb-4">
            <button 
              v-for="inv in invoices" 
              :key="inv.name"
              @click="selectInvoice(inv)"
              class="mb-2 flex w-full flex-col gap-1.5 rounded-xl p-4 text-left transition-all outline-none group border shadow-sm"
              :class="selectedInvoice?.name === inv.name 
                ? 'bg-blue-600 border-blue-500 ring-2 ring-blue-100' 
                : 'bg-white hover:bg-slate-50 border-slate-200'"
            >
              <div class="flex items-start justify-between">
                <span class="font-mono text-[11px] font-bold" :class="selectedInvoice?.name === inv.name ? 'text-blue-100' : 'text-blue-600'">
                  {{ inv.name }}
                </span>
                <span class="text-xs font-bold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-emerald-600'">
                  ₹{{ fmt(inv.grand_total) }}
                </span>
              </div>
              <div class="truncate text-sm font-semibold" :class="selectedInvoice?.name === inv.name ? 'text-white' : 'text-slate-900'">
                {{ inv.customer_name }}
              </div>
              <div class="flex items-center justify-between mt-1">
                <span class="text-[10px] font-medium" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-400'">
                  {{ inv.docstatus === 0 ? 'DRAFT' : 'UNPAID' }}
                </span>
                <span class="text-[10px] font-medium" :class="selectedInvoice?.name === inv.name ? 'text-blue-200' : 'text-slate-400'">
                  {{ formatDate(inv.posting_date) }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- MIDDLE PANEL: PREVIEW -->
      <main class="flex flex-1 flex-col bg-slate-100/30 overflow-hidden">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-6 text-slate-400"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <p class="text-lg font-medium text-slate-500">Select an invoice to preview</p>
        </div>

        <template v-else>
          <!-- PREVIEW HEADER -->
          <div class="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-4 shadow-sm z-10">
            <div>
              <h2 class="text-xl font-bold text-slate-900 leading-none mb-1">{{ selectedInvoice.name }}</h2>
              <p class="text-sm font-medium text-slate-500">{{ selectedInvoice.customer_name }}</p>
            </div>
            <div class="flex gap-3">
              <!-- PRINT BUTTON PLACEHOLDER -->
              <button 
                class="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-all border border-slate-200 shadow-sm active:scale-95"
                @click="printPlaceholder"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-500"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                <span>Print Bill</span>
              </button>
            </div>
          </div>

          <!-- PREVIEW CONTENT -->
          <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div class="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-md border border-slate-200">
              <div class="flex justify-between mb-8 border-b border-slate-100 pb-8">
                <div>
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Billing To</div>
                  <div class="text-lg font-bold text-slate-900 leading-none mb-1">{{ selectedInvoice.customer_name }}</div>
                  <div class="text-sm font-medium text-slate-500 font-mono">{{ selectedInvoice.customer }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Invoice Details</div>
                  <div class="text-sm text-slate-600 mb-1">Date: <span class="font-bold text-slate-900">{{ formatDate(selectedInvoice.posting_date) }}</span></div>
                  <div class="flex justify-end">
                    <span class="rounded bg-slate-100 px-2 py-0.5 text-[10px] uppercase font-bold text-slate-600 border border-slate-200">{{ selectedInvoice.docstatus === 0 ? 'DRAFT' : 'UNPAID' }}</span>
                  </div>
                </div>
              </div>

              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    <th class="py-3 px-2">Item</th>
                    <th class="py-3 px-2 text-right">Qty</th>
                    <th class="py-3 px-2 text-right">Rate</th>
                    <th class="py-3 px-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody class="text-sm">
                  <tr v-for="item in previewItems" :key="item.item_code" class="border-b border-slate-50">
                    <td class="py-4 px-2">
                      <div class="font-bold text-slate-800">{{ item.item_name }}</div>
                      <div class="text-[11px] text-slate-400 font-mono">{{ item.item_code }}</div>
                    </td>
                    <td class="py-4 px-2 text-right text-slate-600 font-medium">{{ item.qty }} {{ item.uom }}</td>
                    <td class="py-4 px-2 text-right text-slate-600 font-mono">₹{{ fmt(item.rate) }}</td>
                    <td class="py-4 px-2 text-right font-bold text-slate-900 font-mono">₹{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>

              <div class="mt-8 flex justify-end">
                <div class="w-64 space-y-3">
                  <div class="flex justify-between text-sm text-slate-500">
                    <span class="font-medium">Subtotal</span>
                    <span class="font-mono font-bold">₹{{ fmt(previewSubtotal) }}</span>
                  </div>
                  <div v-if="selectedInvoice.discount_percentage" class="flex justify-between text-sm text-rose-600">
                    <span class="font-medium">Discount ({{ selectedInvoice.discount_percentage }}%)</span>
                    <span class="font-mono font-bold">-₹{{ fmt(previewDiscount) }}</span>
                  </div>
                  <div class="flex justify-between border-t border-slate-200 pt-3 text-lg font-bold text-slate-900">
                    <span>Grand Total</span>
                    <span class="font-mono text-emerald-600">₹{{ fmt(selectedInvoice.grand_total) }}</span>
                  </div>
                  <div v-if="selectedInvoice.outstanding_amount && selectedInvoice.docstatus === 1" class="flex justify-between text-sm text-blue-600 bg-blue-50/50 p-2 rounded-lg border border-blue-100 mt-2">
                    <span class="font-bold uppercase tracking-wider text-[10px]">Outstanding</span>
                    <span class="font-mono font-bold">₹{{ fmt(selectedInvoice.outstanding_amount) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT PANEL: PAYMENT -->
      <aside class="flex w-96 shrink-0 flex-col border-l border-slate-200 bg-white shadow-xl">
        <div class="p-6 border-b border-slate-100 bg-slate-50/50">
          <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400">Payment Entry</h2>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-full text-slate-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-3"><rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>
            <p class="text-xs font-medium uppercase tracking-wider">Select bill to pay</p>
          </div>

          <template v-else>
            <!-- TOP SUMMARY CARD -->
            <div class="rounded-2xl bg-white border-2 border-slate-100 shadow-sm relative overflow-hidden">
              <div class="absolute top-0 left-0 w-full h-1 bg-emerald-500"></div>
              <div class="grid grid-cols-3 divide-x divide-slate-100">
                <div class="p-4 text-center">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Bill Amount</div>
                  <div class="text-xl font-black tracking-tight text-slate-900 font-mono">
                    ₹{{ fmt(amountToCollect) }}
                  </div>
                </div>
                <div class="p-4 text-center bg-slate-50/20">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Received</div>
                  <div class="text-xl font-black tracking-tight text-slate-700 font-mono">
                    ₹{{ fmt(totalPaid) }}
                  </div>
                </div>
                <div class="p-4 text-center bg-slate-50/50">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
                    {{ changeAmount > 0.005 ? 'Return Change' : 'Balance' }}
                  </div>
                  <div class="text-xl font-black tracking-tight font-mono" 
                    :class="[
                      changeAmount > 0.005 ? 'text-blue-600' : 
                      (balance <= 0.01 ? 'text-emerald-600' : 'text-rose-600')
                    ]"
                  >
                    ₹{{ fmt(changeAmount > 0.005 ? changeAmount : Math.max(0, balance)) }}
                  </div>
                </div>
              </div>
              <div v-if="isCredit" class="pb-2 text-center border-t border-slate-100 pt-1.5">
                <div class="inline-flex items-center gap-1.5 rounded-full bg-purple-50 px-3 py-0.5 text-[9px] font-bold uppercase tracking-widest text-purple-600 border border-purple-100">
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m5 15 7 7 7-7"/></svg>
                  Credit Ledger Posting
                </div>
              </div>
            </div>

            <!-- PAYMENT METHODS -->
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Method</span>
                <button 
                  @click="toggleCredit"
                  class="rounded-lg px-3 py-1 text-[10px] font-bold uppercase tracking-widest transition-all border"
                  :class="isCredit ? 'bg-purple-600 text-white border-purple-500 shadow-sm' : 'bg-white text-slate-400 border-slate-200 hover:bg-slate-50 hover:text-slate-600'"
                >
                  Credit
                </button>
              </div>

              <div class="grid gap-4" :class="{ 'opacity-30 pointer-events-none grayscale': isCredit }">
                <!-- CASH -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Cash</label>
                    <span v-if="seriesAccounts.cash" class="text-[9px] font-bold text-slate-400 truncate max-w-[150px]">{{ seriesAccounts.cash }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-emerald-500">₹</span>
                    <input 
                      :value="payments.cash === 0 ? '' : payments.cash"
                      @input="e => payments.cash = e.target.value === '' ? 0 : Number(e.target.value)"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-12 text-right font-mono text-lg text-slate-900 outline-none focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-50 transition-all group-hover:border-slate-300 shadow-inner"
                      placeholder="0.00"
                    />
                    <button 
                      @click="settleToField('cash')"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-500 hover:text-emerald-700 p-1 rounded-md hover:bg-emerald-50 transition-colors"
                      title="Settle balance to Cash"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </button>
                  </div>
                </div>

                <!-- UPI -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">UPI / QR</label>
                    <span v-if="seriesAccounts.upi" class="text-[9px] font-bold text-slate-400 truncate max-w-[150px]">{{ seriesAccounts.upi }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-blue-500">₹</span>
                    <input 
                      :value="payments.upi === 0 ? '' : payments.upi"
                      @input="e => payments.upi = e.target.value === '' ? 0 : Number(e.target.value)"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-12 text-right font-mono text-lg text-slate-900 outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50 transition-all group-hover:border-slate-300 shadow-inner"
                      placeholder="0.00"
                    />
                    <button 
                      @click="settleToField('upi')"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-blue-500 hover:text-blue-700 p-1 rounded-md hover:bg-blue-50 transition-colors"
                      title="Settle balance to UPI"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </button>
                  </div>
                </div>

                <!-- BANK -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Bank Transfer</label>
                    <span v-if="seriesAccounts.bank" class="text-[9px] font-bold text-slate-400 truncate max-w-[150px]">{{ seriesAccounts.bank }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-sky-500">₹</span>
                    <input 
                      :value="payments.bank === 0 ? '' : payments.bank"
                      @input="e => payments.bank = e.target.value === '' ? 0 : Number(e.target.value)"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-12 text-right font-mono text-lg text-slate-900 outline-none focus:border-sky-500 focus:bg-white focus:ring-4 focus:ring-sky-50 transition-all group-hover:border-slate-300 shadow-inner"
                      placeholder="0.00"
                    />
                    <button 
                      @click="settleToField('bank')"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-sky-500 hover:text-sky-700 p-1 rounded-md hover:bg-sky-50 transition-colors"
                      title="Settle balance to Bank"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </button>
                  </div>
                </div>

                <!-- DISCOUNT -->
                <div class="space-y-1.5">
                  <div class="flex justify-between items-center px-1">
                    <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Discount / Write-off</label>
                    <span v-if="seriesAccounts.discount" class="text-[9px] font-bold text-slate-400 truncate max-w-[150px]">{{ seriesAccounts.discount }}</span>
                  </div>
                  <div class="relative group">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-rose-500">₹</span>
                    <input 
                      :value="payments.discount === 0 ? '' : payments.discount"
                      @input="e => payments.discount = e.target.value === '' ? 0 : Number(e.target.value)"
                      @focus="$event.target.select()"
                      type="number" 
                      class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-12 text-right font-mono text-lg text-slate-900 outline-none focus:border-rose-500 focus:bg-white focus:ring-4 focus:ring-rose-50 transition-all group-hover:border-slate-300 shadow-inner"
                      placeholder="0.00"
                    />
                    <button 
                      @click="settleToField('discount')"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-rose-500 hover:text-rose-700 p-1 rounded-md hover:bg-rose-50 transition-colors"
                      title="Apply remaining as Discount"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- SUBMIT ACTION -->
        <div class="p-6 border-t border-slate-200 bg-white shadow-[0_-10px_25px_rgba(0,0,0,0.05)]">
          <div v-if="errorMsg" class="mb-4 rounded-xl bg-rose-50 p-3 text-xs font-bold text-rose-600 border border-rose-100">
            {{ errorMsg }}
          </div>
          <div v-if="successMsg" class="mb-4 rounded-xl bg-emerald-50 p-3 text-xs font-bold text-emerald-600 border border-emerald-100">
            {{ successMsg }}
          </div>

          <button 
            @click="processPayment"
            :disabled="!canSubmit"
            class="flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-sm font-bold uppercase tracking-widest transition-all active:scale-95 disabled:bg-slate-100 disabled:text-slate-400 disabled:shadow-none shadow-lg text-white group"
            :class="isCredit ? 'bg-purple-600 hover:bg-purple-700 shadow-purple-100' : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-100'"
          >
            <span v-if="isSubmitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            <span v-else>{{ isCredit ? 'Confirm Credit' : 'Submit Payment' }}</span>
            <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="ml-1 group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
          <div class="mt-4 text-center">
            <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Press <kbd class="rounded border border-slate-300 bg-slate-50 px-1.5 py-0.5 font-mono text-slate-500">F9</kbd> to submit</span>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings } from '../api.js'

// --- STATE ---
const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const isCredit = ref(false)
const isSubmitting = ref(false)
const loadingList = ref(false)
const loadingPreview = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const searchQuery = ref('')
const filterDate = ref(new Date().toISOString().slice(0, 10))

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

// --- COMPUTED ---
const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
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
  // Change only comes from actual money received (Cash, UPI, Bank)
  // net_to_pay = amountToCollect - discount
  // change = (cash + upi + bank) - net_to_pay
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

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function updatePayment(field, value) {
  payments.value[field] = value === '' ? 0 : Number(value)
}

function settleToField(field) {
  if (!selectedInvoice.value) return
  const otherSum = totalPaid.value - (Number(payments.value[field]) || 0)
  const rem = amountToCollect.value - otherSum
  payments.value[field] = parseFloat(Math.max(0, rem).toFixed(2))
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
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
  
  payments.value = { cash: 0, upi: 0, bank: 0, discount: 0 }
  
  try {
    const details = await getInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    
    // Start at 0 so Balance Due shows the full bill amount
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
    const settings = await fetchDashboardSettings()

    // 1. User defaults from settings (highest priority)
    const userDefaults = settings.user_defaults || {}

    // 2. Series defaults if user defaults are missing
    const seriesConfig = (settings.billing_series || []).find(s => s.series === series)

    seriesAccounts.value = {
      cash: userDefaults.cash || seriesConfig?.cash_account || 'Cash',
      upi: userDefaults.upi || seriesConfig?.upi || 'UPI',
      bank: userDefaults.bank_account || seriesConfig?.bank || 'Bank',
      discount: settings.discount_account || 'Write Off'
    }
  } catch (e) {
    console.warn("Could not load accounts", e)
  }
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
  
  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: payments.value.cash,
      upi_amount: payments.value.upi,
      bank_amount: payments.value.bank,
      discount_amount: payments.value.discount,
      is_credit: isCredit.value,
      // Pass the accounts resolved in UI to backend
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

function handleKeydown(e) {
  if (e.key === 'F9') {
    e.preventDefault()
    processPayment()
  }
}

onMounted(() => {
  loadInvoices()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
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
</style>
