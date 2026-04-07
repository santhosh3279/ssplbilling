<template>
  <div :class="isSubWindow ? 'fixed inset-0 z-[100] bg-slate-900' : 'h-screen bg-slate-900'" class="flex overflow-hidden">
    <Item_Invoice_Template :show-back-button="true" title="Sales Entry">

      <!-- ═══════════════════ SIDEBAR ═══════════════════ -->
      <template #sidebar>
    <aside class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-slate-500">Modify Bills</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-slate-700 p-0 bg-slate-900">
          <button @click="changeSidebarDate(-1)" class="rounded p-2 text-xl text-slate-500 hover:bg-slate-800 hover:text-slate-300">&larr;</button>
          <input 
            type="date" 
            v-model="sidebarDate"
            class="w-full bg-transparent text-xl font-bold text-slate-300 outline-none"
          />
          <button @click="changeSidebarDate(1)" class="rounded p-2 text-xl text-slate-500 hover:bg-slate-800 hover:text-slate-300">&rarr;</button>
        </div>

        <!-- Search & Series Filters -->
        <div class="flex flex-col gap-2 border-b border-slate-700 p-3 bg-slate-800/20">
          <input 
            type="text" 
            v-model="sidebarSearch"
            placeholder="Search invoice/cust..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-[1px] text-2xl text-slate-300 outline-none focus:border-blue-500"
          />
          <select
            ref="sidebarSeriesSelect"
            v-model="sidebarSeries"
            class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-[1px] text-2xl text-slate-300 outline-none focus:border-blue-500"
            @keydown.enter.prevent="focusFirstSidebarBill"
          >
            <option value="">All Series</option>
            <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
          </select>
          <button
            @click="draftOnly = !draftOnly"
            class="w-full rounded border py-[1px] text-xl font-bold uppercase transition-colors"
            :class="draftOnly ? 'bg-amber-900/40 border-amber-500 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Bills' }}
          </button>
        </div>

        <!-- Bill List -->
        <div class="flex-1 overflow-y-auto scrollbar-none">
          <div v-if="sidebarLoading" class="p-4 text-center text-lg text-slate-500">Loading...</div>
          <div v-else-if="!sidebarBills.length" class="p-4 text-center text-lg text-slate-600 italic">No bills found</div>
          <div 
            v-for="(inv, idx) in sidebarBills" 
            :key="inv.name"
            :ref="el => setSidebarBillRef(el, idx)"
            @click="loadInvoice(inv.name)"
            class="group cursor-pointer border-b border-slate-800 px-2 py-1 transition-colors outline-none focus:ring-1 focus:ring-blue-500"
            :class="savedInvoiceName === inv.name || sidebarFocusedIdx === idx ? 'border-l-2 border-l-blue-500' : 'bg-slate-900 hover:bg-slate-800'"
            :style="savedInvoiceName === inv.name || sidebarFocusedIdx === idx ? { backgroundColor: '#B0E4CC !important', opacity: '1 !important' } : {}"
            tabindex="0"
            @focus="sidebarFocusedIdx = idx"
            @blur="sidebarFocusedIdx = -1"
            @keydown.enter="loadInvoice(inv.name)"
            @keydown.up.prevent="navigateSidebarBill(idx, -1)"
            @keydown.down.prevent="navigateSidebarBill(idx, 1)"
          >
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-1.5 truncate min-w-0">
                <span class="h-2 w-2 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-green-500' : 'bg-red-500'"></span>
                <span class="truncate font-mono text-2xl" :class="savedInvoiceName === inv.name || sidebarFocusedIdx === idx ? 'text-black font-bold' : 'text-blue-400'">{{ inv.name }}</span>
              </div>
              <span class="shrink-0 font-mono font-normal text-4xl tabular-nums" :class="savedInvoiceName === inv.name || sidebarFocusedIdx === idx ? 'text-black' : 'text-slate-200'">{{ inv.grand_total.toFixed(0) }}</span>
            </div>
            <div class="truncate text-2xl" :class="savedInvoiceName === inv.name || sidebarFocusedIdx === idx ? 'text-black font-medium' : 'text-slate-400'">
              {{ inv.custom_customer_name || inv.customer_name }}
              <span v-if="inv.custom_customer_name" class="ml-1 text-lg font-normal opacity-60">({{ inv.customer_name }})</span>
            </div>
          </div>
        </div>
      </aside>
      </template>

      <!-- ═══════════════════ HEADER RIGHT (zoom + shortcuts) ═══════════════════ -->
      <template #header-right>
          <div class="flex items-center gap-3 text-[10px] text-slate-400">
            <div class="flex items-center rounded border border-slate-700 bg-slate-800 shadow-sm overflow-hidden">
              <button @click="zoomPercent = Math.max(10, zoomPercent - 10)" class="flex h-5 w-6 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&minus;</button>
              <div class="flex items-center border-x border-slate-700 bg-slate-900 px-2 gap-1">
                <span class="text-[9px] font-bold uppercase text-slate-500">Zoom</span>
                <span class="text-[10px] text-slate-300">{{ zoomPercent }}%</span>
              </div>
              <button @click="zoomPercent = Math.min(500, zoomPercent + 10)" class="flex h-5 w-6 items-center justify-center font-bold text-slate-400 hover:bg-slate-700">&plus;</button>
            </div>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Up/Down</kbd> Nav</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Tab</kbd> Col</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F4</kbd> Series</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Ins</kbd> Incentive</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Ctrl+S</kbd> Save</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F2</kbd> New Bill</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">F5</kbd> Print</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Ctrl+M</kbd> Modify</span>
            <span><kbd class="rounded border border-slate-600 bg-slate-700 px-1 py-0.5 font-mono text-[9px] text-slate-300">Esc</kbd> Back</span>
            <div class="h-3 w-px bg-slate-700"></div>
            <div class="flex items-center gap-1 font-bold text-blue-400">
              <span class="text-[9px] text-slate-500 font-medium">HI</span>
              <span class="truncate max-w-[100px] uppercase tracking-wide text-[10px]">{{ (session.fullName.value || 'User').split('@')[0] }}</span>
            </div>
          </div>
      </template>

      <!-- ═══════════════════ HEADER BAR (bill no / customer / date) ═══════════════════ -->
      <template #header-bar>
      <div class="flex items-center gap-6">
        <!-- Bill No -->
        <div class="flex items-center gap-2 border-l border-slate-700 pl-6">
          <label class="text-[10px] uppercase text-slate-500 whitespace-nowrap">Bill No</label>
          <div class="text-xl text-slate-100 tabular-nums">
            {{ nextBillNo }}
          </div>
        </div>

        <!-- Customer Section (Flex-1 to take middle space) -->
        <div class="flex-1 flex flex-col border-l border-slate-700 pl-6 overflow-hidden cursor-pointer hover:bg-slate-800/40 transition-colors group" @click="openCustomerSearch">
          <!-- Line 1: Name, Mobile, GST, Balance, and Stats -->
          <div class="flex items-center gap-6">
            <div class="flex items-baseline gap-2 min-w-0">
              <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap group-hover:text-blue-400 transition-colors">Customer</label>
              <div
                ref="customerInput"
                class="shrink-0 max-w-[400px] truncate text-4xl transition-colors outline-none leading-none font-semibold"
                :class="customer ? 'text-slate-100' : 'text-slate-600 italic'"
                tabindex="0"
                @keydown.enter.prevent.stop="openCustomerSearch"
                @keydown.space.prevent.stop="openCustomerSearch"
              >
                {{ custSearch || 'Not Selected' }}
              </div>
            </div>

            <div v-if="selectedCustomerDetails?.mobile_no" class="flex items-center gap-1 text-blue-400 font-mono text-2xl whitespace-nowrap">
              <span class="text-[10px] uppercase text-slate-500">Mob:</span>
              {{ selectedCustomerDetails.mobile_no }}
            </div>

            <div v-if="selectedCustomerDetails?.gstin" class="flex items-center gap-1 text-slate-400 font-mono text-xl whitespace-nowrap">
              <span class="text-[10px] uppercase text-slate-500">GST:</span>
              {{ selectedCustomerDetails.gstin }}
            </div>

            <div v-if="selectedCustomerDetails?.balance !== undefined" class="flex items-center gap-2 whitespace-nowrap">
              <span class="text-[10px] font-bold uppercase text-slate-500">Balance</span>
              <span 
                class="text-2xl font-bold font-mono"
                :class="(selectedCustomerDetails.balance > 0) ? 'text-green-400' : (selectedCustomerDetails.balance < 0) ? 'text-red-400' : 'text-slate-500'"
              >
                ₹ {{ Math.abs(selectedCustomerDetails.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                <span class="text-[10px]">{{ (selectedCustomerDetails.balance > 0) ? 'DR' : (selectedCustomerDetails.balance < 0) ? 'CR' : '' }}</span>
              </span>
            </div>

            <div v-if="selectedCustomerDetails?.last_invoice_date" class="flex items-center gap-2 whitespace-nowrap">
              <span class="text-[10px] font-bold uppercase text-slate-500">Last Inv</span>
              <span class="text-2xl font-mono text-blue-400">
                {{ new Date(selectedCustomerDetails.last_invoice_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) }}
              </span>
            </div>

            <!-- Custom name badge -->
            <div v-if="customAddress.custom_customer_name" class="flex items-center gap-1.5 rounded-full bg-amber-500/20 border border-amber-500/40 px-2.5 py-0.5 leading-none shrink-0">
              <span class="text-[9px] font-bold uppercase text-amber-500">Custom</span>
              <span class="text-lg font-semibold text-amber-300 max-w-[220px] truncate">{{ customAddress.custom_customer_name }}</span>
            </div>
          </div>
        </div>

        <!-- Bill Date -->
        <div class="flex items-center gap-3 border-l border-slate-700 pl-6 whitespace-nowrap">
          <label class="text-[10px] font-bold uppercase text-slate-500">Bill Date</label>
          <div class="flex items-center gap-1 bg-slate-900 rounded border border-slate-600 px-1 py-0.5">
            <button 
              @click="changeBillDate(-1)" 
              :disabled="billDocStatus !== 0 || billSaved"
              class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              &larr;
            </button>
            <span class="text-xl text-slate-100 tabular-nums px-2 min-w-[120px] text-center cursor-default select-none">
              {{ new Date(billDate).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) }}
            </span>
            <button 
              @click="changeBillDate(1)" 
              :disabled="billDocStatus !== 0 || billSaved"
              class="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              &rarr;
            </button>
            <!-- Hidden input to maintain dateInput ref if needed by other logic -->
            <input ref="dateInput" v-model="billDate" type="date" class="hidden" />
          </div>
        </div>
      </div>
    </template>

      <!-- ═══════════════════ ITEM ROWS (scoped slot) ═══════════════════ -->
      <template #row="{ item, index: idx }">
                <tr :ref="el => setRowRef(el, idx)" tabindex="-1" class="cursor-pointer border-b border-slate-700 outline-none transition-colors" :class="{ 'bg-[#B0E4CC] border-l-2 border-l-blue-500 text-black': selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing, 'bg-green-900/30 border-l-2 border-l-green-400': item._is_free && !item.deleted, 'bg-green-900/20 border-l-2 border-l-green-600': !item._is_free && item._rule_discount != null && !item.deleted, 'bg-purple-900/20 border-l-2 border-l-purple-500': !item._is_free && item._rule_discount == null && item._customer_pricing && !item.deleted, 'bg-red-900/10': item.deleted, 'hover:bg-slate-800/50': !item.deleted && !item._is_free && item._rule_discount == null && !item._customer_pricing && selectedRow !== idx }" :style="{ fontSize: dynamicRowStyle.fontSize, outline: (item.discount > 0 && !item.deleted && selectedRow !== idx) ? '2px solid rgba(64, 138, 113, 0.6)' : (isRateDifferent(item) && !item.deleted && selectedRow !== idx) ? '2px solid rgba(59, 130, 246, 0.6)' : undefined, outlineOffset: '-2px' }" @click="selectRow(idx)" @keydown="onRowKeydown($event, idx)">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full" :class="item.deleted ? 'bg-red-900/30 text-red-400' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-slate-700 text-[#B0E4CC]' : 'bg-slate-800 text-slate-400')" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">{{ idx + 1 }}</span></td>
                  <td class="p-0 border-r border-slate-700">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'code', idx)" v-model="item.item_code" :disabled="billDocStatus !== 0 || billSaved || item._is_free" class="w-full rounded border border-slate-600 font-mono outline-none focus:border-blue-500 disabled:bg-slate-900" :class="selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-[#B0E4CC] text-black' : 'bg-slate-800 text-slate-200'" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @focus="onCodeFocus(idx)" @input="onCodeInput(idx)" @keydown.tab.prevent="focusField('qty', idx)" @keydown.right.prevent="openSearch(item.item_code, idx)" @keydown.enter.prevent="onCodeEnter(idx)" @keydown="handleQuickSearchKeydown($event, idx)" />
                    <span v-else class="font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-400')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_code }}</span>
                  </td>
                  <td class="px-2 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span :class="item.deleted ? 'text-red-900/50 line-through' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-200')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.item_name || '--' }}</span><span v-if="item._is_free" class="ml-1 rounded bg-green-900/60 px-1 py-0.5 font-bold text-green-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">FREE</span><span v-else-if="item.deleted" class="ml-1 font-semibold text-red-500" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">DELETED</span></td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'qty', idx)" type="number" v-model.number="item.qty" :disabled="billDocStatus !== 0 || billSaved || item._is_free" min="0" class="w-full rounded border border-transparent text-right font-mono focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed appearance-none" :class="selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-[#B0E4CC] text-black focus:bg-[#B0E4CC]' : 'bg-transparent text-slate-200 focus:bg-slate-800'" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="item.qty !== 0 && ((item.uoms||[]).length > 1 ? focusField('uom', idx) : focusField('rate', idx))" @keydown.tab.prevent="(item.uoms||[]).length > 1 ? focusField('uom', idx) : focusField('rate', idx)" @keydown.shift.tab.prevent="focusField('code', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-300')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ isReturn ? -item.qty : item.qty }}</span>
                  </td>
                  <td class="p-0 border-r border-slate-700">
                    <select v-if="selectedRow === idx && !item.deleted && (item.uoms || []).length > 1" :ref="el => setRef(el, 'uom', idx)" v-model="item.uom" :disabled="billDocStatus !== 0 || billSaved" class="w-full rounded border border-transparent font-mono outline-none focus:border-blue-500 disabled:cursor-not-allowed appearance-none" :class="selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-[#B0E4CC] text-black focus:bg-[#B0E4CC]' : 'bg-transparent text-slate-200 focus:bg-slate-800'" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @change="onUomChange(idx)" @keydown.enter.prevent="focusField('rate', idx)" @keydown.tab.prevent="focusField('rate', idx)" @keydown.shift.tab.prevent="focusField('qty', idx)" @keydown.up.stop @keydown.down.stop>
                      <option v-for="u in item.uoms" :key="u.uom" :value="u.uom">{{ u.uom }}</option>
                    </select>
                    <span v-else class="px-2 font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-400')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.uom || '--' }}</span>
                  </td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'rate', idx)" type="number" v-model.number="item.rate" :disabled="billDocStatus !== 0 || billSaved || item._is_free" step="0.01" class="w-full rounded border border-transparent text-right font-mono focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed appearance-none" :class="selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-[#B0E4CC] text-black focus:bg-[#B0E4CC]' : 'bg-transparent text-slate-200 focus:bg-slate-800'" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @focus="onRateFocus(idx)" @blur="onRateBlur(idx)" @keydown.enter.prevent="focusField('discount', idx)" @keydown.tab.prevent="focusField('discount', idx)" @keydown.shift.tab.prevent="(item.uoms||[]).length > 1 ? focusField('uom', idx) : focusField('qty', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-300')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.rate.toFixed(2) }}</span>
                  </td>
                  <td class="px-2 py-0 border-r border-slate-700 text-right">
                    <input v-if="selectedRow === idx && !item.deleted" :ref="el => setRef(el, 'discount', idx)" type="number" v-model.number="item.discount" :disabled="billDocStatus !== 0 || billSaved || item._is_free" step="0.5" min="0" max="100" class="w-full rounded border border-transparent text-right font-mono focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed appearance-none" :class="selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'bg-[#B0E4CC] text-black focus:bg-[#B0E4CC]' : 'bg-transparent text-slate-200 focus:bg-slate-800'" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @focus="onDiscountFocus(idx)" @blur="onDiscountBlur(idx)" @keydown.enter.prevent="goToNextRow(idx)" @keydown.tab.prevent="goToNextRow(idx)" @keydown.shift.tab.prevent="focusField('rate', idx)" @keydown.down.prevent="moveRow(idx, 1)" @keydown.up.prevent="moveRow(idx, -1)" />
                    <span v-else class="block text-right font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-300')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ item.discount || 0 }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : (item.discount ? 'text-amber-400' : 'text-slate-600'))" :style="{ fontSize: dynamicRowStyle.fontSize }">
                      {{ item.discount ? (item.rate * (1 - (item.discount) / 100)).toFixed(2) : '—' }}
                    </span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span class="font-mono" :class="item.deleted ? 'text-slate-600' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black' : 'text-slate-400')" :style="{ fontSize: dynamicRowStyle.fontSize }">{{ isExempted ? 0 : (item.tax_rate != null ? item.tax_rate : defaultTaxRate) }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700 font-mono" :class="item.deleted ? 'text-slate-600 line-through' : (selectedRow === idx && !item.deleted && !item._is_free && !item._rule_discount && !item._customer_pricing ? 'text-black font-bold' : 'text-slate-200')" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ item.deleted ? '' : ((isReturn ? -1 : 1) * item.qty * item.rate * (1 - (item.discount || 0) / 100)).toFixed(2) }}</td>
                  <td class="px-2 text-center" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <button v-if="!item.deleted && !item._is_free" class="rounded px-1 py-0.5 text-slate-600 hover:bg-red-900/30 hover:text-red-400" :style="{ fontSize: dynamicRowStyle.fontSize }" @click.stop="softDelete(idx)">&times;</button>
                    <button v-else-if="item.deleted" class="rounded px-1 py-0.5 font-semibold text-blue-500 hover:bg-blue-900/30 hover:text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }" @click.stop="restoreItem(idx)">&larr;</button>
                  </td>
                </tr>
      </template>

      <!-- ═══════════════════ NEW ENTRY ROW ═══════════════════ -->
      <template #table-extra-rows>
                <tr v-if="billDocStatus === 0 && !billSaved" class="border-b border-slate-700" :class="selectedRow === -1 ? 'bg-blue-900/20' : 'bg-slate-800/30'" :style="{ fontSize: dynamicRowStyle.fontSize }">
                  <td class="px-3 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-900/50 text-blue-400" :style="{ fontSize: `${(8 * zoomPercent) / 100}px` }">+</span></td>
                  <td class="p-0 border-r border-slate-700"><input ref="newCodeInput" v-model="newItemCode" class="w-full rounded border border-slate-600 bg-slate-800 py-1 text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-900/50" style="padding-left:0;padding-right:0;" :style="{ fontSize: dynamicRowStyle.fontSize }" placeholder="Barcode" @input="onNewCodeInput" @keydown.tab.prevent="focusNewQty" @keydown.right.prevent="openSearch(newItemCode, null)" @keydown="handleQuickSearchKeydown($event)" /></td>
                  <td class="px-2 text-slate-400 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.item_name || '--' }}</td>
                  <td class="px-0 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }"><input ref="newQtyInput" v-model.number="newQty" type="number" min="0" class="w-full rounded border border-slate-600 bg-slate-800 text-right font-mono text-slate-200 outline-none focus:border-blue-500 appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @keydown.enter.prevent="newQty !== 0 && ((newPending.uoms||[]).length > 1 ? $nextTick(() => newUomSelect?.focus()) : addNewItem())" @keydown.shift.tab.prevent="focusNewCode" /></td>                  <td class="p-0 border-r border-slate-700">
                    <select v-if="(newPending.uoms || []).length > 1" ref="newUomSelect" v-model="newPending.uom" class="w-full rounded border border-slate-600 bg-slate-800 font-mono text-slate-200 outline-none focus:border-blue-500 appearance-none" style="padding:0" :style="{ fontSize: dynamicRowStyle.fontSize }" @change="onNewUomChange" @keydown.enter.prevent="addNewItem" @keydown.tab.prevent="addNewItem" @keydown.shift.tab.prevent="focusNewQty">
                      <option v-for="u in newPending.uoms" :key="u.uom" :value="u.uom">{{ u.uom }}</option>
                    </select>
                    <span v-else class="px-2 text-slate-400" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom, fontSize: dynamicRowStyle.fontSize }">{{ newPending.uom || '--' }}</span>
                  </td>
                  <td class="px-2 text-right border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">
                    <span v-if="newPending.rate" class="font-mono text-slate-300">{{ newPending.rate.toFixed(2) }}</span>
                    <span v-else class="text-slate-600">--</span>
                  </td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">0</td>
                  <td class="px-2 text-right font-mono text-slate-600 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">—</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ isExempted ? 0 : defaultTaxRate }}</td>
                  <td class="px-2 text-right font-mono text-slate-500 border-r border-slate-700" :style="{ paddingTop: dynamicRowStyle.paddingTop, paddingBottom: dynamicRowStyle.paddingBottom }">{{ newPending.rate ? ((isReturn ? -1 : 1) * newQty * newPending.rate).toFixed(2) : '--' }}</td>
                  <td class="border-slate-700"></td>
                </tr>
      </template>

      <!-- ═══════════════════ BOTTOM LEFT (insights) ═══════════════════ -->
      <template #bottom-left>
            <!-- 1. Previous Sales row -->
            <div class="flex flex-col border-b border-slate-700">
              <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Previous Sales<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
              <div class="overflow-y-auto scrollbar-none max-h-[110px]">
                <table v-if="selectedItemData && selectedItemData.previousPurchases && selectedItemData.previousPurchases.length" class="w-full border-collapse text-[10px]">
                  <thead>
                    <tr class="bg-slate-800 sticky top-0 z-10">
                      <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Invoice</th>
                      <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Date</th>
                      <th class="px-1 py-0.5 text-right font-medium text-slate-500 border border-slate-700">Rate</th>
                      <th class="px-1 py-0.5 text-right font-medium text-slate-500 border border-slate-700">Qty</th>
                      <th class="px-1 py-0.5 text-right font-medium text-slate-500 border border-slate-700">Disc%</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in selectedItemData.previousPurchases" :key="p.name" class="border-b border-slate-800 hover:bg-slate-800/40">
                      <td class="px-1 py-0.5 font-medium text-blue-400 border border-slate-700 truncate max-w-[70px]" :title="p.name">{{ p.name }}</td>
                      <td class="px-1 py-0.5 text-slate-500 border border-slate-700 whitespace-nowrap">{{ p.date }}</td>
                      <td class="px-1 py-0.5 text-right font-mono text-slate-300 border border-slate-700 text-xl">{{ p.rate.toFixed(2) }}</td>
                      <td class="px-1 py-0.5 text-right font-mono text-slate-400 border border-slate-700">{{ p.qty }}</td>
                      <td class="px-1 py-0.5 text-right border border-slate-700 text-lg" :class="p.discount > 0 ? 'text-red-400' : 'text-slate-600'">{{ p.discount > 0 ? p.discount + '%' : '—' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No previous sales' : 'Select a row to see history' }}</div>
              </div>
            </div>

            <!-- 2. Price List row -->
            <div class="flex flex-col">
              <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Price Lists<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
              <table v-if="selectedItemData && selectedItemData.priceLists && selectedItemData.priceLists.length" class="w-full border-collapse text-[10px]">
                <thead>
                  <tr class="bg-slate-800">
                    <th class="px-1 py-0.5 text-center font-semibold text-slate-500 border border-slate-700">T</th>
                    <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">List</th>
                    <th class="px-1 py-0.5 text-right font-medium text-slate-500 border border-slate-700">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pl in selectedItemData.priceLists" :key="pl.name + pl.type" class="hover:bg-slate-800/40">
                    <td class="px-1 py-0.5 text-center border border-slate-700">
                      <span class="rounded px-1 py-0.5 text-[9px] uppercase" :class="pl.type === 'buying' ? 'bg-blue-900/40 text-blue-400' : 'bg-slate-700 text-slate-400'">{{ pl.type === 'buying' ? 'B' : 'S' }}</span>
                    </td>
                    <td class="px-1 py-0.5 text-slate-400 border border-slate-700 truncate max-w-[90px] text-lg" :title="pl.name">{{ pl.name }}</td>
                    <td class="px-1 py-0.5 text-right font-mono text-amber-400 border border-slate-700 text-2xl">{{ encPrice(pl.rate || 0) }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No price lists' : 'Select a row to see prices' }}</div>
            </div>

            <!-- 3. Warehouse Stock row (Dynamic height) -->
            <div class="flex flex-col pt-4">
              <div class="px-2 pt-2 pb-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Warehouse Stock<span v-if="selectedItemData" class="ml-1 font-normal normal-case text-slate-600">{{ selectedItemData.item_code }}</span></div>
              <table v-if="selectedItemData && selectedItemData.stock && selectedItemData.stock.length" class="w-full border-collapse text-[10px]" style="table-layout:fixed">
                <colgroup>
                  <col style="width:70%"><col style="width:30%">
                </colgroup>
                <thead>
                  <tr class="bg-slate-800">
                    <th class="px-1 py-0.5 text-left font-semibold text-slate-500 border border-slate-700">Warehouse</th>
                    <th class="px-1 py-0.5 text-right font-medium text-slate-500 border border-slate-700">Actual</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in selectedItemData.stock" :key="s.warehouse" class="hover:bg-slate-800/40">
                    <td class="px-1 py-0.5 text-slate-400 border border-slate-700 overflow-hidden text-ellipsis whitespace-nowrap text-lg" :title="s.warehouse">{{ s.warehouse }}</td>
                    <td class="px-1 py-0.5 text-right font-mono border border-slate-700 text-xl" :class="s.actual_qty > 20 ? 'text-green-400' : s.actual_qty > 0 ? 'text-amber-400' : 'text-red-400'">{{ s.actual_qty }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="px-2 py-2 text-[10px] text-slate-600">{{ selectedItemData ? 'No stock data' : 'Select a row to see stock' }}</div>
            </div>
      </template>

      <!-- ═══════════════════ BOTTOM MIDDLE (settings panel) ═══════════════════ -->
      <template #bottom-middle>
<div class="flex flex-col gap-2 p-2">
              <div class="flex gap-1">
                <button @click="exportItems" class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-sm font-bold uppercase text-slate-400 hover:text-blue-400 hover:border-blue-600 transition-colors">Export</button>
                <button @click="openImportModal" class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-sm font-bold uppercase text-slate-400 hover:text-blue-400 hover:border-blue-600 transition-colors">Import</button>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Price List</label>
                <select v-model="priceList" :disabled="billDocStatus !== 0 || billSaved" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-xl text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
                  <option v-for="pl in availablePriceLists" :key="pl" :value="pl">{{ pl }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Tax</label>
                <select v-model="taxTemplate" :disabled="billDocStatus !== 0 || billSaved" class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-xl text-slate-200 outline-none focus:border-blue-500 disabled:bg-slate-800">
                  <option value="">-- None --</option>
                  <option v-for="t in availableTaxTemplates" :key="t" :value="t">{{ t }}</option>
                </select>
                <label class="flex items-center gap-2 mt-1 cursor-pointer select-none">
                  <input type="checkbox" v-model="isInclusiveTax" :disabled="billDocStatus !== 0 || billSaved" class="h-4 w-4 rounded border-slate-600 accent-blue-500 cursor-pointer disabled:cursor-not-allowed" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Inclusive Tax</span>
                </label>
              </div>
              <div class="flex flex-col gap-1.5 py-1">
                <label class="flex items-center gap-2 cursor-pointer select-none">
                  <input type="checkbox" v-model="ignoreDiscountRule" :disabled="billDocStatus !== 0 || billSaved" class="h-4 w-4 rounded border-slate-600 accent-amber-500 cursor-pointer disabled:cursor-not-allowed" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Ignore Pricing Rule</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer select-none">
                  <input type="checkbox" v-model="isReturn" :disabled="billDocStatus !== 0 || billSaved" class="h-4 w-4 rounded border-slate-600 accent-red-500 cursor-pointer disabled:cursor-not-allowed" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Sale Return</span>
                </label>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Warehouse</label>
                <select v-model="defaultWarehouse" disabled class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-lg text-slate-400 outline-none cursor-not-allowed">
                  <option :value="defaultWarehouse">{{ defaultWarehouse || 'None' }}</option>
                </select>
              </div>
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Cost Center</label>
                <select v-model="costCenter" disabled class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-lg text-slate-400 outline-none cursor-not-allowed">
                  <option :value="costCenter">{{ costCenter || 'None' }}</option>
                </select>
              </div>
            </div>
      </template>

      <!-- ═══════════════════ CALCULATION ROWS ═══════════════════ -->
      <template #calculation-rows>
            <tbody>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Item Discount</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-{{ Math.abs(itemDiscountTotal).toFixed(2) }}</td>
                <td class="border border-slate-700 px-2" rowspan="10">
                  <div class="flex flex-col gap-2 h-full py-2">
                    <div class="text-4xl text-slate-500/80">{{ activeItems.length }} item{{ activeItems.length !== 1 ? 's' : '' }}{{ deletedCount > 0 ? ' (' + deletedCount + ' deleted)' : '' }}</div>
                    
                    <div class="rounded-xl border border-blue-500/40 bg-blue-950/60 p-3.5 shadow-2xl">
                      <div class="text-[9px] font-black uppercase tracking-[0.3em] text-blue-400/90 mb-1">Total Amount</div>
                      <div class="flex items-baseline gap-2" :class="grandTotal >= 0 ? 'text-green-500/70' : 'text-red-500/70'">
                        <span class="text-[6mm] font-black">₹</span>
                        <span class="font-mono text-[10.5mm] font-black leading-none" :style="{ filter: `drop-shadow(0 0 14px ${grandTotal >= 0 ? 'rgba(34,197,94,0.42)' : 'rgba(239,68,68,0.42)'})` }">
                          {{ grandTotal.toFixed(2) }}
                        </span>
                      </div>
                    </div>

                    <!-- Row 1: Save/Modify and Print -->
                    <div class="flex gap-2">
                      <div class="flex-1">
                        <button v-if="billSaved && billDocStatus === 0" @click="enterEditMode" class="w-full rounded border border-amber-600/50 bg-amber-900/20 py-2.5 text-center text-xl font-semibold text-amber-400 transition hover:bg-amber-900/30">✏ Modify (Ctrl+M)</button>
                        <button v-else-if="!billSaved" ref="saveButton" @click="saveBill" class="w-full rounded py-2.5 text-center text-xl font-semibold text-white transition shadow bg-[#285A48] hover:bg-[#1e4538]">{{ savedInvoiceName ? 'Update' : 'Save (Ctrl+S)' }}</button>
                      </div>
                      <button class="flex-1 rounded border border-slate-600 bg-slate-800 py-2.5 text-center text-xl font-semibold text-slate-300 hover:bg-slate-700" @click="printBill">Print</button>
                    </div>

                    <!-- Row 2: Cancel/New Bill and Incentive -->
                    <div class="flex gap-2">
                      <button class="flex-1 rounded border border-red-900/50 bg-red-900/10 py-2.5 text-center text-xl font-semibold text-red-400 hover:bg-red-900/20" @click="cancelBill">{{ billSaved ? 'New Bill' : 'Cancel' }}</button>
                      <button @click="showIncentiveModal = true" class="flex-1 rounded border border-indigo-700/50 bg-indigo-900/20 py-2.5 text-center text-xl font-semibold text-indigo-400 hover:bg-indigo-900/40 transition">👥 Incentive{{ incentiveRows.length ? ' (' + incentiveRows.length + ')' : '' }}</button>
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
                        :disabled="billDocStatus !== 0 || billSaved || discountInputMode === 'amt'"
                        min="0" max="100" step="0.5" style="width:100%;height:100%;padding:0 2px"
                        class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="e => { discountInputMode = parseFloat(e.target.value) > 0 ? 'pct' : null; discountDirectAmt = 0 }"
                        @keydown.enter="discountAmtInput?.focus(); discountAmtInput?.select()"
                        @keydown.tab.prevent="discountAmtInput?.focus(); discountAmtInput?.select()" />
                        <span class="shrink-0 px-1 text-slate-300 text-xs">%</span>
                        </div>
                    <div class="flex flex-1 items-center">
                      <span class="shrink-0 px-1 text-slate-500 text-xs"></span>
                      <input ref="discountAmtInput" type="number" v-model.number="discountDirectAmt"
                        :disabled="billDocStatus !== 0 || billSaved || discountInputMode === 'pct'"
                        min="0" step="1" style="width:100%;height:100%;padding:0 2px"
                        class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="e => { discountInputMode = parseFloat(e.target.value) > 0 ? 'amt' : null; discountPct = 0 }"
                        @keydown.enter="freightInput?.focus(); freightInput?.select()"
                        @keydown.tab.prevent="freightInput?.focus(); freightInput?.select()" />
                    </div>
                  </div>
                </td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-{{ Math.abs(discountAmt).toFixed(2) }}</td>
              </tr>
              <tr class="bg-slate-800/40">
               <td class="px-2 text-lg text-slate-200/80 border border-slate-600">Subtotal</td>
               <td class="px-2 border border-slate-600"></td>
               <td class="px-2 text-right font-mono text-slate-100 text-2xl border border-slate-600">{{ subtotal.toFixed(2) }}</td>
              </tr>              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Freight</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="freightInput" type="number" v-model.number="freightAmt"
                    :disabled="billDocStatus !== 0 || billSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.packingInput?.focus(); $refs.packingInput?.select()"
                    @keydown.tab.prevent="$refs.packingInput?.focus(); $refs.packingInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ (freightAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Packing</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="packingInput" type="number" v-model.number="packingAmt"
                    :disabled="billDocStatus !== 0 || billSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.loadingInput?.focus(); $refs.loadingInput?.select()"
                    @keydown.tab.prevent="$refs.loadingInput?.focus(); $refs.loadingInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ (packingAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Loading</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="loadingInput" type="number" v-model.number="loadingAmt"
                    :disabled="billDocStatus !== 0 || billSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="$refs.otherChargesInput?.focus(); $refs.otherChargesInput?.select()"
                    @keydown.tab.prevent="$refs.otherChargesInput?.focus(); $refs.otherChargesInput?.select()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ (loadingAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Other</td>
                <td class="p-0 border-y border-slate-700">
                  <input ref="otherChargesInput" type="number" v-model.number="otherChargesAmt"
                    :disabled="billDocStatus !== 0 || billSaved" min="0" step="1" style="width:100%;height:100%;display:block;padding:0 2px"
                    class="bg-transparent text-right font-mono text-3xl text-slate-200 outline-none focus:bg-[#B0E4CC] focus:text-black disabled:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    @keydown.enter="saveButton?.focus()"
                    @keydown.tab.prevent="saveButton?.focus()" />
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ (otherChargesAmt || 0).toFixed(2) }}</td>
              </tr>
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Tax</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-300 text-2xl border border-slate-700">+{{ totalTax.toFixed(2) }}</td>
              </tr>
            </tbody>
      </template>

    </Item_Invoice_Template>

    <!-- ═══════════════════ MODALS (all fixed-position, outside template shell) ═══════════════════ -->
    <!-- SHORTCUT REFERENCE -->
    <ShortcutPage
      :show="showShortcutPage"
      extra-title="Sales Entry"
      :extra="[
        { key: 'F3', desc: 'Focus modify panel (sidebar)' },
        { key: 'F4', desc: 'Focus sidebar series' },
        { key: 'F6', desc: 'Select Customer' },
        { key: 'Page Up', desc: 'Focus series selector' },
        { key: 'Insert', desc: 'Open incentive entry' },
      ]"
      @close="showShortcutPage = false"
    />

    <!-- INCENTIVE ENTRY MODAL -->
    <IncentiveEntry
      :show="showIncentiveModal"
      doctype="Sales Invoice"
      :docname="savedInvoiceName || ''"
      :initial-rows="incentiveRows"
      @close="showIncentiveModal = false"
      @update:rows="rows => { incentiveRows = rows; showIncentiveModal = false }"
    />

    <!-- CUSTOMER SEARCH MODAL -->
    <CustomerSearchModal
      ref="custSearchModalRef"
      :show="showCustomerSearchModal"
      initial-type="Customer"
      :initial-query="custSearchInitialQuery"
      :allowed-types="isBiller ? ['Customer', 'Supplier', 'Employee'] : undefined"
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
      :invoice-name="savedInvoiceName"
      :initial-print-format="printScheme"
      @close="showPrintModal = false; if (printModalAfterSave) startNewBill()"
    />

    <JumpToRowModal 
      v-model:show="showJumpModal"
      :max-rows="items.length" 
      @jump="handleJump" 
    />

    <Warning
      :show="showClearBillWarning"
      title="Clear Bill Items?"
      message="This will remove all items from the current bill. Continue?"
      @close="showClearBillWarning = false; focusNewCode()"
      @confirm="showClearBillWarning = false; startNewBill()"
    />

    <Warning
      :show="showExitModifyWarning"
      title="Exit without Saving?"
      message="Discard changes to this bill and start a new one?"
      @close="showExitModifyWarning = false; nextTick(() => lastFocusedEl?.focus())"
      @confirm="showExitModifyWarning = false; startNewBill(); openCustomerSearch()"
    />

    <BarcodePrintingModal
      :show="showBarcodeModal"
      @close="showBarcodeModal = false"
    />

    <ErrorWindow
      :show="showErrorModal"
      :message="errorMessage"
      @close="showErrorModal = false"
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
              : s === billSeries
                ? 'border-blue-700 bg-blue-900/20 text-blue-300'
                : 'border-slate-700 bg-slate-800 text-slate-200'"
            @click="selectSeries(s)"
            @mouseenter="seriesHighlightIdx = idx"
          >
            <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-700 font-mono text-sm text-slate-300">
              {{ idx + 1 }}
            </span>
            <span class="font-bold tracking-wide">{{ s }}</span>
            <span v-if="s === billSeries" class="ml-auto text-[10px] font-bold text-blue-400">ACTIVE</span>
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

    <!-- Quick Search results while typing -->
    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :price-list="priceList"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
    />

    <!-- Price Update Modal (Refactored Component) -->
    <CustomerPrice
      v-if="savePricePopup.show"
      :data="savePricePopup"
      :customer="customer"
      :price-list="priceList"
      @saveCustomer="confirmSavePrice"
      @updatePricelist="confirmUpdatePricelist"
      @dismiss="dismissSavePrice"
      @advanced="showPriceListUpdate = true"
    />

    <!-- Price List Update Subwindow -->
    <PriceListUpdate
      v-if="showPriceListUpdate"
      is-sub-window
      :item-code="savePricePopup.item_code"
      :selected-price-list="priceList"
      :initial-factor="savePricePopup.multiplication_factor"
      @close="showPriceListUpdate = false"
      @saved="onPriceListSaved"
    />

    <!-- CUSTOM ADDRESS MODAL -->
    <div v-if="showCustomAddressModal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm" @click.self="showCustomAddressModal = false">
      <div class="w-[960px] overflow-hidden rounded-[32px] bg-slate-900 border border-amber-700/50 shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-700 bg-slate-800/60 px-10 py-8">
          <div>
            <div class="text-3xl font-bold text-slate-100">Custom Delivery Name &amp; Address</div>
            <div class="text-base text-slate-400 mt-1">Overrides customer name &amp; address on the printed invoice</div>
          </div>
          <button @click="showCustomAddressModal = false" class="rounded p-2 text-slate-400 hover:bg-slate-700 hover:text-slate-200 text-4xl leading-none">&times;</button>
        </div>
        <div class="p-12 flex flex-col gap-8">
          <div class="flex flex-col gap-3">
            <label class="text-2xl font-bold uppercase tracking-wider text-amber-500">Customer Name</label>
            <input
              ref="customNameInput"
              v-model="customAddress.custom_customer_name"
              type="text"
              placeholder="e.g. Ramesh &amp; Brothers"
              class="w-full rounded-2xl border-2 border-slate-600 bg-slate-800 px-6 py-5 text-4xl text-slate-100 outline-none focus:border-amber-500 placeholder-slate-600"
              @keydown.enter.prevent="focusCustomAddr1"
            />
          </div>
          <div class="flex flex-col gap-3">
            <label class="text-2xl font-bold uppercase tracking-wider text-slate-500">Address Line 1</label>
            <input
              ref="customAddr1Input"
              v-model="customAddress.custom_address_line1"
              type="text"
              placeholder="Street / Door No"
              class="w-full rounded-2xl border-2 border-slate-600 bg-slate-800 px-6 py-5 text-4xl text-slate-100 outline-none focus:border-blue-500 placeholder-slate-600"
              @keydown.enter.prevent="focusCustomAddr2"
            />
          </div>
          <div class="flex flex-col gap-3">
            <label class="text-2xl font-bold uppercase tracking-wider text-slate-500">Address Line 2</label>
            <input
              ref="customAddr2Input"
              v-model="customAddress.custom_address_line2"
              type="text"
              placeholder="City / District / Pincode"
              class="w-full rounded-2xl border-2 border-slate-600 bg-slate-800 px-6 py-5 text-4xl text-slate-100 outline-none focus:border-blue-500 placeholder-slate-600"
              @keydown.enter.prevent="focusCustomMobile"
            />
          </div>
          <div class="flex flex-col gap-3">
            <label class="text-2xl font-bold uppercase tracking-wider text-slate-500">Mobile Number</label>
            <input
              ref="customMobileInput"
              v-model="customAddress.custom_mobile_number"
              type="text"
              placeholder="e.g. 9876543210"
              class="w-full rounded-2xl border-2 border-slate-600 bg-slate-800 px-6 py-5 text-4xl text-slate-100 outline-none focus:border-blue-500 placeholder-slate-600"
              @keydown.enter.prevent="showCustomAddressModal = false"
            />
          </div>
        </div>
        <div class="flex items-center justify-between border-t border-slate-800 bg-slate-800/50 px-12 py-8">
          <button
            v-if="customAddress.custom_customer_name || customAddress.custom_address_line1 || customAddress.custom_address_line2 || customAddress.custom_mobile_number"
            @click="customAddress = { custom_customer_name: '', custom_address_line1: '', custom_address_line2: '', custom_mobile_number: '' }"
            class="rounded-xl border-2 border-red-900/50 bg-transparent px-8 py-4 text-xl font-bold uppercase text-red-400 hover:bg-red-900/20 transition-colors"
          >Clear</button>
          <div v-else></div>
          <div class="flex gap-6">
            <button @click="showCustomAddressModal = false" class="rounded-xl border-2 border-slate-600 bg-slate-800 px-10 py-4 text-xl font-bold text-slate-300 hover:bg-slate-700 transition-colors">Cancel</button>
            <button @click="showCustomAddressModal = false" class="rounded-xl bg-amber-600 px-10 py-4 text-xl font-bold text-white hover:bg-amber-700 transition-colors">Done</button>
          </div>
        </div>
      </div>
    </div>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import Item_Invoice_Template from '../components/Item_Invoice_Template.vue'
import { useRouter, useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { fetchBillingSettings, fetchItemPrice, searchItems, fetchItemDetails, frappeGet, frappePost } from '../api.js'
import { searchCustomers } from '../customersearch.js'
import PrintOptionsModal from '../components/PrintOptionsModal.vue'
import CustomerSearchModal from '../components/CustomerSearchModal.vue'
import ItemSearch from '../components/ItemSearch.vue'
import CustomerPrice from '../components/CustomerPrice.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import BarcodePrintingModal from '../components/BarcodePrintingModal.vue'
import JumpToRowModal from '../components/JumpToRowModal.vue'
import IncentiveEntry from '../components/IncentiveEntry.vue'
import ShortcutPage from '../components/ShortcutPage.vue'
import Warning from '../components/Warning.vue'
import ErrorWindow from '../components/ErrorWindow.vue'
import PriceListUpdate from './PriceListUpdate.vue'
import { createCustomer, updateCustomer, fetchCustomerDetails } from '../api/customer.js'
import { saveCustomerItemPrice, updateItemPriceList } from '../api/customerPrice.js'
import { useItemCache, searchItemsInCache } from '../services/itemCache.js'
import { useDiscountRules } from '../composables/useDiscountRules.js'
import CustomerLedger from './CustomerLedger.vue'
import { useShortcuts, useSubwindow, useSubwindowWatcher } from '../services/shortcutManager'
import { getUserRole } from '../composables/usePermission'
import { salesEntryShortcuts } from '../shortcuts/salesEntryShortcuts'
import * as XLSX from 'xlsx'

const router = useRouter()
const route = useRoute()
const API = '/api/method/ssplbilling.api.SaleEntry_api'

const { items: cachedItems, refreshItemCache, lookupItemInCache, lastSync, fetchCustomerSalesHistory, getItemHistoryFromCache, refreshDiscountRuleCache } = useItemCache()

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

const isBiller = getUserRole() === 'biller'

const showPrintModal = ref(false)
const printModalAfterSave = ref(false)
const showIncentiveModal = ref(false)
const showShortcutPage = ref(false)
const incentiveRows = ref([])
const showBarcodeModal = ref(false)
const showErrorModal = ref(false)
const errorMessage = ref('')

function showError(msg) {
  errorMessage.value = msg
  showErrorModal.value = true
}
const showImportModal = ref(false)
const showPriceListUpdate = ref(false)

function onPriceListSaved() {
  refreshItemCache('Sales', priceList.value, defaultWarehouse.value)
}
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
const defaultTaxRate = ref(0)
const priceList = ref('Standard Selling')
const printScheme = ref('')
const taxTemplate = ref('')
const isInclusiveTax = ref(false)

watch(taxTemplate, (val) => {
  if (val.toLowerCase().includes('inclusive')) {
    isInclusiveTax.value = true
  } else {
    isInclusiveTax.value = false
  }
  applyRegionalTaxLogic()
})

function applyRegionalTaxLogic() {
  if (!selectedCustomerDetails.value || !taxTemplate.value) return
  
  const companyState = localStorage.getItem('wb-company-state') || ''
  const partyState = selectedCustomerDetails.value.state || ''
  
  if (!companyState || !partyState) return
  
  const isInterState = companyState.toLowerCase() !== partyState.toLowerCase()
  const currentTax = taxTemplate.value
  
  if (isInterState) {
    if (currentTax.toLowerCase().includes('in-state')) {
      const targetTax = currentTax.replace(/in-state/i, 'Out-State')
      const found = availableTaxTemplates.value.find(t => t.toLowerCase() === targetTax.toLowerCase())
      if (found) taxTemplate.value = found
    }
  } else {
    if (currentTax.toLowerCase().includes('out-state')) {
      const targetTax = currentTax.replace(/out-state/i, 'In-State')
      const found = availableTaxTemplates.value.find(t => t.toLowerCase() === targetTax.toLowerCase())
      if (found) taxTemplate.value = found
    }
  }
}

const costCenter = ref(localStorage.getItem('wb-cost-center') || '')
const incomeAccount = ref(localStorage.getItem('wb-income-account') || '')

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
  
  // 1. Try local storage first for this series
  const cachedPL = localStorage.getItem(`wb-price-list-${series}`)
  if (cachedPL && !skipPriceListSync.value) {
    priceList.value = cachedPL
  } else if (cfg?.price_list && !skipPriceListSync.value) {
    // 2. Fallback to series config from backend
    priceList.value = cfg.price_list
  }

  if (!cfg) return
  
  if (cfg.print_format) printScheme.value = cfg.print_format
  if (cfg.tax_template) taxTemplate.value = cfg.tax_template
  
  if (!localStorage.getItem('wb-income-account')) {
    incomeAccount.value = cfg.income_account || ''
  }

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
  return frappePost(`ssplbilling.api.SaleEntry_api.${method}`, params)
}

// ==================== INPUT REFS ====================
const inputRefs = {}
const rowRefs   = {}
const sidebarBillRefs = new Map()
const sidebarFocusedIdx = ref(-1)
function setRef(el, type, idx) { const k = `${type}-${idx}`; if (el) inputRefs[k] = el; else delete inputRefs[k] }
function setRowRef(el, idx)    { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setSidebarBillRef(el, idx) { if (el) sidebarBillRefs.set(idx, el); else sidebarBillRefs.delete(idx) }
function navigateSidebarBill(idx, dir) {
  const target = sidebarBillRefs.get(idx + dir)
  if (target) { target.focus(); target.scrollIntoView({ block: 'nearest' }) }
}
function focusFirstSidebarBill() {
  const first = sidebarBillRefs.get(0)
  if (first) { first.focus(); first.scrollIntoView({ block: 'nearest' }) }
}
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const skipPriceListSync = ref(false)
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
const custSearchInitialQuery = ref('')

function openSeriesModal() {
  seriesHighlightIdx.value = Math.max(0, availableSeries.value.indexOf(billSeries.value))
  showSeriesDropdown.value = true
}

function selectSeries(s) {
  billSeries.value = s
  showSeriesDropdown.value = false
  nextTick(() => openCustomerSearch())
}

function openCustomerSearch(prefill = '') {
  if (billSaved.value || billDocStatus.value !== 0) return
  const query = typeof prefill === 'string' ? prefill : ''
  showCustomerSearchModal.value = true
  custSearchInitialQuery.value = query
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
  applyRegionalTaxLogic();
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
const editingOriginalCode = ref(null)  // tracks item_code before user edits an existing row
const newItemCode = ref('')
const quickSearchResults = ref([])
const quickSearchRef = ref(null)
const quickSearchAnchor = ref(null)

async function onQuickSearchSelect(item) {
  if (!item) return
  // Use the same logic as the main search modal
  itemSearchTargetRow = selectedRow.value !== -1 ? selectedRow.value : null
  await pickItem(item)
  quickSearchResults.value = []
}
const newQty = ref(0)
const isReturn = ref(false)
const billSaved = ref(false)
const billDocStatus = ref(0) // 0=Draft, 1=Submitted, 2=Cancelled
const showJumpModal = ref(false)
const showClearBillWarning = ref(false)
const showExitModifyWarning = ref(false)
const lastFocusedEl = ref(null)
const savedInvoiceName = ref(null)   // null = new bill; string = existing/just-saved invoice name
const showDiscardModal = ref(false)
const showCustomAddressModal = ref(false)
const customAddress = ref({ custom_customer_name: '', custom_address_line1: '', custom_address_line2: '', custom_mobile_number: '' })
const customNameInput = ref(null)
const customAddr1Input = ref(null)
const customAddr2Input = ref(null)
const customMobileInput = ref(null)
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

// Re-calculate all items when global customer factor changes
watch(selectedCustomerDetails, (newVal) => {
  if (newVal && !billSaved.value) {
    items.value.forEach((_, idx) => applyCustomerPricingForRow(idx))
  }
})

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
  
  // 1. Get global customer factor (default to 1 if null, undefined, or 0)
  let globalFactor = parseFloat(selectedCustomerDetails.value?.pricelist_multiplication_factor) || 1
  if (globalFactor === 0) globalFactor = 1

  // 2. Get item-specific factor (default to 1 if not found or zero)
  let itemFactor = customerPricing.value[item.item_code] || 1
  if (itemFactor === 0) itemFactor = 1
  
  // 3. Combine factors (Multiplicative)
  const finalFactor = globalFactor * itemFactor

  // 4. Always use the base list price from cache to avoid compounding factors
  const cached = lookupItemInCache(item.item_code)
  const baseRate = cached ? rateForUom(cached, item.uom) : item.rate
  
  // 5. Update rate (always multiply)
  item.rate = baseRate * finalFactor
  item._customer_pricing = Math.abs(finalFactor - 1) > 0.0001
}

// Save-price popup
const savePricePopup = ref({ show: false, idx: null, item_code: '', item_name: '', multiplication_factor: 1, rate: 0, uom: '' })
let _rateAtFocus = null
let _discAtFocus = null

function onRateFocus(idx) { _rateAtFocus = items.value[idx]?.rate ?? null }
function onDiscountFocus(idx) { _discAtFocus = items.value[idx]?.discount ?? null }

function onRateBlur(idx) {
  const item = items.value[idx]
  if (!item) { _rateAtFocus = null; return }
  const newRate = item.rate
  const rateChanged = _rateAtFocus !== null && newRate !== _rateAtFocus
  _rateAtFocus = null
  if (!rateChanged) return
  
  // Clear any previous customer pricing for this row if rate was manually edited
  item._customer_pricing = false
  
  if (!customer.value || item._rule_discount != null) return
  
  // Compute multiplication factor vs cached list price and offer to save
  const cached = lookupItemInCache(item.item_code)
  const listRate = rateForUom(cached, item.uom) || 0
  const factor = listRate > 0 ? (newRate / listRate) : 1
  
  // If listRate is 0, we can't really compute a factor but we should still allow 
  // updating the pricelist or saving for customer if the new rate > 0
  if (listRate === 0 && newRate > 0) {
    _triggerSavePricePopup(idx, 1) // Factor of 1 for 0-based, or we could use factor = newRate
  } else if (Math.abs(factor - 1) > 0.0001) {
    _triggerSavePricePopup(idx, factor)
  }
}

function onDiscountBlur(idx) {
  _discAtFocus = null
}
function _triggerSavePricePopup(idx, factor) {
  const item = items.value[idx]
  if (!item?.item_code) return
  savePricePopup.value = { 
    show: true, 
    idx, 
    item_code: item.item_code, 
    item_name: item.item_name, 
    multiplication_factor: factor,
    rate: item.rate,
    uom: item.uom
  }
}

async function confirmSavePrice() {
  const { item_code, multiplication_factor, idx } = savePricePopup.value
  try {
    await saveCustomerItemPrice(customer.value, item_code, multiplication_factor)
    customerPricing.value[item_code] = multiplication_factor
    if (idx != null && items.value[idx]) items.value[idx]._customer_pricing = true
  } catch (e) {
    console.error('[CustomerPricing] save failed', e)
  }
  savePricePopup.value.show = false
  if (idx !== null) goToNextRow(idx)
  else focusNewCode()
}

async function confirmUpdatePricelist() {
  const { item_code, rate, uom, idx } = savePricePopup.value
  try {
    await updateItemPriceList(item_code, priceList.value, rate, uom)
    refreshItemCache('Sales', priceList.value, defaultWarehouse.value)
  } catch (e) {
    console.error('[PriceList] update failed', e)
  }
  savePricePopup.value.show = false
  if (idx !== null) goToNextRow(idx)
  else focusNewCode()
}

function dismissSavePrice() {
  const { idx } = savePricePopup.value
  savePricePopup.value.show = false
  if (idx !== null) goToNextRow(idx)
  else focusNewCode()
}

// ==================== API RESOURCES ====================
const itemLookup = createResource({ url: `${API}.get_item_details` })
const itemSearchResource = createResource({ url: `${API}.search_items` })
const insightResource = createResource({ url: `${API}.get_item_insight` })

const newPending = ref({ item_name: '', uom: '', uoms: [], rate: null })
const newUomSelect = ref(null)

async function lookupItem(code) {
  // 1. Try local cache first
  const cached = lookupItemInCache(code)
  if (cached) {
    // Use rateForUom to respect per-UOM Item Price records for the stock/default UOM
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

function rateForUom(cached, uom) {
  // 1. Check for an actual Item Price record for this price list + UOM
  const plUomRates = cached.uom_price_lists?.[priceList.value]
  if (plUomRates && plUomRates[uom] != null) {
    return plUomRates[uom]
  }
  // 2. Fallback: base (stock-UOM) rate × conversion factor
  let baseRate = cached.price || cached.rate || 0
  if (cached.price_lists && priceList.value) {
    const pl = cached.price_lists.find(p => p.name === priceList.value)
    if (pl) baseRate = pl.rate
  }
  const uomEntry = (cached.uoms || []).find(u => u.uom === uom)
  return baseRate * (uomEntry ? uomEntry.conversion_factor : 1)
}

function isRateDifferent(item) {
  if (!item.item_code || item.deleted) return false
  const cached = lookupItemInCache(item.item_code)
  if (!cached) return false
  const plRate = rateForUom(cached, item.uom)
  return Math.abs(item.rate - plRate) > 0.001
}

function onUomChange(idx) {
  const item = items.value[idx]
  // Build a minimal cached-like object from the row itself, falling back to cache
  const cached = lookupItemInCache(item.item_code) || {
    price: item.rate,
    price_lists: [],
    uoms: item.uoms || [],
    uom_price_lists: item.uom_price_lists || {},
  }
  item.rate = rateForUom(cached, item.uom)
}

function onNewUomChange() {
  const cached = lookupItemInCache(newItemCode.value.trim())
  if (!cached) return
  newPending.value.rate = rateForUom(cached, newPending.value.uom)
}

function onNewCodeInput() {
  const code = newItemCode.value.trim()
  if (code && code.length >= 2) {
    quickSearchResults.value = searchItemsInCache(code)
    quickSearchAnchor.value = newCodeInput.value
  } else {
    quickSearchResults.value = []
  }
}

let lookupTimeout = null
watch(newItemCode, (val) => {
  clearTimeout(lookupTimeout); const code = val.trim()
  
  if (code.length < 2) { 
    newPending.value = { item_name: '', uom: '', uoms: [], rate: null }
    return 
  }

  lookupTimeout = setTimeout(async () => {
    const r = await lookupItem(code)
    newPending.value = r ? { item_name: r.item_name, uom: r.uom, uoms: r.uoms || [], rate: r.rate, tax_rate: r.tax_rate, warehouse: r.warehouse } : { item_name: '', uom: '', uoms: [], rate: null }
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

  // 2. Map all available price lists with UOM-aware rates
  const resolvedPriceLists = availablePriceLists.value.map(plName => {
    let rate = 0
    // Try UOM specific price list first
    if (cached?.uom_price_lists?.[plName]?.[uom] != null) {
      rate = cached.uom_price_lists[plName][uom]
    } else if (cached?.price_lists) {
      // Fallback to base price list rate (applying conversion if needed, though usually handled by rateForUom)
      const pl = cached.price_lists.find(p => p.name === plName)
      if (pl) {
        // If we have a cached object, we can use rateForUom logic
        rate = rateForUom(cached, uom, plName)
      }
    }

    return {
      name: plName,
      type: 'selling', // SalesEntry is for selling
      rate: rate
    }
  })

  selectedItemData.value = {
    item_code: code,
    item_name: itemName || cached?.item_name || '',
    uom: uom || cached?.uom || '',
    stock: (cached?.warehouse_stock || []).map(s => ({
      warehouse: s.warehouse,
      actual_qty: s.qty
    })),
    previousPurchases: localHistory.slice(0, 10), // Show latest 10 from cache
    priceLists: resolvedPriceLists,
  }
}
watch(selectedRow, async (idx) => {
  if (idx >= 0 && idx < items.value.length && !items.value[idx].deleted) {
    const item = items.value[idx]
    await loadItemInsight(item.item_code, item.item_name, item.uom)
  } else {
    selectedItemData.value = null
  }
  // Clear quick search results when moving between rows
  quickSearchResults.value = []
})

// Re-price all active items when price list changes
watch(priceList, (newPL) => {
  if (billSeries.value && !skipPriceListSync.value) {
    localStorage.setItem(`wb-price-list-${billSeries.value}`, newPL)
  }
  
  // Update active items in grid
  items.value.forEach(item => {
    if (!item.deleted && item.item_code) {
      const cached = lookupItemInCache(item.item_code)
      if (cached) {
        const price = rateForUom(cached, item.uom)
        if (price > 0) item.rate = price
      }
    }
  })

  // Update pending item
  if (newItemCode.value.trim() && newPending.value.rate !== null) {
    const cached = lookupItemInCache(newItemCode.value.trim())
    if (cached) {
      const price = rateForUom(cached, newPending.value.uom)
      if (price > 0) newPending.value.rate = price
    }
  }

  // Update insight panel if a row is selected
  if (selectedRow.value >= 0 && selectedRow.value < items.value.length) {
    const item = items.value[selectedRow.value]
    loadItemInsight(item.item_code, item.item_name, item.uom)
  }
})

// ==================== FOCUS ====================
function focusField(f, idx) { 
  nextTick(() => { 
    const el = inputRefs[`${f}-${idx}`]; 
    if (el) { 
      el.focus(); 
      el.select();
      el.scrollIntoView({ block: 'nearest' });
    } 
  }) 
}
function focusRow(idx) { 
  nextTick(() => {
    const el = rowRefs[idx]
    if (el) {
      el.focus()
      el.scrollIntoView({ block: 'nearest' })
    }
  }) 
}
function focusNewCode() { 
  nextTick(() => {
    if (newCodeInput.value) {
      newCodeInput.value.focus()
      newCodeInput.value.scrollIntoView({ block: 'nearest' })
    }
  }) 
}

function handleQuickSearchKeydown(e, idx = null) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return true
    } else if (e.key === 'Escape') {
      e.preventDefault()
      quickSearchResults.value = []
      return true
    }
  }
  
  // Navigation keys when search is NOT active
  if (e.key === 'ArrowDown') {
    if (idx !== null) { e.preventDefault(); moveRow(idx, 1) }
  } else if (e.key === 'ArrowUp') {
    if (idx !== null) { e.preventDefault(); moveRow(idx, -1) }
    else { e.preventDefault(); moveToLastActiveRow() }
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (idx !== null) onCodeEnter(idx)
    else onNewCodeEnter()
  }
  return false
}

function focusNewQty() {
  if (newItemCode.value.trim() && newPending.value.item_name) {
    loadItemInsight(newItemCode.value.trim(), newPending.value.item_name, newPending.value.uom)
  }
  nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() })
}

function focusCustomName() { nextTick(() => { customNameInput.value?.focus(); customNameInput.value?.select() }) }
function focusCustomAddr1() { nextTick(() => { customAddr1Input.value?.focus(); customAddr1Input.value?.select() }) }
function focusCustomAddr2() { nextTick(() => { customAddr2Input.value?.focus(); customAddr2Input.value?.select() }) }
function focusCustomMobile() { nextTick(() => { customMobileInput.value?.focus(); customMobileInput.value?.select() }) }

watch(showCustomAddressModal, (val) => {
  if (val) focusCustomName()
})

// ==================== ROW NAV ====================
function findNextActiveRow(from, dir) { let i = from + dir; while (i >= 0 && i < items.value.length) { if (!items.value[i].deleted) return i; i += dir }; return null }
function moveRow(from, dir) { const n = findNextActiveRow(from, dir); if (n !== null) { selectedRow.value = n; focusRow(n) } else if (dir === 1) { selectedRow.value = -1; focusNewCode() } }
function moveToLastActiveRow() { for (let i = items.value.length - 1; i >= 0; i--) { if (!items.value[i].deleted) { selectedRow.value = i; focusRow(i); return } } }
function selectRow(idx) { if (!items.value[idx].deleted) { selectedRow.value = idx; focusRow(idx) } }
function goToNextRow(from) {
  if (items.value[from]?.qty === 0) return
  const n = findNextActiveRow(from, 1);
  if (n !== null) { selectedRow.value = n; focusField('code', n) }
  else { selectedRow.value = -1; focusNewCode() }
}
function enterRow(idx) { if (!items.value[idx]?.deleted && billDocStatus.value === 0) focusField('code', idx) }
function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return  // bubbled from a child input — ignore
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); enterRow(idx) }
}

// ==================== ITEM ENTRY ====================
function onCodeFocus(idx) { editingOriginalCode.value = items.value[idx].item_code }

function onCodeInput(idx) {
  const val = items.value[idx].item_code
  if (val && val.length >= 2) {
    quickSearchResults.value = searchItemsInCache(val)
    quickSearchAnchor.value = inputRefs[`code-${idx}`]
  } else {
    quickSearchResults.value = []
  }
}

async function onCodeEnter(idx) {
  const code = items.value[idx].item_code.trim(); if (!code) return; items.value[idx].item_code = code

  // If the code hasn't changed, just move to qty
  if (code === editingOriginalCode.value) {
    focusField('qty', idx)
    return
  }

  const r = await lookupItem(code)
  if (r) {
    const resolvedCode = r.item_code || code

    // If the targeted row was deleted while searching, or we want to ALWAYS populate at the end
    // we should use push instead. But here, if it was already deleted, we definitely push.
    if (items.value[idx].deleted) {
      items.value.push({
        item_code: resolvedCode,
        item_name: r.item_name,
        uom: r.uom,
        uoms: r.uoms || [],
        uom_price_lists: r.uom_price_lists || {},
        qty: 1,
        rate: r.rate,
        discount: 0,
        tax_rate: r.tax_rate ?? defaultTaxRate.value,
        warehouse: r.warehouse || defaultWarehouse.value,
        deleted: false,
        _rowKey: makeRowKey(),
        _is_free: false,
        _rule_discount: null,
        _customer_pricing: false
      })
      const newIdx = items.value.length - 1
      applyDiscountRuleForRow(newIdx)
      applyCustomerPricingForRow(newIdx)
      loadItemInsight(resolvedCode, r.item_name, r.uom)
      focusField('qty', newIdx)
      return
    }

    // Reset the row like a new one
    items.value[idx] = {
      ...items.value[idx],
      item_code: resolvedCode,
      item_name: r.item_name,
      uom: r.uom,
      uoms: r.uoms || [],
      uom_price_lists: r.uom_price_lists || {},
      qty: 1,
      rate: r.rate,
      discount: 0,
      tax_rate: r.tax_rate ?? defaultTaxRate.value,
      warehouse: r.warehouse || defaultWarehouse.value,
      deleted: false,
      _is_free: false,
      _rule_discount: null,
      _customer_pricing: false
    }

    if (!items.value[idx]._rowKey) items.value[idx]._rowKey = makeRowKey()
    applyDiscountRuleForRow(idx)
    applyCustomerPricingForRow(idx)

    loadItemInsight(resolvedCode, r.item_name, r.uom)
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
    newPending.value = { item_name: r.item_name, uom: r.uom, uoms: r.uoms || [], rate: r.rate, tax_rate: r.tax_rate, warehouse: r.warehouse }
    focusNewQty()
  }
  else openSearch(code, null)
}

async function addNewItem() {
  const code = newItemCode.value.trim(); if (!code) return
  if (newQty.value === 0) return
  
  // Use newPending if it matches, otherwise lookup
  let r = (newPending.value && newItemCode.value === code && newPending.value.item_name) 
    ? newPending.value 
    : await lookupItem(code)

  if (!r) { openSearch(code, null); return }

  items.value.push({
    item_code: r.item_code || code,
    item_name: r.item_name,
    uom: r.uom,
    uoms: r.uoms || [],
    uom_price_lists: r.uom_price_lists || {},
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
  newQty.value = 0;
  newPending.value = { item_name: '', uom: '', uoms: [], rate: null };
  selectedRow.value = -1; // Reset selection so we stay in "new entry" mode
  focusNewCode()
}

function softDelete(idx) {
  items.value[idx].deleted = true
  // If the deleted row was selected, move selection to a nearby active row
  if (selectedRow.value === idx) {
    const next = findNextActiveRow(idx, 1)
    if (next !== null) {
      selectedRow.value = next
      focusRow(next)
    } else {
      const prev = findNextActiveRow(idx, -1)
      if (prev !== null) {
        selectedRow.value = prev
        focusRow(prev)
      } else {
        selectedRow.value = -1
        focusNewCode()
      }
    }
  }
}
function restoreItem(idx) {
  items.value[idx].deleted = false
  selectedRow.value = idx
  focusRow(idx)
}

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

  // If the code hasn't changed for an existing row, just focus qty
  if (itemSearchTargetRow !== null && item.item_code === editingOriginalCode.value) {
    focusField('qty', itemSearchTargetRow)
    return
  }

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
    // If the targeted row is deleted, we must always push to the last row
    if (items.value[itemSearchTargetRow].deleted) {
      items.value.push({
        item_code: item.item_code,
        item_name: item.item_name,
        uom: item.uom,
        uoms: item.uoms || [],
        uom_price_lists: item.uom_price_lists || {},
        qty: 1,
        rate: finalRate,
        discount: 0,
        tax_rate: finalTax,
        warehouse: finalWh,
        deleted: false,
        _rowKey: makeRowKey(),
        _is_free: false,
        _rule_discount: null,
        _customer_pricing: false
      })
      const newIdx = items.value.length - 1
      applyDiscountRuleForRow(newIdx)
      applyCustomerPricingForRow(newIdx)
      selectedRow.value = newIdx
      focusField('qty', newIdx)
      return
    }

    // Reset the row like a new one
    items.value[itemSearchTargetRow] = {
      ...items.value[itemSearchTargetRow],
      item_code: item.item_code,
      item_name: item.item_name,
      uom: item.uom,
      uoms: item.uoms || [],
      uom_price_lists: item.uom_price_lists || {},
      qty: 1,
      rate: finalRate,
      discount: 0,
      tax_rate: finalTax,
      warehouse: finalWh,
      deleted: false,
      _is_free: false,
      _rule_discount: null,
      _customer_pricing: false
    }

    if (!items.value[itemSearchTargetRow]._rowKey) items.value[itemSearchTargetRow]._rowKey = makeRowKey()
    applyDiscountRuleForRow(itemSearchTargetRow)
    applyCustomerPricingForRow(itemSearchTargetRow)

    selectedRow.value = itemSearchTargetRow
    focusField('qty', itemSearchTargetRow)
  } else {
    newItemCode.value = item.item_code
    newPending.value = { item_name: item.item_name, uom: item.uom, uoms: item.uoms || [], rate: finalRate }
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

      // Always push to the last row, ignoring existing items
      items.value.push({
        item_code: itemCode,
        item_name: itemName,
        uom: uom,
        qty: qty,
        rate: rate,
        discount: discount,
        tax_rate: taxRate,
        warehouse: defaultWarehouse.value,
        deleted: false,
        _rowKey: makeRowKey()
      })
      applyDiscountRuleForRow(items.value.length - 1)
      applyCustomerPricingForRow(items.value.length - 1)
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
  XLSX.writeFile(wb, `Sales_Items_${new Date().toISOString().slice(0, 10)}.xlsx`)
}

// ==================== SIDEBAR MODIFY PANEL ====================
const sidebarDate = ref(getTodayIST())
const sidebarSearch = ref('')
const sidebarSeries = ref('')
const draftOnly = ref(false)
const sidebarBills = ref([])
const sidebarLoading = ref(false)

async function fetchSidebarBills() {
  sidebarLoading.value = true
  try {
    sidebarBills.value = await frappeGet('ssplbilling.api.cashier_api.get_sales_invoices', {
      query: sidebarSearch.value,
      limit: 100,
      posting_date: sidebarDate.value,
      naming_series: sidebarSeries.value || '',
      draft_only: draftOnly.value
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

watch([sidebarDate, sidebarSeries, draftOnly], fetchSidebarBills)

let sidebarSearchTimeout = null
watch(sidebarSearch, () => {
  clearTimeout(sidebarSearchTimeout)
  sidebarSearchTimeout = setTimeout(fetchSidebarBills, 500)
})

async function loadInvoice(invoiceName) {
  try {
    const inv = await frappeGet('ssplbilling.api.cashier_api.get_sales_invoice', { invoice_name: invoiceName })
    if (!inv) { showError('Could not load invoice'); return }

    // 1. Basic Info
    savedInvoiceName.value = inv.name
    billDocStatus.value = inv.docstatus
    billSaved.value = true
    billDate.value = inv.posting_date
    isReturn.value = !!inv.is_return
    paymentMode.value = inv.payment_mode || 'Cash'
    customer.value = inv.customer
    custSearch.value = inv.customer_name
    selectedCustomerDetails.value = { name: inv.customer, customer_name: inv.customer_name, state: inv.state || '' }
    
    // 2. Series & Price List
    skipPriceListSync.value = true
    if (inv.naming_series && availableSeries.value.includes(inv.naming_series)) {
      billSeries.value = inv.naming_series
    }
    await nextTick()
    if (inv.price_list) priceList.value = inv.price_list
    skipPriceListSync.value = false

    // 3. Totals & Discounts
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
    isInclusiveTax.value = !!inv.is_inclusive
    if (inv.cost_center) costCenter.value = inv.cost_center

    // 4. Items
    items.value = inv.items.map(i => {
      const disc = i.discount || 0
      const listRate = i.price_list_rate || i.rate
      const isFreeRow = (i.rate === 0 || i.rate === '0') && disc === 0
      return {
        ...i,
        qty: isReturn.value ? Math.abs(i.qty) : i.qty,
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

    // 5. Incentive
    incentiveRows.value = (inv.incentive_system || []).map(r => ({
      employee: r.employee || '', employee_name: r.employee_name || '',
      role: r.role || '', points: parseFloat(r.points) || 0,
    }))
    fetchNextBillNo()

    // 6. Set selectedCustomerDetails BEFORE customer.value
    try {
      const details = await fetchCustomerDetails(inv.customer)
      selectedCustomerDetails.value = details
    } catch (e) {
      selectedCustomerDetails.value = {
        name: inv.customer,
        customer_name: inv.customer_name,
        balance: 0,
        address_line1: ""
      }
    }
    
    customer.value = inv.customer
    custSearch.value = inv.customer_name

    // 7. Custom address fields
    customAddress.value = {
      custom_customer_name: inv.custom_customer_name || '',
      custom_address_line1: inv.custom_address_line1 || '',
      custom_address_line2: inv.custom_address_line2 || '',
      custom_mobile_number: inv.custom_mobile_number || '',
    }
  } catch (e) {
    showError('Error loading invoice: ' + (e.message || 'Unknown error'))
  }
}

/** Click Edit after save → re-enable the form for updates */
function enterEditMode() {
  if (billDocStatus.value !== 0) {
    showError('Cannot edit a submitted/cancelled invoice.')
    return
  }
  billSaved.value = false
  nextTick(() => {
    if (items.value.length > 0) {
      selectedRow.value = 0
      focusField('code', 0)
    } else {
      customerInput.value?.focus()
    }
  })
}

function getTodayIST() {
  const date = new Date()
  const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }
  const formatter = new Intl.DateTimeFormat('en-CA', options) // 'en-CA' gives YYYY-MM-DD
  return formatter.format(date)
}

function changeBillDate(days) {
  if (billSaved.value || billDocStatus.value !== 0) return
  const d = new Date(billDate.value)
  d.setDate(d.getDate() + days)
  billDate.value = d.toISOString().split('T')[0]
}

// ==================== BILLING ====================
const billDate = ref(getTodayIST())
const customer = ref('')
const billSeries = ref('')

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
    console.warn('[SalesEntry] Failed to fetch customer quick stats:', e)
  }
})

const paymentMode = ref('Cash')
const discountPct = ref(0)
const discountDirectAmt = ref(0)
const discountInputMode = ref(null) // null | 'pct' | 'amt'
const freightAmt = ref(0)
const packingAmt = ref(0)
const loadingAmt = ref(0)
const otherChargesAmt = ref(0)
const availableSeries = ref([])
const nextBillNo = ref('...')

watch(billSeries, (series) => {
  syncSeriesConfig(series)
  fetchNextBillNo()
})

import { session } from '../session.js'

async function fetchSeriesList() {
  try {
    const targetUser = localStorage.getItem('wb-inherited-user') || null
    const settings = await fetchBillingSettings(targetUser)
    const rows = (settings?.billing_series || []).filter(r => r.series)

    // Fetch allowed series for this user
    let allowedList = []
    let userAllowedString = ''
    try {
      const d = await frappeGet('ssplbilling.api.dashboard_api.get_allowed_series', { user: targetUser })
      allowedList = d.allowed_series || []
      userAllowedString = d.user_allowed_string || ''
    } catch (e) {
      console.warn('[SalesEntry] get_allowed_series failed:', e)
    }

    // Fetch ERPNext allowed series for Sales Invoice
    let erpnextSeries = []
    try {
      const list = await frappeGet('ssplbilling.api.SaleEntry_api.get_naming_series')
      if (Array.isArray(list)) erpnextSeries = list
    } catch (e) {
      console.warn('[SalesEntry] get_naming_series failed:', e)
    }

    if (rows.length) {
      billingSeriesConfig.value = rows
      // Filter available series strictly based on user allowed series
      const allSeries = rows.map(r => r.series)
      
      let finalSeries = []
      if (allowedList.length === 0 && !userAllowedString) {
        // Unrestricted user: show all series from billing settings
        finalSeries = allSeries
      } else {
        // Restricted user: show only allowed series
        finalSeries = allSeries.filter(s => allowedList.includes(s))
      }

      // Intersect with actual ERPNext Sales Invoice series
      if (erpnextSeries.length) {
        finalSeries = finalSeries.filter(s => erpnextSeries.includes(s))
      }

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

      availableSeries.value = finalSeries

      if (availableSeries.value.length === 0) {
        showError('You do not have permission to use any Sales Invoice series.')
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
    const list = await frappeGet('ssplbilling.api.SaleEntry_api.get_naming_series')
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
  if (savedInvoiceName.value) {
    nextBillNo.value = savedInvoiceName.value
    return
  }
  if (!billSeries.value) { nextBillNo.value = '...'; return }
  try {
    const res = await frappeGet('ssplbilling.api.SaleEntry_api.get_next_bill_no', { naming_series: billSeries.value })
    nextBillNo.value = res || '...'
  } catch (e) { nextBillNo.value = '...' }
}

const isExempted = computed(() => taxTemplate.value.toLowerCase().includes('exempt'))
const isInclusive = computed(() => isInclusiveTax.value)

// Gross = sum of (qty * rate * (1 - item discount%)) — after item-level discount
const grossTotal = computed(() => {
  const val = activeItems.value.reduce((s, i) => s + i.qty * i.rate * (1 - (i.discount || 0) / 100), 0)
  return isReturn.value ? -val : val
})

const totalBeforeItemDiscount = computed(() => {
  const val = activeItems.value.reduce((s, i) => s + i.qty * i.rate, 0)
  return isReturn.value ? -val : val
})

const itemDiscountTotal = computed(() => {
  const val = activeItems.value.reduce((s, i) => s + i.qty * i.rate * ((i.discount || 0) / 100), 0)
  return isReturn.value ? -val : val
})

// Subtotal: ex-tax amount for inclusive, gross otherwise
const subtotal = computed(() => {
  if (isInclusive.value) {
    const val = activeItems.value.reduce((s, i) => {
      const amt = i.qty * i.rate * (1 - (i.discount || 0) / 100)
      return s + amt / (1 + (i.tax_rate || 0) / 100)
    }, 0)
    return isReturn.value ? -val : val
  }
  return grossTotal.value
})

const discountAmt = computed(() => {
  const val = discountInputMode.value === 'amt'
    ? discountDirectAmt.value
    : subtotal.value * (discountPct.value / 100)
  // discountAmt should stay positive or match subtotal sign? 
  // Usually discount is subtracted. If subtotal is -500, discount -50 makes it -450? 
  // No, if I return 500, and I had 50 discount, I return 450.
  // So discount should probably have same sign as subtotal if we are negating everything.
  return val 
})
const taxableAmt = computed(() => subtotal.value - (isReturn.value ? -discountAmt.value : discountAmt.value))

const totalTax = computed(() => {
  if (isExempted.value) return 0
  if (isInclusive.value) {
    return (grossTotal.value - subtotal.value) * (1 - discountPct.value / 100)
  }
  const val = activeItems.value.reduce((s, i) => {
    const a = i.qty * i.rate * (1 - (i.discount || 0) / 100)
    return s + (a - a * (discountPct.value / 100)) * (i.tax_rate / 100)
  }, 0)
  return isReturn.value ? -val : val
})

const grandTotal = computed(() => {
  const base = isInclusive.value
    ? grossTotal.value * (1 - discountPct.value / 100)
    : taxableAmt.value + totalTax.value
  const charges = (freightAmt.value || 0) + (packingAmt.value || 0) + (loadingAmt.value || 0) + (otherChargesAmt.value || 0)
  return base + (isReturn.value ? -charges : charges)
})
async function saveBill() {
  if (!customer.value.trim()) { openCustomerSearch(); return }
  if (!activeItems.value.length) { showError('Add at least one item'); return }

  const payload = {
    customer: customer.value,
    customer_address: selectedCustomerDetails.value?.address_name || '',
    date: billDate.value,
    due_date: getTodayIST(),
    is_return: isReturn.value ? 1 : 0,
    naming_series: billSeries.value,
    price_list: priceList.value || 'Standard Selling',
    payment_mode: paymentMode.value,
    ...(discountInputMode.value === 'amt'
      ? { additional_discount_amount: discountDirectAmt.value, discount_percentage: 0 }
      : { discount_percentage: discountPct.value, additional_discount_amount: 0 }),
    freight_amount: freightAmt.value,
    freight_account: localStorage.getItem('wb_freight') || '',
    tax_template: taxTemplate.value || '',
    is_inclusive: isInclusiveTax.value ? 1 : 0,
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
    incentive_system: incentiveRows.value.map(r => ({
      employee: r.employee,
      role: r.role,
      points: r.points || 0,
    })),
    custom_customer_name: customAddress.value.custom_customer_name || '',
    custom_address_line1: customAddress.value.custom_address_line1 || '',
    custom_address_line2: customAddress.value.custom_address_line2 || '',
    custom_mobile_number: customAddress.value.custom_mobile_number || '',
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
    fetchSidebarBills()
    printModalAfterSave.value = true
    showPrintModal.value = true
  } catch (e) {
    showError('Error: ' + (e?.message || 'Failed to save invoice'))
  }
}

async function deleteBill() {
  if (!savedInvoiceName.value) return
  if (!confirm('Are you sure you want to delete this draft bill?')) return
  try {
    await apiPost('delete_sales_invoice', { invoice_name: savedInvoiceName.value })
    showError('Bill deleted successfully')
    startNewBill()
    fetchSidebarBills()
  } catch (e) {
    showError('Error deleting bill: ' + (e.message || 'Unknown error'))
  }
}

function startNewBill() {
  items.value = []; selectedRow.value = -1
  isReturn.value = false
  discountPct.value = 0; discountDirectAmt.value = 0; discountInputMode.value = null; freightAmt.value = 0; packingAmt.value = 0; loadingAmt.value = 0; otherChargesAmt.value = 0; newItemCode.value = ''; newQty.value = 1; paymentMode.value = 'Cash'
  billDate.value = getTodayIST()
  billSaved.value = false; billDocStatus.value = 0; savedInvoiceName.value = null; selectedItemData.value = null
  customAddress.value = { custom_customer_name: '', custom_address_line1: '', custom_address_line2: '', custom_mobile_number: '' }
  syncSeriesConfig(billSeries.value)
  nextTick(() => focusNewCode())
}

function printBill() {
  if (!savedInvoiceName.value) { showError('Save the bill first before printing.'); return }
  printModalAfterSave.value = false
  showPrintModal.value = true
}
function cancelBill() { startNewBill() }

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
    const el = sidebarBillRefs.get(0)
    if (el) el.focus()
  })
}

function handleBack() {
  if (activeItems.value.length > 0 && !billSaved.value) {
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
useShortcuts(salesEntryShortcuts({
  openShortcuts: () => { showShortcutPage.value = !showShortcutPage.value },
  save: () => { if (!showPrintModal.value) saveBill() },
  newBill: () => { if (!showPrintModal.value) cancelBill() },
  print: () => { if (!showPrintModal.value) printBill() },
  selectCustomer: () => { if (!showPrintModal.value) openCustomerSearch(custSearch.value) },
  newCustomer: () => { if (!showPrintModal.value) openCustomerSearch() },
  searchItem: () => { if (!showPrintModal.value) openSearch('', null) },
  focusModifyPanel: () => { if (!showPrintModal.value) focusModifyPanel() },
  enterEditMode: () => { if (billSaved.value && billDocStatus.value === 0) enterEditMode() },
  focusSidebarSeries: () => { sidebarSeriesSelect.value?.focus() },
  deleteRow: () => {
    if (!showPrintModal.value && selectedRow.value >= 0 && (!document.activeElement || document.activeElement.tagName !== 'INPUT')) {
      softDelete(selectedRow.value)
    }
  },
  focusSeries: () => { if (!showPrintModal.value) openSeriesModal() },
  openIncentive: () => { showIncentiveModal.value = true },
  toggleDiscountSave: () => {
    if (showPrintModal.value) return
    const activeEl = document.activeElement
    const isEditMode = !!savedInvoiceName.value && !billSaved.value  // modifying existing draft
    const isNewBill = !savedInvoiceName.value

    // If focused on any charge input → End triggers save/update
    const chargeInputs = [discountInput.value, discountAmtInput.value, freightInput.value, packingInput.value, loadingInput.value, otherChargesInput.value]
    if (chargeInputs.includes(activeEl)) {
      saveBill()
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
    if (showCustomAddressModal.value) { showCustomAddressModal.value = false; return }
    if (showJumpModal.value) { showJumpModal.value = false; return }
    if (showDiscardModal.value) { showDiscardModal.value = false; return }
    if (showPrintModal.value) { showPrintModal.value = false; startNewBill(); return }
    if (showBarcodeModal.value) { showBarcodeModal.value = false; return }
    if (showImportModal.value) { showImportModal.value = false; return }
    if (showCustomerSearchModal.value) { closeCustomerSearchModal(); return }
    if (showItemSearchModal.value) { closeItemSearch(); return }
    if (showCustomerLedgerWindow.value) { showCustomerLedgerWindow.value = false; return }
    if (showClearBillWarning.value) { showClearBillWarning.value = false; focusNewCode(); return }
    if (showExitModifyWarning.value) {
      showExitModifyWarning.value = false;
      nextTick(() => lastFocusedEl.value?.focus());
      return
    }

    // New logic: If focused on a row input (code, qty, rate, discount, etc.), just blur it first
    const activeEl = document.activeElement
    if (activeEl && activeEl.tagName === 'INPUT') {
      // Check if it's one of the grid inputs (including new entry row)
      const isGridInput = activeEl === newCodeInput.value || 
                          activeEl === newQtyInput.value || 
                          Object.values(inputRefs).includes(activeEl)

      if (isGridInput) {
        activeEl.blur()
        return // Just blur, keep selectedRow intact
      }
    }

    // 1. If in "Modify Bill" mode (editing an existing draft)
    if (savedInvoiceName.value && !billSaved.value && billDocStatus.value === 0) {
      if (selectedRow.value !== -1 || newItemCode.value || (newPending.value && newPending.value.item_name)) {
        lastFocusedEl.value = document.activeElement
        showExitModifyWarning.value = true
        return
      }
    }

    // 2. If entering/editing an item in the grid (not saved bill, new bill)
    if (billDocStatus.value === 0 && !billSaved.value && !savedInvoiceName.value) {
      // If a row is selected or we have pending barcode entry
      if (selectedRow.value !== -1 || newItemCode.value || (newPending.value && newPending.value.item_name)) {
        selectedRow.value = -1
        newItemCode.value = ''
        newPending.value = { item_name: '', uom: '', rate: null }
        focusNewCode()
        return
      }

      // 2. If item table has items, ask to clear
      if (activeItems.value.length > 0) {
        showClearBillWarning.value = true
        return
      }
    }

    // 3. If item table is empty or bill is saved/submitted, take to dashboard
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

onMounted(async () => {
  // Listen for global shortcut events
  window.addEventListener('wb-global-ledger-search', openCustomerSearch);
  window.addEventListener('wb-global-item-search', () => openSearch('', null));
  window.addEventListener('wb-global-date-focus', () => dateInput.value?.focus());
  window.addEventListener('storage', handleStorageChange);
  window.addEventListener('keydown', handleSeriesNumberKey);

  fetchDropdownOptions()
  fetchSidebarBills()

  // Ensure item cache is populated (TTL 5 mins)
  if (!cachedItems.value.length || (Date.now() - lastSync.value) > 5 * 60 * 1000) {
    refreshItemCache('Sales', priceList.value, defaultWarehouse.value)
  }
  // Always refresh discount rules for every new invoice session
  refreshDiscountRuleCache()

  const targetInvoice = props.isSubWindow ? props.invoiceName : route.query.invoice
  if (targetInvoice) {
    // For modify bill: wait for series/settings to fully load FIRST so
    // syncSeriesConfig doesn't race against the invoice's saved price list.
    await fetchSeriesList()
    loadInvoice(targetInvoice)
  } else {
    fetchSeriesList()
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

/* Hide scrollbars but keep functionality */
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
