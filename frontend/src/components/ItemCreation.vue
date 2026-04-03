<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
    @click.self="$emit('close')"
  >
    <div class="w-[90vw] bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-5 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
        <div>
          <h3 class="text-3xl font-bold text-slate-100">{{ isEditMode ? 'Edit Item' : 'Create New Item' }}</h3>
          <p class="text-lg text-slate-400">{{ isEditMode ? 'Update item details' : 'Add a new item to the system' }}</p>
        </div>
        <button
          @click="$emit('close')"
          class="text-slate-500 hover:text-slate-300 transition-colors p-2 hover:bg-slate-700 rounded-full"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto p-8 space-y-8">
        <!-- Main Info -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Item Name *</label>
            <input
              ref="itemNameInput"
              v-model="form.item_name"
              type="text"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-2xl font-medium text-slate-200 outline-none focus:border-blue-500 transition-all"
              placeholder="Enter full item name..."
              @keydown.enter.prevent="itemPrintNameInput?.focus()"
            />
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Item Print Name</label>
            <input
              ref="itemPrintNameInput"
              v-model="form.item_print_name"
              type="text"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-2xl font-medium text-slate-200 outline-none focus:border-blue-500 transition-all"
              placeholder="Name as shown on printouts..."
              @keydown.enter.prevent="barcodeInput?.focus()"
            />
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Barcode / Code</label>
            <div class="relative">
              <input
                ref="barcodeInput"
                v-model="form.barcode"
                type="text"
                :disabled="isEditMode"
                class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 font-mono text-xl text-slate-200 outline-none focus:border-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Enter alphanumeric barcode..."
                @focus="e => e.target.select()"
                @keydown.enter.prevent="itemGroupInput?.focus()"
              />
              <div v-if="isFetchingBarcode" class="absolute right-4 top-1/2 -translate-y-1/2">
                <span class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent inline-block"></span>
              </div>
            </div>
          </div>

          <!-- Extra Barcodes -->
          <div class="space-y-2 md:col-span-2">
            <div class="flex items-center justify-between px-1">
              <label class="text-base font-bold text-slate-500 uppercase tracking-wider">Additional Barcodes</label>
              <button type="button" @click="addBarcodeRow" class="text-sm font-bold text-blue-400 hover:text-blue-300 transition-colors">+ Add Barcode</button>
            </div>
            <div class="rounded-xl border border-slate-700 bg-slate-800/50 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-slate-700 bg-slate-800">
                    <th class="px-4 py-2 text-left text-xs font-bold uppercase text-slate-500">Barcode</th>
                    <th class="w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  <!-- Primary barcode (locked) -->
                  <tr class="border-b border-slate-700/50">
                    <td class="px-4 py-3 flex items-center gap-3">
                      <span class="font-mono text-lg text-slate-300">{{ form.barcode || '—' }}</span>
                      <span class="text-[10px] font-bold uppercase text-slate-600 bg-slate-700 px-2 py-1 rounded">Primary</span>
                    </td>
                    <td></td>
                  </tr>
                  <!-- Additional barcode rows -->
                  <tr v-for="(row, idx) in form.extra_barcodes" :key="idx" class="border-b border-slate-700/50 last:border-0">
                    <td class="px-3 py-2">
                      <input v-model="row.barcode" type="text" class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-lg text-slate-200 outline-none focus:border-blue-500" placeholder="Enter barcode value..." />
                    </td>
                    <td class="px-3 py-2 text-center">
                      <button type="button" @click="removeBarcodeRow(idx)" class="text-slate-600 hover:text-red-400 transition-colors text-2xl font-bold leading-none">&times;</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Item Group *</label>
            <select
              ref="itemGroupInput"
              v-model="form.item_group"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-xl text-slate-200 outline-none focus:border-blue-500 transition-all appearance-none"
              @keydown.enter.prevent="hsnInput?.focus()"
            >
              <option value="">Select Group...</option>
              <option v-for="g in metadata.item_groups" :key="g.name" :value="g.name">{{ g.name }}</option>
            </select>
          </div>

          <div class="space-y-2 relative">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">HSN/SAC Code</label>
            <input
              ref="hsnInput"
              v-model="form.hsn_sac"
              type="text"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-xl text-slate-200 outline-none focus:border-blue-500 transition-all"
              placeholder="Search code..."
              @focus="showHSNDropdown = true"
              @blur="setTimeout(() => showHSNDropdown = false, 200)"
              @keydown.enter.prevent="onHSNEnter"
              @keydown.down.prevent="hsnHighlightIdx = (hsnHighlightIdx + 1) % filteredHSNCodes.length"
              @keydown.up.prevent="hsnHighlightIdx = (hsnHighlightIdx - 1 + filteredHSNCodes.length) % filteredHSNCodes.length"
            />
            <div v-if="showHSNDropdown && filteredHSNCodes.length > 0" class="absolute left-0 right-0 top-full z-10 mt-1 max-h-60 overflow-y-auto rounded-xl bg-slate-800 border border-slate-700 p-1 shadow-xl">
              <button
                v-for="(res, idx) in filteredHSNCodes"
                :key="res.name"
                class="w-full rounded-lg px-4 py-3 text-left transition-colors group flex flex-col gap-1"
                :class="hsnHighlightIdx === idx ? 'bg-blue-600' : 'hover:bg-blue-900/30'"
                @click="selectHSN(res.name)"
              >
                <span class="text-lg font-bold group-hover:text-blue-400" :class="hsnHighlightIdx === idx ? 'text-white' : 'text-slate-200'">{{ res.name }}</span>
                <span v-if="res.description" class="text-xs truncate line-clamp-1 italic" :class="hsnHighlightIdx === idx ? 'text-blue-100' : 'text-slate-500'">{{ res.description }}</span>
              </button>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Default UOM *</label>
            <select
              ref="uomInput"
              v-model="form.stock_uom"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-xl text-slate-200 outline-none focus:border-blue-500 transition-all appearance-none"
              @keydown.enter.prevent="rateInput?.focus()"
            >
              <option v-for="u in metadata.uoms" :key="u.name" :value="u.name">{{ u.name }}</option>
            </select>
          </div>

          <!-- UOM Conversions -->
          <div class="space-y-2 md:col-span-2">
            <div class="flex items-center justify-between px-1">
              <label class="text-base font-bold text-slate-500 uppercase tracking-wider">UOM Conversions</label>
              <button type="button" @click="addUomRow" class="text-sm font-bold text-blue-400 hover:text-blue-300 transition-colors">+ Add UOM</button>
            </div>
            <div class="rounded-xl border border-slate-700 bg-slate-800/50 overflow-hidden">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-slate-700 bg-slate-800">
                    <th class="px-4 py-2 text-left text-xs font-bold uppercase text-slate-500">UOM</th>
                    <th class="px-4 py-2 text-left text-xs font-bold uppercase text-slate-500">
                      Conversion Factor
                      <span class="normal-case font-normal text-slate-600 ml-1">(1 UOM = ? stock UOM)</span>
                    </th>
                    <th class="w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  <!-- Base stock UOM row (locked) -->
                  <tr class="border-b border-slate-700/50">
                    <td class="px-4 py-3 flex items-center gap-3">
                      <span class="text-lg font-semibold text-slate-300">{{ form.stock_uom || '—' }}</span>
                      <span class="text-[10px] font-bold uppercase text-slate-600 bg-slate-700 px-2 py-1 rounded">Base</span>
                    </td>
                    <td class="px-4 py-3 font-mono text-lg text-slate-500">1.000</td>
                    <td></td>
                  </tr>
                  <!-- Additional UOM rows -->
                  <tr v-for="(row, idx) in form.uom_conversions" :key="idx" class="border-b border-slate-700/50 last:border-0">
                    <td class="px-3 py-2">
                      <select v-model="row.uom" class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500 appearance-none">
                        <option value="">Select UOM...</option>
                        <option v-for="u in metadata.uoms" :key="u.name" :value="u.name" :disabled="u.name === form.stock_uom">{{ u.name }}</option>
                      </select>
                    </td>
                    <td class="px-3 py-2">
                      <input v-model.number="row.conversion_factor" type="number" min="0.0001" step="0.001" class="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-base text-slate-200 outline-none focus:border-blue-500" placeholder="1.000" />
                    </td>
                    <td class="px-3 py-2 text-center">
                      <button type="button" @click="removeUomRow(idx)" class="text-slate-600 hover:text-red-400 transition-colors text-2xl font-bold leading-none">&times;</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Standard Rate (Selling)</label>
            <div class="relative">
              <span class="absolute left-5 top-1/2 -translate-y-1/2 font-bold text-slate-500 text-xl">₹</span>
              <input
                ref="rateInput"
                v-model.number="form.standard_rate"
                type="number"
                class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 pl-10 pr-5 text-right font-mono text-2xl font-bold text-slate-200 outline-none focus:border-emerald-500 transition-all"
                placeholder="0.00"
                @keydown.enter.prevent="safetyStockInput?.focus()"
              />
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Safety Stock</label>
            <input
              ref="safetyStockInput"
              v-model.number="form.safety_stock"
              type="number"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-right font-mono text-2xl text-slate-200 outline-none focus:border-blue-500 transition-all"
              placeholder="0"
              @keydown.enter.prevent="taxTemplateInput?.focus()"
            />
          </div>

          <div class="space-y-2 md:col-span-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Tax Template</label>
            <select
              ref="taxTemplateInput"
              v-model="form.item_tax_template"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-xl text-slate-200 outline-none focus:border-blue-500 transition-all appearance-none"
              @keydown.enter.prevent="supplierInput?.focus()"
            >
              <option value="">No Tax / Exempt</option>
              <option v-for="t in metadata.tax_templates" :key="t.name" :value="t.name">{{ t.name }}</option>
            </select>
          </div>

          <!-- Supplier -->
          <div class="space-y-2 md:col-span-2 relative">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Supplier</label>
            <div class="relative">
              <input
                ref="supplierInput"
                :value="supplierSearch"
                type="text"
                class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 text-xl text-slate-200 outline-none focus:border-blue-500 transition-all"
                :class="form.supplier ? 'border-emerald-600' : ''"
                placeholder="Search supplier..."
                autocomplete="off"
                @input="onSupplierInput"
                @focus="showSupplierDropdown = true"
                @blur="setTimeout(() => { showSupplierDropdown = false }, 200)"
                @keydown.enter.prevent="onSupplierEnter"
                @keydown.escape="clearSupplier"
              />
              <button
                v-if="form.supplier"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-red-400 transition-colors text-2xl"
                @click.prevent="clearSupplier"
                tabindex="-1"
              >&times;</button>
              <div
                v-if="showSupplierDropdown && supplierOptions.length"
                class="absolute left-0 right-0 top-full z-10 mt-1 max-h-60 overflow-y-auto rounded-xl bg-slate-800 border border-slate-700 p-1 shadow-xl"
              >
                <button
                  v-for="opt in supplierOptions"
                  :key="opt.name"
                  class="w-full rounded-lg px-5 py-3 text-left hover:bg-blue-900/30 transition-colors flex flex-col gap-1"
                  @mousedown.prevent="selectSupplier(opt)"
                >
                  <span class="text-lg font-bold text-slate-200">{{ opt.label }}</span>
                  <span class="text-xs text-slate-500">{{ opt.name }}</span>
                </button>
              </div>
            </div>
            <p v-if="form.supplier" class="text-xs text-emerald-400 px-1">Mapped: {{ form.supplier }}</p>
          </div>

          <!-- Supplier Part No -->
          <div class="space-y-2 md:col-span-2">
            <label class="text-base font-bold text-slate-500 uppercase tracking-wider px-1">Supplier Part No <span class="normal-case font-normal text-slate-600">(optional)</span></label>
            <input
              ref="supplierPartNoInput"
              v-model="form.supplier_part_no"
              type="text"
              :disabled="!form.supplier"
              class="w-full rounded-xl border border-slate-600 bg-slate-800 py-4 px-5 font-mono text-xl text-slate-200 outline-none focus:border-blue-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              placeholder="Supplier's part / SKU number..."
              @keydown.enter.prevent="handleSubmit"
            />
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-6 py-5 bg-slate-800 border-t border-slate-700 flex gap-4">
        <button
          @click="$emit('close')"
          class="flex-1 rounded-xl py-4 text-base font-bold uppercase tracking-widest text-slate-400 bg-slate-700 border border-slate-600 hover:bg-slate-600 transition-all active:scale-95"
        >
          Cancel
        </button>
        <button
          @click="handleSubmit"
          :disabled="isSubmitting || !canSubmit"
          class="flex-[2] rounded-xl py-4 text-base font-bold uppercase tracking-widest text-white transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none shadow-lg flex items-center justify-center gap-3"
          :class="canSubmit ? 'bg-blue-600 hover:bg-blue-700' : 'bg-slate-700'"
        >
          <span v-if="isSubmitting" class="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>{{ isEditMode ? 'Update Item' : 'Create Item' }}</span>
          <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { fetchItemCreationMetadata, getNextBarcode, createItem, updateItem, getItemForEdit, frappeGet } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  editItemCode: { type: String, default: '' },  // when set → edit mode
})

const emit = defineEmits(['close', 'created'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

const isEditMode = computed(() => !!props.editItemCode)

async function loadForEdit(itemCode) {
  try {
    const data = await getItemForEdit(itemCode)
    form.value.item_name        = data.item_name        || ''
    form.value.item_print_name  = data.item_print_name  || ''
    form.value.barcode           = data.barcode           || itemCode
    form.value.item_group        = data.item_group        || ''
    form.value.hsn_sac           = data.hsn_sac           || ''
    form.value.stock_uom         = data.stock_uom         || 'Nos'
    form.value.standard_rate     = data.standard_rate     || 0
    form.value.safety_stock      = data.safety_stock      || 0
    form.value.item_tax_template = data.item_tax_template || ''
    form.value.supplier          = data.supplier          || ''
    form.value.supplier_part_no  = data.supplier_part_no  || ''
    form.value.uom_conversions   = data.uom_conversions   || []
    form.value.extra_barcodes    = data.extra_barcodes    || []
    supplierSearch.value = data.supplier || ''
    autoBarcode.value = ''
    isBarcodeManual.value = true
  } catch (e) {
    console.error('[ItemCreation] loadForEdit failed:', e)
  }
}

const itemNameInput = ref(null)
const itemPrintNameInput = ref(null)
const barcodeInput = ref(null)
const itemGroupInput = ref(null)
const hsnInput = ref(null)
const uomInput = ref(null)
const rateInput = ref(null)
const safetyStockInput = ref(null)
const taxTemplateInput = ref(null)
const supplierInput = ref(null)
const supplierPartNoInput = ref(null)

const isSubmitting = ref(false)
const isFetchingBarcode = ref(false)
const isBarcodeManual = ref(false)
const autoBarcode = ref('')
const selectedSeries = ref('')
const showHSNDropdown = ref(false)
const hsnHighlightIdx = ref(0)

const form = ref({
  item_name: '',
  item_print_name: '',
  barcode: '',
  item_group: '',
  hsn_sac: '',
  stock_uom: 'Nos',
  standard_rate: 0,
  safety_stock: 0,
  item_tax_template: '',
  supplier: '',
  supplier_part_no: '',
  uom_conversions: [],
  extra_barcodes: [],
})

function addBarcodeRow() {
  form.value.extra_barcodes.push({ barcode: '' })
}

function removeBarcodeRow(idx) {
  form.value.extra_barcodes.splice(idx, 1)
}

function addUomRow() {
  form.value.uom_conversions.push({ uom: '', conversion_factor: 1 })
}

function removeUomRow(idx) {
  form.value.uom_conversions.splice(idx, 1)
}

// ── Supplier search state ──────────────────────────────────────────────────
const supplierSearch = ref('')          // display label
const supplierOptions = ref([])
const showSupplierDropdown = ref(false)
let supplierSearchTimeout = null

async function onSupplierInput(e) {
  const q = e.target.value
  supplierSearch.value = q
  form.value.supplier = ''             // clear until a match is selected
  clearTimeout(supplierSearchTimeout)
  if (!q.trim()) { supplierOptions.value = []; return }
  supplierSearchTimeout = setTimeout(async () => {
    try {
      supplierOptions.value = await frappeGet('ssplbilling.api.item_api.search_suppliers', { query: q, limit: 15 })
    } catch (_) { supplierOptions.value = [] }
  }, 250)
}

function selectSupplier(opt) {
  form.value.supplier = opt.name
  supplierSearch.value = opt.label
  supplierOptions.value = []
  showSupplierDropdown.value = false
  nextTick(() => supplierPartNoInput.value?.focus())
}

function clearSupplier() {
  form.value.supplier = ''
  supplierSearch.value = ''
  supplierOptions.value = []
}

function onSupplierEnter() {
  if (showSupplierDropdown.value && supplierOptions.value.length > 0) {
    selectSupplier(supplierOptions.value[0])
  } else if (form.value.supplier) {
    supplierPartNoInput.value?.focus()
  } else {
    // If no supplier selected and no options found, submit the form
    handleSubmit()
  }
}

// Sync Item Print Name from Item Name by default
watch(() => form.value.item_name, (newVal) => {
  form.value.item_print_name = newVal
})

// Track manual changes — strip all leading zeros on every change
watch(() => form.value.barcode, (newVal, oldVal) => {
  if (newVal && /^0/.test(newVal)) {
    form.value.barcode = stripLeadingZeros(newVal)
    return
  }
  if (oldVal !== undefined && !isFetchingBarcode.value) {
    isBarcodeManual.value = newVal !== autoBarcode.value
  }
})

const metadata = ref({
  item_groups: [],
  uoms: [],
  tax_templates: [],
  hsn_codes: [],
  naming_series: []
})

const filteredHSNCodes = computed(() => {
  const q = (form.value.hsn_sac || '').toLowerCase().trim()
  if (!q) return metadata.value.hsn_codes.slice(0, 50)
  return metadata.value.hsn_codes
    .filter(h => h.name.toLowerCase().includes(q) || (h.description || '').toLowerCase().includes(q))
    .slice(0, 50)
})

const canSubmit = computed(() => {
  return form.value.item_name.trim() && form.value.item_group && form.value.stock_uom
})

async function loadMetadata() {
  try {
    const data = await fetchItemCreationMetadata()
    metadata.value = data
    
    // Default group if available
    if (data.item_groups?.length && !form.value.item_group) {
      const allGroup = data.item_groups.find(g => g.name === 'All Item Groups')
      form.value.item_group = allGroup ? allGroup.name : data.item_groups[0].name
    }
    
    if (data.naming_series?.length) {
      selectedSeries.value = data.naming_series[0]
      generateBarcode()
    }
  } catch (e) {
    console.warn('Failed to load item metadata', e)
  }
}

function stripLeadingZeros(val) {
  const s = String(val || '').replace(/^0+/, '')
  return s || '0'
}

async function generateBarcode() {
  const series = selectedSeries.value || metadata.value.naming_series[0]
  if (!series) return

  isFetchingBarcode.value = true
  try {
    const res = await getNextBarcode(series)
    const stripped = stripLeadingZeros(res)
    form.value.barcode = stripped
    autoBarcode.value = stripped
    nextTick(() => { isBarcodeManual.value = false })
  } catch (e) {
    console.error('Failed to generate barcode', e)
  } finally {
    isFetchingBarcode.value = false
  }
}

function selectHSN(name) {
  form.value.hsn_sac = name
  showHSNDropdown.value = false
  hsnHighlightIdx.value = 0
  nextTick(() => uomInput.value?.focus())
}

function onHSNEnter() {
  if (showHSNDropdown.value && filteredHSNCodes.value.length > 0) {
    selectHSN(filteredHSNCodes.value[hsnHighlightIdx.value].name)
  } else {
    uomInput.value?.focus()
  }
}

watch(filteredHSNCodes, () => {
  hsnHighlightIdx.value = 0
})

async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return

  // Strip all leading zeros from primary barcode and any additional barcodes before saving
  form.value.barcode = stripLeadingZeros(form.value.barcode)
  form.value.extra_barcodes = form.value.extra_barcodes.map(r => ({
    ...r,
    barcode: stripLeadingZeros(r.barcode),
  }))

  isSubmitting.value = true
  try {
    if (isEditMode.value) {
      const res = await updateItem({
        ...form.value,
        item_code: props.editItemCode,
        supplier: form.value.supplier || '',
        supplier_part_no: form.value.supplier_part_no || '',
      })
      alert(`Item ${res.item_code} updated successfully!`)
      emit('created', {
        item_code: res.item_code,
        item_name: res.item_name,
        price: form.value.standard_rate,
        uom: form.value.stock_uom,
        tax_rate: 0
      })
    } else {
      const res = await createItem({
        ...form.value,
        is_manual_barcode: isBarcodeManual.value,
        naming_series: selectedSeries.value,
        supplier: form.value.supplier || '',
        supplier_part_no: form.value.supplier_part_no || '',
      })
      alert(`Item ${res.name} created successfully!`)
      emit('created', {
        item_code: res.item_code,
        item_name: form.value.item_name,
        price: form.value.standard_rate,
        uom: form.value.stock_uom,
        tax_rate: 0
      })
      resetForm()
    }
  } catch (e) {
    alert(`Failed to ${isEditMode.value ? 'update' : 'create'} item: ` + e.message)
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  form.value = {
    item_name: '',
    item_print_name: '',
    barcode: '',
    item_group: metadata.value.item_groups[0]?.name || '',
    hsn_sac: '',
    stock_uom: 'Nos',
    standard_rate: 0,
    safety_stock: 0,
    item_tax_template: '',
    supplier: '',
    supplier_part_no: '',
    uom_conversions: [],
    extra_barcodes: [],
  }
  supplierSearch.value = ''
  supplierOptions.value = []
  isBarcodeManual.value = false
  autoBarcode.value = ''
  if (selectedSeries.value) generateBarcode()
}

watch(() => props.show, async (newVal) => {
  if (newVal) {
    await loadMetadata()
    if (isEditMode.value) {
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})

onMounted(async () => {
  if (props.show) {
    await loadMetadata()
    if (isEditMode.value) {
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})
</script>
