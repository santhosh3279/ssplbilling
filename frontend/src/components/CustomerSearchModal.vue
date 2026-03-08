<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 outline-none" 
    @click.self="handleEsc"
    @keydown="handleGlobalKeydown"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[95vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between bg-gray-50">
        <div>
          <div class="text-2xl font-semibold text-gray-700">Detailed Ledger Search</div>
          <div class="text-lg text-gray-500">Search Customers, Suppliers, and Accounting Ledgers</div>
        </div>
        <div class="flex items-center gap-3">
          <!-- Quick Filter Tabs -->
          <div class="flex rounded-lg border border-gray-300 bg-white p-1 shadow-sm mr-4">
            <button 
              v-for="t in ['All', 'Customer', 'Supplier', 'Account']" 
              :key="t"
              @click="activeType = t"
              class="px-4 py-1.5 text-sm font-bold transition-all rounded-md"
              :class="activeType === t ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-100'"
            >
              {{ t }}
            </button>
          </div>

          <button 
            @click="openNewForm" 
            v-if="activeType === 'Customer'"
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 shadow-sm transition-colors"
          >
            New Customer <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F2</kbd>
          </button>
          <button 
            @click="openEditForm(results[selectedIdx])" 
            v-if="results[selectedIdx] && results[selectedIdx].type === 'Customer'"
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 shadow-sm transition-colors"
          >
            Edit Details <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F3</kbd>
          </button>
          <button 
            @click="preloadLedger" 
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 transition-colors"
          >
            🔄 Refresh <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-gray-400">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-gray-100 p-4 relative">
        <input
          ref="searchInput"
          v-model="query"
          class="w-full rounded border border-gray-300 px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Search by Name, Mobile, WhatsApp, GST, City..."
          @keydown.esc.stop="handleEsc"
        />
        <div v-if="loading" class="absolute right-8 top-1/2 -translate-y-1/2">
          <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></span>
        </div>
      </div>

      <!-- Results Table -->
      <div ref="scrollContainer" class="flex-1 overflow-y-auto">
        <table class="w-full text-2xl">
          <thead class="sticky top-0 bg-white shadow-sm z-10">
            <tr class="text-lg font-bold uppercase tracking-wider text-gray-600 border-b bg-gray-50">
              <th class="px-5 py-3 text-left w-24">Type</th>
              <th class="px-5 py-3 text-left">Ledger Name</th>
              <th class="px-5 py-3 text-left">ID / Code</th>
              <th class="px-5 py-3 text-right">Balance</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="(c, idx) in results"
              :key="c.name"
              class="cursor-pointer transition-colors"
              :class="{ 'bg-blue-200': selectedIdx === idx, 'hover:bg-gray-50': selectedIdx !== idx }"
              @click="handleSelect(c)"
            >
              <td class="px-5 py-3">
                <span 
                  class="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-tight"
                  :class="{
                    'bg-blue-100 text-blue-700': c.type === 'Customer',
                    'bg-orange-100 text-orange-700': c.type === 'Supplier',
                    'bg-gray-100 text-gray-700': c.type === 'Account'
                  }"
                >
                  {{ c.type }}
                </span>
              </td>
              <td class="px-5 py-3">
                <div class="font-medium text-gray-800">{{ c.label }}</div>
              </td>
              <td class="px-5 py-3 text-gray-400 font-mono text-base">
                {{ c.name }}
              </td>
              <td class="px-5 py-3 text-right">
                <span 
                  class="font-bold whitespace-nowrap"
                  :class="(c.balance || 0) > 0 ? 'text-red-600' : (c.balance || 0) < 0 ? 'text-green-600' : 'text-gray-400'"
                >
                  {{ Math.abs(c.balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                  <span class="text-xs font-normal uppercase ml-0.5">
                    {{ (c.balance || 0) > 0 ? 'DR' : (c.balance || 0) < 0 ? 'CR' : '' }}
                  </span>
                </span>
              </td>
            </tr>
            <tr v-if="!results.length && !loading">
              <td colspan="3" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                No ledgers found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Detail Panel (Moved to Footer) -->
      <div v-if="results[selectedIdx]" class="border-t border-gray-200 bg-white px-8 py-6">
        <div class="flex items-start gap-4">

          <!-- Last Invoice (Customer Only) -->
          <div class="flex flex-col shrink-0" style="width: 10%">
            <span class="text-sm font-bold uppercase text-gray-400 truncate">Last Inv</span>
            <span class="text-xl font-semibold text-gray-700 truncate">
              {{ results[selectedIdx].last_invoice_date
                  ? new Date(results[selectedIdx].last_invoice_date).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: '2-digit' })
                  : 'None' }}
            </span>
          </div>

          <!-- WhatsApp -->
          <div class="flex flex-col shrink-0" style="width: 10%">
            <span class="text-sm font-bold uppercase text-gray-400 truncate">WhatsApp</span>
            <span class="text-2xl font-semibold text-gray-700 truncate">{{ results[selectedIdx].whatsapp || '--' }}</span>
          </div>

          <!-- Email -->
          <div class="flex flex-col shrink-0" style="width: 20%">
            <span class="text-sm font-bold uppercase text-gray-400 truncate">Email</span>
            <span class="text-xl font-semibold text-gray-700 truncate">{{ results[selectedIdx].email || '--' }}</span>
          </div>

          <!-- Address -->
          <div class="flex flex-col shrink-0" style="width: 45%">
            <span class="text-sm font-bold uppercase text-gray-400 truncate">Address</span>
            <span class="text-xl text-gray-700 line-clamp-2 leading-tight">
              {{ getCustomerAddressFormatted(results[selectedIdx]) }}
            </span>
          </div>

          <!-- GSTIN (Right End) -->
          <div class="flex flex-col shrink-0" style="width: 15%">
            <span class="text-sm font-bold uppercase text-gray-400 truncate">GSTIN</span>
            <span class="text-2xl font-semibold text-gray-700 font-mono truncate">{{ results[selectedIdx].gstin || '--' }}</span>
          </div>

        </div>
      </div>

      <!-- SUB-MODALS (New / Edit / Date) -->
      <div v-if="showNewForm || showEditForm || showDateModal" class="absolute inset-0 z-[60] flex items-center justify-center bg-black/40" @click.self="handleEsc">
        
        <!-- Date Range Sub-window -->
        <DateFilter
          v-if="showDateModal"
          :show="showDateModal"
          :customer-name="results[selectedIdx]?.label"
          @close="showDateModal = false"
          @confirm="handleDateConfirm"
        />

        <!-- New / Edit Form (Customer Only) -->
        <div v-if="showNewForm || showEditForm" class="w-[600px] rounded-xl bg-white shadow-2xl overflow-hidden">
          <div class="border-b border-gray-200 px-5 py-4 bg-gray-50">
            <div class="text-xl font-bold text-gray-700">{{ showNewForm ? 'New Customer' : 'Modify Customer Details' }}</div>
            <div class="text-sm text-gray-600 flex items-center gap-2">
              <template v-if="showEditForm && editLoading">
                <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-400 border-t-transparent"></span>
                Loading from ERPNext…
              </template>
              <template v-else>
                {{ showNewForm ? 'Enter customer details to create a new record' : ('Update information for ' + (editData.customer_name || '')) }}
              </template>
            </div>
          </div>
          
          <div class="flex flex-col gap-4 px-6 py-5 max-h-[70vh] overflow-y-auto">
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Customer Name *</label>
              <input ref="formNameInput" v-model="(showNewForm ? newData : editData).customer_name" class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Full name" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile Number *</label>
                <input v-model="(showNewForm ? newData : editData).mobile" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="10-digit mobile" maxlength="10" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">WhatsApp Number</label>
                <input v-model="(showNewForm ? newData : editData).whatsapp" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="10-digit whatsapp" maxlength="10" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
                <input v-model="(showNewForm ? newData : editData).email" type="email" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">GSTIN</label>
                <input v-model="(showNewForm ? newData : editData).gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-base uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 1</label>
              <input v-model="(showNewForm ? newData : editData).address_line1" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">City</label>
                <input v-model="(showNewForm ? newData : editData).city" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="City" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Pincode</label>
                <input v-model="(showNewForm ? newData : editData).pincode" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="678XXX" maxlength="6" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">State</label>
                <select v-model="(showNewForm ? newData : editData).state" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" @keydown.esc.stop="handleEsc" @keydown.enter.prevent="handleFormEnter" >
                  <option value="">Select State</option>
                  <option v-for="s in indianStates" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50">
            <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 transition-colors" @click="closeSubForm">Cancel</button>
            <button class="rounded px-6 py-2 font-bold text-white shadow-md flex items-center gap-2 transition-all active:scale-95" :class="showNewForm ? 'bg-blue-600' : 'bg-orange-600'" @click="submitForm" :disabled="saving || editLoading">
              {{ saving ? (showNewForm ? 'Saving...' : 'Updating...') : (showNewForm ? 'Save & Select' : 'Update Details') }}
              <kbd class="rounded border px-1.5 py-0.5 font-mono text-xs shadow-sm" :class="showNewForm ? 'border-blue-500 bg-blue-500' : 'border-orange-500 bg-orange-500'">End</kbd>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue'
import { fetchCustomerDetails, createCustomer, updateCustomer } from '../api/customer.js'
import { frappeGet } from '../api.js'
import DateFilter from './DateFilter.vue'

const props = defineProps({
  show: Boolean,
  skipDateFilter: {
    type: Boolean,
    default: false
  },
  initialType: {
    type: String,
    default: 'All'
  }
})

const emit = defineEmits(['close', 'select'])

// Internal State
const query = ref('')
const allLedgers = ref([]) 
const activeType = ref(props.initialType) 
const selectedIdx = ref(0)
const loading = ref(false)
const saving = ref(false)

const searchInput = ref(null)
const formNameInput = ref(null)
const scrollContainer = ref(null)

const showNewForm = ref(false)
const showEditForm = ref(false)
const showDateModal = ref(false)
const editLoading = ref(false)

const indianStates = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
  "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

const newData = ref({ 
  customer_name: '', mobile: '', whatsapp: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', 
  city: 'Palakkad', pincode: '678000', state: 'Kerala' 
})

const editData = ref({ 
  customer_name: '', mobile: '', whatsapp: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', 
  city: '', pincode: '', state: '' 
})

// ─── Data Preloading ─────────────────────────────────────────────────────────

async function preloadLedger() {
  loading.value = true
  try {
    const data = await frappeGet('ssplbilling.api.customersearch_api.get_all_ledgers')
    allLedgers.value = data || []
  } catch (e) {
    console.error('[CustomerSearchModal] Preload failed:', e)
  } finally {
    loading.value = false
  }
}

// ─── Local Filtering ─────────────────────────────────────────────────────────

const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  let list = allLedgers.value

  // Type Filter
  if (activeType.value !== 'All') {
    list = list.filter(l => l.type === activeType.value)
  }

  // Search Filter
  if (!q) return list

  return list.filter(l => {
    return (l.label || '').toLowerCase().includes(q) ||
           (l.name || '').toLowerCase().includes(q) ||
           (l.mobile_no || '').includes(q) ||
           (l.whatsapp || '').includes(q) ||
           (l.gstin || '').toLowerCase().includes(q) ||
           (l.city || '').toLowerCase().includes(q) ||
           (l.email || '').toLowerCase().includes(q)
  })
})

watch([query, activeType], () => {
  selectedIdx.value = 0
})

function getCustomerAddressFormatted(c) {
  if (c.type === 'Account') return 'General Accounting Ledger'
  const parts = [c.address_line1, c.city].filter(Boolean)
  return parts.join(', ') || 'No address provided'
}

// ─── Navigation & Events ─────────────────────────────────────────────────────

function handleEsc() {
  if (showNewForm.value || showEditForm.value || showDateModal.value) {
    closeSubForm()
  } else {
    emit('close')
  }
}

function handleGlobalKeydown(e) {
  if (showNewForm.value || showEditForm.value) {
    if (e.key === 'End') {
      e.preventDefault()
      submitForm()
    }
    return
  }
  
  if (showDateModal.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, results.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  } else if (e.key === 'Enter') {
    const item = results.value[selectedIdx.value]
    if (item) {
      e.preventDefault()
      handleSelect(item)
    }
  } else if (e.key === 'F2') {
    e.preventDefault()
    if (activeType.value === 'Customer') openNewForm()
  } else if (e.key === 'F3') {
    e.preventDefault()
    const item = results.value[selectedIdx.value]
    if (item && item.type === 'Customer') openEditForm(item)
  } else if (e.key === 'F5') {
    e.preventDefault()
    preloadLedger()
  }
}

function handleSelect(item) {
  if (props.skipDateFilter) {
    emit('select', item)
  } else {
    showDateModal.value = true
  }
}

function handleDateConfirm(dates) {
  const item = results.value[selectedIdx.value]
  if (item) {
    showDateModal.value = false
    emit('select', item, dates)
  }
}

function focus() {
  nextTick(() => {
    if (showNewForm.value || showEditForm.value) {
      formNameInput.value?.focus()
    } else {
      searchInput.value?.focus()
    }
  })
}

defineExpose({ focus, closeSubForm })

watch(selectedIdx, async (idx) => {
  await nextTick()
  const container = scrollContainer.value
  const activeRow = container?.querySelector(`tbody tr:nth-child(${idx + 1})`)
  
  if (container && activeRow) {
    const rowTop = activeRow.offsetTop
    const rowBottom = rowTop + activeRow.offsetHeight
    const containerScrollTop = container.scrollTop
    const containerHeight = container.offsetHeight
    const headerHeight = container.querySelector('thead')?.offsetHeight || 50

    if (rowTop < containerScrollTop + headerHeight) {
      container.scrollTop = rowTop - headerHeight
    } else if (rowBottom > containerScrollTop + containerHeight) {
      container.scrollTop = rowBottom - containerHeight
    }
  }
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    query.value = ''
    preloadLedger()
    focus()
  } else {
    closeSubForm()
  }
})

// ─── Sub-Form Logic (Customer Only) ──────────────────────────────────────────

function openNewForm() {
  newData.value = { 
    customer_name: query.value.trim(), mobile: '', whatsapp: '', email: '', gstin: '', 
    address_line1: '', address_line2: '', 
    city: 'Palakkad', pincode: '678000', state: 'Kerala' 
  }
  showNewForm.value = true
  focus()
}

async function openEditForm(target) {
  if (!target || target.type !== 'Customer') return
  editData.value = {
    name: target.name,
    customer_name: target.label || '',
    mobile: target.mobile_no || '',
    whatsapp: target.whatsapp || '',
    email: target.email || '',
    gstin: target.gstin || '',
    address_line1: target.address_line1 || '',
    address_line2: '',
    city: target.city || '',
    pincode: target.pincode || '',
    state: target.state || 'Kerala',
  }
  showEditForm.value = true
  editLoading.value = true
  focus()

  try {
    const full = await fetchCustomerDetails(target.name)
    editData.value = { ...editData.value, ...full }
  } catch (e) {
    console.warn('[CustomerSearchModal] fetch details failed:', e)
  } finally {
    editLoading.value = false
  }
}

function closeSubForm() {
  showNewForm.value = false
  showEditForm.value = false
  showDateModal.value = false
  focus()
}

function validateForm(data) {
  if (!data.customer_name.trim()) { alert('Customer Name is required'); return false }
  if (!data.mobile || !/^\d{10}$/.test(data.mobile)) { alert('Valid 10-digit Mobile required'); return false }
  return true
}

function handleFormEnter(e) {
  const form = e.target.closest('.flex-col.gap-4')
  if (!form) return
  const focusables = Array.from(form.querySelectorAll('input, select, button'))
  const index = focusables.indexOf(e.target)
  if (index > -1 && index < focusables.length - 1) focusables[index + 1].focus()
  else submitForm()
}

async function submitForm() {
  const data = showNewForm.value ? newData.value : editData.value
  if (!validateForm(data)) return

  saving.value = true
  try {
    let result
    if (showNewForm.value) {
      result = await createCustomer(data)
    } else {
      result = await updateCustomer(data.name, data)
    }
    
    await preloadLedger()
    
    const savedName = result.name || result.customer_name
    const foundIdx = results.value.findIndex(c => c.name === savedName)
    if (foundIdx !== -1) selectedIdx.value = foundIdx

    if (showNewForm.value) {
       handleSelect(results.value[selectedIdx.value])
    } else {
       closeSubForm()
    }
  } catch (e) {
    alert('Failed to save customer: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>
