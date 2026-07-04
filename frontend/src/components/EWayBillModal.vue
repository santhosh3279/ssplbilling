<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div class="flex flex-col bg-[var(--color-bg)] rounded-2xl border border-[var(--color-border)] shadow-2xl overflow-hidden w-[650px]">

      <!-- Header -->
      <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <span class="text-2xl font-bold uppercase tracking-tight text-[var(--color-text)]">Generate E-Way Bill</span>
        <button
          class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition"
          @click="emit('close')"
        >✕</button>
      </header>

      <!-- Fields (Scrollable if needed) -->
      <div class="flex flex-col gap-4 p-6 max-h-[70vh] overflow-y-auto custom-scrollbar">

        <!-- Row 1: Mode of Transport and Distance -->
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Mode of Transport</label>
            <select
              ref="transportModeRef"
              v-model="form.mode_of_transport"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusDistance"
              @keydown.esc.prevent="emit('close')"
            >
              <option value="Road">Road</option>
              <option value="Rail">Rail</option>
              <option value="Air">Air</option>
              <option value="Ship">Ship</option>
            </select>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Distance (km) <span class="text-[var(--color-danger)]">*</span></label>
            <input
              ref="distanceRef"
              v-model.number="form.distance"
              type="number"
              min="1"
              placeholder="e.g. 150"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusVehicleNo"
              @keydown.esc.prevent="emit('close')"
            />
          </div>
        </div>

        <!-- Row 2: Vehicle Number and Vehicle Type -->
        <div class="grid grid-cols-2 gap-4" v-if="form.mode_of_transport === 'Road'">
          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Vehicle Number <span class="text-[var(--color-danger)]">*</span></label>
            <input
              ref="vehicleNoRef"
              v-model="form.vehicle_no"
              type="text"
              placeholder="e.g. KL-09-AH-1234"
              class="uppercase rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusVehicleType"
              @keydown.esc.prevent="emit('close')"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Vehicle Type</label>
            <select
              ref="vehicleTypeRef"
              v-model="form.gst_vehicle_type"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusTransporterId"
              @keydown.esc.prevent="emit('close')"
            >
              <option value="Regular">Regular</option>
              <option value="Over Dimensional Cargo (ODC)">Over Dimensional Cargo (ODC)</option>
            </select>
          </div>
        </div>

        <!-- Row 3: Company as transporter toggle -->
        <label class="flex cursor-pointer items-center gap-3 rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 select-none transition-colors hover:border-[var(--color-highlight)]">
          <input
            type="checkbox"
            :checked="useCompanyTransporter"
            @change="toggleCompanyTransporter"
            class="h-5 w-5 accent-[var(--color-info)]"
          />
          <span class="text-lg font-bold uppercase text-[var(--color-text)]">
            Company as transporter
            <span class="block text-sm font-medium normal-case text-[var(--color-text-muted)]">Keeps the company's name and GSTIN in the transporter fields</span>
          </span>
        </label>

        <!-- Row 4: Transporter ID and Transporter Name -->
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Transporter ID / GSTIN</label>
            <input
              ref="transporterIdRef"
              v-model="form.gst_transporter_id"
              type="text"
              placeholder="15-digit GSTIN"
              :disabled="useCompanyTransporter"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors disabled:opacity-60 disabled:bg-[var(--color-surface)]"
              @keydown.enter.prevent="focusTransporterName"
              @keydown.esc.prevent="emit('close')"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">Transporter Name</label>
            <input
              ref="transporterNameRef"
              v-model="form.transporter_name"
              type="text"
              placeholder="Name of Transporter"
              :disabled="useCompanyTransporter"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors disabled:opacity-60 disabled:bg-[var(--color-surface)]"
              @keydown.enter.prevent="focusLrNo"
              @keydown.esc.prevent="emit('close')"
            />
          </div>
        </div>

        <!-- Row 5: LR / Transport Doc No and Date -->
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">LR / Doc Number</label>
            <input
              ref="lrNoRef"
              v-model="form.lr_no"
              type="text"
              placeholder="e.g. LR-98765"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusLrDate"
              @keydown.esc.prevent="emit('close')"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-lg font-bold uppercase text-[var(--color-text-muted)]">LR / Doc Date</label>
            <input
              ref="lrDateRef"
              v-model="form.lr_date"
              type="date"
              class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-3xl text-[var(--color-text)] outline-none focus:border-[var(--color-highlight)] transition-colors"
              @keydown.enter.prevent="focusSubmit"
              @keydown.esc.prevent="emit('close')"
            />
          </div>
        </div>

      </div>

      <!-- Footer -->
      <footer class="flex justify-end gap-4 border-t border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-4">
        <button
          @click="emit('close')"
          class="rounded-xl border-2 border-[var(--color-border)] bg-[var(--color-bg)] px-8 py-3 text-2xl font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] transition"
        >Cancel</button>
        <button
          ref="submitBtnRef"
          @click="handleSubmit"
          :disabled="loading"
          class="rounded-xl px-10 py-3 text-2xl font-bold text-white transition-all active:scale-95 disabled:opacity-50"
          :class="loading ? 'bg-slate-500' : 'bg-[var(--color-info)] hover:brightness-110'"
        >
          {{ loading ? 'Generating...' : 'Generate' }}
        </button>
      </footer>

    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { frappeGet } from '../api'

const props = defineProps({
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'submit'])

const form = ref({
  mode_of_transport: 'Road',
  distance: '',
  vehicle_no: '',
  gst_vehicle_type: 'Regular',
  gst_transporter_id: '',
  transporter_name: '',
  lr_no: '',
  lr_date: new Date().toISOString().split('T')[0]
})

// Input Element Refs
const transportModeRef = ref(null)
const distanceRef = ref(null)
const vehicleNoRef = ref(null)
const vehicleTypeRef = ref(null)
const transporterIdRef = ref(null)
const transporterNameRef = ref(null)
const lrNoRef = ref(null)
const lrDateRef = ref(null)
const submitBtnRef = ref(null)

// "Company as transporter": keep the company's own name + GSTIN in the
// transporter fields (own-vehicle dispatch). Persisted across sessions.
const useCompanyTransporter = ref(localStorage.getItem('wb-company-as-transporter') === '1')
let companyDetails = null

async function applyCompanyTransporter() {
  try {
    if (!companyDetails) {
      companyDetails = await frappeGet('ssplbilling.api.quotation_api.get_company_transporter_details')
    }
    form.value.gst_transporter_id = companyDetails.gstin || ''
    form.value.transporter_name = companyDetails.company || ''
  } catch (e) {
    console.error('[EWayBillModal] Failed to fetch company transporter details:', e)
    alert('Could not fetch company name / GSTIN.')
    useCompanyTransporter.value = false
    localStorage.setItem('wb-company-as-transporter', '0')
  }
}

function toggleCompanyTransporter() {
  useCompanyTransporter.value = !useCompanyTransporter.value
  localStorage.setItem('wb-company-as-transporter', useCompanyTransporter.value ? '1' : '0')
  if (useCompanyTransporter.value) {
    applyCompanyTransporter()
  } else {
    form.value.gst_transporter_id = ''
    form.value.transporter_name = ''
  }
}

onMounted(() => {
  if (useCompanyTransporter.value) applyCompanyTransporter()
  nextTick(() => {
    distanceRef.value?.focus()
  })
})

function focusDistance() { nextTick(() => distanceRef.value?.focus() ) }
function focusVehicleNo() {
  if (form.value.mode_of_transport === 'Road') {
    nextTick(() => vehicleNoRef.value?.focus() )
  } else {
    focusTransporterId()
  }
}
function focusVehicleType() { nextTick(() => vehicleTypeRef.value?.focus() ) }
function focusTransporterId() {
  if (useCompanyTransporter.value) {
    focusLrNo()
  } else {
    nextTick(() => transporterIdRef.value?.focus() )
  }
}
function focusTransporterName() {
  if (useCompanyTransporter.value) {
    focusLrNo()
  } else {
    nextTick(() => transporterNameRef.value?.focus() )
  }
}
function focusLrNo() { nextTick(() => lrNoRef.value?.focus() ) }
function focusLrDate() { nextTick(() => lrDateRef.value?.focus() ) }
function focusSubmit() { nextTick(() => submitBtnRef.value?.focus() ) }

watch(
  () => form.value.vehicle_no,
  (newVal) => {
    if (newVal && newVal !== newVal.toUpperCase()) {
      form.value.vehicle_no = newVal.toUpperCase()
    }
  }
)

function handleSubmit() {
  if (!form.value.distance) {
    alert('Distance (km) is required.')
    focusDistance()
    return
  }
  if (form.value.mode_of_transport === 'Road' && !form.value.vehicle_no) {
    alert('Vehicle Number is required for transport by Road.')
    focusVehicleNo()
    return
  }
  if (form.value.vehicle_no) {
    form.value.vehicle_no = form.value.vehicle_no.toUpperCase().trim()
  }
  emit('submit', form.value)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 3px;
}
</style>
