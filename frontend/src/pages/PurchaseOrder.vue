<template>
  <div class="h-screen bg-[var(--color-bg)] overflow-hidden">
    <Item_Invoice_Template
      ref="invoiceTemplateRef"
      title="Purchase Order"
      :doc-number="orderNo"
      :party-name="supplierName"
      :party-details="supplierDetails"
      :party-address="supplierAddress"
      :party-mobile="supplierMobile"
      :party-gstin="supplierGstin"
      :party-balance="null"
      :party-last-inv-date="supplierLastInvDate"
      :doc-date="orderDate"
      :items="items"
      :subtotal="subtotal"
      :item-discount-total="itemDiscountTotal"
      :total-tax="totalTax"
      :total-amount="totalAmount"
      :price-list="priceList"
      :tax-template="taxTemplate"
      :is-inclusive-tax="isInclusiveTax"
      :is-return="false"
      :warehouse="warehouse"
      :cost-center="costCenter"
      :income-account="''"
      :sidebar-date="sidebarDate"
      :sidebar-items="recentOrders"
      :sidebar-search="sidebarSearch"
      :sidebar-series="sidebarSeries"
      :available-series="availableSeries"
      :draft-only="draftOnly"
      :sidebar-loading="sidebarLoading"
      :save-button-text="saveButtonText"
      :is-read-only="isReadOnly"
      :show-submit-button="true"
      :is-draft="!isSubmitted"
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
      @submit="handleSubmit"
      @print="handlePrint"
      @discount-pct-keydown="handleDiscountPctKeydown"
      @cancel="handleCancel"
      @incentive="handleIncentive"
      @party-click="supplierInitialQuery = ''; showSupplierModal = true"
    >
      <template #row="{ item, index }">
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
              type="number" min="0"
              class="w-full bg-white/10 px-2 py-1 text-6xl font-mono text-[var(--color-text)] outline-none text-right focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              @keydown.enter.prevent="item.qty > 0 && openRowPriceListUpdate(index)"
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
              @keydown.enter.prevent="focusEditField('qty', index)"
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
            <div v-else-if="historyLoading" class="text-sm text-[var(--color-info)] animate-pulse">
              Fetching history...
            </div>
            <div v-else-if="!selectedItemHistory.length" class="text-sm text-[var(--color-text-muted)] italic">
              No previous history found for this supplier.
            </div>
            <div v-else class="max-h-[110px] overflow-y-auto mb-4 custom-scrollbar">
              <table class="w-full text-left text-lg border-collapse">
                <thead class="sticky top-0 bg-[var(--color-bg)] z-10">
                  <tr class="text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50">
                    <th class="py-0.5 pr-1 font-bold">Order</th>
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
          </div>

          <!-- Additional Info -->
          <div class="grid grid-cols-2 gap-2">
            <!-- Warehouse -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
              <select
                v-model="warehouse"
                :disabled="isReadOnly"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] disabled:opacity-50"
              >
                <option v-for="wh in localWarehouses" :key="wh" :value="wh">{{ wh }}</option>
              </select>
            </div>

            <!-- Cost Center -->
            <div class="flex flex-col gap-0.5">
              <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
              <select
                ref="costCenterRef"
                v-model="costCenter"
                :disabled="isReadOnly"
                class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1 py-0.5 text-base text-[var(--color-text)] outline-none focus:bg-[var(--color-focus)] focus:text-[var(--color-text-on-focus)] disabled:opacity-50"
              >
                <option v-for="cc in localCostCenters" :key="cc" :value="cc">{{ cc }}</option>
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
            <div class="flex items-baseline gap-2 font-bold text-[var(--color-success)]">
              <span class="text-[9mm] font-black">₹</span>
              <span class="font-mono text-[15.75mm] font-black leading-none">{{ totalAmount }}</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button ref="saveBtnRef" @click="handleSave" :disabled="isSubmitted" class="flex-1 rounded py-2.5 text-center text-3xl font-semibold transition-colors uppercase focus:outline-none" :class="isSubmitted ? 'bg-[var(--color-surface-raised)]/40 text-[var(--color-text-muted)] cursor-not-allowed' : 'text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 focus:bg-[var(--color-success)]/70'">{{ saveButtonText }}</button>
            <button @click="handlePrint" :disabled="!isReadOnly" class="flex-1 rounded border py-2.5 text-center text-3xl font-semibold transition-colors" :class="isReadOnly ? 'border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-midlight)] cursor-pointer' : 'border-[var(--color-border)]/40 bg-[var(--color-surface)]/30 text-[var(--color-text-muted)] cursor-not-allowed'">Print</button>
          </div>
          <div class="flex gap-2">
            <button @click="showClearWarning = true" class="flex-1 rounded border border-[var(--color-highlight)]/50 bg-[var(--color-highlight)]/10 py-2.5 text-center text-3xl font-semibold text-[var(--color-highlight)] hover:bg-[var(--color-highlight)]/20 transition-colors">New</button>
            <button v-if="isReadOnly && !isSubmitted" @click="handleSubmit" class="flex-1 rounded border border-[var(--color-success)] bg-[var(--color-success)]/20 py-2.5 text-center text-3xl font-semibold text-[var(--color-success)] hover:bg-[var(--color-success)]/30 transition-all uppercase active:scale-95">Submit</button>
          </div>
        </div>
      </template>

      <template #table-extra-rows>
        <!-- Pending row -->
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
                @keydown.enter.prevent="openPriceListUpdate"
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
            <td colspan="9" class="px-2 text-[var(--color-text-muted)] italic text-lg">Enter Item Code to add to order</td>
          </tr>
        </template>
      </template>
    </Item_Invoice_Template>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :query="quickSearchQuery"
      :price-list="priceList"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
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
      @close="showSupplierModal = false; supplierInitialQuery = ''"
      @select="handleSupplierSelected"
    />

    <Userseries
      :show="showSeriesModal"
      doctype="Purchase Order"
      @close="showSeriesModal = false"
      @selected="handleSeriesSelected"
    />

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="orderNo"
      doctype="Purchase Order"
      @close="closePrintModal"
    />

    <JumpToRowModal
      v-model:show="showJumpModal"
      :max-rows="items.length"
      @jump="handleJump"
    />

    <Warning
      :show="showClearWarning"
      title="Clear Order"
      message="All items will be removed and a new order number will be assigned."
      @close="showClearWarning = false"
      @confirm="showClearWarning = false; clearBill()"
    />

    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Purchase Order"
      :extra="[
        { key: 'F2', desc: 'Clear order / refresh order number' },
        { key: 'F3', desc: 'Focus sidebar order list' },
        { key: 'F4', desc: 'Select series' },
        { key: 'F5', desc: 'Print order' },
        { key: 'F8 / Ctrl+S', desc: 'Save order' },
        { key: 'Page Up', desc: 'Series (empty) / Change supplier (with items)' },
        { key: 'Delete', desc: 'Delete selected row' },
      ]"
      @close="showShortcutPage = false"
    />

    <PriceListUpdate
      v-if="showPriceListUpdate && priceListUpdateItemCode"
      :is-sub-window="true"
      :item-code="priceListUpdateItemCode"
      :selected-price-list="priceList"
      @close="onPriceListUpdateClose"
      @saved="onPriceListUpdateSaved"
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
import JumpToRowModal from '../components/JumpToRowModal.vue'
import Warning from '../components/Warning.vue'
import { useItemCache, lookupItemInCache } from '../services/itemCache.js'
import { useCustomerHistory } from '../composables/useCustomerHistory.js'
import { encryptPrice } from '../encryption.js'
import { useShortcuts } from '../services/shortcutManager'
import { useAllowedSeries } from '../composables/useAllowedSeries.js'
import { purchaseOrderShortcuts } from '../shortcuts/purchaseOrderShortcuts'
import ShortcutPage from '../components/ShortcutPage.vue'
import PriceListUpdate from './PriceListUpdate.vue'

const router = useRouter()

// --- Data Fetching & State Management ---
const { items: cachedItems, lastSync, refreshItemCache, searchItemsInCache } = useItemCache()
const { allowedSeries: availableSeries, fetchAllowedSeries } = useAllowedSeries()
const {
  fetchCustomerSalesHistory, hasHistory, clearHistory, getItemHistoryFromCache, historyLoading,
  fetchItemStock, itemStock, stockLoading,
  fetchItemPrices, itemPrices, pricesLoading
} = useCustomerHistory()

const items = ref([])
const recentOrders = ref([])

const localPriceLists = ref([])
try { localPriceLists.value = JSON.parse(localStorage.getItem('wb-purchase-pricelist') || '[]') } catch { localPriceLists.value = [] }
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
const isInclusiveTax = ref(false)

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

const showSeriesModal = ref(false)
const showSupplierModal = ref(false)
const showShortcutPage = ref(false)
const showClearWarning = ref(false)
const supplierInitialQuery = ref('')
const invoiceTemplateRef = ref(null)
const priceListSelectRef = ref(null)
const taxTemplateRef = ref(null)
const inclusiveTaxRef = ref(null)
const costCenterRef = ref(null)
const showPrintModal = ref(false)
const pendingClearAfterPrint = ref(false)
const showJumpModal = ref(false)
const showPriceListUpdate = ref(false)
const editRowPriceUpdateIdx = ref(null)
const priceListUpdateItemCode = computed(() => {
  if (editRowPriceUpdateIdx.value !== null) return items.value[editRowPriceUpdateIdx.value]?.item_code || ''
  return pendingItem.value?.item_code || ''
})

const lastEnterTime = ref(0)
const orderNo = ref('NEW')
const selectedSeries = ref('')
const orderDate = ref(new Date().toISOString().split('T')[0])
const sidebarDate = ref(new Date().toISOString().split('T')[0])
const sidebarSearch = ref('')
const sidebarSeries = ref([])
const draftOnly = ref(false)
const sidebarLoading = ref(false)

const isReadOnly = ref(false)
const isSaved = ref(false)
const isSubmitted = ref(false)
const saveButtonText = computed(() => {
  if (!isSaved.value) return 'Save'
  if (isSubmitted.value) return 'Submitted'
  return isReadOnly.value ? 'Modify Order' : 'Update Order'
})

function handleDocDateChange(days) {
  const d = new Date(orderDate.value)
  d.setDate(d.getDate() + days)
  orderDate.value = d.toISOString().split('T')[0]
}

async function fetchRecentOrders() {
  sidebarLoading.value = true
  try {
    recentOrders.value = await frappeGet('ssplbilling.api.purchase_order_api.get_purchase_orders', {
      query: sidebarSearch.value,
      limit: 100,
      posting_date: sidebarDate.value,
      naming_series: sidebarSeries.value.join(','),
      draft_only: draftOnly.value
    })
  } catch (e) {
    recentOrders.value = []
  }
  sidebarLoading.value = false
}

function handleSidebarDateChange(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

watch([sidebarDate, sidebarSeries, draftOnly], () => {
  fetchRecentOrders()
})

let searchTimeout = null
watch(sidebarSearch, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(fetchRecentOrders, 300)
})

async function handleSelectSidebarItem(item) {
  try {
    const data = await frappeGet('ssplbilling.api.purchase_order_api.get_purchase_order', { order_name: item.name })

    orderNo.value = data.name
    selectedSeries.value = data.naming_series || selectedSeries.value
    orderDate.value = data.posting_date || orderDate.value

    supplierId.value = data.supplier || ''
    supplierName.value = data.supplier_name || 'Select Supplier...'
    supplierState.value = data.state || ''

    if (data.price_list) priceList.value = data.price_list
    if (data.tax_template) taxTemplate.value = data.tax_template
    isInclusiveTax.value = data.is_inclusive === 1
    if (data.cost_center) costCenter.value = data.cost_center

    freightEntry.value = data.freight_amount || ''
    packingEntry.value = data.packing_amount || ''
    loadingEntry.value = data.loading_amount || ''
    otherEntry.value = data.other_charges_amount || ''

    discountPct.value = data.discount_percentage || ''
    discountDirectAmt.value = data.additional_discount_amount || ''

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
    alert('Failed to load order: ' + item.name)
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
const selectedRowIdx = ref(-1)
const rowRefs = ref([])
const editingRowIdx = ref(-1)
const originalRowCode = ref('')
const editingField = ref(null)
const editCodeInput = ref(null)
const editQtyInput = ref(null)
const editUomSelect = ref(null)
const editRateInput = ref(null)
const editDiscInput = ref(null)

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
    const addCharges = freightAmt.value + packingAmt.value + loadingAmt.value + otherAmt.value
    const undiscountedTotal = grossSubtotal + taxOnGross.value + addCharges
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
  if (grossSubtotal <= 0) return 1
  return (grossSubtotal - discountAmt.value) / grossSubtotal
})

const selectedItemHistory = computed(() => {
  if (pendingItem.value) return getItemHistoryFromCache(pendingItem.value.item_code)
  if (selectedRowIdx.value === -1) return []
  const item = items.value[selectedRowIdx.value]
  return item ? getItemHistoryFromCache(item.item_code) : []
})

const totalTax = computed(() => {
  if (isExempted.value) return '0.00'
  const factor = discountFactor.value
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    const discountedAmt = item.amount * factor
    let tax = 0
    if (isInclusiveTax.value) tax = discountedAmt - (discountedAmt / (1 + rate / 100))
    else tax = discountedAmt * (rate / 100)
    return sum + tax
  }, 0).toFixed(2)
})

const subtotal = computed(() => {
  const factor = discountFactor.value
  return activeItems.value.reduce((sum, item) => {
    const rate = item.tax_rate || 0
    const discountedAmt = item.amount * factor
    let net = discountedAmt
    if (isInclusiveTax.value && !isExempted.value) net = discountedAmt / (1 + rate / 100)
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

watch(items, (newItems) => {
  newItems.forEach((_, idx) => recalcAmount(idx))
}, { deep: true })

watch([pendingItem, selectedRowIdx], ([pending, rowIdx]) => {
  let code = null
  if (pending) code = pending.item_code
  else if (rowIdx !== -1) code = items.value[rowIdx]?.item_code
  if (code) {
    fetchItemStock(code)
    fetchItemPrices(code)
  }
})

watch(taxTemplate, (val) => {
  if (!val) return
  isInclusiveTax.value = val.toLowerCase().includes('inclusive')
})

watch(priceList, (newList) => {
  if (!newList) return
  updateTableRates()
  refreshItemCache('Purchase', newList, warehouse.value).then(() => updateTableRates())
})

function goBack() { router.push('/') }

function formatDateShort(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${String(d.getDate()).padStart(2, '0')}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getFullYear()).slice(-2)}`
}

async function clearBill() {
  items.value = []
  pendingItem.value = null
  newItemCode.value = ''
  selectedRowIdx.value = -1
  editingRowIdx.value = -1
  discountPct.value = ''
  discountDirectAmt.value = ''
  freightEntry.value = ''
  loadingEntry.value = ''
  packingEntry.value = ''
  otherEntry.value = ''
  clearHistory()
  orderNo.value = 'NEW'
  isReadOnly.value = false
  isSaved.value = false
  isSubmitted.value = false

  if (selectedSeries.value) {
    try {
      const next = await frappeGet('ssplbilling.api.purchase_order_api.get_next_bill_no', { naming_series: selectedSeries.value })
      orderNo.value = next || 'NEW'
    } catch { orderNo.value = 'NEW' }
  }
  nextTick(() => { newCodeInput.value?.focus() })
}

function handleF2() {
  if (items.value.some(i => !i.deleted)) showClearWarning.value = true
  else clearBill()
}

function handleF3() { nextTick(() => { invoiceTemplateRef.value?.focusSidebarList() }) }

function handleModifyPanelKeydown(e) {
  if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return
  e.preventDefault()
  const refs = [priceListSelectRef.value, taxTemplateRef.value, inclusiveTaxRef.value, costCenterRef.value].filter(Boolean)
  const idx = refs.indexOf(document.activeElement)
  if (e.key === 'ArrowDown') refs[(idx + 1) % refs.length]?.focus()
  else refs[(idx - 1 + refs.length) % refs.length]?.focus()
}

function handlePageUp() {
  if (items.value.some(i => !i.deleted)) {
    supplierInitialQuery.value = supplierId.value || supplierName.value
    showSupplierModal.value = true
  } else {
    showSeriesModal.value = true
  }
}

async function handleSave() {
  if (isSubmitted.value) return
  if (isReadOnly.value && isSaved.value) {
    isReadOnly.value = false
    if (items.value.length > 0) focusRow(0)
    else focusBarcodeInput()
    return
  }

  const active = items.value.filter(i => !i.deleted)
  if (!active.length) { alert('No items to save'); return }
  if (!supplierId.value) { alert('Please select a supplier first.'); return }
  if (!selectedSeries.value) { alert('Please select a series first.'); return }

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
    date: orderDate.value,
    price_list: priceList.value,
    discount_percentage: discountPct.value,
    tax_template: taxTemplate.value,
    cost_center: costCenter.value,
    warehouse: warehouse.value,
    is_inclusive: isInclusiveTax.value ? 1 : 0,
    taxes: additionalCharges,
    items: active.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      rate: parseFloat(((i.rate || 0) * (1 - (i.discount || 0) / 100)).toFixed(2)),
      price_list_rate: i._base_rate || i.price_list_rate || i.rate,
      discount_percentage: i.discount || 0,
      warehouse: warehouse.value,
    }))
  }

  try {
    let res
    if (isSaved.value) {
      payload.order_name = orderNo.value
      res = await frappePost('ssplbilling.api.purchase_order_api.update_purchase_order', { data: JSON.stringify(payload) })
      if (res.order_name || res.grand_total !== undefined) {
        isReadOnly.value = true; isSaved.value = true; fetchRecentOrders()
        pendingClearAfterPrint.value = false; showPrintModal.value = true
      }
    } else {
      res = await frappePost('ssplbilling.api.purchase_order_api.create_purchase_order', { data: JSON.stringify(payload) })
      if (res.order_name) {
        orderNo.value = res.order_name; isSaved.value = true; isReadOnly.value = true; fetchRecentOrders()
        pendingClearAfterPrint.value = true; showPrintModal.value = true
      }
    }
  } catch (error) { alert('Failed to save order.') }
}

function handleDiscountPctKeydown(e) {
  if (e.key === 'Enter') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountAmt() }
  else if (e.key === 'End') { e.preventDefault(); invoiceTemplateRef.value?.focusSaveBtn() }
}

function handlePrint() {
  if (!isSaved.value) { alert('Please save the order before printing.'); return }
  showPrintModal.value = true
}

async function closePrintModal() {
  showPrintModal.value = false
  if (!pendingClearAfterPrint.value) return
  pendingClearAfterPrint.value = false
  clearBill()
}

async function handleSubmit() {
  if (!isSaved.value || isSubmitted.value) return
  if (!confirm(`Are you sure you want to SUBMIT Purchase Order ${orderNo.value}?`)) return

  try {
    const res = await frappePost('ssplbilling.api.purchase_order_api.submit_purchase_order', {
      order_name: orderNo.value
    })
    if (res.status === 'Submitted') {
      isSubmitted.value = true
      isReadOnly.value = true
      fetchRecentOrders()
    }
  } catch (e) {
    alert('Failed to submit order: ' + e.message)
  }
}

function handleCancel() {
  if (items.value.length === 0) {
    router.push('/')
  } else {
    selectedRowIdx.value = -1
    editingRowIdx.value = -1
    editingField.value = null
    focusBarcodeInput()
  }
}
function handleIncentive() { showIncentiveModal.value = true }

function handleJump(targetNo) {
  if (items.value.length === 0) return
  let idx = Math.max(0, Math.min(targetNo - 1, items.value.length - 1))
  focusRow(idx)
}

function getItemRateForPriceList(cachedItem, uom = null) {
  if (!cachedItem) return 0
  const plName = priceList.value
  const targetUom = uom || cachedItem.uom || 'Nos'
  if (cachedItem.uom_price_lists?.[plName]?.[targetUom] != null) return cachedItem.uom_price_lists[plName][targetUom]
  const plEntry = (cachedItem.price_lists || []).find(p => p.name === plName)
  return plEntry ? plEntry.rate : parseFloat(cachedItem.price || 0)
}

function updateTableRates() {
  items.value.forEach((item, idx) => {
    if (item.deleted) return
    const cached = lookupItemInCache(item.item_code)
    if (cached) {
      const newRate = getItemRateForPriceList(cached, item.uom)
      item._base_rate = newRate; item.rate = newRate; recalcAmount(idx)
    }
  })
}

function recalcAmount(idx) {
  const item = items.value[idx]
  if (!item) return
  item.amount = parseFloat(((item.qty || 0) * (item.rate || 0) * (1 - (item.discount || 0) / 100)).toFixed(2))
}

function scrollRowToEdge(idx, direction) {
  const rowEl = rowRefs.value[idx]; if (!rowEl) return
  const container = rowEl.closest('.overflow-y-auto'); if (!container) return
  const rowRect = rowEl.getBoundingClientRect(), cRect = container.getBoundingClientRect()
  if (direction === 'down') container.scrollTop += (rowRect.bottom - cRect.bottom)
  else container.scrollTop += (rowRect.top - cRect.top - (container.querySelector('thead')?.offsetHeight || 0))
}

function focusRow(idx, direction = null) {
  selectedRowIdx.value = idx
  nextTick(() => {
    const el = rowRefs.value[idx]; if (!el) return
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

function onQuickSearchSelect(item) {
  if (!item) return
  
  // Capture the query used to find this item
  const currentQuery = editQuickSearchRowIdx.value !== null 
    ? (items.value[editQuickSearchRowIdx.value]?.item_code || '').trim()
    : newItemCode.value.trim()
    
  // If the query was a barcode, lookupItemInCache will return the item with that barcode's specific UOM
  const barcodeMatch = lookupItemInCache(currentQuery)
  const finalItem = (barcodeMatch && barcodeMatch.item_code === item.item_code) ? barcodeMatch : item

  quickSearchResults.value = []
  if (editQuickSearchRowIdx.value !== null) {
    const rowIdx = editQuickSearchRowIdx.value; editQuickSearchRowIdx.value = null
    applyItemToRow(rowIdx, finalItem)
    if (getItemUoms(finalItem.item_code).length > 1) focusEditField('uom', rowIdx)
    else focusEditField('qty', rowIdx)
    return
  }
  newItemCode.value = ''
  setPendingItem({
    item_code: finalItem.item_code, item_name: finalItem.item_name, qty: 0, rate: getItemRateForPriceList(finalItem, finalItem.uom),
    uom: finalItem.uom || 'Nos', discount: 0, tax_rate: finalItem.tax_rate || 0, deleted: false
  })
}

function applyItemToRow(rowIdx, item) {
  const row = items.value[rowIdx]; if (!row) return
  const isSameItem = originalRowCode.value === item.item_code
  row.item_code = item.item_code; row.item_name = item.item_name
  if (!isSameItem || item._from_barcode) row.uom = item.uom || 'Nos'
  row.tax_rate = item.tax_rate || 0

  if (!isSameItem) {
    const base = getItemRateForPriceList(item, row.uom)
    row._base_rate = base; row.rate = base; row.discount = 0
  }
  recalcAmount(rowIdx)
}

function openItemSearch(query, targetRowIdx = null) {
  quickSearchResults.value = []; editQuickSearchRowIdx.value = null
  itemSearchTargetRowIdx.value = targetRowIdx; itemSearchInitialQuery.value = query || ''; showItemSearch.value = true
  nextTick(() => { itemSearchRef.value?.focus() })
}

function closeItemSearch() {
  showItemSearch.value = false; const rowIdx = itemSearchTargetRowIdx.value; itemSearchTargetRowIdx.value = null
  if (rowIdx !== null) nextTick(() => { focusEditField('code', rowIdx) })
  else nextTick(() => { newCodeInput.value?.focus() })
}

function onItemSearchSelect(item) {
  showItemSearch.value = false; const rowIdx = itemSearchTargetRowIdx.value; itemSearchTargetRowIdx.value = null
  
  // Re-check for barcode match to get correct UOM from the initial query
  const barcodeMatch = lookupItemInCache(itemSearchInitialQuery.value.trim())
  const finalItem = (barcodeMatch && barcodeMatch.item_code === item.item_code) ? barcodeMatch : item

  if (rowIdx !== null) { applyItemToRow(rowIdx, finalItem); focusEditField('qty', rowIdx); return }
  newItemCode.value = ''; setPendingItem({
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
      has_history: hasHistory(item.item_code)
    }))
    quickSearchAnchor.value = editCodeInput.value
    editQuickSearchRowIdx.value = rowIdx
  }
  else { quickSearchResults.value = []; editQuickSearchRowIdx.value = null }
}

function onEditCodeKeydown(e, rowIdx) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return }
    else if (e.key === 'Enter') { e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return }
    else if (e.key === 'Escape') { e.preventDefault(); quickSearchResults.value = []; editQuickSearchRowIdx.value = null; return }
  }
  if (e.key === 'Enter') {
    e.preventDefault(); const code = (items.value[rowIdx]?.item_code || '').trim(); const match = lookupItemInCache(code)
    if (match) {
      applyItemToRow(rowIdx, match)
      if (getItemUoms(match.item_code).length > 1) focusEditField('uom', rowIdx)
      else focusEditField('qty', rowIdx)
    } else openItemSearch(code, rowIdx)
  } else if (e.key === 'Escape') { e.preventDefault(); exitEditMode(rowIdx, true) }
}

function onPendingUomChange() {
  const p = pendingItem.value; if (!p) return
  const cached = lookupItemInCache(p.item_code)
  if (cached) { const newRate = getItemRateForPriceList(cached, p.uom); p._base_rate = newRate; p.rate = newRate }
}

function setPendingItem(item) {
  item._base_rate = item.rate || 0; pendingItem.value = item
  nextTick(() => { pendingQtyInput.value?.focus(); pendingQtyInput.value?.select() })
}

function openPriceListUpdate() { if (!pendingItem.value || pendingItem.value.qty <= 0) return; editRowPriceUpdateIdx.value = null; showPriceListUpdate.value = true }
function openRowPriceListUpdate(idx) { editRowPriceUpdateIdx.value = idx; showPriceListUpdate.value = true }

function onPriceListUpdateSaved(data) {
  showPriceListUpdate.value = false
  if (editRowPriceUpdateIdx.value !== null) {
    const idx = editRowPriceUpdateIdx.value; editRowPriceUpdateIdx.value = null; const item = items.value[idx]
    if (item && data.changedPrices?.length) {
      const pl = data.changedPrices.find(p => p.price_list === priceList.value)
      if (pl) { const uomRate = pl.uom_rates?.[item.uom]; const newRate = uomRate != null ? uomRate : (pl.rate ?? item.rate); item.rate = newRate; item._base_rate = newRate; recalcAmount(idx) }
    }
    focusEditField('rate', idx)
  } else {
    if (pendingItem.value && data.changedPrices?.length) {
      const pl = data.changedPrices.find(p => p.price_list === priceList.value)
      if (pl) { const uomRate = pl.uom_rates?.[pendingItem.value.uom]; const newRate = uomRate != null ? uomRate : (pl.rate ?? pendingItem.value.rate); pendingItem.value.rate = newRate; pendingItem.value._base_rate = newRate }
    }
    confirmPendingItem()
  }
}

function onPriceListUpdateClose() {
  showPriceListUpdate.value = false
  if (editRowPriceUpdateIdx.value !== null) { const idx = editRowPriceUpdateIdx.value; editRowPriceUpdateIdx.value = null; focusEditField('rate', idx) }
  else confirmPendingItem()
}

function confirmPendingItem() {
  if (!pendingItem.value || pendingItem.value.qty <= 0) return
  const p = pendingItem.value; const newItem = {
    item_code: p.item_code, item_name: p.item_name, qty: p.qty, uom: p.uom || 'Nos',
    rate: p.rate || 0, _base_rate: p._base_rate ?? p.rate ?? 0, discount: p.discount || 0, tax_rate: p.tax_rate || 0,
    amount: parseFloat((p.qty * (p.rate || 0)).toFixed(2)), deleted: false,
  }
  items.value.push(newItem); pendingItem.value = null; newItemCode.value = ''; quickSearchResults.value = []
  nextTick(() => { newCodeInput.value?.focus(); newCodeInput.value?.scrollIntoView({ block: 'nearest' }) })
}

function cancelPendingItem(skipFocus = false) { pendingItem.value = null; if (!skipFocus) nextTick(() => { newCodeInput.value?.focus() }) }

function handleSupplierSelected(party) {
  supplierName.value = party.label || party.name; supplierId.value = party.name
  supplierDetails.value = party.mobile_no || party.email || ''; supplierMobile.value = party.mobile_no || ''
  supplierGstin.value = party.gstin || ''; supplierState.value = party.state || ''
  const addrParts = [party.address_line1, party.city, party.state].filter(Boolean)
  supplierAddress.value = addrParts.join(', ')
  if (party.last_invoice_date) {
    const d = new Date(party.last_invoice_date)
    supplierLastInvDate.value = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })
  } else supplierLastInvDate.value = 'None'
  fetchCustomerSalesHistory(party.name); showSupplierModal.value = false; nextTick(() => { newCodeInput.value?.focus() })
}

async function handleSeriesSelected(series) {
  try {
    selectedSeries.value = series
    const next = await frappeGet('ssplbilling.api.purchase_order_api.get_next_bill_no', { naming_series: series })
    orderNo.value = next || 'NEW'; showSeriesModal.value = false; supplierInitialQuery.value = ''; showSupplierModal.value = true
  } catch (e) { showSeriesModal.value = false }
}

function handleItemEntry() {
  if (!newItemCode.value) return
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) return
  const code = newItemCode.value.trim(); const match = lookupItemInCache(code)
  if (!match) { openItemSearch(code); return }
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
      has_history: hasHistory(item.item_code)
    }))
    quickSearchAnchor.value = newCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

function handleNewCodeKeydown(e) {
  if (e.key === 'Enter') {
    const now = Date.now(); const isDouble = (now - lastEnterTime.value < 400); lastEnterTime.value = now
    if (isDouble) { e.preventDefault(); cancelPendingItem(true); newItemCode.value = ''; quickSearchResults.value = []; lastEnterTime.value = 0; return }
  }
  if (e.key === 'ArrowRight') { e.preventDefault(); openItemSearch(newItemCode.value.trim()); return }
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return }
    else if (e.key === 'Enter') { e.preventDefault(); quickSearchRef.value.handleQuickSearchKeydown(e); return }
    else if (e.key === 'Escape') { e.preventDefault(); quickSearchResults.value = []; return }
  }
  if (e.key === 'Enter') { if (!newItemCode.value) return; handleItemEntry() }
  else if (e.key === 'ArrowUp' && items.value.length > 0) { e.preventDefault(); focusRow(items.value.length - 1) }
  else if (e.key === 'End') { e.preventDefault(); invoiceTemplateRef.value?.focusDiscountPct() }
}

function handlePendingQtyKeydown(e) {
  if (e.key === 'Enter') {
    const now = Date.now(); const isDouble = (now - lastEnterTime.value < 400); lastEnterTime.value = now
    if (isDouble && (!pendingItem.value.qty || pendingItem.value.qty === 0)) { e.preventDefault(); cancelPendingItem(true); lastEnterTime.value = 0; return }
    if (pendingItem.value.qty > 0) {
      e.preventDefault()
      if (getItemUoms(pendingItem.value.item_code).length > 1) { pendingUomSelect.value?.focus(); if (pendingUomSelect.value?.showPicker) pendingUomSelect.value.showPicker() }
      else openPriceListUpdate()
    }
  } else if (e.key === 'Escape') cancelPendingItem()
  else if (e.key === 'Backspace' && (!pendingItem.value.qty || pendingItem.value.qty === 0)) { e.preventDefault(); cancelPendingItem() }
}

function handleRowKeydown(e, idx) {
  const item = items.value[idx]; if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
  if (e.key === 'Enter' && !item.deleted && !item._is_free) { e.preventDefault(); focusEditField('code', idx) }
  else if (e.key === 'ArrowDown') { e.preventDefault(); if (idx < items.value.length - 1) focusRow(idx + 1, 'down'); else focusBarcodeInput() }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (idx > 0) focusRow(idx - 1, 'up') }
  else if (e.key === 'End') { e.preventDefault(); focusRow(items.value.length - 1, 'down') }
  else if (e.key === 'Home') { e.preventDefault(); focusRow(0, 'up') }
  else if (e.key === 'Escape') { e.preventDefault(); if (!items.value.length) router.push('/'); else focusBarcodeInput() }
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
    const el = inputMap[field]?.value; if (!el) return
    el.focus(); if (el.select) el.select(); if (field === 'uom' && el.showPicker) el.showPicker()
  })
}

function exitEditMode(idx, cancel = false) {
  if (cancel) { clearItem(idx); editingRowIdx.value = -1; editingField.value = null; quickSearchResults.value = []; editQuickSearchRowIdx.value = null; focusBarcodeInput(); return }
  recalcAmount(idx); editingRowIdx.value = -1; editingField.value = null; quickSearchResults.value = []; editQuickSearchRowIdx.value = null; nextTick(() => { rowRefs.value[idx]?.focus() })
}

function clearItem(idx) { if (idx !== -1 && items.value[idx]) { items.value.splice(idx, 1); if (editingRowIdx.value === idx) { editingRowIdx.value = -1; editingField.value = null } } }

function getItemUoms(itemCode) { const cached = lookupItemInCache(itemCode); return (cached && cached.uoms) ? cached.uoms.map(u => u.uom) : [] }

function onUomChange(idx) {
  const item = items.value[idx]; if (!item) return
  const cached = lookupItemInCache(item.item_code)
  if (cached) { const newRate = getItemRateForPriceList(cached, item.uom); item._base_rate = newRate; item.rate = newRate; recalcAmount(idx) }
}

function finishRowEdit(idx) {
  recalcAmount(idx); editingRowIdx.value = -1; editingField.value = null
  if (idx < items.value.length - 1) focusRow(idx + 1); else focusBarcodeInput()
}

useShortcuts(purchaseOrderShortcuts({
  openShortcuts:    () => { showShortcutPage.value = !showShortcutPage.value },
  clearBill:        () => handleF2(),
  focusModifyPanel: () => handleF3(),
  openSeries:       () => { showSeriesModal.value = true },
  modify:           () => { if (isReadOnly.value && isSaved.value) { isReadOnly.value = false; if (items.value.length) focusRow(0); else focusBarcodeInput() } },
  print:            () => handlePrint(),
  save:             () => handleSave(),
  cancel:           () => handleCancel(),
  pageUp:           () => handlePageUp(),
  deleteRow:        () => { if (selectedRowIdx.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) deleteItem(selectedRowIdx.value) },
}))

onMounted(() => {
  fetchRecentOrders()
  fetchAllowedSeries('Purchase Order')
  showSeriesModal.value = true
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) refreshItemCache('Purchase', priceList.value, warehouse.value)
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
