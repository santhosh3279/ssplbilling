<template>
  <div class="flex h-full overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)] font-sans">
    <!-- Optional Sidebar -->
    <aside v-if="showSidebar" class="flex w-[15%] flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden shrink-0">
      <slot name="sidebar">
        <div class="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] p-2 text-center">
          <div class="text-xl font-bold uppercase tracking-wider text-[var(--color-text-muted)]">{{ sidebarTitle }}</div>
        </div>
        
        <!-- Date Filter -->
        <div class="flex items-center gap-1 border-b border-[var(--color-border)] p-0 bg-[var(--color-bg)]">
          <button @click="$emit('sidebar-date-change', -1)" class="rounded p-2 text-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]">&larr;</button>
          <div class="flex-1 text-center font-bold text-[var(--color-text)] text-lg">{{ formatDate(sidebarDate) }}</div>
          <button @click="$emit('sidebar-date-change', 1)" class="rounded p-2 text-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]">&rarr;</button>
        </div>

        <!-- Search & Series Filters -->
        <div class="flex flex-col gap-2 border-b border-[var(--color-border)] p-3 bg-[var(--color-surface-raised)]/20">
          <div class="relative group">
            <input
              ref="sidebarSearchRef"
              type="text"
              :value="sidebarSearch"
              @input="$emit('update:sidebarSearch', $event.target.value)"
              placeholder="Search..."
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-10 pr-3 text-[15px] font-bold text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:border-[var(--color-focus)] focus:ring-4 focus:ring-[var(--color-focus)]/10 transition-all"
            />
            <svg class="absolute left-3.5 top-2.5 text-[var(--color-text-muted)] group-focus-within:text-[var(--color-info)] transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
          <div class="relative series-dropdown-container">
            <button
              @click="showSeriesDropdown = !showSeriesDropdown"
              class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-1.5 px-3 text-[15px] font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-focus)] transition-all text-left flex justify-between items-center h-9"
            >
              <span class="truncate">{{ sidebarSeries.length === availableSeries.length ? 'All Series' : (sidebarSeries.length > 0 ? sidebarSeries[0] + (sidebarSeries.length > 1 ? '..' : '') : 'None') }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" :class="{'rotate-180': showSeriesDropdown}" class="transition-transform"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            
            <!-- Dropdown Menu -->
            <div v-if="showSeriesDropdown" class="absolute top-full left-0 mt-1 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-2xl z-50 py-2 max-h-64 overflow-y-auto custom-scrollbar">
              <div class="px-3 py-1.5 border-b border-[var(--color-border)] mb-1 flex items-center gap-2 hover:bg-[var(--color-surface-raised)] cursor-pointer select-none" @click="toggleAllSeries">
                <input 
                  type="checkbox" 
                  :checked="sidebarSeries.length === availableSeries.length" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-bold uppercase tracking-wider">All Series</span>
              </div>
              <div v-for="s in availableSeries" :key="s" class="px-3 py-1.5 flex items-center gap-2 hover:bg-[var(--color-surface-raised)] cursor-pointer select-none" @click="toggleSeries(s)">
                <input 
                  type="checkbox" 
                  :checked="isSeriesSelected(s)" 
                  class="rounded border-[var(--color-border)] text-[var(--color-info)] focus:ring-[var(--color-focus)] h-3 w-3 pointer-events-none" 
                />
                <span class="text-[13px] font-bold uppercase tracking-wider">{{ s }}</span>
              </div>
            </div>
          </div>
          <button
            @click="$emit('toggle-draft-only')"
            class="w-full rounded-xl border py-1.5 text-[10px] font-bold uppercase transition-all"
            :class="draftOnly ? 'bg-[var(--color-warning)]/40 border-[var(--color-warning)] text-[var(--color-warning)] shadow-sm' : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'"
          >
            {{ draftOnly ? 'Drafts Only' : 'All Items' }}
          </button>
        </div>

        <!-- Item List -->
        <div ref="sidebarListRef" class="flex-1 overflow-y-auto scrollbar-none">
          <slot name="sidebar-list">
            <div v-if="sidebarLoading" class="p-4 text-center text-lg text-[var(--color-text-muted)]">Loading...</div>
            <div v-else-if="!sidebarItems.length" class="p-4 text-center text-lg text-[var(--color-text-muted)] italic">No items found</div>
            <div
              v-for="(inv, idx) in sidebarItems"
              :key="inv.name"
              :ref="el => setSidebarItemRef(el, idx)"
              tabindex="0"
              @click="$emit('select-sidebar-item', inv)"
              @keydown.enter="$emit('select-sidebar-item', inv)"
              @keydown.up.prevent="navigateSidebar(idx, -1)"
              @keydown.down.prevent="navigateSidebar(idx, 1)"
              class="group cursor-pointer border-b border-[var(--color-border)] px-2 py-1 transition-colors outline-none hover:bg-[var(--color-surface-raised)] focus:bg-[var(--color-focus)] focus:border-l-2 focus:border-l-[var(--color-focus)]"
              :class="{ 'bg-[var(--color-focus)] border-l-2 border-l-[var(--color-focus)]': selectedSidebarItemName === inv.name }"
            >
              <div class="flex items-center justify-between gap-1">
                <div class="flex items-center gap-1.5 truncate min-w-0">
                  <span class="h-2 w-2 shrink-0 rounded-full" :class="inv.docstatus === 0 ? 'bg-[var(--color-success)]' : 'bg-[var(--color-danger)]'"></span>
                  <span class="truncate font-mono text-2xl group-hover:brightness-125 group-focus:text-[var(--color-text-on-focus)] group-focus:font-bold" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)] font-bold' : 'text-[var(--color-highlight)]'">{{ inv.name }}</span>
                </div>
                <span v-if="inv.total_qty" class="shrink-0 font-mono font-normal text-4xl tabular-nums group-focus:text-[var(--color-text-on-focus)]" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text)]'">{{ inv.total_qty }}</span>
              </div>
              <div v-if="inv.posting_date" class="truncate text-2xl group-focus:text-[var(--color-text-on-focus)]" :class="selectedSidebarItemName === inv.name ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">
                {{ formatDate(inv.posting_date) }}
              </div>
            </div>
          </slot>
        </div>
      </slot>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="flex flex-1 flex-col overflow-hidden bg-[var(--color-bg)]">
      <!-- Top Nav Bar -->
      <div
        class="flex items-center justify-between border-b border-[var(--color-border)]/60 px-4 py-2"
        :style="titleBarColor ? { backgroundColor: titleBarColor } : {}"
        :class="!titleBarColor ? 'bg-[var(--color-surface-raised)]/60' : ''"
      >
        <div class="flex items-center gap-3">
          <button v-if="showBackButton" class="rounded px-2 py-1 text-2xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]" @click="$emit('back')">&larr; Back</button>
          <span v-if="showBackButton" class="text-[var(--color-border)] text-2xl">|</span>
          <span class="text-2xl font-semibold text-[var(--color-text)]">{{ title }}</span>
        </div>
        <div class="flex items-center gap-3 text-xl text-[var(--color-text-muted)]">
          <slot name="header-right"></slot>
        </div>
      </div>

      <!-- Header Bar -->
      <div class="border-b border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-2">
        <div class="flex flex-col gap-2">
          <slot name="header-bar">
            <div class="flex items-center gap-6 overflow-hidden">
              <div v-if="docNumber" class="flex items-center gap-2 border-r border-[var(--color-border)] pr-6 shrink-0">
                <div class="text-4xl text-[var(--color-text)] tabular-nums font-mono font-bold">{{ docNumber }}</div>
              </div>

              <div class="flex-1 flex items-baseline gap-6 overflow-hidden">
                <div v-if="partyName" class="flex items-baseline gap-3 shrink-0">
                  <label class="text-xl font-bold uppercase text-[var(--color-text-muted)] whitespace-nowrap">Party</label>
                  <div class="text-5xl font-bold text-[var(--color-text)] truncate max-w-[600px]">{{ partyName }}</div>
                </div>
              </div>

              <div v-if="docDate" class="flex items-center gap-3 border-l border-[var(--color-border)] pl-6 whitespace-nowrap ml-auto">
                <label class="text-xl font-bold uppercase text-[var(--color-text-muted)]">Date</label>
                <div class="flex items-center gap-1">
                  <button @click="$emit('doc-date-change', -1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&larr;</button>
                  <div class="text-3xl text-[var(--color-text)] tabular-nums">{{ formatDate(docDate) }}</div>
                  <button @click="$emit('doc-date-change', 1)" class="rounded p-0.5 text-3xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] leading-none flex items-center">&rarr;</button>
                </div>
              </div>
            </div>
          </slot>
        </div>
      </div>

      <!-- Items Table Area -->
      <div class="flex flex-[7] flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto overflow-x-hidden scrollbar-none">
          <table class="w-full text-sm border-collapse border-l border-t border-[var(--color-border)]">
            <thead>
              <tr class="sticky top-0 z-10 bg-[var(--color-lowlight)] border-b border-[var(--color-border)]">
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-8">#</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Barcode</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)]">Item Name</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Qty</th>
                <th class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-left text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-24">UOM</th>
                <th v-if="showRate" class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Rate</th>
                <th v-if="showAmount" class="border-r border-b border-[var(--color-border)] px-1.5 py-2 text-right text-4xl font-normal uppercase tracking-wider text-[var(--color-text)] w-32">Value</th>
                <th class="border-b border-[var(--color-border)] w-12"></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(item, idx) in items" :key="idx">
                <slot name="row" :item="item" :index="idx">
                  <tr class="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]/50">
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl font-mono text-center">{{ idx + 1 }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-highlight)] text-4xl font-mono">{{ item.item_code }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-4xl font-medium">{{ item.item_name }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-6xl font-mono text-right tabular-nums">{{ item.qty }}</td>
                    <td class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-3xl">{{ item.uom || 'Nos' }}</td>
                    <td v-if="showRate" class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ item.rate }}</td>
                    <td v-if="showAmount" class="px-2 py-1 border-r border-[var(--color-border)] text-[var(--color-text)] text-5xl font-mono text-right tabular-nums">{{ item.amount || (item.qty * item.rate).toFixed(2) }}</td>
                    <td class="px-2 py-1 text-center">
                      <button class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/20 hover:text-[var(--color-danger)]" @click="$emit('delete-item', idx)">&times;</button>
                    </td>
                  </tr>
                </slot>
              </template>
              <slot name="table-extra-rows"></slot>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bottom Panel (Summary / Actions) -->
      <div class="flex flex-[3] border-t border-[var(--color-border)] bg-[var(--color-bg)] overflow-hidden">
        <!-- Insights / Left Column -->
        <div v-if="showBottomLeft" class="flex flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-y-auto scrollbar-none" style="min-width:360px;max-width:420px;">
          <slot name="bottom-left"></slot>
        </div>

        <!-- Settings / Middle Column -->
        <div v-if="showBottomMiddle" class="flex flex-col border-r border-[var(--color-border)] bg-[var(--color-bg)] overflow-y-auto scrollbar-none" style="min-width:236px;max-width:270px;">
          <slot name="bottom-middle">
            <div class="flex flex-col gap-4 p-4">
              <div v-if="warehouse" class="flex flex-col gap-1">
                <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Warehouse</label>
                <div class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-xl text-[var(--color-text)] truncate">{{ warehouse }}</div>
              </div>
            </div>
          </slot>
        </div>

        <!-- Actions / Right Column -->
        <div class="flex-1 flex border-l border-[var(--color-border)] bg-[var(--color-surface-raised)]/30">
          <slot name="calculation-rows">
            <div class="flex flex-1 items-stretch p-4 gap-6">
              <!-- Summary Card -->
              <div class="flex-[3] flex flex-col justify-center gap-4">
                <div class="rounded-2xl border-2 border-[var(--color-highlight)]/30 bg-[var(--color-highlight)]/5 p-6 shadow-xl flex justify-between items-baseline">
                  <div class="text-2xl font-black uppercase tracking-[0.2em] text-[var(--color-highlight)]">{{ totalLabel }}</div>
                  <div class="flex items-baseline gap-3 font-bold text-[var(--color-success)]">
                    <span v-if="showTotalCurrency" class="text-4xl font-black">₹</span>
                    <span class="font-mono text-7xl font-black leading-none tabular-nums">{{ totalAmount }}</span>
                  </div>
                </div>
                <div v-if="itemCount !== null" class="text-2xl font-bold text-[var(--color-text-muted)] px-2">
                  Total {{ itemCount }} items
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex-[2] flex flex-col justify-center gap-3">
                <button 
                  ref="saveBtnRef" 
                  @click="$emit('save')" 
                  class="rounded-xl py-5 text-center text-4xl font-bold text-[var(--color-text-on-highlight)] bg-[var(--color-highlight)] hover:brightness-110 transition-all uppercase shadow-lg active:scale-[0.98] focus:ring-4 focus:ring-[var(--color-focus)]/50"
                >
                  {{ saveButtonText }}
                </button>
                <div class="flex gap-3">
                  <button 
                    @click="$emit('cancel')" 
                    class="flex-1 rounded-xl border-2 border-[#C2A96E] bg-[#D4B896] py-4 text-center text-3xl font-bold text-[#4A3520] hover:brightness-105 transition-all shadow-lg active:scale-[0.98]"
                  >
                    Cancel
                  </button>
                  <button 
                    v-if="isDraft && isReadOnly" 
                    @click="$emit('submit')" 
                    class="flex-1 rounded-xl border-2 border-[var(--color-success)] bg-[var(--color-success)]/10 py-4 text-center text-3xl font-bold text-[var(--color-success)] hover:bg-[var(--color-success)]/20 transition-all uppercase shadow-lg active:scale-[0.98]"
                  >
                    Submit
                  </button>
                  <button 
                    v-else-if="showPrintButton"
                    :disabled="!isReadOnly"
                    @click="$emit('print')" 
                    class="flex-1 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] py-4 text-center text-3xl font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition-all shadow-lg active:scale-[0.98] disabled:opacity-50"
                  >
                    Print
                  </button>
                </div>
              </div>
            </div>
          </slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Stock_Template.vue
 * A reusable UI template component for stock-related documents (Store Transfer, Reconciliation, etc.)
 */

import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Stock Entry' },
  showSidebar: { type: Boolean, default: true },
  sidebarTitle: { type: String, default: 'History' },
  showBackButton: { type: Boolean, default: true },
  titleBarColor: { type: String, default: '' },
  docNumber: { type: String, default: '' },
  partyName: { type: String, default: '' },
  docDate: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  
  // Sidebar Props
  sidebarDate: { type: String, default: '' },
  sidebarSearch: { type: String, default: '' },
  sidebarSeries: { type: Array, default: () => [] },
  availableSeries: { type: Array, default: () => [] },
  draftOnly: { type: Boolean, default: false },
  sidebarLoading: { type: Boolean, default: false },
  sidebarItems: { type: Array, default: () => [] },
  selectedSidebarItemName: { type: String, default: '' },

  // Layout Props
  showBottomLeft: { type: Boolean, default: true },
  showBottomMiddle: { type: Boolean, default: true },
  showRate: { type: Boolean, default: true },
  showAmount: { type: Boolean, default: true },
  showPrintButton: { type: Boolean, default: true },
  showTotalCurrency: { type: Boolean, default: true },

  // Summary Props
  totalLabel: { type: String, default: 'Total Value' },
  totalAmount: { type: [Number, String], default: '0.00' },
  itemCount: { type: [Number, String], default: null },
  warehouse: { type: String, default: '' },

  // State Props
  saveButtonText: { type: String, default: 'Save' },
  isReadOnly: { type: Boolean, default: false },
  isDraft: { type: Boolean, default: false }
})

const emit = defineEmits([
  'back', 'save', 'print', 'cancel', 'submit',
  'doc-date-change', 'sidebar-date-change', 'update:sidebarDate', 'update:sidebarSearch', 'update:sidebarSeries',
  'toggle-draft-only', 'select-sidebar-item', 'delete-item'
])

const sidebarSearchRef = ref(null)
const sidebarListRef = ref(null)
const showSeriesDropdown = ref(false)
const saveBtnRef = ref(null)
const sidebarItemRefs = new Map()

function setSidebarItemRef(el, idx) {
  if (el) sidebarItemRefs.set(idx, el)
  else sidebarItemRefs.delete(idx)
}

function toggleAllSeries() {
  if (props.sidebarSeries.length === props.availableSeries.length) {
    emit('update:sidebarSeries', [])
  } else {
    emit('update:sidebarSeries', [...props.availableSeries])
  }
}

function toggleSeries(s) {
  const current = [...props.sidebarSeries]
  const idx = current.indexOf(s)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(s)
  }
  emit('update:sidebarSeries', current)
}

function isSeriesSelected(s) {
  return props.sidebarSeries.includes(s)
}

function navigateSidebar(idx, dir) {
  const target = sidebarItemRefs.get(idx + dir)
  if (target) {
    target.focus()
    target.scrollIntoView({ block: 'nearest' })
  }
}

watch(() => props.selectedSidebarItemName, (newVal) => {
  if (!newVal) return
  nextTick(() => {
    const idx = props.sidebarItems.findIndex(inv => inv.name === newVal)
    if (idx !== -1) {
      const el = sidebarItemRefs.get(idx)
      if (el) {
        el.focus({ preventScroll: true })
        el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
      }
    }
  })
})

defineExpose({
  focusSidebar: () => sidebarSearchRef.value?.focus(),
  focusSidebarList: () => sidebarListRef.value?.querySelector('[tabindex="0"]')?.focus(),
  focusSaveBtn: () => saveBtnRef.value?.focus(),
})

function formatDate(dateString) {
  if (!dateString) return 'Select Date'
  const d = new Date(dateString)
  if (isNaN(d)) return dateString
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}
</style>
