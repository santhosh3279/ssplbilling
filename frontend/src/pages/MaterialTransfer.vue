<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-[var(--color-bg)]' : 'h-screen bg-[var(--color-bg)]'" class="flex">
    <!-- LEFT SIDEBAR: MODIFY ENTRIES -->
    <aside class="flex w-[18%] flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden shrink-0">
      <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-center">
        <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Modify Entries</div>
      </div>

      <!-- Date Filter -->
      <div class="flex items-center gap-1 border-b border-[var(--color-border)] p-2 bg-[var(--color-bg)]">
        <button @click="changeSidebarDate(-1)" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)] transition-colors">&larr;</button>
        <input 
          type="date" 
          v-model="sidebarDate"
          class="w-full bg-transparent text-xs font-bold text-[var(--color-text)] outline-none"
        />
        <button @click="changeSidebarDate(1)" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text)] transition-colors">&rarr;</button>
      </div>

      <!-- Search & Status Filters -->
      <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3 bg-[var(--color-surface)]/20">
        <div class="relative group">
          <input
            v-model="sidebarSearch"
            placeholder="Search bills..."
            class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-10 pr-3 text-[15px] font-bold text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10 transition-all"
          />
          <svg class="absolute left-3.5 top-2.5 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </div>
        <select
          v-model="sidebarPurpose"
          class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-2 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
        >
          <option value="">All Types</option>
          <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
        </select>
      </div>

      <!-- Entry List -->
      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <div v-if="sidebarLoading" class="p-8 text-center text-xs text-[var(--color-text-muted)] animate-pulse">Loading...</div>
        <div v-else-if="!sidebarEntries.length" class="p-8 text-center text-xs text-[var(--color-text-muted)] italic">No entries found</div>
        <div 
          v-for="entry in sidebarEntries" 
          :key="entry.name"
          @click="loadEntry(entry.name)"
          class="group cursor-pointer border-b border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 transition-all hover:bg-[var(--color-surface)]/60"
          :class="{ 'bg-[var(--color-surface)]/80 border-l-2 border-l-blue-500': entryName === entry.name }"
        >
          <div class="flex items-center justify-between gap-1 mb-0.5">
            <span class="truncate font-mono text-[13px] font-bold text-[var(--color-info)]">{{ entry.name }}</span>
            <span class="shrink-0 font-mono text-xs font-bold text-[var(--color-text)] tabular-nums">₹{{ (entry.total_value || 0).toFixed(0) }}</span>
          </div>

          <div class="flex items-center justify-between">
            <div class="truncate text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-tight">{{ entry.purpose }}</div>
            <div class="text-[9px] font-bold text-[var(--color-text-muted)] px-1 rounded bg-[var(--color-surface)] border border-[var(--color-border)]">{{ entry.posting_date }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Top Bar -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm">
        <div class="flex items-center gap-3">
          <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="handleBack">&larr; Dashboard</button>
          <span class="text-sm text-[var(--color-text-muted)]">|</span>
          <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">Material Transfer Entry</span>
        </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <div class="flex items-center rounded border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-[var(--color-border)] bg-[var(--color-surface)] px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-[var(--color-text-muted)] leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-[var(--color-text)] leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]">&plus;</button>
        </div>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Up/Down</kbd> Navigate</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Tab</kbd> Next</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <div class="flex items-center gap-8">
        <!-- Purpose -->
        <div class="flex items-center gap-2">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">Type</label>
          <select
            v-model="purpose"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1.5 text-sm font-bold text-[var(--color-info)] outline-none focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[150px]"
          >
            <option v-for="p in availablePurposes" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <!-- From Warehouse -->
        <div v-if="purpose !== 'Material Receipt'" class="flex items-center gap-2 border-l border-[var(--color-border)] pl-8">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">From</label>
          <select
            v-model="fromWarehouse"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-lg font-bold text-[var(--color-danger)] outline-none focus:border-[var(--color-danger)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[200px]"
          >
            <option value="">-- Select Source --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <!-- Arrow -->
        <div v-if="purpose === 'Material Transfer'" class="text-2xl text-[var(--color-text-muted)]">➜</div>

        <!-- To Warehouse -->
        <div v-if="purpose !== 'Material Issue'" class="flex items-center gap-2" :class="{ 'border-l border-[var(--color-border)] pl-8': purpose === 'Material Receipt' }">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">To</label>
          <select
            v-model="toWarehouse"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-lg font-bold text-[var(--color-success)] outline-none focus:border-[var(--color-success)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] min-w-[200px]"
          >
            <option value="">-- Select Target --</option>
            <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>

        <!-- Date -->
        <div class="flex items-center gap-3 border-l border-[var(--color-border)] pl-8 ml-auto">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Date</label>
          <input
            v-model="entryDate"
            type="date"
            :disabled="entryDocStatus !== 0"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-lg font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)] tabular-nums"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-1 overflow-hidden bg-[var(--color-bg)]">
      <!-- MAIN CONTENT -->
      <div class="flex w-full flex-col p-4 overflow-hidden">
        <div class="flex-1 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm flex flex-col">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                  <th class="w-12 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">#</th>
                  <th class="w-48 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Code</th>
                  <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Name</th>
                  <th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Qty</th>
                  <th class="w-20 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">UOM</th>
                  <th class="w-32 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Rate</th>
                  <th class="w-36 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Total Value</th>
                  <th class="w-12 px-4 py-3 text-center"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="group border-b border-[var(--color-border)] last:border-0 outline-none transition-colors" :class="{ 'bg-[var(--color-info)]/30': selectedRow === idx && !item.deleted, 'bg-[var(--color-danger)]/20': item.deleted, 'hover:bg-[var(--color-surface)]/40': !item.deleted && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-4 py-2 text-[var(--color-text-muted)] font-mono">{{ idx + 1 }}</td>
                  <td class="px-4 py-2">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="entryDocStatus !== 0" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:bg-[var(--color-bg)] disabled:text-[var(--color-text-muted)]" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono font-semibold" :class="item.deleted ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-info)]'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-4 py-2">
                    <div :class="item.deleted ? 'text-[var(--color-danger)] line-through' : 'text-[var(--color-text)] font-medium'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</div>
                  </td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="entryDocStatus !== 0" min="0.001" step="any" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-[var(--color-text)] focus:border-[var(--color-info)] focus:bg-[var(--color-surface)] outline-none disabled:text-[var(--color-text-muted)]" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else :class="item.deleted ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text)]'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.qty }}</span>
                  </td>
                  <td class="px-4 py-2 text-[var(--color-text-muted)]" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-4 py-2 text-right font-mono">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="entryDocStatus !== 0" step="0.01" class="w-full rounded border border-transparent bg-transparent px-2 py-1 text-right text-[var(--color-text)] focus:border-[var(--color-info)] focus:bg-[var(--color-surface)] outline-none disabled:text-[var(--color-text-muted)]" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else :class="item.deleted ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text)]'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ (item.rate || 0).toFixed(2) }}</span>
                  </td>
                  <td class="px-4 py-2 text-right font-mono font-bold text-[var(--color-text)]" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ (item.qty * item.rate).toFixed(2) }}</td>
                  <td class="px-4 py-2 text-center">
                    <button v-if="!item.deleted" class="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)] opacity-0 group-hover:opacity-100 transition" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else class="text-[10px] font-bold text-[var(--color-info)] hover:underline" @click.stop="restoreItem(idx)">RESTORE</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="entryDocStatus === 0" class="border-b border-[var(--color-border)] bg-[var(--color-info)]/10" :class="{ 'bg-[var(--color-info)]/30 ring-2 ring-inset ring-[var(--color-info)]': selectedRow === -1 }" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-4 py-3 text-[var(--color-info)] font-bold">+</td>
                  <td class="px-4 py-3">
                    <input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Item code / Scan" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" />
                  </td>
                  <td class="px-4 py-3">
                    <div class="text-[var(--color-text-muted)] italic" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ newPending.item_name || 'Scan or type to find item...' }}</div>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <input ref="newQtyInput" v-model.number="newQty" type="number" min="0.001" step="any" class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-right font-mono text-[var(--color-text)] outline-none focus:border-[var(--color-info)] shadow-sm" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="addNewItem" />
                  </td>
                  <td class="px-4 py-3 text-[var(--color-text-muted)]">{{ newPending.uom || '--' }}</td>
                  <td class="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono">{{ (newPending.rate || 0).toFixed(2) }}</td>
                  <td class="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono font-bold">{{ (newQty * (newPending.rate || 0)).toFixed(2) }}</td>
                  <td class="px-4 py-3"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TABLE FOOTER -->
          <div class="flex items-center justify-between border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-2.5">
            <div class="flex gap-8 items-center text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
              <span>Total Items: {{ activeItems.length }}</span>
              <span v-if="deletedCount > 0" class="text-[var(--color-danger)]">{{ deletedCount }} DELETED</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-widest">Transfer Total:</span>
              <span class="text-2xl font-mono font-black text-[var(--color-text)]">₹{{ totalValue.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <!-- BOTTOM PANEL: INSIGHT & ACTIONS -->
        <div class="mt-4 flex gap-4 h-[200px]">
          <!-- Item Insight -->
          <div class="flex-[3] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm overflow-y-auto">
            <div class="mb-3 text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Item Insight <span v-if="selectedItemData" class="ml-2 text-[var(--color-info)] font-mono">{{ selectedItemData.item_code }}</span></div>
            <template v-if="selectedItemData">
              <div class="flex gap-12">
                <div class="flex flex-col gap-3 min-w-[200px]">
                  <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-1">
                    <span class="text-xs font-bold text-[var(--color-text-muted)]">From (Source)</span>
                    <span class="rounded bg-[var(--color-danger)]/20 px-2 py-0.5 text-xs font-bold text-[var(--color-danger)] font-mono">{{ stockAtSource }} {{ selectedItemData.uom }}</span>
                  </div>
                  <div class="flex items-center justify-between border-b border-[var(--color-border)] pb-1">
                    <span class="text-xs font-bold text-[var(--color-text-muted)]">To (Target)</span>
                    <span class="rounded bg-[var(--color-success)]/20 px-2 py-0.5 text-xs font-bold text-[var(--color-success)] font-mono">{{ stockAtTarget }} {{ selectedItemData.uom }}</span>
                  </div>
                </div>
                <div class="flex-1">
                  <div class="text-xs font-bold text-[var(--color-text-muted)] mb-2">Valuation Details</div>
                  <div class="flex items-baseline gap-2">
                    <span class="text-2xl font-mono font-bold text-[var(--color-text)]">₹{{ (selectedItemData.valuation_rate || 0).toFixed(2) }}</span>
                    <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase">Per {{ selectedItemData.uom }}</span>
                  </div>
                </div>
              </div>
            </template>
            <div v-else class="flex h-full items-center justify-center text-sm italic text-[var(--color-text-muted)]">
              Select an item to see real-time stock and valuation
            </div>
          </div>

          <!-- Actions -->
          <div class="flex-[1] flex flex-col gap-2">
            <button
              ref="saveButton"
              @click="saveEntry"
              :disabled="entryDocStatus !== 0"
              class="flex-1 rounded-xl bg-[var(--color-info)] text-lg font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] active:scale-95 transition-all disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)]"
            >
              {{ entryName ? 'Update Entry' : 'Save Draft (Ctrl+S)' }}
            </button>
            <button
              v-if="entryName && entryDocStatus === 0"
              @click="submitEntry"
              class="h-12 rounded-xl bg-[var(--color-success)] text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-success)] active:scale-95 transition-all"
            >
              Submit / Post
            </button>
            <button
              v-if="entryName"
              @click="showIncentiveModal = true"
              class="h-10 rounded-xl border border-[var(--color-info)] bg-[var(--color-info)]/20 text-sm font-semibold text-[var(--color-info)] hover:bg-[var(--color-info)]/40 transition-all"
            >👥 Incentive</button>
            <div class="flex gap-2 h-14">
              <button @click="startNewEntry" class="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition">Clear</button>
              <button @click="handleBack" class="flex-1 rounded-xl border border-[var(--color-danger)] bg-[var(--color-danger)]/20 text-sm font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)]/40 transition">Exit</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

    <!-- INCENTIVE ENTRY MODAL -->
    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Stock Entry"
      :docname="entryName"
      @close="showIncentiveModal = false"
      @saved="showIncentiveModal = false"
    />

    <!-- SERIES SUBWINDOW -->
    <div
      v-if="showSeriesDropdown"
      class="fixed inset-0 z-[120] flex items-center justify-center bg-black/70 backdrop-blur-sm"
      @click.self="showSeriesDropdown = false"
      @keydown.escape.capture="showSeriesDropdown = false"
    >
      <div class="w-[360px] overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3">
          <div class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Select Series</div>
          <div class="mt-0.5 text-[10px] text-[var(--color-text-muted)]">↑ ↓ navigate · Enter select · 1–9 quick pick</div>
        </div>
        <div class="p-3 flex flex-col gap-2">
          <button
            v-for="(s, idx) in availableSeries"
            :key="s"
            class="flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-all focus:outline-none"
            :class="idx === seriesHighlightIdx
              ? 'border-[var(--color-info)] bg-[var(--color-info)]/30 text-[var(--color-text-on-highlight)] ring-1 ring-[var(--color-info)]'
              : s === entrySeries
                ? 'border-[var(--color-info)] bg-[var(--color-info)]/20 text-[var(--color-info)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]'"
            @click="selectSeries(s)"
            @mouseenter="seriesHighlightIdx = idx"
          >
            <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[var(--color-surface-raised)] font-mono text-sm font-black text-[var(--color-text)]">
              {{ idx + 1 }}
            </span>
            <span class="font-bold tracking-wide">{{ s }}</span>
            <span v-if="s === entrySeries" class="ml-auto text-[10px] font-bold text-[var(--color-info)]">ACTIVE</span>
          </button>
        </div>
        <div class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 px-5 py-2 text-[10px] text-[var(--color-text-muted)] text-center">
          Esc to close
        </div>
      </div>
    </div>

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Stock"
      :warehouse="fromWarehouse"
      :skip-date-filter="true"
      @close="showItemSearchModal = false"
      @select="pickItem"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import ItemSearch from '../components/ItemSearch.vue'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { materialTransferShortcuts } from '../shortcuts/materialTransferShortcuts'

const router = useRouter()
const API = 'ssplbilling.api.stock_api'
const { allowedSeries: availableSeries, fetchAllowedSeries } = useAllowedSeries()

// ==================== PROPS & EMITS ====================
const props = defineProps({
  isSubWindow: Boolean,
  name: String
})
const emit = defineEmits(['close'])

if (props.isSubWindow) useSubwindow()

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const newItemCode = ref('')
const newQty = ref(1)
const entryName = ref(null)
const entryDocStatus = ref(0)
const entryDate = ref(new Date().toISOString().split('T')[0])
const entrySeries = ref('')
const purpose = ref('Material Transfer')
const fromWarehouse = ref('')
const toWarehouse = ref('')

const availableSeries = ref([])
const availableWarehouses = ref([])
const availablePurposes = ref(['Material Issue', 'Material Receipt', 'Material Transfer'])
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)

const newPending = ref({ item_name: '', uom: '', rate: 0 })
const selectedItemData = ref(null)

const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`
}))

const activeItems = computed(() => items.value.filter(i => !i.deleted))
const deletedCount = computed(() => items.value.filter(i => i.deleted).length)
const totalValue = computed(() => activeItems.value.reduce((s, i) => s + (i.qty * i.rate), 0))

// ==================== REFS & FOCUS ====================
const inputRefs = {}
const rowRefs = {}
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const seriesSelect = ref(null)
const showSeriesDropdown = ref(false)
const seriesHighlightIdx = ref(0)
const saveButton = ref(null)
const itemSearchModalRef = ref(null)
const showItemSearchModal = ref(false)

function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }

function focusField(f, idx) { nextTick(() => inputRefs[`${f}-${idx}`]?.focus()) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusNewCode()   { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty()    { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }

function openSeriesModal() {
  seriesHighlightIdx.value = Math.max(0, availableSeries.value.indexOf(entrySeries.value))
  showSeriesDropdown.value = true
}

function selectSeries(s) {
  entrySeries.value = s
  showSeriesDropdown.value = false
  nextTick(focusNewCode)
}

// ==================== NAVIGATION ====================
function findNextActiveRow(from, dir) { let i = from + dir; while (i >= 0 && i < items.value.length) { if (!items.value[i].deleted) return i; i += dir }; return null }
function moveRow(from, dir) { const n = findNextActiveRow(from, dir); if (n !== null) { selectedRow.value = n; focusRow(n) } else if (dir === 1) { selectedRow.value = -1; focusNewCode() } }
function moveToLastActiveRow() { for (let i = items.value.length - 1; i >= 0; i--) { if (!items.value[i].deleted) { selectedRow.value = i; focusRow(i); return } } }
function selectRow(idx) { if (!items.value[idx].deleted) { selectedRow.value = idx; focusRow(idx) } }
function goToNextRow(from) { const n = findNextActiveRow(from, 1); if (n !== null) { selectedRow.value = n; focusRow(n) } else { selectedRow.value = -1; focusNewCode() } }

function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); focusField('code', idx) }
}

// ==================== DATA FETCHING ====================
async function fetchConfig() {
  try {
    const series = await frappeGet(`${API}.get_naming_series`)
    availableSeries.value = series || []
    if (series.length && !entrySeries.value) entrySeries.value = series[0]

    const whs = await frappeGet('frappe.client.get_list', {
      doctype: 'Warehouse',
      filters: { is_group: 0, disabled: 0 },
      fields: ['name'],
      limit: 1000
    })
    availableWarehouses.value = whs.map(w => w.name)
    
    // Auto-select first two distinct warehouses if available and not set
    if (!fromWarehouse.value && !toWarehouse.value && availableWarehouses.value.length >= 2) {
      fromWarehouse.value = availableWarehouses.value[0]
      toWarehouse.value = availableWarehouses.value[1]
    }

    const purposes = await frappeGet(`${API}.get_stock_entry_purposes`)
    if (purposes && purposes.length) {
      availablePurposes.value = purposes
    }
  } catch (e) {
    console.error('Failed to fetch config', e)
  }
}

async function lookupItem(code) {
  try {
    return await frappeGet(`${API}.get_item_details`, { item_code: code, warehouse: fromWarehouse.value })
  } catch (e) { return null }
}

watch(newItemCode, async (val) => {
  const code = val.trim()
  if (code.length < 2) { newPending.value = { item_name: '', uom: '', rate: 0 }; return }
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.valuation_rate }
  }
})

watch(selectedRow, async (idx) => {
  if (idx >= 0 && items.value[idx]) {
    const item = items.value[idx]
    try {
      const res = await frappeGet(`${API}.get_item_details`, { item_code: item.item_code })
      const stock = await frappeGet('frappe.client.get_list', {
        doctype: 'Bin',
        filters: { item_code: item.item_code, warehouse: ['in', [fromWarehouse.value, toWarehouse.value]] },
        fields: ['warehouse', 'actual_qty']
      })
      selectedItemData.value = { 
        ...res, 
        stock: stock.map(s => ({ warehouse: s.warehouse, qty: s.actual_qty })) 
      }
    } catch (e) {}
  } else {
    selectedItemData.value = null
  }
})

const stockAtSource = computed(() => {
  if (!selectedItemData.value) return 0
  return selectedItemData.value.stock?.find(s => s.warehouse === fromWarehouse.value)?.qty || 0
})

const stockAtTarget = computed(() => {
  if (!selectedItemData.value) return 0
  return selectedItemData.value.stock?.find(s => s.warehouse === toWarehouse.value)?.qty || 0
})

// ==================== ITEM ACTIONS ====================
async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    const row = items.value[idx]
    row.item_name = r.item_name; row.uom = r.uom; row.rate = r.valuation_rate; row.deleted = false
    focusField('qty', idx)
  } else {
    openSearch(idx)
  }
}

async function onNewCodeEnter() {
  const code = newItemCode.value.trim(); if (!code) return
  const r = await lookupItem(code)
  if (r && r.found) {
    newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.valuation_rate }
    focusNewQty()
  } else {
    openSearch()
  }
}

function addNewItem() {
  if (!newItemCode.value || !newPending.value.item_name) return
  
  const existing = items.value.find(i => i.item_code === newItemCode.value && !i.deleted)
  if (existing) {
    existing.qty += newQty.value
  } else {
    items.value.push({
      item_code: newItemCode.value,
      item_name: newPending.value.item_name,
      uom: newPending.value.uom,
      qty: newQty.value,
      rate: newPending.value.rate,
      deleted: false
    })
  }
  
  newItemCode.value = ''
  newQty.value = 1
  newPending.value = { item_name: '', uom: '', rate: 0 }
  focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== SEARCH ====================
function openSearch(idx = null) {
  selectedRow.value = idx === null ? -1 : idx
  showItemSearchModal.value = true
  nextTick(() => itemSearchModalRef.value?.focus())
}

function pickItem(item) {
  showItemSearchModal.value = false
  if (selectedRow.value === -1) {
    newItemCode.value = item.item_code
    newPending.value = { item_name: item.item_name, uom: item.uom, rate: item.valuation_rate }
    nextTick(focusNewQty)
  } else {
    const row = items.value[selectedRow.value]
    row.item_code = item.item_code; row.item_name = item.item_name; row.uom = item.uom; row.rate = item.valuation_rate
    focusField('qty', selectedRow.value)
  }
}

// ==================== SAVE / LOAD ====================
async function saveEntry() {
  if (purpose.value !== 'Material Receipt' && !fromWarehouse.value) { alert('Select From warehouse'); return }
  if (purpose.value !== 'Material Issue' && !toWarehouse.value) { alert('Select To warehouse'); return }
  if (purpose.value === 'Material Transfer' && fromWarehouse.value === toWarehouse.value) { alert('Source and Target warehouses cannot be same'); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    name: entryName.value,
    date: entryDate.value,
    naming_series: entrySeries.value,
    purpose: purpose.value,
    from_warehouse: (purpose.value !== 'Material Receipt') ? fromWarehouse.value : '',
    to_warehouse: (purpose.value !== 'Material Issue') ? toWarehouse.value : '',
    items: activeItems.value.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      uom: i.uom,
      rate: i.rate
    }))
  }

  try {
    const method = entryName.value ? 'update_stock_entry' : 'create_stock_entry'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    entryName.value = res.name
    alert(`Entry ${res.name} saved as Draft`)
    fetchSidebarEntries()
    // Optionally stay on the page to allow submission
  } catch (e) {
    alert(e.message || 'Save failed')
  }
}

async function submitEntry() {
  if (!entryName.value) return
  if (!confirm('Are you sure you want to SUBMIT this entry? This will update stock levels and cannot be undone.')) return

  try {
    await frappePost(`${API}.submit_stock_entry`, { name: entryName.value })
    alert(`Entry ${entryName.value} submitted successfully`)
    fetchSidebarEntries()
    startNewEntry()
  } catch (e) {
    alert(e.message || 'Submission failed')
  }
}

function startNewEntry() {
  items.value = []; entryName.value = null; entryDocStatus.value = 0
  newItemCode.value = ''; newQty.value = 1; selectedRow.value = -1
  selectedItemData.value = null
  fetchSidebarEntries()
  nextTick(() => openSeriesModal())
}

// ==================== SIDEBAR (MODIFY) ====================
const sidebarEntries = ref([])
const sidebarLoading = ref(false)
const sidebarDate = ref(new Date().toISOString().split('T')[0])
const sidebarSearch = ref('')
const sidebarPurpose = ref('')
const showIncentiveModal = ref(false)

function changeSidebarDate(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

async function fetchSidebarEntries() {
  sidebarLoading.value = true
  try {
    sidebarEntries.value = await frappeGet(`${API}.get_stock_entries`, {
      posting_date: sidebarDate.value,
      query: sidebarSearch.value,
      purpose: sidebarPurpose.value || null
    })
  } catch (e) {
    console.error('Sidebar fetch failed', e)
  }
  sidebarLoading.value = false
}

watch([sidebarDate, sidebarPurpose], () => fetchSidebarEntries())

let searchTimeout = null
watch(sidebarSearch, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(fetchSidebarEntries, 300)
})

async function loadEntry(name) {
  try {
    const data = await frappeGet(`${API}.get_stock_entry`, { name })
    entryName.value = data.name
    entryDate.value = data.posting_date
    entrySeries.value = data.naming_series
    purpose.value = data.purpose || 'Material Transfer'
    fromWarehouse.value = data.from_warehouse
    toWarehouse.value = data.to_warehouse
    items.value = data.items
    entryDocStatus.value = data.docstatus
    nextTick(focusNewCode)
  } catch (e) { alert('Load failed') }
}

// ==================== SHORTCUTS ====================
function handleBack() {
  if (items.value.length && !entryName.value) {
    if (!confirm('Discard unsaved entry?')) return
  }
  router.push('/')
}

function handleSeriesNumberKey(e) {
  if (!showSeriesDropdown.value) return
  const len = availableSeries.value.length
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    seriesHighlightIdx.value = (seriesHighlightIdx.value + 1) % len
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    seriesHighlightIdx.value = (seriesHighlightIdx.value - 1 + len) % len
  } else if (e.key === 'Enter') {
    e.preventDefault()
    selectSeries(availableSeries.value[seriesHighlightIdx.value])
  } else if (e.key === 'Escape') {
    e.preventDefault()
    showSeriesDropdown.value = false
  } else {
    const n = parseInt(e.key)
    if (!isNaN(n) && n >= 1 && n <= len) {
      e.preventDefault()
      selectSeries(availableSeries.value[n - 1])
    }
  }
}

// Block page shortcuts while any inline subwindow is open
useSubwindowWatcher(showSeriesDropdown)

useShortcuts(materialTransferShortcuts({
  save: saveEntry,
  searchItem: () => openSearch(),
  deleteRow: () => { if (selectedRow.value >= 0) softDelete(selectedRow.value) },
  focusSeries: () => openSeriesModal(),
  openIncentive: () => { if (entryName.value) showIncentiveModal.value = true },
  contextualBack: () => {
    if (showItemSearchModal.value) { showItemSearchModal.value = false; return }
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

onMounted(() => {
  window.addEventListener('keydown', handleSeriesNumberKey)
  fetchAllowedSeries('Stock Entry')
  fetchConfig()
  fetchSidebarEntries()
  if (props.name) loadEntry(props.name)
  else nextTick(() => openSeriesModal())
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleSeriesNumberKey)
})
</script>
