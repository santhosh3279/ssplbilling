<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] overflow-hidden">
    <header 
      class="grid grid-cols-[360px_1fr_700px] h-14 items-center border-b border-[var(--color-border)] bg-[var(--color-surface)] z-20 shrink-0 overflow-hidden transition-all duration-300"
      :style="postingDate !== getTodayIST() ? {
        '--color-surface': '#dc2626',
        '--color-border': 'rgba(255, 255, 255, 0.2)',
        '--color-text': '#ffffff',
        '--color-text-muted': 'rgba(255, 255, 255, 0.7)',
        '--color-info': '#ffffff',
        '--color-surface-raised': 'rgba(255, 255, 255, 0.15)',
        '--color-highlight': '#ffffff',
        '--color-text-on-highlight': '#dc2626'
      } : {}"
    >
      <!-- Col 1: App Title & Navigation -->
      <div class="flex items-center px-6 gap-4 border-r border-[var(--color-border)] h-full">
        <button @click="$router.push('/')" class="shrink-0 flex items-center gap-1.5 rounded-lg bg-[var(--color-surface-raised)]/50 px-2.5 py-1.5 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-all active:scale-95">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back
        </button>
        <button v-if="canAccessTile('sales')" @click="$router.push('/sales')" class="shrink-0 flex items-center gap-1.5 rounded-lg bg-[var(--color-surface-raised)]/50 px-2.5 py-1.5 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-all active:scale-95">
          <span>🧾</span> Sales Invoice
        </button>
        <div class="flex items-center gap-2 font-bold text-[var(--color-info)] truncate">
          <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)]">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
          </div>
          <span class="text-sm font-black tracking-widest uppercase text-[var(--color-text)] truncate">Cashier Desk</span>
        </div>
      </div>

      <!-- Col 2: Selected Invoice Info (Centered exactly above main section) -->
      <div class="flex items-center justify-between px-6 h-full overflow-hidden">
        <div v-if="selectedInvoice" class="flex-1 flex items-center justify-between gap-4 overflow-hidden animate-fade-in">
          <!-- Left: Bill No & Customer -->
          <div class="flex items-center gap-4 overflow-hidden">
            <h2 class="text-[21.6px] font-medium text-[var(--color-text)] leading-none truncate shrink-0">{{ selectedInvoice.name }}</h2>
            <div v-if="selectedInvoice.docstatus === 1 && (selectedInvoice.outstanding_amount || 0) <= 0.01" class="rounded px-1.5 py-0.5 bg-[var(--color-success)]/30 border border-[var(--color-success)]/30 shrink-0">
              <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-success)]">Paid</span>
            </div>
            <div v-if="selectedInvoice.mop" class="rounded px-1.5 py-0.5 shrink-0 border"
              :class="selectedInvoice.mop === 'Cash' ? 'bg-[var(--color-success)]/20 border-[var(--color-success)]/30 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/20 border-[var(--color-warning)]/30 text-[var(--color-warning)]'">
              <span class="text-[9px] font-black uppercase tracking-widest">{{ selectedInvoice.mop }}</span>
            </div>
            <div class="h-4 w-[1px] bg-[var(--color-border)] shrink-0"></div>
            <span class="text-[17.5px] font-bold uppercase tracking-wider text-[var(--color-info)] truncate">{{ selectedInvoice.customer }}</span>
          </div>
          
          <!-- Right: Date & Print -->
          <div class="flex items-center gap-4 shrink-0">
            <span class="text-[13.75px] font-bold text-[var(--color-text-muted)] whitespace-nowrap">{{ formatDate(selectedInvoice.posting_date) }}<template v-if="formatTime(selectedInvoice.posting_time)"> · {{ formatTime(selectedInvoice.posting_time) }}</template></span>
            <button @click="showModifyModal = true" class="shrink-0 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[12.5px] font-black uppercase tracking-widest text-[var(--color-text)] hover:bg-[var(--color-border)] active:scale-95 transition-all flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>
              Modify
            </button>
            <button @click="showPrintModal = true" class="shrink-0 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-[12.5px] font-black uppercase tracking-widest text-[var(--color-text)] hover:bg-[var(--color-border)] active:scale-95 transition-all flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
              Print
            </button>
          </div>
        </div>
        <div v-else class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] italic opacity-50">
          No Bill Selected
        </div>
      </div>

      <!-- Col 3: User Profiles (Covers both right asides area) -->
      <div class="flex items-center justify-end px-6 border-l border-[var(--color-border)] h-full gap-4 bg-[var(--color-surface)]/50">
        <div class="flex items-center gap-2">
          <div class="text-right hidden xl:block">
            <div class="text-xs font-bold text-[var(--color-text)]">
              {{ session.fullName.value }}
              <span v-if="inheritedUser" class="font-normal text-[var(--color-text-muted)]"> ({{ inheritedUser }})</span>
            </div>
            <div class="truncate text-[10px] text-[var(--color-text-muted)]">{{ session.user.value }}</div>
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-surface-raised)] to-[var(--color-border)] text-xs font-black text-[var(--color-text)] border border-[var(--color-border)]">
            {{ userInitials }}
          </div>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT ASIDE: INVOICE LIST & CONTROLS -->
      <aside class="flex w-[360px] flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] z-10 shrink-0">
        
        <!-- SIDE PANEL CONTROLS -->
        <div class="p-2 border-b border-[var(--color-border)] space-y-2 bg-[var(--color-surface)]/30">
          <!-- Date & Toggle Section -->
          <div class="flex flex-col gap-2">
            <!-- Sidebar Title Section -->
            <div class="flex items-center justify-between bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] p-1 px-3 h-10">
              <div class="flex items-center gap-2">
                <span class="text-sm font-black uppercase tracking-wider text-[var(--color-text)]">
                  Draft Bills
                </span>
                <span class="flex h-5 items-center justify-center rounded-full bg-[var(--color-focus)]/10 px-2 text-[10px] font-black text-[var(--color-info)]">
                  {{ invoices.length }}
                </span>
              </div>
              <button
                @click="loadInvoices"
                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-highlight)]/20 text-[var(--color-info)] border border-[var(--color-focus)]/30 hover:bg-[var(--color-highlight)] hover:text-[var(--color-text-on-highlight)] transition-all active:scale-90"
                title="Sync Bills"
              >
                <svg :class="{'animate-spin': loadingList}" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
              </button>
            </div>

            <!-- Series & Toggle -->
            <div class="flex items-center gap-2">
              <div class="flex-1 relative series-dropdown-container">
                <button 
                  @click="showSeriesDropdown = !showSeriesDropdown"
                  class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-1.5 px-2 text-[11px] font-bold uppercase tracking-wider text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] transition-all text-left flex justify-between items-center h-9"
                >
                  <span class="truncate">{{ sidebarSeries.length === availableSeries.length ? 'All Series' : (sidebarSeries.length > 0 ? sidebarSeries[0] + (sidebarSeries.length > 1 ? '..' : '') : 'None') }}</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" :class="{'rotate-180': showSeriesDropdown}" class="transition-transform"><path d="m6 9 6 6 6-6"/></svg>
                </button>
                
                <!-- Dropdown Menu -->
                <div v-if="showSeriesDropdown" class="absolute top-full left-0 mt-1 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-2xl z-50 py-2 max-h-64 overflow-y-auto custom-scrollbar">
                  <div class="px-3 py-1.5 border-b border-[var(--color-border)] mb-1 flex items-center gap-2 hover:bg-[var(--color-surface-raised)] cursor-pointer select-none" @click="toggleAllSeries">
                    <input 
                      type="checkbox" 
                      :checked="sidebarSeries.length === availableSeries.length" 
                      class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                    />
                    <span class="text-[11px] font-bold uppercase tracking-wider">All Series</span>
                  </div>
                  <div v-for="s in availableSeries" :key="s" class="px-3 py-1.5 flex items-center gap-2 hover:bg-[var(--color-surface-raised)] cursor-pointer select-none" @click="toggleSeries(s)">
                    <input 
                      type="checkbox" 
                      :checked="isSeriesSelected(s)" 
                      class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                    />
                    <span class="text-[11px] font-bold uppercase tracking-wider">{{ s }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Search Bar -->
          <div class="relative group">
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              placeholder="Search bills..."
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-10 pr-3 text-[15px] font-bold text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10 transition-all"
            />
            <svg class="absolute left-3.5 top-2.5 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="loadingList" class="flex flex-col items-center justify-center py-15 gap-4">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-focus)] border-t-transparent"></div>
            <span class="text-[15px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">Loading...</span>
          </div>
          <div v-else-if="invoices.length === 0" class="flex flex-col items-center justify-center py-15 text-center px-8">
            <div class="mb-4 rounded-xl bg-[var(--color-surface)] p-5 text-[var(--color-text-muted)]">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
            </div>
            <div class="text-[17.5px] font-bold text-[var(--color-text-muted)]">No bills found</div>
            <div class="text-[12.5px] text-[var(--color-text-muted)] uppercase tracking-widest mt-1.5">Pending drafts will appear here</div>
          </div>
          <div v-else class="p-2.5 space-y-4">
            <div v-for="bucket in bucketedInvoices" :key="bucket.date" class="space-y-1 select-none">
              <!-- Date Bucket Header -->
              <div class="flex items-center justify-between px-2.5 py-0.5 bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] rounded-lg shadow-sm">
                <span class="text-[16.5px] font-black uppercase tracking-wider">
                  {{ bucket.label }}
                </span>
                <span class="text-[12px] font-black uppercase tracking-widest opacity-90">
                  {{ bucket.invoices.length }} {{ bucket.invoices.length === 1 ? 'bill' : 'bills' }}
                </span>
              </div>
              
              <!-- Invoices List -->
              <div class="space-y-1">
                <button
                  v-for="inv in bucket.invoices"
                  :key="inv.name"
                  :data-inv-name="inv.name"
                  @click="selectInvoice(inv)"
                  class="group flex w-full flex-col rounded-xl p-1 text-left transition-all active:scale-[0.98]"
                  :class="highlightedInvoiceName === inv.name
                    ? 'bg-[var(--color-focus)] text-[var(--color-text-on-focus)] shadow-lg'
                    : 'bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-[var(--color-text-muted)]'"
                >
                  <div class="flex items-center justify-between mb-0.5">
                    <span
                      class="rounded px-2 py-0.5 text-[11.25px] font-black uppercase tracking-wider"
                      :class="highlightedInvoiceName === inv.name
                        ? 'bg-[var(--color-focus)]/50 text-[var(--color-text-on-focus)]'
                        : inv.docstatus === 0 
                          ? 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]' 
                          : (inv.outstanding_amount <= 0.01 ? 'bg-[var(--color-success)]/40 text-[var(--color-success)]' : 'bg-[var(--color-danger)]/40 text-[var(--color-danger)]')"
                    >
                      {{ inv.docstatus === 0 ? 'DRAFT' : (inv.outstanding_amount <= 0.01 ? 'PAID' : 'UNPAID') }}
                    </span>
                    <span v-if="inv.mop"
                      class="rounded px-2 py-0.5 text-[11.25px] font-black uppercase tracking-wider border ml-1"
                      :class="highlightedInvoiceName === inv.name
                        ? 'border-white/30 text-white'
                        : inv.mop === 'Cash' ? 'bg-[var(--color-success)]/10 border-[var(--color-success)]/20 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/10 border-[var(--color-warning)]/20 text-[var(--color-warning)]'"
                    >
                      {{ inv.mop }}
                    </span>
                    <div class="flex items-center gap-3">
                      <span class="text-[11.25px] font-black uppercase tracking-widest opacity-70">{{ inv.items_count || 0 }} items</span>
                      <span v-if="formatTime(inv.posting_time)" class="text-[13px] font-medium" :class="highlightedInvoiceName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
                        {{ formatTime(inv.posting_time) }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between mb-0.5">
                    <div class="text-[17.5px] font-bold leading-tight" :class="highlightedInvoiceName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ inv.name }}</div>
                    <div class="font-mono text-[27px] font-bold shrink-0" :class="highlightedInvoiceName === inv.name ? 'text-[var(--color-text-on-focus)]' : (((inv.rounded_total || inv.grand_total) < 0) ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]')">{{ fmt(inv.rounded_total || inv.grand_total) }}</div>
                  </div>
                  <div class="truncate text-[16.5px] mt-0.5" :class="highlightedInvoiceName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
                    {{ inv.customer }}
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- CENTER: INVOICE PREVIEW -->
      <main class="flex flex-1 flex-col bg-[var(--color-bg)] overflow-hidden relative">
        <div v-if="!selectedInvoice" class="flex flex-1 flex-col items-center justify-center text-[var(--color-text-muted)]">
          <div class="mb-6 h-28 w-28 opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
          </div>
          <div class="text-base font-bold text-[var(--color-text-muted)]">Select a bill to process payment</div>
          <div class="mt-3 flex items-center gap-4 text-xs font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)]">
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)]">↑</kbd>
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)]">↓</kbd>
              Navigate
            </span>
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)]">ENTER</kbd>
              Select
            </span>
          </div>
        </div>

        <template v-else>
          <!-- Items Table -->
          <div class="flex-1 overflow-y-auto custom-scrollbar px-6 py-4">
            <div v-if="loadingPreview" class="flex flex-col items-center justify-center h-64 gap-3">
              <div class="h-7 w-7 animate-spin rounded-full border-2 border-[var(--color-focus)] border-t-transparent"></div>
              <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-[0.2em]">Loading details...</span>
            </div>
            <div v-else class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-[var(--color-surface-raised)]/50 text-[15px] uppercase tracking-widest text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                    <th class="px-3 py-1.5 font-medium">Item Details</th>
                    <th class="px-3 py-1.5 text-right font-medium">Qty</th>
                    <th class="px-3 py-1.5 text-right font-medium">Rate</th>
                    <th class="px-3 py-1.5 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--color-border)]/50">
                  <tr v-for="item in previewItems" :key="item.name" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                    <td class="px-3 py-1.5">
                      <div class="text-[21px] text-[var(--color-text)]">
                        {{ item.item_name }}
                        <!-- Backend is_free_item flag; rate-0 fallback for rows saved before it was stored -->
                        <span
                          v-if="item.is_free_item === 1 || !Number(item.rate)"
                          class="ml-1 rounded bg-[var(--color-success)] px-1.5 text-[20px] font-bold uppercase leading-tight text-[var(--color-text-on-highlight)]"
                        >Free</span>
                      </div>
                    </td>
                    <td class="px-3 py-1.5 text-right font-mono text-[21px] text-[var(--color-text-muted)]">{{ item.qty }} {{ item.uom }}</td>
                    <td class="px-3 py-1.5 text-right font-mono text-[21px] text-[var(--color-text-muted)]">{{ fmt(item.rate) }}</td>
                    <td class="px-3 py-1.5 text-right font-mono text-[21px] text-[var(--color-text)]">{{ fmt(item.qty * item.rate) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Summary Bar -->
          <div class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
            <div class="flex items-end justify-between">
              <div class="flex gap-6">
                <div class="space-y-0.5">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Total Qty</div>
                  <div class="text-xl font-black tracking-tight text-[var(--color-text)]">{{ previewItems.reduce((acc, i) => acc + i.qty, 0) }}</div>
                </div>
                <div class="space-y-0.5">
                  <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Items</div>
                  <div class="text-xl font-black tracking-tight text-[var(--color-text)]">{{ previewItems.length }}</div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <!-- Compact Reconcile Alert -->
                <button v-if="unallocatedPayments.length > 0 && (selectedInvoice.rounded_total || selectedInvoice.grand_total || 0) > 0" 
                  @click="showReconcileModal = true"
                  class="bg-[var(--color-warning)]/10 border border-[var(--color-warning)]/30 rounded-2xl px-10 py-3 flex items-center gap-5 hover:bg-[var(--color-warning)]/20 transition-all group shadow-md min-w-[240px]"
                  title="Unallocated cash available to adjust"
                >
                  <div class="h-10 w-10 rounded-xl bg-[var(--color-warning)]/20 flex items-center justify-center text-[var(--color-warning)] group-hover:scale-110 transition-transform text-2xl font-black">
                    ₹
                  </div>
                  <div class="text-left">
                    <div class="text-[13.5px] font-black uppercase tracking-widest text-[var(--color-warning)] leading-none">Unallocated</div>
                    <div class="text-[21px] font-black text-[var(--color-warning)]/80 font-mono leading-none mt-1.5">₹{{ fmt(unallocatedAmountTotal) }}</div>
                  </div>
                </button>

                <!-- Allocated Advances Table in Bottom Panel -->
                <div v-if="selectedInvoice?.advances?.length > 0" class="flex flex-col mr-2">
                  <div class="rounded-xl border border-[var(--color-info)]/20 bg-[var(--color-info)]/5 overflow-hidden shadow-sm">
                    <table class="min-w-[280px] border-collapse">
                      <tbody class="divide-y divide-[var(--color-info)]/10">
                        <tr v-for="adv in selectedInvoice.advances.slice(0, 3)" :key="adv.reference_name" class="hover:bg-[var(--color-info)]/10 transition-colors">
                          <td class="px-3 py-1 text-[11px] font-black uppercase tracking-wider text-[var(--color-info)] border-r border-[var(--color-info)]/10 bg-[var(--color-info)]/5">
                            <div class="flex items-center gap-2">
                              <div class="h-1 w-1 rounded-full bg-[var(--color-info)]"></div>
                              <span class="truncate max-w-[150px]">{{ adv.reference_name }}</span>
                            </div>
                          </td>
                          <td class="px-3 py-1 text-right font-mono text-[16px] font-black text-[var(--color-text)]">
                            ₹{{ fmt(adv.allocated_amount) }}
                          </td>
                          <td class="px-2 py-1 text-center">
                            <button 
                              @click="removeAdvance(adv)"
                              class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] p-0.5 rounded transition-colors inline-flex items-center align-middle"
                              title="Remove credit note allocation"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- Template-wise Tax Breakdown -->
                <div v-if="taxSummary.length > 0" class="flex flex-col mr-2">
                  <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)]/40 overflow-hidden shadow-sm">
                    <table class="min-w-[300px] border-collapse">
                      <tbody class="divide-y divide-[var(--color-border)]/50">
                        <tr v-for="grp in taxSummary" :key="grp.template" class="hover:bg-[var(--color-surface-raised)]/60 transition-colors">
                          <td class="px-3 py-1 text-[11px] font-black uppercase tracking-wider text-[var(--color-text-muted)] border-r border-[var(--color-border)]/40">
                            {{ taxTemplateLabel(grp.template) }}
                          </td>
                          <td class="px-3 py-1 text-right font-mono text-[13px] text-[var(--color-text-muted)] border-r border-[var(--color-border)]/40" :title="'Taxable value'">
                            {{ fmt(grp.taxable_amount) }}
                          </td>
                          <td class="px-3 py-1 text-right font-mono text-[15px] font-black text-[var(--color-text)]">
                            ₹{{ fmt(grp.tax_amount) }}
                          </td>
                        </tr>
                        <tr class="bg-[var(--color-surface-raised)]/70">
                          <td class="px-3 py-1 text-[11px] font-black uppercase tracking-wider text-[var(--color-text)] border-r border-[var(--color-border)]/40" colspan="2">
                            Total Tax<span v-if="selectedInvoice?.is_inclusive" class="ml-1 normal-case font-bold text-[var(--color-text-muted)]">(incl.)</span>
                          </td>
                          <td class="px-3 py-1 text-right font-mono text-[16px] font-black text-[var(--color-text)]">
                            ₹{{ fmt(totalTax) }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div class="flex items-center gap-4 bg-[var(--color-info)]/10 px-4 py-2 rounded-xl border border-[var(--color-info)]/20 shadow-sm">
                  <div class="text-[15px] font-black uppercase tracking-[0.2em] text-[var(--color-info)]">Grand Total</div>
                  <div class="text-[36px] font-black tracking-tighter text-[var(--color-text)] font-mono">₹{{ fmt(selectedInvoice.rounded_total || selectedInvoice.grand_total) }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </main>

      <!-- RIGHT ASIDE: PAYMENT CONTROLS -->
      <aside class="flex w-[380px] flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)] z-10 shrink-0">
        <div class="p-5 border-b border-[var(--color-border)] bg-[var(--color-surface)]/50">
          <h3 class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-4 flex items-center gap-2">
            <div class="h-1.5 w-1.5 rounded-full bg-[var(--color-highlight)]"></div>
            Payment Settlement
          </h3>

          <div v-if="!selectedInvoice" class="flex flex-col items-center justify-center h-64 text-center">
            <p class="text-xs font-bold text-[var(--color-text-muted)] leading-relaxed px-10">Select a bill from the left to enable payment processing</p>
          </div>

          <template v-else>
            <div class="space-y-3">
              <!-- Allocated Advances -->
              <div v-if="selectedInvoice?.advances?.length > 0" class="space-y-2 mb-2 animate-in fade-in slide-in-from-top-1 duration-300">
                <div class="flex items-center gap-2 px-1 mb-1">
                  <div class="h-1 w-1 rounded-full bg-[var(--color-info)]"></div>
                  <span class="text-[9px] font-black uppercase tracking-widest text-[var(--color-info)]">Allocated Advances</span>
                </div>
                <div v-for="adv in selectedInvoice.advances" :key="adv.reference_name" 
                  class="flex items-center justify-between p-2.5 rounded-xl bg-[var(--color-info)]/10 border border-[var(--color-info)]/20 text-[11px] font-bold uppercase tracking-wider text-[var(--color-info)] group hover:bg-[var(--color-info)]/15 transition-colors shadow-sm">
                  <div class="flex items-center gap-2 flex-1 min-w-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="opacity-70 group-hover:scale-110 transition-transform shrink-0"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                    <span class="truncate max-w-[150px]">{{ adv.reference_name }}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <span class="font-mono text-[13px] font-black">₹{{ fmt(adv.allocated_amount) }}</span>
                    <button 
                      @click="removeAdvance(adv)"
                      class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] p-0.5 rounded transition-colors"
                      title="Remove credit note allocation"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Summary Mini-Card -->
              <div class="relative rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
                <!-- Credit Badge -->
                <div v-if="isCredit" class="absolute -top-2 -right-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-danger)] text-[var(--color-text-on-highlight)] shadow-lg animate-pulse ring-4 ring-[var(--color-bg)]">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                </div>

                <div class="flex justify-between items-start mb-4">
                  <div>
                    <div class="text-[15px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Bill Amount</div>
                    <div class="text-[36px] font-black tracking-tight text-[var(--color-text)] font-mono">
                      ₹{{ fmt(amountToCollect) }}
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-1">Status</div>
                    <span class="inline-flex rounded px-2 py-0.5 text-[10px] font-black uppercase tracking-widest border"
                      :class="isCredit ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)]' : 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)]'">
                      {{ isCredit ? 'Credit' : 'Cash' }}
                    </span>
                  </div>
                </div>

                <div class="space-y-2 border-t border-[var(--color-border)] pt-3">
                  <div class="flex justify-between items-center">
                    <span class="text-[18px] font-bold text-[var(--color-text-muted)]">Paid Amount</span>
                    <span class="font-mono font-bold text-[var(--color-text)] text-[18px]">₹{{ fmt(totalPaid) }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-[18px] font-bold uppercase tracking-widest" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
                      {{ balance <= 0.01 ? 'Change Return' : 'Balance Due' }}
                    </span>
                    <span class="text-[30px] font-black font-mono" :class="balance <= 0.01 ? 'text-[var(--color-danger)]' : 'text-[var(--color-info)]'">
                      ₹{{ fmt(Math.abs(balance)) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Payment Mode Selector Buttons -->
              <div class="flex gap-2">
                <button
                  @click="toggleCredit(false)"
                  :disabled="isSecondaryParty || selectedInvoice?.is_return"
                  class="flex-1 flex items-center justify-center gap-2 rounded-xl py-1.25 text-[17.5px] font-black uppercase tracking-widest transition-all border"
                  :class="[
                    !isCredit ? 'bg-[var(--color-success)]/30 border-[var(--color-success)] text-[var(--color-success)] shadow-lg' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]',
                    (isSecondaryParty || selectedInvoice?.is_return) ? 'opacity-30 cursor-not-allowed' : ''
                  ]"
                  :title="isSecondaryParty ? 'Secondary parties can only process Credit Sales' : (selectedInvoice?.is_return ? 'Sales returns can only be processed as Credit' : '')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
                  Cash Bill
                </button>
                <button
                  @click="toggleCredit(true)"
                  class="flex-1 flex items-center justify-center gap-2 rounded-xl py-1.25 text-[17.5px] font-black uppercase tracking-widest transition-all border"
                  :class="isCredit ? 'bg-[var(--color-danger)]/40 border-[var(--color-danger)] text-[var(--color-danger)] shadow-lg' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  Credit
                </button>
              </div>

              <!-- Posting Date Selector -->
              <div class="flex flex-col gap-1.5 pb-2">
                <label class="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--color-text-muted)] text-center block w-full">Posting Date</label>
                <div 
                  class="flex items-center justify-between gap-1.5 rounded-xl border p-0.5 transition-all duration-300"
                  :class="postingDate !== getTodayIST()
                    ? 'bg-red-600 border-red-700 text-white'
                    : 'bg-[var(--color-bg)] border-[var(--color-border)]'
                  "
                >
                  <button 
                    @click="adjustPostingDate(-1)" 
                    class="rounded-lg p-[3px] transition-colors"
                    :class="postingDate !== getTodayIST()
                      ? 'text-white/70 hover:bg-white/10 hover:text-white'
                      : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]'
                    "
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                  </button>
                  <div class="flex-1 text-center">
                    <input
                      ref="postingDateInput"
                      type="date"
                      v-model="postingDate"
                      class="bg-transparent border-none text-2xl font-black focus:ring-0 p-0 text-center cursor-pointer w-full transition-all duration-300"
                      :class="postingDate !== getTodayIST() ? 'text-white' : 'text-[var(--color-text)]'"
                    />
                  </div>
                  <button 
                    @click="adjustPostingDate(1)" 
                    class="rounded-lg p-[3px] transition-colors"
                    :class="postingDate !== getTodayIST()
                      ? 'text-white/70 hover:bg-white/10 hover:text-white'
                      : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]'
                    "
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                  </button>
                </div>
              </div>

              <!-- Input Grid -->
              <div v-if="!isCredit" class="space-y-2">
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors uppercase">{{ cashLabel }}</div>
                  <input
                    ref="cashInput"
                    type="number"
                    v-model="payments.cash"
                    @focus="$event.target.select()"
                    step="0.01"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-24 pr-6 text-right font-mono text-[24px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20 transition-all"
                  />
                </div>
                <div class="group relative flex items-center">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 flex items-center gap-2 whitespace-nowrap z-10">
                    <span class="text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-success)] transition-colors uppercase">{{ upiLabel }}</span>
                    <button 
                      @click="sendUpiMqtt"
                      type="button"
                      class="px-2 py-1 rounded-lg bg-[var(--color-success)] text-white font-black text-[15px] uppercase tracking-wider hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 active:scale-95 transition-all shadow-sm"
                    >
                      Send QR
                    </button>
                  </div>
                  <input
                    ref="upiInput"
                    type="number"
                    v-model="payments.upi"
                    @focus="$event.target.select()"
                    step="0.01"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-44 pr-6 text-right font-mono text-[24px] font-black text-[var(--color-text)] focus:border-[var(--color-success)] focus:ring-4 focus:ring-[var(--color-success)]/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors uppercase">{{ cardLabel }}</div>
                  <input
                    ref="cardInput"
                    type="number"
                    v-model="payments.card"
                    @focus="$event.target.select()"
                    step="0.01"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-24 pr-6 text-right font-mono text-[24px] font-black text-[var(--color-text)] focus:border-[var(--color-info)] focus:ring-4 focus:ring-[var(--color-info)]/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-danger)] transition-colors uppercase">Credit</div>
                  <input
                    ref="creditInput"
                    type="number"
                    v-model="payments.credit"
                    @focus="$event.target.select()"
                    step="0.01"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-24 pr-6 text-right font-mono text-[24px] font-black text-[var(--color-text)] focus:border-[var(--color-danger)] focus:ring-4 focus:ring-[var(--color-danger)]/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-warning)] transition-colors uppercase">{{ discountLabel }}</div>
                  <input
                    ref="discountInput"
                    type="number"
                    v-model="payments.discount"
                    @focus="$event.target.select()"
                    step="0.01"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-24 pr-6 text-right font-mono text-[24px] font-black text-[var(--color-text)] focus:border-[var(--color-warning)] focus:ring-4 focus:ring-amber-500/20 transition-all"
                  />
                </div>
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-focus)] transition-colors uppercase">Remarks</div>
                  <input
                    ref="remarksInput"
                    type="text"
                    v-model="payments.remarks"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-32 pr-6 text-right font-mono text-[20px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20 transition-all"
                  />
                </div>
              </div>

              <!-- Credit Fields -->
              <div v-else class="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div class="rounded-xl border border-[var(--color-danger)]/60 bg-[var(--color-danger)]/20 p-4">
                  <label class="text-[15px] font-black uppercase tracking-widest text-[var(--color-danger)] block mb-2 ml-1">Promise Date (Due Date)</label>
                  <div class="relative group">
                    <div class="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-danger)] group-focus-within:text-[var(--color-danger)] transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
                    </div>
                    <input
                      ref="dueDateInput"
                      type="text"
                      v-model="dueDate"
                      @input="handleDueDateInput"
                      @keydown.backspace="handleDueDateKeyDown"
                      placeholder="DDMM or DD/MM/YYYY"
                      class="w-full rounded-2xl border border-[var(--color-danger)]/50 bg-[var(--color-bg)] py-5 pl-12 pr-4 text-center font-mono font-black text-[22.5px] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-danger)] focus:ring-8 focus:ring-[var(--color-danger)]/10 transition-all outline-none"
                    />
                  </div>
                  <div class="mt-3 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[var(--color-danger)]/80 bg-[var(--color-danger)]/30 rounded-lg p-2 border border-[var(--color-danger)]/40">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="m5 15 7 7 7-7"/></svg>
                    Credit Ledger Posting Enabled
                  </div>
                </div>
                <!-- Same ref as the cash-mode box: v-if/v-else means only one is ever mounted -->
                <div class="group relative">
                  <div class="absolute left-5 top-1/2 -translate-y-1/2 text-[18px] font-black text-[var(--color-text-muted)] group-focus-within:text-[var(--color-focus)] transition-colors uppercase">Remarks</div>
                  <input
                    ref="remarksInput"
                    type="text"
                    v-model="payments.remarks"
                    @focus="$event.target.select()"
                    class="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] py-3 pl-32 pr-6 text-right font-mono text-[20px] font-black text-[var(--color-text)] focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/20 transition-all"
                  />
                </div>
              </div>

              <!-- Status Messages -->
              <div class="min-h-[20px]">
                <p v-if="errorMsg" class="text-[11px] font-bold text-[var(--color-danger)] flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
                  {{ errorMsg }}
                </p>
                <p v-if="successMsg" class="text-[11px] font-bold text-[var(--color-success)] flex items-center gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  {{ successMsg }}
                </p>
              </div>

              <!-- Action Button -->
              <button
                ref="postButton"
                @click="processPayment"
                :disabled="!canSubmit"
                class="group w-full rounded-xl py-4 font-black uppercase tracking-[0.2em] text-sm transition-all active:scale-95 focus:outline-none disabled:opacity-30 disabled:pointer-events-none"
                :class="isCredit
                  ? 'bg-[var(--color-danger)] border-2 border-[var(--color-danger)] text-[var(--color-text-on-highlight)] hover:brightness-110 active:bg-[var(--color-danger)] shadow-lg shadow-[var(--color-danger)]/40'
                  : 'bg-transparent border-2 border-[var(--color-success)] text-[var(--color-success)] hover:bg-[var(--color-success)]/10 active:bg-[var(--color-success)] active:text-[var(--color-text-on-highlight)] focus:bg-[var(--color-success)] focus:text-[var(--color-text-on-highlight)] shadow-md shadow-[var(--color-success)]/20'"
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
    <div v-if="showCardRefModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[var(--color-bg)]/80 backdrop-blur-sm">
      <div class="w-full max-w-md bg-[var(--color-surface)] rounded-2xl shadow-2xl overflow-hidden border border-[var(--color-border)] animate-in fade-in zoom-in duration-200">
        <div class="p-5 border-b border-[var(--color-border)] flex justify-between items-center">
          <h3 class="text-sm font-bold uppercase tracking-widest text-[var(--color-text)] flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-[var(--color-info)]"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
            Card / {{ cardLabel }} Reference
          </h3>
          <button @click="showCardRefModal = false" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>
        <div class="p-6 space-y-5">
          <div class="rounded-lg bg-[var(--color-info)]/30 border border-[var(--color-info)]/50 p-3">
            <p class="text-[11px] font-bold text-[var(--color-info)] leading-relaxed uppercase tracking-wider">Enter the authorization or reference number for the card payment.</p>
          </div>
          <input
            ref="cardRefInput"
            v-model="cardRefNo"
            @keydown.enter="confirmCardRef"
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] py-4 px-5 font-mono font-black text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-info)] focus:ring-2 focus:ring-[var(--color-info)]/20 transition-all outline-none"
            placeholder="Enter card reference..."
          />
          <div class="flex gap-3">
            <button
              @click="showCardRefModal = false"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] hover:bg-[var(--color-border)] transition-all active:scale-95"
            >Cancel</button>
            <button
              @click="confirmCardRef"
              :disabled="!cardRefNo"
              class="flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] bg-[var(--color-info)] hover:bg-[var(--color-info)] transition-all active:scale-95 disabled:opacity-40 disabled:pointer-events-none"
            >Confirm & Post</button>
          </div>
        </div>
      </div>
    </div>

    <!-- RECONCILIATION MODAL -->
    <Unallocated
      :show="showReconcileModal"
      :invoice="selectedInvoice"
      :unallocated="unallocatedPayments"
      @close="handleReconcileClose"
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

    <!-- CASHIER ENTRY MODAL -->
    <CashierEntry
      v-if="showCashierEntry"
      title="Cashier Opening"
      :date="getTodayIST()"
      @close="showCashierEntry = false"
      @saved="handleCashierEntrySaved"
    />

    <!-- MODIFY BILL SUBWINDOW -->
    <div v-if="showModifyModal" class="fixed inset-0 z-[100] bg-[var(--color-bg)]">
      <SalesInvoice 
        is-subwindow 
        :invoice-name="selectedInvoice?.name" 
        @close="handleModifyClose" 
      />
    </div>

    <!-- SUCCESS SETTLEMENT POPUP (BOTTOM RIGHT) -->
    <transition name="slide-up">
      <div v-if="showSuccessModal" @click="showSuccessModal = false" class="fixed bottom-8 right-8 z-[110] cursor-pointer">
        <div class="flex items-center gap-4 rounded-2xl border border-[var(--color-success)]/30 bg-[var(--color-surface)] p-4 pr-6 shadow-2xl shadow-[var(--color-success)]/20 animate-in slide-in-from-right-4 fade-in duration-300">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-success)]/20 text-[var(--color-success)] border border-[var(--color-success)]/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
          <div class="flex flex-col">
            <h2 class="text-lg font-black text-[var(--color-text)] uppercase tracking-tight leading-none">
              {{ wasMirrored ? 'Bill Settled & Mirrored' : 'Bill Settled' }}
            </h2>
            <p class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mt-1.5 opacity-70">
              {{ processedInvoiceName }}
            </p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { onBillPanelUpdate } from '../composables/useBillPanelSync.js'
import { session } from '../session'
import { fetchDraftInvoices, getInvoiceDetails, submitInvoiceWithPayment, fetchDashboardSettings, frappeGet, frappePost } from '../api.js'
import { useShortcuts, useSubwindowWatcher, isSubwindowActive } from '../services/shortcutManager'
import { cashierpageShortcuts } from '../shortcuts/cashierpageShortcuts'
import { useLedgerCache } from '../services/ledgerCache'
import { getSeriesForDoctype } from '../services/seriesCache.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import Unallocated from '../components/Unallocated.vue'
import CashierEntry from '../components/CashierEntry.vue'
import SalesInvoice from './SalesInvoice.vue'
import BillMirrorCreator from '../components/BillMirrorCreator.vue'
import Warning from '../components/Warning.vue'
import { canAccessTile } from '../composables/usePermission'

import { formatDMY } from '../utils/date'
import { serverToday } from '../services/serverTime'
/**
 * HELPER: getTodayIST
 * Defined early to ensure it's available for ref initialization.
 */
function getTodayIST() {
  return serverToday()
}

const inheritedUser = computed(() => {
  const inherited = localStorage.getItem('wb-inherited-user')
  return inherited && inherited !== session.user.value ? inherited : null
})

// ==================== STATE (REFS) ====================
// Define all refs first to avoid ReferenceErrors in functions or watchers
const filterDate = ref(getTodayIST())
const postingDate = ref(getTodayIST())
const searchQuery = ref('')
const sidebarSeries = ref([])
const showSeriesDropdown = ref(false)
const availableSeries = ref([])

// Toggle individual series
function toggleSeries(series) {
  const idx = sidebarSeries.value.indexOf(series)
  if (idx > -1) {
    sidebarSeries.value.splice(idx, 1)
  } else {
    sidebarSeries.value.push(series)
  }
  loadInvoices()
}

function isSeriesSelected(series) {
  return sidebarSeries.value.includes(series)
}

function toggleAllSeries() {
  if (sidebarSeries.value.length === availableSeries.value.length) {
    sidebarSeries.value = []
  } else {
    sidebarSeries.value = [...availableSeries.value]
  }
  loadInvoices()
}

const showCardRefModal = ref(false)
const showPrintModal = ref(false)
const showModifyModal = ref(false)
const showReconcileModal = ref(false)
const showSuccessModal = ref(false)
const showBillMirrorCreator = ref(false)
const showGstWarning = ref(false)
const cardRefNo = ref('')
const processedInvoiceName = ref('')
const showCashierEntry = ref(false)
const wasMirrored = ref(false)

// Block page shortcuts while any inline subwindow is open
useSubwindowWatcher(showCardRefModal)
useSubwindowWatcher(showPrintModal)
useSubwindowWatcher(showModifyModal)
useSubwindowWatcher(showReconcileModal)
useSubwindowWatcher(showCashierEntry)
useSubwindowWatcher(showBillMirrorCreator)
useSubwindowWatcher(showGstWarning)

const invoices = ref([])
const selectedInvoice = ref(null)
const highlightedInvoiceName = ref('')
const previewItems = ref([])
const unallocatedPayments = ref([])
const allocatedAdvances = ref([])
const unallocatedAmountTotal = ref(0)
const postButton = ref(null)

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
  credit: 0,
  discount: 0,
  remarks: ''
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
const creditInput = ref(null)
const discountInput = ref(null)
const remarksInput = ref(null)
const dueDateInput = ref(null)
const cardRefInput = ref(null)
const postingDateInput = ref(null)

// ==================== COMPUTED ====================
const { partyLinks } = useLedgerCache()

const bucketedInvoices = computed(() => {
  const groups = {}
  
  for (const inv of invoices.value) {
    const d = inv.posting_date || 'Unknown Date'
    if (!groups[d]) {
      groups[d] = []
    }
    groups[d].push(inv)
  }

  const today = getTodayIST()
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayStr = yesterday.toISOString().slice(0, 10)

  return Object.keys(groups)
    .sort((a, b) => b.localeCompare(a))
    .map(dateKey => {
      let label = ''
      if (dateKey === today) {
        label = 'Today'
      } else if (dateKey === yesterdayStr) {
        label = 'Yesterday'
      } else if (dateKey === 'Unknown Date') {
        label = 'Unknown Date'
      } else {
        label = formatDate(dateKey)
      }
      return {
        date: dateKey,
        label,
        invoices: groups[dateKey]
      }
    })
})

const isSecondaryParty = computed(() => {
  if (!selectedInvoice.value?.customer) return false
  const link = partyLinks.value[selectedInvoice.value.customer]
  return link?.is_secondary || false
})

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
const discountLabel = computed(() => {
  const acc = seriesAccounts.value.discount || localStorage.getItem('wb-discount-account') || ''
  return acc ? acc.split(' - ')[0].trim() : 'Disc'
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

const balance = computed(() => {
  const diff = amountToCollect.value - totalPaid.value
  return parseFloat(diff.toFixed(2))
})

const changeAmount = computed(() => {
  const actualMoney = (Number(payments.value.cash) || 0) +
                      (Number(payments.value.upi) || 0) +
                      (Number(payments.value.card) || 0)
  const netToPay = amountToCollect.value - (Number(payments.value.discount) || 0) - (Number(payments.value.credit) || 0)
  const change = actualMoney - netToPay
  return change > 0.005 ? parseFloat(change.toFixed(2)) : 0
})

const canSubmit = computed(() => {
  if (!selectedInvoice.value || isSubmitting.value) return false
  if (selectedInvoice.value.docstatus === 1 && (selectedInvoice.value.outstanding_amount || 0) <= 0.01) return false
  if (selectedInvoice.value.is_return && !isCredit.value) return false
  if (isCredit.value) return true
  // Force cashier to account for the full bill (using Cash/UPI/Card/Disc OR the Credit box)
  return balance.value <= 0.01
})

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

const previewSubtotal = computed(() => {
  return previewItems.value.reduce((acc, item) => acc + (item.qty * item.rate), 0)
})

const hasPaymentValues = computed(() =>
  (Number(payments.value.cash)     || 0) > 0 ||
  (Number(payments.value.credit)   || 0) > 0 ||
  (Number(payments.value.discount) || 0) > 0 ||
  (Number(payments.value.upi)      || 0) > 0 ||
  (Number(payments.value.card)     || 0) > 0
)

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
    showCashierEntry.value = false
    return
  }

  try {
    const hasOpening = await frappeGet('ssplbilling.api.cahierlog_api.check_cashier_opening', {
      date: today,
      user: session.user.value
    })
    const boxCash = Number(localStorage.getItem('wb-opening-box-cash') || 0)
    
    if (!hasOpening || !boxCash) {
      showCashierEntry.value = true
    } else {
      showCashierEntry.value = false
    }
  } catch (e) {
    console.error('[CashierDesk] Opening check failed:', e)
  }
}

function handleCashierEntrySaved(data) {
  if (data && data.total !== undefined) {
    localStorage.setItem('wb-opening-box-cash', String(data.total))
  }
  showCashierEntry.value = false
  loadInvoices()
}

async function loadInvoices() {
  loadingList.value = true
  try {
    const res = await fetchDraftInvoices(searchQuery.value, 500, '', sidebarSeries.value.join(','))
    res.sort((a, b) => {
      const dateA = a.posting_date || ''
      const dateB = b.posting_date || ''
      if (dateA !== dateB) {
        return dateB.localeCompare(dateA)
      }
      return b.name.localeCompare(a.name)
    })
    invoices.value = res
    // Keep the current highlight when it survived the refresh; otherwise fall back
    // to the top of the list (or clear it when nothing is left).
    const stillListed = highlightedInvoiceName.value
      && invoices.value.some(i => i.name === highlightedInvoiceName.value)
    if (!stillListed) {
      highlightedInvoiceName.value = invoices.value.length > 0 ? invoices.value[0].name : ''
    }
  } catch (e) {
    errorMsg.value = "Failed to load invoices: " + e.message
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
            .filter(s => 
              allowedPrefixes.some(prefix => s && s.startsWith(prefix))
            )
        }
      } catch (e) {
        console.warn('[CashierDesk] Local series parsing failed:', e)
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
      loadInvoices()
    }
  } catch (e) {
    console.warn('[CashierDesk] Could not fetch series list:', e)
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
  return formatDMY(dateStr, '')
}

// "14:23:45.123456" → "2:23 PM"
function formatTime(timeStr) {
  if (!timeStr) return ''
  const [h, m] = String(timeStr).split(':')
  const hh = parseInt(h, 10)
  if (isNaN(hh) || m == null) return ''
  const ampm = hh >= 12 ? 'PM' : 'AM'
  return `${hh % 12 || 12}:${m} ${ampm}`
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
  highlightedInvoiceName.value = inv.name
  if (selectedInvoice.value?.name === inv.name) return
  
  loadingPreview.value = true
  selectedInvoice.value = inv
  previewItems.value = []
  unallocatedPayments.value = []
  errorMsg.value = ''
  successMsg.value = ''
  isCredit.value = false
  cardRefNo.value = ''
  
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: '' }
  
  try {
    const details = await getInvoiceDetails(inv.name)
    selectedInvoice.value = details
    previewItems.value = details.items || []
    // Carry the entry-time remark in: submit writes the box back to custom_remarks,
    // so starting blank would silently wipe whatever Sales Entry saved
    payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: details.custom_remarks || '' }
    await loadSeriesSettings(details.naming_series)

    // Check for Unallocated Cash
    const unallocated = await frappeGet('ssplbilling.api.cashier_api.get_customer_unallocated_cash', {
      customer: details.customer,
      invoice_name: details.name,
      company: localStorage.getItem('wb-company') || undefined
    })
    
    let remaining = details.outstanding_amount || details.rounded_total || details.grand_total
    const filteredUnallocated = (unallocated || []).filter(pe => pe.mode_of_payment === 'Credit Note')
    unallocatedPayments.value = filteredUnallocated.map(pe => {
      const alloc = Math.min(Number(pe.unallocated_amount), remaining)
      remaining -= alloc
      return { ...pe, amount_to_allocate: parseFloat(alloc.toFixed(2)) }
    })
    
    unallocatedAmountTotal.value = filteredUnallocated.reduce((acc, p) => acc + Number(p.unallocated_amount || 0), 0)

    if (details.is_return) {
      toggleCredit(true)
    } else if (isSecondaryParty.value) {
      toggleCredit(true)
    } else if (details.mop) {
      toggleCredit(details.mop === 'Credit')
    }
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
    const targetUser = localStorage.getItem('wb-inherited-user') || null
    const lsCash = localStorage.getItem('wb-cash')
    const lsUpi  = localStorage.getItem('wb-upi')
    const lsCard = localStorage.getItem('wb-card')
    const settings = await fetchDashboardSettings(targetUser)
    // Server resolves discount_account against wb-company; never hardcode a
    // company-tagged account here or discounts post to the wrong company's GL.
    const discountAccount = settings.discount_account || ''

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
  const targetVal = (val !== undefined && typeof val === 'boolean') ? val : !isCredit.value
  
  if (!targetVal && isSecondaryParty.value) {
    errorMsg.value = "Secondary parties can only process Credit Sales."
    return
  }

  if (!targetVal && selectedInvoice.value?.is_return) {
    errorMsg.value = "Sales returns can only be processed as Credit."
    return
  }

  isCredit.value = targetVal
  // Amounts are mode-specific and get cleared; the remark is not, so it survives the flip
  const keptRemarks = payments.value.remarks || ''
  payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: keptRemarks }
  if (isCredit.value) {
    nextTick(() => dueDateInput.value?.focus())
  } else {
    nextTick(() => cashInput.value?.focus())
  }
}

async function sendUpiMqtt() {
  errorMsg.value = ''
  successMsg.value = ''
  
  const upiVal = Number(payments.value.upi) || 0
  if (upiVal <= 0) {
    errorMsg.value = 'Please enter a UPI amount greater than 0.'
    return
  }

  try {
    // 1. Fetch MQTT Settings
    const settings = await frappeGet('frappe.client.get', {
      doctype: 'MQTT Settings',
      name: 'MQTT Settings'
    })
    
    if (!settings || !settings.topics || !settings.topics.length) {
      errorMsg.value = 'MQTT Settings or Topics child table is empty.'
      return
    }

    // 2. Find row with upi_account matching the selected UPI account
    const activeUpiAccount = seriesAccounts.value.upi || localStorage.getItem('wb-upi') || 'UPI'
    const row = settings.topics.find(r => r.upi_account === activeUpiAccount)
    if (!row) {
      errorMsg.value = `No MQTT configuration found for UPI account "${activeUpiAccount}".`
      return
    }

    if (!row.topic || !row.vpa) {
      errorMsg.value = `Topic or VPA is missing in the MQTT Settings for "${activeUpiAccount}".`
      return
    }

    // 3. Format the amount to 2 decimal places
    const formattedAmount = upiVal.toFixed(2)

    // 4. Replace "amount" (literal) with the formatted amount in the vpa string
    const formattedMessage = row.vpa.replace(/amount/g, formattedAmount)

    // 5. Call backend to publish the message
    const res = await frappePost('ssplbilling.api.mqtt_api.publish_mqtt_message', {
      topic: row.topic,
      message: formattedMessage
    })

    if (res && res.status === 'success') {
      successMsg.value = 'MQTT Payment Request sent successfully!'
      setTimeout(() => successMsg.value = '', 4000)
    } else {
      errorMsg.value = 'Failed to publish MQTT payment request.'
    }
  } catch (e) {
    console.error('[CashierDesk] Send MQTT error:', e)
    errorMsg.value = e.message || 'Failed to send MQTT payment request.'
  }
}

async function processPayment() {
  if (!canSubmit.value) return

  isSubmitting.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    if (postingDate.value === getTodayIST()) {
      try {
        const hasOpening = await frappeGet('ssplbilling.api.cahierlog_api.check_cashier_opening', {
          date: getTodayIST(),
          user: session.user.value
        })
        if (!hasOpening) {
          showCashierEntry.value = true
          isSubmitting.value = false
          return
        }
      } catch (e) { console.error(e) }
    }

    if (Number(payments.value.card) > 0.01 && !cardRefNo.value) {
      showCardRefModal.value = true
      nextTick(() => cardRefInput.value?.focus())
      isSubmitting.value = false
      return
    }

    if (!isCredit.value && selectedInvoice.value?.is_return) {
      errorMsg.value = "Sales returns can only be processed as Credit."
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
    if (finalDueDate < today) {
      finalDueDate = today
    }

    const payload = {
      invoice_name: selectedInvoice.value.name,
      cash_amount: cash,
      upi_amount: upi,
      card_amount: card,
      discount_amount: disc,
      credit_amount: credit,
      is_credit: isCredit.value,
      due_date: finalDueDate,
      posting_date: postingDate.value,
      card_ref_no: cardRefNo.value,
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

    wasMirrored.value = false
    const res = await submitInvoiceWithPayment(payload)
    wasMirrored.value = res?.mirrored || false
    
    processedInvoiceName.value = invoiceName
    showSuccessModal.value = true
    
    const nameToRemove = invoiceName
    const removedIdx = invoices.value.findIndex(i => i.name === nameToRemove)
    
    // Clear state immediately for next transaction
    invoices.value = invoices.value.filter(i => i.name !== nameToRemove)
    selectedInvoice.value = null
    // Stay where the settled bill was: the row that slid into its slot, or the new
    // last row when the bottom bill was the one settled.
    if (invoices.value.length > 0) {
      const nextIdx = Math.min(Math.max(removedIdx, 0), invoices.value.length - 1)
      highlightedInvoiceName.value = invoices.value[nextIdx].name
    } else {
      highlightedInvoiceName.value = ''
    }
    previewItems.value = []
    unallocatedPayments.value = []
    postingDate.value = getTodayIST()
    errorMsg.value = ''
    successMsg.value = ''
    
    // Auto-hide success modal after 1.5 seconds
    setTimeout(() => {
      showSuccessModal.value = false
    }, 1500)

    const hasAlternativeCompany = !!localStorage.getItem('ae-alternative_company')
    if (wasUpi && wasExempted && hasAlternativeCompany) {
      nextTick(() => {
        showGstWarning.value = true
      })
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

async function handleModifyClose() {
  showModifyModal.value = false
  if (selectedInvoice.value) {
    const currentName = selectedInvoice.value.name
    // Re-fetch the entire list to ensure grand total and other metadata are fresh
    await loadInvoices()
    // Re-select to refresh preview items and payment amounts
    const inv = invoices.value.find(i => i.name === currentName)
    if (inv) {
      // Small delay to ensure template re-renders and refs are ready
      selectedInvoice.value = null
      await nextTick()
      await selectInvoice(inv)
    }
  }
}

function handleReconcileClose() {
  showReconcileModal.value = false
  nextTick(() => {
    cashInput.value?.focus()
    cashInput.value?.select()
  })
}

function handleAllocationSuccess(res) {
  if (res.outstanding !== undefined) selectedInvoice.value.outstanding_amount = res.outstanding
  if (res.posting_date) selectedInvoice.value.posting_date = res.posting_date
  if (res.due_date) selectedInvoice.value.due_date = res.due_date
  
  // Only update advances if they are provided in the response
  if (res.advances) {
    selectedInvoice.value.advances = res.advances
  }

  // Update sidebar list if needed
  const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
  if (idx !== -1 && res.posting_date) {
    invoices.value[idx].posting_date = res.posting_date
  }

  unallocatedPayments.value = []
  showReconcileModal.value = false

  const remaining = parseFloat((res.outstanding || 0).toFixed(2))
  if (remaining <= 0.01) {
    // Advances fully cover the invoice — just submit
    payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: '' }
    successMsg.value = "Advances cover full amount. Click Post Settlement to finalise."
    nextTick(() => postButton.value?.focus())
  } else {
    // Keep first entry box as zero instead of the balance amount
    payments.value = { cash: 0, upi: 0, card: 0, discount: 0, credit: 0, remarks: '' }
    successMsg.value = `₹${fmt(remaining)} remaining after advance allocation.`
    nextTick(() => { cashInput.value?.focus(); cashInput.value?.select() })
  }
  setTimeout(() => successMsg.value = '', 4000)
}

async function removeAdvance(adv) {
  if (!selectedInvoice.value) return
  
  // Filter out this advance from the current advances list
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
      // Update local advances and outstanding amounts using the response
      if (res.outstanding !== undefined) selectedInvoice.value.outstanding_amount = res.outstanding
      if (res.advances) selectedInvoice.value.advances = res.advances

      // Update sidebar list outstanding amount
      const idx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
      if (idx !== -1) {
        invoices.value[idx].outstanding_amount = res.outstanding
      }

      // Also reload unallocated cash list to make this credit note available again in the modal
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
    errorMsg.value = "Failed to remove advance: " + (e.message || e)
  } finally {
    isSubmitting.value = false
  }
}
// Shortcut Handlers
function navigateBills(dir) {
  if (!invoices.value.length) return
  
  let currentIdx = -1
  if (highlightedInvoiceName.value) {
    currentIdx = invoices.value.findIndex(i => i.name === highlightedInvoiceName.value)
  } else if (selectedInvoice.value) {
    currentIdx = invoices.value.findIndex(i => i.name === selectedInvoice.value.name)
  }

  const nextIdx = currentIdx + dir
  if (nextIdx >= 0 && nextIdx < invoices.value.length) {
    highlightedInvoiceName.value = invoices.value[nextIdx].name
    nextTick(() => {
      const el = document.querySelector(`[data-inv-name="${invoices.value[nextIdx].name}"]`)
      el?.scrollIntoView({ block: 'nearest' })
    })
  }
}

function handleArrowUp() {
  const active = document.activeElement
  if (active.tagName === 'INPUT') {
    // Credit mode only mounts Due Date + Remarks, so it walks its own two-step chain
    if (isCredit.value) {
      if (active === remarksInput.value) dueDateInput.value?.focus()
      return
    }
    if (active === upiInput.value) { cashInput.value?.focus(); cashInput.value?.select() }
    else if (active === cardInput.value) { upiInput.value?.focus(); upiInput.value?.select() }
    else if (active === creditInput.value) { cardInput.value?.focus(); cardInput.value?.select() }
    else if (active === discountInput.value) { creditInput.value?.focus(); creditInput.value?.select() }
    else if (active === remarksInput.value) { discountInput.value?.focus(); discountInput.value?.select() }
  } else {
    navigateBills(-1)
  }
}

function handleArrowDown() {
  const active = document.activeElement
  if (active.tagName === 'INPUT') {
    if (isCredit.value) {
      if (active === dueDateInput.value) { remarksInput.value?.focus(); remarksInput.value?.select() }
      return
    }
    if (active === cashInput.value) { upiInput.value?.focus(); upiInput.value?.select() }
    else if (active === upiInput.value) { cardInput.value?.focus(); cardInput.value?.select() }
    else if (active === cardInput.value) { creditInput.value?.focus(); creditInput.value?.select() }
    else if (active === creditInput.value) { discountInput.value?.focus(); discountInput.value?.select() }
    else if (active === discountInput.value) { remarksInput.value?.focus(); remarksInput.value?.select() }
  } else {
    navigateBills(1)
  }
}

function handleArrowLeft() {
  const active = document.activeElement
  if (active.tagName === 'INPUT') {
    active.blur()
    // By blurring, we return to "navigation mode" where ArrowUp/Down work on the sidebar
  }
}

function handleArrowRight() {
  const active = document.activeElement
  if (active.tagName !== 'INPUT' && selectedInvoice.value) {
    if (isCredit.value) {
      dueDateInput.value?.focus()
    } else {
      cashInput.value?.focus()
      cashInput.value?.select()
    }
  }
}

function handleEnter(e) {
  const active = document.activeElement
  
  // 1. If we are in navigation mode (no input focused)
  if (active.tagName !== 'INPUT' && active !== postButton.value) {
    // If there's a highlighted invoice and it's not the selected one, select it
    if (highlightedInvoiceName.value && (!selectedInvoice.value || selectedInvoice.value.name !== highlightedInvoiceName.value)) {
      const inv = invoices.value.find(i => i.name === highlightedInvoiceName.value)
      if (inv) {
        selectInvoice(inv)
        return
      }
    }

    if (!selectedInvoice.value) {
      if (invoices.value.length) selectInvoice(invoices.value[0])
      return
    }

    // If already selected, proceed to next step
    if (unallocatedPayments.value.length > 0 && (selectedInvoice.value.rounded_total || selectedInvoice.value.grand_total || 0) > 0) {
      showReconcileModal.value = true
    } else if (isCredit.value) {
      dueDateInput.value?.focus()
    } else {
      cashInput.value?.focus()
    }
    return
  }

  if (isCredit.value) {
    if (active === dueDateInput.value) {
      remarksInput.value?.focus()
      remarksInput.value?.select()
    } else if (active === remarksInput.value) {
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
      creditInput.value?.focus()
      creditInput.value?.select()
    } else if (active === creditInput.value) {
      discountInput.value?.focus()
      discountInput.value?.select()
    } else if (active === discountInput.value) {
      remarksInput.value?.focus()
      remarksInput.value?.select()
    } else if (active === remarksInput.value) {
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
  if (isSubwindowActive()) return
  if (e.key === 'F9') {
    e.preventDefault()
    processPayment()
  } else if (e.key === 'End') {
    if (canSubmit.value) {
      e.preventDefault()
      postButton.value?.focus()
    }
  } else if (e.key.toLowerCase() === 'r' && !e.ctrlKey && !e.altKey && !e.metaKey) {
    // shortcutManager drops every single-character key while an input is focused, and
    // this page parks the caret in a payment box the moment a bill is selected — so its
    // registered 'R' never fired. Handled here for exactly the focused-input case; with
    // no input focused the manager still owns it, and acting again would double-toggle.
    const t = e.target
    const inInput = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)
    if (!inInput) return
    // Remarks is the one field where 'r' is real text the operator meant to type
    if (t === remarksInput.value || t.tagName === 'TEXTAREA' || t.isContentEditable) return
    e.preventDefault()
    if (hasPaymentValues.value) {
      // Silently doing nothing here is what makes the key look broken
      errorMsg.value = 'Clear the entered amounts before switching Cash/Credit.'
      return
    }
    toggleCredit()
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
const handleSeriesClickAway = (e) => {
  if (!e.target.closest('.series-dropdown-container')) {
    showSeriesDropdown.value = false
  }
}

const handleGlobalDateFocus = () => {
  postingDateInput.value?.focus()
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', handleGlobalDateFocus)
  window.addEventListener('click', handleSeriesClickAway)
  
  initAccountsFromLocalStorage()
  fetchSeriesList()
  loadInvoices()
  // Immediately block if no opening recorded (fast path via localStorage)
  if (!Number(localStorage.getItem('wb-opening-box-cash') || 0)) {
    showCashierEntry.value = true
  }
  checkDayOpening()
  window.addEventListener('keydown', handleKeydown)

  _billPanelCleanup = onBillPanelUpdate('Sales Invoice', sidebarSeries, loadInvoices)
})

let _billPanelCleanup = null

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', handleGlobalDateFocus);
  window.removeEventListener('click', handleSeriesClickAway)
  window.removeEventListener('keydown', handleKeydown)
  _billPanelCleanup?.()
})

// Register shortcuts
useShortcuts(cashierpageShortcuts({
  navigateBillsUp: handleArrowUp,
  navigateBillsDown: handleArrowDown,
  navigatePanelLeft: handleArrowLeft,
  navigatePanelRight: handleArrowRight,
  handleEnter: handleEnter,
  toggleCredit: () => { if (!hasPaymentValues.value) toggleCredit() },
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
  background: var(--color-border);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-surface-raised);
}

input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
input[type="date"]::-webkit-inner-spin-button,
input[type="date"]::-webkit-calendar-picker-indicator {
  display: none;
  -webkit-appearance: none;
}
input[type="date"]::-webkit-datetime-edit {
  display: flex;
  justify-content: center;
  width: 100%;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
