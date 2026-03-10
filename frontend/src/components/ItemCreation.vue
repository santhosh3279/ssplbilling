<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
        <div>
          <h3 class="text-xl font-bold text-slate-800">Create New Item</h3>
          <p class="text-sm text-slate-500">Add a new item to the system</p>
        </div>
        <button 
          @click="$emit('close')" 
          class="text-slate-400 hover:text-slate-600 transition-colors p-2 hover:bg-slate-100 rounded-full"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Main Info -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-1.5 md:col-span-2">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Item Name *</label>
            <input 
              ref="itemNameInput"
              v-model="form.item_name"
              type="text"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-lg font-medium outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-50 transition-all"
              placeholder="Enter full item name..."
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Barcode / Code</label>
            <div class="flex gap-2">
              <input 
                v-model="form.barcode"
                type="text"
                class="flex-1 rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 font-mono text-base outline-none focus:border-blue-500 focus:bg-white transition-all"
                placeholder="Auto or manual..."
              />
              <select 
                v-model="selectedSeries"
                class="w-24 rounded-xl border border-slate-200 bg-white px-2 text-xs font-bold outline-none focus:border-blue-500"
                @change="generateBarcode"
              >
                <option value="">Series</option>
                <option v-for="s in metadata.naming_series" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Item Group *</label>
            <select 
              v-model="form.item_group"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-base outline-none focus:border-blue-500 focus:bg-white transition-all appearance-none"
            >
              <option value="">Select Group...</option>
              <option v-for="g in metadata.item_groups" :key="g.name" :value="g.name">{{ g.name }}</option>
            </select>
          </div>

          <div class="space-y-1.5 relative">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">HSN/SAC Code</label>
            <input 
              v-model="form.hsn_sac"
              type="text"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-base outline-none focus:border-blue-500 focus:bg-white transition-all"
              placeholder="Search code..."
              @input="onHSNInput"
            />
            <div v-if="hsnResults.length > 0" class="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-y-auto rounded-xl bg-white p-1 shadow-xl border border-slate-100">
              <button
                v-for="res in hsnResults"
                :key="res.name"
                class="w-full rounded-lg px-4 py-2 text-left text-sm hover:bg-blue-50 hover:text-blue-600 transition-colors"
                @click="selectHSN(res.name)"
              >
                {{ res.name }}
              </button>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Default UOM *</label>
            <select 
              v-model="form.stock_uom"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-base outline-none focus:border-blue-500 focus:bg-white transition-all appearance-none"
            >
              <option v-for="u in metadata.uoms" :key="u.name" :value="u.name">{{ u.name }}</option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Standard Rate (Selling)</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-slate-400">₹</span>
              <input 
                v-model.number="form.standard_rate"
                type="number"
                class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-4 text-right font-mono text-lg font-bold text-slate-700 outline-none focus:border-emerald-500 focus:bg-white transition-all"
                placeholder="0.00"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Safety Stock</label>
            <input 
              v-model.number="form.safety_stock"
              type="number"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-right font-mono text-lg text-slate-700 outline-none focus:border-blue-500 focus:bg-white transition-all"
              placeholder="0"
            />
          </div>

          <div class="space-y-1.5 md:col-span-2">
            <label class="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-1">Tax Template</label>
            <select 
              v-model="form.item_tax_template"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 px-4 text-base outline-none focus:border-blue-500 focus:bg-white transition-all appearance-none"
            >
              <option value="">No Tax / Exempt</option>
              <option v-for="t in metadata.tax_templates" :key="t.name" :value="t.name">{{ t.name }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex gap-3">
        <button 
          @click="$emit('close')"
          class="flex-1 rounded-xl py-3 text-sm font-bold uppercase tracking-widest text-slate-500 bg-white border border-slate-200 hover:bg-slate-50 transition-all active:scale-95"
        >
          Cancel
        </button>
        <button 
          @click="handleSubmit"
          :disabled="isSubmitting || !canSubmit"
          class="flex-[2] rounded-xl py-3 text-sm font-bold uppercase tracking-widest text-white transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none shadow-lg shadow-blue-100 flex items-center justify-center gap-2"
          :class="canSubmit ? 'bg-blue-600 hover:bg-blue-700' : 'bg-slate-300'"
        >
          <span v-if="isSubmitting" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
          <span v-else>Create Item</span>
          <svg v-if="!isSubmitting" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { fetchItemCreationMetadata, getNextBarcode, createItem, fetchHSNCodes } from '../api.js'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'created'])

const itemNameInput = ref(null)
const isSubmitting = ref(false)
const selectedSeries = ref('')
const hsnResults = ref([])

const form = ref({
  item_name: '',
  barcode: '',
  item_group: '',
  hsn_sac: '',
  stock_uom: 'Nos',
  standard_rate: 0,
  safety_stock: 0,
  item_tax_template: ''
})

const metadata = ref({
  item_groups: [],
  uoms: [],
  tax_templates: [],
  naming_series: []
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
    
    if (data.naming_series?.length && !selectedSeries.value) {
      selectedSeries.value = data.naming_series[0]
      generateBarcode()
    }
  } catch (e) {
    console.warn('Failed to load item metadata', e)
  }
}

async function generateBarcode() {
  if (!selectedSeries.value) return
  try {
    const res = await getNextBarcode(selectedSeries.value)
    form.value.barcode = res
  } catch (e) {
    console.error('Failed to generate barcode', e)
  }
}

let hsnTimeout = null
function onHSNInput() {
  clearTimeout(hsnTimeout)
  if (!form.value.hsn_sac) {
    hsnResults.value = []
    return
  }
  hsnTimeout = setTimeout(async () => {
    try {
      const res = await fetchHSNCodes(form.value.hsn_sac)
      hsnResults.value = res || []
    } catch (e) {
      hsnResults.value = []
    }
  }, 300)
}

function selectHSN(name) {
  form.value.hsn_sac = name
  hsnResults.value = []
}

async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return
  
  isSubmitting.value = true
  try {
    const name = await createItem(form.value)
    alert(`Item ${name} created successfully!`)
    emit('created', {
      item_code: form.value.barcode || name,
      item_name: form.value.item_name,
      price: form.value.standard_rate,
      uom: form.value.stock_uom,
      tax_rate: 0 // Will be fetched by search enrichment
    })
    resetForm()
  } catch (e) {
    alert('Failed to create item: ' + e.message)
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  form.value = {
    item_name: '',
    barcode: '',
    item_group: metadata.value.item_groups[0]?.name || '',
    hsn_sac: '',
    stock_uom: 'Nos',
    standard_rate: 0,
    safety_stock: 0,
    item_tax_template: ''
  }
  if (selectedSeries.value) generateBarcode()
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadMetadata()
    nextTick(() => itemNameInput.value?.focus())
  }
})

onMounted(() => {
  if (props.show) {
    loadMetadata()
    nextTick(() => itemNameInput.value?.focus())
  }
})
</script>
