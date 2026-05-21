<template>
  <div 
    :class="isSubWindow ? 'fixed inset-0 z-[150] flex items-center justify-center bg-black/80 backdrop-blur-md p-4' : 'min-h-screen bg-[var(--color-bg)] flex flex-col'"
    class="font-sans text-[var(--color-text)]"
  >
    <div 
      :class="isSubWindow ? 'flex h-[90vh] w-[95vw] flex-col overflow-hidden rounded-3xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl relative' : 'flex flex-1 flex-col'"
    >
      <!-- Nav Bar -->
      <nav 
        :class="isSubWindow ? 'h-16' : 'fixed top-0 left-0 right-0 h-16'"
        class="z-50 flex shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 px-6 backdrop-blur-xl"
      >
        <div class="flex items-center gap-6">
          <button
            class="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-xs font-bold text-[var(--color-text)] transition hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text-on-highlight)] active:scale-95"
            @click="handleBack"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            {{ isSubWindow ? 'Close' : 'Dashboard' }}
          </button>
          <div class="h-6 w-px bg-[var(--color-surface)]"></div>
          <h1 class="text-lg font-black tracking-tight text-[var(--color-text)] uppercase">
            🏷️ Barcode <span class="text-[var(--color-text-muted)] font-light">Printing</span>
          </h1>
          <span v-if="localBillNo" class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-xs font-bold text-[var(--color-info)]">
            {{ localBillNo }}
          </span>
        </div>

        <div class="flex items-center gap-3">
          <span v-if="itemsToPrint.length" class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 px-3 py-1.5 text-xs font-bold text-[var(--color-text-muted)]">
            {{ itemsToPrint.length }} item{{ itemsToPrint.length !== 1 ? 's' : '' }}
          </span>
        </div>
      </nav>

      <!-- Body -->
      <div 
        class="flex flex-1 gap-4 p-4 overflow-hidden"
        :class="!isSubWindow ? 'pt-20' : ''"
      >
        <!-- LEFT: Printer / Template selects -->
        <div class="flex flex-col gap-3 w-64 flex-shrink-0 overflow-y-auto custom-scrollbar pr-1">
          <!-- Printer select -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 p-4 shrink-0">
            <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Printer</label>
            <div class="relative">
              <select v-model="selectedPrinter" :disabled="loadingResources || printing"
                class="w-full appearance-none rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-50">
                <option value="">— Select Printer —</option>
                <option v-for="p in printers" :key="p.name" :value="p.name">
                  {{ p.printer_name }} — {{ p.status }}{{ p.is_default ? ' ★' : '' }}
                </option>
              </select>
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">▾</span>
            </div>
            <p v-if="!printers.length && !loadingResources" class="mt-1.5 text-[10px] text-[var(--color-danger)]">No printers configured</p>
          </div>

          <!-- Template select -->
          <div class="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 p-4 shrink-0">
            <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Template</label>
            <div class="relative">
              <select v-model="selectedTemplate" :disabled="loadingResources || printing"
                class="w-full appearance-none rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-50">
                <option value="">— Select Template —</option>
                <option v-for="t in templates" :key="t.name" :value="t.name">
                  {{ t.template_name || t.name }}
                </option>
              </select>
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">▾</span>
            </div>
            <p v-if="!templates.length && !loadingResources" class="mt-1.5 text-[10px] text-[var(--color-danger)]">No Barcode templates</p>
          </div>

          <button
            @click="triggerPrint"
            :disabled="!canPrint || printing"
            class="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--color-supplier)] py-4 text-lg font-black text-[var(--color-text-on-highlight)] shadow-xl transition hover:brightness-110 active:scale-95 disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)] disabled:grayscale disabled:cursor-not-allowed uppercase tracking-widest"
          >
            <span v-if="printing" class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            {{ printing ? 'Sending…' : '🖨️ Print Barcodes' }}
          </button>

          <div v-if="loadingResources" class="text-center text-xs text-[var(--color-text-muted)] italic py-2">Loading…</div>

          <!-- Status -->
          <div v-if="statusMsg"
            class="rounded-xl px-4 py-3 text-sm font-bold text-center"
            :class="statusError ? 'bg-[var(--color-danger)]/50 border border-[var(--color-danger)] text-[var(--color-danger)]' : 'bg-[var(--color-success)]/50 border border-[var(--color-success)] text-[var(--color-success)]'">
            {{ statusMsg }}
          </div>

          <!-- Shortcuts hint -->
          <div class="mt-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/30 p-3 text-[10px] text-[var(--color-text-muted)] space-y-1">
            <div><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text-muted)]">Enter</kbd> Resolve item / add</div>
            <div><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text-muted)]">Tab</kbd> Move to qty</div>
            <div><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text-muted)]">↑ ↓</kbd> Navigate rows</div>
            <div><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-[var(--color-text-muted)]">Del</kbd> Remove row</div>
          </div>
        </div>

        <!-- RIGHT: Items table -->
        <div class="flex flex-1 flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/60">
          <!-- Table header -->
          <div class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-bg)]/60 px-4 py-2.5 flex-shrink-0">
            <div class="text-[10px] font-black uppercase tracking-widest text-[var(--color-text-muted)]">Items to Print</div>
            <button v-if="itemsToPrint.length && !printing"
              @click="itemsToPrint = []; selectedRow = -1; focusNewCode()"
              class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition font-bold">
              Clear All
            </button>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar">
            <table class="w-full text-2xl border-collapse border-l border-t border-[var(--color-border)]">
              <thead>
                <tr class="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                  <th class="w-8 border-r border-[var(--color-border)] px-2 py-1.5 text-left text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">#</th>
                  <th class="w-48 border-r border-[var(--color-border)] px-2 py-1.5 text-left text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Code</th>
                  <th class="border-r border-[var(--color-border)] px-2 py-1.5 text-left text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Item Name</th>
                  <th class="w-48 border-r border-[var(--color-border)] px-2 py-1.5 text-left text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Barcode</th>
                  <th class="w-24 border-r border-[var(--color-border)] px-2 py-1.5 text-left text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">UOM</th>
                  <th v-for="pl in availablePriceLists" :key="pl"
                    class="w-32 border-r border-[var(--color-border)] px-2 py-1.5 text-right text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                    {{ pl }}
                  </th>
                  <th class="w-48 border-r border-[var(--color-border)] px-2 py-1.5 text-right text-lg font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Qty</th>
                  <th class="w-8 border-[var(--color-border)]"></th>
                </tr>
              </thead>
              <tbody>
                <!-- Existing rows -->
                <tr
                  v-for="(item, idx) in itemsToPrint"
                  :key="idx"
                  :ref="el => setRowRef(el, idx)"
                  tabindex="-1"
                  class="cursor-pointer border-b border-[var(--color-border)] outline-none transition-colors"
                  :class="selectedRow === idx
                    ? 'bg-[var(--color-info)]/30 border-l-2 border-l-blue-500'
                    : 'hover:bg-[var(--color-surface-raised)]/30'"
                  @click="selectRow(idx)"
                  @keydown="onRowKeydown($event, idx)"
                >
                  <!-- # -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <span class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-surface)] text-xs font-bold text-[var(--color-text-muted)]">{{ idx + 1 }}</span>
                  </td>
                  <!-- Item Code -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <input
                      v-if="selectedRow === idx"
                      :ref="el => setRef(el, 'code', idx)"
                      v-model="item.item_code"
                      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-0.5 font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                      @input="onCodeInput(idx)"
                      @keydown="handleCodeKeydown($event, idx)"
                      @keydown.delete.stop
                    />
                    <span v-else class="font-mono text-[var(--color-text-muted)]">{{ item.item_code }}</span>
                  </td>
                  <!-- Item Name -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-[var(--color-text)] font-medium">{{ item.item_name || '—' }}</td>
                  <!-- Barcode -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <input
                      v-if="selectedRow === idx"
                      :ref="el => setRef(el, 'barcode', idx)"
                      v-model="item.barcode"
                      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-0.5 font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                      @keydown.enter.prevent="focusField('qty', idx)"
                      @keydown.tab.prevent="focusField('qty', idx)"
                    />
                    <span v-else class="font-mono text-[var(--color-text-muted)]">{{ item.barcode || '—' }}</span>
                  </td>
                  <!-- UOM -->
                  <td class="p-0 border-r border-[var(--color-border)]">
                    <select
                      v-if="selectedRow === idx && getItemUoms(item.item_code).length > 1"
                      :ref="el => setRef(el, 'uom', idx)"
                      v-model="item.uom"
                      class="w-full h-full bg-transparent px-2 py-1.5 font-mono text-xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/20"
                      @keydown.enter.prevent="focusField('barcode', idx)"
                      @keydown.tab.prevent="focusField('barcode', idx)"
                      @keydown.shift.tab.prevent="focusField('code', idx)"
                      @change="onUomChange(idx)"
                    >
                      <option v-for="u in getItemUoms(item.item_code)" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ u }}</option>
                    </select>
                    <span v-else class="block px-2 py-1.5 font-mono text-xl text-[var(--color-text-muted)]">{{ item.uom || 'Nos' }}</span>
                  </td>
                  <!-- Price List Rates -->
                  <td v-for="pl in availablePriceLists" :key="pl"
                    class="px-2 py-1.5 border-r border-[var(--color-border)] text-right font-mono text-xl text-[var(--color-text-muted)]">
                    {{ item.rates?.[pl]?.toFixed(2) || '0.00' }}
                  </td>
                  <!-- Qty -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-right">
                    <div v-if="selectedRow === idx" class="flex items-center justify-end gap-1.5">
                      <button @click.stop="item.qty = Math.max(1, item.qty - 1)"
                        class="h-8 w-8 rounded bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] font-bold text-xl">&minus;</button>
                      <input
                        :ref="el => setRef(el, 'qty', idx)"
                        type="number" v-model.number="item.qty" min="1"
                        class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-center font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                        @keydown.enter.prevent="moveToNextQty(idx)"
                        @keydown.tab.prevent="moveToNextQty(idx)"
                        @keydown.shift.tab.prevent="focusField('barcode', idx)"
                        @keydown.down.prevent="moveToNextQty(idx)"
                        @keydown.up.prevent="moveToPrevQty(idx)"
                      />
                      <button @click.stop="item.qty++"
                        class="h-8 w-8 rounded bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] font-bold text-xl">&plus;</button>
                    </div>
                    <span v-else class="font-mono text-[var(--color-text)] font-black text-3xl">{{ item.qty }}</span>
                  </td>
                  <!-- Remove -->
                  <td class="px-2 py-1.5 text-center">
                    <button @click.stop="itemsToPrint.splice(idx, 1); selectedRow = -1; focusNewCode()"
                      class="rounded px-1 py-0.5 text-[var(--color-text-muted)] hover:bg-[var(--color-danger)]/30 hover:text-[var(--color-danger)] transition text-2xl">&times;</button>
                  </td>
                </tr>

                <!-- NEW ENTRY ROW -->
                <tr class="border-b border-[var(--color-border)]"
                  :class="selectedRow === -1 ? 'bg-[var(--color-info)]/15' : 'bg-[var(--color-surface)]/20'">
                  <!-- # -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <span class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-info)]/50 text-xs font-bold text-[var(--color-info)]">+</span>
                  </td>
                  <!-- Item Code input -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <input
                      ref="newCodeInput"
                      v-model="newItemCode"
                      :disabled="printing"
                      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)]/50 disabled:opacity-50"
                      placeholder="Item code…"
                      @input="onNewCodeInput"
                      @keydown="handleNewCodeKeydown"
                    />
                  </td>
                  <!-- Pending item name -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl italic">{{ newPending.item_name || '—' }}</td>
                  <!-- Pending Barcode -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)]">
                    <input
                      ref="newBarcodeInput"
                      v-model="newPending.barcode"
                      class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                      placeholder="Barcode…"
                      @keydown.enter.prevent="focusNewQty"
                      @keydown.tab.prevent="focusNewQty"
                    />
                  </td>
                  <!-- Pending UOM -->
                  <td class="p-0 border-r border-[var(--color-border)]">
                    <select
                      v-if="newPending.item_code && getItemUoms(newPending.item_code).length > 1"
                      ref="newUomSelect"
                      v-model="newPending.uom"
                      class="w-full h-full bg-transparent px-2 py-1.5 font-mono text-xl text-[var(--color-text)] outline-none focus:bg-[var(--color-info)]/20"
                      @keydown.enter.prevent="focusNewBarcode"
                      @keydown.tab.prevent="focusNewBarcode"
                      @keydown.shift.tab.prevent="focusNewCode"
                      @change="onNewUomChange"
                    >
                      <option v-for="u in getItemUoms(newPending.item_code)" :key="u" :value="u" class="bg-[var(--color-bg)]">{{ u }}</option>
                    </select>
                    <span v-else class="block px-2 py-1.5 font-mono text-xl text-[var(--color-text-muted)]">{{ newPending.uom || '—' }}</span>
                  </td>
                  <!-- Pending Rates -->
                  <td v-for="pl in availablePriceLists" :key="pl"
                    class="px-2 py-1.5 border-r border-[var(--color-border)] text-right font-mono text-xl text-[var(--color-text-muted)] italic">
                    {{ newPending.rates?.[pl]?.toFixed(2) || '0.00' }}
                  </td>
                  <!-- Qty input -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-right">
                    <input
                      ref="newQtyInput"
                      v-model.number="newQty"
                      type="number" min="1"
                      :disabled="printing"
                      class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-1 text-center font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-50"
                      @keydown.enter.prevent="addNewItem"
                      @keydown.shift.tab.prevent="focusNewBarcode"
                    />
                  </td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <QuickItemSearch
      ref="quickSearchRef"
      :results="quickSearchResults"
      :query="quickSearchQuery"
      price-list="Standard Selling"
      search-type="Sales"
      :anchor-el="quickSearchAnchor"
      @select="onQuickSearchSelect"
      @close="quickSearchResults = []"
      @refresh="onQuickSearchRefresh"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useItemCache, searchItemsInCache } from '../services/itemCache.js'
import { frappeGet, frappePost, fetchItemPrice } from '../api.js'
import { useShortcuts, useSubwindow } from '../services/shortcutManager'
import QuickItemSearch from '../components/QuickItemSearch.vue'

const props = defineProps({
  isSubWindow: Boolean,
  billNo: String,
  items: Array
})

const emit = defineEmits(['close'])

const router = useRouter()
const route = useRoute()

useShortcuts({
  'ESCAPE': handleBack
}, props.isSubWindow ? 'subwindow' : 'local')

const { items: allItems, lookupItemInCache, refreshItemCache } = useItemCache()

// ── Price Lists ──────────────────────────────────────────────────────────────
const availablePriceLists = ref([])
try {
  availablePriceLists.value = JSON.parse(localStorage.getItem('wb-pricelist') || '[]')
} catch (e) {
  availablePriceLists.value = []
}

async function fetchAllRates(item) {
  if (!item.item_code) return
  const rates = {}
  
  // 1. Try to find in cache first
  const cached = lookupItemInCache(item.item_code)
  if (cached) {
    // Check per-UOM price lists if UOM is specified
    if (item.uom && cached.uom_price_lists) {
      Object.entries(cached.uom_price_lists).forEach(([plName, uomMap]) => {
        if (uomMap[item.uom] !== undefined) {
          rates[plName] = uomMap[item.uom]
        }
      })
    }
    // Check base price lists (if not already set by UOM check)
    if (cached.price_lists) {
      cached.price_lists.forEach(pl => {
        if (rates[pl.name] === undefined) {
          rates[pl.name] = pl.rate
        }
      })
    }
  }

  // 2. Fetch missing ones from API
  await Promise.all(availablePriceLists.value.map(async pl => {
    if (rates[pl] === undefined) {
      rates[pl] = await fetchItemPrice(item.item_code, pl, item.uom)
    }
  }))
  item.rates = rates
}

// ── Printer / Template ───────────────────────────────────────────────────────
const printers = ref([])
const templates = ref([])
const selectedPrinter = ref('')
const selectedTemplate = ref('')
const loadingResources = ref(false)

const SETTINGS_CACHE_KEY = 'wb-settings-v2'

async function fetchBarcodeForItem(itemCode) {
  const cached = lookupItemInCache(itemCode)
  if (cached && cached.barcode) return cached.barcode

  try {
    const res = await frappeGet('frappe.client.get_list', {
      doctype: 'Item Barcode',
      fields: ['barcode'],
      filters: { parent: itemCode },
      limit: 1
    })
    return res.length ? res[0].barcode : itemCode
  } catch (e) {
    return itemCode
  }
}

function getUserPrinterSettings() {
  try {
    const cachedTemplates = JSON.parse(localStorage.getItem('wb-printer-templates') || '[]')
    const cachedSettings = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const currentUser = cachedSettings?.data?._current_user || ''
    
    const userRows = cachedTemplates.filter(ps => ps.user === currentUser)
    return userRows.length ? userRows : cachedTemplates.filter(ps => !ps.user)
  } catch (e) {
    return []
  }
}

function syncPrinter() {
  const template = selectedTemplate.value
  if (!template || !printers.value.length) return

  const userRows = getUserPrinterSettings()
  const mapping = userRows.find(ps => ps.template === template)
  const targetPrinter = mapping?.printer || ''

  if (targetPrinter && printers.value.some(pr => pr.name === targetPrinter)) {
    selectedPrinter.value = targetPrinter
  } else {
    const userDefault = localStorage.getItem('wb-default-printer') || localStorage.getItem('wb-printer')
    if (userDefault && printers.value.some(pr => pr.name === userDefault)) {
      selectedPrinter.value = userDefault
    } else {
      const def = printers.value.find(pr => pr.is_default) || printers.value[0]
      if (def) selectedPrinter.value = def.name
    }
  }
}

watch(selectedTemplate, () => syncPrinter())

async function loadResources() {
  loadingResources.value = true
  try {
    const userRows = getUserPrinterSettings()
    
    // 1. Fetch all valid barcode templates
    const validTemplates = await frappeGet('frappe.client.get_list', {
      doctype: 'Print Template',
      filters: { document_type: 'Barcode_Prinitng', format_type: 'Barcode' },
      fields: ['name', 'template_name'],
      limit: 100
    })
    const validTemplateNames = validTemplates.map(f => f.name)

    if (userRows.length) {
      // 2. Filter cached user templates to only those that exist for this doctype
      const filteredTemplates = userRows
        .filter(r => r.template && validTemplateNames.includes(r.template))
        .map(r => ({ name: r.template, template_name: r.template }))
      
      // Deduplicate
      const uniqueTemplates = [...new Map(filteredTemplates.map(t => [t.name, t])).values()]
      const uniquePrinterNames = [...new Set(userRows.map(r => r.printer).filter(Boolean))]

      const allPrinters = await frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers')
      const filteredPrinters = (allPrinters || []).filter(p => uniquePrinterNames.includes(p.name))
      
      printers.value  = filteredPrinters.length ? filteredPrinters : (allPrinters || [])
      templates.value = uniqueTemplates.length ? uniqueTemplates : validTemplates
    } else {
      const [p] = await Promise.all([
        frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers'),
      ])
      printers.value  = p || []
      templates.value = validTemplates
    }

    if (templates.value.length) {
      selectedTemplate.value = templates.value[0].name
    }

    syncPrinter()
  } catch (e) {
    console.error('[BarcodePrintPage] loadResources failed', e)
  } finally {
    loadingResources.value = false
  }
}

// ── Item table state ─────────────────────────────────────────────────────────
const itemsToPrint = ref([])
const selectedRow = ref(-1)

// ── Quick Search state ───────────────────────────────────────────────────────
const quickSearchRef = ref(null)
const quickSearchResults = ref([])
const editQuickSearchRowIdx = ref(null) // null for NEW row, index for existing rows
const quickSearchAnchor = computed(() => {
  if (editQuickSearchRowIdx.value !== null) {
    return fieldRefs[editQuickSearchRowIdx.value]?.code
  }
  return newCodeInput.value
})
const quickSearchQuery = computed(() => {
  if (editQuickSearchRowIdx.value !== null) {
    return itemsToPrint.value[editQuickSearchRowIdx.value]?.item_code || ''
  }
  return newItemCode.value
})

// Row refs for focus management (like SalesEntry)
const rowRefs = {}
const fieldRefs = {}
function setRowRef(el, idx) { if (el) rowRefs[idx] = el; else delete rowRefs[idx] }
function setRef(el, field, idx) {
  if (!fieldRefs[idx]) fieldRefs[idx] = {}
  if (el) fieldRefs[idx][field] = el; else delete fieldRefs[idx]?.[field]
}
function focusField(field, idx) {
  nextTick(() => fieldRefs[idx]?.[field]?.focus())
}

// New entry row refs
const newCodeInput = ref(null)
const newQtyInput = ref(null)
const newUomSelect = ref(null)
const newBarcodeInput = ref(null)
const newItemCode = ref('')
const newQty = ref(1)
const newPending = reactive({ item_code: '', item_name: '', uom: '', barcode: '', rates: {} })

function getItemUoms(itemCode) {
  const cached = lookupItemInCache(itemCode)
  if (!cached?.uoms) return []
  return cached.uoms.map(u => u.uom)
}
function focusNewCode() { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty() {
  nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() })
}
function focusNewUom() { nextTick(() => newUomSelect.value?.focus()) }
function focusNewBarcode() { nextTick(() => newBarcodeInput.value?.focus()) }
function focusAfterCode(idx) {
  if (getItemUoms(itemsToPrint.value[idx]?.item_code).length > 1) focusField('uom', idx)
  else focusField('barcode', idx)
}
function focusNewAfterCode() {
  if (newPending.item_code && getItemUoms(newPending.item_code).length > 1) focusNewUom()
  else focusNewBarcode()
}

async function onUomChange(idx) {
  const row = itemsToPrint.value[idx]
  if (row) {
    // If UOM changed, try to find a specific barcode for this UOM
    const cached = lookupItemInCache(row.item_code)
    if (cached?.barcodes_detailed) {
      const bcMatch = cached.barcodes_detailed.find(b => b.uom === row.uom)
      if (bcMatch) row.barcode = bcMatch.barcode
    }
    await fetchAllRates(row)
  }
}

async function onNewUomChange() {
  // If UOM changed, try to find a specific barcode for this UOM
  const cached = lookupItemInCache(newPending.item_code)
  if (cached?.barcodes_detailed) {
    const bcMatch = cached.barcodes_detailed.find(b => b.uom === newPending.uom)
    if (bcMatch) newPending.barcode = bcMatch.barcode
  }
  await fetchAllRates(newPending)
}

function selectQtyField(idx) {
  nextTick(() => { const el = fieldRefs[idx]?.qty; if (el) { el.focus(); el.select() } })
}
function focusQty(idx) {
  selectedRow.value = idx
  selectQtyField(idx)
}
function moveToNextQty(idx) {
  const next = idx + 1
  if (next < itemsToPrint.value.length) { selectedRow.value = next; selectQtyField(next) }
  else { selectedRow.value = -1; focusNewCode() }
}
function moveToPrevQty(idx) {
  const prev = idx - 1
  if (prev >= 0) { selectedRow.value = prev; selectQtyField(prev) }
}

// ── Item lookup from cache ────────────────────────────────────────────────────
function lookupItem(code) {
  const cached = lookupItemInCache(code)
  if (cached) {
    // If found via barcode, the cleanCode was the barcode
    if (cached._from_barcode) {
      cached._matched_barcode = code.trim()
    }
    return cached
  }
  // Fuzzy from full list
  const q = code.toLowerCase().trim()
  const found = allItems.value.find(i => {
    const itm_code = (i.item_code || '').toLowerCase()
    const barcode = (i.barcode || '').toLowerCase()
    const barcodesList = (i.barcodes || '').toLowerCase().split(',').map(b => b.trim())
    const detailed = i.barcodes_detailed || []
    return itm_code === q || barcode === q || barcodesList.includes(q) || detailed.some(b => (b.barcode || '').toLowerCase() === q)
  })
  if (found) {
    const item = { ...found }
    if ((item.item_code || '').toLowerCase() !== q) {
      item._matched_barcode = code.trim()
      // Resolve UOM for fuzzy barcode match
      if (item.barcodes_detailed) {
        const match = item.barcodes_detailed.find(b => (b.barcode || '').toLowerCase() === q)
        if (match && match.uom) {
          item.uom = match.uom
        }
      }
    }
    return item
  }
  return null
}

// ── Row navigation ────────────────────────────────────────────────────────────
function selectRow(idx) { selectedRow.value = idx; nextTick(() => rowRefs[idx]?.focus()) }
function moveRow(from, dir) {
  const next = from + dir
  if (next >= 0 && next < itemsToPrint.value.length) {
    selectedRow.value = next
    nextTick(() => rowRefs[next]?.focus())
  } else if (dir > 0) {
    selectedRow.value = -1
    focusNewCode()
  }
}
function moveToLastRow() {
  const last = itemsToPrint.value.length - 1
  if (last >= 0) { selectedRow.value = last; nextTick(() => rowRefs[last]?.focus()) }
}

// ── Quick Search handlers ───────────────────────────────────────────────────
function onQuickSearchSelect(item) {
  if (editQuickSearchRowIdx.value !== null) {
    // Existing row
    const idx = editQuickSearchRowIdx.value
    itemsToPrint.value[idx].item_code = item.item_code
    onCodeEnter(idx)
  } else {
    // New row
    newItemCode.value = item.item_code
    onNewCodeEnter()
  }
  quickSearchResults.value = []
  editQuickSearchRowIdx.value = null
}

function onQuickSearchRefresh() {
  const q = quickSearchQuery.value
  if (q.length >= 2) {
    quickSearchResults.value = searchItemsInCache(q)
  }
}

function onCodeInput(idx) {
  editQuickSearchRowIdx.value = idx
  const val = itemsToPrint.value[idx].item_code
  if (val.length >= 2) {
    quickSearchResults.value = searchItemsInCache(val)
  } else {
    quickSearchResults.value = []
  }
}

function onNewCodeInput() {
  editQuickSearchRowIdx.value = null
  if (newItemCode.value.length >= 2) {
    quickSearchResults.value = searchItemsInCache(newItemCode.value)
  } else {
    quickSearchResults.value = []
  }
}

function handleCodeKeydown(e, idx) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      quickSearchResults.value = []
      return
    }
  }
  
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Tab') { e.preventDefault(); focusAfterCode(idx) }
}

function handleNewCodeKeydown(e) {
  if (quickSearchResults.value.length > 0 && quickSearchRef.value) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
      e.preventDefault()
      quickSearchRef.value.handleQuickSearchKeydown(e)
      return
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      quickSearchResults.value = []
      return
    }
  }
  
  if (e.key === 'Enter') { e.preventDefault(); onNewCodeEnter() }
  else if (e.key === 'Tab') { e.preventDefault(); focusNewAfterCode() }
  else if (e.key === 'ArrowUp') { e.preventDefault(); moveToLastRow() }
}

function handleBack() {
  if (props.isSubWindow) emit('close')
  else router.push('/')
}

function onRowKeydown(e, idx) {
  if (e.target !== e.currentTarget) return
  if (e.key === 'ArrowDown')  { e.preventDefault(); moveRow(idx, 1) }
  else if (e.key === 'ArrowUp')   { e.preventDefault(); moveRow(idx, -1) }
  else if (e.key === 'Enter')     { e.preventDefault(); focusField('code', idx) }
  else if (e.key === 'Delete' || e.key === 'Backspace') {
    e.preventDefault()
    itemsToPrint.value.splice(idx, 1)
    selectedRow.value = -1
    focusNewCode()
  }
}

// ── Item code entry on existing row ─────────────────────────────────────────
async function onCodeEnter(idx) {
  const code = itemsToPrint.value[idx].item_code.trim()
  if (!code) return
  quickSearchResults.value = []
  const r = lookupItem(code)
  if (r) {
    const row = itemsToPrint.value[idx]
    row.item_code = r.item_code
    row.item_name = r.item_name
    row.uom = r.uom || 'Nos'
    
    if (r._matched_barcode) {
      row.barcode = r._matched_barcode
    } else {
      row.barcode = r.barcode || r.item_code
      fetchBarcodeForItem(r.item_code).then(bc => {
        if (bc) row.barcode = bc
      })
    }
    
    await fetchAllRates(row)
    focusAfterCode(idx)
  }
}

// ── New entry row handlers ────────────────────────────────────────────────────
async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) return
  quickSearchResults.value = []
  const r = lookupItem(code)
  if (r) {
    newItemCode.value = r.item_code
    newPending.item_code = r.item_code
    newPending.item_name = r.item_name
    newPending.uom = r.uom || 'Nos'
    
    if (r._matched_barcode) {
      newPending.barcode = r._matched_barcode
    } else {
      newPending.barcode = r.barcode || r.item_code
      fetchBarcodeForItem(r.item_code).then(bc => {
        if (bc) newPending.barcode = bc
      })
    }

    await fetchAllRates(newPending)
    nextTick(() => focusNewAfterCode())
  } else {
    newPending.item_code = code
    newPending.item_name = ''
    newPending.uom = 'Nos'
    newPending.barcode = code
    newPending.rates = {}
    focusNewBarcode()
  }
}

async function addNewItem() {
  const code = newPending.item_code || newItemCode.value.trim()
  if (!code) return

  itemsToPrint.value.push({
    item_code: code,
    item_name: newPending.item_name || code,
    uom: newPending.uom || 'Nos',
    qty: newQty.value,
    barcode: newPending.barcode || code,
    rates: { ...newPending.rates }
  })

  newItemCode.value = ''
  newQty.value = 1
  newPending.item_code = ''
  newPending.item_name = ''
  newPending.uom = ''
  newPending.barcode = ''
  newPending.rates = {}
  selectedRow.value = -1
  focusNewCode()
}

// ── Print ─────────────────────────────────────────────────────────────────────
const printing = ref(false)
const statusMsg = ref('')
const statusError = ref(false)
const localBillNo = ref('')

const canPrint = computed(() =>
  itemsToPrint.value.length > 0 && !!selectedPrinter.value && !!selectedTemplate.value
)

function setStatus(msg, isError = false) {
  statusMsg.value = msg
  statusError.value = isError
  if (!isError) setTimeout(() => { statusMsg.value = '' }, 4000)
}

async function triggerPrint() {
  if (!canPrint.value || printing.value) return
  printing.value = true
  statusMsg.value = ''
  try {
    const itemsWithRates = itemsToPrint.value.map(item => {
      const itm = { ...item }
      availablePriceLists.value.forEach((pl, idx) => {
        if (idx < 10) itm[`rate_${idx + 1}`] = item.rates?.[pl] || 0
      })
      return itm
    })

    const docName = await frappePost('ssplbilling.api.barcode_api.create_barcode_print_entry', {
      items: JSON.stringify(itemsWithRates),
      bill_no: localBillNo.value || null,
      price_lists: JSON.stringify(availablePriceLists.value.slice(0, 10))
    })
    if (!docName) { setStatus('Failed to create barcode entry.', true); return }
    const res = await frappePost(
      'printer_server_configuration.printer_server_configuration.api.print_document',
      {
        printer:        selectedPrinter.value,
        print_template: selectedTemplate.value,
        document_type:  'Barcode_Prinitng',
        document_name:  docName,
        title:          docName,
      },
    )
    setStatus(`✓ Sent to printer — Job ${res?.cups_job_id ?? ''}`)
  } catch (e) {
    setStatus(e?.message || 'Print failed. Check printer connection.', true)
  } finally {
    printing.value = false
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (!allItems.value.length) {
    try {
      await refreshItemCache('Sales')
    } catch (e) {
      console.warn('[BarcodePrintPage] Item cache refresh failed:', e)
    }
  }
  await loadResources()

  // Handle props or route query
  localBillNo.value = props.billNo || route.query.bill || ''
  
  if (props.items && props.items.length > 0) {
    itemsToPrint.value = await Promise.all(props.items.map(async i => {
      const bc = await fetchBarcodeForItem(i.item_code)
      const itm = {
        item_code: i.item_code,
        item_name: i.item_name,
        uom: i.uom || 'Nos',
        qty: i.qty || 1,
        barcode: bc || i.item_code
      }
      await fetchAllRates(itm)
      return itm
    }))
  } else {
    const rawItems = route.query.items
    if (rawItems) {
      try {
        const parsed = JSON.parse(decodeURIComponent(rawItems))
        itemsToPrint.value = await Promise.all(parsed.map(async i => {
          const bc = await fetchBarcodeForItem(i.item_code)
          const itm = {
            item_code: i.item_code,
            item_name: i.item_name,
            uom: i.uom || 'Nos',
            qty: i.qty || 1,
            barcode: bc || i.item_code
          }
          await fetchAllRates(itm)
          return itm
        }))
      } catch (e) {
        console.warn('[BarcodePrintPage] Failed to parse items from query', e)
      }
    }
  }

  nextTick(() => {
    if (itemsToPrint.value.length > 0) focusQty(0)
    else focusNewCode()
  })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #1e293b; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 8px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
