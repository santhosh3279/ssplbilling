<template>
  <div class="fixed inset-x-0 top-0 flex h-[100dvh] flex-col bg-[var(--color-bg)] text-[var(--color-text)]" :style="viewportStyle">
    <!-- Header: back · title · print / refresh. Turns red when posting on a date other than today -->
    <header
      class="z-20 shrink-0 border-b border-[var(--color-border)] px-3 pb-2 pt-[max(0.75rem,env(safe-area-inset-top))] shadow-sm"
      :class="postingDate !== getTodayIST() ? 'bg-red-600 text-white' : 'bg-[var(--color-surface)]'"
    >
      <div class="flex items-center gap-2">
        <button type="button" aria-label="Back" class="rounded-lg px-2 py-1 text-lg" @click="goBack">←</button>
        <div class="min-w-0 flex-1">
          <template v-if="selectedInvoice">
            <h1 class="truncate text-base font-bold leading-tight">
              {{ selectedInvoice.name }}
              <span v-if="selectedInvoice.mop" class="ml-1 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                :class="selectedInvoice.mop === 'Cash' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'"
              >{{ selectedInvoice.mop }}</span>
              <span v-if="selectedInvoice.is_return" class="ml-1 rounded bg-[var(--color-danger)]/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--color-danger)]">Return</span>
            </h1>
            <div class="truncate text-[11px] opacity-80">
              {{ formatDate(selectedInvoice.posting_date) }}<template v-if="formatTime(selectedInvoice.posting_time)"> · {{ formatTime(selectedInvoice.posting_time) }}</template>
            </div>
          </template>
          <template v-else>
            <h1 class="truncate text-base font-bold leading-tight">Cashier</h1>
            <div class="truncate text-[11px] opacity-80">{{ invoices.length }} draft {{ invoices.length === 1 ? 'bill' : 'bills' }}</div>
          </template>
        </div>
        <button
          v-if="selectedInvoice"
          type="button"
          class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm font-semibold active:bg-[var(--color-surface-raised)]"
          @click="showPrintModal = true"
        >Print</button>
        <button
          v-else
          type="button"
          aria-label="Refresh bills"
          class="shrink-0 rounded-lg border border-[var(--color-border)] p-2 active:bg-[var(--color-surface-raised)]"
          @click="loadInvoices"
        >
          <svg :class="{ 'animate-spin': loadingList }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
        </button>
      </div>

      <!-- List view: series filter + search -->
      <div v-if="!selectedInvoice" class="mt-2 flex gap-2">
        <div class="series-dropdown-container relative w-2/5 shrink-0">
          <button
            type="button"
            class="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-2 text-sm font-semibold text-[var(--color-text)]"
            @click="showSeriesDropdown = !showSeriesDropdown"
          >
            <span class="truncate">{{ sidebarSeries.length === availableSeries.length ? 'All Series' : (sidebarSeries.length > 0 ? sidebarSeries[0].replace(/#/g, '') + (sidebarSeries.length > 1 ? '..' : '') : 'None') }}</span>
            <span class="text-xs" :class="{ 'rotate-180': showSeriesDropdown }">▾</span>
          </button>
          <div v-if="showSeriesDropdown" class="absolute left-0 top-full z-50 mt-1 max-h-72 w-64 overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-1 text-[var(--color-text)] shadow-2xl">
            <label class="flex items-center gap-3 border-b border-[var(--color-border)] px-3 py-2.5 text-sm font-bold uppercase">
              <input type="checkbox" class="h-4 w-4" :checked="sidebarSeries.length === availableSeries.length" @change="toggleAllSeries" />
              All Series
            </label>
            <label v-for="s in availableSeries" :key="s" class="flex items-center gap-3 px-3 py-2.5 text-sm font-semibold">
              <input type="checkbox" class="h-4 w-4" :checked="isSeriesSelected(s)" @change="toggleSeries(s)" />
              {{ s.replace(/#/g, '') }}
            </label>
          </div>
        </div>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search bills…"
          class="min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-focus)]"
          @input="debouncedSearch"
        />
      </div>
    </header>

    <!-- ==================== LIST VIEW ==================== -->
    <main v-if="!selectedInvoice" class="relative min-h-0 flex-1 overflow-y-auto">
      <p v-if="errorMsg" class="mx-3 mt-3 rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-semibold text-[var(--color-danger)]">{{ errorMsg }}</p>
      <div v-if="loadingList && !invoices.length" class="py-16 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading bills…</div>
      <div v-else-if="!invoices.length" class="px-6 py-16 text-center">
        <div class="text-base font-bold text-[var(--color-text-muted)]">No bills found</div>
        <div class="mt-1 text-xs uppercase tracking-widest text-[var(--color-text-muted)]">Pending drafts will appear here</div>
      </div>
      <div v-else class="space-y-4 p-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
        <section v-for="bucket in bucketedInvoices" :key="bucket.date" class="space-y-2">
          <div class="flex items-center justify-between rounded-lg bg-[var(--color-highlight)] px-3 py-1 text-[var(--color-text-on-highlight)]">
            <span class="text-sm font-black uppercase tracking-wider">{{ bucket.label }}</span>
            <span class="text-[11px] font-bold uppercase">{{ bucket.invoices.length }} {{ bucket.invoices.length === 1 ? 'bill' : 'bills' }}</span>
          </div>
          <button
            v-for="inv in bucket.invoices"
            :key="inv.name"
            type="button"
            class="block w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left shadow-sm active:scale-[0.98] active:bg-[var(--color-surface-raised)]"
            @click="selectInvoice(inv)"
          >
            <div class="flex items-center gap-2 text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
              <span class="rounded bg-[var(--color-surface-raised)] px-1.5 py-0.5">Draft</span>
              <span v-if="inv.mop" class="rounded px-1.5 py-0.5"
                :class="inv.mop === 'Cash' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'"
              >{{ inv.mop }}</span>
              <span class="ml-auto">{{ inv.items_count || 0 }} items</span>
              <span v-if="formatTime(inv.posting_time)">· {{ formatTime(inv.posting_time) }}</span>
            </div>
            <div class="mt-1 flex items-end justify-between gap-2">
              <div class="min-w-0">
                <div class="truncate text-base font-bold">{{ inv.name }}</div>
                <div class="truncate text-sm text-[var(--color-text-muted)]">{{ inv.customer }}</div>
              </div>
              <div class="shrink-0 font-mono text-xl font-bold tabular-nums"
                :class="(inv.rounded_total || inv.grand_total) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'"
              >{{ fmt(inv.rounded_total || inv.grand_total) }}</div>
            </div>
          </button>
        </section>
      </div>
    </main>

    <!-- ==================== BILL + PAYMENT VIEW ==================== -->
    <template v-else>
      <main class="relative min-h-0 flex-1 overflow-y-auto">
        <div v-if="loadingPreview" class="py-16 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading bill…</div>
        <div v-else class="space-y-3 p-3">
          <!-- Customer -->
          <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2">
            <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer</div>
            <div class="truncate text-base font-bold text-[var(--color-info)]">{{ selectedInvoice.customer }}</div>
          </div>

          <!-- Items (collapsible: the payment boxes are what the cashier needs most) -->
          <div class="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
            <button type="button" class="flex w-full items-center justify-between px-3 py-2 text-left" @click="showItems = !showItems">
              <span class="text-sm font-bold uppercase tracking-wider">Items · {{ previewItems.length }} · Qty {{ totalQty }}</span>
              <span class="text-xs text-[var(--color-text-muted)]">{{ showItems ? 'Hide' : 'Show' }}</span>
            </button>
            <ul v-if="showItems" class="divide-y divide-[var(--color-border)] border-t border-[var(--color-border)]">
              <li v-for="item in previewItems" :key="item.name" class="px-3 py-2">
                <div class="text-sm font-semibold leading-tight">
                  {{ item.item_name }}
                  <!-- Backend is_free_item flag; rate-0 fallback for rows saved before it was stored -->
                  <span
                    v-if="item.is_free_item === 1 || !Number(item.rate)"
                    class="ml-1 rounded bg-[var(--color-success)] px-1.5 text-[10px] font-bold uppercase text-[var(--color-text-on-highlight)]"
                  >Free</span>
                </div>
                <div class="mt-0.5 flex justify-between font-mono text-sm tabular-nums text-[var(--color-text-muted)]">
                  <span>{{ item.qty }} {{ item.uom }} × {{ fmt(item.rate) }}</span>
                  <span class="font-bold text-[var(--color-text)]">{{ fmt(item.qty * item.rate) }}</span>
                </div>
              </li>
            </ul>
          </div>

          <!-- Tax breakdown -->
          <div v-if="taxSummary.length > 0" class="overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm">
            <div v-for="grp in taxSummary" :key="grp.template" class="flex items-center justify-between gap-2 border-b border-[var(--color-border)] px-3 py-1.5">
              <span class="truncate text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ taxTemplateLabel(grp.template) }}</span>
              <span class="font-mono text-xs text-[var(--color-text-muted)]">{{ fmt(grp.taxable_amount) }}</span>
              <span class="font-mono font-bold">₹{{ fmt(grp.tax_amount) }}</span>
            </div>
            <div class="flex items-center justify-between bg-[var(--color-surface-raised)]/60 px-3 py-1.5">
              <span class="text-xs font-black uppercase">Total Tax<span v-if="selectedInvoice?.is_inclusive" class="ml-1 normal-case text-[var(--color-text-muted)]">(incl.)</span></span>
              <span class="font-mono font-black">₹{{ fmt(totalTax) }}</span>
            </div>
          </div>

          <!-- Unallocated credit notes -->
          <button
            v-if="unallocatedPayments.length > 0 && (selectedInvoice.rounded_total || selectedInvoice.grand_total || 0) > 0"
            type="button"
            class="flex w-full items-center gap-3 rounded-xl border border-[var(--color-warning)]/40 bg-[var(--color-warning)]/10 px-3 py-2.5 text-left active:bg-[var(--color-warning)]/20"
            @click="showReconcileModal = true"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--color-warning)]/20 text-xl font-black text-[var(--color-warning)]">₹</span>
            <span class="flex-1">
              <span class="block text-xs font-black uppercase tracking-wider text-[var(--color-warning)]">Unallocated · tap to adjust</span>
              <span class="block font-mono text-lg font-black text-[var(--color-warning)]">₹{{ fmt(unallocatedAmountTotal) }}</span>
            </span>
          </button>

          <!-- Allocated advances -->
          <div v-if="selectedInvoice?.advances?.length > 0" class="space-y-1.5">
            <div class="px-1 text-[10px] font-black uppercase tracking-widest text-[var(--color-info)]">Allocated Advances</div>
            <div v-for="adv in selectedInvoice.advances" :key="adv.reference_name"
              class="flex items-center justify-between gap-2 rounded-xl border border-[var(--color-info)]/20 bg-[var(--color-info)]/10 px-3 py-2 text-sm font-bold text-[var(--color-info)]"
            >
              <span class="min-w-0 truncate">{{ adv.reference_name }}</span>
              <span class="flex shrink-0 items-center gap-2">
                <span class="font-mono">₹{{ fmt(adv.allocated_amount) }}</span>
                <button type="button" aria-label="Remove credit note allocation" class="rounded px-2 text-lg leading-none text-[var(--color-text-muted)]" :disabled="isSubmitting" @click="removeAdvance(adv)">&times;</button>
              </span>
            </div>
          </div>

          <!-- Bill summary -->
          <div class="relative rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
            <div class="flex items-start justify-between">
              <div>
                <div class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Bill Amount</div>
                <div class="font-mono text-3xl font-black tabular-nums">₹{{ fmt(amountToCollect) }}</div>
              </div>
              <span class="rounded border px-2 py-0.5 text-[10px] font-black uppercase tracking-widest"
                :class="isCredit ? 'border-[var(--color-danger)] bg-[var(--color-danger)]/20 text-[var(--color-danger)]' : 'border-[var(--color-success)] bg-[var(--color-success)]/20 text-[var(--color-success)]'"
              >{{ isCredit ? 'Credit' : 'Cash' }}</span>
            </div>
            <div class="mt-2 flex justify-between border-t border-[var(--color-border)] pt-2 text-sm">
              <span class="font-bold text-[var(--color-text-muted)]">Grand Total</span>
              <span class="font-mono font-bold">₹{{ fmt(selectedInvoice.rounded_total || selectedInvoice.grand_total) }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="font-bold text-[var(--color-text-muted)]">Paid Amount</span>
              <span class="font-mono font-bold">₹{{ fmt(totalPaid) }}</span>
            </div>
          </div>

          <!-- Cash / Credit toggle -->
          <div class="flex gap-2">
            <button
              type="button"
              :disabled="isSecondaryParty || selectedInvoice?.is_return"
              class="flex-1 rounded-xl border py-2.5 text-base font-black uppercase tracking-wider disabled:opacity-30"
              :class="!isCredit ? 'border-[var(--color-success)] bg-[var(--color-success)]/20 text-[var(--color-success)]' : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)]'"
              @click="onToggleCredit(false)"
            >Cash Bill</button>
            <button
              type="button"
              class="flex-1 rounded-xl border py-2.5 text-base font-black uppercase tracking-wider"
              :class="isCredit ? 'border-[var(--color-danger)] bg-[var(--color-danger)]/20 text-[var(--color-danger)]' : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)]'"
              @click="onToggleCredit(true)"
            >Credit</button>
          </div>

          <!-- Posting date -->
          <div class="rounded-xl border p-2"
            :class="postingDate !== getTodayIST() ? 'border-red-700 bg-red-600 text-white' : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
          >
            <div class="text-center text-[10px] font-black uppercase tracking-[0.2em] opacity-80">Posting Date</div>
            <div class="flex items-center justify-between gap-2">
              <button v-if="canModifyDate()" type="button" aria-label="Previous day" class="rounded-lg px-3 py-1 text-xl" @click="adjustPostingDate(-1)">‹</button>
              <input
                v-model="postingDate"
                type="date"
                :disabled="!canModifyDate()"
                class="min-w-0 flex-1 border-none bg-transparent p-0 text-center text-lg font-black focus:ring-0"
              />
              <button v-if="canModifyDate()" type="button" aria-label="Next day" class="rounded-lg px-3 py-1 text-xl" @click="adjustPostingDate(1)">›</button>
            </div>
          </div>

          <!-- Cash-mode payment boxes -->
          <div v-if="!isCredit" class="space-y-2">
            <label class="pay-row focus-within:border-[var(--color-info)]">
              <span class="pay-label">{{ cashLabel }}</span>
              <input v-model="payments.cash" type="number" inputmode="decimal" step="0.01" class="pay-input" @focus="$event.target.select()" />
            </label>
            <label class="pay-row focus-within:border-[var(--color-success)]" :class="upiLocked ? 'border-[var(--color-success)]/50 bg-[var(--color-success)]/10' : ''">
              <span class="pay-label">{{ upiLabel }}</span>
              <input v-model="payments.upi" type="number" inputmode="decimal" step="0.01" class="pay-input" :readonly="upiLocked" @focus="$event.target.select()" />
            </label>
            <!-- Paytm: push the UPI box amount to the machine (UPI QR / card) or show a QR here -->
            <div v-if="!upiLocked && (hasPaytmMachine || paytm.qrEnabled)" class="flex gap-2">
              <button v-if="hasPaytmMachine" type="button" class="flex-1 rounded-xl bg-[var(--color-success)] py-2 text-sm font-black uppercase tracking-wider text-white active:opacity-80" @click="openPaytmModal('QR')">Machine UPI</button>
              <button v-if="hasPaytmMachine" type="button" class="flex-1 rounded-xl bg-[var(--color-info)] py-2 text-sm font-black uppercase tracking-wider text-white active:opacity-80" @click="openPaytmModal('CARD')">Machine Card</button>
              <button v-if="paytm.qrEnabled" type="button" class="flex-1 rounded-xl border border-[var(--color-success)] py-2 text-sm font-black uppercase tracking-wider text-[var(--color-success)] active:bg-[var(--color-success)]/10" @click="openPaytmQr">Show QR</button>
            </div>
            <!-- Saved as the UPI Payment Entry's Reference No; Paytm fills it on a machine payment -->
            <input
              v-if="Number(payments.upi) > 0"
              v-model.trim="upiRefNo"
              :readonly="upiLocked"
              type="text"
              placeholder="UPI Ref No (optional)"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-right font-mono text-sm font-bold text-[var(--color-text)] outline-none read-only:border-[var(--color-success)]/50 read-only:bg-[var(--color-success)]/10 focus:border-[var(--color-success)]"
            />
            <label class="pay-row focus-within:border-[var(--color-info)]" :class="cardLocked ? 'border-[var(--color-success)]/50 bg-[var(--color-success)]/10' : ''">
              <span class="pay-label">{{ cardLabel }}</span>
              <input v-model="payments.card" type="number" inputmode="decimal" step="0.01" class="pay-input" :readonly="cardLocked" @focus="$event.target.select()" />
            </label>
            <label class="pay-row focus-within:border-[var(--color-danger)]">
              <span class="pay-label">Credit</span>
              <input v-model="payments.credit" type="number" inputmode="decimal" step="0.01" class="pay-input" @focus="$event.target.select()" />
            </label>
            <label class="pay-row focus-within:border-[var(--color-warning)]">
              <span class="pay-label">{{ discountLabel }}</span>
              <input v-model="payments.discount" type="number" inputmode="decimal" step="0.01" class="pay-input" @focus="$event.target.select()" />
            </label>
          </div>

          <!-- Credit-mode: promise date -->
          <div v-else class="rounded-xl border border-[var(--color-danger)]/60 bg-[var(--color-danger)]/15 p-3">
            <label class="mb-2 block text-xs font-black uppercase tracking-widest text-[var(--color-danger)]">Promise Date (Due Date)</label>
            <div class="flex items-center gap-2">
              <input
                v-model="dueDate"
                type="text"
                inputmode="numeric"
                placeholder="DDMM or DD/MM/YYYY"
                class="min-w-0 flex-1 rounded-xl border border-[var(--color-danger)]/50 bg-[var(--color-bg)] px-3 py-3 text-center font-mono text-lg font-black text-[var(--color-text)] outline-none focus:border-[var(--color-danger)]"
                @input="handleDueDateInput"
                @keydown.backspace="handleDueDateKeyDown"
              />
              <DatePickerButton :model-value="dueDate ? getIsoDueDate() : ''" label="Choose promise date" @update:model-value="dueDate = $event ? $event.split('-').reverse().join('/') : ''" />
            </div>
          </div>

          <label class="pay-row focus-within:border-[var(--color-focus)]">
            <span class="pay-label">Remarks</span>
            <input v-model="payments.remarks" type="text" class="pay-input text-base" />
          </label>

          <p v-if="errorMsg" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm font-semibold text-[var(--color-danger)]">{{ errorMsg }}</p>
          <p v-if="successMsg" class="rounded-lg bg-[var(--color-success)]/15 px-3 py-2 text-sm font-semibold text-[var(--color-success)]">{{ successMsg }}</p>
        </div>
      </main>

      <!-- Sticky footer: balance + post -->
      <footer class="z-20 shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2">
        <div v-if="!isCredit" class="mb-2 flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
            {{ balance <= 0.01 ? 'Change Return' : 'Balance Due' }}
          </span>
          <span class="font-mono text-2xl font-black tabular-nums" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">₹{{ fmt(Math.abs(balance)) }}</span>
        </div>
        <button
          type="button"
          :disabled="!canSubmit"
          class="w-full rounded-xl py-3.5 text-base font-black uppercase tracking-[0.15em] text-white active:scale-[0.98] disabled:opacity-30"
          :class="isCredit ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-success)]'"
          @click="processPayment"
        >
          <span v-if="isSubmitting">Processing…</span>
          <span v-else>{{ isCredit ? 'Post Credit Sale' : 'Post Settlement' }}</span>
        </button>
      </footer>
    </template>

    <!-- CARD REFERENCE MODAL -->
    <div v-if="showCardRefModal" class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center">
      <div class="w-full max-w-md rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:rounded-2xl">
        <h3 class="mb-3 text-sm font-bold uppercase tracking-widest">Card / {{ cardLabel }} Reference</h3>
        <input
          ref="cardRefInput"
          v-model="cardRefNo"
          :readonly="cardLocked"
          class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 font-mono text-base font-black text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          placeholder="Authorization / reference no"
          @keydown.enter="confirmCardRef"
        />
        <div class="mt-3 flex gap-2">
          <button type="button" class="flex-1 rounded-xl bg-[var(--color-surface-raised)] py-3 text-sm font-bold uppercase text-[var(--color-text-muted)]" @click="showCardRefModal = false">Cancel</button>
          <button type="button" :disabled="!cardRefNo" class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-sm font-bold uppercase text-white disabled:opacity-40" @click="confirmCardRef">Confirm & Post</button>
        </div>
      </div>
    </div>

    <!-- PAYTM CARD MACHINE MODAL -->
    <div v-if="paytm.show" class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center">
      <div class="w-full max-w-md space-y-3 rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:rounded-2xl">
        <h3 class="text-sm font-bold uppercase tracking-widest">Paytm Machine · {{ paytm.payMode === 'CARD' ? 'Card' : 'UPI' }}</h3>
        <div class="flex justify-between"><span class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Amount</span><span class="font-mono text-xl font-black">₹{{ fmt(paytm.amount) }}</span></div>
        <div class="flex justify-between gap-2"><span class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Machine</span><span class="truncate font-bold">{{ paytm.deviceName }} ({{ paytm.tid }})</span></div>
        <div v-if="paytm.customerName" class="flex justify-between gap-2">
          <span class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Customer</span>
          <span class="truncate font-bold">{{ paytm.customerName }}<template v-if="paytm.phone && !paytm.askPhone"> · {{ paytm.phone }}</template></span>
        </div>
        <!-- The bill has no real number (e.g. 9999999999): the cashier may add one, or skip it -->
        <input
          v-if="paytm.askPhone && !paytm.orderId"
          ref="paytmPhoneInput"
          v-model.trim="paytm.phone"
          type="tel"
          maxlength="13"
          placeholder="Customer phone (optional)"
          class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 font-mono font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          @keydown.enter="sendToPaytm"
        />
        <div v-if="paytm.message" class="rounded-lg border p-3 text-xs font-bold uppercase tracking-wider" :class="statusClass(paytm.status)">{{ paytm.message }}</div>
        <div class="flex gap-2">
          <button type="button" :disabled="paytm.sending" class="flex-1 rounded-xl bg-[var(--color-surface-raised)] py-3 text-sm font-bold uppercase text-[var(--color-text-muted)] disabled:opacity-40" @click="closePaytmModal">
            {{ paytm.orderId && paytm.status === 'Pending' ? 'Stop Waiting' : 'Close' }}
          </button>
          <button
            v-if="paytm.status === 'Failed' || (paytm.askPhone && !paytm.orderId)"
            type="button"
            :disabled="paytm.sending"
            class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-sm font-bold uppercase text-white disabled:opacity-40"
            @click="sendToPaytm"
          >{{ paytm.sending ? 'Sending…' : paytm.status === 'Failed' ? 'Retry' : 'Send to Machine' }}</button>
        </div>
      </div>
    </div>

    <!-- PAYTM DYNAMIC QR MODAL -->
    <div v-if="paytmQr.show" class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center">
      <div class="w-full max-w-md space-y-3 rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:rounded-2xl">
        <h3 class="text-sm font-bold uppercase tracking-widest">Paytm UPI QR</h3>
        <div class="flex justify-between"><span class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Amount</span><span class="font-mono text-xl font-black">₹{{ fmt(paytmQr.amount) }}</span></div>
        <div class="flex justify-center">
          <!-- white backing so the code scans in dark mode too -->
          <img v-if="paytmQr.image && paytmQr.status !== 'Failed'" :src="paytmQrSrc" alt="Paytm UPI QR" class="h-64 w-64 rounded-xl bg-white p-2" :class="paytmQr.status === 'Success' ? 'opacity-30' : ''" />
          <div v-else-if="paytmQr.sending" class="flex h-64 w-64 items-center justify-center text-xs font-bold uppercase text-[var(--color-text-muted)]">Creating QR…</div>
        </div>
        <div v-if="paytmQr.message" class="rounded-lg border p-3 text-xs font-bold uppercase tracking-wider" :class="statusClass(paytmQr.status)">{{ paytmQr.message }}</div>
        <div class="flex gap-2">
          <button type="button" class="flex-1 rounded-xl bg-[var(--color-surface-raised)] py-3 text-sm font-bold uppercase text-[var(--color-text-muted)]" @click="closePaytmQr">
            {{ paytmQr.orderId && paytmQr.status === 'Pending' ? 'Stop Waiting' : 'Close' }}
          </button>
          <button
            v-if="paytmQr.status === 'Failed'"
            type="button"
            :disabled="paytmQr.sending"
            class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-sm font-bold uppercase text-white disabled:opacity-40"
            @click="createPaytmQr"
          >{{ paytmQr.sending ? 'Creating…' : 'New QR' }}</button>
        </div>
      </div>
    </div>

    <!-- RECONCILIATION MODAL -->
    <Unallocated
      :show="showReconcileModal"
      :invoice="selectedInvoice"
      :unallocated="unallocatedPayments"
      @close="showReconcileModal = false"
      @success="handleAllocationSuccess"
    />

    <!-- PRINT OPTIONS MODAL -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="selectedInvoice?.name"
      :series="selectedInvoice?.naming_series"
      @close="showPrintModal = false"
    />

    <!-- BILL MIRROR CREATOR MODAL -->
    <BillMirrorCreator
      v-if="showBillMirrorCreator"
      :show="showBillMirrorCreator"
      :invoice-name="processedInvoiceName"
      @close="showBillMirrorCreator = false"
    />

    <!-- GST MIRROR WARNING MODAL -->
    <Warning
      :show="showGstWarning"
      title="GST Mirroring"
      :message="`mirror salesinvoice no: ${processedInvoiceName} to alternate company`"
      @close="showGstWarning = false"
      @confirm="handleGstConfirm"
    />

    <!-- SUCCESS TOAST -->
    <transition name="slide-up">
      <div v-if="showSuccessModal" class="fixed inset-x-3 bottom-[max(1rem,env(safe-area-inset-bottom))] z-[110]" @click="showSuccessModal = false">
        <div class="flex items-center gap-3 rounded-2xl border border-[var(--color-success)]/30 bg-[var(--color-surface)] p-3 shadow-2xl">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-xl font-black text-[var(--color-success)]">✓</span>
          <div class="min-w-0">
            <div class="text-base font-black uppercase">{{ mirrorQueued ? 'Bill Settled · Mirror Queued' : 'Bill Settled' }}</div>
            <div class="truncate text-xs font-bold text-[var(--color-text-muted)]">{{ processedInvoiceName }}</div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
// Phone front end for the Cashier Desk: same draft list and settlement flow as CashierDesk.vue,
// laid out as list → bill/payment views. No keyboard shortcuts and no Modify subwindow here.
import DatePickerButton from '../components/DatePickerButton.vue'
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { onBillPanelUpdate } from '../composables/useBillPanelSync.js'
import { applyPanelEvent } from '../services/billPanelCache.js'
import { session } from '../session'
import { getFrappeSocket } from '../services/frappeSocket.js'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings, frappeGet, frappePost } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'
import { useLedgerCache } from '../services/ledgerCache'
import { getSeriesForDoctype } from '../services/seriesCache.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import Unallocated from '../components/Unallocated.vue'
import BillMirrorCreator from '../components/BillMirrorCreator.vue'
import Warning from '../components/Warning.vue'
import { canModifyDate } from '../composables/usePermission'
import { formatDMY } from '../utils/date'
import { serverToday, serverCalendarDate, toLocalISO, parseCalendarDate } from '../services/serverTime'

const router = useRouter()

function getTodayIST() {
  return serverToday()
}

// ==================== STATE ====================
const postingDate = ref(getTodayIST())
const searchQuery = ref('')
const sidebarSeries = ref([])
const showSeriesDropdown = ref(false)
const availableSeries = ref([])
const showItems = ref(false)

function toggleSeries(series) {
  const idx = sidebarSeries.value.indexOf(series)
  if (idx > -1) sidebarSeries.value.splice(idx, 1)
  else sidebarSeries.value.push(series)
  loadInvoices()
}

function isSeriesSelected(series) {
  return sidebarSeries.value.includes(series)
}

function toggleAllSeries() {
  sidebarSeries.value = sidebarSeries.value.length === availableSeries.value.length ? [] : [...availableSeries.value]
  loadInvoices()
}

const showCardRefModal = ref(false)
const showPrintModal = ref(false)
const showReconcileModal = ref(false)
const showSuccessModal = ref(false)
const showBillMirrorCreator = ref(false)
const showGstWarning = ref(false)
const cardRefNo = ref('')
const upiRefNo = ref('')
const cardRefInput = ref(null)

// Paytm EDC card machine: push the UPI box amount to the machine, wait for the result
// (socket event from the webhook, with polling as fallback), then fill UPI or Card.
const paytm = ref({ enabled: false, qrEnabled: false, devices: [], show: false, payMode: 'QR', tid: '', deviceName: '', customerName: '', phone: '', askPhone: false, amount: 0, orderId: '', status: '', message: '', sending: false })
let paytmPollTimer = null
const paytmPhoneInput = ref(null)
// Paytm dynamic UPI QR: same wait-for-result flow, but the QR is shown on this screen
const paytmQr = ref({ show: false, amount: 0, orderId: '', status: '', message: '', image: '', sending: false })
let paytmQrPollTimer = null
const paytmQrSrc = computed(() => {
  const img = paytmQr.value.image || ''
  return img.startsWith('data:') ? img : `data:image/png;base64,${img}`
})
// Machine buttons only for a cashier with a machine assigned in SSPL Paytm Settings
const hasPaytmMachine = computed(() => paytm.value.enabled && paytm.value.devices.length > 0)
const processedInvoiceName = ref('')
const mirrorQueued = ref(false)

// Modals reuse the shared subwindow flag so global shortcuts stay quiet behind them
useSubwindowWatcher(showCardRefModal)
useSubwindowWatcher(computed(() => paytm.value.show))
useSubwindowWatcher(computed(() => paytmQr.value.show))
useSubwindowWatcher(showPrintModal)
useSubwindowWatcher(showReconcileModal)
useSubwindowWatcher(showBillMirrorCreator)
useSubwindowWatcher(showGstWarning)

const invoices = ref([])
const selectedInvoice = ref(null)
const previewItems = ref([])
const unallocatedPayments = ref([])
const unallocatedAmountTotal = ref(0)

const isCredit = ref(false)
const dueDate = ref('')
const isSubmitting = ref(false)
const loadingList = ref(false)
const loadingPreview = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const payments = ref({ cash: 0, upi: 0, card: 0, credit: 0, discount: 0, remarks: '' })

// A UPI / Card amount received through Paytm is locked, with its reference, to what Paytm
// confirmed for this bill; only the other payment fields stay editable
const paytmLock = ref({ invoice: '', upi: null, upiRef: '', card: null, cardRef: '' })
const upiLocked = computed(() => paytmLock.value.upi != null && paytmLock.value.invoice === selectedInvoice.value?.name)
const cardLocked = computed(() => paytmLock.value.card != null && paytmLock.value.invoice === selectedInvoice.value?.name)
function lockPaytmPayment(mode, amount, ref) {
  const lock = paytmLock.value.invoice === selectedInvoice.value?.name
    ? paytmLock.value
    : { invoice: selectedInvoice.value?.name, upi: null, upiRef: '', card: null, cardRef: '' }
  if (mode === 'card') Object.assign(lock, { card: Number(payments.value.card) || amount, cardRef: ref })
  else Object.assign(lock, { upi: amount, upiRef: ref })
  paytmLock.value = { ...lock }
}
// Every reset of the payment boxes (credit flip, advance allocation…) puts locked values back
watch([payments, upiRefNo, cardRefNo], () => {
  const lock = paytmLock.value
  if (upiLocked.value) {
    if (Number(payments.value.upi) !== lock.upi) payments.value.upi = lock.upi
    if (upiRefNo.value !== lock.upiRef) upiRefNo.value = lock.upiRef
  }
  if (cardLocked.value) {
    if (Number(payments.value.card) !== lock.card) payments.value.card = lock.card
    if (cardRefNo.value !== lock.cardRef) cardRefNo.value = lock.cardRef
  }
}, { deep: true })

const seriesAccounts = ref({ cash: '', upi: '', card: '', discount: '' })

// Keep the page the height of the visible viewport so the on-screen keyboard
// doesn't push the Post button out of reach
const viewportHeight = ref(0)
const viewportStyle = computed(() => (viewportHeight.value ? { height: viewportHeight.value + 'px' } : null))
function fitViewport() {
  viewportHeight.value = Math.round(window.visualViewport?.height || window.innerHeight)
}

// ==================== COMPUTED ====================
const { partyLinks } = useLedgerCache()

const bucketedInvoices = computed(() => {
  const groups = {}
  for (const inv of invoices.value) {
    const d = inv.posting_date || 'Unknown Date'
    if (!groups[d]) groups[d] = []
    groups[d].push(inv)
  }

  const today = getTodayIST()
  const yesterday = serverCalendarDate()
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayStr = toLocalISO(yesterday)

  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map(dateKey => ({
      date: dateKey,
      label: dateKey === today ? 'Today'
        : dateKey === yesterdayStr ? 'Yesterday'
        : dateKey === 'Unknown Date' ? 'Unknown Date'
        : formatDate(dateKey),
      invoices: groups[dateKey],
    }))
})

const isSecondaryParty = computed(() => {
  if (!selectedInvoice.value?.customer) return false
  return partyLinks.value[selectedInvoice.value.customer]?.is_secondary || false
})

function glLabel(key, fallback) {
  const acc = localStorage.getItem(key) || ''
  return acc ? acc.split(' - ')[0].trim() : fallback
}
const cashLabel = computed(() => glLabel('wb-cash', 'Cash'))
const upiLabel  = computed(() => glLabel('wb-upi', 'UPI'))
const cardLabel = computed(() => glLabel('wb-card', 'Card'))
const discountLabel = computed(() => {
  const acc = seriesAccounts.value.discount || localStorage.getItem('wb-discount-account') || ''
  return acc ? acc.split(' - ')[0].trim() : 'Disc'
})

const amountToCollect = computed(() => {
  if (!selectedInvoice.value) return 0
  const gt = Number(selectedInvoice.value.rounded_total || selectedInvoice.value.grand_total || 0)
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
              (Number(payments.value.credit) || 0) +
              (Number(payments.value.discount) || 0)
  return parseFloat(sum.toFixed(2))
})

const balance = computed(() => parseFloat((amountToCollect.value - totalPaid.value).toFixed(2)))

const canSubmit = computed(() => {
  if (!selectedInvoice.value || isSubmitting.value || loadingPreview.value) return false
  if (selectedInvoice.value.docstatus === 1 && (selectedInvoice.value.outstanding_amount || 0) <= 0.01) return false
  if (selectedInvoice.value.is_return && !isCredit.value) return false
  if (isCredit.value) return true
  // Force cashier to account for the full bill (using Cash/UPI/Card/Disc OR the Credit box)
  return balance.value <= 0.01
})

const totalQty = computed(() => previewItems.value.reduce((acc, i) => acc + Number(i.qty || 0), 0))

const taxSummary = computed(() => selectedInvoice.value?.tax_summary || [])

const totalTax = computed(() => {
  const rows = taxSummary.value
  if (rows.length) return rows.reduce((acc, r) => acc + Number(r.tax_amount || 0), 0)
  return Number(selectedInvoice.value?.total_tax || 0)
})

// Item Tax Templates are named "GST 18% - SSPL"; drop the company abbr for the footer.
function taxTemplateLabel(template) {
  if (!template) return 'No Tax Template'
  const idx = template.lastIndexOf(' - ')
  return idx > 0 ? template.slice(0, idx) : template
}

const hasPaymentValues = computed(() =>
  (Number(payments.value.cash)     || 0) > 0 ||
  (Number(payments.value.credit)   || 0) > 0 ||
  (Number(payments.value.discount) || 0) > 0 ||
  (Number(payments.value.upi)      || 0) > 0 ||
  (Number(payments.value.card)     || 0) > 0
)

function statusClass(status) {
  if (status === 'Failed') return 'bg-[var(--color-danger)]/20 border-[var(--color-danger)]/50 text-[var(--color-danger)]'
  if (status === 'Success') return 'bg-[var(--color-success)]/20 border-[var(--color-success)]/50 text-[var(--color-success)]'
  return 'bg-[var(--color-info)]/20 border-[var(--color-info)]/50 text-[var(--color-info)]'
}

// ==================== LIST ====================
function setInvoiceList(rows) {
  invoices.value = [...rows].sort((a, b) => {
    const dateA = a.posting_date || ''
    const dateB = b.posting_date || ''
    if (dateA !== dateB) return dateB.localeCompare(dateA)
    return b.name.localeCompare(a.name)
  })
}

// Patch the draft list in place from a bill_panel_update socket payload, so a bill
// saved by any biller doesn't make every cashier tab refetch up to 500 drafts.
// Returns true when handled; onBillPanelUpdate then skips the refetch.
function applyCashierPanelEvent(data) {
  if (searchQuery.value) return false // search results — let the refetch handle it
  // No series picked means "all allowed series", which only the server can resolve.
  if (!sidebarSeries.value.length) return false
  const currentCompany = localStorage.getItem('wb-company') || ''
  if (currentCompany && data?.row?.company && data.row.company !== currentCompany) {
    // Another company's bill (e.g. a mirror bill) never belongs in this list.
    invoices.value = invoices.value.filter(i => i.name !== data.row.name)
    return true
  }
  setInvoiceList(applyPanelEvent(invoices.value, data, { draftOnly: true }))
  return true
}

async function loadInvoices() {
  loadingList.value = true
  try {
    const res = await fetchDraftInvoices(searchQuery.value, 500, '', sidebarSeries.value.join(','))
    setInvoiceList(res)
  } catch (e) {
    errorMsg.value = 'Failed to load invoices: ' + e.message
  } finally {
    loadingList.value = false
  }
}

async function fetchSeriesList() {
  try {
    // 1. Try to get intersection from localStorage (seriesCache refetches when empty)
    const storedAllowed = localStorage.getItem('wb-allowed-series')
    const dtSeries = await getSeriesForDoctype('Sales Invoice')

    let finalSeries = []
    if (storedAllowed && dtSeries.length) {
      try {
        const allowedPrefixes = JSON.parse(storedAllowed)
        if (Array.isArray(allowedPrefixes)) {
          finalSeries = dtSeries
            .map(s => typeof s === 'string' ? s : s.prefix)
            .filter(s => allowedPrefixes.some(prefix => s && s.startsWith(prefix)))
        }
      } catch (e) {
        console.warn('[CashierMobile] Local series parsing failed:', e)
      }
    }

    // 2. If intersection empty or not possible, fallback to backend
    if (!finalSeries.length) {
      const res = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { doctype: 'Sales Invoice' })
      finalSeries = res.allowed_series || []
    }

    availableSeries.value = finalSeries
    if (sidebarSeries.value.length === 0 && availableSeries.value.length > 0) {
      sidebarSeries.value = [...availableSeries.value]
    }
  } catch (e) {
    console.warn('[CashierMobile] Could not fetch series list:', e)
  }
}

function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatDate(dateStr) {
  return formatDMY(dateStr, '')
}

// "14:23:45.123456" → "2:23 PM"
function formatTime(timeStr) {
  if (!timeStr) return ''
  const [h, m] = String(timeStr).split(':')
  const hh = parseInt(h, 10)
  if (isNaN(hh) || m == null) return ''
  return `${hh % 12 || 12}:${m} ${hh >= 12 ? 'PM' : 'AM'}`
}

function adjustPostingDate(days) {
  if (!canModifyDate()) return
  const d = parseCalendarDate(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = toLocalISO(d)
}

let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(loadInvoices, 300)
}

// Back: bill view → list, list → dashboard
function goBack() {
  if (selectedInvoice.value) {
    closeInvoice()
    return
  }
  router.push('/')
}

function closeInvoice() {
  selectedInvoice.value = null
  previewItems.value = []
  unallocatedPayments.value = []
  errorMsg.value = ''
  successMsg.value = ''
}

// ==================== BILL ====================
async function selectInvoice(inv) {
  loadingPreview.value = true
  selectedInvoice.value = inv
  previewItems.value = []
  unallocatedPayments.value = []
  errorMsg.value = ''
  successMsg.value = ''
  isCredit.value = false
  dueDate.value = ''
  cardRefNo.value = ''
  upiRefNo.value = ''
  showItems.value = false
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: '' }

  try {
    // The list row already carries the customer, so the unallocated-cash lookup
    // runs alongside the details fetch instead of after it
    const [details, unallocated] = await Promise.all([
      getInvoiceDetails(inv.name),
      frappeGet('ssplbilling.api.cashier_api.get_customer_unallocated_cash', {
        customer: inv.customer,
        invoice_name: inv.name,
        company: localStorage.getItem('wb-company') || undefined
      }),
    ])
    // The cashier went back (or opened another bill) while this one loaded
    if (selectedInvoice.value?.name !== inv.name) return
    selectedInvoice.value = details
    previewItems.value = details.items || []
    // Carry the entry-time remark in: submit writes the box back to custom_remarks,
    // so starting blank would silently wipe whatever Sales Entry saved
    payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: details.custom_remarks || '' }
    await loadSeriesSettings(details.naming_series)

    let remaining = details.outstanding_amount || details.rounded_total || details.grand_total
    const filteredUnallocated = (unallocated || []).filter(pe => pe.mode_of_payment === 'Credit Note')
    unallocatedPayments.value = filteredUnallocated.map(pe => {
      const alloc = Math.min(Number(pe.unallocated_amount), remaining)
      remaining -= alloc
      return { ...pe, amount_to_allocate: parseFloat(alloc.toFixed(2)) }
    })
    unallocatedAmountTotal.value = filteredUnallocated.reduce((acc, p) => acc + Number(p.unallocated_amount || 0), 0)

    if (details.is_return) toggleCredit(true)
    else if (isSecondaryParty.value) toggleCredit(true)
    else if (details.mop) toggleCredit(details.mop === 'Credit')
  } catch (e) {
    errorMsg.value = 'Failed to load details: ' + e.message
  } finally {
    loadingPreview.value = false
  }
}

// Billing settings depend on the user, not the bill: fetch once per page visit
// and reuse for every invoice selected.
let billingSettingsPromise = null
function getBillingSettingsCached() {
  if (!billingSettingsPromise) {
    const targetUser = localStorage.getItem('wb-inherited-user') || null
    billingSettingsPromise = fetchDashboardSettings(targetUser).catch(e => {
      billingSettingsPromise = null
      throw e
    })
  }
  return billingSettingsPromise
}

async function loadSeriesSettings(series) {
  try {
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi  = localStorage.getItem('wb-upi')
    const lsCard = localStorage.getItem('wb-card')
    const settings = await getBillingSettingsCached()
    // Server resolves discount_account against wb-company; never hardcode a
    // company-tagged account here or discounts post to the wrong company's GL.
    const discountAccount = settings.discount_account || ''
    const seriesConfig = (settings.billing_series || []).find(s => s.series === series)

    if (lsCash || lsUpi || lsCard) {
      seriesAccounts.value = {
        cash:     lsCash || seriesConfig?.cash_account || 'Cash',
        upi:      lsUpi  || seriesConfig?.upi          || 'UPI',
        card:     lsCard || seriesConfig?.card         || 'Card',
        discount: discountAccount,
      }
    } else {
      const userDefaults = settings.user_defaults || {}
      seriesAccounts.value = {
        cash:     userDefaults.cash || seriesConfig?.cash_account || 'Cash',
        upi:      userDefaults.upi  || seriesConfig?.upi          || 'UPI',
        card:     userDefaults.card || seriesConfig?.card         || 'Card',
        discount: discountAccount,
      }
    }
  } catch (e) {
    console.warn('Could not load accounts', e)
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
  const targetVal = typeof val === 'boolean' ? val : !isCredit.value

  if (targetVal && (upiLocked.value || cardLocked.value)) {
    errorMsg.value = "A Paytm payment is already received on this bill; it can't be switched to Credit."
    return
  }
  if (!targetVal && isSecondaryParty.value) {
    errorMsg.value = 'Secondary parties can only process Credit Sales.'
    return
  }
  if (!targetVal && selectedInvoice.value?.is_return) {
    errorMsg.value = 'Sales returns can only be processed as Credit.'
    return
  }

  isCredit.value = targetVal
  // Amounts are mode-specific and get cleared; the remark is not, so it survives the flip
  const keptRemarks = payments.value.remarks || ''
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: keptRemarks }
}

// Tapping the toggle would silently wipe typed amounts, so refuse while any are entered
function onToggleCredit(val) {
  if (val === isCredit.value) return
  if (hasPaymentValues.value) {
    errorMsg.value = 'Clear the entered amounts before switching Cash/Credit.'
    return
  }
  errorMsg.value = ''
  toggleCredit(val)
}

// ==================== PAYTM ====================
// Machines follow the inherited user's settings (server honours it for admin only)
function paytmMachineUser() {
  let inherited = ''
  try { inherited = localStorage.getItem('wb-inherited-user') || '' } catch (e) { /* storage blocked */ }
  return inherited || session.user.value
}

async function loadPaytmDevices() {
  try {
    const res = await frappeGet('ssplbilling.api.paytm_api.get_devices', { user: paytmMachineUser() })
    paytm.value.enabled = !!res?.enabled
    paytm.value.qrEnabled = !!res?.qr_enabled
    paytm.value.devices = res?.devices || []
  } catch (e) {
    paytm.value.enabled = false
    paytm.value.qrEnabled = false
  }
}

async function openPaytmModal(payMode) {
  errorMsg.value = ''
  const amount = Number(payments.value.upi) || 0
  if (!selectedInvoice.value) {
    errorMsg.value = 'Select a bill before sending to the card machine.'
    return
  }
  if (!paytm.value.devices.length) {
    errorMsg.value = 'No card machine assigned to you. Set your user on a device in SSPL Paytm Settings.'
    return
  }
  if (amount <= 0) {
    errorMsg.value = `Enter the amount in the ${upiLabel.value} box before sending to the card machine.`
    return
  }
  // The machine is fixed by SSPL Paytm Settings (the user's assigned row); no picking here
  const device = paytm.value.devices[0]
  Object.assign(paytm.value, { show: true, payMode, tid: device.tid, deviceName: device.device_name, amount, orderId: '', status: '', message: '', sending: false, customerName: '', phone: '', askPhone: false })
  // Customer name + phone ride along in extendInfo; a placeholder number makes us ask first
  let contact = null
  try {
    contact = await frappeGet('ssplbilling.api.paytm_api.get_invoice_contact', { invoice_name: selectedInvoice.value.name })
  } catch (e) { /* send without contact details */ }
  Object.assign(paytm.value, { customerName: contact?.customer_name || '', phone: contact?.phone || '', askPhone: !!contact && !contact.phone })
  if (paytm.value.askPhone) {
    nextTick(() => paytmPhoneInput.value?.focus())
    return
  }
  sendToPaytm()
}

async function sendToPaytm() {
  const p = paytm.value
  Object.assign(p, { sending: true, orderId: '', status: '', message: 'Sending to the machine…' })
  try {
    const res = await frappePost('ssplbilling.api.paytm_api.send_to_device', {
      invoice_name: selectedInvoice.value.name,
      amount: p.amount,
      tid: p.tid,
      pay_mode: p.payMode,
      user: paytmMachineUser(),
      phone: p.phone,
    }, { silent: true })
    p.orderId = res.order_id
    p.status = 'Pending'
    p.message = `Waiting for payment on ${res.device_name}…`
    startPaytmPolling()
  } catch (e) {
    p.status = 'Failed'
    p.message = e.message || 'Could not send to the card machine.'
  } finally {
    p.sending = false
  }
}

function startPaytmPolling() {
  stopPaytmPolling()
  paytmPollTimer = setInterval(async () => {
    const orderId = paytm.value.orderId
    if (!orderId) return stopPaytmPolling()
    try {
      applyPaytmResult(await frappePost('ssplbilling.api.paytm_api.get_status', { order_id: orderId }, { silent: true }))
    } catch (e) { /* keep polling; the socket event may still arrive */ }
  }, 3000)
}

function stopPaytmPolling() {
  if (paytmPollTimer) clearInterval(paytmPollTimer)
  paytmPollTimer = null
}

function applyPaytmResult(r) {
  const p = paytm.value
  if (!r || r.order_id !== p.orderId || p.status !== 'Pending' || r.status === 'Pending') return
  stopPaytmPolling()
  p.status = r.status
  if (r.status !== 'Success') {
    p.message = r.message || `Payment ${r.status.toLowerCase()}.`
    return
  }
  if (r.mode === 'card') {
    // Paid by card on the machine: move the amount out of UPI into the Card box
    payments.value.upi = Math.max(0, (Number(payments.value.upi) || 0) - r.amount)
    payments.value.card = (Number(payments.value.card) || 0) + r.amount
    cardRefNo.value = r.reference_no
    lockPaytmPayment('card', r.amount, r.reference_no)
  } else {
    payments.value.upi = r.amount
    upiRefNo.value = r.reference_no
    lockPaytmPayment('upi', r.amount, r.reference_no)
  }
  p.message = `₹${fmt(r.amount)} received by ${r.mode === 'card' ? 'card' : 'UPI'} (Ref ${r.reference_no})`
  setTimeout(() => {
    if (paytm.value.orderId === r.order_id) closePaytmModal()
  }, 1500)
}

function onPaytmSocket(r) {
  applyPaytmResult(r)
  applyPaytmQrResult(r)
}

async function closePaytmModal() {
  const p = paytm.value
  stopPaytmPolling()
  if (p.orderId && p.status === 'Pending') {
    try {
      const r = await frappePost('ssplbilling.api.paytm_api.cancel', { order_id: p.orderId }, { silent: true })
      if (r?.status === 'Success') {
        // Paid just before the cashier gave up waiting — keep the payment
        applyPaytmResult(r)
        return
      }
    } catch (e) { /* closing anyway */ }
  }
  Object.assign(p, { show: false, orderId: '', status: '', message: '' })
}

function openPaytmQr() {
  errorMsg.value = ''
  const amount = Number(payments.value.upi) || 0
  if (!selectedInvoice.value) {
    errorMsg.value = 'Select a bill before creating the Paytm QR.'
    return
  }
  if (amount <= 0) {
    errorMsg.value = `Enter the amount in the ${upiLabel.value} box before creating the Paytm QR.`
    return
  }
  Object.assign(paytmQr.value, { show: true, amount, orderId: '', status: '', message: '', image: '', sending: false })
  createPaytmQr()
}

async function createPaytmQr() {
  const q = paytmQr.value
  Object.assign(q, { sending: true, orderId: '', status: '', message: '', image: '' })
  try {
    const res = await frappePost('ssplbilling.api.paytm_api.create_qr', {
      invoice_name: selectedInvoice.value.name,
      amount: q.amount,
    }, { silent: true })
    Object.assign(q, { orderId: res.order_id, image: res.qr_image, status: 'Pending', message: 'Waiting for the customer to scan and pay…' })
    stopPaytmQrPolling()
    paytmQrPollTimer = setInterval(async () => {
      const orderId = paytmQr.value.orderId
      if (!orderId) return stopPaytmQrPolling()
      try {
        applyPaytmQrResult(await frappePost('ssplbilling.api.paytm_api.get_status', { order_id: orderId }, { silent: true }))
      } catch (e) { /* keep polling; the socket event may still arrive */ }
    }, 3000)
  } catch (e) {
    q.status = 'Failed'
    q.message = e.message || 'Could not create the Paytm QR.'
  } finally {
    q.sending = false
  }
}

function stopPaytmQrPolling() {
  if (paytmQrPollTimer) clearInterval(paytmQrPollTimer)
  paytmQrPollTimer = null
}

function applyPaytmQrResult(r) {
  const q = paytmQr.value
  if (!r || r.order_id !== q.orderId || q.status !== 'Pending' || r.status === 'Pending') return
  stopPaytmQrPolling()
  q.status = r.status
  if (r.status !== 'Success') {
    q.message = r.message || `Payment ${r.status.toLowerCase()}.`
    return
  }
  payments.value.upi = r.amount
  upiRefNo.value = r.reference_no
  lockPaytmPayment('upi', r.amount, r.reference_no)
  q.message = `₹${fmt(r.amount)} received by UPI (Ref ${r.reference_no})`
  setTimeout(() => {
    if (paytmQr.value.orderId === r.order_id) closePaytmQr()
  }, 1500)
}

async function closePaytmQr() {
  const q = paytmQr.value
  stopPaytmQrPolling()
  if (q.orderId && q.status === 'Pending') {
    try {
      const r = await frappePost('ssplbilling.api.paytm_api.cancel', { order_id: q.orderId }, { silent: true })
      if (r?.status === 'Success') {
        // Paid just before the cashier gave up waiting — keep the payment
        applyPaytmQrResult(r)
        return
      }
    } catch (e) { /* closing anyway */ }
  }
  Object.assign(q, { show: false, orderId: '', status: '', message: '', image: '' })
}

// ==================== SUBMIT ====================
async function processPayment() {
  if (!canSubmit.value) return

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    if (Number(payments.value.card) > 0.01 && !cardRefNo.value) {
      showCardRefModal.value = true
      nextTick(() => cardRefInput.value?.focus())
      isSubmitting.value = false
      return
    }

    if (!isCredit.value && selectedInvoice.value?.is_return) {
      errorMsg.value = 'Sales returns can only be processed as Credit.'
      isSubmitting.value = false
      return
    }

    const bill = amountToCollect.value
    const upi  = Number(payments.value.upi)  || 0
    const card = Number(payments.value.card) || 0
    const disc = Number(payments.value.discount) || 0
    const credit = Number(payments.value.credit) || 0
    let cash = Number(payments.value.cash) || 0

    const total = cash + upi + card + disc + credit
    if (total > bill + 0.005) {
      // Adjustment logic if overpaid (always reduces cash first)
      cash = Math.max(0, bill - upi - card - disc - credit)
    }

    let finalDueDate = getIsoDueDate()
    const today = getTodayIST()
    if (finalDueDate < today) finalDueDate = today

    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: cash,
      upi_amount: upi,
      card_amount: card,
      discount_amount: disc,
      credit_amount: credit,
      is_credit: isCredit.value,
      due_date: finalDueDate,
      posting_date: canModifyDate() ? postingDate.value : getTodayIST(),
      card_ref_no: cardRefNo.value,
      upi_ref_no: upiRefNo.value,
      cash_account: seriesAccounts.value.cash,
      upi_account: seriesAccounts.value.upi,
      card_account: seriesAccounts.value.card,
      discount_account: seriesAccounts.value.discount,
      custom_remarks: payments.value.remarks,
      cost_center: localStorage.getItem('wb-cost-center') || null
    }

    const wasUpi = upi > 0.01
    const wasExempted = selectedInvoice.value?.tax_template?.toLowerCase().includes('exempt')
    const invoiceName = selectedInvoice.value?.name

    mirrorQueued.value = false
    const res = await submitInvoiceWithPayment(payload)
    mirrorQueued.value = res?.mirror_queued || false

    processedInvoiceName.value = invoiceName
    showSuccessModal.value = true

    // Back to the list for the next bill
    invoices.value = invoices.value.filter(i => i.name !== invoiceName)
    closeInvoice()
    postingDate.value = getTodayIST()

    setTimeout(() => { showSuccessModal.value = false }, 1500)

    const hasAlternativeCompany = !!localStorage.getItem('ae-alternative_company')
    if (wasUpi && wasExempted && hasAlternativeCompany) {
      nextTick(() => { showGstWarning.value = true })
    }
  } catch (e) {
    errorMsg.value = e.message
  } finally {
    isSubmitting.value = false
  }
}

function handleGstConfirm() {
  showGstWarning.value = false
  showBillMirrorCreator.value = true
}

async function confirmCardRef() {
  if (!cardRefNo.value) return
  showCardRefModal.value = false
  await processPayment()
}

function handleAllocationSuccess(res) {
  if (res.outstanding !== undefined) selectedInvoice.value.outstanding_amount = res.outstanding
  if (res.posting_date) selectedInvoice.value.posting_date = res.posting_date
  if (res.due_date) selectedInvoice.value.due_date = res.due_date
  // Only update advances if they are provided in the response
  if (res.advances) selectedInvoice.value.advances = res.advances

  const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
  if (idx !== -1 && res.posting_date) invoices.value[idx].posting_date = res.posting_date

  unallocatedPayments.value = []
  showReconcileModal.value = false

  const remaining = parseFloat((res.outstanding || 0).toFixed(2))
  const keptRemarks = payments.value.remarks || ''
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: keptRemarks }
  successMsg.value = remaining <= 0.01
    ? 'Advances cover full amount. Tap Post Settlement to finalise.'
    : `₹${fmt(remaining)} remaining after advance allocation.`
  setTimeout(() => successMsg.value = '', 4000)
}

async function removeAdvance(adv) {
  if (!selectedInvoice.value) return

  const updatedAllocations = (selectedInvoice.value.advances || [])
    .filter(a => a.reference_name !== adv.reference_name)
    .map(a => ({
      reference_name: a.reference_name,
      reference_row: a.reference_row,
      reference_type: a.reference_type,
      allocated_amount: a.allocated_amount
    }))

  isSubmitting.value = true
  try {
    const res = await frappePost('ssplbilling.api.cashier_api.update_invoice_advances', {
      invoice_name: selectedInvoice.value.name,
      allocations: updatedAllocations
    })
    if (res.status === 'success') {
      if (res.outstanding !== undefined) selectedInvoice.value.outstanding_amount = res.outstanding
      if (res.advances) selectedInvoice.value.advances = res.advances

      const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
      if (idx !== -1) invoices.value[idx].outstanding_amount = res.outstanding

      // Reload unallocated cash so this credit note is available again in the modal
      const unallocated = await frappeGet('ssplbilling.api.cashier_api.get_customer_unallocated_cash', {
        customer: selectedInvoice.value.customer,
        invoice_name: selectedInvoice.value.name,
        company: localStorage.getItem('wb-company') || undefined
      })
      const filteredUnallocated = (unallocated || []).filter(pe => pe.mode_of_payment === 'Credit Note')

      let remaining = res.outstanding || selectedInvoice.value.rounded_total || selectedInvoice.value.grand_total
      unallocatedPayments.value = filteredUnallocated.map(pe => {
        const alloc = Math.min(Number(pe.unallocated_amount), remaining)
        remaining -= alloc
        return { ...pe, amount_to_allocate: parseFloat(alloc.toFixed(2)) }
      })
      unallocatedAmountTotal.value = filteredUnallocated.reduce((acc, p) => acc + Number(p.unallocated_amount || 0), 0)

      successMsg.value = `Removed advance: ${adv.reference_name}`
      setTimeout(() => successMsg.value = '', 4000)
    }
  } catch (e) {
    errorMsg.value = 'Failed to remove advance: ' + (e.message || e)
  } finally {
    isSubmitting.value = false
  }
}

// ==================== DUE DATE ====================
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
    dueDate.value = `${raw.slice(0, 2)}/${raw.slice(2, 4)}/${serverCalendarDate().getFullYear()}`
    return
  }

  let formatted = raw
  if (raw.length >= 5) formatted = raw.slice(0, 2) + '/' + raw.slice(2, 4) + '/' + raw.slice(4)
  else if (raw.length >= 3) formatted = raw.slice(0, 2) + '/' + raw.slice(2)
  dueDate.value = formatted
}

function getIsoDueDate() {
  if (!dueDate.value || !dueDate.value.includes('/')) {
    if (dueDate.value.match(/^\d{4}-\d{2}-\d{2}$/)) return dueDate.value
    return getTodayIST()
  }
  const parts = dueDate.value.split('/')
  if (parts.length !== 3) return getTodayIST()
  const [dd, mm, yyyy] = parts
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`
}

// ==================== WATCHERS ====================
watch(postingDate, (newVal) => {
  if (!canModifyDate() && newVal !== getTodayIST()) postingDate.value = getTodayIST()
})

// ==================== LIFECYCLE ====================
const handleSeriesClickAway = (e) => {
  if (!e.target.closest('.series-dropdown-container')) showSeriesDropdown.value = false
}

let _billPanelCleanup = null

onMounted(() => {
  fitViewport()
  window.visualViewport?.addEventListener('resize', fitViewport)
  window.addEventListener('resize', fitViewport)
  window.addEventListener('click', handleSeriesClickAway)

  initAccountsFromLocalStorage()
  getBillingSettingsCached().catch(() => {})
  // Resolve the series first, then load once with the series filter applied
  fetchSeriesList().then(() => loadInvoices())

  _billPanelCleanup = onBillPanelUpdate('Sales Invoice', sidebarSeries, loadInvoices, applyCashierPanelEvent)
  loadPaytmDevices()
  getFrappeSocket()?.on('paytm_payment_update', onPaytmSocket)
})

onUnmounted(() => {
  window.visualViewport?.removeEventListener('resize', fitViewport)
  window.removeEventListener('resize', fitViewport)
  window.removeEventListener('click', handleSeriesClickAway)
  if (searchTimeout) clearTimeout(searchTimeout)
  _billPanelCleanup?.()
  stopPaytmPolling()
  stopPaytmQrPolling()
  getFrappeSocket()?.off('paytm_payment_update', onPaytmSocket)
})
</script>

<style scoped>
.pay-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  padding: 0.25rem 0.75rem;
}
.pay-label {
  flex-shrink: 0;
  max-width: 40%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 900;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.pay-input {
  min-width: 0;
  flex: 1;
  border: none;
  background: transparent;
  padding: 0.5rem 0;
  text-align: right;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.375rem;
  font-weight: 900;
  color: var(--color-text);
  outline: none;
  box-shadow: none;
}
.pay-input:read-only {
  cursor: not-allowed;
}

input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
