<template>
  <div
    v-if="show"
    class="w-[640px] rounded-xl bg-white shadow-2xl overflow-hidden"
    @keydown="handleKeydown"
  >
    <!-- Header -->
    <div class="border-b border-gray-200 px-5 py-4 bg-gray-50 flex items-start justify-between">
      <div>
        <div class="text-xl font-bold text-gray-700">
          {{ isEdit ? 'Edit Employee' : 'New Employee' }}
        </div>
        <div class="text-sm text-gray-600 flex items-center gap-2 mt-0.5">
          <template v-if="isEdit && loading">
            <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-400 border-t-transparent"></span>
            Loading from ERPNext…
          </template>
          <template v-else>
            {{ isEdit ? `Update information for ${form.employee_name}` : 'Enter employee details to create a new record' }}
          </template>
        </div>
      </div>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-xl leading-none mt-0.5">✕</button>
    </div>

    <!-- Form -->
    <div class="flex flex-col gap-4 px-6 py-5 max-h-[72vh] overflow-y-auto">

      <!-- First Name / Last Name -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">First Name *</label>
          <input
            ref="firstNameInput"
            v-model="form.first_name"
            class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="First name"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Last Name</label>
          <input
            ref="lastNameInput"
            v-model="form.last_name"
            class="rounded border border-gray-300 px-3 py-2 text-base font-semibold outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Last name"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
      </div>

      <!-- Gender / Date of Joining -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Gender *</label>
          <div class="flex rounded border border-gray-300 overflow-hidden">
            <button
              v-for="g in ['Male', 'Female']"
              :key="g"
              type="button"
              @click="form.gender = g"
              class="flex-1 py-2 text-sm font-bold transition-all"
              :class="form.gender === g ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'"
            >
              {{ g }}
            </button>
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Date of Joining *</label>
          <input
            ref="dojInput"
            v-model="form.date_of_joining"
            type="date"
            class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
      </div>

      <!-- Date of Birth -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Date of Birth</label>
        <input
          ref="dobInput"
          v-model="form.date_of_birth"
          type="date"
          class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500"
          @keydown.esc.stop="$emit('close')"
          @keydown.enter.prevent="focusNext"
        />
      </div>

      <!-- Mobile / Email -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Mobile Number</label>
          <input
            ref="mobileInput"
            v-model="form.mobile"
            class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500"
            placeholder="10-digit mobile"
            maxlength="10"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Email</label>
          <input
            ref="emailInput"
            v-model="form.email"
            type="email"
            class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500"
            placeholder="email@example.com"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
      </div>

      <!-- Current Address -->
      <div class="flex flex-col gap-1.5">
        <label class="text-[10px] font-bold uppercase tracking-wider text-gray-500">Current Address</label>
        <textarea
          ref="addressInput"
          v-model="form.current_address"
          rows="3"
          class="rounded border border-gray-300 px-3 py-2 text-base outline-none focus:border-blue-500 resize-none"
          placeholder="Street, Area, City, Pincode"
          @keydown.esc.stop="$emit('close')"
        ></textarea>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex justify-end gap-3 border-t border-gray-200 px-6 py-4 bg-gray-50">
      <button
        class="rounded border border-gray-300 bg-white px-5 py-2 font-semibold text-gray-600 transition-colors hover:bg-gray-50"
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
import { ref, reactive, watch, nextTick } from 'vue'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  show:        { type: Boolean, default: false },
  isEdit:      { type: Boolean, default: false },
  employeeRow: { type: Object,  default: null },
})

const emit = defineEmits(['close', 'saved'])

// ─── Form state ───────────────────────────────────────────────────────────────
const form = reactive({
  name:            '',
  first_name:      '',
  last_name:       '',
  employee_name:   '',
  gender:          'Male',
  date_of_joining: '',
  date_of_birth:   '',
  mobile:          '',
  email:           '',
  current_address: '',
})

const saving  = ref(false)
const loading = ref(false)

// ─── Field refs (tab order) ───────────────────────────────────────────────────
const firstNameInput = ref(null)
const lastNameInput  = ref(null)
const dojInput       = ref(null)
const dobInput       = ref(null)
const mobileInput    = ref(null)
const emailInput     = ref(null)
const addressInput   = ref(null)

const fieldOrder = [firstNameInput, lastNameInput, dojInput, dobInput, mobileInput, emailInput, addressInput]

// ─── Focus helpers ────────────────────────────────────────────────────────────
function focusFirst() {
  nextTick(() => firstNameInput.value?.focus())
}

function focusNext() {
  const current = document.activeElement
  const inputs = fieldOrder.map(r => r.value).filter(Boolean)
  const idx = inputs.indexOf(current)
  if (idx > -1 && idx < inputs.length - 1) inputs[idx + 1].focus()
  else submit()
}

function handleKeydown(e) {
  if (e.key === 'End') { e.preventDefault(); submit() }
}

// ─── Init / populate form ─────────────────────────────────────────────────────
function getTodayIST() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
}

function resetForm() {
  Object.assign(form, {
    name: '', first_name: '', last_name: '', employee_name: '',
    gender: 'Male', date_of_joining: getTodayIST(), date_of_birth: '',
    mobile: '', email: '', current_address: '',
  })
}

async function initForm() {
  if (!props.show) return
  resetForm()
  if (props.isEdit && props.employeeRow) {
    Object.assign(form, {
      name:          props.employeeRow.name,
      employee_name: props.employeeRow.label        || '',
      mobile:        props.employeeRow.mobile_no    || '',
      email:         props.employeeRow.email        || '',
    })
    loading.value = true
    try {
      const full = await frappeGet('ssplbilling.api.employee_api.get_employee_details', { employee: props.employeeRow.name })
      for (const [k, v] of Object.entries(full)) {
        if (v !== '') form[k] = v
      }
    } catch (e) {
      console.warn('[EmployeeCreator] fetch details failed:', e)
    } finally {
      loading.value = false
    }
  }
  focusFirst()
}

watch(() => props.show, initForm, { immediate: true })

// ─── Validation ───────────────────────────────────────────────────────────────
function validate() {
  if (!form.first_name.trim()) {
    alert('First Name is required')
    firstNameInput.value?.focus()
    return false
  }
  if (!form.date_of_joining) {
    alert('Date of Joining is required')
    dojInput.value?.focus()
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
    const payload = { ...form }
    const result = props.isEdit
      ? await frappePost('ssplbilling.api.employee_api.update_employee', { data: JSON.stringify(payload) })
      : await frappePost('ssplbilling.api.employee_api.create_employee', { data: JSON.stringify(payload) })
    emit('saved', result)
  } catch (e) {
    alert('Failed to save employee: ' + e.message)
  } finally {
    saving.value = false
  }
}

defineExpose({ focusFirst })
</script>
