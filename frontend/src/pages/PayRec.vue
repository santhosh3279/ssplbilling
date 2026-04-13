<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)]">
    <!-- HEADER -->
    <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 shadow-sm">
      <div class="flex items-center gap-4">
        <button
          @click="$router.push('/')"
          class="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <h1 class="text-lg font-bold tracking-tight text-[var(--color-text)] uppercase">{{ entryTypeLabel }}</h1>
        <div class="h-4 w-px bg-[var(--color-surface-raised)] mx-2"></div>
        
        <!-- Selection Box for All Entry Types -->
        <div class="flex items-center gap-3">
          <div class="flex rounded-lg bg-[var(--color-surface-raised)] p-1">
            <button
              v-for="type in entryTypes"
              :key="type.value"
              @click="entryType = type.value"
              class="rounded-md px-4 py-1.5 text-lg font-bold transition-all flex items-center gap-1.5"
              :class="entryType === type.value ? `bg-[var(--color-surface)] text-${type.color}-400 shadow-sm` : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
            >
              <span>{{ type.label }}</span>
            </button>
          </div>

          <div 
            class="flex items-center gap-2 bg-[var(--color-surface-raised)] p-1 rounded-lg border transition-all"
            :class="journalTypes.includes(entryType) ? 'border-[var(--color-info)] bg-[var(--color-surface)]/50 shadow-sm' : 'border-[var(--color-border)] opacity-60 hover:opacity-100'"
          >
            <span class="text-lg font-bold text-[var(--color-text-muted)] ml-1 tracking-tight">GENERAL</span>
            <select
              v-model="entryType"
              class="rounded-md bg-[var(--color-surface)] border-none px-3 py-1.5 text-lg font-bold text-[var(--color-text)] outline-none focus:ring-1 focus:ring-[var(--color-info)] transition-all cursor-pointer"
            >
              <option v-if="!journalTypes.includes(entryType)" disabled :value="entryType">-- Select --</option>
              <option v-for="type in journalTypes" :key="type" :value="type">
                {{ type }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- Keyboard hints -->
        <div class="flex items-center gap-3 text-[11px] text-[var(--color-text-muted)]">
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">INS</kbd> Add Row</span>
          <span class="text-[var(--color-text-muted)]">|</span>
          <span class="flex items-center gap-1">
            <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">INS</kbd>
            <span class="text-[var(--color-text-muted)]">while picking account →</span>
            <span class="font-bold text-[var(--color-text-muted)]">Show All Accounts</span>
          </span>
          <span class="text-[var(--color-text-muted)]">|</span>
          <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text)]">F9</kbd> Save</span>
        </div>

        <div class="flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-xl border border-[var(--color-border)] shadow-sm">
          <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Posting Date</label>
          <div class="flex items-center gap-1">
            <button
              @click="changeDate(-1)"
              class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <input
              ref="dateInput"
              v-model="displayDate"
              type="text"
              class="bg-transparent text-xl font-black text-[var(--color-text)] outline-none focus:text-[var(--color-info)] w-44 font-mono"
              placeholder="DD/MM/YYYY"
              @focus="e => e.target.select()"
              @input="onDateInput"
            />
            <button
              @click="changeDate(1)"
              class="p-1 hover:bg-[var(--color-surface-raised)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-info)] transition-all"
              tabindex="-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="flex-1 overflow-hidden p-6">
      <div class="h-full flex flex-col bg-[var(--color-surface)] rounded-2xl shadow-sm border border-[var(--color-border)] overflow-hidden">
        
        <!-- HEADER FORM (Only for Receipt/Payment) -->
        <div v-if="entryType === 'Receipt' || entryType === 'Payment'" class="shrink-0 p-6 bg-[var(--color-surface-raised)]/20 border-b border-[var(--color-border)]">
          <div class="grid grid-cols-12 gap-6">
            <!-- Party Column -->
            <div class="col-span-6 space-y-2">
              <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                {{ isReceipt ? 'Paid By (Customer)' : 'Paid To (Supplier)' }}
              </label>
              <div
                @click="openLedgerSearch(0)"
                class="h-16 px-6 rounded-2xl border-2 border-dashed border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between cursor-pointer hover:border-[var(--color-info)] transition-all group"
              >
                <div class="flex flex-col">
                  <span v-if="rows[0]?.account" class="text-2xl font-black text-[var(--color-text)] truncate max-w-[400px]">
                    {{ rows[0].account_name }}
                  </span>
                  <span v-else class="text-xl font-bold text-[var(--color-text-muted)] italic">
                    Select Party...
                  </span>
                  <span v-if="rows[0]?.account" class="text-xs font-bold text-[var(--color-text-muted)] font-mono">
                    Balance: {{ formatBalance(rows[0].current_balance) }}
                  </span>
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)] group-hover:text-[var(--color-info)]"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              </div>
            </div>

            <!-- Amount Column -->
            <div class="col-span-3 space-y-2">
              <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">
                {{ isReceipt ? 'Received Amount' : 'Paid Amount' }}
              </label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-2xl font-black text-[var(--color-text-muted)]">₹</span>
                <input
                  v-if="isReceipt"
                  v-model.number="rows[0].credit"
                  @focus="activeRowIdx = 0"
                  @keydown.enter.prevent="moveNext(0, 'credit')"
                  type="number"
                  class="w-full h-16 pl-10 pr-6 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] text-3xl font-black text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all font-mono"
                  placeholder="0.00"
                />
                <input
                  v-else
                  v-model.number="rows[0].debit"
                  @focus="activeRowIdx = 0"
                  @keydown.enter.prevent="moveNext(0, 'debit')"
                  type="number"
                  class="w-full h-16 pl-10 pr-6 rounded-2xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] text-3xl font-black text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all font-mono"
                  placeholder="0.00"
                />
              </div>
            </div>

            <!-- Allocation Status Column -->
            <div class="col-span-3 space-y-2">
              <label class="text-[11px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Allocation Status</label>
              <div class="h-16 px-6 rounded-2xl bg-[var(--color-bg)]/50 border-2 border-[var(--color-border)] flex items-center justify-between">
                <div class="flex flex-col">
                  <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-tight">Difference</span>
                  <span :class="Math.abs(difference) < 0.01 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'" class="text-xl font-black font-mono">
                    {{ fmt(difference) }}
                  </span>
                </div>
                <div v-if="Math.abs(difference) < 0.01" class="h-8 w-8 rounded-full bg-[var(--color-success)]/20 flex items-center justify-center text-[var(--color-success)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TABLE SECTION -->
        <div class="flex-1 overflow-y-auto custom-scrollbar bg-slate-50/5">
          <div v-if="entryType === 'Receipt' || entryType === 'Payment'" class="p-6 border-b border-[var(--color-border)] bg-[var(--color-bg)]/20">
            <h4 class="text-[11px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-4 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>
              Payment Methods (Bank / Cash)
            </h4>
          </div>

          <table class="w-full border-collapse border border-[var(--color-border)] table-fixed">
            <thead class="sticky top-0 z-10 bg-[var(--color-surface-raised)] border-b-2 border-[var(--color-border)]">
              <tr class="text-[11px] font-black uppercase tracking-wider text-[var(--color-text-muted)] text-left">
                <th class="px-3 py-3 w-14 text-center border-r border-[var(--color-border)]">#</th>
                <th class="px-4 py-3 min-w-[400px] border-r border-[var(--color-border)]">Ledger / Account</th>
                <th v-if="entryType !== 'Receipt' && entryType !== 'Payment'" class="px-4 py-3 w-64 text-right border-r border-[var(--color-border)]">Current Balance</th>
                <th class="px-4 py-3 w-64 text-right border-r border-[var(--color-border)]">Debit (₹)</th>
                <th class="px-4 py-3 w-64 text-right border-r border-[var(--color-border)]">Credit (₹)</th>
                <th v-if="entryType !== 'Receipt' && entryType !== 'Payment'" class="px-4 py-3 w-64 text-right border-r border-[var(--color-border)]">New Balance</th>
                <th class="px-4 py-3 w-14 border-r border-[var(--color-border)]"></th>
              </tr>
            </thead>
            <tbody class="bg-[var(--color-bg)]">
              <tr
                v-for="(row, idx) in ((entryType === 'Receipt' || entryType === 'Payment') ? rows.slice(1) : rows)"
                :key="idx"
                class="group transition-colors border-b border-[var(--color-border)] hover:bg-slate-500/5 even:bg-slate-500/5"
                :class="{ 'bg-[var(--color-info)]/10': activeRowIdx === ((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx) }"
              >
                <td class="px-3 py-0 text-center text-sm font-bold text-[var(--color-text-muted)] border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]/20">
                  {{ (entryType === 'Receipt' || entryType === 'Payment') ? idx + 2 : idx + 1 }}
                </td>
                <td class="p-0 border-r border-[var(--color-border)] relative">
                  <div
                    :ref="el => { if (el) ledgerRefs[(entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx] = el }"
                    @click="openLedgerSearch((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx)"
                    @keydown.enter.prevent.stop="openLedgerSearch((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx)"
                    tabindex="0"
                    class="w-full h-[52px] px-4 flex items-center justify-between cursor-pointer group/input outline-none focus:bg-[var(--color-surface-raised)] focus:ring-inset focus:ring-2 focus:ring-[var(--color-info)] transition-all"
                    :class="row.account ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)] italic'"
                  >
                    <div class="flex items-center gap-2 truncate">
                      <span class="text-xl font-black truncate">{{ row.account_name || 'Select Account...' }}</span>
                    </div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-text-muted)] group-hover/input:text-[var(--color-info)] opacity-0 group-hover/input:opacity-100 transition-opacity"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                  </div>
                </td>
                <td v-if="entryType !== 'Receipt' && entryType !== 'Payment'" class="px-4 py-0 text-right border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]/10">
                  <div v-if="row.account" class="text-xl font-bold text-[var(--color-text-muted)] font-mono whitespace-nowrap">
                    {{ formatBalance(row.current_balance) }}
                  </div>
                </td>
                <td class="p-0 border-r border-[var(--color-border)]">
                  <input
                    :ref="el => { if (el) debitRefs[(entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx] = el }"
                    v-model.number="row.debit"
                    @focus="activeRowIdx = (entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx"
                    @input="row.credit = 0"
                    @keydown.enter.prevent="moveNext((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx, 'debit')"
                    :disabled="isFieldDisabled((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx, 'debit')"
                    type="number"
                    class="w-full h-[52px] bg-transparent px-4 text-right font-mono text-2xl font-black text-[var(--color-text)] outline-none focus:bg-[var(--color-surface-raised)] focus:ring-inset focus:ring-2 focus:ring-[var(--color-info)] transition-all disabled:opacity-10"
                    placeholder="0.00"
                  />
                </td>
                <td class="p-0 border-r border-[var(--color-border)]">
                  <input
                    :ref="el => { if (el) creditRefs[(entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx] = el }"
                    v-model.number="row.credit"
                    @focus="activeRowIdx = (entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx"
                    @input="row.debit = 0"
                    @keydown.enter.prevent="moveNext((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx, 'credit')"
                    :disabled="isFieldDisabled((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx, 'credit')"
                    type="number"
                    class="w-full h-[52px] bg-transparent px-4 text-right font-mono text-2xl font-black text-[var(--color-text)] outline-none focus:bg-[var(--color-surface-raised)] focus:ring-inset focus:ring-2 focus:ring-[var(--color-info)] transition-all disabled:opacity-10"
                    placeholder="0.00"
                  />
                </td>
                <td v-if="entryType !== 'Receipt' && entryType !== 'Payment'" class="px-4 py-0 text-right border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]/10">
                  <div v-if="row.account" class="text-xl font-bold font-mono whitespace-nowrap" :class="getNewBalance(row) !== row.current_balance ? 'text-[var(--color-info)]' : 'text-[var(--color-text-muted)]'">
                    {{ formatBalance(getNewBalance(row)) }}
                  </div>
                </td>
                <td class="px-0 py-0 text-center border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]/5">
                  <button
                    @click="removeRow((entryType === 'Receipt' || entryType === 'Payment') ? idx + 1 : idx)"
                    class="w-full h-full text-[var(--color-text-muted)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 transition-all opacity-0 group-hover:opacity-100 flex items-center justify-center"
                    tabindex="-1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                  </button>
                </td>
              </tr>
              <!-- Empty state message -->
              <tr v-if="rows.length === 0 || (entryType === 'Receipt' || entryType === 'Payment' && rows.length === 1)">
                <td :colspan="(entryType === 'Receipt' || entryType === 'Payment') ? 5 : 7" class="h-32 text-center text-[var(--color-text-muted)] italic text-lg font-bold bg-[var(--color-bg)]/50">
                  {{ (entryType === 'Receipt' || entryType === 'Payment') ? 'No payment methods added. Press INS to add a bank or cash account.' : 'No rows added. Press INS to add a new row.' }}
                </td>
              </tr>
            </tbody>
          </table>

          <div class="p-2">
            <button
              @click="addRow"
              class="flex items-center gap-2 rounded-xl border border-dashed border-[var(--color-border)] px-4 py-2 text-xs font-bold text-[var(--color-text-muted)] hover:border-[var(--color-info)] hover:text-[var(--color-info)] hover:bg-[var(--color-info)]/20 transition-all w-full justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              Add New Row (INS)
            </button>
          </div>
        </div>

        <!-- FOOTER: TOTALS -->
        <div class="shrink-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-6 flex flex-col gap-4">
          <!-- ERROR ALERT -->
          <div v-if="validationError" class="flex items-center gap-2 bg-[var(--color-danger)]/20 text-[var(--color-danger)] px-4 py-2 rounded-lg border border-[var(--color-danger)] text-xs font-bold" :class="errorBlink ? 'animate-blink' : ''">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
            {{ validationError }}
          </div>

          <!-- LINKED REFERENCES TABLE -->
          <div v-if="linkedReferences.length > 0" class="rounded-xl border border-[var(--color-info)]/40 bg-[var(--color-info)]/10 overflow-hidden">
            <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--color-info)]/30 bg-[var(--color-info)]/20">
              <span class="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[var(--color-info)]">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                Linked to {{ linkedReferences.length }} Reference{{ linkedReferences.length !== 1 ? 's' : '' }}
              </span>
              <div class="flex items-center gap-4">
                <span class="text-[10px] font-bold text-[var(--color-text-muted)]">
                  Total Linked: <span class="text-[var(--color-info)] font-black font-mono">₹{{ fmt(totalAllocated) }}</span>
                </span>
                <button
                  @click="linkedReferences = []"
                  class="text-[10px] font-bold text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors uppercase tracking-wider"
                  tabindex="-1"
                >Clear All</button>
              </div>
            </div>
            <table class="w-full border-collapse">
              <thead>
                <tr class="text-[9px] font-black uppercase tracking-widest text-[var(--color-text-muted)] border-b border-[var(--color-info)]/30">
                  <th class="px-4 py-1.5 text-left">Reference</th>
                  <th class="px-4 py-1.5 text-left">Date</th>
                  <th class="px-4 py-1.5 text-right">Invoice Amt</th>
                  <th class="px-4 py-1.5 text-right">Outstanding</th>
                  <th class="px-4 py-1.5 text-right">Allocating</th>
                  <th class="px-4 py-1.5 w-8"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-blue-900/30">
                <tr v-for="(ref, i) in linkedReferences" :key="ref.ref_name" class="hover:bg-[var(--color-info)]/20 transition-colors">
                  <td class="px-4 py-1.5 font-mono text-xs font-bold text-[var(--color-info)]">{{ ref.ref_name }}</td>
                  <td class="px-4 py-1.5 text-xs text-[var(--color-text-muted)] whitespace-nowrap">{{ ref.ref_date }}</td>
                  <td class="px-4 py-1.5 text-right font-mono text-xs text-[var(--color-text-muted)]">₹{{ fmt(ref.grand_total) }}</td>
                  <td class="px-4 py-1.5 text-right font-mono text-xs text-[var(--color-warning)]">₹{{ fmt(ref.outstanding_amount) }}</td>
                  <td class="px-4 py-1.5 text-right font-mono text-xs font-black text-[var(--color-success)]">₹{{ fmt(ref.alloc_amount) }}</td>
                  <td class="px-3 py-1.5 text-center">
                    <button
                      @click="linkedReferences.splice(i, 1)"
                      class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors"
                      tabindex="-1"
                      title="Remove reference"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex items-start justify-between">
            <div class="flex-1 max-w-xl">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1 block">Reference No</label>
                  <input
                    v-model="referenceNo"
                    type="text"
                    class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all shadow-sm"
                    placeholder="Cheque / UTR"
                  />
                </div>
                <div>
                  <label class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1 block">Remarks</label>
                  <input
                    ref="remarksInput"
                    v-model="userRemarks"
                    @keydown.enter.prevent="handleRemarksEnter"
                    class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all shadow-sm"
                    placeholder="Notes..."
                  />
                </div>
              </div>
            </div>
            <div class="flex gap-12 ml-12">
              <div v-if="entryType !== 'Opening Entry'" class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Debit</div>
                <div class="text-2xl font-black text-[var(--color-text)] font-mono">₹ {{ fmt(totalDebit) }}</div>
              </div>
              <div v-if="entryType !== 'Opening Entry'" class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Total Credit</div>
                <div class="text-2xl font-black text-[var(--color-text)] font-mono">₹ {{ fmt(totalCredit) }}</div>
              </div>
              <div class="text-right border-l border-[var(--color-border)] pl-12" :class="{ 'border-none': entryType === 'Opening Entry' }">
                <div v-if="entryType !== 'Opening Entry'">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Difference</div>
                  <div
                    class="text-2xl font-black font-mono"
                    :class="Math.abs(difference) < 0.01 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'"
                  >
                    ₹ {{ fmt(difference) }}
                  </div>
                </div>
                <!-- SAVE BUTTON -->
                <div class="mt-4 flex justify-end">
                  <button
                    ref="saveButton"
                    @click="saveEntry"
                    @keydown.enter="saveEntry"
                    :disabled="isSubmitting || !canSave"
                    class="flex items-center gap-2 rounded-xl bg-[var(--color-info)] px-8 py-3 text-base font-bold text-[var(--color-text-on-highlight)] shadow-lg shadow-blue-900/50 hover:bg-[var(--color-info)] transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    <span v-if="isSubmitting" class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent mr-1"></span>
                    <span>Save Entry</span>
                    <kbd class="ml-2 rounded border border-[var(--color-info)] bg-[var(--color-info)] px-2 py-0.5 font-mono text-xs text-[var(--color-text-on-focus)]">F9</kbd>
                  </button>
                </div>
              </div>
            </div>
          </div>
      </div>
      </div>
    </div>

    <!-- OUTSTANDING INVOICES / RECONCILIATION MODAL -->
    <div v-if="showOutstandingModal" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="confirmOutstanding">
      <div class="w-[860px] max-h-[90vh] flex flex-col overflow-hidden rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
          <div>
            <div class="text-base font-bold text-[var(--color-text)]">Reconciliation Overview</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-0.5">
              {{ rows[0].account_name }}
              <span v-if="outstandingInvoices.length"> &mdash; {{ outstandingInvoices.length }} pending bill{{ outstandingInvoices.length !== 1 ? 's' : '' }}</span>
              <span v-if="unlinkedPayments.length" class="text-[var(--color-info)]"> &middot; {{ unlinkedPayments.length }} unlinked payment{{ unlinkedPayments.length !== 1 ? 's' : '' }}</span>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="text-right">
              <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">New Receipt</div>
              <div class="font-mono text-2xl font-bold text-[var(--color-info)]">₹{{ fmt(isReceipt ? rows[0].credit : rows[0].debit) }}</div>
            </div>
            <div v-if="unlinkedPayments.length" class="text-right border-l border-[var(--color-border)] pl-4">
              <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-info)]">Unlinked Float</div>
              <div class="font-mono text-2xl font-bold text-[var(--color-info)]">₹{{ fmt(unlinkedTotal) }}</div>
            </div>
            <div class="text-right border-l border-[var(--color-border)] pl-4">
              <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Allocating</div>
              <div class="font-mono text-2xl font-bold" :class="outstandingAllocatedTotal > (isReceipt ? rows[0].credit : rows[0].debit) + 0.005 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                ₹{{ fmt(outstandingAllocatedTotal) }}
              </div>
            </div>
            <div v-if="outstandingInvoices.length" class="text-right border-l border-[var(--color-border)] pl-4">
              <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Total Outstanding</div>
              <div class="font-mono text-2xl font-bold text-[var(--color-warning)]">₹{{ fmt(outstandingInvoices.reduce((s, i) => s + i.outstanding_amount, 0)) }}</div>
            </div>
          </div>
        </div>

        <!-- Reconciliation hint when both exist -->
        <div
          v-if="unlinkedPayments.length > 0 && outstandingInvoices.length > 0"
          class="flex items-center gap-2 bg-[var(--color-info)]/20 border-b border-[var(--color-info)]/40 px-6 py-2 text-[11px] font-bold text-[var(--color-info)]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
          This customer has ₹{{ fmt(unlinkedTotal) }} in unlinked payments. Use Cashier Desk to reconcile them against the outstanding bills below.
        </div>

        <!-- Scrollable body -->
        <div class="flex-1 overflow-y-auto">

          <!-- OUTSTANDING BILLS section -->
          <div v-if="outstandingInvoices.length > 0">
            <div class="sticky top-0 z-10 bg-[var(--color-surface)]/90 backdrop-blur-sm px-6 py-2 border-b border-[var(--color-border)]">
              <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-warning)]">Outstanding Bills</span>
            </div>
            <table class="w-full border-collapse">
              <thead class="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                <tr class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-4 py-2 text-left">Invoice</th>
                  <th class="px-4 py-2 text-left">Date</th>
                  <th class="px-4 py-2 text-center">Days</th>
                  <th class="px-4 py-2 text-right">Invoice Amt</th>
                  <th class="px-4 py-2 text-right">Outstanding</th>
                  <th class="px-4 py-2 text-right">Allocate (New Receipt)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800">
                <tr v-for="(inv, i) in outstandingInvoices" :key="inv.name"
                  class="transition-colors" :class="inv._alloc > 0 ? 'bg-[var(--color-info)]/10' : 'hover:bg-[var(--color-surface)]/40'">
                  <td class="px-4 py-2 font-mono text-sm font-bold text-[var(--color-info)]">{{ inv.name }}</td>
                  <td class="px-4 py-2 text-sm text-[var(--color-text-muted)] whitespace-nowrap">{{ inv.posting_date }}</td>
                  <td class="px-4 py-2 text-center">
                    <span class="rounded-full px-2 py-0.5 text-xs font-bold"
                      :class="inv._days > 90 ? 'bg-[var(--color-danger)]/40 text-[var(--color-danger)]' : inv._days > 30 ? 'bg-[var(--color-warning)]/40 text-[var(--color-warning)]' : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'">
                      {{ inv._days }}d
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right font-mono text-sm text-[var(--color-text-muted)]">₹{{ fmt(inv.grand_total) }}</td>
                  <td class="px-4 py-2 text-right font-mono font-bold text-[var(--color-warning)]">₹{{ fmt(inv.outstanding_amount) }}</td>
                  <td class="px-3 py-1.5 text-right">
                    <input
                      v-model.number="inv._alloc"
                      type="number"
                      min="0"
                      :max="inv.outstanding_amount"
                      step="0.01"
                      :ref="el => { if (el) outstandingAllocRefs[i] = el }"
                      @focus="e => e.target.select()"
                      @keydown.enter.prevent="focusNextAllocOrProceed(i)"
                      class="w-32 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-sm font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:bg-[var(--color-surface-raised)]"
                      placeholder="0.00"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- UNLINKED PAYMENTS section -->
          <div v-if="unlinkedPayments.length > 0">
            <div class="sticky top-0 z-10 bg-[var(--color-surface)]/90 backdrop-blur-sm px-6 py-2 border-b border-[var(--color-info)]/30" :class="outstandingInvoices.length ? 'border-t border-[var(--color-border)] mt-2' : ''">
              <span class="text-[10px] font-black uppercase tracking-widest text-[var(--color-info)]">Unlinked Payments (Floating)</span>
            </div>
            <table class="w-full border-collapse">
              <thead class="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                <tr class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th class="px-4 py-2 text-left">Reference</th>
                  <th class="px-4 py-2 text-left">Date</th>
                  <th class="px-4 py-2 text-left">Mode</th>
                  <th class="px-4 py-2 text-right">Unlinked Amount</th>
                  <th class="px-4 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800">
                <tr v-for="pe in unlinkedPayments" :key="pe.name + (pe.reference_row || '')"
                  class="hover:bg-[var(--color-surface)]/40 transition-colors">
                  <td class="px-4 py-2 font-mono text-sm font-bold text-[var(--color-info)]">{{ pe.name }}</td>
                  <td class="px-4 py-2 text-sm text-[var(--color-text-muted)] whitespace-nowrap">{{ pe.posting_date }}</td>
                  <td class="px-4 py-2 text-sm text-[var(--color-text-muted)]">{{ pe.mode_of_payment }}</td>
                  <td class="px-4 py-2 text-right font-mono font-bold text-[var(--color-info)]">₹{{ fmt(pe.unallocated_amount) }}</td>
                  <td class="px-4 py-2">
                    <span class="rounded-full bg-[var(--color-info)]/30 border border-[var(--color-info)]/40 px-2 py-0.5 text-[10px] font-bold text-[var(--color-info)] uppercase tracking-wider">
                      Unreconciled
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Empty state when neither exists (shouldn't normally show but guard) -->
          <div v-if="!outstandingInvoices.length && !unlinkedPayments.length" class="flex flex-col items-center justify-center py-16 text-[var(--color-text-muted)]">
            <div class="text-sm font-bold">No outstanding bills or unlinked payments</div>
          </div>

        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 px-6 py-3">
          <div class="text-xs text-[var(--color-text-muted)]">
            <span v-if="outstandingInvoices.length">Enter amount to allocate per bill · Enter on last row proceeds</span>
            <span v-else class="text-[var(--color-info)]">No outstanding bills. Unlinked payments shown for reference.</span>
          </div>
          <div class="flex items-center gap-3">
            <button
              v-if="outstandingInvoices.length"
              @click="outstandingInvoices.forEach(i => i._alloc = 0)"
              class="rounded-lg border border-[var(--color-border)] px-4 py-1.5 text-xs font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] transition-all"
            >
              Clear
            </button>
            <button
              ref="outstandingProceedBtn"
              @click="confirmOutstanding"
              @keydown.enter.prevent="confirmOutstanding"
              class="rounded-xl bg-[var(--color-info)] px-6 py-2 text-sm font-bold text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] transition-all shadow-lg"
            >
              Proceed &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL -->
    <CustomerSearchModal
      ref="ledgerSearchModal"
      :show="showSearchModal"
      :allowed-types="searchAllowedTypes"
      :initial-type="searchInitialType"
      :skip-date-filter="true"
      @close="showSearchModal = false"
      @select="selectLedger"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappePost, frappeGet } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { useShortcuts, useSubwindowWatcher } from '../services/shortcutManager'
import { payrecShortcuts } from '../shortcuts/payrecShortcuts'
import { getUserRole } from '../composables/usePermission'

const router = useRouter()

// --- STATE ---
const entryTypes = [
  { label: 'Receipt', value: 'Receipt', color: 'blue' },
  { label: 'Payment', value: 'Payment', color: 'emerald' },
]
const entryType = ref('Receipt')
const journalTypes = ref([])

const isReceipt = computed(() => entryType.value === 'Receipt')
const entryTypeLabel = computed(() => {
  const type = entryTypes.find(t => t.value === entryType.value)
  if (type) return `${type.label} Entry`
  return `${entryType.value}`
})

const mopLedgers = ref(null)

watch(entryType, () => {
  rows.value = [
    { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
  ]
  linkedReferences.value = []
  activeRowIdx.value = 0
  nextTick(() => ledgerRefs[0]?.focus())
})

const searchInitialType = computed(() => 'All')

const searchFilterList = computed(() => {
  if ((entryType.value === 'Receipt' || entryType.value === 'Payment') && activeRowIdx.value > 0) {
    return ['wb-cash', 'wb-card', 'wb-upi', 'wb-bank']
      .map(k => localStorage.getItem(k))
      .filter(Boolean)
  }
  return null
})

const searchAllowedTypes = computed(() => {
  // If row 1+ in Receipt/Payment, default to Account but allow all types (Customer, Supplier, Employee, Account)
  if ((entryType.value === 'Receipt' || entryType.value === 'Payment') && activeRowIdx.value > 0) {
    return ['Account', 'Customer', 'Supplier', 'Employee']
  }
  return ['Account', 'Customer', 'Supplier', 'Employee']
})

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) 
  return formatter.format(date)
}

const postingDate = ref(getTodayIST())
const displayDate = ref(formatDateToDisplay(postingDate.value))
const dateInput = ref(null)

function formatDateToDisplay(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function onDateInput(e) {
  let val = e.target.value.replace(/\D/g, '')
  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const year = new Date().getFullYear()
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      postingDate.value = `${year}-${monthStr}-${dayStr}`
      displayDate.value = `${dayStr}/${monthStr}/${year}`
      return
    }
  }
  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '/' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '/' + val.slice(2, 4) + '/' + val.slice(4, 8)
  }
  displayDate.value = val
  if (val.length === 10) {
    const [d, m, y] = val.split('/')
    if (d && m && y && y.length === 4) {
      postingDate.value = `${y}-${m}-${d}`
    }
  }
}

function changeDate(days) {
  const d = new Date(postingDate.value)
  d.setDate(d.getDate() + days)
  postingDate.value = d.toISOString().slice(0, 10)
  displayDate.value = formatDateToDisplay(postingDate.value)
}

const referenceNo = ref('')
const userRemarks = ref('')
const rows = ref([
  { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
])
const activeRowIdx = ref(0)
const isSubmitting = ref(false)
const showSearchModal = ref(false)
const showAllAccounts = ref(false)
const ledgerSearchModal = ref(null)
const remarksInput = ref(null)
const saveButton = ref(null)
const errorBlink = ref(false)
const blinkCell = ref(null)
const showOutstandingModal = ref(false)
const outstandingInvoices = ref([])
const unlinkedPayments = ref([])
const linkedReferences = ref([])   // allocations confirmed from modal → shown as table in footer
const outstandingProceedBtn = ref(null)
const outstandingAllocRefs = []
const outstandingAllocatedTotal = computed(() =>
  outstandingInvoices.value.reduce((s, i) => s + (Number(i._alloc) || 0), 0)
)
const unlinkedTotal = computed(() =>
  unlinkedPayments.value.reduce((s, p) => s + (Number(p.unallocated_amount) || 0), 0)
)
const totalAllocated = computed(() =>
  linkedReferences.value.reduce((s, r) => s + (Number(r.alloc_amount) || 0), 0)
)

// Template Refs
const ledgerRefs = []
const debitRefs = []
const creditRefs = []

// --- COMPUTED ---
const totalDebit = computed(() => rows.value.reduce((s, r) => s + (Number(r.debit) || 0), 0))
const totalCredit = computed(() => rows.value.reduce((s, r) => s + (Number(r.credit) || 0), 0))
const difference = computed(() => totalDebit.value - totalCredit.value)

const validationError = computed(() => {
  if (entryType.value === 'Journal Entry' || entryType.value === 'Opening Entry') return null

  const r1 = rows.value[0]
  if (!r1) return null
  
  if (Number(r1.debit) > 0.005) {
    const sumOtherCredit = rows.value.slice(1).reduce((s, r) => s + (Number(r.credit) || 0), 0)
    if (sumOtherCredit > Number(r1.debit) + 0.005) {
      return `Total Credit (₹${fmt(sumOtherCredit)}) exceeds first row Debit (₹${fmt(r1.debit)})`
    }
  } else if (Number(r1.credit) > 0.005) {
    const sumOtherDebit = rows.value.slice(1).reduce((s, r) => s + (Number(r.debit) || 0), 0)
    if (sumOtherDebit > Number(r1.credit) + 0.005) {
      return `Total Debit (₹${fmt(sumOtherDebit)}) exceeds first row Credit (₹${fmt(r1.credit)})`
    }
  }
  return null
})

const canSave = computed(() => {
  if (entryType.value === 'Opening Entry') {
    return rows.value.some(r => r.account && (Number(r.debit) > 0 || Number(r.credit) > 0))
  }
  return rows.value.filter(r => r.account).length >= 2 && 
         Math.abs(difference.value) < 0.01 && 
         totalDebit.value > 0 &&
         !validationError.value
})

// --- METHODS ---
function fmt(val) {
  return Number(val || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function getResolvedLabel(accountName) {
  if (accountName === localStorage.getItem('wb-cash')) return 'CASH'
  if (accountName === localStorage.getItem('wb-bank')) return 'BANK'
  if (accountName === localStorage.getItem('wb-upi')) return 'UPI'
  if (accountName === localStorage.getItem('wb-card')) return 'CARD'
  return null
}

function addRow() {
  rows.value.push({ account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 })
  activeRowIdx.value = rows.value.length - 1
}

function removeRow(idx) {
  if (rows.value.length <= 1) {
    rows.value[idx] = { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    return
  }
  rows.value.splice(idx, 1)
}

function openLedgerSearch(idx) {
  activeRowIdx.value = idx
  const role = getUserRole()
  showAllAccounts.value = (role === 'admin' || role === 'accounts')
  showSearchModal.value = true
  nextTick(() => ledgerSearchModal.value?.focus())
}

function selectLedger(ledger) {
  const row = rows.value[activeRowIdx.value]
  row.account = ledger.name
  row.account_name = ledger.label
  row.account_type = ledger.type
  row.current_balance = ledger.balance || 0
  showSearchModal.value = false
  
  nextTick(() => {
    let el = null
    if (isFieldDisabled(activeRowIdx.value, 'debit')) {
      el = creditRefs[activeRowIdx.value]
    } else {
      el = debitRefs[activeRowIdx.value]
    }
    if (el) { el.focus(); el.select() }
  })
}

function formatBalance(val) {
  const absVal = Math.abs(val || 0)
  const suffix = val > 0.005 ? ' DR' : (val < -0.005 ? ' CR' : '')
  return absVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + suffix
}

function getNewBalance(row) {
  return (Number(row.current_balance) || 0) + (Number(row.debit) || 0) - (Number(row.credit) || 0)
}

function isFieldDisabled(idx, field) {
  // If General entry (one from journalTypes) or Opening Entry, nothing is disabled by default
  if (journalTypes.value.includes(entryType.value) || entryType.value === 'Opening Entry') return false

  // Row 0: mode-based restriction
  if (idx === 0) {
    if (entryType.value === 'Receipt' && field === 'debit') return true   // Receipt → party is credited
    if (entryType.value === 'Payment' && field === 'credit') return true // Payment → party is debited
  }
  // Other rows: follow what row 0 has entered
  const firstRowDebit = Number(rows.value[0]?.debit) || 0
  const firstRowCredit = Number(rows.value[0]?.credit) || 0
  if (firstRowDebit > 0.005 && idx > 0 && field === 'debit') return true
  if (firstRowCredit > 0.005 && idx > 0 && field === 'credit') return true
  return false
}

function triggerBlink(idx, field) {
  errorBlink.value = true
  blinkCell.value = { idx, field }
  nextTick(() => {
    const el = field === 'debit' ? debitRefs[idx] : creditRefs[idx]
    el?.focus()
    el?.select()
  })
  setTimeout(() => {
    errorBlink.value = false
    blinkCell.value = null
  }, 700)
}

async function fetchAndShowOutstanding() {
  const row0 = rows.value[0]
  if (!row0.account) return false
  const partyType = row0.account_type || (entryType.value === 'Receipt' ? 'Customer' : 'Supplier')
  if (!['Customer', 'Supplier', 'Employee'].includes(partyType)) return false
  try {
    // Fetch outstanding bills and unlinked payments in parallel (unlinked only for Customers)
    const [res, unlinked] = await Promise.all([
      frappeGet('ssplbilling.api.ledgerentry_api.get_outstanding_invoices', {
        party: row0.account,
        party_type: partyType,
      }),
      partyType === 'Customer'
        ? frappeGet('ssplbilling.api.cashier_api.get_customer_unallocated_cash', {
            customer: row0.account,
          })
        : Promise.resolve([])
    ])
    const today = new Date()
    outstandingInvoices.value = (res?.invoices || [])
      .filter(i => i.outstanding_amount > 0)
      .map(i => ({
        ...i,
        _alloc: 0,
        _days: Math.floor((today - new Date(i.posting_date)) / 86400000),
      }))
    unlinkedPayments.value = unlinked || []

    if (outstandingInvoices.value.length > 0 || unlinkedPayments.value.length > 0) {
      showOutstandingModal.value = true
      nextTick(() => {
        if (outstandingAllocRefs[0]) { outstandingAllocRefs[0].focus(); outstandingAllocRefs[0].select() }
        else outstandingProceedBtn.value?.focus()
      })
      return true
    }
  } catch (e) {}
  return false
}

function focusNextAllocOrProceed(i) {
  const inv = outstandingInvoices.value[i]
  const amountEntered = isReceipt.value ? Number(rows.value[0].credit) : Number(rows.value[0].debit)
  const currentlyAllocatedExcludingThis = outstandingInvoices.value.reduce((s, item, idx) => {
    if (idx === i) return s
    return s + (Number(item._alloc) || 0)
  }, 0)

  const remainingToAllocate = amountEntered - currentlyAllocatedExcludingThis

  if (remainingToAllocate > 0) {
    if (remainingToAllocate >= inv.outstanding_amount) {
      // Allocate full amount for this bill
      inv._alloc = inv.outstanding_amount
      const next = outstandingAllocRefs[i + 1]
      if (next) { next.focus(); next.select() }
      else confirmOutstanding()
    } else {
      // Allocate remaining balance to this bill and proceed directly
      inv._alloc = parseFloat(remainingToAllocate.toFixed(2))
      confirmOutstanding()
    }
    return
  }

  const next = outstandingAllocRefs[i + 1]
  if (next) { next.focus(); next.select() }
  else confirmOutstanding()
}

function fillRow1Amount() {
  const row0 = rows.value[0]
  const amount = entryType.value === 'Receipt' ? Number(row0.credit) : Number(row0.debit)
  if (rows.value.length < 2) addRow()
  const row1 = rows.value[1]
  if (entryType.value === 'Receipt') { row1.debit = amount; row1.credit = 0 }
  else { row1.credit = amount; row1.debit = 0 }
}

function confirmOutstanding() {
  showOutstandingModal.value = false

  const row0 = rows.value[0]
  const partyType = row0.account_type || (entryType.value === 'Receipt' ? 'Customer' : 'Supplier')
  const refDocType = partyType === 'Supplier' ? 'Purchase Invoice' : 'Sales Invoice'

  // Collect whichever invoices the user allocated against
  const allocs = outstandingInvoices.value.filter(i => (Number(i._alloc) || 0) > 0.005)
  if (allocs.length > 0) {
    linkedReferences.value = allocs.map(i => ({
      ref_type: refDocType,
      ref_name: i.name,
      ref_date: i.posting_date,
      grand_total: i.grand_total,
      outstanding_amount: i.outstanding_amount,
      alloc_amount: Number(i._alloc),
    }))
  }

  if (outstandingInvoices.value.length > 0 || Number(row0.credit || row0.debit) > 0) {
    fillRow1Amount()
    activeRowIdx.value = 1
    openLedgerSearch(1)
  }
}

async function moveNext(idx, field) {
  if (validationError.value) {
    triggerBlink(idx, field)
    return
  }
  const isBalanced = Math.abs(difference.value) < 0.01
  const hasValue = totalDebit.value > 0
  if (isBalanced && hasValue) {
    nextTick(() => remarksInput.value?.focus())
    return
  }
  if (idx === 0 && (entryType.value === 'Receipt' || entryType.value === 'Payment')) {
    // Try to show outstanding bills; if none, go directly to row 1
    const shown = await fetchAndShowOutstanding()
    if (!shown) {
      fillRow1Amount()
      activeRowIdx.value = 1
      openLedgerSearch(1)
    }
    return
  }
  // Subsequent rows: move to next row ledger
  if (idx === rows.value.length - 1) addRow()
  else activeRowIdx.value = idx + 1
  nextTick(() => ledgerRefs[activeRowIdx.value]?.focus())
}

function handleRemarksEnter() {
  saveButton.value?.focus()
}

onMounted(async () => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  
  // Load GL account ledgers for row 2+
  try {
    mopLedgers.value = await frappeGet('ssplbilling.api.customersearch_api.get_user_mop_ledgers')
  } catch (e) {
    console.warn('Failed to load account ledgers:', e)
  }

  // Fetch Journal Entry Types from backend
  try {
    const res = await frappeGet('ssplbilling.api.journalcontra_api.get_journal_entry_types')
    journalTypes.value = res || []
  } catch (e) {
    console.warn('Failed to fetch journal entry types:', e)
    journalTypes.value = ['Journal Entry', 'Opening Entry', 'Contra Entry']
  }

  // Block page shortcuts while the outstanding modal is open
  useSubwindowWatcher(showOutstandingModal)

  useShortcuts(payrecShortcuts({
    switchToReceipt: () => { entryType.value = 'Receipt' },
    switchToPayment: () => { entryType.value = 'Payment' },
    switchToGeneral: () => { if (journalTypes.value.length) entryType.value = journalTypes.value[0] },
    addRow: () => {
      if (showSearchModal.value) { showAllAccounts.value = true; nextTick(() => ledgerSearchModal.value?.focus()); return }
      addRow()
    },
    saveEntry: saveEntry,
    navigateUp: () => { if (showSearchModal.value) return; if (activeRowIdx.value > 0) activeRowIdx.value-- },
    navigateDown: () => { if (showSearchModal.value) return; if (activeRowIdx.value < rows.value.length - 1) activeRowIdx.value++ },
    focusDate: () => dateInput.value?.focus(),
    focusLastRow: () => {
      activeRowIdx.value = rows.value.length - 1
      nextTick(() => ledgerRefs[activeRowIdx.value]?.focus())
    },
    handleEnter: (e) => {
      if (showSearchModal.value) return
      const active = document.activeElement
      if (active.tagName === 'BUTTON') { active.click(); return }
      const isBalanced = Math.abs(difference.value) < 0.01
      const hasValue = totalDebit.value > 0
      if (isBalanced && hasValue && active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') {
        remarksInput.value?.focus()
        return
      }
      if (active === document.body || !active) { activeRowIdx.value = 0; openLedgerSearch(0); return }
      if (active.tagName !== 'INPUT' && active.tagName !== 'TEXTAREA') openLedgerSearch(activeRowIdx.value)
    },
    goBack: () => {
      if (showOutstandingModal.value) { confirmOutstanding(); return }
      router.push('/')
    }
  }))
  nextTick(() => ledgerRefs[0]?.focus())
})

async function saveEntry() {
  if (!canSave.value || isSubmitting.value) return
  isSubmitting.value = true
  try {
    const isPayRec = entryType.value === 'Receipt' || entryType.value === 'Payment'
    const apiMethod = isPayRec 
      ? 'ssplbilling.api.payrec_api.create_payrec_payment_entry'
      : 'ssplbilling.api.journalcontra_api.create_journal_contra_entry'

    const payload = {
      entry_type: entryType.value,
      voucher_type: entryType.value,
      posting_date: postingDate.value,
      user_remark: userRemarks.value,
      cheque_no: referenceNo.value,
      accounts: rows.value
        .filter(r => r.account)
        .map((r, idx) => {
          const accPayload = {
            account: r.account,
            account_type: r.account_type,
            debit_in_account_currency: r.debit,
            credit_in_account_currency: r.credit,
            cost_center: localStorage.getItem('wb-cost-center') || '',
            user_remark: userRemarks.value,
          }
          return accPayload
        }),
      // Pass references separately for PayRec API
      ...(isPayRec && linkedReferences.value.length > 0
        ? { references: linkedReferences.value.map(ref => ({
              ref_type: ref.ref_type,
              name: ref.ref_name,
              amount: ref.alloc_amount,
            })) }
        : {})
    }

    // For Journal Entry, we still need references attached to the first row in the payload
    if (!isPayRec && linkedReferences.value.length > 0) {
      payload.accounts[0].references = linkedReferences.value.map(ref => ({
        ref_type: ref.ref_type,
        ref_name: ref.ref_name,
        alloc_amount: ref.alloc_amount,
      }))
    }

    await frappePost(apiMethod, { data: payload })
    alert('Entry saved successfully!')
    userRemarks.value = ''
    referenceNo.value = ''
    linkedReferences.value = []
    rows.value = [
      { account: '', account_name: '', account_type: '', current_balance: 0, debit: 0, credit: 0 }
    ]
    activeRowIdx.value = 0
    nextTick(() => ledgerRefs[0]?.focus())
  } catch (e) {
    alert('Failed to save: ' + e.message)
  } finally {
    isSubmitting.value = false
  }
}

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
})
</script>

<style scoped>
@keyframes blink {
  0%, 100% { opacity: 1; }
  25% { opacity: 0.2; }
  50% { opacity: 1; }
  75% { opacity: 0.2; }
}
.animate-blink {
  animation: blink 0.7s ease-in-out;
}
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #64748b; }
input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
