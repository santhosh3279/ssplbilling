<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)] font-sans">

    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-[21px] font-bold uppercase tracking-widest text-[var(--color-text)]">Cancellation &amp; Amendment</h1>
      </div>
      <div class="flex items-center gap-3">
        <!-- Mode toggle -->
        <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden text-[18px] font-bold">
          <button
            @click="viewMode = 'submitted'"
            :class="viewMode === 'submitted' ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            class="px-3 py-1.5 transition-colors uppercase tracking-wider"
          >Submitted</button>
          <button
            @click="viewMode = 'cancelled'"
            :class="viewMode === 'cancelled' ? 'bg-[var(--color-danger)] text-[var(--color-text-on-highlight)]' : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            class="px-3 py-1.5 transition-colors uppercase tracking-wider"
          >Cancelled</button>
        </div>
        <!-- Date filter -->
        <div class="flex items-center gap-1">
          <button @click="adjustDate('from', -1)" class="p-1.5 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <input type="date" v-model="fromDate" @change="loadDocs" class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-[18px] text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all" />
          <span class="text-[15px] text-[var(--color-text-muted)] font-bold">TO</span>
          <input type="date" v-model="toDate" @change="loadDocs" class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-[18px] text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all" />
          <button @click="adjustDate('to', 1)" class="p-1.5 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          </button>
        </div>
        <button @click="loadDocs" class="p-1.5 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors" title="Refresh">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
        </button>
      </div>
    </header>

    <!-- TABS -->
    <div class="flex shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="switchTab(tab.value)"
        class="relative px-5 py-3 text-[18px] font-bold uppercase tracking-widest transition-all"
        :class="activeTab === tab.value ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
      >
        {{ tab.label }}
        <span
          v-if="activeTab === tab.value"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--color-info)]"
        ></span>
      </button>
    </div>

    <!-- BODY: split layout -->
    <div class="flex flex-1 overflow-hidden">

      <!-- LEFT: Document List -->
      <aside class="flex w-[400px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <!-- Search -->
        <div class="p-3 border-b border-[var(--color-border)]">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--color-text-muted)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
            <input
              v-model="search"
              @input="debouncedLoad"
              type="text"
              placeholder="Search by name…"
              class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] py-2 pl-9 pr-3 text-[18px] text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)] transition-all"
            />
          </div>
        </div>

        <!-- List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar bg-[var(--color-bg)]/30">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-50">
            <div class="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent mb-2"></div>
            <span class="text-[18px] text-[var(--color-text-muted)]">Loading…</span>
          </div>
          <div v-else-if="!docs.length" class="flex flex-col items-center justify-center py-16 opacity-30">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-3 text-[var(--color-text-muted)]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span class="text-[18px] font-medium text-[var(--color-text-muted)]">No documents found</span>
          </div>
          <div v-else class="px-3 py-3 space-y-2">
            <button
              v-for="doc in docs"
              :key="doc.name"
              @click="selectDoc(doc)"
              class="w-full flex flex-col gap-1 rounded-xl p-3 text-left transition-all border shadow-sm"
              :class="selected?.name === doc.name
                ? viewMode === 'submitted'
                  ? 'bg-[var(--color-info)]/20 border-[var(--color-info)] ring-1 ring-[var(--color-info)]/30'
                  : 'bg-[var(--color-danger)]/20 border-[var(--color-danger)] ring-1 ring-[var(--color-danger)]/30'
                : 'bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] border-[var(--color-border)]'"
            >
              <div class="flex items-start justify-between">
                <span class="font-mono text-[17px] font-bold text-[var(--color-info)]">{{ doc.name }}</span>
                <span class="text-[18px] font-bold text-[var(--color-success)]">₹{{ fmt(docAmount(doc)) }}</span>
              </div>
              <div class="truncate text-[18px] font-semibold text-[var(--color-text)]">{{ docParty(doc) }}</div>
              <div class="flex items-center justify-between mt-0.5">
                <span
                  class="text-[15px] font-bold px-1.5 py-0.5 rounded"
                  :class="viewMode === 'submitted' ? 'bg-[var(--color-success)]/20 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'"
                >{{ viewMode === 'submitted' ? 'SUBMITTED' : 'CANCELLED' }}</span>
                <span class="text-[15px] text-[var(--color-text-muted)]">{{ formatDate(doc.posting_date) }}</span>
              </div>
              <div v-if="doc.amended_from" class="text-[15px] text-[var(--color-text-muted)] truncate">
                Amends: {{ doc.amended_from }}
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- MIDDLE: Preview -->
      <main class="flex flex-1 flex-col overflow-hidden bg-[var(--color-bg)]">
        <div v-if="!selected" class="flex flex-1 flex-col items-center justify-center opacity-30">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mb-4 text-[var(--color-text-muted)]"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          <p class="text-[21px] font-medium text-[var(--color-text-muted)]">Select a document to preview</p>
        </div>

        <template v-else>
          <!-- Preview header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4 shadow-sm z-10">
            <div>
              <h2 class="text-[24px] font-bold text-[var(--color-text)]">{{ selected.name }}</h2>
              <p class="text-[18px] text-[var(--color-text-muted)]">{{ docParty(selected) }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="px-3 py-1 rounded-full text-[15px] font-bold uppercase tracking-wider border"
                :class="detail?.docstatus === 1 ? 'bg-[var(--color-success)]/20 border-[var(--color-success)] text-[var(--color-success)]' : 'bg-[var(--color-danger)]/20 border-[var(--color-danger)] text-[var(--color-danger)]'"
              >{{ detail?.docstatus === 1 ? 'Submitted' : 'Cancelled' }}</span>
            </div>
          </div>

          <!-- Preview body -->
          <div v-if="loadingDetail" class="flex flex-1 items-center justify-center">
            <div class="h-7 w-7 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></div>
          </div>
          <div v-else-if="detail" class="flex-1 overflow-y-auto p-6 custom-scrollbar">
            <div class="mx-auto max-w-5xl rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-6 shadow-md space-y-6">

              <!-- Meta info -->
              <div class="grid grid-cols-2 gap-4 pb-4 border-b border-[var(--color-border)]">
                <div>
                  <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1">{{ partyLabel }}</div>
                  <div class="text-[21px] font-bold text-[var(--color-text)]">{{ docParty(detail) }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Posting Date</div>
                  <div class="text-[21px] font-bold text-[var(--color-text)]">{{ formatDate(detail.posting_date) }}</div>
                </div>
                <div v-if="detail.voucher_type">
                  <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Voucher Type</div>
                  <div class="text-[21px] font-bold text-[var(--color-text)]">{{ detail.voucher_type }}</div>
                </div>
                <div v-if="detail.amended_from" class="col-span-2">
                  <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Amended From</div>
                  <div class="text-[18px] font-mono text-[var(--color-info)]">{{ detail.amended_from }}</div>
                </div>
              </div>

              <!-- Items table (Sales / Purchase Invoice) -->
              <template v-if="activeTab === 'Sales' || activeTab === 'Purchase'">
                <table class="w-full text-left">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] text-[15px] uppercase tracking-wider text-[var(--color-text-muted)]">
                      <th class="py-2 px-1">Item</th>
                      <th class="py-2 px-1 text-right">Qty</th>
                      <th class="py-2 px-1 text-right">Rate</th>
                      <th class="py-2 px-1 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody class="text-[18px] divide-y divide-[var(--color-border)]">
                    <tr v-for="item in detail.items" :key="item.item_code">
                      <td class="py-3 px-1">
                        <div class="font-semibold text-[var(--color-text)]">{{ item.item_name }}</div>
                        <div class="font-mono text-[15px] text-[var(--color-text-muted)]">{{ item.item_code }}</div>
                      </td>
                      <td class="py-3 px-1 text-right text-[var(--color-text)]">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-3 px-1 text-right font-mono text-[var(--color-text)]">₹{{ fmt(item.rate) }}</td>
                      <td class="py-3 px-1 text-right font-mono font-bold text-[var(--color-text)]">₹{{ fmt(item.amount) }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="flex justify-end pt-2 border-t border-[var(--color-border)]">
                  <div class="w-[448px] space-y-1.5">
                    <div v-for="tax in detail.taxes" :key="tax.description" class="flex justify-between text-[18px] text-[var(--color-text-muted)]">
                      <span>{{ tax.description }}</span>
                      <span class="font-mono">₹{{ fmt(tax.tax_amount) }}</span>
                    </div>
                    <div class="flex justify-between pt-2 border-t border-[var(--color-border)] text-[21px] font-bold text-[var(--color-text)]">
                      <span>Grand Total</span>
                      <span class="font-mono text-[var(--color-success)]">₹{{ fmt(detail.grand_total) }}</span>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Journal Entry accounts -->
              <template v-else-if="activeTab === 'Journal'">
                <table class="w-full text-left">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] text-[15px] uppercase tracking-wider text-[var(--color-text-muted)]">
                      <th class="py-2 px-1">Account</th>
                      <th class="py-2 px-1">Party</th>
                      <th class="py-2 px-1 text-right">Debit</th>
                      <th class="py-2 px-1 text-right">Credit</th>
                    </tr>
                  </thead>
                  <tbody class="text-[18px] divide-y divide-[var(--color-border)]">
                    <tr v-for="(acc, idx) in detail.accounts" :key="idx">
                      <td class="py-2.5 px-1 font-semibold text-[var(--color-text)]">{{ acc.account }}</td>
                      <td class="py-2.5 px-1 text-[var(--color-text-muted)]">{{ acc.party || '—' }}</td>
                      <td class="py-2.5 px-1 text-right font-mono text-[var(--color-text)]">{{ acc.debit_in_account_currency ? '₹' + fmt(acc.debit_in_account_currency) : '—' }}</td>
                      <td class="py-2.5 px-1 text-right font-mono text-[var(--color-text)]">{{ acc.credit_in_account_currency ? '₹' + fmt(acc.credit_in_account_currency) : '—' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="flex justify-end pt-2 border-t border-[var(--color-border)]">
                  <div class="text-[21px] font-bold text-[var(--color-text)] font-mono">
                    Total: ₹{{ fmt(detail.total_debit) }}
                  </div>
                </div>
              </template>

              <!-- Payment Entry -->
              <template v-else-if="activeTab === 'Payment'">
                <div class="grid grid-cols-2 gap-3 text-[18px]">
                  <div>
                    <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-0.5">Payment Type</div>
                    <div class="font-bold text-[var(--color-text)]">{{ detail.payment_type }}</div>
                  </div>
                  <div>
                    <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-0.5">Mode</div>
                    <div class="font-bold text-[var(--color-text)]">{{ detail.mode_of_payment }}</div>
                  </div>
                  <div>
                    <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-0.5">Paid Amount</div>
                    <div class="font-bold font-mono text-[var(--color-success)]">₹{{ fmt(detail.paid_amount) }}</div>
                  </div>
                  <div>
                    <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-0.5">Received Amount</div>
                    <div class="font-bold font-mono text-[var(--color-text)]">₹{{ fmt(detail.received_amount) }}</div>
                  </div>
                </div>
                <div v-if="detail.references?.length" class="pt-4 border-t border-[var(--color-border)]">
                  <div class="text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] mb-2">References</div>
                  <table class="w-full text-[18px]">
                    <thead>
                      <tr class="border-b border-[var(--color-border)] text-[15px] uppercase tracking-wider text-[var(--color-text-muted)]">
                        <th class="py-1.5 px-1">Doctype</th>
                        <th class="py-1.5 px-1">Name</th>
                        <th class="py-1.5 px-1 text-right">Allocated</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-[var(--color-border)]">
                      <tr v-for="ref in detail.references" :key="ref.reference_name">
                        <td class="py-2 px-1 text-[var(--color-text-muted)]">{{ ref.reference_doctype }}</td>
                        <td class="py-2 px-1 font-mono text-[var(--color-info)]">{{ ref.reference_name }}</td>
                        <td class="py-2 px-1 text-right font-mono text-[var(--color-text)]">₹{{ fmt(ref.allocated_amount) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT: Actions -->
      <aside class="flex w-[360px] shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl">
        <div class="flex-1 flex flex-col justify-center p-6 space-y-4">
          <div v-if="!selected" class="flex flex-col items-center text-center text-[var(--color-text-muted)] opacity-40">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-2"><path d="m9 9-2 2 2 2"/><path d="m15 9 2 2-2 2"/><path d="M3 12h18"/></svg>
            <p class="text-[18px] uppercase tracking-wider font-medium">Select a document</p>
          </div>

          <template v-else>
            <!-- Summary card -->
            <div class="rounded-2xl border-2 p-5 text-center relative overflow-hidden"
              :class="viewMode === 'submitted' ? 'border-[var(--color-info)] bg-[var(--color-info)]/10' : 'border-[var(--color-danger)] bg-[var(--color-danger)]/10'"
            >
              <div class="absolute top-0 left-0 w-full h-1" :class="viewMode === 'submitted' ? 'bg-[var(--color-info)]' : 'bg-[var(--color-danger)]'"></div>
              <div class="text-[15px] uppercase tracking-widest mb-1" :class="viewMode === 'submitted' ? 'text-[var(--color-info)]' : 'text-[var(--color-danger)]'">
                {{ viewMode === 'submitted' ? 'Total' : 'Cancelled Amount' }}
              </div>
              <div class="text-[45px] font-black font-mono text-[var(--color-text)]">₹{{ fmt(docAmount(selected)) }}</div>
              <div class="mt-2 text-[18px] text-[var(--color-text-muted)]">{{ selected.name }}</div>
            </div>

            <!-- Error / Success -->
            <div v-if="actionError" class="rounded-xl bg-[var(--color-danger)]/20 border border-[var(--color-danger)] p-3 text-[18px] font-bold text-[var(--color-danger)]">
              {{ actionError }}
            </div>
            <div v-if="actionSuccess" class="rounded-xl bg-[var(--color-success)]/20 border border-[var(--color-success)] p-3 text-[18px] font-bold text-[var(--color-success)]">
              {{ actionSuccess }}
            </div>

            <!-- CANCEL button (only for submitted) -->
            <div v-if="viewMode === 'submitted'" class="space-y-3">
              <div class="rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] p-3 text-[18px] text-[var(--color-text-muted)] leading-relaxed">
                Cancelling will reverse all stock and accounting entries for this document. This action cannot be undone directly — use Amend to create a corrected copy.
              </div>
              <button
                @click="confirmCancel"
                :disabled="actioning"
                class="flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-[18px] font-bold uppercase tracking-widest transition-all active:scale-95 disabled:opacity-50 shadow-lg bg-[var(--color-danger)] text-[var(--color-text-on-highlight)] hover:opacity-90"
              >
                <span v-if="actioning && actionType === 'cancel'" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                Cancel Document
              </button>
            </div>

            <!-- AMEND + SUBMIT buttons (for cancelled) -->
            <div v-else class="space-y-3">
              <div class="rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] p-3 text-[18px] text-[var(--color-text-muted)] leading-relaxed">
                Amending creates a new draft copy of this cancelled document for correction. You can then save or submit the amendment.
              </div>
              <button
                @click="doAmend"
                :disabled="actioning || !!amendedName"
                class="flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-[18px] font-bold uppercase tracking-widest transition-all active:scale-95 disabled:opacity-50 shadow-lg bg-[var(--color-warning)] text-[var(--color-text-on-highlight)] hover:opacity-90"
              >
                <span v-if="actioning && actionType === 'amend'" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
                {{ amendedName ? 'Amended: ' + amendedName : 'Amend Document' }}
              </button>

              <button
                v-if="amendedName"
                @click="doSubmitAmended"
                :disabled="actioning"
                class="flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-[18px] font-bold uppercase tracking-widest transition-all active:scale-95 disabled:opacity-50 shadow-lg bg-[var(--color-success)] text-[var(--color-text-on-highlight)] hover:opacity-90"
              >
                <span v-if="actioning && actionType === 'submit'" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Submit Amendment
              </button>
            </div>
          </template>
        </div>
      </aside>
    </div>

    <!-- Confirm Cancel Modal -->
    <div v-if="showCancelModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div class="w-96 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] shadow-2xl p-6 space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-full bg-[var(--color-danger)]/20 flex items-center justify-center text-[var(--color-danger)]">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </div>
          <div>
            <h3 class="text-[21px] font-bold text-[var(--color-text)]">Confirm Cancellation</h3>
            <p class="text-[18px] text-[var(--color-text-muted)]">This will reverse all GL and stock entries.</p>
          </div>
        </div>
        <div class="rounded-xl bg-[var(--color-surface-raised)] border border-[var(--color-border)] p-3 text-[18px] font-mono text-[var(--color-text)]">
          {{ selected?.name }}
        </div>
        <div class="flex gap-3">
          <button @click="showCancelModal = false" class="flex-1 rounded-xl py-3 text-[18px] font-bold uppercase tracking-wider border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            Go Back
          </button>
          <button @click="doCancel" :disabled="actioning" class="flex-1 rounded-xl py-3 text-[18px] font-bold uppercase tracking-wider bg-[var(--color-danger)] text-[var(--color-text-on-highlight)] hover:opacity-90 active:scale-95 transition-all disabled:opacity-50">
            <span v-if="actioning">Cancelling…</span>
            <span v-else>Yes, Cancel</span>
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.cancellation_api'

const tabs = [
  { label: 'Sales',    value: 'Sales',    doctype: 'Sales Invoice' },
  { label: 'Purchase', value: 'Purchase', doctype: 'Purchase Invoice' },
  { label: 'Journal',  value: 'Journal',  doctype: 'Journal Entry' },
  { label: 'Payment',  value: 'Payment',  doctype: 'Payment Entry' },
]

function getTodayIST() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
}

// --- state ---
const activeTab   = ref('Sales')
const viewMode    = ref('submitted')  // 'submitted' | 'cancelled'
const fromDate    = ref(getTodayIST())
const toDate      = ref(getTodayIST())
const search      = ref('')
const docs        = ref([])
const selected    = ref(null)
const detail      = ref(null)
const loadingList = ref(false)
const loadingDetail = ref(false)
const actioning   = ref(false)
const actionType  = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const amendedName = ref('')
const showCancelModal = ref(false)

// --- computed ---
const currentDoctype = computed(() => tabs.find(t => t.value === activeTab.value)?.doctype ?? 'Sales Invoice')

const partyLabel = computed(() => {
  if (activeTab.value === 'Sales')    return 'Customer'
  if (activeTab.value === 'Purchase') return 'Supplier'
  if (activeTab.value === 'Payment')  return 'Party'
  return 'Remarks'
})

// --- helpers ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function docParty(doc) {
  if (!doc) return ''
  return doc.customer_name || doc.supplier_name || doc.party_name || doc.user_remark || doc.party || doc.name
}

function docAmount(doc) {
  if (!doc) return 0
  return doc.grand_total ?? doc.total_debit ?? doc.paid_amount ?? 0
}

// --- load list ---
async function loadDocs() {
  loadingList.value = true
  selected.value = null
  detail.value = null
  actionError.value = ''
  actionSuccess.value = ''
  amendedName.value = ''
  try {
    const method = viewMode.value === 'submitted'
      ? `${API}.get_cancellable_documents`
      : `${API}.get_cancelled_documents`
    docs.value = await frappeGet(method, {
      doctype: currentDoctype.value,
      from_date: fromDate.value,
      to_date: toDate.value,
      search: search.value,
      limit: 100,
    })
  } catch (e) {
    actionError.value = e.message
  } finally {
    loadingList.value = false
  }
}

async function selectDoc(doc) {
  if (selected.value?.name === doc.name) return
  selected.value = doc
  detail.value = null
  actionError.value = ''
  actionSuccess.value = ''
  amendedName.value = ''
  loadingDetail.value = true
  try {
    detail.value = await frappeGet(`${API}.get_document_detail`, {
      doctype: currentDoctype.value,
      name: doc.name,
    })
  } catch (e) {
    actionError.value = e.message
  } finally {
    loadingDetail.value = false
  }
}

function switchTab(val) {
  activeTab.value = val
  search.value = ''
  loadDocs()
}

function adjustDate(field, delta) {
  const ref_ = field === 'from' ? fromDate : toDate
  const d = new Date(ref_.value)
  d.setDate(d.getDate() + delta)
  ref_.value = d.toISOString().slice(0, 10)
  loadDocs()
}

let searchTimer = null
function debouncedLoad() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadDocs, 280)
}

// --- actions ---
function confirmCancel() {
  actionError.value = ''
  actionSuccess.value = ''
  showCancelModal.value = true
}

async function doCancel() {
  actioning.value = true
  actionType.value = 'cancel'
  try {
    await frappePost(`${API}.cancel_document`, {
      doctype: currentDoctype.value,
      name: selected.value.name,
    })
    showCancelModal.value = false
    actionSuccess.value = `${selected.value.name} cancelled successfully.`
    await loadDocs()
  } catch (e) {
    showCancelModal.value = false
    actionError.value = e.message
  } finally {
    actioning.value = false
    actionType.value = ''
  }
}

async function doAmend() {
  if (amendedName.value) return
  actioning.value = true
  actionType.value = 'amend'
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const res = await frappePost(`${API}.amend_document`, {
      doctype: currentDoctype.value,
      name: selected.value.name,
    })
    amendedName.value = res.name
    actionSuccess.value = `Amendment created: ${res.name}. Review and submit when ready.`
  } catch (e) {
    actionError.value = e.message
  } finally {
    actioning.value = false
    actionType.value = ''
  }
}

async function doSubmitAmended() {
  actioning.value = true
  actionType.value = 'submit'
  actionError.value = ''
  actionSuccess.value = ''
  try {
    await frappePost(`${API}.submit_amended_document`, {
      doctype: currentDoctype.value,
      name: amendedName.value,
    })
    actionSuccess.value = `${amendedName.value} submitted successfully.`
    amendedName.value = ''
    await loadDocs()
  } catch (e) {
    actionError.value = e.message
  } finally {
    actioning.value = false
    actionType.value = ''
  }
}

// reload list when viewMode changes
watch(viewMode, () => loadDocs())

onMounted(() => loadDocs())
</script>
