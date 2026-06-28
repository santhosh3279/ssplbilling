<template>
  <div class="h-screen bg-[var(--color-bg)] overflow-hidden">
    <Item_Invoice_Template
      :show-sidebar="!isSubwindow"
      :show-back-button="!isSubwindow"
      ref="invoiceTemplateRef"
      title="Purchase Invoice"
      :doc-number="invoiceNo"
      :party-name="supplierName"
      :party-details="supplierDetails"
      :party-address="supplierAddress"
      :party-mobile="supplierMobile"
      :party-gstin="supplierGstin"
      :party-balance="null"
      :party-last-inv-date="supplierLastInvDate"
      :doc-date="invoiceDate"
      :items="items"
      :subtotal="subtotal"
      :item-discount-total="itemDiscountTotal"
      :total-tax="totalTax"
      :total-amount="totalAmount"
      :round-off="roundOff"
      :price-list="priceList"
      :tax-template="taxTemplate"
      :is-inclusive-tax="isInclusiveTax"
      :is-return="isReturn"
      :warehouse="warehouse"
      :cost-center="costCenter"
      doctype="Purchase Invoice"
      :income-account="''"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentInvoices"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :available-series="availableSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      :posting-time="postingTime"
      @sidebar-date-change="handleSidebarDateChange"
      @doc-date-change="handleDocDateChange"
      @update:sidebarSearch="sidebarSearch = $event"
      @update:sidebarSeries="sidebarSeries = $event"
      @toggle-draft-only="draftOnly = !draftOnly"
      @select-sidebar-item="handleSelectSidebarItem"
      v-model:freight-entry="freightEntry"
      :freight-amt="freightAmt"
      v-model:packing-entry="packingEntry"
      :packing-amt="packingAmt"
      v-model:loading-entry="loadingEntry"
      :loading-amt="loadingAmt"
      loading-label="Tax Paid"
      v-model:other-entry="otherEntry"
      :other-amt="otherAmt"
      v-model:discount-pct="discountPct"
      v-model:discount-direct-amt="discountDirectAmt"
      :discount-amt="discountAmt"
      @back="goBack"
      @save="handleSave"
      @print="handlePrint"
      @discount-pct-keydown="handleDiscountPctKeydown"
      @discount-amt-keydown="handleDiscountAmtKeydown"
      @other-entry-enter="saveBtnRef?.focus()"
      @cancel="handleCancel"
      @incentive="handleIncentive"
      @party-click="supplierInitialQuery = ''; showSupplierModal = true"
    >
      <template #header-right>
        <div class="flex items-center gap-4">
          <button
            v-if="supplierId"
            @click="showHistoryModal = true"
            class="flex items-center gap-2 rounded bg-[var(--color-highlight)] px-3 py-1 text-xs font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all hover:bg-[var(--color-highlight)]/80 active:scale-95 shadow-lg"
          >
            <span>📜</span> History
          </button>
        </div>
      </template>

      <template #header-bar>
        <!-- Line 1: Doc Number, Party Name, Mobile, GST, Balance -->
        <div class="flex items-center gap-6 overflow-hidden">
          <div v-if="invoiceNo" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
            <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ invoiceNo }}</div>
          </div>

          <div 
            class="flex-1 flex items-baseline gap-6 overflow-hidden transition-colors group"
            :class="isReadOnly ? 'cursor-default' : 'cursor-pointer hover:bg-[var(--color-surface-raised)]/80'"
            @click="!isReadOnly && (supplierInitialQuery = '', showSupplierModal = true)"
          >
            <div class="flex items-baseline gap-3 shrink-0">
              <label 
                class="text-xl font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap transition-colors"
                :class="!isReadOnly ? 'group-hover:text-[var(--color-highlight)]' : ''"
              >Supplier</label>
              <div class="text-5xl font-bold text-[var(--color-text)] truncate max-w-[600px]">{{ supplierName || 'Not Selected' }}</div>
            </div>

            <div v-if="supplierMobile" class="flex items-center gap-1 text-[var(--color-highlight)] font-mono text-3xl whitespace-nowrap shrink-0">
              <span class="text-xl uppercase text-[var(--color-text-muted)]">Mob:</span>
              {{ supplierMobile }}
            </div>

            <div v-if="supplierGstin" class="flex items-center gap-1 text-[var(--color-text)]/70 font-mono text-3xl whitespace-nowrap shrink-0">
              <span class="text-xl uppercase text-[var(--color-text-muted)]">GST:</span>
              {{ supplierGstin }}
            </div>
          </div>

          <!-- Time & Discount % (Right Aligned on Supplier Name row) -->
          <div class="flex items-center gap-6 ml-auto whitespace-nowrap shrink-0">
            <div v-if="postingTime" @click.stop class="flex items-center gap-2 border-[var(--color-border)]">
              <span class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Time</span>
              <span class="text-3xl font-bold font-mono text-[var(--color-text)]">{{ formatTime(postingTime) }}</span>
            </div>
            <div v-if="!isSaved" class="flex items-center gap-2" :class="postingTime ? 'border-l border-[var(--color-border)] pl-6' : ''">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Discount %</label>
              <input
                v-model.number="globalDiscountPct"
                type="number"
                min="0"
                max="100"
                step="0.01"
                placeholder="0.00"
                :disabled="isReadOnly"
                class="border-b border-[var(--color-border)] px-1 py-0 text-4xl font-bold outline-none bg-transparent text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] w-24 text-right [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
            </div>
          </div>
        </div>

        <!-- Line 2: Secondary Details + Supp Inv info (Right Aligned) -->
        <div class="flex items-center gap-8 border-t border-[var(--color-border)]/30 pt-2">
          <div v-if="supplierLastInvDate" class="flex items-center gap-2 whitespace-nowrap shrink overflow-hidden">
            <span class="text-xl font-bold uppercase text-[var(--color-text-muted)] shrink-0">Last Inv</span>
            <span class="text-3xl font-mono text-[var(--color-highlight)] truncate">{{ supplierLastInvDate }}</span>
          </div>

          <!-- Supplier Invoice Info & Bill Date (Right Aligned Container) -->
          <div class="flex items-center gap-8 ml-auto whitespace-nowrap">
            <!-- Supplier Invoice Info -->
            <div class="flex items-center gap-6 border-l border-[var(--color-border)] pl-6">
              <div class="flex items-center gap-2">
                <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Supp. Inv No</label>
                <input
                  ref="supplierInvoiceNoRef"
                  v-model="supplierInvoiceNo"
                  :disabled="isReadOnly"
                  placeholder="Bill No"
                  class="border-b border-[var(--color-border)] px-1 py-0 text-4xl font-bold outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] bg-transparent text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] w-48"
                  @keydown.enter.prevent="supplierInvoiceNo.trim() ? supplierInvoiceDateInputRef?.focus() : alert('Supplier Invoice No is mandatory.')"
                />
              </div>

              <div class="flex items-center gap-2">
                <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Supp. Date</label>
                <div class="flex items-center gap-1 border-b border-[var(--color-border)]" :class="suppDateFocused ? 'bg-[var(--color-focus)]' : ''">
                  <button
                    @click="handleSupplierInvoiceDateChange(-1)"
                    :disabled="isReadOnly"
                    class="disabled:opacity-30 px-1 text-3xl" :class="suppDateFocused ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-on-highlight)]'"
                  >&larr;</button>
                  <div class="relative min-w-[140px] flex items-center justify-center">
                    <span v-show="!suppDateFocused" class="text-4xl font-bold tabular-nums" :class="suppDateFocused ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ formatDateShort(supplierInvoiceDate) }}</span>
                    <input
                      ref="supplierInvoiceDateInputRef"
                      type="text"
                      v-model="suppDateEntry"
                      :disabled="isReadOnly"
                      maxlength="10"
                      placeholder="DD/MM/YYYY"
                      class="text-4xl font-bold tabular-nums text-center outline-none bg-transparent"
                      :class="suppDateFocused ? 'w-full text-[var(--color-text-on-focus)]' : 'absolute inset-0 opacity-0 cursor-pointer w-full h-full'"
                      @focus="onSuppDateFocus"
                      @blur="onSuppDateBlur"
                      @input="onSuppDateInput"
                      @keydown.backspace="handleSuppDateBackspace"
                      @keydown.enter.prevent="parseSuppDate"
                    />
                  </div>
                  <button
                    @click="handleSupplierInvoiceDateChange(1)"
                    :disabled="isReadOnly"
                    class="disabled:opacity-30 px-1 text-3xl" :class="suppDateFocused ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-on-highlight)]'"
                  >&rarr;</button>
                </div>
              </div>
            </div>

            <!-- Bill Date (Original) -->
            <div v-if="invoiceDate" class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6">
              <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Bill Date</label>
              <div class="flex items-center gap-1">
                <button @click="handleDocDateChange(-1)" class="rounded p-0.5 text-4xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&larr;</button>
                <div class="text-4xl font-bold text-[var(--color-text)] tabular-nums">{{ formatDateShort(invoiceDate) }}</div>
                <button @click="handleDocDateChange(1)" class="rounded p-0.5 text-4xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&rarr;</button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template #row="{ item, index, formatQty }">
        <tr
          :ref="el => { if (el) rowRefs[index] = el }"
          :tabindex="isReadOnly ? -1 : 0"
          class="border-b border-[var(--color-border)] outline-none cursor-pointer transition-all"
          :class="{
            'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)] font-bold !text-[var(--color-text-on-focus)]': !isReadOnly && (selectedRowIdx === index || editingRowIdx === index) && !item.deleted && !item._is_free,
            'bg-[var(--color-success)]/20': item._is_free && !item.deleted,
            'opacity-40 bg-[var(--color-danger)]/10 grayscale-[0.5]': item.deleted,
            'hover:bg-[var(--color-surface-raised)]/50': !isReadOnly && selectedRowIdx !== index && editingRowIdx !== index && !item.deleted
          }"
          @focus="!isReadOnly && (selectedRowIdx = index)"
          @keydown="!isReadOnly && handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-center relative" :class="selectedRowIdx === index && !item.deleted ? 'text-black' : 'text-[var(--color-text-muted)]'">
            <span v-if="item.deleted" class="text-[10px] bg-[var(--color-danger)] text-[var(--color-text-on-highlight)] px-1 rounded block uppercase font-bold leading-tight mb-1">Deleted</span>
            {{ index + 1 }}
          </td>

          <!-- item_code -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'code'"
              ref="editCodeInput"
              v-model="item.item_code"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @focus="e => e.target.select()"
              @input="onEditCodeInput(index)"
              @keydown="onEditCodeKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">{{ item.item_code }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-medium" :class="selectedRowIdx === index && !item.deleted && !item._is_free ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">
            {{ item.item_name }}
            <span v-if="item._is_free" class="ml-1 rounded bg-[var(--color-success)] text-[var(--color-text-on-highlight)] px-1 text-[10px] font-bold uppercase leading-tight">Free</span>
          </td>

          <!-- qty -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'qty'"
              ref="editQtyInput"
              v-model.number="item.qty"
              type="number"
              :step="item.uom === 'Nos' ? '1' : '0.01'"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @input="item.uom === 'Nos' && (item.qty = Math.floor(item.qty))"
              @keydown="onEditQtyKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ formatQty(item.qty, item.uom) }}</span>
          </td>

          <td class="p-0 border-r border-[var(--color-border)]">
            <select v-if="editingRowIdx === index && editingField === 'uom'"
              ref="editUomSelect"
              v-model="item.uom"
              class="w-full bg-white/10 px-2 py-1 text-3xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @change="onUomChange(index)"
              @keydown="onEditUomKeydown($event, index)"
            >
              <option v-for="u in getItemUoms(item.item_code)" :key="u" :value="u" class="bg-[var(--color-bg)] text-3xl">{{ u }}</option>
              <option v-if="!getItemUoms(item.item_code).length" :value="item.uom" class="bg-[var(--color-bg)] text-3xl">{{ item.uom }}</option>
            </select>
            <span v-else class="block px-2 py-1 text-3xl" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ item.uom || 'Nos' }}</span>
          </td>

          <!-- rate -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'rate'"
              ref="editRateInput"
              v-model.number="item.rate"
              type="number" min="0" step="0.01"
              class="w-full bg-white/10 px-2 py-1 text-5xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown="onEditRateKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ format(item.rate) }}</span>
          </td>

          <!-- disc % -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'disc'"
              ref="editDiscInput"
              v-model.number="item.discount"
              type="number" min="0" max="100" step="0.5"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown="onEditDiscKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono text-right" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]'">{{ format(item.discount) }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]/80'">
            {{ format((item.rate || 0) * (1 - (item.discount || 0) / 100)) }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
            {{ format(isExempted ? 0 : (item.tax_rate ?? 0)) }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ format(item.amount) }}</td>
          <td class="px-2 py-1 text-center">
            <button
              class="rounded px-1 py-0.5 hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]"
              :class="item.deleted ? 'text-[var(--color-danger)] hover:text-[var(--color-danger)] font-bold' : (selectedRowIdx === index ? 'text-[var(--color-text)]/60 hover:text-[var(--color-danger)]' : 'text-[var(--color-text-muted)]')"
              @click.stop="selectedRowIdx = index; deleteItem(index)"
            >
              {{ item.deleted ? 'Undo' : '×' }}
            </button>
          </td>
        </tr>
      </template>

      <template #bottom-left>
        <div class="flex flex-col h-full overflow-hidden">
          <div class="flex-1 overflow-y-auto px-4 pb-4 pt-2 scrollbar-none">
            <div v-if="selectedRowIdx === -1 && !pendingItem" class="text-sm text-[var(--color-text-muted)] italic">
              Scan an item or select a row to see history.
            </div>
            <div v-else class="space-y-4">
              <!-- Current Supplier History -->
              <div>
                <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Purchase History (This Supplier):</div>
                <div v-if="historyLoading" class="text-sm text-[var(--color-info)] animate-pulse">
                  Fetching history...
                </div>
                <div v-else-if="!selectedItemHistory.length" class="text-sm text-[var(--color-text-muted)] italic">
                  No previous history found for this supplier.
                </div>
                <div v-else class="max-h-[110px] overflow-y-auto custom-scrollbar">
                  <table class="w-full text-left text-lg border-collapse">
                    <thead class="sticky top-0 bg-[var(--color-bg)] z-10">
                      <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                        <th class="py-0.5 pr-1 font-bold">Bill</th>
                        <th class="py-0.5 px-1 font-bold">Date</th>
                        <th class="py-0.5 px-1 text-right font-bold">Qty</th>
                        <th class="py-0.5 px-1 text-right font-bold">Rate</th>
                        <th class="py-0.5 pl-1 text-right font-bold">Disc%</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-[var(--color-border)]/30">
                      <tr v-for="(h, i) in selectedItemHistory.slice(0, 10)" :key="i" class="text-[var(--color-text)]">
                        <td class="py-1 pr-1 font-mono leading-none whitespace-nowrap">{{ h.name }}</td>
                        <td class="py-1 px-1 font-mono leading-none whitespace-nowrap">{{ formatDateShort(h.date) }}</td>
                        <td class="py-1 px-1 text-right font-mono leading-none">{{ h.qty }}</td>
                        <td class="py-1 px-1 text-right font-mono leading-none font-bold">{{ h.rate.toFixed(2) }}</td>
                        <td class="py-1 pl-1 text-right font-mono leading-none text-[var(--color-warning)]">{{ h.discount || 0 }}%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Different Suppliers History -->
              <div class="border-t border-[var(--color-border)] pt-2">
                <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Purchase History (Different Suppliers):</div>
                <div v-if="otherSuppliersHistoryLoading" class="text-sm text-[var(--color-info)] animate-pulse">
                  Fetching history...
                </div>
                <div v-else-if="!otherSuppliersItemHistory.length" class="text-sm text-[var(--color-text-muted)] italic">
                  No previous history found from other suppliers.
                </div>
                <div v-else class="max-h-[110px] overflow-y-auto custom-scrollbar">
                  <table class="w-full text-left text-lg border-collapse">
                    <thead class="sticky top-0 bg-[var(--color-bg)] z-10">
                      <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                        <th class="py-0.5 pr-1 font-bold">Supplier</th>
                        <th class="py-0.5 px-1 font-bold">Bill</th>
                        <th class="py-0.5 px-1 font-bold">Date</th>
                        <th class="py-0.5 px-1 text-right font-bold">Qty</th>
                        <th class="py-0.5 px-1 text-right font-bold">Rate</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-[var(--color-border)]/30">
                      <tr v-for="(h, i) in otherSuppliersItemHistory.slice(0, 10)" :key="i" class="text-[var(--color-text)]">
                        <td class="py-1 pr-1 font-semibold truncate max-w-[120px]" :title="h.supplier_name || h.supplier">{{ h.supplier_name || h.supplier }}</td>
                        <td class="py-1 px-1 font-mono leading-none whitespace-nowrap">{{ h.name }}</td>
                        <td class="py-1 px-1 font-mono leading-none whitespace-nowrap">{{ formatDateShort(h.date) }}</td>
                        <td class="py-1 px-1 text-right font-mono leading-none">{{ h.qty }}</td>
                        <td class="py-1 px-1 text-right font-mono leading-none font-bold">{{ h.rate.toFixed(2) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- Warehouse Stock -->
            <div v-if="activeItemCode && itemStock.length" class="border-t border-[var(--color-border)] pt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Stock:</div>
              <div v-if="stockLoading" class="text-sm text-[var(--color-info)] animate-pulse">Updating stock...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="s in itemStock" :key="s.warehouse" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ s.warehouse.split(' - ')[0] }}</span>
                  <span :class="s.qty > 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'" class="font-bold">{{ s.qty }}</span>
                </div>
              </div>
            </div>

            <!-- Available Prices -->
            <div v-if="activeItemCode && itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Prices:</div>
              <div v-if="pricesLoading" class="text-sm text-[var(--color-info)] animate-pulse">Updating prices...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="p in itemPrices" :key="p.price_list" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ p.price_list }}</span>
                  <span class="text-[var(--color-highlight)] font-bold tracking-widest">{{ encryptPrice(p.rate) }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="activeItemCode && !historyLoading && !pricesLoading && !itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2 text-sm text-[var(--color-text-muted)] italic">
              No additional price lists available.
            </div>
          </div>
        </div>
      </template>

      <template #bottom-middle>
        <div class="flex flex-col gap-3 p-2 max-h-[300px] overflow-y-auto custom-scrollbar" @keydown="handleModifyPanelKeydown">
          <!-- Export / Import -->
          <div class="flex gap-1">
            <button
              @click="handleExport"
              :disabled="!items.length"
              class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-1 text-[13px] font-bold uppercase text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] disabled:opacity-40 disabled:cursor-default transition-colors"
            >Export CSV</button>
            <button
              @click="handleImportClick"
              :disabled="isReadOnly"
              class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-1 text-[13px] font-bold uppercase text-[var(--color-text-muted)] hover:bg-[var(--color-midlight)] disabled:opacity-40 disabled:cursor-default transition-colors"
            >Import CSV</button>
          </div>

          <!-- Row 1: Price List -->
          <div class="flex flex-col gap-0.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Price List</label>
            <select
              ref="priceListSelectRef"
              v-model="priceList"
              :disabled="isReadOnly"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] disabled:opacity-50 disabled:cursor-default"
            >
              <option v-for="pl in localPriceLists" :key="pl" :value="pl">{{ pl }}</option>
              <option v-if="!localPriceLists.length" value="Standard Buying">Standard Buying</option>
            </select>
          </div>

          <!-- Row 2: Tax Template -->
          <div class="flex flex-col gap-0.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Tax Template</label>
            <select
              ref="taxTemplateRef"
              v-model="taxTemplate"
              :disabled="isReadOnly"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-2xl text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] disabled:opacity-50 disabled:cursor-default"
            >
              <option value="">-- None --</option>
              <option v-for="tax in localTaxTemplates" :key="tax" :value="tax">{{ tax }}</option>
            </select>
          </div>

          <!-- Checkboxes -->
          <div class="flex flex-col gap-1.5 py-1 border-y border-[var(--color-border)]/30">
            <label class="flex items-center gap-3 cursor-pointer" :class="isReadOnly ? 'cursor-default' : ''">
              <input ref="inclusiveTaxRef" type="checkbox" v-model="isInclusiveTax" :disabled="isReadOnly" class="h-6 w-6 rounded border-[var(--color-border)] accent-[var(--color-highlight)] disabled:opacity-50" />
              <span class="text-[var(--color-text-muted)] text-xl font-bold uppercase">Inclusive Tax</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer" :class="isReadOnly ? 'cursor-default' : ''">
              <input type="checkbox" v-model="isReturn" :disabled="isReadOnly" class="h-6 w-6 rounded border-[var(--color-border)] accent-[var(--color-danger)] disabled:opacity-50" />
              <span class="text-[var(--color-text-muted)] text-xl font-bold uppercase">Purchase Return</span>
            </label>
          </div>

          <!-- Additional Info -->
          <div class="grid grid-cols-2 gap-2">
            <!-- Warehouse -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
              <select
                v-model="warehouse"
                :disabled="isReadOnly"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] transition-colors disabled:opacity-50 disabled:cursor-default"
              >
                <option v-for="w in localWarehouses" :key="w" :value="w">{{ w }}</option>
                <option v-if="!localWarehouses.length" :value="warehouse">{{ warehouse }}</option>
              </select>
            </div>

            <!-- Cost Center -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
              <select
                ref="costCenterRef"
                v-model="costCenter"
                disabled
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none disabled:opacity-50 disabled:cursor-default"
              >
                <option v-for="cc in localCostCenters" :key="cc" :value="cc">{{ cc }}</option>
                <option v-if="!localCostCenters.length" :value="costCenter">{{ costCenter }}</option>
              </select>
            </div>
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex flex-col gap-2 h-full py-2">
          <div class="rounded-xl border border-[var(--color-highlight)]/40 bg-[var(--color-highlight)]/10 p-3.5 shadow-2xl">
            <div class="flex justify-between items-start mb-1">
              <div class="text-lg font-black uppercase tracking-[0.3em] text-[var(--color-highlight)]">Total Amount</div>
              <div class="text-xl font-bold text-[var(--color-text-muted)] tabular-nums">{{ items.length }} items</div>
            </div>
            <div class="flex items-baseline gap-2 font-bold" :class="parseFloat(totalAmount) < 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-success)]'">
              <span class="text-[9mm] font-black">₹</span>
              <span class="font-mono text-[15.75mm] font-black leading-none">{{ totalAmount }}</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button ref="saveBtnRef" @click="handleSave" :disabled="isSubmitted || submitting" class="flex-1 rounded py-2.5 text-center text-3xl font-semibold transition-colors uppercase focus:outline-none" :class="isSubmitted || submitting ? 'bg-[var(--color-surface-raised)]/40 text-[var(--color-text-muted)] cursor-not-allowed' : 'text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 focus:bg-[var(--color-success)]'">{{ saveButtonText }}</button>
            <button @click="handlePrint" :disabled="!isReadOnly" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isReadOnly ? 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-midlight)] cursor-pointer' : 'border-[var(--color-border)]/40 bg-[var(--color-surface)]/30 text-[var(--color-text-muted)] cursor-not-allowed'">Print</button>
          </div>
          <div class="flex gap-2">
            <button @click="showClearWarning = true" class="flex-1 rounded border border-[var(--color-highlight)]/50 bg-[var(--color-highlight)]/10 py-2.5 text-center text-3xl font-semibold text-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/20 transition-colors">New</button>
            <button @click="handleIncentive" :disabled="isSubmitted" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isSubmitted ? 'border-[var(--color-border)]/40 bg-[var(--color-surface)]/20 text-[var(--color-text-muted)] cursor-not-allowed' : 'border-[#D8C9A8] bg-[#EDE3CC] text-[#4A3520] hover:bg-[#E0D4B8]'">Incentive</button>
          </div>
          <button @click="handleBarcodePrint" @keydown.alt.p.prevent="handleBarcodePrint" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-2.5 text-center text-3xl font-semibold text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition-colors">Print Barcode</button>
          <button 
            @click="linkSupplierToAllItems" 
            :disabled="!supplierId || !items.some(i => !i.deleted) || linkingSupplier" 
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] py-2.5 text-center text-3xl font-semibold text-[var(--color-text)] hover:bg-[var(--color-midlight)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ linkingSupplier ? 'Mapping Supplier...' : 'Map Supplier to Item Master' }}
          </button>
        </div>
      </template>

      <template #table-extra-rows>
        <!-- Pending row: qty input after item selected -->
        <template v-if="pendingItem">
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/10">
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-xl font-mono text-center">+</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-2xl font-mono">{{ pendingItem.item_code }}</td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-2xl">{{ pendingItem.item_name }}</td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="pendingQtyInput"
                v-model.number="pendingItem.qty"
                type="number"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keydown="handlePendingQtyKeydown"
              />
            </td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <select
                v-if="getItemUoms(pendingItem.item_code).length > 1"
                ref="pendingUomSelect"
                v-model="pendingItem.uom"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
                @change="onPendingUomChange"
                @keydown.enter.prevent="focusPendingRate()"
                @keydown.escape="cancelPendingItem"
              >
                <option v-for="u in getItemUoms(pendingItem.item_code)" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ u }}</option>
              </select>
              <span v-else class="block px-2 py-1 text-xl text-[var(--color-text-muted)]">{{ pendingItem.uom || 'Nos' }}</span>
            </td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="pendingRateInput"
                v-model.number="pendingItem.rate"
                type="number" min="0" step="0.01"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keydown="handlePendingRateKeydown"
              />
            </td>
            <!-- disc % -->
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="pendingDiscInput"
                v-model.number="pendingItem.discount"
                type="number" min="0" max="100" step="0.5"
                class="w-full bg-[var(--color-highlight)]/20 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                @keydown="handlePendingDiscKeydown"
              />
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums text-[var(--color-warning)]/80">
              {{ format((pendingItem.rate || 0) * (1 - (pendingItem.discount || 0) / 100)) }}
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums text-[var(--color-text-muted)]">
              {{ format(isExempted ? 0 : (pendingItem.tax_rate ?? 0)) }}
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-5xl font-mono text-right tabular-nums text-[var(--color-text)]">
              {{ format((pendingItem.qty || 0) * (pendingItem.rate || 0) * (1 - (pendingItem.discount || 0) / 100)) }}
            </td>
            <td class="px-2 text-[var(--color-text-muted)] italic text-lg text-center">
              <button class="text-2xl opacity-50 hover:opacity-100" @click="cancelPendingItem()">×</button>
            </td>
          </tr>
        </template>

        <!-- Barcode input row -->
        <template v-else-if="!isReadOnly">
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-highlight)]/5">
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl font-mono text-center">*</td>
            <td class="p-0 border-r border-[var(--color-border)]">
              <input
                ref="newCodeInput"
                v-model="newItemCode"
                class="w-full bg-transparent px-2 py-1 text-2xl font-mono text-[var(--color-highlight)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] placeholder:text-[var(--color-text-muted)]/30"
                placeholder="Scan or Type Item..."
                @input="onNewCodeInput"
                @keydown="handleNewCodeKeydown"
              />
            </td>
            <td colspan="9" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter Item Code to add to invoice</td>
          </tr>
        </template>
      </template>
    </Item_Invoice_Template>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :query="quickSearchQuery"
      :price-list="priceList"
      search-type="Purchase"
      :warehouse="warehouse"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
      @refresh="onQuickSearchRefresh"
    />

    <ItemSearch
      ref="itemSearchRef"
      :show="showItemSearch"
      search-type="Purchase"
      :price-list="priceList"
      :warehouse="warehouse"
      :skip-date-filter="true"
      :initial-query="itemSearchInitialQuery"
      @close="closeItemSearch"
      @select="onItemSearchSelect"
    />

    <CustomerSearchModal
      v-if="showSupplierModal"
      :show="showSupplierModal"
      skip-date-filter
      initial-type="Supplier"
      :allowed-types="['Supplier']"
      :initial-query="supplierInitialQuery"
      :hide-secondary="false"
      :show-hide-secondary="false"
      @close="showSupplierModal = false; supplierInitialQuery = ''"
      @select="handleSupplierSelected"
    />

    <Userseries
      :show="showSeriesModal"
      doctype="Purchase Invoice"
      @close="showSeriesModal = false"
      @selected="handleSeriesSelected"
    />

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="invoiceNo"
      doctype="Purchase Invoice"
      :initial-template="defaultTemplate"
      @close="closePrintModal"
    />

    <JumpToRowModal
      v-model:show="showJumpModal"
      :max-rows="items.length"
      @jump="handleJump"
    />

    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Purchase Invoice"
      :docname="isSaved ? invoiceNo : ''"
      :initial-rows="incentiveRows"
      @close="showIncentiveModal = false"
      @update:rows="onIncentiveSaved"
    />

    <Warning
      :show="showClearWarning"
      title="Clear Bill"
      message="All items will be removed and a new bill number will be assigned."
      @close="showClearWarning = false"
      @confirm="showClearWarning = false; clearBill()"
    />

    <Warning
      :show="showExitWarning"
      title="Exit Page"
      message="Are you sure you want to exit? Unsaved changes will be lost."
      @close="showExitWarning = false"
      @confirm="router.push('/')"
    />

    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Purchase Invoice"
      :extra="[
        { key: 'F2', desc: 'Clear bill / refresh bill number' },
        { key: 'F3', desc: 'Focus modify panel' },
        { key: 'F5', desc: 'Print invoice' },

        { key: 'ALT + P', desc: 'Print barcodes' },
        { key: 'F8 / Ctrl+S', desc: 'Save invoice' },
        { key: 'Insert', desc: 'Open incentive entry' },
        { key: 'Page Up', desc: 'Series (empty) / Change supplier (with items)' },
        { key: 'Delete', desc: 'Delete selected row' },
      ]"
      @close="showShortcutPage = false"
    />

    <!-- Hidden file input for CSV import -->
    <input ref="csvImportRef" type="file" accept=".csv" class="hidden" @change="onCsvFileSelected" />

    <PriceListUpdate
      v-if="showPriceListUpdate && priceListUpdateItemCode"
      :is-sub-window="true"
      :item-code="priceListUpdateItemCode"
      :selected-price-list="priceList"
      :initial-rate="priceListUpdateRate"
      :initial-uom="priceListUpdateUom"
      :initial-discount="priceListUpdateDiscount"
      :tax-rate="priceListUpdateTaxRate"
      :is-inclusive="isInclusiveTax"
      @close="onPriceListUpdateClose"
      @saved="onPriceListUpdateSaved"
    />

    <!-- Barcode Print Subwindow -->
    <BarcodePrintPage
      v-if="showBarcodeModal"
      isSubWindow
      :billNo="invoiceNo"
      :items="activeItems"
      @close="showBarcodeModal = false"
    />

    <!-- History Modal -->
    <div v-if="showHistoryModal" class="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="showHistoryModal = false">
      <div class="flex h-[80vh] w-[80vw] flex-col rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
        <div class="border-b border-[var(--color-border)] px-6 py-4 flex justify-between items-center bg-[var(--color-surface-raised)]">
          <div class="flex items-center gap-6">
            <div>
              <div class="text-2xl font-bold">Purchase History: {{ supplierName }}</div>
              <div class="text-sm text-[var(--color-text-muted)]">{{ historyViewMode === 'invoice' ? supplierPurchaseHistory.length : supplierHistoryItemWise.length }} {{ historyViewMode === 'invoice' ? 'transactions' : 'unique items' }} previously purchased</div>
            </div>
            <div class="flex rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-0.5 ml-4">
              <button 
                @click="historyViewMode = 'invoice'"
                class="px-3 py-1 text-xs font-bold uppercase rounded transition-all"
                :class="historyViewMode === 'invoice' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
              >
                Invoice-wise
              </button>
              <button 
                @click="historyViewMode = 'item'"
                class="px-3 py-1 text-xs font-bold uppercase rounded transition-all"
                :class="historyViewMode === 'item' ? 'bg-[var(--color-highlight)] text-[var(--color-text-on-highlight)] shadow-sm' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
              >
                Item-wise
              </button>
            </div>
          </div>
          <button @click="showHistoryModal = false" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)]">✕</button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 bg-[var(--color-surface-raised)] shadow-sm">
              <!-- Invoice-wise Header -->
              <tr v-if="historyViewMode === 'invoice'" class="text-left text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                <th class="px-4 py-2">Date</th>
                <th class="px-4 py-2">Item Code</th>
                <th class="px-4 py-2">Item Name</th>
                <th class="px-4 py-2">Barcodes</th>
                <th class="px-4 py-2 text-right">Qty</th>
                <th class="px-4 py-2 text-right">Rate</th>
                <th class="px-4 py-2">Invoice</th>
              </tr>
              <!-- Item-wise Header -->
              <tr v-else class="text-left text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                <th class="px-4 py-2">Item Code</th>
                <th class="px-4 py-2">Item Name</th>
                <th class="px-4 py-2">Barcodes</th>
                <th class="px-4 py-2 text-right">Total Qty</th>
                <th class="px-4 py-2 text-right">Last Rate</th>
                <th class="px-4 py-2">Last Date</th>
                <th class="px-4 py-2">Last Invoice</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
              <!-- Invoice-wise Rows -->
              <template v-if="historyViewMode === 'invoice'">
                <tr v-for="(h, idx) in supplierPurchaseHistory" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                  <td class="px-4 py-3 font-mono text-sm">{{ h.date }}</td>
                  <td class="px-4 py-3 font-mono font-bold text-[var(--color-highlight)]">{{ h.item_code }}</td>
                  <td class="px-4 py-3 text-lg font-medium">{{ h.item_name }}</td>
                  <td class="px-4 py-3 font-mono text-xs text-[var(--color-text-muted)]">{{ h.barcodes }}</td>
                  <td class="px-4 py-3 text-right font-bold text-xl">{{ h.qty }}</td>
                  <td class="px-4 py-3 text-right font-mono text-lg text-[var(--color-warning)]">{{ h.rate.toFixed(2) }}</td>
                  <td class="px-4 py-3 text-sm text-[var(--color-info)]">{{ h.name }}</td>
                </tr>
              </template>
              <!-- Item-wise Rows -->
              <template v-else>
                <tr v-for="(h, idx) in supplierHistoryItemWise" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                  <td class="px-4 py-3 font-mono font-bold text-[var(--color-highlight)]">{{ h.item_code }}</td>
                  <td class="px-4 py-3 text-lg font-medium">{{ h.item_name }}</td>
                  <td class="px-4 py-3 font-mono text-xs text-[var(--color-text-muted)]">{{ h.barcodes }}</td>
                  <td class="px-4 py-3 text-right font-bold text-xl">{{ h.total_qty }}</td>
                  <td class="px-4 py-3 text-right font-mono text-lg text-[var(--color-warning)]">{{ h.last_rate.toFixed(2) }}</td>
                  <td class="px-4 py-3 font-mono text-sm">{{ h.last_date }}</td>
                  <td class="px-4 py-3 text-sm text-[var(--color-info)]">{{ h.last_invoice }}</td>
                </tr>
              </template>
              <!-- Empty State -->
              <tr v-if="historyViewMode === 'invoice' ? !supplierPurchaseHistory.length : !supplierHistoryItemWise.length">
                <td colspan="7" class="px-4 py-12 text-center text-[var(--color-text-muted)] italic">No history available for this supplier</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="border-t border-[var(--color-border)] px-6 py-3 bg-[var(--color-surface-raised)] text-right">
          <button @click="showHistoryModal = false" class="rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] px-6 py-2 font-bold uppercase tracking-wider hover:bg-[var(--color-surface-raised)] transition-all">Close</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost, linkSupplierToItems } from '../api'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Userseries from '../components/Userseries.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import ItemSearch from '../components/ItemSearch.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import Warning from '../components/Warning.vue'
import { useItemCache, lookupItemInCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'
import { encryptPrice } from '../encryption.js'
import { useShortcuts } from '../services/shortcutManager'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import { salesInvoiceShortcuts } from '../shortcuts/salesInvoiceShortcuts'
import ShortcutPage from '../components/ShortcutPage.vue'
import PriceListUpdate from './PriceListUpdate.vue'
import BarcodePrintPage from './BarcodePrintPage.vue'

const router = useRouter()

const props = defineProps({
  isSubwindow: Boolean,
  invoiceName: String
})

const emit = defineEmits(['close'])

// --- Data Fetching & State Management ---
const { items: cachedItems, lastSync, refreshItemCache, searchItemsInCache } = useItemCache()
const { allowedSeries: availableSeries, fetchAllowedSeries } = useAllowedSeries()
const {
  fetchSupplierPurchaseHistory, clearHistory, hasSupplierHistory, getSupplierItemHistoryFromCache, historyLoading,
  supplierPurchaseHistory,
  fetchItemStock, itemStock, stockLoading,
  fetchItemPrices, itemPrices, pricesLoading,
  otherSuppliersItemHistory, otherSuppliersHistoryLoading, fetchOtherSuppliersItemHistory
} = useCustomerHistory()

// --- Primary Collections ---
const items = ref([])
const recentInvoices = ref([])

// --- Billing Settings & Defaults ---
const localPriceLists = ref([])
try { localPriceLists.value = JSON.parse(localStorage.getItem('wb-purchase-pricelist') || '[]') } catch { localPriceLists.value = [] }
if (!localPriceLists.value.length) {
  try { localPriceLists.value = JSON.parse(localStorage.getItem('wb-pricelist') || '[]') } catch { localPriceLists.value = [] }
}
const localTaxTemplates = ref([])
try { localTaxTemplates.value = JSON.parse(localStorage.getItem('wb-purchase-tax-template') || '[]') } catch { localTaxTemplates.value = [] }
const localWarehouses = ref([])
try { localWarehouses.value = JSON.parse(localStorage.getItem('wb-warehouses') || '[]') } catch { localWarehouses.value = [] }
const localCostCenters = ref([])
try { localCostCenters.value = JSON.parse(localStorage.getItem('wb-cost-centers') || '[]') } catch { localCostCenters.value = [] }

const priceList = ref(localPriceLists.value[0] || 'Standard Buying')
const taxTemplate = ref(localTaxTemplates.value[0] || '')
const warehouse = ref(localStorage.getItem('wb-warehouse') || localWarehouses.value[0] || 'None')
const costCenter = ref(localStorage.getItem('wb-cost-center') || localCostCenters.value[0] || 'None')
const isInclusiveTax = ref(localStorage.getItem('wb-tax-type-incl') === '1')
const isReturn = ref(false)

const supplierInvoiceNo = ref('')
const supplierInvoiceDate = ref(new Date().toISOString().split('T')[0])

function handleSupplierInvoiceDateChange(days) {
  const d = new Date(supplierInvoiceDate.value)
  d.setDate(d.getDate() + days)
  supplierInvoiceDate.value = d.toISOString().split('T')[0]
}

// --- Additional Charges ---
const freightEntry = ref('')
const packingEntry = ref('')
const loadingEntry = ref('')
const otherEntry = ref('')
const discountPct = ref('')
const discountDirectAmt = ref('')
const globalDiscountPct = ref('')

watch(globalDiscountPct, (newVal) => {
  const pct = newVal === '' || newVal === null || newVal === undefined ? 0 : parseFloat(newVal)
  if (!isNaN(pct)) {
    items.value.forEach((item, idx) => {
      if (!item.deleted && !item._is_free) {
        item.discount = pct
        recalcAmount(idx)
      }
    })
  }
})

const freightAmt = computed(() => parseFloat(freightEntry.value) || 0)
const packingAmt = computed(() => parseFloat(packingEntry.value) || 0)
const loadingAmt = computed(() => parseFloat(loadingEntry.value) || 0)
const otherAmt = computed(() => parseFloat(otherEntry.value) || 0)

// --- Page & UI State ---
const showSeriesModal = ref(false)
const showSupplierModal = ref(false)
const showShortcutPage = ref(false)
const showIncentiveModal = ref(false)
const incentiveRows = ref([])
const showClearWarning = ref(false)
const showExitWarning = ref(false)
const supplierInitialQuery = ref('')
const showHistoryModal = ref(false)
const historyViewMode = ref('item') // 'invoice' or 'item'

const supplierHistoryItemWise = computed(() => {
  const map = {}
  supplierPurchaseHistory.value.forEach(h => {
    if (!map[h.item_code]) {
      map[h.item_code] = {
        item_code: h.item_code,
        item_name: h.item_name,
        barcodes: h.barcodes,
        total_qty: 0,
        last_rate: h.rate,
        last_date: h.date,
        last_invoice: h.name,
      }
    }
    const entry = map[h.item_code]
    entry.total_qty += h.qty
  })
  return Object.values(map)
})
const invoiceTemplateRef = ref(null)
const priceListSelectRef = ref(null)
const taxTemplateRef = ref(null)
const inclusiveTaxRef = ref(null)
const costCenterRef = ref(null)
const supplierInvoiceNoRef = ref(null)
const supplierInvoiceDateInputRef = ref(null)
const suppDateFocused = ref(false)
const suppDateEntry = ref('')

function isoToDisplayDate(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

function onSuppDateFocus(e) {
  suppDateFocused.value = true
  suppDateEntry.value = isoToDisplayDate(supplierInvoiceDate.value)
  nextTick(() => { e.target.select() })
}

function onSuppDateBlur() {
  autoCompleteSuppDate()
  suppDateFocused.value = false
}

function onSuppDateInput(e) {
  let val = e.target.value.replace(/\D/g, '')

  if (val.length === 4) {
    const day = parseInt(val.slice(0, 2))
    const month = parseInt(val.slice(2, 4))
    if (!isNaN(day) && !isNaN(month) && month >= 1 && month <= 12) {
      const now = new Date()
      const opts = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit' }
      const [y, m] = new Intl.DateTimeFormat('en-CA', opts).format(now).split('-').map(Number)
      let year = y
      if (month > m) year--
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = month.toString().padStart(2, '0')
      supplierInvoiceDate.value = `${year}-${monthStr}-${dayStr}`
      suppDateEntry.value = `${dayStr}/${monthStr}/${year}`
      return
    }
  }

  if (val.length > 2 && val.length <= 4) {
    val = val.slice(0, 2) + '/' + val.slice(2)
  } else if (val.length > 4) {
    val = val.slice(0, 2) + '/' + val.slice(2, 4) + '/' + val.slice(4, 8)
  }

  suppDateEntry.value = val

  if (val.length === 10) {
    const [d, m, y] = val.split('/')
    if (d && m && y && y.length === 4) {
      supplierInvoiceDate.value = `${y}-${m}-${d}`
    }
  }
}

function handleSuppDateBackspace(e) {
  if (suppDateEntry.value && suppDateEntry.value.length > 0) {
    e.preventDefault()
    suppDateEntry.value = ''
    supplierInvoiceDate.value = ''
  }
}

function autoCompleteSuppDate() {
  const val = suppDateEntry.value.replace(/\D/g, '')
  if (val.length >= 1 && val.length <= 2) {
    const day = parseInt(val)
    if (!isNaN(day) && day >= 1 && day <= 31) {
      const now = new Date()
      const opts = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit' }
      const [y, m] = new Intl.DateTimeFormat('en-CA', opts).format(now).split('-').map(Number)
      const dayStr = day.toString().padStart(2, '0')
      const monthStr = m.toString().padStart(2, '0')
      supplierInvoiceDate.value = `${y}-${monthStr}-${dayStr}`
      suppDateEntry.value = `${dayStr}/${monthStr}/${y}`
    }
  }
}

function parseSuppDate() {
  autoCompleteSuppDate()
  if (supplierInvoiceNo.value.trim()) {
    focusBarcodeInput()
  } else {
    alert('Supplier Invoice No is mandatory.')
    supplierInvoiceNoRef.value?.focus()
  }
}
const saveBtnRef = ref(null)
const showPrintModal = ref(false)
const showBarcodeModal = ref(false)
const pendingClearAfterPrint = ref(false)
const showJumpModal = ref(false)
const showPriceListUpdate = ref(false)
const editRowPriceUpdateIdx = ref(null) // null = pending-item context, number = row-edit context
const priceListUpdateItemCode = computed(() => {
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.item_code || ''
  return pendingItem.value?.item_code || ''
})

const priceListUpdateRate = computed(() => {
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.rate || 0
  return pendingItem.value?.rate || 0
})

const priceListUpdateUom = computed(() => {
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.uom || ''
  return pendingItem.value?.uom || ''
})

const priceListUpdateDiscount = computed(() => {
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.discount || 0
  return pendingItem.value?.discount || 0
})

const priceListUpdateTaxRate = computed(() => {
  if (isExempted.value) return 0
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.tax_rate || 0
  return pendingItem.value?.tax_rate || 0
})

const lastEnterTime = ref(0)

const invoiceNo = ref('NEW')
const postingTime = ref('')
const selectedSeries = ref('')
const defaultTemplate = ref('')
const invoiceDate = ref(new Date().toISOString().split('T')[0])
const sidebarDate = ref(new Date().toISOString().split('T')[0])
const sidebarSearch = ref('')
const sidebarSeries = ref([])
const draftOnly = ref(false)
const sidebarLoading = ref(false)
const isLoadingBill = ref(false)

const isReadOnly = ref(false)
const isSaved = ref(false)
const isSubmitted = ref(false)
let tabId = sessionStorage.getItem('wb_tab_id')
if (!tabId) {
  tabId = Math.random().toString(36).substring(2, 15)
  sessionStorage.setItem('wb_tab_id', tabId)
}

const hasLock = ref(false)

async function releaseLock() {
  if (!hasLock.value || !invoiceNo.value || invoiceNo.value === 'NEW') return
  try {
    await frappePost('ssplbilling.api.salesinvoice_api.release_bill_edit', {
      bill_no: invoiceNo.value,
      tab_id: tabId
    })
  } catch (err) {
    console.error('Failed to release lock:', err)
  } finally {
    hasLock.value = false
  }
}

const saveButtonText = computed(() => {
  if (!isSaved.value) return 'Save'
  if (isSubmitted.value) return 'Submitted'
  return isReadOnly.value ? 'Modify Bill' : 'Update Bill'
})

function handleDocDateChange(days) {
  const d = new Date(invoiceDate.value)
  d.setDate(d.getDate() + days)
  invoiceDate.value = d.toISOString().split('T')[0]
}

async function fetchRecentInvoices() {
  sidebarLoading.value = true
  try {
    recentInvoices.value = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoices', {
      query: sidebarSearch.value,
      limit: 100,
      posting_date: sidebarDate.value,
      naming_series: sidebarSeries.value.join(','),
      draft_only: draftOnly.value
    })
  } catch (e) {
    recentInvoices.value = []
  }
  sidebarLoading.value = false
}

function handleSidebarDateChange(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

watch([sidebarDate, sidebarSeries, draftOnly], () => {
  fetchRecentInvoices()
})

let searchTimeout = null
watch(sidebarSearch, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(fetchRecentInvoices, 300)
})

async function handleSelectSidebarItem(item) {
  await releaseLock()
  try {
    isLoadingBill.value = true
    const data = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoice', { invoice_name: item.name })

    invoiceNo.value = data.name
    postingTime.value = data.posting_time || ''
    selectedSeries.value = data.naming_series || selectedSeries.value
    invoiceDate.value = data.posting_date || invoiceDate.value
    supplierInvoiceNo.value = data.bill_no || ''
    supplierInvoiceDate.value = data.bill_date || data.posting_date || new Date().toISOString().split('T')[0]

    supplierId.value = data.supplier || ''
    supplierName.value = data.supplier_name || data.customer_name || 'Select Supplier...'
    supplierState.value = data.state || ''

    if (data.price_list) priceList.value = data.price_list
    if (data.tax_template) taxTemplate.value = data.tax_template
    warehouse.value = data.set_warehouse || localStorage.getItem('wb-warehouse') || localWarehouses.value[0] || 'None'
    nextTick(() => {
      isInclusiveTax.value = data.is_inclusive === 1
    })
    isReturn.value = data.is_return === 1
    if (data.cost_center) costCenter.value = data.cost_center

    freightEntry.value = data.freight_amount || ''
    packingEntry.value = data.packing_amount || ''
    loadingEntry.value = data.loading_amount || ''
    otherEntry.value = data.other_charges_amount || ''

    discountPct.value = data.discount_percentage || ''
    discountDirectAmt.value = data.additional_discount_amount || ''

    incentiveRows.value = data.incentive_system || []

    items.value = (data.items || []).map(i => {
      const discount = i.discount || 0
      const effectiveRate = i.rate || 0
      const preDiscountRate = discount > 0
        ? parseFloat((effectiveRate / (1 - discount / 100)).toFixed(2))
        : effectiveRate
      return {
        item_code: i.item_code,
        item_name: i.item_name,
        qty: i.qty,
        rate: preDiscountRate,
        _base_rate: i.price_list_rate || preDiscountRate,
        price_list_rate: i.price_list_rate || preDiscountRate,
        discount,
        uom: i.uom || 'Nos',
        tax_rate: i.tax_rate || 0,
        deleted: false,
        _is_free: effectiveRate === 0,
        amount: parseFloat(((i.qty || 0) * effectiveRate).toFixed(2)),
      }
    })

    selectedRowIdx.value = -1
    editingRowIdx.value = -1
    pendingItem.value = null
    newItemCode.value = ''
    isReadOnly.value = true
    isSaved.value = true
    isSubmitted.value = data.docstatus === 1
  } catch (e) {
    console.error('Failed to load invoice:', e)
    alert('Failed to load invoice: ' + item.name)
  } finally {
    nextTick(() => {
      isLoadingBill.value = false
    })
  }
}

const supplierName = ref('Select Supplier...')
const supplierId = ref('')
const supplierDetails = ref('')
const supplierAddress = ref('')
const supplierMobile = ref('')
const supplierGstin = ref('')
const supplierLastInvDate = ref('')
const supplierState = ref('')
const submitting = ref(false)

const newItemCode = ref('')
const newCodeInput = ref(null)
const quickSearchResults = ref([])
const quickSearchQuery = computed(() => {
  if (editQuickSearchRowIdx.value !== null) {
    return (items.value[editQuickSearchRowIdx.value]?.item_code || '').trim()
  }
  return newItemCode.value
})
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)
const showItemSearch = ref(false)
const itemSearchRef = ref(null)
const itemSearchInitialQuery = ref('')
const editQuickSearchRowIdx = ref(null)
const itemSearchTargetRowIdx = ref(null)
const pendingItem = ref(null)
const pendingQtyInput = ref(null)
const pendingUomSelect = ref(null)
const pendingRateInput = ref(null)
const pendingDiscInput = ref(null)
const selectedRowIdx = ref(-1)
const rowRefs = ref([])
const editingRowIdx = ref(-1)
const originalRowCode = ref('')
const editingField = ref(null) // 'code' | 'qty' | 'uom' | 'rate' | 'disc'
const editCodeInput = ref(null)
const editQtyInput = ref(null)
const editUomSelect = ref(null)
const editRateInput = ref(null)
const editDiscInput = ref(null)

// --- Computeds ---
const activeItemCode = computed(() => {
  if (pendingItem.value) return pendingItem.value.item_code
  if (selectedRowIdx.value !== -1) return items.value[selectedRowIdx.value]?.item_code
  return null
})

const isExempted = computed(() => (taxTemplate.value || '').toLowerCase().includes('exempt'))

const activeItems = computed(() => items.value.filter(i => !i.deleted))

const taxOnGross = computed(() => {
  if (isExempted.value) return 0
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    if (isInclusiveTax.value) {
      return sum + (item.amount - item.amount / (1 + rate / 100))
    } else {
      return sum + (item.amount * (rate / 100))
    }
  }, 0)
})

const discountAmt = computed(() => {
  const p = parseFloat(discountPct.value) || 0
  const a = parseFloat(discountDirectAmt.value) || 0
  const grossSubtotal = activeItems.value.reduce((sum, item) => sum + item.amount, 0)
  if (p > 0) {
    const additionalChargesTotal = freightAmt.value + packingAmt.value + loadingAmt.value + otherAmt.value
    const undiscountedTotal = grossSubtotal + (isInclusiveTax.value ? 0 : taxOnGross.value) + additionalChargesTotal
    return undiscountedTotal * (p / 100)
  }
  return a
})

const itemDiscountTotal = computed(() => {
  return activeItems.value.reduce((sum, item) => {
    const rate = item.rate || 0
    const qty = item.qty || 0
    const disc = item.discount || 0
    return sum + ((rate * qty) * (disc / 100))
  }, 0).toFixed(2)
})

const discountFactor = computed(() => {
  const grossSubtotal = activeItems.value.reduce((sum, item) => sum + item.amount, 0)
  const discountBase = grossSubtotal + (isInclusiveTax.value ? 0 : taxOnGross.value)
  if (discountBase <= 0) return 1
  return (discountBase - discountAmt.value) / discountBase
})

const selectedItemHistory = computed(() => {
  if (pendingItem.value) return getSupplierItemHistoryFromCache(pendingItem.value.item_code)
  if (selectedRowIdx.value === -1) return []
  const item = items.value[selectedRowIdx.value]
  if (!item) return []
  return getSupplierItemHistoryFromCache(item.item_code)
})

const totalTax = computed(() => {
  if (isExempted.value) return '0.00'
  const factor = discountFactor.value
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    const discountedAmt = item.amount * factor
    let tax = 0
    if (isInclusiveTax.value) {
      tax = discountedAmt - (discountedAmt / (1 + rate / 100))
    } else {
      tax = discountedAmt * (rate / 100)
    }
    return sum + tax
  }, 0).toFixed(2)
})

const subtotal = computed(() => {
  const factor = discountFactor.value
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    const discountedAmt = item.amount * factor
    let net = discountedAmt
    if (isInclusiveTax.value && !isExempted.value) {
      net = discountedAmt / (1 + rate / 100)
    }
    return sum + net
  }, 0).toFixed(2)
})

const unroundedTotal = computed(() => {
  return (
    parseFloat(subtotal.value) +
    parseFloat(totalTax.value) +
    freightAmt.value +
    packingAmt.value +
    loadingAmt.value +
    otherAmt.value
  )
})

const totalAmount = computed(() => {
  return Math.round(unroundedTotal.value).toFixed(2)
})

const roundOff = computed(() => {
  return (parseFloat(totalAmount.value) - unroundedTotal.value).toFixed(2)
})

// --- Watchers ---

watch(items, (newItems) => {
  newItems.forEach((_, idx) => recalcAmount(idx))
}, { deep: true })

watch([activeItemCode, supplierId], ([code, suppId]) => {
  if (code) {
    fetchItemStock(code)
    fetchItemPrices(code)
    fetchOtherSuppliersItemHistory(code, suppId)
  } else {
    fetchOtherSuppliersItemHistory(null)
  }
})

watch(taxTemplate, (val) => {
  if (!val) return
  isInclusiveTax.value = val.toLowerCase().includes('inclusive')
})

watch(isReturn, (val) => {
  items.value.forEach((item, idx) => {
    if (item.deleted || item._is_free) return
    item.qty = val ? -Math.abs(item.qty || 0) : Math.abs(item.qty || 0)
    recalcAmount(idx)
  })
  if (pendingItem.value) {
    pendingItem.value.qty = val ? -Math.abs(pendingItem.value.qty || 0) : Math.abs(pendingItem.value.qty || 0)
  }
})

watch(priceList, (newList) => {
  if (!newList || isLoadingBill.value) return
  updateTableRates()
  refreshItemCache('Purchase', newList, warehouse.value)
    .then(() => updateTableRates())
    .catch(e => console.warn('[PurchaseInvoice] Background price refresh failed:', e))
})

watch(warehouse, (newVal) => {
  if (!newVal || isLoadingBill.value) return
  refreshItemCache('Purchase', priceList.value, newVal)
    .then(() => updateTableRates())
    .catch(e => console.warn('[PurchaseInvoice] Background price refresh failed:', e))
})

// --- Methods ---

function goBack() {
  if (props.isSubwindow) {
    emit('close')
  } else {
    router.push('/')
  }
}

function formatDateShort(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  return `${day}-${month}-${year}`
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const parts = timeStr.split('.')
  let mainTime = parts[0].trim()
  if (/^\d:\d{2}:\d{2}$/.test(mainTime)) {
    mainTime = '0' + mainTime
  }
  return mainTime
}

function format(val) {
  if (val === null || val === undefined || val === '') return '0.00'
  const num = Number(val)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

async function clearBill() {
  await releaseLock()
  items.value = []
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
  discountPct.value = ''
  discountDirectAmt.value = ''
  globalDiscountPct.value = ''
  freightEntry.value = ''
  loadingEntry.value = ''
  packingEntry.value = ''
  otherEntry.value = ''
  supplierInvoiceNo.value = ''
  supplierInvoiceDate.value = new Date().toISOString().split('T')[0]
  incentiveRows.value = []
  clearHistory()
  invoiceNo.value = 'NEW'
  postingTime.value = ''
  isReturn.value = false
  isReadOnly.value = false
  isSaved.value = false
  warehouse.value = localStorage.getItem('wb-warehouse') || localWarehouses.value[0] || 'None'
  if (selectedSeries.value) {
    try {
      const res = await frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: selectedSeries.value, doctype: 'Purchase Invoice' })
      invoiceNo.value = res.invoice_no || 'NEW'
      defaultTemplate.value = res.print_format || ''
    } catch {
      invoiceNo.value = 'NEW'
    }
  }

  nextTick(() => { newCodeInput.value?.focus() })
}

function handleF2() {
  const hasItems = items.value.some(i => !i.deleted)
  if (hasItems) {
    showClearWarning.value = true
  } else {
    clearBill()
  }
}

function handleF3() {
  nextTick(() => { invoiceTemplateRef.value?.focusSidebarList() })
}

function handleModifyPanelKeydown(e) {
  if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return
  e.preventDefault()
  const refs = [
    supplierInvoiceNoRef.value,
    supplierInvoiceDateInputRef.value,
    priceListSelectRef.value,
    taxTemplateRef.value,
    inclusiveTaxRef.value,
  ].filter(Boolean)
  const idx = refs.indexOf(document.activeElement)
  if (e.key === 'ArrowDown') {
    refs[(idx + 1) % refs.length]?.focus()
  } else {
    refs[(idx - 1 + refs.length) % refs.length]?.focus()
  }
}

function handlePageUp() {
  const hasItems = items.value.some(i => !i.deleted)
  if (hasItems) {
    supplierInitialQuery.value = supplierId.value || supplierName.value
    showSupplierModal.value = true
  } else {
    showSeriesModal.value = true
  }
}

async function handleSave() {
  if (isSubmitted.value || submitting.value) return
  if (isReadOnly.value && isSaved.value) {
    await handleModify()
    return
  }

  const active = items.value.filter(i => !i.deleted)
  if (!active.length) { alert('No items to save'); return }
  if (!supplierId.value) { alert('Please select a supplier first.'); return }
  if (!supplierInvoiceNo.value.trim()) { alert('Supplier Invoice No is mandatory.'); return }
  if (!selectedSeries.value) { alert('Please select a series first.'); return }

  submitting.value = true
  const additionalCharges = []
  const freight = parseFloat(freightEntry.value) || 0
  const loading = parseFloat(loadingEntry.value) || 0
  const packing = parseFloat(packingEntry.value) || 0
  const other = parseFloat(otherEntry.value) || 0
  if (freight !== 0) {
    const acct = localStorage.getItem('wb_freight')
    if (acct) additionalCharges.push({ charge_type: 'Actual', account_head: acct, tax_amount: freight, description: 'Freight' })
  }
  if (loading !== 0) {
    const acct = localStorage.getItem('wb-tax-paid-on-purchase')
    if (acct) additionalCharges.push({ charge_type: 'Actual', account_head: acct, tax_amount: loading, description: 'Tax Paid' })
  }
  if (packing !== 0) {
    const acct = localStorage.getItem('wb-packing')
    if (acct) additionalCharges.push({ charge_type: 'Actual', account_head: acct, tax_amount: packing, description: 'Packing' })
  }
  if (other !== 0) {
    const acct = localStorage.getItem('wb-other-charges')
    if (acct) additionalCharges.push({ charge_type: 'Actual', account_head: acct, tax_amount: other, description: 'Other Charges' })
  }


  const payload = {
    naming_series: selectedSeries.value,
    supplier: supplierId.value,
    bill_no: supplierInvoiceNo.value,
    bill_date: supplierInvoiceDate.value,
    update_stock: 1,
    date: invoiceDate.value,
    price_list: priceList.value,
    discount_percentage: discountPct.value,
    tax_template: taxTemplate.value,
    cost_center: costCenter.value,
    set_warehouse: warehouse.value,
    is_inclusive: isInclusiveTax.value ? 1 : 0,
    is_return: isReturn.value ? 1 : 0,
    taxes: additionalCharges,
    incentive_system: incentiveRows.value.map(r => ({ employee: r.employee, role: r.role, points: r.points || 0 })),
    items: active.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      uom: i.uom || 'Nos',
      rate: parseFloat(((i.rate || 0) * (1 - (i.discount || 0) / 100)).toFixed(2)),
      price_list_rate: i._base_rate || i.price_list_rate || i.rate,
      discount_percentage: i.discount || 0,
    }))
  }

  const isUpdate = isSaved.value

  try {
    let res
    if (isUpdate) {
      payload.invoice_name = invoiceNo.value
      res = await frappePost('ssplbilling.api.purchase_api.update_purchase_invoice', {
        data: JSON.stringify(payload)
      })
      if (res.invoice_name || res.grand_total !== undefined) {
        await releaseLock()
        if (props.isSubwindow) {
          emit('close')
          return
        }
        isReadOnly.value = true
        isSaved.value = true
        fetchRecentInvoices()
        pendingClearAfterPrint.value = false
        showPrintModal.value = true
      }
    } else {
      res = await frappePost('ssplbilling.api.purchase_api.create_purchase_invoice', {
        data: JSON.stringify(payload)
      })
      if (res.invoice_name) {
        invoiceNo.value = res.invoice_name
        isSaved.value = true
        isReadOnly.value = true
        fetchRecentInvoices()
        pendingClearAfterPrint.value = true
        showPrintModal.value = true
      }
    }
  } catch (error) {
    console.error('Error saving invoice:', error)
    alert(isUpdate ? 'Failed to update invoice.' : 'Failed to save invoice.')
  } finally {
    submitting.value = false
  }
}

function handleDiscountPctKeydown(e) {
  if (e.key === 'Enter') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountAmt() }
  else if (e.key === 'End') { e.preventDefault(); saveBtnRef.value?.focus() }
}

function handleDiscountAmtKeydown(e) {
  if (e.key === 'End') { e.preventDefault(); saveBtnRef.value?.focus() }
}

async function handleModify() {
  if (isSubmitted.value) {
    alert('Bill is submitted. Modify is denied.')
    return
  }
  if (!isReadOnly.value || !isSaved.value) return

  try {
    const res = await frappePost('ssplbilling.api.salesinvoice_api.record_bill_edit', {
      bill_no: invoiceNo.value,
      tab_id: tabId
    })
    if (res && res.status === 'conflict') {
      if (res.reason === 'same_user_other_tab') {
        alert('this bill is already editing by you in another browser tab')
      } else {
        alert(`the bill is in editing by the user: ${res.user}`)
      }
      return
    }
    hasLock.value = true
  } catch (err) {
    console.error(err)
    alert(err.message || 'Failed to check bill editing status.')
    return
  }

  isReadOnly.value = false
  if (items.value.length > 0) {
    focusRow(0)
  } else {
    focusBarcodeInput()
  }
}

function handlePrint() {
  if (!isSaved.value) {
    alert('Please save the invoice before printing.')
    return
  }
  showPrintModal.value = true
}

function handleBarcodePrint() {
  if (!isSaved.value) {
    alert('Please save the invoice before printing barcodes.')
    return
  }
  showBarcodeModal.value = true
}

async function closePrintModal() {
  showPrintModal.value = false
  if (!pendingClearAfterPrint.value) return
  pendingClearAfterPrint.value = false

  items.value = []
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
  discountPct.value = ''
  discountDirectAmt.value = ''
  globalDiscountPct.value = ''
  freightEntry.value = ''
  loadingEntry.value = ''
  packingEntry.value = ''
  otherEntry.value = ''
  supplierInvoiceNo.value = ''
  supplierInvoiceDate.value = new Date().toISOString().split('T')[0]
  incentiveRows.value = []
  clearHistory()

  isSaved.value = false
  isReadOnly.value = false
  try {
    const series = await frappeGet('ssplbilling.api.purchase_api.get_next_bill_no', { naming_series: selectedSeries.value })
    invoiceNo.value = series || 'NEW'
  } catch {
    invoiceNo.value = 'NEW'
  }

  nextTick(() => { newCodeInput.value?.focus() })
}

function handleCancel() {
  const hasParty = supplierId.value;
  const hasItems = items.value.length > 0;

  if (!isReadOnly.value && (hasParty || hasItems) && !props.isSubwindow) {
    showExitWarning.value = true;
  } else {
    if (items.value.length === 0 || isReadOnly.value || props.isSubwindow) {
      goBack();
    } else {
      selectedRowIdx.value = -1
      editingRowIdx.value = -1
      editingField.value = null
      focusBarcodeInput()
    }
  }
}

function handleIncentive() { showIncentiveModal.value = true }

// --- Export / Import CSV ---
const csvImportRef = ref(null)

function handleExport() {
  if (!items.value.length) return
  const header = ['item_code', 'item_name', 'qty', 'uom', 'rate', 'discount', 'tax_rate', 'amount']
  const rows = items.value
    .filter(i => !i.deleted)
    .map(i => [
      i.item_code,
      `"${(i.item_name || '').replace(/"/g, '""')}"`,
      i.qty,
      i.uom || 'Nos',
      i.rate,
      i.discount || 0,
      i.tax_rate != null ? i.tax_rate : 0,
      i.amount,
    ].join(','))
  const csv = [header.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${invoiceNo.value || 'purchase-invoice'}-items.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function handleImportClick() {
  if (isReadOnly.value) return
  csvImportRef.value.value = ''
  csvImportRef.value.click()
}

function onCsvFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const lines = ev.target.result.split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length < 2) { alert('CSV has no data rows.'); return }
    const header = lines[0].split(',').map(h => h.trim().toLowerCase())
    const idx = (col) => header.indexOf(col)
    const parsed = []
    for (let i = 1; i < lines.length; i++) {
      // handle quoted fields
      const cols = lines[i].match(/(".*?"|[^,]+)(?=,|$)/g) || []
      const get = (col) => (cols[idx(col)] || '').replace(/^"|"$/g, '').replace(/""/g, '"').trim()
      const item_code = get('item_code')
      if (!item_code) continue
      const qty = parseFloat(get('qty')) || 1
      const rate = parseFloat(get('rate')) || 0
      const discount = parseFloat(get('discount')) || 0
      const tax_rate = parseFloat(get('tax_rate')) || 0
      const effectiveRate = discount > 0 ? parseFloat((rate * (1 - discount / 100)).toFixed(2)) : rate
      parsed.push({
        item_code,
        item_name: get('item_name') || item_code,
        qty,
        uom: get('uom') || 'Nos',
        rate,
        _base_rate: rate,
        price_list_rate: rate,
        discount,
        tax_rate,
        deleted: false,
        _is_free: effectiveRate === 0,
        amount: parseFloat((qty * effectiveRate).toFixed(2)),
      })
    }
    if (!parsed.length) { alert('No valid rows found in CSV.'); return }
    if (items.value.length && !confirm(`Replace ${items.value.filter(i => !i.deleted).length} existing item(s) with ${parsed.length} imported row(s)?`)) return
    items.value = parsed
  }
  reader.readAsText(file)
}

function onIncentiveSaved(rows) {
  incentiveRows.value = rows
  showIncentiveModal.value = false
}

function handleJump(targetNo) {
  if (items.value.length === 0) return
  let idx = Math.max(0, Math.min(targetNo - 1, items.value.length - 1))
  focusRow(idx)
}

function getItemRateForPriceList(cachedItem, uom = null) {
  if (!cachedItem) return 0
  const plName = priceList.value

  const targetUom = uom || cachedItem.uom || 'Nos'
  if (cachedItem.uom_price_lists?.[plName]?.[targetUom] != null) {
    return cachedItem.uom_price_lists[plName][targetUom]
  }

  const plEntry = (cachedItem.price_lists || []).find(p => p.name === plName)
  if (plEntry) return plEntry.rate

  return parseFloat(cachedItem.price || 0)
}

function updateTableRates() {
  items.value.forEach((item, idx) => {
    if (item.deleted) return
    const cached = lookupItemInCache(item.item_code)
    if (cached) {
      const newRate = getItemRateForPriceList(cached, item.uom)
      item._base_rate = newRate
      item.rate = newRate
      recalcAmount(idx)
    }
  })
}

function recalcAmount(idx) {
  const item = items.value[idx]
  if (!item) return
  const netRate = parseFloat(((item.rate || 0) * (1 - (item.discount || 0) / 100)).toFixed(2))
  item.amount = parseFloat(((item.qty || 0) * netRate).toFixed(2))
}

function scrollRowToEdge(idx, direction) {
  const rowEl = rowRefs.value[idx]
  if (!rowEl) return
  const container = rowEl.closest('.overflow-y-auto')
  if (!container) return
  const rowRect = rowEl.getBoundingClientRect()
  const cRect = container.getBoundingClientRect()
  if (direction === 'down') {
    if (rowRect.bottom > cRect.bottom)
      container.scrollTop += (rowRect.bottom - cRect.bottom)
  } else {
    const theadH = container.querySelector('thead')?.offsetHeight || 0
    if (rowRect.top < cRect.top + theadH)
      container.scrollTop += (rowRect.top - cRect.top - theadH)
  }
}

function focusRow(idx, direction = null) {
  selectedRowIdx.value = idx
  nextTick(() => {
    const el = rowRefs.value[idx]
    if (!el) return
    el.focus({ preventScroll: true })
    if (direction) scrollRowToEdge(idx, direction)
    else el.scrollIntoView({ block: 'nearest' })
  })
}
function focusBarcodeInput() { selectedRowIdx.value = -1; nextTick(() => { newCodeInput.value?.focus() }) }

function deleteItem(idx) {
  const item = items.value[idx]; if (!item) return
  item.deleted = !item.deleted
  if (item.deleted && editingRowIdx.value === idx) { editingRowIdx.value = -1; editingField.value = null }
}

function onQuickSearchRefresh() {
  // After cache refresh, re-run search if there's a query
  if (newItemCode.value) {
    quickSearchResults.value = searchItemsInCache(newItemCode.value)
  }
}

function onQuickSearchSelect(item) {
  if (!item) return
  if (!supplierInvoiceNo.value.trim()) {
    alert('Supplier Invoice No is mandatory.')
    quickSearchResults.value = []
    supplierInvoiceNoRef.value?.focus()
    return
  }
  if (!isExempted.value && supplierId.value && !supplierGstin.value.trim()) {
    alert("Add party Gstin or change the tax template to exempted")
    quickSearchResults.value = []
    return
  }
  
  // Capture the query used to find this item
  const currentQuery = editQuickSearchRowIdx.value !== null 
    ? (items.value[editQuickSearchRowIdx.value]?.item_code || '').trim()
    : newItemCode.value.trim()
    
  // If the query was a barcode, lookupItemInCache will return the item with that barcode's specific UOM
  const barcodeMatch = lookupItemInCache(currentQuery)
  const finalItem = (barcodeMatch && barcodeMatch.item_code === item.item_code) ? barcodeMatch : item

  quickSearchResults.value = []
  if (editQuickSearchRowIdx.value !== null) {
    const rowIdx = editQuickSearchRowIdx.value
    editQuickSearchRowIdx.value = null
    applyItemToRow(rowIdx, finalItem)
    if (getItemUoms(finalItem.item_code).length > 1) {
      focusEditField('uom', rowIdx)
    } else {
      focusEditField('qty', rowIdx)
    }
    return
  }
  newItemCode.value = ''
  setPendingItem({
    item_code: finalItem.item_code, item_name: finalItem.item_name, qty: 0, rate: getItemRateForPriceList(finalItem, finalItem.uom),
    uom: finalItem.uom || 'Nos', discount: 0, tax_rate: finalItem.tax_rate || 0, deleted: false
  })
}

function applyItemToRow(rowIdx, item) {
  const row = items.value[rowIdx]
  if (!row) return
  const isSameItem = originalRowCode.value === item.item_code
  row.item_code = item.item_code
  row.item_name = item.item_name
  // Update UOM if it's a different item, OR if this specific match came from a barcode scan
  if (!isSameItem || item._from_barcode) {
    row.uom = item.uom || 'Nos'
  }
  row.tax_rate = item.tax_rate || 0

  if (!isSameItem) {
    const base = getItemRateForPriceList(item, row.uom)
    row._base_rate = base
    row.rate = base
    row.discount = 0
  }
  recalcAmount(rowIdx)
}

function openItemSearch(query, targetRowIdx = null) {
  if (targetRowIdx === null && !isExempted.value && supplierId.value && !supplierGstin.value.trim()) {
    alert("Add party Gstin or change the tax template to exempted")
    return
  }
  quickSearchResults.value = []
  editQuickSearchRowIdx.value = null
  itemSearchTargetRowIdx.value = targetRowIdx
  itemSearchInitialQuery.value = query || ''
  showItemSearch.value = true
  nextTick(() => { itemSearchRef.value?.focus() })
}

function closeItemSearch() {
  showItemSearch.value = false
  const rowIdx = itemSearchTargetRowIdx.value
  itemSearchTargetRowIdx.value = null
  if (rowIdx !== null) {
    nextTick(() => { focusEditField('code', rowIdx) })
  } else {
    nextTick(() => { newCodeInput.value?.focus() })
  }
}

function onItemSearchSelect(item) {
  if (!supplierInvoiceNo.value.trim()) {
    alert('Supplier Invoice No is mandatory.')
    supplierInvoiceNoRef.value?.focus()
    return
  }
  if (itemSearchTargetRowIdx.value === null && !isExempted.value && supplierId.value && !supplierGstin.value.trim()) {
    alert("Add party Gstin or change the tax template to exempted")
    return
  }
  showItemSearch.value = false
  const rowIdx = itemSearchTargetRowIdx.value
  itemSearchTargetRowIdx.value = null

  // Re-check for barcode match to get correct UOM from the initial query
  const barcodeMatch = lookupItemInCache(itemSearchInitialQuery.value.trim())
  const finalItem = (barcodeMatch && barcodeMatch.item_code === item.item_code) ? barcodeMatch : item

  if (rowIdx !== null) {
    applyItemToRow(rowIdx, finalItem)
    focusEditField('qty', rowIdx)
    return
  }
  newItemCode.value = ''
  setPendingItem({
    item_code: finalItem.item_code, item_name: finalItem.item_name, qty: 0, rate: getItemRateForPriceList(finalItem, finalItem.uom),
    uom: finalItem.uom || 'Nos', discount: 0, tax_rate: finalItem.tax_rate || 0, deleted: false
  })
}

function onEditCodeInput(rowIdx) {
  const code = (items.value[rowIdx]?.item_code || '').trim()
  if (code.length >= 2) {
    const rawResults = searchItemsInCache(code)
    quickSearchResults.value = rawResults.map(item => ({
      ...item,
      has_history: hasSupplierHistory(item.item_code)
    }))
    quickSearchAnchor.value = editCodeInput.value
    editQuickSearchRowIdx.value = rowIdx
  } else {
    quickSearchResults.value = []
    editQuickSearchRowIdx.value = null
  }
}

function onEditCodeKeydown(e, rowIdx) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return
    } else if (e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Escape') {
      e.preventDefault(); quickSearchResults.value = []; editQuickSearchRowIdx.value = null; return
    }
  }

  if (handleCellNavigation(e, rowIdx, 'code')) {
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    const code = (items.value[rowIdx]?.item_code || '').trim()
    const match = lookupItemInCache(code)
    if (match) {
      applyItemToRow(rowIdx, match)
      if (getItemUoms(match.item_code).length > 1) {
        focusEditField('uom', rowIdx)
      } else {
        focusEditField('qty', rowIdx)
      }
    } else {
      openItemSearch(code, rowIdx)
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    quickSearchResults.value = []
    editQuickSearchRowIdx.value = null
    exitEditMode(rowIdx, true)
  }
}

function onEditQtyKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'qty')) {
    return
  }
  
  if (e.key === 'Enter') {
    e.preventDefault()
    const item = items.value[idx]
    if (item && item.qty) {
      if (getItemUoms(item.item_code).length > 1) {
        focusEditField('uom', idx)
      } else {
        focusEditField('rate', idx)
      }
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode(idx, true)
  } else if (e.key === 'Backspace') {
    const item = items.value[idx]
    if (item && (!item.qty || item.qty === 0)) {
      e.preventDefault()
      focusEditField('code', idx)
    }
  }
}

function onEditUomKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'uom')) {
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    focusEditField('rate', idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode(idx, true)
  }
}

function onEditRateKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'rate')) {
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    focusEditField('disc', idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode(idx, true)
  }
}

function onEditDiscKeydown(e, idx) {
  if (handleCellNavigation(e, idx, 'disc')) {
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    openRowPriceListUpdate(idx)
  } else if (e.key === 'Escape') {
    e.preventDefault()
    exitEditMode(idx, true)
  }
}

function getNextField(currentField, itemCode) {
  const fields = ['code', 'qty', 'uom', 'rate', 'disc']
  const idx = fields.indexOf(currentField)
  if (idx === -1 || idx === fields.length - 1) return null
  const next = fields[idx + 1]
  if (next === 'uom' && getItemUoms(itemCode).length <= 1) {
    return getNextField('uom', itemCode)
  }
  return next
}

function getPrevField(currentField, itemCode) {
  const fields = ['code', 'qty', 'uom', 'rate', 'disc']
  const idx = fields.indexOf(currentField)
  if (idx === -1 || idx === 0) return null
  const prev = fields[idx - 1]
  if (prev === 'uom' && getItemUoms(itemCode).length <= 1) {
    return getPrevField('uom', itemCode)
  }
  return prev
}

function handleCellNavigation(e, idx, field) {
  const item = items.value[idx]
  if (!item) return false

  let isAtStart = true
  let isAtEnd = true

  if (e.target && e.target.tagName === 'INPUT' && (e.target.type === 'text' || !e.target.type)) {
    try {
      isAtStart = e.target.selectionStart === 0
      isAtEnd = e.target.selectionStart === null || e.target.selectionStart === e.target.value?.length
    } catch (err) {
      isAtStart = true
      isAtEnd = true
    }
  }

  if (e.key === 'ArrowLeft') {
    if (isAtStart) {
      const prev = getPrevField(field, item.item_code)
      if (prev) {
        e.preventDefault()
        focusEditField(prev, idx)
        return true
      } else if (idx > 0) {
        e.preventDefault()
        recalcAmount(idx)
        focusEditField('disc', idx - 1)
        return true
      }
    }
  } else if (e.key === 'ArrowRight') {
    if (isAtEnd) {
      const next = getNextField(field, item.item_code)
      if (next) {
        e.preventDefault()
        focusEditField(next, idx)
        return true
      } else if (idx < items.value.length - 1) {
        e.preventDefault()
        recalcAmount(idx)
        focusEditField('code', idx + 1)
        return true
      }
    }
  } else if (e.key === 'ArrowUp') {
    if (field !== 'uom' && idx > 0) {
      e.preventDefault()
      recalcAmount(idx)
      const targetItem = items.value[idx - 1]
      let targetField = field
      if (targetField === 'uom' && getItemUoms(targetItem.item_code).length <= 1) {
        targetField = 'rate'
      }
      focusEditField(targetField, idx - 1)
      return true
    }
  } else if (e.key === 'ArrowDown') {
    if (field !== 'uom' && idx < items.value.length - 1) {
      e.preventDefault()
      recalcAmount(idx)
      const targetItem = items.value[idx + 1]
      let targetField = field
      if (targetField === 'uom' && getItemUoms(targetItem.item_code).length <= 1) {
        targetField = 'rate'
      }
      focusEditField(targetField, idx + 1)
      return true
    }
  }
  return false
}

function onPendingUomChange() {
  const p = pendingItem.value
  if (!p) return
  const cached = lookupItemInCache(p.item_code)
  if (cached) {
    const newRate = getItemRateForPriceList(cached, p.uom)
    p._base_rate = newRate
    p.rate = newRate
  }
}

function setPendingItem(item) {
  item._base_rate = item.rate || 0
  const globalPct = parseFloat(globalDiscountPct.value)
  if (!isNaN(globalPct)) {
    item.discount = globalPct
  }
  pendingItem.value = item
  nextTick(() => {
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  })
}

function openPriceListUpdate() {
  if (!pendingItem.value || !pendingItem.value.qty) return
  editRowPriceUpdateIdx.value = null
  showPriceListUpdate.value = true
}

function openRowPriceListUpdate(idx) {
  editRowPriceUpdateIdx.value = idx
  showPriceListUpdate.value = true
}

function onPriceListUpdateSaved(data) {
  showPriceListUpdate.value = false
  if (editRowPriceUpdateIdx.value !== null) {
    const idx = editRowPriceUpdateIdx.value
    editRowPriceUpdateIdx.value = null
    const item = items.value[idx]
    if (item && data.changedPrices?.length) {
      const pl = data.changedPrices.find(p => p.price_list === priceList.value)
      if (pl) {
        const uomRate = pl.uom_rates?.[item.uom]
        const newRate = uomRate != null ? uomRate : (pl.rate ?? item.rate)
        item.rate = newRate
        item._base_rate = newRate
        recalcAmount(idx)
      }
    }
    finishRowEdit(idx)
  } else {
    if (pendingItem.value && data.changedPrices?.length) {
      const pl = data.changedPrices.find(p => p.price_list === priceList.value)
      if (pl) {
        const uomRate = pl.uom_rates?.[pendingItem.value.uom]
        const newRate = uomRate != null ? uomRate : (pl.rate ?? pendingItem.value.rate)
        pendingItem.value.rate = newRate
        pendingItem.value._base_rate = newRate
      }
    }
    confirmPendingItem()
  }
}

function onPriceListUpdateClose() {
  showPriceListUpdate.value = false
  if (editRowPriceUpdateIdx.value !== null) {
    const idx = editRowPriceUpdateIdx.value
    editRowPriceUpdateIdx.value = null
    finishRowEdit(idx)
  } else {
    confirmPendingItem()
  }
}

function focusPendingDisc() {
  nextTick(() => {
    pendingDiscInput.value?.focus()
    pendingDiscInput.value?.select()
  })
}

function focusPendingRate() {
  nextTick(() => {
    pendingRateInput.value?.focus()
    pendingRateInput.value?.select()
  })
}

function confirmPendingItem() {
  if (!pendingItem.value || !pendingItem.value.qty) return
  if (!isExempted.value && supplierId.value && !supplierGstin.value.trim()) {
    alert("Add party Gstin or change the tax template to exempted")
    return
  }
  const p = pendingItem.value
  const qty = isReturn.value ? -Math.abs(p.qty) : p.qty
  const itemDiscount = p.discount || 0
  const netRate = parseFloat(((p.rate || 0) * (1 - itemDiscount / 100)).toFixed(2))
  const newItem = {
    item_code: p.item_code, item_name: p.item_name, qty, uom: p.uom || 'Nos',
    rate: p.rate || 0, _base_rate: p._base_rate ?? p.rate ?? 0,
    discount: itemDiscount, tax_rate: p.tax_rate || 0,
    amount: parseFloat((qty * netRate).toFixed(2)),
    deleted: false,
  }
  items.value.push(newItem)
  pendingItem.value = null; newItemCode.value = ''; quickSearchResults.value = []
  nextTick(() => { newCodeInput.value?.focus(); newCodeInput.value?.scrollIntoView({ block: 'nearest' }) })
}

function cancelPendingItem(skipFocus = false) {
  pendingItem.value = null
  if (!skipFocus) nextTick(() => { newCodeInput.value?.focus() })
}

function handleSupplierSelected(party) {
  supplierName.value = party.label || party.name
  supplierId.value = party.name
  supplierDetails.value = party.mobile_no || party.email || ''
  supplierMobile.value = party.mobile_no || ''
  supplierGstin.value = party.gstin || ''
  supplierState.value = party.state || ''
  const addrParts = [party.address_line1, party.city, party.state].filter(Boolean)
  supplierAddress.value = addrParts.join(', ')
  if (party.last_invoice_date) {
    const d = new Date(party.last_invoice_date)
    supplierLastInvDate.value = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })
  } else {
    supplierLastInvDate.value = 'None'
  }
  fetchSupplierPurchaseHistory(party.name)
  showSupplierModal.value = false
  nextTick(() => { supplierInvoiceNoRef.value?.focus() })
}

async function handleSeriesSelected(series) {
  try {
    selectedSeries.value = series
    const res = await frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: series, doctype: 'Purchase Invoice' })
    invoiceNo.value = res.invoice_no
    priceList.value = res.price_list
    taxTemplate.value = res.tax_template
    defaultTemplate.value = res.print_format || ''
    if (res.warehouse) warehouse.value = res.warehouse
    if (res.cost_center) costCenter.value = res.cost_center

    // Update inclusive tax from billing series settings
    try {
      const cached = JSON.parse(localStorage.getItem('wb-settings-v2') || 'null')
      if (cached?.data?.billing_series) {
        const entry = cached.data.billing_series.find(bs => bs.series === series)
        if (entry) {
          isInclusiveTax.value = !!entry.tax_type_incl
          localStorage.setItem('wb-tax-type-incl', entry.tax_type_incl ? '1' : '0')
        }
      }
    } catch (e) {
      console.warn('[PurchaseInvoice] Failed to sync inclusive tax from series settings:', e)
    }

    showSeriesModal.value = false
    supplierInitialQuery.value = ''
    showSupplierModal.value = true
  } catch (e) {
    console.error('[PurchaseInvoice] Failed to fetch series defaults:', e)
    showSeriesModal.value = false
  }
}

function handleItemEntry() {
  if (!supplierInvoiceNo.value.trim()) {
    alert('Supplier Invoice No is mandatory.')
    supplierInvoiceNoRef.value?.focus()
    return
  }
  if (!isExempted.value && supplierId.value && !supplierGstin.value.trim()) {
    alert("Add party Gstin or change the tax template to exempted")
    return
  }
  if (!newItemCode.value) return
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) return

  const code = newItemCode.value.trim()
  const match = lookupItemInCache(code)

  if (!match) {
    openItemSearch(code)
    return
  }

  setPendingItem({
    item_code: match.item_code, item_name: match.item_name, qty: 0,
    rate: getItemRateForPriceList(match, match.uom), uom: match.uom || 'Nos',
    discount: 0, tax_rate: match.tax_rate || 0, deleted: false
  })
}

function onNewCodeInput() {
  const code = newItemCode.value.trim()
  if (code.length >= 2) {
    const rawResults = searchItemsInCache(code)
    quickSearchResults.value = rawResults.map(item => ({
      ...item,
      has_history: hasSupplierHistory(item.item_code)
    }))
    quickSearchAnchor.value = newCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

function handleNewCodeKeydown(e) {
  if (e.key === 'Enter') {
    const now = Date.now()
    const isDouble = (now - lastEnterTime.value < 400)
    lastEnterTime.value = now

    if (isDouble) {
      e.preventDefault()
      cancelPendingItem(true)
      newItemCode.value = ''
      quickSearchResults.value = []
      lastEnterTime.value = 0
      return
    }
  }

  if (e.key === 'ArrowRight') { e.preventDefault(); openItemSearch(newItemCode.value.trim()); return }

  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return
    } else if (e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    } else if (e.key === 'Escape') {
      e.preventDefault(); quickSearchResults.value = []; return
    }
  }

  if (e.key === 'Enter') {
    if (!newItemCode.value) return
    handleItemEntry()
  } else if (e.key === 'ArrowUp' && items.value.length > 0) { e.preventDefault(); focusRow(items.value.length - 1) }
  else if (e.key === 'End') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountPct() }
}

function handlePendingQtyKeydown(e) {
  if (e.key === 'Enter') {
    if (pendingItem.value.qty) {
      e.preventDefault()
      if (getItemUoms(pendingItem.value.item_code).length > 1) {
        pendingUomSelect.value?.focus()
        if (pendingUomSelect.value?.showPicker) pendingUomSelect.value.showPicker()
      } else {
        focusPendingRate()
      }
    }
  } else if (e.key === 'Escape') {
    cancelPendingItem()
  } else if (e.key === 'Backspace' && (!pendingItem.value.qty || pendingItem.value.qty === 0)) {
    e.preventDefault()
    cancelPendingItem()
  }
}

function handlePendingRateKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    focusPendingDisc()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    cancelPendingItem()
  } else if (e.key === 'Backspace' && (!pendingItem.value.rate || pendingItem.value.rate === 0)) {
    e.preventDefault()
    if (getItemUoms(pendingItem.value.item_code).length > 1) {
      pendingUomSelect.value?.focus()
    } else {
      pendingQtyInput.value?.focus()
      pendingQtyInput.value?.select()
    }
  }
}

function handlePendingDiscKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    openPriceListUpdate()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    cancelPendingItem()
  } else if (e.key === 'Backspace' && (!pendingItem.value.discount || pendingItem.value.discount === 0)) {
    e.preventDefault()
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  }
}

function handleRowKeydown(e, idx) {
  const item = items.value[idx]
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (e.key === 'Enter' && !item.deleted && !item._is_free) { e.preventDefault(); focusEditField('code', idx) }
  else if (e.key === 'ArrowDown') { e.preventDefault(); if (idx < items.value.length - 1) focusRow(idx + 1, 'down'); else focusBarcodeInput() }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (idx > 0) focusRow(idx - 1, 'up') }
  else if (e.key === 'End') {
    e.preventDefault()
    if (idx === items.value.length - 1) focusBarcodeInput()
    else focusRow(items.value.length - 1, 'down')
  }
  else if (e.key === 'Home') { e.preventDefault(); focusRow(0, 'up') }
  else if (e.key === 'Escape') { e.preventDefault(); if (!items.value.length) goBack(); else focusBarcodeInput() }
  else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteItem(idx) }
}

function focusEditField(field, idx) {
  if (items.value[idx]?.deleted || items.value[idx]?._is_free) return
  if (editingRowIdx.value !== idx) {
    originalRowCode.value = items.value[idx].item_code
  }
  editingRowIdx.value = idx; editingField.value = field; selectedRowIdx.value = idx
  const inputMap = { code: editCodeInput, qty: editQtyInput, uom: editUomSelect, rate: editRateInput, disc: editDiscInput }
  nextTick(() => {
    const el = inputMap[field]?.value
    if (!el) return
    el.focus()
    if (el.select) el.select()
    if (field === 'uom' && el.showPicker) el.showPicker()
  })
}

function exitEditMode(idx, cancel = false) {
  if (cancel && !items.value[idx]?.item_code) {
    clearItem(idx)
    focusBarcodeInput()
    return
  }
  recalcAmount(idx); editingRowIdx.value = -1; editingField.value = null
  quickSearchResults.value = []; editQuickSearchRowIdx.value = null
  nextTick(() => { focusRow(idx) })
}

function clearItem(idx) {
  if (idx !== -1 && items.value[idx]) {
    items.value.splice(idx, 1)
    if (editingRowIdx.value === idx) {
      editingRowIdx.value = -1
      editingField.value = null
    }
  }
}

function getItemUoms(itemCode) {
  const cached = lookupItemInCache(itemCode)
  if (!cached || !cached.uoms) return []
  return cached.uoms.map(u => u.uom)
}

function onUomChange(idx) {
  const item = items.value[idx]
  if (!item) return
  const cached = lookupItemInCache(item.item_code)
  if (cached) {
    const newRate = getItemRateForPriceList(cached, item.uom)
    item._base_rate = newRate
    item.rate = parseFloat((newRate || 0).toFixed(2))
    recalcAmount(idx)
  }
}

function finishRowEdit(idx) {
  const item = items.value[idx]
  if (item && isReturn.value) item.qty = -Math.abs(item.qty || 0)
  recalcAmount(idx); editingRowIdx.value = -1; editingField.value = null

  const nextTarget = idx < items.value.length - 1
    ? { type: 'row', index: idx + 1 }
    : { type: 'barcode' }

  if (nextTarget.type === 'row') focusRow(nextTarget.index)
  else focusBarcodeInput()
}

useShortcuts(salesInvoiceShortcuts({
  openShortcuts:    () => { showShortcutPage.value = !showShortcutPage.value },
  clearBill:        () => handleF2(),
  focusModifyPanel: () => handleF3(),
  openSeries:       () => { showSeriesModal.value = true },
  modify:           () => handleModify(),
  print:            () => handlePrint(),
  'ALT+P':          () => handleBarcodePrint(),
  openParcelAddress:() => {},
  save:             () => handleSave(),
  cancel:           () => handleCancel(),
  openIncentive:    () => { showIncentiveModal.value = true },
  pageUp:           () => handlePageUp(),
  deleteRow:        () => {
    if (selectedRowIdx.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      deleteItem(selectedRowIdx.value)
    }
  },
}), props.isSubwindow ? 'subwindow' : 'local')

function handleBeforeUnload() {
  releaseLock()
}

function handleGlobalEscape(e) {
  if (e.key === 'Escape') {
    if (showHistoryModal.value) {
      showHistoryModal.value = false
      return
    }
    const modalOpen = showSeriesModal.value || showSupplierModal.value || 
                      showItemSearch.value || showPrintModal.value || 
                      showJumpModal.value || showIncentiveModal.value || 
                      showClearWarning.value || showExitWarning.value || 
                      showShortcutPage.value || showPriceListUpdate.value || 
                      showBarcodeModal.value || showHistoryModal.value ||
                      quickSearchResults.value.length > 0 ||
                      pendingItem.value || editingRowIdx.value !== -1;

    if (!modalOpen) {
      goBack();
    }
  }
}
const linkingSupplier = ref(false)

async function linkSupplierToAllItems() {
  if (!supplierId.value) {
    alert('Please select a supplier first.')
    return
  }
  const itemCodes = items.value.filter(i => !i.deleted && i.item_code).map(i => i.item_code)
  if (!itemCodes.length) {
    alert('No items found in the invoice.')
    return
  }
  if (!confirm(`Are you sure you want to add supplier "${supplierName.value}" to all ${itemCodes.length} items in the Item Master?`)) {
    return
  }
  linkingSupplier.value = true
  try {
    const res = await linkSupplierToItems(supplierId.value, itemCodes)
    if (res.status === 'success') {
      alert(`Successfully linked supplier to ${res.linked_count} item(s) in the Item Master!`)
    } else {
      alert('Failed: ' + res.message)
    }
  } catch (e) {
    console.error(e)
    alert('Error linking supplier to items: ' + e.message)
  } finally {
    linkingSupplier.value = false
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  if (props.isSubwindow) {
    window.addEventListener('keydown', handleGlobalEscape)
  }
  if (props.isSubwindow && props.invoiceName) {
    handleSelectSidebarItem({ name: props.invoiceName })
  } else {
    fetchRecentInvoices()
    fetchAllowedSeries('Purchase Invoice')
    showSeriesModal.value = true
  }
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) {
    refreshItemCache('Purchase', priceList.value, warehouse.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalEscape)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  releaseLock()
})
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: var(--color-highlight); }
</style>
