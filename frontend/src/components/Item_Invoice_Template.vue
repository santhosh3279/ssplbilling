<template>
  <div class="flex h-full overflow-hidden bg-slate-900 text-slate-200 font-sans">
    <!-- Optional Sidebar (based on SalesEntry) -->
    <aside v-if="showSidebar" class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
      <slot name="sidebar">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-slate-500">{{ sidebarTitle }}</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-slate-700 p-0 bg-slate-900">
          <button @click="$emit('sidebar-date-change', -1)" class="rounded p-2 text-xl text-slate-500 hover:bg-slate-800 hover:text-slate-300">&larr;</button>
          <div class="flex-1 text-center font-bold text-slate-300 text-lg">{{ sidebarDate || 'Select Date' }}</div>
          <button @click="$emit('sidebar-date-change', 1)" class="rounded p-2 text-xl text-slate-500 hover:bg-slate-800 hover:text-slate-300">&rarr;</button>
        </div>

        <!-- Search & Series Filters -->
        <div class="flex flex-col gap-2 border-b border-slate-700 p-3 bg-slate-800/20">
          <input 
            type="text" 
            :value="sidebarSearch"
            @input="$emit('update:sidebarSearch', $event.target.value)"
            placeholder="Search invoice/cust..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-[1px] text-2xl text-slate-300 outline-none focus:border-blue-500"
          />
          <select
            :value="sidebarSeries"
            @change="$emit('update:sidebarSeries', $event.target.value)"
            class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-[1px] text-2xl text-slate-300 outline-none focus:border-blue-500"
          >
            <option value="">All Series</option>
            <option v-for="s in availableSeries" :key="s" :value="s">{{ s }}</option>
          </select>
          <button
            @click="$emit('toggle-draft-only')"
            class="w-full rounded border py-[1px] text-xl font-bold uppercase transition-colors"
            :class="draftOnly ? 'bg-amber-900/40 border-amber-500 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Bills' }}
          </button>
        </div>

        <!-- Bill List -->
        <div class="flex-1 overflow-y-auto scrollbar-none">
          <slot name="sidebar-list">
            <div v-if="sidebarLoading" class="p-4 text-center text-lg text-slate-500">Loading...</div>
            <div v-else-if="!sidebarItems.length" class="p-4 text-center text-lg text-slate-600 italic">No bills found</div>
            <div 
              v-for="(inv, idx) in sidebarItems" 
              :key="inv.name"
              @click="$emit('select-sidebar-item', inv)"
              class="group cursor-pointer border-b border-slate-800 px-2 py-1 transition-colors outline-none hover:bg-slate-800"
              :class="{ 'bg-blue-900/20 border-l-2 border-l-blue-500': selectedSidebarItemName === inv.name }"
            >
              <div class="flex items-center justify-between gap-1">
                <div class="flex items-center gap-1.5 truncate min-w-0">
                  <span class="h-2 w-2 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-green-500' : 'bg-red-500'"></span>
                  <span class="truncate font-mono text-2xl text-blue-400 group-hover:text-blue-300">{{ inv.name }}</span>
                </div>
                <span class="shrink-0 font-mono font-normal text-4xl tabular-nums text-slate-200">{{ inv.grand_total }}</span>
              </div>
              <div class="truncate text-2xl text-slate-400">
                {{ inv.customer_name }}
              </div>
            </div>
          </slot>
        </div>
      </slot>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 flex-col overflow-hidden bg-slate-900">
      <!-- Top Nav Bar -->
      <div class="flex items-center justify-between border-b border-slate-700/60 bg-slate-800/60 px-4 py-1">
        <div class="flex items-center gap-3">
          <button v-if="showBackButton" class="rounded px-2 py-0.5 text-xs text-slate-400 hover:bg-slate-700" @click="$emit('back')">&larr; Back</button>
          <span v-if="showBackButton" class="text-slate-600 text-xs">|</span>
          <span class="text-xs font-semibold text-slate-300">{{ title }}</span>
        </div>
        <div class="flex items-center gap-3 text-[10px] text-slate-400">
          <slot name="header-right"></slot>
        </div>
      </div>

      <!-- Header Bar (Series / Customer / Date) -->
      <div class="border-b border-slate-700 bg-slate-800 px-4 py-2">
        <div class="flex items-center gap-6">
          <slot name="header-bar">
            <!-- Default Header Layout -->
            <div v-if="docNumber" class="flex items-center gap-2 border-l border-slate-700 pl-6">
              <label class="text-[10px] uppercase text-slate-500 whitespace-nowrap">No.</label>
              <div class="text-xl text-slate-100 tabular-nums">{{ docNumber }}</div>
            </div>

            <div class="flex-1 flex items-center gap-4 border-l border-slate-700 pl-6 overflow-hidden">
              <label class="text-[10px] font-bold uppercase text-slate-500 whitespace-nowrap">Party</label>
              <div class="text-2xl text-slate-100 truncate">{{ partyName || 'Not Selected' }}</div>
              <div v-if="partyDetails" class="flex items-center gap-3 min-w-0">
                <span class="truncate max-w-[350px] text-lg text-slate-400 font-normal leading-none">{{ partyDetails }}</span>
              </div>
            </div>

            <div v-if="docDate" class="flex items-center gap-3 border-l border-slate-700 pl-6 whitespace-nowrap">
              <label class="text-[10px] font-bold uppercase text-slate-500">Date</label>
              <div class="text-xl text-slate-100 tabular-nums">{{ docDate }}</div>
            </div>
          </slot>
        </div>
      </div>

      <!-- Items Table Area -->
      <div class="flex flex-[7] flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto overflow-x-hidden scrollbar-none">
          <table class="w-full text-sm border-collapse border-l border-t border-slate-700">
            <thead>
              <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-lg font-bold uppercase tracking-wider text-slate-300 w-16">#</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-lg font-bold uppercase tracking-wider text-slate-300 w-48">Item Code</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-lg font-bold uppercase tracking-wider text-slate-300">Item Name</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-right text-lg font-bold uppercase tracking-wider text-slate-300 w-24">Qty</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-lg font-bold uppercase tracking-wider text-slate-300 w-24">UOM</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-right text-lg font-bold uppercase tracking-wider text-slate-300 w-32">Rate</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-right text-lg font-bold uppercase tracking-wider text-slate-300 w-24">Disc %</th>
                <th class="border-r border-b border-slate-700 px-2 py-2.5 text-right text-lg font-bold uppercase tracking-wider text-slate-300 w-32">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in items" :key="idx" class="border-b border-slate-700 hover:bg-slate-800/50">
                <slot name="row" :item="item" :index="idx">
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-500 text-xl font-mono text-center">{{ idx + 1 }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-blue-400 text-2xl font-mono">{{ item.item_code }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-200 text-2xl font-medium">{{ item.item_name }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-100 text-4xl font-mono text-right tabular-nums">{{ item.qty }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-400 text-xl">{{ item.uom || 'Nos' }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-100 text-3xl font-mono text-right tabular-nums">{{ item.rate }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-amber-500 text-2xl font-mono text-right">{{ item.discount_percentage || '0' }}</td>
                  <td class="px-2 py-1 border-r border-slate-700 text-slate-100 text-3xl font-mono text-right tabular-nums">{{ item.amount }}</td>
                </slot>
              </tr>
              <!-- Empty rows to maintain layout -->
              <tr v-for="i in Math.max(0, 10 - items.length)" :key="'empty-'+i" class="border-b border-slate-800/50">
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
                <td class="px-2 py-4 border-r border-slate-700"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bottom Panel (Summary / Actions) -->
      <div class="flex flex-[4] border-t border-slate-700 bg-slate-900 overflow-hidden">
        <!-- Insights / Left Column -->
        <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:360px;max-width:420px;">
          <slot name="bottom-left"></slot>
        </div>

        <!-- Settings / Middle Column -->
        <div class="flex flex-col border-r border-slate-700 bg-slate-900 overflow-y-auto scrollbar-none" style="min-width:236px;max-width:270px;">
          <slot name="bottom-middle">
            <div class="flex flex-col gap-2 p-2">
              <!-- Export/Import buttons -->
              <div class="flex gap-1">
                <button class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-sm font-bold uppercase text-slate-400">Export</button>
                <button class="flex-1 rounded border border-slate-700 bg-slate-800 py-1 text-sm font-bold uppercase text-slate-400">Import</button>
              </div>

              <!-- Price List -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Price List</label>
                <div class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-xl text-slate-200 truncate">{{ priceList }}</div>
              </div>

              <!-- Tax -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Tax</label>
                <div class="w-full rounded border border-slate-600 bg-slate-900 px-1 py-0.5 text-xl text-slate-200 truncate">{{ taxTemplate || '-- None --' }}</div>
                <label class="flex items-center gap-2 mt-1">
                  <input type="checkbox" :checked="isInclusiveTax" disabled class="h-4 w-4 rounded border-slate-600 accent-blue-500" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Inclusive Tax</span>
                </label>
              </div>

              <!-- Pricing Rules & Return -->
              <div class="flex flex-col gap-1.5 py-1">
                <label class="flex items-center gap-2">
                  <input type="checkbox" :checked="ignoreDiscountRule" disabled class="h-4 w-4 rounded border-slate-600 accent-amber-500" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Ignore Pricing Rule</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="checkbox" :checked="isReturn" disabled class="h-4 w-4 rounded border-slate-600 accent-red-500" />
                  <span class="text-slate-400 text-lg font-bold uppercase">Sale Return</span>
                </label>
              </div>

              <!-- Warehouse -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Warehouse</label>
                <div class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-lg text-slate-400 truncate">{{ warehouse || 'None' }}</div>
              </div>

              <!-- Cost Center -->
              <div class="flex flex-col gap-0.5">
                <label class="text-lg font-bold uppercase text-slate-600">Cost Center</label>
                <div class="w-full rounded border border-slate-700 bg-slate-900 px-1 py-0.5 text-lg text-slate-400 truncate">{{ costCenter || 'None' }}</div>
              </div>
            </div>
          </slot>
        </div>

        <!-- Summary / Right Column (Calculation Panel + Actions) -->
        <table class="flex-1 bg-slate-800/50 border-collapse text-xs border border-slate-700 h-full" style="table-layout:fixed">
          <colgroup>
            <col style="width:17%"><col style="width:18%"><col style="width:14%"><col style="width:51%">
          </colgroup>
          <thead>
            <tr class="bg-slate-800">
              <th class="px-2 text-left text-[10px] uppercase tracking-wider text-slate-500 border border-slate-700">Description</th>
              <th class="px-2 text-center text-[10px] uppercase tracking-wider text-slate-500 border border-slate-700">Entry</th>
              <th class="px-2 text-right text-[10px] uppercase tracking-wider text-slate-500 border border-slate-700">Amount</th>
              <th class="px-2 text-center text-[10px] uppercase tracking-wider text-slate-500 border border-slate-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            <slot name="calculation-rows">
              <!-- Default Calculation Rows (Props based) -->
              <!-- Item Discount -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Item Discount</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500 italic">Auto</td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-{{ itemDiscountTotal }}</td>
                <td class="border border-slate-700 px-2" rowspan="10">
                  <slot name="actions">
                    <div class="flex flex-col gap-2 h-full py-2">
                      <div class="text-4xl text-slate-500/80">{{ items.length }} items</div>
                      
                      <div class="rounded-xl border border-blue-500/40 bg-blue-950/60 p-3.5 shadow-2xl">
                        <div class="text-[9px] font-black uppercase tracking-[0.3em] text-blue-400/90 mb-1">Total Amount</div>
                        <div class="flex items-baseline gap-2 text-green-500/70">
                          <span class="text-[6mm] font-black">₹</span>
                          <span class="font-mono text-[10.5mm] font-black leading-none">{{ totalAmount }}</span>
                        </div>
                      </div>

                      <!-- Row 1: Save and Print -->
                      <div class="flex gap-2">
                        <button @click="$emit('save')" class="flex-1 rounded py-2.5 text-center text-xl font-semibold text-white bg-[#285A48] hover:bg-[#1e4538] transition-colors">Save</button>
                        <button @click="$emit('print')" class="flex-1 rounded border border-slate-600 bg-slate-800 py-2.5 text-center text-xl font-semibold text-slate-300 hover:bg-slate-700 transition-colors">Print</button>
                      </div>

                      <!-- Row 2: Cancel and Incentive -->
                      <div class="flex gap-2">
                        <button @click="$emit('cancel')" class="flex-1 rounded border border-red-900/50 bg-red-900/10 py-2.5 text-center text-xl font-semibold text-red-400 hover:bg-red-900/20 transition-colors">Cancel</button>
                        <button @click="$emit('incentive')" class="flex-1 rounded border border-indigo-700/50 bg-indigo-900/20 py-2.5 text-center text-xl font-semibold text-indigo-400 hover:bg-indigo-900/40 transition-colors">Incentive</button>
                      </div>
                    </div>
                  </slot>
                </td>
              </tr>
              <!-- Global Discount -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Discount</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500">
                  <div v-if="discountEntry" class="bg-slate-900 text-slate-200 font-mono text-xl py-1">{{ discountEntry }}</div>
                </td>
                <td class="px-2 text-right font-mono text-red-400 text-2xl border border-slate-700">-{{ discountAmt }}</td>
              </tr>
              <!-- Subtotal -->
              <tr class="bg-slate-800/40">
                <td class="px-2 text-lg text-slate-200/80 border border-slate-600">Subtotal</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-100 text-2xl border border-slate-600">{{ subtotal }}</td>
                <td class="border border-slate-600"></td>
              </tr>
              <!-- Freight -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Freight</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500">
                  <div v-if="freightEntry" class="bg-slate-900 text-slate-200 font-mono text-xl py-1">{{ freightEntry }}</div>
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ freightAmt }}</td>
              </tr>
              <!-- Packing -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Packing</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500">
                  <div v-if="packingEntry" class="bg-slate-900 text-slate-200 font-mono text-xl py-1">{{ packingEntry }}</div>
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ packingAmt }}</td>
              </tr>
              <!-- Loading -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Loading</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500">
                  <div v-if="loadingEntry" class="bg-slate-900 text-slate-200 font-mono text-xl py-1">{{ loadingEntry }}</div>
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ loadingAmt }}</td>
              </tr>
              <!-- Other -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Other</td>
                <td class="p-0 border-y border-slate-700 text-center text-[10px] text-slate-500">
                  <div v-if="otherEntry" class="bg-slate-900 text-slate-200 font-mono text-xl py-1">{{ otherEntry }}</div>
                </td>
                <td class="px-2 text-right font-mono text-blue-400 text-2xl border border-slate-700">+{{ otherAmt }}</td>
              </tr>
              <!-- Tax -->
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Tax</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-300 text-2xl border border-slate-700">+{{ totalTax }}</td>
              </tr>
              <tr v-for="i in 2" :key="i">
                <td class="px-2 border border-slate-700">&nbsp;</td>
                <td class="p-0 border border-slate-700"></td>
                <td class="px-2 border border-slate-700"></td>
              </tr>
            </slot>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Item_Invoice_Template.vue
 * A reusable UI template component based on SalesEntry.vue
 */

const props = defineProps({
  title: { type: String, default: 'Invoice' },
  showSidebar: { type: Boolean, default: true },
  sidebarTitle: { type: String, default: 'Modify Bills' },
  showBackButton: { type: Boolean, default: true },
  docNumber: { type: String, default: '' },
  partyName: { type: String, default: '' },
  partyDetails: { type: String, default: '' },
  docDate: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  
  // Sidebar Props
  sidebarDate: { type: String, default: '' },
  sidebarSearch: { type: String, default: '' },
  sidebarSeries: { type: String, default: '' },
  availableSeries: { type: Array, default: () => [] },
  draftOnly: { type: Boolean, default: false },
  sidebarLoading: { type: Boolean, default: false },
  sidebarItems: { type: Array, default: () => [] },
  selectedSidebarItemName: { type: String, default: '' },

  // Settings Panel Props
  priceList: { type: String, default: 'Standard Selling' },
  taxTemplate: { type: String, default: '' },
  isInclusiveTax: { type: Boolean, default: false },
  ignoreDiscountRule: { type: Boolean, default: false },
  isReturn: { type: Boolean, default: false },
  warehouse: { type: String, default: '' },
  costCenter: { type: String, default: '' },

  // Calculation Panel Props
  itemDiscountTotal: { type: [Number, String], default: '0.00' },
  discountEntry: { type: String, default: '' },
  discountAmt: { type: [Number, String], default: '0.00' },
  subtotal: { type: [Number, String], default: '0.00' },
  freightEntry: { type: String, default: '' },
  freightAmt: { type: [Number, String], default: '0.00' },
  packingEntry: { type: String, default: '' },
  packingAmt: { type: [Number, String], default: '0.00' },
  loadingEntry: { type: String, default: '' },
  loadingAmt: { type: [Number, String], default: '0.00' },
  otherEntry: { type: String, default: '' },
  otherAmt: { type: [Number, String], default: '0.00' },
  totalTax: { type: [Number, String], default: '0.00' },
  totalAmount: { type: [Number, String], default: '0.00' }
})

const emit = defineEmits([
  'back', 'save', 'print', 'cancel', 'incentive',
  'sidebar-date-change', 'update:sidebarSearch', 'update:sidebarSeries', 
  'toggle-draft-only', 'select-sidebar-item'
])
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
