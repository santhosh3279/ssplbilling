<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] text-[var(--color-text)] font-sans">
    
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm z-10">
      <div class="flex items-center gap-4">
        <button
          @click="goBack"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors active:scale-95 border border-[var(--color-border)]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-[var(--color-text)]">LANDED COST VOUCHER</h1>
        <div class="h-4 w-px bg-[var(--color-surface-raised)] mx-2"></div>
        <span class="rounded-full bg-[var(--color-success)]/10 px-3 py-1 text-[12px] font-bold uppercase tracking-wider text-[var(--color-success)] border border-[var(--color-success)]/20">
          {{ isNew ? 'New Entry' : doc.docstatus === 0 ? 'Draft' : doc.docstatus === 1 ? 'Submitted' : 'Cancelled' }}
        </span>
      </div>
      
      <div class="flex items-center gap-3">
        <!-- Action Buttons -->
        <button
          v-if="doc.docstatus === 0"
          @click="handleSave"
          :disabled="isSaving"
          class="rounded-lg bg-[var(--color-highlight)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-highlight)]/80 active:scale-95 disabled:opacity-50"
        >
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
        <button
          v-if="doc.name && doc.docstatus === 0"
          @click="handleSubmit"
          :disabled="isSubmitting"
          class="rounded-lg bg-[var(--color-success)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-success)]/80 active:scale-95 disabled:opacity-50"
        >
          {{ isSubmitting ? 'Submitting...' : 'Submit' }}
        </button>
        <button
          v-if="doc.name && doc.docstatus === 1"
          @click="handleCancel"
          :disabled="isCancelling"
          class="rounded-lg bg-[var(--color-danger)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-danger)]/80 active:scale-95 disabled:opacity-50"
        >
          {{ isCancelling ? 'Cancelling...' : 'Cancel' }}
        </button>
        <button
          v-if="doc.name && doc.docstatus === 0"
          @click="handleDelete"
          :disabled="isDeleting"
          class="rounded-lg bg-[var(--color-danger)]/20 border border-[var(--color-danger)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-danger)] transition-all hover:bg-[var(--color-danger)]/10 active:scale-95 disabled:opacity-50"
        >
          {{ isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
        <button
          @click="initNewDoc"
          class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[var(--color-text)] transition-all hover:bg-[var(--color-surface-raised)]/80 active:scale-95"
        >
          New
        </button>
      </div>
    </header>

    <!-- CONTENT BODY -->
    <div class="flex flex-1 overflow-hidden">

      <!-- LEFT SIDEBAR: LISTING -->
      <aside v-if="!isSubwindow" class="flex w-80 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="p-4">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--color-text-muted)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            </span>
            <input
              v-model="listSearch"
              type="text"
              placeholder="Search Vouchers..."
              class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-2 pl-9 pr-4 text-[14px] text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-all"
            />
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar bg-[var(--color-bg)]/20">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-20 opacity-55">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-highlight)] border-t-transparent mb-2"></div>
            <span class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Loading Vouchers...</span>
          </div>
          <div v-else-if="filteredVouchers.length === 0" class="flex flex-col items-center justify-center py-20 opacity-35 text-center px-4">
            <span class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">No Landed Cost Vouchers</span>
          </div>
          <div v-else class="px-3 pb-4 space-y-2">
            <button
              v-for="item in filteredVouchers"
              :key="item.name"
              @click="loadDoc(item.name)"
              class="flex w-full flex-col gap-1 rounded-xl p-3 text-left transition-all border outline-none shadow-sm"
              :class="doc.name === item.name
                ? 'bg-[var(--color-highlight)]/10 border-[var(--color-highlight)] ring-1 ring-[var(--color-highlight)]'
                : 'bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] border-[var(--color-border)]'"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono text-sm font-bold text-[var(--color-highlight)]">{{ item.name }}</span>
                <span 
                  class="rounded px-2 py-0.5 text-[10px] font-black uppercase tracking-wider border"
                  :class="item.docstatus === 0
                    ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                    : item.docstatus === 1
                    ? 'bg-green-500/10 text-green-500 border-green-500/20'
                    : 'bg-red-500/10 text-red-500 border-red-500/20'"
                >
                  {{ item.docstatus === 0 ? 'Draft' : item.docstatus === 1 ? 'Sub' : 'Can' }}
                </span>
              </div>
              <div class="text-[12px] text-[var(--color-text-muted)] font-medium mt-1">
                <div>Date: <span class="text-[var(--color-text)] font-semibold">{{ formatDate(item.posting_date) }}</span></div>
                <div>Landed Cost: <span class="text-[var(--color-text)] font-semibold font-mono">{{ fmtCurrency(item.total_taxes_and_charges) }}</span></div>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- MAIN AREA -->
      <main class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[var(--color-bg)]">
        
        <!-- STATUS NOTIFICATION / ALERTS -->
        <div v-if="errorMsg" class="rounded-xl bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 p-4 text-sm font-bold text-[var(--color-danger)]">
          {{ errorMsg }}
        </div>
        <div v-if="successMsg" class="rounded-xl bg-[var(--color-success)]/10 border border-[var(--color-success)]/20 p-4 text-sm font-bold text-[var(--color-success)]">
          {{ successMsg }}
        </div>

        <!-- FORM CARD -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-6">
          <div class="grid grid-cols-4 gap-6">
            
            <!-- Company -->
            <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Company</label>
              <select
                v-model="doc.company"
                :disabled="isReadOnly"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-[15px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
              >
                <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
              </select>
            </div>

            <!-- Posting Date -->
            <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</label>
              <div class="flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] overflow-hidden focus-within:border-[var(--color-highlight)]">
                <button
                  type="button"
                  @click="adjustDate(-1)"
                  :disabled="isReadOnly"
                  class="px-3 text-[var(--color-text-muted)] hover:bg-[var(--color-border)]/50 transition-colors disabled:opacity-40"
                >
                  &larr;
                </button>
                <input
                  type="date"
                  v-model="doc.posting_date"
                  :disabled="isReadOnly"
                  class="w-full bg-transparent px-2 py-2 text-center text-[15px] font-bold outline-none disabled:text-[var(--color-text-muted)]"
                />
                <button
                  type="button"
                  @click="adjustDate(1)"
                  :disabled="isReadOnly"
                  class="px-3 text-[var(--color-text-muted)] hover:bg-[var(--color-border)]/50 transition-colors disabled:opacity-40"
                >
                  &rarr;
                </button>
              </div>
            </div>

            <!-- Distribute Charges Based On -->
            <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Distribute Charges Based On</label>
              <select
                v-model="doc.distribute_charges_based_on"
                :disabled="isReadOnly"
                class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2.5 text-[15px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
              >
                <option value="Qty">Qty</option>
                <option value="Amount">Amount</option>
                <option value="Weight">Weight</option>
                <option value="Volume">Volume</option>
              </select>
            </div>

            <!-- Totals Overview -->
            <div class="flex flex-col gap-2 bg-[var(--color-surface-raised)] p-3 rounded-xl border border-[var(--color-border)] justify-center">
              <div class="text-[11px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Total Landed Cost</div>
              <div class="text-2xl font-black font-mono text-[var(--color-highlight)]">{{ fmtCurrency(doc.total_taxes_and_charges) }}</div>
            </div>

          </div>
        </div>

        <!-- VOUCHERS TABLE -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">1. Vouchers (Purchase Receipts / Invoices)</h3>
            <div class="flex gap-2">
              <button
                v-if="!isReadOnly"
                @click="fetchItems"
                :disabled="isFetchingItems || doc.purchase_receipts.length === 0"
                class="rounded-lg bg-[var(--color-highlight)]/10 border border-[var(--color-highlight)] px-3 py-1 text-xs font-bold uppercase text-[var(--color-highlight)] transition-all hover:bg-[var(--color-highlight)]/20 active:scale-95 disabled:opacity-40"
              >
                {{ isFetchingItems ? 'Fetching...' : 'Get Items' }}
              </button>
              <button
                v-if="!isReadOnly"
                @click="addVoucherRow"
                class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1 text-xs font-bold uppercase text-[var(--color-text)] transition-all hover:bg-[var(--color-border)]/20 active:scale-95"
              >
                + Add Row
              </button>
            </div>
          </div>

          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                <th class="py-2.5 px-3 w-12">#</th>
                <th class="py-2.5 px-3 w-48">Document Type</th>
                <th class="py-2.5 px-3">Document Number</th>
                <th class="py-2.5 px-3">Supplier</th>
                <th class="py-2.5 px-3 w-36">Posting Date</th>
                <th class="py-2.5 px-3 w-36 text-right">Grand Total</th>
                <th v-if="!isReadOnly" class="py-2.5 px-3 w-12 text-center"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="doc.purchase_receipts.length === 0">
                <td colspan="7" class="py-8 text-center text-sm font-semibold text-[var(--color-text-muted)] opacity-60">
                  No vouchers linked. Click "+ Add Row" to search and link a Purchase Receipt or Purchase Invoice.
                </td>
              </tr>
              <tr
                v-for="(row, index) in doc.purchase_receipts"
                :key="index"
                class="border-b border-[var(--color-border)] text-[14px]"
              >
                <td class="py-2 px-3 font-mono text-[var(--color-text-muted)]">{{ index + 1 }}</td>
                
                <!-- Type Selection -->
                <td class="py-2 px-3">
                  <select
                    v-model="row.receipt_document_type"
                    :disabled="isReadOnly"
                    @change="clearRowDoc(row)"
                    class="w-full bg-transparent border border-[var(--color-border)]/50 rounded px-2 py-1 outline-none text-[13px] font-bold text-[var(--color-text)] focus:border-[var(--color-highlight)] disabled:border-none disabled:px-0"
                  >
                    <option value="Purchase Receipt">Purchase Receipt</option>
                    <option value="Purchase Invoice">Purchase Invoice</option>
                  </select>
                </td>

                <!-- Document Link Selection with Autocomplete -->
                <td class="py-2 px-3 relative">
                  <div v-if="!isReadOnly" class="relative">
                    <input
                      v-model="row.receipt_document"
                      @focus="focusDocSearch(row)"
                      @blur="blurDocSearch(row)"
                      @input="handleDocSearch(row)"
                      type="text"
                      placeholder="Type to search..."
                      class="w-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] rounded px-3 py-1 text-[13px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
                    />
                    <!-- Suggestions Dropdown -->
                    <div 
                      v-if="row.showSearch && row.suggestions.length"
                      class="absolute left-0 mt-1 z-30 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl max-h-60 overflow-y-auto"
                    >
                      <button
                        v-for="sug in row.suggestions"
                        :key="sug.name"
                        type="button"
                        @mousedown="selectVoucherDoc(row, sug)"
                        class="w-full text-left p-2.5 hover:bg-[var(--color-highlight)]/10 text-xs transition-colors border-b border-[var(--color-border)] last:border-none outline-none"
                      >
                        <div class="font-mono font-bold text-[var(--color-highlight)]">{{ sug.name }}</div>
                        <div class="flex justify-between mt-1 text-[11px] text-[var(--color-text-muted)]">
                          <span>Supplier: {{ sug.supplier }}</span>
                          <span>Total: {{ fmtCurrency(sug.grand_total) }}</span>
                        </div>
                      </button>
                    </div>
                  </div>
                  <span v-else class="font-mono font-bold text-[var(--color-highlight)]">{{ row.receipt_document }}</span>
                </td>

                <!-- Supplier -->
                <td class="py-2 px-3 text-[var(--color-text-muted)] font-medium">{{ row.supplier || '-' }}</td>

                <!-- Posting Date -->
                <td class="py-2 px-3 font-mono text-[var(--color-text-muted)]">{{ row.posting_date ? formatDate(row.posting_date) : '-' }}</td>

                <!-- Grand Total -->
                <td class="py-2 px-3 text-right font-mono text-[var(--color-text)]">{{ row.grand_total ? fmtCurrency(row.grand_total) : '-' }}</td>

                <!-- Delete Action -->
                <td v-if="!isReadOnly" class="py-2 px-3 text-center">
                  <button
                    @click="deleteVoucherRow(index)"
                    class="rounded-lg p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/15 hover:text-[var(--color-danger)] transition-all"
                  >
                    &times;
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- TAXES AND CHARGES -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">2. Landed Cost Taxes & Charges</h3>
            <button
              v-if="!isReadOnly"
              @click="addTaxRow"
              class="rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1 text-xs font-bold uppercase text-[var(--color-text)] transition-all hover:bg-[var(--color-border)]/20 active:scale-95"
            >
              + Add Row
            </button>
          </div>

          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                <th class="py-2.5 px-3 w-12">#</th>
                <th class="py-2.5 px-3 w-72">Expense Account</th>
                <th class="py-2.5 px-3">Description</th>
                <th class="py-2.5 px-3 w-48 text-right">Amount</th>
                <th v-if="!isReadOnly" class="py-2.5 px-3 w-12 text-center"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="doc.taxes.length === 0">
                <td colspan="5" class="py-8 text-center text-sm font-semibold text-[var(--color-text-muted)] opacity-60">
                  No taxes or charges added yet. Click "+ Add Row" to add shipping, custom duty, or loading costs.
                </td>
              </tr>
              <tr
                v-for="(row, index) in doc.taxes"
                :key="index"
                class="border-b border-[var(--color-border)] text-[14px]"
              >
                <td class="py-2 px-3 font-mono text-[var(--color-text-muted)]">{{ index + 1 }}</td>
                
                <!-- Account Autocomplete -->
                <td class="py-2 px-3 relative">
                  <div v-if="!isReadOnly" class="relative">
                    <input
                      v-model="row.expense_account"
                      @focus="focusAccountSearch(row)"
                      @blur="blurAccountSearch(row)"
                      @input="handleAccountSearch(row)"
                      type="text"
                      placeholder="Search account..."
                      class="w-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] rounded px-3 py-1 text-[13px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
                    />
                    <!-- Suggestion Dropdown -->
                    <div 
                      v-if="row.showSearch && row.suggestions.length"
                      class="absolute left-0 mt-1 z-30 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-xl max-h-60 overflow-y-auto"
                    >
                      <button
                        v-for="sug in row.suggestions"
                        :key="sug.name"
                        type="button"
                        @mousedown="selectTaxAccount(row, sug)"
                        class="w-full text-left p-2.5 hover:bg-[var(--color-highlight)]/10 text-xs transition-colors border-b border-[var(--color-border)] last:border-none outline-none font-bold text-[var(--color-text)]"
                      >
                        {{ sug.name }}
                      </button>
                    </div>
                  </div>
                  <span v-else class="font-bold text-[var(--color-text)]">{{ row.expense_account }}</span>
                </td>

                <!-- Description -->
                <td class="py-2 px-3">
                  <input
                    v-if="!isReadOnly"
                    v-model="row.description"
                    type="text"
                    placeholder="e.g. Freight Charges"
                    class="w-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] rounded px-3 py-1 text-[13px] font-medium text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
                  />
                  <span v-else class="text-[var(--color-text)]">{{ row.description || '-' }}</span>
                </td>

                <!-- Amount -->
                <td class="py-2 px-3">
                  <input
                    v-if="!isReadOnly"
                    v-model.number="row.amount"
                    @input="onAmountChanged"
                    type="number"
                    step="0.01"
                    class="w-full bg-[var(--color-surface-raised)] border border-[var(--color-border)] rounded px-3 py-1 text-[13px] font-mono text-right text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)]"
                  />
                  <span v-else class="block text-right font-mono text-[var(--color-text)]">{{ fmtCurrency(row.amount) }}</span>
                </td>

                <!-- Delete -->
                <td v-if="!isReadOnly" class="py-2 px-3 text-center">
                  <button
                    @click="deleteTaxRow(index)"
                    class="rounded-lg p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/15 hover:text-[var(--color-danger)] transition-all"
                  >
                    &times;
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ITEMS LIST -->
        <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-black uppercase tracking-widest text-[var(--color-text)]">3. Receipt Items & Allocated Charges</h3>
            <span class="rounded bg-[var(--color-surface-raised)] border border-[var(--color-border)] px-3 py-1 text-xs font-bold text-[var(--color-text-muted)]">
              {{ doc.items.length }} Items
            </span>
          </div>

          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-[var(--color-border)] text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                <th class="py-2.5 px-3 w-12">#</th>
                <th class="py-2.5 px-3 w-48">Item Code</th>
                <th class="py-2.5 px-3">Description / Name</th>
                <th class="py-2.5 px-3 w-36">Voucher</th>
                <th class="py-2.5 px-3 w-28 text-right">Qty</th>
                <th class="py-2.5 px-3 w-32 text-right">Rate</th>
                <th class="py-2.5 px-3 w-32 text-right">Amount</th>
                <th class="py-2.5 px-3 w-36 text-right text-[var(--color-highlight)]">Applicable Charges</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="doc.items.length === 0">
                <td colspan="8" class="py-8 text-center text-sm font-semibold text-[var(--color-text-muted)] opacity-60">
                  No items loaded. Link vouchers in Section 1 and click "Get Items" to fetch receipt items.
                </td>
              </tr>
              <tr
                v-for="(row, index) in doc.items"
                :key="index"
                class="border-b border-[var(--color-border)] text-[14px] hover:bg-[var(--color-surface-raised)]/20"
              >
                <td class="py-2 px-3 font-mono text-[var(--color-text-muted)]">{{ index + 1 }}</td>
                <td class="py-2 px-3 font-mono text-[var(--color-highlight)] font-semibold">{{ row.item_code }}</td>
                <td class="py-2 px-3 text-[var(--color-text)] font-medium">{{ row.description || row.item_name }}</td>
                <td class="py-2 px-3 font-mono text-xs text-[var(--color-text-muted)]">{{ row.receipt_document }}</td>
                <td class="py-2 px-3 text-right font-mono text-[var(--color-text)]">{{ row.qty }}</td>
                <td class="py-2 px-3 text-right font-mono text-[var(--color-text-muted)]">{{ fmtCurrency(row.rate) }}</td>
                <td class="py-2 px-3 text-right font-mono text-[var(--color-text-muted)]">{{ fmtCurrency(row.amount) }}</td>
                <td class="py-2 px-3 text-right font-mono font-bold text-[var(--color-highlight)]">{{ fmtCurrency(row.applicable_charges) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

      </main>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'

const props = defineProps({
  isSubwindow: Boolean,
  prelinkDocType: { type: String, default: 'Purchase Invoice' },
  prelinkDocName: String,
  prelinkCompany: String,
  prelinkSupplier: String,
  prelinkPostingDate: String,
  prelinkGrandTotal: Number
})

const emit = defineEmits(['close'])
const router = useRouter()

if (props.isSubwindow) {
  useSubwindow()
}

// --- STATE ---
const doc = reactive({
  name: '',
  company: '',
  posting_date: new Date().toISOString().split('T')[0],
  distribute_charges_based_on: 'Qty',
  purchase_receipts: [],
  taxes: [],
  vendor_invoices: [],
  items: [],
  total_vendor_invoices_cost: 0,
  total_taxes_and_charges: 0,
  docstatus: 0
})

const companies = ref([])
const vouchersList = ref([])
const loadingList = ref(false)
const listSearch = ref('')

const isSaving = ref(false)
const isSubmitting = ref(false)
const isCancelling = ref(false)
const isDeleting = ref(false)
const isFetchingItems = ref(false)

const errorMsg = ref('')
const successMsg = ref('')

const isNew = computed(() => !doc.name)
const isReadOnly = computed(() => doc.docstatus !== 0 && doc.name)

// --- SIDEBAR FILTERING ---
const filteredVouchers = computed(() => {
  if (!listSearch.value) return vouchersList.value
  const query = listSearch.value.toLowerCase()
  return vouchersList.value.filter(v => 
    v.name.toLowerCase().includes(query) || 
    (v.company && v.company.toLowerCase().includes(query))
  )
})

// --- DATE ADJUSTMENT ---
function adjustDate(days) {
  if (isReadOnly.value || !doc.posting_date) return
  const d = new Date(doc.posting_date)
  d.setDate(d.getDate() + days)
  doc.posting_date = d.toISOString().split('T')[0]
}

// --- UTILS ---
function fmtCurrency(val) {
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

function goBack() {
  if (props.isSubwindow) {
    emit('close')
  } else {
    router.push('/')
  }
}

// --- INITIALIZATION ---
async function loadCompanies() {
  try {
    const list = await frappeGet('frappe.client.get_list', {
      doctype: 'Company',
      fields: ['name']
    })
    companies.value = list || []
    if (companies.value.length && !doc.company) {
      doc.company = companies.value[0].name
    }
  } catch (err) {
    console.error('Failed to load companies:', err)
  }
}

async function loadVouchersList() {
  loadingList.value = true
  try {
    const list = await frappeGet('frappe.client.get_list', {
      doctype: 'Landed Cost Voucher',
      fields: ['name', 'company', 'posting_date', 'total_taxes_and_charges', 'docstatus'],
      limit_page_length: 50,
      order_by: 'creation desc'
    })
    vouchersList.value = list || []
  } catch (err) {
    errorMsg.value = 'Failed to load Landed Cost Vouchers: ' + err.message
  } finally {
    loadingList.value = false
  }
}

function initNewDoc() {
  doc.name = ''
  doc.posting_date = new Date().toISOString().split('T')[0]
  doc.distribute_charges_based_on = 'Qty'
  doc.purchase_receipts = []
  doc.taxes = []
  doc.vendor_invoices = []
  doc.items = []
  doc.total_vendor_invoices_cost = 0
  doc.total_taxes_and_charges = 0
  doc.docstatus = 0
  
  if (companies.value.length) {
    doc.company = companies.value[0].name
  }
  errorMsg.value = ''
  successMsg.value = ''
}

// --- LOAD A SPECIFIC VOUCHER ---
async function loadDoc(name) {
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await frappeGet('frappe.client.get', {
      doctype: 'Landed Cost Voucher',
      name
    })
    Object.assign(doc, res)
    doc.purchase_receipts = res.purchase_receipts || []
    doc.taxes = res.taxes || []
    doc.items = res.items || []
  } catch (err) {
    errorMsg.value = `Failed to load ${name}: ` + err.message
  }
}

// --- ROW MANAGEMENT (VOUCHERS) ---
function addVoucherRow() {
  doc.purchase_receipts.push({
    receipt_document_type: 'Purchase Receipt',
    receipt_document: '',
    supplier: '',
    posting_date: '',
    grand_total: 0,
    showSearch: false,
    suggestions: []
  })
}

function deleteVoucherRow(index) {
  doc.purchase_receipts.splice(index, 1)
  distributeCharges()
}

function clearRowDoc(row) {
  row.receipt_document = ''
  row.supplier = ''
  row.posting_date = ''
  row.grand_total = 0
}

// --- AUTOCOMPLETE: DOCUMENTS ---
function focusDocSearch(row) {
  row.showSearch = true
  handleDocSearch(row)
}

function blurDocSearch(row) {
  // Use a slight timeout so clicks on suggestions complete first
  setTimeout(() => {
    row.showSearch = false
  }, 250)
}

let docSearchTimeout = null
function handleDocSearch(row) {
  if (docSearchTimeout) clearTimeout(docSearchTimeout)
  docSearchTimeout = setTimeout(async () => {
    if (!row.receipt_document) {
      row.suggestions = []
      return
    }
    try {
      const list = await frappeGet('frappe.client.get_list', {
        doctype: row.receipt_document_type,
        filters: {
          name: ['like', `%${row.receipt_document}%`],
          docstatus: 1, // only submitted documents
          company: doc.company
        },
        fields: ['name', 'supplier', 'posting_date', 'grand_total'],
        limit_page_length: 10
      })
      row.suggestions = list || []
    } catch (err) {
      console.warn('Document search failed:', err)
    }
  }, 300)
}

function selectVoucherDoc(row, sug) {
  row.receipt_document = sug.name
  row.supplier = sug.supplier || ''
  row.posting_date = sug.posting_date || ''
  row.grand_total = sug.grand_total || 0
  row.showSearch = false
  row.suggestions = []
}

// --- ROW MANAGEMENT (TAXES) ---
function addTaxRow() {
  doc.taxes.push({
    expense_account: '',
    description: '',
    amount: 0,
    base_amount: 0,
    showSearch: false,
    suggestions: []
  })
}

function deleteTaxRow(index) {
  doc.taxes.splice(index, 1)
  onAmountChanged()
}

// --- AUTOCOMPLETE: ACCOUNTS ---
function focusAccountSearch(row) {
  row.showSearch = true
  handleAccountSearch(row)
}

function blurAccountSearch(row) {
  setTimeout(() => {
    row.showSearch = false
  }, 250)
}

let accSearchTimeout = null
function handleAccountSearch(row) {
  if (accSearchTimeout) clearTimeout(accSearchTimeout)
  accSearchTimeout = setTimeout(async () => {
    if (!row.expense_account) {
      row.suggestions = []
      return
    }
    try {
      const list = await frappeGet('frappe.client.get_list', {
        doctype: 'Account',
        filters: {
          account_name: ['like', `%${row.expense_account}%`],
          is_group: 0,
          company: doc.company
        },
        fields: ['name', 'account_name'],
        limit_page_length: 10
      })
      row.suggestions = list || []
    } catch (err) {
      console.warn('Account search failed:', err)
    }
  }, 300)
}

function selectTaxAccount(row, sug) {
  row.expense_account = sug.name
  row.showSearch = false
  row.suggestions = []
}

function onAmountChanged() {
  doc.total_taxes_and_charges = doc.taxes.reduce((sum, t) => sum + Number(t.amount || 0), 0)
  distributeCharges()
}

// --- GET ITEMS FROM VOUCHERS (SERVER CALL) ---
async function fetchItems() {
  if (!doc.purchase_receipts.length) return
  isFetchingItems.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const payloadDoc = {
      doctype: 'Landed Cost Voucher',
      company: doc.company,
      distribute_charges_based_on: doc.distribute_charges_based_on,
      posting_date: doc.posting_date,
      purchase_receipts: doc.purchase_receipts.map(r => ({
        receipt_document_type: r.receipt_document_type,
        receipt_document: r.receipt_document,
        supplier: r.supplier,
        posting_date: r.posting_date,
        grand_total: r.grand_total
      })),
      taxes: doc.taxes.map(t => ({
        expense_account: t.expense_account,
        description: t.description,
        amount: t.amount,
        base_amount: t.amount
      })),
      items: []
    }

    const res = await frappePost('run_doc_method', {
      method: 'get_items_from_purchase_receipts',
      docs: JSON.stringify(payloadDoc)
    })

    if (res.docs && res.docs.length > 0) {
      const updated = res.docs[0]
      doc.items = updated.items || []
      distributeCharges()
      successMsg.value = 'Receipt items loaded successfully.'
    } else {
      errorMsg.value = 'Failed to fetch items. Verify the linked vouchers are submitted.'
    }
  } catch (err) {
    errorMsg.value = 'Fetch items failed: ' + err.message
  } finally {
    isFetchingItems.value = false
  }
}

// --- REAL-TIME CHARGES DISTRIBUTION ---
function distributeCharges() {
  const total_taxes = doc.total_taxes_and_charges
  if (doc.items.length === 0 || total_taxes === 0) {
    doc.items.forEach(item => {
      item.applicable_charges = 0
    })
    return
  }

  const based_on = doc.distribute_charges_based_on.toLowerCase()
  const total_item_cost = doc.items.reduce((sum, item) => sum + Number(item[based_on] || 0), 0)
  if (total_item_cost === 0) return

  let total_charges = 0
  doc.items.forEach((item) => {
    let charge = (Number(item[based_on] || 0) * total_taxes) / total_item_cost
    charge = Math.round(charge * 100) / 100
    item.applicable_charges = charge
    total_charges += charge
  })

  // Rounding correction logic
  const diff = total_taxes - total_charges
  if (Math.abs(diff) > 0.001 && doc.items.length > 0) {
    const lastIdx = doc.items.length - 1
    doc.items[lastIdx].applicable_charges = Math.round((doc.items[lastIdx].applicable_charges + diff) * 100) / 100
  }
}

watch(() => doc.distribute_charges_based_on, () => {
  distributeCharges()
})

// --- DOC WORKFLOWS ---
async function handleSave() {
  if (!doc.company) {
    errorMsg.value = 'Company is required.'
    return
  }
  if (!doc.purchase_receipts.length) {
    errorMsg.value = 'Please add at least one Purchase Receipt or Invoice.'
    return
  }

  isSaving.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const payload = {
      doctype: 'Landed Cost Voucher',
      company: doc.company,
      posting_date: doc.posting_date,
      distribute_charges_based_on: doc.distribute_charges_based_on,
      purchase_receipts: doc.purchase_receipts.map(r => ({
        receipt_document_type: r.receipt_document_type,
        receipt_document: r.receipt_document,
        supplier: r.supplier,
        posting_date: r.posting_date,
        grand_total: r.grand_total
      })),
      taxes: doc.taxes.map(t => ({
        expense_account: t.expense_account,
        description: t.description,
        amount: t.amount,
        base_amount: t.amount
      })),
      items: doc.items.map(i => ({
        item_code: i.item_code,
        description: i.description,
        receipt_document_type: i.receipt_document_type,
        receipt_document: i.receipt_document,
        qty: i.qty,
        rate: i.rate,
        amount: i.amount,
        applicable_charges: i.applicable_charges,
        purchase_receipt_item: i.purchase_receipt_item,
        stock_entry_item: i.stock_entry_item,
        cost_center: i.cost_center
      }))
    }

    let res
    if (isNew.value) {
      res = await frappePost('frappe.client.insert', { doc: payload })
      successMsg.value = `${res.name} saved successfully.`
    } else {
      payload.name = doc.name
      res = await frappePost('frappe.client.save', { doc: payload })
      successMsg.value = `${res.name} updated successfully.`
    }

    Object.assign(doc, res)
    await loadVouchersList()
  } catch (err) {
    errorMsg.value = 'Save failed: ' + err.message
  } finally {
    isSaving.value = false
  }
}

async function handleSubmit() {
  if (isNew.value || !doc.name) return
  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await frappePost('frappe.client.submit', { doc: doc })
    successMsg.value = `${res.name} submitted successfully.`
    Object.assign(doc, res)
    await loadVouchersList()
  } catch (err) {
    errorMsg.value = 'Submission failed: ' + err.message
  } finally {
    isSubmitting.value = false
  }
}

async function handleCancel() {
  if (!doc.name) return
  isCancelling.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const res = await frappePost('frappe.client.cancel', {
      doctype: 'Landed Cost Voucher',
      name: doc.name
    })
    successMsg.value = `${doc.name} cancelled successfully.`
    Object.assign(doc, res)
    await loadVouchersList()
  } catch (err) {
    errorMsg.value = 'Cancellation failed: ' + err.message
  } finally {
    isCancelling.value = false
  }
}

async function handleDelete() {
  if (!doc.name) return
  if (!confirm('Are you sure you want to delete this Landed Cost Voucher?')) return
  isDeleting.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    await frappePost('frappe.client.delete', {
      doctype: 'Landed Cost Voucher',
      name: doc.name
    })
    initNewDoc()
    successMsg.value = 'Document deleted successfully.'
    await loadVouchersList()
  } catch (err) {
    errorMsg.value = 'Deletion failed: ' + err.message
  } finally {
    isDeleting.value = false
  }
}

// --- MOUNTED ---
onMounted(async () => {
  await loadCompanies()
  if (props.isSubwindow && props.prelinkDocName) {
    if (props.prelinkCompany) {
      doc.company = props.prelinkCompany
    }
    doc.purchase_receipts = [{
      receipt_document_type: props.prelinkDocType,
      receipt_document: props.prelinkDocName,
      supplier: props.prelinkSupplier || '',
      posting_date: props.prelinkPostingDate || '',
      grand_total: props.prelinkGrandTotal || 0,
      showSearch: false,
      suggestions: []
    }]
    await fetchItems()
  } else {
    await loadVouchersList()
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
  height: 5px;
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
