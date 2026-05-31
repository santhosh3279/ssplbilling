<template>
  <div v-if="show" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="w-full max-w-[96vw] h-[90vh] rounded-3xl bg-[var(--color-surface)] shadow-2xl border border-[var(--color-border)] flex flex-col overflow-hidden">

      <!-- HEADER -->
      <div class="flex items-center justify-between px-6 py-5 border-b border-[var(--color-border)] shrink-0">
        <div class="flex items-center gap-5">
          <h2 class="text-4xl font-black uppercase tracking-tight text-[var(--color-text)]">Outstanding Items</h2>
          <span v-if="party" class="text-2xl font-bold text-[var(--color-highlight)] bg-[var(--color-highlight)]/10 px-4 py-1.5 rounded-lg font-mono">{{ party }}</span>
          <!-- Direction Filter -->
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5">
            <button
              v-for="d in ['All', 'Dr', 'Cr']"
              :key="d"
              @click="filterDirection = d"
              class="min-w-[60px] rounded-md px-4 py-1.5 text-[20px] font-black uppercase transition-all duration-150"
              :class="filterDirection === d ? 'bg-[var(--color-highlight)] text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >{{ d }}</button>
          </div>

          <!-- Type Filter -->
          <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-0.5 ml-4">
            <button
              @click="showTypeInv = !showTypeInv"
              class="min-w-[80px] rounded-md px-4 py-1.5 text-[20px] font-black uppercase transition-all duration-150 flex items-center justify-center gap-2"
              :class="showTypeInv ? 'bg-[var(--color-danger)] text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              <span v-if="showTypeInv">●</span> Invoices
            </button>
            <button
              v-if="!disablePayments"
              @click="showTypePay = !showTypePay"
              class="min-w-[80px] rounded-md px-4 py-1.5 text-[20px] font-black uppercase transition-all duration-150 flex items-center justify-center gap-2"
              :class="showTypePay ? 'bg-[var(--color-success)] text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              <span v-if="showTypePay">●</span> Payments
            </button>
            <button
              @click="showTypeJrn = !showTypeJrn"
              class="min-w-[80px] rounded-md px-4 py-1.5 text-[20px] font-black uppercase transition-all duration-150 flex items-center justify-center gap-2"
              :class="showTypeJrn ? 'bg-[var(--color-info)] text-white shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              <span v-if="showTypeJrn">●</span> Journals
            </button>
          </div>
        </div>
        <button @click="$emit('close')" class="h-11 w-11 rounded-full hover:bg-[var(--color-midlight)] flex items-center justify-center text-2xl transition-colors">✕</button>
      </div>

      <!-- SUMMARY STRIP -->
      <div class="grid grid-cols-4 divide-x divide-[var(--color-border)] border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface-raised)]/40">
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Net Outstanding</span>
          <span class="text-5xl font-black font-mono"
            :class="netOutstanding > 0.005 ? 'text-[var(--color-danger)]' : netOutstanding < -0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'">
            ₹{{ fmt(netOutstanding) }}<span class="text-2xl ml-1 font-bold">{{ netOutstanding > 0.005 ? 'Dr' : netOutstanding < -0.005 ? 'Cr' : '' }}</span>
          </span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Entered Amount</span>
          <span class="text-5xl font-black font-mono text-[var(--color-text)]">₹{{ fmt(enteredAmount) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Total Allocated</span>
          <span class="text-5xl font-black font-mono text-[var(--color-success)]">₹{{ fmt(totalAllocated) }}</span>
        </div>
        <div class="flex flex-col items-center justify-center py-4 gap-1">
          <span class="text-[18px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] opacity-70">Remaining Balance</span>
          <span class="text-5xl font-black font-mono"
            :class="Math.abs(remainingBalance) < 0.005 ? 'text-[var(--color-success)]' : remainingBalance < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">
            {{ remainingBalance < -0.005 ? '-' : '' }}₹{{ fmt(Math.abs(remainingBalance)) }}
          </span>
        </div>
      </div>

      <!-- TABLE -->
      <div class="flex-1 overflow-y-auto custom-scrollbar">

        <!-- Loading -->
        <div v-if="isLoading" class="flex items-center justify-center py-24 gap-3 text-[var(--color-text-muted)]">
          <svg class="animate-spin w-8 h-8 shrink-0" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span class="text-3xl font-bold">Loading...</span>
        </div>

        <!-- Empty -->
        <div v-else-if="!filteredInvoices.length && !filteredPayments.length && !filteredJournals.length"
          class="flex flex-col items-center justify-center py-24 gap-4 text-[var(--color-text-muted)]">
          <span class="text-[6rem] opacity-30">✓</span>
          <span class="text-3xl font-bold">No outstanding items found</span>
        </div>

        <table v-else class="w-full table-fixed border-collapse">
          <colgroup>
            <col style="width:26%" />
            <col style="width:8%" />
            <col style="width:8%" />
            <col style="width:6%" />
            <col style="width:5%" />
            <col style="width:13%" />
            <col style="width:7%" />
            <col style="width:10%" />
            <col style="width:17%" />
          </colgroup>

          <thead class="sticky top-0 z-10 bg-[var(--color-surface-raised)]">
            <tr class="border-b border-[var(--color-border)] text-[20px] font-black uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
              <th class="px-6 py-3 text-left">Reference</th>
              <th class="px-3 py-3 text-left">Type</th>
              <th class="px-3 py-3 text-center">Date</th>
              <th class="px-3 py-3 text-center">Age</th>
              <th class="px-3 py-3 text-center">Dir</th>
              <th class="px-3 py-3 text-right">Outstanding</th>
              <th class="px-3 py-3 text-center">Linked</th>
              <th class="px-3 py-3 text-right">Allocate</th>
              <th class="px-3 py-3 text-right">Balance</th>
            </tr>
          </thead>

          <tbody>

            <!-- OUTSTANDING INVOICES -->
            <template v-if="filteredInvoices.length">
              <tr class="bg-[var(--color-danger)]/5 border-b border-[var(--color-danger)]/15">
                <td colspan="9" class="px-6 py-2">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-danger)] shrink-0"></span>
                    <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-danger)]">Outstanding Invoices & Returns</span>
                    <span class="ml-auto text-[20px] font-bold text-[var(--color-danger)] opacity-60">{{ filteredInvoices.length }}</span>
                  </div>
                </td>
              </tr>
              <tr v-for="inv in filteredInvoices" :key="inv.name"
                class="border-b border-[var(--color-border)] hover:bg-[var(--color-midlight)]/20 transition-colors">
                <td class="px-6 py-3 max-w-0">
                  <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ inv.name }}</div>
                </td>
                <td class="px-3 py-3 text-[20px] font-semibold text-[var(--color-text-muted)]">
                  {{ inv.doctype === 'Sales Invoice' ? 'Sales Inv' : 'Purch Inv' }}
                </td>
                <td class="px-3 py-3 text-center text-[20px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(inv.posting_date) }}</td>
                <td class="px-3 py-3 text-center text-[20px] font-black"
                  :class="dueDays(inv.posting_date) > 30 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)] opacity-50'">
                  {{ dueDays(inv.posting_date) }}d
                </td>
                <td class="px-3 py-3 text-center">
                  <span class="px-1.5 py-0.5 rounded text-[20px] font-black uppercase"
                    :class="inv.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                    {{ inv.direction }}
                  </span>
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono"
                    :class="inv.direction === 'Cr' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                    ₹{{ fmt(inv.outstanding_amount) }}
                  </span>
                  <span v-if="inv.grand_total && Math.abs(inv.grand_total - inv.outstanding_amount) > 0.005"
                    class="text-[20px] font-bold font-mono text-[var(--color-text-muted)] opacity-50 ml-1">
                    / ₹{{ fmt(inv.grand_total) }}
                  </span>
                </td>
                <td class="px-3 py-3 text-center">
                  <span v-if="inv.linked_count > 0"
                    @click="showLinkedDocs(inv.doctype, inv.name)"
                    class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[20px] font-black bg-[var(--color-highlight)]/15 text-[var(--color-highlight)] cursor-pointer hover:bg-[var(--color-highlight)]/30 transition-colors">
                    {{ inv.linked_count }}
                  </span>
                  <span v-else class="text-[20px] text-[var(--color-text-muted)] opacity-30">—</span>
                </td>
                <td class="px-3 py-3">
                  <input v-model.number="localAmounts[inv.name]" type="number" step="0.01" min="0"
                    :max="Math.abs(inv.outstanding_amount)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-3 text-right font-mono text-[20px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                    @keydown.enter="focusNextAllocate($event)" @input="onAllocationChange(inv.name)" />
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono"
                    :class="balanceFor(inv.name, inv.outstanding_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                    ₹{{ fmt(balanceFor(inv.name, inv.outstanding_amount)) }}
                  </span>
                </td>
              </tr>
            </template>

            <!-- UNLINKED PAYMENT ENTRIES -->
            <template v-if="filteredPayments.length">
              <tr class="bg-[var(--color-success)]/5 border-b border-[var(--color-success)]/15">
                <td colspan="9" class="px-6 py-2">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-success)] shrink-0"></span>
                    <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-success)]">Unlinked Payment Entries</span>
                    <span class="ml-auto text-[20px] font-bold text-[var(--color-success)] opacity-60">{{ filteredPayments.length }}</span>
                  </div>
                </td>
              </tr>
              <tr v-for="pe in filteredPayments" :key="pe.name"
                class="border-b border-[var(--color-border)] hover:bg-[var(--color-midlight)]/20 transition-colors">
                <td class="px-6 py-3 max-w-0">
                  <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ pe.name }}</div>
                  <div v-if="pe.remarks" class="text-[20px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ pe.remarks }}</div>
                </td>
                <td class="px-3 py-3 text-[20px] font-semibold text-[var(--color-text-muted)]">Payment</td>
                <td class="px-3 py-3 text-center text-[20px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(pe.posting_date) }}</td>
                <td class="px-3 py-3 text-center text-[20px] font-black text-[var(--color-text-muted)] opacity-50">{{ dueDays(pe.posting_date) }}d</td>
                <td class="px-3 py-3 text-center">
                  <span class="px-1.5 py-0.5 rounded text-[20px] font-black uppercase"
                    :class="pe.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                    {{ pe.direction }}
                  </span>
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono text-[var(--color-success)]">₹{{ fmt(pe.unallocated_amount) }}</span>
                  <span v-if="pe.paid_amount && Math.abs(pe.paid_amount - pe.unallocated_amount) > 0.005"
                    class="text-[20px] font-bold font-mono text-[var(--color-text-muted)] opacity-50 ml-1">
                    / ₹{{ fmt(pe.paid_amount) }}
                  </span>
                </td>
                <td class="px-3 py-3 text-center">
                  <span v-if="pe.linked_count > 0"
                    @click="showLinkedDocs('Payment Entry', pe.name)"
                    class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[20px] font-black bg-[var(--color-highlight)]/15 text-[var(--color-highlight)] cursor-pointer hover:bg-[var(--color-highlight)]/30 transition-colors">
                    {{ pe.linked_count }}
                  </span>
                  <span v-else class="text-[20px] text-[var(--color-text-muted)] opacity-30">—</span>
                </td>
                <td class="px-3 py-3">
                  <input v-model.number="localAmounts[pe.name]" type="number" step="0.01" min="0"
                    :max="Math.abs(pe.unallocated_amount)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-3 text-right font-mono text-[20px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                    @keydown.enter="focusNextAllocate($event)" @input="onAllocationChange(pe.name)" />
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono"
                    :class="balanceFor(pe.name, pe.unallocated_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                    ₹{{ fmt(balanceFor(pe.name, pe.unallocated_amount)) }}
                  </span>
                </td>
              </tr>
            </template>

            <!-- UNLINKED JOURNAL ENTRIES -->
            <template v-if="filteredJournals.length">
              <tr class="bg-[var(--color-info)]/5 border-b border-[var(--color-info)]/15">
                <td colspan="9" class="px-6 py-2">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-[var(--color-info)] shrink-0"></span>
                    <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-info)]">Unlinked Journal Entries</span>
                    <span class="ml-auto text-[20px] font-bold text-[var(--color-info)] opacity-60">{{ filteredJournals.length }}</span>
                  </div>
                </td>
              </tr>
              <tr v-for="je in filteredJournals" :key="je.reference_row || (je.name + je.account)"
                class="border-b border-[var(--color-border)] hover:bg-[var(--color-midlight)]/20 transition-colors">
                <td class="px-6 py-3 max-w-0">
                  <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ je.name }}</div>
                  <div v-if="je.remarks" class="text-[20px] italic text-[var(--color-text-muted)] truncate opacity-70">{{ je.remarks }}</div>
                </td>
                <td class="px-3 py-3 text-[20px] font-semibold text-[var(--color-text-muted)]">Journal</td>
                <td class="px-3 py-3 text-center text-[20px] font-bold text-[var(--color-text-muted)]">{{ fmtDate(je.posting_date) }}</td>
                <td class="px-3 py-3 text-center text-[20px] font-black text-[var(--color-text-muted)] opacity-50">{{ dueDays(je.posting_date) }}d</td>
                <td class="px-3 py-3 text-center">
                  <span class="px-1.5 py-0.5 rounded text-[20px] font-black uppercase"
                    :class="je.direction === 'Cr' ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/15 text-[var(--color-danger)]'">
                    {{ je.direction }}
                  </span>
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono text-[var(--color-info)]">₹{{ fmt(je.unallocated_amount) }}</span>
                  <span v-if="(je.journal_total_debit || je.total_amount) && Math.abs((je.journal_total_debit || je.total_amount) - je.unallocated_amount) > 0.005"
                    class="text-[20px] font-bold font-mono text-[var(--color-text-muted)] opacity-50 ml-1">
                    / ₹{{ fmt(je.journal_total_debit || je.total_amount) }}
                  </span>
                </td>
                <td class="px-3 py-3 text-center">
                  <span v-if="je.linked_count > 0"
                    @click="showLinkedDocs('Journal Entry', je.name)"
                    class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[20px] font-black bg-[var(--color-highlight)]/15 text-[var(--color-highlight)] cursor-pointer hover:bg-[var(--color-highlight)]/30 transition-colors">
                    {{ je.linked_count }}
                  </span>
                  <span v-else class="text-[20px] text-[var(--color-text-muted)] opacity-30">—</span>
                </td>
                <td class="px-3 py-3">
                  <input v-model.number="localAmounts[je.reference_row]" type="number" step="0.01" min="0"
                    :max="Math.abs(je.unallocated_amount)"
                    class="allocate-input w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-2 px-3 text-right font-mono text-[20px] font-black text-[var(--color-highlight)] focus:border-[var(--color-highlight)] focus:ring-2 focus:ring-[var(--color-highlight)]/10 outline-none disabled:opacity-20 disabled:grayscale transition-all"
                    @keydown.enter="focusNextAllocate($event)" @input="onAllocationChange(je.reference_row)" />
                </td>
                <td class="px-3 py-3 text-right">
                  <span class="text-[20px] font-black font-mono"
                    :class="balanceFor(je.reference_row, je.unallocated_amount) < 0.005 ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)] opacity-60'">
                    ₹{{ fmt(balanceFor(je.reference_row, je.unallocated_amount)) }}
                  </span>
                </td>
              </tr>
            </template>

          </tbody>
        </table>
      </div>

      <!-- FOOTER -->
      <div class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]/60 px-6 py-5 flex items-center justify-between">
        <div class="text-[20px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest flex items-center gap-4">
          <span>{{ totalItemCount }} item{{ totalItemCount !== 1 ? 's' : '' }}</span>
          <span class="opacity-30">·</span>
          <span>{{ allocatedCount }} allocated</span>
        </div>
        <button
          ref="confirmBtn"
          @click="confirmAdjustments"
          class="rounded-2xl bg-[var(--color-highlight)] px-12 py-5 text-4xl font-black uppercase tracking-widest text-white hover:brightness-110 active:scale-95 transition-all shadow-xl shadow-[var(--color-highlight)]/20"
        >
          Confirm Adjustments
        </button>
      </div>

    </div>
  </div>

  <!-- LINKED DOCUMENTS POPUP -->
  <div v-if="linkedPopup.show"
    class="fixed inset-0 z-[120] flex items-center justify-center bg-black/40 backdrop-blur-sm"
    @click.self="linkedPopup.show = false">
    <div class="w-full max-w-2xl rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] shadow-2xl flex flex-col overflow-hidden">

      <!-- popup header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
        <div class="flex flex-col gap-0.5">
          <span class="text-[20px] font-black uppercase tracking-widest text-[var(--color-text)]">Linked Documents</span>
          <span class="text-[20px] font-bold font-mono text-[var(--color-highlight)]">{{ linkedPopup.docname }}</span>
        </div>
        <button @click="linkedPopup.show = false"
          class="h-9 w-9 rounded-full hover:bg-[var(--color-midlight)] flex items-center justify-center text-xl transition-colors">✕</button>
      </div>

      <!-- popup body -->
      <div class="overflow-y-auto custom-scrollbar" style="max-height:60vh;">
        <div v-if="linkedPopup.loading" class="flex items-center justify-center py-12 gap-3 text-[var(--color-text-muted)]">
          <svg class="animate-spin w-5 h-5" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span class="text-[20px] font-bold">Loading...</span>
        </div>

        <div v-else-if="!linkedPopup.docs.length"
          class="flex items-center justify-center py-12 text-[20px] text-[var(--color-text-muted)]">
          No linked documents found.
        </div>

        <table v-else class="w-full table-fixed border-collapse">
          <colgroup>
            <col style="width:40%" />
            <col style="width:20%" />
            <col style="width:15%" />
            <col style="width:25%" />
          </colgroup>
          <thead class="sticky top-0 bg-[var(--color-surface-raised)]">
            <tr class="border-b border-[var(--color-border)] text-[20px] font-black uppercase tracking-[0.12em] text-[var(--color-text-muted)]">
              <th class="px-6 py-2.5 text-left">Document</th>
              <th class="px-3 py-2.5 text-left">Type</th>
              <th class="px-3 py-2.5 text-center">Date</th>
              <th class="px-3 py-2.5 text-right">Allocated</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(doc, i) in linkedPopup.docs" :key="i"
              class="border-b border-[var(--color-border)] hover:bg-[var(--color-midlight)]/20 transition-colors">
              <td class="px-6 py-3 max-w-0">
                <div class="font-mono text-[20px] font-black text-[var(--color-text)] truncate">{{ doc.name }}</div>
              </td>
              <td class="px-3 py-3 text-[20px] font-semibold text-[var(--color-text-muted)]">
                {{ doc.link_doctype === 'Payment Entry' ? 'Payment' : doc.link_doctype === 'Journal Entry' ? 'Journal' : doc.link_doctype }}
              </td>
              <td class="px-3 py-3 text-center text-[20px] font-bold text-[var(--color-text-muted)]">
                {{ doc.posting_date ? fmtDate(doc.posting_date) : '—' }}
              </td>
              <td class="px-3 py-3 text-right text-[20px] font-black font-mono text-[var(--color-success)]">
                ₹{{ fmt(doc.allocated_amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- popup footer -->
      <div v-if="!linkedPopup.loading && linkedPopup.docs.length"
        class="px-6 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)]/50 flex items-center justify-between">
        <span class="text-[20px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
          {{ linkedPopup.docs.length }} document{{ linkedPopup.docs.length !== 1 ? 's' : '' }}
        </span>
        <span class="text-[20px] font-black font-mono text-[var(--color-success)]">
          Total ₹{{ fmt(linkedPopup.totalAllocated) }}
        </span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { frappeGet } from '../api.js'

const props = defineProps({
  show: Boolean,
  loading: { type: Boolean, default: false },
  partyType: { type: String, default: '' },
  party: { type: String, default: '' },
  enteredAmount: { type: Number, default: 0 },
  activeTab: String,
  modalAmounts: { type: Object, default: () => ({}) },
  disablePayments: { type: Boolean, default: false },
  // Backward-compat props (used when data is passed in from parent)
  invoices: { type: Array, default: () => [] },
  unlinkedPayments: { type: Array, default: () => [] },
  unlinkedJournals: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'update-allocations'])

const localLoading = ref(false)
const localInvoices = ref([])
const localPayments = ref([])
const localJournals = ref([])
const filterDirection = ref('All')
const showTypeInv = ref(true)
const showTypePay = ref(!props.disablePayments)
const showTypeJrn = ref(true)

watch(() => props.disablePayments, (val) => {
  if (val) showTypePay.value = false
  else showTypePay.value = true
})
const localAmounts = ref({})
const lastModifiedKey = ref(null)
const confirmBtn = ref(null)
const linkedPopup = ref({ show: false, docname: '', doctype: '', docs: [], totalAllocated: 0, loading: false })

const isLoading = computed(() => props.loading || localLoading.value)

async function fetchData() {
  if (!props.party || !props.partyType) return
  localLoading.value = true
  try {
    const res = await frappeGet('ssplbilling.api.outstanding_api.get_party_outstanding', {
      party_type: props.partyType,
      party: props.party,
    })
    localInvoices.value = res.invoices || []
    localPayments.value = res.payment_entries || []
    localJournals.value = res.journal_entries || []
  } catch (e) {
    console.error('[OutstandingBillsModal] fetch failed:', e)
  } finally {
    localLoading.value = false
    nextTick(focusFirstAllocate)
  }
}

watch(() => props.modalAmounts, (newVal) => {
  localAmounts.value = { ...newVal }
  if (!lastModifiedKey.value) {
    const keys = Object.keys(localAmounts.value)
    for (let i = keys.length - 1; i >= 0; i--) {
      if (localAmounts.value[keys[i]] > 0) { lastModifiedKey.value = keys[i]; break }
    }
  }
}, { immediate: true, deep: true })

watch(() => props.show, (val) => {
  if (val) {
    if (props.activeTab === 'Receipt') filterDirection.value = 'Dr'
    else if (props.activeTab === 'Payment') filterDirection.value = 'Cr'
    else filterDirection.value = 'All'
    
    if (props.party) fetchData()
  } else {
    lastModifiedKey.value = null
    localInvoices.value = []
    localPayments.value = []
    localJournals.value = []
  }
}, { immediate: true })

const currentInvoices = computed(() => localInvoices.value.length ? localInvoices.value : props.invoices)
const currentPayments = computed(() => localPayments.value.length ? localPayments.value : props.unlinkedPayments)
const currentJournals = computed(() => localJournals.value.length ? localJournals.value : props.unlinkedJournals)

const filteredInvoices = computed(() => {
  if (!showTypeInv.value) return []
  const list = currentInvoices.value || []
  return filterDirection.value === 'All' ? list : list.filter(i => i.direction === filterDirection.value)
})
const filteredPayments = computed(() => {
  if (!showTypePay.value) return []
  const list = currentPayments.value || []
  return filterDirection.value === 'All' ? list : list.filter(p => p.direction === filterDirection.value)
})
const filteredJournals = computed(() => {
  if (!showTypeJrn.value) return []
  const list = currentJournals.value || []
  return filterDirection.value === 'All' ? list : list.filter(j => j.direction === filterDirection.value)
})

const totalAllocated = computed(() =>
  Object.values(localAmounts.value).reduce((s, v) => s + (isNaN(parseFloat(v)) ? 0 : parseFloat(v)), 0)
)
const remainingBalance = computed(() => props.enteredAmount - totalAllocated.value)

const netOutstanding = computed(() => {
  const sign = (dir) => dir === 'Dr' ? 1 : -1
  const invBal = (currentInvoices.value || []).reduce((s, i) => s + sign(i.direction) * Math.abs(i.outstanding_amount), 0)
  const jeBal  = (currentJournals.value || []).reduce((s, j) => s + sign(j.direction) * Math.abs(j.unallocated_amount), 0)
  const peBal  = (currentPayments.value || []).reduce((s, p) => s + sign(p.direction) * Math.abs(p.unallocated_amount), 0)
  return invBal + jeBal + peBal
})

const totalItemCount = computed(() => filteredInvoices.value.length + filteredPayments.value.length + filteredJournals.value.length)
const allocatedCount = computed(() => Object.values(localAmounts.value).filter(v => parseFloat(v) > 0).length)

async function showLinkedDocs(doctype, docname) {
  linkedPopup.value = { show: true, docname, doctype, docs: [], totalAllocated: 0, loading: true }
  try {
    const res = await frappeGet('ssplbilling.api.outstanding_api.get_linked_documents', { doctype, docname })
    linkedPopup.value.docs = res.docs || []
    linkedPopup.value.totalAllocated = res.total_allocated || 0
  } catch (e) {
    console.error('[OutstandingBillsModal] linked docs fetch failed:', e)
  } finally {
    linkedPopup.value.loading = false
  }
}

function balanceFor(key, outstanding) {
  return Math.max(0, Math.abs(outstanding) - (parseFloat(localAmounts.value[key]) || 0))
}

function onAllocationChange(key) {
  lastModifiedKey.value = key
}

function emitAllocations() {
  const allInvoices = currentInvoices.value.map(i => ({
    reference_doctype: i.doctype,
    reference_name: i.name,
    total_amount: i.grand_total,
    outstanding_amount: Math.abs(i.outstanding_amount),
    allocated_amount: parseFloat(localAmounts.value[i.name]) || 0,
  }))
  const allJournals = currentJournals.value.map(j => ({
    reference_doctype: 'Journal Entry',
    reference_name: j.name,
    total_amount: j.total_amount || j.unallocated_amount,
    outstanding_amount: Math.abs(j.unallocated_amount),
    allocated_amount: parseFloat(localAmounts.value[j.reference_row]) || 0,
    _row: j.reference_row,
  }))
  const allPayments = currentPayments.value.map(p => ({
    reference_doctype: 'Payment Entry',
    reference_name: p.name,
    total_amount: p.paid_amount,
    outstanding_amount: Math.abs(p.unallocated_amount),
    allocated_amount: parseFloat(localAmounts.value[p.name]) || 0,
  }))
  emit('update-allocations', [...allInvoices, ...allJournals, ...allPayments].filter(a => a.allocated_amount > 0))
}

function confirmAdjustments() {
  emitAllocations()
  emit('close')
}

function fmt(val) {
  return Math.abs(Number(val || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]}`
}

function dueDays(dateStr) {
  if (!dateStr) return 0
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const d = new Date(dateStr); d.setHours(0, 0, 0, 0)
  return Math.floor((today - d) / 86400000)
}

function focusFirstAllocate() {
  const inputs = document.querySelectorAll('.allocate-input:not(:disabled)')
  if (inputs.length > 0) { inputs[0].focus(); inputs[0].select() }
}

function focusNextAllocate(event) {
  event.preventDefault()
  const inputs = Array.from(document.querySelectorAll('.allocate-input:not(:disabled)'))
  const idx = inputs.indexOf(event.target)
  if (idx >= 0 && idx < inputs.length - 1) {
    inputs[idx + 1].focus()
    inputs[idx + 1].select()
  } else {
    confirmBtn.value?.focus()
  }
}
</script>

<style scoped>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }

.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }
</style>
