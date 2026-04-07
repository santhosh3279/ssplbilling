<template>
  <div class="flex h-full overflow-hidden bg-slate-900 text-slate-200 font-sans">
    <!-- Optional Sidebar (based on SalesEntry) -->
    <aside v-if="showSidebar" class="flex w-[15%] flex-col border-r border-slate-700 bg-slate-900 overflow-hidden shrink-0">
      <slot name="sidebar">
        <div class="border-b border-slate-700 bg-slate-800 p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-slate-500">{{ sidebarTitle }}</div>
        </div>
        <!-- Placeholder Search -->
        <div class="p-3 border-b border-slate-700 bg-slate-800/20">
          <input 
            type="text" 
            placeholder="Search..."
            class="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-300 outline-none"
          />
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <div class="text-xs text-slate-600 italic px-2 mb-2">Recent Invoices</div>
          <div v-for="i in 5" :key="i" class="p-2 border-b border-slate-800 hover:bg-slate-800 cursor-pointer rounded transition-colors mb-1">
            <div class="flex justify-between text-xs font-mono text-blue-400">
              <span>INV-00{{i}}</span>
              <span class="text-slate-200">₹{{ i * 1000 }}</span>
            </div>
            <div class="text-[10px] text-slate-500 truncate">Sample Customer {{i}}</div>
          </div>
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
                <th v-for="col in columns" :key="col.key" :class="col.class" class="border-r border-b border-slate-700 px-2 py-2.5 text-left text-lg font-bold uppercase tracking-wider text-slate-300">
                  {{ col.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in items" :key="idx" class="border-b border-slate-700 hover:bg-slate-800/50">
                <slot name="row" :item="item" :index="idx">
                  <td v-for="col in columns" :key="col.key" :class="col.cellClass" class="px-2 py-1 border-r border-slate-700 text-slate-300 text-xl">
                    {{ item[col.key] }}
                  </td>
                </slot>
              </tr>
              <slot name="after-rows"></slot>
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
          <slot name="bottom-middle"></slot>
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
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Subtotal</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-100 text-2xl border border-slate-700">{{ subtotal }}</td>
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
              <tr>
                <td class="px-2 text-lg text-slate-400/80 border border-slate-700">Tax</td>
                <td class="p-0 border-y border-slate-700"></td>
                <td class="px-2 text-right font-mono text-slate-300 text-2xl border border-slate-700">+{{ totalTax }}</td>
              </tr>
              <tr v-for="i in 6" :key="i">
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
  columns: { 
    type: Array, 
    default: () => [
      { key: 'item_code', label: 'Item Code', class: 'w-32' },
      { key: 'item_name', label: 'Item Name' },
      { key: 'qty', label: 'Qty', class: 'w-16', cellClass: 'text-right' },
      { key: 'rate', label: 'Rate', class: 'w-24', cellClass: 'text-right font-mono' },
      { key: 'amount', label: 'Amount', class: 'w-24', cellClass: 'text-right font-mono' },
    ] 
  },
  subtotal: { type: [Number, String], default: '0.00' },
  totalTax: { type: [Number, String], default: '0.00' },
  totalAmount: { type: [Number, String], default: '0.00' }
})

const emit = defineEmits(['back', 'save', 'print', 'cancel', 'incentive'])
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
