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
              <th class="px-5 py-3 text-left">Mobile Number</th>
              <th class="px-5 py-3 text-right">Balance</th>
              <th class="px-5 py-3 text-left">Address</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="(c, idx) in results"
              :key="c.name"
              class="cursor-pointer hover:bg-blue-50/50"
              :class="{ 'bg-blue-50': selectedIdx === idx }"
              @click="$emit('select', c)"
              @mouseenter="$emit('update:selectedIdx', idx)"
            >
              <td class="px-5 py-2">
                <div class="font-medium text-gray-800">{{ c.customer_name }}</div>
              </td>
              <td class="px-5 py-2 text-gray-600">
                {{ c.mobile_no || '--' }}
              </td>
              <td class="px-5 py-2 text-right">
                <span :class="c.balance > 0 ? 'text-red-600' : c.balance < 0 ? 'text-green-600' : 'text-gray-400'" class="font-bold">
                  &#8377;{{ (c.balance || 0).toFixed(2) }}
                </span>
              </td>
              <td class="px-5 py-2 text-gray-500 text-lg truncate max-w-[300px]">
                {{ c.address_line1 }}{{ c.city ? ', ' + c.city : '' }}
              </td>
            </tr>
            <tr v-if="!results.length">
              <td colspan="4" class="px-5 py-12 text-center text-gray-400 text-xl italic">
                No customers found matching "{{ query }}"
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Detail Footer -->
      <div v-if="results[selectedIdx]" class="border-t border-gray-200 bg-blue-50/30 px-6 py-3">
        <div class="flex flex-wrap gap-x-8 gap-y-2">
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">Current Balance</span>
            <span class="text-xl font-bold" :class="results[selectedIdx].balance > 0 ? 'text-red-600' : 'text-green-600'">
              &#8377;{{ (results[selectedIdx].balance || 0).toFixed(2) }}
              <span class="text-xs font-normal uppercase ml-1">{{ results[selectedIdx].balance > 0 ? 'Debit' : 'Credit' }}</span>
            </span>
          </div>
          <div class="flex flex-col flex-1">
            <span class="text-[10px] font-bold uppercase text-gray-400">Address</span>
            <span class="text-lg text-gray-700">
              <template v-if="results[selectedIdx].address_line1">
                {{ results[selectedIdx].address_line1 }}{{ results[selectedIdx].city ? ', ' + results[selectedIdx].city : '' }}{{ results[selectedIdx].pincode ? ' - ' + results[selectedIdx].pincode : '' }}
              </template>
              <template v-else>
                <span class="text-gray-300 italic">No address provided</span>
              </template>
            </span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-bold uppercase text-gray-400">Mobile</span>
            <span class="text-lg text-gray-700">{{ results[selectedIdx].mobile_no || '--' }}</span>
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
            <div class="text-sm text-gray-600">
              {{ showNewForm ? 'Enter customer details to create a new record' : ('Update information for ' + (editData.customer_name || '')) }}
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

            <div class="grid grid-cols-3 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile</label>
                <input v-model="(showNewForm ? newData : editData).mobile" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="+91 XXXXX XXXXX" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">WhatsApp</label>
                <input v-model="(showNewForm ? newData : editData).whatsapp" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="+91 XXXXX XXXXX" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
                <input v-model="(showNewForm ? newData : editData).email" type="email" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="email@example.com" @keydown.esc.stop="handleEsc" />
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">GSTIN</label>
              <input v-model="(showNewForm ? newData : editData).gstin" class="rounded border border-gray-300 px-3 py-2 font-mono text-base uppercase outline-none focus:border-blue-500" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc.stop="handleEsc" />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 1</label>
              <input v-model="(showNewForm ? newData : editData).address_line1" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Street / Building" @keydown.esc.stop="handleEsc" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 2</label>
                <input v-model="(showNewForm ? newData : editData).address_line2" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Area / Locality" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Address Line 3</label>
                <input v-model="(showNewForm ? newData : editData).address_line3" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="Landmark" @keydown.esc.stop="handleEsc" />
              </div>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">City</label>
                <input v-model="(showNewForm ? newData : editData).city" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="City" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Pincode</label>
                <input v-model="(showNewForm ? newData : editData).pincode" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="678XXX" @keydown.esc.stop="handleEsc" />
              </div>
              <div class="flex flex-col gap-1.5">
                <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">State</label>
                <input v-model="(showNewForm ? newData : editData).state" class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500" placeholder="State" @keydown.esc.stop="handleEsc" />
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50">
            <button class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 hover:bg-gray-100 transition-colors" @click="closeSubForm">Cancel</button>
            <button 
              class="rounded px-6 py-2 font-bold text-white shadow-md flex items-center gap-2 transition-all active:scale-95" 
              :class="showNewForm ? 'bg-blue-600 hover:bg-blue-700' : 'bg-orange-600 hover:bg-orange-700'"
              @click="submitForm"
              :disabled="saving"
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

const newData = ref({ 
  customer_name: '', mobile: '', whatsapp: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', address_line3: '', 
  city: 'Palakkad', pincode: '678000', state: 'Kerala' 
})

const editData = ref({ 
  customer_name: '', mobile: '', whatsapp: '', email: '', gstin: '', 
  address_line1: '', address_line2: '', address_line3: '', 
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
    address_line1: '', address_line2: '', address_line3: '', 
    city: 'Palakkad', pincode: '678000', state: 'Kerala' 
  }
  showNewForm.value = true
  focus()
}

function openEditForm(c) {
  const target = c || props.selectedCustomer
  if (!target) return
  
  editData.value = { 
    name: target.name,
    customer_name: target.customer_name || '', 
    mobile: target.mobile_no || '', 
    whatsapp: target.whatsapp_no || '',
    email: target.email_id || '', 
    gstin: target.gstin || '', 
    address_line1: target.address_line1 || '', 
    address_line2: target.address_line2 || '', 
    address_line3: target.address_line3 || '', 
    city: target.city || '', 
    pincode: target.pincode || '', 
    state: target.state || '' 
  }
  showEditForm.value = true
  focus()
}

function closeSubForm() {
  showNewForm.value = false
  showEditForm.value = false
  focus()
}

function submitForm() {
  if (showNewForm.value) {
    emit('save-new', newData.value)
  } else if (showEditForm.value) {
    emit('save-edit', editData.value)
  }
}
</script>
