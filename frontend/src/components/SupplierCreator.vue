<template>
  <div
    v-if="show"
    class="w-[90vw] rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
    @keydown="handleKeydown"
  >
    <!-- Header -->
    <div class="border-b border-[var(--color-border)] px-5 py-4 bg-[var(--color-surface)] flex items-start justify-between">
      <div>
        <div class="text-xl font-bold text-[var(--color-text)]">
          {{ isEdit ? 'Edit Supplier' : 'New Supplier' }}
        </div>
        <div class="text-sm text-[var(--color-text-muted)] flex items-center gap-2 mt-0.5">
          <template v-if="isEdit && loading">
            <span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent"></span>
            Loading from ERPNext…
          </template>
          <template v-else>
            {{ isEdit ? `Update information for ${form.supplier_name}` : 'Enter supplier details to create a new record' }}
          </template>
        </div>
      </div>
      <button @click="$emit('close')" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-xl leading-none mt-0.5">✕</button>
    </div>

    <!-- Form -->
    <div class="grid grid-cols-3 gap-6 px-6 py-5 max-h-[72vh] overflow-y-auto align-stretch form-fields-container">
      <!-- Column 1: Identity & Grouping -->
      <div class="flex flex-col gap-4">
        <!-- GSTIN + GST Category badge -->
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex justify-between items-center w-full">
                <span>GSTIN</span>
                <button 
                  v-if="form.gstin && form.gstin.length === 15"
                  @click="fetchGstInfo"
                  class="text-[18px] bg-[var(--color-info)] text-white px-4 py-1 rounded hover:opacity-80 transition-opacity flex items-center gap-2 shadow-sm"
                  :disabled="fetchingGst"
                  title="Fetch Details from GST"
                >
                  <span v-if="fetchingGst" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                  <span>{{ fetchingGst ? 'Fetching...' : 'GST Fetch' }}</span>
                </button>
              </label>
            </div>
            <span
              class="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
              :class="gstCategory === 'Registered Regular'
                ? 'bg-[var(--color-success)]/30 text-[var(--color-success)]'
                : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]'"
            >
              {{ gstCategory }}
            </span>
          </div>
          <input
            ref="gstinInput"
            v-model="form.gstin"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] font-mono uppercase text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="22AAAAA0000A1Z5"
            maxlength="15"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
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
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Supplier Type *</label>
          <select
            ref="typeInput"
            v-model="form.supplier_type"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="Company">Company</option>
            <option value="Individual">Individual</option>
            <option value="Partnership">Partnership</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Supplier Group *</label>
          <select
            ref="groupInput"
            v-model="form.supplier_group"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="">— Select Group —</option>
            <option v-for="g in supplierGroups" :key="g.name" :value="g.name">{{ g.name }}</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Supplier Name *</label>
          <input
            ref="nameInput"
            v-model="form.supplier_name"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="Full name"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Supplier Print Name</label>
          <input
            ref="printNameInput"
            v-model="form.supplier_print_name"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] font-semibold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="Name as it appears on print"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <!-- Primary Party (Party Link) -->
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Primary Party (Link)</label>
          <div class="relative">
            <input
              ref="primaryPartyInputRef"
              v-model="primaryPartyQuery"
              class="w-full rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
              style="font-size: 1.5rem; padding: 0.2em;"
              placeholder="Search Customer..."
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

        <div class="flex items-center gap-2 mt-2">
          <input
            id="supplier_disabled"
            v-model="form.disabled"
            type="checkbox"
            class="h-5 w-5 rounded border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-info)] focus:ring-[var(--color-info)]"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
          <label for="supplier_disabled" class="text-base font-semibold uppercase tracking-wider text-[var(--color-text)] cursor-pointer">Disabled</label>
        </div>
      </div>

      <!-- Column 2: Contact & Tax -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Mobile Number</label>
          <input
            ref="mobileInput"
            v-model="form.mobile"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="10-digit mobile"
            maxlength="10"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">WhatsApp</label>
          <input
            ref="whatsappInput"
            v-model="form.whatsapp"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="10-digit whatsapp"
            maxlength="10"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Email</label>
          <input
            ref="emailInput"
            v-model="form.email"
            type="email"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="email@example.com"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>
      </div>

      <!-- Column 3: Address & Location -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 1 *</label>
          <input
            ref="addr1Input"
            v-model="form.address_line1"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="Street / Building"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Address Line 2</label>
          <input
            ref="addr2Input"
            v-model="form.address_line2"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="Area / Landmark (optional)"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">City</label>
          <input
            ref="cityInput"
            v-model="form.city"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="City"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Pincode</label>
          <input
            ref="pincodeInput"
            v-model="form.pincode"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            placeholder="678XXX"
            maxlength="6"
            @keydown.esc.stop="$emit('close')"
            @keydown.enter.prevent="focusNext"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-[15px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">State</label>
          <select
            ref="stateInput"
            v-model="form.state"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
            style="font-size: 1.5rem; padding: 0.2em;"
            @keydown.esc.stop="$emit('close')"
          >
            <option value="">Select State</option>
            <option v-for="s in indianStates" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex justify-end gap-3 border-t border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
      <button
        class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-5 py-2 font-semibold text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-raised)]"
        @click="$emit('close')"
      >
        Cancel
      </button>
      <button
        class="rounded px-6 py-2 font-bold text-[var(--color-text-on-highlight)] shadow-md flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        :class="isEdit ? 'bg-[var(--color-supplier)] hover:bg-[var(--color-supplier)]' : 'bg-[var(--color-info)] hover:bg-[var(--color-info)]'"
        :disabled="saving || loading || !canSubmit"
        @click="submit"
      >
        {{ saving ? (isEdit ? 'Updating...' : 'Saving...') : (isEdit ? 'Update Details' : 'Save & Select') }}
        <kbd
          class="rounded border px-1.5 py-0.5 font-mono text-xs shadow-sm"
          :class="isEdit ? 'border-[var(--color-supplier)] bg-[var(--color-supplier)]' : 'border-[var(--color-info)] bg-[var(--color-info)]'"
        >End</kbd>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { createSupplier, fetchSupplierDetails, updateSupplier } from '../api/supplier.js'
import { frappeGet, validateGstin } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'
import { useLedgerCache, searchLedgersInCache } from '../services/ledgerCache'
import QuickLedgerSearch from './QuickLedgerSearch.vue'

useSubwindow()

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
  supplier_print_name: '',
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
  primary_party: '',
  primary_party_role: '',
  disabled: 0,
})

const saving = ref(false)
const loading = ref(false)
const fetchingGst = ref(false)
const fetchedGstData = ref(null)

// GST category derived live from GSTIN input
const gstCategory = computed(() =>
  form.gstin.trim() ? 'Registered Regular' : 'Unregistered'
)

// ─── Field refs (in tab order) ────────────────────────────────────────────────
const typeInput            = ref(null)
const groupInput           = ref(null)
const nameInput            = ref(null)
const printNameInput       = ref(null)
const primaryPartyInputRef = ref(null)
const quickSearchRef       = ref(null)
const mobileInput          = ref(null)
const whatsappInput        = ref(null)
const emailInput           = ref(null)
const gstinInput           = ref(null)
const addr1Input           = ref(null)
const addr2Input           = ref(null)
const cityInput            = ref(null)
const pincodeInput         = ref(null)
const stateInput           = ref(null)

const primaryPartyQuery = ref('')
const primaryParties = ref([])

const fieldOrder = [
  gstinInput,
  typeInput,
  groupInput,
  nameInput,
  printNameInput,
  primaryPartyInputRef,
  mobileInput,
  whatsappInput,
  emailInput,
  addr1Input,
  addr2Input,
  cityInput,
  pincodeInput,
  stateInput
]

// ─── Focus helpers ────────────────────────────────────────────────────────────
function focusFirst() {
  nextTick(() => gstinInput.value?.focus())
}

async function searchPrimaryParties() {
  const q = primaryPartyQuery.value.trim()
  if (q.length < 2) {
    primaryParties.value = []
    return
  }
  try {
    const results = searchLedgersInCache(q)
    // Filter to only Customers
    primaryParties.value = results.filter(l => l.type === 'Customer')
  } catch (e) {
    console.warn('[SupplierCreator] searchPrimaryParties failed:', e)
  }
}

function selectPrimaryParty(p) {
  form.primary_party = p.name
  form.primary_party_role = p.type
  primaryPartyQuery.value = p.name
  primaryParties.value = []
}

function handlePrimaryPartyKeydown(e) {
  if (e.key === 'Enter') {
    if (primaryParties.value.length > 0 && quickSearchRef.value) {
      quickSearchRef.value.handleKeydown(e)
    } else {
      e.preventDefault()
      focusNext()
    }
  } else if (primaryParties.value.length > 0 && quickSearchRef.value) {
    quickSearchRef.value.handleKeydown(e)
  }
}

async function fetchGstInfo() {
  if (!form.gstin || form.gstin.length !== 15) return
  
  if (!confirm('This will use 0.5 API tokens. Proceed?')) return

  fetchingGst.value = true
  fetchedGstData.value = null
  try {
    const info = await validateGstin(form.gstin)
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
    console.error('[SupplierCreator] GST fetch failed:', e)
    alert('Failed to fetch GST details: ' + e.message)
  } finally {
    fetchingGst.value = false
  }
}

function applyGstData() {
  if (!fetchedGstData.value) return
  const d = fetchedGstData.value
  form.supplier_name = d.business_name
  form.supplier_print_name = d.business_name
  form.address_line1 = d.address_line1
  form.address_line2 = d.address_line2
  form.city = d.city
  form.pincode = d.pincode
  
  if (d.state) {
    const matchedState = indianStates.find(s => s.toLowerCase() === d.state.toLowerCase())
    if (matchedState) form.state = matchedState
  }
  
  fetchedGstData.value = null
}

// Custom Enter key traversal that relies on fieldOrder
function focusNext() {
  if (fetchedGstData.value) {
    applyGstData()
    return
  }
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
      supplier_name: props.supplierRow.supplier_name || props.supplierRow.label || '',
      supplier_print_name: props.supplierRow.supplier_print_name || '',
      mobile:        props.supplierRow.mobile_no    || '',
      whatsapp:      props.supplierRow.whatsapp     || '',
      email:         props.supplierRow.email        || '',
      gstin:         props.supplierRow.gstin        || '',
      address_line1: props.supplierRow.address_line1 || '',
      city:          props.supplierRow.city         || 'Palakkad',
      pincode:       props.supplierRow.pincode      || '678000',
      state:         props.supplierRow.state        || 'Kerala',
      primary_party: '',
      primary_party_role: '',
      disabled:      props.supplierRow.disabled     || 0,
    })
    loading.value = true
    try {
      const full = await fetchSupplierDetails(props.supplierRow.name)
      // Merge: only overwrite with non-empty values from API so ledger prefill isn't blanked
      for (const [k, v] of Object.entries(full)) {
        if (k === 'address_name' || v !== '') form[k] = v
      }
      if (form.primary_party) {
        primaryPartyQuery.value = form.primary_party
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
  fetchedGstData.value = null
  primaryPartyQuery.value = ''
  primaryParties.value = []
  Object.assign(form, {
    name: '',
    supplier_type: 'Individual',
    supplier_group: supplierGroups.value[0]?.name || '',
    supplier_name: '',
    supplier_print_name: '',
    mobile: '', whatsapp: '', email: '', gstin: '',
    address_name: '', address_line1: '', address_line2: '',
    city: 'Palakkad', pincode: '678000', state: 'Kerala',
    primary_party: '',
    primary_party_role: '',
    disabled: 0,
  })
}

const canSubmit = computed(() => {
  if (!form.supplier_name || !form.supplier_name.trim()) return false
  if (!form.supplier_group) return false
  if (!form.address_line1 || !form.address_line1.trim()) return false
  return true
})

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
  if (!form.address_line1 || !form.address_line1.trim()) {
    alert('Address Line 1 is required')
    addr1Input.value?.focus()
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
