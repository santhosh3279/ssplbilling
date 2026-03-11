<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-white' : 'h-screen flex flex-col'">
    <div class="flex h-full flex-col">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100" @click="handleBack">&larr; Dashboard</button>
        <span class="text-sm text-gray-300">|</span>
        <span class="text-sm font-semibold text-gray-800">Purchase Entry</span>
        <button class="rounded border border-gray-300 px-2.5 py-1 text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-1.5" @click="openModifyBill">
          <span>Modify Bill</span>
          <kbd class="rounded border bg-gray-50 px-1 text-[10px] text-gray-400">F3</kbd>
        </button>
      </div>
      <div class="flex items-center gap-3 text-sm text-gray-600">
        <div class="flex items-center rounded border border-gray-200 bg-white shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-gray-500 hover:bg-gray-100">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-gray-200 bg-gray-50 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-gray-400 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-gray-600 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-gray-500 hover:bg-gray-100">&plus;</button>
        </div>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Up/Down</kbd> Navigate rows</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Tab</kbd> Next column</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">F3</kbd> Modify</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Esc</kbd> {{ billSaved ? 'New Bill' : 'Back' }}</span>
      </div>
    </header>

    <div class="border-b border-gray-200 bg-white px-4 py-2">
      <div class="flex items-center gap-6">
        <!-- Series -->
        <div class="flex items-center gap-2">
          <label class="text-[10px] font-bold uppercase text-gray-400 whitespace-nowrap">Series</label>
          <select 
            ref="seriesSelect" 
            v-model="billSeries" 
            :disabled="billDocStatus !== 0" 
            class="rounded border border-gray-300 bg-white px-2 py-1 text-sm font-bold outline-none focus:border-blue-500 disabled:bg-gray-50"
            @keydown.enter.prevent="openSupplierSearch"
          >
            <option v-for="s in availableSeries" :key="s">{{ s }}</option>
          </select>
        </div>

        <!-- Bill No -->
        <div class="flex items-center gap-2 border-l border-gray-100 pl-6">
          <label class="text-[10px] font-bold uppercase text-gray-400 whitespace-nowrap">Bill No</label>
          <div class="text-xl font-bold text-gray-900 tabular-nums" style="font-family: 'Poppins', sans-serif">
            {{ nextBillNo }}
          </div>
        </div>

        <!-- Supplier Section (Flex-1 to take middle space) -->
        <div class="flex-1 flex items-center gap-4 border-l border-gray-100 pl-6 overflow-hidden">
          <label class="text-[10px] font-bold uppercase text-gray-400 whitespace-nowrap">Supplier</label>
          
          <!-- Name & Address -->
          <div class="flex items-baseline gap-4 min-w-0">
            <div 
              ref="supplierInput"
              class="shrink-0 max-w-[300px] truncate text-xl font-bold transition-colors cursor-pointer outline-none hover:text-blue-600 focus:text-blue-600 leading-none"
              :class="supplier ? 'text-gray-900' : 'text-gray-300 italic'"
              style="font-family: 'Poppins', sans-serif"
              @click="openSupplierSearch"
              tabindex="0"
              @keydown.enter.prevent="openSupplierSearch"
              @keydown.space.prevent="openSupplierSearch"
            >
              {{ suppSearch || 'Not Selected' }}
            </div>

            <div v-if="selectedSupplierDetails" class="flex items-center gap-3 min-w-0">
              <span v-if="selectedSupplierDetails.address_line1" class="truncate max-w-[350px] text-xl text-gray-500 font-normal leading-none" :title="selectedSupplierDetails.address_line1">
                {{ selectedSupplierDetails.address_line1 }}{{ selectedSupplierDetails.city ? ', ' + selectedSupplierDetails.city : '' }}
              </span>
              <span v-if="selectedSupplierDetails.mobile_no" class="whitespace-nowrap text-[10px] text-gray-400 font-bold leading-none">
                PH: {{ selectedSupplierDetails.mobile_no }}
              </span>
            </div>
          </div>

          <!-- Stats Group -->
          <div v-if="selectedSupplierDetails" class="flex items-center gap-6 ml-auto mr-6">
            <!-- Last Invoice Date -->
            <div v-if="selectedSupplierDetails.last_invoice_date" class="flex flex-col items-end leading-none">
              <span class="text-[8px] uppercase tracking-wider text-gray-400 font-bold mb-0.5">Last Inv</span>
              <span class="text-sm text-gray-700 font-medium">
                {{ new Date(selectedSupplierDetails.last_invoice_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) }}
              </span>
            </div>

            <!-- Ledger Balance -->
            <div class="flex flex-col items-end leading-none border-l border-gray-100 pl-6">
              <span class="text-[8px] uppercase tracking-wider text-gray-400 font-bold mb-0.5">Ledger Bal</span>
              <span :class="selectedSupplierDetails.balance > 0 ? 'text-red-500' : 'text-green-500'" class="text-xl font-bold tabular-nums">
                &#8377;{{ Math.abs(selectedSupplierDetails.balance || 0).toFixed(2) }} <span class="text-[10px] font-bold">{{ selectedSupplierDetails.balance > 0 ? 'DR' : 'CR' }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Bill Date -->
        <div class="flex items-center gap-3 border-l border-gray-100 pl-6 whitespace-nowrap">
          <label class="text-[10px] font-bold uppercase text-gray-400">Bill Date</label>
          <input 
            ref="dateInput"
            v-model="billDate" 
            type="date" 
            :disabled="billDocStatus !== 0"
            class="rounded border border-gray-300 bg-white px-2 py-0.5 text-xl font-bold text-gray-900 outline-none focus:border-blue-500 disabled:bg-gray-50 tabular-nums"
            style="font-family: 'Poppins', sans-serif"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-1 overflow-hidden">
      <!-- MAIN CONTENT -->
      <div class="flex w-full flex-col">
        <div class="flex flex-[7] flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-sm border-collapse border-l border-t border-gray-300">
              <thead>
                <tr class="sticky top-0 z-10 bg-gray-50 border-b border-gray-300">
                  <th class="w-8 border-r border-b border-gray-300 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-800">#</th>
                  <th class="w-32 border-r border-b border-gray-300 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-1000">Item Code</th>
                  <th class="border-r border-b border-gray-300 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-1000">Item Name</th>
                  <th class="w-16 border-r border-b border-gray-300 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-1000">Qty</th>
                  <th class="w-14 border-r border-b border-gray-300 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-1000">UOM</th>
                  <th class="w-24 border-r border-b border-gray-300 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-1000">Rate</th>
                  <th class="w-16 border-r border-b border-gray-300 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-1000">Disc %</th>
                  <th class="w-16 border-r border-b border-gray-300 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-1000">Tax %</th>
                  <th class="w-24 border-r border-b border-gray-300 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-1000">Amount</th>
                  <th class="w-8 border-b border-gray-300"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="cursor-pointer border-b border-gray-300 outline-none" :class="{ 'bg-blue-200 border-l-2 border-l-blue-500': selectedRow === idx && !item.deleted, 'bg-red-50/40': item.deleted, 'hover:bg-blue-50': !item.deleted && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-3 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full font-bold" :class="item.deleted ? 'bg-red-100 text-red-400' : 'bg-gray-100 text-gray-500'" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">{{ idx + 1 }}</span></td>
                  <td class="px-2 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="billDocStatus !== 0" class="w-full rounded border border-gray-300 bg-white px-2 py-0.5 font-mono outline-none focus:border-blue-500 disabled:bg-gray-50" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-600'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span :class="item.deleted ? 'text-red-300 line-through' : 'text-gray-800'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</span><span v-if="item.deleted" class="ml-1 font-semibold text-red-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">DELETED</span></td>
                  <td class="px-2 border-r border-gray-300 text-right" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="billDocStatus !== 0" min="1" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono focus:border-blue-400 focus:bg-white focus:outline-none disabled:cursor-not-allowed" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onQtyEnter(idx)" @keydown.tab.prevent="onQtyEnter(idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-700'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.qty }}</span>
                  </td>
                  <td class="px-2 text-gray-600 border-r border-gray-300" :class="item.deleted ? 'text-gray-300' : ''" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-2 border-r border-gray-300 text-right" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="billDocStatus !== 0" step="0.01" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono focus:border-blue-400 focus:bg-white focus:outline-none disabled:cursor-not-allowed" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('discount', idx)" @keydown.tab.prevent="focusField('discount', idx)" @keydown.shift.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-700'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.rate.toFixed(2) }}</span>
                  </td>
                  <td class="px-2 border-r border-gray-300 text-right" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'discount', idx)" type="number" v-model.number="item.discount" :disabled="billDocStatus !== 0" step="0.5" min="0" max="100" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono focus:border-blue-400 focus:bg-white focus:outline-none disabled:cursor-not-allowed" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.shift.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-700'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.discount || 0 }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-600'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ isExempted ? 0 : (item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-gray-300 font-mono font-semibold" :class="item.deleted ? 'text-gray-300 line-through' : 'text-gray-800'" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.deleted ? '' : (item.qty * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2) }}</td>
                  <td class="px-2 text-center" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button v-if="!item.deleted" class="rounded px-1 py-0.5 text-gray-300 hover:bg-red-50 hover:text-red-500" :style="{ fontSize: dynamicRowStyle.fontSize }" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else class="rounded px-1 py-0.5 font-semibold text-blue-400 hover:bg-blue-50 hover:text-blue-600" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }" @click.stop="restoreItem(idx)">&larr;</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="billDocStatus === 0" class="border-b border-gray-300" :class="selectedRow === -1 ? 'bg-blue-100' : 'bg-gray-50/50'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-3 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-500" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">+</span></td>
                  <td class="px-2 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-gray-300 bg-white px-2 py-1 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-100" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Item code" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" /></td>
                  <td class="px-2 text-gray-600 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.item_name || '--' }}</td>
                  <td class="px-2 text-right border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><input ref="newQtyInput" v-model.number="newQty" type="number" min="1" class="w-14 rounded border border-gray-300 bg-white px-1 py-1 text-right font-mono outline-none focus:border-blue-500" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="addNewItem" @keydown.shift.tab.prevent="focusNewCode" /></td>
                  <td class="px-2 text-gray-600 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.uom || '--' }}</td>
                  <td class="px-2 text-right border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="newPending.rate" class="font-mono text-gray-700">{{ newPending.rate.toFixed(2) }}</span>
                    <span v-else class="text-gray-600">--</span>
                  </td>
                  <td class="px-2 text-right font-mono text-gray-600 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">0</td>
                  <td class="px-2 text-right font-mono text-gray-600 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ isExempted ? 0 : defaultTaxRate }}</td>
                  <td class="px-2 text-right font-mono text-gray-600 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.rate ? (newQty * newPending.rate).toFixed(2) : '--' }}</td>
                  <td class="border-gray-300"></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-1 text-[10px] text-gray-600">
            <div class="flex items-center gap-6">
              <span>{{ activeItems.length }} item{{ activeItems.length !== 1 ? 's' : '' }}{{ deletedCount > 0 ? ' (' + deletedCount + ' deleted)' : '' }}</span>
              
              <div class="h-4 w-px bg-gray-300 mx-2"></div>

              <!-- Warehouse -->
              <div class="flex items-center gap-1.5">
                <label class="text-[10px] font-bold uppercase text-gray-500">WH</label>
                <select v-model="defaultWarehouse" :disabled="billDocStatus !== 0" class="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] outline-none focus:border-blue-500 disabled:bg-gray-50 max-w-[120px]">
                  <option value="">-- Default --</option>
                  <option v-for="w in availableWarehouses" :key="w" :value="w">{{ w }}</option>
                </select>
              </div>
              <!-- Price List -->
              <div class="flex items-center gap-1.5">
                <label class="text-[10px] font-bold uppercase text-gray-500">Price</label>
                <select v-model="priceList" :disabled="billDocStatus !== 0" class="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] outline-none focus:border-blue-500 disabled:bg-gray-50 max-w-[120px]">
                  <option v-for="pl in availablePriceLists" :key="pl" :value="pl">{{ pl }}</option>
                </select>
              </div>
              <!-- Tax Template -->
              <div class="flex items-center gap-1.5">
                <label class="text-[10px] font-bold uppercase text-gray-500">Tax</label>
                <select v-model="taxTemplate" :disabled="billDocStatus !== 0" class="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] outline-none focus:border-blue-500 disabled:bg-gray-50 min-w-[200px] max-w-[220px]">
                  <option value="">-- None --</option>
                  <option v-for="t in availableTaxTemplates" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <!-- Cost Center -->
              <div class="flex items-center gap-1.5">
                <label class="text-[10px] font-bold uppercase text-gray-500">CC</label>
                <select v-model="costCenter" :disabled="billDocStatus !== 0" class="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] outline-none focus:border-blue-500 disabled:bg-gray-50 min-w-[200px] max-w-[220px]">
                  <option value="">-- Default --</option>
                  <option v-for="cc in availableCostCenters" :key="cc" :value="cc">{{ cc }}</option>
                </select>
              </div>
            </div>
            <span class="font-mono font-semibold text-gray-500">Grid Subtotal: &#8377;{{ subtotal.toFixed(2) }}</span>
          </div>
        </div>

        <!-- BOTTOM PANEL (Insight + Calculation) -->
        <div class="flex flex-[4] border-t border-gray-200 bg-white overflow-hidden">
          <!-- Left Column: Item Insight -->
          <div class="flex-1 overflow-y-auto px-4 py-3 border-r border-gray-100">
            <div class="mb-1.5 text-xs font-bold uppercase tracking-wider text-gray-600">Item Insight <span v-if="selectedItemData" class="ml-2 font-normal normal-case text-gray-300">{{ selectedItemData.item_code }}</span></div>
            <template v-if="selectedItemData">
              <div class="flex gap-6">
                <div class="flex-1">
                  <div class="mb-1 text-[10px] font-bold uppercase text-gray-600">Stock</div>
                  <div v-if="selectedItemData.stock.length">
                    <div v-for="s in selectedItemData.stock" :key="s.warehouse" class="flex justify-between text-sm">
                      <span class="text-gray-500">{{ s.warehouse }}</span>
                      <span class="rounded-full px-2 py-0.5 font-bold" :class="s.actual_qty > 20 ? 'bg-green-50 text-green-600' : s.actual_qty > 0 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'">{{ s.actual_qty }}</span>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-300">No stock data</div>
                </div>
                <div class="flex-1">
                  <div class="mb-1 text-[10px] font-bold uppercase text-gray-600">Previous Purchases</div>
                  <div v-if="selectedItemData.previousPurchases && selectedItemData.previousPurchases.length" class="flex flex-col">
                    <div v-for="p in selectedItemData.previousPurchases" :key="p.name" class="flex items-center gap-2 border-b border-gray-50 py-0.5 text-[11px] last:border-0">
                      <span class="w-24 truncate font-medium text-blue-600" :title="p.name">{{ p.name }}</span>
                      <span class="text-gray-600">{{ p.date }}</span>
                      <span class="font-mono font-bold text-gray-700">&#8377;{{ p.rate.toFixed(2) }}</span>
                      <span class="text-gray-600">x{{ p.qty }}</span>
                      <span v-if="p.discount > 0" class="font-bold text-red-500">-{{ p.discount }}%</span>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-300">--</div>
                </div>
                <div class="flex-1">
                  <div class="mb-1 text-[10px] font-bold uppercase text-gray-600">Prices</div>
                  <div class="flex flex-wrap gap-3">
                    <span v-for="pl in selectedItemData.priceLists" :key="pl.name" class="rounded bg-amber-50 px-2.5 py-1 text-lg">
                      <span class="text-gray-500">{{ pl.name }}:</span>
                      <span class="ml-1 font-mono font-bold text-amber-700">&#8377;{{ encPrice(pl.rate || 0) }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </template>
            <div v-else class="py-2 text-sm text-gray-300">Click a row to see stock, last purchase &amp; prices</div>
          </div>

          <!-- Right Column: Bill Summary (Split into two sub-cols) -->
          <div class="flex flex-1 max-w-[600px] bg-gray-50/50 p-4">
            <!-- Summary Left: Calculations -->
            <div class="flex-1 pr-6 border-r border-gray-200">
              <div class="mb-3 text-xs font-bold uppercase tracking-wider text-gray-600">Calculations</div>
              <div class="flex flex-col gap-2">
                <div class="flex justify-between text-lg font-semibold">
                  <span class="text-gray-600">Total (Gross)</span>
                  <span class="font-mono text-gray-800">&#8377;{{ totalBeforeItemDiscount.toFixed(2) }}</span>
                </div>
                <div class="flex justify-between text-lg">
                  <span class="text-gray-600 font-semibold">Item Discount</span>
                  <span class="font-mono font-semibold text-red-500">-&#8377;{{ itemDiscountTotal.toFixed(2) }}</span>
                </div>
                <div class="flex justify-between text-xl border-t border-gray-100 pt-1">
                  <span class="text-gray-700 font-bold">Subtotal</span>
                  <span class="font-mono font-bold text-gray-900">&#8377;{{ subtotal.toFixed(2) }}</span>
                </div>
                <div class="flex items-center justify-between text-lg">
                  <div class="flex items-center gap-1.5">
                    <span class="text-gray-600 font-semibold">Discount</span>
                    <input ref="discountInput" type="number" v-model.number="discountPct" :disabled="billDocStatus !== 0" min="0" max="100" step="0.5" class="w-20 rounded border border-gray-300 px-1.5 py-1 text-right text-lg font-bold outline-none focus:border-blue-400 disabled:bg-gray-50" @keydown.enter="saveButton?.focus()" />
                    <span class="text-base text-gray-600 font-bold">%</span>
                  </div>
                  <span class="font-mono font-semibold text-red-500">-&#8377;{{ discountAmt.toFixed(2) }}</span>
                </div>
                <div class="flex justify-between text-lg font-semibold">
                  <span class="text-gray-600">Tax</span>
                  <span class="font-mono text-gray-800">+&#8377;{{ totalTax.toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <!-- Summary Right: Grand Total & Actions -->
            <div class="flex-1 pl-6 flex flex-col justify-between">
              <div>
                <div class="text-xs font-bold uppercase tracking-wider text-gray-600 mb-1">Total Payable</div>
                <div class="font-mono text-6xl font-bold text-blue-600 leading-none">&#8377;{{ grandTotal.toFixed(2) }}</div>
                
                <div v-if="billSaved" class="mt-3 flex items-center justify-between rounded bg-green-50 px-3 py-1.5 text-sm text-green-700">
                  <span class="font-bold">{{ savedInvoiceName }}</span>
                  <span class="font-semibold uppercase text-[10px]">Saved</span>
                </div>
              </div>

              <div class="flex flex-col gap-2">
                <button v-if="billSaved && billDocStatus === 0" @click="enterEditMode" class="w-full rounded-lg border border-amber-400 bg-amber-50 py-2.5 text-center text-sm font-semibold text-amber-700 transition hover:bg-amber-100">✏ Edit Bill</button>
                <button v-else-if="!billSaved" ref="saveButton" @click="saveBill" class="w-full rounded-lg py-2.5 text-center text-sm font-semibold text-white transition shadow-lg" :class="savedInvoiceName ? 'bg-orange-500 hover:bg-orange-600' : 'bg-blue-600 hover:bg-blue-700'">{{ savedInvoiceName ? 'Update Bill' : 'Save Bill (Ctrl+S)' }}</button>
                
                <div class="flex gap-2">
                  <button class="flex-1 rounded-lg border border-gray-300 py-2 text-center text-sm font-semibold text-gray-600 hover:bg-gray-50" @click="cancelBill">{{ billSaved ? 'New Bill' : 'Cancel' }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- =================== MODIFY BILL SUBWINDOW =================== -->
    <div v-if="showModifyBill" class="fixed inset-0 z-50 flex justify-center bg-black/40 pt-12" @click.self="showModifyBill = false">
      <div class="flex max-h-[85vh] w-[680px] flex-col rounded-xl bg-white shadow-2xl">
        <!-- Header -->
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-sm font-semibold text-gray-700">Modify Existing Bill</div>
          <div class="mt-0.5 text-sm text-gray-600">Search and select a Draft invoice to edit</div>
        </div>

        <!-- Search & Date Filter -->
        <div class="flex items-center gap-3 border-b border-gray-100 px-5 py-3">
          <input
            ref="modifySearchInput"
            v-model="modifyQuery"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Search by invoice no. or supplier name..."
            @keydown.esc="showModifyBill = false"
          />
          <div class="flex items-center rounded border border-gray-300">
            <button @click="changeModifyDate(-1)" class="px-2 py-1.5 text-gray-500 hover:bg-gray-50 border-r border-gray-300">&larr;</button>
            <input
              type="date"
              v-model="modifyDate"
              class="w-36 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
            />
            <button @click="changeModifyDate(1)" class="px-2 py-1.5 text-gray-500 hover:bg-gray-50 border-l border-gray-300">&rarr;</button>
          </div>
        </div>

        <!-- Results -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="modifyLoading" class="flex items-center justify-center py-10 text-sm text-gray-600">Loading...</div>
          <table v-else-if="modifyResults.length" class="w-full text-sm">
            <thead>
              <tr class="sticky top-0 bg-gray-50">
                <th class="px-4 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-600">Invoice No.</th>
                <th class="px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-600">Supplier</th>
                <th class="px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-600">Date</th>
                <th class="px-3 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-gray-600">Amount</th>
                <th class="px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="inv in modifyResults"
                :key="inv.name"
                class="cursor-pointer border-b border-gray-100 hover:bg-blue-50"
                @click="loadInvoice(inv.name)"
              >
                <td class="px-4 py-2.5 font-mono text-sm font-semibold text-blue-700">{{ inv.name }}</td>
                <td class="px-3 py-2.5">
                  <div class="text-sm font-medium text-gray-800">{{ inv.supplier_name }}</div>
                  <div class="text-[10px] text-gray-600">{{ inv.supplier }}</div>
                </td>
                <td class="px-3 py-2.5 text-sm text-gray-500">{{ inv.posting_date }}</td>
                <td class="px-3 py-2.5 text-right font-mono text-sm font-semibold text-gray-800">&#8377;{{ inv.grand_total.toFixed(2) }}</td>
                <td class="px-3 py-2.5">
                  <span class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase" :class="{
                    'bg-gray-100 text-gray-600': inv.status === 'Draft',
                    'bg-green-100 text-green-700': inv.status === 'Paid',
                    'bg-blue-100 text-blue-700': inv.status === 'Submitted',
                    'bg-red-100 text-red-700': inv.status === 'Cancelled'
                  }">{{ inv.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="flex flex-col items-center py-10 text-sm text-gray-600">
            <div>No draft invoices found</div>
            <div v-if="modifyQuery" class="mt-1 text-gray-300">Try a different search term</div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between border-t border-gray-100 px-5 py-3">
          <span class="text-sm text-gray-600">Click a row to open it for editing</span>
          <button class="rounded border border-gray-300 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-50" @click="showModifyBill = false">Close</button>
        </div>
      </div>
    </div>

    <!-- SUPPLIER SEARCH MODAL -->
    <CustomerSearchModal
      ref="suppSearchModalRef"
      :show="showSupplierSearchModal"
      initial-type="Supplier"
      :skip-date-filter="true"
      @close="closeSupplierSearchModal"
      @select="pickSupp"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Purchase"
      :price-list="priceList"
      :warehouse="defaultWarehouse"
      :skip-date-filter="true"
      @close="closeItemSearch"
      @select="pickItem"
    />

    <JumpToRowModal 
      v-model:show="showJumpModal"
      :max-rows="items.length" 
      @jump="handleJump" 
    />

    <!-- PRICE LIST UPDATE SUB-WINDOW -->
    <PriceListUpdate
      v-if="showPriceListUpdate"
      :is-sub-window="true"
      :item-code="priceListItemCode"
      :selected-price-list="priceList"
      :initial-discount="priceListUpdateDiscount"
      @close="closePriceListUpdate"
      @saved="onPriceListSaved"
    />

    <!-- DISCARD BILL MODAL -->
    <div v-if="showDiscardModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60" @click.self="showDiscardModal = false">
      <div class="w-[450px] overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div class="bg-amber-50 px-6 py-6 flex items-center gap-4 border-b border-amber-100">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl text-amber-600">⚠️</div>
          <div>
            <div class="text-xl font-bold text-gray-900">Discard Unsaved Bill?</div>
            <div class="text-sm text-amber-700">You have unsaved items in this bill.</div>
          </div>
        </div>
        <div class="p-6">
          <p class="text-gray-600 leading-relaxed">Are you sure you want to go back to the dashboard? All unsaved changes will be permanently lost.</p>
        </div>
        <div class="flex justify-end gap-3 border-t border-gray-100 bg-gray-50 px-6 py-4">
          <button 
            ref="stayHereBtn"
            class="rounded-xl border border-gray-300 bg-white px-6 py-2.5 text-sm font-bold text-gray-700 hover:bg-gray-100 transition-all shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
            @click="showDiscardModal = false"
          >
            Stay Here
          </button>
          <button 
            class="rounded-xl bg-red-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-red-700 shadow-md hover:shadow-lg transition-all"
            @click="router.push('/')"
          >
            Discard & Exit
          </button>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice, searchItems, fetchItemDetails, frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import ItemSearch from '../components/ItemSearch.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import PriceListUpdate from './PriceListUpdate.vue'
import { useItemCache } from '../services/itemCache.js'


const router = useRouter()
const route = useRoute()
const API = '/api/method/ssplbilling.api.purchase_api'

const { items: cachedItems, refreshItemCache, lookupItemInCache, lastSync } = useItemCache()

const props = defineProps({
  isSubWindow: {
    type: Boolean,
    default: false
  },
  invoiceName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

// ==================== BILLING SETTINGS ====================
const billingSeriesConfig = ref([])
const cipherMap = ref([])
const defaultWarehouse = ref('')
const defaultTaxRate = ref(18)
const priceList = ref('Standard Buying')
const taxTemplate = ref('')
const costCenter = ref('')

const availableTaxTemplates = ref([])
const availableWarehouses = ref([])
const availableCostCenters = ref([])

const availablePriceLists = computed(() => {
  return ['Standard Buying']
})

async function fetchDropdownOptions() {
  try {
    const [templates, warehouses, costCenters] = await Promise.all([
      frappeGet('frappe.client.get_list', {
        doctype: 'Purchase Taxes and Charges Template',
        fields: ['name'],
        filters: [['disabled', '=', 0]],
        limit_page_length: 100,
      }),
      frappeGet('frappe.client.get_list', {
        doctype: 'Warehouse',
        fields: ['name'],
        filters: [['is_group', '=', 0], ['disabled', '=', 0]],
        limit_page_length: 100,
      }),
      frappeGet('frappe.client.get_list', {
        doctype: 'Cost Center',
        fields: ['name'],
        filters: [['is_group', '=', 0], ['disabled', '=', 0]],
        limit_page_length: 100,
      }),
    ])

    availableTaxTemplates.value = templates.map(r => r.name)
    availableWarehouses.value = warehouses.map(r => r.name)
    availableCostCenters.value = costCenters.map(r => r.name)
  } catch (e) {
    console.warn('[PurchaseEntry] fetchDropdownOptions failed:', e)
  }
}

// ==================== PRICE FORMATTING ====================
function fmtPrice(val) {
  const n = Number(val || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(2)
}

function fmtDate(d) {
  if (!d) return ''
  return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

function encPrice(val) {
  return fmtPrice(val)
}

// ==================== SHARED POST HELPER ====================
async function apiPost(method, params) {
  return frappePost(`ssplbilling.api.purchase_api.${method}`, params)
}

// ==================== INPUT REFS ====================
const inputRefs = {}
const rowRefs   = {}
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const supplierInput = ref(null)
const modifySearchInput = ref(null)
const seriesSelect = ref(null)
const dateInput = ref(null)
const discountInput = ref(null)
const saveButton = ref(null)
const stayHereBtn = ref(null)
const suppSearchModalRef = ref(null)

// ==================== SUPPLIER SEARCH ====================
const suppSearch = ref('')
const showSupplierSearchModal = ref(false)
const selectedSupplierDetails = ref(null)

function openSupplierSearch() {
  showSupplierSearchModal.value = true
  suppSearch.value = ''
  nextTick(() => {
    suppSearchModalRef.value?.closeSubForm()
    suppSearchModalRef.value?.focus()
  })
}

function pickSupp(s) {
  supplier.value = s.name; 
  suppSearch.value = s.label || s.supplier_name; 
  showSupplierSearchModal.value = false; 
  selectedSupplierDetails.value = s;
  nextTick(() => newCodeInput.value?.focus())
}

function closeSupplierSearchModal() {
  showSupplierSearchModal.value = false
}

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const newItemCode = ref('')
const newQty = ref(1)
const billSaved = ref(false)
const billDocStatus = ref(0) // 0=Draft, 1=Submitted, 2=Cancelled
const showJumpModal = ref(false)
const savedInvoiceName = ref(null)
const showDiscardModal = ref(false)
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)
const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`,
  paddingTop: '0px',
  paddingBottom: '0px'
}))

const activeItems = computed(() => items.value.filter(i => !i.deleted))
const deletedCount = computed(() => items.value.filter(i => i.deleted).length)

// ==================== API RESOURCES ====================
const itemLookup = createResource({ url: `${API}.get_item_details` })
const insightResource = createResource({ url: `${API}.get_item_insight` })

const newPending = ref({ item_name: '', uom: '', rate: null })

async function lookupItem(code) {
  // 1. Try local cache first
  const cached = lookupItemInCache(code)
  if (cached) {
    return {
      found: true,
      item_code: cached.item_code,
      item_name: cached.item_name,
      uom: cached.uom,
      rate: cached.price || cached.rate || 0,
      stock_qty: cached.stock || 0,
      tax_rate: cached.tax_rate,
      warehouse: cached.warehouse
    }
  }

  // 2. Fallback to API if not found or cache empty
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

watch(showDiscardModal, (val) => {
  if (val) {
    nextTick(() => {
      stayHereBtn.value?.focus()
    })
  }
})

const selectedItemData = ref(null)

async function loadItemInsight(code, itemName = '', uom = '') {
  if (!code) {
    selectedItemData.value = null
    return
  }

  // 1. Fetch from local cache (Instant)
  const cached = lookupItemInCache(code)
  
  selectedItemData.value = {
    item_code: code,
    item_name: itemName || cached?.item_name || '',
    uom: uom || cached?.uom || '',
    stock: cached?.stock != null ? [{ warehouse: cached.warehouse || 'Total', actual_qty: cached.stock }] : [],
    previousPurchases: [], // Historical lookup not yet cached for Purchase
    priceLists: cached?.price_lists || [],
  }
}

watch(selectedRow, async (idx) => {
  if (idx >= 0 && idx < items.value.length && !items.value[idx].deleted) {
    const item = items.value[idx]
    await loadItemInsight(item.item_code, item.item_name, item.uom)
  } else {
    selectedItemData.value = null
  }
})

// Re-price all active items when price list changes
watch(priceList, (newList) => {
  const getPrice = (itemCode) => {
    const cached = lookupItemInCache(itemCode)
    if (cached?.price_lists) {
      const pl = cached.price_lists.find(p => p.name === newList)
      return pl ? pl.rate : 0
    }
    return 0
  }

  // Update active items in grid
  items.value.forEach(item => {
    if (!item.deleted && item.item_code) {
      const price = getPrice(item.item_code)
      if (price > 0) item.rate = price
    }
  })

  // Update pending item
  if (newItemCode.value.trim() && newPending.value.rate !== null) {
    const price = getPrice(newItemCode.value.trim())
    if (price > 0) newPending.value.rate = price
  }
})

// ==================== FOCUS ====================
function focusField(f, idx) { nextTick(() => { const el = inputRefs[`${f}-${idx}`]; if (el) { el.focus(); el.select() } }) }
function focusRow(idx)    { nextTick(() => rowRefs[idx]?.focus()) }
function focusNewCode()   { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty() {
  if (newItemCode.value.trim() && newPending.value.item_name) {
    loadItemInsight(newItemCode.value.trim(), newPending.value.item_name, newPending.value.uom)
  }
  nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() })
}

// ==================== ROW NAV ====================
function findNextActiveRow(from, dir) { let i = from + dir; while (i >= 0 && i < items.value.length) { if (!items.value[i].deleted) return i; i += dir }; return null }
function moveRow(from, dir) { const n = findNextActiveRow(from, dir); if (n !== null) { selectedRow.value = n; focusRow(n) } else if (dir === 1) { selectedRow.value = -1; focusNewCode() } }
function moveToLastActiveRow() { for (let i = items.value.length - 1; i >= 0; i--) { if (!items.value[i].deleted) { selectedRow.value = i; focusRow(i); return } } }
function selectRow(idx) { if (!items.value[idx].deleted) { selectedRow.value = idx; focusRow(idx) } }
function goToNextRow(from) { const n = findNextActiveRow(from, 1); if (n !== null) { selectedRow.value = n; focusRow(n) } else { selectedRow.value = -1; focusNewCode() } }
function enterRow(idx) { if (!items.value[idx]?.deleted && billDocStatus.value === 0) focusField('code', idx) }
function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); enterRow(idx) }
}

// ==================== ITEM ENTRY ====================
async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return; items.value[idx].item_code = code
  const r = await lookupItem(code)
  if (r) {
    items.value[idx].item_name = r.item_name; items.value[idx].uom = r.uom; items.value[idx].rate = r.rate; items.value[idx].tax_rate = r.tax_rate ?? defaultTaxRate.value; items.value[idx].warehouse = r.warehouse; items.value[idx].deleted = false;
    loadItemInsight(code, r.item_name, r.uom)
    focusField('qty', idx)
  }
  else openSearch(code, idx)
}

let emptyCodeEnters = 0
async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) {
    emptyCodeEnters++
    if (emptyCodeEnters >= 2) {
      emptyCodeEnters = 0
      openSearch('', null)
    }
    return
  }
  emptyCodeEnters = 0
  const r = await lookupItem(code)
  if (r) { newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.rate }; focusNewQty() }
  else openSearch(code, null)
}

async function addNewItem() {
  const code = newItemCode.value.trim(); if (!code) return
  const r = await lookupItem(code)
  if (!r) { openSearch(code, null); return }
  
  // Show Price List Update BEFORE adding to grid and resetting
  priceListUpdateTargetIdx.value = -1
  priceListItemCode.value = r.item_code
  priceListUpdateDiscount.value = 0 // Default for new item
  showPriceListUpdate.value = true
}

/** Triggered when Enter is pressed on Qty field of an existing row */
function onQtyEnter(idx) {
  priceListUpdateTargetIdx.value = idx
  priceListItemCode.value = items.value[idx].item_code
  priceListUpdateDiscount.value = items.value[idx].discount || 0
  showPriceListUpdate.value = true
}

/** Called after PriceListUpdate is closed */
function finalizeAddItem() {
  const code = newItemCode.value.trim()
  const r = newPending.value
  const ei = items.value.findIndex(i => i.item_code === code && !i.deleted)
  if (ei >= 0) { 
    items.value[ei].qty += newQty.value; 
  } else { 
    items.value.push({ 
      item_code: code, 
      item_name: r.item_name, 
      uom: r.uom, 
      qty: newQty.value, 
      rate: r.rate, 
      discount: priceListUpdateDiscount.value, 
      tax_rate: r.tax_rate ?? defaultTaxRate.value, 
      warehouse: r.warehouse, 
      deleted: false 
    }); 
  }
  newItemCode.value = ''; 
  newQty.value = 1; 
  newPending.value = { item_name: '', uom: '', rate: null }; 
  priceListUpdateDiscount.value = 0;
  selectedRow.value = -1; // Reset selection so we stay in "new entry" mode
  focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== PRICE LIST UPDATE ====================
const showPriceListUpdate = ref(false)
const priceListItemCode = ref('')
const priceListUpdateDiscount = ref(0)
const priceListUpdateTargetIdx = ref(null) // null = none, -1 = new row, 0+ = existing row

function closePriceListUpdate() {
  const targetIdx = priceListUpdateTargetIdx.value
  showPriceListUpdate.value = false
  
  if (targetIdx === -1) {
    finalizeAddItem()
  } else if (targetIdx !== null && targetIdx >= 0) {
    focusField('rate', targetIdx)
  }
  priceListUpdateTargetIdx.value = null
}

function onPriceListSaved(data) {
  const { changedPrices, discount: newDisc } = data
  
  // Update local discount ref first
  priceListUpdateDiscount.value = newDisc

  // If the current price list was updated, sync its rate back to the entry
  const current = changedPrices.find(p => p.price_list === priceList.value)
  
  const targetIdx = priceListUpdateTargetIdx.value
  if (targetIdx === -1) {
    if (current) newPending.value.rate = current.rate
    // finalizeAddItem will pick up priceListUpdateDiscount.value
  } else if (targetIdx !== null && targetIdx >= 0) {
    if (current) items.value[targetIdx].rate = current.rate
    items.value[targetIdx].discount = newDisc
  }
}

// ==================== ITEM SEARCH MODAL ====================
const showItemSearchModal = ref(false)
const itemSearchModalRef = ref(null)
let itemSearchTargetRow = null

async function openSearch(prefill = '', rowIdx = null) {
  itemSearchTargetRow = rowIdx
  showItemSearchModal.value = true
  nextTick(() => {
    itemSearchModalRef.value?.focus()
  })
}

function closeItemSearch() {
  showItemSearchModal.value = false
  if (itemSearchTargetRow !== null) {
    focusField('code', itemSearchTargetRow)
  } else {
    focusNewCode()
  }
}

async function pickItem(item) {
  showItemSearchModal.value = false
  let finalRate = item.rate || item.price || 0
  let finalTax = item.tax_rate ?? defaultTaxRate.value
  let finalWh = item.warehouse || defaultWarehouse.value
  let finalName = item.item_name
  let finalUom = item.uom
  
  try {
    const r = await lookupItem(item.item_code)
    if (r) {
      finalRate = r.rate
      finalTax = r.tax_rate ?? defaultTaxRate.value
      finalWh = r.warehouse || defaultWarehouse.value
      finalName = r.item_name
      finalUom = r.uom
    }
  } catch (e) {}

  if (itemSearchTargetRow !== null) {
    const row = items.value[itemSearchTargetRow]
    row.item_code = item.item_code
    row.item_name = finalName
    row.uom = finalUom
    row.rate = finalRate
    row.tax_rate = finalTax
    row.warehouse = finalWh
    row.deleted = false
    selectedRow.value = itemSearchTargetRow
    focusField('qty', itemSearchTargetRow)
  } else {
    newItemCode.value = item.item_code
    newPending.value = { item_name: finalName, uom: finalUom, rate: finalRate, tax_rate: finalTax, warehouse: finalWh }
    nextTick(() => focusNewQty())
  }
}

// ==================== MODIFY BILL ====================
const showModifyBill = ref(false)
const modifyQuery = ref('')
const modifyDate = ref(getTodayIST())
const modifyResults = ref([])
const modifyLoading = ref(false)
let modifySearchTimeout = null

watch(modifyQuery, (q) => {
  clearTimeout(modifySearchTimeout)
  modifySearchTimeout = setTimeout(() => searchBills(q), 300)
})

watch(modifyDate, (d) => {
  searchBills(modifyQuery.value)
})

function changeModifyDate(days) {
  const d = new Date(modifyDate.value)
  d.setDate(d.getDate() + days)
  modifyDate.value = d.toISOString().split('T')[0]
}

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
    modifyResults.value = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoices', {
      query: query || '',
      limit: 30,
      posting_date: modifyDate.value,
    })
  } catch (e) {
    modifyResults.value = []
  }
  modifyLoading.value = false
}

async function loadInvoice(invoiceName) {
  try {
    const inv = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoice', { invoice_name: invoiceName })
    if (!inv) { alert('Could not load invoice'); return }

    supplier.value = inv.supplier
    suppSearch.value = inv.supplier_name
    billDate.value = inv.posting_date
    if (inv.naming_series && availableSeries.value.includes(inv.naming_series)) {
      billSeries.value = inv.naming_series
    }
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
    billDocStatus.value = inv.docstatus
    billSaved.value = inv.docstatus !== 0
    showModifyBill.value = false

    selectedSupplierDetails.value = {
      name: inv.supplier,
      supplier_name: inv.supplier_name,
      balance: 0,
    }

    nextTick(() => supplierInput.value?.focus())
  } catch (e) {
    alert('Error loading invoice: ' + (e.message || 'Unknown error'))
  }
}

function enterEditMode() {
  if (billDocStatus.value !== 0) {
    alert('Cannot edit a submitted/cancelled invoice.')
    return
  }
  billSaved.value = false
  nextTick(() => supplierInput.value?.focus())
}

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ==================== BILLING ====================
const billDate = ref(getTodayIST())
const supplier = ref('')
const billSeries = ref('')

const discountPct = ref(0)
const availableSeries = ref([])
const nextBillNo = ref('...')

watch(billSeries, () => {
  fetchNextBillNo()
})

async function fetchSeriesList() {
  try {
    const list = await frappeGet('ssplbilling.api.purchase_api.get_naming_series')
    if (Array.isArray(list) && list.length) {
      availableSeries.value = list
      if (list.includes(billSeries.value)) { fetchNextBillNo() }
      else { billSeries.value = list[0] }
    }
  } catch (e) {}

  fetchNextBillNo()
}

async function fetchNextBillNo() {
  if (!billSeries.value) { nextBillNo.value = '...'; return }
  try {
    const res = await frappeGet('ssplbilling.api.purchase_api.get_next_bill_no', { naming_series: billSeries.value })
    nextBillNo.value = res || '...'
  } catch (e) { nextBillNo.value = '...' }
}

const isExempted = computed(() => taxTemplate.value.toLowerCase().includes('exempt'))
const isInclusive = computed(() => taxTemplate.value.toLowerCase().includes('inclusive'))

const grossTotal = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate * (1 - (i.discount || 0) / 100), 0)
)

const totalBeforeItemDiscount = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate, 0)
)

const itemDiscountTotal = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate * ((i.discount || 0) / 100), 0)
)

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
  if (!supplier.value.trim()) { alert('Please enter a supplier'); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    supplier: supplier.value,
    date: billDate.value,
    naming_series: billSeries.value,
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
      result = await apiPost('update_purchase_invoice', {
        data: JSON.stringify({ ...payload, invoice_name: savedInvoiceName.value }),
      })
    } else {
      result = await apiPost('create_purchase_invoice', {
        data: JSON.stringify(payload),
      })
      savedInvoiceName.value = result?.invoice_name || null
    }

    billSaved.value = true
    billDocStatus.value = 0
    fetchNextBillNo()
    alert('Bill saved successfully: ' + savedInvoiceName.value)
  } catch (e) {
    alert('Error: ' + (e?.message || 'Failed to save invoice'))
  }
}

function startNewBill() {
  items.value = []; selectedRow.value = -1; supplier.value = ''; suppSearch.value = ''
  discountPct.value = 0; newItemCode.value = ''; newQty.value = 1; 
  billDate.value = getTodayIST()
  billSaved.value = false; billDocStatus.value = 0; savedInvoiceName.value = null; selectedItemData.value = null
  selectedSupplierDetails.value = null
  nextTick(() => seriesSelect.value?.focus())
}

function cancelBill() { startNewBill() }

function handleJump(targetNo) {
  if (items.value.length === 0) return
  let targetIdx = targetNo - 1
  if (targetIdx >= items.value.length) targetIdx = items.value.length - 1
  if (items.value[targetIdx].deleted) {
    const prev = findNextActiveRow(targetIdx, -1)
    if (prev !== null) targetIdx = prev
    else {
      const next = findNextActiveRow(targetIdx, 1)
      if (next !== null) targetIdx = next
      else return
    }
  }
  selectedRow.value = targetIdx
  focusRow(targetIdx)
}

function handleBack() {
  if (activeItems.value.length > 0 && !billSaved.value) {
    showDiscardModal.value = true
  } else {
    if (props.isSubWindow) {
      emit('close')
      return
    }
    router.push('/')
  }
}

import { useShortcuts } from '../services/shortcutManager'
import { purchaseEntryShortcuts } from '../shortcuts/purchaseEntryShortcuts'

useShortcuts(purchaseEntryShortcuts({
  save: () => saveBill(),
  newCustomer: () => openSupplierSearch(),
  searchItem: () => openSearch('', null),
  openModifyBill: () => openModifyBill(),
  deleteRow: () => {
    if (selectedRow.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      softDelete(selectedRow.value)
    }
  },
  focusSeries: () => seriesSelect.value?.focus(),
  toggleDiscountSave: () => {
    if (document.activeElement === discountInput.value) {
      saveButton.value?.focus()
    } else {
      discountInput.value?.focus()
      discountInput.value?.select()
    }
  },
  contextualBack: () => {
    if (showJumpModal.value) { showJumpModal.value = false; return }
    if (showDiscardModal.value) { showDiscardModal.value = false; return }
    if (showPriceListUpdate.value) { showPriceListUpdate.value = false; return }
    if (showSupplierSearchModal.value) { closeSupplierSearchModal(); return }
    if (showItemSearchModal.value) { closeItemSearch(); return }
    if (showModifyBill.value) { showModifyBill.value = false; return }
    handleBack()
  }
}))

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  fetchSeriesList()
  fetchDropdownOptions()
  
  // Ensure item cache is correctly populated for Purchase
  const { lastParams: cacheLastParams } = useItemCache()
  const needsRefresh = !cachedItems.value.length || 
    (Date.now() - lastSync.value) > 5 * 60 * 1000 ||
    cacheLastParams.value.searchType !== 'Purchase' ||
    cacheLastParams.value.priceList !== priceList.value ||
    cacheLastParams.value.warehouse !== defaultWarehouse.value

  if (needsRefresh) {
    refreshItemCache('Purchase', priceList.value, defaultWarehouse.value)
  }
  
  if (props.invoiceName) {
    loadInvoice(props.invoiceName)
  } else {
    nextTick(() => seriesSelect.value?.focus())
  }
})

onUnmounted(() => {
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
})
</script>
