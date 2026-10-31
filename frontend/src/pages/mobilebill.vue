<template>
  <div class="fixed inset-x-0 top-0 flex h-[100dvh] flex-col bg-[var(--color-bg)] text-[var(--color-text)]" :style="viewportStyle">
    <!-- Header: bill no · series · customer · item search + camera scan -->
    <header class="z-20 shrink-0 space-y-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] shadow-sm">
      <div class="flex items-center gap-2">
        <button type="button" aria-label="Back to dashboard" class="rounded-lg px-2 py-1 text-lg" @click="router.push('/')">←</button>
        <div class="min-w-0 flex-1">
          <h1 class="truncate text-base font-bold leading-tight">
            {{ invoiceName || 'New Bill' }}
            <span v-if="isSubmitted" class="ml-1 rounded bg-[var(--color-success)]/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--color-success)]">Submitted</span>
            <span v-else-if="invoiceName" class="ml-1 rounded bg-[var(--color-warning)]/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--color-warning)]">Draft</span>
            <span v-if="isReturn" class="ml-1 rounded bg-[var(--color-danger)]/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--color-danger)]">Return</span>
          </h1>
          <div class="truncate text-[11px] text-[var(--color-text-muted)]">{{ priceList || 'No price list' }} · {{ warehouse || 'No warehouse' }}</div>
        </div>
        <select
          v-model="selectedSeries"
          :disabled="!!invoiceName"
          aria-label="Series"
          class="w-2/5 shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-2 text-[1.09375rem] outline-none disabled:opacity-60"
        >
          <option value="" disabled>Series…</option>
          <!-- Shown without the # digit placeholders of the naming series -->
          <option v-for="s in seriesOptions" :key="s" :value="s">{{ s.replace(/#/g, '') }}</option>
        </select>
      </div>

      <div class="flex gap-2">
        <button
          type="button"
          :disabled="isReadOnly"
          class="min-w-0 flex-1 truncate rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-left text-[1.09375rem] font-semibold disabled:opacity-60"
          @click="openCustomerPicker"
        >{{ customerName || 'Select customer' }}</button>
      </div>

      <button
        v-if="isReadOnly && invoiceName && !isSubmitted"
        type="button"
        :disabled="busy"
        class="w-full rounded-xl bg-[var(--color-warning)] py-2.5 text-sm font-bold text-black disabled:opacity-50"
        @click="startModify"
      >Modify this bill</button>

      <!-- Selected item: qty and rate are entered here with the keypad below -->
      <div v-if="pending && !isReadOnly" class="pending-panel rounded-xl p-2">
        <div class="flex items-center gap-2">
          <span class="line-no shrink-0">{{ pendingLineNo }}</span>
          <MarqueeText manual :text="pending.item_name" class="min-w-0 flex-1 text-[1.3125rem] font-bold leading-tight" />
          <!-- Multi-UOM item: pick the unit the qty is entered in; the rate follows the price list for that unit -->
          <select
            v-if="pendingUoms.length > 1"
            v-model="pending.uom"
            :aria-label="`Unit of ${pending.item_name}`"
            class="shrink-0 rounded-lg border-2 border-[var(--color-info)] bg-[var(--color-bg)] px-1.5 py-1 text-sm font-bold uppercase text-[var(--color-text)] outline-none"
            @change="onPendingUomChange"
          >
            <option v-for="u in pendingUoms" :key="u" :value="u">{{ uomLabel(pending.item_code, u) }}</option>
          </select>
          <span v-else class="shrink-0 rounded bg-[var(--color-bg)] px-1.5 py-0.5 text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ pending.uom }}</span>
          <span v-if="pending.target !== 'new'" class="shrink-0 rounded bg-[var(--color-warning)]/15 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[var(--color-warning)]">Edit</span>
          <button
            v-if="itemHasBatch(pending.item_code)"
            type="button"
            :aria-label="`Batch of ${pending.item_name}`"
            class="shrink-0 rounded px-1.5 py-0.5 font-mono text-xs font-bold"
            :class="pending.batch_no ? 'bg-[var(--color-info)]/15 text-[var(--color-info)]' : 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'"
            @click="openBatchPicker"
          >{{ pending.batch_no || 'Batch: Auto' }}</button>
          <button type="button" aria-label="Cancel item" class="shrink-0 rounded-lg px-2 text-lg leading-none text-[var(--color-text-muted)]" @click="cancelPending">&times;</button>
        </div>
        <!-- Qty · rate · disc at 1.25× size; the amount wraps below when the row runs out of room -->
        <!-- Field names are headings above the boxes; the boxes hold only the values -->
        <div class="mt-1.5 flex flex-wrap items-end gap-1.5">
          <div v-for="f in PENDING_FIELDS" :key="f.key">
            <div class="whitespace-nowrap px-0.5 text-[12.5px] font-bold uppercase text-[var(--color-text-muted)]">{{ f.label }}</div>
            <button
              type="button"
              class="w-full rounded-lg border-2 px-2 py-1 text-left"
              :class="pending.field === f.key ? 'edit-focus' : 'border-[var(--color-border)] bg-[var(--color-bg)]'"
              @click="focusPendingField(f.key)"
            >
              <!-- Sized to f.chars characters, growing when a longer value is typed -->
              <div class="font-mono text-[1.25rem] font-bold tabular-nums" :style="{ minWidth: `${f.chars}ch` }">{{ pending[f.key] || '0' }}</div>
            </button>
          </div>
          <span class="ml-auto pb-1.5 font-mono text-[1.25rem] font-bold tabular-nums">{{ money(pendingAmount) }}</span>
        </div>
      </div>
    </header>

    <main class="relative min-h-0 flex-1 overflow-y-auto">
      <div v-if="loadingBill" class="py-16 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading bill…</div>
      <div v-else-if="!activeRows.length" class="px-6 py-16 text-center text-sm text-[var(--color-text-muted)]">
        <template v-if="!selectedSeries">Pick a series to start.</template>
        <template v-else>Tap Scan to add an item.</template>
      </div>

      <ul v-else class="space-y-2 px-2 py-2" :style="lineColumns">
        <li v-for="(row, idx) in activeRows" :key="row._rowKey ?? `free-${row._free_parent_key}-${row.item_code}`" class="bill-line px-3 py-2.5 transition-[background-color,opacity]" :class="[isEditing(row) ? 'row-editing' : row._is_free ? 'bill-line--free' : '', keypadVisible && !isEditing(row) ? 'row-dimmed' : '']" @click="selectRow(row)">
          <div class="flex items-start gap-2">
            <span class="line-no mt-0.5 shrink-0">{{ idx + 1 }}</span>
            <div class="min-w-0 flex-1">
              <MarqueeText manual :text="row.item_name || row.item_code" :class="isEditing(row) ? 'text-[1.875rem] font-bold leading-tight' : 'text-[1.25rem] font-semibold'" />
              <!-- Code · qty · rate · amount on one line (1.25× size); tap qty / rate to edit on the keypad.
                   Qty, rate and amount are sized to the bill's longest value (lineColumns) so they line up on every row. -->
              <div class="mt-0.5 flex items-center gap-1.5 text-[0.9375rem] text-[var(--color-text-muted)]">
                <span class="min-w-0 flex-1 truncate font-mono">{{ row.item_code }}<template v-if="row.batch_no"> · <b class="text-[var(--color-info)]">{{ row.batch_no }}</b></template><template v-if="row._is_free"> · <b class="text-[var(--color-success)]">FREE</b></template><template v-else-if="row.discount"> · <b class="text-[var(--color-warning)]">{{ row.discount }}% off</b></template></span>
                <button
                  type="button"
                  :disabled="isReadOnly || row._is_free"
                  :aria-label="`Quantity of ${row.item_name}`"
                  class="shrink-0 rounded-lg border px-1.5 py-1 font-mono text-[1.09375rem] font-bold tabular-nums text-[var(--color-text)] disabled:opacity-100"
                  :class="isEditing(row) && pending.field === 'qty' ? 'edit-focus' : 'line-box'"
                  @click.stop="editRow(row, 'qty')"
                ><span class="inline-block text-right" :style="{ minWidth: 'var(--qty-ch)' }">{{ fmtQty(row.qty) }}</span> <span class="inline-block text-left text-[12.5px] font-normal" :style="{ minWidth: 'var(--uom-ch)' }">{{ row.uom }}</span></button>
                <span class="shrink-0">×</span>
                <button
                  type="button"
                  :disabled="isReadOnly || row._is_free"
                  :aria-label="`Rate of ${row.item_name}`"
                  class="shrink-0 rounded-lg border px-1.5 py-1 font-mono text-[1.09375rem] tabular-nums text-[var(--color-text)] disabled:opacity-100"
                  :class="isEditing(row) && pending.field === 'rate' ? 'edit-focus' : 'line-box'"
                  @click.stop="editRow(row, 'rate')"
                ><span class="inline-block text-right" :style="{ minWidth: 'var(--rate-ch)' }">{{ row.rate }}</span></button>
                <span class="shrink-0 text-right font-mono text-[1.25rem] font-bold tabular-nums text-[var(--color-text)]" :style="{ minWidth: 'var(--amt-ch)' }">{{ money(rowAmount(row)) }}</span>
              </div>
            </div>
            <button
              v-if="!isReadOnly && !row._is_free"
              type="button"
              aria-label="Remove item"
              class="shrink-0 rounded-lg px-2 py-1 text-lg text-[var(--color-danger)]"
              @click.stop="removeRow(row)"
            >&times;</button>
            <!-- Free lines have no remove button; hold its space so their columns stay in line -->
            <span v-else-if="!isReadOnly" aria-hidden="true" class="invisible shrink-0 px-2 py-1 text-lg">&times;</span>
          </div>
        </li>
      </ul>
    </main>

    <!-- On-screen number pad (no system keyboard) with qty ± and discount buttons for the selected item -->
    <section v-if="keypadVisible" class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 pb-1.5 pt-1">
      <div class="mb-1 flex items-center gap-1.5">
        <div class="flex overflow-hidden rounded-lg border border-[var(--color-border)] text-xs font-bold">
          <button
            v-for="f in PENDING_FIELDS"
            :key="f.key"
            type="button"
            class="px-2.5 py-1.5"
            :class="pending.field === f.key ? 'bg-[var(--color-info)] text-white' : ''"
            @click="focusPendingField(f.key)"
          >{{ f.label }}</button>
        </div>
        <!-- Bill total as it will be once the item being typed is added / updated -->
        <div class="ml-auto min-w-0 truncate text-right">
          <span class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">Bill</span>
          <span class="ml-1 font-mono text-xl font-black tabular-nums">{{ money(billWithPending) }}</span>
        </div>
        <button type="button" class="shrink-0 rounded-lg border border-[var(--color-border)] px-2.5 py-1.5 text-xs font-bold" @click="showKeypad = false">Hide ▾</button>
      </div>

      <div class="mb-1 grid grid-cols-6 gap-1">
        <button
          v-for="d in DISCOUNT_PRESETS"
          :key="d"
          type="button"
          class="keypad-key keypad-key--sm"
          :class="Number(pending.discount) === d ? 'keypad-key--on' : ''"
          @click="setPendingDiscount(d)"
        >{{ d ? `${d}%` : 'No disc' }}</button>
      </div>
      <div class="grid grid-cols-4 gap-1">
        <button v-for="k in ['7', '8', '9']" :key="k" type="button" class="keypad-key" @click="keypadPress(k)">{{ k }}</button>
        <button type="button" aria-label="Backspace" class="keypad-key" @click="keypadPress('back')">⌫</button>
        <button v-for="k in ['4', '5', '6']" :key="k" type="button" class="keypad-key" @click="keypadPress(k)">{{ k }}</button>
        <button type="button" aria-label="Decrease quantity" class="keypad-key text-[var(--color-danger)]" @click="pendingStepQty(-1)">Qty −</button>
        <button v-for="k in ['1', '2', '3']" :key="k" type="button" class="keypad-key" @click="keypadPress(k)">{{ k }}</button>
        <button type="button" aria-label="Increase quantity" class="keypad-key text-[var(--color-success)]" @click="pendingStepQty(1)">Qty +</button>
        <button type="button" class="keypad-key" @click="keypadPress('.')">.</button>
        <button type="button" class="keypad-key" @click="keypadPress('0')">0</button>
        <button type="button" class="keypad-key text-sm" @click="keypadPress('clear')">C</button>
        <button type="button" class="keypad-key keypad-key--ok" @click="keypadAdd">{{ pending.target !== 'new' ? 'OK' : 'Add & Scan' }}</button>
      </div>
    </section>

    <!-- Totals + save (one compact row while the keyboard is open) -->
    <footer
      class="shrink-0 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-3 shadow-[0_-2px_8px_rgba(0,0,0,0.06)]"
      :class="keypadVisible ? 'flex items-center gap-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5' : 'pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2.5'"
    >
      <div class="flex items-baseline justify-between" :class="keypadVisible ? 'min-w-0 flex-1' : 'mb-2'">
        <span v-if="!keypadVisible" class="text-xs text-[var(--color-text-muted)]">
          {{ activeRows.length }} {{ activeRows.length === 1 ? 'item' : 'items' }} · Qty {{ fmtQty(totalQty) }}
          <template v-if="taxTemplate && !isInclusive"> · tax extra</template>
        </span>
        <span class="font-mono font-black tabular-nums" :class="keypadVisible ? 'truncate text-lg' : 'text-2xl'">{{ money(isReadOnly && loadedTotal != null ? loadedTotal : subTotal) }}</span>
      </div>
      <div class="flex gap-1.5" :class="keypadVisible ? 'shrink-0' : ''">
        <button
          v-if="!isReadOnly"
          type="button"
          aria-label="Scan or search item"
          class="flex items-center gap-1 rounded-xl bg-[var(--color-info)] px-2 text-xs font-bold text-white shadow-sm active:scale-95"
          @click="openScanner"
        ><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8"/><path d="M11 8v8"/><path d="M15 8v8"/><path d="M18 8v8"/></svg>Scan</button>
        <button type="button" class="rounded-xl border border-[var(--color-border)] px-2 text-xs font-bold" @click="openPastBills">{{ keypadVisible ? 'Past' : 'Past Bills' }}</button>
        <button type="button" class="rounded-xl border border-[var(--color-border)] px-2 text-xs font-bold" @click="newBill()">New</button>
        <button
          v-if="!isReadOnly"
          type="button"
          :disabled="busy || (!activeRows.length && pending?.target !== 'new')"
          class="rounded-xl bg-[var(--color-success)] font-bold text-white shadow active:scale-[0.98] disabled:opacity-50"
          :class="keypadVisible ? 'px-3 py-2 text-sm' : 'flex-1 py-3 text-base'"
          @click="saveBill"
        >{{ busy ? 'Saving…' : pending?.target === 'new' ? 'Add & Save' : invoiceName ? 'Update' : 'Save' }}<template v-if="!keypadVisible"> Bill</template></button>
        <button
          v-else-if="invoiceName"
          type="button"
          class="flex-1 rounded-xl bg-[var(--color-info)] py-3 text-base font-bold text-white shadow"
          @click="showPrintModal = true"
        >Print</button>
      </div>
    </footer>

    <BarcodeScanner v-if="showScanner" :search="scannerSearch" @detected="onScanned" @close="closeScanner" />

    <!-- Customer picker -->
    <div v-if="showCustomerPicker" class="fixed inset-0 z-40 flex flex-col bg-[var(--color-bg)]">
      <div class="flex shrink-0 items-center gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <input
          ref="customerSearchRef"
          v-model="customerQuery"
          type="search"
          inputmode="none"
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="Customer name, code or mobile"
          class="hl-input min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-base outline-none"
        />
        <button type="button" class="px-2 text-sm font-bold text-[var(--color-info)]" @click="showCustomerPicker = false">Close</button>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto">
        <div v-if="ledgerSyncing && !allLedgers.length" class="py-12 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading customers…</div>
        <div v-else-if="!customerResults.length" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
          {{ customerQuery.trim() ? 'No customers found.' : 'Type to search customers.' }}
        </div>
        <button
          v-for="c in customerResults"
          :key="c.name"
          type="button"
          class="block w-full border-b border-[var(--color-border)] px-4 py-3 text-left active:bg-[var(--color-surface-raised)]"
          @click="pickCustomer(c)"
        >
          <MarqueeText manual :text="c.label || c.name" class="text-[1.25rem] font-semibold" />
          <div class="truncate text-xs text-[var(--color-text-muted)]">{{ c.name }}<template v-if="c.mobile_no"> · {{ c.mobile_no }}</template></div>
        </button>
      </div>
      <!-- On-screen keyboard instead of the phone's, so it never covers the list -->
      <MobileSearchKeyboard
        class="shrink-0"
        @key="k => { customerQuery += k }"
        @backspace="customerQuery = customerQuery.slice(0, -1)"
        @clear="customerQuery = ''"
        @enter="pickOnlyCustomer"
      />
    </div>

    <!-- Past bills -->
    <div v-if="showPastBills" class="fixed inset-0 z-40 flex flex-col bg-[var(--color-bg)]">
      <div class="shrink-0 space-y-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <div class="flex items-center justify-between">
          <h2 class="text-base font-bold">Past Bills</h2>
          <button type="button" class="px-2 text-sm font-bold text-[var(--color-info)]" @click="showPastBills = false">Close</button>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" aria-label="Previous day" :disabled="!!pastQuery.trim()" class="rounded-lg border border-[var(--color-border)] px-3 py-2 disabled:opacity-40" @click="shiftPastDate(-1)">‹</button>
          <input v-model="pastDate" type="date" :disabled="!!pastQuery.trim()" class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-2 text-sm disabled:opacity-40" />
          <button type="button" aria-label="Next day" :disabled="!!pastQuery.trim()" class="rounded-lg border border-[var(--color-border)] px-3 py-2 disabled:opacity-40" @click="shiftPastDate(1)">›</button>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="pastQuery"
            type="search"
            autocomplete="off"
            placeholder="Search bill no or customer (all dates)"
            class="hl-input min-w-0 flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2.5 text-sm outline-none"
          />
          <label class="flex shrink-0 items-center gap-1 text-xs font-semibold">
            <input v-model="pastDraftOnly" type="checkbox" class="h-4 w-4" /> Drafts
          </label>
        </div>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto">
        <div v-if="pastLoading" class="py-12 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading bills…</div>
        <div v-else-if="!pastBills.length" class="py-12 text-center text-sm text-[var(--color-text-muted)]">No bills found.</div>
        <button
          v-for="b in pastBills"
          :key="b.name"
          type="button"
          class="flex w-full items-center gap-3 border-b border-[var(--color-border)] px-4 py-3 text-left active:bg-[var(--color-surface-raised)]"
          @click="openPastBill(b.name)"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="font-mono text-sm font-bold">{{ b.name }}</span>
              <span
                class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                :class="b.docstatus === 1 ? 'bg-[var(--color-success)]/15 text-[var(--color-success)]' : 'bg-[var(--color-warning)]/15 text-[var(--color-warning)]'"
              >{{ b.docstatus === 1 ? 'Submitted' : 'Draft' }}</span>
            </div>
            <MarqueeText manual :text="b.custom_customer_name || b.customer_name || b.customer" class="text-[1.09375rem]" />
            <div class="text-[11px] text-[var(--color-text-muted)]">{{ formatDMY(parseCalendarDate(b.posting_date), '') }} · {{ b.mop || '—' }}</div>
          </div>
          <div class="shrink-0 font-mono text-base font-bold tabular-nums">{{ money(b.rounded_total) }}</div>
        </button>
      </div>
    </div>

    <!-- Batch picker for the selected item: sales take stock from a batch held in the warehouse -->
    <div v-if="showBatchPicker && pending" class="fixed inset-0 z-40 flex flex-col bg-[var(--color-bg)]">
      <div class="flex shrink-0 items-center gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]">
        <div class="min-w-0 flex-1">
          <h2 class="text-base font-bold">Select Batch</h2>
          <MarqueeText manual :text="pending.item_name" class="text-xs text-[var(--color-text-muted)]" />
        </div>
        <button type="button" class="px-2 text-sm font-bold text-[var(--color-info)]" @click="showBatchPicker = false">Close</button>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto">
        <button
          v-if="!isReturn"
          type="button"
          class="block w-full border-b border-[var(--color-border)] px-4 py-3 text-left active:bg-[var(--color-surface-raised)]"
          :class="!pending.batch_no ? 'bg-[var(--color-info)]/10' : ''"
          @click="pickBatch('')"
        >
          <div class="text-[1.09375rem] font-semibold">Auto</div>
          <div class="text-xs text-[var(--color-text-muted)]">Oldest stock is picked when the bill is submitted</div>
        </button>
        <div v-if="batchLoading" class="py-12 text-center text-sm text-[var(--color-text-muted)] animate-pulse">Loading batches…</div>
        <div v-else-if="batchError" class="py-12 text-center text-sm text-[var(--color-danger)]">{{ batchError }}</div>
        <div v-else-if="!batchOptions.length" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
          {{ isReturn ? 'No batches for this item.' : 'No batch has stock in this warehouse.' }}
        </div>
        <button
          v-for="b in batchOptions"
          :key="b.batch_no"
          type="button"
          class="flex w-full items-center gap-3 border-b border-[var(--color-border)] px-4 py-3 text-left active:bg-[var(--color-surface-raised)]"
          :class="pending.batch_no === b.batch_no ? 'bg-[var(--color-info)]/10' : ''"
          @click="pickBatch(b.batch_no)"
        >
          <div class="min-w-0 flex-1">
            <div class="font-mono text-[1.09375rem] font-bold">{{ b.batch_no }}</div>
            <div class="text-[11px]" :class="b.expired ? 'font-bold text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]'">
              <template v-if="b.expiry_date">Exp {{ formatDMY(b.expiry_date, '') }}{{ b.expired ? ' (expired)' : '' }}</template>
              <template v-else-if="b.manufacturing_date">Mfg {{ formatDMY(b.manufacturing_date, '') }}</template>
            </div>
          </div>
          <div class="shrink-0 font-mono text-base font-bold tabular-nums">{{ fmtQty(b.qty) }}</div>
        </button>
      </div>
    </div>

    <PrintOptionsModal
      v-if="showPrintModal && invoiceName"
      :invoice-name="invoiceName"
      :series="selectedSeries"
      doctype="Sales Invoice"
      :initial-template="printTemplate"
      @close="closePrintModal"
    />

    <div v-if="toast" role="status" class="fixed left-1/2 top-20 z-50 -translate-x-1/2 rounded-xl bg-slate-900/90 px-4 py-2 text-sm font-semibold text-white shadow-lg">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { frappeGet, frappePost } from '../api'
import BarcodeScanner from '../components/BarcodeScanner.vue'
import MarqueeText from '../components/MarqueeText.vue'
import MobileSearchKeyboard from '../components/MobileSearchKeyboard.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import { useItemCache, lookupItemInCache, refreshItemCache, refreshDiscountRuleCache, itemHasBatch, uomLabel } from '../services/itemCache.js'
import { useLedgerCache, ledgerCacheReady } from '../services/ledgerCache.js'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import { useDiscountRules } from '../composables/useDiscountRules.js'
import { getFloatPrecision } from '../encryption.js'
import { formatDMY } from '../utils/date'
import { serverToday, toLocalISO, parseCalendarDate } from '../services/serverTime'

const router = useRouter()
const precision = getFloatPrecision()
const SERIES_KEY = 'mb-series'

// ── Current user's billing settings (cached at login / dashboard load) ──────
function readSettings() {
  try { return JSON.parse(localStorage.getItem('wb-settings-v2') || 'null')?.data || {} } catch { return {} }
}
const settings = readSettings()
const userDefaults = settings.user_defaults || {}
const company = localStorage.getItem('wb-company') || userDefaults.company || ''

const { allowedSeries: seriesOptions, fetchAllowedSeries } = useAllowedSeries()
const selectedSeries = ref('')
const priceList = ref('')
const taxTemplate = ref('')
const isInclusive = ref(false)
const isReturn = ref(false)
const printTemplate = ref('')
const warehouse = ref(userDefaults.warehouse || localStorage.getItem('wb-warehouse') || '')
const costCenter = ref(userDefaults.cost_center || localStorage.getItem('wb-cost-center') || '')
const incomeAccount = ref(userDefaults.income_account || localStorage.getItem('wb-income-account') || '')

// Same rules as SalesInvoice.handleSeriesSelected: the series row decides price list,
// tax and return; the user's row decides warehouse, cost center and income account.
function applySeriesDefaults(series) {
  const entry = (settings.billing_series || []).find(bs => bs.series === series)
  priceList.value = entry?.price_list || 'Standard Selling'
  taxTemplate.value = entry?.tax_template || ''
  isInclusive.value = !!entry?.tax_type_incl
  isReturn.value = !!entry?.is_return
  printTemplate.value = entry?.print_format || ''
}

watch(selectedSeries, (series) => {
  if (!series) return
  try { localStorage.setItem(SERIES_KEY, series) } catch { /* storage blocked */ }
  if (invoiceName.value) return // a loaded bill keeps its own saved settings
  applySeriesDefaults(series)
})

// Load the item dataset for the price list in use, then re-rate lines being edited
watch(priceList, (pl) => {
  if (!pl) return
  refreshItemCache('Sales', pl, warehouse.value)
    .then(() => { if (!isReadOnly.value) repriceRows() })
    .catch(e => console.warn('[MobileBill] item cache refresh failed:', e))
})

// ── Bill state ───────────────────────────────────────────────────────────────
const rows = ref([])
const invoiceName = ref('')
const docstatus = ref(0)
const loadedTotal = ref(null)
const isReadOnly = ref(false)
const customerId = ref('')
const customerName = ref('')
const customerAddress = ref('')
const customerState = ref('')
const customerModifier = ref(null)
const ignoreModifier = ref(false)
const customerPricing = ref({})
const mop = ref('Cash')
const busy = ref(false)
const loadingBill = ref(false)
const showPrintModal = ref(false)
const toast = ref('')

const isSubmitted = computed(() => docstatus.value === 1)
const activeRows = computed(() => rows.value.filter(r => !r.deleted))

// Rules stay frozen while a saved bill is only being viewed, so it shows what was billed
const { makeRowKey, reapplyAllDiscountRules } = useDiscountRules({ items: rows, priceList, lookupItemInCache, pauseRules: isReadOnly })

const round = v => parseFloat((Number(v) || 0).toFixed(precision))
const netRate = row => round((row.rate || 0) * (1 - (Number(row.discount) || 0) / 100))
const rowAmount = row => round((Number(row.qty) || 0) * netRate(row))
const subTotal = computed(() => round(activeRows.value.reduce((s, r) => s + rowAmount(r), 0)))
const totalQty = computed(() => activeRows.value.reduce((s, r) => s + (Number(r.qty) || 0), 0))

function money(v) {
  return (Number(v) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtQty(n) {
  const v = Number(n) || 0
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

// Same qty / uom / rate / amount widths on every bill line: longest value in ch (all monospace),
// each read against its own element's font size, so the columns line up down the list
const lineColumns = computed(() => {
  const longest = f => `${Math.max(1, ...activeRows.value.map(r => String(f(r)).length))}ch`
  return {
    '--qty-ch': longest(r => fmtQty(r.qty)),
    '--uom-ch': longest(r => r.uom || ''),
    '--rate-ch': longest(r => r.rate ?? ''),
    '--amt-ch': longest(r => money(rowAmount(r))),
  }
})

let toastTimer = null
function flash(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

// ── Pricing (price list rate × customer modifier × customer item pricing) ────
function baseRateFor(cached, uom) {
  if (!cached) return 0
  const pl = priceList.value
  const targetUom = uom || cached.uom || 'Nos'
  if (cached.uom_price_lists?.[pl]?.[targetUom] != null) return cached.uom_price_lists[pl][targetUom]
  const entry = (cached.price_lists || []).find(p => p.name === pl)
  if (entry) return entry.rate
  return parseFloat(cached.price || 0)
}

function combinedFactor(itemCode) {
  let mod = (!ignoreModifier.value && customerModifier.value != null) ? customerModifier.value : 1
  if (mod === 0) mod = 1
  let cp = customerPricing.value[itemCode]
  if (cp === 0) cp = 1
  const factor = cp != null ? mod * cp : mod
  return factor === 0 ? 1 : factor
}

function rateFor(cached, uom) {
  return round(baseRateFor(cached, uom) * combinedFactor(cached.item_code))
}

function repriceRows() {
  if (isReturn.value) return
  for (const row of rows.value) {
    if (row.deleted || row._is_free || row._rate_overridden) continue
    const cached = lookupItemInCache(row.item_code)
    if (!cached) continue
    row._base_rate = baseRateFor(cached, row.uom)
    row.rate = round(row._base_rate * combinedFactor(row.item_code))
  }
}

// ── Item entry ───────────────────────────────────────────────────────────────
const { searchItemsInCache } = useItemCache()
const showScanner = ref(false)

function canEdit() {
  if (isReadOnly.value) return false
  if (!selectedSeries.value) { alert('Please select a series first.'); return false }
  return true
}

// ── On-screen keyboard + selected item entry ─────────────────────────────────
// Items are found only on the scanner screen (camera or typed search there). A picked item is
// staged in `pending` and its qty / rate / discount typed on the number pad; Add moves it into
// the bill. `pending.target` is 'new' for a picked item, or the bill row being re-edited.
const PENDING_FIELDS = [
  { key: 'qty', label: 'Qty', chars: 3 },
  { key: 'rate', label: 'Rate', chars: 6 },
  { key: 'discount', label: 'Disc %', chars: 3 },
]
const DISCOUNT_PRESETS = [0, 5, 10, 15, 20, 25]

const pending = ref(null)
// Hide closes the pad until a field is tapped again
const showKeypad = ref(true)
const keypadVisible = computed(() =>
  showKeypad.value && !!pending.value && !isReadOnly.value &&
  !showScanner.value && !showCustomerPicker.value && !showPastBills.value && !showPrintModal.value && !showBatchPicker.value)
// Bill line number of the staged item: its own line when re-editing, else the next line
const pendingLineNo = computed(() => {
  const p = pending.value
  if (!p) return 0
  return p.target === 'new' ? activeRows.value.length + 1 : activeRows.value.indexOf(p.target) + 1
})
const pendingAmount = computed(() => {
  const p = pending.value
  if (!p) return 0
  const disc = Math.min(100, parseFloat(p.discount) || 0)
  return round((parseFloat(p.qty) || 0) * (parseFloat(p.rate) || 0) * (1 - disc / 100))
})

// Bill total counting the staged item: a new item adds its amount, a re-edited line
// replaces its saved amount with the one being typed
const billWithPending = computed(() => {
  const p = pending.value
  if (!p) return subTotal.value
  const current = p.target === 'new' ? 0 : rowAmount(p.target)
  return round(subTotal.value - current + pendingAmount.value)
})

// UOMs the staged item can be sold in (stock UOM + its conversion rows)
const pendingUoms = computed(() => {
  const p = pending.value
  if (!p) return []
  const cached = lookupItemInCache(p.item_code)
  const list = (cached?.uoms || []).map(u => u.uom).filter(Boolean)
  if (cached?.uom && !list.includes(cached.uom)) list.unshift(cached.uom)
  if (p.uom && !list.includes(p.uom)) list.push(p.uom)
  return list
})

// A new unit takes that unit's price list rate; a rate typed earlier is replaced
function onPendingUomChange() {
  const p = pending.value
  const cached = p && lookupItemInCache(p.item_code)
  if (!cached) return
  const base = baseRateFor(cached, p.uom)
  const rate = round(base * combinedFactor(p.item_code))
  p.baseRate = base
  p.computedRate = rate
  p.rate = String(rate)
  p.field = 'qty'
  p.fresh = true
}

function openPending(entry) {
  // Keep the system keyboard closed so the keypad is not covered
  document.activeElement?.blur?.()
  pending.value = { fresh: true, ...entry }
  showKeypad.value = true
}

function addItem(cached, uom = null) {
  if (!canEdit()) return
  const rowUom = uom || cached.uom || 'Nos'
  // Every pick is its own bill line, even when the same item is entered again
  if (pending.value) commitPending()
  const base = baseRateFor(cached, rowUom)
  const rate = round(base * combinedFactor(cached.item_code))
  openPending({
    target: 'new',
    item_code: cached.item_code,
    item_name: cached.item_name || cached.item_code,
    uom: rowUom,
    qty: '1',
    rate: String(rate),
    discount: '0',
    computedRate: rate,
    baseRate: base,
    tax_rate: cached.tax_rate || 0,
    batch_no: '',
    field: 'qty',
  })
  if (itemHasBatch(cached.item_code)) openBatchPicker()
}

// ── Batch ───────────────────────────────────────────────────────────────────
const showBatchPicker = ref(false)
const batchOptions = ref([])
const batchLoading = ref(false)
const batchError = ref('')
let batchRequest = 0

// Batches of the staged item; a return lists every batch, a sale only those with stock here
async function openBatchPicker() {
  const p = pending.value
  if (!p) return
  showBatchPicker.value = true
  const request = ++batchRequest
  batchLoading.value = true
  batchError.value = ''
  batchOptions.value = []
  try {
    const res = await frappeGet('ssplbilling.api.batch_api.get_item_batches', { item_code: p.item_code, warehouse: warehouse.value || '' })
    if (request !== batchRequest) return
    const list = res?.batches || []
    batchOptions.value = isReturn.value ? list : list.filter(b => b.qty > 0)
  } catch (e) {
    if (request === batchRequest) batchError.value = e.message || 'Failed to load batches'
  } finally {
    if (request === batchRequest) batchLoading.value = false
  }
}

function pickBatch(batchNo) {
  if (pending.value) pending.value.batch_no = batchNo
  showBatchPicker.value = false
}

// A return brings stock back in, which needs a named batch unless the item creates batches itself
function batchRequired(itemCode) {
  const cached = lookupItemInCache(itemCode)
  return !!Number(cached?.has_batch_no) && !Number(cached?.create_new_batch)
}

function editRow(row, field) {
  if (isReadOnly.value || row._is_free) return
  if (pending.value?.target === row) { focusPendingField(field); return }
  if (pending.value) commitPending()
  openPending({
    target: row,
    item_code: row.item_code,
    item_name: row.item_name || row.item_code,
    uom: row.uom,
    // An offer line (10 + 1 free) is edited as its total, the quantity the operator entered
    qty: String(row._total_qty ?? row.qty),
    rate: String(row.rate),
    discount: String(Number(row.discount) || 0),
    batch_no: row.batch_no || '',
    field,
  })
}

// The bill line currently open on the keypad
function isEditing(row) {
  return !!pending.value && pending.value.target === row
}

// Tapping anywhere on a line opens it on the keypad (qty first)
function selectRow(row) {
  if (!isEditing(row)) editRow(row, 'qty')
}

function focusPendingField(field) {
  if (!pending.value) return
  pending.value.field = field
  pending.value.fresh = true
  showKeypad.value = true
}

function keypadPress(key) {
  const p = pending.value
  if (!p) return
  let s = p.fresh && key !== 'back' ? '' : String(p[p.field] ?? '')
  if (key === 'back') s = s.slice(0, -1)
  else if (key === 'clear') s = ''
  else if (key === '.') {
    if (s.includes('.')) return
    s = (s || '0') + '.'
  } else if (s.length < 10) s = s === '0' ? key : s + key
  if (p.field === 'discount' && (parseFloat(s) || 0) > 100) return
  p.fresh = false
  p[p.field] = s
}

function setPendingDiscount(pct) {
  const p = pending.value
  if (!p) return
  p.discount = String(pct)
  p.field = 'discount'
  p.fresh = true
}

function pendingStepQty(delta) {
  const p = pending.value
  if (!p) return
  p.qty = String(Math.max(0, round((parseFloat(p.qty) || 0) + delta)))
  p.field = 'qty'
  p.fresh = true
}

function cancelPending() {
  pending.value = null
  showBatchPicker.value = false
}

function commitPending() {
  const p = pending.value
  if (!p) return
  pending.value = null
  const qty = round(parseFloat(p.qty) || 0)
  const rate = round(parseFloat(p.rate) || 0)
  const discount = round(Math.min(100, Math.max(0, parseFloat(p.discount) || 0)))

  if (p.target !== 'new') {
    const row = p.target
    if (!rows.value.includes(row)) return // removed meanwhile
    if (qty <= 0) { removeRow(row); return }
    // The typed quantity is the total: the offer re-splits it into paid + free right away,
    // also when it equals the old paid quantity (11 → 10 + 1 edited back to 10)
    const qtyChanged = qty !== (row._total_qty ?? row.qty)
    if (qtyChanged) {
      row.qty = qty
      delete row._paid_qty
      delete row._total_qty
      delete row._loaded_free_qty
      delete row._loaded_paid_qty
    }
    const uomChanged = !!p.uom && p.uom !== row.uom
    if (uomChanged) {
      // Unit switched on the keypad: the line carries that unit's price list rate again
      row.uom = p.uom
      row._base_rate = p.baseRate
      row.price_list_rate = p.baseRate
      row.rate = rate
      row._rate_overridden = rate !== p.computedRate
    } else if (rate !== round(row.rate)) {
      row.rate = rate
      row._rate_overridden = true
    }
    if (discount !== round(Number(row.discount) || 0)) {
      row.discount = discount
      row._rule_discount = null // typed by hand, not set by a discount rule
    }
    row.batch_no = p.batch_no || ''
    if (qtyChanged || uomChanged) reapplyAllDiscountRules()
    return
  }

  if (qty <= 0) return
  rows.value.push({
    item_code: p.item_code,
    item_name: p.item_name,
    qty,
    uom: p.uom,
    rate,
    _base_rate: p.baseRate,
    price_list_rate: p.baseRate,
    // A rate typed on the keypad survives repricing
    _rate_overridden: rate !== p.computedRate,
    discount,
    tax_rate: p.tax_rate,
    warehouse: warehouse.value,
    batch_no: p.batch_no || '',
    deleted: false,
    _rowKey: makeRowKey(),
  })
  flash(`Added ${p.item_name}`)
}

// All barcodes of a cached item (comma list + detailed rows)
function itemBarcodes(i) {
  return [
    ...(i.barcodes || '').split(','),
    ...(i.barcodes_detailed || []).map(b => b.barcode || ''),
  ].map(b => b.trim()).filter(Boolean)
}

// Typed-entry matches inside the scanner screen
function scannerSearch(q) {
  return searchItemsInCache(q, 30).map(i => ({
    code: i.item_code,
    name: i.item_name || i.item_code,
    price: rateFor(i, i.uom),
    barcodes: itemBarcodes(i),
  }))
}

function onScanned(code) {
  showScanner.value = false
  addCode(code)
}

// Exact item code / barcode from the camera or a keyboard-wedge scanner
function addCode(code) {
  const match = lookupItemInCache(code)
  if (match) addItem(match, match.uom)
  else flash(`No item for ${code}`)
}

function openScanner() {
  if (canEdit()) showScanner.value = true
}

// Add & Scan: a new item goes into the bill and the camera opens for the next one
function keypadAdd() {
  const wasNew = pending.value?.target === 'new'
  commitPending()
  if (wasNew) openScanner()
}

function closeScanner() {
  showScanner.value = false
}

function removeRow(row) {
  if (pending.value?.target === row) cancelPending()
  const idx = rows.value.indexOf(row)
  if (idx >= 0) rows.value.splice(idx, 1)
}

// ── Customer ─────────────────────────────────────────────────────────────────
const { ledgers: allLedgers, syncLoading: ledgerSyncing, refreshLedgerCache, searchLedgersInCache } = useLedgerCache()
const showCustomerPicker = ref(false)
const customerQuery = ref('')
const customerSearchRef = ref(null)
const customerResults = computed(() => {
  const q = customerQuery.value.trim()
  return q ? searchLedgersInCache(q, 'Customer').slice(0, 30) : []
})

async function openCustomerPicker() {
  if (isReadOnly.value) return
  customerQuery.value = ''
  showCustomerPicker.value = true
  nextTick(() => customerSearchRef.value?.focus())
  await ledgerCacheReady
  if (!allLedgers.value.length) refreshLedgerCache()
}

// Keyboard "Search" key: a single match is picked straight away
function pickOnlyCustomer() {
  if (customerResults.value.length === 1) pickCustomer(customerResults.value[0])
}

async function pickCustomer(c) {
  showCustomerPicker.value = false
  await setCustomer(c.name, c.label || c.name)
  repriceRows()
}

async function setCustomer(id, name) {
  customerId.value = id
  customerName.value = name
  customerModifier.value = null
  customerPricing.value = {}
  customerAddress.value = ''
  customerState.value = ''
  if (!id) return
  const [details, pricing] = await Promise.allSettled([
    frappeGet('ssplbilling.api.salesinvoice_api.get_customer_details', { customer: id }),
    frappeGet('ssplbilling.api.customer_pricing_api.get_customer_pricing', { customer: id }),
  ])
  if (customerId.value !== id) return // picked another customer meanwhile
  if (details.status === 'fulfilled' && details.value) {
    const d = details.value
    customerModifier.value = d.pricelist_multiplication_factor ?? null
    customerAddress.value = d.address_name || ''
    customerState.value = d.state || ''
  }
  if (pricing.status === 'fulfilled') customerPricing.value = pricing.value || {}
}

// ── Edit lock (same Redis lock the desktop Sales screen takes) ──────────────
let tabId = sessionStorage.getItem('wb_tab_id')
if (!tabId) {
  tabId = Math.random().toString(36).substring(2, 15)
  sessionStorage.setItem('wb_tab_id', tabId)
}
const hasLock = ref(false)

async function releaseLock() {
  if (!hasLock.value || !invoiceName.value) return
  try {
    await frappePost('ssplbilling.api.salesinvoice_api.release_bill_edit', { bill_no: invoiceName.value, tab_id: tabId })
  } catch (e) {
    console.error('[MobileBill] release lock failed:', e)
  } finally {
    hasLock.value = false
  }
}

async function startModify() {
  if (!invoiceName.value || isSubmitted.value || busy.value) return
  busy.value = true
  try {
    const res = await frappePost('ssplbilling.api.salesinvoice_api.record_bill_edit', { bill_no: invoiceName.value, tab_id: tabId })
    if (res?.status === 'conflict') {
      alert(res.reason === 'same_user_other_tab'
        ? 'This bill is already being edited by you in another tab.'
        : `This bill is being edited by ${res.user}.`)
      return
    }
    hasLock.value = true
    // Reload so the edit starts from the latest saved version
    await loadBill(invoiceName.value)
    if (isSubmitted.value) {
      await releaseLock()
      alert('Bill is submitted. Modify is denied.')
      return
    }
    isReadOnly.value = false
    // Lines added while modifying take this customer's item pricing, as on the desktop
    if (customerId.value) {
      const id = customerId.value
      frappeGet('ssplbilling.api.customer_pricing_api.get_customer_pricing', { customer: id })
        .then(data => { if (customerId.value === id) customerPricing.value = data || {} })
        .catch(() => {})
    }
  } catch (e) {
    alert(e.message || 'Failed to start editing.')
    if (hasLock.value) await releaseLock()
  } finally {
    busy.value = false
  }
}

// ── Load / new / save ───────────────────────────────────────────────────────
async function loadBill(name) {
  loadingBill.value = true
  try {
    const data = await frappeGet('ssplbilling.api.cashier_api.get_sales_invoice', { invoice_name: name, include_customer_details: 1 })
    cancelPending()
    invoiceName.value = data.name
    docstatus.value = data.docstatus ?? 0
    loadedTotal.value = data.rounded_total ?? data.grand_total ?? null
    selectedSeries.value = data.naming_series || selectedSeries.value
    priceList.value = data.price_list || priceList.value
    taxTemplate.value = data.tax_template || ''
    isInclusive.value = data.is_inclusive === 1
    isReturn.value = data.is_return === 1
    warehouse.value = data.warehouse || warehouse.value
    costCenter.value = data.cost_center || costCenter.value
    incomeAccount.value = data.income_account || incomeAccount.value
    mop.value = data.mop || 'Cash'
    ignoreModifier.value = data.customer_rate_multiplier === 0
    customerId.value = data.customer || ''
    customerName.value = data.customer_name || data.customer || ''
    customerAddress.value = data.customer_address || ''
    customerState.value = data.state || ''
    customerModifier.value = data.customer_billing_details?.pricelist_multiplication_factor ?? null
    customerPricing.value = {}
    _loadedExtras = data
    rows.value = (data.items || []).map(i => {
      const discount = Number(i.discount) || 0
      const effective = i.rate || 0
      const gross = i.gross_rate ?? (discount > 0 && discount < 100 ? round(effective / (1 - discount / 100)) : effective)
      return {
        item_code: i.item_code,
        item_name: i.item_name,
        qty: i.qty,
        uom: i.uom || 'Nos',
        rate: gross,
        _base_rate: i.price_list_rate || gross,
        price_list_rate: i.price_list_rate || gross,
        // Keep billed rates as they are; only newly added lines take today's price
        _rate_overridden: true,
        discount,
        tax_rate: i.tax_rate || 0,
        batch_no: i.batch_no || '',
        deleted: false,
        _is_free: i.is_free_item === 1 || (effective === 0 && discount === 0),
        _rowKey: makeRowKey(),
      }
    })
    isReadOnly.value = true
    return true
  } catch (e) {
    alert(e.message || 'Failed to load bill')
    return false
  } finally {
    loadingBill.value = false
  }
}

// Header fields the mobile screen does not edit, carried over unchanged on update
let _loadedExtras = null

async function newBill(confirmDiscard = true) {
  if (confirmDiscard && !isReadOnly.value && (activeRows.value.length || pending.value) && !confirm('Discard this bill?')) return
  await releaseLock()
  cancelPending()
  invoiceName.value = ''
  docstatus.value = 0
  loadedTotal.value = null
  isReadOnly.value = false
  rows.value = []
  mop.value = 'Cash'
  ignoreModifier.value = false
  _loadedExtras = null
  await setCustomer('', '')
  warehouse.value = userDefaults.warehouse || localStorage.getItem('wb-warehouse') || ''
  costCenter.value = userDefaults.cost_center || localStorage.getItem('wb-cost-center') || ''
  incomeAccount.value = userDefaults.income_account || localStorage.getItem('wb-income-account') || ''
  if (selectedSeries.value) applySeriesDefaults(selectedSeries.value)
}

function chargeRows(extra) {
  // Freight / packing / loading / other charges set on the desktop are kept on update
  if (!extra) return []
  const out = []
  const add = (amount, key, description) => {
    const v = parseFloat(amount) || 0
    const acct = localStorage.getItem(key)
    if (v !== 0 && acct) out.push({ charge_type: 'Actual', account_head: acct, tax_amount: v, description })
  }
  add(extra.freight_amount, 'wb_freight', 'Freight')
  add(extra.loading_amount, 'wb-tax-paid-on-purchase', 'Tax Collected')
  add(extra.packing_amount, 'wb-packing', 'Packing')
  add(extra.other_charges_amount, 'wb-other-charges', 'Other Charges')
  return out
}

async function saveBill() {
  if (busy.value || isReadOnly.value) return
  if (!selectedSeries.value) { alert('Please select a series first.'); return }
  commitPending()
  if (!customerId.value) { alert('Please select a customer first.'); openCustomerPicker(); return }
  const lines = activeRows.value.filter(r => Number(r.qty) > 0)
  if (!lines.length) { alert('No items to save'); return }
  if (isReturn.value) {
    const missing = lines.find(r => !r._is_free && !r.batch_no && batchRequired(r.item_code))
    if (missing) {
      alert(`Select a batch for ${missing.item_name || missing.item_code} on this return.`)
      editRow(missing, 'qty')
      openBatchPicker()
      return
    }
  }

  const extra = _loadedExtras
  const payload = {
    company,
    series: selectedSeries.value,
    custom_invoice_no: '',
    customer: customerId.value,
    customer_address: customerAddress.value,
    mop: mop.value,
    posting_date: extra?.posting_date || serverToday(),
    update_stock: 1,
    price_list: priceList.value,
    discount_pct: extra?.discount_percentage || '',
    discount_amt: extra?.additional_discount_amount || '',
    tax_template: taxTemplate.value,
    cost_center: costCenter.value,
    warehouse: warehouse.value,
    income_account: incomeAccount.value,
    is_inclusive_tax: isInclusive.value ? 1 : 0,
    is_return: isReturn.value ? 1 : 0,
    customer_rate_multiplier: ignoreModifier.value ? 0 : 1,
    additional_charges: chargeRows(extra),
    place_of_supply: customerState.value || '',
    custom_customer_name: extra?.custom_customer_name || '',
    custom_address_line1: extra?.custom_address_line1 || '',
    custom_address_line2: extra?.custom_address_line2 || '',
    custom_mobile_number: extra?.custom_mobile_number || '',
    custom_remarks: extra?.custom_remarks || '',
    items: lines.map(r => ({
      item_code: r.item_code,
      qty: r.qty,
      uom: r.uom || 'Nos',
      rate: netRate(r),
      gross_rate: r.rate || 0,
      price_list_rate: r._base_rate || r.price_list_rate || r.rate,
      discount: Number(r.discount) || 0,
      is_free_item: r._is_free ? 1 : 0,
      batch_no: r.batch_no || '',
    })),
  }

  busy.value = true
  const isUpdate = !!invoiceName.value
  try {
    const res = isUpdate
      ? await frappePost('ssplbilling.api.sales.update_sales_invoice', { invoice_name: invoiceName.value, payload: JSON.stringify(payload) })
      : await frappePost('ssplbilling.api.sales.post_sales_invoice', { payload: JSON.stringify(payload) })
    if (res?.status !== 'success') throw new Error(res?.message || 'Failed to save bill.')
    const name = res.name || invoiceName.value
    await releaseLock()
    await loadBill(name)
    showPrintModal.value = true
  } catch (e) {
    alert(e?.message || (isUpdate ? 'Failed to update bill.' : 'Failed to save bill.'))
  } finally {
    busy.value = false
  }
}

function closePrintModal() {
  showPrintModal.value = false
}

// ── Past bills ───────────────────────────────────────────────────────────────
const showPastBills = ref(false)
const pastBills = ref([])
const pastLoading = ref(false)
const pastDate = ref(serverToday())
const pastQuery = ref('')
const pastDraftOnly = ref(false)
let pastSeq = 0
let pastTimer = null

async function fetchPastBills() {
  const seq = ++pastSeq
  pastLoading.value = true
  try {
    const list = await frappeGet('ssplbilling.api.sales.get_sales_invoices', {
      query: pastQuery.value.trim(),
      limit: 100,
      posting_date: pastDate.value,
      naming_series: seriesOptions.value.join(','),
      draft_only: pastDraftOnly.value,
      company,
    })
    if (seq !== pastSeq) return
    pastBills.value = (list || []).filter(b => b.docstatus !== 2)
  } catch (e) {
    if (seq === pastSeq) pastBills.value = []
  } finally {
    if (seq === pastSeq) pastLoading.value = false
  }
}

function openPastBills() {
  showPastBills.value = true
  fetchPastBills()
}

function shiftPastDate(days) {
  const d = parseCalendarDate(pastDate.value)
  d.setDate(d.getDate() + days)
  pastDate.value = toLocalISO(d)
}

watch([pastDate, pastDraftOnly], () => { if (showPastBills.value) fetchPastBills() })
watch(pastQuery, () => {
  clearTimeout(pastTimer)
  pastTimer = setTimeout(fetchPastBills, 300)
})

async function openPastBill(name) {
  if (!isReadOnly.value && (activeRows.value.length || pending.value) && !confirm('Discard the current bill and open ' + name + '?')) return
  showPastBills.value = false
  await releaseLock()
  await loadBill(name)
}

// ── Leave guard: a new bill being entered or a bill in Modify mode is unsaved ──
const hasUnsavedWork = computed(() => !isReadOnly.value && (activeRows.value.length > 0 || !!pending.value))

function confirmLeave() {
  if (!hasUnsavedWork.value) return true
  return confirm(invoiceName.value
    ? `You are modifying ${invoiceName.value}. Leave without saving? Your changes will be lost.`
    : 'This bill is not saved. Leave and discard it?')
}

// ← button and the phone's Back button (both are router navigations)
onBeforeRouteLeave(() => confirmLeave())

// Refresh / closing the tab: the browser shows its own "Leave site?" prompt
function onBeforeUnload(e) {
  if (!hasUnsavedWork.value) return
  e.preventDefault()
  e.returnValue = ''
}

// ── Layout / lifecycle ───────────────────────────────────────────────────────
// Fit the page to the area the browser actually shows (address bar / toolbar slide in and out)
const viewportHeight = ref(0)
const viewportStyle = computed(() => (viewportHeight.value ? { height: viewportHeight.value + 'px' } : null))
function fitViewport() {
  viewportHeight.value = Math.round(window.visualViewport?.height || window.innerHeight)
}

// Keys typed while nothing is focused (e.g. a Bluetooth barcode scanner) are collected
// and looked up as an item code / barcode on Enter
let wedgeBuffer = ''
let wedgeTimer = null
function onPageKeydown(e) {
  if (showScanner.value || showCustomerPicker.value || showPastBills.value || showPrintModal.value) return
  if (isReadOnly.value || e.ctrlKey || e.metaKey || e.altKey) return
  const el = document.activeElement
  if (el?.matches?.('input, textarea, select, [contenteditable="true"]')) return
  if (e.key === 'Enter') {
    const code = wedgeBuffer.trim()
    wedgeBuffer = ''
    if (code) { e.preventDefault(); addCode(code) }
  } else if (e.key.length === 1) {
    e.preventDefault()
    wedgeBuffer += e.key
    // A pause between keys means typing, not a scanner burst
    clearTimeout(wedgeTimer)
    wedgeTimer = setTimeout(() => { wedgeBuffer = '' }, 500)
  }
}

function onPageHide() {
  if (hasLock.value && invoiceName.value) {
    // Best effort: free the edit lock when the tab is closed mid-edit
    frappePost('ssplbilling.api.salesinvoice_api.release_bill_edit', { bill_no: invoiceName.value, tab_id: tabId }).catch(() => {})
  }
}

onMounted(async () => {
  fitViewport()
  window.visualViewport?.addEventListener('resize', fitViewport)
  window.addEventListener('resize', fitViewport)
  window.addEventListener('keydown', onPageKeydown)
  window.addEventListener('pagehide', onPageHide)
  window.addEventListener('beforeunload', onBeforeUnload)
  // Fetch the ZXing decoder now so the camera scanner reads bars from its first frame
  // on phones without a native BarcodeDetector (iOS Safari)
  import('@zxing/browser').catch(() => {})
  import('@zxing/library').catch(() => {})

  const series = await fetchAllowedSeries('Sales Invoice')
  const saved = localStorage.getItem(SERIES_KEY)
  selectedSeries.value = (series || []).includes(saved) ? saved : (series?.[0] || '')
  // Setting the series fills the price list, whose watcher loads the item dataset
  if (!selectedSeries.value) refreshItemCache('Sales', priceList.value || null, warehouse.value)
  // Discount rules are otherwise only loaded by the Dashboard; a phone may open this page directly
  refreshDiscountRuleCache().catch(() => {})
  ledgerCacheReady.then(() => { if (!allLedgers.value.length) refreshLedgerCache() })
})

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
  clearTimeout(pastTimer)
  clearTimeout(wedgeTimer)
  releaseLock()
  window.visualViewport?.removeEventListener('resize', fitViewport)
  window.removeEventListener('resize', fitViewport)
  window.removeEventListener('keydown', onPageKeydown)
  window.removeEventListener('pagehide', onPageHide)
  window.removeEventListener('beforeunload', onBeforeUnload)
})

</script>

<style scoped>
/* Each bill line is its own card, alternate lines shaded, so lines are easy to tell apart */
.bill-line {
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  background: var(--color-surface);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}
.bill-line:nth-child(even) {
  background: var(--color-surface-raised);
}
.bill-line.bill-line--free {
  background: color-mix(in srgb, var(--color-success) 10%, var(--color-bg));
}
.line-no {
  display: flex;
  height: 1.5rem;
  min-width: 1.5rem;
  padding: 0 0.25rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: var(--color-text);
  color: var(--color-bg);
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  font-weight: 700;
}
/* Bill line whose qty / rate / discount is open on the keypad */
/* Highlights are fills, not borders (user preference) */
.bill-line.row-editing {
  border-color: transparent;
  background: color-mix(in srgb, var(--color-success) 35%, var(--color-bg));
}
/* Other lines fade back while a qty / rate / discount is being typed on the keypad */
.bill-line.row-dimmed {
  opacity: 0.35;
}
/* Item picked on the scanner screen (or a line being modified), staged above the keypad */
.pending-panel {
  background: color-mix(in srgb, var(--color-success) 35%, var(--color-bg));
}
/* Input being typed into */
.hl-input:focus {
  border-color: transparent;
  background: color-mix(in srgb, var(--color-info) 22%, var(--color-bg));
}
/* Qty / rate box on a bill line: own fill and a strong border so it stands out on dark or shaded rows */
.line-box {
  border-color: var(--color-text-muted);
  background: var(--color-bg);
}
/* The value being typed into: solid focus colour instead of just a border */
.edit-focus {
  border-color: var(--color-info);
  background: var(--color-info);
  color: #fff;
}
.keypad-key {
  display: flex;
  height: 2.75rem;
  min-width: 0;
  padding: 0;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-family: ui-monospace, monospace;
  font-size: 1.25rem;
  font-weight: 700;
  user-select: none;
  touch-action: manipulation;
}
.keypad-key--ok {
  border-color: var(--color-success);
  background: var(--color-success);
  color: #fff;
  font-family: inherit;
  font-size: 1rem;
}
.keypad-key--sm {
  height: 2.25rem;
  font-family: inherit;
  font-size: 0.75rem;
}
.keypad-key--on {
  border-color: var(--color-info);
  background: var(--color-info);
  color: #fff;
}
.keypad-key:active {
  transform: scale(0.95);
}
</style>
