<template>
  <div class="min-h-screen bg-slate-900 text-slate-200 font-sans flex flex-col">

    <!-- Nav Bar -->
    <nav class="fixed top-0 left-0 right-0 z-50 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-6 backdrop-blur-xl">
      <div class="flex items-center gap-6">
        <button
          class="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-bold text-slate-300 transition hover:bg-slate-700 hover:text-white active:scale-95"
          @click="router.push('/')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Dashboard
        </button>
        <div class="h-6 w-px bg-slate-800"></div>
        <h1 class="text-lg font-black tracking-tight text-white uppercase">
          🏷️ Barcode <span class="text-slate-500 font-light">Printing</span>
        </h1>
        <span v-if="billNo" class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-bold text-blue-300">
          {{ billNo }}
        </span>
      </div>

      <div class="flex items-center gap-3">
        <span v-if="itemsToPrint.length" class="rounded-xl border border-slate-700 bg-slate-800/60 px-3 py-1.5 text-xs font-bold text-slate-400">
          {{ itemsToPrint.length }} item{{ itemsToPrint.length !== 1 ? 's' : '' }}
        </span>
        <button
          @click="triggerPrint"
          :disabled="!canPrint || printing"
          class="flex items-center gap-2 rounded-xl bg-orange-600 px-5 py-2 text-sm font-bold text-white shadow-lg transition hover:bg-orange-700 active:scale-95 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed"
        >
          <span v-if="printing" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          {{ printing ? 'Sending…' : '🖨️ Print Barcodes' }}
        </button>
      </div>
    </nav>

    <!-- Body -->
    <div class="flex flex-1 gap-4 p-4 pt-20" style="height: calc(100vh - 4rem);">

      <!-- LEFT: Printer / Template selects -->
      <div class="flex flex-col gap-3 w-64 flex-shrink-0">

        <div class="rounded-2xl border border-slate-700 bg-slate-800/60 p-4">
          <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-slate-500">Printer</label>
          <div class="relative">
            <select v-model="selectedPrinter" :disabled="loadingResources || printing"
              class="w-full appearance-none rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-blue-500 disabled:opacity-50">
              <option value="">— Select Printer —</option>
              <option v-for="p in printers" :key="p.name" :value="p.name">
                {{ p.printer_name }}{{ p.is_default ? ' ★' : '' }}
              </option>
            </select>
            <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">▾</span>
          </div>
          <p v-if="!printers.length && !loadingResources" class="mt-1.5 text-[10px] text-red-400">No printers configured</p>
        </div>

        <div class="rounded-2xl border border-slate-700 bg-slate-800/60 p-4">
          <label class="mb-2 block text-[10px] font-black uppercase tracking-widest text-slate-500">Template</label>
          <div class="relative">
            <select v-model="selectedTemplate" :disabled="loadingResources || printing"
              class="w-full appearance-none rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-blue-500 disabled:opacity-50">
              <option value="">— Select Template —</option>
              <option v-for="t in templates" :key="t.name" :value="t.name">
                {{ t.template_name }}
              </option>
            </select>
            <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">▾</span>
          </div>
          <p v-if="!templates.length && !loadingResources" class="mt-1.5 text-[10px] text-red-400">No Barcode templates</p>
        </div>

        <div v-if="loadingResources" class="text-center text-xs text-slate-600 italic py-2">Loading…</div>

        <!-- Status -->
        <div v-if="statusMsg"
          class="rounded-xl px-4 py-3 text-sm font-bold text-center"
          :class="statusError ? 'bg-red-900/50 border border-red-700 text-red-300' : 'bg-emerald-900/50 border border-emerald-700 text-emerald-300'">
          {{ statusMsg }}
        </div>

        <!-- Shortcuts hint -->
        <div class="mt-auto rounded-xl border border-slate-800 bg-slate-800/30 p-3 text-[10px] text-slate-600 space-y-1">
          <div><kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-500">Enter</kbd> Resolve item / add</div>
          <div><kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-500">Tab</kbd> Move to qty</div>
          <div><kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-500">↑ ↓</kbd> Navigate rows</div>
          <div><kbd class="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-slate-500">Del</kbd> Remove row</div>
        </div>
      </div>

      <!-- RIGHT: Items table -->
      <div class="flex flex-1 flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-800/60">
        <!-- Table header -->
        <div class="flex items-center justify-between border-b border-slate-700 bg-slate-900/60 px-4 py-2.5 flex-shrink-0">
          <div class="text-[10px] font-black uppercase tracking-widest text-slate-500">Items to Print</div>
          <button v-if="itemsToPrint.length && !printing"
            @click="itemsToPrint = []; selectedRow = -1; focusNewCode()"
            class="text-xs text-slate-600 hover:text-red-400 transition font-bold">
            Clear All
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <table class="w-full text-sm border-collapse border-l border-t border-slate-700">
            <thead>
              <tr class="sticky top-0 z-10 bg-slate-800 border-b border-slate-700">
                <th class="w-8 border-r border-slate-700 px-3 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-500">#</th>
                <th class="w-36 border-r border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Code</th>
                <th class="border-r border-slate-700 px-2 py-2.5 text-left text-xs font-bold uppercase tracking-wider text-slate-400">Item Name</th>
                <th class="w-32 border-r border-slate-700 px-2 py-2.5 text-right text-xs font-bold uppercase tracking-wider text-slate-400">Qty</th>
                <th class="w-8 border-slate-700"></th>
              </tr>
            </thead>
            <tbody>
              <!-- Existing rows -->
              <tr
                v-for="(item, idx) in itemsToPrint"
                :key="idx"
                :ref="el => setRowRef(el, idx)"
                tabindex="-1"
                class="cursor-pointer border-b border-slate-700 outline-none transition-colors"
                :class="selectedRow === idx
                  ? 'bg-blue-900/30 border-l-2 border-l-blue-500'
                  : 'hover:bg-slate-700/30'"
                @click="selectRow(idx)"
                @keydown="onRowKeydown($event, idx)"
              >
                <!-- # -->
                <td class="px-3 py-2.5 border-r border-slate-700">
                  <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-slate-400">{{ idx + 1 }}</span>
                </td>
                <!-- Item Code -->
                <td class="px-2 py-2.5 border-r border-slate-700">
                  <input
                    v-if="selectedRow === idx"
                    :ref="el => setRef(el, 'code', idx)"
                    v-model="item.item_code"
                    class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-0.5 font-mono text-sm text-slate-200 outline-none focus:border-blue-500"
                    @keydown.enter.prevent="onCodeEnter(idx)"
                    @keydown.tab.prevent="focusField('qty', idx)"
                    @keydown.down.prevent="moveRow(idx, 1)"
                    @keydown.up.prevent="moveRow(idx, -1)"
                    @keydown.delete.stop
                  />
                  <span v-else class="font-mono text-slate-400">{{ item.item_code }}</span>
                </td>
                <!-- Item Name -->
                <td class="px-2 py-2.5 border-r border-slate-700 text-slate-200">{{ item.item_name || '—' }}</td>
                <!-- Qty -->
                <td class="px-2 py-2.5 border-r border-slate-700 text-right">
                  <div v-if="selectedRow === idx" class="flex items-center justify-end gap-1.5">
                    <button @click.stop="item.qty = Math.max(1, item.qty - 1)"
                      class="h-6 w-6 rounded bg-slate-700 text-slate-300 hover:bg-slate-600 font-bold text-xs">&minus;</button>
                    <input
                      :ref="el => setRef(el, 'qty', idx)"
                      type="number" v-model.number="item.qty" min="1"
                      class="w-16 rounded border border-slate-600 bg-slate-800 px-1 py-0.5 text-center font-mono text-sm text-slate-200 outline-none focus:border-blue-500"
                      @keydown.enter.prevent="moveRow(idx, 1)"
                      @keydown.tab.prevent="moveRow(idx, 1)"
                      @keydown.shift.tab.prevent="focusField('code', idx)"
                      @keydown.down.prevent="moveRow(idx, 1)"
                      @keydown.up.prevent="moveRow(idx, -1)"
                    />
                    <button @click.stop="item.qty++"
                      class="h-6 w-6 rounded bg-slate-700 text-slate-300 hover:bg-slate-600 font-bold text-xs">&plus;</button>
                  </div>
                  <span v-else class="font-mono text-slate-300">{{ item.qty }}</span>
                </td>
                <!-- Remove -->
                <td class="px-2 py-2.5 text-center">
                  <button @click.stop="itemsToPrint.splice(idx, 1); selectedRow = -1; focusNewCode()"
                    class="rounded px-1 py-0.5 text-slate-600 hover:bg-red-900/30 hover:text-red-400 transition">&times;</button>
                </td>
              </tr>

              <!-- NEW ENTRY ROW -->
              <tr class="border-b border-slate-700"
                :class="selectedRow === -1 ? 'bg-blue-900/15' : 'bg-slate-800/20'">
                <!-- # -->
                <td class="px-3 py-2.5 border-r border-slate-700">
                  <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-900/50 text-[10px] font-bold text-blue-400">+</span>
                </td>
                <!-- Item Code input -->
                <td class="px-2 py-2.5 border-r border-slate-700">
                  <input
                    ref="newCodeInput"
                    v-model="newItemCode"
                    :disabled="printing"
                    class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 font-mono text-sm text-slate-200 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-900/50 disabled:opacity-50"
                    placeholder="Item code…"
                    @keydown.enter.prevent="onNewCodeEnter"
                    @keydown.tab.prevent="focusNewQty"
                    @keydown.up.prevent="moveToLastRow"
                  />
                </td>
                <!-- Pending item name -->
                <td class="px-2 py-2.5 border-r border-slate-700 text-slate-400 text-sm">{{ newPending.item_name || '—' }}</td>
                <!-- Qty input -->
                <td class="px-2 py-2.5 border-r border-slate-700 text-right">
                  <input
                    ref="newQtyInput"
                    v-model.number="newQty"
                    type="number" min="1"
                    :disabled="printing"
                    class="w-16 rounded border border-slate-600 bg-slate-800 px-1 py-1 text-center font-mono text-sm text-slate-200 outline-none focus:border-blue-500 disabled:opacity-50"
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
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useItemCache } from '../services/itemCache.js'
import { frappeGet, frappePost, fetchItemPrice } from '../api.js'

const router = useRouter()
const route = useRoute()

const { items: allItems, lookupItemInCache } = useItemCache()

// ── Printer / Template ───────────────────────────────────────────────────────
const printers = ref([])
const templates = ref([])
const selectedPrinter = ref('')
const selectedTemplate = ref('')
const loadingResources = ref(false)

async function loadResources() {
  loadingResources.value = true
  try {
    const [p, t] = await Promise.all([
      frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers'),
      frappeGet('frappe.client.get_list', {
        doctype: 'Print Template',
        filters: JSON.stringify({ document_type: 'Barcode_Prinitng', format_type: 'Barcode' }),
        fields: JSON.stringify(['name', 'template_name', 'format_type']),
        limit: 50,
      }),
    ])
    printers.value = p || []
    templates.value = t || []
    const userDefault = localStorage.getItem('wb-default-printer')
    if (userDefault && printers.value.some(pr => pr.name === userDefault)) {
      selectedPrinter.value = userDefault
    } else {
      const def = printers.value.find(pr => pr.is_default) || printers.value[0]
      if (def) selectedPrinter.value = def.name
    }
    if (templates.value.length === 1) selectedTemplate.value = templates.value[0].name
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
const billNo = ref(route.query.bill || '')

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
      bill_no: billNo.value || null,
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

  nextTick(() => focusNewCode())
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #1e293b; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 8px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
