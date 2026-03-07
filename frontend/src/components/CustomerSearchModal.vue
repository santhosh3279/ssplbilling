<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 outline-none" 
    @click.self="handleEsc"
    @keydown="handleGlobalKeydown"
    tabindex="-1"
  >
    <div class="flex h-[90vh] w-[90vw] flex-col rounded-xl bg-white shadow-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="border-b border-gray-200 px-5 py-4 flex items-center justify-between bg-gray-50">
        <div>
          <div class="text-2xl font-semibold text-gray-700">Detailed Customer Search</div>
          <div class="text-lg text-gray-500">View contact info and select customer</div>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="openNewForm" 
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm transition-colors"
          >
            New Customer <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F2</kbd>
          </button>
          <button 
            @click="openEditForm(results[selectedIdx])" 
            v-if="selectedCustomer || results[selectedIdx]"
            class="flex items-center gap-2 rounded-lg border border-gray-300 bg-gray-100 px-4 py-2 text-lg font-semibold text-gray-700 hover:bg-gray-200 shadow-sm transition-colors"
          >
            Edit Details <kbd class="ml-1 rounded border border-gray-300 bg-white px-1.5 py-0.5 font-mono text-xs text-gray-400">F3</kbd>
          </button>
          <button 
            @click="$emit('refresh')" 
            class="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-lg font-semibold text-blue-600 hover:bg-blue-100 transition-colors"
          >
            🔄 Refresh <kbd class="ml-1 rounded border border-blue-200 bg-white px-1.5 py-0.5 font-mono text-xs text-blue-400">F5</kbd>
          </button>
          <button @click="$emit('close')" class="text-2xl text-gray-400 hover:text-gray-600">✕</button>
        </div>
      </div>

      <!-- Search input -->
      <div class="border-b border-gray-100 p-4">
        <input
          ref="searchInput"
          :value="query"
          @input="$emit('update:query', $event.target.value)"
          class="w-full rounded border border-gray-300 px-4 py-3 text-2xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Type customer name or mobile..."
          @keydown.esc.stop="handleEsc"
          @keydown.down.prevent="$emit('update:selectedIdx', Math.min(selectedIdx + 1, results.length - 1))"
          @keydown.up.prevent="$emit('update:selectedIdx', Math.max(selectedIdx - 1, 0))"
          @keydown.enter.prevent="results[selectedIdx] && $emit('select', results[selectedIdx])"
        />
      </div>

      <!-- Results Table -->
      <div class="flex-1 overflow-y-auto">
        <table class="w-full text-2xl">
          <thead class="sticky top-0 bg-white shadow-sm">
            <tr class="text-lg font-bold uppercase tracking-wider text-gray-600 border-b">
              <th class="px-5 py-3 text-left">Customer Name</th>
              <th class="px-5 py-3 text-left">Mobile</th>
              <th class="px-5 py-3 text-left">WhatsApp</th>
              <th class="px-5 py-3 text-left">Address</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="(c, idx) in results"
              :key="c.name"
              class="cursor-pointer hover:bg-blue-100"
              :class="{ 'bg-blue-200': selectedIdx === idx }"
              @click="$emit('select', c)"
              @mouseenter="$emit('update:selectedIdx', idx)"
            >
              <td class="px-5 py-2">
                <div class="font-medium text-gray-800">{{ c.customer_name }}</div>
              </td>
              <td class="px-5 py-2 text-gray-600">{{ c.mobile_no || '--' }}</td>
              <td class="px-5 py-2 text-gray-600">{{ c.whatsapp || '--' }}</td>
              <td class="px-5 py-2 text-gray-500 text-lg truncate max-w-[300px]">
                {{ c.address_line1 }}{{ c.city ? ', ' + c.city : '' }}
              </td>
            </tr>
            <tr v-if="!results.length">
              <td colspan="5" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                No customers found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Detail Footer -->
      <div v-if="results[selectedIdx]" class="border-t border-gray-200 bg-blue-50/30 px-6 py-3">
        <div class="flex flex-wrap items-start gap-x-8 gap-y-2">

          <!-- Balance -->
          <div class="flex flex-col min-w-[130px]">
            <span class="text-[10px] font-bold uppercase text-gray-400">Ledger Balance</span>
            <template v-if="footerLoading">
              <span class="mt-0.5 inline-block h-4 w-24 animate-pulse rounded bg-gray-200"></span>
            </template>
            <template v-else-if="footerStats">
              <span
                class="text-xl font-bold"
                :class="footerStats.balance > 0 ? 'text-red-600' : footerStats.balance < 0 ? 'text-green-600' : 'text-gray-400'"
              >
                &#8377;{{ Math.abs(footerStats.balance).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                <span class="text-xs font-normal uppercase ml-1">
                  {{ footerStats.balance > 0 ? 'DR' : footerStats.balance < 0 ? 'CR' : '' }}
                </span>
              </span>
            </template>
            <template v-else>
              <span class="text-lg text-gray-300">--</span>
            </template>
          </div>

          <!-- Last Invoice -->
          <div class="flex flex-col min-w-[130px]">
            <span class="text-[10px] font-bold uppercase text-gray-400">Last Invoice</span>
            <template v-if="footerLoading">
              <span class="mt-0.5 inline-block h-4 w-20 animate-pulse rounded bg-gray-200"></span>
            </template>
            <template v-else-if="footerStats">
              <span class="text-lg font-semibold text-gray-700">
                {{ footerStats.last_invoice_date
                    ? new Date(footerStats.last_invoice_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                    : 'No invoices' }}
              </span>
            </template>
            <template v-else>
              <span class="text-lg text-gray-300">--</span>
            </template>
          </div>

          <!-- Mobile -->
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">Mobile</span>
            <span class="text-lg font-semibold text-gray-700">{{ results[selectedIdx].mobile_no || '--' }}</span>
          </div>

          <!-- WhatsApp -->
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">WhatsApp</span>
            <span class="text-lg font-semibold text-gray-700">{{ results[selectedIdx].whatsapp || '--' }}</span>
          </div>

          <!-- Address -->
          <div class="flex flex-col flex-1">
            <span class="text-[10px] font-bold uppercase text-gray-400">Address</span>
            <span class="text-lg text-gray-700">
              <template v-if="results[selectedIdx].address_line1">
                {{ results[selectedIdx].address_line1 }}{{ results[selectedIdx].city ? ', ' + results[selectedIdx].city : '' }}
              </template>
              <template v-else>
                <span class="text-gray-300 italic">No address provided</span>
              </template>
            </span>
          </div>

        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-gray-100 bg-gray-50 px-5 py-4 flex items-center justify-between text-lg text-gray-500">
        <div class="flex gap-4">
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F2</kbd> New</span>
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F3</kbd> Edit</span>
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">F5</kbd> Refresh</span>
          <span><kbd class="rounded border bg-white px-2 py-1 font-mono">Enter</kbd> Select</span>
        </div>
        <button @click="$emit('close')" class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-50 transition-colors">Close</button>
      </div>

      <!-- SUB-MODALS (New / Edit) -->
      <div v-if="showNewForm || showEditForm" class="absolute inset-0 z-[60] flex items-center justify-center bg-black/40" @click.self="handleEsc">
        <div class="w-[600px] rounded-xl bg-white shadow-2xl overflow-hidden">
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
            <!-- Form Fields -->
            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Customer Name *</label>
              <input 
                ref="formNameInput" 
                v-model="(showNewForm ? newData : editData).customer_name" 
                class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" 
                placeholder="Full name"
                @keydown.esc.stop="handleEsc"
                @keydown.enter.prevent="submitForm"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile Number *</label>
                <input 
                  v-model="(showNewForm ? newData : editData).mobile" 
                  class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" 
                  placeholder="10-digit mobile" 
                  maxlength="10"
                  @keydown.esc.stop="handleEsc" 
                />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">WhatsApp Number</label>
                <input 
                  v-model="(showNewForm ? newData : editData).whatsapp" 
                  class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" 
                  placeholder="10-digit whatsapp" 
                  maxlength="10"
                  @keydown.esc.stop="handleEsc" 
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
                <input v-model="(showNewForm ? newData : editData).email" type="email" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">GSTIN</label>
                <input v-model="(showNewForm ? newData : editData).gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-base uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc.stop="handleEsc" />
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 1</label>
              <input v-model="(showNewForm ? newData : editData).address_line1" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc.stop="handleEsc" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 2</label>
              <input v-model="(showNewForm ? newData : editData).address_line2" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Area / Locality" @keydown.esc.stop="handleEsc" />
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">City</label>
                <input v-model="(showNewForm ? newData : editData).city" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="City" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Pincode</label>
                <input 
                  v-model="(showNewForm ? newData : editData).pincode" 
                  class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" 
                  placeholder="678XXX" 
                  maxlength="6"
                  @keydown.esc.stop="handleEsc" 
                />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">State</label>
                <select
                  v-model="(showNewForm ? newData : editData).state"
                  class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500"
                  @keydown.esc.stop="handleEsc"
                >
                  <option value="">Select State</option>
                  <option v-for="s in indianStates" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50">
            <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-100 transition-colors" @click="closeSubForm">Cancel</button>
            <button 
              class="rounded px-6 py-2 font-bold text-white shadow-md flex items-center gap-2 transition-all active:scale-95" 
              :class="showNewForm ? 'bg-blue-600 hover:bg-blue-700' : 'bg-orange-600 hover:bg-orange-700'"
              @click="submitForm"
              :disabled="saving || editLoading"
            >
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
import { ref, nextTick, watch } from 'vue'
import { fetchCustomerDetails } from '../api/customer.js'
import { frappeGet } from '../api.js'


const props = defineProps({
  show: Boolean,
  query: String,
  results: {
    type: Array,
    default: () => []
  },
  selectedIdx: {
    type: Number,
    default: 0
  },
  selectedCustomer: Object,
  saving: Boolean
})

const emit = defineEmits([
  'close',
  'update:query',
  'update:selectedIdx',
  'select',
  'refresh',
  'save-new',
  'save-edit'
])

const searchInput = ref(null)
const formNameInput = ref(null)

const showNewForm = ref(false)
const showEditForm = ref(false)
const editLoading = ref(false)

// States listed first (alphabetical), then Union Territories — must match ERPNext State doctype exactly
const indianStates = [
  // States
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  // Union Territories
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

function handleEsc() {
  if (showNewForm.value || showEditForm.value) {
    closeSubForm()
  } else {
    emit('close')
  }
}

function handleGlobalKeydown(e) {
  // If a sub-form is open, handle End key for submission
  if (showNewForm.value || showEditForm.value) {
    if (e.key === 'End') {
      e.preventDefault()
      submitForm()
    }
    return
  }

  if (e.key === 'F2') {
    e.preventDefault()
    openNewForm()
  } else if (e.key === 'F3') {
    e.preventDefault()
    const current = props.results[props.selectedIdx] || props.selectedCustomer
    if (current) openEditForm(current)
  } else if (e.key === 'F5') {
    e.preventDefault()
    emit('refresh')
  }
}

function focus() {
  nextTick(() => {
    if (showNewForm.value || showEditForm.value) {
      formNameInput.value?.focus()
    } else {
      searchInput.value?.focus()
      searchInput.value?.select()
    }
  })
}

defineExpose({ focus, closeSubForm })

// ── Footer live stats (balance + last invoice) ────────────────────────────────
const footerStats = ref(null)   // { balance, last_invoice_date } or null
const footerLoading = ref(false)
let statsTimer = null

watch(() => props.selectedIdx, (idx) => {
  clearTimeout(statsTimer)
  footerStats.value = null
  const customer = props.results[idx]
  if (!customer) return
  statsTimer = setTimeout(async () => {
    footerLoading.value = true
    try {
      footerStats.value = await frappeGet(
        'ssplbilling.api.sales_api.get_customer_quick_stats',
        { customer: customer.name }
      )
    } catch { /* silently ignore */ }
    footerLoading.value = false
  }, 350)
})

watch(() => props.show, (newVal) => {
  if (newVal) {
    focus()
  } else {
    showNewForm.value = false
    showEditForm.value = false
  }
})

function openNewForm() {
  newData.value = { 
    customer_name: props.query.trim(), mobile: '', whatsapp: '', email: '', gstin: '', 
    address_line1: '', address_line2: '', 
    city: 'Palakkad', pincode: '678000', state: 'Kerala' 
  }
  showNewForm.value = true
  focus()
}

async function openEditForm(c) {
  const target = c || props.selectedCustomer
  if (!target) return

  // Show the form immediately with whatever data we have from the search result
  editData.value = {
    name: target.name,
    customer_name: target.customer_name || '',
    mobile: target.mobile_no || '',
    whatsapp: '',
    email: target.email_id || '',
    gstin: target.gstin || '',
    address_line1: target.address_line1 || '',
    address_line2: target.address_line2 || '',
    city: target.city || '',
    pincode: target.pincode || '',
    state: target.state || 'Kerala',
  }
  showEditForm.value = true
  editLoading.value = true
  focus()

  try {
    const full = await fetchCustomerDetails(target.name)
    // Merge fetched details into editData
    // We expect full to contain address fields and whatsapp from contact
    editData.value = { ...editData.value, ...full }
  } catch (e) {
    console.warn('[CustomerSearchModal] fetchCustomerDetails failed:', e.message)
  } finally {
    editLoading.value = false
  }
}

function closeSubForm() {
  showNewForm.value = false
  showEditForm.value = false
  focus()
}

function validateForm(data) {
  if (!data.customer_name.trim()) {
    alert('Customer Name is required')
    return false
  }
  if (!data.mobile || !/^\d{10}$/.test(data.mobile)) {
    alert('Please enter a valid 10-digit Mobile Number')
    return false
  }
  if (data.whatsapp && !/^\d{10}$/.test(data.whatsapp)) {
    alert('Please enter a valid 10-digit WhatsApp Number')
    return false
  }
  if (data.pincode && !/^\d{6}$/.test(data.pincode)) {
    alert('Please enter a valid 6-digit Pincode')
    return false
  }
  return true
}

function submitForm() {
  const data = showNewForm.value ? newData.value : editData.value
  if (!validateForm(data)) return

  if (showNewForm.value) {
    emit('save-new', data)
  } else if (showEditForm.value) {
    emit('save-edit', data)
  }
}
</script>
