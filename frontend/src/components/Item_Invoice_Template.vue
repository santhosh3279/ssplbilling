<template>
  <div class="flex h-full overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)] font-sans">
    <!-- Optional Sidebar (based on SalesEntry) -->
    <aside 
      v-if="showSidebar" 
      class="flex flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden shrink-0 transition-all duration-300 ease-in-out"
      :class="isSidebarCollapsed ? 'w-0 border-r-0' : 'w-[20%] xl:w-[15%]'"
    >
      <div :class="{'opacity-0 invisible': isSidebarCollapsed, 'opacity-100 visible': !isSidebarCollapsed}" class="flex flex-col h-full transition-opacity duration-200">
        <slot name="sidebar">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">{{ sidebarTitle }}</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-[var(--color-border)] p-0 bg-[var(--color-bg)]">
          <button @click="$emit('sidebar-date-change', -1)" class="rounded p-2 text-xl text-[var(--color-text-muted)]">&larr;</button>
          <div class="flex-1 text-center font-bold text-[var(--color-text)] text-lg">{{ formatDate(sidebarDate) }}</div>
          <button @click="$emit('sidebar-date-change', 1)" class="rounded p-2 text-xl text-[var(--color-text-muted)]">&rarr;</button>
        </div>

        <!-- Search & Series Filters -->
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3 bg-[var(--color-surface-raised)]/20">
          <div class="relative group">
            <input
              ref="sidebarSearchRef"
              type="text"
              :value="sidebarSearch"
              @input="$emit('update:sidebarSearch', $event.target.value)"
              placeholder="Search bills..."
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-10 pr-3 text-[15px] font-bold text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10 transition-all"
            />
            <svg class="absolute left-3.5 top-2.5 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
          <div class="relative series-dropdown-container">
            <button
              @click="showSeriesDropdown = !showSeriesDropdown"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-1.5 px-3 text-[15px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] transition-all text-left flex justify-between items-center h-9"
            >
              <span class="truncate">{{ sidebarSeries.length === availableSeries.length ? 'All Series' : (sidebarSeries.length > 0 ? sidebarSeries[0] + (sidebarSeries.length > 1 ? '..' : '') : 'None') }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" :class="{'rotate-180': showSeriesDropdown}" class="transition-transform"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            
            <!-- Dropdown Menu -->
            <div v-if="showSeriesDropdown" class="absolute top-full left-0 mt-1 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-2xl z-50 py-2 max-h-64 overflow-y-auto custom-scrollbar">
              <div class="px-3 py-1.5 border-b border-[var(--color-border)] mb-1 flex items-center gap-2 cursor-pointer select-none" @click="toggleAllSeries">
                <input 
                  type="checkbox" 
                  :checked="sidebarSeries.length === availableSeries.length" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-bold uppercase tracking-wider">All Series</span>
              </div>
              <div v-for="s in availableSeries" :key="s" class="px-3 py-1.5 flex items-center gap-2 cursor-pointer select-none" @click="toggleSeries(s)">
                <input 
                  type="checkbox" 
                  :checked="isSeriesSelected(s)" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-bold uppercase tracking-wider">{{ s }}</span>
              </div>
            </div>
          </div>
          <button
            @click="$emit('toggle-draft-only')"
            class="w-full rounded-xl border py-1.5 text-[10px] font-bold uppercase transition-all"
            :class="draftOnly ? 'bg-[var(--color-warning)]/40 border-[var(--color-warning)] text-[var(--color-warning)] shadow-sm' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)]'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Bills' }}
          </button>
        </div>

        <!-- Bill List -->
        <div ref="sidebarListRef" class="flex-1 overflow-y-auto scrollbar-none">
          <slot name="sidebar-list">
            <div v-if="sidebarLoading" class="p-4 text-center text-lg text-[var(--color-text-muted)]">Loading...</div>
            <div v-else-if="!sidebarItems.length" class="p-4 text-center text-lg text-[var(--color-text-muted)] italic">No bills found</div>
            <div
              v-for="(inv, idx) in sidebarItems"
              :key="inv.name"
              :ref="el => setSidebarItemRef(el, idx)"
              tabindex="0"
              @click="$emit('select-sidebar-item', inv)"
              @keydown.enter="$emit('select-sidebar-item', inv)"
              @keydown.up.prevent="navigateSidebar(idx, -1)"
              @keydown.down.prevent="navigateSidebar(idx, 1)"
              class="group cursor-pointer border-b border-[var(--color-border)] px-2 py-1 transition-colors outline-none focus:bg-[var(--color-focus)] focus:border-l-2 focus:border-l-[var(--color-focus)]"
              :class="{ 'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)]': selectedSidebarItemName === inv.name }"
            >
              <div class="flex items-center justify-between gap-1">
                <div class="flex items-center gap-1.5 truncate min-w-0">
                  <span class="h-2 w-2 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-[var(--color-success)]' : 'bg-[var(--color-danger)]'"></span>
                  <span class="truncate font-mono text-2xl group-focus:text-[var(--color-text-on-focus)] group-focus:font-bold" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)] font-bold' : 'text-[var(--color-highlight)]'">{{ inv.name }}</span>
                  <span v-if="inv.mop" class="text-[10px] px-1 rounded border uppercase font-bold shrink-0"
                    :class="inv.mop === 'Cash' ? 'border-[var(--color-success)]/40 text-[var(--color-success)]' : 'border-[var(--color-warning)]/40 text-[var(--color-warning)]'">
                    {{ inv.mop }}
                  </span>
                </div>
                <span class="shrink-0 font-mono font-normal text-4xl tabular-nums group-focus:text-[var(--color-text-on-focus)]" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ inv.rounded_total ?? inv.grand_total }}</span>
              </div>
              <div class="truncate text-2xl group-focus:text-[var(--color-text-on-focus)]" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
                {{ inv.customer_name }}
              </div>
            </div>
          </slot>
        </div>
      </slot>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 flex-col overflow-hidden bg-[var(--color-bg)]">
      <!-- Top Nav Bar -->
      <div
        class="flex items-center justify-between border-b border-[var(--color-border)]/60 px-4 py-2"
        :style="titleBarColor ? { backgroundColor: titleBarColor } : {}"
        :class="!titleBarColor ? 'bg-[var(--color-surface-raised)]/60' : ''"
      >
        <div class="flex items-center gap-3">
          <!-- Sidebar Toggle (Collapsible) -->
          <button
            v-if="showSidebar"
            @click="isSidebarCollapsed = !isSidebarCollapsed"
            class="flex items-center justify-center rounded p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-colors mr-1"
            :title="isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'"
          >
            <svg v-if="isSidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"></polyline><polyline points="18 17 13 12 18 7"></polyline></svg>
          </button>

          <button v-if="showBackButton" class="rounded px-2 py-1 text-2xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]" @click="$emit('back')">&larr; Back</button>
          <span v-if="showBackButton" class="text-[var(--color-border)] text-2xl">|</span>
          <span class="text-2xl font-semibold text-[var(--color-text)]">{{ title }}</span>

          <!-- ERPNext Links -->
          <div class="ml-4 flex items-center gap-3 bg-[var(--color-surface-raised)] px-4 py-1.5 rounded-full border border-[var(--color-border)] shadow-sm">
            <a :href="erpNextListUrl" target="_blank" title="Go to ERPNext Listview" class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:text-[var(--color-highlight)] transition-colors">List</a>
            <span class="h-3 w-px bg-[var(--color-border)] opacity-50"></span>
            <a :href="`/app/${doctype.toLowerCase().replace(/ /g, '-')}/new`" target="_blank" title="Create New in ERPNext" class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] hover:text-[var(--color-highlight)] transition-colors">New</a>
            <template v-if="docNumber">
              <span class="h-3 w-px bg-[var(--color-border)] opacity-50"></span>
              <a :href="erpNextUrl" target="_blank" title="Open this document in ERPNext" class="text-xs font-black uppercase tracking-wider text-[var(--color-highlight)] hover:underline">Open</a>
            </template>
          </div>
        </div>
        <div class="flex items-center gap-3 text-xl text-[var(--color-text-muted)]">
          <slot name="header-right"></slot>
        </div>
      </div>

      <!-- Header Bar (Series / Customer / Date) -->
      <div class="border-b border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2">
        <div class="flex flex-col gap-2">
          <slot name="header-bar">
            <!-- Line 1: Doc Number, Party Name, Mobile, GST, Balance -->
            <div class="flex items-center gap-6 overflow-hidden">
              <div v-if="docNumber" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
                <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ docNumber }}</div>
              </div>

              <div 
                class="flex-1 flex items-baseline gap-6 overflow-hidden transition-colors group"
                :class="isReadOnly ? 'cursor-default' : 'cursor-pointer hover:bg-[var(--color-surface-raised)]/80'"
                @click="!isReadOnly && $emit('party-click')"
              >
                <div class="flex items-baseline gap-3 shrink-0">
                  <label 
                    class="text-xl font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap transition-colors"
                    :class="!isReadOnly ? 'group-hover:text-[var(--color-highlight)]' : ''"
                  >Party</label>
                  <div class="text-5xl font-bold text-[var(--color-text)] truncate max-w-[600px]">{{ partyName || 'Not Selected' }}</div>
                </div>

                <div v-if="partyMobile" class="flex items-center gap-1 text-[var(--color-highlight)] font-mono text-3xl whitespace-nowrap shrink-0">
                  <span class="text-xl uppercase text-[var(--color-text-muted)]">Mob:</span>
                  {{ partyMobile }}
                </div>

                <div v-if="partyGstin" class="flex items-center gap-1 text-[var(--color-text)]/70 font-mono text-3xl whitespace-nowrap shrink-0">
                  <span class="text-xl uppercase text-[var(--color-text-muted)]">GST:</span>
                  {{ partyGstin }}
                </div>

                <div v-if="partyBalance !== null" class="flex items-center gap-2 whitespace-nowrap shrink-0">
                  <span class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Balance</span>
                  <span
                    class="text-3xl font-bold font-mono"
                    :class="(Number(partyBalance) > 0) ? 'text-[var(--color-success)]' : (Number(partyBalance) < 0) ? 'text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'"
                  >
                    ₹ {{ Math.abs(partyBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                    <span class="text-xl">{{ (Number(partyBalance) > 0) ? 'DR' : (Number(partyBalance) < 0) ? 'CR' : '' }}</span>
                  </span>
                </div>

                <div v-if="postingTime && showMop" class="flex items-center gap-2 border-l border-[var(--color-border)] pl-6 whitespace-nowrap shrink-0 ml-auto">
                  <span class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Time</span>
                  <span class="text-3xl font-bold font-mono text-[var(--color-text)]">{{ formatTime(postingTime) }}</span>
                </div>

                <div v-if="showMop" @click.stop class="flex items-center gap-2 border-l border-[var(--color-border)] pl-6 whitespace-nowrap shrink-0" :class="{'ml-auto': !(postingTime && showMop)}">
                  <span class="text-xl font-bold uppercase text-[var(--color-text-muted)]">MOP</span>
                  <select
                    ref="mopSelectRef"
                    :value="mop"
                    @change="$emit('update:mop', $event.target.value)"
                    :disabled="isReadOnly"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-2xl font-bold text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] focus:border-[var(--color-focus)] disabled:opacity-80"
                    @keydown.enter.prevent="$emit('mop-enter')"
                  >
                    <option value="Cash">Cash</option>
                    <option value="Credit">Credit</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Line 2: Secondary Details -->
            <div class="flex items-center gap-8 border-t border-[var(--color-border)]/30 pt-2">
              <div v-if="partyLastInvDate" class="flex items-center gap-2 whitespace-nowrap shrink overflow-hidden">
                <span class="text-xl font-bold uppercase text-[var(--color-text-muted)] shrink-0">Last Inv</span>
                <span class="text-3xl font-mono text-[var(--color-highlight)] truncate">{{ partyLastInvDate }}</span>
              </div>

              <div v-if="partyModifier !== null && Number(partyModifier) !== 0" class="flex items-center gap-2 border-l border-[var(--color-border)] pl-6 whitespace-nowrap">
                <span class="text-3xl font-mono font-bold" :class="ignoreModifier ? 'text-[var(--color-text-muted)] line-through' : 'text-[var(--color-warning)]'">{{ partyModifier }}</span>
                <input
                  type="checkbox"
                  :checked="!ignoreModifier"
                  :disabled="isReadOnly"
                  class="h-[25px] w-[25px] accent-[var(--color-warning)] disabled:opacity-50 disabled:cursor-default"
                  :class="isReadOnly ? '' : 'cursor-pointer'"
                  title="Apply Multiplier"
                  @change="$emit('update:ignoreModifier', !$event.target.checked)"
                />
              </div>

              <div v-if="docDate" class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
                <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Date</label>
                <div class="flex items-center gap-1">
                  <button @click="$emit('doc-date-change', -1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&larr;</button>
                  <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(docDate) }}</div>
                  <button @click="$emit('doc-date-change', 1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&rarr;</button>
                </div>
              </div>
            </div>
          </slot>
        </div>
      </div>

      <!-- Items Table Area -->
      <div class="flex flex-[7] flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto overflow-x-hidden scrollbar-none">
          <table class="w-full text-sm border-collapse border-l border-t border-[var(--color-border)]">
            <thead>
              <tr class="sticky top-0 z-10 bg-[var(--color-lowlight)] border-b border-[var(--color-border)]">
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-8">#</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Barcode</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)]">Item Name</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-16">Qty</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-14">UOM</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Rate</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-28">Disc %</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-warning)] w-24">DISC</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Tax %</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">Amount</th>
                <th class="border-b border-[var(--color-border)] w-8"></th>
              </tr>
            </thead>
            <tbody>
              <!-- #row slot wraps the entire <tr> so consumers can add :class/:ref/@click on the row -->
              <template v-for="(item, idx) in items" :key="idx">
                <slot name="row" :item="item" :index="idx" :formatQty="formatQty" :format="format">
                  <tr class="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]/50">
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl font-mono text-center">{{ idx + 1 }}</td>
                    <td class="px-2 py-1 border-r border(--color-border)] text-[var(--color-highlight)] text-4xl font-mono">{{ item.item_code }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-4xl font-medium">{{ item.item_name }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-6xl font-mono text-right tabular-nums">{{ formatQty(item.qty, item.uom) }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ item.uom || 'Nos' }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ format(item.rate) }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-warning)] text-4xl font-mono text-right">{{ format(item.discount_percentage) }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-warning)]/80 text-4xl font-mono text-right tabular-nums">
                      {{ format((item.rate || 0) * (1 - (item.discount_percentage || item.discount || 0) / 100)) }}
                    </td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-4xl font-mono text-right tabular-nums">
                      {{ format(item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}
                    </td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ format(item.amount) }}</td>
                    <td class="px-2 py-1 text-center">
                      <button class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]" @click="$emit('delete-item', idx)">&times;</button>
                    </td>
                  </tr>
                </slot>
              </template>
              <slot name="table-extra-rows"></slot>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bottom Panel (Summary / Actions) -->
      <div class="flex flex-[4] border-t border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden">
        <!-- Insights / Left Column -->
        <div class="flex flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-y-auto scrollbar-none" style="min-width:360px;max-width:420px;">
          <slot name="bottom-left"></slot>
        </div>

        <!-- Settings / Middle Column -->
        <div class="flex flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-y-auto scrollbar-none" style="min-width:236px;max-width:270px;">
          <slot name="bottom-middle">
            <div class="flex flex-col gap-2 p-2">
              <!-- Export/Import buttons -->
              <div class="flex gap-1">
                <button @click="$emit('export')" :disabled="isReadOnly" class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-1 text-sm font-bold uppercase text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] disabled:opacity-50 disabled:cursor-default">Export</button>
                <button @click="$emit('import')" :disabled="isReadOnly" class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-1 text-sm font-bold uppercase text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] disabled:opacity-50 disabled:cursor-default">Import</button>
              </div>

              <!-- Price List -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Price List</label>
                <div class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-xl text-[var(--color-text)] truncate">{{ priceList }}</div>
              </div>

              <!-- Tax -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Tax</label>
                <div class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-xl text-[var(--color-text)] truncate">{{ taxTemplate || '-- None --' }}</div>
              </div>

              <!-- 3 Checkboxes: Inclusive, Pricing Rule, Sale Return -->
              <div class="flex flex-col gap-1.5 py-1">
                <label class="flex items-center gap-2">
                  <input type="checkbox" :checked="isInclusiveTax" disabled class="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-highlight)]" />
                  <span class="text-[var(--color-text-muted)] text-lg font-bold uppercase">Inclusive Tax</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" :checked="ignoreDiscountRule" disabled class="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-warning)]" />
                  <span class="text-[var(--color-text-muted)] text-lg font-bold uppercase">Ignore Pricing Rule</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" :checked="isReturn" disabled class="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-danger)]" />
                  <span class="text-[var(--color-text-muted)] text-lg font-bold uppercase">Sale Return</span>
                </label>
              </div>

              <!-- Warehouse -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
                <div class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-lg text-[var(--color-text-muted)] truncate">{{ warehouse || 'None' }}</div>
              </div>

              <!-- Cost Center -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
                <div class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-lg text-[var(--color-text-muted)] truncate">{{ costCenter || 'None' }}</div>
              </div>
            </div>
          </slot>
        </div>

        <!-- Summary / Right Column (Calculation Panel + Actions) -->
        <div class="flex-1 flex overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface-raised)]/50">
          <!-- Left Side: Calculation Rows (Scrollable) -->
          <div class="flex-[49] overflow-y-auto scrollbar-none border-r border-[var(--color-border)]">
            <table class="w-full border-collapse text-base" style="table-layout:fixed">
              <colgroup>
                <col style="width:35%"><col style="width:36%"><col style="width:29%">
              </colgroup>
              <tbody>
                <slot name="calculation-rows">
                  <!-- Default Calculation Rows (Props based) -->
                  <!-- Item Discount -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Item Discount</td>
                    <td class="p-0 border border-[var(--color-border)] text-center text-lg text-[var(--color-text-muted)] italic">Auto</td>
                    <td class="px-2 text-right font-mono text-[var(--color-danger)] text-4xl border border-[var(--color-border)]">-{{ format(itemDiscountTotal) }}</td>
                  </tr>
                  <!-- Global Discount -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Discount</td>
                    <td class="p-0 border border-[var(--color-border)]">
                      <div class="flex h-full items-stretch">
                        <!-- Pct Half -->
                        <div class="flex flex-1 items-center border-r border-[var(--color-border)]/50">
                          <span class="pl-2 pr-1 text-[var(--color-text-muted)] font-bold text-lg">%</span>
                          <input
                            ref="discountPctRef"
                            type="number"
                            :value="discountPct"
                            @input="$emit('update:discountPct', $event.target.value)"
                            @keydown="$emit('discount-pct-keydown', $event)"
                            :disabled="isReadOnly"
                            class="w-full h-full bg-transparent text-[var(--color-text)] font-mono text-3xl text-right outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none disabled:opacity-50"
                          />
                        </div>
                        <!-- Amt Half -->
                        <div class="flex flex-1 items-center">
                          <input
                            ref="discountAmtRef"
                            type="number"
                            :value="discountDirectAmt"
                            @input="$emit('update:discountDirectAmt', $event.target.value)"
                            @keydown.enter.prevent="freightRef?.focus(); freightRef?.select()"
                            @keydown="$emit('discount-amt-keydown', $event)"
                            :disabled="isReadOnly"
                            class="w-full h-full bg-transparent text-[var(--color-text)] font-mono text-3xl text-right px-2 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none placeholder:text-[var(--color-text-muted)]/20 disabled:opacity-50"
                            placeholder="Amt"
                          />
                        </div>
                      </div>
                    </td>
                    <td class="px-2 text-right font-mono text-[var(--color-danger)] text-4xl border border-[var(--color-border)]">-{{ format(discountAmt) }}</td>
                  </tr>
                  <!-- Subtotal -->
                  <tr class="bg-[var(--color-surface-raised)]/40">
                    <td class="px-2 text-2xl text-[var(--color-text)]/80 border border-[var(--color-border)]">Subtotal</td>
                    <td class="p-0 border border-[var(--color-border)] h-full"></td>
                    <td class="px-2 text-right font-mono text-[var(--color-text)] text-4xl border border-[var(--color-border)]">{{ format(subtotal) }}</td>
                  </tr>
                  <!-- Tax -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Tax</td>
                    <td class="p-0 border border-[var(--color-border)]"></td>
                    <td class="px-2 text-right font-mono text-[var(--color-text-muted)] text-4xl border border-[var(--color-border)]">+{{ format(totalTax) }}</td>
                  </tr>
                  <!-- Freight -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Freight</td>
                    <td class="p-0 border border-[var(--color-border)]">
                      <input
                        ref="freightRef"
                        type="number"
                        :value="freightEntry"
                        @input="$emit('update:freightEntry', $event.target.value)"
                        @keydown.enter.prevent="packingRef?.focus(); packingRef?.select()"
                        :disabled="isReadOnly"
                        class="w-full h-full block bg-transparent text-[var(--color-text)] font-mono text-3xl py-2 text-right px-2 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none disabled:opacity-50"
                      />
                    </td>
                    <td class="px-2 text-right font-mono text-[var(--color-highlight)] text-4xl border border-[var(--color-border)]">+{{ format(freightAmt) }}</td>
                  </tr>
                  <!-- Packing -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Packing</td>
                    <td class="p-0 border border-[var(--color-border)]">
                      <input
                        ref="packingRef"
                        type="number"
                        :value="packingEntry"
                        @input="$emit('update:packingEntry', $event.target.value)"
                        @keydown.enter.prevent="loadingRef?.focus(); loadingRef?.select()"
                        :disabled="isReadOnly"
                        class="w-full h-full block bg-transparent text-[var(--color-text)] font-mono text-3xl py-2 text-right px-2 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none disabled:opacity-50"
                      />
                    </td>
                    <td class="px-2 text-right font-mono text-[var(--color-highlight)] text-4xl border border-[var(--color-border)]">+{{ format(packingAmt) }}</td>
                  </tr>
                  <!-- Loading -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">{{ loadingLabel }}</td>
                    <td class="p-0 border border-[var(--color-border)]">
                      <input
                        ref="loadingRef"
                        type="number"
                        :value="loadingEntry"
                        @input="$emit('update:loadingEntry', $event.target.value)"
                        @keydown.enter.prevent="otherRef?.focus(); otherRef?.select()"
                        :disabled="isReadOnly"
                        class="w-full h-full block bg-transparent text-[var(--color-text)] font-mono text-3xl py-2 text-right px-2 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none disabled:opacity-50"
                      />
                    </td>
                    <td class="px-2 text-right font-mono text-[var(--color-highlight)] text-4xl border border-[var(--color-border)]">+{{ format(loadingAmt) }}</td>
                  </tr>
                  <!-- Other -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Other</td>
                    <td class="p-0 border border-[var(--color-border)]">
                      <input
                        ref="otherRef"
                        type="number"
                        :value="otherEntry"
                        @input="$emit('update:otherEntry', $event.target.value)"
                        @keydown.enter.prevent="$emit('other-entry-enter'); saveBtnRef?.focus()"
                        :disabled="isReadOnly"
                        class="w-full h-full block bg-transparent text-[var(--color-text)] font-mono text-3xl py-2 text-right px-2 outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none disabled:opacity-50"
                      />
                    </td>
                    <td class="px-2 text-right font-mono text-[var(--color-highlight)] text-4xl border border-[var(--color-border)]">+{{ format(otherAmt) }}</td>
                  </tr>
                  <!-- Round Off -->
                  <tr>
                    <td class="px-2 text-2xl text-[var(--color-text-muted)] border border-[var(--color-border)]">Round Off</td>
                    <td class="p-0 border border-[var(--color-border)]"></td>
                    <td class="px-2 text-right font-mono text-[var(--color-text-muted)] text-4xl border border-[var(--color-border)]">{{ format(roundOff) }}</td>
                  </tr>
                </slot>
              </tbody>
            </table>
          </div>

          <!-- Right Side: Actions / Total Amount (Fixed) -->
          <div class="flex-[51] bg-[var(--color-bg)] overflow-y-auto custom-scrollbar px-2">
            <slot name="actions">
              <div class="flex flex-col gap-2 h-full py-2">
                <div class="rounded-xl border border-[var(--color-highlight)]/40 bg-[var(--color-highlight)]/10 p-3.5 shadow-2xl">
                  <div class="flex justify-between items-start mb-1">
                    <div class="text-lg font-black uppercase tracking-[0.3em] text-[var(--color-highlight)]">Total Amount</div>
                    <div class="text-xl font-bold text-[var(--color-text-muted)] tabular-nums">{{ items.length }} items</div>
                  </div>
                  <div class="flex items-baseline gap-2 font-bold" :class="parseFloat(totalAmount) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
                    <span class="text-[9mm] font-black">₹</span>
                    <span class="font-mono text-[15.75mm] font-black leading-none">{{ format(totalAmount) }}</span>
                  </div>
                </div>

                <!-- Row 1: Save and Print -->
                <div class="flex gap-2">
                  <button ref="saveBtnRef" @click="$emit('save')" class="flex-1 rounded py-2.5 text-center text-3xl font-semibold text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 transition-colors uppercase focus:bg-[var(--color-success)] focus:outline-none">{{ saveButtonText }}</button>
                  <button @click="$emit('print')" :disabled="!isReadOnly" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isReadOnly ? 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-midlight)] cursor-pointer' : 'border-[var(--color-border)]/40 bg-[var(--color-surface)]/30 text-[var(--color-text-muted)] cursor-not-allowed'">Print</button>
                </div>

                <!-- Row 2: Cancel and Incentive/Submit -->
                <div class="flex gap-2">
                  <button @click="$emit('cancel')" class="flex-1 rounded border border-[#C2A96E] bg-[#D4B896] py-2.5 text-center text-3xl font-semibold text-[#4A3520] hover:bg-[#C9A87A] transition-colors">Cancel</button>
                  <button v-if="showSubmitButton" v-show="isDraft && isReadOnly" @click="$emit('submit')" class="flex-1 rounded border border-[var(--color-success)] bg-[var(--color-success)]/20 py-2.5 text-center text-3xl font-semibold text-[var(--color-success)] hover:bg-[var(--color-success)]/30 transition-colors uppercase">Submit</button>
                  <button v-else-if="!showSubmitButton" @click="$emit('incentive')" class="flex-1 rounded border border-[#D8C9A8] bg-[#EDE3CC] py-2.5 text-center text-3xl font-semibold text-[#4A3520] hover:bg-[#E0D4B8] transition-colors">Incentive</button>
                </div>
              </div>
            </slot>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Item_Invoice_Template.vue
 * A reusable UI template component based on SalesEntry.vue
 */

import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useDevice } from '../composables/useDevice'
import { useLayout } from '../composables/useLayout'

const props = defineProps({
  title: { type: String, default: 'Invoice' },
  showSidebar: { type: Boolean, default: true },
  sidebarTitle: { type: String, default: 'Modify Bills' },
  showBackButton: { type: Boolean, default: true },
  titleBarColor: { type: String, default: '' },
  docNumber: { type: String, default: '' },
  partyName: { type: String, default: '' },
  partyDetails: { type: String, default: '' }, // Deprecated or for generic info
  partyAddress: { type: String, default: '' },
  partyMobile: { type: String, default: '' },
  partyGstin: { type: String, default: '' },
  partyBalance: { type: [Number, String], default: null },
  mop: { type: String, default: 'Cash' },
  showMop: { type: Boolean, default: false },
  postingTime: { type: String, default: '' },
  partyLastInvDate: { type: String, default: '' },
  partyModifier: { type: [Number, String], default: null },
  ignoreModifier: { type: Boolean, default: false },
  docDate: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  
  // Sidebar Props (sidebarDate supports v-model via update:sidebarDate emit)
  sidebarDate: { type: String, default: '' },
  sidebarSearch: { type: String, default: '' },
  sidebarSeries: { type: Array, default: () => [] },
  availableSeries: { type: Array, default: () => [] },
  draftOnly: { type: Boolean, default: false },
  sidebarLoading: { type: Boolean, default: false },
  sidebarItems: { type: Array, default: () => [] },
  selectedSidebarItemName: { type: String, default: '' },

  // Settings Panel Props
  priceList: { type: String, default: 'Standard Selling' },
  taxTemplate: { type: String, default: '' },
  isInclusiveTax: { type: Boolean, default: false },
  ignoreDiscountRule: { type: Boolean, default: false },
  isReturn: { type: Boolean, default: false },
  warehouse: { type: String, default: '' },
  costCenter: { type: String, default: '' },

  // Table Props
  defaultTaxRate: { type: [Number, String], default: 0 },

  // Calculation Panel Props
  itemDiscountTotal: { type: [Number, String], default: '0.00' },
  discountEntry: { type: String, default: '' },
  discountPct: { type: [Number, String], default: 0 },
  discountDirectAmt: { type: [Number, String], default: 0 },
  discountAmt: { type: [Number, String], default: '0.00' },
  subtotal: { type: [Number, String], default: '0.00' },
  freightEntry: { type: String, default: '' },
  freightAmt: { type: [Number, String], default: '0.00' },
  packingEntry: { type: String, default: '' },
  packingAmt: { type: [Number, String], default: '0.00' },
  loadingEntry: { type: String, default: '' },
  loadingAmt: { type: [Number, String], default: '0.00' },
  loadingLabel: { type: String, default: 'Loading' },
  otherEntry: { type: String, default: '' },
  otherAmt: { type: [Number, String], default: '0.00' },
  roundOff: { type: [Number, String], default: '0.00' },
  totalTax: { type: [Number, String], default: '0.00' },
  totalAmount: { type: [Number, String], default: '0.00' },
  saveButtonText: { type: String, default: 'Save' },
  isReadOnly: { type: Boolean, default: false },
  showSubmitButton: { type: Boolean, default: false },
  isDraft: { type: Boolean, default: false },
  doctype: { type: String, default: 'Sales Invoice' }
})

const emit = defineEmits([
  'back', 'save', 'print', 'cancel', 'incentive', 'submit', 'export', 'import', 'party-click',
  'doc-date-change', 'sidebar-date-change', 'update:sidebarDate', 'update:sidebarSearch', 'update:sidebarSeries',
  'toggle-draft-only', 'select-sidebar-item', 'delete-item', 'discount-pct-keydown', 'discount-amt-keydown',
  'update:freightEntry', 'update:packingEntry', 'update:loadingEntry', 'update:otherEntry',
  'update:discountPct', 'update:discountDirectAmt',
  'update:ignoreModifier', 'other-entry-enter'
])

const { isTablet } = useDevice()
const { isSidebarCollapsed } = useLayout()

const erpNextUrl = computed(() => {
  const slug = props.doctype.toLowerCase().replace(/ /g, '-')
  if (props.docNumber) {
    return `/app/${slug}/${props.docNumber}`
  }
  return `/app/${slug}/new`
})

const erpNextListUrl = computed(() => {
  const slug = props.doctype.toLowerCase().replace(/ /g, '-')
  return `/app/${slug}`
})

onMounted(() => {
  if (isTablet.value) {
    isSidebarCollapsed.value = true
  }
})

const sidebarSearchRef = ref(null)
const sidebarListRef = ref(null)
const showSeriesDropdown = ref(false)
const discountPctRef = ref(null)
const discountAmtRef = ref(null)
const freightRef = ref(null)
const packingRef = ref(null)
const loadingRef = ref(null)
const otherRef = ref(null)
const saveBtnRef = ref(null)
const sidebarItemRefs = new Map()

function setSidebarItemRef(el, idx) {
  if (el) sidebarItemRefs.set(idx, el)
  else sidebarItemRefs.delete(idx)
}

function toggleAllSeries() {
  if (props.sidebarSeries.length === props.availableSeries.length) {
    emit('update:sidebarSeries', [])
  } else {
    emit('update:sidebarSeries', [...props.availableSeries])
  }
}

function toggleSeries(s) {
  const current = [...props.sidebarSeries]
  const idx = current.indexOf(s)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(s)
  }
  emit('update:sidebarSeries', current)
}

function isSeriesSelected(s) {
  return props.sidebarSeries.includes(s)
}

function navigateSidebar(idx, dir) {
  const target = sidebarItemRefs.get(idx + dir)
  if (target) {
    target.focus()
    target.scrollIntoView({ block: 'nearest' })
  }
}

watch(() => props.selectedSidebarItemName, (newVal) => {
  if (!newVal) return
  nextTick(() => {
    // Find index of the item with this name
    const idx = props.sidebarItems.findIndex(inv => inv.name === newVal)
    if (idx !== -1) {
      const el = sidebarItemRefs.get(idx)
      if (el) {
        el.focus({ preventScroll: true })
        el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
      }
    }
  })
})

const mopSelectRef = ref(null)

defineExpose({
  focusSidebar: () => sidebarSearchRef.value?.focus(),
  focusSidebarList: () => sidebarListRef.value?.querySelector('[tabindex="0"]')?.focus(),
  focusDiscountPct: () => { discountPctRef.value?.focus(); discountPctRef.value?.select() },
  focusDiscountAmt: () => { discountAmtRef.value?.focus(); discountAmtRef.value?.select() },
  focusSaveBtn: () => saveBtnRef.value?.focus(),
  focusMop: () => mopSelectRef.value?.focus(),
  toggleSidebar: () => { isSidebarCollapsed.value = !isSidebarCollapsed.value }
})

onMounted(() => {
  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key.toLowerCase() === 'b') {
      e.preventDefault()
      isSidebarCollapsed.value = !isSidebarCollapsed.value
    }
  }
  window.addEventListener('keydown', handleKeyDown)
  onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
})

function formatTime(timeStr) {
  if (!timeStr) return ''
  const parts = timeStr.split('.')
  let mainTime = parts[0].trim()
  if (/^\d:\d{2}:\d{2}$/.test(mainTime)) {
    mainTime = '0' + mainTime
  }
  return mainTime
}

function formatDate(dateString) {
  if (!dateString) return 'Select Date'
  const d = new Date(dateString)
  if (isNaN(d)) return dateString
  // Format as DD-MMM-YYYY
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

function format(val) {
  if (val === null || val === undefined || val === '') return '0.00'
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

function formatQty(val, uom) {
  if (val === null || val === undefined || val === '') return '0'
  const num = Number(val)
  if (isNaN(num)) return '0'
  // For 'Nos' UOM, don't show decimals and don't allow float (truncate)
  if (uom === 'Nos' || !uom) {
    return Math.floor(num).toString()
  }
  return num.toFixed(2)
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--color-highlight); }
</style>
