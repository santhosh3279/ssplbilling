<template>
  <div class="flex flex-col bg-[var(--color-bg)] overflow-hidden" :class="embedded ? 'h-full' : 'h-screen'">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="goBack"
        >
          {{ embedded ? '✕ Close' : '← Dashboard' }}
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Document Print</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Upload a PDF or image and print it — nothing is saved</p>
        </div>
      </div>
      <span class="hidden sm:inline text-xs text-[var(--color-text-muted)]">
        <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F2</kbd> Choose file
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F8</kbd> Print
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> {{ embedded ? 'Close' : 'Back' }}
      </span>
    </header>

    <main class="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-[360px_1fr] text-[var(--color-text)]">
      <!-- Controls -->
      <aside class="flex flex-col gap-4 overflow-y-auto border-b md:border-b-0 md:border-r border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <div
          class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors"
          :class="dragging
            ? 'border-[var(--color-info)] bg-[var(--color-info)]/15'
            : 'border-[var(--color-border)] hover:bg-[var(--color-surface-raised)]'"
          @click="fileInput?.click()"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <span class="text-3xl">🖨️</span>
          <span class="text-sm font-semibold">{{ file ? file.name : 'Click or drop a file here' }}</span>
          <span class="text-xs text-[var(--color-text-muted)]">
            {{ file ? formatSize(file.size) : 'PDF, JPG, PNG, WEBP — up to 25 MB' }}
          </span>
          <input
            ref="fileInput"
            type="file"
            class="hidden"
            :accept="ACCEPT"
            @change="onPick"
          />
        </div>
        <button
          v-if="file"
          class="self-start text-xs font-semibold text-[var(--color-danger)] hover:underline"
          @click="clearFile"
        >
          Remove file
        </button>

        <div>
          <label class="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">
            Printer
            <button class="normal-case tracking-normal font-semibold text-[var(--color-info)] hover:underline" @click="loadPrinters">Reload</button>
          </label>
          <select v-model="selectedPrinter" :class="inputCls" :disabled="loadingPrinters">
            <option v-if="loadingPrinters" value="">Loading printers…</option>
            <option v-else-if="!printers.length" disabled value="">No PDF printers found</option>
            <option v-for="p in printers" :key="p.name" :value="p.name">
              {{ p.printer_name || p.name }} — {{ p.status || 'Unknown' }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">Copies</label>
          <input v-model.number="copies" type="number" min="1" :max="MAX_COPIES" :class="inputCls" />
        </div>

        <div>
          <label class="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">
            Pages
            <span class="normal-case tracking-normal font-semibold">
              <template v-if="countingPages">Counting…</template>
              <template v-else-if="totalPages">{{ totalPages }} page{{ totalPages === 1 ? '' : 's' }} in file</template>
            </span>
          </label>
          <div class="grid grid-cols-3 gap-1 rounded-lg bg-[var(--color-surface-raised)] p-1">
            <button
              v-for="m in PAGE_MODES"
              :key="m.id"
              class="rounded-md px-2 py-1.5 text-xs font-semibold transition-colors"
              :class="pageMode === m.id
                ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
              @click="setPageMode(m.id)"
            >
              {{ m.label }}
            </button>
          </div>
          <div v-if="pageMode === 'single'" class="mt-2">
            <input v-model.number="pageFrom" type="number" min="1" :max="totalPages || undefined" placeholder="Page number" :class="inputCls" />
          </div>
          <div v-else-if="pageMode === 'range'" class="mt-2 flex items-center gap-2">
            <input v-model.number="pageFrom" type="number" min="1" :max="totalPages || undefined" placeholder="From" :class="inputCls" />
            <span class="text-xs text-[var(--color-text-muted)]">to</span>
            <input v-model.number="pageTo" type="number" min="1" :max="totalPages || undefined" placeholder="To" :class="inputCls" />
          </div>
          <p v-if="pageError" class="mt-1 text-xs text-[var(--color-danger)]">{{ pageError }}</p>
        </div>

        <button
          class="rounded-lg px-4 py-3 text-sm font-bold uppercase tracking-wider transition-all active:scale-95"
          :class="canPrint
            ? 'bg-[var(--color-success)] text-[var(--color-text-on-highlight)] hover:bg-[var(--color-success)]/80'
            : 'bg-[var(--color-surface-raised)] text-[var(--color-text-muted)] cursor-not-allowed'"
          :disabled="!canPrint"
          @click="sendPrint"
        >
          {{ printing ? 'Sending to printer…' : 'Print' }}
        </button>

        <p v-if="error" class="rounded-lg bg-[var(--color-danger)]/15 px-3 py-2 text-sm text-[var(--color-danger)] whitespace-pre-wrap">{{ error }}</p>
        <p v-if="success" class="rounded-lg bg-[var(--color-success)]/15 px-3 py-2 text-sm text-[var(--color-success)]">{{ success }}</p>
      </aside>

      <!-- Preview: rendered from a local object URL, the file never leaves the browser until Print -->
      <section class="flex min-h-0 flex-col overflow-hidden p-4">
        <div v-if="!previewUrl" class="flex flex-1 items-center justify-center text-sm italic text-[var(--color-text-muted)]">
          Preview appears here once a file is chosen.
        </div>
        <iframe
          v-else-if="isPdf"
          :src="previewUrl"
          class="flex-1 w-full rounded-xl border border-[var(--color-border)] bg-white"
          title="Document preview"
        />
        <div v-else class="flex flex-1 items-center justify-center overflow-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <img :src="previewUrl" alt="Document preview" class="max-h-full max-w-full object-contain" />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet } from '../api.js'
import { session } from '../session.js'

const router = useRouter()

const ACCEPT = 'application/pdf,.pdf,image/jpeg,image/png,image/webp,image/bmp,image/gif,image/tiff'
const MAX_BYTES = 25 * 1024 * 1024
const MAX_COPIES = 50
const inputCls = 'w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] outline-none focus:border-[var(--color-info)]'

const fileInput = ref(null)
const file = ref(null)
const previewUrl = ref('')
const dragging = ref(false)
const printers = ref([])
const selectedPrinter = ref('')
const loadingPrinters = ref(false)
const copies = ref(1)
const printing = ref(false)
const error = ref('')
const success = ref('')
// Embedded: opened as a window over another page (WhatsApp Chat) with its file already loaded
const props = defineProps({
  embedded: { type: Boolean, default: false },
  initialFile: { type: Object, default: null },
})
const emit = defineEmits(['close'])

function goBack() {
  if (props.embedded) emit('close')
  else router.push('/')
}

const PAGE_MODES = [
  { id: 'all', label: 'All' },
  { id: 'single', label: 'One page' },
  { id: 'range', label: 'Range' },
]
const pageMode = ref('all')
const pageFrom = ref(1)
const pageTo = ref(1)
const totalPages = ref(0)
const countingPages = ref(false)

const isPdf = computed(() => !!file.value && (file.value.type === 'application/pdf' || /\.pdf$/i.test(file.value.name)))

// [from, to] to send, or null for all pages
const pageSelection = computed(() => {
  if (pageMode.value === 'single') return [Number(pageFrom.value), Number(pageFrom.value)]
  if (pageMode.value === 'range') return [Number(pageFrom.value), Number(pageTo.value)]
  return null
})
const pageError = computed(() => {
  const sel = pageSelection.value
  if (!sel) return ''
  const [from, to] = sel
  if (!Number.isInteger(from) || !Number.isInteger(to) || from < 1 || to < 1) return 'Enter page numbers of 1 or more'
  if (from > to) return 'From page must not be after To page'
  if (totalPages.value && to > totalPages.value) return `File has only ${totalPages.value} page${totalPages.value === 1 ? '' : 's'}`
  return ''
})
const canPrint = computed(() => !!file.value && !!selectedPrinter.value && !printing.value && !pageError.value)

function setPageMode(mode) {
  pageMode.value = mode
  if (mode === 'range' && (!pageTo.value || pageTo.value < pageFrom.value)) {
    pageTo.value = totalPages.value || pageFrom.value || 1
  }
}

// Frappe errors carry the message in _server_messages (may contain HTML like <br>)
async function postFile(method, fields) {
  const body = new FormData()
  body.append('file', file.value, file.value.name)
  for (const [k, v] of Object.entries(fields)) body.append(k, v)
  const res = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': window.csrf_token ?? 'fetch' },
    body,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    let msg = `HTTP ${res.status} — ${res.statusText}`
    try {
      const server = JSON.parse(data._server_messages || '[]')
      if (server.length) msg = JSON.parse(server[0]).message || msg
    } catch { /* keep HTTP message */ }
    throw new Error(msg.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, ''))
  }
  return data.message || {}
}

async function countPages() {
  const current = file.value
  totalPages.value = 0
  if (!current) return
  countingPages.value = true
  try {
    const r = await postFile('ssplbilling.api.document_print_api.count_pages', {})
    if (file.value === current) totalPages.value = Number(r.total_pages) || 0
  } catch (e) {
    if (file.value === current) error.value = e.message || 'Could not read the PDF'
  } finally {
    if (file.value === current) countingPages.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function setFile(f) {
  error.value = ''
  success.value = ''
  if (!f) return
  const okType = f.type === 'application/pdf' || f.type.startsWith('image/') || /\.(pdf|jpe?g|png|webp|bmp|gif|tiff?)$/i.test(f.name)
  if (!okType) {
    error.value = 'Only PDF and image files can be printed'
    return
  }
  if (f.size > MAX_BYTES) {
    error.value = 'File is larger than 25 MB'
    return
  }
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = f
  previewUrl.value = URL.createObjectURL(f)
  pageMode.value = 'all'
  pageFrom.value = 1
  pageTo.value = 1
  countPages()
}

function onPick(e) {
  setFile(e.target.files?.[0])
  e.target.value = ''
}

function onDrop(e) {
  dragging.value = false
  setFile(e.dataTransfer?.files?.[0])
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = null
  previewUrl.value = ''
  success.value = ''
  error.value = ''
  totalPages.value = 0
  countingPages.value = false
  pageMode.value = 'all'
}

// Printers the user is allowed in SSPL Printer Setting (wb-printer-records); empty list = all
function allowedPrinterNames() {
  try {
    const user = session.user.value || ''
    const rows = JSON.parse(localStorage.getItem('wb-printer-records') || '[]')
    return new Set(rows.filter(r => !r.user || r.user === user).map(r => r.printer).filter(Boolean))
  } catch {
    return new Set()
  }
}

async function loadPrinters() {
  loadingPrinters.value = true
  error.value = ''
  try {
    const list = (await frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers')) || []
    const allowed = allowedPrinterNames()
    const mine = allowed.size ? list.filter(p => allowed.has(p.name)) : []
    const pool = mine.length ? mine : list
    // Uploads are always sent as PDF, so only PDF-capable printers are offered
    const isPdfPrinter = p => /pdf|a4|laser/i.test(p.printer_name || p.name)
    printers.value = pool.filter(isPdfPrinter)

    const remembered = localStorage.getItem('wb-document-printer')
    if (remembered && printers.value.some(p => p.name === remembered)) {
      selectedPrinter.value = remembered
    } else if (!printers.value.some(p => p.name === selectedPrinter.value)) {
      selectedPrinter.value = (printers.value.find(p => p.is_default) || printers.value[0])?.name || ''
    }
  } catch (e) {
    printers.value = []
    error.value = e.message || 'Could not load printers'
  } finally {
    loadingPrinters.value = false
  }
}

async function sendPrint() {
  if (!canPrint.value) return
  printing.value = true
  error.value = ''
  success.value = ''
  try {
    const fields = {
      printer: selectedPrinter.value,
      copies: String(Math.max(1, Math.min(Number(copies.value) || 1, MAX_COPIES))),
    }
    const sel = pageSelection.value
    if (sel) {
      fields.page_from = String(sel[0])
      fields.page_to = String(sel[1])
    }
    const r = await postFile('ssplbilling.api.document_print_api.print_uploaded_file', fields)
    try { localStorage.setItem('wb-document-printer', selectedPrinter.value) } catch { /* ignore */ }
    const n = r.copies || 1
    const pages = sel
      ? (sel[0] === sel[1] ? ` (page ${sel[0]})` : ` (pages ${sel[0]}–${sel[1]})`)
      : (r.total_pages ? ` (all ${r.total_pages} page${r.total_pages === 1 ? '' : 's'})` : '')
    success.value = `Sent ${n} cop${n === 1 ? 'y' : 'ies'}${pages} to ${r.printer || selectedPrinter.value}${r.cups_job_id ? ` — Job ${r.cups_job_id}` : ''}`
  } catch (e) {
    error.value = e.message || 'Print failed'
  } finally {
    printing.value = false
  }
}

function onKey(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    goBack()
  } else if (e.key === 'F2') {
    e.preventDefault()
    fileInput.value?.click()
  } else if (e.key === 'F8') {
    e.preventDefault()
    sendPrint()
  }
}

onMounted(() => {
  if (props.initialFile) setFile(props.initialFile)
  loadPrinters()
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>
