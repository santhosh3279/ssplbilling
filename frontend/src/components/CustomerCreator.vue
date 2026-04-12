<template>
  <div class="w-[600px] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
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

    <div class="flex flex-col gap-4 px-6 py-5 max-h-[70vh] overflow-y-auto">
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

      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile Number *</label>
          <input v-model="form.mobile" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="10-digit mobile" maxlength="10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">WhatsApp Number</label>
          <input v-model="form.whatsapp" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="10-digit whatsapp" maxlength="10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Email</label>
          <input v-model="form.email" type="email" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="email@example.com" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">GSTIN</label>
          <input v-model="form.gstin" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 font-mono text-base uppercase text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="22AAAAA0000A1Z5" maxlength="15" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Pricelist Modifier %</label>
        <div class="relative w-full">
          <input v-model.number="form.pricelist_modifier" type="number" step="0.1" class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)] pr-8" placeholder="e.g. 10 or -10" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
          <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] font-bold">%</span>
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 1</label>
        <input v-model="form.address_line1" class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] outline-none focus:border-[var(--color-info)]" placeholder="Street / Building" @keydown.esc.stop="$emit('close')" @keydown.enter.prevent="handleFormEnter" />
      </div>

      <div class="grid grid-cols-3 gap-4">
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

const props = defineProps({
  show: Boolean,
  isEdit: { type: Boolean, default: false },
  customerRow: { type: Object, default: null },
  initialName: { type: String, default: '' },
})

const emit = defineEmits(['close', 'saved'])

const nameInputRef = ref(null)
const saving = ref(false)
const editLoading = ref(false)
const customerGroups = ref([])

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
    }
    editLoading.value = true
    try {
      const full = await fetchCustomerDetails(row.name)
      const merged = { ...form.value }
      for (const [k, v] of Object.entries(full)) {
        if (k === 'address_name' || v !== '') merged[k] = v
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
  nextTick(() => nameInputRef.value?.focus())
}

function validate() {
  if (!form.value.customer_name.trim()) { alert('Customer Name is required'); return false }
  if (!props.isEdit && (!form.value.mobile || !/^\d{10}$/.test(form.value.mobile))) {
    alert('Valid 10-digit Mobile required'); return false
  }
  return true
}

function handleFormEnter(e) {
  const container = e.target.closest('.flex-col.gap-4')
  if (!container) return
  const focusables = Array.from(container.querySelectorAll('input, select, button'))
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
