<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'h-screen bg-slate-900'" class="flex">
    <aside class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Modify Quotations</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-slate-700 p-1.5 bg-slate-900">
          <button @click="changeSidebarDate(-1)" class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300">&larr;</button>
          <input 
            type="date" 
            v-model="sidebarDate"
            class="w-full bg-transparent text-xs font-bold text-slate-300 outline-none"
          />
          <button @click="changeSidebarDate(1)" class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300">&rarr;</button>
        </div>

        <!-- Search & Series Filters -->
        <div class="flex flex-col gap-1.5 border-b border-slate-700 p-2 bg-slate-800/20">
          <input 
            type="text" 
            v-model="sidebarSearch"
            placeholder="Search quotation/cust..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 outline-none focus:border-blue-500"
          />
          <select
            ref="sidebarSeriesSelect"
            v-model="sidebarSeries"
            class="w-full rounded border border-slate-700 bg-slate-900 px-1.5 py-1 text-[11px] text-slate-300 outline-none focus:border-blue-500"
            @keydown.enter.prevent="focusFirstSidebarQuotation"
          >
            <option value="">All Series</option>
            <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
          </select>
          <button
            @click="draftOnly = !draftOnly"
            class="w-full rounded border py-1 text-[10px] font-bold uppercase transition-colors"
            :class="draftOnly ? 'bg-amber-900/40 border-amber-500 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Quotations' }}
          </button>
        </div>

        <!-- Quotation List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="sidebarLoading" class="p-4 text-center text-xs text-slate-500">Loading...</div>
          <div v-else-if="!sidebarQuotations.length" class="p-4 text-center text-xs text-slate-600 italic">No quotations found</div>
          <div 
            v-for="(inv, idx) in sidebarQuotations" 
            :key="inv.name"
            :ref="el => setSidebarQuotationRef(el, idx)"
            @click="loadQuotation(inv.name)"
            class="group cursor-pointer border-b border-slate-800 bg-slate-900 px-2 py-1 transition-colors hover:bg-slate-800 outline-none focus:bg-slate-800 focus:ring-1 focus:ring-blue-500"
            :class="{ 'bg-slate-800 border-l-2 border-l-blue-500': savedQuotationName === inv.name }"
            tabindex="0"
            @keydown.enter="loadQuotation(inv.name)"
            @keydown.up.prevent="navigateSidebarQuotation(idx, -1)"
            @keydown.down.prevent="navigateSidebarQuotation(idx, 1)"
          >
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-1.5 truncate min-w-0">
                <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-green-500' : 'bg-red-500'"></span>
                <span class="truncate font-mono text-[15px] font-bold text-blue-400">{{ inv.name }}</span>
              </div>
              <span class="shrink-0 font-mono text-[20px] font-bold text-slate-200 tabular-nums">₹{{ inv.grand_total.toFixed(0) }}</span>
            </div>
            <div class="truncate text-[11px] text-slate-400">{{ inv.customer_name }}</div>
          </div>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <div class="flex flex-1 flex-col overflow-hidden bg-slate-900">
        <!-- Nav bar: Dashboard link + title + zoom + shortcuts + user -->
        <div class="flex items-center justify-between border-b border-slate-700/60 bg-slate-800/60 px-4 py-1">
          <div class="flex items-center gap-3">
            <button class="rounded px-2 py-0.5 text-xs text-slate-400 hover:bg-slate-700" @click="handleBack">&larr; Dashboard</button>
            <span class="text-slate-600 text-xs">|</span>
            <span class="text-xs font-semibold text-slate-300">Quotation Entry</span>
          </div>
          <div class="flex items-center gap-3 text-[10px] text-slate-400">
            <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden">
              <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-5 w-6 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
              <div class="flex items-center border-x border-slate-700 bg-slate-900 px-2 gap-1">
                <span class="text-[9px] font-bold uppercase text-slate-500">Zoom</span>
                <span class="text-[10px] font-bold text-slate-300">{{ zoomPercent }}%</span>
              </div>
              <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-5 w-6 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
            </div>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Up/Down</kbd> Nav</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Tab</kbd> Col</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F4</kbd> Series</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Ctrl+S</kbd> Save</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F2</kbd> New Quotation</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F5</kbd> Print</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Esc</kbd> Back</span>
            <div class="h-3 w-px bg-slate-700"></div>
            <div class="flex items-center gap-1 font-bold text-blue-400">
              <span class="text-[9px] text-slate-500 font-medium">HI</span>
              <span class="truncate max-w-[100px] uppercase tracking-wide text-[10px]">{{ (session.fullName.value || 'User').split('@')[0] }}</span>
            </div>
          </div>
        </div>
        <!-- Series / Customer / Date bar -->
        <div class="border-b border-slate-700 bg-slate-800 px-4 py-2">
      <div class="flex items-center gap-6">
        <!-- Quotation No -->
        <div class="flex items-center gap-2 border-l border-slate-700 pl-6">
          <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Quotation No</label>
          <div class="text-xl font-bold text-slate-100 tabular-nums" style="font-family: 'Poppins', sans-serif">
            {{ nextQuotationNo }}
          </div>
        </div>

        <!-- Customer Section (Flex-1 to take middle space) -->
        <div class="flex-1 flex items-center gap-4 border-l border-slate-700 pl-6 overflow-hidden">
          <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Customer</label>
          
          <!-- Name & Address -->
          <div class="flex items-baseline gap-4 min-w-0">
            <div 
              ref="customerInput"
              class="shrink-0 max-w-[300px] truncate text-xl font-bold transition-colors cursor-pointer outline-none hover:text-blue-400 focus:text-blue-400 leading-none"
              :class="customer ? 'text-slate-100' : 'text-slate-600 italic'"
              style="font-family: 'Poppins', sans-serif"
              @click="openCustomerSearch"
              tabindex="0"
              @keydown.enter.prevent="openCustomerSearch"
              @keydown.space.prevent="openCustomerSearch"
            >
              {{ custSearch || 'Not Selected' }}
            </div>

            <div v-if="selectedCustomerDetails" class="flex items-center gap-3 min-w-0">
              <span v-if="selectedCustomerDetails.address_line1" class="truncate max-w-[350px] text-xl text-slate-400 font-normal leading-none" :title="selectedCustomerDetails.address_line1">
                {{ selectedCustomerDetails.address_line1 }}{{ selectedCustomerDetails.city ? ', ' + selectedCustomerDetails.city : '' }}
              </span>
              <span v-if="selectedCustomerDetails.mobile_no" class="whitespace-nowrap text-[10px] text-slate-500 font-bold leading-none">
                PH: {{ selectedCustomerDetails.mobile_no }}
              </span>
            </div>
          </div>

          <!-- Stats Group -->
          <div v-if="selectedCustomerDetails" class="flex items-center gap-6 ml-auto mr-6">
            <!-- Last Quotation Date -->
            <div v-if="selectedCustomerDetails.last_invoice_date" class="flex flex-col items-end leading-none">
              <span class="text-[8px] uppercase tracking-wider text-slate-500 font-bold mb-0.5">Last Quote</span>
              <span class="text-sm text-slate-300 font-medium">
                {{ new Date(selectedCustomerDetails.last_invoice_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) }}
              </span>
            </div>

            <!-- Ledger Balance -->
            <div class="flex flex-col items-end leading-none border-l border-slate-700 pl-6">
              <span class="text-[8px] uppercase tracking-wider text-slate-500 font-bold mb-0.5">Ledger Bal</span>
              <span :class="selectedCustomerDetails.balance > 0 ? 'text-green-400' : 'text-red-400'" class="text-xl font-bold tabular-nums">
                &#8377;{{ Math.abs(selectedCustomerDetails.balance || 0).toFixed(2) }} <span class="text-[10px] font-bold">{{ selectedCustomerDetails.balance > 0 ? 'DR' : 'CR' }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Quotation Date -->
        <div class="flex items-center gap-3 border-l border-slate-700 pl-6 whitespace-nowrap">
          <label class="text-[10px] font-bold uppercase text-slate-500">Quotation Date</label>
          <input
            ref="dateInput"
            v-model="quotationDate"
            type="date"
            :disabled="quotationDocStatus !== 0 || quotationSaved"
            class="rounded border border-slate-600 bg-slate-900 px-2 py-0.5 text-xl font-bold text-slate-100 outline-none focus:border-blue-500 disabled:bg-slate-800 disabled:text-slate-500 tabular-nums"
            style="font-family: 'Poppins', sans-serif"
          />
          <label class="flex items-center gap-1.5 cursor-pointer select-none ml-2">
            <input type="checkbox" v-model="ignoreDiscountRule" :disabled="quotationDocStatus !== 0 || quotationSaved" class="h-3 w-3 rounded border-slate-600 accent-amber-500 cursor-pointer disabled:cursor-not-allowed" />
            <span class="text-slate-500 text-[10px]">Ignore Discount Rule</span>
          </label>
        </div>
      </div>
    </div>

        <div class="flex flex-[7] flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto">
            <table class="w-full text-sm border-collapse border-l border-t border-slate-700">
              <thead>
                <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
                  <th class="w-8 border-r border-b border-slate-700 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-400">#</th>
                  <th class="w-32 border-r border-b border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-300">Barcode</th>
                  <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-300">Item Name</th>
                  <th class="w-16 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Qty</th>
                  <th class="w-14 border-r border-b border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-300">UOM</th>
                  <th class="w-24 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Rate</th>
                  <th class="w-16 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Disc %</th>
                  <th class="w-24 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-amber-500">Disc Rate</th>
                  <th class="w-16 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Tax %</th>
                  <th class="w-24 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Amount</th>
                  <th class="w-8 border-b border-slate-700"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="cursor-pointer border-b border-slate-700 outline-none transition-colors" :class="{ 'bg-blue-900/30 border-l-2 border-l-blue-500': selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing, 'bg-green-900/30 border-l-2 border-l-green-400': item._is_free && !item.deleted, 'bg-green-900/20 border-l-2 border-l-green-600': !item._is_free && item._rule_discount != null && !item.deleted, 'bg-purple-900/20 border-l-2 border-l-purple-500': !item._is_free && item._rule_discount == null && item._customer_pricing && !item.deleted, 'bg-red-900/10': item.deleted, 'hover:bg-slate-800/50': !item.deleted && !item._is_free && item._rule_discount == null && !item._customer_pricing && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full font-bold" :class="item.deleted ? 'bg-red-900/30 text-red-400' : 'bg-slate-800 text-slate-400'" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">{{ idx + 1 }}</span></td>
                  <td class="p-0 border-r border-slate-700">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="quotationDocStatus !== 0 || quotationSaved || item._is_free" class="w-full rounded border border-slate-600 bg-slate-800 font-mono text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-900" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span :class="item.deleted ? 'text-red-900/50 line-through' : 'text-slate-200'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</span><span v-if="item._is_free" class="ml-1 rounded bg-green-900/60 px-1 py-0.5 font-bold text-green-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">FREE</span><span v-else-if="item.deleted" class="ml-1 font-semibold text-red-500" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">DELETED</span></td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="quotationDocStatus !== 0 || quotationSaved || item._is_free" min="1" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.qty }}</span>
                  </td>
                  <td class="px-2 text-slate-400 border-r border-slate-700" :class="item.deleted ? 'text-slate-600' : ''" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="quotationDocStatus !== 0 || quotationSaved || item._is_free" step="0.01" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @focus="onRateFocus(idx)" @blur="onRateBlur(idx)" @keydown.enter.prevent="focusField('discount', idx)" @keydown.tab.prevent="focusField('discount', idx)" @keydown.shift.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.rate.toFixed(2) }}</span>
                  </td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'discount', idx)" type="number" v-model.number="item.discount" :disabled="quotationDocStatus !== 0 || quotationSaved || item._is_free" step="0.5" min="0" max="100" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @focus="onDiscountFocus(idx)" @blur="onDiscountBlur(idx)" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.shift.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.discount || 0 }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-slate-600' : (item.discount ? 'text-amber-400' : 'text-slate-600')" :style="{ fontSize: dynamicRowStyle.fontSize }">
                      {{ item.discount ? (item.rate * (1 - (item.discount) / 100)).toFixed(2) : '—' }}
                    </span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ isExempted ? 0 : (item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700 font-mono font-semibold" :class="item.deleted ? 'text-slate-600 line-through' : 'text-slate-200'" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.deleted ? '' : (item.qty * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2) }}</td>
                  <td class="px-2 text-center" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button v-if="!item.deleted && !item._is_free" class="rounded px-1 py-0.5 text-slate-600 hover:bg-red-900/30 hover:text-red-400" :style="{ fontSize: dynamicRowStyle.fontSize }" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else-if="item.deleted" class="rounded px-1 py-0.5 font-semibold text-blue-500 hover:bg-blue-900/30 hover:text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }" @click.stop="restoreItem(idx)">&larr;</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="quotationDocStatus === 0 && !quotationSaved" class="border-b border-slate-700" :class="selectedRow === -1 ? 'bg-blue-900/20' : 'bg-slate-800/30'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-900/50 font-bold text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">+</span></td>
                  <td class="p-0 border-r border-slate-700"><input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-slate-600 bg-slate-800 py-1 text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-900/50" style="padding-left:0;padding-right:0;" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Barcode" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" /></td>
                  <td class="px-2 text-slate-400 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.item_name || '--' }}</td>
                  <td class="px-0 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><input ref="newQtyInput" v-model.number="newQty" type="number" min="1" class="w-full rounded border border-slate-600 bg-slate-800 text-right font-mono text-slate-200 outline-none focus:border-blue-500 appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="addNewItem" @keydown.shift.tab.prevent="focusNewCode" /></td>
                  <td class="px-2 text-slate-400 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.uom || '--' }}</td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="newPending.rate" class="font-mono text-slate-300">{{ newPending.rate.toFixed(2) }}</span>
                    <span v-else class="text-slate-600">--</span>
                  </td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">0</td>
                  <td class="px-2 text-right font-mono text-slate-600 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">—</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ isExempted ? 0 : defaultTaxRate }}</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.rate ? (newQty * newPending.rate).toFixed(2) : '--' }}</td>
                  <td class="border-slate-700"></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- BOTTOM PANEL (Insight + Settings + Calculation) -->
        <div class="flex flex-[4] border-t border-slate-700 bg-slate-900 overflow-hidden">
          <!-- Stock Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:260px;max-width:320px;scrollbar-width:none">
            <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Warehouse Stock<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
            <table v-if="selectedItemData && selectedItemData.stock && selectedItemData.stock.length" class="w-full border-collapse text-[10px]" style="table-layout:fixed">
              <colgroup>
                <col style="width:70%"><col style="width:30%">
              </colgroup>
              <thead>
                <tr class="bg-slate-800">
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Warehouse</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Actual</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in selectedItemData.stock" :key="s.warehouse" class="hover:bg-slate-800/40">
                  <td class="px-1 py-0.5 text-slate-400 border border-slate-700 overflow-hidden text-ellipsis whitespace-nowrap" :title="s.warehouse">{{ s.warehouse }}</td>
                  <td class="px-1 py-0.5 text-right font-mono font-bold border border-slate-700" :class="s.actual_qty > 20 ? 'text-green-400' : s.actual_qty > 0 ? 'text-amber-400' : 'text-red-400'">{{ s.actual_qty }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No stock data' : 'Select a row to see stock' }}</div>
          </div>

          <!-- Price List Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:170px;max-width:200px;scrollbar-width:none">
            <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Price Lists<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
            <table v-if="selectedItemData && selectedItemData.priceLists && selectedItemData.priceLists.length" class="w-full border-collapse text-[10px]">
              <thead>
                <tr class="bg-slate-800">
                  <th class="px-1 py-0.5 text-center font-semibold text-slate-500 border border-slate-700">T</th>
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">List</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Rate</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pl in selectedItemData.priceLists" :key="pl.name + pl.type" class="hover:bg-slate-800/40">
                  <td class="px-1 py-0.5 text-center border border-slate-700">
                    <span class="rounded px-1 py-0.5 text-[9px] font-bold uppercase" :class="pl.type === 'buying' ? 'bg-blue-900/40 text-blue-400' : 'bg-slate-700 text-slate-400'">{{ pl.type === 'buying' ? 'B' : 'S' }}</span>
                  </td>
                  <td class="px-1 py-0.5 text-slate-400 border border-slate-700 truncate max-w-[90px]" :title="pl.name">{{ pl.name }}</td>
                  <td class="px-1 py-0.5 text-right font-mono font-bold text-amber-400 border border-slate-700 text-base">&#8377;{{ encPrice(pl.rate || 0) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No price lists' : 'Select a row to see prices' }}</div>
          </div>

          <!-- Previous Quotations Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:200px;max-width:240px;scrollbar-width:none">
            <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Previous Quotations<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
            <table v-if="selectedItemData && selectedItemData.previousPurchases && selectedItemData.previousPurchases.length" class="w-full border-collapse text-[10px]">
              <thead>
                <tr class="bg-slate-800">
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Quote</th>
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Date</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Rate</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Qty</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Disc%</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in selectedItemData.previousPurchases" :key="p.name" class="border-b border-slate-800 hover:bg-slate-800/40">
                  <td class="px-1 py-0.5 font-medium text-blue-400 border border-slate-700 truncate max-w-[70px]" :title="p.name">{{ p.name }}</td>
                  <td class="px-1 py-0.5 text-slate-500 border border-slate-700 whitespace-nowrap">{{ p.date }}</td>
                  <td class="px-1 py-0.5 text-right font-mono font-bold text-slate-300 border border-slate-700">&#8377;{{ p.rate.toFixed(2) }}</td>
                  <td class="px-1 py-0.5 text-right font-mono text-slate-400 border border-slate-700">{{ p.qty }}</td>
                  <td class="px-1 py-0.5 text-right font-bold border border-slate-700" :class="p.discount > 0 ? 'text-red-400' : 'text-slate-600'">{{ p.discount > 0 ? p.discount + '%' : '—' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No previous quotes' : 'Select a row to see history' }}</div>
          </div>

          <!-- Settings Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:210px;max-width:240px;scrollbar-width:none">
<div class="flex flex-col gap-2 p-2">
              <div class="flex gap-1">
                <button @click="exportItems" class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-[10px] font-bold uppercase text-slate-400 hover:text-blue-400 hover:border-blue-600 transition-colors">Export</button>
                <button @click="openImportModal" class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-[10px] font-bold uppercase text-slate-400 hover:text-blue-400 hover:border-blue-600 transition-colors">Import</button>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Warehouse</label>
                <select v-model="defaultWarehouse" disabled class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-400 outline-none cursor-not-allowed">
                  <option :value="defaultWarehouse">{{ defaultWarehouse || 'None' }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Price List</label>
                <select v-model="priceList" :disabled="quotationDocStatus !== 0 || quotationSaved" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
                  <option v-for="pl in availablePriceLists" :key="pl" :value="pl">{{ pl }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Tax</label>
                <select v-model="taxTemplate" :disabled="quotationDocStatus !== 0 || quotationSaved" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
                  <option value="">-- None --</option>
                  <option v-for="t in availableTaxTemplates" :key="t" :value="t">{{ t }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Cost Center</label>
                <select v-model="costCenter" disabled class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-400 outline-none cursor-not-allowed">
                  <option :value="costCenter">{{ costCenter || 'None' }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Print Format</label>
                <select v-model="printScheme" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-200 outline-none focus:border-blue-500">
                  <option value="">-- Default --</option>
                  <option v-for="pf in availablePrintSchemes" :key="pf" :value="pf">{{ pf }}</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Right Column: Quotation Summary as full table -->
          <table class="flex-1 bg-slate-800/50 border-collapse text-xs border border-slate-700 h-full" style="table-layout:fixed">
            <colgroup>
              <col style="width:21%"><col style="width:18%"><col style="width:20%"><col style="width:41%">
            </colgroup>
            <thead>
              <tr class="bg-slate-800">
                <th class="px-2 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-500 border border-slate-700">Description</th>
                <th class="px-2 text-center text-[10px] font-semibold uppercase tracking-wider text-slate-500 border border-slate-700">Entry</th>
                <th class="px-2 text-right text-[10px] font-semibold uppercase tracking-wider text-slate-500 border border-slate-700">Amount</th>
                <th class="px-2 text-center text-[10px] font-semibold uppercase tracking-wider text-slate-500 border border-slate-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Item Discount</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-&#8377;{{ itemDiscountTotal.toFixed(2) }}</td>
                <td class="border border-slate-700 px-2" rowspan="10">
                  <div class="flex flex-col gap-2 h-full py-2">
                    <div class="text-[10px] text-slate-500">{{ activeItems.length }} item{{ activeItems.length !== 1 ? 's' : '' }}{{ deletedCount > 0 ? ' (' + deletedCount + ' deleted)' : '' }}</div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Quotation</div>
                    <div class="font-mono text-4xl font-bold text-blue-500 leading-none">&#8377;{{ grandTotal.toFixed(2) }}</div>
                    <div v-if="quotationSaved" class="flex items-center justify-between rounded bg-green-900/30 px-2 py-1 text-xs text-green-400">
                      <span class="font-bold">{{ savedQuotationName }}</span>
                      <span class="font-semibold uppercase text-[10px]">Saved</span>
                    </div>
                    <button v-if="quotationSaved && quotationDocStatus === 0" @click="enterEditMode" class="w-full rounded border border-amber-600/50 bg-amber-900/20 py-1.5 text-center text-xs font-semibold text-amber-400 transition hover:bg-amber-900/30">✏ Modify Quotation</button>
                    <button v-else-if="!quotationSaved" ref="saveButton" @click="saveQuotation" class="w-full rounded py-1.5 text-center text-xs font-semibold text-white transition shadow" :class="savedQuotationName ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'">{{ savedQuotationName ? 'Update Quotation' : 'Save Quotation (Ctrl+S)' }}</button>
                    <div class="flex gap-1">
                      <button class="flex-1 rounded border border-slate-600 bg-slate-800 py-1.5 text-center text-xs font-semibold text-slate-300 hover:bg-slate-700" @click="printQuotation">Print</button>
                      <button class="flex-1 rounded border border-red-900/50 bg-red-900/10 py-1.5 text-center text-xs font-semibold text-red-400 hover:bg-red-900/20" @click="cancelQuotation">{{ quotationSaved ? 'New Quotation' : 'Cancel' }}</button>
                    </div>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Discount</td>
                <td class="p-0 border-y border-slate-700">
                  <div class="flex h-full">
                    <div class="flex flex-1 items-center border-r border-slate-700">
                      <input ref="discountInput" type="number" v-model.number="discountPct"
                        :disabled="quotationDocStatus !== 0 || quotationSaved || discountInputMode === 'amt'"
                        min="0" max="100" step="0.5" style="width:100%;height:100%;padding:0 2px"
                        class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="e => { discountInputMode = parseFloat(e.target.value) > 0 ? 'pct' : null; discountDirectAmt = 0 }"
                        @keydown.enter="discountAmtInput?.focus(); discountAmtInput?.select()"
                        @keydown.tab.prevent="discountAmtInput?.focus(); discountAmtInput?.select()" />
                      <span class="shrink-0 px-1 text-slate-500 text-xs">%</span>
                    </div>
                    <div class="flex flex-1 items-center">
                      <span class="shrink-0 px-1 text-slate-500 text-xs">&#8377;</span>
                      <input ref="discountAmtInput" type="number" v-model.number="discountDirectAmt"
                        :disabled="quotationDocStatus !== 0 || quotationSaved || discountInputMode === 'pct'"
                        min="0" step="1" style="width:100%;height:100%;padding:0 2px"
                        class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="e => { discountInputMode = parseFloat(e.target.value) > 0 ? 'amt' : null; discountPct = 0 }"
                        @keydown.enter="freightInput?.focus(); freightInput?.select()"
                        @keydown.tab.prevent="freightInput?.focus(); freightInput?.select()" />
                    </div>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-&#8377;{{ discountAmt.toFixed(2) }}</td>
              </tr>
              <tr class="bg-slate-800/40">
                <td class="px-2 text-lg font-semibold text-slate-200/80 border border-slate-600">Subtotal</td>
                <td class="px-2 border border-slate-600"></td>
                <td class="px-2 text-right font-mono font-semibold text-slate-100 text-2xl border border-slate-600">&#8377;{{ subtotal.toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Freight</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="freightInput" type="number" v-model.number="freightAmt"
                    :disabled="quotationDocStatus !== 0 || quotationSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.packingInput?.focus(); $refs.packingInput?.select()"
                    @keydown.tab.prevent="$refs.packingInput?.focus(); $refs.packingInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+&#8377;{{ (freightAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Packing</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="packingInput" type="number" v-model.number="packingAmt"
                    :disabled="quotationDocStatus !== 0 || quotationSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.loadingInput?.focus(); $refs.loadingInput?.select()"
                    @keydown.tab.prevent="$refs.loadingInput?.focus(); $refs.loadingInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+&#8377;{{ (packingAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Loading</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="loadingInput" type="number" v-model.number="loadingAmt"
                    :disabled="quotationDocStatus !== 0 || quotationSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.otherChargesInput?.focus(); $refs.otherChargesInput?.select()"
                    @keydown.tab.prevent="$refs.otherChargesInput?.focus(); $refs.otherChargesInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+&#8377;{{ (loadingAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Other</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="otherChargesInput" type="number" v-model.number="otherChargesAmt"
                    :disabled="quotationDocStatus !== 0 || quotationSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-slate-200 outline-none focus:bg-slate-700/40 disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="saveButton?.focus()"
                    @keydown.tab.prevent="saveButton?.focus()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+&#8377;{{ (otherChargesAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Tax</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-300 text-2xl border border-slate-700">+&#8377;{{ totalTax.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SHORTCUT REFERENCE -->
    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Quotation Entry"
      :extra="[
        { key: 'F3', desc: 'Focus modify panel (sidebar)' },
        { key: 'F4', desc: 'Focus sidebar series' },
        { key: 'Page Up', desc: 'Focus series selector' },
      ]"
      @close="showShortcutPage = false"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      initial-type="Customer"
      :skip-date-filter="true"
      @close="closeCustomerSearchModal"
      @select="pickCust"
    />

    <!-- CUSTOMER LEDGER SUB-WINDOW -->
    <CustomerLedger
      v-if="showCustomerLedgerWindow"
      :is-sub-window="true"
      :ledger-name="ledgerCustomerName"
      :ledger-type="ledgerType"
      :initial-from-date="ledgerFromDate"
      :initial-to-date="ledgerToDate"
      @close="showCustomerLedgerWindow = false"
    />

    <!-- ITEM SEARCH MODAL -->
    <ItemSearch
      ref="itemSearchModalRef"
      :show="showItemSearchModal"
      search-type="Sales"
      :price-list="priceList"
      :warehouse="defaultWarehouse"
      :skip-date-filter="true"
      :initial-query="itemSearchInitialQuery"
      @close="closeItemSearch"
      @select="pickItem"
    />

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="savedQuotationName"
      :initial-print-format="printScheme"
      @close="showPrintModal = false; if (printModalAfterSave) startNewQuotation()"
    />

    <JumpToRowModal 
      v-model:show="showJumpModal"
      :max-rows="items.length" 
      @jump="handleJump" 
    />

    <BarcodePrintingModal
      :show="showBarcodeModal"
      @close="showBarcodeModal = false"
    />

    <!-- SERIES SUBWINDOW -->
    <div
      v-if="showSeriesDropdown"
      class="fixed inset-0 z-[120] flex items-center justify-center bg-black/70 backdrop-blur-sm"
      @click.self="showSeriesDropdown = false"
      @keydown.escape.capture="showSeriesDropdown = false"
    >
      <div class="w-[360px] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div class="border-b border-slate-700 bg-slate-800 px-5 py-3">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400">Select Series</div>
          <div class="mt-0.5 text-[10px] text-slate-600">↑ ↓ navigate · Enter select · 1–9 quick pick</div>
        </div>
        <div class="p-3 flex flex-col gap-2">
          <button
            v-for="(s, idx) in availableSeries"
            :key="s"
            class="flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-all focus:outline-none"
            :class="idx === seriesHighlightIdx
              ? 'border-blue-500 bg-blue-600/30 text-white ring-1 ring-blue-500'
              : s === quotationSeries
                ? 'border-blue-700 bg-blue-900/20 text-blue-300'
                : 'border-slate-700 bg-slate-800 text-slate-200'"
            @click="selectSeries(s)"
            @mouseenter="seriesHighlightIdx = idx"
          >
            <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-700 font-mono text-sm font-black text-slate-300">
              {{ idx + 1 }}
            </span>
            <span class="font-bold tracking-wide">{{ s }}</span>
            <span v-if="s === quotationSeries" class="ml-auto text-[10px] font-bold text-blue-400">ACTIVE</span>
          </button>
        </div>
        <div class="border-t border-slate-700 bg-slate-800/50 px-5 py-2 text-[10px] text-slate-600 text-center">
          Esc to close
        </div>
      </div>
    </div>

    <!-- IMPORT OPTIONS MODAL -->
    <div v-if="showImportModal" class="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="showImportModal = false">
      <div class="w-[400px] overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl">
        <div class="bg-blue-900/20 px-6 py-4 border-b border-blue-900/30">
          <div class="text-xl font-bold text-slate-100">Import Items</div>
        </div>
        <div class="p-6">
          <p class="text-sm text-slate-400 mb-4">Choose where to pull the Rate and Discount from:</p>
          <div class="flex flex-col gap-3">
            <label class="flex items-center gap-3 cursor-pointer group">
              <input type="radio" v-model="importOption" value="Master" class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 focus:ring-blue-500" />
              <div class="flex flex-col">
                <span class="text-slate-200 font-semibold group-hover:text-blue-400">Master (Price List)</span>
                <span class="text-[10px] text-slate-500">Pull current rates and discounts from ERPNext Price List</span>
              </div>
            </label>
            <label class="flex items-center gap-3 cursor-pointer group">
              <input type="radio" v-model="importOption" value="File" class="w-4 h-4 text-blue-600 bg-slate-800 border-slate-600 focus:ring-blue-500" />
              <div class="flex flex-col">
                <span class="text-slate-200 font-semibold group-hover:text-blue-400">Import File</span>
                <span class="text-[10px] text-slate-500">Keep rates and discounts exactly as specified in the file</span>
              </div>
            </label>
          </div>
        </div>
        <div class="flex justify-end gap-3 border-t border-slate-800 bg-slate-800/50 px-6 py-4">
          <button @click="showImportModal = false" class="rounded-xl border border-slate-600 bg-slate-800 px-6 py-2 text-sm font-bold text-slate-300 hover:bg-slate-700 transition-all">Cancel</button>
          <button @click="openFilePicker" class="rounded-xl bg-blue-600 px-6 py-2 text-sm font-bold text-white hover:bg-blue-700 shadow-md transition-all">Select File</button>
        </div>
      </div>
    </div>

    <input type="file" ref="fileInput" class="hidden" @change="handleImportFile" accept=".csv,.xlsx,.xls" />

    <!-- SAVE CUSTOMER PRICE POPUP -->
    <div v-if="savePricePopup.show" class="fixed bottom-6 right-6 z-[200] w-80 rounded-xl border border-purple-500/40 bg-slate-900 shadow-2xl">
      <div class="flex items-center gap-3 border-b border-slate-700 px-4 py-3">
        <span class="text-base">💜</span>
        <span class="text-sm font-semibold text-slate-200">Save Customer Price?</span>
      </div>
      <div class="px-4 py-3 text-xs text-slate-400">
        <div class="mb-1 font-medium text-slate-300">{{ savePricePopup.item_name || savePricePopup.item_code }}</div>
        <div>Save <span class="font-mono text-purple-400">{{ savePricePopup.discount_percentage.toFixed(2) }}%</span> discount for <span class="text-slate-300">{{ customer }}</span>?</div>
      </div>
      <div class="flex gap-2 px-4 pb-3">
        <button @click="confirmSavePrice" class="flex-1 rounded-lg bg-purple-600 py-1.5 text-xs font-bold text-white hover:bg-purple-700">Yes, Save</button>
        <button @click="dismissSavePrice" class="flex-1 rounded-lg bg-slate-700 py-1.5 text-xs font-bold text-slate-300 hover:bg-slate-600">No</button>
      </div>
    </div>

    <!-- DISCARD QUOTATION MODAL -->
    <div v-if="showDiscardModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="showDiscardModal = false">
      <div class="w-[450px] overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl">
        <div class="bg-amber-900/20 px-6 py-6 flex items-center gap-4 border-b border-amber-900/30">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-amber-900/40 text-2xl text-amber-500">⚠️</div>
          <div>
            <div class="text-xl font-bold text-slate-100">Discard Unsaved Quotation?</div>
            <div class="text-sm text-amber-400">You have unsaved items in this quotation.</div>
          </div>
        </div>
        <div class="p-6">
          <p class="text-slate-400 leading-relaxed">Are you sure you want to go back to the dashboard? All unsaved changes will be permanently lost.</p>
        </div>
        <div class="flex justify-end gap-3 border-t border-slate-800 bg-slate-800/50 px-6 py-4">
          <button 
            ref="stayHereBtn"
            class="rounded-xl border border-slate-600 bg-slate-800 px-6 py-2.5 text-sm font-bold text-slate-300 hover:bg-slate-700 transition-all shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice, searchItems, fetchItemDetails, frappeGet, frappePost } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import ItemSearch from '../components/ItemSearch.vue'
import BarcodePrintingModal from '../components/BarcodePrintingModal.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import ShortcutPage from '../components/ShortcutPage.vue'
import { createCustomer, updateCustomer, fetchCustomerDetails } from '../api/customer.js'
import { useItemCache } from '../services/itemCache.js'
import { useDiscountRules } from '../composables/useDiscountRules.js'
import CustomerLedger from './CustomerLedger.vue'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { quotationEntryShortcuts } from '../shortcuts/quotationEntryShortcuts'
import * as XLSX from 'xlsx'

const router = useRouter()
const route = useRoute()
const API = 'ssplbilling.api.quotation_api'

const { items: cachedItems, refreshItemCache, lookupItemInCache, lastSync, fetchCustomerSalesHistory, getItemHistoryFromCache, refreshDiscountRuleCache } = useItemCache()

const props = defineProps({
  isSubWindow: {
    type: Boolean,
    default: false
  },
  quotationName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

if (props.isSubWindow) useSubwindow()

const showPrintModal = ref(false)
const printModalAfterSave = ref(false)
const showShortcutPage = ref(false)
const showBarcodeModal = ref(false)
const showImportModal = ref(false)
const importOption = ref('Master')
const fileInput = ref(null)

function openBarcodePrinting() {
  showBarcodeModal.value = true
}

function openImportModal() {
  showImportModal.value = true
}

function openFilePicker() {
  fileInput.value?.click()
}

// ==================== BILLING SETTINGS ====================
const billingSeriesConfig = ref([])
const cipherMap = ref([])
const defaultWarehouse = ref(localStorage.getItem('wb-warehouse') || '')
const defaultTaxRate = ref(18)
const priceList = ref('Standard Selling')
const printScheme = ref('')
const taxTemplate = ref('')
const costCenter = ref(localStorage.getItem('wb-cost-center') || '')
const incomeAccount = ref('')

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
  incomeAccount.value = cfg.income_account || ''

  // Only override if not set in localStorage
  if (!localStorage.getItem('wb-warehouse')) {
    if (cfg.warehouse) defaultWarehouse.value = cfg.warehouse
  }
  if (!localStorage.getItem('wb-cost-center')) {
    if (cfg.cost_center) costCenter.value = cfg.cost_center
  }
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
    console.warn('[QuotationEntry] fetchDropdownOptions failed:', e)
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
  return frappePost(`${API}.${method}`, params)
}

// ==================== INPUT REFS ====================
const inputRefs = {}
const rowRefs   = {}
const sidebarQuotationRefs = new Map()
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarQuotationRef(el, idx) { if (el) sidebarQuotationRefs.set(idx, el); else sidebarQuotationRefs.delete(idx) }
function navigateSidebarQuotation(idx, dir) {
  const target = sidebarQuotationRefs.get(idx + dir)
  if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }) }
}
function focusFirstSidebarQuotation() {
  const first = sidebarQuotationRefs.get(0)
  if (first) { first.focus(); first.scrollIntoView({ block: 'nearest' }) }
}
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const customerInput = ref(null)
const searchInput = ref(null)
const modifySearchInput = ref(null)
const seriesSelect = ref(null)
const showSeriesDropdown = ref(false)
const seriesHighlightIdx = ref(0)
const sidebarSeriesSelect = ref(null)
const dateInput = ref(null)
const discountInput = ref(null)
const discountAmtInput = ref(null)
const freightInput = ref(null)
const packingInput = ref(null)
const loadingInput = ref(null)
const otherChargesInput = ref(null)
const saveButton = ref(null)
const stayHereBtn = ref(null)
const custSearchModalRef = ref(null)
const resultsWrapRef = ref(null)
const searchRowRefs = new Map()
function setSearchRowRef(el, idx) { if (el) searchRowRefs.set(idx, el); else searchRowRefs.delete(idx) }

// ==================== CUSTOMER DROPDOWN ====================
const custSearch = ref('')
const showCustomerSearchModal = ref(false)
const selectedCustomerDetails = ref(null)

function openSeriesModal() {
  seriesHighlightIdx.value = Math.max(0, availableSeries.value.indexOf(quotationSeries.value))
  showSeriesDropdown.value = true
}

function selectSeries(s) {
  quotationSeries.value = s
  showSeriesDropdown.value = false
  nextTick(() => openCustomerSearch())
}

function openCustomerSearch() {
  if (quotationSaved.value || quotationDocStatus.value !== 0) return
  showCustomerSearchModal.value = true
  custSearch.value = ''
  nextTick(() => {
    custSearchModalRef.value?.closeSubForm()
    custSearchModalRef.value?.focus()
  })
}

function pickCust(c, dates) {
  if (c.type !== 'Customer') {
    showCustomerSearchModal.value = false
    openCustomerLedger(c.name, c.type, dates)
    return
  }
  customer.value = c.name; 
  custSearch.value = c.label || c.customer_name; 
  showCustomerSearchModal.value = false; 
  selectedCustomerDetails.value = c;
  nextTick(() => newCodeInput.value?.focus())
}

const showCustomerLedgerWindow = ref(false)
const ledgerCustomerName = ref('')
const ledgerType = ref('Customer')
const ledgerFromDate = ref('')
const ledgerToDate = ref('')

function openCustomerLedger(name, type, dates = null) {
  ledgerCustomerName.value = name
  ledgerType.value = type
  if (dates) {
    ledgerFromDate.value = dates.from
    ledgerToDate.value = dates.to
  } else {
    ledgerFromDate.value = ''
    ledgerToDate.value = ''
  }
  showCustomerLedgerWindow.value = true
}

function closeCustomerSearchModal() {
  showCustomerSearchModal.value = false
}

// ==================== STATE ====================
const items = ref([])
const selectedRow = ref(-1)
const newItemCode = ref('')
const newQty = ref(1)
const quotationSaved = ref(false)
const quotationDocStatus = ref(0) // 0=Draft, 1=Submitted, 2=Cancelled
const showJumpModal = ref(false)
const savedQuotationName = ref(null)   // null = new quotation; string = existing/just-saved quotation name
const showDiscardModal = ref(false)
const zoomPercent = ref(parseInt(localStorage.getItem('wb-zoom')) || 150)
const dynamicRowStyle = computed(() => ({
  fontSize: `${(14 * zoomPercent.value) / 100}px`,
  paddingTop: '0px',
  paddingBottom: '0px'
}))

const activeItems = computed(() => items.value.filter(i => !i.deleted))
const deletedCount = computed(() => items.value.filter(i => i.deleted).length)

// ==================== DISCOUNT RULES ====================
const { ignoreDiscountRule, makeRowKey, applyDiscountRuleForRow, reapplyAllDiscountRules } = useDiscountRules({
  items,
  priceList,
  lookupItemInCache,
})

// ==================== CUSTOMER PRICING ====================
const customerPricing = ref({}) // { item_code: discount_percentage }

async function loadCustomerPricing(cust) {
  if (!cust) { customerPricing.value = {}; return }
  try {
    const data = await frappeGet('ssplbilling.api.customer_pricing_api.get_customer_pricing', { customer: cust })
    customerPricing.value = data || {}
    // Re-apply to items already in the list (fetch may arrive after items were added)
    items.value.forEach((_, idx) => applyCustomerPricingForRow(idx))
  } catch (e) {
    customerPricing.value = {}
  }
}

function applyCustomerPricingForRow(idx) {
  const item = items.value[idx]
  if (!item || item.deleted || item._is_free || item._rule_discount != null) return
  const disc = customerPricing.value[item.item_code]
  if (disc != null && disc > 0) {
    item.discount = disc
    item._customer_pricing = true
  }
}

// Save-price popup
const savePricePopup = ref({ show: false, idx: null, item_code: '', item_name: '', discount_percentage: 0 })
let _rateAtFocus = null
let _discAtFocus = null

function onRateFocus(idx) { _rateAtFocus = items.value[idx]?.rate ?? null }
function onDiscountFocus(idx) { _discAtFocus = items.value[idx]?.discount ?? null }

function onRateBlur(idx) {
  const item = items.value[idx]
  if (!item || !customer.value || item._rule_discount != null) { _rateAtFocus = null; return }
  const newRate = item.rate
  if (_rateAtFocus === null || newRate === _rateAtFocus) { _rateAtFocus = null; return }
  // Compute discount vs cached list price
  const cached = lookupItemInCache(item.item_code)
  const listRate = (cached?.price || cached?.rate) || _rateAtFocus
  const discPct = listRate > 0 ? Math.max(0, Math.round(((listRate - newRate) / listRate) * 10000) / 100) : 0
  _rateAtFocus = null
  if (discPct >= 0) _triggerSavePricePopup(idx, discPct)
}

function onDiscountBlur(idx) {
  const item = items.value[idx]
  if (!item || !customer.value || item._rule_discount != null) { _discAtFocus = null; return }
  if (_discAtFocus === null || item.discount === _discAtFocus) { _discAtFocus = null; return }
  _discAtFocus = null
  _triggerSavePricePopup(idx, item.discount || 0)
}

function _triggerSavePricePopup(idx, discPct) {
  const item = items.value[idx]
  if (!item?.item_code) return
  savePricePopup.value = { show: true, idx, item_code: item.item_code, item_name: item.item_name, discount_percentage: discPct }
}

async function confirmSavePrice() {
  const { item_code, discount_percentage, idx } = savePricePopup.value
  try {
    await frappePost('ssplbilling.api.customer_pricing_api.save_customer_item_price', {
      customer: customer.value,
      item_code,
      discount_percentage,
    })
    customerPricing.value[item_code] = discount_percentage
    if (idx != null && items.value[idx]) items.value[idx]._customer_pricing = true
  } catch (e) {
    console.error('[CustomerPricing] save failed', e)
  }
  savePricePopup.value.show = false
}

function dismissSavePrice() { savePricePopup.value.show = false }

// ==================== API RESOURCES ====================
const itemLookup = createResource({ url: `/api/method/${API}.get_item_details` })
const itemSearchResource = createResource({ url: `/api/method/${API}.search_items` })
const insightResource = createResource({ url: `/api/method/${API}.get_item_insight` })

const newPending = ref({ item_name: '', uom: '', rate: null })

async function lookupItem(code) {
  // 1. Try local cache first
  const cached = lookupItemInCache(code)
  if (cached) {
    let finalRate = cached.price || cached.rate || 0
    if (cached.price_lists && priceList.value) {
      const pl = cached.price_lists.find(p => p.name === priceList.value)
      if (pl) finalRate = pl.rate
    }
    return {
      found: true,
      item_code: cached.item_code,
      item_name: cached.item_name,
      uom: cached.uom,
      rate: finalRate,
      stock_qty: cached.stock || 0,
      tax_rate: cached.tax_rate,
      warehouse: cached.warehouse
    }
  }

  // 2. Fallback to API if not found or cache empty
  try {
    const res = await itemLookup.submit({ item_code: code, price_list: priceList.value, warehouse: defaultWarehouse.value })
    const d = res?.message || res || itemLookup.data?.message || itemLookup.data
    return d?.found ? d : null
  } catch (e) { return null }
}

let lookupTimeout = null
watch(newItemCode, (val) => {
  clearTimeout(lookupTimeout); const code = val.trim()
  if (code.length < 2) { newPending.value = { item_name: '', uom: '', rate: null }; return }
  lookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    newPending.value = r ? { item_name: r.item_name, uom: r.uom, rate: r.rate, tax_rate: r.tax_rate, warehouse: r.warehouse } : { item_name: '', uom: '', rate: null }
  }, 300)
})

watch(showDiscardModal, (val) => {
  if (val) {
    nextTick(() => {
      stayHereBtn.value?.focus()
    })
  }
})

// Block page shortcuts while any inline subwindow is open
useSubwindowWatcher(showSeriesDropdown)
useSubwindowWatcher(showImportModal)
useSubwindowWatcher(showDiscardModal)

const selectedItemData = ref(null)

async function loadItemInsight(code, itemName = '', uom = '') {
  if (!code) {
    selectedItemData.value = null
    return
  }

  // 1. Fetch from local cache (Instant)
  const cached = lookupItemInCache(code)
  const localHistory = getItemHistoryFromCache(code)
  
  selectedItemData.value = {
    item_code: code,
    item_name: itemName || cached?.item_name || '',
    uom: uom || cached?.uom || '',
    stock: cached?.stock != null ? [{ warehouse: cached.warehouse || 'Total', actual_qty: cached.stock }] : [],
    previousPurchases: localHistory.slice(0, 10), // Show latest 10 from cache
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
function enterRow(idx) { if (!items.value[idx]?.deleted && quotationDocStatus.value === 0) focusField('code', idx) }
function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return  // bubbled from a child input — ignore
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); enterRow(idx) }
}

// ==================== ITEM ENTRY ====================
async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return; items.value[idx].item_code = code
  const r = await lookupItem(code)
  if (r) {
    items.value[idx].item_code = r.item_code || code  // use canonical case from lookup
    items.value[idx].item_name = r.item_name; items.value[idx].uom = r.uom; items.value[idx].rate = r.rate; items.value[idx].tax_rate = r.tax_rate ?? defaultTaxRate.value; items.value[idx].warehouse = r.warehouse; items.value[idx].deleted = false;
    if (!items.value[idx]._rowKey) items.value[idx]._rowKey = makeRowKey()
    loadItemInsight(r.item_code || code, r.item_name, r.uom)
    applyDiscountRuleForRow(idx)
    applyCustomerPricingForRow(idx)
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
  if (r) {
    if (r.item_code) newItemCode.value = r.item_code  // normalize to canonical case
    newPending.value = { item_name: r.item_name, uom: r.uom, rate: r.rate, tax_rate: r.tax_rate, warehouse: r.warehouse }
    focusNewQty()
  }
  else openSearch(code, null)
}

async function addNewItem() {
  const code = newItemCode.value.trim(); if (!code) return
  
  // Use newPending if it matches, otherwise lookup
  let r = (newPending.value && newItemCode.value === code && newPending.value.item_name) 
    ? newPending.value 
    : await lookupItem(code)

  if (!r) { openSearch(code, null); return }

  items.value.push({
    item_code: r.item_code || code,
    item_name: r.item_name,
    uom: r.uom,
    qty: newQty.value,
    rate: r.rate,
    discount: 0,
    tax_rate: r.tax_rate ?? defaultTaxRate.value,
    warehouse: r.warehouse || defaultWarehouse.value,
    deleted: false,
    _rowKey: makeRowKey(),
  })
  applyDiscountRuleForRow(items.value.length - 1)
  applyCustomerPricingForRow(items.value.length - 1)

  newItemCode.value = '';
  newQty.value = 1;
  newPending.value = { item_name: '', uom: '', rate: null };
  selectedRow.value = -1; // Reset selection so we stay in "new entry" mode
  focusNewCode()
}

function softDelete(idx) { items.value[idx].deleted = true }
function restoreItem(idx) { items.value[idx].deleted = false }

// ==================== ITEM SEARCH MODAL ====================
const showItemSearchModal = ref(false)
const itemSearchModalRef = ref(null)
const itemSearchInitialQuery = ref('')
let itemSearchTargetRow = null

async function openSearch(prefill = '', rowIdx = null) {
  itemSearchTargetRow = rowIdx
  // Determine which item to highlight (search box stays empty)
  if (prefill) {
    itemSearchInitialQuery.value = prefill
  } else if (selectedRow.value >= 0 && items.value[selectedRow.value]) {
    itemSearchInitialQuery.value = items.value[selectedRow.value].item_code || ''
  } else {
    // New entry row: highlight the last active item
    const lastItem = [...items.value].reverse().find(i => !i.deleted)
    itemSearchInitialQuery.value = lastItem?.item_code || ''
  }
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
  
  // Fetch real-time details
  let finalRate = item.price || 0
  let finalTax = item.tax_rate ?? defaultTaxRate.value
  let finalWh = item.warehouse || defaultWarehouse.value
  
  try {
    const r = await lookupItem(item.item_code)
    if (r) {
      finalRate = r.rate
      finalTax = r.tax_rate ?? defaultTaxRate.value
      finalWh = r.warehouse || defaultWarehouse.value
    }
  } catch (e) {}

  if (itemSearchTargetRow !== null) {
    const row = items.value[itemSearchTargetRow]
    row.item_code = item.item_code
    row.item_name = item.item_name
    row.uom = item.uom
    row.rate = finalRate
    row.discount = row.discount || 0
    row.tax_rate = finalTax
    row.warehouse = finalWh
    row.deleted = false
    if (!row._rowKey) row._rowKey = makeRowKey()
    selectedRow.value = itemSearchTargetRow
    applyDiscountRuleForRow(itemSearchTargetRow)
    applyCustomerPricingForRow(itemSearchTargetRow)
    focusField('qty', itemSearchTargetRow)
  } else {
    newItemCode.value = item.item_code
    newPending.value = { item_name: item.item_name, uom: item.uom, rate: finalRate }
    nextTick(() => focusNewQty())
  }
}

async function handleImportFile(event) {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = async (e) => {
    const data = new Uint8Array(e.target.result)
    const workbook = XLSX.read(data, { type: 'array' })
    const sheetName = workbook.SheetNames[0]
    const sheet = workbook.Sheets[sheetName]
    const jsonData = XLSX.utils.sheet_to_json(sheet)

    for (const row of jsonData) {
      const itemCode = String(row['Item Code'] || row['item_code'] || '').trim()
      const qty = parseFloat(row['Qty'] || row['qty'] || 1)
      if (!itemCode) continue

      let rate = parseFloat(row['Rate'] || row['rate'] || 0)
      let discount = parseFloat(row['Discount %'] || row['Discount'] || row['discount'] || 0)
      let itemName = row['Item Name'] || row['item_name'] || ''
      let uom = row['UOM'] || row['uom'] || ''
      let taxRate = parseFloat(row['Tax %'] || row['tax_rate'] || defaultTaxRate.value)

      if (importOption.value === 'Master') {
        const master = await lookupItem(itemCode)
        if (master) {
          rate = master.rate
          discount = 0 
          itemName = master.item_name
          uom = master.uom
          taxRate = master.tax_rate ?? defaultTaxRate.value
        }
      }

      const existing = items.value.findIndex(i => i.item_code === itemCode && !i.deleted)
      if (existing >= 0) {
        items.value[existing].qty += qty
        if (importOption.value === 'File') {
          items.value[existing].rate = rate
          items.value[existing].discount = discount
        }
      } else {
        items.value.push({
          item_code: itemCode,
          item_name: itemName,
          uom: uom,
          qty: qty,
          rate: rate,
          discount: discount,
          tax_rate: taxRate,
          warehouse: defaultWarehouse.value,
          deleted: false
        })
      }
    }
    showImportModal.value = false
    event.target.value = '' 
  }
  reader.readAsArrayBuffer(file)
}

function exportItems() {
  const data = activeItems.value.map((i, idx) => ({
    '#': idx + 1,
    'Item Code': i.item_code,
    'Item Name': i.item_name,
    'Qty': i.qty,
    'UOM': i.uom,
    'Rate': i.rate,
    'Discount %': i.discount || 0,
    'Tax %': i.tax_rate,
    'Amount': (i.qty * i.rate * (1 - (i.discount || 0) / 100)).toFixed(2)
  }))

  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Items')
  XLSX.writeFile(wb, `Quotation_Items_${new Date().toISOString().slice(0, 10)}.xlsx`)
}

// ==================== SIDEBAR MODIFY PANEL ====================
const sidebarDate = ref(getTodayIST())
const sidebarSearch = ref('')
const sidebarSeries = ref('')
const draftOnly = ref(false)
const sidebarQuotations = ref([])
const sidebarLoading = ref(false)

async function fetchSidebarQuotations() {
  sidebarLoading.value = true
  try {
    sidebarQuotations.value = await apiPost('get_quotations', {
      query: sidebarSearch.value,
      limit: 100,
      transaction_date: sidebarDate.value,
      show_submitted: !draftOnly.value
    })
  } catch (e) {
    sidebarQuotations.value = []
  }
  sidebarLoading.value = false
}

function changeSidebarDate(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

watch([sidebarDate, sidebarSeries, draftOnly], fetchSidebarQuotations)

let sidebarSearchTimeout = null
watch(sidebarSearch, () => {
  clearTimeout(sidebarSearchTimeout)
  sidebarSearchTimeout = setTimeout(fetchSidebarQuotations, 500)
})

async function loadQuotation(quotationName) {
  try {
    const inv = await apiPost('get_quotation', { quotation_name: quotationName })
    if (!inv) { alert('Could not load quotation'); return }

    // Populate form with quotation data
    customer.value = inv.customer
    custSearch.value = inv.customer_name
    quotationDate.value = inv.transaction_date
    if (inv.naming_series && availableSeries.value.includes(inv.naming_series)) {
      quotationSeries.value = inv.naming_series
    }
    if (inv.additional_discount_amount > 0) {
      discountDirectAmt.value = inv.additional_discount_amount
      discountPct.value = 0
      discountInputMode.value = 'amt'
    } else {
      discountPct.value = inv.discount_percentage || 0
      discountDirectAmt.value = 0
      discountInputMode.value = inv.discount_percentage > 0 ? 'pct' : null
    }
    freightAmt.value = inv.freight_amount || 0
    packingAmt.value = inv.packing_amount || 0
    loadingAmt.value = inv.loading_amount || 0
    otherChargesAmt.value = inv.other_charges_amount || 0
    if (inv.tax_template) taxTemplate.value = inv.tax_template
    if (inv.cost_center) costCenter.value = inv.cost_center
    if (inv.price_list) priceList.value = inv.price_list
    items.value = inv.items.map(i => {
      const disc = i.discount || 0
      const savedListRate = disc > 0 ? Math.round((i.rate / (1 - disc / 100)) * 100) / 100 : i.rate
      const cached = lookupItemInCache(i.item_code)
      const listRate = (cached && (cached.price || cached.rate)) ? (cached.price || cached.rate) : savedListRate
      const isFreeRow = (i.rate === 0 || i.rate === '0') && disc === 0
      return {
        ...i,
        rate: listRate,
        discount: disc,
        tax_rate: i.tax_rate ?? defaultTaxRate.value,
        _rowKey: makeRowKey(),
        _rule_discount: disc > 0 ? disc : null,
        _is_free: isFreeRow,
      }
    })
    selectedRow.value = -1
    newItemCode.value = ''
    newQty.value = 1
    newPending.value = { item_name: '', uom: '', rate: null }
    selectedItemData.value = null

    savedQuotationName.value = inv.name
    quotationDocStatus.value = inv.docstatus
    quotationSaved.value = true
    // Auto-enter edit mode for draft quotations
    if (inv.docstatus === 0) {
      quotationSaved.value = false
    }
    fetchNextQuotationNo()

    // Set selectedCustomerDetails for display
    try {
      selectedCustomerDetails.value = await fetchCustomerDetails(inv.customer)
    } catch (e) {
      selectedCustomerDetails.value = {
        name: inv.customer,
        customer_name: inv.customer_name,
        balance: 0,
        address_line1: ""
      }
    }

    nextTick(() => customerInput.value?.focus())
  } catch (e) {
    alert('Error loading quotation: ' + (e.message || 'Unknown error'))
  }
}

/** Click Edit after save → re-enable the form for updates */
function enterEditMode() {
  if (quotationDocStatus.value !== 0) {
    alert('Cannot edit a submitted/cancelled quotation.')
    return
  }
  quotationSaved.value = false
  nextTick(() => customerInput.value?.focus())
}

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

// ==================== QUOTATION ====================
const quotationDate = ref(getTodayIST())
const customer = ref('')
const quotationSeries = ref('')

watch(customer, async (newVal) => {
  if (!newVal) {
    fetchCustomerSalesHistory(null)
    loadCustomerPricing(null)
    return
  }

  // Fetch sales history and customer pricing in bulk
  fetchCustomerSalesHistory(newVal)
  loadCustomerPricing(newVal)

  if (!selectedCustomerDetails.value) return
  try {
    const stats = await frappeGet('ssplbilling.api.customersearch_api.get_customer_quick_stats', { customer: newVal })
    if (stats && selectedCustomerDetails.value && selectedCustomerDetails.value.name === newVal) {
      selectedCustomerDetails.value = { ...selectedCustomerDetails.value, ...stats }
    }
  } catch (e) {
    console.warn('[QuotationEntry] Failed to fetch customer quick stats:', e)
  }
})

const discountPct = ref(0)
const discountDirectAmt = ref(0)
const discountInputMode = ref(null) // null | 'pct' | 'amt'
const freightAmt = ref(0)
const packingAmt = ref(0)
const loadingAmt = ref(0)
const otherChargesAmt = ref(0)
const availableSeries = ref([])
const nextQuotationNo = ref('...')

watch(quotationSeries, (series) => {
  syncSeriesConfig(series)
  fetchNextQuotationNo()
})

import { session } from '../session.js'

async function fetchSeriesList() {
  try {
    const settings = await fetchBillingSettings()
    const rows = (settings?.billing_series || []).filter(r => r.series)

    // Filter available series based on Quotation naming series
    try {
      const list = await apiPost('get_naming_series')
      if (Array.isArray(list) && list.length) {
        availableSeries.value = list
        
        const target = availableSeries.value.includes(quotationSeries.value)
          ? quotationSeries.value
          : availableSeries.value[0]

        if (target !== quotationSeries.value) {
          quotationSeries.value = target
        } else {
          syncSeriesConfig(target)
          fetchNextQuotationNo()
        }
        return
      }
    } catch (e) {}

    if (rows.length) {
      billingSeriesConfig.value = rows
      availableSeries.value = rows.map(r => r.series)

      if (!localStorage.getItem('wb-warehouse')) {
        if (settings.default_warehouse) defaultWarehouse.value = settings.default_warehouse
      }
      try {
        const raw = settings.cipher_map
        if (raw) {
          const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
          if (Array.isArray(parsed) && parsed.length === 10) cipherMap.value = parsed
        }
      } catch (e) { /* non-fatal */ }

      const target = availableSeries.value.includes(quotationSeries.value)
        ? quotationSeries.value
        : availableSeries.value[0]

      if (target !== quotationSeries.value) {
        quotationSeries.value = target
      } else {
        syncSeriesConfig(target)
        fetchNextQuotationNo()
      }
      return
    }
  } catch (e) {
    console.warn('[QuotationEntry] fetchBillingSettings failed, falling back:', e)
  }

  fetchNextQuotationNo()
}

async function fetchNextQuotationNo() {
  if (savedQuotationName.value) {
    nextQuotationNo.value = savedQuotationName.value
    return
  }
  if (!quotationSeries.value) { nextQuotationNo.value = '...'; return }
  try {
    const res = await apiPost('get_next_quotation_no', { naming_series: quotationSeries.value })
    nextQuotationNo.value = res || '...'
  } catch (e) { nextQuotationNo.value = '...' }
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

const discountAmt = computed(() =>
  discountInputMode.value === 'amt'
    ? discountDirectAmt.value
    : subtotal.value * (discountPct.value / 100)
)
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
  const base = isInclusive.value 
    ? grossTotal.value * (1 - discountPct.value / 100)
    : taxableAmt.value + totalTax.value
  return base + (freightAmt.value || 0) + (packingAmt.value || 0) + (loadingAmt.value || 0) + (otherChargesAmt.value || 0)
})

async function saveQuotation() {
  if (!customer.value.trim()) { openCustomerSearch(); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    customer: customer.value,
    date: quotationDate.value,
    naming_series: quotationSeries.value,
    ...(discountInputMode.value === 'amt'
      ? { additional_discount_amount: discountDirectAmt.value, discount_percentage: 0 }
      : { discount_percentage: discountPct.value, additional_discount_amount: 0 }),
    freight_amount: freightAmt.value,
    freight_account: localStorage.getItem('wb_freight') || '',
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
      income_account: incomeAccount.value || '',
    })),
  }

  const chargeDefs = [
    { amt: freightAmt.value,       key: 'wb_freight',        desc: 'Freight Charges' },
    { amt: packingAmt.value,       key: 'wb-packing',        desc: 'Packing Charges' },
    { amt: loadingAmt.value,       key: 'wb-loading',        desc: 'Loading Charges' },
    { amt: otherChargesAmt.value,  key: 'wb-other-charges',  desc: 'Other Charges'   },
  ]
  const taxRows = chargeDefs
    .filter(c => c.amt > 0 && localStorage.getItem(c.key))
    .map(c => ({
      charge_type: 'Actual',
      account_head: localStorage.getItem(c.key),
      description: c.desc,
      tax_amount: c.amt,
      cost_center: costCenter.value || '',
    }))
  if (taxRows.length) payload.taxes = taxRows

  try {
    let result
    if (savedQuotationName.value) {
      // Update existing draft quotation
      result = await apiPost('update_quotation', {
        data: JSON.stringify({ ...payload, quotation_name: savedQuotationName.value }),
      })
    } else {
      // Create new quotation
      result = await apiPost('create_quotation', {
        data: JSON.stringify(payload),
      })
      savedQuotationName.value = result?.quotation_name || null
    }

    quotationSaved.value = true
    quotationDocStatus.value = 0 // Still Draft after save/update
    fetchNextQuotationNo()
    fetchSidebarQuotations()
    printModalAfterSave.value = true
    showPrintModal.value = true
  } catch (e) {
    alert('Error: ' + (e?.message || 'Failed to save quotation'))
  }
}

function startNewQuotation() {
  items.value = []; selectedRow.value = -1; customer.value = ''; custSearch.value = ''
  discountPct.value = 0; discountDirectAmt.value = 0; discountInputMode.value = null; freightAmt.value = 0; packingAmt.value = 0; loadingAmt.value = 0; otherChargesAmt.value = 0; newItemCode.value = ''; newQty.value = 1
  quotationDate.value = getTodayIST()
  quotationSaved.value = false; quotationDocStatus.value = 0; savedQuotationName.value = null; selectedItemData.value = null
  selectedCustomerDetails.value = null
  syncSeriesConfig(quotationSeries.value) // Restore price list and other settings from general settings
  fetchCustomerSalesHistory(null) // Clear history cache
  nextTick(() => focusNewCode())
}

function printQuotation() {
  if (!savedQuotationName.value) { alert('Save the quotation first before printing.'); return }
  printModalAfterSave.value = false
  showPrintModal.value = true
}
function cancelQuotation() { startNewQuotation() }

function handleJump(targetNo) {
  if (items.value.length === 0) return
  
  // Convert 1-based row number to 0-based index
  let targetIdx = targetNo - 1
  
  // If number is higher than total rows, go to last row
  if (targetIdx >= items.value.length) {
    targetIdx = items.value.length - 1
  }
  
  // If row is deleted, find previous active row
  if (items.value[targetIdx].deleted) {
    const prev = findNextActiveRow(targetIdx, -1)
    if (prev !== null) targetIdx = prev
    else {
      const next = findNextActiveRow(targetIdx, 1)
      if (next !== null) targetIdx = next
      else return // All items deleted
    }
  }

  selectedRow.value = targetIdx
  focusRow(targetIdx)
}

function focusModifyPanel() {
  nextTick(() => {
    const el = sidebarQuotationRefs.get(0)
    if (el) el.focus()
  })
}

function handleBack() {
  if (activeItems.value.length > 0 && !quotationSaved.value) {
    showDiscardModal.value = true
  } else {
    if (props.isSubWindow) {
      emit('close')
      return
    }
    if (route.query.from === 'ledger' && customer.value) {
      router.push({ path: '/ledger', query: { customer: customer.value } })
    } else {
      router.push('/')
    }
  }
}

// ==================== KEYBOARD SHORTCUTS ====================
useShortcuts(quotationEntryShortcuts({
  openShortcuts: () => { showShortcutPage.value = !showShortcutPage.value },
  save: () => { if (!showPrintModal.value) saveQuotation() },
  newQuotation: () => { if (!showPrintModal.value) cancelQuotation() },
  print: () => { if (!showPrintModal.value) printQuotation() },
  newCustomer: () => { if (!showPrintModal.value) openCustomerSearch() },
  searchItem: () => { if (!showPrintModal.value) openSearch('', null) },
  focusModifyPanel: () => { if (!showPrintModal.value) focusModifyPanel() },
  enterEditMode: () => { if (quotationSaved.value) enterEditMode() },
  focusSidebarSeries: () => { sidebarSeriesSelect.value?.focus() },
  deleteRow: () => {
    if (!showPrintModal.value && selectedRow.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      softDelete(selectedRow.value)
    }
  },
  focusSeries: () => { if (!showPrintModal.value) openSeriesModal() },
  toggleDiscountSave: () => {
    if (showPrintModal.value) return
    const activeEl = document.activeElement
    const isEditMode = !!savedQuotationName.value && !quotationSaved.value  // modifying existing draft
    const isNewQuotation = !savedQuotationName.value

    // If focused on any charge input → End triggers save/update
    const chargeInputs = [discountInput.value, discountAmtInput.value, freightInput.value, packingInput.value, loadingInput.value, otherChargesInput.value]
    if (chargeInputs.includes(activeEl)) {
      saveQuotation()
      return
    }

    // If in existing items table
    if (selectedRow.value !== -1) {
      const lastActiveIdx = items.value.reduce((acc, item, i) => (!item.deleted ? i : acc), -1)
      if (selectedRow.value < lastActiveIdx) {
        selectRow(lastActiveIdx)
        return
      }
    }

    // From last row or new entry row: go to discount %
    discountInput.value?.focus()
    discountInput.value?.select()
  },
  jumpToFirstRow: () => {
    if (activeItems.value.length) selectRow(items.value.findIndex(i => !i.deleted))
  },
  contextualBack: () => {
    if (showJumpModal.value) { showJumpModal.value = false; return }
    if (showDiscardModal.value) { showDiscardModal.value = false; return }
    if (showPrintModal.value) { showPrintModal.value = false; startNewQuotation(); return }
    if (showBarcodeModal.value) { showBarcodeModal.value = false; return }
    if (showImportModal.value) { showImportModal.value = false; return }
    if (showCustomerSearchModal.value) { closeCustomerSearchModal(); return }
    if (showItemSearchModal.value) { closeItemSearch(); return }
    if (showCustomerLedgerWindow.value) { showCustomerLedgerWindow.value = false; return }
    // First Esc: clear active quotation; Second Esc (quotation already empty): exit
    const hasQuotationContent = activeItems.value.length > 0 || customer.value || savedQuotationName.value
    if (hasQuotationContent) { startNewQuotation(); return }
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

function handleStorageChange(e) {
  if (e.key === 'wb-zoom') zoomPercent.value = parseInt(e.newValue) || 150
  if (e.key === 'wb-warehouse') defaultWarehouse.value = e.newValue || ''
  if (e.key === 'wb-cost-center') costCenter.value = e.newValue || ''
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

onMounted(() => {
  // Listen for global shortcut events
  window.addEventListener('wb-global-ledger-search', openCustomerSearch);
  window.addEventListener('wb-global-item-search', () => openSearch('', null));
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('storage', handleStorageChange);
  window.addEventListener('keydown', handleSeriesNumberKey);

  fetchSeriesList()
  fetchDropdownOptions()
  fetchSidebarQuotations()
  
  // Ensure item cache is populated (TTL 5 mins)
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) {
    refreshItemCache('Sales', priceList.value, defaultWarehouse.value)
  }
  // Always refresh discount rules for every new quotation session
  refreshDiscountRuleCache()
  
  const targetQuotation = props.isSubWindow ? props.quotationName : route.query.quotation
  if (targetQuotation) {
    loadQuotation(targetQuotation)
  } else {
    nextTick(() => openSeriesModal())
  }
})
onUnmounted(() => {
  window.removeEventListener('wb-global-ledger-search', openCustomerSearch);
  window.removeEventListener('wb-global-item-search', () => openSearch('', null));
  window.removeEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.removeEventListener('storage', handleStorageChange);
  window.removeEventListener('keydown', handleSeriesNumberKey);
})
</script>

<style scoped>
/* Hide number input spinners across all browsers */
input[type='number']::-webkit-inner-spin-button,
input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type='number'] {
  -moz-appearance: textfield;
}
</style>
