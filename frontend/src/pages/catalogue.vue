<template>
  <div class="h-screen flex flex-col bg-[var(--color-bg)] font-sans text-[var(--color-text)] text-[13px] overflow-hidden catalogue-display-page">
    
    <!-- ── HEADER ────────────────────────────────────────────────── -->
    <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 shadow-sm shrink-0">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/catelogue')"
            class="flex items-center gap-1 rounded px-2 py-1 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-text)] transition"
          >
            ← Catalogue
          </button>
          <span class="text-[var(--color-text-muted)]">|</span>
          <h1 class="text-sm font-semibold text-[var(--color-text)]">
            Cataloge Mangement
          </h1>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="handleNewCatalogue"
            class="rounded bg-[var(--color-success)] px-4 py-1.5 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-sm"
          >
            + New Catalogue List
          </button>
          <button
            @click="fetchCatalogues"
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
      
      <!-- ── LEFT COLUMN: CATALOGUES LIST (17.5%) ── -->
      <aside class="w-[17.5%] flex flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
        <!-- Search bar -->
        <div class="p-3 border-b border-[var(--color-border)] shrink-0 bg-[var(--color-surface)]/50">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search catalogues by heading or address..."
            class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs text-[var(--color-text)] outline-none focus:border-[var(--color-info)] transition"
          />
        </div>

        <!-- Catalogues List -->
        <div class="flex-1 overflow-y-auto">
          <div v-if="loading && !catalogues.length" class="flex h-32 items-center justify-center">
            <span class="text-xs text-[var(--color-text-muted)] animate-pulse">Loading catalogue lists...</span>
          </div>
          <div v-else-if="!filteredCatalogues.length" class="flex h-32 items-center justify-center">
            <span class="text-xs italic text-[var(--color-text-muted)]">No catalogue lists found</span>
          </div>
          <div v-else class="divide-y divide-[var(--color-border)]/50">
            <div
              v-for="catalogue in filteredCatalogues"
              :key="catalogue.name"
              @click="selectCatalogue(catalogue.name)"
              class="p-4 cursor-pointer hover:bg-[var(--color-surface-raised)]/40 transition-colors flex flex-col gap-2 relative"
              :class="{
                'bg-[var(--color-info)]/10 border-l-4 border-[var(--color-info)]': selectedName === catalogue.name
              }"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="font-bold text-[14px] text-[var(--color-text)] truncate" :title="catalogue.heading">
                  {{ catalogue.heading }}
                </div>
              </div>

              <div class="text-[11px] text-[var(--color-text-muted)] flex flex-wrap items-center gap-x-2 gap-y-1">
                <span>Address: 
                  <a 
                    :href="`/catalogue/${catalogue.pageaddress}`"
                    target="_blank" 
                    class="text-[var(--color-info)] hover:underline font-mono"
                    @click.stop
                  >
                    /catalogue/{{ catalogue.pageaddress }}
                  </a>
                </span>
                <span>•</span>
                <span>ID: <span class="font-mono text-[var(--color-text-muted)]">{{ catalogue.name }}</span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer status -->
        <div class="p-3 border-t border-[var(--color-border)] shrink-0 bg-[var(--color-surface)] text-center text-xs text-[var(--color-text-muted)]">
          <strong>{{ filteredCatalogues.length }}</strong> lists shown (Total: {{ catalogues.length }})
        </div>
      </aside>

      <!-- ── RIGHT COLUMN: FORM / DETAILS (82.5%) ── -->
      <main class="w-[82.5%] flex flex-col bg-[var(--color-bg)] overflow-hidden">
        <!-- Loading overlay for details -->
        <div v-if="detailLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <span class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-info)] border-t-transparent mb-2"></span>
            <div class="text-xs text-[var(--color-text-muted)]">Loading catalogue details...</div>
          </div>
        </div>

        <div v-else-if="!isFormActive" class="flex-1 flex flex-col items-center justify-center p-8 text-center text-[var(--color-text-muted)]">
          <span class="text-5xl mb-4">🏷️</span>
          <h2 class="text-base font-bold text-[var(--color-text)] mb-1">Catalogue Display Management</h2>
          <p class="max-w-md text-xs leading-relaxed mb-4">
            Select a catalogue list from the left panel to edit its details and items, or click the button below to create a new one.
          </p>
          <button
            @click="handleNewCatalogue"
            class="rounded bg-[var(--color-success)] px-5 py-2 text-xs font-bold text-white hover:bg-[var(--color-success)]/90 transition shadow-md"
          >
            + Create New Catalogue List
          </button>
        </div>

        <!-- FORM PANEL -->
        <div v-else class="flex-1 flex flex-col overflow-hidden">
          <!-- Form Header -->
          <div class="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between shrink-0">
            <div>
              <h2 class="text-[14px] font-bold text-[var(--color-text)]">
                {{ form.name ? 'Edit Catalogue List' : 'New Catalogue List' }}
              </h2>
              <p class="text-[10px] text-[var(--color-text-muted)] font-mono truncate max-w-sm mt-0.5">
                {{ form.name || 'Draft document' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="form.name"
                @click="handleDeleteCatalogue"
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
                {{ saving ? 'Saving...' : 'Save Catalogue List' }}
              </button>
            </div>
          </div>

          <!-- Form Fields Wrapper -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Basic Info Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]/50 pb-1.5">
                Catalogue Information
              </h3>
              
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Heading -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Heading <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.heading"
                    type="text"
                    placeholder="Enter catalogue display heading"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                  />
                </div>

                <!-- Page Address -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
                  <label class="text-[11px] font-bold uppercase text-[var(--color-text-muted)]">
                    Page Address <span class="text-[var(--color-danger)]">*</span>
                  </label>
                  <input
                    v-model="form.pageaddress"
                    type="text"
                    placeholder="Enter unique page address"
                    class="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition font-mono"
                  />
                  <p class="text-[9px] text-[var(--color-text-muted)] mt-0.5" v-if="!form.name">
                    This will be used as the unique ID for this document.
                  </p>
                  <a
                    v-if="form.name"
                    :href="`/catalogue/${form.pageaddress}`"
                    target="_blank"
                    class="text-[10px] text-[var(--color-info)] hover:underline mt-1 font-mono inline-flex items-center gap-1 w-fit"
                  >
                    🔗 View Page: /catalogue/{{ form.pageaddress }}
                  </a>
                </div>

                <!-- Tile Grid -->
                <div class="flex flex-col gap-1.5 md:col-span-1">
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
                <div class="flex flex-col gap-1.5 md:col-span-1">
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
                    Time in seconds to auto-refresh/reload catalogue details (0 to disable).
                  </p>
                </div>
              </div>
            </div>

            <!-- Price Lists Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-1.5">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Applies to Price Lists ({{ form.price_lists?.length || 0 }})
                </h3>
                <button
                  @click="addPriceListRow"
                  type="button"
                  class="rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1 text-[10px] font-bold text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]/80 transition"
                >
                  + Add Price List
                </button>
              </div>

              <!-- Price Lists Table/List -->
              <div v-if="form.price_lists && form.price_lists.length" class="space-y-2">
                <div 
                  v-for="(pl, idx) in form.price_lists" 
                  :key="idx" 
                  class="flex items-center gap-3"
                >
                  <span class="text-xs text-[var(--color-text-muted)] font-mono w-6 text-center">
                    {{ idx + 1 }}
                  </span>
                  
                  <select
                    v-model="pl.price_list"
                    class="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-1.5 text-xs outline-none focus:border-[var(--color-info)] transition"
                  >
                    <option value="" disabled>Select Price List...</option>
                    <option 
                      v-for="list in priceLists" 
                      :key="list.name" 
                      :value="list.name"
                    >
                      {{ list.name }}
                    </option>
                  </select>

                  <button
                    @click="removePriceListRow(idx)"
                    type="button"
                    class="text-red-500 hover:text-red-700 font-bold px-2 py-1 text-sm transition"
                    title="Remove price list"
                  >
                    ✕
                  </button>
                </div>
              </div>
              <div v-else class="text-xs text-[var(--color-text-muted)] italic text-center py-2">
                No price lists configured. This catalogue applies to all price lists by default.
              </div>
            </div>

            <!-- Items Table Card -->
            <div class="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-sm space-y-4">
              <div class="flex items-center justify-between border-b border-[var(--color-border)]/50 pb-1.5">
                <h3 class="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Catalogue Items ({{ form.items.length }})
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
                  @focus="searchTargetRow = null"
                  @blur="closeItemSearch"
                  @keydown="handleSearchKeydown"
                  type="text"
                  placeholder="Type code, name, or barcode to add item..."
                  class="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-xs outline-none focus:border-[var(--color-info)] transition"
                />
                
                <div @mousedown.prevent>
                  <QuickItemSearch
                    ref="quickSearchRef"
                    :results="searchSuggestions"
                    :query="itemSearchQuery"
                    search-type="Sales"
                    @select="selectSearchItem"
                    @close="closeItemSearch"
                    @refresh="handleItemSearch"
                  />
                </div>
              </div>

              <!-- Invoice-style catalogue items -->
              <p id="catalogue-grid-help" class="text-[var(--color-text-muted)]">
                Click a cell to edit. Tab moves across cells; Enter and ↑ / ↓ move between rows. Enter on the last row adds a new row.
              </p>
              <div ref="itemsGrid" class="catalogue-grid" tabindex="0" aria-label="Catalogue items spreadsheet">
                <table class="catalogue-sheet" aria-describedby="catalogue-grid-help">
                  <thead>
                    <tr>
                      <th scope="col" class="sheet-row-number">#</th>
                      <th v-for="column in itemColumns" :key="column.key" scope="col">
                        {{ column.label }}
                      </th>
                      <th scope="col" class="sheet-action">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="!form.items.length">
                      <td colspan="4" class="sheet-empty">Add an item from inventory or add an empty row to begin.</td>
                    </tr>
                    <tr v-for="(item, idx) in form.items" :key="idx">
                      <th scope="row" class="sheet-row-number">{{ idx + 1 }}</th>
                      <td v-for="(column, columnIndex) in itemColumns" :key="column.key" class="sheet-cell">
                        <input
                          :value="column.key === 'itemcode' && searchTargetRow === idx ? itemSearchQuery : item[column.key]"
                          @input="column.key === 'itemcode' ? searchRowItem($event, idx) : item[column.key] = $event.target.value"
                          @blur="column.key === 'itemcode' && closeItemSearch()"
                          type="text"
                          :data-cell="`${idx}-${columnIndex}`"
                          :aria-label="`${column.label}, row ${idx + 1}`"
                          :class="{ 'sheet-mono': column.key !== 'itemname', 'sheet-code': column.key === 'itemcode' }"
                          @focus="$event.target.select()"
                          autocomplete="off"
                          @keydown="handleItemCellKeydown($event, idx, columnIndex)"
                        />
                      </td>
                      <td class="sheet-action">
                        <button type="button" @click="removeItemRow(idx)" :aria-label="`Remove row ${idx + 1}`" title="Remove row" class="sheet-remove">×</button>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import QuickItemSearch from '../components/QuickItemSearch.vue'
import { frappeGet, frappePost } from '../api.js'
import { useItemCache } from '../services/itemCache.js'

const router = useRouter()
const { items: cachedItems, refreshItemCache } = useItemCache()

// State
const catalogues = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedName = ref(null)
const detailLoading = ref(false)
const saving = ref(false)
const priceLists = ref([])

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
  price_lists: [],
  items: []
})

const form = ref(emptyForm())
const isFormActive = ref(false)

// Item autocomplete search state
const itemSearchQuery = ref('')
const searchSuggestions = ref([])
const quickSearchRef = ref(null)
const searchTargetRow = ref(null)

// Fetch all catalogue documents from the database
async function fetchCatalogues() {
  loading.value = true
  try {
    const data = await frappeGet('frappe.client.get_list', {
      doctype: 'Offer-Items',
      fields: ['name', 'heading', 'pageaddress', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 100
    })
    catalogues.value = data || []
  } catch (e) {
    alert(e.message || 'Failed to fetch catalogue lists')
  } finally {
    loading.value = false
  }
}

// Filter catalogue lists in sidebar
const filteredCatalogues = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return catalogues.value
  return catalogues.value.filter(o =>
    (o.heading || '').toLowerCase().includes(q) ||
    (o.pageaddress || '').toLowerCase().includes(q) ||
    (o.name || '').toLowerCase().includes(q)
  )
})

// Select a catalogue list and load it details including the items child table
async function selectCatalogue(name) {
  selectedName.value = name
  detailLoading.value = true
  isFormActive.value = true
  closeItemSearch()
  
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
      price_lists: (doc.price_lists || []).map(p => ({
        name: p.name,
        price_list: p.price_list || ''
      })),
      items: (doc.items || []).map(i => ({
        name: i.name,
        itemcode: i.itemcode || '',
        itemname: i.itemname || '',
        barcode: i.barcode || ''
      }))
    }
  } catch (e) {
    alert(e.message || 'Failed to load catalogue details')
    closeForm()
  } finally {
    detailLoading.value = false
  }
}

// Open clean form for creating new Catalogue List
function handleNewCatalogue() {
  selectedName.value = null
  isFormActive.value = true
  form.value = emptyForm()
  closeItemSearch()
}

function closeForm() {
  closeItemSearch()
  isFormActive.value = false
  selectedName.value = null
  form.value = emptyForm()
}

// QuickItemSearch filters the shared cache by item code, name, and barcode.
function handleItemSearch() {
  searchSuggestions.value = itemSearchQuery.value.length ? cachedItems.value.slice(0, 1) : []
}

function closeItemSearch() {
  searchSuggestions.value = []
  searchTargetRow.value = null
  itemSearchQuery.value = ''
}

function searchRowItem(event, row) {
  searchTargetRow.value = row
  itemSearchQuery.value = event.target.value
  handleItemSearch()
}

function handleSearchKeydown(event) {
  if (event.isComposing) return
  if (event.key === 'Escape') {
    event.preventDefault()
    closeItemSearch()
    return
  }
  if (searchSuggestions.value.length && ['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)) {
    event.preventDefault()
    quickSearchRef.value?.handleQuickSearchKeydown(event)
  }
}

function handleItemCellKeydown(event, row, column) {
  if (column === 0 && searchTargetRow.value === row) {
    handleSearchKeydown(event)
    if (event.defaultPrevented || event.isComposing) return
    if (event.key === 'Tab') closeItemSearch()
  }
  handleCellKeydown(event, row, column)
}

async function selectSearchItem(item) {
  const row = searchTargetRow.value
  const values = {
    itemcode: item.item_code,
    itemname: item.item_name || '',
    barcode: item.barcodes_detailed?.[0]?.barcode || item.barcodes?.split(',')[0]?.trim() || '',
  }
  if (row !== null && form.value.items[row]) {
    Object.assign(form.value.items[row], values)
  } else {
    form.value.items.push(values)
  }
  closeItemSearch()
  if (row !== null) {
    await nextTick()
    itemsGrid.value?.querySelector(`[data-cell="${row}-0"]`)?.focus()
  }
}

const itemsGrid = ref(null)
const itemColumns = [
  { key: 'itemcode', label: 'Item/Barcode' },
  { key: 'itemname', label: 'Item Name' },
]

async function handleCellKeydown(event, row, column) {
  if (event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return
  let nextRow = row
  let nextColumn = column
  if (event.key === 'Enter') nextRow += event.shiftKey ? -1 : 1
  else if (event.key === 'ArrowDown') nextRow++
  else if (event.key === 'ArrowUp') nextRow--
  else if (event.key === 'Tab') {
    const nextIndex = row * itemColumns.length + column + (event.shiftKey ? -1 : 1)
    nextRow = Math.floor(nextIndex / itemColumns.length)
    nextColumn = (nextIndex + itemColumns.length) % itemColumns.length
  } else return
  if (event.key === 'Enter' && !event.shiftKey && nextRow === form.value.items.length) {
    addEmptyRow()
  }
  // Let Tab leave the grid at its boundaries; Enter stays in the current column.
  if (nextRow < 0 || nextRow >= form.value.items.length) {
    if (event.key !== 'Tab') event.preventDefault()
    return
  }
  event.preventDefault()
  await nextTick()
  const input = itemsGrid.value?.querySelector(`[data-cell="${nextRow}-${nextColumn}"]`)
  input?.focus()
  input?.select()
}

function addEmptyRow() {
  form.value.items.push({
    itemcode: '',
    itemname: '',
    barcode: ''
  })
}

function removeItemRow(idx) {
  closeItemSearch()
  form.value.items.splice(idx, 1)
}

// Save the catalogue document
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
    alert('Please add at least one Item to the catalogue list.')
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
      price_lists: (form.value.price_lists || []).filter(p => p.price_list && p.price_list.trim()).map(p => ({
        ...(p.name && { name: p.name }),
        doctype: 'Offer-Pricelist',
        price_list: p.price_list.trim()
      })),
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

    alert('Catalogue list saved successfully!')
    await fetchCatalogues()
    if (res && res.name) {
      await selectCatalogue(res.name)
    } else {
      closeForm()
    }
  } catch (e) {
    alert(e.message || 'Failed to save catalogue list')
  } finally {
    saving.value = false
  }
}

// Delete the selected Catalogue List
async function handleDeleteCatalogue() {
  if (!form.value.name) return
  if (!confirm(`Are you sure you want to delete catalogue list "${form.value.heading}"?`)) return

  saving.value = true
  try {
    await frappePost('frappe.client.delete', {
      doctype: 'Offer-Items',
      name: form.value.name
    })
    alert('Catalogue list deleted successfully!')
    closeForm()
    await fetchCatalogues()
  } catch (e) {
    alert(e.message || 'Failed to delete catalogue list')
  } finally {
    saving.value = false
  }
}

function addPriceListRow() {
  if (!form.value.price_lists) {
    form.value.price_lists = []
  }
  form.value.price_lists.push({
    price_list: ''
  })
}

function removePriceListRow(idx) {
  form.value.price_lists.splice(idx, 1)
}

async function fetchPriceLists() {
  try {
    const data = await frappeGet('frappe.client.get_list', {
      doctype: 'Price List',
      fields: ['name'],
      order_by: 'name asc',
      limit_page_length: 200
    })
    priceLists.value = data || []
  } catch (e) {
    console.error('Failed to fetch price lists:', e)
  }
}

onMounted(() => {
  fetchCatalogues()
  fetchPriceLists()
  if (!cachedItems.value.length) {
    refreshItemCache('Sales')
  }
})
</script>

<style scoped>
.catalogue-grid {
  max-height: 60vh;
  overflow: auto;
  border: 1px solid var(--color-border);
}
.catalogue-sheet {
  width: 100%;
  min-width: 1000px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 27px;
  line-height: 30px;
}
.catalogue-sheet th,
.catalogue-sheet td {
  border-right: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
.catalogue-sheet thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 8px 6px;
  text-align: left;
  background: var(--color-lowlight);
  color: var(--color-text);
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.catalogue-sheet .sheet-row-number {
  width: 64px;
  text-align: center;
}
.catalogue-sheet tbody .sheet-row-number {
  color: var(--color-text-muted);
  font-family: monospace;
  font-size: 22.5px;
  font-weight: 400;
}
.catalogue-sheet th:nth-child(2) { width: 36%; }
.catalogue-sheet .sheet-action { width: 72px; text-align: center; }
.catalogue-sheet thead .sheet-action { font-size: 10.5px; }
.catalogue-sheet tbody tr { transition: background-color 120ms; }
.catalogue-sheet tbody tr:hover { background: var(--color-surface-raised); }
.catalogue-sheet tbody tr:focus-within {
  background: var(--color-focus);
  color: var(--color-text-on-focus);
  font-weight: 700;
  box-shadow: inset 2px 0 var(--color-focus);
}
.sheet-cell { padding: 0; }
.sheet-cell input {
  display: block;
  width: 100%;
  min-width: 0;
  padding: 4px 8px;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-weight: 500;
}
.sheet-cell input.sheet-mono { font-family: monospace; }
.sheet-cell input.sheet-code { color: var(--color-highlight); }
.sheet-cell input:focus {
  outline: 2px solid var(--color-text-on-focus);
  outline-offset: -2px;
}
.catalogue-sheet tbody tr:focus-within input,
.catalogue-sheet tbody tr:focus-within .sheet-row-number {
  color: var(--color-text-on-focus);
  font-weight: 700;
}
.sheet-remove {
  padding: 2px 4px;
  border-radius: 4px;
  color: var(--color-text-muted);
}
.catalogue-sheet tr:focus-within .sheet-remove { color: var(--color-text-on-focus); }
.catalogue-sheet .sheet-remove:hover,
.catalogue-sheet .sheet-remove:focus-visible {
  background: var(--color-surface-raised);
  color: var(--color-danger);
}
.sheet-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13.5px;
  line-height: 21px;
}

.catalogue-display-page {
  font-size: 19.5px !important; /* 13px * 1.5 */
}
.catalogue-display-page :deep(.text-xs),
.catalogue-display-page :deep(input.text-xs),
.catalogue-display-page :deep(select.text-xs),
.catalogue-display-page :deep(button.text-xs),
.catalogue-display-page :deep(textarea.text-xs) {
  font-size: 18px !important; /* 12px * 1.5 */
}
.catalogue-display-page :deep(.text-sm) {
  font-size: 21px !important; /* 14px * 1.5 */
}
.catalogue-display-page :deep(.text-base) {
  font-size: 24px !important; /* 16px * 1.5 */
}
.catalogue-display-page :deep(.text-5xl) {
  font-size: 72px !important; /* 48px * 1.5 */
}
.catalogue-display-page :deep(.text-\[14px\]) {
  font-size: 21px !important; /* 14px * 1.5 */
}
.catalogue-display-page :deep(.text-\[11px\]) {
  font-size: 16.5px !important; /* 11px * 1.5 */
}
.catalogue-display-page :deep(.text-\[10px\]) {
  font-size: 15px !important; /* 10px * 1.5 */
}
.catalogue-display-page :deep(.text-\[9px\]) {
  font-size: 13.5px !important; /* 9px * 1.5 */
}
</style>
