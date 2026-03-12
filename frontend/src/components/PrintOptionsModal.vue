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

      <!-- ── Combined Print Options ── -->
      <div class="flex flex-col gap-5 p-6">
        <div v-if="loading" class="py-6 text-center text-xs font-medium" style="color:#94a3b8">
          Loading printers &amp; templates…
        </div>

        <template v-else>
          <!-- Settings Selection -->
          <div class="space-y-4">
            <!-- Printer -->
            <div>
              <div class="mb-1 flex items-center justify-between">
                <label class="block text-[10px] uppercase tracking-wider font-bold" style="color:#94a3b8">Printer</label>
                <kbd class="rounded border border-gray-200 bg-white px-1 py-0.5 font-mono text-[9px] text-gray-400">F2</kbd>
              </div>
              <select
                ref="printerSelect"
                v-model="selectedPrinter"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all shadow-sm"
                style="background:#f8fafc;border-color:#e2e8f0;color:#1e293b"
                @focus="e => { e.target.style.borderColor='#3b82f6'; e.target.style.background='#ffffff' }"
                @blur="e => { e.target.style.borderColor='#e2e8f0'; e.target.style.background='#f8fafc' }"
              >
                <option v-for="p in printers" :key="p.name" :value="p.name">
                  {{ p.printer_name }} — {{ p.status }}
                </option>
                <option v-if="!printers.length" disabled value="">No printers found</option>
              </select>
            </div>

            <!-- Template -->
            <div>
              <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold" style="color:#94a3b8">Template</label>
              <select
                v-model="selectedTemplate"
                class="w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all shadow-sm"
                style="background:#f8fafc;border-color:#e2e8f0;color:#1e293b"
                @focus="e => { e.target.style.borderColor='#3b82f6'; e.target.style.background='#ffffff' }"
                @blur="e => { e.target.style.borderColor='#e2e8f0'; e.target.style.background='#f8fafc' }"
              >
                <option v-for="t in templates" :key="t.name" :value="t.name">{{ t.name }}</option>
                <option v-if="!templates.length" disabled value="">No templates found</option>
              </select>
            </div>
          </div>

          <!-- Error / success -->
          <div v-if="error" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#fef2f2;color:#ef4444;border-color:#fee2e2">{{ error }}</div>
          <div v-if="success" class="rounded-lg px-3 py-2 text-xs font-medium border" style="background:#f0fdf4;color:#16a34a;border-color:#dcfce7">{{ success }}</div>

          <!-- Actions -->
          <div class="flex flex-col gap-3 mt-2">
            <button
              @click="sendPrint"
              :disabled="printing || !printers.length || !templates.length"
              class="w-full rounded-xl py-3.5 text-sm font-bold tracking-wider transition-all flex items-center justify-center gap-3 shadow-md"
              :style="(!printing && printers.length && templates.length)
                ? 'background:#2563eb;color:#fff;cursor:pointer'
                : 'background:#f1f5f9;color:#94a3b8;cursor:not-allowed'"
            >
              <span class="text-lg">🖨</span>
              {{ printing ? 'Sending to printer…' : 'Print Now' }}
              <kbd v-if="!printing" class="rounded border border-blue-400 bg-blue-500 px-1.5 py-0.5 font-mono text-[10px] text-white">Enter</kbd>
            </button>

            <button
              @click="openPreview"
              class="w-full rounded-xl py-3 text-sm font-bold border border-gray-200 transition-all flex items-center justify-center gap-3 hover:bg-gray-50 text-gray-600"
            >
              <span class="text-lg">📄</span>
              Print Preview
              <kbd class="rounded border border-gray-200 bg-white px-1.5 py-0.5 font-mono text-[10px] text-gray-400">P</kbd>
            </button>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { frappeGet, frappePost } from '../api.js'

const props = defineProps({
  invoiceName: { type: String, required: true },
  doctype:     { type: String, default: 'Sales Invoice' },
  initialPrintFormat: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const printerSelect  = ref(null)
const loading        = ref(false)
const printers       = ref([])
const templates      = ref([])
const selectedPrinter  = ref('')
const selectedTemplate = ref('')
const printing       = ref(false)
const error          = ref('')
const success        = ref('')

const GENERAL_SETTINGS_CACHE_KEY = 'wb-general-settings-v1'

function syncPrinter() {
  const template = selectedTemplate.value
  if (!template || !printers.value.length) return
  
  let targetPrinter = ''
  try {
    const cached = JSON.parse(localStorage.getItem(GENERAL_SETTINGS_CACHE_KEY) || 'null')
    if (cached?.data?.printer_settings) {
      const mapping = cached.data.printer_settings.find(ps => ps.template === template)
      if (mapping) targetPrinter = mapping.printer
    }
  } catch (e) {}

  if (targetPrinter && printers.value.some(pr => pr.name === targetPrinter)) {
    selectedPrinter.value = targetPrinter
  } else {
    // Fallback to default printer
    const def = printers.value.find(pr => pr.is_default) || printers.value[0]
    if (def) selectedPrinter.value = def.name
  }
}

watch(selectedTemplate, () => syncPrinter())

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    sendPrint()
  } else if (e.key === 'F2') {
    e.preventDefault()
    printerSelect.value?.focus()
  } else if (e.key.toLowerCase() === 'p') {
    e.preventDefault()
    openPreview()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadSettings()
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

async function loadSettings() {
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

    // Setting the template triggers the watcher to select the correct printer
    if (props.initialPrintFormat && templates.value.some(tmp => tmp.name === props.initialPrintFormat)) {
      selectedTemplate.value = props.initialPrintFormat
    } else if (templates.value.length) {
      selectedTemplate.value = templates.value[0].name
    }

    // Explicitly sync printer after printers are loaded, in case watcher ran too early
    syncPrinter()
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
