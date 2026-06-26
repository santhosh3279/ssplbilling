<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
    @click.self="$emit('close')"
  >
    <div class="w-[90vw] bg-[var(--color-bg)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="p-[12px] bg-[var(--color-surface)] border-b border-[var(--color-border)] flex justify-between items-center">
        <div class="flex items-baseline gap-4">
          <h3 class="text-5xl font-bold text-[var(--color-text)]">{{ isEditMode ? 'Edit Item' : 'Create New Item' }}</h3>
          <span class="text-[var(--color-text-muted)] text-2xl">|</span>
          <p class="text-2xl text-[var(--color-text-muted)]">{{ isEditMode ? 'Update item details' : 'Add a new item to the system' }}</p>
        </div>
        <button
          @click="$emit('close')"
          class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors px-[20px] py-[12px] hover:bg-[var(--color-surface-raised)] rounded-full"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto px-[20px] py-[12px]">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-[24px]">
          <!-- Column 1: Names & Barcodes -->
          <div class="space-y-[16px]">
            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Name *</label>
              <input
                ref="itemNameInput"
                v-model="form.item_name"
                type="text"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-4xl font-medium text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                placeholder="Enter full item name..."
                @keydown.enter.prevent="itemPrintNameInput?.focus()"
              />
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Print Name</label>
              <input
                ref="itemPrintNameInput"
                v-model="form.item_print_name"
                type="text"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-4xl font-medium text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                placeholder="Print name..."
                @keydown.enter.prevent="itemGroupInput?.focus()"
              />
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Barcode / Code</label>
              <div class="relative">
                <input
                  ref="barcodeInput"
                  v-model="form.barcode"
                  type="text"
                  :disabled="isEditMode"
                  class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] pl-[20px] pr-[30px] py-[12px] font-mono text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Barcode..."
                  @focus="e => e.target.select()"
                  @keydown.enter.prevent="itemGroupInput?.focus()"
                />
                <div v-if="isFetchingBarcode" class="absolute right-[8px] top-1/2 -translate-y-1/2">
                  <span class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent inline-block"></span>
                </div>
              </div>
            </div>

            <!-- Extra Barcodes -->
            <div class="space-y-[4px]">
              <div class="flex items-center justify-between px-[20px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">Additional Barcodes</label>
                <button type="button" @click="addBarcodeRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add Barcode</button>
              </div>
              <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/30 px-[20px] py-[4px] min-h-[64px] flex items-center">
                <div class="flex flex-nowrap gap-[8px] overflow-x-auto custom-scrollbar w-full pb-[2px]">
                  <div class="flex items-center gap-[8px] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 px-[20px] py-[12px] shrink-0">
                    <span class="font-mono text-2xl text-[var(--color-text)]">{{ form.barcode || '—' }}</span>
                    <span class="text-sm font-bold uppercase text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] px-2 py-1 rounded">Primary</span>
                  </div>
                  <div v-for="(row, idx) in form.extra_barcodes" :key="idx" class="flex items-center gap-[12px] rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[16px] py-[8px] relative group shrink-0">
                    <div class="flex flex-col gap-1">
                      <input v-model="row.barcode" type="text" class="bg-transparent border-none p-0 font-mono text-2xl text-[var(--color-text)] outline-none w-48" placeholder="Barcode..." />
                      <select v-model="row.uom" class="bg-transparent border-none p-0 text-sm font-bold text-[var(--color-text-muted)] uppercase outline-none cursor-pointer hover:text-[var(--color-info)] transition-colors">
                        <option v-for="u in availableUoms" :key="u" :value="u" class="bg-[var(--color-surface)] text-[var(--color-text)]">{{ u }}</option>
                      </select>
                    </div>
                    <button type="button" @click="removeBarcodeRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none pr-1">&times;</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 2: Classification & Taxes -->
          <div class="space-y-[16px]">
            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Item Group *</label>
              <select
                ref="itemGroupInput"
                v-model="form.item_group"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="hsnInput?.focus()"
              >
                <option value="">Select Group...</option>
                <option v-for="g in metadata.item_groups" :key="g.name" :value="g.name">{{ g.name }}</option>
              </select>
            </div>

            <div class="space-y-[4px] relative">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">HSN/SAC Code</label>
              <input
                ref="hsnInput"
                v-model="form.hsn_sac"
                type="text"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                placeholder="Search HSN..."
                @focus="showHSNDropdown = true"
                @blur="setTimeout(() => showHSNDropdown = false, 200)"
                @keydown.enter.prevent="onHSNEnter"
                @keydown.down.prevent="hsnHighlightIdx = (hsnHighlightIdx + 1) % filteredHSNCodes.length"
                @keydown.up.prevent="hsnHighlightIdx = (hsnHighlightIdx - 1 + filteredHSNCodes.length) % filteredHSNCodes.length"
              />
              <div v-if="showHSNDropdown && filteredHSNCodes.length > 0" class="absolute left-0 right-0 top-full z-10 mt-1 max-h-80 overflow-y-auto rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] px-[20px] py-[12px] shadow-xl">
                <button
                  v-for="(res, idx) in filteredHSNCodes"
                  :key="res.name"
                  class="w-full rounded-lg px-[20px] py-[12px] text-left transition-colors group flex flex-col gap-2"
                  :class="hsnHighlightIdx === idx ? 'bg-[var(--color-info)]' : 'hover:bg-[var(--color-info)]/20'"
                  @click="selectHSN(res.name)"
                >
                  <span class="text-2xl font-bold group-hover:text-[var(--color-info)]" :class="hsnHighlightIdx === idx ? 'text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text)]'">{{ res.name }}</span>
                  <span v-if="res.description" class="text-base truncate line-clamp-1 italic" :class="hsnHighlightIdx === idx ? 'text-[var(--color-text-on-focus)]' : 'text-[var(--color-text-muted)]'">{{ res.description }}</span>
                </button>
              </div>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Default UOM *</label>
              <select
                ref="uomInput"
                v-model="form.stock_uom"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="taxTemplateInput?.focus()"
              >
                <option v-for="u in metadata.uoms" :key="u.name" :value="u.name">{{ u.name }}</option>
              </select>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Tax Template</label>
              <select
                ref="taxTemplateInput"
                v-model="form.item_tax_template"
                class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all appearance-none"
                @keydown.enter.prevent="rateInput?.focus()"
              >
                <option value="">No Tax / Exempt</option>
                <option v-for="t in metadata.tax_templates" :key="t.name" :value="t.name">{{ t.name }}</option>
              </select>
            </div>
          </div>

          <!-- Column 3: Conversions, Rates & Supplier -->
          <div class="space-y-[16px]">
            <!-- UOM Conversions -->
            <div class="space-y-[4px]">
              <div class="flex items-center justify-between px-[20px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider">UOM Conversions</label>
                <button type="button" @click="addUomRow" class="text-xl font-bold text-[var(--color-info)] hover:text-[var(--color-info)] transition-colors">+ Add UOM</button>
              </div>
              <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/50 overflow-hidden">
                <table class="w-full text-2xl">
                  <thead>
                    <tr class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                      <th class="px-[20px] py-[12px] text-left font-bold uppercase text-[var(--color-text-muted)]">UOM</th>
                      <th class="px-[20px] py-[12px] text-left font-bold uppercase text-[var(--color-text-muted)]">Factor</th>
                      <th class="w-16"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in form.uom_conversions" :key="idx" class="border-b border-[var(--color-border)]/50 last:border-0">
                      <td class="px-[20px] py-[12px]">
                        <select v-model="row.uom" class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] appearance-none">
                          <option v-for="u in metadata.uoms" :key="u.name" :value="u.name" :disabled="u.name === form.stock_uom">{{ u.name }}</option>
                        </select>
                      </td>
                      <td class="px-[20px] py-[12px]">
                        <input v-model.number="row.conversion_factor" type="number" step="0.001" class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] font-mono text-2xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" />
                      </td>
                      <td class="px-[20px] py-[12px] text-center">
                        <button type="button" @click="removeUomRow(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl font-bold leading-none">&times;</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-[8px]">
              <div class="space-y-[4px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Standard Rate</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 font-bold text-[var(--color-text-muted)] text-3xl">₹</span>
                  <input ref="rateInput" v-model.number="form.standard_rate" type="number" class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] pl-[40px] text-right font-mono text-4xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-success)] transition-all" placeholder="0.00" @keydown.enter.prevent="safetyStockInput?.focus()" />
                </div>
              </div>
              <div class="space-y-[4px]">
                <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Safety Stock</label>
                <input ref="safetyStockInput" v-model.number="form.safety_stock" type="number" class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-right font-mono text-4xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all placeholder:text-[var(--color-text-muted)]" placeholder="0" @keydown.enter.prevent="supplierInput?.focus()" />
              </div>
            </div>

            <div class="space-y-[4px] relative">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Supplier</label>
              <div class="relative">
                <input
                  ref="supplierInput"
                  :value="supplierSearch"
                  type="text"
                  class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all"
                  :class="form.supplier ? 'border-[var(--color-success)]' : ''"
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
                  class="absolute right-[8px] top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors text-4xl"
                  @click.prevent="clearSupplier"
                  tabindex="-1"
                >&times;</button>
                <div
                  v-if="showSupplierDropdown && supplierOptions.length"
                  class="absolute left-0 right-0 top-full z-10 mt-1 max-h-80 overflow-y-auto rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] px-[20px] py-[12px] shadow-xl"
                >
                  <button
                    v-for="opt in supplierOptions"
                    :key="opt.name"
                    class="w-full rounded-lg px-[20px] py-[12px] text-left hover:bg-[var(--color-info)]/20 transition-colors flex flex-col gap-2"
                    @mousedown.prevent="selectSupplier(opt)"
                  >
                    <span class="text-2xl font-bold text-[var(--color-text)]">{{ opt.label }}</span>
                    <span class="text-base text-[var(--color-text-muted)]">{{ opt.name }}</span>
                  </button>
                </div>
              </div>
              <p v-if="form.supplier" class="text-lg text-[var(--color-success)] px-[20px]">Mapped: {{ form.supplier }}</p>
            </div>

            <div class="space-y-[4px]">
              <label class="text-2xl font-bold text-[var(--color-text-muted)] uppercase tracking-wider px-[20px]">Supplier Part No</label>
              <input ref="supplierPartNoInput" v-model="form.supplier_part_no" type="text" :disabled="!form.supplier" class="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-[20px] py-[12px] font-mono text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition-all disabled:opacity-40 disabled:cursor-not-allowed" placeholder="SKU..." @keydown.enter.prevent="handleSubmit" />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-[20px] py-[12px] bg-[var(--color-surface)] border-t border-[var(--color-border)] flex gap-[8px]">
        <button
          @click="$emit('close')"
          class="flex-1 rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-muted)] bg-[var(--color-surface-raised)] border border-[var(--color-border)] hover:bg-[var(--color-midlight)] transition-all active:scale-95"
        >
          Cancel
        </button>
        <button
          @click="handleSubmit"
          :disabled="isSubmitting || !canSubmit"
          class="flex-[2] rounded-xl py-[12px] text-2xl font-bold uppercase tracking-widest text-[var(--color-text-on-highlight)] transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none shadow-lg flex items-center justify-center gap-[8px]"
          :class="canSubmit ? 'bg-[var(--color-info)] hover:bg-[var(--color-info)]/80' : 'bg-[var(--color-surface-raised)]'"
        >
          <span v-if="isSubmitting" class="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>{{ isEditMode ? 'Update Item' : 'Create Item' }}</span>
          <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
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

// ── Field cache (item_group, hsn_sac, stock_uom, item_tax_template, supplier) ─
const CACHE_KEY = 'ic-field-cache'

function loadCache() {
  try { return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}') } catch { return {} }
}

function saveCache() {
  const c = {
    item_group:        form.value.item_group,
    hsn_sac:           form.value.hsn_sac,
    stock_uom:         form.value.stock_uom,
    item_tax_template: form.value.item_tax_template,
    supplier:          form.value.supplier,
    supplier_label:    supplierSearch.value,
  }
  localStorage.setItem(CACHE_KEY, JSON.stringify(c))
}

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
  form.value.extra_barcodes.push({ barcode: '', uom: form.value.stock_uom })
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

// Sync Item Print Name from Item Name by default (only if empty or matching)
watch(() => form.value.item_name, (newVal) => {
  if (!isEditMode.value) {
    form.value.item_print_name = newVal
  }
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

const availableUoms = computed(() => {
  const list = [form.value.stock_uom]
  form.value.uom_conversions.forEach(c => {
    if (c.uom && !list.includes(c.uom)) list.push(c.uom)
  })
  return list
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
      saveCache()
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
      saveCache()
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
  const cache = loadCache()
  form.value = {
    item_name: '',
    item_print_name: '',
    barcode: '',
    item_group:        cache.item_group        || metadata.value.item_groups[0]?.name || '',
    hsn_sac:           cache.hsn_sac           || '',
    stock_uom:         cache.stock_uom         || 'Nos',
    item_tax_template: cache.item_tax_template || '',
    standard_rate: 0,
    safety_stock: 0,
    supplier:          cache.supplier          || '',
    supplier_part_no: '',
    uom_conversions: [],
    extra_barcodes: [],
  }
  supplierSearch.value  = cache.supplier_label || ''
  supplierOptions.value = []
  isBarcodeManual.value = false
  autoBarcode.value = ''
  if (selectedSeries.value) generateBarcode()
}

watch(() => props.show, async (newVal) => {
  if (newVal) {
    if (!isEditMode.value) {
      resetForm()
      await loadMetadata()
    } else {
      await loadMetadata()
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})

onMounted(async () => {
  if (props.show) {
    if (!isEditMode.value) resetForm()
    await loadMetadata()
    if (isEditMode.value) {
      await loadForEdit(props.editItemCode)
    }
    nextTick(() => itemNameInput.value?.focus())
  }
})
</script>
