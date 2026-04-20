<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-[var(--color-bg)]' : 'flex min-h-screen flex-col bg-[var(--color-bg)]'">
    <div class="flex h-full flex-col">
    <!-- ═══════ HEADER ═══════ -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="handleBack"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ← {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-bold text-[var(--color-text)]">
            <span v-if="selectedLedger">{{ selectedLedger.type }} Ledger</span>
            <span v-else>Ledger Viewer</span>
          </h1>
          <span v-if="ledgerData" class="rounded bg-[var(--color-employee)]/20 px-2 py-0.5 text-[10px] font-semibold text-[var(--color-employee)]">
            {{ ledgerData.entries.length }} entries
          </span>
        </div>

        <!-- Shortcut info -->
        <div class="flex items-center gap-4 text-[10px] text-[var(--color-text-muted)]">
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Ctrl+L</kbd> Search</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Ctrl+P</kbd> Print</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> {{ isSubWindow ? 'Close' : 'Back' }}</span>
        </div>

        <!-- Print Button -->
        <button
          v-if="ledgerData"
          @click="showPrintModal = true"
          class="flex items-center gap-1.5 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          title="Print Ledger (Ctrl+P)"
        >
          🖨 Print
        </button>

        <!-- Zoom Controls -->
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
      </div>
    </header>

    <!-- ═══════ FILTER BAR ═══════ -->
    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex flex-wrap items-end gap-3">

        <!-- Ledger search -->
        <div class="relative w-80">
          <label class="mb-1 flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span>Ledger Account / Party</span>
            <span class="font-normal opacity-70">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 font-mono text-[9px] text-[var(--color-text)]">Ctrl+L</kbd> Search
            </span>
          </label>
          <div
            class="flex items-center justify-between rounded border px-3 py-2 text-sm cursor-pointer transition-colors"
            :class="selectedLedger ? 'bg-[var(--color-info)]/20 font-semibold text-[var(--color-info)] border-[var(--color-info)]' : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)] hover:border-[var(--color-info)]'"
            @click="openCustomerSearch"
          >
            <div class="truncate flex items-center gap-2">
              <span v-if="selectedLedger" class="px-1 py-0.5 rounded bg-[var(--color-info)]/40 text-[8px] uppercase tracking-tighter text-[var(--color-info)]">{{ selectedLedger.type }}</span>
              <span v-if="selectedLedger">{{ selectedLedger.label || selectedLedger.customer_name }}</span>
              <span v-else>Select account or party...</span>
            </div>
            <button
              v-if="selectedLedger"
              @click.stop="clearLedger"
              class="ml-2 text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- From date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">From</label>
          <input
            ref="dateInput"
            v-model="fromDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <!-- To date -->
        <div>
          <label class="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">To</label>
          <input
            v-model="toDate"
            type="date"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
        </div>

        <button
          @click="loadLedger"
          :disabled="!selectedLedger || loading"
          class="rounded-lg px-5 py-2 text-sm font-semibold transition-colors"
          :class="selectedLedger && !loading
            ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] cursor-pointer'
            : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] cursor-not-allowed'"
        >
          {{ loading ? 'Loading...' : 'Load Ledger' }}
        </button>

        <!-- Summary chips (visible after load) -->
        <template v-if="ledgerData">
          <div class="ml-2 flex items-center gap-3 text-xl">
            <span class="rounded bg-[var(--color-success)]/20 px-3 py-1.5 font-semibold text-[var(--color-success)]">
              Opening ₹{{ fmt(Math.abs(ledgerData.opening_balance)) }} {{ ledgerData.opening_balance < 0 ? '(Cr)' : '(Dr)' }}
            </span>
            <span class="rounded bg-[var(--color-success)]/20 px-3 py-1.5 font-semibold text-[var(--color-success)]">
              Dr ₹{{ fmt(ledgerData.total_debit) }}
            </span>
            <span class="rounded bg-[var(--color-danger)]/20 px-3 py-1.5 font-semibold text-[var(--color-danger)]">
              Cr ₹{{ fmt(ledgerData.total_credit) }}
            </span>
            <span
              class="rounded px-3 py-1.5 font-bold"
              :class="ledgerData.closing_balance >= 0 ? 'bg-[var(--color-success)]/20 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/20 text-[var(--color-danger)]'"
            >
              Balance ₹{{ fmt(Math.abs(ledgerData.closing_balance)) }}
              {{ ledgerData.closing_balance < 0 ? '(Cr)' : '(Dr)' }}
            </span>
          </div>
        </template>
      </div>
    </div>

    <!-- ═══════ MAIN CONTENT ═══════ -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Ledger Table ── -->
      <div class="flex flex-1 flex-col overflow-hidden">

        <!-- Empty / loading state -->
        <div v-if="!ledgerData && !loading && !error" class="flex flex-1 flex-col items-center justify-center gap-2 text-[var(--color-text-muted)]">
          <div class="text-4xl">📋</div>
          <div class="text-sm font-semibold">Search and select a ledger to view history</div>
        </div>

        <div v-else-if="loading" class="flex flex-1 items-center justify-center text-sm text-[var(--color-text-muted)]">
          Loading ledger...
        </div>

        <div v-else-if="error" class="m-6 rounded-lg border border-[var(--color-danger)] bg-[var(--color-danger)]/20 px-4 py-3 text-sm text-[var(--color-danger)]">
          {{ error }}
        </div>

        <template v-else-if="ledgerData">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full border-collapse" :style="{ fontSize: dynamicRowStyle.fontSize }">
              <thead class="sticky top-0 z-10 bg-[var(--color-surface)]">
                <tr class="border-b border-[var(--color-border)]">
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Date</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Type</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Voucher No</th>
                  <th class="px-4 py-3 text-left font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Reference</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Debit (Dr)</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Credit (Cr)</th>
                  <th class="px-4 py-3 text-right font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">Balance</th>
                </tr>
              </thead>
              <tbody ref="tableBodyRef">
                <!-- Opening Balance row -->
                <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface)]/50">
                  <td colspan="6" class="px-4 font-semibold text-[var(--color-text-muted)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    Opening Balance
                    <span class="ml-1 font-normal text-[var(--color-text-muted)]" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">(before {{ fmtDate(ledgerData.from_date) }})</span>
                  </td>
                  <td class="px-4 text-right font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="ledgerData.opening_balance >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                    ₹{{ fmt(Math.abs(ledgerData.opening_balance)) }}
                    <span class="ml-0.5 font-normal" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ ledgerData.opening_balance < 0 ? 'Cr' : 'Dr' }}</span>
                  </td>
                </tr>

                <!-- No entries message -->
                <tr v-if="!ledgerData.entries.length">
                  <td colspan="7" class="px-4 py-12 text-center text-[var(--color-text-muted)]">
                    No transactions found for the selected period.
                  </td>
                </tr>

                <!-- Ledger rows -->
                <tr
                  v-for="(entry, idx) in ledgerData.entries"
                  :key="idx"
                  :data-idx="idx"
                  @click="onRowClick(entry, idx)"
                  @mouseenter="onRowMouseEnter(entry, idx)"
                  class="cursor-pointer border-b border-[var(--color-border)] transition-colors"
                  :class="focusedIdx === idx
                    ? 'bg-[var(--color-info)]/30 border-l-blue-500'
                    : selectedEntry === entry
                      ? 'bg-[var(--color-info)]/20'
                      : 'hover:bg-[var(--color-surface)]/40'"
                >
                  <td class="px-4 text-[var(--color-text-muted)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ fmtDate(entry.date) }}</td>
                  <td class="px-4" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span
                      class="rounded px-1.5 py-0.5 font-bold"
                      :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }"
                      :class="voucherBadgeClass(entry.voucher_type)"
                    >
                      {{ voucherLabel(entry.voucher_type) }}
                    </span>
                  </td>
                  <td class="px-4" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button
                      @click.stop="openInErpNext(entry.voucher_type, entry.voucher_no)"
                      class="font-mono text-[var(--color-info)] hover:underline"
                    >
                      {{ entry.voucher_no }}
                    </button>
                  </td>
                  <td class="px-4 text-[var(--color-text-muted)]" 
                    :style="{ 
                      paddingTop: dynamicRowStyle.paddingTop, 
                      paddingBottom: dynamicRowStyle.paddingBottom,
                      fontSize: `${(14 * zoomPercent * 0.75) / 100}px` 
                    }">
                    <div class="line-clamp-2 break-words max-w-[150px] leading-[1.1]" :title="entry.reference_no">
                      {{ entry.reference_no || '—' }}
                    </div>
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="entry.debit" class="font-semibold text-[var(--color-success)]">₹{{ fmt(entry.debit) }}</span>
                    <span v-else class="text-[var(--color-text-muted)]">—</span>
                  </td>
                  <td class="px-4 text-right font-mono" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="entry.credit" class="font-semibold text-[var(--color-danger)]">₹{{ fmt(entry.credit) }}</span>
                    <span v-else class="text-[var(--color-text-muted)]">—</span>
                  </td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="entry.balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    ₹{{ fmt(Math.abs(entry.balance)) }}
                    <span class="ml-0.5 font-normal text-[var(--color-text-muted)]" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ entry.balance < 0 ? 'Cr' : 'Dr' }}</span>
                  </td>
                </tr>

                <!-- Closing Balance row -->
                <tr v-if="ledgerData.entries.length" class="border-t-2 border-[var(--color-border)] bg-[var(--color-surface)]/50">
                  <td colspan="4" class="px-4 font-bold text-[var(--color-text)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">Closing Balance</td>
                  <td class="px-4 text-right font-mono font-bold text-[var(--color-success)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">₹{{ fmt(ledgerData.total_debit) }}</td>
                  <td class="px-4 text-right font-mono font-bold text-[var(--color-danger)]" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">₹{{ fmt(ledgerData.total_credit) }}</td>
                  <td class="px-4 text-right font-mono font-bold"
                    :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"
                    :class="ledgerData.closing_balance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    ₹{{ fmt(Math.abs(ledgerData.closing_balance)) }}
                    <span class="ml-0.5 font-normal text-[var(--color-text-muted)]" :style="{ fontSize: `${(10 * zoomPercent) / 100}px` }">{{ ledgerData.closing_balance < 0 ? 'Cr' : 'Dr' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>

      <!-- ── Detail Panel ── -->
      <transition name="slide">
        <div
          v-if="selectedEntry"
          class="flex w-96 shrink-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)]"
        >
          <!-- Panel header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="rounded px-2 py-0.5 text-[10px] font-bold" :class="voucherBadgeClass(selectedEntry.voucher_type)">
                {{ voucherLabel(selectedEntry.voucher_type) }}
              </span>
              <span class="font-mono text-sm font-bold text-[var(--color-text)]">{{ selectedEntry.voucher_no }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="selectedEntry.voucher_type === 'Sales Invoice'"
                @click="openInternalSalesEntry(selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-[var(--color-info)] hover:bg-[var(--color-info)]/20"
              >
                View / Edit
              </button>
              <button
                @click="openInErpNext(selectedEntry.voucher_type, selectedEntry.voucher_no)"
                class="rounded px-2 py-1 text-[10px] font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]"
                title="Open in ERPNext"
              >
                ERPNext ↗
              </button>
              <button @click="closeDetail" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">✕</button>
            </div>
          </div>

          <!-- Loading detail -->
          <div v-if="loadingDetail" class="flex flex-1 items-center justify-center text-sm text-[var(--color-text-muted)]">
            Loading...
          </div>

          <div v-else-if="voucherDetail" class="flex-1 overflow-y-auto p-4">

            <!-- Key fields -->
            <div class="mb-4 space-y-2 rounded-lg bg-[var(--color-surface-raised)] p-3 text-xs">
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Date</span>
                <span class="font-semibold text-[var(--color-text)]">{{ fmtDate(voucherDetail.posting_date) }}</span>
              </div>
              <div v-if="voucherDetail.party_name || voucherDetail.party" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Party</span>
                <span class="font-semibold text-[var(--color-text)] text-right">{{ voucherDetail.party_name || voucherDetail.party }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Amount</span>
                <span class="font-bold text-[var(--color-text)]">₹{{ fmt(voucherDetail.total_amount) }}</span>
              </div>
              <div v-if="voucherDetail.mode_of_payment" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Mode</span>
                <span class="font-semibold text-[var(--color-text)]">{{ voucherDetail.mode_of_payment }}</span>
              </div>
              <div v-if="voucherDetail.outstanding_amount !== undefined" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Outstanding</span>
                <span class="font-semibold" :class="voucherDetail.outstanding_amount > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                  ₹{{ fmt(voucherDetail.outstanding_amount) }}
                </span>
              </div>
              <div v-if="voucherDetail.status" class="flex justify-between">
                <span class="text-[var(--color-text-muted)]">Status</span>
                <span class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                  :class="{
                    'bg-[var(--color-success)]/20 text-[var(--color-success)]': ['Paid', 'Submitted'].includes(voucherDetail.status),
                    'bg-[var(--color-warning)]/20 text-[var(--color-warning)]': voucherDetail.status === 'Unpaid',
                    'bg-[var(--color-info)]/20 text-[var(--color-info)]': voucherDetail.status === 'Partly Paid',
                    'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]': !['Paid','Submitted','Unpaid','Partly Paid'].includes(voucherDetail.status),
                  }"
                >
                  {{ voucherDetail.status }}
                </span>
              </div>
              <div v-if="voucherDetail.remarks" class="pt-1">
                <span class="text-[var(--color-text-muted)]">Remarks</span>
                <p class="mt-0.5 text-[var(--color-text)]">{{ voucherDetail.remarks }}</p>
              </div>
            </div>

            <!-- Line items -->
            <div v-if="voucherDetail.items?.length">
              <div class="mb-2 text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                {{ voucherDetail.voucher_type === 'Payment Entry' ? 'References' :
                   voucherDetail.voucher_type === 'Journal Entry' ? 'Accounts' : 'Items' }}
              </div>

              <!-- Sales/Purchase/Credit items -->
              <template v-if="['Sales Invoice', 'Purchase Invoice', 'Credit Note'].includes(voucherDetail.voucher_type)">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] text-[10px] text-[var(--color-text-muted)]">
                      <th class="pb-1.5 text-left font-normal">Item</th>
                      <th class="pb-1.5 text-right font-normal">Qty</th>
                      <th class="pb-1.5 text-right font-normal">Rate</th>
                      <th class="pb-1.5 text-right font-normal">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, i) in voucherDetail.items" :key="i" class="border-b border-[var(--color-border)]">
                      <td class="py-1.5">
                        <div class="font-semibold text-[var(--color-text)]">{{ item.item_code }}</div>
                        <div class="text-[10px] text-[var(--color-text-muted)]">{{ item.item_name }}</div>
                      </td>
                      <td class="py-1.5 text-right text-[var(--color-text-muted)]">{{ item.qty }} {{ item.uom }}</td>
                      <td class="py-1.5 text-right font-mono text-[var(--color-text-muted)]">₹{{ fmt(item.rate) }}</td>
                      <td class="py-1.5 text-right font-mono font-semibold text-[var(--color-text)]">₹{{ fmt(item.amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </template>

              <!-- Payment Entry references -->
              <template v-else-if="voucherDetail.voucher_type === 'Payment Entry'">
                <div v-for="(ref, i) in voucherDetail.items" :key="i"
                  class="mb-1.5 flex items-center justify-between rounded bg-[var(--color-surface-raised)] px-3 py-2 text-xs">
                  <div>
                    <span class="text-[10px] text-[var(--color-text-muted)]">{{ ref.reference_doctype }}</span>
                    <button
                      @click="openInErpNext(ref.reference_doctype, ref.reference_name)"
                      class="ml-1 font-mono text-[var(--color-info)] hover:underline"
                    >{{ ref.reference_name }}</button>
                  </div>
                  <span class="font-mono font-semibold text-[var(--color-success)]">₹{{ fmt(ref.allocated_amount) }}</span>
                </div>
              </template>

              <!-- Journal Entry accounts -->
              <template v-else-if="voucherDetail.voucher_type === 'Journal Entry'">
                <!-- Linked References section -->
                <template v-if="voucherDetail.items.some(a => a.reference_name)">
                  <div class="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--color-info)]">Linked References</div>
                  <div
                    v-for="(acc, i) in voucherDetail.items.filter(a => a.reference_name)"
                    :key="'ref-' + i"
                    class="mb-1.5 flex items-center justify-between rounded bg-[var(--color-info)]/30 px-3 py-2 text-xs border border-[var(--color-info)]/40"
                  >
                    <div class="flex flex-col gap-0.5">
                      <span class="text-[10px] text-[var(--color-info)]">{{ acc.reference_type }}</span>
                      <button
                        @click="openInErpNext(acc.reference_type, acc.reference_name)"
                        class="font-mono text-[var(--color-info)] hover:text-[var(--color-info)] hover:underline text-left"
                      >{{ acc.reference_name }}</button>
                      <span v-if="acc.party" class="text-[10px] text-[var(--color-text-muted)]">{{ acc.party_type }}: {{ acc.party }}</span>
                    </div>
                    <div class="flex flex-col items-end gap-0.5">
                      <span v-if="acc.credit" class="font-mono font-semibold text-[var(--color-success)]">₹{{ fmt(acc.credit) }} Cr</span>
                      <span v-if="acc.debit" class="font-mono font-semibold text-[var(--color-danger)]">₹{{ fmt(acc.debit) }} Dr</span>
                    </div>
                  </div>
                  <div class="my-2 border-t border-[var(--color-border)]"></div>
                </template>
                <!-- All accounts breakdown -->
                <div class="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">Accounts</div>
                <table class="w-full text-xs">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] text-[10px] text-[var(--color-text-muted)]">
                      <th class="pb-1.5 text-left font-normal">Account</th>
                      <th class="pb-1.5 text-right font-normal">Dr</th>
                      <th class="pb-1.5 text-right font-normal">Cr</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(acc, i) in voucherDetail.items" :key="i" class="border-b border-[var(--color-border)]">
                      <td class="py-1.5 text-[var(--color-text)]">
                        {{ acc.account }}
                        <span v-if="acc.party" class="ml-1 text-[10px] text-[var(--color-text-muted)]">({{ acc.party }})</span>
                      </td>
                      <td class="py-1.5 text-right font-mono text-[var(--color-danger)]">
                        <span v-if="acc.debit">₹{{ fmt(acc.debit) }}</span>
                        <span v-else class="text-[var(--color-text-muted)]">—</span>
                      </td>
                      <td class="py-1.5 text-right font-mono text-[var(--color-success)]">
                        <span v-if="acc.credit">₹{{ fmt(acc.credit) }}</span>
                        <span v-else class="text-[var(--color-text-muted)]">—</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </template>
            </div>
          </div>
        </div>
      </transition>

    </div>

    <SalesEntry
      v-if="showSalesEntryWindow"
      :is-sub-window="true"
      :invoice-name="subWindowInvoiceName"
      @close="showSalesEntryWindow = false"
    />

    <StockLedger
      v-if="showStockLedgerWindow"
      :is-sub-window="true"
      :item-code="stockLedgerItemCode"
      :initial-from-date="stockLedgerFromDate"
      :initial-to-date="stockLedgerToDate"
      @close="showStockLedgerWindow = false"
    />

    <!-- PRINT MODAL -->
    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="printKey"
      :doctype="''"
      @close="showPrintModal = false"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="ledgerCustSearchModalRef"
      :show="showCustomerSearchModal"
      :allowed-types="isBiller ? ['Customer', 'Supplier', 'Employee'] : undefined"
      @close="closeCustomerSearchModal"
      @select="(c, d) => { pickLedger(c, d); closeCustomerSearchModal() }"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="ledgerItemSearchModalRef"
      :show="showItemSearchModal"
      v-model:query="itemSearchQuery"
      v-model:selectedIdx="itemDDIdx"
      :results="itemSearchResults"
      @close="closeItemSearch"
      @select="pickItem"
      @refresh="refreshItemSearch"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchLedger, fetchVoucherDetail, frappeGet } from '../api.js'
import SalesEntry from './SalesInvoice.vue'
import StockLedger from './StockLedger.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import ItemSearch from '../components/ItemSearch.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import { searchItems } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'
import { getUserRole } from '../composables/usePermission'

const isBiller = getUserRole() === 'biller'

const props = defineProps({
  isSubWindow: {
    type: Boolean,
    default: false
  },
  ledgerName: {
    type: String,
    default: ''
  },
  ledgerType: {
    type: String,
    default: 'Customer'
  },
  initialFromDate: {
    type: String,
    default: ''
  },
  initialToDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

if (props.isSubWindow) useSubwindow()

const router = useRouter()
const route = useRoute()

function handleBack() {
  if (props.isSubWindow) {
    emit('close')
  } else {
    router.push('/')
  }
}

const showSalesEntryWindow = ref(false)
const subWindowInvoiceName = ref('')

// ─── Stock Ledger Sub-window ──────────────────────────────────────────────────
const showStockLedgerWindow = ref(false)
const stockLedgerItemCode = ref('')
const stockLedgerFromDate = ref('')
const stockLedgerToDate = ref('')

function openStockLedger(itemCode, dates = null) {
  stockLedgerItemCode.value = itemCode
  if (dates) {
    stockLedgerFromDate.value = dates.from
    stockLedgerToDate.value = dates.to
  } else {
    stockLedgerFromDate.value = ''
    stockLedgerToDate.value = ''
  }
  showStockLedgerWindow.value = true
}

// ─── Item Search Modal State ──────────────────────────────────────────────────
const showItemSearchModal = ref(false)
const itemSearchQuery = ref('')
const allItems = ref([])
const itemSearchResults = ref([])
const itemDDIdx = ref(0)
const ledgerItemSearchModalRef = ref(null)
const isItemLoading = ref(false)

async function refreshItemSearch() {
  isItemLoading.value = true
  try {
    const items = await searchItems('')
    allItems.value = items.map(i => ({ 
      ...i, 
      price: 0, 
      stock: 0, 
      _loading: true,
      enriched: false 
    }))
    filterItems()
  } catch (e) {
    console.error('Item search refresh failed:', e)
  } finally {
    isItemLoading.value = false
  }
}

function filterItems() {
  const q = itemSearchQuery.value.toLowerCase().trim()
  if (!q) {
    itemSearchResults.value = allItems.value.slice(0, 100)
    return
  }
  itemSearchResults.value = allItems.value.filter(i =>
    i.item_code.toLowerCase().includes(q) ||
    i.item_name.toLowerCase().includes(q)
  ).slice(0, 100)
  itemDDIdx.value = 0
}

watch(itemSearchQuery, filterItems)

async function openItemSearch() {
  showItemSearchModal.value = true
  if (allItems.value.length === 0) {
    await refreshItemSearch()
  } else {
    filterItems()
  }
  nextTick(() => ledgerItemSearchModalRef.value?.focus())
}

function closeItemSearch() {
  showItemSearchModal.value = false
}

function pickItem(item, dates) {
  showItemSearchModal.value = false
  openStockLedger(item.item_code, dates)
}

// ─── Ledger Search Modal State ──────────────────────────────────────────────
const showCustomerSearchModal = ref(false)
const ledgerCustSearchModalRef = ref(null)

function openCustomerSearch() {
  showCustomerSearchModal.value = true
}

function closeCustomerSearchModal() {
  showCustomerSearchModal.value = false
}

function pickLedger(l, dates) {
  if (isBiller && l.type === 'Account') return
  selectedLedger.value = l
  if (dates) {
    fromDate.value = dates.from
    toDate.value = dates.to
  }
  loadLedger()
}

function clearLedger() {
  selectedLedger.value = null
  ledgerData.value = null
  error.value = ''
}

// ─── Print ────────────────────────────────────────────────────────────────────
const showPrintModal = ref(false)
const printKey = computed(() => {
  if (!selectedLedger.value) return ''
  return `${selectedLedger.value.name}||${fromDate.value}||${toDate.value}||${selectedLedger.value.type || 'Account'}`
})

// ─── Zoom ─────────────────────────────────────────────────────────────────────
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)
const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`,
  paddingTop: `${(4 * zoomPercent.value) / 100}px`,
  paddingBottom: `${(4 * zoomPercent.value) / 100}px`
}))

watch(zoomPercent, (newZoom) => {
  localStorage.setItem('wb-zoom', newZoom.toString())
})

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

function getNinetyDaysAgoIST() {
  const date = new Date(Date.now() - 90 * 86400000)
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ─── Filter state ─────────────────────────────────────────────────────────────
const today = getTodayIST()
const ninetyDaysAgo = getNinetyDaysAgoIST()

const selectedLedger = ref(null)
const fromDate = ref(ninetyDaysAgo)
const toDate = ref(today)
const dateInput = ref(null)

// ─── Ledger state ─────────────────────────────────────────────────────────────
const loading = ref(false)
const error = ref('')
const ledgerData = ref(null)

// ─── Detail panel state ───────────────────────────────────────────────────────
const selectedEntry = ref(null)
const voucherDetail = ref(null)
const loadingDetail = ref(false)

// Ledger row keyboard navigation
const focusedIdx = ref(-1)
const tableBodyRef = ref(null)

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(n || 0)
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function fmtDate(d) {
  if (!d) return ''
  const date = new Date(d + 'T00:00:00')
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()
  return `${dd}/${mm}/${yyyy}`
}

const VOUCHER_CONFIG = {
  'Sales Invoice':    { label: 'SINV', cls: 'bg-[var(--color-info)]/20 text-[var(--color-info)]' },
  'Payment Entry':    { label: 'PAY',  cls: 'bg-[var(--color-success)]/20 text-[var(--color-success)]' },
  'Journal Entry':    { label: 'JE',   cls: 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' },
  'Purchase Invoice': { label: 'PINV', cls: 'bg-[var(--color-supplier)]/20 text-[var(--color-supplier)]' },
  'Credit Note':      { label: 'CN',   cls: 'bg-[var(--color-employee)]/20 text-[var(--color-employee)]' },
  'Expense Claim':    { label: 'EXP',  cls: 'bg-[var(--color-employee)]/20 text-[var(--color-employee)]' },
}

function voucherLabel(type) {
  return VOUCHER_CONFIG[type]?.label ?? type?.slice(0, 4).toUpperCase() ?? '?'
}
function voucherBadgeClass(type) {
  return VOUCHER_CONFIG[type]?.cls ?? 'bg-[var(--color-surface)] text-[var(--color-text-muted)]'
}

function openInErpNext(voucherType, voucherNo) {
  const slug = voucherType.toLowerCase().replace(/ /g, '-')
  window.open(`/app/${slug}/${voucherNo}`, '_blank')
}

// ─── Load Ledger ──────────────────────────────────────────────────────────────
async function loadLedger() {
  if (!selectedLedger.value) return
  loading.value = true
  error.value = ''
  ledgerData.value = null
  selectedEntry.value = null
  voucherDetail.value = null
  focusedIdx.value = -1

  try {
    ledgerData.value = await fetchLedger(
      selectedLedger.value.name,
      selectedLedger.value.type || 'Account',
      fromDate.value,
      toDate.value,
    )
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// Auto-reload when dates change
watch(fromDate, () => { if (selectedLedger.value) loadLedger() })
watch(toDate,   () => { if (selectedLedger.value) loadLedger() })

// ─── Row hover/keyboard → update preview ───────────────────────────────────
async function updatePreview(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx
  if (selectedEntry.value === entry) return

  selectedEntry.value = entry
  voucherDetail.value = null
  
  // 1. Try to get from pre-fetched cache
  const cached = ledgerData.value?.voucher_details?.[entry.voucher_no]
  if (cached) {
    voucherDetail.value = cached
    return
  }

  // 2. Fallback to API if not in cache (e.g. legacy data or unusual type)
  loadingDetail.value = true
  try {
    voucherDetail.value = await fetchVoucherDetail(entry.voucher_type, entry.voucher_no)
  } catch (e) {
    voucherDetail.value = { error: e.message }
  } finally {
    loadingDetail.value = false
  }
}

function onRowMouseEnter(entry, idx) {
  updatePreview(entry, idx)
}

async function onRowClick(entry, idx) {
  if (idx !== undefined) focusedIdx.value = idx

  if (entry.voucher_type === 'Sales Invoice') {
    openInternalSalesEntry(entry.voucher_no)
    return
  }

  if (selectedEntry.value === entry && voucherDetail.value) {
    // Already showing
  } else {
    updatePreview(entry, idx)
  }
}

function openInternalSalesEntry(invoiceNo) {
  subWindowInvoiceName.value = invoiceNo
  showSalesEntryWindow.value = true
}

function closeDetail() {
  selectedEntry.value = null
  voucherDetail.value = null
  clearTimeout(previewTimer)
}

function onTableKeydown(e) {
  if (!ledgerData.value?.entries?.length) return
  const len = ledgerData.value.entries.length

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedIdx.value = Math.min(focusedIdx.value + 1, len - 1)
    updatePreview(ledgerData.value.entries[focusedIdx.value], focusedIdx.value)
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIdx.value = Math.max(focusedIdx.value - 1, 0)
    updatePreview(ledgerData.value.entries[focusedIdx.value], focusedIdx.value)
    scrollRowIntoView(focusedIdx.value)
  } else if (e.key === 'Enter' && focusedIdx.value >= 0) {
    e.preventDefault()
    const entry = ledgerData.value.entries[focusedIdx.value]
    if (entry.voucher_type === 'Sales Invoice') {
      openInternalSalesEntry(entry.voucher_no)
    } else {
      onRowClick(entry, focusedIdx.value)
    }
  }
}

function scrollRowIntoView(idx) {
  nextTick(() => {
    const rows = tableBodyRef.value?.querySelectorAll('tr[data-idx]')
    rows?.[idx]?.scrollIntoView({ block: 'nearest' })
  })
}

function onGlobalKeydown(e) {
  if (showSalesEntryWindow.value) return
  if (showCustomerSearchModal.value || showItemSearchModal.value) {
    if (e.key === 'Escape') {
      if (showCustomerSearchModal.value) closeCustomerSearchModal()
      if (showItemSearchModal.value) closeItemSearch()
    }
    return
  }

  if (e.key === 'Escape') {
    if (selectedEntry.value) {
      e.preventDefault()
      closeDetail()
      return
    }
    e.preventDefault()
    handleBack()
    return
  }

  if (e.ctrlKey && e.key === 'l') {
    e.preventDefault()
    openCustomerSearch()
    return
  }

  if (e.ctrlKey && e.key === 'i') {
    e.preventDefault()
    openItemSearch()
    return
  }

  if (e.ctrlKey && e.key === 'p' && ledgerData.value) {
    e.preventDefault()
    showPrintModal.value = true
    return
  }

  if (!ledgerData.value) return
  onTableKeydown(e)
}

onMounted(async () => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('keydown', onGlobalKeydown)

  if (props.initialFromDate) fromDate.value = props.initialFromDate
  if (props.initialToDate) toDate.value = props.initialToDate

  const targetName = props.ledgerName || route.query.customer || route.query.ledger
  const targetType = props.ledgerType || (route.query.customer ? 'Customer' : 'Account')

  if (targetName) {
    loading.value = true
    try {
      let label = targetName
      if (targetType === 'Customer') {
        const doc = await frappeGet('frappe.client.get', { doctype: 'Customer', name: targetName })
        label = doc.customer_name
      } else if (targetType === 'Supplier') {
        const doc = await frappeGet('frappe.client.get', { doctype: 'Supplier', name: targetName })
        label = doc.supplier_name
      } else if (targetType === 'Employee') {
        const doc = await frappeGet('frappe.client.get', { doctype: 'Employee', name: targetName })
        label = doc.employee_name
      } else {
        const doc = await frappeGet('frappe.client.get', { doctype: 'Account', name: targetName })
        label = doc.account_name
      }

      selectedLedger.value = {
        name: targetName,
        label: label,
        type: targetType
      }
      loadLedger()
    } catch (e) {
      console.warn('[Ledger] Failed to auto-load:', e.message)
    } finally {
      loading.value = false
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.removeEventListener('keydown', onGlobalKeydown)
})
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
