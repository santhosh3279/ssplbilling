<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)] font-sans">

    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-[var(--color-text)]">PURCHASE SUBMISSION</h1>
        <div class="h-4 w-px bg-[var(--color-surface-raised)] mx-2"></div>
        <span class="rounded-full bg-[var(--color-warning)]/20 px-3 py-1 text-[14px] font-semibold text-[var(--color-warning)] border border-[var(--color-warning)]">
          {{ invoices.length }} Pending Purchases
        </span>
      </div>
      <div class="flex items-center gap-4">
        <button
          @click="router.push('/purchase-invoice')"
          class="flex items-center gap-2 rounded bg-[var(--color-warning)] px-3 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-warning)]/80 active:scale-95 shadow-md"
        >
          <span>✍️</span> Purchase Invoice
        </button>
        <div class="h-8 w-px bg-[var(--color-border)] mx-1"></div>
        <div class="text-right">
          <div class="text-[12px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Current Date</div>
          <div class="text-[17px] font-medium text-[var(--color-text)]">{{ todayStr }}</div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      
      <!-- LEFT PANEL: INVOICE LIST -->
      <aside class="flex w-80 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="p-4">
          <div class="flex gap-2">
            <div class="relative flex-1">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--color-text-muted)]">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              </span>
              <input
                v-model="searchQuery"
                @input="debouncedSearch"
                type="text"
                placeholder="Search PINV or supplier..."
                class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-9 pr-4 text-[15px] text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)] transition-all"
              />
            </div>
            <button
              @click="loadInvoices"
              class="rounded-lg bg-[var(--color-surface-raised)] px-3 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-all border border-[var(--color-border)] flex items-center justify-center active:scale-95"
              title="Refresh List"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-[var(--color-bg)]/30">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-50">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-warning)] border-t-transparent mb-2"></div>
            <span class="text-[14px] text-[var(--color-text-muted)]">Loading purchases...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-20 opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4 text-[var(--color-text-muted)]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-[17px] font-medium text-[var(--color-text-muted)]">No draft purchases found</span>
          </div>
          <div v-else class="px-3 pb-4 space-y-4">
            <div v-for="(bucket, idx) in invoicesByDate" :key="bucket.date" :class="{ 'mt-4': idx > 0 }" class="space-y-2">
              <div class="sticky top-0 bg-[var(--color-highlight)] py-[3px] px-[4px] text-[18px] font-bold uppercase tracking-wider text-[var(--color-text-on-highlight)] border-b border-[var(--color-border)] z-10 flex items-center justify-between">
                <span>{{ bucket.formattedDate }}</span>
                <span class="rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-bold text-[var(--color-text-on-highlight)] border border-white/10">
                  {{ bucket.invoices.length }}
                </span>
              </div>
              <div class="space-y-2">
                <button
                  v-for="inv in bucket.invoices"
                  :key="inv.name"
                  :data-inv-name="inv.name"
                  @click="selectInvoice(inv)"
                  class="flex w-full flex-col gap-1 rounded-xl py-[5px] px-2 text-left transition-all outline-none group border shadow-sm"
                  :class="selectedInvoice?.name === inv.name
                    ? 'bg-[var(--color-warning)] border-[var(--color-warning)] ring-2 ring-amber-500/30'
                    : 'bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] border-[var(--color-border)]'"
                >
                  <div class="flex items-start justify-between">
                    <span class="font-mono text-[16.5px] font-bold" :class="selectedInvoice?.name === inv.name ? 'text-[var(--color-text-on-highlight)]' : 'text-[var(--color-warning)]'">
                      {{ inv.name }}
                    </span>
                    <span class="text-[18px] font-bold font-mono" :class="selectedInvoice?.name === inv.name ? 'text-[var(--color-text-on-highlight)]' : 'text-[var(--color-success)]'">
                      {{ fmt(inv.rounded_total || inv.grand_total) }}
                    </span>
                  </div>
                  <div class="truncate text-[21px] font-semibold" :class="selectedInvoice?.name === inv.name ? 'text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)]'">
                    {{ inv.supplier_name }}
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- MIDDLE PANEL: PREVIEW -->
      <main class="flex flex-1 flex-col bg-[var(--color-bg)] overflow-hidden">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-6 text-[var(--color-text-muted)]"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <p class="text-lg font-medium text-[var(--color-text-muted)]">Select a purchase to preview</p>
        </div>

        <template v-else>
          <!-- PREVIEW HEADER -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-8 py-4 shadow-sm z-10">
            <div class="flex items-center gap-4">
              <div>
                <h2 class="text-xl font-bold text-[var(--color-text)] leading-none mb-1">{{ selectedInvoice.name }}</h2>
                <p class="text-[17px] font-medium text-[var(--color-text-muted)]">{{ selectedInvoice.supplier_name }}</p>
              </div>
              <div class="flex items-center gap-2 text-[14px] text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] px-2.5 py-1 rounded-md border border-[var(--color-border)]">
                <span>Date: <span class="font-bold text-[var(--color-text)]">{{ formatDate(selectedInvoice.posting_date) }}</span></span>
                <span class="h-3 w-px bg-[var(--color-border)]"></span>
                <span class="font-bold uppercase tracking-wider text-[var(--color-warning)] text-[12px]">DRAFT</span>
              </div>
            </div>
            <div class="flex gap-3">
              <!-- MODIFY BUTTON -->
              <button
                class="flex items-center gap-2 rounded-lg bg-[var(--color-surface-raised)] px-4 py-2 text-[17px] font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-all border border-[var(--color-border)] shadow-sm active:scale-95"
                @click="showModifyModal = true"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)]"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
                <span>Modify</span>
              </button>
              <!-- BARCODE PRINT BUTTON -->
              <button
                class="flex items-center gap-2 rounded-lg bg-[var(--color-surface-raised)] px-4 py-2 text-[17px] font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-all border border-[var(--color-border)] shadow-sm active:scale-95"
                @click="handleBarcodePrint"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)]"><path d="M3 5v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2z"/><path d="M7 7h10"/><path d="M7 12h10"/><path d="M7 17h10"/></svg>
                <span>Print Barcodes</span>
              </button>
              <!-- BILL PRINT BUTTON -->
              <button
                class="flex items-center gap-2 rounded-lg bg-[var(--color-surface-raised)] px-4 py-2 text-[17px] font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition-all border border-[var(--color-border)] shadow-sm active:scale-95"
                @click="handleBillPrint"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)]"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
                <span>Print Bill</span>
              </button>
            </div>
          </div>

          <!-- PREVIEW CONTENT -->
          <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div class="flex items-start gap-6">
            <div class="min-w-0 flex-1 rounded-2xl bg-[var(--color-surface)] p-8 shadow-md border border-[var(--color-border)]">

              <table class="w-full text-left">
                <thead>
                  <tr class="border-b border-[var(--color-border)] text-[16.5px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                    <th class="py-1.5 px-2">Code</th>
                    <th class="py-1.5 px-2">Item</th>
                    <th class="py-1.5 px-2 text-right">Qty</th>
                    <th class="py-1.5 px-2 text-right">Rate</th>
                    <th class="py-1.5 px-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody class="text-[21px]">
                  <tr v-for="item in previewItems" :key="item.item_code" class="border-b border-[var(--color-border)]">
                    <td class="py-2 px-2 text-[16.5px] text-[var(--color-text-muted)] font-mono">{{ item.item_code }}</td>
                    <td class="py-2 px-2">
                      <div class="font-bold text-[var(--color-text)]">{{ item.item_name }}</div>
                    </td>
                    <td class="py-2 px-2 text-right text-[var(--color-text)] font-medium">{{ item.qty }} {{ item.uom }}</td>
                    <td class="py-2 px-2 text-right text-[var(--color-text)] font-mono">{{ fmt(item.rate) }}</td>
                    <td class="py-2 px-2 text-right font-bold text-[var(--color-text)] font-mono">{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>

              <div class="mt-8 flex justify-end">
                <div class="w-80 space-y-3">
                  <div class="flex justify-between border-t border-[var(--color-border)] pt-3 text-[27px] font-bold text-[var(--color-text)]">
                    <span>Rounded Total</span>
                    <span class="font-mono text-[var(--color-warning)]">{{ fmt(selectedInvoice.rounded_total || selectedInvoice.grand_total) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- UNLINKED PAYMENTS / DEBIT NOTES PANE -->
            <div class="w-80 shrink-0 rounded-2xl bg-[var(--color-surface)] shadow-md border border-[var(--color-border)] overflow-hidden">
              <div class="px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
                <div class="text-[12px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Unlinked Payments / Debit Notes</div>
              </div>

              <div v-if="loadingUnlinked" class="flex items-center justify-center gap-2 py-8 opacity-50">
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-warning)] border-t-transparent"></div>
                <span class="text-[13px] text-[var(--color-text-muted)]">Checking supplier...</span>
              </div>

              <div v-else-if="unlinkedEntries.length === 0" class="py-8 px-4 text-center opacity-40">
                <span class="text-[13px] font-medium text-[var(--color-text-muted)]">No unlinked payments or debit notes for this supplier</span>
              </div>

              <template v-else>
                <div class="max-h-96 overflow-y-auto custom-scrollbar divide-y divide-[var(--color-border)]">
                  <div v-for="entry in unlinkedEntries" :key="entry.doctype + entry.name" class="p-3 space-y-1.5">
                    <div class="flex items-center justify-between gap-2">
                      <span class="font-mono text-[13px] font-bold text-[var(--color-warning)] truncate">{{ entry.name }}</span>
                      <div class="flex items-center gap-1 shrink-0">
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wider border"
                          :class="entry.doctype === 'Purchase Invoice'
                            ? 'bg-red-500/10 text-red-500 border-red-500/20'
                            : 'bg-blue-500/10 text-blue-500 border-blue-500/20'"
                        >
                          {{ entry.doctype === 'Purchase Invoice' ? 'Debit Note' : entry.doctype === 'Journal Entry' ? 'Journal' : 'Payment' }}
                        </span>
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wider border"
                          :class="entry.direction === 'Dr'
                            ? 'bg-green-500/10 text-green-500 border-green-500/20'
                            : 'bg-amber-500/10 text-amber-500 border-amber-500/20'"
                        >
                          {{ entry.direction === 'Dr' ? 'Debit' : 'Credit' }}
                        </span>
                      </div>
                    </div>
                    <div class="flex items-center justify-between text-[12px] text-[var(--color-text-muted)]">
                      <span>{{ formatDate(entry.posting_date) }}</span>
                      <span>Avail: <span class="font-mono font-bold" :class="entry.direction === 'Dr' ? 'text-[var(--color-success)]' : 'text-amber-500'">{{ fmt(entry.available) }}</span></span>
                    </div>
                    <div v-if="entry.direction === 'Dr'" class="flex items-center gap-2">
                      <label class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] shrink-0">Link Amt</label>
                      <input
                        v-model.number="entry.alloc"
                        @input="clampAlloc(entry)"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2 py-1 text-right text-[14px] font-mono font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-warning)] transition-all"
                      />
                    </div>
                    <div v-else class="text-[11px] italic text-[var(--color-text-muted)] opacity-70">
                      Credit entry — cannot be linked to this bill
                    </div>
                  </div>
                </div>

                <div class="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 space-y-1">
                  <div class="flex justify-between text-[13px] font-bold">
                    <span class="uppercase tracking-wider text-[var(--color-text-muted)]">Total to Link</span>
                    <span class="font-mono text-[var(--color-success)]">{{ fmt(totalToLink) }}</span>
                  </div>
                  <div class="flex justify-between text-[13px] font-bold">
                    <span class="uppercase tracking-wider text-[var(--color-text-muted)]">Balance Payable</span>
                    <span class="font-mono text-[var(--color-warning)]">{{ fmt((selectedInvoice.rounded_total || selectedInvoice.grand_total) - totalToLink) }}</span>
                  </div>
                </div>
              </template>
            </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT PANEL: SUBMISSION -->
      <aside class="flex w-96 shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-3 mx-auto"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            <p class="text-[14px] font-medium uppercase tracking-wider">Select purchase to submit</p>
          </div>

          <template v-else>
            <!-- SUMMARY CARD -->
            <div class="rounded-2xl bg-[var(--color-warning)]/20 border-2 border-[var(--color-warning)] p-6 relative overflow-hidden text-center">
              <div class="absolute top-0 left-0 w-full h-1 bg-[var(--color-warning)]"></div>
              <div class="text-[12px] font-bold uppercase tracking-widest text-[var(--color-warning)] mb-2">Total Payable to Supplier</div>
              <div class="text-4xl font-black tracking-tight text-[var(--color-text)] font-mono">
                {{ fmt(selectedInvoice.rounded_total || selectedInvoice.grand_total) }}
              </div>
              <div class="mt-4 inline-flex items-center gap-1.5 rounded-full bg-[var(--color-surface-raised)] px-3 py-1 text-[12px] font-bold uppercase tracking-widest text-[var(--color-text)]">
                Credit Purchase
              </div>
            </div>

            <div class="space-y-4">
              <div class="p-4 rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)]">
                <div class="text-[12px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Submission Note</div>
                <p class="text-[14px] text-[var(--color-text)] leading-relaxed">
                  Submitting this invoice will update your stock and post the liability to the supplier's ledger as a credit entry.
                </p>
              </div>

              <!-- SUBMIT ACTION -->
              <div class="pt-4">
                <div v-if="errorMsg" class="mb-4 rounded-xl bg-[var(--color-danger)]/20 p-3 text-[14px] font-bold text-[var(--color-danger)] border border-[var(--color-danger)]">
                  {{ errorMsg }}
                </div>
                <div v-if="successMsg" class="mb-4 rounded-xl bg-[var(--color-success)]/20 p-3 text-[14px] font-bold text-[var(--color-success)] border border-[var(--color-success)]">
                  {{ successMsg }}
                </div>

                <button
                  @click="confirmSubmission"
                  :disabled="isSubmitting"
                  class="flex w-full items-center justify-center gap-2 rounded-2xl py-5 text-[17px] font-bold uppercase tracking-widest transition-all active:scale-95 disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)] disabled:shadow-none shadow-lg text-[var(--color-text-on-highlight)] bg-[var(--color-warning)] hover:bg-[var(--color-warning)] shadow-amber-900/50 group"
                >
                  <span v-if="isSubmitting" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                  <span v-else>Confirm & Submit Purchase</span>
                  <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="ml-1 group-hover:translate-x-1 transition-transform"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </button>
              </div>
            </div>
          </template>
        </div>
      </aside>
    </div>

    <!-- Print Options Modal -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="selectedInvoice?.name"
      doctype="Purchase Invoice"
      @close="showPrintModal = false"
    />

    <!-- Barcode Print Subwindow -->
    <BarcodePrintPage
      v-if="showBarcodeModal"
      isSubWindow
      :billNo="selectedInvoice?.name"
      :items="previewItems"
      @close="showBarcodeModal = false"
    />

    <!-- MODIFY BILL SUBWINDOW -->
    <div v-if="showModifyModal" class="fixed inset-0 z-[100] bg-[var(--color-bg)]">
      <PurchaseInvoice 
        is-subwindow 
        :invoice-name="selectedInvoice?.name" 
        @close="handleModifyClose" 
      />
    </div>

    <!-- LANDED COST VOUCHER WARNING MODAL -->
    <Warning
      :show="showLcvWarningModal"
      title="Create Landed Cost Voucher?"
      message="Would you like to distribute transport or other landed cost charges for this Purchase Invoice?"
      @close="handleLcvWarningClose"
      @confirm="handleLcvWarningConfirm"
    />

    <!-- LANDED COST VOUCHER SUBWINDOW -->
    <div v-if="showLcvModal" class="fixed inset-0 z-[100] bg-[var(--color-bg)]">
      <LandCostVoucher
        is-subwindow
        prelink-doc-type="Purchase Invoice"
        :prelink-doc-name="lastSubmittedInvoice?.name"
        :prelink-company="lastSubmittedInvoice?.company"
        :prelink-supplier="lastSubmittedInvoice?.supplier"
        :prelink-posting-date="lastSubmittedInvoice?.posting_date"
        :prelink-grand-total="lastSubmittedInvoice?.grand_total"
        @close="handleLcvClose"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { onBillPanelUpdate } from '../composables/useBillPanelSync.js'
import { useRouter } from 'vue-router'
import { fetchPurchaseInvoices, getPurchaseInvoiceDetails, submitPurchaseInvoice, frappeGet, frappePost, linkSupplierToItems } from '../api.js'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import BarcodePrintPage from './BarcodePrintPage.vue'
import PurchaseInvoice from './PurchaseInvoice.vue'
import Warning from '../components/Warning.vue'
import LandCostVoucher from './land_cost_voucher.vue'

const router = useRouter()

// --- STATE ---
const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const isSubmitting = ref(false)
const loadingList = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const showPrintModal = ref(false)
const showBarcodeModal = ref(false)
const showModifyModal = ref(false)
const showLcvWarningModal = ref(false)
const showLcvModal = ref(false)
const lastSubmittedInvoice = ref(null)
const unlinkedEntries = ref([])
const loadingUnlinked = ref(false)

useSubwindowWatcher(showPrintModal)
useSubwindowWatcher(showBarcodeModal)
useSubwindowWatcher(showModifyModal)
useSubwindowWatcher(showLcvWarningModal)
useSubwindowWatcher(showLcvModal)

const searchQuery = ref('')

const props = defineProps({ isSubWindow: Boolean })
if (props.isSubWindow) useSubwindow()

// --- SHORTCUTS ---
useShortcuts({
  'ARROWUP':   () => navigateBills(-1),
  'ARROWDOWN': () => navigateBills(1),
  'ENTER':     () => { if (selectedInvoice.value && !isSubmitting.value) confirmSubmission() },
  'ESCAPE':    () => window.history.back(),
  'F5':        () => loadInvoices(),
  'F9':        () => { if (selectedInvoice.value && !isSubmitting.value) confirmSubmission() },
  'F10':       () => { if (selectedInvoice.value) handleBarcodePrint() },
  'F11':       () => { if (selectedInvoice.value) handleBillPrint() },
  'CTRL+M':    () => { if (selectedInvoice.value) showModifyModal.value = true }
}, props.isSubWindow ? 'subwindow' : 'local')

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

// --- COMPUTED ---
const todayStr = computed(() => {
  return new Date().toLocaleDateString('en-IN', { 
    timeZone: 'Asia/Kolkata',
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
  })
})

const invoicesByDate = computed(() => {
  const groups = {}
  for (const inv of invoices.value) {
    const date = inv.posting_date || 'Unknown Date'
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(inv)
  }
  
  return Object.keys(groups)
    .sort((a, b) => new Date(b) - new Date(a))
    .map(date => ({
      date,
      formattedDate: formatDate(date),
      invoices: groups[date]
    }))
})

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2, maximumFractionDigits: 2
  })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

async function loadInvoices() {
  loadingList.value = true
  try {
    const all = await fetchPurchaseInvoices(searchQuery.value, 500, '', true)
    invoices.value = all.filter(i => i.docstatus === 0).sort((a, b) => {
      const dateA = new Date(a.posting_date || 0)
      const dateB = new Date(b.posting_date || 0)
      if (dateA - dateB !== 0) {
        return dateB - dateA
      }
      return b.name.localeCompare(a.name)
    })
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

  selectedInvoice.value = inv
  previewItems.value = []
  unlinkedEntries.value = []
  errorMsg.value = ''
  successMsg.value = ''

  try {
    const details = await getPurchaseInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    loadUnlinkedEntries(details.supplier, inv.name)
  } catch (e) {
    errorMsg.value = "Failed to load details: " + e.message
  }
}

// --- UNLINKED PAYMENTS / DEBIT NOTES ---
const totalToLink = computed(() =>
  unlinkedEntries.value.reduce((sum, e) => sum + Number(e.alloc || 0), 0)
)

async function loadUnlinkedEntries(supplier, invName) {
  if (!supplier) return
  loadingUnlinked.value = true
  try {
    const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
      party_type: 'Supplier',
      party: supplier
    })
    // Ignore stale responses if the user has moved to another invoice
    if (selectedInvoice.value?.name !== invName) return

    const rows = []
    for (const p of res.payment_entries || []) {
      rows.push({
        doctype: 'Payment Entry',
        name: p.name,
        posting_date: p.posting_date,
        direction: p.direction,
        available: Number(p.unallocated_amount || 0),
        reference_row: null,
        alloc: null
      })
    }
    for (const j of res.journal_entries || []) {
      rows.push({
        doctype: 'Journal Entry',
        name: j.name,
        posting_date: j.posting_date,
        direction: j.direction,
        available: Number(j.unallocated_amount || 0),
        reference_row: j.reference_row || null,
        alloc: null
      })
    }
    // Only debit notes (return PIs) — regular outstanding bills are not shown here
    for (const i of (res.invoices || []).filter(i => i.doctype === 'Purchase Invoice' && i.direction === 'Dr')) {
      rows.push({
        doctype: 'Purchase Invoice',
        name: i.name,
        posting_date: i.posting_date,
        direction: 'Dr',
        available: Number(i.outstanding_amount || 0),
        reference_row: null,
        alloc: null
      })
    }
    // Linkable debit entries first
    rows.sort((a, b) => (a.direction === 'Dr' ? 0 : 1) - (b.direction === 'Dr' ? 0 : 1))
    unlinkedEntries.value = rows
  } catch (err) {
    console.warn('Failed to load unlinked entries for supplier:', err)
  } finally {
    loadingUnlinked.value = false
  }
}

function clampAlloc(entry) {
  let val = Number(entry.alloc || 0)
  if (val < 0) val = 0
  if (val > entry.available) val = entry.available
  // Total linked cannot exceed the bill amount
  const billTotal = Number(selectedInvoice.value?.rounded_total || selectedInvoice.value?.grand_total || 0)
  const others = unlinkedEntries.value.reduce(
    (sum, e) => (e === entry ? sum : sum + Number(e.alloc || 0)), 0
  )
  if (others + val > billTotal) val = Math.max(0, billTotal - others)
  entry.alloc = val
}

function handleBarcodePrint() {
  if (!selectedInvoice.value) return
  showBarcodeModal.value = true
}

function handleBillPrint() {
  showPrintModal.value = true
}

async function handleModifyClose() {
  showModifyModal.value = false
  if (selectedInvoice.value) {
    const currentName = selectedInvoice.value.name
    await loadInvoices()
    const inv = invoices.value.find(i => i.name === currentName)
    if (inv) {
      selectedInvoice.value = null
      await nextTick()
      await selectInvoice(inv)
    }
  }
}

async function confirmSubmission() {
  if (!selectedInvoice.value || isSubmitting.value) return

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    const invName = selectedInvoice.value.name
    const supplier = selectedInvoice.value.supplier
    const grandTotal = selectedInvoice.value.rounded_total || selectedInvoice.value.grand_total

    const allocations = unlinkedEntries.value
      .filter(e => Number(e.alloc) > 0)
      .map(e => ({
        payment_type: e.doctype,
        payment_name: e.name,
        reference_row: e.reference_row,
        invoice_type: 'Purchase Invoice',
        invoice_name: invName,
        amount: Number(e.alloc),
        unreconciled_amount: e.available
      }))

    await submitPurchaseInvoice(invName)

    const itemCodes = (previewItems.value || [])
      .filter(i => i.item_code)
      .map(i => i.item_code)
    if (itemCodes.length > 0) {
      try {
        await linkSupplierToItems(supplier, itemCodes)
      } catch (err) {
        console.error('Failed to link supplier to items:', err)
      }
    }

    if (allocations.length > 0) {
      try {
        await frappePost('ssplbilling.api.reconcile_api.post_reconciliation', {
          party_type: 'Supplier',
          party: supplier,
          allocations: JSON.stringify(allocations)
        })
      } catch (err) {
        errorMsg.value = 'Bill submitted, but linking payments failed: ' + (err.message || err)
      }
    }

    const nameToRemove = selectedInvoice.value.name
    lastSubmittedInvoice.value = {
      name: invName,
      company: selectedInvoice.value.company,
      supplier: supplier,
      posting_date: selectedInvoice.value.posting_date,
      grand_total: grandTotal
    }
    invoices.value = invoices.value.filter(i => i.name !== nameToRemove)
    selectedInvoice.value = null
    previewItems.value = []
    unlinkedEntries.value = []
    successMsg.value = ''

    loadInvoices()
    showLcvWarningModal.value = true

  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

function handleLcvWarningClose() {
  showLcvWarningModal.value = false
  lastSubmittedInvoice.value = null
}

function handleLcvWarningConfirm() {
  showLcvWarningModal.value = false
  showLcvModal.value = true
}

function handleLcvClose() {
  showLcvModal.value = false
  lastSubmittedInvoice.value = null
  loadInvoices()
}

onMounted(() => {
  loadInvoices()
  // No series filter on this desk — refresh on any Purchase Invoice change.
  _billPanelCleanup = onBillPanelUpdate('Purchase Invoice', null, loadInvoices)
})

let _billPanelCleanup = null

onUnmounted(() => {
  _billPanelCleanup?.()
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
  background: #475569;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
