<template>
  <div class="flex h-screen flex-col">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-gray-500 hover:bg-gray-100" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-gray-300">|</span>
        <span class="text-sm font-semibold text-gray-800">Sales Entry</span>
        <button class="rounded border border-gray-300 px-2.5 py-1 text-sm text-gray-600 hover:bg-gray-50" @click="openModifyBill">Modify Bill</button>
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
        <span><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Ctrl+S</kbd> Save</span>
        <span v-if="escWarning" class="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">Press Esc again to discard and exit</span>
        <span v-else><kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 font-mono text-[10px]">Esc</kbd> {{ billSaved ? 'New Bill' : 'Back' }}</span>
      </div>
    </header>

    <div class="flex flex-col border-b border-gray-200 bg-white px-4 py-3">
      <div class="flex flex-wrap items-center justify-between gap-6">
        <!-- Left Side: Basic Info Row -->
        <div class="flex flex-wrap items-center gap-x-6 gap-y-2">

          <!-- Series -->
          <div class="flex items-center gap-3">
            <label class="text-[10px] font-bold uppercase text-gray-500 whitespace-nowrap">Series</label>
            <select ref="seriesSelect" v-model="billSeries" :disabled="billDocStatus !== 0" class="rounded border border-gray-300 bg-white px-2 py-1 text-sm font-bold outline-none focus:border-blue-500 disabled:bg-gray-50" @keydown.enter.prevent="openCustomerSearch">
              <option v-for="s in availableSeries" :key="s">{{ s }}</option>
            </select>
          </div>

          <!-- Bill No -->
          <div class="flex items-center gap-2 w-[180px]">
            <label class="text-[10px] font-bold uppercase text-gray-500 whitespace-nowrap">Bill No</label>
            <div class="text-2xl font-medium text-gray-900 tracking-normal truncate" style="font-family: 'Poppins', sans-serif">
              {{ nextBillNo }}
            </div>
          </div>

          <!-- Customer -->
          <div class="flex items-center gap-2 w-[400px]">
            <label class="text-[10px] font-bold uppercase text-gray-500 whitespace-nowrap">Customer</label>
            <div class="flex-1 overflow-hidden flex flex-col">
              <div 
                ref="customerInput"
                class="truncate text-2xl font-medium transition-colors cursor-pointer outline-none hover:text-blue-600 focus:text-blue-600 leading-none"
                :class="customer ? 'text-gray-900' : 'text-gray-300 italic'"
                style="font-family: 'Poppins', sans-serif"
                @click="openCustomerSearch"
                tabindex="0"
                @keydown.enter.prevent="openCustomerSearch"
                @keydown.space.prevent="openCustomerSearch"
              >
                {{ custSearch || 'Not Selected' }}
              </div>
              <div v-if="selectedCustomerDetails" class="flex items-center gap-3 mt-0.5 text-[11px] font-bold">
                <span :class="selectedCustomerDetails.balance > 0 ? 'text-red-500' : 'text-green-500'">
                  Bal: &#8377;{{ Math.abs(selectedCustomerDetails.balance || 0).toFixed(2) }} {{ selectedCustomerDetails.balance > 0 ? 'DR' : 'CR' }}
                </span>
                <span v-if="selectedCustomerDetails.address_line1" class="text-gray-400 truncate max-w-[200px]" :title="selectedCustomerDetails.address_line1">
                  {{ selectedCustomerDetails.address_line1 }}{{ selectedCustomerDetails.city ? ', ' + selectedCustomerDetails.city : '' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Side: Date -->
        <div class="flex items-center gap-3">
          <label class="text-[10px] font-bold uppercase text-gray-500 whitespace-nowrap">Bill Date</label>
          <div class="text-2xl font-medium tracking-tight text-gray-900" style="font-family: 'Poppins', sans-serif">
            {{ fmtDate(billDate) }}
          </div>
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
                <tr v-for="(item, idx) in items" :key="idx" class="cursor-pointer border-b border-gray-300" :class="{ 'bg-blue-50': selectedRow === idx && !item.deleted, 'bg-red-50/40': item.deleted, 'hover:bg-blue-50/50': !item.deleted }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)">
                  <td class="px-3 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full font-bold" :class="item.deleted ? 'bg-red-100 text-red-400' : 'bg-gray-100 text-gray-500'" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">{{ idx + 1 }}</span></td>
                  <td class="px-2 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="billDocStatus !== 0" class="w-full rounded border border-gray-300 bg-white px-2 py-0.5 font-mono outline-none focus:border-blue-500 disabled:bg-gray-50" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono" :class="item.deleted ? 'text-gray-300' : 'text-gray-600'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 border-r border-gray-300" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span :class="item.deleted ? 'text-red-300 line-through' : 'text-gray-800'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</span><span v-if="item.deleted" class="ml-1 font-semibold text-red-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">DELETED</span></td>
                  <td class="px-2 border-r border-gray-300 text-right" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="billDocStatus !== 0" min="1" class="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-right font-mono focus:border-blue-400 focus:bg-white focus:outline-none disabled:cursor-not-allowed" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
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
                <tr v-if="billDocStatus === 0" class="border-b border-gray-300 bg-gray-50/50" :style="{ fontSize: dynamicRowStyle.fontSize }">
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
              <!-- Print Format -->
              <div class="flex items-center gap-1.5">
                <label class="text-[10px] font-bold uppercase text-gray-500">Print</label>
                <select v-model="printScheme" class="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[10px] outline-none focus:border-blue-500 shadow-sm max-w-[150px]">
                  <option value="">-- Default --</option>
                  <option v-for="pf in availablePrintSchemes" :key="pf" :value="pf">{{ pf }}</option>
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
                  <div class="mb-1 text-[10px] font-bold uppercase text-gray-600">Previous Sales</div>
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
                  <div class="flex flex-wrap gap-2">
                    <span v-for="pl in selectedItemData.priceLists" :key="pl.name" class="rounded bg-amber-50 px-1.5 py-0.5 text-[11px]">
                      <span class="text-gray-500">{{ pl.name }}:</span>
                      <span class="ml-0.5 font-mono font-bold text-amber-700">&#8377;{{ encPrice(pl.rate || 0) }}</span>
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
                  <button class="flex-1 rounded-lg border border-gray-300 py-2 text-center text-sm font-semibold text-gray-600 hover:bg-gray-50" @click="printBill">Print</button>
                  <button class="flex-1 rounded-lg border border-red-200 py-2 text-center text-sm font-semibold text-red-500 hover:bg-red-50" @click="cancelBill">{{ billSaved ? 'New Bill' : 'Cancel' }}</button>
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
            placeholder="Search by invoice no. or customer name..."
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
                <th class="px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-gray-600">Customer</th>
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
                  <div class="text-sm font-medium text-gray-800">{{ inv.customer_name }}</div>
                  <div class="text-[10px] text-gray-600">{{ inv.customer }}</div>
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

    <!-- EDIT CUSTOMER SUBWINDOW -->
    <div v-if="showEditCustForm" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40" @click.self="showEditCustForm = false">
      <div class="w-[600px] rounded-xl bg-white shadow-2xl">
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-xl font-bold text-gray-700">Modify Customer Details</div>
          <div class="text-sm text-gray-600">Update information for {{ selectedCustomerDetails?.customer_name }}</div>
        </div>
        <div class="flex flex-col gap-4 px-6 py-5 max-h-[75vh] overflow-y-auto">
          <!-- Basic Info Row -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Customer Name *</label>
            <input ref="editCustNameInput" v-model="editCustData.customer_name" class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Full name" @keydown.esc="showEditCustForm = false" />
          </div>

          <!-- Contact Row -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile</label>
              <input v-model="editCustData.mobile" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="+91 XXXXX XXXXX" @keydown.esc="showEditCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
              <input v-model="editCustData.email" type="email" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc="showEditCustForm = false" />
            </div>
          </div>

          <!-- GSTIN -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">GSTIN</label>
            <input v-model="editCustData.gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-base uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc="showEditCustForm = false" />
          </div>

          <!-- Address Lines -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 1</label>
            <input v-model="editCustData.address_line1" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc="showEditCustForm = false" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 2</label>
              <input v-model="editCustData.address_line2" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Area / Locality" @keydown.esc="showEditCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 3</label>
              <input v-model="editCustData.address_line3" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Landmark" @keydown.esc="showEditCustForm = false" />
            </div>
          </div>

          <!-- City, Pincode, State -->
          <div class="grid grid-cols-3 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">City</label>
              <input v-model="editCustData.city" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="City" @keydown.esc="showEditCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Pincode</label>
              <input v-model="editCustData.pincode" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="678XXX" @keydown.esc="showEditCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">State</label>
              <input v-model="editCustData.state" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="State" @keydown.esc="showEditCustForm = false" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
          <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-100 transition-colors" @click="showEditCustForm = false">Cancel</button>
          <button class="rounded bg-orange-600 px-6 py-2 font-bold text-white hover:bg-orange-700 shadow-md hover:shadow-lg transition-all flex items-center gap-2" :disabled="newCustSaving" @click="saveEditCust">
            {{ newCustSaving ? 'Updating...' : 'Update Details' }}
            <kbd v-if="!newCustSaving" class="rounded border border-orange-500 bg-orange-500 px-1.5 py-0.5 font-mono text-xs text-white shadow-sm">End</kbd>
          </button>
        </div>
      </div>
    </div>
    <div v-if="showNewCustForm" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/40" @click.self="showNewCustForm = false">
      <div class="w-[600px] rounded-xl bg-white shadow-2xl">
        <div class="border-b border-gray-200 px-5 py-4">
          <div class="text-xl font-bold text-gray-700">New Customer</div>
          <div class="text-sm text-gray-600">Enter customer details to create a new record</div>
        </div>
        <div class="flex flex-col gap-4 px-6 py-5 max-h-[75vh] overflow-y-auto">
          <!-- Basic Info Row -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Customer Name *</label>
            <input ref="newCustNameInput" v-model="newCustData.customer_name" class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Full name" @keydown.esc="showNewCustForm = false" />
          </div>

          <!-- Contact Row -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile</label>
              <input v-model="newCustData.mobile" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="+91 XXXXX XXXXX" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
              <input v-model="newCustData.email" type="email" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc="showNewCustForm = false" />
            </div>
          </div>

          <!-- GSTIN -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">GSTIN</label>
            <input v-model="newCustData.gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-base uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc="showNewCustForm = false" />
          </div>

          <!-- Address Lines -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 1</label>
            <input v-model="newCustData.address_line1" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc="showNewCustForm = false" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 2</label>
              <input v-model="newCustData.address_line2" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Area / Locality" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 3</label>
              <input v-model="newCustData.address_line3" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Landmark" @keydown.esc="showNewCustForm = false" />
            </div>
          </div>

          <!-- City, Pincode, State -->
          <div class="grid grid-cols-3 gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">City</label>
              <input v-model="newCustData.city" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="City" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Pincode</label>
              <input v-model="newCustData.pincode" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="678XXX" @keydown.esc="showNewCustForm = false" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">State</label>
              <input v-model="newCustData.state" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="State" @keydown.esc="showNewCustForm = false" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
          <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-100 transition-colors" @click="showNewCustForm = false">Cancel</button>
          <button class="rounded bg-blue-600 px-6 py-2 font-bold text-white hover:bg-blue-700 shadow-md hover:shadow-lg transition-all flex items-center gap-2" :disabled="newCustSaving" @click="saveNewCust">
            {{ newCustSaving ? 'Saving...' : 'Save & Select Customer' }}
            <kbd v-if="!newCustSaving" class="rounded border border-blue-500 bg-blue-500 px-1.5 py-0.5 font-mono text-xs text-white shadow-sm">End</kbd>
          </button>
        </div>
      </div>
    </div>

    <!-- ITEM SEARCH POPUP -->
    <div v-if="showSearch" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="closeSearch">
      <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden">

        <div class="border-b border-gray-200 px-4 py-3 flex items-center justify-between bg-gray-50/50">
          <div class="text-2xl font-semibold text-gray-700">Search Item</div>
          <button 
            @click="refreshLocalItems" 
            :disabled="isSyncing"
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 hover:bg-blue-100 disabled:opacity-50"
          >
            <span v-if="isSyncing" class="animate-spin">⏳</span>
            <span v-else>🔄</span>
            {{ isSyncing ? 'Syncing...' : 'Refresh Items' }} <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
        </div>
        <div class="border-b border-gray-200 px-4 py-3">
          <input
            ref="searchInput"
            v-model="searchQuery"
            class="w-full rounded border border-gray-300 bg-white px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Type item code or name..."
            @keydown.esc="closeSearch"
            @keydown.down.prevent="searchIdx = Math.min(searchIdx + 1, searchResults.length - 1)"
            @keydown.up.prevent="searchIdx = Math.max(searchIdx - 1, 0)"
            @keydown.enter.prevent="pickSearchItem"
          />
       </div>
        <div class="flex-1 overflow-y-auto">
          <table v-if="searchResults.length" class="w-full text-2xl">
            <thead><tr class="bg-gray-50"><th class="px-4 py-3 text-left text-lg font-bold uppercase text-gray-600">Code</th><th class="px-3 py-3 text-left text-lg font-bold uppercase text-gray-600">Item Name</th><th class="px-3 py-3 text-left text-lg font-bold uppercase text-gray-600">UOM</th><th class="px-3 py-3 text-right text-lg font-bold uppercase text-gray-600">Rate</th><th class="px-3 py-3 text-right text-lg font-bold uppercase text-gray-600">Stock</th></tr></thead>
            <tbody>
              <tr v-for="(item, idx) in searchResults" :key="item.item_code" class="cursor-pointer border-b border-gray-100" :class="{ 'bg-blue-50': searchIdx === idx }" @click="pickSearchItemByIdx(idx)" @mouseenter="searchIdx = idx">
                <td class="px-4 py-3 font-mono text-2xl">{{ item.item_code }}</td><td class="px-3 py-3">{{ item.item_name }}</td><td class="px-3 py-3 text-gray-600">{{ item.uom }}</td><td class="px-3 py-3 text-right font-mono">{{ item.rate.toFixed(2) }}</td>
                <td class="px-3 py-3 text-right"><span class="rounded-full px-3 py-1 text-xl font-bold" :class="item.stock_qty > 20 ? 'bg-green-50 text-green-600' : item.stock_qty > 0 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'">{{ item.stock_qty }}</span></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="px-4 py-8 text-center text-2xl text-gray-600">No items found</div>
        </div>
        <div class="flex items-center justify-between border-t border-gray-200 px-4 py-3 text-lg text-gray-600">
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Up/Down</kbd> Navigate <kbd class="ml-2 rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Enter</kbd> Select</span>
          <span><kbd class="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-base">Esc</kbd> Close</span>
        </div>
      </div>
    </div>
    <!-- CUSTOMER SEARCH MODAL -->
    <div v-if="showCustomerSearchModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCustomerSearchModal = false">
      <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden">

        <!-- Header -->
        <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between bg-gray-50">
          <div>
            <div class="text-2xl font-semibold text-gray-700">Detailed Customer Search</div>
            <div class="text-lg text-gray-500">View contact info and select customer</div>
          </div>
          <div class="flex items-center gap-3">
            <button 
              @click="openNewCustForm" 
              class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm"
            >
              New Customer <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F2</kbd>
            </button>
            <button 
              @click="openEditCustForm" 
              v-if="selectedCustomerDetails"
              class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm"
            >
              Edit Details <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F3</kbd>
            </button>
            <button 
              @click="fetchAllCustomers(true)" 
              class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 hover:bg-blue-100"
            >
              🔄 Refresh <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
            </button>
            <button @click="showCustomerSearchModal = false" class="text-2xl text-gray-400 hover:text-gray-600">✕</button>
          </div>
        </div>

        <!-- Search input -->
        <div class="border-b border-gray-100 p-4">
          <input
            ref="custSearchInput"
            v-model="custSearch"
            @input="doCustSearch"
            class="w-full rounded border border-gray-300 px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Type customer name or mobile..."
            @keydown.esc="showCustomerSearchModal = false"
            @keydown.down.prevent="custDDIdx = Math.min(custDDIdx + 1, custResults.length - 1)"
            @keydown.up.prevent="custDDIdx = Math.max(custDDIdx - 1, 0)"
            @keydown.enter.prevent="custResults[custDDIdx] && pickCust(custResults[custDDIdx])"
          />
        </div>

        <!-- Results Table -->
        <div class="flex-1 overflow-y-auto">
          <table class="w-full text-2xl">
            <thead class="sticky top-0 bg-white shadow-sm">
              <tr class="text-lg font-bold uppercase tracking-wider text-gray-600 border-b">
                <th class="px-5 py-3 text-left">Customer Name</th>
                <th class="px-5 py-3 text-left">Mobile Number</th>
                <th class="px-5 py-3 text-right">Balance</th>
                <th class="px-5 py-3 text-left">Address</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="(c, idx) in custResults"
                :key="c.name"
                class="cursor-pointer hover:bg-blue-50/50"
                :class="{ 'bg-blue-50': custDDIdx === idx }"
                @click="pickCust(c)"
                @mouseenter="custDDIdx = idx"
              >
                <td class="px-5 py-2">
                  <div class="font-medium text-gray-800">{{ c.customer_name }}</div>
                </td>
                <td class="px-5 py-2 text-gray-600">
                  {{ c.mobile_no || '--' }}
                </td>
                <td class="px-5 py-2 text-right">
                  <span :class="c.balance > 0 ? 'text-red-600' : c.balance < 0 ? 'text-green-600' : 'text-gray-400'" class="font-bold">
                    &#8377;{{ (c.balance || 0).toFixed(2) }}
                  </span>
                </td>
                <td class="px-5 py-2 text-gray-500 text-lg truncate max-w-[300px]">
                  {{ c.address_line1 }}{{ c.city ? ', ' + c.city : '' }}
                </td>
              </tr>
              <tr v-if="!custResults.length">
                <td colspan="4" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                  No customers found matching "{{ custSearch }}"
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Detail Footer -->
        <div v-if="custResults[custDDIdx]" class="border-t border-gray-200 bg-blue-50/30 px-6 py-3">
          <div class="flex flex-wrap gap-x-8 gap-y-2">
            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase text-gray-400">Current Balance</span>
              <span class="text-xl font-bold" :class="custResults[custDDIdx].balance > 0 ? 'text-red-600' : 'text-green-600'">
                &#8377;{{ (custResults[custDDIdx].balance || 0).toFixed(2) }}
                <span class="text-xs font-normal uppercase ml-1">{{ custResults[custDDIdx].balance > 0 ? 'Debit' : 'Credit' }}</span>
              </span>
            </div>
            <div class="flex flex-col flex-1">
              <span class="text-[10px] font-bold uppercase text-gray-400">Address</span>
              <span class="text-lg text-gray-700">
                <template v-if="custResults[custDDIdx].address_line1">
                  {{ custResults[custDDIdx].address_line1 }}{{ custResults[custDDIdx].city ? ', ' + custResults[custDDIdx].city : '' }}{{ custResults[custDDIdx].pincode ? ' - ' + custResults[custDDIdx].pincode : '' }}
                </template>
                <template v-else>
                  <span class="text-gray-300 italic">No address provided</span>
                </template>
              </span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase text-gray-400">Mobile</span>
              <span class="text-lg text-gray-700">{{ custResults[custDDIdx].mobile_no || '--' }}</span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-100 bg-gray-50 px-5 py-4 flex items-center justify-between text-lg text-gray-500">
          <div class="flex gap-4">
            <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F2</kbd> New Customer</span>
            <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F3</kbd> Edit</span>
            <span><kbd class="rounded border bg-white px-2 py-1 font-mono">Enter</kbd> to Select</span>
          </div>
          <button @click="showCustomerSearchModal = false" class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-50">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice, searchCustomers, frappeGet, frappePost } from '../api.js'
import { localDb } from '../services/localDb'

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
  try {
    const [templates, warehouses, costCenters] = await Promise.all([
      frappeGet('frappe.client.get_list', {
        doctype: 'Sales Taxes and Charges Template',
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
    console.warn('[SalesEntry] fetchDropdownOptions failed:', e)
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
  const str = fmtPrice(val)
  if (!cipherMap.value.length) return str
  return str.replace(/\d/g, d => cipherMap.value[parseInt(d)] ?? d)
}

// ==================== SHARED POST HELPER ====================
async function apiPost(method, params) {
  return frappePost(`ssplbilling.api.sales_api.${method}`, params)
}

// ==================== INPUT REFS ====================
const inputRefs = {}
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const customerInput = ref(null)
const custSearchInput = ref(null)
const searchInput = ref(null)
const modifySearchInput = ref(null)
const seriesSelect = ref(null)
const discountInput = ref(null)
const saveButton = ref(null)
const escWarning = ref(false)
let escWarnTimer = null

// ==================== CUSTOMER DROPDOWN ====================
const custSearch = ref('')
const allCustomers = ref([])
const custResults = ref([])
const showCustDD = ref(false)
const showCustomerSearchModal = ref(false)
const custDDIdx = ref(0)
const selectedCustomerDetails = ref(null)

async function fetchAllCustomers(force = false) {
  try {
    // 1. Try loading customers from local IndexedDB first (unless forcing)
    let custFromDb = force ? [] : await localDb.getAllCustomers()
    
    // 2. If empty or forced, sync from server
    if (!custFromDb || custFromDb.length === 0) {
      custFromDb = await frappeGet('ssplbilling.api.sales_api.get_all_customers_detailed')
      if (custFromDb && custFromDb.length) {
        await localDb.clearStore('customers')
        await localDb.saveCustomers(custFromDb)
      }
    }

    allCustomers.value = custFromDb || []
    filterCustomers()
  } catch (e) {
    console.error('Failed to fetch customers:', e)
  }
}

function filterCustomers() {
  const q = custSearch.value.toLowerCase().trim()
  if (!q) {
    custResults.value = allCustomers.value.slice(0, 100)
    return
  }
  custResults.value = allCustomers.value.filter(c => 
    c.customer_name.toLowerCase().includes(q) || 
    c.name.toLowerCase().includes(q) ||
    (c.mobile_no && c.mobile_no.includes(q))
  ).slice(0, 100)
  custDDIdx.value = 0
}

function doCustSearch() {
  filterCustomers()
}

function openCustomerSearch() {
  showCustDD.value = false
  showCustomerSearchModal.value = true
  if (allCustomers.value.length === 0) fetchAllCustomers(); else filterCustomers();
  nextTick(() => custSearchInput.value?.focus())
}

function pickCust(c) {
  customer.value = c.name; 
  custSearch.value = c.customer_name; 
  showCustDD.value = false; 
  showCustomerSearchModal.value = false;
  // We can store extra info in a reactive ref if we want to show it on the main page
  selectedCustomerDetails.value = c;
  nextTick(() => newCodeInput.value?.focus())
}

function clearCustomerSelection() {
  customer.value = ''; custSearch.value = ''; custResults.value = []; showCustDD.value = false; selectedCustomerDetails.value = null
  nextTick(() => customerInput.value?.focus())
}

// ==================== NEW/EDIT CUSTOMER SUBWINDOW ====================
const showNewCustForm = ref(false)
const showEditCustForm = ref(false)
const newCustSaving = ref(false)
const newCustNameInput = ref(null)
const editCustNameInput = ref(null)
const newCustData = ref({ 
  customer_name: '', mobile: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', address_line3: '', 
  city: '', pincode: '', state: '' 
})
const editCustData = ref({ 
  customer_name: '', mobile: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', address_line3: '', 
  city: '', pincode: '', state: '' 
})

function openNewCustForm() {
  newCustData.value = { 
    customer_name: custSearch.value.trim(), mobile: '', email: '', gstin: '', 
    address_line1: '', address_line2: '', address_line3: '', 
    city: '', pincode: '', state: '' 
  }
  showCustDD.value = false
  showCustomerSearchModal.value = false
  showNewCustForm.value = true
  nextTick(() => newCustNameInput.value?.focus())
}

function openEditCustForm(c = null) {
  const target = c || selectedCustomerDetails.value
  if (!target || !target.name) return

  editCustData.value = { 
    customer_name: target.customer_name || '', 
    mobile: target.mobile_no || '', 
    email: target.email_id || '', 
    gstin: target.gstin || '', 
    address_line1: target.address_line1 || '', 
    address_line2: target.address_line2 || '', 
    address_line3: target.address_line3 || '', 
    city: target.city || '', 
    pincode: target.pincode || '', 
    state: target.state || '' 
  }
  showCustomerSearchModal.value = false
  showEditCustForm.value = true
  nextTick(() => editCustNameInput.value?.focus())
}

async function saveEditCust() {
  if (!editCustData.value.customer_name.trim()) { alert('Customer name is required'); return }
  newCustSaving.value = true
  try {
    const customerId = selectedCustomerDetails.value?.name
    const res = await apiPost('update_customer_details', { 
      customer: customerId, 
      data: JSON.stringify(editCustData.value) 
    })
    
    // Update local state
    if (selectedCustomerDetails.value) {
      Object.assign(selectedCustomerDetails.value, editCustData.value)
      selectedCustomerDetails.value.customer_name = res.customer_name
      custSearch.value = res.customer_name
    }
    
    // Re-fetch all customers to update the cache
    fetchAllCustomers(true)
    
    showEditCustForm.value = false
    alert(`Customer ${res.customer_name} updated successfully!`)
  } catch (e) { 
    alert('Error: ' + (e?.message || 'Unknown')) 
  }
  newCustSaving.value = false
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
const billDocStatus = ref(0) // 0=Draft, 1=Submitted, 2=Cancelled
const savedInvoiceName = ref(null)   // null = new bill; string = existing/just-saved invoice name
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

async function loadItemInsight(code, itemName = '', uom = '') {
  if (!code) {
    selectedItemData.value = null
    return
  }
  try {
    await insightResource.submit({
      item_code: code,
      customer: customer.value || null,
      warehouse: defaultWarehouse.value || null
    })
    const d = insightResource.data?.message || insightResource.data
    if (d) {
      selectedItemData.value = {
        item_code: code,
        item_name: itemName || d.item_name || '',
        uom: uom || d.uom || '',
        stock: d.stock || [],
        previousPurchases: d.previous_purchases || [],
        priceLists: (d.price_lists || []).map(pl => ({ name: pl.name, rate: pl.rate })),
      }
    }
  } catch (e) {
    selectedItemData.value = null
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
function focusNewQty() {
  if (newItemCode.value.trim() && newPending.value.item_name) {
    loadItemInsight(newItemCode.value.trim(), newPending.value.item_name, newPending.value.uom)
  }
  nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() })
}

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
  if (r.stock_qty <= 0) { alert('Out of stock: ' + r.item_name); return }
  const ei = items.value.findIndex(i => i.item_code === code && !i.deleted)
  if (ei >= 0) { items.value[ei].qty += newQty.value; selectedRow.value = ei }
  else { items.value.push({ item_code: r.item_code, item_name: r.item_name, uom: r.uom, qty: newQty.value, rate: r.rate, discount: 0, tax_rate: r.tax_rate ?? defaultTaxRate.value, warehouse: r.warehouse, deleted: false }); selectedRow.value = items.value.length - 1 }
  newItemCode.value = ''; newQty.value = 1; newPending.value = { item_name: '', uom: '', rate: null }; focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== ITEM SEARCH POPUP ====================
const showSearch = ref(false); const searchQuery = ref(''); const searchIdx = ref(0); let searchTargetRow = null; 
const allItems = ref([]); const searchResults = ref([]); const isSyncing = ref(false)

async function refreshLocalItems() {
  if (isSyncing.value) return
  isSyncing.value = true
  try {
    await fetchAllItems(true)
  } catch (e) {
    console.error('Manual sync failed:', e)
    alert('Failed to refresh items from server')
  } finally {
    isSyncing.value = false
  }
}

async function fetchAllItems(force = false) {
  try {
    // 1. Try loading items from local IndexedDB first
    let itemsFromDb = force ? [] : await localDb.getAllItems()
    
    // 2. If empty, sync from server
    if (!itemsFromDb || itemsFromDb.length === 0) {
      itemsFromDb = await frappeGet('frappe.client.get_list', {
        doctype: 'Item',
        fields: ['item_code', 'item_name', 'stock_uom as uom', 'standard_rate as rate'],
        filters: { disabled: 0, is_sales_item: 1 },
        limit_page_length: 5000,
        order_by: 'item_name asc'
      })
      if (itemsFromDb && itemsFromDb.length) {
        await localDb.clearStore('items')
        await localDb.saveItems(itemsFromDb)
      }
    }

    // 3. Always fetch real-time stock from Bin (not stored in local DB as it changes)
    const binsRes = await frappeGet('frappe.client.get_list', {
      doctype: 'Bin',
      fields: ['item_code', 'actual_qty as stock_qty'],
      limit_page_length: 10000
    })
    
    const stockMap = {}
    binsRes.forEach(b => {
      stockMap[b.item_code] = (stockMap[b.item_code] || 0) + b.stock_qty
    })

    allItems.value = (itemsFromDb || []).map(i => ({
      ...i,
      stock_qty: stockMap[i.item_code] || 0
    }))
    filterItems()
  } catch (e) {
    console.error('Failed to fetch items:', e)
  }
}

function filterItems() {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) {
    searchResults.value = allItems.value.slice(0, 100)
    return
  }
  searchResults.value = allItems.value.filter(i => 
    i.item_code.toLowerCase().includes(q) || 
    i.item_name.toLowerCase().includes(q)
  ).slice(0, 100)
  searchIdx.value = 0
}

watch(searchQuery, filterItems)

function openSearch(prefill, rowIdx) { 
  searchTargetRow = rowIdx; 
  searchQuery.value = prefill || ''; 
  searchIdx.value = 0; 
  showSearch.value = true; 
  if (allItems.value.length === 0) fetchAllItems(); else filterItems();
  nextTick(() => searchInput.value?.focus()) 
}
function closeSearch() { showSearch.value = false; searchQuery.value = ''; if (searchTargetRow !== null && searchTargetRow >= 0) focusField('code', searchTargetRow); else focusNewCode() }
function pickSearchItem() { if (searchResults.value.length) pickSearchItemByIdx(searchIdx.value) }

async function pickSearchItemByIdx(idx) {
  const p = searchResults.value[idx]; if (!p) return
  
  // Fetch real-time rate for the selected price list before picking
  let finalRate = p.rate || 0
  try {
    const r = await lookupItem(p.item_code)
    if (r) finalRate = r.rate
  } catch (e) {}

  if (searchTargetRow !== null && searchTargetRow >= 0) {
    const row = items.value[searchTargetRow]; row.item_code = p.item_code; row.item_name = p.item_name; row.uom = p.uom; row.rate = finalRate; row.tax_rate = p.tax_rate ?? defaultTaxRate.value; row.warehouse = p.warehouse || defaultWarehouse.value; row.deleted = false
    showSearch.value = false; selectedRow.value = searchTargetRow; focusField('qty', searchTargetRow)
  } else {
    newItemCode.value = p.item_code; newPending.value = { item_name: p.item_name, uom: p.uom, rate: finalRate }
    showSearch.value = false; nextTick(() => focusNewQty())
  }
}

// ==================== MODIFY BILL ====================
const showModifyBill = ref(false)
const modifyQuery = ref('')
const modifyDate = ref(new Date().toISOString().split('T')[0])
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

function changeBillDate(days) {
  if (billDocStatus.value !== 0) return
  const d = new Date(billDate.value)
  d.setDate(d.getDate() + days)
  billDate.value = d.toISOString().split('T')[0]
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
    modifyResults.value = await frappeGet('ssplbilling.api.sales_api.get_sales_invoices', {
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
    const inv = await frappeGet('ssplbilling.api.sales_api.get_sales_invoice', { invoice_name: invoiceName })
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
    billDocStatus.value = inv.docstatus
    // If it's already submitted or cancelled, treat as saved/read-only
    billSaved.value = inv.docstatus !== 0
    showModifyBill.value = false

    // Set selectedCustomerDetails for display
    selectedCustomerDetails.value = allCustomers.value.find(c => c.name === inv.customer) || {
      name: inv.customer,
      customer_name: inv.customer_name,
      balance: 0,
      address_line1: ""
    }

    nextTick(() => customerInput.value?.focus())
  } catch (e) {
    alert('Error loading invoice: ' + (e.message || 'Unknown error'))
  }
}

/** Click Edit after save → re-enable the form for updates */
function enterEditMode() {
  if (billDocStatus.value !== 0) {
    alert('Cannot edit a submitted/cancelled invoice.')
    return
  }
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

    // Fetch allowed series for this user
    let allowedList = []
    let userAllowedString = ''
    try {
      const d = await frappeGet('ssplbilling.api.sales_api.get_allowed_series')
      allowedList = d.allowed_series || []
      userAllowedString = d.user_allowed_string || ''
    } catch (e) {
      console.warn('[SalesEntry] get_allowed_series failed:', e)
    }

    if (rows.length) {
      billingSeriesConfig.value = rows
      // Filter available series strictly based on user allowed series
      const allSeries = rows.map(r => r.series)
      if (allowedList.length === 0 && !userAllowedString) {
        // Unrestricted user: show all series from billing settings
        availableSeries.value = allSeries
      } else {
        // Restricted user: show only allowed series
        availableSeries.value = allSeries.filter(s => allowedList.includes(s))
      }

      if (settings.default_warehouse) defaultWarehouse.value = settings.default_warehouse
      try {
        const raw = settings.cipher_map
        if (raw) {
          const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
          if (Array.isArray(parsed) && parsed.length === 10) cipherMap.value = parsed
        }
      } catch (e) { /* non-fatal */ }

      if (availableSeries.value.length === 0) {
        alert('You do not have permission to use any naming series.')
        return
      }

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
    const list = await frappeGet('ssplbilling.api.sales_api.get_naming_series')
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
    const res = await frappeGet('ssplbilling.api.sales_api.get_next_bill_no', { naming_series: billSeries.value })
    nextBillNo.value = res || '...'
  } catch (e) { nextBillNo.value = '...' }
}

const isExempted = computed(() => taxTemplate.value.toLowerCase().includes('exempt'))
const isInclusive = computed(() => taxTemplate.value.toLowerCase().includes('inclusive'))

// Gross = sum of (qty * rate * (1 - item discount%)) — after item-level discount
const grossTotal = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate * (1 - (i.discount || 0) / 100), 0)
)

const totalBeforeItemDiscount = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate, 0)
)

const itemDiscountTotal = computed(() =>
  activeItems.value.reduce((s, i) => s + i.qty * i.rate * ((i.discount || 0) / 100), 0)
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
    billDocStatus.value = 0 // Still Draft after save/update
    fetchNextBillNo()
    alert(`Invoice ${result?.invoice_name || ''} saved!\nTotal: ₹${(result?.grand_total || grandTotal.value).toFixed(2)}\n\nPress Esc to start a new bill`)
  } catch (e) {
    alert('Error: ' + (e?.message || 'Failed to save invoice'))
  }
}

function startNewBill() {
  items.value = []; selectedRow.value = -1; customer.value = ''; custSearch.value = ''
  discountPct.value = 0; newItemCode.value = ''; newQty.value = 1; paymentMode.value = 'Cash'
  billSaved.value = false; billDocStatus.value = 0; savedInvoiceName.value = null; selectedItemData.value = null
  selectedCustomerDetails.value = null
  escWarning.value = false; clearTimeout(escWarnTimer)
  nextTick(() => seriesSelect.value?.focus())
}

function printBill() { alert('Print preview coming soon') }
function cancelBill() { startNewBill() }

// ==================== GLOBAL KEYS ====================
function handleKeydown(e) {
  if (showNewCustForm.value && e.key === 'End') {
    e.preventDefault()
    saveNewCust()
    return
  }
  if (showEditCustForm.value && e.key === 'End') {
    e.preventDefault()
    saveEditCust()
    return
  }
  if (showCustomerSearchModal.value) {
    if (e.key === 'F5') {
      e.preventDefault()
      fetchAllCustomers(true)
      return
    }
    if (e.key === 'F2') {
      e.preventDefault()
      openNewCustForm()
      return
    }
    if (e.key === 'F3') {
      e.preventDefault()
      const c = custResults.value[custDDIdx.value]
      if (c) openEditCustForm(c)
      return
    }
  }
  if (showSearch.value) {
    if (e.key === 'F5') {
      e.preventDefault()
      refreshLocalItems()
      return
    }
  }
  if (!showCustomerSearchModal.value && !showNewCustForm.value && !showEditCustForm.value && e.key === 'F3' && selectedCustomerDetails.value) {
    e.preventDefault()
    openEditCustForm()
    return
  }
  if (showSearch.value || showCustDD.value || showNewCustForm.value || showEditCustForm.value || showModifyBill.value || showCustomerSearchModal.value) {
    if (e.key === 'Escape') {
      showSearch.value = false; showCustDD.value = false; showNewCustForm.value = false; showEditCustForm.value = false; showModifyBill.value = false; showCustomerSearchModal.value = false
    }
    return
  }
  if (e.key === 'F2') {
    e.preventDefault()
    openCustomerSearch()
    return
  }
  if (e.key === 'PageUp') {
    e.preventDefault()
    seriesSelect.value?.focus()
    return
  }
  if (e.key === 'F4') {
    e.preventDefault()
    openSearch('', null)
    return
  }
  if (e.key === 'End') {
    e.preventDefault()
    if (document.activeElement === discountInput.value) {
      saveButton.value?.focus()
    } else {
      discountInput.value?.focus()
      discountInput.value?.select()
    }
    return
  }
  if (e.ctrlKey && e.key === 's') { e.preventDefault(); saveBill() }
  if (e.key === 'Delete' && selectedRow.value >= 0) { const el = document.activeElement; if (!el || el.tagName !== 'INPUT') { e.preventDefault(); softDelete(selectedRow.value) } }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  fetchSeriesList()
  fetchDropdownOptions()
  fetchAllItems()
  fetchAllCustomers()
  if (route.query.invoice) {
    loadInvoice(route.query.invoice)
  } else {
    nextTick(() => seriesSelect.value?.focus())
  }
})
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>
