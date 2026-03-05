<template>
  <div class="flex h-screen flex-col">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-xs text-gray-300">|</span>
        <span class="text-sm font-semibold text-gray-800">Sales Entry</span>
        <button class="rounded border border-gray-300 px-2.5 py-1 text-sm text-gray-600 hover:bg-gray-50" @click="openModifyBill">Modify Bill</button>
      </div>
      <div class="flex items-center gap-3 text-xs text-gray-400">
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Up/Down</kbd> Navigate rows</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Tab</kbd> Next column</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Ctrl+S</kbd> Save</span>
        <span v-if="escWarning" class="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">Press Esc again to discard and exit</span>
        <span v-else><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Esc</kbd> {{ billSaved ? 'New Bill' : 'Back' }}</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- LEFT SIDE (70%) -->
      <div class="flex w-[70%] flex-col border-r border-gray-200">
        <div class="flex flex-[8] flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="sticky top-0 z-10 bg-gray-50">
                  <th class="w-8 border-b-2 border-gray-200 px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">#</th>
                  <th class="w-32 border-b-2 border-gray-200 px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Item Code</th>
                  <th class="border-b-2 border-gray-200 px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Item Name</th>
                  <th class="w-14 border-b-2 border-gray-200 px-2 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">UOM</th>
                  <th class="w-16 border-b-2 border-gray-200 px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Qty</th>
                  <th class="w-24 border-b-2 border-gray-200 px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Rate</th>
                  <th class="w-16 border-b-2 border-gray-200 px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Disc %</th>
                  <th class="w-16 border-b-2 border-gray-200 px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Tax %</th>
                  <th class="w-24 border-b-2 border-gray-200 px-2 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Amount</th>
                  <th class="w-8 border-b-2 border-gray-200"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" class="cursor-pointer border-b border-gray-100" :class="{ 'bg-blue-50': selectedRow === idx && !item.deleted, 'bg-red-50/40': item.deleted, 'hover:bg-blue-50/50': !item.deleted }" @click="selectRow(idx)">
                  <td class="px-3 py-1.5"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold" :class="item.deleted ? 'bg-red-100 text-red-400' : 'bg-gray-100 text-gray-500'">{{ idx + 1 }}</span></td>
                  <td class="px-2 py-1.5">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" class="w-full rounded border border-gray-300 bg-white px-2 py-0.5 font-mono text-xs outline-none focus:border-blue-500" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono text-xs" :class="item.deleted ? 'text-gray-300' : 'text-gray-600'">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 py-1.5"><span :class="item.deleted ? 'text-red-300 line-through' : 'text-gray-800'">{{ item.item_name || '--' }}</span><span v-if="item.deleted" class="ml-1 text-[10px] font-semibold text-red-400">DELETED</span></td>
                  <td class="px-2 py-1.5 text-gray-400" :class="{ 'text-gray-300': item.deleted }">{{ item.uom || '--' }}</td>
                  <td class="px-2 py-1.5">
                    <input v-if="!item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" min="1" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono text-sm focus:border-blue-400 focus:bg-white focus:outline-none" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono text-xs text-gray-300">{{ item.qty }}</span>
                  </td>
                  <td class="px-2 py-1.5">
                    <input v-if="!item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" step="0.01" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono text-sm focus:border-blue-400 focus:bg-white focus:outline-none" @keydown.enter.prevent="focusField('discount', idx)" @keydown.tab.prevent="focusField('discount', idx)" @keydown.shift.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono text-xs text-gray-300">{{ item.rate }}</span>
                  </td>
                  <td class="px-2 py-1.5">
                    <input v-if="!item.deleted" :ref="el => setRef(el, 'discount', idx)" type="number" v-model.number="item.discount" step="0.5" min="0" max="100" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono text-sm focus:border-blue-400 focus:bg-white focus:outline-none" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.shift.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono text-xs text-gray-300">{{ item.discount || 0 }}</span>
                  </td>
                  <td class="px-2 py-1.5 text-right">
                    <span class="font-mono text-sm" :class="item.deleted ? 'text-gray-300' : 'text-gray-600'">{{ isExempted ? 0 : (item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}</span>
                  </td>
                  <td class="px-2 py-1.5 text-right font-mono font-semibold" :class="item.deleted ? 'text-gray-300 line-through' : 'text-gray-800'">{{ item.deleted ? '' : (item.qty * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2) }}</td>
                  <td class="px-2 py-1.5 text-center">
                    <button v-if="!item.deleted" class="rounded px-1 py-0.5 text-xs text-gray-300 hover:bg-red-50 hover:text-red-500" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else class="rounded px-1 py-0.5 text-[10px] font-semibold text-blue-400 hover:bg-blue-50 hover:text-blue-600" @click.stop="restoreItem(idx)">&larr;</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr class="border-b border-gray-100 bg-gray-50/50">
                  <td class="px-3 py-1.5"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 text-[10px] font-bold text-blue-500">+</span></td>
                  <td class="px-2 py-1.5"><input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-gray-300 bg-white px-2 py-1 text-xs outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100" placeholder="Item code" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" /></td>
                  <td class="px-2 py-1.5 text-xs text-gray-400">{{ newPending.item_name || '--' }}</td>
                  <td class="px-2 py-1.5 text-xs text-gray-400">{{ newPending.uom || '--' }}</td>
                  <td class="px-2 py-1.5 text-right"><input ref="newQtyInput" v-model.number="newQty" type="number" min="1" class="w-14 rounded border border-gray-300 bg-white px-1 py-1 text-right font-mono text-xs outline-none focus:border-blue-500" @keydown.enter.prevent="addNewItem" @keydown.shift.tab.prevent="focusNewCode" /></td>
                  <td class="px-2 py-1.5 text-right font-mono text-xs text-gray-400">{{ newPending.rate ? newPending.rate.toFixed(2) : '--' }}</td>
                  <td class="px-2 py-1.5 text-right font-mono text-xs text-gray-400">0</td>
                  <td class="px-2 py-1.5 text-right font-mono text-xs text-gray-400">{{ isExempted ? 0 : defaultTaxRate }}</td>
                  <td class="px-2 py-1.5 text-right font-mono text-xs text-gray-400">{{ newPending.rate ? (newQty * newPending.rate).toFixed(2) : '--' }}</td>
                  <td></td>
                </tr>
              </tbody>
            </table>
            <div v-if="!items.length" class="flex flex-col items-center py-8 text-gray-300">
              <div class="text-xs">Type an item code and press <kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Enter</kbd></div>
            </div>
          </div>
          <div class="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-1.5 text-xs text-gray-400">
            <span>{{ activeItems.length }} item{{ activeItems.length !== 1 ? 's' : '' }}{{ deletedCount > 0 ? ' (' + deletedCount + ' deleted)' : '' }}</span>
            <span class="font-mono font-semibold text-gray-600">Subtotal: &#8377;{{ subtotal.toFixed(2) }}</span>
          </div>
        </div>

        <!-- Item Insight (20%) -->
        <div class="flex-[2] overflow-y-auto border-t border-gray-200 bg-white px-4 py-3">
          <div class="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400">Item Insight <span v-if="selectedItemData" class="ml-2 font-normal normal-case text-gray-300">{{ selectedItemData.item_code }}</span></div>
          <template v-if="selectedItemData">
            <div class="flex gap-6">
              <div class="flex-1">
                <div class="mb-1 text-[10px] font-bold uppercase text-gray-400">Stock</div>
                <div v-if="selectedItemData.stock.length">
                  <div v-for="s in selectedItemData.stock" :key="s.warehouse" class="flex justify-between text-xs">
                    <span class="text-gray-500">{{ s.warehouse }}</span>
                    <span class="rounded-full px-2 py-0.5 font-bold" :class="s.actual_qty > 20 ? 'bg-green-50 text-green-600' : s.actual_qty > 0 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'">{{ s.actual_qty }}</span>
                  </div>
                </div>
                <div v-else class="text-xs text-gray-300">No stock data</div>
              </div>
              <div class="flex-1">
                <div class="mb-1 text-[10px] font-bold uppercase text-gray-400">Previous purchases</div>
                <div v-if="selectedItemData.previousPurchases && selectedItemData.previousPurchases.length" class="flex flex-col">
                  <div v-for="p in selectedItemData.previousPurchases" :key="p.name" class="flex items-center gap-2 border-b border-gray-50 py-0.5 text-[11px] last:border-0">
                    <span class="w-24 truncate font-medium text-blue-600" :title="p.name">{{ p.name }}</span>
                    <span class="text-gray-400">{{ p.date }}</span>
                    <span class="font-mono font-bold text-gray-700">&#8377;{{ p.rate.toFixed(2) }}</span>
                    <span class="text-gray-400">x{{ p.qty }}</span>
                    <span v-if="p.discount > 0" class="font-bold text-red-500">-{{ p.discount }}%</span>
                  </div>
                </div>
                <div v-else class="text-xs text-gray-300">--</div>
              </div>
              <div class="flex-1">
                <div class="mb-1 text-[10px] font-bold uppercase text-gray-400">Prices</div>
                <div class="flex flex-wrap gap-2">
                  <span v-for="pl in selectedItemData.priceLists" :key="pl.name" class="rounded bg-amber-50 px-1.5 py-0.5 text-[11px]">
                    <span class="text-gray-500">{{ pl.name }}:</span>
                    <span class="ml-0.5 font-mono font-bold text-amber-700">&#8377;{{ encPrice(pl.rate || 0) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="py-2 text-xs text-gray-300">Click a row to see stock, last purchase &amp; prices</div>
        </div>
      </div>

      <!-- RIGHT SIDE (30%) -->
      <div class="flex w-[30%] flex-col overflow-y-auto bg-white">
        <!-- Invoice Details -->
        <div class="border-b border-gray-100 p-4">
          <div class="mb-3 text-[10px] font-bold uppercase tracking-wider text-gray-400">Invoice Details</div>
          <div class="flex flex-col gap-2.5">
            <div class="flex flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">Bill Date</label>
              <input type="date" v-model="billDate" class="rounded border border-gray-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500" />
            </div>
            <!-- Series + Bill No — starting point -->
            <div class="flex gap-2">
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Series</label>
                <select ref="seriesSelect" v-model="billSeries" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
                  <option v-for="s in availableSeries" :key="s">{{ s }}</option>
                </select>
              </div>
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Bill No</label>
                <input :value="nextBillNo" readonly class="rounded border border-gray-200 bg-gray-50 px-2.5 py-1.5 font-mono text-sm text-gray-400" />
              </div>
            </div>
            <!-- Customer -->
            <div class="flex flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">Customer</label>
              <div class="relative">
                <input ref="customerInput" v-model="custSearch" class="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm outline-none focus:border-blue-500" :placeholder="customer || 'Search customer...'" :class="{ 'border-green-400': customer }" @input="doCustSearch" @focus="showCustDD = true" @keydown.enter.prevent="onCustomerEnter" @keydown.down.prevent="custDDIdx = Math.min(custDDIdx + 1, custResults.length)" @keydown.up.prevent="custDDIdx = Math.max(custDDIdx - 1, 0)" @keydown.esc="showCustDD = false" />
                <div v-if="showCustDD && (custResults.length || custSearch.trim())" class="absolute left-0 right-0 top-full z-30 mt-1 max-h-48 overflow-y-auto rounded border border-gray-200 bg-white shadow-lg">
                  <div v-for="(c, i) in custResults" :key="c.name" class="cursor-pointer px-3 py-1.5 text-sm" :class="custDDIdx === i ? 'bg-blue-50' : 'hover:bg-gray-50'" @click="pickCust(c)" @mouseenter="custDDIdx = i"><span class="font-medium text-gray-700">{{ c.customer_name }}</span> <span class="ml-2 text-[10px] text-gray-400">{{ c.name }}</span></div>
                  <div v-if="custSearch.trim()" class="cursor-pointer border-t border-gray-100 px-3 py-2 text-sm font-semibold text-blue-600" :class="custDDIdx === custResults.length ? 'bg-blue-50' : 'hover:bg-blue-50'" @click="openNewCustForm" @mouseenter="custDDIdx = custResults.length">+ Create "{{ custSearch.trim() }}"</div>
                </div>
              </div>
            </div>
            <!-- Warehouse + Price List (single row) -->
            <div class="flex gap-2">
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Warehouse</label>
                <select v-model="defaultWarehouse" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
                  <option value="">-- Default --</option>
                  <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
                </select>
              </div>
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Price List</label>
                <select v-model="priceList" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
                  <option v-for="pl in availablePriceLists" :key="pl" :value="pl">{{ pl }}</option>
                </select>
              </div>
            </div>
            <!-- Tax Template + Cost Center (single row) -->
            <div class="flex gap-2">
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Tax Template</label>
                <select v-model="taxTemplate" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
                  <option value="">-- None --</option>
                  <option v-for="t in availableTaxTemplates" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="flex flex-1 flex-col gap-1">
                <label class="text-[10px] font-bold uppercase text-gray-400">Cost Center</label>
                <select v-model="costCenter" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
                  <option value="">-- Default --</option>
                  <option v-for="cc in availableCostCenters" :key="cc" :value="cc">{{ cc }}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Payment Mode -->
        <div class="border-b border-gray-100 p-4">
          <div class="mb-3 text-[10px] font-bold uppercase tracking-wider text-gray-400">Payment Mode</div>
          <div class="flex gap-2">
            <button class="flex-1 rounded border py-2 text-center text-sm font-semibold transition" :class="paymentMode === 'Cash' ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'" @click="paymentMode = 'Cash'">Cash</button>
            <button class="flex-1 rounded border py-2 text-center text-sm font-semibold transition" :class="paymentMode === 'Credit' ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'" @click="paymentMode = 'Credit'">Credit</button>
          </div>
        </div>

        <!-- Summary -->
        <div class="border-b border-gray-100 p-4">
          <div class="mb-3 text-[10px] font-bold uppercase tracking-wider text-gray-400">Summary</div>
          <div class="flex justify-between py-1 text-sm"><span class="text-gray-500">Subtotal{{ isInclusive ? ' (ex-tax)' : '' }}</span><span class="font-mono font-semibold">&#8377;{{ subtotal.toFixed(2) }}</span></div>
          <div class="flex items-center justify-between py-1 text-sm">
            <div class="flex items-center gap-1.5"><span class="text-gray-500">Discount</span><input type="number" v-model.number="discountPct" min="0" max="100" class="w-12 rounded border border-gray-200 px-1 py-0.5 text-right text-xs outline-none focus:border-blue-400" /><span class="text-xs text-gray-400">%</span></div>
            <span class="font-mono font-semibold text-red-500">-&#8377;{{ discountAmt.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between py-1 text-sm"><span class="text-gray-500">Total Tax</span><span class="font-mono font-semibold">+&#8377;{{ totalTax.toFixed(2) }}</span></div>
          <div class="mt-2 flex justify-between border-t-2 border-gray-200 pt-2"><span class="font-semibold text-gray-700">Grand Total</span><span class="font-mono text-lg font-bold text-blue-600">&#8377;{{ grandTotal.toFixed(2) }}</span></div>
        </div>

        <!-- Bottom Actions -->
        <div class="mt-auto flex flex-col gap-2 p-4">
          <!-- Print Scheme -->
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-gray-400">Print Scheme</label>
            <select v-model="printScheme" class="rounded border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-blue-500">
              <option value="">-- Default --</option>
              <option v-for="pf in availablePrintSchemes" :key="pf" :value="pf">{{ pf }}</option>
            </select>
          </div>

          <!-- Saved state indicator -->
          <div v-if="billSaved" class="flex items-center justify-between rounded bg-green-50 px-3 py-2 text-xs">
            <span class="font-semibold text-green-700">Saved: <span class="font-mono">{{ savedInvoiceName }}</span></span>
            <span class="text-gray-400">Esc → new bill</span>
          </div>

          <!-- Edit button (shown after save) -->
          <button
            v-if="billSaved"
            @click="enterEditMode"
            class="w-full rounded-lg border border-amber-400 bg-amber-50 py-2.5 text-center text-sm font-semibold text-amber-700 transition hover:bg-amber-100"
          >
            ✏ Edit Bill
          </button>

          <!-- Save / Update button (shown when not saved) -->
          <button
            v-else
            @click="saveBill"
            class="w-full rounded-lg py-2.5 text-center text-sm font-semibold text-white transition"
            :class="savedInvoiceName ? 'bg-orange-500 hover:bg-orange-600' : 'bg-blue-600 hover:bg-blue-700'"
          >
            {{ savedInvoiceName ? 'Update Bill' : 'Save Bill' }}
          </button>

          <div class="flex gap-2">
            <button class="flex-1 rounded-lg border border-gray-300 py-2 text-center text-sm font-semibold text-gray-600 transition hover:bg-gray-50" @click="printBill">Print</button>
            <button class="flex-1 rounded-lg border border-red-200 py-2 text-center text-sm font-semibold text-red-500 transition hover:bg-red-50" @click="cancelBill">{{ billSaved ? 'New Bill' : 'Cancel' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- =================== MODIFY BILL SUBWINDOW =================== -->
    <div v-if="showModifyBill" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showModifyBill = false">
      <div class="flex max-h-[80vh] w-[680px] flex-col rounded-xl bg-white shadow-2xl">
        <!-- Header -->
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-sm font-semibold text-gray-700">Modify Existing Bill</div>
          <div class="mt-0.5 text-xs text-gray-400">Search and select a Draft invoice to edit</div>
        </div>

        <!-- Search -->
        <div class="border-b border-gray-100 px-5 py-3">
          <input
            ref="modifySearchInput"
            v-model="modifyQuery"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Search by invoice no. or customer name..."
            @keydown.esc="showModifyBill = false"
          />
        </div>

        <!-- Results -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="modifyLoading" class="flex items-center justify-center py-10 text-xs text-gray-400">Loading...</div>
          <table v-else-if="modifyResults.length" class="w-full text-sm">
            <thead>
              <tr class="sticky top-0 bg-gray-50">
                <th class="px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Invoice No.</th>
                <th class="px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Customer</th>
                <th class="px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Date</th>
                <th class="px-3 py-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Amount</th>
                <th class="px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Series</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="inv in modifyResults"
                :key="inv.name"
                class="cursor-pointer border-b border-gray-100 hover:bg-blue-50"
                @click="loadInvoice(inv.name)"
              >
                <td class="px-4 py-2.5 font-mono text-xs font-semibold text-blue-700">{{ inv.name }}</td>
                <td class="px-3 py-2.5">
                  <div class="text-xs font-medium text-gray-800">{{ inv.customer_name }}</div>
                  <div class="text-[10px] text-gray-400">{{ inv.customer }}</div>
                </td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ inv.posting_date }}</td>
                <td class="px-3 py-2.5 text-right font-mono text-sm font-semibold text-gray-800">&#8377;{{ inv.grand_total.toFixed(2) }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-400">{{ inv.naming_series }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="flex flex-col items-center py-10 text-xs text-gray-400">
            <div>No draft invoices found</div>
            <div v-if="modifyQuery" class="mt-1 text-gray-300">Try a different search term</div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between border-t border-gray-100 px-5 py-3">
          <span class="text-xs text-gray-400">Click a row to open it for editing</span>
          <button class="rounded border border-gray-300 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-50" @click="showModifyBill = false">Close</button>
        </div>
      </div>
    </div>

    <!-- NEW CUSTOMER SUBWINDOW -->
    <div v-if="showNewCustForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showNewCustForm = false">
      <div class="w-[460px] rounded-xl bg-white shadow-2xl">
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-sm font-semibold text-gray-700">New Customer</div>
          <div class="text-[10px] text-gray-400">Create a new customer record</div>
        </div>
        <div class="flex flex-col gap-3 px-5 py-4">
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-gray-400">Customer Name *</label>
            <input ref="newCustNameInput" v-model="newCustData.customer_name" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="Full name" @keydown.esc="showNewCustForm = false" />
          </div>
          <div class="flex gap-3">
            <div class="flex flex-1 flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">Mobile</label>
              <input v-model="newCustData.mobile" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="+91 XXXXX XXXXX" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-1 flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">Email</label>
              <input v-model="newCustData.email" type="email" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc="showNewCustForm = false" />
            </div>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-gray-400">GSTIN</label>
            <input v-model="newCustData.gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-sm uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc="showNewCustForm = false" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-bold uppercase text-gray-400">Address</label>
            <input v-model="newCustData.address_line1" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc="showNewCustForm = false" />
          </div>
          <div class="flex gap-3">
            <div class="flex flex-1 flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">City</label>
              <input v-model="newCustData.city" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="City" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-1 flex-col gap-1">
              <label class="text-[10px] font-bold uppercase text-gray-400">Pincode</label>
              <input v-model="newCustData.pincode" class="rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500" placeholder="678XXX" @keydown.esc="showNewCustForm = false" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button class="rounded border border-gray-300 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-50" @click="showNewCustForm = false">Cancel</button>
          <button class="rounded bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700" :disabled="newCustSaving" @click="saveNewCust">{{ newCustSaving ? 'Saving...' : 'Save &amp; Select' }}</button>
        </div>
      </div>
    </div>

    <!-- ITEM SEARCH POPUP -->
    <div v-if="showSearch" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="closeSearch">
      <div class="flex max-h-[70vh] w-[600px] flex-col rounded-xl bg-white shadow-2xl">
        <div class="border-b border-gray-200 px-4 py-3">
          <div class="mb-2 text-sm font-semibold text-gray-700">Search Item</div>
          <input ref="searchInput" v-model="searchQuery" class="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Type item code or name..." @keydown.esc="closeSearch" @keydown.down.prevent="searchIdx = Math.min(searchIdx + 1, searchResults.length - 1)" @keydown.up.prevent="searchIdx = Math.max(searchIdx - 1, 0)" @keydown.enter.prevent="pickSearchItem" />
        </div>
        <div class="flex-1 overflow-y-auto">
          <table v-if="searchResults.length" class="w-full text-sm">
            <thead><tr class="bg-gray-50"><th class="px-4 py-2 text-left text-[10px] font-bold uppercase text-gray-400">Code</th><th class="px-3 py-2 text-left text-[10px] font-bold uppercase text-gray-400">Item Name</th><th class="px-3 py-2 text-left text-[10px] font-bold uppercase text-gray-400">UOM</th><th class="px-3 py-2 text-right text-[10px] font-bold uppercase text-gray-400">Rate</th><th class="px-3 py-2 text-right text-[10px] font-bold uppercase text-gray-400">Stock</th></tr></thead>
            <tbody>
              <tr v-for="(item, idx) in searchResults" :key="item.item_code" class="cursor-pointer border-b border-gray-100" :class="{ 'bg-blue-50': searchIdx === idx }" @click="pickSearchItemByIdx(idx)" @mouseenter="searchIdx = idx">
                <td class="px-4 py-2 font-mono text-xs">{{ item.item_code }}</td><td class="px-3 py-2">{{ item.item_name }}</td><td class="px-3 py-2 text-gray-400">{{ item.uom }}</td><td class="px-3 py-2 text-right font-mono">{{ item.rate.toFixed(2) }}</td>
                <td class="px-3 py-2 text-right"><span class="rounded-full px-2 py-0.5 text-xs font-bold" :class="item.stock_qty > 20 ? 'bg-green-50 text-green-600' : item.stock_qty > 0 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'">{{ item.stock_qty }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="px-4 py-8 text-center text-xs text-gray-400">No items found</div>
        </div>
        <div class="flex items-center justify-between border-t border-gray-200 px-4 py-2 text-xs text-gray-400">
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Up/Down</kbd> Navigate <kbd class="ml-2 rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Enter</kbd> Select</span>
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Esc</kbd> Close</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice } from '../api.js'

const router = useRouter()
const route = useRoute()
const API = '/api/method/ssplbilling.api.sales_api'

// ==================== BILLING SETTINGS ====================
const billingSeriesConfig = ref([])
const cipherMap = ref([])
const defaultWarehouse = ref('')
const defaultTaxRate = ref(18)
const priceList = ref('Standard Selling')
const printScheme = ref('')
const taxTemplate = ref('')
const costCenter = ref('')

const availableTaxTemplates = ref([])
const availableWarehouses = ref([])
const availableCostCenters = ref([])

const availablePriceLists = computed(() => {
  const lists = billingSeriesConfig.value.map(r => r.price_list).filter(Boolean)
  const unique = [...new Set(lists)]
  return unique.length ? unique : ['Standard Selling']
})

const availablePrintSchemes = computed(() => {
  return [...new Set(billingSeriesConfig.value.map(r => r.print_format).filter(Boolean))]
})

function getSeriesConfig(series) {
  return billingSeriesConfig.value.find(r => r.series === series) || null
}

function syncSeriesConfig(series) {
  const cfg = getSeriesConfig(series)
  if (!cfg) return
  if (cfg.price_list) priceList.value = cfg.price_list
  if (cfg.print_format) printScheme.value = cfg.print_format
  if (cfg.tax_template) taxTemplate.value = cfg.tax_template
  if (cfg.warehouse) defaultWarehouse.value = cfg.warehouse
  if (cfg.cost_center) costCenter.value = cfg.cost_center
}

async function fetchDropdownOptions() {
  // Fetch tax templates, warehouses, cost centers in parallel
  const qs = (doctype, fields, extraFilters = '') => {
    const params = new URLSearchParams({
      doctype,
      fields: JSON.stringify(fields),
      limit_page_length: 100,
    })
    if (extraFilters) params.set('filters', extraFilters)
    return fetch(`/api/method/frappe.client.get_list?${params}`)
      .then(r => r.json())
      .then(j => (j.message || []).map(r => r.name))
      .catch(() => [])
  }

  const [templates, warehouses, costCenters] = await Promise.all([
    qs('Sales Taxes and Charges Template', ['name'], JSON.stringify([['disabled', '=', 0]])),
    qs('Warehouse', ['name'], JSON.stringify([['is_group', '=', 0], ['disabled', '=', 0]])),
    qs('Cost Center', ['name'], JSON.stringify([['is_group', '=', 0], ['disabled', '=', 0]])),
  ])

  availableTaxTemplates.value = templates
  availableWarehouses.value = warehouses
  availableCostCenters.value = costCenters
}

// ==================== PRICE FORMATTING ====================
function fmtPrice(val) {
  const n = Number(val || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(2)
}

function encPrice(val) {
  const str = fmtPrice(val)
  if (!cipherMap.value.length) return str
  return str.replace(/\d/g, d => cipherMap.value[parseInt(d)] ?? d)
}

// ==================== SHARED POST HELPER ====================
async function apiPost(method, params) {
  const res = await fetch(`${API}.${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token || 'fetch',
    },
    body: JSON.stringify(params),
  })
  const json = await res.json()
  if (!res.ok || json.exc) {
    let msg = 'Request failed'
    if (json.exc) {
      try {
        const lines = JSON.parse(json.exc)
        msg = (Array.isArray(lines) ? lines.join('\n') : String(lines))
          .split('\n').filter(Boolean).pop() || msg
      } catch { msg = String(json.exc).split('\n').filter(Boolean).pop() || msg }
    } else if (json._server_messages) {
      try {
        const msgs = JSON.parse(json._server_messages)
        msg = Array.isArray(msgs) ? (msgs[0] || msg) : String(msgs)
      } catch { msg = String(json._server_messages) }
    } else if (json.message && typeof json.message === 'string') {
      msg = json.message
    }
    throw new Error(msg)
  }
  return json.message
}

// ==================== INPUT REFS ====================
const inputRefs = {}
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const customerInput = ref(null)
const modifySearchInput = ref(null)
const seriesSelect = ref(null)
const escWarning = ref(false)
let escWarnTimer = null

// ==================== CUSTOMER DROPDOWN ====================
const custSearch = ref('')
const custResults = ref([])
const showCustDD = ref(false)
const custDDIdx = ref(0)
let custSearchTimeout = null
const customerSearchResource = createResource({ url: `${API}.search_customers` })

function doCustSearch() {
  clearTimeout(custSearchTimeout); custDDIdx.value = 0
  const q = custSearch.value.trim()
  if (q.length < 1) { custResults.value = []; return }
  custSearchTimeout = setTimeout(async () => {
    try {
      await customerSearchResource.submit({ query: q })
      const d = customerSearchResource.data?.message || customerSearchResource.data
      custResults.value = Array.isArray(d) ? d : []
    } catch (e) { custResults.value = [] }
  }, 250)
}

function pickCust(c) {
  customer.value = c.name; custSearch.value = c.customer_name; showCustDD.value = false
  nextTick(() => newCodeInput.value?.focus())
}

// ==================== NEW CUSTOMER SUBWINDOW ====================
const showNewCustForm = ref(false)
const newCustSaving = ref(false)
const newCustNameInput = ref(null)
const newCustData = ref({ customer_name: '', mobile: '', email: '', gstin: '', address_line1: '', city: '', pincode: '' })

function openNewCustForm() {
  newCustData.value = { customer_name: custSearch.value.trim(), mobile: '', email: '', gstin: '', address_line1: '', city: '', pincode: '' }
  showCustDD.value = false
  showNewCustForm.value = true
  nextTick(() => newCustNameInput.value?.focus())
}

async function saveNewCust() {
  if (!newCustData.value.customer_name.trim()) { alert('Customer name is required'); return }
  newCustSaving.value = true
  try {
    const data = await apiPost('quick_create_customer', { data: JSON.stringify(newCustData.value) })
    customer.value = data?.name || newCustData.value.customer_name
    custSearch.value = data?.customer_name || newCustData.value.customer_name
    showNewCustForm.value = false
    nextTick(() => newCodeInput.value?.focus())
  } catch (e) { alert('Error: ' + (e?.message || 'Unknown')) }
  newCustSaving.value = false
}

async function onCustomerEnter() {
  if (custDDIdx.value < custResults.value.length && showCustDD.value) { pickCust(custResults.value[custDDIdx.value]); return }
  if (custDDIdx.value === custResults.value.length && custSearch.value.trim() && showCustDD.value) { openNewCustForm(); return }
  if (!customer.value) { alert('Please select or create a customer'); return }
  showCustDD.value = false; nextTick(() => newCodeInput.value?.focus())
}

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const newItemCode = ref('')
const newQty = ref(1)
const billSaved = ref(false)
const savedInvoiceName = ref(null)   // null = new bill; string = existing/just-saved invoice name
const activeItems = computed(() => items.value.filter(i => !i.deleted))
const deletedCount = computed(() => items.value.filter(i => i.deleted).length)

// ==================== API RESOURCES ====================
const itemLookup = createResource({ url: `${API}.get_item_details` })
const itemSearchResource = createResource({ url: `${API}.search_items` })
const insightResource = createResource({ url: `${API}.get_item_insight` })

const newPending = ref({ item_name: '', uom: '', rate: null })

async function lookupItem(code) {
  try {
    await itemLookup.submit({ item_code: code, price_list: priceList.value, warehouse: defaultWarehouse.value })
    const d = itemLookup.data?.message || itemLookup.data
    return d?.found ? d : null
  } catch (e) { return null }
}

let lookupTimeout = null
watch(newItemCode, (val) => {
  clearTimeout(lookupTimeout); const code = val.trim()
  if (code.length < 2) { newPending.value = { item_name: '', uom: '', rate: null }; return }
  lookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    newPending.value = r ? { item_name: r.item_name, uom: r.uom, rate: r.rate } : { item_name: '', uom: '', rate: null }
  }, 300)
})

const selectedItemData = ref(null)
watch(selectedRow, async (idx) => {
  if (idx >= 0 && idx < items.value.length && !items.value[idx].deleted) {
    const code = items.value[idx].item_code
    try {
      await insightResource.submit({ item_code: code, customer: customer.value || null, warehouse: defaultWarehouse.value || null })
      const d = insightResource.data?.message || insightResource.data
      if (d) {
          selectedItemData.value = {
            item_code: code,
            item_name: items.value[idx].item_name,
            uom: items.value[idx].uom,
            stock: d.stock || [],
            previousPurchases: d.previous_purchases || [],
            priceLists: (d.price_lists || []).map(pl => ({ name: pl.name, rate: pl.rate })),
          }
      }
    } catch (e) { selectedItemData.value = null }
  } else { selectedItemData.value = null }
})

// Re-price all active items when price list changes
watch(priceList, async (newList) => {
  const repriceItem = async (item) => {
    try {
      const price = await fetchItemPrice(item.item_code, newList)
      if (price > 0) item.rate = price
    } catch (e) {}
  }

  const tasks = items.value.filter(i => !i.deleted && i.item_code).map(repriceItem)

  if (newItemCode.value.trim() && newPending.value.rate !== null) {
    tasks.push(
      fetchItemPrice(newItemCode.value.trim(), newList)
        .then(price => { if (price > 0) newPending.value = { ...newPending.value, rate: price } })
        .catch(() => {})
    )
  }

  await Promise.all(tasks)
})

// ==================== FOCUS ====================
function focusField(f, idx) { nextTick(() => { const el = inputRefs[`${f}-${idx}`]; if (el) { el.focus(); el.select() } }) }
function focusNewCode() { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty() { nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() }) }

// ==================== ROW NAV ====================
function findNextActiveRow(from, dir) { let i = from + dir; while (i >= 0 && i < items.value.length) { if (!items.value[i].deleted) return i; i += dir }; return null }
function moveRow(from, dir) { const n = findNextActiveRow(from, dir); if (n !== null) { selectedRow.value = n; focusField('code', n) } else if (dir === 1) { selectedRow.value = -1; focusNewCode() } }
function moveToLastActiveRow() { for (let i = items.value.length - 1; i >= 0; i--) { if (!items.value[i].deleted) { selectedRow.value = i; focusField('code', i); return } } }
function selectRow(idx) { if (!items.value[idx].deleted) selectedRow.value = idx }
function goToNextRow(from) { const n = findNextActiveRow(from, 1); if (n !== null) { selectedRow.value = n; focusField('code', n) } else { selectedRow.value = -1; focusNewCode() } }

// ==================== ITEM ENTRY ====================
async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return; items.value[idx].item_code = code
  const r = await lookupItem(code)
  if (r) { items.value[idx].item_name = r.item_name; items.value[idx].uom = r.uom; items.value[idx].rate = r.rate; items.value[idx].tax_rate = r.tax_rate ?? defaultTaxRate.value; items.value[idx].warehouse = r.warehouse; items.value[idx].deleted = false; focusField('qty', idx) }
  else openSearch(code, idx)
}

async function onNewCodeEnter() {
  const code = newItemCode.value.trim(); if (!code) return
  const r = await lookupItem(code)
  if (r) { newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.rate }; focusNewQty() }
  else openSearch(code, null)
}

async function addNewItem() {
  const code = newItemCode.value.trim(); if (!code) return
  const r = await lookupItem(code)
  if (!r) { openSearch(code, null); return }
  if (r.stock_qty <= 0) { alert('Out of stock: ' + r.item_name); return }
  const ei = items.value.findIndex(i => i.item_code === code && !i.deleted)
  if (ei >= 0) { items.value[ei].qty += newQty.value; selectedRow.value = ei }
  else { items.value.push({ item_code: r.item_code, item_name: r.item_name, uom: r.uom, qty: newQty.value, rate: r.rate, discount: 0, tax_rate: r.tax_rate ?? defaultTaxRate.value, warehouse: r.warehouse, deleted: false }); selectedRow.value = items.value.length - 1 }
  newItemCode.value = ''; newQty.value = 1; newPending.value = { item_name: '', uom: '', rate: null }; focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== ITEM SEARCH POPUP ====================
const showSearch = ref(false); const searchQuery = ref(''); const searchIdx = ref(0); const searchInput = ref(null); let searchTargetRow = null; const searchResults = ref([])

watch(searchQuery, async (q) => {
  searchIdx.value = 0; const t = (q || '').trim(); if (t.length < 1) { searchResults.value = []; return }
  try { await itemSearchResource.submit({ query: t, price_list: priceList.value }); const d = itemSearchResource.data?.message || itemSearchResource.data; searchResults.value = Array.isArray(d) ? d : [] } catch (e) { searchResults.value = [] }
})

function openSearch(prefill, rowIdx) { searchTargetRow = rowIdx; searchQuery.value = prefill || ''; searchIdx.value = 0; showSearch.value = true; nextTick(() => searchInput.value?.focus()) }
function closeSearch() { showSearch.value = false; searchQuery.value = ''; if (searchTargetRow !== null && searchTargetRow >= 0) focusField('code', searchTargetRow); else focusNewCode() }
function pickSearchItem() { if (searchResults.value.length) pickSearchItemByIdx(searchIdx.value) }

function pickSearchItemByIdx(idx) {
  const p = searchResults.value[idx]; if (!p) return
  if (searchTargetRow !== null && searchTargetRow >= 0) {
    const row = items.value[searchTargetRow]; row.item_code = p.item_code; row.item_name = p.item_name; row.uom = p.uom; row.rate = p.rate; row.tax_rate = p.tax_rate ?? defaultTaxRate.value; row.warehouse = p.warehouse || defaultWarehouse.value; row.deleted = false
    showSearch.value = false; selectedRow.value = searchTargetRow; focusField('qty', searchTargetRow)
  } else {
    newItemCode.value = p.item_code; newPending.value = { item_name: p.item_name, uom: p.uom, rate: p.rate }
    showSearch.value = false; nextTick(() => focusNewQty())
  }
}

// ==================== MODIFY BILL ====================
const showModifyBill = ref(false)
const modifyQuery = ref('')
const modifyResults = ref([])
const modifyLoading = ref(false)
let modifySearchTimeout = null

watch(modifyQuery, (q) => {
  clearTimeout(modifySearchTimeout)
  modifySearchTimeout = setTimeout(() => searchBills(q), 300)
})

function openModifyBill() {
  modifyQuery.value = ''
  modifyResults.value = []
  showModifyBill.value = true
  nextTick(() => {
    modifySearchInput.value?.focus()
    searchBills('')
  })
}

async function searchBills(query) {
  modifyLoading.value = true
  try {
    const qs = new URLSearchParams({ query: query || '', limit: 30 })
    const res = await fetch(`${API}.get_sales_invoices?${qs}`)
    const json = await res.json()
    modifyResults.value = Array.isArray(json.message) ? json.message : []
  } catch (e) {
    modifyResults.value = []
  }
  modifyLoading.value = false
}

async function loadInvoice(invoiceName) {
  try {
    const qs = new URLSearchParams({ invoice_name: invoiceName })
    const res = await fetch(`${API}.get_sales_invoice?${qs}`)
    const json = await res.json()
    const inv = json.message
    if (!inv) { alert('Could not load invoice'); return }

    // Populate form with invoice data
    customer.value = inv.customer
    custSearch.value = inv.customer_name
    billDate.value = inv.posting_date
    if (inv.naming_series && availableSeries.value.includes(inv.naming_series)) {
      billSeries.value = inv.naming_series
    }
    paymentMode.value = inv.payment_mode || 'Cash'
    discountPct.value = inv.discount_percentage || 0
    if (inv.tax_template) taxTemplate.value = inv.tax_template
    if (inv.cost_center) costCenter.value = inv.cost_center
    items.value = inv.items.map(i => ({ ...i, discount: i.discount || 0, tax_rate: i.tax_rate ?? defaultTaxRate.value }))
    selectedRow.value = -1
    newItemCode.value = ''
    newQty.value = 1
    newPending.value = { item_name: '', uom: '', rate: null }
    selectedItemData.value = null

    savedInvoiceName.value = inv.name
    billSaved.value = false
    showModifyBill.value = false

    nextTick(() => customerInput.value?.focus())
  } catch (e) {
    alert('Error loading invoice: ' + (e.message || 'Unknown error'))
  }
}

/** Click Edit after save → re-enable the form for updates */
function enterEditMode() {
  billSaved.value = false
  nextTick(() => customerInput.value?.focus())
}

// ==================== BILLING ====================
const billDate = ref(new Date().toISOString().split('T')[0])
const customer = ref('')
const billSeries = ref('')
const paymentMode = ref('Cash')
const discountPct = ref(0)
const availableSeries = ref([])
const nextBillNo = ref('...')

watch(billSeries, (series) => {
  syncSeriesConfig(series)
  fetchNextBillNo()
})

async function fetchSeriesList() {
  try {
    const settings = await fetchBillingSettings()
    const rows = (settings?.billing_series || []).filter(r => r.series)

    if (rows.length) {
      billingSeriesConfig.value = rows
      availableSeries.value = rows.map(r => r.series)
      if (settings.default_warehouse) defaultWarehouse.value = settings.default_warehouse
      try {
        const raw = settings.cipher_map
        if (raw) {
          const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
          if (Array.isArray(parsed) && parsed.length === 10) cipherMap.value = parsed
        }
      } catch (e) { /* non-fatal */ }

      const target = availableSeries.value.includes(billSeries.value)
        ? billSeries.value
        : availableSeries.value[0]

      if (target !== billSeries.value) {
        billSeries.value = target
      } else {
        syncSeriesConfig(target)
        fetchNextBillNo()
      }
      return
    }
  } catch (e) {
    console.warn('[SalesEntry] fetchBillingSettings failed, falling back:', e)
  }

  try {
    const res = await fetch(`${API}.get_naming_series`)
    const json = await res.json()
    const list = json.message
    if (Array.isArray(list) && list.length) {
      availableSeries.value = list
      if (list.includes(billSeries.value)) { fetchNextBillNo() }
      else { billSeries.value = list[0] }
      return
    }
  } catch (e) {}

  fetchNextBillNo()
}

async function fetchNextBillNo() {
  if (!billSeries.value) { nextBillNo.value = '...'; return }
  try {
    const res = await fetch(`${API}.get_next_bill_no?naming_series=${encodeURIComponent(billSeries.value)}`)
    const json = await res.json()
    nextBillNo.value = json.message || '...'
  } catch (e) { nextBillNo.value = '...' }
}

const isExempted = computed(() => taxTemplate.value.toLowerCase().includes('exempt'))
const isInclusive = computed(() => taxTemplate.value.toLowerCase().includes('inclusive'))

// Gross = sum of (qty * rate * (1 - item discount%)) — after item-level discount
const grossTotal = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate * (1 - (i.discount || 0) / 100), 0)
)

// Subtotal: ex-tax amount for inclusive, gross otherwise
const subtotal = computed(() => {
  if (isInclusive.value) {
    return activeItems.value.reduce((s, i) => {
      const amt = i.qty * i.rate * (1 - (i.discount || 0) / 100)
      return s + amt / (1 + (i.tax_rate || 0) / 100)
    }, 0)
  }
  return grossTotal.value
})

const discountAmt = computed(() => subtotal.value * (discountPct.value / 100))
const taxableAmt = computed(() => subtotal.value - discountAmt.value)

const totalTax = computed(() => {
  if (isExempted.value) return 0
  if (isInclusive.value) {
    return (grossTotal.value - subtotal.value) * (1 - discountPct.value / 100)
  }
  return activeItems.value.reduce((s, i) => {
    const a = i.qty * i.rate * (1 - (i.discount || 0) / 100)
    return s + (a - a * (discountPct.value / 100)) * (i.tax_rate / 100)
  }, 0)
})

const grandTotal = computed(() => {
  if (isInclusive.value) return grossTotal.value * (1 - discountPct.value / 100)
  return taxableAmt.value + totalTax.value
})

async function saveBill() {
  if (!customer.value.trim()) { alert('Please enter a customer'); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    customer: customer.value,
    date: billDate.value,
    naming_series: billSeries.value,
    payment_mode: paymentMode.value,
    discount_percentage: discountPct.value,
    tax_template: taxTemplate.value || '',
    cost_center: costCenter.value || '',
    items: activeItems.value.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      price_list_rate: i.rate,
      discount_percentage: i.discount || 0,
      rate: i.rate * (1 - (i.discount || 0) / 100),
      warehouse: i.warehouse || defaultWarehouse.value,
      cost_center: costCenter.value || '',
    })),
  }

  try {
    let result
    if (savedInvoiceName.value) {
      // Update existing draft invoice
      result = await apiPost('update_sales_invoice', {
        data: JSON.stringify({ ...payload, invoice_name: savedInvoiceName.value }),
      })
    } else {
      // Create new invoice
      result = await apiPost('create_sales_invoice', {
        data: JSON.stringify(payload),
      })
      savedInvoiceName.value = result?.invoice_name || null
    }

    billSaved.value = true
    fetchNextBillNo()
    alert(`Invoice ${result?.invoice_name || ''} saved!\nTotal: ₹${(result?.grand_total || grandTotal.value).toFixed(2)}\n\nPress Esc to start a new bill`)
  } catch (e) {
    alert('Error: ' + (e?.message || 'Failed to save invoice'))
  }
}

function startNewBill() {
  items.value = []; selectedRow.value = -1; customer.value = ''; custSearch.value = ''
  discountPct.value = 0; newItemCode.value = ''; newQty.value = 1; paymentMode.value = 'Cash'
  billSaved.value = false; savedInvoiceName.value = null; selectedItemData.value = null
  escWarning.value = false; clearTimeout(escWarnTimer)
  nextTick(() => seriesSelect.value?.focus())
}

function printBill() { alert('Print preview coming soon') }
function cancelBill() { startNewBill() }

// ==================== GLOBAL KEYS ====================
function handleKeydown(e) {
  if (showSearch.value || showCustDD.value || showNewCustForm.value || showModifyBill.value) return
  if (e.key === 'Escape') {
    if (billSaved.value) { startNewBill(); return }
    // If bill has content, require a second Esc to exit
    const hasContent = items.value.length > 0 || customer.value
    if (hasContent && !escWarning.value) {
      escWarning.value = true
      clearTimeout(escWarnTimer)
      escWarnTimer = setTimeout(() => { escWarning.value = false }, 3000)
      return
    }
    escWarning.value = false
    clearTimeout(escWarnTimer)
    router.push('/')
    return
  }
  if (e.ctrlKey && e.key === 's') { e.preventDefault(); saveBill() }
  if (e.key === 'Delete' && selectedRow.value >= 0) { const el = document.activeElement; if (!el || el.tagName !== 'INPUT') { e.preventDefault(); softDelete(selectedRow.value) } }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  fetchSeriesList()
  fetchDropdownOptions()
  if (route.query.invoice) {
    loadInvoice(route.query.invoice)
  } else {
    nextTick(() => seriesSelect.value?.focus())
  }
})
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>
