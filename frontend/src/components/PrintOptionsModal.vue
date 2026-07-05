<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <div
      class="overflow-hidden rounded-2xl border border-[var(--color-border)] shadow-2xl flex transition-all duration-300 bg-[var(--color-bg)] text-[var(--color-text)]"
      style="width: 400px"
    >

      <!-- Left panel: controls (always visible) -->
      <div class="flex flex-col w-full">

        <!-- Header -->
        <div class="flex items-center justify-between border-b border-[var(--color-border)] px-6 py-4 bg-[var(--color-surface)]">
          <div>
            <div class="text-[10px] uppercase tracking-widest font-bold text-[var(--color-text-muted)]">{{ headerLabel }}</div>
            <div class="font-mono text-xl font-bold text-[var(--color-success)]">{{ invoiceName }}</div>
          </div>
          <button
            @click="$emit('close')"
            class="rounded-lg px-3 py-1.5 text-xs transition-colors border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
          >
            ✕ Close
          </button>
        </div>

        <!-- ── Combined Print Options ── -->
        <div class="flex flex-col gap-5 p-6 overflow-y-auto flex-1">
          <div v-if="loading" class="py-6 text-center text-xs font-medium text-[var(--color-text-muted)]">
            Loading printers &amp; templates…
          </div>

          <template v-else>
            <!-- Settings Selection -->
            <div class="space-y-4">
              <!-- Template -->
              <div>
                <div class="mb-1 flex items-center justify-between">
                  <label class="block text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">Template</label>
                  <kbd v-if="!lockTemplate" class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[9px] text-[var(--color-text-muted)]">F2</kbd>
                </div>
                <select
                  ref="templateSelect"
                  v-model="selectedTemplate"
                  :disabled="lockTemplate"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none transition-all shadow-sm focus:border-[var(--color-info)] disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-[var(--color-surface-raised)]"
                >
                  <option v-for="t in templates" :key="t.name" :value="t.name">{{ t.name }}</option>
                  <option v-if="!templates.length" disabled value="">No templates found</option>
                </select>
              </div>

              <!-- Printer -->
              <div>
                <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">Printer</label>
                <select
                  ref="printerSelect"
                  v-model="selectedPrinter"
                  class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none transition-all shadow-sm focus:border-[var(--color-info)]"
                >
                  <option v-for="p in printers" :key="p.name" :value="p.name">
                    {{ p.printer_name }} — {{ p.status }}
                  </option>
                  <option v-if="!printers.length" disabled value="">No printers found</option>
                </select>
              </div>
            </div>

            <!-- Error / success -->
            <div v-if="error" class="rounded-lg px-3 py-2 text-xs font-medium border bg-[var(--color-danger)]/20 text-[var(--color-danger)] border-[var(--color-danger)]">{{ error }}</div>
            <div v-if="success" class="rounded-lg px-3 py-2 text-xs font-medium border bg-[var(--color-success)]/20 text-[var(--color-success)] border-[var(--color-success)]">{{ success }}</div>

            <!-- Actions -->
            <div class="flex flex-col gap-3 mt-2">
              <button
                ref="printNowBtn"
                @click="sendPrint"
                :disabled="printing || !printers.length || !templates.length"
                class="w-full rounded-xl py-3.5 text-sm font-bold tracking-wider transition-all flex items-center justify-center gap-3 shadow-md"
                :class="(!printing && printers.length && templates.length)
                  ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)] hover:bg-[var(--color-info)] cursor-pointer'
                  : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] cursor-not-allowed'"
              >
                <span class="text-lg">🖨</span>
                {{ printing ? 'Sending to printer…' : 'Print Now' }}
                <kbd v-if="!printing" class="rounded border border-[var(--color-info)] bg-[var(--color-info)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-on-highlight)]">Enter</kbd>
              </button>

              <button
                @click="openPreview"
                :disabled="previewing || !templates.length"
                class="w-full rounded-xl py-3 text-sm font-bold border transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed border-[var(--color-border)] text-[var(--color-text)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-raised)]"
              >
                <span class="text-lg">📄</span>
                {{ previewing ? 'Generating…' : 'Print Preview' }}
                <kbd v-if="!previewing" class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-muted)]">P</kbd>
              </button>
            </div>
          </template>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { frappeGet, frappePost } from '../api.js'
import { useSubwindow } from '../services/shortcutManager'

useSubwindow()

const props = defineProps({
  invoiceName: { type: String, required: true },
  doctype:     { type: String, default: 'Sales Invoice' },
  initialTemplate: { type: String, default: '' },
  series:      { type: String, default: '' },
  // Fix the template to initialTemplate: select is greyed out, only the printer can be changed
  lockTemplate: { type: Boolean, default: false },
  headerLabel: { type: String, default: 'Bill Saved' },
})
const emit = defineEmits(['close'])

const printerSelect  = ref(null)
const templateSelect = ref(null)
const printNowBtn    = ref(null)
const loading        = ref(false)
const printers       = ref([])
const templates      = ref([])
const selectedPrinter  = ref('')
const selectedTemplate = ref('')
const printing       = ref(false)
const previewing     = ref(false)
const previewUrls    = ref([])
const error          = ref('')
const success        = ref('')

const SETTINGS_CACHE_KEY = 'wb-settings-v2'

// Returns printer_settings rows for the current user from the billing settings cache
function getUserPrinterSettings() {
  try {
    const cachedTemplates = JSON.parse(localStorage.getItem('wb-printer-templates') || '[]')
    const cachedSettings = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const currentUser = cachedSettings?.data?._current_user || ''
    
    // Filter by current user; fall back to all rows if no user field is set
    const userRows = cachedTemplates.filter(ps => ps.user === currentUser)
    return userRows.length ? userRows : cachedTemplates.filter(ps => !ps.user)
  } catch (e) {
    return []
  }
}

function syncPrinter() {
  const template = selectedTemplate.value
  if (!template || !printers.value.length) return

  const userRows = getUserPrinterSettings()
  const mapping = userRows.find(ps => ps.template === template)
  const targetPrinter = mapping?.printer || ''

  if (targetPrinter && printers.value.some(pr => pr.name === targetPrinter)) {
    selectedPrinter.value = targetPrinter
    return
  }

  // Locked-template mode (e.g. e-Way Bill): default to a PDF printer if one exists
  if (props.lockTemplate) {
    const pdfPrinter = printers.value.find(pr => /pdf/i.test(pr.printer_name || pr.name))
    if (pdfPrinter) {
      selectedPrinter.value = pdfPrinter.name
      return
    }
  }

  const userDefault = localStorage.getItem('wb-default-printer') || localStorage.getItem('wb-printer')
  if (userDefault && printers.value.some(pr => pr.name === userDefault)) {
    selectedPrinter.value = userDefault
  } else {
    const def = printers.value.find(pr => pr.is_default) || printers.value[0]
    if (def) selectedPrinter.value = def.name
  }
}

watch(selectedTemplate, () => syncPrinter())
// Note: no watch on selectedPrinter — changing printer must not auto-change the template

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }

  if (e.key === 'Enter') {
    const active = document.activeElement
    if (active === templateSelect.value) {
      e.preventDefault()
      printerSelect.value?.focus()
    } else if (active === printerSelect.value) {
      e.preventDefault()
      printNowBtn.value?.focus()
    } else {
      e.preventDefault()
      sendPrint()
    }
  } else if (e.key === 'F2') {
    e.preventDefault()
    if (!props.lockTemplate) templateSelect.value?.focus()
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
  previewUrls.value.forEach(url => {
    try {
      URL.revokeObjectURL(url)
    } catch (e) {
      // ignore
    }
  })
})

async function loadSettings() {
  loading.value = true
  error.value = ''
  try {
    const userRows = getUserPrinterSettings()

    // Locked template mode: template is fixed by the caller, only the printer is selectable
    if (props.lockTemplate && props.initialTemplate) {
      const allPrinters = await frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers')
      const uniquePrinterNames = [...new Set(userRows.map(r => r.printer).filter(Boolean))]
      const filteredPrinters = (allPrinters || []).filter(p => uniquePrinterNames.includes(p.name))
      printers.value  = filteredPrinters.length ? filteredPrinters : (allPrinters || [])
      templates.value = [{ name: props.initialTemplate }]
      selectedTemplate.value = props.initialTemplate
      syncPrinter()
      return
    }

    // 1. Fetch all valid print templates for this doctype to ensure we only show relevant ones
    const validTemplates = await frappeGet('frappe.client.get_list', {
      doctype: 'Print Template',
      filters: { document_type: props.doctype },
      fields: ['name'],
      limit: 100
    })
    const validTemplateNames = validTemplates.map(f => f.name)

    if (userRows.length) {
      // 2. Filter cached user templates to only those that exist for this doctype
      const filteredTemplates = userRows
        .filter(r => r.template && validTemplateNames.includes(r.template))
        .map(r => ({ name: r.template }))
      
      // Deduplicate
      const uniqueTemplates = [...new Map(filteredTemplates.map(t => [t.name, t])).values()]
      
      const uniquePrinterNames = [...new Set(userRows.map(r => r.printer).filter(Boolean))]

      // Fetch all printers for status info, then filter to user's printers
      const allPrinters = await frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers')
      const filteredPrinters = (allPrinters || []).filter(p => uniquePrinterNames.includes(p.name))
      
      printers.value  = filteredPrinters.length ? filteredPrinters : (allPrinters || [])
      templates.value = uniqueTemplates
      
      // If no cached templates matched the doctype, fall back to all valid templates
      if (!templates.value.length) {
        templates.value = validTemplates
      }
    } else {
      // No user-specific rows — fall back to fetching all printers + templates for this doctype
      const [p] = await Promise.all([
        frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers'),
      ])
      printers.value  = p || []
      templates.value = validTemplates
    }

    let initialTemplate = props.initialTemplate

    try {
      const cachedSettings = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
      const billingSeries = cachedSettings?.data?.billing_series || []
      
      let matchedSeries = null
      if (props.series) {
        matchedSeries = billingSeries.find(bs => bs.series === props.series)
      }
      if (!matchedSeries && props.invoiceName) {
        matchedSeries = billingSeries.find(bs => bs.series && props.invoiceName.startsWith(bs.series))
      }

      if (matchedSeries?.print_format) {
        initialTemplate = matchedSeries.print_format
      }
    } catch (e) {
      console.warn('[PrintOptionsModal] Failed to resolve series print template:', e)
    }

    if (initialTemplate && templates.value.some(tmp => tmp.name === initialTemplate)) {
      selectedTemplate.value = initialTemplate
    } else if (templates.value.length) {
      selectedTemplate.value = templates.value[0].name
    }

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
    emit('close')
  } catch (e) {
    error.value = e.message
  } finally {
    printing.value = false
  }
}

async function openPreview() {
  if (!selectedTemplate.value) return
  previewing.value = true
  error.value = ''
  try {
    const b64 = await frappePost('run_doc_method', {
      dt: 'Print Template',
      dn: selectedTemplate.value,
      method: 'preview_pdf',
      args: JSON.stringify({ document_name: props.invoiceName }),
    })
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
    const blob = new Blob([bytes], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    previewUrls.value.push(url)
    window.open(url, '_blank')
  } catch (e) {
    // preview_pdf failed (e.g. CUPS PDF renderer not configured for thermal templates)
    // fall back to Frappe's built-in printview in a new tab
    const fallbackUrl = `/printview?doctype=${encodeURIComponent(props.doctype)}&name=${encodeURIComponent(props.invoiceName)}&format=${encodeURIComponent(selectedTemplate.value)}&trigger_print=0`
    window.open(fallbackUrl, '_blank')
  } finally {
    previewing.value = false
  }
}
</script>
