<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    @click.self="$emit('close')"
  >
    <div class="w-[400px] overflow-hidden rounded-2xl shadow-2xl" style="background:#ffffff;color:#1e293b">

      <!-- Header -->
      <div class="flex items-center justify-between border-b px-6 py-4" style="border-color:#f1f5f9">
        <div>
          <div class="text-[10px] uppercase tracking-widest font-bold" style="color:#94a3b8">Bill Saved</div>
          <div class="font-mono text-xl font-bold" style="color:#16a34a">{{ invoiceName }}</div>
        </div>
        <button
          @click="$emit('close')"
          class="rounded-lg px-3 py-1.5 text-xs transition-colors border"
          style="background:#f8fafc;color:#64748b;border-color:#e2e8f0"
          @mouseenter="e => { e.currentTarget.style.background='#f1f5f9'; e.currentTarget.style.color='#1e293b' }"
          @mouseleave="e => { e.currentTarget.style.background='#f8fafc'; e.currentTarget.style.color='#64748b' }"
        >
          ✕ Close
        </button>
      </div>

      <!-- ── Main choice ── -->
      <div v-if="!showThermal" class="flex flex-col gap-3 p-6">
        <button
          @click="openThermal"
          class="flex items-center gap-4 rounded-xl px-5 py-4 text-left outline-none transition-all group border shadow-sm"
          style="background:#ffffff;border-color:#e2e8f0"
          @mouseenter="e => { e.currentTarget.style.background='#f1f5f9'; e.currentTarget.style.borderColor='#3b82f6' }"
          @mouseleave="e => { e.currentTarget.style.background='#ffffff'; e.currentTarget.style.borderColor='#e2e8f0' }"
        >
          <span class="text-3xl leading-none">🖨</span>
          <div class="flex-1">
            <div class="font-bold flex items-center justify-between" style="color:#0f172a">
              Thermal Print
              <kbd class="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-[10px] text-gray-400 group-hover:text-blue-600 transition-colors">1</kbd>
            </div>
            <div class="text-xs font-medium" style="color:#64748b">Send receipt to thermal printer via CUPS</div>
          </div>
        </button>

        <button
          @click="openPreview"
          class="flex items-center gap-4 rounded-xl px-5 py-4 text-left outline-none transition-all group border shadow-sm"
          style="background:#ffffff;border-color:#e2e8f0"
          @mouseenter="e => { e.currentTarget.style.background='#f1f5f9'; e.currentTarget.style.borderColor='#3b82f6' }"
          @mouseleave="e => { e.currentTarget.style.background='#ffffff'; e.currentTarget.style.borderColor='#e2e8f0' }"
        >
          <span class="text-3xl leading-none">📄</span>
          <div class="flex-1">
            <div class="font-bold flex items-center justify-between" style="color:#0f172a">
              Print Preview
              <kbd class="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-[10px] text-gray-400 group-hover:text-blue-600 transition-colors">2</kbd>
            </div>
            <div class="text-xs font-medium" style="color:#64748b">Open formatted invoice in browser</div>
          </div>
        </button>
      </div>

      <!-- ── Thermal options ── -->
      <div v-else class="flex flex-col gap-4 p-6">
        <button
          @click="showThermal = false"
          class="self-start text-xs transition-colors flex items-center gap-2 font-bold"
          style="color:#64748b"
          @mouseenter="e => e.currentTarget.style.color='#1e293b'"
          @mouseleave="e => e.currentTarget.style.color='#64748b'"
        >
          <span>← Back</span>
          <kbd class="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-[10px] text-gray-400">Bksp</kbd>
        </button>

        <div v-if="loading" class="py-6 text-center text-xs font-medium" style="color:#94a3b8">
          Loading printers &amp; templates…
        </div>

        <template v-else>
          <!-- No printers -->
          <div v-if="!printers.length" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#fef2f2;color:#ef4444;border-color:#fee2e2">
            No printers configured. Add a Printer in Printer Server Configuration.
          </div>

          <!-- No templates -->
          <div v-else-if="!templates.length" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#fef2f2;color:#ef4444;border-color:#fee2e2">
            No Print Template found for <strong>{{ doctype }}</strong>. Create one first.
          </div>

          <template v-else>
            <!-- Printer -->
            <div>
              <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold" style="color:#94a3b8">Printer</label>
              <select
                v-model="selectedPrinter"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all shadow-sm"
                style="background:#f8fafc;border-color:#e2e8f0;color:#1e293b"
                @focus="e => { e.target.style.borderColor='#3b82f6'; e.target.style.ring='2px'; e.target.style.background='#ffffff' }"
                @blur="e => { e.target.style.borderColor='#e2e8f0'; e.target.style.background='#f8fafc' }"
              >
                <option v-for="p in printers" :key="p.name" :value="p.name">
                  {{ p.printer_name }} — {{ p.status }}
                </option>
              </select>
            </div>

            <!-- Template -->
            <div>
              <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold" style="color:#94a3b8">Template</label>
              <select
                v-model="selectedTemplate"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all shadow-sm"
                style="background:#f8fafc;border-color:#e2e8f0;color:#1e293b"
                @focus="e => { e.target.style.borderColor='#3b82f6'; e.target.style.ring='2px'; e.target.style.background='#ffffff' }"
                @blur="e => { e.target.style.borderColor='#e2e8f0'; e.target.style.background='#f8fafc' }"
              >
                <option v-for="t in templates" :key="t.name" :value="t.name">{{ t.name }}</option>
              </select>
            </div>

            <!-- Error / success -->
            <div v-if="error" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#fef2f2;color:#ef4444;border-color:#fee2e2">{{ error }}</div>
            <div v-if="success" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#f0fdf4;color:#16a34a;border-color:#dcfce7">{{ success }}</div>

            <!-- Print button -->
            <button
              @click="sendPrint"
              :disabled="printing"
              class="w-full rounded-xl py-3 text-sm font-bold tracking-wider transition-all flex items-center justify-center gap-3 shadow-md"
              :style="!printing
                ? 'background:#2563eb;color:#fff;cursor:pointer'
                : 'background:#f1f5f9;color:#94a3b8;cursor:not-allowed'"
            >
              {{ printing ? 'Sending to printer…' : 'Print Now' }}
              <kbd v-if="!printing" class="rounded border border-blue-400 bg-blue-500 px-1.5 py-0.5 font-mono text-[10px] text-white">End</kbd>
            </button>
          </template>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  invoiceName: { type: String, required: true },
  doctype:     { type: String, default: 'Sales Invoice' },
})
const emit = defineEmits(['close'])

const showThermal    = ref(false)
const loading        = ref(false)
const printers       = ref([])
const templates      = ref([])
const selectedPrinter  = ref('')
const selectedTemplate = ref('')
const printing       = ref(false)
const error          = ref('')
const success        = ref('')

function handleKeydown(e) {
  if (e.key === 'Escape') {
    if (showThermal.value) showThermal.value = false
    else emit('close')
    return
  }

  if (!showThermal.value) {
    if (e.key === '1') {
      e.preventDefault()
      openThermal()
    } else if (e.key === '2') {
      e.preventDefault()
      openPreview()
    }
  } else {
    if (e.key === 'End' || e.key === 'Enter') {
      e.preventDefault()
      sendPrint()
    } else if (e.key === 'Backspace') {
      showThermal.value = false
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

async function openThermal() {
  showThermal.value = true
  if (printers.value.length) return   // already loaded

  loading.value = true
  error.value = ''
  try {
    const [p, t] = await Promise.all([
      frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers'),
      frappeGet('frappe.client.get_list', {
        doctype: 'Print Template',
        filters: JSON.stringify({ document_type: props.doctype }),
        fields: JSON.stringify(['name']),
        limit: 50,
      }),
    ])
    printers.value  = p || []
    templates.value = t || []

    const def = printers.value.find(pr => pr.is_default) || printers.value[0]
    if (def) selectedPrinter.value = def.name
    if (templates.value.length) selectedTemplate.value = templates.value[0].name
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function sendPrint() {
  if (!selectedPrinter.value || !selectedTemplate.value) return
  printing.value = true
  error.value   = ''
  success.value = ''
  try {
    const res = await frappePost(
      'printer_server_configuration.printer_server_configuration.api.print_document',
      {
        printer:        selectedPrinter.value,
        print_template: selectedTemplate.value,
        document_type:  props.doctype,
        document_name:  props.invoiceName,
        title:          props.invoiceName,
      },
    )
    success.value = `Sent to printer — Job ${res.cups_job_id}`
  } catch (e) {
    error.value = e.message
  } finally {
    printing.value = false
  }
}

function openPreview() {
  window.open(
    `/printview?doctype=${encodeURIComponent(props.doctype)}&name=${encodeURIComponent(props.invoiceName)}&trigger_print=0`,
    '_blank',
  )
}
</script>
