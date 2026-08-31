<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
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
          <div class="flex items-center gap-2">
            <button
              @click="refreshLists"
              :disabled="refreshing || loading"
              title="Reload templates and printers from the server (R)"
              class="rounded-lg px-3 py-1.5 text-xs transition-colors border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span :class="refreshing ? 'inline-block animate-spin' : ''">⟳</span>
              {{ refreshing ? 'Refreshing…' : 'Refresh' }}
            </button>
            <button
              @click="$emit('close')"
              class="rounded-lg px-3 py-1.5 text-xs transition-colors border border-[var(--color-border)] bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)]"
            >
              ✕ Close
            </button>
          </div>
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

              <button
                @click="sendWhatsApp"
                :disabled="whatsapping || !templates.length"
                class="w-full rounded-xl py-3 text-sm font-bold border transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed border-[#25D366] text-[#25D366] bg-[var(--color-surface)] hover:bg-[#25D366]/10"
              >
                <span class="text-lg">💬</span>
                {{ whatsapping ? 'Preparing bill…' : 'Send on WhatsApp' }}
                <kbd v-if="!whatsapping" class="rounded border border-[#25D366] px-1.5 py-0.5 font-mono text-[10px] text-[#25D366]">W</kbd>
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
import { getCachedPrintLists, refreshPrintCache, loadPrintLists } from '../services/printCache'
import { hasWhatsAppBridge, openWhatsAppTab } from '../services/whatsappBridge'

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
const whatsapping    = ref(false)
const refreshing     = ref(false)
const error          = ref('')
const success        = ref('')

const SETTINGS_CACHE_KEY = 'wb-settings-v2'

// Print Template.format_type -> keyword to match against Printer.printer_name, so the
// printer dropdown only shows printers built for the selected template's output type
// (same convention as the barcode-only filter in BarcodePrintPage.vue).
const FORMAT_TYPE_KEYWORD = {
  'Thermal': 'thermal',
  'PDF': 'pdf',
  'Custom PDF': 'pdf',
  'Barcode': 'barcode',
}

const allPrinters = ref([])       // unfiltered printer list for this doctype
const templateFormatMap = ref({}) // template name -> format_type

// Returns printer rows ({user, printer, template}) for the current user. SSPL Printer
// Setting records (wb-printer-records) come first so they win the .find() in syncPrinter;
// the legacy SSPL Billing Settings child table (wb-printer-templates) is the fallback.
function getUserPrinterSettings() {
  try {
    const cachedSettings = JSON.parse(localStorage.getItem(SETTINGS_CACHE_KEY) || 'null')
    const currentUser = cachedSettings?.data?._current_user || ''

    // Rows with no user are wildcards — a printer whose allowed-users table is empty
    const forUser = rows => {
      const mine = rows.filter(ps => ps.user === currentUser)
      const anyUser = rows.filter(ps => !ps.user)
      return [...mine, ...anyUser]
    }

    const printerRecords = JSON.parse(localStorage.getItem('wb-printer-records') || '[]')

    // Legacy rows keep their original either/or semantics: a user with own rows
    // never saw the blank-user rows, and widening that would change the dropdown
    const legacyRows = JSON.parse(localStorage.getItem('wb-printer-templates') || '[]')
    const legacyMine = legacyRows.filter(ps => ps.user === currentUser)
    const legacy = legacyMine.length ? legacyMine : legacyRows.filter(ps => !ps.user)

    return [...forUser(printerRecords), ...legacy]
  } catch (e) {
    return []
  }
}

// Narrows `printers` to those matching the selected template's format_type (Thermal/PDF/
// Custom PDF/Barcode), then further to the user's saved printers within that type when any
// qualify. Locked-template mode keeps its own dedicated PDF-only filtering (no format is
// being "selected" there), so this is a no-op for it.
function filterPrintersForTemplate(templateName) {
  if (props.lockTemplate || !allPrinters.value.length) return

  const keyword = FORMAT_TYPE_KEYWORD[templateFormatMap.value[templateName]]
  const typeMatched = keyword
    ? allPrinters.value.filter(pr => new RegExp(keyword, 'i').test(pr.printer_name || pr.name))
    : allPrinters.value
  const typeFiltered = typeMatched.length ? typeMatched : allPrinters.value

  const rows = getUserPrinterSettings()
  const uniquePrinterNames = new Set(rows.map(r => r.printer).filter(Boolean))
  const userFiltered = typeFiltered.filter(p => uniquePrinterNames.has(p.name))
  const pool = userFiltered.length ? userFiltered : typeFiltered

  // Printers that list this template (or list none at all, i.e. accept anything)
  // come first, so the format drives which printer the dropdown offers
  const templateNames = new Set(
    rows.filter(r => r.template === templateName || !r.template).map(r => r.printer).filter(Boolean)
  )
  const templateMatched = pool.filter(p => templateNames.has(p.name))

  printers.value = templateMatched.length ? templateMatched : pool
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

watch(selectedTemplate, () => {
  filterPrintersForTemplate(selectedTemplate.value)
  syncPrinter()
})
// Note: no watch on selectedPrinter — changing printer must not auto-change the template

function handleKeydown(e) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }

  // Browser shortcuts (Cmd/Ctrl+W to close the tab, Alt+P, …) must reach the browser
  // instead of triggering a print, a refresh or a WhatsApp share.
  if (e.ctrlKey || e.metaKey || e.altKey) return

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
  } else if (e.key.toLowerCase() === 'r') {
    e.preventDefault()
    refreshLists()
  } else if (e.key.toLowerCase() === 'w') {
    e.preventDefault()
    sendWhatsApp()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadSettings()
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// Cache-first load: when both lists are already in localStorage the modal renders
// with no network wait at all; a stale hit still renders instantly and revalidates
// in the background. Only a cold cache pays for a fetch, and that fetch runs both
// requests in parallel instead of sequentially.
function loadSettings() {
  error.value = ''
  const cached = getCachedPrintLists(props.doctype)

  if (cached) {
    applyLists(cached)
    loading.value = false
    if (!cached.fresh) revalidate()
    return
  }

  loading.value = true
  loadPrintLists(props.doctype)
    .then(lists => applyLists(lists))
    .catch(e => { error.value = e.message })
    .finally(() => { loading.value = false })
}

// Background refresh after a stale cache hit. Must not disturb what the operator is
// already looking at, so selections are preserved whenever they survive the new lists.
function revalidate() {
  refreshPrintCache(props.doctype)
    .then(lists => applyLists(lists, true))
    .catch(() => {
      // stale lists are still usable; a failed revalidate is not worth an error banner
    })
}

// Operator-triggered refresh, for when a template or printer was added server-side and
// the cached lists still predate it. Reuses the revalidate path so current selections
// survive whenever they still exist in the refreshed lists.
async function refreshLists() {
  if (refreshing.value) return
  refreshing.value = true
  error.value = ''
  success.value = ''
  try {
    const lists = await refreshPrintCache(props.doctype)
    applyLists(lists, true)
    success.value = `Refreshed — ${templates.value.length} template(s), ${printers.value.length} printer(s)`
  } catch (e) {
    error.value = 'Refresh failed: ' + (e.message || e)
  } finally {
    refreshing.value = false
  }
}

function applyLists({ templates: fetchedTemplates, printers: fetchedPrinters }, isRevalidate = false) {
  const previousTemplate = selectedTemplate.value
  const previousPrinter = selectedPrinter.value
  const userRows = getUserPrinterSettings()

  // Locked template mode: template is fixed by the caller, only the printer is selectable.
  // Output is an A4 PDF (e-Way Bill), so only PDF printers are shown — narrowed to the
  // user's allowed printers, falling back to all PDF printers if none of theirs qualify.
  if (props.lockTemplate && props.initialTemplate) {
    const pdfPrinters = (fetchedPrinters || []).filter(pr => /pdf/i.test(pr.printer_name || pr.name))
    const uniquePrinterNames = [...new Set(userRows.map(r => r.printer).filter(Boolean))]
    const filteredPrinters = pdfPrinters.filter(p => uniquePrinterNames.includes(p.name))
    printers.value  = filteredPrinters.length ? filteredPrinters : pdfPrinters
    templates.value = [{ name: props.initialTemplate }]
    selectedTemplate.value = props.initialTemplate
    if (isRevalidate && previousPrinter && printers.value.some(pr => pr.name === previousPrinter)) {
      selectedPrinter.value = previousPrinter
    } else {
      syncPrinter()
    }
    return
  }

  // Print Templates carry their format_type (Thermal/PDF/Custom PDF/Barcode), so the
  // printer list can be narrowed to printers built for whichever format the selected
  // template uses.
  const validTemplates = fetchedTemplates || []
  const validTemplateNames = validTemplates.map(f => f.name)
  templateFormatMap.value = Object.fromEntries(validTemplates.map(t => [t.name, t.format_type]))

  allPrinters.value = fetchedPrinters || []

  if (userRows.length) {
    // Filter cached user templates to only those that exist for this doctype
    const filteredTemplates = userRows
      .filter(r => r.template && validTemplateNames.includes(r.template))
      .map(r => ({ name: r.template }))

    // Deduplicate
    const uniqueTemplates = [...new Map(filteredTemplates.map(t => [t.name, t])).values()]

    // If no cached templates matched the doctype, fall back to all valid templates
    templates.value = uniqueTemplates.length ? uniqueTemplates : validTemplates
  } else {
    // No user-specific rows — fall back to all templates for this doctype
    templates.value = validTemplates
  }

  // A background revalidate keeps whatever is already selected as long as it survived
  // the refreshed lists, so the dropdowns never jump under the operator's hands.
  if (isRevalidate && previousTemplate && templates.value.some(tmp => tmp.name === previousTemplate)) {
    selectedTemplate.value = previousTemplate
    filterPrintersForTemplate(previousTemplate)
    if (previousPrinter && printers.value.some(pr => pr.name === previousPrinter)) {
      selectedPrinter.value = previousPrinter
    } else {
      syncPrinter()
    }
    return
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

  filterPrintersForTemplate(selectedTemplate.value)
  syncPrinter()
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

// Served-file preview endpoint for the current template + document.
function previewFileUrl() {
  const params = new URLSearchParams({
    print_template: selectedTemplate.value,
    document_name: props.invoiceName,
    doctype: props.doctype,
  })
  return `/api/method/ssplbilling.api.print_preview_api.preview_print_template_file?${params}`
}

async function openPreview() {
  if (!selectedTemplate.value) return
  previewing.value = true
  error.value = ''
  try {
    // Opened as a served file, not a blob URL: the response carries
    // Content-Disposition with "<invoice>.pdf", so the viewer's download button
    // saves the invoice number instead of a random UUID. The endpoint also
    // rotates A5 Portrait previews upright and redirects to Frappe's printview
    // when preview_pdf itself fails (e.g. thermal templates).
    window.open(previewFileUrl(), '_blank')
  } finally {
    previewing.value = false
  }
}

// The preview endpoint answers with Content-Disposition: inline, so the PDF has to be
// pulled as a blob and saved through an anchor to land in Downloads under the bill name.
function filenameFromDisposition(header) {
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header || '')
  if (encoded) {
    try { return decodeURIComponent(encoded[1]) } catch { /* fall through */ }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header || '')
  return plain ? plain[1] : `${props.invoiceName}.pdf`
}

async function downloadBillPdf() {
  const res = await fetch(previewFileUrl(), {
    headers: { 'X-Frappe-CSRF-Token': window.csrf_token ?? 'fetch' },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${res.statusText}`)
  // Templates whose preview_pdf fails (thermal ones do) redirect to Frappe's printview,
  // which fetch follows into an HTML page. Saving that as .pdf would be a corrupt bill.
  if (!/pdf/i.test(res.headers.get('Content-Type') || '')) {
    throw new Error(`"${selectedTemplate.value}" has no PDF output — pick a PDF template`)
  }

  const blob = await res.blob()
  const name = filenameFromDisposition(res.headers.get('Content-Disposition'))
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Revoked late so the browser has finished reading the blob for the save.
  setTimeout(() => URL.revokeObjectURL(url), 60000)
  return name
}

// A browser can only re-target a tab it opened itself, and only by the name it opened it
// under — a WhatsApp tab the operator opened by hand is unreachable from here. Naming the
// window keeps every share in one tab for the life of the browser session, whichever modal
// or page opened it, so the constant and the last-target memo live at module scope.
const WHATSAPP_WINDOW_NAME = 'sspl-whatsapp'
let lastWhatsappTab = null
let lastWhatsappUrl = ''
let lastWhatsappAt = 0

// How long a chat opened in the reused tab is assumed to still be the chat on screen.
// Past this the operator has probably moved around inside WhatsApp, so the tab is
// re-navigated to be sure the bill goes to the right party.
const WHATSAPP_REUSE_MS = 60000

// True only for a window still on about:blank; reading .location of a window already on
// web.whatsapp.com throws on the cross-origin access, which is itself the answer.
function isBlankWindow(win) {
  if (!win) return false
  try {
    return !win.location.href || win.location.href === 'about:blank'
  } catch {
    return false
  }
}

// WhatsApp cannot be handed a file through a URL — only text — so the bill is saved to
// Downloads and WhatsApp is opened on the party's chat for the operator to drag it in.
// The number comes from the party's Contact WhatsApp row (mobile_no as fallback); with
// no number on file WhatsApp opens unfiltered so the operator can search the contact.
async function sendWhatsApp() {
  if (!selectedTemplate.value || whatsapping.value) return
  whatsapping.value = true
  error.value = ''
  success.value = ''

  // With the SSPL WhatsApp Tab extension installed, the tab is found and focused by the
  // extension — opening one here as well would leave the operator with two.
  const viaBridge = hasWhatsAppBridge()

  // No extension: fall back to a named target so at least this app's own tab is reused.
  // WhatsApp's Cross-Origin-Opener-Policy clears that name once the tab reaches
  // web.whatsapp.com, so the reuse only holds until the first chat loads. Opened
  // synchronously inside the click because a window.open after the awaits below is
  // blocked as an unsolicited popup.
  const waTab = viaBridge ? null : window.open('', WHATSAPP_WINDOW_NAME)
  waTab?.focus()
  // Only a tab this click created is disposable. A reused one already holds the operator's
  // WhatsApp session and must survive a failure below. A fresh window is still same-origin
  // about:blank, which is the one thing readable across the boundary.
  const openedFresh = isBlankWindow(waTab)

  try {
    let recipient = { party: '', phone: '', amount: 0 }
    try {
      recipient = await frappeGet('ssplbilling.api.print_preview_api.get_whatsapp_recipient', {
        doctype: props.doctype,
        document_name: props.invoiceName,
      })
    } catch (e) {
      // A missing number must not block the share — WhatsApp still opens for a manual search.
      console.warn('[PrintOptionsModal] WhatsApp recipient lookup failed:', e)
    }

    const savedAs = await downloadBillPdf()

    const lines = [
      recipient.party ? `${recipient.party},` : '',
      `Bill ${props.invoiceName}`,
      // Returns carry a negative total; sending "Amount: -16" to a customer invites a call.
      recipient.amount > 0 ? `Amount: ${recipient.amount.toLocaleString('en-IN')}` : '',
    ].filter(Boolean)
    const text = encodeURIComponent(lines.join('\n'))

    const waUrl = recipient.phone
      ? `https://web.whatsapp.com/send?phone=${recipient.phone}&text=${text}`
      : `https://web.whatsapp.com/`

    if (viaBridge) {
      const relayed = await openWhatsAppTab(waUrl)
      success.value = relayed.ok
        ? `Saved "${savedAs}" — drag it into the WhatsApp tab`
        : `Saved "${savedAs}" — could not reach the WhatsApp tab (${relayed.error}); open WhatsApp and drag it in`
      return
    }

    if (!waTab) {
      success.value = `Saved "${savedAs}" — allow popups for this site to open WhatsApp automatically`
      return
    }

    // Re-navigating the reused tab reloads WhatsApp Web from scratch (slow, and it drops
    // whatever the operator had typed), so a tab already sitting on this exact chat is
    // left alone and merely focused. The tab is cross-origin, so its own location cannot
    // be read back — what was last sent there has to be remembered on this side.
    const sameChatStillOpen =
      waTab === lastWhatsappTab &&
      waUrl === lastWhatsappUrl &&
      Date.now() - lastWhatsappAt < WHATSAPP_REUSE_MS
    if (!sameChatStillOpen) {
      waTab.location = waUrl
      lastWhatsappTab = waTab
      lastWhatsappUrl = waUrl
    }
    lastWhatsappAt = Date.now()

    success.value = recipient.phone
      ? `Saved "${savedAs}" — drag it into the WhatsApp chat`
      : `Saved "${savedAs}" — no WhatsApp number on file, search the contact and drag it in`
  } catch (e) {
    if (openedFresh) waTab?.close()
    error.value = 'WhatsApp share failed: ' + (e.message || e)
  } finally {
    whatsapping.value = false
  }
}
</script>
