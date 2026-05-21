<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm"
  >
    <div class="flex h-[90vh] w-[80vw] flex-col rounded-2xl bg-[var(--color-bg)] border border-[var(--color-border)] shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="border-b border-[var(--color-border)] px-6 py-4 flex items-center justify-between bg-[var(--color-surface)]">
        <div>
          <div class="text-xl font-bold text-[var(--color-text)]">Barcode Printing</div>
          <div class="flex items-center gap-3 mt-0.5">
            <span class="text-xs text-[var(--color-text-muted)]">Manage items and quantities to print</span>
            <span v-if="billNo" class="rounded bg-[var(--color-surface-raised)] px-2 py-0.5 text-xs font-bold text-[var(--color-info)]">
              Bill: {{ billNo }}
            </span>
          </div>
        </div>
        <button @click="$emit('close')" :disabled="printing" class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] disabled:opacity-40">✕</button>
      </div>

      <div class="flex-1 flex flex-col p-6 gap-5 overflow-hidden">

        <!-- Printer & Template Row -->
        <div class="flex gap-4">
          <!-- Printer Select -->
          <div class="flex flex-col gap-1.5 flex-1">
            <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Printer</label>
            <div class="relative">
              <select
                v-model="selectedPrinter"
                class="w-full appearance-none rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)] disabled:opacity-50"
                :disabled="loadingResources || printing"
              >
                <option value="">— Select Printer —</option>
                <option v-for="p in printers" :key="p.name" :value="p.name">
                  {{ p.printer_name }}{{ p.is_default ? ' ★' : '' }}
                </option>
              </select>
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">▾</span>
            </div>
            <span v-if="!printers.length && !loadingResources" class="text-[10px] text-[var(--color-danger)]">No printers configured</span>
          </div>

          <!-- Template Select -->
          <div class="flex flex-col gap-1.5 flex-1">
            <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Print Template</label>
            <div class="relative">
              <select
                v-model="selectedTemplate"
                class="w-full appearance-none rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)] disabled:opacity-50"
                :disabled="loadingResources || printing"
              >
                <option value="">— Select Template —</option>
                <option v-for="t in templates" :key="t.name" :value="t.name">
                  {{ t.template_name }}
                </option>
              </select>
              <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">▾</span>
            </div>
            <span v-if="!templates.length && !loadingResources" class="text-[10px] text-[var(--color-danger)]">No Barcode templates found</span>
          </div>

          <div v-if="loadingResources" class="flex items-end pb-2 text-xs text-[var(--color-text-muted)] italic">
            Loading…
          </div>
        </div>

        <!-- Item Search -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Add Item to List</label>
          <div class="relative">
            <input
              ref="itemInput"
              v-model="query"
              :disabled="printing"
              class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-lg text-[var(--color-text)] outline-none focus:border-[var(--color-info)] focus:ring-1 focus:ring-[var(--color-info)] disabled:opacity-50"
              placeholder="Start typing item code or name..."
              @keydown.down.prevent="moveSelection(1)"
              @keydown.up.prevent="moveSelection(-1)"
              @keydown.enter.prevent="handleEnter"
            />

            <!-- Search Results Dropdown -->
            <div v-if="showResults && results.length" class="absolute left-0 right-0 top-full z-20 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl custom-scrollbar">
              <div
                v-for="(item, idx) in results"
                :key="item.item_code"
                class="flex items-center justify-between border-b border-[var(--color-border)]/50 px-4 py-2.5 cursor-pointer hover:bg-[var(--color-surface-raised)]"
                :class="{ 'bg-[var(--color-surface-raised)]': selectedIdx === idx }"
                @click="selectItem(item)"
              >
                <div class="flex flex-col">
                  <span class="font-mono text-sm font-bold text-[var(--color-info)]">{{ item.item_code }}</span>
                  <span class="text-xs text-[var(--color-text)]">{{ item.item_name }}</span>
                </div>
                <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase">{{ item.uom }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Items Table -->
        <div class="flex-1 overflow-auto border border-[var(--color-border)] rounded-xl bg-[var(--color-surface)]/30">
          <table class="w-full border-collapse">
            <thead class="sticky top-0 z-10 bg-[var(--color-surface)] text-[10px] font-bold uppercase text-[var(--color-text-muted)]">
              <tr>
                <th class="px-4 py-3 text-left">Item Code</th>
                <th class="px-4 py-3 text-left">Item Name</th>
                <th class="px-4 py-3 text-left w-24">UOM</th>
                <th class="px-4 py-3 text-right w-32">Quantity</th>
                <th class="px-4 py-3 text-center w-16">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              <tr v-for="(item, idx) in itemsToPrint" :key="idx" class="hover:bg-[var(--color-surface-raised)]/30 transition-colors">
                <td class="px-4 py-3 font-mono text-sm text-[var(--color-info)]">{{ item.item_code }}</td>
                <td class="px-4 py-3 text-sm text-[var(--color-text)]">{{ item.item_name }}</td>
                <td class="px-4 py-3 text-sm text-[var(--color-text-muted)] font-mono">{{ item.uom || 'Nos' }}</td>
                <td class="px-4 py-3 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button :disabled="printing" @click="item.qty = Math.max(1, item.qty - 1)" class="h-8 w-8 rounded bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] disabled:opacity-40">&minus;</button>
                    <input
                      type="number"
                      v-model.number="item.qty"
                      min="1"
                      :disabled="printing"
                      class="h-8 w-16 rounded border border-[var(--color-border)] bg-[var(--color-bg)] text-center text-sm font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] disabled:opacity-40"
                    />
                    <button :disabled="printing" @click="item.qty++" class="h-8 w-8 rounded bg-[var(--color-surface-raised)] text-[var(--color-text)] hover:bg-[var(--color-surface-raised)] disabled:opacity-40">&plus;</button>
                  </div>
                </td>
                <td class="px-4 py-3 text-center">
                  <button :disabled="printing" @click="removeItem(idx)" class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors disabled:opacity-40">✕</button>
                </td>
              </tr>
              <tr v-if="!itemsToPrint.length">
                <td colspan="5" class="px-4 py-12 text-center text-[var(--color-text-muted)] italic">
                  No items added yet. Search and select items to print.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Status Banner -->
        <div
          v-if="statusMsg"
          class="rounded-lg px-4 py-2.5 text-sm font-bold text-center"
          :class="statusError ? 'bg-[var(--color-danger)]/60 text-[var(--color-danger)] border border-[var(--color-danger)]' : 'bg-[var(--color-success)]/60 text-[var(--color-success)] border border-[var(--color-success)]'"
        >
          {{ statusMsg }}
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-[var(--color-border)] bg-[var(--color-surface)]/50 px-6 py-4 flex items-center justify-between">
        <div class="flex gap-4">
          <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
            <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 text-[var(--color-text)] mr-1">ESC</kbd> Close
          </span>
          <span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
            <kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 text-[var(--color-text)] mr-1">ENTER</kbd> Print
          </span>
        </div>

        <div class="flex items-center gap-3">
          <button
            v-if="itemsToPrint.length && !printing"
            @click="itemsToPrint = []"
            class="px-4 py-2.5 text-sm font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
          >
            Clear All
          </button>
          <button
            @click="triggerPrint"
            :disabled="!canPrint || printing"
            class="min-w-[160px] rounded-xl bg-[var(--color-supplier)] px-8 py-2.5 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg transition-all hover:bg-[var(--color-supplier)] disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)] disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span v-if="printing" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            {{ printing ? 'Sending to Printer…' : 'Print Barcodes' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useItemCache } from '../services/itemCache.js'
import { frappeGet, frappePost } from '../api.js'
import { useSubwindowWatcher } from '../services/shortcutManager'

const props = defineProps({
  show: Boolean,
  billNo: String,
  initialItems: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'printed'])

useSubwindowWatcher(computed(() => props.show), { ESCAPE: () => emit('close') })

const { items: allItems, lookupItemInCache } = useItemCache()

// ── item search ─────────────────────────────────────────────────────────────
const query = ref('')
const selectedIdx = ref(0)
const itemsToPrint = ref([])
const showResults = ref(false)
const itemInput = ref(null)

// ── printer / template ───────────────────────────────────────────────────────
const printers = ref([])
const templates = ref([])
const selectedPrinter = ref('')
const selectedTemplate = ref('')
const loadingResources = ref(false)

// ── print state ───────────────────────────────────────────────────────────────
const printing = ref(false)
const statusMsg = ref('')
const statusError = ref(false)

function setStatus(msg, isError = false) {
  statusMsg.value = msg
  statusError.value = isError
  if (!isError) setTimeout(() => { statusMsg.value = '' }, 3000)
}

async function loadResources() {
  loadingResources.value = true
  try {
    const [p, t] = await Promise.all([
      frappeGet('printer_server_configuration.printer_server_configuration.api.get_printers'),
      frappeGet('frappe.client.get_list', {
        doctype: 'Print Template',
        filters: JSON.stringify({ document_type: 'Barcode_Prinitng', format_type: 'Barcode' }),
        fields: JSON.stringify(['name', 'template_name', 'format_type']),
        limit: 50,
      }),
    ])
    printers.value = p || []
    templates.value = t || []

    const userDefault = localStorage.getItem('wb-default-printer')
    if (userDefault && printers.value.some(pr => pr.name === userDefault)) {
      selectedPrinter.value = userDefault
    } else {
      const def = printers.value.find(pr => pr.is_default) || printers.value[0]
      if (def) selectedPrinter.value = def.name
    }

    if (templates.value.length === 1) selectedTemplate.value = templates.value[0].name
  } catch (e) {
    console.error('Failed to load barcode resources', e)
  } finally {
    loadingResources.value = false
  }
}

// ── computed ─────────────────────────────────────────────────────────────────
const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return allItems.value.filter(i =>
    (i.item_code || '').toLowerCase().includes(q) ||
    (i.item_name || '').toLowerCase().includes(q)
  ).slice(0, 10)
})

const canPrint = computed(() =>
  itemsToPrint.value.length > 0 && !!selectedPrinter.value && !!selectedTemplate.value
)

// ── watchers ─────────────────────────────────────────────────────────────────
watch(query, (val) => {
  showResults.value = val.length > 0
  selectedIdx.value = 0
})

watch(() => props.show, (val) => {
  if (val) {
    query.value = ''
    statusMsg.value = ''
    printing.value = false
    syncInitialItems()
    loadResources()
    nextTick(() => itemInput.value?.focus())
  }
})

// ── functions ────────────────────────────────────────────────────────────────
function moveSelection(dir) {
  if (!results.value.length) return
  selectedIdx.value = (selectedIdx.value + dir + results.value.length) % results.value.length
}

function handleEnter() {
  if (showResults.value && results.value[selectedIdx.value]) {
    selectItem(results.value[selectedIdx.value])
  } else if (canPrint.value && !query.value && !printing.value) {
    triggerPrint()
  }
}

async function triggerPrint() {
  if (!canPrint.value || printing.value) return

  printing.value = true
  statusMsg.value = ''

  try {
    // Step 1 — create Barcode_Prinitng doc entry
    const docName = await frappePost('ssplbilling.api.barcode_api.create_barcode_print_entry', {
      items: JSON.stringify(itemsToPrint.value),
      bill_no: props.billNo || null,
    })

    if (!docName) {
      setStatus('Failed to create barcode entry.', true)
      return
    }

    // Step 2 — send to printer (same as PrintOptionsModal.sendPrint)
    const res = await frappePost(
      'printer_server_configuration.printer_server_configuration.api.print_document',
      {
        printer:        selectedPrinter.value,
        print_template: selectedTemplate.value,
        document_type:  'Barcode_Prinitng',
        document_name:  docName,
        title:          docName,
      },
    )

    setStatus(`Sent to printer — Job ${res?.cups_job_id ?? ''}`)
    emit('printed', docName)
    setTimeout(() => emit('close'), 1500)
  } catch (e) {
    const msg = e?.message || e?.exc_type || 'Print failed. Check printer connection.'
    setStatus(msg, true)
    console.error('Barcode print error:', e)
  } finally {
    printing.value = false
  }
}

function selectItem(item) {
  const uom = item.uom || lookupItemInCache(item.item_code)?.uom || 'Nos'
  const existing = itemsToPrint.value.find(i => i.item_code === item.item_code)
  if (existing) {
    existing.qty++
    existing.uom = uom
  } else {
    itemsToPrint.value.push({ item_code: item.item_code, item_name: item.item_name, uom, qty: 1 })
  }
  query.value = ''
  showResults.value = false
  nextTick(() => itemInput.value?.focus())
}

function removeItem(idx) {
  itemsToPrint.value.splice(idx, 1)
}

function syncInitialItems() {
  itemsToPrint.value = (props.initialItems || []).map(i => ({
    item_code: i.item_code,
    item_name: i.item_name,
    uom: i.uom || lookupItemInCache(i.item_code)?.uom || 'Nos',
    qty: i.qty || 1
  }))
}
</script>
