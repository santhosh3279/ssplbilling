<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px] overflow-hidden offer-display-page">
    
    <!-- ── HEADER ────────────────────────────────────────────────── -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition"
          >
            ← Dashboard
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Offer Items Management
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleNewOffer"
            class="rounded bg-[var(--color-success)] px-4 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-sm"
          >
            + New Offer List
          </button>
          <button
            @click="fetchOffers"
            :disabled="loading"
            class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-semibold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
          >
            {{ loading ? 'Loading...' : '🔄 Refresh List' }}
          </button>
        </div>
      </div>
    </header>

    <!-- ── MAIN BODY: SPLIT VIEW ─────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">
      
      <!-- ── LEFT COLUMN: OFFERS LIST (35%) ── -->
      <aside class="w-[35%] flex flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <!-- Search bar -->
        <div class="p-3 border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface)]/50">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search offers by heading or address..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition"
          />
        </div>

        <!-- Offers List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="loading && !offers.length" class="flex h-32 items-center justify-center">
            <span class="text-xs text-[var(--color-text-muted)] animate-pulse">Loading offer lists...</span>
          </div>
          <div v-else-if="!filteredOffers.length" class="flex h-32 items-center justify-center">
            <span class="text-xs italic text-[var(--color-text-muted)]">No offer lists found</span>
          </div>
          <div v-else class="divide-y divide-[var(--color-border)]/50">
            <div
              v-for="offer in filteredOffers"
              :key="offer.name"
              @click="selectOffer(offer.name)"
              class="p-4 cursor-pointer hover:bg-[var(--color-surface-raised)]/40 transition-colors flex flex-col gap-2 relative"
              :class="{
                'bg-[var(--color-info)]/10 border-l-4 border-[var(--color-info)]': selectedName === offer.name
              }"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="font-bold text-[14px] text-[var(--color-text)] truncate" :title="offer.heading">
                  {{ offer.heading }}
                </div>
              </div>

              <!-- Page Address & Info -->
              <div class="text-[11px] text-[var(--color-text-muted)] flex flex-wrap items-center gap-x-2 gap-y-1">
                <span>Address: <strong class="text-[var(--color-text)]">{{ offer.pageaddress }}</strong></span>
                <span>•</span>
                <span>ID: <span class="font-mono text-[var(--color-text-muted)]">{{ offer.name }}</span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer status -->
        <div class="p-3 border-t border-[var(--color-border)] shrink-0 bg-[var(--color-surface)] text-center text-xs text-[var(--color-text-muted)]">
          <strong>{{ filteredOffers.length }}</strong> lists shown (Total: {{ offers.length }})
        </div>
      </aside>

      <!-- ── RIGHT COLUMN: FORM / DETAILS (65%) ── -->
      <main class="w-[65%] flex flex-col bg-[var(--color-bg)] overflow-hidden">
        <!-- Loading overlay for details -->
        <div v-if="detailLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent mb-2"></span>
            <div class="text-xs text-[var(--color-text-muted)]">Loading offer details...</div>
          </div>
        </div>

        <div v-else-if="!isFormActive" class="flex-1 flex flex-col items-center justify-center p-8 text-center text-[var(--color-text-muted)]">
          <span class="text-5xl mb-4">🏷️</span>
          <h2 class="text-base font-bold text-[var(--color-text)] mb-1">Offer Display Management</h2>
          <p class="max-w-md text-xs leading-relaxed mb-4">
            Select an offer list from the left panel to edit its details and items, or click the button below to create a new one.
          </p>
          <button
            @click="handleNewOffer"
            class="rounded bg-[var(--color-success)] px-5 py-2 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-md"
          >
            + Create New Offer List
          </button>
        </div>

        <!-- FORM PANEL -->
        <div v-else class="flex-1 flex flex-col overflow-hidden">
          <!-- Form Header -->
          <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0">
            <div>
              <h2 class="text-[14px] font-bold text-[var(--color-text)]">
                {{ form.name ? 'Edit Offer List' : 'New Offer List' }}
              </h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-mono truncate max-w-sm mt-0.5">
                {{ form.name || 'Draft document' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="form.name"
                @click="handleDeleteOffer"
                :disabled="saving"
                class="rounded border border-red-300 text-red-600 bg-red-50 px-3 py-1.5 text-xs font-bold hover:bg-red-100 disabled:opacity-50 transition"
              >
                🗑 Delete List
              </button>
              <button
                @click="closeForm"
                class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-xs font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
              >
                Cancel
              </button>
              <button
                @click="handleSave"
                :disabled="saving"
                class="rounded bg-[var(--color-info)] px-5 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-info)]/90 disabled:opacity-50 transition shadow"
              >
                {{ saving ? 'Saving...' : 'Save Offer List' }}
              </button>
            </div>
          </div>

          <!-- Form Fields Wrapper -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Basic Info Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Offer Information
              </h3>
              
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Heading -->
                <div class="flex flex-col gap-1.5 md:col-span-2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Heading <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.heading"
                    type="text"
                    placeholder="Enter offer display heading"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>

                <!-- Page Address -->
                <div class="flex flex-col gap-1.5 md:col-span-2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Page Address <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.pageaddress"
                    type="text"
                    placeholder="Enter unique page address"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition font-mono"
                    :disabled="!!form.name"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5" v-if="!form.name">
                    This will be used as the unique ID for this document.
                  </p>
                </div>

                <!-- Tile Grid -->
                <div class="flex flex-col gap-1.5 md:col-span-2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Tile Grid <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <select
                    v-model="form.tile_grid"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="1">1 Column</option>
                    <option value="2">2 Columns</option>
                    <option value="4">4 Columns</option>
                    <option value="6">6 Columns</option>
                    <option value="9">9 Columns</option>
                  </select>
                </div>

                <!-- Timer -->
                <div class="flex flex-col gap-1.5 md:col-span-2">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)] block">
                    Timer (Seconds)
                  </label>
                  <input
                    v-model="form.timer"
                    type="number"
                    min="0"
                    placeholder="e.g. 30 (0 to disable auto-refresh)"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5">
                    Time in seconds to auto-refresh/reload offer details (0 to disable).
                  </p>
                </div>
              </div>
            </div>

            <!-- Items Table Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-1.5">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Offer Items ({{ form.items.length }})
                </h3>
                <button
                  @click="addEmptyRow"
                  type="button"
                  class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-[10px] font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
                >
                  + Add Empty Row
                </button>
              </div>
              
              <!-- Autocomplete Item Search Box -->
              <div class="relative max-w-md">
                <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)] block mb-1">
                  Add Item from Inventory
                </label>
                <input
                  v-model="itemSearchQuery"
                  @input="handleItemSearch"
                  @keydown.down.prevent="moveSearchSelection(1)"
                  @keydown.up.prevent="moveSearchSelection(-1)"
                  @keydown.enter.prevent="addSearchSelectedItem"
                  type="text"
                  placeholder="Type code, name, or barcode to add item..."
                  class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                />
                
                <!-- Search Results dropdown -->
                <div
                  v-if="searchSuggestions.length"
                  class="absolute z-50 left-0 right-0 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg divide-y divide-[var(--color-border)]/50"
                >
                  <div
                    v-for="(item, idx) in searchSuggestions"
                    :key="item.item_code"
                    @click="addItemToScope(item)"
                    class="p-2.5 cursor-pointer text-xs hover:bg-[var(--color-info)]/10 flex items-center justify-between"
                    :class="{'bg-[var(--color-info)]/15 font-bold': searchActiveIndex === idx}"
                  >
                    <div class="truncate pr-4 flex flex-col gap-0.5">
                      <div>
                        <span class="font-mono font-bold text-[var(--color-info)]">{{ item.item_code }}</span>
                        <span class="text-[var(--color-text-muted)] ml-2">— {{ item.item_name }}</span>
                      </div>
                      <div class="text-[10px] text-[var(--color-text-muted)]" v-if="item.barcodes">
                        Barcodes: {{ item.barcodes }}
                      </div>
                    </div>
                    <span class="text-[10px] text-gray-500 font-mono shrink-0">{{ item.uom || 'Nos' }}</span>
                  </div>
                </div>
              </div>

              <!-- Offer Items Table -->
              <div class="border border-[var(--color-border)] rounded-lg overflow-hidden">
                <table class="w-full text-left">
                  <thead>
                    <tr class="bg-[var(--color-surface-raised)] text-[10px] uppercase font-bold text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                      <th class="p-2 w-[10%] text-center">#</th>
                      <th class="p-2 w-[30%]">Item Code</th>
                      <th class="p-2 w-[35%]">Item Name</th>
                      <th class="p-2 w-[20%]">Barcode</th>
                      <th class="p-2 w-[5%] text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[var(--color-border)]">
                    <tr v-if="!form.items.length">
                      <td colspan="5" class="p-6 text-center text-xs text-[var(--color-text-muted)] italic">
                        No items added to this offer list. Use the search bar above or add an empty row.
                      </td>
                    </tr>
                    <tr v-for="(item, idx) in form.items" :key="idx" class="text-xs hover:bg-[var(--color-surface-raised)]/20">
                      <!-- Row Number -->
                      <td class="p-2 text-center text-[var(--color-text-muted)] font-mono">
                        {{ idx + 1 }}
                      </td>
                      
                      <!-- Item Code -->
                      <td class="p-1.5">
                        <input
                          v-model="item.itemcode"
                          type="text"
                          placeholder="e.g. ITEM-001"
                          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition font-mono"
                        />
                      </td>

                      <!-- Item Name -->
                      <td class="p-1.5">
                        <input
                          v-model="item.itemname"
                          type="text"
                          placeholder="e.g. Premium Item Name"
                          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition"
                        />
                      </td>

                      <!-- Barcode -->
                      <td class="p-1.5">
                        <input
                          v-model="item.barcode"
                          type="text"
                          placeholder="e.g. 12345678"
                          class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 outline-none focus:border-[var(--color-info)] transition font-mono"
                        />
                      </td>

                      <!-- Actions -->
                      <td class="p-1.5 text-center">
                        <button
                          @click="removeItemRow(idx)"
                          class="text-red-500 hover:text-red-700 font-bold px-2 py-1 text-sm transition"
                          title="Remove item"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { frappeGet, frappePost } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { searchItemsInCache } = useItemCache()

// State
const offers = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedName = ref(null)
const detailLoading = ref(false)
const saving = ref(false)

// Form structure
const emptyForm = () => ({
  name: null,
  modified: null,
  creation: null,
  owner: null,
  heading: '',
  pageaddress: '',
  tile_grid: '4',
  timer: 0,
  items: []
})

const form = ref(emptyForm())
const isFormActive = ref(false)

// Item autocomplete search state
const itemSearchQuery = ref('')
const searchSuggestions = ref([])
const searchActiveIndex = ref(-1)

// Fetch all Offer-Items documents from the database
async function fetchOffers() {
  loading.value = true
  try {
    const data = await frappeGet('frappe.client.get_list', {
      doctype: 'Offer-Items',
      fields: ['name', 'heading', 'pageaddress', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 100
    })
    offers.value = data || []
  } catch (e) {
    alert(e.message || 'Failed to fetch offer lists')
  } finally {
    loading.value = false
  }
}

// Filter offer lists in sidebar
const filteredOffers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return offers.value
  return offers.value.filter(o =>
    (o.heading || '').toLowerCase().includes(q) ||
    (o.pageaddress || '').toLowerCase().includes(q) ||
    (o.name || '').toLowerCase().includes(q)
  )
})

// Select an offer list and load it details including the items child table
async function selectOffer(name) {
  selectedName.value = name
  detailLoading.value = true
  isFormActive.value = true
  itemSearchQuery.value = ''
  searchSuggestions.value = []
  
  try {
    const doc = await frappeGet('frappe.client.get', {
      doctype: 'Offer-Items',
      name: name
    })
    form.value = {
      name: doc.name,
      modified: doc.modified,
      creation: doc.creation,
      owner: doc.owner,
      heading: doc.heading || '',
      pageaddress: doc.pageaddress || '',
      tile_grid: doc.tile_grid || '4',
      timer: doc.timer || 0,
      items: (doc.items || []).map(i => ({
        name: i.name,
        itemcode: i.itemcode || '',
        itemname: i.itemname || '',
        barcode: i.barcode || ''
      }))
    }
  } catch (e) {
    alert(e.message || 'Failed to load offer details')
    closeForm()
  } finally {
    detailLoading.value = false
  }
}

// Open clean form for creating new Offer List
function handleNewOffer() {
  selectedName.value = null
  isFormActive.value = true
  form.value = emptyForm()
  itemSearchQuery.value = ''
  searchSuggestions.value = []
}

function closeForm() {
  isFormActive.value = false
  selectedName.value = null
  form.value = emptyForm()
}

// Item autocomplete search
function handleItemSearch() {
  const q = itemSearchQuery.value.trim()
  if (!q || q.length < 2) {
    searchSuggestions.value = []
    searchActiveIndex.value = -1
    return
  }
  
  // Quick search in local cached items index
  const found = searchItemsInCache(q, 10)
  
  searchSuggestions.value = found
  searchActiveIndex.value = searchSuggestions.value.length ? 0 : -1
}

// Handle keyboard selections in item autocomplete list
function moveSearchSelection(dir) {
  if (!searchSuggestions.value.length) return
  const len = searchSuggestions.value.length
  searchActiveIndex.value = (searchActiveIndex.value + dir + len) % len
}

function addSearchSelectedItem() {
  if (searchActiveIndex.value >= 0 && searchActiveIndex.value < searchSuggestions.value.length) {
    addItemToScope(searchSuggestions.value[searchActiveIndex.value])
  }
}

function addItemToScope(item) {
  // Extract barcode if any
  let itemBarcode = ''
  if (item.barcodes_detailed?.length) {
    itemBarcode = item.barcodes_detailed[0].barcode || ''
  } else if (item.barcodes) {
    itemBarcode = item.barcodes.split(',')[0] || ''
  }

  form.value.items.push({
    itemcode: item.item_code,
    itemname: item.item_name || '',
    barcode: itemBarcode
  })
  
  // Reset search
  itemSearchQuery.value = ''
  searchSuggestions.value = []
  searchActiveIndex.value = -1
}

function addEmptyRow() {
  form.value.items.push({
    itemcode: '',
    itemname: '',
    barcode: ''
  })
}

function removeItemRow(idx) {
  form.value.items.splice(idx, 1)
}

// Save the Offer-Items document
async function handleSave() {
  if (!form.value.heading.trim()) {
    alert('Please enter a Heading.')
    return
  }
  if (!form.value.pageaddress.trim()) {
    alert('Please enter a Page Address.')
    return
  }
  if (!form.value.items.length) {
    alert('Please add at least one Item to the offer list.')
    return
  }

  // Validate items
  for (let i = 0; i < form.value.items.length; i++) {
    const item = form.value.items[i]
    if (!item.itemcode.trim()) {
      alert(`Row ${i + 1}: Item Code is required.`)
      return
    }
  }

  saving.value = true
  try {
    let res
    const isNew = !form.value.name
    
    const docPayload = {
      doctype: 'Offer-Items',
      heading: form.value.heading.trim(),
      pageaddress: form.value.pageaddress.trim(),
      tile_grid: form.value.tile_grid,
      timer: parseInt(form.value.timer) || 0,
      ...(form.value.modified && { modified: form.value.modified }),
      ...(form.value.creation && { creation: form.value.creation }),
      ...(form.value.owner && { owner: form.value.owner }),
      items: form.value.items.map(i => ({
        ...(i.name && { name: i.name }),
        doctype: 'Offer-Item',
        itemcode: i.itemcode.trim(),
        itemname: i.itemname.trim(),
        barcode: i.barcode.trim()
      }))
    }

    if (isNew) {
      // Set name to pageaddress if autonamed by pageaddress or name field
      docPayload.name = form.value.pageaddress.trim()
      res = await frappePost('frappe.client.insert', { doc: docPayload })
    } else {
      docPayload.name = form.value.name
      res = await frappePost('frappe.client.save', { doc: docPayload })
    }

    alert('Offer list saved successfully!')
    await fetchOffers()
    if (res && res.name) {
      await selectOffer(res.name)
    } else {
      closeForm()
    }
  } catch (e) {
    alert(e.message || 'Failed to save offer list')
  } finally {
    saving.value = false
  }
}

// Delete the selected Offer List
async function handleDeleteOffer() {
  if (!form.value.name) return
  if (!confirm(`Are you sure you want to delete offer list "${form.value.heading}"?`)) return

  saving.value = true
  try {
    await frappePost('frappe.client.delete', {
      doctype: 'Offer-Items',
      name: form.value.name
    })
    alert('Offer list deleted successfully!')
    closeForm()
    await fetchOffers()
  } catch (e) {
    alert(e.message || 'Failed to delete offer list')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchOffers()
})
</script>

<style scoped>
.offer-display-page {
  /* Utilizing core styling variables */
}
</style>
