<template>
  <div class="w-[1000px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
    <div class="border-b border-[var(--color-border)] px-5 py-4 bg-[var(--color-surface)]">
      <div class="text-xl font-bold text-[var(--color-text)]">{{ isEdit ? 'Modify Customer Details' : 'New Customer' }}</div>
      <div class="text-sm text-[var(--color-text-muted)] flex items-center gap-2">
        <template v-if="isEdit && editLoading">
          <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></span>
          Loading from ERPNext…
        </template>
        <template v-else>
          {{ isEdit ? 'Update information for ' + (form.customer_name || '') : 'Enter customer details to create a new record' }}
        </template>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6 px-6 py-5 max-h-[70vh] overflow-y-auto align-stretch form-fields-container">
      <!-- Column 1: Identity & Grouping -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex justify-between items-center">
            <span>GSTIN</span>
            <button 
              v-if="form.gstin && form.gstin.length === 15"
              @click="fetchGstInfo"
              class="text-[9px] bg-[var(--color-info)] text-white px-2 py-0.5 rounded hover:opacity-80 transition-opacity flex items-center gap-1 shadow-sm"
              :disabled="fetchingGst"
              title="Fetch Details from GST"
            >
              <span v-if="fetchingGst" class="inline-block h-2 w-2 animate-spin rounded-full border border-white border-t-transparent"></span>
              <span>{{ fetchingGst ? 'Fetching...' : 'GST Fetch' }}</span>
            </button>
          </label>
          <input ref="gstinInputRef" v-model="form.gstin" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-base uppercase text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <!-- GST Preview Area -->
        <div v-if="fetchedGstData" class="p-4 bg-[var(--color-info)]/10 border border-[var(--color-info)]/30 rounded-xl text-xs animate-in fade-in slide-in-from-top-2">
          <div class="flex justify-between items-start mb-2">
            <div class="font-bold text-[var(--color-info)] uppercase tracking-wider text-[9px]">Verified Business Found</div>
            <button @click="fetchedGstData = null" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors">✕</button>
          </div>
          <div class="space-y-1 text-[var(--color-text)]">
            <p class="font-bold text-sm">{{ fetchedGstData.business_name }}</p>
            <div class="text-[var(--color-text-muted)]">
              <p>{{ fetchedGstData.address_line1 }}</p>
              <p v-if="fetchedGstData.address_line2">{{ fetchedGstData.address_line2 }}</p>
              <p>{{ fetchedGstData.city }}, {{ fetchedGstData.state }} - {{ fetchedGstData.pincode }}</p>
            </div>
          </div>
          <button 
            @click="applyGstData" 
            class="mt-3 w-full bg-[var(--color-info)] text-white font-bold py-2 rounded-lg hover:brightness-110 transition-all active:scale-95 shadow-md flex items-center justify-center gap-2"
          >
            <span>Fill Form with GST Data</span>
            <kbd class="text-[10px] bg-white/20 px-1.5 rounded">Enter</kbd>
          </button>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer Name *</label>
          <input
            ref="nameInputRef"
            v-model="form.customer_name"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            placeholder="Full name"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="handleFormEnter"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Customer Group *</label>
          <select
            v-model="form.customer_group"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="handleFormEnter"
          >
            <option v-for="cg in customerGroups" :key="cg" :value="cg">{{ cg }}</option>
          </select>
        </div>

        <!-- Primary Party (Party Link) -->
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Primary Party (Link)</label>
          <div class="relative">
            <input
              ref="primaryPartyInputRef"
              v-model="primaryPartyQuery"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
              placeholder="Search Supplier..."
              @input="searchPrimaryParties"
              @keydown.esc.stop="primaryPartyQuery = ''; primaryParties = []"
              @keydown="handlePrimaryPartyKeydown"
            />

            <QuickLedgerSearch 
              ref="quickSearchRef"
              :results="primaryParties"
              :query="primaryPartyQuery"
              :anchor-el="primaryPartyInputRef"
              @select="selectPrimaryParty"
              @close="primaryParties = []"
            />

            <div v-if="form.primary_party" class="mt-1 flex items-center justify-between rounded-lg bg-[var(--color-info)]/10 px-3 py-1.5 text-xs font-bold text-[var(--color-info)]">
              <span>Linked to: {{ form.primary_party }}</span>
              <button @click="form.primary_party = ''; form.primary_party_role = ''; primaryPartyQuery = ''" class="hover:text-red-500">✕</button>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Pricelist Modifier %</label>
          <div class="relative w-full">
            <input v-model.number="form.pricelist_modifier" type="number" step="0.1" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)] pr-8" placeholder="e.g. 10 or -10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
            <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] font-bold">%</span>
          </div>
        </div>
      </div>

      <!-- Column 2: Contact & Tax -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile Number *</label>
          <input v-model="form.mobile" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="10-digit mobile" maxlength="10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">WhatsApp Number</label>
          <input v-model="form.whatsapp" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="10-digit whatsapp" maxlength="10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Email</label>
          <input v-model="form.email" type="email" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="email@example.com" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>
      </div>

      <!-- Column 3: Address & Location -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 1 *</label>
          <input v-model="form.address_line1" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="Street / Building" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 2</label>
          <input v-model="form.address_line2" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="Area / Landmark" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">City</label>
          <input v-model="form.city" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="City" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Pincode</label>
          <input v-model="form.pincode" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="678XXX" maxlength="6" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">State</label>
          <select v-model="form.state" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter">
            <option value="">Select State</option>
            <option v-for="s in indianStates" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
    </div>

    <div class="flex justify-end gap-3 border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
      <button class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-raised)]" @click="$emit('close')">Cancel</button>
      <button
        class="rounded px-6 py-2 font-bold text-[var(--color-text-on-highlight)] shadow-md flex items-center gap-2 transition-all active:scale-95"
        :class="isEdit ? 'bg-[var(--color-supplier)] hover:bg-[var(--color-supplier)]' : 'bg-[var(--color-info)] hover:bg-[var(--color-info)]'"
        @click="submit"
        :disabled="saving || editLoading"
      >
        {{ saving ? (isEdit ? 'Updating...' : 'Saving...') : (isEdit ? 'Update Details' : 'Save & Select') }}
        <kbd class="rounded border px-1.5 py-0.5 font-mono text-xs shadow-sm" :class="isEdit ? 'border-[var(--color-supplier)] bg-[var(--color-supplier)]' : 'border-[var(--color-info)] bg-[var(--color-info)]'">End</kbd>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { fetchCustomerDetails, createCustomer, updateCustomer, fetchCustomerGroups } from '../api/customer.js'
import { validateGstin } from '../api.js'
import { useLedgerCache, searchLedgersInCache } from '../services/ledgerCache'
import QuickLedgerSearch from './QuickLedgerSearch.vue'

const props = defineProps({
  show: Boolean,
  isEdit: { type: Boolean, default: false },
  customerRow: { type: Object, default: null },
  initialName: { type: String, default: '' },
})

const emit = defineEmits(['close', 'saved'])

const nameInputRef = ref(null)
const primaryPartyInputRef = ref(null)
const quickSearchRef = ref(null)
const gstinInputRef = ref(null)

const saving = ref(false)
const editLoading = ref(false)
const fetchingGst = ref(false)
const fetchedGstData = ref(null)
const customerGroups = ref([])

const { ledgers } = useLedgerCache()
const primaryPartyQuery = ref('')
const primaryParties = ref([])

const indianStates = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Andaman and Nicobar Islands', 'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
  'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
]

const defaultForm = () => ({
  customer_name: '', customer_group: 'All Customer Groups',
  mobile: '', whatsapp: '', email: '', gstin: '',
  address_name: '', address_line1: '', address_line2: '',
  city: 'Palakkad', pincode: '678000', state: 'Kerala',
  pricelist_modifier: null,
  primary_party: '',
  primary_party_role: '',
})

const form = ref(defaultForm())

onMounted(async () => {
  // Fetch customer groups
  try {
    const groups = await fetchCustomerGroups()
    customerGroups.value = groups.length ? groups : ['All Customer Groups']
  } catch (e) {
    console.error('[CustomerCreator] fetchCustomerGroups failed:', e)
    customerGroups.value = ['All Customer Groups']
  }

  if (props.isEdit && props.customerRow) {
    const row = props.customerRow
    form.value = {
      name:           row.name,
      customer_name:  row.label          || '',
      customer_group: row.customer_group || 'All Customer Groups',
      mobile:         row.mobile_no      || '',
      whatsapp:       row.whatsapp       || '',
      email:          row.email          || '',
      gstin:          row.gstin          || '',
      address_name:   '',
      address_line1:  row.address_line1  || '',
      address_line2:  '',
      city:           row.city           || '',
      pincode:        row.pincode        || '',
      state:          row.state          || '',
      pricelist_modifier: null,
      primary_party:  '',
      primary_party_role: '',
    }
    primaryPartyQuery.value = ''
    editLoading.value = true
    try {
      const full = await fetchCustomerDetails(row.name)
      const merged = { ...form.value }
      for (const [k, v] of Object.entries(full)) {
        if (k === 'address_name' || v !== '') merged[k] = v
      }
      
      if (merged.primary_party) {
        primaryPartyQuery.value = merged.primary_party
      }
      
      // Reverse calculate modifier percentage
      if (full.pricelist_multiplication_factor != null) {
        const factor = full.pricelist_multiplication_factor
        if (factor === 0 || factor === 1) {
          merged.pricelist_modifier = 0
        } else if (factor > 1) {
          merged.pricelist_modifier = Math.round((factor - 1) * 100 * 100) / 100
        } else if (factor < 1) {
          merged.pricelist_modifier = -Math.round((1 - factor) * 100 * 100) / 100
        }
      }
      
      form.value = merged
    } catch (e) {
      console.warn('[CustomerCreator] fetch customer details failed:', e)
    } finally {
      editLoading.value = false
    }
  } else {
    form.value = { ...defaultForm(), customer_name: props.initialName || '' }
  }
})

function focusFirst() {
  nextTick(() => gstinInputRef.value?.focus())
}

async function searchPrimaryParties() {
  const q = primaryPartyQuery.value.trim()
  if (q.length < 2) {
    primaryParties.value = []
    return
  }
  try {
    // Search locally in cache across all ledgers
    const results = searchLedgersInCache(q)
    // Filter to only Suppliers
    primaryParties.value = results.filter(l => l.type === 'Supplier')
  } catch (e) {
    console.warn('[CustomerCreator] searchPrimaryParties failed:', e)
  }
}

function selectPrimaryParty(p) {
  form.value.primary_party = p.name
  form.value.primary_party_role = p.type
  primaryPartyQuery.value = p.name
  primaryParties.value = []
}

function handlePrimaryPartyEnter() {
  if (primaryParties.value.length === 1) {
    selectPrimaryParty(primaryParties.value[0])
  }
}

function handlePrimaryPartyKeydown(e) {
  if (e.key === 'Enter') {
    if (primaryParties.value.length > 0 && quickSearchRef.value) {
      quickSearchRef.value.handleKeydown(e)
    } else {
      e.preventDefault()
      handleFormEnter(e)
    }
  } else if (primaryParties.value.length > 0 && quickSearchRef.value) {
    quickSearchRef.value.handleKeydown(e)
  }
}

async function fetchGstInfo() {
  if (!form.value.gstin || form.value.gstin.length !== 15) return
  
  if (!confirm('This will use 0.5 API tokens. Proceed?')) return

  fetchingGst.value = true
  fetchedGstData.value = null
  try {
    const info = await validateGstin(form.value.gstin)
    if (info && info.business_name) {
      const addr = info.permanent_address || {}
      fetchedGstData.value = {
        business_name: info.business_name,
        address_line1: addr.address_line1 || '',
        address_line2: addr.address_line2 || '',
        city: addr.city || '',
        pincode: addr.pincode || '',
        state: addr.state || '',
      }
    }
  } catch (e) {
    console.error('[CustomerCreator] GST fetch failed:', e)
    alert('Failed to fetch GST details: ' + e.message)
  } finally {
    fetchingGst.value = false
  }
}

function applyGstData() {
  if (!fetchedGstData.value) return
  const d = fetchedGstData.value
  form.value.customer_name = d.business_name
  form.value.address_line1 = d.address_line1
  form.value.address_line2 = d.address_line2
  form.value.city = d.city
  form.value.pincode = d.pincode
  
  if (d.state) {
    const matchedState = indianStates.find(s => s.toLowerCase() === d.state.toLowerCase())
    if (matchedState) form.value.state = matchedState
  }
  
  fetchedGstData.value = null
}

function validate() {
  if (!form.value.customer_name.trim()) { alert('Customer Name is required'); return false }
  if (!props.isEdit && (!form.value.mobile || !/^\d{10}$/.test(form.value.mobile))) {
    alert('Valid 10-digit Mobile required'); return false
  }
  if (!form.value.address_line1 || !form.value.address_line1.trim()) {
    alert('Address Line 1 is required'); return false
  }
  return true
}

function handleFormEnter(e) {
  if (fetchedGstData.value) {
    applyGstData()
    return
  }
  const container = e.target.closest('.form-fields-container')
  if (!container) return
  const focusables = Array.from(container.querySelectorAll('input, select'))
  const idx = focusables.indexOf(e.target)
  if (idx > -1 && idx < focusables.length - 1) focusables[idx + 1].focus()
  else submit()
}

async function submit() {
  if (!validate()) return
  saving.value = true
  try {
    const result = props.isEdit
      ? await updateCustomer(form.value.name, form.value)
      : await createCustomer(form.value)
    emit('saved', result)
  } catch (e) {
    alert('Failed to save customer: ' + e.message)
  } finally {
    saving.value = false
  }
}

defineExpose({ focusFirst, submit })
</script>
