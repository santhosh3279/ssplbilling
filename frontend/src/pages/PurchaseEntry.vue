<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'h-screen flex flex-col bg-slate-900'">
    <div class="flex h-full flex-col">
    <!-- Top Bar -->
    <header class="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-4 py-2.5">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-slate-400 hover:bg-slate-700" @click="handleBack">&larr; Dashboard</button>
        <span class="text-sm text-slate-600">|</span>
        <span class="text-sm font-semibold text-slate-200">Purchase Entry</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-slate-400">
        <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden mr-4">
          <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
          <div class="flex flex-col items-center justify-center border-x border-slate-700 bg-slate-900 px-3 min-w-[50px]">
            <span class="text-[9px] font-bold uppercase tracking-tight text-slate-500 leading-none">Zoom</span>
            <span class="text-[11px] font-bold text-slate-300 leading-tight">{{ zoomPercent }}%</span>
          </div>
          <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-7 w-8 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
        </div>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Up/Down</kbd> Navigate rows</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Tab</kbd> Next column</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[10px] text-slate-300">Esc</kbd> {{ billSaved ? 'New Bill' : 'Back' }}</span>
        <div class="ml-2 h-4 w-px bg-slate-700"></div>
        <div class="flex items-center gap-1.5 font-bold text-blue-400">
          <span class="text-[10px] text-slate-500 font-medium">HI</span>
          <span class="truncate max-w-[120px] uppercase tracking-wide">{{ (session.fullName.value || 'User').split('@')[0] }}</span>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- SIDEBAR: Modify Bills -->
      <aside class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Modify Bills</div>
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

        <!-- Search & Filters -->
        <div class="flex flex-col gap-1.5 border-b border-slate-700 p-2 bg-slate-800/20">
          <input
            type="text"
            v-model="sidebarSearch"
            placeholder="Search invoice/supplier..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 outline-none focus:border-blue-500"
          />
          <button
            @click="showSubmitted = !showSubmitted"
            class="w-full rounded border py-1 text-[10px] font-bold uppercase transition-colors"
            :class="showSubmitted ? 'bg-blue-900/40 border-blue-500 text-blue-300' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'"
          >
            {{ showSubmitted ? 'Showing All' : 'Drafts Only' }}
          </button>
        </div>

        <!-- Bill List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="sidebarLoading" class="p-4 text-center text-xs text-slate-500">Loading...</div>
          <div v-else-if="!sidebarBills.length" class="p-4 text-center text-xs text-slate-600 italic">No bills found</div>
          <div
            v-for="(inv, idx) in sidebarBills"
            :key="inv.name"
            :ref="el => setSidebarBillRef(el, idx)"
            @click="loadInvoice(inv.name)"
            class="group cursor-pointer border-b border-slate-800 bg-slate-900 p-2.5 transition-colors hover:bg-slate-800 outline-none focus:bg-slate-800 focus:ring-1 focus:ring-blue-500"
            :class="{ 'bg-slate-800 border-l-2 border-l-blue-500': savedInvoiceName === inv.name }"
            tabindex="0"
            @keydown.enter="loadInvoice(inv.name)"
          >
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-2 truncate">
                <span class="h-2 w-2 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-green-500' : 'bg-red-500'"></span>
                <span class="truncate font-mono text-2xl font-bold text-blue-400">{{ inv.name }}</span>
              </div>
              <span class="rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-tighter" :class="{
                'bg-slate-700 text-slate-400': inv.status === 'Draft',
                'bg-green-900/40 text-green-400': inv.status === 'Paid',
                'bg-blue-900/40 text-blue-400': inv.status === 'Submitted',
                'bg-red-900/40 text-red-400': inv.status === 'Cancelled'
              }">{{ inv.status[0] }}</span>
            </div>
            <div class="mt-0.5 truncate text-lg font-medium text-slate-400">{{ inv.supplier_name }}</div>
            <div class="flex items-center justify-between text-lg font-bold text-slate-200 tabular-nums">
              <span>₹{{ inv.grand_total.toFixed(0) }}</span>
              <button
                class="rounded px-1.5 py-0.5 text-[11px] font-bold text-orange-400 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-orange-900/30"
                @click.stop="loadAndPrintBarcodes(inv.name)"
                title="Print Barcodes"
              >🏷️</button>
            </div>
          </div>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <div class="flex flex-1 flex-col overflow-hidden bg-slate-900">
        <!-- Subheader: Series / Supplier / Date -->
        <div class="border-b border-slate-700 bg-slate-800 px-4 py-2 shrink-0">
          <div class="flex items-center gap-6">
            <!-- Series -->
            <div class="flex items-center gap-2">
              <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Series</label>
              <select
                ref="seriesSelect"
                v-model="billSeries"
                :disabled="billDocStatus !== 0"
                class="rounded border border-slate-600 bg-slate-900 px-2 py-1 text-sm font-bold text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800 disabled:text-slate-500"
                @keydown.enter.prevent="openSupplierSearch"
              >
                <option v-for="s in availableSeries" :key="s">{{ s }}</option>
              </select>
            </div>

            <!-- Bill No -->
            <div class="flex items-center gap-2 border-l border-slate-700 pl-6">
              <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Bill No</label>
              <div class="text-xl font-bold text-slate-100 tabular-nums" style="font-family: 'Poppins', sans-serif">
                {{ nextBillNo }}
              </div>
            </div>

            <!-- Supplier Section -->
            <div class="flex-1 flex items-center gap-4 border-l border-slate-700 pl-6 overflow-hidden">
              <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Supplier</label>
              <div class="flex items-baseline gap-4 min-w-0">
                <div
                  ref="supplierInput"
                  class="shrink-0 max-w-[300px] truncate text-xl font-bold transition-colors cursor-pointer outline-none hover:text-blue-400 focus:text-blue-400 leading-none"
                  :class="supplier ? 'text-slate-100' : 'text-slate-600 italic'"
                  style="font-family: 'Poppins', sans-serif"
                  @click="openSupplierSearch"
                  tabindex="0"
                  @keydown.enter.prevent="openSupplierSearch"
                  @keydown.space.prevent="openSupplierSearch"
                >
                  {{ suppSearch || 'Not Selected' }}
                </div>
                <div v-if="selectedSupplierDetails" class="flex items-center gap-3 min-w-0">
                  <span v-if="selectedSupplierDetails.address_line1" class="truncate max-w-[350px] text-xl text-slate-400 font-normal leading-none" :title="selectedSupplierDetails.address_line1">
                    {{ selectedSupplierDetails.address_line1 }}{{ selectedSupplierDetails.city ? ', ' + selectedSupplierDetails.city : '' }}
                  </span>
                  <span v-if="selectedSupplierDetails.mobile_no" class="whitespace-nowrap text-[10px] text-slate-500 font-bold leading-none">
                    PH: {{ selectedSupplierDetails.mobile_no }}
                  </span>
                </div>
              </div>
              <div v-if="selectedSupplierDetails" class="flex items-center gap-6 ml-auto mr-6">
                <div v-if="selectedSupplierDetails.last_invoice_date" class="flex flex-col items-end leading-none">
                  <span class="text-[8px] uppercase tracking-wider text-slate-500 font-bold mb-0.5">Last Inv</span>
                  <span class="text-sm text-slate-300 font-medium">
                    {{ new Date(selectedSupplierDetails.last_invoice_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) }}
                  </span>
                </div>
                <div class="flex flex-col items-end leading-none border-l border-slate-700 pl-6">
                  <span class="text-[8px] uppercase tracking-wider text-slate-500 font-bold mb-0.5">Ledger Bal</span>
                  <span :class="selectedSupplierDetails.balance > 0 ? 'text-green-400' : 'text-red-400'" class="text-xl font-bold tabular-nums">
                    &#8377;{{ Math.abs(selectedSupplierDetails.balance || 0).toFixed(2) }} <span class="text-[10px] font-bold">{{ selectedSupplierDetails.balance > 0 ? 'DR' : 'CR' }}</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- Supplier Bill No -->
            <div class="flex items-center gap-3 border-l border-slate-700 pl-6 whitespace-nowrap">
              <label class="text-[10px] font-bold uppercase text-slate-500">Bill No</label>
              <input
                ref="billNoInput"
                v-model="billNo"
                placeholder="Supplier Bill #"
                :disabled="billDocStatus !== 0"
                class="w-32 rounded border border-slate-600 bg-slate-900 px-2 py-0.5 text-lg font-bold text-slate-100 outline-none focus:border-blue-500 disabled:bg-slate-800 disabled:text-slate-500"
                @keydown.enter.prevent="focusNewCode"
              />
            </div>

            <!-- Bill Date -->
            <div class="flex items-center gap-3 border-l border-slate-700 pl-6 whitespace-nowrap">
              <label class="text-[10px] font-bold uppercase text-slate-500">Bill Date</label>
              <input
                ref="dateInput"
                v-model="billDate"
                type="date"
                :disabled="billDocStatus !== 0"
                class="rounded border border-slate-600 bg-slate-900 px-2 py-0.5 text-xl font-bold text-slate-100 outline-none focus:border-blue-500 disabled:bg-slate-800 disabled:text-slate-500 tabular-nums"
                style="font-family: 'Poppins', sans-serif"
              />
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
                  <th class="w-16 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Tax %</th>
                  <th class="w-24 border-r border-b border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-300">Amount</th>
                  <th class="w-8 border-b border-slate-700"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in items" :key="idx" :ref="el => setRowRef(el, idx)" tabindex="-1" class="cursor-pointer border-b border-slate-700 outline-none transition-colors" :class="{ 'bg-blue-900/30 border-l-2 border-l-blue-500': selectedRow === idx && !item.deleted, 'bg-red-900/20': item.deleted, 'hover:bg-slate-800/40': !item.deleted && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full font-bold" :class="item.deleted ? 'bg-red-900/30 text-red-400' : 'bg-slate-800 text-slate-400'" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">{{ idx + 1 }}</span></td>
                  <td class="p-0 border-r border-slate-700">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="billDocStatus !== 0" class="w-full rounded border border-slate-600 bg-slate-800 font-mono text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-900" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="onCodeEnter(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span :class="item.deleted ? 'text-red-900/50 line-through' : 'text-slate-200'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</span><span v-if="item.deleted" class="ml-1 font-semibold text-red-500" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">DELETED</span></td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="billDocStatus !== 0" min="1" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="(item.uoms||[]).length > 1 ? focusField('uom', idx) : onQtyEnter(idx)" @keydown.tab.prevent="(item.uoms||[]).length > 1 ? focusField('uom', idx) : onQtyEnter(idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.qty }}</span>
                  </td>
                  <td class="p-0 border-r border-slate-700">
                    <select v-if="selectedRow === idx && !item.deleted && (item.uoms || []).length > 1" :ref="el => setRef(el, 'uom', idx)" v-model="item.uom" :disabled="billDocStatus !== 0" class="w-full rounded border border-transparent bg-transparent font-mono text-slate-200 outline-none focus:border-blue-500 focus:bg-slate-800 disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @change="onUomChange(idx)" @keydown.enter.prevent="onQtyEnter(idx)" @keydown.tab.prevent="onQtyEnter(idx)" @keydown.shift.tab.prevent="focusField('qty', idx)" @keydown.up.stop @keydown.down.stop>
                      <option v-for="u in item.uoms" :key="u.uom" :value="u.uom">{{ u.uom }}</option>
                    </select>
                    <span v-else class="px-2 font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</span>
                  </td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="billDocStatus !== 0" step="0.01" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="focusField('discount', idx)" @keydown.tab.prevent="focusField('discount', idx)" @keydown.shift.tab.prevent="(item.uoms||[]).length > 1 ? focusField('uom', idx) : focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.rate.toFixed(2) }}</span>
                  </td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'discount', idx)" type="number" v-model.number="item.discount" :disabled="billDocStatus !== 0" step="0.5" min="0" max="100" class="w-full rounded border border-transparent bg-transparent text-right font-mono text-slate-200 focus:border-blue-500 focus:bg-slate-800 focus:outline-none disabled:cursor-not-allowed appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.shift.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-300'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.discount || 0 }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-slate-600' : 'text-slate-400'" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ isExempted ? 0 : (item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700 font-mono font-semibold" :class="item.deleted ? 'text-slate-600 line-through' : 'text-slate-200'" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.deleted ? '' : (item.qty * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2) }}</td>
                  <td class="px-2 text-center" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button v-if="!item.deleted" class="rounded px-1 py-0.5 text-slate-600 hover:bg-red-900/30 hover:text-red-400" :style="{ fontSize: dynamicRowStyle.fontSize }" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else class="rounded px-1 py-0.5 font-semibold text-blue-500 hover:bg-blue-900/30 hover:text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }" @click.stop="restoreItem(idx)">&larr;</button>
                  </td>
                </tr>
                <!-- NEW ENTRY ROW -->
                <tr v-if="billDocStatus === 0" class="border-b border-slate-700" :class="selectedRow === -1 ? 'bg-blue-900/20' : 'bg-slate-800/30'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-900/50 font-bold text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">+</span></td>
                  <td class="p-0 border-r border-slate-700"><input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-slate-600 bg-slate-800 text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-900/50" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Barcode" @keydown.enter.prevent="onNewCodeEnter" @keydown.tab.prevent="focusNewQty" @keydown.up.prevent="moveToLastActiveRow" /></td>
                  <td class="px-2 text-slate-400 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.item_name || '--' }}</td>
                  <td class="px-0 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><input ref="newQtyInput" v-model.number="newQty" type="number" min="1" class="w-full rounded border border-slate-600 bg-slate-800 text-right font-mono text-slate-200 outline-none focus:border-blue-500 appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="(newPending.uoms||[]).length > 1 ? $nextTick(() => newUomSelect?.focus()) : addNewItem()" @keydown.shift.tab.prevent="focusNewCode" /></td>
                  <td class="p-0 border-r border-slate-700">
                    <select v-if="(newPending.uoms || []).length > 1" ref="newUomSelect" v-model="newPending.uom" class="w-full rounded border border-slate-600 bg-slate-800 font-mono text-slate-200 outline-none focus:border-blue-500 appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @change="onNewUomChange" @keydown.enter.prevent="addNewItem" @keydown.tab.prevent="addNewItem" @keydown.shift.tab.prevent="focusNewQty" @keydown.up.stop @keydown.down.stop>
                      <option v-for="u in newPending.uoms" :key="u.uom" :value="u.uom">{{ u.uom }}</option>
                    </select>
                    <span v-else class="px-2 text-slate-400" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ newPending.uom || '--' }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="newPending.rate" class="font-mono text-slate-300">{{ newPending.rate.toFixed(2) }}</span>
                    <span v-else class="text-slate-600">--</span>
                  </td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">0</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ isExempted ? 0 : defaultTaxRate }}</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.rate ? (newQty * newPending.rate).toFixed(2) : '--' }}</td>
                  <td class="border-slate-700"></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- BOTTOM PANEL -->
        <div class="flex flex-[4] border-t border-slate-700 bg-slate-900 overflow-hidden">

          <!-- Warehouse Stock Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:260px;max-width:320px;scrollbar-width:none">
            <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Warehouse Stock<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
            <table v-if="selectedItemData && selectedItemData.stock && selectedItemData.stock.length" class="w-full border-collapse text-[10px]" style="table-layout:fixed">
              <colgroup><col style="width:70%"><col style="width:30%"></colgroup>
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
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">List</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Rate</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="pl in selectedItemData.priceLists" :key="pl.name" class="hover:bg-slate-800/40">
                  <td class="px-1 py-0.5 text-slate-400 border border-slate-700 truncate max-w-[90px]" :title="pl.name">{{ pl.name }}</td>
                  <td class="px-1 py-0.5 text-right font-mono font-bold text-amber-400 border border-slate-700 text-base">&#8377;{{ encPrice(pl.rate || 0) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No price lists' : 'Select a row to see prices' }}</div>
          </div>

          <!-- Previous Purchases Panel -->
          <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:200px;max-width:240px;scrollbar-width:none">
            <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Previous Purchases<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
            <table v-if="selectedItemData && selectedItemData.previousPurchases && selectedItemData.previousPurchases.length" class="w-full border-collapse text-[10px]">
              <thead>
                <tr class="bg-slate-800">
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Invoice</th>
                  <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Date</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Rate</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Qty</th>
                  <th class="px-1 py-0.5 text-right font-semibold text-slate-500 border border-slate-700">Disc%</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in selectedItemData.previousPurchases" :key="p.name" class="hover:bg-slate-800/40">
                  <td class="px-1 py-0.5 font-medium text-blue-400 border border-slate-700 truncate max-w-[70px]" :title="p.name">{{ p.name }}</td>
                  <td class="px-1 py-0.5 text-slate-500 border border-slate-700 whitespace-nowrap">{{ p.date }}</td>
                  <td class="px-1 py-0.5 text-right font-mono font-bold text-slate-300 border border-slate-700">&#8377;{{ p.rate.toFixed(2) }}</td>
                  <td class="px-1 py-0.5 text-right font-mono text-slate-400 border border-slate-700">{{ p.qty }}</td>
                  <td class="px-1 py-0.5 text-right font-bold border border-slate-700" :class="p.discount > 0 ? 'text-red-400' : 'text-slate-600'">{{ p.discount > 0 ? p.discount + '%' : '—' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No previous purchases' : 'Select a row to see history' }}</div>
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
                <select v-model="priceList" :disabled="billDocStatus !== 0" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
                  <option v-for="pl in availablePriceLists" :key="pl" :value="pl">{{ pl }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-[9px] font-bold uppercase text-slate-600">Tax</label>
                <select v-model="taxTemplate" :disabled="billDocStatus !== 0" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-[10px] text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
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
            </div>
          </div>

          <!-- Bill Summary Table -->
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
                <td class="border border-slate-700 px-2" rowspan="11">
                  <div class="flex flex-col gap-2 h-full py-2">
                    <div class="text-[10px] text-slate-500">{{ activeItems.length }} item{{ activeItems.length !== 1 ? 's' : '' }}{{ deletedCount > 0 ? ' (' + deletedCount + ' deleted)' : '' }}</div>
                    <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Payable</div>
                    <div class="font-mono text-4xl font-bold text-blue-500 leading-none">&#8377;{{ grandTotal.toFixed(2) }}</div>
                    <div v-if="billSaved" class="flex items-center justify-between rounded bg-green-900/30 px-2 py-1 text-xs text-green-400">
                      <span class="font-bold">{{ savedInvoiceName }}</span>
                      <span class="font-semibold uppercase text-[10px]">Saved</span>
                    </div>
                    <button v-if="billSaved" @click="openBarcodePrinting" class="w-full rounded border border-orange-600/50 bg-orange-900/20 py-1.5 text-center text-xs font-bold text-orange-400 transition hover:bg-orange-900/30">🏷️ Print Barcodes</button>
                    <button v-if="billSaved && billDocStatus === 0" @click="submitBill" class="w-full rounded border border-green-600/50 bg-green-900/20 py-1.5 text-center text-xs font-semibold text-green-400 transition hover:bg-green-900/40">Submit Bill</button>
                    <button v-if="billSaved && billDocStatus === 0" @click="enterEditMode" class="w-full rounded border border-amber-600/50 bg-amber-900/20 py-1.5 text-center text-xs font-semibold text-amber-400 transition hover:bg-amber-900/30">✏ Edit Bill</button>
                    <button v-else-if="!billSaved" ref="saveButton" @click="saveBill" class="w-full rounded py-1.5 text-center text-xs font-semibold text-white transition shadow" :class="savedInvoiceName ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'">{{ savedInvoiceName ? 'Update Bill' : 'Save Bill (Ctrl+S)' }}</button>
                    <div class="flex gap-1">
                      <button class="flex-1 rounded border border-red-900/50 bg-red-900/10 py-1.5 text-center text-xs font-semibold text-red-400 hover:bg-red-900/20" @click="cancelBill">{{ billSaved ? 'New Bill' : 'Cancel' }}</button>
                    </div>
                    <button v-if="savedInvoiceName" @click="showIncentiveModal = true" class="w-full rounded border border-indigo-700/50 bg-indigo-900/20 py-1.5 text-center text-xs font-semibold text-indigo-400 hover:bg-indigo-900/40 transition">👥 Incentive</button>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Subtotal</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-200 text-2xl border border-slate-700">&#8377;{{ subtotal.toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Discount</td>
                <td class="p-0 border-y border-slate-700">
                  <div class="flex h-full">
                    <div class="flex flex-1 items-center border-r border-slate-700">
                      <input ref="discountInput" type="number" v-model.number="discountPct" :disabled="billDocStatus !== 0" min="0" max="100" step="0.5" class="w-full bg-transparent text-right font-mono text-slate-200 outline-none appearance-none disabled:cursor-not-allowed" style="padding:0 2px" @input="discountInputMode = 'pct'; discountDirectAmt = 0" @keydown.enter="saveButton?.focus()" />
                      <span class="shrink-0 px-1 text-slate-500 text-xs">%</span>
                    </div>
                    <div class="flex flex-1 items-center">
                      <span class="shrink-0 px-1 text-slate-500 text-xs">&#8377;</span>
                      <input type="number" v-model.number="discountDirectAmt" :disabled="billDocStatus !== 0" min="0" step="0.5" class="w-full bg-transparent text-right font-mono text-slate-200 outline-none appearance-none disabled:cursor-not-allowed" style="padding:0 2px" @input="discountInputMode = 'amt'; discountPct = 0" @keydown.enter="saveButton?.focus()" />
                    </div>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-&#8377;{{ discountAmt.toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Freight</td>
                <td class="p-0 border-y border-slate-700">
                  <div class="flex h-full items-center px-1">
                    <input type="number" v-model.number="freightAmt" :disabled="billDocStatus !== 0" min="0" step="0.5" class="w-full bg-transparent text-right font-mono text-slate-200 outline-none appearance-none disabled:cursor-not-allowed" style="width:100%;height:100%;display:block;padding:0 2px" />
                    <span class="shrink-0 px-1 text-slate-500 text-xs">&#8377;</span>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-slate-200 text-2xl border border-slate-700">&#8377;{{ (Number(freightAmt) || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Loading</td>
                <td class="p-0 border-y border-slate-700">
                  <div class="flex h-full items-center px-1">
                    <input type="number" v-model.number="loadingAmt" :disabled="billDocStatus !== 0" min="0" step="0.5" class="w-full bg-transparent text-right font-mono text-slate-200 outline-none appearance-none disabled:cursor-not-allowed" style="width:100%;height:100%;display:block;padding:0 2px" />
                    <span class="shrink-0 px-1 text-slate-500 text-xs">&#8377;</span>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-slate-200 text-2xl border border-slate-700">&#8377;{{ (Number(loadingAmt) || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Tax</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-200 text-2xl border border-slate-700">+&#8377;{{ totalTax.toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-amber-400/80 border border-slate-700">Tax Paid on Purchase</td>
                <td class="p-0 border-y border-slate-700">
                  <div class="flex h-full items-center px-1">
                    <input type="number" v-model.number="taxPaidAmt" :disabled="billDocStatus !== 0" min="0" step="0.01" class="w-full bg-transparent text-right font-mono text-slate-200 outline-none appearance-none disabled:cursor-not-allowed" style="width:100%;height:100%;display:block;padding:0 2px" />
                    <span class="shrink-0 px-1 text-slate-500 text-xs">&#8377;</span>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-amber-400 text-2xl border border-slate-700">&#8377;{{ (Number(taxPaidAmt) || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-200/80 font-bold border border-slate-700">Grand Total</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono font-bold text-blue-400 text-2xl border border-slate-700">&#8377;{{ grandTotal.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>

        </div>
      </div>
    </div>

    <!-- SHORTCUT REFERENCE -->
    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Purchase Entry"
      :extra="[
        { key: 'Page Up', desc: 'Focus series selector' },
        { key: 'Insert', desc: 'Open incentive entry' },
      ]"
      @close="showShortcutPage = false"
    />

    <!-- INCENTIVE ENTRY MODAL -->
    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Purchase Invoice"
      :docname="savedInvoiceName"
      @close="showIncentiveModal = false"
      @saved="showIncentiveModal = false"
    />

    <!-- SUPPLIER SEARCH MODAL -->
    <CustomerSearchModal
      ref="suppSearchModalRef"
      :show="showSupplierSearchModal"
      initial-type="Supplier"
      :allowed-types="isBiller ? ['Customer', 'Supplier', 'Employee'] : undefined"
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

    <!-- DISCARD BILL MODAL -->
    <div v-if="showDiscardModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="showDiscardModal = false">
      <div class="w-[450px] overflow-hidden rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl">
        <div class="bg-amber-900/20 px-6 py-6 flex items-center gap-4 border-b border-amber-900/30">
          <div class="flex h-12 w-12 items-center justify-center rounded-full bg-amber-900/40 text-2xl text-amber-500">⚠️</div>
          <div>
            <div class="text-xl font-bold text-slate-100">Discard Unsaved Bill?</div>
            <div class="text-sm text-amber-400">You have unsaved items in this bill.</div>
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

    <!-- PRINT OPTIONS MODAL -->
    <BarcodePrintingModal
      :show="showBarcodeModal"
      :bill-no="savedInvoiceName"
      :initial-items="barcodeInitialItems"
      @close="showBarcodeModal = false"
      @printed="showBarcodeModal = false"
    />

    <PrintOptionsModal
      v-if="showPrintModal"
      :invoice-name="printModalInvoiceName"
      :doctype="printModalDoctype"
      @close="showPrintModal = false"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice, searchItems, fetchItemDetails, frappeGet, frappePost } from '../api.js'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import { getUserRole } from '../composables/usePermission'
import ItemSearch from '../components/ItemSearch.vue'
import BarcodePrintingModal from '../components/BarcodePrintingModal.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import PriceListUpdate from './PriceListUpdate.vue'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import ShortcutPage from '../components/ShortcutPage.vue'
import { useItemCache } from '../services/itemCache.js'
import { session } from '../session.js'
import * as XLSX from 'xlsx'


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

if (props.isSubWindow) useSubwindow()

// ==================== PRINT MODAL ====================
const showPrintModal = ref(false)
const showIncentiveModal = ref(false)
const showShortcutPage = ref(false)
const showImportModal = ref(false)
const importOption = ref('Master')
const fileInput = ref(null)
const printModalInvoiceName = ref('')
const printModalDoctype = ref('Purchase Invoice')

function openPrintModal(name, doctype = 'Purchase Invoice') {
  printModalInvoiceName.value = name
  printModalDoctype.value = doctype
  showPrintModal.value = true
}

// ==================== IMPORT / EXPORT ====================
function openImportModal() { showImportModal.value = true }
function openFilePicker() { fileInput.value?.click() }

function exportItems() {
  const data = activeItems.value.map((i, idx) => ({
    '#': idx + 1,
    'Item Code': i.item_code,
    'Item Name': i.item_name,
    'Qty': i.qty,
    'UOM': i.uom,
    'Rate': i.rate,
    'Discount %': i.discount || 0,
    'Tax %': i.tax_rate || 0,
    'Amount': (i.qty * i.rate * (1 - (i.discount || 0) / 100)).toFixed(2)
  }))
  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Items')
  XLSX.writeFile(wb, `Purchase_Items_${new Date().toISOString().slice(0, 10)}.xlsx`)
}

async function handleImportFile(event) {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = async (e) => {
    const data = new Uint8Array(e.target.result)
    const workbook = XLSX.read(data, { type: 'array' })
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
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
        if (master) { rate = master.rate; discount = 0; itemName = master.item_name; uom = master.uom; taxRate = master.tax_rate ?? defaultTaxRate.value }
      }
      const existing = items.value.findIndex(i => i.item_code === itemCode && !i.deleted)
      if (existing >= 0) {
        items.value[existing].qty += qty
        if (importOption.value === 'File') { items.value[existing].rate = rate; items.value[existing].discount = discount }
      } else {
        items.value.push({ item_code: itemCode, item_name: itemName, uom, qty, rate, discount, tax_rate: taxRate, warehouse: defaultWarehouse.value, deleted: false })
      }
    }
    showImportModal.value = false
    event.target.value = ''
  }
  reader.readAsArrayBuffer(file)
}

// ==================== BILLING SETTINGS ====================
const billingSeriesConfig = ref([])
const cipherMap = ref([])
const defaultWarehouse = ref(localStorage.getItem('wb-warehouse') || '')
const defaultTaxRate = ref(0)
const priceList = ref('Standard Buying')
const taxTemplate = ref('')
const costCenter = ref(localStorage.getItem('wb-cost-center') || '')
const expenseAccount = ref('')

const availableTaxTemplates = ref([])
const availableWarehouses = ref([])
const availableCostCenters = ref([])

const availablePriceLists = computed(() => {
  return ['Standard Buying']
})

function getSeriesConfig(series) {
  return billingSeriesConfig.value.find(r => r.series === series) || null
}

function syncSeriesConfig(series) {
  const cfg = getSeriesConfig(series)
  if (!cfg) return
  if (cfg.price_list) priceList.value = cfg.price_list
  if (cfg.tax_template) taxTemplate.value = cfg.tax_template
  expenseAccount.value = cfg.expense_account || ''

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
const sidebarBillRefs = new Map()
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarBillRef(el, idx) { if (el) sidebarBillRefs.set(idx, el); else sidebarBillRefs.delete(idx) }
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const supplierInput = ref(null)
const billNoInput = ref(null)
const seriesSelect = ref(null)
const dateInput = ref(null)
const discountInput = ref(null)
const saveButton = ref(null)
const stayHereBtn = ref(null)
const suppSearchModalRef = ref(null)

const isBiller = getUserRole() === 'biller'

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
  nextTick(() => billNoInput.value?.focus())
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

const newPending = ref({ item_name: '', uom: '', uoms: [], rate: null })
const newUomSelect = ref(null)

function rateForUom(cached, uom) {
  // 1. Check for an actual Item Price record for this price list + UOM
  const plUomRates = cached.uom_price_lists?.[priceList.value]
  if (plUomRates && plUomRates[uom] != null) {
    return plUomRates[uom]
  }
  // 2. Fallback: base rate × conversion factor
  let baseRate = cached.price || cached.rate || 0
  if (cached.price_lists && priceList.value) {
    const pl = cached.price_lists.find(p => p.name === priceList.value)
    if (pl) baseRate = pl.rate
  }
  const uomEntry = (cached.uoms || []).find(u => u.uom === uom)
  return baseRate * (uomEntry ? uomEntry.conversion_factor : 1)
}

function onUomChange(idx) {
  const item = items.value[idx]
  const cached = lookupItemInCache(item.item_code) || {
    uoms: item.uoms || [],
    uom_price_lists: item.uom_price_lists || {},
    rate: item.rate
  }
  item.rate = rateForUom(cached, item.uom)
}

function onNewUomChange() {
  const cached = lookupItemInCache(newItemCode.value.trim()) || {
    uoms: newPending.value.uoms || [],
    uom_price_lists: newPending.value.uom_price_lists || {},
    rate: newPending.value.rate
  }
  newPending.value.rate = rateForUom(cached, newPending.value.uom)
}

async function lookupItem(code) {
  // 1. Try local cache first
  const cached = lookupItemInCache(code)
  if (cached) {
    const finalRate = rateForUom(cached, cached.uom)
    return {
      found: true,
      item_code: cached.item_code,
      item_name: cached.item_name,
      uom: cached.uom,
      uoms: cached.uoms || [],
      uom_price_lists: cached.uom_price_lists || {},
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
  if (code.length < 2) { newPending.value = { item_name: '', uom: '', uoms: [], rate: null }; return }
  lookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    newPending.value = r ? { item_name: r.item_name, uom: r.uom, uoms: r.uoms || [], uom_price_lists: r.uom_price_lists || {}, rate: r.rate } : { item_name: '', uom: '', uoms: [], rate: null }
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
    items.value[idx].item_name = r.item_name; items.value[idx].uom = r.uom; items.value[idx].uoms = r.uoms || []; items.value[idx].uom_price_lists = r.uom_price_lists || {}; items.value[idx].rate = r.rate; items.value[idx].tax_rate = r.tax_rate ?? defaultTaxRate.value; items.value[idx].warehouse = r.warehouse; items.value[idx].deleted = false;
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
  if (r) {
    newPending.value = { item_name: r.item_name, uom: r.uom, uoms: r.uoms || [], uom_price_lists: r.uom_price_lists || {}, rate: r.rate }
    focusNewQty()
  }
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
      uoms: r.uoms || [],
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
  newPending.value = { item_name: '', uom: '', uoms: [], rate: null }; 
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
  let finalUoms = item.uoms || []
  let finalUomPriceLists = item.uom_price_lists || {}
  
  try {
    const r = await lookupItem(item.item_code)
    if (r) {
      finalRate = r.rate
      finalTax = r.tax_rate ?? defaultTaxRate.value
      finalWh = r.warehouse || defaultWarehouse.value
      finalName = r.item_name
      finalUom = r.uom
      finalUoms = r.uoms || []
      finalUomPriceLists = r.uom_price_lists || {}
    }
  } catch (e) {}

  if (itemSearchTargetRow !== null) {
    const row = items.value[itemSearchTargetRow]
    row.item_code = item.item_code
    row.item_name = finalName
    row.uom = finalUom
    row.uoms = finalUoms
    row.uom_price_lists = finalUomPriceLists
    row.rate = finalRate
    row.tax_rate = finalTax
    row.warehouse = finalWh
    row.deleted = false
    selectedRow.value = itemSearchTargetRow
    focusField('qty', itemSearchTargetRow)
  } else {
    newItemCode.value = item.item_code
    newPending.value = { item_name: finalName, uom: finalUom, uoms: finalUoms, uom_price_lists: finalUomPriceLists, rate: finalRate, tax_rate: finalTax, warehouse: finalWh }
    nextTick(() => focusNewQty())
  }
}

// ==================== SIDEBAR MODIFY PANEL ====================
const sidebarDate = ref(getTodayIST())
const sidebarSearch = ref('')
const showSubmitted = ref(false)
const sidebarBills = ref([])
const sidebarLoading = ref(false)

async function fetchSidebarBills() {
  sidebarLoading.value = true
  try {
    sidebarBills.value = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoices', {
      query: sidebarSearch.value,
      limit: 50,
      posting_date: sidebarDate.value,
      show_submitted: showSubmitted.value,
    })
  } catch (e) {
    sidebarBills.value = []
  }
  sidebarLoading.value = false
}

function changeSidebarDate(days) {
  const d = new Date(sidebarDate.value)
  d.setDate(d.getDate() + days)
  sidebarDate.value = d.toISOString().split('T')[0]
}

watch([sidebarDate, showSubmitted], fetchSidebarBills)

let sidebarSearchTimeout = null
watch(sidebarSearch, () => {
  clearTimeout(sidebarSearchTimeout)
  sidebarSearchTimeout = setTimeout(fetchSidebarBills, 500)
})

async function loadInvoice(invoiceName) {
  try {
    const inv = await frappeGet('ssplbilling.api.purchase_api.get_purchase_invoice', { invoice_name: invoiceName })
    if (!inv) { alert('Could not load invoice'); return }

    supplier.value = inv.supplier
    suppSearch.value = inv.supplier_name
    billNo.value = inv.bill_no || ''
    billDate.value = inv.posting_date
    if (inv.naming_series && availableSeries.value.includes(inv.naming_series)) {
      billSeries.value = inv.naming_series
    }
    discountPct.value = inv.discount_percentage || 0
    if (inv.tax_template) taxTemplate.value = inv.tax_template
    if (inv.cost_center) costCenter.value = inv.cost_center
    items.value = inv.items.map(i => ({
      ...i,
      rate: i.price_list_rate || i.rate,
      discount: i.discount || 0,
      tax_rate: i.tax_rate ?? defaultTaxRate.value,
    }))
    selectedRow.value = -1
    newItemCode.value = ''
    newQty.value = 1
    newPending.value = { item_name: '', uom: '', uoms: [], rate: null }
    selectedItemData.value = null

    savedInvoiceName.value = inv.name
    billDocStatus.value = inv.docstatus
    billSaved.value = inv.docstatus !== 0

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
const billNo = ref('')
const supplier = ref('')
const billSeries = ref('')

// ==================== BARCODE MODAL ====================
const showBarcodeModal = ref(false)
const barcodeInitialItems = ref([])

function openBarcodePrinting() {
  const items = activeItems.value.map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    qty: i.qty,
    rate: i.rate || 0,
  }))
  router.push({
    path: '/barcode-print',
    query: {
      bill: savedInvoiceName.value || undefined,
      items: encodeURIComponent(JSON.stringify(items)),
    },
  })
}

async function loadAndPrintBarcodes(invoiceName) {
  await loadInvoice(invoiceName)
  nextTick(() => openBarcodePrinting())
}


const discountPct = ref(0)
const discountDirectAmt = ref(0)
const discountInputMode = ref(null) // 'pct' | 'amt'
const freightAmt = ref(0)
const loadingAmt = ref(0)
const taxPaidAmt = ref(0)
const taxPaidAccount = ref('')
const availableSeries = ref([])
const nextBillNo = ref('...')

watch(billSeries, () => {
  fetchNextBillNo()
})

async function fetchSeriesList() {
  try {
    const settings = await fetchBillingSettings()
    if (!localStorage.getItem('wb-warehouse')) {
      if (settings.default_warehouse) defaultWarehouse.value = settings.default_warehouse
    }
    if (settings.tax_paid_on_purchase) taxPaidAccount.value = settings.tax_paid_on_purchase

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

const discountAmt = computed(() => {
  if (discountInputMode.value === 'amt') return Number(discountDirectAmt.value) || 0
  return subtotal.value * ((Number(discountPct.value) || 0) / 100)
})
const taxableAmt = computed(() => subtotal.value - discountAmt.value)

const totalTax = computed(() => {
  if (isExempted.value) return 0
  if (isInclusive.value) {
    return (grossTotal.value - subtotal.value) * (1 - (Number(discountPct.value) || 0) / 100)
  }
  return activeItems.value.reduce((s, i) => {
    const a = i.qty * i.rate * (1 - (i.discount || 0) / 100)
    return s + (a - a * ((Number(discountPct.value) || 0) / 100)) * (i.tax_rate / 100)
  }, 0)
})

const grandTotal = computed(() => {
  const charges = (Number(freightAmt.value) || 0) + (Number(loadingAmt.value) || 0)
  if (isInclusive.value) return grossTotal.value * (1 - (Number(discountPct.value) || 0) / 100) + charges
  return taxableAmt.value + totalTax.value + charges
})

async function saveBill() {
  if (!supplier.value.trim()) { alert('Please enter a supplier'); return }
  if (!activeItems.value.length) { alert('Add at least one item'); return }

  const payload = {
    supplier: supplier.value,
    bill_no: billNo.value,
    date: billDate.value,
    naming_series: billSeries.value,
    discount_percentage: discountInputMode.value === 'amt' ? 0 : (discountPct.value || 0),
    additional_discount_amount: discountInputMode.value === 'amt' ? (discountDirectAmt.value || 0) : 0,
    tax_template: taxTemplate.value || '',
    cost_center: costCenter.value || '',
    taxes: [
      ...(freightAmt.value > 0 ? [{ charge_type: 'Actual', account_head: '', description: 'Freight Charges', tax_amount: freightAmt.value }] : []),
      ...(loadingAmt.value > 0 ? [{ charge_type: 'Actual', account_head: '', description: 'Loading Charges', tax_amount: loadingAmt.value }] : []),
      ...(taxPaidAmt.value > 0 ? [{ charge_type: 'Actual', account_head: taxPaidAccount.value || '', description: 'Tax Paid on Purchase', tax_amount: taxPaidAmt.value }] : []),
    ],
    items: activeItems.value.map(i => ({
      item_code: i.item_code,
      qty: i.qty,
      price_list_rate: i.rate,
      discount_percentage: i.discount || 0,
      rate: i.rate * (1 - (i.discount || 0) / 100),
      warehouse: i.warehouse || defaultWarehouse.value,
      cost_center: costCenter.value || '',
      expense_account: expenseAccount.value || '',
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
    fetchSidebarBills()
  } catch (e) {
    alert('Error: ' + (e?.message || 'Failed to save invoice'))
  }
}

async function submitBill() {
  if (!savedInvoiceName.value || billDocStatus.value !== 0) return
  if (!confirm(`Submit invoice ${savedInvoiceName.value}? This cannot be undone.`)) return
  try {
    await apiPost('submit_purchase_invoice', { invoice_name: savedInvoiceName.value })
    billDocStatus.value = 1
  } catch (e) {
    alert('Submit failed: ' + (e?.message || 'Unknown error'))
  }
}

function startNewBill() {
  items.value = []; selectedRow.value = -1; supplier.value = ''; suppSearch.value = ''; billNo.value = ''
  discountPct.value = 0; discountDirectAmt.value = 0; discountInputMode.value = null; freightAmt.value = 0; loadingAmt.value = 0; taxPaidAmt.value = 0; newItemCode.value = ''; newQty.value = 1;
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

import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { purchaseEntryShortcuts } from '../shortcuts/purchaseEntryShortcuts'

useShortcuts(purchaseEntryShortcuts({
  openShortcuts: () => { showShortcutPage.value = !showShortcutPage.value },
  save: () => saveBill(),
  newCustomer: () => openSupplierSearch(),
  searchItem: () => openSearch('', null),
  deleteRow: () => {
    if (selectedRow.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      softDelete(selectedRow.value)
    }
  },
  focusSeries: () => seriesSelect.value?.focus(),
  openIncentive: () => { if (savedInvoiceName.value) showIncentiveModal.value = true },
  toggleDiscountSave: () => {
    const activeEl = document.activeElement

    // 1. If in existing items table
    if (selectedRow.value !== -1) {
      const rowIdx = selectedRow.value
      const lastFieldInRow = inputRefs[`discount-${rowIdx}`]
      
      if (activeEl !== lastFieldInRow) {
        // Go to end of current row
        focusField('discount', rowIdx)
      } else {
        // Already at end of current row, jump to last row (New Entry row)
        selectedRow.value = -1
        focusNewCode()
      }
      return
    }

    // 2. If in new entry row (the "last row")
    if (activeEl === newCodeInput.value || activeEl === newQtyInput.value) {
      if (activeEl === newCodeInput.value) {
        newQtyInput.value?.focus()
        newQtyInput.value?.select()
      } else {
        // At end of last row, go to global discount
        discountInput.value?.focus()
        discountInput.value?.select()
      }
      return
    }

    // 3. Global summary inputs
    if (activeEl === discountInput.value) {
      saveBill()
    } else {
      // 4. From anywhere else, jump to last row (New Entry row)
      selectedRow.value = -1
      focusNewCode()
    }
  },
  contextualBack: () => {
    if (showJumpModal.value) { showJumpModal.value = false; return }
    if (showDiscardModal.value) { showDiscardModal.value = false; return }
    if (showPriceListUpdate.value) { showPriceListUpdate.value = false; return }
    if (showSupplierSearchModal.value) { closeSupplierSearchModal(); return }
    if (showItemSearchModal.value) { closeItemSearch(); return }
    if (showPrintModal.value) { showPrintModal.value = false; startNewBill(); return }
    if (showImportModal.value) { showImportModal.value = false; return }
    // First Esc: clear active bill; Second Esc (bill already empty): exit
    const hasBillContent = activeItems.value.length > 0 || supplier.value || savedInvoiceName.value
    if (hasBillContent) { startNewBill(); return }
    handleBack()
  }
}), props.isSubWindow ? 'subwindow' : 'local')

function handleStorageChange(e) {
  if (e.key === 'wb-zoom') zoomPercent.value = parseInt(e.newValue) || 150
  if (e.key === 'wb-warehouse') defaultWarehouse.value = e.newValue || ''
  if (e.key === 'wb-cost-center') costCenter.value = e.newValue || ''
}

onMounted(() => {
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('storage', handleStorageChange);
  fetchSeriesList()
  fetchDropdownOptions()
  fetchSidebarBills()

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
  window.removeEventListener('storage', handleStorageChange);
})
</script>

<style scoped>
input[type='number']::-webkit-inner-spin-button,
input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type='number'] {
  -moz-appearance: textfield;
}
</style>
