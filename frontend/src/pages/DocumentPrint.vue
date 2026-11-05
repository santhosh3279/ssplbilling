<template>
  <div class="flex h-screen flex-col bg-[var(--color-bg)] overflow-hidden">
    <header class="shrink-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div class="flex items-center gap-4">
        <button
          class="rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition-colors"
          @click="router.push('/')"
        >
          &larr; Dashboard
        </button>
        <div>
          <h1 class="text-lg font-bold text-[var(--color-text)] uppercase tracking-wider">Document Print</h1>
          <p class="text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest font-medium">Upload a PDF or image and print it — nothing is saved</p>
        </div>
      </div>
      <span class="hidden sm:inline text-xs text-[var(--color-text-muted)]">
        <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F2</kbd> Choose file
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">F8</kbd> Print
        <kbd class="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[var(--color-text)]">Esc</kbd> Back
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
            <option v-else-if="!printers.length" disabled value="">No printers found</option>
            <option v-for="p in printers" :key="p.name" :value="p.name">
              {{ p.printer_name || p.name }} — {{ p.status || 'Unknown' }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1 block text-[10px] uppercase tracking-wider font-bold text-[var(--color-text-muted)]">Copies</label>
          <input v-model.number="copies" type="number" min="1" :max="MAX_COPIES" :class="inputCls" />
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

const isPdf = computed(() => !!file.value && (file.value.type === 'application/pdf' || /\.pdf$/i.test(file.value.name)))
const canPrint = computed(() => !!file.value && !!selectedPrinter.value && !printing.value)

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
    // Uploads are always sent as PDF, so PDF-capable printers lead the list
    const isPdfPrinter = p => /pdf|a4|laser/i.test(p.printer_name || p.name)
    printers.value = [...pool.filter(isPdfPrinter), ...pool.filter(p => !isPdfPrinter(p))]

    const remembered = localStorage.getItem('wb-document-printer')
    if (remembered && printers.value.some(p => p.name === remembered)) {
      selectedPrinter.value = remembered
    } else if (!printers.value.some(p => p.name === selectedPrinter.value)) {
      selectedPrinter.value = (printers.value.find(isPdfPrinter) || printers.value.find(p => p.is_default) || printers.value[0])?.name || ''
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
    const body = new FormData()
    body.append('file', file.value, file.value.name)
    body.append('printer', selectedPrinter.value)
    body.append('copies', String(Math.max(1, Math.min(Number(copies.value) || 1, MAX_COPIES))))

    const res = await fetch('/api/method/ssplbilling.api.document_print_api.print_uploaded_file', {
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
      throw new Error(msg)
    }
    const r = data.message || {}
    try { localStorage.setItem('wb-document-printer', selectedPrinter.value) } catch { /* ignore */ }
    success.value = `Sent ${r.copies || 1} cop${(r.copies || 1) === 1 ? 'y' : 'ies'} to ${r.printer || selectedPrinter.value}${r.cups_job_id ? ` — Job ${r.cups_job_id}` : ''}`
  } catch (e) {
    error.value = e.message || 'Print failed'
  } finally {
    printing.value = false
  }
}

function onKey(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    router.push('/')
  } else if (e.key === 'F2') {
    e.preventDefault()
    fileInput.value?.click()
  } else if (e.key === 'F8') {
    e.preventDefault()
    sendPrint()
  }
}

onMounted(() => {
  loadPrinters()
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>
