<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)]">

    <!-- ── TOP BAR ───────────────────────────────────────────────── -->
    <header class="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shadow-sm shrink-0">
      <div class="flex items-center gap-3">
        <button class="rounded px-2 py-1 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition" @click="router.push('/')">&larr; Dashboard</button>
        <span class="text-sm text-[var(--color-text-muted)]">|</span>
        <span class="text-sm font-bold text-[var(--color-text)] uppercase tracking-tight">Customer Enquiry</span>
        <span v-if="docName" class="rounded bg-[var(--color-surface-raised)] px-2 py-0.5 font-mono text-xs text-[var(--color-info)]">{{ docName }}</span>
      </div>
      <div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Ctrl+S</kbd> Save</span>
        <span><kbd class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1 py-0.5 font-mono text-[10px] text-[var(--color-text)]">Esc</kbd> Back</span>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">

      <!-- ── LEFT: ENQUIRY FORM ──────────────────────────────────── -->
      <aside class="flex w-[38%] min-w-[420px] shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto">
        <div class="p-4 flex flex-col gap-4">

          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold uppercase tracking-wide text-[var(--color-text)]">{{ docName ? 'Edit Enquiry' : 'New Enquiry' }}</h2>
            <button
              v-if="docName || rows.length || form.customer || form.new_customer"
              class="rounded border border-[var(--color-border)] px-3 py-1 text-xs font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition"
              @click="clearForm"
            >+ New</button>
          </div>

          <!-- Date + Cost Center -->
          <div class="grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-1">
              <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Enquiry Date</label>
              <input
                v-model="form.enquiry_date"
                type="date"
                class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-lg font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] tabular-nums"
              />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Cost Center</label>
              <input
                :value="form.cost_center || 'None'"
                type="text"
                class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-lg font-bold text-[var(--color-text)] outline-none opacity-80"
                readonly
                disabled
              />
            </div>
          </div>

          <!-- Customer -->
          <div class="flex flex-col gap-1 relative">
            <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Customer Name</label>
            <div class="flex gap-2">
              <input
                ref="customerInputRef"
                v-model="customerQuery"
                type="text"
                placeholder="Type name or search customer..."
                class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-1.5 py-1 text-3xl font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)] uppercase"
                @input="onCustomerInput"
                @focus="onCustomerFocus"
                @keydown="handleCustomerKeydown"
              />
              <button
                v-if="form.customer || customerQuery"
                class="rounded border border-[var(--color-border)] px-3 text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition"
                title="Clear customer"
                @click="clearCustomer"
              >&times;</button>
            </div>

            <!-- Quick Ledger Search Dropdown -->
            <QuickLedgerSearch
              ref="quickSearchRef"
              v-if="showQuickSearch && searchResults.length"
              :results="searchResults"
              :query="customerQuery"
              :anchor-el="customerInputRef"
              @select="onCustomerSelected"
              @close="showQuickSearch = false"
            />
          </div>

          <!-- Mobile -->
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">
              Mobile Number
              <span v-if="mobileFromCache" class="normal-case font-normal text-[var(--color-success)]">(from customer cache)</span>
            </label>
            <input
              v-model="form.mobile_no"
              type="text"
              placeholder="Mobile number..."
              class="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-2xl font-mono font-bold text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
              @input="mobileFromCache = false"
            />
          </div>

          <!-- Items -->
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold uppercase text-[var(--color-text-muted)]">Enquired Items</label>
            <div class="rounded border border-[var(--color-border)] overflow-visible">
              <table class="w-full text-lg border-collapse">
                <thead>
                  <tr class="bg-[var(--color-surface-raised)]">
                    <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] w-[45%]">Item</th>
                    <th class="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Description</th>
                    <th class="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in rows" :key="idx" class="border-t border-[var(--color-border)]">
                    <td class="px-4 py-3">
                      <div class="font-bold text-[var(--color-text)]">{{ row.item_name }}</div>
                      <div v-if="row.is_new_item" class="text-xs font-bold uppercase text-[var(--color-warning,#f59e0b)]">New item</div>
                      <div v-else-if="row.item_code" class="font-mono text-xs text-[var(--color-text-muted)]">{{ row.item_code }}</div>
                    </td>
                    <td class="px-4 py-3">
                      <input
                        v-model="row.description"
                        type="text"
                        placeholder="Details..."
                        class="w-full bg-transparent text-[var(--color-text)] outline-none border-b border-transparent focus:border-[var(--color-info)]"
                      />
                    </td>
                    <td class="px-3 text-center">
                      <button class="text-2xl text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition" @click="rows.splice(idx, 1)">&times;</button>
                    </td>
                  </tr>

                  <!-- New item row -->
                  <tr class="border-t border-[var(--color-border)] bg-[var(--color-info)]/5">
                    <td class="px-4 py-3 relative">
                      <input
                        ref="newItemInput"
                        v-model="newItem.query"
                        type="text"
                        placeholder="Type item name..."
                        class="w-full bg-transparent text-[var(--color-text)] outline-none"
                        @input="onItemSearch"
                        @focus="showQuickItemSearch = true"
                        @keydown="handleItemInputKeydown"
                      />
                      
                      <QuickItemSearch
                        ref="quickItemSearchRef"
                        v-if="showQuickItemSearch && itemResults.length"
                        :results="itemResults"
                        :query="newItem.query"
                        :anchor-el="newItemInput"
                        @select="pickItem"
                        @close="showQuickItemSearch = false"
                      />
                    </td>
                    <td class="px-4 py-3">
                      <input
                        ref="newDescInput"
                        v-model="newItem.description"
                        type="text"
                        placeholder="Description (esp. for new items)..."
                        class="w-full bg-transparent text-[var(--color-text)] outline-none"
                        @keydown.enter.prevent="commitNewItem"
                      />
                    </td>
                    <td class="px-3 text-center">
                      <button class="text-2xl font-bold text-[var(--color-info)]" title="Add item" @click="commitNewItem">+</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-[10px] text-[var(--color-text-muted)]">Pick an item from the list, or press Enter on unmatched text to record it as a new item — add details in Description.</p>
          </div>

          <!-- Save -->
          <div class="flex gap-3">
            <button
              @click="saveEnquiry"
              :disabled="saving"
              class="flex-1 rounded-xl bg-[var(--color-info)] px-6 py-2.5 text-sm font-bold text-[var(--color-text-on-highlight)] shadow-lg hover:bg-[var(--color-info)] active:scale-95 transition-all disabled:bg-[var(--color-surface-raised)] disabled:text-[var(--color-text-muted)]"
            >{{ saving ? 'Saving...' : docName ? 'Update Enquiry' : 'Save Enquiry' }}</button>
            <button
              v-if="docName"
              @click="closeEnquiry(docName)"
              class="rounded-xl border border-[var(--color-border)] bg-[var(--color-success)]/10 px-6 py-2.5 text-sm font-bold text-[var(--color-success)] hover:bg-[var(--color-success)]/20 transition"
            >✓ Close Enquiry</button>
          </div>

        </div>
      </aside>

      <!-- ── RIGHT: ENQUIRY BOARD ────────────────────────────────── -->
      <div class="flex flex-1 flex-col overflow-hidden">

        <!-- Board toolbar -->
        <div class="flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 shrink-0">
          <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden">
            <button
              v-for="s in ['Open', 'Closed']"
              :key="s"
              class="px-4 py-1.5 text-xs font-bold uppercase tracking-wide transition"
              :class="viewStatus === s ? 'bg-[var(--color-info)] text-[var(--color-text-on-highlight)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)]'"
              @click="viewStatus = s"
            >{{ s }}</button>
          </div>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search name / mobile..."
            class="flex-1 max-w-xs rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-info)]"
          />
          <span class="ml-auto text-xs font-bold uppercase text-[var(--color-text-muted)]">{{ enquiries.length }} {{ viewStatus.toLowerCase() }} enquir{{ enquiries.length === 1 ? 'y' : 'ies' }}</span>
        </div>

        <!-- Cards -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="listLoading" class="flex items-center justify-center py-16 text-sm text-[var(--color-text-muted)]">Loading...</div>
          <div v-else-if="!enquiries.length" class="flex flex-col items-center justify-center py-16 gap-2">
            <span class="text-4xl">📞</span>
            <span class="text-sm italic text-[var(--color-text-muted)]">No {{ viewStatus.toLowerCase() }} enquiries</span>
          </div>
          <div v-else class="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-3">
            <div
              v-for="e in enquiries"
              :key="e.name"
              class="rounded-xl border bg-[var(--color-surface)] p-3 shadow-sm flex flex-col gap-2 transition"
              :class="docName === e.name ? 'border-[var(--color-info)] ring-1 ring-[var(--color-info)]' : 'border-[var(--color-border)]'"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="truncate text-lg font-bold text-[var(--color-text)]">
                    {{ e.customer_name || e.new_customer || e.customer }}
                    <span v-if="!e.customer" class="ml-1 rounded bg-[var(--color-warning,#f59e0b)]/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-[var(--color-warning,#f59e0b)] align-middle">New Customer</span>
                  </div>
                  <div class="font-mono text-sm text-[var(--color-text-muted)]">{{ e.mobile_no || 'No mobile' }}</div>
                </div>
                <div class="text-right shrink-0">
                  <div class="font-mono text-[10px] text-[var(--color-text-muted)]">{{ e.name }}</div>
                  <div class="text-xs font-bold tabular-nums text-[var(--color-text)]">{{ e.enquiry_date }}</div>
                  <div v-if="e.cost_center" class="text-[10px] font-bold text-[var(--color-info)]">{{ e.cost_center }}</div>
                </div>
              </div>

              <ul class="flex flex-col gap-1 border-t border-[var(--color-border)] pt-2">
                <li v-for="(it, i) in e.items" :key="i" class="flex items-baseline gap-2 text-sm">
                  <span class="text-[var(--color-info)]">▸</span>
                  <span class="font-semibold text-[var(--color-text)]">{{ it.item_name }}</span>
                  <span v-if="it.is_new_item" class="rounded bg-[var(--color-warning,#f59e0b)]/15 px-1 text-[9px] font-bold uppercase text-[var(--color-warning,#f59e0b)]">new</span>
                  <span v-if="it.description" class="truncate text-xs text-[var(--color-text-muted)]">— {{ it.description }}</span>
                </li>
              </ul>

              <div class="mt-auto flex gap-2 pt-1">
                <template v-if="e.status === 'Open'">
                  <button
                    class="flex-1 rounded-lg bg-[var(--color-success)]/10 px-3 py-1.5 text-xs font-bold text-[var(--color-success)] hover:bg-[var(--color-success)]/20 transition"
                    @click="closeEnquiry(e.name)"
                  >✓ Close</button>
                  <button
                    class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-bold text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] transition"
                    @click="loadEnquiry(e.name)"
                  >Edit</button>
                </template>
                <template v-else>
                  <span class="flex-1 px-3 py-1.5 text-[10px] font-bold uppercase text-[var(--color-text-muted)]">Closed {{ e.closed_on ? e.closed_on.split('.')[0] : '' }}</span>
                  <button
                    class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs font-bold text-[var(--color-info)] hover:bg-[var(--color-surface-raised)] transition"
                    @click="reopenEnquiry(e.name)"
                  >↺ Reopen</button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>



  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappePost } from '../api.js'
import QuickLedgerSearch from '../components/QuickLedgerSearch.vue'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { searchItemsInCache } from '../services/itemCache.js'
import { useLedgerCache, searchLedgersInCache } from '../services/ledgerCache.js'

const router = useRouter()
const API = 'ssplbilling.api.enquiry_api'
const today = new Date().toISOString().split('T')[0]

// ── COST CENTERS (from localStorage, synced by Dashboard) ───────────
let localCostCenters = []
try { localCostCenters = JSON.parse(localStorage.getItem('wb-cost-centers') || '[]') } catch { localCostCenters = [] }
const defaultCostCenter = localStorage.getItem('wb-cost-center') || ''
if (defaultCostCenter && !localCostCenters.includes(defaultCostCenter)) localCostCenters.unshift(defaultCostCenter)
const costCenters = ref(localCostCenters)

// ── FORM STATE ───────────────────────────────────────────────────────
function blankForm() {
  return { enquiry_date: today, cost_center: defaultCostCenter, customer: '', customer_name: '', new_customer: '', mobile_no: '' }
}
const form = ref(blankForm())
const rows = ref([])
const docName = ref(null)
const saving = ref(false)
const mobileFromCache = ref(false)
const customerQuery = ref('')
const showQuickSearch = ref(false)
const searchResults = ref([])
const customerInputRef = ref(null)
const quickSearchRef = ref(null)
const { refreshLedgerCache } = useLedgerCache()

const showQuickItemSearch = ref(false)
const quickItemSearchRef = ref(null)

// ── CUSTOMER ─────────────────────────────────────────────────────────
function searchCustomers() {
  const q = customerQuery.value.trim()
  if (!q) {
    searchResults.value = []
    showQuickSearch.value = false
    return
  }
  try {
    searchResults.value = searchLedgersInCache(q, 'Customer')
    showQuickSearch.value = true
  } catch (e) {
    console.warn('[CustomerEnquiry] searchCustomers failed:', e)
    searchResults.value = []
  }
}

function onCustomerInput() {
  if (form.value.customer) {
    form.value.customer = ''
    form.value.customer_name = ''
    mobileFromCache.value = false
  }
  const upperVal = customerQuery.value.toUpperCase()
  customerQuery.value = upperVal
  form.value.new_customer = upperVal.trim()
  form.value.customer_name = upperVal.trim()
  searchCustomers()
}

function onCustomerFocus() {
  showQuickSearch.value = true
  searchCustomers()
}

function handleCustomerKeydown(e) {
  if (e.key === 'Escape') {
    if (showQuickSearch.value) {
      e.preventDefault()
      e.stopPropagation()
      showQuickSearch.value = false
    }
  } else if (e.key === 'Enter') {
    if (showQuickSearch.value && searchResults.value.length > 0 && quickSearchRef.value) {
      quickSearchRef.value.handleKeydown(e)
    }
  } else if (showQuickSearch.value && quickSearchRef.value) {
    quickSearchRef.value.handleKeydown(e)
  }
}

function onCustomerSelected(c) {
  if (!c) return
  form.value.customer = c.name
  const upperName = (c.label || c.customer_name || c.name).toUpperCase()
  form.value.customer_name = upperName
  customerQuery.value = upperName
  form.value.new_customer = ''
  // Mobile number comes straight from the local customer cache
  form.value.mobile_no = c.mobile_no || ''
  mobileFromCache.value = !!c.mobile_no
  showQuickSearch.value = false
  nextTick(() => newItemInput.value?.focus())
}

function clearCustomer() {
  form.value.customer = ''
  form.value.customer_name = ''
  form.value.new_customer = ''
  customerQuery.value = ''
  form.value.mobile_no = ''
  mobileFromCache.value = false
  showQuickSearch.value = false
}

// ── ITEM ENTRY (searches local item cache) ───────────────────────────
const newItem = ref({ query: '', description: '' })
const itemResults = ref([])
const itemHighlight = ref(0)
const newItemInput = ref(null)
const newDescInput = ref(null)
let pickedItem = null

function onItemSearch() {
  pickedItem = null
  itemHighlight.value = 0
  if (newItem.value.query.trim().length >= 2) {
    itemResults.value = searchItemsInCache(newItem.value.query, 8)
    showQuickItemSearch.value = true
  } else {
    itemResults.value = []
    showQuickItemSearch.value = false
  }
}

function handleItemInputKeydown(e) {
  if (e.key === 'Escape') {
    if (showQuickItemSearch.value) {
      e.preventDefault()
      e.stopPropagation()
      showQuickItemSearch.value = false
    }
  } else if (e.key === 'Enter') {
    if (showQuickItemSearch.value && itemResults.value.length > 0 && quickItemSearchRef.value) {
      quickItemSearchRef.value.handleQuickSearchKeydown(e)
    } else if (newItem.value.query.trim()) {
      addTypedAsNewItem()
    }
  } else if (showQuickItemSearch.value && quickItemSearchRef.value) {
    quickItemSearchRef.value.handleQuickSearchKeydown(e)
  }
}

function pickItem(it) {
  pickedItem = it
  newItem.value.query = it.item_name || it.item_code
  newItem.value.description = it.item_name || ''
  itemResults.value = []
  showQuickItemSearch.value = false
  nextTick(() => newDescInput.value?.focus())
}

function addTypedAsNewItem() {
  pickedItem = null
  newItem.value.description = ''
  itemResults.value = []
  showQuickItemSearch.value = false
  nextTick(() => newDescInput.value?.focus())
}

function commitNewItem() {
  const text = newItem.value.query.trim()
  if (!text) return
  rows.value.push({
    item_code: pickedItem ? pickedItem.item_code : '',
    item_name: pickedItem ? (pickedItem.item_name || pickedItem.item_code) : text,
    is_new_item: pickedItem ? 0 : 1,
    description: newItem.value.description.trim(),
  })
  newItem.value = { query: '', description: '' }
  pickedItem = null
  itemResults.value = []
  showQuickItemSearch.value = false
  nextTick(() => newItemInput.value?.focus())
}

// ── SAVE / LOAD / CLEAR ──────────────────────────────────────────────
async function saveEnquiry() {
  // Commit any half-typed item row before validating
  if (newItem.value.query.trim()) commitNewItem()
  
  const finalCustomerName = form.value.customer ? form.value.customer_name : customerQuery.value.trim()
  if (!form.value.customer && !finalCustomerName) {
    alert('Select a customer or enter a customer name')
    return
  }
  if (!rows.value.length) { alert('Add at least one enquired item'); return }

  const upperFinalName = finalCustomerName.toUpperCase()
  if (!form.value.customer) {
    form.value.new_customer = upperFinalName
    form.value.customer_name = upperFinalName
  } else {
    form.value.customer_name = upperFinalName
    form.value.new_customer = ''
  }

  saving.value = true
  try {
    const payload = {
      name: docName.value,
      ...form.value,
      customer_name: form.value.customer ? form.value.customer_name : form.value.new_customer,
      items: rows.value,
    }
    const method = docName.value ? 'update_enquiry' : 'create_enquiry'
    const res = await frappePost(`${API}.${method}`, { data: JSON.stringify(payload) })
    docName.value = res.name
    await fetchEnquiries()
    clearForm()
  } catch (e) {
    alert(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

function clearForm() {
  form.value = blankForm()
  customerQuery.value = ''
  rows.value = []
  docName.value = null
  mobileFromCache.value = false
  newItem.value = { query: '', description: '' }
  pickedItem = null
  itemResults.value = []
  showQuickSearch.value = false
  showQuickItemSearch.value = false
}

async function loadEnquiry(name) {
  try {
    const d = await frappePost(`${API}.get_enquiry`, { name })
    docName.value = d.name
    form.value = {
      enquiry_date: d.enquiry_date || today,
      cost_center: d.cost_center || '',
      customer: d.customer || '',
      customer_name: (d.customer_name || '').toUpperCase(),
      new_customer: (d.new_customer || '').toUpperCase(),
      mobile_no: d.mobile_no || '',
    }
    const val = d.customer ? (d.customer_name || d.customer) : (d.new_customer || d.customer_name || '')
    customerQuery.value = (val || '').toUpperCase()
    mobileFromCache.value = false
    rows.value = (d.items || []).map(r => ({ ...r }))
  } catch (e) {
    alert(e.message || 'Failed to load enquiry')
  }
}

// ── BOARD (open enquiries) ───────────────────────────────────────────
const enquiries = ref([])
const listLoading = ref(false)
const viewStatus = ref('Open')
const searchQuery = ref('')
let searchTimer = null

async function fetchEnquiries() {
  listLoading.value = true
  try {
    enquiries.value = await frappePost(`${API}.get_enquiries`, {
      status: viewStatus.value,
      query: searchQuery.value,
      cost_center: defaultCostCenter || null,
    })
  } catch {
    enquiries.value = []
  } finally {
    listLoading.value = false
  }
}

watch(viewStatus, fetchEnquiries)
watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchEnquiries, 300)
})

async function closeEnquiry(name) {
  if (!confirm('Close this enquiry? It will disappear from the open list.')) return
  try {
    await frappePost(`${API}.close_enquiry`, { name })
    if (docName.value === name) clearForm()
    await fetchEnquiries()
  } catch (e) {
    alert(e.message || 'Failed to close enquiry')
  }
}

async function reopenEnquiry(name) {
  try {
    await frappePost(`${API}.reopen_enquiry`, { name })
    await fetchEnquiries()
  } catch (e) {
    alert(e.message || 'Failed to reopen enquiry')
  }
}

// ── KEYBOARD SHORTCUTS ───────────────────────────────────────────────
function onKeydown(e) {
  if (showQuickSearch.value || showQuickItemSearch.value) return
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveEnquiry() }
  if (e.key === 'Escape') { router.push('/') }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  fetchEnquiries()
  refreshLedgerCache(false).catch(e => console.error('[CustomerEnquiry] Cache sync failed', e))
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
