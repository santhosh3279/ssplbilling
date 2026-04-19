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
                      @keydown.enter.prevent="onCodeEnter(idx)"
                      @keydown.tab.prevent="focusField('qty', idx)"
                      @keydown.down.prevent="moveRow(idx, 1)"
                      @keydown.up.prevent="moveRow(idx, -1)"
                      @keydown.delete.stop
                    />
                    <span v-else class="font-mono text-[var(--color-text-muted)]">{{ item.item_code }}</span>
                  </td>
                  <!-- Item Name -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-[var(--color-text)] font-medium">{{ item.item_name || '—' }}</td>
                  <!-- Qty -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-right">
                    <div v-if="selectedRow === idx" class="flex items-center justify-end gap-1.5">
                      <button @click.stop="item.qty = Math.max(1, item.qty - 1)"
                        class="h-8 w-8 rounded bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] font-bold text-xl">&minus;</button>
                      <input
                        :ref="el => setRef(el, 'qty', idx)"
                        type="number" v-model.number="item.qty" min="1"
                        class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-0.5 text-center font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
                        @keydown.enter.prevent="moveRow(idx, 1)"
                        @keydown.tab.prevent="moveRow(idx, 1)"
                        @keydown.shift.tab.prevent="focusField('code', idx)"
                        @keydown.down.prevent="moveRow(idx, 1)"
                        @keydown.up.prevent="moveRow(idx, -1)"
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
                      @keydown.enter.prevent="onNewCodeEnter"
                      @keydown.tab.prevent="focusNewQty"
                      @keydown.up.prevent="moveToLastRow"
                    />
                  </td>
                  <!-- Pending item name -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-[var(--color-text-muted)] text-xl italic">{{ newPending.item_name || '—' }}</td>
                  <!-- Qty input -->
                  <td class="px-2 py-1.5 border-r border-[var(--color-border)] text-right">
                    <input
                      ref="newQtyInput"
                      v-model.number="newQty"
                      type="number" min="1"
                      :disabled="printing"
                      class="w-24 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1 py-1 text-center font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-50"
                      @keydown.enter.prevent="addNewItem"
                      @keydown.shift.tab.prevent="focusNewCode"
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
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useItemCache } from '../services/itemCache.js'
import { frappeGet, frappePost, fetchItemPrice } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'

const props = defineProps({
  isSubWindow: Boolean,
  billNo: String,
  items: Array
})

const emit = defineEmits(['close'])
if (props.isSubWindow) useSubwindow()

const router = useRouter()
const route = useRoute()

const { items: allItems, lookupItemInCache } = useItemCache()

// ── Printer / Template ───────────────────────────────────────────────────────
const printers = ref([])
const templates = ref([])
const selectedPrinter = ref('')
const selectedTemplate = ref('')
const loadingResources = ref(false)

const SETTINGS_CACHE_KEY = 'wb-settings-v2'

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

// ── Price list ────────────────────────────────────────────────────────────────
const priceList = ref(localStorage.getItem('wb-price-list') || 'Standard Selling')

// ── Item table state ─────────────────────────────────────────────────────────
const itemsToPrint = ref([])
const selectedRow = ref(-1)

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
const newItemCode = ref('')
const newQty = ref(1)
const newPending = reactive({ item_code: '', item_name: '', uom: '', rate: 0 })

function focusNewCode() { nextTick(() => newCodeInput.value?.focus()) }
function focusNewQty() {
  nextTick(() => { newQtyInput.value?.focus(); newQtyInput.value?.select() })
}

// ── Item lookup from cache ────────────────────────────────────────────────────
function lookupItem(code) {
  const cached = lookupItemInCache(code)
  if (cached) return cached
  // Fuzzy from full list
  const q = code.toLowerCase()
  return allItems.value.find(i =>
    (i.item_code || '').toLowerCase() === q ||
    (i.barcode || '').toLowerCase() === q
  ) || null
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
  const r = lookupItem(code)
  if (r) {
    itemsToPrint.value[idx].item_code = r.item_code || code
    itemsToPrint.value[idx].item_name = r.item_name
    fetchItemPrice(r.item_code || code, priceList.value).then(rate => {
      itemsToPrint.value[idx].rate = rate
    })
    focusField('qty', idx)
  }
}

// ── New entry row handlers ────────────────────────────────────────────────────
async function onNewCodeEnter() {
  const code = newItemCode.value.trim()
  if (!code) return
  const r = lookupItem(code)
  if (r) {
    newPending.item_code = r.item_code || code
    newPending.item_name = r.item_name
    newPending.uom = r.uom || ''
    newPending.rate = 0
    focusNewQty()
    fetchItemPrice(newPending.item_code, priceList.value).then(rate => {
      newPending.rate = rate
    })
  } else {
    newPending.item_code = code
    newPending.item_name = ''
    newPending.rate = 0
    focusNewQty()
  }
}

async function addNewItem() {
  const code = newPending.item_code || newItemCode.value.trim()
  if (!code) return
  const existing = itemsToPrint.value.findIndex(i => i.item_code === code)
  if (existing >= 0) {
    itemsToPrint.value[existing].qty += newQty.value
  } else {
    itemsToPrint.value.push({
      item_code: code,
      item_name: newPending.item_name || code,
      qty: newQty.value,
      rate: newPending.rate || 0,
    })
  }
  newItemCode.value = ''
  newQty.value = 1
  newPending.item_code = ''
  newPending.item_name = ''
  newPending.uom = ''
  newPending.rate = 0
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
    const docName = await frappePost('ssplbilling.api.barcode_api.create_barcode_print_entry', {
      items: JSON.stringify(itemsToPrint.value),
      bill_no: localBillNo.value || null,
      price_list: priceList.value,
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
  await loadResources()

  // Handle props or route query
  localBillNo.value = props.billNo || route.query.bill || ''
  
  if (props.items && props.items.length > 0) {
    itemsToPrint.value = props.items.map(i => ({
      item_code: i.item_code,
      item_name: i.item_name,
      qty: i.qty || 1,
      rate: i.rate || 0,
    }))
  } else {
    const rawItems = route.query.items
    if (rawItems) {
      try {
        const parsed = JSON.parse(decodeURIComponent(rawItems))
        itemsToPrint.value = parsed.map(i => ({
          item_code: i.item_code,
          item_name: i.item_name,
          qty: i.qty || 1,
          rate: i.rate || 0,
        }))
      } catch (e) {
        console.warn('[BarcodePrintPage] Failed to parse items from query', e)
      }
    }
  }

  nextTick(() => focusNewCode())
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #1e293b; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 8px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
