<template>
  <div class="h-screen bg-slate-900 overflow-hidden">
    <Item_Invoice_Template
      ref="invoiceTemplateRef"
      title="SALES INVOICE"
      title-bar-color="#b2dfb0"
      :doc-number="invoiceNo"
      :party-name="customerName"
      :party-details="customerDetails"
      :party-address="customerAddress"
      :party-mobile="customerMobile"
      :party-gstin="customerGstin"
      :party-balance="customerBalance"
      :party-last-inv-date="customerLastInvDate"
      :party-modifier="customerModifier"
      v-model:ignore-modifier="ignoreModifier"
      :doc-date="invoiceDate"
      :items="items"
      :subtotal="subtotal"
      :item-discount-total="itemDiscountTotal"
      :total-tax="totalTax"
      :total-amount="totalAmount"
      :price-list="priceList"
      :tax-template="taxTemplate"
      :is-inclusive-tax="isInclusiveTax"
      :is-return="isReturn"
      :warehouse="warehouse"
      :cost-center="costCenter"
      :income-account="incomeAccount"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentInvoices"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
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
      v-model:other-entry="otherEntry"
      :other-amt="otherAmt"
      v-model:discount-pct="discountPct"
      v-model:discount-direct-amt="discountDirectAmt"
      :discount-amt="discountAmt"
      @back="goBack"
      @save="handleSave"
      @print="handlePrint"
      @discount-pct-keydown="handleDiscountPctKeydown"
      @other-entry-enter="saveBtnRef?.focus()"
      @cancel="handleCancel"
      @incentive="handleIncentive"
      @party-click="customerInitialQuery = ''; showCustomerModal = true"
    >
      <!-- Custom slots for additional logic if needed -->
      <template #header-right>
        <span class="text-blue-400 font-bold uppercase tracking-widest">{{ session.fullName.value || session.user.value }}</span>
      </template>

      <template #row="{ item, index }">
        <tr
          :ref="el => { if (el) rowRefs[index] = el }"
          :tabindex="isReadOnly ? -1 : 0"
          class="border-b border-[var(--color-border)] outline-none cursor-pointer transition-all"
          :class="{
            'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)] font-bold !text-[var(--color-text-on-focus)]': !isReadOnly && (selectedRowIdx === index || editingRowIdx === index) && !item.deleted && !item._is_free,
            'bg-green-900/20': item._is_free && !item.deleted,
            'opacity-40 bg-red-900/10 grayscale-[0.5]': item.deleted,
            'hover:bg-[var(--color-surface-raised)]/50': !isReadOnly && selectedRowIdx !== index && editingRowIdx !== index && !item.deleted
          }"
          @focus="!isReadOnly && (selectedRowIdx = index)"
          @keydown="!isReadOnly && handleRowKeydown($event, index)"
        >
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-3xl font-mono text-center relative" :class="selectedRowIdx === index && !item.deleted ? 'text-black' : 'text-[var(--color-text-muted)]'">
            <span v-if="item._cp_applied" class="absolute left-0 inset-y-0 w-[3px] bg-blue-500 rounded-r"></span>
            <span v-if="item.deleted" class="text-[10px] bg-red-600 text-white px-1 rounded block uppercase font-bold leading-tight mb-1">Deleted</span>
            {{ index + 1 }}
          </td>

          <!-- item_code -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'code'"
              ref="editCodeInput"
              v-model="item.item_code"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @input="onEditCodeInput(index)"
              @keydown="onEditCodeKeydown($event, index)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-highlight)]'">{{ item.item_code }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-medium" :class="selectedRowIdx === index && !item.deleted && !item._is_free ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">
            {{ item.item_name }}
            <span v-if="item._is_free" class="ml-1 rounded bg-green-600 text-white px-1 text-[10px] font-bold uppercase leading-tight">Free</span>
          </td>

          <!-- qty -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'qty'"
              ref="editQtyInput"
              v-model.number="item.qty"
              type="number" min="0"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="item.qty > 0 && (getItemUoms(item.item_code).length > 1 ? focusEditField('uom', index) : focusEditField('rate', index))"
              @keydown.escape="exitEditMode(index, true)"
              @keydown.backspace="(!item.qty || item.qty === 0) && (focusEditField('code', index), $event.preventDefault())"
            />
            <span v-else class="block px-2 py-1 text-6xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.qty }}</span>
          </td>

          <td class="p-0 border-r border-[var(--color-border)]">
            <select v-if="editingRowIdx === index && editingField === 'uom'"
              ref="editUomSelect"
              v-model="item.uom"
              class="w-full bg-white/10 px-2 py-1 text-3xl font-mono text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)]"
              @change="onUomChange(index)"
              @keydown.enter.prevent="focusEditField('rate', index)"
              @keydown.escape="exitEditMode(index, true)"
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
              @keydown.enter.prevent="focusEditField('disc', index)"
              @keydown.escape="exitEditMode(index, true)"
            />
            <span v-else class="block px-2 py-1 text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.rate }}</span>
          </td>

          <!-- disc % -->
          <td class="p-0 border-r border-[var(--color-border)]">
            <input v-if="editingRowIdx === index && editingField === 'disc'"
              ref="editDiscInput"
              v-model.number="item.discount"
              type="number" min="0" max="100" step="0.5"
              class="w-full bg-white/10 px-2 py-1 text-4xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="finishRowEdit(index)"
              @keydown.escape="exitEditMode(index, true)"
            />
            <span v-else class="block px-2 py-1 text-4xl font-mono text-right" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]'">{{ item.discount || '0' }}</span>
          </td>

          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-warning)]/80'">
            {{ item.discount ? (item.rate * (1 - item.discount / 100)).toFixed(2) : '—' }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-4xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
            {{ isExempted ? 0 : (item.tax_rate ?? 0) }}
          </td>
          <td class="px-2 py-1 border-r border-[var(--color-border)] text-5xl font-mono text-right tabular-nums" :class="selectedRowIdx === index && !item.deleted ? '!text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ item.amount }}</td>
          <td class="px-2 py-1 text-center">
            <button
              class="rounded px-1 py-0.5 hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]"
              :class="item.deleted ? 'text-red-500 hover:text-red-400 font-bold' : (selectedRowIdx === index ? 'text-[var(--color-text)]/60 hover:text-red-700' : 'text-[var(--color-text-muted)]')"
              @click.stop="deleteItem(index)"
            >
              {{ item.deleted ? 'Undo' : '×' }}
            </button>
          </td>
        </tr>
      </template>

      <template #bottom-left>
        <div class="flex flex-col h-full overflow-hidden">
          <div class="flex-1 overflow-y-auto px-4 pb-4 pt-2 scrollbar-none">
            <div v-if="selectedRowIdx === -1 && !pendingItem" class="text-sm text-slate-400 italic">
              Scan an item or select a row to see history.
            </div>
            <div v-else-if="historyLoading" class="text-sm text-blue-400 animate-pulse">
              Fetching history...
            </div>
            <div v-else-if="!selectedItemHistory.length" class="text-sm text-slate-500 italic">
              No previous history found for this customer.
            </div>
            <div v-else class="max-h-[110px] overflow-y-auto mb-4 custom-scrollbar">
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

            <!-- Warehouse Stock -->
            <div v-if="activeItemCode && itemStock.length" class="border-t border-[var(--color-border)] pt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Stock:</div>
              <div v-if="stockLoading" class="text-sm text-blue-400 animate-pulse">Updating stock...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="s in itemStock" :key="s.warehouse" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ s.warehouse.split(' - ')[0] }}</span>
                  <span :class="s.qty > 0 ? 'text-green-400' : 'text-red-400'" class="font-bold">{{ s.qty }}</span>
                </div>
              </div>
            </div>

            <!-- Available Prices -->
            <div v-if="activeItemCode && itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2">
              <div class="mb-1 text-[var(--color-text-muted)] text-xs font-bold uppercase tracking-wider">Available Prices:</div>
              <div v-if="pricesLoading" class="text-sm text-blue-400 animate-pulse">Updating prices...</div>
              <div v-else class="grid grid-cols-2 gap-x-4 gap-y-1">
                <div v-for="p in itemPrices" :key="p.price_list" class="flex justify-between items-center text-lg font-mono leading-none">
                  <span class="text-[var(--color-text-muted)] truncate mr-2">{{ p.price_list }}</span>
                  <span class="text-[var(--color-highlight)] font-bold tracking-widest">{{ encryptPrice(p.rate) }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="activeItemCode && !historyLoading && !pricesLoading && !itemPrices.length" class="border-t border-[var(--color-border)] pt-2 mt-2 text-sm text-slate-500 italic">
              No additional price lists available.
            </div>
          </div>
        </div>
      </template>

      <template #bottom-middle>
        <div class="flex flex-col gap-3 p-2 max-h-[300px] overflow-y-auto custom-scrollbar" @keydown="handleModifyPanelKeydown">
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
              <option v-if="!localPriceLists.length" value="Standard Selling">Standard Selling</option>
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

          <!-- 3 Checkboxes -->
          <div class="flex flex-col gap-1.5 py-1 border-y border-[var(--color-border)]/30">
            <label class="flex items-center gap-3 cursor-pointer" :class="isReadOnly ? 'cursor-default' : ''">
              <input ref="inclusiveTaxRef" type="checkbox" v-model="isInclusiveTax" :disabled="isReadOnly" class="h-6 w-6 rounded border-[var(--color-border)] accent-[var(--color-highlight)] disabled:opacity-50" />
              <span class="text-[var(--color-text-muted)] text-xl font-bold uppercase">Inclusive Tax</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer" :class="isReadOnly ? 'cursor-default' : ''">
              <input ref="ignoreRuleRef" type="checkbox" v-model="ignoreDiscountRule" :disabled="isReadOnly" class="h-6 w-6 rounded border-[var(--color-border)] accent-[var(--color-warning)] disabled:opacity-50" />
              <span class="text-[var(--color-text-muted)] text-xl font-bold uppercase">Ignore Pricing Rule</span>
            </label>
            <label class="flex items-center gap-3 cursor-pointer" :class="isReadOnly ? 'cursor-default' : ''">
              <input type="checkbox" v-model="isReturn" :disabled="isReadOnly" class="h-6 w-6 rounded border-[var(--color-border)] accent-[var(--color-danger)] disabled:opacity-50" />
              <span class="text-[var(--color-text-muted)] text-xl font-bold uppercase">Sale Return</span>
            </label>
          </div>

          <!-- Additional Info -->
          <div class="grid grid-cols-2 gap-2">
            <!-- Warehouse (Readonly) -->
            <div class="flex flex-col gap-0.5">
              <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
              <input
                :value="warehouse"
                readonly
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30 px-1 py-0.5 text-2xl text-[var(--color-text-muted)] outline-none cursor-not-allowed"
              />
            </div>

            <!-- Cost Center -->
            <div class="flex flex-col gap-0.5">
              <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
              <select
                ref="costCenterRef"
                v-model="costCenter"
                disabled
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-2xl text-[var(--color-text)] outline-none disabled:opacity-50 disabled:cursor-default"
              >
                <option v-for="cc in localCostCenters" :key="cc" :value="cc">{{ cc }}</option>
                <option v-if="!localCostCenters.length" :value="costCenter">{{ costCenter }}</option>
              </select>
            </div>

            <!-- wb-income-account -->
            <div class="flex flex-col gap-0.5">
              <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">wb-income-account</label>
              <input
                :value="incomeAccount"
                readonly
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)]/30 px-1 py-0.5 text-2xl text-[var(--color-text-muted)] outline-none cursor-not-allowed"
              />
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
            <button ref="saveBtnRef" @click="handleSave" :disabled="isSubmitted" class="flex-1 rounded py-2.5 text-center text-3xl font-semibold transition-colors uppercase focus:outline-none" :class="isSubmitted ? 'bg-slate-700/40 text-slate-500 cursor-not-allowed' : 'text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 focus:bg-green-600/70'">{{ saveButtonText }}</button>
            <button @click="handlePrint" :disabled="!isReadOnly" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isReadOnly ? 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-midlight)] cursor-pointer' : 'border-slate-700/40 bg-slate-800/30 text-slate-600 cursor-not-allowed'">Print</button>
          </div>
          <div class="flex gap-2">
            <button @click="showClearWarning = true" class="flex-1 rounded border border-[var(--color-highlight)]/50 bg-[var(--color-highlight)]/10 py-2.5 text-center text-3xl font-semibold text-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/20 transition-colors">New</button>
            <button @click="handleIncentive" :disabled="isSubmitted" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isSubmitted ? 'border-slate-700/40 bg-slate-800/20 text-slate-500 cursor-not-allowed' : 'border-[#D8C9A8] bg-[#EDE3CC] text-[#4A3520] hover:bg-[#E0D4B8]'">Incentive</button>
          </div>
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
                min="0"
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
                @keydown.enter.prevent="confirmPendingItem"
                @keydown.escape="cancelPendingItem"
              >
                <option v-for="u in getItemUoms(pendingItem.item_code)" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ u }}</option>
              </select>
              <span v-else class="block px-2 py-1 text-xl text-[var(--color-text-muted)]">{{ pendingItem.uom || 'Nos' }}</span>
            </td>
            <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-3xl font-mono text-right">{{ pendingItem.rate }}</td>
            <td colspan="5" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter qty and press Enter</td>
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
      :price-list="priceList"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
    />

    <ItemSearch
      ref="itemSearchRef"
      :show="showItemSearch"
      search-type="Sales"
      :price-list="priceList"
      :warehouse="warehouse"
      :skip-date-filter="true"
      :initial-query="itemSearchInitialQuery"
      @close="closeItemSearch"
      @select="onItemSearchSelect"
    />



    <CustomerSearchModal
      v-if="showCustomerModal"
      :show="showCustomerModal"
      skip-date-filter
      initial-type="Customer"
      :initial-query="customerInitialQuery"
      @close="showCustomerModal = false; customerInitialQuery = ''"
      @select="handleCustomerSelected"
    />

    <Userseries
      :show="showSeriesModal"
      doctype="Sales Invoice"
      @close="showSeriesModal = false"
      @selected="handleSeriesSelected"
    />

    <CustomerPrice
      v-if="showPriceDetectModal"
      :data="priceDetectData"
      :customer="customerId"
      :price-list="priceList"
      @saved="onCustomerPriceSaved"
      @updatePricelist="updatePriceList"
      @dismiss="dismissPriceModal"
    />

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="invoiceNo"
      @close="closePrintModal"
    />

    <JumpToRowModal
      v-model:show="showJumpModal"
      :max-rows="items.length"
      @jump="handleJump"
    />

    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Sales Invoice"
      :docname="isSaved ? invoiceNo : ''"
      :initial-rows="incentiveRows"
      @close="showIncentiveModal = false"
      @update:rows="onIncentiveSaved"
    />

    <CustomAddress
      v-if="showCustomAddressModal"
      :initial-data="customAddress"
      @saved="data => { customAddress = data }"
      @close="showCustomAddressModal = false"
    />

    <Warning
      :show="showClearWarning"
      title="Clear Bill"
      message="All items will be removed and a new bill number will be assigned."
      @close="showClearWarning = false"
      @confirm="showClearWarning = false; clearBill()"
    />

    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Sales Invoice"
      :extra="[
        { key: 'F2', desc: 'Clear bill / refresh bill number' },
        { key: 'F3', desc: 'Focus sidebar bill list' },
        { key: 'F4', desc: 'Select series' },
        { key: 'F5', desc: 'Print invoice' },
        { key: 'F6', desc: 'Open Custom Address' },
        { key: 'F8 / Ctrl+S', desc: 'Save invoice' },
        { key: 'Insert', desc: 'Open incentive entry' },
        { key: 'Page Up', desc: 'Series (empty) / Change customer (with items)' },
        { key: 'Delete', desc: 'Delete selected row' },
      ]"
      @close="showShortcutPage = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import Userseries from '../components/Userseries.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import ItemSearch from '../components/ItemSearch.vue'

import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import CustomerPrice from '../components/CustomerPrice.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import CustomAddress from '../components/CustomAddress.vue'
import Warning from '../components/Warning.vue'
import { useItemCache, lookupItemInCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'
import { encryptPrice } from '../encryption.js'
import { useDiscountRules } from '../composables/useDiscountRules.js'
import { useShortcuts } from '../services/shortcutManager'
import { session } from '../session'
import { salesInvoiceShortcuts } from '../shortcuts/salesInvoiceShortcuts'
import ShortcutPage from '../components/ShortcutPage.vue'

const router = useRouter()

// --- Data Fetching & State Management ---
const { items: cachedItems, lastSync, refreshItemCache, searchItemsInCache } = useItemCache()
const { 
  fetchCustomerSalesHistory, clearHistory, clearItemInsights, getItemHistoryFromCache, historyLoading, 
  fetchItemStock, itemStock, stockLoading,
  fetchItemPrices, itemPrices, pricesLoading
} = useCustomerHistory()

// --- Primary Collections ---
const items = ref([])
const recentInvoices = ref([])

// --- Billing Settings & Defaults ---
const localPriceLists = ref([])
try { localPriceLists.value = JSON.parse(localStorage.getItem('wb-pricelist') || '[]') } catch { localPriceLists.value = [] }
const localTaxTemplates = ref([])
try { localTaxTemplates.value = JSON.parse(localStorage.getItem('wb-sales-tax-template') || '[]') } catch { localTaxTemplates.value = [] }
const localWarehouses = ref([])
try { localWarehouses.value = JSON.parse(localStorage.getItem('wb-warehouses') || '[]') } catch { localWarehouses.value = [] }
const localCostCenters = ref([])
try { localCostCenters.value = JSON.parse(localStorage.getItem('wb-cost-centers') || '[]') } catch { localCostCenters.value = [] }
const localAccounts = ref([])
try { localAccounts.value = JSON.parse(localStorage.getItem('wb-visible-accounts') || '[]') } catch { localAccounts.value = [] }

const priceList = ref(localPriceLists.value[0] || 'Standard Selling')
const taxTemplate = ref(localTaxTemplates.value[0] || '')
const warehouse = ref(localStorage.getItem('wb-warehouse') || localWarehouses.value[0] || 'None')
const costCenter = ref(localStorage.getItem('wb-cost-center') || localCostCenters.value[0] || 'None')
const incomeAccount = ref(localStorage.getItem('wb-income-account') || localAccounts.value[0] || 'None')
const isInclusiveTax = ref(true)
const isReturn = ref(false)

// --- Additional Charges ---
const freightEntry = ref('')
const packingEntry = ref('')
const loadingEntry = ref('')
const otherEntry = ref('')
const discountPct = ref('')
const discountDirectAmt = ref('')

const freightAmt = computed(() => parseFloat(freightEntry.value) || 0)
const packingAmt = computed(() => parseFloat(packingEntry.value) || 0)
const loadingAmt = computed(() => parseFloat(loadingEntry.value) || 0)
const otherAmt = computed(() => parseFloat(otherEntry.value) || 0)

// --- Composable Logic (Discount Rules) ---
const { makeRowKey, ignoreDiscountRule } = useDiscountRules({ items, priceList, lookupItemInCache })

// --- Page & UI State ---
const showSeriesModal = ref(false)
const showCustomerModal = ref(false)
const showShortcutPage = ref(false)
const showIncentiveModal = ref(false)
const incentiveRows = ref([])
const showCustomAddressModal = ref(false)
const customAddress = ref({ customer_name: '', mobile_number: '', address_line_1: '', address_line_2: '' })
const showClearWarning = ref(false)
const customerInitialQuery = ref('')
const invoiceTemplateRef = ref(null)
const saveBtnRef = ref(null)
const priceListSelectRef = ref(null)
const taxTemplateRef = ref(null)
const inclusiveTaxRef = ref(null)
const ignoreRuleRef = ref(null)
const costCenterRef = ref(null)
const showPrintModal = ref(false)
const pendingClearAfterPrint = ref(false)

const lastEnterTime = ref(0)
const showPriceDetectModal = ref(false)
const showJumpModal = ref(false)
const priceDetectData = ref(null)
const postModalFocusTarget = ref(null) // { type: 'row'|'barcode', index?: number }

const invoiceNo = ref('NEW')
const selectedSeries = ref('')
const invoiceDate = ref(new Date().toISOString().split('T')[0])
const sidebarDate = ref(new Date().toISOString().split('T')[0])
const sidebarSearch = ref('')
const sidebarSeries = ref('')
const draftOnly = ref(false)
const sidebarLoading = ref(false)

const isReadOnly = ref(false)
const isSaved = ref(false)
const isSubmitted = ref(false)
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
    recentInvoices.value = await frappeGet('ssplbilling.api.sales.get_sales_invoices', {
      query: sidebarSearch.value,
      limit: 100,
      posting_date: sidebarDate.value,
      naming_series: sidebarSeries.value || '',
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

watch([sidebarDate, sidebarSearch, sidebarSeries, draftOnly], () => {
  fetchRecentInvoices()
})

async function handleSelectSidebarItem(item) {
  try {
    const data = await frappeGet('ssplbilling.api.cashier_api.get_sales_invoice', { invoice_name: item.name })

    // Header
    invoiceNo.value = data.name
    selectedSeries.value = data.naming_series || selectedSeries.value
    invoiceDate.value = data.posting_date || invoiceDate.value

    // Customer
    customerId.value = data.customer || ''
    customerName.value = data.customer_name || 'Select Customer...'
    customerState.value = data.state || ''

    // Settings
    if (data.price_list) priceList.value = data.price_list
    if (data.tax_template) taxTemplate.value = data.tax_template
    isInclusiveTax.value = data.is_inclusive === 1
    isReturn.value = data.is_return === 1
    ignoreModifier.value = data.customer_rate_multiplier === 0
    if (data.cost_center) costCenter.value = data.cost_center

    // Charges
    freightEntry.value = data.freight_amount || ''
    packingEntry.value = data.packing_amount || ''
    loadingEntry.value = data.loading_amount || ''
    otherEntry.value = data.other_charges_amount || ''

    // Discounts
    discountPct.value = data.discount_percentage || ''
    discountDirectAmt.value = data.additional_discount_amount || ''

    // Custom address
    customAddress.value = {
      customer_name: data.custom_customer_name || '',
      mobile_number: data.custom_mobile_number || '',
      address_line_1: data.custom_address_line1 || '',
      address_line_2: data.custom_address_line2 || '',
    }

    // Incentive rows
    incentiveRows.value = data.incentive_system || []

    // Items — reverse-calc pre-discount rate from stored effective rate + discount%
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
  }
}

const customerName = ref('Select Customer...')
const customerId = ref('')          // actual Customer doc name (for backend calls)
const customerDetails = ref('')
const customerAddress = ref('')
const customerMobile = ref('')
const customerGstin = ref('')
const customerBalance = ref(null)
const customerLastInvDate = ref('')
const customerState = ref('')
const customerModifier = ref(null)
const ignoreModifier = ref(false)
const customerPricing = ref({}) // { item_code: multiplication_factor }

const newItemCode = ref('')
const newCodeInput = ref(null)
const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)
const showItemSearch = ref(false)
const itemSearchRef = ref(null)
const itemSearchInitialQuery = ref('')
const editQuickSearchRowIdx = ref(null) // null = barcode entry, number = row edit mode
const itemSearchTargetRowIdx = ref(null) // null = barcode entry, number = row edit mode
const pendingItem = ref(null)
const pendingQtyInput = ref(null)
const pendingUomSelect = ref(null)
const selectedRowIdx = ref(-1)
const rowRefs = ref([])
const editingRowIdx = ref(-1)
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

// Tax computed on undiscounted items (factor = 1) — used to derive base total for discount %
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
    const undiscountedTotal = grossSubtotal + taxOnGross.value + additionalChargesTotal
    return undiscountedTotal * (p / 100)
  }
  return a
})

const itemDiscountTotal = computed(() => {
  return activeItems.value.reduce((sum, item) => {
    const rate = item.rate || 0
    const qty = item.qty || 0
    const disc = item.discount || 0
    // Total discount for this row = (Rate * Qty) * (Disc / 100)
    return sum + ((rate * qty) * (disc / 100))
  }, 0).toFixed(2)
})

const discountFactor = computed(() => {
  const grossSubtotal = activeItems.value.reduce((sum, item) => sum + item.amount, 0)
  if (grossSubtotal <= 0) return 1
  return (grossSubtotal - discountAmt.value) / grossSubtotal
})

const selectedItemHistory = computed(() => {
  if (pendingItem.value) return getItemHistoryFromCache(pendingItem.value.item_code)
  if (selectedRowIdx.value === -1) return []
  const item = items.value[selectedRowIdx.value]
  if (!item) return []
  return getItemHistoryFromCache(item.item_code)
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

const totalAmount = computed(() => {
  return (
    parseFloat(subtotal.value) + 
    parseFloat(totalTax.value) + 
    freightAmt.value + 
    packingAmt.value + 
    loadingAmt.value + 
    otherAmt.value
  ).toFixed(2)
})

// --- Watchers ---

// Re-calculate row amounts when qty, rate, or discount changes
watch(items, (newItems) => {
  newItems.forEach((_, idx) => recalcAmount(idx))
}, { deep: true })

// Fetch live stock and prices when an item is selected or scanned
watch([pendingItem, selectedRowIdx], ([pending, rowIdx]) => {
  let code = null
  if (pending) code = pending.item_code
  else if (rowIdx !== -1) code = items.value[rowIdx]?.item_code

  if (code) {
    fetchItemStock(code)
    fetchItemPrices(code)
  }
})

// Handle Inclusive Tax toggle and Regional logic when template changes
watch(taxTemplate, (val) => {
  if (!val) return
  isInclusiveTax.value = val.toLowerCase().includes('inclusive')
  applyRegionalTaxLogic()
})

// --- Methods ---

function goBack() { router.push('/') }

function formatDateShort(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  return `${day}-${month}-${year}`
}

async function clearBill() {
  items.value = []
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
  discountPct.value = ''
  discountDirectAmt.value = ''
  freightEntry.value = ''
  loadingEntry.value = ''
  packingEntry.value = ''
  otherEntry.value = ''
  incentiveRows.value = []
  customAddress.value = { customer_name: '', mobile_number: '', address_line_1: '', address_line_2: '' }
  clearHistory()
  invoiceNo.value = 'NEW'
  isReturn.value = false
  isReadOnly.value = false
  isSaved.value = false
  isSubmitted.value = false

  if (selectedSeries.value) {
    try {
      const next = await frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: selectedSeries.value })
      invoiceNo.value = next.invoice_no || 'NEW'
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
    priceListSelectRef.value,
    taxTemplateRef.value,
    inclusiveTaxRef.value,
    ignoreRuleRef.value,
    costCenterRef.value,
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
    customerInitialQuery.value = customerId.value || customerName.value
    showCustomerModal.value = true
  } else {
    showSeriesModal.value = true
  }
}

async function handleSave() {
  if (isSubmitted.value) return
  if (isReadOnly.value && isSaved.value) {
    isReadOnly.value = false
    if (items.value.length > 0) {
      focusRow(0)
    } else {
      focusBarcodeInput()
    }
    return
  }

  const active = items.value.filter(i => !i.deleted)
  if (!active.length) { alert('No items to save'); return }
  
  if (!customerId.value) { alert('Please select a customer first.'); return; }
  if (!selectedSeries.value) { alert('Please select a series first.'); return; }

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
    const acct = localStorage.getItem('wb-loading')
    if (acct) additionalCharges.push({ charge_type: 'Actual', account_head: acct, tax_amount: loading, description: 'Loading' })
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
    series: selectedSeries.value,
    customer: customerId.value,
    posting_date: invoiceDate.value,
    price_list: priceList.value,
    discount_pct: discountPct.value,
    discount_amt: discountDirectAmt.value,
    tax_template: taxTemplate.value,
    cost_center: costCenter.value,
    warehouse: warehouse.value,
    income_account: incomeAccount.value,
    is_inclusive_tax: isInclusiveTax.value ? 1 : 0,
    is_return: isReturn.value ? 1 : 0,
    customer_rate_multiplier: ignoreModifier.value ? 0 : 1,
    additional_charges: additionalCharges,
    incentive_rows: incentiveRows.value.map(r => ({ employee: r.employee, role: r.role, points: r.points || 0 })),
    place_of_supply: customerState.value || '',
    custom_customer_name: customAddress.value.customer_name || '',
    custom_address_line1: customAddress.value.address_line_1 || '',
    custom_address_line2: customAddress.value.address_line_2 || '',
    custom_mobile_number: customAddress.value.mobile_number || '',
    items: active.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      rate: parseFloat(((i.rate || 0) * (1 - (i.discount || 0) / 100)).toFixed(2)),
      price_list_rate: i._base_rate || i.price_list_rate || i.rate,
      discount: i.discount || 0,
      is_free_item: i._is_free ? 1 : 0
    }))
  }

  const isUpdate = isSaved.value

  try {
    let res
    if (isUpdate) {
      res = await frappePost('ssplbilling.api.sales.update_sales_invoice', {
        invoice_name: invoiceNo.value,
        payload: JSON.stringify(payload)
      })
    } else {
      res = await frappePost('ssplbilling.api.sales.post_sales_invoice', { payload: JSON.stringify(payload) })
    }

    if (res.status === 'success') {
      if (isUpdate) {
        isReadOnly.value = true
        isSaved.value = true
        fetchRecentInvoices()
        pendingClearAfterPrint.value = false
        showPrintModal.value = true
      } else {
        invoiceNo.value = res.name
        fetchRecentInvoices()
        pendingClearAfterPrint.value = true
        showPrintModal.value = true
      }
    }
  } catch (error) {
    console.error('Error saving invoice:', error)
    alert(isUpdate ? 'Failed to update invoice.' : 'Failed to save invoice.')
  }
}

function handleDiscountPctKeydown(e) {
  if (e.key === 'Enter') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountAmt() }
  else if (e.key === 'End') { e.preventDefault(); saveBtnRef.value?.focus() }
}

function handleModify() {
  if (!isReadOnly.value || !isSaved.value) return
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

async function closePrintModal() {
  showPrintModal.value = false
  if (!pendingClearAfterPrint.value) return
  pendingClearAfterPrint.value = false

  // Clear bill for next entry (keep customer)
  items.value = []
  pendingItem.value = null
  newItemCode.value = ''
  quickSearchResults.value = []
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  editingField.value = null
  discountPct.value = ''
  discountDirectAmt.value = ''
  freightEntry.value = ''
  loadingEntry.value = ''
  packingEntry.value = ''
  otherEntry.value = ''
  incentiveRows.value = []
  customAddress.value = { customer_name: '', mobile_number: '', address_line_1: '', address_line_2: '' }
  clearHistory()

  isSaved.value = false
  try {
    const next = await frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: selectedSeries.value })
    invoiceNo.value = next.invoice_no || 'NEW'
  } catch {
    invoiceNo.value = 'NEW'
  }

  nextTick(() => { newCodeInput.value?.focus() })
}

function handleCancel() {
  if (activeItems.value.length === 0) {
    router.push('/')
  } else {
    focusBarcodeInput()
  }
}

function handleIncentive() { showIncentiveModal.value = true }

function onIncentiveSaved(rows) {
  incentiveRows.value = rows
  showIncentiveModal.value = false
}

function handleJump(targetNo) {
  if (items.value.length === 0) return
  let idx = Math.max(0, Math.min(targetNo - 1, items.value.length - 1))
  focusRow(idx)
}

function detectPriceChange(item, focusTarget) {
  const cached = lookupItemInCache(item.item_code)
  if (!cached) return false

  // standard_rate = UOM-specific rate for the currently selected price list — used by CustomerPrice to compute factor
  const standardRate = getItemRateForPriceList(cached, item.uom)
  const currentRate = parseFloat(item.rate || 0)
  const currentDiscount = parseFloat(item.discount || 0)

  // effective rate the user intends (discount applied to standard if only discount changed)
  const effectiveRate = currentDiscount > 0.001
    ? parseFloat((standardRate * (1 - currentDiscount / 100)).toFixed(2))
    : currentRate

  const priceListStandard = parseFloat((standardRate * combinedFactor(item.item_code)).toFixed(2))
  const rateChanged = Math.abs(priceListStandard - currentRate) > 0.001
  const discountChanged = Math.abs(currentDiscount) > 0.001

  if (rateChanged || discountChanged) {
    priceDetectData.value = {
      ...item,
      standard_rate: standardRate,   // base price list rate → CustomerPrice computes factor from this
      current_rate: effectiveRate     // what the user actually wants
    }
    postModalFocusTarget.value = focusTarget
    showPriceDetectModal.value = true
    return true
  }
  return false
}

function onCustomerPriceSaved(freshPricing) {
  if (freshPricing && Object.keys(freshPricing).length) {
    customerPricing.value = freshPricing
  }
  dismissPriceModal()
}

async function updatePriceList() {
  if (!priceDetectData.value) return
  try {
    await frappeGet('ssplbilling.api.pricelist_api.update_item_price', {
      item_code: priceDetectData.value.item_code,
      price_list: priceList.value,
      rate: priceDetectData.value.rate,
      uom: priceDetectData.value.uom || ''
    })
    dismissPriceModal()
  } catch (e) {
    console.error('Failed to update price list:', e)
    dismissPriceModal()
  }
}

function dismissPriceModal() {
  showPriceDetectModal.value = false
  const target = postModalFocusTarget.value
  if (target) {
    if (target.type === 'row') focusRow(target.index)
    else focusBarcodeInput()
  }
  priceDetectData.value = null
  postModalFocusTarget.value = null
}

function applyRegionalTaxLogic() {
  if (!customerState.value || !taxTemplate.value) return
  const companyState = localStorage.getItem('wb-company-state') || ''
  if (!companyState || !customerState.value) return
  
  const isInterState = companyState.toLowerCase() !== customerState.value.toLowerCase()
  const currentTax = taxTemplate.value
  
  if (isInterState) {
    if (currentTax.toLowerCase().includes('in-state')) {
      const target = currentTax.replace(/in-state/i, 'Out-State')
      const found = localTaxTemplates.value.find(t => t.toLowerCase() === target.toLowerCase())
      if (found) taxTemplate.value = found
    }
  } else {
    if (currentTax.toLowerCase().includes('out-state')) {
      const target = currentTax.replace(/out-state/i, 'In-State')
      const found = localTaxTemplates.value.find(t => t.toLowerCase() === target.toLowerCase())
      if (found) taxTemplate.value = found
    }
  }
}

function handleItemEntry() {
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
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = newCodeInput.value

    // Auto-select on exact barcode match
    const exactMatch = quickSearchResults.value.find(i => 
      i.barcodes && i.barcodes.split(',').some(b => b.trim() === code)
    )
    if (exactMatch) {
      onQuickSearchSelect(exactMatch)
      setTimeout(() => {
        pendingQtyInput.value?.focus()
        pendingQtyInput.value?.select()
      }, 400)
    }
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
  }

  else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    handleCancel()
  }

  else if (e.key === 'ArrowUp' && items.value.length > 0) { e.preventDefault(); focusRow(items.value.length - 1) }
  else if (e.key === 'End') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountPct() }
}

function handlePendingQtyKeydown(e) {
  if (e.key === 'Enter') {
    const now = Date.now()
    const isDouble = (now - lastEnterTime.value < 400)
    lastEnterTime.value = now

    if (isDouble && (!pendingItem.value.qty || pendingItem.value.qty === 0)) {
      e.preventDefault()
      cancelPendingItem(true)
      lastEnterTime.value = 0
      return
    }

    if (pendingItem.value.qty > 0) {
      e.preventDefault()
      if (getItemUoms(pendingItem.value.item_code).length > 1) {
        pendingUomSelect.value?.focus()
      } else {
        confirmPendingItem()
      }
    }
  } else if (e.key === 'Escape') {
    cancelPendingItem()
  } else if (e.key === 'Backspace' && (!pendingItem.value.qty || pendingItem.value.qty === 0)) {
    e.preventDefault()
    cancelPendingItem()
  }
}

function handleRowKeydown(e, idx) {
  const item = items.value[idx]
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (e.key === 'Enter' && !item.deleted && !item._is_free) { e.preventDefault(); focusEditField('qty', idx) }
  else if (e.key === 'ArrowDown') { e.preventDefault(); if (idx < items.value.length - 1) focusRow(idx + 1, 'down'); else focusBarcodeInput() }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (idx > 0) focusRow(idx - 1, 'up') }
  else if (e.key === 'End') { e.preventDefault(); focusRow(items.value.length - 1, 'down') }
  else if (e.key === 'Home') { e.preventDefault(); focusRow(0, 'up') }
  else if (e.key === 'Escape') {
    e.preventDefault()
    e.stopPropagation()
    if (activeItems.value.length === 0) {
      router.push('/')
    } else {
      clearItem(idx)
      focusBarcodeInput()
    }
  }
  else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteItem(idx) }
}

function focusEditField(field, idx) {
  if (items.value[idx]?.deleted || items.value[idx]?._is_free) return
  editingRowIdx.value = idx; editingField.value = field; selectedRowIdx.value = idx
  const inputMap = { code: editCodeInput, qty: editQtyInput, uom: editUomSelect, rate: editRateInput, disc: editDiscInput }
  nextTick(() => {
    const el = inputMap[field]?.value
    if (!el) return
    el.focus()
    if (el.select) el.select()
  })
}

function exitEditMode(idx, cancel = false) {
  if (cancel) {
    clearItem(idx)
    editingRowIdx.value = -1
    editingField.value = null
    quickSearchResults.value = []
    editQuickSearchRowIdx.value = null
    focusBarcodeInput()
    return
  }
  recalcAmount(idx); editingRowIdx.value = -1; editingField.value = null
  quickSearchResults.value = []; editQuickSearchRowIdx.value = null
  nextTick(() => { rowRefs.value[idx]?.focus() })
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
    item.rate = parseFloat(((newRate || 0) * combinedFactor(item.item_code)).toFixed(2))
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

  if (!detectPriceChange(item, nextTarget)) {
    if (nextTarget.type === 'row') focusRow(nextTarget.index)
    else focusBarcodeInput()
  }
}

function recalcAmount(idx) {
  const item = items.value[idx]
  if (!item) return
  item.amount = parseFloat(((item.qty || 0) * (item.rate || 0) * (1 - (item.discount || 0) / 100)).toFixed(2))
}

function effectiveModifier() {
  const mod = (!ignoreModifier.value && customerModifier.value != null) ? customerModifier.value : 1
  return mod === 0 ? 1 : mod
}

function applyModifierToRate(baseRate) {
  return parseFloat(((baseRate || 0) * effectiveModifier()).toFixed(2))
}

function combinedFactor(item_code) {
  const globalFactor = effectiveModifier()
  let cpFactor = customerPricing.value[item_code]
  if (cpFactor === 0) cpFactor = 1
  
  const factor = cpFactor != null ? globalFactor * cpFactor : globalFactor
  return factor === 0 ? 1 : factor
}

// Get price for the currently selected price list from the cache
function getItemRateForPriceList(cachedItem, uom = null) {
  if (!cachedItem) return 0
  const plName = priceList.value
  
  // 1. Check per-UOM overrides first
  const targetUom = uom || cachedItem.uom || 'Nos'
  if (cachedItem.uom_price_lists?.[plName]?.[targetUom] != null) {
    return cachedItem.uom_price_lists[plName][targetUom]
  }

  // 2. Check direct price_lists array (base rates)
  const plEntry = (cachedItem.price_lists || []).find(p => p.name === plName)
  if (plEntry) return plEntry.rate

  // 3. Fallback to the main 'price' field
  // If the lastSync was for this price list, cachedItem.price is correct.
  // Otherwise, it might be from a previous price list.
  return parseFloat(cachedItem.price || 0)
}

function updateTableRates() {
  items.value.forEach((item, idx) => {
    if (item.deleted) return
    const cached = lookupItemInCache(item.item_code)
    if (cached) {
      const newRate = getItemRateForPriceList(cached, item.uom)
      item._base_rate = newRate
      item.rate = parseFloat(((newRate || 0) * combinedFactor(item.item_code)).toFixed(2))
      recalcAmount(idx)
    }
  })
}

// Negate / restore all row qtys when Sale Return is toggled
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

// Reprice all rows when price list is changed in settings panel
watch(priceList, (newList) => {
  if (!newList) return
  localStorage.setItem('wb-pricelist-selected', newList) // Persist selection
  
  // 1. Update UI INSTANTLY using whatever is already in the local cache
  updateTableRates()
  
  // 2. Refresh cache in background to ensure latest rates from server
  refreshItemCache('Sales', newList, warehouse.value)
    .then(() => {
      // 3. Re-run update once background sync completes to catch any changed values
      updateTableRates()
    })
    .catch(e => console.warn('[SalesInvoice] Background price refresh failed:', e))
})

function reapplyCustomerPricing() {
  items.value.forEach((item, idx) => {
    if (item.deleted || item._is_free) return
    const base = item.price_list_rate || item._base_rate || item.rate
    item._base_rate = base
    item.rate = parseFloat(((base || 0) * combinedFactor(item.item_code)).toFixed(2))
    item._cp_applied = customerPricing.value[item.item_code] != null
    recalcAmount(idx)
  })
}

watch(ignoreModifier, () => {
  items.value.forEach(item => {
    const base = item._base_rate ?? item.rate
    item._base_rate = base
    item.rate = parseFloat(((base || 0) * combinedFactor(item.item_code)).toFixed(2))
    item.amount = parseFloat(((item.qty || 0) * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2))
  })
})

function scrollRowToEdge(idx, direction) {
  const rowEl = rowRefs.value[idx]
  if (!rowEl) return
  const container = rowEl.closest('.overflow-y-auto')
  if (!container) return
  const rowRect = rowEl.getBoundingClientRect()
  const cRect = container.getBoundingClientRect()
  if (direction === 'down') {
    // Align row bottom with container bottom
    container.scrollTop += (rowRect.bottom - cRect.bottom)
  } else {
    // Align row top with container top (below sticky thead)
    const thead = container.querySelector('thead')
    const theadH = thead ? thead.offsetHeight : 0
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

function clearItem(idx) {
  if (idx !== -1 && items.value[idx]) {
    items.value.splice(idx, 1)
    if (editingRowIdx.value === idx) {
      editingRowIdx.value = -1
      editingField.value = null
    }
  }
}

function onQuickSearchSelect(item) {
  if (!item) return
  quickSearchResults.value = []
  if (editQuickSearchRowIdx.value !== null) {
    const rowIdx = editQuickSearchRowIdx.value
    editQuickSearchRowIdx.value = null
    applyItemToRow(rowIdx, item)
    if (getItemUoms(item.item_code).length > 1) {
      focusEditField('uom', rowIdx)
    } else {
      focusEditField('qty', rowIdx)
    }
    return
  }
  newItemCode.value = ''
  setPendingItem({
    item_code: item.item_code, item_name: item.item_name, qty: 0, rate: getItemRateForPriceList(item, item.uom),
    uom: item.uom || 'Nos', discount: 0, tax_rate: item.tax_rate || 0, deleted: false
  })
}

function applyItemToRow(rowIdx, item) {
  const row = items.value[rowIdx]
  if (!row) return
  const isSameItem = row.item_code === item.item_code
  row.item_code = item.item_code
  row.item_name = item.item_name
  // Update UOM if it's a different item, OR if this specific match came from a barcode scan
  if (!isSameItem || item._from_barcode) {
    row.uom = item.uom || 'Nos'
  }
  row.tax_rate = item.tax_rate || 0
  const base = getItemRateForPriceList(item, row.uom)
  row._base_rate = base
  const cpFactor = customerPricing.value[item.item_code]
  row._cp_applied = cpFactor != null
  row.rate = parseFloat((base * combinedFactor(item.item_code)).toFixed(2))
  recalcAmount(rowIdx)
}

function openItemSearch(query, targetRowIdx = null) {
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
  showItemSearch.value = false
  const rowIdx = itemSearchTargetRowIdx.value
  itemSearchTargetRowIdx.value = null
  if (rowIdx !== null) {
    applyItemToRow(rowIdx, item)
    focusEditField('qty', rowIdx)
    return
  }
  newItemCode.value = ''
  setPendingItem({
    item_code: item.item_code, item_name: item.item_name, qty: 0, rate: getItemRateForPriceList(item, item.uom),
    uom: item.uom || 'Nos', discount: 0, tax_rate: item.tax_rate || 0, deleted: false
  })
}

function onEditCodeInput(rowIdx) {
  const code = (items.value[rowIdx]?.item_code || '').trim()
  if (code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = editCodeInput.value
    editQuickSearchRowIdx.value = rowIdx

    // Auto-select on exact barcode match
    const exactMatch = quickSearchResults.value.find(i => 
      i.barcodes && i.barcodes.split(',').some(b => b.trim() === code)
    )
    if (exactMatch) {
      applyItemToRow(rowIdx, exactMatch)
      quickSearchResults.value = []
      setTimeout(() => {
        focusEditField('qty', rowIdx)
      }, 400)
    }
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


function onPendingUomChange() {
  const p = pendingItem.value
  if (!p) return
  const cached = lookupItemInCache(p.item_code)
  if (cached) {
    const newRate = getItemRateForPriceList(cached, p.uom)
    p._base_rate = newRate
    p.rate = parseFloat(((newRate || 0) * combinedFactor(p.item_code)).toFixed(2))
  }
}

function setPendingItem(item) {
  const base = item.rate || 0
  item._base_rate = base
  const cpFactor = customerPricing.value[item.item_code]
  item._cp_applied = cpFactor != null
  item.rate = parseFloat((base * combinedFactor(item.item_code)).toFixed(2))
  pendingItem.value = item
  nextTick(() => {
    pendingQtyInput.value?.focus()
    pendingQtyInput.value?.select()
  })
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value
  const qty = isReturn.value ? -Math.abs(p.qty) : p.qty
  const newItem = {
    item_code: p.item_code, item_name: p.item_name, qty, uom: p.uom || 'Nos',
    rate: p.rate || 0, _base_rate: p._base_rate ?? p.rate ?? 0, _cp_applied: !!p._cp_applied,
    discount: p.discount || 0, tax_rate: p.tax_rate || 0,
    amount: parseFloat((qty * (p.rate || 0)).toFixed(2)),
    deleted: false, _rowKey: makeRowKey()
  }
  items.value.push(newItem)
  pendingItem.value = null; newItemCode.value = ''; quickSearchResults.value = []
  nextTick(() => { newCodeInput.value?.focus(); newCodeInput.value?.scrollIntoView({ block: 'nearest' }) })
}

function cancelPendingItem(skipFocus = false) { 
  pendingItem.value = null
  if (!skipFocus) nextTick(() => { newCodeInput.value?.focus() }) 
}

function handleCustomerSelected(cust) {
  customerName.value = cust.label || cust.name
  customerId.value = cust.name
  customerDetails.value = cust.mobile_no || cust.email || ''
  customerMobile.value = cust.mobile_no || ''
  customerGstin.value = cust.gstin || ''
  customerBalance.value = cust.balance ?? 0
  customerState.value = cust.state || ''
  customerModifier.value = cust.pricelist_multiplication_factor ?? null
  ignoreModifier.value = false
  customerPricing.value = {}
  reapplyCustomerPricing()
  frappeGet('ssplbilling.api.customer_pricing_api.get_customer_pricing', { customer: cust.name || cust.label })
    .then(data => { customerPricing.value = data || {}; reapplyCustomerPricing() })
    .catch(() => { customerPricing.value = {} })
  const addrParts = [cust.address_line1, cust.city, cust.state].filter(Boolean)
  customerAddress.value = addrParts.join(', ')
  if (cust.last_invoice_date) {
    const d = new Date(cust.last_invoice_date)
    customerLastInvDate.value = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })
  } else {
    customerLastInvDate.value = 'None'
  }
  applyRegionalTaxLogic()
  fetchCustomerSalesHistory(cust.name)
  showCustomerModal.value = false
  nextTick(() => { newCodeInput.value?.focus() })
}

async function handleSeriesSelected(series) {
  try {
    selectedSeries.value = series
    const res = await frappeGet('ssplbilling.api.salesinvoice_api.get_series_defaults', { naming_series: series })
    invoiceNo.value = res.invoice_no; priceList.value = res.price_list; taxTemplate.value = res.tax_template
    if (res.warehouse) warehouse.value = res.warehouse
    if (res.cost_center) costCenter.value = res.cost_center
    showSeriesModal.value = false; customerInitialQuery.value = ''; showCustomerModal.value = true
  } catch (e) { console.error('[SalesInvoice] Failed to fetch series defaults:', e) }
}

useShortcuts(salesInvoiceShortcuts({
  openShortcuts:    () => { showShortcutPage.value = !showShortcutPage.value },
  clearBill:        () => handleF2(),
  focusModifyPanel: () => handleF3(),
  openSeries:       () => { showSeriesModal.value = true },
  modify:           () => handleModify(),
  print:            () => handlePrint(),
  openParcelAddress:() => { showCustomAddressModal.value = true },
  save:             () => handleSave(),
  cancel:           () => handleCancel(),
  openIncentive:    () => { showIncentiveModal.value = true },
  pageUp:           () => handlePageUp(),
  deleteRow:        () => {
    if (selectedRowIdx.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      deleteItem(selectedRowIdx.value)
    }
  },
}))

onMounted(() => {
  fetchRecentInvoices()
  showSeriesModal.value = true
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) {
    refreshItemCache('Sales', priceList.value, warehouse.value)
  }
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
