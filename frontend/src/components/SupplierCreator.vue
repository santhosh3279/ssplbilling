<template>
  <div
    v-if="show"
    class="w-[640px] rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden"
    @keydown="handleKeydown"
  >
    <!-- Header -->
    <div class="border-b border-slate-700 px-5 py-4 bg-slate-800 flex items-start justify-between">
      <div>
        <div class="text-xl font-bold text-slate-200">
          {{ isEdit ? 'Edit Supplier' : 'New Supplier' }}
        </div>
        <div class="text-sm text-slate-400 flex items-center gap-2 mt-0.5">
          <template v-if="isEdit && loading">
            <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-400 border-t-transparent"></span>
            Loading from ERPNext…
          </template>
          <template v-else>
            {{ isEdit ? `Update information for ${form.supplier_name}` : 'Enter supplier details to create a new record' }}
          </template>
        </div>
      </div>
      <button @click="$emit('close')" class="text-slate-500 hover:text-slate-300 text-xl leading-none mt-0.5">✕</button>
    </div>

    <!-- Form -->
    <div class="flex flex-col gap-4 px-6 py-5 max-h-[72vh] overflow-y-auto">

      <!-- Supplier Type / Supplier Group -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Supplier Type *</label>
          <select
            ref="typeInput"
            v-model="form.supplier_type"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base font-semibold text-slate-200 outline-none focus:border-blue-500"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="Company">Company</option>
            <option value="Individual">Individual</option>
            <option value="Partnership">Partnership</option>
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Supplier Group *</label>
          <select
            ref="groupInput"
            v-model="form.supplier_group"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="">— Select Group —</option>
            <option v-for="g in supplierGroups" :key="g.name" :value="g.name">{{ g.name }}</option>
          </select>
        </div>
      </div>

      <!-- Supplier Name -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Supplier Name *</label>
        <input
          ref="nameInput"
          v-model="form.supplier_name"
          class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base font-semibold text-slate-200 outline-none focus:border-blue-500"
          placeholder="Full name"
          @keydown.esc.stop="$emit('close')"
          @keydown.enter.prevent="focusNext"
        />
      </div>

      <!-- GSTIN + GST Category badge -->
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">GSTIN</label>
          <span
            class="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
            :class="gstCategory === 'Registered Regular'
              ? 'bg-green-900/30 text-green-400'
              : 'bg-slate-700 text-slate-500'"
          >
            {{ gstCategory }}
          </span>
        </div>
        <input
          ref="gstinInput"
          v-model="form.gstin"
          class="rounded border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-base uppercase text-slate-200 outline-none focus:border-blue-500"
          placeholder="22AAAAA0000A1Z5"
          maxlength="15"
          @keydown.esc.stop="$emit('close')"
          @keydown.enter.prevent="focusNext"
        />
      </div>

      <!-- Mobile / WhatsApp / Email -->
      <div class="grid grid-cols-3 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Mobile Number</label>
          <input
            ref="mobileInput"
            v-model="form.mobile"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            placeholder="10-digit mobile"
            maxlength="10"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">WhatsApp</label>
          <input
            ref="whatsappInput"
            v-model="form.whatsapp"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            placeholder="10-digit whatsapp"
            maxlength="10"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Email</label>
          <input
            ref="emailInput"
            v-model="form.email"
            type="email"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            placeholder="email@example.com"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
      </div>

      <!-- Address Line 1 -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Address Line 1</label>
        <input
          ref="addr1Input"
          v-model="form.address_line1"
          class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
          placeholder="Street / Building"
          @keydown.esc.stop="$emit('close')"
          @keydown.enter.prevent="focusNext"
        />
      </div>

      <!-- Address Line 2 -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Address Line 2</label>
        <input
          ref="addr2Input"
          v-model="form.address_line2"
          class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
          placeholder="Area / Landmark (optional)"
          @keydown.esc.stop="$emit('close')"
          @keydown.enter.prevent="focusNext"
        />
      </div>

      <!-- City / Pincode / State -->
      <div class="grid grid-cols-3 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">City</label>
          <input
            ref="cityInput"
            v-model="form.city"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            placeholder="City"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Pincode</label>
          <input
            ref="pincodeInput"
            v-model="form.pincode"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            placeholder="678XXX"
            maxlength="6"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-slate-500">State</label>
          <select
            ref="stateInput"
            v-model="form.state"
            class="rounded border border-slate-600 bg-slate-800 px-3 py-2 text-base text-slate-200 outline-none focus:border-blue-500"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="">Select State</option>
            <option v-for="s in indianStates" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex justify-end gap-3 border-t border-slate-700 px-6 py-4 bg-slate-800">
      <button
        class="rounded border border-slate-600 bg-slate-700 px-5 py-2 font-semibold text-slate-300 transition-colors hover:bg-slate-600"
        @click="$emit('close')"
      >
        Cancel
      </button>
      <button
        class="rounded px-6 py-2 font-bold text-white shadow-md flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50"
        :class="isEdit ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'"
        :disabled="saving || loading"
        @click="submit"
      >
        {{ saving ? (isEdit ? 'Updating...' : 'Saving...') : (isEdit ? 'Update Details' : 'Save & Select') }}
        <kbd
          class="rounded border px-1.5 py-0.5 font-mono text-xs shadow-sm"
          :class="isEdit ? 'border-orange-500 bg-orange-500' : 'border-blue-500 bg-blue-500'"
        >End</kbd>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { createSupplier, fetchSupplierDetails, updateSupplier } from '../api/supplier.js'
import { frappeGet } from '../api.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  isEdit: { type: Boolean, default: false },
  supplierRow: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

// ─── Supplier Groups (fetched once) ───────────────────────────────────────────
const supplierGroups = ref([])

onMounted(async () => {
  try {
    supplierGroups.value = await frappeGet('ssplbilling.api.supplier_creator_api.get_supplier_groups')
    // Re-run init so supplier_group default/fetched value is applied after groups load
    await initForm()
  } catch (e) {
    console.warn('[SupplierCreator] failed to load supplier groups:', e)
  }
})

// ─── Form state ───────────────────────────────────────────────────────────────
const form = reactive({
  name: '',
  supplier_type: 'Individual',
  supplier_group: '',
  supplier_name: '',
  mobile: '',
  whatsapp: '',
  email: '',
  gstin: '',
  address_name: '',
  address_line1: '',
  address_line2: '',
  city: 'Palakkad',
  pincode: '678000',
  state: 'Kerala',
})

const saving = ref(false)
const loading = ref(false)

// GST category derived live from GSTIN input
const gstCategory = computed(() =>
  form.gstin.trim() ? 'Registered Regular' : 'Unregistered'
)

// ─── Field refs (in tab order) ────────────────────────────────────────────────
const typeInput      = ref(null)
const groupInput     = ref(null)
const nameInput      = ref(null)
const gstinInput     = ref(null)
const mobileInput    = ref(null)
const whatsappInput  = ref(null)
const emailInput     = ref(null)
const addr1Input     = ref(null)
const addr2Input     = ref(null)
const cityInput      = ref(null)
const pincodeInput   = ref(null)
const stateInput     = ref(null)

const fieldOrder = [typeInput, groupInput, nameInput, gstinInput, mobileInput, whatsappInput, emailInput, addr1Input, addr2Input, cityInput, pincodeInput, stateInput]

// ─── Focus helpers ────────────────────────────────────────────────────────────
function focusFirst() {
  nextTick(() => typeInput.value?.focus())
}

function focusNext() {
  const current = document.activeElement
  const inputs = fieldOrder.map(r => r.value).filter(Boolean)
  const idx = inputs.indexOf(current)
  if (idx > -1 && idx < inputs.length - 1) {
    inputs[idx + 1].focus()
  } else {
    submit()
  }
}

function handleKeydown(e) {
  if (e.key === 'End') {
    e.preventDefault()
    submit()
  }
}

// ─── Watch: populate form when shown ─────────────────────────────────────────
async function initForm() {
  if (!props.show) return
  resetForm()
  if (props.isEdit && props.supplierRow) {
    Object.assign(form, {
      name:          props.supplierRow.name,
      supplier_name: props.supplierRow.label        || '',
      mobile:        props.supplierRow.mobile_no    || '',
      whatsapp:      props.supplierRow.whatsapp     || '',
      email:         props.supplierRow.email        || '',
      gstin:         props.supplierRow.gstin        || '',
      address_line1: props.supplierRow.address_line1 || '',
      city:          props.supplierRow.city         || 'Palakkad',
      pincode:       props.supplierRow.pincode      || '678000',
      state:         props.supplierRow.state        || 'Kerala',
    })
    loading.value = true
    try {
      const full = await fetchSupplierDetails(props.supplierRow.name)
      // Merge: only overwrite with non-empty values from API so ledger prefill isn't blanked
      for (const [k, v] of Object.entries(full)) {
        if (k === 'address_name' || v !== '') form[k] = v
      }
    } catch (e) {
      console.warn('[SupplierCreator] fetch details failed:', e)
    } finally {
      loading.value = false
    }
  }
  focusFirst()
}

watch(() => props.show, initForm, { immediate: true })

// ─── Helpers ──────────────────────────────────────────────────────────────────
function resetForm() {
  Object.assign(form, {
    name: '',
    supplier_type: 'Individual',
    supplier_group: supplierGroups.value[0]?.name || '',
    supplier_name: '',
    mobile: '', whatsapp: '', email: '', gstin: '',
    address_name: '', address_line1: '', address_line2: '',
    city: 'Palakkad', pincode: '678000', state: 'Kerala',
  })
}

function validate() {
  if (!form.supplier_name.trim()) {
    alert('Supplier Name is required')
    nameInput.value?.focus()
    return false
  }
  if (!form.supplier_group) {
    alert('Supplier Group is required')
    groupInput.value?.focus()
    return false
  }
  return true
}

// ─── Submit ───────────────────────────────────────────────────────────────────
async function submit() {
  if (saving.value || loading.value) return
  if (!validate()) return

  saving.value = true
  try {
    const result = props.isEdit
      ? await updateSupplier(form.name, { ...form })
      : await createSupplier({ ...form })
    emit('saved', result)
  } catch (e) {
    alert('Failed to save supplier: ' + e.message)
  } finally {
    saving.value = false
  }
}

defineExpose({ focusFirst })

// ─── Indian States ────────────────────────────────────────────────────────────
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
</script>
